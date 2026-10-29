"""
Thalamus / Global Workspace (Baars, Dehaene).

Every module posts candidate contents with a salience. They compete.
If the winner crosses an ignition threshold it is *broadcast*: it
becomes the one thing every module now conditions on (the planner sets
its goal from it, the hippocampus stores it with high priority, the
language cortex may only report it). Broadcast content self-sustains
for a while (reverberation) and can only be displaced by something
clearly stronger. Contents that never ignite can still drive reflexes
and habits, but they are never reportable.

This is the functional definition of "access consciousness" used in
this project: reportable + globally available + capacity-limited.
"""
from dataclasses import dataclass, field
import numpy as np


@dataclass
class Content:
    kind: str            # need | percept | recall | threat | surprise | goal
    target: str          # e.g. "water", "food", "hazard", "push"
    salience: float
    source: str
    data: dict = field(default_factory=dict)

    def key(self):
        return f"{self.kind}:{self.target}"

    def __str__(self):
        return f"{self.kind}:{self.target}"


class GlobalWorkspace:
    def __init__(self, rng, threshold=0.3, margin=0.15, min_dwell=4, enabled=True):
        self.rng = rng
        self.threshold = threshold
        self.margin = margin
        self.min_dwell = min_dwell
        self.enabled = enabled
        self.current = None
        self.dwell = 0
        self.ignitions = 0
        self.candidates = []

    def post(self, content):
        self.candidates.append(content)

    def cycle(self):
        """Run one competition. Returns (broadcast content or None, ignited_now)."""
        cands = self.candidates
        self.candidates = []
        if not cands:
            self.dwell += 1
            return self.current, False
        noise = self.rng.normal(0, 0.03, len(cands))
        scores = np.array([c.salience for c in cands]) + noise
        i = int(scores.argmax())
        winner, score = cands[i], scores[i]

        if not self.enabled:
            # Ablation: no workspace. The strongest signal of this instant
            # simply wins: no threshold, no persistence, no hysteresis.
            self.current = winner
            return winner, False

        if self.current is not None:
            # the broadcast content is refreshed from its own module
            same = [c for c in cands if c.key() == self.current.key()]
            if same:
                self.current = same[0]
            else:
                self.current.salience *= 0.85  # decays without support
            self.dwell += 1
            stronger = score > self.current.salience + self.margin
            expired = self.current.salience < self.threshold * 0.6
            interrupt = winner.kind == "threat" and score > self.threshold
            switch = winner.key() != self.current.key() and (
                (stronger and self.dwell >= self.min_dwell) or expired or interrupt)
            if not switch:
                return self.current, False
        if score >= self.threshold:
            self.current = winner
            self.dwell = 0
            self.ignitions += 1
            return winner, True
        self.current = None
        return None, False
