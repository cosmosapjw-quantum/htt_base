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

---

## FB-2.2 — Class A II / VI_0 / VIII ∇̃ axis-aligned dispatch + T1/T2 spatial-Ricci wire-up + FB14-F1 twist calibration

**Session date**: 2026-04-19
**Commit target**: `FB-2.2: Class A II / VI_0 / VIII nabla_tilde + T1/T2 spatial-Ricci wire-up + FB14-F1 calibration`
**Parent commit at entry**: `5765e0b` (HEAD before FB-2.2) — pre-FB-2.2 baseline 3,032 passed + 1 skipped
**Exit test count**: 3,056 passed + 1 skipped (+24 new)

### §1 Audit target reconstruction

1. **Physical/mathematical claim**. The ``∇̃`` harmonic-mode dispatch
   extends to the remaining Class A Bianchi types — II / VI_0 / VIII —
   on each type's **abelian subalgebra** of the underlying Lie
   algebra. On the abelian subalgebra the Lie bracket vanishes so a
   plane-wave mode ``e^{i k·x}`` is an exact eigenmode of the spatial
   Laplacian, and ``∇̃_a Y = i k_a Y`` acts as on FLRW. The non-abelian
   directions are reserved for FB-5.2 (Wigner rotation for the
   semisimple VIII, Grushin harmonic-oscillator reduction for the
   nilpotent II, hyperbolic Lorentz action for VI_0).

   Additionally, the hierarchy RHS ``T1`` and ``T2`` functions receive
   a structural **spatial-Ricci hook**: an optional
   ``aniso_ricci_tensor`` kwarg that ingests the anisotropic 3-Ricci
   ``³R_ab^{aniso}`` from ``TetradBackgroundState.aniso_3_curvature``
   (FB-1.4 deliverable). ``T1`` receives a rank-preserving
   ``T8``-style contraction with prefactor ``ℓ/(2ℓ+3)``; ``T2``
   receives a ``∇̃ ³R_ab`` hook that is **zero at background** (the
   Ricci is spatially homogeneous in the left-invariant tetrad) and
   participates in the FB-5 complex-dtype wire-up transparently. Both
   terms' default kwargs (``None``) preserve bit-identical LB-6
   regression.

   Finally, **FB14-F1** (FB-1.4 P3 carry-forward) is calibrated in
   place via new regression tests that pin the ``(2/3) A²/(1+|h|)``
   piece of the Class B W-E ``S^{WE}_+`` source (already present in
   ``shear_sources.py::source_VIh`` / ``source_VIIh``) against the
   closed-form h-scaling for two ``a_twist`` configurations sharing
   ``(n_1, n_3)``. This upgrades the pre-existing rel 1e-12
   formula pin to include a parameter-sweep consistency check.

2. **Algorithm**.
   * Add ``II``, ``VI_0``, ``VIII`` to ``SUPPORTED_FB22_TYPES`` with
     per-type validators checking the axis-aligned subset (``II``:
     ``k_vec = (k_1, 0, 0)``; ``VI_0``: ``k_2 = 0``; ``VIII``:
     ``k_vec = (k_1, 0, 0)``).  Off-axis modes raise
     ``NotImplementedError("FB-5.2")``.
   * Drop ``II / VI_0 / VIII`` from ``DEFERRED_FB22_TYPES`` (now
     empty; retained only as a backward-compatible import).
   * Extend ``scalar_laplacian_eigenvalue`` with branches for II
     (``λ = −k_1²``), VI_0 (``λ = −(k_1² + k_3²)``), VIII
     (``λ = −k_1²``).
   * Augment ``T1_expansion`` signature with
     ``aniso_ricci_tensor: Optional[np.ndarray]``. Coupling form:
     ``(ℓ/(2ℓ+3)) · PSTF[ ³R^b_{⟨a_ℓ} Π_{A_{ℓ−1}⟩ b} ]``. At ℓ = 0
     or ``aniso_ricci_tensor = None``: no addition.
   * Augment ``T2_gradient`` signature with ``aniso_ricci_tensor``.
     Coupling form: PSTF contraction of ``∇̃_c ³R_ab`` with
     ``Π_{A_{ℓ−1}}``. At background (``zero_nabla_operator``):
     identically zero (the hook is structural, not load-bearing).

3. **Source of truth**. Implementation is the authoritative source
   for FB-2.2 dispatch rules; the docstrings now cross-reference
   Wainwright-Ellis 1997 §1.4.4 (Class A Lie algebras) and
   Ellis-Maartens-MacCallum 2012 §14.3 (spatial-Ricci lift).

### §2 Contract / interface table

| Contract item | Value |
|---|---|
| Supported FB-2.2 types | ``II``, ``VI_0``, ``VIII`` (abelian subalgebra axis-aligned) |
| II abelian subalgebra | ``span{e_1}`` (Heisenberg center) |
| VI_0 abelian subalgebra | ``span{e_1, e_3}`` (``[e_1, e_3] = n_2 e_2 = 0``) |
| VIII abelian subalgebra | ``span{e_1}`` (Cartan; sign-different ``n_1 < 0``) |
| Off-axis → FB-5.2 | Non-zero ``k_2`` on II or VI_0; non-zero ``k_2, k_3`` on VIII |
| Laplacian II | ``λ = −k_1²`` |
| Laplacian VI_0 | ``λ = −(k_1² + k_3²)`` |
| Laplacian VIII | ``λ = −k_1²`` |
| T1 Ricci hook | ``(ℓ/(2ℓ+3)) · sym_trace_free(Π_ℓ · ³R)`` |
| T2 Ricci hook | ``sym_trace_free( ∇̃³R ⊗ Π_{ℓ-1} )`` — zero at background |
| Dispatch partition | ``SUPPORTED_TYPES = FB21 ∪ FB22`` disjoint from ``DEFERRED_FB23_TYPES``; ``DEFERRED_FB22_TYPES = ()`` |
| FB14-F1 invariant | ``(2/3) A²/(1+|h|)`` piece verified on two-config h-scaling |

