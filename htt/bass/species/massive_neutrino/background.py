"""Massive-neutrino background thermodynamics for the FB-9 species slot.

The load-bearing invariant remains ``Sigma_mnu = 0 -> byte-identical to
the LB-1 massless NeutrinoBackground``: the registry keeps the default
zero-mass path on the existing LB-1 class, while this implementation
serves the positive-mass branch.

The background density and pressure are evaluated from the standard
Fermi-Dirac phase-space integrals

    rho(a) = Omega_ncdm,0 / a^4 * I_rho(y) / I_rho(0)
    p(a)   = Omega_ncdm,0 / a^4 * I_p(y)   / I_rho(0)

with

    y = m a / T_ncdm,0,
    I_rho(y) = ∫ dq q² sqrt(q² + y²) f_FD(q),
    I_p(y)   = (1/3) ∫ dq q^4 / sqrt(q² + y²) f_FD(q).

FB-9 uses the degenerate-mass approximation: the registry passes
``mass_eV = Sigma_mnu / 3``. For ``mass_eV > 0`` the branch follows the
standard CLASS/CAMB split of ``N_eff = 3.044`` into three degenerate
massive eigenstates with ``N_eff ~= 3 x 1.0132`` plus the tiny
massless remainder ``N_ur ~= 0.00441``. That implies a slightly hotter
``T_ncdm`` and a corresponding ``Omega_ncdm,0`` rescaling on the
positive-mass path, while ``mass_eV = 0`` remains analytically pinned to
the exact LB-1 massless formulas.
"""
from __future__ import annotations

from typing import Union

import numpy as np
from scipy.interpolate import CubicSpline

from bass.species.background_table import FLRWBackgroundTable
from bass.species.base import (
    SpeciesBackground,
    SpeciesLabel,
    _as_1d,
    _squeeze_if_scalar,
)
from bass.species.massive_neutrino.phase_space import (
    MASSLESS_FD_ENERGY_INTEGRAL,
    phase_space_grid,
)


_Number = Union[float, np.ndarray]
_K_B_EV_PER_K: float = 8.617333262145e-5
_SQRT_THREE_OVER_TWO: float = float(np.sqrt(3.0 / 2.0))
_MEAN_FD_MOMENTUM: float = 3.151
_DEGENERATE_MASSIVE_SPECIES: float = 3.0
_NEFF_PER_MASSIVE_EIGENSTATE: float = 1.0132
_NCDM_NEFF_TOTAL: float = (
    _DEGENERATE_MASSIVE_SPECIES * _NEFF_PER_MASSIVE_EIGENSTATE
)
_T_NCDM_OVER_T_NU: float = _NEFF_PER_MASSIVE_EIGENSTATE ** 0.25


