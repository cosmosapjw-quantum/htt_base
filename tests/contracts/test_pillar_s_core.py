"""PR-271 exact/core Pillar-S statistical-foundation contracts."""

from __future__ import annotations

from dataclasses import replace
from fractions import Fraction
import hashlib
import json
import math
from pathlib import Path

import numpy as np
import pytest
import yaml

from common.conditional_exceedance import (
    ConditioningSource,
    ExceedanceLane,
    SamplingLaw,
    build_missing_probability_law_profile,
    build_null_calibrated_exceedance,
    build_sampling_draws,
    build_sampling_law_spec,
)
from common.vector_tensor_statistical_foundations import (
    CLAIM_CEILING,
    AcceptanceBoundaryRelation,
    AcceptanceBodyKind,
    AcceptanceBodySpec,
    EvidenceGrade,
    FoundationVerdict,
    PairingStatus,
    VectorTensorStatisticalFoundationError,
    certify_deterministic_scalarization,
    certify_finite_partition_tower,
    certify_samplewise_pushforward,
    certify_survival_monotonicity,
    compare_samplewise_ratio_to_ratio_of_means,
    evaluate_acceptance_gauge,
    exact_parity_sign_test,
    load_pillar_s_core_registry,
    paired_contrast_covariance,
)


ROOT = Path(__file__).resolve().parents[2]
SPEC = ROOT / "docs/research_program/vector_tensor/pr271_spec.yaml"
POLICY = ROOT / (
    "docs/research_program/vector_tensor/pr271_publication_policy.json"
)
REGISTRY = ROOT / (
    "docs/research_program/vector_tensor/proofs/"
    "PILLAR_S_CORE_PROOFS_V1.yaml"
)
BACKLOG = ROOT / "docs/codex_handoff/pr_backlog.yaml"


@pytest.fixture(scope="module")
def registry():
    return load_pillar_s_core_registry(ROOT)


def test_spec_and_backlog_bind_pr271_scope_and_dependencies() -> None:
    spec = yaml.safe_load(SPEC.read_text(encoding="utf-8"))
    backlog = yaml.safe_load(BACKLOG.read_text(encoding="utf-8"))
    card = next(card for card in backlog["prs"] if card["id"] == "PR-271")
    assert spec["pr_id"] == "PR-271"
    assert spec["dependencies"] == ["PR-268"]
    assert card["depends"] == ["PR-268"]
    assert card["owner"] == "HTT"
    assert set(card["contributors"]) == {"COMMON", "OBSSTAT"}
    assert spec["claim_ceiling"] == CLAIM_CEILING
    assert spec["selection"]["vt_exact_core"]["exact_ids"] == [
        "VT-S1",
        "VT-S2",
        "VT-S4",
        "VT-S7",
        "VT-S8",
    ]
    tf09 = spec["typed_statements"]["TF-09-PARITY-SIGN-EXACTNESS"]
    assert any(
        "uniform" in assumption
        for assumption in tf09["assumptions"]
    )
    tf11 = spec["typed_statements"]["TF-11-MASK-PATH-MARTINGALE"]
    assert any(
        "common target" in assumption
        for assumption in tf11["assumptions"]
    )
    vt8 = spec["typed_statements"]["VT-S8"]["statement"]
    assert "C_omitted-C_actual=C_ab+C_ba" in vt8


def test_registry_has_exact_34_plus_5_plus_2_partition(registry) -> None:
    legacy = tuple(
        row for row in registry.records if row.source_group == "LEGACY_S"
    )
    vt_rows = tuple(
        row for row in registry.records if row.source_group == "VT_S"
    )
    tf_rows = tuple(
        row for row in registry.records if row.source_group == "TF_S"
    )
    assert len(legacy) == 34
    assert {row.obligation_id for row in vt_rows} == {
        "VT-S1",
        "VT-S2",
        "VT-S4",
        "VT-S7",
        "VT-S8",
    }
    assert {row.obligation_id for row in tf_rows} == {
        "TF-09-PARITY-SIGN-EXACTNESS",
        "TF-11-MASK-PATH-MARTINGALE",
    }
    reference = {
        row.obligation_id
        for row in legacy
        if row.verdict
        is FoundationVerdict.REFERENCE_RESOLVED_WITH_SCALAR_REDUCTION
    }
    assert reference == {
        "SIG-P18",
        "SIG-T1p",
        "SIG-DL1",
        "SIG-L-T2-EXIST",
        "SIG-T2G",
    }
    assert sum(
        row.verdict is FoundationVerdict.INCONCLUSIVE_MISSING_SIGNATURE
        for row in legacy
    ) == 29
    assert all(
        row.source_proof_adjudication_status == "NOT_ADJUDICATED"
        for row in registry.records
    )
    assert all(row.claim_ceiling == CLAIM_CEILING for row in registry.records)
    with pytest.raises(
        VectorTensorStatisticalFoundationError,
        match="not an accepted proof count",
    ):
        registry.reject_raw_proof_count(len(registry.records))


