# Development log — FB-3 through FB-7

**Purpose**: canonical ledger of every FB sub-phase from FB-3 onward.
Entries are append-only: once a row lands it is never rewritten; a
superseding fact is appended as a new row with a cross-reference.

**Parent**: [INDEX.md](INDEX.md).
**Parent plan**: [FULL_BIANCHI_COVERAGE_PLAN.md](../FULL_BIANCHI_COVERAGE_PLAN.md).

## Row format

Each entry has the following fields (absent fields are filled with
`—` rather than omitted):

- **Tag** — sub-phase label (e.g. `FB-3.2`).
- **Scope sentence** — one line describing what the session *shipped*.
- **Commit anchor** — short SHA of the merge commit on `main`.
- **Test delta** — `<before> → <after>` from the `bass/ tsc/` suite.
- **Audit document** — relative link to the `AUDIT_PHASE_*` entry.
- **Gallery status** — `regenerated` (new PNGs shipped), `no-op`
  (explicitly justified in the audit), or `deferred` (with the PR
  that will close the gap).
- **Carry-forward** — P2/P3 items that survived the audit.
- **Notes** — anything short that a reader needs to reconstruct the
  intent of the session.

---

## Phase FB-0 — Convention & dispatch SSOT

### FB-0.1 — Ellis Σ-convention flip

- **Scope**: Flipped the Σ-convention in
  [bass/background/einstein_bianchi.py](../../../htt/bass/background/einstein_bianchi.py)
  to Ellis-canonical `Σ_ab = a σ_ab`, closing the LB-5 F2 carry. LB-6
  tests re-anchored.
- **Commit**: see `git log --grep='FB-0.1'`.
- **Test delta**: pre-session 2,558 → 2,558 (+ re-anchored LB-6 tests).
- **Audit**: [AUDIT_PHASE_FB0_2026-04-19.md](../../audits/AUDIT_PHASE_FB0_2026-04-19.md).
- **Gallery**: regenerated (shear timeseries re-rendered under the
  new convention).
- **Carry-forward**: **F3** — `TetradBackgroundState.shear_magnitude_sq`
  still carries dimensional Σ²; dimensionless rescale deferred to
  FB-5 / FB-6 to avoid a cascading rename.

### FB-0.2 — Tilt-field surface

- **Scope**: Added `beta` and `v_hat_e` fields to
  [BianchiCosmology](../../../htt/bass/background/einstein_bianchi.py);
  no consumer wired yet.
- **Audit**: `AUDIT_PHASE_FB0_2026-04-19.md` §FB-0.2.
- **Gallery**: no-op.

### FB-0.3 — LB-6 F2 seal

- **Scope**: Added `eta_star` / `chi_star` keys to
  `detect_critical_events` output; LB-6 helper updated.
- **Audit**: `AUDIT_PHASE_FB0_2026-04-19.md` §FB-0.3.
- **Gallery**: no-op.

---

## Phase FB-1 — Per-type background validation

### FB-1.1 — Class A {I, II, VI_0, VII_0}

- **Scope**: `SOURCE_STATUS` for I / II / VI_0 / VII_0 promoted to
  `VALIDATED` against Wainwright-Ellis §18 Table 11.1 fixed points.
- **Audit**: [AUDIT_PHASE_FB1_2026-04-19.md](../../audits/AUDIT_PHASE_FB1_2026-04-19.md).
- **Carry-forward**: **FB11-F1** — W-E Table 11.1 fixed-point
  *coordinates* are not directly reachable at fixed N; rescheduled
  to FB-5 / FB-6.

### FB-1.2 — Class A {VIII, IX}

- **Scope**: VIII / IX shear sources validated; IX recollapse added
  as a `solve_ivp` event (`bianchi_ix_recollapse_event`).
- **Carry-forward**: **FB12-F1** (IX isotropic leading-order
  shear-source residual `S_+ = +(2/3) n² ℋ²`, W-E pathology);
  **FB12-F3** (the recollapse event function couples to `_hubble_squared`;
  refactor deferred). Both rescheduled to FB-5 / FB-6.

### FB-1.3 — Class B {III, IV, V, VI_h, VII_h}

- **Scope**: Twist-coupled shear sources validated. Type V open-FLRW
  limit confirmed. VII_h Pontzen-Challinor spiral matched
  qualitatively.
- **Carry-forward**: **FB13-κ-calibration** — quantitative κ
  calibration for the VII_h spiral deferred.

### FB-1.4 — `anisotropic_3_curvature` for all 11 types

- **Scope**: `TetradBackgroundState.aniso_3_curvature` is now
  non-None for every Bianchi type; FLRW / Type I / Type V remain
  explicitly zero.
- **Audit**: `AUDIT_PHASE_FB1_2026-04-19.md` §FB-1.4.
- **Gallery**: regenerated — topics 03 through 13 added to
  `figures/physics_gallery/`.

---

## Phase FB-2 — Hierarchy RHS curved-space T-terms

### FB-2.1 — ∇̃ on FLRW / I / V / VII_0 / IX harmonic modes

- **Scope**: 35 new tests; complex-dtype `nabla_dispatch` core.
- **Carry-forward**: **FB-2.1 P2** — complex-dtype dispatch not yet
  wired to the real-dtype `hierarchy_rhs_photon` driver. Reserved
  for FB-5.1 (harmonic-mode amplitude state machine).

### FB-2.2 — Class A {II, VI_0, VIII} ∇̃

- **Scope**: axis-aligned ∇̃ for II / VI_0 / VIII. T1 / T2 carry an
  optional `aniso_ricci_tensor` hook (FB-2.2). 24 new tests.
- **Carry-forward**: **FB14-F1** — `anisotropic_3_curvature`
  h-scaling calibration landed as part of this rotation.
- **Audit**: [AUDIT_PHASE_FB2_2026-04-19.md](../../audits/AUDIT_PHASE_FB2_2026-04-19.md).

### FB-2.3 — Class B {III, IV, VI_h, VII_h} ∇̃

- **Scope**: twist-coupled ∇̃ on the abelian (e_1, e_3) 2-plane.
  Harrison-V twist offset `a²/(1+|h|)` pinned. T1 Ricci
  auto-activation wired. 27 new tests.
- **Carry-forward**: **FB-2.3 P3 (env)** — `venv/bin/pip` shebang is
  stale after an interpreter change; rebuild deferred to post-FB
  devops.
- **Audit**: `AUDIT_PHASE_FB2_2026-04-19.md` §FB-2.3.

### FB-2.4 — Driver-level aniso-Ricci routing + T4..T7 structural pin

