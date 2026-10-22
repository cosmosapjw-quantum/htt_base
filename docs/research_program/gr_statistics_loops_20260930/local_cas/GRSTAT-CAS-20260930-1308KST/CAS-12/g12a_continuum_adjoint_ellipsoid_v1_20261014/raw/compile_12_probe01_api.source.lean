import Mathlib
import G11CWeightedEllipsoid
import G12DCardClosure
open MeasureTheory
#check @MeasureTheory.measurePreserving_prodAssoc
#check @MeasureTheory.MeasurePreserving.prod
#check @MeasureTheory.MeasurePreserving.prodMap
#check @MeasureTheory.Measure.measurePreserving_swap
#check @MeasureTheory.MeasurePreserving.integral_comp'
#check @MeasureTheory.MeasurePreserving.integrable_comp_emb
#check @MeasureTheory.MeasurePreserving.symm
#check @MeasurableEquiv.prodAssoc
#check @MeasurableEquiv.prodCongr
#check @MeasurableEquiv.prodComm
#check @MeasureTheory.Integrable.integral_prod_left
#check @MeasureTheory.Integrable.prod_right_ae
#check @MeasureTheory.integral_prod
#check @MeasureTheory.Integrable.comp_fst
#check @MeasureTheory.AEStronglyMeasurable.integral_prod_right'
#check @MeasureTheory.AEStronglyMeasurable.prodMk_left
#check @MeasureTheory.AEStronglyMeasurable.comp_quasiMeasurePreserving
#check @MeasureTheory.Measure.quasiMeasurePreserving_fst
#check @MeasureTheory.Measure.QuasiMeasurePreserving.ae
#check @MeasureTheory.MemLp.of_le_mul
#check @MeasureTheory.MemLp.toLp_congr
#check @MeasureTheory.MemLp.toLp_const_smul
#check @MeasureTheory.integral_fintype
#check @MeasureTheory.Integrable.of_finite
#check @MeasureTheory.withDensity_absolutelyContinuous
#check @MeasureTheory.AEStronglyMeasurable.mono_ac
#check @MeasureTheory.integral_const_mul
#check @MeasureTheory.Measure.toSphere
example : IsFiniteMeasure G11A.dOmega := by unfold G11A.dOmega; infer_instance
example : IsFiniteMeasure (Measure.count : Measure Bool) := by infer_instance
example (C : ℝ) : SFinite ((volume.restrict (Set.Ioi (0:ℝ))).withDensity (fun E => ENNReal.ofReal (C * E ^ 2))) := by infer_instance
example : OpensMeasurableSpace (G11A.Sphere2 × G11A.Sphere2) := by infer_instance
example : MeasurableSingletonClass ((Bool × Bool) × Bool) := by infer_instance
#check @G12DClosure.between_states_weight_bound
#print G12DClosure.between_states_weight_bound_type
#check @G11C.weighted_residual_ellipsoid
#check @G11C.all_retained
#check @Measure.count_singleton
