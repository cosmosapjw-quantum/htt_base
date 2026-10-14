/-
P06-A additive closeout (PORT-CAS-06, card lean_step 2): the aberration of ONE
observer change, restricted to the unit sphere, transports the measure
`D(n)⁻² · σS` to the surface measure `σS = Measure.toSphere volume` of S².

Builds on the reviewed unit `endpoint_optical_invariants_v1_20261014`
(`P06AOptics`, imported unchanged), whose aberration Jacobian was proved only in
the β̂-polar chart.  Here no chart, no rotation reduction and no `dΩ = dμ dφ`
convention is used.  Route:

* light-cone lift `coneMap x = x + (γ‖x‖ + h β·x) β` (spatial part of the boosted
  null vector, homogeneous of degree one): `coneMap (r n) = (r D(n)) aberr(n)`;
* explicit inverse `coneMap (-β)`; derivative `id + ℓ ⊗ β` with determinant
  `1 + ℓ(β) = D(x̂)` (computed, not postulated);
* Mathlib change of variables on `{0}ᶜ` and Mathlib's polar decomposition
  `volume ↦ toSphere ⊗ r² dr`, applied to the indicator of the unit cone over a
  measurable `A ⊆ S²`; the radial integral produces `D⁻³/3`.

Scalar, flat-space, single-event observer change only.  No polarization or
spin-2 transfer; reciprocity is not used.  Scientific admission: HOLD.
-/
import Mathlib
import PortCas01
import PassiveTensorBridge
import EndpointScalarInvariant
import P06AOptics

open MeasureTheory Metric Set PortCas01 P06AOptics
open scoped RealInnerProductSpace ENNReal
open PORTCAS06EndpointScalarInvariant (zNew dANew endpoint_product_invariant)

namespace P06ASphere

abbrev E3 := EuclideanSpace ℝ (Fin 3)
abbrev S2 := sphere (0 : E3) 1

/-! ## Frozen definitions -/

/-- Mathlib's surface measure on the unit sphere (same expression as the reviewed
    G15-B `σS`, CAS-15 g15b `lean/G15BSphere.lean:40`; not imported). -/
noncomputable def σS : Measure S2 := (volume : Measure E3).toSphere

noncomputable def bvec (b1 b2 b3 : ℝ) : E3 := !₂[b1, b2, b3]

/-- Doppler factor `D(n) = γ(1+β·n)` of the ray with old sourceward direction `n`. -/
noncomputable def dopS (b1 b2 b3 : ℝ) (n : E3) : ℝ := doppler b1 b2 b3 (n 0) (n 1) (n 2)

/-- The P06AOptics closed-form aberration, as a vector of `E3`. -/
noncomputable def aberrV (b1 b2 b3 : ℝ) (n : E3) : E3 :=
  !₂[aberr b1 b2 b3 (n 0) (n 1) (n 2) 0, aberr b1 b2 b3 (n 0) (n 1) (n 2) 1,
    aberr b1 b2 b3 (n 0) (n 1) (n 2) 2]

/-! ## Coordinate helpers -/

lemma inner_eq3 (x y : E3) : ⟪x, y⟫ = x 0 * y 0 + x 1 * y 1 + x 2 * y 2 := by
  simp [PiLp.inner_apply, Fin.sum_univ_three]
  ring

lemma norm_sq3 (x : E3) : ‖x‖ ^ 2 = x 0 ^ 2 + x 1 ^ 2 + x 2 ^ 2 := by
  rw [← real_inner_self_eq_norm_sq, inner_eq3]; ring

lemma sphere_s (n : S2) : s ((n : E3) 0) ((n : E3) 1) ((n : E3) 2) = 1 := by
  have h1 := norm_eq_of_mem_sphere n
  have h2 := norm_sq3 (n : E3)
  rw [h1] at h2
  unfold s; linarith

lemma norm_of_sq_one {v : E3} (hv : ‖v‖ ^ 2 = 1) : ‖v‖ = 1 := by
  rw [← Real.sqrt_sq (norm_nonneg v), hv, Real.sqrt_one]

lemma inner_bvec (b1 b2 b3 : ℝ) (x : E3) :
    ⟪bvec b1 b2 b3, x⟫ = dot3 b1 b2 b3 (x 0) (x 1) (x 2) := by
  rw [inner_eq3]; simp [bvec, dot3]

lemma norm_bvec_sq (b1 b2 b3 : ℝ) : ‖bvec b1 b2 b3‖ ^ 2 = s b1 b2 b3 := by
  rw [norm_sq3]; simp [bvec, s]

lemma bvec_neg (b1 b2 b3 : ℝ) : bvec (-b1) (-b2) (-b3) = -bvec b1 b2 b3 := by
  ext i; fin_cases i <;> simp [bvec]

lemma h_mul {b1 b2 b3 : ℝ} (hb : s b1 b2 b3 < 1) :
    h b1 b2 b3 * (gamma b1 b2 b3 + 1) = gamma b1 b2 b3 ^ 2 := by
  have hg := (core b1 b2 b3 hb).1
  have hne : gamma b1 b2 b3 + 1 ≠ 0 := (by linarith : (0 : ℝ) < gamma b1 b2 b3 + 1).ne'
  unfold h; field_simp

lemma neg_adm {b1 b2 b3 : ℝ} (hb : s b1 b2 b3 < 1) : s (-b1) (-b2) (-b3) < 1 := by
  rw [s_neg]; exact hb

lemma continuous_coord (k : Fin 3) : Continuous (fun x : E3 => x k) :=
  (EuclideanSpace.proj k : E3 →L[ℝ] ℝ).continuous

lemma continuous_dopS (b1 b2 b3 : ℝ) : Continuous (fun x : E3 => dopS b1 b2 b3 x) := by
  show Continuous fun x : E3 => gamma b1 b2 b3 * (1 + (b1 * x 0 + b2 * x 1 + b3 * x 2))
  exact continuous_const.mul (continuous_const.add
    (((continuous_const.mul (continuous_coord 0)).add (continuous_const.mul (continuous_coord 1))).add
      (continuous_const.mul (continuous_coord 2))))

lemma dopS_pos {b1 b2 b3 : ℝ} (hb : s b1 b2 b3 < 1) (n : S2) : 0 < dopS b1 b2 b3 n :=
  doppler_pos hb (sphere_s n)

