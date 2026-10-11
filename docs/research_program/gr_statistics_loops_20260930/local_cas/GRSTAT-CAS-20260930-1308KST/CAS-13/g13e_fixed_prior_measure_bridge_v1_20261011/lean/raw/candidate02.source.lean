import MeasureExtremizerBridge
import RationalCounterexample

open MeasureTheory
noncomputable section

def fixedA : ℝ := 4 / 5
def fixedB : ℝ := 6 / 5
def fixedM3 : ℝ := 26 / 25
def fixedM4 : ℝ := 3376 / 3125
def frame5 : ℝ := 5698688 / 5078125
def frame6 : ℝ := 9619385344 / 8251953125
def matchedTau : ℝ := fixedM4 / fixedM3
def matchedAmplitude : ℝ := fixedM3 ^ 4 / fixedM4 ^ 3

private theorem fixedM3_pos : 0 < fixedM3 := by norm_num [fixedM3]
private theorem fixedM4_pos : 0 < fixedM4 := by norm_num [fixedM4]

theorem fixed_data_strictInterior :
    CAS13C02.StrictInterior fixedA fixedB fixedM3 fixedM4 := by
  have htpos : 0 < fixedM3 ^ ((4 : ℝ) / 3) :=
    Real.rpow_pos_of_pos fixedM3_pos _
  have ht3 : (fixedM3 ^ ((4 : ℝ) / 3)) ^ 3 = fixedM3 ^ 4 := by
    calc
      _ = fixedM3 ^ (((4 : ℝ) / 3) * 3) := by
        simpa only [Real.rpow_natCast] using
          (Real.rpow_mul fixedM3_pos.le ((4 : ℝ) / 3) (3 : ℝ)).symm
      _ = fixedM3 ^ 4 := by norm_num
  have hlow : fixedM3 ^ ((4 : ℝ) / 3) < fixedM4 := by
    have hnum : fixedM3 ^ 4 < fixedM4 ^ 3 := by
      norm_num [fixedM3, fixedM4]
    exact lt_of_pow_lt_pow_left₀ 3 fixedM4_pos.le (by rw [ht3]; exact hnum)
  refine ⟨?_, ?_, ?_, ?_, hlow, ?_⟩ <;>
    norm_num [fixedA, fixedB, fixedM3, fixedM4]

private theorem witness_data :
    ∃ u : ℝ, (539 / 500 : ℝ) < u ∧ u < (1079 / 1000 : ℝ) ∧
      20625 * u ^ 3 - 9700 * u ^ 2 - 7760 * u - 6208 = 0 ∧
      frame5 < (8250 * u ^ 4 + 6600 * u ^ 3 + 10400 * u ^ 2 +
        8320 * u + 6656) / (15625 * u ^ 2 + 12500 * u + 10000) ∧
      frame6 < 66 * u ^ 3 / 125 + 1664 / 3125 := by
  simpa only [frame5, frame6] using
    CAS13RationalCounterexample.g13e_rational_counterexample

