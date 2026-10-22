import Mathlib

/-!
# L2-W1-A: variation-space kernel inclusion theorem

For a finite-dimensional real normed space `E`, arbitrary real normed spaces `Y`, `Z`,
a linear variation space `V ≤ E` and linear maps `B : E →ₗ Y`, `P : E →ₗ Z`:

  (∃ C ≥ 0, ∀ v ∈ V, ‖P v‖ ≤ C ‖B v‖)  ↔  (ker B ∩ V ⊆ ker P).

Proof of (←): restrict to `V`, factor `P|V` through `range (B|V)` via the first
isomorphism theorem, and use continuity of linear maps on the finite-dimensional
space `range (B|V)`; `C` is the operator norm of the factor map.

The negative control shows the iff must not be applied to bounded feasible sets.
-/

namespace L2W1KernelBound

variable {E Y Z : Type*}
  [NormedAddCommGroup E] [NormedSpace ℝ E] [FiniteDimensional ℝ E]
  [NormedAddCommGroup Y] [NormedSpace ℝ Y]
  [NormedAddCommGroup Z] [NormedSpace ℝ Z]

/-- Target 1: uniform kernel bound on a variation space iff kernel inclusion. -/
theorem kernel_bound_iff (V : Submodule ℝ E) (B : E →ₗ[ℝ] Y) (P : E →ₗ[ℝ] Z) :
    (∃ C : ℝ, 0 ≤ C ∧ ∀ v ∈ V, ‖P v‖ ≤ C * ‖B v‖) ↔ (∀ v ∈ V, B v = 0 → P v = 0) := by
  constructor
  · rintro ⟨C, -, hC⟩ v hv hB
    have h := hC v hv
    rw [hB, norm_zero, mul_zero] at h
    exact norm_le_zero_iff.mp h
  · intro h
    let B' : V →ₗ[ℝ] Y := B.domRestrict V
    let P' : V →ₗ[ℝ] Z := P.domRestrict V
    have hker : LinearMap.ker B' ≤ LinearMap.ker P' := by
      intro x hx
      rw [LinearMap.mem_ker] at hx ⊢
      exact h x x.2 hx
    let L₀ : LinearMap.range B' →ₗ[ℝ] Z :=
      ((LinearMap.ker B').liftQ P' hker).comp
        (B'.quotKerEquivRange.symm : LinearMap.range B' →ₗ[ℝ] V ⧸ LinearMap.ker B')
    have hL₀ : ∀ x : V, L₀ (B'.rangeRestrict x) = P' x := by
      intro x
      have hq : B'.quotKerEquivRange.symm (B'.rangeRestrict x) = Submodule.Quotient.mk x := by
        rw [LinearEquiv.symm_apply_eq, LinearMap.quotKerEquivRange_apply_mk]
        rfl
      show (LinearMap.ker B').liftQ P' hker (B'.quotKerEquivRange.symm (B'.rangeRestrict x)) = P' x
      rw [hq, Submodule.liftQ_apply]
    let L : LinearMap.range B' →L[ℝ] Z := LinearMap.toContinuousLinearMap L₀
    refine ⟨‖L‖, norm_nonneg _, fun v hv => ?_⟩
    have h1 : P v = L (B'.rangeRestrict ⟨v, hv⟩) := by
      rw [LinearMap.coe_toContinuousLinearMap', hL₀]
      rfl
    rw [h1]
    calc ‖L (B'.rangeRestrict ⟨v, hv⟩)‖ ≤ ‖L‖ * ‖B'.rangeRestrict ⟨v, hv⟩‖ := L.le_opNorm _
      _ = ‖L‖ * ‖B v‖ := rfl

/-- Target 2: affine domain `x0 + V` uses the declared variation space `V`. -/
theorem affine_kernel_bound (V : Submodule ℝ E) (B : E →ₗ[ℝ] Y) (P : E →ₗ[ℝ] Z) (x0 : E)
    (h : ∀ v ∈ V, B v = 0 → P v = 0) :
    ∃ C : ℝ, 0 ≤ C ∧ ∀ x y : E, x - x0 ∈ V → y - x0 ∈ V → ‖P x - P y‖ ≤ C * ‖B x - B y‖ := by
  obtain ⟨C, hC0, hC⟩ := (kernel_bound_iff V B P).mpr h
  refine ⟨C, hC0, fun x y hx hy => ?_⟩
  have hxy : x - y ∈ V := by
    have := V.sub_mem hx hy
    rwa [sub_sub_sub_cancel_right] at this
  rw [← map_sub, ← map_sub]
  exact hC _ hxy

/-- Target 3: trivial variation space branch. -/
theorem bot_branch (B : E →ₗ[ℝ] Y) (P : E →ₗ[ℝ] Z) :
    ∃ C : ℝ, 0 ≤ C ∧ ∀ v ∈ (⊥ : Submodule ℝ E), ‖P v‖ ≤ C * ‖B v‖ := by
  refine ⟨0, le_rfl, fun v hv => ?_⟩
  rw [Submodule.mem_bot] at hv
  subst hv
  simp

/-- Target 4: zero observation map branch. -/
theorem zero_B_branch (V : Submodule ℝ E) (P : E →ₗ[ℝ] Z) :
    (∃ C, 0 ≤ C ∧ ∀ v ∈ V, ‖P v‖ ≤ C * ‖(0 : E →ₗ[ℝ] Y) v‖) ↔ ∀ v ∈ V, P v = 0 := by
  rw [kernel_bound_iff V (0 : E →ₗ[ℝ] Y) P]
  simp

/-- Target 5: negative control. `B = 0`, `P = id` on `ℝ`, `K = [-1, 1]`: the image `P '' K`
is bounded although kernel inclusion fails, so the iff must not be applied to bounded
feasible sets. -/
theorem bounded_set_negative_control :
    Bornology.IsBounded ((LinearMap.id : ℝ →ₗ[ℝ] ℝ) '' Set.Icc (-1 : ℝ) 1) ∧
      ¬ (∀ v : ℝ, (0 : ℝ →ₗ[ℝ] ℝ) v = 0 → (LinearMap.id : ℝ →ₗ[ℝ] ℝ) v = 0) := by
  refine ⟨?_, ?_⟩
  · rw [LinearMap.coe_id, Set.image_id]
    exact Metric.isBounded_Icc (-1 : ℝ) 1
  · intro hall
    have h1 := hall 1 (by simp)
    simp at h1

end L2W1KernelBound