### §3 Phys-math audit ledger

| Check | Verdict | Notes |
|---|---|---|
| Type II plane-wave on ``e_1`` center, ``∇̃ Y = i k_1 Y e_1`` | **pass** | `test_typeII_nabla_heisenberg_mode` rel 1e-12 |
| Type II off-axis raises FB-5.2 | **pass** | `test_typeII_off_axis_raises_fb52` |
| Type II Laplacian ``−k_1²`` | **pass** | `test_typeII_scalar_laplacian_eigenvalue` |
| VI_0 plane-wave on abelian 2-plane | **pass** | `test_typeVI0_nabla_mixed_sign_mode` |
| VI_0 Laplacian ``−(k_1² + k_3²)`` | **pass** | `test_typeVI0_scalar_laplacian_eigenvalue` |
| VI_0 off-plane (k_2 ≠ 0) raises FB-5.2 | **pass** | `test_typeVI0_off_plane_raises_fb52` |
| VIII plane-wave on Cartan ``e_1`` | **pass** | `test_typeVIII_nabla_sl2R_mode` |
| VIII Laplacian ``−k_1²`` | **pass** | `test_typeVIII_scalar_laplacian_eigenvalue` |
| VIII off-Cartan (k_2 or k_3 ≠ 0) raises FB-5.2 | **pass** | `test_typeVIII_off_cartan_raises_fb52` |
| T1 with ``³R = 0`` matches base expansion | **pass** | `test_T1_zero_ricci_matches_base` rel 1e-14 |
| T1 default kwarg (``None``) matches LB-2b base | **pass** | `test_T1_no_ricci_matches_base_expansion` bit-identical |
| T1 with Type II ``³R_aniso`` is non-zero | **pass** | `test_T1_typeII_ricci_contribution_nonzero` |
| T1 ℓ = 0 ignores ``³R`` | **pass** | `test_T1_ell_zero_ignores_ricci` rel 1e-14 |
| T2 hook at background = base (FLRW preserved) | **pass** | `test_T2_hook_zero_at_background_typeII` + `..._ell2` |
| T2 bad shape rejected | **pass** | `test_T2_hook_bad_shape_rejected` |
| FB14-F1: VI_h h-scaling pinned | **pass** | `test_VIh_h_factor_scaling_pinned` rel 1e-12 |
| FB14-F1: VII_h h-scaling pinned | **pass** | `test_VIIh_h_factor_scaling_pinned` rel 1e-12 |
| FB14-F1: VI_h small-``a`` quadratic scaling | **pass** | `test_VIh_twist_piece_vanishes_at_zero_a` rel 1e-6 (cancellation-limited) |
| SUPPORTED_FB22_TYPES = {II, VI_0, VIII} | **pass** | `test_fb22_supported_types_contains_class_a_additions` |
| SUPPORTED_TYPES = FB21 ∪ FB22 (8 labels) | **pass** | `test_fb22_supported_types_is_union_aggregate` |
| FB-2.1 partition test updated + still green | **pass** | `test_fb21_dispatch_covers_all_11_bianchi_types_plus_flrw` |
| Dimensional consistency ([k] = 1/Mpc, [³R] = 1/Mpc²) | **pass** | inspection |
| FLRW bit-identical LB-6 regression | **pass** | 3,032 pre-existing tests unchanged |

### §4 Equation-to-code mapping audit

| Equation | Code location | Verdict |
|---|---|---|
| II axis-aligned validator (Heisenberg center) | `_validate_mode_typeII` in `bass/hierarchy/nabla_dispatch.py` | pass — tolerance-aware zero check on ``k_2, k_3``; explicit FB-5.2 message |
| VI_0 axis-aligned validator (``e(1,1)`` abelian 2-plane) | `_validate_mode_typeVI0` | pass — ``k_2 = 0`` check + Jacobi sanity (``n_1 > 0, n_3 < 0``) |
| VIII axis-aligned validator (SL(2,R) Cartan) | `_validate_mode_typeVIII` | pass — ``k_2, k_3 = 0`` check + ``n_1 < 0, n_2, n_3 > 0`` |
| ``make_nabla_tilde`` dispatch: FB21 ∪ FB22 → plane wave; FB23 → NotImplementedError | `make_nabla_tilde` | pass — branch ``label in SUPPORTED_TYPES`` |
| ``scalar_laplacian_eigenvalue`` II / VI_0 / VIII → ``−\|k\|²`` | `scalar_laplacian_eigenvalue` | pass — unified ``return -k2`` after validator accepts |
| T1 Ricci coupling | `T1_expansion` in `bass/hierarchy/terms.py` | pass — ``np.tensordot(Pi_ell_full, R, axes=([-1], [1]))`` + ``sym_trace_free`` + ``ℓ/(2ℓ+3)`` prefactor |
| T2 Ricci hook (background zero) | `T2_gradient` | pass — ``ricci_grad = nabla_operator(R, 'gradient')`` returns zeros for ``zero_nabla_operator``; explicit dtype promotion for FB-5 complex wire-up |
| FB14-F1 ``(2/3) A²/(1+\|h\|)`` piece (already in place) | `source_VIh` / `source_VIIh` in `bass/transport/shear_sources.py` | pass — verified by parameter-sweep h-scaling test |
| No silent fallback for deferred types | inspection | pass — FB-5.2 off-axis guards raise before returning any operator |

