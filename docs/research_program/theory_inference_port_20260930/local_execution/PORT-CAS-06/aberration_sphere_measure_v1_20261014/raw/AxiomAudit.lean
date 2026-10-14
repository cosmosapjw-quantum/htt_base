import Mathlib
import P06ASphere

open P06ASphere PortCas01 P06AOptics MeasureTheory

/-! Frozen-target types (F1-F10) and every public lemma: #check + #print axioms. -/

#check @P06ASphere.inner_eq3
#print axioms P06ASphere.inner_eq3
#check @P06ASphere.norm_sq3
#print axioms P06ASphere.norm_sq3
#check @P06ASphere.sphere_s
#print axioms P06ASphere.sphere_s
#check @P06ASphere.norm_of_sq_one
#print axioms P06ASphere.norm_of_sq_one
#check @P06ASphere.inner_bvec
#print axioms P06ASphere.inner_bvec
#check @P06ASphere.norm_bvec_sq
#print axioms P06ASphere.norm_bvec_sq
#check @P06ASphere.bvec_neg
#print axioms P06ASphere.bvec_neg
#check @P06ASphere.h_mul
#print axioms P06ASphere.h_mul
#check @P06ASphere.neg_adm
#print axioms P06ASphere.neg_adm
#check @P06ASphere.continuous_coord
#print axioms P06ASphere.continuous_coord
#check @P06ASphere.continuous_dopS
#print axioms P06ASphere.continuous_dopS
#check @P06ASphere.dopS_pos
#print axioms P06ASphere.dopS_pos
#check @P06ASphere.aberrV_mem_sphere
#print axioms P06ASphere.aberrV_mem_sphere
#check @P06ASphere.aberrS_same_ray
#print axioms P06ASphere.aberrS_same_ray
#check @P06ASphere.coneMap_zero
#print axioms P06ASphere.coneMap_zero
#check @P06ASphere.coneMap_smul
#print axioms P06ASphere.coneMap_smul
#check @P06ASphere.coneMap_sphere
#print axioms P06ASphere.coneMap_sphere
#check @P06ASphere.coneMap_ray
#print axioms P06ASphere.coneMap_ray
#check @P06ASphere.coneMap_norm
#print axioms P06ASphere.coneMap_norm
#check @P06ASphere.coneMap_inv
#print axioms P06ASphere.coneMap_inv
#check @P06ASphere.coneMap_inv'
#print axioms P06ASphere.coneMap_inv'
#check @P06ASphere.coneMap_image
#print axioms P06ASphere.coneMap_image
#check @P06ASphere.coneMap_injOn
#print axioms P06ASphere.coneMap_injOn
#check @P06ASphere.hasFDerivAt_norm3
#print axioms P06ASphere.hasFDerivAt_norm3
#check @P06ASphere.coneMap_hasFDerivAt
#print axioms P06ASphere.coneMap_hasFDerivAt
#check @P06ASphere.det_rank_one
#print axioms P06ASphere.det_rank_one
#check @P06ASphere.coneDeriv_eq
#print axioms P06ASphere.coneDeriv_eq
#check @P06ASphere.coneMap_jacobian
#print axioms P06ASphere.coneMap_jacobian
#check @P06ASphere.aberrS_coe
#print axioms P06ASphere.aberrS_coe
#check @P06ASphere.aberrS_inv_gen
#print axioms P06ASphere.aberrS_inv_gen
#check @P06ASphere.aberrS_left
#print axioms P06ASphere.aberrS_left
#check @P06ASphere.aberrS_right
#print axioms P06ASphere.aberrS_right
#check @P06ASphere.continuous_coneMap
#print axioms P06ASphere.continuous_coneMap
#check @P06ASphere.aberrS_continuous
#print axioms P06ASphere.aberrS_continuous
#check @P06ASphere.aberrS_bijective
#print axioms P06ASphere.aberrS_bijective
#check @P06ASphere.lintegral_polar
#print axioms P06ASphere.lintegral_polar
#check @P06ASphere.radial_Iio
#print axioms P06ASphere.radial_Iio
#check @P06ASphere.radial_one
#print axioms P06ASphere.radial_one
#check @P06ASphere.mem_coneSet_smul
#print axioms P06ASphere.mem_coneSet_smul
#check @P06ASphere.ind_congr
#print axioms P06ASphere.ind_congr
#check @P06ASphere.measurable_dens
#print axioms P06ASphere.measurable_dens
#check @P06ASphere.key_identity
#print axioms P06ASphere.key_identity
#check @P06ASphere.aberr_pushforward
#print axioms P06ASphere.aberr_pushforward
#check @P06ASphere.aberr_integral
#print axioms P06ASphere.aberr_integral
#check @P06ASphere.solidAngleNew_eq
#print axioms P06ASphere.solidAngleNew_eq
#check @P06ASphere.areaDist_scale
#print axioms P06ASphere.areaDist_scale
#check @P06ASphere.areaDist_sphere
#print axioms P06ASphere.areaDist_sphere
#check @P06ASphere.endpoint_optical_sphere
#print axioms P06ASphere.endpoint_optical_sphere
#check @P06ASphere.beta_zero_admissible
#print axioms P06ASphere.beta_zero_admissible
#check @P06ASphere.endpoint_optical_sphere_beta_zero
#print axioms P06ASphere.endpoint_optical_sphere_beta_zero
#check @P06ASphere.witness_admissible
#print axioms P06ASphere.witness_admissible
#check @P06ASphere.pushforward_without_density_ne
#print axioms P06ASphere.pushforward_without_density_ne

/-! Definitions used by the frozen statements -/
#print axioms P06ASphere.σS
#print axioms P06ASphere.bvec
#print axioms P06ASphere.dopS
#print axioms P06ASphere.aberrV
#print axioms P06ASphere.aberrS
#print axioms P06ASphere.dens
#print axioms P06ASphere.solidAngleNew
#print axioms P06ASphere.coneMap
#print axioms P06ASphere.coneDeriv
#print axioms P06ASphere.σS_finite
#print axioms P06ASphere.σS_openPos
#print axioms P06ASphere.aberrEquiv
#print axioms P06ASphere.coneSet
#print axioms P06ASphere.cone

/-! Non-vacuity instantiations at beta = (0,0,3/5) and beta = 0 -/
example : Measure.map (aberrS witness_admissible) (σS.withDensity (dens 0 0 (3 / 5))) = σS :=
  aberr_pushforward witness_admissible
example : ∫ n, (fun _ : S2 => (1 : ℝ)) (aberrS witness_admissible n) * (dopS 0 0 (3 / 5) n ^ 2)⁻¹ ∂σS =
    ∫ n, (fun _ : S2 => (1 : ℝ)) n ∂σS :=
  aberr_integral witness_admissible continuous_const
example : σS ≠ 0 := pushforward_without_density_ne.2
example : solidAngleNew beta_zero_admissible = σS :=
  (endpoint_optical_sphere_beta_zero (E := 1) (Es := 1) (dS := 1) (dΩ := 1) one_pos).2.1

