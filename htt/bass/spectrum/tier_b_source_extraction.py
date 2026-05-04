"""Tier-B → FLRWSourceTerms extractor (V5 Round-5 audit landing).

This module extracts the five callables consumed by the scalar FLRW LoS
projector (``bass/los/flrw_bessel_projector.py``) from the VER2 Tier-B
PSTF output. It deliberately separates two source frames:

* ``legacy_newtonian_constraint`` is the live BASS/PSTF production frame.
  It reconstructs potentials from the available density, velocity, and
  intensity-quadrupole histories.
* ``mb95_synchronous_effective`` is an opt-in frame. If the native result
  carries metadata-proven ``scalar_metric_history`` from
  ``IntegratorConfig.co_evolve_scalar_metric=True``, that co-evolved
  history is the authority. Otherwise this frame falls back to a
  diagnostic post-process reconstruction for oracle comparison only.

The extractor therefore does not claim to close the external CAMB scalar
closure gap by itself. It removes toy Sachs-Wolfe closures and makes the
remaining scalar-source frame choice explicit and testable.

Audit trail:
    - Round-5 prompt:  docs/V5_RUNTIME_TRACK_ALGEBRAIC_PROMPT_ROUND5.md
    - Round-5 answer:  v5_residual_harmonic_algebraic_audit_round5.md
    - Key corrections from the auditor:
      * Q-16/Q-17: the legacy live path treats the m=0 VER2 intensity
        moments as the PSTF source moments used by the BASS LoS contract.
        The MB-95 synchronous reconstruction is diagnostic-only unless the
        metric variables are co-evolved with the photon hierarchy. The
        co-evolved path is now metadata-gated and routed through BDF until
        an IMEX scalar-metric block exists.
      * Q-17: Einstein anisotropic stress depends on the INTENSITY
        quadrupoles Θ_2^γ, Θ_2^ν — NOT on Π = Θ_2 - √6·E_2. Π belongs
        to the Thomson source, intensity quadrupoles drive Ψ − Φ.
      * Q-17: MB normalization σ_γ = 2·Θ_2^γ, σ_ν = 2·Θ_2^ν so
        (ρ+p)·σ_tot = (8/3)·(ρ_γ·Θ_2^γ + ρ_ν·Θ_2^ν).
      * Q-20: Π = Θ_2 − √6·E_2 as written, no extra PSTF prefactor.

Legacy live-frame physics:
    Newtonian-gauge Einstein constraints (conformal time, Ma-Bertschinger
    convention):

        k² Φ + 3·ℋ·(Φ' + ℋ·Ψ) = 4πG·a²·δρ_tot
        k² (Φ' + ℋ·Ψ) = 4πG·a²·(ρ + p)·θ_tot        with θ = k·v
        Ψ − Φ = (12πG·a²/k²) · (ρ + p)·σ_tot          (anisotropic stress)

    Combining:
        Φ = (4πG·a²/k²) · [δρ_tot − 3ℋ·Σ_i (ρ_i+p_i)·v_i / k]
        Ψ = Φ + (12πG·a²/k²) · (ρ+p)·σ_tot

    BASS unit convention (species.bg_table.constants):
        ρ_bass = ρ_phys / ρ_crit,0 = dimensionless (in ρ_crit,0 units)
        H_0_mpc = H_0 / c = H_0 in 1/Mpc
        (H/H_0)² = ρ_tot_bass (flat-ΛCDM Friedmann residual=0)
        ⇒ 4πG = (3/2)·H_0² (in natural 1/Mpc² units)
        ⇒ 4πG·a²/k² = (3/2)·H_0_mpc²·a²/k²  (dimensionless)

ISW driver:
    In the legacy frame, Φ̇ + Ψ̇ is computed by 4th-order centered finite
    differences in the bulk, 2nd-order one-sided differences at the
    boundaries. In the MB-95 diagnostic frame the exported effective ISW
    driver is ``2 Φdot`` from the reconstructed ``etak/sigma`` history.

Interpolation:
    scipy.interpolate.PchipInterpolator with extrapolate=False — shape-
    preserving and does not ring near the recombination visibility peak.
    Callers evaluating outside [η_0, η_{N-1}] will receive NaN.

References:
    - Ma & Bertschinger 1995 (synchronous ↔ Newtonian gauge dictionary,
      ρ·v convention, θ = k·v, σ = 2·Θ_2 for radiation)
    - Ellis & van Elst 1998 (1+3 covariant PSTF formalism, gauge-
      invariance of ℓ≥1 multipoles around FRW)
    - Seljak & Zaldarriaga 1996 (LoS source assembly)
    - Kamionkowski, Kosowsky, Stebbins 1997 (Π decomposition)
"""
from __future__ import annotations

