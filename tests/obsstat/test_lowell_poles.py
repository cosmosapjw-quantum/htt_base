from __future__ import annotations

import math
import os
from pathlib import Path
import subprocess
import sys

import numpy as np
import pytest
from scipy.linalg import expm

from obsstat.lowell_poles import (
    AntipodalAxis,
    LowEllPoleEstimate,
    MIN_NUMERICAL_GAP_TOLERANCE,
    PoleDefinition,
    PoleStatus,
    angular_momentum_power_tensor,
    estimate_lowell_pole,
    mean_squared_multipole_alignment,
)


REPO_ROOT = Path(__file__).resolve().parents[2]


def _alm_mapping(ell: int, coefficients: np.ndarray) -> dict[tuple[int, int], complex]:
    return {
        (ell, m): complex(coefficients[m + ell])
        for m in range(-ell, ell + 1)
    }


def _m_zero(ell: int) -> np.ndarray:
    coefficients = np.zeros(2 * ell + 1, dtype=np.complex128)
    coefficients[ell] = 1.0
    return coefficients


def _real_sectoral(ell: int) -> np.ndarray:
    coefficients = np.zeros(2 * ell + 1, dtype=np.complex128)
    coefficients[0] = (-1) ** ell
    coefficients[-1] = 1.0
    return coefficients


def _random_real_alm(ell: int, rng: np.random.Generator) -> np.ndarray:
    coefficients = np.zeros(2 * ell + 1, dtype=np.complex128)
    coefficients[ell] = rng.normal()
    for m in range(1, ell + 1):
        positive = rng.normal() + 1.0j * rng.normal()
        coefficients[ell + m] = positive
        coefficients[ell - m] = ((-1) ** m) * np.conj(positive)
    return coefficients


def _generators(ell: int) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    m_values = np.arange(-ell, ell + 1, dtype=float)
    raising = np.zeros((2 * ell + 1, 2 * ell + 1), dtype=np.complex128)
    for index, m_value in enumerate(m_values[:-1]):
        raising[index + 1, index] = np.sqrt(
            ell * (ell + 1) - m_value * (m_value + 1.0)
        )
    lowering = raising.T.conj()
    return (
        (raising + lowering) / 2.0,
        (raising - lowering) / (2.0j),
        np.diag(m_values).astype(np.complex128),
    )


def _rotate_alm(
    coefficients: np.ndarray,
    ell: int,
    alpha: float,
    beta: float,
    gamma: float,
) -> np.ndarray:
    _, j_y, j_z = _generators(ell)
    operator = (
        expm(-1.0j * alpha * j_z)
        @ expm(-1.0j * beta * j_y)
        @ expm(-1.0j * gamma * j_z)
    )
    return operator @ coefficients


def _rotation_3d(alpha: float, beta: float, gamma: float) -> np.ndarray:
    def rotate_z(angle: float) -> np.ndarray:
        cosine, sine = math.cos(angle), math.sin(angle)
        return np.asarray(
            [[cosine, -sine, 0.0], [sine, cosine, 0.0], [0.0, 0.0, 1.0]]
        )

    cosine, sine = math.cos(beta), math.sin(beta)
    rotate_y = np.asarray(
        [[cosine, 0.0, sine], [0.0, 1.0, 0.0], [-sine, 0.0, cosine]]
    )
    return rotate_z(alpha) @ rotate_y @ rotate_z(gamma)


def _pole_estimate(
    ell: int,
    axis: AntipodalAxis | None,
    *,
    definition: PoleDefinition = PoleDefinition.MAX_ANGULAR_MOMENTUM,
) -> LowEllPoleEstimate:
    if axis is None:
        return LowEllPoleEstimate(
            ell=ell,
            definition=definition,
            status=PoleStatus.UNDETERMINED,
            axis=None,
            eigenvalues=(0.2, 0.4, 0.4),
            selection_gap=0.0,
            gap_tolerance=MIN_NUMERICAL_GAP_TOLERANCE,
        )
    selection_gap = {
        PoleDefinition.MAX_ANGULAR_MOMENTUM: 0.3,
        PoleDefinition.MIN_ANGULAR_MOMENTUM: 0.2,
        PoleDefinition.ANISOTROPY_TENSOR: 1.0 / 30.0,
    }[definition]
    return LowEllPoleEstimate(
        ell=ell,
        definition=definition,
        status=PoleStatus.IDENTIFIED,
        axis=axis,
        eigenvalues=(0.1, 0.3, 0.6),
        selection_gap=selection_gap,
        gap_tolerance=MIN_NUMERICAL_GAP_TOLERANCE,
    )


