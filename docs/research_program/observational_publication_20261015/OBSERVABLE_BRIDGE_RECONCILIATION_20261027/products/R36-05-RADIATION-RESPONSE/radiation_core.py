"""Static bolometric radiation stress and its five-dimensional response.

The observer uses metric (-,+,+,+), outward sky direction n, photon
propagation e=-n, and energy density per solid angle I in J m^-3 sr^-1.
Weights integrate dOmega/(4*pi); ``rho0`` is 4*pi times the reference I0.
No transport derivative, matter shear, or frequency completion is inferred.
"""

from __future__ import annotations

from dataclasses import dataclass
import numpy as np
from numpy.polynomial.legendre import leggauss


ETA = np.diag([-1.0, 1.0, 1.0, 1.0])
EYE = np.eye(3)
RT2, RT6 = np.sqrt(2.0), np.sqrt(6.0)
STF_BASIS = np.array([
    np.diag([1, -1, 0]) / RT2,
    np.diag([1, 1, -2]) / RT6,
    np.array([[0, 1, 0], [1, 0, 0], [0, 0, 0]]) / RT2,
    np.array([[0, 0, 1], [0, 0, 0], [1, 0, 0]]) / RT2,
    np.array([[0, 0, 0], [0, 0, 1], [0, 1, 0]]) / RT2,
])


def stf2(a: np.ndarray) -> np.ndarray:
    a = np.asarray(a, dtype=float)
    a = (a + a.T) / 2
    return a - EYE * np.trace(a) / 3


def sphere_rule(nmu: int = 32, nphi: int = 24) -> tuple[np.ndarray, np.ndarray]:
    """Product rule normalized to unit mean; exact for low angular polynomials."""
    if nmu < 4 or nphi < 9:
        raise ValueError("angular rule too small for rank-four response")
    mu, weight = leggauss(nmu)
    phi = 2 * np.pi * np.arange(nphi) / nphi
    n = np.stack(np.broadcast_arrays(
        np.sqrt(1 - mu[:, None] ** 2) * np.cos(phi)[None, :],
        np.sqrt(1 - mu[:, None] ** 2) * np.sin(phi)[None, :],
        mu[:, None]), axis=-1).reshape(-1, 3)
    return n, np.repeat(weight / (2 * nphi), nphi)


def temperature_brightness(theta: np.ndarray) -> np.ndarray:
    """Exact bolometric Planckian-ray conversion I/I0=(1+Theta)^4.

    A calibrated thermodynamic-K channel may be used here only if its
    spectral/reference calibration establishes the full energy temperature.
    """
    theta = np.asarray(theta, dtype=float)
    if not np.all(np.isfinite(theta)) or np.any(1 + theta <= 0):
        raise ValueError("energy temperature must be finite and positive")
    return (1 + theta) ** 4


def stf4_direction(e: np.ndarray) -> np.ndarray:
    """Cartesian rank-four STF of a unit propagation direction."""
    e = np.asarray(e, dtype=float)
    if e.shape != (3,):
        raise ValueError("direction must have three components")
    first = np.einsum("i,j,k,l->ijkl", e, e, e, e)
    second = (np.einsum("ij,k,l->ijkl", EYE, e, e)
              + np.einsum("ik,j,l->ijkl", EYE, e, e)
              + np.einsum("il,j,k->ijkl", EYE, e, e)
              + np.einsum("jk,i,l->ijkl", EYE, e, e)
              + np.einsum("jl,i,k->ijkl", EYE, e, e)
              + np.einsum("kl,i,j->ijkl", EYE, e, e))
    third = (np.einsum("ij,kl->ijkl", EYE, EYE)
             + np.einsum("ik,jl->ijkl", EYE, EYE)
             + np.einsum("il,jk->ijkl", EYE, EYE))
    return first - second / 7 + third / 35


@dataclass(frozen=True)
class Moments:
    rho: float  # J m^-3
    flux: np.ndarray  # W m^-2 = c times energy-density vector
    pi: np.ndarray  # J m^-3
    h4: np.ndarray  # J m^-3, rank-four STF
    stress: np.ndarray  # T^{mu nu}, J m^-3; T^{0i}=flux_i/c


def moments(n: np.ndarray, weights: np.ndarray, brightness: np.ndarray,
            rho0: float, c: float = 299792458.0) -> Moments:
    """Map positive bolometric sky samples to physical moments and T^munu.

    Positive samples give a constructive member of the angular moment cone.
    The quadrature is a declared finite full-sky observation operator.
    """
    n, weights, brightness = map(lambda x: np.asarray(x, dtype=float),
                                 (n, weights, brightness))
    if (n.ndim != 2 or n.shape[1] != 3 or weights.shape != (len(n),)
            or brightness.shape != (len(n),)):
        raise ValueError("incompatible sky arrays")
    if (not np.all(np.isfinite(n)) or not np.all(np.isfinite(weights))
            or not np.all(np.isfinite(brightness)) or np.any(weights <= 0)
            or not np.isclose(weights.sum(), 1, atol=1e-12)
            or not np.allclose(np.linalg.norm(n, axis=1), 1, atol=1e-12)
            or np.any(brightness < 0) or np.sum(weights * brightness) <= 0
            or not np.isfinite(rho0) or rho0 <= 0 or not np.isfinite(c) or c <= 0):
        raise ValueError("outside positive physical moment construction")
    e = -n
    weighted = rho0 * weights * brightness
    rho = float(weighted.sum())
    j = np.einsum("n,ni->i", weighted, e)
    pressure = np.einsum("n,ni,nj->ij", weighted, e, e)
    pi = stf2(pressure)
    h4 = np.einsum("n,nijkl->ijkl", weighted,
                   np.array([stf4_direction(v) for v in e]))
    stress = np.empty((4, 4))
    stress[0, 0] = rho
    stress[0, 1:] = stress[1:, 0] = j
    stress[1:, 1:] = pressure
    return Moments(rho, c * j, pi, h4, stress)


