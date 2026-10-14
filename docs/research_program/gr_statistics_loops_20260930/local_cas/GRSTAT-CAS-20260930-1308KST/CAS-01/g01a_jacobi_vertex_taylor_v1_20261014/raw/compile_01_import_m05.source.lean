import CAS07M01Accepted
import CAS07M04Accepted
import CAS07C02Accepted

noncomputable section

namespace CAS07M05

open Cas07M04

/-- Coordinate matrix of an arbitrary real Euclidean-plane operator. -/
def matrixOf (T : Cas07M04.Op) : CAS07C02.Mat :=
  Matrix.toEuclideanLin.symm T.toLinearMap

private theorem matrixOf_toOp (T : Cas07M04.Op) :
    (Matrix.toEuclideanLin (matrixOf T)).toContinuousLinearMap = T := by
  ext v
  simp [matrixOf]

private theorem identity_toOp :
    (Matrix.toEuclideanLin (1 : CAS07C02.Mat)).toContinuousLinearMap =
      ContinuousLinearMap.id ℝ Cas07M04.Plane := by
  ext v
  simp

private theorem error_toOp (T : Cas07M04.Op) (s : ℝ) :
    (Matrix.toEuclideanLin (matrixOf T - s • (1 : CAS07C02.Mat))).toContinuousLinearMap =
      T - s • ContinuousLinearMap.id ℝ Cas07M04.Plane := by
  ext v
  simp [map_sub, map_smul, matrixOf_toOp]

/-- The matrix norm used by C02 is exactly the operator norm used by M04. -/
theorem opnorm_error_eq (T : Cas07M04.Op) (s : ℝ) :
    CAS07C02.euclideanOpNorm (matrixOf T - s • (1 : CAS07C02.Mat)) =
      ‖T - s • ContinuousLinearMap.id ℝ Cas07M04.Plane‖ := by
  simpa only [CAS07C02.euclideanOpNorm] using congrArg norm (error_toOp T s)

/-- Exact defining rewrite; no series or approximation is used. -/
theorem f_sub_eq_s_eta (K s : ℝ) (hs : 0 < s) :
    Cas07M04.f K s - s = s * CAS07M01.eta K s := by
  have hf : Cas07M04.f K s = CAS07M01.fd K s := by
    simp [Cas07M04.f, CAS07M01.fd]
  rw [hf, CAS07M01.eta]
  have hs0 : s ≠ 0 := ne_of_gt hs
  field_simp

/-- Exactly the admitted Jacobi premises consumed by the accepted M04 theorem. -/
structure JacobiPremises (K L : ℝ) where
  D : ℝ → Cas07M04.Op
  D1 : ℝ → Cas07M04.Op
  D2 : ℝ → Cas07M04.Op
  R : ℝ → Cas07M04.Op
  deriv_D : ∀ t ∈ Set.Icc 0 L, HasDerivWithinAt D (D1 t) (Set.Icc 0 L) t
  deriv_D1 : ∀ t ∈ Set.Icc 0 L, HasDerivWithinAt D1 (D2 t) (Set.Icc 0 L) t
  continuous_D2 : ContinuousOn D2 (Set.Icc 0 L)
  continuous_R : ContinuousOn R (Set.Icc 0 L)
  D_zero : D 0 = 0
  D1_zero : D1 0 = ContinuousLinearMap.id ℝ Cas07M04.Plane
  jacobi : ∀ t ∈ Set.Icc 0 L, D2 t = -R t ∘SL D t
  curvature_bound : ∀ t ∈ Set.Icc 0 L, ‖R t‖ ≤ K