def test_mean_squared_multipole_alignment_matches_analytic_axes() -> None:
    x_axis = AntipodalAxis((1.0, 0.0, 0.0))
    y_axis = AntipodalAxis((0.0, 1.0, 0.0))
    z_axis = AntipodalAxis((0.0, 0.0, 1.0))
    sixty_deg = AntipodalAxis((0.5, math.sqrt(3.0) / 2.0, 0.0))

    assert mean_squared_multipole_alignment(
        estimates=(
            _pole_estimate(2, x_axis),
            _pole_estimate(3, AntipodalAxis((-1.0, 0.0, 0.0))),
            _pole_estimate(4, AntipodalAxis((2.0, 0.0, 0.0))),
        )
    ) == pytest.approx(1.0)
    assert mean_squared_multipole_alignment(
        estimates=(_pole_estimate(2, x_axis), _pole_estimate(3, sixty_deg))
    ) == pytest.approx(0.25)
    assert mean_squared_multipole_alignment(
        estimates=(
            _pole_estimate(2, x_axis),
            _pole_estimate(3, y_axis),
            _pole_estimate(4, z_axis),
        )
    ) == pytest.approx(0.0)


def test_multipole_alignment_is_rotation_sign_and_order_invariant() -> None:
    estimates = (
        _pole_estimate(2, AntipodalAxis((1.0, 0.0, 0.0))),
        _pole_estimate(
            3, AntipodalAxis((0.5, math.sqrt(3.0) / 2.0, 0.0))
        ),
        _pole_estimate(4, AntipodalAxis((0.0, 0.0, 1.0))),
        _pole_estimate(5, AntipodalAxis((0.0, 1.0, 0.0))),
    )
    baseline = mean_squared_multipole_alignment(estimates=estimates)
    assert baseline == pytest.approx(1.0 / 6.0)

    rotation = _rotation_3d(0.31, -0.47, 0.83)
    permutation = (estimates[2], estimates[0], estimates[3], estimates[1])
    transformed: list[LowEllPoleEstimate] = []
    for estimate, sign in zip(permutation, (-1.0, 1.0, -1.0, 1.0)):
        assert estimate.axis is not None
        rotated = sign * rotation @ np.asarray(estimate.axis.representative)
        transformed.append(
            _pole_estimate(
                estimate.ell,
                AntipodalAxis(tuple(float(value) for value in rotated)),
            )
        )
    assert mean_squared_multipole_alignment(
        estimates=transformed
    ) == pytest.approx(baseline, abs=2.0e-15)


def test_multipole_alignment_propagates_undetermined_poles() -> None:
    assert mean_squared_multipole_alignment(
        estimates=(
            _pole_estimate(2, AntipodalAxis((1.0, 0.0, 0.0))),
            _pole_estimate(3, AntipodalAxis((0.0, 1.0, 0.0))),
            _pole_estimate(4, None),
        )
    ) is None


def test_multipole_alignment_rejects_ambiguous_requests_before_abstaining() -> None:
    first = _pole_estimate(2, AntipodalAxis((1.0, 0.0, 0.0)))
    undetermined = _pole_estimate(2, None)
    mixed = _pole_estimate(
        3,
        AntipodalAxis((0.0, 1.0, 0.0)),
        definition=PoleDefinition.MIN_ANGULAR_MOMENTUM,
    )

    with pytest.raises(ValueError, match="at least two"):
        mean_squared_multipole_alignment(estimates=())
    with pytest.raises(ValueError, match="at least two"):
        mean_squared_multipole_alignment(estimates=(first,))
    with pytest.raises(ValueError, match="at least two"):
        mean_squared_multipole_alignment(estimates=(undetermined,))
    with pytest.raises(TypeError, match="LowEllPoleEstimate"):
        mean_squared_multipole_alignment(
            estimates=(first, object())  # type: ignore[arg-type]
        )
    with pytest.raises(ValueError, match="same pole definition"):
        mean_squared_multipole_alignment(estimates=(first, mixed))
    with pytest.raises(ValueError, match="same pole definition"):
        mean_squared_multipole_alignment(estimates=(undetermined, mixed))
    with pytest.raises(ValueError, match="distinct ell"):
        mean_squared_multipole_alignment(estimates=(first, undetermined))


