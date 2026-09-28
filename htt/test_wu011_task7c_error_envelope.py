from __future__ import annotations

import numpy as np
import pytest

from obsstat import processed_boost_error_envelope as api


def test_cartesian_family_loewner_envelope_bounds_every_unit_direction():
    rng = np.random.default_rng(20260902)
    family = rng.normal(size=(3, 5, 7))
    envelope = api.build_output_error_envelope(
        {"fullsky_cartesian": family},
        reference_operator_norm=10.0,
    )
    for _ in range(128):
        direction = rng.normal(size=3)
        direction /= np.linalg.norm(direction)
        error = np.einsum("i,imn->mn", direction, family)
        residual = envelope.output_covariance - error @ error.T
        assert np.linalg.eigvalsh(residual).min() >= -2e-12
        normalized = np.linalg.svd(
            envelope.inverse_square_root @ error, compute_uv=False
        )[0]
        assert normalized <= 1 + 2e-12


def test_additive_family_multiplier_bounds_a_sum_of_family_errors():
    rng = np.random.default_rng(7)
    first = rng.normal(size=(3, 4, 6))
    second = rng.normal(size=(2, 4, 6))
    envelope = api.build_output_error_envelope(
        {"fullsky": first, "resolution": second},
        reference_operator_norm=8.0,
    )
    b1 = np.array([1.0, -2.0, 3.0])
    b1 /= np.linalg.norm(b1)
    b2 = np.array([2.0, -1.0])
    b2 /= np.linalg.norm(b2)
    e1 = np.einsum("i,imn->mn", b1, first)
    e2 = np.einsum("i,imn->mn", b2, second)
    combined = e1 + e2
    normalized = np.linalg.svd(
        envelope.inverse_square_root @ combined, compute_uv=False
    )[0]
    assert normalized <= 1 + 2e-12


def test_weighted_family_radii_bound_the_declared_additive_error_class():
    rng = np.random.default_rng(20260903)
    first = rng.normal(size=(3, 4, 6))
    second = rng.normal(size=(2, 4, 6))
    radii = {"fullsky": 2.0, "resolution": 0.5}
    envelope = api.build_output_error_envelope(
        {"fullsky": first, "resolution": second},
        family_radii=radii,
        reference_operator_norm=8.0,
    )

    assert dict(envelope.family_radii) == radii
    assert envelope.total_family_radius == pytest.approx(2.5)
    assert envelope.perturbation_class == "additive_family_l2_balls"

    for _ in range(128):
        b1 = rng.normal(size=3)
        b1 *= radii["fullsky"] / np.linalg.norm(b1)
        b2 = rng.normal(size=2)
        b2 *= radii["resolution"] / np.linalg.norm(b2)
        combined = (
            np.einsum("i,imn->mn", b1, first)
            + np.einsum("i,imn->mn", b2, second)
        )
        normalized = np.linalg.svd(
            envelope.inverse_square_root @ combined,
            compute_uv=False,
        )[0]
        assert normalized <= 1 + 5e-12


def test_compensated_family_scaling_preserves_envelope_and_certificate():
    rng = np.random.default_rng(20260903)
    fullsky = rng.normal(size=(3, 4, 6)) * 0.03
    resolution = rng.normal(size=(2, 4, 6)) * 0.02
    signal = rng.normal(size=(4, 6))
    radii = {"fullsky": 2.0, "resolution": 0.5}
    reference_norm = np.linalg.norm(signal, 2)

    base_envelope = api.build_output_error_envelope(
        {"fullsky": fullsky, "resolution": resolution},
        family_radii=radii,
        reference_operator_norm=reference_norm,
    )
    base_certificate = api.certify_error_whitened_row_rank(
        signal,
        base_envelope,
    )

    for scale in (1.0e-6, 1.0e-3, 1.0e3, 1.0e6):
        transformed_envelope = api.build_output_error_envelope(
            {
                "fullsky": scale * fullsky,
                "resolution": resolution,
            },
            family_radii={
                "fullsky": radii["fullsky"] / scale,
                "resolution": radii["resolution"],
            },
            reference_operator_norm=reference_norm,
        )
        transformed_certificate = api.certify_error_whitened_row_rank(
            signal,
            transformed_envelope,
        )

        np.testing.assert_allclose(
            transformed_envelope.output_covariance,
            base_envelope.output_covariance,
            rtol=2.0e-12,
            atol=2.0e-12,
        )
        np.testing.assert_allclose(
            transformed_envelope.inverse_square_root,
            base_envelope.inverse_square_root,
            rtol=2.0e-11,
            atol=2.0e-11,
        )
        np.testing.assert_allclose(
            transformed_certificate.error_whitened_singular_values,
            base_certificate.error_whitened_singular_values,
            rtol=2.0e-11,
            atol=2.0e-11,
        )
        assert transformed_certificate.status is base_certificate.status
        assert (
            transformed_certificate.guaranteed_rank_lower_bound
            == base_certificate.guaranteed_rank_lower_bound
        )


def test_family_radius_registry_fails_closed():
    family = np.zeros((2, 3, 4))
    with pytest.raises(api.MatrixErrorEnvelopeError):
        api.build_output_error_envelope(
            {"a": family},
            family_radii={},
            reference_operator_norm=1.0,
        )
    with pytest.raises(api.MatrixErrorEnvelopeError):
        api.build_output_error_envelope(
            {"a": family},
            family_radii={"a": 1.0, "extra": 1.0},
            reference_operator_norm=1.0,
        )
    with pytest.raises(api.MatrixErrorEnvelopeError):
        api.build_output_error_envelope(
            {"a": family},
            family_radii={"a": 0.0},
            reference_operator_norm=1.0,
        )