private theorem witness_node {u : ℝ}
    (hlo : (539 / 500 : ℝ) < u) (hhi : u < (1079 / 1000 : ℝ))
    (hcubic : 20625 * u ^ 3 - 9700 * u ^ 2 - 7760 * u - 6208 = 0) :
    CAS13C02.positiveCubeRoot fixedM3 < u ∧ u < fixedB ∧
      (u ^ 4 - fixedA ^ 4) / (u ^ 3 - fixedA ^ 3) =
        (fixedM4 - fixedA ^ 4) / (fixedM3 - fixedA ^ 3) := by
  have hu0 : 0 < u := by linarith
  have ha0 : 0 < fixedA := by norm_num [fixedA]
  have hau : fixedA < u := by norm_num [fixedA] at *; linarith
  have hr3 := CAS13C02.positiveCubeRoot_cube fixedM3_pos.le
  have hr0 := CAS13C02.positiveCubeRoot_pos fixedM3_pos
  have hrlt : CAS13C02.positiveCubeRoot fixedM3 < u := by
    have hcube : fixedM3 < u ^ 3 := by
      have hh : (539 / 500 : ℝ) ^ 3 < u ^ 3 :=
        pow_lt_pow_left₀ hlo (by norm_num) (by norm_num)
      norm_num [fixedM3] at *
      linarith
    exact lt_of_pow_lt_pow_left₀ 3 hu0.le (by rw [hr3]; exact hcube)
  have hub : u < fixedB := by norm_num [fixedB] at *; linarith
  have hden1 : u ^ 3 - fixedA ^ 3 ≠ 0 :=
    (CAS13C02.cube_sub_pos ha0 hu0 hau).ne'
  have hden2 : fixedM3 - fixedA ^ 3 ≠ 0 := by norm_num [fixedM3, fixedA]
  refine ⟨hrlt, hub, ?_⟩
  apply (div_eq_div_iff hden1 hden2).2
  dsimp only [fixedA, fixedM3, fixedM4]
  have hfactor :
      (u ^ 4 - (4 / 5 : ℝ) ^ 4) * ((26 / 25 : ℝ) - (4 / 5 : ℝ) ^ 3) -
        ((3376 / 3125 : ℝ) - (4 / 5 : ℝ) ^ 4) *
          (u ^ 3 - (4 / 5 : ℝ) ^ 3) =
      2 * (5 * u - 4) *
        (20625 * u ^ 3 - 9700 * u ^ 2 - 7760 * u - 6208) / 390625 := by
    ring
  exact sub_eq_zero.mp (by rw [hfactor, hcubic]; ring :
    (u ^ 4 - (4 / 5 : ℝ) ^ 4) * ((26 / 25 : ℝ) - (4 / 5 : ℝ) ^ 3) -
      ((3376 / 3125 : ℝ) - (4 / 5 : ℝ) ^ 4) *
        (u ^ 3 - (4 / 5 : ℝ) ^ 3) = 0)

private theorem witness_is_unique_lower_node {u : ℝ}
    (hu : CAS13C02.positiveCubeRoot fixedM3 < u ∧ u < fixedB ∧
      (u ^ 4 - fixedA ^ 4) / (u ^ 3 - fixedA ^ 3) =
        (fixedM4 - fixedA ^ 4) / (fixedM3 - fixedA ^ 3)) :
    ∀ v : ℝ, (CAS13C02.positiveCubeRoot fixedM3 < v ∧ v < fixedB ∧
      (v ^ 4 - fixedA ^ 4) / (v ^ 3 - fixedA ^ 3) =
        (fixedM4 - fixedA ^ 4) / (fixedM3 - fixedA ^ 3)) → v = u := by
  obtain ⟨v, hv, huniq⟩ := CAS13C02.lower_node_existsUnique fixed_data_strictInterior
  intro x hx
  exact (huniq x hx).trans (huniq u hu).symm

private theorem lower_measure_data {u : ℝ}
    (hu : CAS13C02.positiveCubeRoot fixedM3 < u ∧ u < fixedB ∧
      (u ^ 4 - fixedA ^ 4) / (u ^ 3 - fixedA ^ 3) =
        (fixedM4 - fixedA ^ 4) / (fixedM3 - fixedA ^ 3)) :
    let w := CAS13C02.lowerWeight fixedA fixedM3 u
    0 < w ∧ w < 1 ∧
      (1 - w) * fixedA ^ 3 + w * u ^ 3 = fixedM3 ∧
      (1 - w) * fixedA ^ 4 + w * u ^ 4 = fixedM4 := by
  obtain ⟨hw0, hw1, _, hm3, hm4⟩ :=
    CAS13C02.lower_weight_moments fixed_data_strictInterior hu
  exact ⟨hw0, hw1, hm3, hm4⟩

