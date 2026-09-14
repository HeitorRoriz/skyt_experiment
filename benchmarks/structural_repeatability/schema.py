"""Overlay output schema. Measuring tape only — no canon, no repair.

Public metric names follow SPEC.md OPEN 1 (recommended, not frozen):
``same@2`` and ``same@2|cert``. JSON keys cannot hold ``@``/``|``, so the
files use ``same_at_2`` and ``same_at_2_given_cert``. Protocol field names
stay alongside for comparability with HumanEval+ summaries.

``relation_version`` is stamped here (overlay reports) without changing the
generation-record schema in ``src/``. That is SPEC OPEN 4 still open for the
runtime artifacts; the overlay does not wait on it.
"""

from __future__ import annotations

SCHEMA = "skyt-structural-repeatability-overlay-v1"
RELATION_VERSION = 2
RELATION_VERSION_NOTE = (
    "canonical-form fingerprint; docstrings stripped; "
    "scope-aware alpha-renaming of bound names only"
)

# Overlay JSON key -> analyze_repeatability / analyze_records field
METRIC_FIELDS = {
    "same_at_2": "pairwise_exact_match_end_to_end",
    "same_at_2_given_cert": "pairwise_exact_match_certified",
    "plus_pass": "certification_rate",
}

METRIC_HELP = {
    "same_at_2": (
        "Pr[both draws certify and are the same program]. "
        "All C(N,2) pairs; non-certifying draws stay in the denominator."
    ),
    "same_at_2_given_cert": (
        "Pr[same program | both draws certify]. Undefined when a config "
        "has fewer than two certified draws; those configs are dropped and "
        "the drop count is reported."
    ),
    "plus_pass": "Share of the N draws that certify (HumanEval+ plus tests).",
}
