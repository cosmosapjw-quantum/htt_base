# G09-B — independent review (verbatim final report of a fresh read-only reviewer)

# G09-B fresh independent review: two-radius 9+4 rank-13 design (CAS-09 C01)

**Reviewer model:** Claude Opus 5.5 (`claude-opus-5-5`), self-reported and not attested.

**Mode:** read-only. I edited no repository files and ran no state-changing git commands. Scratch work is in `/tmp/claude-1000/-home-cosmosapjw-Dropbox-bianchi-htt-base/aa20be99-6b30-4316-9fe2-fbf4edfcb6c6/scratchpad/g09-b_rerun/`.

**Target directory:** `/home/cosmosapjw/Dropbox/bianchi/htt_base/docs/research_program/gr_statistics_loops_20260930/local_cas/GRSTAT-CAS-20260930-1308KST/CAS-09/g09b_rank13_design_v1_20261023/`

## Verdict: PASS_WITH_NOTES (scoped). No blocking findings.

All four card lean_steps are proved, exactly and without floating-point rank, in Lean 4.31.0 with mathlib `fabf563a`. I recompiled independently and got exit 0. Every axiom report shows only `[propext, Classical.choice, Quot.sound]`.

The theorem hypotheses match the source assumptions at l.150. My exact sympy computation shows they are sharp: det X = ±det E9 · det E4σ · R1⁵ (R1−R2)⁴ / c⁹.

Scientific admission stays **HOLD**.

---

## Per-check table

