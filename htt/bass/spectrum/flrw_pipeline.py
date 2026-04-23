"""FLRW end-to-end D_ℓ pipeline for low-ℓ CAMB cross-checks (S8).

Bridges the v5 transport / assembly machinery into a single call that
consumes a Planck-like cosmology and emits ``D_ℓ^{TT, EE, TE}`` for
ℓ = 2..ℓ_max. The analytic layer uses the **Sachs–Wolfe plateau**
approximation:

* ``(Θ₀ + Ψ)_* = -R_k / 5`` (matter-dominated limit, adiabatic IC),
* ``Δ_ℓ^T(k) = -(1/5) · j_ℓ(k · Δη_*)`` (sharp-visibility limit),
* ``Δ_ℓ^E(k) ≈ 0`` on the plateau (tight-coupling suppression).

This is NOT a full Boltzmann calculation — it omits integrated
Sachs–Wolfe, Doppler, tight-coupling acoustic amplification, and
reionization re-scattering. CAMB at τ = 0.0544 lensed/unlensed for the
same cosmology is ~1022 μK² at D_2; the pure-SW plateau produces
~600-700 μK². The residual (gap / CAMB) is the validation surface for
a follow-up Tier-B bridge that wires ``execute_tier_b_solver`` into
the source callables.

Module surface:

* :class:`FLRWCosmology` — frozen Planck-like cosmology parameters.
* :func:`FLRWCosmology.from_camb_reference` — load the bundled CAMB
  reference at ``data/camb_ref_planck2018.npz``.
* :func:`build_sw_plateau_transfer_fn` — returns a k-callable that
  produces :class:`BianchiTransferFunctions` under the SW plateau.
* :func:`compute_flrw_dls_sw_plateau` — full end-to-end: assembles
  C_ℓ via :func:`assemble_cl_TT_isotropic` et al., converts to D_ℓ.

The SW plateau exactly reproduces the scale-invariant closed form
``D_ℓ_SW = A_s · T_CMB² / 25`` when ``n_s = 1`` — verified in tests.
"""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
from scipy.special import spherical_jn

from bass.los.bianchi_propagator import BianchiTransferFunctions
from bass.spectrum.cl_assembly import (
    CLAssemblyConfig,
    assemble_cl_EE_isotropic,
    assemble_cl_TE_isotropic,
    assemble_cl_TT_isotropic,
    compute_dl,
)


__all__ = (
    "FLRWCosmology",
    "SW_AMPLITUDE_FACTOR",
    "build_sw_plateau_transfer_fn",
    "compute_flrw_dls_sw_plateau",
    "sw_plateau_scale_invariant_dl",
    "DEFAULT_CAMB_REFERENCE_PATH",
)


DEFAULT_CAMB_REFERENCE_PATH: Path = (
    Path(__file__).resolve().parents[3] / "data" / "camb_ref_planck2018.npz"
)


# Sachs–Wolfe amplitude factor: (Θ_0 + Ψ)_* = -R / 5 in the MD limit
# with Ψ_k = -(3/5) R_k. The sign is irrelevant for the TT autocorrelation
# (it cancels in |Δ|²), but it matters for TE cross-correlation — there
# we use the same sign convention as Ma-Bertschinger 1995.
SW_AMPLITUDE_FACTOR: float = -1.0 / 5.0


