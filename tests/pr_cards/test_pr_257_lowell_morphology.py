from __future__ import annotations

from dataclasses import replace
import hashlib
import math
from pathlib import Path

import numpy as np
import pytest

from common.anchor_geometry import (
    NormalizerKind,
    NormalizerPurpose,
    NormalizerSpec,
)
from common.anchored_response_geometry import (
    anchored_numeric_content_id,
    measure_schur_morphology_information,
)
from common.orbit_catalogue_v2 import (
    CatalogueClaimStatus,
    OrbitCatalogueV2Error,
    OrbitCatalogueV2Report,
    OrbitCatalogueV2Spec,
    PR257_POLYNOMIAL_NAMES,
    PolynomialParity,
    orbit_catalogue_v2,
    revalidate_orbit_catalogue_v2,
)
from common.orbit_nonlinearity import (
    DEPARTURE_O3_PARITY,
    O3Transform,
    STF5_CARTESIAN_BASIS,
    transform_departure_state,
)
from common.statistical_foundations import DepartureState
from common.transfer_registry import TransferSource
from htt.statistics.morphology_benchmark import (
    MorphologyBenchmarkError,
    MorphologyBenchmarkProtocol,
    MorphologyBenchmarkStatus,
    MorphologyRepresentation,
    RepresentationAvailability,
    RepresentationBenchmarkInput,
    RepresentationBenchmarkStatus,
    evaluate_morphology_benchmark,
)
from obsstat.lowell_counterpairs import (
    CounterpairFactor,
    FeatureAvailability,
    InterventionOperator,
    LowEllCounterpairError,
    LowEllInterventionSpec,
    MorphologyFeatureKind,
    ParityRealization,
    apply_lowell_counterpair_intervention,
    build_lowell_morphology_feature_packet,
    build_matched_counterpair,
    register_morphology_feature,
    revalidate_matched_counterpair,
)
from obsstat.lowell_poles import IMPLEMENTED_HARMONIC_CONVENTION


ROOT = Path(__file__).resolve().parents[2]
CAS_CONTRACT = (
    ROOT
    / "docs/generated/pr257_lowell_morphology/"
    "CAS_CONTRACT_PR257_ORBIT_V2.json"
)


def _receipt(text: str) -> str:
    return "sha256:" + hashlib.sha256(text.encode("utf-8")).hexdigest()


def _state(
    *,
    sigma: tuple[float, ...] = (1.0, 2.0, 0.0, 0.0, 0.0),
    omega: tuple[float, ...] = (1.0, 2.0, 3.0),
    beta: tuple[float, ...] = (1.0, 1.0, 1.0),
) -> DepartureState:
    return DepartureState(
        sigma_ab=sigma,
        omega_a=omega,
        beta_a=beta,
        delta_omega_k=0.0,
        frame="PR257 synthetic Cartesian frame",
        congruence="PR257 synthetic observer congruence",
        epoch_window="PR257 synthetic ell 2-3 window",
        averaging_scale="PR257 synthetic unit scale",
        basis=STF5_CARTESIAN_BASIS,
        units="dimensionless",
        parity=DEPARTURE_O3_PARITY,
        perturbative_order="diagnostic finite polynomial state",
    )


def _catalog() -> OrbitCatalogueV2Spec:
    return OrbitCatalogueV2Spec(
        catalog_id="PR257-SIGMA-OMEGA-BETA-POLYNOMIALS-V2",
        polynomial_names=PR257_POLYNOMIAL_NAMES,
        multiplicity_method="MAX_ABS_Z_FIXED_CATALOGUE_V1",
        alignment_null_id="PR257-SYNTHETIC-ALIGNMENT-NULL-V1",
        preregistration_id="PR257-PRE-SKY-CATALOGUE-FREEZE-V1",
        cas_contract_id=(
            "sha256:" + hashlib.sha256(CAS_CONTRACT.read_bytes()).hexdigest()
        ),
    )


def _reflection() -> O3Transform:
    return O3Transform(
        matrix=((-1.0, 0.0, 0.0), (0.0, -1.0, 0.0), (0.0, 0.0, -1.0)),
        transform_id="PR257-R-MINUS-I",
        coordinate_frame="PR257 synthetic Cartesian frame",
    )


