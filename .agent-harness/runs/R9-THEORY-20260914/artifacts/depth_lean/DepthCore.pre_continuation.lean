/-
  Bounded Lean evidence for R9 depth obligations.

  This file deliberately formalizes only the type-polymorphic finite-recursion
  core that Lean core can express without a finite-dimensional real-matrix or
  probability library.  The executable `main` marks every contract obligation
  false, because none of D1--D4 is fully established by these helper lemmas.
  In particular, this is not a formalization of a Gaussian law.
-/

namespace DepthLean

universe u v

/-- The sole algebraic law used by the reconstruction recursion.  Lean core
    does not provide the bundled additive-group hierarchy used by mathlib. -/
class AddSubCancel (α : Type u) extends Add α, Sub α where
  sub_add_cancel' : ∀ a b : α, a - b + b = a

/-- Rebuild a finite trajectory from its initial element and successive
    residuals for one fixed additive transport. -/
def reconstruct {α : Type u} [AddSubCancel α] (transport : α → α)
    (initial : α) : List α → List α
  | [] => [initial]
  | residual :: rest => initial :: reconstruct transport (residual + transport initial) rest

/-- Consecutive residuals of a nonempty finite trajectory. -/
def residuals {α : Type u} [AddSubCancel α] (transport : α → α) : List α → List α
  | [] => []
  | [_] => []
  | first :: second :: rest =>
      (second - transport first) :: residuals transport (second :: rest)

/-- Taking residuals after reconstruction returns the input residual list. -/
theorem residuals_reconstruct {α : Type u} [AddSubCancel α] (transport : α → α)
    (initial : α) (rs : List α) :
    residuals transport (reconstruct transport initial rs) = rs := by
  induction rs generalizing initial with
  | nil => simp [reconstruct, residuals]
  | cons residual rest ih =>
      cases rest with
      | nil => simp [reconstruct, residuals]
      | cons next tail =>
          simp [reconstruct, residuals, ih]

/-- Reconstructing from all residuals of a trajectory returns that trajectory. -/
theorem reconstruct_residuals {α : Type u} [AddSubCancel α] (transport : α → α)
    (initial : α) (tail : List α) :
    reconstruct transport initial (residuals transport (initial :: tail)) =
      initial :: tail := by
  induction tail generalizing initial with
  | nil => simp [reconstruct, residuals]
  | cons next tail ih =>
      simp [reconstruct, residuals, AddSubCancel.sub_add_cancel', ih]

/-- The residual operation is surjective onto each finite residual list once
    an initial state is retained. -/
theorem residuals_surjective {α : Type u} [AddSubCancel α] (transport : α → α)
    (initial : α) (rs : List α) :
    ∃ ys, residuals transport ys = rs := by
  exact ⟨reconstruct transport initial rs,
    residuals_reconstruct transport initial rs⟩

/-- A precise homogeneous-state kernel/reconstruction equivalence. -/
theorem residuals_eq_iff_reconstruct {α : Type u} [AddSubCancel α]
    (transport : α → α) (initial : α) (tail rs : List α) :
    residuals transport (initial :: tail) = rs ↔
      reconstruct transport initial rs = initial :: tail := by
  constructor
  · intro h
    rw [← h]
    exact reconstruct_residuals transport initial tail
  · intro h
    rw [← h]
    exact residuals_reconstruct transport initial rs

/-- Abstract quadratic-form pullback positivity.  It is the logical core of
    the PSD pullback step, but deliberately has no matrices or real scalars. -/
theorem nonnegative_pullback {α : Type u} {β : Type v}
    (quadratic : α → Int) (map : β → α)
    (h_nonnegative : ∀ x, 0 ≤ quadratic x) :
    ∀ z, 0 ≤ quadratic (map z) := by
  intro z
  exact h_nonnegative (map z)

private def d1Payload : String :=
  "{\"checks\":{\"D1_MEAN_COVARIANCE_LINEAR_MAP\":false,\"D1_ALL_CROSS_STEP_BLOCKS\":false,\"D1_PSD_PULLBACK_GENERAL_DIMENSION\":false},\"domain_assumption_diff\":[\"Only an abstract Int-valued pullback positivity helper is compiled; the project has no pinned finite-dimensional real matrix/covariance formalization.\"],\"counterexample\":null}"

private def d3Payload : String :=
  "{\"checks\":{\"D3_RECURSION_BOTH_INVERSES_ARBITRARY_BLOCKS\":false,\"D3_KERNEL_SURJECTIVITY_DETERMINANT\":false,\"D3_FULL_LAW_SUPPORT_PRESERVED\":false},\"domain_assumption_diff\":[\"Compiled helpers cover one homogeneous state type with a named sub-add cancellation law and one fixed transport. They omit arbitrary dependent block dimensions, rectangular real matrices, determinant, and full mean/covariance/support preservation.\"],\"counterexample\":null}"

private def d2Payload : String :=
  "{\"checks\":{\"D2_GAUSSIAN_PUSHFORWARD_SUPPORT\":false,\"D2_SUPPORTED_PSEUDOINVERSE_CHISQUARE\":false,\"D2_RANK_ZERO_AND_OFF_SUPPORT\":false},\"domain_assumption_diff\":[\"No finite-dimensional real Gaussian, image-support, pseudoinverse, spectral whitening, or chi-square formalization is available in this core-Lean project.\"],\"counterexample\":null}"

private def d4Payload : String :=
  "{\"checks\":{\"D4_PSD_RANGE_SCHUR_SUPPORT\":false,\"D4_FULL_PAST_CONDITIONAL_GAUSSIAN\":false,\"D4_INNOVATION_INDEPENDENCE_AND_FIXED_LAW_LIMIT\":false},\"domain_assumption_diff\":[\"No finite-dimensional real Gaussian conditioning, Moore-Penrose inverse, Schur complement, or independence library is pinned in this core-Lean project.\"],\"counterexample\":null}"

/-- Contract runner.  It accepts exactly one proposition identifier and writes
    one JSON object to stdout. -/
def main (args : List String) : IO Unit := do
  match args with
  | ["D1"] => IO.println d1Payload
  | ["D3"] => IO.println d3Payload
  | ["D2"] => IO.println d2Payload
  | ["D4"] => IO.println d4Payload
  | _ =>
      IO.println "{\"checks\":{},\"domain_assumption_diff\":[\"expected exactly one of D1,D3,D2,D4\"],\"counterexample\":null}"
      IO.Process.exit 64

end DepthLean
