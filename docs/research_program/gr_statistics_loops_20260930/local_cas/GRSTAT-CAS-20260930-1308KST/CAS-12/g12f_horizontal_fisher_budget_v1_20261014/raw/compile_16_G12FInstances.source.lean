import Mathlib
import G12ECounterexample
import G12FFisherBudget

/-!
# G12-F instances: stress kernels on dν = C E² dE dΩ, non-vacuity, consistency with G12-E

Targets frozen in `../FROZEN_TARGETS.md` (T11–T14).

* `stressKernel a c (E, e) = n^a n^c E`, `n = (1, e)`: massless kinetic stress
  `T^{ac} = ∫ K^{ac} f dν` relative to `dν = C E² dE dΩ` (constant absorbed in `C`).
* T11: under the BE envelope `0 ≤ f ≤ F_b` its weighted norm `∫ K² f(1+f) dν` is finite and
  bounded by the envelope-only quantity `∫ C E² W_b K²` (reviewed G12-D lemmas).
* T12: final typed stress-derivative bound in the parallel construction (T5 + T11).
* T13: non-vacuity of T12 on the photon envelope (`f_t = (1+t) F_{2b}`).
* T14: the positive bound and the G12-E no-go are consistent: the G12-E family violates every
  finite budget for large `n`.

The carrier is `G12D.energyAngularMeasure G11A.dOmega` with explicit density `C E²`; its
identification with `G11A.nu C` is not claimed.  Reviewed imports are unchanged.
Scientific admission is not claimed.
-/

open MeasureTheory Set Filter Topology
open scoped ENNReal

noncomputable section

namespace G12F

open G11A

/-! ## Definitions -/

/-- Null tetrad direction `n = (1, e)`. -/
def nvec (e : Sphere2) : Fin 4 → ℝ :=
  ![1, (e : EuclideanSpace ℝ (Fin 3)) 0, (e : EuclideanSpace ℝ (Fin 3)) 1,
    (e : EuclideanSpace ℝ (Fin 3)) 2]

/-- Massless stress kernel `K^{ac}(E, e) = n^a n^c E` relative to `dν = C E² dE dΩ`. -/
def stressKernel (a c : Fin 4) (z : ℝ × Sphere2) : ℝ := (nvec z.2 a * nvec z.2 c) * z.1

/-- Dominating function used for the non-vacuity instance (auxiliary). -/
def nvBound (b C : ℝ) (z : ℝ × Sphere2) : ℝ := G12D.kernelDensity b C z.1 * (1 + z.1 ^ 2)

/-! ## Auxiliary lemmas -/

theorem abs_coord_le_one (e : Sphere2) (k : Fin 3) :
    |(e : EuclideanSpace ℝ (Fin 3)) k| ≤ 1 := by
  have h1 : ‖(e : EuclideanSpace ℝ (Fin 3))‖ = 1 := by simp
  have := PiLp.norm_apply_le (e : EuclideanSpace ℝ (Fin 3)) k
  rw [Real.norm_eq_abs] at this
  linarith

theorem abs_nvec_le_one (e : Sphere2) (a : Fin 4) : |nvec e a| ≤ 1 := by
  fin_cases a
  · simp [nvec]
  · simpa [nvec] using abs_coord_le_one e 0
  · simpa [nvec] using abs_coord_le_one e 1
  · simpa [nvec] using abs_coord_le_one e 2

theorem continuous_nvec (a : Fin 4) : Continuous (fun e : Sphere2 => nvec e a) := by
  fin_cases a <;> simp [nvec] <;> fun_prop

theorem measurable_stressKernel (a c : Fin 4) : Measurable (stressKernel a c) := by
  have h : Continuous (fun z : ℝ × Sphere2 => (nvec z.2 a * nvec z.2 c) * z.1) :=
    (((continuous_nvec a).comp continuous_snd).mul
      ((continuous_nvec c).comp continuous_snd)).mul continuous_fst
  exact h.measurable

theorem abs_angular_le_one (e : Sphere2) (a c : Fin 4) : |nvec e a * nvec e c| ≤ 1 := by
  rw [abs_mul]
  have := mul_le_mul (abs_nvec_le_one e a) (abs_nvec_le_one e c) (abs_nonneg _) zero_le_one
  simpa using this

