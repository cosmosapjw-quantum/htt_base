# P08-B — independent review (verbatim final report of a fresh read-only reviewer)

# P08-B review: ellipsoid quotient image (`P08EllipsoidImage.lean`)

**Verdict: PASS_WITH_NOTES.** All four required targets (Q1–Q4) and the stretch targets (Q1′, Q5a, Q5b) are formally checked within the stated scope. Nothing blocks.

**Reviewer:** Claude Opus 5.5, in a fresh read-only session. I did not author this work and I did not edit any repository file. The author return lists its author as `claude-opus-5-5`, which is the same model family as me. The card asked for a gpt-6-astra/ultra reviewer, so this review is context-independent but not model-independent. Record that in the review state.

## Per-check table

| Check | Result | Evidence |
|---|---|---|
| **Source citations** (`SOURCE_RECOVERY.md`) | OK | All `typefree_fibers.py` line citations match the file: L `:18-31`, z0 `:48`, kernel `:43,56`, gauge `:72-91`, support `:126-133`, docstring `:137`, solve call `:148`, η `:153`, boundary `:154-163`, lift `:164-165`, target `:166,170`, incompatible `:149-150`. The Python file is clean at commit `bc45fb92`, sha `6f5f9a01…` (matches). Contract `904d95fe…` and PORT_MAP `d0050aa3…` match. |
| **Q1: two-sided equality, x-space vs z-space** | OK | `fibreImage_eq` has exactly the frozen statement. The x↔z mapping is correct: `fibreImage_eq_latent` proves both directions. Forward: for x = c + Lz, `B x = y` becomes `(B*L) z = y - B c` by `mulVec_mulVec`. Backward: lift z to `c + L z`. `Ell` is the whole bounded set `{c + L z : z·z ≤ 1}`, not a coercive relaxation. `kernel_ball_param` is an iff. Both inclusions are proved through P08-A `fiber_eq_kernel_ball`. |
| **Q1′: η ≤ 1** | OK | `fibreImage_eq_of_le`; Q1 is obtained from it via `hη.le`. |
| **Q2a: any two orthonormal kernel bases** | OK | `basis_invariance`, with widths d and d′ arbitrary. Both sides are rewritten to the same `FibreImage`. |
| **Q2b: N ↦ N R** | OK | `isKerONB_mul_orthogonal` (the hypothesis is preserved) and `ellImage_mul_orthogonal` (the set is unchanged, both inclusions). |
| **Q3: boundary return** | OK | `boundary_eq_one` gives a singleton at η = 1. `boundary_consistent` shows the closed form at radius √0 gives the same point. `boundary_gt_one` gives ∅ for η > 1. `incompatible_empty` gives ∅ without needing a Moore–Penrose inverse. The two empty cases have separate causes. |
| **Q4: an N exists for every A** | OK | `exists_kerONB`, built from `stdOrthonormalBasis` of `kerE A`, with `kerN_orthonormal` and `kerN_range`. `fibreImage_exists_param` shows the Q1 hypotheses can all be satisfied at once (X from `moorePenrose_exists`). |
| **Q5a: support function** | OK | `support_function` proves the upper bound and that it is attained, for s ≥ 0. It is the same formula as `support()` at `:126-133`: `w·θ0 + ‖Fᵀw‖`. |
| **Q5b: gauge and nonemptiness** | OK | `eta_squared_gauge`: z0 solves the system and η ≤ z·z for every solution. `fibreImage_nonempty_iff`: the image is nonempty iff the data are compatible and η ≤ 1. |
| **No hypothesis assumes a conclusion** | OK | The hypotheses are only: the four Penrose conditions (definition printed and checked), `∃ z, A z = b`, `IsKerONB`, and a bound on η. Each is independent of the conclusion. Q4 and `moorePenrose_exists` show they can be satisfied together. |
| **Receipts** | OK | For compile_01–05, every recorded source, stdout and stderr sha matches its file. Exit codes are 1, 1, 0, 0, 0 (01 and 02 are kept failures with their errors). `compile_04_main.source.lean` matches the candidate sha `0cb88696…`. The stored olean `a50e9a91…` matches the compile_04 receipt. The import oleans and sources did not change before vs after any run. |
| **Axioms / forbidden constructs** | OK | All 29 audited declarations show only `[propext, Classical.choice, Quot.sound]`. Searching `lean/` for sorry, admit, native_decide, axiom, set_option, opaque, implemented_by and extern finds nothing. |
| **Independent recompile** | OK | I copied the source to scratch and compiled it from `viii_oracle` (Lean v4.31.0, mathlib `fabf563a…`) with G08A and P08-A `raw/imports` on `LEAN_PATH`. Exit 0 in about 26 s. The output olean is byte-identical to the stored one: sha `a50e9a91…`. My own `#print axioms` on the scratch olean gave the same three axioms for all 14 headline theorems, and the printed definitions match FROZEN_TARGETS. |
| **Numerical cross-check against `typefree_fibers.py`** | OK | 40 random cases (n = 3–6, half full-rank U and half exact-rank U), using an independent `scipy.linalg.null_space` basis N and `pinv`. Worst errors against the Lean formulas: η 2e-16; centre 9e-16; F Fᵀ 3e-14; Python kernel is orthonormal (8e-15) and lies in ker A (5e-15). Forward and backward membership: zero norm excess, image residual ≤ 3e-15. Python `support` vs Lean formula 4e-15; vs SLSQP optimisation 1.5e-7 (optimiser tolerance). Random R basis change 4e-15. `ellipsoid_quotient_gauge` radius_sq vs η 2e-16. Branch probes: incompatible and η = 1.5 return EMPTY_SET; η = 1 returns BOUNDARY_NUMERICALLY_UNRESOLVED. |

