"""Shared loaders for VER2 preliminary-result packs and generated artifacts."""
from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
import json
from pathlib import Path
from typing import Any, Mapping

from common.contracts import (
    ArtifactManifest,
    AtlasEntryLite,
    DiscriminationMatrix,
    ObservableVector,
    SkySupport,
    TscAdequacyOverlay,
    TscChannelAdequacyBudget,
    TscDomainReport,
    TscResidualReport,
    TscSourceBridgeReport,
    TscUpgradeRecommendation,
)
from workspace.contracts.mio_certificate import MioCertificate


REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_GENERATED_ROOT = REPO_ROOT / "docs" / "ver2_upgrade" / "generated"
DEFAULT_ARTIFACT_ROOT = DEFAULT_GENERATED_ROOT / "artifacts"
_PACK_STEMS = {
    "A": "result_pack_A_scalar_to_morphology.json",
    "B": "result_pack_B_local_global.json",
    "C": "result_pack_C_departure_cards.json",
    "D": "result_pack_D_mio_certificates.json",
    "E": "result_pack_E_equivalence_classes.json",
}

OBSERVABLE_VECTOR_ARTIFACT_ID = "bass.ver2.export.solver_core_output_tier_b.observable_vector"
ATLAS_ENTRY_LITE_ARTIFACT_ID = "bass.ver2.export.solver_core_output_tier_b.atlas_lite"
DISCRIMINATION_MATRIX_ARTIFACT_ID = "htt.ver2.export.discrimination_matrix"
TSC_OVERLAY_ARTIFACT_ID = "tsc.ver2.export.overlay"
MIO_CERTIFICATE_ARTIFACT_ID = "mio.predictive_residuals.certificate"
REPRESENTATIVE_FAMILY_SWEEP_ARTIFACT_ID = "bass.ver2.export.representative_family_sweep"


@dataclass(frozen=True)
class PreliminaryPackArtifactRef:
    artifact_id: str
    title: str
    owner: str
    claim_tier: str
    production_status: str
    evidence_refs: tuple[str, ...]
    summary: str


@dataclass(frozen=True)
class PreliminaryResultPack:
    pack_id: str
    title: str
    topic: str
    figure_base: str
    claim_tier: str
    production_status: str
    caveats: tuple[str, ...]
    summary_lines: tuple[str, ...]
    artifacts: tuple[PreliminaryPackArtifactRef, ...]

    def artifact_ids(self) -> tuple[str, ...]:
        return tuple(artifact.artifact_id for artifact in self.artifacts)


@dataclass(frozen=True)
class ExportedArtifactEnvelope:
    title: str
    topic: str
    summary: str
    allowed_claims: tuple[str, ...]
    forbidden_claims: tuple[str, ...]
    evidence_refs: tuple[str, ...]
    notes: tuple[str, ...]
    manifest: ArtifactManifest
    payload: Mapping[str, Any]


def _resolve_generated_root(generated_root: str | Path | None) -> Path:
    return Path(generated_root) if generated_root is not None else DEFAULT_GENERATED_ROOT