def test_registry_exactness_grades_do_not_hide_finite_boundaries(registry) -> None:
    assert (
        registry.record("TF-11-MASK-PATH-MARTINGALE").evidence_grade
        is EvidenceGrade.FINITE_REGISTERED_EXACT
    )
    assert (
        registry.record("TF-11-MASK-PATH-MARTINGALE").verdict
        is FoundationVerdict.PROVED_FINITE_REGISTERED_PATH
    )
    assert (
        registry.record("TF-09-PARITY-SIGN-EXACTNESS").evidence_grade
        is EvidenceGrade.EXACT_ANALYTIC
    )
    assert all(
        row.evidence_grade is not EvidenceGrade.SIMULATION_DIAGNOSTIC
        for row in registry.records
        if row.verdict
        in {
            FoundationVerdict.PROVED_ANALYTIC_UNDER_TYPED_PREMISES,
            FoundationVerdict.PROVED_FINITE_REGISTERED_PATH,
        }
    )
    assert any(
        "fast-oracle" in boundary
        for boundary in registry.record(
            "TF-11-MASK-PATH-MARTINGALE"
        ).counterexample_boundaries
    )


def test_registry_generator_is_deterministic() -> None:
    import subprocess
    import sys

    subprocess.run(
        [
            sys.executable,
            "-B",
            str(
                ROOT
                / "scripts/codex_harness/build_pr271_pillar_s_core.py"
            ),
            "--check",
        ],
        cwd=ROOT,
        check=True,
    )


def test_registry_hostile_mutations_fail_closed(tmp_path: Path) -> None:
    payload = yaml.safe_load(REGISTRY.read_text(encoding="utf-8"))

    def write(mutated, name):
        path = tmp_path / name
        path.write_text(
            yaml.safe_dump(mutated, sort_keys=False),
            encoding="utf-8",
        )
        return path

    promoted = yaml.safe_load(REGISTRY.read_text(encoding="utf-8"))
    promoted["records"][0]["source_proof_adjudication_status"] = "PROVED"
    with pytest.raises(
        VectorTensorStatisticalFoundationError,
        match="registry bytes drifted",
    ):
        load_pillar_s_core_registry(ROOT, write(promoted, "promoted.yaml"))

    duplicate = yaml.safe_load(REGISTRY.read_text(encoding="utf-8"))
    duplicate["records"].append(dict(duplicate["records"][0]))
    duplicate["canonical_records_sha256"] = hashlib.sha256(
        json.dumps(
            duplicate["records"],
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
        ).encode("ascii")
    ).hexdigest()
    with pytest.raises(
        VectorTensorStatisticalFoundationError,
        match="registry bytes drifted",
    ):
        load_pillar_s_core_registry(ROOT, write(duplicate, "duplicate.yaml"))

    simulated = yaml.safe_load(REGISTRY.read_text(encoding="utf-8"))
    vt = next(
        row for row in simulated["records"] if row["obligation_id"] == "VT-S1"
    )
    vt["evidence_grade"] = "SIMULATION_DIAGNOSTIC"
    with pytest.raises(
        VectorTensorStatisticalFoundationError,
        match="registry bytes drifted",
    ):
        load_pillar_s_core_registry(ROOT, write(simulated, "simulated.yaml"))

    missing = yaml.safe_load(REGISTRY.read_text(encoding="utf-8"))
    missing["records"] = [
        row for row in missing["records"] if row["obligation_id"] != "VT-S8"
    ]
    missing["canonical_records_sha256"] = "forged"
    with pytest.raises(
        VectorTensorStatisticalFoundationError,
        match="registry bytes drifted",
    ):
        load_pillar_s_core_registry(ROOT, write(missing, "missing.yaml"))

    assert payload["raw_count_publication"] == "FORBIDDEN"