## Blocking findings

None.

## Non-blocking notes

1. **η = 1 differs from Python.** Lean proves an exact singleton at η = 1. Python returns `BOUNDARY_NUMERICALLY_UNRESOLVED` inside its floating band (`:158-163`). This is expected under "exact algebra separate from numeric rank rule", but the return should say that the Lean singleton is not what the code outputs.
2. **The ellipsoid is defined from the factor L, not from U.** `Ell` is `{c + L z : z·z ≤ 1}` for any n×r matrix L. That matches what the code computes. The docstring form `c + U^{1/2}·ball`, and its equality with the L form whenever L Lᵀ = U, is not formalised.
3. **The gauge is stated in z-space.** Q5b says η is the minimum of z·z over the solutions. It is not stated as a Minkowski functional on x-space, and `ellipsoid_quotient_gauge` (whose `projection` argument is the observation operator) is not linked symbolically.
4. **Independence from the choice of X is only implicit.** Since `fibreImage_eq` holds for every Moore–Penrose X, any two choices give the same set, but no theorem states this.
5. **Q2a assumes η ≤ 1.** This is harmless, because for η > 1 both sides are the same centre point. The η > 1 case is simply not stated.
6. **Line range off by two.** PORT_MAP F4 is cited as lines 31-44, but the object runs from line 31 to 46. Cosmetic.
7. **Upstream P08-A has notes.** Q1, Q3 and Q5b inherit P08-A's PASS_WITH_NOTES review state.
8. **Reviewer is the same model family as the author** (see the reviewer line above).

## Not proved / out of scope

- That `_solve_range` or the SVD computes X and N to any accuracy (no numerical SVD link).
- Soundness of the floating `EMPTY_SET` and `BOUNDARY_NUMERICALLY_UNRESOLVED` statuses, and of the tolerances at `:22, 44, 51-52, 158`.
- The `POINT_IMAGE` and `NO_DIRECTIONS` status labels.
- The `U^{1/2}` ↔ L equivalence of the ellipsoid.
- `rational_polytope_fiber_support`.
- Physical units, the full PORT-CAS-08, and scientific admission (which stays at HOLD).

Scratch artifacts (source copy, rebuilt olean, audit, numeric check, `MANIFEST.sha256`) are in `/tmp/claude-1000/-home-cosmosapjw-Dropbox-bianchi-htt-base/aa20be99-6b30-4316-9fe2-fbf4edfcb6c6/scratchpad/p08b_rerun/`.