import warnings
from dataclasses import dataclass
from typing import TYPE_CHECKING, Literal

import numpy as np
from scipy.interpolate import PchipInterpolator

from bass.los.flrw_bessel_projector import FLRWSourceTerms

if TYPE_CHECKING:
    from bass.hierarchy.integrator import IntegrationResult
    from bass.species.registry import SpeciesBackgroundRegistry


__all__ = [
    "SynchronousMetricHistory",
    "extract_flrw_sources_from_tier_b",
    "reconstruct_synchronous_metric_history_from_tier_b",
    "_slot",
    "_fd4_derivative",
]


_SQRT6 = float(np.sqrt(6.0))

SourceFrame = Literal[
    "mb95_synchronous_effective",
    "legacy_newtonian_constraint",
]


@dataclass(frozen=True)
class SynchronousMetricHistory:
    """Post-processed MB-95 synchronous scalar metric history.

    The VER2 Tier-B state historically evolved photon/neutrino/matter
    histories without carrying the two scalar metric variables used by
    CAMB's synchronous-gauge source path.  This object reconstructs the
    missing ``etak`` and ``sigma`` channels from the live radiation and
    baryon histories using the same momentum/stress equations as the Rust
    MB-95/PSTF-primary path:

        etak'  = dgq / 2
        sigma' = -2 H sigma - dgs / k + etak

    The initial condition uses Lowell/CAMB seed ``eta_cov = -2 eta_s``.
    The corresponding ``sigma`` seed is not present in the packed Python
    seed yet, so the current authority bridge uses the regular superhorizon
    ``sigma(eta_initial)=0`` condition and records that policy explicitly.
    """

    eta: np.ndarray
    etak: np.ndarray
    sigma: np.ndarray
    etak_dot: np.ndarray
    sigma_dot: np.ndarray
    hdot: np.ndarray
    phi: np.ndarray
    psi_newtonian_no_stress: np.ndarray
    psi_effective_sw: np.ndarray
    isw_driver: np.ndarray
    doppler_velocity_effective: np.ndarray
    metadata: dict[str, object]


def _slot(ell: int, m: int) -> int:
    """Real-spherical-harmonic packed slot index: ``ℓ² + (m + ℓ)``."""
    return ell * ell + (m + ell)


def _fd4_derivative(x: np.ndarray, y: np.ndarray) -> np.ndarray:
    """Finite-difference derivative matching the Round-5 Q-18.2 recipe.

    - 4th-order centered in the bulk,
    - 2nd-order one-sided at the two outermost points,
    - 2nd-order centered at indices 1 and N-2 (not enough neighbours
      for 4th-order stencil).

    Works on non-uniform grids via the local spacing ``h = (x[i+1] − x[i−1])/2``.
    """
    x = np.asarray(x, dtype=np.float64)
    y = np.asarray(y, dtype=np.float64)
    n = x.size
    if y.shape != x.shape:
        raise ValueError(
            f"_fd4_derivative requires y.shape == x.shape, got "
            f"y.shape={y.shape}, x.shape={x.shape}"
        )
    if n < 5:
        raise ValueError(f"_fd4_derivative requires at least 5 points; got {n}")

    dydx = np.empty_like(y)
    # 2nd-order one-sided at boundaries:
    dydx[0] = (-3.0 * y[0] + 4.0 * y[1] - y[2]) / (x[2] - x[0])
    dydx[-1] = (3.0 * y[-1] - 4.0 * y[-2] + y[-3]) / (x[-1] - x[-3])
    # 2nd-order centered at indices 1 and N-2 (not enough room for 4th order):
    dydx[1] = (y[2] - y[0]) / (x[2] - x[0])
    dydx[-2] = (y[-1] - y[-3]) / (x[-1] - x[-3])
    # 4th-order centered in the bulk (non-uniform grid via local h).
    # Vectorized equivalent of the original i=2..N-3 loop with
    # h_i = (x[i+1] - x[i-1]) / 2.
    dydx[2:-2] = (
        -y[4:]
        + 8.0 * y[3:-1]
        - 8.0 * y[1:-3]
        + y[:-4]
    ) / (6.0 * (x[3:-1] - x[1:-3]))
    return dydx