def test_holdout_validation_detects_containment_and_escape():
    family = np.zeros((1, 2, 2))
    family[0] = 0.1 * np.eye(2)
    envelope = api.build_output_error_envelope(
        {"training": family},
        reference_operator_norm=1.0,
    )

    contained = api.validate_error_envelope_holdouts(
        {
            "resolution_holdout": np.stack(
                [0.05 * np.eye(2), 0.08 * np.eye(2)]
            )
        },
        envelope,
    )
    assert (
        contained.status
        is api.HoldoutValidationStatus.ALL_HOLDOUTS_CONTAINED
    )
    assert contained.all_contained
    assert contained.maximum_normalized_norm < 1.0

    escaped = api.validate_error_envelope_holdouts(
        {"resolution_holdout": np.stack([2.0 * np.eye(2)])},
        envelope,
    )
    assert escaped.status is api.HoldoutValidationStatus.HOLDOUT_ESCAPE
    assert escaped.all_contained is False
    assert escaped.maximum_normalized_norm > 1.0


def test_holdout_validation_shape_and_tolerance_fail_closed():
    family = np.zeros((1, 2, 2))
    family[0] = 0.1 * np.eye(2)
    envelope = api.build_output_error_envelope(
        {"training": family},
        reference_operator_norm=1.0,
    )
    with pytest.raises(api.MatrixErrorEnvelopeError):
        api.validate_error_envelope_holdouts(
            {"bad": np.zeros((1, 3, 2))},
            envelope,
        )
    with pytest.raises(api.MatrixErrorEnvelopeError):
        api.validate_error_envelope_holdouts(
            {"bad": np.zeros((1, 2, 2))},
            envelope,
            escape_tolerance=-1.0,
        )


def test_registered_control_alone_cannot_certify_signal_rank():
    control = np.zeros((3, 2, 2))
    control[0] = np.eye(2)
    envelope = api.build_output_error_envelope(
        {"control": control}, reference_operator_norm=1.0
    )
    decision = api.certify_error_whitened_row_rank(control[0], envelope)
    assert decision.full_row_rank_certified is False
    assert decision.guaranteed_rank_lower_bound == 0
    assert decision.status in {
        api.RankCertificateStatus.THRESHOLD_AMBIGUOUS,
        api.RankCertificateStatus.UNRESOLVED,
    }


def test_matrix_envelope_can_resolve_directions_hidden_by_scalar_floor():
    family = np.zeros((3, 2, 2))
    family[0, 0, 0] = 1.0
    envelope = api.build_output_error_envelope(
        {"anisotropic_control": family},
        reference_operator_norm=3.0,
        regularization_relative=1e-2,
    )
    observed = np.diag([3.0, 0.20])
    decision = api.certify_error_whitened_row_rank(observed, envelope)
    assert decision.status is api.RankCertificateStatus.FULL_ROW_RANK_CERTIFIED
    assert decision.full_row_rank_certified
    assert decision.smallest_singular_value > 1.1


def test_output_and_source_orthogonal_reparameterizations_preserve_certificate():
    rng = np.random.default_rng(1234)
    q_out, _ = np.linalg.qr(rng.normal(size=(4, 4)))
    q_src, _ = np.linalg.qr(rng.normal(size=(6, 6)))
    family = rng.normal(size=(3, 4, 6)) * 0.01
    signal = rng.normal(size=(4, 6))
    envelope = api.build_output_error_envelope(
        {"control": family}, reference_operator_norm=np.linalg.norm(signal, 2)
    )
    base = api.certify_error_whitened_row_rank(signal, envelope)

    rotated_family = np.einsum("ab,ibc,cd->iad", q_out, family, q_src)
    rotated_signal = q_out @ signal @ q_src
    rotated_envelope = api.build_output_error_envelope(
        {"control": rotated_family},
        reference_operator_norm=np.linalg.norm(rotated_signal, 2),
    )
    transformed = api.certify_error_whitened_row_rank(
        rotated_signal, rotated_envelope
    )
    np.testing.assert_allclose(
        transformed.error_whitened_singular_values,
        base.error_whitened_singular_values,
        rtol=0.0,
        atol=2e-10,
    )
    assert (
        transformed.guaranteed_rank_lower_bound
        == base.guaranteed_rank_lower_bound
    )
    assert transformed.status is base.status


def test_threshold_shell_and_malformed_inputs_fail_closed():
    with pytest.raises(api.MatrixErrorEnvelopeError):
        api.build_output_error_envelope({}, reference_operator_norm=1.0)
    with pytest.raises(api.MatrixErrorEnvelopeError):
        api.build_output_error_envelope(
            {"a": np.zeros((3, 2, 2)), "b": np.zeros((3, 2, 3))},
            reference_operator_norm=1.0,
        )
    family = np.zeros((3, 2, 2))
    family[0] = np.eye(2)
    envelope = api.build_output_error_envelope(
        {"control": family}, reference_operator_norm=1.0
    )
    with pytest.raises(api.MatrixErrorEnvelopeError):
        api.certify_error_whitened_row_rank(np.eye(3), envelope)
    with pytest.raises(api.MatrixErrorEnvelopeError):
        api.certify_error_whitened_row_rank(
            np.eye(2), envelope, ambiguity_half_width=1.0
        )