def test_typed_polynomial_catalogue_obeys_o3_scalar_pseudoscalar_parity() -> None:
    original = orbit_catalogue_v2(_state(), _catalog())
    reflected = orbit_catalogue_v2(
        transform_departure_state(_state(), _reflection()),
        _catalog(),
    )
    for name, parity in zip(
        PR257_POLYNOMIAL_NAMES,
        original.parity,
        strict=True,
    ):
        expected = (
            original.values_by_name[name]
            if parity is PolynomialParity.EVEN
            else -original.values_by_name[name]
        )
        assert reflected.values_by_name[name] == pytest.approx(
            expected,
            abs=1.0e-12,
        )
    assert original.values_by_name[
        "det_beta_sigma_beta_sigma2_beta"
    ] == pytest.approx(20.0)
    assert original.values_by_name["beta_dot_omega"] == 6.0
    assert original.values_by_name["beta_sigma_omega"] == -4.0
    assert original.values_by_name["beta_sigma2_omega"] == 36.0
    assert original.catalog.generic_orbit_separation_status is CatalogueClaimStatus.UNPROVEN
    assert original.catalog.degree_completeness_status is CatalogueClaimStatus.UNPROVEN
    assert "typed_polynomials" in original.as_payload()
    assert "invariants" not in original.as_payload()
    assert revalidate_orbit_catalogue_v2(original).report_id == original.report_id


def test_catalogue_preserves_exact_nongeneric_nonseparation_witness() -> None:
    positive = orbit_catalogue_v2(
        _state(beta=(0.0, 0.0, 0.0), omega=(1.0, 2.0, 3.0)),
        _catalog(),
    )
    negative = orbit_catalogue_v2(
        _state(beta=(0.0, 0.0, 0.0), omega=(-1.0, -2.0, -3.0)),
        _catalog(),
    )
    assert positive.polynomial_values == negative.polynomial_values
    assert positive.state_id != negative.state_id
    assert positive.catalog.generic_orbit_separation_status is CatalogueClaimStatus.UNPROVEN


def test_catalogue_syzygies_and_factory_boundary() -> None:
    report = orbit_catalogue_v2(_state(), _catalog())
    assert report.cayley_hamilton_relative_residual <= 1.0e-12
    assert report.beta_contraction_relative_residual <= 1.0e-12
    assert report.omega_contraction_relative_residual <= 1.0e-12
    assert report.mixed_contraction_relative_residual <= 1.0e-12
    assert report.beta_krylov_gram_relative_residual <= 1.0e-12
    with pytest.raises(
        OrbitCatalogueV2Error,
        match="must be created",
    ):
        OrbitCatalogueV2Report(
            state=report.state,
            catalog=report.catalog,
            polynomial_values=report.polynomial_values,
            parity=report.parity,
            cayley_hamilton_relative_residual=0.0,
            beta_contraction_relative_residual=0.0,
            omega_contraction_relative_residual=0.0,
            mixed_contraction_relative_residual=0.0,
            beta_krylov_gram_relative_residual=0.0,
            state_id=report.state_id,
        )
    with pytest.raises(OrbitCatalogueV2Error, match="must be created"):
        replace(report, polynomial_values=(0.0,) * 12)
    with pytest.raises(OrbitCatalogueV2Error, match="remain UNPROVEN"):
        replace(
            _catalog(),
            generic_orbit_separation_status=(
                CatalogueClaimStatus.PREREGISTERED_DEGREE_BOUNDED
            ),
        )


def _alm() -> dict[tuple[int, int], complex]:
    result: dict[tuple[int, int], complex] = {}
    for ell in (2, 3):
        result[(ell, 0)] = complex(1.0 + 0.2 * ell, 0.0)
        for m in range(1, ell + 1):
            value = complex(0.4 * (ell + m), 0.17 * (ell - m + 1))
            result[(ell, m)] = value
            result[(ell, -m)] = ((-1) ** m) * value.conjugate()
    return result


def _features(
    *,
    wavelet_provider_id: str | None = None,
) -> tuple:
    return (
        register_morphology_feature(
            kind=MorphologyFeatureKind.DIRECTIONAL_WAVELET,
            availability=FeatureAvailability.MISSING_FEATURE_PROVIDER,
            provider_id=(
                _receipt("pr257-missing-wavelet-provider")
                if wavelet_provider_id is None
                else wavelet_provider_id
            ),
            units="not_available",
            missing_reason="no registered directional-wavelet provider",
        ),
        register_morphology_feature(
            kind=MorphologyFeatureKind.TEB_CROSS_MORPHOLOGY,
            availability=FeatureAvailability.MISSING_FEATURE_PROVIDER,
            provider_id=_receipt("pr257-missing-teb-provider"),
            units="not_available",
            missing_reason="E/B export sign and spin convention are not registered",
        ),
    )


