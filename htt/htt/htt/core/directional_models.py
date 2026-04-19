"""Directional evidence models: tilt amplitude + sky direction.

Extends the scalar-amplitude pipeline with the tilt axis direction
(l, b) in galactic coordinates. The directional likelihood uses
Fisher-distribution penalties weighted by each survey's (S/N)².

Reference directions:
  CMB dipole:  (l, b) = (264.021, 48.253)  — Planck 2018
  CF4 bulk:    (l, b) = (282, 6)            — Watkins+2023
  CatWISE:     (l, b) = (240, -4)           — Secrest+2021/Böhme+2025

The directional model has 3 parameters: (β, l, b) where β is the
tilt rapidity and (l, b) is the tilt axis in galactic degrees.

STATUS: EXPLORATORY — directional inference is preliminary.
The summary-statistic pipeline was designed for amplitude-only
analysis; directional extension is a proof of concept.
"""
import numpy as np
import sys
from pathlib import Path

_root = str(Path(__file__).resolve().parent.parent.parent.parent)
for _p in [_root, _root + '/htt', _root + '/bass']:
    if _p not in sys.path:
        sys.path.insert(0, _p)

from htt.core.evidence_models_R03a import (
    FLRW_tilt, eps1_from_beta, boost_to_D2,
    ObsData, T0_UK, D2_LCDM, D3_LCDM,
)

__all__ = [
    'FLRW_tilt_directional',
    'BI_tilt_directional',
    'DirectionalResult',
]


# ── Reference directions (galactic coordinates, degrees) ─────

REFS = {
    'CMB_dipole': {'l': 264.021, 'b': 48.253, 'label': 'CMB dipole (Planck 2018)'},
    'CF4_bulk':   {'l': 282.0,   'b': 6.0,    'label': 'CF4 bulk flow (Watkins+2023)'},
    'CatWISE':    {'l': 240.0,   'b': -4.0,   'label': 'CatWISE (Secrest+2021)'},
    'radio_NVSS': {'l': 245.0,   'b': 18.0,   'label': 'NVSS+RACS (Wagenveld+2023)'},
}


def _unit_vector(l_deg, b_deg):
    """Convert galactic (l, b) in degrees to unit vector."""
    l, b = np.radians(l_deg), np.radians(b_deg)
    return np.array([np.cos(b)*np.cos(l), np.cos(b)*np.sin(l), np.sin(b)])


def _angular_separation(l1, b1, l2, b2):
    """Angular separation in radians."""
    d1 = _unit_vector(l1, b1)
    d2 = _unit_vector(l2, b2)
    return np.arccos(np.clip(np.dot(d1, d2), -1, 1))


def _fisher_logpdf(sep_rad, kappa):
    """Log of Fisher distribution on the sphere: κ cos(θ) + const."""
    return kappa * np.cos(sep_rad)


