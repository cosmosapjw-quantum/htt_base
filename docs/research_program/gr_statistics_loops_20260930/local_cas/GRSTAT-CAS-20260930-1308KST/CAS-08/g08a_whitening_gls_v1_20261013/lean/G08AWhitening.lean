import Mathlib
import ProjectionBridge

/-!
G08-A (parent GR-CAS-08, contract C01/C02): whitening, Moore-Penrose
pseudoinverse, GLS residual projector and its spectrum, over real matrices
indexed by `Fin n` / `Fin k`.

Constructions (not assumptions):
* `whitening_exists` builds `W = Uᵀ diag(d^{-1/2}) U = C^{-1/2}` from an
  orthogonal eigen-decomposition `C = Uᵀ diag(d) U` (spectral theorem for the
  symmetric operator `toEuclideanLin C`).
* `moorePenrose_exists` builds `X = (AᵀA)⁺ Aᵀ` where `(AᵀA)⁺ = Vᵀ diag(d⁻¹) V`
  (with Lean's `0⁻¹ = 0`) from the eigen-decomposition of `AᵀA`; any rank,
  including `A = 0`.

No Gaussian law, chi-square law, coverage, four-way decision (G08-C) or
scientific admission is asserted here.
-/

noncomputable section

namespace G08AWhitening

open Matrix

variable {n k : ℕ}

/-! ### Orthogonal diagonalization of a real symmetric matrix -/

/-- Spectral theorem in matrix form with an explicit orthogonal `U` whose rows
are an orthonormal eigenbasis, eigenvalues sorted decreasingly. -/
theorem symm_diagonalize (S : Matrix (Fin n) (Fin n) ℝ) (hS : Sᵀ = S) :
    ∃ (U : Matrix (Fin n) (Fin n) ℝ) (d : Fin n → ℝ),
      U * Uᵀ = 1 ∧ Uᵀ * U = 1 ∧ S = Uᵀ * diagonal d * U ∧ Antitone d := by
  have hH : S.IsHermitian := by
    unfold IsHermitian
    rw [conjTranspose_eq_transpose_of_trivial, hS]
  have hT : (toEuclideanLin S).IsSymmetric := isSymmetric_toEuclideanLin_iff.mpr hH
  have hn : Module.finrank ℝ (EuclideanSpace ℝ (Fin n)) = n := finrank_euclideanSpace_fin
  let b := hT.eigenvectorBasis hn
  let d := hT.eigenvalues hn
  let U : Matrix (Fin n) (Fin n) ℝ := Matrix.of fun i j => WithLp.ofLp (b i) j
  have hUU : U * Uᵀ = 1 := by
    ext i j
    have h := orthonormal_iff_ite.mp b.orthonormal i j
    rw [EuclideanSpace.inner_eq_star_dotProduct] at h
    simp only [star_trivial] at h
    rw [mul_apply, one_apply, ← h]
    simp only [dotProduct]
    refine Finset.sum_congr rfl fun l _ => ?_
    simp only [U, of_apply, transpose_apply]
    ring
  have hUU' : Uᵀ * U = 1 := mul_eq_one_comm.mp hUU
  have heig : ∀ i, S *ᵥ WithLp.ofLp (b i) = d i • WithLp.ofLp (b i) := by
    intro i
    have h := congrArg WithLp.ofLp (hT.apply_eigenvectorBasis hn i)
    simp only [toLpLin_apply, WithLp.ofLp_toLp, WithLp.ofLp_smul, RCLike.ofReal_real_eq_id,
      id] at h
    exact h
  have hSU : S * Uᵀ = Uᵀ * diagonal d := by
    ext x i
    rw [mul_diagonal, transpose_apply]
    have h := congrFun (heig i) x
    simp only [mulVec, dotProduct, Pi.smul_apply, smul_eq_mul] at h
    rw [mul_apply]
    simp only [U, transpose_apply, of_apply]
    rw [h, mul_comm]
  refine ⟨U, d, hUU, hUU', ?_, hT.eigenvalues_antitone hn⟩
  calc S = S * (Uᵀ * U) := by rw [hUU', Matrix.mul_one]
    _ = (S * Uᵀ) * U := by rw [Matrix.mul_assoc]
    _ = Uᵀ * diagonal d * U := by rw [hSU]

/-- Products of matrices diagonal in the same orthogonal frame. -/
theorem conj_diag_mul (U : Matrix (Fin n) (Fin n) ℝ) (hU : U * Uᵀ = 1) (a b : Fin n → ℝ) :
    (Uᵀ * diagonal a * U) * (Uᵀ * diagonal b * U) =
      Uᵀ * diagonal (fun i => a i * b i) * U := by
  calc (Uᵀ * diagonal a * U) * (Uᵀ * diagonal b * U)
      = Uᵀ * diagonal a * (U * Uᵀ) * diagonal b * U := by simp only [Matrix.mul_assoc]
    _ = Uᵀ * (diagonal a * diagonal b) * U := by
        rw [hU, Matrix.mul_one, Matrix.mul_assoc Uᵀ (diagonal a)]
    _ = Uᵀ * diagonal (fun i => a i * b i) * U := by rw [diagonal_mul_diagonal]

theorem conj_diag_transpose (U : Matrix (Fin n) (Fin n) ℝ) (a : Fin n → ℝ) :
    (Uᵀ * diagonal a * U)ᵀ = Uᵀ * diagonal a * U := by
  simp only [transpose_mul, transpose_transpose, diagonal_transpose, Matrix.mul_assoc]

/-! ### Target 1: whitening -/

theorem whitening_exists (C : Matrix (Fin n) (Fin n) ℝ) (hC : C.PosDef) :
    ∃ W : Matrix (Fin n) (Fin n) ℝ, IsUnit W ∧ W * C * Wᵀ = 1 := by
  have hCt : Cᵀ = C := by
    have h := hC.isHermitian
    unfold IsHermitian at h
    rwa [conjTranspose_eq_transpose_of_trivial] at h
  obtain ⟨U, d, hUU, hUU', hCU, -⟩ := symm_diagonalize C hCt
  -- eigenvalues are positive: d i = (U C Uᵀ) i i = (row i) ⬝ C (row i) > 0
  have hD : U * C * Uᵀ = diagonal d := by
    rw [hCU]
    calc U * (Uᵀ * diagonal d * U) * Uᵀ = (U * Uᵀ) * diagonal d * (U * Uᵀ) := by
          simp only [Matrix.mul_assoc]
      _ = diagonal d := by rw [hUU, Matrix.one_mul, Matrix.mul_one]
  have hpos : ∀ i, 0 < d i := by
    intro i
    have hrow : U i ≠ 0 := by
      intro h0
      have h1 := congrFun (congrFun hUU i) i
      rw [mul_apply, one_apply_eq] at h1
      simp [transpose_apply, h0] at h1
    have h2 := hC.dotProduct_mulVec_pos hrow
    simp only [star_trivial] at h2
    have h3 : (U * C * Uᵀ) i i = U i ⬝ᵥ (C *ᵥ U i) := by
      rw [dotProduct_mulVec]
      rfl
    rw [hD, diagonal_apply_eq] at h3
    rw [h3]
    exact h2
  let s : Fin n → ℝ := fun i => (Real.sqrt (d i))⁻¹
  let r : Fin n → ℝ := fun i => Real.sqrt (d i)
  refine ⟨Uᵀ * diagonal s * U, ?_, ?_⟩
  · have h1 : (Uᵀ * diagonal s * U) * (Uᵀ * diagonal r * U) = 1 := by
      rw [conj_diag_mul U hUU]
      have : (fun i => s i * r i) = fun _ => (1 : ℝ) := by
        funext i
        have hs : Real.sqrt (d i) ≠ 0 := (Real.sqrt_pos.mpr (hpos i)).ne'
        simp only [s, r]
        exact inv_mul_cancel₀ hs
      rw [this, diagonal_one, Matrix.mul_one, hUU']
    exact ⟨⟨_, _, h1, mul_eq_one_comm.mp h1⟩, rfl⟩
  · rw [conj_diag_transpose, hCU, conj_diag_mul U hUU, conj_diag_mul U hUU]
    have : (fun i => s i * d i * s i) = fun _ => (1 : ℝ) := by
      funext i
      have hd := hpos i
      have hs : Real.sqrt (d i) ≠ 0 := (Real.sqrt_pos.mpr hd).ne'
      have hsq : Real.sqrt (d i) * Real.sqrt (d i) = d i := Real.mul_self_sqrt hd.le
      simp only [s]
      calc (Real.sqrt (d i))⁻¹ * d i * (Real.sqrt (d i))⁻¹
          = d i / (Real.sqrt (d i) * Real.sqrt (d i)) := by ring
        _ = 1 := by rw [hsq, div_self hd.ne']
    rw [this, diagonal_one, Matrix.mul_one, hUU']

/-! ### Target 2: Moore-Penrose conditions -/

/-- The four Penrose conditions (real case: transpose = adjoint). -/
def IsMoorePenrose (A : Matrix (Fin n) (Fin k) ℝ) (X : Matrix (Fin k) (Fin n) ℝ) : Prop :=
  A * X * A = A ∧ X * A * X = X ∧ (A * X)ᵀ = A * X ∧ (X * A)ᵀ = X * A

/-! ### Target 3: existence -/

/-- Diagonal-frame pseudoinverse of a symmetric matrix. -/
theorem symm_pinv_exists (M : Matrix (Fin k) (Fin k) ℝ) (hM : Mᵀ = M) :
    ∃ Mp : Matrix (Fin k) (Fin k) ℝ,
      M * Mp * M = M ∧ Mp * M * Mp = Mp ∧ Mpᵀ = Mp ∧ M * Mp = Mp * M := by
  obtain ⟨V, d, hVV, -, hMV, -⟩ := symm_diagonalize M hM
  refine ⟨Vᵀ * diagonal (fun i => (d i)⁻¹) * V, ?_, ?_, ?_, ?_⟩
  · rw [hMV, conj_diag_mul V hVV, conj_diag_mul V hVV]
    congr 3
    funext i
    by_cases h : d i = 0
    · simp [h]
    · field_simp
  · rw [hMV, conj_diag_mul V hVV, conj_diag_mul V hVV]
    congr 3
    funext i
    by_cases h : d i = 0
    · simp [h]
    · field_simp
  · exact conj_diag_transpose V _
  · rw [hMV, conj_diag_mul V hVV, conj_diag_mul V hVV]
    congr 3
    funext i
    ring

theorem moorePenrose_exists (A : Matrix (Fin n) (Fin k) ℝ) :
    ∃ X : Matrix (Fin k) (Fin n) ℝ, IsMoorePenrose A X := by
  have hMt : (Aᵀ * A)ᵀ = Aᵀ * A := by rw [transpose_mul, transpose_transpose]
  obtain ⟨Mp, h1, h2, h3, h4⟩ := symm_pinv_exists (Aᵀ * A) hMt
  -- A * (1 - Mp * (Aᵀ A)) = 0 since its Gram matrix vanishes
  have hAQ : A * (Mp * (Aᵀ * A)) = A := by
    have hMQ : (Aᵀ * A) * (1 - Mp * (Aᵀ * A)) = 0 := by
      rw [Matrix.mul_sub, Matrix.mul_one, ← Matrix.mul_assoc, h1, sub_self]
    have hG : (A * (1 - Mp * (Aᵀ * A)))ᴴ * (A * (1 - Mp * (Aᵀ * A))) = 0 := by
      rw [conjTranspose_eq_transpose_of_trivial, transpose_mul]
      calc (1 - Mp * (Aᵀ * A))ᵀ * Aᵀ * (A * (1 - Mp * (Aᵀ * A)))
          = (1 - Mp * (Aᵀ * A))ᵀ * ((Aᵀ * A) * (1 - Mp * (Aᵀ * A))) := by
            simp only [Matrix.mul_assoc]
        _ = 0 := by rw [hMQ, Matrix.mul_zero]
    have h0 := conjTranspose_mul_self_eq_zero.mp hG
    rw [Matrix.mul_sub, Matrix.mul_one, sub_eq_zero] at h0
    exact h0.symm
  refine ⟨Mp * Aᵀ, ?_, ?_, ?_, ?_⟩
  · calc A * (Mp * Aᵀ) * A = A * (Mp * (Aᵀ * A)) := by simp only [Matrix.mul_assoc]
      _ = A := hAQ
  · calc Mp * Aᵀ * A * (Mp * Aᵀ) = (Mp * (Aᵀ * A) * Mp) * Aᵀ := by
          simp only [Matrix.mul_assoc]
      _ = Mp * Aᵀ := by rw [h2]
  · calc (A * (Mp * Aᵀ))ᵀ = A * (Mpᵀ * Aᵀ) := by
          simp only [transpose_mul, transpose_transpose, Matrix.mul_assoc]
      _ = A * (Mp * Aᵀ) := by rw [h3]
  · calc (Mp * Aᵀ * A)ᵀ = (Mp * (Aᵀ * A))ᵀ := by rw [Matrix.mul_assoc]
      _ = (Aᵀ * A) * Mp := by rw [transpose_mul, hMt, h3]
      _ = Mp * (Aᵀ * A) := h4
      _ = Mp * Aᵀ * A := by rw [Matrix.mul_assoc]

/-! ### Target 4: uniqueness -/

theorem moorePenrose_unique (A : Matrix (Fin n) (Fin k) ℝ) (X Y : Matrix (Fin k) (Fin n) ℝ)
    (hX : IsMoorePenrose A X) (hY : IsMoorePenrose A Y) : X = Y := by
  obtain ⟨h1, h2, h3, h4⟩ := hX
  obtain ⟨g1, g2, g3, g4⟩ := hY
  have eX : X = X * A * Y :=
    calc X = X * A * X := h2.symm
      _ = X * (A * X)ᵀ := by rw [h3, Matrix.mul_assoc]
      _ = X * (Xᵀ * Aᵀ) := by rw [transpose_mul]
      _ = X * (Xᵀ * (A * Y * A)ᵀ) := by rw [g1]
      _ = X * ((A * X)ᵀ * (A * Y)ᵀ) := by simp only [transpose_mul, Matrix.mul_assoc]
      _ = X * (A * X * (A * Y)) := by rw [h3, g3]
      _ = X * A * X * A * Y := by simp only [Matrix.mul_assoc]
      _ = X * A * Y := by rw [h2]
  have eY : Y = X * A * Y :=
    calc Y = Y * A * Y := g2.symm
      _ = (Y * A)ᵀ * Y := by rw [g4]
      _ = Aᵀ * Yᵀ * Y := by rw [transpose_mul]
      _ = (A * X * A)ᵀ * Yᵀ * Y := by rw [h1]
      _ = (X * A)ᵀ * (Y * A)ᵀ * Y := by simp only [transpose_mul, Matrix.mul_assoc]
      _ = X * A * (Y * A) * Y := by rw [h4, g4]
      _ = X * A * (Y * A * Y) := by simp only [Matrix.mul_assoc]
      _ = X * A * Y := by rw [g2]
  rw [eX, ← eY]

/-! ### Residual algebra used by targets 5-9 -/

theorem transpose_mul_residual (A : Matrix (Fin n) (Fin k) ℝ) (X : Matrix (Fin k) (Fin n) ℝ)
    (hX : IsMoorePenrose A X) : Aᵀ * (1 - A * X) = 0 := by
  rw [Matrix.mul_sub, Matrix.mul_one, ← hX.2.2.1, ← transpose_mul, hX.1, sub_self]

theorem residual_orthogonal (A : Matrix (Fin n) (Fin k) ℝ) (X : Matrix (Fin k) (Fin n) ℝ)
    (hX : IsMoorePenrose A X) (v : Fin n → ℝ) (w : Fin k → ℝ) :
    ((1 - A * X) *ᵥ v) ⬝ᵥ (A *ᵥ w) = 0 := by
  rw [dotProduct_mulVec, ← mulVec_transpose, mulVec_mulVec, transpose_mul_residual A X hX,
    zero_mulVec, zero_dotProduct]

theorem fit_idempotent (A : Matrix (Fin n) (Fin k) ℝ) (X : Matrix (Fin k) (Fin n) ℝ)
    (hX : IsMoorePenrose A X) : (A * X) * (A * X) = A * X := by
  rw [← Matrix.mul_assoc, hX.1]

theorem residual_transpose (A : Matrix (Fin n) (Fin k) ℝ) (X : Matrix (Fin k) (Fin n) ℝ)
    (hX : IsMoorePenrose A X) : (1 - A * X)ᵀ = 1 - A * X := by
  rw [transpose_sub, transpose_one, hX.2.2.1]

theorem residual_idempotent (A : Matrix (Fin n) (Fin k) ℝ) (X : Matrix (Fin k) (Fin n) ℝ)
    (hX : IsMoorePenrose A X) : (1 - A * X) * (1 - A * X) = 1 - A * X := by
  rw [sub_mul, Matrix.mul_sub, Matrix.mul_sub, Matrix.one_mul, Matrix.mul_one, Matrix.one_mul,
    fit_idempotent A X hX, sub_self, sub_zero]

/-! ### Target 5: the matrix residual operator is the bridge projector -/

theorem residualProjector_eq (A : Matrix (Fin n) (Fin k) ℝ) (X : Matrix (Fin k) (Fin n) ℝ)
    (hX : IsMoorePenrose A X) :
    Matrix.toEuclideanLin (1 - A * X) =
      ((CAS08ProjectionBridge.P (LinearMap.toContinuousLinearMap (Matrix.toEuclideanLin A)) :
        EuclideanSpace ℝ (Fin n) →L[ℝ] EuclideanSpace ℝ (Fin n)) :
        EuclideanSpace ℝ (Fin n) →ₗ[ℝ] EuclideanSpace ℝ (Fin n)) := by
  set L : EuclideanSpace ℝ (Fin k) →L[ℝ] EuclideanSpace ℝ (Fin n) :=
    LinearMap.toContinuousLinearMap (Matrix.toEuclideanLin A) with hL
  apply LinearMap.ext
  intro x
  rw [ContinuousLinearMap.coe_coe, CAS08ProjectionBridge.residual_identity]
  have hproj : (CAS08ProjectionBridge.responseRange L).starProjection x =
      WithLp.toLp 2 ((A * X) *ᵥ WithLp.ofLp x) := by
    apply Submodule.eq_starProjection_of_mem_of_inner_eq_zero
    · refine ⟨WithLp.toLp 2 (X *ᵥ WithLp.ofLp x), ?_⟩
      simp only [hL, ContinuousLinearMap.coe_coe, LinearMap.coe_toContinuousLinearMap',
        toLpLin_apply, mulVec_mulVec]
    · rintro w ⟨z, rfl⟩
      rw [EuclideanSpace.inner_eq_star_dotProduct]
      simp only [hL, ContinuousLinearMap.coe_coe, LinearMap.coe_toContinuousLinearMap',
        toLpLin_apply, WithLp.ofLp_toLp, WithLp.ofLp_sub, star_trivial]
      rw [dotProduct_comm]
      have := residual_orthogonal A X hX (WithLp.ofLp x) (WithLp.ofLp z)
      rwa [sub_mulVec, one_mulVec] at this
  rw [hproj]
  apply WithLp.ofLp_injective
  simp only [toLpLin_apply, WithLp.ofLp_toLp, WithLp.ofLp_sub, sub_mulVec, one_mulVec]

/-! ### Target 6: GLS quadratic form equals whitened Euclidean norm -/

theorem gls_quadratic_eq (C W : Matrix (Fin n) (Fin n) ℝ) (F : Matrix (Fin n) (Fin k) ℝ)
    (hC : C.PosDef) (hW : IsUnit W ∧ W * C * Wᵀ = 1) (y : Fin n → ℝ) (θ : Fin k → ℝ) :
    (y - F *ᵥ θ) ⬝ᵥ (C⁻¹ *ᵥ (y - F *ᵥ θ)) =
      (W *ᵥ (y - F *ᵥ θ)) ⬝ᵥ (W *ᵥ (y - F *ᵥ θ)) := by
  have h1 : Wᵀ * (W * C) = 1 := mul_eq_one_comm.mp hW.2
  have hinv : C⁻¹ = Wᵀ * W := inv_eq_left_inv (by rw [Matrix.mul_assoc]; exact h1)
  rw [hinv, ← mulVec_mulVec, dotProduct_mulVec, vecMul_transpose]

/-! ### Target 7: exact GLS residual minimization -/

theorem gls_minimum (C W : Matrix (Fin n) (Fin n) ℝ) (F : Matrix (Fin n) (Fin k) ℝ)
    (X : Matrix (Fin k) (Fin n) ℝ) (y : Fin n → ℝ)
    (hC : C.PosDef) (hW : IsUnit W ∧ W * C * Wᵀ = 1) (hX : IsMoorePenrose (W * F) X) :
    (∀ θ : Fin k → ℝ,
        ((1 - W * F * X) *ᵥ (W *ᵥ y)) ⬝ᵥ ((1 - W * F * X) *ᵥ (W *ᵥ y)) ≤
          (y - F *ᵥ θ) ⬝ᵥ (C⁻¹ *ᵥ (y - F *ᵥ θ))) ∧
      (∃ θ : Fin k → ℝ, (y - F *ᵥ θ) ⬝ᵥ (C⁻¹ *ᵥ (y - F *ᵥ θ)) =
        ((1 - W * F * X) *ᵥ (W *ᵥ y)) ⬝ᵥ ((1 - W * F * X) *ᵥ (W *ᵥ y))) := by
  set A := W * F with hA
  set z := W *ᵥ y with hz
  set r := (1 - A * X) *ᵥ z with hr
  have hWres : ∀ θ, W *ᵥ (y - F *ᵥ θ) = z - A *ᵥ θ := by
    intro θ
    rw [mulVec_sub, mulVec_mulVec]
  have hsplit : ∀ θ, z - A *ᵥ θ = r + A *ᵥ (X *ᵥ z - θ) := by
    intro θ
    rw [hr, sub_mulVec, one_mulVec, mulVec_sub, mulVec_mulVec z A X]
    abel
  have hQ : ∀ θ, (y - F *ᵥ θ) ⬝ᵥ (C⁻¹ *ᵥ (y - F *ᵥ θ)) =
      r ⬝ᵥ r + (A *ᵥ (X *ᵥ z - θ)) ⬝ᵥ (A *ᵥ (X *ᵥ z - θ)) := by
    intro θ
    rw [gls_quadratic_eq C W F hC hW y θ, hWres, hsplit, add_dotProduct, dotProduct_add,
      dotProduct_add]
    have h0 : r ⬝ᵥ (A *ᵥ (X *ᵥ z - θ)) = 0 := residual_orthogonal A X hX z _
    rw [h0, dotProduct_comm (A *ᵥ (X *ᵥ z - θ)) r, h0]
    ring
  refine ⟨fun θ => ?_, ⟨X *ᵥ z, ?_⟩⟩
  · rw [hQ]
    have : 0 ≤ (A *ᵥ (X *ᵥ z - θ)) ⬝ᵥ (A *ᵥ (X *ᵥ z - θ)) := by
      simp only [dotProduct]
      exact Finset.sum_nonneg fun i _ => mul_self_nonneg _
    linarith
  · rw [hQ, sub_self, mulVec_zero, dotProduct_zero, add_zero]

/-! ### Target 8: whitened projected covariance is the projector -/

theorem projected_covariance (C W : Matrix (Fin n) (Fin n) ℝ) (F : Matrix (Fin n) (Fin k) ℝ)
    (X : Matrix (Fin k) (Fin n) ℝ) (hW : IsUnit W ∧ W * C * Wᵀ = 1)
    (hX : IsMoorePenrose (W * F) X) :
    (1 - W * F * X) * (W * C * Wᵀ) * (1 - W * F * X)ᵀ = 1 - W * F * X := by
  rw [hW.2, Matrix.mul_one, residual_transpose _ X hX, residual_idempotent _ X hX]

/-! ### Target 9: spectrum of the residual projector -/

theorem orthogonal_det_isUnit (U : Matrix (Fin n) (Fin n) ℝ) (hU : U * Uᵀ = 1) :
    IsUnit U.det ∧ IsUnit Uᵀ.det := by
  have h := congrArg det hU
  rw [det_mul, det_one] at h
  exact ⟨IsUnit.of_mul_eq_one _ h, IsUnit.of_mul_eq_one_right _ h⟩

theorem rank_conj_diag (U : Matrix (Fin n) (Fin n) ℝ) (hU : U * Uᵀ = 1) (a : Fin n → ℝ) :
    (Uᵀ * diagonal a * U).rank = (Finset.univ.filter (fun i => a i ≠ 0)).card := by
  obtain ⟨h1, h2⟩ := orthogonal_det_isUnit U hU
  rw [rank_mul_eq_left_of_isUnit_det U _ h1, rank_mul_eq_right_of_isUnit_det Uᵀ _ h2,
    rank_diagonal, Fintype.card_subtype]

/-- Spectral normal form of a real symmetric idempotent matrix: `m` ones then zeros,
with `m = rank P` and `n - m = rank (1 - P)`. -/
theorem symm_idempotent_spectrum (P : Matrix (Fin n) (Fin n) ℝ) (hPt : Pᵀ = P)
    (hPP : P * P = P) :
    ∃ (U : Matrix (Fin n) (Fin n) ℝ) (m : ℕ), U * Uᵀ = 1 ∧ Uᵀ * U = 1 ∧
      P = Uᵀ * diagonal (fun i : Fin n => if (i : ℕ) < m then (1 : ℝ) else 0) * U ∧
      m ≤ n ∧ (1 - P).rank = n - m := by
  obtain ⟨U, d, hUU, hUU', hPU, hanti⟩ := symm_diagonalize P hPt
  have hD : U * P * Uᵀ = diagonal d := by
    rw [hPU]
    calc U * (Uᵀ * diagonal d * U) * Uᵀ = (U * Uᵀ) * diagonal d * (U * Uᵀ) := by
          simp only [Matrix.mul_assoc]
      _ = diagonal d := by rw [hUU, Matrix.one_mul, Matrix.mul_one]
  have hdd : ∀ i, d i * d i = d i := by
    have hdiag : diagonal (fun i => d i * d i) = diagonal d :=
      calc diagonal (fun i => d i * d i) = diagonal d * diagonal d :=
            (diagonal_mul_diagonal _ _).symm
        _ = (U * P * Uᵀ) * (U * P * Uᵀ) := by rw [hD]
        _ = U * P * (Uᵀ * U) * P * Uᵀ := by simp only [Matrix.mul_assoc]
        _ = U * (P * P) * Uᵀ := by rw [hUU', Matrix.mul_one, Matrix.mul_assoc U P P]
        _ = diagonal d := by rw [hPP, hD]
    intro i
    have h := congrFun (congrFun hdiag i) i
    simpa only [diagonal_apply_eq] using h
  have h01 : ∀ i, d i = 0 ∨ d i = 1 := by
    intro i
    have h : d i * (d i - 1) = 0 := by linear_combination hdd i
    rcases mul_eq_zero.mp h with h | h
    · exact Or.inl h
    · exact Or.inr (by linarith)
  obtain ⟨m, hm⟩ : ∃ m, (Finset.univ.filter (fun j : Fin n => d j = 1)).card = m := ⟨_, rfl⟩
  have hform : ∀ i : Fin n, d i = if (i : ℕ) < m then 1 else 0 := by
    intro i
    rcases h01 i with h | h
    · rw [if_neg, h]
      intro hi
      have hsub : Finset.univ.filter (fun j : Fin n => d j = 1) ⊆ Finset.Iio i := by
        intro j hj
        rw [Finset.mem_filter] at hj
        rw [Finset.mem_Iio]
        by_contra hji
        have hle := hanti (not_lt.mp hji)
        linarith [hj.2]
      have hc := Finset.card_le_card hsub
      rw [hm, Fin.card_Iio] at hc
      omega
    · rw [if_pos, h]
      have hsub : Finset.Iic i ⊆ Finset.univ.filter (fun j : Fin n => d j = 1) := by
        intro j hj
        rw [Finset.mem_Iic] at hj
        rw [Finset.mem_filter]
        refine ⟨Finset.mem_univ _, ?_⟩
        have hle := hanti hj
        rcases h01 j with h' | h'
        · linarith
        · exact h'
      have hc := Finset.card_le_card hsub
      rw [hm, Fin.card_Iic] at hc
      omega
  have hmn : m ≤ n := by
    rw [← hm]
    calc (Finset.univ.filter (fun j : Fin n => d j = 1)).card ≤ (Finset.univ : Finset (Fin n)).card :=
          Finset.card_filter_le _ _
      _ = n := by rw [Finset.card_univ, Fintype.card_fin]
  have hcompl : 1 - P = Uᵀ * diagonal (fun i => 1 - d i) * U := by
    calc 1 - P = Uᵀ * diagonal (fun _ => (1 : ℝ)) * U - Uᵀ * diagonal d * U := by
          rw [diagonal_one, Matrix.mul_one, hUU', ← hPU]
      _ = Uᵀ * (diagonal (fun _ => (1 : ℝ)) - diagonal d) * U := by
          rw [Matrix.mul_sub, Matrix.sub_mul]
      _ = Uᵀ * diagonal (fun i => 1 - d i) * U := by rw [diagonal_sub]
  refine ⟨U, m, hUU, hUU', ?_, hmn, ?_⟩
  · rw [hPU, show d = (fun i : Fin n => if (i : ℕ) < m then (1 : ℝ) else 0) from funext hform]
  · rw [hcompl, rank_conj_diag U hUU]
    have hfil : Finset.univ.filter (fun i : Fin n => 1 - d i ≠ 0) =
        Finset.univ.filter (fun i : Fin n => ¬ d i = 1) := by
      apply Finset.filter_congr
      intro i _
      constructor
      · intro h h1
        exact h (by rw [h1]; ring)
      · intro h h1
        exact h (by linarith)
    have hsum := Finset.card_filter_add_card_filter_not (s := (Finset.univ : Finset (Fin n)))
      (fun j : Fin n => d j = 1)
    rw [hm, Finset.card_univ, Fintype.card_fin] at hsum
    rw [hfil]
    omega

theorem projector_spectrum (A : Matrix (Fin n) (Fin k) ℝ) (X : Matrix (Fin k) (Fin n) ℝ)
    (hX : IsMoorePenrose A X) :
    ∃ U : Matrix (Fin n) (Fin n) ℝ, U * Uᵀ = 1 ∧ Uᵀ * U = 1 ∧
      (1 - A * X) = Uᵀ * Matrix.diagonal
        (fun i : Fin n => if (i : ℕ) < n - A.rank then (1 : ℝ) else 0) * U := by
  obtain ⟨U, m, hUU, hUU', hP, hmn, hrank⟩ :=
    symm_idempotent_spectrum (1 - A * X) (residual_transpose A X hX) (residual_idempotent A X hX)
  have hAX : (A * X).rank = A.rank := by
    apply le_antisymm (rank_mul_le_left A X)
    calc A.rank = (A * X * A).rank := by rw [hX.1]
      _ ≤ (A * X).rank := rank_mul_le_left _ _
  rw [sub_sub_cancel, hAX] at hrank
  have hm : n - A.rank = m := by omega
  exact ⟨U, hUU, hUU', by rw [hm]; exact hP⟩

/-! ### Target 10: branch corollaries -/

theorem rank_zero_branch (A : Matrix (Fin n) (Fin k) ℝ) (X : Matrix (Fin k) (Fin n) ℝ)
    (hA : A = 0) : 1 - A * X = 1 := by
  rw [hA, Matrix.zero_mul, sub_zero]

theorem full_row_rank_branch (A : Matrix (Fin n) (Fin k) ℝ) (X : Matrix (Fin k) (Fin n) ℝ)
    (hX : IsMoorePenrose A X) (hA : A.rank = n) : 1 - A * X = 0 := by
  obtain ⟨U, -, -, hP⟩ := projector_spectrum A X hX
  rw [hP, hA, Nat.sub_self]
  simp

end G08AWhitening
