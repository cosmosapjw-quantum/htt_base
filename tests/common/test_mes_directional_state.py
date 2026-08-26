"""PR-326 typed observer-space MES directional-state tests."""
from __future__ import annotations

from dataclasses import replace
import importlib

import numpy as np
import pytest

from common.statistical_foundations import (
    AnchorConditioning,
    registered_geodesic_mes_anchors,
)


SHA = "sha256:" + "1" * 64


def _common():
    try:
        return importlib.import_module("common.mes_directional_state")
    except ModuleNotFoundError:
        pytest.fail("PR-326 COMMON directional-state contract is not implemented")


def _anchor(*, eps2: float = 2.0e-6, eps3: float = 5.0e-6):
    return registered_geodesic_mes_anchors(
        eps1=0.0,
        eps2=eps2,
        eps3=eps3,
        attribution="explicit SAG residual eps1=0 fixture",
        conditioning=AnchorConditioning.REALIZATION_CONDITIONAL,
    )["sigma"]


def _estimate(
    module,
    *,
    dipole=(1.0, -2.0, 2.0),
    stf=None,
    field_identity="sha256:" + "5" * 64,
):
    if stf is None:
        stf = ((2.0, 1.0, 0.0), (1.0, -1.0, 0.5), (0.0, 0.5, -1.0))
    return module.make_directional_moment_estimate(
        monopole=0.25,
        dipole=dipole,
        stf2=stf,
        field_parity=module.DirectionalFieldParity.SCALAR_EVEN,
        estimator_kind=module.DirectionalEstimatorKind.FULL_SKY_QUADRATURE,
        direction_frame="registered observer Cartesian frame",
        direction_convention="RIGHT_HANDED_ACTIVE_O3",
        field_quantity="dimensionless directional morphology fixture",
        field_units="dimensionless",
        field_bandlimit=2,
        support_identity=SHA,
        weight_identity="sha256:" + "2" * 64,
        mask_identity="sha256:" + "3" * 64,
        transfer_identity="sha256:" + "4" * 64,
        field_identity=field_identity,
        covariance_identity="sha256:" + "6" * 64,
        estimator_identity="sha256:" + "7" * 64,
        support_size=14,
        design_rank=9,
        weighted_residual_norm=0.0,
    )


def test_scalar_only_and_zero_moment_paths_never_fabricate_orientation() -> None:
    module = _common()
    anchor = _anchor()

    with pytest.raises(module.DirectionalBridgeError, match="BLOCKED_DIRECTIONAL_SUPPORT"):
        module.build_mes_directional_state(
            directional_moments=anchor.value,
            anchor=anchor,
        )

    zero = _estimate(
        module,
        dipole=(0.0, 0.0, 0.0),
        stf=((0.0, 0.0, 0.0),) * 3,
    )
    state = module.build_mes_directional_state(
        directional_moments=zero,
        anchor=anchor,
    )
    assert state.dipole_shape is None
    assert state.stf2_shape is None
    assert state.directional_support_status == "DIRECTION_INDEXED_SUPPORT_BOUND"


def test_active_anchor_rescales_amplitude_but_not_vector_or_stf_shape() -> None:
    module = _common()
    estimate = _estimate(module)
    first = module.build_mes_directional_state(
        directional_moments=estimate,
        anchor=_anchor(eps2=2.0e-6, eps3=5.0e-6),
    )
    second = module.build_mes_directional_state(
        directional_moments=estimate,
        anchor=_anchor(eps2=3.0e-6, eps3=7.0e-6),
    )

    assert first.claim_tier == "diagnostic_only"
    assert first.observer_space_only is True
    assert first.physical_response_bound is False
    assert first.independent_information_gain is False
    assert first.vector_representation is module.VectorO3Representation.POLAR
    assert first.tensor_representation is module.TensorO3Representation.EVEN_STF2
    assert first.dipole_shape == pytest.approx(second.dipole_shape, abs=1e-15)
    assert np.asarray(first.stf2_shape) == pytest.approx(
        np.asarray(second.stf2_shape), abs=1e-15
    )
    assert first.mes_dipole_amplitude / second.mes_dipole_amplitude == pytest.approx(
        second.anchor_value / first.anchor_value, rel=1e-14
    )
    assert first.anchor_channel_key == _anchor().channel_key