def test_vt_s1_deterministic_scalarization_obeys_tv_and_kl() -> None:
    report = certify_deterministic_scalarization(
        profile_labels=("p0", "p1", "p2", "p3"),
        scalar_labels=("low", "low", "high", "high"),
        law_p=(0.4, 0.1, 0.2, 0.3),
        law_q=(0.1, 0.2, 0.4, 0.3),
        registered_decisions=("A", "A", "B", "B"),
    )
    assert report.scalar_total_variation <= report.profile_total_variation
    assert report.scalar_kl <= report.profile_kl
    assert report.decision_sufficient is True

    lossy = certify_deterministic_scalarization(
        profile_labels=("p0", "p1"),
        scalar_labels=("same", "same"),
        law_p=(1.0, 0.0),
        law_q=(0.0, 1.0),
        registered_decisions=("A", "B"),
    )
    assert math.isinf(lossy.profile_kl)
    assert lossy.scalar_kl == pytest.approx(0.0)
    assert lossy.decision_sufficient is False


def test_vt_s1_refuses_nonfunctional_or_malformed_laws() -> None:
    with pytest.raises(
        VectorTensorStatisticalFoundationError,
        match="not a deterministic function",
    ):
        certify_deterministic_scalarization(
            profile_labels=("same", "same"),
            scalar_labels=("a", "b"),
            law_p=(0.5, 0.5),
            law_q=(0.5, 0.5),
        )
    with pytest.raises(
        VectorTensorStatisticalFoundationError,
        match="summing to one",
    ):
        certify_deterministic_scalarization(
            profile_labels=("a", "b"),
            scalar_labels=("a", "b"),
            law_p=(0.4, 0.4),
            law_q=(0.5, 0.5),
        )
    with pytest.raises(
        VectorTensorStatisticalFoundationError,
        match="summing to one",
    ):
        certify_deterministic_scalarization(
            profile_labels=("only",),
            scalar_labels=("only",),
            law_p=(1.0,),
            law_q=(1.0 + 5.0e-13,),
        )
    with pytest.raises(
        VectorTensorStatisticalFoundationError,
        match="profile label must be hashable",
    ):
        certify_deterministic_scalarization(
            profile_labels=(["a"],),
            scalar_labels=("a",),
            law_p=(1.0,),
            law_q=(1.0,),
        )


def test_vt_s2_unifies_scalar_box_max_and_ellipsoid_gauges() -> None:
    box = AcceptanceBodySpec(
        body_id="PR271-BOX",
        kind=AcceptanceBodyKind.COORDINATE_THRESHOLDS,
        coordinate_labels=("x", "y"),
        radii=(2.0, 4.0),
    )
    weighted_max = AcceptanceBodySpec(
        body_id="PR271-MAX",
        kind=AcceptanceBodyKind.WEIGHTED_MAX,
        coordinate_labels=("x", "y"),
        radii=(2.0, 4.0),
    )
    point = (1.0, -3.0)
    assert evaluate_acceptance_gauge(box, point).q_value == pytest.approx(0.75)
    assert evaluate_acceptance_gauge(
        weighted_max, point
    ).q_value == pytest.approx(0.75)

    scalar = AcceptanceBodySpec(
        body_id="PR271-SCALAR",
        kind=AcceptanceBodyKind.ONE_DIMENSIONAL_INTERVAL,
        coordinate_labels=("legacy_x",),
        radii=(0.17,),
    )
    assert evaluate_acceptance_gauge(
        scalar, (-0.17,)
    ).q_value == pytest.approx(1.0)
    scalar_report = evaluate_acceptance_gauge(scalar, (-0.17,))
    assert scalar_report.exact_acceptance_relation is (
        AcceptanceBoundaryRelation.EQ
    )
    assert scalar_report.accepted

    covariance = ((2.0, 0.5), (0.5, 1.0))
    ellipsoid = AcceptanceBodySpec(
        body_id="PR271-ELLIPSOID",
        kind=AcceptanceBodyKind.COVARIANCE_ELLIPSOID,
        coordinate_labels=("x", "y"),
        covariance=covariance,
    )
    expected = math.sqrt(
        np.asarray(point) @ np.linalg.solve(covariance, np.asarray(point))
    )
    assert evaluate_acceptance_gauge(
        ellipsoid, point
    ).q_value == pytest.approx(expected)


