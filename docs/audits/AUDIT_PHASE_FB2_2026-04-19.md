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