def _reference():
    return build_lowell_morphology_feature_packet(
        sample_id="PR257-REFERENCE-SKY",
        alm_by_lm=_alm(),
        ell_values=(2, 3),
        additional_features=_features(),
        coordinate_frame="PR257 synthetic Cartesian frame",
        harmonic_convention=IMPLEMENTED_HARMONIC_CONVENTION,
        anchor_id=_receipt("pr257-typed-anchor"),
        anchor_stress_interval=(0.6, 0.7),
        mask_id=_receipt("pr257-mask"),
        beam_id=_receipt("pr257-beam"),
        foreground_model_id=_receipt("pr257-foreground"),
    )


@pytest.mark.parametrize(
    ("factor", "operator", "angle"),
    (
        (
            CounterpairFactor.PHASE,
            InterventionOperator.NONLINEAR_M_PHASE_V1,
            0.37,
        ),
        (
            CounterpairFactor.ORIENTATION,
            InterventionOperator.COMMON_PROPER_Z_ROTATION_V1,
            0.41,
        ),
        (
            CounterpairFactor.PARITY,
            InterventionOperator.SCALAR_PARITY_V1,
            None,
        ),
    ),
)
def test_exact_intervention_factories_build_matched_counterpairs(
    factor: CounterpairFactor,
    operator: InterventionOperator,
    angle: float | None,
) -> None:
    reference = _reference()
    intervention = LowEllInterventionSpec(
        factor=factor,
        operator=operator,
        angle_radians=angle,
    )
    transformed = apply_lowell_counterpair_intervention(
        reference=reference,
        intervention=intervention,
        sample_id=f"PR257-{factor.value}-SKY",
        additional_features=_features(),
    )
    report = build_matched_counterpair(
        pair_id=f"PR257-{factor.value}-PAIR",
        factor=factor,
        left=reference,
        right=transformed,
    )
    assert reference.cl_by_ell == transformed.cl_by_ell
    assert transformed.parent_packet_id == reference.packet_id
    assert transformed.intervention == intervention
    assert report.separated_feature_kinds
    assert set(report.missing_feature_kinds) == {
        MorphologyFeatureKind.DIRECTIONAL_WAVELET,
        MorphologyFeatureKind.TEB_CROSS_MORPHOLOGY,
    }
    assert revalidate_matched_counterpair(report).report_id == report.report_id
    if factor is CounterpairFactor.PARITY:
        assert transformed.parity_realization is ParityRealization.O3_REFLECTION
        for ell, m, real, imag in transformed.alm_entries:
            source = dict(
                ((left_ell, left_m), complex(left_real, left_imag))
                for left_ell, left_m, left_real, left_imag in reference.alm_entries
            )[(ell, m)]
            assert complex(real, imag) == pytest.approx(((-1) ** ell) * source)
    else:
        assert transformed.parity_realization is ParityRealization.REFERENCE


def test_phase_operator_rejects_identity_and_rotation_overlap() -> None:
    for angle in (0.0, math.pi, 2.0 * math.pi):
        with pytest.raises(LowEllCounterpairError):
            LowEllInterventionSpec(
                factor=CounterpairFactor.PHASE,
                operator=InterventionOperator.NONLINEAR_M_PHASE_V1,
                angle_radians=angle,
            )
    with pytest.raises(LowEllCounterpairError, match="does not match"):
        LowEllInterventionSpec(
            factor=CounterpairFactor.PHASE,
            operator=InterventionOperator.SCALAR_PARITY_V1,
            angle_radians=None,
        )


