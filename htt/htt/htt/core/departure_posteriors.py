#!/usr/bin/env python3
"""
departure_posteriors.py — Three-layer pushforward engine (IS-01)
=================================================================
Post-processes dynesty posterior samples into the departure-variable
framework:

  Layer 1  x  — comparator-conditioned algebraic departure
  Layer 2  Q  — policy-normalized HTT posterior score (ceiling-normalised)
  Layer 3  Π_HTT / P_post — model-conditional posterior exceedance

Plus derived physical observables: q₀ (apparent deceleration),
v_tilt (tilt velocity), Ω_tilt (tilt density parameter).

This module is a legacy HTT posterior diagnostic export.  It sits DOWNSTREAM
of evidence_models_R03a.py and does NOT modify any likelihood.  It only
transforms posterior samples.  Its posterior exceedance outputs are not MIO Pi
and are not report-card sources.

Depends on: ssot.py, bounds.py, tilted_flrw.py
Convention: VA-02 (Σ²_std = σ_{ab}σ^{ab}/(6H²))
"""
import numpy as np
from htt.core.ssot import C, omega_tilt
from htt.core.bounds import B_sigma_corrected, Sig2_max_MES

# PR-124: active MES consumers traverse the typed successor registry
# (common.mes_theorem_authority is the live authority; legacy values are
# labeled non-authoritative reproduction, see legacy_reproduction_coefficients).
from common.mes_successor_registry import current_mes_successor_registry

_MES_SUCCESSOR = current_mes_successor_registry().successor
_MES_SUCCESSOR_ID = _MES_SUCCESSOR.successor_id

__all__ = [
    'DeparturePosterior',
    'weighted_quantile', 'weighted_hpd',
    'comparator_sensitivity',
]

# ─── Weighted statistics helpers ──────────────────────────────

def weighted_quantile(values, quantile, weights):
    """Compute a weighted quantile via sorted CDF interpolation.

    Parameters
    ----------
    values : array_like
        Sample values.
    quantile : float
        Quantile in [0, 1].
    weights : array_like
        Sample weights (need not be normalised).

    Returns
    -------
    float
        Weighted quantile.
    """
    values = np.asarray(values, dtype=float)
    weights = np.asarray(weights, dtype=float)
    idx = np.argsort(values)
    sv = values[idx]
    sw = weights[idx]
    cum = np.cumsum(sw)
    cum /= cum[-1]
    return float(np.interp(quantile, cum, sv))


def weighted_hpd(values, weights, level=0.68):
    """Highest posterior density interval from weighted samples.

    Scans sorted sample pairs to find the shortest interval containing
    at least `level` fraction of the total weight.

    Parameters
    ----------
    values : array_like
        Sample values.
    weights : array_like
        Sample weights (need not be normalised).
    level : float
        Credible level (default 0.68).

    Returns
    -------
    tuple of float
        (lower, upper) bounds of the HPD interval.
    """
    values = np.asarray(values, dtype=float)
    weights = np.asarray(weights, dtype=float)
    idx = np.argsort(values)
    sv = values[idx]
    sw = weights[idx]
    # Normalise weights so they sum to 1
    sw = sw / sw.sum()
    cum = np.cumsum(sw)
    # cum[i] = total normalised weight up to and including sample i

    best_width = np.inf
    lo, hi = sv[0], sv[-1]

    n = len(sv)
    for i in range(n):
        # Weight from i to j inclusive = cum[j] - cum[i] + sw[i]
        # We want this >= level, so cum[j] >= cum[i] - sw[i] + level
        threshold = cum[i] - sw[i] + level
        if threshold > 1.0:
            break  # no valid j exists for this i
        j = np.searchsorted(cum, threshold)
        if j >= n:
            j = n - 1
        w = sv[j] - sv[i]
        if w < best_width:
            best_width = w
            lo, hi = sv[i], sv[j]

    return (float(lo), float(hi))


# ─── Core engine ──────────────────────────────────────────────

