import Mathlib

noncomputable section
namespace CAS07C02

abbrev E := EuclideanSpace ℝ (Fin 2)
abbrev Mat := Matrix (Fin 2) (Fin 2) ℝ

def euclideanOpNorm (A : Mat) : ℝ :=
  ‖(Matrix.toEuclideanLin A).toContinuousLinearMap‖

theorem norm_error_le (A : Mat) (r : ℝ) (hr : euclideanOpNorm A ≤ r) (v : E) :
    ‖Matrix.toEuclideanLin A v‖ ≤ r * ‖v‖ := by
  have h := (Matrix.toEuclideanLin A).toContinuousLinearMap.le_opNorm v
  exact h.trans (mul_le_mul_of_nonneg_right hr (norm_nonneg v))

theorem norm_error_le_iff (A : Mat) (r : ℝ) (hr : 0 ≤ r) :
    euclideanOpNorm A ≤ r ↔ ∀ v : E, ‖Matrix.toEuclideanLin A v‖ ≤ r * ‖v‖ := by
  constructor
  · intro h v
    exact norm_error_le A r h v
  · intro h
    exact ContinuousLinearMap.opNorm_le_bound _ hr h

theorem matrix_action_add_scaled_identity (D : Mat) (s : ℝ) (v : E) :
    Matrix.toEuclideanLin D v = s • v + Matrix.toEuclideanLin (D - s • (1 : Mat)) v := by
  have hunit : Matrix.toEuclideanLin (1 : Mat) = (LinearMap.id : E →ₗ[ℝ] E) := by
    apply LinearMap.ext
    intro w
    simp [Matrix.toEuclideanLin_apply]
  have heq : D = s • (1 : Mat) + (D - s • (1 : Mat)) := by abel
  conv_lhs => rw [heq]
  simp [map_add, map_smul, hunit]

theorem vector_norm_bounds (D : Mat) (s eta : ℝ)
    (hs : 0 < s) (h : euclideanOpNorm (D - s • (1 : Mat)) ≤ s * eta) (v : E) :
    s * (1 - eta) * ‖v‖ ≤ ‖Matrix.toEuclideanLin D v‖ ∧
      ‖Matrix.toEuclideanLin D v‖ ≤ s * (1 + eta) * ‖v‖ := by
  have he := norm_error_le _ _ h v
  have hv := matrix_action_add_scaled_identity D s v
  have hsabs : |s| = s := abs_of_pos hs
  constructor
  · rw [hv]
    have ht := norm_sub_le (s • v + Matrix.toEuclideanLin (D - s • (1 : Mat)) v)
      (Matrix.toEuclideanLin (D - s • (1 : Mat)) v)
    simp only [add_sub_cancel_right] at ht
    rw [norm_smul, Real.norm_eq_abs, hsabs] at ht
    nlinarith [norm_nonneg v, norm_nonneg (s • v + Matrix.toEuclideanLin (D - s • (1 : Mat)) v)]
  · rw [hv]
    have ht := norm_add_le (s • v) (Matrix.toEuclideanLin (D - s • (1 : Mat)) v)
    rw [norm_smul, Real.norm_eq_abs, hsabs] at ht
    nlinarith [norm_nonneg v]

theorem singular_value_as_norm (D : Mat) (i : Fin 2) :
    (Matrix.toEuclideanLin D).singularValues i =
      ‖Matrix.toEuclideanLin D
        ((Matrix.toEuclideanLin D).isSymmetric_adjoint_comp_self.eigenvectorBasis
          (by simp) i)‖ := by
  let T := Matrix.toEuclideanLin D
  let G := T.adjoint ∘ₗ T
  let hG := T.isSymmetric_adjoint_comp_self
  let e := hG.eigenvectorBasis (by simp) i
  have he : ‖e‖ = 1 := by
    exact (hG.eigenvectorBasis (by simp)).norm_eq_one i
  have heig : G e = hG.eigenvalues (by simp) i • e := by
    exact hG.apply_eigenvectorBasis (by simp) i
  have hsq : ‖T e‖ ^ 2 = hG.eigenvalues (by simp) i := by
    have hgram : inner ℝ (T e) (T e) = inner ℝ e (G e) := by
      simpa [G] using (T.adjoint_inner_right e (T e)).symm
    rw [real_inner_self_eq_norm_sq, heig, real_inner_smul_right,
      real_inner_self_eq_norm_sq, he] at hgram
    norm_num at hgram ⊢
    exact hgram
  rw [T.singularValues_fin (by simp) i]
  rw [← hsq, Real.sqrt_sq (norm_nonneg _)]

