# V5 Round-16 — Numerics & Runtime (IMEX-ARK4, Sparse Layout, Fairness, Code-Port)
_Authority: this doc + 00. Status: implementation-ready._

This document specifies the numerical-architecture layer: IMEX-ARK4 mainline integrator, frozen non-identity mass-matrix, sparse layout, adaptive controller, fairness benchmarks, profiling harness, and the Rust↔Python code-port contract. Each section ends with skeleton, pseudocode, tests, and adversarial audit.

## 1. IMEX-ARK4 mainline (closes G1 prerequisite)

The current production stepper is Rodas5P (3rd-order Rosenbrock-W); the audit identified that bit-identical D_2 closure on the Python side requires a higher-order, embedded-error stepper that handles the explicit free-streaming + implicit Thomson collision split *natively* without composition tricks. Round-16 adopts **Kennedy-Carpenter ARK4(3)6L[2]SA** as the mainline integrator for Phase 2+ (per `IMEX_DECISION_2026-04-18.md §6`). Rodas5P remains as a fallback for legacy benchmarks only.

### 1.1 Tableau

ARK4(3)6L[2]SA is a 6-stage diagonally-implicit / explicit pair, formally 4th-order with embedded 3rd-order estimator. The tableau is fixed (Kennedy-Carpenter 2001, Table 8):

```
Implicit (DIRK) Butcher tableau:
   c_i      a^I_{ij}                                                     b^I_i  b̂^I_i
   ────────────────────────────────────────────────────────────────────────────────────
   0        0                                                            0      0
   1/2      1/4    1/4                                                   ...    ...
   83/250   ...    ...    1/4                                             
   31/50    ...    ...    ...    1/4                                      
   17/20    ...    ...    ...    ...    1/4                               
   1        ...    ...    ...    ...    ...    1/4                       

Explicit pair (a^E_{ij}, b^E_i, b̂^E_i): same c_i, lower-triangular, no diagonal.
```

Full coefficients are in `bass/integration/ark4_tableau.py` (NEW; copy-paste from Kennedy-Carpenter 2001 Table 8).

### 1.2 Split structure

```
M(η) U' = f^E(η, U) + f^I(η, U)

f^E(η, U) =
    free_streaming(U, k_eff)               # T1 + k-recursion (T2, T3)
  + mode_mixing(U, A_mix)                   # T7, T8, T9 (off-diagonal shear)
  + curvature(U, A_curv)                    # S_AB-induced corrections
  + EB_mixing(U_E, U_B, sigma_2M)           # parity-odd cross-coupling
  + metric_source(η, U)                     # T6: -Φ̇, +(k/3)Ψ
  + baryon_doppler_from_v_b(U)              # baryon-photon momentum exchange (explicit part)

f^I(η, U) =
    thomson_collision(U, Gamma_T)           # K block: -Γ_T (Π - (1/10)Π_2 δ_{l2})
  + tca_relaxation(U, Gamma_T, H, threshold) # DAE-relaxation when active
```

### 1.3 Mass matrix

The mass matrix M is **non-identity** in general: the mode-coupling kernels in Type V/IX (and in Class-B for h ≠ 0) introduce off-diagonal mixing between the storage-ordered state slots. The rule:

```
M(η) is assembled at step start; it is BLOCK-DIAGONAL per (sector, ℓ),
with off-block coupling only via A_mix (which lives on the RHS, not M).
For sectors where the family kernel pack declares mass = δ (FLRW + Type I),
M is identity. For all other families, M is computed from
backend.assemble_mass_matrix(bg, truncation).
```

This **is not** simplified to `M = I` even when sparse; doing so is detected by adversarial audit P5 below.

### 1.4 Skeleton

