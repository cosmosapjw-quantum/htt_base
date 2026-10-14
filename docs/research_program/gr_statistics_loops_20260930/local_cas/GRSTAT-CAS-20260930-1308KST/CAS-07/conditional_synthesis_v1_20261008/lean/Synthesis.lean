import CAS07M02Accepted
import CAS07M06Accepted

noncomputable section
namespace CAS07Synthesis

/-- Exactly the scalar witnesses required by the published M02 theorem. -/
structure ScalarPremises (L M2 : ℝ) where
  Z : ℝ → ℝ
  Z1 : ℝ → ℝ
  Z2 : ℝ → ℝ
  deriv_Z : ∀ r ∈ Set.Icc 0 L, HasDerivAt Z (Z1 r) r
  deriv_Z1 : ∀ r ∈ Set.Icc 0 L, HasDerivAt Z1 (Z2 r) r
  continuous_Z2 : ContinuousOn Z2 (Set.Icc 0 L)
  second_bound : ∀ r ∈ Set.Icc 0 L, |Z2 r| ≤ M2

/-- Construct the algebraic premises; none of the FD targets is assumed. -/
theorem algebra_premises {K L c M2 Z0 H0 s : ℝ}
    (J : CAS07M05.JacobiPremises K L) (S : ScalarPremises L M2)
    (hK : 0 ≤ K) (hL : 0 < L) (hc : 0 < c) (hM2 : 0 ≤ M2)
    (hEtaL : CAS07M01.eta K L < 1)
    (hZ0 : Z0 = S.Z 0) (hH0 : H0 = c * S.Z1 0)
    (hs : 0 < s) (hsL : s ≤ L) :
    Cas07C03.Premises K s L c M2 (S.Z s) Z0 H0 (CAS07M06.distance J s)
      (CAS07M01.eta K s) (CAS07M01.eta K L) := by
  have hb := CAS07M05.determinant_distance_bridge J hK hL hs hsL hEtaL
  have he := CAS07M01.eta_bounds hK hs hsL hEtaL
  refine ⟨hK, hs, hsL, hc, hM2, ?_, ?_, hb.2.1, hb.2.2, he.1, he.2.1, hEtaL⟩
  · exact Real.sqrt_pos.mpr hb.1
  · exact CAS07M02.remainder_bound_physical L s c M2 S.Z S.Z1 S.Z2
      hL hs.le hsL hc hM2 S.deriv_Z S.deriv_Z1 S.continuous_Z2
      S.second_bound Z0 H0 hZ0 hH0

