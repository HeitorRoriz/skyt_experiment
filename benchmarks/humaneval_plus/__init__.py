"""HumanEval+ adapter.

This package does not change the frozen SKYT research runtime. It does not
author style contracts and does not run SKYT repair. The human reference
solution is an external baseline, not the protocol's definition of a canon.
"""

from .manifest import MANIFEST, PILOT_TASK_IDS, load_manifest

__all__ = ["MANIFEST", "PILOT_TASK_IDS", "load_manifest"]
