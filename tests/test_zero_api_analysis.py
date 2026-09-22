"""Zero-API fingerprint rulers. No Docker."""

import pytest

from skyt.zero_api_analysis import ast_normalized_id, sameeval_id, source_normalized_id, spearman

FORM_A = "def add(a, b):\n    return a + b\n"
FORM_A_WS = "def add(a, b):\n\n    return a + b\n"
FORM_A_NAME = "def add(x, y):\n    return x + y\n"
FORM_B = "def add(a, b):\n    total = a + b\n    return total\n"


def test_source_normalized_ignores_whitespace():
    assert source_normalized_id(FORM_A) == source_normalized_id(FORM_A_WS)


def test_sameeval_alpha_renames_parameters():
    assert sameeval_id(FORM_A) == sameeval_id(FORM_A_NAME)


def test_source_normalized_keeps_parameter_names():
    assert source_normalized_id(FORM_A) != source_normalized_id(FORM_A_NAME)


def test_rulers_distinguish_different_bodies():
    assert source_normalized_id(FORM_A) != source_normalized_id(FORM_B)
    assert ast_normalized_id(FORM_A) != ast_normalized_id(FORM_B)
    assert sameeval_id(FORM_A) != sameeval_id(FORM_B)


def test_spearman_negative_for_inverse():
    xs = [1.0, 2.0, 3.0, 4.0]
    ys = [8.0, 6.0, 4.0, 2.0]
    assert spearman(xs, ys) == pytest.approx(-1.0)
