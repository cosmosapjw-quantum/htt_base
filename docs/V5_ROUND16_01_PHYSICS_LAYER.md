# V5 Round-16 — Physics Layer (Background, Geometry, Tilt, Recomb/Reion)
_Authority: this doc + V5_ROUND16_00. Status: implementation-ready._

This document specifies the physics-layer architecture: the full per-family Bianchi background ODE with King-Ellis-evolved global tilt, the PSTF/tetrad geometry stack, and the anisotropy-aware recombination/reionization extensions. Each section ends with skeleton code, pseudocode, tests with tolerances, and an adversarial audit checklist.

## 1. Conventions (frozen)

```
Signature:      g_ab = -u_a u_b + h_ab        [(-,+,+,+)]
Tetrad:         e^a_A,  γ_AB = δ_ab e^a_A e^b_B
PSTF projector: X_⟨AB⟩ = X_(AB) - (1/3) γ_AB γ^CD X_CD
Conformal time: dη = dt / a_m,  a_m = mean scale factor (det(γ)^{1/6})
Shear sign:     σ_ab = ∇_⟨a u_b⟩  ⟹  σ²:= σ_ab σ^ab ≥ 0
Tilt rapidity:  u^a_e = γ_e (n^a + v^a_e),  γ_e = cosh β,  v_e = sinh β v̂_e
SSoT references: bianchi_design_pack_v5/01_SSOT_FORMALISM_AND_PHYSICS.md §2
                 docs/lowell_bianchi/00_conventions.md §4.1
```

**Banned forms in this layer**:
- Any `if family == "FLRW"` shortcut that bypasses tilt or shear evolution.
- Any "small β" linearization in the *production* RHS. Linearized variants live in `validation/` only and carry `linearization_status="diagnostic_only"` metadata.
- Any synchronous-gauge metric variable (`h_S`, `ḣ_S`); BASS is PSTF/tetrad-native (CLAUDE.md §1).

## 2. Per-family geometry stack (closes G3-geometry side)

The geometry stack provides `BianchiGeometry` objects per (family, branch, h) that produce:
- Structure constants `C^A_{BC}` (eight Class-A + three Class-B intrinsic + h-continuous VI_h, VII_h).
- Spatial Ricci tensor `^{(3)}R_AB` and its PSTF γ-projection `S_AB`.
- Background-coupled mode operators consumed by the hierarchy (`L_A`, `n_AB`, `a_A`).

**Per-family algebra** (frozen by `bianchi_design_pack_v5/03B`):

| Family | Class | Algebra (n_1, n_2, n_3; a) | Spatial spectrum |
|--------|-------|------------------------------|------------------|
| I       | A | (0, 0, 0; 0) | plane waves e^{ik·x}; ∇² = −k² |
| II      | A | (n_1, 0, 0; 0), n_1 > 0 | nilpotent Heisenberg; eigenvalue −(k_1² + n_1²k_⊥²/4) |
| VI₀     | A | (0, 1, −1; 0) | solvable e(1,1); −(k_1² + k_3²), k_2 ∈ ℤ (lattice) |
| VII₀    | A | (0, 1, 1; 0) | helical Euclidean; −(k_⊥² + k_3² ± 2 k_⊥) |
| VIII    | A | (−1, 1, 1; 0) | sl(2,ℝ) Plancherel — continuous (μ, s) + discrete D^±_λ |
| IX      | A | (1, 1, 1; 0) | compact SU(2); discrete ℓ(ℓ+2) |
| III    | B | (0, 1, −1; √(-h)), h = -1 | hyperbolic; −(k² + a²/2) |
| IV     | B | (0, 0, 1; a > 0) | solvable rank-1; −(k_1² + k_2² + a²) |
| V      | B | (0, 0, 0; a > 0) | open hyperbolic; −(k² + a²) |
| VI_h   | B | (0, 1, −1; √(-h)), h ∈ (-∞,-1) ∪ (-1,0) | h-continuous: −(|k|² + a²/(1+h)) |
| VII_h  | B | (0, 1, 1; √h), h > 0 | helical-open Pontzen-Challinor; −(|k|² + a²/(1+h)) ∓ 2a√h |

