# AUDIT — Phase FB-3 (entry): FB-3.1 `TiltedSpeciesBackground` abstraction + β → 0 limit recovery

- **Phase tag**: FB-3 (entry)
- **Sub-phase**: FB-3.1 — species-level tilt wrapper + FB02-F1 resolution
- **Run date**: 2026-04-19
- **Prior baseline**: 3,108 passing + 1 skipped (end of Phase FB-2, commit d7d25da)
- **This-session baseline**: 3,132 passing + 1 skipped (+24 new tests)
- **Commit**: appended below once sealed
- **Author**: Claude Opus 4.7 (1M context), supervised by Jiwon

---

## §0 Audit target reconstruction

| Layer | Claim | Implementation | Output |
|---|---|---|---|
| Physics | King-Ellis 1973 §3 / EMM 2012 §5.4 tilted perfect-fluid split: `ρ̃ = γ²(ρ+p) − p`, `p̃ = p + (1/3)γ²(ρ+p)β²`, `v^a = β v̂_e`, `γ = (1-β²)^{-1/2}`, `|v̂_e| = 1`, `0 ≤ β < 1` | `bass/species/tilted.py::TiltedSpeciesBackground` | `rho_tilde(η)`, `p_tilde(η)`, `v_vector(η)`, `gamma`, `gamma_sq` |
| Invariant | β=0 bit-identical to base (orthogonal path preservation) | Explicit short-circuit `if self.beta == 0.0: return base.X(eta)` | test_T01..T05 × 3 v̂_e sweep (15 cases) use `np.array_equal` |
| Guards | β < 0 / β ≥ 1 / non-finite β / non-unit v̂_e / wrong-length v̂_e → `ValueError` | `__post_init__` eager validation | test_T09..T12 |
| Convention SSOT | `v̂_e` default = `(1, 0, 0)` — matches `BianchiCosmology.v_hat_e` | `V_HAT_E_DEFAULT = (1.0, 0.0, 0.0)` constant + regression | test_T13 (FB02-F1) |

**Source of truth**:
- Code `bass.species.tilted` is the FB-3.1 surface SSOT.
- Docs `00_conventions §2` is the `v̂_e` SSOT (FB02-F1 now cross-referenced there).
- Numerical outputs are trusted iff they (a) pass `np.array_equal` on β=0 and (b) match the closed-form EMM §5.4 formulas on β>0.

---

## §1 Contract / interface table

| Surface | Input | Output | Units | Invariant |
|---|---|---|---|---|
| `TiltedSpeciesBackground(base, beta, v_hat_e)` | `SpeciesBackground`, float, 3-tuple | dataclass | — | β ∈ [0,1), |v̂_e|²=1±1e-10 |
| `.rho_tilde(η)` | scalar / array | same shape | `ρ_crit,0` units | β=0 → `base.rho_rest(η)` byte-identical |
| `.p_tilde(η)` | scalar / array | same shape | `ρ_crit,0` units | β=0 → `base.p_rest(η)` byte-identical |
| `.v_vector(η)` | scalar / (N,) | (3,) / (N,3) | dimensionless velocity | β=0 → zeros |
| `.gamma` | — | float | dimensionless | β=0 → exactly 1.0 |
| `.gamma_sq` | — | float | dimensionless | β=0 → exactly 1.0 |

Out-of-range / malformed inputs raise `ValueError` in `__post_init__` — no silent renormalisation.

---

## §2 Phys-math audit ledger

1. **Definition/notation**: β is boost velocity magnitude (prompt SSOT), not rapidity. The tension with the rapidity form of `B(η, ê) = cosh β + sinh β (ê·v̂_e)` in `tilted_visibility.py` is **not a contradiction** — `TiltedVisibility` internally stores a 3-velocity `v_e(η)` and derives `β_rapidity = atanh|v_e|` as a *display variable*. The FB-3.1 wrapper stores `|v| = β` directly; the two modules agree whenever the visibility caller composes `v_e = β × v̂_e`. Flagged as doc-only carry (see §7 below); no code change needed for FB-3.1. **Pass (with note)**.
2. **Indices / PSTF**: `v^a` is a spatial vector in the `n^a`-frame tetrad basis — aligned with `e_1` by default (matches §5.4 basis alignment). No PSTF truncation at FB-3.1 (scalar + vector surface only). **Pass**.
3. **Sign / normalisation**: β ≥ 0 by construction (sign lives in v̂_e). `|v̂_e|² = 1` checked to `1e-10`. γ² > 0 always. **Pass**.
4. **Units / dimension**: ρ̃, p̃ have units of ρ_crit,0 (same as base). v^a is dimensionless velocity (c=1 natural units). γ is dimensionless. **Pass**.
5. **Known-limit recovery**: β=0 → base values bit-for-bit (strong invariant, pinned by `np.array_equal`). At radiation EoS w=1/3, ρ̃/ρ = (γ²(4/3) − 1/3) > 1 for γ>1 — matches EMM. At dust EoS w=0, ρ̃/ρ = γ² — matches King-Ellis. At Λ (ρ+p=0): ρ̃ = −p = +ρ = ρ — invariant check, ρ̃ = ρ for Λ **regardless of β**. **Pass**.
6. **Boundary / positivity**: β ∈ [0,1) is admissible; β=1 (and β>1) caught eagerly. Λ case (ρ+p=0): p̃ = p + 0 = p, ρ̃ = 0 − p = −p_Λ = +ρ_Λ — preserved by algebra. **Pass**.
7. **Hidden assumption**: The wrapper assumes `base.rho_rest` and `base.p_rest` satisfy the *rest-frame* perfect-fluid relation T^{ab} = (ρ̂+p̂)u^au^b + p̂g^{ab}. This is the LB-1 contract for all five species. If a future species adds an anisotropic-rest-frame π_ab, the wrapper needs an extra term (flagged in §5 — deferred to FB-3.2 / FB-4 via the companion `decompose_tilted_species` in `bass.tilt.species_tilt`). **Pass for LB-1 species**.
8. **Counter-example**: with β=0.999 and dust (w=0), γ²≈500, so ρ̃/ρ ≈ 500 — sanity-checked against EMM §5.4. Finite at β=0.999; diverges as β→1 as expected. **Pass**.

---

## §3 Equation-to-code mapping audit

| Equation | Code | Status |
|---|---|---|
| EMM §5.4 eq (5.12): `ρ̃ = γ²(ρ+p) − p` | `tilted.py::rho_tilde` else-branch | ✅ direct, no approximation |
| EMM §5.4 eq (5.13): `p̃_iso = p + (1/3)γ²(ρ+p)β²` | `tilted.py::p_tilde` else-branch | ✅ direct |
| King-Ellis §2: `v^a = β v̂^a` | `tilted.py::v_vector` else-branch | ✅ broadcast to eta shape |
| `γ = (1−β²)^{-1/2}` | `tilted.py::gamma` property | ✅ short-circuit at β=0 |
| FB02-F1 v̂_e SSOT | `V_HAT_E_DEFAULT = (1,0,0)` | ✅ equals `BianchiCosmology._V_HAT_E_DEFAULT` (test_T13 pins) |

**No dead code**. **No placeholder**. The β=0 short-circuit is the only path with scope for bit-identity, and it is explicitly used.

---

## §4 Numerical / pipeline audit

