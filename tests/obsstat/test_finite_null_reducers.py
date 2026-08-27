from fractions import Fraction

import numpy as np
import pytest

from obsstat.finite_null_reducers import (
    legacy_absolute_median_scan,
    loo_ecdf_midrank_scan,
)


def test_legacy_reducer_matches_frozen_scan_and_row_permutation() -> None:
    rows = np.array([[0.0, 2.0], [1.0, 0.0], [3.0, 1.0], [2.0, 4.0]])
    baseline = legacy_absolute_median_scan(rows, ("two-sided", "two-sided"))
    assert baseline.global_p == Fraction(1, 1)
    perm = np.array([2, 0, 3, 1])
    replay = legacy_absolute_median_scan(
        rows[perm], ("two-sided", "two-sided"), observation_index=1
    )
    assert replay.local_p == baseline.local_p
    assert replay.global_p == baseline.global_p


def test_ecdf_is_monotone_permutation_invariant_with_ties() -> None:
    rows = np.array([[0.0, 2.0], [1.0, 2.0], [1.0, 4.0], [3.0, 8.0]])
    tails = ("two-sided", "upper")
    baseline = loo_ecdf_midrank_scan(rows, tails)
    transformed = np.column_stack((np.exp(rows[:, 0]), rows[:, 1] ** 3))
    monotone = loo_ecdf_midrank_scan(transformed, tails)
    assert monotone.local_p_all_rows == baseline.local_p_all_rows
    assert monotone.global_p == baseline.global_p
    reverse = loo_ecdf_midrank_scan(rows[::-1], tails, observation_index=3)
    assert reverse.local_p == baseline.local_p
    assert reverse.global_p == baseline.global_p


def test_reducers_refuse_bad_tail_and_never_return_zero() -> None:
    rows = np.arange(12.0).reshape(4, 3)
    with pytest.raises(ValueError, match="tail"):
        loo_ecdf_midrank_scan(rows, ("upper", "lower", "selected"))
    for reducer in (legacy_absolute_median_scan, loo_ecdf_midrank_scan):
        scan = reducer(rows, ("two-sided",) * 3)
        assert scan.global_p >= Fraction(1, 4)
        assert all(value >= Fraction(1, 4) for value in scan.local_p)


def _exact_two_sided_oracle(values: np.ndarray) -> tuple[Fraction, ...]:
    n_rows = values.size
    denominator = n_rows - 1
    scores = []
    for row, value in enumerate(values):
        others = np.delete(values, row)
        twice_midrank = 2 * int(np.count_nonzero(others < value)) + int(
            np.count_nonzero(others == value)
        )
        scores.append(abs(twice_midrank - denominator))
    return tuple(
        Fraction(sum(candidate >= score for candidate in scores), n_rows)
        for score in scores
    )


@pytest.mark.parametrize(
    "values",
    (np.arange(301.0), np.repeat(np.arange(43.0), 7)),
)
def test_ecdf_two_sided_matches_exact_integer_oracle(values: np.ndarray) -> None:
    scan = loo_ecdf_midrank_scan(values[:, None], ("two-sided",))
    expected = _exact_two_sided_oracle(values)
    assert tuple(row[0] for row in scan.local_p_all_rows) == expected