def _load_json(path: Path) -> Mapping[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _manifest(raw: Mapping[str, Any]) -> ArtifactManifest:
    return ArtifactManifest(**dict(raw))


def _artifact_root(generated_root: Path) -> Path:
    return generated_root / "artifacts"


@lru_cache(maxsize=None)
def _artifact_index(generated_root_str: str) -> dict[str, Path]:
    root = Path(generated_root_str) / "artifacts"
    index: dict[str, Path] = {}
    for path in sorted(root.glob("*.json")):
        payload = _load_json(path)
        manifest = payload.get("manifest")
        if isinstance(manifest, Mapping) and "artifact_id" in manifest:
            index[str(manifest["artifact_id"])] = path
    return index


def _artifact_path(
    artifact_id_or_path: str | Path,
    *,
    generated_root: Path,
) -> Path:
    path = Path(artifact_id_or_path)
    if path.exists():
        return path
    if path.suffix == ".json":
        candidate = _artifact_root(generated_root) / path.name
        if candidate.exists():
            return candidate
    index = _artifact_index(str(generated_root))
    if str(artifact_id_or_path) in index:
        return index[str(artifact_id_or_path)]
    raise FileNotFoundError(
        f"Could not resolve generated artifact {artifact_id_or_path!r} under {generated_root}"
    )


def _pack_path(
    pack_id_or_path: str | Path,
    *,
    generated_root: Path,
) -> Path:
    if isinstance(pack_id_or_path, Path) and pack_id_or_path.exists():
        return pack_id_or_path
    path = Path(pack_id_or_path)
    if path.exists():
        return path
    key = str(pack_id_or_path)
    if key in _PACK_STEMS:
        return generated_root / _PACK_STEMS[key]
    raise FileNotFoundError(
        f"Could not resolve preliminary result pack {pack_id_or_path!r} under {generated_root}"
    )


def load_preliminary_result_pack(
    pack_id_or_path: str | Path,
    *,
    generated_root: str | Path | None = None,
) -> PreliminaryResultPack:
    root = _resolve_generated_root(generated_root)
    payload = _load_json(_pack_path(pack_id_or_path, generated_root=root))
    return PreliminaryResultPack(
        pack_id=str(payload["pack_id"]),
        title=str(payload["title"]),
        topic=str(payload["topic"]),
        figure_base=str(payload["figure_base"]),
        claim_tier=str(payload["claim_tier"]),
        production_status=str(payload["production_status"]),
        caveats=tuple(payload.get("caveats", ())),
        summary_lines=tuple(payload.get("summary_lines", ())),
        artifacts=tuple(
            PreliminaryPackArtifactRef(
                artifact_id=str(item["artifact_id"]),
                title=str(item["title"]),
                owner=str(item["owner"]),
                claim_tier=str(item["claim_tier"]),
                production_status=str(item["production_status"]),
                evidence_refs=tuple(item.get("evidence_refs", ())),
                summary=str(item["summary"]),
            )
            for item in payload.get("artifacts", ())
        ),
    )


def load_exported_artifact(
    artifact_id_or_path: str | Path,
    *,
    generated_root: str | Path | None = None,
) -> ExportedArtifactEnvelope:
    root = _resolve_generated_root(generated_root)
    payload = _load_json(_artifact_path(artifact_id_or_path, generated_root=root))
    return ExportedArtifactEnvelope(
        title=str(payload["title"]),
        topic=str(payload["topic"]),
        summary=str(payload["summary"]),
        allowed_claims=tuple(payload.get("allowed_claims", ())),
        forbidden_claims=tuple(payload.get("forbidden_claims", ())),
        evidence_refs=tuple(payload.get("evidence_refs", ())),
        notes=tuple(payload.get("notes", ())),
        manifest=_manifest(payload["manifest"]),
        payload=dict(payload["payload"]),
    )


def load_exported_observable_vector(
    *,
    artifact_id_or_path: str | Path = OBSERVABLE_VECTOR_ARTIFACT_ID,
    generated_root: str | Path | None = None,
) -> ObservableVector:
    envelope = load_exported_artifact(
        artifact_id_or_path,
        generated_root=generated_root,
    )
    payload = envelope.payload
    statistics = dict(envelope.manifest.statistics_definitions)
    sky_support_payload = dict(statistics.get("sky_support", {}))
    return ObservableVector(
        ell_max=int(payload["ell_max"]),
        channels=tuple(payload["channels"]),
        cl=dict(payload.get("cl", {})),
        alm_features=dict(
            payload.get(
                "alm_features",
                {
                    "generated_summary_only": True,
                    "unique_index_count": int(payload.get("unique_index_count", 0)),
                    "null_proxy_status": payload.get("null_proxy_status"),
                },
            )
        ),
        biposh=dict(payload["biposh"]) if payload.get("biposh") is not None else None,
        template_fit=dict(payload["template_fit"]) if payload.get("template_fit") is not None else None,
        covariance_features=(
            dict(payload["covariance_features"])
            if payload.get("covariance_features") is not None
            else None
        ),
        scan_volume=dict(
            payload.get(
                "scan_volume",
                {
                    "selection_mode": sky_support_payload.get("selection_mode", "unknown"),
                    "scan_volume_hash": sky_support_payload.get("scan_volume_hash", "unknown"),
                    "generated_summary_only": True,
                },
            )
        ),
        sky_support=SkySupport(**sky_support_payload),
        manifest=_manifest(payload["manifest"]),
    )


def load_exported_atlas_entry_lite(
    *,
    artifact_id_or_path: str | Path = ATLAS_ENTRY_LITE_ARTIFACT_ID,
    generated_root: str | Path | None = None,
) -> AtlasEntryLite:
    envelope = load_exported_artifact(
        artifact_id_or_path,
        generated_root=generated_root,
    )
    payload = envelope.payload
    input_hashes = tuple(envelope.manifest.input_hashes)
    solver_output_ref = next(
        (
            item
            for item in input_hashes
            if item.startswith("bass.ver2.export.solver_core_output")
        ),
        "generated_summary_only",
    )
    observable_vector_ref = next(
        (
            item
            for item in input_hashes
            if item.endswith(".observable_vector")
        ),
        OBSERVABLE_VECTOR_ARTIFACT_ID,
    )
    return AtlasEntryLite(
        atlas_id=str(payload.get("atlas_id", envelope.manifest.artifact_id)),
        theory_family=str(payload["theory_family"]),
        geometry_params=dict(payload.get("geometry_params", {})),
        kinematic_params=dict(payload.get("kinematic_params", {})),
        tilt_params=dict(payload.get("tilt_params", {})),
        solver_output_ref=str(payload.get("solver_output_ref", solver_output_ref)),
        observable_vector_ref=str(
            payload.get("observable_vector_ref", observable_vector_ref)
        ),
        response_blocks=dict(payload["response_blocks"]),
        validity_domain=dict(payload["validity_domain"]),
        interpolation_status=str(
            payload.get("interpolation_status", "generated_summary_only")
        ),
        manifest=_manifest(payload["manifest"]),
    )


def load_exported_discrimination_matrix(
    *,
    artifact_id_or_path: str | Path = DISCRIMINATION_MATRIX_ARTIFACT_ID,
    generated_root: str | Path | None = None,
) -> DiscriminationMatrix:
    envelope = load_exported_artifact(
        artifact_id_or_path,
        generated_root=generated_root,
    )
    payload = envelope.payload
    return DiscriminationMatrix(
        hypotheses=tuple(payload["hypotheses"]),
        overlap_matrix=payload["overlap_matrix"],
        response_norms=dict(payload.get("response_norms", {})),
        degeneracy_flags=dict(payload.get("degeneracy_flags", {})),
        recommended_next_observable=dict(payload["recommended_next_observable"]),
        claim_tier_by_pair=dict(payload["claim_tier_by_pair"]),
        manifest=_manifest(payload["manifest"]),
    )


def load_exported_tsc_overlay(
    *,
    artifact_id_or_path: str | Path = TSC_OVERLAY_ARTIFACT_ID,
    generated_root: str | Path | None = None,
) -> TscAdequacyOverlay:
    envelope = load_exported_artifact(
        artifact_id_or_path,
        generated_root=generated_root,
    )
    payload = envelope.payload
    source_payload = payload.get("source_bridge_report")
    source_bridge = (
        TscSourceBridgeReport(
            **{
                key: value
                for key, value in dict(source_payload).items()
                if key != "manifest"
            },
            manifest=_manifest(source_payload["manifest"]),
        )
        if isinstance(source_payload, Mapping)
        else None
    )
    return TscAdequacyOverlay(
        domain_report=TscDomainReport(
            **{
                key: value
                for key, value in dict(payload["domain_report"]).items()
                if key != "manifest"
            },
            manifest=_manifest(payload["domain_report"]["manifest"]),
        ),
        residual_report=TscResidualReport(
            **{
                key: value
                for key, value in dict(payload["residual_report"]).items()
                if key != "manifest"
            },
            manifest=_manifest(payload["residual_report"]["manifest"]),
        ),
        source_bridge_report=source_bridge,
        channel_budgets=tuple(
            TscChannelAdequacyBudget(
                **{key: value for key, value in dict(item).items() if key != "manifest"},
                manifest=_manifest(item["manifest"]),
            )
            for item in payload["channel_budgets"]
        ),
        upgrade_recommendation=TscUpgradeRecommendation(
            **{
                key: value
                for key, value in dict(payload["upgrade_recommendation"]).items()
                if key != "manifest"
            },
            manifest=_manifest(payload["upgrade_recommendation"]["manifest"]),
        ),
        no_overclaim_flags=dict(payload["no_overclaim_flags"]),
        quarantine_reasons=tuple(payload["quarantine_reasons"]),
        public_caveat_snippet=str(payload["public_caveat_snippet"]),
        manifest=_manifest(payload["manifest"]),
    )


def load_exported_mio_certificate(
    *,
    artifact_id_or_path: str | Path = MIO_CERTIFICATE_ARTIFACT_ID,
    generated_root: str | Path | None = None,
) -> MioCertificate:
    envelope = load_exported_artifact(
        artifact_id_or_path,
        generated_root=generated_root,
    )
    payload = envelope.payload
    return MioCertificate(
        report_type=str(payload["report_type"]),
        probe_name=str(payload["probe_name"]),
        channel=str(payload["channel"]),
        departure_variables=dict(payload["departure_variables"]),
        adequacy_indicators=dict(payload["adequacy_indicators"]),
        consistency_metrics=dict(payload["consistency_metrics"]),
        domain_caveats=list(payload["domain_caveats"]),
        channel_caveats=list(payload["channel_caveats"]),
        reduction_status=str(payload["reduction_status"]),
        generated_by=str(payload["generated_by"]),
        git_commit=str(payload["git_commit"]),
        config_hash=str(payload["config_hash"]),
        input_data_hashes=list(payload["input_data_hashes"]),
        manifest=_manifest(payload["manifest"]) if payload.get("manifest") is not None else None,
        tsc_overlay_ref=str(payload["tsc_overlay_ref"]) if payload.get("tsc_overlay_ref") is not None else None,
        htt_cross_check_suggested=(
            dict(payload["htt_cross_check_suggested"])
            if payload.get("htt_cross_check_suggested") is not None
            else None
        ),
    )


__all__ = [
    "ATLAS_ENTRY_LITE_ARTIFACT_ID",
    "DEFAULT_GENERATED_ROOT",
    "DISCRIMINATION_MATRIX_ARTIFACT_ID",
    "ExportedArtifactEnvelope",
    "MIO_CERTIFICATE_ARTIFACT_ID",
    "OBSERVABLE_VECTOR_ARTIFACT_ID",
    "PreliminaryPackArtifactRef",
    "PreliminaryResultPack",
    "REPRESENTATIVE_FAMILY_SWEEP_ARTIFACT_ID",
    "TSC_OVERLAY_ARTIFACT_ID",
    "load_exported_artifact",
    "load_exported_atlas_entry_lite",
    "load_exported_discrimination_matrix",
    "load_exported_mio_certificate",
    "load_exported_observable_vector",
    "load_exported_tsc_overlay",
    "load_preliminary_result_pack",
]