### §5 Numerical / pipeline audit

| Item | Status | Notes |
|---|---|---|
| Plane-wave eigenmode rel 1e-12 on II / VI_0 / VIII | ok | Complex arithmetic at ε_mach |
| T1 with zero Ricci matches base rel 1e-14 | ok | Floating-point cancellation is clean (only an addition) |
| T2 hook equality with/without Ricci at background | ok | atol=0 — structural zero propagates exactly |
| FB14-F1 small-``a`` test rtol 1e-6 | ok | Catastrophic cancellation between N² and A² pieces limits precision — physical artefact, not a bug |
| Dtype promotion in T2 hook (real → complex) | ok | ``base.astype(ricci_hook.dtype)`` ensures FB-5 complex-dtype-ready |
| ``aniso_ricci_tensor`` shape validation | ok | Rank-2 (3, 3) enforced in both T1 and T2 |
| No external code | ok | Only ``numpy`` imports; no CAMB / CLASS / Healpy |
| Determinism | ok | Pure functions; no global state |

### §6 Ranked failure modes

- **None P0 / P1** identified.
- **P2 (carry-forward)** — Complex-dtype ``nabla_dispatch`` still not
  wired into ``hierarchy_rhs_photon``; production driver continues to
  use ``zero_nabla_operator``. This is **not a regression** — the
  FB-2.1 audit already documented the hand-off to FB-5.1. The
  T1/T2 Ricci hooks added in FB-2.2 are similarly structural (see §4
  T2 entry); the production driver does not yet route
  ``tetrad_state.aniso_3_curvature`` into the term functions because
  doing so would change the II / VI_0 / VIII background RHS and
  require a per-type regression sweep scheduled for FB-2.4 (T4-T7
  wire-up). Documented as new P2 below.
- **FB-2.2 P2 (new)** — ``T1_expansion`` / ``T2_gradient`` accept
  ``aniso_ricci_tensor`` but ``hierarchy_rhs_photon`` does not yet
  pass it in. Next session (FB-2.3 or FB-2.4) must connect the tetrad
  state to the term functions and run the per-type regression sweep.
- **P3 (future)** — Off-axis modes on II / VI_0 / VIII require the
  full FB-5.2 dispatch: Grushin decomposition for Heisenberg, Wigner
  rotation for ``e(1,1)``, SL(2,R) principal series for VIII.
  Documented explicitly at each validator.

### §7 Verifier results

| Verifier | Result |
|---|---|
| A. Physics: known-limit recovery | **passed** (II / VI_0 / VIII axis-aligned subsets reduce to plane wave; the FB-5.2 off-axis cases raise, so no silent approximation) |
| A. Physics: dimensional consistency | **passed** |
| A. Physics: sign / normalisation (``∇̃ = i k``, ``³R`` prefactor ``ℓ/(2ℓ+3)``) | **passed** |
| A. Physics: admissibility (positive eigenvalues for the supported sign pattern) | **passed** |
| B. Code: contract satisfaction | **passed** (signatures preserve LB-2b default behaviour) |
| B. Code: reproducibility | **passed** (pure functions) |
| B. Code: regression risk | **passed** (3,032 pre-existing tests unchanged; +24 new) |
| C. Numerical: tolerance robustness | **passed** (rel 1e-12 on eigenmode pins; rel 1e-6 on cancellation-limited FB14-F1 test with explicit rationale) |
| C. Numerical: baseline reproducibility | **passed** (3,056 passed + 1 skipped) |
| C. Numerical: misspecification | **passed** (off-axis / wrong-shape / wrong-sign inputs all raise with specific FB-tag messages) |

### §8 Minimal repair plan

- **None required** — no P0 / P1 issues surfaced. The FB-2.2 P2 and
  the pre-existing FB-2.1 P2 remain carry-forwards for FB-2.3 /
  FB-2.4 / FB-5.1.

### §9 Minimal test set (all present)

| Category | Test |
|---|---|
| Baseline reproduction | `test_T1_no_ricci_matches_base_expansion` (LB-2b bit-identical FLRW) |
| Edge / adversarial | 3 × off-axis → FB-5.2 raises (`test_typeII_off_axis_raises_fb52`, `test_typeVI0_off_plane_raises_fb52`, `test_typeVIII_off_cartan_raises_fb52`) + T2 bad-shape rejection |
| Physics sanity | 3 × axis-aligned plane-wave pins + 3 × Laplacian eigenvalue pins |
| Numerical stability | `test_VIh_twist_piece_vanishes_at_zero_a` (cancellation-limited rel 1e-6; documented rationale) |
| Regression / dispatch | `test_fb22_supported_types_is_union_aggregate` + `test_fb21_dispatch_covers_all_11_bianchi_types_plus_flrw` (updated) |
| FB14-F1 calibration | `test_VIh_h_factor_scaling_pinned` + `test_VIIh_h_factor_scaling_pinned` (rel 1e-12 closed-form match) |

