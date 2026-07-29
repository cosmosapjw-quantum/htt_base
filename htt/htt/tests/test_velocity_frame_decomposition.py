"""Unit tests for PR-256 velocity-frame and source-response contracts."""

from __future__ import annotations

from dataclasses import replace
import hashlib

import numpy as np
import pytest

from common.anchor_geometry import (
    NormalizerKind,
    NormalizerPurpose,
    NormalizerSpec,
)
from common.anchored_response_geometry import anchored_numeric_content_id
from common.transfer_registry import (
    CalibrationStatus,
    ObservableKind,
    TransferFunctionSpec,
    TransferSource,
    TransferValidRange,
)
from htt.departure.velocity_frame_decomposition import (
    ResponseProviderAvailability,
    ResponseProviderKind,
    SourceHypothesis,
    SourceResponseGeometryReport,
    SourceResponseGeometryStatus,
    SourceResponseProviderSpec,
    VelocityComponent,
    VelocityDecompositionStatus,
    VelocityFrameDecomposition,
    VelocityFrameError,
    build_velocity_frame_decomposition,
    measure_source_response_geometry,
    register_source_response_provider,
    revalidate_source_response_geometry,
    revalidate_source_response_provider,
    revalidate_velocity_frame_decomposition,
)


def _receipt(value: str) -> str:
    return "sha256:" + hashlib.sha256(value.encode("utf-8")).hexdigest()


MASK_ID = _receipt("pr256-unit-synthetic-full-mask")
TRANSFER_ID = _receipt("pr256-unit-synthetic-transfer-none")


def _provider(
    hypothesis: SourceHypothesis,
    response: object | None,
    *,
    observables: tuple[str, ...] = ("dipole", "depth"),
    availability: ResponseProviderAvailability = (
        ResponseProviderAvailability.AVAILABLE
    ),
    provider_id: str | None = None,
    transfer_id: str = TRANSFER_ID,
) -> SourceResponseProviderSpec:
    is_local = hypothesis is SourceHypothesis.LOCAL_BOOST
    label = "beta_MO_x" if is_local else "beta_RM_x"
    return register_source_response_provider(
        provider_id=(
            provider_id
            if provider_id is not None
            else _receipt(
                f"provider-{hypothesis.value}-{availability.value}"
            )
        ),
        hypothesis=hypothesis,
        velocity_component=(
            VelocityComponent.BETA_MO
            if is_local
            else VelocityComponent.BETA_RM
        ),
        provider_kind=ResponseProviderKind.SYNTHETIC,
        availability=availability,
        observable_labels=observables,
        parameter_labels=(label,),
        response=response,
        transfer_id=transfer_id,
        transfer_source=TransferSource.NONE,
        basis="registered synthetic Cartesian basis",
        epoch_window="registered synthetic common window",
        assumptions=("linear response",),
        caveats=("synthetic hypothesis response only",),
        missing_reason=(
            None
            if availability is ResponseProviderAvailability.AVAILABLE
            else "remote-dipole provider unavailable"
        ),
    )


def _normalizer(
    *,
    coordinate_map: tuple[tuple[float, ...], ...] = (
        (1.0, 0.0),
        (0.0, 1.0),
    ),
) -> NormalizerSpec:
    return NormalizerSpec(
        normalizer_id="pr256-unit-identity-normalizer",
        kind=NormalizerKind.EXPANSION_NORMALIZED,
        purposes=(NormalizerPurpose.RESPONSE_CONDITIONING,),
        coordinate_labels=("beta_MO_x", "beta_RM_x"),
        coordinate_map=coordinate_map,
        source_identity="PR256-UNIT-SYNTHETIC",
        assumptions=("block-preserving coordinate map",),
    )


