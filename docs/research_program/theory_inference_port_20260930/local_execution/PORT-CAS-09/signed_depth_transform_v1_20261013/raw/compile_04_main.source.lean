import Mathlib

/-!
# P09-A: signed joint depth transform (PORT-CAS-09)

Source definitions (see `SOURCE_RECOVERY.md`):
* `htt/src/common/depth_path.py:41-62` — contrast matrix `H`, initial-plus-contrast `T`, `restore`.
* `docs/research_program/tensor_joint_r9/revision2/THEORY_EXTENSION.md:7-58` — D1/D3.

Depth `d : ℕ` means `d+1` ordered blocks `x_0, …, x_d`, block `i` of size `n i`.
Transports `K j : ℝ^{n j} → ℝ^{n (j+1)}` are arbitrary FIXED real matrices (a parameter;
nothing depends on the sample point).  Contrast `r_j = x_{j+1} - K_j x_j`.
`T x = (x_0, r_0, …, r_{d-1})` uses the same block layout as `x`.

No independence hypothesis appears anywhere; covariance matrices are the FULL matrices of all
ordered pairwise covariances.  Block indices are ordering labels only.
-/

noncomputable section

namespace P09SignedDepth

open Matrix MeasureTheory ProbabilityTheory

section Defs

variable {d : ℕ}

/-- Full ordered joint index: block `i`, coordinate `a`. -/
abbrev Idx (n : Fin (d+1) → ℕ) := Σ i : Fin (d+1), Fin (n i)

/-- Contrast index: step `j < d`, coordinate in block `j+1`. -/
abbrev CIdx (n : Fin (d+1) → ℕ) := Σ j : Fin d, Fin (n j.succ)

/-- Fixed transports `K j : Matrix (n (j+1)) (n j)`, one per adjacent pair of blocks. -/
abbrev Transport (n : Fin (d+1) → ℕ) :=
  (j : Fin d) → Matrix (Fin (n j.succ)) (Fin (n j.castSucc)) ℝ

variable {n : Fin (d+1) → ℕ}

/-- Signed contrast `r_j = x_{j+1} - K_j x_j`. -/
def contrast (K : Transport n) (x : Idx n → ℝ) : CIdx n → ℝ :=
  fun p => x ⟨p.1.succ, p.2⟩ - (K p.1 *ᵥ fun b => x ⟨p.1.castSucc, b⟩) p.2

/-- The contrast map as a linear map. -/
def contrastLin (K : Transport n) : (Idx n → ℝ) →ₗ[ℝ] (CIdx n → ℝ) where
  toFun := contrast K
  map_add' x y := by
    funext p
    simp only [contrast, Pi.add_apply, mulVec, dotProduct, mul_add, Finset.sum_add_distrib]
    ring
  map_smul' c x := by
    funext p
    simp only [contrast, Pi.smul_apply, smul_eq_mul, RingHom.id_apply, mulVec, dotProduct,
      mul_sub, Finset.mul_sum]
    congr 1
    exact Finset.sum_congr rfl fun b _ => by ring

/-- The contrast matrix `H` (rows: contrasts; columns: full joint index). -/
def H (K : Transport n) : Matrix (CIdx n) (Idx n) ℝ := LinearMap.toMatrix' (contrastLin K)

/-- Initial-plus-contrast map: block `0` keeps `x_0`; block `j+1` carries `r_j`. -/
def anchored (K : Transport n) (x : Idx n → ℝ) : Idx n → ℝ :=
  fun p => Fin.cases (motive := fun i => Fin (n i) → ℝ) (fun a => x ⟨0, a⟩)
    (fun j a => contrast K x ⟨j, a⟩) p.1 p.2

theorem anchored_zero (K : Transport n) (x : Idx n → ℝ) (a : Fin (n 0)) :
    anchored K x ⟨0, a⟩ = x ⟨0, a⟩ := by
  simp only [anchored, Fin.cases_zero]

theorem anchored_succ (K : Transport n) (x : Idx n → ℝ) (j : Fin d) (a : Fin (n j.succ)) :
    anchored K x ⟨j.succ, a⟩ = contrast K x ⟨j, a⟩ := by
  simp only [anchored, Fin.cases_succ]