theorem singular_value_bounds (D : Mat) (s eta : ℝ)
    (hs : 0 < s) (h : euclideanOpNorm (D - s • (1 : Mat)) ≤ s * eta)
    (i : Fin 2) :
    s * (1 - eta) ≤ (Matrix.toEuclideanLin D).singularValues i ∧
      (Matrix.toEuclideanLin D).singularValues i ≤ s * (1 + eta) := by
  let T := Matrix.toEuclideanLin D
  let e := T.isSymmetric_adjoint_comp_self.eigenvectorBasis (by simp) i
  have he : ‖e‖ = 1 :=
    (T.isSymmetric_adjoint_comp_self.eigenvectorBasis (by simp)).norm_eq_one i
  have hb := vector_norm_bounds D s eta hs h e
  rw [he, mul_one, mul_one] at hb
  simpa only [singular_value_as_norm] using hb

theorem inner_action_pos (D : Mat) (s eta : ℝ)
    (hs : 0 < s) (heta : eta < 1)
    (h : euclideanOpNorm (D - s • (1 : Mat)) ≤ s * eta)
    (v : E) (hv : v ≠ 0) :
    0 < inner ℝ v (Matrix.toEuclideanLin D v) := by
  let A := Matrix.toEuclideanLin (D - s • (1 : Mat))
  have hnorm : ‖A v‖ ≤ s * eta * ‖v‖ := norm_error_le _ _ h v
  have hcs := neg_le_of_abs_le (abs_real_inner_le_norm v (A v))
  have hmul := mul_le_mul_of_nonneg_left hnorm (norm_nonneg v)
  have hvpos : 0 < ‖v‖ := norm_pos_iff.mpr hv
  have hc : 0 < s * (1 - eta) := mul_pos hs (sub_pos.mpr heta)
  rw [matrix_action_add_scaled_identity D s v]
  rw [inner_add_right, real_inner_smul_right, real_inner_self_eq_norm_mul_norm]
  nlinarith [mul_pos hvpos hvpos]

theorem diagonal11_pos (D : Mat) (s eta : ℝ)
    (hs : 0 < s) (heta : eta < 1)
    (h : euclideanOpNorm (D - s • (1 : Mat)) ≤ s * eta) :
    0 < D 1 1 := by
  let v : E := WithLp.toLp 2 ![(0 : ℝ), 1]
  have hv : v ≠ 0 := by
    intro hzero
    have hz := congrArg (fun w : E => w.ofLp 1) hzero
    norm_num [v] at hz
  have hp := inner_action_pos D s eta hs heta h v hv
  simpa [v, EuclideanSpace.inner_eq_star_dotProduct, Matrix.toEuclideanLin_apply,
    Matrix.mulVec, dotProduct, Fin.sum_univ_two] using hp

theorem determinant_pos (D : Mat) (s eta : ℝ)
    (hs : 0 < s) (heta : eta < 1)
    (h : euclideanOpNorm (D - s • (1 : Mat)) ≤ s * eta) :
    0 < D.det := by
  have hd11 := diagonal11_pos D s eta hs heta h
  let v : E := WithLp.toLp 2 ![D 1 1, -(D 1 0)]
  have hv : v ≠ 0 := by
    intro hzero
    have hz := congrArg (fun w : E => w.ofLp 0) hzero
    simp [v] at hz
    exact (ne_of_gt hd11) hz
  have hp := inner_action_pos D s eta hs heta h v hv
  have hcalc : inner ℝ v (Matrix.toEuclideanLin D v) = D 1 1 * D.det := by
    simp [v, EuclideanSpace.inner_eq_star_dotProduct, Matrix.toEuclideanLin_apply,
      Matrix.mulVec, dotProduct, Fin.sum_univ_two, Matrix.det_fin_two]
    ring
  rw [hcalc] at hp
  exact (mul_pos_iff_of_pos_left hd11).mp hp