def _geometry(
    local_response: object,
    global_response: object,
    *,
    covariance: object = ((1.0, 0.0), (0.0, 1.0)),
    threshold: float = 0.2,
) -> tuple[SourceResponseGeometryReport, NormalizerSpec]:
    normalizer = _normalizer()
    report = measure_source_response_geometry(
        local_provider=_provider(
            SourceHypothesis.LOCAL_BOOST,
            local_response,
        ),
        global_provider=_provider(
            SourceHypothesis.GLOBAL_TILT,
            global_response,
        ),
        covariance=covariance,
        normalizer=normalizer,
        covariance_id=anchored_numeric_content_id(covariance),
        mask_id=MASK_ID,
        separation_threshold_radians=threshold,
    )
    return report, normalizer


def test_first_order_velocity_closure_is_explicit_and_replayable() -> None:
    report = build_velocity_frame_decomposition(
        beta_RO=(3.0e-3, -1.0e-3, 0.5e-3),
        beta_RM=(1.0e-3, -0.5e-3, 0.25e-3),
        beta_MO=(2.0e-3, -0.5e-3, 0.25e-3),
        basis="right-handed Cartesian tetrad",
        epoch_window="z=0 common synthetic window",
        first_order_beta_ceiling=1.0e-2,
    )
    assert report.status is VelocityDecompositionStatus.CLOSURE_VERIFIED
    assert report.closure_norm == 0.0
    assert report.as_payload()["relation"] == (
        "beta_RO = beta_RM + beta_MO + O(beta^2)"
    )
    assert revalidate_velocity_frame_decomposition(report) is report


def test_closure_mismatch_and_sum_only_do_not_derive_a_source() -> None:
    mismatch = build_velocity_frame_decomposition(
        beta_RO=(9.0e-3, 0.0, 0.0),
        beta_RM=(1.0e-3, 0.0, 0.0),
        beta_MO=(1.0e-3, 0.0, 0.0),
        basis="Cartesian",
        epoch_window="synthetic",
        first_order_beta_ceiling=1.0e-2,
        atol=1.0e-15,
        rtol=1.0e-12,
    )
    assert mismatch.status is VelocityDecompositionStatus.CLOSURE_MISMATCH
    assert mismatch.closure_norm == pytest.approx(7.0e-3)

    sum_only = build_velocity_frame_decomposition(
        beta_RO=(3.0e-3, 0.0, 0.0),
        beta_RM=None,
        beta_MO=None,
        basis="Cartesian",
        epoch_window="synthetic",
        first_order_beta_ceiling=1.0e-2,
    )
    assert sum_only.status is VelocityDecompositionStatus.SUM_ONLY
    assert sum_only.beta_RM is None
    assert sum_only.beta_MO is None
    assert sum_only.closure_residual is None
    assert sum_only.missing_components == ("beta_RM", "beta_MO")


def test_first_order_closure_accepts_registered_remainder_and_rejects_order_drift() -> None:
    beta_rm = 1.0e-3
    beta_mo = 2.0e-3
    exact_collinear = (beta_rm + beta_mo) / (1.0 + beta_rm * beta_mo)
    report = build_velocity_frame_decomposition(
        beta_RO=(exact_collinear, 0.0, 0.0),
        beta_RM=(beta_rm, 0.0, 0.0),
        beta_MO=(beta_mo, 0.0, 0.0),
        basis="Cartesian",
        epoch_window="synthetic",
        first_order_beta_ceiling=1.0e-2,
    )
    assert report.status is VelocityDecompositionStatus.CLOSURE_VERIFIED
    assert report.closure_norm == pytest.approx(
        abs(exact_collinear - beta_rm - beta_mo)
    )
    assert report.truncation_remainder_bound == pytest.approx(
        (beta_rm + beta_mo) ** 2
    )
    assert report.closure_norm <= report.closure_tolerance

    with pytest.raises(VelocityFrameError, match="first_order_small_velocity"):
        build_velocity_frame_decomposition(
            beta_RO=(0.0, 0.0, 0.0),
            beta_RM=(0.0, 0.0, 0.0),
            beta_MO=(0.0, 0.0, 0.0),
            basis="Cartesian",
            epoch_window="synthetic",
            first_order_beta_ceiling=1.0e-2,
            perturbative_order="exact_all_orders",
        )

    with pytest.raises(VelocityFrameError, match="first_order_beta_ceiling"):
        build_velocity_frame_decomposition(
            beta_RO=(0.0, 0.0, 0.0),
            beta_RM=(0.8, 0.0, 0.0),
            beta_MO=(0.8, 0.0, 0.0),
            basis="Cartesian",
            epoch_window="synthetic",
            first_order_beta_ceiling=0.1,
        )

    with pytest.raises(VelocityFrameError, match="first_order_beta_ceiling"):
        build_velocity_frame_decomposition(
            beta_RO=None,
            beta_RM=(6.0e-3, 0.0, 0.0),
            beta_MO=(6.0e-3, 0.0, 0.0),
            basis="Cartesian",
            epoch_window="synthetic",
            first_order_beta_ceiling=1.0e-2,
        )