def test_feature_missingness_and_teb_convention_fail_closed() -> None:
    with pytest.raises(LowEllCounterpairError, match="must not carry values"):
        register_morphology_feature(
            kind=MorphologyFeatureKind.DIRECTIONAL_WAVELET,
            availability=FeatureAvailability.MISSING_FEATURE_PROVIDER,
            provider_id=_receipt("missing-with-zero"),
            units="not_available",
            values=(0.0,),
            missing_reason="provider absent",
        )
    with pytest.raises(LowEllCounterpairError, match="must remain"):
        build_lowell_morphology_feature_packet(
            sample_id="BAD-TEB",
            alm_by_lm=_alm(),
            ell_values=(2, 3),
            additional_features=(
                register_morphology_feature(
                    kind=MorphologyFeatureKind.DIRECTIONAL_WAVELET,
                    availability=FeatureAvailability.MISSING_FEATURE_PROVIDER,
                    provider_id=_receipt("wavelet"),
                    units="not_available",
                    missing_reason="missing",
                ),
                register_morphology_feature(
                    kind=MorphologyFeatureKind.TEB_CROSS_MORPHOLOGY,
                    availability=FeatureAvailability.AVAILABLE,
                    provider_id=_receipt("teb"),
                    source_alm_id=_receipt("teb-source"),
                    units="synthetic",
                    values=(0.0, 1.0),
                ),
            ),
            coordinate_frame="frame",
            harmonic_convention=IMPLEMENTED_HARMONIC_CONVENTION,
            anchor_id=_receipt("anchor"),
            anchor_stress_interval=(0.2, 0.3),
            mask_id=_receipt("mask"),
            beam_id=_receipt("beam"),
            foreground_model_id=_receipt("foreground"),
        )

    with pytest.raises(LowEllCounterpairError, match="factory-derived"):
        build_lowell_morphology_feature_packet(
            sample_id="BAD-CALLER-BIPOSH",
            alm_by_lm=_alm(),
            ell_values=(2, 3),
            additional_features=(
                register_morphology_feature(
                    kind=MorphologyFeatureKind.BIPOSH,
                    availability=FeatureAvailability.AVAILABLE,
                    provider_id=_receipt("caller-biposh"),
                    source_alm_id=_receipt("caller-source"),
                    units="synthetic",
                    values=(1.0,),
                ),
                *_features(),
            ),
            coordinate_frame="frame",
            harmonic_convention=IMPLEMENTED_HARMONIC_CONVENTION,
            anchor_id=_receipt("anchor"),
            anchor_stress_interval=(0.2, 0.3),
            mask_id=_receipt("mask"),
            beam_id=_receipt("beam"),
            foreground_model_id=_receipt("foreground"),
        )


def test_pair_rejects_factor_spoof_and_anchor_mismatch() -> None:
    reference = _reference()
    phase = LowEllInterventionSpec(
        factor=CounterpairFactor.PHASE,
        operator=InterventionOperator.NONLINEAR_M_PHASE_V1,
        angle_radians=0.3,
    )
    transformed = apply_lowell_counterpair_intervention(
        reference=reference,
        intervention=phase,
        sample_id="PHASE",
        additional_features=_features(),
    )
    with pytest.raises(LowEllCounterpairError, match="declared intervention"):
        build_matched_counterpair(
            pair_id="SPOOF",
            factor=CounterpairFactor.PARITY,
            left=reference,
            right=transformed,
        )
    different_reference = build_lowell_morphology_feature_packet(
        sample_id="DIFFERENT-ANCHOR",
        alm_by_lm=_alm(),
        ell_values=(2, 3),
        additional_features=_features(),
        coordinate_frame=reference.coordinate_frame,
        harmonic_convention=reference.harmonic_convention,
        anchor_id=_receipt("different-anchor"),
        anchor_stress_interval=reference.anchor_stress_interval,
        mask_id=reference.mask_id,
        beam_id=reference.beam_id,
        foreground_model_id=reference.foreground_model_id,
    )
    different_phase = apply_lowell_counterpair_intervention(
        reference=different_reference,
        intervention=phase,
        sample_id="DIFFERENT-PHASE",
        additional_features=_features(),
    )
    with pytest.raises(LowEllCounterpairError, match="anchor_id"):
        build_matched_counterpair(
            pair_id="ANCHOR-MISMATCH",
            factor=CounterpairFactor.PHASE,
            left=reference,
            right=different_phase,
        )

    provider_drift = apply_lowell_counterpair_intervention(
        reference=reference,
        intervention=phase,
        sample_id="PROVIDER-DRIFT",
        additional_features=_features(
            wavelet_provider_id=_receipt("different-wavelet-provider"),
        ),
    )
    with pytest.raises(LowEllCounterpairError, match="provider identity"):
        build_matched_counterpair(
            pair_id="PROVIDER-DRIFT",
            factor=CounterpairFactor.PHASE,
            left=reference,
            right=provider_drift,
        )


