import CAS07M05Accepted

/-!
# G01-A: frame-level Jacobi vertex, Taylor order, screen transition

Scope (see `FROZEN_TARGETS.md`): everything below lives in a fixed parallel
orthonormal screen frame.  `ScreenFrameData` is the recovered *source definition*
(affine parameter interval `[0,L]` and optical tidal operator field `R`); it is
NOT derived here from a Lorentzian manifold.  Sign convention: `D'' = -R D`
(FINITE_DISTANCE_THEOREM.md), i.e. the `jacobi` field of `CAS07M05.JacobiPremises`.
-/

/- Instance search on operators of `EuclideanSpace ℝ (Fin 2)` exceeds the default
budget; the same setting is used by the accepted CAS07 M04 module.  It raises a
resource limit only and does not suppress any error. -/
set_option synthInstance.maxHeartbeats 400000

noncomputable section

open Set MeasureTheory intervalIntegral
open scoped NNReal

namespace G01A

open Cas07M04

local notation "id₂" => ContinuousLinearMap.id ℝ Plane

/-- Recovered source definition, frame level: optical tidal operator field in a
parallel orthonormal screen frame along an affine-parameter segment `[0,L]`. -/
structure ScreenFrameData (K L : ℝ) where
  R : ℝ → Op
  continuous_R : ContinuousOn R (Icc 0 L)
  curvature_bound : ∀ t ∈ Icc 0 L, ‖R t‖ ≤ K

/-! ## T0 sign notation -/

/-- OPTICAL_THEOREMS writes `J'' = ℛ J`; with the *definition* `ℛ := -Ropt` this is
exactly the FINITE_DISTANCE form `D'' = -Ropt D`. -/
theorem optical_sign_bridge (Ropt : ℝ → Op) (D2 D : Op) (t : ℝ) :
    D2 = (-(Ropt t)).comp D ↔ D2 = -(Ropt t).comp D := by
  rw [ContinuousLinearMap.neg_comp]

/-! ## T1 first-order system -/

/-- First-order Jacobi vector field on `Y = (D, D')`. -/
def jacobiField (R : ℝ → Op) (t : ℝ) (Y : Op × Op) : Op × Op := (Y.2, -(R t).comp Y.1)

theorem first_order_iff {L : ℝ} (R D D1 : ℝ → Op) :
    (∀ t ∈ Icc 0 L, HasDerivWithinAt D (D1 t) (Icc 0 L) t ∧
        HasDerivWithinAt D1 (-(R t).comp (D t)) (Icc 0 L) t) ↔
      ∀ t ∈ Icc 0 L,
        HasDerivWithinAt (fun u => (D u, D1 u)) (jacobiField R t (D t, D1 t)) (Icc 0 L) t := by
  constructor
  · intro h t ht
    exact (h t ht).1.prodMk (h t ht).2
  · intro h t ht
    have h1 := (ContinuousLinearMap.fst ℝ Op Op).hasFDerivAt.comp_hasDerivWithinAt t (h t ht)
    have h2 := (ContinuousLinearMap.snd ℝ Op Op).hasFDerivAt.comp_hasDerivWithinAt t (h t ht)
    exact ⟨h1, h2⟩

/-- Columns of the matrix solution are vector Jacobi fields with `J(0)v=0`, `J'(0)v=v`. -/
theorem column_jacobi_field {K L : ℝ} (J : CAS07M05.JacobiPremises K L) (v : Plane) :
    (J.D 0 v = 0 ∧ J.D1 0 v = v) ∧
    ∀ t ∈ Icc 0 L, HasDerivWithinAt (fun u => J.D u v) (J.D1 t v) (Icc 0 L) t ∧
      HasDerivWithinAt (fun u => J.D1 u v) (-(J.R t) (J.D t v)) (Icc 0 L) t := by
  refine ⟨⟨by simp [J.D_zero], by simp [J.D1_zero]⟩, fun t ht => ⟨?_, ?_⟩⟩
  · exact (ContinuousLinearMap.apply ℝ Plane v).hasFDerivAt.comp_hasDerivWithinAt t
      (J.deriv_D t ht)
  · have h := (ContinuousLinearMap.apply ℝ Plane v).hasFDerivAt.comp_hasDerivWithinAt t
      (J.deriv_D1 t ht)
    have e : (ContinuousLinearMap.apply ℝ Plane v) (-(J.R t).comp (J.D t)) =
        -(J.R t) (J.D t v) := by simp
    rw [J.jacobi t ht, e] at h
    exact h

/-- The first-order field is globally Lipschitz when `‖R t‖ ≤ K`. -/
theorem field_lipschitz (R : ℝ → Op) (t : ℝ) {K : ℝ} (hA : ‖R t‖ ≤ K) :
    LipschitzWith (Real.toNNReal (max 1 K)) (jacobiField R t) := by
  apply LipschitzWith.of_dist_le_mul
  intro x y
  have hM : ((Real.toNNReal (max 1 K) : ℝ≥0) : ℝ) = max 1 K :=
    Real.coe_toNNReal _ (le_trans zero_le_one (le_max_left _ _))
  rw [hM]
  have hx1 : dist x.1 y.1 ≤ dist x y := by rw [Prod.dist_eq]; exact le_max_left _ _
  have hx2 : dist x.2 y.2 ≤ dist x y := by rw [Prod.dist_eq]; exact le_max_right _ _
  have hd : 0 ≤ dist x y := dist_nonneg
  rw [Prod.dist_eq]
  apply max_le
  · calc dist (jacobiField R t x).1 (jacobiField R t y).1 = dist x.2 y.2 := rfl
      _ ≤ dist x y := hx2
      _ ≤ max 1 K * dist x y := le_mul_of_one_le_left hd (le_max_left _ _)
  · calc dist (jacobiField R t x).2 (jacobiField R t y).2
          = ‖(R t).comp (x.1 - y.1)‖ := by
            simp only [jacobiField]
            rw [dist_neg_neg, dist_eq_norm, ContinuousLinearMap.comp_sub]
      _ ≤ ‖R t‖ * ‖x.1 - y.1‖ := ContinuousLinearMap.opNorm_comp_le _ _
      _ ≤ K * dist x y := by
            rw [← dist_eq_norm]
            exact mul_le_mul hA hx1 dist_nonneg (le_trans (norm_nonneg _) hA)
      _ ≤ max 1 K * dist x y := mul_le_mul_of_nonneg_right (le_max_right _ _) hd

