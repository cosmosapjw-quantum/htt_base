"""
htt/infer/directional_lowell.py — Low-ℓ Directional CMB Likelihood
=====================================================================
Phase 2 deliverable (Stage 2B). Implements a directional low-ℓ likelihood
that tests whether CMB quadrupole/octupole morphology is consistent with
the low-z dipole axis.

The key observable: angular separation between the low-z bulk flow axis
and the CMB low-ℓ preferred axes (quadrupole principal axis, octupole
planarity normal, quadrupole-octupole alignment axis).

This module does NOT fit full CMB maps. It uses pre-computed low-ℓ
summary statistics and tests directional consistency.
"""
import numpy as np
from dataclasses import dataclass
from typing import Optional, Tuple

__all__ = [
    'DirectionalLowellResult', 'LowellLikelihood',
    'angular_separation', 'alignment_probability',
]


def angular_separation(l1: float, b1: float, l2: float, b2: float) -> float:
    """Angular separation between two directions in galactic coordinates (degrees).

    Parameters
    ----------
    l1, b1 : float
        Galactic longitude, latitude of direction 1 (degrees)
    l2, b2 : float
        Same for direction 2

    Returns
    -------
    float
        Angular separation in degrees
    """
    l1r, b1r = np.radians(l1), np.radians(b1)
    l2r, b2r = np.radians(l2), np.radians(b2)
    cos_sep = (np.sin(b1r) * np.sin(b2r) +
               np.cos(b1r) * np.cos(b2r) * np.cos(l1r - l2r))
    cos_sep = np.clip(cos_sep, -1, 1)
    return np.degrees(np.arccos(cos_sep))


def alignment_probability(sep_deg: float, n_sim: int = 10000,
                          rng: Optional[np.random.Generator] = None) -> float:
    """Probability that two random directions are closer than sep_deg.

    Under the null (isotropic random axes), the CDF of angular separation
    θ on the sphere is P(θ < θ₀) = (1 − cos θ₀)/2.
    """
    cos_sep = np.cos(np.radians(sep_deg))
    return (1 - cos_sep) / 2


@dataclass(frozen=True)
class DirectionalLowellResult:
    """Result of a directional low-ℓ consistency test."""
    # Axis directions (galactic coordinates, degrees)
    lowz_l: float
    lowz_b: float
    cmb_quad_l: float
    cmb_quad_b: float
    cmb_oct_l: float
    cmb_oct_b: float

    # Angular separations (degrees)
    sep_lowz_quad: float
    sep_lowz_oct: float
    sep_quad_oct: float

    # Alignment probabilities (p-values under isotropic null)
    p_lowz_quad: float
    p_lowz_oct: float
    p_quad_oct: float

    # Combined alignment statistic
    combined_p: float

    # Interpretation
    aligned: bool               # True if combined_p < 0.05
    status: str = 'INFERENTIAL'


class LowellLikelihood:
    """Low-ℓ directional likelihood for tilt-CMB axis alignment.

    Uses the CF4 bulk flow direction and Planck low-ℓ preferred axes.
    The likelihood tests whether three axes (low-z dipole, CMB quadrupole,
    CMB octupole) are mutually closer than expected from isotropy.
    """

    # Planck 2018 low-ℓ axes (de Oliveira-Costa+ 2004, updated Planck)
    CMB_QUAD_L = 240.0          # quadrupole principal axis (l, deg)
    CMB_QUAD_B = 63.0           # quadrupole principal axis (b, deg)
    CMB_OCT_L = 236.0           # octupole planarity normal (l, deg)
    CMB_OCT_B = 64.0            # octupole planarity normal (b, deg)

    # CF4 bulk flow direction (Watkins+ 2023)
    CF4_L = 285.0
    CF4_B = 10.0

    def __init__(self, lowz_l: float = None, lowz_b: float = None):
        self.lowz_l = lowz_l or self.CF4_L
        self.lowz_b = lowz_b or self.CF4_B

    def evaluate(self) -> DirectionalLowellResult:
        """Evaluate the directional low-ℓ consistency test."""
        sep_lq = angular_separation(self.lowz_l, self.lowz_b,
                                    self.CMB_QUAD_L, self.CMB_QUAD_B)
        sep_lo = angular_separation(self.lowz_l, self.lowz_b,
                                    self.CMB_OCT_L, self.CMB_OCT_B)
        sep_qo = angular_separation(self.CMB_QUAD_L, self.CMB_QUAD_B,
                                    self.CMB_OCT_L, self.CMB_OCT_B)

        p_lq = alignment_probability(sep_lq)
        p_lo = alignment_probability(sep_lo)
        p_qo = alignment_probability(sep_qo)

        # Fisher's method for combining p-values
        chi2_stat = -2 * (np.log(max(p_lq, 1e-30)) +
                          np.log(max(p_lo, 1e-30)) +
                          np.log(max(p_qo, 1e-30)))
        from scipy.stats import chi2
        combined_p = float(chi2.sf(chi2_stat, df=6))

        return DirectionalLowellResult(
            lowz_l=self.lowz_l, lowz_b=self.lowz_b,
            cmb_quad_l=self.CMB_QUAD_L, cmb_quad_b=self.CMB_QUAD_B,
            cmb_oct_l=self.CMB_OCT_L, cmb_oct_b=self.CMB_OCT_B,
            sep_lowz_quad=sep_lq, sep_lowz_oct=sep_lo, sep_quad_oct=sep_qo,
            p_lowz_quad=p_lq, p_lowz_oct=p_lo, p_quad_oct=p_qo,
            combined_p=combined_p,
            aligned=combined_p < 0.05,
        )

    def directional_log_likelihood(self, l_deg: float, b_deg: float,
                                   sigma_deg: float = 15.0) -> float:
        """Log-likelihood of a proposed tilt axis direction.

        Gaussian penalty based on angular separation from CMB preferred axes.
        sigma_deg controls the concentration (smaller = more directional info).
        """
        sep_q = angular_separation(l_deg, b_deg, self.CMB_QUAD_L, self.CMB_QUAD_B)
        sep_o = angular_separation(l_deg, b_deg, self.CMB_OCT_L, self.CMB_OCT_B)
        return -0.5 * (sep_q**2 + sep_o**2) / sigma_deg**2

    def information_gain(self, n_samples: int = 5000,
                         sigma_deg: float = 15.0) -> float:
        """Estimate directional information gain (bits) from low-ℓ axes.

        Compares directional likelihood to isotropic prior via importance sampling.
        """
        rng = np.random.default_rng(42)
        # Sample from isotropic prior
        cos_b = rng.uniform(-1, 1, n_samples)
        b_samples = np.degrees(np.arcsin(cos_b))
        l_samples = rng.uniform(0, 360, n_samples)

        logw = np.array([self.directional_log_likelihood(l, b, sigma_deg)
                         for l, b in zip(l_samples, b_samples)])
        logw -= logw.max()
        w = np.exp(logw)

        # KL divergence estimate (bits)
        w_norm = w / w.sum()
        kl = np.sum(w_norm * (np.log2(w_norm + 1e-30) - np.log2(1.0 / n_samples)))
        return max(0.0, float(kl))
