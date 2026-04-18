# LB-5 — Unified Background + Hierarchy Integrator Specification

**Session LB-5**. Produces `bass/hierarchy/integrator.py` — a `scipy.integrate.solve_ivp` driver that simultaneously evolves the background, species densities, tetrad state, and the full PSTF multipole tower (temperature + E-mode) on a single η-grid.

**Prerequisites**:
- LB-0 through LB-4 complete and tested
- `bass.species.*` (LB-1) — species background objects
- `bass.hierarchy.pstf_tensor` (LB-2) — state container
- `bass.hierarchy.hierarchy_rhs` (LB-2) — RHS computation
- `bass.hierarchy.closure` (LB-3) — truncation/closure strategies
- `bass.collision.thomson_pstf` (LB-4) — collision source
- `bass.background.tetrad_state` (Y-Block) — σ_ab(η), ω_ab(η)
- `bass.background.einstein_bianchi` — FLRW-limit background ODE

**Size estimate**: ~500 LoC implementation + ~400 LoC tests.

**Reference material**:

- **Ellis §6.1–6.3** — conservation laws and integrability
- **Ellis §18.5** — integration strategy for Bianchi tetrad
- **Lecture notes §2.3–2.4** — Friedmann integration, density-ratio evolution
- **Ma-Bertschinger 1995 §8** — numerical integration strategies for the FLRW Boltzmann system
- **Hamilton 2001** (CAMB) — operator-splitting and stiffness in CMB codes
- **Press-Teukolsky** *Numerical Recipes* Ch 17 — stiff ODE solvers

---

## Table of contents

1. Global architecture
2. State vector packing
3. Right-hand side assembly
4. Stiffness and solver selection
5. η-grid construction
6. Initial conditions
7. Step-size control and event detection
8. Diagnostics and invariants
9. Data contracts
10. Test criteria
11. Implementation checklist
12. Cite map

---

## 1. Global architecture

LB-5 is the **single driver** that ties everything together. The combined system is:

```
Combined state vector Y(η):

    [ a(η),                                  # background scale factor — 1 element
      Σ_+(η), Σ_-(η),                        # tetrad shear amplitudes — 2 elements
      Π_0(η), Π_1(η), ..., Π_L(η),           # photon temperature tower — sum(2ℓ+1)
      E_2(η), E_3(η), ..., E_L(η),           # photon E-mode tower — sum(2ℓ+1)_{ℓ≥2}
      ν_0(η), ν_1(η), ..., ν_L(η),           # (optional) neutrino tower
    ]
```

At LB-5 scope, we default to:
- **Orthogonal Bianchi I** — simplest case where all physics is exercised
- **L = 6** — baseline truncation from LB-3
- **Photon + E-mode evolved dynamically**; neutrino tower in a reduced fluid approximation (Δ_ν, q_ν, π_ν, G_3 — 4 scalars — matching lowell §9.3 "low-ℓ retained set"). Full neutrino tower is LB-5b.

Species backgrounds (γ, ν, b, c, Λ) from LB-1 are **not integrated** — they are analytic or spline-evaluated. Only the *hierarchy* and *kinematic* variables are integrated.

### 1.1 Total state size

For default L=6:
- Background: 3 elements (a, Σ_+, Σ_-)
- Photon temperature: 1 + 3 + 5 + 7 + 9 + 11 + 13 = 49 elements
- Photon E-mode (ℓ ≥ 2): 5 + 7 + 9 + 11 + 13 = 45 elements
- Neutrino reduced: 4 scalars

Total: 3 + 49 + 45 + 4 = **101 elements per k-mode**. At LB-5 we integrate only k = 0 (background-only — no Fourier-mode dependence). LB-6 may extend to a k-grid.

### 1.2 Design principle — flat-state integration

All state packed into one flat ndarray. Packing/unpacking utilities:

