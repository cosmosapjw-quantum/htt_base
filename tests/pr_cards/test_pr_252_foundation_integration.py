"""PR-252 cross-package migration and claim-boundary integration checks."""
from __future__ import annotations

import ast
from dataclasses import fields, replace
import json
from pathlib import Path
import types

import pytest
import yaml

from bass.validation.comparator_policy import ComparatorPolicy
from common.contracts import ArtifactManifest
from common.mes_successor_registry import (
    MesConsumerDeclaration,
    SourceAvailability,
    SourceHashBinding,
    scan_declared_mes_consumers,
    validate_mes_successor_registry,
)
from common.statistical_foundations import (
    AnchorConditioning,
    AnchorStatus,
    AnchorStressReport,
    BC1_LEGACY_PROJECTION,
    BC2_NO_REPRESENTATION_PROMOTION,
    DepartureState,
    DiagnosticScalarReport,
    IdentificationStatus,
    IdentifiedDepartureSet,
    LegacyProjectionReport,
    NullKind,
    ScalarRange,
    StatisticalFoundationError,
    SummaryDepartureState,
    build_anchor_stress_report,
    evaluate_sector_stress,
    quarantined_shear_anchors,
    registered_geodesic_mes_anchors,
)
from workspace.contracts.htt_to_mio import MioCrossCheckExport


REPO_ROOT = Path(__file__).resolve().parents[2]


def _directional_payload() -> dict[str, object]:
    return {
        "artifact_kind": "htt_directional_posterior_summary_v2",
        "artifact_name": "directional.json",
        "model": "FLRW_tilt",
        "legacy_projection_summary": {
            "classification": BC1_LEGACY_PROJECTION,
            "representation_policy": BC2_NO_REPRESENTATION_PROMOTION,
            "status": "LEGACY_REPRODUCTION",
            "allowed_use": [
                "historical value reproduction",
                "diagnostic cross-check",
            ],
            "forbidden_use": [
                "posterior estimand",
                "departure distance",
                "occupancy",
                "probability",
                "evidence",
                "family identification",
            ],
            "values": {
                "x_C": {
                    "median": 0.2,
                    "hpd_68": [0.1, 0.3],
                    "hpd_95": [0.05, 0.35],
                },
                "Q": {"median": 0.4, "hpd_68": [0.2, 0.5]},
                "Pi": {"median": 0.1, "hpd_68": [0.05, 0.2]},
                "F": {"median": 0.07, "hpd_68": [0.05, 0.09]},
            },
        },
        "evidence_summary": {
            "lnB_total": 5.0,
            "model_evidences": {"FLRW_tilt": 5.0, "FLRW": 0.0},
            "n_live": 128,
        },
        "refs": {
            "posterior_ref": "results.json#departure/FLRW_tilt",
            "evidence_ref": "results.json#evidence/FLRW_tilt",
            "posterior_predictive_ref": None,
            "loocv_ref": None,
        },
        "manifest": {
            "artifact_id": "htt.directional.fixture",
            "artifact_path": "artifacts/htt/directional.json",
            "owner": "HTT",
            "implementation_scope": "htt",
            "claim_tier": "diagnostic_only",
            "production_status": "diagnostic_only",
            "created_by": "test-suite",
            "git_commit": "fixture",
            "config_hash": "fixture-config",
            "input_hashes": ["fixture-input"],
            "code_version": "fixture",
            "schema_version": "v2",
        },
    }


def _diagnostic_manifest() -> ArtifactManifest:
    return ArtifactManifest(
        artifact_id="htt.directional.fixture",
        artifact_path="artifacts/htt/directional.json",
        owner="HTT",
        implementation_scope="htt",
        claim_tier="diagnostic_only",
        production_status="diagnostic_only",
        created_by="test-suite",
        git_commit="fixture",
        config_hash="fixture-config",
        input_hashes=["fixture-input"],
        code_version="fixture",
        schema_version="v2",
    )


def _yaml(path: str) -> dict[str, object]:
    payload = yaml.safe_load((REPO_ROOT / path).read_text(encoding="utf-8"))
    assert isinstance(payload, dict)
    return payload


