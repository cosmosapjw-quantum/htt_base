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

#print axioms C01_coordinate_riemann_from_metric

end
end CAS06Bundles