```python
def pack_combined_state(a, Sigma_pm, Pi, E, nu_reduced, L) -> np.ndarray: ...
def unpack_combined_state(y, L) -> CombinedState: ...

@dataclass
class CombinedState:
    a: float
    Sigma_plus: float
    Sigma_minus: float
    photon_T: PSTFHierarchyState       # ℓ = 0..L
    photon_E: PSTFHierarchyState       # ℓ = 2..L; packed with zeros at ℓ=0,1
    neutrino_reduced: NeutrinoReduced  # 4 scalars
```

---

## 2. State vector packing

### 2.1 Packing order — FIXED

```
Index range         Variable
────────────────────────────────────────────
0                   a(η)
1                   Σ_+(η)
2                   Σ_−(η)
3                   Π_0 (photon monopole)
4..6                Π_1 (photon dipole, 3 components)
7..11               Π_2 (photon quadrupole, 5 components)
12..18              Π_3 (photon ℓ=3, 7 components)
19..27              Π_4 (photon ℓ=4, 9 components)
28..38              Π_5 (photon ℓ=5, 11 components)
39..51              Π_6 (photon ℓ=6, 13 components)
52..56              E_2 (5 components)
57..63              E_3 (7 components)
64..72              E_4 (9 components)
73..83              E_5 (11 components)
84..96              E_6 (13 components)
97                  Δ_ν (neutrino density contrast)
98                  q_ν (neutrino heat flux magnitude)
99                  π_ν (neutrino anisotropic stress magnitude)
100                 G_3 (neutrino next moment)
```

Fixed index table is a constant in `bass/hierarchy/integrator.py`. Deviating from this layout in the future requires updating all pack/unpack utilities *and* all regression tests.

### 2.2 Sub-structure accessors

```python
def slice_a(L: int) -> slice:           return slice(0, 1)
def slice_sigma_pm(L: int) -> slice:    return slice(1, 3)
def slice_photon_T(L: int) -> slice:    return slice(3, 3 + sum_components(L))
def slice_photon_E(L: int) -> slice:
    start = 3 + sum_components(L)
    return slice(start, start + sum_components_ge2(L))
def slice_neutrino_reduced(L: int) -> slice:
    start = 3 + sum_components(L) + sum_components_ge2(L)
    return slice(start, start + 4)
```

---

## 3. Right-hand side assembly

The RHS function given to `solve_ivp`:

```python
def combined_rhs(
    eta: float,
    y: np.ndarray,
    *,
    L: int,
    bg_config: BianchiCosmology,
    species: SpeciesBackgroundRegistry,
    tetrad_state: TetradBackgroundState,
    closure: ClosureStrategy,
    collision: CollisionOperator,
    aux_state: IntegratorAuxState,
) -> np.ndarray:
    """Combined RHS for background + photon T + photon E + neutrino reduced.

    aux_state holds cached intermediate values (splines, etc.) that
    don't need recomputation at every step.
    """
    state = unpack_combined_state(y, L)

    # (1) Background: reuse solve_bianchi_background's RHS form
    a_rhs, Sigma_pm_rhs = background_rhs(eta, state.a, state.Sigma_plus,
                                           state.Sigma_minus, bg_config)

    # (2) Photon temperature hierarchy
    photon_T_rhs = hierarchy_rhs_photon(
        eta, state.photon_T.as_flat(), L,
        bg_table=aux_state.bg_table, tetrad_state=tetrad_state,
        Gamma_T_of_eta=aux_state.Gamma_T_spline,
        v_b_dipole_of_eta=aux_state.v_b_dipole_of_eta,
        closure=closure,
        collision=collision,
    )

    # (3) Photon E-mode hierarchy — similar call with E-only source
    photon_E_rhs = hierarchy_rhs_polarization(
        eta, state.photon_E.as_flat(), L,
        bg_table=aux_state.bg_table, tetrad_state=tetrad_state,
        Gamma_T_of_eta=aux_state.Gamma_T_spline,
        Pi_2_for_source=state.photon_T.tensors[2],
        closure=closure,
        collision=collision,
    )

    # (4) Neutrino reduced (4 scalars)
    nu_rhs = neutrino_reduced_rhs(
        eta, state.neutrino_reduced,
        bg_table=aux_state.bg_table, tetrad_state=tetrad_state,
    )

    return pack_combined_state(
        a=a_rhs,
        Sigma_pm=Sigma_pm_rhs,
        Pi=unpack_pstf(photon_T_rhs, L),
        E=unpack_pstf(photon_E_rhs, L),
        nu_reduced=nu_rhs,
        L=L,
    )
```

