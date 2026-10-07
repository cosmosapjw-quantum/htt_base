import Mathlib
import CAS07M03Accepted

set_option maxHeartbeats 400000
set_option synthInstance.maxHeartbeats 400000

/-!
CAS-07-M04. All matrix norms below are the induced operator norm on real
continuous linear maps of the Euclidean two-plane.
-/

open Set intervalIntegral MeasureTheory

namespace Cas07M04

abbrev Plane := EuclideanSpace ℝ (Fin 2)
abbrev Op := Plane →L[ℝ] Plane

noncomputable def f (K s : ℝ) : ℝ :=
  if K = 0 then s else Real.sinh (Real.sqrt K * s) / Real.sqrt K

theorem f_at_zero (K : ℝ) : f K 0 = 0 := by
  simp [f]

theorem f_K_zero (s : ℝ) : f 0 s = s := by
  simp [f]

private theorem integral_taylor_two
    {D D1 D2 : ℝ → Op} {L s : ℝ} (hs : 0 ≤ s) (hsL : s ≤ L)
    (hD : ∀ t ∈ Icc 0 L, HasDerivWithinAt D (D1 t) (Icc 0 L) t)
    (hD1 : ∀ t ∈ Icc 0 L, HasDerivWithinAt D1 (D2 t) (Icc 0 L) t)
    (hD2 : ContinuousOn D2 (Icc 0 L)) :
    D s = D 0 + s • D1 0 + ∫ t in (0:ℝ)..s, (s-t) • D2 t := by
  have hsub : Icc (0:ℝ) s ⊆ Icc 0 L := Icc_subset_Icc_right hsL
  have hD' : ∀ t ∈ Icc (0:ℝ) s, HasDerivWithinAt D (D1 t) (Icc 0 s) t := by
    intro t ht
    exact (hD t (hsub ht)).mono hsub
  have hD1' : ∀ t ∈ Icc (0:ℝ) s, HasDerivWithinAt D1 (D2 t) (Icc 0 s) t := by
    intro t ht
    exact (hD1 t (hsub ht)).mono hsub
  have hD1cont : ContinuousOn D1 (Icc (0:ℝ) s) := HasDerivWithinAt.continuousOn hD1'
  have hDcont : ContinuousOn D (Icc (0:ℝ) s) := HasDerivWithinAt.continuousOn hD'
  have hD1int : IntervalIntegrable D1 volume 0 s := hD1cont.intervalIntegrable_of_Icc hs
  have hD2int : IntervalIntegrable D2 volume 0 s :=
    (hD2.mono hsub).intervalIntegrable_of_Icc hs
  have hFTC : (∫ t in (0:ℝ)..s, D1 t) = D s - D 0 := by
    apply intervalIntegral.integral_eq_sub_of_hasDerivAt_of_le hs hDcont
    · intro t ht
      exact (hD' t ⟨ht.1.le, ht.2.le⟩).hasDerivAt (Icc_mem_nhds ht.1 ht.2)
    · exact hD1int
  have hparts := integral_smul_deriv_eq_deriv_smul_of_hasDerivWithinAt
    (a := (0:ℝ)) (b := s) (u := fun t : ℝ => s-t) (u' := fun _ => (-1:ℝ))
    (v := D1) (v' := D2)
    (fun t ht => by
      rw [uIcc_of_le hs] at ht ⊢
      exact ((hasDerivAt_id t).const_sub s).hasDerivWithinAt)
    (by simpa only [uIcc_of_le hs] using hD1')
    (intervalIntegral.intervalIntegrable_const) hD2int
  simp only [sub_self, zero_smul, sub_zero, neg_one_smul] at hparts
  rw [intervalIntegral.integral_neg] at hparts
  rw [hFTC] at hparts
  -- The integration-by-parts identity is the vector-valued second-order Taylor formula.
  rw [hparts]
  abel

theorem volterra_identity
    {D D1 D2 R : ℝ → Op} {L s : ℝ} (hs : 0 ≤ s) (hsL : s ≤ L)
    (hD : ∀ t ∈ Icc 0 L, HasDerivWithinAt D (D1 t) (Icc 0 L) t)
    (hD1 : ∀ t ∈ Icc 0 L, HasDerivWithinAt D1 (D2 t) (Icc 0 L) t)
    (hD2 : ContinuousOn D2 (Icc 0 L))
    (hD0 : D 0 = 0) (hD10 : D1 0 = ContinuousLinearMap.id ℝ Plane)
    (hJac : ∀ t ∈ Icc 0 L, D2 t = -(R t).comp (D t)) :
    D s = s • (ContinuousLinearMap.id ℝ Plane) -
      ∫ t in (0:ℝ)..s, (s-t) • ((R t).comp (D t)) := by
  have hT := integral_taylor_two hs hsL hD hD1 hD2
  rw [hD0, hD10, zero_add] at hT
  have hInt :
      (∫ t in (0:ℝ)..s, (s-t) • D2 t) =
        -(∫ t in (0:ℝ)..s, (s-t) • ((R t).comp (D t))) := by
    rw [← intervalIntegral.integral_neg]
    apply intervalIntegral.integral_congr
    intro t ht
    rw [uIcc_of_le hs] at ht
    have htL : t ∈ Icc (0:ℝ) L := ⟨ht.1, le_trans ht.2 hsL⟩
    simp [hJac t htL]
  rw [hInt] at hT
  simpa only [sub_eq_add_neg] using hT

theorem scalar_premise
    {D D1 D2 R : ℝ → Op} {K L : ℝ} (_hK : 0 ≤ K) (_hL : 0 < L)
    (hD : ∀ t ∈ Icc 0 L, HasDerivWithinAt D (D1 t) (Icc 0 L) t)
    (hD1 : ∀ t ∈ Icc 0 L, HasDerivWithinAt D1 (D2 t) (Icc 0 L) t)
    (hD2 : ContinuousOn D2 (Icc 0 L))
    (_hR : ContinuousOn R (Icc 0 L))
    (hD0 : D 0 = 0) (hD10 : D1 0 = ContinuousLinearMap.id ℝ Plane)
    (hJac : ∀ t ∈ Icc 0 L, D2 t = -(R t).comp (D t))
    (hRnorm : ∀ t ∈ Icc 0 L, ‖R t‖ ≤ K) :
    ContinuousOn (fun t => ‖D t‖) (Icc 0 L) ∧
    (∀ t ∈ Icc 0 L, 0 ≤ ‖D t‖) ∧
    ∀ s ∈ Icc 0 L, ‖D s‖ ≤
      s + K * ∫ t in (0:ℝ)..s, (s-t) * ‖D t‖ := by
  have hDcont : ContinuousOn D (Icc 0 L) := HasDerivWithinAt.continuousOn hD
  have hucont : ContinuousOn (fun t => ‖D t‖) (Icc 0 L) := hDcont.norm
  refine ⟨hucont, (fun t _ => norm_nonneg _), ?_⟩
  intro s hs
  have hs0 : 0 ≤ s := hs.1
  have hsL : s ≤ L := hs.2
  have hsub : Icc (0:ℝ) s ⊆ Icc 0 L := Icc_subset_Icc_right hsL
  have hbound : IntervalIntegrable (fun t : ℝ => K * ((s-t) * ‖D t‖)) volume 0 s := by
    apply ContinuousOn.intervalIntegrable_of_Icc hs0
    exact continuousOn_const.mul ((continuousOn_const.sub continuousOn_id).mul (hucont.mono hsub))
  have hI :
      ‖∫ t in (0:ℝ)..s, (s-t) • ((R t).comp (D t))‖ ≤
        K * ∫ t in (0:ℝ)..s, (s-t) * ‖D t‖ := by
    rw [← intervalIntegral.integral_const_mul]
    apply intervalIntegral.norm_integral_le_of_norm_le hs0
    · filter_upwards [] with t
      intro ht
      have htL : t ∈ Icc (0:ℝ) L := ⟨ht.1.le, le_trans ht.2 hsL⟩
      have hst : 0 ≤ s-t := sub_nonneg.mpr ht.2
      calc
        ‖(s-t) • ((R t).comp (D t))‖ = (s-t) * ‖(R t).comp (D t)‖ := by
          simp [norm_smul, Real.norm_eq_abs, abs_of_nonneg hst]
        _ ≤ (s-t) * (‖R t‖ * ‖D t‖) :=
          mul_le_mul_of_nonneg_left (ContinuousLinearMap.opNorm_comp_le _ _) hst
        _ ≤ K * ((s-t) * ‖D t‖) := by
          have := mul_le_mul_of_nonneg_right (hRnorm t htL) (norm_nonneg (D t))
          nlinarith
    · exact hbound
  have hV := volterra_identity hs0 hsL hD hD1 hD2 hD0 hD10 hJac
  rw [hV]
  have hid : ‖s • (ContinuousLinearMap.id ℝ Plane)‖ = s := by
    simp [norm_smul, Real.norm_eq_abs, abs_of_nonneg hs0, ContinuousLinearMap.norm_id]
  calc
    ‖s • (ContinuousLinearMap.id ℝ Plane) -
      ∫ t in (0:ℝ)..s, (s-t) • ((R t).comp (D t))‖
        ≤ ‖s • (ContinuousLinearMap.id ℝ Plane)‖ +
            ‖∫ t in (0:ℝ)..s, (s-t) • ((R t).comp (D t))‖ := norm_sub_le _ _
    _ ≤ s + K * ∫ t in (0:ℝ)..s, (s-t) * ‖D t‖ := by
      rw [hid]
      exact add_le_add (le_refl s) hI

theorem d_norm
    {D D1 D2 R : ℝ → Op} {K L : ℝ} (hK : 0 ≤ K) (hL : 0 < L)
    (hD : ∀ t ∈ Icc 0 L, HasDerivWithinAt D (D1 t) (Icc 0 L) t)
    (hD1 : ∀ t ∈ Icc 0 L, HasDerivWithinAt D1 (D2 t) (Icc 0 L) t)
    (hD2 : ContinuousOn D2 (Icc 0 L)) (hR : ContinuousOn R (Icc 0 L))
    (hD0 : D 0 = 0) (hD10 : D1 0 = ContinuousLinearMap.id ℝ Plane)
    (hJac : ∀ t ∈ Icc 0 L, D2 t = -(R t).comp (D t))
    (hRnorm : ∀ t ∈ Icc 0 L, ‖R t‖ ≤ K) :
    ∀ s ∈ Icc 0 L, ‖D s‖ ≤ f K s := by
  obtain ⟨hucont, hunonneg, hsub⟩ :=
    scalar_premise hK hL hD hD1 hD2 hR hD0 hD10 hJac hRnorm
  intro s hs
  have hsub' : ∀ x ∈ Icc 0 L, ‖D x‖ ≤ x + CAS07M03.T K (fun t => ‖D t‖) x := by
    intro x hx
    simpa only [CAS07M03.T] using hsub x hx
  have hc := CAS07M03.scalar_volterra_comparison K L hK hL
    (fun t => ‖D t‖) hucont hunonneg hsub' s hs
  simpa only [f, CAS07M03.f] using hc

theorem d_minus_si
    {D D1 D2 R : ℝ → Op} {K L : ℝ} (hK : 0 ≤ K) (hL : 0 < L)
    (hD : ∀ t ∈ Icc 0 L, HasDerivWithinAt D (D1 t) (Icc 0 L) t)
    (hD1 : ∀ t ∈ Icc 0 L, HasDerivWithinAt D1 (D2 t) (Icc 0 L) t)
    (hD2 : ContinuousOn D2 (Icc 0 L)) (_hR : ContinuousOn R (Icc 0 L))
    (hD0 : D 0 = 0) (hD10 : D1 0 = ContinuousLinearMap.id ℝ Plane)
    (hJac : ∀ t ∈ Icc 0 L, D2 t = -(R t).comp (D t))
    (hRnorm : ∀ t ∈ Icc 0 L, ‖R t‖ ≤ K) :
    ∀ s ∈ Icc 0 L,
      ‖D s - s • (ContinuousLinearMap.id ℝ Plane)‖ ≤ f K s - s := by
  let w : ℝ → ℝ := fun t => ‖D t - t • (ContinuousLinearMap.id ℝ Plane)‖ + t
  have hDcont : ContinuousOn D (Icc 0 L) := HasDerivWithinAt.continuousOn hD
  have hwcont : ContinuousOn w (Icc 0 L) := by
    dsimp [w]
    exact (hDcont.sub (continuousOn_id.smul continuousOn_const)).norm.add continuousOn_id
  have hwnonneg : ∀ t ∈ Icc 0 L, 0 ≤ w t := by
    intro t ht
    dsimp [w]
    exact add_nonneg (norm_nonneg _) ht.1
  have hDle : ∀ t ∈ Icc 0 L, ‖D t‖ ≤ w t := by
    intro t ht
    have htId : ‖t • (ContinuousLinearMap.id ℝ Plane)‖ = t := by
      simp [norm_smul, Real.norm_eq_abs, abs_of_nonneg ht.1, ContinuousLinearMap.norm_id]
    dsimp [w]
    calc
      ‖D t‖ = ‖(D t - t • (ContinuousLinearMap.id ℝ Plane)) +
          t • (ContinuousLinearMap.id ℝ Plane)‖ := by congr 1; abel
      _ ≤ ‖D t - t • (ContinuousLinearMap.id ℝ Plane)‖ +
          ‖t • (ContinuousLinearMap.id ℝ Plane)‖ := norm_add_le _ _
      _ = ‖D t - t • (ContinuousLinearMap.id ℝ Plane)‖ + t := by rw [htId]
  have hwsub : ∀ s ∈ Icc 0 L, w s ≤ s + CAS07M03.T K w s := by
    intro s hs
    have hs0 : 0 ≤ s := hs.1
    have hsL : s ≤ L := hs.2
    have hsub : Icc (0:ℝ) s ⊆ Icc 0 L := Icc_subset_Icc_right hsL
    have hbound : IntervalIntegrable (fun t : ℝ => K * ((s-t) * w t)) volume 0 s := by
      apply ContinuousOn.intervalIntegrable_of_Icc hs0
      exact continuousOn_const.mul ((continuousOn_const.sub continuousOn_id).mul (hwcont.mono hsub))
    have hI :
        ‖∫ t in (0:ℝ)..s, (s-t) • ((R t).comp (D t))‖ ≤
          K * ∫ t in (0:ℝ)..s, (s-t) * w t := by
      rw [← intervalIntegral.integral_const_mul]
      apply intervalIntegral.norm_integral_le_of_norm_le hs0
      · filter_upwards [] with t
        intro ht
        have htL : t ∈ Icc (0:ℝ) L := ⟨ht.1.le, le_trans ht.2 hsL⟩
        have hst : 0 ≤ s-t := sub_nonneg.mpr ht.2
        calc
          ‖(s-t) • ((R t).comp (D t))‖ = (s-t) * ‖(R t).comp (D t)‖ := by
            simp [norm_smul, Real.norm_eq_abs, abs_of_nonneg hst]
          _ ≤ (s-t) * (‖R t‖ * ‖D t‖) :=
            mul_le_mul_of_nonneg_left (ContinuousLinearMap.opNorm_comp_le _ _) hst
          _ ≤ K * ((s-t) * w t) := by
            have h1 := mul_le_mul_of_nonneg_right (hRnorm t htL) (norm_nonneg (D t))
            have h2 := mul_le_mul_of_nonneg_left (hDle t htL) hK
            nlinarith [mul_nonneg hst (norm_nonneg (D t))]
      · exact hbound
    have hV := volterra_identity hs0 hsL hD hD1 hD2 hD0 hD10 hJac
    have hrem : ‖D s - s • (ContinuousLinearMap.id ℝ Plane)‖ =
        ‖∫ t in (0:ℝ)..s, (s-t) • ((R t).comp (D t))‖ := by
      rw [hV]
      abel_nf
      simp
    change ‖D s - s • (ContinuousLinearMap.id ℝ Plane)‖ + s ≤
      s + K * ∫ t in (0:ℝ)..s, (s-t) * w t
    calc
      ‖D s - s • (ContinuousLinearMap.id ℝ Plane)‖ + s =
          s + ‖D s - s • (ContinuousLinearMap.id ℝ Plane)‖ := add_comm _ _
      _ ≤ s + K * ∫ t in (0:ℝ)..s, (s-t) * w t :=
        add_le_add (le_refl s) (hrem.trans_le hI)
  intro s hs
  have hc := CAS07M03.scalar_volterra_comparison K L hK hL w hwcont hwnonneg hwsub s hs
  dsimp [w] at hc
  change ‖D s - s • (ContinuousLinearMap.id ℝ Plane)‖ + s ≤ f K s at hc
  linarith

theorem zero_parameter_control
    {D D1 D2 R : ℝ → Op} {L : ℝ} (_hL : 0 < L)
    (hD : ∀ t ∈ Icc 0 L, HasDerivWithinAt D (D1 t) (Icc 0 L) t)
    (hD1 : ∀ t ∈ Icc 0 L, HasDerivWithinAt D1 (D2 t) (Icc 0 L) t)
    (hD2 : ContinuousOn D2 (Icc 0 L))
    (hD0 : D 0 = 0) (hD10 : D1 0 = ContinuousLinearMap.id ℝ Plane)
    (hJac : ∀ t ∈ Icc 0 L, D2 t = -(R t).comp (D t))
    (hRnorm : ∀ t ∈ Icc 0 L, ‖R t‖ ≤ (0:ℝ)) :
    ∀ s ∈ Icc 0 L, D s = s • (ContinuousLinearMap.id ℝ Plane) := by
  intro s hs
  have hRzero : ∀ t ∈ Icc 0 L, R t = 0 := by
    intro t ht
    apply norm_eq_zero.mp
    exact le_antisymm (hRnorm t ht) (norm_nonneg _)
  have hV := volterra_identity hs.1 hs.2 hD hD1 hD2 hD0 hD10 hJac
  have hI : (∫ t in (0:ℝ)..s, (s-t) • ((R t).comp (D t))) = 0 := by
    calc
      (∫ t in (0:ℝ)..s, (s-t) • ((R t).comp (D t))) =
          ∫ t in (0:ℝ)..s, (0:Op) := by
            apply intervalIntegral.integral_congr
            intro t ht
            rw [uIcc_of_le hs.1] at ht
            have htL : t ∈ Icc (0:ℝ) L := ⟨ht.1, le_trans ht.2 hs.2⟩
            change (s-t) • ((R t).comp (D t)) = 0
            rw [hRzero t htL]
            simp only [ContinuousLinearMap.zero_comp]
            ext x
            simp
      _ = 0 := by simp
  simpa [hI] using hV

theorem zero_distance_control {D : ℝ → Op} (hD0 : D 0 = 0) (K : ℝ) :
    D 0 = 0 ∧ ‖D 0‖ = f K 0 ∧
      ‖D 0 - (0:ℝ) • (ContinuousLinearMap.id ℝ Plane)‖ = f K 0 - 0 := by
  constructor
  · exact hD0
  constructor
  · simp [hD0, f_at_zero]
  · simp [hD0, f_at_zero, norm_smul]


end Cas07M04
