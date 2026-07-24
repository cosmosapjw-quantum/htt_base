from __future__ import annotations

import sys
from fractions import Fraction as F
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
for entry in (str(REPO / "htt"), str(REPO / "htt" / "src")):
    if entry not in sys.path:
        sys.path.insert(0, entry)

from common.joint_feasible_set import (  # noqa: E402
    InfeasibleError,
    UnboundedError,
    exact_support,
)


def test_unbounded_ray_is_not_reported_as_a_finite_point() -> None:
    with pytest.raises(UnboundedError):
        exact_support([F(1)], [[F(-1)]], [F(0)])


def test_unbounded_orthogonal_direction_violates_compact_precondition() -> None:
    constraints = [
        [F(1), F(0)],
        [F(-1), F(0)],
    ]
    with pytest.raises(UnboundedError):
        exact_support([F(1), F(0)], constraints, [F(1), F(0)])


def test_empty_polyhedron_remains_distinct_from_unbounded() -> None:
    constraints = [
        [F(1), F(0)],
        [F(-1), F(0)],
    ]
    with pytest.raises(InfeasibleError):
        exact_support([F(1), F(0)], constraints, [F(0), F(-1)])


def test_bounded_polytope_keeps_exact_support() -> None:
    constraints = [[F(-1)], [F(1)]]
    result = exact_support([F(1)], constraints, [F(0), F(1)])
    assert result["exact_interval"] == ["0", "1"]