theorem abs_stressKernel_le (a c : Fin 4) (z : ℝ × Sphere2) (hz : 0 < z.1) :
    |stressKernel a c z| ≤ z.1 := by
  rw [stressKernel, abs_mul, abs_of_pos hz]
  calc |nvec z.2 a * nvec z.2 c| * z.1 ≤ 1 * z.1 :=
        mul_le_mul_of_nonneg_right (abs_angular_le_one z.2 a c) hz.le
    _ = z.1 := one_mul _

theorem ae_energy_pos :
    ∀ᵐ z ∂(G12D.energyAngularMeasure dOmega), 0 < (z : ℝ × Sphere2).1 := by
  rw [ae_iff]
  have h := (G12DClosure.no_nonpositive_energy_mass dOmega (1 : ℝ) 1).1
  simpa [not_lt] using h

theorem stress_kernelDensity_integrable (C b : ℝ) (hC : 0 < C) (hb : 0 < b) (a c : Fin 4) :
    Integrable (fun z => G12D.kernelDensity b C z.1 * stressKernel a c z ^ 2)
      (G12D.energyAngularMeasure dOmega) := by
  have h := (G12DClosure.angular_bounded_rpow_kernel_integrable dOmega b C 1 1
    (fun ω => nvec ω a * nvec ω c) hb hC zero_le_one zero_le_one
    ((continuous_nvec a).mul (continuous_nvec c)).aestronglyMeasurable
    (ae_of_all _ fun ω => abs_angular_le_one ω a c)).1
  refine h.congr (ae_of_all _ fun z => ?_)
  simp only [stressKernel, Real.rpow_one]

theorem kernelDensity_integrable (C b : ℝ) (hC : 0 < C) (hb : 0 < b) :
    Integrable (fun z : ℝ × Sphere2 => G12D.kernelDensity b C z.1)
      (G12D.energyAngularMeasure dOmega) := by
  have h := (G12DClosure.angular_bounded_rpow_kernel_integrable dOmega b C 1 0
    (fun _ => (1 : ℝ)) hb hC zero_le_one le_rfl aestronglyMeasurable_const
    (ae_of_all _ fun _ => by norm_num)).1
  refine h.congr (ae_of_all _ fun z => ?_)
  simp only [Real.rpow_zero, mul_one, one_pow]

/-! ## T11: finite weighted norm of every stress kernel under the BE envelope -/

theorem stress_weighted_norm (C b : ℝ) (hC : 0 < C) (hb : 0 < b) (f : ℝ × Sphere2 → ℝ)
    (hf : Measurable f)
    (henv : ∀ z : ℝ × Sphere2, 0 < z.1 → 0 ≤ f z ∧ f z ≤ G12D.occupation b 0 z.1)
    (a c : Fin 4) :
    Integrable (fun z => stressKernel a c z ^ 2 * statWeight .BE (f z) * (C * z.1 ^ 2))
      (G12D.energyAngularMeasure dOmega) ∧
    ∫ z, stressKernel a c z ^ 2 * statWeight .BE (f z) * (C * z.1 ^ 2)
        ∂(G12D.energyAngularMeasure dOmega) ≤
      ∫ z, G12D.kernelDensity b C z.1 * stressKernel a c z ^ 2
        ∂(G12D.energyAngularMeasure dOmega) := by
  have hKD := stress_kernelDensity_integrable C b hC hb a c
  have hdom : ∀ᵐ z ∂(G12D.energyAngularMeasure dOmega),
      ‖stressKernel a c z ^ 2 * statWeight .BE (f z) * (C * z.1 ^ 2)‖ ≤
        G12D.kernelDensity b C z.1 * stressKernel a c z ^ 2 := by
    filter_upwards [ae_energy_pos] with z hz
    obtain ⟨h0, hF⟩ := henv z hz
    have hW : statWeight .BE (f z) ≤ CAS12PlanckIR.weight b z.1 := by
      have := G12DClosure.between_states_weight_bound b z.1 (f z) (f z) (f z) hb hz h0 hF h0 hF
        (min_le_left _ _) (le_max_left _ _)
      simpa [statWeight, xi] using this
    have hsw : 0 ≤ statWeight .BE (f z) := statWeight_nonneg .BE (by simpa [cdom] using h0)
    have hE2 : 0 ≤ C * z.1 ^ 2 := mul_nonneg hC.le (sq_nonneg _)
    rw [Real.norm_eq_abs, abs_of_nonneg (mul_nonneg (mul_nonneg (sq_nonneg _) hsw) hE2)]
    unfold G12D.kernelDensity
    calc stressKernel a c z ^ 2 * statWeight .BE (f z) * (C * z.1 ^ 2)
        ≤ stressKernel a c z ^ 2 * CAS12PlanckIR.weight b z.1 * (C * z.1 ^ 2) :=
          mul_le_mul_of_nonneg_right (mul_le_mul_of_nonneg_left hW (sq_nonneg _)) hE2
      _ = C * z.1 ^ 2 * CAS12PlanckIR.weight b z.1 * stressKernel a c z ^ 2 := by ring
  have hsw : Measurable (fun z => statWeight .BE (f z)) := by
    show Measurable (fun z => f z * (1 + xi .BE * f z))
    exact hf.mul (measurable_const.add (measurable_const.mul hf))
  have hmeas : AEStronglyMeasurable
      (fun z => stressKernel a c z ^ 2 * statWeight .BE (f z) * (C * z.1 ^ 2))
      (G12D.energyAngularMeasure dOmega) :=
    ((((measurable_stressKernel a c).pow_const 2).mul hsw).mul
      (measurable_const.mul (measurable_fst.pow_const 2))).aestronglyMeasurable
  have hint := Integrable.mono' hKD hmeas hdom
  refine ⟨hint, integral_mono_ae hint hKD ?_⟩
  filter_upwards [hdom] with z hz
  rw [Real.norm_eq_abs] at hz
  exact le_trans (le_abs_self _) hz