/-- M01 bounds and the exact M04 estimate give C02's matrix-norm premise. -/
theorem c02_premise {K L s : ℝ} (J : JacobiPremises K L)
    (hK : 0 ≤ K) (hL : 0 < L) (hs : 0 < s) (hsL : s ≤ L)
    (hEtaL : CAS07M01.eta K L < 1) :
    0 ≤ CAS07M01.eta K s ∧ CAS07M01.eta K s < 1 ∧
      CAS07C02.euclideanOpNorm (matrixOf (J.D s) - s • (1 : CAS07C02.Mat)) ≤
        s * CAS07M01.eta K s := by
  have hEta := CAS07M01.eta_bounds hK hs hsL hEtaL
  have hM04 := Cas07M04.d_minus_si hK hL J.deriv_D J.deriv_D1
    J.continuous_D2 J.continuous_R J.D_zero J.D1_zero J.jacobi
    J.curvature_bound s ⟨le_of_lt hs, hsL⟩
  have hRewrite := f_sub_eq_s_eta K s hs
  rw [opnorm_error_eq, ← hRewrite]
  exact ⟨hEta.1, hEta.2.2, hM04⟩

/-- The accepted full C02 theorem supplies the determinant sign and positive-root bounds. -/
theorem determinant_distance_bridge {K L s : ℝ} (J : JacobiPremises K L)
    (hK : 0 ≤ K) (hL : 0 < L) (hs : 0 < s) (hsL : s ≤ L)
    (hEtaL : CAS07M01.eta K L < 1) :
    0 < Matrix.det (matrixOf (J.D s)) ∧
      s * (1 - CAS07M01.eta K s) ≤ Real.sqrt (Matrix.det (matrixOf (J.D s))) ∧
      Real.sqrt (Matrix.det (matrixOf (J.D s))) ≤ s * (1 + CAS07M01.eta K s) := by
  obtain ⟨hEta0, hEta1, hNorm⟩ := c02_premise J hK hL hs hsL hEtaL
  exact (CAS07C02.CAS_07_C02_full (matrixOf (J.D s)) s
    (CAS07M01.eta K s) hs hEta0 hEta1 hNorm).2

private theorem eta_zero {t : ℝ} (ht : t ≠ 0) : CAS07M01.eta 0 t = 0 := by
  simp [CAS07M01.eta, CAS07M01.fd, ht]

/-- At zero curvature M04 gives the exact identity map, and C02 gives dA=s. -/
theorem zero_curvature_control {L s : ℝ} (J : JacobiPremises 0 L)
    (hL : 0 < L) (hs : 0 < s) (hsL : s ≤ L) :
    J.D s = s • ContinuousLinearMap.id ℝ Cas07M04.Plane ∧
      0 < Matrix.det (matrixOf (J.D s)) ∧
      Real.sqrt (Matrix.det (matrixOf (J.D s))) = s ∧
      Matrix.det (matrixOf (J.D s)) = s ^ 2 := by
  have hEtaL : CAS07M01.eta 0 L < 1 := by
    rw [eta_zero (ne_of_gt hL)]
    norm_num
  have hEtaS : CAS07M01.eta 0 s = 0 := eta_zero (ne_of_gt hs)
  have hD := Cas07M04.zero_parameter_control hL J.deriv_D J.deriv_D1
    J.continuous_D2 J.D_zero J.D1_zero J.jacobi J.curvature_bound
    s ⟨le_of_lt hs, hsL⟩
  have hBridge := determinant_distance_bridge J (le_refl 0) hL hs hsL hEtaL
  have hLower : s ≤ Real.sqrt (Matrix.det (matrixOf (J.D s))) := by
    simpa [hEtaS] using hBridge.2.1
  have hUpper : Real.sqrt (Matrix.det (matrixOf (J.D s))) ≤ s := by
    simpa [hEtaS] using hBridge.2.2
  have hDistance := le_antisymm hUpper hLower
  have hDet : Matrix.det (matrixOf (J.D s)) = s ^ 2 := by
    calc
      Matrix.det (matrixOf (J.D s)) =
          Real.sqrt (Matrix.det (matrixOf (J.D s))) ^ 2 :=
        (Real.sq_sqrt (le_of_lt hBridge.1)).symm
      _ = s ^ 2 := by rw [hDistance]
  exact ⟨hD, hBridge.1, hDistance, hDet⟩

end CAS07M05