class FLRW_tilt_directional:
    """Tilt-only model with direction: θ = (β, l, b).

    Likelihood = L_amplitude(β) × L_direction(l, b | β)

    L_amplitude: same as FLRW_tilt (scalar pipeline)
    L_direction: Fisher penalties for alignment with CF4 and CatWISE,
                 with concentration κ = (S/N)²
    """
    name = 'FLRW_tilt_dir'
    param_names = ['beta', 'l_gal', 'b_gal']
    ndim = 3

    def __init__(self):
        self.obs = ObsData()
        self._scalar = FLRW_tilt()
        # Fisher concentrations from survey S/N
        self.kappa_CF4 = (self.obs.b_CF4 / self.obs.b_CF4_s)**2
        self.kappa_CW = 25.0  # CatWISE dipole ~5σ → κ ≈ 25

    def prior_transform(self, u):
        """Prior: β log-uniform [1e-8, 0.1], l uniform [0, 360], b cosine."""
        beta = 10**(u[0] * 7 - 8)  # log-uniform 1e-8 to 0.1
        l_gal = u[1] * 360.0       # uniform 0..360
        b_gal = np.degrees(np.arcsin(2*u[2] - 1))  # cosine prior on b
        return np.array([beta, l_gal, b_gal])

    def predicted_observables(self, theta):
        """Returns scalar observables + direction."""
        beta, l_gal, b_gal = theta
        scalar_obs = self._scalar.predicted_observables(np.array([beta]))
        if scalar_obs is None:
            return None
        scalar_obs['l_gal'] = l_gal
        scalar_obs['b_gal'] = b_gal
        return scalar_obs

    def log_likelihood(self, theta):
        """Combined amplitude + directional log-likelihood."""
        beta, l_gal, b_gal = theta

        # Amplitude part (from scalar model)
        ll_amp = self._scalar.log_likelihood(np.array([beta]))
        if not np.isfinite(ll_amp):
            return -1e30

        # Directional part: Fisher penalties
        sep_CF4 = _angular_separation(l_gal, b_gal,
                                       REFS['CF4_bulk']['l'],
                                       REFS['CF4_bulk']['b'])
        sep_CW = _angular_separation(l_gal, b_gal,
                                      REFS['CatWISE']['l'],
                                      REFS['CatWISE']['b'])

        ll_dir = (_fisher_logpdf(sep_CF4, self.kappa_CF4) +
                  _fisher_logpdf(sep_CW, self.kappa_CW))

        return ll_amp + ll_dir


class BI_tilt_directional:
    """Bianchi I + tilt with direction: θ = (Σ², β, l, b).

    Same directional likelihood as FLRW_tilt_directional,
    but includes a shear parameter.
    """
    name = 'BI_tilt_dir'
    param_names = ['Sigma2', 'beta', 'l_gal', 'b_gal']
    ndim = 4

    def __init__(self):
        self.obs = ObsData()
        from htt.core.evidence_models_R03a import BianchiI_tilt
        self._scalar = BianchiI_tilt()
        self.kappa_CF4 = (self.obs.b_CF4 / self.obs.b_CF4_s)**2
        self.kappa_CW = 25.0

    def prior_transform(self, u):
        Sigma2 = 10**(u[0] * 26 - 30)  # log-uniform 1e-30..1e-4
        beta = 10**(u[1] * 7 - 8)
        l_gal = u[2] * 360.0
        b_gal = np.degrees(np.arcsin(2*u[3] - 1))
        return np.array([Sigma2, beta, l_gal, b_gal])

    def predicted_observables(self, theta):
        Sigma2, beta, l_gal, b_gal = theta
        scalar_obs = self._scalar.predicted_observables(
            np.array([Sigma2, beta]))
        if scalar_obs is None:
            return None
        scalar_obs['l_gal'] = l_gal
        scalar_obs['b_gal'] = b_gal
        return scalar_obs

    def log_likelihood(self, theta):
        Sigma2, beta, l_gal, b_gal = theta
        ll_amp = self._scalar.log_likelihood(np.array([Sigma2, beta]))
        if not np.isfinite(ll_amp):
            return -1e30

        sep_CF4 = _angular_separation(l_gal, b_gal,
                                       REFS['CF4_bulk']['l'],
                                       REFS['CF4_bulk']['b'])
        sep_CW = _angular_separation(l_gal, b_gal,
                                      REFS['CatWISE']['l'],
                                      REFS['CatWISE']['b'])
        ll_dir = (_fisher_logpdf(sep_CF4, self.kappa_CF4) +
                  _fisher_logpdf(sep_CW, self.kappa_CW))
        return ll_amp + ll_dir