def test_pair_rejects_one_ulp_registered_cl_drift() -> None:
    reference = _reference()
    phase = LowEllInterventionSpec(
        factor=CounterpairFactor.PHASE,
        operator=InterventionOperator.NONLINEAR_M_PHASE_V1,
        angle_radians=0.37,
    )
    transformed = apply_lowell_counterpair_intervention(
        reference=reference,
        intervention=phase,
        sample_id="ONE-ULP-DRIFT",
        additional_features=_features(),
    )
    assert transformed.cl_by_ell == reference.cl_by_ell
    drifted = tuple(
        (
            ell,
            np.nextafter(value, math.inf) if ell == 3 else value,
        )
        for ell, value in transformed.cl_by_ell
    )
    object.__setattr__(transformed, "cl_by_ell", drifted)
    with pytest.raises(LowEllCounterpairError, match="identical exact C_ell"):
        build_matched_counterpair(
            pair_id="ONE-ULP-DRIFT",
            factor=CounterpairFactor.PHASE,
            left=reference,
            right=transformed,
        )


def test_pair_revalidates_factory_feature_provenance_at_evaluation() -> None:
    reference = _reference()
    phase = LowEllInterventionSpec(
        factor=CounterpairFactor.PHASE,
        operator=InterventionOperator.NONLINEAR_M_PHASE_V1,
        angle_radians=0.37,
    )
    transformed = apply_lowell_counterpair_intervention(
        reference=reference,
        intervention=phase,
        sample_id="STALE-BIPOSH-PROVENANCE",
        additional_features=_features(),
    )
    biposh = transformed.feature(MorphologyFeatureKind.BIPOSH)
    object.__setattr__(
        biposh,
        "source_alm_id",
        reference.feature(MorphologyFeatureKind.BIPOSH).source_alm_id,
    )
    with pytest.raises(
        LowEllCounterpairError,
        match="not bound|does not replay",
    ):
        build_matched_counterpair(
            pair_id="STALE-BIPOSH-PROVENANCE",
            factor=CounterpairFactor.PHASE,
            left=reference,
            right=transformed,
        )

    transformed = apply_lowell_counterpair_intervention(
        reference=reference,
        intervention=phase,
        sample_id="MUTATED-BIPOSH-VALUES",
        additional_features=_features(),
    )
    biposh = transformed.feature(MorphologyFeatureKind.BIPOSH)
    assert biposh.values is not None
    object.__setattr__(
        biposh,
        "values",
        (biposh.values[0] + 1.0, *biposh.values[1:]),
    )
    with pytest.raises(LowEllCounterpairError, match="does not replay"):
        build_matched_counterpair(
            pair_id="MUTATED-BIPOSH-VALUES",
            factor=CounterpairFactor.PHASE,
            left=reference,
            right=transformed,
        )

    transformed = apply_lowell_counterpair_intervention(
        reference=reference,
        intervention=phase,
        sample_id="MUTATED-INTERVENTION-RECEIPT",
        additional_features=_features(),
    )
    assert transformed.intervention is not None
    object.__setattr__(
        transformed.intervention,
        "intervention_id",
        _receipt("valid-but-unbound-intervention-id"),
    )
    with pytest.raises(LowEllCounterpairError, match="nested contract"):
        build_matched_counterpair(
            pair_id="MUTATED-INTERVENTION-RECEIPT",
            factor=CounterpairFactor.PHASE,
            left=reference,
            right=transformed,
        )
    mutated_phase = LowEllInterventionSpec(
        factor=CounterpairFactor.PHASE,
        operator=InterventionOperator.NONLINEAR_M_PHASE_V1,
        angle_radians=0.37,
    )
    object.__setattr__(
        mutated_phase,
        "intervention_id",
        _receipt("valid-but-unbound-apply-id"),
    )
    with pytest.raises(LowEllCounterpairError, match="not canonical"):
        apply_lowell_counterpair_intervention(
            reference=reference,
            intervention=mutated_phase,
            sample_id="REUSED-MUTATED-INTERVENTION",
            additional_features=_features(),
        )

    fresh_phase = LowEllInterventionSpec(
        factor=CounterpairFactor.PHASE,
        operator=InterventionOperator.NONLINEAR_M_PHASE_V1,
        angle_radians=0.37,
    )
    transformed = apply_lowell_counterpair_intervention(
        reference=reference,
        intervention=fresh_phase,
        sample_id="MUTATED-PHASE-RECEIPT",
        additional_features=_features(),
    )
    object.__setattr__(transformed, "phase_id", _receipt("wrong-phase"))
    with pytest.raises(LowEllCounterpairError, match="phase signature"):
        build_matched_counterpair(
            pair_id="MUTATED-PHASE-RECEIPT",
            factor=CounterpairFactor.PHASE,
            left=reference,
            right=transformed,
        )