def _defined_names(path: str) -> set[str]:
    tree = ast.parse((REPO_ROOT / path).read_text(encoding="utf-8"))
    names = {
        node.name
        for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
    }
    names.update(
        alias.asname or alias.name
        for node in ast.walk(tree)
        if isinstance(node, (ast.Import, ast.ImportFrom))
        for alias in node.names
    )
    return names


def _state() -> DepartureState:
    return DepartureState(
        sigma_ab=(0.2, -0.1, 0.05, 0.0, 0.02),
        omega_a=(0.01, 0.02, 0.03),
        beta_a=(0.04, 0.05, 0.06),
        delta_omega_k=-0.01,
        frame="registered tetrad",
        congruence="geodesic",
        epoch_window="fixture epoch",
        averaging_scale="fixture scale",
        basis="stf5-cartesian-v1",
        units="dimensionless H-normalized",
        parity="sigma even; omega axial; beta polar",
        perturbative_order="kinematic state",
    )


def test_active_namespaces_exclude_scalar_mes_and_occupancy_helpers() -> None:
    from bass.validation import comparator_policy
    from htt.core import bounds
    import mio.formalism as formalism

    active_names = {
        "B_accel",
        "B_sigma_corrected",
        "Sig2_max_MES",
        "A2_max_MES",
        "filling_fraction",
        "sector_filling",
    }
    assert active_names.isdisjoint(vars(bounds))
    assert {"filling_fraction", "legacy_projection_ratio"}.isdisjoint(
        vars(comparator_policy)
    )
    assert {
        "NormalizedScore",
        "CertifiedFillingFraction",
        "ExceedanceCurve",
        "IsotropyGap",
    }.isdisjoint(vars(formalism))

    for path in (
        "htt/htt/htt/core/bounds.py",
        "htt/htt/htt/core/evidence_models_R03a.py",
        "htt/bass/validation/comparator_policy.py",
        "htt/mio/formalism/__init__.py",
    ):
        assert active_names.isdisjoint(_defined_names(path))


def test_historical_xc_and_mes_helpers_require_explicit_legacy_import() -> None:
    from bass.validation.comparator_policy import (
        ComparatorPolicy,
        DepartureComponents,
    )
    from bass.validation.legacy_comparator_policy import legacy_projection_ratio
    from tsc_legacy import htt_core_bounds as legacy_bounds

    summary = SummaryDepartureState(
        sigma2=0.5,
        w2=0.2,
        omega_tilt=0.1,
        delta_omega_k=-0.05,
        normalization="historical fixture",
        source_state_id="PR-252-fixture",
    )
    assert summary.x_C == legacy_bounds.x_defect(0.5, 0.1, -0.05, 0.2)

    components = DepartureComponents(
        Sigstd_sq=0.5,
        Wstd_sq=0.2,
        Omega_tilt=0.1,
        Omega_k=-0.05,
        Omega_k_ref=0.0,
        policy=ComparatorPolicy.FLAT,
    )
    ratio, status = legacy_projection_ratio(components, 2.0)
    assert ratio == pytest.approx(summary.x_C / 2.0)
    assert status == "legacy_nonnegative_projection"
    assert legacy_bounds.LEGACY_REPRODUCTION_ONLY is True


def test_active_anchor_set_is_typed_and_withheld_values_stay_quarantined() -> None:
    anchors = registered_geodesic_mes_anchors(
        eps1=0.0,
        eps2=2.0e-5,
        eps3=3.0e-5,
        attribution="integration fixture",
        conditioning=AnchorConditioning.ENSEMBLE_CALIBRATED,
    )
    assert anchors["sigma"].status is AnchorStatus.VERIFIED
    assert anchors["omega"].status is AnchorStatus.VERIFIED
    assert anchors["acceleration"].status is AnchorStatus.NO_MES_ANCHOR
    assert anchors["acceleration"].value is None
    assert anchors["anisotropic_curvature"].status is AnchorStatus.NO_MES_ANCHOR
    assert anchors["anisotropic_curvature"].value is None

    quarantined = quarantined_shear_anchors(
        eps1=1.0e-3,
        eps2=2.0e-5,
        eps3=3.0e-5,
        attribution="integration fixture",
        conditioning=AnchorConditioning.ENSEMBLE_CALIBRATED,
    )
    assert quarantined["frame_corrected"].status is AnchorStatus.WITHHELD
    assert "2.69 eps1" in quarantined["frame_corrected"].withheld_reason
    assert quarantined["s2a_catwise"].status is AnchorStatus.LEGACY_REPRODUCTION
    assert quarantined["s2a_catwise"].value == 9.25e-6


