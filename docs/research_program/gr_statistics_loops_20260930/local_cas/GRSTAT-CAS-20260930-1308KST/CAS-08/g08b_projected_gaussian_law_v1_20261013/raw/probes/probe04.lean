import Mathlib
import G08ACorollaries

/-!
# G08-B: projected Gaussian law, chi-square law and quantile coverage

Frozen targets: `../FROZEN_TARGETS.md` (sha256 recorded in `raw/frozen_targets_v1.sha256`).
Source: NATIVE_INFERENCE_THEOREMS.md §4 (model (4), statistic and set (7), coverage (8),
rank-0 rule line 90); see `../SOURCE_RECOVERY.md`.

Reused unchanged: `G08AWhitening`, `G08ACorollaries`, `ProjectionBridge`.

`chiSq ν` is *defined* as the law of a sum of `ν` squared independent standard normals
(the source's own wording). Its identification with `gammaMeasure (ν/2) (1/2)` or with any
numerical `chi2.ppf` is not claimed here.
-/

namespace G08BGaussianLaw

open MeasureTheory ProbabilityTheory Matrix WithLp Filter Topology
open scoped RealInnerProductSpace

variable {n k : ℕ}

/-! ## Definitions -/

/-- χ²_ν: the law of the sum of squares of ν independent standard normals. -/
noncomputable def chiSq (ν : ℕ) : Measure ℝ :=
  (Measure.pi fun _ : Fin ν => gaussianReal 0 1).map (fun z => ∑ i, z i ^ 2)

/-- Lower p-quantile (generalized inverse of the CDF). -/
noncomputable def lowerQuantile (ρ : Measure ℝ) (p : ℝ) : ℝ := sInf {x | p ≤ cdf ρ x}

/-- Source threshold: q_{ν,α} = (1-α)-quantile of χ²_ν for ν > 0; q = 0 for ν = 0 (line 90). -/
noncomputable def threshold (ν : ℕ) (α : ℝ) : ℝ :=
  if ν = 0 then 0 else lowerQuantile (chiSq ν) (1 - α)

/-- Q_y(θ) = ‖P W (y - m(θ))‖², source (7). -/
noncomputable def Qstat (W : Matrix (Fin n) (Fin n) ℝ) (F : Matrix (Fin n) (Fin k) ℝ)
    (X : Matrix (Fin k) (Fin n) ℝ) (mθ y : EuclideanSpace ℝ (Fin n)) : ℝ :=
  ‖toEuclideanCLM (𝕜 := ℝ) (1 - W * F * X) (toEuclideanCLM (𝕜 := ℝ) W (y - mθ))‖ ^ 2

/-- Source confidence set (7): Cα(y) = {θ ∈ Ω : Q_y(θ) ≤ q}  (non-strict ≤). -/
def confSet {Θ : Type*} (Ωd : Set Θ) (m : Θ → EuclideanSpace ℝ (Fin n))
    (W : Matrix (Fin n) (Fin n) ℝ) (F : Matrix (Fin n) (Fin k) ℝ) (X : Matrix (Fin k) (Fin n) ℝ)
    (q : ℝ) (y : EuclideanSpace ℝ (Fin n)) : Set Θ :=
  {θ | θ ∈ Ωd ∧ Qstat W F X (m θ) y ≤ q}

/-! ## Helper lemmas (not part of the frozen interface) -/

lemma quad_aux (A S : Matrix (Fin n) (Fin n) ℝ) (u v : Fin n → ℝ) :
    (Aᵀ *ᵥ u) ⬝ᵥ S *ᵥ (Aᵀ *ᵥ v) = u ⬝ᵥ (A * S * Aᵀ) *ᵥ v := by
  rw [← mulVec_mulVec, ← mulVec_mulVec, dotProduct_mulVec u A, ← mulVec_transpose A u]

lemma adjoint_toEuclideanCLM (A : Matrix (Fin n) (Fin n) ℝ) :
    (toEuclideanCLM (𝕜 := ℝ) A).adjoint = toEuclideanCLM (𝕜 := ℝ) Aᵀ := by
  rw [← conjTranspose_eq_transpose_of_trivial, ← ContinuousLinearMap.star_eq_adjoint,
    ← map_star, star_eq_conjTranspose]

lemma measurable_Qstat (W : Matrix (Fin n) (Fin n) ℝ) (F : Matrix (Fin n) (Fin k) ℝ)
    (X : Matrix (Fin k) (Fin n) ℝ) (mθ : EuclideanSpace ℝ (Fin n)) :
    Measurable (Qstat W F X mθ) := by
  unfold Qstat
  exact Continuous.measurable (by fun_prop)

lemma measurable_sumSq (ν : ℕ) : Measurable (fun z : Fin ν → ℝ => ∑ i, z i ^ 2) := by
  fun_prop

lemma frame_norm_sq {E : Type*} [NormedAddCommGroup E] [InnerProductSpace ℝ E] {ν : ℕ}
    {u : Fin ν → E} (hu : Orthonormal ℝ u) (c : Fin ν → ℝ) :
    ‖∑ i, c i • u i‖ ^ 2 = ∑ i, c i ^ 2 := by
  rw [← real_inner_self_eq_norm_sq, hu.inner_sum]
  simp [sq]

/-! ## T1: affine pushforward of a multivariate Gaussian law -/

theorem map_affine_multivariateGaussian {μ c : EuclideanSpace ℝ (Fin n)}
    {S : Matrix (Fin n) (Fin n) ℝ} (hS : S.PosSemidef) (A : Matrix (Fin n) (Fin n) ℝ) :
    (multivariateGaussian μ S).map (fun x => toEuclideanCLM (𝕜 := ℝ) A (x - c)) =
      multivariateGaussian (toEuclideanCLM (𝕜 := ℝ) A (μ - c)) (A * S * Aᵀ) := by
  set L := toEuclideanCLM (𝕜 := ℝ) A with hL
  have hf : (fun x => L (x - c)) = (fun z => (-(L c)) + z) ∘ L := by
    funext x
    simp only [Function.comp_apply, map_sub]
    abel
  have hASA : (A * S * Aᵀ).PosSemidef := by
    simpa [conjTranspose_eq_transpose_of_trivial] using hS.mul_mul_conjTranspose_same A
  have hint : Integrable (fun x : EuclideanSpace ℝ (Fin n) => x) (multivariateGaussian μ S) :=
    IsGaussian.integrable_id
  rw [hf, ← Measure.map_map (measurable_const_add _) L.measurable]
  apply IsGaussian.ext
  · rw [integral_id_multivariateGaussian']
    change ∫ x, x ∂((multivariateGaussian μ S).map L).map (fun z => -(L c) + z) = _
    rw [integral_map (by fun_prop) (by fun_prop), integral_map (by fun_prop) (by fun_prop),
      integral_add (integrable_const _) (L.integrable_comp hint), integral_const,
      L.integral_comp_comm hint, integral_id_multivariateGaussian]
    simp only [probReal_univ, one_smul, map_sub]
    abel
  · rw [covarianceBilin_map_const_add]
    ext u v
    rw [covarianceBilin_map IsGaussian.memLp_two_id, covarianceBilin_multivariateGaussian hS,
      covarianceBilin_multivariateGaussian hASA, hL, adjoint_toEuclideanCLM,
      ofLp_toEuclideanCLM, ofLp_toEuclideanCLM]
    exact quad_aux A S _ _

/-! ## T2: law of the projected whitened residual -/

lemma PW_annihilates (W : Matrix (Fin n) (Fin n) ℝ) (F : Matrix (Fin n) (Fin k) ℝ)
    (X : Matrix (Fin k) (Fin n) ℝ) (hX : G08AWhitening.IsMoorePenrose (W * F) X)
    (β : Fin k → ℝ) :
    toEuclideanCLM (𝕜 := ℝ) ((1 - W * F * X) * W) (toLp 2 (F *ᵥ β)) = 0 := by
  have h0 : (1 - W * F * X) * W * F = 0 := by
    rw [Matrix.mul_assoc]; exact G08AWhitening.residual_annihilates (W * F) X hX
  rw [toEuclideanCLM_toLp, mulVec_mulVec, h0, zero_mulVec]
  rfl

lemma PW_covariance (C W : Matrix (Fin n) (Fin n) ℝ) (F : Matrix (Fin n) (Fin k) ℝ)
    (X : Matrix (Fin k) (Fin n) ℝ) (hW : IsUnit W ∧ W * C * Wᵀ = 1)
    (hX : G08AWhitening.IsMoorePenrose (W * F) X) :
    (1 - W * F * X) * W * C * ((1 - W * F * X) * W)ᵀ = 1 - W * F * X := by
  have := G08AWhitening.projected_covariance C W F X hW hX
  rw [transpose_mul]
  simpa only [Matrix.mul_assoc] using this

lemma map_PW (C W : Matrix (Fin n) (Fin n) ℝ) (F : Matrix (Fin n) (Fin k) ℝ)
    (X : Matrix (Fin k) (Fin n) ℝ) (hC : C.PosDef) (hW : IsUnit W ∧ W * C * Wᵀ = 1)
    (hX : G08AWhitening.IsMoorePenrose (W * F) X) (μ c : EuclideanSpace ℝ (Fin n)) :
    (multivariateGaussian μ C).map
        (fun y => toEuclideanCLM (𝕜 := ℝ) (1 - W * F * X) (toEuclideanCLM (𝕜 := ℝ) W (y - c))) =
      multivariateGaussian (toEuclideanCLM (𝕜 := ℝ) ((1 - W * F * X) * W) (μ - c))
        (1 - W * F * X) := by
  have hfun : (fun y => toEuclideanCLM (𝕜 := ℝ) (1 - W * F * X)
      (toEuclideanCLM (𝕜 := ℝ) W (y - c))) =
      fun y => toEuclideanCLM (𝕜 := ℝ) ((1 - W * F * X) * W) (y - c) := by
    funext y; rw [map_mul]; rfl
  rw [hfun, map_affine_multivariateGaussian hC.posSemidef, PW_covariance C W F X hW hX]

theorem projected_residual_law (C W : Matrix (Fin n) (Fin n) ℝ) (F : Matrix (Fin n) (Fin k) ℝ)
    (X : Matrix (Fin k) (Fin n) ℝ) (hC : C.PosDef) (hW : IsUnit W ∧ W * C * Wᵀ = 1)
    (hX : G08AWhitening.IsMoorePenrose (W * F) X) (mθ : EuclideanSpace ℝ (Fin n)) (β : Fin k → ℝ) :
    (multivariateGaussian (mθ + toLp 2 (F *ᵥ β)) C).map
        (fun y => toEuclideanCLM (𝕜 := ℝ) (1 - W * F * X) (toEuclideanCLM (𝕜 := ℝ) W (y - mθ))) =
      multivariateGaussian 0 (1 - W * F * X) := by
  rw [map_PW C W F X hC hW hX, add_sub_cancel_left, PW_annihilates W F X hX β]

theorem projected_residual_law_rv {Ω : Type*} [MeasurableSpace Ω] («ℙ» : Measure Ω)
    (C W : Matrix (Fin n) (Fin n) ℝ) (F : Matrix (Fin n) (Fin k) ℝ) (X : Matrix (Fin k) (Fin n) ℝ)
    (hC : C.PosDef) (hW : IsUnit W ∧ W * C * Wᵀ = 1) (hX : G08AWhitening.IsMoorePenrose (W * F) X)
    (mθ : EuclideanSpace ℝ (Fin n)) (β : Fin k → ℝ) (ε : Ω → EuclideanSpace ℝ (Fin n))
    (hε : Measurable ε) (hlaw : «ℙ».map ε = multivariateGaussian 0 C) :
    «ℙ».map (fun ω => toEuclideanCLM (𝕜 := ℝ) (1 - W * F * X)
        (toEuclideanCLM (𝕜 := ℝ) W ((mθ + toLp 2 (F *ᵥ β) + ε ω) - mθ))) =
      multivariateGaussian 0 (1 - W * F * X) := by
  have hcomp : (fun ω => toEuclideanCLM (𝕜 := ℝ) (1 - W * F * X)
        (toEuclideanCLM (𝕜 := ℝ) W ((mθ + toLp 2 (F *ᵥ β) + ε ω) - mθ))) =
      (fun e => toEuclideanCLM (𝕜 := ℝ) (1 - W * F * X)
        (toEuclideanCLM (𝕜 := ℝ) W (e - (-toLp 2 (F *ᵥ β))))) ∘ ε := by
    funext ω
    simp only [Function.comp_apply]
    congr 2
    abel
  rw [hcomp, ← Measure.map_map (Continuous.measurable (by fun_prop)) hε, hlaw,
    map_PW C W F X hC hW hX, zero_sub, neg_neg, PW_annihilates W F X hX β]

/-! ## T3: orthonormal coordinates of the standard Gaussian are iid N(0,1) -/

theorem stdGaussian_map_orthonormal {E : Type*} [NormedAddCommGroup E] [InnerProductSpace ℝ E]
    [FiniteDimensional ℝ E] [MeasurableSpace E] [BorelSpace E] {ν : ℕ} (u : Fin ν → E)
    (hu : Orthonormal ℝ u) :
    (stdGaussian E).map (fun x i => ⟪u i, x⟫) = Measure.pi (fun _ : Fin ν => gaussianReal 0 1) := by
  set L : E → EuclideanSpace ℝ (Fin ν) := fun x => toLp 2 (fun i => ⟪u i, x⟫) with hLdef
  have hLc : Continuous L := by
    simp only [hLdef]
    exact (PiLp.continuous_toLp 2 _).comp (continuous_pi fun i => by fun_prop)
  have key : (stdGaussian E).map L = stdGaussian (EuclideanSpace ℝ (Fin ν)) := by
    apply Measure.ext_of_charFun
    ext t
    set v : E := ∑ i, t i • u i with hv
    have hin : ∀ x, ⟪L x, t⟫ = ⟪x, v⟫ := by
      intro x
      rw [PiLp.inner_apply, hv, inner_sum]
      refine Finset.sum_congr rfl fun i _ => ?_
      rw [inner_smul_right]
      simp only [hLdef, PiLp.toLp_apply, real_inner_comm x (u i)]
      simp [mul_comm]
    have hnorm : ‖v‖ ^ 2 = ‖t‖ ^ 2 := by
      rw [hv, frame_norm_sq hu, EuclideanSpace.real_norm_sq_eq]
    rw [charFun_apply, integral_map hLc.measurable.aemeasurable
      (Continuous.aestronglyMeasurable (by fun_prop))]
    simp_rw [hin]
    have hnorm' : ((‖v‖ : ℂ)) ^ 2 = ((‖t‖ : ℂ)) ^ 2 := by exact_mod_cast hnorm
    rw [← charFun_apply, charFun_stdGaussian, charFun_stdGaussian, hnorm']
  have hpi : Measure.pi (fun _ : Fin ν => gaussianReal 0 1) =
      (stdGaussian (EuclideanSpace ℝ (Fin ν))).map ofLp := by
    rw [← map_pi_eq_stdGaussian, Measure.map_map (by fun_prop) (by fun_prop)]
    exact Measure.map_id.symm
  rw [hpi, ← key, Measure.map_map (by fun_prop) hLc.measurable]
  rfl

/-- Reindexing a masked sum over `Fin n` to a sum over `Fin ν`, `ν ≤ n`. -/
lemma sum_castLE {ν : ℕ} (hle : ν ≤ n) (g : Fin n → ℝ) :
    ∑ i : Fin ν, g (Fin.castLE hle i) = ∑ a : Fin n, if (a : ℕ) < ν then g a else 0 := by
  rw [Finset.sum_ite, Finset.sum_const_zero, add_zero]
  refine Finset.sum_bij (fun i _ => Fin.castLE hle i) ?_ ?_ ?_ ?_
  · intro i _
    simp
  · intro i _ j _ h
    exact Fin.castLE_injective hle h
  · intro b hb
    simp only [Finset.mem_filter, Finset.mem_univ, true_and] at hb
    exact ⟨⟨b, hb⟩, Finset.mem_univ _, Fin.ext rfl⟩
  · intro i _
    rfl

theorem projector_frame (C W : Matrix (Fin n) (Fin n) ℝ) (F : Matrix (Fin n) (Fin k) ℝ)
    (X : Matrix (Fin k) (Fin n) ℝ) (hW : IsUnit W ∧ W * C * Wᵀ = 1)
    (hX : G08AWhitening.IsMoorePenrose (W * F) X) :
    ∃ u : Fin (n - F.rank) → EuclideanSpace ℝ (Fin n), Orthonormal ℝ u ∧
      ∀ x, toEuclideanCLM (𝕜 := ℝ) (1 - W * F * X) x = ∑ i, ⟪u i, x⟫ • u i := by
  obtain ⟨U, hUU, -, hP⟩ := G08AWhitening.projector_spectrum (W * F) X hX
  rw [G08AWhitening.nu_eq C W F hW] at hP
  have hle : n - F.rank ≤ n := Nat.sub_le _ _
  let r : Fin (n - F.rank) → EuclideanSpace ℝ (Fin n) :=
    fun i => toLp 2 (fun j => U (Fin.castLE hle i) j)
  have hinner : ∀ (a : Fin n) (x : EuclideanSpace ℝ (Fin n)),
      ⟪toLp 2 (fun j => U a j), x⟫ = ∑ l, U a l * x l := by
    intro a x
    rw [PiLp.inner_apply]
    refine Finset.sum_congr rfl fun l _ => ?_
    simp [mul_comm]
  refine ⟨r, ?_, ?_⟩
  · rw [orthonormal_iff_ite]
    intro i j
    have h1 : ⟪r i, r j⟫ = (U * Uᵀ) (Fin.castLE hle i) (Fin.castLE hle j) := by
      simp only [r]
      rw [hinner, Matrix.mul_apply]
      simp
    rw [h1, hUU, Matrix.one_apply]
    by_cases hij : i = j
    · simp [hij]
    · simp [hij, (Fin.castLE_injective hle).ne hij]
  · intro x
    ext m
    have lhs : (toEuclideanCLM (𝕜 := ℝ) (1 - W * F * X) x) m =
        ∑ a : Fin n, if (a : ℕ) < n - F.rank then (∑ l, U a l * x l) * U a m else 0 := by
      have hd : ∀ (d w : Fin n → ℝ), diagonal d *ᵥ w = fun a => d a * w a := by
        intro d w; funext a; exact mulVec_diagonal d w a
      rw [hP, ofLp_toEuclideanCLM, ← mulVec_mulVec, ← mulVec_mulVec, hd]
      simp only [mulVec, dotProduct, transpose_apply]
      refine Finset.sum_congr rfl fun a _ => ?_
      split_ifs <;> ring
    have rhs : (∑ i, ⟪r i, x⟫ • r i) m =
        ∑ i : Fin (n - F.rank), (∑ l, U (Fin.castLE hle i) l * x l) * U (Fin.castLE hle i) m := by
      simp only [r, hinner]
      rw [WithLp.ofLp_sum, Finset.sum_apply]
      simp [smul_eq_mul]
    rw [lhs, rhs, sum_castLE hle (fun a => (∑ l, U a l * x l) * U a m)]

/-- The projector is the image of the standard Gaussian under `P`: `N(0,P) = P_# N(0,I)`. -/
lemma stdGaussian_map_projector (C W : Matrix (Fin n) (Fin n) ℝ) (F : Matrix (Fin n) (Fin k) ℝ)
    (X : Matrix (Fin k) (Fin n) ℝ) (hX : G08AWhitening.IsMoorePenrose (W * F) X) :
    (stdGaussian (EuclideanSpace ℝ (Fin n))).map (toEuclideanCLM (𝕜 := ℝ) (1 - W * F * X)) =
      multivariateGaussian 0 (1 - W * F * X) := by
  have h := map_affine_multivariateGaussian (μ := (0 : EuclideanSpace ℝ (Fin n)))
    (c := 0) Matrix.PosSemidef.one (1 - W * F * X)
  rw [multivariateGaussian_zero_one, Matrix.mul_one, G08AWhitening.residual_transpose _ X hX,
    G08AWhitening.residual_idempotent _ X hX] at h
  simp only [sub_zero, map_zero] at h
  exact h

lemma coords_projector {ν : ℕ} {u : Fin ν → EuclideanSpace ℝ (Fin n)} (hu : Orthonormal ℝ u)
    {P : Matrix (Fin n) (Fin n) ℝ}
    (hP : ∀ x, toEuclideanCLM (𝕜 := ℝ) P x = ∑ i, ⟪u i, x⟫ • u i) (z : EuclideanSpace ℝ (Fin n)) :
    (fun i => ⟪u i, toEuclideanCLM (𝕜 := ℝ) P z⟫) = fun i => ⟪u i, z⟫ := by
  funext i
  rw [hP z]
  exact hu.inner_right_fintype (fun j => ⟪u j, z⟫) i

lemma coords_law_projector (C W : Matrix (Fin n) (Fin n) ℝ) (F : Matrix (Fin n) (Fin k) ℝ)
    (X : Matrix (Fin k) (Fin n) ℝ) (hX : G08AWhitening.IsMoorePenrose (W * F) X)
    (u : Fin (n - F.rank) → EuclideanSpace ℝ (Fin n)) (hu : Orthonormal ℝ u)
    (hP : ∀ x, toEuclideanCLM (𝕜 := ℝ) (1 - W * F * X) x = ∑ i, ⟪u i, x⟫ • u i) :
    (multivariateGaussian 0 (1 - W * F * X)).map (fun z i => ⟪u i, z⟫) =
      Measure.pi (fun _ => gaussianReal 0 1) := by
  rw [← stdGaussian_map_projector C W F X hX, Measure.map_map (by fun_prop) (by fun_prop)]
  have : ((fun z i => ⟪u i, z⟫) ∘ toEuclideanCLM (𝕜 := ℝ) (1 - W * F * X)) =
      fun z i => ⟪u i, z⟫ := funext (coords_projector hu hP)
  rw [this, stdGaussian_map_orthonormal u hu]

theorem projected_coordinates_rv {Ω : Type*} [MeasurableSpace Ω] («ℙ» : Measure Ω)
    [IsProbabilityMeasure «ℙ»]
    (C W : Matrix (Fin n) (Fin n) ℝ) (F : Matrix (Fin n) (Fin k) ℝ) (X : Matrix (Fin k) (Fin n) ℝ)
    (hC : C.PosDef) (hW : IsUnit W ∧ W * C * Wᵀ = 1) (hX : G08AWhitening.IsMoorePenrose (W * F) X)
    (mθ : EuclideanSpace ℝ (Fin n)) (β : Fin k → ℝ) (ε : Ω → EuclideanSpace ℝ (Fin n))
    (hε : Measurable ε) (hlaw : «ℙ».map ε = multivariateGaussian 0 C)
    (u : Fin (n - F.rank) → EuclideanSpace ℝ (Fin n)) (hu : Orthonormal ℝ u)
    (hP : ∀ x, toEuclideanCLM (𝕜 := ℝ) (1 - W * F * X) x = ∑ i, ⟪u i, x⟫ • u i) :
    let R : Ω → EuclideanSpace ℝ (Fin n) := fun ω => toEuclideanCLM (𝕜 := ℝ) (1 - W * F * X)
        (toEuclideanCLM (𝕜 := ℝ) W ((mθ + toLp 2 (F *ᵥ β) + ε ω) - mθ))
    «ℙ».map (fun ω i => ⟪u i, R ω⟫) = Measure.pi (fun _ => gaussianReal 0 1) ∧
      (∀ i, «ℙ».map (fun ω => ⟪u i, R ω⟫) = gaussianReal 0 1) ∧
      iIndepFun (fun i ω => ⟪u i, R ω⟫) «ℙ» ∧
      ∀ ω, ‖R ω‖ ^ 2 = ∑ i, ⟪u i, R ω⟫ ^ 2 := by
  intro R
  have hRc : Continuous (fun e : EuclideanSpace ℝ (Fin n) => toEuclideanCLM (𝕜 := ℝ)
      (1 - W * F * X) (toEuclideanCLM (𝕜 := ℝ) W ((mθ + toLp 2 (F *ᵥ β) + e) - mθ))) := by
    fun_prop
  have hRm : Measurable R := hRc.measurable.comp hε
  have hRlaw : «ℙ».map R = multivariateGaussian 0 (1 - W * F * X) :=
    projected_residual_law_rv «ℙ» C W F X hC hW hX mθ β ε hε hlaw
  have hcm : Measurable (fun (z : EuclideanSpace ℝ (Fin n)) (i : Fin (n - F.rank)) => ⟪u i, z⟫) :=
    by fun_prop
  have hcR : Measurable (fun ω (i : Fin (n - F.rank)) => ⟪u i, R ω⟫) := hcm.comp hRm
  have hmi : ∀ i, Measurable (fun ω => ⟪u i, R ω⟫) := fun i => (measurable_pi_apply i).comp hcR
  have hjoint : «ℙ».map (fun ω i => ⟪u i, R ω⟫) = Measure.pi (fun _ => gaussianReal 0 1) := by
    rw [show (fun ω i => ⟪u i, R ω⟫) = (fun z i => ⟪u i, z⟫) ∘ R from rfl,
      ← Measure.map_map hcm hRm, hRlaw, coords_law_projector C W F X hX u hu hP]
  have hmarg : ∀ i, «ℙ».map (fun ω => ⟪u i, R ω⟫) = gaussianReal 0 1 := by
    intro i
    rw [show (fun ω => ⟪u i, R ω⟫) = Function.eval i ∘ (fun ω i => ⟪u i, R ω⟫) from rfl,
      ← Measure.map_map (measurable_pi_apply i) hcR, hjoint, Measure.pi_map_eval]
    simp
  refine ⟨hjoint, hmarg, ?_, ?_⟩
  · rw [iIndepFun_iff_map_fun_eq_pi_map (fun i => (hmi i).aemeasurable), hjoint]
    congr 1
    funext i
    rw [hmarg i]
  · intro ω
    change ‖toEuclideanCLM (𝕜 := ℝ) (1 - W * F * X) _‖ ^ 2 =
      ∑ i, ⟪u i, toEuclideanCLM (𝕜 := ℝ) (1 - W * F * X) _⟫ ^ 2
    have h1 := fun i => congrFun (coords_projector hu hP
      (toEuclideanCLM (𝕜 := ℝ) W ((mθ + toLp 2 (F *ᵥ β) + ε ω) - mθ))) i
    simp only [h1]
    rw [hP, frame_norm_sq hu]

/-! ## T4: chi-square law of the statistic -/

lemma law_norm_sq (C W : Matrix (Fin n) (Fin n) ℝ) (F : Matrix (Fin n) (Fin k) ℝ)
    (X : Matrix (Fin k) (Fin n) ℝ) (hW : IsUnit W ∧ W * C * Wᵀ = 1)
    (hX : G08AWhitening.IsMoorePenrose (W * F) X) :
    (multivariateGaussian 0 (1 - W * F * X)).map (fun z => ‖z‖ ^ 2) = chiSq (n - F.rank) := by
  obtain ⟨u, hu, hP⟩ := projector_frame C W F X hW hX
  rw [← stdGaussian_map_projector C W F X hX, Measure.map_map (by fun_prop) (by fun_prop)]
  have : ((fun z : EuclideanSpace ℝ (Fin n) => ‖z‖ ^ 2) ∘ toEuclideanCLM (𝕜 := ℝ) (1 - W * F * X))
      = (fun c : Fin (n - F.rank) → ℝ => ∑ i, c i ^ 2) ∘ (fun x i => ⟪u i, x⟫) := by
    funext x
    simp only [Function.comp_apply]
    rw [hP x, frame_norm_sq hu]
  rw [this, ← Measure.map_map (measurable_sumSq _) (by fun_prop), stdGaussian_map_orthonormal u hu]
  rfl

theorem chiSq_law (C W : Matrix (Fin n) (Fin n) ℝ) (F : Matrix (Fin n) (Fin k) ℝ)
    (X : Matrix (Fin k) (Fin n) ℝ) (hC : C.PosDef) (hW : IsUnit W ∧ W * C * Wᵀ = 1)
    (hX : G08AWhitening.IsMoorePenrose (W * F) X) (mθ : EuclideanSpace ℝ (Fin n)) (β : Fin k → ℝ) :
    (multivariateGaussian (mθ + toLp 2 (F *ᵥ β)) C).map (Qstat W F X mθ) = chiSq (n - F.rank) := by
  rw [show Qstat W F X mθ = (fun z : EuclideanSpace ℝ (Fin n) => ‖z‖ ^ 2) ∘
      (fun y => toEuclideanCLM (𝕜 := ℝ) (1 - W * F * X) (toEuclideanCLM (𝕜 := ℝ) W (y - mθ)))
      from rfl, ← Measure.map_map (by fun_prop) (Continuous.measurable (by fun_prop)),
    projected_residual_law C W F X hC hW hX mθ β, law_norm_sq C W F X hW hX]

theorem chiSq_law_rv {Ω : Type*} [MeasurableSpace Ω] («ℙ» : Measure Ω)
    (C W : Matrix (Fin n) (Fin n) ℝ) (F : Matrix (Fin n) (Fin k) ℝ) (X : Matrix (Fin k) (Fin n) ℝ)
    (hC : C.PosDef) (hW : IsUnit W ∧ W * C * Wᵀ = 1) (hX : G08AWhitening.IsMoorePenrose (W * F) X)
    (mθ : EuclideanSpace ℝ (Fin n)) (β : Fin k → ℝ) (ε : Ω → EuclideanSpace ℝ (Fin n))
    (hε : Measurable ε) (hlaw : «ℙ».map ε = multivariateGaussian 0 C) :
    «ℙ».map (fun ω => Qstat W F X mθ (mθ + toLp 2 (F *ᵥ β) + ε ω)) = chiSq (n - F.rank) := by
  have hc : Continuous (fun e : EuclideanSpace ℝ (Fin n) => toEuclideanCLM (𝕜 := ℝ)
      (1 - W * F * X) (toEuclideanCLM (𝕜 := ℝ) W ((mθ + toLp 2 (F *ᵥ β) + e) - mθ))) := by
    fun_prop
  have hm : Measurable (fun ω => toEuclideanCLM (𝕜 := ℝ) (1 - W * F * X)
      (toEuclideanCLM (𝕜 := ℝ) W ((mθ + toLp 2 (F *ᵥ β) + ε ω) - mθ))) := hc.measurable.comp hε
  rw [show (fun ω => Qstat W F X mθ (mθ + toLp 2 (F *ᵥ β) + ε ω)) =
      (fun z : EuclideanSpace ℝ (Fin n) => ‖z‖ ^ 2) ∘ (fun ω => toEuclideanCLM (𝕜 := ℝ)
        (1 - W * F * X) (toEuclideanCLM (𝕜 := ℝ) W ((mθ + toLp 2 (F *ᵥ β) + ε ω) - mθ)))
      from rfl, ← Measure.map_map (by fun_prop) hm,
    projected_residual_law_rv «ℙ» C W F X hC hW hX mθ β ε hε hlaw, law_norm_sq C W F X hW hX]

theorem chiSq_zero : chiSq 0 = Measure.dirac 0 := by
  have : (fun z : Fin 0 → ℝ => ∑ i, z i ^ 2) = fun _ => 0 := by
    funext z; simp
  rw [chiSq, this, Measure.map_const]
  simp

lemma projector_zero (C W : Matrix (Fin n) (Fin n) ℝ) (F : Matrix (Fin n) (Fin k) ℝ)
    (X : Matrix (Fin k) (Fin n) ℝ) (hW : IsUnit W ∧ W * C * Wᵀ = 1)
    (hX : G08AWhitening.IsMoorePenrose (W * F) X) (hν : n - F.rank = 0) :
    1 - W * F * X = 0 := by
  apply G08AWhitening.full_row_rank_branch (W * F) X hX
  rw [G08AWhitening.nu_eq C W F hW]
  have := F.rank_le_height
  omega

lemma Qstat_rank_zero (C W : Matrix (Fin n) (Fin n) ℝ) (F : Matrix (Fin n) (Fin k) ℝ)
    (X : Matrix (Fin k) (Fin n) ℝ) (hW : IsUnit W ∧ W * C * Wᵀ = 1)
    (hX : G08AWhitening.IsMoorePenrose (W * F) X) (hν : n - F.rank = 0)
    (mθ y : EuclideanSpace ℝ (Fin n)) : Qstat W F X mθ y = 0 := by
  simp [Qstat, projector_zero C W F X hW hX hν]

theorem chiSq_law_rank_zero (C W : Matrix (Fin n) (Fin n) ℝ) (F : Matrix (Fin n) (Fin k) ℝ)
    (X : Matrix (Fin k) (Fin n) ℝ) (hC : C.PosDef) (hW : IsUnit W ∧ W * C * Wᵀ = 1)
    (hX : G08AWhitening.IsMoorePenrose (W * F) X) (mθ : EuclideanSpace ℝ (Fin n)) (β : Fin k → ℝ)
    (hν : n - F.rank = 0) :
    (multivariateGaussian (mθ + toLp 2 (F *ᵥ β)) C).map (Qstat W F X mθ) = Measure.dirac 0 := by
  rw [chiSq_law C W F X hC hW hX mθ β, hν, chiSq_zero]

/-! ## T5: properties of χ²_ν -/

instance isProbabilityMeasure_chiSq (ν : ℕ) : IsProbabilityMeasure (chiSq ν) := by
  unfold chiSq
  exact Measure.isProbabilityMeasure_map (measurable_sumSq ν).aemeasurable

theorem chiSq_Iio_zero (ν : ℕ) : chiSq ν (Set.Iio 0) = 0 := by
  rw [chiSq, Measure.map_apply (measurable_sumSq ν) measurableSet_Iio]
  have : (fun z : Fin ν → ℝ => ∑ i, z i ^ 2) ⁻¹' Set.Iio 0 = ∅ := by
    ext z
    simp only [Set.mem_preimage, Set.mem_Iio, Set.mem_empty_iff_false, iff_false, not_lt]
    positivity
  rw [this, measure_empty]

theorem chiSq_singleton {ν : ℕ} (hν : 0 < ν) (c : ℝ) : chiSq ν {c} = 0 := by
  obtain ⟨m, rfl⟩ := Nat.exists_eq_succ_of_ne_zero hν.ne'
  haveI : NoAtoms (gaussianReal 0 1) := noAtoms_gaussianReal one_ne_zero
  rw [chiSq, Measure.map_apply (measurable_sumSq _) (measurableSet_singleton c)]
  set S := (fun z : Fin (m + 1) → ℝ => ∑ i, z i ^ 2) ⁻¹' {c} with hSdef
  have hS : MeasurableSet S := measurable_sumSq _ (measurableSet_singleton c)
  have hmp := measurePreserving_piFinSuccAbove (fun _ : Fin (m + 1) => gaussianReal 0 1) 0
  rw [← (MeasurePreserving.symm _ hmp).measure_preimage_equiv S]
  have hS' : MeasurableSet ((MeasurableEquiv.piFinSuccAbove (fun _ : Fin (m + 1) => ℝ) 0).symm ⁻¹' S) :=
    (MeasurableEquiv.measurable _) hS
  rw [Measure.prod_apply_symm hS']
  refine (lintegral_congr fun y => ?_).trans lintegral_zero
  set s := ∑ j, y j ^ 2
  apply measure_mono_null (t := {Real.sqrt (c - s), -Real.sqrt (c - s)})
  · intro x hx
    simp only [Set.mem_preimage, MeasurableEquiv.piFinSuccAbove_symm_apply, hSdef,
      Set.mem_singleton_iff] at hx
    have hx' : x ^ 2 + s = c := by simpa [s, Fin.sum_univ_succ] using hx
    have h0 : 0 ≤ c - s := by nlinarith [sq_nonneg x]
    have hsq : x ^ 2 = Real.sqrt (c - s) ^ 2 := by rw [Real.sq_sqrt h0]; linarith
    simpa [Set.mem_insert_iff, Set.mem_singleton_iff] using sq_eq_sq_iff_eq_or_eq_neg.mp hsq
  · exact (Set.toFinite _).measure_zero _

/-! ## T6: quantile convention -/

theorem cdf_lowerQuantile (ρ : Measure ℝ) [IsProbabilityMeasure ρ] {p : ℝ} (hp0 : 0 < p)
    (hp1 : p < 1) (hatom : ρ {lowerQuantile ρ p} = 0) : cdf ρ (lowerQuantile ρ p) = p := by
  set S := {x | p ≤ cdf ρ x} with hSdef
  set q := lowerQuantile ρ p with hqdef
  have hq : q = sInf S := rfl
  have hne : S.Nonempty := by
    obtain ⟨x, hx⟩ := ((tendsto_order.1 (tendsto_cdf_atTop (μ := ρ))).1 p hp1).exists
    exact ⟨x, hx.le⟩
  obtain ⟨L, hL⟩ := Filter.eventually_atBot.1 ((tendsto_order.1 (tendsto_cdf_atBot (μ := ρ))).2 p hp0)
  have hbdd : BddBelow S := ⟨L, fun x hx => le_of_not_gt fun h => absurd hx (not_le.2 (hL x h.le))⟩
  have hgt : ∀ x, q < x → p ≤ cdf ρ x := by
    intro x hx
    rw [hq] at hx
    obtain ⟨s, hsS, hsx⟩ := exists_lt_of_csInf_lt hne hx
    exact hsS.trans (monotone_cdf ρ hsx.le)
  have hlt : ∀ x, x < q → cdf ρ x ≤ p := by
    intro x hx
    by_contra h
    push Not at h
    exact absurd (csInf_le hbdd (show x ∈ S from h.le)) (not_le.2 (hq ▸ hx))
  have hright : Tendsto (cdf ρ) (𝓝[>] q) (𝓝 (cdf ρ q)) :=
    ((cdf ρ).right_continuous q).mono Set.Ioi_subset_Ici_self
  have hge : p ≤ cdf ρ q := ge_of_tendsto hright (eventually_nhdsWithin_of_forall hgt)
  have hleft : Tendsto (cdf ρ) (𝓝[<] q) (𝓝 (Function.leftLim (cdf ρ) q)) :=
    (monotone_cdf ρ).tendsto_leftLim q
  have hll : Function.leftLim (cdf ρ) q ≤ p := le_of_tendsto hleft (eventually_nhdsWithin_of_forall hlt)
  have hsing := (cdf ρ).measure_singleton q
  rw [measure_cdf, hatom] at hsing
  have : cdf ρ q - Function.leftLim (cdf ρ) q ≤ 0 := ENNReal.ofReal_eq_zero.1 hsing.symm
  linarith

theorem cdf_threshold {ν : ℕ} (hν : 0 < ν) {α : ℝ} (hα0 : 0 < α) (hα1 : α < 1) :
    cdf (chiSq ν) (threshold ν α) = 1 - α := by
  unfold threshold
  rw [if_neg hν.ne']
  exact cdf_lowerQuantile _ (by linarith) (by linarith) (chiSq_singleton hν _)

/-- consistency: at ν = 0 the lower quantile of χ²_0 = δ₀ is the source's q = 0 -/
theorem lowerQuantile_chiSq_zero {p : ℝ} (hp0 : 0 < p) (hp1 : p ≤ 1) :
    lowerQuantile (chiSq 0) p = 0 := by
  rw [lowerQuantile, chiSq_zero]
  have : {x : ℝ | p ≤ cdf (Measure.dirac 0) x} = Set.Ici 0 := by
    ext x
    simp only [Set.mem_setOf_eq, Set.mem_Ici, cdf_eq_real]
    by_cases hx : (0 : ℝ) ≤ x
    · simp [measureReal_def, hx, hp1]
    · simp [measureReal_def, hx, hp0]
  rw [this, csInf_Ici]

/-! ## T7: coverage -/

theorem coverage {Θ : Type*} (Ωd : Set Θ) (m : Θ → EuclideanSpace ℝ (Fin n)) (θs : Θ)
    (hθ : θs ∈ Ωd) (C W : Matrix (Fin n) (Fin n) ℝ) (F : Matrix (Fin n) (Fin k) ℝ)
    (X : Matrix (Fin k) (Fin n) ℝ) (hC : C.PosDef) (hW : IsUnit W ∧ W * C * Wᵀ = 1)
    (hX : G08AWhitening.IsMoorePenrose (W * F) X) (β : Fin k → ℝ) {α : ℝ} (hα0 : 0 < α)
    (hα1 : α < 1) (hν : 0 < n - F.rank) :
    (multivariateGaussian (m θs + toLp 2 (F *ᵥ β)) C)
        {y | θs ∈ confSet Ωd m W F X (threshold (n - F.rank) α) y} = ENNReal.ofReal (1 - α) := by
  have hset : {y | θs ∈ confSet Ωd m W F X (threshold (n - F.rank) α) y} =
      Qstat W F X (m θs) ⁻¹' Set.Iic (threshold (n - F.rank) α) := by
    ext y; simp [confSet, hθ]
  rw [hset, ← Measure.map_apply (measurable_Qstat W F X (m θs)) measurableSet_Iic,
    chiSq_law C W F X hC hW hX (m θs) β, ← ofReal_cdf, cdf_threshold hν hα0 hα1]

theorem coverage_rv {Θ : Type*} (Ωd : Set Θ) (m : Θ → EuclideanSpace ℝ (Fin n)) (θs : Θ)
    (hθ : θs ∈ Ωd) {Ω : Type*} [MeasurableSpace Ω] («ℙ» : Measure Ω)
    (C W : Matrix (Fin n) (Fin n) ℝ) (F : Matrix (Fin n) (Fin k) ℝ) (X : Matrix (Fin k) (Fin n) ℝ)
    (hC : C.PosDef) (hW : IsUnit W ∧ W * C * Wᵀ = 1) (hX : G08AWhitening.IsMoorePenrose (W * F) X)
    (β : Fin k → ℝ) (ε : Ω → EuclideanSpace ℝ (Fin n)) (hε : Measurable ε)
    (hlaw : «ℙ».map ε = multivariateGaussian 0 C) {α : ℝ} (hα0 : 0 < α) (hα1 : α < 1)
    (hν : 0 < n - F.rank) :
    «ℙ» {ω | θs ∈ confSet Ωd m W F X (threshold (n - F.rank) α) (m θs + toLp 2 (F *ᵥ β) + ε ω)} =
      ENNReal.ofReal (1 - α) := by
  have hset : {ω | θs ∈ confSet Ωd m W F X (threshold (n - F.rank) α)
      (m θs + toLp 2 (F *ᵥ β) + ε ω)} =
      (fun ω => Qstat W F X (m θs) (m θs + toLp 2 (F *ᵥ β) + ε ω)) ⁻¹'
        Set.Iic (threshold (n - F.rank) α) := by
    ext ω; simp [confSet, hθ]
  have hm : Measurable (fun ω => Qstat W F X (m θs) (m θs + toLp 2 (F *ᵥ β) + ε ω)) :=
    (measurable_Qstat W F X (m θs)).comp (hε.const_add _)
  rw [hset, ← Measure.map_apply hm measurableSet_Iic,
    chiSq_law_rv «ℙ» C W F X hC hW hX (m θs) β ε hε hlaw, ← ofReal_cdf, cdf_threshold hν hα0 hα1]

theorem confSet_rank_zero {Θ : Type*} (Ωd : Set Θ) (m : Θ → EuclideanSpace ℝ (Fin n))
    (C W : Matrix (Fin n) (Fin n) ℝ) (F : Matrix (Fin n) (Fin k) ℝ) (X : Matrix (Fin k) (Fin n) ℝ)
    (hW : IsUnit W ∧ W * C * Wᵀ = 1) (hX : G08AWhitening.IsMoorePenrose (W * F) X)
    (hν : n - F.rank = 0) (α : ℝ) (y : EuclideanSpace ℝ (Fin n)) :
    confSet Ωd m W F X (threshold (n - F.rank) α) y = Ωd := by
  ext θ
  simp [confSet, Qstat_rank_zero C W F X hW hX hν, threshold, hν]

theorem coverage_rank_zero {Θ : Type*} (Ωd : Set Θ) (m : Θ → EuclideanSpace ℝ (Fin n)) (θs : Θ)
    (hθ : θs ∈ Ωd) (C W : Matrix (Fin n) (Fin n) ℝ) (F : Matrix (Fin n) (Fin k) ℝ)
    (X : Matrix (Fin k) (Fin n) ℝ) (hC : C.PosDef) (hW : IsUnit W ∧ W * C * Wᵀ = 1)
    (hX : G08AWhitening.IsMoorePenrose (W * F) X) (β : Fin k → ℝ) (α : ℝ)
    (hν : n - F.rank = 0) :
    (multivariateGaussian (m θs + toLp 2 (F *ᵥ β)) C)
        {y | θs ∈ confSet Ωd m W F X (threshold (n - F.rank) α) y} = 1 := by
  simp only [confSet_rank_zero Ωd m C W F X hW hX hν α, hθ, Set.setOf_true, measure_univ]

/-! ## T8: ≤ versus < -/

theorem coverage_strict {Θ : Type*} (Ωd : Set Θ) (m : Θ → EuclideanSpace ℝ (Fin n)) (θs : Θ)
    (hθ : θs ∈ Ωd) (C W : Matrix (Fin n) (Fin n) ℝ) (F : Matrix (Fin n) (Fin k) ℝ)
    (X : Matrix (Fin k) (Fin n) ℝ) (hC : C.PosDef) (hW : IsUnit W ∧ W * C * Wᵀ = 1)
    (hX : G08AWhitening.IsMoorePenrose (W * F) X) (β : Fin k → ℝ) {α : ℝ} (hα0 : 0 < α)
    (hα1 : α < 1) (hν : 0 < n - F.rank) :
    (multivariateGaussian (m θs + toLp 2 (F *ᵥ β)) C)
        {y | θs ∈ Ωd ∧ Qstat W F X (m θs) y < threshold (n - F.rank) α} =
          ENNReal.ofReal (1 - α) := by
  have hset : {y | θs ∈ Ωd ∧ Qstat W F X (m θs) y < threshold (n - F.rank) α} =
      Qstat W F X (m θs) ⁻¹' Set.Iio (threshold (n - F.rank) α) := by
    ext y; simp [hθ]
  rw [hset, ← Measure.map_apply (measurable_Qstat W F X (m θs)) measurableSet_Iio,
    chiSq_law C W F X hC hW hX (m θs) β, ← Set.Iic_sdiff_right,
    measure_sdiff_null (chiSq_singleton hν _), ← ofReal_cdf, cdf_threshold hν hα0 hα1]

theorem strict_rank_zero_fails {Θ : Type*} (Ωd : Set Θ) (m : Θ → EuclideanSpace ℝ (Fin n))
    (θs : Θ) (C W : Matrix (Fin n) (Fin n) ℝ) (F : Matrix (Fin n) (Fin k) ℝ)
    (X : Matrix (Fin k) (Fin n) ℝ) (hC : C.PosDef) (hW : IsUnit W ∧ W * C * Wᵀ = 1)
    (hX : G08AWhitening.IsMoorePenrose (W * F) X) (β : Fin k → ℝ) (α : ℝ)
    (hν : n - F.rank = 0) :
    (multivariateGaussian (m θs + toLp 2 (F *ᵥ β)) C)
        {y | θs ∈ Ωd ∧ Qstat W F X (m θs) y < threshold (n - F.rank) α} = 0 := by
  have hset : {y | θs ∈ Ωd ∧ Qstat W F X (m θs) y < threshold (n - F.rank) α} = ∅ := by
    ext y
    simp [Qstat_rank_zero C W F X hW hX hν, threshold, hν]
  rw [hset, measure_empty]

/-! ## T9: non-vacuity and negative controls -/

/-- hypotheses jointly satisfiable with ν = 1 > 0 (n = k = 1, C = W = 1, F = X = 0) -/
theorem nonvacuous_nu_pos :
    ∃ (C W F X : Matrix (Fin 1) (Fin 1) ℝ), C.PosDef ∧ (IsUnit W ∧ W * C * Wᵀ = 1) ∧
      G08AWhitening.IsMoorePenrose (W * F) X ∧ 1 - F.rank = 1 := by
  refine ⟨1, 1, 0, 0, Matrix.PosDef.one, ⟨isUnit_one, by simp⟩, ?_, by simp [Matrix.rank_zero]⟩
  simp [G08AWhitening.IsMoorePenrose]

/-- hypotheses jointly satisfiable with ν = 0 (n = k = 1, C = W = F = X = 1) -/
theorem nonvacuous_nu_zero :
    ∃ (C W F X : Matrix (Fin 1) (Fin 1) ℝ), C.PosDef ∧ (IsUnit W ∧ W * C * Wᵀ = 1) ∧
      G08AWhitening.IsMoorePenrose (W * F) X ∧ 1 - F.rank = 0 := by
  refine ⟨1, 1, 1, 1, Matrix.PosDef.one, ⟨isUnit_one, by simp⟩, ?_, by simp [Matrix.rank_one]⟩
  simp [G08AWhitening.IsMoorePenrose]

/-- the degrees of freedom matter: χ²_1 ≠ χ²_0 = δ₀ -/
theorem chiSq_one_ne_zero : chiSq 1 ≠ chiSq 0 := by
  intro h
  have h1 := chiSq_singleton (ν := 1) one_pos 0
  rw [h, chiSq_zero] at h1
  simp at h1

end G08BGaussianLaw
