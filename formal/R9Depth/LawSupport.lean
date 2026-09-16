import R9Depth.BlockBridge
import R9Depth.Covariance
import Mathlib.Data.Real.Basic
import Mathlib.MeasureTheory.Measure.MeasureSpaceDef
import Mathlib.MeasureTheory.Measure.Map
import Mathlib.MeasureTheory.Measure.Support
import Mathlib.MeasureTheory.Constructions.BorelSpace.Basic
import Mathlib.Topology.Algebra.Module.FiniteDimension
import Mathlib.LinearAlgebra.Matrix.ToLin
import Mathlib.LinearAlgebra.Matrix.NonsingularInverse

set_option autoImplicit false
open Matrix MeasureTheory
open scoped BigOperators

namespace R9Depth

abbrev StateIx (d : Nat → Nat) (s n : Nat) := R9Block.Ix d s n

noncomputable def transformLinearEquiv (d : Nat → Nat)
    (K : ∀ j, Matrix (Fin (d (j+1))) (Fin (d j)) ℝ) (s n : Nat) :
    (StateIx d s n → ℝ) ≃ₗ[ℝ] (StateIx d s n → ℝ) :=
  LinearEquiv.ofBijective (Matrix.mulVecLin (R9Block.transform d K s n))
    (R9Block.transform_bijective d K s n)

noncomputable def transformContinuousLinearEquiv (d : Nat → Nat)
    (K : ∀ j, Matrix (Fin (d (j+1))) (Fin (d j)) ℝ) (s n : Nat) :
    (StateIx d s n → ℝ) ≃L[ℝ] (StateIx d s n → ℝ) :=
  (transformLinearEquiv d K s n).toContinuousLinearEquiv

noncomputable def transformHomeomorph (d : Nat → Nat)
    (K : ∀ j, Matrix (Fin (d (j+1))) (Fin (d j)) ℝ) (s n : Nat) :
    (StateIx d s n → ℝ) ≃ₜ (StateIx d s n → ℝ) :=
  (transformContinuousLinearEquiv d K s n).toHomeomorph

noncomputable def transformMeasurableEquiv (d : Nat → Nat)
    (K : ∀ j, Matrix (Fin (d (j+1))) (Fin (d j)) ℝ) (s n : Nat) :
    (StateIx d s n → ℝ) ≃ᵐ (StateIx d s n → ℝ) :=
  (transformHomeomorph d K s n).toMeasurableEquiv

@[simp] theorem transformMeasurableEquiv_apply (d : Nat → Nat)
    (K : ∀ j, Matrix (Fin (d (j+1))) (Fin (d j)) ℝ) (s n : Nat)
    (y : StateIx d s n → ℝ) :
    transformMeasurableEquiv d K s n y = R9Block.transform d K s n *ᵥ y := rfl

/-- The fixed, parameter-independent retained-state transform is an exact law equivalence. -/
theorem map_transform_symm_map (d : Nat → Nat)
    (K : ∀ j, Matrix (Fin (d (j+1))) (Fin (d j)) ℝ) (s n : Nat)
    (μ : Measure (StateIx d s n → ℝ)) :
    (μ.map (transformMeasurableEquiv d K s n)).map
      (transformMeasurableEquiv d K s n).symm = μ := by
  exact MeasurableEquiv.map_symm_map _

/-- The reverse round-trip, pointwise for an arbitrary parameterized law family. -/
theorem map_transform_map_symm (d : Nat → Nat)
    (K : ∀ j, Matrix (Fin (d (j+1))) (Fin (d j)) ℝ) (s n : Nat)
    (μ : Measure (StateIx d s n → ℝ)) :
    (μ.map (transformMeasurableEquiv d K s n).symm).map
      (transformMeasurableEquiv d K s n) = μ := by
  exact MeasurableEquiv.map_map_symm _

theorem transform_family_roundtrip {Θ : Type*} (d : Nat → Nat)
    (K : ∀ j, Matrix (Fin (d (j+1))) (Fin (d j)) ℝ) (s n : Nat)
    (P : Θ → Measure (StateIx d s n → ℝ)) (θ : Θ) :
    ((P θ).map (transformMeasurableEquiv d K s n)).map
      (transformMeasurableEquiv d K s n).symm = P θ := by
  exact map_transform_symm_map d K s n (P θ)

