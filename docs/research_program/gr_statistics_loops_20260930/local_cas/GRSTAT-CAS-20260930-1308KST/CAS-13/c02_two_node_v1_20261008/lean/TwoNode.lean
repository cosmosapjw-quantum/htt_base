import Mathlib

/-!
CAS-13-C02, independent Lean axis.  The scope is exactly the strict two-node
feasibility statement and its separate boundary measures.
-/

namespace CAS13C02

noncomputable def secant (a x : ℝ) : ℝ :=
  (x ^ 3 + a * x ^ 2 + a ^ 2 * x + a ^ 3) / (x ^ 2 + a * x + a ^ 2)

theorem denominator_pos {a x : ℝ} (ha : 0 < a) (hx : 0 < x) :
    0 < x ^ 2 + a * x + a ^ 2 := by positivity

theorem secant_eq_ratio {a x : ℝ} (ha : a ≠ x)
    (hden : x ^ 2 + a * x + a ^ 2 ≠ 0) :
    secant a x = (x ^ 4 - a ^ 4) / (x ^ 3 - a ^ 3) := by
  have hdiff : x ^ 3 - a ^ 3 ≠ 0 := by
    intro h
    have hfact : (x - a) * (x ^ 2 + a * x + a ^ 2) = 0 := by
      nlinarith [h]
    rcases mul_eq_zero.mp hfact with h | h
    · exact ha (sub_eq_zero.mp h).symm
    · exact hden h
  unfold secant
  apply (div_eq_div_iff hden hdiff).2
  ring

theorem secant_deriv {a x : ℝ} (ha : 0 < a) (hx : 0 < x) :
    deriv (secant a) x =
      x ^ 2 * (3 * a ^ 2 + 2 * a * x + x ^ 2) /
        (a ^ 2 + a * x + x ^ 2) ^ 2 := by
  have hd : x ^ 2 + a * x + a ^ 2 ≠ 0 := (denominator_pos ha hx).ne'
  have hn : HasDerivAt
      (fun y : ℝ => y ^ 3 + a * y ^ 2 + a ^ 2 * y + a ^ 3)
      (3 * x ^ 2 + 2 * a * x + a ^ 2) x := by
    convert (((hasDerivAt_id x).pow 3).add
      (((hasDerivAt_id x).pow 2).const_mul a) |>.add
      ((hasDerivAt_id x).const_mul (a ^ 2)) |>.add
      (hasDerivAt_const x (a ^ 3))) using 1 <;> first | rfl | (dsimp; ring)
  have hq : HasDerivAt
      (fun y : ℝ => y ^ 2 + a * y + a ^ 2)
      (2 * x + a) x := by
    convert (((hasDerivAt_id x).pow 2).add
      ((hasDerivAt_id x).const_mul a) |>.add
      (hasDerivAt_const x (a ^ 2))) using 1 <;> first | rfl | (dsimp; ring)
  have h := (hn.div hq hd).deriv
  change deriv (secant a) x = _
  rw [show deriv (secant a) x = _ from h]
  field_simp
  ring

theorem secant_deriv_pos {a x : ℝ} (ha : 0 < a) (hx : 0 < x) :
    0 < deriv (secant a) x := by
  rw [secant_deriv ha hx]
  have h1 : 0 < x ^ 2 := by positivity
  have h2 : 0 < 3 * a ^ 2 + 2 * a * x + x ^ 2 := by positivity
  have h3 : 0 < (a ^ 2 + a * x + x ^ 2) ^ 2 := by positivity
  exact div_pos (mul_pos h1 h2) h3

theorem secant_strictMonoOn {a : ℝ} (ha : 0 < a) :
    StrictMonoOn (secant a) (Set.Ioi 0) := by
  apply strictMonoOn_of_deriv_pos (convex_Ioi 0)
  · unfold secant
    apply ContinuousOn.div₀ (by fun_prop) (by fun_prop)
    intro x hx
    exact (denominator_pos ha hx).ne'
  · intro x hx
    have hx' : 0 < x := by simpa using hx
    exact secant_deriv_pos ha hx'

