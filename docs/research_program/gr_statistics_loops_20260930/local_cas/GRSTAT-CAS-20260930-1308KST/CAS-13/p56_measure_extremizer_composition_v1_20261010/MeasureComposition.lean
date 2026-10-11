import Mathlib

/-!
Conditional CAS13 measure composition. C02 feasibility and C03 Hermite sign/contact
facts are hypotheses; their polynomial derivations are not reproved here. All
integrals below are actual real Bochner integrals against measures on ℝ. No C04
relative-minimax result or scientific admission is used or asserted.
-/

noncomputable section
open MeasureTheory
open scoped ENNReal

namespace CAS13MeasureComposition

def hermite (c0 c3 c4 x : ℝ) : ℝ := c0 + c3 * x ^ 3 + c4 * x ^ 4

def moment (μ : Measure ℝ) (p : ℕ) : ℝ := ∫ x : ℝ, x ^ p ∂μ

/-- The weight `w` belongs to the second node; `1-w` belongs to the first. -/
def twoDirac (w a u : ℝ) : Measure ℝ :=
  ENNReal.ofReal (1 - w) • Measure.dirac a + ENNReal.ofReal w • Measure.dirac u

theorem twoDirac_probability {w a u : ℝ} (hw0 : 0 ≤ w) (hw1 : w ≤ 1) :
    IsProbabilityMeasure (twoDirac w a u) := by
  constructor
  simp only [twoDirac, Measure.add_apply, Measure.smul_apply, Measure.dirac_apply_of_mem,
    Set.mem_univ, smul_eq_mul, mul_one]
  rw [← ENNReal.ofReal_add (sub_nonneg.mpr hw1) hw0]
  simp

/-- All real-valued functions have finite integrals on this finite-support measure. -/
theorem integrable_twoDirac (f : ℝ → ℝ) (w a u : ℝ) :
    Integrable f (twoDirac w a u) := by
  have ha : Integrable f (Measure.dirac a) := integrable_dirac (by simp)
  have hu : Integrable f (Measure.dirac u) := integrable_dirac (by simp)
  exact (ha.smul_measure ENNReal.ofReal_ne_top).add_measure
    (hu.smul_measure ENNReal.ofReal_ne_top)

theorem integral_twoDirac (f : ℝ → ℝ) {w a u : ℝ}
    (hw0 : 0 ≤ w) (hw1 : w ≤ 1) :
    (∫ x, f x ∂twoDirac w a u) = (1 - w) * f a + w * f u := by
  have ha : Integrable f (Measure.dirac a) := integrable_dirac (by simp)
  have hu : Integrable f (Measure.dirac u) := integrable_dirac (by simp)
  rw [twoDirac, integral_add_measure (ha.smul_measure ENNReal.ofReal_ne_top)
    (hu.smul_measure ENNReal.ofReal_ne_top)]
  simp only [integral_smul_measure, integral_dirac, ENNReal.toReal_ofReal hw0,
    ENNReal.toReal_ofReal (sub_nonneg.mpr hw1), smul_eq_mul]

theorem moment_twoDirac (p : ℕ) {w a u : ℝ} (hw0 : 0 ≤ w) (hw1 : w ≤ 1) :
    moment (twoDirac w a u) p = (1 - w) * a ^ p + w * u ^ p :=
  integral_twoDirac (fun x => x ^ p) hw0 hw1

theorem twoDirac_supported {w v z a b : ℝ}
    (hv : v ∈ Set.Icc a b) (hz : z ∈ Set.Icc a b) :
    ∀ᵐ x ∂twoDirac w v z, x ∈ Set.Icc a b := by
  rw [twoDirac, ae_add_measure_iff]
  exact ⟨Measure.ae_smul_measure ((ae_dirac_iff measurableSet_Icc).mpr hv) _,
    Measure.ae_smul_measure ((ae_dirac_iff measurableSet_Icc).mpr hz) _⟩

