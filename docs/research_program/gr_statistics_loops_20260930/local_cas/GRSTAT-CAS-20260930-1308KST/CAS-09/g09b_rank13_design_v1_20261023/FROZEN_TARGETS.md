# G09-B frozen targets (written before any proof compile)

Module `lean/G09BRankDesign.lean`, namespace `G09B` (opens `G09A`). It imports the reviewed G09-A module
`G09ADefinitions` UNCHANGED (source sha256 `e39c42e70478ccb181785e8dcdf1c50248691fcca9433aaa1db3ef0bc477f86b`).
Toolchain: Lean 4.31.0, Mathlib `fabf563a7c95a166b8d7b6efca11c8b4dc9d911f`
(Lake project `/home/cosmosapjw/lean_oracles/viii_oracle`). Section variables: in section `General`
`{K : Type*} [Field K]` and `{m n₁ n₂ : Type*} [Fintype m] [Fintype n₁] [Fintype n₂]`; in section `Matrices`
`{ι : Type*} [Fintype ι]`. Scientific admission: HOLD. Source map: `SOURCE_RECOVERY.md`.

Card: `HTT_ALL_OBLIGATIONS_20261011/tasks/G09-B.json` — scope "C01 rank-of-concatenation intersection and
explicit nonzero determinant based rank13".

## Fidelity to the card / source (NATIVE_INFERENCE_THEOREMS.md l.124–157)

* "Rank" of `X=[E4, D E9]` is now ALSO the literal `Matrix.rank` of an explicit `ι × (Fin 4 ⊕ Fin 9)` real
  matrix `Xmat = fromCols E4mat (diag(r/c) * E9mat)`; `rank_Xmat` ties it to the G09-A linear-map rank.
* E9 basis (source: "any real basis … containing the degree≤1 basis", l.124–125): the explicit columns are
  `1, n0, n1, n2, n0²−n2², 2n0n1, 2n0n2, n1²−n2², 2n1n2` (exactly the G09-A STF coordinates), the first four are
  E4 (`E9mat_first_cols`), and any other basis `E9mat * P`, `det P ≠ 0`, has the same rank and nonzero-ness of
  determinant (`E9_basis_change_rank`, `E9_basis_change_det`).
* Source hypotheses for the 9+4 design (l.150), kept verbatim as theorem hypotheses of
  `two_radius_*_of_det` / `_of_ranks`: `R1 > 0`; repeated radius `R2 > 0`; `R1 ≠ R2`; nine unisolvent
  directions = `det E9mat(dir9) ≠ 0` (equivalently rank 9, `E9_injective_iff_det`, `E9_injective_iff_rank`);
  four repeated directions with E4 submatrix of rank 4 = `det E4mat(dir9∘σ) ≠ 0`
  (`E4_injective_iff_det`, `E4_injective_iff_rank`); plus `c > 0` (contract/G09-A convention for D=diag(r/c)).
  No hypothesis assumes kernel = 0 or rank 13.
* `two_radius_ker_iff` (kernel elimination) needs only `R1 > 0`, `c > 0`, unisolvency; it is an exact
  characterization for ALL `R2` (no `R2 > 0`, no `R1 ≠ R2`, no E4 hypothesis) — a more general statement.
* Dimension formula: additive form, ℕ truncated-subtraction form (shown exact via the additive form), ℤ form.
* Exact arithmetic only; no floating rank. The witness is the G09-A rational design (R1=1, R2=2, c=1);
  it is NOT generalized: universal statements carry the source hypotheses.

## Card step / acceptance → theorem map