@dataclass(frozen=True)
class FLRWCosmology:
    """Planck-like FLRW cosmology parameters.

    Field convention: ``eta_0_mpc`` is the conformal time today
    (= comoving horizon today ≈ 14153 Mpc). ``comoving_distance_to_ls_mpc``
    is ``Δη_* = η_0 - η(z_*) ≈ 13873 Mpc`` — the comoving distance to
    the last-scattering surface, which is what enters the Sachs-Wolfe
    kernel ``j_ℓ(k Δη_*)``.

    The bundled CAMB reference ``data/camb_ref_planck2018.npz`` uses
    ``eta_star`` as its field name, but the stored value is
    ``Δη_*``, not ``η(z_*)``. :func:`from_camb_reference` re-labels
    the field correctly so downstream callers don't inherit the
    ambiguity.
    """

    H0: float
    ombh2: float
    omch2: float
    tau: float
    As: float
    ns: float
    k_pivot_mpc: float
    comoving_distance_to_ls_mpc: float
    eta_0_mpc: float
    z_star: float
    T_CMB_K: float

    @classmethod
    def from_camb_reference(
        cls,
        path: Path | str | None = None,
        *,
        T_CMB_K: float = 2.7255,
        k_pivot_mpc: float = 0.05,
    ) -> "FLRWCosmology":
        """Load cosmology parameters from a CAMB reference ``.npz``.

        Parameters not stored in the fixture (T_CMB_K, k_pivot) default
        to Fixsen 2009 / Planck-convention values. The fixture's
        ``eta_star`` field is re-labeled to
        ``comoving_distance_to_ls_mpc`` to match its actual physical
        content (see class docstring).
        """
        fixture_path = Path(path) if path is not None else DEFAULT_CAMB_REFERENCE_PATH
        if not fixture_path.is_file():
            raise FileNotFoundError(f"CAMB reference not found: {fixture_path}")
        data = np.load(fixture_path)
        return cls(
            H0=float(data["H0"]),
            ombh2=float(data["ombh2"]),
            omch2=float(data["omch2"]),
            tau=float(data["tau"]),
            As=float(data["As"]),
            ns=float(data["ns"]),
            k_pivot_mpc=k_pivot_mpc,
            comoving_distance_to_ls_mpc=float(data["eta_star"]),
            eta_0_mpc=float(data["eta_0"]),
            z_star=float(data["z_star"]),
            T_CMB_K=T_CMB_K,
        )

    @property
    def delta_eta_star_mpc(self) -> float:
        """Alias for ``comoving_distance_to_ls_mpc``. This is the quantity
        that enters the SW Bessel kernel ``j_ℓ(k Δη_*)``."""
        return self.comoving_distance_to_ls_mpc


def build_sw_plateau_transfer_fn(
    cosmology: FLRWCosmology,
    *,
    ell_max: int,
) -> Callable[[float], BianchiTransferFunctions]:
    """Construct a k-callable producing :class:`BianchiTransferFunctions`
    under the Sachs-Wolfe plateau approximation.

    * ``Δ_ℓ^T(k) = A_sw · j_ℓ(k · Δη_*)`` for all ℓ.
    * ``Δ_ℓ^E(k) = 0`` for all ℓ (tight-coupling suppression).
    * m=±2 slots are zero (FLRW has no transverse-traceless tensor modes
      under this scalar-only approximation).
    """
    if ell_max < 0:
        raise ValueError(f"ell_max must be ≥ 0, got {ell_max}")
    delta_eta = cosmology.delta_eta_star_mpc
    if delta_eta <= 0.0:
        raise ValueError(
            f"Δη_* must be > 0; got eta_0={cosmology.eta_0_mpc}, "
            f"comoving_distance_to_ls={cosmology.comoving_distance_to_ls_mpc}"
        )
    ell_grid = np.arange(ell_max + 1, dtype=int)

    def _transfer(k: float) -> BianchiTransferFunctions:
        kr = k * delta_eta
        dT = SW_AMPLITUDE_FACTOR * spherical_jn(ell_grid, kr)
        zero = np.zeros(ell_max + 1, dtype=float)
        return BianchiTransferFunctions(
            delta_T_m0=np.asarray(dT, dtype=float),
            delta_T_m_plus2=zero,
            delta_T_m_minus2=zero,
            delta_E_m0=zero,
            delta_E_m_plus2=zero,
            delta_E_m_minus2=zero,
            delta_B_all_zero=zero,
        )

    return _transfer


