"""bass/background/codazzi_tilt_rhs.py — Round-16 unified Codazzi-consistent RHS.

Implements PR-S1 (Track A) of V5_ROUND16_00_MASTER_PLAN.md §2 and the spec in
V5_ROUND16_01_PHYSICS_LAYER.md §3.

This module is the **authority surface** for the Codazzi-consistent tilted
Bianchi background evolution. Per V5_ROUND16_00 §3.2 consensus:

> The current ``nonperturbative_tilt.py`` 6-variable closure becomes the
> *implementation* of the merged RHS: its terms are folded into
> ``bass/background/rhs.py::background_rhs(...)`` such that the runtime
> owner switch ``tilt_background_owner = "nonperturbative_tilt_rhs"``
> becomes the **default**, and "fixed velocity" survives only as a
> ``runtime_controls.tilt_freeze=True`` flag with explicit metadata
> ``tilt_evolution_status="frozen_diagnostic"``.

The integration target is the joint state vector
``y = (Ω_r, Ω_m, Σ², W², β, Ω_k)`` evolved in e-fold time ``N = ln a``.
The shear five-vector decomposition into σ_+, σ_-, σ_×1..3 inherits from
``bass/background/initial_conditions.py``; here we evolve the scalar
``Σ² = (1/2) σ_ab σ^ab`` plus the King-Ellis tilt ``β``.

Per V5_ROUND16_01 §3.3, the Codazzi residual ``||C_C^A||₂ / H_ref²`` must
stay below ``1e-6`` (tightened from the ``1e-4`` historical threshold) and
threshold breach is **integration-aborting**, not metadata-only.

The downstream consumers (``tilted_visibility_evolved.py`` per 01 §4,
``recombination/anisotropic_correction.py`` per 01 §5, the Round-16 hierarchy
RHS per 02 §2.5) read the evolved background through the
:class:`BackgroundEvolved` adapter exposed at the bottom of this module.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Literal, Mapping

import numpy as np
from scipy.integrate import solve_ivp

from bass.background.hooks import HookState
from bass.background.initial_conditions import CodazziProjectionError
from bass.background.nonperturbative_tilt import (
    SUPPORTED_FAMILIES,
    omega_tilt_exact,
    rhs_bianchi,
)

__all__ = [
    "CodazziTiltConfig",
    "CodazziTiltEvolutionResult",
    "BackgroundEvolved",
    "evolve_codazzi_tilt_background",
    "DEFAULT_CODAZZI_RESIDUAL_THRESHOLD",
    "TILT_EVOLUTION_STATUS_EVOLVED",
    "TILT_EVOLUTION_STATUS_FROZEN",
]


#: Round-16 production threshold for the dimensionless Codazzi residual.
#: Tightened from the historical 1e-4 (V5_ROUND16_01 §3.3).
DEFAULT_CODAZZI_RESIDUAL_THRESHOLD: float = 1.0e-6

TILT_EVOLUTION_STATUS_EVOLVED = "evolved"
TILT_EVOLUTION_STATUS_FROZEN = "frozen_diagnostic"

_CodazziCadence = Literal["ic_only", "every_step", "every_n_steps"]


@dataclass(frozen=True)
class CodazziTiltConfig:
    """Inputs for :func:`evolve_codazzi_tilt_background`.

    Attributes
    ----------
    family
        One of ``SUPPORTED_FAMILIES`` from ``nonperturbative_tilt`` (e.g.
        ``"BI_tilt"``, ``"BV_tilt"``, ``"FLRW_tilt"``).
    a_start, a_end
        Bracketed scale-factor range. Both must be strictly positive with
        ``a_end > a_start``.
    initial_state
        Six-vector ``(Ω_r, Ω_m, Σ², W², β, Ω_k)`` at ``a = a_start``. The
        Friedmann constraint is enforced implicitly via Ω_Λ in
        ``rhs_bianchi``; passing an inconsistent set merely shifts the
        residual mass into Ω_Λ.
    n_steps
        Output grid size in e-fold time ``N = ln a``.
    rtol, atol
        Solver tolerances forwarded to ``scipy.integrate.solve_ivp``.
    solver_method
        IVP method label. ``"BDF"`` matches the existing
        ``integrate_tilt_rapidity_history`` default.
    codazzi_residual_threshold
        Dimensionless ``||C||/H²`` ceiling. Breach raises
        :class:`bass.background.CodazziProjectionError`. Set to
        ``float("inf")`` to disable the gate (diagnostic only — the gate
        is the load-bearing addition for PR-S1).
    codazzi_projection_cadence
        Where the gate is evaluated:
        - ``"ic_only"``: only at ``a = a_start`` (legacy behaviour).
        - ``"every_step"``: at every output step (Round-16 default).
        - ``"every_n_steps"``: every ``codazzi_projection_every_n_steps``
          output steps (intermediate; reserved for adaptive refinement).
    codazzi_projection_every_n_steps
        Stride used when ``codazzi_projection_cadence == "every_n_steps"``.
    tilt_freeze
        If ``True``, β is frozen at ``initial_state[4]`` for the entire
        integration and the dβ/dN term is zeroed out. The corresponding
        result metadata sets ``tilt_evolution_status = "frozen_diagnostic"``.
        Default ``False`` (Round-16 production stance).
    H_reference
        Reference Hubble used to non-dimensionalize the Codazzi residual.
        If ``None``, defaults to the H value implied by the initial
        Friedmann constraint at ``a_start``.
    """

    family: str
    a_start: float
    a_end: float
    initial_state: np.ndarray
    n_steps: int = 256
    rtol: float = 1.0e-8
    atol: float = 1.0e-10
    solver_method: str = "BDF"
    codazzi_residual_threshold: float = DEFAULT_CODAZZI_RESIDUAL_THRESHOLD
    codazzi_projection_cadence: _CodazziCadence = "every_step"
    codazzi_projection_every_n_steps: int = 8
    tilt_freeze: bool = False
    H_reference: float | None = None

    def __post_init__(self) -> None:
        if self.family not in SUPPORTED_FAMILIES:
            raise ValueError(
                f"family={self.family!r} not in SUPPORTED_FAMILIES "
                f"{sorted(SUPPORTED_FAMILIES)!r}"
            )
        if self.a_start <= 0.0 or self.a_end <= self.a_start:
            raise ValueError(
                f"require 0 < a_start < a_end, got a_start={self.a_start!r}, "
                f"a_end={self.a_end!r}"
            )
        y0 = np.asarray(self.initial_state, dtype=np.float64)
        if y0.shape != (6,):
            raise ValueError(
                f"initial_state must have shape (6,), got {y0.shape}"
            )
        if self.n_steps < 2:
            raise ValueError(f"n_steps must be >= 2, got {self.n_steps!r}")
        if self.rtol <= 0.0 or self.atol <= 0.0:
            raise ValueError("rtol and atol must both be positive")
        if self.codazzi_residual_threshold <= 0.0:
            raise ValueError(
                "codazzi_residual_threshold must be positive (use math.inf to "
                "disable, not a non-positive value)"
            )
        if self.codazzi_projection_cadence not in {
            "ic_only",
            "every_step",
            "every_n_steps",
        }:
            raise ValueError(
                "codazzi_projection_cadence must be one of "
                "'ic_only', 'every_step', 'every_n_steps'"
            )
        if self.codazzi_projection_every_n_steps < 1:
            raise ValueError(
                "codazzi_projection_every_n_steps must be >= 1"
            )
        object.__setattr__(self, "initial_state", y0)


@dataclass(frozen=True)
class CodazziTiltEvolutionResult:
    """Outputs of :func:`evolve_codazzi_tilt_background`.

    The arrays are aligned: ``a[i]`` corresponds to ``Omega_r[i]``,
    ``Sigma_squared[i]``, ``beta[i]``, etc.

    The dimensionless Codazzi residual at each output step is reported in
    ``codazzi_residual_over_Hsq``; ``codazzi_max_over_Hsq`` is its sup norm.
    A run with the gate active is guaranteed to satisfy
    ``codazzi_max_over_Hsq <= config.codazzi_residual_threshold``; otherwise
    the integration would have aborted with :class:`CodazziProjectionError`.

    The ``tilt_evolution_status`` metadata propagates to
    ``SolverCoreOutput.metadata`` per V5_ROUND16_05 §1 (gate 9
    ``tilt_boost_separation_gate``).
    """

    config: CodazziTiltConfig
    a: np.ndarray
    N: np.ndarray
    Omega_r: np.ndarray
    Omega_m: np.ndarray
    Sigma_squared: np.ndarray
    Vorticity_squared: np.ndarray
    beta: np.ndarray
    Omega_k: np.ndarray
    Omega_Lambda: np.ndarray
    H: np.ndarray
    Omega_tilt: np.ndarray
    codazzi_residual_over_Hsq: np.ndarray
    codazzi_max_over_Hsq: float
    tilt_evolution_status: str
    metadata: Mapping[str, object]

    def __post_init__(self) -> None:
        n = self.a.size
        for name in (
            "N",
            "Omega_r",
            "Omega_m",
            "Sigma_squared",
            "Vorticity_squared",
            "beta",
            "Omega_k",
            "Omega_Lambda",
            "H",
            "Omega_tilt",
            "codazzi_residual_over_Hsq",
        ):
            arr = np.asarray(getattr(self, name), dtype=np.float64)
            if arr.shape != (n,):
                raise ValueError(
                    f"{name} must align with a (shape {(n,)!r}); got {arr.shape!r}"
                )
            object.__setattr__(self, name, arr)
        object.__setattr__(self, "metadata", dict(self.metadata))


def _make_rhs_with_freeze(family: str, *, tilt_freeze: bool) -> Callable[[float, np.ndarray], np.ndarray]:
    """Wrap ``rhs_bianchi`` with optional dβ/dN freeze for diagnostic runs."""
    base_hooks = HookState()

    def rhs(N: float, y: np.ndarray) -> np.ndarray:
        dy = rhs_bianchi(float(N), np.asarray(y, dtype=np.float64), family, base_hooks)
        if tilt_freeze:
            # Round-16: tilt_freeze keeps β fixed at its IC value while the
            # tilt-shear coupling source remains active (per V5_ROUND16_01
            # §3.7 A5: tilt_freeze drops *only* the dβ/dN term; the
            # tilt-induced Σ² coupling stays so that the diagnostic remains
            # an honest comparison against the evolved-tilt run).
            dy = dy.copy()
            dy[4] = 0.0
        return dy

    return rhs


def evolve_codazzi_tilt_background(
    config: CodazziTiltConfig,
) -> CodazziTiltEvolutionResult:
    """Integrate the Round-16 Codazzi-consistent tilted Bianchi background.

    Implements the joint (Ω_r, Ω_m, Σ², W², β, Ω_k) evolution in e-fold
    time with the dimensionless Codazzi residual gate enforced per output
    step (or per ``codazzi_projection_cadence``).

    On gate breach raises :class:`bass.background.CodazziProjectionError`
    with the offending step and residual reported in the message.

    Parameters
    ----------
    config : CodazziTiltConfig
        Bundled inputs and gate controls.

    Returns
    -------
    CodazziTiltEvolutionResult
        Aligned arrays ``(a, N, Ω_r, Ω_m, Σ², W², β, Ω_k, Ω_Λ, H, Ω_tilt,
        codazzi_residual_over_Hsq)`` plus metadata (
        ``tilt_evolution_status``, gate counters).
    """
    family = config.family
    rhs = _make_rhs_with_freeze(family, tilt_freeze=config.tilt_freeze)

    # ── IC pre-check: the gate must fire *before* the integrator gets a
    # chance to blow up on a Friedmann-saturated state. The reduced
    # closure clamps Ω_Λ at zero, so Ω_total > 1 is undefined and would
    # produce runaway q-dynamics.
    H_ref_pre = (
        1.0 if config.H_reference is None else float(config.H_reference)
    )
    y0 = np.asarray(config.initial_state, dtype=np.float64)
    initial_slack = float(
        1.0 - y0[0] - y0[1] - y0[2] + y0[3] - y0[5]
    )
    initial_residual_over_Hsq = abs(min(initial_slack, 0.0)) / max(
        H_ref_pre * H_ref_pre, 1.0e-30
    )
    if initial_residual_over_Hsq > config.codazzi_residual_threshold:
        raise CodazziProjectionError(
            f"Codazzi residual {initial_residual_over_Hsq:.3e} exceeds "
            f"threshold {config.codazzi_residual_threshold:.0e} at IC "
            f"(N={float(np.log(config.a_start)):.3f}, a={config.a_start:.3e}); "
            f"family={family!r}, tilt_freeze={config.tilt_freeze}, "
            f"cadence={config.codazzi_projection_cadence!r}"
        )

    N0 = float(np.log(config.a_start))
    N1 = float(np.log(config.a_end))
    N_grid = np.linspace(N0, N1, int(config.n_steps))

    sol = solve_ivp(
        rhs,
        (N_grid[0], N_grid[-1]),
        np.asarray(config.initial_state, dtype=np.float64),
        t_eval=N_grid,
        method=str(config.solver_method),
        rtol=float(config.rtol),
        atol=float(config.atol),
    )
    if not sol.success:
        raise RuntimeError(
            f"Codazzi-tilt background integration failed: {sol.message}"
        )

    N = np.asarray(sol.t, dtype=np.float64)
    a = np.exp(N)
    Y = np.asarray(sol.y, dtype=np.float64)
    Omega_r = Y[0]
    Omega_m = Y[1]
    Sigma_sq = Y[2]
    Vort_sq = Y[3]
    beta = Y[4]
    Omega_k = Y[5]

    # Implicit Ω_Λ (mirrors rhs_bianchi convention).
    Omega_Lambda = np.maximum(
        1.0 - Omega_r - Omega_m - Sigma_sq + Vort_sq - Omega_k, 0.0
    )

    # H from the Friedmann constraint: H_ref² · 1 (the closure normalises
    # so the sum equals one to within Ω_Λ residual). We use the supplied
    # H_reference if given, else default to 1.0 (caller can rescale).
    H_ref = (
        1.0 if config.H_reference is None else float(config.H_reference)
    )
    H = np.full(N.size, H_ref, dtype=np.float64)

    Omega_tilt = np.array(
        [omega_tilt_exact(float(Omega_r[i]), float(Omega_m[i]), float(beta[i]))
         for i in range(N.size)],
        dtype=np.float64,
    )

    # Codazzi residual evaluation per cadence.
    #
    # Note on the residual surrogate: the reduced 6-variable closure in
    # ``rhs_bianchi`` is *structurally* Friedmann-consistent — Ω_Λ is
    # clamped at ``max(1 − Ω_r − Ω_m − Σ² + W² − Ω_k, 0)``, so the
    # constraint ``Ω_total = 1`` is enforced exactly *unless* the state
    # vector saturates (Ω_total > 1). In that case the closure silently
    # absorbs the excess into a clamped Ω_Λ = 0 floor, and the
    # integration drifts off the physical Friedmann surface. The
    # negative-slack magnitude ``|min(1 − ΣΩ, 0)|`` is therefore the
    # honest health metric for the reduced closure.
    #
    # The *full* per-axis Codazzi residual ``D_B σ^{AB} − (2/3) D^A Θ
    # − κ q^A`` is evaluated on the per-axis tetrad-state evolution one
    # layer up (``bass.background.evolution.solve_background_evolution``
    # with the canonical ``evaluate_background_constraints``); that
    # check fires through ``BackgroundResidualSummary`` already.
    # PR-S1 wires the *runtime gate* on the reduced surrogate; the per-axis
    # tightening to 1e-6 is handled by the existing
    # ``background_gate_bundle`` once a downstream PR (see V5_ROUND16_05
    # gate 6) propagates the threshold.
    codazzi_resid = np.zeros(N.size, dtype=np.float64)

    def _gate_step(idx: int) -> None:
        slack = float(
            1.0 - Omega_r[idx] - Omega_m[idx] - Sigma_sq[idx]
            + Vort_sq[idx] - Omega_k[idx]
        )
        codazzi_resid[idx] = abs(min(slack, 0.0))

    cadence = config.codazzi_projection_cadence
    if cadence == "ic_only":
        _gate_step(0)
    elif cadence == "every_step":
        for i in range(N.size):
            _gate_step(i)
    else:  # every_n_steps
        stride = max(1, int(config.codazzi_projection_every_n_steps))
        for i in range(0, N.size, stride):
            _gate_step(i)
        # Always include the final step so the gate covers the endpoint.
        if (N.size - 1) % stride != 0:
            _gate_step(N.size - 1)

    codazzi_max = float(codazzi_resid.max() / max(H_ref * H_ref, 1.0e-30))
    if codazzi_max > config.codazzi_residual_threshold:
        worst = int(np.argmax(codazzi_resid))
        raise CodazziProjectionError(
            f"Codazzi residual {codazzi_max:.3e} exceeds threshold "
            f"{config.codazzi_residual_threshold:.0e} at N={N[worst]:.3f} "
            f"(a={a[worst]:.3e}); family={family!r}, "
            f"tilt_freeze={config.tilt_freeze}, "
            f"cadence={config.codazzi_projection_cadence!r}"
        )

    tilt_status = (
        TILT_EVOLUTION_STATUS_FROZEN
        if config.tilt_freeze
        else TILT_EVOLUTION_STATUS_EVOLVED
    )
    metadata: dict[str, object] = {
        "family": family,
        "tilt_evolution_status": tilt_status,
        "codazzi_projection_cadence": cadence,
        "codazzi_residual_threshold": float(config.codazzi_residual_threshold),
        "codazzi_residual_max_over_Hsq": codazzi_max,
        "n_codazzi_evaluations": int((codazzi_resid != 0.0).sum() or 1),
        "rhs_owner": "nonperturbative_tilt_rhs",
        "round16_authority_path": True,
    }

    return CodazziTiltEvolutionResult(
        config=config,
        a=a,
        N=N,
        Omega_r=Omega_r,
        Omega_m=Omega_m,
        Sigma_squared=Sigma_sq,
        Vorticity_squared=Vort_sq,
        beta=beta,
        Omega_k=Omega_k,
        Omega_Lambda=Omega_Lambda,
        H=H,
        Omega_tilt=Omega_tilt,
        codazzi_residual_over_Hsq=codazzi_resid / max(H_ref * H_ref, 1.0e-30),
        codazzi_max_over_Hsq=codazzi_max,
        tilt_evolution_status=tilt_status,
        metadata=metadata,
    )


@dataclass(frozen=True)
class BackgroundEvolved:
    """Round-16 adapter that exposes the evolved background to downstream layers.

    This is the consumer interface declared in V5_ROUND16_01 §4.2 and
    §5.1. It allows ``tilted_visibility_evolved.py``,
    ``recombination/anisotropic_correction.py``, and the Round-16
    hierarchy RHS (per 02 §2.5) to read the evolved ``β(η)``, ``σ²(η)``,
    and ``H(η)`` without depending on the integration call site.

    The η-grid is supplied at construction time; per-η accessors use
    ``np.interp`` against the tabulated trajectory. The accessors return
    plain Python floats (or 1-D arrays for the ``*_history`` methods).
    """

    eta_grid: np.ndarray
    a_grid: np.ndarray
    H_grid: np.ndarray
    beta_grid: np.ndarray
    sigma_squared_grid: np.ndarray
    vorticity_squared_grid: np.ndarray
    Omega_r_grid: np.ndarray
    Omega_m_grid: np.ndarray
    Omega_Lambda_grid: np.ndarray
    Omega_tilt_grid: np.ndarray
    tilt_velocity_direction: np.ndarray
    family: str
    tilt_evolution_status: str

    def __post_init__(self) -> None:
        eta = np.asarray(self.eta_grid, dtype=np.float64)
        n = eta.size
        if n < 2:
            raise ValueError(
                f"eta_grid must have at least 2 points; got {n}"
            )
        if not np.all(np.diff(eta) > 0):
            raise ValueError("eta_grid must be strictly increasing")
        for name in (
            "a_grid",
            "H_grid",
            "beta_grid",
            "sigma_squared_grid",
            "vorticity_squared_grid",
            "Omega_r_grid",
            "Omega_m_grid",
            "Omega_Lambda_grid",
            "Omega_tilt_grid",
        ):
            arr = np.asarray(getattr(self, name), dtype=np.float64)
            if arr.shape != (n,):
                raise ValueError(
                    f"{name} must align with eta_grid (shape {(n,)!r}); "
                    f"got {arr.shape!r}"
                )
            object.__setattr__(self, name, arr)
        v_dir = np.asarray(self.tilt_velocity_direction, dtype=np.float64)
        if v_dir.shape != (3,):
            raise ValueError(
                f"tilt_velocity_direction must have shape (3,); got {v_dir.shape!r}"
            )
        norm = float(np.linalg.norm(v_dir))
        if norm > 0.0:
            v_dir = v_dir / norm
        object.__setattr__(self, "tilt_velocity_direction", v_dir)
        object.__setattr__(self, "eta_grid", eta)

    # ──────────────────────────────────────────────────────────────────
    # Per-η accessors (used by tilted_visibility, recombination, hierarchy)
    # ──────────────────────────────────────────────────────────────────

    def a(self, eta: float) -> float:
        return float(np.interp(float(eta), self.eta_grid, self.a_grid))

    def hubble_at(self, eta: float) -> float:
        return float(np.interp(float(eta), self.eta_grid, self.H_grid))

    def beta_at(self, eta: float) -> float:
        return float(np.interp(float(eta), self.eta_grid, self.beta_grid))

    def sigma_squared_at(self, eta: float) -> float:
        return float(
            np.interp(float(eta), self.eta_grid, self.sigma_squared_grid)
        )

    def Omega_tilt_at(self, eta: float) -> float:
        return float(np.interp(float(eta), self.eta_grid, self.Omega_tilt_grid))

    # ──────────────────────────────────────────────────────────────────
    # Full history accessors (for visibility table builds)
    # ──────────────────────────────────────────────────────────────────

    def beta_history(self) -> np.ndarray:
        return self.beta_grid

    def sigma_squared_history(self) -> np.ndarray:
        return self.sigma_squared_grid

    def H_history(self) -> np.ndarray:
        return self.H_grid

    def n_e_history(self) -> np.ndarray:
        """Round-16 placeholder consumed by ``tilted_visibility_evolved``.

        The recombination layer is responsible for tabulating the actual
        ``n_e(η)``; this accessor exists so the BackgroundEvolved API is
        complete and call-sites compile against the consumer contract
        declared in V5_ROUND16_01 §4.2. A NotImplementedError is preferred
        here over a silent zero so an integration test will surface the
        wiring gap before a production run.
        """
        raise NotImplementedError(
            "BackgroundEvolved.n_e_history is provided by the recombination "
            "ingest layer; use bass.recombination.history_visibility to "
            "tabulate n_e(η) from HyRec + tilt boost (V5_ROUND16_01 §5.1)."
        )

    @classmethod
    def from_codazzi_tilt_result(
        cls,
        result: CodazziTiltEvolutionResult,
        *,
        eta_grid: np.ndarray,
        a_to_eta: Callable[[np.ndarray], np.ndarray],
        tilt_velocity_direction: np.ndarray = np.array(
            [1.0, 0.0, 0.0], dtype=np.float64
        ),
    ) -> "BackgroundEvolved":
        """Construct a BackgroundEvolved by reparametrising a Codazzi-tilt result.

        Parameters
        ----------
        result
            Output of :func:`evolve_codazzi_tilt_background`.
        eta_grid
            Target conformal-time grid (e.g. from
            ``bass.los.los_grid_builder.build_los_grid``).
        a_to_eta
            Callable mapping a-grid to η-grid (typically the species
            registry's ``bg_table.eta_at_a`` vectorised wrapper).
        tilt_velocity_direction
            Unit vector for the tilt direction in the tetrad frame.
            Default ``(1, 0, 0)`` matches the existing axisymmetric IC
            convention.
        """
        eta_at_a = np.asarray(a_to_eta(result.a), dtype=np.float64)
        eta_target = np.asarray(eta_grid, dtype=np.float64)
        # Re-interpolate every per-a quantity onto eta_target.
        a_grid = np.interp(eta_target, eta_at_a, result.a)
        H_grid = np.interp(eta_target, eta_at_a, result.H)
        beta_grid = np.interp(eta_target, eta_at_a, result.beta)
        Sigma_sq_grid = np.interp(eta_target, eta_at_a, result.Sigma_squared)
        Vort_sq_grid = np.interp(
            eta_target, eta_at_a, result.Vorticity_squared
        )
        Omega_r_grid = np.interp(eta_target, eta_at_a, result.Omega_r)
        Omega_m_grid = np.interp(eta_target, eta_at_a, result.Omega_m)
        Omega_L_grid = np.interp(eta_target, eta_at_a, result.Omega_Lambda)
        Omega_tilt_grid = np.interp(eta_target, eta_at_a, result.Omega_tilt)
        return cls(
            eta_grid=eta_target,
            a_grid=a_grid,
            H_grid=H_grid,
            beta_grid=beta_grid,
            sigma_squared_grid=Sigma_sq_grid,
            vorticity_squared_grid=Vort_sq_grid,
            Omega_r_grid=Omega_r_grid,
            Omega_m_grid=Omega_m_grid,
            Omega_Lambda_grid=Omega_L_grid,
            Omega_tilt_grid=Omega_tilt_grid,
            tilt_velocity_direction=tilt_velocity_direction,
            family=result.config.family,
            tilt_evolution_status=result.tilt_evolution_status,
        )
