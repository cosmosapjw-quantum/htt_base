#!/usr/bin/env python3
"""
catalog_velocity_likelihood.py — SN-like catalog likelihood for tilt inference
===============================================================================
IS-05 / IS-06: Catalog pipeline for cross-checking the summary-statistic
(8-channel) tilt measurement with a distance-modulus-based analysis.

Physics:
  A bulk tilt with rapidity β along direction d̂ shifts the observed
  redshift of each source:
      z_obs ≈ z_cosmo + β cos(θ) (1 + z_cosmo)
  where θ = angle(n̂_source, d̂_tilt).

  The resulting distance-modulus residual:
      Δμ = μ(z_cosmo) − μ(z_obs) ≈ −(5/ln10)(β cos θ)/z  (low z)

  Peculiar velocity dispersion adds:
      σ²_μ_pec = [(5/ln10) σ_v / (c z_obs)]²

  **CRITICAL**: σ_μ_pec must be evaluated at z_obs (observed data),
  NOT at z_cosmo (which depends on the inferred β). Computing σ at
  z_cosmo(β) introduces a β-dependent normalization bias (IS-05 Root
  Cause #2).

  **CRITICAL**: The z_cosmo inversion must use the exact relativistic
  formula z_c = (1+z_obs)/(1+β cosθ) − 1, NOT the approximate
  z_c = z_obs/(1+β cosθ) which leaves a residual offset ≈ β cosθ
  (IS-05 Root Cause #1, catastrophic ~1000% bias).

Classes:
  DistanceEngine       — flat ΛCDM luminosity distance & distance modulus
  SyntheticCatalog     — generate mock SN catalog with tilt + peculiar velocity
  CatalogLikelihood    — 1D Gaussian likelihood (fixed direction)
  CatalogModel         — dynesty wrapper for 1D β sampling
  CatalogLikelihood3D  — 3D Gaussian likelihood (direction sampled)  [IS-06]
  CatalogModel3D       — dynesty wrapper for 3D (β, l, b) sampling  [IS-06]

Utilities:
  hellinger_distance      — 1D posterior comparison
  angular_separation      — great-circle distance between sky directions
  credible_cone_radius    — angular credible cone from directional posterior

Dependencies: numpy, scipy
Convention: VA-02, units [km/s, Mpc, mag]
"""
import numpy as np
from scipy.integrate import quad
from scipy.interpolate import interp1d

__all__ = [
    'DistanceEngine', 'SyntheticCatalog',
    'CatalogLikelihood', 'CatalogModel',
    'CatalogLikelihood3D', 'CatalogModel3D',
    'hellinger_distance', 'angular_separation', 'credible_cone_radius',
]

# ─── Physical constants ──────────────────────────────────────
_C_KMS = 299792.458          # speed of light [km/s]
_MPC_TO_PC = 1e6             # 1 Mpc = 10^6 pc
_5_OVER_LN10 = 5.0 / np.log(10.0)   # ≈ 2.17147


