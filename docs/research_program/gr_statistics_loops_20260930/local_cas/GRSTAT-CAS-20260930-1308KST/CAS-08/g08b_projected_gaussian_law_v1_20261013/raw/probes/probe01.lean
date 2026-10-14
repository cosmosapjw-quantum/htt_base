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

theorem projected_residual_law_rv {Ω : Type*} [MeasurableSpace Ω] (ℙ : Measure Ω)
    (C W : Matrix (Fin n) (Fin n) ℝ) (F : Matrix (Fin n) (Fin k) ℝ) (X : Matrix (Fin k) (Fin n) ℝ)
    (hC : C.PosDef) (hW : IsUnit W ∧ W * C * Wᵀ = 1) (hX : G08AWhitening.IsMoorePenrose (W * F) X)
    (mθ : EuclideanSpace ℝ (Fin n)) (β : Fin k → ℝ) (ε : Ω → EuclideanSpace ℝ (Fin n))
    (hε : Measurable ε) (hlaw : ℙ.map ε = multivariateGaussian 0 C) :
    ℙ.map (fun ω => toEuclideanCLM (𝕜 := ℝ) (1 - W * F * X)
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
    rw [← charFun_apply, charFun_stdGaussian, charFun_stdGaussian, hnorm]
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
      rw [hP]
      simp [← mulVec_mulVec, mulVec, dotProduct]
      trace_state
      sorry
    sorry

end G08BGaussianLaw
