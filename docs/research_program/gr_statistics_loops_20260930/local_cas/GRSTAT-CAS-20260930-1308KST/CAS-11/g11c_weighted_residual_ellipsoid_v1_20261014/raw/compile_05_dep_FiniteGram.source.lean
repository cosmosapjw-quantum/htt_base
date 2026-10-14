import Mathlib

/-!
CAS11-C02 finite Gram forward implication. `spectralPinvVec` inverts every
nonzero eigenvalue and leaves zero eigenvalues zero, including singular and
zero operators. The matrix corollary below is the contracted target.
-/

namespace CAS11C02

open Matrix

noncomputable def spectralPinvVec {E : Type*} [NormedAddCommGroup E]
    [InnerProductSpace ℝ E] [FiniteDimensional ℝ E]
    {T : E →ₗ[ℝ] E} (hT : T.IsSymmetric) (e : E) : E :=
  let b := hT.eigenvectorBasis (rfl : Module.finrank ℝ E = Module.finrank ℝ E)
  let ev := hT.eigenvalues (rfl : Module.finrank ℝ E = Module.finrank ℝ E)
  b.repr.symm (WithLp.toLp 2 fun i => (ev i)⁻¹ * (b.repr e i))

noncomputable def spectralPinvLin {E : Type*} [NormedAddCommGroup E]
    [InnerProductSpace ℝ E] [FiniteDimensional ℝ E]
    {T : E →ₗ[ℝ] E} (hT : T.IsSymmetric) : E →ₗ[ℝ] E :=
  let b := hT.eigenvectorBasis (rfl : Module.finrank ℝ E = Module.finrank ℝ E)
  let ev := hT.eigenvalues (rfl : Module.finrank ℝ E = Module.finrank ℝ E)
  b.repr.symm.toLinearMap ∘ₗ
    (Matrix.diagonal (fun i => (ev i)⁻¹)).toEuclideanLin ∘ₗ
      b.repr.toLinearMap

theorem spectralPinvLin_apply {E : Type*} [NormedAddCommGroup E]
    [InnerProductSpace ℝ E] [FiniteDimensional ℝ E]
    {T : E →ₗ[ℝ] E} (hT : T.IsSymmetric) (e : E) :
    spectralPinvLin hT e = spectralPinvVec hT e := by
  simp [spectralPinvLin, spectralPinvVec, Matrix.toEuclideanLin_apply]
  funext i
  exact Matrix.mulVec_diagonal _ _ i

theorem finiteGramForwardAbstract {E : Type*} [NormedAddCommGroup E]
    [InnerProductSpace ℝ E] [FiniteDimensional ℝ E]
    {T : E →ₗ[ℝ] E} (hT : T.IsSymmetric) (hPSD : ∀ a : E, 0 ≤ inner ℝ a (T a))
    (e : E) (ε : ℝ) (_hε : 0 ≤ ε)
    (hbound : ∀ a : E, (inner ℝ a e) ^ 2 ≤ 2 * ε * inner ℝ a (T a)) :
    e ∈ LinearMap.range T ∧ inner ℝ e (spectralPinvVec hT e) ≤ 2 * ε := by
  let b := hT.eigenvectorBasis (rfl : Module.finrank ℝ E = Module.finrank ℝ E)
  let ev := hT.eigenvalues (rfl : Module.finrank ℝ E = Module.finrank ℝ E)
  let x := spectralPinvVec hT e
  have hzero (i : Fin (Module.finrank ℝ E)) (hi : ev i = 0) : b.repr e i = 0 := by
    have hTi : T (b i) = 0 := by
      simpa [b, ev, hi] using
        (hT.apply_eigenvectorBasis (rfl : Module.finrank ℝ E = Module.finrank ℝ E) i)
    have hh := hbound (b i)
    rw [hTi] at hh
    simp at hh
    have he : inner ℝ (b i) e = 0 := by nlinarith
    simpa [b, OrthonormalBasis.repr_apply_apply] using he
  have hTx : T x = e := by
    apply b.repr.injective
    ext i
    rw [hT.eigenvectorBasis_apply_self_apply
      (rfl : Module.finrank ℝ E = Module.finrank ℝ E)]
    change ev i * (b.repr x i) = b.repr e i
    have hx : b.repr x i = (ev i)⁻¹ * b.repr e i := by
      simp [x, spectralPinvVec, b, ev]
    rw [hx]
    by_cases hi : ev i = 0
    · simp [hi, hzero i hi]
    · field_simp
  have hq := hbound x
  rw [hTx] at hq
  have hnonneg := hPSD x
  rw [hTx] at hnonneg
  constructor
  · exact ⟨x, hTx⟩
  · change inner ℝ e x ≤ 2 * ε
    rw [real_inner_comm]
    nlinarith

