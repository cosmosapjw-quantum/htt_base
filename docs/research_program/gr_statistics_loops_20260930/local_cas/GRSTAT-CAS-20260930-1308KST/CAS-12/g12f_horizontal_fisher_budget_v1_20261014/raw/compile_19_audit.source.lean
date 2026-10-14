import G12FInstances

open MeasureTheory Set Filter Topology
open scoped ENNReal
open G11A G12F

/-! Statement alignment: every frozen signature in ../FROZEN_TARGETS.md, re-elaborated verbatim and
closed by the compiled theorem of the same name. -/

example : ∀ (s : Stat) {f : ℝ} (hf : f ∈ cdom s),
    0 ≤ statWeight s f :=
  @G12F.statWeight_nonneg

example : ∀ (s : Stat) {f : ℝ} (hf : f ∈ dom s) (d : ℝ),
    fisherDens d (statWeight s f) = ENNReal.ofReal (d ^ 2 * hess s f) :=
  @G12F.fisherDens_of_dom

example : ∀ {X : Type*} [MeasurableSpace X] (μ : Measure X)
    (K d w ρ : X → ℝ) (J : ℝ)
    (hK : Measurable K) (hd : Measurable d) (hw : Measurable w) (hρ : Measurable ρ)
    (hw0 : ∀ᵐ z ∂μ, 0 ≤ w z) (hρ0 : ∀ᵐ z ∂μ, 0 ≤ ρ z)
    (hKw : Integrable (fun z => K z ^ 2 * w z * ρ z) μ)
    (hJ : ∫⁻ z, ENNReal.ofReal (ρ z) * fisherDens (d z) (w z) ∂μ ≤ ENNReal.ofReal J),
    Integrable (fun z => K z * d z * ρ z) μ ∧
      |∫ z, K z * d z * ρ z ∂μ| ≤ Real.sqrt J * Real.sqrt (∫ z, K z ^ 2 * w z * ρ z ∂μ) :=
  @G12F.weighted_cauchy_schwarz

example : ∀ {X : Type*} [MeasurableSpace X] (μ : Measure X) (s : Stat)
    (d f ρ : X → ℝ) (J : ℝ)
    (hdom : ∀ᵐ z ∂μ, f z ∈ dom s) (hρ0 : ∀ᵐ z ∂μ, 0 ≤ ρ z)
    (hint : Integrable (fun z => d z ^ 2 * hess s (f z) * ρ z) μ)
    (hle : ∫ z, d z ^ 2 * hess s (f z) * ρ z ∂μ ≤ J),
    ∫⁻ z, ENNReal.ofReal (ρ z) * fisherDens (d z) (statWeight s (f z)) ∂μ ≤ ENNReal.ofReal J :=
  @G12F.real_budget_le

example : ∀ {X : Type*} [MeasurableSpace X] (μ : Measure X)
    (d w ρ : X → ℝ) (J : ℝ) (hd : Measurable d) (hw : Measurable w) (hρ : Measurable ρ)
    (hJ : ∫⁻ z, ENNReal.ofReal (ρ z) * fisherDens (d z) (w z) ∂μ ≤ ENNReal.ofReal J),
    ∀ᵐ z ∂μ, w z ≤ 0 → 0 < ρ z → d z = 0 :=
  @G12F.zero_weight_null

example : ∀ (s : Stat) (φ : ℝ → ℝ) (x0 d : ℝ)
    (hφ : ∀ᶠ t in 𝓝 x0, φ t ∈ cdom s) (hd : HasDerivAt φ d x0)
    (h0 : statWeight s (φ x0) = 0),
    d = 0 ∧ fisherDens d (statWeight s (φ x0)) = 0 :=
  @G12F.zero_occupation_derivative

