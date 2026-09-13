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
  add_sub_cancel' : ∀ a b : α, a + b - b = a
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
      | nil =>
          calc
            residuals transport (reconstruct transport initial [residual]) =
                [residual + transport initial - transport initial] := rfl
            _ = [residual] := by rw [AddSubCancel.add_sub_cancel']
      | cons next tail =>
          calc
            residuals transport
                (reconstruct transport initial (residual :: next :: tail)) =
                (residual + transport initial - transport initial) ::
                  residuals transport
                    (reconstruct transport (residual + transport initial) (next :: tail)) := rfl
            _ = residual :: next :: tail := by
                rw [AddSubCancel.add_sub_cancel']
                rw [ih]

/-- Reconstructing from all residuals of a trajectory returns that trajectory. -/
theorem reconstruct_residuals {α : Type u} [AddSubCancel α] (transport : α → α)
    (initial : α) (tail : List α) :
    reconstruct transport initial (residuals transport (initial :: tail)) =
      initial :: tail := by
  induction tail generalizing initial with
  | nil => simp [reconstruct, residuals]
  | cons next tail ih =>
      calc
        reconstruct transport initial (residuals transport (initial :: next :: tail)) =
            initial :: reconstruct transport
              (next - transport initial + transport initial)
              (residuals transport (next :: tail)) := rfl
        _ = initial :: reconstruct transport next (residuals transport (next :: tail)) := by
            rw [AddSubCancel.sub_add_cancel']
        _ = initial :: next :: tail := by rw [ih]

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

/-- The transport can vary with depth while the state type remains homogeneous.
    A missing transport defaults to identity only outside the intended finite
    horizon, so the inverse lemmas below do not require an extra length premise. -/
def reconstructVarying {α : Type u} [AddSubCancel α]
    (transports : List (α → α)) (initial : α) : List α → List α
  | [] => [initial]
  | residual :: rest =>
      initial :: reconstructVarying transports.tail
        (residual + (transports.headD (fun x => x)) initial) rest

/-- Residuals aligned with a depth-indexed list of transports. -/
def residualsVarying {α : Type u} [AddSubCancel α]
    (transports : List (α → α)) : List α → List α
  | [] => []
  | [_] => []
  | first :: second :: rest =>
      (second - (transports.headD (fun x => x)) first) ::
        residualsVarying transports.tail (second :: rest)

/-- First inverse for finite, time-dependent homogeneous transports. -/
theorem residualsVarying_reconstructVarying {α : Type u} [AddSubCancel α]
    (transports : List (α → α)) (initial : α) (rs : List α) :
    residualsVarying transports (reconstructVarying transports initial rs) = rs := by
  induction rs generalizing initial transports with
  | nil => rfl
  | cons residual rest ih =>
      cases rest with
      | nil =>
          calc
            residualsVarying transports
                (reconstructVarying transports initial [residual]) =
                [residual + (transports.headD (fun x => x)) initial -
                  (transports.headD (fun x => x)) initial] := rfl
            _ = [residual] := by rw [AddSubCancel.add_sub_cancel']
      | cons next tail =>
          calc
            residualsVarying transports
                (reconstructVarying transports initial (residual :: next :: tail)) =
                (residual + (transports.headD (fun x => x)) initial -
                  (transports.headD (fun x => x)) initial) ::
                residualsVarying transports.tail
                  (reconstructVarying transports.tail
                    (residual + (transports.headD (fun x => x)) initial)
                    (next :: tail)) := rfl
            _ = residual :: next :: tail := by
                rw [AddSubCancel.add_sub_cancel']
                rw [ih]

/-- Second inverse for finite, time-dependent homogeneous transports. -/
theorem reconstructVarying_residualsVarying {α : Type u} [AddSubCancel α]
    (transports : List (α → α)) (initial : α) (tail : List α) :
    reconstructVarying transports initial
      (residualsVarying transports (initial :: tail)) = initial :: tail := by
  induction tail generalizing initial transports with
  | nil => rfl
  | cons next tail ih =>
      calc
        reconstructVarying transports initial
            (residualsVarying transports (initial :: next :: tail)) =
            initial :: reconstructVarying transports.tail
              (next - (transports.headD (fun x => x)) initial +
                (transports.headD (fun x => x)) initial)
              (residualsVarying transports.tail (next :: tail)) := rfl
        _ = initial :: reconstructVarying transports.tail next
              (residualsVarying transports.tail (next :: tail)) := by
                rw [AddSubCancel.sub_add_cancel']
        _ = initial :: next :: tail := by rw [ih]

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
  "{\"checks\":{\"D3_RECURSION_BOTH_INVERSES_ARBITRARY_BLOCKS\":false,\"D3_KERNEL_SURJECTIVITY_DETERMINANT\":false,\"D3_FULL_LAW_SUPPORT_PRESERVED\":false},\"domain_assumption_diff\":[\"Compiled inverse lemmas cover homogeneous state types with time-dependent transports, and one dependent-block composition. The reverse dependent-block composition, real rectangular-matrix determinant, and full mean/covariance/support preservation theorem remain unproved.\"],\"counterexample\":null}"

private def d2Payload : String :=
  "{\"checks\":{\"D2_GAUSSIAN_PUSHFORWARD_SUPPORT\":false,\"D2_SUPPORTED_PSEUDOINVERSE_CHISQUARE\":false,\"D2_RANK_ZERO_AND_OFF_SUPPORT\":false},\"domain_assumption_diff\":[\"No finite-dimensional real Gaussian, image-support, pseudoinverse, spectral whitening, or chi-square formalization is available in this core-Lean project.\"],\"counterexample\":null}"

private def d4Payload : String :=
  "{\"checks\":{\"D4_PSD_RANGE_SCHUR_SUPPORT\":false,\"D4_FULL_PAST_CONDITIONAL_GAUSSIAN\":false,\"D4_INNOVATION_INDEPENDENCE_AND_FIXED_LAW_LIMIT\":false},\"domain_assumption_diff\":[\"No finite-dimensional real Gaussian conditioning, Moore-Penrose inverse, Schur complement, or independence library is pinned in this core-Lean project.\"],\"counterexample\":null}"

/-- Contract runner.  It accepts exactly one proposition identifier and writes
    one JSON object to stdout. -/
def run (args : List String) : IO Unit := do
  match args with
  | ["D1"] => IO.println d1Payload
  | ["D3"] => IO.println d3Payload
  | ["D2"] => IO.println d2Payload
  | ["D4"] => IO.println d4Payload
  | _ =>
      IO.println "{\"checks\":{},\"domain_assumption_diff\":[\"expected exactly one of D1,D3,D2,D4\"],\"counterexample\":null}"
      IO.Process.exit 64

end DepthLean

def main (args : List String) : IO Unit := DepthLean.run args