- **Commit anchor**: `d7d25da`.
- **Scope**: `hierarchy_rhs_photon` forwards
  `tetrad_state.aniso_3_curvature` through `aniso_ricci_at_eta`
  into T1 / T2. T4, T5, T6, T7 are structurally forwarded via
  `accel_vector` / `vorticity_vector` kwargs (no caller supplies
  them yet). F3 docstring correction applied. 12-label regression
  sweep added. 25 new tests.
- **Test delta**: 2,997 → 3,108.
- **Audit**: `AUDIT_PHASE_FB2_2026-04-19.md` §FB-2.4.
- **Gallery**: regenerated.
- **Notes**: Phase FB-2 closed with 111 tests across the four
  sessions. `d7d25da` is the byte-identical regression anchor used
  by every β = 0 adapter test from FB-3.2 onward.

---

## Phase FB-3 — Tilted sector (non-perturbative β)

### FB-3.1 — `TiltedSpeciesBackground` abstraction

- **Commit anchor**: `9336280`.
- **Scope**: Added
  [bass/species/tilted.py::TiltedSpeciesBackground](../../../htt/bass/species/tilted.py)
  with β=0 bit-identical short-circuit across all five LB-1 species
  (photon / neutrino / baryon / CDM / Λ) × 3-direction v̂_e sweep.
  EMM 2012 §5.4 equations (5.12)-(5.13) exact at β>0. Eager
  `ValueError` guards on β<0, β≥1, non-finite β, non-unit v̂_e.
  **FB02-F1** (v̂_e default cross-reference) resolved via the
  cross-reference table in
  [00_conventions.md §2](../00_conventions.md). 24 new tests.
- **Test delta**: 3,108 → 3,132.
- **Audit**: [AUDIT_PHASE_FB3_2026-04-19.md](../../audits/AUDIT_PHASE_FB3_2026-04-19.md)
  (Phase FB-3 entry declaration + FB-3.1 sections 0–9).
- **Gallery**: no-op (abstraction only — no new physical trajectory).
- **Carry-forward** (new P2):
  1. β-parametrisation split (velocity `TiltedSpeciesBackground`
     vs rapidity `TiltedVisibility`) — composition rule
     `v_e(η) = β × v̂_e` unifies; formal unification audit reserved
     for FB-3.5.
  2. Overlap with `bass.tilt.species_tilt.TiltedSpeciesParams`
     (Y-Block API accepting `v` directly). Addressed in FB-3.2.

### FB-3.2 — tilt-projected `A^a` / `ω^a` wire-up

- **Commit anchor**: `fdb1d86`.
- **Scope**: Added
  [bass/hierarchy/tilt_kinematics.py](../../../htt/bass/hierarchy/tilt_kinematics.py)
  with two adapters:
  - `accel_from_tilt(tilted, eta) → (3,)`: β=0 → fresh zeros;
    β>0 → `γ² v^a` (EMM eq 5.14 species-specific piece; King-Ellis
    1973 §3).
  - `vorticity_from_tilt(tilted, eta, structure=None) → (3,)`:
    β=0 → zeros; Class A (a_twist=0) → zeros; Class B →
    `(1/2) ε^{abc} a_b v_c` (Pontzen-Challinor 2009 §2).
  `hierarchy_rhs_photon` signature unchanged — adapters feed the
  FB-2.4 kwargs. β=0 adapter-fed driver RHS byte-identical to the
  no-kwargs baseline on all 12 structure-constant labels (FLRW + 11
  Bianchi types), pinned by `np.array_equal`. 57 new tests. FB-3.1
  P2 overlap closed via composition rule `v = β · v̂_e`.
- **Test delta**: 3,132 → 3,189.
- **Audit**: `AUDIT_PHASE_FB3_2026-04-19.md` §FB-3.2 Supplement.
- **Gallery**: no-op (β>0 trajectory integration deferred to FB-3.3
  per the non-goals pin).
- **Carry-forward** (new P2):
  1. Additive `(Θ/3) v^a + σ^a_b v^b` completion of
     `accel_from_tilt` — reserved for FB-3.3.
  2. Class A harmonic-mode vorticity piece
     `ε^{abc} ∇̃_b v_c` — reserved for FB-5.1.

---

## Phase FB-3 — forward anchors (FB-3.3 through FB-3.6)

These entries are planned, not shipped. Each row is superseded by a
"shipped" row once the corresponding PR lands; the "planned" row is
struck-through but retained for archaeology.

### FB-3.3 — Einstein + tilt coupling + boost-kernel seed

- **Scope**: `accel_from_tilt` extended with optional `bg_table` /
  `tetrad_state` kwargs that additively append the EMM eq (5.17)
  kinematic pieces `γ²(Θ/3) v^a + γ² σ^a_b v^b` to the FB-3.2
  placeholder; new `bass/hierarchy/boost_kernel.py` ships
  `boost_project_axisymmetric` with the linear Challinor 2000 eq
  (26) recurrence on the m=0 PSTF slice; off-axis `v̂_e` raises
  `NotImplementedError` (FB-5.2 reserved). `rhs_bianchi` already
  consumes tilt via its `family` dispatch (not re-opened here).
- **Commit anchor**: see `git log --grep='FB-3.3'`.
- **Test delta**: 3,189 → 3,213 (+24 tests in
  `bass/hierarchy/test_fb33_einstein_tilt.py`).
- **Audit**: `AUDIT_PHASE_FB3_2026-04-19.md` §FB-3.3 Supplement.
- **Gallery**: no-op (additive RHS; FB-3.6 β-sweep is the gallery
  checkpoint).
- **Carry-forward closed**: FB-3.2 P2 "(Θ/3)v + σ·v completion of
  `accel_from_tilt`".
- **Carry-forward new**: boost-kernel off-axis Wigner-d rotation →
  FB-5.2 reserved.

### FB-3.4 — Dynamic vorticity feedback

- **Scope**: `vorticity_from_tilt` gains optional `bg_table` kwarg.
  When supplied, the FB-3.2 static piece is multiplied by the
  EMM §6.4 dilution factor `(a_today / a(η))²` so T6 receives an
  η-dependent vorticity on β>0 × Class B. FB-3.2 backward-compat
  (no kwargs) preserved byte-for-byte; β=0 and Class A paths
  short-circuit before any `bg_table` read.
- **Test delta**: 3,213 → 3,232 (+19 tests in
  `bass/hierarchy/test_fb34_vorticity_feedback.py`).
- **Audit**: `AUDIT_PHASE_FB3_2026-04-19.md` §FB-3.4 Supplement.
- **Gallery**: no-op.
- **Carry-forward new**: shear-driven `ε^{abc} ∇̃_b A_c` vorticity
  piece → FB-5.1 reserved.

