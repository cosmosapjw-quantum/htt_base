# Phase FB-2 audit log — ∇̃ operator dispatch + hierarchy curved-space T-terms

**Phase**: FB-2 (Hierarchy RHS curved-space T-terms, 4 sessions)
**Parent plan**: `docs/lowell_bianchi/FULL_BIANCHI_COVERAGE_PLAN.md §4 FB-2`
**Predecessor audit**: `docs/audits/AUDIT_PHASE_FB1_2026-04-19.md` (Phase FB-1 exit declaration)
**Baseline at entry**: 2,997 passed + 1 skipped (post-FB-1.4 commit `e7af284`)
**Current rotation**: FB-2.1 completed; FB-2.2 / FB-2.3 / FB-2.4 pending.

---

## FB-2.1 — ∇̃ operator dispatch table (FLRW / I / V / VII_0 / IX)

**Session date**: 2026-04-19
**Commit target**: `FB-2.1: nabla_tilde dispatch for FLRW / I / V / VII_0 / IX harmonic modes`
**Exit test count**: 3,032 passed + 1 skipped (+35 new)

### §1 Audit target reconstruction

1. **Physical/mathematical claim**. The spatial covariant derivative
   `∇̃_a` on a Bianchi homogeneous 3-space admits a harmonic-mode
   diagonalisation: for a mode `Y_k(x)`,

        ∇̃_a Y_k = i k_a Y_k           (plane-wave family)
        ∇̃² Y_{ℓ,m} = -ℓ(ℓ+2) Y_{ℓ,m} (S³ discrete spectrum; Bianchi IX)

   Per-type specialisations — Harrison 1967 for Bianchi V hyperbolic
   harmonics (`∇̃² = -(k² + a²)`); Pontzen-Challinor 2007 eq (2.12) for
   VII_0 helical phase (trivialises on the symmetric line `n_1 = n_3`
   with mode aligned to the e_2 symmetry axis); Lifshitz-Khalatnikov
   1963 for Bianchi IX (closed S³ with `ℓ ≥ 1` cutoff).

2. **Algorithm**. Build a factory `make_nabla_tilde(structure, mode)`
   that returns a callable matching the existing
   `zero_nabla_operator(tensor, kind)` contract but with complex-valued
   output encoding the `i k_a` eigenvalue action. Expose
   `scalar_laplacian_eigenvalue(structure, mode)` separately for the
   Laplacian eigenvalue (needed by FB-5 for the perturbation-sector
   k-dispatch).

3. **Source of truth**. Implementation is source of truth for FB-2.1
   dispatch rules; `docs/lowell_bianchi/FULL_BIANCHI_COVERAGE_PLAN.md §4 FB-2.1`
   is the spec-level pointer; `lowell_bianchi_solver_reference.md §6`
   supplies the T-term equations that consume `∇̃`.

### §2 Contract / interface table

| Contract item | Value |
|---|---|
| Entry point | `bass.hierarchy.nabla_dispatch.make_nabla_tilde(structure, mode)` |
| Input | `StructureConstants` (11 types + FLRW); `HarmonicMode(type_label, k_vec: (3,), ell: Optional[int])` |
| Output | `Callable[[ndarray, str], ndarray]` with `kind ∈ {'gradient', 'divergence'}` |
| Output dtype | `complex128` (the `i` factor from `∇̃ = i k`) |
| Gradient convention | New axis prepended: shape `(3,) + tensor.shape` |
| Divergence convention | Contract last axis of tensor with `i k` (matches `T3_divergence` consumer) |
| Laplacian | `scalar_laplacian_eigenvalue(structure, mode) → float` |
| Error surface | `ValueError` for malformed mode / label mismatch; `NotImplementedError("FB-2.2")` / `NotImplementedError("FB-2.3")` / `NotImplementedError("FB-5.2")` for deferred scope |
| Dispatch partition | Disjoint: `SUPPORTED_FB21_TYPES` ∪ `DEFERRED_FB22_TYPES` ∪ `DEFERRED_FB23_TYPES` = {12 labels} |
| Invariant test | `test_fb21_dispatch_covers_all_11_bianchi_types_plus_flrw` enforces the partition at runtime |

