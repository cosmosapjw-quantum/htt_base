"""RED/GREEN contracts for the WU-011 processed coefficient Jacobian.

The public scientific tensor is ordered as
``(beta_axis, retained_output, source_mode)``.  Its source registry is the
physical monopole temperature followed by the scientific stored-real
``ell=1..6`` coefficients.  The retained registry is the scientific stored-real
``ell=2..5`` carrier.

The exact scientific monopole column is structurally zero after the
simultaneous ``ell=0,1`` nuisance solve.  HEALPix replay leakage is retained in
a separately typed numerical tensor and must not be promoted to monopole
identifiability or contracted by the default scientific predictor.
"""

from __future__ import annotations

import math

import numpy as np
import pytest


hp = pytest.importorskip(
    "healpy",
    reason="healpy is required by the WU-011 Jacobian contract",
)

from obsstat.planck_pr3_operator import build_joint_cutsky_operator  # noqa: E402
from obsstat.processed_boost_linearization import (  # noqa: E402
    evaluate_processed_linear_response,
)
from obsstat.processed_boost_operator import (  # noqa: E402
    ProcessedBoostOperator,
    evaluate_processed_boost,
)
from obsstat.processed_boost_response import (  # noqa: E402
    PositiveAbsoluteSkySpec,
    healpix_sky_directions,
)


pytestmark = pytest.mark.requires_healpy


def _api():
    try:
        from obsstat import processed_boost_jacobian as api
    except ImportError as exc:
        pytest.fail(f"WU-011 Jacobian API missing: {exc}", pytrace=False)
    return api


def _operator() -> ProcessedBoostOperator:
    nside = 8
    processing_lmax = 12
    z = healpix_sky_directions(nside)[:, 2]
    mask = np.clip((z + 0.45) / 0.9, 0.0, 1.0)
    joint = build_joint_cutsky_operator(mask, lmin=0, lmax=5, retained_lmin=2)
    ell = np.arange(processing_lmax + 1, dtype=float)
    source_beam = np.exp(-0.5 * ell * (ell + 1.0) * 0.075**2)
    source_pixel = np.exp(-0.5 * ell * (ell + 1.0) * 0.025**2)
    target_beam = np.exp(-0.5 * ell * (ell + 1.0) * 0.11**2)
    target_pixel = np.exp(-0.5 * ell * (ell + 1.0) * 0.04**2)
    return ProcessedBoostOperator.from_components(
        mask=mask,
        joint_operator=joint,
        processing_lmax=processing_lmax,
        source_beam=source_beam,
        source_pixel_window=source_pixel,
        target_beam=target_beam,
        target_pixel_window=target_pixel,
    )


def _source_sky() -> PositiveAbsoluteSkySpec:
    coefficients = np.zeros(48, dtype=float)
    coefficients[3:8] = (0.018, -0.011, 0.007, 0.013, -0.009)
    ell5_start = sum(2 * ell + 1 for ell in range(1, 5))
    coefficients[ell5_start] = 0.006
    coefficients[ell5_start + 5] = -0.004
    ell6_start = sum(2 * ell + 1 for ell in range(1, 6))
    coefficients[ell6_start + 2] = 0.002
    return PositiveAbsoluteSkySpec(2.7255, coefficients, 6, "K_CMB")


def _source_basis_pair(
    source_index: int,
    *,
    reference_monopole: float,
    source_step: float,
) -> tuple[PositiveAbsoluteSkySpec, PositiveAbsoluteSkySpec]:
    if not 0 <= source_index < 49:
        raise AssertionError("source index outside the frozen 49-coordinate registry")
    plus_coefficients = np.zeros(48, dtype=float)
    minus_coefficients = np.zeros(48, dtype=float)
    plus_monopole = reference_monopole
    minus_monopole = reference_monopole
    if source_index == 0:
        plus_monopole += source_step
        minus_monopole -= source_step
    else:
        plus_coefficients[source_index - 1] = source_step
        minus_coefficients[source_index - 1] = -source_step
    return (
        PositiveAbsoluteSkySpec(plus_monopole, plus_coefficients, 6, "K_CMB"),
        PositiveAbsoluteSkySpec(minus_monopole, minus_coefficients, 6, "K_CMB"),
    )


@pytest.fixture(scope="module")
def jacobian():
    return _api().build_processed_boost_jacobian(_operator())


