"""HTT → MIO integration with an evidence firewall.

The active adapter exports only a typed ``LegacyProjectionReport`` for
diagnostic comparison.  HTT posterior/evidence quantities remain HTT-owned.
The old ``PosteriorExportBundle`` path is retained solely behind an explicit
``legacy_reproduction=True`` switch so frozen historical bytes remain
replayable without becoming an active API.
"""
from __future__ import annotations

import json
from pathlib import Path
import warnings
from typing import Any, Mapping

from common.contracts import ArtifactManifest
from common.statistical_foundations import (
    DiagnosticScalarReport,
    LegacyProjectionReport,
    ScalarRange,
)
from htt.integration.posterior_artifact import (
    HTT_DIRECTIONAL_POSTERIOR_ARTIFACT_KIND,
    HTT_DIRECTIONAL_POSTERIOR_ARTIFACT_KIND_V1,
    DirectionalPosteriorArtifact,
    build_cross_check_manifest_from_directional_artifact,
    load_directional_posterior_artifact,
)
from htt.infer.ver2_directional_shell import (
    DirectionalLikelihoodInputs,
    build_directional_output_manifest,
    require_directional_model_outputs_ready,
)
from workspace.contracts.htt_to_mio import (
    MioCrossCheckExport,
    PosteriorExportBundle,
)

__all__ = ["build_mio_cross_check_export", "build_posterior_bundle"]


def _default_results_path() -> Path:
    return (
        Path(__file__).resolve().parent.parent.parent.parent
        / "workspace"
        / "results"
        / "integrated_pipeline_results.json"
    )


def _required_mapping(payload: Mapping[str, Any], key: str) -> Mapping[str, Any]:
    value = payload.get(key)
    if not isinstance(value, Mapping):
        raise ValueError(f"legacy results require mapping {key!r}")
    return value


def _required_path(payload: Mapping[str, Any], *keys: str) -> Any:
    current: Any = payload
    traversed: list[str] = []
    for key in keys:
        traversed.append(key)
        if not isinstance(current, Mapping) or key not in current:
            raise ValueError(
                "legacy results require field " + "/".join(traversed)
            )
        current = current[key]
    return current


def _required_alias(
    payload: Mapping[str, Any],
    *,
    field_name: str,
    aliases: tuple[str, ...],
) -> Any:
    present = tuple(key for key in aliases if key in payload)
    if not present:
        raise ValueError(
            f"legacy results require field {field_name} "
            f"(accepted spellings: {', '.join(aliases)})"
        )
    if len(present) > 1:
        values = tuple(payload[key] for key in present)
        if any(value != values[0] for value in values[1:]):
            raise ValueError(
                f"legacy results contain conflicting aliases for {field_name}"
            )
    return payload[present[0]]


def _pair(value: Any, name: str) -> tuple[float, float]:
    if isinstance(value, (str, bytes)) or not hasattr(value, "__len__"):
        raise ValueError(f"{name} must contain exactly two values")
    if len(value) != 2:
        raise ValueError(f"{name} must contain exactly two values")
    return (float(value[0]), float(value[1]))


def _diagnostic_report(
    name: str,
    interval: tuple[float, float],
    *,
    bin_label: str | None = None,
) -> DiagnosticScalarReport:
    metadata = ()
    if bin_label is not None:
        metadata = (("summary_bin", bin_label),)
    return DiagnosticScalarReport(
        name=name,
        value_range=ScalarRange(*interval),
        status="LEGACY_REPRODUCTION",
        null_calibration="historical HTT summary; no active MIO calibration",
        bin_metadata=metadata,
    )


def _legacy_projection_from_artifact(
    artifact: DirectionalPosteriorArtifact,
) -> LegacyProjectionReport:
    return LegacyProjectionReport(
        x_C=_diagnostic_report("x_C", artifact.x_hpd68),
        Q=_diagnostic_report("Q", artifact.Q_hpd68, bin_label="hpd_68"),
        F=_diagnostic_report("F", artifact.F_hpd68, bin_label="hpd_68"),
        Pi=_diagnostic_report("Pi", artifact.Pi_hpd68, bin_label="hpd_68"),
    )


def build_mio_cross_check_export(
    results_path: str | Path,
    *,
    manifest: ArtifactManifest | None = None,
) -> MioCrossCheckExport:
    """Build the active, evidence-free HTT → MIO diagnostic export.

    Only the v2 dedicated artifact is accepted.  Integrated pipeline JSON and
    v1 artifacts remain available through ``build_posterior_bundle`` with the
    explicit legacy switch.
    """

    path = Path(results_path)
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("artifact_kind") != HTT_DIRECTIONAL_POSTERIOR_ARTIFACT_KIND:
        raise ValueError(
            "active MIO cross-check requires a v2 dedicated directional artifact"
        )
    artifact = load_directional_posterior_artifact(payload)
    resolved_manifest = manifest or build_cross_check_manifest_from_directional_artifact(
        artifact,
        artifact_id=f"htt.mio_cross_check.{artifact.model}",
        artifact_path=f"artifacts/htt/{artifact.model}_mio_cross_check.json",
    )
    return MioCrossCheckExport(
        model=artifact.model,
        legacy_projection=_legacy_projection_from_artifact(artifact),
        manifest=resolved_manifest,
        source_artifact_ref=artifact.manifest.artifact_id,
        posterior_ref=artifact.posterior_ref,
    )