/-! ## Global existence for a globally Lipschitz linear-growth field (gluing Picard-Lindelöf) -/

section Global

variable {E : Type*} [NormedAddCommGroup E] [NormedSpace ℝ E] [CompleteSpace E]

theorem ode_extend (F : ℝ → E → E) (M : ℝ≥0) (hM : 0 < M)
    (hlip : ∀ t, LipschitzWith M (F t)) (hcont : ∀ x, Continuous fun t => F t x)
    (h0 : ∀ t, F t 0 = 0) {T : ℝ} (hT : 0 ≤ T) (α : ℝ → E)
    (hα : ∀ t ∈ Icc 0 T, HasDerivWithinAt α (F t (α t)) (Icc 0 T) t) :
    ∃ β : ℝ → E, β 0 = α 0 ∧ ∀ t ∈ Icc 0 (T + 1 / (2 * (M : ℝ))),
      HasDerivWithinAt β (F t (β t)) (Icc 0 (T + 1 / (2 * (M : ℝ)))) t := by
  have hMpos : (0 : ℝ) < M := hM
  set h : ℝ := 1 / (2 * (M : ℝ)) with hh
  have hpos : 0 < h := by positivity
  set y := α T with hy
  have hT0 : T ∈ Icc T (T + h) := ⟨le_refl _, by linarith⟩
  have hPL : IsPicardLindelof F (tmin := T) (tmax := T + h) ⟨T, hT0⟩ y ‖y‖₊ 0
      (M * (‖y‖₊ + ‖y‖₊)) M := by
    refine ⟨fun t _ => (hlip t).lipschitzOnWith, fun x _ => (hcont x).continuousOn, ?_, ?_⟩
    · intro t _ x hx
      have h1 : ‖F t x‖ ≤ M * ‖x‖ := by
        have := (hlip t).dist_le_mul x 0
        simpa [h0, dist_zero_right] using this
      have hx' : ‖x - y‖ ≤ ‖y‖ := by
        rw [Metric.mem_closedBall, dist_eq_norm] at hx
        simpa using hx
      have h2 : ‖x‖ ≤ ‖y‖ + ‖y‖ := by
        calc ‖x‖ = ‖(x - y) + y‖ := by rw [sub_add_cancel]
          _ ≤ ‖x - y‖ + ‖y‖ := norm_add_le _ _
          _ ≤ ‖y‖ + ‖y‖ := by linarith
      push_cast
      calc ‖F t x‖ ≤ M * ‖x‖ := h1
        _ ≤ M * (‖y‖ + ‖y‖) := mul_le_mul_of_nonneg_left h2 hMpos.le
    · show ((M * (‖y‖₊ + ‖y‖₊) : ℝ≥0) : ℝ) * max (T + h - T) (T - T) ≤ ((‖y‖₊ : ℝ≥0) : ℝ) - ((0 : ℝ≥0) : ℝ)
      have e1 : max (T + h - T) (T - T) = h := by
        rw [add_sub_cancel_left, sub_self]; exact max_eq_left hpos.le
      rw [e1]
      push_cast
      rw [hh]
      field_simp
      linarith [norm_nonneg y]
  obtain ⟨γ, hγ0, hγ⟩ := hPL.exists_eq_forall_mem_Icc_hasDerivWithinAt₀
  have hγT : γ T = α T := hγ0
  refine ⟨fun t => if t ≤ T then α t else γ t, by simp [hT], ?_⟩
  have hglue : ∀ x ∈ Icc T (T + h), (if x ≤ T then α x else γ x) = γ x := by
    intro x hx
    split_ifs with hxT
    · have : x = T := le_antisymm hxT hx.1
      rw [this, hγT]
    · rfl
  intro t ht
  have hU : Icc 0 (T + h) = Icc 0 T ∪ Icc T (T + h) :=
    (Icc_union_Icc_eq_Icc hT (by linarith)).symm
  rw [hU]
  apply HasDerivWithinAt.union
  · by_cases ht1 : t ∈ Icc 0 T
    · have e : (if t ≤ T then α t else γ t) = α t := if_pos ht1.2
      beta_reduce
      rw [e]
      exact (hα t ht1).congr (fun x hx => if_pos hx.2) (if_pos ht1.2)
    · have hncl : t ∉ closure (Icc 0 T) := by rwa [isClosed_Icc.closure_eq]
      exact (hasDerivWithinAt_iff_hasFDerivWithinAt).2 (HasFDerivWithinAt.of_notMem_closure hncl)
  · by_cases ht2 : t ∈ Icc T (T + h)
    · beta_reduce
      rw [hglue t ht2]
      exact (hγ t ht2).congr (fun x hx => hglue x hx) (hglue t ht2)
    · have hncl : t ∉ closure (Icc T (T + h)) := by rwa [isClosed_Icc.closure_eq]
      exact (hasDerivWithinAt_iff_hasFDerivWithinAt).2 (HasFDerivWithinAt.of_notMem_closure hncl)

