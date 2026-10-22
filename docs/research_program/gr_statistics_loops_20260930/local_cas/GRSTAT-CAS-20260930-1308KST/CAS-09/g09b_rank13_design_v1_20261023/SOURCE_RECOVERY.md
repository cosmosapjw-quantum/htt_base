# G09-B source recovery: CAS-09 C01 (rank identity and two-radius 9+4 unisolvence)

Task card: `HTT_ALL_OBLIGATIONS_20261011_PACKAGE.zip::HTT_ALL_OBLIGATIONS_20261011/tasks/G09-B.json`
(card sha256 `c748e16fa9c6a5d6d3f9f18d995ef07cb26689d1a5ccedad1cac4f89bbd00fff`,
package sha256 `2d0b6da9308ab43e070a620f49241640b5aa7c80c277e1f0857edea22bc4af6f`).
Checkout HEAD when this file was written: `120c8a7487b5c5129a6e45e843281506e8b66095` (read-only; no git state
changes by this unit). Scientific admission: **HOLD**.

Paths are relative to `docs/research_program/gr_statistics_loops_20260930/` unless absolute.

## 1. Inputs read and their hashes

| role | path | sha256 |
|---|---|---|
| card source_path 1 (contract) | `cas/contracts/CAS-09.json` | `4913de308fc006f3658a45a88cd1d8400b1aaf3d1249927e677cca74842e4a3b` |
| card source_path 2 (blocker) | `local_cas/GRSTAT-CAS-20260930-1308KST/CAS-09/input_definition_blocker_v1_20261011/RETURN.json` | `e8b4e50f483df69d95d89a3423f3bbe0dd5f09ccc2efbf7afe6dba2740caeee5` |
| primary source (contract research provenance) | `statistics/NATIVE_INFERENCE_THEOREMS.md` | `e215836882047c50a1a5ae6da605d62aa2c553d0de055e279eee3ce35ec8e322` (matches contract) |
| neutral conventions | `cas/COMMON_SPEC.md` | `4714827e52acf3cb149f4014ac50ab2aa995dd4a0526f6b26ac7257807fe1897` (matches contract) |
| reused reviewed Lean (G09-A, imported unchanged) | `local_cas/.../CAS-09/g09a_definition_recovery_v1_20261014/lean/G09ADefinitions.lean` | `e39c42e70478ccb181785e8dcdf1c50248691fcca9433aaa1db3ef0bc477f86b` (= G09-A RETURN.json `sources`) |
| G09-A RETURN / REVIEW / ADDENDUM | `.../g09a_definition_recovery_v1_20261014/{RETURN.json,REVIEW.md,ADDENDUM_20261023.md}` | `11988dd6…2024` / `88d868a8…4fc` (review verdict PASS_WITH_NOTES, 0 blocking) / `9de38203…74fc` |
| G09-A SOURCE_RECOVERY / FROZEN_TARGETS | `.../g09a_definition_recovery_v1_20261014/{SOURCE_RECOVERY.md,FROZEN_TARGETS.md}` | `d7217d3b…7712` / `f11188d9…5f5` |

The definitions needed by G09-B (E4, E9 basis, D, X, two-radius layout, unisolvency, witness) were already
recovered by G09-A (see its SOURCE_RECOVERY §3, table "C01"); this unit re-uses them through `import
G09ADefinitions` and adds the explicit matrix forms. No new definition had to be recovered from PR history or
`htt/` (G09-A's search trail, `git log -S unisolvent`, `-S "R/(1+"`, `grep htt/`, is not repeated; its residual
UNKNOWN "concrete catalogue directions" still applies and is not needed by any G09-B target).

## 2. Source statements (NATIVE_INFERENCE_THEOREMS.md, §6) → G09-B Lean