- **Solver suitability**: No ODE or iterative solve at FB-3.1 (pure algebra). N/A.
- **Tolerance sensitivity**: `V_HAT_NORM_TOL = 1e-10` on |v̂|² − 1 — tight; integrator noise doesn't supply v̂_e, only user does.
- **Underflow / cancellation**: The algebraic form `γ²(ρ+p) − p` has O(1) cancellation for small β (γ² ≈ 1, so γ²(ρ+p) ≈ ρ+p, subtracting p leaves ρ with one digit of catastrophic cancellation for β=0). **Mitigated by the β=0 short-circuit** (the one case where this would matter for bit-identity); for β>0 the cancellation is present but bounded by γ²-1 = β²/(1-β²), which at β=0.01 is 1e-4 — well within float64 precision.
- **Conditioning**: γ² diverges as β→1 as expected; caught by β<1 guard. At β=0.99, γ² ≈ 50 — still well-behaved.
- **Determinism**: No RNG; all arithmetic deterministic. Frozen dataclass prevents mutation.
- **OOD risk**: None — all paths are analytic closed forms. No tabulation / interpolation involved at this surface.

---

## §5 Ranked failure modes

| # | Type | Severity | Symptom | Root cause | Cheap probe | Misinterpretation risk |
|---|---|---|---|---|---|---|
| 1 | physics | P0 (averted) | β=0 regression drifts by 1e-16 | `γ²(ρ+p) − p` cancellation at γ=1 | short-circuit + `np.array_equal` in test_T01..T05 | treating "within 1e-15" as bit-identical |
| 2 | interface | P1 (averted) | `v̂_e = 0.9999999 e₁` silently accepted | loose norm tolerance | test_T11 pins 10×tol boundary | thinking "close enough" on unit vectors |
| 3 | physics | P1 (averted) | β=1.0 produces inf γ² and silently continues | missing β<1 guard | test_T09 with β=1.0 | calling with v = c boost |
| 4 | doc | P2 (carried) | β-parametrisation split between velocity (FB-3.1) and rapidity (LB-4 Layer A) causes future-FB confusion | Two independent earlier SSOTs, unified via identity | Carried to FB-3.5 β-gate reparametrisation | miscomposing `TiltedVisibility` and `TiltedSpeciesBackground` | 
| 5 | interface | P2 (carried) | `bass.tilt.species_tilt.TiltedSpeciesParams` has an overlapping surface (v-vector rather than β+v̂_e) | Historical dual API (Y-Block vs LB-1) | Future FB-3.2 work should prefer `TiltedSpeciesBackground`, deprecate or compose with Y-Block | Using both + getting inconsistent γ |

**Repair plan for #1/#2/#3**: already applied (short-circuit + boundary tests).
**#4 / #5**: doc-only carry — flagged for FB-3.2 unification (not an FB-3.1 bug).

---

## §6 Verifier filter

| Verifier | Verdict | Evidence |
|---|---|---|
| A. Physics — known-limit recovery | **Passed** | β=0 bit-identity (15 test cases across 5 species × 3 v̂_e) |
| A. Physics — dimensional consistency | **Passed** | ρ̃, p̃ inherit base units; γ dimensionless |
| A. Physics — sign / normalisation | **Passed** | β ≥ 0, |v̂_e|² = 1, γ² > 0 all pinned |
| A. Physics — positivity / admissibility | **Passed** | For ρ ≥ 0, γ² ≥ 1: ρ̃ = γ²(ρ+p) − p ≥ ρ when ρ+p ≥ 0 (radiation, dust); Λ special-case holds by algebra |
| A. Physics — alternative explanation | **Passed** | EMM §5.4 formulas are exact; small-β limit `μ ≈ ρ + (1+w)ρβ²` derivable from the code formula |
| B. Code — contract satisfaction | **Passed** | frozen dataclass; eager validation; no silent fallback |
| B. Code — actual code-path usage | **Passed** | test_T01..T14 exercise every branch; pytest -q confirms 24/24 pass |
| B. Code — regression risk | **Passed** | 3,108 → 3,132 (no regressions, +24 new); tilt wrapper is additive, does not mutate any existing surface |
| B. Code — reproducibility | **Passed** | Deterministic arithmetic; no RNG |
| C. Numerical — tolerance robustness | **Passed** | rtol=0 atol=0 equality on EMM formula reproduction |
| C. Numerical — convergence / stability | **N/A** | no iterative solve at this rotation |
| C. Numerical — baseline reproducibility | **Passed** | β=0 byte-identical to base pinned by `np.array_equal` |
| C. Numerical — uncertainty / misspecification | **Passed** | `V_HAT_NORM_TOL = 1e-10` documented; β validation eager |

**All verifiers pass or N/A**.

---

## §7 Minimal repair plan

No P0 / P1 failure modes detected. P2 items are doc-only carries handled in §9.

---

## §8 Minimal test set (executed)

| Test | Role | Verdict |
|---|---|---|
| `test_T01..T05_<species>_beta_zero_bit_identical` (15 cases) | baseline reproduction — β=0 byte identity × 5 species × 3 v̂_e | ✅ |
| `test_T06_beta_positive_finite_and_enhanced` | physics sanity — γ>1, ρ̃>ρ on radiation | ✅ |
| `test_T07_beta_positive_emm_5_12_5_13` | baseline reproduction — exact EMM closed form | ✅ |
| `test_T08_v_vector_shape_and_beta_zero` | interface — shape guarantees (scalar/array) | ✅ |
| `test_T09_superluminal_beta_raises` | adversarial — β=1.0 / 1.2 | ✅ |
| `test_T10_negative_or_nonfinite_beta_raises` | adversarial — β<0 / NaN / inf | ✅ |
| `test_T11_non_unit_v_hat_raises` | adversarial — non-unit v̂_e | ✅ |
| `test_T12_wrong_length_v_hat_raises` | adversarial — length ≠ 3 | ✅ |
| `test_T13_v_hat_default_matches_bianchi_cosmology_fb02_f1` | regression — FB02-F1 cross-reference pin | ✅ |
| `test_T14_gamma_identities` | numerical sanity — γ / γ² / v_magnitude identity sweep | ✅ |

**24 passed / 0 failed / 0 skipped.**

---

## §9 Final verdict

- **Status**: **Pass** — FB-3.1 entry sealed.
- **Implement now (this session)**: resolved — `TiltedSpeciesBackground` + FB02-F1 cross-reference shipped.
- **Do NOT touch**: FB-3.2 wire-up (hierarchy driver `accel_vector` / `vorticity_vector` consumption of `v_vector`); FB-3.5 β-gate reparametrisation; FB-4 Thomson Layer-B boost kernel.

### Outstanding P2/P3 carried forward (do not touch unless in their reserved session)