theorem ode_global (F : ℝ → E → E) (M : ℝ≥0) (hM : 0 < M)
    (hlip : ∀ t, LipschitzWith M (F t)) (hcont : ∀ x, Continuous fun t => F t x)
    (h0 : ∀ t, F t 0 = 0) (y0 : E) (L : ℝ) (hL : 0 ≤ L) :
    ∃ α : ℝ → E, α 0 = y0 ∧ ∀ t ∈ Icc 0 L, HasDerivWithinAt α (F t (α t)) (Icc 0 L) t := by
  have hMpos : (0 : ℝ) < M := hM
  have hpos : (0 : ℝ) < 1 / (2 * (M : ℝ)) := by positivity
  have key : ∀ n : ℕ, ∃ α : ℝ → E, α 0 = y0 ∧
      ∀ t ∈ Icc 0 ((n : ℝ) * (1 / (2 * (M : ℝ)))),
        HasDerivWithinAt α (F t (α t)) (Icc 0 ((n : ℝ) * (1 / (2 * (M : ℝ))))) t := by
    intro n
    induction n with
    | zero =>
      refine ⟨fun _ => y0, rfl, ?_⟩
      intro t _
      have hsub : (Icc (0 : ℝ) (((0 : ℕ) : ℝ) * (1 / (2 * (M : ℝ))))).Subsingleton := by
        simp
      exact (hasDerivWithinAt_iff_hasFDerivWithinAt).2 (HasFDerivWithinAt.of_subsingleton hsub)
    | succ n ih =>
      obtain ⟨α, hα0, hα⟩ := ih
      obtain ⟨β, hβ0, hβ⟩ := ode_extend F M hM hlip hcont h0 (by positivity) α hα
      refine ⟨β, hβ0.trans hα0, ?_⟩
      have e : ((n + 1 : ℕ) : ℝ) * (1 / (2 * (M : ℝ))) =
          (n : ℝ) * (1 / (2 * (M : ℝ))) + 1 / (2 * (M : ℝ)) := by push_cast; ring
      rw [e]
      exact hβ
  obtain ⟨n, hn⟩ := exists_nat_ge (L / (1 / (2 * (M : ℝ))))
  obtain ⟨α, hα0, hα⟩ := key n
  have hle : L ≤ (n : ℝ) * (1 / (2 * (M : ℝ))) := by
    rwa [div_le_iff₀ hpos] at hn
  have hsub : Icc 0 L ⊆ Icc 0 ((n : ℝ) * (1 / (2 * (M : ℝ)))) := Icc_subset_Icc_right hle
  exact ⟨α, hα0, fun t ht => (hα t (hsub ht)).mono hsub⟩

end Global

/-! ## Clamp extension of the tidal field -/

/-- Extension of `R` from `[0,L]` to `ℝ` by clamping the parameter. -/
def clampR (R : ℝ → Op) (L : ℝ) (t : ℝ) : Op := R (max 0 (min t L))

theorem clamp_mem {L : ℝ} (hL : 0 ≤ L) (t : ℝ) : max 0 (min t L) ∈ Icc 0 L :=
  ⟨le_max_left _ _, max_le hL (min_le_right _ _)⟩

theorem clampR_eq {R : ℝ → Op} {L t : ℝ} (ht : t ∈ Icc 0 L) : clampR R L t = R t := by
  simp [clampR, min_eq_left ht.2, max_eq_right ht.1]

/-! ## T2 existence: frame data ↦ every field of `CAS07M05.JacobiPremises` -/

theorem exists_jacobi {K L : ℝ} (F : ScreenFrameData K L) (hL : 0 < L) :
    ∃ J : CAS07M05.JacobiPremises K L, J.R = F.R := by
  have hRc : Continuous (clampR F.R L) :=
    F.continuous_R.comp_continuous
      (continuous_const.max (continuous_id.min continuous_const)) (clamp_mem hL.le)
  have hb : ∀ t, ‖clampR F.R L t‖ ≤ K := fun t => F.curvature_bound _ (clamp_mem hL.le t)
  have hM : (0 : ℝ≥0) < Real.toNNReal (max 1 K) := by
    rw [Real.toNNReal_pos]; exact lt_max_of_lt_left one_pos
  have hcont : ∀ x : Op × Op, Continuous fun t => jacobiField (clampR F.R L) t x := by
    intro x
    exact continuous_const.prodMk ((hRc.clm_comp continuous_const).neg)
  obtain ⟨α, hα0, hα⟩ := ode_global (jacobiField (clampR F.R L)) (Real.toNNReal (max 1 K)) hM
    (fun t => field_lipschitz (clampR F.R L) t (hb t)) hcont
    (fun t => by simp [jacobiField]) ((0 : Op), id₂) L hL.le
  have hD : ∀ t ∈ Icc 0 L, HasDerivWithinAt (fun u => (α u).1) ((α t).2) (Icc 0 L) t :=
    fun t ht => (ContinuousLinearMap.fst ℝ Op Op).hasFDerivAt.comp_hasDerivWithinAt t (hα t ht)
  have hD1 : ∀ t ∈ Icc 0 L,
      HasDerivWithinAt (fun u => (α u).2) (-(F.R t).comp (α t).1) (Icc 0 L) t := by
    intro t ht
    have h := (ContinuousLinearMap.snd ℝ Op Op).hasFDerivAt.comp_hasDerivWithinAt t (hα t ht)
    have e : (ContinuousLinearMap.snd ℝ Op Op) (jacobiField (clampR F.R L) t (α t)) =
        -(F.R t).comp (α t).1 := by
      simp [jacobiField, clampR_eq ht]
    rw [e] at h
    exact h
  have hDc : ContinuousOn (fun u => (α u).1) (Icc 0 L) := HasDerivWithinAt.continuousOn hD
  exact ⟨{ D := fun u => (α u).1
           D1 := fun u => (α u).2
           D2 := fun u => -(F.R u).comp (α u).1
           R := F.R
           deriv_D := hD
           deriv_D1 := hD1
           continuous_D2 := (F.continuous_R.clm_comp hDc).neg
           continuous_R := F.continuous_R
           D_zero := by simp [hα0]
           D1_zero := by simp [hα0]
           jacobi := fun _ _ => rfl
           curvature_bound := F.curvature_bound }, rfl⟩

/-! ## T3 uniqueness -/

theorem jacobi_unique {K L : ℝ} (J₁ J₂ : CAS07M05.JacobiPremises K L)
    (hR : ∀ t ∈ Icc 0 L, J₁.R t = J₂.R t) :
    ∀ t ∈ Icc 0 L, J₁.D t = J₂.D t ∧ J₁.D1 t = J₂.D1 t ∧ J₁.D2 t = J₂.D2 t := by
  have hderiv : ∀ J : CAS07M05.JacobiPremises K L, (∀ t ∈ Icc 0 L, J.R t = J₁.R t) →
      ∀ t ∈ Icc 0 L, HasDerivWithinAt (fun u => (J.D u, J.D1 u))
        (jacobiField J₁.R t (J.D t, J.D1 t)) (Icc 0 L) t := by
    intro J hJ t ht
    have h := (J.deriv_D t ht).prodMk (J.deriv_D1 t ht)
    rw [J.jacobi t ht, hJ t ht] at h
    exact h
  have h1 := hderiv J₁ (fun _ _ => rfl)
  have h2 := hderiv J₂ (fun t ht => (hR t ht).symm)
  have heq := ODE_solution_unique_of_mem_Icc_right (v := jacobiField J₁.R)
    (s := fun _ => (univ : Set (Op × Op))) (K := Real.toNNReal (max 1 K))
    (fun t ht => (field_lipschitz J₁.R t
      (J₁.curvature_bound t (Ico_subset_Icc_self ht))).lipschitzOnWith)
    (HasDerivWithinAt.continuousOn h1)
    (fun t ht => (h1 t (Ico_subset_Icc_self ht)).mono_of_mem_nhdsWithin
      (Icc_mem_nhdsGE_of_mem ht))
    (fun _ _ => mem_univ _)
    (HasDerivWithinAt.continuousOn h2)
    (fun t ht => (h2 t (Ico_subset_Icc_self ht)).mono_of_mem_nhdsWithin
      (Icc_mem_nhdsGE_of_mem ht))
    (fun _ _ => mem_univ _)
    (by simp [J₁.D_zero, J₂.D_zero, J₁.D1_zero, J₂.D1_zero])
  intro t ht
  have h := heq ht
  simp only [Prod.mk.injEq] at h
  refine ⟨h.1, h.2, ?_⟩
  rw [J₁.jacobi t ht, J₂.jacobi t ht, h.1, hR t ht]