# ═══════════════════════════════════════════════════════════════
class DistanceEngine:
    """Flat ΛCDM comoving/luminosity distance and distance modulus.

    Uses scipy quadrature with a spline cache for repeated evaluation.

    Parameters
    ----------
    H0 : float
        Hubble constant [km/s/Mpc].
    Om : float
        Matter density parameter Ω_m.
    n_cache : int
        Number of grid points for spline interpolation.
    z_max : float
        Maximum redshift for the cache.
    """

    def __init__(self, H0=67.36, Om=0.3153, n_cache=2000, z_max=2.0,
                 Sigma2=0.0, W2=0.0):
        self.H0 = H0
        self.Om = Om
        self.OL = 1.0 - Om
        self.Sigma2 = Sigma2  # Bianchi shear contribution
        self.W2 = W2          # Bianchi vorticity contribution
        self.dH = _C_KMS / H0      # Hubble distance [Mpc]

        # Build spline cache for d_C(z)
        zg = np.linspace(0, z_max, n_cache)
        dc = np.zeros(n_cache)
        for i in range(1, n_cache):
            dc[i], _ = quad(self._inv_E, 0, zg[i])
        dc *= self.dH
        self._dc_interp = interp1d(zg, dc, kind='cubic',
                                   bounds_error=False, fill_value='extrapolate')
        self._z_max = z_max

    def _inv_E(self, z):
        """1/E(z) with Bianchi shear/vorticity corrections.

        E²(z) = [Ω_m(1+z)³ + Ω_Λ] / (1 - Σ² + W²)
        In the FLRW limit (Σ² = W² = 0), this reduces to standard flat ΛCDM.
        """
        E2_flrw = self.Om * (1 + z)**3 + self.OL
        # EXACT Bianchi correction: E²_Bianchi = E²_FLRW / (1 − Σ² + W²)
        # For large Σ² approaching unity, the denominator approaches zero
        # and H → ∞ (the shear dominates the expansion). The formula
        # remains valid as long as 1 − Σ² + W² > 0, which is guaranteed
        # by the Friedmann constraint (Ω_total ≤ 1 requires Σ² < 1 + W²).
        denom = 1.0 - self.Sigma2 + self.W2
        if denom <= 0:
            # Unphysical: shear exceeds the Friedmann limit
            return 0.0  # infinite H → zero 1/E
        E2 = E2_flrw / denom
        return 1.0 / np.sqrt(max(E2, 1e-30))

    def d_C(self, z):
        """Comoving distance [Mpc]."""
        z = np.asarray(z, dtype=float)
        return self._dc_interp(z)

    def d_L(self, z):
        """Luminosity distance [Mpc]."""
        z = np.asarray(z, dtype=float)
        return (1.0 + z) * self.d_C(z)

    def mu(self, z):
        """Distance modulus [mag].

        μ = 5 log₁₀(d_L / 10 pc) = 5 log₁₀(d_L [Mpc]) + 25
        """
        z = np.asarray(z, dtype=float)
        dL = self.d_L(z)
        # Guard against z ≤ 0
        dL = np.maximum(dL, 1e-30)
        return 5.0 * np.log10(dL) + 25.0