theorem aberrV_mem_sphere {b1 b2 b3 : ℝ} (hb : s b1 b2 b3 < 1) (n : S2) :
    aberrV b1 b2 b3 n ∈ S2 := by
  rw [mem_sphere_zero_iff_norm]
  apply norm_of_sq_one
  rw [norm_sq3]
  have := aberr_unit hb (sphere_s n)
  unfold s at this
  simpa [aberrV] using this

/-- Aberration restricted to the unit sphere: `S² → S²`. -/
noncomputable def aberrS {b1 b2 b3 : ℝ} (hb : s b1 b2 b3 < 1) (n : S2) : S2 :=
  ⟨aberrV b1 b2 b3 n, aberrV_mem_sphere hb n⟩

/-- Density `D(n)⁻²`. -/
noncomputable def dens (b1 b2 b3 : ℝ) (n : S2) : ℝ≥0∞ :=
  ENNReal.ofReal ((dopS b1 b2 b3 n ^ 2)⁻¹)

/-- New-frame solid-angle measure, pulled back to old directions:
    `solidAngleNew hb A = σS (aberrS hb '' A)` (proved, F6). -/
noncomputable def solidAngleNew {b1 b2 b3 : ℝ} (hb : s b1 b2 b3 < 1) : Measure S2 :=
  Measure.comap (aberrS hb) σS

/-- Light-cone lift of the aberration to `E3` (spatial part of the boosted null
    vector, homogeneous of degree one): used for the 3-D change of variables. -/
noncomputable def coneMap (b1 b2 b3 : ℝ) (x : E3) : E3 :=
  x + (gamma b1 b2 b3 * ‖x‖ + h b1 b2 b3 * ⟪bvec b1 b2 b3, x⟫) • bvec b1 b2 b3

/-- Its derivative at `x ≠ 0` (an explicit formula; F3 proves it is the derivative). -/
noncomputable def coneDeriv (b1 b2 b3 : ℝ) (x : E3) : E3 →L[ℝ] E3 :=
  ContinuousLinearMap.id ℝ E3 +
    (gamma b1 b2 b3 • (‖x‖⁻¹ • innerSL ℝ x) + h b1 b2 b3 • innerSL ℝ (bvec b1 b2 b3)).smulRight
      (bvec b1 b2 b3)

instance σS_finite : IsFiniteMeasure σS := by unfold σS; infer_instance

instance σS_openPos : σS.IsOpenPosMeasure := by unfold σS; infer_instance

/-! ## F1: same physical ray -/

theorem aberrS_same_ray {b1 b2 b3 : ℝ} (hb : s b1 b2 b3 < 1) (n : S2) {E : ℝ} (hE : 0 < E)
    (i : Fin 3) :
    (aberrS hb n : E3) i =
      dirOf (newComp b1 b2 b3 (photon E ((n : E3) 0) ((n : E3) 1) ((n : E3) 2))) i := by
  show (aberrV b1 b2 b3 n) i = _
  rw [newDir_formula hb (sphere_s n) hE i]
  fin_cases i <;> simp [aberrV]

/-! ## The light-cone lift -/

lemma coneMap_zero (b1 b2 b3 : ℝ) : coneMap b1 b2 b3 0 = 0 := by simp [coneMap]

lemma coneMap_smul (b1 b2 b3 : ℝ) {c : ℝ} (hc : 0 ≤ c) (x : E3) :
    coneMap b1 b2 b3 (c • x) = c • coneMap b1 b2 b3 x := by
  ext i
  simp only [coneMap, PiLp.add_apply, PiLp.smul_apply, smul_eq_mul, norm_smul,
    Real.norm_of_nonneg hc, real_inner_smul_right]
  ring

lemma coneMap_sphere {b1 b2 b3 : ℝ} (hb : s b1 b2 b3 < 1) (n : S2) :
    coneMap b1 b2 b3 (n : E3) = dopS b1 b2 b3 n • (aberrS hb n : E3) := by
  have hD := (dopS_pos hb n).ne'
  have hn1 : ‖(n : E3)‖ = 1 := norm_eq_of_mem_sphere n
  unfold dopS at hD
  simp only [coneMap, inner_bvec]
  ext i
  fin_cases i <;>
    simp [aberrS, aberrV, aberr, hn1, bvec, dopS] <;> field_simp <;> ring

theorem coneMap_ray {b1 b2 b3 : ℝ} (hb : s b1 b2 b3 < 1) (n : S2) {r : ℝ} (hr : 0 ≤ r) :
    coneMap b1 b2 b3 (r • (n : E3)) = (r * dopS b1 b2 b3 n) • (aberrS hb n : E3) := by
  rw [coneMap_smul _ _ _ hr, coneMap_sphere hb n, smul_smul]

lemma coneMap_norm {b1 b2 b3 : ℝ} (hb : s b1 b2 b3 < 1) (x : E3) :
    ‖coneMap b1 b2 b3 x‖ = gamma b1 b2 b3 * (‖x‖ + ⟪bvec b1 b2 b3, x⟫) := by
  obtain ⟨hg, hg2, hqs⟩ := core b1 b2 b3 hb
  have hhh := h_mul hb
  have hS := norm_bvec_sq b1 b2 b3
  have hsq : ‖coneMap b1 b2 b3 x‖ ^ 2 =
      (gamma b1 b2 b3 * (‖x‖ + ⟪bvec b1 b2 b3, x⟫)) ^ 2 := by
    rw [coneMap, norm_add_sq_real, real_inner_smul_right, norm_smul, mul_pow, Real.norm_eq_abs,
      sq_abs, hS, real_inner_comm (bvec b1 b2 b3) x]
    linear_combination (-‖x‖ ^ 2) * hg2 +
      (2 * gamma b1 b2 b3 * ‖x‖ * ⟪bvec b1 b2 b3, x⟫ + h b1 b2 b3 * ⟪bvec b1 b2 b3, x⟫ ^ 2) * hqs +
      ⟪bvec b1 b2 b3, x⟫ ^ 2 * hhh
  have hβ : ‖bvec b1 b2 b3‖ ≤ 1 := by nlinarith [norm_nonneg (bvec b1 b2 b3)]
  have ht := abs_le.1 (abs_real_inner_le_norm (bvec b1 b2 b3) x)
  have hnn : 0 ≤ ‖x‖ + ⟪bvec b1 b2 b3, x⟫ := by
    nlinarith [norm_nonneg x, norm_nonneg (bvec b1 b2 b3)]
  rw [← Real.sqrt_sq (norm_nonneg _), hsq, Real.sqrt_sq (mul_nonneg hg.le hnn)]