/-! ## T4 vertex jet -/

theorem vertex_jet {K L : ℝ} (J : CAS07M05.JacobiPremises K L) (hL : 0 ≤ L) :
    J.D 0 = 0 ∧ J.D1 0 = id₂ ∧ J.D2 0 = 0 := by
  refine ⟨J.D_zero, J.D1_zero, ?_⟩
  rw [J.jacobi 0 ⟨le_refl _, hL⟩, J.D_zero]
  simp

/-! ## T5 exact integral remainder (reuse of accepted M04 Volterra identity) -/

theorem integral_remainder {K L : ℝ} (J : CAS07M05.JacobiPremises K L) :
    ∀ s ∈ Icc 0 L, J.D s = s • id₂ - ∫ t in (0:ℝ)..s, (s - t) • (J.R t).comp (J.D t) :=
  fun s hs => Cas07M04.volterra_identity hs.1 hs.2 J.deriv_D J.deriv_D1 J.continuous_D2
    J.D_zero J.D1_zero J.jacobi

/-! ## T6 cubic order -/

theorem integral_kernel (s : ℝ) : ∫ t in (0:ℝ)..s, (s - t) * t = s ^ 3 / 6 := by
  have hder : ∀ x ∈ uIcc (0:ℝ) s,
      HasDerivAt (fun t => s * t ^ 2 / 2 - t ^ 3 / 3) ((s - x) * x) x := by
    intro x _
    have h1 := ((hasDerivAt_pow 2 x).const_mul s).div_const 2
    have h2 := (hasDerivAt_pow 3 x).div_const 3
    convert h1.sub h2 using 1
    norm_num
    ring
  rw [integral_eq_sub_of_hasDerivAt hder (by apply Continuous.intervalIntegrable; fun_prop)]
  beta_reduce
  ring

theorem norm_D_le_linear {K L : ℝ} (J : CAS07M05.JacobiPremises K L) :
    ∃ B : ℝ, 0 ≤ B ∧ ∀ t ∈ Icc 0 L, ‖J.D t‖ ≤ B * t := by
  have hD1c : ContinuousOn J.D1 (Icc 0 L) := HasDerivWithinAt.continuousOn J.deriv_D1
  obtain ⟨B, hB⟩ := isCompact_Icc.exists_bound_of_continuousOn hD1c
  refine ⟨max B 0, le_max_right _ _, fun t ht => ?_⟩
  have h := norm_image_sub_le_of_norm_deriv_le_segment' (C := max B 0) J.deriv_D
    (fun x hx => (hB x (Ico_subset_Icc_self hx)).trans (le_max_left B 0)) t ht
  simpa [J.D_zero] using h

theorem cubic_bound {K L : ℝ} (J : CAS07M05.JacobiPremises K L) (hK : 0 ≤ K) :
    ∃ C : ℝ, 0 ≤ C ∧ ∀ s ∈ Icc 0 L, ‖J.D s - s • id₂‖ ≤ C * s ^ 3 := by
  obtain ⟨B, hB0, hB⟩ := norm_D_le_linear J
  refine ⟨K * B / 6, by positivity, fun s hs => ?_⟩
  have hV := integral_remainder J s hs
  have hEq : J.D s - s • id₂ = -∫ t in (0:ℝ)..s, (s - t) • (J.R t).comp (J.D t) := by
    rw [hV]; abel
  rw [hEq, norm_neg]
  have hsub : Icc 0 s ⊆ Icc 0 L := Icc_subset_Icc_right hs.2
  calc ‖∫ t in (0:ℝ)..s, (s - t) • (J.R t).comp (J.D t)‖
        ≤ ∫ t in (0:ℝ)..s, K * B * ((s - t) * t) := by
          apply intervalIntegral.norm_integral_le_of_norm_le hs.1
          · filter_upwards with t ht
            have htL : t ∈ Icc 0 L := hsub ⟨ht.1.le, ht.2⟩
            have hst : 0 ≤ s - t := sub_nonneg.2 ht.2
            rw [norm_smul, Real.norm_eq_abs, abs_of_nonneg hst]
            calc (s - t) * ‖(J.R t).comp (J.D t)‖
                  ≤ (s - t) * (‖J.R t‖ * ‖J.D t‖) :=
                    mul_le_mul_of_nonneg_left (ContinuousLinearMap.opNorm_comp_le _ _) hst
              _ ≤ (s - t) * (K * (B * t)) :=
                    mul_le_mul_of_nonneg_left
                      (mul_le_mul (J.curvature_bound t htL) (hB t htL) (norm_nonneg _) hK) hst
              _ = K * B * ((s - t) * t) := by ring
          · apply Continuous.intervalIntegrable; fun_prop
    _ = K * B / 6 * s ^ 3 := by
          rw [intervalIntegral.integral_const_mul, integral_kernel]; ring

/-! ## T7 cubic vertex coefficient -/