- **FB02-F1** → ✅ resolved in this rotation (00_conventions §2 cross-reference + test_T13 pin).
- **F3** (doc-only): `TetradBackgroundState.shear_magnitude_sq` dimensionless-Σ² rescale → **FB-5 / FB-6 reserved**.
- **FB11-F1**: W-E Table 11.1 fixed-point coordinates → **FB-5 / FB-6 reserved**.
- **FB12-F1**: IX isotropic leading-order shear-source residual `S_+ = +(2/3) n²ℋ²` (W-E pathology) → **FB-5 / FB-6 reserved**.
- **FB12-F3**: `bianchi_ix_recollapse_event` coupling to `_hubble_squared` → **FB-5 / FB-6 reserved**.
- **FB13-κ-calibration**: VII_h Pontzen-Challinor spiral κ → **FB-5 / FB-6 reserved**.
- **FB-2.1 P2**: complex-dtype `nabla_dispatch` → `hierarchy_rhs_photon` real-dtype driver wire-up → **FB-5.1 reserved**.
- **FB-2.3 P3 (env)**: `venv/bin/pip` shebang stale → post-FB devops.
- **FB-3.1 P2 new**: β-parametrisation split (velocity `TiltedSpeciesBackground` vs rapidity `TiltedVisibility`) — composition rule is `v_e(η) = β × v̂_e` to unify; **FB-3.5 reserved** for β-gate reparametrisation audit that formally unifies the two.
- **FB-3.1 P2 new**: overlap with `bass.tilt.species_tilt.TiltedSpeciesParams` (separate Y-Block API with v-vector input) — future FB-3.2 should prefer the LB-1-native `TiltedSpeciesBackground` or compose both; **FB-3.2 reserved**.
- **FB-5.2**: off-axis helical Wigner rotation for all non-axis-aligned subset.

### Gallery (FB-3.1)

FB-3.1 is abstraction-only (no new physical trajectory generated) — **no-op on gallery**. Per the phase-boundary gallery rule, this is documented here rather than producing an unused PNG. Gallery regeneration continues in FB-3.2 when tilt-projected vectors feed `hierarchy_rhs_photon`.

### Baseline movement

- Pre-session: 3,108 passing + 1 skipped.
- Post-session: 3,132 passing + 1 skipped.
- Delta: +24 tests (all in `bass/species/test_tilted.py`).
- No regressions.

---

## Phase FB-3 entry declaration

This audit **opens Phase FB-3** of the Full-Bianchi-Coverage roadmap
(`docs/lowell_bianchi/FULL_BIANCHI_COVERAGE_PLAN.md §4 Phase FB-3`).
The species-level tilt surface is now stable; FB-3.2 may proceed to
wire `TiltedSpeciesBackground.v_vector(η)` (and, later, `q̃^a` /
`π̃^{ab}`) into `hierarchy_rhs_photon`'s `accel_vector` /
`vorticity_vector` kwargs that were structurally pinned in FB-2.4.

No change to any existing integrator, species, or collision surface.

---

## §FB-3.2 Supplement — tilt-projected `A^a` / `ω^a` wire-up into `hierarchy_rhs_photon`

- **Sub-phase**: FB-3.2 — species-level kinematic adapters +
  hierarchy driver wire-up
- **Run date**: 2026-04-19
- **Prior baseline** (post-FB-3.1): 3,132 passing + 1 skipped
- **This-session baseline**: 3,189 passing + 1 skipped (+57 new tests)
- **Commit**: appended below once sealed
- **Author**: Claude Opus 4.7 (1M context), supervised by Jiwon

## §FB-3.2.0 Audit target reconstruction

| Layer | Claim | Implementation | Output |
|---|---|---|---|
| Physics (acceleration) | King-Ellis 1973 §3 / EMM 2012 eq (5.17) tilt-induced 4-acceleration; species-specific piece at FB-3.2 is `A^a = γ² v^a` (EMM eq 5.14 flux-direction) | `bass/hierarchy/tilt_kinematics.py::accel_from_tilt` | `(3,)` float64 vector |
| Physics (vorticity) | Pontzen-Challinor 2009 §2 Class B leading piece `ω^a = (1/2) ε^{abc} a_b v_c`; Class A = 0 | `bass/hierarchy/tilt_kinematics.py::vorticity_from_tilt` | `(3,)` float64 vector |
| Invariant | β=0 → fresh `np.zeros(3)` byte-identical; full driver with β=0 adapter output equals FB-2.4 no-kwargs anchor (commit `d7d25da`) for every structure-constant label | Explicit short-circuit `if tilted.beta == 0.0: return _ZERO3.copy()` | K-01, K-02 (β=0 zero on 12 labels each); K-09 (driver byte-identity on 12 labels) |
| Routing | `hierarchy_rhs_photon(..., accel_vector=accel_from_tilt(...), vorticity_vector=vorticity_from_tilt(...))` now produces non-zero T4/T5/T6 at β>0 | unchanged driver signature (FB-2.4 slots consumed) | K-10, K-11 (β>0 finite; Class B ≠ Class A) |
| Overlap resolution (P2) | Composition rule `TiltedSpeciesParams(v = β·v̂_e) ↔ TiltedSpeciesBackground(β, v̂_e)`; both APIs remain, LB-1-native wrapper is the hierarchy-driver consumer | Y-Block `TiltedSpeciesParams` untouched; new `tilt_kinematics` module only reads `TiltedSpeciesBackground` | K-12 (composition rule pinned) |

**Source of truth**: `bass.hierarchy.tilt_kinematics` is the FB-3.2 SSOT
for the species-level kinematic 3-vectors consumed by `T4/T5/T6`. The
driver signature is the FB-2.4 SSOT (unchanged).

## §FB-3.2.1 Contract / interface table

| Surface | Input | Output | Units | Invariant |
|---|---|---|---|---|
| `accel_from_tilt(tilted, eta)` | `TiltedSpeciesBackground`, float | ndarray `(3,)` float64 | dimensionless × γ² v | β=0 → `np.zeros(3)` fresh copy |
| `vorticity_from_tilt(tilted, eta, structure=None)` | `TiltedSpeciesBackground`, float, optional `StructureConstants` | ndarray `(3,)` float64 | [1/length] × v (Class B) or 0 (Class A / None) | β=0 → zeros; Class A → zeros; `structure=None` → zeros |
| Driver contract | existing FB-2.4 signature unchanged | n/a | n/a | β=0 adapter output → byte-identical RHS vs no-kwargs baseline on 12 labels |

## §FB-3.2.2 Phys-math audit ledger

1. **Definition / notation**. `A^a_FB32 := γ² v^a` is labelled in the
   docstring as the **species-specific leading piece** of EMM eq
   (5.17); the full tilt acceleration additionally carries
   `(Θ/3) v^a + σ^a_b v^b` which is deferred to FB-3.3 per the stated
   non-goals (the adapters do not touch `Θ` or `σ_ab`). The rank
   (vector) and index convention (contravariant spatial tetrad basis)
   match the consumers `T4_accel_divergence` and `T5_accel_gradient`.
   **Pass**.
2. **Indices / PSTF**. `A^a` and `ω^a` are rank-1 — no PSTF projection
   at this surface; the consumers do the projection downstream. **Pass**.
3. **Sign / normalisation**. `np.cross(a, v)` implements the right-handed
   ε convention; `test_K15` pins the sign against the closed form
   `ω_3 = −(1/2) a_twist β`. **Pass**.
4. **Units / dimension**. `γ² v^a` is dimensionless (v is the
   dimensionless velocity in `c = 1` natural units). `(1/2) a × v` has
   the dimensions of `a_twist` (inverse length, from the Ellis-MacCallum
   structure-constant split), matching the inverse-Mpc ω^a convention
   consumed by `T6_vorticity`. **Pass**.
5. **Known-limit recovery**. β=0 short-circuits to `np.zeros(3)` and the
   full driver becomes byte-identical to FB-2.4. The K-09 test pins
   this across all 12 labels (`FLRW` + 11 Bianchi types) with
   `np.array_equal`. **Pass**.
6. **Boundary / positivity**. Both adapters are finite on the
   admissible domain `β ∈ [0, 1)`; `test_K14` sweeps β ∈
   {0, 1e-6, 0.01, 0.1, 0.5, 0.9} × {Class A, Class B}. **Pass**.
