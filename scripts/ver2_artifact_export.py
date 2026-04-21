#!/usr/bin/env python3
"""VER2 live artifact-to-figure/table exporter.

This script closes the IM-09D figure/export path on top of manifest-backed
artifacts produced from the current VER2 code surface. It emits:

- shared `status_snapshot.json` and `claim_ledger.json`,
- result-pack JSON / Markdown / LaTeX exports,
- gallery topic maps,
- generated figure assets with caption + canonical manifest sidecars,
- manuscript-facing generated TeX snippets,
- a full paper-figure manifest audit.

Usage:
    venv/bin/python scripts/ver2_artifact_export.py
    venv/bin/python scripts/ver2_artifact_export.py --check
"""
from __future__ import annotations

import argparse
from collections import Counter
from dataclasses import asdict, dataclass, fields, replace
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
from textwrap import dedent
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


REPO_ROOT = Path(__file__).resolve().parents[1]
HTT_ROOT = REPO_ROOT / "htt"
COMMON_ROOT = HTT_ROOT / "src"
for root in (HTT_ROOT, COMMON_ROOT):
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))

from bass.observational import (  # noqa: E402
    build_atlas_entry_lite,
    build_descriptive_departure_report,
    build_full_cov_mes_report,
    build_observable_vector_from_solver_output,
)
from bass.background.bianchi_types import get_type  # noqa: E402
from bass.background.einstein_bianchi import BianchiCosmology  # noqa: E402
from bass.forward.ver2_solver_output import BassReleaseMetadata  # noqa: E402
from bass.hierarchy.integrator import IntegratorConfig  # noqa: E402
from bass.runtime import (  # noqa: E402
    CheckpointPolicy,
    ConstraintProjectionPolicy,
    CouplingMode,
    FeatureStatus,
    IntegratorFamily,
    RuntimeControlBlock,
    SolverFeatureFlags,
    SolverTier,
    execute_tier_a_validation_solver,
    execute_tier_b_lowell_solver,
)
from bass.spectrum import CutoffCampaignSpec  # noqa: E402
from bass.species.registry import SpeciesBackgroundRegistry  # noqa: E402
from common.claim_ledger import claim_entry_to_dict  # noqa: E402
from common.contracts import (  # noqa: E402
    ArtifactManifest,
    ClaimLedgerEntry,
    DiscriminationMatrix,
    SkySupport,
    SolverCoreOutput,
    StatusSnapshotEntry,
)
from common.departure_contracts import BudgetSpec, DepartureBundle  # noqa: E402
from common.status_snapshot import snapshot_entry_to_dict  # noqa: E402
from htt.infer.local_global_discrimination import (  # noqa: E402
    build_discrimination_matrix,
)
from mio.diagnostics import (  # noqa: E402
    build_predictive_residual_atlas_from_shared_schema,
    to_predictive_residual_mio_certificate,
)
from mio.interface.mio_certificate import certificate_to_payload  # noqa: E402
from tsc.admissibility.domain import build_domain_report  # noqa: E402
from tsc.budget.source_to_channel import build_channel_budgets  # noqa: E402
from tsc.control.upgrade_advisor import recommend_chart_transition  # noqa: E402
from tsc.reports import (  # noqa: E402
    attach_overlay_to_departure_report,
    attach_overlay_to_mes_report,
    build_tsc_overlay,
    overlay_publication_blockers,
    overlay_to_json_dict,
)
from tsc.residuals.blockwise import ambient_vs_projected_defect_report  # noqa: E402
from tsc.source.thomson_bridge import build_source_bridge_report  # noqa: E402
from workspace.contracts import HttForwardOutput  # noqa: E402
from workspace.contracts.validation_registry import (  # noqa: E402
    REQUIRED_VALIDATION_CATEGORIES,
    validation_registry_payload,
)


VER2_GEN = REPO_ROOT / "docs" / "ver2_upgrade" / "generated"
MANUSCRIPT_GEN = REPO_ROOT / "docs" / "manuscript" / "generated"
FIGURE_ROOT = REPO_ROOT / "figures" / "paper"
FIGURE_GEN = FIGURE_ROOT / "ver2_generated"
ARTIFACT_GEN = VER2_GEN / "artifacts"
STATUS_JSON = VER2_GEN / "status_snapshot.json"
CLAIM_JSON = VER2_GEN / "claim_ledger.json"
TOPIC_MAP_JSON = VER2_GEN / "FIGURE_GALLERY_TOPIC_MAP.json"
TOPIC_MAP_MD = VER2_GEN / "FIGURE_GALLERY_TOPIC_MAP.md"
FIGURE_GEN_INDEX = FIGURE_GEN / "INDEX.md"

CLAIM_TIER_ORDER = {
    "blocked": 0,
    "exploratory": 1,
    "conditional": 2,
    "validated": 3,
}
CLAIM_TIER_LABEL = {
    "blocked": "Blocked",
    "exploratory": "Exploratory",
    "conditional": "Conditional",
    "validated": "Validated",
}
PRODUCTION_STATUS_ORDER = {
    "diagnostic_only": 0,
    "blocked_missing_covariance": 0,
    "blocked_missing_null_mocks": 0,
    "blocked_missing_atlas": 0,
    "blocked_owner_violation": 0,
    "production_candidate": 1,
    "production_validated": 2,
}
PACK_FILE_STEMS = {
    "A": "result_pack_A_scalar_to_morphology",
    "B": "result_pack_B_local_global",
    "C": "result_pack_C_departure_cards",
    "D": "result_pack_D_mio_certificates",
    "E": "result_pack_E_equivalence_classes",
}

MANUSCRIPT_ROLE_BY_PACK = {
    "A": "main-text conditional morphology proxy; not a directional BiPoSH or posterior claim",
    "B": "appendix-only diagnostic on local-vs-global degeneracy; not posterior odds",
    "C": "appendix-only descriptive departure card; not certified filling or geometry validation",
    "D": "main-text conditional residual-atlas check; not truth certification or posterior evidence",
    "E": "appendix-only validation coverage matrix; warn campaigns remain no-claim gates",
}


@dataclass(frozen=True)
class ArtifactRecord:
    key: str
    title: str
    topic: str
    pack_id: str
    manifest: ArtifactManifest
    payload: dict[str, object]
    summary: str
    allowed_claims: tuple[str, ...]
    forbidden_claims: tuple[str, ...]
    evidence_refs: tuple[str, ...]
    notes: tuple[str, ...] = ()


@dataclass(frozen=True)
class PackRecord:
    pack_id: str
    title: str
    topic: str
    figure_base: str
    artifacts: tuple[ArtifactRecord, ...]
    claim_tier: str
    production_status: str
    caveats: tuple[str, ...]
    summary_lines: tuple[str, ...]


def _resolve_git_commit() -> str:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=REPO_ROOT,
            check=True,
            capture_output=True,
            text=True,
            timeout=5,
        )
    except (OSError, subprocess.SubprocessError):
        return "unknown"
    return result.stdout.strip() or "unknown"


CURRENT_COMMIT = _resolve_git_commit()


def _field_names(contract: type[object]) -> list[str]:
    return [field.name for field in fields(contract)]


