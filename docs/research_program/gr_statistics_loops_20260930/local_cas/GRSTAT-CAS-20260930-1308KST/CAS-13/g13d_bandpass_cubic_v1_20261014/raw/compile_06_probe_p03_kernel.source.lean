import Mathlib

open MeasureTheory Set

noncomputable section

namespace P03

def bandIntegral (K : ℝ → ℝ) (E1 E2 : ℝ) (G : ℝ × ℝ → ℝ) (y : ℝ) : ℝ :=
  ∫ E in Icc E1 E2, K E * G (y, E)

def dY (G : ℝ × ℝ → ℝ) : ℝ × ℝ → ℝ := fun p => fderiv ℝ G p (1, 0)

theorem dY_contDiffOn {G : ℝ × ℝ → ℝ} {Ω : Set (ℝ × ℝ)} {m n : WithTop ℕ∞} (hΩ : IsOpen Ω)
    (hG : ContDiffOn ℝ n G Ω) (hmn : m + 1 ≤ n) : ContDiffOn ℝ m (dY G) Ω :=
  (hG.fderiv_of_isOpen hΩ hmn).clm_apply contDiffOn_const

theorem hasDerivAt_slice {G : ℝ × ℝ → ℝ} {Ω : Set (ℝ × ℝ)} (hΩ : IsOpen Ω)
    (hG : ContDiffOn ℝ 1 G Ω) {x E : ℝ} (hp : (x, E) ∈ Ω) :
    HasDerivAt (fun t => G (t, E)) (dY G (x, E)) x := by
  have hdiff : DifferentiableAt ℝ G (x, E) :=
    (hG.differentiableOn one_ne_zero (x, E) hp).differentiableAt (hΩ.mem_nhds hp)
  have hpath : HasDerivAt (fun t : ℝ => (t, E)) ((1 : ℝ), (0 : ℝ)) x :=
    (hasDerivAt_id' x).prodMk (hasDerivAt_const x E)
  exact hdiff.hasFDerivAt.comp_hasDerivAt x hpath

theorem bandIntegral_hasDerivAt {K : ℝ → ℝ} {E1 E2 A B y : ℝ} {G : ℝ × ℝ → ℝ}
    {Ω : Set (ℝ × ℝ)} (hK : IntegrableOn K (Icc E1 E2)) (hΩ : IsOpen Ω)
    (hG : ContDiffOn ℝ 1 G Ω) (hsub : Icc A B ×ˢ Icc E1 E2 ⊆ Ω) (hy : y ∈ Ioo A B) :
    HasDerivAt (bandIntegral K E1 E2 G) (bandIntegral K E1 E2 (dY G) y) y := by
  have hScpt : IsCompact (Icc A B ×ˢ Icc E1 E2) := isCompact_Icc.prod isCompact_Icc
  have hGc : ContinuousOn G (Icc A B ×ˢ Icc E1 E2) := hG.continuousOn.mono hsub
  have hdY : ContDiffOn ℝ 0 (dY G) Ω := dY_contDiffOn hΩ hG (by norm_num)
  have hdYc : ContinuousOn (dY G) (Icc A B ×ˢ Icc E1 E2) := hdY.continuousOn.mono hsub
  obtain ⟨M, hM⟩ := hScpt.exists_bound_of_continuousOn hdYc
  have slice : ∀ {H : ℝ × ℝ → ℝ}, ContinuousOn H (Icc A B ×ˢ Icc E1 E2) →
      ∀ x ∈ Icc A B, ContinuousOn (fun E => H (x, E)) (Icc E1 E2) := by
    intro H hH x hx
    exact hH.comp (Continuous.continuousOn (by fun_prop)) (fun E hE => ⟨hx, hE⟩)
  have hIoo : Ioo A B ∈ nhds y := isOpen_Ioo.mem_nhds hy
  have hmeasK : AEStronglyMeasurable K (volume.restrict (Icc E1 E2)) := hK.aestronglyMeasurable
  have key := hasDerivAt_integral_of_dominated_loc_of_deriv_le (μ := volume.restrict (Icc E1 E2))
    (F := fun x E => K E * G (x, E)) (F' := fun x E => K E * dY G (x, E)) (x₀ := y)
    (bound := fun E => ‖K E‖ * M) hIoo
    (Filter.eventually_of_mem hIoo fun x hx => hmeasK.mul
      ((slice hGc x (Ioo_subset_Icc_self hx)).aestronglyMeasurable measurableSet_Icc))
    (hK.mul_continuousOn (slice hGc y (Ioo_subset_Icc_self hy)) isCompact_Icc)
    (hmeasK.mul ((slice hdYc y (Ioo_subset_Icc_self hy)).aestronglyMeasurable measurableSet_Icc))
    ((ae_restrict_mem measurableSet_Icc).mono fun E hE x hx => by
      rw [norm_mul]
      exact mul_le_mul_of_nonneg_left (hM (x, E) ⟨Ioo_subset_Icc_self hx, hE⟩) (norm_nonneg _))
    (hK.norm.mul_const M)
    ((ae_restrict_mem measurableSet_Icc).mono fun E hE x hx =>
      (hasDerivAt_slice hΩ hG (hsub ⟨Ioo_subset_Icc_self hx, hE⟩)).const_mul (K E))
  exact key.2

def thermalFactor (θ η0 ξ : ℝ) (p : ℝ × ℝ) : ℝ :=
  p.2 ^ 2 / (Real.exp (p.2 / (θ * p.1) - η0) - ξ)

def regDomain (θ η0 ξ : ℝ) : Set (ℝ × ℝ) :=
  {p | 0 < p.1 ∧ 0 < p.2 ∧ ξ < Real.exp (p.2 / (θ * p.1) - η0)}

theorem regDomain_isOpen {θ η0 ξ : ℝ} (hθ : 0 < θ) : IsOpen (regDomain θ η0 ξ) := by
  have hs : IsOpen {p : ℝ × ℝ | 0 < p.1 ∧ 0 < p.2} :=
    (isOpen_lt continuous_const continuous_fst).inter (isOpen_lt continuous_const continuous_snd)
  have hc : ContinuousOn (fun p : ℝ × ℝ => Real.exp (p.2 / (θ * p.1) - η0))
      {p : ℝ × ℝ | 0 < p.1 ∧ 0 < p.2} := by
    apply ContinuousOn.rexp
    apply ContinuousOn.sub _ continuousOn_const
    apply ContinuousOn.div continuous_snd.continuousOn
      (continuous_const.mul continuous_fst).continuousOn
    intro p hp
    exact mul_ne_zero hθ.ne' hp.1.ne'
  have := hc.isOpen_inter_preimage hs (isOpen_Ioi (a := ξ))
  convert this using 1
  ext p
  simp [regDomain, and_assoc]

theorem thermalFactor_contDiffOn {θ η0 ξ : ℝ} (hθ : 0 < θ) :
    ContDiffOn ℝ 4 (thermalFactor θ η0 ξ) (regDomain θ η0 ξ) := by
  have hnum : ContDiffOn ℝ 4 (fun p : ℝ × ℝ => p.2 ^ 2) (regDomain θ η0 ξ) :=
    (contDiff_snd.pow 2).contDiffOn
  have harg : ContDiffOn ℝ 4 (fun p : ℝ × ℝ => p.2 / (θ * p.1)) (regDomain θ η0 ξ) :=
    contDiff_snd.contDiffOn.div (contDiff_const.mul contDiff_fst).contDiffOn
      (fun p hp => mul_ne_zero hθ.ne' hp.1.ne')
  have hden : ContDiffOn ℝ 4 (fun p : ℝ × ℝ => Real.exp (p.2 / (θ * p.1) - η0) - ξ)
      (regDomain θ η0 ξ) :=
    (Real.contDiff_exp.comp_contDiffOn (harg.sub contDiffOn_const)).sub contDiffOn_const
  exact hnum.div hden (fun p hp => (sub_pos.mpr hp.2.2).ne')

end P03