### §10 Verdict

**통과 (pass)**. FB-2.2 adds Class A II / VI_0 / VIII ``∇̃`` dispatch
on each type's abelian subalgebra (with explicit FB-5.2 off-axis
guards), structurally wires the anisotropic-3-Ricci tensor into T1
and T2 (with default-None preserving bit-identical LB-6 regression),
and calibrates the FB14-F1 twist piece via a closed-form h-scaling
parameter sweep at rel 1e-12. 24 new tests, all passing, zero
regression (3,032 → 3,056 passed + 1 skipped).

**Do now (1 item)**: rotate ``NEXT_SESSION_PROMPT §2`` to FB-2.3
(Class B III / IV / VI_h / VII_h ``∇̃`` twist-coupled dispatch).

**Do not touch (1 item)**: ``hierarchy_rhs_photon``'s call sites for
T1 / T2 — they continue to pass ``aniso_ricci_tensor=None``. FB-2.3
or FB-2.4 will switch to the live Ricci wire-up once the per-type
background regression sweep is specified.

### Phase FB-2.2 → FB-2.3 hand-off

FB-2.3 consumes:

1. ``SUPPORTED_FB22_TYPES`` (II / VI_0 / VIII) — for cross-type
   consistency checks.
2. The FB14-F1 h-scaling contract — so Class B ∇̃ dispatch can
   leverage the same ``a_twist`` identification.
3. The ``T1`` / ``T2`` Ricci hook signatures — FB-2.3 may activate
   them for Class B once the twist-coupled ``∇̃`` dispatch is online.

### Carry-forwards to FB-2.3 / FB-2.4

| Tag | Item | Target |
|---|---|---|
| FB-2.1 P2 | Complex-dtype ``nabla_dispatch`` not wired into ``hierarchy_rhs_photon`` | FB-5.1 |
| FB-2.2 P2 (new) | ``hierarchy_rhs_photon`` does not pass ``aniso_ricci_tensor`` to T1 / T2 | FB-2.4 |
| F3 (from LB-5) | ``TetradBackgroundState.shear_magnitude_sq`` dimensionless-Σ² normalisation | FB-2.4 |
| FB-5.2 | II / VI_0 / VIII / VII_0 / VII_h generic off-axis dispatch | FB-5.2 |
| FB-2.3 | Class B III / IV / VI_h / VII_h ``∇̃`` twist coupling | FB-2.3 |
| FB-2.4 | T4–T7 wire-up + aniso_ricci driver wire-up | FB-2.4 |

### Deliverables (diff summary)

| Item | File | Status |
|---|---|---|
| A | ``bass/hierarchy/nabla_dispatch.py`` — II / VI_0 / VIII validators + ``SUPPORTED_FB22_TYPES`` / ``SUPPORTED_TYPES`` tuples + dispatch + Laplacian branches | ✅ |
| B | ``bass/hierarchy/terms.py`` — optional ``aniso_ricci_tensor`` kwarg on T1 and T2 (default ``None`` preserves LB-2b bit-identical) | ✅ |
| C | ``bass/hierarchy/__init__.py`` — re-export ``SUPPORTED_FB22_TYPES`` + ``SUPPORTED_TYPES`` | ✅ |
| D | ``bass/hierarchy/test_nabla_dispatch_fb22.py`` — 24 new tests (9 eigenmode + 3 off-axis FB-5.2 + 4 T1 + 3 T2 + 3 FB14-F1 + 2 partition) | ✅ |
| E | ``bass/hierarchy/test_nabla_dispatch.py`` — updated: FB-2.2 deferred tests replaced with axis-aligned-supported tests; dispatch-coverage test refreshed | ✅ |
| F | ``docs/audits/AUDIT_PHASE_FB2_2026-04-19.md`` — this file (FB-2.2 supplement append) | ✅ |
| G | ``docs/lowell_bianchi/NEXT_SESSION_PROMPT.md §2`` — rotated to FB-2.3 (Class B twist-coupled ∇̃ dispatch) | ✅ |

*End of FB-2.2 audit supplement.*

---

## FB-2.3 — Class B III / IV / VI_h / VII_h ∇̃ twist-coupled dispatch on the abelian 2-plane + T1 Ricci hook activation

**Session date**: 2026-04-19
**Commit target**: `FB-2.3: Class B III / IV / VI_h / VII_h twist-coupled nabla_tilde + T1 Ricci hook activation`
**Parent commit at entry**: `6f6df1c` (HEAD before FB-2.3) — pre-FB-2.3 baseline 3,056 passed + 1 skipped
**Exit test count**: 3,083 passed + 1 skipped (+27 new)
**Env note**: on entry the venv editable-install finder
(`venv/lib/python3.12/site-packages/__editable___htt_8_3_0_finder.py`)
still pointed ``htt``/``tests`` at the deleted
`bass_phase1_snapshot_2026-04-18/bass_phase1_snapshot/bass_py/htt/…`
paths, blocking every `bass.species.constants` import. Re-running
`../venv/bin/python -m pip install -e .` from `htt_base/htt/htt/`
re-pinned the finder at `htt_base/htt/htt/htt` (present tree) — a pure
environment fix, no code change.

