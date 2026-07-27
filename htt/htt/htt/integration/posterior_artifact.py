"""HTT-owned posterior/evidence artifact writer and reader for VER2."""
from __future__ import annotations

from dataclasses import asdict, dataclass
import json
import math
from numbers import Real
from pathlib import Path
from types import MappingProxyType
from typing import Any, Mapping, Sequence

from common.contracts import ArtifactManifest
from common.statistical_foundations import (
    BC1_LEGACY_PROJECTION,
    BC2_NO_REPRESENTATION_PROMOTION,
)
from htt.departure.response_overlap import ResponseOverlapAudit
from htt.infer.ver2_directional_shell import (
    DirectionalLikelihoodInputs,
    build_directional_output_manifest,
    require_directional_model_outputs_ready,
)

__all__ = [
    "HTT_DIRECTIONAL_POSTERIOR_ARTIFACT_KIND",
    "HTT_DIRECTIONAL_POSTERIOR_ARTIFACT_KIND_V1",
    "DirectionalPosteriorArtifact",
    "build_cross_check_manifest_from_directional_artifact",
    "emit_directional_posterior_artifact",
    "load_directional_posterior_artifact",
]

HTT_DIRECTIONAL_POSTERIOR_ARTIFACT_KIND = "htt_directional_posterior_summary_v2"
HTT_DIRECTIONAL_POSTERIOR_ARTIFACT_KIND_V1 = (
    "htt_directional_posterior_summary_v1"
)
_LEGACY_ALLOWED_USE = (
    "historical value reproduction",
    "diagnostic cross-check",
)
_LEGACY_FORBIDDEN_USE = (
    "posterior estimand",
    "departure distance",
    "occupancy",
    "probability",
    "evidence",
    "family identification",
)


def _require_manifest_response_overlap_provenance(
    manifest: ArtifactManifest,
    audit: ResponseOverlapAudit,
) -> None:
    stats = manifest.statistics_definitions
    expected = {
        "response_overlap_rank_ready": True,
        "response_overlap_audit_ref": audit.manifest.artifact_id,
        "response_overlap_audit_config_hash": audit.manifest.config_hash,
        "response_overlap_transfer_source": audit.transfer_source,
        "response_overlap_transfer_spec_id": audit.transfer_spec_id,
    }
    mismatches = [
        f"{key} expected {value!r} got {stats.get(key)!r}"
        for key, value in expected.items()
        if stats.get(key) != value
    ]
    input_refs = set(str(ref) for ref in manifest.input_hashes)
    required_input_refs = {
        audit.manifest.artifact_id,
        audit.manifest.config_hash,
        *audit.input_hashes,
    }
    if audit.transfer_spec_id is not None:
        required_input_refs.add(audit.transfer_spec_id)
    missing_refs = sorted(
        str(ref) for ref in required_input_refs if str(ref) not in input_refs
    )
    if manifest.production_status not in {
        "production_candidate",
        "production_validated",
    }:
        mismatches.append(
            "production_status expected production_candidate/production_validated "
            f"got {manifest.production_status!r}"
        )
    if mismatches or missing_refs:
        detail = "; ".join(mismatches)
        if missing_refs:
            detail = "; ".join(
                part
                for part in (
                    detail,
                    "missing input refs: " + ", ".join(missing_refs),
                )
                if part
            )
        raise ValueError(
            "Directional posterior manifest missing response-overlap audit "
            f"provenance: {detail}"
        )


def _interval(values: Sequence[float], *, field_name: str) -> tuple[float, float]:
    if isinstance(values, (str, bytes)):
        raise ValueError(f"{field_name} must contain exactly two numeric values")
    if len(values) != 2:
        raise ValueError(f"{field_name} must contain exactly two values")
    result = (
        _finite_float(values[0], f"{field_name}[0]"),
        _finite_float(values[1], f"{field_name}[1]"),
    )
    if result[0] > result[1]:
        raise ValueError(f"{field_name} must be ordered low-to-high")
    return result


def _finite_float(value: Any, field_name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, Real):
        raise ValueError(f"{field_name} must be a real number, not boolean")
    number = float(value)
    if not math.isfinite(number):
        raise ValueError(f"{field_name} must be finite")
    return number


