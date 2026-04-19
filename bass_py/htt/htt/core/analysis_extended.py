#!/usr/bin/env python3
"""
analysis_extended.py — Unified Statistical & Evidence Analysis
==============================================================
Consolidates VT-09c (filling fraction), VT-09d (growing mode),
VT-09f (scenario table), VT-09g (forecast), and VE-R03a (evidence).

Classes:
  FillingFraction     — ℱ = x_V / x_max  Monte Carlo posterior
  GrowingMode         — Regular tensor growing mode defect analysis
  ScenarioTable       — Dual-framing scenario table (VT-07/08)
  ForecastTable       — Experiment prediction matrix
  EvidenceComparison  — Bayesian model selection wrapper

Depends on: ssot.py, bounds.py, evidence_models_R03a.py
Convention: VA-02 (Σ²_std = σ_{ab}σ^{ab}/(6H²))
"""
import numpy as np
import json
from pathlib import Path

from htt.core.ssot import C, sigma_H_from_Sig2
from htt.core.bounds import (B_sigma as B_sigma_lin, B_sigma_corrected, Sig2_max_MES,
                    eps1_from_beta, beta_safe, Sig2_BV, filling_fraction)

__all__ = ['FillingFraction', 'GrowingMode', 'ScenarioTable',
           'ForecastTable', 'EvidenceComparison']

# ─── SSOT scenarios ──────────────────────────────────────
SCENARIOS = {
    'S0':  {'eps1': 0.0,       'beta': 0.0,       'desc': 'FLRW'},
    'S1':  {'eps1': 1.233e-3,  'beta': 0.0,       'desc': 'Kinematic dipole'},
    'S2a': {'eps1': 1.476e-3,  'beta': 1.334e-3,  'desc': 'CatWISE'},
    'S2b': {'eps1': 1.233e-3,  'beta': 1.334e-3,  'desc': 'Kinematic+tilt'},
    'S2c': {'eps1': 3.296e-3,  'beta': 1.334e-3,  'desc': 'Radio'},
    'S3':  {'eps1': 1.476e-3,  'beta': 1.334e-3,  'desc': 'Full anomaly'},
}