These are read into `bass/background/bianchi_types.py` (already implemented; no change needed for §2).

### 2.1 Spatial Ricci computation (frozen)

For all 11 families, the closed form (Wainwright-Ellis 1997, eq. 1.10):
```
^{(3)}R_AB = (1/4) [ 2 n_AC n^C_B − n^C_C n_AB − γ_AB ((1/2)(n^C_C)² − n^DE n_DE) ]
            + a_C (n^{C}_{(A} γ_{B)D} − n_{(A}^{D} γ_{B)C}) ε^{...}
            − a_A a_B + γ_AB a_C a^C
```
The PSTF γ-projection `S_AB := ^{(3)}R_⟨AB⟩` is the source for the shear evolution equation in §3.

### 2.2 Skeleton

```python
# bass/background/geometry_per_family.py
@dataclass(frozen=True)
class BianchiGeometry:
    family: str
    branch: Literal["orthogonal", "tilted"]
    h: float | None
    structure_constants: StructureConstants  # frozen registry entry
    triad_dual: np.ndarray  # e_A^i, shape (3,3); inverse e^A_i
    
    def spatial_ricci(self) -> np.ndarray:
        """Return ^{(3)}R_AB in tetrad indices, shape (3,3)."""
        ...
    def pstf_curvature(self) -> np.ndarray:
        """Return S_AB := ^{(3)}R_⟨AB⟩ (PSTF γ-projection), shape (3,3)."""
        ricci = self.spatial_ricci()
        gamma = self.structure_constants.metric_tetrad()  # γ_AB
        trace = np.einsum("AB,AB->", gamma, ricci)
        return ricci - (1/3) * trace * gamma
    def laplacian_eigenvalue(self, k_vec: np.ndarray) -> complex:
        """Return ∇² eigenvalue for spatial harmonic at k_vec. Family-dispatched."""
        ...
```

## 3. Codazzi-consistent tilted-Bianchi background ODE (closes G4)

This section replaces the static-β authority path (`bass/background/einstein_bianchi.py:98-156`) with a *jointly evolved* state vector and Codazzi residual enforced *during* integration.

### 3.1 State variables

```
y_bg = (
    a,              # mean scale factor
    σ_+, σ_-,       # tetrad shear (PSTF traceless 2-of-5 components)
    σ_×1, σ_×2, σ_×3,  # off-diagonal 3 components — non-zero for non-Type-I
    β,              # tilt rapidity
    Ω_r, Ω_m, Ω_Λ,  # species fractions (matter/radiation/Λ)
    [Ω_k]           # only for Class-B: V, III, IV, VI_h, VII_h
)
```

The current code holds `(a, Σ_+, Σ_-)` (3 vars); Round-16 adds 4 more for full anisotropic shear and 1 for tilt (β). Class-B adds Ω_k → 8–9 vars depending on family.

### 3.2 Pinned RHS

From Ellis-Maartens-MacCallum §18 + nonperturbative_tilt.py §3:

```
ȧ = (1/3) Θ a                                                 (Hubble)

Θ̇ = -(1/3) Θ² - 2 σ² - (1/2) κ (ρ_tot + 3 p_tot) + Λ           (Raychaudhuri)

σ̇_⟨AB⟩ = -(2/3) Θ σ_AB - σ_⟨A^C σ_B⟩C
        - S_AB  +  (1/2) κ π_AB^{tilt}                         (shear)

dβ/dN = -(1 - 3 c_s²) sinh β cosh β                            (King-Ellis tilt)
       where N = ln a, c_s² = p_tot / ρ_tot

Ω̇_r = -4 ℋ Ω_r,   Ω̇_m = -3 ℋ Ω_m                              (species; FLRW limit)
                  + tilt-driven corrections at O(sinh² β)      (King-Ellis 1973 §4)

S_AB = ^{(3)}R_⟨AB⟩  computed at each step from current (γ_AB, n_AB, a_A)

π_AB^{tilt} = Σ_s (ρ̂_s + p̂_s) γ_s² v_{s,⟨A} v_{s,B⟩}           (anisotropic stress
                                                                 sourced by tilt)
```

