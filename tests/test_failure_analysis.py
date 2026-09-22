"""Failure-analysis construct flags. No Docker, no API."""

from skyt.failure_analysis import construct_profile


RECURSIVE = """
def fact(n):
    if n <= 1:
        return 1
    return n * fact(n - 1)
"""

LOOPS = """
def walk(xs):
    total = 0
    for x in xs:
        total += x
    while total > 10:
        total -= 1
    return total
"""


def test_recursion_and_loops():
    rec = construct_profile(RECURSIVE)
    assert rec["parse_ok"]
    assert rec["recursion"]
    assert not rec["for_loop"]
    loops = construct_profile(LOOPS)
    assert loops["for_loop"]
    assert loops["while_loop"]
    assert not loops["recursion"]


def test_bad_syntax():
    flags = construct_profile("def oops(")
    assert flags["parse_ok"] is False