```python
# bass/integration/imex_ark4.py  (NEW; closes G1 prerequisite)
import numpy as np
import scipy.sparse as sp
from bass.integration.ark4_tableau import ARK4_TABLEAU

class IMEXARK4Integrator:
    """
    Kennedy-Carpenter ARK4(3)6L[2]SA additive Runge-Kutta with embedded 3rd-order
    error estimator, supporting non-identity mass matrix M(η).
    """
    
    def __init__(self, *, mass_matrix_fn, f_explicit, f_implicit, jac_implicit,
                 rtol=1e-8, atol=1e-12, max_step=None):
        self.mass_matrix_fn = mass_matrix_fn
        self.f_explicit = f_explicit
        self.f_implicit = f_implicit
        self.jac_implicit = jac_implicit
        self.rtol = rtol
        self.atol = atol
        self.max_step = max_step or np.inf
        self._tableau = ARK4_TABLEAU
    
    def step(self, eta, U, h):
        """One ARK4 step from η to η+h. Returns (U_new, error_estimate)."""
        s = self._tableau.num_stages
        K_E = np.zeros((s, U.size))
        K_I = np.zeros((s, U.size))
        
        for i in range(s):
            U_stage = U.copy()
            for j in range(i):
                U_stage += h * (self._tableau.a_E[i, j] * K_E[j]
                              + self._tableau.a_I[i, j] * K_I[j])
            
            # Implicit solve at stage i
            if self._tableau.a_I[i, i] > 0:
                M = self.mass_matrix_fn(eta + self._tableau.c[i] * h)
                rhs = M @ U_stage
                U_stage = self._implicit_solve(
                    eta + self._tableau.c[i] * h,
                    rhs / (1 + h * self._tableau.a_I[i, i]),
                    h * self._tableau.a_I[i, i],
                )
            
            K_E[i] = self.f_explicit(eta + self._tableau.c[i] * h, U_stage)
            K_I[i] = self.f_implicit(eta + self._tableau.c[i] * h, U_stage)
        
        # Combine stages → high- and low-order solutions
        U_high = U + h * sum(self._tableau.b_E[i] * K_E[i] + self._tableau.b_I[i] * K_I[i]
                              for i in range(s))
        U_low = U + h * sum(self._tableau.bhat_E[i] * K_E[i] + self._tableau.bhat_I[i] * K_I[i]
                             for i in range(s))
        err = np.linalg.norm((U_high - U_low) / (self.atol + self.rtol * np.abs(U_high)))
        return U_high, err
    
    def _implicit_solve(self, eta, rhs, gamma_h):
        """Solve M U + γh f^I(U) = rhs via Newton (sparse)."""
        # Quasi-Newton: J = M + γh ∂f^I/∂U; reuse factorization across stages
        J = self.mass_matrix_fn(eta) + gamma_h * self.jac_implicit(eta)
        if sp.issparse(J):
            U_new = sp.linalg.spsolve(J.tocsc(), rhs)
        else:
            U_new = np.linalg.solve(J, rhs)
        return U_new
    
    def integrate(self, eta_grid, U0):
        """Adaptive march from U0 over eta_grid; returns full history."""
        U = U0.copy()
        history = [U.copy()]
        eta = eta_grid[0]
        h = (eta_grid[1] - eta_grid[0]) * 0.5  # initial guess
        for eta_target in eta_grid[1:]:
            while eta < eta_target:
                h_try = min(h, eta_target - eta, self.max_step)
                U_new, err = self.step(eta, U, h_try)
                if err <= 1.0:
                    eta += h_try
                    U = U_new
                    h = h_try * min(5.0, 0.9 * (1.0 / max(err, 1e-12)) ** (1/4))
                else:
                    h = h_try * max(0.1, 0.9 * (1.0 / err) ** (1/4))
            history.append(U.copy())
        return np.array(history)
```

### 1.5 Tests + tolerances

```
test_imex_ark4_integrator.py
- test_prothero_robinson_4th_order:
    Solve ε y' = -y + cos(η), ε ∈ {1, 1e-3, 1e-6}; assert ≤ 1e-12 vs analytic
- test_constant_step_recovers_4th_order: rtol → 0 → ||U_h - U_{h/2}|| ~ h^4
- test_adaptive_step_recovers_3rd_order_in_error: error decays as h^3
- test_mass_matrix_identity_short_circuit:
    M = I → spsolve(I + γhJ, ·) skipped where possible
- test_non_identity_mass_matrix_used:
    M ≠ I → assert sp.linalg.spsolve called

test_imex_ark4_pipeline_parity.py
- test_ark4_matches_rodas5p_to_1e-10_for_FLRW:
    Full FLRW pipeline with both integrators; D_2(ARK4) - D_2(Rodas5P) ≤ 1e-10 μK²
- test_ark4_matches_rodas5p_for_typeI_orthogonal: same
- test_ark4_diverges_from_rodas5p_when_anisotropic:
    For Type V σ=0.01: |D_2(ARK4) - D_2(Rodas5P)| ≥ 1e-4 (different stages =
    different truncation; this is expected and documented)
```