# ═══════════════════════════════════════════════════════════
class FillingFraction:
    """Monte Carlo filling fraction ℱ = x_V / x_max.
    
    From VT-09c: propagates observational uncertainties through
    the defect variable ratio.
    
    x_V  = (1+w)/4 × sinh²[ε₁/(1+η_u̇)]    (tilt contribution)
    x_max = Σ²_max(ε₁_ref) = (3/2)[B_σ^corr(ε₁_ref)]²
    """
    
    def __init__(self, w=0.0, eta=C.eta_udot):
        self.w = w
        self.eta = eta
    
    def x_V(self, eps1):
        """Tilt defect variable: Ω_tilt = (1+w)Ω_m sinh²β.

        Physics: the geometry-frame energy density includes a tilt
        contribution ρ_tilt = (ρ+p)sinh²β. After dividing by 3H²,
        this gives Ω_tilt = (1+w)Ω_m sinh²β (Eq. 2.15).

        The safe-route β = ε₁/(1+η_u̇) is used (VT-07 corrected).

        Parameters
        ----------
        eps1 : float or array
            Total observed dipole amplitude ε₁ (dimensionless ΔT/T).

        Returns
        -------
        float or array
            Tilt defect Ω_tilt. At S3: ~2.69×10⁻⁷.

        References
        ----------
        Eq. (2.15), VT-07 §3.5, VN-05 §2.
        """
        beta = eps1 / (1.0 + self.eta)
        return (1.0 + self.w) * C.Omega_m * np.sinh(beta)**2
    
    def x_max(self, eps1_ref=None):
        """MES ceiling at reference ε₁.
        If eps1_ref is None, must be supplied by caller.
        """
        if eps1_ref is None:
            raise ValueError("eps1_ref must be specified")
        return Sig2_max_MES(eps1_ref)
    
    def F(self, eps1, eps1_ref=None):
        """Point estimate of ℱ = x_V / x_max.
        By default, both x_V and x_max are evaluated at the same ε₁
        (self-consistent definition, Eq. 7.15).
        """
        if eps1_ref is None:
            eps1_ref = eps1
        xm = self.x_max(eps1_ref)
        return self.x_V(eps1) / xm if xm > 0 else np.inf
    
    def mc_posterior(self, scenario='S3', N=100000, seed=42,
                     *, pre_drawn_eps=None):
        """Monte Carlo posterior for ℱ.

        Propagates uncertainties in ε₁, ε₂, ε₃ through the ℱ formula.
        Returns (samples, median, q16, q84, q025, q975).

        Parameters
        ----------
        scenario, N, seed
            As before — back-compat with the pre-W9 signature.
        pre_drawn_eps
            Optional triple ``(eps1_samp, eps2_samp, eps3_samp)`` of
            equal-length 1-D arrays. When supplied, the internal
            ``np.random.default_rng(seed)`` draws are skipped and the
            caller-supplied stream is used directly. This closes
            W7 FM2 (tsc/htt stream-alignment coupling): the bridge can
            draw the triple once and pass it to both the htt path and
            its tsc re-derivation, removing the implicit assumption
            that htt's internal rng call order never changes.
        """
        if pre_drawn_eps is not None:
            e1_samp, e2_samp, e3_samp = pre_drawn_eps
            e1_samp = np.asarray(e1_samp)
            e2_samp = np.asarray(e2_samp)
            e3_samp = np.asarray(e3_samp)
            if not (e1_samp.shape == e2_samp.shape == e3_samp.shape):
                raise ValueError(
                    "pre_drawn_eps arrays must share the same shape; "
                    f"got {e1_samp.shape}, {e2_samp.shape}, {e3_samp.shape}"
                )
            N = int(e1_samp.shape[0])
            e1_samp = np.clip(e1_samp, 0, None)
        else:
            rng = np.random.default_rng(seed)
            sc = SCENARIOS[scenario]

            # Sample ε₁ (split-normal around scenario value)
            e1_samp = sc['eps1'] + rng.normal(0, 0.30e-3, N)
            e1_samp = np.clip(e1_samp, 0, None)

            # Sample ε₂, ε₃ (Gaussian)
            e2_samp = rng.normal(C.eps2, 1.5e-6, N)
            e3_samp = rng.normal(C.eps3, 2.0e-6, N)
        
        # Reference ε₁ for x_max (kinematic dipole = 1.233e-3 from SSOT)
        e1_ref = C.eps1_kin
        
        # Compute ℱ samples: x_V = (1+w)Ω_m sinh²(β_sr)
        xV = (1 + self.w) * C.Omega_m * np.sinh(e1_samp / (1 + self.eta))**2
        Bs_c = (1 + 2.69 * e1_ref) * ((5./3)*e1_ref + 3*e2_samp + (3./7)*e3_samp)
        xmax = 1.5 * Bs_c**2
        
        F_samp = xV / xmax
        F_samp = F_samp[np.isfinite(F_samp) & (F_samp > 0)]
        
        med = np.median(F_samp)
        q16, q84 = np.percentile(F_samp, [16, 84])
        q025, q975 = np.percentile(F_samp, [2.5, 97.5])
        
        return F_samp, med, q16, q84, q025, q975
    
    def bayes_factor(self, F_samp, threshold=0.0):
        """Savage-Dickey Bayes factor: P(ℱ > threshold) / P(ℱ ≤ threshold)."""
        above = np.sum(F_samp > threshold)
        below = len(F_samp) - above
        return above / max(below, 1)