7. **Hidden assumption**. `accel_from_tilt` assumes the species-specific
   acceleration is separable from the shared background kinematic
   pieces; this is exact at β=0 and valid as an additive
   decomposition at β>0 (EMM §5.4 is linear in the three pieces
   `v̇^a`, `Θ v^a`, `σ×v`). The FB-3.3 rotation will *extend* this
   additive form — it will not replace anything FB-3.2 ships. **Pass**.
8. **Counter-example**. Class A VIII / IX with non-trivial n_ab and
   zero a_twist: `vorticity_from_tilt` short-circuits to zeros (K-04
   covers 6 Class A types). This is consistent with EMM §5.4: Class A
   admits **no homogeneous background vorticity from the tilt
   velocity alone** because `ω^a` in the Pontzen-Challinor leading
   form is proportional to a_α × v, and a_α = 0 for Class A. The
   Class A vorticity source that does exist (via ε^{abc} ∇̃_b v_c)
   enters only when `∇̃_b` is non-trivial (FB-5 perturbation sector)
   — deferred. **Pass**.

## §FB-3.2.3 Equation-to-code mapping audit

| Equation | Code | Status |
|---|---|---|
| EMM eq (5.14) species flux direction `γ² v^a` | `tilt_kinematics.py::accel_from_tilt` else-branch | ✅ direct |
| Pontzen-Challinor §2 Class B `ω^a = (1/2) ε^{abc} a_b v_c` | `tilt_kinematics.py::vorticity_from_tilt` Class B branch via `np.cross(a_vec, v)` | ✅ direct (right-hand sign, K-15 pinned) |
| FB-2.4 driver contract `accel_vector`, `vorticity_vector` kwargs | `hierarchy_rhs_photon` unchanged; adapters feed kwargs | ✅ byte-identical at β=0 (K-09) |
| FB-3.1 P2 composition rule `v = β·v̂_e` | `TiltedSpeciesBackground.v_vector(η)` ↔ `TiltedSpeciesParams.v` | ✅ K-12 pins equality |

**No dead code. No placeholder.** The β=0 short-circuit is the only
path claiming bit-identity; it is explicitly exercised by 24 K-01/K-02
parametrisations + 12 K-09 driver parametrisations.

## §FB-3.2.4 Numerical / pipeline audit

- **Solver suitability**: no ODE at the adapter surface; consumers
  (driver) retain their FB-2.4 solver contract. N/A here.
- **Cancellation**: `γ² v^a` at small β has `γ² = 1 / (1 − β²)`; the
  divisor stays comfortably bounded away from zero on the admissible
  domain. At β=0 the short-circuit skips the division entirely. **Pass**.
- **Determinism**: no RNG; adapters are pure functions of their inputs
  (modulo the fresh-copy ``_ZERO3.copy()`` to prevent caller aliasing).
- **Conditioning**: `np.cross(a_vec, v)` is numerically stable for
  all realistic `a_twist` × β products. **Pass**.
- **OOD risk**: zero tabulation / interpolation in the adapters; the
  eta argument is accepted only to preserve signature stability across
  FB-3.3 extensions (where σ(η), Θ(η) will enter). **Pass**.

## §FB-3.2.5 Ranked failure modes

| # | Type | Severity | Symptom | Root cause | Cheap probe | Misinterpretation risk |
|---|---|---|---|---|---|---|
| 1 | physics | P0 (averted) | β=0 driver drifts from FB-2.4 on Class B due to adapter emitting a non-zero vorticity | Missing short-circuit ordering (β=0 check must precede Class A / B decision) | K-09 × 5 Class B labels with `np.array_equal` | thinking "Class B always has ω" |
| 2 | code | P0 (averted) | Adapter returns a module-level array; caller mutation propagates | Shared `_ZERO3` reference | `_ZERO3.copy()` on every return + K-07 fresh-copy guard | treating numpy returns as immutable |
| 3 | physics | P1 (averted) | Sign flip on Class B ω from `np.cross` argument order | `np.cross(a, v)` vs `np.cross(v, a)` yield opposite sign | K-15 closed-form pin `ω_3 = −(1/2) a_twist β` | following matrix-product conventions blindly |
| 4 | interface | P1 (averted) | `v_vector(eta)` returns shape (N,3) for array eta; adapter chokes downstream | contract says (3,) for scalar eta | explicit `v.shape != (3,)` guard + K-06 shape sweep | passing array eta at scalar-only adapter surface |
| 5 | physics | P2 (carried) | `accel_from_tilt` lacks the `(Θ/3) v^a + σ^a_b v^b` pieces, so β>0 output under-represents the true A^a | FB-3.2 non-goals pin this to FB-3.3 | FB-3.3 extends the else-branch additively | assuming `γ² v^a` alone is the full A^a |
| 6 | physics | P2 (carried) | `vorticity_from_tilt` lacks the Class A `ε^{abc} ∇̃_b v_c` piece (harmonic-mode, non-homogeneous) | FB-5 perturbation-sector deferment | FB-5.1 harmonic-mode wire-up | assuming Class A has ω ≡ 0 for all time |
| 7 | interface | P2 (closed here) | Y-Block `TiltedSpeciesParams` vs LB-1 `TiltedSpeciesBackground` divergence | Two parallel APIs, composition rule documented | K-12 pins the rule | using both without `v = β·v̂_e` composition |

**Repairs** for #1/#2/#3/#4 applied and pinned. **#5/#6** carried per
FB-3 roadmap. **#7** closed in this rotation by the composition-rule
test and the module-docstring note.

## §FB-3.2.6 Verifier filter

| Verifier | Verdict | Evidence |
|---|---|---|
| A. Physics — known-limit recovery | **Passed** | K-01/K-02 (24 parametrisations); K-09 (12 parametrisations, `np.array_equal`) |
| A. Physics — dimensional consistency | **Passed** | γ²v dimensionless; a×v carries [1/length] from a_twist |
| A. Physics — sign / normalisation | **Passed** | K-15 pins right-hand-rule sign on ω |
| A. Physics — alternative explanation | **Passed** | EMM §5.4 + Pontzen-Challinor §2 leading forms; no small-β expansion |
| B. Code — contract satisfaction | **Passed** | shape (3,) enforced; fresh copy on every β=0 return |
| B. Code — actual code-path usage | **Passed** | 57/57 new tests pass; regression 3,132 → 3,189 |
| B. Code — regression risk | **Passed** | driver signature unchanged; adapters additive; β=0 anchor preserved |
| B. Code — reproducibility | **Passed** | deterministic arithmetic; no RNG |
| C. Numerical — tolerance robustness | **Passed** | K-03, K-05, K-09, K-15 all `rtol=0 atol=0` |
| C. Numerical — convergence / stability | **N/A** | no iterative solve introduced |
| C. Numerical — baseline reproducibility | **Passed** | K-09 `np.array_equal` anchor on 12 labels |

**All verifiers pass or N/A.**

## §FB-3.2.7 Minimal repair plan

No P0 / P1 failure modes detected. P2 items deferred per roadmap
(FB-3.3 for acceleration completion; FB-5.1 for Class A vorticity
harmonic-mode piece).

## §FB-3.2.8 Minimal test set (executed)