theorem fixed_prior_fibre_nonempty :
    ∃ μ : Measure ℝ,
      CAS13MeasureComposition.Admissible μ fixedA fixedB fixedM3 fixedM4 5 ∧
      CAS13MeasureComposition.Admissible μ fixedA fixedB fixedM3 fixedM4 6 := by
  obtain ⟨u, hlo, hhi, hcubic, _, _⟩ := witness_data
  have hu := witness_node hlo hhi hcubic
  let w := CAS13C02.lowerWeight fixedA fixedM3 u
  obtain ⟨hw0, hw1, hm3, hm4⟩ := lower_measure_data hu
  have haI : fixedA ∈ Set.Icc fixedA fixedB :=
    ⟨le_rfl, fixed_data_strictInterior.a_lt_b.le⟩
  have huI : u ∈ Set.Icc fixedA fixedB := by
    obtain ⟨_, _, har, _⟩ := CAS13C02.root_properties fixed_data_strictInterior
    exact ⟨(har.trans hu.1).le, hu.2.1.le⟩
  refine ⟨CAS13MeasureComposition.twoDirac w fixedA u, ?_, ?_⟩
  · exact CAS13MeasureComposition.twoDirac_admissible 5 hw0.le hw1.le haI huI hm3 hm4
  · exact CAS13MeasureComposition.twoDirac_admissible 6 hw0.le hw1.le haI huI hm3 hm4

private theorem witness_lower_results :
    ∃ u : ℝ, (539 / 500 : ℝ) < u ∧
      frame5 < (8250 * u ^ 4 + 6600 * u ^ 3 + 10400 * u ^ 2 +
        8320 * u + 6656) / (15625 * u ^ 2 + 12500 * u + 10000) ∧
      frame6 < 66 * u ^ 3 / 125 + 1664 / 3125 ∧
      CAS13MeasureExtremizerBridge.LowerResult 5 fixedA fixedB u
        (CAS13C02.lowerWeight fixedA fixedM3 u)
        (CAS13C03.c05 fixedA u) (CAS13C03.c35 fixedA u)
        (CAS13C03.c45 fixedA u) fixedM3 fixedM4 ∧
      CAS13MeasureExtremizerBridge.LowerResult 6 fixedA fixedB u
        (CAS13C02.lowerWeight fixedA fixedM3 u)
        (CAS13C03.c06 fixedA u) (CAS13C03.c36 fixedA u)
        (CAS13C03.c46 fixedA u) fixedM3 fixedM4 := by
  obtain ⟨u, hlo, hhi, hcubic, hgap5, hgap6⟩ := witness_data
  have hu := witness_node hlo hhi hcubic
  obtain ⟨v, d, hv, hd, h5, _, h6, _⟩ :=
    CAS13MeasureExtremizerBridge.strictInterior_measure_extremizers fixed_data_strictInterior
  have hvu : v = u := witness_is_unique_lower_node hu v hv
  subst v
  exact ⟨u, hlo, hgap5, hgap6, h5, h6⟩

