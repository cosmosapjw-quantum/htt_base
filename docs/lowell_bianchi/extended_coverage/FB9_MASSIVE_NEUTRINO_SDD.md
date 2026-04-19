# FB-9 SDD — Massive neutrino species

**Status**: draft, scope sealed 2026-04-20.
**Coordinator**: [EXTENDED_COVERAGE_PLAN_FB8_FB9_FB11.md §5 FB-9](EXTENDED_COVERAGE_PLAN_FB8_FB9_FB11.md).
**Parent plan decision**: D7 = (a) — included in FB scope.
**Audit contract**: [SELF_AUDIT_AUTOMATION.md](SELF_AUDIT_AUTOMATION.md).

## 1. Purpose + scope

### 1.1 Problem statement

LB-1 assumes massless neutrinos. Planck-2018 constraints on
`Σm_ν < 0.12 eV (95 %)` require the stack to integrate a
massive-neutrino species. A massive ν species has three properties
the massless one does not:

1. **Non-relativistic transition** at `a_NR = T_{ν,0}/m` — the
   equation of state `w(a)` runs from `1/3` at early times to
   `0` at late times.
2. **Finite free-streaming length** — the mass regulates the
   small-scale cutoff of the neutrino perturbation, modifying
   the matter power spectrum and the CMB damping tail.
3. **Phase-space dependence** — the background `ρ`, `p` and the
   perturbation multipoles require a momentum grid (integral over
   the Fermi-Dirac distribution), not a single analytic form.

FB-9 ships all three ingredients while preserving byte-identity
with the LB-1 stack when `Σm_ν = 0`.

### 1.2 Shipping surfaces

- **`bass.species.massive_neutrino.phase_space_grid(mass_eV,
  N_q=15) → (q_grid, weights)`** — deterministic momentum grid +
  quadrature weights.
- **`bass.species.massive_neutrino.MassiveNeutrinoBackground(
  bg_table, mass_eV, N_q=15)`** — `SpeciesBackground` subclass.
- **`SpeciesBackgroundRegistry.from_planck2018(Sigma_mnu=0.0)`** —
  registry factory with a new optional kwarg.
- **`bass.hierarchy.hierarchy_rhs_neutrino`** — extended to
  consume a massive-ν background (mass-dependent free-streaming
  term).
- **`bass.species.tilted.TiltedSpeciesBackground`** — unchanged
  signature; accepts a `MassiveNeutrinoBackground` as its `base`
  argument (tested in FB-9.5).

### 1.3 Non-goals (pinned)

- **Mass hierarchy splitting** (normal vs inverted, individual
  `m_1, m_2, m_3`): FB-9 ships the **degenerate** approximation
  `m_1 = m_2 = m_3 = Σm_ν / 3`. Non-degenerate hierarchy is
  deferred to a post-extended session; any carry-forward gets a
  dedicated reserved tag.
- **Interacting neutrino sector** (self-interactions, dark-sector
  couplings): out of scope.
- **CAMB HMcode / non-linear power spectrum effects**: out of
  scope (flows from the FB-10 / FB-12 disposal per
  [SCOPE_DECISIONS.md](SCOPE_DECISIONS.md)).

### 1.4 Literature anchors

- **Ma & Bertschinger 1995**, *ApJ* 455, 7 — canonical massive-ν
  Boltzmann hierarchy. Reference equations (56), (57), (97).
- **Lesgourgues & Tram 2011**, *JCAP* 09, 032 — CLASS ncdm
  integration strategy; reference for the momentum grid
  (`N_q = 15` default) and for the `w(a)` interpolation.
- **Dodelson §4** — collisionless phase-space integration.
- **Planck 2018 VI** — constraint target for `Σm_ν`.

---

## 2. FB-9.1 — `phase_space_grid` + determinism tests

### 2.1 Contract

```python
def phase_space_grid(
    mass_eV: float,
    N_q: int = 15,
) -> tuple[np.ndarray, np.ndarray]:
    """Return (q_grid, weights), both shape (N_q,), float64.

    q_grid carries the dimensionless momentum q = p/T_nu0; weights
    carry the product of the Gauss-Laguerre quadrature weight and
    the q² Fermi-Dirac phase-space measure so that
        ∫ q² f(q) g(q) dq = Σ_i weights[i] · g(q_grid[i])
    for any smooth g.
    """
```

### 2.2 Invariants

- Deterministic per `(mass_eV, N_q)`: two calls return byte-
  identical arrays.
- At `mass_eV = 0`, the quadrature reduces to the massless-ν
  analytic integrals: the total phase-space integral
  `Σ_i weights[i]` matches `7π⁴ / 120` within `rtol=1e-12`.
- `N_q ≥ 10` convergence test: the computed `ρ_ν` at any sample
  `a` converges as `N_q → ∞`; the default `N_q = 15` matches the
  CLASS default and is pinned by a convergence-budget test that
  fails on any silent regression of `N_q`.