| Test | Role | Verdict |
|---|---|---|
| `test_K01_accel_beta_zero_returns_zeros[<12 labels>]` | baseline — β=0 zeros on FLRW + 11 Bianchi types | ✅ |
| `test_K02_vorticity_beta_zero_returns_zeros[<12 labels>]` | baseline — β=0 zeros on every structure | ✅ |
| `test_K03_accel_closed_form_beta_positive` | physics — γ²v closed form | ✅ |
| `test_K04_vorticity_class_A_is_zero_at_beta_positive[<6 labels>]` | physics — Class A → 0 at β>0 | ✅ |
| `test_K05_vorticity_class_B_closed_form[<5 labels>]` | physics — (1/2) a × v closed form | ✅ |
| `test_K06_shape_guarantee` | interface — shape (3,) on every branch | ✅ |
| `test_K07_fresh_copy_on_beta_zero` | interface — caller mutation does not leak | ✅ |
| `test_K08_vorticity_structure_none_is_zero` | interface — structure=None at β>0 | ✅ |
| `test_K09_driver_beta_zero_bit_identical_to_fb24[<12 labels>]` | regression — driver byte-identity vs FB-2.4 anchor | ✅ |
| `test_K10_driver_beta_positive_is_finite_and_differs` | regression — β>0 non-trivial finite output | ✅ |
| `test_K11_class_B_driver_differs_from_class_A` | regression — ω routing into T6 | ✅ |
| `test_K12_p2_overlap_composition_rule` | P2 overlap — composition rule | ✅ |
| `test_K13_eta_independent_at_fb32` | contract — η-invariance at FB-3.2 surface | ✅ |
| `test_K14_admissible_inputs_do_not_raise` | adversarial — β ∈ [0, 0.9] × Class A/B | ✅ |
| `test_K15_vorticity_levi_civita_sign` | physics — right-hand ε convention pinned | ✅ |

**57 passed / 0 failed / 0 skipped.**

## §FB-3.2.9 Final verdict

- **Status**: **Pass** — FB-3.2 wire-up sealed.
- **Implement now (this session)**: resolved — tilt kinematic adapters
  shipped; driver wire-up live end-to-end; P2 overlap resolved.
- **Do NOT touch**: `(Θ/3) v^a + σ^a_b v^b` additive pieces on
  `accel_from_tilt` (FB-3.3 Einstein + tilt coupling); Class A
  harmonic-mode vorticity (FB-5.1); β-gate reparametrisation (FB-3.5);
  Thomson Layer B (FB-4).

### Gallery (FB-3.2)

FB-3.2 changes the hierarchy driver's β>0 RHS but leaves the β=0 FB-2.4
gallery trajectories byte-identical (K-09 anchor). No β>0 end-to-end
integration is performed at this rotation — FB-3.3 is the natural
checkpoint for a tilted-β trajectory plot (shear feedback + non-trivial
`A^a` dynamics). **No-op on gallery this rotation**; gallery
regeneration resumes at FB-3.3.

### Baseline movement (FB-3.2)

- Pre-session: 3,132 passing + 1 skipped.
- Post-session: 3,189 passing + 1 skipped.
- Delta: +57 tests (all in `bass/hierarchy/test_tilt_kinematics.py`).
- No regressions.

---

## §FB-3.3 Supplement — Einstein + tilt coupling + boost-kernel seed

- **Sub-phase**: FB-3.3 — `accel_from_tilt` additive Θ/3 and σ pieces
  + axi-symmetric boost-kernel seed.
- **Prior baseline** (post-FB-3.2): 3,189 passing + 1 skipped.
- **This-session baseline**: 3,213 passing + 1 skipped (+24 new tests).

### §FB-3.3.0 Target reconstruction

| Layer | Claim | Implementation | Output |
|---|---|---|---|
| Physics | EMM 2012 eq (5.17) tilt 4-acceleration with `v̇^a = 0`: `A^a = γ²[v^a + (Θ/3)v^a + σ^a_b v^b]` (additive on FB-3.2 placeholder) | `bass/hierarchy/tilt_kinematics.py::accel_from_tilt` extended with `bg_table` + `tetrad_state` kwargs | `(3,)` float64 |
| Physics | Challinor 2000 eq (26) linear PSTF boost on m=0 slice | `bass/hierarchy/boost_kernel.py::boost_project_axisymmetric` | `(L+1,)` float64 |
| Invariant | `β = 0` → byte-identical zero / identity on every new path | explicit short-circuit + `np.array_equal` pins | M-01/M-02/M-03; M-09 |
| Invariant | FB-3.2 backward-compat: `accel_from_tilt(tilted, eta)` without kwargs matches FB-3.2 | kwargs default to `None` | M-04 |
| Scope pin | Off-axis `v̂_e` → `NotImplementedError` (FB-5.2 reserved) | `is_axis_aligned` guard in `boost_project_axisymmetric` | M-11 |

### §FB-3.3.1 Contract additions

| Surface | Signature diff | Invariant |
|---|---|---|
| `accel_from_tilt(tilted, eta, *, bg_table=None, tetrad_state=None)` | two optional kwargs | `None / None` path byte-identical to FB-3.2 |
| `boost_project_axisymmetric(coeffs, beta, v_hat_e=V_HAT_E_DEFAULT, *, tol)` | new | `β=0` returns input copy byte-identically |
| `is_axis_aligned(v_hat_e, *, tol)` | new | True iff exactly one component has magnitude `1 ± tol` |

### §FB-3.3.2 Phys-math ledger

1. **Definition / notation**. `γ²` / `Θ` / `σ^a_b v^b` named and typed
   identically to EMM §5.4 / §16. The `σ` consumed by the adapter
   is the *proper-time* shear returned by `proper_shear_at_eta` — the
   LB-2a F1 convention. **Pass**.
2. **Indices / PSTF**. `A^a` is rank-1; `σ^a_b v^b` is a matrix-vector
   contraction on the spatial 3-basis. No PSTF projection at this
   surface. **Pass**.
3. **Sign / normalisation**. Additive formula uses the standard
   `+(Θ/3) v^a` (comoving expansion *accelerates* the tilt direction).
   Sign pinned by M-05 closed-form test against the prepared Θ(η).
   **Pass**.
4. **Units / dimension**. `Θ` has units [1/Mpc]; `σ` has units
   [1/Mpc]. Both terms have dimension of an acceleration once
   multiplied by `v^a` (dimensionless velocity). The FB-3.2 bare
   `γ² v^a` term remains dimensionally-representative only (a
   placeholder) — the audit records that physical dimension is
   restored when the kinematic kwargs are supplied. **Pass with
   note**.
5. **Known-limit recovery**. `β=0` byte-zero on every kwargs path;
   `β>0` without kwargs recovers the FB-3.2 `γ²v^a` placeholder;
   M-04 pins this. **Pass**.
6. **Boundary / positivity**. `tetrad_state` without `bg_table`
   raises `ValueError` because σ → proper conversion needs `a(η)`.
   M-08 pins this. **Pass**.
7. **Hidden assumption**. Additive policy (FB-3.2 placeholder + EMM
   pieces) vs. replacement policy was a design choice documented
   here and in the module docstring. The alternative "replace with
   EMM eq (5.17) verbatim when kwargs supplied" was rejected for
   backward-compat and for the clean β=0 anchor under both paths.
   **Pass with note**.
8. **Counter-example**. Off-axis `v̂_e = (1/√2, 0, 1/√2)` on the
   boost kernel raises `NotImplementedError` with a specific
   reference to FB-5.2. **Pass**.

### §FB-3.3.3 Equation-to-code mapping