@pytest.mark.parametrize(
    ("factor", "operator", "angle"),
    (
        (
            CounterpairFactor.PHASE,
            InterventionOperator.NONLINEAR_M_PHASE_V1,
            0.37,
        ),
        (
            CounterpairFactor.ORIENTATION,
            InterventionOperator.COMMON_PROPER_Z_ROTATION_V1,
            0.41,
        ),
        (
            CounterpairFactor.PARITY,
            InterventionOperator.SCALAR_PARITY_V1,
            None,
        ),
    ),
)
def test_intervention_receipt_is_bound_to_canonical_semantics(
    factor: CounterpairFactor,
    operator: InterventionOperator,
    angle: float | None,
) -> None:
    reference = _reference()
    intervention = LowEllInterventionSpec(
        factor=factor,
        operator=operator,
        angle_radians=angle,
    )
    assert intervention.intervention_id.startswith("sha256:")
    same = LowEllInterventionSpec(
        factor=factor,
        operator=operator,
        angle_radians=angle,
    )
    assert same.intervention_id == intervention.intervention_id

    receipt_substitution = LowEllInterventionSpec(
        factor=factor,
        operator=operator,
        angle_radians=angle,
    )
    object.__setattr__(
        receipt_substitution,
        "intervention_id",
        _receipt(f"substituted-{factor.value}-receipt"),
    )
    with pytest.raises(LowEllCounterpairError, match="not canonical"):
        apply_lowell_counterpair_intervention(
            reference=reference,
            intervention=receipt_substitution,
            sample_id=f"{factor.value}-SUBSTITUTED-RECEIPT",
            additional_features=_features(),
        )

    transformed = apply_lowell_counterpair_intervention(
        reference=reference,
        intervention=intervention,
        sample_id=f"{factor.value}-SEMANTIC-DRIFT",
        additional_features=_features(),
    )
    report = build_matched_counterpair(
        pair_id=f"{factor.value}-SEMANTIC-DRIFT",
        factor=factor,
        left=reference,
        right=transformed,
    )
    assert transformed.intervention is not None
    if factor is CounterpairFactor.PARITY:
        object.__setattr__(
            transformed.intervention,
            "factor",
            CounterpairFactor.ORIENTATION,
        )
        object.__setattr__(
            transformed.intervention,
            "operator",
            InterventionOperator.COMMON_PROPER_Z_ROTATION_V1,
        )
        object.__setattr__(transformed.intervention, "angle_radians", 0.41)
    else:
        assert angle is not None
        object.__setattr__(
            transformed.intervention,
            "angle_radians",
            angle + 0.04,
        )
    with pytest.raises(
        LowEllCounterpairError,
        match="nested contract|parity_realization",
    ):
        build_matched_counterpair(
            pair_id=f"{factor.value}-STALE-SEMANTIC-ID",
            factor=factor,
            left=reference,
            right=transformed,
        )
    with pytest.raises(
        LowEllCounterpairError,
        match="nested contract|parity_realization",
    ):
        revalidate_matched_counterpair(report)


def _normalizer() -> NormalizerSpec:
    return NormalizerSpec(
        normalizer_id="PR257-SHARED-RESPONSE-NORMALIZER",
        kind=NormalizerKind.FISHER_WHITENED,
        purposes=(NormalizerPurpose.RESPONSE_CONDITIONING,),
        coordinate_labels=("u0",),
        coordinate_map=((1.0,),),
        source_identity="PR257-SYNTHETIC-COMMON-PARAMETERIZATION",
    )


def _geometry(strength: float):
    covariance = np.eye(2)
    normalizer = _normalizer()
    geometry = measure_schur_morphology_information(
        baseline_response=((1.0,),),
        morphology_response=((strength,),),
        joint_covariance=covariance,
        normalizer=normalizer,
        parameter_labels=("u0",),
        transfer_id=_receipt("pr257-transfer-none"),
        transfer_source=TransferSource.NONE,
        mask_id=_receipt("pr257-common-mask"),
        joint_covariance_id=anchored_numeric_content_id(covariance),
        baseline_observable_id=_receipt("pr257-common-baseline"),
        morphology_observable_id=_receipt(f"pr257-morphology-{strength}"),
    )
    return geometry, normalizer


