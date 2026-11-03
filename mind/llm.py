"""
Ember's mind: which LLM it thinks with, and the call itself.

Set in .env: EMBER_VOICE = auto | template | gemini | anthropic | openai | ollama,
plus the provider's key (GEMINI_API_KEY, ANTHROPIC_API_KEY, OPENAI_API_KEY).
auto picks the first provider that has a key, else the template mind (no LLM).
Standard library only.
"""
import json
import os
import re
import urllib.error
import urllib.request

# Gemini's free tier (2026-10): gemini-3.5-flash-lite allows about 500 requests a day.
DEFAULT_MODELS = {"anthropic": "claude-haiku-5-5", "gemini": "gemini-3.5-flash-lite", "ollama": "llama3.2", "openai": None}
NAMES = {"anthropic": "Claude", "gemini": "Gemini", "openai": "OpenAI-compatible", "ollama": "Ollama",
         "template": "template mind (no LLM)"}


class LLMError(Exception):
    pass


class LLMConfig:
    def __init__(self, env=None):
        env = os.environ if env is None else env
        choice = (env.get("EMBER_VOICE") or "auto").strip().lower()
        keys = {"anthropic": env.get("ANTHROPIC_API_KEY"), "gemini": env.get("GEMINI_API_KEY"),
                "openai": env.get("OPENAI_API_KEY")}
        if choice == "auto":
            choice = next((p for p in ("gemini", "anthropic", "openai") if keys[p]), "template")
        if choice not in NAMES:
            choice = "template"
        self.provider = choice
        self.key = keys.get(choice)
        self.model = env.get("EMBER_VOICE_MODEL") or DEFAULT_MODELS.get(choice)
        self.base_url = (env.get("EMBER_VOICE_URL") or env.get("OPENAI_BASE_URL")
                         or ("http://localhost:11434/v1" if choice == "ollama" else "https://api.openai.com/v1"))
        self.problem = None
        if choice in ("anthropic", "gemini", "openai") and not self.key:
            self.problem = f"EMBER_VOICE={choice} but no API key is set"
        if choice in ("openai", "ollama") and not self.model:
            self.problem = "set EMBER_VOICE_MODEL to the model's name"

    @property
    def usable(self):
        return self.provider != "template" and not self.problem

    def describe(self):
        if self.provider == "template":
            return NAMES["template"]
        return f"{NAMES[self.provider]} ({self.model})"


def load_dotenv(path):
    """KEY=VALUE lines into the environment (existing variables win). No package needed."""
    if not os.path.exists(path):
        return
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            k, v = k.strip(), v.strip().strip('"').strip("'")
            if k and k not in os.environ:
                os.environ[k] = v


def _post(url, body, headers, timeout=60):
    req = urllib.request.Request(url, data=json.dumps(body).encode(), headers={"content-type": "application/json",
                                                                                  **headers})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        msg = e.read().decode("utf-8", "replace")[:300]
        raise LLMError(f"HTTP {e.code}: {msg}") from None
    except urllib.error.URLError as e:
        raise LLMError(f"can't reach {url.split('/')[2]}: {e.reason}") from None


def call_llm(cfg, system, user, max_tokens=1500, json_mode=False):
    if not cfg.usable:
        raise LLMError(cfg.problem or "no LLM configured")
    p = cfg.provider
    if p == "anthropic":
        d = _post("https://api.anthropic.com/v1/messages",
                  {"model": cfg.model, "max_tokens": max_tokens, "system": system,
                   "messages": [{"role": "user", "content": user}]},
                  {"x-api-key": cfg.key, "anthropic-version": "2023-06-01"})
        return "".join(b.get("text", "") for b in d.get("content", []) if b.get("type") == "text")
    if p == "gemini":
        gen = {"maxOutputTokens": max(max_tokens, 2048)}
        if json_mode:
            gen["responseMimeType"] = "application/json"
        d = _post(f"https://generativelanguage.googleapis.com/v1beta/models/{cfg.model}:generateContent",
                  {"systemInstruction": {"parts": [{"text": system}]},
                   "contents": [{"role": "user", "parts": [{"text": user}]}],
                   "generationConfig": gen},
                  {"x-goog-api-key": cfg.key})
        parts = (d.get("candidates") or [{}])[0].get("content", {}).get("parts", [])
        return "".join(x.get("text", "") for x in parts if not x.get("thought"))
    if p in ("openai", "ollama"):
        headers = {"authorization": f"Bearer {cfg.key}"} if cfg.key else {}
        d = _post(cfg.base_url.rstrip("/") + "/chat/completions",
                  {"model": cfg.model, "messages": [{"role": "system", "content": system},
                                                    {"role": "user", "content": user}]}, headers, timeout=120)
        return d["choices"][0]["message"]["content"] or ""
    raise LLMError("no LLM configured")


def parse_json(text):
    """The first {...} in the reply, tolerating code fences and chatter around it."""
    if not text:
        return None
    t = re.sub(r"^```(?:json)?|```$", "", text.strip(), flags=re.M).strip()
    i, j = t.find("{"), t.rfind("}")
    if i < 0 or j <= i:
        return None
    try:
        return json.loads(t[i:j + 1])
    except json.JSONDecodeError:
        return None