private theorem fifth_moment_response {u : ℝ}
    (hu : (539 / 500 : ℝ) < u) :
    CAS13MeasureComposition.moment
      (CAS13MeasureComposition.twoDirac
        (CAS13C02.lowerWeight fixedA fixedM3 u) fixedA u) 5 =
      (8250 * u ^ 4 + 6600 * u ^ 3 + 10400 * u ^ 2 +
        8320 * u + 6656) / (15625 * u ^ 2 + 12500 * u + 10000) := by
  have hden : u ^ 3 - fixedA ^ 3 ≠ 0 := by
    have hu0 : 0 < u := by linarith
    have ha0 : 0 < fixedA := by norm_num [fixedA]
    have hau : fixedA < u := by norm_num [fixedA] at *; linarith
    exact (CAS13C02.cube_sub_pos ha0 hu0 hau).ne'
  have hquad : (15625 * u ^ 2 + 12500 * u + 10000 : ℝ) ≠ 0 := by
    have hu0 : 0 < u := by linarith
    have hpos : 0 < (15625 * u ^ 2 + 12500 * u + 10000 : ℝ) := by positivity
    exact hpos.ne'
  have hden' : (125 * u ^ 3 - 64 : ℝ) ≠ 0 := by
    intro heq
    apply hden
    dsimp [fixedA]
    norm_num at *
    linear_combination heq / 125
  have hw0 : 0 ≤ CAS13C02.lowerWeight fixedA fixedM3 u := by
    unfold CAS13C02.lowerWeight
    apply div_nonneg
    · norm_num [fixedM3, fixedA]
    · have hu0 : 0 < u := by linarith
      have ha0 : 0 < fixedA := by norm_num [fixedA]
      have hau : fixedA < u := by norm_num [fixedA] at *; linarith
      exact (CAS13C02.cube_sub_pos ha0 hu0 hau).le
  have hw1 : CAS13C02.lowerWeight fixedA fixedM3 u ≤ 1 := by
    unfold CAS13C02.lowerWeight
    apply (div_le_one ?_).2
    · norm_num [fixedM3, fixedA]
      have hcube : (539 / 500 : ℝ) ^ 3 < u ^ 3 :=
        pow_lt_pow_left₀ hu (by norm_num) (by norm_num)
      norm_num at hcube
      linarith
    · have hu0 : 0 < u := by linarith
      have ha0 : 0 < fixedA := by norm_num [fixedA]
      have hau : fixedA < u := by norm_num [fixedA] at *; linarith
      exact (CAS13C02.cube_sub_pos ha0 hu0 hau)
  rw [CAS13MeasureComposition.moment_twoDirac 5 hw0 hw1]
  unfold CAS13C02.lowerWeight
  norm_num [fixedA, fixedM3]
  field_simp [hden']
  ring

private theorem sixth_moment_response {u : ℝ}
    (hu : (539 / 500 : ℝ) < u) :
    CAS13MeasureComposition.moment
      (CAS13MeasureComposition.twoDirac
        (CAS13C02.lowerWeight fixedA fixedM3 u) fixedA u) 6 =
      66 * u ^ 3 / 125 + 1664 / 3125 := by
  have hu0 : 0 < u := by linarith
  have ha0 : 0 < fixedA := by norm_num [fixedA]
  have hau : fixedA < u := by norm_num [fixedA] at *; linarith
  have hden : u ^ 3 - fixedA ^ 3 ≠ 0 :=
    (CAS13C02.cube_sub_pos ha0 hu0 hau).ne'
  have hden' : (125 * u ^ 3 - 64 : ℝ) ≠ 0 := by
    intro heq
    apply hden
    dsimp [fixedA]
    norm_num at *
    linear_combination heq / 125
  have hw0 : 0 ≤ CAS13C02.lowerWeight fixedA fixedM3 u := by
    unfold CAS13C02.lowerWeight
    exact div_nonneg (by norm_num [fixedM3, fixedA])
      (CAS13C02.cube_sub_pos ha0 hu0 hau).le
  have hw1 : CAS13C02.lowerWeight fixedA fixedM3 u ≤ 1 := by
    unfold CAS13C02.lowerWeight
    apply (div_le_one (CAS13C02.cube_sub_pos ha0 hu0 hau)).2
    have hcube : (539 / 500 : ℝ) ^ 3 < u ^ 3 :=
      pow_lt_pow_left₀ hu (by norm_num) (by norm_num)
    norm_num [fixedA, fixedM3] at *
    linarith
  rw [CAS13MeasureComposition.moment_twoDirac 6 hw0 hw1]
  unfold CAS13C02.lowerWeight
  norm_num [fixedA, fixedM3]
  field_simp [hden']
  ring

theorem frame5_lt_every_admissible (μ : Measure ℝ)
    (hμ : CAS13MeasureComposition.Admissible μ fixedA fixedB fixedM3 fixedM4 5) :
    frame5 < CAS13MeasureComposition.moment μ 5 := by
  obtain ⟨u, hlo, hgap5, _, h5, _⟩ := witness_lower_results
  obtain ⟨hbound, hattain, _⟩ := h5 μ hμ
  rw [fifth_moment_response hlo] at hattain
  exact hgap5.trans_le (hattain.trans_le hbound)

theorem frame6_lt_every_admissible (μ : Measure ℝ)
    (hμ : CAS13MeasureComposition.Admissible μ fixedA fixedB fixedM3 fixedM4 6) :
    frame6 < CAS13MeasureComposition.moment μ 6 := by
  obtain ⟨u, hlo, _, hgap6, _, h6⟩ := witness_lower_results
  obtain ⟨hbound, hattain, _⟩ := h6 μ hμ
  rw [sixth_moment_response hlo] at hattain
  exact hgap6.trans_le (hattain.trans_le hbound)

theorem frame5_not_attained :
    ¬ ∃ μ : Measure ℝ,
      CAS13MeasureComposition.Admissible μ fixedA fixedB fixedM3 fixedM4 5 ∧
      CAS13MeasureComposition.moment μ 5 = frame5 := by
  rintro ⟨μ, hμ, heq⟩
  exact (frame5_lt_every_admissible μ hμ).ne heq.symm

theorem frame6_not_attained :
    ¬ ∃ μ : Measure ℝ,
      CAS13MeasureComposition.Admissible μ fixedA fixedB fixedM3 fixedM4 6 ∧
      CAS13MeasureComposition.moment μ 6 = frame6 := by
  rintro ⟨μ, hμ, heq⟩
  exact (frame6_lt_every_admissible μ hμ).ne heq.symm

theorem frame_pair_not_jointly_attained :
    ¬ ∃ μ : Measure ℝ,
      CAS13MeasureComposition.Admissible μ fixedA fixedB fixedM3 fixedM4 5 ∧
      CAS13MeasureComposition.Admissible μ fixedA fixedB fixedM3 fixedM4 6 ∧
      CAS13MeasureComposition.moment μ 5 = frame5 ∧
      CAS13MeasureComposition.moment μ 6 = frame6 := by
  rintro ⟨μ, h5, _, heq5, _⟩
  exact (frame5_lt_every_admissible μ h5).ne heq5.symm

theorem matched_parameters_exact :
    matchedTau = 1688 / 1625 ∧
    matchedAmplitude = 2231328125 / 2404846336 ∧
    0 < matchedAmplitude ∧ matchedAmplitude < 1 ∧
    fixedA < matchedTau ∧ matchedTau < fixedB ∧
    matchedAmplitude * matchedTau ^ 3 = fixedM3 ∧
    matchedAmplitude * matchedTau ^ 4 = fixedM4 ∧
    matchedAmplitude * matchedTau ^ 5 = fixedM4 ^ 2 / fixedM3 ∧
    matchedAmplitude * matchedTau ^ 6 = fixedM4 ^ 3 / fixedM3 ^ 2 := by
  norm_num [matchedTau, matchedAmplitude, fixedA, fixedB, fixedM3, fixedM4]

theorem matched_log_shift :
    Real.log matchedAmplitude =
      4 * Real.log fixedM3 - 3 * Real.log fixedM4 ∧
    Real.log matchedAmplitude < 0 := by
  have h := matched_parameters_exact
  constructor
  · unfold matchedAmplitude
    rw [Real.log_div (pow_ne_zero 4 fixedM3_pos.ne')
      (pow_ne_zero 3 fixedM4_pos.ne'), Real.log_pow, Real.log_pow]
    ring
  · exact Real.log_neg (by exact h.2.2.1) h.2.2.2.1

#check fixed_data_strictInterior
#check fixed_prior_fibre_nonempty
#check frame5_lt_every_admissible
#check frame6_lt_every_admissible
#check frame5_not_attained
#check frame6_not_attained
#check frame_pair_not_jointly_attained
#check matched_parameters_exact
#check matched_log_shift
#print axioms fixed_data_strictInterior
#print axioms fixed_prior_fibre_nonempty
#print axioms frame5_lt_every_admissible
#print axioms frame6_lt_every_admissible
#print axioms frame5_not_attained
#print axioms frame6_not_attained
#print axioms frame_pair_not_jointly_attained
#print axioms matched_parameters_exact
#print axioms matched_log_shift