def test_result_card_keeps_output_spaces_disjoint_and_diagnostic_only() -> None:
    from mio.reports import StatisticalFoundationResultCard

    state = _state()
    identified = IdentifiedDepartureSet(
        coordinate_names=("Sigma2",),
        vertices=((0.0,), (0.2,)),
        recession_directions=(),
        null_kinds=(NullKind.NONE,),
        assumptions=("registered response fixture",),
        status=IdentificationStatus.PARTIALLY_IDENTIFIED,
    )
    anchor = registered_geodesic_mes_anchors(
        eps1=0.0,
        eps2=2.0e-5,
        eps3=3.0e-5,
        attribution="integration fixture",
        conditioning=AnchorConditioning.ENSEMBLE_CALIBRATED,
    )["sigma"]
    stress = evaluate_sector_stress(
        sector="Sigma2",
        numerator=ScalarRange(0.0, 0.2),
        numerator_channel_key=anchor.channel_key,
        anchor=anchor,
    )
    stress_report = build_anchor_stress_report(
        stresses=(stress,),
        conditioning=AnchorConditioning.ENSEMBLE_CALIBRATED,
    )
    legacy = LegacyProjectionReport(
        x_C=DiagnosticScalarReport(
            name="x_C",
            value_range=ScalarRange(-0.1, 0.1),
            status="HISTORICAL_VALUE_PRESERVED",
            null_calibration="not an evidence calibration",
        )
    )
    card = StatisticalFoundationResultCard(
        card_id="PR-252-integration",
        departure_state=state,
        identified_set=identified,
        anchor_stress=stress_report,
        legacy_projection=legacy,
        morphology_reference={
            "artifact_id": "obsstat.fixture",
            "owner": "OBSSTAT",
            "status": "diagnostic_only",
        },
    )
    payload = card.as_payload()
    assert payload["owner"] == "MIO"
    assert payload["status"] == "diagnostic_only"
    assert payload["automatic_conversion"] is False
    assert set(payload["output_spaces"]) == {
        "departure_state",
        "identified_set",
        "anchor_stress",
        "legacy_projection",
        "nonlinearity",
        "morphology_reference",
    }
    assert payload["output_spaces"]["legacy_projection"]["classification"] == (
        BC1_LEGACY_PROJECTION
    )
    assert payload["output_spaces"]["legacy_projection"][
        "representation_policy"
    ] == BC2_NO_REPRESENTATION_PROMOTION
    json.dumps(payload, allow_nan=False)


def test_result_card_rejects_anchor_report_subclass_claim_lane_override() -> None:
    from mio.reports import StatisticalFoundationResultCard

    anchor = registered_geodesic_mes_anchors(
        eps1=0.0,
        eps2=2.0e-5,
        eps3=3.0e-5,
        attribution="subclass-boundary fixture",
        conditioning=AnchorConditioning.ENSEMBLE_CALIBRATED,
    )["sigma"]
    stress = evaluate_sector_stress(
        sector="Sigma2",
        numerator=ScalarRange(0.0, 0.2),
        numerator_channel_key=anchor.channel_key,
        anchor=anchor,
    )
    legitimate = build_anchor_stress_report(
        stresses=(stress,),
        conditioning=AnchorConditioning.ENSEMBLE_CALIBRATED,
    )

    class ForgedAggregate(AnchorStressReport):
        def __init__(self, source: AnchorStressReport) -> None:
            object.__setattr__(self, "stresses", source.stresses)
            object.__setattr__(self, "conditioning", source.conditioning)
            object.__setattr__(self, "allowed_use", source.allowed_use)
            object.__setattr__(self, "forbidden_use", source.forbidden_use)

        def __getattribute__(self, name: str):
            if name == "allowed_use":
                return ("evidence",)
            return super().__getattribute__(name)

    assert type(
        ForgedAggregate.build(
            stresses=(stress,),
            conditioning=AnchorConditioning.ENSEMBLE_CALIBRATED,
        )
    ) is AnchorStressReport
    with pytest.raises(TypeError, match="exact AnchorStressReport"):
        StatisticalFoundationResultCard(
            card_id="forged-anchor-report",
            anchor_stress=ForgedAggregate(legitimate),
        )


