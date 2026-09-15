import Mathlib.Data.Real.Basic
import Mathlib.Data.Matrix.Block
import Mathlib.LinearAlgebra.Matrix.NonsingularInverse
import Mathlib.LinearAlgebra.Matrix.ToLin

/- R9 D3: explicit ordered, heterogeneous finite block coordinates.
This formalizes a prior deterministic result; it does not admit Gaussian laws. -/
set_option autoImplicit false
open Matrix
namespace R9Block

abbrev Ix (d : Nat → Nat) (s : Nat) : Nat → Type
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


theorem transform_bijective (d : Nat → Nat)
    (K : ∀ j, Matrix (Fin (d (j+1))) (Fin (d j)) ℝ) (s n : Nat) :
    Function.Bijective (fun y => transform d K s n *ᵥ y) := by
  let M := transform d K s n
  have h : IsUnit M.det := by dsimp [M]; rw [determinant_one]; exact isUnit_one
  have left : Function.LeftInverse (fun y => M⁻¹ *ᵥ y) (fun y => M *ᵥ y) := by
    intro y
    dsimp only
    rw [Matrix.mulVec_mulVec, Matrix.nonsing_inv_mul _ h, Matrix.one_mulVec]
  have right : Function.RightInverse (fun y => M⁻¹ *ᵥ y) (fun y => M *ᵥ y) := by
    intro y
    dsimp only
    rw [Matrix.mulVec_mulVec, Matrix.mul_nonsing_inv _ h, Matrix.one_mulVec]
  exact ⟨left.injective, right.surjective⟩

/-- The homogeneous trajectory, propagating the whole initial block. -/
def propagated (d : Nat → Nat)
    (K : ∀ j, Matrix (Fin (d (j+1))) (Fin (d j)) ℝ) (s : Nat) :
    (n : Nat) → (Fin (d s) → ℝ) → Ix d s n → ℝ
  | 0, a => a
  | n+1, a => Sum.elim a (propagated d K (s+1) n (K s *ᵥ a))

theorem inject_neg_add (d : Nat → Nat) (s n : Nat) (a : Fin (d s) → ℝ) :
    injectFirst d s n (-a) + injectFirst d s n a = 0 := by
  cases n with
  | zero => exact neg_add_cancel a
  | succ n => funext i; cases i <;> simp [injectFirst, Pi.add_apply, Pi.neg_apply]

theorem transform_propagated (d : Nat → Nat)
    (K : ∀ j, Matrix (Fin (d (j+1))) (Fin (d j)) ℝ) (s n : Nat)
    (a : Fin (d s) → ℝ) :
    transform d K s n *ᵥ propagated d K s n a = injectFirst d s n a := by
  induction n generalizing s with
  | zero => simp [transform, propagated, injectFirst]
  | succ n ih =>
    rw [transform_step]
    change Sum.elim a (injectFirst d (s+1) n (-(K s *ᵥ a)) +
      transform d K (s+1) n *ᵥ propagated d K (s+1) n (K s *ᵥ a)) = _
    rw [ih, inject_neg_add]
    rfl

/-- H contains every non-initial row of T. -/
def contrastMatrix (d : Nat → Nat)
    (K : ∀ j, Matrix (Fin (d (j+1))) (Fin (d j)) ℝ) (s n : Nat) :
    Matrix (Ix d (s+1) n) (Ix d s (n+1)) ℝ :=
  (transform d K s (n+1)).submatrix Sum.inr id

theorem contrast_apply (d : Nat → Nat)
    (K : ∀ j, Matrix (Fin (d (j+1))) (Fin (d j)) ℝ) (s n : Nat)
    (y : Ix d s (n+1) → ℝ) :
    contrastMatrix d K s n *ᵥ y = (transform d K s (n+1) *ᵥ y) ∘ Sum.inr := by
  rfl

theorem contrast_surjective (d : Nat → Nat)
    (K : ∀ j, Matrix (Fin (d (j+1))) (Fin (d j)) ℝ) (s n : Nat) :
    Function.Surjective (fun y => contrastMatrix d K s n *ᵥ y) := by
  intro z
  obtain ⟨y, hy⟩ := (transform_bijective d K s (n+1)).surjective (Sum.elim 0 z)
  refine ⟨y, ?_⟩
  dsimp only at hy ⊢
  rw [contrast_apply, hy]
  rfl

/-- No additional null directions: zero contrasts are exactly propagated initial states. -/
theorem kernel_iff_propagated (d : Nat → Nat)
    (K : ∀ j, Matrix (Fin (d (j+1))) (Fin (d j)) ℝ) (s n : Nat)
    (y : Ix d s (n+1) → ℝ) :
    contrastMatrix d K s n *ᵥ y = 0 ↔
      y = propagated d K s (n+1) (y ∘ Sum.inl) := by
  constructor
  · intro h
    apply (transform_bijective d K s (n+1)).injective
    dsimp only
    rw [transform_propagated]
    funext i
    cases i with
    | inl j =>
      rw [transform_step d K s n y]
      rfl
    | inr j => exact congrFun h j
  · intro h
    have heq := congrArg (fun x => transform d K s (n+1) *ᵥ x) h
    rw [transform_propagated] at heq
    rw [contrast_apply, heq]
    rfl

/-- Zero depth has no contrast coordinates: the zero-row H is onto the singleton
empty-vector space and its kernel is the entire initial-state space. -/
theorem zero_depth_contrasts (d : Nat → Nat) (s : Nat) :
    Function.Surjective (fun y : Ix d s 0 → ℝ =>
      (0 : Matrix (Fin 0) (Ix d s 0) ℝ) *ᵥ y) ∧
    ∀ y : Ix d s 0 → ℝ, (0 : Matrix (Fin 0) (Ix d s 0) ℝ) *ᵥ y = 0 := by
  constructor
  · intro z; exact ⟨0, Subsingleton.elim _ _⟩
  · intro y; exact Matrix.zero_mulVec y

end R9Block
#print axioms R9Block.determinant_one
#print axioms R9Block.transform_step

#print axioms R9Block.transform_bijective
#print axioms R9Block.transform_propagated
#print axioms R9Block.contrast_surjective
#print axioms R9Block.kernel_iff_propagated