class MassiveNeutrinoBackground(SpeciesBackground):
    """Massive-neutrino ``SpeciesBackground`` with FD phase-space support.

    The invariant remains ``Sigma_mnu = 0 -> byte-identical to the
    LB-1 massless NeutrinoBackground`` because the registry must keep the
    zero-mass production path on the existing LB-1 class. Inside this
    class, however, the exact ``mass_eV == 0`` limit is still handled
    analytically so any explicit opt-in to a massless massive-ν object
    remains bit-identical to the LB-1 closed form.
    """

    label = SpeciesLabel.NEUTRINO

    def __init__(
        self,
        bg_table: FLRWBackgroundTable,
        mass_eV: float,
        N_q: int = 15,
    ) -> None:
        if mass_eV < 0.0:
            raise ValueError(f"mass_eV must be non-negative, got {mass_eV}")
        if N_q <= 0:
            raise ValueError(f"N_q must be positive, got {N_q}")
        self._bg = bg_table
        self.mass_eV = float(mass_eV)
        self.N_q = int(N_q)
        self._Omega_nu_0 = float(bg_table.constants.Omega_nu_0)
        self._T_nu_0 = (
            bg_table.constants.T_nu_over_T_gamma
            * bg_table.constants.T_gamma_0_K
        )
        self._Omega_ncdm_0 = (
            self._Omega_nu_0 * (_NCDM_NEFF_TOTAL / bg_table.constants.N_eff)
        )
        self._T_ncdm_0 = self._T_nu_0 * _T_NCDM_OVER_T_NU
        self._T_ncdm_0_eV = self._T_ncdm_0 * _K_B_EV_PER_K
        self._massless_energy_integral = float(MASSLESS_FD_ENERGY_INTEGRAL)
        self._q_grid, self._weights = phase_space_grid(self.mass_eV, self.N_q)
        self._log_a_grid = np.log(np.asarray(bg_table.a, dtype=np.float64))

        # FB-9.6 doc contract: cache the thermodynamic transition surface
        # on the shared FLRW a-grid and interpolate on log(a).
        rho_grid, p_grid, v_grid = self._thermo_on_a_grid(bg_table.a)
        self._log_rho_spline = CubicSpline(
            self._log_a_grid, np.log(rho_grid), bc_type="natural",
        )
        self._log_p_spline = CubicSpline(
            self._log_a_grid, np.log(p_grid), bc_type="natural",
        )
        self._v_spline = CubicSpline(
            self._log_a_grid, v_grid, bc_type="natural",
        )

    def _a_of_eta(self, eta: _Number) -> _Number:
        return self._bg.interp_a(eta)

    def _thermo_on_a_grid(
        self, a: np.ndarray,
    ) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        a_arr = np.asarray(a, dtype=np.float64)
        if self.mass_eV == 0.0:
            rho = self._Omega_nu_0 / a_arr ** 4
            p = rho / 3.0
            v = np.ones_like(a_arr)
            return rho, p, v

        y = (self.mass_eV / self._T_ncdm_0_eV) * a_arr
        eps = np.sqrt(self._q_grid[None, :] ** 2 + y[:, None] ** 2)
        rho_integral = np.einsum("q,aq->a", self._weights, eps)
        p_integral = (1.0 / 3.0) * np.einsum(
            "q,aq->a", self._weights * self._q_grid ** 2, 1.0 / eps,
        )
        rho = (
            self._Omega_ncdm_0
            * rho_integral
            / (self._massless_energy_integral * a_arr ** 4)
        )
        p = (
            self._Omega_ncdm_0
            * p_integral
            / (self._massless_energy_integral * a_arr ** 4)
        )
        # MB-95 free-streaming terms scale with q / epsilon. Averaging
        # that factor over the energy-density weight yields an effective
        # velocity that is 1 in the relativistic limit and ~1/a in the
        # NR regime.
        v = self._massless_energy_integral / rho_integral
        return rho, p, v

    def _interp_log_a(
        self, eta: _Number, spline: CubicSpline, *, positive: bool,
    ) -> _Number:
        arr_eta, scalar = _as_1d(eta)
        a = np.asarray(self._bg.interp_a(arr_eta), dtype=np.float64)
        log_a = np.log(a)
        out = spline(log_a)
        if positive:
            out = np.exp(out)
        return _squeeze_if_scalar(np.asarray(out, dtype=np.float64), scalar)

    def nr_transition_scale_factor(self) -> float:
        """Return the nominal non-relativistic transition scale factor.

        Uses the mean thermal momentum criterion

            <q> T_nu(a_NR) ~= m   with   <q> ~= 3.151 ,

        which places ``w(a_NR)`` close to the canonical transition
        midpoint ``1/6``. ``mass_eV = 0`` returns ``np.inf``.
        """
        if self.mass_eV == 0.0:
            return float(np.inf)
        return float(_MEAN_FD_MOMENTUM * self._T_ncdm_0_eV / self.mass_eV)

    def rho_rest(self, eta: _Number) -> _Number:
        """Rest-frame energy density ``rho_nu(eta)`` in ``rho_crit,0`` units."""
        if self.mass_eV == 0.0:
            a = np.asarray(self._bg.interp_a(eta), dtype=np.float64)
            return self._Omega_nu_0 / a ** 4
        return self._interp_log_a(eta, self._log_rho_spline, positive=True)

    def p_rest(self, eta: _Number) -> _Number:
        """Rest-frame isotropic pressure ``p_nu(eta)`` in ``rho_crit,0`` units."""
        if self.mass_eV == 0.0:
            return np.asarray(self.rho_rest(eta), dtype=np.float64) / 3.0
        return self._interp_log_a(eta, self._log_p_spline, positive=True)

    def dot_rho(self, eta: _Number) -> _Number:
        """Proper-time density derivative from collisionless continuity."""
        arr_eta, scalar = _as_1d(eta)
        theta = np.asarray(self._bg.interp_Theta(arr_eta), dtype=np.float64)
        rho = np.asarray(self.rho_rest(arr_eta), dtype=np.float64)
        if self.mass_eV == 0.0:
            out = -(4.0 / 3.0) * theta * rho
        else:
            p = np.asarray(self.p_rest(arr_eta), dtype=np.float64)
            out = -theta * (rho + p)
        return _squeeze_if_scalar(out, scalar)

    def temperature(self, eta: _Number) -> _Number:
        """Return ``T_nu(eta) = T_nu,0 / a(eta)`` in Kelvin."""
        a = np.asarray(self._bg.interp_a(eta), dtype=np.float64)
        if self.mass_eV == 0.0:
            return self._T_nu_0 / a
        return self._T_ncdm_0 / a

    def free_streaming_velocity(self, eta: _Number) -> _Number:
        """Effective velocity-weight factor for MB-95 free streaming.

        This is the energy-weighted average of ``q / epsilon(q, a)``.
        It equals 1 in the relativistic limit and decays as ``1/a`` once
        the species becomes non-relativistic.
        """
        if self.mass_eV == 0.0:
            arr_eta, scalar = _as_1d(eta)
            out = np.ones_like(arr_eta)
            return _squeeze_if_scalar(out, scalar)
        arr_eta, scalar = _as_1d(eta)
        out = np.asarray(
            self._interp_log_a(arr_eta, self._v_spline, positive=False),
            dtype=np.float64,
        )
        out = np.maximum(out, 0.0)
        return _squeeze_if_scalar(out, scalar)

    def free_streaming_modifier(self, eta: _Number) -> _Number:
        """Alias used by the hierarchy wrapper for the MB-95 ``q/epsilon`` factor."""
        return self.free_streaming_velocity(eta)

    def free_streaming_wavenumber(self, eta: _Number) -> _Number:
        """Comoving free-streaming wavenumber ``k_fs(eta)`` in ``Mpc^-1``.

        Uses the standard Jeans-like estimate

            k_fs = sqrt(3/2) * calH / v_fs

        with ``v_fs`` supplied by :meth:`free_streaming_velocity`.
        """
        arr_eta, scalar = _as_1d(eta)
        calH = np.asarray(self._bg.interp_calH(arr_eta), dtype=np.float64)
        v_fs = np.asarray(self.free_streaming_velocity(arr_eta), dtype=np.float64)
        out = _SQRT_THREE_OVER_TWO * calH / v_fs
        return _squeeze_if_scalar(out, scalar)