| card item | Lean (G09-B new) | reused G09-A (unchanged) |
|---|---|---|
| lean_step 1: dim(U+V)=dimU+dimV−dim(U∩V) | `dim_sup_add_dim_inf`, `dim_sup_eq_sub`, `dim_sup_eq_sub_int`, `dim_inf_le_left/right`, `rank_fromCols_add`, `rank_fromCols_eq_sub`, `Xmat_rank_concat`, `Xmat_rank_eq_sub` | `rank_concat_identity`, `rank13_iff` |
| lean_step 2: [E4, D E9] range = subspace sum | `range_fromCols`, `range_Xmap_eq_sup`, `range_Xmat_eq_sup`, `range_E4mat`, `range_E9mat`, `range_DE9mat`, `range_Xmat`, `rank_*mat`, `rank_DE9mat`, `Xmat_mulVec`, `Xmap_eq_mulVec`, `E9mat_first_cols` | `Xmap`, `finrank_range_DE9` |
| lean_step 3: two-radius coefficient-kernel elimination with exact basis identities | `two_radius_ker_iff` (uses `Hval_liftLin`: H(lift a)=p_a) | `two_radius_injective`, `Hval_liftLin` |
| lean_step 4: kernel=0 / rank13 from determinants & radius inequality | `two_radius_ker_eq_bot_of_det`, `two_radius_Xmat_mulVec_eq_zero`, `two_radius_Xmat_rank13_of_det`, `two_radius_Xmat_rank13_of_ranks`, `E9_injective_iff_det`, `E4_injective_iff_det`, `E9_injective_iff_rank`, `E4_injective_iff_rank` | `two_radius_rank13`, `finrank_range_of_injective_13` |
| acceptance 1: exact determinant / linear independence | `witness_det4` (= −2 exactly), `witness_det9_ne_zero` (exact via linear independence), `witness_Xmat_rank13` | `dirStar_unisolvent`, `σStar_E4`, `witness_rank13` |
| acceptance 2: all source nonzero-det/radius assumptions = hypotheses | see fidelity list; negative controls `two_radius_Xmat_rank_lt13_of_det4_eq_zero` (det4=0), `two_radius_Xmat_equal_radius_le9`, `witness_equal_radius_le9` (R1=R2) | `two_radius_fails_of_E4_deficient`, `two_radius_equal_fails` |
| pitfall: ℕ subtraction boundary | `dim_sup_eq_sub`, `dim_sup_eq_sub_int`, `witness_const_radius_dims` (nonzero intersection: 4+9−4=9) | — |

## Explicitly not targeted (no claim)

* Exact numeric value of the 9×9 witness determinant (only `≠ 0`, exactly); reviewer's sympy value 331776/15625 is not a Lean claim.
* "Two full unisolvent shells", small-perturbation stability "by continuity of a nonzero minor" (l.150 last sentences).
* Projector form rank[(I−P4) D E9]=9; physical rank 12 (G09-A C02); any precision/conditioning statement.
* Any catalogue-specific design (no catalogue directions exist in the repository).

## Exact frozen Lean signatures (auto-extracted from the source before compiling)