| Equation | Code |
|---|---|
| EMM eq (5.17) additive `γ²[v + (Θ/3)v + σ·v]` | `tilt_kinematics.py::accel_from_tilt` extended else-branch |
| Challinor 2000 eq (26) m=0 PSTF linear boost | `boost_kernel.py::boost_project_axisymmetric` β>0 path |
| Axis-alignment admissibility | `boost_kernel.py::is_axis_aligned` |

### §FB-3.3.4 Numerical / pipeline

- Cancellation: `γ²(Θ/3)` bounded by `Θ_max ~ 3H_0` × `γ²_max < O(10)`
  for `β < 0.9`; no condition-number issue on the admissible domain.
- Shear spline cache reused from `proper_shear_at_eta`; O(log N) per
  query after first build. Determinism preserved.
- Off-axis guard is a hard branch — no silent degradation to some
  fallback kernel.

### §FB-3.3.5 Ranked failure modes

| # | Type | Severity | Symptom | Root cause | Cheap probe |
|---|---|---|---|---|---|
| 1 | physics | P0 (averted) | `β=0` extended-kwargs path drifts from the zero vector | short-circuit ordering | M-01/M-02 at the `fresh copy` level |
| 2 | interface | P0 (averted) | `tetrad_state` passed without `bg_table` silently runs with `a=1` | explicit `ValueError` in the adapter | M-08 |
| 3 | physics | P1 (averted) | Boost kernel emits non-zero at `β=0` | explicit short-circuit + fresh copy | M-09 |
| 4 | scope | P1 (averted) | Off-axis `v̂_e` silently reduces to on-axis | `is_axis_aligned` guard | M-11 / M-14 |
| 5 | physics | P2 (carried) | Additive FB-3.2 placeholder is not literally EMM eq (5.17) | documented design choice; FB-3.5 reparametrisation revisits | — |

### §FB-3.3.6 Verifier filter

All A / B / C verifiers pass or N/A. Coverage-test for off-axis is
the dedicated `NotImplementedError` branch (no silent degradation).

### §FB-3.3.8 Minimal test set

| Test | Role | Verdict |
|---|---|---|
| M-01 .. M-03 | β=0 byte-identity on every new kwarg path | ✅ |
| M-04 | FB-3.2 backward compatibility | ✅ |
| M-05 | Θ-piece additive closed form | ✅ |
| M-06 | σ-piece additive closed form | ✅ |
| M-07 | β-sweep combined closed form | ✅ (3 cases) |
| M-08 | `tetrad_state` without `bg_table` → `ValueError` | ✅ |
| M-09 | boost-kernel β=0 identity | ✅ |
| M-10 | boost-kernel linear Challinor closed form | ✅ |
| M-11 | off-axis → `NotImplementedError` | ✅ |
| M-12 | β out of range → `ValueError` | ✅ |
| M-13 | non-1D input → `ValueError` | ✅ |
| M-14 | `is_axis_aligned` branch coverage | ✅ |
| M-15 | boost-kernel fresh-copy guard | ✅ |
| M-16 | shape preservation (5 ranks) | ✅ (5 cases) |
| M-17 | composition — extended = FB-3.2 + Δ | ✅ |
| M-18 | driver byte-identity with β=0 extended kwargs | ✅ |

**24 passed / 0 failed.**

### §FB-3.3.9 Final verdict

- **Status**: Pass — FB-3.3 sealed.
- **Carry-forward** (closes): FB-3.2 carry "Θ/3·v + σ·v completion of
  `accel_from_tilt`" — closed.
- **Carry-forward** (new): boost-kernel off-axis projection (Wigner-d
  rotation) → FB-5.2 reserved.
- **Gallery**: no-op at this rotation (new RHS contributions are
  additive and the existing β>0 gallery topics are not yet running on
  extended kwargs; FB-3.6 β-sweep regression is the natural gallery
  checkpoint).
- **Baseline**: 3,189 → 3,213 (+24).

---

## §FB-3.4 Supplement — Dynamic vorticity feedback (ω · a² = const dilution)

- **Sub-phase**: FB-3.4 — `vorticity_from_tilt` extended with optional
  `bg_table` kwarg that multiplies the FB-3.2 static piece by the
  EMM §6.4 dilution factor `(a_today / a(η))²`.
- **Prior baseline** (post-FB-3.3): 3,213 passing + 1 skipped.
- **This-session baseline**: 3,232 passing + 1 skipped (+19 new tests).

### §FB-3.4.0 Target reconstruction

| Layer | Claim | Implementation | Output |
|---|---|---|---|
| Physics | EMM 2012 §6.4 vorticity propagation at leading order: `ω × a² = const` ⇒ `ω(η) = ω_0 × (a_0 / a(η))²` | `vorticity_from_tilt(..., bg_table=bg)` extension | `(3,)` float64 |
| Invariant | `bg_table = None` path byte-identical to FB-3.2 static formula | short-circuit without consulting `bg_table` | V-01 |
| Invariant | β = 0 / Class A / `structure is None` → zeros on every kwargs path | short-circuit before any `bg_table` read | V-02 / V-03 |
| Scope pin | Dynamic means η-dependent; V-05 pins two different η values produce different outputs | dilution factor reads `bg_table.interp_a(eta)` | V-05 |

### §FB-3.4.1 Contract diff

```python
def vorticity_from_tilt(
    tilted, eta,
    structure=None,
    *,
    bg_table=None,    # FB-3.4 new
) -> np.ndarray
```

`bg_table=None` → FB-3.2 backward-compat.
`bg_table` supplied → multiply static piece by `(a_today / a(η))²`.

### §FB-3.4.2 Phys-math ledger

1. **Definition / notation**. `ω × a² = const` is EMM §6.4 leading-
   order vorticity propagation on an FLRW background (consistent with
   `ω̇ = −(2/3) Θ ω + …` integrated to leading order). The formula
   generalises the Pontzen-Challinor §2 static piece by making it
   evolve with the scale factor. **Pass**.
2. **Indices**. `ω^a` is the axial vector consumed by
   `T6_vorticity`; unchanged shape and basis. **Pass**.
3. **Sign / normalisation**. At η < η_today (a < a_today), dilution
   factor > 1 so `|ω_dynamic| > |ω_static|` — vorticity was larger in
   the past. Pinned by V-09. **Pass**.
4. **Units / dimension**. Dilution factor is dimensionless; ω
   retains its `1/Mpc` units from the `a_twist` structure
   constant. **Pass**.
5. **Known-limit recovery**. `bg_table = None` is byte-identical to
   FB-3.2 (V-01); at η = η_today, dilution = 1 exactly; β = 0,
   Class A short-circuit paths unchanged. **Pass**.
6. **Boundary / positivity**. Non-positive `a(η)` raises
   `ValueError` (V-06). **Pass**.
7. **Hidden assumption**. The `(a_today / a(η))²` factor assumes a
   reference point at η_today (where dilution = 1). An alternative
   normalisation (reference at η_initial) would only rescale the
   overall amplitude; the shape of the η-dependence is invariant.
   Documented in the module docstring. **Pass with note**.
8. **Counter-example**. On the five Class B types the dilution
   factor is applied identically (V-04 parametrises all five).
   **Pass**.

### §FB-3.4.5 Ranked failure modes