### 1.6 Adversarial audit (PR-S2)

```
A1: grep for "scipy.integrate.solve_ivp" in production hierarchy paths:
    only in Rodas5P fallback; main authority is IMEX-ARK4
A2: verify the ARK4 tableau coefficients match Kennedy-Carpenter 2001 Table 8
    bit-for-bit (compare against constants in ark4_tableau.py)
A3: mass matrix is computed from a real assembler, not hard-coded identity
A5: verify the implicit block carries Thomson + TCA-relaxation (not just Thomson)
A6: for Type V/IX: assert mass_matrix_fn returns non-identity sparse matrix
A7: convergence sweep: rtol ∈ {1e-4, 1e-6, 1e-8, 1e-10};
    D_2 final converges as O(rtol²) (4th-order embedded estimator)
A9: parallel-vs-sequential: bit-identity holds at rtol = atol = 0 (re-run
    test_optimization_fairness on ARK4 path)
```

## 2. State layout and sparse blocks (frozen)

The state is laid out in this canonical block order (matches v5 §02A §1.2):

```
U.flat = [
    # Sector 1: photon T tower (explicit-block)
    Θ_{ℓ=0..L_T, m=-2..+2}                  # 5*(L_T+1) slots
    
    # Sector 2: photon E tower (explicit-block)
    E_{ℓ=2..L_E, m=-2..+2}                  # 5*(L_E-1) slots
    
    # Sector 3: photon B tower (explicit-block)
    B_{ℓ=2..L_B, m=-2..+2}                  # 5*(L_B-1) slots
    
    # Sector 4: massless neutrino tower
    N_{ℓ=0..L_ν, m=-2..+2}                  # 5*(L_ν+1) slots
    
    # Sector 5: massive neutrino momentum hierarchy (per-q slice)
    F^q_{ℓ=0..L_νm, m=-2..+2} for each q in q_grid  # n_q*5*(L_νm+1) slots
    
    # Sector 6: baryon
    δ_b, v_b_{m=-2..+2}                      # 6 slots
    
    # Sector 7: CDM
    δ_c, v_c_{m=-2..+2}                      # 6 slots
    
    # Sector 8: TCA microblock auxiliaries (only when TCA active)
    π_γ_qs, slip                             # 2 slots, conditional
]
```

The total is 5*(L_T+1) + 5*(L_E-1) + 5*(L_B-1) + 5*(L_ν+1) + n_q*5*(L_νm+1) + 6 + 6 (+ 2 if TCA on). Default `(L_T, L_E, L_B, L_ν, L_νm, n_q) = (12, 8, 8, 12, 4, 50)` → 65 + 35 + 35 + 65 + 1250 + 6 + 6 = **1462** slots per (k, family).

### 2.1 Sparse-matrix budget

The integrator's per-step linear system has 1462² ≈ 2.1×10⁶ entries dense; the block sparsity pattern reduces this by a factor of ~50, yielding ~4×10⁴ non-zeros. `scipy.sparse.csc_matrix` is the storage; `splu` for LU factorization (re-used across ARK4 stages).

### 2.2 Skeleton for canonical layout indexing

```python
# bass/hierarchy/state_layout.py  (NEW; replaces partial pack_unpack.py)
@dataclass(frozen=True)
class StateLayout:
    L_T: int
    L_E: int
    L_B: int
    L_nu: int
    L_nu_massive: int
    n_q_massive: int
    tca_active: bool = False
    
    @property
    def total_size(self) -> int:
        s = 5 * (self.L_T + 1) + 5 * (self.L_E - 1) + 5 * (self.L_B - 1) \
            + 5 * (self.L_nu + 1) \
            + self.n_q_massive * 5 * (self.L_nu_massive + 1) \
            + 6 + 6
        if self.tca_active:
            s += 2
        return s
    
    def slot(self, sector: str, ell: int, m: int, q: int | None = None) -> int:
        offset = self._sector_offset(sector)
        if sector in ("photon_T", "photon_E", "photon_B", "neutrino"):
            ell_min = self._ell_min(sector)
            return offset + 5 * (ell - ell_min) + (m + 2)
        elif sector == "neutrino_massive":
            return offset + q * 5 * (self.L_nu_massive + 1) + 5 * ell + (m + 2)
        elif sector == "baryon":
            return offset + (0 if (ell, m) == (0, 0) else 1 + (m + 2))
        # ... etc ...
```

