"""Sensory organs. Every world declares whether it is synthetic.

There is deliberately NO silent fallback from real data to fake data: if a
live feed fails, the agent gets an exception, not made-up numbers.
"""
import math
import random


class World:
    name = "world"
    synthetic = True

    def step(self):
        raise NotImplementedError


class SeasonalWorld(World):
    """Positive control: learnable daily-cycle structure + noise."""
    name = "seasonal_structured"
    synthetic = True

    def __init__(self, seed=0, period=24, noise=0.3):
        self.rng = random.Random(seed)
        self.t = 0
        self.period = period
        self.noise = noise

    def step(self):
        self.t += 1
        p = self.period
        return (2.0 * math.sin(2 * math.pi * self.t / p)
                + 0.7 * math.sin(2 * math.pi * self.t / (p / 3))
                + self.rng.gauss(0, self.noise))


class NoiseWorld(World):
    """Negative control: nothing to learn. The agent must NOT show an edge here."""
    name = "pure_noise_control"
    synthetic = True

    def __init__(self, seed=0):
        self.rng = random.Random(seed)

    def step(self):
        return self.rng.gauss(0, 1.0)


class CSVWorld(World):
    """REAL data: replay one numeric column of a recorded series (e.g. an
    ENTSO-E load export or logged ADS-B counts). Raises when the data ends."""
    synthetic = False

    def __init__(self, path, column=0, skip_header=True, name="csv_replay"):
        self.name = name
        vals = []
        with open(path, encoding="utf-8") as f:
            for i, line in enumerate(f):
                if i == 0 and skip_header:
                    continue
                parts = line.strip().split(",")
                try:
                    vals.append(float(parts[column]))
                except (ValueError, IndexError):
                    continue
        if not vals:
            raise ValueError("no numeric data found in " + path)
        self.vals, self.i = vals, 0

    def step(self):
        if self.i >= len(self.vals):
            raise StopIteration("recorded series exhausted")
        v = self.vals[self.i]
        self.i += 1
        return v