@pytest.mark.parametrize("use_subclass", (False, True))
def test_legacy_projection_rejects_forged_nested_scalar_reports(
    use_subclass: bool,
) -> None:
    from mio.reports import StatisticalFoundationResultCard

    legitimate_scalar = DiagnosticScalarReport(
        name="x_C",
        value_range=ScalarRange(-0.1, 0.1),
        status="HISTORICAL_VALUE_PRESERVED",
        null_calibration="not an evidence calibration",
    )

    class ForgedScalar(DiagnosticScalarReport):
        pass

    forged_type = ForgedScalar if use_subclass else DiagnosticScalarReport
    forged_scalar = object.__new__(forged_type)
    for name, value in vars(legitimate_scalar).items():
        object.__setattr__(forged_scalar, name, value)
    object.__setattr__(forged_scalar, "status", "")
    object.__setattr__(forged_scalar, "null_calibration", "")
    object.__setattr__(
        forged_scalar,
        "bin_metadata",
        (("duplicate", "one"), ("duplicate", "two")),
    )

    with pytest.raises(
        StatisticalFoundationError,
        match="x_C must be|status must be a non-empty string",
    ):
        LegacyProjectionReport(x_C=forged_scalar)

    legitimate_legacy = LegacyProjectionReport(x_C=legitimate_scalar)
    forged_legacy = object.__new__(LegacyProjectionReport)
    for name, value in vars(legitimate_legacy).items():
        object.__setattr__(forged_legacy, name, value)
    object.__setattr__(forged_legacy, "x_C", forged_scalar)
    with pytest.raises(
        ValueError,
        match="legacy_projection does not satisfy its constructor invariants",
    ):
        StatisticalFoundationResultCard(
            card_id=f"forged-legacy-scalar-{use_subclass}",
            legacy_projection=forged_legacy,
        )


def test_legacy_projection_rejects_forged_nested_scalar_range() -> None:
    forged_range = object.__new__(ScalarRange)
    object.__setattr__(forged_range, "lower", 2.0)
    object.__setattr__(forged_range, "upper", 1.0)
    forged_scalar = object.__new__(DiagnosticScalarReport)
    for name, value in {
        "name": "x_C",
        "value_range": forged_range,
        "status": "HISTORICAL_VALUE_PRESERVED",
        "null_calibration": "not an evidence calibration",
        "bin_metadata": (),
    }.items():
        object.__setattr__(forged_scalar, name, value)
    with pytest.raises(
        StatisticalFoundationError,
        match="ScalarRange requires ordered",
    ):
        LegacyProjectionReport(x_C=forged_scalar)


def test_sector_stress_rejects_duck_typed_numerators_anchors_and_channels() -> None:
    anchor = registered_geodesic_mes_anchors(
        eps1=0.0,
        eps2=2.0e-5,
        eps3=3.0e-5,
        attribution="type-boundary fixture",
        conditioning=AnchorConditioning.ENSEMBLE_CALIBRATED,
    )["sigma"]
    with pytest.raises(
        StatisticalFoundationError,
        match="numerator must be a ScalarRange",
    ):
        evaluate_sector_stress(
            sector="Sigma2",
            numerator=types.SimpleNamespace(lower=1.0, upper=3.0),
            numerator_channel_key=anchor.channel_key,
            anchor=anchor,
        )
    fake_anchor = types.SimpleNamespace(
        normalization_allowed=True,
        target_sector="Sigma2",
        channel_key=anchor.channel_key,
        anchor_id="FAKE",
        conditioning=AnchorConditioning.ENSEMBLE_CALIBRATED,
        value=anchor.value,
    )
    with pytest.raises(
        StatisticalFoundationError,
        match="anchor must be a MESAnchorSpec",
    ):
        evaluate_sector_stress(
            sector="Sigma2",
            numerator=ScalarRange(1.0, 3.0),
            numerator_channel_key=anchor.channel_key,
            anchor=fake_anchor,
        )
    for malformed in ("not-a-channel", ("valid", 3), ()):
        with pytest.raises(
            StatisticalFoundationError,
            match="numerator_channel_key",
        ):
            evaluate_sector_stress(
                sector="Sigma2",
                numerator=ScalarRange(1.0, 3.0),
                numerator_channel_key=malformed,
                anchor=anchor,
            )