noncomputable def spectralPinvMatrix {n : ℕ} (R : Matrix (Fin n) (Fin n) ℝ)
    (hR : R.IsHermitian) : Matrix (Fin n) (Fin n) ℝ :=
  Matrix.toEuclideanLin.symm
    (spectralPinvLin (Matrix.isSymmetric_toEuclideanLin_iff.mpr hR))

theorem finiteGramForward {n : ℕ} (_hn : 0 < n)
    (R : Matrix (Fin n) (Fin n) ℝ) (hR : R.PosSemidef)
    (e : Fin n → ℝ) (ε : ℝ) (hε : 0 ≤ ε)
    (hbound : ∀ a : Fin n → ℝ,
      (dotProduct a e) ^ 2 ≤ 2 * ε * dotProduct a (R.mulVec a)) :
    R.PosSemidef ∧ e ∈ LinearMap.range R.toLin' ∧
      dotProduct e ((spectralPinvMatrix R hR.isHermitian).mulVec e) ≤ 2 * ε := by
  let T := R.toEuclideanLin
  have hT : T.IsSymmetric :=
    Matrix.isSymmetric_toEuclideanLin_iff.mpr hR.isHermitian
  have hP : T.IsPositive := Matrix.isPositive_toEuclideanLin_iff.mpr hR
  have hbound' : ∀ a : EuclideanSpace ℝ (Fin n),
      (inner ℝ a (WithLp.toLp 2 e)) ^ 2 ≤
        2 * ε * inner ℝ a (T a) := by
    intro a
    have ha := hbound (WithLp.ofLp a)
    simpa [T, EuclideanSpace.inner_eq_star_dotProduct,
      Matrix.toEuclideanLin_apply, dotProduct_comm] using ha
  obtain ⟨hrange, henergy⟩ :=
    finiteGramForwardAbstract hT hP.inner_nonneg_right
      (WithLp.toLp 2 e) ε hε hbound'
  refine ⟨hR, ?_, ?_⟩
  · rcases hrange with ⟨x, hx⟩
    refine ⟨WithLp.ofLp x, ?_⟩
    have hh := congrArg WithLp.ofLp hx
    simpa [T, Matrix.toEuclideanLin_apply] using hh
  · have hM :
        (spectralPinvMatrix R hR.isHermitian).toEuclideanLin =
          spectralPinvLin hT := by
      simp [spectralPinvMatrix, T, hT]
    have hvec :
        (spectralPinvMatrix R hR.isHermitian).mulVec e =
          WithLp.ofLp (spectralPinvVec hT (WithLp.toLp 2 e)) := by
      have hh := congrArg WithLp.ofLp
        (congrArg (fun f => f (WithLp.toLp 2 e)) hM)
      simpa [Matrix.toEuclideanLin_apply,
        spectralPinvLin_apply] using hh
    rw [hvec]
    simpa [EuclideanSpace.inner_eq_star_dotProduct,
      dotProduct_comm] using henergy

#print axioms finiteGramForward
#print finiteGramForward

#print axioms finiteGramForwardAbstract

end CAS11C02