theorem cubic_jet_identity {K L : ℝ} (J : CAS07M05.JacobiPremises K L) :
    ∀ s ∈ Icc 0 L, J.D s - s • id₂ + (s ^ 3 / 6) • J.R 0 =
      -∫ t in (0:ℝ)..s, (s - t) • ((J.R t).comp (J.D t) - t • J.R 0) := by
  intro s hs
  have hsub : Icc 0 s ⊆ Icc 0 L := Icc_subset_Icc_right hs.2
  have hDc : ContinuousOn J.D (Icc 0 L) := HasDerivWithinAt.continuousOn J.deriv_D
  have hI1 : IntervalIntegrable (fun t => (s - t) • (J.R t).comp (J.D t)) volume 0 s := by
    apply ContinuousOn.intervalIntegrable_of_Icc hs.1
    exact (continuousOn_const.sub continuousOn_id).smul
      ((J.continuous_R.clm_comp hDc).mono hsub)
  have hI2 : IntervalIntegrable (fun t => ((s - t) * t) • J.R 0) volume 0 s := by
    apply Continuous.intervalIntegrable; fun_prop
  have hK3 : ∫ t in (0:ℝ)..s, ((s - t) * t) • J.R 0 = (s ^ 3 / 6) • J.R 0 := by
    rw [intervalIntegral.integral_smul_const, integral_kernel]
  have hsplit : (∫ t in (0:ℝ)..s, (s - t) • ((J.R t).comp (J.D t) - t • J.R 0)) =
      (∫ t in (0:ℝ)..s, (s - t) • (J.R t).comp (J.D t)) -
        ∫ t in (0:ℝ)..s, ((s - t) * t) • J.R 0 := by
    rw [← intervalIntegral.integral_sub hI1 hI2]
    apply intervalIntegral.integral_congr
    intro t _
    simp only [smul_sub, mul_smul]
  rw [hsplit, hK3]
  conv_lhs => rw [integral_remainder J s hs]
  abel

theorem cubic_jet {K L : ℝ} (J : CAS07M05.JacobiPremises K L) (hK : 0 ≤ K) (hL : 0 < L) :
    ∀ ε > 0, ∃ δ > 0, ∀ s ∈ Icc 0 L, s < δ →
      ‖J.D s - s • id₂ + (s ^ 3 / 6) • J.R 0‖ ≤ ε * s ^ 3 := by
  intro ε hε
  obtain ⟨C, hC0, hC⟩ := cubic_bound J hK
  have hRc : ContinuousWithinAt J.R (Icc 0 L) 0 := J.continuous_R 0 ⟨le_refl _, hL.le⟩
  obtain ⟨δ1, hδ1, hδ1'⟩ := Metric.continuousWithinAt_iff.1 hRc ε hε
  have hKC : 0 ≤ K * C := mul_nonneg hK hC0
  have hKC1 : 0 < K * C + 1 := by linarith
  refine ⟨min δ1 (min 1 (ε / (K * C + 1))), by positivity, ?_⟩
  intro s hs hsδ
  have hs1 : s < δ1 := lt_of_lt_of_le hsδ (min_le_left _ _)
  have hs2 : s < 1 := lt_of_lt_of_le hsδ ((min_le_right _ _).trans (min_le_left _ _))
  have hs3 : s < ε / (K * C + 1) := lt_of_lt_of_le hsδ ((min_le_right _ _).trans (min_le_right _ _))
  have hs3' : s * (K * C + 1) < ε := (lt_div_iff₀ hKC1).1 hs3
  have hss : s ^ 2 ≤ s := by nlinarith [hs.1]
  have hKCs : K * C * s ^ 2 ≤ ε := by
    have : K * C * s ^ 2 ≤ K * C * s := mul_le_mul_of_nonneg_left hss hKC
    nlinarith [hs.1]
  rw [cubic_jet_identity J s hs, norm_neg]
  have hsub : Icc 0 s ⊆ Icc 0 L := Icc_subset_Icc_right hs.2
  calc ‖∫ t in (0:ℝ)..s, (s - t) • ((J.R t).comp (J.D t) - t • J.R 0)‖
        ≤ ∫ t in (0:ℝ)..s, (2 * ε) * ((s - t) * t) := by
          apply intervalIntegral.norm_integral_le_of_norm_le hs.1
          · filter_upwards with t ht
            have htL : t ∈ Icc 0 L := hsub ⟨ht.1.le, ht.2⟩
            have ht0 : 0 ≤ t := ht.1.le
            have hst : 0 ≤ s - t := sub_nonneg.2 ht.2
            have hsplit : (J.R t).comp (J.D t) - t • J.R 0 =
                (J.R t).comp (J.D t - t • id₂) + t • (J.R t - J.R 0) := by
              rw [ContinuousLinearMap.comp_sub, ContinuousLinearMap.comp_smul,
                ContinuousLinearMap.comp_id, smul_sub]
              abel
            have hA : ‖(J.R t).comp (J.D t - t • id₂)‖ ≤ K * (C * t ^ 3) :=
              (ContinuousLinearMap.opNorm_comp_le _ _).trans
                (mul_le_mul (J.curvature_bound t htL) (hC t htL) (norm_nonneg _) hK)
            have hdist : dist t 0 < δ1 := by
              rw [Real.dist_eq, sub_zero, abs_of_nonneg ht0]; linarith [ht.2]
            have hB : ‖t • (J.R t - J.R 0)‖ ≤ t * ε := by
              rw [norm_smul, Real.norm_eq_abs, abs_of_nonneg ht0]
              apply mul_le_mul_of_nonneg_left _ ht0
              have := hδ1' htL hdist
              rw [dist_eq_norm] at this
              exact this.le
            have ht2 : t ^ 2 ≤ s ^ 2 := pow_le_pow_left₀ ht0 ht.2 2
            have ht3 : K * (C * t ^ 3) ≤ ε * t := by
              have e : K * (C * t ^ 3) = t * (K * C * t ^ 2) := by ring
              rw [e]
              have : K * C * t ^ 2 ≤ K * C * s ^ 2 := mul_le_mul_of_nonneg_left ht2 hKC
              nlinarith
            rw [norm_smul, Real.norm_eq_abs, abs_of_nonneg hst, hsplit]
            calc (s - t) * ‖(J.R t).comp (J.D t - t • id₂) + t • (J.R t - J.R 0)‖
                  ≤ (s - t) * (K * (C * t ^ 3) + t * ε) :=
                    mul_le_mul_of_nonneg_left ((norm_add_le _ _).trans (add_le_add hA hB)) hst
              _ ≤ (s - t) * (ε * t + t * ε) :=
                    mul_le_mul_of_nonneg_left (by linarith) hst
              _ = (2 * ε) * ((s - t) * t) := by ring
          · apply Continuous.intervalIntegrable; fun_prop
    _ = ε * s ^ 3 / 3 := by
          rw [intervalIntegral.integral_const_mul, integral_kernel]; ring
    _ ≤ ε * s ^ 3 := by
          have : 0 ≤ ε * s ^ 3 := mul_nonneg hε.le (pow_nonneg hs.1 3)
          linarith

