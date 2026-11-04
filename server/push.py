"""
Phone notifications (Web Push): Ember's check-ups reach your phone even when its window is closed.

Your browser (or the home-screen app) gives the server a subscription: an address at Apple's, Google's or
Mozilla's push service, plus two keys. To notify you, the server encrypts the message for your browser alone
(RFC 8291, aes128gcm) and signs the request with Ember's own key (VAPID, RFC 8292), so only Ember can send
to it. Uses the `cryptography` package (Szilard's choice, 2026-11-04) and urllib.

Settings (Render): VAPID_PRIVATE_KEY (made once by tools/make_vapid.py; a secret), VAPID_SUBJECT (optional:
a mailto: or https: address the push services can contact; default: the service's own address).
"""
import base64
import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.asymmetric.utils import decode_dss_signature
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.hkdf import HKDF

RECORD = 4096           # the one record's size (aes128gcm); a notification is far smaller


def b64u(data):
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def unb64u(text):
    return base64.urlsafe_b64decode(text + "=" * (-len(text) % 4))


def _raw_public(key):
    return key.public_key().public_bytes(serialization.Encoding.X962, serialization.PublicFormat.UncompressedPoint)


def _hkdf(salt, ikm, info, length):
    return HKDF(algorithm=hashes.SHA256(), length=length, salt=salt, info=info).derive(ikm)


def new_private_key():
    """A new VAPID key, as the text that goes into VAPID_PRIVATE_KEY."""
    return b64u(ec.generate_private_key(ec.SECP256R1()).private_numbers().private_value.to_bytes(32, "big"))


def encrypt(payload, p256dh, auth, salt=None, sender=None):
    """The body of a push message: payload encrypted for one subscription (RFC 8291)."""
    ua_public = unb64u(p256dh)
    sender = sender or ec.generate_private_key(ec.SECP256R1())
    as_public = _raw_public(sender)
    shared = sender.exchange(ec.ECDH(), ec.EllipticCurvePublicKey.from_encoded_point(ec.SECP256R1(), ua_public))
    ikm = _hkdf(unb64u(auth), shared, b"WebPush: info\x00" + ua_public + as_public, 32)
    salt = salt or os.urandom(16)
    cek = _hkdf(salt, ikm, b"Content-Encoding: aes128gcm\x00", 16)
    nonce = _hkdf(salt, ikm, b"Content-Encoding: nonce\x00", 12)
    sealed = AESGCM(cek).encrypt(nonce, payload + b"\x02", None)          # \x02: the last (and only) record
    return salt + RECORD.to_bytes(4, "big") + bytes([len(as_public)]) + as_public + sealed


class PushGone(Exception):
    """The subscription no longer exists (the person turned notifications off, or reinstalled)."""


class Push:
    def __init__(self, private_key, subject=None):
        self.key = ec.derive_private_key(int.from_bytes(unb64u(private_key), "big"), ec.SECP256R1())
        self.public = b64u(_raw_public(self.key))         # the window subscribes with this (applicationServerKey)
        self.subject = subject or os.environ.get("RENDER_EXTERNAL_URL") or "https://ember.example"

    def _vapid(self, endpoint, now):
        u = urllib.parse.urlsplit(endpoint)
        head = b64u(json.dumps({"typ": "JWT", "alg": "ES256"}).encode())
        claims = b64u(json.dumps({"aud": f"{u.scheme}://{u.netloc}", "exp": int(now) + 12 * 3600,
                                  "sub": self.subject}).encode())
        r, s = decode_dss_signature(self.key.sign(f"{head}.{claims}".encode(), ec.ECDSA(hashes.SHA256())))
        token = f"{head}.{claims}." + b64u(r.to_bytes(32, "big") + s.to_bytes(32, "big"))
        return f"vapid t={token}, k={self.public}"

    def send(self, device, message, ttl=24 * 3600, now=None):
        """Send one notification ({title, body, chat}) to one device; PushGone if it no longer exists."""
        body = encrypt(json.dumps(message, ensure_ascii=False).encode(), device["keys"]["p256dh"], device["keys"]["auth"])
        req = urllib.request.Request(device["endpoint"], data=body, method="POST", headers={
            "Authorization": self._vapid(device["endpoint"], time.time() if now is None else now),
            "TTL": str(ttl), "Content-Encoding": "aes128gcm", "Content-Type": "application/octet-stream",
            "Urgency": "normal"})
        try:
            with urllib.request.urlopen(req, timeout=15) as r:
                return r.status
        except urllib.error.HTTPError as e:
            if e.code in (404, 410):
                raise PushGone() from None
            raise