The shear PSTF projection `σ_⟨AB⟩` enforces traceless + symmetric, so 5 (instead of 6) independent components remain. We use the standard 5-component vector `(σ_+, σ_-, σ_{×1}, σ_{×2}, σ_{×3})` with σ_+ = (1/2)(σ_11 - σ_22), σ_- = (1/(2√3))(σ_11 + σ_22 - 2σ_33), and σ_{×i} the three off-diagonals.

### 3.3 Codazzi constraint as runtime gate

```
C_C^A := D_B σ^AB - (2/3) D^A Θ - κ q^A                    [≡ 0 on-shell]

|| C_C^A ||₂ / H_ref²  ≤  10⁻⁶   (tightened from current 10⁻⁴)
```

Enforced per RHS call via `bass/background/constraints.py` — already monitored, but now (a) the gate threshold becomes **integration-aborting** (not just metadata-flag), (b) the projection step `project_shear_to_codazzi()` runs not only at IC but optionally at each output step (controlled by `runtime_controls.codazzi_projection_cadence`).

### 3.4 Skeleton

```python
# bass/background/codazzi_tilt_rhs.py  (NEW; replaces einstein_bianchi.py authority)
import numpy as np
from typing import Callable
from bass.background.bianchi_types import StructureConstants
from bass.background.geometry_per_family import BianchiGeometry
from bass.background.constraints import codazzi_constraint_residual

def background_state_dim(family: str) -> int:
    """5 (FLRW limit) + 5 σ + 1 β + 3 species + 1 Ω_k for Class-B."""
    base = 5 + 5 + 1 + 3
    if family in {"V", "III", "IV", "VI_h", "VII_h"}:
        base += 1
    return base

def background_rhs_codazzi_tilt(
    eta: float,
    y: np.ndarray,
    *,
    geometry: BianchiGeometry,
    species_eos: SpeciesEOS,           # gives c_s²(a), p_tot(a, β), ρ_tot(a, β)
    Lambda: float,
    codazzi_residual_threshold: float = 1.0e-6,
) -> np.ndarray:
    """
    Joint Codazzi-consistent RHS of the (a, σ, β, Ω) background.
    Raises CodazziProjectionError if ||C_C^A||/H² exceeds threshold.
    """
    a, sigma_5, beta, Omega_r, Omega_m, Omega_L, Omega_k = unpack(y, geometry.family)
    
    # 1. Hubble + species
    rho_tot, p_tot = species_eos.totals(a, beta)
    H = hubble_from_friedmann(a, sigma_5, Omega_r, Omega_m, Omega_L, Omega_k)
    Theta = 3.0 * H
    
    # 2. Geometry — S_AB at this step
    S_AB = geometry.pstf_curvature()  # frozen at family level
    
    # 3. Tilt-induced anisotropic stress
    pi_AB_tilt = species_anisotropic_stress(species_eos, a, beta, geometry)
    
    # 4. Shear evolution (PSTF traceless 5-vector)
    sigma_dot_5 = (
        -(2.0/3.0) * Theta * sigma_5
        - shear_self_coupling(sigma_5)        # σ_⟨A^C σ_B⟩C in 5-vec basis
        - pstf_5vec(S_AB)                     # spatial Ricci anisotropy
        + 0.5 * kappa * pstf_5vec(pi_AB_tilt) # tilted matter source
    )
    
    # 5. Tilt rapidity
    c_s_sq = p_tot / rho_tot
    dbeta_dlna = -(1.0 - 3.0 * c_s_sq) * np.sinh(beta) * np.cosh(beta)
    dbeta_deta = (1.0 / a) * H * dbeta_dlna   # dN = H dt = (H/a) dη  (mind units)
    
    # 6. Species evolution (with tilt corrections)
    Omega_dot = species_evolution_rhs(a, beta, Omega_r, Omega_m, Omega_L, Omega_k)
    
    # 7. Codazzi gate — abort integration if drift exceeds threshold
    C_resid = codazzi_constraint_residual(sigma_5, beta, geometry, H)
    if np.linalg.norm(C_resid) / max(H**2, 1e-30) > codazzi_residual_threshold:
        raise CodazziProjectionError(
            f"Codazzi residual {np.linalg.norm(C_resid)/H**2:.3e} > "
            f"{codazzi_residual_threshold:.0e} at η={eta}"
        )
    
    return pack(
        a_dot=H * a,
        sigma_dot_5=sigma_dot_5,
        beta_dot=dbeta_deta,
        Omega_dot=Omega_dot,
    )
```

