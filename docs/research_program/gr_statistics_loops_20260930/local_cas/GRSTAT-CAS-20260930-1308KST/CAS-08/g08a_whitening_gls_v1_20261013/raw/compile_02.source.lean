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
    rw [mul_apply, one_apply, ← h, dotProduct, dotProduct]
    refine Finset.sum_congr rfl fun l _ => ?_
    simp only [U, of_apply, transpose_apply]
    ring
  have hUU' : Uᵀ * U = 1 := mul_eq_one_comm.mp hUU
  have heig : ∀ i, S *ᵥ WithLp.ofLp (b i) = d i • WithLp.ofLp (b i) := by
    intro i
    have h := congrArg WithLp.ofLp (hT.apply_eigenvectorBasis hn i)
    simpa [toLpLin_apply] using h
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

end G08AWhitening
