"""PR-252 cross-package migration and claim-boundary integration checks."""
from __future__ import annotations

import ast
from dataclasses import fields
import json
from pathlib import Path

import pytest
import yaml

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
    SummaryDepartureState,
    evaluate_sector_stress,
    quarantined_shear_anchors,
    registered_geodesic_mes_anchors,
)
from workspace.contracts.htt_to_mio import MioCrossCheckExport


REPO_ROOT = Path(__file__).resolve().parents[2]


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
    stress_report = AnchorStressReport(
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


def test_active_htt_to_mio_contract_carries_no_evidence_fields(tmp_path: Path) -> None:
    from htt.integration.to_mio import build_posterior_bundle

    exported_fields = {item.name for item in fields(MioCrossCheckExport)}
    assert "ln_B_total" not in exported_fields
    assert "model_evidences" not in exported_fields
    assert "evidence_included" in exported_fields
    with pytest.raises(RuntimeError, match="legacy reproduction only"):
        build_posterior_bundle(tmp_path / "missing.json")


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