# ═══════════════════════════════════════════════════════════
class GrowingMode:
    """Regular tensor growing mode analysis (VT-09d).
    
    The growing mode in BVIIh has T₂^grow = 5.5 (±20%).
    At (σ/H)₀ ~ 10⁻⁶, it produces a detectable CMB quadrupole.
    """
    
    T2_GROW = 5.5
    T2_GROW_ERR = 0.20  # fractional
    
    def D2_shear(self, sigma_over_H):
        """D₂^shear from growing tensor mode."""
        eps2_shear = sigma_over_H * self.T2_GROW
        return (6.0 / (2*np.pi)) * (eps2_shear * C.T0_uK)**2
    
    def Sigma2_from_sigma(self, sigma_over_H):
        """Convert σ/H to Σ²_std = (3/2)(σ/Θ)² = (1/6)(σ/H)²."""
        return sigma_over_H**2 / 6.0
    
    def defect_from_shear(self, sigma_over_H):
        """Compute defect variable from (σ/H)₀.
        
        Returns dict with Σ², D₂^shear, x/x_max.
        """
        Sig2 = self.Sigma2_from_sigma(sigma_over_H)
        D2 = self.D2_shear(sigma_over_H)
        x_max = Sig2_max_MES(C.eps1_kin)
        
        return {
            'sigma_H': sigma_over_H,
            'Sigma2': Sig2,
            'D2_shear': D2,
            'D2_over_obs': D2 / C.D2_obs,
            'x_over_xmax': Sig2 / x_max if x_max > 0 else np.inf,
        }
    
    def detection_window(self, D2_threshold=10.0):
        """(σ/H) range where D₂^shear > threshold.
        
        Default threshold: 10 μK² (detectable above cosmic variance).
        """
        # D₂ = (6/2π)(T₂ σ/H T₀)² = (3/π)(5.5 σ/H × 2.7255e6)²
        # σ/H = √(D₂ × π / (3 × 5.5² × T₀²))
        sigma_min = np.sqrt(D2_threshold * np.pi / (3 * self.T2_GROW**2 * C.T0_uK**2))
        sigma_max = np.sqrt(C.D2_obs * np.pi / (3 * self.T2_GROW**2 * C.T0_uK**2))
        return sigma_min, sigma_max


# ═══════════════════════════════════════════════════════════
class ScenarioTable:
    """Dual-framing scenario table (VT-09f).
    
    Computes B_σ, Σ²_max, β_max, x_V, ℱ, frame-attribution bias
    for all scenarios, with both original and VT-07-corrected values.
    """
    
    def __init__(self):
        self.ff = FillingFraction()
    
    def compute(self, scenario_name='S3'):
        """Full computation for a single scenario.
        
        Returns dict with all quantities.
        """
        sc = SCENARIOS[scenario_name]
        e1 = sc['eps1']; beta = sc['beta']
        
        # Original (uncorrected)
        Bs_orig = B_sigma_lin(e1)
        S2_orig = 1.5 * Bs_orig**2
        beta_orig = e1  # no η correction
        
        # VT-07 corrected
        Bs_corr = B_sigma_corrected(e1)
        S2_corr = 1.5 * Bs_corr**2
        beta_corr = beta_safe(e1)
        
        # Frame-attribution bias
        bias = Bs_corr - Bs_orig
        bias_frac = bias / Bs_orig if Bs_orig > 0 else 0
        
        # Filling fraction
        F_orig = self.ff.F(e1) if e1 > 0 else 0
        
        return {
            'scenario': scenario_name, 'eps1': e1, 'beta': beta,
            'B_sigma_orig': Bs_orig, 'B_sigma_corr': Bs_corr,
            'Sigma2_orig': S2_orig, 'Sigma2_corr': S2_corr,
            'beta_max_orig': beta_orig, 'beta_max_corr': beta_corr,
            'bias': bias, 'bias_frac': bias_frac,
            'F': F_orig,
        }
    
    def compute_all(self):
        """Compute for all scenarios. Returns dict of dicts."""
        return {sn: self.compute(sn) for sn in SCENARIOS}


# ═══════════════════════════════════════════════════════════
class ForecastTable:
    """Experiment prediction matrix (VT-09g).
    
    Maps 7 framework predictions to ~10 experiments.
    """
    
    PREDICTIONS = [
        'P1: Dipole excess > kinematic',
        'P2: Dipole direction aligned',
        'P3: Tilt rapidity β ~ 10⁻³',
        'P4: Vorticity (ω/H) < 5e-11',
        'P5: Quadrupole suppression',
        'P6: Growing mode signature',
        'P7: Scale-dependent anisotropy',
    ]
    
    EXPERIMENTS = {
        'Euclid DR1':      {'date': 'Oct 2026', 'tests': ['P1','P2','P3']},
        'Vera Rubin LSST':  {'date': '2025+',   'tests': ['P1','P2','P7']},
        'SKA Phase 1':      {'date': '2028+',   'tests': ['P1','P2','P3']},
        'Simons Obs':       {'date': 'operational', 'tests': ['P4','P5','P6']},
        'LiteBIRD':         {'date': '~Q1 2033', 'tests': ['P4','P5','P6']},
        'SPHEREx':          {'date': '2025+',   'tests': ['P1','P7']},
    }
    
    def golden_experiments(self, threshold=3):
        """Experiments testing ≥ threshold predictions."""
        return {name: info for name, info in self.EXPERIMENTS.items()
                if len(info['tests']) >= threshold}
    
    def matrix(self):
        """Returns the prediction × experiment binary matrix."""
        preds = self.PREDICTIONS
        exps = list(self.EXPERIMENTS.keys())
        M = np.zeros((len(preds), len(exps)), dtype=int)
        for j, (ename, einfo) in enumerate(self.EXPERIMENTS.items()):
            for test in einfo['tests']:
                idx = int(test[1]) - 1
                if 0 <= idx < len(preds):
                    M[idx, j] = 1
        return preds, exps, M