class DeparturePosterior:
    """Three-layer pushforward from dynesty samples to x/Q/Π.

    This class takes the raw weighted samples from a dynesty nested
    sampling run (for any model in the evidence_models_R03a registry)
    and computes all derived departure quantities.

    Parameters
    ----------
    model_tag : str
        Model identifier, e.g. 'FLRW_tilt', 'BI_tilt', 'BVIIh_orth'.
    samples : ndarray (N, ndim)
        Raw dynesty samples.
    logwt : ndarray (N,)
        Log-weights from dynesty (logwt = logz_new - logz_old + logL).
        If None, equal-weighted samples are assumed (post-resample).
    param_names : list of str
        Parameter names matching columns of `samples`.
    comparator : str
        Reporting comparator: 'flat' | 'closed' | 'matched'.
    w : float
        Equation of state (default 0 for dust).
    Om : float
        Matter density parameter Ω_m.

    Attributes
    ----------
    weights : ndarray
        Normalised posterior weights.
    N_eff : float
        Effective sample size (Kish ESS).
    """

    COMPARATORS = ('flat', 'closed', 'matched')

    def __init__(self, model_tag, samples, logwt=None, param_names=None,
                 comparator='flat', w=0.0, Om=None, inactive_params=None):
        self.model_tag = model_tag
        self.comparator = comparator
        self.w = w
        self.Om = Om if Om is not None else C.Omega_m
        self.inactive_params = set(inactive_params) if inactive_params else set()

        if comparator not in self.COMPARATORS:
            raise ValueError(
                f"comparator must be one of {self.COMPARATORS}, got '{comparator}'")

        samples = np.atleast_2d(samples)

        # Weights
        if logwt is not None:
            logwt = np.asarray(logwt, dtype=float)
            self.weights = np.exp(logwt - logwt.max())
            self.weights /= self.weights.sum()
        else:
            n = len(samples)
            self.weights = np.full(n, 1.0 / n)

        self.N_eff = 1.0 / np.sum(self.weights**2)

        # Extract named parameter columns
        self.param_names = list(param_names) if param_names else []
        self._extract_params(samples)

    def _extract_params(self, samples):
        """Pull named columns from the sample array."""
        def _col(name):
            if name in self.param_names:
                return samples[:, self.param_names.index(name)].copy()
            return np.zeros(len(samples))

        self.beta = _col('beta')
        self.Sigma2 = _col('Sigma2')
        self.W2 = _col('W2')
        self.Omega_K = _col('Omega_k')
        # Some models use 'Omega_K' (capital K)
        if 'Omega_K' in self.param_names and np.all(self.Omega_K == 0):
            self.Omega_K = _col('Omega_K')

    # ─── Layer 1: Departure variable x ────────────────────────

    def compute_x(self):
        """Comparator-conditioned algebraic departure identity per sample.

        x = Σ²_std − W²_std + Ω_tilt + Ω_{k,aniso}

        Uses the MATTER-FRAME convention for Ω_tilt because self.Om
        is the Planck-fitted matter-frame density parameter (0.3153).

        For the geometry-frame convention (used by BackgroundState.x),
        see htt.core.ssot.omega_tilt(..., frame='geometry').
        The conventions have been compared only at historical observational
        inputs that are unavailable to active code.  No numerical agreement
        claim is carried forward here.

        Note: this is an algebraic pushforward under the chosen comparator
        and frame convention, not a frame-independent exact identity.
        The frame difference grows with β (< 0.02% for β < 0.01,
        ~9% at β = 0.3) but is negligible in the posterior regime.

        Returns
        -------
        ndarray
            Departure variable x for each sample.
        """
        # Use shared SSOT function with explicit frame convention
        Or = np.full_like(self.beta, C.Omega_r)
        self.Omega_tilt = omega_tilt(self.Om, Or, self.beta, frame='matter')
        self.Omega_k_aniso = self._aniso_curvature()
        self.x = self.Sigma2 - self.W2 + self.Omega_tilt + self.Omega_k_aniso
        return self.x

    # EGS3 framework upgrade (additive): the graded comparator preserves sector
    # identity, so the signed x_C is a derived linear summary x = <c, g>,
    # c = (+1, -1, +1, +1). This removes the x_C sign-cancellation ambiguity
    # (a large Sigma^2 and W^2 can cancel in x but stay visible in g) and the
    # F = x/x_max < 0 pathology (per-sector filling uses the nonnegative sectors).
    # x is unchanged: g is a view, not a redefinition.
    GRADED_SECTORS = ("Sigma2", "W2", "Omega_tilt", "Omega_k_aniso")
    GRADED_SIGNS = (1.0, -1.0, 1.0, 1.0)

    def compute_graded_comparator(self):
        """Return the graded comparator sectors g and verify x = <c, g> exactly.

        g = (Sigma^2_std, W^2_std, Omega_tilt, Omega_{k,aniso}); the signed
        comparator x is recovered bit-identically as the linear summary
        x = Sigma^2 - W^2 + Omega_tilt + Omega_{k,aniso}."""
        if not hasattr(self, "x"):
            self.compute_x()
        g = {
            "Sigma2": self.Sigma2,
            "W2": self.W2,
            "Omega_tilt": self.Omega_tilt,
            "Omega_k_aniso": self.Omega_k_aniso,
        }
        x_from_g = g["Sigma2"] - g["W2"] + g["Omega_tilt"] + g["Omega_k_aniso"]
        # bit-identical reconstruction of the signed summary
        assert np.array_equal(x_from_g, self.x), "graded comparator must reconstruct x exactly"
        self.graded_comparator = g
        return g

    def _aniso_curvature(self):
        """Model- and comparator-dependent anisotropic curvature.

        flat:    Ω_{k,aniso} = Ω_K  (full curvature is "anisotropic")
        closed:  Ω_{k,aniso} = Ω_K + |Ω_K|  (offset so closed FLRW → 0)
        matched: Ω_{k,aniso} = 0  (curvature absorbed into comparator)
        """
        if self.comparator == 'matched':
            return np.zeros_like(self.Omega_K)
        elif self.comparator == 'closed':
            # Closed FLRW has Ω_K < 0; shift so that the reference state → 0
            return self.Omega_K + np.abs(self.Omega_K)
        else:  # flat
            return self.Omega_K.copy()

    # ─── Layer 2: policy-normalized HTT posterior score Q ─────

    # Known inactive parameters that feed into x but are not
    # constrained by the likelihood (prior-driven artifacts).
    _X_FEEDING_PARAMS = {'Omega_k', 'Omega_K', 'W2'}

    def compute_Q(self, eps1_ceiling=None):
        """Policy-normalized HTT posterior score Q = x / x_max.

        The ceiling x_max is the MES algebraic ceiling evaluated at a
        reference ε₁.  This is an *adopted* ceiling, not a proven
        strong ceiling theorem.

        Guards (A2 fix):
          - If x < 0 for the weighted mean → Q_status = 'defect_negative'
          - If Q > 1 for the weighted mean → Q_status = 'super_ceiling'
          - If a likelihood-inactive parameter dominates |x| → Q_status = 'prior_contaminated'
          - Otherwise → Q_status = 'identified'

        When Q_status is not 'identified', Q values are still computed
        (they are mathematically well-defined) but the status flag warns
        that they should NOT be interpreted as data-constrained filling,
        model evidence, or MIO diagnostic certification.

        Parameters
        ----------
        eps1_ceiling : float, optional
            Observed ε₁ for MES ceiling computation.  Default: kinematic
            dipole ε₁ = 1.233e-3 from SSOT.

        Returns
        -------
        ndarray
            Policy-normalized HTT posterior score Q for each sample.
        """
        if not hasattr(self, 'x'):
            self.compute_x()

        if eps1_ceiling is None:
            eps1_ceiling = C.eps1_kin

        self.x_max = float(Sig2_max_MES(eps1_ceiling))
        self.eps1_ceiling = eps1_ceiling

        if self.x_max <= 0:
            self.Q = np.full_like(self.x, np.nan)
        else:
            self.Q = self.x / self.x_max

        # Classify Q status
        self.Q_status = self._classify_Q_status()
        return self.Q

    def _classify_Q_status(self):
        """Classify the physical reliability of Q.

        Returns one of:
          'identified'          — Q is data-constrained; safe to report
          'defect_negative'     — weighted mean x < 0 (vorticity/curvature dominated)
          'super_ceiling'       — weighted mean Q > 1 (x exceeds adopted MES ceiling)
          'prior_contaminated'  — a likelihood-inactive param dominates x
        """
        x_mean = float(np.average(self.x, weights=self.weights))
        Q_mean = float(np.average(self.Q, weights=self.weights))

        # Check for prior contamination: inactive params feeding x
        contaminated_params = self.inactive_params & self._X_FEEDING_PARAMS
        if contaminated_params:
            # Estimate the contribution of inactive params to |x|
            inactive_contribution = 0.0
            if 'Omega_k' in contaminated_params or 'Omega_K' in contaminated_params:
                inactive_contribution += float(np.average(
                    np.abs(self.Omega_k_aniso), weights=self.weights))
            if 'W2' in contaminated_params:
                inactive_contribution += float(np.average(
                    np.abs(self.W2), weights=self.weights))
            total_x_abs = float(np.average(np.abs(self.x), weights=self.weights))
            if total_x_abs > 0 and inactive_contribution / total_x_abs > 0.1:
                return 'prior_contaminated'

        if x_mean < 0:
            return 'defect_negative'
        if Q_mean > 1.0:
            return 'super_ceiling'
        return 'identified'

    # ─── Layer 3: HTT posterior exceedance Π_HTT / P_post ─────

    def compute_Pi(self, q_stars=(0.01, 0.05, 0.1, 0.5)):
        """HTT model-conditional posterior exceedance probabilities.

        Π_HTT(q*) = P_post(Q > q*) = Σ_i w_i 𝟙[Q_i > q*].
        This is not MIO Pi, which is an empirical diagnostic exceedance curve.

        Parameters
        ----------
        q_stars : tuple of float
            Threshold values for exceedance computation.

        Returns
        -------
        dict
            {q_star: Π_HTT(q_star)} mapping.
        """
        if not hasattr(self, 'Q'):
            self.compute_Q()

        self.Pi = {}
        for qs in q_stars:
            self.Pi[qs] = float(np.sum(self.weights[self.Q > qs]))
        return self.Pi

    # ─── Derived physical observables ─────────────────────────

    def compute_q0(self, d_Mpc=40.0, H0=None):
        """Pushforward for apparent deceleration parameter q₀.

        q₀_apparent = q₀_true + Δq_tilt(β, d)
        where Δq = (β/9)(λ_H/d)³.

        Parameters
        ----------
        d_Mpc : float
            Comoving survey depth in Mpc.
        H0 : float, optional
            Hubble constant.  Default: SSOT value.

        Returns
        -------
        ndarray
            Apparent q₀ for each sample.
        """
        from htt.core.tilted_flrw import Delta_q

        if H0 is None:
            H0 = C.h * 100.0
        self.Dq_tilt = np.array([Delta_q(b, d_Mpc, H0) for b in self.beta])
        q0_true = 0.5 * self.Om - (1.0 - self.Om)  # flat ΛCDM
        self.q0_apparent = q0_true + self.Dq_tilt
        self.q0_true = q0_true
        return self.q0_apparent

    def compute_v_tilt(self):
        """Derived tilt velocity.

        v = c × tanh(β) [km/s].

        This is a derived physical observable, NOT a departure variable.

        Returns
        -------
        ndarray
            Tilt velocity in km/s for each sample.
        """
        c_km_s = 299792.458
        self.v_tilt = c_km_s * np.tanh(self.beta)
        return self.v_tilt

    # ─── Statistical summaries ────────────────────────────────

    def weighted_summary(self, arr):
        """Weighted posterior summary statistics.

        Returns
        -------
        dict
            Keys: mean, std, median, hpd_68, hpd_95.
        """
        w = self.weights
        mean = float(np.average(arr, weights=w))
        var = float(np.average((arr - mean)**2, weights=w))
        med = weighted_quantile(arr, 0.5, w)
        hpd68 = weighted_hpd(arr, w, 0.68)
        hpd95 = weighted_hpd(arr, w, 0.95)
        return {
            'mean': mean,
            'std': float(np.sqrt(max(var, 0))),
            'median': med,
            'hpd_68': list(hpd68),
            'hpd_95': list(hpd95),
        }

    # ─── Full report ──────────────────────────────────────────

    def full_report(self, eps1_ceiling=None, d_Mpc=40.0, H0=None,
                    q_stars=(0.01, 0.05, 0.1, 0.5)):
        """Run all computations and return complete JSON-serialisable dict.

        Parameters
        ----------
        eps1_ceiling : float, optional
            ε₁ for MES ceiling.  Default: kinematic dipole.
        d_Mpc : float
            Survey depth for q₀ pushforward.
        H0 : float, optional
            Hubble constant.
        q_stars : tuple of float
            Exceedance thresholds.

        Returns
        -------
        dict
            Complete departure report with all three layers.
        """
        self.compute_x()
        self.compute_Q(eps1_ceiling)
        self.compute_Pi(q_stars)
        self.compute_q0(d_Mpc, H0)
        self.compute_v_tilt()

        report = {
            'model': self.model_tag,
            'comparator': self.comparator,
            'N_eff': round(float(self.N_eff), 1),
            'layer_1_departure': {
                'x': self.weighted_summary(self.x),
                'components': {
                    'Sigma2': self.weighted_summary(self.Sigma2),
                    'W2': self.weighted_summary(self.W2),
                    'Omega_tilt': self.weighted_summary(self.Omega_tilt),
                    'Omega_k_aniso': self.weighted_summary(self.Omega_k_aniso),
                },
            },
            'layer_2_policy_normalized_score': {
                'Q': self.weighted_summary(self.Q),
                'Q_status': self.Q_status,
                'x_max': float(self.x_max),
                'eps1_ceiling': float(self.eps1_ceiling),
                'ceiling_status': 'adopted_MES_algebraic',
            },
            # Backward-compatible aliases remain for legacy consumers. They are
            # HTT posterior summaries, not MIO diagnostic report-card fields.
            'layer_2_occupancy': {
                'Q': self.weighted_summary(self.Q),
                'Q_status': self.Q_status,
                'semantic_alias': 'layer_2_policy_normalized_score',
                'mio_diagnostic_compatible': False,
            },
            'layer_3_htt_posterior_exceedance': {
                'Pi_HTT': {str(k): v for k, v in self.Pi.items()},
                'P_post': {str(k): v for k, v in self.Pi.items()},
                'mio_pi_compatible': False,
                'q_stars': list(q_stars),
            },
            'layer_3_exceedance': {
                'Pi': {str(k): v for k, v in self.Pi.items()},
                'semantic_alias': 'layer_3_htt_posterior_exceedance',
                'mio_pi_compatible': False,
            },
            'derived_observables': {
                'q0_apparent': self.weighted_summary(self.q0_apparent),
                'q0_true': float(self.q0_true),
                'Dq_tilt': self.weighted_summary(self.Dq_tilt),
                'v_tilt_km_s': self.weighted_summary(self.v_tilt),
                'beta': self.weighted_summary(self.beta),
                'd_Mpc': d_Mpc,
            },
        }
        return report