/-- A homeomorphism transports the topological support of every measure exactly. -/
theorem support_map_homeomorph {X Y : Type*}
    [TopologicalSpace X] [MeasurableSpace X]
    [TopologicalSpace Y] [MeasurableSpace Y]
    [BorelSpace X] [BorelSpace Y]
    (h : X ≃ₜ Y) (e : X ≃ᵐ Y) (he : (e : X → Y) = h) (μ : Measure X) :
    (μ.map e).support = h '' μ.support := by
  ext y
  constructor
  · intro hy
    rw [Measure.support_eq_forall_isOpen] at hy
    let x := h.symm y
    have hxy : h x = y := h.apply_symm_apply y
    refine ⟨x, ?_, hxy⟩
    rw [Measure.support_eq_forall_isOpen]
    intro V hxV hV
    have hU : IsOpen (h '' V) := h.isOpen_image.mpr hV
    have hyU : y ∈ h '' V := ⟨x, hxV, hxy⟩
    have hpos := hy (h '' V) hyU hU
    rw [e.map_apply (h '' V)] at hpos
    have hpre : e ⁻¹' (h '' V) = V := by
      rw [he]
      exact Set.preimage_image_eq V h.injective
    simpa [hpre] using hpos
  · rintro ⟨x, hx, rfl⟩
    rw [Measure.support_eq_forall_isOpen] at hx ⊢
    intro U hU hUopen
    have hV : IsOpen (h ⁻¹' U) := h.isOpen_preimage.mpr hUopen
    have hxV : x ∈ h ⁻¹' U := hU
    have hpos := hx _ hxV hV
    rw [e.map_apply U]
    have hpre : e ⁻¹' U = h ⁻¹' U := by rw [he]
    simpa [hpre] using hpos

/-- Matrix congruence transports the range even for singular covariance matrices. -/
theorem matrix_range_congruence {ι : Type*} [Fintype ι] [DecidableEq ι]
    (T C : Matrix ι ι ℝ)
    (hT : Function.Bijective (T *ᵥ ·))
    (hTt : Function.Surjective (T.transpose *ᵥ ·)) :
    Set.range (fun x => (T * C * T.transpose) *ᵥ x) =
      (fun x => T *ᵥ x) '' Set.range (fun x => C *ᵥ x) := by
  ext z
  constructor
  · rintro ⟨x, rfl⟩
    refine ⟨C *ᵥ (T.transpose *ᵥ x), ?_, ?_⟩
    · exact ⟨T.transpose *ᵥ x, rfl⟩
    · dsimp
      simpa [Matrix.mul_assoc, Matrix.mulVec_mulVec]
  · rintro ⟨z, ⟨u, rfl⟩, rfl⟩
    obtain ⟨x, hx⟩ := hTt u
    refine ⟨x, ?_⟩
    dsimp
    rw [← hx]
    simp [Matrix.mul_assoc, Matrix.mulVec_mulVec]

theorem transform_transpose_surjective (d : Nat → Nat)
    (K : ∀ j, Matrix (Fin (d (j+1))) (Fin (d j)) ℝ) (s n : Nat) :
    Function.Surjective ((R9Block.transform d K s n).transpose *ᵥ ·) := by
  apply Matrix.mulVec_surjective_iff_isUnit.mpr
  apply (Matrix.isUnit_iff_isUnit_det (A := (R9Block.transform d K s n).transpose)).mpr
  rw [Matrix.det_transpose, R9Block.determinant_one]
  exact isUnit_one

theorem transform_matrix_range_congruence (d : Nat → Nat)
    (K : ∀ j, Matrix (Fin (d (j+1))) (Fin (d j)) ℝ) (s n : Nat)
    (C : Matrix (StateIx d s n) (StateIx d s n) ℝ) :
    Set.range (fun x => (R9Block.transform d K s n * C * (R9Block.transform d K s n).transpose) *ᵥ x) =
      (fun x => R9Block.transform d K s n *ᵥ x) '' Set.range (fun x => C *ᵥ x) := by
  letI : Fintype (StateIx d s n) := R9Block.ixFinite d s n
  letI : DecidableEq (StateIx d s n) := R9Block.ixDecidable d s n
  apply matrix_range_congruence
  · exact (R9Block.transform_bijective d K s n)
  · exact transform_transpose_surjective d K s n

def affineRange {ι : Type*} [Fintype ι] (μ : ι → ℝ) (C : Matrix ι ι ℝ) : Set (ι → ℝ) :=
  {z | ∃ u, z = μ + C *ᵥ u}

theorem affine_range_transport {ι : Type*} [Fintype ι] [DecidableEq ι]
    (T C : Matrix ι ι ℝ) (μ : ι → ℝ)
    (hT : Function.Bijective (T *ᵥ ·))
    (hTt : Function.Surjective (T.transpose *ᵥ ·)) :
    (fun x => T *ᵥ x) '' affineRange μ C =
      affineRange (T *ᵥ μ) (T * C * T.transpose) := by
  ext z
  simp only [affineRange, Set.mem_setOf_eq]
  constructor
  · rintro ⟨x, hx, rfl⟩
    rcases hx with ⟨u, hu⟩
    subst x
    obtain ⟨w, hw⟩ := hTt u
    refine ⟨w, ?_⟩
    rw [← hw]
    simp [Matrix.mul_assoc, Matrix.mulVec_add, Matrix.mulVec_mulVec]
  · rintro ⟨u, rfl⟩
    refine ⟨μ + C *ᵥ (T.transpose *ᵥ u), ⟨_, rfl⟩, ?_⟩
    simp [Matrix.mul_assoc, Matrix.mulVec_add, Matrix.mulVec_mulVec]

theorem transform_affine_range_transport (d : Nat → Nat)
    (K : ∀ j, Matrix (Fin (d (j+1))) (Fin (d j)) ℝ) (s n : Nat)
    (μ : StateIx d s n → ℝ) (C : Matrix (StateIx d s n) (StateIx d s n) ℝ) :
    (fun x => R9Block.transform d K s n *ᵥ x) '' affineRange μ C =
      affineRange (R9Block.transform d K s n *ᵥ μ)
        (R9Block.transform d K s n * C * (R9Block.transform d K s n).transpose) := by
  letI : Fintype (StateIx d s n) := R9Block.ixFinite d s n
  letI : DecidableEq (StateIx d s n) := R9Block.ixDecidable d s n
  apply affine_range_transport
  · exact R9Block.transform_bijective d K s n
  · exact transform_transpose_surjective d K s n

/-- D1 mean transport specialized to the retained full transform. -/
theorem transform_mean_transport {Ω : Type*} [MeasurableSpace Ω]
    (d : Nat → Nat) (K : ∀ j, Matrix (Fin (d (j+1))) (Fin (d j)) ℝ)
    (s n : Nat)
    [Fintype (StateIx d s n)]
    (Y : Ω → StateIx d s n → ℝ) (μ : Measure Ω) [IsProbabilityMeasure μ]
    (hY : ∀ i, MemLp (fun ω => Y ω i) 2 μ) :
    meanVector (fun ω => R9Block.transform d K s n *ᵥ Y ω) μ =
      R9Block.transform d K s n *ᵥ meanVector Y μ := by
  exact mean_linear_map Y (R9Block.transform d K s n) hY

/-- D1 covariance transport keeps every retained coordinate, including initial cross blocks. -/
theorem transform_covariance_transport {Ω : Type*} [MeasurableSpace Ω]
    (d : Nat → Nat) (K : ∀ j, Matrix (Fin (d (j+1))) (Fin (d j)) ℝ)
    (s n : Nat)
    [Fintype (StateIx d s n)]
    (Y : Ω → StateIx d s n → ℝ) (μ : Measure Ω) [IsProbabilityMeasure μ]
    (hY : ∀ i, MemLp (fun ω => Y ω i) 2 μ) :
    covarianceMatrix (fun ω => R9Block.transform d K s n *ᵥ Y ω) μ =
      R9Block.transform d K s n * covarianceMatrix Y μ *
        (R9Block.transform d K s n).transpose := by
  exact covariance_linear_map Y (R9Block.transform d K s n) hY

end R9Depth

#print axioms R9Depth.transformLinearEquiv
#print axioms R9Depth.map_transform_symm_map
#print axioms R9Depth.support_map_homeomorph
#print axioms R9Depth.matrix_range_congruence
#print axioms R9Depth.transform_matrix_range_congruence
#print axioms R9Depth.transform_mean_transport
#print axioms R9Depth.transform_covariance_transport