def test_antipodal_axis_makes_sign_invariance_explicit() -> None:
    positive = AntipodalAxis((2.0, 0.0, 0.0))
    negative = AntipodalAxis((-1.0, 0.0, 0.0))
    orthogonal = AntipodalAxis((0.0, 1.0, 0.0))

    assert positive.representative == (1.0, 0.0, 0.0)
    assert positive == negative
    assert hash(positive) == hash(negative)
    assert positive.abs_dot(negative) == pytest.approx(1.0)
    assert positive.separation_deg(negative) == pytest.approx(0.0)
    assert positive.separation_deg(orthogonal) == pytest.approx(90.0)
    with pytest.raises(TypeError, match="AntipodalAxis"):
        positive.abs_dot(np.asarray([-1.0, 0.0, 0.0]))  # type: ignore[arg-type]


def test_pole_estimate_constructor_cannot_bypass_gap_abstention() -> None:
    with pytest.raises(ValueError, match="selection gap"):
        LowEllPoleEstimate(
            ell=2,
            definition=PoleDefinition.MAX_ANGULAR_MOMENTUM,
            status=PoleStatus.IDENTIFIED,
            axis=AntipodalAxis((1.0, 0.0, 0.0)),
            eigenvalues=(0.2, 0.4, 0.4),
            selection_gap=MIN_NUMERICAL_GAP_TOLERANCE,
            gap_tolerance=MIN_NUMERICAL_GAP_TOLERANCE,
        )


def test_analytic_zonal_and_sectoral_modes_select_or_abstain() -> None:
    zonal = _alm_mapping(2, _m_zero(2))
    np.testing.assert_allclose(
        angular_momentum_power_tensor(alm_by_lm=zonal, ell=2),
        np.diag([0.5, 0.5, 0.0]),
        atol=1.0e-14,
    )

    zonal_min = estimate_lowell_pole(
        alm_by_lm=zonal,
        ell=2,
        definition=PoleDefinition.MIN_ANGULAR_MOMENTUM,
        gap_tolerance=MIN_NUMERICAL_GAP_TOLERANCE,
    )
    zonal_max = estimate_lowell_pole(
        alm_by_lm=zonal,
        ell=2,
        definition=PoleDefinition.MAX_ANGULAR_MOMENTUM,
        gap_tolerance=MIN_NUMERICAL_GAP_TOLERANCE,
    )
    zonal_anisotropy = estimate_lowell_pole(
        alm_by_lm=zonal,
        ell=2,
        definition=PoleDefinition.ANISOTROPY_TENSOR,
        gap_tolerance=MIN_NUMERICAL_GAP_TOLERANCE,
    )
    assert zonal_min.axis is not None
    assert zonal_min.axis.abs_dot(AntipodalAxis((0.0, 0.0, 1.0))) == pytest.approx(1.0)
    assert zonal_anisotropy.axis is not None
    assert zonal_anisotropy.axis.abs_dot(zonal_min.axis) == pytest.approx(1.0)
    assert zonal_max.status is PoleStatus.UNDETERMINED
    assert zonal_max.axis is None

    sectoral = _alm_mapping(2, _real_sectoral(2))
    np.testing.assert_allclose(
        angular_momentum_power_tensor(alm_by_lm=sectoral, ell=2),
        np.diag([1.0 / 6.0, 1.0 / 6.0, 2.0 / 3.0]),
        atol=1.0e-14,
    )
    sectoral_max = estimate_lowell_pole(
        alm_by_lm=sectoral,
        ell=2,
        definition=PoleDefinition.MAX_ANGULAR_MOMENTUM,
        gap_tolerance=MIN_NUMERICAL_GAP_TOLERANCE,
    )
    sectoral_min = estimate_lowell_pole(
        alm_by_lm=sectoral,
        ell=2,
        definition=PoleDefinition.MIN_ANGULAR_MOMENTUM,
        gap_tolerance=MIN_NUMERICAL_GAP_TOLERANCE,
    )
    sectoral_anisotropy = estimate_lowell_pole(
        alm_by_lm=sectoral,
        ell=2,
        definition=PoleDefinition.ANISOTROPY_TENSOR,
        gap_tolerance=MIN_NUMERICAL_GAP_TOLERANCE,
    )
    assert sectoral_max.axis is not None
    assert sectoral_max.axis.abs_dot(
        AntipodalAxis((0.0, 0.0, 1.0))
    ) == pytest.approx(1.0)
    assert sectoral_anisotropy.axis is not None
    assert sectoral_anisotropy.axis.abs_dot(sectoral_max.axis) == pytest.approx(1.0)
    assert sectoral_min.status is PoleStatus.UNDETERMINED
    assert sectoral_min.axis is None


