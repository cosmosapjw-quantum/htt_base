"""HTT-owned posterior/evidence artifact writer and reader for VER2."""
from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from pathlib import Path
from typing import Any, Mapping, Sequence

from common.contracts import ArtifactManifest
from htt.infer.ver2_directional_shell import (
    DirectionalLikelihoodInputs,
    build_directional_output_manifest,
)

__all__ = [
    "HTT_DIRECTIONAL_POSTERIOR_ARTIFACT_KIND",
    "DirectionalPosteriorArtifact",
    "build_cross_check_manifest_from_directional_artifact",
    "emit_directional_posterior_artifact",
    "load_directional_posterior_artifact",
]

HTT_DIRECTIONAL_POSTERIOR_ARTIFACT_KIND = "htt_directional_posterior_summary_v1"


def _interval(values: Sequence[float], *, field_name: str) -> tuple[float, float]:
    if len(values) != 2:
        raise ValueError(f"{field_name} must contain exactly two values")
    return (float(values[0]), float(values[1]))


def _float_mapping(payload: Mapping[str, Any]) -> dict[str, float]:
    return {str(key): float(value) for key, value in payload.items()}


@dataclass(frozen=True)
class DirectionalPosteriorArtifact:
    """Typed HTT-owned posterior/evidence summary artifact payload."""

    model: str
    x_median: float
    x_hpd68: tuple[float, float]
    x_hpd95: tuple[float, float]
    Q_median: float
    Q_hpd68: tuple[float, float]
    Pi_median: float
    Pi_hpd68: tuple[float, float]
    ln_B_total: float
    model_evidences: Mapping[str, float]
    F_median: float
    F_hpd68: tuple[float, float]
    n_live: int
    manifest: ArtifactManifest
    posterior_ref: str
    evidence_ref: str
    posterior_predictive_ref: str | None = None
    loocv_ref: str | None = None

    def __post_init__(self) -> None:
        if not self.model:
            raise ValueError("DirectionalPosteriorArtifact.model must be non-empty")
        if self.n_live <= 0:
            raise ValueError("DirectionalPosteriorArtifact.n_live must be positive")
        if self.manifest.owner != "HTT":
            raise ValueError("DirectionalPosteriorArtifact.manifest.owner must be 'HTT'")
        if not self.posterior_ref:
            raise ValueError(
                "DirectionalPosteriorArtifact.posterior_ref must be non-empty"
            )
        if not self.evidence_ref:
            raise ValueError(
                "DirectionalPosteriorArtifact.evidence_ref must be non-empty"
            )


def _artifact_to_payload(artifact: DirectionalPosteriorArtifact) -> dict[str, object]:
    return {
        "artifact_kind": HTT_DIRECTIONAL_POSTERIOR_ARTIFACT_KIND,
        "artifact_name": Path(artifact.manifest.artifact_path).name,
        "model": artifact.model,
        "posterior_summary": {
            "x": {
                "median": float(artifact.x_median),
                "hpd_68": list(artifact.x_hpd68),
                "hpd_95": list(artifact.x_hpd95),
            },
            "Q": {
                "median": float(artifact.Q_median),
                "hpd_68": list(artifact.Q_hpd68),
            },
            "Pi": {
                "median": float(artifact.Pi_median),
                "hpd_68": list(artifact.Pi_hpd68),
            },
        },
        "evidence_summary": {
            "lnB_total": float(artifact.ln_B_total),
            "model_evidences": dict(artifact.model_evidences),
            "n_live": int(artifact.n_live),
        },
        "filling_fraction_summary": {
            "median": float(artifact.F_median),
            "hpd_68": list(artifact.F_hpd68),
        },
        "refs": {
            "posterior_ref": artifact.posterior_ref,
            "evidence_ref": artifact.evidence_ref,
            "posterior_predictive_ref": artifact.posterior_predictive_ref,
            "loocv_ref": artifact.loocv_ref,
        },
        "manifest": asdict(artifact.manifest),
    }