example : ∀ {X : Type*} [MeasurableSpace X] (μ : Measure X) (s : Stat)
    (K ρ : X → ℝ) (f f' : ℝ → X → ℝ) (x0 J : ℝ) (bound : X → ℝ) (U : Set ℝ) (hU : U ∈ 𝓝 x0)
    (hF_meas : ∀ᶠ t in 𝓝 x0, AEStronglyMeasurable (fun z => K z * f t z * ρ z) μ)
    (hF_int : Integrable (fun z => K z * f x0 z * ρ z) μ)
    (h_bound : ∀ᵐ z ∂μ, ∀ t ∈ U, |K z * f' t z * ρ z| ≤ bound z)
    (hbound : Integrable bound μ)
    (h_diff : ∀ᵐ z ∂μ, ∀ t ∈ U, HasDerivAt (fun t => f t z) (f' t z) t)
    (hK : Measurable K) (hρ : Measurable ρ) (hf0 : Measurable (f x0)) (hd : Measurable (f' x0))
    (hρ0 : ∀ᵐ z ∂μ, 0 ≤ ρ z) (hcdom : ∀ᵐ z ∂μ, f x0 z ∈ cdom s)
    (hKw : Integrable (fun z => K z ^ 2 * statWeight s (f x0 z) * ρ z) μ)
    (hJ : ∫⁻ z, ENNReal.ofReal (ρ z) * fisherDens (f' x0 z) (statWeight s (f x0 z)) ∂μ ≤
      ENNReal.ofReal J),
    HasDerivAt (fun t => ∫ z, K z * f t z * ρ z ∂μ) (∫ z, K z * f' x0 z * ρ z ∂μ) x0 ∧
      |∫ z, K z * f' x0 z * ρ z ∂μ| ≤
        Real.sqrt J * Real.sqrt (∫ z, K z ^ 2 * statWeight s (f x0 z) * ρ z ∂μ) :=
  @G12F.parallel_derivative_bound

example : ∀ {X : Type*} [MeasurableSpace X] (μ : Measure X)
    (K : X → ℝ) (f f' : ℝ → X → ℝ) (x0 J : ℝ) (bound : X → ℝ) (U : Set ℝ) (hU : U ∈ 𝓝 x0)
    (hF_meas : ∀ᶠ t in 𝓝 x0, AEStronglyMeasurable (fun z => K z * f t z) μ)
    (hF_int : Integrable (fun z => K z * f x0 z) μ)
    (h_bound : ∀ᵐ z ∂μ, ∀ t ∈ U, |K z * f' t z| ≤ bound z)
    (hbound : Integrable bound μ)
    (h_diff : ∀ᵐ z ∂μ, ∀ t ∈ U, HasDerivAt (fun t => f t z) (f' t z) t)
    (hK : Measurable K) (hf0 : Measurable (f x0)) (hd : Measurable (f' x0))
    (hnn : ∀ᵐ z ∂μ, 0 ≤ f x0 z)
    (hKw : Integrable (fun z => K z ^ 2 * (f x0 z * (1 + f x0 z))) μ)
    (hJ : ∫⁻ z, fisherDens (f' x0 z) (f x0 z * (1 + f x0 z)) ∂μ ≤ ENNReal.ofReal J),
    HasDerivAt (fun t => ∫ z, K z * f t z ∂μ) (∫ z, K z * f' x0 z ∂μ) x0 ∧
      |∫ z, K z * f' x0 z ∂μ| ≤
        Real.sqrt J * Real.sqrt (∫ z, K z ^ 2 * (f x0 z * (1 + f x0 z)) ∂μ) :=
  @G12F.teff_a4_derivative_bound_BE

example : ∀ {X : Type*} [MeasurableSpace X] (μ : Measure X) (s : Stat)
    (K K' f f' ρ ρ' : ℝ → X → ℝ) (x0 J : ℝ) (bound : X → ℝ) (U : Set ℝ) (hU : U ∈ 𝓝 x0)
    (hF_meas : ∀ᶠ t in 𝓝 x0, AEStronglyMeasurable (fun z => K t z * f t z * ρ t z) μ)
    (hF_int : Integrable (fun z => K x0 z * f x0 z * ρ x0 z) μ)
    (h_bound : ∀ᵐ z ∂μ, ∀ t ∈ U, |K t z * f' t z * ρ t z + K' t z * f t z * ρ t z +
      K t z * f t z * ρ' t z| ≤ bound z)
    (hbound : Integrable bound μ)
    (hK_diff : ∀ᵐ z ∂μ, ∀ t ∈ U, HasDerivAt (fun t => K t z) (K' t z) t)
    (hf_diff : ∀ᵐ z ∂μ, ∀ t ∈ U, HasDerivAt (fun t => f t z) (f' t z) t)
    (hρ_diff : ∀ᵐ z ∂μ, ∀ t ∈ U, HasDerivAt (fun t => ρ t z) (ρ' t z) t)
    (hKm : Measurable (K x0)) (hK'm : Measurable (K' x0)) (hfm : Measurable (f x0))
    (hdm : Measurable (f' x0)) (hρm : Measurable (ρ x0)) (hρ'm : Measurable (ρ' x0))
    (hρ0 : ∀ᵐ z ∂μ, 0 ≤ ρ x0 z) (hcdom : ∀ᵐ z ∂μ, f x0 z ∈ cdom s)
    (hKw : Integrable (fun z => K x0 z ^ 2 * statWeight s (f x0 z) * ρ x0 z) μ)
    (hJ : ∫⁻ z, ENNReal.ofReal (ρ x0 z) * fisherDens (f' x0 z) (statWeight s (f x0 z)) ∂μ ≤
      ENNReal.ofReal J)
    (hkern : Integrable (fun z => K' x0 z * f x0 z * ρ x0 z) μ),
    Integrable (fun z => K x0 z * f x0 z * ρ' x0 z) μ ∧
    HasDerivAt (fun t => ∫ z, K t z * f t z * ρ t z ∂μ)
      ((∫ z, K x0 z * f' x0 z * ρ x0 z ∂μ) + (∫ z, K' x0 z * f x0 z * ρ x0 z ∂μ) +
        (∫ z, K x0 z * f x0 z * ρ' x0 z ∂μ)) x0 ∧
    |(∫ z, K x0 z * f' x0 z * ρ x0 z ∂μ) + (∫ z, K' x0 z * f x0 z * ρ x0 z ∂μ) +
        (∫ z, K x0 z * f x0 z * ρ' x0 z ∂μ)| ≤
      Real.sqrt J * Real.sqrt (∫ z, K x0 z ^ 2 * statWeight s (f x0 z) * ρ x0 z ∂μ) +
        |∫ z, K' x0 z * f x0 z * ρ x0 z ∂μ| + |∫ z, K x0 z * f x0 z * ρ' x0 z ∂μ| :=
  @G12F.general_derivative_bound

example : ∀ {X : Type*} [MeasurableSpace X] (μ : Measure X)
    (s : Stat) (K K' f f' ρ ρ' : ℝ → X → ℝ) (x0 J : ℝ) (bound F : X → ℝ) (U : Set ℝ)
    (hU : U ∈ 𝓝 x0)
    (hF_meas : ∀ᶠ t in 𝓝 x0, AEStronglyMeasurable (fun z => K t z * f t z * ρ t z) μ)
    (hF_int : Integrable (fun z => K x0 z * f x0 z * ρ x0 z) μ)
    (h_bound : ∀ᵐ z ∂μ, ∀ t ∈ U, |K t z * f' t z * ρ t z + K' t z * f t z * ρ t z +
      K t z * f t z * ρ' t z| ≤ bound z)
    (hbound : Integrable bound μ)
    (hK_diff : ∀ᵐ z ∂μ, ∀ t ∈ U, HasDerivAt (fun t => K t z) (K' t z) t)
    (hf_diff : ∀ᵐ z ∂μ, ∀ t ∈ U, HasDerivAt (fun t => f t z) (f' t z) t)
    (hρ_diff : ∀ᵐ z ∂μ, ∀ t ∈ U, HasDerivAt (fun t => ρ t z) (ρ' t z) t)
    (hKm : Measurable (K x0)) (hK'm : Measurable (K' x0)) (hfm : Measurable (f x0))
    (hdm : Measurable (f' x0)) (hρm : Measurable (ρ x0)) (hρ'm : Measurable (ρ' x0))
    (hρ0 : ∀ᵐ z ∂μ, 0 ≤ ρ x0 z) (hcdom : ∀ᵐ z ∂μ, f x0 z ∈ cdom s)
    (hKw : Integrable (fun z => K x0 z ^ 2 * statWeight s (f x0 z) * ρ x0 z) μ)
    (hJ : ∫⁻ z, ENNReal.ofReal (ρ x0 z) * fisherDens (f' x0 z) (statWeight s (f x0 z)) ∂μ ≤
      ENNReal.ofReal J)
    (hkern : Integrable (fun z => K' x0 z * f x0 z * ρ x0 z) μ)
    (henv : ∀ᵐ z ∂μ, |f x0 z| ≤ F z)
    (hI1 : Integrable (fun z => |K' x0 z| * F z * ρ x0 z) μ)
    (hI2 : Integrable (fun z => |K x0 z| * F z * |ρ' x0 z|) μ),
    |(∫ z, K x0 z * f' x0 z * ρ x0 z ∂μ) + (∫ z, K' x0 z * f x0 z * ρ x0 z ∂μ) +
        (∫ z, K x0 z * f x0 z * ρ' x0 z ∂μ)| ≤
      Real.sqrt J * Real.sqrt (∫ z, K x0 z ^ 2 * statWeight s (f x0 z) * ρ x0 z ∂μ) +
        (∫ z, |K' x0 z| * F z * ρ x0 z ∂μ) + (∫ z, |K x0 z| * F z * |ρ' x0 z| ∂μ) :=
  @G12F.general_derivative_bound_envelope

example : (∫⁻ z : Unit, ENNReal.ofReal 1 * fisherDens 1 (statWeight .BE 1) ∂(Measure.dirac ()) =
      ENNReal.ofReal (1 / 2)) ∧
    (∫ z : Unit, (1 : ℝ) ^ 2 * statWeight .BE 1 * 1 ∂(Measure.dirac ()) = 2) ∧
    HasDerivAt (fun t : ℝ => ∫ z : Unit, (1 : ℝ) * (1 + t) * 1 ∂(Measure.dirac ())) 1 0 ∧
    |(1 : ℝ)| = Real.sqrt (1 / 2) * Real.sqrt 2 :=
  G12F.sharp_witness

example : (∫ z : Unit, (1 : ℝ) ^ 2 * hess .BE 0 ∂(Measure.dirac ())) = 0 ∧
    ¬ (|∫ z : Unit, (1 : ℝ) * 1 * 1 ∂(Measure.dirac ())| ≤
        Real.sqrt 0 * Real.sqrt (∫ z : Unit, (1 : ℝ) ^ 2 * statWeight .BE 0 * 1 ∂(Measure.dirac ()))) ∧
    fisherDens 1 (statWeight .BE 0) = ⊤ :=
  G12F.junk_hess_control

example : HasDerivAt (fun t : ℝ => ∫ z : Unit, (1 : ℝ) * 1 * (1 + t) ∂(Measure.dirac ())) 1 0 ∧
    (∫⁻ z : Unit, ENNReal.ofReal 1 * fisherDens 0 (statWeight .BE 1) ∂(Measure.dirac ()) = 0) ∧
    ¬ (|(1 : ℝ)| ≤ Real.sqrt 0 *
        Real.sqrt (∫ z : Unit, (1 : ℝ) ^ 2 * statWeight .BE 1 * 1 ∂(Measure.dirac ()))) :=
  G12F.measure_term_necessary

example : HasDerivAt (fun t : ℝ => ∫ z : Unit, (1 + t) * 1 * 1 ∂(Measure.dirac ())) 1 0 ∧
    (∫⁻ z : Unit, ENNReal.ofReal 1 * fisherDens 0 (statWeight .BE 1) ∂(Measure.dirac ()) = 0) ∧
    ¬ (|(1 : ℝ)| ≤ Real.sqrt 0 *
        Real.sqrt (∫ z : Unit, (1 : ℝ) ^ 2 * statWeight .BE 1 * 1 ∂(Measure.dirac ()))) :=
  G12F.kernel_term_necessary

example : ∀ (C b : ℝ) (hC : 0 < C) (hb : 0 < b) (f : ℝ × Sphere2 → ℝ)
    (hf : Measurable f)
    (henv : ∀ z : ℝ × Sphere2, 0 < z.1 → 0 ≤ f z ∧ f z ≤ G12D.occupation b 0 z.1)
    (a c : Fin 4),
    Integrable (fun z => stressKernel a c z ^ 2 * statWeight .BE (f z) * (C * z.1 ^ 2))
      (G12D.energyAngularMeasure dOmega) ∧
    ∫ z, stressKernel a c z ^ 2 * statWeight .BE (f z) * (C * z.1 ^ 2)
        ∂(G12D.energyAngularMeasure dOmega) ≤
      ∫ z, G12D.kernelDensity b C z.1 * stressKernel a c z ^ 2 ∂(G12D.energyAngularMeasure dOmega) :=
  @G12F.stress_weighted_norm

example : ∀ (C b : ℝ) (hC : 0 < C) (hb : 0 < b) (a c : Fin 4)
    (f f' : ℝ → ℝ × Sphere2 → ℝ) (x0 J : ℝ) (bound : ℝ × Sphere2 → ℝ) (U : Set ℝ)
    (hU : U ∈ 𝓝 x0)
    (hF_meas : ∀ᶠ t in 𝓝 x0, AEStronglyMeasurable
      (fun z => stressKernel a c z * f t z * (C * z.1 ^ 2)) (G12D.energyAngularMeasure dOmega))
    (hF_int : Integrable (fun z => stressKernel a c z * f x0 z * (C * z.1 ^ 2))
      (G12D.energyAngularMeasure dOmega))
    (h_bound : ∀ᵐ z ∂(G12D.energyAngularMeasure dOmega), ∀ t ∈ U,
      |stressKernel a c z * f' t z * (C * z.1 ^ 2)| ≤ bound z)
    (hbound : Integrable bound (G12D.energyAngularMeasure dOmega))
    (h_diff : ∀ᵐ z ∂(G12D.energyAngularMeasure dOmega), ∀ t ∈ U,
      HasDerivAt (fun t => f t z) (f' t z) t)
    (hf0 : Measurable (f x0)) (hd : Measurable (f' x0))
    (henv : ∀ z : ℝ × Sphere2, 0 < z.1 → 0 ≤ f x0 z ∧ f x0 z ≤ G12D.occupation b 0 z.1)
    (hJ : ∫⁻ z, ENNReal.ofReal (C * z.1 ^ 2) * fisherDens (f' x0 z) (statWeight .BE (f x0 z))
      ∂(G12D.energyAngularMeasure dOmega) ≤ ENNReal.ofReal J),
    HasDerivAt (fun t => ∫ z, stressKernel a c z * f t z * (C * z.1 ^ 2)
        ∂(G12D.energyAngularMeasure dOmega))
      (∫ z, stressKernel a c z * f' x0 z * (C * z.1 ^ 2) ∂(G12D.energyAngularMeasure dOmega)) x0 ∧
    |∫ z, stressKernel a c z * f' x0 z * (C * z.1 ^ 2) ∂(G12D.energyAngularMeasure dOmega)| ≤
      Real.sqrt J * Real.sqrt (∫ z, stressKernel a c z ^ 2 * statWeight .BE (f x0 z) * (C * z.1 ^ 2)
        ∂(G12D.energyAngularMeasure dOmega)) ∧
    ∫ z, stressKernel a c z ^ 2 * statWeight .BE (f x0 z) * (C * z.1 ^ 2)
        ∂(G12D.energyAngularMeasure dOmega) ≤
      ∫ z, G12D.kernelDensity b C z.1 * stressKernel a c z ^ 2 ∂(G12D.energyAngularMeasure dOmega) :=
  @G12F.stress_derivative_bound

example : ∀ (C b : ℝ) (hC : 0 < C) (hb : 0 < b) (a c : Fin 4),
    ∃ J : ℝ,
      HasDerivAt (fun t => ∫ z, stressKernel a c z * ((1 + t) * G12D.occupation (2 * b) 0 z.1) *
          (C * z.1 ^ 2) ∂(G12D.energyAngularMeasure dOmega))
        (∫ z, stressKernel a c z * G12D.occupation (2 * b) 0 z.1 * (C * z.1 ^ 2)
          ∂(G12D.energyAngularMeasure dOmega)) 0 ∧
      |∫ z, stressKernel a c z * G12D.occupation (2 * b) 0 z.1 * (C * z.1 ^ 2)
          ∂(G12D.energyAngularMeasure dOmega)| ≤
        Real.sqrt J * Real.sqrt (∫ z, stressKernel a c z ^ 2 *
          statWeight .BE ((1 + 0) * G12D.occupation (2 * b) 0 z.1) * (C * z.1 ^ 2)
          ∂(G12D.energyAngularMeasure dOmega)) :=
  @G12F.stress_nonvacuity

example : ∀ (C : ℝ) (hC : 0 < C) (s : Stat) (g q : ℝ → ℝ)
    {E1 E2 : ℝ} (hgm : Measurable g) (hgc : ContinuousOn g (Icc E1 E2))
    (hgdom : ∀ E, 0 < E → g E ∈ dom s) (hq : Continuous q) (hE1 : 0 < E1)
    (hz : ∀ E ∉ Icc E1 E2, q E = 0) (hq0 : ∃ E0, q E0 ≠ 0) (a : ℝ) (ha : a ≠ 0) (J : ℝ),
    ∀ᶠ n : ℕ in atTop, ¬ (∫⁻ z, fisherDens (a * n * q z.1)
        (statWeight s (G12E.family (Ω := Sphere2) g q a n 0 z)) ∂nu C ≤ ENNReal.ofReal J) :=
  @G12F.g12e_family_violates_budget

#check @G12F.statWeight_nonneg
#check @G12F.fisherDens_of_dom
#check @G12F.weighted_cauchy_schwarz
#check @G12F.real_budget_le
#check @G12F.zero_weight_null
#check @G12F.zero_occupation_derivative
#check @G12F.parallel_derivative_bound
#check @G12F.teff_a4_derivative_bound_BE
#check @G12F.general_derivative_bound
#check @G12F.general_derivative_bound_envelope
#check @G12F.sharp_witness
#check @G12F.junk_hess_control
#check @G12F.measure_term_necessary
#check @G12F.kernel_term_necessary
#check @G12F.stress_weighted_norm
#check @G12F.stress_derivative_bound
#check @G12F.stress_nonvacuity
#check @G12F.g12e_family_violates_budget
#print axioms G12F.statWeight_nonneg
#print axioms G12F.fisherDens_of_dom
#print axioms G12F.weighted_cauchy_schwarz
#print axioms G12F.real_budget_le
#print axioms G12F.zero_weight_null
#print axioms G12F.zero_occupation_derivative
#print axioms G12F.parallel_derivative_bound
#print axioms G12F.teff_a4_derivative_bound_BE
#print axioms G12F.general_derivative_bound
#print axioms G12F.general_derivative_bound_envelope
#print axioms G12F.sharp_witness
#print axioms G12F.junk_hess_control
#print axioms G12F.measure_term_necessary
#print axioms G12F.kernel_term_necessary
#print axioms G12F.stress_weighted_norm
#print axioms G12F.stress_derivative_bound
#print axioms G12F.stress_nonvacuity
#print axioms G12F.g12e_family_violates_budget