def test_gap_threshold_is_inclusive_and_never_leaks_a_tied_eigenvector() -> None:
    coefficients = _m_zero(2)
    coefficients[0] = 1.0e-6
    coefficients[-1] = 1.0e-6
    alm = _alm_mapping(2, coefficients)
    probe = estimate_lowell_pole(
        alm_by_lm=alm,
        ell=2,
        definition=PoleDefinition.MAX_ANGULAR_MOMENTUM,
        gap_tolerance=MIN_NUMERICAL_GAP_TOLERANCE,
    )
    assert probe.status is PoleStatus.IDENTIFIED
    assert probe.selection_gap > 0.0

    below = estimate_lowell_pole(
        alm_by_lm=alm,
        ell=2,
        definition=PoleDefinition.MAX_ANGULAR_MOMENTUM,
        gap_tolerance=math.nextafter(probe.selection_gap, 0.0),
    )
    at_threshold = estimate_lowell_pole(
        alm_by_lm=alm,
        ell=2,
        definition=PoleDefinition.MAX_ANGULAR_MOMENTUM,
        gap_tolerance=probe.selection_gap,
    )
    assert below.status is PoleStatus.IDENTIFIED
    assert below.axis is not None
    assert at_threshold.status is PoleStatus.UNDETERMINED
    assert at_threshold.axis is None


def test_anisotropy_extreme_branch_tie_abstains() -> None:
    coefficients = _m_zero(2)
    branch_tie_amplitude = math.sqrt(2.0) - math.sqrt(6.0) / 2.0
    coefficients[0] = branch_tie_amplitude
    coefficients[-1] = branch_tie_amplitude
    alm = _alm_mapping(2, coefficients)

    tensor = angular_momentum_power_tensor(alm_by_lm=alm, ell=2)
    eigenvalues = np.linalg.eigvalsh(tensor)
    assert eigenvalues[1] == pytest.approx(1.0 / 3.0, abs=1.0e-14)

    anisotropy = estimate_lowell_pole(
        alm_by_lm=alm,
        ell=2,
        definition=PoleDefinition.ANISOTROPY_TENSOR,
        gap_tolerance=2.0e-14,
    )
    maximum = estimate_lowell_pole(
        alm_by_lm=alm,
        ell=2,
        definition=PoleDefinition.MAX_ANGULAR_MOMENTUM,
        gap_tolerance=2.0e-14,
    )
    minimum = estimate_lowell_pole(
        alm_by_lm=alm,
        ell=2,
        definition=PoleDefinition.MIN_ANGULAR_MOMENTUM,
        gap_tolerance=2.0e-14,
    )
    assert anisotropy.status is PoleStatus.UNDETERMINED
    assert anisotropy.axis is None
    assert maximum.status is PoleStatus.IDENTIFIED
    assert minimum.status is PoleStatus.IDENTIFIED


