import Mathlib.LinearAlgebra.Multilinear.Basic
import Mathlib.LinearAlgebra.Dual.Defs
import Mathlib.LinearAlgebra.Trace
import Mathlib.Data.Real.Basic
import Mathlib.Tactic.NormNum

/-!
CAS-17-C04: finite tensor contractions under one common invertible passive
coordinate change. Mathematical inputs: EXECUTION_CONTRACT.json and COMMON_SPEC.md.

For a tensor of type (p,q), its p contravariant slots accept covectors and its
q covariant slots accept vectors. All slots use the SAME coordinate change L.
The covector action is inverse pullback; the tensor action is inverse pullback
on every slot. No invariance premise is assumed. The statements are universal
in the tensor, slot arguments, and invertible linear change.

This does not replace the physical observer, prove calibration availability,
or promote the historical four-axis/scientific status. No derivative of a
coordinate map is modeled: the statement is the pointwise finite tensor law.
-/

namespace CAS17C04

noncomputable section

variable {V : Type} [AddCommGroup V] [Module ℝ V]

/-- Covector components transform by the inverse of the vector component map. -/
def covectorChange (L : V ≃ₗ[ℝ] V) :
    Module.Dual ℝ V ≃ₗ[ℝ] Module.Dual ℝ V where
  toFun α := α.comp L.symm.toLinearMap
  invFun α := α.comp L.toLinearMap
  left_inv α := by ext v; simp
  right_inv α := by ext v; simp
  map_add' α β := by ext v; simp
  map_smul' r α := by ext v; simp

@[simp] theorem covectorChange_apply (L : V ≃ₗ[ℝ] V)
    (α : Module.Dual ℝ V) (v : V) :
    covectorChange L α v = α (L.symm v) := rfl

/-- The fundamental upper/lower index contraction. -/
theorem covector_vector_contraction (L : V ≃ₗ[ℝ] V)
    (α : Module.Dual ℝ V) (v : V) :
    covectorChange L α (L v) = α v := by simp

/-- The slot family for a type-(p,q) tensor, with variance preserved. -/
abbrev Slot (V : Type) [AddCommGroup V] [Module ℝ V]
    {p q : ℕ} : Fin p ⊕ Fin q → Type :=
  fun i => match i with
  | .inl _ => Module.Dual ℝ V
  | .inr _ => V

instance {p q : ℕ} (i : Fin p ⊕ Fin q) : AddCommGroup (Slot V i) :=
  match i with
  | .inl _ => inferInstance
  | .inr _ => inferInstance

instance {p q : ℕ} (i : Fin p ⊕ Fin q) : Module ℝ (Slot V i) :=
  match i with
  | .inl _ => inferInstance
  | .inr _ => inferInstance

/-- One common L supplies every vector and covector slot action. -/
def slotChange {p q : ℕ} (L : V ≃ₗ[ℝ] V) (i : Fin p ⊕ Fin q) :
    Slot V i ≃ₗ[ℝ] Slot V i :=
  match i with
  | .inl _ => covectorChange L
  | .inr _ => L

abbrev Tensor (V : Type) [AddCommGroup V] [Module ℝ V] (p q : ℕ) :=
  MultilinearMap ℝ (Slot V (p := p) (q := q)) ℝ

/-- Passive tensor components are pulled back by the inverse slot action. -/
def tensorChange {p q : ℕ} (L : V ≃ₗ[ℝ] V) (T : Tensor V p q) :
    Tensor V p q :=
  T.compLinearMap (fun i => (slotChange L i).symm.toLinearMap)

def argumentChange {p q : ℕ} (L : V ≃ₗ[ℝ] V)
    (a : ∀ i : Fin p ⊕ Fin q, Slot V i) :
    ∀ i : Fin p ⊕ Fin q, Slot V i := fun i => slotChange L i (a i)

/-- Any complete evaluation contraction of any finite mixed tensor is invariant.
    Includes p=0, q=0, the scalar case, and arbitrary (not merely Lorentz) L. -/
theorem mixed_tensor_contraction_invariant {p q : ℕ}
    (L : V ≃ₗ[ℝ] V) (T : Tensor V p q)
    (a : ∀ i : Fin p ⊕ Fin q, Slot V i) :
    tensorChange L T (argumentChange L a) = T a := by
  change T (fun i => (slotChange L i).symm (slotChange L i (a i))) = T a
  congr 1
  funext i
  exact (slotChange L i).symm_apply_apply (a i)

/-- Finite coordinate spaces are covered uniformly in dimension n. -/
theorem finite_coordinate_contraction_invariant {n p q : ℕ}
    (L : (Fin n → ℝ) ≃ₗ[ℝ] (Fin n → ℝ))
    (T : Tensor (Fin n → ℝ) p q)
    (a : ∀ i : Fin p ⊕ Fin q, Slot (Fin n → ℝ) i) :
    tensorChange L T (argumentChange L a) = T a :=
  mixed_tensor_contraction_invariant L T a