### 3.5 Pseudocode for `project_shear_to_codazzi`

```python
def project_shear_to_codazzi(sigma_5, beta, geometry, *, max_iter=10, tol=1e-10):
    """
    Project σ onto the Codazzi-constraint surface using a Newton step:
        σ_new = σ - α ∇C  with α = (∇C)^T C / (∇C)^T (∇C) + ε
    Iterate until ||C|| < tol or max_iter.
    """
    sigma = sigma_5.copy()
    for _ in range(max_iter):
        C = codazzi_constraint_residual(sigma, beta, geometry, H_local)
        if np.linalg.norm(C) < tol:
            break
        grad_C = codazzi_jacobian(sigma, beta, geometry, H_local)  # 3×5 matrix
        sigma -= np.linalg.lstsq(grad_C, C, rcond=None)[0]
    else:
        raise CodazziProjectionError("Codazzi projection failed to converge")
    return sigma
```

### 3.6 Tests + tolerances

```
test_background_codazzi_tilt_evolution.py
- test_flrw_limit_recovers_isotropic_friedmann: σ=0, β=0 → standard FRW within 1e-12
- test_type_i_static_beta_recovered: β_initial=0.1, force tilt_freeze=True → constant β within 1e-15
- test_type_i_evolved_beta_decays: β_initial=0.1, tilt_freeze=False, in radiation era →
    β(N) follows King-Ellis exponential decay e^{-(1-3·1/3)N} = constant (RD has c_s²=1/3),
    matter era → β decays as e^{-N} within 1e-6 over [N=-3, N=0]
- test_codazzi_residual_under_1e-6: every output step
- test_shear_decays_as_a_minus_3: σ²·a⁶ approximately constant in MD-only (Bianchi I)
- test_class_b_curvature_scales_correctly: Ω_k a² constant (Type V)
```

### 3.7 Adversarial audit checklist (PR-S1)

```
A1 (toy/naive):
  □ grep for "small_beta", "linear_tilt", "if abs(beta) < ": every hit removed or
    moved to bass/validation/ with linearization_status="diagnostic_only"
  □ grep for "FLRW shortcut" branches in background_rhs_codazzi_tilt: zero hits

A2 (pretend perturbation as nonperturbative):
  □ Verify dβ/dN includes sinh(β)·cosh(β), not β·1 (small-β truncation)
  □ Verify π_AB^{tilt} scales as sinh²(β), not β²

A3 (temporary analytic model):
  □ Verify project_shear_to_codazzi() actually iterates (max_iter ≥ 1 documented)
  □ Verify no constant-Codazzi-residual placeholder

A5 (tilt + anisotropy correction):
  □ For each shear/curvature term: verify the corresponding tilt contribution
    enters at the same line group (no asymmetric application)
  □ Verify tilt_freeze=True removes ALL tilt-induced corrections, not just dβ/dN

A6 (family-specific code path silently FLRW):
  □ For each non-FLRW family: assert that S_AB ≠ 0 in the RHS at any t > 0
  □ Verify Class-B branches carry Ω_k state and update Ω_k through Friedmann

A7 (convergence):
  □ Re-run with rtol ∈ {1e-6, 1e-8, 1e-10}; D_2 final ≤ 1e-3 spread
  □ Codazzi residual scales as O(rtol²) with rtol → 0
```

## 4. Anisotropic-frame visibility and electron-frame collision (links to 02 §5)