### FB-3.5 — β-gate reparametrisation (rapidity SSOT + shared gate)

- **Scope**: Publishes `assert_tilt_admissible(β, v̂_e)` as the
  single SSOT admissibility gate and routes
  `TiltedSpeciesBackground.__post_init__` through it. Adds
  `velocity_to_rapidity` / `rapidity_to_velocity` conversion
  helpers with exact zero branches; adds `.rapidity` property and
  `from_rapidity` classmethod so downstream consumers (FB-8
  `ObserverBoost`, FB-11 priors) can work in the rapidity surface
  without crossing the conversion boundary themselves. Internal
  storage stays velocity-parametrised (FB-3.1 byte anchor requires
  this; storage migration is an intentional post-extended deferral
  documented in the module docstring).
- **Test delta**: 3,232 → 3,286 (+54 tests in
  `bass/species/test_fb35_beta_gate.py`).
- **Audit**: `AUDIT_PHASE_FB3_2026-04-19.md` §FB-3.5 Supplement.
- **Gallery**: no-op.
- **Carry-forward closes**: FB-3.1 P2 β-parametrisation split
  (decision level; storage migration noted as post-extended).

### FB-3.6 — Tilted regression suite (Phase FB-3 closure)

- **Scope**: β × 12-label hierarchy RHS sweep (4 β × 12 labels = 48
  configs on S-01, plus focused anchor/regression checks) covering
  FB-3.1..FB-3.5 end-to-end. β=0 byte-identity preserved against
  the FB-2.4 anchor (`d7d25da`) on all 12 labels via S-02 and S-05.
  β-jump stress, rapidity-path parity, Class A × Class B
  vorticity cross, no silent FPE on the full sweep.
- **Test delta**: 3,286 → 3,403 (+117 tests in
  `bass/hierarchy/test_fb36_tilted_regression.py`).
- **Audit**: `AUDIT_PHASE_FB3_2026-04-19.md` §FB-3.6 Supplement +
  Phase FB-3 closing declaration.
- **Gallery**: no-op at this RHS-level rotation; integrator-level
  trajectory gallery belongs to FB-4 / FB-5 when the full solver
  wires through.
- **Phase FB-3 outcome**: sealed. Cumulative +295 tests across
  Phase FB-3 (3,108 → 3,403).

---

## Phase FB-4 (planned) — Tilted Thomson kernel Layer B

Planned sub-phases per [FULL_BIANCHI_COVERAGE_PLAN.md §4 Phase FB-4](../FULL_BIANCHI_COVERAGE_PLAN.md).
Bracket summary for bundle-completeness:

- **FB-META-4.0**: pre-flight scan complete; required reading closed,
  exact baseline confirmed, audit scaffold created before any
  skeleton plant.
- **FB-4.1**: full-Lorentz Thomson PSTF collision operator; β=0
  recovers the LB-4 kernel.
- **FB-4.2**: E↔B mixing under tilted LOS; `PolarizationHierarchyState`
  gains a B slot.
- **FB-4.3**: explicit `v_e²` Doppler 2nd-order corrections;
  Pontzen-Challinor cross-check.

Exit: β-sweep × polarisation regression. BB identically zero at
β=0; at β = 0.1, BB scales as ~10⁻¹ × EE (P-C reference).

### FB-META-4.0 — pre-flight scan + audit scaffolding

- **Scope**: Completed the FB-4 META pre-flight scan, read the six
  required sources, confirmed the exact `bass/ tsc/` baseline
  `3403 passed + 1 skipped`, and created the Phase FB-4 audit scaffold
  with empty `§FB-4.1` / `§FB-4.2` / `§FB-4.3` sections before any
  skeleton planting.
- **Commit anchor**: see `git log --grep='FB-META-4.0'`.
- **Test delta**: `3,403 passed + 1 skipped` →
  `3,403 passed + 1 skipped`.
- **Audit**: [AUDIT_PHASE_FB_META4_2026-04-20.md](../../audits/AUDIT_PHASE_FB_META4_2026-04-20.md).
- **Gallery**: no-op (META pre-flight only; no physics shipped).
- **Carry-forward**: —
- **Notes**: `htt/` remains unstaged by contract; subsequent
  FB-META-4.k commits advance one sub-phase at a time with docs-only
  staging and local skeleton-only code plants.

### FB-META-4.1 — full-Lorentz PSTF collision skeleton

- **Scope**: Recorded FB-4.1 three-channel verification, corrected the
  broken prompt-supplied Challinor arXiv ID to `astro-ph/9911481`,
  and planted the local-only
  `evaluate_tilted_thomson_pstf_collision(...)` skeleton plus one
  skipped contract test without staging any `htt/` changes.
- **Commit anchor**: see `git log --grep='FB-META-4.1'`.
- **Test delta**: `3,403 passed + 1 skipped` →
  `3,403 passed + 2 skipped`.
- **Audit**: [AUDIT_PHASE_FB_META4_2026-04-20.md](../../audits/AUDIT_PHASE_FB_META4_2026-04-20.md) §FB-4.1.
- **Gallery**: no-op (skeleton only; no physics shipped).
- **Carry-forward**: —
- **Notes**: the named on-disk Lowell solver-reference path is absent
  in this tree, so the audit records it as a broken internal locator;
  the historical `§11.3` text is recoverable from `HEAD` only.

### FB-META-4.2 — tilted E↔B mixing skeleton

- **Scope**: Recorded FB-4.2 three-channel verification and planted
  the local-only `evaluate_tilted_polarization_eb_collision(...)`
  skeleton plus one skipped contract test while keeping the shipped
  E-only polarization storage unchanged.
- **Commit anchor**: see `git log --grep='FB-META-4.2'`.
- **Test delta**: `3,403 passed + 2 skipped` →
  `3,403 passed + 3 skipped`.
- **Audit**: [AUDIT_PHASE_FB_META4_2026-04-20.md](../../audits/AUDIT_PHASE_FB_META4_2026-04-20.md) §FB-4.2.
- **Gallery**: no-op (skeleton only; no physics shipped).
- **Carry-forward**: —
- **Notes**: the orthogonal Type I `ψ' = 0` B-mode floor remains the
  named known-limit anchor for the future implementation.

### FB-META-4.3 — explicit `v_e²` Doppler skeleton

- **Scope**: Recorded FB-4.3 three-channel verification, noted that
  the prompt's Pontzen-Challinor anchor resolves on arXiv to
  `arXiv:0706.2075` submitted on 2007-06-14 while the Maartens 2011
  locator remained unverified, and planted the local-only
  `evaluate_tilted_second_order_doppler_correction(...)` skeleton
  plus one skipped contract test without staging any `htt/` changes.