/-- Finite Einstein sums preserve the contraction term by term. -/
theorem summed_tensor_contraction_invariant {p q : ℕ}
    {κ : Type} [Fintype κ] (L : V ≃ₗ[ℝ] V) (T : Tensor V p q)
    (a : κ → ∀ i : Fin p ⊕ Fin q, Slot V i) :
    (∑ k, tensorChange L T (argumentChange L (a k))) = ∑ k, T (a k) := by
  apply Finset.sum_congr rfl
  intro k _
  exact mixed_tensor_contraction_invariant L T (a k)

/-- Dual basis/vector slots for arbitrary pairing of every upper/lower index. -/
def pairedBasisSlots {n r : ℕ} (e : Module.Basis (Fin n) ℝ (Fin n → ℝ))
    (σ : Fin r ≃ Fin r) (f : Fin r → Fin n) :
    ∀ i : Fin r ⊕ Fin r, Slot (Fin n → ℝ) i :=
  fun i => match i with
  | .inl j => e.coord (f j)
  | .inr j => e (f (σ j))

/-- All internal indices of an arbitrary type-(r,r) tensor may be contracted,
    with any pairing σ and any basis e. The same L transforms tensor, basis
    vectors, and dual covectors. Rank zero and dimension zero remain included. -/
theorem complete_internal_contraction_invariant {n r : ℕ}
    (L : (Fin n → ℝ) ≃ₗ[ℝ] (Fin n → ℝ))
    (T : Tensor (Fin n → ℝ) r r)
    (e : Module.Basis (Fin n) ℝ (Fin n → ℝ)) (σ : Fin r ≃ Fin r) :
    (∑ f : Fin r → Fin n,
      tensorChange L T (argumentChange L (pairedBasisSlots e σ f))) =
      ∑ f : Fin r → Fin n, T (pairedBasisSlots e σ f) :=
  summed_tensor_contraction_invariant L T (pairedBasisSlots e σ)

/-- Internal upper/lower contraction of a (1,1) tensor is its trace. -/
theorem endomorphism_trace_contraction_invariant {n : ℕ}
    (L : (Fin n → ℝ) ≃ₗ[ℝ] (Fin n → ℝ))
    (T : (Fin n → ℝ) →ₗ[ℝ] (Fin n → ℝ)) :
    LinearMap.trace ℝ (Fin n → ℝ) (L.conj T) =
      LinearMap.trace ℝ (Fin n → ℝ) T :=
  LinearMap.trace_conj' T L

/-- The fixed signature (-,+,+,+) of the common specification. -/
def minkowski (v w : Fin 4 → ℝ) : ℝ :=
  -(v 0 * w 0) + v 1 * w 1 + v 2 * w 2 + v 3 * w 3

def observer : Fin 4 → ℝ := ![1, 0, 0, 0]
def replacedObserver : Fin 4 → ℝ := ![5 / 3, 4 / 3, 0, 0]
def sourcewardNull : Fin 4 → ℝ := ![-1, 1, 0, 0]

/-- Concrete scope falsifier: two future unit physical observers measure
    different contractions with the same null vector. This is NOT a passive
    change of all fields by one L. Both observer norms and the null norm are
    checked, rather than assumed as conclusion-shaped premises. -/
theorem physical_observer_replacement_counterexample :
    minkowski observer observer = -1 ∧
    minkowski replacedObserver replacedObserver = -1 ∧
    observer 0 > 0 ∧ replacedObserver 0 > 0 ∧
    minkowski sourcewardNull sourcewardNull = 0 ∧
    minkowski observer sourcewardNull = 1 ∧
    minkowski replacedObserver sourcewardNull = 3 ∧
    minkowski observer sourcewardNull ≠
      minkowski replacedObserver sourcewardNull := by
  norm_num [minkowski, observer, replacedObserver, sourcewardNull,
    Matrix.cons_val_two, Matrix.cons_val_three]

end
end CAS17C04

#check CAS17C04.finite_coordinate_contraction_invariant
#check CAS17C04.complete_internal_contraction_invariant
#check CAS17C04.endomorphism_trace_contraction_invariant
#check CAS17C04.physical_observer_replacement_counterexample
#print axioms CAS17C04.covector_vector_contraction
#print axioms CAS17C04.mixed_tensor_contraction_invariant
#print axioms CAS17C04.finite_coordinate_contraction_invariant
#print axioms CAS17C04.summed_tensor_contraction_invariant
#print axioms CAS17C04.complete_internal_contraction_invariant
#print axioms CAS17C04.endomorphism_trace_contraction_invariant
#print axioms CAS17C04.physical_observer_replacement_counterexample
