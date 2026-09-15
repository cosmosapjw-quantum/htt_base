import Mathlib.Data.Real.Basic
import Mathlib.Data.Matrix.Block
import Mathlib.LinearAlgebra.Matrix.NonsingularInverse
import Mathlib.LinearAlgebra.Matrix.ToLin

/- R9 D3: explicit ordered, heterogeneous finite block coordinates.
This formalizes a prior deterministic result; it does not admit Gaussian laws. -/
set_option autoImplicit false
open Matrix
namespace R9Block

def Ix (d : Nat → Nat) (s : Nat) : Nat → Type
  | 0 => Fin (d s)
  | n+1 => Fin (d s) ⊕ Ix d (s+1) n

instance ixFinite (d : Nat → Nat) (s n : Nat) : Fintype (Ix d s n) := by
  induction n generalizing s with
  | zero => exact inferInstanceAs (Fintype (Fin (d s)))
  | succ n ih => letI := ih (s+1); exact inferInstanceAs (Fintype (Fin (d s) ⊕ Ix d (s+1) n))

instance ixDecidable (d : Nat → Nat) (s n : Nat) : DecidableEq (Ix d s n) := by
  induction n generalizing s with
  | zero => exact inferInstanceAs (DecidableEq (Fin (d s)))
  | succ n ih => letI := ih (s+1); exact inferInstanceAs (DecidableEq (Fin (d s) ⊕ Ix d (s+1) n))

/-- Inject a block into the first block, with all remaining coordinates zero. -/
def injectFirst (d : Nat → Nat) (s : Nat) : (n : Nat) → (Fin (d s) → ℝ) → Ix d s n → ℝ
  | 0, a => a
  | _+1, a => Sum.elim a 0

def first (d : Nat → Nat) (s : Nat) : (n : Nat) → (Ix d s n → ℝ) → Fin (d s) → ℝ
  | 0, y => y
  | _+1, y => y ∘ Sum.inl

/-- Coupling has -K only in the next block, and zeros at every deeper block. -/
def coupling (d : Nat → Nat)
    (K : ∀ j, Matrix (Fin (d (j+1))) (Fin (d j)) ℝ) (s n : Nat) :
    Matrix (Ix d (s+1) n) (Fin (d s)) ℝ :=
  fun i j => injectFirst d (s+1) n (fun k => -K s k j) i

/-- The exact block lower-bidiagonal matrix T, retaining the initial observation. -/
def transform (d : Nat → Nat)
    (K : ∀ j, Matrix (Fin (d (j+1))) (Fin (d j)) ℝ) (s : Nat) :
    (n : Nat) → Matrix (Ix d s n) (Ix d s n) ℝ
  | 0 => 1
  | n+1 => fromBlocks 1 0 (coupling d K s n) (transform d K (s+1) n)

theorem determinant_one (d : Nat → Nat)
    (K : ∀ j, Matrix (Fin (d (j+1))) (Fin (d j)) ℝ) (s n : Nat) :
    (transform d K s n).det = 1 := by
  induction n generalizing s with
  | zero => exact Matrix.det_one
  | succ n ih =>
    change (fromBlocks 1 0 (coupling d K s n) (transform d K (s+1) n)).det = 1
    rw [Matrix.det_fromBlocks_zero₁₂, Matrix.det_one, ih, one_mul]

theorem coupling_mulVec (d : Nat → Nat)
    (K : ∀ j, Matrix (Fin (d (j+1))) (Fin (d j)) ℝ) (s n : Nat)
    (a : Fin (d s) → ℝ) :
    coupling d K s n *ᵥ a = injectFirst d (s+1) n (-(K s *ᵥ a)) := by
  cases n with
  | zero => ext i; simp [coupling, injectFirst, Matrix.mulVec, dotProduct, Finset.sum_neg_distrib]
  | succ n =>
    funext i
    cases i <;> simp [coupling, injectFirst, Matrix.mulVec, dotProduct, Finset.sum_neg_distrib]

/-- Matrix multiplication equals the full retained-first-block residual recursion. -/
theorem transform_step (d : Nat → Nat)
    (K : ∀ j, Matrix (Fin (d (j+1))) (Fin (d j)) ℝ) (s n : Nat)
    (y : Ix d s (n+1) → ℝ) :
    transform d K s (n+1) *ᵥ y =
      Sum.elim (y ∘ Sum.inl)
        (injectFirst d (s+1) n (-(K s *ᵥ (y ∘ Sum.inl))) +
          transform d K (s+1) n *ᵥ (y ∘ Sum.inr)) := by
  change fromBlocks 1 0 (coupling d K s n) (transform d K (s+1) n) *ᵥ y = _
  rw [Matrix.fromBlocks_mulVec, Matrix.one_mulVec, Matrix.zero_mulVec, add_zero,
    coupling_mulVec]

end R9Block
#print axioms R9Block.determinant_one
#print axioms R9Block.transform_step