@pytest.mark.parametrize(
    "field,value",
    (
        ("beta_RO", (True, 0.0, 0.0)),
        ("beta_RM", (np.nan, 0.0, 0.0)),
        ("beta_MO", (np.inf, 0.0, 0.0)),
        ("beta_RO", (0.0, 0.0)),
    ),
)
def test_velocity_inputs_fail_closed(field: str, value: object) -> None:
    inputs = {
        "beta_RO": (0.0, 0.0, 0.0),
        "beta_RM": (0.0, 0.0, 0.0),
        "beta_MO": (0.0, 0.0, 0.0),
    }
    inputs[field] = value
    with pytest.raises(VelocityFrameError):
        build_velocity_frame_decomposition(
            **inputs,
            basis="Cartesian",
            epoch_window="synthetic",
            first_order_beta_ceiling=1.0e-2,
        )


def test_factory_only_velocity_and_provider_contracts_reject_forgery() -> None:
    report = build_velocity_frame_decomposition(
        beta_RO=(0.0, 0.0, 0.0),
        beta_RM=(0.0, 0.0, 0.0),
        beta_MO=(0.0, 0.0, 0.0),
        basis="registered synthetic Cartesian basis",
        epoch_window="registered synthetic common window",
        first_order_beta_ceiling=1.0e-2,
    )
    with pytest.raises(VelocityFrameError):
        replace(report, status=VelocityDecompositionStatus.CLOSURE_MISMATCH)

    provider = _provider(SourceHypothesis.LOCAL_BOOST, ((1.0,), (0.0,)))
    assert revalidate_source_response_provider(provider) is provider
    with pytest.raises(VelocityFrameError):
        replace(provider, response_role="observational_evidence")

    with pytest.raises(VelocityFrameError):
        VelocityFrameDecomposition(
            beta_RO=(0.0, 0.0, 0.0),
            beta_RM=(0.0, 0.0, 0.0),
            beta_MO=(0.0, 0.0, 0.0),
            basis="Cartesian",
            epoch_window="synthetic",
            units="dimensionless_beta_c_equals_1",
            parity="polar_vector",
            perturbative_order="first_order_small_velocity",
            first_order_beta_ceiling=1.0e-2,
            status=VelocityDecompositionStatus.CLOSURE_VERIFIED,
            closure_residual=(0.0, 0.0, 0.0),
            closure_norm=0.0,
            closure_tolerance=1.0e-15,
            atol=1.0e-15,
            rtol=1.0e-10,
            missing_components=(),
        )