# ─── Comparator sensitivity ──────────────────────────────────

def comparator_sensitivity(model_tag, samples, logwt=None,
                           param_names=None, w=0.0, Om=None,
                           eps1_ceiling=None,
                           comparators=('flat', 'closed', 'matched'),
                           q_stars=(0.01, 0.05, 0.1, 0.5)):
    """Compute departure reports under multiple comparators.

    This function quantifies the sensitivity of the three-layer
    framework to the choice of reporting comparator.

    Parameters
    ----------
    model_tag : str
        Model identifier.
    samples, logwt, param_names, w, Om, eps1_ceiling, q_stars
        As for DeparturePosterior.
    comparators : tuple of str
        Which comparators to evaluate.

    Returns
    -------
    dict
        {comparator_name: full_report_dict} mapping, plus a
        'sensitivity_summary' key with Delta_Pi across comparators.
    """
    reports = {}
    for comp in comparators:
        dp = DeparturePosterior(
            model_tag, samples, logwt, param_names,
            comparator=comp, w=w, Om=Om)
        reports[comp] = dp.full_report(eps1_ceiling=eps1_ceiling,
                                        q_stars=q_stars)

    # Sensitivity summary: max spread in Π across comparators
    summary = {}
    if len(comparators) > 1:
        ref_comp = comparators[0]
        for qs in q_stars:
            pi_vals = [reports[c]['layer_3_exceedance']['Pi'][str(qs)]
                       for c in comparators]
            summary[str(qs)] = {
                'min': float(min(pi_vals)),
                'max': float(max(pi_vals)),
                'spread': float(max(pi_vals) - min(pi_vals)),
            }

    return {
        'reports': reports,
        'sensitivity_summary': summary,
        'comparators_evaluated': list(comparators),
    }