def _scaled_pchip_no_extrapolation(eta_grid: np.ndarray, values: np.ndarray):
    """Build a no-extrapolation PCHIP callable after amplitude scaling.

    Some Tier-B probe channels are finite but extremely small. Constructing
    scipy's PCHIP slopes directly on subnormal-scale values can raise an
    internal overflow RuntimeWarning in the reciprocal-slope harmonic mean.
    Scaling to O(1) before construction preserves the interpolated function
    and avoids treating that numerical conditioning detail as physics failure.
    """

    eta_arr = np.asarray(eta_grid, dtype=np.float64)
    values_arr = np.asarray(values, dtype=np.float64)
    if values_arr.shape != eta_arr.shape:
        raise ValueError(
            "PCHIP source interpolation requires values.shape == eta_grid.shape, "
            f"got values.shape={values_arr.shape}, eta_grid.shape={eta_arr.shape}"
        )
    if not np.all(np.isfinite(values_arr)):
        raise ValueError("PCHIP source interpolation requires finite values")
    amplitude = float(np.max(np.abs(values_arr)))
    if amplitude == 0.0:
        return PchipInterpolator(eta_arr, values_arr, extrapolate=False)
    scaled = values_arr / amplitude
    try:
        with warnings.catch_warnings():
            warnings.filterwarnings(
                "error",
                message="overflow encountered in divide",
                category=RuntimeWarning,
            )
            interp = PchipInterpolator(eta_arr, scaled, extrapolate=False)
    except RuntimeWarning:
        return _linear_no_extrapolation(eta_arr, values_arr)

    def _call(query):
        return amplitude * interp(query)

    return _call


def _linear_no_extrapolation(eta_grid: np.ndarray, values: np.ndarray):
    """Linear no-extrapolation fallback for finite but PCHIP-ill-conditioned data."""

    eta_arr = np.asarray(eta_grid, dtype=np.float64)
    values_arr = np.asarray(values, dtype=np.float64)

    def _call(query):
        query_arr = np.asarray(query, dtype=np.float64)
        out = np.interp(query_arr, eta_arr, values_arr)
        out = np.asarray(out, dtype=np.float64)
        out = np.where(
            (query_arr < eta_arr[0]) | (query_arr > eta_arr[-1]),
            np.nan,
            out,
        )
        if np.ndim(query_arr) == 0:
            return float(out)
        return out

    return _call