def test_separable_and_sum_only_geometry_use_supported_response() -> None:
    separable, normalizer = _geometry(
        ((1.0,), (0.0,)),
        ((0.0,), (1.0,)),
    )
    assert (
        separable.status
        is SourceResponseGeometryStatus.SEPARABLE_CANDIDATE
    )
    assert separable.separable_candidate is True
    assert not hasattr(separable, "identifiable_candidate")
    assert separable.local_rank == separable.global_rank == 1
    assert separable.joint_rank == 2
    assert separable.direct_sum is True
    assert separable.minimum_principal_angle_radians == pytest.approx(
        np.pi / 2.0
    )
    assert revalidate_source_response_geometry(
        separable,
        normalizer=normalizer,
    ) is separable

    sum_only, _ = _geometry(
        ((1.0,), (0.0,)),
        ((2.0,), (0.0,)),
    )
    assert sum_only.status is SourceResponseGeometryStatus.SUM_ONLY
    assert sum_only.joint_rank == 1
    assert sum_only.direct_sum is False
    assert sum_only.minimum_principal_angle_radians == pytest.approx(0.0)


def test_covariance_null_response_is_non_identified_not_zero_cost() -> None:
    report, _ = _geometry(
        ((1.0,), (0.0,)),
        ((0.0,), (1.0,)),
        covariance=((1.0, 0.0), (0.0, 0.0)),
    )
    assert report.status is SourceResponseGeometryStatus.NON_IDENTIFIED
    assert report.covariance_null_response_norm_sq == pytest.approx(1.0)
    assert report.common_geometry is not None
    assert (
        report.common_geometry.status.value
        == "EXPLICIT_NULL_RESPONSE"
    )


def test_internal_block_rank_deficiency_cannot_be_separable_candidate() -> None:
    observables = ("dipole", "depth", "morphology")
    local = register_source_response_provider(
        provider_id=_receipt("rank-deficient-local"),
        hypothesis=SourceHypothesis.LOCAL_BOOST,
        velocity_component=VelocityComponent.BETA_MO,
        provider_kind=ResponseProviderKind.SYNTHETIC,
        availability=ResponseProviderAvailability.AVAILABLE,
        observable_labels=observables,
        parameter_labels=("beta_MO_x", "beta_MO_y"),
        response=((1.0, 0.0), (0.0, 0.0), (0.0, 0.0)),
        transfer_id=TRANSFER_ID,
        transfer_source=TransferSource.NONE,
        basis="registered synthetic Cartesian basis",
        epoch_window="registered synthetic common window",
        assumptions=("linear response",),
        caveats=("synthetic hypothesis response only",),
    )
    global_value = register_source_response_provider(
        provider_id=_receipt("rank-complete-global"),
        hypothesis=SourceHypothesis.GLOBAL_TILT,
        velocity_component=VelocityComponent.BETA_RM,
        provider_kind=ResponseProviderKind.SYNTHETIC,
        availability=ResponseProviderAvailability.AVAILABLE,
        observable_labels=observables,
        parameter_labels=("beta_RM_x",),
        response=((0.0,), (1.0,), (0.0,)),
        transfer_id=TRANSFER_ID,
        transfer_source=TransferSource.NONE,
        basis="registered synthetic Cartesian basis",
        epoch_window="registered synthetic common window",
        assumptions=("linear response",),
        caveats=("synthetic hypothesis response only",),
    )
    normalizer = NormalizerSpec(
        normalizer_id="rank-deficient-block-normalizer",
        kind=NormalizerKind.MES_ANCHORED,
        purposes=(NormalizerPurpose.RESPONSE_CONDITIONING,),
        coordinate_labels=(
            "beta_MO_x",
            "beta_MO_y",
            "beta_RM_x",
        ),
        coordinate_map=(
            (1.0, 0.0, 0.0),
            (0.0, 1.0, 0.0),
            (0.0, 0.0, 1.0),
        ),
        source_identity="PR256-RANK-DEFICIENT-TYPED-COORDINATES",
        assumptions=("block-preserving map",),
    )
    covariance = np.eye(3)
    report = measure_source_response_geometry(
        local_provider=local,
        global_provider=global_value,
        covariance=covariance,
        normalizer=normalizer,
        covariance_id=anchored_numeric_content_id(covariance),
        mask_id=MASK_ID,
    )
    assert report.local_rank == 1
    assert report.global_rank == 1
    assert report.joint_rank == 2
    assert report.direct_sum is True
    assert report.status is SourceResponseGeometryStatus.NON_IDENTIFIED
    assert report.separable_candidate is False