def compute_flrw_dls_sw_plateau(
    cosmology: FLRWCosmology,
    *,
    ell_max: int = 30,
    k_grid: np.ndarray | None = None,
    quadrature: str = "simpson",
) -> dict[str, np.ndarray]:
    """End-to-end FLRW SW-plateau D_ℓ pipeline.

    Steps:

    1. Build a SW-plateau transfer ``k → BianchiTransferFunctions``.
    2. Construct :class:`CLAssemblyConfig` with the cosmology's
       ``A_s``, ``n_s``, ``T_CMB`` and ``k_pivot``.
    3. Call :func:`assemble_cl_TT_isotropic` (and EE/TE for completeness).
    4. Convert C_ℓ → D_ℓ via :func:`compute_dl`.

    Parameters
    ----------
    k_grid : np.ndarray | None
        If None, a 513-point log-grid over ``k ∈ [1e-5, 1.0]`` Mpc⁻¹ is
        used (odd length for Simpson). The grid spans well past the
        first acoustic peak so the SW plateau integral converges.
    quadrature : {'trapezoid', 'simpson'}
        Forwarded to :class:`CLAssemblyConfig`. Simpson requires odd
        ``k_grid`` length.

    Returns
    -------
    dict with keys ``ell``, ``D_TT``, ``D_EE``, ``D_TE``, ``C_TT``,
    ``C_EE``, ``C_TE``, plus ``metadata`` (cosmology + sw_amplitude).
    """
    if k_grid is None:
        k_grid = np.logspace(-5.0, 0.0, 513)
    if quadrature == "simpson" and k_grid.size % 2 == 0:
        raise ValueError(
            f"Simpson quadrature requires odd k_grid length, got {k_grid.size}"
        )

    cfg = CLAssemblyConfig(
        ell_max=ell_max,
        k_grid=k_grid,
        A_s=cosmology.As,
        n_s=cosmology.ns,
        k_pivot_mpc=cosmology.k_pivot_mpc,
        T_CMB_K=cosmology.T_CMB_K,
        quadrature=quadrature,
    )
    transfer_fn = build_sw_plateau_transfer_fn(cosmology, ell_max=ell_max)

    c_tt = assemble_cl_TT_isotropic(transfer_fn, cfg)
    c_ee = assemble_cl_EE_isotropic(transfer_fn, cfg)
    c_te = assemble_cl_TE_isotropic(transfer_fn, cfg)

    d_tt = compute_dl(c_tt, T_CMB_K=cosmology.T_CMB_K)
    d_ee = compute_dl(c_ee, T_CMB_K=cosmology.T_CMB_K)
    d_te = compute_dl(c_te, T_CMB_K=cosmology.T_CMB_K)

    ell = np.arange(ell_max + 1, dtype=int)
    metadata: dict[str, Any] = {
        "cosmology": {
            "H0": cosmology.H0,
            "ombh2": cosmology.ombh2,
            "omch2": cosmology.omch2,
            "tau": cosmology.tau,
            "As": cosmology.As,
            "ns": cosmology.ns,
            "k_pivot_mpc": cosmology.k_pivot_mpc,
            "comoving_distance_to_ls_mpc": cosmology.comoving_distance_to_ls_mpc,
            "eta_0_mpc": cosmology.eta_0_mpc,
            "z_star": cosmology.z_star,
            "T_CMB_K": cosmology.T_CMB_K,
        },
        "approximation": "sachs_wolfe_plateau",
        "sw_amplitude_factor": SW_AMPLITUDE_FACTOR,
        "notes": (
            "Sachs-Wolfe plateau only: omits ISW, Doppler, tight-coupling "
            "acoustic amplification, and reionization. Low-ell baseline for "
            "the S9 CAMB comparison; a full Tier-B bridge is the follow-up "
            "path to close the residual gap against CAMB at tau > 0."
        ),
        "k_grid_points": int(k_grid.size),
        "k_grid_range_mpc": (float(k_grid.min()), float(k_grid.max())),
        "quadrature": quadrature,
    }
    return {
        "ell": ell,
        "D_TT": d_tt,
        "D_EE": d_ee,
        "D_TE": d_te,
        "C_TT": c_tt,
        "C_EE": c_ee,
        "C_TE": c_te,
        "metadata": metadata,
    }


def sw_plateau_scale_invariant_dl(
    *,
    A_s: float,
    T_CMB_K: float,
    sw_amplitude_factor: float = SW_AMPLITUDE_FACTOR,
) -> float:
    """Closed-form scale-invariant SW plateau D_ℓ in μK².

    Under ``n_s = 1`` the SW plateau integral collapses to the exact
    expression

        D_ℓ_SW = |A_sw|² · A_s · T_CMB² · 4π · ∫dlnk j_ℓ²(kΔη) · ℓ(ℓ+1)/(2π)
               = |A_sw|² · A_s · T_CMB²

    after applying the Bessel identity
    ``∫_0^∞ j_ℓ²(x) d(ln x) = 1/[2 ℓ(ℓ+1)]`` (for ℓ ≥ 1). The closed
    form is ell-independent on the plateau, confirming the textbook
    result ``D_ℓ_SW = A_s (T_CMB)² / 25`` for ``A_sw = -1/5``.
    """
    T_CMB_microK = T_CMB_K * 1.0e6
    return float(sw_amplitude_factor ** 2 * A_s * T_CMB_microK ** 2)