theorem integrable_hermite (μ : Measure ℝ) [IsProbabilityMeasure μ]
    {c0 c3 c4 : ℝ} (h3 : Integrable (fun x : ℝ => x ^ 3) μ)
    (h4 : Integrable (fun x : ℝ => x ^ 4) μ) :
    Integrable (hermite c0 c3 c4) μ :=
  ((integrable_const c0).add (h3.const_mul c3)).add (h4.const_mul c4)

theorem integral_hermite (μ : Measure ℝ) [IsProbabilityMeasure μ]
    {c0 c3 c4 m3 m4 : ℝ} (h3 : Integrable (fun x : ℝ => x ^ 3) μ)
    (h4 : Integrable (fun x : ℝ => x ^ 4) μ)
    (hm3 : moment μ 3 = m3) (hm4 : moment μ 4 = m4) :
    (∫ x, hermite c0 c3 c4 x ∂μ) = c0 + c3 * m3 + c4 * m4 := by
  have hc3 : Integrable (fun x : ℝ => c3 * x ^ 3) μ := h3.const_mul c3
  have hc4 : Integrable (fun x : ℝ => c4 * x ^ 4) μ := h4.const_mul c4
  have hsum : Integrable (fun x : ℝ => c0 + c3 * x ^ 3) μ :=
    (integrable_const c0).add hc3
  simp only [hermite]
  rw [integral_add hsum hc4, integral_add (integrable_const c0) hc3,
    integral_const_mul, integral_const_mul]
  simp only [integral_const, probReal_univ, one_smul]
  change c0 + c3 * moment μ 3 + c4 * moment μ 4 = _
  rw [hm3, hm4]

/-- Transport a pointwise lower Hermite certificate on the supported interval. -/
theorem lower_transport (p : ℕ) (μ : Measure ℝ) [IsProbabilityMeasure μ]
    {a b c0 c3 c4 m3 m4 : ℝ}
    (hsupport : ∀ᵐ x ∂μ, x ∈ Set.Icc a b)
    (h3 : Integrable (fun x : ℝ => x ^ 3) μ)
    (h4 : Integrable (fun x : ℝ => x ^ 4) μ)
    (hp : Integrable (fun x : ℝ => x ^ p) μ)
    (hm3 : moment μ 3 = m3) (hm4 : moment μ 4 = m4)
    (hlower : ∀ x ∈ Set.Icc a b, hermite c0 c3 c4 x ≤ x ^ p) :
    c0 + c3 * m3 + c4 * m4 ≤ moment μ p := by
  rw [← integral_hermite μ h3 h4 hm3 hm4]
  exact integral_mono_ae (integrable_hermite μ h3 h4) hp
    (hsupport.mono (fun x hx => hlower x hx))

/-- Transport a pointwise upper Hermite certificate on the supported interval. -/
theorem upper_transport (p : ℕ) (μ : Measure ℝ) [IsProbabilityMeasure μ]
    {a b c0 c3 c4 m3 m4 : ℝ}
    (hsupport : ∀ᵐ x ∂μ, x ∈ Set.Icc a b)
    (h3 : Integrable (fun x : ℝ => x ^ 3) μ)
    (h4 : Integrable (fun x : ℝ => x ^ 4) μ)
    (hp : Integrable (fun x : ℝ => x ^ p) μ)
    (hm3 : moment μ 3 = m3) (hm4 : moment μ 4 = m4)
    (hupper : ∀ x ∈ Set.Icc a b, x ^ p ≤ hermite c0 c3 c4 x) :
    moment μ p ≤ c0 + c3 * m3 + c4 * m4 := by
  rw [← integral_hermite μ h3 h4 hm3 hm4]
  exact integral_mono_ae hp (integrable_hermite μ h3 h4)
    (hsupport.mono (fun x hx => hupper x hx))