def test_missing_provider_is_typed_and_never_zero_filled() -> None:
    local = _provider(SourceHypothesis.LOCAL_BOOST, ((1.0,), (0.0,)))
    missing_global = _provider(
        SourceHypothesis.GLOBAL_TILT,
        None,
        availability=ResponseProviderAvailability.MISSING,
    )
    covariance = np.eye(2)
    report = measure_source_response_geometry(
        local_provider=local,
        global_provider=missing_global,
        covariance=covariance,
        normalizer=_normalizer(),
        covariance_id=anchored_numeric_content_id(covariance),
        mask_id=MASK_ID,
    )
    assert (
        report.status
        is SourceResponseGeometryStatus.MISSING_RESPONSE_PROVIDER
    )
    assert report.common_geometry is None
    assert report.global_rank is None
    assert report.missing_provider_ids == (missing_global.provider_id,)
    assert missing_global.response_replay_matrix is None

    with pytest.raises(VelocityFrameError, match="must not carry"):
        register_source_response_provider(
            provider_id=_receipt("contradictory-missing"),
            hypothesis=SourceHypothesis.GLOBAL_TILT,
            velocity_component=VelocityComponent.BETA_RM,
            provider_kind=ResponseProviderKind.SYNTHETIC,
            availability=ResponseProviderAvailability.MISSING,
            observable_labels=("dipole", "depth"),
            parameter_labels=("beta_RM_x",),
            response=((0.0,), (0.0,)),
            transfer_id=TRANSFER_ID,
            transfer_source=TransferSource.NONE,
            basis="Cartesian",
            epoch_window="synthetic",
            caveats=("missing provider test",),
            missing_reason="provider absent",
        )


def test_missing_provider_does_not_bypass_transfer_provenance() -> None:
    transfer = TransferFunctionSpec(
        transfer_id="pr256-unit-missing-empirical-proxy-v1",
        source=TransferSource.EMPIRICAL_PROXY,
        family="local_global_hypothesis_response",
        valid_range=TransferValidRange(
            k_min=1.0e-5,
            k_max=0.2,
            ell_min=1,
            ell_max=4,
        ),
        observable_kind=ObservableKind.SCALAR_SUMMARY,
        normalization="registered empirical proxy normalization",
        calibration_status=CalibrationStatus.EMPIRICAL_PROXY,
        caveats=("not a native transfer", "hypothesis-only response"),
        source_ref="synthetic-test-provider",
        version="pr256-unit-missing-v1",
    )
    local = _provider(SourceHypothesis.LOCAL_BOOST, ((1.0,), (0.0,)))
    missing_global = register_source_response_provider(
        provider_id=_receipt("missing-global-empirical-proxy"),
        hypothesis=SourceHypothesis.GLOBAL_TILT,
        velocity_component=VelocityComponent.BETA_RM,
        provider_kind=ResponseProviderKind.EMPIRICAL_PROXY,
        availability=ResponseProviderAvailability.MISSING,
        observable_labels=("dipole", "depth"),
        parameter_labels=("beta_RM_x",),
        response=None,
        transfer_id=transfer.transfer_id,
        transfer_source=TransferSource.EMPIRICAL_PROXY,
        transfer_spec=transfer,
        basis="registered synthetic Cartesian basis",
        epoch_window="registered synthetic common window",
        assumptions=("conditional on empirical proxy",),
        caveats=("not observational validation",),
        missing_reason="provider absent",
    )
    covariance = np.eye(2)
    with pytest.raises(VelocityFrameError, match="share exact transfer"):
        measure_source_response_geometry(
            local_provider=local,
            global_provider=missing_global,
            covariance=covariance,
            normalizer=_normalizer(),
            covariance_id=anchored_numeric_content_id(covariance),
            mask_id=MASK_ID,
        )


