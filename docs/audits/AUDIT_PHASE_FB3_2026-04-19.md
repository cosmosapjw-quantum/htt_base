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
