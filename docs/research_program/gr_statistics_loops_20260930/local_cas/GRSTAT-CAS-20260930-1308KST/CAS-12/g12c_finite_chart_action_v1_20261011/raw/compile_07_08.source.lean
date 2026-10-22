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
    integral_subtype_comap measurableSet_Icc _]
  unfold CAS16C03.sphereMean
  congr 1
  rw [intervalIntegral.integral_of_le (by norm_num : (-1 : Real) ≤ 1)]
  rw [← integral_Icc_eq_integral_Ioc]
  apply setIntegral_congr_fun measurableSet_Icc
  intro mu hmu
  rw [intervalIntegral.integral_of_le Real.two_pi_pos.le]
  rw [← integral_Icc_eq_integral_Ioc]

end G12CFiniteChart