def _build_legacy_bundle_from_directional_artifact(
    artifact_payload: Mapping[str, Any],
    *,
    manifest: ArtifactManifest | None,
) -> PosteriorExportBundle:
    artifact = load_directional_posterior_artifact(
        artifact_payload,
        allow_legacy_reproduction=True,
    )
    resolved_manifest = manifest or build_cross_check_manifest_from_directional_artifact(
        artifact,
        artifact_id=f"htt.directional_posterior_export.{artifact.model}",
        artifact_path=f"artifacts/htt/{artifact.model}_posterior_export.json",
    )
    return PosteriorExportBundle(
        x_median=artifact.x_median,
        x_hpd68=artifact.x_hpd68,
        x_hpd95=artifact.x_hpd95,
        Q_median=artifact.Q_median,
        Q_hpd68=artifact.Q_hpd68,
        Pi_median=artifact.Pi_median,
        Pi_hpd68=artifact.Pi_hpd68,
        ln_B_total=artifact.ln_B_total,
        model_evidences=dict(artifact.model_evidences),
        F_median=artifact.F_median,
        F_hpd68=artifact.F_hpd68,
        n_live=artifact.n_live,
        model=artifact.model,
        manifest=resolved_manifest,
    )


def build_posterior_bundle(
    results_path: str | Path | None = None,
    model: str = "FLRW_tilt",
    manifest: ArtifactManifest | None = None,
    *,
    legacy_reproduction: bool = False,
    directional_inputs: DirectionalLikelihoodInputs | None = None,
    posterior_ref: str | None = None,
    evidence_ref: str | None = None,
    posterior_predictive_ref: str | None = None,
    loocv_ref: str | None = None,
) -> PosteriorExportBundle:
    """Replay the historical HTT posterior export explicitly.

    This function is not an active MIO interface.  It never fills missing
    values with zero.
    """

    if not legacy_reproduction:
        raise RuntimeError(
            "PosteriorExportBundle is legacy reproduction only; use "
            "build_mio_cross_check_export for the active evidence-free adapter"
        )
    warnings.warn(
        "build_posterior_bundle is a legacy reproduction path",
        DeprecationWarning,
        stacklevel=2,
    )
    path = _default_results_path() if results_path is None else Path(results_path)
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("artifact_kind") in {
        HTT_DIRECTIONAL_POSTERIOR_ARTIFACT_KIND,
        HTT_DIRECTIONAL_POSTERIOR_ARTIFACT_KIND_V1,
    }:
        return _build_legacy_bundle_from_directional_artifact(
            data,
            manifest=manifest,
        )

    departure = _required_mapping(data, "departure")
    model_departure = _required_mapping(departure, model)
    evidence = _required_mapping(data, "evidence")
    model_evidence = _required_mapping(evidence, model)
    filling = _required_mapping(data, "filling_fraction")

    x_data = _required_mapping(
        _required_mapping(model_departure, "layer_1_departure"), "x"
    )
    q_data = _required_mapping(
        _required_mapping(model_departure, "layer_2_occupancy"), "Q"
    )
    pi_data = _required_mapping(
        _required_mapping(model_departure, "layer_3_exceedance"), "Pi"
    )

    x_median = float(_required_path(x_data, "median"))
    x_hpd68 = _pair(_required_path(x_data, "hpd_68"), "x.hpd_68")
    x_hpd95 = _pair(_required_path(x_data, "hpd_95"), "x.hpd_95")
    q_median = float(_required_path(q_data, "median"))
    q_hpd68 = _pair(_required_path(q_data, "hpd_68"), "Q.hpd_68")
    pi_median = float(_required_path(pi_data, "0.05"))
    pi_hpd68 = (
        float(_required_path(pi_data, "0.01")),
        float(
            _required_alias(
                pi_data,
                field_name="Pi upper threshold",
                aliases=("0.10", "0.1"),
            )
        ),
    )
    ln_b = float(_required_path(model_evidence, "lnB"))
    model_evidences = {
        str(name): float(_required_path(_required_mapping(evidence, str(name)), "lnB"))
        for name in evidence
    }
    if "F_S3_mc_median" in filling:
        f_median = float(filling["F_S3_mc_median"])
    else:
        f_median = float(_required_path(filling, "F_S3_point"))
    f_hpd68 = _pair(_required_path(filling, "F_S3_mc_68"), "F.hpd_68")
    n_live = int(_required_path(model_evidence, "neff"))

    resolved_manifest = manifest
    if directional_inputs is not None:
        require_directional_model_outputs_ready(directional_inputs)
    if resolved_manifest is None and directional_inputs is not None:
        results_ref = str(path)
        resolved_manifest = build_directional_output_manifest(
            inputs=directional_inputs,
            artifact_id=f"htt.directional_posterior_export.{model}",
            artifact_path=f"artifacts/htt/{model}_posterior_export.json",
            model_name=model,
            posterior_ref=posterior_ref or f"{results_ref}#departure/{model}",
            evidence_ref=evidence_ref or f"{results_ref}#evidence/{model}",
            output_role="posterior_export_bundle_legacy_reproduction",
            cross_check_only=True,
            posterior_predictive_ref=posterior_predictive_ref,
            loocv_ref=loocv_ref,
            created_by="htt.integration.to_mio.build_posterior_bundle",
        )

    return PosteriorExportBundle(
        x_median=x_median,
        x_hpd68=x_hpd68,
        x_hpd95=x_hpd95,
        Q_median=q_median,
        Q_hpd68=q_hpd68,
        Pi_median=pi_median,
        Pi_hpd68=pi_hpd68,
        ln_B_total=ln_b,
        model_evidences=model_evidences,
        F_median=f_median,
        F_hpd68=f_hpd68,
        n_live=n_live,
        model=model,
        manifest=resolved_manifest,
    )