### 2.3 Tests

```
test_state_layout.py
- test_total_size_matches_sum_of_sector_sizes
- test_slot_indices_unique: hash all (sector, ell, m, q) combos → unique
- test_round_trip_pack_unpack: random state → pack → unpack → identical
```

## 3. Adaptive step controller

The integrator uses a **multi-scale safety controller**: at each step, four independent timescales are estimated, and the next step `h` is bounded by their minimum.

```
h_next = min(
    c_H · |H|^{-1},                      # Hubble; c_H = 0.1
    c_σ · |σ|^{-1},                       # shear; c_σ = 0.1
    c_T · |Γ_T|^{-1},                     # Thomson; c_T = 0.05 (allows TCA-active step ≪ τ_c)
    c_geo · |M_geo|^{-1},                 # geometric mode-coupling rate; c_geo = 0.1
    c_step · h_prev · (rtol/err)^{1/4},   # error control (4th-order ARK)
    h_max,                                # absolute cap
)
```

Defaults from `IMEX_DECISION §5`. The controller is in `bass/integration/adaptive_controller.py` (extends existing logic).

### 3.1 Skeleton

```python
# bass/integration/adaptive_controller.py
def safe_step_size(*, h_prev, error, eta, bg, gamma_T, max_step):
    """Multi-scale safe step."""
    H = bg.hubble_at(eta)
    sigma = bg.sigma_norm_at(eta)
    M_geo_norm = bg.geom_mode_coupling_norm_at(eta)
    
    h_H = 0.1 / max(H, 1e-30)
    h_sigma = 0.1 / max(sigma, 1e-30)
    h_T = 0.05 / max(gamma_T, 1e-30)
    h_geo = 0.1 / max(M_geo_norm, 1e-30)
    h_err = 0.9 * h_prev * min(5.0, max(0.1, (1.0 / max(error, 1e-12)) ** 0.25))
    
    return min(h_H, h_sigma, h_T, h_geo, h_err, max_step)
```

### 3.2 Adversarial audit

```
A2: verify all four physical timescales are sampled at every step (not cached
    longer than 1 step). Common bug: caching σ from 100 steps ago.
A5: verify when tilt_freeze=True, h_geo still uses M_geo (because shear can be
    anisotropic without tilt evolution). Bug class: tilting off → step opens up
    incorrectly.
```

## 4. Cosmological-range stability (closes Round-15 Blocker-2; preserved into Round-16)

The Round-15 algebraic audit closed `λ_max(A_right) ≈ 1e-16` machine precision at γ_T=0 and γ_T=1; cosmological-range integration `η = 261 → 14147 Mpc` completes in 130 s. Round-16 must preserve this property.

### 4.1 Regression baseline

```
test_cosmological_range_stability_v16.py
- test_imex_ark4_eta_261_to_14147_completes_in_under_180s:
    Allow 50% wall-time overhead for new Round-16 features (mode-mixing, etc.)
- test_imex_ark4_lambda_max_machine_precision: re-run algebraic audit at γ_T ∈ {0, 1}
- test_no_negative_xe_after_recombination: x_e(η) > 0 for all η in output
```

## 5. Cutoff convergence (extends R15-AUDIT-PATCH P-12)

Round-16 promotes the `production_cutoff_gate` to a hard regression: `D_2(L_max)` must converge to 10⁻³ μK² across `L_max ∈ {6, 10, 20, 40}`. The current Round-15 patch added the test as `xfail` until PR-S13 closes D_2; Round-16 PR-S13 changes `xfail` → `xpass` and removes the marker.

## 6. Optimization fairness (extends R15-AUDIT-PATCH P-09)

Round-16 adds three new fairness axes:

(a) **IMEX-ARK4 vs Rodas5P** (FLRW limit only): ≤ 1e-10 bit-identity expected.
(b) **Sparse vs dense LU**: identical D_2 to ≤ 1e-12.
(c) **Cached vs uncached Wigner-3j table**: D_2 identical to 1e-15 (deterministic table).