def test_chapter7_scenario_table_has_detachable_claim_metadata() -> None:
    chapter = (
        REPO_ROOT / "docs/manuscript/ch07_results.tex"
    ).read_text(encoding="utf-8")
    label_index = chapter.index(r"\label{tab:scenario-dual}")
    caption_start = chapter.rfind(r"\caption{", 0, label_index)
    caption = chapter[caption_start:label_index]
    for required in (
        "Owner: HTT",
        "Claim tier:",
        "diagnostic-only",
        r"BC1\_LEGACY\_PROJECTION",
        r"BC2\_NO\_REPRESENTATION\_PROMOTION",
        "historical external/proxy",
        "current mask/random, covariance, null, PPC",
        "Allowed use:",
        "Forbidden use:",
        "Bianchi family identification",
    ):
        assert required in caption


def test_result_card_claim_policy_and_morphology_status_are_not_caller_controlled() -> None:
    from mio.reports import StatisticalFoundationResultCard

    with pytest.raises(TypeError, match="allowed_use"):
        StatisticalFoundationResultCard(
            card_id="claim-policy-mutation",
            departure_state=_state(),
            allowed_use=("Bianchi family identification",),
        )
    with pytest.raises(ValueError, match="status must remain diagnostic_only"):
        StatisticalFoundationResultCard(
            card_id="morphology-status-mutation",
            departure_state=_state(),
            morphology_reference={
                "artifact_id": "obsstat.fixture",
                "owner": "OBSSTAT",
                "status": "native Bianchi family identified",
            },
        )
    card = StatisticalFoundationResultCard(
        card_id="morphology-post-init-mutation",
        departure_state=_state(),
        morphology_reference={
            "artifact_id": "obsstat.fixture",
            "owner": "OBSSTAT",
            "status": "diagnostic_only",
        },
    )
    with pytest.raises(TypeError):
        card.morphology_reference["status"] = (  # type: ignore[index]
            "native Bianchi family identified"
        )
    assert card.as_payload()["output_spaces"]["morphology_reference"][
        "status"
    ] == "diagnostic_only"


def test_active_htt_to_mio_contract_carries_no_evidence_fields(tmp_path: Path) -> None:
    from htt.integration.to_mio import build_posterior_bundle

    exported_fields = {item.name for item in fields(MioCrossCheckExport)}
    assert "ln_B_total" not in exported_fields
    assert "model_evidences" not in exported_fields
    assert "evidence_included" in exported_fields
    with pytest.raises(RuntimeError, match="legacy reproduction only"):
        build_posterior_bundle(tmp_path / "missing.json")


@pytest.mark.parametrize(
    ("path", "bad_value"),
    [
        (("legacy_projection_summary", "values", "x_C", "median"), True),
        (("legacy_projection_summary", "values", "Q", "median"), True),
        (("legacy_projection_summary", "values", "Pi", "median"), True),
        (("legacy_projection_summary", "values", "F", "median"), True),
        (("evidence_summary", "lnB_total"), True),
        (("evidence_summary", "model_evidences", "FLRW_tilt"), True),
    ],
)
def test_v2_directional_loader_rejects_boolean_scalars(
    path: tuple[str, ...],
    bad_value: object,
) -> None:
    from htt.integration.posterior_artifact import (
        load_directional_posterior_artifact,
    )

    payload = _directional_payload()
    target = payload
    for key in path[:-1]:
        target = target[key]  # type: ignore[index,assignment]
    target[path[-1]] = bad_value  # type: ignore[index]
    with pytest.raises(ValueError, match="real number, not boolean"):
        load_directional_posterior_artifact(payload)


