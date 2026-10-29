"""Artificial Mind v3: an embodied whole-brain architecture.

The LLM is one peripheral (the language cortex). The mind is the loop.
"""
from .world import World
from .agent import Mind
from .simulate import simulate, ABLATIONS
