"""Off-diagonal <a_lm a*_l'm'> / Bipolar Spherical Harmonic (BipoSH) extraction from a
single real CMB sky (e.g. Planck SMICA), for the pre-solver statistical-isotropy test.

A single sky gives one realization of a_lm, so the empirical a_lm a*_l'm' outer product
is NOT a covariance. The rotationally-contracted BipoSH coefficient IS a real single-sky
observable (Planck's SI & Statistics test):

    A^{LM}_{l1 l2} = sum_{m1 m2} C^{LM}_{l1 m1 l2 m2} a_{l1 m1} a_{l2 m2} ,

with C the Clebsch-Gordan coefficient. L is the bipolar multipole (the coupling scale):
  * L = 1  is the observer-boost / aberration l <-> l+1 coupling (the Doppler signature);
  * L = 2  is the quadrupolar SI violation a global tilt or shear would source.
The bipolar power  D^L_{l1 l2} = (1/(2L+1)) sum_M |A^{LM}_{l1 l2}|^2  is rotationally
invariant; its excess over an isotropic ensemble (GRF now, FFP10 when downloaded) is
the SI-violation statistic, null-calibrated with the shared `calibrate_max_scan`.

This is the honest realization of "extract C_{lm,l'm'} from SMICA": the DATA off-diagonal
is measured here; the THEORY prediction A^{LM}_{l1 l2}(g) for a given Bianchi g still needs
the native low-ell solver and stays fail-closed (`bass.spectrum.cl_assembly.off_diagonal_biposh`,
`AWAITING_NATIVE_LOWELL_SOLVER`). Diagnostic-only: model-independent SI descriptor; no
Bianchi family, geometry, frame-violation, or native-solver claim.
"""
from __future__ import annotations

from dataclasses import dataclass
from math import factorial, sqrt
import numpy as np

from htt.obsstat.lowell_map_features import densify_alm
from htt.obsstat.biposh_features import SparseBiPoSHCoefficient

__all__ = [
    "wigner_3j",
    "clebsch_gordan",
    "compute_biposh_from_alm",
    "biposh_power_by_L",
    "biposh_power_vector",
    "BiposhMeasurement",
]


def wigner_3j(j1: int, j2: int, j3: int, m1: int, m2: int, m3: int) -> float:
    """Exact Wigner 3-j symbol (Racah formula) for integer arguments."""
    if m1 + m2 + m3 != 0:
        return 0.0
    if abs(m1) > j1 or abs(m2) > j2 or abs(m3) > j3:
        return 0.0
    if j3 < abs(j1 - j2) or j3 > j1 + j2:
        return 0.0
    if (j1 + j2 + j3) < 0:
        return 0.0
    # triangle coefficient
    tri = (factorial(j1 + j2 - j3) * factorial(j1 - j2 + j3) * factorial(-j1 + j2 + j3)
           / factorial(j1 + j2 + j3 + 1))
    fac = (factorial(j1 + m1) * factorial(j1 - m1) * factorial(j2 + m2)
           * factorial(j2 - m2) * factorial(j3 + m3) * factorial(j3 - m3))
    pref = sqrt(tri * fac)
    kmin = max(0, j2 - j3 - m1, j1 - j3 + m2)
    kmax = min(j1 + j2 - j3, j1 - m1, j2 + m2)
    s = 0.0
    for k in range(kmin, kmax + 1):
        denom = (factorial(k) * factorial(j1 + j2 - j3 - k) * factorial(j1 - m1 - k)
                 * factorial(j2 + m2 - k) * factorial(j3 - j2 + m1 + k)
                 * factorial(j3 - j1 - m2 + k))
        s += (-1) ** k / denom
    return (-1) ** (j1 - j2 - m3) * pref * s


def clebsch_gordan(l1: int, m1: int, l2: int, m2: int, L: int, M: int) -> float:
    """<l1 m1 l2 m2 | L M> from the 3-j symbol."""
    if m1 + m2 != M:
        return 0.0
    return ((-1) ** (l1 - l2 + M) * sqrt(2 * L + 1)
            * wigner_3j(l1, l2, L, m1, m2, -M))


@dataclass(frozen=True)
class BiposhMeasurement:
    coefficients: tuple             # SparseBiPoSHCoefficient
    power_by_L: dict                # {L: total bipolar power}
    power_by_L_l1_l2: dict          # {(L,l1,l2): D^L_{l1l2}}
    lmax: int
    ell_min: int
    L_values: tuple
    channel: str


def compute_biposh_from_alm(alm_packed, lmax: int, *, L_values=(1, 2),
                            ell_min: int = 2, channel: str = "T",
                            threshold: float = 0.0) -> BiposhMeasurement:
    """Contract a real map's a_lm into BipoSH coefficients A^{LM}_{l1 l2}.

    alm_packed: healpy m>=0 packed a_lm. Negative-m filled by reality
    a_{l,-m} = (-1)^m conj(a_{l,m}). Returns the sparse coefficients + the
    rotationally-invariant bipolar power D^L_{l1l2} and its per-L totals.
    """
    dense = densify_alm(alm_packed, lmax)
    coeffs = []
    power_by_L = {int(L): 0.0 for L in L_values}
    power_by_L_l1_l2: dict = {}
    for L in L_values:
        for l1 in range(ell_min, lmax + 1):
            for l2 in range(l1, lmax + 1):                 # l1 <= l2 (upper triangle)
                if L < abs(l1 - l2) or L > l1 + l2:
                    continue
                d_power = 0.0
                for M in range(-L, L + 1):
                    A = 0.0 + 0.0j
                    for m1 in range(-l1, l1 + 1):
                        m2 = M - m1
                        if abs(m2) > l2:
                            continue
                        cg = clebsch_gordan(l1, m1, l2, m2, L, M)
                        if cg == 0.0:
                            continue
                        A += cg * dense[(l1, m1)] * dense[(l2, m2)]
                    d_power += abs(A) ** 2
                    if abs(A) > threshold:
                        coeffs.append(SparseBiPoSHCoefficient(
                            channel_pair=(channel, channel), ell1=l1, ell2=l2,
                            L=int(L), M=int(M), value=complex(A)))
                d_power /= (2 * L + 1)                      # rotational invariant D^L
                power_by_L[int(L)] += d_power
                power_by_L_l1_l2[(int(L), l1, l2)] = float(d_power)
    return BiposhMeasurement(tuple(coeffs), {k: float(v) for k, v in power_by_L.items()},
                             power_by_L_l1_l2, int(lmax), int(ell_min),
                             tuple(int(L) for L in L_values), channel)


def biposh_power_by_L(measurement: BiposhMeasurement) -> dict:
    """The per-L total bipolar power {L: D^L} (the primary SI-violation statistics)."""
    return dict(measurement.power_by_L)


def biposh_power_vector(measurement: BiposhMeasurement, keys=None):
    """A flat statistic vector for null calibration: the per-L totals (default), or the
    per-(L,l1,l2) powers for an explicit key list. Returns (vector, key_list)."""
    if keys is None:
        keys = sorted(measurement.power_by_L)
        return (np.array([measurement.power_by_L[k] for k in keys], dtype=float),
                [("L", k) for k in keys])
    return (np.array([measurement.power_by_L_l1_l2[k] for k in keys], dtype=float), list(keys))