@pytest.mark.parametrize(
    ("availability", "response"),
    (
        (ResponseProviderAvailability.MISSING, None),
        (ResponseProviderAvailability.AVAILABLE, ((0.0,), (1.0,))),
    ),
)
def test_none_transfer_id_mismatch_fails_before_status_assignment(
    availability: ResponseProviderAvailability,
    response: object | None,
) -> None:
    local = _provider(SourceHypothesis.LOCAL_BOOST, ((1.0,), (0.0,)))
    global_value = _provider(
        SourceHypothesis.GLOBAL_TILT,
        response,
        availability=availability,
        transfer_id=_receipt("pr256-unit-distinct-none-transfer"),
    )
    covariance = np.eye(2)
    with pytest.raises(VelocityFrameError, match="share exact transfer"):
        measure_source_response_geometry(
            local_provider=local,
            global_provider=global_value,
            covariance=covariance,
            normalizer=_normalizer(),
            covariance_id=anchored_numeric_content_id(covariance),
            mask_id=MASK_ID,
        )


def test_local_and_global_provider_alias_reuse_fails_closed() -> None:
    local = _provider(SourceHypothesis.LOCAL_BOOST, ((1.0,), (0.0,)))
    global_value = _provider(
        SourceHypothesis.GLOBAL_TILT,
        ((0.0,), (1.0,)),
        provider_id=local.provider_id,
    )
    covariance = np.eye(2)
    with pytest.raises(VelocityFrameError, match="distinct provider_id"):
        measure_source_response_geometry(
            local_provider=local,
            global_provider=global_value,
            covariance=covariance,
            normalizer=_normalizer(),
            covariance_id=anchored_numeric_content_id(covariance),
            mask_id=MASK_ID,
        )


def test_cross_block_normalizer_and_provider_mismatch_fail_closed() -> None:
    local = _provider(SourceHypothesis.LOCAL_BOOST, ((1.0,), (0.0,)))
    global_value = _provider(
        SourceHypothesis.GLOBAL_TILT,
        ((0.0,), (1.0,)),
    )
    covariance = np.eye(2)
    with pytest.raises(VelocityFrameError, match="must not mix"):
        measure_source_response_geometry(
            local_provider=local,
            global_provider=global_value,
            covariance=covariance,
            normalizer=_normalizer(
                coordinate_map=((1.0, 0.1), (0.0, 1.0))
            ),
            covariance_id=anchored_numeric_content_id(covariance),
            mask_id=MASK_ID,
        )

    wrong_component = SourceHypothesis.LOCAL_BOOST
    with pytest.raises(VelocityFrameError, match="requires beta_MO"):
        register_source_response_provider(
            provider_id=_receipt("wrong-component"),
            hypothesis=wrong_component,
            velocity_component=VelocityComponent.BETA_RM,
            provider_kind=ResponseProviderKind.SYNTHETIC,
            availability=ResponseProviderAvailability.AVAILABLE,
            observable_labels=("dipole", "depth"),
            parameter_labels=("beta_MO_x",),
            response=((1.0,), (0.0,)),
            transfer_id=TRANSFER_ID,
            transfer_source=TransferSource.NONE,
            basis="Cartesian",
            epoch_window="synthetic",
            caveats=("wrong component test",),
        )