- **Commit anchor**: see `git log --grep='FB-META-4.3'`.
- **Test delta**: `3,403 passed + 3 skipped` →
  `3,403 passed + 4 skipped`.
- **Audit**: [AUDIT_PHASE_FB_META4_2026-04-20.md](../../audits/AUDIT_PHASE_FB_META4_2026-04-20.md) §FB-4.3.
- **Gallery**: no-op (skeleton only; no physics shipped).
- **Carry-forward**: `arXiv:1104.0420` remains citation-needed if the
  future second-order path is ever re-opened.
- **Notes**: scope remains contract-only because
  `extended_coverage/SCOPE_DECISIONS.md §4` currently discards
  production `v_e²` Thomson terms; the planted helper is additive
  rather than an `order=2` kwarg on the shipped operator.

### FB-META-4.CLOSE — Phase FB-4 skeleton cycle closed

- **Scope**: Declared Phase FB-4 closed after the three skeleton-only
  sub-phases; no physics shipped and no `htt/` paths were staged at
  any point in the META cycle.
- **Commit anchor**: see `git log --grep='FB-META-4.CLOSE'`.
- **Test delta**: `3,403 passed + 4 skipped` →
  `3,403 passed + 4 skipped`.
- **Audit**: [AUDIT_PHASE_FB_META4_2026-04-20.md](../../audits/AUDIT_PHASE_FB_META4_2026-04-20.md) (Phase close note).
- **Gallery**: no-op.
- **Carry-forward**: FB-META-5 requires a fresh phase prompt rather
  than another inherited FB-4 handoff.
- **Notes**: `NEXT_SESSION_PROMPT.md §2` now intentionally contains
  only the generic FB-META-5 placeholder.

### FB-4.1 — axis-aligned Layer-B Thomson seed

- **Scope**: Replaced the FB-4.1 skeleton with an axis-aligned
  electron-frame boost sandwich around the LB-4 Thomson operator,
  preserving the exact `beta = 0` anchor and wiring the new Topic-10
  TT proxy plot plus the manuscript Layer-B section.
- **Commit anchor**: inherited branch state before the dedicated FB-4.2 / FB-4.3 commits; no standalone `FB-4.1:` commit was present on the current branch.
- **Test delta**: `3,401 passed + 73 skipped + 3 errors` →
  `3,425 passed + 72 skipped + 3 errors`.
- **Audit**: [AUDIT_PHASE_FB4_2026-04-20.md](../../audits/AUDIT_PHASE_FB4_2026-04-20.md) §FB-4.1.
- **Gallery**: rendered
  `figures/physics_gallery/10_collision_and_visibility/04_thomson_beta_sweep_Dl.png`.
- **Manuscript anchor**:
  `docs/manuscript/ch05_teff_corrections.tex §sec:tilted-thomson-layer-b`.
- **Carry-forward**: off-axis Wigner-d lift remains reserved for FB-5.2.

### FB-4.2 — axis-aligned E↔B collision seed

- **Scope**: Replaced the FB-4.2 skeleton with an axis-aligned
  same-`ell` E/B rotation seed, kept the orthogonal Type-I B floor
  exact, and added the Topic-10 BB/EE heatmap plus the matching
  manuscript subsection.
- **Commit anchor**: `96737f4` (`FB-4.2: axis-aligned E↔B collision seed`).
- **Test delta**: `3,425 passed + 72 skipped + 3 errors` →
  `3,448 passed + 71 skipped + 3 errors`.
- **Audit**: [AUDIT_PHASE_FB4_2026-04-20.md](../../audits/AUDIT_PHASE_FB4_2026-04-20.md) §FB-4.2.
- **Gallery**: rendered
  `figures/physics_gallery/10_collision_and_visibility/05_bb_from_tilted_lens_e.png`.
- **Manuscript anchor**:
  `docs/manuscript/ch05_teff_corrections.tex §sec:tilted-thomson-layer-b`.
- **Carry-forward**: arbitrary-direction polarization rotation remains reserved for FB-5.2.

### FB-4.3 — additive quadratic Doppler remainder

- **Scope**: Replaced the FB-4.3 skeleton with an additive
  `gamma_sq - 1` quadratic Doppler remainder, kept the zero-tilt path
  exact, and added the Topic-10 residual plot plus the matching
  manuscript subsection and audit note on the explicit scope demotion.
- **Commit anchor**: `e72e685` (`FB-4.3: additive quadratic Doppler remainder`).
- **Test delta**: `3,448 passed + 71 skipped + 3 errors` →
  `3,479 passed + 70 skipped + 3 errors`.
- **Audit**: [AUDIT_PHASE_FB4_2026-04-20.md](../../audits/AUDIT_PHASE_FB4_2026-04-20.md) §FB-4.3.
- **Gallery**: rendered
  `figures/physics_gallery/10_collision_and_visibility/06_doppler_second_order_residual.png`.
- **Manuscript anchor**:
  `docs/manuscript/ch05_teff_corrections.tex §sec:tilted-thomson-layer-b`.
- **Carry-forward**: literature-complete Thomson `v_e^2` term remains deferred until a verified source is recovered.

### FB-4.CLOSE — tilted Thomson Layer B

- **Scope**: Phase FB-4 is closed locally with Topic-10 plots `04`--`06`,
  the manuscript Layer-B section, the FB-4 audit supplement, and the
  handoff rotated to FB-5 actual work.
- **Commit anchor**: pending current close commit (`FB-4: Phase FB-4 complete (tilted Thomson Layer B)`).
- **Regression anchor**: `3,479 passed + 70 skipped + 3 errors`
  (same pre-existing CAMB fixture blocker at LB-6-19/20/21).
- **Next target**: `docs/lowell_bianchi/NEXT_SESSION_PROMPT.md §2`
  now points to FB-5 actual work.

---

## Phase FB-5 (planned) — Perturbation sector k ≠ 0

Planned sub-phases per parent §4 Phase FB-5.

- **FB-5.1**: per-type harmonic-mode decomposition; plane-wave /
  discrete IX `ℓ ≤ n` / VII_h spiral Q-modes. Also closes
  FB-2.1 P2 (complex-dtype dispatch wire-up) and the phase-0 audit
  "Full-mode D_2 collapse".
- **FB-5.2**: full ∇̃ operator (lowell §13) dispatched by mode;
  closes the FB-5.2 off-axis helical Wigner rotation carry.
- **FB-5.3**: CAMB regular adiabatic seed IC (lowell §13.2).
- **FB-5.4**: k=0 limit recovers LB-6 background; large-scale
  Sachs-Wolfe gate.
