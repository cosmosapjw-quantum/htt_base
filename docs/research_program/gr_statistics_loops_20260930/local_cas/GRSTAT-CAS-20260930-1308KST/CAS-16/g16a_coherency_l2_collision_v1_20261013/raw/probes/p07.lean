import Mathlib
open MeasureTheory
attribute [local instance] Matrix.frobeniusNormedAddCommGroup Matrix.frobeniusNormedSpace
  Matrix.frobeniusNormSMulClass Matrix.frobeniusIsBoundedSMul
abbrev CMat := Matrix (Fin 3) (Fin 3) ℂ
/-- Frobenius-metric topology, made the preferred instance (defeq to the product topology). -/
@[reducible] def frobTop : TopologicalSpace CMat :=
  @UniformSpace.toTopologicalSpace CMat (@PseudoMetricSpace.toUniformSpace CMat
      (@SeminormedAddCommGroup.toPseudoMetricSpace CMat (@NormedAddCommGroup.toSeminormedAddCommGroup CMat Matrix.frobeniusNormedAddCommGroup)))
attribute [local instance high] frobTop
example {X : Type} [MeasurableSpace X] (μ : Measure X) (f g : X → CMat) (hf : AEStronglyMeasurable f μ) (hg : AEStronglyMeasurable g μ) :
  eLpNorm (f + g) 2 μ ≤ eLpNorm f 2 μ + eLpNorm g 2 μ := eLpNorm_add_le hf hg (by norm_num)
example {X : Type} [TopologicalSpace X] (f : X → CMat) (hf : ∀ i j, Continuous fun x => f x i j) : Continuous f := by
  have : @Continuous X CMat _ (instTopologicalSpaceMatrix) f := continuous_pi fun i => continuous_pi fun j => hf i j
  exact this
#synth TopologicalSpace.PseudoMetrizableSpace CMat
example {X : Type} [TopologicalSpace X] (f g : X → CMat) (hf : Continuous f) (hg : Continuous g) : Continuous (fun x => f x * g x) := by
  exact hf.matrix_mul hg