### §3 Phys-math audit ledger

| Check | Verdict | Notes |
|---|---|---|
| `∇̃_a Y_k = i k_a Y_k` on FLRW (Ma-Bertschinger §4) | **pass** | `test_flrw_nabla_plane_wave_eigenmode` (rel 1e-12) |
| Type I = FLRW in Cartesian tetrad (n_i = a = 0) | **pass** | `test_typeI_nabla_matches_flrw` (bit-identical within rel 1e-12) |
| Type V Harrison eigenvalue `∇̃² = -(k² + a²)` | **pass** | `test_typeV_scalar_laplacian_includes_curvature_shift`, Harrison 1967 eq (4.5) |
| Type V → FLRW limit as `a_twist → 0` | **pass** | `test_typeV_flrw_limit_as_a_vanishes` (O(a²) continuity) |
| Type VII_0 axis-aligned symmetric-line reduction → FLRW | **pass** | `test_typeVII0_nabla_plane_wave_helical_phase_axis_aligned` + `..._scalar_laplacian_matches_flrw_on_axis` |
| VII_0 off-axis / asymmetric line → deferred to FB-5.2 | **pass** | explicit `NotImplementedError("FB-5.2")` with informative message |
| Type IX S³ eigenvalue `-ℓ(ℓ+2)` (Lifshitz-Khalatnikov §4) | **pass** | `test_typeIX_nabla_discrete_S3_spectrum[1..8]` + independence from `k_vec` magnitude |
| IX ℓ=0 constant mode rejected at construction | **pass** | `test_typeIX_rejects_ell_zero_constant_mode` |
| Divergence of scalar raises (rank-0 divergence undefined) | **pass** | `test_divergence_of_scalar_raises` |
| Dispatch completeness (12 labels partitioned) | **pass** | `test_fb21_dispatch_covers_all_11_bianchi_types_plus_flrw` |
| Label mismatch between structure + mode rejected | **pass** | `test_label_mismatch_raises` |
| Dimensional consistency (k in [1/Mpc], eigenvalue in [1/Mpc²]) | **pass** | inspection; consistent with Ellis §16 |
| Sign convention (`i k_a` with `(-, +, +, +)`) | **pass** | matches Ma-Bertschinger 1995; Ellis-Maartens-MacCallum §16.1 |

### §4 Equation-to-code mapping audit

| Equation | Code location | Verdict |
|---|---|---|
| `∇̃_a = i k_a` (plane wave) | `_plane_wave_operator` in `bass/hierarchy/nabla_dispatch.py:167-190` | pass — explicit `1j * k_vec` with correct axis dispatch |
| `gradient(Π_{ℓ-1})` ⇒ rank ℓ via `tensordot(..., axes=0)` | same | pass — new axis prepended, consistent with `zero_nabla_operator` convention (caller applies `sym_trace_free`) |
| `divergence(Π_{ℓ+1})` ⇒ rank ℓ contracting last axis | same | pass — matches `T3_divergence` consumer (`nabla_operator(·, 'divergence')` expects rank `ell` output) |
| Harrison hyperbolic offset `+ a²` | `scalar_laplacian_eigenvalue:362-365` | pass — Type V branch: `return -(k2 + a_twist²)` |
| IX eigenvalue `-ℓ(ℓ+2)` | `scalar_laplacian_eigenvalue:359-361` | pass — `return -float(ell * (ell + 2))` |
| VII_0 axis-aligned check `k_vec ∥ e_2 and n_1 = n_3` | `_validate_mode_typeVII0:237-258` | pass — explicit tolerance-aware check + explicit `NotImplementedError("FB-5.2")` for generic case |
| Deferred types: explicit `NotImplementedError` | `make_nabla_tilde:295-304` | pass — distinct FB-2.2 / FB-2.3 messages carry the roadmap pointer |
| No silent fallback to `zero_nabla_operator` | inspection | pass — `make_nabla_tilde` raises rather than returning a zero op |

### §5 Numerical / pipeline audit