- **FB-5.5**: Class B mode quantisation including Type V Harrison
  hyperbolic harmonics.
- **FB-5.6**: tilted-boost seed rule (lowell §13.5) with
  PSTF-regularisation on the initial-value surface.
- **FB-5.7**: full k × type regression + audit.

Exit: Type I C_ℓ^{TT} baseline matches CAMB Planck-2018 `Dl_TT` to
within 5 % at ell ∈ [2, 30]. The phase-0 "ODE divergence for k > 0.03"
carry is addressed here.

---

## Phase FB-6 (planned) — 22-configuration regression suite

- **FB-6.1**: new `bass/integration/test_full_bianchi_coverage.py`;
  22 fixtures (11 types × {orthogonal, tilted}).
- **FB-6.2**: cross-type continuity checks — VII_h → VII_0 as h→0⁺,
  VI_h → III as h→-1, VII_0 → I as n→0, V → I as a→0, IX → BKL
  isotropic as n→0.
- **FB-6.3**: Pontzen-Challinor C_TT / off-diagonal cross-check for
  VII_h and IX; CAMB FLRW limit match for I / V / VII_0 / VII_h→0 /
  IX→BKL.

Exit: 22 configs green, 3 literature ground-truth shape matches.
The F3 dimensionless-Σ² rescale (FB-0.1 carry) closes here.

---

## Phase FB-7 (planned) — Spectrum + HTT + cosmological-frame likelihood

- **FB-7.1**: line-of-sight matrix propagator
  (`bass/spectrum/lowell_los.py`). Closes the phase-0 Limber `η_sp`
  sign-convention carry.
- **FB-7.2**: `C_ℓ^{TT,EE,TE,BB}` plus off-diagonal
  `C_{ℓm, ℓ'm'}` extraction.
- **FB-7.3**: HTT decomposition (lowell §14.2) + the P0 triad
  (prior alignment / tangency / β-gate).
- **FB-7.4**: direction-dependent likelihood (lowell §14.3) — tiered
  resolution. **Crucial caveat**: FB-7.4 delivers a
  *cosmological-frame* likelihood only. The observer-frame boost
  layer is deferred to FB-8 per [EXTENDED_COVERAGE_PLAN_FB8_FB9_FB11.md](EXTENDED_COVERAGE_PLAN_FB8_FB9_FB11.md).
- **FB-7.5**: Planck-2018 likelihood match at the FLRW limit.

Exit (parent plan M6): likelihood evaluator returns a stable ln B
for each of the 11 types given a synthetic Planck-2018-quality
dataset. At this point the parent plan's stated target is reached
*modulo* the observer-frame gap. The [extended plan](EXTENDED_COVERAGE_PLAN_FB8_FB9_FB11.md)
(FB-8 / FB-9 / FB-11) starts here.

---

## Baseline ledger (cumulative)

| Tag | Test count | Cumulative new tests since LB baseline |
|---|---|---|
| LB-6 exit | 2,558 | 0 |
| FB-0 exit | 2,558 | 0 (re-anchored only) |
| FB-1 exit | ~2,800 (estimate — see per-session audit) | ~240 |
| FB-2 exit | 3,108 | ~550 |
| FB-3.1 exit | 3,132 | +24 |
| FB-3.2 exit | 3,189 | +57 |
| FB-3.3 exit | 3,213 | +24 |
| FB-3.4 exit | 3,232 | +19 |
| FB-3.5 exit | 3,286 | +54 |
| FB-3.6 / Phase FB-3 exit | 3,403 | +117 |
| FB-META-4.0 pre-flight | 3,403 | +117 |
| FB-META-4.1 skeleton | 3,403 | +117 |
| FB-META-4.2 skeleton | 3,403 | +117 |

After each new FB row ships, append a new ledger row here with the
fresh cumulative count.

---

## Phase FB-META-5 — skeleton cycle (2026-04-20)

### FB-META-5.1 — harmonic-mode context skeleton

- **Scope**: Recorded FB-5.1 three-channel verification, corrected the
  prompt's Pontzen-Challinor anchor from the broken `astro-ph/0607373`
  locator to `arXiv:0706.2075`, and planted the local-only
  `make_harmonic_mode_rhs_context(...)` skeleton plus one skipped
  contract test without staging any `htt/` changes.
- **Commit anchor**: see `git log --grep='FB-META-5.1'`.
- **Test delta**: `3,403 passed + 4 skipped` →
  `3,403 passed + 5 skipped`.
- **Audit**: [AUDIT_PHASE_FB_META5_2026-04-20.md](../../audits/AUDIT_PHASE_FB_META5_2026-04-20.md) §FB-5.1.
- **Gallery**: no-op (skeleton only; no physics shipped).
- **Carry-forward**: historical Lowell solver-reference `§13.1` path
  remains absent on disk; FB-5.2 still owns the off-axis Wigner-d lift.
- **Notes**: the chosen surface wraps the existing FB-2 `HarmonicMode`
  SSOT instead of reopening the shipped real-dtype hierarchy driver.

### FB-META-5.2 — off-axis ``nabla_tilde`` skeleton

- **Scope**: Recorded FB-5.2 three-channel verification and planted the
  local-only `make_full_mode_nabla_tilde_operator(...)` skeleton plus
  one skipped contract test without staging any `htt/` changes. The
  arXiv-only channel verified the broad Bianchi hierarchy context but
  did not recover a specific Wigner-d locator, so that citation remains
  explicitly demoted to `# TODO`.
- **Commit anchor**: see `git log --grep='FB-META-5.2'`.
- **Test delta**: `3,403 passed + 5 skipped` →
  `3,403 passed + 6 skipped`.
- **Audit**: [AUDIT_PHASE_FB_META5_2026-04-20.md](../../audits/AUDIT_PHASE_FB_META5_2026-04-20.md) §FB-5.2.
- **Gallery**: no-op (skeleton only; no physics shipped).
- **Carry-forward**: exact off-axis Wigner-d citation still
  citation-needed; the missing Lowell solver-reference `§13` path
  remains unresolved on disk.
- **Notes**: scope stays in a separate factory on purpose so the
  already-audited FB-2 axis-aligned dispatch cannot be widened
  implicitly.

### FB-META-5.3 — regular adiabatic seed skeleton

- **Scope**: Recorded FB-5.3 three-channel verification, validated
  Ma-Bertschinger as the super-horizon adiabatic-seed anchor, rejected
  the prompt-supplied Lewis-Challinor `astro-ph/9911177` locator as a
  closed-FRW line-of-sight paper, and planted the local-only
  `make_camb_regular_adiabatic_seed(...)` skeleton plus one skipped
  contract test without staging any `htt/` changes.
