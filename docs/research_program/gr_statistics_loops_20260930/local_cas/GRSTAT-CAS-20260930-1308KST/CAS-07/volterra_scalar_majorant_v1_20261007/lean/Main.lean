import Mathlib
import Mathlib.Analysis.SpecialFunctions.Integrals.Basic
import Mathlib.Analysis.SpecialFunctions.Trigonometric.Series

/-!
CAS-07-M03 Lean axis. This file contains only proved auxiliary statements.
The universal K>0 comparison target is not declared unless its entire proof compiles.
-/

open Set intervalIntegral MeasureTheory

namespace CAS07M03

noncomputable def T (K : ℝ) (v : ℝ → ℝ) (x : ℝ) : ℝ :=
  K * ∫ t in 0..x, (x - t) * v t

noncomputable def f (K x : ℝ) : ℝ :=
  if K = 0 then x else Real.sinh (Real.sqrt K * x) / Real.sqrt K

theorem f_zero (x : ℝ) : f 0 x = x := by simp [f]

theorem comparison_K0 (L : ℝ) (u : ℝ → ℝ)
    (hsub : ∀ x ∈ Icc 0 L, u x ≤ x + T 0 u x) :
    ∀ x ∈ Icc 0 L, u x ≤ f 0 x := by
  intro x hx
  simpa [T, f] using hsub x hx

theorem T_mono (K x : ℝ) (hK : 0 ≤ K) (hx : 0 ≤ x)
    {v w : ℝ → ℝ} (hv : ContinuousOn v (Icc 0 x))
    (hw : ContinuousOn w (Icc 0 x))
    (hvw : ∀ t ∈ Icc 0 x, v t ≤ w t) :
    T K v x ≤ T K w x := by
  unfold T
  apply mul_le_mul_of_nonneg_left _ hK
  apply intervalIntegral.integral_mono_on hx
  · exact ((continuousOn_const.sub continuousOn_id).mul hv).intervalIntegrable_of_Icc hx
  · exact ((continuousOn_const.sub continuousOn_id).mul hw).intervalIntegrable_of_Icc hx
  · intro t ht
    exact mul_le_mul_of_nonneg_left (hvw t ht) (sub_nonneg.mpr ht.2)