/-- C02 weighted moments and C03 node contacts imply attainment by the actual measure.
No division, node-existence theorem or boundary substitution occurs in this proof. -/
theorem twoDirac_attainment (p : ℕ) {w a u c0 c3 c4 m3 m4 : ℝ}
    (hw0 : 0 ≤ w) (hw1 : w ≤ 1)
    (hm3 : (1 - w) * a ^ 3 + w * u ^ 3 = m3)
    (hm4 : (1 - w) * a ^ 4 + w * u ^ 4 = m4)
    (ha : a ^ p = hermite c0 c3 c4 a)
    (hu : u ^ p = hermite c0 c3 c4 u) :
    moment (twoDirac w a u) p = c0 + c3 * m3 + c4 * m4 := by
  letI := twoDirac_probability (a := a) (u := u) hw0 hw1
  have hmatch3 : moment (twoDirac w a u) 3 = m3 := by
    rw [moment_twoDirac 3 hw0 hw1, hm3]
  have hmatch4 : moment (twoDirac w a u) 4 = m4 := by
    rw [moment_twoDirac 4 hw0 hw1, hm4]
  calc
    moment (twoDirac w a u) p = ∫ x, hermite c0 c3 c4 x ∂twoDirac w a u := by
      rw [moment, integral_twoDirac (fun x : ℝ => x ^ p) hw0 hw1,
        integral_twoDirac (hermite c0 c3 c4) hw0 hw1, ha, hu]
    _ = c0 + c3 * m3 + c4 * m4 := integral_hermite (twoDirac w a u)
      (integrable_twoDirac _ _ _ _) (integrable_twoDirac _ _ _ _) hmatch3 hmatch4

/-- The exact probability, support, finite-moment and moment-matching class. -/
def Admissible (μ : Measure ℝ) (a b m3 m4 : ℝ) (p : ℕ) : Prop :=
  IsProbabilityMeasure μ ∧ (∀ᵐ x ∂μ, x ∈ Set.Icc a b) ∧
    Integrable (fun x : ℝ => x ^ 3) μ ∧ Integrable (fun x : ℝ => x ^ 4) μ ∧
    Integrable (fun x : ℝ => x ^ p) μ ∧ moment μ 3 = m3 ∧ moment μ 4 = m4

theorem twoDirac_admissible (p : ℕ) {w v z a b m3 m4 : ℝ}
    (hw0 : 0 ≤ w) (hw1 : w ≤ 1)
    (hv : v ∈ Set.Icc a b) (hz : z ∈ Set.Icc a b)
    (hm3 : (1 - w) * v ^ 3 + w * z ^ 3 = m3)
    (hm4 : (1 - w) * v ^ 4 + w * z ^ 4 = m4) :
    Admissible (twoDirac w v z) a b m3 m4 p := by
  refine ⟨twoDirac_probability hw0 hw1, twoDirac_supported hv hz,
    integrable_twoDirac _ _ _ _, integrable_twoDirac _ _ _ _,
    integrable_twoDirac _ _ _ _, ?_, ?_⟩
  · rw [moment_twoDirac 3 hw0 hw1, hm3]
  · rw [moment_twoDirac 4 hw0 hw1, hm4]

/-- A lower-bound transport together with its attaining, moment-matched measure. -/
def LowerComposition (p : ℕ) : Prop :=
  ∀ (μ : Measure ℝ), IsProbabilityMeasure μ →
  ∀ (a b v z w c0 c3 c4 m3 m4 : ℝ),
    (∀ᵐ x ∂μ, x ∈ Set.Icc a b) →
    Integrable (fun x : ℝ => x ^ 3) μ →
    Integrable (fun x : ℝ => x ^ 4) μ →
    Integrable (fun x : ℝ => x ^ p) μ →
    moment μ 3 = m3 → moment μ 4 = m4 →
    (∀ x ∈ Set.Icc a b, hermite c0 c3 c4 x ≤ x ^ p) →
    0 ≤ w → w ≤ 1 →
    v ∈ Set.Icc a b → z ∈ Set.Icc a b →
    (1 - w) * v ^ 3 + w * z ^ 3 = m3 →
    (1 - w) * v ^ 4 + w * z ^ 4 = m4 →
    v ^ p = hermite c0 c3 c4 v → z ^ p = hermite c0 c3 c4 z →
    c0 + c3 * m3 + c4 * m4 ≤ moment μ p ∧
      moment (twoDirac w v z) p = c0 + c3 * m3 + c4 * m4 ∧
      Admissible (twoDirac w v z) a b m3 m4 p