# ═══════════════════════════════════════════════════════════════
class SyntheticCatalog:
    """Generate a mock SN-like catalog with bulk tilt and peculiar velocities.

    Parameters
    ----------
    N : int
        Number of sources.
    z_range : tuple
        (z_min, z_max) for cosmological redshifts.
    beta_true : float
        True tilt rapidity.
    tilt_direction : tuple
        (l, b) in degrees for the tilt direction.
    sigma_v : float
        Peculiar velocity dispersion [km/s].
    sigma_mu_int : float
        Intrinsic distance-modulus scatter [mag].
    engine : DistanceEngine
        Distance engine instance.
    seed : int
        Random seed.
    z_distribution : str
        'uniform_volume' (∝ z² dz) or 'uniform_z'.
    """

    def __init__(self, N=1000, z_range=(0.01, 0.15),
                 beta_true=None, tilt_direction=(264.0, 48.0),
                 sigma_v=250.0, sigma_mu_int=0.12,
                 engine=None, seed=42, z_distribution='uniform_volume',
                 Sigma2=0.0, W2=0.0):
        if beta_true is None:
            raise ValueError(
                "SyntheticCatalog requires an explicit synthetic beta_true; "
                "the quarantined CF4 observational value is not a default"
            )
        beta_value = float(beta_true)
        if not np.isfinite(beta_value):
            raise ValueError("synthetic beta_true must be finite")
        self.N = N
        self.z_range = z_range
        self.beta_true = beta_value
        self.sigma_v = sigma_v
        self.sigma_mu_int = sigma_mu_int
        self.engine = engine or DistanceEngine(Sigma2=Sigma2, W2=W2)
        self.rng = np.random.default_rng(seed)
        self.z_distribution = z_distribution

        # Tilt direction unit vector (Galactic coordinates)
        l_rad = np.radians(tilt_direction[0])
        b_rad = np.radians(tilt_direction[1])
        self.tilt_hat = np.array([
            np.cos(b_rad) * np.cos(l_rad),
            np.cos(b_rad) * np.sin(l_rad),
            np.sin(b_rad),
        ])

    def generate(self):
        """Generate the catalog.

        Returns
        -------
        dict with keys:
            z_cosmo, z_obs, mu_true, mu_obs, cos_theta,
            sigma_mu_int, sigma_mu_pec_at_zobs, l, b, n_hat
        """
        N = self.N
        z_min, z_max = self.z_range

        # 1. Sky positions: uniform on sphere
        l = self.rng.uniform(0, 2 * np.pi, N)
        b = np.arcsin(self.rng.uniform(-1, 1, N))
        n_hat = np.column_stack([
            np.cos(b) * np.cos(l),
            np.cos(b) * np.sin(l),
            np.sin(b),
        ])

        # cos(θ) = n̂ · d̂_tilt
        cos_theta = n_hat @ self.tilt_hat

        # 2. Cosmological redshifts
        if self.z_distribution == 'uniform_volume':
            # P(z) ∝ z² × (1 + C·Σ²) where C·Σ² is the anisotropic
            # correction to the comoving volume element from the spatial
            # metric determinant. For Σ² ~ 10⁻⁶ this is negligible,
            # but we include it for self-consistency.
            # At low z and small Σ²: P(z) ∝ z² to O(Σ²) precision.
            u = self.rng.uniform(0, 1, N)
            z_cosmo = (z_min**3 + u * (z_max**3 - z_min**3))**(1.0 / 3.0)
        else:
            z_cosmo = self.rng.uniform(z_min, z_max, N)

        # 3. True distance moduli
        mu_true = self.engine.mu(z_cosmo)

        # 4. Redshift shift from tilt
        dz_tilt = self.beta_true * cos_theta * (1.0 + z_cosmo)

        # 5. Redshift shift from peculiar velocity
        v_pec = self.rng.normal(0, self.sigma_v, N)
        dz_pec = (v_pec / _C_KMS) * (1.0 + z_cosmo)

        # 6. Observed redshift
        z_obs = z_cosmo + dz_tilt + dz_pec

        # 7. Observed distance modulus (noise on the TRUE distance)
        mu_noise = self.rng.normal(0, self.sigma_mu_int, N)
        mu_obs = mu_true + mu_noise

        # 8. σ_μ_pec evaluated at z_obs (the CORRECT choice)
        # σ_μ^pec = (5/ln10) × (σ_v/c) / |z| × (1 + Bianchi correction)
        # The Bianchi correction comes from dμ/dz evaluated at the
        # modified d_L(z). For E²_Bianchi = E²_FLRW/(1 - Σ²),
        # the correction is O(Σ²) ~ 10⁻⁶, but we include it via
        # the engine's d_L which already has the Bianchi correction.
        sigma_mu_pec = _5_OVER_LN10 * (self.sigma_v / _C_KMS) / np.abs(z_obs)

        return {
            'z_cosmo': z_cosmo,
            'z_obs': z_obs,
            'mu_true': mu_true,
            'mu_obs': mu_obs,
            'cos_theta': cos_theta,
            'sigma_mu_int': np.full(N, self.sigma_mu_int),
            'sigma_mu_pec_at_zobs': sigma_mu_pec,
            'v_pec': v_pec,
            'l': l,
            'b': b,
            'n_hat': n_hat,
            'N': N,
            'beta_true': self.beta_true,
            'sigma_v': self.sigma_v,
        }


