"""
htt/nulls/runner.py — Null Library Runner
==========================================
P-14 deliverable. Generates 100 datasets per family, runs a fast
evidence approximation, and computes false-positive rates.

For production use, replace the fast approximation with full
dynesty nested sampling (takes ~5 min per dataset × 500 = ~40h).
"""
import hashlib
import json
import numpy as np
import platform
from pathlib import Path
from typing import Any, Mapping

from htt.core.cf4_observational_input import OPEN_FINDING_IDS

from htt.nulls.common_interface import NullFamilyResult, FalsePositiveRates
from htt.nulls.scanning_law import ScanningLawNull
from htt.nulls.mask_leakage import MaskLeakageNull
from htt.nulls.clustering import (
    ClusteringDipoleNull, SelectionResponseNull, SurveyAxisNull
)

__all__ = ['run_null_library', 'null_library_fpr_report_artifact', 'ALL_FAMILIES']

ALL_FAMILIES = [
    ScanningLawNull(),
    MaskLeakageNull(),
    ClusteringDipoleNull(),
    SelectionResponseNull(),
    SurveyAxisNull(),
]


def _jsonify(obj: Any) -> Any:
    """Recursively convert numpy-heavy structures to JSON-native values."""
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    if isinstance(obj, np.generic):
        return obj.item()
    if isinstance(obj, Mapping):
        return {str(k): _jsonify(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_jsonify(v) for v in obj]
    return obj


def _config_hash(payload: Mapping[str, Any]) -> str:
    """Stable SHA256 hash for report configuration payloads."""
    blob = json.dumps(_jsonify(payload), sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def _fast_lnB_approx(ds) -> float:
    """Fast analytical Bayes factor approximation for a null dataset.

    Uses the Gaussian-channel likelihood structure:
      lnB ≈ (1/2) Σ_ch (d_ch / σ_ch)² - (1/2) ln(2π σ_β² / prior_width²)

    For β = 0 null data, this reduces to the sum of (S/N)² contributions
    from each channel, minus the Occam penalty for the β parameter.
    """
    # Channel contributions (squared signal-to-noise)
    sn_cw = ds.e1_CW / ds.e1_CW_s if ds.e1_CW_s > 0 else 0
    sn_rad = ds.e1_rad / ds.e1_rad_s if ds.e1_rad_s > 0 else 0

    # Bivariate Gaussian for CW+Radio (channel b)
    rho = ds.rho_CW_radio
    det_factor = 1.0 / (1 - rho**2) if abs(rho) < 0.99 else 1.0
    chi2_biv = det_factor * (sn_cw**2 + sn_rad**2 - 2*rho*sn_cw*sn_rad)

    # Total lnB ≈ half the chi² improvement minus Occam penalty
    # Occam penalty for β: ln(prior_width / posterior_width) ≈ ln(100)
    occam = np.log(100)  # prior is ~100× wider than posterior
    lnB = 0.5 * chi2_biv - occam

    return float(lnB)


def _fast_beta_approx(ds) -> float:
    """Fast β posterior median approximation."""
    # Inverse-variance weighted mean of the two active channels.
    w_cw = 1.0 / ds.e1_CW_s**2 if ds.e1_CW_s > 0 else 0
    w_rad = 1.0 / ds.e1_rad_s**2 if ds.e1_rad_s > 0 else 0
    w_total = w_cw + w_rad
    if w_total == 0:
        return 0.0
    beta = (w_cw * ds.e1_CW + w_rad * ds.e1_rad) / w_total
    return float(beta)


def run_family(family, obs_base: dict, n_datasets: int = 100,
               pi_threshold: float = 0.05,
               lnB_threshold: float = 5.0) -> NullFamilyResult:
    """Run inference on null datasets from one family."""
    datasets = family.generate_batch(n_datasets, obs_base)

    lnBs = []
    betas = []
    for ds in datasets:
        lnB = _fast_lnB_approx(ds)
        beta = _fast_beta_approx(ds)
        lnBs.append(lnB)
        betas.append(beta)

    lnBs = np.array(lnBs)
    betas = np.array(betas)

    # False-positive: lnB > threshold
    n_det_lnB = int((lnBs > lnB_threshold).sum())

    # False-positive: Π(0.05) > 0.95
    # Approximate Π from lnB: if lnB > 10, Π(0.05) ≈ 1; if lnB < 0, Π ≈ 0
    Pi_approx = np.clip((lnBs - 0) / 15, 0, 1)  # rough linear map
    n_det_Pi = int((Pi_approx > 0.95).sum())

    return NullFamilyResult(
        family=family.name,
        n_datasets=n_datasets,
        n_detections_Pi005=n_det_Pi,
        n_detections_lnB5=n_det_lnB,
        fp_rate_Pi005=n_det_Pi / n_datasets,
        fp_rate_lnB5=n_det_lnB / n_datasets,
        lnB_median=float(np.median(lnBs)),
        lnB_std=float(np.std(lnBs)),
        beta_median_mean=float(np.mean(betas)),
    )


def run_null_library(obs_base: dict, n_datasets: int = 100,
                     output_path: str = None) -> dict:
    """Run the full 5-family null library.

    Returns dict suitable for JSON serialisation.
    """
    fpr = FalsePositiveRates()

    for family in ALL_FAMILIES:
        result = run_family(family, obs_base, n_datasets)
        fpr.add(result)
        print(f"  {family.name:20s}: FP(lnB>5)={result.fp_rate_lnB5:.2%}, "
              f"FP(Π>0.95)={result.fp_rate_Pi005:.2%}, "
              f"lnB_med={result.lnB_median:+.1f}")

    output = {
        '_meta': {
            'task': 'P-14',
            'n_datasets_per_family': n_datasets,
            'n_families': len(ALL_FAMILIES),
            'total_datasets': n_datasets * len(ALL_FAMILIES),
            'claim_tier': 'diagnostic_only',
            'excluded_channels': ['c'],
            'cf4_channel_status': 'QUARANTINED_OPEN_FINDINGS',
            'cf4_finding_ids': list(OPEN_FINDING_IDS),
        },
        'families': fpr.to_dict(),
        'union_fp_Pi005': fpr.union_fp_Pi005,
        'target': {
            'individual_fp_max': 0.05,
            'union_fp_max': 0.01,
        },
    }

    if output_path:
        with open(output_path, 'w') as f:
            json.dump(output, f, indent=2)

    return output


def null_library_fpr_report_artifact(
    model_results: Mapping[str, Mapping[str, Any]],
    *,
    model_order: list[str] | None = None,
    family_order: list[str] | None = None,
    metadata: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Build ``null_library_fpr_v1.json`` from per-model null-library outputs.

    ``model_results`` maps ``model_tag -> run_null_library(...)`` output.
    The report collapses those per-model runs into the 5-family × 15-model
    heatmap requested by the research plan.
    """
    from htt.core.analysis_extended import EVIDENCE_MODEL_TAGS

    models = list(model_order or EVIDENCE_MODEL_TAGS)
    families = list(family_order or [fam.name for fam in ALL_FAMILIES])
    missing_models = [tag for tag in models if tag not in model_results]
    if missing_models:
        raise KeyError(f"Missing model result(s): {missing_models}")

    fp_pi = np.empty((len(families), len(models)), dtype=float)
    fp_lnb = np.empty((len(families), len(models)), dtype=float)
    union = []

    for j, model_tag in enumerate(models):
        result = model_results[model_tag]
        fam_payload = result.get('families')
        if not isinstance(fam_payload, Mapping):
            raise ValueError(
                f"model {model_tag!r} result must contain a `families` mapping"
            )
        missing_families = [name for name in families if name not in fam_payload]
        if missing_families:
            raise KeyError(
                f"model {model_tag!r} missing family result(s): {missing_families}"
            )
        union.append({
            'tag': model_tag,
            'union_fp_Pi005': float(result.get('union_fp_Pi005', 0.0)),
        })
        for i, family in enumerate(families):
            fam = fam_payload[family]
            fp_pi[i, j] = float(fam['fp_rate_Pi005'])
            fp_lnb[i, j] = float(fam['fp_rate_lnB5'])

    extra = dict(metadata or {})
    config_payload = {
        'model_order': models,
        'family_order': families,
        'metadata': extra,
    }
    return _jsonify({
        'artifact_name': 'null_library_fpr_v1.json',
        'generated_by': extra.get(
            'generated_by',
            'htt.nulls.runner.null_library_fpr_report_artifact',
        ),
        'git_commit': extra.get('git_commit', ''),
        'config_hash': _config_hash(config_payload),
        'input_data_hashes': list(extra.get('input_data_hashes', [])),
        'random_seed': extra.get('random_seed'),
        'wall_time_sec': extra.get('wall_time_sec'),
        'python_version': extra.get('python_version', platform.python_version()),
        'numpy_version': extra.get('numpy_version', np.__version__),
        'claim_tier': extra.get('claim_tier', 'diagnostic_only'),
        'scope_label': extra.get('scope_label', 'report'),
        'production_allowed': False,
        'excluded_channels': ['c'],
        'cf4_channel_status': 'QUARANTINED_OPEN_FINDINGS',
        'cf4_finding_ids': list(OPEN_FINDING_IDS),
        'shape': {
            'n_families': len(families),
            'n_models': len(models),
            'orientation': 'rows=families, cols=models',
        },
        'family_order': families,
        'model_order': models,
        'fp_rate_Pi005_matrix': fp_pi,
        'fp_rate_lnB5_matrix': fp_lnb,
        'union_fp_Pi005_by_model': union,
    })


if __name__ == '__main__':
    import json
    with open('obs_defaults.json') as f:
        obs = json.load(f)
    run_null_library(obs, n_datasets=100,
                     output_path='false_positive_rates.json')
