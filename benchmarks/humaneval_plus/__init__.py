"""HumanEval+ adapter.

This package does not change the frozen SKYT research runtime. Generation
and Table 1 do not author style contracts and do not run SKYT repair. Table 2
is a separate replay of Certified Consensus repair on stored generations.
The human reference solution is an external baseline, not the protocol canon.
"""

from .manifest import MANIFEST, PILOT_TASK_IDS, load_manifest

__all__ = ["MANIFEST", "PILOT_TASK_IDS", "load_manifest"]
