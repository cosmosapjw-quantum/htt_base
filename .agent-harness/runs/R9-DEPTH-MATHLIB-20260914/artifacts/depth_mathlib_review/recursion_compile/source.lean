import Mathlib.Data.Real.Basic
import Mathlib.Algebra.Group.Basic
import Mathlib.LinearAlgebra.Matrix.ToLin

/- R9 D3 heterogeneous recursion; prior source at a6a4827f, new reverse inverse.
No determinant or probability admission follows from these algebraic lemmas. -/

set_option autoImplicit false

namespace DepthLean

universe u v

/-- The sole algebraic law used by the reconstruction recursion.  Lean core
    does not provide the bundled additive-group hierarchy used by mathlib. -/
class AddSubCancel (α : Type u) extends Add α, Sub α where
  add_sub_cancel' : ∀ a b : α, a + b - b = a
  sub_add_cancel' : ∀ a b : α, a - b + b = a

/-- Heterogeneous finite block paths.  The index records the block level and
    the length records the remaining finite depth. -/
inductive DepChain (α : Nat → Type u) : Nat → Nat → Type u where
  | single {start : Nat} : α start → DepChain α start 0
  | step {start depth : Nat} : α start → DepChain α (Nat.succ start) depth →
      DepChain α start (Nat.succ depth)

/-- Residual blocks have the next-level type at every finite step. -/
inductive DepResidual (α : Nat → Type u) : Nat → Nat → Type u where
  | nil {start : Nat} : DepResidual α start 0
  | step {start depth : Nat} : α (Nat.succ start) →
      DepResidual α (Nat.succ start) depth → DepResidual α start (Nat.succ depth)

/-- Typed reconstruction for arbitrary finite block dimensions and
    time-dependent transports.  This is a compiled definition only; the
    contract's matrix, determinant, and law-preservation theorems are not
    asserted below. -/
def reconstructDependent {α : Nat → Type u}
    (ops : ∀ level, AddSubCancel (α level))
    (transport : ∀ level, α level → α (Nat.succ level))
    {start depth : Nat} (initial : α start) :
    DepResidual α start depth → DepChain α start depth
  | .nil => .single initial
  | .step residual rest =>
      letI := ops (Nat.succ start)
      .step initial
        (reconstructDependent ops transport (residual + transport start initial) rest)

/-- Typed residual extraction for arbitrary finite block dimensions and
    time-dependent transports. -/
def residualsDependent {α : Nat → Type u}
    (ops : ∀ level, AddSubCancel (α level))
    (transport : ∀ level, α level → α (Nat.succ level)) :
    {start depth : Nat} → DepChain α start depth → DepResidual α start depth
  | _, _, .single _ => .nil
  | start, _, .step first (.single second) =>
      letI := ops (Nat.succ start)
      .step (second - transport start first) .nil
  | start, _, .step first (.step second rest) =>
      letI := ops (Nat.succ start)
      .step (second - transport start first)
        (residualsDependent ops transport (.step second rest))

/-- First reconstruction inverse for arbitrary finite dependent block types.
    This uses only the stated cancellation law at each next-level block. -/