def _targets(rng: np.random.Generator, count: int) -> np.ndarray:
    values = np.tile(np.array((0, 1), dtype=np.int64), count // 2)
    return rng.permutation(values)


def _common_targets() -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    rng = np.random.default_rng(20260728)
    return tuple(_targets(rng, count) for count in (60, 40, 80))


def _common_partition_ids() -> tuple[str, str, str, str]:
    return tuple(
        _receipt(f"pr257-common-{role}-partition")
        for role in ("train", "validation", "heldout", "unknown")
    )


def _available_input(
    representation: MorphologyRepresentation,
    *,
    strength: float,
    seed: int,
) -> RepresentationBenchmarkInput:
    rng = np.random.default_rng(seed)
    counts = (60, 40, 80)
    targets = _common_targets()
    if representation is MorphologyRepresentation.SCALAR_X_C:
        features = tuple(np.zeros((count, 1)) for count in counts)
        unknown = np.zeros((80, 1))
    else:
        features = tuple(
            (2.0 * target[:, None] - 1.0)
            * strength
            + rng.normal(0.0, 0.15, size=(count, 1))
            for target, count in zip(targets, counts, strict=True)
        )
        unknown = rng.normal(20.0, 0.2, size=(80, 1))
    geometry, normalizer = _geometry(
        0.0 if representation is MorphologyRepresentation.SCALAR_X_C else strength
    )
    held = features[2]
    return RepresentationBenchmarkInput(
        representation=representation,
        availability=RepresentationAvailability.AVAILABLE,
        partition_ids=_common_partition_ids(),
        train_features=features[0],
        train_targets=targets[0],
        validation_features=features[1],
        validation_targets=targets[1],
        held_out_features=held,
        held_out_targets=targets[2],
        unknown_features=unknown,
        mask_perturbed_features=held + 0.02,
        beam_perturbed_features=held * 0.98,
        foreground_features=held + rng.normal(0.0, 0.05, size=held.shape),
        geometry=geometry,
        geometry_normalizer=normalizer,
    )


def _protocol() -> MorphologyBenchmarkProtocol:
    return MorphologyBenchmarkProtocol(
        protocol_id=_receipt("pr257-benchmark-protocol"),
        preregistration_id=_receipt("pr257-pre-sky-freeze"),
        catalogue_id=_receipt("pr257-catalogue"),
        master_seed=20260728,
        train_fraction=0.6,
        validation_fraction=0.2,
        held_out_fraction=0.2,
        confidence_margin_threshold=0.2,
        unknown_distance_threshold=6.0,
        maximum_mcse=0.0025,
        null_center_id=_receipt("pr257-train-null-center"),
        null_scale_id=_receipt("pr257-train-null-scale"),
        available_representations=tuple(MorphologyRepresentation)[:-2],
        missing_representations=tuple(MorphologyRepresentation)[-2:],
    )


def _benchmark_inputs() -> tuple[RepresentationBenchmarkInput, ...]:
    available = tuple(
        _available_input(
            representation,
            strength=0.7 + 0.2 * index,
            seed=1200 + index,
        )
        for index, representation in enumerate(
            tuple(MorphologyRepresentation)[:-2]
        )
    )
    missing = tuple(
        RepresentationBenchmarkInput(
            representation=representation,
            availability=RepresentationAvailability.MISSING_FEATURE_PROVIDER,
            partition_ids=_common_partition_ids(),
            missing_reason=(
                "provider unavailable before held-out scoring; no zero fill"
            ),
        )
        for representation in tuple(MorphologyRepresentation)[-2:]
    )
    return (*available, *missing)


def test_held_out_benchmark_uses_common_geometry_and_frozen_missingness() -> None:
    report = evaluate_morphology_benchmark(
        protocol=_protocol(),
        inputs=_benchmark_inputs(),
    )
    assert report.status is MorphologyBenchmarkStatus.INCONCLUSIVE_MC_PRECISION
    assert report.held_out_count == 80
    assert report.unknown_count == 80
    scalar = report.results[0]
    assert scalar.status is RepresentationBenchmarkStatus.DEGENERATE_ABSTENTION
    assert scalar.supported_rank == 0
    assert scalar.held_out_abstention_rate == 1.0
    assert scalar.generator_label_loss == 0.5
    assert scalar.zero_scale_coordinates == (0,)
    assert scalar.held_out_max_abs_z_q95 is None
    for result in report.results[1:-2]:
        assert result.status is RepresentationBenchmarkStatus.MEASURED
        assert result.supported_rank == 1
        assert result.generator_label_loss_reduction_from_scalar is not None
        assert (
            result.generator_label_loss_reduction_mcse_from_scalar
            is not None
        )
        assert result.generator_label_loss_reduction_mcse_from_scalar >= 0.0
        assert result.unknown_known_assignment_rate == 0.0
        assert result.zero_scale_coordinates == ()
        assert result.train_null_center_id.startswith("sha256:")
        assert result.train_null_scale_id.startswith("sha256:")
        assert result.held_out_max_abs_z_q95 is not None
        assert (
            result.geometry_payload["contraction"]["status"]
            in {
                "DEFINED_FULL_DIMENSION",
                "FINITE_COMMON_SUBSPACE_CONTRACTION",
                "RANK_GAIN_NO_FINITE_RATIO",
            }
        )
    assert all(
        item.status is RepresentationBenchmarkStatus.MISSING_FEATURE_PROVIDER
        for item in report.results[-2:]
    )
    assert report.observed_data_used is False
    assert report.pr151_data_used is False
    assert report.native_solver_output_used is False


def test_benchmark_rejects_postfreeze_availability_and_reused_splits() -> None:
    inputs = list(_benchmark_inputs())
    inputs[-1] = _available_input(
        MorphologyRepresentation.TEB_CROSS_MORPHOLOGY,
        strength=1.0,
        seed=9,
    )
    with pytest.raises(MorphologyBenchmarkError, match="frozen protocol mask"):
        evaluate_morphology_benchmark(protocol=_protocol(), inputs=inputs)

    base = _available_input(
        MorphologyRepresentation.FULL_DEPARTURE_STATE,
        strength=1.0,
        seed=17,
    )
    with pytest.raises(MorphologyBenchmarkError, match="feature bytes"):
        replace(
            base,
            validation_features=base.train_features,
            validation_targets=base.train_targets,
        )


def test_benchmark_rejects_unpaired_targets_and_partition_identity_drift() -> None:
    inputs = list(_benchmark_inputs())
    inputs[1] = replace(
        inputs[1],
        held_out_targets=np.roll(inputs[1].held_out_targets, 1),
    )
    with pytest.raises(MorphologyBenchmarkError, match="share target bytes"):
        evaluate_morphology_benchmark(protocol=_protocol(), inputs=inputs)

    inputs = list(_benchmark_inputs())
    inputs[1] = replace(
        inputs[1],
        partition_ids=tuple(
            _receipt(f"pr257-drifted-{role}-partition")
            for role in ("train", "validation", "heldout", "unknown")
        ),
    )
    with pytest.raises(
        MorphologyBenchmarkError,
        match="share train, validation, held-out, and unknown partition",
    ):
        evaluate_morphology_benchmark(protocol=_protocol(), inputs=inputs)


def test_benchmark_rejects_inconsistent_common_geometry_and_numeric_smuggling() -> None:
    geometry, different = _geometry(1.0)
    different = replace(
        different,
        source_identity="DIFFERENT-PARAMETERIZATION",
    )
    with pytest.raises(
        (MorphologyBenchmarkError, ValueError),
        match="normalizer|source_identity|content identity|replayed Schur geometry",
    ):
        replace(
            _benchmark_inputs()[1],
            geometry=geometry,
            geometry_normalizer=different,
        )

    base = _available_input(
        MorphologyRepresentation.FULL_DEPARTURE_STATE,
        strength=1.0,
        seed=22,
    )
    bad = np.asarray(base.train_features, dtype=object)
    bad[0, 0] = True
    with pytest.raises(MorphologyBenchmarkError, match="real, non-boolean"):
        replace(base, train_features=bad)


def test_benchmark_input_arrays_are_alias_safe_and_byte_backed() -> None:
    base = _available_input(
        MorphologyRepresentation.FULL_DEPARTURE_STATE,
        strength=1.0,
        seed=23,
    )
    caller_held_out = np.array(base.held_out_features, copy=True)
    protected = replace(base, held_out_features=caller_held_out)
    frozen_identities = protected.input_ids

    caller_held_out[:] = 1000.0
    assert protected.input_ids == frozen_identities
    assert not np.all(protected.held_out_features == caller_held_out)

    for name in (
        "train_features",
        "train_targets",
        "validation_features",
        "validation_targets",
        "held_out_features",
        "held_out_targets",
        "unknown_features",
        "mask_perturbed_features",
        "beam_perturbed_features",
        "foreground_features",
    ):
        stored = getattr(protected, name)
        assert stored.flags.writeable is False
        with pytest.raises(ValueError, match="WRITEABLE"):
            stored.setflags(write=True)


def test_worst_case_bernoulli_mcse_requires_at_least_40000() -> None:
    assert math.sqrt(0.25 / 20_000) > 0.0025
    assert math.sqrt(0.25 / 40_000) == pytest.approx(0.0025)
