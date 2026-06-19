"""
htt/integration/to_mio.py — HTT → MIO Integration Adapter
=============================================================
C-16 deliverable. Constructs a PosteriorExportBundle from HTT outputs.

Reads the integrated_pipeline_results.json structure:
  departure[model]['layer_1_departure']['x'] → x posterior
  departure[model]['layer_2_occupancy']['Q'] → legacy HTT Q cross-check
  departure[model]['layer_3_exceedance']['Pi'] → legacy HTT P_post cross-check
  evidence[model]['lnB'] → Bayes factor
  filling_fraction → F summary
"""
import json
from pathlib import Path

from common.contracts import ArtifactManifest
from htt.integration.posterior_artifact import (
    HTT_DIRECTIONAL_POSTERIOR_ARTIFACT_KIND,
    build_cross_check_manifest_from_directional_artifact,
    load_directional_posterior_artifact,
)
from htt.infer.ver2_directional_shell import (
    DirectionalLikelihoodInputs,
    build_directional_output_manifest,
    require_directional_model_outputs_ready,
)
from workspace.contracts.htt_to_mio import PosteriorExportBundle

__all__ = ['build_posterior_bundle']


def _get_nested(d, *keys, default=0.0):
    """Safely traverse nested dict."""
    for k in keys:
        if isinstance(d, dict):
            d = d.get(k, None)
        else:
            return default
        if d is None:
            return default
    return d


def _build_bundle_from_directional_artifact(
    artifact_payload,
    *,
    model: str,
    manifest: ArtifactManifest | None,
) -> PosteriorExportBundle:
    artifact = load_directional_posterior_artifact(artifact_payload)
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


def build_posterior_bundle(results_path: str = None,
                           model: str = 'FLRW_tilt',
                           manifest: ArtifactManifest | None = None,
                           *,
                           directional_inputs: DirectionalLikelihoodInputs | None = None,
                           posterior_ref: str | None = None,
                           evidence_ref: str | None = None,
                           posterior_predictive_ref: str | None = None,
                           loocv_ref: str | None = None) -> 'PosteriorExportBundle':
    """Build a PosteriorExportBundle from HTT pipeline results.

    Parameters
    ----------
    results_path : str, optional
        Path to either a dedicated HTT posterior summary artifact or the
        legacy integrated_pipeline_results.json.
    model : str
        Reference model for posteriors (default: FLRW_tilt as best-fit).
    manifest : ArtifactManifest, optional
        HTT-owned VER2 manifest for cross-check export provenance.
    """
    if results_path is None:
        results_path = str(
            Path(__file__).resolve().parent.parent.parent.parent
            / 'workspace' / 'results' / 'integrated_pipeline_results.json'
        )

    with open(results_path) as f:
        data = json.load(f)
    if data.get("artifact_kind") == HTT_DIRECTIONAL_POSTERIOR_ARTIFACT_KIND:
        return _build_bundle_from_directional_artifact(
            data,
            model=model,
            manifest=manifest,
        )

    dep = data.get('departure', {}).get(model, {})
    ev_model = data.get('evidence', {}).get(model, {})
    ff = data.get('filling_fraction', {})

    # Layer 1: x
    x_data = _get_nested(dep, 'layer_1_departure', 'x', default={})
    x_med = x_data.get('median', 0.0) if isinstance(x_data, dict) else 0.0
    x_68 = tuple(x_data.get('hpd_68', [0.0, 0.0])) if isinstance(x_data, dict) else (0.0, 0.0)
    x_95 = tuple(x_data.get('hpd_95', [0.0, 0.0])) if isinstance(x_data, dict) else (0.0, 0.0)

    # Layer 2: legacy HTT policy-normalized Q cross-check.
    Q_data = _get_nested(dep, 'layer_2_occupancy', 'Q', default={})
    Q_med = Q_data.get('median', 0.0) if isinstance(Q_data, dict) else 0.0
    Q_68 = tuple(Q_data.get('hpd_68', [0.0, 0.0])) if isinstance(Q_data, dict) else (0.0, 0.0)

    # Layer 3: legacy HTT posterior exceedance cross-check at q*=0.05.
    Pi_data = _get_nested(dep, 'layer_3_exceedance', 'Pi', default={})
    if isinstance(Pi_data, dict):
        Pi_med = Pi_data.get('0.05', 0.0)
        Pi_68 = (Pi_data.get('0.1', 0.0), Pi_data.get('0.01', 1.0))
    else:
        Pi_med = 0.0
        Pi_68 = (0.0, 0.0)

    # Evidence
    ln_B = ev_model.get('lnB', 0.0) if isinstance(ev_model, dict) else 0.0
    model_evidences = {
        name: info.get('lnB', 0.0) if isinstance(info, dict) else 0.0
        for name, info in data.get('evidence', {}).items()
    }

    # Filling fraction
    F_med = ff.get('F_S3_mc_median', ff.get('F_S3_point', 0.0))
    F_68 = tuple(ff.get('F_S3_mc_68', [0.0, 0.0]))

    n_live = ev_model.get('neff', 500) if isinstance(ev_model, dict) else 500
    resolved_manifest = manifest
    if directional_inputs is not None:
        require_directional_model_outputs_ready(directional_inputs)
    if resolved_manifest is None and directional_inputs is not None:
        results_ref = str(results_path)
        resolved_manifest = build_directional_output_manifest(
            inputs=directional_inputs,
            artifact_id=f"htt.directional_posterior_export.{model}",
            artifact_path=f"artifacts/htt/{model}_posterior_export.json",
            model_name=model,
            posterior_ref=posterior_ref or f"{results_ref}#departure/{model}",
            evidence_ref=evidence_ref or f"{results_ref}#evidence/{model}",
            output_role="posterior_export_bundle",
            cross_check_only=True,
            posterior_predictive_ref=posterior_predictive_ref,
            loocv_ref=loocv_ref,
            created_by="htt.integration.to_mio.build_posterior_bundle",
        )

    return PosteriorExportBundle(
        x_median=x_med, x_hpd68=x_68, x_hpd95=x_95,
        Q_median=Q_med, Q_hpd68=Q_68,
        Pi_median=Pi_med, Pi_hpd68=Pi_68,
        ln_B_total=ln_B, model_evidences=model_evidences,
        F_median=F_med, F_hpd68=F_68,
        n_live=n_live,
        model=model,
        manifest=resolved_manifest,
    )
