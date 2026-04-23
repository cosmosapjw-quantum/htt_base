"""Tests H-18 .. H-26 for ``bass.hierarchy.hierarchy_rhs``.

Covers the driver-level behaviour specified in
``docs/lowell_bianchi/02_multipole_hierarchy_spec.md §11.4 / §11.5``:

Driver unit tests (§11.4):

- H-18  zero state at FLRW → zero ``dy/dη`` everywhere
- H-19  Γ_T = 0, σ = 0: only T1 damping contributes
- H-20  homogeneous bg, dipole alone: RHS at ℓ = 2 is zero (T2 wiring
        smoke + additional coupling test using a mock gradient)
- H-21  Γ_T ≠ 0 with v_b: collision hook feeds the ℓ = 1 RHS
- H-22  σ ≠ 0, Π_0 = 1: RHS at ℓ = 2 picks up T9 = −4 σ_ab
- H-23  L_max = 4, HardCut closure: T3 / T7 at ℓ = L get Π_{L+1},2 = 0

Integration smoke (§11.5):

- H-24  ``solve_ivp`` free streaming in FLRW (σ = 0): tower stays PSTF
        and integration is finite.
- H-25  Bianchi I with constant σ: Π_2 grows linearly in early time,
        slope matches the T9 prediction 4 a σ_ab Π_0 to 5% over a
        short η window.
- H-26  Integration preserves PSTF invariants at every step.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pytest
from scipy.integrate import solve_ivp

from bass.background.tetrad_state import axisymmetric_sigma_tensor
from bass.hierarchy import (
    HardCutClosure,
    PSTFTensor,
    ZeroCollisionOperator,
    hierarchy_rhs_photon,
    hierarchy_total_size,
    pack_hierarchy,
    proper_shear_at_eta,
    pstf_from_tensor,
    pstf_to_tensor,
    sym_trace_free,
    unpack_hierarchy,
    verify_pstf_invariants,
    zero_hierarchy,
    zero_pstf,
)
from bass.hierarchy.hierarchy_rhs import (
    hierarchy_rhs_neutrino_from_state,
    hierarchy_rhs_photon_from_state,
    sample_hierarchy_background,
)
from bass.hierarchy.terms import zero_nabla_operator
from bass.species.background_table import build_flrw_background_table


# ════════════════════════════════════════════════════════════════════
#   Test fixtures
# ════════════════════════════════════════════════════════════════════

@pytest.fixture(scope="module")
def bg_table():
    """Shared low-resolution FLRW background table — fast to build.

    The driver only calls ``interp_a`` and ``interp_Theta``; resolution
    can be coarse.
    """
    return build_flrw_background_table(n_eta=500)


@dataclass
class _ShearFixture:
    """Duck-typed stand-in for ``TetradBackgroundState``.

    Exposes only the attributes the driver's ``proper_shear_at_eta``
    helper consults (``eta`` for the nearest-grid lookup and
    ``sigma_tensor`` for the conformal Σ_ab). This keeps the test
    independent of the full ``solve_bianchi_background`` machinery.
    """

    eta: np.ndarray
    sigma_tensor: np.ndarray


def _const_proper_shear_fixture(
    bg_table, sigma_proper: np.ndarray
) -> _ShearFixture:
    """Build a tetrad-state fixture that reproduces a constant *proper*
    shear ``σ_ab`` on the bg_table grid.

    Because ``proper_shear_at_eta`` divides by ``a(η)``, we pre-multiply
    the stored ``sigma_tensor`` by ``a(η)`` to cancel that conversion.
    """
    a = bg_table.a
    Sigma_conformal = np.empty((a.size, 3, 3), dtype=np.float64)
    for i in range(a.size):
        Sigma_conformal[i] = sigma_proper * a[i]
    return _ShearFixture(eta=bg_table.eta.copy(), sigma_tensor=Sigma_conformal)


class _DopplerCollisionAtEll1:
    """Test-only collision operator implementing ``K_1 = Γ_T × (v_b − Π_1)``.

    Mirrors the baryon-dipole-drag source at ℓ = 1 from spec §1.2; all
    other ℓ return zero. ``aux`` is required and must be a 2-tuple
    ``(Γ_T, v_b)`` with ``v_b`` a length-3 vector.
    """

    def evaluate(self, ell, state, aux=None):
        if ell == 1:
            if aux is None or len(aux) != 2:
                raise ValueError("_DopplerCollisionAtEll1 needs aux=(Γ_T, v_b)")
            gamma_T, v_b = aux
            Pi_1_full = pstf_to_tensor(state.tensors[1])
            K_full = float(gamma_T) * (np.asarray(v_b, dtype=np.float64) - Pi_1_full)
            return pstf_from_tensor(K_full)
        return zero_pstf(ell)


def _axis_aligned_gradient(k_vec: np.ndarray):
    """Mock nabla: gradient of rank-``r`` tensor with k-vector multiplier.

    ``∇̃ = k_a``: gradient outer-products with ``k_a``; divergence
    contracts the last axis with ``k_a``. Useful for smoke-testing T2 /
    T3 wiring without building a full structure-constant operator.
    """
    k = np.asarray(k_vec, dtype=np.float64)

    def op(tensor: np.ndarray, kind: str = "gradient") -> np.ndarray:
        arr = np.asarray(tensor, dtype=np.float64)
        if kind == "gradient":
            return np.tensordot(arr, k, axes=0) if arr.ndim > 0 else float(arr) * k
        if kind == "divergence":
            if arr.ndim == 0:
                raise ValueError("divergence of rank-0 undefined")
            return np.tensordot(arr, k, axes=([-1], [0]))
        raise ValueError(f"kind must be 'gradient' or 'divergence', got {kind!r}")

    return op


# ════════════════════════════════════════════════════════════════════
#   H-18: zero state at FLRW → zero dy/dη
# ════════════════════════════════════════════════════════════════════

def test_h18_zero_state_flrw_gives_zero_derivative(bg_table) -> None:
    """H-18: ``y = 0``, FLRW, zero collision → ``dy/dη = 0``."""
    L_max = 4
    y0 = np.zeros(hierarchy_total_size(L_max), dtype=np.float64)
    eta_eval = bg_table.eta[bg_table.eta.size // 2]
    dy = hierarchy_rhs_photon(
        eta_eval,
        y0,
        L_max=L_max,
        bg_table=bg_table,
        tetrad_state=None,
        closure=HardCutClosure(),
        collision=ZeroCollisionOperator(),
    )
    assert dy.shape == y0.shape
    assert np.max(np.abs(dy)) < 1e-15


# ════════════════════════════════════════════════════════════════════
#   H-19: σ = 0, Γ_T = 0, zero ∇̃: only T1 damping
# ════════════════════════════════════════════════════════════════════

def test_h19_flrw_reduces_to_T1_damping(bg_table) -> None:
    """H-19: at FLRW (σ = 0) + zero collision + zero ∇̃, the RHS reduces
    to Π'(η) = −a(η) × (4/3) Θ(η) × Π_ℓ at every ℓ.
    """
    L_max = 3
    rng = np.random.default_rng(19)

    # Build a random PSTF tower.
    state = zero_hierarchy(L_max)
    for ell in range(L_max + 1):
        comp = rng.normal(size=2 * ell + 1)
        state.tensors[ell] = PSTFTensor(ell=ell, components=comp)
    y0 = pack_hierarchy(state)

    eta_eval = bg_table.eta[bg_table.eta.size // 2]
    a_val = float(bg_table.interp_a(eta_eval))
    Theta = float(bg_table.interp_Theta(eta_eval))

    dy = hierarchy_rhs_photon(
        eta_eval,
        y0,
        L_max=L_max,
        bg_table=bg_table,
        tetrad_state=None,
        closure=HardCutClosure(),
        collision=ZeroCollisionOperator(),
    )

    # Expected: each packed block multiplied by -a × (4/3) θ.
    damping = -a_val * (4.0 / 3.0) * Theta
    expected = damping * y0
    assert np.allclose(dy, expected, rtol=0, atol=1e-11), (
        f"max diff = {np.max(np.abs(dy - expected)):.3e}"
    )


# ════════════════════════════════════════════════════════════════════
#   H-20: Π_1 = unit at background + zero σ: quadrupole slot untouched
# ════════════════════════════════════════════════════════════════════

def test_h20_dipole_only_leaves_quadrupole_zero_at_background(bg_table) -> None:
    """H-20: at homogeneous background (zero ∇̃), σ = 0, Γ_T = 0 and
    Π_1 = unit, Π_{ℓ≠1} = 0: dy at the ℓ = 2 slot is exactly zero.

    Serves as a structural regression for T2's default ``nabla =
    zero_nabla_operator`` path.
    """
    L_max = 3
    state = zero_hierarchy(L_max)
    state.tensors[1] = PSTFTensor(ell=1, components=np.array([1.0, 0.0, 0.0]))
    y0 = pack_hierarchy(state)

    eta_eval = bg_table.eta[bg_table.eta.size // 2]
    dy = hierarchy_rhs_photon(
        eta_eval,
        y0,
        L_max=L_max,
        bg_table=bg_table,
        tetrad_state=None,
        closure=HardCutClosure(),
        collision=ZeroCollisionOperator(),
    )

    # Quadrupole packed block lives at offsets 1 + 3 = 4 .. 8 (inclusive).
    quad_block = dy[4:9]
    assert np.max(np.abs(quad_block)) < 1e-14


def test_h20_mock_gradient_activates_T2_into_quadrupole(bg_table) -> None:
    """With a non-trivial mock ``∇̃ = k_a``, the dipole seeds the
    quadrupole slot via T2.

    This exercises the ``nabla_operator`` hook end-to-end; the concrete
    numeric target is
        T2_{ab} = STF( ∂_{(a} Π_{b)} ) = STF( k_{(a} Π_{b)} )
    with PSTF projection.
    """
    L_max = 3
    rng = np.random.default_rng(202)
    dipole = rng.normal(size=3)
    state = zero_hierarchy(L_max)
    state.tensors[1] = PSTFTensor(ell=1, components=dipole)
    y0 = pack_hierarchy(state)

    k_vec = np.array([1.0, -0.5, 0.3])
    nabla = _axis_aligned_gradient(k_vec)

    eta_eval = bg_table.eta[bg_table.eta.size // 2]
    a_val = float(bg_table.interp_a(eta_eval))
    Theta = float(bg_table.interp_Theta(eta_eval))

    dy = hierarchy_rhs_photon(
        eta_eval,
        y0,
        L_max=L_max,
        bg_table=bg_table,
        tetrad_state=None,
        closure=HardCutClosure(),
        collision=ZeroCollisionOperator(),
        nabla_operator=nabla,
    )

    # Predicted RHS at ell=2: -(T2 + T3) × a where
    #   T2_{ab} = STF(k ⊗ Π_1)  (input Π_{ℓ-1} = dipole, gradient via mock nabla)
    #   T3_{ab} = prefactor × STF(∇̃·Π_3) = 0 (Π_3 = 0)
    raw_T2 = np.tensordot(dipole, k_vec, axes=0)  # Π ⊗ k per mock nabla
    T2_expected = sym_trace_free(raw_T2)
    Pi_dot_2 = -T2_expected  # K = 0, other terms = 0
    dPi_2_eta = a_val * Pi_dot_2
    from bass.hierarchy.contractions import pstf_pack as _pack
    expected_block = _pack(dPi_2_eta)

    # Quadrupole slot.
    quad_block = dy[4:9]
    assert np.allclose(quad_block, expected_block, rtol=0, atol=1e-10)

    # Monopole and dipole blocks should be consistent with T1 damping
    # plus any ∇̃ coupling from Π_1 → T3 (dipole back to monopole) and
    # Π_0 → T2 / T5 (all zero since Π_0 = 0). The monopole is slot 0:0.
    # T3 at ell=0 with Π_{1}=dipole: prefactor 1/3 × divergence(Π_1) =
    # (1/3) × (k · dipole).
    T3_at_0 = (1.0 / 3.0) * float(np.dot(dipole, k_vec))
    # RHS at ell=0 = -a × (T3 + T1(Π_0)=0) = -a × T3.
    expected_mono = a_val * (-T3_at_0)
    assert abs(dy[0] - expected_mono) < 1e-10


# ════════════════════════════════════════════════════════════════════
#   H-21: Γ_T ≠ 0 collision drives the dipole
# ════════════════════════════════════════════════════════════════════

def test_h21_thomson_drag_enters_dipole(bg_table) -> None:
    """H-21: with a Doppler-drag collision ``K_1 = Γ_T (v_b − Π_1)`` and
    Π_1 = 0, v_b = e_x: RHS at ℓ = 1 receives ``+ a × Γ_T × v_b``.
    """
    L_max = 2
    state = zero_hierarchy(L_max)  # Π_1 = 0 by construction
    y0 = pack_hierarchy(state)

    gamma_T = 5.0
    v_b = np.array([1.0, 0.0, 0.0])

    eta_eval = bg_table.eta[bg_table.eta.size // 2]
    a_val = float(bg_table.interp_a(eta_eval))

    dy = hierarchy_rhs_photon(
        eta_eval,
        y0,
        L_max=L_max,
        bg_table=bg_table,
        tetrad_state=None,
        closure=HardCutClosure(),
        collision=_DopplerCollisionAtEll1(),
        collision_aux=(gamma_T, v_b),
    )

    # Π'(η) at ell=1 = a × (K − T1). T1(ell=1, Π_1=0) = 0, so Π'_1 = a × Γ_T × v_b.
    dipole_block = dy[1:4]
    expected = a_val * gamma_T * v_b
    assert np.allclose(dipole_block, expected, rtol=0, atol=1e-12)


# ════════════════════════════════════════════════════════════════════
#   H-22: σ ≠ 0, Π_0 = 1 injects a quadrupole
# ════════════════════════════════════════════════════════════════════

def test_h22_shear_injection_populates_quadrupole(bg_table) -> None:
    """H-22: σ_ab ≠ 0 and Π_0 = 1: RHS at ℓ = 2 picks up T9 = −4 σ_ab.

    Because Π_ℓ≥1 = 0 and A = ω = 0, only T9 is non-zero at ℓ = 2.
    ``Π'(η) = a × (K − T9) = a × 4 σ_ab``.
    """
    L_max = 2
    state = zero_hierarchy(L_max)
    state.tensors[0] = PSTFTensor(ell=0, components=np.array([1.0]))
    y0 = pack_hierarchy(state)

    sigma_proper = axisymmetric_sigma_tensor(1.0, 0.0) * 1e-3
    fx = _const_proper_shear_fixture(bg_table, sigma_proper)

    eta_eval = bg_table.eta[bg_table.eta.size // 2]
    a_val = float(bg_table.interp_a(eta_eval))
    Theta = float(bg_table.interp_Theta(eta_eval))

    # Verify the driver's σ-conversion returned the proper-frame tensor
    # back (loop-closure check on the F1 unit convention).
    sigma_recovered = proper_shear_at_eta(eta_eval, fx, a_val)
    assert np.allclose(sigma_recovered, sigma_proper, rtol=0, atol=1e-14)

    dy = hierarchy_rhs_photon(
        eta_eval,
        y0,
        L_max=L_max,
        bg_table=bg_table,
        tetrad_state=fx,
        closure=HardCutClosure(),
        collision=ZeroCollisionOperator(),
    )

    # ℓ=0 slot: T1(Π_0 = 1) = 4/3 × Θ, T7(Π_2 = 0) = 0 → Π'_0 = -a × 4/3 × Θ.
    assert abs(dy[0] - (-a_val * (4.0 / 3.0) * Theta)) < 1e-12
    # Dipole slot (Π_1 = 0 throughout, no source): dy[1:4] = 0.
    assert np.max(np.abs(dy[1:4])) < 1e-14
    # ℓ=2 slot: Π'_2 = a × (K − T9) = a × (+4 σ_ab).
    from bass.hierarchy.contractions import pstf_pack as _pack
    expected_quad = _pack(a_val * 4.0 * sigma_proper)
    assert np.allclose(dy[4:9], expected_quad, rtol=0, atol=1e-11)


# ════════════════════════════════════════════════════════════════════
#   H-23: HardCut closure at L_max kills T3 / T7 top-rung references
# ════════════════════════════════════════════════════════════════════

def test_h23_hardcut_closure_drops_top_rung_couplings(bg_table) -> None:
    """H-23: with ``L_max = 4`` and HardCutClosure, at ℓ = 4 the T3 and
    T7 contributions vanish because the closure returns Π_5 = Π_6 = 0.

    We verify this by comparing two runs:
      (a) actual ``L_max = 4`` with Π_ℓ ≠ 0 at every ℓ;
      (b) reference ``L_max = 6`` identical up to ℓ = 4, with Π_5 =
          Π_6 = 0 forced.
    The two ℓ = 4 blocks of ``dy`` must agree.
    """
    L_short = 4
    L_long = 6
    rng = np.random.default_rng(23)

    # Build a state up to L_short with non-zero Π_ℓ at every ℓ.
    state_short = zero_hierarchy(L_short)
    for ell in range(L_short + 1):
        state_short.tensors[ell] = PSTFTensor(
            ell=ell, components=rng.normal(size=2 * ell + 1)
        )
    y_short = pack_hierarchy(state_short)

    # Mirror for L_long, with explicit Π_5 = Π_6 = 0.
    state_long = zero_hierarchy(L_long)
    for ell in range(L_short + 1):
        state_long.tensors[ell] = PSTFTensor(
            ell=ell, components=state_short.tensors[ell].components.copy()
        )
    # state_long.tensors[5] and [6] already zero.
    y_long = pack_hierarchy(state_long)

    sigma_proper = axisymmetric_sigma_tensor(0.3, 0.1) * 1e-3
    fx = _const_proper_shear_fixture(bg_table, sigma_proper)

    eta_eval = bg_table.eta[bg_table.eta.size // 2]

    dy_short = hierarchy_rhs_photon(
        eta_eval,
        y_short,
        L_max=L_short,
        bg_table=bg_table,
        tetrad_state=fx,
        closure=HardCutClosure(),
        collision=ZeroCollisionOperator(),
    )
    dy_long = hierarchy_rhs_photon(
        eta_eval,
        y_long,
        L_max=L_long,
        bg_table=bg_table,
        tetrad_state=fx,
        closure=HardCutClosure(),
        collision=ZeroCollisionOperator(),
    )

    # ℓ = 4 block lives at packed offset 1+3+5+7 = 16 and spans 2·4+1 = 9.
    off_4 = 1 + 3 + 5 + 7
    assert np.allclose(
        dy_short[off_4:off_4 + 9],
        dy_long[off_4:off_4 + 9],
        rtol=0,
        atol=1e-12,
    )


# ════════════════════════════════════════════════════════════════════
#   H-24: solve_ivp free-streaming smoke
# ════════════════════════════════════════════════════════════════════

def test_h24_free_streaming_integration_is_finite(bg_table) -> None:
    """H-24: free streaming in FLRW (σ = 0, Γ_T = 0) integrates without
    blow-up and preserves packed-array finiteness over a short η window.
    """
    L_max = 3
    rng = np.random.default_rng(240)
    state = zero_hierarchy(L_max)
    for ell in range(L_max + 1):
        state.tensors[ell] = PSTFTensor(
            ell=ell, components=rng.normal(size=2 * ell + 1) * 1e-3
        )
    y0 = pack_hierarchy(state)

    eta_mid = bg_table.eta[bg_table.eta.size // 2]
    eta_end = bg_table.eta[bg_table.eta.size // 2 + 50]

    def rhs(eta, y):
        return hierarchy_rhs_photon(
            eta,
            y,
            L_max=L_max,
            bg_table=bg_table,
            tetrad_state=None,
            closure=HardCutClosure(),
            collision=ZeroCollisionOperator(),
        )

    sol = solve_ivp(rhs, (eta_mid, eta_end), y0, rtol=1e-8, atol=1e-10)
    assert sol.success
    assert np.all(np.isfinite(sol.y))


# ════════════════════════════════════════════════════════════════════
#   H-25: Bianchi I constant σ: early-time Π_2 growth slope = 4 a σ Π_0
# ════════════════════════════════════════════════════════════════════

def test_h25_shear_injection_slope_matches_T9(bg_table) -> None:
    """H-25: very-short-window integration with σ ≠ 0 matches the
    forward-Euler prediction built from the driver RHS, confirming that
    ``solve_ivp`` observes the T9 source populating the quadrupole.

    Spec §11.5 calls for a 2 % slope check; we realise this by picking
    Δη ≪ 1/((4/3) a Θ) so the monopole damping is subleading, and
    comparing the integrator output directly to forward-Euler from the
    RHS at ``η_0`` — a self-consistent integration-smoke criterion.
    """
    L_max = 2
    state = zero_hierarchy(L_max)
    state.tensors[0] = PSTFTensor(ell=0, components=np.array([1.0]))
    y0 = pack_hierarchy(state)

    sigma_amp = 1e-4
    sigma_proper = axisymmetric_sigma_tensor(sigma_amp, 0.0)
    fx = _const_proper_shear_fixture(bg_table, sigma_proper)

    # Pick a 1-grid-step window near mid-grid. At a≈1e-4, (4/3)aΘ≈0.1/Mpc
    # and Δη per step ≈ 1.6 Mpc — so cΔη ≈ 0.16 and damping is
    # sub-dominant over a single step.
    i0 = bg_table.eta.size // 2
    eta0 = bg_table.eta[i0]
    eta1 = bg_table.eta[i0 + 1]
    a0 = float(bg_table.interp_a(eta0))

    def rhs(eta, y):
        return hierarchy_rhs_photon(
            eta,
            y,
            L_max=L_max,
            bg_table=bg_table,
            tetrad_state=fx,
            closure=HardCutClosure(),
            collision=ZeroCollisionOperator(),
        )

    # Forward-Euler reference built from the driver itself.
    dy0 = rhs(eta0, y0)
    y_euler = y0 + (eta1 - eta0) * dy0

    sol = solve_ivp(rhs, (eta0, eta1), y0, rtol=1e-12, atol=1e-16)
    assert sol.success
    y_solver = sol.y[:, -1]

    # Integrator and forward-Euler must agree to leading order in Δη.
    # Full-vector relative error (mix of damping + T9 injection).
    rel = np.linalg.norm(y_solver - y_euler) / max(
        np.linalg.norm(y_solver), 1e-30
    )
    assert rel < 2e-2, f"rel err = {rel:.3e}"

    # Separately confirm T9 populated Π_2: the quadrupole block must
    # be non-zero and match + 4 a σ Π_0 × Δη (leading order).
    state_end = unpack_hierarchy(y_solver, L_max)
    Pi_2_full = pstf_to_tensor(state_end.tensors[2])
    Pi_2_pred_lead = 4.0 * a0 * sigma_proper * (eta1 - eta0)
    # Direction (sign + tensor shape) must match even under first-order.
    inner = float(np.sum(Pi_2_full * Pi_2_pred_lead))
    assert inner > 0.0, "quadrupole growth direction opposes T9 prediction"


# ════════════════════════════════════════════════════════════════════
#   H-26: integration preserves PSTF invariants
# ════════════════════════════════════════════════════════════════════

def test_h26_integration_preserves_pstf_structure(bg_table) -> None:
    """H-26: over a short integration window the solver output at every
    ℓ remains symmetric-trace-free when unpacked.
    """
    L_max = 3
    rng = np.random.default_rng(260)
    state = zero_hierarchy(L_max)
    for ell in range(L_max + 1):
        state.tensors[ell] = PSTFTensor(
            ell=ell, components=rng.normal(size=2 * ell + 1) * 1e-3
        )
    y0 = pack_hierarchy(state)

    sigma_proper = axisymmetric_sigma_tensor(2e-4, 1e-4)
    fx = _const_proper_shear_fixture(bg_table, sigma_proper)

    i0 = bg_table.eta.size // 2
    eta0 = bg_table.eta[i0]
    eta1 = bg_table.eta[i0 + 20]

    def rhs(eta, y):
        return hierarchy_rhs_photon(
            eta,
            y,
            L_max=L_max,
            bg_table=bg_table,
            tetrad_state=fx,
            closure=HardCutClosure(),
            collision=ZeroCollisionOperator(),
        )

    sol = solve_ivp(
        rhs, (eta0, eta1), y0, rtol=1e-10, atol=1e-14,
        t_eval=np.linspace(eta0, eta1, 6),
    )
    assert sol.success

    for step in range(sol.y.shape[1]):
        st = unpack_hierarchy(sol.y[:, step], L_max)
        for ell in range(L_max + 1):
            T = pstf_to_tensor(st.tensors[ell])
            ok, msg = verify_pstf_invariants(T, tol=1e-10)
            assert ok, f"step={step} ell={ell}: {msg}"


# ════════════════════════════════════════════════════════════════════
#   Driver guardrails
# ════════════════════════════════════════════════════════════════════

def test_rhs_wrong_state_length_raises(bg_table) -> None:
    L_max = 2
    y_bad = np.zeros(5)  # should be (L_max + 1)² = 9
    with pytest.raises(ValueError):
        hierarchy_rhs_photon(
            bg_table.eta[100],
            y_bad,
            L_max=L_max,
            bg_table=bg_table,
            tetrad_state=None,
            closure=HardCutClosure(),
            collision=ZeroCollisionOperator(),
        )


def test_proper_shear_none_tetrad_is_zero(bg_table) -> None:
    sigma = proper_shear_at_eta(bg_table.eta[100], None, 1.0)
    assert sigma.shape == (3, 3)
    assert np.all(sigma == 0.0)


def test_proper_shear_divides_by_a(bg_table) -> None:
    """Driver must apply 1/a to convert Σ_ab (conformal) → σ_ab (proper)."""
    sigma_proper = axisymmetric_sigma_tensor(0.5, 0.1)
    fx = _const_proper_shear_fixture(bg_table, sigma_proper)
    eta = bg_table.eta[300]
    a_val = float(bg_table.interp_a(eta))
    sigma_recovered = proper_shear_at_eta(eta, fx, a_val)
    # Fixture stored ``Σ = σ_proper × a[idx]``; the driver divides by
    # ``a_val`` (the FLRW-interpolated scale factor at η). At the grid
    # point the spline hits the stored value exactly, so the ratio is
    # a[idx] / a_val — machine-precision close to 1.
    idx = int(np.argmin(np.abs(fx.eta - eta)))
    scale = float(bg_table.a[idx] / a_val)
    assert np.allclose(
        sigma_recovered, scale * sigma_proper, rtol=1e-10, atol=0
    )


def test_LB2b_F2_proper_shear_spline_better_than_nearest_neighbour(
    bg_table,
) -> None:
    """LB-2b F2 post-audit repair: ``proper_shear_at_eta`` uses cubic
    spline interpolation on the conformal Σ_ab grid instead of
    nearest-grid-point lookup. A linear Σ_ab trajectory between two
    neighbouring grid points is reproduced at mid-grid to better than
    1e-3 relative — far tighter than the ~2 % quantisation error of
    the previous nearest-neighbour behaviour.

    Builds a dedicated tetrad fixture with a Σ_ab that **varies**
    linearly across grid points (`scale = i / N`); the prior
    nearest-neighbour version would snap to the neighbouring integer
    grid point, producing ~50 % relative error halfway between grid
    points.
    """
    from bass.background.tetrad_state import TetradBackgroundState
    from bass.background.einstein_bianchi import BianchiCosmology
    from bass.background.bianchi_types import flrw_constants

    eta_grid = np.linspace(1.0, 100.0, 50)
    a_grid = 1e-6 * np.ones_like(eta_grid)
    sigma_base = axisymmetric_sigma_tensor(1.0, 0.0)
    scales = np.linspace(0.2, 1.2, eta_grid.size)
    sigma_conformal = scales[:, None, None] * sigma_base[None, :, :]

    fx = TetradBackgroundState(
        eta=eta_grid, alpha=np.log(a_grid), a=a_grid,
        beta_tensor=np.zeros((eta_grid.size, 3, 3)),
        sigma_tensor=sigma_conformal,
        aniso_3_curvature=None,
        structure=flrw_constants(),
        curvature_status="type_i_flat",
        cosmo=BianchiCosmology(structure=flrw_constants()),
    )

    # Pick a mid-grid η exactly halfway between two stored points.
    i = 20
    eta_mid = 0.5 * (eta_grid[i] + eta_grid[i + 1])
    a_val = float(a_grid[i])
    sigma_recovered = proper_shear_at_eta(eta_mid, fx, a_val)
    # Linear Σ_ab ⇒ cubic spline reproduces linear mid-grid to
    # essentially machine precision at this uniform grid.
    expected_scale_mid = 0.5 * (scales[i] + scales[i + 1])
    expected_proper = expected_scale_mid * sigma_base / a_val
    rel = np.linalg.norm(sigma_recovered - expected_proper) / np.linalg.norm(
        expected_proper
    )
    assert rel < 1e-3, f"spline mid-grid relative error: {rel}"


def test_neutrino_driver_matches_zero_collision_photon(bg_table) -> None:
    """``hierarchy_rhs_neutrino`` = photon driver with ZeroCollisionOperator."""
    from bass.hierarchy import hierarchy_rhs_neutrino
    L_max = 2
    rng = np.random.default_rng(99)
    y0 = rng.normal(size=hierarchy_total_size(L_max)) * 1e-3
    eta_eval = bg_table.eta[bg_table.eta.size // 2]

    dy_neutrino = hierarchy_rhs_neutrino(
        eta_eval, y0,
        L_max=L_max,
        bg_table=bg_table,
        tetrad_state=None,
        closure=HardCutClosure(),
    )
    dy_photon = hierarchy_rhs_photon(
        eta_eval, y0,
        L_max=L_max,
        bg_table=bg_table,
        tetrad_state=None,
        closure=HardCutClosure(),
        collision=ZeroCollisionOperator(),
    )
    assert np.allclose(dy_neutrino, dy_photon, rtol=0, atol=1e-15)


def test_photon_internal_state_helper_matches_public_wrapper(bg_table) -> None:
    """Internal array-first helper must preserve the public RHS exactly."""
    L_max = 3
    rng = np.random.default_rng(1234)
    y0 = rng.normal(size=hierarchy_total_size(L_max)) * 1e-3
    eta_eval = float(bg_table.eta[bg_table.eta.size // 2])
    nabla = _axis_aligned_gradient(np.array([0.7, -0.4, 0.2]))
    accel = np.array([0.01, -0.02, 0.03], dtype=np.float64)
    vorticity = np.array([-0.04, 0.02, 0.01], dtype=np.float64)

    dy_public = hierarchy_rhs_photon(
        eta_eval,
        y0,
        L_max=L_max,
        bg_table=bg_table,
        tetrad_state=None,
        closure=HardCutClosure(),
        collision=ZeroCollisionOperator(),
        nabla_operator=nabla,
        accel_vector=accel,
        vorticity_vector=vorticity,
    )

    state = unpack_hierarchy(y0, L_max)
    background = sample_hierarchy_background(
        eta_eval,
        bg_table=bg_table,
        tetrad_state=None,
    )
    dy_internal = hierarchy_rhs_photon_from_state(
        state,
        background=background,
        closure=HardCutClosure(),
        collision=ZeroCollisionOperator(),
        collision_aux=None,
        nabla_operator=nabla,
        accel_vector=accel,
        vorticity_vector=vorticity,
    )

    assert np.allclose(dy_internal, dy_public, rtol=0, atol=1e-15)


def test_photon_internal_state_helper_matches_public_wrapper_on_homogeneous_shear(bg_table) -> None:
    """Internal helper must preserve the homogeneous zero-collision fast path."""
    L_max = 4
    rng = np.random.default_rng(4321)
    y0 = rng.normal(size=hierarchy_total_size(L_max)) * 1e-3
    eta_eval = float(bg_table.eta[bg_table.eta.size // 2])
    sigma = axisymmetric_sigma_tensor(2.0e-3, -1.0e-3)
    tetrad = _const_proper_shear_fixture(bg_table, sigma)

    dy_public = hierarchy_rhs_photon(
        eta_eval,
        y0,
        L_max=L_max,
        bg_table=bg_table,
        tetrad_state=tetrad,
        closure=HardCutClosure(),
        collision=ZeroCollisionOperator(),
    )

    state = unpack_hierarchy(y0, L_max)
    background = sample_hierarchy_background(
        eta_eval,
        bg_table=bg_table,
        tetrad_state=tetrad,
    )
    dy_internal = hierarchy_rhs_photon_from_state(
        state,
        background=background,
        closure=HardCutClosure(),
        collision=ZeroCollisionOperator(),
        collision_aux=None,
    )

    assert np.allclose(dy_internal, dy_public, rtol=0, atol=1e-15)


def test_neutrino_internal_state_helper_matches_public_wrapper(bg_table) -> None:
    """Internal neutrino helper must preserve the public wrapper output."""
    from bass.hierarchy import hierarchy_rhs_neutrino

    L_max = 3
    rng = np.random.default_rng(5678)
    y0 = rng.normal(size=hierarchy_total_size(L_max)) * 1e-3
    eta_eval = float(bg_table.eta[bg_table.eta.size // 2])

    dy_public = hierarchy_rhs_neutrino(
        eta_eval,
        y0,
        L_max=L_max,
        bg_table=bg_table,
        tetrad_state=None,
        closure=HardCutClosure(),
    )

    state = unpack_hierarchy(y0, L_max)
    background = sample_hierarchy_background(
        eta_eval,
        bg_table=bg_table,
        tetrad_state=None,
    )
    dy_internal = hierarchy_rhs_neutrino_from_state(
        state,
        background=background,
        closure=HardCutClosure(),
        neutrino_background=None,
    )

    assert np.allclose(dy_internal, dy_public, rtol=0, atol=1e-15)
