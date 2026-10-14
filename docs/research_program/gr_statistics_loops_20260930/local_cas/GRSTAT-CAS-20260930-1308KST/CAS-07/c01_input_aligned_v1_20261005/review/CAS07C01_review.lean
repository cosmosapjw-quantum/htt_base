import Mathlib

/-! CAS-07-C01: exact scalar comparison function. `s` and `t` are lengths and
`k` has units inverse length squared. This file concerns only the scalar identity. -/

namespace CAS07C01

open Filter MeasureTheory intervalIntegral
open scoped Topology

/-- Positive-curvature-parameter hyperbolic branch, with its mathematical expression
also defined at other `k` by Lean's total square root and division operations. -/
noncomputable def hyper (k s : ℝ) : ℝ := Real.sinh (Real.sqrt k * s) / Real.sqrt k

/-- The separately defined flat branch. -/
def flat (s : ℝ) : ℝ := s

private theorem sqrt_ne (k : ℝ) (hk : 0 < k) : Real.sqrt k ≠ 0 :=
  ne_of_gt (Real.sqrt_pos.2 hk)

private theorem sqrt_sq (k : ℝ) (hk : 0 < k) : Real.sqrt k ^ 2 = k :=
  Real.sq_sqrt hk.le

theorem hyper_zero (k : ℝ) : hyper k 0 = 0 := by simp [hyper]

theorem hyper_hasDerivAt (k s : ℝ) (hk : 0 < k) :
    HasDerivAt (hyper k) (Real.cosh (Real.sqrt k * s)) s := by
  let a := Real.sqrt k
  have ha : a ≠ 0 := sqrt_ne k hk
  have h : HasDerivAt (fun t : ℝ => Real.sinh (a * t) / a)
      (Real.cosh (a * s) * a / a) s :=
    ((Real.hasDerivAt_sinh (a * s)).comp s (hasDerivAt_const_mul a)).div_const a
  change HasDerivAt (fun t : ℝ => Real.sinh (a * t) / a) (Real.cosh (a * s)) s
  convert h using 1
  field_simp [ha]

theorem hyper_deriv_zero (k : ℝ) (hk : 0 < k) : deriv (hyper k) 0 = 1 := by
  rw [(hyper_hasDerivAt k 0 hk).deriv]
  simp

theorem hyper_second_hasDerivAt (k s : ℝ) (hk : 0 < k) :
    HasDerivAt (fun t => deriv (hyper k) t) (k * hyper k s) s := by
  have hd : (fun t => deriv (hyper k) t) =
      (fun t => Real.cosh (Real.sqrt k * t)) := by
    funext t
    exact (hyper_hasDerivAt k t hk).deriv
  rw [hd]
  have h : HasDerivAt (fun t : ℝ => Real.cosh (Real.sqrt k * t))
      (Real.sinh (Real.sqrt k * s) * Real.sqrt k) s :=
    (Real.hasDerivAt_cosh _).comp s (hasDerivAt_const_mul _)
  convert h using 1
  simp only [hyper]
  field_simp [sqrt_ne k hk]
  rw [sqrt_sq k hk]

theorem hyper_second_deriv (k s : ℝ) (hk : 0 < k) :
    deriv (fun t => deriv (hyper k) t) s = k * hyper k s :=
  (hyper_second_hasDerivAt k s hk).deriv

private theorem primitive_hasDerivAt (k s t : ℝ) (hk : 0 < k) :
    HasDerivAt
      (fun u => (s - u) * Real.cosh (Real.sqrt k * u) +
        Real.sinh (Real.sqrt k * u) / Real.sqrt k)
      (k * ((s - t) * hyper k t)) t := by
  let a := Real.sqrt k
  have ha : a ≠ 0 := sqrt_ne k hk
  have hlin : HasDerivAt (fun u : ℝ => s - u) (-1) t := by
    convert (hasDerivAt_id t).const_sub s using 1 <;> try rfl
  have hcos : HasDerivAt (fun u : ℝ => Real.cosh (a * u))
      (Real.sinh (a * t) * a) t :=
    (Real.hasDerivAt_cosh _).comp t (hasDerivAt_const_mul _)
  have hsinh : HasDerivAt (fun u : ℝ => Real.sinh (a * u) / a)
      (Real.cosh (a * t) * a / a) t :=
    ((Real.hasDerivAt_sinh _).comp t (hasDerivAt_const_mul _)).div_const a
  convert (hlin.mul hcos).add hsinh using 1 <;> try rfl
  dsimp [hyper, a]
  field_simp [sqrt_ne k hk]
  conv_lhs => arg 1; rw [← sqrt_sq k hk]
  ring

theorem hyper_integral (k s : ℝ) (hk : 0 < k) (hs : 0 ≤ s) :
    k * (∫ t in (0 : ℝ)..s, (s - t) * hyper k t) = hyper k s - s := by
  let F : ℝ → ℝ := fun t => (s - t) * Real.cosh (Real.sqrt k * t) +
    Real.sinh (Real.sqrt k * t) / Real.sqrt k
  let G : ℝ → ℝ := fun t => k * ((s - t) * hyper k t)
  have hderiv : ∀ t ∈ Set.uIcc (0 : ℝ) s, HasDerivAt F (G t) t := by
    intro t _
    exact primitive_hasDerivAt k s t hk
  have hcont : Continuous G := by
    dsimp [G, hyper]
    fun_prop
  have hint : IntervalIntegrable G volume (0 : ℝ) s := hcont.intervalIntegrable _ _
  have hFTC := intervalIntegral.integral_eq_sub_of_hasDerivAt hderiv hint
  have hmul : (∫ t in (0 : ℝ)..s, G t) =
      k * (∫ t in (0 : ℝ)..s, (s - t) * hyper k t) := by
    simp [G, intervalIntegral.integral_const_mul]
  rw [hmul] at hFTC
  simpa [F, hyper] using hFTC