The collision/visibility layer is *fully* implemented for FLRW + tilted observer (G found this code is exact on the rate side). Round-16 *extends* it to the case where the cosmological tilt β evolves: the collision rate must be re-evaluated at each integration step from the *current* `β(η)` (formerly static).

### 4.1 Direction-resolved opacity (frozen)

```
Γ̃_T(η, ê) = a(η) ñ_e(η, β) σ_T γ_e(η) [1 - v_e(η) · ê]    (electron frame)
ñ_e(η, β)  = n_e(η) cosh β                                    (Lorentz-boosted density)
g̃(η, ê)   = Γ̃_T(η, ê) e^{-κ̃(η, ê)}
κ̃(η, ê)   = ∫_η^{η_0} Γ̃_T(η', ê) dη'
```

Round-16 work: tabulate `n_e(η)` from the unbiased recombination output; `cosh β` is then read from the background ODE; the integrand for `κ̃` is direction-dependent → the integral is precomputed per (η, ê) on a discrete sky grid (default `Nside=8`, 768 directions).

### 4.2 Skeleton (extension)

```python
# bass/transport/tilted_visibility_evolved.py
def build_tilted_visibility_history(
    *,
    bg: BackgroundEvolved,                # carries β(η), n_e(η)
    sky_grid: HealpixGrid,                # Nside=8 default
) -> TiltedVisibilityHistory:
    """Tabulate g̃(η, ê) for all (η, ê) consumed by Bianchi LoS in 03 §2."""
    eta_grid = bg.eta_grid
    ne_eta   = bg.n_e_history()           # from recombination + tilt boost
    beta_eta = bg.beta_history()
    
    Gamma_tilde = np.zeros((len(eta_grid), sky_grid.npix))
    for i, eta in enumerate(eta_grid):
        gamma_e = np.cosh(beta_eta[i])
        v_e_dir = sinh_beta * v_hat_e_history[i]   # (3,)
        ne_boosted = ne_eta[i] * gamma_e
        for j, e_hat in enumerate(sky_grid.directions):
            Gamma_tilde[i, j] = (
                bg.a(eta) * ne_boosted * SIGMA_T * gamma_e
                * (1.0 - np.dot(v_e_dir, e_hat))
            )
    
    # Integrate κ̃ along η for each direction; back-cumulative trapezoid.
    kappa_tilde = np.zeros_like(Gamma_tilde)
    for j in range(sky_grid.npix):
        kappa_tilde[:, j] = -cumtrapz_back(Gamma_tilde[:, j], eta_grid, initial=0.0)
    g_tilde = Gamma_tilde * np.exp(-kappa_tilde)
    
    return TiltedVisibilityHistory(eta_grid=eta_grid, sky_grid=sky_grid,
                                    Gamma_tilde=Gamma_tilde, g_tilde=g_tilde,
                                    kappa_tilde=kappa_tilde)
```

### 4.3 Tests

```
test_tilted_visibility_evolved.py
- test_no_tilt_reproduces_isotropic: β≡0 → g̃ direction-independent and = g_FLRW
- test_dipole_only_tilt_recovers_dipole: β=0.05, v̂_e=(1,0,0) →
    g̃(η,ê) - g_FLRW(η) ∝ (ê·v̂_e) at peak η_*; coefficient matches sinh β · n_e(η_*) σ_T ...
- test_evolved_tilt_changes_visibility_peak: dβ/dN active → g̃ peak shifts
    with respect to fixed-β by ≥ 1e-3 absolute at z=1100
```

### 4.4 Adversarial audit (PR-A2; subset of PR-S1)

```
A5 (tilt always applied):
  □ Verify the 1-v_e·ê factor carries (1 - v_e·ê), not (1 + v_e·ê) (sign of Doppler:
    photon propagation direction convention); see PhotonDirectionConvention enum.
  □ Verify cosh β multiplies n_e (Lorentz boost of electron density), not just γ_e
    in the 1-v_e·ê factor.
  □ Verify the v_e·ê dot-product uses tetrad-frame components (not coordinate).
A6 (no FLRW shortcut):
  □ Verify there is no `if v_hat_e is None: return g_flrw_isotropic` shortcut
    that silently bypasses the direction integral.
```