def test_v2_directional_loader_rejects_empty_ids_and_claim_policy_drift() -> None:
    from htt.integration.posterior_artifact import (
        load_directional_posterior_artifact,
    )

    empty_id = _directional_payload()
    empty_id["evidence_summary"]["model_evidences"] = {"": 0.0}  # type: ignore[index]
    with pytest.raises(ValueError, match="non-empty strings"):
        load_directional_posterior_artifact(empty_id)

    for key, replacement in (
        ("allowed_use", ["evidence"]),
        ("forbidden_use", []),
    ):
        drifted = _directional_payload()
        drifted["legacy_projection_summary"][key] = replacement  # type: ignore[index]
        with pytest.raises(ValueError, match=f"{key} policy drift"):
            load_directional_posterior_artifact(drifted)


def test_v2_directional_evidences_are_immutable_after_validation() -> None:
    from htt.integration.posterior_artifact import (
        load_directional_posterior_artifact,
    )

    artifact = load_directional_posterior_artifact(_directional_payload())
    with pytest.raises(TypeError):
        artifact.model_evidences["FLRW_tilt"] = float("nan")  # type: ignore[index]
    assert artifact.model_evidences["FLRW_tilt"] == 5.0


def test_directional_intervals_are_defensively_normalized() -> None:
    from htt.integration.posterior_artifact import (
        load_directional_posterior_artifact,
    )

    artifact = load_directional_posterior_artifact(_directional_payload())
    source_interval = [0.1, 0.3]
    replaced = replace(artifact, x_hpd68=source_interval)
    source_interval[0] = float("nan")
    assert replaced.x_hpd68 == (0.1, 0.3)
    json.dumps(
        {
            "x_hpd68": replaced.x_hpd68,
            "model_evidences": dict(replaced.model_evidences),
        },
        allow_nan=False,
    )
    with pytest.raises(ValueError, match="exactly two numeric values"):
        replace(artifact, x_hpd68=3)
    with pytest.raises(ValueError, match="model_evidences must be a mapping"):
        replace(artifact, model_evidences=[("FLRW_tilt", 5.0)])


@pytest.mark.parametrize("bad_ref", ["", True, 3])
def test_directional_optional_refs_reject_invalid_direct_inputs(
    bad_ref: object,
) -> None:
    from htt.integration.posterior_artifact import (
        load_directional_posterior_artifact,
    )

    artifact = load_directional_posterior_artifact(_directional_payload())
    with pytest.raises(ValueError, match="must be a non-empty string"):
        replace(artifact, posterior_predictive_ref=bad_ref)
    with pytest.raises(ValueError, match="must be a non-empty string"):
        replace(artifact, loocv_ref=bad_ref)


@pytest.mark.parametrize(
    ("is_cross_check_only", "evidence_included"),
    [(1, False), (True, 0)],
)
def test_mio_cross_check_firewall_requires_exact_booleans(
    is_cross_check_only: object,
    evidence_included: object,
) -> None:
    legacy = LegacyProjectionReport(
        x_C=DiagnosticScalarReport(
            name="x_C",
            value_range=ScalarRange(-0.1, 0.1),
            status="HISTORICAL_VALUE_PRESERVED",
            null_calibration="not an evidence calibration",
        )
    )
    with pytest.raises(TypeError, match="exact booleans"):
        MioCrossCheckExport(
            model="FLRW_tilt",
            legacy_projection=legacy,
            manifest=_diagnostic_manifest(),
            source_artifact_ref="artifact.json",
            posterior_ref="artifact.json#posterior",
            is_cross_check_only=is_cross_check_only,  # type: ignore[arg-type]
            evidence_included=evidence_included,  # type: ignore[arg-type]
        )