def test_physical_stress_readiness_refuses_missing_or_cross_channel_response() -> None:
    module = _common()
    state = module.build_mes_directional_state(
        directional_moments=_estimate(module),
        anchor=_anchor(),
    )

    assert module.assess_physical_stress_readiness(state) is (
        module.PhysicalStressReadiness.BLOCKED_PHYSICAL_RESPONSE_REQUIRED
    )
    assert module.assess_physical_stress_readiness(
        state,
        response_identity="sha256:" + "8" * 64,
        response_channel_key=("W2",) + state.anchor_channel_key[1:],
    ) is module.PhysicalStressReadiness.BLOCKED_CHANNEL_MATCH
    assert module.assess_physical_stress_readiness(
        state,
        response_identity="sha256:" + "8" * 64,
        response_channel_key=state.anchor_channel_key,
    ) is module.PhysicalStressReadiness.RESPONSE_BOUND_NUMERATOR_REQUIRED


def test_moment_type_rejects_non_stf_and_wrong_content_identities() -> None:
    module = _common()
    with pytest.raises(module.DirectionalBridgeError, match="symmetric trace-free"):
        _estimate(
            module,
            stf=((1.0, 2.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0)),
        )
    with pytest.raises(module.DirectionalBridgeError, match="field_identity"):
        _estimate(module, field_identity="caller-label")


@pytest.mark.parametrize(
    ("change", "message"),
    (
        ({"physical_response_bound": True}, "claim boundary"),
        ({"independent_information_gain": True}, "claim boundary"),
        ({"claim_tier": "native_validated"}, "claim boundary"),
        ({"family_identification_status": "IDENTIFIED"}, "claim boundary"),
        ({"anchor_conditioning": "FORGED"}, "AnchorConditioning"),
        ({"mes_dipole": (9.0, 8.0, 7.0)}, "anchor scaling"),
        ({"state_identity": "sha256:" + "9" * 64}, "state_identity"),
    ),
)
def test_directional_state_cannot_be_replaced_into_an_inconsistent_claim(
    change: dict[str, object], message: str
) -> None:
    module = _common()
    state = module.build_mes_directional_state(
        directional_moments=_estimate(module),
        anchor=_anchor(),
    )

    with pytest.raises(module.DirectionalBridgeError, match=message):
        replace(state, **change)


def test_realizability_certificate_revalidates_direct_replacement() -> None:
    module = _common()
    certificate = module.certify_spherical_second_moment(
        mean=(0.0, 0.0, 0.0),
        second_moment=((0.2, 0.0, 0.0), (0.0, 0.3, 0.0), (0.0, 0.0, 0.5)),
        support_identity="sha256:" + "8" * 64,
    )

    with pytest.raises(
        module.DirectionalBridgeError, match="BLOCKED_MOMENT_REALIZABILITY"
    ):
        replace(certificate, eigenvalues=(0.1, 0.4, 0.5))


def test_directional_field_cannot_self_award_parity_or_realizability_status() -> None:
    module = _common()
    estimate = _estimate(module)

    with pytest.raises(module.DirectionalBridgeError, match="O3 representation"):
        replace(
            estimate,
            field_parity=module.DirectionalFieldParity.PSEUDOSCALAR_ODD,
        )
    with pytest.raises(
        module.DirectionalBridgeError, match="probability-measure certificate"
    ):
        replace(estimate, realizability_status="PSD_TRACE_ONE_ZERO_MEAN_VERIFIED")
    with pytest.raises(module.DirectionalBridgeError, match="field_units"):
        replace(estimate, field_units="microK_CMB")
    with pytest.raises(module.DirectionalBridgeError, match="DIRECTIONAL_LEAKAGE"):
        replace(estimate, field_bandlimit=3)