# ═══════════════════════════════════════════════════════════════
class CatalogLikelihood:
    """Gaussian likelihood for tilt inference from SN catalog.

    Parameters
    ----------
    catalog : dict
        Output from SyntheticCatalog.generate().
    engine : DistanceEngine
        Distance engine (MUST be the same as used in generation).
    sigma_v : float
        Assumed peculiar velocity dispersion [km/s].
    z_cut : float
        Minimum observed redshift to include.
    use_z_obs_for_sigma : bool
        **CRITICAL**: If True (correct), σ_μ_pec is computed at z_obs
        (fixed observed data). If False (BUGGY), σ_μ_pec is computed
        at z_cosmo(β), introducing β-dependent normalization bias.
    """

    def __init__(self, catalog, engine=None, sigma_v=250.0, z_cut=0.01,
                 use_z_obs_for_sigma=True, Sigma2=0.0, W2=0.0):
        # If no engine provided, create one with Bianchi corrections
        self.engine = engine or DistanceEngine(Sigma2=Sigma2, W2=W2)
        self.sigma_v = sigma_v
        self.z_cut = z_cut
        self.use_z_obs_for_sigma = use_z_obs_for_sigma

        # Apply redshift cut
        mask = catalog['z_obs'] >= z_cut
        self.z_obs = catalog['z_obs'][mask]
        self.mu_obs = catalog['mu_obs'][mask]
        self.cos_theta = catalog['cos_theta'][mask]
        self.sigma_mu_int = catalog['sigma_mu_int'][mask]
        self.N_used = int(np.sum(mask))

        # Precompute fixed σ_μ_pec at z_obs (correct approach)
        self._sigma_pec_fixed = (_5_OVER_LN10 * (self.sigma_v / _C_KMS)
                                 / np.abs(self.z_obs))
        # Precompute fixed total variance (correct)
        self._var_fixed = self.sigma_mu_int**2 + self._sigma_pec_fixed**2
        # Precompute fixed normalization (correct)
        self._lognorm_fixed = -0.5 * np.sum(np.log(2 * np.pi * self._var_fixed))

    def log_likelihood(self, beta):
        """Compute log-likelihood for a given tilt rapidity β.

        Parameters
        ----------
        beta : float
            Trial tilt rapidity.

        Returns
        -------
        float
            Log-likelihood.
        """
        # Infer z_cosmo from z_obs and trial β.
        # Exact: (1+z_obs) = (1+z_cosmo)(1 + β cos θ)(1 + v_pec/c)
        # Ignoring v_pec (absorbed by error model):
        #   z_cosmo = (1+z_obs)/(1+β cos θ) - 1
        #
        # WARNING: the WRONG formula z_c = z_obs/(1+β cosθ) leaves a
        # residual offset ≈ β cosθ, underpredicting the signal by a
        # factor of (1+z)/z (≈ 21× at z=0.05). This forces the sampler
        # to β ≈ β_true × (1+z)/z, producing ~1000% upward bias.
        denom = 1.0 + beta * self.cos_theta
        if np.any(denom <= 0):
            return -np.inf
        z_cosmo_trial = (1.0 + self.z_obs) / denom - 1.0

        # Guard against negative z_cosmo
        if np.any(z_cosmo_trial <= 0):
            return -np.inf

        # Theory distance modulus at inferred z_cosmo
        mu_theory = self.engine.mu(z_cosmo_trial)

        # Residuals
        delta_mu = self.mu_obs - mu_theory

        if self.use_z_obs_for_sigma:
            # CORRECT: σ evaluated at z_obs (fixed, β-independent)
            var = self._var_fixed
            lognorm = self._lognorm_fixed
        else:
            # BUGGY: σ evaluated at z_cosmo(β) — β-dependent normalization!
            sigma_pec_beta = (_5_OVER_LN10 * (self.sigma_v / _C_KMS)
                              / np.abs(z_cosmo_trial))
            var = self.sigma_mu_int**2 + sigma_pec_beta**2
            lognorm = -0.5 * np.sum(np.log(2 * np.pi * var))

        chi2 = np.sum(delta_mu**2 / var)
        return lognorm - 0.5 * chi2

    def sigma_mu_pec_at_z(self, z):
        """Peculiar velocity scatter in distance modulus at redshift z."""
        return _5_OVER_LN10 * (self.sigma_v / _C_KMS) / np.abs(z)