/-! ## T8 area distance at the vertex (positive branch) -/

theorem area_distance_vertex {K L : ℝ} (J : CAS07M05.JacobiPremises K L) (hK : 0 ≤ K) :
    ∃ C : ℝ, 0 ≤ C ∧ ∃ δ > 0, ∀ s, 0 < s → s ≤ L → s < δ →
      0 < Matrix.det (CAS07M05.matrixOf (J.D s)) ∧
      |Real.sqrt (Matrix.det (CAS07M05.matrixOf (J.D s))) - s| ≤ C * s ^ 3 := by
  obtain ⟨C, hC0, hC⟩ := cubic_bound J hK
  have hpos : 0 < C + 1 := by linarith
  refine ⟨C, hC0, 1 / (C + 1), by positivity, fun s hs hsL hsδ => ?_⟩
  have hsC : s * (C + 1) < 1 := (lt_div_iff₀ hpos).1 hsδ
  have hs1 : s < 1 := by nlinarith
  have hss : s ^ 2 ≤ s := by nlinarith
  have hη0 : 0 ≤ C * s ^ 2 := by positivity
  have hη1 : C * s ^ 2 < 1 := by
    have : C * s ^ 2 ≤ C * s := mul_le_mul_of_nonneg_left hss hC0
    nlinarith
  have hnorm : CAS07C02.euclideanOpNorm
      (CAS07M05.matrixOf (J.D s) - s • (1 : CAS07C02.Mat)) ≤ s * (C * s ^ 2) := by
    rw [CAS07M05.opnorm_error_eq]
    calc ‖J.D s - s • ContinuousLinearMap.id ℝ Cas07M04.Plane‖ ≤ C * s ^ 3 :=
          hC s ⟨hs.le, hsL⟩
      _ = s * (C * s ^ 2) := by ring
  have h := (CAS07C02.CAS_07_C02_full (CAS07M05.matrixOf (J.D s)) s (C * s ^ 2) hs hη0 hη1
    hnorm).2
  refine ⟨h.1, abs_sub_le_iff.2 ⟨?_, ?_⟩⟩
  · have := h.2.2; nlinarith
  · have := h.2.1; nlinarith

/-! ## T9 screen transition: constant `O ∈ O(2)` between parallel orthonormal frames -/

/-- Change of orthonormal screen frame: `A ↦ O A O⁻¹`. -/
def conj (O : Plane ≃ₗᵢ[ℝ] Plane) (A : Op) : Op :=
  (O.toContinuousLinearEquiv : Plane →L[ℝ] Plane).comp
    (A.comp (O.symm.toContinuousLinearEquiv : Plane →L[ℝ] Plane))

@[simp] theorem conj_apply (O : Plane ≃ₗᵢ[ℝ] Plane) (A : Op) (v : Plane) :
    conj O A v = O (A (O.symm v)) := rfl

/-- `conj O` as a continuous linear map on operators. -/
def conjL (O : Plane ≃ₗᵢ[ℝ] Plane) : Op →L[ℝ] Op :=
  (ContinuousLinearMap.compL ℝ Plane Plane Plane
      (O.toContinuousLinearEquiv : Plane →L[ℝ] Plane)).comp
    ((ContinuousLinearMap.compL ℝ Plane Plane Plane).flip
      (O.symm.toContinuousLinearEquiv : Plane →L[ℝ] Plane))

theorem conjL_apply (O : Plane ≃ₗᵢ[ℝ] Plane) (A : Op) : conjL O A = conj O A := by
  apply ContinuousLinearMap.ext
  intro v
  simp [conjL]

theorem conj_comp (O : Plane ≃ₗᵢ[ℝ] Plane) (A B : Op) :
    conj O (A.comp B) = (conj O A).comp (conj O B) := by
  apply ContinuousLinearMap.ext; intro v; simp

theorem conj_neg (O : Plane ≃ₗᵢ[ℝ] Plane) (A : Op) : conj O (-A) = -conj O A := by
  apply ContinuousLinearMap.ext; intro v; simp

theorem conj_id (O : Plane ≃ₗᵢ[ℝ] Plane) : conj O id₂ = id₂ := by
  apply ContinuousLinearMap.ext; intro v; simp

theorem conj_zero (O : Plane ≃ₗᵢ[ℝ] Plane) : conj O 0 = 0 := by
  apply ContinuousLinearMap.ext; intro v; simp

theorem norm_conj_le (O : Plane ≃ₗᵢ[ℝ] Plane) (A : Op) : ‖conj O A‖ ≤ ‖A‖ := by
  unfold conj
  calc ‖(O.toContinuousLinearEquiv : Plane →L[ℝ] Plane).comp
          (A.comp (O.symm.toContinuousLinearEquiv : Plane →L[ℝ] Plane))‖
        ≤ ‖(O.toContinuousLinearEquiv : Plane →L[ℝ] Plane)‖ *
            (‖A‖ * ‖(O.symm.toContinuousLinearEquiv : Plane →L[ℝ] Plane)‖) :=
          (ContinuousLinearMap.opNorm_comp_le _ _).trans
            (mul_le_mul_of_nonneg_left (ContinuousLinearMap.opNorm_comp_le _ _) (norm_nonneg _))
    _ = ‖A‖ := by
          rw [LinearIsometryEquiv.norm_toContinuousLinearMap,
            LinearIsometryEquiv.norm_toContinuousLinearMap]
          ring

