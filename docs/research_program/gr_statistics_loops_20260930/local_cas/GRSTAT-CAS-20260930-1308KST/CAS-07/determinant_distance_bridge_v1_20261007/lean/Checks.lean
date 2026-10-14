import Main

open CAS07M05

-- CAS-07-M05-REWRITE: exact f_K(s)-s = s eta_K(s).
example (K s : ℝ) (hs : 0 < s) :
    Cas07M04.f K s - s = s * CAS07M01.eta K s :=
  f_sub_eq_s_eta K s hs

-- CAS-07-M05-C02-PREMISE: M01+M04, transported through an exact norm identity.
example {K L s : ℝ} (J : JacobiPremises K L)
    (hK : 0 ≤ K) (hL : 0 < L) (hs : 0 < s) (hsL : s ≤ L)
    (hEtaL : CAS07M01.eta K L < 1) :
    0 ≤ CAS07M01.eta K s ∧ CAS07M01.eta K s < 1 ∧
      CAS07C02.euclideanOpNorm (matrixOf (J.D s) - s • (1 : CAS07C02.Mat)) ≤
        s * CAS07M01.eta K s :=
  c02_premise J hK hL hs hsL hEtaL

-- CAS-07-M05-DETERMINANT-SIGN: C02's full arbitrary-matrix theorem is applied.
example {K L s : ℝ} (J : JacobiPremises K L)
    (hK : 0 ≤ K) (hL : 0 < L) (hs : 0 < s) (hsL : s ≤ L)
    (hEtaL : CAS07M01.eta K L < 1) :
    0 < Matrix.det (matrixOf (J.D s)) :=
  (determinant_distance_bridge J hK hL hs hsL hEtaL).1

-- CAS-07-M05-DISTANCE-BOUND: positive sqrt(det) lies in the stated interval.
example {K L s : ℝ} (J : JacobiPremises K L)
    (hK : 0 ≤ K) (hL : 0 < L) (hs : 0 < s) (hsL : s ≤ L)
    (hEtaL : CAS07M01.eta K L < 1) :
    s * (1 - CAS07M01.eta K s) ≤ Real.sqrt (Matrix.det (matrixOf (J.D s))) ∧
      Real.sqrt (Matrix.det (matrixOf (J.D s))) ≤ s * (1 + CAS07M01.eta K s) :=
  (determinant_distance_bridge J hK hL hs hsL hEtaL).2

-- K=0 control: exact operator identity and dA=s.
example {L s : ℝ} (J : JacobiPremises 0 L)
    (hL : 0 < L) (hs : 0 < s) (hsL : s ≤ L) :
    J.D s = s • ContinuousLinearMap.id ℝ Cas07M04.Plane ∧
      0 < Matrix.det (matrixOf (J.D s)) ∧
      Real.sqrt (Matrix.det (matrixOf (J.D s))) = s ∧
      Matrix.det (matrixOf (J.D s)) = s ^ 2 :=
  zero_curvature_control J hL hs hsL

#print axioms CAS07M05.f_sub_eq_s_eta
#print axioms CAS07M05.c02_premise
#print axioms CAS07M05.determinant_distance_bridge
#print axioms CAS07M05.zero_curvature_control