def test_exact_degeneracies_remain_undetermined_after_rotation() -> None:
    branch_tie = _m_zero(2)
    branch_tie[0] = math.sqrt(2.0) - math.sqrt(6.0) / 2.0
    branch_tie[-1] = branch_tie[0]
    fixtures = (
        (_m_zero(2), PoleDefinition.MAX_ANGULAR_MOMENTUM),
        (_real_sectoral(2), PoleDefinition.MIN_ANGULAR_MOMENTUM),
        (branch_tie, PoleDefinition.ANISOTROPY_TENSOR),
    )
    rng = np.random.default_rng(1251)

    for coefficients, definition in fixtures:
        before = estimate_lowell_pole(
            alm_by_lm=_alm_mapping(2, coefficients),
            ell=2,
            definition=definition,
            gap_tolerance=MIN_NUMERICAL_GAP_TOLERANCE,
        )
        assert before.status is PoleStatus.UNDETERMINED
        assert before.axis is None
        for _ in range(20):
            angles = tuple(float(value) for value in rng.uniform(-math.pi, math.pi, 3))
            rotated = _rotate_alm(coefficients, 2, *angles)
            after = estimate_lowell_pole(
                alm_by_lm=_alm_mapping(2, rotated),
                ell=2,
                definition=definition,
                gap_tolerance=MIN_NUMERICAL_GAP_TOLERANCE,
            )
            assert after.status is PoleStatus.UNDETERMINED
            assert after.axis is None
            np.testing.assert_allclose(
                after.eigenvalues, before.eigenvalues, rtol=0.0, atol=2.0e-12
            )
            assert after.selection_gap == pytest.approx(
                before.selection_gap, rel=0.0, abs=2.0e-12
            )


def test_active_y_quarter_turn_takes_zonal_axis_from_z_to_x() -> None:
    coefficients = _m_zero(2)
    rotated = _rotate_alm(coefficients, 2, 0.0, math.pi / 2.0, 0.0)
    estimate = estimate_lowell_pole(
        alm_by_lm=_alm_mapping(2, rotated),
        ell=2,
        definition=PoleDefinition.MIN_ANGULAR_MOMENTUM,
        gap_tolerance=1.0e-12,
    )
    assert estimate.axis is not None
    assert estimate.axis.abs_dot(AntipodalAxis((1.0, 0.0, 0.0))) == pytest.approx(
        1.0, abs=1.0e-14
    )


def test_tensor_and_pole_are_invariant_to_extreme_amplitude_rescaling() -> None:
    coefficients = np.asarray(
        [
            0.4 - 0.2j,
            -0.3 - 0.1j,
            0.7,
            0.3 - 0.1j,
            0.4 + 0.2j,
        ],
        dtype=np.complex128,
    )
    baseline_tensor = angular_momentum_power_tensor(
        alm_by_lm=_alm_mapping(2, coefficients), ell=2
    )
    baseline = estimate_lowell_pole(
        alm_by_lm=_alm_mapping(2, coefficients),
        ell=2,
        definition=PoleDefinition.ANISOTROPY_TENSOR,
        gap_tolerance=1.0e-12,
    )
    assert baseline.axis is not None

    for scale in (1.0e-200, 1.0, 1.0e200):
        scaled = coefficients * scale
        tensor = angular_momentum_power_tensor(
            alm_by_lm=_alm_mapping(2, scaled), ell=2
        )
        estimate = estimate_lowell_pole(
            alm_by_lm=_alm_mapping(2, scaled),
            ell=2,
            definition=PoleDefinition.ANISOTROPY_TENSOR,
            gap_tolerance=1.0e-12,
        )
        np.testing.assert_allclose(tensor, baseline_tensor, rtol=0.0, atol=2.0e-15)
        assert estimate.axis is not None
        assert estimate.axis.abs_dot(baseline.axis) == pytest.approx(
            1.0, abs=2.0e-15
        )
        assert estimate.selection_gap == pytest.approx(
            baseline.selection_gap, rel=0.0, abs=2.0e-15
        )