theorem coneMap_inv {b1 b2 b3 : ℝ} (hb : s b1 b2 b3 < 1) (x : E3) :
    coneMap (-b1) (-b2) (-b3) (coneMap b1 b2 b3 x) = x := by
  obtain ⟨hg, hg2, hqs⟩ := core b1 b2 b3 hb
  have hhh := h_mul hb
  have hS := norm_bvec_sq b1 b2 b3
  have hn := coneMap_norm hb x
  have hin : ⟪bvec b1 b2 b3, coneMap b1 b2 b3 x⟫ = ⟪bvec b1 b2 b3, x⟫ +
      (gamma b1 b2 b3 * ‖x‖ + h b1 b2 b3 * ⟪bvec b1 b2 b3, x⟫) * s b1 b2 b3 := by
    rw [coneMap, inner_add_right, real_inner_smul_right, real_inner_self_eq_norm_sq, hS]
  have key : (gamma b1 b2 b3 * ‖x‖ + h b1 b2 b3 * ⟪bvec b1 b2 b3, x⟫) -
      (gamma b1 b2 b3 * (gamma b1 b2 b3 * (‖x‖ + ⟪bvec b1 b2 b3, x⟫)) -
        h b1 b2 b3 * (⟪bvec b1 b2 b3, x⟫ +
          (gamma b1 b2 b3 * ‖x‖ + h b1 b2 b3 * ⟪bvec b1 b2 b3, x⟫) * s b1 b2 b3)) = 0 := by
    linear_combination (gamma b1 b2 b3 * ‖x‖ + h b1 b2 b3 * ⟪bvec b1 b2 b3, x⟫) * hqs +
      ⟪bvec b1 b2 b3, x⟫ * hhh
  have hdef : ∀ y : E3, coneMap (-b1) (-b2) (-b3) y =
      y + (gamma (-b1) (-b2) (-b3) * ‖y‖ + h (-b1) (-b2) (-b3) * ⟪bvec (-b1) (-b2) (-b3), y⟫) •
        bvec (-b1) (-b2) (-b3) := fun y => rfl
  rw [hdef, gamma_neg, h_neg, bvec_neg, inner_neg_left, hn, hin]
  ext i
  simp only [coneMap, PiLp.add_apply, PiLp.smul_apply, PiLp.neg_apply, smul_eq_mul]
  linear_combination (bvec b1 b2 b3 i) * key

lemma coneMap_inv' {b1 b2 b3 : ℝ} (hb : s b1 b2 b3 < 1) (y : E3) :
    coneMap b1 b2 b3 (coneMap (-b1) (-b2) (-b3) y) = y := by
  have := coneMap_inv (neg_adm hb) y
  simpa only [neg_neg] using this

