"""
Ember's mind: which LLM it thinks with, and the call itself.

Set in .env (or the server's environment): EMBER_VOICE = auto | template | anthropic | gemini | openai | ollama,
plus the provider's key (ANTHROPIC_API_KEY, GEMINI_API_KEY, OPENAI_API_KEY).
auto picks the first provider that has a key (Claude first), else the template mind (no LLM).
Claude goes through the official `anthropic` SDK (imported only when used); the others use urllib.
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
    """retryable: the mind was busy or unreachable (overloaded, rate-limited, network), worth trying again."""
    def __init__(self, msg, retryable=False):
        super().__init__(msg)
        self.retryable = retryable


class LLMConfig:
    def __init__(self, env=None):
        env = os.environ if env is None else env
        choice = (env.get("EMBER_VOICE") or "auto").strip().lower()
        keys = {"anthropic": env.get("ANTHROPIC_API_KEY"), "gemini": env.get("GEMINI_API_KEY"),
                "openai": env.get("OPENAI_API_KEY")}
        if choice == "auto":
            choice = next((p for p in ("anthropic", "gemini", "openai") if keys[p]), "template")
        if choice not in NAMES:
            choice = "template"
        self.provider = choice
        self.key = keys.get(choice)
        self.model = env.get("EMBER_VOICE_MODEL") or DEFAULT_MODELS.get(choice)
        self.base_url = (env.get("EMBER_VOICE_URL") or env.get("OPENAI_BASE_URL")
                         or ("http://localhost:11434/v1" if choice == "ollama" else "https://api.openai.com/v1"))
        self.problem = None
        self.last_usage = None       # (input tokens, output tokens) of the last Claude call, for cost logging
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
        raise LLMError(f"HTTP {e.code}: {msg}", retryable=e.code in (408, 429) or e.code >= 500) from None
    except (urllib.error.URLError, TimeoutError) as e:
        raise LLMError(f"can't reach {url.split('/')[2]}: {getattr(e, 'reason', e)}", retryable=True) from None


def call_llm(cfg, system, user, max_tokens=1500, json_mode=False):
    if not cfg.usable:
        raise LLMError(cfg.problem or "no LLM configured")
    p = cfg.provider
    if p == "anthropic":
        return _call_claude(cfg, system, user)
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


_claude = {}


def _call_claude(cfg, system, user):
    """One reply from Claude. Low effort: fast and cheap, and plenty for conversation.
    The SDK itself retries overloaded, rate-limited and network errors a few times."""
    import anthropic
    client = _claude.get(cfg.key)
    if client is None:
        client = _claude[cfg.key] = anthropic.Anthropic(api_key=cfg.key, max_retries=3, timeout=60.0)
    try:
        r = client.messages.create(model=cfg.model, max_tokens=16000, system=system,
                                   output_config={"effort": "low"},
                                   messages=[{"role": "user", "content": user}])
    except (anthropic.RateLimitError, anthropic.APIConnectionError) as e:
        raise LLMError(f"Claude is busy or unreachable: {type(e).__name__}", retryable=True) from None
    except anthropic.APIStatusError as e:
        raise LLMError(f"Claude API error {e.status_code}", retryable=e.status_code >= 500) from None
    cfg.last_usage = (r.usage.input_tokens, r.usage.output_tokens)
    if r.stop_reason == "refusal":
        raise LLMError("Claude declined to answer this one", retryable=False)
    return "".join(b.text for b in r.content if b.type == "text")


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