/-- The Jacobi premises transported to a rotated/reflected parallel orthonormal frame. -/
def rotate {K L : ℝ} (O : Plane ≃ₗᵢ[ℝ] Plane) (J : CAS07M05.JacobiPremises K L) :
    CAS07M05.JacobiPremises K L where
  D t := conj O (J.D t)
  D1 t := conj O (J.D1 t)
  D2 t := conj O (J.D2 t)
  R t := conj O (J.R t)
  deriv_D t ht := by
    have h := (conjL O).hasFDerivAt.comp_hasDerivWithinAt t (J.deriv_D t ht)
    simpa [Function.comp_def, conjL_apply] using h
  deriv_D1 t ht := by
    have h := (conjL O).hasFDerivAt.comp_hasDerivWithinAt t (J.deriv_D1 t ht)
    simpa [Function.comp_def, conjL_apply] using h
  continuous_D2 := by
    have h := (conjL O).continuous.comp_continuousOn J.continuous_D2
    simpa [Function.comp_def, conjL_apply] using h
  continuous_R := by
    have h := (conjL O).continuous.comp_continuousOn J.continuous_R
    simpa [Function.comp_def, conjL_apply] using h
  D_zero := by rw [J.D_zero, conj_zero]
  D1_zero := by rw [J.D1_zero, conj_id]
  jacobi t ht := by rw [J.jacobi t ht, conj_neg, conj_comp]
  curvature_bound t ht := (norm_conj_le O _).trans (J.curvature_bound t ht)

theorem det_matrixOf (T : Op) :
    Matrix.det (CAS07M05.matrixOf T) = LinearMap.det (T : Plane →ₗ[ℝ] Plane) := by
  have h : Matrix.toEuclideanLin (CAS07M05.matrixOf T) = (T : Plane →ₗ[ℝ] Plane) := by
    simp [CAS07M05.matrixOf]
  rw [← h, Matrix.toEuclideanLin_eq_toLin, LinearMap.det_toLin]

theorem det_conj (O : Plane ≃ₗᵢ[ℝ] Plane) (A : Op) :
    Matrix.det (CAS07M05.matrixOf (conj O A)) = Matrix.det (CAS07M05.matrixOf A) := by
  rw [det_matrixOf, det_matrixOf]
  have e : ((conj O A : Op) : Plane →ₗ[ℝ] Plane) =
      (O.toLinearEquiv : Plane →ₗ[ℝ] Plane) ∘ₗ (A : Plane →ₗ[ℝ] Plane) ∘ₗ
        (O.toLinearEquiv.symm : Plane →ₗ[ℝ] Plane) := by
    apply LinearMap.ext; intro v; simp
  rw [e, LinearMap.det_conj]