## 5. Recombination extension (anisotropic-frame coupling)

BASS imports HyRec as a fixture (`bass/recombination/fixtures/recombination_ref_planck2018.csv`). For Round-16 the *anisotropic-coupling* extension specified in `recombination_design.md §5.1` becomes implementation-grade. The minimum viable path is:

1. Use HyRec output `(z, x_e, T_m)` as the **isotropic baseline**.
2. Add a *tilt correction* to the visibility integrand: `n_e(η, β) = n_e^HyRec(η) cosh β(η)`.
3. Add a *shear correction* to the recombination temperature `T_m(η, σ²)` via the geometry-dependent frequency drift `d ln ν / dℓ = -(Θ/3 + σ_ij n^i n^j)`. For low-shear cases (σ²/H² < 10⁻⁵), this reduces to the FLRW HyRec output to better than 10⁻⁴ accuracy.

Higher-order full angular line-RT (line core diffusion via S_N short-characteristics) is **Round-17**.

### 5.1 Skeleton

```python
# bass/recombination/anisotropic_correction.py  (NEW)
def apply_tilt_shear_correction(
    hyrec_table: HyRecTable,
    bg_evolved: BackgroundEvolved,
    *,
    shear_correction_active: bool = True,
) -> AnisotropicRecombinationTable:
    """Return (z, x_e, T_m) with first-order tilt + shear corrections."""
    table = hyrec_table.copy()
    eta_grid = bg_evolved.eta_grid
    table.n_e = table.n_e_baseline * np.cosh(bg_evolved.beta_history())
    if shear_correction_active:
        sigma_sq = bg_evolved.sigma_squared_history()
        # First-order shift in T_m from anisotropic redshift; bounded by σ²/H²
        ratio = sigma_sq / bg_evolved.H_history() ** 2
        if np.max(ratio) > 1.0e-3:
            warnings.warn(
                f"σ²/H² peak {np.max(ratio):.3e} exceeds linear-correction "
                "validity range; promote to full angular line-RT (Round-17)."
            )
        table.T_m = table.T_m_baseline * (1.0 - (1.0/3.0) * ratio)
    table.tilt_correction_status = "linear_in_sinh_beta_squared"
    table.shear_correction_status = "linear_in_sigma_sq_over_H_sq"
    return table
```

### 5.2 Tests

```
test_recombination_anisotropic_correction.py
- test_no_tilt_no_shear_recovers_hyrec_bit_identical:
    bg.beta=0, bg.sigma²=0 → x_e, T_m identical to baseline
- test_pure_tilt_corrects_n_e_only:
    β=0.05, σ²=0 → n_e changes, T_m unchanged
- test_pure_shear_corrects_T_m_only:
    β=0, σ²/H²=1e-5 → T_m changes by ≈ -(1/3)·1e-5, n_e unchanged
- test_warning_at_large_shear:
    σ²/H²=1e-2 → assert UserWarning raised
```

### 5.3 Adversarial audit (PR-A3)

```
A2: linearization is named (linear_in_sinh_beta_squared etc) and only fires when
    metadata.shear_correction_status is set; not silently default
A3: HyRec table is an immutable input; correction returns a new object
A5: both tilt and shear corrections are gated by independent flags so neither can
    be silently dropped. tilt_freeze=True must drop ONLY the tilt correction,
    keeping shear active (and vice versa)
```

## 6. Reionization extension (retarded directional photon-budget)

Implementation: the retarded directional integral from `reionization_design.md §10`. Round-16 implements the **scalar** budget reduction (FLRW-equivalent) with metadata flag for the directional version (Round-17).

```
Σ_m w_m Σ_b ∫ ds Φ_{bm}(x^{ret}) e^{-τ_{bm}}  ≥  n_H ΔV [1 - x_{HII} + N_rec^eff]
```