theorem cube_sub_pos {x y : ℝ} (hx : 0 < x) (hy : 0 < y) (hxy : x < y) :
    0 < y ^ 3 - x ^ 3 := by
  have hprod := mul_pos (sub_pos.mpr hxy) (denominator_pos hx hy)
  nlinarith

theorem quartic_sub_pos {x y : ℝ} (hx : 0 < x) (_hy : 0 < y) (hxy : x < y) :
    0 < y ^ 4 - x ^ 4 := by
  exact sub_pos.mpr (pow_lt_pow_left₀ hxy hx.le (by norm_num : (4 : ℕ) ≠ 0))

structure StrictInterior (a b m3 m4 : ℝ) : Prop where
  a_pos : 0 < a
  a_lt_b : a < b
  a3_lt_m3 : a ^ 3 < m3
  m3_lt_b3 : m3 < b ^ 3
  lower : m3 ^ ((4 : ℝ) / 3) < m4
  upper : m4 < a ^ 4 + (m3 - a ^ 3) * (b ^ 4 - a ^ 4) / (b ^ 3 - a ^ 3)

noncomputable def positiveCubeRoot (m3 : ℝ) : ℝ := m3 ^ ((3 : ℕ)⁻¹ : ℝ)

theorem positiveCubeRoot_pos {m3 : ℝ} (hm3 : 0 < m3) : 0 < positiveCubeRoot m3 := by
  exact Real.rpow_pos_of_pos hm3 _

theorem positiveCubeRoot_cube {m3 : ℝ} (hm3 : 0 ≤ m3) :
    positiveCubeRoot m3 ^ 3 = m3 := by
  exact Real.rpow_inv_natCast_pow hm3 (by norm_num : (3 : ℕ) ≠ 0)

theorem positiveCubeRoot_fourth {m3 : ℝ} (hm3 : 0 ≤ m3) :
    positiveCubeRoot m3 ^ 4 = m3 ^ ((4 : ℝ) / 3) := by
  calc
    _ = (positiveCubeRoot m3) ^ (4 : ℝ) := (Real.rpow_natCast _ 4).symm
    _ = m3 ^ (((3 : ℕ)⁻¹ : ℝ) * 4) :=
      (Real.rpow_mul hm3 _ _).symm
    _ = m3 ^ ((4 : ℝ) / 3) := by congr 1; norm_num

theorem root_between {a b m3 : ℝ} (ha : 0 < a) (hab : a < b)
    (ham : a ^ 3 < m3) (hmb : m3 < b ^ 3) :
    let r := positiveCubeRoot m3
    0 < r ∧ r ^ 3 = m3 ∧ a < r ∧ r < b := by
  dsimp only
  have hbpos : 0 < b := lt_trans ha hab
  have hm3pos : 0 < m3 := lt_trans (pow_pos ha 3) ham
  have hrpos := positiveCubeRoot_pos hm3pos
  have hr3 := positiveCubeRoot_cube hm3pos.le
  have har : a < positiveCubeRoot m3 := by
    by_contra hnot
    have hp := pow_le_pow_left₀ hrpos.le (le_of_not_gt hnot) 3
    linarith only [hp, hr3, ham]
  have hrb : positiveCubeRoot m3 < b := by
    by_contra hnot
    have hp := pow_le_pow_left₀ hbpos.le (le_of_not_gt hnot) 3
    linarith only [hp, hr3, hmb]
  exact ⟨hrpos, hr3, har, hrb⟩

theorem root_properties {a b m3 m4 : ℝ} (h : StrictInterior a b m3 m4) :
    let r := positiveCubeRoot m3
    0 < r ∧ r ^ 3 = m3 ∧ a < r ∧ r < b ∧ r ^ 4 < m4 := by
  dsimp only
  have hm3pos : 0 < m3 := lt_trans (pow_pos h.a_pos 3) h.a3_lt_m3
  obtain ⟨hrpos, hr3, har, hrb⟩ := root_between h.a_pos h.a_lt_b h.a3_lt_m3 h.m3_lt_b3
  have hr4 := positiveCubeRoot_fourth hm3pos.le
  exact ⟨hrpos, hr3, har, hrb, hr4.trans_lt h.lower⟩