| Item | Status | Notes |
|---|---|---|
| Dtype promotion float64 → complex128 | ok | explicit `.astype(np.complex128)` |
| Round-off on `1j * k_vec` | ok | eigenmode pin at rel 1e-12; well within ε_mach |
| Divergence-over-rank-0 guard | ok | raises `ValueError` with clear message |
| Invalid `kind` guard | ok | raises `ValueError("'gradient' or 'divergence'")` |
| Complex dtype vs real-dtype driver | **carry-forward** | `hierarchy_rhs_photon` is float64-only; FB-5 will wire the complex operator by splitting into real/imag part evolution. FB-2.1 exposes the dispatch as a standalone utility; no driver coupling yet. |
| Determinism | ok | pure functions; no global state; complex arithmetic is deterministic |
| No external code | ok | only `numpy` imports |
| Jacobi identity (structure constants) | ok | `StructureConstants` factories validate in-place; our validators re-check Class B twist constraints |

### §6 Ranked failure modes

- **None P0 / P1** identified.
- **P2 (carry-forward)** — Complex-valued dispatch not yet wired into
  `hierarchy_rhs_photon`. The FB-2.1 deliverable is the dispatch
  *table*; production wire-up is FB-5 when the harmonic-mode amplitude
  becomes a first-class state. Documented in §5.
- **P3 (future)** — VII_0 generic off-axis helical Wigner rotation
  (FB-5.2) — explicitly raised as `NotImplementedError("FB-5.2")` at
  dispatch time rather than silently approximated.

### §7 Verifier results

| Verifier | Result |
|---|---|
| A. Physics: known-limit recovery | **passed** (FLRW / Type I / V flat limit / VII_0 symmetric reduction / IX ℓ-spectrum) |
| A. Physics: dimensional consistency | **passed** ([k] = 1/Mpc; [∇̃²] = 1/Mpc²) |
| A. Physics: sign / normalisation | **passed** (i k_a convention; -|k|² Laplacian; -ℓ(ℓ+2) for IX) |
| A. Physics: admissibility (ell ≥ 1 on IX) | **passed** |
| B. Code: contract satisfaction | **passed** (`(tensor, kind) → ndarray` matches `zero_nabla_operator` signature modulo dtype) |
| B. Code: reproducibility | **passed** (pure function, no state) |
| B. Code: regression risk | **passed** (no existing code path calls `make_nabla_tilde` yet; FB-5 will wire it) |
| C. Numerical: tolerance robustness | **passed** (rel 1e-12 on all eigenmode pins) |
| C. Numerical: baseline reproducibility | **passed** (3,032 passed + 1 skipped; +35 new; pre-existing 2,997 unchanged) |
| C. Numerical: misspecification | **passed** (label mismatch, wrong ell, non-finite k, off-axis VII_0 all raise explicit errors) |

### §8 Minimal repair plan

- **None required**. No P0 / P1 issues surfaced.

### §9 Minimal test set (all present)

| Category | Test |
|---|---|
| Baseline reproduction | `test_flrw_nabla_plane_wave_eigenmode` (the FLRW reference Ma-Bertschinger eigenmode) |
| Edge / adversarial | `test_typeVII0_off_axis_mode_raises_fb52_notimplemented`, `test_typeIX_rejects_ell_zero_constant_mode`, `test_label_mismatch_raises` |
| Physics sanity | `test_typeV_scalar_laplacian_includes_curvature_shift`, `test_typeIX_nabla_discrete_S3_spectrum[1..8]` |
| Numerical stability | `test_typeV_flrw_limit_as_a_vanishes` (continuity O(a²) as `a_twist → 0`) |
| Regression / dispatch | `test_fb21_dispatch_covers_all_11_bianchi_types_plus_flrw` (partition invariant) |
| Deferred scope pins | 7 `NotImplementedError` tests across FB-2.2 / FB-2.3 / FB-5.2 deferrals |

### §10 Verdict