### §1 Audit target reconstruction

1. **Physical/mathematical claim**. The Class B Bianchi types
   (III / IV / VI_h / VII_h) all carry a twist vector
   ``a_α = (0, a_twist, 0)`` in the PC frame; Jacobi
   (``n^{αβ} a_β = 0``) forces ``n_2 = 0``, so
   ``[e_3, e_1] = n_2 e_2 = 0`` and ``span{e_1, e_3}`` is an
   **abelian** 2-subalgebra. On that abelian plane a scalar plane wave
   ``Y = e^{i k · x}`` with ``k_2 = 0`` is an exact eigenmode of
   ``∇̃``, and the scalar Laplacian acquires a Harrison-V-style
   curvature offset from the twist sector:

        ∇̃² Y = −(|k|² + a_twist² / (1 + |h|)) Y      (h = a²/(n₁ n₃))

   The denominator ``1 + |h|`` matches the FB14-F1
   ``(2/3) A² / (1 + |h|)`` piece of the Class B W-E ``S^{WE}_+``
   shear source (already in-tree). Special cases: Type III
   (``|h| = 1``) → factor 1/2; Type IV (``h = 0``) → factor 1
   (Harrison-V limit); Type V at ``h = 0`` → identical eigenvalue.

   For T1 / T2: the FB-1.4 consolidation made
   ``anisotropic_3_curvature`` return a non-zero Class B
   ``³R_{ab}^{aniso}``, so the FB-2.2 optional ``aniso_ricci_tensor``
   kwarg on ``T1_expansion`` now activates automatically for Class B
   callers. ``T2_gradient`` remains structurally zero at background
   (``zero_nabla_operator``), awaiting FB-5 complex-dtype wire-up.

2. **Algorithm**.
   * Add ``III``, ``IV``, ``VI_h``, ``VII_h`` to
     ``SUPPORTED_FB23_TYPES``; per-type validators
     ``_validate_mode_typeIII / _IV / _VIh / _VIIh`` delegate to a
     shared ``_validate_class_b_axis_aligned_k2_zero`` guard that
     checks ``k_2 = 0`` and ``a_twist > 0``; off-plane modes raise
     ``NotImplementedError("FB-5.2")``.
   * Extend ``scalar_laplacian_eigenvalue`` with the
     ``−(|k|² + a²/(1+|h|))`` branch for every ``label in
     SUPPORTED_FB23_TYPES``.
   * Drain ``DEFERRED_FB23_TYPES`` to ``()``; recompute
     ``SUPPORTED_TYPES = FB21 ∪ FB22 ∪ FB23`` (12 labels).

3. **Source of truth**. ``bass/hierarchy/nabla_dispatch.py``
   docstrings cite Wainwright-Ellis 1997 §9.1, Ellis-Maartens-MacCallum
   2012 §14.3, Harrison 1967 eq (4.5), Pontzen & Challinor 2007 eq
   (2.12). The FB14-F1 ``1/(1+|h|)`` denominator is cross-linked to
   ``bass/transport/shear_sources.py`` (source_VIh / source_VIIh) so
   the ∇̃ twist offset and the W-E shear source share a single
   parameterisation.

### §2 Contract / interface table