### 3.1 Auxiliary state

```python
@dataclass
class IntegratorAuxState:
    """Precomputed quantities shared across all RHS evaluations."""
    bg_table: FLRWBackgroundTable
    sigma_spline: Callable[[float], np.ndarray]    # σ_ab spline (3,3) at eta
    Gamma_T_spline: Callable[[float], float]        # τ̇(η) from recombination
    v_b_dipole_of_eta: Callable[[float], np.ndarray]  # (3,) v_b at eta
    # Added as needed
```

Building the aux state is an O(1) setup cost before the integration starts.

---

## 4. Stiffness and solver selection

### 4.1 Stiffness map

| Regime | η range | Stiffness source | Consequence |
|---|---|---|---|
| Early radiation (z > 10⁵) | η ≲ 50 Mpc | Γ_T ≫ H — tight coupling | Π_{ℓ≥3} damp fast; (Θ_2, E_2) near algebraic equilibrium |
| Around recombination (z ≈ 1100) | η ≈ 280 Mpc | Γ_T / H → O(1) — transition | intermediate; TCA breaks down |
| Post-recombination (z ≲ 1000) | η > 300 Mpc | Γ_T → 0 — free-streaming | hierarchy decouples; E-mode mostly frozen |
| Late (z < 1) | η ≈ 14000 Mpc | Reionization bump in Γ_T | small polter boost |

### 4.2 Solver choice

Use `scipy.integrate.solve_ivp` with method `LSODA`:

- Automatic switching between Adams (non-stiff) and BDF (stiff)
- Handles the full η range in one call
- Accepts `max_step` to prevent missing the recombination transition

Fallback: if LSODA fails at some step, catch the failure and retry with explicit `BDF` method + tighter tolerances.

### 4.3 Tolerances

```python
solve_ivp(
    combined_rhs,
    (eta_initial, eta_today),
    y0,
    t_eval=eta_output_grid,
    method='LSODA',
    rtol=1e-6,          # adequate for Kolb-table matching
    atol=1e-12,         # catches tiny ρ_Λ + tiny Π components
    max_step=(eta_today - eta_initial) / 1000,
    args=(L, bg_config, species, tetrad_state, closure, collision, aux_state),
)
```

**Rationale for rtol=1e-6**: LB-5 targets 1% accuracy on z_eq / z_*; rtol=1e-6 is 10⁴× safer. Tighter tolerances are allowed at the cost of runtime.

---

## 5. η-grid construction

### 5.1 Initial and final times

- **η_initial**: earliest time on the HyRec table, corresponding to z_max ≈ 8017. Concretely: use `solve_bianchi_background(a_start=1e-4, ...)` to get η(z=10000) ≈ **0.5 Mpc**.
- **η_today**: η(a=1) ≈ **14153 Mpc** (matches CAMB reference).

### 5.2 Output grid

Output at `n_eta = 2000` points, log-spaced in η (captures rapid recombination transition):

```python
eta_out = np.geomspace(eta_initial, eta_today, n_eta)
```

Alternative: linear in ln(a) — equivalent for power-law background.

### 5.3 Critical-η detection

Key transitions that should appear as interior points:

| Transition | η [Mpc] | z | What's happening |
|---|---|---|---|
| Matter-radiation equality | ~100 | 3400 | Ω_m / Ω_r crosses 1 |
| Last scattering | ~280 | 1090 | Γ_T / H drops through 1 |
| Reionization onset | ~13800 | 8 | x_e rises again |
| Today | 14153 | 0 | a = 1 |

Event functions:

```python
def event_recombination(eta, y, *args):
    """Trigger at z = z_* ≈ 1089.94 for verification."""
    z = 1.0 / y[0] - 1.0
    return z - 1089.94

event_recombination.terminal = False
```