theorem screen_transition {K L : ℝ} (O : Plane ≃ₗᵢ[ℝ] Plane)
    (J J' : CAS07M05.JacobiPremises K L)
    (hR : ∀ t ∈ Icc 0 L, J'.R t = conj O (J.R t)) :
    ∀ t ∈ Icc 0 L, J'.D t = conj O (J.D t) ∧
      Real.sqrt (Matrix.det (CAS07M05.matrixOf (J'.D t))) =
        Real.sqrt (Matrix.det (CAS07M05.matrixOf (J.D t))) := by
  intro t ht
  have h : J'.D t = conj O (J.D t) := (jacobi_unique J' (rotate O J) hR t ht).1
  refine ⟨h, ?_⟩
  rw [h, det_conj]

/-! ## T10 affine rescaling `s = c σ` -/

theorem comp_mul_deriv {f f' : ℝ → Op} {L c σ : ℝ} (hc : 0 < c)
    (hf : ∀ t ∈ Icc 0 L, HasDerivWithinAt f (f' t) (Icc 0 L) t) (hσ : σ ∈ Icc 0 (L / c)) :
    HasDerivWithinAt (fun u => f (c * u)) (c • f' (c * σ)) (Icc 0 (L / c)) σ := by
  have hmaps : MapsTo (fun u => c * u) (Icc 0 (L / c)) (Icc 0 L) := by
    intro u hu
    refine ⟨mul_nonneg hc.le hu.1, ?_⟩
    have := hu.2
    rw [le_div_iff₀ hc] at this
    linarith
  have hlin : HasDerivWithinAt (fun u => c * u) c (Icc 0 (L / c)) σ := by
    simpa using ((hasDerivAt_id σ).const_mul c).hasDerivWithinAt
  exact (hf (c * σ) (hmaps hσ)).scomp σ hlin hmaps

theorem rescale_maps {L c : ℝ} (hc : 0 < c) :
    MapsTo (fun u => c * u) (Icc 0 (L / c)) (Icc 0 L) := by
  intro u hu
  refine ⟨mul_nonneg hc.le hu.1, ?_⟩
  have := hu.2
  rw [le_div_iff₀ hc] at this
  linarith

/-- Affine reparametrisation `s = c σ` of the Jacobi premises. -/
def rescale {K L : ℝ} (c : ℝ) (hc : 0 < c) (J : CAS07M05.JacobiPremises K L) :
    CAS07M05.JacobiPremises (c ^ 2 * K) (L / c) where
  D σ := c⁻¹ • J.D (c * σ)
  D1 σ := J.D1 (c * σ)
  D2 σ := c • J.D2 (c * σ)
  R σ := c ^ 2 • J.R (c * σ)
  deriv_D σ hσ := by
    have h := (comp_mul_deriv hc J.deriv_D hσ).fun_const_smul c⁻¹
    rw [smul_smul, inv_mul_cancel₀ hc.ne', one_smul] at h
    exact h
  deriv_D1 σ hσ := comp_mul_deriv hc J.deriv_D1 hσ
  continuous_D2 :=
    (J.continuous_D2.comp (continuousOn_const.mul continuousOn_id) (rescale_maps hc)).const_smul c
  continuous_R :=
    (J.continuous_R.comp (continuousOn_const.mul continuousOn_id) (rescale_maps hc)).const_smul
      (c ^ 2)
  D_zero := by
    rw [mul_zero, J.D_zero]
    exact ContinuousLinearMap.ext fun v => by simp
  D1_zero := by simp [J.D1_zero]
  jacobi σ hσ := by
    have hcc : c ^ 2 * c⁻¹ = c := by
      rw [pow_two, mul_assoc, mul_inv_cancel₀ hc.ne', mul_one]
    rw [J.jacobi _ (rescale_maps hc hσ), ContinuousLinearMap.smul_comp,
      ContinuousLinearMap.comp_smul, smul_smul, hcc, smul_neg]
  curvature_bound σ hσ := by
    rw [norm_smul, Real.norm_eq_abs, abs_of_nonneg (by positivity)]
    exact mul_le_mul_of_nonneg_left (J.curvature_bound _ (rescale_maps hc hσ)) (by positivity)

theorem matrixOf_smul (a : ℝ) (T : Op) :
    CAS07M05.matrixOf (a • T) = a • CAS07M05.matrixOf T := by
  simp [CAS07M05.matrixOf]

theorem rescale_area_distance {K L c : ℝ} (hc : 0 < c) (J : CAS07M05.JacobiPremises K L)
    (σ : ℝ) :
    Real.sqrt (Matrix.det (CAS07M05.matrixOf ((rescale c hc J).D σ))) =
      Real.sqrt (Matrix.det (CAS07M05.matrixOf (J.D (c * σ)))) / c := by
  show Real.sqrt (Matrix.det (CAS07M05.matrixOf (c⁻¹ • J.D (c * σ)))) = _
  rw [matrixOf_smul, Matrix.det_smul, Fintype.card_fin,
    Real.sqrt_mul (by positivity : (0 : ℝ) ≤ c⁻¹ ^ 2), Real.sqrt_sq (by positivity),
    div_eq_inv_mul]

theorem eta_rescale_invariant {K L c : ℝ} (hK : 0 ≤ K) (hc : 0 < c) :
    CAS07M01.eta (c ^ 2 * K) (L / c) = CAS07M01.eta K L := by
  unfold CAS07M01.eta CAS07M01.fd
  rcases eq_or_lt_of_le hK with h | h
  · subst h
    rcases eq_or_ne L 0 with hL | hL
    · subst hL; simp
    · simp only [mul_zero, if_true]
      rw [div_self (div_ne_zero hL hc.ne'), div_self hL]
  · have hK' : c ^ 2 * K ≠ 0 := by positivity
    rw [if_neg hK', if_neg h.ne']
    have hs : Real.sqrt (c ^ 2 * K) = c * Real.sqrt K := by
      rw [Real.sqrt_mul (by positivity), Real.sqrt_sq hc.le]
    have hsK : 0 < Real.sqrt K := Real.sqrt_pos.2 h
    rw [hs]
    have e : c * Real.sqrt K * (L / c) = Real.sqrt K * L := by field_simp
    rw [e]
    rcases eq_or_ne L 0 with hL | hL
    · subst hL; simp
    · field_simp

/-! ## T11 observer normalization (tangent-space algebra at the vertex) -/

theorem observer_normalization {V : Type*} [AddCommGroup V] [Module ℝ V]
    (B : LinearMap.BilinForm ℝ V) (hB : B.IsSymm) (o n : V)
    (hoo : B o o = -1) (hnn : B n n = 1) (hon : B o n = 0) :
    B (-o + n) (-o + n) = 0 ∧ B o (-o + n) = 1 ∧
      ∀ c : ℝ, B o (c • (-o + n)) = 1 ↔ c = 1 := by
  have hno : B n o = 0 := by rw [hB.eq]; exact hon
  have hK : B o (-o + n) = 1 := by
    simp [map_add, map_neg, hoo, hon]
  refine ⟨?_, hK, ?_⟩
  · simp [map_add, map_neg, LinearMap.add_apply, LinearMap.neg_apply, hoo, hnn, hon, hno]
  · intro c
    rw [map_smul, hK, smul_eq_mul, mul_one]

/-! ## T12 mapping theorem into the reviewed CAS07 determinant-distance bridge -/

theorem frame_determinant_distance {K L s : ℝ} (F : ScreenFrameData K L)
    (hK : 0 ≤ K) (hL : 0 < L) (hs : 0 < s) (hsL : s ≤ L)
    (hEtaL : CAS07M01.eta K L < 1) :
    ∃ J : CAS07M05.JacobiPremises K L, J.R = F.R ∧
      0 < Matrix.det (CAS07M05.matrixOf (J.D s)) ∧
      s * (1 - CAS07M01.eta K s) ≤ Real.sqrt (Matrix.det (CAS07M05.matrixOf (J.D s))) ∧
      Real.sqrt (Matrix.det (CAS07M05.matrixOf (J.D s))) ≤ s * (1 + CAS07M01.eta K s) := by
  obtain ⟨J, hJ⟩ := exists_jacobi F hL
  exact ⟨J, hJ, CAS07M05.determinant_distance_bridge J hK hL hs hsL hEtaL⟩

/-! ## Non-vacuity witness and negative control -/

/-- Flat witness: `R = 0`, `D s = s • id`. -/
def flatJacobi (L : ℝ) : CAS07M05.JacobiPremises 0 L where
  D s := s • id₂
  D1 _ := id₂
  D2 _ := 0
  R _ := 0
  deriv_D t _ := by
    simpa using ((hasDerivAt_id t).smul_const id₂).hasDerivWithinAt
  deriv_D1 t _ := hasDerivWithinAt_const _ _ _
  continuous_D2 := continuousOn_const
  continuous_R := continuousOn_const
  D_zero := ContinuousLinearMap.ext fun v => by simp
  D1_zero := rfl
  jacobi t _ := ContinuousLinearMap.ext fun v => by simp
  curvature_bound t _ := by simp

theorem flatJacobi_D (L s : ℝ) : (flatJacobi L).D s = s • id₂ := rfl

/-- Negative control: an exactly linear Jacobi map forces zero tidal operator at the
vertex, so the cubic coefficient `-R(0)/6` is genuinely detected. -/
theorem negative_control {K L : ℝ} (J : CAS07M05.JacobiPremises K L) (hK : 0 ≤ K)
    (hL : 0 < L) (hflat : ∀ s ∈ Icc 0 L, J.D s = s • id₂) : J.R 0 = 0 := by
  by_contra hne
  have hpos : 0 < ‖J.R 0‖ := norm_pos_iff.2 hne
  obtain ⟨δ, hδ, hδ'⟩ := cubic_jet J hK hL (‖J.R 0‖ / 12) (by positivity)
  have hs0 : 0 < min (δ / 2) L := lt_min (half_pos hδ) hL
  have hsL : min (δ / 2) L ∈ Icc 0 L := ⟨hs0.le, min_le_right _ _⟩
  have hsδ : min (δ / 2) L < δ := lt_of_le_of_lt (min_le_left _ _) (half_lt_self hδ)
  have h := hδ' _ hsL hsδ
  rw [hflat _ hsL, sub_self, zero_add, norm_smul, Real.norm_eq_abs,
    abs_of_nonneg (by positivity)] at h
  have hs3 : 0 < (min (δ / 2) L) ^ 3 := by positivity
  nlinarith

end G01A
