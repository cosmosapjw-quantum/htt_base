import Mathlib

/-!
CAS-07 C03: exact finite-distance algebra over the reals. The Taylor remainder
and two-sided screen inequalities are explicit premises; no differential or
physical assertion is derived here.
-/

namespace Cas07C03

structure Premises (Kc s L c M2 Z Z0 H0 dA eta etaL : ℝ) : Prop where
  Kc_nonneg : 0 ≤ Kc
  s_pos : 0 < s
  s_le_L : s ≤ L
  c_pos : 0 < c
  M2_nonneg : 0 ≤ M2
  dA_pos : 0 < dA
  taylor : |Z - Z0 - H0 * s / c| ≤ M2 * s ^ 2 / 2
  screen_lower : s * (1 - eta) ≤ dA
  screen_upper : dA ≤ s * (1 + eta)
  eta_nonneg : 0 ≤ eta
  eta_le_etaL : eta ≤ etaL
  etaL_lt_one : etaL < 1

theorem FD1 (Kc s L c M2 Z Z0 H0 dA eta etaL : ℝ)
    (h : Premises Kc s L c M2 Z Z0 H0 dA eta etaL) :
    |Z - Z0 - H0 * dA / c| ≤ M2 * s ^ 2 / 2 + |H0| * s * eta / c := by
  have hdist : |s - dA| ≤ s * eta := by
    apply abs_le.mpr
    constructor <;> nlinarith [h.screen_lower, h.screen_upper]
  have hpert : |H0 * (s - dA) / c| ≤ |H0| * s * eta / c := by
    rw [abs_div, abs_mul, abs_of_pos h.c_pos]
    have hm := mul_le_mul_of_nonneg_left hdist (abs_nonneg H0)
    have hd := div_le_div_of_nonneg_right hm (le_of_lt h.c_pos)
    simpa only [mul_assoc] using hd
  have hsplit : Z - Z0 - H0 * dA / c =
      (Z - Z0 - H0 * s / c) + H0 * (s - dA) / c := by
    field_simp [ne_of_gt h.c_pos]
    ring
  rw [hsplit]
  exact (abs_add_le _ _).trans (add_le_add h.taylor hpert)

theorem FD2 (Kc s L c M2 Z Z0 H0 dA eta etaL : ℝ)
    (h : Premises Kc s L c M2 Z Z0 H0 dA eta etaL) :
    |Z - Z0 - H0 * dA / c| ≤
      M2 * dA ^ 2 / (2 * (1 - etaL) ^ 2) +
        |H0| * dA * etaL / (c * (1 - etaL)) := by
  have hq : 0 < 1 - etaL := by linarith [h.etaL_lt_one]
  have hsq : s * (1 - etaL) ≤ dA := by
    calc
      s * (1 - etaL) ≤ s * (1 - eta) :=
        mul_le_mul_of_nonneg_left (by linarith [h.eta_le_etaL]) (le_of_lt h.s_pos)
      _ ≤ dA := h.screen_lower
  have hsbound : s ≤ dA / (1 - etaL) :=
    (le_div_iff₀ hq).mpr (by nlinarith [hsq])
  have hfirst : M2 * s ^ 2 / 2 ≤
      M2 * dA ^ 2 / (2 * (1 - etaL) ^ 2) := by
    calc
      M2 * s ^ 2 / 2 ≤ M2 * (dA / (1 - etaL)) ^ 2 / 2 := by
        gcongr
        · exact h.M2_nonneg
        · exact le_of_lt h.s_pos
      _ = M2 * dA ^ 2 / (2 * (1 - etaL) ^ 2) := by
        field_simp [ne_of_gt hq]
  have hmult : s * eta ≤ (dA / (1 - etaL)) * etaL := by
    calc
      s * eta ≤ (dA / (1 - etaL)) * eta :=
        mul_le_mul_of_nonneg_right hsbound h.eta_nonneg
      _ ≤ (dA / (1 - etaL)) * etaL :=
        mul_le_mul_of_nonneg_left h.eta_le_etaL (le_of_lt (div_pos h.dA_pos hq))
  have hsecond : |H0| * s * eta / c ≤
      |H0| * dA * etaL / (c * (1 - etaL)) := by
    have hm := mul_le_mul_of_nonneg_left hmult (abs_nonneg H0)
    have hd := div_le_div_of_nonneg_right hm (le_of_lt h.c_pos)
    calc
      |H0| * s * eta / c = |H0| * (s * eta) / c := by ring
      _ ≤ |H0| * ((dA / (1 - etaL)) * etaL) / c := hd
      _ = |H0| * dA * etaL / (c * (1 - etaL)) := by
        field_simp [ne_of_gt hq, ne_of_gt h.c_pos]
  exact (FD1 Kc s L c M2 Z Z0 H0 dA eta etaL h).trans
    (add_le_add hfirst hsecond)

