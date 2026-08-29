from __future__ import annotations

import itertools
import math

import numpy as np
import pytest

from obsstat.planck_irrep_injections import (
    AMPLITUDES,
    CALIBRATION_COUNT,
    COMBINERS,
    ECDF,
    LEGACY,
    family_numerators,
    harmonic_energy,
    inject,
    local_numerators,
    metric,
    orientation_bank,
    orientation_uniforms,
    reference_scale,
    rotate_template,
    rotation_matrix,
    score_queries,
    split_indices,
    template_bank,
    threshold_crossings,
)


def _slow_local_numerators(
    pools: np.ndarray, tails: tuple[str, ...], reducer: str
) -> np.ndarray:
    batches, rows, columns = pools.shape
    scores = np.empty((batches, rows, columns), dtype=object)
    for batch, row, column in itertools.product(
        range(batches), range(rows), range(columns)
    ):
        values = pools[batch, :, column]
        others = np.delete(values, row)
        value = values[row]
        tail = tails[column]
        if reducer == ECDF:
            twice_midrank = 2 * int(np.count_nonzero(others < value)) + int(
                np.count_nonzero(others == value)
            )
            denominator = rows - 1
            scores[batch, row, column] = {
                "two-sided": abs(twice_midrank - denominator),
                "upper": twice_midrank,
                "lower": 2 * denominator - twice_midrank,
            }[tail]
        else:
            center = float(np.median(others))
            scores[batch, row, column] = {
                "two-sided": abs(float(value) - center),
                "upper": float(value),
                "lower": -float(value),
            }[tail]
    output = np.empty((batches, rows, columns), dtype=np.int64)
    for batch, row, column in itertools.product(
        range(batches), range(rows), range(columns)
    ):
        output[batch, row, column] = sum(
            scores[batch, other, column] >= scores[batch, row, column]
            for other in range(rows)
        )
    return output


def _slow_family(local: np.ndarray, query_index: int) -> np.ndarray:
    output = []
    for batch in range(local.shape[0]):
        minimum = np.min(local[batch], axis=1)
        product = [math.prod(map(int, row)) for row in local[batch]]
        output.append(
            (
                sum(value <= minimum[query_index] for value in minimum),
                sum(value <= product[query_index] for value in product),
            )
        )
    return np.asarray(output, dtype=np.int64)


def test_registered_templates_have_exact_support_and_weighted_unit_energy() -> None:
    templates = template_bank()
    assert len(templates) == 5
    assert {template.template_id for template in templates} == {
        "Q_AXIAL",
        "O_PLANAR",
        "MIX_AXIAL",
        "MIX_PLANAR",
        "MIX_GENERIC",
    }
    for template in templates:
        assert harmonic_energy(template.coefficients) == pytest.approx(
            1.0, rel=0.0, abs=5.0e-14
        )
        assert np.array_equal(template.coefficients[12:], np.zeros(20))
        assert template.coefficients.flags.writeable is False


def test_orientation_bank_is_deterministic_proper_and_composes_in_the_registered_basis() -> None:
    uniforms = orientation_uniforms()
    rotations = orientation_bank()
    assert uniforms.shape == (32, 3)
    assert np.all((uniforms > 0.0) & (uniforms < 1.0))
    assert rotations.shape == (32, 3, 3)
    for rotation in rotations:
        assert np.allclose(rotation @ rotation.T, np.eye(3), rtol=0, atol=5e-13)
        assert np.linalg.det(rotation) == pytest.approx(1.0, rel=0, abs=5e-13)
    left, right = rotations[3], rotations[17]
    for ell in (2, 3):
        representation = rotation_matrix(ell, left @ right)
        composed = rotation_matrix(ell, left) @ rotation_matrix(ell, right)
        assert np.allclose(representation, composed, rtol=0, atol=5e-13)
        weights = np.diag(metric(ell))
        assert np.allclose(
            representation.T @ weights @ representation,
            weights,
            rtol=0,
            atol=5e-13,
        )