```
test_optimization_fairness_v16.py
- test_ark4_vs_rodas5p_flrw_match
- test_sparse_vs_dense_lu_match
- test_wigner_table_cache_invariance
```

## 7. Profiling harness

The CLAUDE.md performance target is "10–15s single-run on low-spec; CAMB 5s / CLASS 7s reference". Round-16 keeps this target; the IMEX-ARK4 mainline + sparse layout should meet it.

```python
# scripts/profile_v16_full_run.py  (NEW)
import cProfile
import pstats
import io
from bass.spectrum.flrw_pipeline import compute_flrw_d_ell
# ... configure 64-k single-run ...
profiler = cProfile.Profile()
profiler.enable()
bundle = compute_flrw_d_ell(species, k_grid, pipeline_config=cfg, n_workers=8)
profiler.disable()
ps = pstats.Stats(profiler).sort_stats("cumulative")
ps.print_stats(40)
```

Targets (per `project_perf_targets.md`):
- Wall-time per single k: ≤ 1 s (after Round-16 IMEX-ARK4 + sparse).
- Total 64-k pipeline (8 workers): ≤ 15 s.

If targets are missed, profile the dominant function and:
1. If kernel assembly dominates → cache backends per family on first call.
2. If LU factorization dominates → reuse factorization across ARK4 stages.
3. If Bessel evaluation dominates → tabulate j_ℓ once at integrator init.
4. If Wigner-3j dominates → table is already cached at backend init.

### 7.1 Adversarial audit

```
A1: profiler output included in PR description; no "TODO: profile this"
A9 (fairness): no optimization that changes physics (cutoff truncation, etc.)
   is presented as "speedup". All wall-time numbers come with same-config
   D_2 verification.
```

## 8. Code-port contract (Rust ↔ Python)

The dual-track architecture (CLAUDE.md §1) requires that:
- **MB-95 production path** (`sync_gauge_camb.rs`, 7363 lines, Rodas5P) produces D_2 = 1002.086744 μK² as the *anchor*.
- **PSTF primary path** (Python, IMEX-ARK4) produces the **same** D_2 to bit-identity (PR-S13 closure).

### 8.1 Per-module port table

| Layer | Rust source | Python target | Status |
|-------|-------------|---------------|--------|
| Background | `sync_gauge_camb.rs::Background` | `bass/background/codazzi_tilt_rhs.py` | NEW (extends einstein_bianchi) |
| Recombination | `sync_gauge_camb.rs::Recfast`/`HyRec adapter` | `bass/recombination/{hyrec,fixtures}` | EXISTS (fixture) |
| Hierarchy | `sync_gauge_camb.rs::Hierarchy::rhs` | `bass/hierarchy/hierarchy_rhs_v16` | NEW (extends Round-15) |
| Mode mixing | (not in MB-95; Bianchi-only) | `bass/hierarchy/mode_mixing_blocks.py` | NEW |
| LoS / projector | `sync_gauge_camb.rs::LoS::project` | `bass/los/{flrw,bianchi}_propagator.py` | EXISTS (FLRW); NEW (Bianchi) |
| TCA | `sync_gauge_camb.rs::tca_compute` | `bass/closure/quadrupole_tca.py` + `bass/hierarchy/integrator.py` | EXISTS |
| IMEX-ARK4 | (not in Rust; Python uses Rodas5P) | `bass/integration/imex_ark4.py` | NEW |

### 8.2 Bit-identity contract (FLRW limit)

For PR-S13, the success criterion is:

```
|D_2^Python - D_2^Rust| / D_2^Rust < 1e-9   (effectively bit-identical at float64)
```

at the same parameters: Planck 2018 cosmology, L_max = 40, k_grid 200 points. The two paths use different ODE steppers (Rodas5P vs ARK4) and different memory layouts, but must produce identical observables to within numerical precision when both are converged. This is the fairness contract for the production switch in PR-S15.

### 8.3 Cross-validation harness

```python
# htt/bass/validation/test_rust_python_full_pipeline_parity.py  (NEW; PR-S13)
@pytest.mark.slow
def test_rust_python_d_l_full_pipeline_match():
    """Full pipeline parity: Rust MB-95 vs Python PSTF."""
    rust_anchors = load_rust_d_l_anchors()  # from sync_gauge_camb fixture
    python_d_l = compute_flrw_d_ell(species, k_grid, ...)
    np.testing.assert_allclose(
        python_d_l["d_tt"][2], rust_anchors["d_tt_2"],
        rtol=1e-9, atol=1e-9,
        err_msg="Python PSTF D_2 not bit-identical with Rust MB-95",
    )
```