# ═══════════════════════════════════════════════════════════
class EvidenceComparison:
    """Bayesian model selection across the Bianchi classification.
    
    Wraps evidence_models_R03a.py for batch nested sampling,
    master table generation, and prior sensitivity automation.
    """
    
    # All 16 model classes (15 Bianchi + 1 FLRW reference)
    MODEL_REGISTRY = None  # Lazy-loaded
    
    def __init__(self, channels='abcdefh', obs=None):
        self.channels = channels
        self.obs = obs  # custom ObsData, or None for default
        self._load_models()
    
    def _load_models(self):
        """Lazy-load evidence_models to avoid circular imports."""
        if EvidenceComparison.MODEL_REGISTRY is not None:
            return

        try:
            from evidence_models import (
                FLRW, FLRW_tilt,
                BianchiI_orth, BianchiVII0_orth, BianchiII_orth,
                BianchiVI0_orth, BianchiVIII_orth, BianchiIX_orth,
                BianchiVIIh_orth, BianchiVIIh_orth_grow,
                BianchiI_tilt, BianchiV_tilt, BianchiIII_tilt,
                BianchiIX_tilt, BianchiVIIh_tilt, BianchiVIIh_tilt_grow,
            )
        except ImportError:
            from evidence_models_R03a import (
                FLRW, FLRW_tilt,
                BianchiI_orth, BianchiVII0_orth, BianchiII_orth,
                BianchiVI0_orth, BianchiVIII_orth, BianchiIX_orth,
                BianchiVIIh_orth, BianchiVIIh_orth_grow,
                BianchiI_tilt, BianchiV_tilt, BianchiIII_tilt,
                BianchiIX_tilt, BianchiVIIh_tilt, BianchiVIIh_tilt_grow,
            )
        
        EvidenceComparison.MODEL_REGISTRY = {
            'FLRW':             FLRW,
            'FLRW_tilt':        FLRW_tilt,
            'BI_orth':          BianchiI_orth,
            'BVII0_orth':       BianchiVII0_orth,
            'BII_orth':         BianchiII_orth,
            'BVI0_orth':        BianchiVI0_orth,
            'BVIII_orth':       BianchiVIII_orth,
            'BIX_orth':         BianchiIX_orth,
            'BVIIh_orth':       BianchiVIIh_orth,
            'BVIIh_orth_grow':  BianchiVIIh_orth_grow,
            'BI_tilt':          BianchiI_tilt,
            'BV_tilt':          BianchiV_tilt,
            'BIII_tilt':        BianchiIII_tilt,
            'BIX_tilt':         BianchiIX_tilt,
            'BVIIh_tilt':       BianchiVIIh_tilt,
            'BVIIh_tilt_grow':  BianchiVIIh_tilt_grow,
        }
    
    def flrw_evidence(self, channels=None):
        """FLRW reference log-evidence (analytic)."""
        ch = channels or self.channels
        return self.MODEL_REGISTRY['FLRW'](obs=self.obs, channels=ch).log_evidence()
    
    def run_single(self, tag, nlive=500, dlogz=0.1, channels=None):
        """Run nested sampling for a single model.
        
        Returns dict with lnZ, err, lnB, neff, samples.
        """
        import dynesty
        from dynesty.utils import resample_equal
        
        ch = channels or self.channels
        Mcls = self.MODEL_REGISTRY[tag]
        m = Mcls(obs=self.obs, channels=ch)
        Z0 = self.flrw_evidence(ch)
        
        if m.ndim == 0:
            return {'tag': tag, 'lnZ': Z0, 'err': 0, 'lnB': 0, 'neff': 0}
        
        sampler = dynesty.NestedSampler(
            m.log_likelihood, m.prior_transform, m.ndim,
            nlive=nlive, walks=30, sample='rwalk')
        sampler.run_nested(dlogz=dlogz, print_progress=False)
        res = sampler.results
        
        eq = resample_equal(res.samples, np.exp(res.logwt - res.logwt.max()))
        
        return {
            'tag': tag, 'channels': ch,
            'lnZ': float(res.logz[-1]),
            'err': float(res.logzerr[-1]),
            'lnB': float(res.logz[-1]) - Z0,
            'neff': len(eq),
            'niter': int(res.niter),
            'param_names': m.param_names,
            'ndim': m.ndim,
            'eq_samples': eq,
        }
    
    def run_all(self, nlive_orth=500, nlive_tilt=800,
                dlogz_orth=0.1, dlogz_tilt=0.05):
        """Run all 14 models. Returns list of result dicts."""
        results = []
        for tag in list(self.MODEL_REGISTRY.keys()):
            if tag == 'FLRW':
                continue
            is_tilt = 'tilt' in tag
            nl = nlive_tilt if is_tilt else nlive_orth
            dl = dlogz_tilt if is_tilt else dlogz_orth
            r = self.run_single(tag, nlive=nl, dlogz=dl)
            results.append(r)
        return results
    
    def prior_sensitivity(self, tag, variants, nlive=500, dlogz=0.1):
        """Run prior sensitivity for one model with variant priors.
        
        variants: list of (name, sig2_range, beta_range) tuples.
        Returns list of {name, lnB, delta} dicts.
        """
        Mcls = self.MODEL_REGISTRY[tag]
        Z0 = self.flrw_evidence()
        
        # Fiducial
        r_fid = self.run_single(tag, nlive=nlive, dlogz=dlogz)
        results = [{'name': 'Fiducial', 'lnB': r_fid['lnB'], 'delta': 0.0}]
        
        for vname, sig2_range, beta_range in variants:
            class V(Mcls):
                _sr = sig2_range; _br = beta_range
                def prior_transform(self, u):
                    th = super().prior_transform(u)
                    if self._sr:
                        si = self.param_names.index('Sigma2')
                        th[si] = 10.**(u[si]*(self._sr[1]-self._sr[0]) + self._sr[0])
                    if self._br:
                        bi = self.param_names.index('beta')
                        th[bi] = 10.**(u[bi]*(self._br[1]-self._br[0]) + self._br[0])
                    return th
            
            import dynesty
            mv = V(channels=self.channels)
            sampler = dynesty.NestedSampler(
                mv.log_likelihood, mv.prior_transform, mv.ndim,
                nlive=nlive, walks=30, sample='rwalk')
            sampler.run_nested(dlogz=dlogz, print_progress=False)
            lnB = float(sampler.results.logz[-1]) - Z0
            
            results.append({
                'name': vname, 'lnB': round(lnB, 2),
                'delta': round(lnB - r_fid['lnB'], 2),
            })
        
        return results
    
    def master_table(self, results):
        """Generate ranked master table from run_all results.
        
        Returns sorted list of dicts with rank, tier, Jeffreys label.
        """
        ranked = sorted(results, key=lambda r: r['lnB'], reverse=True)
        
        for i, r in enumerate(ranked, 1):
            r['rank'] = i
            lnB = r['lnB']
            if lnB > 5:
                r['tier'] = 'Decisive'
            elif lnB > -5:
                r['tier'] = 'Negligible'
            else:
                r['tier'] = 'Excluded'
        
        return ranked
    
    def to_json(self, results, path):
        """Save results to JSON (excluding numpy arrays)."""
        serialisable = []
        for r in results:
            d = {k: v for k, v in r.items() if k != 'eq_samples'}
            if 'eq_samples' in r and r['eq_samples'] is not None:
                d['n_samples'] = len(r['eq_samples'])
            serialisable.append(d)
        
        with open(path, 'w') as f:
            json.dump(serialisable, f, indent=2)