class DirectionalResult:
    """Post-process nested sampling output for directional models."""

    def __init__(self, name, samples, weights, lnZ, lnZ_err):
        self.name = name
        self.samples = samples
        self.weights = weights
        self.lnZ = lnZ
        self.lnZ_err = lnZ_err

    @property
    def beta_samples(self):
        return self.samples[:, 0]

    @property
    def l_samples(self):
        return self.samples[:, -2]

    @property
    def b_samples(self):
        return self.samples[:, -1]

    def direction_summary(self) -> dict:
        """Weighted summary of the directional posterior."""
        w = self.weights / self.weights.sum()

        # Weighted mean direction via unit-vector averaging
        ls, bs = np.radians(self.l_samples), np.radians(self.b_samples)
        x = np.average(np.cos(bs)*np.cos(ls), weights=w)
        y = np.average(np.cos(bs)*np.sin(ls), weights=w)
        z = np.average(np.sin(bs), weights=w)
        r = np.sqrt(x**2 + y**2 + z**2)

        l_mean = np.degrees(np.arctan2(y, x)) % 360
        b_mean = np.degrees(np.arcsin(np.clip(z/max(r, 1e-30), -1, 1)))

        # Angular dispersions (weighted)
        l_std = float(np.sqrt(np.average(
            (self.l_samples - l_mean)**2, weights=w)))
        b_std = float(np.sqrt(np.average(
            (self.b_samples - b_mean)**2, weights=w)))

        # Separations from reference directions
        seps = {}
        for ref_name, ref_data in REFS.items():
            sep = np.degrees(_angular_separation(
                l_mean, b_mean, ref_data['l'], ref_data['b']))
            seps[ref_name] = {
                'separation_deg': round(float(sep), 1),
                'label': ref_data['label'],
            }

        # Concentration parameter (R-bar statistic)
        R_bar = float(r)  # 0 = uniform, 1 = delta function

        return {
            'l_mean_deg': round(float(l_mean), 1),
            'b_mean_deg': round(float(b_mean), 1),
            'l_std_deg': round(float(l_std), 1),
            'b_std_deg': round(float(b_std), 1),
            'R_bar': round(R_bar, 4),
            'separations': seps,
            'n_eff': round(float(1.0 / np.sum(w**2)), 1),
            'lnZ': round(float(self.lnZ), 2),
            'lnZ_err': round(float(self.lnZ_err), 2),
        }


def run_directional_inference(nlive=200, dlogz=1.0, maxcall=20000):
    """Run directional nested sampling for FLRW_tilt_dir and BI_tilt_dir.

    Returns dict of DirectionalResult objects.
    """
    try:
        import dynesty
    except ImportError:
        print("  dynesty not available — skipping directional inference")
        return {}

    results = {}
    for ModelClass in [FLRW_tilt_directional, BI_tilt_directional]:
        m = ModelClass()
        print(f"  Running {m.name} (ndim={m.ndim}, nlive={nlive})...")

        sampler = dynesty.NestedSampler(
            m.log_likelihood, m.prior_transform, m.ndim,
            nlive=nlive)
        sampler.run_nested(dlogz=dlogz, maxcall=maxcall, print_progress=False)
        res = sampler.results

        samples = res.samples
        weights = np.exp(res.logwt - res.logwt.max())
        weights /= weights.sum()

        dr = DirectionalResult(
            name=m.name,
            samples=samples,
            weights=weights,
            lnZ=float(res.logz[-1]),
            lnZ_err=float(res.logzerr[-1]),
        )
        results[m.name] = dr

        ds = dr.direction_summary()
        print(f"    lnZ = {ds['lnZ']:.2f} ± {ds['lnZ_err']:.2f}")
        print(f"    Direction: (l, b) = ({ds['l_mean_deg']:.1f}°, {ds['b_mean_deg']:.1f}°) "
              f"± ({ds['l_std_deg']:.1f}°, {ds['b_std_deg']:.1f}°)")
        print(f"    R̄ = {ds['R_bar']:.3f} (concentration)")
        for ref, sep_data in ds['separations'].items():
            print(f"    {sep_data['label']}: {sep_data['separation_deg']}° away")

    return results
