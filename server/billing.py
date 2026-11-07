"""
Ember Plus through Stripe. Ember never sees card details: people pay on Stripe's
own checkout page, manage or cancel on Stripe's own portal, and Stripe tells this
server what happened through a signed webhook. Standard library only (urllib, hmac).

Settings (Render): STRIPE_SECRET_KEY, STRIPE_PRICE_ID (the monthly Ember Plus price),
STRIPE_WEBHOOK_SECRET (signs the webhook calls), EMBER_PRICE_LABEL (shown in the window).
"""
import hashlib
import hmac
import json
import urllib.error
import urllib.parse
import urllib.request

PLUS_STATUSES = {"active", "trialing", "past_due"}   # past_due: Stripe is still retrying the card
TOLERANCE = 300                                       # seconds a webhook signature stays valid


class BillingError(Exception):
    pass


def branding(base_url):
    """Ember's name, icon and colours on its Stripe payment page (just this page: the Stripe account may sell
    other things, whose pages keep the account's own branding)."""
    return {"branding_settings[display_name]": "Ember",
            "branding_settings[icon][type]": "url", "branding_settings[icon][url]": f"{base_url}/icons/icon-512.png",
            "branding_settings[background_color]": "#17130f", "branding_settings[button_color]": "#ffa862",
            "branding_settings[border_style]": "pill", "branding_settings[font_family]": "nunito"}


class Billing:
    def __init__(self, secret_key=None, price_id=None, webhook_secret=None, price_label="$4.99 / month",
                 api="https://api.stripe.com", terms_url=None):
        self.key, self.price, self.whsec = secret_key, price_id, webhook_secret
        self.price_label, self.api = price_label, api.rstrip("/")
        self.terms_url = (terms_url or "").strip() or None      # the ÁSZF; buyers accept it at checkout
        self.enabled = bool(secret_key and price_id and webhook_secret)
        self.live = bool(secret_key and secret_key.startswith(("sk_live_", "rk_live_")))
        # real money only once the terms are online (a live key without EMBER_TERMS_URL: "Ember Plus opens soon")
        self.selling = self.enabled and (not self.live or bool(self.terms_url))

    def _post(self, path, fields):
        data = urllib.parse.urlencode(fields).encode()
        req = urllib.request.Request(self.api + path, data=data, method="POST",
                                     headers={"Authorization": f"Bearer {self.key}",
                                              "Content-Type": "application/x-www-form-urlencoded"})
        try:
            with urllib.request.urlopen(req, timeout=20) as r:
                return json.loads(r.read())
        except urllib.error.HTTPError as e:
            raise BillingError(f"Stripe {path}: HTTP {e.code}") from None
        except (urllib.error.URLError, TimeoutError) as e:
            raise BillingError(f"Stripe unreachable: {getattr(e, 'reason', e)}") from None

    def checkout(self, uid, email, customer, base_url):
        """A Stripe Checkout page for a monthly Ember Plus subscription; returns its address."""
        fields = {"mode": "subscription", "line_items[0][price]": self.price, "line_items[0][quantity]": "1",
                  "success_url": f"{base_url}/?plus=success", "cancel_url": f"{base_url}/?plus=cancel",
                  "client_reference_id": uid, "subscription_data[metadata][user_id]": uid,
                  # tagged as Ember's: the Stripe account may sell other things too, and their events reach this webhook
                  "metadata[app]": "ember", "subscription_data[metadata][app]": "ember",
                  "allow_promotion_codes": "true",
                  "payment_method_types[0]": "card"}           # cards (Apple Pay and Google Pay included), nothing else
        if self.terms_url:                                  # Stripe asks them to accept the terms (its Public details
            fields["consent_collection[terms_of_service]"] = "required"     # must have the same terms URL)
        who = ([{"customer": customer}] if customer else []) + ([{"customer_email": email}] if email else [{}])
        last = None
        for w in who:                    # a customer Stripe no longer knows (say, from test mode): start fresh by email
            for brand in (branding(base_url), {}):          # Ember's own look; plain if this API version refuses it
                try:
                    return self._post("/v1/checkout/sessions", {**fields, **w, **brand})["url"]
                except BillingError as e:
                    last = e
        raise last

    def portal(self, customer, base_url):
        """Stripe's page where a subscriber cancels or changes their card; returns its address."""
        return self._post("/v1/billing_portal/sessions", {"customer": customer, "return_url": base_url + "/"})["url"]

    def cancel(self, subscription):
        """Stop a subscription right away (used when someone deletes their Ember)."""
        req = urllib.request.Request(f"{self.api}/v1/subscriptions/{urllib.parse.quote(subscription)}", method="DELETE",
                                     headers={"Authorization": f"Bearer {self.key}"})
        try:
            with urllib.request.urlopen(req, timeout=20) as r:
                return json.loads(r.read())
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return None                          # already gone
            raise BillingError(f"Stripe cancel: HTTP {e.code}") from None
        except (urllib.error.URLError, TimeoutError) as e:
            raise BillingError(f"Stripe unreachable: {getattr(e, 'reason', e)}") from None

    def verify(self, payload, signature, now):
        """The event, if Stripe really sent it (HMAC-SHA256 over 't.payload', within 5 minutes)."""
        try:
            parts = dict(p.split("=", 1) for p in signature.split(",") if "=" in p)
            sigs = [p.split("=", 1)[1] for p in signature.split(",") if p.startswith("v1=")]
            t = int(parts["t"])
        except (KeyError, ValueError, AttributeError):
            raise BillingError("bad signature header") from None
        expected = hmac.new(self.whsec.encode(), f"{t}.".encode() + payload, hashlib.sha256).hexdigest()
        if not any(hmac.compare_digest(expected, s) for s in sigs):
            raise BillingError("signature doesn't match")
        if abs(now - t) > TOLERANCE:
            raise BillingError("signature too old")
        return json.loads(payload)

    @staticmethod
    def plan_from_event(event, price=None):
        """(user id, plan) for the events that change someone's Ember Plus; None for the rest, including
        whatever else the same Stripe account sells: only Ember's own (tagged app=ember, or older ones
        with Ember's price) count."""
        kind, obj = event.get("type"), (event.get("data") or {}).get("object") or {}
        meta = obj.get("metadata") or {}
        items = ((obj.get("items") or {}).get("data") or [])
        ours = meta.get("app") == "ember" or bool(price and any((i.get("price") or {}).get("id") == price for i in items))
        if not ours:
            return None
        if kind == "checkout.session.completed" and obj.get("mode") == "subscription":
            uid = obj.get("client_reference_id")
            return (uid, {"status": "active", "customer": obj.get("customer"),
                          "subscription": obj.get("subscription")}) if uid else None
        if kind in ("customer.subscription.created", "customer.subscription.updated",
                    "customer.subscription.deleted"):
            uid = (obj.get("metadata") or {}).get("user_id")
            status = "canceled" if kind.endswith("deleted") else obj.get("status")
            return (uid, {"status": status, "customer": obj.get("customer"),
                          "subscription": obj.get("id")}) if uid else None
        return None
