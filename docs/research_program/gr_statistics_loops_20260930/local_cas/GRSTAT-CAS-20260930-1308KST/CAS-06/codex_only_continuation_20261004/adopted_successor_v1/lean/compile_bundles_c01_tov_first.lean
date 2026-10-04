import C03Action

/-! Complete finite target declarations assembled from the independently derived
metric and action facts.  Each field retains its coordinate/frame and local
domain, so a compiled aggregate cannot hide a component by abbreviation. -/

namespace CAS06Bundles
noncomputable section
open scoped Topology

def C01CoordinateRiemann (ν F : ℝ → ℝ) (r θ νrr Frr : ℝ) : Prop :=
  let R := CAS06Adopted.chartRiemannCovActual ν F r θ
  R 0 1 0 1 = Real.exp (2 * ν r) *
      (νrr + (deriv ν r) ^ 2 + deriv ν r * deriv F r / (2 * F r)) ∧
  R 0 2 0 2 = Real.exp (2 * ν r) * F r * deriv ν r * r ∧
  R 0 3 0 3 = Real.exp (2 * ν r) * F r * deriv ν r * r * Real.sin θ ^ 2 ∧
  R 1 2 1 2 = -(deriv F r) * r / (2 * F r) ∧
  R 1 3 1 3 = -(deriv F r) * r * Real.sin θ ^ 2 / (2 * F r) ∧
  R 2 3 2 3 = r ^ 2 * (1 - F r) * Real.sin θ ^ 2 ∧
  (∀ a b c d : Fin 4, ¬CAS06Adopted.SameIndexPair a b c d →
    R a b c d = 0)

theorem C01_coordinate_riemann_from_metric
    {ν F : ℝ → ℝ} {r θ νrr Frr : ℝ}
    (hr : 0 < r) (hF : 0 < F r)
    (hθpos : 0 < θ) (hθlt : θ < Real.pi)
    (hνdiff : DifferentiableAt ℝ ν r)
    (hFdiff : DifferentiableAt ℝ F r)
    (hνrr : HasDerivAt (deriv ν) νrr r)
    (hFrr : HasDerivAt (deriv F) Frr r) :
    C01CoordinateRiemann ν F r θ νrr Frr := by
  have hs : Real.sin θ ≠ 0 :=
    (Real.sin_pos_of_pos_of_lt_pi hθpos hθlt).ne'
  have hj (a b c d : Fin 4) :=
    CAS06Adopted.chartRiemannCovActual_eq_jet hνdiff hFdiff hνrr hFrr
      hF.ne' hr.ne' hs a b c d
  unfold C01CoordinateRiemann
  refine ⟨?_, ?_, ?_, ?_, ?_, ?_, ?_⟩
  · rw [hj 0 1 0 1]
    exact CAS06Adopted.chartRiemannCovJet_0101 _ _ _ _ _ _ _ _
      hF.ne' hr.ne' hs
  · rw [hj 0 2 0 2]
    exact CAS06Adopted.chartRiemannCovJet_0202 _ _ _ _ _ _ _ _
      hF.ne' hr.ne' hs
  · rw [hj 0 3 0 3]
    exact CAS06Adopted.chartRiemannCovJet_0303 _ _ _ _ _ _ _ _
      hF.ne' hr.ne' hs
  · rw [hj 1 2 1 2]
    exact CAS06Adopted.chartRiemannCovJet_1212 _ _ _ _ _ _ _ _
      hF.ne' hr.ne' hs
  · rw [hj 1 3 1 3]
    exact CAS06Adopted.chartRiemannCovJet_1313 _ _ _ _ _ _ _ _
      hF.ne' hr.ne' hs
  · rw [hj 2 3 2 3]
    exact CAS06Adopted.chartRiemannCovJet_2323 _ _ _ _ _ _ _ _
      hF.ne' hr.ne' hs
  · intro a b c d hm
    rw [hj a b c d]
    exact CAS06Adopted.chartRiemannCovJet_mixed_zero
      _ _ _ _ _ _ _ _ hF.ne' hr.ne' hs a b c d hm

def C01TOVNuSecond (m ε : ℝ → ℝ) (κ Λ α r : ℝ) : ℝ :=
  CAS06Adopted.tovNuSecondJet (m r) (κ * r ^ 2 * ε r / 2) κ (α * ε r)
    (-(ε r + α * ε r) *
      CAS06Adopted.tovNuFunction m (fun s => α * ε s)
        (CAS06Adopted.massLapse m Λ) κ Λ r)
    Λ (CAS06Adopted.massLapse m Λ r)
    (CAS06Adopted.massLapseJet (m r) (κ * r ^ 2 * ε r / 2) Λ r) r