| # | Check | Result | Evidence |
|---|---|---|---|
| 0 | Card read | done | Card sha256 `c748e16f…0fff` and package `2d0b6da9…f6f` both match SOURCE_RECOVERY and AUTHOR_RETURN. |
| 1a | Source citations in SOURCE_RECOVERY | PASS | NATIVE_INFERENCE_THEOREMS.md (sha `e2158368…e322`, matches): l.124 has E4, E9, D=diag(r/c) and r_i>0; l.126 is eq.(10); l.130–134 is N3; l.136 is the dimension formula; l.138 is unisolvent = rank E9 = 9; l.150 is the 9+4 design and the elimination. CAS-09.json (`4913de30…a3b`) has C01 at l.105 and the uncontracted target at l.252. Blocker RETURN (`e8b4e50f…ee5`) and COMMON_SPEC (`4714827e…1897`) match. G09-A files match: lean `e39c42e7…f86b`, RETURN `11988dd6…2024`, REVIEW `88d868a8…2b65` (PASS_WITH_NOTES, 0 blocking), ADDENDUM `9de38203…74fc`, SOURCE_RECOVERY `d7217d3b…7712`, FROZEN `f11188d9…5f5`. The witness point set matches the historical `CAS-09/wolfram_xact/check.wl` l.10–11. |
| 1b | Faithfulness: dimension formula (step 1), including ℕ-subtraction | PASS | `dim_sup_eq_sub` and `rank_fromCols_eq_sub` are derived from the additive Mathlib identity by `omega`, so truncation cannot bite: the intersection's dimension is at most each part's. There is also an ℤ form (`dim_sup_eq_sub_int`). Instantiated on actual ranges by `Xmat_rank_concat` and `Xmat_rank_eq_sub`. `witness_const_radius_dims` is a boundary instance with a nonzero intersection, 4+9−4=9. My sympy check agrees: constant-radius rank X = 9 and intersection dim = 4. |
| 1c | Design range = subspace sum (step 2), tied to G09-A | PASS | `range_fromCols`, `range_Xmat_eq_sup` and `range_Xmap_eq_sup` give the sum. `Xmat_mulVec`/`Xmap_eq_mulVec` and `range_Xmat`/`rank_Xmat` tie `Xmat` to G09-A `Xmap`. `E4mat_mulVec`, `E9mat_mulVec` and `Dmat_mulVec` tie the blocks to G09-A `E4`, `E9`, `Dmap`. `rank_DE9mat` needs r_i>0 and c>0, as in the source ("D invertible"). |
| 1d | E9 basis / normalization | PASS | sympy confirms G09-A `quad` = Σ q_i·(n0²−n2², 2n0n1, 2n0n2, n1²−n2², 2n1n2) symbolically. `E9mat_first_cols` shows the basis contains the degree≤1 basis (source l.124). |
| 1e | Kernel elimination (step 3) | PASS | `two_radius_ker_iff` gives X(a,h)=0 ↔ h = −(c/R1)·lift a ∧ (1−R2/R1)·E4σ a = 0. Hand check: an R1 row gives p + (R1/c)H = 0, so H = −(c/R1)p. An R2 row then gives (1−R2/R1)p = 0. Both match l.150 verbatim. The lemma is stated without R2>0, R1≠R2 or any E4 hypothesis, which makes it more general. |
| 1f | Kernel = 0 / rank 13 (step 4) and hypothesis alignment (acceptance 2) | PASS | `two_radius_Xmat_rank13_of_det` hypotheses: R1>0, R2>0, c>0, R1≠R2, det E9mat(dir9)≠0, det E4mat(dir9∘σ)≠0. `_of_ranks` is the same with rank 9 / rank 4. Each corresponds to a source assumption: "R1>0", "distinct positive radius R2", "unisolvent", "E4 submatrix rank 4", and r_i>0. The only addition is c>0 (the convention behind D=diag(r/c); see note N1). None is missing. No hypothesis assumes kernel = 0, injectivity or rank 13. |
| 1g | Exact determinants and rank (acceptance 1), recomputed in sympy (`sympy_check.py`) | PASS | The E4 block is [[1,1,0,0],[1,−1,0,0],[1,0,1,0],[1,0,0,1]]. det4 = −2, matching Lean `witness_det4`. det9 = 331776/15625 ≠ 0, matching `witness_det9_ne_zero` (Lean proves ≠0 only, through linear independence, and claims no value). rank X = 13 at (R1,R2) = (1,2), (2,1), (1,1/3), (3,7) and rank 9 at R1=R2. Symbolically, det X(13×13) = −663552·R1⁵(R1−R2)⁴/(15625 c⁹). Three random non-unit rational designs (`sympy_general.py`) give det X/(det9·det4) = R1⁵(R1−R2)⁴/c⁹. So the hypothesis set is sharp: R1≠0, c≠0, R1≠R2, det9≠0, det4≠0, and R2>0 is redundant. |
| 1h | Pitfall: witness not generalized | PASS | The universal theorems carry the source hypotheses. The witness is used only for non-vacuity. Directions are not required to be unit vectors, which strengthens the statement. |
| 1i | Negative controls genuine | PASS | `two_radius_Xmat_rank_lt13_of_det4_eq_zero` (DESIGN-ANGULAR) assumes only det4=0, R1>0, c>0. `two_radius_Xmat_equal_radius_le9` and `witness_equal_radius_le9` (DESIGN-R1R2) apply with both determinants nonzero, which shows R1≠R2 is needed. I also instantiated σ=(0,0,2,4) (repeated row) in Lean: rank < 13 compiles. In sympy that design has rank 12. |
| 2 | No assumed conclusion; no vacuity | PASS | My `audit/ReviewAudit.lean` instantiates three things. (i) The DESIGN-ANGULAR control. (ii) The RHS of `two_radius_ker_iff` with a = (1,0) ≠ 0 at R1=R2, giving a nonzero kernel vector, so the iff is non-vacuous both ways. (iii) `two_radius_Xmat_rank13_of_det` on a second design (R1=3, R2=7, c=2). It also re-derives the matrix rank 13 from G09-A `two_radius_rank13` via `rank_Xmat`. All compile. |
| 3a | Integrity: hashes | PASS | Recomputed sha256 matches AUTHOR_RETURN for every file. Lean `2f409375…9055` (= compile_06 source); AxiomAudit `e05937d3…af4`; run_compile `68724cc2…cd7`; oleans `3f5a19e1…eb2` and `be85bbb5…c22`. All seven stdout hashes match. All stderr are the empty hash. SOURCE_RECOVERY `176fd19c…12f7`; FROZEN `a248bcc2…c2c2`; snapshot `f9631312…7563`. |
| 3b | Exit codes; failed attempts kept | PASS | 01 import exit 0, 02 main exit 1, 03 probe exit 1, 04 probe exit 1, 05 main exit 1, 06 main exit 0, 07 audit exit 0. All sources are kept as `compile_NN_*.source.lean`. Probe 03's source (`472f…`) survives only in its snapshot, because `raw/probes/Probe.lean` now holds probe 04 (`fda4…`). That is acceptable. |
| 3c | Freeze predates compiles | PASS | Snapshot mtime is 2026-10-22 18:40:13.08Z. First receipt (import) is 18:40:16.61Z; first main compile is 18:43:22Z. The source hash at freeze (`b20311aa…`) equals the compile_02 source. |
| 3d | Post-freeze changes | PASS | My own header diff (`sigdiff.py`) finds 62 declarations in the source and 61 in the freeze. The only extra is `witness_E4block`; no frozen header changed. The source diff from compile_02 to final is: added `open scoped Matrix`, added `witness_E4block`, and proof-only edits in `witness_det4` and `two_radius_Xmat_mulVec_eq_zero`. `open scoped Matrix` only enables the `*ᵥ` notation the frozen text already used. Before it, the file failed to elaborate, so no alternative meaning was ever compiled. |
| 3e | Forbidden tokens / axioms | PASS | grep for `sorry\|admit\|native_decide\|axiom\|set_option\|opaque\|implemented_by\|extern\|unsafe\|decide` in `lean/` and `AxiomAudit.lean` finds nothing. My audit runs `#print axioms` on all 62 G09B declarations (54 theorems + 8 defs). All 62 print `[propext, Classical.choice, Quot.sound]`; no other axiom appears. |
| 4 | Independent recompile | PASS | From `/home/cosmosapjw/lean_oracles/viii_oracle` (toolchain v4.31.0, manifest mathlib rev `fabf563a7c95a166b8d7b6efca11c8b4dc9d911f`) I rebuilt `G09ADefinitions.olean` from the copied source (`e39c42e7…`), exit 0 (2 linter warnings). Then `lake env bash -c "LEAN_PATH=<S>/imports:$LEAN_PATH lean -R <S>/srcB -o <S>/imports/G09BRankDesign.olean <S>/srcB/G09BRankDesign.lean"` gave exit 0, empty stderr and 7 linter warnings, identical in kind to compile_06. The reviewer audit compiled with exit 0. |
| 5 | Overlap with G09-A: is G09-B genuinely closed? | PASS (scoped), see N5 | G09-A already proved most of C01 in linear-map form (details in N5). G09-B adds new content: explicit `Matrix.rank` of `[E4, D E9]`; the source's "declared nonzero determinants" as literal hypotheses, with det ↔ injective ↔ rank equivalences; ℕ/ℤ subtraction forms; the exact kernel iff; an exact det4 = −2; and the subspace-sum identification for matrices. These are exactly the card items G09-A did not state, so the card is closed by this unit. |

