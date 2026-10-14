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
  change (volume : Measure Real) (Set.Icc (-1) 1) = ENNReal.ofReal 2
  rw [Real.volume_Icc]
  norm_num

private theorem phiMeasure_univ :
    phiMeasure Set.univ = ENNReal.ofReal (2 * Real.pi) := by
  rw [phiMeasure, comap_subtype_coe_apply measurableSet_Icc]
  change (volume : Measure Real) (Set.Icc 0 (2 * Real.pi)) =
    ENNReal.ofReal (2 * Real.pi)
  rw [Real.volume_Icc]
  ring

theorem sigmaChart_univ :
    sigmaChart Set.univ = ENNReal.ofReal (4 * Real.pi) := by
  haveI : FiniteMeasure phiMeasure := ⟨by
    rw [phiMeasure_univ]
    exact ENNReal.ofReal_lt_top⟩
  rw [sigmaChart, Measure.map_apply measurable_chartPoint MeasurableSet.univ]
  rw [Set.preimage_univ]
  change (muMeasure.prod phiMeasure) Set.univ = _
  rw [← Set.univ_prod_univ, Measure.prod_prod, muMeasure_univ, phiMeasure_univ]
  rw [← ENNReal.ofReal_mul (by norm_num : (0 : Real) ≤ 2)]
  congr 1
  ring

end G12CFiniteChart