- **Commit anchor**: see `git log --grep='FB-META-5.3'`.
- **Test delta**: `3,403 passed + 6 skipped` →
  `3,403 passed + 7 skipped`.
- **Audit**: [AUDIT_PHASE_FB_META5_2026-04-20.md](../../audits/AUDIT_PHASE_FB_META5_2026-04-20.md) §FB-5.3.
- **Gallery**: no-op (skeleton only; no physics shipped).
- **Carry-forward**: exact CAMB seed literature pin remains
  citation-needed; historical Lowell solver-reference `§13.2` path is
  still absent on disk.
- **Notes**: the chosen surface stays separate from the shipped
  `make_initial_state` zero-IC contract to avoid implying that the
  analytic k-dependent seed has already been sealed.

### FB-META-5.4 — ``k = 0`` limit gate skeleton

- **Scope**: Recorded FB-5.4 three-channel verification and planted the
  local-only `assert_k_zero_limit_matches_background(...)` skeleton
  plus one skipped contract test without staging any `htt/` changes.
  The external channel stayed honest: Sachs-Wolfe 1967 and
  Kolb-Turner 1990 remain `# TODO` because this session restricted
  verification to arXiv-only sources.
- **Commit anchor**: see `git log --grep='FB-META-5.4'`.
- **Test delta**: `3,403 passed + 7 skipped` →
  `3,403 passed + 8 skipped`.
- **Audit**: [AUDIT_PHASE_FB_META5_2026-04-20.md](../../audits/AUDIT_PHASE_FB_META5_2026-04-20.md) §FB-5.4.
- **Gallery**: no-op (skeleton only; no physics shipped).
- **Carry-forward**: textbook-only Sachs-Wolfe / Kolb references remain
  citation-needed in the arXiv-only channel.
- **Notes**: the chosen surface is an explicit validator rather than an
  integrator flag so the `k = 0` recovery check cannot become a hidden
  runtime branch.

### FB-META-5.5 — Class B mode-quantisation skeleton

- **Scope**: Recorded FB-5.5 three-channel verification and planted the
  local-only `quantise_class_b_mode(...)` skeleton plus one skipped
  contract test without staging any `htt/` changes. The local SSOT for
  the contract is the existing Class B twist / `h` structure already
  recorded in `nabla_dispatch.py` and `bianchi_types.py`.
- **Commit anchor**: see `git log --grep='FB-META-5.5'`.
- **Test delta**: `3,403 passed + 8 skipped` →
  `3,403 passed + 9 skipped`.
- **Audit**: [AUDIT_PHASE_FB_META5_2026-04-20.md](../../audits/AUDIT_PHASE_FB_META5_2026-04-20.md) §FB-5.5.
- **Gallery**: no-op (skeleton only; no physics shipped).
- **Carry-forward**: Harrison 1967 and Lyth-Stewart 1990 remain
  citation-needed in the arXiv-only channel.
- **Notes**: quantisation stays as a separate helper so the audited
  FB-2 `HarmonicMode` descriptor is not widened prematurely.

### FB-META-5.6 — tilted-seed-rule skeleton

- **Scope**: Recorded FB-5.6 three-channel verification and planted the
  local-only `apply_tilted_boost_seed_rule(...)` skeleton plus one
  skipped contract test without staging any `htt/` changes. The broad
  PSTF boost formalism is externally anchored to Challinor 2000, while
  the exact `boost then re-regularise on the initial surface` rule
  remains citation-needed.
- **Commit anchor**: see `git log --grep='FB-META-5.6'`.
- **Test delta**: `3,403 passed + 9 skipped` →
  `3,403 passed + 10 skipped`.
- **Audit**: [AUDIT_PHASE_FB_META5_2026-04-20.md](../../audits/AUDIT_PHASE_FB_META5_2026-04-20.md) §FB-5.6.
- **Gallery**: no-op (skeleton only; no physics shipped).
- **Carry-forward**: exact Lowell `§13.5` tilted-seed text remains
  unavailable on disk; the stronger initial-surface regularisation
  claim is still `# TODO` in the arXiv-only channel.
- **Notes**: tilt regularisation stays as a post-seed helper so the
  orthogonal seed contract from FB-5.3 remains separate and explicit.

### FB-META-5.7 — ``k × type`` regression skeleton

- **Scope**: Recorded FB-5.7 three-channel verification and planted the
  local-only `run_k_type_regression_matrix(...)` skeleton plus one
  skipped contract test without staging any `htt/` changes. The
  regression oracle remains the existing Planck/CAMB policy already
  pinned in `test_lowell_bianchi.py`.
- **Commit anchor**: see `git log --grep='FB-META-5.7'`.
- **Test delta**: `3,403 passed + 10 skipped` →
  `3,403 passed + 11 skipped`.
- **Audit**: [AUDIT_PHASE_FB_META5_2026-04-20.md](../../audits/AUDIT_PHASE_FB_META5_2026-04-20.md) §FB-5.7.
- **Gallery**: no-op (skeleton only; no physics shipped).
- **Carry-forward**: exact Planck table-level `Dl_TT` locator remains
  citation-needed if the future regression needs a direct table quote.
- **Notes**: the chosen surface makes the future coverage grid explicit
  rather than hiding it only inside a parametrized test decorator.

### FB-META-5.CLOSE — Phase FB-5 skeleton cycle closed

- **Scope**: Declared Phase FB-5 skeleton-only rotation closed after
  seven local perturbation skeleton plants, a final full regression, and
  the handoff rotation to the generic FB-META-6 placeholder. No `htt/`
  paths were staged at any point in the cycle.
- **Commit anchor**: see `git log --grep='FB-META-5.CLOSE'`.
- **Test delta**: `3,403 passed + 11 skipped` →
  `3,403 passed + 11 skipped`.
- **Audit**: [AUDIT_PHASE_FB_META5_2026-04-20.md](../../audits/AUDIT_PHASE_FB_META5_2026-04-20.md) (Phase close note).
- **Gallery**: no-op.
- **Carry-forward**: FB-META-6 requires a fresh phase prompt rather
  than an inherited FB-5 task list.
- **Notes**: final regression count matched the phase-entry baseline in
  passes and increased skips only by the seven intended contract tests.

---

## Phase FB-META-6 — skeleton cycle (2026-04-20)

### FB-META-6.1 — 22-configuration regression-harness skeleton

- **Scope**: Recorded FB-6.1 three-channel verification, normalized the
  Pontzen paper split (`arXiv:0901.2122` as the 2009 figure-bearing
  paper; `arXiv:0706.2075` as the earlier 2007 hierarchy paper), and
  planted the committed
  `htt/bass/integration/test_full_bianchi_coverage.py` harness with an
  explicit 22-row `{11 types} × {orthogonal, tilted}` matrix.