def test_empirical_proxy_requires_one_complete_shared_transfer_spec() -> None:
    transfer = TransferFunctionSpec(
        transfer_id="pr256-unit-empirical-proxy-v1",
        source=TransferSource.EMPIRICAL_PROXY,
        family="local_global_hypothesis_response",
        valid_range=TransferValidRange(
            k_min=1.0e-5,
            k_max=0.2,
            ell_min=1,
            ell_max=4,
        ),
        observable_kind=ObservableKind.SCALAR_SUMMARY,
        normalization="registered empirical proxy normalization",
        calibration_status=CalibrationStatus.EMPIRICAL_PROXY,
        caveats=("not a native transfer", "hypothesis-only response"),
        source_ref="synthetic-test-provider",
        version="pr256-unit-v1",
    )

    def empirical_provider(
        hypothesis: SourceHypothesis,
        response: object,
        *,
        transfer_spec: TransferFunctionSpec = transfer,
    ) -> SourceResponseProviderSpec:
        local = hypothesis is SourceHypothesis.LOCAL_BOOST
        return register_source_response_provider(
            provider_id=_receipt(f"empirical-{hypothesis.value}"),
            hypothesis=hypothesis,
            velocity_component=(
                VelocityComponent.BETA_MO
                if local
                else VelocityComponent.BETA_RM
            ),
            provider_kind=ResponseProviderKind.EMPIRICAL_PROXY,
            availability=ResponseProviderAvailability.AVAILABLE,
            observable_labels=("dipole", "depth"),
            parameter_labels=(
                ("beta_MO_x",) if local else ("beta_RM_x",)
            ),
            response=response,
            transfer_id=transfer_spec.transfer_id,
            transfer_source=TransferSource.EMPIRICAL_PROXY,
            transfer_spec=transfer_spec,
            basis="registered empirical-proxy basis",
            epoch_window="registered empirical-proxy window",
            assumptions=("conditional on empirical proxy",),
            caveats=("not observational validation",),
        )

    covariance = np.eye(2)
    report = measure_source_response_geometry(
        local_provider=empirical_provider(
            SourceHypothesis.LOCAL_BOOST,
            ((1.0,), (0.0,)),
        ),
        global_provider=empirical_provider(
            SourceHypothesis.GLOBAL_TILT,
            ((0.0,), (1.0,)),
        ),
        covariance=covariance,
        normalizer=_normalizer(),
        covariance_id=anchored_numeric_content_id(covariance),
        mask_id=MASK_ID,
    )
    assert (
        report.status
        is SourceResponseGeometryStatus.SEPARABLE_CANDIDATE
    )
    assert report.joint_transfer_id == transfer.transfer_id
    assert report.common_geometry is not None
    assert report.common_geometry.transfer_spec == transfer

    conflicting = TransferFunctionSpec(
        transfer_id="pr256-unit-empirical-proxy-v2",
        source=TransferSource.EMPIRICAL_PROXY,
        family=transfer.family,
        valid_range=transfer.valid_range,
        observable_kind=transfer.observable_kind,
        normalization=transfer.normalization,
        calibration_status=transfer.calibration_status,
        caveats=transfer.caveats,
        source_ref=transfer.source_ref,
        version="pr256-unit-v2",
    )
    with pytest.raises(VelocityFrameError, match="share exact transfer"):
        measure_source_response_geometry(
            local_provider=empirical_provider(
                SourceHypothesis.LOCAL_BOOST,
                ((1.0,), (0.0,)),
            ),
            global_provider=empirical_provider(
                SourceHypothesis.GLOBAL_TILT,
                ((0.0,), (1.0,)),
                transfer_spec=conflicting,
            ),
            covariance=covariance,
            normalizer=_normalizer(),
            covariance_id=anchored_numeric_content_id(covariance),
            mask_id=MASK_ID,
        )


def test_report_construction_is_factory_only() -> None:
    report, _ = _geometry(
        ((1.0,), (0.0,)),
        ((0.0,), (1.0,)),
    )
    with pytest.raises(VelocityFrameError):
        replace(
            report,
            status=SourceResponseGeometryStatus.SUM_ONLY,
        )
    assert type(report) is SourceResponseGeometryReport