lemma coneMap_image {b1 b2 b3 : ℝ} (hb : s b1 b2 b3 < 1) :
    coneMap b1 b2 b3 '' ({0}ᶜ : Set E3) = {0}ᶜ := by
  ext y
  simp only [mem_image, mem_compl_iff, mem_singleton_iff]
  constructor
  · rintro ⟨x, hx, rfl⟩ h0
    apply hx
    rw [← coneMap_inv hb x, h0, coneMap_zero]
  · intro hy
    refine ⟨coneMap (-b1) (-b2) (-b3) y, fun h0 => hy ?_, coneMap_inv' hb y⟩
    rw [← coneMap_inv' hb y, h0, coneMap_zero]

lemma coneMap_injOn {b1 b2 b3 : ℝ} (hb : s b1 b2 b3 < 1) :
    InjOn (coneMap b1 b2 b3) ({0}ᶜ : Set E3) := fun x _ y _ hxy => by
  rw [← coneMap_inv hb x, hxy, coneMap_inv hb y]

/-! ## F3: derivative and Jacobian of the lift -/

lemma hasFDerivAt_norm3 {x : E3} (hx : x ≠ 0) :
    HasFDerivAt (fun y : E3 => ‖y‖) (‖x‖⁻¹ • innerSL ℝ x) x := by
  have hN : ‖x‖ ≠ 0 := norm_ne_zero_iff.2 hx
  have h1 := (hasStrictFDerivAt_norm_sq x).hasFDerivAt.sqrt (pow_ne_zero 2 hN)
  simp only [Real.sqrt_sq (norm_nonneg _)] at h1
  refine h1.congr_fderiv ?_
  ext v
  simp only [ContinuousLinearMap.smul_apply, innerSL_apply_apply, smul_eq_mul, nsmul_eq_mul]
  field_simp
  ring

lemma coneMap_hasFDerivAt (b1 b2 b3 : ℝ) {x : E3} (hx : x ≠ 0) :
    HasFDerivAt (coneMap b1 b2 b3) (coneDeriv b1 b2 b3 x) x := by
  have hN := hasFDerivAt_norm3 hx
  have hI : HasFDerivAt (fun y : E3 => ⟪bvec b1 b2 b3, y⟫) (innerSL ℝ (bvec b1 b2 b3)) x :=
    (innerSL ℝ (bvec b1 b2 b3)).hasFDerivAt
  exact (hasFDerivAt_id x).add (((hN.const_mul (gamma b1 b2 b3)).add
    (hI.const_mul (h b1 b2 b3))).smul_const (bvec b1 b2 b3))

lemma det_rank_one (w v : E3) :
    (ContinuousLinearMap.id ℝ E3 + (innerSL ℝ w).smulRight v).det = 1 + ⟪w, v⟫ := by
  rw [ContinuousLinearMap.det, ← LinearMap.det_toMatrix (EuclideanSpace.basisFun (Fin 3) ℝ).toBasis,
    Matrix.det_fin_three]
  simp [LinearMap.toMatrix_apply, inner_eq3]
  ring

lemma coneDeriv_eq (b1 b2 b3 : ℝ) (x : E3) :
    coneDeriv b1 b2 b3 x = ContinuousLinearMap.id ℝ E3 +
      (innerSL ℝ ((gamma b1 b2 b3 * ‖x‖⁻¹) • x + h b1 b2 b3 • bvec b1 b2 b3)).smulRight
        (bvec b1 b2 b3) := by
  unfold coneDeriv
  congr 2
  ext v
  simp
  ring

theorem coneMap_jacobian {b1 b2 b3 : ℝ} (hb : s b1 b2 b3 < 1) {x : E3} (hx : x ≠ 0) :
    HasFDerivAt (coneMap b1 b2 b3) (coneDeriv b1 b2 b3 x) x ∧
      (coneDeriv b1 b2 b3 x).det = dopS b1 b2 b3 (‖x‖⁻¹ • x) := by
  refine ⟨coneMap_hasFDerivAt b1 b2 b3 hx, ?_⟩
  obtain ⟨-, -, hqs⟩ := core b1 b2 b3 hb
  rw [coneDeriv_eq, det_rank_one, inner_add_left, real_inner_smul_left, real_inner_smul_left,
    real_inner_self_eq_norm_sq, norm_bvec_sq]
  have hD : dopS b1 b2 b3 (‖x‖⁻¹ • x) = gamma b1 b2 b3 * (1 + ‖x‖⁻¹ * ⟪bvec b1 b2 b3, x⟫) := by
    simp only [dopS, doppler, inner_bvec, dot3, PiLp.smul_apply, smul_eq_mul]
    ring
  rw [hD, real_inner_comm (bvec b1 b2 b3) x]
  linear_combination hqs

/-! ## F2: the sphere map is a continuous bijection -/

lemma aberrS_coe {b1 b2 b3 : ℝ} (hb : s b1 b2 b3 < 1) (n : S2) :
    (aberrS hb n : E3) = aberrV b1 b2 b3 n := rfl

lemma aberrS_inv_gen {b1 b2 b3 c1 c2 c3 : ℝ} (hb : s b1 b2 b3 < 1) (hc : s c1 c2 c3 < 1)
    (h1 : c1 = -b1) (h2 : c2 = -b2) (h3 : c3 = -b3) (n : S2) :
    aberrS hc (aberrS hb n) = n := by
  subst h1 h2 h3
  apply Subtype.ext
  have e1 := coneMap_inv hb (n : E3)
  rw [coneMap_sphere hb n, coneMap_smul _ _ _ (dopS_pos hb n).le, coneMap_sphere hc (aberrS hb n),
    smul_smul] at e1
  have hk : dopS b1 b2 b3 n * dopS (-b1) (-b2) (-b3) (aberrS hb n) = 1 := by
    have hn := congrArg norm e1
    rw [norm_smul, norm_eq_of_mem_sphere (aberrS hc (aberrS hb n)), norm_eq_of_mem_sphere n,
      mul_one, Real.norm_eq_abs, abs_of_pos (mul_pos (dopS_pos hb n) (dopS_pos hc _))] at hn
    exact hn
  rw [hk, one_smul] at e1
  exact e1

lemma aberrS_left {b1 b2 b3 : ℝ} (hb : s b1 b2 b3 < 1) (n : S2) :
    aberrS (neg_adm hb) (aberrS hb n) = n :=
  aberrS_inv_gen hb (neg_adm hb) rfl rfl rfl n

lemma aberrS_right {b1 b2 b3 : ℝ} (hb : s b1 b2 b3 < 1) (n : S2) :
    aberrS hb (aberrS (neg_adm hb) n) = n :=
  aberrS_inv_gen (neg_adm hb) hb (neg_neg b1).symm (neg_neg b2).symm (neg_neg b3).symm n

lemma continuous_coneMap (b1 b2 b3 : ℝ) : Continuous (coneMap b1 b2 b3) := by
  unfold coneMap
  exact continuous_id.add (((continuous_const.mul continuous_norm).add
    (continuous_const.mul (continuous_const.inner continuous_id))).smul continuous_const)

lemma aberrS_continuous {b1 b2 b3 : ℝ} (hb : s b1 b2 b3 < 1) : Continuous (aberrS hb) := by
  have hfun : (fun n : S2 => (aberrS hb n : E3)) =
      fun n : S2 => (dopS b1 b2 b3 n)⁻¹ • coneMap b1 b2 b3 n := by
    funext n
    rw [coneMap_sphere hb n, smul_smul, inv_mul_cancel₀ (dopS_pos hb n).ne', one_smul]
  refine continuous_induced_rng.2 ?_
  show Continuous (fun n : S2 => (aberrS hb n : E3))
  rw [hfun]
  exact (((continuous_dopS b1 b2 b3).comp continuous_subtype_val).inv₀
    (fun n => (dopS_pos hb n).ne')).smul ((continuous_coneMap b1 b2 b3).comp continuous_subtype_val)

/-- The aberration as a measurable equivalence of `S²` (inverse: aberration by `-β`). -/
noncomputable def aberrEquiv {b1 b2 b3 : ℝ} (hb : s b1 b2 b3 < 1) : S2 ≃ᵐ S2 where
  toFun := aberrS hb
  invFun := aberrS (neg_adm hb)
  left_inv := aberrS_left hb
  right_inv := aberrS_right hb
  measurable_toFun := (aberrS_continuous hb).measurable
  measurable_invFun := (aberrS_continuous (neg_adm hb)).measurable

theorem aberrS_bijective {b1 b2 b3 : ℝ} (hb : s b1 b2 b3 < 1) :
    Function.Bijective (aberrS hb) ∧ Continuous (aberrS hb) :=
  ⟨Function.bijective_iff_has_inverse.2 ⟨aberrS (neg_adm hb), aberrS_left hb, aberrS_right hb⟩,
    aberrS_continuous hb⟩

/-! ## Polar decomposition and the unit cone -/

lemma lintegral_polar (f : E3 → ℝ≥0∞) :
    ∫⁻ x in ({0}ᶜ : Set E3), f x =
      ∫⁻ p : S2 × Ioi (0 : ℝ), f ((p.2 : ℝ) • (p.1 : E3)) ∂(σS.prod (Measure.volumeIoiPow 2)) := by
  rw [← lintegral_subtype_comap (measurableSet_singleton (0 : E3)).compl]
  have hmp : MeasurePreserving (homeomorphUnitSphereProd E3) (Measure.comap Subtype.val volume)
      (σS.prod (Measure.volumeIoiPow 2)) := by
    have := (volume : Measure E3).measurePreserving_homeomorphUnitSphereProd
    rwa [finrank_euclideanSpace_fin] at this
  calc ∫⁻ x : ({0}ᶜ : Set E3), f x ∂(Measure.comap Subtype.val volume)
      = ∫⁻ x : ({0}ᶜ : Set E3), (fun p : S2 × Ioi (0 : ℝ) => f ((p.2 : ℝ) • (p.1 : E3)))
          (homeomorphUnitSphereProd E3 x) ∂(Measure.comap Subtype.val volume) := by
        congr 1; funext x
        simp only
        rw [← homeomorphUnitSphereProd_symm_apply_coe, Homeomorph.symm_apply_apply]
    _ = _ := hmp.lintegral_comp_emb (homeomorphUnitSphereProd E3).measurableEmbedding
          (fun p : S2 × Ioi (0 : ℝ) => f ((p.2 : ℝ) • (p.1 : E3)))

lemma radial_Iio {c : ℝ} (hc : 0 < c) :
    Measure.volumeIoiPow 2 {r : Ioi (0 : ℝ) | (r : ℝ) * c < 1} = ENNReal.ofReal (c⁻¹ ^ 3 / 3) := by
  have hset : {r : Ioi (0 : ℝ) | (r : ℝ) * c < 1} = Iio ⟨c⁻¹, inv_pos.2 hc⟩ := by
    ext r
    show (r : ℝ) * c < 1 ↔ (r : ℝ) < c⁻¹
    rw [← one_div, lt_div_iff₀ hc]
  rw [hset, Measure.volumeIoiPow_apply_Iio]
  norm_num

lemma radial_one : Measure.volumeIoiPow 2 (Iio (⟨1, mem_Ioi.2 one_pos⟩ : Ioi (0 : ℝ))) =
    ENNReal.ofReal (1 / 3) := by
  rw [Measure.volumeIoiPow_apply_Iio]
  norm_num

/-- Unit cone over `A ⊆ S²`. -/
def coneSet (A : Set S2) : Set E3 := {y | ‖y‖ < 1 ∧ ‖y‖⁻¹ • y ∈ ((↑) '' A : Set E3)}

noncomputable def cone (A : Set S2) : E3 → ℝ≥0∞ := (coneSet A).indicator 1

lemma mem_coneSet_smul (A : Set S2) {c : ℝ} (hc : 0 < c) (m : S2) :
    c • (m : E3) ∈ coneSet A ↔ m ∈ A ∧ c < 1 := by
  have hnorm : ‖c • (m : E3)‖ = c := by
    rw [norm_smul, norm_eq_of_mem_sphere m, mul_one, Real.norm_of_nonneg hc.le]
  have hdir : ‖c • (m : E3)‖⁻¹ • (c • (m : E3)) = m := by
    rw [hnorm, smul_smul, inv_mul_cancel₀ hc.ne', one_smul]
  simp only [coneSet, mem_setOf_eq, hdir, Subtype.val_injective.mem_set_image]
  rw [hnorm]
  exact and_comm

lemma ind_congr {α β : Type*} {S : Set α} {T : Set β} {a : α} {b : β} (hab : a ∈ S ↔ b ∈ T) :
    S.indicator (1 : α → ℝ≥0∞) a = T.indicator 1 b := by
  by_cases ha : a ∈ S
  · rw [indicator_of_mem ha, indicator_of_mem (hab.1 ha)]; rfl
  · rw [indicator_of_notMem ha, indicator_of_notMem (fun hb => ha (hab.2 hb))]

lemma measurable_dens (b1 b2 b3 : ℝ) : Measurable (dens b1 b2 b3) :=
  ENNReal.measurable_ofReal.comp
    ((((continuous_dopS b1 b2 b3).comp continuous_subtype_val).measurable.pow_const 2).inv)

/-- Core identity: `σS A = ∫_{aberr⁻¹ A} D⁻² dσS` for every measurable `A`. -/
theorem key_identity {b1 b2 b3 : ℝ} (hb : s b1 b2 b3 < 1) (A : Set S2) (hA : MeasurableSet A) :
    σS A = ∫⁻ n in aberrS hb ⁻¹' A, dens b1 b2 b3 n ∂σS := by
  set c : ℝ≥0∞ := ENNReal.ofReal (1 / 3) with hc
  set ν := Measure.volumeIoiPow 2
  set P : Set (S2 × Ioi (0 : ℝ)) :=
    {p | aberrS hb p.1 ∈ A ∧ (p.2 : ℝ) * dopS b1 b2 b3 p.1 < 1} with hP
  have hDc : Continuous (fun n : S2 => dopS b1 b2 b3 n) :=
    (continuous_dopS b1 b2 b3).comp continuous_subtype_val
  have hPm : MeasurableSet P :=
    (((aberrS_continuous hb).measurable.comp measurable_fst) hA).inter
      (measurableSet_lt ((measurable_subtype_coe.comp measurable_snd).mul
        (hDc.measurable.comp measurable_fst)) measurable_const)
  have hpre : MeasurableSet (aberrS hb ⁻¹' A) := (aberrS_continuous hb).measurable hA
  -- left side: the unit cone over `A`
  have hlhs : ∫⁻ x in ({0}ᶜ : Set E3), cone A x = σS A * c := by
    refine (lintegral_polar (cone A)).trans ?_
    have hpt : ∀ p : S2 × Ioi (0 : ℝ), cone A ((p.2 : ℝ) • (p.1 : E3)) =
        (A ×ˢ Iio (⟨1, mem_Ioi.2 one_pos⟩ : Ioi (0 : ℝ))).indicator 1 p := fun p =>
      ind_congr (mem_coneSet_smul A p.2.2 p.1)
    rw [lintegral_congr hpt, lintegral_indicator_one (hA.prod measurableSet_Iio),
      Measure.prod_prod, radial_one]
  -- pointwise form of the change-of-variables integrand in polar coordinates
  have hpt : ∀ p : S2 × Ioi (0 : ℝ),
      ENNReal.ofReal |(coneDeriv b1 b2 b3 ((p.2 : ℝ) • (p.1 : E3))).det| *
          cone A (coneMap b1 b2 b3 ((p.2 : ℝ) • (p.1 : E3))) =
        ENNReal.ofReal (dopS b1 b2 b3 p.1) * P.indicator (1 : S2 × Ioi (0 : ℝ) → ℝ≥0∞) p := by
    rintro ⟨n, r⟩
    have hr : 0 < (r : ℝ) := r.2
    have hx : (r : ℝ) • (n : E3) ≠ 0 := smul_ne_zero hr.ne' (ne_zero_of_mem_unit_sphere n)
    have hdir : ‖(r : ℝ) • (n : E3)‖⁻¹ • ((r : ℝ) • (n : E3)) = n := by
      rw [norm_smul, norm_eq_of_mem_sphere n, mul_one, Real.norm_of_nonneg hr.le, smul_smul,
        inv_mul_cancel₀ hr.ne', one_smul]
    rw [(coneMap_jacobian hb hx).2, hdir, abs_of_pos (dopS_pos hb n), coneMap_ray hb n hr.le]
    congr 1
    exact ind_congr ((mem_coneSet_smul A (mul_pos hr (dopS_pos hb n)) (aberrS hb n)))
  have hG : Measurable (fun p : S2 × Ioi (0 : ℝ) =>
      ENNReal.ofReal (dopS b1 b2 b3 p.1) * P.indicator (1 : S2 × Ioi (0 : ℝ) → ℝ≥0∞) p) :=
    (ENNReal.measurable_ofReal.comp (hDc.measurable.comp measurable_fst)).mul
      (measurable_one.indicator hPm)
  -- inner radial integral
  have hinner : ∀ n : S2, ∫⁻ r, ENNReal.ofReal (dopS b1 b2 b3 n) * P.indicator (1 : S2 × Ioi (0 : ℝ) → ℝ≥0∞) (n, r) ∂ν =
      (aberrS hb ⁻¹' A).indicator (fun n => dens b1 b2 b3 n * c) n := by
    intro n
    have hD := dopS_pos hb n
    have hIm : MeasurableSet {r : Ioi (0 : ℝ) | (r : ℝ) * dopS b1 b2 b3 n < 1} :=
      measurableSet_lt (measurable_subtype_coe.mul_const _) measurable_const
    by_cases hn : n ∈ aberrS hb ⁻¹' A
    · rw [indicator_of_mem hn]
      have hset : ∀ r : Ioi (0 : ℝ), P.indicator (1 : S2 × Ioi (0 : ℝ) → ℝ≥0∞) (n, r) =
          {r : Ioi (0 : ℝ) | (r : ℝ) * dopS b1 b2 b3 n < 1}.indicator 1 r := fun r =>
        ind_congr ⟨fun h => h.2, fun h => ⟨hn, h⟩⟩
      calc ∫⁻ r, ENNReal.ofReal (dopS b1 b2 b3 n) * P.indicator (1 : S2 × Ioi (0 : ℝ) → ℝ≥0∞) (n, r) ∂ν
          = ∫⁻ r, ENNReal.ofReal (dopS b1 b2 b3 n) *
              {r : Ioi (0 : ℝ) | (r : ℝ) * dopS b1 b2 b3 n < 1}.indicator 1 r ∂ν :=
            lintegral_congr (fun r => by rw [hset r])
        _ = ENNReal.ofReal (dopS b1 b2 b3 n) *
              ν {r : Ioi (0 : ℝ) | (r : ℝ) * dopS b1 b2 b3 n < 1} := by
            rw [lintegral_const_mul _ (measurable_one.indicator hIm), lintegral_indicator_one hIm]
        _ = dens b1 b2 b3 n * c := by
            rw [radial_Iio hD, dens, hc, ← ENNReal.ofReal_mul hD.le,
              ← ENNReal.ofReal_mul (by positivity)]
            congr 1
            field_simp
    · rw [indicator_of_notMem hn]
      have h0 : ∀ r : Ioi (0 : ℝ), P.indicator (1 : S2 × Ioi (0 : ℝ) → ℝ≥0∞) (n, r) = 0 := fun r =>
        indicator_of_notMem (fun h => hn h.1) _
      simp [h0]
  have hcne : c ≠ 0 := by rw [hc]; norm_num
  have hctop : c ≠ ⊤ := ENNReal.ofReal_ne_top
  have hmain : σS A * c = (∫⁻ n in aberrS hb ⁻¹' A, dens b1 b2 b3 n ∂σS) * c := by
    calc σS A * c = ∫⁻ x in ({0}ᶜ : Set E3), cone A x := hlhs.symm
      _ = ∫⁻ x in coneMap b1 b2 b3 '' ({0}ᶜ : Set E3), cone A x := by rw [coneMap_image hb]
      _ = ∫⁻ x in ({0}ᶜ : Set E3),
            ENNReal.ofReal |(coneDeriv b1 b2 b3 x).det| * cone A (coneMap b1 b2 b3 x) :=
          lintegral_image_eq_lintegral_abs_det_fderiv_mul volume
            (measurableSet_singleton (0 : E3)).compl
            (fun x hx => (coneMap_hasFDerivAt b1 b2 b3 hx).hasFDerivWithinAt)
            (coneMap_injOn hb) (cone A)
      _ = ∫⁻ p : S2 × Ioi (0 : ℝ),
            ENNReal.ofReal |(coneDeriv b1 b2 b3 ((p.2 : ℝ) • (p.1 : E3))).det| *
              cone A (coneMap b1 b2 b3 ((p.2 : ℝ) • (p.1 : E3))) ∂(σS.prod ν) :=
          lintegral_polar (fun x =>
            ENNReal.ofReal |(coneDeriv b1 b2 b3 x).det| * cone A (coneMap b1 b2 b3 x))
      _ = ∫⁻ p : S2 × Ioi (0 : ℝ), ENNReal.ofReal (dopS b1 b2 b3 p.1) * P.indicator (1 : S2 × Ioi (0 : ℝ) → ℝ≥0∞) p
            ∂(σS.prod ν) := lintegral_congr hpt
      _ = ∫⁻ n, ∫⁻ r, ENNReal.ofReal (dopS b1 b2 b3 n) * P.indicator (1 : S2 × Ioi (0 : ℝ) → ℝ≥0∞) (n, r) ∂ν ∂σS :=
          lintegral_prod _ hG.aemeasurable
      _ = ∫⁻ n, (aberrS hb ⁻¹' A).indicator (fun n => dens b1 b2 b3 n * c) n ∂σS :=
          lintegral_congr hinner
      _ = (∫⁻ n in aberrS hb ⁻¹' A, dens b1 b2 b3 n ∂σS) * c := by
          rw [lintegral_indicator hpre, lintegral_mul_const _ (measurable_dens b1 b2 b3)]
  exact (ENNReal.mul_left_inj hcne hctop).mp hmain

/-! ## F4: pushforward of `D⁻² σS` under aberration is `σS` -/

theorem aberr_pushforward {b1 b2 b3 : ℝ} (hb : s b1 b2 b3 < 1) :
    Measure.map (aberrS hb) (σS.withDensity (dens b1 b2 b3)) = σS := by
  ext A hA
  rw [Measure.map_apply (aberrS_continuous hb).measurable hA,
    withDensity_apply _ ((aberrS_continuous hb).measurable hA)]
  exact (key_identity hb A hA).symm

/-! ## F5: integral form for continuous `g` -/

theorem aberr_integral {b1 b2 b3 : ℝ} (hb : s b1 b2 b3 < 1) {g : S2 → ℝ} (hg : Continuous g) :
    ∫ n, g (aberrS hb n) * (dopS b1 b2 b3 n ^ 2)⁻¹ ∂σS = ∫ n, g n ∂σS := by
  conv_rhs => rw [← aberr_pushforward hb]
  rw [integral_map (aberrS_continuous hb).aemeasurable hg.aestronglyMeasurable,
    integral_withDensity_eq_integral_toReal_smul (measurable_dens b1 b2 b3)
      (ae_of_all _ (fun _ => ENNReal.ofReal_lt_top))]
  congr 1
  funext n
  rw [dens, ENNReal.toReal_ofReal (by positivity), smul_eq_mul, mul_comm]

/-! ## F6: new-frame solid angle of the same bundle of rays -/

theorem solidAngleNew_eq {b1 b2 b3 : ℝ} (hb : s b1 b2 b3 < 1) :
    solidAngleNew hb = σS.withDensity (dens b1 b2 b3) ∧
      ∀ A : Set S2, MeasurableSet A →
        solidAngleNew hb A = σS (aberrS hb '' A) ∧
          σS (aberrS hb '' A) = ∫⁻ n in A, dens b1 b2 b3 n ∂σS := by
  have hemb : MeasurableEmbedding (aberrS hb) := (aberrEquiv hb).measurableEmbedding
  have himg : ∀ A : Set S2, aberrS hb '' A = aberrS (neg_adm hb) ⁻¹' A := fun A =>
    congrFun (Set.image_eq_preimage_of_inverse (aberrS_left hb) (aberrS_right hb)) A
  have hW : Measure.map (aberrS (neg_adm hb)) σS = σS.withDensity (dens b1 b2 b3) := by
    conv_lhs => rw [← aberr_pushforward hb]
    rw [Measure.map_map (aberrS_continuous (neg_adm hb)).measurable (aberrS_continuous hb).measurable]
    have hid : aberrS (neg_adm hb) ∘ aberrS hb = id := funext (aberrS_left hb)
    rw [hid, Measure.map_id]
  have hmain : solidAngleNew hb = σS.withDensity (dens b1 b2 b3) := by
    ext A hA
    rw [solidAngleNew, hemb.comap_apply, himg,
      ← Measure.map_apply (aberrS_continuous (neg_adm hb)).measurable hA, hW]
  refine ⟨hmain, fun A hA => ⟨by rw [solidAngleNew, hemb.comap_apply], ?_⟩⟩
  rw [← hemb.comap_apply]
  show solidAngleNew hb A = _
  rw [hmain, withDensity_apply _ hA]

/-! ## F7: area distance with the same source area -/

lemma areaDist_scale {D : ℝ} (hD : 0 < D) (dS dΩ : ℝ) :
    areaDist dS ((D ^ 2)⁻¹ * dΩ) = dANew (areaDist dS dΩ) D := by
  unfold areaDist dANew
  have hrw : dS / ((D ^ 2)⁻¹ * dΩ) = D ^ 2 * (dS / dΩ) := by
    rw [div_mul_eq_div_div, div_inv_eq_mul]; ring
  rw [hrw, Real.sqrt_mul (by positivity), Real.sqrt_sq hD.le]

theorem areaDist_sphere {b1 b2 b3 : ℝ} (hb : s b1 b2 b3 < 1) (dS dΩ : ℝ) :
    ∀ᵐ n ∂σS, areaDist dS (((solidAngleNew hb).rnDeriv σS n).toReal * dΩ) =
      dANew (areaDist dS dΩ) (dopS b1 b2 b3 n) := by
  have hrn : (solidAngleNew hb).rnDeriv σS =ᵐ[σS] dens b1 b2 b3 := by
    rw [(solidAngleNew_eq hb).1]
    exact Measure.rnDeriv_withDensity σS (measurable_dens b1 b2 b3)
  filter_upwards [hrn] with n hn
  rw [hn, dens, ENNReal.toReal_ofReal (by positivity), areaDist_scale (dopS_pos hb n)]

/-! ## F8: same-ray composite on the sphere measure -/

theorem endpoint_optical_sphere {b1 b2 b3 : ℝ} (hb : s b1 b2 b3 < 1) {E Es dS dΩ : ℝ}
    (hE : 0 < E) :
    ∀ᵐ (n : S2) ∂σS,
      redshiftOf Es (energy (fourVelocity b1 b2 b3)
          (photon E ((n : E3) 0) ((n : E3) 1) ((n : E3) 2))) =
        zNew (redshiftOf Es (energy e0 (photon E ((n : E3) 0) ((n : E3) 1) ((n : E3) 2))))
          (dopS b1 b2 b3 n) ∧
      areaDist dS (((solidAngleNew hb).rnDeriv σS n).toReal * dΩ) =
        dANew (areaDist dS dΩ) (dopS b1 b2 b3 n) ∧
      (1 + redshiftOf Es (energy (fourVelocity b1 b2 b3)
          (photon E ((n : E3) 0) ((n : E3) 1) ((n : E3) 2)))) *
          areaDist dS (((solidAngleNew hb).rnDeriv σS n).toReal * dΩ) =
        (1 + redshiftOf Es (energy e0 (photon E ((n : E3) 0) ((n : E3) 1) ((n : E3) 2)))) *
          areaDist dS dΩ := by
  filter_upwards [areaDist_sphere hb dS dΩ] with n hn
  have hD := dopS_pos hb n
  have hz : redshiftOf Es (energy (fourVelocity b1 b2 b3)
        (photon E ((n : E3) 0) ((n : E3) 1) ((n : E3) 2))) =
      zNew (redshiftOf Es (energy e0 (photon E ((n : E3) 0) ((n : E3) 1) ((n : E3) 2))))
        (dopS b1 b2 b3 n) := by
    rw [energy_new, energy_old]; exact redshift_endpoint hE hD
  refine ⟨hz, hn, ?_⟩
  rw [hz, hn]
  exact endpoint_product_invariant _ _ _ hD

/-! ## F9: β = 0 composite (corollary) -/

theorem beta_zero_admissible : s 0 0 0 < 1 := by norm_num [s]

theorem endpoint_optical_sphere_beta_zero {E Es dS dΩ : ℝ} (hE : 0 < E) :
    (∀ n : S2, aberrS beta_zero_admissible n = n) ∧
      solidAngleNew beta_zero_admissible = σS ∧
      ∀ᵐ (n : S2) ∂σS,
        redshiftOf Es (energy (fourVelocity 0 0 0)
            (photon E ((n : E3) 0) ((n : E3) 1) ((n : E3) 2))) =
          redshiftOf Es (energy e0 (photon E ((n : E3) 0) ((n : E3) 1) ((n : E3) 2))) ∧
        areaDist dS (((solidAngleNew beta_zero_admissible).rnDeriv σS n).toReal * dΩ) =
          areaDist dS dΩ ∧
        (1 + redshiftOf Es (energy (fourVelocity 0 0 0)
            (photon E ((n : E3) 0) ((n : E3) 1) ((n : E3) 2)))) *
            areaDist dS (((solidAngleNew beta_zero_admissible).rnDeriv σS n).toReal * dΩ) =
          (1 + redshiftOf Es (energy e0 (photon E ((n : E3) 0) ((n : E3) 1) ((n : E3) 2)))) *
            areaDist dS dΩ := by
  have hab : ∀ a b c : ℝ, ∀ i : Fin 3, aberr 0 0 0 a b c i = ![a, b, c] i :=
    fun a b c => (boundary_beta_zero a b c 0 0).2.2.1
  have hid : ∀ n : S2, aberrS beta_zero_admissible n = n := by
    intro n
    apply Subtype.ext
    ext i
    fin_cases i <;> simp [aberrS, aberrV, hab]
  have hfun : aberrS beta_zero_admissible = fun n => n := funext hid
  refine ⟨hid, by rw [solidAngleNew, hfun, Measure.comap_id], ?_⟩
  filter_upwards [endpoint_optical_sphere beta_zero_admissible (Es := Es) (dS := dS) (dΩ := dΩ) hE]
    with n hn
  obtain ⟨h1, h2, h3⟩ := hn
  have hD1 : dopS 0 0 0 n = 1 := (boundary_beta_zero ((n : E3) 0) ((n : E3) 1) ((n : E3) 2) 0 0).1
  rw [hD1] at h1 h2
  refine ⟨by rw [h1]; simp [zNew], by rw [h2]; simp [dANew], h3⟩

/-! ## F10: negative control and non-vacuity -/

theorem witness_admissible : s 0 0 (3 / 5) < 1 := by norm_num [s]

theorem pushforward_without_density_ne :
    Measure.map (aberrS witness_admissible) σS ≠ σS ∧ σS ≠ 0 := by
  have hne : σS ≠ 0 := by unfold σS; exact Measure.toSphere_ne_zero _
  refine ⟨fun heq => ?_, hne⟩
  set hb := witness_admissible
  have h1 : Measure.map (aberrS hb) (σS.withDensity (dens 0 0 (3 / 5))) =
      Measure.map (aberrS hb) σS := by rw [aberr_pushforward, heq]
  have h2 : σS.withDensity (dens 0 0 (3 / 5)) = σS := by
    have := congrArg (Measure.map (aberrS (neg_adm hb))) h1
    have hid : aberrS (neg_adm hb) ∘ aberrS hb = id := funext (aberrS_left hb)
    rwa [Measure.map_map (aberrS_continuous (neg_adm hb)).measurable
        (aberrS_continuous hb).measurable,
      Measure.map_map (aberrS_continuous (neg_adm hb)).measurable
        (aberrS_continuous hb).measurable, hid, Measure.map_id, Measure.map_id] at this
  set U : Set S2 := {n | 3 / 2 < dopS 0 0 (3 / 5) n} with hU
  have hUo : IsOpen U :=
    isOpen_lt continuous_const ((continuous_dopS 0 0 (3 / 5)).comp continuous_subtype_val)
  have hpole : ‖(!₂[0, 0, 1] : E3)‖ = 1 := by
    apply norm_of_sq_one; rw [norm_sq3]; simp
  set p : S2 := ⟨!₂[0, 0, 1], by rw [mem_sphere_zero_iff_norm]; exact hpole⟩
  have hpU : p ∈ U := by
    show 3 / 2 < doppler 0 0 (3 / 5) ((!₂[0, 0, 1] : E3) 0) ((!₂[0, 0, 1] : E3) 1)
      ((!₂[0, 0, 1] : E3) 2)
    have hw := nonvacuity_witness.2.2.2
    simp only [Matrix.cons_val_zero, Matrix.cons_val_one, Matrix.cons_val_two,
      Matrix.tail_cons, Matrix.head_cons]
    rw [hw]; norm_num
  have hpos : 0 < σS U := hUo.measure_pos σS ⟨p, hpU⟩
  have hfin : σS U ≠ ⊤ := measure_ne_top σS U
  have hle : σS U ≤ ENNReal.ofReal (4 / 9) * σS U := by
    calc σS U = σS.withDensity (dens 0 0 (3 / 5)) U := by rw [h2]
      _ = ∫⁻ n in U, dens 0 0 (3 / 5) n ∂σS := withDensity_apply _ hUo.measurableSet
      _ ≤ ∫⁻ _ in U, ENNReal.ofReal (4 / 9) ∂σS := by
          refine setLIntegral_mono measurable_const (fun n hn => ?_)
          apply ENNReal.ofReal_le_ofReal
          have hn' : 3 / 2 < dopS 0 0 (3 / 5) n := hn
          rw [inv_le_comm₀ (by positivity) (by norm_num)]
          nlinarith
      _ = ENNReal.ofReal (4 / 9) * σS U := setLIntegral_const U _
  have hr := ENNReal.toReal_mono (ENNReal.mul_ne_top ENNReal.ofReal_ne_top hfin) hle
  rw [ENNReal.toReal_mul, ENNReal.toReal_ofReal (by norm_num)] at hr
  have hp := ENNReal.toReal_pos hpos.ne' hfin
  nlinarith

end P06ASphere
