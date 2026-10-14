import Mathlib
import G12ECounterexample
open MeasureTheory
#check @Real.HolderConjugate.two_two
#check @ENNReal.lintegral_mul_le_Lp_mul_Lq
#check @hasDerivAt_integral_of_dominated_loc_of_deriv_le
#check @ofReal_integral_eq_lintegral_ofReal
#check @ae_lt_top
#check @ENNReal.ofReal_rpow_of_nonneg
#check @Real.sqrt_eq_rpow
#check @norm_integral_le_lintegral_norm
#check @norm_integral_le_of_norm_le
#check @IsLocalMin.hasDerivAt_eq_zero
#check @measurableSet_eq_fun
#check @G12DClosure.angular_bounded_rpow_kernel_integrable
#check @G12DClosure.between_states_weight_bound
#check @G12DClosure.no_nonpositive_energy_mass
#check @G12E.fisher_unbounded
#check @G12E.nu_facts
#check @EuclideanSpace.norm_eq
example (e : G11A.Sphere2) : ℝ := (e : EuclideanSpace ℝ (Fin 3)) 0
example (e : G11A.Sphere2) (k : Fin 3) : |(e : EuclideanSpace ℝ (Fin 3)) k| ≤ 1 := by
  have h1 : ‖(e : EuclideanSpace ℝ (Fin 3))‖ = 1 := by simp
  have := PiLp.norm_apply_le (e : EuclideanSpace ℝ (Fin 3)) k
  rw [Real.norm_eq_abs] at this; linarith
example (k : Fin 3) : Continuous (fun e : G11A.Sphere2 => (e : EuclideanSpace ℝ (Fin 3)) k) := by
  fun_prop
#check (inferInstance : IsFiniteMeasure G11A.dOmega)