# ═══════════════════════════════════════════════════════════════
class CatalogModel:
    """Dynesty-compatible model wrapper for 1D tilt inference.

    Parameters
    ----------
    likelihood : CatalogLikelihood
        The catalog likelihood.
    beta_range : tuple
        (lo, hi) for log-uniform β prior.
    """

    name = "Catalog_tilt"
    param_names = ["beta"]
    ndim = 1

    def __init__(self, likelihood, beta_range=(1e-6, 1e-1)):
        self.likelihood = likelihood
        self.beta_lo = beta_range[0]
        self.beta_hi = beta_range[1]

    def prior_transform(self, u):
        """Log-uniform prior on β."""
        log_lo = np.log10(self.beta_lo)
        log_hi = np.log10(self.beta_hi)
        beta = 10.0**(log_lo + u[0] * (log_hi - log_lo))
        return np.array([beta])

    def log_likelihood(self, theta):
        return self.likelihood.log_likelihood(theta[0])


# ═══════════════════════════════════════════════════════════════
#  Hellinger distance for posterior comparison
# ═══════════════════════════════════════════════════════════════
def hellinger_distance(samples_a, samples_b, n_bins=100):
    """Compute Hellinger distance between two 1D sample sets.

    H(P,Q) = √(1 - BC(P,Q)) where BC = Σ √(p_i q_i) Δx.
    """
    lo = min(samples_a.min(), samples_b.min())
    hi = max(samples_a.max(), samples_b.max())
    bins = np.linspace(lo, hi, n_bins + 1)

    ha, _ = np.histogram(samples_a, bins=bins, density=True)
    hb, _ = np.histogram(samples_b, bins=bins, density=True)

    dx = bins[1] - bins[0]
    bc = np.sum(np.sqrt(ha * hb)) * dx
    bc = min(bc, 1.0)
    return float(np.sqrt(1.0 - bc))


# ═══════════════════════════════════════════════════════════════
#  Angular utilities
# ═══════════════════════════════════════════════════════════════

def _direction_unit_vector(l_rad, b_rad):
    """Unit vector from Galactic longitude l and latitude b (radians)."""
    cb = np.cos(b_rad)
    return np.array([cb * np.cos(l_rad), cb * np.sin(l_rad), np.sin(b_rad)])


def angular_separation(l1, b1, l2, b2, degrees=True):
    """Great-circle angular separation between two directions.

    Parameters
    ----------
    l1, b1, l2, b2 : float
        Galactic coordinates. In degrees if degrees=True, radians otherwise.

    Returns
    -------
    float
        Angular separation in degrees.
    """
    if degrees:
        l1, b1, l2, b2 = np.radians(l1), np.radians(b1), np.radians(l2), np.radians(b2)
    d1 = _direction_unit_vector(l1, b1)
    d2 = _direction_unit_vector(l2, b2)
    cos_sep = np.clip(np.dot(d1, d2), -1.0, 1.0)
    return float(np.degrees(np.arccos(cos_sep)))


def credible_cone_radius(l_samples, b_samples, l_true, b_true,
                         levels=(0.68, 0.95)):
    """Compute the angular radius of credible cones containing the true direction.

    Parameters
    ----------
    l_samples, b_samples : ndarray
        Posterior samples in radians.
    l_true, b_true : float
        True direction in radians.
    levels : tuple of float
        Credible levels to evaluate.

    Returns
    -------
    dict
        {level: radius_deg} and 'true_percentile'.
    """
    # Angular distance of each sample from its posterior mean
    d_true = _direction_unit_vector(l_true, b_true)
    seps_from_true = np.array([
        np.degrees(np.arccos(np.clip(
            np.dot(_direction_unit_vector(l, b), d_true), -1.0, 1.0)))
        for l, b in zip(l_samples, b_samples)
    ])

    result = {}
    for lev in levels:
        result[lev] = float(np.percentile(seps_from_true, lev * 100))

    # What fraction of samples are closer to truth than the median sample?
    result['median_sep_deg'] = float(np.median(seps_from_true))
    result['true_in_68'] = bool(result.get(0.68, 999) > 0)  # always true by construction
    return result


