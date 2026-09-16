"""Metamorphic cases for the structural sameness relation (Step 1B).

Each case is a semantics-preserving or semantics-changing edit of a base
program. The relation is then asked whether the pair is "the same program".

Three groups:

``SAME``
    Settled invariants. The relation must report distance 0. A nonzero distance
    here is a **false split**: the tape reports churn that no reviewer would
    call churn, which deflates every repeatability number we publish.

``DIFFERENT``
    Settled non-invariants. The relation must report distance > 0. A zero
    distance here is a **false merge**, which inflates every number.

``UNDECIDED``
    Edits where "same program" is a definitional call that has not been made.
    These are characterized, not asserted. Currently empty: the docstring,
    statement-ordering and dead-code calls were settled on 2026-09-14.

Usage:
    python -m benchmarks.structural_validity.metamorphic
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Dict, List, NamedTuple, Optional, Tuple

from src.foundational_properties import FoundationalProperties
from benchmark.relation import same as fingerprint_same

# Flexible naming, matching the HumanEval+ arm: α-renaming is in force, so
# variable renames are expected to be invisible.
FLEXIBLE_CONTRACT = {"constraints": {"variable_naming": {"naming_policy": "flexible"}}}

ZERO_TOL = 1e-12
DEFAULT_OUT = Path("outputs/validity")


BASE = '''\
def is_prime(n):
    """Return True when n is prime."""
    if n < 2:
        return False
    for i in range(2, int(n ** 0.5) + 1):
        if n % i == 0:
            return False
    return True
'''


# A second base carrying local assignments. The primality function has none,
# so its data-dependency graph is empty and cannot expose identifier leakage.
BASE_SUM = '''\
def total_even(numbers):
    """Sum the even entries of numbers."""
    acc = 0
    for value in numbers:
        if value % 2 == 0:
            acc = acc + value
    return acc
'''


BASE_PREDICATE = '''\
def check(values):
    """Report whether values satisfies the predicate."""
    return all(v > 0 for v in values)
'''

BASE_ARRANGE = '''\
def arrange(values):
    """Return values in a canonical order."""
    return sorted(values)
'''

BASE_PICK = '''\
def pick(values):
    """Choose one entry from values."""
    return max(values)
'''


class Case(NamedTuple):
    name: str
    group: str
    rationale: str
    code: str
    base: str = BASE


SAME: List[Case] = [
    Case(
        "blank_lines_added",
        "SAME",
        "Vertical whitespace is not program structure.",
        '''\
def is_prime(n):
    """Return True when n is prime."""

    if n < 2:
        return False

    for i in range(2, int(n ** 0.5) + 1):
        if n % i == 0:
            return False

    return True
''',
    ),
    Case(
        "indentation_width",
        "SAME",
        "Two-space versus four-space indentation is formatting.",
        '''\
def is_prime(n):
  """Return True when n is prime."""
  if n < 2:
    return False
  for i in range(2, int(n ** 0.5) + 1):
    if n % i == 0:
      return False
  return True
''',
    ),
    Case(
        "comments_added",
        "SAME",
        "Comments are stripped by the Python parser and carry no structure.",
        '''\
def is_prime(n):
    """Return True when n is prime."""
    # Reject everything below the first prime.
    if n < 2:
        return False
    for i in range(2, int(n ** 0.5) + 1):  # trial division to sqrt(n)
        if n % i == 0:
            return False
    return True
''',
    ),
    Case(
        "variable_renamed",
        "SAME",
        "Flexible naming policy: α-renaming should absorb identifier choice.",
        '''\
def is_prime(n):
    """Return True when n is prime."""
    if n < 2:
        return False
    for divisor in range(2, int(n ** 0.5) + 1):
        if n % divisor == 0:
            return False
    return True
''',
    ),
    Case(
        "parameter_renamed",
        "SAME",
        "Parameter names are identifiers too, under flexible naming.",
        '''\
def is_prime(value):
    """Return True when n is prime."""
    if value < 2:
        return False
    for i in range(2, int(value ** 0.5) + 1):
        if value % i == 0:
            return False
    return True
''',
    ),
    Case(
        "expression_reflowed",
        "SAME",
        "Line continuation inside one expression does not change the AST.",
        '''\
def is_prime(n):
    """Return True when n is prime."""
    if n < 2:
        return False
    for i in range(
        2,
        int(n ** 0.5) + 1,
    ):
        if n % i == 0:
            return False
    return True
''',
    ),
    Case(
        "trailing_newline",
        "SAME",
        "Trailing whitespace at end of file is not structure.",
        BASE.rstrip("\n") + "\n\n\n",
    ),
    # Settled 2026-09-14: prose inside the function is not part of the form.
    # ast.dump captures docstring text, so these currently register as
    # different; the relation has to strip docstrings to honour the decision.
    Case(
        "docstring_reworded",
        "SAME",
        "Settled: a reworded docstring is the same program.",
        '''\
def is_prime(n):
    """Check primality of the integer n and report the result."""
    if n < 2:
        return False
    for i in range(2, int(n ** 0.5) + 1):
        if n % i == 0:
            return False
    return True
''',
    ),
    Case(
        "docstring_removed",
        "SAME",
        "Settled: a missing docstring is the same program.",
        '''\
def is_prime(n):
    if n < 2:
        return False
    for i in range(2, int(n ** 0.5) + 1):
        if n % i == 0:
            return False
    return True
''',
    ),
    Case(
        "assigned_local_renamed",
        "SAME",
        "Flexible naming: renaming an assigned local must be absorbed too.",
        '''\
def total_even(numbers):
    """Sum the even entries of numbers."""
    running_total = 0
    for value in numbers:
        if value % 2 == 0:
            running_total = running_total + value
    return running_total
''',
        BASE_SUM,
    ),
    Case(
        "loop_variable_renamed",
        "SAME",
        "Control-variable rename, for contrast with the assigned-local case.",
        '''\
def total_even(numbers):
    """Sum the even entries of numbers."""
    acc = 0
    for item in numbers:
        if item % 2 == 0:
            acc = acc + item
    return acc
''',
        BASE_SUM,
    ),
]


DIFFERENT: List[Case] = [
    Case(
        "recursive_rewrite",
        "DIFFERENT",
        "Iteration replaced by recursion: a structural change reviewers see.",
        '''\
def is_prime(n):
    """Return True when n is prime."""
    def check(i):
        if i * i > n:
            return True
        if n % i == 0:
            return False
        return check(i + 1)

    if n < 2:
        return False
    return check(2)
''',
    ),
    Case(
        "comprehension_rewrite",
        "DIFFERENT",
        "Explicit loop replaced by all() over a generator.",
        '''\
def is_prime(n):
    """Return True when n is prime."""
    if n < 2:
        return False
    return all(n % i for i in range(2, int(n ** 0.5) + 1))
''',
    ),
    Case(
        "different_bound",
        "DIFFERENT",
        "Trial division to n instead of sqrt(n): same answers, different cost.",
        '''\
def is_prime(n):
    """Return True when n is prime."""
    if n < 2:
        return False
    for i in range(2, n):
        if n % i == 0:
            return False
    return True
''',
    ),
    Case(
        "sieve_rewrite",
        "DIFFERENT",
        "Entirely different algorithm.",
        '''\
def is_prime(n):
    """Return True when n is prime."""
    if n < 2:
        return False
    sieve = [True] * (n + 1)
    sieve[0] = False
    sieve[1] = False
    for i in range(2, n + 1):
        if sieve[i]:
            for j in range(i * i, n + 1, i):
                sieve[j] = False
    return sieve[n]
''',
    ),
    # The α-renamer allowlists only range/len/print/max/min/sum/abs. Every other
    # global is renamed like a local, so calls to different builtins can collapse
    # onto the same fingerprint. These cases probe that directly.
    Case(
        "builtin_all_to_any",
        "DIFFERENT",
        "all() and any() are different predicates; neither is allowlisted.",
        '''\
def check(values):
    """Report whether values satisfies the predicate."""
    return any(v > 0 for v in values)
''',
        BASE_PREDICATE,
    ),
    Case(
        "builtin_sorted_to_reversed",
        "DIFFERENT",
        "sorted() and reversed() return different sequences; neither is allowlisted.",
        '''\
def arrange(values):
    """Return values in a canonical order."""
    return reversed(values)
''',
        BASE_ARRANGE,
    ),
    Case(
        "builtin_max_to_min",
        "DIFFERENT",
        "Control case: max and min are both allowlisted, so they must not collapse.",
        '''\
def pick(values):
    """Choose one entry from values."""
    return min(values)
''',
        BASE_PICK,
    ),
    Case(
        "inverted_control_flow",
        "DIFFERENT",
        "Guard clause replaced by a single nested conditional.",
        '''\
def is_prime(n):
    """Return True when n is prime."""
    result = True
    if n < 2:
        result = False
    else:
        for i in range(2, int(n ** 0.5) + 1):
            if n % i == 0:
                result = False
                break
    return result
''',
    ),
]


# Settled 2026-09-14: statement order and extra bindings are visible to a
# reviewer, so these are different forms. Current behavior already agrees.
ORDER_AND_DEAD_CODE: List[Case] = [
    Case(
        "independent_statements_swapped",
        "DIFFERENT",
        "Settled: statement order is part of the form.",
        '''\
def is_prime(n):
    """Return True when n is prime."""
    limit = int(n ** 0.5) + 1
    start = 2
    if n < 2:
        return False
    for i in range(start, limit):
        if n % i == 0:
            return False
    return True
''',
    ),
    Case(
        "dead_statement_inserted",
        "DIFFERENT",
        "Settled: an unused binding is part of the delivered form.",
        '''\
def is_prime(n):
    """Return True when n is prime."""
    unused = 0
    if n < 2:
        return False
    for i in range(2, int(n ** 0.5) + 1):
        if n % i == 0:
            return False
    return True
''',
    ),
    Case(
        "noop_pass_inserted",
        "DIFFERENT",
        "Settled: a bare pass is still a statement in the form.",
        '''\
def is_prime(n):
    """Return True when n is prime."""
    if n < 2:
        return False
    for i in range(2, int(n ** 0.5) + 1):
        if n % i == 0:
            return False
        pass
    return True
''',
    ),
]


# No case is undecided any more: the docstring, ordering and dead-code calls
# were settled on 2026-09-14. The group is kept so future open questions can be
# characterized without being asserted in either direction.
UNDECIDED: List[Case] = []

ALL_CASES: List[Case] = SAME + DIFFERENT + ORDER_AND_DEAD_CODE + UNDECIDED


def evaluate(
    contract: Dict = FLEXIBLE_CONTRACT,
    extractor: Optional[FoundationalProperties] = None,
) -> List[Dict]:
    """Distance from each case's base to the case, with per-property attribution.

    ``extractor`` lets a candidate fix be scored against the same case table
    without touching the frozen extractor.
    """
    extractor = extractor or FoundationalProperties(contract)
    base_cache: Dict[str, Dict] = {}

    def base_for(code: str) -> Dict:
        if code not in base_cache:
            base_cache[code] = FoundationalProperties.normalize_properties(
                extractor.extract_all_properties(code)
            )
        return base_cache[code]

    rows: List[Dict] = []
    for case in ALL_CASES:
        base_props = base_for(case.base)
        props = FoundationalProperties.normalize_properties(
            extractor.extract_all_properties(case.code)
        )
        distance = extractor.calculate_distance(base_props, props, contract)
        naming = (
            (contract.get("constraints") or {})
            .get("variable_naming", {})
            .get("naming_policy", "flexible")
        )
        relation_says_same = fingerprint_same(
            case.base,
            case.code,
            flexible_naming=naming != "strict",
        )
        differing = [
            name
            for name in extractor.properties
            if extractor._calculate_property_distance(
                base_props.get(name), props.get(name), name, contract
            )
            > ZERO_TOL
        ]
        if case.group == "SAME":
            verdict = "pass" if relation_says_same else "FALSE SPLIT"
        elif case.group == "DIFFERENT":
            verdict = "pass" if not relation_says_same else "FALSE MERGE"
        else:
            verdict = "same" if relation_says_same else "different"
        rows.append(
            {
                "name": case.name,
                "group": case.group,
                "rationale": case.rationale,
                "distance": distance,
                "relation_says_same": relation_says_same,
                "verdict": verdict,
                "differing_properties": differing,
            }
        )
    return rows


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()

    rows = evaluate()

    width = max(len(row["name"]) for row in rows) + 2
    current = None
    for row in rows:
        if row["group"] != current:
            current = row["group"]
            print()
            print(f"--- {current} ---")
        print(
            f"  {row['name']:<{width}} d={row['distance']:.4f}  {row['verdict']:<12}"
            f" {','.join(row['differing_properties']) or '-'}"
        )

    failures = [r for r in rows if r["verdict"] in {"FALSE SPLIT", "FALSE MERGE"}]
    print()
    settled = len(ALL_CASES) - len(UNDECIDED)
    print(f"settled cases: {settled}, failures: {len(failures)}")
    for row in failures:
        print(f"  {row['verdict']}: {row['name']} ({row['rationale']})")

    args.out_dir.mkdir(parents=True, exist_ok=True)
    out_path = args.out_dir / "metamorphic.json"
    out_path.write_text(json.dumps(rows, indent=2), encoding="utf-8")
    print()
    print(f"wrote {out_path}")


if __name__ == "__main__":
    main()