theorem residualsDependent_reconstructDependent {α : Nat → Type u}
    (ops : ∀ level, AddSubCancel (α level))
    (transport : ∀ level, α level → α (Nat.succ level))
    {start depth : Nat} (initial : α start) (rs : DepResidual α start depth) :
    residualsDependent ops transport
      (reconstructDependent ops transport initial rs) = rs := by
  induction rs with
  | nil => rfl
  | @step start depth residual rest ih =>
      cases rest with
      | nil =>
          letI := ops (Nat.succ start)
          calc
            residualsDependent ops transport
                (reconstructDependent ops transport initial (.step residual .nil)) =
                .step (residual + transport start initial - transport start initial) .nil := rfl
            _ = .step residual .nil := by rw [AddSubCancel.add_sub_cancel']
      | @step _ _ next tail =>
          letI := ops (Nat.succ start)
          calc
            residualsDependent ops transport
                (reconstructDependent ops transport initial (.step residual (.step next tail))) =
                .step (residual + transport start initial - transport start initial)
                  (residualsDependent ops transport
                    (reconstructDependent ops transport
                      (residual + transport start initial) (.step next tail))) := rfl
            _ = .step residual (.step next tail) := by
                rw [AddSubCancel.add_sub_cancel']
                rw [ih]


/-- Initial block of a nonempty dependent trajectory. -/
def initialDependent {α : Nat → Type u} :
    {start depth : Nat} → DepChain α start depth → α start
  | _, _, .single first => first
  | _, _, .step first _ => first

/-- Reconstructing a heterogeneous path from its retained initial block and all
residual blocks returns the original path, for every finite depth. -/
theorem reconstructDependent_residualsDependent {α : Nat → Type u}
    (ops : ∀ level, AddSubCancel (α level))
    (transport : ∀ level, α level → α (Nat.succ level))
    {start depth : Nat} (ys : DepChain α start depth) :
    reconstructDependent ops transport (initialDependent ys)
      (residualsDependent ops transport ys) = ys := by
  induction ys with
  | single first => rfl
  | @step start depth first tail ih =>
      cases tail with
      | single second =>
          letI := ops (Nat.succ start)
          simp [initialDependent, residualsDependent, reconstructDependent,
            AddSubCancel.sub_add_cancel']
      | @step _ _ second rest =>
          letI := ops (Nat.succ start)
          change DepChain.step first
            (reconstructDependent ops transport
              (second - transport start first + transport start first)
              (residualsDependent ops transport (.step second rest))) = _
          rw [AddSubCancel.sub_add_cancel']
          exact congrArg (DepChain.step first) ih

/-- The cancellation structure is supplied by ordinary mathlib additive commutative groups. -/
abbrev addGroupCancellation (α : Type u) [AddCommGroup α] : AddSubCancel α where
  add := (· + ·)
  sub := (· - ·)
  add_sub_cancel' := (by intros; simp)
  sub_add_cancel' := (by intros; simp)


/-- Reconstruction retains the given initial block exactly. -/
theorem initialDependent_reconstructDependent {α : Nat → Type u}
    (ops : ∀ level, AddSubCancel (α level))
    (transport : ∀ level, α level → α (Nat.succ level))
    {start depth : Nat} (initial : α start) (rs : DepResidual α start depth) :
    initialDependent (reconstructDependent ops transport initial rs) = initial := by
  cases rs <;> rfl

/-- An explicit two-sided equivalence, retaining the entire initial block. -/
def pathEquiv {α : Nat → Type u} (ops : ∀ level, AddSubCancel (α level))
    (transport : ∀ level, α level → α (Nat.succ level)) (start depth : Nat) :
    DepChain α start depth ≃ α start × DepResidual α start depth where
  toFun ys := (initialDependent ys, residualsDependent ops transport ys)
  invFun pair := reconstructDependent ops transport pair.1 pair.2
  left_inv := reconstructDependent_residualsDependent ops transport
  right_inv := by
    intro pair
    apply Prod.ext
    · exact initialDependent_reconstructDependent ops transport pair.1 pair.2
    · exact residualsDependent_reconstructDependent ops transport pair.1 pair.2

/-- Every compatible residual path occurs for any retained initial block. -/
theorem residualsDependent_surjective {α : Nat → Type u}
    (ops : ∀ level, AddSubCancel (α level))
    (transport : ∀ level, α level → α (Nat.succ level))
    {start depth : Nat} (initial : α start) (rs : DepResidual α start depth) :
    ∃ ys : DepChain α start depth, residualsDependent ops transport ys = rs :=
  ⟨reconstructDependent ops transport initial rs,
    residualsDependent_reconstructDependent ops transport initial rs⟩

/-- Arbitrary rectangular real matrices instantiate the same exact equivalence.
No equal block size, nonsingular K or fixed depth is assumed. -/
noncomputable def realBlockPathEquiv (d : Nat → Nat)
    (K : ∀ j, Matrix (Fin (d (j+1))) (Fin (d j)) ℝ) (start depth : Nat) :
    DepChain (fun j => Fin (d j) → ℝ) start depth ≃
      (Fin (d start) → ℝ) × DepResidual (fun j => Fin (d j) → ℝ) start depth :=
  pathEquiv (fun j => addGroupCancellation (Fin (d j) → ℝ))
    (fun j x => Matrix.mulVec (K j) x) start depth

end DepthLean

#print axioms DepthLean.reconstructDependent_residualsDependent
#print axioms DepthLean.residualsDependent_reconstructDependent

#print axioms DepthLean.pathEquiv
#print axioms DepthLean.realBlockPathEquiv