theorem determinant_square_eq_singular_product_square (D : Mat) :
    D.det ^ 2 =
      ((Matrix.toEuclideanLin D).singularValues 0) ^ 2 *
      ((Matrix.toEuclideanLin D).singularValues 1) ^ 2 := by
  let T := Matrix.toEuclideanLin D
  let G := T.adjoint ∘ₗ T
  let hG := T.isSymmetric_adjoint_comp_self
  have hdetT : T.det = D.det := by
    change LinearMap.det (Matrix.toEuclideanLin D) = D.det
    rw [Matrix.toEuclideanLin_eq_toLin_orthonormal]
    exact LinearMap.det_toLin (EuclideanSpace.basisFun (Fin 2) ℝ).toBasis D
  have hdetAdj : T.adjoint.det = D.det := by
    rw [← Matrix.toEuclideanLin_conjTranspose_eq_adjoint D]
    rw [Matrix.toEuclideanLin_eq_toLin_orthonormal]
    rw [LinearMap.det_toLin]
    simp
  have hdetG : G.det = D.det ^ 2 := by
    rw [show G = T.adjoint ∘ₗ T by rfl, LinearMap.det_comp, hdetAdj, hdetT]
    ring
  have hprod := hG.det_eq_prod_eigenvalues (n := 2) (by simp)
  rw [hdetG, Fin.prod_univ_two] at hprod
  have hsq0 := T.sq_singularValues_fin (n := 2) (by simp) (0 : Fin 2)
  have hsq1 := T.sq_singularValues_fin (n := 2) (by simp) (1 : Fin 2)
  rw [← hsq0, ← hsq1] at hprod
  exact hprod

theorem determinant_eq_singular_product (D : Mat) (s eta : ℝ)
    (hs : 0 < s) (heta : eta < 1)
    (h : euclideanOpNorm (D - s • (1 : Mat)) ≤ s * eta) :
    D.det = (Matrix.toEuclideanLin D).singularValues 0 *
      (Matrix.toEuclideanLin D).singularValues 1 := by
  have hd := determinant_pos D s eta hs heta h
  have hb0 := singular_value_bounds D s eta hs h (0 : Fin 2)
  have hb1 := singular_value_bounds D s eta hs h (1 : Fin 2)
  have hlow : 0 < s * (1 - eta) := mul_pos hs (sub_pos.mpr heta)
  have hp0 : 0 < (Matrix.toEuclideanLin D).singularValues 0 := lt_of_lt_of_le hlow hb0.1
  have hp1 : 0 < (Matrix.toEuclideanLin D).singularValues 1 := lt_of_lt_of_le hlow hb1.1
  apply (sq_eq_sq₀ (le_of_lt hd) (le_of_lt (mul_pos hp0 hp1))).mp
  rw [mul_pow]
  exact determinant_square_eq_singular_product_square D

theorem CAS_07_C02_full (D : Mat) (s eta : ℝ)
    (hs : 0 < s) (_heta_nonneg : 0 ≤ eta) (heta : eta < 1)
    (h : euclideanOpNorm (D - s • (1 : Mat)) ≤ s * eta) :
    (∀ i : Fin 2, s * (1 - eta) ≤ (Matrix.toEuclideanLin D).singularValues i ∧
      (Matrix.toEuclideanLin D).singularValues i ≤ s * (1 + eta)) ∧
    0 < D.det ∧
    s * (1 - eta) ≤ Real.sqrt D.det ∧
    Real.sqrt D.det ≤ s * (1 + eta) := by
  have hb : ∀ i : Fin 2, s * (1 - eta) ≤ (Matrix.toEuclideanLin D).singularValues i ∧
      (Matrix.toEuclideanLin D).singularValues i ≤ s * (1 + eta) :=
    singular_value_bounds D s eta hs h
  have hd := determinant_pos D s eta hs heta h
  have hprod := determinant_eq_singular_product D s eta hs heta h
  have hlo : 0 < s * (1 - eta) := mul_pos hs (sub_pos.mpr heta)
  have hhi : 0 ≤ s * (1 + eta) := by positivity
  have hp0 : 0 ≤ (Matrix.toEuclideanLin D).singularValues 0 := le_trans (le_of_lt hlo) (hb 0).1
  have hlo_sq : (s * (1 - eta)) ^ 2 ≤ D.det := by
    rw [hprod, pow_two]
    exact le_trans (mul_le_mul_of_nonneg_right (hb 0).1 (le_of_lt hlo))
      (mul_le_mul_of_nonneg_left (hb 1).1 hp0)
  have hhi_sq : D.det ≤ (s * (1 + eta)) ^ 2 := by
    rw [hprod, pow_two]
    exact le_trans (mul_le_mul_of_nonneg_right (hb 0).2
      (le_trans (le_of_lt hlo) (hb 1).1))
      (mul_le_mul_of_nonneg_left (hb 1).2 hhi)
  have hsqrt := Real.sq_sqrt (le_of_lt hd)
  have hsqrt_nonneg := Real.sqrt_nonneg D.det
  refine ⟨hb, hd, ?_, ?_⟩
  · nlinarith
  · nlinarith

#print axioms CAS_07_C02_full

end CAS07C02