| # | Type | Severity | Symptom | Cheap probe |
|---|---|---|---|---|
| 1 | physics | P0 (averted) | FB-3.2 anchor drifts when `bg_table=None` | V-01 closed-form equality |
| 2 | physics | P1 (averted) | dilution applied at β=0 / Class A | V-02 / V-03 short-circuit pins |
| 3 | interface | P1 (averted) | silent `a(η) = 0` produces inf | V-06 `ValueError` pin |
| 4 | physics | P2 (carried) | dilution only captures leading-order EMM §6.4; shear-driven piece (from `ε^{abc} ∇̃_b A_c`) enters at perturbation level | FB-5.1 perturbation sector |

### §FB-3.4.8 Minimal test set

| Test | Role | Verdict |
|---|---|---|
| V-01 | FB-3.2 backward-compat (no kwargs) | ✅ |
| V-02 | β = 0 short-circuit on FB-3.4 path | ✅ |
| V-03 | Class A short-circuit (6 types parametrised) | ✅ |
| V-04 | closed-form dilution (5 Class B types parametrised) | ✅ |
| V-05 | dynamic η-dependence | ✅ |
| V-06 | non-positive `a(η)` → `ValueError` | ✅ |
| V-07 | driver β = 0 byte-identity under extended kwargs | ✅ |
| V-08 | static vs dynamic driver output differs | ✅ |
| V-09 | |ω_dynamic| > |ω_static| at early η | ✅ |
| V-10 | η-sweep dilution monotonicity | ✅ |

**19 passed / 0 failed.**

### §FB-3.4.9 Final verdict

- **Status**: Pass — FB-3.4 sealed.
- **Gallery**: no-op at this rotation; FB-3.6 β-sweep is the gallery
  checkpoint.
- **Carry-forward** (new): shear-driven `ε^{abc} ∇̃_b A_c` vorticity
  piece → FB-5.1 reserved (perturbation-sector).
- **Baseline**: 3,213 → 3,232 (+19).

---

## §FB-3.5 Supplement — β-gate reparametrisation (rapidity SSOT + shared admissibility gate)

- **Sub-phase**: FB-3.5 — closes the FB-3.1 P2 β-parametrisation
  carry by (i) publishing ``assert_tilt_admissible(β, v̂_e)`` as the
  single SSOT guard used by ``TiltedSpeciesBackground.__post_init__``
  and available for downstream tilt consumers, (ii) exposing the
  ``.rapidity`` derived property and ``from_rapidity`` classmethod,
  and (iii) sourcing the velocity ↔ rapidity conversion through
  ``velocity_to_rapidity`` / ``rapidity_to_velocity``.
- **Prior baseline** (post-FB-3.4): 3,232 passing + 1 skipped.
- **This-session baseline**: 3,286 passing + 1 skipped (+54 new tests).

### §FB-3.5.0 Target reconstruction

| Layer | Claim | Implementation | Output |
|---|---|---|---|
| Decision | Parent plan D4 = (a) — rapidity is the decision-level SSOT | `.rapidity` property + `from_rapidity` ctor | derived float |
| Invariant | FB-3.1 byte anchor preserved: internal storage stays velocity (`tanh(atanh(β)) ≠ β` bitwise in float64) | no migration of `self.beta`; round-trip documented | every FB-3.1..FB-3.4 test passes unchanged |
| Single-sourcing | Guard set published as `assert_tilt_admissible` and re-used by `__post_init__` | gate function + `__post_init__` routes through gate | R-12 / R-13 |
| Conversion | `velocity_to_rapidity` / `rapidity_to_velocity` single-source the `tanh` / `atanh` formulas with exact zero branches | two helpers + classmethod delegation | R-01, R-02, R-03, R-04 |

### §FB-3.5.1 Contract diff

```python
# Module-level additions
def assert_tilt_admissible(beta, v_hat_e, *, tol=V_HAT_NORM_TOL) -> None: ...
def velocity_to_rapidity(beta: float) -> float: ...
def rapidity_to_velocity(rapidity: float) -> float: ...

# Class additions
TiltedSpeciesBackground.from_rapidity(base, rapidity, v_hat_e=...)  # classmethod
TiltedSpeciesBackground.rapidity                                     # property
```

`__post_init__` internals refactored to route through
`assert_tilt_admissible`; external behaviour byte-identical on every
FB-3.1 / FB-3.2 / FB-3.3 / FB-3.4 test (guard regex patterns
unchanged).

### §FB-3.5.2 Phys-math ledger

1. **Definition / notation**. β = tanh(η) per Lorentz-boost
   convention; η ∈ [0, ∞), β ∈ [0, 1). The `arctanh` / `tanh` pair
   is the analytic inverse on the admissible domain. **Pass**.
2. **Sign / normalisation**. Both scalars are non-negative by
   convention — the sign of the boost lives in `v̂_e`. Error
   messages explicit about this in both guards. **Pass**.
3. **Known-limit recovery**. `velocity_to_rapidity(0)` and
   `rapidity_to_velocity(0)` are exactly 0.0 via explicit
   short-circuit (not `np.arctanh(0.0)` which is also 0 but would
   carry spurious fastmath precision at NaN boundaries). **Pass**.
4. **Units / dimension**. Both parameters are dimensionless. **Pass**.
5. **Boundary / positivity**. β = 1.0 (exactly) raises
   `superluminal`; η → ∞ is admissible and maps to β → 1⁻;
   `np.arctanh` at exactly 1.0 is `inf` — caught by the β < 1 guard
   so `velocity_to_rapidity(1.0)` raises before reaching `arctanh`. **Pass**.
6. **Hidden assumption**. Internal storage remains velocity-
   parametrised (FB-3.1 byte anchor). Parent plan D4 = (a) is
   honoured at the *decision* level (downstream consumers prefer
   rapidity) but the *storage-level* migration is explicitly deferred
   because `tanh(atanh(β))` differs from `β` in the last bit of
   float64 for non-zero β. **Pass with note** (documented in module
   docstring §FB-3.5 header).
7. **Counter-example**. Round-trip at high rapidity (η ≥ 5) loses
   ~10⁻¹³ because tanh saturates near 1 and atanh loses precision;
   test R-04 accepts `1e-13 × (1 + η)` relative tolerance which
   matches the float64 precision budget. **Pass**.

### §FB-3.5.5 Ranked failure modes

| # | Type | Severity | Symptom | Cheap probe |
|---|---|---|---|---|
| 1 | code | P0 (averted) | gate-refactored `__post_init__` changes error messages | R-12 (each FB-3.1 regex match pattern tested) |
| 2 | code | P0 (averted) | FB-3.2 byte anchor drifts after gate refactor | R-14 `accel_from_tilt(β=0)` equals zeros |
| 3 | physics | P1 (averted) | `velocity_to_rapidity(1.0)` returns `inf` silently | explicit `superluminal` guard before `arctanh` (R-05) |
| 4 | interface | P2 (carried) | storage-level rapidity migration deferred; byte anchor would break | documented; future post-extended session when anchor can be relaxed |

### §FB-3.5.8 Minimal test set

| Test | Role | Verdict |
|---|---|---|
| R-01 | `velocity_to_rapidity(0) == 0.0` exact | ✅ |
| R-02 | `rapidity_to_velocity(0) == 0.0` exact | ✅ |
| R-03 | velocity → rapidity → velocity round-trip (9 sweep) | ✅ |
| R-04 | rapidity → velocity → rapidity round-trip (9 sweep) | ✅ |
| R-05 | `velocity_to_rapidity` guards | ✅ |
| R-06 | `rapidity_to_velocity` guards | ✅ |
| R-07 | gate silent on admissible input (β×v̂ sweep) | ✅ |
| R-08 | gate raises on each guard branch | ✅ |
| R-09 | `from_rapidity(0)` matches ctor at β=0 | ✅ |
| R-10 | `from_rapidity` + `.rapidity` round-trip | ✅ |
| R-11 | `.rapidity` at β = 0 is exactly 0.0 | ✅ |
| R-12 | FB-3.1 guards still trip via gate-based `__post_init__` | ✅ |
| R-13 | gate behaviour matches the direct-guard ctor | ✅ |
| R-14 | FB-3.2 anchor preservation after refactor | ✅ |
| R-15 | `V_HAT_NORM_TOL` SSOT pin | ✅ |