def test_vt_s2_rank_symmetry_and_dimension_mutations_refuse() -> None:
    with pytest.raises(
        VectorTensorStatisticalFoundationError,
        match="positive-definite",
    ):
        AcceptanceBodySpec(
            body_id="PR271-SINGULAR",
            kind=AcceptanceBodyKind.COVARIANCE_ELLIPSOID,
            coordinate_labels=("x", "y"),
            covariance=((1.0, 1.0), (1.0, 1.0)),
        )
    with pytest.raises(
        VectorTensorStatisticalFoundationError,
        match="exactly symmetric",
    ):
        AcceptanceBodySpec(
            body_id="PR271-NONSYMMETRIC",
            kind=AcceptanceBodyKind.COVARIANCE_ELLIPSOID,
            coordinate_labels=("x", "y"),
            covariance=((1.0, 0.2), (0.1, 1.0)),
        )
    spec = AcceptanceBodySpec(
        body_id="PR271-DIM",
        kind=AcceptanceBodyKind.WEIGHTED_MAX,
        coordinate_labels=("x", "y"),
        radii=(1.0, 1.0),
    )
    with pytest.raises(
        VectorTensorStatisticalFoundationError,
        match="dimension",
    ):
        evaluate_acceptance_gauge(spec, (1.0,))
    with pytest.raises(
        VectorTensorStatisticalFoundationError,
        match="radii must be finite",
    ):
        AcceptanceBodySpec(
            body_id="PR271-OVERFLOW",
            kind=AcceptanceBodyKind.WEIGHTED_MAX,
            coordinate_labels=("x",),
            radii=(10**10000,),
        )
    with pytest.raises(
        VectorTensorStatisticalFoundationError,
        match="positive-definite",
    ):
        AcceptanceBodySpec(
            body_id="PR271-INDEFINITE",
            kind=AcceptanceBodyKind.COVARIANCE_ELLIPSOID,
            coordinate_labels=("x", "y"),
            covariance=((1.0, 2.0), (2.0, 1.0)),
        )


def test_vt_s2_exact_spd_gate_accepts_cholesky_counterexample() -> None:
    covariance = (
        (1.0, 0.9999999999999997, 0.9999999999999999),
        (0.9999999999999997, 1.0, 0.9999999999999999),
        (0.9999999999999999, 0.9999999999999999, 1.0),
    )
    exact = tuple(
        tuple(Fraction.from_float(value) for value in row)
        for row in covariance
    )
    leading_two = (
        exact[0][0] * exact[1][1] - exact[0][1] * exact[1][0]
    )
    determinant = (
        exact[0][0]
        * (exact[1][1] * exact[2][2] - exact[1][2] * exact[2][1])
        - exact[0][1]
        * (exact[1][0] * exact[2][2] - exact[1][2] * exact[2][0])
        + exact[0][2]
        * (exact[1][0] * exact[2][1] - exact[1][1] * exact[2][0])
    )
    assert exact[0][0] > 0
    assert leading_two > 0
    assert determinant > 0
    body = AcceptanceBodySpec(
        body_id="PR271-EXACT-SPD",
        kind=AcceptanceBodyKind.COVARIANCE_ELLIPSOID,
        coordinate_labels=("x", "y", "z"),
        covariance=covariance,
    )
    report = evaluate_acceptance_gauge(body, (1.0, -1.0, 0.0))
    assert math.isfinite(report.q_value)
    assert report.q_value > 0.0


def test_vt_s2_acceptance_uses_exact_relation_not_rounded_display() -> None:
    covariance = math.nextafter(1.0, 0.0)
    ellipsoid = AcceptanceBodySpec(
        body_id="PR271-ROUNDED-ELLIPSOID",
        kind=AcceptanceBodyKind.COVARIANCE_ELLIPSOID,
        coordinate_labels=("x",),
        covariance=((covariance,),),
    )
    ellipsoid_report = evaluate_acceptance_gauge(ellipsoid, (1.0,))
    assert ellipsoid_report.q_value == 1.0
    assert ellipsoid_report.exact_acceptance_relation is (
        AcceptanceBoundaryRelation.GT
    )
    assert not ellipsoid_report.accepted

    box = AcceptanceBodySpec(
        body_id="PR271-EXACT-BOX-BOUNDARY",
        kind=AcceptanceBodyKind.COORDINATE_THRESHOLDS,
        coordinate_labels=("x",),
        radii=(covariance,),
    )
    box_report = evaluate_acceptance_gauge(box, (1.0,))
    assert box_report.exact_acceptance_relation is (
        AcceptanceBoundaryRelation.GT
    )
    assert not box_report.accepted