- **Commit anchor**: see `git log --grep='FB-META-6.1'`.
- **Test delta**: `3,403 passed + 11 skipped` →
  `3,403 passed + 33 skipped`.
- **Audit**: [AUDIT_PHASE_FB_META6_2026-04-20.md](../../audits/AUDIT_PHASE_FB_META6_2026-04-20.md) §FB-6.1.
- **Gallery**: no-op (skeleton only; no physics shipped).
- **Carry-forward**: the named continuity-limit tuples are reserved for
  FB-6.2; the literature/CAMB oracle-fixture paths are reserved for
  FB-6.3; the Cambridge preview still does not expose the full W-E
  `§11.1` table text in-session.
- **Notes**: the flat 22-row list was chosen over a generated cross
  product so the future coverage declaration is reviewable without
  helper indirection.

### FB-META-6.2 — cross-type continuity-limit skeleton

- **Scope**: Recorded FB-6.2 three-channel verification and extended
  `htt/bass/integration/test_full_bianchi_coverage.py` with the five
  named continuity-limit tuples only, keeping the committed FB-6.1
  22-row matrix unchanged. The source trail is explicit: `arXiv:0901.2122`
  for the open/flat and closed limit statements, plus the local SSOT and
  Ellis-MacCallum 1969 for `III = VI_{-1}`.
- **Commit anchor**: see `git log --grep='FB-META-6.2'`.
- **Test delta**: `3,403 passed + 33 skipped` →
  `3,403 passed + 38 skipped`.
- **Audit**: [AUDIT_PHASE_FB_META6_2026-04-20.md](../../audits/AUDIT_PHASE_FB_META6_2026-04-20.md) §FB-6.2.
- **Gallery**: no-op (skeleton only; no physics shipped).
- **Carry-forward**: literature/CAMB oracle-fixture paths remain
  reserved for FB-6.3; the Cambridge preview still does not expose the
  W-E `§18` table text directly.
- **Notes**: explicit named tuples were chosen over a helper builder so
  the one-sided and isotropic-branch semantics remain reviewable in the
  test file itself.

### FB-META-6.3 — literature/CAMB oracle-fixture skeleton

- **Scope**: Recorded FB-6.3 three-channel verification and extended
  `htt/bass/integration/test_full_bianchi_coverage.py` with reserved
  literature/CAMB oracle paths only. The 2009 Pontzen locator was
  corrected in-flight: the verified `arXiv:0901.2122` text has Figures 1
  and 3 plus a `§IV` closed-model discussion, not the prompt's
  "Fig. 4 + §IV" pairing.
- **Commit anchor**: see `git log --grep='FB-META-6.3'`.
- **Test delta**: `3,403 passed + 38 skipped` →
  `3,403 passed + 48 skipped`.
- **Audit**: [AUDIT_PHASE_FB_META6_2026-04-20.md](../../audits/AUDIT_PHASE_FB_META6_2026-04-20.md) §FB-6.3.
- **Gallery**: no-op (skeleton only; no physics shipped).
- **Carry-forward**: the phase-close pass is next; the off-diagonal
  literature rows remain reserved placeholders until numeric fixtures
  actually land.
- **Notes**: CAMB rows intentionally reuse the shipped
  `data/camb_ref_planck2018.npz` path, while future digitized
  Pontzen-Challinor baselines are reserved under `tests/fixtures/fb6/`.

### FB-META-6.CLOSE — Phase FB-6 skeleton cycle closed

- **Scope**: Declared the Phase FB-6 skeleton-only rotation closed after
  three committed integration-harness plants, a final full regression,
  and the handoff rotation to the generic FB-META-7 placeholder.
- **Commit anchor**: see `git log --grep='FB-META-6.CLOSE'`.
- **Test delta**: `3,403 passed + 48 skipped` →
  `3,403 passed + 48 skipped`.
- **Audit**: [AUDIT_PHASE_FB_META6_2026-04-20.md](../../audits/AUDIT_PHASE_FB_META6_2026-04-20.md) (Phase close note).
- **Gallery**: no-op.
- **Carry-forward**: FB-META-7 requires a fresh phase prompt rather
  than an inherited FB-6 task list.
- **Notes**: final regression count matched the FB-6.3 state exactly,
  so the phase closes with unchanged passes and only the intended 37
  new skipped harness cases over the phase-entry baseline.

---

## Phase FB-META-7 — skeleton cycle (2026-04-20)

### FB-META-7.0 — pre-flight scan + audit scaffolding

- **Scope**: Completed the FB-7 META pre-flight scan, read the seven
  required sources plus the local Lowell-reference fallback, confirmed
  the exact `bass/ tsc/` baseline `3403 passed + 48 skipped`, and
  created the Phase FB-7 audit scaffold with empty `§FB-7.1` through
  `§FB-7.5` sections before any skeleton planting.
- **Commit anchor**: see `git log --grep='FB-META-7.0'`.
- **Test delta**: `3,403 passed + 48 skipped` →
  `3,403 passed + 48 skipped`.
- **Audit**: [AUDIT_PHASE_FB_META7_2026-04-20.md](../../audits/AUDIT_PHASE_FB_META7_2026-04-20.md).
- **Gallery**: no-op (META pre-flight only; no physics shipped).
- **Carry-forward**: the prompt-supplied
  `docs/lowell_bianchi/lowell_bianchi_solver_reference.md` path is
  absent in this worktree; the tracked fallback for this phase is
  `htt/docs/lowell_bianchi_solver_reference_PR_WBS.md`.
- **Notes**: unlike FB-META-4 / FB-META-5, this cycle will commit
  additive `htt/bass/` skeleton modules. Every FB-7.4 artifact must pin
  the scope as cosmological-frame only, with observer-frame composition
  deferred to FB-8.

### FB-META-7.1 — line-of-sight matrix propagator skeleton

- **Scope**: Recorded FB-7.1 three-channel verification and planted the
  committed `htt/bass/spectrum/lowell_los.py` skeleton plus one skipped
  contract test. The all-type LOS builder stays separate from the
  shipped Bianchi-I-only `bass/los/bianchi_propagator.py`, and the
  phase-0 Limber `η_sp` sign carry is made explicit in the new
  signature.
- **Commit anchor**: see `git log --grep='FB-META-7.1'`.
- **Test delta**: `3,403 passed + 48 skipped` →
  `3,403 passed + 49 skipped`.