The Round-15 patch already created this test as `xfail`; Round-16 PR-S13 closes it as `xpass` and removes the marker.

## 9. Runtime control plane

The `RuntimeControlBlock` (existing) gains new flags in Round-16:

```python
# bass/runtime/ver2_execution.py  (extend existing dataclass)
@dataclass(frozen=True)
class RuntimeControlBlock:
    # ... existing fields ...
    
    # ROUND-16 EXTENSIONS:
    integrator_family: Literal["rodas5p", "imex_ark4"] = "imex_ark4"   # default switch
    tilt_freeze: bool = False                  # default FALSE → β evolved
    codazzi_projection_cadence: Literal["ic_only", "every_step", "every_n_steps"] \
                                = "every_step"
    allow_template_card: bool = False           # propagated to ic_provenance_gate
    map_output_nside: int = 0                   # 0 = no maps; 64 default for production
    b_mode_projector: Literal["flrw_zero_only", "wigner_d_path_b"] \
                       = "wigner_d_path_b"      # default switch
    massive_neutrino_quadrature_nq: int = 50    # Lesgourgues-Tram default
    # ... validation ...
```

The `default` values represent the Round-16 production stance: ARK4 + evolved tilt + Codazzi-projected every step + Wigner-D B-mode + 50-bin massive ν.

For backward compatibility, existing tests that bypass the new defaults must explicitly set the flags. CI runs at the new defaults.

### 9.1 Adversarial audit

```
A4 (synthetic-vs-production): verify default values in RuntimeControlBlock
    are the production values (not "diagnostic" / "frozen" / "legacy")
A5: tilt_freeze=False is default; flipping to True must trigger metadata
    "tilt_evolution_status=frozen_diagnostic" — verify in test
A6 (template card): allow_template_card=False default; non-strong family fitting
    must raise without explicit flip
```

## 10. End-of-layer adversarial audit (cross-cutting)

```
P1. ARK4 mainline reachable
   In production runtime: integrator_family default == "imex_ark4"; Rodas5P only
   reachable via explicit override. Common bug: production silently runs Rodas5P
   because ARK4 was never wired through ver2_execution.

P2. Mass matrix never simplified to identity
   For Type V/IX/non-FLRW: assert M.shape == (1462, 1462) and
   sp.linalg.norm(M - sp.eye(1462)) > 1e-3.

P3. Adaptive controller multi-scale
   Run a step with σ = 0 (FLRW) then σ = 0.01 (small Bianchi); assert h_step
   for the second is strictly smaller. Catches σ-scale being silently ignored.

P4. Cosmological-range stability preserved
   Re-run η = 261 → 14147 in ≤ 180 s; D_2 final identical to ≤ 1e-12 vs
   pre-Round-16 baseline.

P5. ARK4 4th-order on Prothero-Robinson
   Fixed-step convergence at h ∈ {1e-2, 1e-3, 1e-4} → error scales as O(h^4).

P6. Cutoff convergence regression
   Re-run production_cutoff_gate at L_max ∈ {6, 10, 20, 40};
   |D_2(L_max=40) - D_2(L_max=20)| ≤ 5×10⁻⁴ μK²;
   |D_2(L_max=20) - D_2(L_max=10)| ≤ 1×10⁻³ μK²

P7. Optimization fairness
   ARK4 vs Rodas5P (FLRW); sparse vs dense LU; cached vs uncached Wigner-3j —
   all within 1e-10 of each other.

P8. Code-port parity
   Run bit-identity test against Rust MB-95 anchor; PR-S13 closure: ≤ 1e-9.

P9. Runtime control plane defaults are production
   New session: load RuntimeControlBlock() default; assert all five Round-16
   flags carry production values.

P10. Profile-target compliance
   Single-k FLRW run: ≤ 1 s wall-time (8 workers, 64 k);
   Full pipeline ≤ 15 s.
```

---

**End of Numerics & Runtime Layer.** Continue to `V5_ROUND16_05_SHIP_GATES_AND_ADVERSARIAL_AUDIT.md`.