def emit_directional_posterior_artifact(
    out_path: str | Path,
    *,
    model: str,
    x_median: float,
    x_hpd68: Sequence[float],
    x_hpd95: Sequence[float],
    Q_median: float,
    Q_hpd68: Sequence[float],
    Pi_median: float,
    Pi_hpd68: Sequence[float],
    ln_B_total: float,
    model_evidences: Mapping[str, float],
    F_median: float,
    F_hpd68: Sequence[float],
    n_live: int,
    directional_inputs: DirectionalLikelihoodInputs,
    posterior_ref: str,
    evidence_ref: str,
    manifest: ArtifactManifest | None = None,
    posterior_predictive_ref: str | None = None,
    loocv_ref: str | None = None,
) -> dict[str, object]:
    """Write a dedicated HTT-owned posterior/evidence summary artifact."""

    out = Path(out_path)
    resolved_manifest = manifest or build_directional_output_manifest(
        inputs=directional_inputs,
        artifact_id=f"htt.directional_posterior_summary.{model}",
        artifact_path=str(out),
        model_name=model,
        posterior_ref=posterior_ref,
        evidence_ref=evidence_ref,
        output_role="directional_posterior_summary",
        posterior_predictive_ref=posterior_predictive_ref,
        loocv_ref=loocv_ref,
        created_by="htt.integration.posterior_artifact.emit_directional_posterior_artifact",
        statistics_definitions={
            "artifact_kind": HTT_DIRECTIONAL_POSTERIOR_ARTIFACT_KIND,
        },
    )
    artifact = DirectionalPosteriorArtifact(
        model=str(model),
        x_median=float(x_median),
        x_hpd68=_interval(x_hpd68, field_name="x_hpd68"),
        x_hpd95=_interval(x_hpd95, field_name="x_hpd95"),
        Q_median=float(Q_median),
        Q_hpd68=_interval(Q_hpd68, field_name="Q_hpd68"),
        Pi_median=float(Pi_median),
        Pi_hpd68=_interval(Pi_hpd68, field_name="Pi_hpd68"),
        ln_B_total=float(ln_B_total),
        model_evidences=_float_mapping(model_evidences),
        F_median=float(F_median),
        F_hpd68=_interval(F_hpd68, field_name="F_hpd68"),
        n_live=int(n_live),
        manifest=resolved_manifest,
        posterior_ref=str(posterior_ref),
        evidence_ref=str(evidence_ref),
        posterior_predictive_ref=posterior_predictive_ref,
        loocv_ref=loocv_ref,
    )
    payload = _artifact_to_payload(artifact)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    return payload