def kappa(s: float) -> float:
    return 3 / (2 + np.sqrt(4 - 3 * s))


def stress_readout(m: Moments, c: float = 299792458.0) -> dict:
    """Exact finite-boost null D and rest-pressure anisotropy A_gamma."""
    f = m.flux / (c * m.rho)
    if f @ f >= 1:
        raise ValueError("timelike flux domain absent")
    p = m.pi / m.rho
    d = p - kappa(float(f @ f)) * stf2(np.outer(f, f))
    eigen, vectors = np.linalg.eig(m.stress @ ETA)
    if np.max(abs(eigen.imag)) > 1e-10 * m.rho:
        raise ValueError("non-real stress eigenvalues")
    timelike = [i for i in range(4)
                if np.real(vectors[:, i].conj() @ ETA @ vectors[:, i]) < -1e-10]
    if len(timelike) != 1:
        raise ValueError("unique timelike Landau eigenbranch absent")
    i = timelike[0]
    rho_l = float(-eigen[i].real)
    pressures = np.delete(eigen.real, i)
    a_gamma = float(np.linalg.norm(pressures - rho_l / 3) / rho_l)
    return {"f": f, "P": p, "D": d, "D_norm": float(np.linalg.norm(d)),
            "landau_rho": rho_l, "A_gamma": a_gamma}


def response_from_moments(m: Moments) -> np.ndarray:
    """Assemble L_I on the five orthonormal STF2 directions from ranks 0/2/4."""
    out = np.empty((5, 5))
    for j, s in enumerate(STF_BASIS):
        image = (8 * m.rho / 15 * s + 10 / 7 * stf2(s @ m.pi)
                 - np.einsum("abcd,cd->ab", m.h4, s))
        out[:, j] = np.einsum("aij,ij->a", STF_BASIS, image)
    return (out + out.T) / 2


def response_direct(n: np.ndarray, weights: np.ndarray,
                    brightness: np.ndarray, rho0: float) -> np.ndarray:
    """Independent angular-kernel evaluation of the same five-by-five matrix."""
    e = -np.asarray(n)
    se = np.einsum("aij,nj->nai", STF_BASIS, e)
    ese = np.einsum("ni,nai->na", e, se)
    kernel = 2 * np.einsum("nai,nbi->nab", se, se) - np.einsum(
        "na,nb->nab", ese, ese)
    out = rho0 * np.einsum("n,n,nab->ab", weights, brightness, kernel)
    return (out + out.T) / 2


def coercivity_diagnostic(weights: np.ndarray, brightness: np.ndarray,
                          response: np.ndarray, rho: float) -> dict:
    """Sufficient entropy bound and actual five-dimensional spectrum.

    The sufficient lower value 8/15-sqrt(8*delta/3) may fail while the
    measured finite operator stays positive. It is never interpreted as an
    observational error law or a confidence interval.
    """
    weights = np.asarray(weights, dtype=float)
    brightness = np.asarray(brightness, dtype=float)
    if np.any(brightness < 0) or rho <= 0 or not np.isclose(weights.sum(), 1):
        raise ValueError("invalid angular energy distribution")
    mean = float(weights @ brightness)
    normalized = brightness / mean
    delta = float(1 - weights @ normalized ** .75)
    bound = float(8 / 15 - np.sqrt(8 * max(delta, 0) / 3))
    eigen = np.linalg.eigvalsh(response / rho)
    return {"angular_entropy_deficit": delta,
            "sufficient_lower_over_rho": bound,
            "sufficient_certificate_pass": bool(bound > 0),
            "actual_eigenvalues_over_rho": eigen.tolist(),
            "actual_lambda_min_over_rho": float(eigen[0]),
            "actual_positive": bool(eigen[0] > 0)}


def temperature_multipoles(n: np.ndarray, d: np.ndarray, q: np.ndarray,
                           o: np.ndarray | None = None) -> np.ndarray:
    """Outward temperature dipole, STF quadrupole, optional STF octupole."""
    theta = n @ np.asarray(d) + np.einsum("ni,ij,nj->n", n, q, n)
    if o is not None:
        theta += np.einsum("ijk,ni,nj,nk->n", o, n, n, n)
    return theta


def linear_temperature_quadrupole(q: np.ndarray) -> np.ndarray:
    """First-order P≈D≈(8/15) Q^Theta on full-sky Planckian rays."""
    return 8 * stf2(q) / 15