For Round-16, we use the standard tanh ionization history (`x_HII(z) = (1/2)(1 + tanh((z_re - z)/Δz))`) with `(z_re, Δz) = (7.7, 0.5)` Planck 2018 default; the directional anisotropic-reionization upgrade is metadata-flagged but not yet integrated into the LoS layer.

### 6.1 Skeleton

```python
# bass/recombination/reionization.py  (existing; add anisotropic placeholder)
def reionization_history(
    z_grid: np.ndarray,
    *,
    z_re: float = 7.7,
    delta_z: float = 0.5,
    direction_dependent: bool = False,    # if True, raise NotImplementedError
) -> ReionizationHistory:
    if direction_dependent:
        raise NotImplementedError(
            "Anisotropic reionization deferred to Round-17 per "
            "V5_ROUND16_00 §9."
        )
    x_HII = 0.5 * (1.0 + np.tanh((z_re - z_grid) / delta_z))
    return ReionizationHistory(
        z=z_grid, x_HII=x_HII,
        anisotropy_status="homogeneous_tanh_only",
        anisotropy_block_reason="anisotropic_reionization_deferred_to_round17",
    )
```

### 6.2 Tests

```
test_reionization_homogeneous_tanh.py
- test_tanh_recovers_x_HII_at_z_re_equals_half: x_HII(z=z_re) ≈ 0.5
- test_direction_dependent_raises_until_round17
```

## 7. End-of-layer adversarial audit (cross-cuts §3, §4, §5, §6)

Before any PR-S1 / PR-S2 closes, run the following composite probe set:

```
P1. Background ODE state size check
   For each family, assert state_dim(family) matches background_state_dim(family).
   Common bug: 5-component shear silently truncated to 2-component (σ_+, σ_-) for
   non-Type-I; this would miss off-diagonal shear injection.

P2. β evolution fingerprint
   Run a 20% off-FLRW Type V simulation to z=10. Assert:
     - β(z=10) / β_initial = e^{-(1-3·c_s²_avg)·ΔN} within 1e-3
     - σ²/H² at z=10 < σ²/H² at z=z_init (shear must dilute as a^{-6} in BI/V)

P3. Codazzi residual scaling
   Run with rtol = {1e-6, 1e-8, 1e-10}. Assert ||C_C^A||/H² scales as O(rtol²).
   Common bug: ad-hoc clamping making residual independent of tolerance.

P4. Recombination invariance
   Run with shear=tilt=0; assert recombination output bit-identical to HyRec fixture.
   (Critical for FLRW closure.)

P5. Map-domain visibility shape
   At z_*, plot g̃(z_*, ê) for an injected dipole (β=0.05). Assert directional
   morphology is dipole, not monopole-shifted (catches the wrong sign).

P6. Tilt + Shear independence
   Set tilt_freeze=True; assert background ODE evolves σ identical to a
   tilt-active run with β=0. Catches wrong-default coupling between flags.

P7. Cosmological-range stability
   Re-run 130s benchmark from CLAUDE.md §3 Blocker-2: η = 261 → 14147 Mpc.
   Wall-time within 50% of baseline; output identical to ≤ 1e-12.
```

Findings from this probe set go into the PR description under "Adversarial Audit", as required by 00 §4.

## 8. Code-port helpers (Rust → Python)

Subsystems implemented in Rust (`sync_gauge_camb.rs`) that already do FLRW background; for porting their Bianchi extension to Python:

- `BianchiBackground::evolve` ↔ `bass/background/codazzi_tilt_rhs.py::background_rhs_codazzi_tilt`
- `apply_codazzi_projection` ↔ `bass/background/constraints.py::project_shear_to_codazzi`
- `tilted_thomson_rate` ↔ `bass/transport/tilted_visibility_evolved.py::build_tilted_visibility_history`

The Python implementation must produce the **same numerical output** as the Rust reference at any (rtol, atol) where both are converged, to within 1e-10. Cross-checks live in `htt/bass/validation/test_rust_python_background_parity.py` (new file in PR-S1).

---

**End of Physics Layer.** Continue to `V5_ROUND16_02_SOLVER_LAYER.md`.