def test_zero_injection_is_exact_and_positive_injection_never_leaks_into_ell4_or_ell5() -> None:
    rng = np.random.default_rng(808)
    rows = rng.normal(size=(7, 32))
    template = template_bank()[-1]
    rotation = orientation_bank()[9]
    zero = inject(rows, template, rotation, 0.0, 2.5)
    assert np.array_equal(zero, rows)
    assert zero is not rows
    positive = inject(rows, template, rotation, 4.0, 2.5)
    assert np.array_equal(positive[:, 12:], rows[:, 12:])
    rotated = rotate_template(template, rotation)
    assert np.array_equal(rotated[12:], np.zeros(20))


@pytest.mark.parametrize("reducer", [LEGACY, ECDF])
def test_integer_local_and_family_ranks_match_independent_tie_oracles(reducer: str) -> None:
    pools = np.asarray(
        [
            [[0, 4, 2], [0, 1, 8], [2, 1, 2], [5, 3, 0], [2, 3, 4]],
            [[3, 0, 1], [3, 9, 1], [1, 4, 7], [8, 4, 7], [2, 0, 5]],
        ],
        dtype=float,
    )
    tails = ("two-sided", "upper", "lower")
    local = local_numerators(pools, tails, reducer)
    expected_local = _slow_local_numerators(pools, tails, reducer)
    assert np.array_equal(local, expected_local)
    family = family_numerators(local, 0)
    assert np.array_equal(family, _slow_family(expected_local, 0))
    assert family.dtype == np.dtype("int64")


def test_score_queries_uses_exact_201_row_pool_and_exact_integer_fisher_product() -> None:
    rng = np.random.default_rng(812)
    reference = rng.integers(-4, 5, size=(CALIBRATION_COUNT, 4)).astype(float)
    queries = rng.integers(-4, 5, size=(3, 4)).astype(float)
    for reducer in (LEGACY, ECDF):
        actual = score_queries(
            reference, queries, ("two-sided", "upper", "lower", "two-sided"), reducer
        )
        pools = np.concatenate(
            (queries[:, None, :], np.broadcast_to(reference, (3, 200, 4))), axis=1
        )
        local = _slow_local_numerators(
            pools, ("two-sided", "upper", "lower", "two-sided"), reducer
        )
        assert np.array_equal(actual, _slow_family(local, 0))
        assert np.all((actual >= 1) & (actual <= 201))


def test_registered_ids_are_disjoint_from_calibration_and_observation() -> None:
    paired = tuple(f"{index:05d}" for index in range(300))
    cmbonly = tuple(f"{index:05d}" for index in range(1000) if index != 970)
    calibration, paired_evaluation = split_indices(paired, "paired300")
    calibration2, cmb_evaluation = split_indices(cmbonly, "cmbonly999")
    assert np.array_equal(calibration, np.arange(200))
    assert np.array_equal(calibration2, np.arange(200))
    assert np.array_equal(paired_evaluation, np.arange(200, 300))
    assert len(cmb_evaluation) == 799
    assert cmbonly[cmb_evaluation[-1]] == "00999"
    assert "00970" not in cmbonly
    with pytest.raises(ValueError, match="inventory|observation"):
        split_indices(("PLANCK-PR3-SMICA-OBSERVED", *paired[1:]), "paired300")


def test_reference_scale_and_threshold_crossings_are_predeclared_and_noninterpolating() -> None:
    carriers = np.ones((200, 32), dtype=float)
    expected = math.sqrt(float(np.sum(np.r_[metric(2), metric(3)])) / (4 * math.pi))
    assert reference_scale(carriers) == pytest.approx(expected, rel=0, abs=1e-15)
    assert AMPLITUDES == (0.0, 0.25, 0.5, 1.0, 2.0, 4.0, 8.0)
    result = threshold_crossings(AMPLITUDES, [0.1, 0.6, 0.4, 0.7, 0.95, 0.8, 0.99], 0.5)
    assert len(result["crossings"]) == 3
    assert result["monotonic_non_decreasing"] is False
    assert result["interpolation_or_extrapolation_performed"] is False
    assert COMBINERS == (
        "MIN_LOCAL_P_V1",
        "EXACT_INTEGER_FISHER_PRODUCT_FINITE_POOL_V1",
    )
