import FullBridge
import ConventionalRodrigues

open MeasureTheory Real
open scoped Interval

namespace G12CFiniteChart

abbrev Vec3 := Fin 3 → Real
abbrev S2 := {u : Vec3 // ∑ i, u i ^ 2 = 1}
abbrev MuChart := {mu : Real // mu ∈ Set.Icc (-1) 1}
abbrev PhiChart := {phi : Real // phi ∈ Set.Icc 0 (2 * Real.pi)}
abbrev ChartDomain := MuChart × PhiChart

private theorem chartVec_unit (mu : MuChart) (phi : PhiChart) :
    ∑ i : Fin 3,
      (![CAS16C03.sphereX mu.1 phi.1,
         CAS16C03.sphereY mu.1 phi.1,
         CAS16C03.sphereZ mu.1] : Vec3) i ^ 2 = 1 := by
  have hmu : 0 ≤ 1 - mu.1 ^ 2 := by
    rcases mu.2 with ⟨hl, hr⟩
    nlinarith
  simp [Fin.sum_univ_three, CAS16C03.sphereX,
    CAS16C03.sphereY, CAS16C03.sphereZ]
  rw [mul_pow, mul_pow, Real.sq_sqrt hmu]
  nlinarith [Real.sin_sq_add_cos_sq phi.1]

noncomputable def chartPoint (z : ChartDomain) : S2 :=
  ⟨![CAS16C03.sphereX z.1.1 z.2.1,
     CAS16C03.sphereY z.1.1 z.2.1,
     CAS16C03.sphereZ z.1.1], chartVec_unit z.1 z.2⟩

noncomputable def muMeasure : Measure MuChart :=
  Measure.comap Subtype.val (volume : Measure Real)

noncomputable def phiMeasure : Measure PhiChart :=
  Measure.comap Subtype.val (volume : Measure Real)

noncomputable def chartMeasure : Measure ChartDomain :=
  muMeasure.prod phiMeasure

/-- Explicit pushforward of the coordinate chart's restricted product Lebesgue measure. -/
noncomputable def sigmaChart : Measure S2 := Measure.map chartPoint chartMeasure

private theorem measurable_chartPoint : Measurable chartPoint := by
  apply Measurable.subtype_mk
  apply measurable_pi_iff.mpr
  intro i
  fin_cases i <;> simp [chartPoint, CAS16C03.sphereX,
    CAS16C03.sphereY, CAS16C03.sphereZ] <;> fun_prop

private theorem muMeasure_univ : muMeasure Set.univ = ENNReal.ofReal 2 := by
  rw [muMeasure, comap_subtype_coe_apply measurableSet_Icc]
  rw [Set.image_univ, Subtype.range_coe_subtype, Set.setOf_mem_eq]
  rw [Real.volume_Icc]
  norm_num

private theorem phiMeasure_univ :
    phiMeasure Set.univ = ENNReal.ofReal (2 * Real.pi) := by
  rw [phiMeasure, comap_subtype_coe_apply measurableSet_Icc]
  rw [Set.image_univ, Subtype.range_coe_subtype, Set.setOf_mem_eq]
  rw [Real.volume_Icc]
  ring

theorem sigmaChart_univ :
    sigmaChart Set.univ = ENNReal.ofReal (4 * Real.pi) := by
  haveI : IsFiniteMeasure phiMeasure := ⟨by
    rw [phiMeasure_univ]
    exact ENNReal.ofReal_lt_top⟩
  rw [sigmaChart, Measure.map_apply measurable_chartPoint MeasurableSet.univ]
  rw [Set.preimage_univ]
  change (muMeasure.prod phiMeasure) Set.univ = _
  rw [← Set.univ_prod_univ, Measure.prod_prod, muMeasure_univ, phiMeasure_univ]
  rw [← ENNReal.ofReal_mul (by norm_num : (0 : Real) ≤ 2)]
  congr 1
  ring

private theorem chartMonomial_integrable (a b c : Nat) :
    Integrable (fun z : ChartDomain =>
      CAS16C03.monomial a b c z.1.1 z.2.1) chartMeasure := by
  letI : IsFiniteMeasure muMeasure := ⟨by
    rw [muMeasure_univ]
    exact ENNReal.ofReal_lt_top⟩
  letI : IsFiniteMeasure phiMeasure := ⟨by
    rw [phiMeasure_univ]
    exact ENNReal.ofReal_lt_top⟩
  letI : CompactSpace MuChart := isCompact_iff_compactSpace.mp isCompact_Icc
  letI : CompactSpace PhiChart := isCompact_iff_compactSpace.mp isCompact_Icc
  have hc : Continuous (fun z : ChartDomain =>
      CAS16C03.monomial a b c z.1.1 z.2.1) := by
    unfold CAS16C03.monomial CAS16C03.sphereX CAS16C03.sphereY
      CAS16C03.sphereZ
    fun_prop
  simpa [chartMeasure] using
    hc.integrable_of_hasCompactSupport (HasCompactSupport.of_compactSpace _)

theorem chart_monomial_bridge (a b c : Nat) :
    (1 / (4 * Real.pi)) *
      (∫ u : S2, u.1 0 ^ a * u.1 1 ^ b * u.1 2 ^ c ∂sigmaChart) =
        CAS16C03.sphereMean a b c := by
  have hm : StronglyMeasurable (fun u : S2 =>
      u.1 0 ^ a * u.1 1 ^ b * u.1 2 ^ c) := by
    have hc (i : Fin 3) : Measurable (fun u : S2 => u.1 i) :=
      (measurable_pi_apply i).comp measurable_subtype_coe
    have hme : Measurable (fun u : S2 =>
        u.1 0 ^ a * u.1 1 ^ b * u.1 2 ^ c) :=
      ((hc 0).pow_const a |>.mul ((hc 1).pow_const b)).mul ((hc 2).pow_const c)
    exact hme.stronglyMeasurable
  rw [sigmaChart, integral_map_of_stronglyMeasurable measurable_chartPoint hm]
  have he : ∀ z : ChartDomain,
      (chartPoint z).1 0 ^ a * (chartPoint z).1 1 ^ b *
        (chartPoint z).1 2 ^ c = CAS16C03.monomial a b c z.1.1 z.2.1 := by
    intro z
    simp [chartPoint, CAS16C03.monomial]
  simp_rw [he]
  haveI : IsFiniteMeasure phiMeasure := ⟨by
    rw [phiMeasure_univ]
    exact ENNReal.ofReal_lt_top⟩
  haveI : IsFiniteMeasure muMeasure := ⟨by
    rw [muMeasure_univ]
    exact ENNReal.ofReal_lt_top⟩
  unfold chartMeasure
  rw [integral_prod _ (chartMonomial_integrable a b c)]
  have hi (mu : MuChart) :
      (∫ phi : PhiChart, CAS16C03.monomial a b c mu.1 phi.1 ∂phiMeasure) =
        ∫ phi in Set.Icc 0 (2 * Real.pi), CAS16C03.monomial a b c mu.1 phi := by
    exact integral_subtype_comap measurableSet_Icc _
  simp_rw [hi]
  rw [show (∫ mu : MuChart,
      (∫ phi in Set.Icc 0 (2 * Real.pi), CAS16C03.monomial a b c mu.1 phi)
        ∂muMeasure) =
      (∫ mu in Set.Icc (-1) 1,
        ∫ phi in Set.Icc 0 (2 * Real.pi), CAS16C03.monomial a b c mu phi) from
    by simpa only [muMeasure] using
      (integral_subtype_comap (μ := (volume : Measure Real))
        (s := Set.Icc (-1 : Real) 1) measurableSet_Icc
        (fun mu : Real =>
          ∫ phi in Set.Icc 0 (2 * Real.pi), CAS16C03.monomial a b c mu phi))]
  unfold CAS16C03.sphereMean
  congr 1
  rw [intervalIntegral.integral_of_le (by norm_num : (-1 : Real) ≤ 1)]
  rw [← integral_Icc_eq_integral_Ioc]
  apply setIntegral_congr_fun measurableSet_Icc
  intro mu hmu
  change (∫ phi in Set.Icc 0 (2 * Real.pi),
      CAS16C03.monomial a b c mu phi) =
    (∫ phi in (0 : Real)..(2 * Real.pi), CAS16C03.monomial a b c mu phi)
  rw [intervalIntegral.integral_of_le Real.two_pi_pos.le]
  rw [← integral_Icc_eq_integral_Ioc]

/-- Euclidean coordinate pairing used only for the bounded real scalar action. -/
def dot (u v : Vec3) : Real := ∑ i, u i * v i

def linearMode (b : Vec3) (u : S2) : Real := dot b u.1

def quadraticMode (A : Matrix (Fin 3) (Fin 3) Real) (u : S2) : Real :=
  ∑ i, ∑ j, A i j * u.1 i * u.1 j

noncomputable def scatter (f : S2 → Real) (e : S2) : Real :=
  ∫ u : S2, (3 * (1 + dot e.1 u.1 ^ 2) / (16 * Real.pi)) * f u ∂sigmaChart

/-! ### Finite moment support (total degree at most four) -/

private theorem continuous_chartPoint : Continuous chartPoint := by
  apply Continuous.subtype_mk
  apply continuous_pi
  intro i
  fin_cases i <;> simp [CAS16C03.sphereX, CAS16C03.sphereY, CAS16C03.sphereZ] <;> fun_prop

@[fun_prop] private theorem continuous_S2_coord {X : Type*} [TopologicalSpace X]
    (f : X → S2) (hf : Continuous f) (i : Fin 3) :
    Continuous fun x => (f x).1 i :=
  (continuous_apply i).comp (continuous_subtype_val.comp hf)

private theorem integrable_of_continuous {f : S2 → Real} (hf : Continuous f) :
    Integrable f sigmaChart := by
  haveI : IsFiniteMeasure muMeasure := ⟨by
    rw [muMeasure_univ]
    exact ENNReal.ofReal_lt_top⟩
  haveI : IsFiniteMeasure phiMeasure := ⟨by
    rw [phiMeasure_univ]
    exact ENNReal.ofReal_lt_top⟩
  haveI : CompactSpace MuChart := isCompact_iff_compactSpace.mp isCompact_Icc
  haveI : CompactSpace PhiChart := isCompact_iff_compactSpace.mp isCompact_Icc
  rw [sigmaChart, integrable_map_measure hf.aestronglyMeasurable
    measurable_chartPoint.aemeasurable]
  unfold chartMeasure
  exact (hf.comp continuous_chartPoint).integrable_of_hasCompactSupport
    (HasCompactSupport.of_compactSpace _)

/-- Radial factor of the chart integral. -/
private noncomputable def R (n c : Nat) : Real :=
  ∫ mu in (-1 : Real)..1, Real.sqrt (1 - mu ^ 2) ^ n * mu ^ c

/-- Azimuthal factor of the chart integral. -/
private noncomputable def J (a b : Nat) : Real :=
  ∫ phi in (0 : Real)..(2 * Real.pi), Real.cos phi ^ a * Real.sin phi ^ b

private theorem sphereMean_factor (a b c : Nat) :
    CAS16C03.sphereMean a b c = (1 / (4 * Real.pi)) * (R (a + b) c * J a b) := by
  unfold CAS16C03.sphereMean
  congr 1
  have hin : ∀ mu : Real,
      (∫ phi in (0 : Real)..(2 * Real.pi), CAS16C03.monomial a b c mu phi) =
        J a b * (Real.sqrt (1 - mu ^ 2) ^ (a + b) * mu ^ c) := by
    intro mu
    unfold J
    rw [← intervalIntegral.integral_mul_const]
    apply intervalIntegral.integral_congr
    intro phi _
    simp only [CAS16C03.monomial, CAS16C03.sphereX, CAS16C03.sphereY,
      CAS16C03.sphereZ, mul_pow, pow_add]
    ring
  simp_rw [hin]
  rw [intervalIntegral.integral_const_mul]
  unfold R
  ring

private theorem mom (a b c : Nat) :
    (∫ u : S2, u.1 0 ^ a * u.1 1 ^ b * u.1 2 ^ c ∂sigmaChart) =
      R (a + b) c * J a b := by
  have h := chart_monomial_bridge a b c
  rw [sphereMean_factor] at h
  have hne : (1 / (4 * Real.pi)) ≠ 0 := by
    have := Real.pi_pos
    positivity
  exact mul_left_cancel₀ hne h

/-! Radial values. -/

private theorem R_zero (c : Nat) : R 0 c = ∫ mu in (-1 : Real)..1, mu ^ c := by
  unfold R
  simp only [pow_zero, one_mul]

private theorem R_two (c : Nat) :
    R 2 c = (∫ mu in (-1 : Real)..1, mu ^ c) - ∫ mu in (-1 : Real)..1, mu ^ (c + 2) := by
  have hsub : (∫ mu in (-1 : Real)..1, mu ^ c) - (∫ mu in (-1 : Real)..1, mu ^ (c + 2)) =
      ∫ mu in (-1 : Real)..1, (mu ^ c - mu ^ (c + 2)) :=
    (intervalIntegral.integral_sub
      (by apply Continuous.intervalIntegrable; fun_prop)
      (by apply Continuous.intervalIntegrable; fun_prop)).symm
  rw [hsub]
  unfold R
  apply intervalIntegral.integral_congr
  intro mu hmu
  rw [Set.uIcc_of_le (by norm_num : (-1 : Real) ≤ 1)] at hmu
  have h0 : 0 ≤ 1 - mu ^ 2 := by nlinarith [hmu.1, hmu.2]
  have hs : Real.sqrt (1 - mu ^ 2) ^ 2 = 1 - mu ^ 2 := Real.sq_sqrt h0
  dsimp only
  rw [hs]
  ring

private theorem R_0_0 : R 0 0 = 2 := by rw [R_zero, integral_pow]; norm_num
private theorem R_0_1 : R 0 1 = 0 := by rw [R_zero, integral_pow]; norm_num
private theorem R_0_2 : R 0 2 = 2 / 3 := by rw [R_zero, integral_pow]; norm_num
private theorem R_0_3 : R 0 3 = 0 := by rw [R_zero, integral_pow]; norm_num
private theorem R_0_4 : R 0 4 = 2 / 5 := by rw [R_zero, integral_pow]; norm_num
private theorem R_2_0 : R 2 0 = 4 / 3 := by
  rw [R_two, integral_pow, integral_pow]; norm_num
private theorem R_2_1 : R 2 1 = 0 := by
  rw [R_two, integral_pow, integral_pow]; norm_num
private theorem R_2_2 : R 2 2 = 4 / 15 := by
  rw [R_two, integral_pow, integral_pow]; norm_num

private theorem R_4_0 : R 4 0 = 16 / 15 := by
  have i1 : IntervalIntegrable (fun mu : Real => mu ^ 0 - 2 * mu ^ 2)
      MeasureTheory.volume (-1) 1 := by
    apply Continuous.intervalIntegrable; fun_prop
  have i2 : IntervalIntegrable (fun mu : Real => mu ^ 4)
      MeasureTheory.volume (-1) 1 := by
    apply Continuous.intervalIntegrable; fun_prop
  have i3 : IntervalIntegrable (fun mu : Real => mu ^ 0)
      MeasureTheory.volume (-1) 1 := by
    apply Continuous.intervalIntegrable; fun_prop
  have i4 : IntervalIntegrable (fun mu : Real => 2 * mu ^ 2)
      MeasureTheory.volume (-1) 1 := by
    apply Continuous.intervalIntegrable; fun_prop
  have hc : R 4 0 = ∫ mu in (-1 : Real)..1, ((mu ^ 0 - 2 * mu ^ 2) + mu ^ 4) := by
    unfold R
    apply intervalIntegral.integral_congr
    intro mu hmu
    rw [Set.uIcc_of_le (by norm_num : (-1 : Real) ≤ 1)] at hmu
    have h0 : 0 ≤ 1 - mu ^ 2 := by nlinarith [hmu.1, hmu.2]
    have hs : Real.sqrt (1 - mu ^ 2) ^ 2 = 1 - mu ^ 2 := Real.sq_sqrt h0
    have h4 : Real.sqrt (1 - mu ^ 2) ^ 4 = (Real.sqrt (1 - mu ^ 2) ^ 2) ^ 2 := by ring
    dsimp only
    rw [h4, hs]
    ring
  rw [hc, intervalIntegral.integral_add i1 i2, intervalIntegral.integral_sub i3 i4,
    intervalIntegral.integral_const_mul, integral_pow, integral_pow, integral_pow]
  norm_num

/-! Azimuthal values. -/

private theorem J_cos_odd (m b : Nat) : J (2 * m + 1) b = 0 := by
  unfold J
  have h : (fun phi : Real => Real.cos phi ^ (2 * m + 1) * Real.sin phi ^ b) =
      fun phi => Real.sin phi ^ b * Real.cos phi ^ (2 * m + 1) :=
    funext fun phi => mul_comm _ _
  rw [h, integral_sin_pow_mul_cos_pow_odd, Real.sin_zero, Real.sin_two_pi,
    intervalIntegral.integral_same]

private theorem J_sin_odd (a m : Nat) : J a (2 * m + 1) = 0 := by
  unfold J
  have h : (fun phi : Real => Real.cos phi ^ a * Real.sin phi ^ (2 * m + 1)) =
      fun phi => Real.sin phi ^ (2 * m + 1) * Real.cos phi ^ a :=
    funext fun phi => mul_comm _ _
  rw [h, integral_sin_pow_odd_mul_cos_pow, Real.cos_zero, Real.cos_two_pi,
    intervalIntegral.integral_same]

private theorem J_1_0 : J 1 0 = 0 := by simpa using J_cos_odd 0 0
private theorem J_1_1 : J 1 1 = 0 := by simpa using J_cos_odd 0 1
private theorem J_1_2 : J 1 2 = 0 := by simpa using J_cos_odd 0 2
private theorem J_1_3 : J 1 3 = 0 := by simpa using J_cos_odd 0 3
private theorem J_3_0 : J 3 0 = 0 := by simpa using J_cos_odd 1 0
private theorem J_3_1 : J 3 1 = 0 := by simpa using J_cos_odd 1 1
private theorem J_0_1 : J 0 1 = 0 := by simpa using J_sin_odd 0 0
private theorem J_2_1 : J 2 1 = 0 := by simpa using J_sin_odd 2 0
private theorem J_0_3 : J 0 3 = 0 := by simpa using J_sin_odd 0 1

private theorem J_0_0 : J 0 0 = 2 * Real.pi := by
  unfold J
  simp

private theorem J_2_0 : J 2 0 = Real.pi := by
  unfold J
  simp only [pow_zero, mul_one]
  rw [integral_cos_sq]
  simp only [Real.sin_two_pi, Real.sin_zero, mul_zero]
  ring

private theorem J_0_2 : J 0 2 = Real.pi := by
  unfold J
  simp only [pow_zero, one_mul]
  rw [integral_sin_sq]
  simp only [Real.sin_two_pi, Real.sin_zero, zero_mul]
  ring

private theorem J_4_0 : J 4 0 = 3 * Real.pi / 4 := by
  unfold J
  simp only [pow_zero, mul_one]
  rw [show (4 : Nat) = 2 + 2 from rfl, integral_cos_pow, integral_cos_sq]
  simp only [Real.sin_two_pi, Real.sin_zero, mul_zero]
  push_cast
  ring

private theorem J_0_4 : J 0 4 = 3 * Real.pi / 4 := by
  unfold J
  simp only [pow_zero, one_mul]
  rw [show (4 : Nat) = 2 + 2 from rfl, integral_sin_pow, integral_sin_sq]
  simp only [Real.sin_two_pi, Real.sin_zero, zero_mul]
  push_cast
  ring

private theorem J_2_2 : J 2 2 = Real.pi / 4 := by
  unfold J
  have h : (fun phi : Real => Real.cos phi ^ 2 * Real.sin phi ^ 2) =
      fun phi => Real.sin phi ^ 2 * Real.cos phi ^ 2 :=
    funext fun phi => mul_comm _ _
  have h8 : Real.sin (4 * (2 * Real.pi)) = 0 := by
    have : (4 : Real) * (2 * Real.pi) = ((8 : Nat) : Real) * Real.pi := by
      push_cast
      ring
    rw [this]
    exact Real.sin_nat_mul_pi 8
  rw [h, integral_sin_sq_mul_cos_sq, h8]
  simp only [mul_zero, Real.sin_zero]
  ring

/-! Coordinate products as monomials. -/

private def ex (i m : Fin 3) : Nat := if i = m then 1 else 0

private theorem ex_00 : ex 0 0 = 1 := by decide
private theorem ex_01 : ex 0 1 = 0 := by decide
private theorem ex_02 : ex 0 2 = 0 := by decide
private theorem ex_10 : ex 1 0 = 0 := by decide
private theorem ex_11 : ex 1 1 = 1 := by decide
private theorem ex_12 : ex 1 2 = 0 := by decide
private theorem ex_20 : ex 2 0 = 0 := by decide
private theorem ex_21 : ex 2 1 = 0 := by decide
private theorem ex_22 : ex 2 2 = 1 := by decide

private theorem coord_eq (v : Vec3) (i : Fin 3) :
    v i = v 0 ^ ex i 0 * v 1 ^ ex i 1 * v 2 ^ ex i 2 := by
  fin_cases i <;> simp [ex]

private theorem M1 (i : Fin 3) :
    (∫ u : S2, u.1 i ∂sigmaChart) =
      R (ex i 0 + ex i 1) (ex i 2) * J (ex i 0) (ex i 1) := by
  have h : (fun u : S2 => u.1 i) =
      fun u => u.1 0 ^ ex i 0 * u.1 1 ^ ex i 1 * u.1 2 ^ ex i 2 :=
    funext fun u => coord_eq u.1 i
  rw [h, mom]

private theorem M2 (i j : Fin 3) :
    (∫ u : S2, u.1 i * u.1 j ∂sigmaChart) =
      R (ex i 0 + ex j 0 + (ex i 1 + ex j 1)) (ex i 2 + ex j 2) *
        J (ex i 0 + ex j 0) (ex i 1 + ex j 1) := by
  have h : (fun u : S2 => u.1 i * u.1 j) =
      fun u => u.1 0 ^ (ex i 0 + ex j 0) * u.1 1 ^ (ex i 1 + ex j 1) *
        u.1 2 ^ (ex i 2 + ex j 2) := by
    funext u
    rw [coord_eq u.1 i, coord_eq u.1 j]
    ring
  rw [h, mom]

private theorem M3 (i j k : Fin 3) :
    (∫ u : S2, u.1 i * u.1 j * u.1 k ∂sigmaChart) =
      R (ex i 0 + ex j 0 + ex k 0 + (ex i 1 + ex j 1 + ex k 1))
        (ex i 2 + ex j 2 + ex k 2) *
        J (ex i 0 + ex j 0 + ex k 0) (ex i 1 + ex j 1 + ex k 1) := by
  have h : (fun u : S2 => u.1 i * u.1 j * u.1 k) =
      fun u => u.1 0 ^ (ex i 0 + ex j 0 + ex k 0) *
        u.1 1 ^ (ex i 1 + ex j 1 + ex k 1) *
        u.1 2 ^ (ex i 2 + ex j 2 + ex k 2) := by
    funext u
    rw [coord_eq u.1 i, coord_eq u.1 j, coord_eq u.1 k]
    ring
  rw [h, mom]

private theorem M4 (i j k l : Fin 3) :
    (∫ u : S2, u.1 i * u.1 j * u.1 k * u.1 l ∂sigmaChart) =
      R (ex i 0 + ex j 0 + ex k 0 + ex l 0 + (ex i 1 + ex j 1 + ex k 1 + ex l 1))
        (ex i 2 + ex j 2 + ex k 2 + ex l 2) *
        J (ex i 0 + ex j 0 + ex k 0 + ex l 0) (ex i 1 + ex j 1 + ex k 1 + ex l 1) := by
  have h : (fun u : S2 => u.1 i * u.1 j * u.1 k * u.1 l) =
      fun u => u.1 0 ^ (ex i 0 + ex j 0 + ex k 0 + ex l 0) *
        u.1 1 ^ (ex i 1 + ex j 1 + ex k 1 + ex l 1) *
        u.1 2 ^ (ex i 2 + ex j 2 + ex k 2 + ex l 2) := by
    funext u
    rw [coord_eq u.1 i, coord_eq u.1 j, coord_eq u.1 k, coord_eq u.1 l]
    ring
  rw [h, mom]

/-! Linearity over the finite index sums. -/

private theorem L1 (w : Fin 3 → Real) :
    (∫ u : S2, ∑ i, w i * u.1 i ∂sigmaChart) =
      ∑ i, w i * ∫ u : S2, u.1 i ∂sigmaChart := by
  rw [integral_finsetSum]
  · exact Finset.sum_congr rfl fun i _ => integral_const_mul _ _
  · intro i _
    exact integrable_of_continuous (by fun_prop)

private theorem L2 (w : Fin 3 → Fin 3 → Real) :
    (∫ u : S2, ∑ i, ∑ j, w i j * (u.1 i * u.1 j) ∂sigmaChart) =
      ∑ i, ∑ j, w i j * ∫ u : S2, u.1 i * u.1 j ∂sigmaChart := by
  rw [integral_finsetSum]
  · refine Finset.sum_congr rfl fun i _ => ?_
    rw [integral_finsetSum]
    · exact Finset.sum_congr rfl fun j _ => integral_const_mul _ _
    · intro j _
      exact integrable_of_continuous (by fun_prop)
  · intro i _
    exact integrable_of_continuous (by fun_prop)

private theorem L3 (w : Fin 3 → Fin 3 → Fin 3 → Real) :
    (∫ u : S2, ∑ i, ∑ j, ∑ k, w i j k * (u.1 i * u.1 j * u.1 k) ∂sigmaChart) =
      ∑ i, ∑ j, ∑ k, w i j k * ∫ u : S2, u.1 i * u.1 j * u.1 k ∂sigmaChart := by
  rw [integral_finsetSum]
  · refine Finset.sum_congr rfl fun i _ => ?_
    rw [integral_finsetSum]
    · refine Finset.sum_congr rfl fun j _ => ?_
      rw [integral_finsetSum]
      · exact Finset.sum_congr rfl fun k _ => integral_const_mul _ _
      · intro k _
        exact integrable_of_continuous (by fun_prop)
    · intro j _
      exact integrable_of_continuous (by fun_prop)
  · intro i _
    exact integrable_of_continuous (by fun_prop)

private theorem L4 (w : Fin 3 → Fin 3 → Fin 3 → Fin 3 → Real) :
    (∫ u : S2, ∑ i, ∑ j, ∑ k, ∑ l,
        w i j k l * (u.1 i * u.1 j * u.1 k * u.1 l) ∂sigmaChart) =
      ∑ i, ∑ j, ∑ k, ∑ l,
        w i j k l * ∫ u : S2, u.1 i * u.1 j * u.1 k * u.1 l ∂sigmaChart := by
  rw [integral_finsetSum]
  · refine Finset.sum_congr rfl fun i _ => ?_
    rw [integral_finsetSum]
    · refine Finset.sum_congr rfl fun j _ => ?_
      rw [integral_finsetSum]
      · refine Finset.sum_congr rfl fun k _ => ?_
        rw [integral_finsetSum]
        · exact Finset.sum_congr rfl fun l _ => integral_const_mul _ _
        · intro l _
          exact integrable_of_continuous (by fun_prop)
      · intro k _
        exact integrable_of_continuous (by fun_prop)
    · intro j _
      exact integrable_of_continuous (by fun_prop)
  · intro i _
    exact integrable_of_continuous (by fun_prop)

private theorem sigmaChart_real_univ : sigmaChart.real Set.univ = 4 * Real.pi := by
  rw [measureReal_def, sigmaChart_univ, ENNReal.toReal_ofReal]
  have := Real.pi_pos
  positivity

/-! ### Finite action on constants, linear modes and trace-free quadratics -/

theorem scatter_affine_traceless_quadratic (c : Real) (b : Vec3)
    (A : Matrix (Fin 3) (Fin 3) Real) (htrace : ∑ i, A i i = 0) (e : S2) :
    scatter (fun u => c + linearMode b u + quadraticMode A u) e =
      c + (1 / 10 : Real) * quadraticMode A e := by
  have he : ∑ i, e.1 i ^ 2 = 1 := e.2
  have hpt : ∀ u : S2,
      3 * (1 + dot e.1 u.1 ^ 2) / (16 * Real.pi) *
          (c + linearMode b u + quadraticMode A u) =
        3 / (16 * Real.pi) *
          (c + (∑ i, b i * u.1 i +
            (∑ i, ∑ j, A i j * (u.1 i * u.1 j) +
              (∑ k, ∑ l, (c * (e.1 k * e.1 l)) * (u.1 k * u.1 l) +
                (∑ k, ∑ l, ∑ i, (e.1 k * e.1 l * b i) * (u.1 k * u.1 l * u.1 i) +
                  ∑ k, ∑ l, ∑ i, ∑ j,
                    (e.1 k * e.1 l * A i j) *
                      (u.1 k * u.1 l * u.1 i * u.1 j)))))) := by
    intro u
    simp only [dot, linearMode, quadraticMode, Fin.sum_univ_three]
    ring
  simp only [scatter, hpt]
  rw [integral_const_mul, integral_add, integral_add, integral_add, integral_add,
    integral_add]
  · rw [integral_const, sigmaChart_real_univ, smul_eq_mul, L1, L2, L2, L3, L4]
    simp only [M1, M2, M3, M4, Fin.sum_univ_three, quadraticMode,
      ex_00, ex_01, ex_02, ex_10, ex_11, ex_12, ex_20, ex_21, ex_22, Nat.reduceAdd]
    simp only [R_0_0, R_0_1, R_0_2, R_0_3, R_0_4, R_2_0, R_2_1, R_2_2, R_4_0,
      J_0_0, J_1_0, J_0_1, J_1_1, J_2_0, J_0_2, J_2_1, J_1_2, J_3_0, J_0_3,
      J_4_0, J_0_4, J_2_2, J_3_1, J_1_3]
    simp only [Fin.sum_univ_three] at he htrace
    have hpi : Real.pi ≠ 0 := Real.pi_ne_zero
    have hK : 3 / (16 * Real.pi) * Real.pi = 3 / 16 := by
      field_simp
    linear_combination
      (4 * c + 4 / 3 * (A 0 0 + A 1 1 + A 2 2) +
        4 / 3 * c * (e.1 0 ^ 2 + e.1 1 ^ 2 + e.1 2 ^ 2) +
        4 / 15 * ((e.1 0 ^ 2 + e.1 1 ^ 2 + e.1 2 ^ 2) * (A 0 0 + A 1 1 + A 2 2) +
          2 * (A 0 0 * e.1 0 * e.1 0 + A 0 1 * e.1 0 * e.1 1 + A 0 2 * e.1 0 * e.1 2 +
            A 1 0 * e.1 1 * e.1 0 + A 1 1 * e.1 1 * e.1 1 + A 1 2 * e.1 1 * e.1 2 +
            A 2 0 * e.1 2 * e.1 0 + A 2 1 * e.1 2 * e.1 1 + A 2 2 * e.1 2 * e.1 2))) * hK +
      (c / 4 + (A 0 0 + A 1 1 + A 2 2) / 20) * he + (3 / 10) * htrace
  all_goals exact integrable_of_continuous (by fun_prop)

theorem scatter_affine_traceless_quadratic_moments (c : Real) (b : Vec3)
    (A : Matrix (Fin 3) (Fin 3) Real) (htrace : ∑ i, A i i = 0) (e : S2) :
    scatter (fun u => c + linearMode b u + quadraticMode A u) e =
      CAS12ScalarWrapper.moment 0 * c + CAS12ScalarWrapper.moment 1 * linearMode b e +
        CAS12ScalarWrapper.moment 2 * quadraticMode A e := by
  rw [scatter_affine_traceless_quadratic c b A htrace e]
  simp [CAS12ScalarWrapper.scalar_thomson_moment]

end G12CFiniteChart