def _positive_int(value: Any, field_name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ValueError(f"{field_name} must be a positive integer, not boolean")
    return value


def _float_mapping(payload: Mapping[str, Any]) -> dict[str, float]:
    if not payload:
        raise ValueError("model_evidences must not be empty")
    result: dict[str, float] = {}
    for key, value in payload.items():
        if not isinstance(key, str) or not key.strip():
            raise ValueError("model_evidences keys must be non-empty strings")
        result[key] = _finite_float(value, f"model_evidences[{key!r}]")
    return result


def _nonempty_string(value: Any, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")
    return value


def _optional_nonempty_string(value: Any, field_name: str) -> str | None:
    if value is None:
        return None
    return _nonempty_string(value, field_name)


def _require_exact_string_list(
    payload: Mapping[str, Any],
    key: str,
    *,
    expected: tuple[str, ...],
) -> None:
    value = _required_value(payload, key)
    if (
        not isinstance(value, list)
        or any(not isinstance(item, str) for item in value)
        or tuple(value) != expected
    ):
        raise ValueError(f"legacy projection {key} policy drift")


def _required_mapping(payload: Mapping[str, Any], key: str) -> Mapping[str, Any]:
    value = payload.get(key)
    if not isinstance(value, Mapping):
        raise ValueError(f"Directional posterior artifact requires mapping {key!r}")
    return value


def _required_value(payload: Mapping[str, Any], key: str) -> Any:
    if key not in payload:
        raise ValueError(f"Directional posterior artifact requires field {key!r}")
    return payload[key]


@dataclass(frozen=True)
class DirectionalPosteriorArtifact:
    """HTT evidence plus explicitly segregated legacy scalar projections."""

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
    legacy_projection_classification: str = BC1_LEGACY_PROJECTION
    representation_policy: str = BC2_NO_REPRESENTATION_PROMOTION

    def __post_init__(self) -> None:
        _nonempty_string(self.model, "DirectionalPosteriorArtifact.model")
        if isinstance(self.n_live, bool) or not isinstance(self.n_live, int):
            raise ValueError("DirectionalPosteriorArtifact.n_live must be an integer")
        if self.n_live <= 0:
            raise ValueError("DirectionalPosteriorArtifact.n_live must be positive")
        for field_name in (
            "x_median",
            "Q_median",
            "Pi_median",
            "ln_B_total",
            "F_median",
        ):
            _finite_float(getattr(self, field_name), field_name)
        for field_name in ("x_hpd68", "x_hpd95", "Q_hpd68", "Pi_hpd68", "F_hpd68"):
            _interval(getattr(self, field_name), field_name=field_name)
        object.__setattr__(
            self,
            "model_evidences",
            MappingProxyType(_float_mapping(self.model_evidences)),
        )
        if self.manifest.owner != "HTT":
            raise ValueError("DirectionalPosteriorArtifact.manifest.owner must be 'HTT'")
        _nonempty_string(
            self.posterior_ref,
            "DirectionalPosteriorArtifact.posterior_ref",
        )
        _nonempty_string(
            self.evidence_ref,
            "DirectionalPosteriorArtifact.evidence_ref",
        )
        if self.legacy_projection_classification != BC1_LEGACY_PROJECTION:
            raise ValueError("legacy projections must remain BC1_LEGACY_PROJECTION")
        if self.representation_policy != BC2_NO_REPRESENTATION_PROMOTION:
            raise ValueError(
                "legacy projections must enforce BC2_NO_REPRESENTATION_PROMOTION"
            )


def _artifact_to_payload(artifact: DirectionalPosteriorArtifact) -> dict[str, object]:
    return {
        "artifact_kind": HTT_DIRECTIONAL_POSTERIOR_ARTIFACT_KIND,
        "artifact_name": Path(artifact.manifest.artifact_path).name,
        "model": artifact.model,
        "legacy_projection_summary": {
            "classification": artifact.legacy_projection_classification,
            "representation_policy": artifact.representation_policy,
            "status": "LEGACY_REPRODUCTION",
            "allowed_use": list(_LEGACY_ALLOWED_USE),
            "forbidden_use": list(_LEGACY_FORBIDDEN_USE),
            "values": {
                "x_C": {
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
                "F": {
                    "median": float(artifact.F_median),
                    "hpd_68": list(artifact.F_hpd68),
                },
            },
        },
        "evidence_summary": {
            "lnB_total": float(artifact.ln_B_total),
            "model_evidences": dict(artifact.model_evidences),
            "n_live": int(artifact.n_live),
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

    require_directional_model_outputs_ready(directional_inputs)
    response_overlap_audit = directional_inputs.response_overlap_audit
    if response_overlap_audit is None:
        raise RuntimeError("rank audit blocks model run: response_overlap_rank_audit_missing")

    out = Path(out_path)
    resolved_manifest = manifest or build_directional_output_manifest(
        inputs=directional_inputs,
        artifact_id=f"htt.directional_evidence_summary.{model}",
        artifact_path=str(out),
        model_name=model,
        posterior_ref=posterior_ref,
        evidence_ref=evidence_ref,
        output_role="directional_evidence_with_legacy_projection",
        posterior_predictive_ref=posterior_predictive_ref,
        loocv_ref=loocv_ref,
        created_by="htt.integration.posterior_artifact.emit_directional_posterior_artifact",
        statistics_definitions={
            "artifact_kind": HTT_DIRECTIONAL_POSTERIOR_ARTIFACT_KIND,
        },
    )
    _require_manifest_response_overlap_provenance(
        resolved_manifest,
        response_overlap_audit,
    )
    artifact = DirectionalPosteriorArtifact(
        model=_nonempty_string(model, "model"),
        x_median=_finite_float(x_median, "x_median"),
        x_hpd68=_interval(x_hpd68, field_name="x_hpd68"),
        x_hpd95=_interval(x_hpd95, field_name="x_hpd95"),
        Q_median=_finite_float(Q_median, "Q_median"),
        Q_hpd68=_interval(Q_hpd68, field_name="Q_hpd68"),
        Pi_median=_finite_float(Pi_median, "Pi_median"),
        Pi_hpd68=_interval(Pi_hpd68, field_name="Pi_hpd68"),
        ln_B_total=_finite_float(ln_B_total, "ln_B_total"),
        model_evidences=_float_mapping(model_evidences),
        F_median=_finite_float(F_median, "F_median"),
        F_hpd68=_interval(F_hpd68, field_name="F_hpd68"),
        n_live=_positive_int(n_live, "n_live"),
        manifest=resolved_manifest,
        posterior_ref=_nonempty_string(posterior_ref, "posterior_ref"),
        evidence_ref=_nonempty_string(evidence_ref, "evidence_ref"),
        posterior_predictive_ref=posterior_predictive_ref,
        loocv_ref=loocv_ref,
    )
    payload = _artifact_to_payload(artifact)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    return payload


def load_directional_posterior_artifact(
    artifact_or_path: Mapping[str, Any] | str | Path,
    *,
    allow_legacy_reproduction: bool = False,
) -> DirectionalPosteriorArtifact:
    """Load a dedicated HTT-owned posterior/evidence summary artifact."""

    payload: Mapping[str, Any]
    if isinstance(artifact_or_path, Mapping):
        payload = artifact_or_path
    else:
        payload = json.loads(Path(artifact_or_path).read_text(encoding="utf-8"))
    artifact_kind = payload.get("artifact_kind")
    if artifact_kind == HTT_DIRECTIONAL_POSTERIOR_ARTIFACT_KIND_V1:
        if not allow_legacy_reproduction:
            raise ValueError(
                "v1 directional posterior artifacts are legacy reproduction "
                "only; pass allow_legacy_reproduction=True explicitly"
            )
        return _load_v1_directional_posterior_artifact(payload)
    if artifact_kind != HTT_DIRECTIONAL_POSTERIOR_ARTIFACT_KIND:
        raise ValueError(
            "Expected HTT directional posterior artifact kind "
            f"{HTT_DIRECTIONAL_POSTERIOR_ARTIFACT_KIND!r}"
        )
    manifest_payload = _required_mapping(payload, "manifest")
    projection = _required_mapping(payload, "legacy_projection_summary")
    if _required_value(projection, "classification") != BC1_LEGACY_PROJECTION:
        raise ValueError("legacy projection classification drift")
    if _required_value(projection, "representation_policy") != (
        BC2_NO_REPRESENTATION_PROMOTION
    ):
        raise ValueError("legacy projection representation policy drift")
    if _required_value(projection, "status") != "LEGACY_REPRODUCTION":
        raise ValueError("legacy projection status must be LEGACY_REPRODUCTION")
    _require_exact_string_list(
        projection,
        "allowed_use",
        expected=_LEGACY_ALLOWED_USE,
    )
    _require_exact_string_list(
        projection,
        "forbidden_use",
        expected=_LEGACY_FORBIDDEN_USE,
    )
    values = _required_mapping(projection, "values")
    evidence_summary = _required_mapping(payload, "evidence_summary")
    refs = _required_mapping(payload, "refs")
    x_summary = _required_mapping(values, "x_C")
    q_summary = _required_mapping(values, "Q")
    pi_summary = _required_mapping(values, "Pi")
    f_summary = _required_mapping(values, "F")
    return DirectionalPosteriorArtifact(
        model=_nonempty_string(_required_value(payload, "model"), "model"),
        x_median=_finite_float(
            _required_value(x_summary, "median"),
            "x_C.median",
        ),
        x_hpd68=_interval(
            _required_value(x_summary, "hpd_68"), field_name="x_C.hpd_68"
        ),
        x_hpd95=_interval(
            _required_value(x_summary, "hpd_95"), field_name="x_C.hpd_95"
        ),
        Q_median=_finite_float(
            _required_value(q_summary, "median"),
            "Q.median",
        ),
        Q_hpd68=_interval(
            _required_value(q_summary, "hpd_68"), field_name="Q.hpd_68"
        ),
        Pi_median=_finite_float(
            _required_value(pi_summary, "median"),
            "Pi.median",
        ),
        Pi_hpd68=_interval(
            _required_value(pi_summary, "hpd_68"), field_name="Pi.hpd_68"
        ),
        ln_B_total=_finite_float(
            _required_value(evidence_summary, "lnB_total"),
            "lnB_total",
        ),
        model_evidences=_float_mapping(
            _required_mapping(evidence_summary, "model_evidences")
        ),
        F_median=_finite_float(
            _required_value(f_summary, "median"),
            "F.median",
        ),
        F_hpd68=_interval(
            _required_value(f_summary, "hpd_68"), field_name="F.hpd_68"
        ),
        n_live=_positive_int(
            _required_value(evidence_summary, "n_live"), "n_live"
        ),
        manifest=ArtifactManifest(**dict(manifest_payload)),
        posterior_ref=_nonempty_string(
            _required_value(refs, "posterior_ref"),
            "posterior_ref",
        ),
        evidence_ref=_nonempty_string(
            _required_value(refs, "evidence_ref"),
            "evidence_ref",
        ),
        posterior_predictive_ref=(
            _optional_nonempty_string(
                refs.get("posterior_predictive_ref"),
                "posterior_predictive_ref",
            )
        ),
        loocv_ref=(
            _optional_nonempty_string(
                refs.get("loocv_ref"),
                "loocv_ref",
            )
        ),
        legacy_projection_classification=str(projection["classification"]),
        representation_policy=str(projection["representation_policy"]),
    )


def _load_v1_directional_posterior_artifact(
    payload: Mapping[str, Any],
) -> DirectionalPosteriorArtifact:
    """Load frozen v1 bytes only through the explicit legacy switch."""

    manifest_payload = _required_mapping(payload, "manifest")
    posterior_summary = _required_mapping(payload, "posterior_summary")
    evidence_summary = _required_mapping(payload, "evidence_summary")
    filling_summary = _required_mapping(payload, "filling_fraction_summary")
    refs = _required_mapping(payload, "refs")
    x_summary = _required_mapping(posterior_summary, "x")
    q_summary = _required_mapping(posterior_summary, "Q")
    pi_summary = _required_mapping(posterior_summary, "Pi")
    return DirectionalPosteriorArtifact(
        model=_nonempty_string(_required_value(payload, "model"), "model"),
        x_median=_finite_float(
            _required_value(x_summary, "median"),
            "x.median",
        ),
        x_hpd68=_interval(
            _required_value(x_summary, "hpd_68"), field_name="x.hpd_68"
        ),
        x_hpd95=_interval(
            _required_value(x_summary, "hpd_95"), field_name="x.hpd_95"
        ),
        Q_median=_finite_float(
            _required_value(q_summary, "median"),
            "Q.median",
        ),
        Q_hpd68=_interval(
            _required_value(q_summary, "hpd_68"), field_name="Q.hpd_68"
        ),
        Pi_median=_finite_float(
            _required_value(pi_summary, "median"),
            "Pi.median",
        ),
        Pi_hpd68=_interval(
            _required_value(pi_summary, "hpd_68"), field_name="Pi.hpd_68"
        ),
        ln_B_total=_finite_float(
            _required_value(evidence_summary, "lnB_total"),
            "lnB_total",
        ),
        model_evidences=_float_mapping(
            _required_mapping(evidence_summary, "model_evidences")
        ),
        F_median=_finite_float(
            _required_value(filling_summary, "median"),
            "F.median",
        ),
        F_hpd68=_interval(
            _required_value(filling_summary, "hpd_68"), field_name="F.hpd_68"
        ),
        n_live=_positive_int(
            _required_value(evidence_summary, "n_live"), "n_live"
        ),
        manifest=ArtifactManifest(**dict(manifest_payload)),
        posterior_ref=_nonempty_string(
            _required_value(refs, "posterior_ref"),
            "posterior_ref",
        ),
        evidence_ref=_nonempty_string(
            _required_value(refs, "evidence_ref"),
            "evidence_ref",
        ),
        posterior_predictive_ref=(
            _optional_nonempty_string(
                refs.get("posterior_predictive_ref"),
                "posterior_predictive_ref",
            )
        ),
        loocv_ref=(
            _optional_nonempty_string(
                refs.get("loocv_ref"),
                "loocv_ref",
            )
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
            "source_claim_tier": base_manifest.claim_tier.value,
            "source_production_status": base_manifest.production_status,
            "legacy_projection_classification": BC1_LEGACY_PROJECTION,
            "representation_policy": BC2_NO_REPRESENTATION_PROMOTION,
            "htt_evidence_exported_to_mio": False,
        }
    )
    return ArtifactManifest(
        artifact_id=artifact_id,
        artifact_path=artifact_path,
        owner="HTT",
        implementation_scope="htt",
        claim_tier="diagnostic_only",
        production_status="diagnostic_only",
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
