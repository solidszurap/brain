"""
Self-knowledge: is Ember getting more self-aware?

"Self-aware" here means *functional* self-knowledge: how well the mind
models itself. Each measure is scored against a baseline that has no
self-knowledge at all, so a number only counts if it beats the baseline.
None of this says anything about whether it feels like something to be Ember.

Four measures, each over a rolling window of its life:

1. Knows where it is
   Fraction of moments its believed position is right (relative to where it
   started its map). Baseline: a random guess, about 1/200.
2. Tells "me" from "not me"
   When the wind pushes it, does it notice (hit rate)? When nothing pushed it,
   does it wrongly think something did (false-alarm rate)? Score = hits - false
   alarms. Baseline: 0.
3. Knows how reliable its own predictions are (metacognition)
   Correlation between how surprised it expected to be and how surprised it
   was. Baseline: 0.
4. Predicts its own next thought (attention schema)
   Each time something new ignites its workspace, it first predicts what kind
   of thing will ignite next (a need, something it sees, something it
   remembers, a surprise, curiosity...). Baseline: always guessing the most
   common kind.

The attention schema is part of Ember's mind (it learns about itself from its
own life). The tracker is the scientist watching from outside.
"""
from collections import Counter, defaultdict

import numpy as np

WINDOW = 2000  # moments per measurement


def _kind(broadcast):
    return broadcast.split(":")[0] if broadcast else "nothing"


class AttentionSchema:
    """A model of its own attention: what will grab it next?"""

    def __init__(self):
        self.counts = defaultdict(Counter)   # context -> next kind counts
        self.marginal = Counter()             # next kind counts ignoring context
        self.pending = None                   # (context, model guess, baseline guess)

    @staticmethod
    def context(current_kind, intero):
        need = np.clip((0.9 - np.asarray(intero)) / 0.9, 0, 1)
        dom = int(need.argmax()) if need.max() > 0.15 else 3
        level = int(min(need.max(), 0.99) * 3)      # low / medium / high
        return (current_kind, dom, level)

    def predict(self, ctx):
        c = self.counts.get(ctx)
        model = c.most_common(1)[0][0] if c else (self.marginal.most_common(1)[0][0] if self.marginal else None)
        base = self.marginal.most_common(1)[0][0] if self.marginal else None
        return model, base

    def on_ignition(self, new_kind, intero):
        """Score the pending guess, learn from what actually happened, guess again.
        Returns (model_correct, baseline_correct) or None."""
        scored = None
        if self.pending is not None:
            ctx, guess, base = self.pending
            if guess is not None:
                scored = (guess == new_kind, base == new_kind)
            self.counts[ctx][new_kind] += 1
            self.marginal[new_kind] += 1
        ctx = self.context(new_kind, intero)
        self.pending = (ctx, *self.predict(ctx))
        return scored


class SelfKnowledgeTracker:
    def __init__(self, anchor):
        self.anchor = tuple(anchor)   # true - believed position at the start of its map
        self.history = []             # one record per WINDOW moments
        self._reset()

    def _reset(self):
        self.n = self.located = 0
        self.pushes = self.hits = self.quiet = self.false_alarms = 0
        self.schema_n = self.schema_hits = self.base_hits = 0

    def observe(self, true_pos, believed_pos, pushed, noticed, schema_score):
        self.n += 1
        off = (true_pos[0] - believed_pos[0], true_pos[1] - believed_pos[1])
        self.located += off == self.anchor
        if pushed:
            self.pushes += 1
            self.hits += bool(noticed)
        else:
            self.quiet += 1
            self.false_alarms += bool(noticed)
        if schema_score is not None:
            self.schema_n += 1
            self.schema_hits += schema_score[0]
            self.base_hits += schema_score[1]

    def close_window(self, tick, time_iso, calibration):
        if self.n < WINDOW:
            return None
        hit = self.hits / self.pushes if self.pushes else None
        fa = self.false_alarms / self.quiet if self.quiet else None
        rec = {
            "tick": tick,
            "time": time_iso,
            "location": round(self.located / self.n, 4),
            "detect_hit": None if hit is None else round(hit, 4),
            "detect_false_alarm": None if fa is None else round(fa, 4),
            "self_other": None if hit is None or fa is None else round(hit - fa, 4),
            "calibration": round(float(calibration), 4),
            "schema": round(self.schema_hits / self.schema_n, 4) if self.schema_n else None,
            "schema_baseline": round(self.base_hits / self.schema_n, 4) if self.schema_n else None,
            "schema_n": self.schema_n,
        }
        self.history.append(rec)
        self._reset()
        return rec