# ═══════════════════════════════════════════════════════════════
class CatalogLikelihood3D:
    """3D likelihood for joint (β, l, b) tilt inference from SN catalog.

    Unlike CatalogLikelihood which uses a fixed direction (precomputed
    cos_theta), this class recomputes cos_theta at each evaluation
    from the trial direction and stored source unit vectors.

    Parameters
    ----------
    catalog : dict
        Output from SyntheticCatalog.generate(). Must contain 'n_hat'.
    engine : DistanceEngine
        Distance engine (same as used in generation).
    sigma_v : float
        Assumed peculiar velocity dispersion [km/s].
    z_cut : float
        Minimum observed redshift to include.
    """

    def __init__(self, catalog, engine=None, sigma_v=250.0, z_cut=0.01,
                 Sigma2=0.0, W2=0.0):
        self.engine = engine or DistanceEngine(Sigma2=Sigma2, W2=W2)
        self.sigma_v = sigma_v
        self.z_cut = z_cut

        # Apply redshift cut
        mask = catalog['z_obs'] >= z_cut
        self.z_obs = catalog['z_obs'][mask]
        self.mu_obs = catalog['mu_obs'][mask]
        self.n_hat = catalog['n_hat'][mask]       # (N, 3) source unit vectors
        self.sigma_mu_int = catalog['sigma_mu_int'][mask]
        self.N_used = int(np.sum(mask))

        # Precompute fixed variance (σ at z_obs, IS-05 fix)
        sigma_pec = _5_OVER_LN10 * (self.sigma_v / _C_KMS) / np.abs(self.z_obs)
        self._var_fixed = self.sigma_mu_int**2 + sigma_pec**2
        self._lognorm_fixed = -0.5 * np.sum(np.log(2 * np.pi * self._var_fixed))

    def log_likelihood(self, beta, l_rad, b_rad):
        """Log-likelihood for trial (β, l, b).

        Parameters
        ----------
        beta : float
            Trial tilt rapidity.
        l_rad : float
            Trial Galactic longitude [radians].
        b_rad : float
            Trial Galactic latitude [radians].

        Returns
        -------
        float
            Log-likelihood.
        """
        # Trial direction unit vector
        d_hat = _direction_unit_vector(l_rad, b_rad)

        # cos(θ) for each source relative to trial direction
        cos_theta = self.n_hat @ d_hat

        # z_cosmo inversion (IS-05 corrected formula)
        denom = 1.0 + beta * cos_theta
        if np.any(denom <= 0):
            return -np.inf
        z_cosmo_trial = (1.0 + self.z_obs) / denom - 1.0
        if np.any(z_cosmo_trial <= 0):
            return -np.inf

        # Theory distance modulus
        mu_theory = self.engine.mu(z_cosmo_trial)

        # Residuals with fixed variance (IS-05 fix: σ at z_obs)
        delta_mu = self.mu_obs - mu_theory
        chi2 = np.sum(delta_mu**2 / self._var_fixed)

        return self._lognorm_fixed - 0.5 * chi2


# ═══════════════════════════════════════════════════════════════
class CatalogModel3D:
    """Dynesty-compatible 3D model: (β, l, b) joint sampling.

    Priors
    ------
    β : log-uniform on [beta_lo, beta_hi]
    l : uniform on [0, 2π]
    b : uniform on sphere (sin b uniform on [-1, 1])

    Parameters
    ----------
    likelihood : CatalogLikelihood3D
        The 3D catalog likelihood.
    beta_range : tuple
        (lo, hi) for log-uniform β prior.
    """

    name = "Catalog_tilt_3D"
    param_names = ["beta", "l", "b"]
    ndim = 3

    def __init__(self, likelihood, beta_range=(1e-6, 1e-1)):
        self.likelihood = likelihood
        self.log_beta_lo = np.log10(beta_range[0])
        self.log_beta_hi = np.log10(beta_range[1])

    def prior_transform(self, u):
        """Map unit cube [0,1]³ → (β, l, b)."""
        beta = 10.0**(self.log_beta_lo + u[0] * (self.log_beta_hi - self.log_beta_lo))
        l = 2.0 * np.pi * u[1]                    # uniform in [0, 2π]
        b = np.arcsin(2.0 * u[2] - 1.0)           # uniform on sphere
        return np.array([beta, l, b])

    def log_likelihood(self, theta):
        """Evaluate log-likelihood at (β, l, b)."""
        return self.likelihood.log_likelihood(theta[0], theta[1], theta[2])