theorem T_continuousOn (K L : ℝ) (hL : 0 ≤ L) {v : ℝ → ℝ}
    (hv : ContinuousOn v (Icc 0 L)) :
    ContinuousOn (T K v) (Icc 0 L) := by
  have hvint : IntervalIntegrable v volume 0 L := hv.intervalIntegrable_of_Icc hL
  have htv : ContinuousOn (fun t : ℝ => t * v t) (Icc 0 L) :=
    continuousOn_id.mul hv
  have htvint : IntervalIntegrable (fun t : ℝ => t * v t) volume 0 L :=
    htv.intervalIntegrable_of_Icc hL
  have hpv : ContinuousOn (fun x => ∫ t in 0..x, v t) (Icc 0 L) := by
    simpa only [uIcc_of_le hL] using
      (continuousOn_primitive_interval' hvint (by simp [hL] : (0 : ℝ) ∈ uIcc 0 L))
  have hptv : ContinuousOn (fun x => ∫ t in 0..x, t * v t) (Icc 0 L) := by
    simpa only [uIcc_of_le hL] using
      (continuousOn_primitive_interval' htvint (by simp [hL] : (0 : ℝ) ∈ uIcc 0 L))
  have hform : ∀ x ∈ Icc 0 L,
      T K v x = K * (x * (∫ t in 0..x, v t) - ∫ t in 0..x, t * v t) := by
    intro x hx
    unfold T
    have hxint : IntervalIntegrable v volume 0 x :=
      (hv.mono (Icc_subset_Icc le_rfl hx.2)).intervalIntegrable_of_Icc hx.1
    have htxint : IntervalIntegrable (fun t : ℝ => t * v t) volume 0 x :=
      (htv.mono (Icc_subset_Icc le_rfl hx.2)).intervalIntegrable_of_Icc hx.1
    have hcxint : IntervalIntegrable (fun t : ℝ => x * v t) volume 0 x := by
      exact hxint.const_mul x
    congr 1
    calc
      (∫ t in 0..x, (x - t) * v t) =
          ∫ t in 0..x, (x * v t - t * v t) := by
            congr 1; funext t; ring
      _ = x * (∫ t in 0..x, v t) - ∫ t in 0..x, t * v t := by
            rw [intervalIntegral.integral_sub hcxint htxint,
              intervalIntegral.integral_const_mul]
  have hc : ContinuousOn
      (fun x => K * (x * (∫ t in 0..x, v t) - ∫ t in 0..x, t * v t))
      (Icc 0 L) :=
    continuousOn_const.mul ((continuousOn_id.mul hpv).sub hptv)
  refine hc.congr ?_
  intro x hx
  exact hform x hx

theorem T_add (K x : ℝ) {v w : ℝ → ℝ}
    (hv : ContinuousOn v (Icc 0 x)) (hw : ContinuousOn w (Icc 0 x))
    (hx : 0 ≤ x) :
    T K (fun t => v t + w t) x = T K v x + T K w x := by
  have hvi : IntervalIntegrable (fun t : ℝ => (x - t) * v t) volume 0 x :=
    ((continuousOn_const.sub continuousOn_id).mul hv).intervalIntegrable_of_Icc hx
  have hwi : IntervalIntegrable (fun t : ℝ => (x - t) * w t) volume 0 x :=
    ((continuousOn_const.sub continuousOn_id).mul hw).intervalIntegrable_of_Icc hx
  unfold T
  simp_rw [mul_add]
  rw [intervalIntegral.integral_add hvi hwi]
  ring

theorem kernel_monomial_integral (x : ℝ) (n : ℕ) :
    (∫ t in 0..x, (x - t) * t ^ n) =
      x ^ (n + 2) / (((n + 1 : ℕ) : ℝ) * ((n + 2 : ℕ) : ℝ)) := by
  have hi₁ : IntervalIntegrable (fun t : ℝ => x * t ^ n) volume 0 x := by
    exact (by fun_prop : Continuous (fun t : ℝ => x * t ^ n)).intervalIntegrable 0 x
  have hi₂ : IntervalIntegrable (fun t : ℝ => t ^ (n + 1)) volume 0 x := by
    exact (by fun_prop : Continuous (fun t : ℝ => t ^ (n + 1))).intervalIntegrable 0 x
  calc
    (∫ t in 0..x, (x - t) * t ^ n) =
        ∫ t in 0..x, (x * t ^ n - t ^ (n + 1)) := by
          congr 1; funext t; ring
    _ = x * (∫ t in 0..x, t ^ n) - (∫ t in 0..x, t ^ (n + 1)) := by
          rw [intervalIntegral.integral_sub hi₁ hi₂, intervalIntegral.integral_const_mul]
    _ = x ^ (n + 2) / (((n + 1 : ℕ) : ℝ) * ((n + 2 : ℕ) : ℝ)) := by
          rw [integral_pow, integral_pow]
          simp only [zero_pow (by omega : n + 1 ≠ 0), sub_zero]
          have hn₁ : (((n + 1 : ℕ) : ℝ)) ≠ 0 := by exact_mod_cast (by omega : n + 1 ≠ 0)
          have hn₂ : (((n + 2 : ℕ) : ℝ)) ≠ 0 := by exact_mod_cast (by omega : n + 2 ≠ 0)
          field_simp
          push_cast
          ring

noncomputable def term (K : ℝ) (n : ℕ) (x : ℝ) : ℝ :=
  K ^ n * x ^ (2 * n + 1) / (Nat.factorial (2 * n + 1) : ℝ)

theorem term_zero (K x : ℝ) : term K 0 x = x := by
  simp [term]

theorem T_term (K x : ℝ) (n : ℕ) : T K (term K n) x = term K (n + 1) x := by
  let m := 2 * n + 1
  have hm : (Nat.factorial m : ℝ) ≠ 0 := by positivity
  have hfactor : (Nat.factorial (m + 2) : ℝ) =
      (Nat.factorial m : ℝ) * ((m + 1 : ℕ) : ℝ) * ((m + 2 : ℕ) : ℝ) := by
    simp only [Nat.factorial_succ]
    push_cast
    ring
  calc
    T K (term K n) x =
        K * ((K ^ n / (Nat.factorial m : ℝ)) *
          ∫ t in 0..x, (x - t) * t ^ m) := by
            unfold T
            congr 1
            rw [← intervalIntegral.integral_const_mul]
            congr 1
            funext t
            dsimp [term, m]
            ring
    _ = K * ((K ^ n / (Nat.factorial m : ℝ)) *
          (x ^ (m + 2) / (((m + 1 : ℕ) : ℝ) * ((m + 2 : ℕ) : ℝ)))) := by
            rw [kernel_monomial_integral]
    _ = term K (n + 1) x := by
          have hpow : 2 * (n + 1) + 1 = m + 2 := by dsimp [m]; omega
          simp only [term, hpow]
          rw [hfactor]
          ring

noncomputable def partialSum (K : ℝ) (n : ℕ) (x : ℝ) : ℝ :=
  ∑ j ∈ Finset.range n, term K j x

theorem partialSum_continuous (K : ℝ) (n : ℕ) : Continuous (partialSum K n) := by
  induction n with
  | zero =>
      have hzero : partialSum K 0 = fun _ : ℝ => (0 : ℝ) := by
        funext x
        simp [partialSum]
      rw [hzero]
      exact continuous_const
  | succ n ih =>
      have ht : Continuous (term K n) := by unfold term; fun_prop
      have hsum : partialSum K (n + 1) = partialSum K n + term K n := by
        funext x
        simp [partialSum, Finset.sum_range_succ]
      rw [hsum]
      exact ih.add ht

theorem T_partialSum (K x : ℝ) (n : ℕ) :
    T K (partialSum K n) x = partialSum K (n + 1) x - x := by
  have hi : ∀ j ∈ Finset.range n,
      IntervalIntegrable (fun t : ℝ => (x - t) * term K j t) volume 0 x := by
    intro j _
    have hct : Continuous (term K j) := by unfold term; fun_prop
    exact ((continuous_const.sub continuous_id).mul hct).intervalIntegrable 0 x
  calc
    T K (partialSum K n) x =
        K * ∫ t in 0..x, ∑ j ∈ Finset.range n, (x - t) * term K j t := by
          unfold T partialSum
          congr 1
          congr 1
          funext t
          rw [Finset.mul_sum]
    _ = K * ∑ j ∈ Finset.range n, ∫ t in 0..x, (x - t) * term K j t := by
          rw [intervalIntegral.integral_finsetSum hi]
    _ = ∑ j ∈ Finset.range n, T K (term K j) x := by
          simp only [T, Finset.mul_sum]
    _ = ∑ j ∈ Finset.range n, term K (j + 1) x := by
          simp_rw [T_term]
    _ = partialSum K (n + 1) x - x := by
          simp [partialSum, Finset.sum_range_succ', term_zero]

theorem term_sqrt (K x : ℝ) (hK : 0 ≤ K) (hK0 : K ≠ 0) (n : ℕ) :
    term K n x =
      ((Real.sqrt K * x) ^ (2 * n + 1) / (Nat.factorial (2 * n + 1) : ℝ)) /
        Real.sqrt K := by
  have hsq : Real.sqrt K ^ 2 = K := Real.sq_sqrt hK
  have hsne : Real.sqrt K ≠ 0 := (Real.sqrt_ne_zero hK).mpr hK0
  have hfne : (Nat.factorial (2 * n + 1) : ℝ) ≠ 0 := by positivity
  have hpow : (Real.sqrt K * x) ^ (2 * n + 1) =
      Real.sqrt K * K ^ n * x ^ (2 * n + 1) := by
    rw [mul_pow, pow_add, pow_mul, hsq]
    ring
  rw [hpow]
  dsimp [term]
  field_simp

theorem summable_term (K x : ℝ) (hK : 0 ≤ K) (hK0 : K ≠ 0) :
    Summable (fun n : ℕ => term K n x) := by
  have hs := (Real.hasSum_sinh (Real.sqrt K * x)).summable
  have hs' : Summable (fun n : ℕ =>
      ((Real.sqrt K * x) ^ (2 * n + 1) / (Nat.factorial (2 * n + 1) : ℝ)) /
        Real.sqrt K) := by
    exact hs.div_const (Real.sqrt K)
  simpa only [term_sqrt K x hK hK0] using hs'

theorem summable_abs_term (K x : ℝ) (hK : 0 ≤ K) (hK0 : K ≠ 0)
    (hx : 0 ≤ x) : Summable (fun n : ℕ => |term K n x|) := by
  have hnonneg (n : ℕ) : 0 ≤ term K n x := by
    unfold term
    positivity
  have heq : (fun n : ℕ => |term K n x|) = (fun n : ℕ => term K n x) := by
    funext n
    exact abs_of_nonneg (hnonneg n)
  rw [heq]
  exact summable_term K x hK hK0

theorem f_eq_tsum_term (K x : ℝ) (hK : 0 ≤ K) (hK0 : K ≠ 0) :
    f K x = ∑' n : ℕ, term K n x := by
  calc
    f K x = Real.sinh (Real.sqrt K * x) / Real.sqrt K := by simp [f, hK0]
    _ = (∑' n : ℕ, (Real.sqrt K * x) ^ (2 * n + 1) /
          (Nat.factorial (2 * n + 1) : ℝ)) / Real.sqrt K := by
            rw [Real.sinh_eq_tsum]
    _ = ∑' n : ℕ, term K n x := by
          rw [← tsum_div_const]
          congr 1
          funext n
          exact (term_sqrt K x hK hK0 n).symm

theorem continuousOn_bounded_above {L : ℝ} {u : ℝ → ℝ}
    (hu : ContinuousOn u (Icc 0 L)) :
    ∃ M : ℝ, ∀ x ∈ Icc 0 L, u x ≤ M := by
  let M := sSup (u '' Icc 0 L)
  refine ⟨M, ?_⟩
  intro x hx
  exact le_csSup (isCompact_Icc.bddAbove_image hu) ⟨x, hx, rfl⟩

noncomputable def remainderTerm (K M : ℝ) (n : ℕ) (x : ℝ) : ℝ :=
  M * K ^ n * x ^ (2 * n) / (Nat.factorial (2 * n) : ℝ)

theorem remainderTerm_zero (K M x : ℝ) : remainderTerm K M 0 x = M := by
  simp [remainderTerm]

theorem T_remainderTerm (K M x : ℝ) (n : ℕ) :
    T K (remainderTerm K M n) x = remainderTerm K M (n + 1) x := by
  let m := 2 * n
  have hm : (Nat.factorial m : ℝ) ≠ 0 := by positivity
  have hfactor : (Nat.factorial (m + 2) : ℝ) =
      (Nat.factorial m : ℝ) * ((m + 1 : ℕ) : ℝ) * ((m + 2 : ℕ) : ℝ) := by
    simp only [Nat.factorial_succ]
    push_cast
    ring
  calc
    T K (remainderTerm K M n) x =
        K * (((M * K ^ n) / (Nat.factorial m : ℝ)) *
          ∫ t in 0..x, (x - t) * t ^ m) := by
            unfold T
            congr 1
            rw [← intervalIntegral.integral_const_mul]
            congr 1
            funext t
            dsimp [remainderTerm, m]
            ring
    _ = K * (((M * K ^ n) / (Nat.factorial m : ℝ)) *
          (x ^ (m + 2) / (((m + 1 : ℕ) : ℝ) * ((m + 2 : ℕ) : ℝ)))) := by
            rw [kernel_monomial_integral]
    _ = remainderTerm K M (n + 1) x := by
          have hpow : 2 * (n + 1) = m + 2 := by dsimp [m]; omega
          simp only [remainderTerm, hpow]
          rw [hfactor]
          ring

theorem remainderTerm_eq_coshTerm (K M x : ℝ) (hK : 0 ≤ K) (n : ℕ) :
    remainderTerm K M n x =
      M * ((Real.sqrt K * x) ^ (2 * n) / (Nat.factorial (2 * n) : ℝ)) := by
  have hsq : Real.sqrt K ^ 2 = K := Real.sq_sqrt hK
  have hpow : (Real.sqrt K * x) ^ (2 * n) = K ^ n * x ^ (2 * n) := by
    rw [mul_pow, pow_mul, hsq]
  rw [hpow]
  dsimp [remainderTerm]
  ring

theorem remainderTerm_tendsto_zero (K M x : ℝ) (hK : 0 ≤ K) :
    Filter.Tendsto (fun n : ℕ => remainderTerm K M n x) Filter.atTop (nhds 0) := by
  have hs := (Real.hasSum_cosh (Real.sqrt K * x)).summable
  have hs' : Summable (fun n : ℕ =>
      M * ((Real.sqrt K * x) ^ (2 * n) / (Nat.factorial (2 * n) : ℝ))) :=
    hs.mul_left M
  have heq : (fun n : ℕ => remainderTerm K M n x) =
      (fun n : ℕ => M * ((Real.sqrt K * x) ^ (2 * n) /
        (Nat.factorial (2 * n) : ℝ))) := by
    funext n
    exact remainderTerm_eq_coshTerm K M x hK n
  rw [heq]
  exact hs'.tendsto_atTop_zero

noncomputable def iterateT (K : ℝ) (u : ℝ → ℝ) (n : ℕ) : ℝ → ℝ :=
  (T K)^[n] u

theorem iterateT_continuousOn (K L : ℝ) (hL : 0 ≤ L) {u : ℝ → ℝ}
    (hu : ContinuousOn u (Icc 0 L)) (n : ℕ) :
    ContinuousOn (iterateT K u n) (Icc 0 L) := by
  induction n with
  | zero => simpa [iterateT] using hu
  | succ n ih =>
      simpa [iterateT, Function.iterate_succ_apply'] using T_continuousOn K L hL ih

theorem iterateT_remainder_bound (K L M : ℝ) (hK : 0 ≤ K) (hL : 0 ≤ L)
    {u : ℝ → ℝ} (hu : ContinuousOn u (Icc 0 L))
    (hM : ∀ x ∈ Icc 0 L, u x ≤ M) :
    ∀ n : ℕ, ∀ x ∈ Icc 0 L, iterateT K u n x ≤ remainderTerm K M n x := by
  intro n
  induction n with
  | zero =>
      intro x hx
      simpa [iterateT, remainderTerm] using hM x hx
  | succ n ih =>
      intro x hx
      have hcont : ContinuousOn (remainderTerm K M n) (Icc 0 x) := by
        unfold remainderTerm
        fun_prop
      have hstep := T_mono K x hK hx.1
        ((iterateT_continuousOn K L hL hu n).mono (Icc_subset_Icc le_rfl hx.2))
        hcont (fun t ht => ih t (Icc_subset_Icc le_rfl hx.2 ht))
      simpa only [iterateT, Function.iterate_succ_apply', T_remainderTerm] using hstep

theorem finite_comparison (K L : ℝ) (hK : 0 ≤ K) (hL : 0 ≤ L)
    {u : ℝ → ℝ} (hu : ContinuousOn u (Icc 0 L))
    (hsub : ∀ x ∈ Icc 0 L, u x ≤ x + T K u x) :
    ∀ n : ℕ, ∀ x ∈ Icc 0 L,
      u x ≤ partialSum K n x + iterateT K u n x := by
  intro n
  induction n with
  | zero =>
      intro x hx
      simp [partialSum, iterateT]
  | succ n ih =>
      intro x hx
      have hps : ContinuousOn (partialSum K n) (Icc 0 x) :=
        (partialSum_continuous K n).continuousOn
      have hit : ContinuousOn (iterateT K u n) (Icc 0 x) :=
        (iterateT_continuousOn K L hL hu n).mono (Icc_subset_Icc le_rfl hx.2)
      have hsum : ContinuousOn
          (fun t => partialSum K n t + iterateT K u n t) (Icc 0 x) :=
        hps.add hit
      have hmono := T_mono K x hK hx.1
        (hu.mono (Icc_subset_Icc le_rfl hx.2)) hsum
        (fun t ht => ih t (Icc_subset_Icc le_rfl hx.2 ht))
      calc
        u x ≤ x + T K u x := hsub x hx
        _ ≤ x + T K (fun t => partialSum K n t + iterateT K u n t) x :=
          add_le_add le_rfl hmono
        _ = partialSum K (n + 1) x + iterateT K u (n + 1) x := by
          rw [T_add K x hps hit hx.1, T_partialSum]
          simp only [iterateT, Function.iterate_succ_apply']
          ring

theorem scalar_volterra_comparison (K L : ℝ) (hK : 0 ≤ K) (hL : 0 < L)
    (u : ℝ → ℝ) (hu : ContinuousOn u (Icc 0 L))
    (_hu_nonneg : ∀ x ∈ Icc 0 L, 0 ≤ u x)
    (hsub : ∀ x ∈ Icc 0 L, u x ≤ x + T K u x) :
    ∀ x ∈ Icc 0 L, u x ≤ f K x := by
  by_cases hK0 : K = 0
  · subst K
    exact comparison_K0 L u hsub
  · obtain ⟨M, hM⟩ := continuousOn_bounded_above hu
    intro x hx
    have hps : Filter.Tendsto (fun n : ℕ => partialSum K n x)
        Filter.atTop (nhds (f K x)) := by
      rw [f_eq_tsum_term K x hK hK0]
      simpa only [partialSum] using
        (summable_term K x hK hK0).hasSum.tendsto_sum_nat
    have hrem := remainderTerm_tendsto_zero K M x hK
    have hlim : Filter.Tendsto
        (fun n : ℕ => partialSum K n x + remainderTerm K M n x)
        Filter.atTop (nhds (f K x)) := by
      simpa using hps.add hrem
    apply ge_of_tendsto hlim
    apply Filter.Eventually.of_forall
    intro n
    exact (finite_comparison K L hK hL.le hu hsub n x hx).trans
      (add_le_add le_rfl (iterateT_remainder_bound K L M hK hL.le hu hM n x hx))

end CAS07M03

#print axioms CAS07M03.comparison_K0
#print axioms CAS07M03.T_mono
#print axioms CAS07M03.T_add
#print axioms CAS07M03.kernel_monomial_integral
#print axioms CAS07M03.T_term
#print axioms CAS07M03.T_partialSum
#print axioms CAS07M03.summable_term
#print axioms CAS07M03.summable_abs_term
#print axioms CAS07M03.f_eq_tsum_term
#print axioms CAS07M03.continuousOn_bounded_above
#print axioms CAS07M03.remainderTerm_tendsto_zero
#print axioms CAS07M03.T_remainderTerm
#print axioms CAS07M03.T_continuousOn
#print axioms CAS07M03.iterateT_remainder_bound
#print axioms CAS07M03.finite_comparison
#print axioms CAS07M03.scalar_volterra_comparison