| source (line) | statement | Lean (namespace `G09B`) |
|---|---|---|
| l.124 | "Let E4 have rows (1,n_iᵀ)" | `E4mat` (explicit `ι × Fin 4` matrix); `E4mat_mulVec`, `E4_eq_mulVec`, `range_E4mat`, `rank_E4mat` tie it to G09-A `E4` |
| l.124 | "any real basis of degree≤2 spherical polynomials, with E9 its N×9 evaluation matrix, containing the degree≤1 basis" | `E9mat` with columns `1,n0,n1,n2,n0²−n2²,2n0n1,2n0n2,n1²−n2²,2n1n2` (= G09-A STF coordinates via `hcoord`/`hdecode`); `E9mat_first_cols` (first four columns = E4); `E9_basis_change_det`, `E9_basis_change_rank` (any other basis `E9mat*P`, `det P≠0`) |
| l.124 | "D=diag(r_i/c), all r_i>0" | `Dmat r c := diagonal (r/c)`; `Dmat_mulVec`; `rank_DE9mat` (needs `r_i>0`, `c>0`) |
| l.126–128, eq.(10) | "X=[E4, D E9] with 13 columns" | `Xmat := fromCols E4mat (Dmat * E9mat)`; `Xmat_mulVec`, `Xmap_eq_mulVec`, `range_Xmat`, `rank_Xmat` |
| l.136 (proof of N3) | "For any matrices A,B, dim(col(A)+col(B)) equals rank(A)+rank(B)−dim(col(A)∩col(B))" | general: `dim_sup_add_dim_inf` (= Mathlib `Submodule.finrank_sup_add_finrank_inf_eq`), `dim_sup_eq_sub` (ℕ), `dim_sup_eq_sub_int` (ℤ), `range_fromCols`, `rank_fromCols_add`, `rank_fromCols_eq_sub`; instance: `Xmat_rank_concat`, `Xmat_rank_eq_sub`; G09-A `rank_concat_identity` |
| contract C01 / `uncontracted_research_targets[0]` (CAS-09.json l.105, l.252) | "rank[E4,DE9]=rankE4+rankE9−dim intersection" | `Xmat_rank_eq_sub` (ℕ, shown exact), `Xmat_rank_concat` (additive) |
| l.130–134 | Theorem N3 criterion (11) | reused G09-A `rank13_iff` (unchanged) |
| l.150 | "nine unisolvent directions at one radius R1>0. Repeat four of those directions at a distinct positive radius R2, choosing the four so their E4 submatrix has rank 4. Then rank X=13" | `two_radius_Xmat_rank13_of_ranks` (hyps `rank E9mat = 9`, `rank E4mat(dir9∘σ) = 4`, `R1>0`, `R2>0`, `R1≠R2`, `c>0`), `two_radius_Xmat_rank13_of_det` (same with the "declared nonzero determinants" `det E9mat(dir9)≠0`, `det E4mat(dir9∘σ)≠0`), `two_radius_ker_eq_bot_of_det`, `two_radius_Xmat_mulVec_eq_zero` |
| l.138 | "unisolvent directions (rank E9=9)" | `E9_injective_iff_rank`, `E9_injective_iff_det` (G09-A convention `Function.Injective (E9 dir)` ⇔ rank 9 ⇔ det ≠ 0) |
| l.150 (elimination) | "a zero linear combination in the first nine rows … vanishes identically. Thus its slope polynomial equals −(c/R1) times its intercept polynomial. At the four repeated directions, the remaining equation is (1−R2/R1)p(n)=0" | `two_radius_ker_iff`: `X(a,h)=0 ↔ h = −(c/R1)·lift(a) ∧ (1−R2/R1)·E4_σ a = 0` (exact basis identity `Hval (liftLin a) n = ipoly a n`, G09-A `Hval_liftLin`) |
| l.150 | "Rank four and R1≠R2 force p=0, and then the slope vanishes" | `two_radius_ker_eq_bot_of_det` |
| contract `singular_loci` | DESIGN-R1R2 equal fails; DESIGN-ANGULAR rank deficient | `two_radius_Xmat_equal_radius_le9`, `witness_equal_radius_le9`; `two_radius_Xmat_rank_lt13_of_det4_eq_zero` |
| contract `canonical_form[0]` | "Exact rational/algebraic sphere direction certificates and basis recorded" | G09-A witness `dirStar`, `σStar` (author-supplied certificate, same point set as the historical `CAS-09/wolfram_xact/check.wl` l.10–11; not a recovered catalogue); `witness_E4block`, `witness_det4` (= −2), `witness_det9_ne_zero`, `witness_Xmat_rank13` |

## 3. Hypothesis alignment (card acceptance 2)

Every nonzero-determinant / radius assumption stated by the source at l.124 and l.150 appears as a hypothesis
of `two_radius_Xmat_rank13_of_det` / `_of_ranks` / `two_radius_ker_eq_bot_of_det`:
`R1>0` (`hR1`), "distinct positive radius R2" (`hR2`, `hne : R1 ≠ R2`), unisolvent nine (`hdet9` or `hrank9`),
rank-4 repeated E4 submatrix (`hdet4` or `hrank4`), `c>0` (`hc`; D=diag(r/c) convention of G09-A/contract).
`hR2` is not used by the proof (Lean linter note) but is kept because the source states it; the kernel lemma
`two_radius_ker_iff` is stated without `R2>0`, `R1≠R2` and without any E4 hypothesis (more general).
No hypothesis states kernel = 0, injectivity of X, or rank 13.

## 4. Residual UNKNOWN

* Concrete catalogue directions/radii: absent from the repository (G09-A §4 item 1). Not needed: all
  G09-B theorems are universal over directions satisfying the source hypotheses, plus the exact witness.
* Exact value of the witness 9×9 determinant is not proved in Lean (only `≠ 0`, exactly, via linear
  independence). Unlock: a Lean determinant evaluation (e.g. block/row-reduction certificate) if a value is needed.