### 2.3 Delivery PR

- **PR title**: `FB-9.1: phase_space_grid (Gauss-Laguerre, N_q=15)`.
- **Changes**: `bass/species/massive_neutrino/phase_space.py` +
  tests.
- **Byte anchor**: FB-3.2 (`fdb1d86`) — adding a new module does
  not affect any existing path.
- **Audit hook**: determinism round-trip; convergence budget at
  `N_q ∈ {10, 15, 30}`; massless-limit integral.

---

## 3. FB-9.2 — `MassiveNeutrinoBackground.rho_rest` / `.p_rest`

### 3.1 Contract

`MassiveNeutrinoBackground` is a `SpeciesBackground` subclass with
`rho_rest(eta)` and `p_rest(eta)` returning the rest-frame mass
density and pressure — the rest-frame quantities per LB-1
conventions, not tilt-projected (tilt projection is `FB-3`'s
responsibility).

### 3.2 Reference equations

For a Fermi-Dirac-distributed species of mass `m`:

```text
    ρ(a) = (T_nu,0 / a)^4 · ∫ dq q² · ε(q, m, a) · f_FD(q)
    p(a) = (T_nu,0 / a)^4 · (1/3) ∫ dq q^4 / ε(q, m, a) · f_FD(q)

    ε(q, m, a) = sqrt(q² + (m a / T_nu,0)²)
```

(Ma-Bertschinger 1995 eq (56), normalised to `T_ν,0` units.)

### 3.3 Invariants

- `mass_eV → 0` byte-identical to `NeutrinoBackground.rho_rest`
  (LB-1) within the declared tolerance of the phase-space
  quadrature (`rtol=1e-10`).
- `w(a) = p(a) / ρ(a)` crosses `1/6` at `a = a_NR` to within the
  convergence budget of the phase-space grid — matches
  Lesgourgues-Tram 2011 eq (22).
- Positivity: `ρ > 0`, `p > 0`, `w ∈ [0, 1/3]` across the entire
  η-grid.
- `ρ(a)` matches a CLASS reference NPZ fixture (stored under
  `data/class_massive_neutrino_fixtures/Sigma_{0.06, 0.12, 0.24}.npz`)
  to within `rtol=1e-4` on the shared η-grid, for all three
  fiducial `Σm_ν` values.

### 3.4 Delivery PR

- **PR title**: `FB-9.2: MassiveNeutrinoBackground rho_rest / p_rest`.
- **Changes**: `bass/species/massive_neutrino/background.py`;
  CLASS-fixture regression tests.
- **Audit hook**: NR-transition scale `a_NR = T_{ν,0} / m` matches
  Ma-Bertschinger eq (97); `w(a)` monotone decreasing; positivity
  guards.

---

## 4. FB-9.3 — Registry integration + `m=0` byte-identity

### 4.1 Contract

```python
class SpeciesBackgroundRegistry:
    @classmethod
    def from_planck2018(
        cls,
        *,
        Sigma_mnu: float = 0.0,
        ...
    ) -> "SpeciesBackgroundRegistry":
        ...
```

When `Sigma_mnu > 0`, the registry's `NEUTRINO` slot is populated
by a `MassiveNeutrinoBackground(bg_table, mass_eV=Sigma_mnu/3)`;
when `Sigma_mnu == 0.0` (the default), the slot retains the LB-1
massless `NeutrinoBackground` byte-identically.

### 4.2 Invariants

- **Byte-identical at `Sigma_mnu = 0`**: every test in the full
  `bass/ tsc/` suite passes unchanged. This is the non-negotiable
  anchor for the phase.
- `SpeciesLabel.NEUTRINO` is retained; the registry dispatches
  internally to massless or massive based on `Sigma_mnu`. There
  is no `MASSIVE_NEUTRINO` enum value — this intentionally
  prevents downstream code from branching on label identity.

### 4.3 Delivery PR

- **PR title**: `FB-9.3: registry integration with Sigma_mnu kwarg`.
- **Audit hook**: `Sigma_mnu = 0` full-suite byte-identity.

---

## 5. FB-9.4 — Hierarchy wire-up + free-streaming regression

### 5.1 Contract

`hierarchy_rhs_neutrino` already exists (LB-1). FB-9 extends its
mass-handling: when the caller passes a `MassiveNeutrinoBackground`
via the tetrad state / species registry, the RHS consumes an
additional mass-dependent term in the free-streaming operator
(Ma-Bertschinger eq (57)).

### 5.2 Invariants

- **Byte-identical at `Sigma_mnu = 0`** against the LB-1
  hierarchy output.
