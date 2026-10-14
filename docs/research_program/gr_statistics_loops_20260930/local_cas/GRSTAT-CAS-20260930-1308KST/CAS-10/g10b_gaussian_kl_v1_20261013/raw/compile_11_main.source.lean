import Mathlib
import CAS10C01
import CAS10C03
import P12GaussianLaw

/-!
# G10-B: Gaussian compression law, block rotation and Kullback-Leibler divergence

Package task G10-B (CAS-10 C01/C03 follow-up). Frozen statements: `FROZEN_TARGETS.md`.

* Observation law (theory (I9)): independent coordinates, coordinate `k` of sector `j` is
  `N(μ_{j,k}, σ_j²)`, encoded as `Measure.pi` of `gaussianReal` on `Idx d → ℝ`.
* Compression: separate-sector powers `P_j = Σ_k x_{j,k}²`.
* KL: Mathlib's measure-theoretic `InformationTheory.klDiv`.

No scientific admission is claimed. Physical admissibility of the tuples is owned elsewhere
(C01/C02/G10-A).
-/

namespace G10BGaussianKL

open MeasureTheory ProbabilityTheory InformationTheory Matrix
open scoped ENNReal NNReal

/-! ## Generic KL infrastructure (not present at the Mathlib pin) -/



/-- KL is invariant under a common measurable embedding. -/
theorem klDiv_map_of_measurableEmbedding {α β : Type*} [MeasurableSpace α] [MeasurableSpace β]
    {f : α → β} (hf : MeasurableEmbedding f) (μ ν : Measure α) [IsFiniteMeasure μ]
    [IsFiniteMeasure ν] : klDiv (μ.map f) (ν.map f) = klDiv μ ν := by
  have hac : μ.map f ≪ ν.map f ↔ μ ≪ ν := by
    refine ⟨fun h s hs => ?_, hf.absolutelyContinuous_map⟩
    have h1 : (ν.map f) (f '' s) = 0 := by
      rw [hf.map_apply, hf.injective.preimage_image]; exact hs
    have h2 := h h1
    rwa [hf.map_apply, hf.injective.preimage_image] at h2
  by_cases h : μ ≪ ν
  · rw [klDiv_eq_lintegral_klFun_of_ac h, klDiv_eq_lintegral_klFun_of_ac (hac.2 h),
      hf.lintegral_map]
    refine lintegral_congr_ae ?_
    filter_upwards [hf.rnDeriv_map μ ν] with x hx
    rw [hx]
  · rw [klDiv_of_not_ac h, klDiv_of_not_ac (fun h' => h (hac.1 h'))]

/-- Tensorization of KL for products of probability measures. -/
theorem klDiv_prod {α β : Type*} [MeasurableSpace α] [MeasurableSpace β]
    (μ ν : Measure α) (μ' ν' : Measure β) [IsProbabilityMeasure μ] [IsProbabilityMeasure ν]
    [IsProbabilityMeasure μ'] [IsProbabilityMeasure ν'] :
    klDiv (μ.prod μ') (ν.prod ν') = klDiv μ ν + klDiv μ' ν' := by
  rw [← Measure.compProd_const, ← Measure.compProd_const, klDiv_compProd_eq_add,
    Measure.compProd_const, Measure.compProd_const]
  congr 1
  rw [← Measure.prod_swap (μ := μ') (ν := μ), ← Measure.prod_swap (μ := ν') (ν := μ)]
  have hemb : MeasurableEmbedding (Prod.swap : β × α → α × β) :=
    (MeasurableEquiv.prodComm : β × α ≃ᵐ α × β).measurableEmbedding
  rw [klDiv_map_of_measurableEmbedding hemb]
  rw [← Measure.compProd_const, ← Measure.compProd_const, klDiv_compProd_left]

theorem klDiv_pi_fin {X : Type} [MeasurableSpace X] :
    ∀ (n : ℕ) (P Q : Fin n → Measure X) [∀ i, IsProbabilityMeasure (P i)]
      [∀ i, IsProbabilityMeasure (Q i)],
      klDiv (Measure.pi P) (Measure.pi Q) = ∑ i, klDiv (P i) (Q i)
  | 0, P, Q, _, _ => by
    have hP := (measurePreserving_pi_empty P).map_eq
    have hQ := (measurePreserving_pi_empty Q).map_eq
    rw [← klDiv_map_of_measurableEmbedding
      (MeasurableEquiv.ofUniqueOfUnique ((i : Fin 0) → X) Unit).measurableEmbedding, hP, hQ]
    simp
  | n + 1, P, Q, _, _ => by
    have hP := (measurePreserving_piFinSuccAbove P 0).map_eq
    have hQ := (measurePreserving_piFinSuccAbove Q 0).map_eq
    rw [← klDiv_map_of_measurableEmbedding
      (MeasurableEquiv.piFinSuccAbove (fun _ => X) 0).measurableEmbedding, hP, hQ, klDiv_prod,
      klDiv_pi_fin n, Fin.sum_univ_succ]
    rfl

theorem klDiv_pi {ι : Type*} {X : Type} [Fintype ι] [MeasurableSpace X] (P Q : ι → Measure X)
    [∀ i, IsProbabilityMeasure (P i)] [∀ i, IsProbabilityMeasure (Q i)] :
    klDiv (Measure.pi P) (Measure.pi Q) = ∑ i, klDiv (P i) (Q i) := by
  let e : Fin (Fintype.card ι) ≃ ι := (Fintype.equivFin ι).symm
  have hP := (measurePreserving_piCongrLeft P e).map_eq
  have hQ := (measurePreserving_piCongrLeft Q e).map_eq
  rw [← hP, ← hQ, klDiv_map_of_measurableEmbedding
    (MeasurableEquiv.piCongrLeft (fun _ => X) e).measurableEmbedding,
    klDiv_pi_fin, Equiv.sum_comp e (fun i => klDiv (P i) (Q i))]