/-- One conditional analytic synthesis, quantified over every positive s≤L.
The functions are supplied; this theorem neither constructs them nor uses C01. -/
theorem conditional_analytic_synthesis {K L c M2 Z0 H0 : ℝ}
    (J : CAS07M05.JacobiPremises K L) (S : ScalarPremises L M2)
    (hK : 0 ≤ K) (hL : 0 < L) (hc : 0 < c) (hM2 : 0 ≤ M2)
    (hEtaL : CAS07M01.eta K L < 1)
    (hZ0 : Z0 = S.Z 0) (hH0 : H0 = c * S.Z1 0) :
    ∀ s : ℝ, 0 < s → s ≤ L →
      ‖J.D s‖ ≤ Cas07M04.f K s ∧
      ‖J.D s - s • ContinuousLinearMap.id ℝ Cas07M04.Plane‖ ≤ Cas07M04.f K s - s ∧
      CAS07C02.euclideanOpNorm (CAS07M05.matrixOf (J.D s) - s • (1 : CAS07C02.Mat))
        ≤ s * CAS07M01.eta K s ∧
      0 < Matrix.det (CAS07M05.matrixOf (J.D s)) ∧
      (s * (1 - CAS07M01.eta K s)) ^ 2 ≤ Matrix.det (CAS07M05.matrixOf (J.D s)) ∧
      Matrix.det (CAS07M05.matrixOf (J.D s)) ≤ (s * (1 + CAS07M01.eta K s)) ^ 2 ∧
      0 < CAS07M06.distance J s ∧
      s * (1 - CAS07M01.eta K s) ≤ CAS07M06.distance J s ∧
      CAS07M06.distance J s ≤ s * (1 + CAS07M01.eta K s) ∧
      0 < 1 - CAS07M01.eta K s ∧ 0 < 1 - CAS07M01.eta K L ∧
      |S.Z s - Z0 - H0 * s / c| ≤ M2 * s ^ 2 / 2 ∧
      |S.Z s - Z0 - H0 * CAS07M06.distance J s / c| ≤
        M2 * s ^ 2 / 2 + |H0| * s * CAS07M01.eta K s / c ∧
      |S.Z s - Z0 - H0 * CAS07M06.distance J s / c| ≤
        M2 * CAS07M06.distance J s ^ 2 / (2 * (1 - CAS07M01.eta K L) ^ 2) +
          |H0| * CAS07M06.distance J s * CAS07M01.eta K L / (c * (1 - CAS07M01.eta K L)) ∧
      |c * (S.Z s - Z0) / CAS07M06.distance J s - H0| ≤
        c * M2 * s / (2 * (1 - CAS07M01.eta K s)) +
          |H0| * CAS07M01.eta K s / (1 - CAS07M01.eta K s) ∧
      s ≤ CAS07M06.tRefined J s ∧ CAS07M06.tRefined J s ≤ L ∧
      0 < CAS07M06.tRefined J s ∧
      0 ≤ CAS07M01.eta K s ∧
      CAS07M01.eta K s ≤ CAS07M01.eta K (CAS07M06.tRefined J s) ∧
      CAS07M01.eta K (CAS07M06.tRefined J s) ≤ CAS07M01.eta K L ∧
      |S.Z s - Z0 - H0 * CAS07M06.distance J s / c| ≤
        CAS07M06.fd1Rhs M2 H0 c (CAS07M06.tRefined J s)
          (CAS07M01.eta K (CAS07M06.tRefined J s)) ∧
      CAS07M06.fd1Rhs M2 H0 c (CAS07M06.tRefined J s)
          (CAS07M01.eta K (CAS07M06.tRefined J s)) ≤
        CAS07M06.fd2Rhs M2 H0 c (CAS07M06.distance J s) (CAS07M01.eta K L) := by
  intro s hs hsL
  have hp := algebra_premises J S hK hL hc hM2 hEtaL hZ0 hH0 hs hsL
  have he := CAS07M05.c02_premise J hK hL hs hsL hEtaL
  have hd := CAS07M05.determinant_distance_bridge J hK hL hs hsL hEtaL
  have ht := CAS07M06.t_domain J hK hL hs hsL hEtaL
  have het := CAS07M06.eta_order J hK hL hs hsL hEtaL
  have hl : 0 ≤ s * (1 - CAS07M01.eta K s) := by
    exact mul_nonneg hs.le (by linarith [he.2.1])
  have hu : 0 ≤ s * (1 + CAS07M01.eta K s) := by
    exact mul_nonneg hs.le (by linarith [he.1])
  have hsqrt : CAS07M06.distance J s ^ 2 = Matrix.det (CAS07M05.matrixOf (J.D s)) :=
    Real.sq_sqrt hd.1.le
  have hlo : (s * (1 - CAS07M01.eta K s)) ^ 2 ≤ Matrix.det (CAS07M05.matrixOf (J.D s)) := by
    have h := hd.2.1
    change s * (1 - CAS07M01.eta K s) ≤ CAS07M06.distance J s at h
    nlinarith [hp.dA_pos]
  have hhi : Matrix.det (CAS07M05.matrixOf (J.D s)) ≤ (s * (1 + CAS07M01.eta K s)) ^ 2 := by
    have h := hd.2.2
    change CAS07M06.distance J s ≤ s * (1 + CAS07M01.eta K s) at h
    nlinarith [hp.dA_pos]
  refine ⟨Cas07M04.d_norm hK hL J.deriv_D J.deriv_D1 J.continuous_D2
      J.continuous_R J.D_zero J.D1_zero J.jacobi J.curvature_bound s ⟨hs.le, hsL⟩,
    Cas07M04.d_minus_si hK hL J.deriv_D J.deriv_D1 J.continuous_D2
      J.continuous_R J.D_zero J.D1_zero J.jacobi J.curvature_bound s ⟨hs.le, hsL⟩,
    he.2.2, hd.1, hlo, hhi, hp.dA_pos, hp.screen_lower, hp.screen_upper,
    by linarith [he.2.1], by linarith,
    hp.taylor, Cas07C03.FD1 _ _ _ _ _ _ _ _ _ _ _ hp,
    Cas07C03.FD2 _ _ _ _ _ _ _ _ _ _ _ hp, Cas07C03.FD3 _ _ _ _ _ _ _ _ _ _ _ hp,
    ht.1, ht.2.1, ht.2.2, het.1, het.2.1, het.2.2.1,
    CAS07M06.refined_fd1 J hK hL hs hsL hEtaL hp,
    CAS07M06.no_worse_than_fd2 J hK hL hs hsL hEtaL hp⟩

/-- Non-divided conclusions remain available at s=0; no eta(0) interpretation. -/
theorem closed_interval_controls {K L c M2 Z0 H0 : ℝ}
    (J : CAS07M05.JacobiPremises K L) (S : ScalarPremises L M2)
    (hK : 0 ≤ K) (hL : 0 < L) (hc : 0 < c) (hM2 : 0 ≤ M2)
    (hZ0 : Z0 = S.Z 0) (hH0 : H0 = c * S.Z1 0) :
    ∀ s ∈ Set.Icc 0 L,
      ‖J.D s‖ ≤ Cas07M04.f K s ∧
      ‖J.D s - s • ContinuousLinearMap.id ℝ Cas07M04.Plane‖ ≤ Cas07M04.f K s - s ∧
      |S.Z s - Z0 - H0 * s / c| ≤ M2 * s ^ 2 / 2 := by
  intro s hs
  exact ⟨Cas07M04.d_norm hK hL J.deriv_D J.deriv_D1 J.continuous_D2
      J.continuous_R J.D_zero J.D1_zero J.jacobi J.curvature_bound s hs,
    Cas07M04.d_minus_si hK hL J.deriv_D J.deriv_D1 J.continuous_D2
      J.continuous_R J.D_zero J.D1_zero J.jacobi J.curvature_bound s hs,
    CAS07M02.remainder_bound_physical L s c M2 S.Z S.Z1 S.Z2 hL hs.1 hs.2 hc hM2
      S.deriv_Z S.deriv_Z1 S.continuous_Z2 S.second_bound Z0 H0 hZ0 hH0⟩

/-- Both min branches, including equality, follow directly from its definition. -/
theorem min_branches {K L : ℝ} (J : CAS07M05.JacobiPremises K L) (s : ℝ) :
    (L ≤ CAS07M06.distance J s / (1 - CAS07M01.eta K L) → CAS07M06.tRefined J s = L) ∧
    (CAS07M06.distance J s / (1 - CAS07M01.eta K L) ≤ L →
      CAS07M06.tRefined J s = CAS07M06.distance J s / (1 - CAS07M01.eta K L)) := by
  exact ⟨fun h => min_eq_left h, fun h => min_eq_right h⟩

#print axioms algebra_premises
#print axioms conditional_analytic_synthesis
#print axioms closed_interval_controls
#print axioms min_branches
end CAS07Synthesis