**통과 (pass)**. FB-2.1 dispatch table lands with 35 new tests, all
passing, and zero regression (2,997 → 3,032 pass + 1 skipped). The
`bass.hierarchy.contractions::NotImplementedError` referenced in the
FB-2.1 task description turned out to be a reference to the **cache
over-rank** guard (`stf_basis(ell > L_MAX_CACHED)`), not the ∇̃ hole:
the real ∇̃ hole lived in `bass/hierarchy/terms.py:zero_nabla_operator`
as the k=0 background default. FB-2.1 resolves this by introducing the
dispatch table **as a sibling utility** (`bass.hierarchy.nabla_dispatch`)
that FB-5 will wire into `hierarchy_rhs_photon` once the complex-valued
harmonic-mode amplitude becomes a first-class state.

**Do now (1 item)**: rotate `NEXT_SESSION_PROMPT §2` to FB-2.2.

**Do not touch (1 item)**: `hierarchy_rhs_photon`'s `zero_nabla_operator`
wire — the FB-2.1 operator is complex-valued; touching the driver's
real-dtype flow prematurely would cascade into all LB-5 / LB-6
regression fixtures. FB-5.1 owns the harmonic-mode amplitude state
machine.

### Phase FB-2.1 → FB-2.2 hand-off

FB-2.2 consumes the FB-2.1 deliverables — `HarmonicMode`,
`SUPPORTED_FB21_TYPES`, the dispatch partition — and:

1. Removes `"II"`, `"VI_0"`, `"VIII"` from `DEFERRED_FB22_TYPES`,
   moving them into `SUPPORTED_FB21_TYPES` (or a new
   `SUPPORTED_FB22_TYPES`).
2. Implements per-type mode validators for those three Class A types
   (II has only `n_1 > 0`; VI_0 has mixed sign; VIII has all n_i ≠ 0).
3. Wires the FB14-F1 twist-coupled anisotropic 3-Ricci correction
   (`W-E A²/(1+|h|)` piece in `S^{WE}_+`) in-place against the T1/T2
   spatial-Ricci hierarchy terms — this is the in-place calibration
   that FB-1.4 deferred.
4. Extends `test_fb21_dispatch_covers_all_11_bianchi_types_plus_flrw`
   (or adds an FB-2.2 sibling) to re-enforce the disjoint partition.

### Carry-forwards to FB-2.2 / FB-2.3 / FB-2.4

| Tag | Item | Target |
|---|---|---|
| FB-2.1 P2 | Complex-dtype operator not wired into `hierarchy_rhs_photon` (production flow still float-only) | FB-5.1 |
| FB14-F1 (from FB-1.4) | Class B twist-coupled aniso 3-Ricci correction (`W-E A²/(1+|h|)`) | FB-2.2 |
| F3 (from LB-5) | `TetradBackgroundState.shear_magnitude_sq` dimensionless-Σ² normalisation | FB-2.4 |
| FB-2.2 | Class A II / VI_0 / VIII ∇̃ implementation + spatial Ricci T1/T2 coupling | FB-2.2 (next session) |
| FB-2.3 | Class B III / IV / VI_h / VII_h ∇̃ twist coupling | FB-2.3 |
| FB-2.4 | T4–T7 wire-up (vorticity, 4-acceleration) for Class B / tilted types | FB-2.4 |
| FB-5.2 | VII_0 / VII_h generic off-axis helical Wigner rotation | FB-5.2 |

### Deliverables (diff summary)

| Item | File | Status |
|---|---|---|
| A | `bass/hierarchy/nabla_dispatch.py` — new module (dispatch + validators + Laplacian) | ✅ |
| B | `bass/hierarchy/test_nabla_dispatch.py` — 35 new tests | ✅ |
| C | `bass/hierarchy/__init__.py` — re-export `HarmonicMode`, `make_nabla_tilde`, `scalar_laplacian_eigenvalue`, and dispatch partition tuples | ✅ |
| D | `docs/audits/AUDIT_PHASE_FB2_2026-04-19.md` — this file (FB-2.1 supplement) | ✅ |
| E | `docs/lowell_bianchi/NEXT_SESSION_PROMPT.md §2` — rotated to FB-2.2 (Class A II / VI_0 / VIII ∇̃ + spatial Ricci T1/T2 + FB14-F1 twist correction calibration) | ✅ |

*End of FB-2.1 audit supplement.*