def _required_history_arrays(
    integration_result: "IntegrationResult",
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Return the Tier-B histories required by scalar source extraction."""

    if integration_result.neutrino_tower is None:
        raise ValueError(
            "integration_result.neutrino_tower is required for the "
            "Tier-B source extractor (neutrino anisotropic stress and density)"
        )
    if integration_result.baryon_local_history is None:
        raise ValueError(
            "integration_result.baryon_local_history is required "
            "(slot 1 = v_b in MB convention)"
        )
    if integration_result.cdm_local_history is None:
        raise ValueError(
            "integration_result.cdm_local_history is required "
            "(slot 1 = v_c)"
        )

    return (
        np.asarray(integration_result.eta, dtype=np.float64),
        np.asarray(integration_result.photon_T_tower, dtype=np.float64),
        np.asarray(integration_result.photon_E_tower, dtype=np.float64),
        np.asarray(integration_result.neutrino_tower, dtype=np.float64),
        np.asarray(integration_result.baryon_local_history, dtype=np.float64),
        np.asarray(integration_result.cdm_local_history, dtype=np.float64),
        np.asarray(integration_result.a, dtype=np.float64),
    )


def _validate_packed_tower_width(t_tower: np.ndarray) -> int:
    l_max_plus_one_sq = int(t_tower.shape[1])
    l_max = int(np.sqrt(l_max_plus_one_sq)) - 1
    if (l_max + 1) ** 2 != l_max_plus_one_sq:
        raise ValueError(
            f"photon_T_tower shape {t_tower.shape} is not a (L+1)^2 packing"
        )
    if l_max < 2:
        raise ValueError(
            f"extract_flrw_sources_from_tier_b needs L_max >= 2 "
            f"(quadrupoles are required); got {l_max}"
        )
    return l_max


def _grho_from_species(
    species: "SpeciesBackgroundRegistry",
    eta: np.ndarray,
    a: np.ndarray,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Return MB-95 ``grho_i = 8*pi*G*a^2*rho_i`` histories."""

    from bass.species.base import SpeciesLabel

    h0_mpc = float(species.bg_table.constants.H0_mpc)
    prefactor = 3.0 * (h0_mpc ** 2) * (np.asarray(a, dtype=np.float64) ** 2)
    rho_g = np.asarray(species[SpeciesLabel.PHOTON].rho_rest(eta), dtype=np.float64)
    rho_nu = np.asarray(species[SpeciesLabel.NEUTRINO].rho_rest(eta), dtype=np.float64)
    rho_b = np.asarray(species[SpeciesLabel.BARYON].rho_rest(eta), dtype=np.float64)
    rho_c = np.asarray(species[SpeciesLabel.CDM].rho_rest(eta), dtype=np.float64)
    return (
        prefactor * rho_g,
        prefactor * rho_nu,
        prefactor * rho_b,
        prefactor * rho_c,
    )


def _seed_metric_initial_conditions(
    integration_result: "IntegrationResult",
    k: float,
) -> tuple[float, float, dict[str, object]]:
    """Map packed Lowell regular seed metric extras to MB-95 variables."""

    seed_obs = dict(integration_result.solver_info.get("matter_seed_observables", {}))
    if "eta_cov" not in seed_obs:
        raise ValueError(
            "mb95_synchronous_effective source extraction requires "
            "integration_result.solver_info['matter_seed_observables']['eta_cov']; "
            "rerun the native Tier-B solver after the seed-provenance upgrade "
            "or request source_frame='legacy_newtonian_constraint' explicitly"
        )
    eta_cov = float(seed_obs["eta_cov"])
    if not np.isfinite(eta_cov):
        raise ValueError(f"seed eta_cov must be finite, got {eta_cov!r}")

    # Lowell/CAMB seed convention: eta_cov is the MB eta variable
    # eta_MB = -2 eta_s, while CAMB stores etak = k eta_s.
    etak0 = -0.5 * float(k) * eta_cov
    sigma0 = float(seed_obs.get("sigma_sync", 0.0))
    if not np.isfinite(sigma0):
        raise ValueError(f"seed sigma_sync must be finite, got {sigma0!r}")
    return (
        float(etak0),
        sigma0,
        {
            "eta_cov": eta_cov,
            "etak_initial": float(etak0),
            "sigma_initial": sigma0,
            "sigma_initial_policy": (
                "seed_sigma_sync"
                if "sigma_sync" in seed_obs
                else "zero_regular_superhorizon_bridge"
            ),
        },
    )


def reconstruct_synchronous_metric_history_from_tier_b(
    integration_result: "IntegrationResult",
    species: "SpeciesBackgroundRegistry",
    k: float,
) -> SynchronousMetricHistory:
    """Reconstruct MB-95 synchronous scalar metric channels on the Tier-B grid."""

    if not (float(k) > 0.0):
        raise ValueError(f"k must be positive, got {k!r}")
    eta, t_tower, _e_tower, n_tower, baryon_hist, _cdm_hist, a_result = (
        _required_history_arrays(integration_result)
    )
    if eta.size < 5:
        raise ValueError(
            f"reconstruct_synchronous_metric_history_from_tier_b needs >=5 eta "
            f"samples; got {eta.size}"
        )
    if np.any(np.diff(eta) <= 0.0):
        raise ValueError("eta grid must be strictly increasing")
    l_max = _validate_packed_tower_width(t_tower)
    if n_tower.shape[1] != t_tower.shape[1]:
        raise ValueError(
            "neutrino_tower must use the same packed width as photon_T_tower"
        )

    bg_table = species.bg_table
    a = np.asarray(bg_table.interp_a(eta), dtype=np.float64)
    if a.shape != eta.shape or not np.all(np.isfinite(a)):
        a = np.asarray(a_result, dtype=np.float64)
    calH = np.asarray(bg_table.interp_calH(eta), dtype=np.float64)
    grho_g, grho_nu, grho_b, _grho_c = _grho_from_species(species, eta, a)

    theta1 = np.asarray(t_tower[:, _slot(1, 0)], dtype=np.float64)
    theta2 = np.asarray(t_tower[:, _slot(2, 0)], dtype=np.float64)
    nu1 = np.asarray(n_tower[:, _slot(1, 0)], dtype=np.float64)
    nu2 = np.asarray(n_tower[:, _slot(2, 0)], dtype=np.float64)
    vb = np.asarray(baryon_hist[:, 1], dtype=np.float64)

    arrays = (calH, grho_g, grho_nu, grho_b, theta1, theta2, nu1, nu2, vb)
    if any(arr.shape != eta.shape for arr in arrays):
        raise ValueError("metric reconstruction inputs must match eta shape")
    if any(not np.all(np.isfinite(arr)) for arr in arrays):
        raise ValueError("metric reconstruction inputs must be finite")

    interp = {
        "calH": _scaled_pchip_no_extrapolation(eta, calH),
        "grho_g": _scaled_pchip_no_extrapolation(eta, grho_g),
        "grho_nu": _scaled_pchip_no_extrapolation(eta, grho_nu),
        "grho_b": _scaled_pchip_no_extrapolation(eta, grho_b),
        "theta1": _scaled_pchip_no_extrapolation(eta, theta1),
        "theta2": _scaled_pchip_no_extrapolation(eta, theta2),
        "nu1": _scaled_pchip_no_extrapolation(eta, nu1),
        "nu2": _scaled_pchip_no_extrapolation(eta, nu2),
        "vb": _scaled_pchip_no_extrapolation(eta, vb),
    }

    def _rhs(eta_value: float, y: np.ndarray) -> np.ndarray:
        etak_val = float(y[0])
        sigma_val = float(y[1])
        h_val = float(interp["calH"](eta_value))
        rg = float(interp["grho_g"](eta_value))
        rn = float(interp["grho_nu"](eta_value))
        rb = float(interp["grho_b"](eta_value))
        th1 = float(interp["theta1"](eta_value))
        th2 = float(interp["theta2"](eta_value))
        n1 = float(interp["nu1"](eta_value))
        n2 = float(interp["nu2"](eta_value))
        vb_val = float(interp["vb"](eta_value))
        dgq = (16.0 / 3.0) * (rg * th1 + rn * n1) + rb * vb_val
        dgs = 4.0 * (rg * th2 + rn * n2)
        etak_dot_val = 0.5 * dgq
        sigma_dot_val = -2.0 * h_val * sigma_val - dgs / float(k) + etak_val
        return np.array([etak_dot_val, sigma_dot_val], dtype=np.float64)

    scalar_metric_history = getattr(integration_result, "scalar_metric_history", None)
    scalar_metric_metadata = dict(
        integration_result.solver_info.get("scalar_metric_history_metadata", {})
    )
    use_coevolved_metric = bool(
        scalar_metric_history is not None
        and scalar_metric_metadata.get("owner") == "ver2_native_integrator.main_state_scalar_metric"
        and scalar_metric_metadata.get("photon_neutrino_monopole_coupled") is True
        and scalar_metric_metadata.get("photon_neutrino_quadrupole_coupled") is True
        and scalar_metric_metadata.get("matter_continuity_coupled") is True
        and scalar_metric_metadata.get("baryon_euler_pressure_coupled") is True
    )
    if use_coevolved_metric:
        scalar_arr = np.asarray(scalar_metric_history, dtype=np.float64)
        if scalar_arr.shape != (eta.size, 2):
            raise ValueError("scalar_metric_history must have shape (len(eta), 2)")
        if not np.all(np.isfinite(scalar_arr)):
            raise ValueError("scalar_metric_history must be finite")
        etak = np.asarray(scalar_arr[:, 0], dtype=np.float64)
        sigma = np.asarray(scalar_arr[:, 1], dtype=np.float64)
        seed_meta = {
            "co_evolved_metric_source": "integration_result.scalar_metric_history",
            "co_evolved_metric_metadata": scalar_metric_metadata,
        }
        integration_scheme = "main_state_coevolved"
        owner = "ver2_native_integrator.main_state_scalar_metric"
    else:
        etak0, sigma0, seed_meta = _seed_metric_initial_conditions(
            integration_result, float(k)
        )
        y = np.array([etak0, sigma0], dtype=np.float64)
        etak = np.empty_like(eta)
        sigma = np.empty_like(eta)
        etak[0] = y[0]
        sigma[0] = y[1]
        for idx in range(eta.size - 1):
            left = float(eta[idx])
            right = float(eta[idx + 1])
            h_step = right - left
            if h_step <= 0.0:
                raise ValueError("eta grid must be strictly increasing")
            k1 = _rhs(left, y)
            k2 = _rhs(left + 0.5 * h_step, y + 0.5 * h_step * k1)
            k3 = _rhs(left + 0.5 * h_step, y + 0.5 * h_step * k2)
            k4 = _rhs(right, y + h_step * k3)
            y = y + (h_step / 6.0) * (k1 + 2.0 * k2 + 2.0 * k3 + k4)
            if not np.all(np.isfinite(y)):
                raise RuntimeError(
                    f"synchronous metric reconstruction became non-finite at step {idx}"
                )
            etak[idx + 1] = y[0]
            sigma[idx + 1] = y[1]
        integration_scheme = "output_grid_rk4"
        owner = "tier_b_source_extraction.mb95_synchronous_metric_postprocessor"
    rhs_vals = np.asarray([_rhs(float(x), np.array([e, s])) for x, e, s in zip(eta, etak, sigma)])
    etak_dot = rhs_vals[:, 0]
    sigma_dot = rhs_vals[:, 1]
    hdot = 2.0 * float(k) * sigma - 6.0 * etak_dot / float(k)
    phi = etak / float(k) - calH * sigma / float(k)
    eta_mb = -2.0 * etak / float(k)
    psi_effective_sw = 2.0 * phi + 0.5 * eta_mb
    isw_driver = 2.0 * _fd4_derivative(eta, phi)
    doppler_velocity_effective = (sigma + vb) / float(k)

    if not all(
        np.all(np.isfinite(arr))
        for arr in (
            etak,
            sigma,
            etak_dot,
            sigma_dot,
            hdot,
            phi,
            psi_effective_sw,
            isw_driver,
            doppler_velocity_effective,
        )
    ):
        raise RuntimeError("synchronous metric reconstruction produced non-finite values")

    return SynchronousMetricHistory(
        eta=eta,
        etak=etak,
        sigma=sigma,
        etak_dot=etak_dot,
        sigma_dot=sigma_dot,
        hdot=hdot,
        phi=phi,
        psi_newtonian_no_stress=-phi,
        psi_effective_sw=psi_effective_sw,
        isw_driver=isw_driver,
        doppler_velocity_effective=doppler_velocity_effective,
        metadata={
            "owner": owner,
            "integration_scheme": integration_scheme,
            "metric_equations": "etak_dot=dgq/2; sigma_dot=-2Hsigma-dgs/k+etak",
            "source_equivalence": (
                "FLRWSourceTerms are effective: theta0+psi reproduces "
                "MB95 SW term and v_b reproduces d[g(sigma+vb)/k]/deta"
            ),
            "l_max": int(l_max),
            "k_mpc": float(k),
            **seed_meta,
        },
    )


def extract_flrw_sources_from_tier_b(
    integration_result: "IntegrationResult",
    species: "SpeciesBackgroundRegistry",
    k: float,
    *,
    anisotropic_stress: bool = True,
    source_frame: SourceFrame = "legacy_newtonian_constraint",
) -> FLRWSourceTerms:
    """Build Newtonian-gauge ``FLRWSourceTerms`` from a Tier-B solver output.

    Parameters
    ----------
    integration_result
        Output of ``execute_tier_b_solver``. Must carry
        ``photon_T_tower``, ``photon_E_tower``, ``neutrino_tower``,
        ``baryon_local_history``, ``cdm_local_history``, and ``eta``.
    species
        ``SpeciesBackgroundRegistry.from_planck2018()`` (or equivalent).
        Provides per-species ``ρ_rest(η)`` and the FLRW background table
        ``bg_table.interp_a``, ``interp_calH`` in Mpc⁻¹.
    k
        Comoving wavenumber at which the Tier-B solver was run
        (Mpc⁻¹). Must match the ``k_grid_mpc`` argument passed to
        ``execute_tier_b_solver`` — the tower state is stored at this
        single k.
    anisotropic_stress
        If True (default), include the intensity-quadrupole stress
        correction ``Ψ − Φ = (12πG·a²/k²)·(ρ+p)·σ_tot``. If False,
        set ``Ψ = Φ`` (no-stress limit). This option applies only to
        ``source_frame='legacy_newtonian_constraint'``.
    source_frame
        ``'legacy_newtonian_constraint'`` (default) preserves the
        PSTF-native algebraic Poisson reconstruction used by the live
        BASS FLRW pipeline. ``'mb95_synchronous_effective'`` reconstructs
        or consumes co-evolved CAMB synchronous metric variables ``etak``
        and ``sigma`` and returns effective ``FLRWSourceTerms``. It is
        intentionally opt-in because only results with active
        ``scalar_metric_history`` metadata have a co-evolved MB-95
        monopole, quadrupole, scalar free-streaming, matter-continuity, and
        baryon-pressure source; otherwise the metric history is post-processed.

    Returns
    -------
    FLRWSourceTerms with 5 η-callables:
        theta_0(η) → Θ_0^γ(η)
        psi(η)    → Ψ(η, k)  (Newtonian-gauge potential)
        phi_dot_plus_psi_dot(η) → Φ̇(η, k) + Ψ̇(η, k)  (ISW driver)
        v_b(η)    → v_b(η)  (baryon peculiar velocity at this k)
        pi(η)     → Θ_2^γ(η) − √6·E_2^γ(η)  (polarization source)

    All callables are no-extrapolation PCHIP-based callables with
    ``extrapolate=False``; evaluation outside the integration-result
    η-domain returns NaN.

    Raises
    ------
    ValueError
        If the integration_result is missing a required tower array
        (neutrino_tower, photon_B_tower, baryon_local_history,
        cdm_local_history); if k ≤ 0; or if the photon/neutrino
        tower widths are inconsistent with the integration_result's
        L_max.
    """

    if not (float(k) > 0.0):
        raise ValueError(f"k must be positive, got {k!r}")
    if source_frame not in ("mb95_synchronous_effective", "legacy_newtonian_constraint"):
        raise ValueError(
            "source_frame must be 'mb95_synchronous_effective' or "
            f"'legacy_newtonian_constraint', got {source_frame!r}"
        )

    eta, t_tower, e_tower, n_tower, baryon_history, cdm_history, _a_result = (
        _required_history_arrays(integration_result)
    )
    if eta.size < 5:
        raise ValueError(
            f"extract_flrw_sources_from_tier_b needs ≥5 η samples for "
            f"the 4th-order ISW finite-difference stencil; got {eta.size}"
        )
    if np.any(np.diff(eta) <= 0.0):
        raise ValueError("eta grid must be strictly increasing")

    # Background a(η) and conformal Hubble ℋ(η) in 1/Mpc from the species
    # registry's frozen bg_table (unit-consistent with k_mpc).
    bg_table = species.bg_table
    a = np.asarray(bg_table.interp_a(eta), dtype=np.float64)
    calH = np.asarray(bg_table.interp_calH(eta), dtype=np.float64)

    # Q-16 / Q-17.1 PSTF → Newtonian-gauge scalar multipoles (m = 0):
    l_max = _validate_packed_tower_width(t_tower)
    if e_tower.shape != t_tower.shape or n_tower.shape != t_tower.shape:
        raise ValueError("photon_E_tower and neutrino_tower must match photon_T_tower shape")

    theta0_g = t_tower[:, _slot(0, 0)]
    theta1_g = t_tower[:, _slot(1, 0)]
    theta2_g = t_tower[:, _slot(2, 0)]
    e2_g = e_tower[:, _slot(2, 0)]

    theta0_nu = n_tower[:, _slot(0, 0)]
    theta1_nu = n_tower[:, _slot(1, 0)]
    theta2_nu = n_tower[:, _slot(2, 0)]

    # Q-20: Π = Θ_2 − √6·E_2 with α_T = 1, α_E = −√6; no extra PSTF prefactor.
    pi_source = theta0_g.copy()  # allocate correct dtype/shape
    pi_source[:] = theta2_g - _SQRT6 * e2_g

    if source_frame == "mb95_synchronous_effective":
        metric = reconstruct_synchronous_metric_history_from_tier_b(
            integration_result,
            species,
            float(k),
        )
        return FLRWSourceTerms(
            theta_0=_scaled_pchip_no_extrapolation(eta, theta0_g),
            psi=_scaled_pchip_no_extrapolation(eta, metric.psi_effective_sw),
            phi_dot_plus_psi_dot=_scaled_pchip_no_extrapolation(
                eta, metric.isw_driver,
            ),
            v_b=_scaled_pchip_no_extrapolation(
                eta, metric.doppler_velocity_effective,
            ),
            pi=_scaled_pchip_no_extrapolation(eta, pi_source),
        )

    from bass.species.base import SpeciesLabel

    # Q-19: baryon_local_history slot dictionary (verified via
    # ver2_native_integrator.py line 2973 and cross-checked against
    # Round-2 Q-5.1 Thomson coupling using slot 1 = v_b).
    delta_b = np.asarray(baryon_history[:, 0], dtype=np.float64)
    vb = np.asarray(baryon_history[:, 1], dtype=np.float64)
    delta_c = np.asarray(cdm_history[:, 0], dtype=np.float64)
    vc = np.asarray(cdm_history[:, 1], dtype=np.float64)

    # Q-17.1: radiation density contrasts δ_r = 4·Θ_0, velocities v_r = 3·Θ_1
    # (MB convention θ_r = 3·k·Θ_1, v = θ/k).
    delta_g = 4.0 * theta0_g
    delta_nu = 4.0 * theta0_nu
    vg = 3.0 * theta1_g
    vnu = 3.0 * theta1_nu

    # Per-species background densities (dimensionless, ρ_crit,0 units).
    rho_b = np.asarray(
        species[SpeciesLabel.BARYON].rho_rest(eta), dtype=np.float64
    )
    rho_c = np.asarray(
        species[SpeciesLabel.CDM].rho_rest(eta), dtype=np.float64
    )
    rho_g = np.asarray(
        species[SpeciesLabel.PHOTON].rho_rest(eta), dtype=np.float64
    )
    rho_nu = np.asarray(
        species[SpeciesLabel.NEUTRINO].rho_rest(eta), dtype=np.float64
    )

    # Q-17.2 Einstein constraints in BASS natural units.
    # Friedmann flat-ΛCDM: (H/H_0)² = ρ_tot_bass ⇒ 4πG·a² = (3/2)·H_0²·a².
    h0_mpc = float(bg_table.constants.H0_mpc)  # 1/Mpc
    four_pi_g_a2_over_k2 = 1.5 * (h0_mpc ** 2) * (a ** 2) / (float(k) ** 2)

    delta_rho_tot = (
        rho_b * delta_b + rho_c * delta_c + rho_g * delta_g + rho_nu * delta_nu
    )
    # Σ_i (ρ_i + p_i)·v_i:  non-relativistic species have p=0, radiation p = ρ/3
    # so (ρ+p) = (4/3)·ρ.
    mom = (
        rho_b * vb
        + rho_c * vc
        + (4.0 / 3.0) * rho_g * vg
        + (4.0 / 3.0) * rho_nu * vnu
    )
    phi = four_pi_g_a2_over_k2 * (delta_rho_tot - 3.0 * calH * mom / float(k))

    # Q-17.2 + auditor correction: anisotropic stress from intensity
    # quadrupoles only. MB σ_r = 2·Θ_2^r ⇒ (ρ+p)·σ = (8/3)·ρ_r·Θ_2^r.
    if anisotropic_stress:
        stress_intensity = (
            (8.0 / 3.0) * rho_g * theta2_g + (8.0 / 3.0) * rho_nu * theta2_nu
        )
        psi_minus_phi = 3.0 * four_pi_g_a2_over_k2 * stress_intensity
    else:
        psi_minus_phi = np.zeros_like(phi)
    psi = phi + psi_minus_phi

    # Q-18: ISW driver via 4th-order centered FD on the (Φ + Ψ) grid.
    phi_plus_psi = phi + psi
    phi_dot_plus_psi_dot = _fd4_derivative(eta, phi_plus_psi)

    return FLRWSourceTerms(
        theta_0=_scaled_pchip_no_extrapolation(eta, theta0_g),
        psi=_scaled_pchip_no_extrapolation(eta, psi),
        phi_dot_plus_psi_dot=_scaled_pchip_no_extrapolation(eta, phi_dot_plus_psi_dot),
        v_b=_scaled_pchip_no_extrapolation(eta, vb),
        pi=_scaled_pchip_no_extrapolation(eta, pi_source),
    )