def load_directional_posterior_artifact(
    artifact_or_path: Mapping[str, Any] | str | Path,
) -> DirectionalPosteriorArtifact:
    """Load a dedicated HTT-owned posterior/evidence summary artifact."""

    payload: Mapping[str, Any]
    if isinstance(artifact_or_path, Mapping):
        payload = artifact_or_path
    else:
        payload = json.loads(Path(artifact_or_path).read_text(encoding="utf-8"))
    if payload.get("artifact_kind") != HTT_DIRECTIONAL_POSTERIOR_ARTIFACT_KIND:
        raise ValueError(
            "Expected HTT directional posterior artifact kind "
            f"{HTT_DIRECTIONAL_POSTERIOR_ARTIFACT_KIND!r}"
        )
    manifest_payload = payload.get("manifest")
    if not isinstance(manifest_payload, Mapping):
        raise ValueError("Directional posterior artifact requires a manifest payload")
    posterior_summary = payload.get("posterior_summary", {})
    evidence_summary = payload.get("evidence_summary", {})
    filling_summary = payload.get("filling_fraction_summary", {})
    refs = payload.get("refs", {})
    x_summary = posterior_summary.get("x", {})
    q_summary = posterior_summary.get("Q", {})
    pi_summary = posterior_summary.get("Pi", {})
    return DirectionalPosteriorArtifact(
        model=str(payload.get("model", "")),
        x_median=float(x_summary.get("median", 0.0)),
        x_hpd68=_interval(x_summary.get("hpd_68", (0.0, 0.0)), field_name="x.hpd_68"),
        x_hpd95=_interval(x_summary.get("hpd_95", (0.0, 0.0)), field_name="x.hpd_95"),
        Q_median=float(q_summary.get("median", 0.0)),
        Q_hpd68=_interval(q_summary.get("hpd_68", (0.0, 0.0)), field_name="Q.hpd_68"),
        Pi_median=float(pi_summary.get("median", 0.0)),
        Pi_hpd68=_interval(pi_summary.get("hpd_68", (0.0, 0.0)), field_name="Pi.hpd_68"),
        ln_B_total=float(evidence_summary.get("lnB_total", 0.0)),
        model_evidences=_float_mapping(evidence_summary.get("model_evidences", {})),
        F_median=float(filling_summary.get("median", 0.0)),
        F_hpd68=_interval(filling_summary.get("hpd_68", (0.0, 0.0)), field_name="F.hpd_68"),
        n_live=int(evidence_summary.get("n_live", 0)),
        manifest=ArtifactManifest(**dict(manifest_payload)),
        posterior_ref=str(refs.get("posterior_ref", "")),
        evidence_ref=str(refs.get("evidence_ref", "")),
        posterior_predictive_ref=(
            None
            if refs.get("posterior_predictive_ref") is None
            else str(refs.get("posterior_predictive_ref"))
        ),
        loocv_ref=(
            None if refs.get("loocv_ref") is None else str(refs.get("loocv_ref"))
        ),
    )


def build_cross_check_manifest_from_directional_artifact(
    artifact: DirectionalPosteriorArtifact,
    *,
    artifact_id: str,
    artifact_path: str,
    created_by: str = (
        "htt.integration.posterior_artifact."
        "build_cross_check_manifest_from_directional_artifact"
    ),
) -> ArtifactManifest:
    """Derive an HTT-owned cross-check manifest from a dedicated HTT artifact."""

    base_manifest = artifact.manifest
    input_hashes = list(base_manifest.input_hashes)
    for ref in (
        base_manifest.artifact_id,
        artifact.posterior_ref,
        artifact.evidence_ref,
        artifact.posterior_predictive_ref,
        artifact.loocv_ref,
    ):
        if ref is None:
            continue
        text = str(ref)
        if text and text not in input_hashes:
            input_hashes.append(text)
    caveats = list(base_manifest.caveats)
    if "mio_cross_check_only_export" not in caveats:
        caveats.append("mio_cross_check_only_export")
    stats = dict(base_manifest.statistics_definitions)
    stats.update(
        {
            "surface": "posterior_export_bundle",
            "model_name": artifact.model,
            "posterior_ref": artifact.posterior_ref,
            "evidence_ref": artifact.evidence_ref,
            "posterior_predictive_ref": artifact.posterior_predictive_ref,
            "loocv_ref": artifact.loocv_ref,
            "cross_check_only": True,
            "source_artifact_id": base_manifest.artifact_id,
            "source_surface": base_manifest.statistics_definitions.get("surface"),
        }
    )
    return ArtifactManifest(
        artifact_id=artifact_id,
        artifact_path=artifact_path,
        owner="HTT",
        implementation_scope="htt",
        claim_tier=base_manifest.claim_tier,
        production_status=base_manifest.production_status,
        created_by=created_by,
        git_commit=base_manifest.git_commit,
        config_hash=base_manifest.config_hash,
        input_hashes=input_hashes,
        code_version=base_manifest.code_version,
        schema_version=base_manifest.schema_version,
        caveats=caveats,
        required_gates=list(base_manifest.required_gates),
        passed_gates=list(base_manifest.passed_gates),
        failed_gates=list(base_manifest.failed_gates),
        statistics_definitions=stats,
    )
