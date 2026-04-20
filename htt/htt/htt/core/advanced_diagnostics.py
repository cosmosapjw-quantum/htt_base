"""Advanced statistical diagnostics for geometry-source discrimination.

Strategy A: Depth Tomography
  Tests whether the tilt signal is depth-independent (geometric) or
  depth-dependent (kinematic local flow) by comparing per-survey
  amplitude estimates at different effective redshifts.

Strategy B: Savage-Dickey Density Ratio
  Computes the Bayes factor for "is Σ² needed?" from the BI_tilt
  posterior at Σ²→0 without re-running nested sampling. This is the
  definitive test for shear detection.

Strategy C: Cross-Channel Coherence
  Measures per-channel β estimates and quantifies tension via an
  internal-consistency χ² statistic.

Additional diagnostics:
  - Posterior predictive observables
  - Leave-one-out cross-validation stability
  - Information content per channel (bits)
"""
import hashlib
import json
import numpy as np
from dataclasses import dataclass, field
import platform
from typing import Any, Dict, List, Mapping, Optional, Tuple

__all__ = [
    'DepthTomography', 'SavageDickeyRatio', 'CrossChannelCoherence',
    'PosteriorPredictive', 'LeaveOneOutCV',
    'redshift_tomography_report_artifact',
    'cross_channel_coherence_report_artifact',
    'posterior_predictive_report_artifact',
    'loocv_report_artifact',
    'run_advanced_diagnostics',
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


# ═══════════════════════════════════════════════════════════════
#  Strategy A: Depth Tomography
# ═══════════════════════════════════════════════════════════════

@dataclass(frozen=True)
class DepthBin:
    name: str
    z_eff: float
    amplitude: float     # observed dipole amplitude (β or ε₁)
    sigma: float
    depth_Mpc: float
    survey_type: str


@dataclass(frozen=True)
class DepthTomographyResult:
    bins: Tuple
    geometric_chi2: float    # χ² for constant-amplitude model
    geometric_pvalue: float
    kinematic_chi2: float    # χ² for 1/r-decay model
    kinematic_pvalue: float
    best_fit_constant: float # best-fit constant amplitude
    depth_gradient: float    # dβ/dz slope
    depth_gradient_sigma: float
    interpretation: str


class DepthTomography:
    """Test depth-dependence of the tilt signal.

    Geometric tilt (Bianchi): amplitude is constant with depth.
    Kinematic local flow: amplitude decays as ~v_bulk/r ∝ 1/(1+z).

    We fit two models to the depth ladder:
    H_geo: β(z) = β₀ (constant)
    H_kin: β(z) = β₀ / (1 + z)^α with α > 0

    The χ² difference discriminates the two hypotheses.
    """

    # Survey depth ladder
    BINS = (
        DepthBin('CF4', 0.05, 1.334e-3, 0.267e-3, 150, 'peculiar velocity'),
        DepthBin('CatWISE', 0.15, 1.476e-3, 0.30e-3, 450, 'number count dipole'),
        DepthBin('Radio', 0.80, 3.296e-3, 0.60e-3, 2400, 'radio continuum'),
    )

    def run(self) -> DepthTomographyResult:
        from scipy.stats import chi2 as chi2_dist

        amps = np.array([b.amplitude for b in self.BINS])
        sigs = np.array([b.sigma for b in self.BINS])
        zs = np.array([b.z_eff for b in self.BINS])
        w = 1.0 / sigs**2

        # H_geo: constant amplitude
        beta_geo = np.sum(w * amps) / np.sum(w)
        chi2_geo = float(np.sum(((amps - beta_geo) / sigs)**2))
        ndof_geo = len(amps) - 1
        pval_geo = float(1 - chi2_dist.cdf(chi2_geo, ndof_geo))

        # H_kin: β(z) = β₀ / (1+z)
        # Linearise: ln(β) = ln(β₀) - α·ln(1+z)
        ln_amp = np.log(amps)
        ln_z = np.log(1 + zs)
        # Weighted least squares: ln(β) = a + b·ln(1+z)
        W = 1.0 / (sigs / amps)**2  # propagated weights
        S0 = np.sum(W)
        Sx = np.sum(W * ln_z)
        Sy = np.sum(W * ln_amp)
        Sxx = np.sum(W * ln_z**2)
        Sxy = np.sum(W * ln_z * ln_amp)
        det = S0 * Sxx - Sx**2
        if abs(det) > 1e-30:
            a = (Sxx * Sy - Sx * Sxy) / det
            b = (S0 * Sxy - Sx * Sy) / det
            b_err = np.sqrt(S0 / det)
        else:
            a, b, b_err = np.log(beta_geo), 0.0, 99.0

        beta_kin_pred = np.exp(a + b * ln_z)
        chi2_kin = float(np.sum(((amps - beta_kin_pred) / sigs)**2))
        ndof_kin = len(amps) - 2
        pval_kin = float(1 - chi2_dist.cdf(chi2_kin, max(ndof_kin, 1)))

        # Interpretation
        if chi2_geo < chi2_kin:
            if pval_geo > 0.05:
                interp = (f"Constant-amplitude model preferred (χ²={chi2_geo:.1f}, "
                          f"p={pval_geo:.2f}). Consistent with GEOMETRIC tilt. "
                          f"But Radio excess (ε₁=3.3e-3 vs CF4 β=1.3e-3) "
                          f"creates tension at {(3.296e-3 - beta_geo)/0.6e-3:.1f}σ.")
            else:
                interp = (f"Neither model fits well. Constant: χ²={chi2_geo:.1f} "
                          f"(p={pval_geo:.2f}), Kinematic: χ²={chi2_kin:.1f} "
                          f"(p={pval_kin:.2f}). Radio excess drives the tension.")
        else:
            interp = (f"Depth-dependent model preferred (χ²={chi2_kin:.1f} vs "
                      f"{chi2_geo:.1f}). Slope α={b:.2f}±{b_err:.2f}. "
                      f"Consistent with KINEMATIC local flow + Radio excess.")

        return DepthTomographyResult(
            bins=self.BINS,
            geometric_chi2=round(chi2_geo, 2),
            geometric_pvalue=round(pval_geo, 4),
            kinematic_chi2=round(chi2_kin, 2),
            kinematic_pvalue=round(pval_kin, 4),
            best_fit_constant=round(float(beta_geo), 6),
            depth_gradient=round(float(b), 3),
            depth_gradient_sigma=round(float(b_err), 3),
            interpretation=interp,
        )


# ═══════════════════════════════════════════════════════════════
#  Strategy B: Savage-Dickey Density Ratio
# ═══════════════════════════════════════════════════════════════

@dataclass(frozen=True)
class SavageDickeyResult:
    model: str
    param_name: str
    param_value_null: float
    posterior_density_at_null: float
    prior_density_at_null: float
    bayes_factor_01: float      # B_01 = p(θ=θ₀|D) / p(θ=θ₀)
    log_bayes_factor: float
    param_needed: bool          # True if data prefer θ ≠ θ₀
    interpretation: str


class SavageDickeyRatio:
    """Savage-Dickey density ratio for nested model comparison.

    For nested models M₀ ⊂ M₁ where M₀ sets parameter θ = θ₀:
      B₀₁ = p(θ = θ₀ | data, M₁) / p(θ = θ₀ | M₁)

    B₀₁ > 1: data support the null (θ₀ sufficient)
    B₀₁ < 1: data prefer θ ≠ θ₀ (extra parameter needed)

    Key application: FLRW_tilt (β only) vs BI_tilt (β, Σ²) at Σ²=0.
    """

    def compute(self, param_name: str, samples: np.ndarray,
                weights: np.ndarray, prior_lo: float, prior_hi: float,
                null_value: float = 0.0,
                log_prior: bool = True,
                model: str = 'BI_tilt') -> SavageDickeyResult:
        """Compute Savage-Dickey ratio.

        Parameters
        ----------
        param_name : str
        samples : array (n_samples,)
            Posterior samples of the parameter.
        weights : array (n_samples,)
        prior_lo, prior_hi : float
            Prior bounds.
        null_value : float
            The nested null hypothesis value.
        log_prior : bool
            If True, prior is log-uniform.
        """
        w = weights / weights.sum()

        # Prior density at null
        if log_prior and null_value > 0:
            # Log-uniform: p(θ) = 1/(θ ln(hi/lo))
            prior_at_null = 1.0 / (null_value * np.log(prior_hi / prior_lo))
        elif log_prior and null_value <= 0:
            # For Σ²=0 in log-uniform prior: density → ∞ at 0
            # Use density at prior_lo as proxy
            prior_at_null = 1.0 / (prior_lo * np.log(prior_hi / prior_lo))
        else:
            prior_at_null = 1.0 / (prior_hi - prior_lo)

        # Posterior density at null via KDE
        from scipy.stats import gaussian_kde
        log_samples = np.log10(np.maximum(samples, 1e-50))
        kde = gaussian_kde(log_samples, weights=w)
        log_null = np.log10(max(null_value, prior_lo))
        post_density_log = float(kde(log_null)[0])
        # Convert from log10 density to linear density
        post_at_null = post_density_log / (max(null_value, prior_lo) * np.log(10))

        B01 = post_at_null / prior_at_null if prior_at_null > 0 else 0
        lnB01 = np.log(max(B01, 1e-50))

        if B01 > 3:
            interp = f"{param_name} not needed (B₀₁={B01:.1f} > 3: null preferred)"
            needed = False
        elif B01 > 1:
            interp = f"{param_name} weakly not needed (B₀₁={B01:.1f})"
            needed = False
        elif B01 > 1/3:
            interp = f"{param_name}: inconclusive (B₀₁={B01:.2f})"
            needed = False
        else:
            interp = f"{param_name} needed (B₀₁={B01:.2f} < 1/3: data prefer {param_name} ≠ 0)"
            needed = True

        return SavageDickeyResult(
            model=model, param_name=param_name,
            param_value_null=null_value,
            posterior_density_at_null=round(post_at_null, 6),
            prior_density_at_null=round(prior_at_null, 6),
            bayes_factor_01=round(float(B01), 4),
            log_bayes_factor=round(float(lnB01), 2),
            param_needed=needed,
            interpretation=interp,
        )


# ═══════════════════════════════════════════════════════════════
#  Strategy C: Cross-Channel Coherence
# ═══════════════════════════════════════════════════════════════

@dataclass(frozen=True)
class ChannelEstimate:
    channel: str
    beta_estimate: float
    sigma: float
    weight: float


@dataclass(frozen=True)
class CrossChannelResult:
    estimates: Tuple
    weighted_mean_beta: float
    chi2_consistency: float
    ndof: int
    pvalue: float
    tension_sigma: float
    most_discrepant: str
    interpretation: str


class CrossChannelCoherence:
    """Internal consistency test across dipole survey channels.

    Each channel gives an independent β estimate. If the channels
    are coherent (same underlying β), the internal-consistency χ²
    should be small. Large χ² indicates either:
    - different physics at different depths (kinematic)
    - systematic contamination in one or more channels
    - genuine geometry-dependent coupling
    """

    def run(self) -> CrossChannelResult:
        from scipy.stats import chi2 as chi2_dist

        # Per-channel β estimates
        # CF4: direct β measurement
        # CatWISE: ε₁ → β via ε₁ = β(1+1/12)
        eta = 1.0 / 12.0
        estimates = (
            ChannelEstimate('CF4', 1.334e-3, 0.267e-3, 1.0),
            ChannelEstimate('CatWISE', 1.476e-3 / (1+eta), 0.30e-3 / (1+eta), 1.0),
            ChannelEstimate('Radio', 3.296e-3 / (1+eta), 0.60e-3 / (1+eta), 1.0),
        )

        betas = np.array([e.beta_estimate for e in estimates])
        sigmas = np.array([e.sigma for e in estimates])
        w = 1.0 / sigmas**2

        # Inverse-variance weighted mean
        beta_mean = float(np.sum(w * betas) / np.sum(w))

        # Consistency χ²
        chi2_val = float(np.sum(((betas - beta_mean) / sigmas)**2))
        ndof = len(betas) - 1
        pval = float(1 - chi2_dist.cdf(chi2_val, ndof))
        tension = float(np.sqrt(chi2_val - ndof)) if chi2_val > ndof else 0.0

        # Most discrepant channel
        pulls = np.abs((betas - beta_mean) / sigmas)
        worst_idx = int(np.argmax(pulls))
        worst = estimates[worst_idx].channel

        if pval > 0.05:
            interp = (f"Channels are consistent (χ²={chi2_val:.1f}/{ndof}, "
                      f"p={pval:.2f}). All surveys agree on β≈{beta_mean:.4e}.")
        elif pval > 0.01:
            interp = (f"Mild tension (χ²={chi2_val:.1f}/{ndof}, p={pval:.3f}). "
                      f"Most discrepant: {worst} ({pulls[worst_idx]:.1f}σ pull).")
        else:
            interp = (f"Significant tension (χ²={chi2_val:.1f}/{ndof}, p={pval:.4f}). "
                      f"{worst} is {pulls[worst_idx]:.1f}σ from the mean. "
                      f"This suggests the dipole amplitude is NOT constant across "
                      f"surveys, which is informative for source discrimination.")

        return CrossChannelResult(
            estimates=estimates,
            weighted_mean_beta=round(beta_mean, 6),
            chi2_consistency=round(chi2_val, 2),
            ndof=ndof,
            pvalue=round(pval, 4),
            tension_sigma=round(tension, 1),
            most_discrepant=worst,
            interpretation=interp,
        )


# ═══════════════════════════════════════════════════════════════
#  Additional: Posterior Predictive Observables
# ═══════════════════════════════════════════════════════════════

@dataclass(frozen=True)
class PosteriorPredictiveResult:
    model: str
    observables: Dict
    chi2_total: float
    ndof: int
    pvalue: float
    interpretation: str


class PosteriorPredictive:
    """What does the best-fit model predict we should observe?

    Given the posterior β, compute predicted observables and compare
    with actual observations. A good model should have χ² ~ ndof.
    """

    def compute(self, model_name: str, beta_med: float) -> PosteriorPredictiveResult:
        from scipy.stats import chi2 as chi2_dist
        from htt.core.evidence_models_R03a import (
            eps1_from_beta, boost_to_D2, D2_LCDM, D3_LCDM)

        eps1 = eps1_from_beta(beta_med)
        D2_boost = boost_to_D2(beta_med)
        v_kms = 299792.458 * np.tanh(beta_med)

        # Predicted vs observed
        obs = {
            'eps1_intrinsic': {
                'predicted': eps1, 'observed': 0.0, 'sigma': 1.5e-3,
                'note': 'Ferreira-Quartin UL (half-Gaussian)',
            },
            'beta_CF4': {
                'predicted': beta_med, 'observed': 1.334e-3, 'sigma': 0.267e-3,
                'note': 'CosmicFlows-4 bulk flow',
            },
            'eps1_CatWISE': {
                'predicted': eps1, 'observed': 1.476e-3, 'sigma': 0.30e-3,
                'note': 'CatWISE+Böhme 2025',
            },
            'D2_total': {
                'predicted': D2_LCDM + D2_boost, 'observed': 225.9, 'sigma': 5.0,
                'note': 'Planck quadrupole (χ²(5) channel)',
            },
            'v_tilt_kms': {
                'predicted': v_kms, 'observed': 400.0, 'sigma': 80.0,
                'note': 'CF4-equivalent velocity',
            },
        }

        chi2_total = 0.0
        ndof = 0
        for key, o in obs.items():
            if o['sigma'] > 0 and o['observed'] != 0:
                chi2_total += ((o['predicted'] - o['observed']) / o['sigma'])**2
                ndof += 1

        pval = float(1 - chi2_dist.cdf(chi2_total, max(ndof, 1)))

        if pval > 0.05:
            interp = f"Model fits well (χ²={chi2_total:.1f}/{ndof}, p={pval:.2f})"
        else:
            interp = f"Some tension (χ²={chi2_total:.1f}/{ndof}, p={pval:.3f})"

        return PosteriorPredictiveResult(
            model=model_name, observables=obs,
            chi2_total=round(chi2_total, 2), ndof=ndof,
            pvalue=round(pval, 4), interpretation=interp,
        )


# ═══════════════════════════════════════════════════════════════
#  Additional: Leave-One-Out Cross-Validation
# ═══════════════════════════════════════════════════════════════

@dataclass(frozen=True)
class LOOCVResult:
    dropped_channel: str
    lnZ_without: float
    lnB_without: float
    delta_lnB: float
    beta_shift_pct: float
    interpretation: str


class LeaveOneOutCV:
    """Leave-one-out cross-validation of evidence stability.

    For each channel, re-run FLRW_tilt without it and measure
    how much the evidence and β estimate change.

    Uses pre-computed channel ablation results if available.
    """

    def compute_from_ablation(self, ablation: dict,
                              lnB_full: float) -> List[LOOCVResult]:
        results = []
        channel_map = {
            'no_CF4': 'c (CF4 bulk flow)',
            'no_CatWISE': 'b (CatWISE+Radio)',
        }
        for key, label in channel_map.items():
            if key in ablation.get('channels', {}):
                ch = ablation['channels'][key]
                lnB_wo = ch['lnB']
                delta = lnB_full - lnB_wo
                interp = (f"Dropping {label}: ΔlnB = {delta:+.1f}. "
                          f"{'Critical channel' if abs(delta) > 5 else 'Evidence stable'}.")
                results.append(LOOCVResult(
                    dropped_channel=label,
                    lnZ_without=0, lnB_without=lnB_wo,
                    delta_lnB=round(delta, 2),
                    beta_shift_pct=0,  # would need re-sampling
                    interpretation=interp,
                ))
        return results


def redshift_tomography_report_artifact(
    result: DepthTomographyResult | None = None,
    *,
    metadata: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Build ``redshift_tomography_v1.json`` from the depth-tomography result."""
    if result is None:
        result = DepthTomography().run()
    bins = list(result.bins)
    z = np.asarray([b.z_eff for b in bins], dtype=float)
    amp = np.asarray([b.amplitude for b in bins], dtype=float)
    sigma = np.asarray([b.sigma for b in bins], dtype=float)
    order = np.argsort(z)
    z_sorted = z[order]
    amp_sorted = amp[order]
    drift_per_z = None
    if len(z_sorted) >= 2 and z_sorted[-1] != z_sorted[0]:
        drift_per_z = float((amp_sorted[-1] - amp_sorted[0]) / (z_sorted[-1] - z_sorted[0]))

    extra = dict(metadata or {})
    config_payload = {
        'bins': [b.name for b in bins],
        'metadata': extra,
    }
    return _jsonify({
        'artifact_name': 'redshift_tomography_v1.json',
        'generated_by': extra.get(
            'generated_by',
            'htt.core.advanced_diagnostics.redshift_tomography_report_artifact',
        ),
        'git_commit': extra.get('git_commit', ''),
        'config_hash': _config_hash(config_payload),
        'input_data_hashes': list(extra.get('input_data_hashes', [])),
        'random_seed': extra.get('random_seed'),
        'wall_time_sec': extra.get('wall_time_sec'),
        'python_version': extra.get('python_version', platform.python_version()),
        'numpy_version': extra.get('numpy_version', np.__version__),
        'claim_tier': extra.get('claim_tier', 'REPORT'),
        'scope_label': extra.get('scope_label', 'report'),
        'production_allowed': False,
        'n_bins': len(bins),
        'bins': [
            {
                'name': b.name,
                'z_eff': float(b.z_eff),
                'amplitude': float(b.amplitude),
                'sigma': float(b.sigma),
                'depth_Mpc': float(b.depth_Mpc),
                'survey_type': b.survey_type,
            }
            for b in bins
        ],
        'geometric_chi2': float(result.geometric_chi2),
        'geometric_pvalue': float(result.geometric_pvalue),
        'kinematic_chi2': float(result.kinematic_chi2),
        'kinematic_pvalue': float(result.kinematic_pvalue),
        'best_fit_constant': float(result.best_fit_constant),
        'depth_gradient': float(result.depth_gradient),
        'depth_gradient_sigma': float(result.depth_gradient_sigma),
        'amplitude_drift_per_unit_z': drift_per_z,
        'interpretation': result.interpretation,
    })


def cross_channel_coherence_report_artifact(
    result: CrossChannelResult | None = None,
    *,
    metadata: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Build ``cross_channel_coherence_v1.json`` from the coherence result."""
    if result is None:
        result = CrossChannelCoherence().run()
    estimates = list(result.estimates)
    channel_order = [e.channel for e in estimates]
    pairwise = np.zeros((len(estimates), len(estimates)), dtype=float)
    for i, lhs in enumerate(estimates):
        for j, rhs in enumerate(estimates):
            if i == j:
                continue
            sigma = np.hypot(lhs.sigma, rhs.sigma)
            pairwise[i, j] = 0.0 if sigma <= 0 else abs(
                lhs.beta_estimate - rhs.beta_estimate
            ) / sigma

    extra = dict(metadata or {})
    config_payload = {
        'channel_order': channel_order,
        'metadata': extra,
    }
    return _jsonify({
        'artifact_name': 'cross_channel_coherence_v1.json',
        'generated_by': extra.get(
            'generated_by',
            'htt.core.advanced_diagnostics.cross_channel_coherence_report_artifact',
        ),
        'git_commit': extra.get('git_commit', ''),
        'config_hash': _config_hash(config_payload),
        'input_data_hashes': list(extra.get('input_data_hashes', [])),
        'random_seed': extra.get('random_seed'),
        'wall_time_sec': extra.get('wall_time_sec'),
        'python_version': extra.get('python_version', platform.python_version()),
        'numpy_version': extra.get('numpy_version', np.__version__),
        'claim_tier': extra.get('claim_tier', 'REPORT'),
        'scope_label': extra.get('scope_label', 'report'),
        'production_allowed': False,
        'channel_order': channel_order,
        'estimates': {
            e.channel: {
                'beta_estimate': float(e.beta_estimate),
                'sigma': float(e.sigma),
                'weight': float(e.weight),
            }
            for e in estimates
        },
        'weighted_mean_beta': float(result.weighted_mean_beta),
        'chi2_consistency': float(result.chi2_consistency),
        'ndof': int(result.ndof),
        'pvalue': float(result.pvalue),
        'tension_sigma': float(result.tension_sigma),
        'most_discrepant': result.most_discrepant,
        'pairwise_tension_sigma_matrix': pairwise,
        'interpretation': result.interpretation,
    })


def posterior_predictive_report_artifact(
    *,
    model_name: str = 'FLRW_tilt',
    beta_med: float = 1.36e-3,
    result: PosteriorPredictiveResult | None = None,
    metadata: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Build ``posterior_predictive_v1.json`` from PPC observables."""
    if result is None:
        result = PosteriorPredictive().compute(model_name, beta_med)
    pulls = {}
    for key, obs in result.observables.items():
        sigma = float(obs['sigma'])
        observed = float(obs['observed'])
        predicted = float(obs['predicted'])
        pulls[key] = (
            None
            if sigma <= 0.0
            else float((predicted - observed) / sigma)
        )

    extra = dict(metadata or {})
    config_payload = {
        'model_name': result.model,
        'beta_med': beta_med,
        'metadata': extra,
    }
    return _jsonify({
        'artifact_name': 'posterior_predictive_v1.json',
        'generated_by': extra.get(
            'generated_by',
            'htt.core.advanced_diagnostics.posterior_predictive_report_artifact',
        ),
        'git_commit': extra.get('git_commit', ''),
        'config_hash': _config_hash(config_payload),
        'input_data_hashes': list(extra.get('input_data_hashes', [])),
        'random_seed': extra.get('random_seed'),
        'wall_time_sec': extra.get('wall_time_sec'),
        'python_version': extra.get('python_version', platform.python_version()),
        'numpy_version': extra.get('numpy_version', np.__version__),
        'claim_tier': extra.get('claim_tier', 'REPORT'),
        'scope_label': extra.get('scope_label', 'report'),
        'production_allowed': False,
        'model': result.model,
        'chi2_total': float(result.chi2_total),
        'ndof': int(result.ndof),
        'pvalue': float(result.pvalue),
        'observables': result.observables,
        'pulls': pulls,
        'interpretation': result.interpretation,
    })


def loocv_report_artifact(
    channel_ablation: Mapping[str, Any],
    *,
    lnB_full: float = 26.33,
    result: List[LOOCVResult] | None = None,
    metadata: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Build ``loocv_report_v1.json`` from channel-ablation results."""
    if result is None:
        result = LeaveOneOutCV().compute_from_ablation(channel_ablation, lnB_full)
    entries = [
        {
            'dropped_channel': r.dropped_channel,
            'lnZ_without': float(r.lnZ_without),
            'lnB_without': float(r.lnB_without),
            'delta_lnB': float(r.delta_lnB),
            'beta_shift_pct': float(r.beta_shift_pct),
            'interpretation': r.interpretation,
        }
        for r in result
    ]
    max_entry = None if not entries else max(entries, key=lambda r: abs(r['delta_lnB']))

    extra = dict(metadata or {})
    config_payload = {
        'lnB_full': lnB_full,
        'channels': list(channel_ablation.get('channels', {}).keys()),
        'metadata': extra,
    }
    return _jsonify({
        'artifact_name': 'loocv_report_v1.json',
        'generated_by': extra.get(
            'generated_by',
            'htt.core.advanced_diagnostics.loocv_report_artifact',
        ),
        'git_commit': extra.get('git_commit', ''),
        'config_hash': _config_hash(config_payload),
        'input_data_hashes': list(extra.get('input_data_hashes', [])),
        'random_seed': extra.get('random_seed'),
        'wall_time_sec': extra.get('wall_time_sec'),
        'python_version': extra.get('python_version', platform.python_version()),
        'numpy_version': extra.get('numpy_version', np.__version__),
        'claim_tier': extra.get('claim_tier', 'REPORT'),
        'scope_label': extra.get('scope_label', 'report'),
        'production_allowed': False,
        'lnB_full': float(lnB_full),
        'n_dropped_channels': len(entries),
        'entries': entries,
        'most_sensitive_channel': max_entry,
    })


# ═══════════════════════════════════════════════════════════════
#  Master: Run all advanced diagnostics
# ═══════════════════════════════════════════════════════════════

def run_advanced_diagnostics(
    bi_tilt_samples: np.ndarray = None,
    bi_tilt_weights: np.ndarray = None,
    channel_ablation: dict = None,
    lnB_full: float = 26.33,
    beta_med: float = 1.36e-3,
    verbose: bool = True,
) -> Dict:
    """Run all advanced statistical diagnostics.

    Returns a dict suitable for JSON serialisation.
    """
    results = {}

    if verbose:
        print(f"\n{'='*65}")
        print(f" ADVANCED STATISTICAL DIAGNOSTICS")
        print(f"{'='*65}")

    # Strategy A: Depth Tomography
    if verbose:
        print(f"\n--- Strategy A: Depth Tomography ---")
    dt = DepthTomography()
    dt_result = dt.run()
    results['depth_tomography'] = {
        'geometric_chi2': dt_result.geometric_chi2,
        'geometric_pvalue': dt_result.geometric_pvalue,
        'kinematic_chi2': dt_result.kinematic_chi2,
        'kinematic_pvalue': dt_result.kinematic_pvalue,
        'best_fit_constant_beta': dt_result.best_fit_constant,
        'depth_gradient_alpha': dt_result.depth_gradient,
        'depth_gradient_sigma': dt_result.depth_gradient_sigma,
        'interpretation': dt_result.interpretation,
    }
    if verbose:
        print(f"  Geometric (constant): χ²={dt_result.geometric_chi2:.1f}, "
              f"p={dt_result.geometric_pvalue:.3f}")
        print(f"  Kinematic (1/(1+z)^α): χ²={dt_result.kinematic_chi2:.1f}, "
              f"p={dt_result.kinematic_pvalue:.3f}")
        print(f"  Gradient α = {dt_result.depth_gradient:.2f} ± "
              f"{dt_result.depth_gradient_sigma:.2f}")
        print(f"  {dt_result.interpretation}")

    # Strategy B: Savage-Dickey (if posterior samples provided)
    if verbose:
        print(f"\n--- Strategy B: Savage-Dickey Density Ratio ---")
    if bi_tilt_samples is not None and bi_tilt_weights is not None:
        sd = SavageDickeyRatio()
        Sigma2_samples = bi_tilt_samples[:, 0]
        sd_result = sd.compute(
            'Sigma2', Sigma2_samples, bi_tilt_weights,
            prior_lo=1e-30, prior_hi=1e-4, null_value=1e-30)
        results['savage_dickey'] = {
            'param': 'Sigma2',
            'B01': sd_result.bayes_factor_01,
            'lnB01': sd_result.log_bayes_factor,
            'param_needed': sd_result.param_needed,
            'interpretation': sd_result.interpretation,
        }
        if verbose:
            print(f"  B₀₁(Σ²=0) = {sd_result.bayes_factor_01:.4f}")
            print(f"  ln B₀₁ = {sd_result.log_bayes_factor:.2f}")
            print(f"  {sd_result.interpretation}")
    else:
        results['savage_dickey'] = {'status': 'skipped (no BI_tilt posterior samples)'}
        if verbose:
            print(f"  Skipped (no posterior samples available)")

    # Strategy C: Cross-Channel Coherence
    if verbose:
        print(f"\n--- Strategy C: Cross-Channel Coherence ---")
    cc = CrossChannelCoherence()
    cc_result = cc.run()
    results['cross_channel_coherence'] = {
        'weighted_mean_beta': cc_result.weighted_mean_beta,
        'chi2': cc_result.chi2_consistency,
        'ndof': cc_result.ndof,
        'pvalue': cc_result.pvalue,
        'tension_sigma': cc_result.tension_sigma,
        'most_discrepant': cc_result.most_discrepant,
        'estimates': {e.channel: {'beta': e.beta_estimate, 'sigma': e.sigma}
                      for e in cc_result.estimates},
        'interpretation': cc_result.interpretation,
    }
    if verbose:
        for e in cc_result.estimates:
            print(f"  {e.channel:12s} β = {e.beta_estimate:.4e} ± {e.sigma:.4e}")
        print(f"  Mean: β = {cc_result.weighted_mean_beta:.4e}")
        print(f"  χ²/ndof = {cc_result.chi2_consistency:.1f}/{cc_result.ndof}, "
              f"p = {cc_result.pvalue:.4f}")
        print(f"  {cc_result.interpretation}")

    # Posterior Predictive
    if verbose:
        print(f"\n--- Posterior Predictive Observables ---")
    pp = PosteriorPredictive()
    pp_result = pp.compute('FLRW_tilt', beta_med)
    results['posterior_predictive'] = {
        'model': pp_result.model,
        'chi2': pp_result.chi2_total,
        'ndof': pp_result.ndof,
        'pvalue': pp_result.pvalue,
        'interpretation': pp_result.interpretation,
    }
    if verbose:
        for key, o in pp_result.observables.items():
            if o['observed'] != 0:
                pull = (o['predicted'] - o['observed']) / o['sigma']
                print(f"  {key:20s} pred={o['predicted']:.4e}  "
                      f"obs={o['observed']:.4e}  pull={pull:+.1f}σ")
        print(f"  Total χ²/ndof = {pp_result.chi2_total:.1f}/{pp_result.ndof}, "
              f"p = {pp_result.pvalue:.3f}")

    # Leave-One-Out
    if channel_ablation is not None and verbose:
        print(f"\n--- Leave-One-Out Cross-Validation ---")
        loocv = LeaveOneOutCV()
        loo_results = loocv.compute_from_ablation(channel_ablation, lnB_full)
        results['leave_one_out'] = [
            {'channel': r.dropped_channel, 'delta_lnB': r.delta_lnB,
             'interpretation': r.interpretation}
            for r in loo_results
        ]
        for r in loo_results:
            print(f"  Drop {r.dropped_channel:30s} ΔlnB = {r.delta_lnB:+.1f}")

    return results
