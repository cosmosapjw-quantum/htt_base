"""NT2-B2 / NT2-B3: GR shear-memory-sourced depth transport + vorticity blind sector.

NT2-B2 (sourced transport). The report's NT-B3 says a depth-steady shear leaves
no depth contrast but leaves the *source* of any contrast unattributed. PAPER-B's
shear-memory law sigma_dot = -3 H sigma + 3 H^2 Pi (the dimensionally consistent
form, B-shear) makes the tilt anisotropic stress Pi(z) the explicit GR source of
the depth-evolving shear, hence of F_shear(z) = sigma(z)^2/x_max, hence of the
depth gap G_F(z). Steady Pi -> sigma relaxes to a constant -> flat G_F;
depth-growing Pi(z) -> growing sigma -> depth-dependent G_F. This upgrades NT-B3's
"attribution" to a *mechanism*.

NT2-B3 (joint blind sector no-go). The vorticity term W^2_std in x_C is
unconstrained by BOTH observational channels the program uses, simultaneously:
(i) CMB temperature multipoles (to EGS order) do not bound the curl/magnetic-Weyl
sector (H3/Weyl loophole) -> sensitivity 0; (ii) radial peculiar-velocity data
carry no vorticity, since n^a Omega_ab n^b = 0 exactly for any antisymmetric Omega
(PAPER-A A-radial-novortex). The union closes both channels: no estimator on
CMB-temperature + radial velocities alone can constrain the comparator's vorticity.

Analytic-check constructs; the scalarized shear-memory ODE uses a depth-like
parameter. No detection is implied.
"""
from __future__ import annotations

from dataclasses import dataclass
import numpy as np

from .egs2_fisher import X_MAX


def integrate_shear_memory(pi_of_z, z_grid, H: float = 1.0, sigma0: float = 0.0) -> list[tuple[float, float]]:
    """RK4-integrate the scalarized shear-memory sigma' = -3 H sigma + 3 H^2 Pi(z)
    over a depth-like grid. Returns [(z, sigma(z)), ...] from the second node on."""
    z = np.asarray(z_grid, dtype=float)
    if z.ndim != 1 or z.size < 2 or np.any(np.diff(z) <= 0):
        raise ValueError("z_grid must be strictly increasing with >= 2 nodes")
    sig = float(sigma0)
    out: list[tuple[float, float]] = []
    for i in range(z.size - 1):
        z0, z1 = float(z[i]), float(z[i + 1])
        h = z1 - z0

        def f(zz: float, s: float) -> float:
            return -3.0 * H * s + 3.0 * H * H * float(pi_of_z(zz))
        k1 = f(z0, sig)
        k2 = f(z0 + h / 2, sig + h / 2 * k1)
        k3 = f(z0 + h / 2, sig + h / 2 * k2)
        k4 = f(z1, sig + h * k3)
        sig = sig + h / 6 * (k1 + 2 * k2 + 2 * k3 + k4)
        out.append((z1, sig))
    return out


def depth_gap_from_shear(shear_track: list[tuple[float, float]], x_max: float = X_MAX) -> list[tuple[float, float]]:
    """G_F(z) = F(z)/F(z_ref=mid), with F(z) = sigma(z)^2 / x_max."""
    F = [(z, s * s / x_max) for z, s in shear_track]
    ref = F[len(F) // 2][1]
    return [(z, (f / ref if ref else 0.0)) for z, f in F]


@dataclass(frozen=True)
class SourcedTransport:
    steady_gap_spread: float
    growing_gap_spread: float
    sourced: bool


def sourced_depth_transport(z_grid=None, H: float = 1.0, sigma0: float = 1e-3,
                            pi_level: float = 1e-3, growth: float = 4.0) -> SourcedTransport:
    """NT2-B2 check: steady tilt stress -> flat G_F; depth-growing tilt stress
    Pi(z) ~ (1 + growth*z) -> depth-evolving G_F. The depth gap is GR-sourced."""
    if z_grid is None:
        z_grid = [i * 0.1 for i in range(11)]
    steady = depth_gap_from_shear(integrate_shear_memory(lambda z: pi_level, z_grid, H, sigma0))
    grow = depth_gap_from_shear(
        integrate_shear_memory(lambda z: pi_level * (1.0 + growth * z), z_grid, H, sigma0))
    s_spread = max(g for _, g in steady) - min(g for _, g in steady)
    g_spread = max(g for _, g in grow) - min(g for _, g in grow)
    return SourcedTransport(s_spread, g_spread, sourced=bool(g_spread > 10.0 * max(s_spread, 1e-12)))


def cmb_temperature_vorticity_sensitivity(W2: float) -> float:
    """NT2-B3 (i): CMB temperature multipoles do not source on the curl/
    magnetic-Weyl sector at EGS order (Weyl loophole) -> sensitivity 0."""
    return 0.0


def radial_vorticity_projection(omega_vec, n_hat) -> float:
    """NT2-B3 (ii): n^a Omega_ab n^b for an antisymmetric Omega built from the
    axial vector omega (Omega_ab n^b = omega x n); dotted with n it is identically 0."""
    omega = np.asarray(omega_vec, dtype=float)
    n = np.asarray(n_hat, dtype=float)
    return float(np.dot(np.cross(omega, n), n))


@dataclass(frozen=True)
class BlindSector:
    cmb_max_sensitivity: float
    radial_max_projection: float
    n_configs: int
    joint_blind: bool


def vorticity_blind_sector(n_configs: int = 1000, seed: int = 33) -> BlindSector:
    """NT2-B3: both channels are blind to the vorticity term simultaneously."""
    rng = np.random.default_rng(seed)
    cmb_max = max(abs(cmb_temperature_vorticity_sensitivity(W2)) for W2 in (1e-6, 1e-3, 1.0))
    radial_max = 0.0
    for _ in range(n_configs):
        omega = rng.normal(size=3)
        n = rng.normal(size=3)
        n = n / np.linalg.norm(n)
        radial_max = max(radial_max, abs(radial_vorticity_projection(omega, n)))
    return BlindSector(cmb_max, radial_max, n_configs,
                       joint_blind=bool(cmb_max == 0.0 and radial_max < 1e-12))