| Contract item | Value |
|---|---|
| Supported FB-2.3 types | ``III``, ``IV``, ``VI_h``, ``VII_h`` (all ``a_twist > 0``) |
| Abelian subalgebra | ``span{e_1, e_3}`` for every Class B (Jacobi ``n_2 = 0``) |
| Admissible mode | ``k_vec = (k_1, 0, k_3)`` (``k_2 = 0``); any finite real components |
| Off-plane → FB-5.2 | Non-zero ``k_2`` on any Class B type raises ``NotImplementedError("FB-5.2")`` |
| Laplacian III | ``λ = −(|k|² + a_twist²/2)`` (``|h|=1``) |
| Laplacian IV | ``λ = −(|k|² + a_twist²)`` (``h=0``; Harrison-V analogue) |
| Laplacian VI_h | ``λ = −(|k|² + a_twist²/(1+|h|))`` for ``h ∈ (−∞,−1) ∪ (−1,0)`` |
| Laplacian VII_h | ``λ = −(|k|² + a_twist²/(1+h))`` for ``h > 0`` (PC 2007 spiral damping) |
| Dispatch partition | ``SUPPORTED_TYPES = FB21 ∪ FB22 ∪ FB23 = 12 labels`` (disjoint); ``DEFERRED_FB22_TYPES = DEFERRED_FB23_TYPES = ()`` |
| T1 Ricci hook | Active on Class B via the FB-2.2 optional kwarg (no code change; driver wire-up still parked for FB-2.4) |
| Sign-constraint guards | ``n_1 > 0`` (III / VI_h / VII_h), ``n_3 < 0`` (III / VI_h), ``n_3 > 0`` (IV / VII_h), ``n_1 = 0`` (IV), ``h ≠ −1`` (VI_h — that's III) |
| FB14-F1 cross-link | ``1/(1+|h|)`` denominator shared with ``bass/transport/shear_sources.py`` |

### §3 Phys-math audit ledger

| Check | Verdict | Notes |
|---|---|---|
| III axis-aligned plane wave ``∇̃ = i k`` | **pass** | `test_typeIII_nabla_axis_aligned` rel 1e-12 |
| III divergence on a rank-1 probe | **pass** | `test_typeIII_divergence_rank1` rel 1e-12 |
| III Laplacian offset ``a²/2`` at ``|h|=1`` | **pass** | `test_typeIII_laplacian_h_minus_one_half_offset` rel 1e-12 |
| IV axis-aligned plane wave | **pass** | `test_typeIV_nabla_axis_aligned` rel 1e-12 |
| IV Laplacian matches Harrison-V at ``h = 0`` | **pass** | `test_typeIV_laplacian_matches_harrison_V` rel 1e-12 |
| VI_h plane wave on the abelian plane | **pass** | `test_typeVIh_nabla_on_abelian` rel 1e-12 |
| VI_h Laplacian ``a²/(1+\|h\|)`` | **pass** | `test_typeVIh_laplacian_h_factor_denominator` rel 1e-12 |
| VII_h symmetric-line + axis-aligned plane wave | **pass** | `test_typeVIIh_nabla_symmetric_axis_aligned` rel 1e-12 |
| VII_h spiral damping ``a²/(1+h)`` | **pass** | `test_typeVIIh_laplacian_spiral_damping` rel 1e-12 |
| VII_h ``h → 0`` limit → Harrison-V | **pass** | `test_typeVIIh_h_to_zero_limit_matches_harrison` rel 1e-12 |
| Class B off-plane → ``NotImplementedError("FB-5.2")`` (4 types) | **pass** | `TestFB23ClassBOffAxis::test_class_b_off_plane_raises_fb52` parametrised on (III, IV, VI_h, VII_h) |
| T1 Ricci contribution non-zero on every Class B type | **pass** | `TestT1ClassBRicciCoupling::test_T1_class_b_ricci_contribution_nonzero` parametrised; ``norm(out_ricci − out_base) > 1e-8`` |
| h-parametrisation: VI_h ``h → −1`` matches III ``a²/2`` | **pass** | `test_III_matches_VI_h_approaching_minus_one` rel 1e-4 (h = −0.9999 perturbation) |
| h-parametrisation: IV ↔ V at identical (``a``, ``k``) across 4 k magnitudes | **pass** | `test_IV_and_V_match_at_identical_a_k` rel 1e-12 |
| Sign-constraint guards (III n_1>0; IV n_1=0; VII_h n_3>0; a_twist>0) | **pass** | `TestClassBValidatorSignGuards` (4 tests) |
| ``SUPPORTED_FB23_TYPES`` = {III, IV, VI_h, VII_h} | **pass** | `test_fb23_supported_types_contains_class_b_additions` |
| ``DEFERRED_FB23_TYPES`` drained to empty | **pass** | `test_fb23_deferred_tuple_is_drained` |
| ``SUPPORTED_TYPES`` = 12 labels (11 Bianchi + FLRW), disjoint | **pass** | `test_fb23_supported_types_covers_twelve_labels` |
| FB-2.1 partition test still green after merge | **pass** | `test_fb21_dispatch_covers_all_11_bianchi_types_plus_flrw` unaffected |
| Dimensional consistency (``[k] = 1/Mpc``, ``[a_twist²] = 1/Mpc²``) | **pass** | inspection |
| Ellis convention preserved; ``∇̃ = i k_a``; PSTF invariants | **pass** | inspection |
| LB-6 baseline bit-identical (3,056 pre-existing tests) | **pass** | 3,083 − 27 = 3,056 |

### §4 Equation-to-code mapping audit

| Equation | Code location | Verdict |
|---|---|---|
| Class B axis-aligned guard (``k_2 = 0`` + ``a_twist > 0``) | `_validate_class_b_axis_aligned_k2_zero` in [htt/bass/hierarchy/nabla_dispatch.py](htt/bass/hierarchy/nabla_dispatch.py) | pass — tolerance-aware zero check on ``k_2``; uniform FB-5.2 message across all 4 types |
| III validator (``n_1 > 0, n_3 < 0``) | `_validate_mode_typeIII` | pass — sign-constraint guard cites W-E §9.1 |
| IV validator (``n_1 = 0, n_3 > 0``) | `_validate_mode_typeIV` | pass — admits ``h = 0`` marginal case |
| VI_h validator (``n_1 > 0, n_3 < 0, h ≠ −1``) | `_validate_mode_typeVIh` | pass — rejects the III-coincident ``h = −1`` boundary |
| VII_h validator (``n_1 > 0, n_3 > 0, h > 0``) | `_validate_mode_typeVIIh` | pass — admits the PC 2007 spiral range |
| ``SUPPORTED_TYPES = FB21 ∪ FB22 ∪ FB23`` | `nabla_dispatch.py` module level | pass — 12 distinct labels, set equality enforced by test |
| Laplacian ``−(|k|² + a²/(1+|h|))`` for Class B | `scalar_laplacian_eigenvalue` Class B branch | pass — unified ``h_denom = 1.0 + abs(h_parameter)`` for all four types |
| Harrison-V reduction at ``h = 0`` (IV = V at identical a, k) | `scalar_laplacian_eigenvalue` IV branch vs V branch | pass — cross-type equality test pins rel 1e-12 |
| T1 ``aniso_ricci_tensor`` kwarg active on Class B | `T1_expansion` in `bass/hierarchy/terms.py` | pass — no code change needed; FB-1.4 ``³R_{ab}^{aniso}`` feeds the FB-2.2 hook |
| ``hierarchy_rhs_photon`` driver still passes ``aniso_ricci_tensor = None`` | consumer unchanged | **carry-forward** — intentional per FB-2.2 P2; driver wire-up scheduled for FB-2.4 |
| No silent fallback for deferred subsets | inspection | pass — ``NotImplementedError("FB-5.2")`` raised before any operator is returned |

### §5 Numerical / pipeline audit

| Item | Status | Notes |
|---|---|---|
| Plane-wave eigenmode rel 1e-12 on III / IV / VI_h / VII_h | ok | Complex arithmetic at ε_mach |
| Laplacian Class B offset rel 1e-12 across 4 k magnitudes | ok | Closed-form comparison, no cancellation |
| VI_h ``h → −1`` continuity at h = −0.9999 | ok | Rel 1e-4 is the expected offset-ratio tolerance (``(1+1)/(1+0.9999) ≈ 1.00005``) |
| VII_h ``h → 0`` limit vs V (Harrison) at ``a_twist = 1e-6`` | ok | Absolute diff < 1e-12 |
| T1 Ricci coupling norm > 1e-8 on all 4 types | ok | Physical tensor magnitude from FB-1.4 ``³R_{ab}^{aniso}`` |
| Off-plane raises on every type (parametrised) | ok | Uniform error surface |
| Dtype promotion float64 → complex128 (inherits FB-2.1) | ok | ``_plane_wave_operator`` reused unchanged |
| Determinism | ok | Pure functions; no global state |
| No external code | ok | Only ``numpy`` imports |
| Jacobi sanity (``n_2 = 0`` forced by ``a_β`` twist) | ok | Enforced by ``StructureConstants`` factories + validator sign guards |

### §6 Ranked failure modes

- **None P0 / P1** identified.
- **P2 (carry-forward from FB-2.2)** — ``hierarchy_rhs_photon`` still
  does not route ``tetrad_state.aniso_3_curvature`` into
  ``T1_expansion`` / ``T2_gradient``. FB-2.3 deliberately leaves this
  untouched (the plan explicitly parks it for FB-2.4 alongside the
  T4-T7 vorticity / 4-accel wire-up and a per-type regression sweep).
  **Not a new finding** — this supplement only re-documents the
  carry-forward.
- **P3 (future)** — Off-axis Class B modes require the full FB-5.2
  dispatch (helical / Wigner-rotation lift around the ``e_2`` twist
  generator). Raised explicitly at every Class B validator; no silent
  approximation.
- **P3 (env, out of FB scope)** — `venv/bin/pip` shebang still points
  at the deleted snapshot path. Working around with
  `../venv/bin/python -m pip`; a full `python -m venv --upgrade` or a
  fresh venv rebuild would clean this up. Unrelated to FB physics; not
  acted on this session.

### §7 Verifier results

| Verifier | Result |
|---|---|
| A. Physics: known-limit recovery | **passed** (IV = V at ``h = 0``; VII_h → V at ``h → 0``; VI_h → III as ``h → −1``) |
| A. Physics: dimensional consistency | **passed** (``[k] = [a_twist] = 1/Mpc``; eigenvalue in ``1/Mpc²``) |
| A. Physics: sign / normalisation (``∇̃ = i k``; ``+a²/(1+|h|)`` offset) | **passed** |
| A. Physics: admissibility (Class B sign pattern + ``a_twist > 0`` enforced) | **passed** |
| B. Code: contract satisfaction (plane-wave operator reuse; 12-label partition) | **passed** |
| B. Code: reproducibility | **passed** (pure functions; no state) |
| B. Code: regression risk | **passed** (3,056 pre-existing tests bit-identical; +27 new) |
| C. Numerical: tolerance robustness | **passed** (rel 1e-12 on all eigenmode + Laplacian pins; rel 1e-4 on the III ↔ VI_h ``h → −1`` limit, rationalised) |
| C. Numerical: baseline reproducibility | **passed** (3,083 passed + 1 skipped) |
| C. Numerical: misspecification | **passed** (off-plane / wrong-sign / ``a_twist ≤ 0`` / ``h = −1`` all raise with FB-tag messages) |

### §8 Minimal repair plan

- **None required** — no P0 / P1 issues surfaced. The FB-2.2 P2 carry-
  forward (driver wire-up of ``aniso_ricci_tensor``) remains deferred
  to FB-2.4 per the approved plan; the env stale-shebang is P3.

### §9 Minimal test set (all present, 27 total in `test_nabla_dispatch_fb23.py`)

| Category | Test |
|---|---|
| Baseline reproduction | `test_IV_and_V_match_at_identical_a_k` (IV at ``h = 0`` reduces to Harrison-V across 4 k magnitudes, rel 1e-12) |
| Edge / adversarial | 4 × `TestFB23ClassBOffAxis::test_class_b_off_plane_raises_fb52` + 4 × `TestClassBValidatorSignGuards` (n₁, n₃, a_twist sign rejection) |
| Physics sanity | 4 × axis-aligned plane-wave pins + 4 × Laplacian eigenvalue pins |
| Numerical stability | `test_typeVIIh_h_to_zero_limit_matches_harrison` (abs < 1e-12 at ``a = 1e-6``), `test_III_matches_VI_h_approaching_minus_one` (rel 1e-4 at h = −0.9999) |
| Regression / dispatch | `test_fb23_supported_types_contains_class_b_additions` + `test_fb23_deferred_tuple_is_drained` + `test_fb23_supported_types_covers_twelve_labels` |
| FB-1.4 × FB-2.2 coupling | 4 × `TestT1ClassBRicciCoupling::test_T1_class_b_ricci_contribution_nonzero` (parametrised on III / IV / VI_h / VII_h) |

### §10 Verdict

**통과 (pass)**. FB-2.3 closes the Class B (III / IV / VI_h / VII_h)
∇̃ dispatch on the abelian ``(e_1, e_3)`` 2-plane with a unified
Harrison-V twist offset ``−(|k|² + a_twist²/(1+|h|))`` that recovers
the FB14-F1 ``S^{WE}_+`` ``(2/3) A²/(1+|h|)`` denominator and the
PC 2007 VII_h spiral damping. The FB-2.2 ``T1_expansion``
``aniso_ricci_tensor`` hook activates automatically on Class B via
the FB-1.4 ``³R_{ab}^{aniso}`` output (no code change in
``terms.py``). Off-plane modes raise ``NotImplementedError("FB-5.2")``
uniformly across all four types. 27 new tests, all passing, zero
regression (3,056 → 3,083 passed + 1 skipped).

**Do now (1 item)**: rotate ``NEXT_SESSION_PROMPT §2`` to FB-2.4
(T4-T7 vorticity / 4-acceleration wire-up + driver-level
``aniso_ricci_tensor`` routing + per-type ``hierarchy_rhs_photon``
regression sweep).

**Do not touch (1 item)**: ``hierarchy_rhs_photon``'s T1 / T2 call
sites — they continue to pass ``aniso_ricci_tensor = None``. FB-2.4
owns the live Ricci wire-up alongside the per-type background
regression sweep. Touching it this session would couple FB-2.3's
dispatch test into the LB-6 regression suite prematurely.

### Gallery note

FB-2.3 is a no-op visually: the Class B twist offset is a scalar
eigenvalue shift, not a trajectory observable. No new PNG added;
FB-1.4 gallery 13 (``anisotropic_3_curvature`` per-type visualisation)
already covers the ``³R_{ab}^{aniso}`` feed that drives the T1 hook.
Documented explicitly per the phase-boundary gallery rule.

### Phase FB-2.3 → FB-2.4 hand-off

FB-2.4 consumes:

1. ``SUPPORTED_TYPES`` (12 labels) — the complete ∇̃ dispatch that
   ``hierarchy_rhs_photon`` will gate against before raising.
2. The ``T1_expansion`` / ``T2_gradient`` ``aniso_ricci_tensor``
   optional kwarg — the driver must now pass
   ``tetrad_state.aniso_3_curvature`` when it is not None.
3. The Class B twist eigenvalue formula — T4 (vorticity) / T5
   (4-acceleration) couplings will reuse the same ``a_twist²/(1+|h|)``
   denominator for their harmonic-mode projections.

### Carry-forwards to FB-2.4 / FB-5

| Tag | Item | Target |
|---|---|---|
| FB-2.1 P2 | Complex-dtype ``nabla_dispatch`` not wired into ``hierarchy_rhs_photon`` | FB-5.1 |
| FB-2.2 P2 | ``hierarchy_rhs_photon`` does not pass ``aniso_ricci_tensor`` to T1 / T2 | FB-2.4 |
| F3 (from LB-5) | ``TetradBackgroundState.shear_magnitude_sq`` dimensionless-Σ² normalisation | FB-2.4 |
| FB-5.2 | Class B off-plane + II / VI_0 / VIII / VII_0 off-axis generic helical Wigner rotation | FB-5.2 |
| FB-2.4 | T4-T7 (vorticity, 4-acceleration) hierarchy wire-up + driver aniso_ricci wire-up + per-type regression sweep | FB-2.4 (next session) |
| FB-2.3 P3 (env) | Stale ``venv/bin/pip`` shebang still points at deleted snapshot path — use ``python -m pip`` until the venv is rebuilt | post-FB (devops) |

### Deliverables (diff summary)

| Item | File | Status |
|---|---|---|
| A | ``bass/hierarchy/nabla_dispatch.py`` — III / IV / VI_h / VII_h validators + ``SUPPORTED_FB23_TYPES`` + Class B Laplacian branch + updated module docstring | ✅ pre-landed |
| B | ``bass/hierarchy/test_nabla_dispatch_fb23.py`` — 27 new tests (2 III axis + 1 III Laplacian + 2 IV axis + Laplacian + 2 VI_h axis + Laplacian + 3 VII_h axis + Laplacian + ``h → 0`` + 4 off-plane + 4 T1 coupling + 2 h-parametrisation + 3 partition + 4 sign guards) | ✅ pre-landed |
| C | ``docs/audits/AUDIT_PHASE_FB2_2026-04-19.md`` — this FB-2.3 supplement | ✅ this commit |
| D | ``docs/lowell_bianchi/NEXT_SESSION_PROMPT.md §2`` — rotated to FB-2.4 | ✅ this commit |
| E | ``venv/lib/python3.12/site-packages/__editable___htt_8_3_0_finder.py`` — MAPPING re-pinned to ``htt_base/htt/htt/htt`` via ``pip install -e`` reinstall | ✅ environment fix only, no code change |

*End of FB-2.3 audit supplement.*