def test_vt_s1_exact_probability_encoding_keeps_kl_nonnegative() -> None:
    denominator = 10**40
    report = certify_deterministic_scalarization(
        profile_labels=("a", "b"),
        scalar_labels=("same", "same"),
        law_p=(
            Fraction(1, denominator),
            Fraction(denominator - 1, denominator),
        ),
        law_q=(
            Fraction(2, denominator),
            Fraction(denominator - 2, denominator),
        ),
    )
    assert report.profile_kl >= 0.0
    assert report.scalar_kl == 0.0
    assert report.scalar_kl <= report.profile_kl
    assert report.kl_stability_verified
    assert report.kl_decimal_precision >= 120


def test_vt_s1_adaptive_kl_precision_preserves_near_equal_dpi() -> None:
    denominator = 10**120
    quarter = denominator // 4
    report = certify_deterministic_scalarization(
        profile_labels=("a", "b", "c", "d"),
        scalar_labels=("x", "x", "y", "y"),
        law_p=(Fraction(1, 4),) * 4,
        law_q=(
            Fraction(quarter + 6, denominator),
            Fraction(quarter - 2, denominator),
            Fraction(quarter - 3, denominator),
            Fraction(quarter - 1, denominator),
        ),
    )
    assert report.profile_kl > 0.0
    assert report.scalar_kl > 0.0
    assert report.scalar_kl <= report.profile_kl
    assert report.profile_kl == pytest.approx(1.0e-238, rel=1.0e-12)
    assert report.scalar_kl == pytest.approx(3.2e-239, rel=1.0e-12)
    assert report.kl_decimal_precision > 400
    assert report.kl_stability_verified


def test_vt_s1_unrepresentable_nonzero_kl_projection_refuses() -> None:
    denominator = 10**200
    half = denominator // 2
    with pytest.raises(
        VectorTensorStatisticalFoundationError,
        match="finite and representable",
    ):
        certify_deterministic_scalarization(
            profile_labels=("a", "b"),
            scalar_labels=("same", "same"),
            law_p=(Fraction(1, 2), Fraction(1, 2)),
            law_q=(
                Fraction(half + 1, denominator),
                Fraction(half - 1, denominator),
            ),
        )


def _null_profile():
    law = build_sampling_law_spec(
        law_id="PR271-NULL-LAW",
        sampling_law=SamplingLaw.FIXED_INJECTION_MOCK,
        conditioning_source=ConditioningSource.INJECTED,
        lane=ExceedanceLane.MIO_NULL,
        source_identity="PR271 finite registered null",
        covariance_id="PR271-COV",
        transfer_source="none",
        assumptions=("exchangeable under the registered finite null",),
    )
    draws = build_sampling_draws(
        draws_id="PR271-DRAWS",
        law=law,
        values=(0.1, 0.2, 0.5, 1.0),
        source_artifact_id="PR271-SYNTHETIC",
        sample_unit="dimensionless Q",
    )
    return build_null_calibrated_exceedance(
        profile_id="PR271-PI",
        functional_id="pr271.q",
        thresholds=(0.0, 0.3, 0.8, 1.2),
        law=law,
        draws=draws,
        conditioning_id="PR271-CONDITION",
        alpha=0.05,
    ).profile


def test_vt_s4_certifies_typed_survival_monotonicity() -> None:
    profile = _null_profile()
    report = certify_survival_monotonicity(profile)
    assert report.sampling_law == SamplingLaw.FIXED_INJECTION_MOCK.value
    assert report.lane == ExceedanceLane.MIO_NULL.value
    assert report.threshold_count == 4
    assert report.exact_empirical_measure_statement
    assert all(
        left >= right
        for left, right in zip(profile.point, profile.point[1:])
    )


def test_vt_s4_refusal_profile_is_not_promoted() -> None:
    refusal = build_missing_probability_law_profile(
        profile_id="PR271-NO-LAW",
        functional_id="pr271.q",
        thresholds=(0.0, 1.0),
        conditioning_id="PR271-CONDITION",
        reason="no law admitted",
    )
    with pytest.raises(
        VectorTensorStatisticalFoundationError,
        match="defined probability-law",
    ):
        certify_survival_monotonicity(refusal)


