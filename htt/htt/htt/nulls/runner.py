"""
htt/nulls/runner.py — Null Library Runner
==========================================
P-14 deliverable. Generates 100 datasets per family, runs a fast
evidence approximation, and computes false-positive rates.

For production use, replace the fast approximation with full
dynesty nested sampling (takes ~5 min per dataset × 500 = ~40h).
"""
import json
import numpy as np
from pathlib import Path


from htt.nulls.common_interface import NullFamilyResult, FalsePositiveRates
from htt.nulls.scanning_law import ScanningLawNull
from htt.nulls.mask_leakage import MaskLeakageNull
from htt.nulls.clustering import (
    ClusteringDipoleNull, SelectionResponseNull, SurveyAxisNull
)

__all__ = ['run_null_library', 'ALL_FAMILIES']

ALL_FAMILIES = [
    ScanningLawNull(),
    MaskLeakageNull(),
    ClusteringDipoleNull(),
    SelectionResponseNull(),
    SurveyAxisNull(),
]


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
    sn_cf4 = ds.b_CF4 / ds.b_CF4_s if ds.b_CF4_s > 0 else 0

    # Bivariate Gaussian for CW+Radio (channel b)
    rho = ds.rho_CW_radio
    det_factor = 1.0 / (1 - rho**2) if abs(rho) < 0.99 else 1.0
    chi2_biv = det_factor * (sn_cw**2 + sn_rad**2 - 2*rho*sn_cw*sn_rad)

    # CF4 channel (channel c)
    chi2_cf4 = sn_cf4**2

    # Total lnB ≈ half the chi² improvement minus Occam penalty
    # Occam penalty for β: ln(prior_width / posterior_width) ≈ ln(100)
    occam = np.log(100)  # prior is ~100× wider than posterior
    lnB = 0.5 * (chi2_biv + chi2_cf4) - occam

    return float(lnB)


def _fast_beta_approx(ds) -> float:
    """Fast β posterior median approximation."""
    # Inverse-variance weighted mean of the three channels
    w_cw = 1.0 / ds.e1_CW_s**2 if ds.e1_CW_s > 0 else 0
    w_rad = 1.0 / ds.e1_rad_s**2 if ds.e1_rad_s > 0 else 0
    w_cf4 = 1.0 / ds.b_CF4_s**2 if ds.b_CF4_s > 0 else 0
    w_total = w_cw + w_rad + w_cf4
    if w_total == 0:
        return 0.0
    beta = (w_cw * ds.e1_CW + w_rad * ds.e1_rad + w_cf4 * ds.b_CF4) / w_total
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


if __name__ == '__main__':
    import json
    with open('obs_defaults.json') as f:
        obs = json.load(f)
    run_null_library(obs, n_datasets=100,
                     output_path='false_positive_rates.json')
