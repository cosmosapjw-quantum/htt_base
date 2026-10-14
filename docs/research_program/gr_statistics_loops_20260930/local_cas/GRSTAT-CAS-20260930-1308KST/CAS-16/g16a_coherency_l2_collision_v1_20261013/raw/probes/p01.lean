import Mathlib
import ProjectorBridge
open MeasureTheory Metric
attribute [local instance] Matrix.frobeniusNormedAddCommGroup Matrix.frobeniusNormedSpace
abbrev E3 := EuclideanSpace ℝ (Fin 3)
abbrev CMat := Matrix (Fin 3) (Fin 3) ℂ
#synth CompleteSpace CMat
#synth NormedSpace ℝ CMat
#synth MeasurableSpace (sphere (0:E3) 1)
#synth BorelSpace (sphere (0:E3) 1)
#check (volume : Measure E3).toSphere
example : (volume : Measure E3).toSphere Set.univ = ENNReal.ofReal (4 * Real.pi) := by
  rw [Measure.toSphere_apply_univ, volume_ball_fin_three]
  simp
  sorry
example (x : sphere (0:E3) 1) : ∑ i, (x : E3) i * (x : E3) i = 1 := by
  have := x.2
  sorry
#check @eLpNorm_le_eLpNorm_mul_rpow_measure_univ
#check @eLpNorm_le_of_ae_bound
#check @MemLp.of_bound
#check @norm_integral_le_integral_norm
#check @eLpNorm_add_le
#check @eLpNorm_const_smul
#check @MemLp.toLp_add
#check @LinearMap.mkContinuous
#check @eLpNorm_smul_measure_of_ne_top
#check @integral_smul_measure
#check @Lp.norm_def
#check @MemLp.eLpNorm_lt_top
#check @Complex.sq_norm
#check @Complex.normSq_apply
#check @MemLp.integrable