theorem anchored_add (K : Transport n) (x y : Idx n → ℝ) :
    anchored K (x + y) = anchored K x + anchored K y := by
  funext ⟨i, a⟩
  induction i using Fin.cases with
  | zero => simp only [anchored_zero, Pi.add_apply]
  | succ j =>
    simp only [anchored_succ, Pi.add_apply]
    exact congrFun (map_add (contrastLin K) x y) ⟨j, a⟩

theorem anchored_smul (K : Transport n) (c : ℝ) (x : Idx n → ℝ) :
    anchored K (c • x) = c • anchored K x := by
  funext ⟨i, a⟩
  induction i using Fin.cases with
  | zero => simp only [anchored_zero, Pi.smul_apply]
  | succ j =>
    simp only [anchored_succ, Pi.smul_apply]
    exact congrFun (map_smul (contrastLin K) c x) ⟨j, a⟩

/-- `anchored` as a linear map. -/
def anchoredLin (K : Transport n) : (Idx n → ℝ) →ₗ[ℝ] (Idx n → ℝ) where
  toFun := anchored K
  map_add' := anchored_add K
  map_smul' := anchored_smul K

/-- The square matrix `T` of the initial-plus-contrast map. -/
def Tmat (K : Transport n) : Matrix (Idx n) (Idx n) ℝ := LinearMap.toMatrix' (anchoredLin K)

/-- Recursive inverse, block by block: `y_0 = r_0-block`, `y_{j+1} = r_{j+1}-block + K_j y_j`
(`depth_path.py:57-62`). -/
def restoreBlock (K : Transport n) (r : Idx n → ℝ) (i : Fin (d+1)) : Fin (n i) → ℝ :=
  Fin.induction (motive := fun i => Fin (n i) → ℝ) (fun a => r ⟨0, a⟩)
    (fun j yj a => r ⟨j.succ, a⟩ + (K j *ᵥ yj) a) i

def restore (K : Transport n) (r : Idx n → ℝ) : Idx n → ℝ := fun p => restoreBlock K r p.1 p.2

theorem restoreBlock_zero (K : Transport n) (r : Idx n → ℝ) :
    restoreBlock K r 0 = fun a => r ⟨0, a⟩ := by
  simp only [restoreBlock, Fin.induction_zero]

theorem restoreBlock_succ (K : Transport n) (r : Idx n → ℝ) (j : Fin d) :
    restoreBlock K r j.succ = fun a => r ⟨j.succ, a⟩ + (K j *ᵥ restoreBlock K r j.castSucc) a := by
  simp only [restoreBlock, Fin.induction_succ]

/-- Block-diagonal part of a joint matrix (cross blocks dropped). Negative control only. -/
def blockDiagPart (C : Matrix (Idx n) (Idx n) ℝ) : Matrix (Idx n) (Idx n) ℝ :=
  fun p q => if p.1 = q.1 then C p q else 0

/-! ## Q1 — structure of `H` and `T` -/

