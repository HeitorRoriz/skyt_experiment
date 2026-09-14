"""Structural repeatability overlay: measuring tape, not the SKYT tool.

This package does not pick a canon and does not repair. It scores stored
generations (or, with ``--allow-api``, generates new ones into a *new*
output tree) and reports ``same@2`` / ``same@2|cert``.

Never writes into ``outputs/gate0/`` or ``outputs/humaneval_plus/pilot/``.
"""

from .schema import RELATION_VERSION, SCHEMA

__all__ = ["RELATION_VERSION", "SCHEMA"]