def test_vt_s7_keeps_samplewise_pushforward_and_plug_in_distinct() -> None:
    comparison = compare_samplewise_ratio_to_ratio_of_means(
        (1.0, 9.0), (1.0, 3.0)
    )
    assert comparison.samplewise_ratios == (1.0, 3.0)
    assert comparison.mean_of_samplewise_ratios == pytest.approx(2.0)
    assert comparison.ratio_of_means == pytest.approx(2.5)
    assert not comparison.interchangeable
    with pytest.raises(
        VectorTensorStatisticalFoundationError,
        match="nonzero",
    ):
        compare_samplewise_ratio_to_ratio_of_means((1.0,), (0.0,))
    with pytest.raises(
        VectorTensorStatisticalFoundationError,
        match="must remain finite",
    ):
        compare_samplewise_ratio_to_ratio_of_means(
            (1.0e308,), (1.0e-308,)
        )


def test_vt_s7_revalidates_existing_certified_pushforward() -> None:
    from tests.contracts.test_tensor_departure_statistics import _pushforward

    pushforward = _pushforward((0.5, 1.0))
    report = certify_samplewise_pushforward(pushforward)
    assert report.sample_count == 2
    assert report.functional_count == 3
    assert report.complete_cell_count == 6
    assert report.missing_or_ineligible_cell_count == 0
    with pytest.raises(TypeError, match="exact"):
        certify_samplewise_pushforward(object())


def test_vt_s8_paired_covariance_and_signed_omission_identity() -> None:
    aa = np.eye(2)
    bb = np.asarray(((1.5, 0.1), (0.1, 1.2)))
    ab = np.asarray(((0.2, 0.1), (0.0, 0.3)))
    ba = ab.T
    report = paired_contrast_covariance(
        covariance_aa=aa,
        covariance_bb=bb,
        covariance_ab=ab,
        covariance_ba=ba,
        pairing_status=PairingStatus.PAIRED_JOINT_LAW,
    )
    actual = np.asarray(report.contrast_covariance)
    omitted = np.asarray(report.omitted_cross_covariance)
    assert np.allclose(actual, aa + bb - ab - ba)
    assert np.allclose(
        np.asarray(report.omitted_minus_actual), ab + ba
    )
    assert np.allclose(
        np.asarray(report.actual_minus_omitted), -(ab + ba)
    )
    assert np.allclose(omitted - actual, ab + ba)


def test_vt_s8_refuses_marginal_only_and_cross_block_mutations() -> None:
    kwargs = {
        "covariance_aa": ((1.0, 0.0), (0.0, 1.0)),
        "covariance_bb": ((1.0, 0.0), (0.0, 1.0)),
        "covariance_ab": ((0.1, 0.2), (0.0, 0.1)),
        "covariance_ba": ((0.1, 0.0), (0.2, 0.1)),
    }
    with pytest.raises(
        VectorTensorStatisticalFoundationError,
        match="cannot be relabelled",
    ):
        paired_contrast_covariance(
            **kwargs,
            pairing_status=PairingStatus.INDEPENDENT_MARGINALS_ONLY,
        )
    with pytest.raises(
        VectorTensorStatisticalFoundationError,
        match=r"C_ba=C_ab\^T",
    ):
        paired_contrast_covariance(
            **{**kwargs, "covariance_ba": ((0.1, 0.2), (0.0, 0.1))},
            pairing_status=PairingStatus.PAIRED_JOINT_LAW,
        )
    with pytest.raises(
        VectorTensorStatisticalFoundationError,
        match="calculation must remain finite",
    ):
        paired_contrast_covariance(
            covariance_aa=((1.0e308,),),
            covariance_bb=((1.0e308,),),
            covariance_ab=((0.0,),),
            covariance_ba=((0.0,),),
            pairing_status=PairingStatus.PAIRED_JOINT_LAW,
        )
    with pytest.raises(
        VectorTensorStatisticalFoundationError,
        match="positive semidefinite",
    ):
        paired_contrast_covariance(
            covariance_aa=((-1.0e290,),),
            covariance_bb=((1.0e308,),),
            covariance_ab=((0.0,),),
            covariance_ba=((0.0,),),
            pairing_status=PairingStatus.PAIRED_JOINT_LAW,
        )