def test_wu011_jacobian_has_typed_registries_metrics_and_decomposition(jacobian) -> None:
    api = _api()
    assert jacobian.tensor.shape == (3, 32, 49)
    assert jacobian.raw_replay_tensor.shape == (3, 32, 49)
    assert len(jacobian.source_registry) == 49
    assert len(jacobian.output_registry) == 32

    t0 = jacobian.source_registry[0]
    assert t0 == api.ScientificMode(0, 0, "REAL")
    assert t0.coordinate_role == "PHYSICAL_MONOPOLE_TEMPERATURE"
    assert t0.field_basis == "CONSTANT_ONE"
    assert t0.harmonic_adapter == "a00=sqrt(4*pi)*T0"

    assert jacobian.source_registry[36] == api.ScientificMode(6, 0, "REAL")
    assert jacobian.source_registry[-1] == api.ScientificMode(6, 6, "IMAG")
    assert jacobian.output_registry[0] == api.ScientificMode(2, 0, "REAL")
    assert jacobian.output_registry[-1] == api.ScientificMode(5, 5, "IMAG")

    assert jacobian.source_metric_diagonal.shape == (49,)
    assert jacobian.output_metric_diagonal.shape == (32,)
    assert jacobian.source_metric_diagonal[0] == pytest.approx(4.0 * math.pi)
    assert set(np.unique(jacobian.source_metric_diagonal[1:])) == {1.0, 2.0}
    assert set(np.unique(jacobian.output_metric_diagonal)) == {1.0, 2.0}

    assert jacobian.ell6_source_response_block.shape == (3, 32, 13)
    assert jacobian.ell6_expected_neighbor_l5_block.shape == (3, 32, 13)
    assert jacobian.ell6_cutsky_alias_residual.shape == (3, 32, 13)
    assert jacobian.ell6_decomposition_residual.shape == (3, 32, 13)
    np.testing.assert_allclose(
        jacobian.ell6_source_response_block,
        jacobian.ell6_expected_neighbor_l5_block
        + jacobian.ell6_cutsky_alias_residual
        + jacobian.ell6_decomposition_residual,
        rtol=5.0e-15,
        atol=5.0e-28,
    )
    assert np.linalg.norm(jacobian.ell6_expected_neighbor_l5_block) > 0.0
    assert np.linalg.norm(jacobian.ell6_cutsky_alias_residual) > 0.0


def test_wu011_jacobian_separates_scientific_null_from_replay_leakage(jacobian) -> None:
    assert np.count_nonzero(jacobian.tensor[:, :, 0]) == 0
    np.testing.assert_array_equal(
        jacobian.raw_replay_tensor[:, :, 0],
        jacobian.monopole_replay_leakage,
    )
    assert jacobian.combined_rank == 48
    assert math.isinf(jacobian.combined_condition_number)
    assert jacobian.nonmonopole_rank == 48
    assert np.isfinite(jacobian.nonmonopole_condition_number)
    assert jacobian.raw_combined_rank in {48, 49}
    assert len(jacobian.raw_combined_singular_values) == 49
    assert jacobian.monopole_replay_leakage_norm <= 5.0e-4
    assert jacobian.monopole_relative_to_nonmonopole_max <= 5.0e-4


def test_wu011_metric_whitened_diagnostics_are_invariantly_defined(jacobian) -> None:
    api = _api()
    stacked = jacobian.tensor.reshape(96, 49)
    expected = api.metric_whitened_matrix(
        stacked,
        source_metric_diagonal=jacobian.source_metric_diagonal,
        output_metric_diagonal=np.tile(jacobian.output_metric_diagonal, 3),
    )
    np.testing.assert_allclose(
        expected,
        jacobian.metric_whitened_stacked_matrix,
        rtol=0.0,
        atol=0.0,
    )
    assert jacobian.metric_whitened_rank == 48
    assert math.isinf(jacobian.metric_whitened_condition_number)
    assert np.isfinite(jacobian.metric_whitened_nonzero_condition_number)
    assert jacobian.metric_whitened_nonzero_condition_number >= 1.0

    source_scale = np.ones(49)
    source_scale[7] = 0.1
    transformed = stacked / source_scale[None, :]
    transformed_metric = jacobian.source_metric_diagonal / (source_scale * source_scale)
    transformed_whitened = api.metric_whitened_matrix(
        transformed,
        source_metric_diagonal=transformed_metric,
        output_metric_diagonal=np.tile(jacobian.output_metric_diagonal, 3),
    )
    np.testing.assert_allclose(
        np.linalg.svd(transformed_whitened, compute_uv=False),
        np.linalg.svd(expected, compute_uv=False),
        rtol=2.0e-13,
        atol=2.0e-13,
    )


def test_wu011_fullsky_reference_spectrum_is_sealed() -> None:
    api = _api()
    reference = api.full_sky_metric_reference()
    np.testing.assert_allclose(
        reference.sigma_squared_by_source_ell,
        np.array([8.0 / 3.0, 27.0 / 5.0, 13.0, 21.0, 125.0 / 11.0, 216.0 / 13.0]),
        rtol=0.0,
        atol=0.0,
    )
    assert reference.multiplicities == (3, 5, 7, 9, 11, 13)
    assert reference.anisotropy_rank == 48
    assert reference.structural_monopole_nullity == 1
    assert reference.nonzero_condition_number == pytest.approx(math.sqrt(63.0 / 8.0))


