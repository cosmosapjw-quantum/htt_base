import Mathlib
open MeasureTheory
attribute [local instance] Matrix.frobeniusNormedAddCommGroup Matrix.frobeniusNormedSpace
  Matrix.frobeniusNormSMulClass Matrix.frobeniusIsBoundedSMul
abbrev CMat := Matrix (Fin 3) (Fin 3) ℂ
set_option pp.explicit true in
#synth TopologicalSpace CMat
example : (inferInstance : TopologicalSpace CMat) =
    @UniformSpace.toTopologicalSpace CMat (@PseudoMetricSpace.toUniformSpace CMat
      (@SeminormedAddCommGroup.toPseudoMetricSpace CMat (@NormedAddCommGroup.toSeminormedAddCommGroup CMat Matrix.frobeniusNormedAddCommGroup))) := by
  with_reducible_and_instances rfl
example : (inferInstance : TopologicalSpace CMat) =
    @UniformSpace.toTopologicalSpace CMat (@PseudoMetricSpace.toUniformSpace CMat
      (@SeminormedAddCommGroup.toPseudoMetricSpace CMat (@NormedAddCommGroup.toSeminormedAddCommGroup CMat Matrix.frobeniusNormedAddCommGroup))) := by
  rfl
#synth TopologicalSpace.PseudoMetrizableSpace (Fin 3 → Fin 3 → ℂ)
#synth TopologicalSpace.SecondCountableTopology CMat
#synth OpensMeasurableSpace CMat
#synth MeasurableSpace CMat
example {X : Type} [MeasurableSpace X] (μ : Measure X) (f g : X → CMat) (hf : AEStronglyMeasurable f μ) (hg : AEStronglyMeasurable g μ) :
  eLpNorm (f + g) 2 μ ≤ eLpNorm f 2 μ + eLpNorm g 2 μ := eLpNorm_add_le hf hg (by norm_num)