```lean
theorem dim_sup_add_dim_inf {V : Type*} [AddCommGroup V] [Module K V] (U W : Submodule K V) [FiniteDimensional K U] [FiniteDimensional K W] : Module.finrank K ↥(U ⊔ W) + Module.finrank K ↥(U ⊓ W) = Module.finrank K ↥U + Module.finrank K ↥W
theorem dim_inf_le_left {V : Type*} [AddCommGroup V] [Module K V] (U W : Submodule K V) [FiniteDimensional K U] : Module.finrank K ↥(U ⊓ W) ≤ Module.finrank K ↥U
theorem dim_inf_le_right {V : Type*} [AddCommGroup V] [Module K V] (U W : Submodule K V) [FiniteDimensional K W] : Module.finrank K ↥(U ⊓ W) ≤ Module.finrank K ↥W
theorem dim_sup_eq_sub {V : Type*} [AddCommGroup V] [Module K V] (U W : Submodule K V) [FiniteDimensional K U] [FiniteDimensional K W] : Module.finrank K ↥(U ⊔ W) = Module.finrank K ↥U + Module.finrank K ↥W - Module.finrank K ↥(U ⊓ W)
theorem dim_sup_eq_sub_int {V : Type*} [AddCommGroup V] [Module K V] (U W : Submodule K V) [FiniteDimensional K U] [FiniteDimensional K W] : (Module.finrank K ↥(U ⊔ W) : ℤ) = Module.finrank K ↥U + Module.finrank K ↥W - Module.finrank K ↥(U ⊓ W)
theorem range_eq_of_transfer {M₁ M₂ W : Type*} [AddCommGroup M₁] [Module K M₁] [AddCommGroup M₂] [Module K M₂] [AddCommGroup W] [Module K W] (A : M₁ →ₗ[K] W) (B : M₂ →ₗ[K] W) (f : M₁ → M₂) (g : M₂ → M₁) (hf : ∀ x, A x = B (f x)) (hg : ∀ y, B y = A (g y)) : LinearMap.range A = LinearMap.range B
theorem range_fromCols (A : Matrix m n₁ K) (B : Matrix m n₂ K) : LinearMap.range (Matrix.fromCols A B).mulVecLin = LinearMap.range A.mulVecLin ⊔ LinearMap.range B.mulVecLin
theorem rank_fromCols_add (A : Matrix m n₁ K) (B : Matrix m n₂ K) : (Matrix.fromCols A B).rank + Module.finrank K ↥(LinearMap.range A.mulVecLin ⊓ LinearMap.range B.mulVecLin) = A.rank + B.rank
theorem rank_fromCols_eq_sub (A : Matrix m n₁ K) (B : Matrix m n₂ K) : (Matrix.fromCols A B).rank = A.rank + B.rank - Module.finrank K ↥(LinearMap.range A.mulVecLin ⊓ LinearMap.range B.mulVecLin)
def icoord (a : IPar) : Fin 4 → ℝ
def idecode (v : Fin 4 → ℝ) : IPar
def hcoord (h : HPar) : Fin 9 → ℝ
def hdecode (v : Fin 9 → ℝ) : HPar
theorem idecode_icoord (a : IPar) : idecode (icoord a) = a
theorem icoord_idecode (v : Fin 4 → ℝ) : icoord (idecode v) = v
theorem hdecode_hcoord (h : HPar) : hdecode (hcoord h) = h
theorem hcoord_hdecode (v : Fin 9 → ℝ) : hcoord (hdecode v) = v
def E4mat (dir : ι → V3) : Matrix ι (Fin 4) ℝ
def E9mat (dir : ι → V3) : Matrix ι (Fin 9) ℝ
noncomputable def Dmat [DecidableEq ι] (r : ι → ℝ) (c : ℝ) : Matrix ι ι ℝ
noncomputable def Xmat [DecidableEq ι] (dir : ι → V3) (r : ι → ℝ) (c : ℝ) : Matrix ι (Fin 4 ⊕ Fin 9) ℝ
theorem E9mat_first_cols (dir : ι → V3) (i : ι) (k : Fin 4) : E9mat dir i (Fin.castLE (by norm_num) k) = E4mat dir i k
theorem E4mat_mulVec (dir : ι → V3) (v : Fin 4 → ℝ) : E4mat dir *ᵥ v = E4 dir (idecode v)
theorem E9mat_mulVec (dir : ι → V3) (v : Fin 9 → ℝ) : E9mat dir *ᵥ v = E9 dir (hdecode v)
theorem E4_eq_mulVec (dir : ι → V3) (a : IPar) : E4 dir a = E4mat dir *ᵥ icoord a
theorem E9_eq_mulVec (dir : ι → V3) (h : HPar) : E9 dir h = E9mat dir *ᵥ hcoord h
theorem Dmat_mulVec [DecidableEq ι] (r : ι → ℝ) (c : ℝ) (v : ι → ℝ) : Dmat r c *ᵥ v = Dmap r c v
theorem DE9mat_mulVec [DecidableEq ι] (dir : ι → V3) (r : ι → ℝ) (c : ℝ) (v : Fin 9 → ℝ) : (Dmat r c * E9mat dir) *ᵥ v = (Dmap r c).comp (E9 dir) (hdecode v)
theorem Xmat_mulVec [DecidableEq ι] (dir : ι → V3) (r : ι → ℝ) (c : ℝ) (v : Fin 4 ⊕ Fin 9 → ℝ) : Xmat dir r c *ᵥ v = Xmap dir r c (idecode (v ∘ Sum.inl), hdecode (v ∘ Sum.inr))
theorem Xmap_eq_mulVec [DecidableEq ι] (dir : ι → V3) (r : ι → ℝ) (c : ℝ) (a : IPar) (h : HPar) : Xmap dir r c (a, h) = Xmat dir r c *ᵥ Sum.elim (icoord a) (hcoord h)
theorem range_E4mat (dir : ι → V3) : LinearMap.range (E4mat dir).mulVecLin = LinearMap.range (E4 dir)
theorem range_E9mat (dir : ι → V3) : LinearMap.range (E9mat dir).mulVecLin = LinearMap.range (E9 dir)
theorem range_DE9mat [DecidableEq ι] (dir : ι → V3) (r : ι → ℝ) (c : ℝ) : LinearMap.range (Dmat r c * E9mat dir).mulVecLin = LinearMap.range ((Dmap r c).comp (E9 dir))
theorem range_Xmat [DecidableEq ι] (dir : ι → V3) (r : ι → ℝ) (c : ℝ) : LinearMap.range (Xmat dir r c).mulVecLin = LinearMap.range (Xmap dir r c)
theorem range_Xmap_eq_sup (dir : ι → V3) (r : ι → ℝ) (c : ℝ) : LinearMap.range (Xmap dir r c) = LinearMap.range (E4 dir) ⊔ LinearMap.range ((Dmap r c).comp (E9 dir))
theorem range_Xmat_eq_sup [DecidableEq ι] (dir : ι → V3) (r : ι → ℝ) (c : ℝ) : LinearMap.range (Xmat dir r c).mulVecLin = LinearMap.range (E4mat dir).mulVecLin ⊔ LinearMap.range (Dmat r c * E9mat dir).mulVecLin
theorem rank_E4mat (dir : ι → V3) : (E4mat dir).rank = Module.finrank ℝ (LinearMap.range (E4 dir))
theorem rank_E9mat (dir : ι → V3) : (E9mat dir).rank = Module.finrank ℝ (LinearMap.range (E9 dir))
theorem rank_Xmat [DecidableEq ι] (dir : ι → V3) (r : ι → ℝ) (c : ℝ) : (Xmat dir r c).rank = Module.finrank ℝ (LinearMap.range (Xmap dir r c))
theorem rank_DE9mat [DecidableEq ι] (dir : ι → V3) (r : ι → ℝ) (c : ℝ) (hr : ∀ i, 0 < r i) (hc : 0 < c) : (Dmat r c * E9mat dir).rank = (E9mat dir).rank
theorem Xmat_rank_concat [DecidableEq ι] (dir : ι → V3) (r : ι → ℝ) (c : ℝ) (hr : ∀ i, 0 < r i) (hc : 0 < c) : (Xmat dir r c).rank + Module.finrank ℝ ↥(LinearMap.range (E4mat dir).mulVecLin ⊓ LinearMap.range (Dmat r c * E9mat dir).mulVecLin) = (E4mat dir).rank + (E9mat dir).rank
theorem Xmat_rank_eq_sub [DecidableEq ι] (dir : ι → V3) (r : ι → ℝ) (c : ℝ) (hr : ∀ i, 0 < r i) (hc : 0 < c) : (Xmat dir r c).rank = (E4mat dir).rank + (E9mat dir).rank - Module.finrank ℝ ↥(LinearMap.range (E4mat dir).mulVecLin ⊓ LinearMap.range (Dmat r c * E9mat dir).mulVecLin)
theorem E9_injective_iff_det (dir9 : Fin 9 → V3) : Function.Injective (E9 dir9) ↔ (E9mat dir9).det ≠ 0
theorem E4_injective_iff_det (dir4 : Fin 4 → V3) : Function.Injective (E4 dir4) ↔ (E4mat dir4).det ≠ 0
theorem E9_injective_iff_rank {ι : Type*} [Fintype ι] (dir : ι → V3) : Function.Injective (E9 dir) ↔ (E9mat dir).rank = 9
theorem E4_injective_iff_rank {ι : Type*} [Fintype ι] (dir : ι → V3) : Function.Injective (E4 dir) ↔ (E4mat dir).rank = 4
theorem E9_basis_change_det (dir9 : Fin 9 → V3) (P : Matrix (Fin 9) (Fin 9) ℝ) (hP : P.det ≠ 0) : (E9mat dir9 * P).det ≠ 0 ↔ (E9mat dir9).det ≠ 0
theorem E9_basis_change_rank {ι : Type*} [Fintype ι] (dir : ι → V3) (P : Matrix (Fin 9) (Fin 9) ℝ) (hP : P.det ≠ 0) : (E9mat dir * P).rank = (E9mat dir).rank
theorem Xmap_apply {ι : Type*} (dir : ι → V3) (r : ι → ℝ) (c : ℝ) (a : IPar) (h : HPar) (i : ι) : Xmap dir r c (a, h) i = ipoly a (dir i) + (r i / c) * Hval h (dir i)
theorem two_radius_ker_iff (dir9 : Fin 9 → V3) (σ : Fin 4 → Fin 9) (R1 R2 c : ℝ) (hR1 : 0 < R1) (hc : 0 < c) (huni : Function.Injective (E9 dir9)) (a : IPar) (h : HPar) : Xmap (twoRadiusDir dir9 σ) (twoRadiusR R1 R2) c (a, h) = 0 ↔ h = (-(c / R1)) • liftLin a ∧ (1 - R2 / R1) • E4 (dir9 ∘ σ) a = 0
theorem two_radius_ker_eq_bot_of_det (dir9 : Fin 9 → V3) (σ : Fin 4 → Fin 9) (R1 R2 c : ℝ) (hR1 : 0 < R1) (hR2 : 0 < R2) (hc : 0 < c) (hne : R1 ≠ R2) (hdet9 : (E9mat dir9).det ≠ 0) (hdet4 : (E4mat (dir9 ∘ σ)).det ≠ 0) : LinearMap.ker (Xmap (twoRadiusDir dir9 σ) (twoRadiusR R1 R2) c) = ⊥
theorem two_radius_Xmat_mulVec_eq_zero (dir9 : Fin 9 → V3) (σ : Fin 4 → Fin 9) (R1 R2 c : ℝ) (hR1 : 0 < R1) (hR2 : 0 < R2) (hc : 0 < c) (hne : R1 ≠ R2) (hdet9 : (E9mat dir9).det ≠ 0) (hdet4 : (E4mat (dir9 ∘ σ)).det ≠ 0) (v : Fin 4 ⊕ Fin 9 → ℝ) (hv : Xmat (twoRadiusDir dir9 σ) (twoRadiusR R1 R2) c *ᵥ v = 0) : v = 0
theorem two_radius_Xmat_rank13_of_det (dir9 : Fin 9 → V3) (σ : Fin 4 → Fin 9) (R1 R2 c : ℝ) (hR1 : 0 < R1) (hR2 : 0 < R2) (hc : 0 < c) (hne : R1 ≠ R2) (hdet9 : (E9mat dir9).det ≠ 0) (hdet4 : (E4mat (dir9 ∘ σ)).det ≠ 0) : (Xmat (twoRadiusDir dir9 σ) (twoRadiusR R1 R2) c).rank = 13
theorem two_radius_Xmat_rank13_of_ranks (dir9 : Fin 9 → V3) (σ : Fin 4 → Fin 9) (R1 R2 c : ℝ) (hR1 : 0 < R1) (hR2 : 0 < R2) (hc : 0 < c) (hne : R1 ≠ R2) (hrank9 : (E9mat dir9).rank = 9) (hrank4 : (E4mat (dir9 ∘ σ)).rank = 4) : (Xmat (twoRadiusDir dir9 σ) (twoRadiusR R1 R2) c).rank = 13
theorem two_radius_Xmat_rank_lt13_of_det4_eq_zero (dir9 : Fin 9 → V3) (σ : Fin 4 → Fin 9) (R1 R2 c : ℝ) (hR1 : 0 < R1) (hc : 0 < c) (hdet4 : (E4mat (dir9 ∘ σ)).det = 0) : (Xmat (twoRadiusDir dir9 σ) (twoRadiusR R1 R2) c).rank < 13
theorem two_radius_Xmat_equal_radius_le9 (dir9 : Fin 9 → V3) (σ : Fin 4 → Fin 9) (R c : ℝ) (hR : 0 < R) (hc : 0 < c) : (Xmat (twoRadiusDir dir9 σ) (twoRadiusR R R) c).rank ≤ 9
theorem witness_det4 : (E4mat (dirStar ∘ σStar)).det = -2
theorem witness_det9_ne_zero : (E9mat dirStar).det ≠ 0
theorem witness_Xmat_rank13 : (Xmat (twoRadiusDir dirStar σStar) (twoRadiusR 1 2) 1).rank = 13
theorem witness_equal_radius_le9 : (Xmat (twoRadiusDir dirStar σStar) (twoRadiusR 1 1) 1).rank ≤ 9
theorem witness_const_radius_dims : (E4mat dirStar).rank = 4 ∧ (E9mat dirStar).rank = 9 ∧ Module.finrank ℝ ↥(LinearMap.range (E4mat dirStar).mulVecLin ⊓ LinearMap.range (Dmat (fun _ => (1 : ℝ)) 1 * E9mat dirStar).mulVecLin) = 4 ∧ (Xmat dirStar (fun _ => (1 : ℝ)) 1).rank = 9
```

## Addendum after compile (no statement change)

The pre-compile snapshot is `raw/FROZEN_TARGETS_v1.snapshot.md` (sha256 and UTC write time in
`raw/FROZEN_TARGETS_v1.written_utc.json`; 0 compile attempts existed when it was written).
Between the freeze and the passing compile `raw/compile_06_main` the changes were: (1) `open scoped Matrix`
added (needed for the `*ᵥ` notation; no signature text changed); (2) one NEW helper theorem
`witness_E4block : E4mat (dirStar ∘ σStar) = !![1, 1, 0, 0; 1, -1, 0, 0; 1, 0, 1, 0; 1, 0, 0, 1]` used by the
proof of `witness_det4`; (3) proof-only edits in `witness_det4` and `two_radius_Xmat_mulVec_eq_zero`.
Re-extracting all declaration headers and diffing against the frozen block shows exactly one added line
(`witness_E4block`) and no other change.