/-! ## T12: stress-derivative bound (parallel construction, fixed dν and stress kernel) -/

theorem stress_derivative_bound (C b : ℝ) (hC : 0 < C) (hb : 0 < b) (a c : Fin 4)
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
      ∂(G12D.energyAngularMeasure dOmega) ≤ ENNReal.ofReal J) :
    HasDerivAt (fun t => ∫ z, stressKernel a c z * f t z * (C * z.1 ^ 2)
        ∂(G12D.energyAngularMeasure dOmega))
      (∫ z, stressKernel a c z * f' x0 z * (C * z.1 ^ 2) ∂(G12D.energyAngularMeasure dOmega)) x0 ∧
    |∫ z, stressKernel a c z * f' x0 z * (C * z.1 ^ 2) ∂(G12D.energyAngularMeasure dOmega)| ≤
      Real.sqrt J * Real.sqrt (∫ z, stressKernel a c z ^ 2 * statWeight .BE (f x0 z) *
        (C * z.1 ^ 2) ∂(G12D.energyAngularMeasure dOmega)) ∧
    ∫ z, stressKernel a c z ^ 2 * statWeight .BE (f x0 z) * (C * z.1 ^ 2)
        ∂(G12D.energyAngularMeasure dOmega) ≤
      ∫ z, G12D.kernelDensity b C z.1 * stressKernel a c z ^ 2
        ∂(G12D.energyAngularMeasure dOmega) := by
  have hcdom : ∀ᵐ z ∂(G12D.energyAngularMeasure dOmega), f x0 z ∈ cdom .BE := by
    filter_upwards [ae_energy_pos] with z hz
    simpa [cdom] using (henv z hz).1
  have hT11 := stress_weighted_norm C b hC hb (f x0) hf0 henv a c
  have h := parallel_derivative_bound (G12D.energyAngularMeasure dOmega) .BE (stressKernel a c)
    (fun z => C * z.1 ^ 2) f f' x0 J bound U hU hF_meas hF_int h_bound hbound h_diff
    (measurable_stressKernel a c) (measurable_const.mul (measurable_fst.pow_const 2)) hf0 hd
    (ae_of_all _ fun z => mul_nonneg hC.le (sq_nonneg _)) hcdom hT11.1 hJ
  exact ⟨h.1, h.2, hT11.2⟩

/-! ## T13: non-vacuity of T12 on the photon envelope -/

theorem stress_nonvacuity (C b : ℝ) (hC : 0 < C) (hb : 0 < b) (a c : Fin 4) :
    ∃ J : ℝ,
      HasDerivAt (fun t => ∫ z, stressKernel a c z * ((1 + t) * G12D.occupation (2 * b) 0 z.1) *
          (C * z.1 ^ 2) ∂(G12D.energyAngularMeasure dOmega))
        (∫ z, stressKernel a c z * G12D.occupation (2 * b) 0 z.1 * (C * z.1 ^ 2)
          ∂(G12D.energyAngularMeasure dOmega)) 0 ∧
      |∫ z, stressKernel a c z * G12D.occupation (2 * b) 0 z.1 * (C * z.1 ^ 2)
          ∂(G12D.energyAngularMeasure dOmega)| ≤
        Real.sqrt J * Real.sqrt (∫ z, stressKernel a c z ^ 2 *
          statWeight .BE ((1 + 0) * G12D.occupation (2 * b) 0 z.1) * (C * z.1 ^ 2)
          ∂(G12D.energyAngularMeasure dOmega)) := by
  have hb2 : b ≤ 2 * b := by linarith
  have hocc_meas : Measurable (fun E : ℝ => G12D.occupation (2 * b) 0 E) := by
    unfold G12D.occupation; fun_prop
  have henvF : ∀ E, 0 < E → 0 ≤ G12D.occupation (2 * b) 0 E ∧
      G12D.occupation (2 * b) 0 E ≤ G12D.occupation b 0 E :=
    fun E hE => G12D.occupation_envelope (2 * b) 0 b E hb2 hb le_rfl hE
  have hFW : ∀ E, 0 < E → G12D.occupation (2 * b) 0 E ≤ CAS12PlanckIR.weight b E := by
    intro E hE
    obtain ⟨h0, h1⟩ := henvF E hE
    have h0b : 0 ≤ G12D.occupation b 0 E := le_trans h0 h1
    rw [G12D.weight_eq_occupation b E hb hE]
    nlinarith
  have hpos2 : ∀ E, 0 < E → 0 < G12D.occupation (2 * b) 0 E := by
    intro E hE
    unfold G12D.occupation
    exact inv_pos.2 (G12DClosure.occupation_denominator_pos (2 * b) 0 E (by linarith) le_rfl hE)
  have hbnd : Integrable (nvBound b C) (G12D.energyAngularMeasure dOmega) := by
    have h0 := (G12DClosure.angular_bounded_rpow_kernel_integrable dOmega b C 1 0
      (fun _ => (1 : ℝ)) hb hC zero_le_one le_rfl aestronglyMeasurable_const
      (ae_of_all _ fun _ => by norm_num)).1
    have h1 := (G12DClosure.angular_bounded_rpow_kernel_integrable dOmega b C 1 1
      (fun _ => (1 : ℝ)) hb hC zero_le_one zero_le_one aestronglyMeasurable_const
      (ae_of_all _ fun _ => by norm_num)).1
    refine (h0.add h1).congr (ae_of_all _ fun z => ?_)
    simp only [Pi.add_apply, Real.rpow_zero, Real.rpow_one, nvBound]
    ring
  have hkey : ∀ᵐ z ∂(G12D.energyAngularMeasure dOmega),
      |stressKernel a c z * G12D.occupation (2 * b) 0 z.1 * (C * z.1 ^ 2)| ≤ nvBound b C z := by
    filter_upwards [ae_energy_pos] with z hz
    have hK := abs_stressKernel_le a c z hz
    have h0 := (henvF z.1 hz).1
    have hW := hFW z.1 hz
    have hWnn : 0 ≤ CAS12PlanckIR.weight b z.1 := le_trans h0 hW
    have hE2 : 0 ≤ C * z.1 ^ 2 := mul_nonneg hC.le (sq_nonneg _)
    rw [abs_mul, abs_mul, abs_of_nonneg h0, abs_of_nonneg hE2]
    have hE : z.1 ≤ 1 + z.1 ^ 2 := by nlinarith [sq_nonneg (z.1 - 1)]
    unfold nvBound G12D.kernelDensity
    calc |stressKernel a c z| * G12D.occupation (2 * b) 0 z.1 * (C * z.1 ^ 2)
        ≤ z.1 * CAS12PlanckIR.weight b z.1 * (C * z.1 ^ 2) :=
          mul_le_mul_of_nonneg_right (mul_le_mul hK hW h0 hz.le) hE2
      _ ≤ (1 + z.1 ^ 2) * CAS12PlanckIR.weight b z.1 * (C * z.1 ^ 2) :=
          mul_le_mul_of_nonneg_right (mul_le_mul_of_nonneg_right hE hWnn) hE2
      _ = C * z.1 ^ 2 * CAS12PlanckIR.weight b z.1 * (1 + z.1 ^ 2) := by ring
  have hfis : ∀ᵐ z ∂(G12D.energyAngularMeasure dOmega),
      ENNReal.ofReal (C * z.1 ^ 2) * fisherDens (G12D.occupation (2 * b) 0 z.1)
        (statWeight .BE ((1 + 0) * G12D.occupation (2 * b) 0 z.1)) ≤
      ENNReal.ofReal (G12D.kernelDensity b C z.1) := by
    filter_upwards [ae_energy_pos] with z hz
    have hp := hpos2 z.1 hz
    have hW := hFW z.1 hz
    have hsw : statWeight .BE ((1 + 0) * G12D.occupation (2 * b) 0 z.1) =
        G12D.occupation (2 * b) 0 z.1 * (1 + G12D.occupation (2 * b) 0 z.1) := by
      simp [statWeight, xi]
    have hswpos : 0 < G12D.occupation (2 * b) 0 z.1 * (1 + G12D.occupation (2 * b) 0 z.1) :=
      mul_pos hp (by linarith)
    rw [hsw, fisherDens, if_pos hswpos, ← ENNReal.ofReal_mul (mul_nonneg hC.le (sq_nonneg _))]
    apply ENNReal.ofReal_le_ofReal
    unfold G12D.kernelDensity
    have h1 : G12D.occupation (2 * b) 0 z.1 ^ 2 /
        (G12D.occupation (2 * b) 0 z.1 * (1 + G12D.occupation (2 * b) 0 z.1)) ≤
        G12D.occupation (2 * b) 0 z.1 := by
      rw [div_le_iff₀ hswpos]
      nlinarith
    exact mul_le_mul_of_nonneg_left (le_trans h1 hW) (mul_nonneg hC.le (sq_nonneg _))
  have hlt : ∫⁻ z, ENNReal.ofReal (C * z.1 ^ 2) * fisherDens (G12D.occupation (2 * b) 0 z.1)
      (statWeight .BE ((1 + 0) * G12D.occupation (2 * b) 0 z.1))
      ∂(G12D.energyAngularMeasure dOmega) < ⊤ :=
    lt_of_le_of_lt (lintegral_mono_ae hfis) (kernelDensity_integrable C b hC hb).lintegral_lt_top
  have hmeasK : Measurable (fun z : ℝ × Sphere2 =>
      stressKernel a c z * G12D.occupation (2 * b) 0 z.1 * (C * z.1 ^ 2)) :=
    ((measurable_stressKernel a c).mul (hocc_meas.comp measurable_fst)).mul
      (measurable_const.mul (measurable_fst.pow_const 2))
  have hF_int : Integrable (fun z : ℝ × Sphere2 =>
      stressKernel a c z * ((1 + 0) * G12D.occupation (2 * b) 0 z.1) * (C * z.1 ^ 2))
      (G12D.energyAngularMeasure dOmega) := by
    have h := Integrable.mono' hbnd hmeasK.aestronglyMeasurable
      (by filter_upwards [hkey] with z hz; rw [Real.norm_eq_abs]; exact hz)
    refine h.congr (ae_of_all _ fun z => ?_)
    simp only [zero_add, one_mul]
  refine ⟨(∫⁻ z, ENNReal.ofReal (C * z.1 ^ 2) * fisherDens (G12D.occupation (2 * b) 0 z.1)
      (statWeight .BE ((1 + 0) * G12D.occupation (2 * b) 0 z.1))
      ∂(G12D.energyAngularMeasure dOmega)).toReal, ?_⟩
  have hmain := stress_derivative_bound C b hC hb a c
    (fun t z => (1 + t) * G12D.occupation (2 * b) 0 z.1)
    (fun _ z => G12D.occupation (2 * b) 0 z.1) 0 _ (nvBound b C) Set.univ Filter.univ_mem
    (Eventually.of_forall fun t =>
      (((measurable_stressKernel a c).mul
        (measurable_const.mul (hocc_meas.comp measurable_fst))).mul
        (measurable_const.mul (measurable_fst.pow_const 2))).aestronglyMeasurable)
    hF_int
    (by filter_upwards [hkey] with z hz t _; exact hz)
    hbnd
    (ae_of_all _ fun z t _ => by
      simpa using ((hasDerivAt_id t).const_add 1).mul_const (G12D.occupation (2 * b) 0 z.1))
    (measurable_const.mul (hocc_meas.comp measurable_fst))
    (hocc_meas.comp measurable_fst)
    (fun z hz => by simpa using henvF z.1 hz)
    (le_of_eq (ENNReal.ofReal_toReal hlt.ne).symm)
  exact ⟨hmain.1, hmain.2.1⟩

/-! ## T14: consistency with the G12-E no-go -/

theorem g12e_family_violates_budget (C : ℝ) (hC : 0 < C) (s : Stat) (g q : ℝ → ℝ)
    {E1 E2 : ℝ} (hgm : Measurable g) (hgc : ContinuousOn g (Icc E1 E2))
    (hgdom : ∀ E, 0 < E → g E ∈ dom s) (hq : Continuous q) (hE1 : 0 < E1)
    (hz : ∀ E ∉ Icc E1 E2, q E = 0) (hq0 : ∃ E0, q E0 ≠ 0) (a : ℝ) (ha : a ≠ 0) (J : ℝ) :
    ∀ᶠ n : ℕ in atTop, ¬ (∫⁻ z, fisherDens (a * n * q z.1)
        (statWeight s (G12E.family (Ω := Sphere2) g q a n 0 z)) ∂nu C ≤ ENNReal.ofReal J) := by
  have hT := G12E.fisher_unbounded C hC s g q hgm hgc hgdom hq hE1 hz hq0 a ha
  have hpos : ∀ᵐ z ∂nu C, 0 < (z : ℝ × Sphere2).1 := by
    rw [ae_iff]
    simpa [not_lt] using (G12E.nu_facts C).1
  filter_upwards [hT.eventually_gt_atTop (max J 0)] with n hn
  intro hbud
  have hdomz : ∀ᵐ z ∂nu C, G12E.family (Ω := Sphere2) g q a n 0 z ∈ dom s := by
    filter_upwards [hpos] with z hz
    simpa [G12E.family] using hgdom z.1 hz
  have hle : ∫⁻ z, ENNReal.ofReal ((a * n * q z.1) ^ 2 *
      hess s (G12E.family (Ω := Sphere2) g q a n 0 z)) ∂nu C ≤ ENNReal.ofReal J := by
    calc ∫⁻ z, ENNReal.ofReal ((a * n * q z.1) ^ 2 *
          hess s (G12E.family (Ω := Sphere2) g q a n 0 z)) ∂nu C
        = ∫⁻ z, fisherDens (a * n * q z.1)
            (statWeight s (G12E.family (Ω := Sphere2) g q a n 0 z)) ∂nu C := by
          apply lintegral_congr_ae
          filter_upwards [hdomz] with z hz
          rw [fisherDens_of_dom s hz]
      _ ≤ ENNReal.ofReal J := hbud
  have hnn : 0 ≤ᵐ[nu C] (fun z => (a * n * q z.1) ^ 2 *
      hess s (G12E.family (Ω := Sphere2) g q a n 0 z)) := by
    filter_upwards [hdomz] with z hz
    obtain ⟨h1, h2⟩ := dom_pos s hz
    have hh : 0 ≤ hess s (G12E.family (Ω := Sphere2) g q a n 0 z) := by
      rw [hess]; exact le_of_lt (one_div_pos.2 (mul_pos h1 h2))
    exact mul_nonneg (sq_nonneg _) hh
  by_cases hint : Integrable (fun z => (a * n * q z.1) ^ 2 *
      hess s (G12E.family (Ω := Sphere2) g q a n 0 z)) (nu C)
  · rw [← ofReal_integral_eq_lintegral_ofReal hint hnn] at hle
    rcases ENNReal.ofReal_le_ofReal_iff'.1 hle with h | h
    · exact absurd hn (not_lt.2 (le_trans h (le_max_left _ _)))
    · exact absurd hn (not_lt.2 (le_trans h (le_max_right _ _)))
  · rw [integral_undef hint] at hn
    exact absurd hn (not_lt.2 (le_max_right _ _))

end G12F