- At `Sigma_mnu = 0.12 eV`, the free-streaming scale
  `k_fs(a) = 0.0801 (m/0.1 eV) (Omega_m/0.3)^(1/2) Mpc^{-1}`
  (Lesgourgues-Tram eq (112)) is recovered from a dedicated test
  that integrates `δ_ν` and extracts the transition wavenumber.
- `P(k)` for `k > k_fs` is suppressed by the expected factor
  `(1 − 8 f_ν)` to leading order in `f_ν = Ω_ν / Ω_m`
  (Hu-Eisenstein-Tegmark 1998 eq (19)) — match to within 10 %.

### 5.3 Delivery PR

- **PR title**: `FB-9.4: hierarchy_rhs_neutrino mass coupling`.
- **Byte anchor**: whichever hierarchy anchor is in force when
  this lands (FB-3.2 `fdb1d86` at minimum).
- **Audit hook**: §2 phys-math step "known-limit recovery" must
  show massless anchor identity; §5 P0 failure mode "mass term
  applied twice" ruled out by the closed-form `k_fs` recovery
  test.

---

## 6. FB-9.5 — FB-3 compatibility (`TiltedSpeciesBackground` on massive ν)

### 6.1 Purpose

FB-3 ships `TiltedSpeciesBackground(base, beta, v_hat_e)` over a
generic `SpeciesBackground`. FB-9.5 verifies that the tilt wrapper
composes correctly with a massive-ν base without modification to
either side.

### 6.2 Tests

- Bit-identical β = 0: `TiltedSpeciesBackground(base=<massive-ν>,
  beta=0, v_hat_e=any)` reproduces the massive-ν rest-frame output
  byte-identically (mirrors the FB-3.1 bit-identical pin).
- EMM §5.4 eqs (5.12), (5.13) hold for `ρ̃`, `p̃` at β > 0 when
  the base species is massive (test at `Σm_ν = 0.12 eV`, β = 0.3).
- `TiltedSpeciesBackground.v_vector(η)` is unchanged (no mass
  dependence in the tilt velocity itself).

### 6.3 Delivery PR

- **PR title**: `FB-9.5: TiltedSpeciesBackground on massive neutrino`.
- **Changes**: new tests in
  `bass/species/test_tilted_massive_neutrino_compose.py`; no
  modification of `bass/species/tilted.py`.
- **Audit hook**: composition test pins that the massive-ν base
  did not leak any mass-dependent state into the tilt wrapper.

---

## 7. FB-9.6 — Docs + gallery

- **Gallery topic**: `figures/physics_gallery/15_massive_neutrino/`
  with
  - `01_w_of_a_sweep.png` — `w(a)` for `Σm_ν ∈ {0, 0.06, 0.12, 0.24} eV`.
  - `02_rho_p_NR_transition.png` — `ρ(a)` and `p(a)` across the
    NR transition; `a_NR` marker.
  - `03_kfs_vs_a.png` — free-streaming wavenumber.
  - `04_dPk_over_Pk.png` — fractional power suppression at
    `k > k_fs`.
- **Docs updates**:
  [01_species_background_spec.md](../01_species_background_spec.md)
  gains a §N "Massive neutrino" section documenting the
  phase-space grid + `w(a)` interpolation contract.
  [DEVELOPMENT_LOG_FB3_TO_FB7.md](DEVELOPMENT_LOG_FB3_TO_FB7.md)
  (or its successor) receives one row per FB-9.* PR.

- **PR title**: `FB-9.6: docs + physics-gallery topic 15`.

---

## 8. Exit criteria (FB-9 closing audit)

1. Every FB-9.1 … FB-9.6 delivery PR has shipped with its audit
   document; the audits are unanimously Pass.
2. `Sigma_mnu = 0` full-suite byte-identity.
3. `ρ(a)` matches the CLASS fixture at `rtol=1e-4` for all three
   fiducial `Σm_ν` values.
4. `w(a)` crosses `1/6` at `a = a_NR` per Lesgourgues-Tram eq
   (22).
5. `TiltedSpeciesBackground(base=<massive-ν>)` composition test
   green.
6. Gallery topic 15 rendered;
   `figures/physics_gallery/README.md` updated.
7. `NEXT_SESSION_PROMPT.md §2` rotated.

---

## 9. Audit-doc skeleton (FB-9 closing)

Use the template in [SELF_AUDIT_AUTOMATION.md §3](SELF_AUDIT_AUTOMATION.md).
Phase-specific additions:

- **§FB-9.A** — CLASS fixture provenance: every `data/class_massive_neutrino_fixtures/*.npz`
  carries a header record of the CLASS version used to generate
  it, the precision settings, and the commit hash of the
  generating script. A dedicated test asserts the header's
  presence and schema.
- **§FB-9.B** — phase-space convergence budget: `ρ_ν` at three
  sample `a` values computed at `N_q ∈ {10, 15, 30}` must show
  monotone convergence; the audit records the computed deltas.
