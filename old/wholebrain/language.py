"""The language cortex: the ONLY place an LLM lives.

Rule: it verbalizes state and (later) parses instructions. Its output is never
written to the ledger or to episodic memory, and never counts as evidence.
"""
import json
import os
import urllib.request


class TemplateCortex:
    """Deterministic readout of internal state (no LLM)."""

    def narrate(self, snap):
        return ("cycle {t}: attention -> {winner}; surprise {surprise:.2f}, "
                "energy {energy:.2f}, hunger {hunger:.2f}; "
                "memory {episodes} episodes").format(**snap)


class AnthropicCortex:
    """Optional LLM narrator. Needs ANTHROPIC_API_KEY in the environment."""

    def __init__(self, model="claude-sonnet-5-5"):
        self.model = model
        self.key = os.environ.get("ANTHROPIC_API_KEY")

    def narrate(self, snap):
        if not self.key:
            return TemplateCortex().narrate(snap)
        body = json.dumps({
            "model": self.model, "max_tokens": 200,
            "messages": [{"role": "user", "content":
                "Describe this agent's internal state in two plain sentences. "
                "Do not claim feelings. State: " + json.dumps(snap)}]}).encode()
        req = urllib.request.Request(
            "https://api.anthropic.com/v1/messages", data=body,
            headers={"content-type": "application/json", "x-api-key": self.key,
                     "anthropic-version": "2023-06-01"})
        with urllib.request.urlopen(req, timeout=20) as r:
            return json.loads(r.read())["content"][0]["text"]