def test_ell_one_to_five_has_100_case_rotation_covariance() -> None:
    rng = np.random.default_rng(251)
    worst_axis_error = 0.0
    case_count = 0
    identified_counts = {definition: 0 for definition in PoleDefinition}

    for ell in range(1, 6):
        for _ in range(20):
            coefficients = _random_real_alm(ell, rng)
            angles = tuple(float(value) for value in rng.uniform(-math.pi, math.pi, 3))
            rotated = _rotate_alm(coefficients, ell, *angles)
            rotation = _rotation_3d(*angles)
            original_mapping = _alm_mapping(ell, coefficients)
            rotated_mapping = _alm_mapping(ell, rotated)

            for definition in PoleDefinition:
                before = estimate_lowell_pole(
                    alm_by_lm=original_mapping,
                    ell=ell,
                    definition=definition,
                    gap_tolerance=1.0e-12,
                )
                after = estimate_lowell_pole(
                    alm_by_lm=rotated_mapping,
                    ell=ell,
                    definition=definition,
                    gap_tolerance=1.0e-12,
                )
                assert after.status is before.status
                np.testing.assert_allclose(
                    after.eigenvalues, before.eigenvalues, rtol=0.0, atol=2.0e-12
                )
                assert after.selection_gap == pytest.approx(
                    before.selection_gap, rel=0.0, abs=2.0e-12
                )
                if before.axis is None:
                    assert after.axis is None
                    continue
                assert after.axis is not None
                identified_counts[definition] += 1
                expected = rotation @ np.asarray(before.axis.representative)
                observed = np.asarray(after.axis.representative)
                error = 1.0 - abs(float(np.dot(expected, observed)))
                worst_axis_error = max(worst_axis_error, error)
            case_count += 1

    assert case_count == 100
    assert all(count > 0 for count in identified_counts.values())
    assert worst_axis_error < 1.0e-9


@pytest.mark.parametrize(
    "gap_tolerance",
    [-1.0, 0.0, MIN_NUMERICAL_GAP_TOLERANCE / 2.0, math.inf, math.nan],
)
def test_gap_tolerance_must_clear_numerical_floor(gap_tolerance: float) -> None:
    with pytest.raises(ValueError, match="gap_tolerance"):
        estimate_lowell_pole(
            alm_by_lm=_alm_mapping(2, _m_zero(2)),
            ell=2,
            definition=PoleDefinition.MIN_ANGULAR_MOMENTUM,
            gap_tolerance=gap_tolerance,
        )


def test_invalid_alm_inputs_are_rejected() -> None:
    valid = _alm_mapping(2, _m_zero(2))
    missing = dict(valid)
    missing.pop((2, -1))
    with pytest.raises(ValueError, match="missing m"):
        angular_momentum_power_tensor(alm_by_lm=missing, ell=2)

    not_real = dict(valid)
    not_real[(2, 1)] = 1.0j
    with pytest.raises(ValueError, match="reality condition"):
        angular_momentum_power_tensor(alm_by_lm=not_real, ell=2)

    for scale in (1.0e-200, 1.0, 1.0e200):
        scaled_violation = {
            (2, m): 0.0j for m in range(-2, 3)
        }
        scaled_violation[(2, 0)] = scale
        scaled_violation[(2, 1)] = 1.0j * scale
        with pytest.raises(ValueError, match="reality condition"):
            angular_momentum_power_tensor(alm_by_lm=scaled_violation, ell=2)

    zero = {key: 0.0j for key in valid}
    with pytest.raises(ValueError, match="zero norm"):
        angular_momentum_power_tensor(alm_by_lm=zero, ell=2)

    not_finite = dict(valid)
    not_finite[(2, 0)] = complex(math.nan, 0.0)
    with pytest.raises(ValueError, match="finite"):
        angular_momentum_power_tensor(alm_by_lm=not_finite, ell=2)


def test_obsstat_import_aliases_share_the_lowell_pole_types() -> None:
    env = os.environ.copy()
    env.pop("PYTHONPATH", None)
    snippets = [
        """
import obsstat
import obsstat.lowell_poles as top_level
import htt.obsstat.lowell_poles as htt_level
assert top_level is htt_level
assert obsstat.mean_squared_multipole_alignment is top_level.mean_squared_multipole_alignment
assert top_level.AntipodalAxis is htt_level.AntipodalAxis
assert top_level.mean_squared_multipole_alignment is htt_level.mean_squared_multipole_alignment
""",
        """
import htt.obsstat.lowell_poles as htt_level
import obsstat.lowell_poles as top_level
assert top_level is htt_level
assert top_level.LowEllPoleEstimate is htt_level.LowEllPoleEstimate
""",
    ]
    for snippet in snippets:
        completed = subprocess.run(
            [sys.executable, "-c", snippet],
            cwd=REPO_ROOT,
            env=env,
            text=True,
            capture_output=True,
            check=False,
        )
        assert completed.returncode == 0, completed.stderr