## Blocking findings

None.

## Non-blocking notes

- **N1 (hypothesis `hc : 0 < c`).** l.150 does not state c>0 literally. It is the speed-of-light convention behind D = diag(r/c) in l.124 and the contract. It is needed: in Lean, r/0 = 0 gives X = [E4, 0], and the exact det X contains 1/c⁹. SOURCE_RECOVERY §3 already records it as a convention. Optional fix: add one line to FROZEN_TARGETS saying "c ≠ 0 suffices; c>0 is the physical convention."
- **N2 (`hR2` redundant).** The exact det formula shows R2>0 plays no role. Keeping it is faithful to the source and is not a weakening. Optional fix: rename it `_hR2`, or add a comment, to silence the linter.
- **N3 (basis independence is partial).** `E9_basis_change_det` and `_rank` take another basis abstractly as `E9mat * P` with det P ≠ 0. The fact that any other real basis of degree≤2 spherical polynomials evaluates to `E9mat * P` holds only for unit directions, and it is not formalized. The G09-B theorems themselves do not assume unit directions, which strengthens them. Optional fix: add a FROZEN_TARGETS sentence that this representation is assumed, not proved.
- **N4 (docstring line reference).** The docstring of `Xmat_rank_concat` says "NATIVE l.132". The dimension formula is at l.136; l.132 is eq. (11). Cosmetic.
- **N5 (overlap and evidence accounting).** G09-A already proved `rank_concat_identity`, `rank13_iff`, `two_radius_injective`, `two_radius_rank13` and `witness_rank13`. G09-B's increment is representational (matrix and determinant form) plus the exact kernel iff and det4. Do not count G09-A and G09-B as independent evidence for C01.
- **N6 (no unisolvency negative control in G09-B).** No G09-B negative control shows det9 = 0 forces rank < 13. It follows from G09-A `rank13_iff`, because the 13 rows contain only the nine distinct directions. Optional.
- **N7 (card tool_tasks).** No sympy, sage_singular or Wolfram receipts were produced by the author. Lean's exact proofs satisfy acceptance 1. My sympy scripts are reviewer-side corroboration only and are not author receipts.
- **N8 (runtime).** The observed author runtime, model and billing are UNKNOWN, as AUTHOR_RETURN correctly records.

