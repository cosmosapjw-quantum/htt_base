"""VER2 TSC active-service skeleton tests."""
from __future__ import annotations

import ast
from dataclasses import fields
from pathlib import Path

import pytest

from common.contracts import ArtifactManifest, TscAdequacyOverlay, TscDomainReport
from tsc.adapters.bass_runtime import SourceAdequacySuggestion
from tsc.audit.no_overclaim import FORBIDDEN_PHRASE_REGISTRY
from tsc.contracts import (
    ALLOWED_COMBINED_LABELS,
    ALLOWED_SERVICE_LABELS,
    FORBIDDEN_COMBINED_LABELS,
    FORBIDDEN_TSC_FIELDS,
    TSC_NOT_APPLICABLE,
    serious_artifact_has_tsc_annotation,
    validate_tsc_service_labels,
)


ROOT = Path(__file__).resolve().parent
FORBIDDEN_IMPORT_PREFIXES = (
    "bass.runtime",
    "htt.htt.htt.core.evidence_models",
    "htt.htt.htt.core.evidence_models_R03a",
)
MODULES_TO_SCAN = (
    ROOT / "contracts.py",
    ROOT / "audit" / "no_overclaim.py",
    ROOT / "adapters" / "bass_runtime.py",
    ROOT / "adapters" / "htt_inference.py",
    ROOT / "adapters" / "mio_certificate.py",
    ROOT / "integration" / "active_service.py",
    ROOT / "reports" / "overlay_builder.py",
)


def _manifest() -> ArtifactManifest:
    return ArtifactManifest(
        artifact_id="tsc.overlay",
        artifact_path="artifacts/tsc/overlay.json",
        owner="TSC",
        implementation_scope="tsc",
        claim_tier="conditional",
        production_status="production_candidate",
        created_by="test-suite",
        git_commit="abc123",
        config_hash="cfg",
        input_hashes=["a"],
        code_version="0.0-test",
        schema_version="ver2-v1",
    )


def _imports(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    found: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                found.add(alias.name)
        elif isinstance(node, ast.ImportFrom) and node.module:
            found.add(node.module)
    return found


def test_tsc_contracts_alias_common_schema():
    from tsc.contracts import TscAdequacyOverlay as LocalOverlay
    from tsc.contracts import TscDomainReport as LocalDomainReport

    assert LocalOverlay is TscAdequacyOverlay
    assert LocalDomainReport is TscDomainReport


def test_forbidden_runtime_and_truth_fields_absent_from_tsc_outputs():
    for tp in (SourceAdequacySuggestion,):
        names = {field.name for field in fields(tp)}
        assert not (names & FORBIDDEN_TSC_FIELDS)


def test_allowed_and_forbidden_label_vocabulary_present():
    assert "source_adequate__propagation_pending" in ALLOWED_COMBINED_LABELS
    assert "source_bridge_bound_pending" in ALLOWED_SERVICE_LABELS
    assert "tsc_validated_full_polarization" in FORBIDDEN_COMBINED_LABELS
    assert TSC_NOT_APPLICABLE == "tsc_not_applicable"
    assert "full_polarization" in FORBIDDEN_PHRASE_REGISTRY


def test_validate_tsc_service_labels_rejects_unknown_and_forbidden_labels():
    assert validate_tsc_service_labels(("stable_no_upgrade", "stable_no_upgrade")) == (
        "stable_no_upgrade",
    )
    with pytest.raises(ValueError, match="unknown TSC service labels"):
        validate_tsc_service_labels(("not_a_real_label",))
    with pytest.raises(ValueError, match="forbidden TSC service labels"):
        validate_tsc_service_labels(("tsc_validated_full_polarization",))


def test_serious_artifact_requires_overlay_or_explicit_na():
    assert serious_artifact_has_tsc_annotation(has_overlay=True, metadata={})
    assert serious_artifact_has_tsc_annotation(
        has_overlay=False, metadata={TSC_NOT_APPLICABLE: True}
    )
    assert not serious_artifact_has_tsc_annotation(has_overlay=False, metadata={})


def test_new_tsc_service_modules_do_not_import_runtime_or_evidence_writers():
    for module in MODULES_TO_SCAN:
        imports = _imports(module)
        offenders = {
            name
            for name in imports
            if any(name == prefix or name.startswith(prefix + ".") for prefix in FORBIDDEN_IMPORT_PREFIXES)
        }
        assert not offenders, f"{module.name} imports forbidden authority paths: {sorted(offenders)}"


def test_tsc_overlay_manifest_owner_is_tsc():
    man = _manifest()
    overlay = TscAdequacyOverlay(
        domain_report=TscDomainReport(
            chart="one_field",
            theta_min=1.0,
            eta_max=None,
            be_eta_nonpositive=None,
            weight_simplex_ok=True,
            jacobian_sigma_min=None,
            domain_margin=1.0,
            status="valid_one_field",
            blocking_reasons=tuple(),
            manifest=man,
        ),
        residual_report=pytest.importorskip("common.contracts").TscResidualReport(
            chart="one_field",
            laguerre_n_ge_2_norm=0.0,
            ambient_defect_rate=None,
            projected_defect_estimate=None,
            onefield_residual=0.0,
            twofield_residual=None,
            eta_tangent_fraction=None,
            trace_residual_q_tr=None,
            spin2_residual=None,
            high_residual=None,
            residual_origin="unknown",
            labels=tuple(),
            manifest=man,
        ),
        source_bridge_report=None,
        channel_budgets=tuple(),
        upgrade_recommendation=pytest.importorskip("common.contracts").TscUpgradeRecommendation(
            current_chart="one_field",
            recommended_chart="one_field",
            reason="stable_no_upgrade",
            severity="info",
            dwell_time_required=None,
            hysteresis_state="stable",
            labels=tuple(),
            manifest=man,
        ),
        no_overclaim_flags={code: True for code in FORBIDDEN_PHRASE_REGISTRY},
        quarantine_reasons=tuple(),
        public_caveat_snippet="diagnostic-only",
        manifest=man,
    )
    assert overlay.manifest.owner == "TSC"
