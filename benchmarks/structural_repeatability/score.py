"""Compatibility shim. Use ``benchmark.score``."""

from benchmark.score import score_directory

__all__ = ["score_directory"]