def C01TOVEinstein (ν m ε : ℝ → ℝ) (κ Λ α r θ : ℝ) : Prop :=
  let E := CAS06Adopted.chartEinsteinFromMetric ν (CAS06Adopted.massLapse m Λ)
    (deriv ν) (deriv (CAS06Adopted.massLapse m Λ)) r θ
  (Real.exp (2 * ν r))⁻¹ * E 0 0 - Λ = κ * ε r ∧
  CAS06Adopted.massLapse m Λ r * E 1 1 + Λ = κ * α * ε r ∧
  (r ^ 2)⁻¹ * E 2 2 + Λ = κ * α * ε r ∧
  (r ^ 2 * Real.sin θ ^ 2)⁻¹ * E 3 3 + Λ = κ * α * ε r ∧
  (∀ b d : Fin 4, b ≠ d → E b d = 0)

theorem C01_TOV_metric_bundle
    {ν m ε : ℝ → ℝ} {κ Λ α r θ Frr : ℝ}
    (hr : 0 < r) (hF : 0 < CAS06Adopted.massLapse m Λ r)
    (hεpos : 0 < ε r) (hα : 0 < α)
    (hθpos : 0 < θ) (hθlt : θ < Real.pi)
    (hm : HasDerivAt m (κ * r ^ 2 * ε r / 2) r)
    (hε : HasDerivAt ε
      (-(1 + α) * ε r *
        CAS06Adopted.tovNuFunction m (fun s => α * ε s)
          (CAS06Adopted.massLapse m Λ) κ Λ r / α) r)
    (hν : HasDerivAt ν
      (CAS06Adopted.tovNuFunction m (fun s => α * ε s)
        (CAS06Adopted.massLapse m Λ) κ Λ r) r)
    (hνnear : deriv ν =ᶠ[𝓝 r]
      CAS06Adopted.tovNuFunction m (fun s => α * ε s)
        (CAS06Adopted.massLapse m Λ) κ Λ)
    (hFrr : HasDerivAt (deriv (CAS06Adopted.massLapse m Λ)) Frr r) :
    C01CoordinateRiemann ν (CAS06Adopted.massLapse m Λ) r θ
      (C01TOVNuSecond m ε κ Λ α r) Frr ∧
    C01TOVEinstein ν m ε κ Λ α r θ ∧
    (∀ a b : Fin 4,
      ∑ d : Fin 4,
        CAS06Adopted.chartInverse (ν r) (CAS06Adopted.massLapse m Λ r)
          r θ a d *
        CAS06Adopted.chartMetric (ν r) (CAS06Adopted.massLapse m Λ r)
          r θ d b = if a = b then 1 else 0) ∧
    (∀ dir a b : Fin 4,
      HasDerivAt
        (CAS06Adopted.chartMetricCoordinateLine ν (CAS06Adopted.massLapse m Λ)
          r θ dir a b)
        (CAS06Adopted.chartPartial (ν r) (CAS06Adopted.massLapse m Λ r)
          (deriv ν r) (deriv (CAS06Adopted.massLapse m Λ) r)
          r θ dir a b)
        (CAS06Adopted.chartBaseCoordinate dir r θ)) ∧
    (∀ a b c : Fin 4,
      CAS06Adopted.chartGamma (ν r) (CAS06Adopted.massLapse m Λ r)
        (deriv ν r) (deriv (CAS06Adopted.massLapse m Λ) r)
        r θ a b c =
      CAS06Adopted.chartGammaTable (ν r) (CAS06Adopted.massLapse m Λ r)
        (deriv ν r) (deriv (CAS06Adopted.massLapse m Λ) r)
        r θ a b c) := by
  have hs : Real.sin θ ≠ 0 :=
    (Real.sin_pos_of_pos_of_lt_pi hθpos hθlt).ne'
  have hp := CAS06Adopted.tov_pressure_derivative_from_epsilon hα hε
  have hFder := CAS06Adopted.massLapse_derivative (Λ := Λ) hr.ne' hm
  have hνrr := CAS06Adopted.local_tov_second_derivative
    hνnear hm hp hFder hr.ne' hF.ne'
  have hνrr' : HasDerivAt (deriv ν) (C01TOVNuSecond m ε κ Λ α r) r := by
    simpa only [C01TOVNuSecond] using hνrr
  refine ⟨?_, ?_, ?_, ?_, ?_⟩
  · exact C01_coordinate_riemann_from_metric hr hF hθpos hθlt
      hν.differentiableAt hFder.differentiableAt hνrr' hFrr
  · exact CAS06Adopted.tov_three_ode_actual_metric_einstein_components
      hr hF hεpos hα hθpos hθlt hm hε hν hνnear hFrr
  · exact CAS06Adopted.chartInverse_left_identity _ _ _ _
      hF.ne' hr.ne' hs
  · simpa only [hν.deriv, hFder.deriv] using
      CAS06Adopted.chartPartial_from_actual_metric hν hFder hF.ne'
  · exact CAS06Adopted.chartGamma_table _ _ _ _ _ _
      hF.ne' hr.ne' hs

#print axioms C01_coordinate_riemann_from_metric
#print axioms C01_TOV_metric_bundle

end
end CAS06Bundles