def _stable_hash(*parts: object) -> str:
    payload = json.dumps(parts, sort_keys=True, default=str, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


def _escape_tex(text: object) -> str:
    value = str(text)
    replacements = {
        "\\": r"\textbackslash{}",
        "&": r"\&",
        "%": r"\%",
        "$": r"\$",
        "#": r"\#",
        "_": r"\_",
        "{": r"\{",
        "}": r"\}",
        "~": r"\textasciitilde{}",
        "^": r"\textasciicircum{}",
    }
    for old, new in replacements.items():
        value = value.replace(old, new)
    return value


def _json_ready(value: object) -> object:
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, (np.floating,)):
        return float(value)
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, dict):
        return {str(key): _json_ready(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    return value


def _dump_json(path: Path, payload: object) -> str:
    text = json.dumps(_json_ready(payload), indent=2, sort_keys=True, default=str)
    return text + "\n"


def _min_claim_tier(tiers: tuple[str, ...]) -> str:
    return min(tiers, key=lambda item: CLAIM_TIER_ORDER[item])


def _derive_export_production_status(
    manifests: tuple[ArtifactManifest, ...],
    *,
    claim_tier: str,
) -> str:
    if claim_tier == "blocked":
        return "diagnostic_only"
    if any(manifest.production_status.startswith("blocked_") for manifest in manifests):
        return "diagnostic_only"
    if claim_tier == "exploratory":
        return "diagnostic_only"
    if all(manifest.production_status == "production_validated" for manifest in manifests):
        return "production_validated"
    if all(
        manifest.production_status in {"production_candidate", "production_validated"}
        for manifest in manifests
    ):
        return "production_candidate"
    return "diagnostic_only"


def _make_manifest(
    *,
    artifact_id: str,
    artifact_path: str,
    owner: str,
    implementation_scope: str,
    claim_tier: str,
    production_status: str,
    input_hashes: tuple[str, ...] = (),
    caveats: tuple[str, ...] = (),
    required_gates: tuple[str, ...] = (),
    passed_gates: tuple[str, ...] = (),
    failed_gates: tuple[str, ...] = (),
    statistics_definitions: dict[str, object] | None = None,
) -> ArtifactManifest:
    return ArtifactManifest(
        artifact_id=artifact_id,
        artifact_path=artifact_path,
        owner=owner,  # type: ignore[arg-type]
        implementation_scope=implementation_scope,  # type: ignore[arg-type]
        claim_tier=claim_tier,  # type: ignore[arg-type]
        production_status=production_status,  # type: ignore[arg-type]
        created_by="scripts.ver2_artifact_export.py",
        git_commit=CURRENT_COMMIT,
        config_hash=_stable_hash(
            artifact_id,
            artifact_path,
            owner,
            implementation_scope,
            claim_tier,
            production_status,
            input_hashes,
            caveats,
            required_gates,
            passed_gates,
            failed_gates,
            statistics_definitions or {},
        ),
        input_hashes=list(input_hashes),
        code_version="ver2-d1",
        schema_version="ver2-v9",
        caveats=list(dict.fromkeys(caveats)),
        required_gates=list(required_gates),
        passed_gates=list(passed_gates),
        failed_gates=list(failed_gates),
        statistics_definitions=dict(statistics_definitions or {}),
    )


def _artifact_path(name: str) -> str:
    return f"docs/ver2_upgrade/generated/artifacts/{name}.json"


def _figure_manifest_path(name: str) -> str:
    return f"figures/paper/ver2_generated/{name}.png"


def _sky_support() -> SkySupport:
    return SkySupport(
        selection_mode="mock_calibrated",
        sky_support_hash="sky-ver2-d1",
        mask_hash="mask-ver2-d1",
        mock_coverage_status="adequate",
        scan_volume_hash="scan-ver2-d1",
    )


def _feature_flags() -> SolverFeatureFlags:
    return SolverFeatureFlags(
        background_dynamics=FeatureStatus.APPROXIMATE,
        photon_transport=FeatureStatus.APPROXIMATE,
        thomson_collision=FeatureStatus.APPROXIMATE,
        visibility_history=FeatureStatus.APPROXIMATE,
        source_propagator=FeatureStatus.APPROXIMATE,
        checkpoint_restart=FeatureStatus.DISABLED,
    )


def _runtime_controls(tier: SolverTier) -> RuntimeControlBlock:
    return RuntimeControlBlock(
        tier=tier,
        integrator_family=IntegratorFamily.IMEX_SPLIT,
        coupling_mode=CouplingMode.BACKGROUND_THEN_RADIATION,
        multipole_cutoff=4,
        rtol=1.0e-6,
        atol=1.0e-9,
        checkpoint=CheckpointPolicy(enabled=False),
        constraint_projection=ConstraintProjectionPolicy(
            enabled=True,
            every_n_steps=4,
            status=FeatureStatus.APPROXIMATE,
        ),
        random_seed=42,
    )


def _release(run_label: str) -> BassReleaseMetadata:
    return BassReleaseMetadata(
        release_stage="research_candidate",
        run_label=run_label,
        config_hash=_stable_hash("ver2-d1", run_label),
        code_version="ver2-d1",
        schema_version="ver2-v9",
        git_commit=CURRENT_COMMIT,
        random_seed=42,
    )


def _integrator_config() -> IntegratorConfig:
    return IntegratorConfig(
        L_max=4,
        eta_initial_mpc=0.5,
        eta_final_mpc=1.0,
        n_output=12,
        rtol=1.0e-6,
        atol=1.0e-9,
        bianchi_cosmo=BianchiCosmology(
            structure=get_type("I"),
            beta=0.0,
        ),
        gamma_T_over_H_threshold=100.0,
        gamma_T_override=lambda eta: 500.0,
    )


def _solver_manifest(name: str) -> ArtifactManifest:
    return _make_manifest(
        artifact_id=f"bass.ver2.export.{name}",
        artifact_path=_artifact_path(f"bass_ver2_export_{name}"),
        owner="BASS",
        implementation_scope="canonical_BASS",
        claim_tier="conditional",
        production_status="production_candidate",
        input_hashes=("species:planck2018",),
        caveats=("observer_neutral_forward_output",),
        required_gates=("runtime", "propagator"),
        passed_gates=("runtime", "propagator"),
        statistics_definitions={"surface": "SolverCoreOutput", "bianchi_type": "I"},
    )


def _build_live_runtime_runs() -> tuple[object, object]:
    species = SpeciesBackgroundRegistry.from_planck2018()
    integrator_config = _integrator_config()
    k_grid_mpc = np.array([1.0e-4, 2.0e-4], dtype=np.float64)
    feature_flags = _feature_flags()
    tier_b_run = execute_tier_b_lowell_solver(
        manifest=_solver_manifest("solver_core_output_tier_b"),
        bianchi_type="I",
        species=species,
        integrator_config=integrator_config,
        runtime_controls=_runtime_controls(SolverTier.TIER_B_PSTF),
        feature_flags=feature_flags,
        release=_release("ver2-d1-tier-b"),
        k_grid_mpc=k_grid_mpc,
        cutoff_spec=CutoffCampaignSpec(
            cutoffs=(4, 6),
            closure_name="tier_b_tca",
            baseline_cutoff=4,
        ),
    )
    tier_a_run = execute_tier_a_validation_solver(
        manifest=_solver_manifest("solver_core_output_tier_a"),
        bianchi_type="I",
        species=species,
        integrator_config=integrator_config,
        runtime_controls=_runtime_controls(SolverTier.TIER_A_ANGULAR),
        feature_flags=feature_flags,
        release=_release("ver2-d1-tier-a"),
        k_grid_mpc=k_grid_mpc,
    )
    return tier_b_run, tier_a_run


def _observable_and_atlas(solver_output: SolverCoreOutput) -> tuple[object, object]:
    observable = build_observable_vector_from_solver_output(
        solver_output,
        sky_support=_sky_support(),
    )
    observable = replace(
        observable,
        manifest=replace(
            observable.manifest,
            artifact_path=_artifact_path("bass_ver2_export_observable_vector"),
            git_commit=CURRENT_COMMIT,
        ),
    )
    atlas = build_atlas_entry_lite(solver_output, observable)
    atlas = replace(
        atlas,
        manifest=replace(
            atlas.manifest,
            artifact_path=_artifact_path("bass_ver2_export_atlas_entry_lite"),
            git_commit=CURRENT_COMMIT,
        ),
    )
    return observable, atlas


def _axis_lb_from_vector(axis: np.ndarray) -> tuple[float, float]:
    vec = np.asarray(axis, dtype=np.float64)
    norm = max(float(np.linalg.norm(vec)), 1.0e-30)
    x, y, z = vec / norm
    l_deg = float(np.degrees(np.arctan2(y, x)) % 360.0)
    b_deg = float(np.degrees(np.arcsin(np.clip(z, -1.0, 1.0))))
    return (l_deg, b_deg)


def _forward_output_from_solver_output(
    *,
    artifact_id: str,
    model_name: str,
    solver_output: SolverCoreOutput,
    atlas_artifact_id: str,
    sigma_tensor: np.ndarray,
    tilt_beta: float,
    background_tag: str,
) -> HttForwardOutput:
    covariance = solver_output.anisotropic_covariance
    if not isinstance(covariance, dict):
        raise TypeError("solver_output.anisotropic_covariance must be a dict-like mapping")
    d_ell = covariance.get("D_ell")
    if not isinstance(d_ell, dict):
        raise TypeError("solver_output.anisotropic_covariance['D_ell'] must be present")
    ell = np.asarray(covariance.get("ell"), dtype=int)
    preferred_axis = np.asarray(
        covariance.get("preferred_axis", np.array([0.0, 0.0, 1.0], dtype=np.float64)),
        dtype=np.float64,
    )
    manifest = _make_manifest(
        artifact_id=artifact_id,
        artifact_path=_artifact_path(artifact_id.replace(".", "_")),
        owner="BASS",
        implementation_scope="canonical_BASS",
        claim_tier=solver_output.manifest.claim_tier,
        production_status=solver_output.manifest.production_status,
        input_hashes=(solver_output.manifest.artifact_id, atlas_artifact_id),
        caveats=("model_dependent_theory_bundle", "figure_export_projection"),
        statistics_definitions={"surface": "HttForwardOutput", "model_name": model_name},
    )
    axis_l_deg, axis_b_deg = _axis_lb_from_vector(preferred_axis)
    sigma_ab = np.asarray(sigma_tensor, dtype=np.float64)
    shear_sigma2 = 0.5 * float(np.sum(sigma_ab * sigma_ab))
    return HttForwardOutput(
        model_name=model_name,
        bianchi_type=str(solver_output.metadata.get("bianchi_type", "I")),
        axis_galactic_lb_deg=(axis_l_deg, axis_b_deg),
        ell=ell,
        C_ell_TT=np.asarray(d_ell["TT"], dtype=float),
        C_ell_TE=np.asarray(d_ell["TE"], dtype=float),
        C_ell_EE=np.asarray(d_ell["EE"], dtype=float),
        directional_summary={
            "axis_l_deg": axis_l_deg,
            "axis_b_deg": axis_b_deg,
            "offdiag_strength": float(covariance.get("offdiag_strength", 0.0)),
            "rotation_strength": float(covariance.get("rotation_strength", 0.0)),
        },
        shear_Sigma2=max(shear_sigma2, 0.0),
        tilt_beta=max(float(tilt_beta), 0.0),
        atlas_entry_hashes=(atlas_artifact_id,),
        generated_by=f"scripts.ver2_artifact_export.py:{background_tag}",
        git_commit=CURRENT_COMMIT,
        config_hash=_stable_hash(model_name, solver_output.manifest.artifact_id, background_tag),
        manifest=manifest,
    )


def _build_export_records() -> dict[str, ArtifactRecord]:
    tier_b_run, tier_a_run = _build_live_runtime_runs()
    solver_output = tier_b_run.solver_output
    observable, atlas = _observable_and_atlas(solver_output)
    mes_result = build_full_cov_mes_report(
        atlas,
        observable,
        parameter_block="R_sigma_proxy",
        diagonal_bound=2.0,
        singular_values=[0.5, 2.0],
        covariance_assumption="diag+offdiag",
        noise_radius=0.5,
    )
    mes_report = replace(
        mes_result.report,
        manifest=replace(
            mes_result.report.manifest,
            artifact_path=_artifact_path("bass_ver2_export_full_cov_mes_report"),
            git_commit=CURRENT_COMMIT,
        ),
    )
    departure_result = build_descriptive_departure_report(
        observable,
        bundle=DepartureBundle(
            comparator="matched",
            Sigma2_std=0.4,
            W2_std=0.1,
            Omega_tilt=0.2,
            Omega_k_aniso=0.1,
            covariance=None,
            frame_convention="normal_frame",
            sector="full",
            provenance={},
        ),
        budget=BudgetSpec(
            kind="linear_MES",
            value=1.0,
            uncertainty=None,
            family_id=None,
            channel="TT",
            redshift=None,
            confidence_level=None,
            assumptions=tuple(),
            is_admissible_ceiling=True,
        ),
        claim_gate_passed=False,
        occupancy_certified=False,
        g_values={"morphology": 0.32, "ceiling": 0.18},
    )
    departure_report = replace(
        departure_result.report,
        manifest=replace(
            departure_result.report.manifest,
            artifact_path=_artifact_path("common_ver2_export_departure_report"),
            git_commit=CURRENT_COMMIT,
        ),
    )
    discrimination = build_discrimination_matrix(
        observable,
        atlas_entry=atlas,
    )
    discrimination = replace(
        discrimination,
        manifest=replace(
            discrimination.manifest,
            artifact_id="htt.ver2.export.discrimination_matrix",
            artifact_path=_artifact_path("htt_ver2_export_discrimination_matrix"),
            git_commit=CURRENT_COMMIT,
            config_hash=_stable_hash("htt.ver2.export.discrimination_matrix"),
            caveats=list(discrimination.manifest.caveats),
        ),
    )

    tsc_manifest = _make_manifest(
        artifact_id="tsc.ver2.export.overlay",
        artifact_path=_artifact_path("tsc_ver2_export_overlay"),
        owner="TSC",
        implementation_scope="tsc",
        claim_tier="conditional",
        production_status="production_candidate",
        input_hashes=(observable.manifest.artifact_id, mes_report.manifest.artifact_id),
        caveats=("advisory_only", "no_runtime_decision_ownership"),
        statistics_definitions={"surface": "TscAdequacyOverlay"},
    )
    domain = build_domain_report(
        chart="one_field",
        theta_samples=[1.0, 1.1, 1.2],
        manifest=tsc_manifest,
    )
    residual = ambient_vs_projected_defect_report(
        chart="one_field",
        laguerre_n_ge_2_norm=0.1,
        ambient_defect_rate=None,
        projected_defect_estimate=None,
        onefield_residual=0.1,
        twofield_residual=0.05,
        eta_tangent_fraction=0.2,
        trace_residual_q_tr=0.1,
        spin2_residual=None,
        high_residual=None,
        labels=tuple(),
        manifest=tsc_manifest,
    )
    source = build_source_bridge_report(
        chart="one_field",
        q2_norm=0.1,
        manifest=tsc_manifest,
        source_error=0.01,
        on_manifold_exact=True,
    )
    budgets = build_channel_budgets(
        manifest=tsc_manifest,
        source_status=source.source_status,
        propagation_status="pending",
        source_error_bound=0.01,
        propagator_norm_bound=4.0,
        spin2_budget=0.2,
    )
    overlay = build_tsc_overlay(
        domain_report=domain,
        residual_report=residual,
        source_bridge_report=source,
        channel_budgets=budgets,
        upgrade_recommendation=recommend_chart_transition(domain, residual, source),
        artifact_manifest=tsc_manifest,
        artifact_metadata={
            "source_artifact_ids": [
                observable.manifest.artifact_id,
                mes_report.manifest.artifact_id,
            ]
        },
    )
    departure_report = attach_overlay_to_departure_report(departure_report, overlay)
    mes_report = attach_overlay_to_mes_report(mes_report, overlay)

    forward_a = _forward_output_from_solver_output(
        artifact_id="bass.ver2.export.forward.tier_a_validation",
        model_name="TierA_validation_reference",
        solver_output=tier_a_run.solver_output,
        atlas_artifact_id=atlas.manifest.artifact_id,
        sigma_tensor=tier_a_run.trace.background_monitor.sigma_tensor[-1],
        tilt_beta=0.0,
        background_tag="tier_a_validation",
    )
    forward_b = _forward_output_from_solver_output(
        artifact_id="bass.ver2.export.forward.tier_b_runtime",
        model_name="TierB_runtime_bridge",
        solver_output=tier_b_run.solver_output,
        atlas_artifact_id=atlas.manifest.artifact_id,
        sigma_tensor=tier_b_run.trace.background_monitor.sigma_tensor[-1],
        tilt_beta=0.0,
        background_tag="tier_b_runtime",
    )
    residual_atlas = build_predictive_residual_atlas_from_shared_schema(
        observable,
        (forward_a, forward_b),
        atlas_entry=atlas,
        covariance_ref=observable.manifest.artifact_id,
    )
    mio_certificate = to_predictive_residual_mio_certificate(
        residual_atlas,
        input_data_hashes=[
            observable.manifest.artifact_id,
            atlas.manifest.artifact_id,
            forward_a.manifest.artifact_id,
            forward_b.manifest.artifact_id,
        ],
        artifact_path=_artifact_path("mio_predictive_residuals_certificate"),
        tsc_overlay=overlay,
    )

    registry_payload = validation_registry_payload()
    registry_manifest = _make_manifest(
        artifact_id="common.ver2.validation_registry_summary",
        artifact_path=_artifact_path("common_ver2_validation_registry_summary"),
        owner="COMMON",
        implementation_scope="common",
        claim_tier="exploratory",
        production_status="production_candidate",
        input_hashes=tuple(
            campaign["campaign_id"] for campaign in registry_payload["campaigns"]  # type: ignore[index]
        ),
        caveats=("warn_campaigns_do_not_validate_claims",),
        statistics_definitions={
            "surface": "ValidationRegistrySummary",
            "campaign_count": len(registry_payload["campaigns"]),
            "theorem_count": len(registry_payload["theorem_map"]),
        },
    )

    records = {
        "observable": ArtifactRecord(
            key="observable",
            title="Observable vector proxy",
            topic="scalar_to_morphology",
            pack_id="A",
            manifest=observable.manifest,
            payload={
                "manifest": asdict(observable.manifest),
                "channels": list(observable.channels),
                "ell_max": observable.ell_max,
                "unique_index_count": int(observable.biposh["unique_index_count"]) if observable.biposh else 0,
                "null_proxy_status": None if observable.biposh is None else observable.biposh["null_proxy_status"],
                "covariance_features": _json_ready(observable.covariance_features),
            },
            summary="BASS low-ell observable substrate with explicit sparse covariance proxy semantics.",
            allowed_claims=(
                "manifest-backed channel availability summary",
                "proxy morphology summary with explicit caveats",
            ),
            forbidden_claims=(
                "validated_biposh_detection",
                "posterior_or_evidence_claim",
            ),
            evidence_refs=(observable.manifest.artifact_id,),
            notes=tuple(observable.manifest.caveats),
        ),
        "atlas": ArtifactRecord(
            key="atlas",
            title="AtlasEntryLite substrate",
            topic="scalar_to_morphology",
            pack_id="A",
            manifest=atlas.manifest,
            payload={
                "manifest": asdict(atlas.manifest),
                "theory_family": atlas.theory_family,
                "response_blocks": _json_ready(atlas.response_blocks),
                "validity_domain": _json_ready(atlas.validity_domain),
            },
            summary="Theory-side atlas substrate that carries morphology validity and sky-support metadata.",
            allowed_claims=("theory-side response overlap summary",),
            forbidden_claims=("observational_data_claim", "posterior_update_claim"),
            evidence_refs=(atlas.manifest.artifact_id,),
            notes=tuple(atlas.manifest.caveats),
        ),
        "mes": ArtifactRecord(
            key="mes",
            title="Full-covariance MES report",
            topic="scalar_to_morphology",
            pack_id="A",
            manifest=mes_report.manifest,
            payload={
                "manifest": asdict(mes_report.manifest),
                "parameter_block": mes_report.parameter_block,
                "diagonal_bound": mes_report.diagonal_bound,
                "covariance_bound": mes_report.covariance_bound,
                "final_bound": mes_report.final_bound,
                "information_gain": mes_report.information_gain,
                "response_rank": mes_report.response_rank,
                "tsc_overlay_ref": mes_report.tsc_overlay_ref,
            },
            summary="MES summary stays rank-gated and descriptive unless covariance prerequisites hold.",
            allowed_claims=("conditional morphology ceiling summary",),
            forbidden_claims=("weak_evidence_promotion_from_rank_failure",),
            evidence_refs=(mes_report.manifest.artifact_id,),
            notes=tuple(mes_report.manifest.caveats),
        ),
        "departure": ArtifactRecord(
            key="departure",
            title="Departure card",
            topic="departure_cards",
            pack_id="C",
            manifest=departure_report.manifest,
            payload={
                "manifest": asdict(departure_report.manifest),
                "x_value": departure_report.x_value,
                "Q_value": departure_report.Q_value,
                "F_value": departure_report.F_value,
                "F_status": departure_report.F_status,
                "G_values": departure_report.G_values,
                "tsc_overlay_ref": departure_report.tsc_overlay_ref,
            },
            summary="x/Q/Pi/F/G card remains descriptive because claim gates are intentionally not passed.",
            allowed_claims=("exploratory departure-card summary",),
            forbidden_claims=("certified_filling_language", "validated_geometry_claim"),
            evidence_refs=(departure_report.manifest.artifact_id,),
            notes=tuple(departure_report.caveats),
        ),
        "discrimination": ArtifactRecord(
            key="discrimination",
            title="Local-vs-global discrimination matrix",
            topic="local_global_discrimination",
            pack_id="B",
            manifest=discrimination.manifest,
            payload={
                "manifest": asdict(discrimination.manifest),
                "hypotheses": list(discrimination.hypotheses),
                "overlap_matrix": _json_ready(np.asarray(discrimination.overlap_matrix, dtype=float)),
                "recommended_next_observable": dict(discrimination.recommended_next_observable),
                "claim_tier_by_pair": dict(discrimination.claim_tier_by_pair),
            },
            summary=(
                "HTT discrimination matrix provides a bounded pre-inference "
                "local-vs-global separation audit."
                if discrimination.manifest.claim_tier == "conditional"
                else "HTT discrimination matrix keeps observer-side and source-side hypotheses separate."
            ),
            allowed_claims=(
                ("conditional local-vs-global discrimination summary",)
                if discrimination.manifest.claim_tier == "conditional"
                else ("exploratory degeneracy summary",)
            ),
            forbidden_claims=("posterior_odds_claim", "global_tilt_confirmation"),
            evidence_refs=(discrimination.manifest.artifact_id,),
            notes=tuple(discrimination.manifest.caveats),
        ),
        "overlay": ArtifactRecord(
            key="overlay",
            title="TSC adequacy overlay",
            topic="adequacy_overlay",
            pack_id="D",
            manifest=overlay.manifest,
            payload=overlay_to_json_dict(overlay),
            summary="TSC overlay remains advisory and records pending propagation explicitly.",
            allowed_claims=("conditional adequacy caveat summary",),
            forbidden_claims=("runtime_allow_block_claim", "posterior_correction_claim"),
            evidence_refs=(overlay.manifest.artifact_id,),
            notes=tuple(overlay.manifest.caveats),
        ),
        "mio": ArtifactRecord(
            key="mio",
            title="MIO predictive residual certificate",
            topic="mio_residual_atlas",
            pack_id="D",
            manifest=mio_certificate.manifest,
            payload=certificate_to_payload(mio_certificate),
            summary="MIO residual atlas stays diagnostic and owner-separated from HTT posterior semantics.",
            allowed_claims=("conditional residual-atlas comparison summary",),
            forbidden_claims=("truth_certificate_claim", "posterior_claim"),
            evidence_refs=(mio_certificate.manifest.artifact_id,),
            notes=tuple(mio_certificate.domain_caveats),
        ),
        "validation_registry": ArtifactRecord(
            key="validation_registry",
            title="Validation registry summary",
            topic="equivalence_classes",
            pack_id="E",
            manifest=registry_manifest,
            payload={
                "manifest": asdict(registry_manifest),
                "registry": registry_payload,
            },
            summary="Executable theorem/campaign registry with five-category coverage and hostile-audit mirrors.",
            allowed_claims=("exploratory validation coverage summary",),
            forbidden_claims=("validated_science_gate_from_warn_campaigns",),
            evidence_refs=(registry_manifest.artifact_id,),
            notes=("warn_campaigns_remain_no_claim",),
        ),
    }
    return records


def _build_pack_records(records: dict[str, ArtifactRecord]) -> tuple[PackRecord, ...]:
    definitions = (
        (
            "A",
            "Scalar-to-morphology bridge",
            "scalar_to_morphology",
            "fig_ver2a_scalar_to_morphology_summary",
            ("observable", "atlas", "mes"),
            (
                "Observable channels, sparse morphology proxy, and MES ceilings are exported together.",
                "The pack remains conditional because morphology is still proxy-scoped, not a full validated BiPoSH basis.",
            ),
        ),
        (
            "B",
            "Local-vs-global discrimination",
            "local_global_discrimination",
            "fig_ver2b_local_global_discrimination_matrix",
            ("discrimination",),
            (
                "The HTT discrimination matrix is exploratory and keeps local boost distinct from global tilt.",
                "No posterior odds or source-side confirmation are exported here.",
            ),
        ),
        (
            "C",
            "Departure cards",
            "departure_cards",
            "fig_ver2c_departure_card_summary",
            ("departure", "overlay"),
            (
                "x/Q/F/G surfaces are emitted as descriptive cards with attached TSC caveats.",
                "Certified filling language remains blocked in this export set.",
            ),
        ),
        (
            "D",
            "MIO certificates",
            "mio_residual_atlas",
            "fig_ver2d_mio_predictive_residuals",
            ("mio", "overlay"),
            (
                "The MIO residual atlas and the TSC overlay are exported together without merging ownership semantics.",
                "Residual slices remain diagnostic model/data comparisons, not posterior or truth outputs.",
            ),
        ),
        (
            "E",
            "Equivalence and validation classes",
            "equivalence_classes",
            "fig_ver2e_validation_campaign_matrix",
            ("validation_registry",),
            (
                "The validation registry is exported as a manifest-backed coverage matrix.",
                "Warn campaigns remain explicit no-claim gates until later manuscript closure.",
            ),
        ),
    )
    packs: list[PackRecord] = []
    for pack_id, title, topic, figure_base, record_keys, summary_lines in definitions:
        artifacts = tuple(records[key] for key in record_keys)
        claim_tier = _min_claim_tier(
            tuple(record.manifest.claim_tier for record in artifacts)
        )
        production_status = _derive_export_production_status(
            tuple(record.manifest for record in artifacts),
            claim_tier=claim_tier,
        )
        caveats = tuple(
            dict.fromkeys(
                caveat
                for record in artifacts
                for caveat in record.manifest.caveats + list(record.notes)
            )
        )
        packs.append(
            PackRecord(
                pack_id=pack_id,
                title=title,
                topic=topic,
                figure_base=figure_base,
                artifacts=artifacts,
                claim_tier=claim_tier,
                production_status=production_status,
                caveats=caveats,
                summary_lines=summary_lines,
            )
        )
    return tuple(packs)


def _status_rows(records: dict[str, ArtifactRecord]) -> list[dict[str, object]]:
    rows = [
        snapshot_entry_to_dict(
            StatusSnapshotEntry(
                artifact_id=record.manifest.artifact_id,
                owner=record.manifest.owner,
                implementation_scope=record.manifest.implementation_scope,
                claim_tier=record.manifest.claim_tier,
                implemented=True,
                smoke_tested=True,
                production_validated=(
                    record.manifest.production_status == "production_validated"
                ),
                manuscript_used=True,
                source_commit=record.manifest.git_commit or CURRENT_COMMIT,
            )
        )
        for record in records.values()
    ]
    return sorted(rows, key=lambda row: str(row["artifact_id"]))


def _claim_rows(records: dict[str, ArtifactRecord]) -> list[dict[str, object]]:
    rows = [
        claim_entry_to_dict(
            ClaimLedgerEntry(
                artifact_id=record.manifest.artifact_id,
                owner=record.manifest.owner,
                claim_tier=record.manifest.claim_tier,
                allowed_claims=record.allowed_claims,
                forbidden_claims=record.forbidden_claims,
                evidence_refs=record.evidence_refs,
                source_commit=record.manifest.git_commit or CURRENT_COMMIT,
                notes=record.notes,
            )
        )
        for record in records.values()
    ]
    return sorted(rows, key=lambda row: str(row["artifact_id"]))


def _record_manifest_payload(record: ArtifactRecord) -> dict[str, object]:
    return {
        "title": record.title,
        "topic": record.topic,
        "summary": record.summary,
        "manifest": asdict(record.manifest),
        "payload": record.payload,
        "allowed_claims": list(record.allowed_claims),
        "forbidden_claims": list(record.forbidden_claims),
        "evidence_refs": list(record.evidence_refs),
        "notes": list(record.notes),
    }


def _pack_payload(pack: PackRecord) -> dict[str, object]:
    return {
        "pack_id": pack.pack_id,
        "title": pack.title,
        "topic": pack.topic,
        "figure_base": pack.figure_base,
        "claim_tier": pack.claim_tier,
        "production_status": pack.production_status,
        "caveats": list(pack.caveats),
        "summary_lines": list(pack.summary_lines),
        "artifacts": [
            {
                "artifact_id": record.manifest.artifact_id,
                "title": record.title,
                "owner": record.manifest.owner,
                "claim_tier": record.manifest.claim_tier,
                "production_status": record.manifest.production_status,
                "summary": record.summary,
                "evidence_refs": list(record.evidence_refs),
            }
            for record in pack.artifacts
        ],
    }


def _render_status_markdown(rows: list[dict[str, object]]) -> str:
    by_owner = Counter(str(row["owner"]) for row in rows)
    total = len(rows)
    implemented = sum(bool(row["implemented"]) for row in rows)
    smoke_tested = sum(bool(row["smoke_tested"]) for row in rows)
    production_validated = sum(bool(row["production_validated"]) for row in rows)
    manuscript_used = sum(bool(row["manuscript_used"]) for row in rows)
    table = "\n".join(
        f"| `{owner}` | {count} |" for owner, count in sorted(by_owner.items())
    )
    return "\n".join(
        (
            "<!-- Generated by scripts/ver2_artifact_export.py -->",
            "# VER2 Status Snapshot",
            "",
            "Semantic source: `htt/src/common/contracts.py::StatusSnapshotEntry`",
            "",
            "| Metric | Count |",
            "| --- | ---: |",
            f"| Total rows | {total} |",
            f"| Implemented | {implemented} |",
            f"| Smoke tested | {smoke_tested} |",
            f"| Production validated | {production_validated} |",
            f"| Manuscript used | {manuscript_used} |",
            "",
            "| Owner | Rows |",
            "| --- | ---: |",
            table,
        )
    ) + "\n"


def _render_claim_markdown(rows: list[dict[str, object]]) -> str:
    by_tier = Counter(str(row["claim_tier"]) for row in rows)
    table = "\n".join(
        f"| `{tier}` | {count} |" for tier, count in sorted(by_tier.items())
    )
    return "\n".join(
        (
            "<!-- Generated by scripts/ver2_artifact_export.py -->",
            "# VER2 Claim Ledger",
            "",
            "Semantic source: `htt/src/common/contracts.py::ClaimLedgerEntry`",
            "",
            "| Claim tier | Rows |",
            "| --- | ---: |",
            table,
            "",
            "Each row remains tied to owner/scope-specific forbidden-claim fences in",
            "the JSON artifact. This Markdown mirror exists only as a human-readable",
            "index over the canonical generated ledger.",
        )
    ) + "\n"


def _render_result_pack_index(packs: tuple[PackRecord, ...]) -> str:
    rows = "\n".join(
        (
            f"| `{pack.pack_id}` | {pack.title} | `{pack.claim_tier}` | "
            f"`{pack.production_status}` | `{pack.figure_base}` | "
            f"{len(pack.artifacts)} |"
        )
        for pack in packs
    )
    return "\n".join(
        (
            "<!-- Generated by scripts/ver2_artifact_export.py -->",
            "# VER2 Result-Pack Index",
            "",
            "Manifest-backed result-pack registry for `PR-MAN-15`.",
            "",
            "| Pack | Title | Claim tier | Production status | Figure base | Source artifacts |",
            "| --- | --- | --- | --- | --- | ---: |",
            rows,
        )
    ) + "\n"


def _render_titlepage_status_tex(rows: list[dict[str, object]]) -> str:
    implemented = sum(bool(row["implemented"]) for row in rows)
    smoke_tested = sum(bool(row["smoke_tested"]) for row in rows)
    production_validated = sum(bool(row["production_validated"]) for row in rows)
    manuscript_used = sum(bool(row["manuscript_used"]) for row in rows)
    body = dedent(
        f"""
\\textbf{{VER2 status hook.}}
Snapshot-backed counts: implemented={implemented}, smoke-tested={smoke_tested},
production-validated={production_validated}, manuscript-used={manuscript_used}.
"""
    ).strip()
    return "% Generated by scripts/ver2_artifact_export.py\n" + body + "\n"


def _render_status_snapshot_tex(rows: list[dict[str, object]]) -> str:
    by_owner = Counter(str(row["owner"]) for row in rows)
    total = len(rows)
    implemented = sum(bool(row["implemented"]) for row in rows)
    smoke_tested = sum(bool(row["smoke_tested"]) for row in rows)
    production_validated = sum(bool(row["production_validated"]) for row in rows)
    owner_rows = "\n".join(
        f"{_escape_tex(owner)} & {count} \\\\" for owner, count in sorted(by_owner.items())
    )
    return dedent(
        f"""
% Generated by scripts/ver2_artifact_export.py
\\paragraph{{VER2 shared status snapshot hook.}}
Snapshot totals: total rows {total}, implemented {implemented},
smoke-tested {smoke_tested}, production-validated {production_validated}.

\\begin{{center}}
\\begin{{tabular}}{{lr}}
\\hline
Owner & Rows \\\\
\\hline
{owner_rows}
\\hline
\\end{{tabular}}
\\end{{center}}
"""
    ).strip() + "\n"


def _render_claim_ledger_tex(rows: list[dict[str, object]]) -> str:
    by_tier = Counter(str(row["claim_tier"]) for row in rows)
    tier_rows = "\n".join(
        f"{_escape_tex(tier)} & {count} \\\\" for tier, count in sorted(by_tier.items())
    )
    return dedent(
        f"""
% Generated by scripts/ver2_artifact_export.py
\\paragraph{{VER2 claim-ledger hook.}}
\\begin{{center}}
\\begin{{tabular}}{{lr}}
\\hline
Claim tier & Rows \\\\
\\hline
{tier_rows}
\\hline
\\end{{tabular}}
\\end{{center}}
"""
    ).strip() + "\n"


def _render_artifact_policy_tex(
    manifest_fields: list[str],
    figures: list[dict[str, object]],
) -> str:
    missing = sum(not bool(row["has_manifest"]) for row in figures)
    ready = sum(row["export_status"] == "manifest_ready" for row in figures)
    total = len(figures)
    field_list = ", ".join(
        f"\\texttt{{{_escape_tex(name)}}}" for name in manifest_fields
    )
    return dedent(
        f"""\
        % Generated by scripts/ver2_artifact_export.py
        \\paragraph{{Artifact-first export hook.}}
        Figures and tables remain blocked from VER2 manuscript promotion unless a
        canonical \\texttt{{ArtifactManifest}} is present. Required manifest fields
        remain owned by \\texttt{{common.contracts}} and are not redefined here:
        {field_list}.

        \\paragraph{{Current figure-manifest audit.}}
        The paper figure tree currently exposes {total} figure bases, of which
        {ready} are manifest-ready and {missing} remain blocked by missing manifests
        or caption/manifest gate failures. The audit lives in
        \\texttt{{figures/paper/VER2\\_MANIFEST\\_INDEX.md}}.
        """
    )


def _render_tsc_scope_boundary_tex() -> str:
    return dedent(
        r"""
% Generated by scripts/ver2_artifact_export.py
\paragraph{TSC scope boundary.}
The active-service TSC layer is an advisory and quarantine surface. It may
diagnose domain failure, residual inadequacy, or source/propagation mismatch,
but it does not own the forward solver, the final runtime allow/block
decision, or posterior/evidence semantics.
"""
    ).strip() + "\n"


def _render_source_vs_propagation_tex() -> str:
    return dedent(
        r"""
% Generated by scripts/ver2_artifact_export.py
\paragraph{Source versus propagation split.}
VER2 keeps source generation, anisotropic propagation, and observable
interpretation as separate ownership layers. TSC commentary may attach to any
of those layers, but it cannot collapse them into a single truth label for
the manuscript.
"""
    ).strip() + "\n"


def _render_channel_responsibility_tex() -> str:
    return dedent(
        r"""
% Generated by scripts/ver2_artifact_export.py
\paragraph{Cross-package responsibility.}
BASS owns runtime and observer-neutral forward outputs. HTT owns
directional likelihoods, posterior, and evidence. MIO owns
model-independent diagnostics and certificates. TSC owns adequacy overlays,
caveats, and quarantine hooks. This insertion point exists so manuscript
wording cannot silently swap one package's responsibility onto another.
"""
    ).strip() + "\n"


def _render_result_pack_summary_tex(packs: tuple[PackRecord, ...]) -> str:
    rows = "\n".join(
        (
            f"{_escape_tex(pack.pack_id)} & {_escape_tex(pack.title)} & "
            f"\\texttt{{{_escape_tex(pack.claim_tier)}}} & "
            f"\\texttt{{{_escape_tex(pack.production_status)}}} & "
            f"{_escape_tex(MANUSCRIPT_ROLE_BY_PACK[pack.pack_id])} \\\\"
        )
        for pack in packs
    )
    return dedent(
        f"""
% Generated by scripts/ver2_artifact_export.py
\\paragraph{{VER2 result-pack to manuscript map.}}
Only manifest-backed result packs may be cited in the VER2 manuscript path.
The current crosswalk is:

\\begin{{center}}
\\begin{{tabular}}{{lp{{3.1cm}}p{{2.2cm}}p{{2.7cm}}p{{6.4cm}}}}
\\hline
Pack & Title & Claim tier & Production status & Manuscript use \\\\
\\hline
{rows}
\\hline
\\end{{tabular}}
\\end{{center}}
"""
    ).strip() + "\n"


def _render_figure_manifest_status_tex(
    packs: tuple[PackRecord, ...],
    figures: list[dict[str, object]],
) -> str:
    ready = [row for row in figures if row["export_status"] == "manifest_ready"]
    blocked = len(figures) - len(ready)
    conditional = [pack.figure_base for pack in packs if pack.claim_tier == "conditional"]
    exploratory = [pack.figure_base for pack in packs if pack.claim_tier == "exploratory"]
    conditional_text = ", ".join(f"\\texttt{{{_escape_tex(name)}}}" for name in conditional)
    exploratory_text = ", ".join(f"\\texttt{{{_escape_tex(name)}}}" for name in exploratory)
    return dedent(
        f"""
% Generated by scripts/ver2_artifact_export.py
\\paragraph{{VER2 figure-promotion status.}}
The shared manifest audit currently reports {len(ready)} manifest-ready VER2 figure
bases and {blocked} blocked legacy bases. The promoted conditional figures are
{conditional_text}. Exploratory appendix-only figures are {exploratory_text}. All
remaining legacy paper figures stay blocked until a canonical manifest and a
caption-tier check are present.
"""
    ).strip() + "\n"


def _render_validation_status_tex(
    records: dict[str, ArtifactRecord],
    rows: list[dict[str, object]],
) -> str:
    registry = records["validation_registry"].payload["registry"]
    campaigns = registry["campaigns"]  # type: ignore[index]
    theorem_map = registry["theorem_map"]  # type: ignore[index]
    by_status = Counter(str(campaign["status"]) for campaign in campaigns)
    status_bits = ", ".join(
        f"{_escape_tex(status)}={count}" for status, count in sorted(by_status.items())
    )
    production_validated = sum(bool(row["production_validated"]) for row in rows)
    return dedent(
        f"""
% Generated by scripts/ver2_artifact_export.py
\\paragraph{{VER2 validation ceiling.}}
The executable VER2 registry currently contains {len(campaigns)} campaigns and
{len(theorem_map)} theorem anchors; campaign states are {status_bits}. The shared
status snapshot reports {production_validated} production-validated rows. Warn-grade
campaigns therefore remain explicit no-claim gates: they document coverage and
hostile-audit provenance, but they do not by themselves validate a scientific claim.
"""
    ).strip() + "\n"


def _pack_file_paths(pack: PackRecord) -> tuple[Path, Path, Path]:
    stem = PACK_FILE_STEMS[pack.pack_id]
    return (
        VER2_GEN / f"{stem}.json",
        VER2_GEN / f"{stem}.md",
        VER2_GEN / f"{stem}.tex",
    )


def _render_pack_markdown(pack: PackRecord) -> str:
    rows = "\n".join(
        (
            f"| `{record.manifest.artifact_id}` | `{record.manifest.owner}` | "
            f"`{record.manifest.claim_tier}` | `{record.manifest.production_status}` | "
            f"{record.summary} |"
        )
        for record in pack.artifacts
    )
    caveat_text = ", ".join(pack.caveats) if pack.caveats else "none"
    summary_text = "\n".join(f"- {line}" for line in pack.summary_lines)
    return "\n".join(
        (
            "<!-- Generated by scripts/ver2_artifact_export.py -->",
            f"# Result Pack {pack.pack_id} — {pack.title}",
            "",
            f"- topic: `{pack.topic}`",
            f"- claim tier: `{pack.claim_tier}`",
            f"- production status: `{pack.production_status}`",
            f"- figure base: `{pack.figure_base}`",
            f"- caveats: {caveat_text}",
            "",
            summary_text,
            "",
            "| Artifact | Owner | Claim tier | Production status | Summary |",
            "| --- | --- | --- | --- | --- |",
            rows,
        )
    ) + "\n"


def _render_pack_tex(pack: PackRecord) -> str:
    rows = "\n".join(
        (
            f"{_escape_tex(record.title)} & {_escape_tex(record.manifest.owner)} & "
            f"{_escape_tex(record.manifest.claim_tier)} & "
            f"{_escape_tex(record.manifest.production_status)} \\\\"
        )
        for record in pack.artifacts
    )
    caveat_text = _escape_tex(", ".join(pack.caveats) if pack.caveats else "none")
    return dedent(
        f"""
% Generated by scripts/ver2_artifact_export.py
\\paragraph{{Result Pack {pack.pack_id}: {_escape_tex(pack.title)}}}
Claim tier: \\texttt{{{_escape_tex(pack.claim_tier)}}}. Production status:
\\texttt{{{_escape_tex(pack.production_status)}}}. Caveats: {caveat_text}.

\\begin{{center}}
\\begin{{tabular}}{{llll}}
\\hline
Artifact & Owner & Claim tier & Production status \\\\
\\hline
{rows}
\\hline
\\end{{tabular}}
\\end{{center}}
"""
    ).strip() + "\n"


def _gallery_topic_map(packs: tuple[PackRecord, ...]) -> tuple[list[dict[str, object]], str]:
    rows = [
        {
            "figure_base": pack.figure_base,
            "chapter": "ver2_generated",
            "pack_id": pack.pack_id,
            "title": pack.title,
            "topic": pack.topic,
            "claim_tier": pack.claim_tier,
            "production_status": pack.production_status,
            "source_artifact_ids": [record.manifest.artifact_id for record in pack.artifacts],
        }
        for pack in packs
    ]
    md_rows = "\n".join(
        (
            f"| `{row['figure_base']}` | `{row['pack_id']}` | {row['title']} | "
            f"`{row['claim_tier']}` | `{row['production_status']}` | "
            f"{', '.join(f'`{ref}`' for ref in row['source_artifact_ids'])} |"
        )
        for row in rows
    )
    markdown = "\n".join(
        (
            "<!-- Generated by scripts/ver2_artifact_export.py -->",
            "# VER2 Figure Gallery Topic Map",
            "",
            "| Figure base | Pack | Title | Claim tier | Production status | Source artifacts |",
            "| --- | --- | --- | --- | --- | --- |",
            md_rows,
        )
    ) + "\n"
    return rows, markdown


def _render_figure_index(packs: tuple[PackRecord, ...]) -> str:
    rows = "\n".join(
        (
            f"| `{pack.figure_base}` | `{pack.pack_id}` | {pack.title} | "
            f"`{pack.claim_tier}` | `{pack.production_status}` |"
        )
        for pack in packs
    )
    return "\n".join(
        (
            "<!-- Generated by scripts/ver2_artifact_export.py -->",
            "# VER2 Generated Figures",
            "",
            "This directory contains manifest-backed D-lane figures emitted directly",
            "from current VER2 artifacts.",
            "",
            "| Figure base | Pack | Title | Claim tier | Production status |",
            "| --- | --- | --- | --- | --- |",
            rows,
        )
    ) + "\n"


def _caption_text(pack: PackRecord) -> str:
    caveat_text = ", ".join(pack.caveats[:4]) if pack.caveats else "none"
    artifacts = ", ".join(record.manifest.artifact_id for record in pack.artifacts)
    return "\n".join(
        (
            f"Claim tier: {pack.claim_tier}.",
            f"Result Pack {pack.pack_id}: {pack.title}.",
            "This figure is generated only from manifest-backed VER2 artifacts.",
            f"Source artifacts: {artifacts}.",
            f"Caveats: {caveat_text}.",
        )
    ) + "\n"


def _caption_claim_violation(caption: str, claim_tier: str) -> str | None:
    lowered = caption.lower()
    if f"claim tier: {claim_tier}." not in lowered:
        return "missing_claim_tier_tag"
    stronger_tokens = {
        "blocked": ("exploratory", "conditional", "validated", "confirmed", "detected"),
        "exploratory": ("conditional", "validated", "confirmed", "detected"),
        "conditional": ("validated", "confirmed", "detected"),
        "validated": (),
    }[claim_tier]
    if any(token in lowered for token in stronger_tokens):
        return "caption_stronger_than_claim_tier"
    return None


def _pack_figure_manifest(pack: PackRecord) -> ArtifactManifest:
    source_manifests = tuple(record.manifest for record in pack.artifacts)
    claim_tier = pack.claim_tier
    production_status = _derive_export_production_status(
        source_manifests,
        claim_tier=claim_tier,
    )
    return _make_manifest(
        artifact_id=f"common.ver2.figure.{pack.pack_id.lower()}",
        artifact_path=_figure_manifest_path(pack.figure_base),
        owner="COMMON",
        implementation_scope="common",
        claim_tier=claim_tier,
        production_status=production_status,
        input_hashes=tuple(record.manifest.artifact_id for record in pack.artifacts),
        caveats=pack.caveats,
        statistics_definitions={
            "surface": "PaperFigureExport",
            "result_pack_id": pack.pack_id,
            "topic": pack.topic,
            "source_artifact_ids": [record.manifest.artifact_id for record in pack.artifacts],
        },
    )


def _figure_axes_style(ax: plt.Axes, *, title: str, ylabel: str | None = None) -> None:
    ax.set_title(title, fontsize=10)
    if ylabel is not None:
        ax.set_ylabel(ylabel)
    ax.grid(axis="y", alpha=0.25)


def _plot_pack_figure(pack: PackRecord, base_path: Path) -> tuple[str, dict[str, object]]:
    fig, ax = plt.subplots(figsize=(7.2, 4.2), constrained_layout=True)
    if pack.pack_id == "A":
        observable = next(record for record in pack.artifacts if record.key == "observable")
        mes = next(record for record in pack.artifacts if record.key == "mes")
        channels = list(observable.payload["channels"])  # type: ignore[index]
        values = [1.0] * len(channels)
        ax.bar(channels, values, color="#4C72B0")
        ax.set_ylim(0.0, 1.3)
        ax.text(
            0.98,
            0.95,
            f"final_bound={float(mes.payload['final_bound']):.2f}\n"
            f"response_rank={int(mes.payload['response_rank'])}",
            transform=ax.transAxes,
            ha="right",
            va="top",
            fontsize=9,
            bbox={"facecolor": "white", "alpha": 0.85, "edgecolor": "#999999"},
        )
        _figure_axes_style(ax, title="Scalar-to-morphology summary", ylabel="present")
    elif pack.pack_id == "B":
        discrimination = pack.artifacts[0]
        matrix = np.asarray(discrimination.payload["overlap_matrix"], dtype=float)  # type: ignore[index]
        hypotheses = list(discrimination.payload["hypotheses"])  # type: ignore[index]
        im = ax.imshow(matrix, cmap="viridis", vmin=0.0, vmax=1.0)
        ax.set_xticks(range(len(hypotheses)), hypotheses, rotation=20)
        ax.set_yticks(range(len(hypotheses)), hypotheses)
        for i in range(matrix.shape[0]):
            for j in range(matrix.shape[1]):
                ax.text(j, i, f"{matrix[i, j]:.2f}", ha="center", va="center", color="white")
        fig.colorbar(im, ax=ax, shrink=0.8, label="overlap")
        _figure_axes_style(ax, title="Local-vs-global discrimination matrix")
    elif pack.pack_id == "C":
        departure = pack.artifacts[0]
        labels = ["x", "Q", "G_morphology", "G_ceiling"]
        values = [
            float(departure.payload["x_value"]),  # type: ignore[index]
            float(departure.payload["Q_value"]),  # type: ignore[index]
            float(departure.payload["G_values"]["morphology"]),  # type: ignore[index]
            float(departure.payload["G_values"]["ceiling"]),  # type: ignore[index]
        ]
        ax.bar(labels, values, color=["#DD8452", "#4C72B0", "#55A868", "#C44E52"])
        ax.set_ylim(0.0, max(values) * 1.35)
        ax.text(
            0.98,
            0.95,
            f"F_status={departure.payload['F_status']}",
            transform=ax.transAxes,
            ha="right",
            va="top",
            fontsize=9,
            bbox={"facecolor": "white", "alpha": 0.85, "edgecolor": "#999999"},
        )
        _figure_axes_style(ax, title="Departure card summary", ylabel="value")
    elif pack.pack_id == "D":
        mio = next(record for record in pack.artifacts if record.key == "mio")
        metrics = mio.payload["consistency_metrics"]  # type: ignore[index]
        slice_keys = sorted(
            key for key in metrics if key.endswith("_max_abs")
        )[:6]
        labels = [key.replace("_max_abs", "") for key in slice_keys]
        values = [float(metrics[key]) for key in slice_keys]
        ax.barh(labels, values, color="#8172B3")
        ax.invert_yaxis()
        _figure_axes_style(ax, title="MIO predictive residual slices", ylabel=None)
        ax.set_xlabel("max |residual|")
    else:
        registry = pack.artifacts[0]
        campaigns = registry.payload["registry"]["campaigns"]  # type: ignore[index]
        categories = list(REQUIRED_VALIDATION_CATEGORIES)
        matrix = np.asarray(
            [
                [1.0 if category in campaign["categories"] else 0.0 for category in categories]
                for campaign in campaigns
            ],
            dtype=float,
        )
        im = ax.imshow(matrix, cmap="Blues", vmin=0.0, vmax=1.0)
        ax.set_xticks(range(len(categories)), categories, rotation=25, ha="right")
        ax.set_yticks(
            range(len(campaigns)),
            [campaign["campaign_id"].replace("validation.", "") for campaign in campaigns],
        )
        for i in range(matrix.shape[0]):
            for j in range(matrix.shape[1]):
                ax.text(j, i, "1" if matrix[i, j] else "0", ha="center", va="center")
        fig.colorbar(im, ax=ax, shrink=0.8, label="coverage")
        _figure_axes_style(ax, title="Validation campaign coverage matrix")
    png_path = base_path.with_suffix(".png")
    pdf_path = base_path.with_suffix(".pdf")
    fig.savefig(png_path, dpi=300)
    fig.savefig(pdf_path)
    plt.close(fig)
    caption = _caption_text(pack)
    manifest = _pack_figure_manifest(pack)
    caption_path = base_path.with_suffix(".caption.txt")
    manifest_path = base_path.with_name(base_path.name + ".manifest.json")
    caption_path.write_text(caption, encoding="utf-8")
    manifest_path.write_text(_dump_json(manifest_path, asdict(manifest)), encoding="utf-8")
    return caption, asdict(manifest)


def _generate_pack_figures(
    packs: tuple[PackRecord, ...],
    *,
    figure_dir: Path = FIGURE_GEN,
) -> dict[str, tuple[str, dict[str, object]]]:
    figure_dir.mkdir(parents=True, exist_ok=True)
    generated: dict[str, tuple[str, dict[str, object]]] = {}
    for pack in packs:
        base_path = figure_dir / pack.figure_base
        caption, manifest_payload = _plot_pack_figure(pack, base_path)
        generated[pack.figure_base] = (caption, manifest_payload)
    return generated


def _load_manifest(manifest_path: Path) -> ArtifactManifest | None:
    try:
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(payload, dict):
        return None
    allowed = {field.name for field in fields(ArtifactManifest)}
    manifest_kwargs = {name: payload[name] for name in allowed if name in payload}
    try:
        return ArtifactManifest(**manifest_kwargs)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None


def _scan_figure_asset(
    *,
    asset: Path,
    figures: dict[tuple[str, str], dict[str, object]],
    chapter: str,
) -> None:
    suffixes = asset.suffixes
    if suffixes[-1:] in ([".png"], [".pdf"]):
        stem = asset.stem
    elif suffixes[-2:] == [".caption", ".txt"]:
        stem = asset.name[: -len(".caption.txt")]
    elif suffixes[-2:] == [".manifest", ".json"]:
        stem = asset.name[: -len(".manifest.json")]
    else:
        return
    key = (chapter, stem)
    entry = figures.setdefault(
        key,
        {
            "chapter": chapter,
            "stem": stem,
            "has_png": False,
            "has_pdf": False,
            "has_caption": False,
            "has_manifest": False,
            "owner": None,
            "claim_tier": None,
            "topic": None,
            "caption_check": "not_checked",
            "export_status": "blocked_no_manifest",
        },
    )
    if suffixes[-1:] == [".png"]:
        entry["has_png"] = True
    elif suffixes[-1:] == [".pdf"]:
        entry["has_pdf"] = True
    elif suffixes[-2:] == [".caption", ".txt"]:
        entry["has_caption"] = True
    elif suffixes[-2:] == [".manifest", ".json"]:
        entry["has_manifest"] = True


def _scan_figures(root: Path, *, generated_root: Path | None = None) -> list[dict[str, object]]:
    figures: dict[tuple[str, str], dict[str, object]] = {}
    for asset in sorted(root.rglob("*")):
        if not asset.is_file():
            continue
        if generated_root is not None and asset.is_relative_to(FIGURE_GEN):
            continue
        _scan_figure_asset(
            asset=asset,
            figures=figures,
            chapter=asset.parent.relative_to(root).as_posix(),
        )

    if generated_root is not None:
        for asset in sorted(generated_root.rglob("*")):
            if not asset.is_file():
                continue
            _scan_figure_asset(
                asset=asset,
                figures=figures,
                chapter="ver2_generated",
            )

    ordered = sorted(figures.values(), key=lambda row: (row["chapter"], row["stem"]))
    for row in ordered:
        if row["chapter"] == "ver2_generated" and generated_root is not None:
            base = generated_root / row["stem"]
        else:
            base = root / row["chapter"] / row["stem"]
        manifest_path = base.with_name(base.name + ".manifest.json")
        caption_path = base.with_suffix(".caption.txt")
        assets = []
        if row["has_png"]:
            assets.append("png")
        if row["has_pdf"]:
            assets.append("pdf")
        if row["has_caption"]:
            assets.append("caption")
        row["assets"] = ", ".join(assets) or "none"
        if not (row["has_png"] and row["has_pdf"] and row["has_caption"]):
            row["export_status"] = "blocked_incomplete_assets"
            continue
        if not row["has_manifest"]:
            row["export_status"] = "blocked_no_manifest"
            continue
        manifest = _load_manifest(manifest_path)
        if manifest is None:
            row["export_status"] = "blocked_invalid_manifest"
            continue
        row["owner"] = manifest.owner
        row["claim_tier"] = manifest.claim_tier
        row["topic"] = manifest.statistics_definitions.get("topic")
        caption = caption_path.read_text(encoding="utf-8")
        violation = _caption_claim_violation(caption, manifest.claim_tier)
        row["caption_check"] = violation or "ok"
        if violation is not None:
            row["export_status"] = "blocked_caption_claim_tier"
        elif manifest.claim_tier == "blocked" or manifest.production_status.startswith("blocked_"):
            row["export_status"] = "quarantined_blocked_artifact"
        else:
            row["export_status"] = "manifest_ready"
    return ordered


def _render_manifest_index(
    figures: list[dict[str, object]],
    manifest_fields: list[str],
) -> str:
    missing = sum(not bool(row["has_manifest"]) for row in figures)
    ready = sum(row["export_status"] == "manifest_ready" for row in figures)
    rows = "\n".join(
        (
            f"| `{row['chapter']}` | `{row['stem']}` | {row['assets']} | "
            f"{'yes' if row['has_manifest'] else 'no'} | "
            f"`{row['claim_tier'] or 'n/a'}` | `{row['caption_check']}` | "
            f"`{row['export_status']}` |"
        )
        for row in figures
    )
    field_line = ", ".join(f"`{name}`" for name in manifest_fields)
    return dedent(
        f"""
<!-- Generated by scripts/ver2_artifact_export.py -->
# VER2 Figure Manifest Index

This is the IM-09D figure-manifest audit surface for the paper figure tree.
Legacy paper figures remain blocked until they carry canonical manifests.
Generated VER2 export figures appear here with claim-tier and caption-gate checks.

Current state:
- Figure bases scanned: {len(figures)}
- Manifest-ready figures: {ready}
- Missing manifests: {missing}
- Export rule: no figure or table may be promoted into the VER2 manuscript
  path unless a matching `.manifest.json` exists and its caption does not
  overclaim the manifest claim tier.
- Canonical manifest fields remain owned by `common.contracts`:
  {field_line}

| Chapter | Figure base | Assets | Manifest | Claim tier | Caption check | Export status |
| --- | --- | --- | --- | --- | --- | --- |
{rows}
"""
    ).strip() + "\n"


def _render_outputs(
    records: dict[str, ArtifactRecord],
    packs: tuple[PackRecord, ...],
    figures: list[dict[str, object]],
) -> dict[Path, str]:
    status_rows = _status_rows(records)
    claim_rows = _claim_rows(records)
    topic_rows, topic_markdown = _gallery_topic_map(packs)
    manifest_fields = _field_names(ArtifactManifest)
    outputs: dict[Path, str] = {
        STATUS_JSON: _dump_json(STATUS_JSON, status_rows),
        CLAIM_JSON: _dump_json(CLAIM_JSON, claim_rows),
        TOPIC_MAP_JSON: _dump_json(TOPIC_MAP_JSON, topic_rows),
        TOPIC_MAP_MD: topic_markdown,
        VER2_GEN / "STATUS_SNAPSHOT.md": _render_status_markdown(status_rows),
        VER2_GEN / "CLAIM_LEDGER.md": _render_claim_markdown(claim_rows),
        VER2_GEN / "RESULT_PACK_INDEX.md": _render_result_pack_index(packs),
        FIGURE_ROOT / "VER2_MANIFEST_INDEX.md": _render_manifest_index(
            figures,
            manifest_fields,
        ),
        FIGURE_GEN_INDEX: _render_figure_index(packs),
        MANUSCRIPT_GEN / "ver2_titlepage_status.tex": _render_titlepage_status_tex(status_rows),
        MANUSCRIPT_GEN / "ver2_status_snapshot.tex": _render_status_snapshot_tex(status_rows),
        MANUSCRIPT_GEN / "ver2_claim_ledger.tex": _render_claim_ledger_tex(claim_rows),
        MANUSCRIPT_GEN / "ver2_artifact_export_policy.tex": _render_artifact_policy_tex(
            manifest_fields,
            figures,
        ),
        MANUSCRIPT_GEN / "ver2_tsc_scope_boundary.tex": _render_tsc_scope_boundary_tex(),
        MANUSCRIPT_GEN / "ver2_source_vs_propagation.tex": _render_source_vs_propagation_tex(),
        MANUSCRIPT_GEN / "ver2_channel_responsibility.tex": _render_channel_responsibility_tex(),
        MANUSCRIPT_GEN / "ver2_result_pack_summary.tex": _render_result_pack_summary_tex(packs),
        MANUSCRIPT_GEN / "ver2_figure_manifest_status.tex": _render_figure_manifest_status_tex(
            packs,
            figures,
        ),
        MANUSCRIPT_GEN / "ver2_validation_status.tex": _render_validation_status_tex(
            records,
            status_rows,
        ),
    }
    for record in records.values():
        outputs[REPO_ROOT / record.manifest.artifact_path] = _dump_json(
            REPO_ROOT / record.manifest.artifact_path,
            _record_manifest_payload(record),
        )
    for pack in packs:
        json_path, md_path, tex_path = _pack_file_paths(pack)
        outputs[json_path] = _dump_json(json_path, _pack_payload(pack))
        outputs[md_path] = _render_pack_markdown(pack)
        outputs[tex_path] = _render_pack_tex(pack)
    return outputs


def _write_outputs(outputs: dict[Path, str]) -> None:
    for path, content in outputs.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content.rstrip() + "\n", encoding="utf-8")


def _generated_figure_file_bytes(root: Path) -> dict[str, bytes]:
    if not root.exists():
        return {}
    payload: dict[str, bytes] = {}
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        if path.suffix == ".png" or path.name.endswith(".caption.txt") or path.name.endswith(
            ".manifest.json"
        ):
            payload[path.relative_to(root).as_posix()] = path.read_bytes()
        elif path.suffix == ".pdf":
            payload[path.relative_to(root).as_posix()] = b"present"
    return payload


def _stale_generated_figure_assets(expected_root: Path, actual_root: Path) -> list[str]:
    expected = _generated_figure_file_bytes(expected_root)
    actual = _generated_figure_file_bytes(actual_root)
    stale: list[str] = []
    for relative_path in sorted(set(expected) | set(actual)):
        if actual.get(relative_path) != expected.get(relative_path):
            actual_path = actual_root / relative_path
            try:
                stale.append(actual_path.relative_to(REPO_ROOT).as_posix())
            except ValueError:
                stale.append(actual_path.as_posix())
    return stale


def _check_outputs(
    outputs: dict[Path, str],
    *,
    expected_generated_root: Path | None = None,
) -> int:
    stale: list[str] = []
    for path, content in outputs.items():
        expected = content.rstrip() + "\n"
        actual = path.read_text(encoding="utf-8") if path.exists() else None
        if actual != expected:
            stale.append(path.relative_to(REPO_ROOT).as_posix())
    if expected_generated_root is not None:
        stale.extend(_stale_generated_figure_assets(expected_generated_root, FIGURE_GEN))
    stale = sorted(dict.fromkeys(stale))
    if stale:
        print("Out-of-date VER2 export surfaces:")
        for path in stale:
            print(f"  - {path}")
        return 1
    print("VER2 export surfaces are up to date.")
    return 0


def build_export_bundle() -> tuple[dict[str, ArtifactRecord], tuple[PackRecord, ...]]:
    records = _build_export_records()
    packs = _build_pack_records(records)
    return records, packs


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="fail if generated export surfaces are missing or stale",
    )
    args = parser.parse_args()

    records, packs = build_export_bundle()
    if args.check:
        with tempfile.TemporaryDirectory() as temp_dir:
            generated_root = Path(temp_dir)
            _generate_pack_figures(packs, figure_dir=generated_root)
            figures = _scan_figures(FIGURE_ROOT, generated_root=generated_root)
            outputs = _render_outputs(records, packs, figures)
            return _check_outputs(
                outputs,
                expected_generated_root=generated_root,
            )

    _generate_pack_figures(packs, figure_dir=FIGURE_GEN)
    figures = _scan_figures(FIGURE_ROOT)
    outputs = _render_outputs(records, packs, figures)

    _write_outputs(outputs)
    ready = sum(row["export_status"] == "manifest_ready" for row in figures)
    print(
        "Generated VER2 figure/export surfaces "
        f"({len(outputs)} files; {len(figures)} figure bases scanned; "
        f"{ready} manifest-ready figures)."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