@pytest.mark.parametrize(
    ("field_name", "bad_value"),
    [
        ("sigma_sq", True),
        ("sigma_sq", -1.0),
        ("omega_sq", -1.0),
        ("H_theta", 0.0),
        ("H_theta", float("nan")),
        ("beta", float("inf")),
        ("w", -1.01),
        ("Omega_matter", -0.1),
        ("Omega_k", float("nan")),
        ("Omega_k_ref", True),
    ],
)
def test_active_comparator_rejects_nonphysical_scalar_inputs(
    field_name: str,
    bad_value: object,
) -> None:
    from bass.background.bianchi_types import get_type
    from bass.validation.comparator_policy import (
        ComparatorPolicy,
        compute_departure_components,
    )

    values: dict[str, object] = {
        "sigma_sq": 1.0e-6,
        "omega_sq": 0.0,
        "H_theta": 1.0,
        "beta": 1.0e-3,
        "w": 0.0,
        "Omega_matter": 0.3,
        "Omega_k": 0.0,
        "Omega_k_ref": None,
    }
    values[field_name] = bad_value
    with pytest.raises((TypeError, ValueError)):
        compute_departure_components(
            get_type("I"),
            policy=ComparatorPolicy.FLAT,
            **values,  # type: ignore[arg-type]
        )


def test_departure_component_constructor_rejects_invalid_pseudo_state() -> None:
    from bass.validation.comparator_policy import (
        ComparatorPolicy,
        DepartureComponents,
    )

    with pytest.raises(ValueError, match="Wstd_sq must be non-negative"):
        DepartureComponents(
            Sigstd_sq=1.0,
            Wstd_sq=-1.0,
            Omega_tilt=0.0,
            Omega_k=0.0,
            Omega_k_ref=0.0,
            policy=ComparatorPolicy.FLAT,
        )


@pytest.mark.parametrize(
    ("policy", "omega_k_ref", "message"),
    [
        (ComparatorPolicy.FLAT, None, "requires Omega_k_ref"),
        (ComparatorPolicy.FLAT, 0.1, "requires Omega_k_ref=0"),
        (ComparatorPolicy.MATCHED, None, "requires Omega_k_ref"),
        (ComparatorPolicy.NULL, 0.0, "requires Omega_k_ref=None"),
    ],
)
def test_departure_component_constructor_enforces_policy_reference_identity(
    policy: ComparatorPolicy,
    omega_k_ref: float | None,
    message: str,
) -> None:
    from bass.validation.comparator_policy import DepartureComponents

    with pytest.raises(ValueError, match=message):
        DepartureComponents(
            Sigstd_sq=1.0,
            Wstd_sq=0.0,
            Omega_tilt=0.0,
            Omega_k=0.0,
            Omega_k_ref=omega_k_ref,
            policy=policy,
        )


@pytest.mark.parametrize(
    ("policy", "omega_k_ref", "message"),
    [
        (ComparatorPolicy.FLAT, 0.1, "requires Omega_k_ref=0"),
        (ComparatorPolicy.NULL, 0.0, "requires Omega_k_ref=None"),
    ],
)
def test_departure_component_factory_rejects_policy_reference_contradictions(
    policy: ComparatorPolicy,
    omega_k_ref: float,
    message: str,
) -> None:
    from bass.background.bianchi_types import get_type
    from bass.validation.comparator_policy import compute_departure_components

    with pytest.raises(ValueError, match=message):
        compute_departure_components(
            get_type("I"),
            sigma_sq=0.0,
            omega_sq=0.0,
            H_theta=1.0,
            Omega_k=0.0,
            Omega_k_ref=omega_k_ref,
            policy=policy,
        )


def test_departure_component_constructor_rejects_direct_projection_overflow() -> None:
    from bass.validation.comparator_policy import DepartureComponents

    with pytest.raises(ValueError, match="x_C_direct must be finite"):
        DepartureComponents(
            Sigstd_sq=1.0e308,
            Wstd_sq=0.0,
            Omega_tilt=1.0e308,
            Omega_k=1.0e308,
            Omega_k_ref=0.0,
            policy=ComparatorPolicy.MATCHED,
        )


def test_departure_component_constructor_rejects_anisotropic_curvature_overflow() -> None:
    from bass.validation.comparator_policy import DepartureComponents

    with pytest.raises(ValueError, match="Omega_k_aniso must be finite"):
        DepartureComponents(
            Sigstd_sq=0.0,
            Wstd_sq=0.0,
            Omega_tilt=0.0,
            Omega_k=1.0e308,
            Omega_k_ref=-1.0e308,
            policy=ComparatorPolicy.MATCHED,
        )