theorem H_mulVec (K : Transport n) (x : Idx n → ℝ) : H K *ᵥ x = contrast K x := by
  rw [H, LinearMap.toMatrix'_mulVec]
  rfl

theorem H_apply' (K : Transport n) (p : CIdx n) (q : Idx n) :
    H K p q = contrast K (Pi.single q 1) p := by
  rw [H, LinearMap.toMatrix'_apply]
  rfl

theorem H_apply_succ (K : Transport n) (j : Fin d) (a b : Fin (n j.succ)) :
    H K ⟨j, a⟩ ⟨j.succ, b⟩ = if a = b then 1 else 0 := by
  have hne : j.castSucc ≠ j.succ := (Fin.castSucc_lt_succ (i := j)).ne
  rw [H_apply']
  simp [contrast, mulVec, dotProduct, Pi.single_apply, hne]

theorem H_apply_castSucc (K : Transport n) (j : Fin d) (a : Fin (n j.succ))
    (b : Fin (n j.castSucc)) :
    H K ⟨j, a⟩ ⟨j.castSucc, b⟩ = -K j a b := by
  have hne : j.succ ≠ j.castSucc := (Fin.castSucc_lt_succ (i := j)).ne'
  rw [H_apply']
  simp [contrast, mulVec, dotProduct, Pi.single_apply, hne]

theorem H_apply_other (K : Transport n) (j : Fin d) (i : Fin (d+1)) (a : Fin (n j.succ))
    (b : Fin (n i)) (h1 : i ≠ j.succ) (h2 : i ≠ j.castSucc) : H K ⟨j, a⟩ ⟨i, b⟩ = 0 := by
  rw [H_apply']
  simp [contrast, mulVec, dotProduct, Ne.symm h1, Ne.symm h2]

theorem Tmat_mulVec (K : Transport n) (x : Idx n → ℝ) : Tmat K *ᵥ x = anchored K x := by
  rw [Tmat, LinearMap.toMatrix'_mulVec]
  rfl

theorem Tmat_apply' (K : Transport n) (p q : Idx n) :
    Tmat K p q = anchored K (Pi.single q 1) p := by
  rw [Tmat, LinearMap.toMatrix'_apply]
  rfl

theorem Tmat_apply_zero (K : Transport n) (a : Fin (n 0)) (q : Idx n) :
    Tmat K ⟨0, a⟩ q = if q = ⟨0, a⟩ then 1 else 0 := by
  rw [Tmat_apply', anchored_zero, Pi.single_apply]
  exact if_congr eq_comm rfl rfl

theorem Tmat_apply_succ (K : Transport n) (j : Fin d) (a : Fin (n j.succ)) (q : Idx n) :
    Tmat K ⟨j.succ, a⟩ q = H K ⟨j, a⟩ q := by
  rw [Tmat_apply', anchored_succ, H_apply']

theorem Tmat_apply_diag (K : Transport n) (i : Fin (d+1)) (a b : Fin (n i)) :
    Tmat K ⟨i, a⟩ ⟨i, b⟩ = if a = b then 1 else 0 := by
  induction i using Fin.cases with
  | zero =>
    rw [Tmat_apply_zero]
    simp [eq_comm]
  | succ j =>
    rw [Tmat_apply_succ, H_apply_succ]

theorem Tmat_apply_upper (K : Transport n) (i i' : Fin (d+1)) (a : Fin (n i)) (b : Fin (n i'))
    (h : i < i') : Tmat K ⟨i, a⟩ ⟨i', b⟩ = 0 := by
  induction i using Fin.cases with
  | zero =>
    rw [Tmat_apply_zero]
    simp [h.ne']
  | succ j =>
    rw [Tmat_apply_succ]
    exact H_apply_other K j i' a b h.ne' (lt_trans Fin.castSucc_lt_succ h).ne'

/-- `T` is block LOWER triangular (Mathlib's `BlockTriangular` with the order-dual block label). -/
theorem Tmat_blockTriangular (K : Transport n) :
    (Tmat K).BlockTriangular (fun p : Idx n => OrderDual.toDual p.1) := by
  intro p q hlt
  obtain ⟨i, a⟩ := p
  obtain ⟨i', b⟩ := q
  exact Tmat_apply_upper K i i' a b (OrderDual.toDual_lt_toDual.mp hlt)

theorem anchored_depth_zero (n : Fin 1 → ℕ) (K : Transport n) : anchored K = id := by
  funext x
  funext ⟨i, a⟩
  induction i using Fin.cases with
  | zero => exact anchored_zero K x a
  | succ j => exact j.elim0

theorem Tmat_depth_zero (n : Fin 1 → ℕ) (K : Transport n) : Tmat K = 1 := by
  ext p q
  rw [Tmat_apply', anchored_depth_zero, id, Pi.single_apply, Matrix.one_apply]

/-! ## Q2 — explicit recursive inverse; bijection at every finite depth -/

theorem anchored_restore (K : Transport n) (r : Idx n → ℝ) : anchored K (restore K r) = r := by
  funext ⟨i, a⟩
  induction i using Fin.cases with
  | zero =>
    rw [anchored_zero]
    simp only [restore, restoreBlock_zero]
  | succ j =>
    rw [anchored_succ]
    simp only [contrast, restore, restoreBlock_succ]
    ring

theorem restoreBlock_anchored (K : Transport n) (x : Idx n → ℝ) (i : Fin (d+1)) :
    restoreBlock K (anchored K x) i = fun a => x ⟨i, a⟩ := by
  induction i using Fin.induction with
  | zero =>
    funext a
    simp only [restoreBlock_zero, anchored_zero]
  | succ j ih =>
    funext a
    simp only [restoreBlock_succ, ih, anchored_succ, contrast]
    ring

theorem restore_anchored (K : Transport n) (x : Idx n → ℝ) : restore K (anchored K x) = x := by
  funext ⟨i, a⟩
  exact congrFun (restoreBlock_anchored K x i) a

theorem restore_succ (K : Transport n) (r : Idx n → ℝ) (j : Fin d) (a : Fin (n j.succ)) :
    restore K r ⟨j.succ, a⟩ = r ⟨j.succ, a⟩ + (K j *ᵥ fun b => restore K r ⟨j.castSucc, b⟩) a := by
  simp only [restore, restoreBlock_succ]

theorem anchored_bijective (K : Transport n) : Function.Bijective (anchored K) :=
  Function.bijective_iff_has_inverse.mpr ⟨restore K, restore_anchored K, anchored_restore K⟩

/-- `T` as a linear equivalence whose inverse is the recursive `restore`. -/
def Tequiv (K : Transport n) : (Idx n → ℝ) ≃ₗ[ℝ] (Idx n → ℝ) :=
  { anchoredLin K with
    invFun := restore K
    left_inv := fun x => restore_anchored K x
    right_inv := fun r => anchored_restore K r }

/-- Matrix of the recursive inverse. -/
def Rmat (K : Transport n) : Matrix (Idx n) (Idx n) ℝ :=
  LinearMap.toMatrix' (Tequiv K).symm.toLinearMap

theorem Tmat_mul_Rmat (K : Transport n) : Tmat K * Rmat K = 1 := by
  have h : anchoredLin K ∘ₗ (Tequiv K).symm.toLinearMap = LinearMap.id :=
    LinearMap.ext fun r => anchored_restore K r
  rw [Tmat, Rmat, ← LinearMap.toMatrix'_comp, h, LinearMap.toMatrix'_id]

theorem Rmat_mul_Tmat (K : Transport n) : Rmat K * Tmat K = 1 := by
  have h : (Tequiv K).symm.toLinearMap ∘ₗ anchoredLin K = LinearMap.id :=
    LinearMap.ext fun x => restore_anchored K x
  rw [Tmat, Rmat, ← LinearMap.toMatrix'_comp, h, LinearMap.toMatrix'_id]

theorem bijective_depth_zero (n : Fin 1 → ℕ) (K : Transport n) :
    Function.Bijective (anchored K) :=
  anchored_bijective K

/-- Stretch: `det T = 1` (identity diagonal blocks, block lower triangular). -/
theorem Tmat_det (K : Transport n) : (Tmat K).det = 1 := by
  rw [(Tmat_blockTriangular K).det]
  refine Finset.prod_eq_one fun A _ => ?_
  have h1 : (Tmat K).toSquareBlock (fun p : Idx n => OrderDual.toDual p.1) A = 1 := by
    ext ⟨⟨i, a⟩, hp⟩ ⟨⟨i', b⟩, hq⟩
    have hii : i = i' := OrderDual.toDual.injective (hp.trans hq.symm)
    subst hii
    simp [toSquareBlock_def, Tmat_apply_diag, Matrix.one_apply]
  rw [h1, det_one]

end Defs

/-! ## Q3 — mean and FULL covariance of a linear image of an L² random vector -/

section Moments

variable {Ω : Type*} [MeasurableSpace Ω] {μ : Measure Ω} {ι κ : Type*} [Fintype ι] [Fintype κ]

/-- Mean vector. -/
def meanVec (μ : Measure Ω) (x : Ω → ι → ℝ) : ι → ℝ := fun i => ∫ ω, x ω i ∂μ

/-- Full covariance matrix: every ordered pair `(i, j)`, all cross blocks. -/
def covMat (μ : Measure Ω) (x : Ω → ι → ℝ) : Matrix ι ι ℝ :=
  fun i j => cov[fun ω => x ω i, fun ω => x ω j; μ]

omit [Fintype κ] in
theorem mean_mulVec (H : Matrix κ ι ℝ) (x : Ω → ι → ℝ)
    (hx : ∀ i, Integrable (fun ω => x ω i) μ) :
    meanVec μ (fun ω => H *ᵥ x ω) = H *ᵥ meanVec μ x := by
  funext k
  simp only [meanVec, mulVec, dotProduct]
  rw [integral_finsetSum _ (fun i _ => (hx i).const_mul (H k i))]
  simp only [integral_const_mul]

omit [Fintype κ] in
theorem covMat_mulVec [IsFiniteMeasure μ] (H : Matrix κ ι ℝ) (x : Ω → ι → ℝ)
    (hx : ∀ i, MemLp (fun ω => x ω i) 2 μ) :
    covMat μ (fun ω => H *ᵥ x ω) = H * covMat μ x * Hᵀ := by
  ext k l
  have hsum := covariance_fun_sum_fun_sum (μ := μ)
    (X := fun i ω => H k i * x ω i) (Y := fun j ω => H l j * x ω j)
    (fun i => (hx i).const_mul (H k i)) (fun j => (hx j).const_mul (H l j))
  simp only [covMat, mulVec, dotProduct] at hsum ⊢
  rw [hsum]
  simp only [covariance_const_mul_left, covariance_const_mul_right, mul_apply, transpose_apply,
    Finset.sum_mul]
  rw [Finset.sum_comm]
  refine Finset.sum_congr rfl fun i _ => Finset.sum_congr rfl fun j _ => ?_
  simp only [covMat]
  ring

end Moments

section DepthMoments

variable {Ω : Type*} [MeasurableSpace Ω] {μ : Measure Ω}
variable {d : ℕ} {n : Fin (d+1) → ℕ}

theorem contrast_moments [IsProbabilityMeasure μ] (K : Transport n) (x : Ω → Idx n → ℝ)
    (hx : ∀ p, MemLp (fun ω => x ω p) 2 μ) :
    meanVec μ (fun ω => contrast K (x ω)) = H K *ᵥ meanVec μ x ∧
    covMat μ (fun ω => contrast K (x ω)) = H K * covMat μ x * (H K)ᵀ := by
  have e : (fun ω => contrast K (x ω)) = fun ω => H K *ᵥ x ω :=
    funext fun ω => (H_mulVec K (x ω)).symm
  rw [e]
  exact ⟨mean_mulVec _ _ fun p => (hx p).integrable one_le_two, covMat_mulVec _ _ hx⟩

theorem anchored_moments [IsProbabilityMeasure μ] (K : Transport n) (x : Ω → Idx n → ℝ)
    (hx : ∀ p, MemLp (fun ω => x ω p) 2 μ) :
    meanVec μ (fun ω => anchored K (x ω)) = Tmat K *ᵥ meanVec μ x ∧
    covMat μ (fun ω => anchored K (x ω)) = Tmat K * covMat μ x * (Tmat K)ᵀ := by
  have e : (fun ω => anchored K (x ω)) = fun ω => Tmat K *ᵥ x ω :=
    funext fun ω => (Tmat_mulVec K (x ω)).symm
  rw [e]
  exact ⟨mean_mulVec _ _ fun p => (hx p).integrable one_le_two, covMat_mulVec _ _ hx⟩

/-- D1 cross-block formula `V_jk = C_{j+1,k+1} - C_{j+1,k}K_kᵀ - K_j C_{j,k+1} + K_j C_jk K_kᵀ`
for an arbitrary joint matrix `C` (all cross blocks enter). -/
theorem HCHt_apply (K : Transport n) (C : Matrix (Idx n) (Idx n) ℝ) (j k : Fin d)
    (a : Fin (n j.succ)) (b : Fin (n k.succ)) :
    (H K * C * (H K)ᵀ) ⟨j, a⟩ ⟨k, b⟩ =
      C ⟨j.succ, a⟩ ⟨k.succ, b⟩
      - ∑ e, C ⟨j.succ, a⟩ ⟨k.castSucc, e⟩ * K k b e
      - ∑ c, K j a c * C ⟨j.castSucc, c⟩ ⟨k.succ, b⟩
      + ∑ c, ∑ e, K j a c * C ⟨j.castSucc, c⟩ ⟨k.castSucc, e⟩ * K k b e := by
  have hCH : ∀ s : Idx n, (C * (H K)ᵀ) s ⟨k, b⟩ =
      C s ⟨k.succ, b⟩ - ∑ e, K k b e * C s ⟨k.castSucc, e⟩ := by
    intro s
    have h1 : (C * (H K)ᵀ) s ⟨k, b⟩ = (H K *ᵥ fun t => C s t) ⟨k, b⟩ := by
      simp only [mul_apply, transpose_apply, mulVec, dotProduct]
      exact Finset.sum_congr rfl fun t _ => mul_comm _ _
    rw [h1, H_mulVec]
    simp only [contrast, mulVec, dotProduct]
  have h2 : (H K * C * (H K)ᵀ) ⟨j, a⟩ ⟨k, b⟩ =
      (H K *ᵥ fun s => (C * (H K)ᵀ) s ⟨k, b⟩) ⟨j, a⟩ := by
    rw [Matrix.mul_assoc]
    rfl
  rw [h2, H_mulVec]
  simp only [contrast, mulVec, dotProduct, hCH]
  have e1 : ∑ e, K k b e * C ⟨j.succ, a⟩ ⟨k.castSucc, e⟩ =
      ∑ e, C ⟨j.succ, a⟩ ⟨k.castSucc, e⟩ * K k b e :=
    Finset.sum_congr rfl fun e _ => mul_comm _ _
  have e2 : ∑ c, K j a c * (C ⟨j.castSucc, c⟩ ⟨k.succ, b⟩ -
        ∑ e, K k b e * C ⟨j.castSucc, c⟩ ⟨k.castSucc, e⟩) =
      ∑ c, K j a c * C ⟨j.castSucc, c⟩ ⟨k.succ, b⟩ -
        ∑ c, ∑ e, K j a c * C ⟨j.castSucc, c⟩ ⟨k.castSucc, e⟩ * K k b e := by
    rw [← Finset.sum_sub_distrib]
    refine Finset.sum_congr rfl fun c _ => ?_
    rw [mul_sub, Finset.mul_sum]
    congr 1
    exact Finset.sum_congr rfl fun e _ => by ring
  rw [e1, e2]
  ring

end DepthMoments

/-! ## Q4 — law of `H x` is the pushforward of the FULL joint law -/

section Law

variable {Ω : Type*} [MeasurableSpace Ω] {μ : Measure Ω} {ι κ : Type*} [Fintype ι] [Fintype κ]

theorem law_mulVec (H : Matrix κ ι ℝ) (x : Ω → ι → ℝ) (hx : AEMeasurable x μ) :
    μ.map (fun ω => H *ᵥ x ω) = (μ.map x).map (fun v => H *ᵥ v) := by
  have hc : Continuous fun v : ι → ℝ => H *ᵥ v :=
    Continuous.matrix_mulVec continuous_const continuous_id
  rw [AEMeasurable.map_map_of_aemeasurable hc.measurable.aemeasurable hx]
  rfl

variable {d : ℕ} {n : Fin (d+1) → ℕ}

theorem contrast_law (K : Transport n) (x : Ω → Idx n → ℝ) (hx : AEMeasurable x μ) :
    μ.map (fun ω => contrast K (x ω)) = (μ.map x).map (fun v => H K *ᵥ v) := by
  have e : (fun ω => contrast K (x ω)) = fun ω => H K *ᵥ x ω :=
    funext fun ω => (H_mulVec K (x ω)).symm
  rw [e, law_mulVec _ _ hx]

theorem contrast_law_congr {Ω' : Type*} [MeasurableSpace Ω'] {ν : Measure Ω'}
    (K : Transport n) (x : Ω → Idx n → ℝ) (y : Ω' → Idx n → ℝ)
    (hx : AEMeasurable x μ) (hy : AEMeasurable y ν) (hlaw : μ.map x = ν.map y) :
    μ.map (fun ω => contrast K (x ω)) = ν.map (fun ω => contrast K (y ω)) := by
  rw [contrast_law K x hx, contrast_law K y hy, hlaw]

theorem contrast_law_marginal_of_anchored (K : Transport n) (x : Ω → Idx n → ℝ)
    (hx : AEMeasurable x μ) :
    μ.map (fun ω => contrast K (x ω)) =
      (μ.map (fun ω => anchored K (x ω))).map (fun y => fun p : CIdx n => y ⟨p.1.succ, p.2⟩) := by
  have hc : Continuous fun v : Idx n → ℝ => anchored K v := by
    have e : (fun v : Idx n → ℝ => anchored K v) = fun v => Tmat K *ᵥ v :=
      funext fun v => (Tmat_mulVec K v).symm
    rw [e]
    exact Continuous.matrix_mulVec continuous_const continuous_id
  have hA : AEMeasurable (fun ω => anchored K (x ω)) μ := hc.measurable.comp_aemeasurable hx
  have hπ : Measurable fun y : Idx n → ℝ => fun p : CIdx n => y ⟨p.1.succ, p.2⟩ :=
    measurable_pi_lambda _ fun p => measurable_pi_apply _
  rw [AEMeasurable.map_map_of_aemeasurable hπ.aemeasurable hA]
  -- the composite agrees with `contrast K ∘ x` definitionally (`anchored_succ` is `Fin.cases_succ`)
  congr 1

end Law

/-! ## Q5 — negative control: dropping cross blocks changes the contrast covariance -/

section NegativeControl

/-- Depth 2, three unit blocks. -/
abbrev n₁ : Fin 3 → ℕ := fun _ => 1

/-- Unit transports `K_j = (1)`. -/
def K₁ : Transport n₁ := fun _ _ _ => 1

/-- Three copies of one unit-variance variable: all-ones joint covariance (cross blocks = 1). -/
def ones : Matrix (Idx n₁) (Idx n₁) ℝ := fun _ _ => 1

theorem ones_contrast_cov_zero : H K₁ * ones * (H K₁)ᵀ = 0 := by
  ext ⟨j, a⟩ ⟨k, b⟩
  rw [HCHt_apply]
  simp [ones, K₁]

theorem blockDiag_contrast_cov_00 :
    (H K₁ * blockDiagPart ones * (H K₁)ᵀ) ⟨0, 0⟩ ⟨0, 0⟩ = 2 := by
  rw [HCHt_apply]
  simp [blockDiagPart, ones, K₁]
  norm_num

theorem blockDiag_contrast_cov_01 :
    (H K₁ * blockDiagPart ones * (H K₁)ᵀ) ⟨0, 0⟩ ⟨1, 0⟩ = -1 := by
  rw [HCHt_apply]
  simp [blockDiagPart, ones, K₁]

theorem dropping_cross_blocks_changes_cov :
    H K₁ * blockDiagPart ones * (H K₁)ᵀ ≠ H K₁ * ones * (H K₁)ᵀ := by
  intro h
  have h00 := congrFun (congrFun h ⟨0, 0⟩) ⟨0, 0⟩
  rw [blockDiag_contrast_cov_00, ones_contrast_cov_zero] at h00
  norm_num at h00

/-- Q5p: an actual copy random vector `x ω = (Z ω, Z ω, Z ω)` has full covariance
`cov[Z,Z] • ones`, hence identically zero contrast covariance. -/
theorem copy_covMat {Ω : Type*} [MeasurableSpace Ω] (μ : Measure Ω) (Z : Ω → ℝ) :
    covMat μ (fun ω (_ : Idx n₁) => Z ω) = cov[Z, Z; μ] • ones := by
  ext p q
  simp [covMat, ones]

theorem copy_contrast_cov_zero {Ω : Type*} [MeasurableSpace Ω] (μ : Measure Ω) (Z : Ω → ℝ) :
    H K₁ * covMat μ (fun ω (_ : Idx n₁) => Z ω) * (H K₁)ᵀ = 0 := by
  rw [copy_covMat, Matrix.mul_smul, Matrix.smul_mul, ones_contrast_cov_zero, smul_zero]

theorem copy_covMat_var {Ω : Type*} [MeasurableSpace Ω] (μ : Measure Ω) (Z : Ω → ℝ)
    (hZ : AEMeasurable Z μ) :
    covMat μ (fun ω (_ : Idx n₁) => Z ω) = Var[Z; μ] • ones := by
  rw [copy_covMat, covariance_self hZ]

/-- Dropping the cross blocks of the SAME actual covariance gives `2 cov[Z,Z]` instead of `0`. -/
theorem copy_blockDiag_contrast_cov_00 {Ω : Type*} [MeasurableSpace Ω] (μ : Measure Ω)
    (Z : Ω → ℝ) :
    (H K₁ * blockDiagPart (covMat μ (fun ω (_ : Idx n₁) => Z ω)) * (H K₁)ᵀ) ⟨0, 0⟩ ⟨0, 0⟩ =
      2 * cov[Z, Z; μ] := by
  have hb : blockDiagPart (covMat μ (fun ω (_ : Idx n₁) => Z ω)) =
      cov[Z, Z; μ] • blockDiagPart ones := by
    rw [copy_covMat]
    ext p q
    by_cases h : p.1 = q.1 <;> simp [blockDiagPart, h]
  rw [hb, Matrix.mul_smul, Matrix.smul_mul, Matrix.smul_apply, blockDiag_contrast_cov_00,
    smul_eq_mul, mul_comm]

end NegativeControl

end P09SignedDepth