/-- KL divergence of two real Gaussians with common positive variance. -/
theorem klDiv_gaussianReal_same_var (a b : ℝ) {v : ℝ≥0} (hv : v ≠ 0) :
    klDiv (gaussianReal a v) (gaussianReal b v) = ENNReal.ofReal ((a - b) ^ 2 / (2 * v)) := by
  have hac : gaussianReal a v ≪ gaussianReal b v :=
    (gaussianReal_absolutelyContinuous a hv).trans (gaussianReal_absolutelyContinuous' b hv)
  have hvpos : (0 : ℝ) < v := by positivity
  -- explicit log-likelihood ratio
  have hrn : (gaussianReal a v).rnDeriv (gaussianReal b v) =ᵐ[volume]
      fun x => (gaussianPDF b v x)⁻¹ * gaussianPDF a v x := by
    rw [gaussianReal_of_var_ne_zero b hv]
    have h1 := Measure.rnDeriv_withDensity_right (gaussianReal a v) volume
      (measurable_gaussianPDF b v).aemeasurable
      (ae_of_all _ fun x => (gaussianPDF_pos _ hv x).ne') (ae_of_all _ fun _ => gaussianPDF_ne_top)
    filter_upwards [h1, rnDeriv_gaussianReal a v] with x hx hx2
    rw [hx, hx2]
  have hllr : llr (gaussianReal a v) (gaussianReal b v) =ᵐ[gaussianReal a v]
      fun x => ((x - b) ^ 2 - (x - a) ^ 2) / (2 * v) := by
    have hrn' := gaussianReal_absolutelyContinuous a hv hrn
    filter_upwards [hrn'] with x hx
    rw [llr, hx, ENNReal.toReal_mul, ENNReal.toReal_inv, toReal_gaussianPDF, toReal_gaussianPDF]
    have hs : √(2 * Real.pi * v) ≠ 0 := by positivity
    have key : (gaussianPDFReal b v x)⁻¹ * gaussianPDFReal a v x =
        Real.exp (((x - b) ^ 2 - (x - a) ^ 2) / (2 * v)) := by
      simp only [gaussianPDFReal_def]
      rw [show ((x - b) ^ 2 - (x - a) ^ 2) / (2 * (v : ℝ)) =
          -(x - a) ^ 2 / (2 * v) - -(x - b) ^ 2 / (2 * v) by ring, Real.exp_sub, mul_inv, inv_inv]
      field_simp
    rw [key, Real.log_exp]
  have hint_id : Integrable (fun x : ℝ => x) (gaussianReal a v) :=
    (memLp_id_gaussianReal 1).integrable le_rfl
  have hint : Integrable (fun x : ℝ => ((x - b) ^ 2 - (x - a) ^ 2) / (2 * v))
      (gaussianReal a v) := by
    have : (fun x : ℝ => ((x - b) ^ 2 - (x - a) ^ 2) / (2 * v)) =
        fun x => (2 * (a - b) / (2 * v)) * x + (b ^ 2 - a ^ 2) / (2 * v) := by
      funext x; field_simp; ring
    rw [this]
    exact (hint_id.const_mul _).add (integrable_const _)
  rw [klDiv_of_ac_of_integrable hac ((integrable_congr hllr).2 hint), integral_congr_ae hllr]
  simp only [probReal_univ, add_sub_cancel_right]
  congr 1
  have : (fun x : ℝ => ((x - b) ^ 2 - (x - a) ^ 2) / (2 * v)) =
      fun x => (2 * (a - b) / (2 * v)) * x + (b ^ 2 - a ^ 2) / (2 * v) := by
    funext x; field_simp; ring
  rw [this, integral_add (hint_id.const_mul _) (integrable_const _), integral_const_mul,
    integral_id_gaussianReal, integral_const]
  simp only [probReal_univ, smul_eq_mul, one_mul]
  field_simp
  ring


/-! ## Generic sector model -/

section Generic


variable {J : Type*} [Fintype J] [DecidableEq J] (d : J → ℕ)

abbrev Idx := Σ j : J, Fin (d j)

noncomputable def coordVar (σ : J → ℝ) (i : Idx d) : ℝ≥0 := ⟨σ i.1 ^ 2, sq_nonneg _⟩

noncomputable def coordLaw {ι : Type*} [Fintype ι] (μ : ι → ℝ) (w : ι → ℝ≥0) :
    Measure (ι → ℝ) :=
  Measure.pi fun i => gaussianReal (μ i) (w i)

noncomputable def obsLaw (μ : Idx d → ℝ) (σ : J → ℝ) : Measure (Idx d → ℝ) :=
  coordLaw μ (coordVar d σ)

def powers (x : Idx d → ℝ) : J → ℝ := fun j => ∑ k : Fin (d j), x ⟨j, k⟩ ^ 2

def blockMap (R : (j : J) → Matrix (Fin (d j)) (Fin (d j)) ℝ) (x : Idx d → ℝ) : Idx d → ℝ :=
  fun i => (R i.1 *ᵥ fun k => x ⟨i.1, k⟩) i.2

instance {ι : Type*} [Fintype ι] (μ : ι → ℝ) (w : ι → ℝ≥0) :
    IsProbabilityMeasure (coordLaw μ w) := by
  unfold coordLaw; infer_instance

instance (μ : Idx d → ℝ) (σ : J → ℝ) : IsProbabilityMeasure (obsLaw d μ σ) := by
  unfold obsLaw; infer_instance

theorem coordVar_coe (σ : J → ℝ) (i : Idx d) : (coordVar d σ i : ℝ) = σ i.1 ^ 2 := rfl

theorem measurable_toLp : Measurable (WithLp.toLp 2 : (Idx d → ℝ) → EuclideanSpace ℝ (Idx d)) :=
  (MeasurableEquiv.toLp 2 (Idx d → ℝ)).measurable

theorem measurable_blockMap (R : (j : J) → Matrix (Fin (d j)) (Fin (d j)) ℝ) :
    Measurable (blockMap d R) := by
  unfold blockMap
  apply measurable_pi_lambda
  intro i
  simp only [Matrix.mulVec, dotProduct]
  fun_prop

theorem measurable_powers : Measurable (powers d) := by
  unfold powers
  fun_prop

/-- Adjoint identity for the blockwise map. -/
theorem sum_blockMap_mul (R : (j : J) → Matrix (Fin (d j)) (Fin (d j)) ℝ) (x t : Idx d → ℝ) :
    ∑ i, blockMap d R x i * t i = ∑ i, x i * blockMap d (fun j => (R j)ᵀ) t i := by
  simp only [blockMap, Fintype.sum_sigma]
  refine Finset.sum_congr rfl fun j _ => ?_
  have h := (Matrix.dotProduct_mulVec (fun k => x ⟨j, k⟩) (R j)ᵀ (fun k => t ⟨j, k⟩))
  rw [Matrix.vecMul_transpose] at h
  simpa [dotProduct] using h.symm

theorem sum_sq_blockMap (R : (j : J) → Matrix (Fin (d j)) (Fin (d j)) ℝ)
    (hR : ∀ j, (R j)ᵀ * R j = 1) (x : Idx d → ℝ) (j : J) :
    ∑ k : Fin (d j), blockMap d R x ⟨j, k⟩ ^ 2 = ∑ k : Fin (d j), x ⟨j, k⟩ ^ 2 := by
  set y : Fin (d j) → ℝ := fun k => x ⟨j, k⟩
  have h1 : ∑ k : Fin (d j), blockMap d R x ⟨j, k⟩ ^ 2 = (R j *ᵥ y) ⬝ᵥ (R j *ᵥ y) := by
    simp [blockMap, dotProduct, sq, y]
  have h2 : ∑ k : Fin (d j), x ⟨j, k⟩ ^ 2 = y ⬝ᵥ y := by simp [dotProduct, sq, y]
  rw [h1, h2, Matrix.dotProduct_mulVec, ← Matrix.vecMul_transpose, Matrix.vecMul_vecMul, hR j,
    Matrix.vecMul_one]


theorem obsLaw_map_blockMap (R : (j : J) → Matrix (Fin (d j)) (Fin (d j)) ℝ)
    (hR : ∀ j, (R j)ᵀ * R j = 1) (μ : Idx d → ℝ) (σ : J → ℝ) :
    (obsLaw d μ σ).map (blockMap d R) = obsLaw d (blockMap d R μ) σ := by
  have hRt : ∀ j, (R j)ᵀᵀ * (R j)ᵀ = 1 := fun j => by
    rw [Matrix.transpose_transpose]; exact mul_eq_one_comm.mp (hR j)
  haveI : IsProbabilityMeasure ((obsLaw d μ σ).map (blockMap d R)) :=
    Measure.isProbabilityMeasure_map (measurable_blockMap d R).aemeasurable
  have hin : ∀ (y : Idx d → ℝ) (u : EuclideanSpace ℝ (Idx d)),
      inner ℝ (WithLp.toLp 2 y) u = ∑ i, y i * u i := by
    intro y u
    simp [PiLp.inner_apply, mul_comm]
  unfold obsLaw coordLaw
  refine (charFun_eq_pi_iff).1 (fun t => ?_)
  set s : Idx d → ℝ := blockMap d (fun j => (R j)ᵀ) (fun i => t i) with hs
  have h1 : charFun (((Measure.pi fun i => gaussianReal (μ i) (coordVar d σ i)).map
        (blockMap d R)).map (WithLp.toLp 2)) t =
      charFun ((Measure.pi fun i => gaussianReal (μ i) (coordVar d σ i)).map (WithLp.toLp 2))
        (WithLp.toLp 2 s) := by
    rw [Measure.map_map (measurable_toLp d) (measurable_blockMap d R)]
    simp only [charFun_apply]
    rw [integral_map ((measurable_toLp d).comp (measurable_blockMap d R)).aemeasurable
      (by fun_prop), integral_map (measurable_toLp d).aemeasurable (by fun_prop)]
    congr 1
    funext x
    simp only [Function.comp_apply, hin]
    rw [sum_blockMap_mul d R x (fun i => t i)]
  rw [h1, charFun_pi]
  simp only [charFun_gaussianReal, ← Complex.exp_sum]
  congr 1
  have hlin : ∑ i, s i * μ i = ∑ i, t i * blockMap d R μ i := by
    calc ∑ i, s i * μ i = ∑ i, μ i * s i := Finset.sum_congr rfl fun i _ => mul_comm _ _
      _ = ∑ i, blockMap d R μ i * t i := (sum_blockMap_mul d R μ (fun i => t i)).symm
      _ = ∑ i, t i * blockMap d R μ i := Finset.sum_congr rfl fun i _ => mul_comm _ _
  have hquad : ∑ i, (coordVar d σ i : ℝ) * s i ^ 2 = ∑ i, (coordVar d σ i : ℝ) * t i ^ 2 := by
    simp only [coordVar_coe, Fintype.sum_sigma]
    refine Finset.sum_congr rfl fun j _ => ?_
    rw [← Finset.mul_sum, ← Finset.mul_sum]
    congr 1
    exact sum_sq_blockMap d (fun j => (R j)ᵀ) hRt (fun i => t i) j
  have e1 : ∑ i, ((↑(s i) : ℂ) * ↑(μ i) * Complex.I - ↑(coordVar d σ i : ℝ) * ↑(s i) ^ 2 / 2) =
      ↑(∑ i, s i * μ i) * Complex.I - ↑(∑ i, (coordVar d σ i : ℝ) * s i ^ 2) / 2 := by
    push_cast
    rw [Finset.sum_sub_distrib, Finset.sum_mul, Finset.sum_div]
  have e2 : ∑ i, ((↑(t i) : ℂ) * ↑(blockMap d R μ i) * Complex.I -
        ↑(coordVar d σ i : ℝ) * ↑(t i) ^ 2 / 2) =
      ↑(∑ i, t i * blockMap d R μ i) * Complex.I -
        ↑(∑ i, (coordVar d σ i : ℝ) * t i ^ 2) / 2 := by
    push_cast
    rw [Finset.sum_sub_distrib, Finset.sum_mul, Finset.sum_div]
  convert e1.trans ?_ using 1
  · rw [e2, hlin, hquad]


/-! ### T1b, T2, T3, T4: rotation and compression -/

theorem blockMap_zero (R : (j : J) → Matrix (Fin (d j)) (Fin (d j)) ℝ) :
    blockMap d R 0 = 0 := by
  funext i
  simp [blockMap, Matrix.mulVec, dotProduct]

theorem obsLaw_zero_map_blockMap (R : (j : J) → Matrix (Fin (d j)) (Fin (d j)) ℝ)
    (hR : ∀ j, (R j)ᵀ * R j = 1) (σ : J → ℝ) :
    (obsLaw d 0 σ).map (blockMap d R) = obsLaw d 0 σ := by
  rw [obsLaw_map_blockMap d R hR, blockMap_zero]

theorem powers_blockMap (R : (j : J) → Matrix (Fin (d j)) (Fin (d j)) ℝ)
    (hR : ∀ j, (R j)ᵀ * R j = 1) (x : Idx d → ℝ) :
    powers d (blockMap d R x) = powers d x := by
  funext j
  exact sum_sq_blockMap d R hR x j

theorem compressed_law_eq (R : (j : J) → Matrix (Fin (d j)) (Fin (d j)) ℝ)
    (hR : ∀ j, (R j)ᵀ * R j = 1) (μ : Idx d → ℝ) (σ : J → ℝ) :
    (obsLaw d (blockMap d R μ) σ).map (powers d) = (obsLaw d μ σ).map (powers d) := by
  rw [← obsLaw_map_blockMap d R hR, Measure.map_map (measurable_powers d) (measurable_blockMap d R)]
  congr 1
  funext x
  exact powers_blockMap d R hR x

theorem powersOnly_integral_eq (R : (j : J) → Matrix (Fin (d j)) (Fin (d j)) ℝ)
    (hR : ∀ j, (R j)ᵀ * R j = 1) (μ : Idx d → ℝ) (σ : J → ℝ) (φ : (J → ℝ) → ℝ)
    (hφ : Measurable φ) :
    ∫ x, φ (powers d x) ∂(obsLaw d (blockMap d R μ) σ) = ∫ x, φ (powers d x) ∂(obsLaw d μ σ) := by
  have h1 := integral_map (μ := obsLaw d (blockMap d R μ) σ) (measurable_powers d).aemeasurable
    hφ.aestronglyMeasurable
  have h2 := integral_map (μ := obsLaw d μ σ) (measurable_powers d).aemeasurable
    hφ.aestronglyMeasurable
  rw [compressed_law_eq d R hR] at h1
  exact h1.symm.trans h2

theorem powersOnly_power_le_size (R : (j : J) → Matrix (Fin (d j)) (Fin (d j)) ℝ)
    (hR : ∀ j, (R j)ᵀ * R j = 1) (μ : Idx d → ℝ) (σ : J → ℝ) (φ : (J → ℝ) → ℝ)
    (hφ : Measurable φ) (α : ℝ) (hsize : ∫ x, φ (powers d x) ∂(obsLaw d μ σ) ≤ α) :
    ∫ x, φ (powers d x) ∂(obsLaw d (blockMap d R μ) σ) ≤ α := by
  rw [powersOnly_integral_eq d R hR μ σ φ hφ]
  exact hsize

/-! ### K2, K3: KL of the product Gaussian laws -/

theorem klDiv_coordLaw {ι : Type*} [Fintype ι] (μ ν : ι → ℝ) (w : ι → ℝ≥0)
    (hw : ∀ i, w i ≠ 0) :
    klDiv (coordLaw μ w) (coordLaw ν w) = ENNReal.ofReal (∑ i, (μ i - ν i) ^ 2 / (2 * w i)) := by
  unfold coordLaw
  rw [klDiv_pi, ENNReal.ofReal_sum_of_nonneg (fun i _ => by positivity)]
  exact Finset.sum_congr rfl fun i _ => klDiv_gaussianReal_same_var _ _ (hw i)

theorem klDiv_obsLaw (μ ν : Idx d → ℝ) (σ : J → ℝ) (hσ : ∀ j, 0 < σ j) :
    klDiv (obsLaw d μ σ) (obsLaw d ν σ) =
      ENNReal.ofReal ((1 / 2) * ∑ i : Idx d, (μ i - ν i) ^ 2 / σ i.1 ^ 2) := by
  have hw : ∀ i, coordVar d σ i ≠ 0 := by
    intro i h
    have h2 : (coordVar d σ i : ℝ) = 0 := by rw [h]; rfl
    rw [coordVar_coe] at h2
    exact pow_ne_zero 2 (hσ i.1).ne' h2
  unfold obsLaw
  rw [klDiv_coordLaw μ ν _ hw]
  congr 1
  rw [Finset.mul_sum]
  refine Finset.sum_congr rfl fun i _ => ?_
  rw [coordVar_coe]
  have := (hσ i.1).ne'
  field_simp

/-! ### B1, B2: identification with `multivariateGaussian`; law equality -/

theorem obsLaw_toLp_eq_multivariateGaussian (μ : Idx d → ℝ) (σ : J → ℝ) :
    (obsLaw d μ σ).map (WithLp.toLp 2) =
      multivariateGaussian (WithLp.toLp 2 μ) (Matrix.diagonal fun i : Idx d => σ i.1 ^ 2) := by
  have hS : (Matrix.diagonal fun i : Idx d => σ i.1 ^ 2).PosSemidef := by
    rw [Matrix.posSemidef_diagonal_iff]
    intro i
    positivity
  haveI : IsProbabilityMeasure ((obsLaw d μ σ).map (WithLp.toLp 2)) :=
    Measure.isProbabilityMeasure_map (measurable_toLp d).aemeasurable
  apply Measure.ext_of_charFun
  funext t
  have hin : inner ℝ t (WithLp.toLp 2 μ) = ∑ i, t i * μ i := by
    simp [PiLp.inner_apply, mul_comm]
  have hq : (WithLp.ofLp t) ⬝ᵥ (Matrix.diagonal fun i : Idx d => σ i.1 ^ 2) *ᵥ (WithLp.ofLp t) =
      ∑ i, (coordVar d σ i : ℝ) * t i ^ 2 := by
    simp only [dotProduct, Matrix.mulVec_diagonal, coordVar_coe]
    exact Finset.sum_congr rfl fun i _ => by ring
  unfold obsLaw coordLaw
  rw [charFun_pi, charFun_multivariateGaussian hS]
  simp only [charFun_gaussianReal, ← Complex.exp_sum]
  congr 1
  rw [hin, hq]
  push_cast
  rw [Finset.sum_sub_distrib, Finset.sum_mul, Finset.sum_div]

theorem obsLaw_eq_iff (μ ν : Idx d → ℝ) (σ : J → ℝ) :
    obsLaw d μ σ = obsLaw d ν σ ↔ μ = ν := by
  constructor
  · intro h
    funext i
    have hm := (measurePreserving_eval (fun i => gaussianReal (μ i) (coordVar d σ i)) i).map_eq
    have hn := (measurePreserving_eval (fun i => gaussianReal (ν i) (coordVar d σ i)) i).map_eq
    unfold obsLaw coordLaw at h
    rw [h, hn] at hm
    exact ((gaussianReal_ext_iff.1 hm).1).symm
  · rintro rfl
    rfl

end Generic

/-! ## Application to the C01/C03 counterexample (sectors Z₀, Z₁, m, p, T) -/

section Application


/-- Sector dimensions `(1,3,1,3,5)` in the order (Z₀, Z₁, m, p, T). -/
def blockDim (j : Fin 5) : ℕ := match j.val with | 0 => 1 | 1 => 3 | 2 => 1 | 3 => 3 | _ => 5

abbrev Obs := Idx blockDim → ℝ

/-- Sector-wise assembly of a mean vector. -/
def meanOf (z0 : ℝ) (z1 : Fin 3 → ℝ) (m : ℝ) (p : Fin 3 → ℝ) (t : Fin 5 → ℝ) : Obs
  | ⟨⟨0, _⟩, _⟩ => z0
  | ⟨⟨1, _⟩, k⟩ => z1 k
  | ⟨⟨2, _⟩, _⟩ => m
  | ⟨⟨3, _⟩, k⟩ => p k
  | ⟨⟨4, _⟩, k⟩ => t k
  | ⟨⟨n + 5, h⟩, _⟩ => absurd h (by omega)

def ofMean (u : CAS10C03.Mean) : Obs := meanOf u.z0 u.z1 u.m u.p u.t

/-- `CAS10C03.R` on the slope-dipole sector `p`, identity elsewhere. -/
def rotP : (j : Fin 5) → Matrix (Fin (blockDim j)) (Fin (blockDim j)) ℝ
  | ⟨3, _⟩ => CAS10C03.R
  | _ => 1

section Unfold

variable (z0 : ℝ) (z1 : Fin 3 → ℝ) (m : ℝ) (p : Fin 3 → ℝ) (t : Fin 5 → ℝ)

theorem meanOf_0 (k : Fin 1) : meanOf z0 z1 m p t ⟨0, k⟩ = z0 := rfl
theorem meanOf_1 (k : Fin 3) : meanOf z0 z1 m p t ⟨1, k⟩ = z1 k := rfl
theorem meanOf_2 (k : Fin 1) : meanOf z0 z1 m p t ⟨2, k⟩ = m := rfl
theorem meanOf_3 (k : Fin 3) : meanOf z0 z1 m p t ⟨3, k⟩ = p k := rfl
theorem meanOf_4 (k : Fin 5) : meanOf z0 z1 m p t ⟨4, k⟩ = t k := rfl

end Unfold

theorem sum_Obs (f : Obs) :
    ∑ i, f i = ∑ k : Fin 1, f ⟨0, k⟩ + ∑ k : Fin 3, f ⟨1, k⟩ + ∑ k : Fin 1, f ⟨2, k⟩ +
      ∑ k : Fin 3, f ⟨3, k⟩ + ∑ k : Fin 5, f ⟨4, k⟩ := by
  rw [Fintype.sum_sigma, Fin.sum_univ_five]
  rfl

theorem powers_apply (x : Obs) :
    powers blockDim x = ![∑ k : Fin 1, x ⟨0, k⟩ ^ 2, ∑ k : Fin 3, x ⟨1, k⟩ ^ 2,
      ∑ k : Fin 1, x ⟨2, k⟩ ^ 2, ∑ k : Fin 3, x ⟨3, k⟩ ^ 2, ∑ k : Fin 5, x ⟨4, k⟩ ^ 2] := by
  funext j
  fin_cases j <;> rfl

/-- A1 -/
theorem rotP_orthogonal : ∀ j, (rotP j)ᵀ * rotP j = 1
  | ⟨0, _⟩ => by simp [rotP]; exact Matrix.mul_one _
  | ⟨1, _⟩ => by simp [rotP]; exact Matrix.mul_one _
  | ⟨2, _⟩ => by simp [rotP]; exact Matrix.mul_one _
  | ⟨3, _⟩ => CAS10C03.R_orthogonal
  | ⟨4, _⟩ => by simp [rotP]; exact Matrix.mul_one _
  | ⟨n + 5, h⟩ => absurd h (by omega)

/-- A2 -/
theorem blockMap_rotP_first (H z0 m : ℝ) (z1 : Fin 3 → ℝ) (t : Fin 5 → ℝ) :
    blockMap blockDim rotP (ofMean (CAS10C03.first H z0 m z1 t)) =
      ofMean (CAS10C03.second H z0 m z1 t) := by
  funext i
  rcases i with ⟨⟨j, hj⟩, k⟩
  match j, hj, k with
  | 0, _, k => simp [blockMap, rotP, ofMean, meanOf, CAS10C03.first, CAS10C03.second]
  | 1, _, k => simp [blockMap, rotP, ofMean, meanOf, CAS10C03.first, CAS10C03.second]
  | 2, _, k => simp [blockMap, rotP, ofMean, meanOf, CAS10C03.first, CAS10C03.second]
  | 3, _, k =>
    show (CAS10C03.R *ᵥ CAS10C03.p H) k = CAS10C03.pPrime H k
    rw [CAS10C03.R_maps_p]
  | 4, _, k => simp [blockMap, rotP, ofMean, meanOf, CAS10C03.first, CAS10C03.second]
  | n + 5, h, _ => exact absurd h (by omega)

/-- A3: equality of the joint law of all five compressed powers. -/
theorem compressed_laws_equal (H z0 m : ℝ) (z1 : Fin 3 → ℝ) (t : Fin 5 → ℝ) (σ : Fin 5 → ℝ) :
    (obsLaw blockDim (ofMean (CAS10C03.second H z0 m z1 t)) σ).map (powers blockDim) =
      (obsLaw blockDim (ofMean (CAS10C03.first H z0 m z1 t)) σ).map (powers blockDim) := by
  rw [← blockMap_rotP_first]
  exact compressed_law_eq blockDim rotP rotP_orthogonal _ σ

/-- A4: every measurable powers-only statistic (in particular every randomized test with values
in `[0,1]`) has the same expectation under the two models. -/
theorem powersOnly_tests_agree (H z0 m : ℝ) (z1 : Fin 3 → ℝ) (t : Fin 5 → ℝ) (σ : Fin 5 → ℝ)
    (φ : (Fin 5 → ℝ) → ℝ) (hφ : Measurable φ) :
    ∫ x, φ (powers blockDim x) ∂(obsLaw blockDim (ofMean (CAS10C03.second H z0 m z1 t)) σ) =
      ∫ x, φ (powers blockDim x) ∂(obsLaw blockDim (ofMean (CAS10C03.first H z0 m z1 t)) σ) := by
  rw [← blockMap_rotP_first]
  exact powersOnly_integral_eq blockDim rotP rotP_orthogonal _ σ φ hφ

/-- A5b: the actual KL equals the C03 finite quadratic. -/
theorem full_kl_eq_C03 (H z0 m : ℝ) (z1 : Fin 3 → ℝ) (t : Fin 5 → ℝ) (σ : Fin 5 → ℝ)
    (hσ : ∀ j, 0 < σ j) :
    klDiv (obsLaw blockDim (ofMean (CAS10C03.first H z0 m z1 t)) σ)
        (obsLaw blockDim (ofMean (CAS10C03.second H z0 m z1 t)) σ) =
      ENNReal.ofReal (CAS10C03.KLQuadratic (σ 0) (σ 1) (σ 2) (σ 3) (σ 4)
        (CAS10C03.first H z0 m z1 t) (CAS10C03.second H z0 m z1 t)) := by
  rw [klDiv_obsLaw blockDim _ _ σ hσ, sum_Obs]
  congr 1
  simp only [ofMean, meanOf_0, meanOf_1, meanOf_2, meanOf_3, meanOf_4, CAS10C03.KLQuadratic,
    CAS10C03.weightedQuadratic, CAS10C03.sqNorm, CAS10C03.first, CAS10C03.second]
  simp only [sub_self, Fin.sum_univ_succ, Fin.sum_univ_zero]
  ring

/-- A5: the actual KL divergence of the full Gaussian experiments is `225 H²/(64 σ_p²)`. -/
theorem full_kl_eq (H z0 m : ℝ) (z1 : Fin 3 → ℝ) (t : Fin 5 → ℝ) (σ : Fin 5 → ℝ)
    (hσ : ∀ j, 0 < σ j) :
    klDiv (obsLaw blockDim (ofMean (CAS10C03.first H z0 m z1 t)) σ)
        (obsLaw blockDim (ofMean (CAS10C03.second H z0 m z1 t)) σ) =
      ENNReal.ofReal (225 * H ^ 2 / (64 * σ 3 ^ 2)) := by
  rw [full_kl_eq_C03 H z0 m z1 t σ hσ,
    CAS10C03.kl_formula H z0 m (σ 0) (σ 1) (σ 2) (σ 3) (σ 4) z1 t (hσ 0) (hσ 1) (hσ 2) (hσ 3)
      (hσ 4)]

/-- A6 -/
theorem full_kl_pos (H z0 m : ℝ) (z1 : Fin 3 → ℝ) (t : Fin 5 → ℝ) (σ : Fin 5 → ℝ)
    (hσ : ∀ j, 0 < σ j) (hH : H ≠ 0) :
    0 < klDiv (obsLaw blockDim (ofMean (CAS10C03.first H z0 m z1 t)) σ)
        (obsLaw blockDim (ofMean (CAS10C03.second H z0 m z1 t)) σ) := by
  rw [full_kl_eq H z0 m z1 t σ hσ, ENNReal.ofReal_pos]
  have := hσ 3
  have : 0 < H ^ 2 := by positivity
  positivity

/-- A6 (finiteness) -/
theorem full_kl_ne_top (H z0 m : ℝ) (z1 : Fin 3 → ℝ) (t : Fin 5 → ℝ) (σ : Fin 5 → ℝ)
    (hσ : ∀ j, 0 < σ j) :
    klDiv (obsLaw blockDim (ofMean (CAS10C03.first H z0 m z1 t)) σ)
        (obsLaw blockDim (ofMean (CAS10C03.second H z0 m z1 t)) σ) ≠ ∞ := by
  rw [full_kl_eq H z0 m z1 t σ hσ]
  exact ENNReal.ofReal_ne_top

/-- The first slope-dipole coordinate. -/
def pIdx : Idx blockDim := ⟨3, ⟨0, by decide⟩⟩

theorem ofMean_first_pIdx (H z0 m : ℝ) (z1 : Fin 3 → ℝ) (t : Fin 5 → ℝ) :
    ofMean (CAS10C03.first H z0 m z1 t) pIdx = 15 * H / 8 := rfl

theorem ofMean_second_pIdx (H z0 m : ℝ) (z1 : Fin 3 → ℝ) (t : Fin 5 → ℝ) :
    ofMean (CAS10C03.second H z0 m z1 t) pIdx = 0 := rfl

/-- A7: non-vacuity — the full laws differ, although the compressed laws coincide. -/
theorem full_laws_ne (H z0 m : ℝ) (z1 : Fin 3 → ℝ) (t : Fin 5 → ℝ) (σ : Fin 5 → ℝ)
    (hH : H ≠ 0) :
    obsLaw blockDim (ofMean (CAS10C03.first H z0 m z1 t)) σ ≠
      obsLaw blockDim (ofMean (CAS10C03.second H z0 m z1 t)) σ := by
  intro h
  have h2 := congrFun ((obsLaw_eq_iff blockDim _ _ σ).1 h) pIdx
  rw [ofMean_first_pIdx, ofMean_second_pIdx] at h2
  exact hH (by linarith)

/-- A8: singular slope covariance. The SPD formula is not used; the KL is `∞`
because absolute continuity fails. -/
theorem full_kl_singular_branch (H z0 m : ℝ) (z1 : Fin 3 → ℝ) (t : Fin 5 → ℝ)
    (σ : Fin 5 → ℝ) (hσ3 : σ 3 = 0) (hH : H ≠ 0) :
    klDiv (obsLaw blockDim (ofMean (CAS10C03.first H z0 m z1 t)) σ)
        (obsLaw blockDim (ofMean (CAS10C03.second H z0 m z1 t)) σ) = ∞ := by
  apply klDiv_of_not_ac
  intro hac
  have hv : coordVar blockDim σ pIdx = 0 := by
    apply NNReal.eq
    rw [coordVar_coe]
    show σ 3 ^ 2 = 0
    rw [hσ3]; norm_num
  set S : Set Obs := Function.eval pIdx ⁻¹' {15 * H / 8} with hS
  have hP := (measurePreserving_eval
    (fun i => gaussianReal (ofMean (CAS10C03.first H z0 m z1 t) i) (coordVar blockDim σ i))
    pIdx).measure_preimage (measurableSet_singleton (15 * H / 8)).nullMeasurableSet
  have hQ := (measurePreserving_eval
    (fun i => gaussianReal (ofMean (CAS10C03.second H z0 m z1 t) i) (coordVar blockDim σ i))
    pIdx).measure_preimage (measurableSet_singleton (15 * H / 8)).nullMeasurableSet
  simp only [hv, gaussianReal_zero_var, ofMean_first_pIdx, ofMean_second_pIdx] at hP hQ
  have hne : (0 : ℝ) ≠ 15 * H / 8 := by
    intro h; apply hH; linarith
  have h0 : (obsLaw blockDim (ofMean (CAS10C03.second H z0 m z1 t)) σ) S = 0 := by
    unfold obsLaw coordLaw
    rw [hQ, Measure.dirac_apply' _ (measurableSet_singleton _)]
    simp [Set.indicator, hne]
  have h1 := hac h0
  unfold obsLaw coordLaw at h1
  rw [hP, Measure.dirac_apply' _ (measurableSet_singleton _)] at h1
  simp at h1

/-! ### X1–X3: cross-checks with C01 -/

/-- X1 -/
theorem slope_vectors_agree (H : ℝ) :
    CAS10C01.p1 H = CAS10C03.p H ∧ CAS10C01.p2 H = CAS10C03.pPrime H := ⟨rfl, rfl⟩

/-- Explicit trace-free quadrupole coordinate (first element of an orthonormal basis). -/
noncomputable def tCoord (H : ℝ) : Fin 5 → ℝ := ![3 * √6 * H / 16, 0, 0, 0, 0]

noncomputable def explicitFirst (H : ℝ) : CAS10C03.Mean :=
  CAS10C03.first H (5 / 4) (7 * H / 4) ![3 / 4, 0, 0] (tCoord H)

noncomputable def explicitSecond (H : ℝ) : CAS10C03.Mean :=
  CAS10C03.second H (5 / 4) (7 * H / 4) ![3 / 4, 0, 0] (tCoord H)

/-- X2 -/
theorem powers_explicit_first (H : ℝ) :
    powers blockDim (ofMean (explicitFirst H)) =
      ![25 / 16, 9 / 16, 49 * H ^ 2 / 16, 225 * H ^ 2 / 64, 27 * H ^ 2 / 128] := by
  rw [powers_apply]
  simp only [ofMean, explicitFirst, CAS10C03.first, meanOf_0, meanOf_1, meanOf_2, meanOf_3,
    meanOf_4, tCoord, CAS10C03.p, Fin.sum_univ_succ, Fin.sum_univ_zero]
  have h6 : (√6 : ℝ) ^ 2 = 6 := Real.sq_sqrt (by norm_num)
  funext j
  fin_cases j <;> simp <;> nlinarith [h6]

/-- X2 -/
theorem powers_explicit_second (H : ℝ) :
    powers blockDim (ofMean (explicitSecond H)) =
      ![25 / 16, 9 / 16, 49 * H ^ 2 / 16, 225 * H ^ 2 / 64, 27 * H ^ 2 / 128] := by
  rw [powers_apply]
  simp only [ofMean, explicitSecond, CAS10C03.second, meanOf_0, meanOf_1, meanOf_2, meanOf_3,
    meanOf_4, tCoord, CAS10C03.pPrime, Fin.sum_univ_succ, Fin.sum_univ_zero]
  have h6 : (√6 : ℝ) ^ 2 = 6 := Real.sq_sqrt (by norm_num)
  funext j
  fin_cases j <;> simp <;> nlinarith [h6]

/-- X2: agreement with the C01 equal-powers tuple. -/
theorem powers_explicit_matches_C01 (H : ℝ) :
    (∀ j : Fin 4, powers blockDim (ofMean (explicitFirst H)) j.castSucc =
        (CAS10C01.expectedPowers H).1 j) ∧
      powers blockDim (ofMean (explicitFirst H)) 4 = (CAS10C01.expectedPowers H).2 := by
  rw [powers_explicit_first]
  refine ⟨fun j => ?_, ?_⟩
  · fin_cases j <;> simp [CAS10C01.expectedPowers]
  · simp [CAS10C01.expectedPowers]

/-- Unit trace-free symmetric element `diag(2,-1,-1)/√6`. -/
noncomputable def E1 : Matrix (Fin 3) (Fin 3) ℝ := (√6)⁻¹ • Matrix.diagonal ![2, -1, -1]

/-- X3 -/
theorem tDiag_eq_coord_E1 (H : ℝ) :
    Matrix.diagonal (CAS10C01.Tdiag H) = (3 * √6 * H / 16) • E1 := by
  have h6 : (√6 : ℝ) ≠ 0 := by positivity
  ext i j
  fin_cases i <;> fin_cases j <;>
    simp [E1, CAS10C01.Tdiag, Matrix.diagonal_apply] <;> field_simp <;> ring

theorem E1_symm : E1ᵀ = E1 := by
  simp [E1, Matrix.transpose_smul]

theorem E1_trace : E1.trace = 0 := by
  simp [E1, Matrix.trace, Fin.sum_univ_succ]
  ring

theorem E1_frobenius : ∑ i, ∑ j, E1 i j ^ 2 = 1 := by
  have h6 : (√6 : ℝ) ^ 2 = 6 := Real.sq_sqrt (by norm_num)
  have h6' : (√6 : ℝ) ≠ 0 := by positivity
  simp [E1, Fin.sum_univ_succ, Matrix.diagonal_apply, mul_pow, inv_pow, h6]
  norm_num

/-! ### N1: proof-route negative control (anisotropic noise) -/

/-- Anisotropic weights: variance 1 on the first slope coordinate only. -/
noncomputable def anisoW : Idx blockDim → ℝ≥0 := fun i => if i = pIdx then 1 else 0

/-- The second slope coordinate. -/
def pIdx1 : Idx blockDim := ⟨3, ⟨1, by decide⟩⟩

theorem blockMap_rotP_pIdx1 (x : Obs) : blockMap blockDim rotP x pIdx1 = x pIdx := by
  change (CAS10C03.R *ᵥ fun k : Fin 3 => x ⟨3, k⟩) 1 = x ⟨3, 0⟩
  simp [CAS10C03.R, Matrix.mulVec, dotProduct, Fin.sum_univ_succ]

/-- N1: without isotropy the rotation step fails (it does NOT assert that anisotropic
compressed laws differ). -/
theorem anisotropic_rotation_changes_law :
    ∃ (μ : Obs) (w : Idx blockDim → ℝ≥0),
      (coordLaw μ w).map (blockMap blockDim rotP) ≠ coordLaw (blockMap blockDim rotP μ) w := by
  refine ⟨0, anisoW, fun h => ?_⟩
  have hpi : (pIdx1 : Idx blockDim) ≠ pIdx := by decide
  have hL : ((coordLaw (0 : Obs) anisoW).map (blockMap blockDim rotP)).map (fun x => x pIdx1) =
      gaussianReal 0 1 := by
    rw [Measure.map_map (measurable_pi_apply _) (measurable_blockMap blockDim rotP)]
    have : (fun x : Obs => x pIdx1) ∘ blockMap blockDim rotP = fun x => x pIdx := by
      funext x; exact blockMap_rotP_pIdx1 x
    rw [this]
    unfold coordLaw
    rw [(measurePreserving_eval (fun i => gaussianReal ((0 : Obs) i) (anisoW i)) pIdx).map_eq]
    simp [anisoW]
  have hR : (coordLaw (blockMap blockDim rotP (0 : Obs)) anisoW).map (fun x => x pIdx1) =
      gaussianReal 0 0 := by
    unfold coordLaw
    rw [(measurePreserving_eval
      (fun i => gaussianReal (blockMap blockDim rotP (0 : Obs) i) (anisoW i)) pIdx1).map_eq]
    simp [anisoW, hpi, blockMap_zero]
  rw [h, hR] at hL
  have := (gaussianReal_ext_iff.1 hL).2
  exact zero_ne_one this

end Application

end G10BGaussianKL