## Not proved / not claimed

- Scientific admission: **HOLD**.
- The exact value of the 9×9 witness determinant in Lean; only ≠ 0 is proved. Sympy gives 331776/15625, which is not a Lean claim.
- The "two full unisolvent shells" design, and stability under small perturbations (continuity of a nonzero minor).
- The projector form rank[(I−P4) D E9] = 9; physical rank 12 (that is G09-A C02); any precision or conditioning statement.
- Any catalogue-specific design, and any generalization of the witness into a universal design theorem.
- The representation "any other basis = E9mat·P" on the sphere (N3).
- CAS-09 four-axis status, and any Wolfram/Sage/SymPy axis receipt from the author.
- Card acceptance 4 is satisfied only by this review.

## Recommended VALIDATION_MATRIX scientific-row update (I did not apply it)

`G09-B | CAS-09 C01 | Lean exact (4.31.0 / mathlib fabf563a) | PASS_WITH_NOTES (fresh review, Opus 5.5) | 0 blocking | hyps {R1>0,R2>0(redundant),c>0(convention),R1≠R2,det E9≠0,det E4σ≠0} sharp vs sympy det X = ±det9·det4·R1⁵(R1−R2)⁴/c⁹ | witness det4=−2, det9=331776/15625 (sympy only), rank13 | overlap with G09-A noted | scientific admission HOLD`

## Files

Reviewed:
- `.../CAS-09/g09b_rank13_design_v1_20261023/lean/G09BRankDesign.lean`
- `.../g09b_rank13_design_v1_20261023/FROZEN_TARGETS.md`
- `.../g09b_rank13_design_v1_20261023/SOURCE_RECOVERY.md`
- `.../g09b_rank13_design_v1_20261023/AUTHOR_RETURN.json`
- `.../g09b_rank13_design_v1_20261023/raw/compile_0[1-7]_*`
- `.../g09b_rank13_design_v1_20261023/raw/AxiomAudit.lean`
- `/home/cosmosapjw/Dropbox/bianchi/htt_base/docs/research_program/gr_statistics_loops_20260930/statistics/NATIVE_INFERENCE_THEOREMS.md`

Reviewer scratch, all under `/tmp/claude-1000/-home-cosmosapjw-Dropbox-bianchi-htt-base/aa20be99-6b30-4316-9fe2-fbf4edfcb6c6/scratchpad/g09-b_rerun/`:
- `/tmp/claude-1000/-home-cosmosapjw-Dropbox-bianchi-htt-base/aa20be99-6b30-4316-9fe2-fbf4edfcb6c6/scratchpad/g09-b_rerun/audit/ReviewAudit.lean`
- `/tmp/claude-1000/-home-cosmosapjw-Dropbox-bianchi-htt-base/aa20be99-6b30-4316-9fe2-fbf4edfcb6c6/scratchpad/g09-b_rerun/audit.stdout`
- `/tmp/claude-1000/-home-cosmosapjw-Dropbox-bianchi-htt-base/aa20be99-6b30-4316-9fe2-fbf4edfcb6c6/scratchpad/g09-b_rerun/compileA.stdout`
- `/tmp/claude-1000/-home-cosmosapjw-Dropbox-bianchi-htt-base/aa20be99-6b30-4316-9fe2-fbf4edfcb6c6/scratchpad/g09-b_rerun/compileB.stdout`
- `/tmp/claude-1000/-home-cosmosapjw-Dropbox-bianchi-htt-base/aa20be99-6b30-4316-9fe2-fbf4edfcb6c6/scratchpad/g09-b_rerun/sympy_check.py`
- `/tmp/claude-1000/-home-cosmosapjw-Dropbox-bianchi-htt-base/aa20be99-6b30-4316-9fe2-fbf4edfcb6c6/scratchpad/g09-b_rerun/sympy_general.py`
- `/tmp/claude-1000/-home-cosmosapjw-Dropbox-bianchi-htt-base/aa20be99-6b30-4316-9fe2-fbf4edfcb6c6/scratchpad/g09-b_rerun/sigdiff.py`
- `/tmp/claude-1000/-home-cosmosapjw-Dropbox-bianchi-htt-base/aa20be99-6b30-4316-9fe2-fbf4edfcb6c6/scratchpad/g09-b_rerun/imports/`
