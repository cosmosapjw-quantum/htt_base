import Mathlib
import FiniteGram
open Matrix

namespace G11CProbe

section Abstract

variable {E : Type*} [NormedAddCommGroup E] [InnerProductSpace ℝ E] [FiniteDimensional ℝ E]
  {T : E →ₗ[ℝ] E}

theorem repr_T (hT : T.IsSymmetric) (v : E) (i : Fin (Module.finrank ℝ E)) :
    ((hT.eigenvectorBasis rfl).repr (T v)).ofLp i
      = (hT.eigenvalues rfl i) * ((hT.eigenvectorBasis rfl).repr v).ofLp i :=
  hT.eigenvectorBasis_apply_self_apply rfl v i

theorem repr_P (hT : T.IsSymmetric) (v : E) (i : Fin (Module.finrank ℝ E)) :
    ((hT.eigenvectorBasis rfl).repr (CAS11C02.spectralPinvLin hT v)).ofLp i
      = ((hT.eigenvalues rfl i))⁻¹ * ((hT.eigenvectorBasis rfl).repr v).ofLp i := by
  rw [CAS11C02.spectralPinvLin_apply]
  simp [CAS11C02.spectralPinvVec]

theorem diag_symm (hT : T.IsSymmetric) (A : E →ₗ[ℝ] E) (d : Fin (Module.finrank ℝ E) → ℝ)
    (hA : ∀ v i, ((hT.eigenvectorBasis rfl).repr (A v)).ofLp i
      = d i * ((hT.eigenvectorBasis rfl).repr v).ofLp i) :
    A.IsSymmetric := by
  intro x y
  rw [← (hT.eigenvectorBasis rfl).repr.inner_map_map (A x) y,
    ← (hT.eigenvectorBasis rfl).repr.inner_map_map x (A y), PiLp.inner_apply, PiLp.inner_apply]
  refine Finset.sum_congr rfl fun i _ => ?_
  rw [hA, hA, RCLike.inner_apply, RCLike.inner_apply, conj_trivial, conj_trivial]
  ring

theorem abstract_penrose (hT : T.IsSymmetric) :
    (∀ v, T (CAS11C02.spectralPinvLin hT (T v)) = T v) ∧
      (∀ v, CAS11C02.spectralPinvLin hT (T (CAS11C02.spectralPinvLin hT v))
        = CAS11C02.spectralPinvLin hT v) ∧
      (T ∘ₗ CAS11C02.spectralPinvLin hT).IsSymmetric ∧
      (CAS11C02.spectralPinvLin hT ∘ₗ T).IsSymmetric := by
  set b := hT.eigenvectorBasis rfl
  set ev := hT.eigenvalues rfl
  have key : ∀ i, ev i * ((ev i)⁻¹ * ev i) = ev i ∧ (ev i)⁻¹ * (ev i * (ev i)⁻¹) = (ev i)⁻¹ := by
    intro i
    by_cases h : ev i = 0
    · simp [h]
    · constructor <;> field_simp
  refine ⟨fun v => ?_, fun v => ?_, ?_, ?_⟩
  · apply b.repr.injective
    ext i
    rw [repr_T, repr_P, repr_T, repr_T, ← mul_assoc ((ev i)⁻¹), ← mul_assoc, (key i).1]
  · apply b.repr.injective
    ext i
    rw [repr_P, repr_T, repr_P, repr_P, ← mul_assoc (ev i), ← mul_assoc, (key i).2]
  · refine diag_symm hT _ (fun i => ev i * (ev i)⁻¹) fun v i => ?_
    rw [LinearMap.comp_apply, repr_T, repr_P, mul_assoc]
  · refine diag_symm hT _ (fun i => (ev i)⁻¹ * ev i) fun v i => ?_
    rw [LinearMap.comp_apply, repr_P, repr_T, mul_assoc]

end Abstract

theorem spectralPinv_penrose {n : ℕ} (R : Matrix (Fin n) (Fin n) ℝ) (hR : R.IsHermitian) :
    R * CAS11C02.spectralPinvMatrix R hR * R = R ∧
      CAS11C02.spectralPinvMatrix R hR * R * CAS11C02.spectralPinvMatrix R hR
        = CAS11C02.spectralPinvMatrix R hR ∧
      (R * CAS11C02.spectralPinvMatrix R hR)ᵀ = R * CAS11C02.spectralPinvMatrix R hR ∧
      (CAS11C02.spectralPinvMatrix R hR * R)ᵀ = CAS11C02.spectralPinvMatrix R hR * R := by
  set T := R.toEuclideanLin with hTdef
  have hT : T.IsSymmetric := Matrix.isSymmetric_toEuclideanLin_iff.mpr hR
  set P := CAS11C02.spectralPinvMatrix R hR with hPdef
  have hPl : P.toEuclideanLin = CAS11C02.spectralPinvLin hT := by
    simp [hPdef, CAS11C02.spectralPinvMatrix, hT]
  have hRv : ∀ v : Fin n → ℝ, R *ᵥ v = WithLp.ofLp (T (WithLp.toLp 2 v)) := fun v => by
    simp [hTdef, Matrix.toEuclideanLin_apply]
  have hPv : ∀ v : Fin n → ℝ, P *ᵥ v = WithLp.ofLp (CAS11C02.spectralPinvLin hT (WithLp.toLp 2 v)) :=
    fun v => by rw [← hPl]; simp [Matrix.toEuclideanLin_apply]
  obtain ⟨h1, h2, h3, h4⟩ := abstract_penrose hT
  have herm : ∀ M : Matrix (Fin n) (Fin n) ℝ,
      (∀ x : EuclideanSpace ℝ (Fin n), M.toEuclideanLin x = T (CAS11C02.spectralPinvLin hT x)) ∨
      (∀ x : EuclideanSpace ℝ (Fin n), M.toEuclideanLin x = CAS11C02.spectralPinvLin hT (T x)) →
      Mᵀ = M := by
    intro M hM
    have hs : M.toEuclideanLin.IsSymmetric := by
      rcases hM with hM | hM
      · intro x y; rw [hM, hM]; exact h3 x y
      · intro x y; rw [hM, hM]; exact h4 x y
    have hH := Matrix.isSymmetric_toEuclideanLin_iff.mp hs
    rw [← Matrix.conjTranspose_eq_transpose_of_trivial]
    exact hH
  refine ⟨?_, ?_, ?_, ?_⟩
  · refine Matrix.toLin'.injective (LinearMap.ext fun v => ?_)
    simp only [Matrix.toLin'_apply]
    rw [← Matrix.mulVec_mulVec, ← Matrix.mulVec_mulVec, hRv, hPv, hRv]
    simp only [WithLp.toLp_ofLp]
    rw [h1, hRv]
  · refine Matrix.toLin'.injective (LinearMap.ext fun v => ?_)
    simp only [Matrix.toLin'_apply]
    rw [← Matrix.mulVec_mulVec, ← Matrix.mulVec_mulVec, hPv, hRv, hPv]
    simp only [WithLp.toLp_ofLp]
    rw [h2, hPv]
  · refine herm _ (Or.inl fun x => ?_)
    rw [Matrix.toEuclideanLin_apply, ← Matrix.mulVec_mulVec, hPv, hRv]
    simp
  · refine herm _ (Or.inr fun x => ?_)
    rw [Matrix.toEuclideanLin_apply, ← Matrix.mulVec_mulVec, hRv, hPv]
    simp

end G11CProbe