def test_vt_s8_exact_psd_gate_preserves_singular_and_dynamic_range() -> None:
    singular = paired_contrast_covariance(
        covariance_aa=((1.0,),),
        covariance_bb=((1.0,),),
        covariance_ab=((1.0,),),
        covariance_ba=((1.0,),),
        pairing_status=PairingStatus.PAIRED_JOINT_LAW,
    )
    assert singular.joint_rank == 1
    assert singular.contrast_covariance == ((0.0,),)

    dynamic = paired_contrast_covariance(
        covariance_aa=((1.0e-290,),),
        covariance_bb=((1.0e308,),),
        covariance_ab=((0.0,),),
        covariance_ba=((0.0,),),
        pairing_status=PairingStatus.PAIRED_JOINT_LAW,
    )
    assert dynamic.joint_rank == 2


def test_tf09_exact_sign_test_conditions_on_nonzero_ties() -> None:
    report = exact_parity_sign_test(
        (1.0, 2.0, 3.0, -1.0, 0.0),
        parity_odd=True,
        uniform_conditional_sign_vector=True,
    )
    assert report.positive_count == 3
    assert report.negative_count == 1
    assert report.tie_count == 1
    assert report.conditioned_nonzero_count == 4
    assert report.two_sided_p_value == Fraction(5, 8)


def test_tf09_global_symmetry_or_parity_erasure_refuses() -> None:
    with pytest.raises(
        VectorTensorStatisticalFoundationError,
        match="uniform conditional",
    ):
        exact_parity_sign_test(
            (1.0, -1.0),
            parity_odd=True,
            uniform_conditional_sign_vector=False,
        )
    with pytest.raises(
        VectorTensorStatisticalFoundationError,
        match="parity-odd",
    ):
        exact_parity_sign_test(
            (1.0, -1.0),
            parity_odd=False,
            uniform_conditional_sign_vector=True,
        )


def test_tf11_exact_finite_partition_tower() -> None:
    report = certify_finite_partition_tower(
        weights=(Fraction(1, 4),) * 4,
        common_target=(0, 2, 4, 6),
        partitions=(
            ("all", "all", "all", "all"),
            ("left", "left", "right", "right"),
            ("a", "b", "c", "d"),
        ),
    )
    assert report.rung_count == 3
    assert report.atom_count == 4
    assert report.exact_equalities == (True, True)
    assert dict(report.conditional_expectations[0])["all"] == "3/1"


def test_tf11_refuses_support_nesting_substitutes_and_inexact_weights() -> None:
    with pytest.raises(
        VectorTensorStatisticalFoundationError,
        match="does not refine",
    ):
        certify_finite_partition_tower(
            weights=(Fraction(1, 4),) * 4,
            common_target=(0, 2, 4, 6),
            partitions=(
                ("left", "left", "right", "right"),
                ("x", "y", "x", "y"),
            ),
        )
    with pytest.raises(
        VectorTensorStatisticalFoundationError,
        match="exact rational",
    ):
        certify_finite_partition_tower(
            weights=(0.5, 0.5),
            common_target=(0, 1),
            partitions=(("all", "all"), ("a", "b")),
        )
    with pytest.raises(
        VectorTensorStatisticalFoundationError,
        match="at least two partition rungs",
    ):
        certify_finite_partition_tower(
            weights=(Fraction(1, 1),),
            common_target=(0,),
            partitions=1,  # type: ignore[arg-type]
        )


def test_claim_ceiling_and_owner_boundaries_are_non_inferential(registry) -> None:
    surfaces = (
        SPEC.read_text(encoding="utf-8")
        + POLICY.read_text(encoding="utf-8")
        + REGISTRY.read_text(encoding="utf-8")
    )
    assert "simulation-only evidence promoted to exact" in surfaces
    assert "model-dependent inference outside HTT ownership" in surfaces
    assert all(row.claim_ceiling == "diagnostic_only" for row in registry.records)
    assert "Bianchi family identified" not in surfaces


def test_record_dataclass_refuses_simulation_exact_promotion(registry) -> None:
    source = registry.record("VT-S1")
    with pytest.raises(
        VectorTensorStatisticalFoundationError,
        match="simulation-only",
    ):
        replace(
            source,
            evidence_grade=EvidenceGrade.SIMULATION_DIAGNOSTIC,
        )