LB-5's integrator doesn't terminate at these events — it logs them and makes them available in the output. Events can be added as needed in LB-6 tests.

---

## 6. Initial conditions

Initial conditions at `η_initial` (deep in radiation era):

| Variable | IC value | Source |
|---|---|---|
| a | 1 / (1 + z_max) ≈ 1e-4 | scale factor at start |
| Σ_+ | 0 (Bianchi I orthogonal baseline) or user-supplied (e.g. √(6 × Σ²_init)) | configurable |
| Σ_- | 0 | configurable |
| Π_0 | 0 | purely background in LB-5 (no super-horizon seed yet) |
| Π_ℓ (ℓ ≥ 1) | 0 | |
| E_ℓ | 0 | |
| ν_{Δ, q, π, G_3} | 0 | |

**All zero by default**. A non-zero Σ_+ triggers the shear-injection T9 term in the hierarchy, which then drives Π_2 through the collision source (damped or TCA'd depending on Γ_T).

LB-6 will add **CAMB-regular-adiabatic seeds** for the perturbation sector (lowell §13.2 eq for `η_cov`, `Δ_γ`, `q_γ`, ...). LB-5 ships with **zero IC** as the baseline; non-zero IC is a configuration option.

---

## 7. Step-size control and event detection

### 7.1 Default behaviour

LSODA handles step-size automatically. Three safeguards:

1. **max_step** bounded to 1/1000 of the total integration span — prevents overshooting recombination
2. **rtol = 1e-6, atol = 1e-12** — tight enough to capture the recombination transition cleanly
3. **max_nstep = 5000** (via LSODA backend) — prevents runaway

### 7.2 Manual critical-η specification

Optionally, the user can supply `critical_eta_list`:

```python
integrator.run(
    ...,
    critical_eta_list=[eta_eq, eta_rec, eta_reion_start, eta_today],
)
```

LSODA will then visit each of these points exactly, which helps resolve rapid transitions.

### 7.3 Failure diagnostics

If `solve_ivp` fails, the failure point is logged with:
- η at failure
- Current state vector
- Estimated required step size
- Stiffness ratio (if available)

This diagnostic output is essential for debugging LB-5 during LB-6 tests.

---

## 8. Diagnostics and invariants

After integration, the following invariants are **checked at every output grid point** in post-processing:

| Invariant | Expression | Expected | Tolerance |
|---|---|---|---|
| Friedmann constraint | 𝓗² − (8πG a² / 3) ρ_total − a² × (curvature) | 0 | 1e-6 rel |
| Species sum rule | Σ Ω_s(a) × (scaling factor) − 1 | 0 | 1e-5 |
| Shear decay | For Bianchi I flat, Σ²(a) × a⁴ = const | constant | 1% |
| Continuity per species | ρ̇_s + Θ(1+w_s) ρ_s | 0 | 1e-10 rel |
| PSTF invariants | `verify_pstf_invariants(tensors)` at every ℓ | passes | — |
| No NaN/Inf | `np.all(np.isfinite(y_out))` | True | exact |

Any invariant violation aborts the integration with a named exception pointing to the responsible field.

---

## 9. Data contracts

### 9.1 Module file layout

```
bass_py/bass/hierarchy/
├── integrator.py                  — main driver (LB-5)
├── pack_unpack.py                 — state packing utilities
├── aux_state.py                   — IntegratorAuxState, factories
├── ic.py                          — initial condition constructors
├── event_detection.py             — critical-η event functions
├── neutrino_reduced.py            — 4-scalar neutrino fluid RHS
├── test_integrator.py
├── test_pack_unpack.py
├── test_ic.py
└── test_neutrino_reduced.py
```

### 9.2 Public API

```python
from bass.hierarchy.integrator import (
    LowellBianchiIntegrator,
    IntegrationResult,
    IntegratorConfig,
)

@dataclass
class IntegratorConfig:
    """Configuration for one LB-5 integration."""
    L_max: int = 6
    eta_initial_mpc: float = 0.5
    eta_final_mpc: float = 14200.0
    n_output: int = 2000
    rtol: float = 1e-6
    atol: float = 1e-12
    bianchi_cosmo: BianchiCosmology = field(default_factory=flrw_cosmology)
    Sigma_plus_initial: float = 0.0
    Sigma_minus_initial: float = 0.0
    include_neutrino_hierarchy: bool = False  # False → reduced fluid
    closure_strategy: ClosureStrategy = field(default_factory=lambda: build_default_closure(L_max=6))
    collision_operator: CollisionOperator = field(default_factory=ThomsonPSTFCollisionOperator)


@dataclass
class IntegrationResult:
    """Full output of one LB-5 integration."""
    eta: np.ndarray                  # output grid
    a: np.ndarray
    Sigma_plus: np.ndarray
    Sigma_minus: np.ndarray
    photon_T_tower: np.ndarray       # shape (n_output, total_T_components)
    photon_E_tower: np.ndarray
    neutrino_reduced: np.ndarray
    invariant_residuals: dict[str, np.ndarray]  # {invariant_name: value_at_each_eta}
    critical_events: dict[str, float]  # {'z_eq': ..., 'z_star': ..., 'eta_reion': ...}
    config: IntegratorConfig
    solver_info: dict                # LSODA solver diagnostics


class LowellBianchiIntegrator:
    """Main driver: initialise, run, validate."""

    def __init__(self,
                 species: SpeciesBackgroundRegistry,
                 tetrad_state: TetradBackgroundState,
                 recombination: RecombinationInterp,
                 config: IntegratorConfig):
        ...

    def run(self) -> IntegrationResult:
        """Execute the integration.  Raises on invariant violation or
        LSODA failure."""
        ...

    def validate_invariants(self, result: IntegrationResult) -> dict:
        """Return per-invariant residual arrays.  Called internally
        at end of run; can be re-called externally for diagnostics."""
        ...
```

---

## 10. Test criteria

### 10.1 Pack/unpack tests (test_pack_unpack.py)

| # | Test | Target | Tol |
|---|---|---|---|
| I-01 | Round-trip: `unpack(pack(state))` == state | bit-identical | 1e-14 |
| I-02 | `pack(state)` has shape (total_size(L),) | total_size | exact |
| I-03 | Slice helpers give correct ranges for L ∈ {4, 6, 8} | — | exact |

### 10.2 IC tests (test_ic.py)

| # | Test | Target | Tol |
|---|---|---|---|
| I-04 | `zero_IC(L)` gives all zeros except a | a, zeros | exact |
| I-05 | `zero_IC` with Σ_plus_initial ≠ 0 sets Σ_+ correctly | Σ_+ | exact |
| I-06 | IC validators: negative a raises ValueError | — | exact |

### 10.3 Integrator tests (test_integrator.py) — FLRW baseline

| # | Test | Target | Tol |
|---|---|---|---|
| I-07 | FLRW (Σ_+ = 0), zero IC: integration terminates successfully, all Π_ℓ remain identically zero (no source → no evolution) | 0 | 1e-10 |
| I-08 | FLRW, zero IC: `a(η_today) ≈ 1.0`; `Σ_+ (η_today) = 0` | 1.0 | 1e-6 |
| I-09 | FLRW, zero IC: Friedmann invariant residual < 1e-6 at all output η | 0 | 1e-6 |
| I-10 | FLRW, zero IC: species sum rule at η_today: Σ Ω_s = 1.0 ± 1e-5 | 1.0 | 1e-5 |

### 10.4 Integrator tests — Bianchi I with shear

| # | Test | Target | Tol |
|---|---|---|---|
| I-11 | Bianchi I flat, Σ_+(0) = 1e-4 × H_0: Σ_+(η_today) matches analytic a⁻² decay | a⁻² × Σ_+(0) × (a(0)/a(η_today))² | 1% |
| I-12 | Bianchi I, Σ² × a⁴ = constant (shear-decay invariant) | constant | 1% |
| I-13 | Bianchi I, non-zero Σ_+: Π_2 develops at amplitude ~ Σ² × g_* (source strength) | order-of-magnitude match | 10% |
| I-14 | Bianchi I, Γ_T → ∞ regime (η < η_*): Π_ℓ≥3 / Π_2 < 0.01 (tight coupling works) | < 0.01 | 1% |

### 10.5 Recombination event detection

| # | Test | Target | Tol |
|---|---|---|---|
| I-15 | `critical_events['z_star']` in [1089, 1091] | 1089.94 | 1 |
| I-16 | `critical_events['z_eq']` in [3300, 3500] | 3400 | 50 |
| I-17 | `critical_events['eta_reion_midpoint']` in [13500, 13800] | τ_reion = 0.054 | 200 Mpc |

### 10.6 Integration with LB-4 TCA limit

| # | Test | Target | Tol |
|---|---|---|---|
| I-18 | At η where Γ_T / H > 100, Π_2 / (source_T / Γ_T) matches W6-04 algebraic form | bit-identical | 1e-4 |

Total: 18+ tests at LB-5.

---

## 11. Implementation checklist

- [ ] Review dependencies (LB-1..LB-4 green)
- [ ] Implement `bass/hierarchy/pack_unpack.py` — state vector pack/unpack utilities; tests I-01 to I-03
- [ ] Implement `bass/hierarchy/aux_state.py` — `IntegratorAuxState` + factories
- [ ] Implement `bass/hierarchy/ic.py` — `zero_IC`, validators; tests I-04 to I-06
- [ ] Implement `bass/hierarchy/neutrino_reduced.py` — 4-scalar ν fluid RHS (deferred to LB-5b if too large)
- [ ] Implement `bass/hierarchy/event_detection.py` — critical-η event functions
- [ ] Implement `bass/hierarchy/integrator.py` `LowellBianchiIntegrator` driver
  - Assemble combined RHS
  - Run `solve_ivp` with LSODA
  - Post-process: verify invariants, extract critical events, return `IntegrationResult`
- [ ] Tests I-07 to I-18
- [ ] Full bass_py regression
- [ ] Commit as `LB-5: unified background + hierarchy integrator (LCDM + Bianchi I)`

---

## 12. Cite map

| Component | Citations |
|---|---|
| `combined_rhs` | Ellis §6.1 (conservation laws); Ma-Bertschinger 1995 §8 (FLRW Boltzmann integration) |
| `background_rhs` | `bass.background.einstein_bianchi.solve_bianchi_background`; Ellis §18.3 |
| `hierarchy_rhs_photon` | LB-2 `02_multipole_hierarchy_spec.md` |
| `hierarchy_rhs_polarization` | LB-2 + LB-4 |
| `neutrino_reduced_rhs` | Ma-Bertschinger 1995 eq (49); lowell §9.3 |
| LSODA stiffness choice | Hindmarsh 1983 (ODEPACK); NumRec Ch 17 |
| `rtol=1e-6, atol=1e-12` | Hamilton 2001 (CAMB tolerance defaults) |
| Friedmann invariant check | Ellis §6.2 |

---

## 13. LB-5 extensions

- **LB-5b — full neutrino hierarchy** (~300 LoC): replace reduced 4-scalar form with full ν PSTF tower up to L (matching photon)
- **LB-5c — k-dependence**: add plane-wave mode k via direction-dependent advection; needed for perturbation work but not for pure background tests
- **LB-5d — adaptive η-grid**: re-sample output near recombination for publication figures (post-LB-6 optimisation)

---

## 14. What LB-5 does NOT do

- **Does not produce C_ℓ**: line-of-sight projection is post-LB-6
- **Does not solve k-dependent perturbations**: LB-5 is background-only (k = 0 effectively; all spatial gradients ∇̃ vanish for BI orthogonal)
- **Does not handle tilted species**: LB-2b/LB-4b extensions required first
- **Does not handle Types VI_h, VIII, IX**: requires full `∇̃` structure-constant dispatch (deferred)
- **Does not auto-tune truncation L**: L is fixed at construction