- **Audit**: [AUDIT_PHASE_FB_META7_2026-04-20.md](../../audits/AUDIT_PHASE_FB_META7_2026-04-20.md) §FB-7.1.
- **Gallery**: no-op (skeleton only; no physics shipped).
- **Carry-forward**: the exact on-disk Lowell `§7` locator remains
  absent in this worktree, so the docstring keeps that citation as an
  explicit `# TODO` rather than inventing a file path.
- **Notes**: a new spectrum-side module was chosen over widening the
  audited Type-I LOS scaffold or mixing LOS construction into
  `cl_assembly.py`.

### FB-META-7.2 — diagonal plus off-diagonal spectrum skeleton

- **Scope**: Recorded FB-7.2 three-channel verification and planted the
  committed `htt/bass/spectrum/off_diagonal_covariance.py` skeleton plus
  one skipped contract test. The contract reserves diagonal
  `C_ell^{TT,EE,TE,BB}` and off-diagonal `C_{ℓm,ℓ' m'}` extraction
  together, with the default strategy pinned as `m_decoupled_blocks`.
- **Commit anchor**: see `git log --grep='FB-META-7.2'`.
- **Test delta**: `3,403 passed + 49 skipped` →
  `3,403 passed + 50 skipped`.
- **Audit**: [AUDIT_PHASE_FB_META7_2026-04-20.md](../../audits/AUDIT_PHASE_FB_META7_2026-04-20.md) §FB-7.2.
- **Gallery**: no-op (skeleton only; no physics shipped).
- **Carry-forward**: the prompt-supplied Pontzen-Challinor locator
  `astro-ph/0607373` is explicitly retired here; the corrected external
  Bianchi anchor is `arXiv:0706.2075`.
- **Notes**: the new module preserves the audited diagonal-only
  `cl_assembly.py` surface and makes the off-diagonal strategy visible
  in the signature instead of hiding it in helper logic.

### FB-META-7.3 — HTT decomposition and P0-triad skeleton

- **Scope**: Recorded FB-7.3 three-channel verification and introduced
  the committed `htt/bass/likelihood/` package with
  `htt_decomposition.py` plus one skipped contract test. The new
  decomposition surface takes `prior_alignment`, `TangencyResult`, and
  `CanonicalDecision` explicitly so the P0 triad remains auditable at
  FB-7.3 rather than being hidden inside the later likelihood builder.
- **Commit anchor**: see `git log --grep='FB-META-7.3'`.
- **Test delta**: `3,403 passed + 50 skipped` →
  `3,403 passed + 51 skipped`.
- **Audit**: [AUDIT_PHASE_FB_META7_2026-04-20.md](../../audits/AUDIT_PHASE_FB_META7_2026-04-20.md) §FB-7.3.
- **Gallery**: no-op (skeleton only; no physics shipped).
- **Carry-forward**: the exact on-disk Lowell `§14.2` locator remains
  absent in this worktree, so the skeleton docstring keeps that citation
  as an explicit TODO.
- **Notes**: the BASS-side likelihood package is introduced here so
  FB-7.4 and the later FB-8 observer-frame adapter have a solver-owned
  home distinct from the legacy `htt/htt/` inference stack.

### FB-META-7.4 — cosmological-frame likelihood skeleton

- **Scope**: Recorded FB-7.4 three-channel verification and added the
  committed `CosmologicalFrameLikelihood` skeleton plus one skipped
  contract test. The class docstring pins the scope as cosmological-
  frame only and names `bass.likelihood.observer_frame_adapter` as the
  FB-8 layer that composes observer-frame effects on top.
- **Commit anchor**: see `git log --grep='FB-META-7.4'`.
- **Test delta**: `3,403 passed + 51 skipped` →
  `3,403 passed + 52 skipped`.
- **Audit**: [AUDIT_PHASE_FB_META7_2026-04-20.md](../../audits/AUDIT_PHASE_FB_META7_2026-04-20.md) §FB-7.4.
- **Gallery**: no-op (skeleton only; no physics shipped).
- **Carry-forward**: the exact on-disk Lowell `§14.3` locator remains
  absent in this worktree, so the skeleton keeps that citation as an
  explicit TODO rather than implying the file exists.
- **Notes**: a named class was chosen over a bare callable because the
  FB-8 observer-frame adapter SDD already expects a
  `CosmologicalFrameLikelihood` type.

### FB-META-7.5 — Planck-2018 FLRW-limit validation skeleton

- **Scope**: Recorded FB-7.5 three-channel verification and added the
  committed `validate_planck2018_flrw_limit_match(...)` skeleton plus
  one skipped contract test. The contract names the shipped
  `data/camb_ref_planck2018.npz` oracle directly and keeps the two
  relevant Planck papers distinct: V (`1907.12875`) for the likelihood
  and VI (`1807.06209`) for the base-ΛCDM parameter baseline embedded in
  the fixture metadata.
- **Commit anchor**: see `git log --grep='FB-META-7.5'`.
- **Test delta**: `3,403 passed + 52 skipped` →
  `3,403 passed + 53 skipped`.
- **Audit**: [AUDIT_PHASE_FB_META7_2026-04-20.md](../../audits/AUDIT_PHASE_FB_META7_2026-04-20.md) §FB-7.5.
- **Gallery**: no-op (skeleton only; no physics shipped).
- **Carry-forward**: the full-stack FLRW validator itself remains
  unimplemented; only the oracle provenance contract is planted here.
- **Notes**: the validator is kept separate from runtime likelihood
  construction so the phase-exit oracle policy stays independently
  auditable.

### FB-META-7.CLOSE — Phase FB-7 skeleton cycle closed

- **Scope**: Declared the Phase FB-7 skeleton-only rotation closed after
  five committed spectrum/likelihood skeleton plants, a final full
  regression, the handoff rotation to the generic FB-META-8
  placeholder, and creation of the successor
  `DEVELOPMENT_LOG_FB8_ONWARD.md` header for the extended bundle.
- **Commit anchor**: see `git log --grep='FB-META-7.CLOSE'`.
- **Test delta**: `3,403 passed + 53 skipped` →
  `3,403 passed + 53 skipped`.
- **Audit**: [AUDIT_PHASE_FB_META7_2026-04-20.md](../../audits/AUDIT_PHASE_FB_META7_2026-04-20.md) (Phase close note).
- **Gallery**: no-op.
- **Carry-forward**: FB-META-8 requires a fresh phase prompt rather
  than an inherited FB-7 task list; the exact Lowell `§7` / `§14.2` /
  `§14.3` on-disk locators remain absent and explicit.
- **Notes**: final regression count matched the intended +5 skip delta,
  and the FB-7.4 scope distinction remains pinned as
  cosmological-frame-only with observer-frame composition deferred to
  FB-8.
