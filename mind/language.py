"""
Language cortex: the LLM, demoted to what it actually is here.

It does not decide anything. It receives only (a) the current content
of the global workspace and (b) the self-model, and turns them into
words. It cannot report what never reached the workspace. That
constraint is what makes its reports *about* the mind instead of a
free-floating story.

Works with no API key (template narration). If ANTHROPIC_API_KEY or
GEMINI_API_KEY is set and MIND_LLM=1, it uses the real model for
richer inner speech and for answering questions about itself.
"""
import json
import os
import urllib.request


def template_report(content, self_model):
    sm = self_model
    body = sm["body"]
    if content is None:
        return "Nothing stands out. I'm idling."
    k, t = content.kind, content.target
    if k == "need":
        return f"I need {'food' if t == 'energy' else 'water' if t == 'hydration' else 'rest'}. ({t} at {body[t]:.0%})"
    if k == "percept":
        return f"I see {t} nearby. Going for it."
    if k == "recall":
        return f"I remember {t} {content.data.get('dist', '?')} steps away. Heading there."
    if k == "threat":
        return "Hazard right next to me. Backing off."
    if k == "surprise":
        moved = content.data.get("shift")
        if moved and moved != (0, 0):
            return f"That wasn't me. Something pushed me; I think I'm {moved} from where I thought."
        return "That wasn't me. Something moved me, but I've kept track of where I am."
    if k == "curiosity" and t == "explore":
        return f"Nothing urgent. Exploring; I know {sm['map_known']} places so far."
    if k == "curiosity":
        return "Nothing urgent. My map is complete, so I'm checking places I haven't seen in a while."
    return f"{k}: {t}"


class LanguageCortex:
    def __init__(self):
        self.use_llm = os.environ.get("MIND_LLM") == "1"
        self.anthropic_key = os.environ.get("ANTHROPIC_API_KEY")
        self.gemini_key = os.environ.get("GEMINI_API_KEY")
        self.model = os.environ.get("MIND_LLM_MODEL")

    def report(self, content, self_model):
        return template_report(content, self_model)

    def ask(self, question, self_model, conscious_episodes):
        """Answer a question about itself, from its own records only."""
        context = {
            "self_model": self_model,
            "recent_conscious_events": conscious_episodes,
        }
        if not self.use_llm:
            evs = " | ".join(f"t={e['t']}: {e['report']}" for e in conscious_episodes[-5:])
            return f"[template, no LLM] Right now I'm attending to {self_model['attending']}. What reached my workspace recently: {evs}"
        prompt = (
            "You are the language area of an artificial agent. You may ONLY use the "
            "facts below, which are the agent's self-model and the events that reached "
            "its global workspace. If the answer is not in them, say you don't know. "
            "Answer in first person, briefly.\n\n"
            f"FACTS:\n{json.dumps(context, default=str)}\n\nQUESTION: {question}"
        )
        try:
            if self.anthropic_key:
                return self._anthropic(prompt)
            if self.gemini_key:
                return self._gemini(prompt)
        except Exception as e:  # language is a peripheral; never crash the mind
            return f"[language cortex offline: {e}]"
        return "[no LLM key set]"

    def _anthropic(self, prompt):
        req = urllib.request.Request(
            "https://api.anthropic.com/v1/messages",
            data=json.dumps({
                "model": self.model or "claude-sonnet-4-5",
                "max_tokens": 300,
                "messages": [{"role": "user", "content": prompt}],
            }).encode(),
            headers={"x-api-key": self.anthropic_key, "anthropic-version": "2023-06-01",
                     "content-type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read())["content"][0]["text"]

    def _gemini(self, prompt):
        model = self.model or "gemini-2.5-flash"
        req = urllib.request.Request(
            f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={self.gemini_key}",
            data=json.dumps({"contents": [{"parts": [{"text": prompt}]}]}).encode(),
            headers={"content-type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read())["candidates"][0]["content"]["parts"][0]["text"]