def test_pr151_remains_background_only_and_dag_mirrors_are_exact() -> None:
    status = _yaml("docs/codex_handoff/pr_status.yaml")
    assert status["background_in_progress"] == ["PR-151"]
    assert status["background_execution_contracts"]["PR-151"] == {
        "kind": "acquisition",
        "allowed_phase": "acquire",
        "partial_scientific_use": "forbidden",
    }
    assert (
        REPO_ROOT / "docs/codex_handoff/pr_status.yaml"
    ).read_bytes() == (
        REPO_ROOT / "machine_readable/pr_status.yaml"
    ).read_bytes()
    assert (
        REPO_ROOT / "docs/codex_handoff/pr_backlog.yaml"
    ).read_bytes() == (
        REPO_ROOT / "machine_readable/pr_backlog.yaml"
    ).read_bytes()


def test_manuscript_keeps_curvature_condition_and_shear_anchor_scope() -> None:
    chapter3 = (REPO_ROOT / "docs/manuscript/ch03_framework.tex").read_text(
        encoding="utf-8"
    )
    chapter7 = (REPO_ROOT / "docs/manuscript/ch07_results.tex").read_text(
        encoding="utf-8"
    )

    assert "Irrotationality alone does not fix the sign" in chapter3
    assert "$\\Wstd = 0$ and $\\Okaniso\\geq0$" in chapter3
    assert "is the MES \\emph{linear} algebraic bound" not in chapter7
    assert "linear geodesic MES \\emph{shear-channel} bound" in chapter7
    assert "does not make $\\xmax$ a joint" in chapter7


def test_detachable_evidence_captions_carry_complete_claim_lanes() -> None:
    chapter7 = (REPO_ROOT / "docs/manuscript/ch07_results.tex").read_text(
        encoding="utf-8"
    )
    labels = (
        "tab:fb7_lnB_11types",
        "tab:class-collapsed",
        "tab:evidence-grand",
        "tab:decomposition-results",
    )
    required = (
        "Owner: HTT.",
        "Claim tier: diagnostic-only.",
        "Artifact mode: conditioned",
        r"BC1\_LEGACY\_PROJECTION",
        r"BC2\_NO\_REPRESENTATION\_PROMOTION",
        "Transfer source: historical external/proxy",
        "Null/covariance status: historical fixture only",
        "Allowed use: historical reproduction and method comparison.",
        "Forbidden use: current",
        "native-solver or morphology ranking",
        "Bianchi family identification.",
    )
    for label in labels:
        before_label = chapter7.split(f"\\label{{{label}}}", 1)[0]
        caption = " ".join(
            before_label.rsplit("\\caption{", 1)[1].split()
        )
        for phrase in required:
            assert phrase in caption, (label, phrase)


def test_foundation_dependency_overlay_has_an_exact_typed_projection() -> None:
    from scripts.codex_harness.progress_report import _dependency_contracts
    from scripts.codex_harness.validate_pr_dag import validate_backlog

    backlog = _yaml("docs/codex_handoff/pr_backlog.yaml")
    info = validate_backlog(backlog)
    for pr_id in ("PR-155", "PR-156", "PR-157"):
        contracts = _dependency_contracts(info, pr_id)
        upstreams = [row["upstream_id"] for row in contracts]
        assert tuple(upstreams) == info.prereqs[pr_id]
        assert all(row["mode"] == "requires_success" for row in contracts[-1:])


def test_mes_registry_accepts_only_the_migrated_active_inventory() -> None:
    report = validate_mes_successor_registry(REPO_ROOT)
    assert report.release_allowed is True
    assert report.findings == ()

    inventory = _yaml(
        "docs/research_program/long_horizon_rescue/"
        "pr122_active_mes_consumers.yaml"
    )
    declarations = tuple(
        MesConsumerDeclaration(
            consumer_id=row["consumer_id"],
            source=SourceHashBinding(
                path=row["path"],
                availability=SourceAvailability.AVAILABLE,
                sha256=row["sha256"],
            ),
        )
        for row in inventory["active_consumers"]
    )
    scan = scan_declared_mes_consumers(REPO_ROOT, declarations)
    assert scan.release_allowed is True
    assert scan.consumers_scanned == 7
    assert scan.findings == ()
