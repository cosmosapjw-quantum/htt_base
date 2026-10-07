import CAS07M01Accepted
import CAS07C03Accepted
import CAS07M05Accepted

/-!
Frozen CAS-07-M06: distance-only `t` refinement.

The imported modules are opaque, kernel-checked interfaces for the accepted
M01, C03, and M05 components.  This file composes those interfaces; it does
not reproduce their proofs.
-/

namespace CAS07M06

noncomputable def distance {K L : ℝ} (J : CAS07M05.JacobiPremises K L)
    (s : ℝ) : ℝ :=
  Real.sqrt (Matrix.det (CAS07M05.matrixOf (J.D s)))

noncomputable def tRefined {K L : ℝ} (J : CAS07M05.JacobiPremises K L)
    (s : ℝ) : ℝ :=
  min L (distance J s / (1 - CAS07M01.eta K L))

noncomputable def fd1Rhs (M2 H0 c r eta : ℝ) : ℝ :=
  M2 * r ^ 2 / 2 + |H0| * r * eta / c

noncomputable def fd2Rhs (M2 H0 c dA etaL : ℝ) : ℝ :=
  M2 * dA ^ 2 / (2 * (1 - etaL) ^ 2) +
    |H0| * dA * etaL / (c * (1 - etaL))

theorem t_domain {K L s : ℝ} (J : CAS07M05.JacobiPremises K L)
    (hK : 0 ≤ K) (hL : 0 < L) (hs : 0 < s) (hsL : s ≤ L)
    (hEtaL : CAS07M01.eta K L < 1) :
    s ≤ tRefined J s ∧ tRefined J s ≤ L ∧ 0 < tRefined J s := by
  have hM05 := CAS07M05.determinant_distance_bridge J hK hL hs hsL hEtaL
  have hEtaS := CAS07M01.eta_bounds hK hs hsL hEtaL
  have hden : 0 < 1 - CAS07M01.eta K L := by linarith
  have hscaled : s * (1 - CAS07M01.eta K L) ≤ distance J s := by
    dsimp [distance]
    calc
      s * (1 - CAS07M01.eta K L) ≤ s * (1 - CAS07M01.eta K s) := by
        nlinarith
      _ ≤ Real.sqrt (Matrix.det (CAS07M05.matrixOf (J.D s))) := hM05.2.1
  have hsq : s ≤ distance J s / (1 - CAS07M01.eta K L) :=
    (le_div_iff₀ hden).2 hscaled
  have hst : s ≤ tRefined J s := by
    exact le_min hsL hsq
  exact ⟨hst, min_le_left _ _, lt_of_lt_of_le hs hst⟩

theorem eta_order {K L s : ℝ} (J : CAS07M05.JacobiPremises K L)
    (hK : 0 ≤ K) (hL : 0 < L) (hs : 0 < s) (hsL : s ≤ L)
    (hEtaL : CAS07M01.eta K L < 1) :
    0 ≤ CAS07M01.eta K s ∧
      CAS07M01.eta K s ≤ CAS07M01.eta K (tRefined J s) ∧
      CAS07M01.eta K (tRefined J s) ≤ CAS07M01.eta K L ∧
      CAS07M01.eta K L < 1 := by
  have ht := t_domain J hK hL hs hsL hEtaL
  have hEtaT := CAS07M01.eta_bounds hK ht.2.2 ht.2.1 hEtaL
  have hEtaS := CAS07M01.eta_bounds hK hs ht.1 hEtaT.2.2
  exact ⟨hEtaS.1, hEtaS.2.1, hEtaT.2.1, hEtaL⟩

theorem refined_fd1 {K L s c M2 Z Z0 H0 : ℝ}
    (J : CAS07M05.JacobiPremises K L)
    (hK : 0 ≤ K) (hL : 0 < L) (hs : 0 < s) (hsL : s ≤ L)
    (hEtaL : CAS07M01.eta K L < 1)
    (hC03 : Cas07C03.Premises K s L c M2 Z Z0 H0 (distance J s)
      (CAS07M01.eta K s) (CAS07M01.eta K L)) :
    |Z - Z0 - H0 * distance J s / c| ≤
      fd1Rhs M2 H0 c (tRefined J s) (CAS07M01.eta K (tRefined J s)) := by
  have ht := t_domain J hK hL hs hsL hEtaL
  have heta := eta_order J hK hL hs hsL hEtaL
  have hsq : s ^ 2 ≤ (tRefined J s) ^ 2 := by nlinarith
  have hprod : s * CAS07M01.eta K s ≤
      tRefined J s * CAS07M01.eta K (tRefined J s) := by
    exact mul_le_mul ht.1 heta.2.1 heta.1 (le_of_lt ht.2.2)
  have hfirst : M2 * s ^ 2 / 2 ≤ M2 * (tRefined J s) ^ 2 / 2 := by
    gcongr
    exact hC03.M2_nonneg
  have hsecond : |H0| * s * CAS07M01.eta K s / c ≤
      |H0| * tRefined J s * CAS07M01.eta K (tRefined J s) / c := by
    apply (div_le_div_iff_of_pos_right hC03.c_pos).2
    nlinarith [abs_nonneg H0]
  have hbase := Cas07C03.FD1 K s L c M2 Z Z0 H0 (distance J s)
    (CAS07M01.eta K s) (CAS07M01.eta K L) hC03
  dsimp [fd1Rhs]
  linarith