theorem flat_zero : flat 0 = 0 := rfl

theorem flat_hasDerivAt (s : ℝ) : HasDerivAt flat 1 s := by
  change HasDerivAt id 1 s
  exact hasDerivAt_id s

theorem flat_deriv_zero : deriv flat 0 = 1 := (flat_hasDerivAt 0).deriv

theorem flat_second_hasDerivAt (s : ℝ) :
    HasDerivAt (fun t => deriv flat t) (0 * flat s) s := by
  have hd : (fun t => deriv flat t) = fun _ : ℝ => (1 : ℝ) := by
    funext t
    exact (flat_hasDerivAt t).deriv
  simp [hd, hasDerivAt_const]

theorem flat_second_deriv (s : ℝ) : deriv (fun t => deriv flat t) s = 0 * flat s :=
  (flat_second_hasDerivAt s).deriv

theorem flat_integral (s : ℝ) (_hs : 0 ≤ s) :
    (0 : ℝ) * (∫ t in (0 : ℝ)..s, (s - t) * flat t) = flat s - s := by
  simp [flat]

private theorem sinh_ratio_right :
    Tendsto (fun x : ℝ => Real.sinh x / x) (𝓝[>] 0) (𝓝 1) := by
  have h := (Real.hasDerivAt_sinh 0).tendsto_slope_zero_right
  convert h using 1
  · funext x
    simp [smul_eq_mul, div_eq_mul_inv, mul_comm]
  · simp

theorem hyper_tendsto_flat (s : ℝ) (hs : 0 ≤ s) :
    Tendsto (fun k : ℝ => hyper k s) (𝓝[>] 0) (𝓝 (flat s)) := by
  rcases hs.eq_or_lt with rfl | hspos
  · simp [hyper, flat, tendsto_const_nhds]
  have harg : Tendsto (fun k : ℝ => Real.sqrt k * s)
      (𝓝[>] 0) (𝓝[>] 0) := by
    apply tendsto_nhdsWithin_iff.mpr
    constructor
    · convert ((Real.continuous_sqrt.tendsto 0).mono_left nhdsWithin_le_nhds).mul
          (tendsto_const_nhds (f := (𝓝[>] (0 : ℝ))) (x := s)) using 1 <;> simp
    · filter_upwards [self_mem_nhdsWithin] with k hk
      exact Set.mem_Ioi.mpr (mul_pos (Real.sqrt_pos.2 (Set.mem_Ioi.mp hk)) hspos)
  have hratio : Tendsto (fun k : ℝ => Real.sinh (Real.sqrt k * s) /
      (Real.sqrt k * s)) (𝓝[>] 0) (𝓝 1) := by
    exact sinh_ratio_right.comp harg
  have hprod : Tendsto (fun k : ℝ =>
      s * (Real.sinh (Real.sqrt k * s) / (Real.sqrt k * s)))
      (𝓝[>] 0) (𝓝 (flat s)) := by
    convert tendsto_const_nhds.mul hratio using 1 <;> simp [flat]
  apply hprod.congr'
  filter_upwards [self_mem_nhdsWithin] with k hk
  have hroot : Real.sqrt k ≠ 0 := sqrt_ne k (Set.mem_Ioi.mp hk)
  have hsne : s ≠ 0 := ne_of_gt hspos
  dsimp [hyper]
  field_simp

/-- All scalar claims packaged without any input initial condition or target identity. -/
theorem complete_target (k s : ℝ) (hk : 0 < k) (hs : 0 ≤ s) :
    hyper k 0 = 0 ∧ deriv (hyper k) 0 = 1 ∧
    deriv (fun t => deriv (hyper k) t) s = k * hyper k s ∧
    k * (∫ t in (0 : ℝ)..s, (s - t) * hyper k t) = hyper k s - s ∧
    flat 0 = 0 ∧ deriv flat 0 = 1 ∧
    deriv (fun t => deriv flat t) s = 0 * flat s ∧
    (0 : ℝ) * (∫ t in (0 : ℝ)..s, (s - t) * flat t) = flat s - s ∧
    Tendsto (fun x : ℝ => hyper x s) (𝓝[>] 0) (𝓝 (flat s)) := by
  exact ⟨hyper_zero k, hyper_deriv_zero k hk, hyper_second_deriv k s hk,
    hyper_integral k s hk hs, flat_zero, flat_deriv_zero,
    flat_second_deriv s, flat_integral s hs, hyper_tendsto_flat s hs⟩

#print axioms CAS07C01.hyper_zero
#print axioms CAS07C01.hyper_hasDerivAt
#print axioms CAS07C01.hyper_deriv_zero
#print axioms CAS07C01.hyper_second_hasDerivAt
#print axioms CAS07C01.hyper_second_deriv
#print axioms CAS07C01.hyper_integral
#print axioms CAS07C01.flat_zero
#print axioms CAS07C01.flat_hasDerivAt
#print axioms CAS07C01.flat_deriv_zero
#print axioms CAS07C01.flat_second_hasDerivAt
#print axioms CAS07C01.flat_second_deriv
#print axioms CAS07C01.flat_integral
#print axioms CAS07C01.hyper_tendsto_flat
#print axioms CAS07C01.complete_target

end CAS07C01