/-- The corresponding upper-bound transport and attainment. -/
def UpperComposition (p : ℕ) : Prop :=
  ∀ (μ : Measure ℝ), IsProbabilityMeasure μ →
  ∀ (a b v z w c0 c3 c4 m3 m4 : ℝ),
    (∀ᵐ x ∂μ, x ∈ Set.Icc a b) →
    Integrable (fun x : ℝ => x ^ 3) μ →
    Integrable (fun x : ℝ => x ^ 4) μ →
    Integrable (fun x : ℝ => x ^ p) μ →
    moment μ 3 = m3 → moment μ 4 = m4 →
    (∀ x ∈ Set.Icc a b, x ^ p ≤ hermite c0 c3 c4 x) →
    0 ≤ w → w ≤ 1 →
    v ∈ Set.Icc a b → z ∈ Set.Icc a b →
    (1 - w) * v ^ 3 + w * z ^ 3 = m3 →
    (1 - w) * v ^ 4 + w * z ^ 4 = m4 →
    v ^ p = hermite c0 c3 c4 v → z ^ p = hermite c0 c3 c4 z →
    moment μ p ≤ c0 + c3 * m3 + c4 * m4 ∧
      moment (twoDirac w v z) p = c0 + c3 * m3 + c4 * m4 ∧
      Admissible (twoDirac w v z) a b m3 m4 p

theorem lower_composition (p : ℕ) : LowerComposition p := by
  intro μ hμ a b v z w c0 c3 c4 m3 m4 hs h3 h4 hp hm3 hm4 hl hw0 hw1
    hvs hzs hnode3 hnode4 hv hz
  letI := hμ
  exact ⟨lower_transport p μ hs h3 h4 hp hm3 hm4 hl,
    twoDirac_attainment p hw0 hw1 hnode3 hnode4 hv hz,
    twoDirac_admissible p hw0 hw1 hvs hzs hnode3 hnode4⟩

theorem upper_composition (p : ℕ) : UpperComposition p := by
  intro μ hμ a b v z w c0 c3 c4 m3 m4 hs h3 h4 hp hm3 hm4 hu hw0 hw1
    hvs hzs hnode3 hnode4 hv hz
  letI := hμ
  exact ⟨upper_transport p μ hs h3 h4 hp hm3 hm4 hu,
    twoDirac_attainment p hw0 hw1 hnode3 hnode4 hv hz,
    twoDirac_admissible p hw0 hw1 hvs hzs hnode3 hnode4⟩

theorem p5_lower_composition : LowerComposition 5 := lower_composition 5
theorem p5_upper_composition : UpperComposition 5 := upper_composition 5
theorem p6_lower_composition : LowerComposition 6 := lower_composition 6
theorem p6_upper_composition : UpperComposition 6 := upper_composition 6

theorem p5_p6_measure_composition :
    LowerComposition 5 ∧ UpperComposition 5 ∧ LowerComposition 6 ∧ UpperComposition 6 :=
  ⟨p5_lower_composition, p5_upper_composition, p6_lower_composition, p6_upper_composition⟩

#check twoDirac_probability
#check integral_twoDirac
#check lower_transport
#check upper_transport
#check twoDirac_attainment
#check twoDirac_admissible
#print Admissible
#print LowerComposition
#print UpperComposition
#check p5_p6_measure_composition
#print axioms twoDirac_probability
#print axioms integral_twoDirac
#print axioms lower_transport
#print axioms upper_transport
#print axioms twoDirac_attainment
#print axioms twoDirac_admissible
#print axioms p5_p6_measure_composition

end CAS13MeasureComposition
