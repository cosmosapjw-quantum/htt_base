import Mathlib
open Filter Topology MeasureTheory
#check @Filter.Tendsto.add_atTop
#check @Filter.Tendsto.pos_mul_atTop
#check @Real.tendsto_log_nhdsGT_zero
#check @ConvexOn.slope_le_of_hasDerivAt
#check @ConvexOn.le_slope_of_hasDerivAt
#check @Real.continuous_mul_log
#check @Real.hasDerivAt_mul_log
#check @MeasureTheory.lintegral_ofReal_ne_top_iff_integrable
#check @MeasureTheory.ofReal_integral_eq_lintegral_ofReal
#check @MeasureTheory.integral_undef
#check @MeasureTheory.tendsto_integral_of_dominated_convergence
#check @interior_Ici
#check @interior_Icc
noncomputable def sph : Measure (Metric.sphere (0 : EuclideanSpace ℝ (Fin 3)) 1) := (volume : Measure (EuclideanSpace ℝ (Fin 3))).toSphere
noncomputable def nu (C : ℝ) : Measure (ℝ × Metric.sphere (0 : EuclideanSpace ℝ (Fin 3)) 1) :=
  ((volume.restrict (Set.Ioi (0:ℝ))).withDensity (fun E => ENNReal.ofReal (C * E^2))).prod sph
