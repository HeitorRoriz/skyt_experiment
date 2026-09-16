"""Structural repeatability benchmark: measuring tape only.

Canonical-form fingerprint, same@2 / same@2|cert, per model × temperature.
SKYT (canon pick, repair, CV) lives in ``skyt/`` and ``src/``, not here.
"""

from .relation import RELATION_VERSION, fingerprint, same
from .schema import SCHEMA

__all__ = ["RELATION_VERSION", "SCHEMA", "fingerprint", "same"]