theorem secant_scaled {a x : ℝ} (ha : 0 < a) (hx : 0 < x) (hax : a < x) :
    (x ^ 3 - a ^ 3) * secant a x = x ^ 4 - a ^ 4 := by
  have hden : x ^ 2 + a * x + a ^ 2 ≠ 0 := (denominator_pos ha hx).ne'
  rw [secant_eq_ratio (ne_of_lt hax) hden]
  have hcube := (cube_sub_pos ha hx hax).ne'
  field_simp

theorem secant_symm {a b : ℝ} (ha : 0 < a) (hab : a < b) :
    secant a b = secant b a := by
  have hb : 0 < b := lt_trans ha hab
  have hd1 : b ^ 2 + a * b + a ^ 2 ≠ 0 := (denominator_pos ha hb).ne'
  have hd2 : a ^ 2 + b * a + b ^ 2 ≠ 0 := (denominator_pos hb ha).ne'
  rw [secant_eq_ratio (ne_of_lt hab) hd1,
    secant_eq_ratio (ne_of_gt hab) hd2]
  have hcube := (cube_sub_pos ha hb hab).ne'
  have hcube' : a ^ 3 - b ^ 3 ≠ 0 :=
    sub_ne_zero.mpr (ne_of_lt (pow_lt_pow_left₀ hab ha.le (by norm_num)))
  apply (div_eq_div_iff hcube hcube').2
  ring

theorem secant_eq_reversed_ratio {x b : ℝ} (hx : 0 < x) (hb : 0 < b) (hxb : x < b) :
    secant b x = (b ^ 4 - x ^ 4) / (b ^ 3 - x ^ 3) := by
  have hd : x ^ 2 + b * x + b ^ 2 ≠ 0 := (denominator_pos hb hx).ne'
  rw [secant_eq_ratio (ne_of_gt hxb) hd]
  have hcube : b ^ 3 - x ^ 3 ≠ 0 := (cube_sub_pos hx hb hxb).ne'
  have hcube' : x ^ 3 - b ^ 3 ≠ 0 :=
    sub_ne_zero.mpr (ne_of_lt (pow_lt_pow_left₀ hxb hx.le (by norm_num)))
  apply (div_eq_div_iff hcube' hcube).2
  ring

theorem strict_brackets {a b m3 m4 : ℝ} (h : StrictInterior a b m3 m4) :
    let r := positiveCubeRoot m3
    secant a r < (m4 - a ^ 4) / (m3 - a ^ 3) ∧
    (m4 - a ^ 4) / (m3 - a ^ 3) < secant a b ∧
    secant b a < (b ^ 4 - m4) / (b ^ 3 - m3) ∧
    (b ^ 4 - m4) / (b ^ 3 - m3) < secant b r := by
  dsimp only
  let r := positiveCubeRoot m3
  obtain ⟨hrpos, hr3, har, hrb, hr4⟩ := root_properties h
  have hbpos : 0 < b := lt_trans h.a_pos h.a_lt_b
  have hma : 0 < m3 - a ^ 3 := sub_pos.mpr h.a3_lt_m3
  have hbm : 0 < b ^ 3 - m3 := sub_pos.mpr h.m3_lt_b3
  have hab3 : 0 < b ^ 3 - a ^ 3 := cube_sub_pos h.a_pos hbpos h.a_lt_b
  have har3 : 0 < r ^ 3 - a ^ 3 := cube_sub_pos h.a_pos hrpos har
  have hbr3 : 0 < b ^ 3 - r ^ 3 := cube_sub_pos hrpos hbpos hrb
  have hscale := secant_scaled h.a_pos hbpos h.a_lt_b
  have hchord : m4 < a ^ 4 + (m3 - a ^ 3) * secant a b := by
    rw [secant_eq_ratio (ne_of_lt h.a_lt_b) (denominator_pos h.a_pos hbpos).ne']
    simpa only [mul_div_assoc] using h.upper
  have hleft : secant a r < (m4 - a ^ 4) / (m3 - a ^ 3) := by
    rw [secant_eq_ratio (ne_of_lt har) (denominator_pos h.a_pos hrpos).ne']
    conv_rhs => rw [← hr3]
    exact div_lt_div_of_pos_right
      (show r ^ 4 - a ^ 4 < m4 - a ^ 4 by dsimp [r]; linarith only [hr4]) har3
  have hright : (m4 - a ^ 4) / (m3 - a ^ 3) < secant a b := by
    exact (div_lt_iff₀ hma).2 (by linarith)
  have hupperleft : secant b a < (b ^ 4 - m4) / (b ^ 3 - m3) := by
    rw [← secant_symm h.a_pos h.a_lt_b]
    apply (lt_div_iff₀ hbm).2
    calc
      secant a b * (b ^ 3 - m3) =
          (b ^ 3 - a ^ 3) * secant a b - (m3 - a ^ 3) * secant a b := by ring
      _ = (b ^ 4 - a ^ 4) - (m3 - a ^ 3) * secant a b := by rw [hscale]
      _ < b ^ 4 - m4 := by linarith only [hchord]
  have hupperright : (b ^ 4 - m4) / (b ^ 3 - m3) < secant b r := by
    rw [secant_eq_ratio (ne_of_gt hrb) (denominator_pos hbpos hrpos).ne']
    conv_lhs => rw [← hr3]
    have hbr4 : 0 < b ^ 4 - r ^ 4 := quartic_sub_pos hrpos hbpos hrb
    have hbr3' : r ^ 3 - b ^ 3 ≠ 0 := by nlinarith
    rw [show (r ^ 4 - b ^ 4) / (r ^ 3 - b ^ 3) =
      (b ^ 4 - r ^ 4) / (b ^ 3 - r ^ 3) by
        apply (div_eq_div_iff hbr3' hbr3.ne').2; ring]
    exact div_lt_div_of_pos_right (by linarith) hbr3
  exact ⟨hleft, hright, hupperleft, hupperright⟩

theorem secant_continuousOn {a l u : ℝ} (ha : 0 < a) (hl : 0 < l) (_hlu : l ≤ u) :
    ContinuousOn (secant a) (Set.Icc l u) := by
  unfold secant
  apply ContinuousOn.div₀ (by fun_prop) (by fun_prop)
  intro x hx
  exact (denominator_pos ha (lt_of_lt_of_le hl hx.1)).ne'

theorem lower_node_existsUnique {a b m3 m4 : ℝ} (h : StrictInterior a b m3 m4) :
    ∃! u : ℝ, positiveCubeRoot m3 < u ∧ u < b ∧
      (u ^ 4 - a ^ 4) / (u ^ 3 - a ^ 3) = (m4 - a ^ 4) / (m3 - a ^ 3) := by
  let r := positiveCubeRoot m3
  obtain ⟨hrpos, _, har, hrb, _⟩ := root_properties h
  obtain ⟨hlo, hhi, _, _⟩ := strict_brackets h
  have hc := secant_continuousOn h.a_pos hrpos hrb.le
  obtain ⟨u, hu, hueq⟩ :=
    (intermediate_value_Ioo hrb.le hc) (show (m4 - a ^ 4) / (m3 - a ^ 3) ∈
      Set.Ioo (secant a r) (secant a b) from ⟨hlo, hhi⟩)
  have huapos : 0 < u := lt_trans hrpos hu.1
  have hau : a < u := lt_trans har hu.1
  have hratio : (u ^ 4 - a ^ 4) / (u ^ 3 - a ^ 3) =
      (m4 - a ^ 4) / (m3 - a ^ 3) := by
    rw [← secant_eq_ratio (ne_of_lt hau) (denominator_pos h.a_pos huapos).ne']
    exact hueq
  refine ⟨u, ⟨hu.1, hu.2, hratio⟩, ?_⟩
  intro v hv
  have hvpos : 0 < v := lt_trans hrpos hv.1
  have hav : a < v := lt_trans har hv.1
  have hveq : secant a v = (m4 - a ^ 4) / (m3 - a ^ 3) := by
    rw [secant_eq_ratio (ne_of_lt hav) (denominator_pos h.a_pos hvpos).ne']
    exact hv.2.2
  exact (secant_strictMonoOn h.a_pos).injOn
    (show u ∈ Set.Ioi 0 from huapos) (show v ∈ Set.Ioi 0 from hvpos)
    (hueq.trans hveq.symm) |>.symm

theorem upper_node_existsUnique {a b m3 m4 : ℝ} (h : StrictInterior a b m3 m4) :
    ∃! d : ℝ, a < d ∧ d < positiveCubeRoot m3 ∧
      (b ^ 4 - d ^ 4) / (b ^ 3 - d ^ 3) = (b ^ 4 - m4) / (b ^ 3 - m3) := by
  let r := positiveCubeRoot m3
  obtain ⟨hrpos, _, har, hrb, _⟩ := root_properties h
  have hbpos : 0 < b := lt_trans h.a_pos h.a_lt_b
  obtain ⟨_, _, hlo, hhi⟩ := strict_brackets h
  have hc := secant_continuousOn hbpos h.a_pos har.le
  obtain ⟨d, hd, hdeq⟩ :=
    (intermediate_value_Ioo har.le hc) (show (b ^ 4 - m4) / (b ^ 3 - m3) ∈
      Set.Ioo (secant b a) (secant b r) from ⟨hlo, hhi⟩)
  have hdpos : 0 < d := lt_trans h.a_pos hd.1
  have hdb : d < b := lt_trans hd.2 hrb
  have hratio : (b ^ 4 - d ^ 4) / (b ^ 3 - d ^ 3) =
      (b ^ 4 - m4) / (b ^ 3 - m3) := by
    rw [← secant_eq_reversed_ratio hdpos hbpos hdb]
    exact hdeq
  refine ⟨d, ⟨hd.1, hd.2, hratio⟩, ?_⟩
  intro e he
  have hepos : 0 < e := lt_trans h.a_pos he.1
  have heb : e < b := lt_trans he.2.1 hrb
  have heeq : secant b e = (b ^ 4 - m4) / (b ^ 3 - m3) := by
    rw [secant_eq_reversed_ratio hepos hbpos heb]
    exact he.2.2
  exact (secant_strictMonoOn hbpos).injOn
    (show d ∈ Set.Ioi 0 from hdpos) (show e ∈ Set.Ioi 0 from hepos)
    (hdeq.trans heeq.symm) |>.symm

noncomputable def lowerWeight (a m3 u : ℝ) : ℝ := (m3 - a ^ 3) / (u ^ 3 - a ^ 3)
noncomputable def upperWeight (b m3 d : ℝ) : ℝ := (m3 - d ^ 3) / (b ^ 3 - d ^ 3)

theorem lower_weight_moments {a b m3 m4 u : ℝ}
    (h : StrictInterior a b m3 m4)
    (hu : positiveCubeRoot m3 < u ∧ u < b ∧
      (u ^ 4 - a ^ 4) / (u ^ 3 - a ^ 3) = (m4 - a ^ 4) / (m3 - a ^ 3)) :
    let w := lowerWeight a m3 u
    0 < w ∧ w < 1 ∧ (1 - w) + w = 1 ∧
      (1 - w) * a ^ 3 + w * u ^ 3 = m3 ∧
      (1 - w) * a ^ 4 + w * u ^ 4 = m4 := by
  dsimp only
  obtain ⟨hrpos, hr3, har, _, _⟩ := root_properties h
  have huapos : 0 < u := lt_trans hrpos hu.1
  have hau : a < u := lt_trans har hu.1
  have hden : 0 < u ^ 3 - a ^ 3 := cube_sub_pos h.a_pos huapos hau
  have hnum : 0 < m3 - a ^ 3 := sub_pos.mpr h.a3_lt_m3
  have hmu : m3 < u ^ 3 := by
    have hp := cube_sub_pos hrpos huapos hu.1
    linarith only [hp, hr3]
  have hwpos : 0 < lowerWeight a m3 u := div_pos hnum hden
  have hwlt : lowerWeight a m3 u < 1 := by
    unfold lowerWeight
    exact (div_lt_one hden).2 (by linarith only [hmu])
  have hcross := (div_eq_div_iff hden.ne' hnum.ne').mp hu.2.2
  have hm3 : (1 - lowerWeight a m3 u) * a ^ 3 +
      lowerWeight a m3 u * u ^ 3 = m3 := by
    unfold lowerWeight
    field_simp [hden.ne']
    ring
  have hm4 : (1 - lowerWeight a m3 u) * a ^ 4 +
      lowerWeight a m3 u * u ^ 4 = m4 := by
    unfold lowerWeight
    field_simp [hden.ne']
    nlinarith only [hcross]
  exact ⟨hwpos, hwlt, by ring, hm3, hm4⟩

theorem upper_weight_moments {a b m3 m4 d : ℝ}
    (h : StrictInterior a b m3 m4)
    (hd : a < d ∧ d < positiveCubeRoot m3 ∧
      (b ^ 4 - d ^ 4) / (b ^ 3 - d ^ 3) = (b ^ 4 - m4) / (b ^ 3 - m3)) :
    let w := upperWeight b m3 d
    0 < w ∧ w < 1 ∧ (1 - w) + w = 1 ∧
      (1 - w) * d ^ 3 + w * b ^ 3 = m3 ∧
      (1 - w) * d ^ 4 + w * b ^ 4 = m4 := by
  dsimp only
  obtain ⟨hrpos, hr3, _, hrb, _⟩ := root_properties h
  have hbpos : 0 < b := lt_trans h.a_pos h.a_lt_b
  have hdpos : 0 < d := lt_trans h.a_pos hd.1
  have hdb : d < b := lt_trans hd.2.1 hrb
  have hden : 0 < b ^ 3 - d ^ 3 := cube_sub_pos hdpos hbpos hdb
  have hbm : 0 < b ^ 3 - m3 := sub_pos.mpr h.m3_lt_b3
  have hdm : d ^ 3 < m3 := by
    have hp := cube_sub_pos hdpos hrpos hd.2.1
    linarith only [hp, hr3]
  have hnum : 0 < m3 - d ^ 3 := sub_pos.mpr hdm
  have hwpos : 0 < upperWeight b m3 d := div_pos hnum hden
  have hwlt : upperWeight b m3 d < 1 := by
    unfold upperWeight
    exact (div_lt_one hden).2 (by linarith only [h.m3_lt_b3])
  have hcross := (div_eq_div_iff hden.ne' hbm.ne').mp hd.2.2
  have hm3 : (1 - upperWeight b m3 d) * d ^ 3 +
      upperWeight b m3 d * b ^ 3 = m3 := by
    unfold upperWeight
    field_simp [hden.ne']
    ring
  have hm4 : (1 - upperWeight b m3 d) * d ^ 4 +
      upperWeight b m3 d * b ^ 4 = m4 := by
    unfold upperWeight
    field_simp [hden.ne']
    nlinarith only [hcross]
  exact ⟨hwpos, hwlt, by ring, hm3, hm4⟩

/- Boundary measures are represented directly as finite atomic measures.  In
particular, their definitions do not evaluate an interior node ratio at 0/0. -/
inductive AtomicMeasure where
  | dirac (x : ℝ)
  | pair (x y weightAtY : ℝ)

def AtomicMeasure.mass : AtomicMeasure → ℝ
  | .dirac _ => 1
  | .pair _ _ w => (1 - w) + w

def AtomicMeasure.moment (p : ℕ) : AtomicMeasure → ℝ
  | .dirac x => x ^ p
  | .pair x y w => (1 - w) * x ^ p + w * y ^ p

noncomputable def chordWeight (a b m3 : ℝ) : ℝ :=
  (m3 - a ^ 3) / (b ^ 3 - a ^ 3)

theorem dirac_boundary {a b m3 m4 : ℝ} (ha : 0 < a) (hab : a < b)
    (ham : a ^ 3 < m3) (hmb : m3 < b ^ 3)
    (hboundary : m4 = m3 ^ ((4 : ℝ) / 3)) :
    let r := positiveCubeRoot m3
    a < r ∧ r < b ∧
      (AtomicMeasure.dirac r).mass = 1 ∧
      (AtomicMeasure.dirac r).moment 3 = m3 ∧
      (AtomicMeasure.dirac r).moment 4 = m4 := by
  dsimp only
  obtain ⟨_, hr3, har, hrb⟩ := root_between ha hab ham hmb
  have hmpos : 0 < m3 := lt_trans (pow_pos ha 3) ham
  simp only [AtomicMeasure.mass, AtomicMeasure.moment]
  exact ⟨har, hrb, trivial, hr3, (positiveCubeRoot_fourth hmpos.le).trans hboundary.symm⟩

theorem chord_boundary {a b m3 m4 : ℝ} (ha : 0 < a) (hab : a < b)
    (ham : a ^ 3 < m3) (hmb : m3 < b ^ 3)
    (hboundary : m4 = a ^ 4 + (m3 - a ^ 3) *
      (b ^ 4 - a ^ 4) / (b ^ 3 - a ^ 3)) :
    let w := chordWeight a b m3
    0 < w ∧ w < 1 ∧
      (AtomicMeasure.pair a b w).mass = 1 ∧
      (AtomicMeasure.pair a b w).moment 3 = m3 ∧
      (AtomicMeasure.pair a b w).moment 4 = m4 := by
  dsimp only
  have hbpos : 0 < b := lt_trans ha hab
  have hden : 0 < b ^ 3 - a ^ 3 := cube_sub_pos ha hbpos hab
  have hnum : 0 < m3 - a ^ 3 := sub_pos.mpr ham
  have hwpos : 0 < chordWeight a b m3 := div_pos hnum hden
  have hwlt : chordWeight a b m3 < 1 := by
    unfold chordWeight
    exact (div_lt_one hden).2 (by linarith only [hmb])
  have hm3 : (AtomicMeasure.pair a b (chordWeight a b m3)).moment 3 = m3 := by
    simp only [AtomicMeasure.moment, chordWeight]
    field_simp [hden.ne']
    ring
  have hm4 : (AtomicMeasure.pair a b (chordWeight a b m3)).moment 4 = m4 := by
    simp only [AtomicMeasure.moment, chordWeight]
    rw [hboundary]
    field_simp [hden.ne']
    ring
  exact ⟨hwpos, hwlt, by simp [AtomicMeasure.mass], hm3, hm4⟩

theorem left_endpoint_dirac {a m3 m4 : ℝ} (hm3 : m3 = a ^ 3) (hm4 : m4 = a ^ 4) :
    (AtomicMeasure.dirac a).mass = 1 ∧
    (AtomicMeasure.dirac a).moment 3 = m3 ∧
    (AtomicMeasure.dirac a).moment 4 = m4 := by
  simp [AtomicMeasure.mass, AtomicMeasure.moment, hm3, hm4]

theorem right_endpoint_dirac {b m3 m4 : ℝ} (hm3 : m3 = b ^ 3) (hm4 : m4 = b ^ 4) :
    (AtomicMeasure.dirac b).mass = 1 ∧
    (AtomicMeasure.dirac b).moment 3 = m3 ∧
    (AtomicMeasure.dirac b).moment 4 = m4 := by
  simp [AtomicMeasure.mass, AtomicMeasure.moment, hm3, hm4]

theorem chord_left_endpoint {a b : ℝ} (ha : 0 < a) (hab : a < b) :
    chordWeight a b (a ^ 3) = 0 := by
  have hbpos : 0 < b := lt_trans ha hab
  unfold chordWeight
  simp

theorem chord_right_endpoint {a b : ℝ} (ha : 0 < a) (hab : a < b) :
    chordWeight a b (b ^ 3) = 1 := by
  have hbpos : 0 < b := lt_trans ha hab
  unfold chordWeight
  exact div_self (cube_sub_pos ha hbpos hab).ne'

#print axioms secant_deriv
#print axioms secant_deriv_pos
#print axioms secant_strictMonoOn
#print axioms root_properties
#print axioms strict_brackets
#print axioms lower_node_existsUnique
#print axioms upper_node_existsUnique
#print axioms lower_weight_moments
#print axioms upper_weight_moments
#print axioms dirac_boundary
#print axioms chord_boundary
#print axioms left_endpoint_dirac
#print axioms right_endpoint_dirac
#print axioms chord_left_endpoint
#print axioms chord_right_endpoint

end CAS13C02