def test_wu011_scientific_and_replay_predictors_are_separate(jacobian) -> None:
    api = _api()
    source = _source_sky()
    beta = np.array([1.7e-3, -9.0e-4, 1.2e-3], dtype=float)
    scientific = api.predict_processed_linear_response(jacobian, source, beta)
    replay = api.predict_processed_replay_linear_response(jacobian, source, beta)
    direct = evaluate_processed_linear_response(source, _operator(), beta)

    replay_scale = max(np.linalg.norm(direct.retained_coefficients), np.finfo(float).tiny)
    replay_relative = np.linalg.norm(replay - direct.retained_coefficients) / replay_scale
    assert replay_relative <= 2.0e-8

    leakage = source.monopole_temperature * np.einsum(
        "i,io->o",
        beta,
        jacobian.monopole_replay_leakage,
        optimize=True,
    )
    np.testing.assert_allclose(
        replay - scientific,
        leakage,
        rtol=2.0e-11,
        atol=2.0e-13,
    )


def test_wu011_replay_jacobian_matches_a_centered_finite_boost_derivative(
    jacobian,
) -> None:
    api = _api()
    source = _source_sky()
    operator = _operator()
    direction = np.array([0.4, -0.2, 0.3], dtype=float)
    direction /= np.linalg.norm(direction)
    epsilon = 2.0e-3
    plus = evaluate_processed_boost(source, operator, epsilon * direction, mode="FINITE")
    minus = evaluate_processed_boost(source, operator, -epsilon * direction, mode="FINITE")
    centered = (plus.retained_coefficients - minus.retained_coefficients) / (2.0 * epsilon)
    predicted = api.predict_processed_replay_linear_response(jacobian, source, direction)
    scale = max(np.linalg.norm(centered), np.finfo(float).tiny)
    relative = np.linalg.norm(centered - predicted) / scale
    assert relative <= 5.0e-4


def test_wu011_all_147_registered_columns_match_centered_mixed_differences(
    jacobian,
) -> None:
    api = _api()
    operator = _operator()
    reference_monopole = jacobian.reference_monopole_temperature
    source_step = jacobian.basis_amplitude
    beta_step = 2.0e-3
    finite_tensor = np.empty_like(jacobian.raw_replay_tensor)

    for source_index in range(49):
        source_plus, source_minus = _source_basis_pair(
            source_index,
            reference_monopole=reference_monopole,
            source_step=source_step,
        )
        for axis, direction in enumerate(np.eye(3, dtype=float)):
            beta = beta_step * direction
            plus_plus = evaluate_processed_boost(
                source_plus, operator, beta, mode="FINITE"
            ).retained_coefficients
            minus_plus = evaluate_processed_boost(
                source_plus, operator, -beta, mode="FINITE"
            ).retained_coefficients
            plus_minus = evaluate_processed_boost(
                source_minus, operator, beta, mode="FINITE"
            ).retained_coefficients
            minus_minus = evaluate_processed_boost(
                source_minus, operator, -beta, mode="FINITE"
            ).retained_coefficients
            finite_tensor[axis, :, source_index] = (
                plus_plus - minus_plus - plus_minus + minus_minus
            ) / (4.0 * beta_step * source_step)

    output_metric = np.tile(jacobian.output_metric_diagonal, 3)
    finite_whitened = api.metric_whitened_matrix(
        finite_tensor.reshape(96, 49),
        source_metric_diagonal=jacobian.source_metric_diagonal,
        output_metric_diagonal=output_metric,
    )
    expected_whitened = api.metric_whitened_matrix(
        jacobian.raw_replay_tensor.reshape(96, 49),
        source_metric_diagonal=jacobian.source_metric_diagonal,
        output_metric_diagonal=output_metric,
    )
    residual = finite_whitened - expected_whitened
    relative_frobenius = np.linalg.norm(residual) / np.linalg.norm(expected_whitened)
    relative_maximum = np.max(np.abs(residual)) / np.max(np.abs(expected_whitened))
    assert relative_frobenius <= 8.0e-4
    assert relative_maximum <= 3.0e-3


def test_wu011_jacobian_arrays_are_content_bound_and_immutable(jacobian) -> None:
    arrays = (
        jacobian.tensor,
        jacobian.raw_replay_tensor,
        jacobian.monopole_replay_leakage,
        jacobian.source_metric_diagonal,
        jacobian.output_metric_diagonal,
        jacobian.metric_whitened_stacked_matrix,
        jacobian.ell6_source_response_block,
        jacobian.ell6_expected_neighbor_l5_block,
        jacobian.ell6_cutsky_alias_residual,
        jacobian.ell6_decomposition_residual,
    )
    assert jacobian.content_id.startswith("sha256:")
    assert all(not array.flags.writeable for array in arrays)
    with pytest.raises(ValueError):
        jacobian.tensor[0, 0, 0] = 1.0