theorem no_worse_than_fd2 {K L s c M2 Z Z0 H0 : ℝ}
    (J : CAS07M05.JacobiPremises K L)
    (hK : 0 ≤ K) (hL : 0 < L) (hs : 0 < s) (hsL : s ≤ L)
    (hEtaL : CAS07M01.eta K L < 1)
    (hC03 : Cas07C03.Premises K s L c M2 Z Z0 H0 (distance J s)
      (CAS07M01.eta K s) (CAS07M01.eta K L)) :
    fd1Rhs M2 H0 c (tRefined J s) (CAS07M01.eta K (tRefined J s)) ≤
      fd2Rhs M2 H0 c (distance J s) (CAS07M01.eta K L) := by
  have ht := t_domain J hK hL hs hsL hEtaL
  have heta := eta_order J hK hL hs hsL hEtaL
  have hden : 0 < 1 - CAS07M01.eta K L := by linarith
  have hqpos : 0 < distance J s / (1 - CAS07M01.eta K L) := by
    have hdet := (CAS07M05.determinant_distance_bridge J hK hL hs hsL hEtaL).1
    exact div_pos (Real.sqrt_pos.2 hdet) hden
  have htq : tRefined J s ≤ distance J s / (1 - CAS07M01.eta K L) :=
    min_le_right _ _
  have hsquares : (tRefined J s) ^ 2 ≤
      (distance J s / (1 - CAS07M01.eta K L)) ^ 2 := by nlinarith
  have hproducts : tRefined J s * CAS07M01.eta K (tRefined J s) ≤
      (distance J s / (1 - CAS07M01.eta K L)) * CAS07M01.eta K L := by
    exact mul_le_mul htq heta.2.2.1 (by linarith [heta.1]) (le_of_lt hqpos)
  have hfirst : M2 * (tRefined J s) ^ 2 / 2 ≤
      M2 * (distance J s / (1 - CAS07M01.eta K L)) ^ 2 / 2 := by
    gcongr
    exact hC03.M2_nonneg
  have hsecond : |H0| * tRefined J s * CAS07M01.eta K (tRefined J s) / c ≤
      |H0| * (distance J s / (1 - CAS07M01.eta K L)) *
        CAS07M01.eta K L / c := by
    apply (div_le_div_iff_of_pos_right hC03.c_pos).2
    nlinarith [abs_nonneg H0]
  dsimp [fd1Rhs, fd2Rhs]
  calc
    M2 * (tRefined J s) ^ 2 / 2 +
          |H0| * tRefined J s * CAS07M01.eta K (tRefined J s) / c
        ≤ M2 * (distance J s / (1 - CAS07M01.eta K L)) ^ 2 / 2 +
          |H0| * (distance J s / (1 - CAS07M01.eta K L)) *
            CAS07M01.eta K L / c := add_le_add hfirst hsecond
    _ = M2 * distance J s ^ 2 / (2 * (1 - CAS07M01.eta K L) ^ 2) +
          |H0| * distance J s * CAS07M01.eta K L /
            (c * (1 - CAS07M01.eta K L)) := by
      field_simp

theorem k_zero_control {L s : ℝ} (J : CAS07M05.JacobiPremises 0 L)
    (hL : 0 < L) (hs : 0 < s) (hsL : s ≤ L) :
    CAS07M01.eta 0 L = 0 ∧ distance J s = s ∧ tRefined J s = s := by
  have hetaS : CAS07M01.eta 0 s = 0 := by
    simp [CAS07M01.eta, CAS07M01.fd, hs.ne']
  have hetaL : CAS07M01.eta 0 L = 0 := by
    simp [CAS07M01.eta, CAS07M01.fd, hL.ne']
  have hm := CAS07M05.determinant_distance_bridge J (le_refl 0) hL hs hsL (by simp [hetaL])
  have hd : distance J s = s := by
    dsimp [distance]
    rw [hetaS] at hm
    norm_num at hm
    linarith
  refine ⟨hetaL, hd, ?_⟩
  simp [tRefined, hd, hetaL, min_eq_right hsL]

#print axioms t_domain
#print axioms eta_order
#print axioms refined_fd1
#print axioms no_worse_than_fd2
#print axioms k_zero_control

end CAS07M06