theorem FD3 (Kc s L c M2 Z Z0 H0 dA eta etaL : ℝ)
    (h : Premises Kc s L c M2 Z Z0 H0 dA eta etaL) :
    |c * (Z - Z0) / dA - H0| ≤
      c * M2 * s / (2 * (1 - eta)) + |H0| * eta / (1 - eta) := by
  have hq : 0 < 1 - eta := by linarith [h.eta_le_etaL, h.etaL_lt_one]
  have hratio : s / dA ≤ 1 / (1 - eta) := by
    apply (div_le_div_iff₀ h.dA_pos hq).mpr
    nlinarith [h.screen_lower]
  have hfirst : (c / dA) * (M2 * s ^ 2 / 2) ≤
      c * M2 * s / (2 * (1 - eta)) := by
    have hn : 0 ≤ c * M2 * s / 2 := by
      exact div_nonneg
        (mul_nonneg (mul_nonneg (le_of_lt h.c_pos) h.M2_nonneg) (le_of_lt h.s_pos))
        (by norm_num)
    have hm := mul_le_mul_of_nonneg_left hratio hn
    calc
      (c / dA) * (M2 * s ^ 2 / 2) = (c * M2 * s / 2) * (s / dA) := by ring
      _ ≤ (c * M2 * s / 2) * (1 / (1 - eta)) := hm
      _ = c * M2 * s / (2 * (1 - eta)) := by
        field_simp [ne_of_gt hq]
  have hsecond : (c / dA) * (|H0| * s * eta / c) ≤
      |H0| * eta / (1 - eta) := by
    have hn : 0 ≤ |H0| * eta := mul_nonneg (abs_nonneg H0) h.eta_nonneg
    have hm := mul_le_mul_of_nonneg_left hratio hn
    calc
      (c / dA) * (|H0| * s * eta / c) = (|H0| * eta) * (s / dA) := by
        field_simp [ne_of_gt h.c_pos]
      _ ≤ (|H0| * eta) * (1 / (1 - eta)) := hm
      _ = |H0| * eta / (1 - eta) := by ring
  have hid : c * (Z - Z0) / dA - H0 =
      (c / dA) * (Z - Z0 - H0 * dA / c) := by
    field_simp [ne_of_gt h.dA_pos, ne_of_gt h.c_pos]
  rw [hid, abs_mul, abs_of_pos (div_pos h.c_pos h.dA_pos)]
  calc
    (c / dA) * |Z - Z0 - H0 * dA / c| ≤
        (c / dA) * (M2 * s ^ 2 / 2 + |H0| * s * eta / c) :=
      mul_le_mul_of_nonneg_left (FD1 Kc s L c M2 Z Z0 H0 dA eta etaL h)
        (le_of_lt (div_pos h.c_pos h.dA_pos))
    _ = (c / dA) * (M2 * s ^ 2 / 2) + (c / dA) * (|H0| * s * eta / c) := by ring
    _ ≤ c * M2 * s / (2 * (1 - eta)) + |H0| * eta / (1 - eta) :=
      add_le_add hfirst hsecond

#print axioms Cas07C03.FD1
#print axioms Cas07C03.FD2
#print axioms Cas07C03.FD3

end Cas07C03