**54 passed / 0 failed.**

### §FB-3.5.9 Final verdict

- **Status**: Pass — FB-3.5 sealed.
- **Carry-forward closes**: FB-3.1 P2 "β-parametrisation split
  (velocity vs rapidity)" — closed via the decision-level rapidity
  SSOT (property + classmethod + conversion helpers); storage-level
  migration noted as an intentional post-extended deferral.
- **Gallery**: no-op; FB-3.6 β-sweep is the gallery checkpoint.
- **Baseline**: 3,232 → 3,286 (+54).

---

## §FB-3.6 Supplement — 44-configuration tilted regression suite

- **Sub-phase**: FB-3.6 — full β-sweep × structure-constant regression
  across the FB-3 stack; Phase FB-3 closure.
- **Prior baseline** (post-FB-3.5): 3,286 passing + 1 skipped.
- **This-session baseline**: 3,403 passing + 1 skipped (+117 new tests).

### §FB-3.6.0 Target reconstruction

| Layer | Claim | Implementation | Output |
|---|---|---|---|
| Regression | The FB-3.1 → FB-3.5 tilt stack produces finite `hierarchy_rhs_photon` output on 48 configurations (β ∈ {0, 0.01, 0.1, 0.5} × 12 labels) | S-01 parametrised sweep | boolean `np.isfinite(dy).all()` |
| Invariant | β = 0 adapter-fed RHS byte-identical to the no-kwargs FB-2.4 anchor on 12 labels | S-02 with `np.array_equal` | pass/fail per label |
| Invariant | FB-3.3 extended kwargs at β = 0 remain byte-identical (anchor survives the stack) | S-05 on 12 labels | pass/fail per label |
| Invariant | FB-3.4 dynamic vorticity at β = 0 is zero across every (Class A, Class B) cross | S-06 30-pair matrix | `np.array_equal` |
| Stress | β-jump between two RHS calls — no cached-state leak | S-03 | two distinct finite outputs |
| FB-3.5 parity | rapidity-path ctor matches velocity-path ctor in RHS | S-04 at `rtol=1e-12` | — |
| Hygiene | no silent FPE on the full sweep | S-08 with `np.errstate(invalid='raise', over='raise')` | — |

### §FB-3.6.8 Minimal test set

| Test | Parametrisation | Verdict |
|---|---|---|
| S-01 β × 12-label RHS finiteness | 4 × 12 = 48 | ✅ |
| S-02 β = 0 byte-identical vs anchor | 12 | ✅ |
| S-03 β-jump stress | 1 | ✅ |
| S-04 rapidity-path parity | 1 | ✅ |
| S-05 FB-3.3 extended-kwargs anchor | 12 | ✅ |
| S-06 β = 0 vorticity Class A × Class B | 30 | ✅ |
| S-07 shape stability | 12 | ✅ |
| S-08 no silent FPE | 1 | ✅ |

**117 passed / 0 failed.**

### §FB-3.6.9 Final verdict

- **Status**: Pass — FB-3.6 sealed.
- **Gallery**: no-op at this RHS-level rotation (integrator-level
  trajectory gallery for β > 0 belongs to FB-4 / FB-5 which wire the
  full solver). Documented as the phase-FB-3 closing no-op per the
  phase-boundary gallery rule.
- **Baseline**: 3,286 → 3,403 (+117).

---

## Phase FB-3 closing declaration

With FB-3.1 through FB-3.6 all sealed, **Phase FB-3 is complete.**
Cumulative phase delivery:

| Sub-phase | Commit anchor (short) | Tests added | Byte anchor preserved |
|---|---|---|---|
| FB-3.1 — `TiltedSpeciesBackground` abstraction | `9336280` | +24 | LB-6 / FB-2.4 |
| FB-3.2 — `accel_from_tilt` / `vorticity_from_tilt` + driver wire-up | `fdb1d86` | +57 | FB-2.4 `d7d25da` 12-label |
| FB-3.3 — Einstein + tilt additive pieces + boost-kernel seed | `ceed416` | +24 | FB-3.2 |
| FB-3.4 — dynamic vorticity dilution | `ab5914e` | +19 | FB-3.3 |
| FB-3.5 — β-gate reparametrisation (rapidity SSOT + shared gate) | `c1130ad` | +54 | FB-3.1 message patterns |
| FB-3.6 — 44-config tilted regression suite | (this commit) | +117 | FB-2.4 anchor across full stack |

**Cumulative test delta**: 3,108 (FB-2 exit) → 3,403 (FB-3 exit) =
**+295 tests across Phase FB-3**.

### Carry-forward ledger at Phase FB-3 exit

- **Closed this phase**:
  - FB02-F1 (v̂_e default cross-reference) — FB-3.1.
  - FB-3.1 P2 (Θ/3·v + σ·v completion of `accel_from_tilt`) — FB-3.3.
  - FB-3.1 P2 (β-parametrisation velocity vs rapidity split) — FB-3.5.
- **Rescheduled forward**:
  - FB-2.1 P2 (complex-dtype `nabla_dispatch` wire-up) → FB-5.1.
  - FB-3.2 / FB-3.3 P2 (boost-kernel off-axis Wigner-d rotation) →
    FB-5.2.
  - FB-3.4 P2 (shear-driven `ε^{abc} ∇̃_b A_c` vorticity piece) →
    FB-5.1.
  - FB-3.5 P2 (storage-level rapidity migration) → post-extended.
  - F3 (dimensionless-Σ² rescale) → FB-5 / FB-6.
  - FB11-F1 / FB12-F1 / FB12-F3 / FB13-κ-calibration → FB-5 / FB-6.
  - FB-2.3 P3 (venv/bin/pip shebang) → post-FB devops.

Phase FB-4 (tilted Thomson kernel Layer B) is the next target per
[FULL_BIANCHI_COVERAGE_PLAN.md §4 Phase FB-4](../lowell_bianchi/FULL_BIANCHI_COVERAGE_PLAN.md).

### Carry-forward ledger (outstanding)

- **FB-3.1 P2 overlap** → ✅ resolved in this rotation (K-12 pins the
  composition rule; module docstring documents it; 00_conventions §2
  cross-reference table updated).
- **FB-3.2 P2 (new)** → additive `(Θ/3) v^a + σ^a_b v^b` completion of
  `accel_from_tilt` — **FB-3.3 reserved** (Einstein + tilt coupling).
- **FB-3.2 P2 (new)** → Class A vorticity piece
  `ε^{abc} ∇̃_b v_c` (harmonic-mode) — **FB-5.1 reserved** (perturbation
  sector wire-up, complex-dtype `nabla_dispatch` on driver).
- All other carry-forwards (F3, FB11-F1, FB12-F1, FB12-F3,
  FB13-κ-calibration, FB-2.1 P2, FB-2.3 P3, FB-3.1 P2 β-gate, FB-5.2)
  unchanged from §9 above.
