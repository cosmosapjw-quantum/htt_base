/- Source-bound bridge. Each source body below is copied verbatim after its
leading import Mathlib is hoisted to this common import. Frozen source SHA256:
TwoNode.lean b16745f7af4f88cb7d923ddb34da1b83e8b564ab42bcfe3e7e750779106d3d7d
CAS13C03.lean e6f90afbfe4c6b9675458594dc5d1936be141b8bccf1bf8b75c3ad63d3f2a455
MeasureComposition.lean 02f09b7f8ec332418d002a80e8f6b1f292a203ada30e01645f940eee9c0df56b -/
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


namespace CAS13C03

def delta (A U : ℝ) : ℝ := 3*A^2 + 2*A*U + U^2

noncomputable def c05 (A U : ℝ) : ℝ := A^3*U^4 / delta A U
noncomputable def c35 (A U : ℝ) : ℝ := -(U*(U^3+2*A*U^2+3*A^2*U+4*A^3)) / delta A U
noncomputable def c45 (A U : ℝ) : ℝ := (2*U^3+4*A*U^2+6*A^2*U+3*A^3) / delta A U
noncomputable def q5 (A U y : ℝ) : ℝ := c05 A U + c35 A U*y^3 + c45 A U*y^4
noncomputable def q5prime (A U y : ℝ) : ℝ := 3*c35 A U*y^2 + 4*c45 A U*y^3

noncomputable def c06 (A U : ℝ) : ℝ := A^3*U^4*(A+2*U) / delta A U
noncomputable def c36 (A U : ℝ) : ℝ := -(2*U*(U^4+2*A*U^3+3*A^2*U^2+4*A^3*U+2*A^4)) / delta A U
noncomputable def c46 (A U : ℝ) : ℝ := 3*(U^2+A*U+A^2)^2 / delta A U
noncomputable def q6 (A U y : ℝ) : ℝ := c06 A U + c36 A U*y^3 + c46 A U*y^4
noncomputable def q6prime (A U y : ℝ) : ℝ := 3*c36 A U*y^2 + 4*c46 A U*y^3

def p5 (A U y : ℝ) : ℝ := delta A U*y^2 + (2*A^2*U+A*U^2)*y + A^2*U^2
def p6 (A U y : ℝ) : ℝ := delta A U*y^3 +
  (3*A^3+8*A^2*U+5*A*U^2+2*U^3)*y^2 +
  (2*A^3*U+5*A^2*U^2+2*A*U^3)*y + A^3*U^2+2*A^2*U^3

private theorem delta_pos {A U : ℝ} (hA : 0 < A) (hU : 0 < U) : 0 < delta A U := by
  unfold delta
  positivity

private theorem delta_ne {A U : ℝ} (hA : 0 < A) (hU : 0 < U) : delta A U ≠ 0 :=
  ne_of_gt (delta_pos hA hU)

theorem p5_identity {A U : ℝ} (hA : 0 < A) (hU : 0 < U) (y : ℝ) :
    delta A U * (y^5 - q5 A U y) = (y-A)*(y-U)^2*p5 A U y := by
  unfold q5 c05 c35 c45 p5
  field_simp [delta_ne hA hU]
  unfold delta
  ring

theorem p6_identity {A U : ℝ} (hA : 0 < A) (hU : 0 < U) (y : ℝ) :
    delta A U * (y^6 - q6 A U y) = (y-A)*(y-U)^2*p6 A U y := by
  unfold q6 c06 c36 c46 p6
  field_simp [delta_ne hA hU]
  unfold delta
  ring

theorem q5_at_A {A U : ℝ} (hA : 0 < A) (hU : 0 < U) : q5 A U A = A^5 := by
  have hf := p5_identity hA hU A
  have hd := delta_pos hA hU
  simp only [sub_self, zero_mul] at hf
  nlinarith

theorem q5_at_U {A U : ℝ} (hA : 0 < A) (hU : 0 < U) : q5 A U U = U^5 := by
  have hf := p5_identity hA hU U
  have hd := delta_pos hA hU
  simp only [sub_self, zero_pow (by decide : 2 ≠ 0), mul_zero, zero_mul] at hf
  nlinarith

theorem q6_at_A {A U : ℝ} (hA : 0 < A) (hU : 0 < U) : q6 A U A = A^6 := by
  have hf := p6_identity hA hU A
  have hd := delta_pos hA hU
  simp only [sub_self, zero_mul] at hf
  nlinarith

theorem q6_at_U {A U : ℝ} (hA : 0 < A) (hU : 0 < U) : q6 A U U = U^6 := by
  have hf := p6_identity hA hU U
  have hd := delta_pos hA hU
  simp only [sub_self, zero_pow (by decide : 2 ≠ 0), mul_zero, zero_mul] at hf
  nlinarith

theorem q5prime_at_U {A U : ℝ} (hA : 0 < A) (hU : 0 < U) :
    q5prime A U U = 5*U^4 := by
  unfold q5prime c35 c45
  field_simp [delta_ne hA hU]
  unfold delta
  ring

theorem q6prime_at_U {A U : ℝ} (hA : 0 < A) (hU : 0 < U) :
    q6prime A U U = 6*U^5 := by
  unfold q6prime c36 c46
  field_simp [delta_ne hA hU]
  unfold delta
  ring

theorem q5_hasDerivAt (A U y : ℝ) : HasDerivAt (q5 A U) (q5prime A U y) y := by
  have h3 : HasDerivAt (fun t : ℝ => t^3) (3*y^2) y := by
    simpa using (hasDerivAt_pow 3 y)
  have h4 : HasDerivAt (fun t : ℝ => t^4) (4*y^3) y := by
    simpa using (hasDerivAt_pow 4 y)
  have h := ((hasDerivAt_const y (c05 A U)).add
    (h3.const_mul (c35 A U))).add (h4.const_mul (c45 A U))
  have hfun : ((fun _ : ℝ => c05 A U) + (fun z => c35 A U*z^3) +
      (fun z => c45 A U*z^4)) = q5 A U := by
    funext z
    simp [q5, Pi.add_apply]
  rw [hfun] at h
  simpa [q5prime, mul_assoc, mul_comm, mul_left_comm] using h

theorem q6_hasDerivAt (A U y : ℝ) : HasDerivAt (q6 A U) (q6prime A U y) y := by
  have h3 : HasDerivAt (fun t : ℝ => t^3) (3*y^2) y := by
    simpa using (hasDerivAt_pow 3 y)
  have h4 : HasDerivAt (fun t : ℝ => t^4) (4*y^3) y := by
    simpa using (hasDerivAt_pow 4 y)
  have h := ((hasDerivAt_const y (c06 A U)).add
    (h3.const_mul (c36 A U))).add (h4.const_mul (c46 A U))
  have hfun : ((fun _ : ℝ => c06 A U) + (fun z => c36 A U*z^3) +
      (fun z => c46 A U*z^4)) = q6 A U := by
    funext z
    simp [q6, Pi.add_apply]
  rw [hfun] at h
  simpa [q6prime, mul_assoc, mul_comm, mul_left_comm] using h

theorem q5_two_node (A U w : ℝ) (hA : 0 < A) (hU : 0 < U) :
    (1-w)*A^5+w*U^5 = c05 A U +
      c35 A U*((1-w)*A^3+w*U^3) +
      c45 A U*((1-w)*A^4+w*U^4) := by
  have ha := q5_at_A hA hU
  have hu := q5_at_U hA hU
  unfold q5 at ha hu
  linear_combination -(1-w)*ha-w*hu

theorem q6_two_node (A U w : ℝ) (hA : 0 < A) (hU : 0 < U) :
    (1-w)*A^6+w*U^6 = c06 A U +
      c36 A U*((1-w)*A^3+w*U^3) +
      c46 A U*((1-w)*A^4+w*U^4) := by
  have ha := q6_at_A hA hU
  have hu := q6_at_U hA hU
  unfold q6 at ha hu
  linear_combination -(1-w)*ha-w*hu

theorem q5_two_node_fixed_moments (A U w m3 m4 : ℝ)
    (hA : 0 < A) (hU : 0 < U)
    (hm3 : (1-w)*A^3+w*U^3 = m3)
    (hm4 : (1-w)*A^4+w*U^4 = m4) :
    (1-w)*A^5+w*U^5 = c05 A U+c35 A U*m3+c45 A U*m4 := by
  rw [← hm3, ← hm4]
  exact q5_two_node A U w hA hU

theorem q6_two_node_fixed_moments (A U w m3 m4 : ℝ)
    (hA : 0 < A) (hU : 0 < U)
    (hm3 : (1-w)*A^3+w*U^3 = m3)
    (hm4 : (1-w)*A^4+w*U^4 = m4) :
    (1-w)*A^6+w*U^6 = c06 A U+c36 A U*m3+c46 A U*m4 := by
  rw [← hm3, ← hm4]
  exact q6_two_node A U w hA hU

theorem integral_q5 (μ : MeasureTheory.Measure ℝ) [MeasureTheory.IsProbabilityMeasure μ]
    (A U : ℝ) (h3 : MeasureTheory.Integrable (fun y : ℝ => y^3) μ)
    (h4 : MeasureTheory.Integrable (fun y : ℝ => y^4) μ) :
    (∫ y, q5 A U y ∂μ) = c05 A U +
      c35 A U*(∫ y : ℝ, y^3 ∂μ) + c45 A U*(∫ y : ℝ, y^4 ∂μ) := by
  have hc : MeasureTheory.Integrable (fun _ : ℝ => c05 A U) μ := MeasureTheory.integrable_const _
  have hc3 : MeasureTheory.Integrable (fun y : ℝ => c35 A U*y^3) μ := h3.const_mul _
  have hc4 : MeasureTheory.Integrable (fun y : ℝ => c45 A U*y^4) μ := h4.const_mul _
  change (∫ y : ℝ, c05 A U+c35 A U*y^3+c45 A U*y^4 ∂μ) = _
  have hsum : (∫ y : ℝ, c05 A U+c35 A U*y^3+c45 A U*y^4 ∂μ) =
      (∫ y : ℝ, c05 A U+c35 A U*y^3 ∂μ) +
      (∫ y : ℝ, c45 A U*y^4 ∂μ) := by
    simpa only [Pi.add_apply] using (MeasureTheory.integral_add (hc.add hc3) hc4)
  have hinner : (∫ y : ℝ, c05 A U+c35 A U*y^3 ∂μ) =
      (∫ y : ℝ, c05 A U ∂μ) + (∫ y : ℝ, c35 A U*y^3 ∂μ) := by
    simpa only [Pi.add_apply] using (MeasureTheory.integral_add hc hc3)
  rw [hsum, hinner]
  simp only [MeasureTheory.integral_const_mul]
  simp

theorem integral_q6 (μ : MeasureTheory.Measure ℝ) [MeasureTheory.IsProbabilityMeasure μ]
    (A U : ℝ) (h3 : MeasureTheory.Integrable (fun y : ℝ => y^3) μ)
    (h4 : MeasureTheory.Integrable (fun y : ℝ => y^4) μ) :
    (∫ y, q6 A U y ∂μ) = c06 A U +
      c36 A U*(∫ y : ℝ, y^3 ∂μ) + c46 A U*(∫ y : ℝ, y^4 ∂μ) := by
  have hc : MeasureTheory.Integrable (fun _ : ℝ => c06 A U) μ := MeasureTheory.integrable_const _
  have hc3 : MeasureTheory.Integrable (fun y : ℝ => c36 A U*y^3) μ := h3.const_mul _
  have hc4 : MeasureTheory.Integrable (fun y : ℝ => c46 A U*y^4) μ := h4.const_mul _
  change (∫ y : ℝ, c06 A U+c36 A U*y^3+c46 A U*y^4 ∂μ) = _
  have hsum : (∫ y : ℝ, c06 A U+c36 A U*y^3+c46 A U*y^4 ∂μ) =
      (∫ y : ℝ, c06 A U+c36 A U*y^3 ∂μ) +
      (∫ y : ℝ, c46 A U*y^4 ∂μ) := by
    simpa only [Pi.add_apply] using (MeasureTheory.integral_add (hc.add hc3) hc4)
  have hinner : (∫ y : ℝ, c06 A U+c36 A U*y^3 ∂μ) =
      (∫ y : ℝ, c06 A U ∂μ) + (∫ y : ℝ, c36 A U*y^3 ∂μ) := by
    simpa only [Pi.add_apply] using (MeasureTheory.integral_add hc hc3)
  rw [hsum, hinner]
  simp only [MeasureTheory.integral_const_mul]
  simp

theorem hermite_unique {A U vA vU derivU : ℝ} (hA : 0 < A) (hAU : A < U)
    {c0 c3 c4 d0 d3 d4 : ℝ}
    (hcA : c0+c3*A^3+c4*A^4 = vA)
    (hcU : c0+c3*U^3+c4*U^4 = vU)
    (hcD : 3*c3*U^2+4*c4*U^3 = derivU)
    (hdA : d0+d3*A^3+d4*A^4 = vA)
    (hdU : d0+d3*U^3+d4*U^4 = vU)
    (hdD : 3*d3*U^2+4*d4*U^3 = derivU) :
    c0 = d0 ∧ c3 = d3 ∧ c4 = d4 := by
  let x0 := c0-d0
  let x3 := c3-d3
  let x4 := c4-d4
  have h1 : x3*(U^3-A^3)+x4*(U^4-A^4) = 0 := by
    dsimp [x3, x4]
    linear_combination (hcU-hdU)-(hcA-hdA)
  have h2 : 3*x3*U^2+4*x4*U^3 = 0 := by
    dsimp [x3, x4]
    linear_combination hcD-hdD
  have hdet : 0 < U^2*(U-A)^2*delta A U := by
    have hU : 0 < U := lt_trans hA hAU
    have hdiff : 0 < U-A := sub_pos.mpr hAU
    have hΔ := delta_pos hA hU
    positivity
  have hdet_eq : 4*U^3*(U^3-A^3)-3*U^2*(U^4-A^4) =
      U^2*(U-A)^2*delta A U := by
    unfold delta
    ring
  have hx4 : x4*(U^2*(U-A)^2*delta A U) = 0 := by
    calc
      _ = (U^3-A^3)*(3*x3*U^2+4*x4*U^3) -
          3*U^2*(x3*(U^3-A^3)+x4*(U^4-A^4)) := by rw [← hdet_eq]; ring
      _ = 0 := by rw [h1, h2]; ring
  have hx4zero : x4 = 0 := (mul_eq_zero.mp hx4).resolve_right (ne_of_gt hdet)
  have hU : 0 < U := lt_trans hA hAU
  have hx3zero : x3 = 0 := by
    rw [hx4zero] at h2
    have hu2 : 0 < U^2 := by positivity
    nlinarith
  have hx0zero : x0 = 0 := by
    have h0 : x0+x3*A^3+x4*A^4 = 0 := by
      dsimp [x0, x3, x4]
      linear_combination hcA-hdA
    rw [hx3zero, hx4zero] at h0
    simpa using h0
  dsimp [x0] at hx0zero
  dsimp [x3] at hx3zero
  dsimp [x4] at hx4zero
  exact ⟨sub_eq_zero.mp hx0zero, sub_eq_zero.mp hx3zero, sub_eq_zero.mp hx4zero⟩

theorem q5_coeff_unique {A U : ℝ} (hA : 0 < A) (hAU : A < U)
    {e0 e3 e4 : ℝ}
    (hA5 : e0+e3*A^3+e4*A^4 = A^5)
    (hU5 : e0+e3*U^3+e4*U^4 = U^5)
    (hD5 : 3*e3*U^2+4*e4*U^3 = 5*U^4) :
    e0 = c05 A U ∧ e3 = c35 A U ∧ e4 = c45 A U := by
  have hU : 0 < U := lt_trans hA hAU
  apply hermite_unique hA hAU hA5 hU5 hD5
  · simpa [q5] using q5_at_A hA hU
  · simpa [q5] using q5_at_U hA hU
  · simpa [q5prime] using q5prime_at_U hA hU

theorem q6_coeff_unique {A U : ℝ} (hA : 0 < A) (hAU : A < U)
    {e0 e3 e4 : ℝ}
    (hA6 : e0+e3*A^3+e4*A^4 = A^6)
    (hU6 : e0+e3*U^3+e4*U^4 = U^6)
    (hD6 : 3*e3*U^2+4*e4*U^3 = 6*U^5) :
    e0 = c06 A U ∧ e3 = c36 A U ∧ e4 = c46 A U := by
  have hU : 0 < U := lt_trans hA hAU
  apply hermite_unique hA hAU hA6 hU6 hD6
  · simpa [q6] using q6_at_A hA hU
  · simpa [q6] using q6_at_U hA hU
  · simpa [q6prime] using q6prime_at_U hA hU

theorem p5_boundary_polynomial {A y : ℝ} (hA : 0 < A) :
    delta A A*(y^5-q5 A A y) = (y-A)^3*p5 A A y := by
  convert p5_identity hA hA y using 1; ring

theorem p6_boundary_polynomial {A y : ℝ} (hA : 0 < A) :
    delta A A*(y^6-q6 A A y) = (y-A)^3*p6 A A y := by
  convert p6_identity hA hA y using 1; ring

theorem p5_pos {A U y : ℝ} (hA : 0 < A) (hU : 0 < U) (hy : 0 ≤ y) :
    0 < p5 A U y := by
  have hd := delta_pos hA hU
  have h1 : 0 ≤ 2*A^2*U+A*U^2 := by positivity
  have h2 : 0 < A^2*U^2 := by positivity
  unfold p5
  positivity

theorem p6_pos {A U y : ℝ} (hA : 0 < A) (hU : 0 < U) (hy : 0 ≤ y) :
    0 < p6 A U y := by
  have hd := delta_pos hA hU
  unfold p6
  positivity

theorem lower5 {a u y : ℝ} (ha : 0 < a) (hau : a < u) (hay : a ≤ y) :
    q5 a u y ≤ y^5 := by
  have hu : 0 < u := lt_trans ha hau
  have hp := p5_pos ha hu (le_trans (le_of_lt ha) hay)
  have hf := p5_identity ha hu y
  have hs : 0 ≤ (y-a)*(y-u)^2*p5 a u y := by positivity
  have hd := delta_pos ha hu
  nlinarith

theorem lower6 {a u y : ℝ} (ha : 0 < a) (hau : a < u) (hay : a ≤ y) :
    q6 a u y ≤ y^6 := by
  have hu : 0 < u := lt_trans ha hau
  have hp := p6_pos ha hu (le_trans (le_of_lt ha) hay)
  have hf := p6_identity ha hu y
  have hs : 0 ≤ (y-a)*(y-u)^2*p6 a u y := by positivity
  have hd := delta_pos ha hu
  nlinarith

theorem upper5 {b d y : ℝ} (hd : 0 < d) (hdb : d < b) (hyb : y ≤ b) (hy : 0 ≤ y) :
    y^5 ≤ q5 b d y := by
  have hb : 0 < b := lt_trans hd hdb
  have hp := p5_pos hb hd hy
  have hf := p5_identity hb hd y
  have hs : (y-b)*(y-d)^2*p5 b d y ≤ 0 := by
    have hs' : 0 ≤ (b-y)*(y-d)^2*p5 b d y := by positivity
    nlinarith
  have hΔ := delta_pos hb hd
  nlinarith

theorem upper6 {b d y : ℝ} (hd : 0 < d) (hdb : d < b) (hyb : y ≤ b) (hy : 0 ≤ y) :
    y^6 ≤ q6 b d y := by
  have hb : 0 < b := lt_trans hd hdb
  have hp := p6_pos hb hd hy
  have hf := p6_identity hb hd y
  have hs : (y-b)*(y-d)^2*p6 b d y ≤ 0 := by
    have hs' : 0 ≤ (b-y)*(y-d)^2*p6 b d y := by positivity
    nlinarith
  have hΔ := delta_pos hb hd
  nlinarith

end CAS13C03

#print axioms CAS13C03.p5_identity
#print axioms CAS13C03.p6_identity
#print axioms CAS13C03.q5_coeff_unique
#print axioms CAS13C03.q6_coeff_unique
#print axioms CAS13C03.q5_hasDerivAt
#print axioms CAS13C03.q6_hasDerivAt
#print axioms CAS13C03.p5_pos
#print axioms CAS13C03.p6_pos
#print axioms CAS13C03.lower5
#print axioms CAS13C03.lower6
#print axioms CAS13C03.upper5
#print axioms CAS13C03.upper6
#print axioms CAS13C03.integral_q5
#print axioms CAS13C03.integral_q6
#print axioms CAS13C03.q5_two_node_fixed_moments
#print axioms CAS13C03.q6_two_node_fixed_moments
#print axioms CAS13C03.p5_boundary_polynomial
#print axioms CAS13C03.p6_boundary_polynomial


/-!
Conditional CAS13 measure composition. C02 feasibility and C03 Hermite sign/contact
facts are hypotheses; their polynomial derivations are not reproved here. All
integrals below are actual real Bochner integrals against measures on ℝ. No C04
relative-minimax result or scientific admission is used or asserted.
-/

noncomputable section
open MeasureTheory
open scoped ENNReal

namespace CAS13MeasureComposition

def hermite (c0 c3 c4 x : ℝ) : ℝ := c0 + c3 * x ^ 3 + c4 * x ^ 4

def moment (μ : Measure ℝ) (p : ℕ) : ℝ := ∫ x : ℝ, x ^ p ∂μ

/-- The weight `w` belongs to the second node; `1-w` belongs to the first. -/
def twoDirac (w a u : ℝ) : Measure ℝ :=
  ENNReal.ofReal (1 - w) • Measure.dirac a + ENNReal.ofReal w • Measure.dirac u

theorem twoDirac_probability {w a u : ℝ} (hw0 : 0 ≤ w) (hw1 : w ≤ 1) :
    IsProbabilityMeasure (twoDirac w a u) := by
  constructor
  simp only [twoDirac, Measure.add_apply, Measure.smul_apply, Measure.dirac_apply_of_mem,
    Set.mem_univ, smul_eq_mul, mul_one]
  rw [← ENNReal.ofReal_add (sub_nonneg.mpr hw1) hw0]
  simp

/-- All real-valued functions have finite integrals on this finite-support measure. -/
theorem integrable_twoDirac (f : ℝ → ℝ) (w a u : ℝ) :
    Integrable f (twoDirac w a u) := by
  have ha : Integrable f (Measure.dirac a) := integrable_dirac (by simp)
  have hu : Integrable f (Measure.dirac u) := integrable_dirac (by simp)
  exact (ha.smul_measure ENNReal.ofReal_ne_top).add_measure
    (hu.smul_measure ENNReal.ofReal_ne_top)

theorem integral_twoDirac (f : ℝ → ℝ) {w a u : ℝ}
    (hw0 : 0 ≤ w) (hw1 : w ≤ 1) :
    (∫ x, f x ∂twoDirac w a u) = (1 - w) * f a + w * f u := by
  have ha : Integrable f (Measure.dirac a) := integrable_dirac (by simp)
  have hu : Integrable f (Measure.dirac u) := integrable_dirac (by simp)
  rw [twoDirac, integral_add_measure (ha.smul_measure ENNReal.ofReal_ne_top)
    (hu.smul_measure ENNReal.ofReal_ne_top)]
  simp only [integral_smul_measure, integral_dirac, ENNReal.toReal_ofReal hw0,
    ENNReal.toReal_ofReal (sub_nonneg.mpr hw1), smul_eq_mul]

theorem moment_twoDirac (p : ℕ) {w a u : ℝ} (hw0 : 0 ≤ w) (hw1 : w ≤ 1) :
    moment (twoDirac w a u) p = (1 - w) * a ^ p + w * u ^ p :=
  integral_twoDirac (fun x => x ^ p) hw0 hw1

theorem twoDirac_supported {w v z a b : ℝ}
    (hv : v ∈ Set.Icc a b) (hz : z ∈ Set.Icc a b) :
    ∀ᵐ x ∂twoDirac w v z, x ∈ Set.Icc a b := by
  rw [twoDirac, ae_add_measure_iff]
  exact ⟨Measure.ae_smul_measure ((ae_dirac_iff measurableSet_Icc).mpr hv) _,
    Measure.ae_smul_measure ((ae_dirac_iff measurableSet_Icc).mpr hz) _⟩

theorem integrable_hermite (μ : Measure ℝ) [IsProbabilityMeasure μ]
    {c0 c3 c4 : ℝ} (h3 : Integrable (fun x : ℝ => x ^ 3) μ)
    (h4 : Integrable (fun x : ℝ => x ^ 4) μ) :
    Integrable (hermite c0 c3 c4) μ :=
  ((integrable_const c0).add (h3.const_mul c3)).add (h4.const_mul c4)

theorem integral_hermite (μ : Measure ℝ) [IsProbabilityMeasure μ]
    {c0 c3 c4 m3 m4 : ℝ} (h3 : Integrable (fun x : ℝ => x ^ 3) μ)
    (h4 : Integrable (fun x : ℝ => x ^ 4) μ)
    (hm3 : moment μ 3 = m3) (hm4 : moment μ 4 = m4) :
    (∫ x, hermite c0 c3 c4 x ∂μ) = c0 + c3 * m3 + c4 * m4 := by
  have hc3 : Integrable (fun x : ℝ => c3 * x ^ 3) μ := h3.const_mul c3
  have hc4 : Integrable (fun x : ℝ => c4 * x ^ 4) μ := h4.const_mul c4
  have hsum : Integrable (fun x : ℝ => c0 + c3 * x ^ 3) μ :=
    (integrable_const c0).add hc3
  simp only [hermite]
  rw [integral_add hsum hc4, integral_add (integrable_const c0) hc3,
    integral_const_mul, integral_const_mul]
  simp only [integral_const, probReal_univ, one_smul]
  change c0 + c3 * moment μ 3 + c4 * moment μ 4 = _
  rw [hm3, hm4]

/-- Transport a pointwise lower Hermite certificate on the supported interval. -/
theorem lower_transport (p : ℕ) (μ : Measure ℝ) [IsProbabilityMeasure μ]
    {a b c0 c3 c4 m3 m4 : ℝ}
    (hsupport : ∀ᵐ x ∂μ, x ∈ Set.Icc a b)
    (h3 : Integrable (fun x : ℝ => x ^ 3) μ)
    (h4 : Integrable (fun x : ℝ => x ^ 4) μ)
    (hp : Integrable (fun x : ℝ => x ^ p) μ)
    (hm3 : moment μ 3 = m3) (hm4 : moment μ 4 = m4)
    (hlower : ∀ x ∈ Set.Icc a b, hermite c0 c3 c4 x ≤ x ^ p) :
    c0 + c3 * m3 + c4 * m4 ≤ moment μ p := by
  rw [← integral_hermite μ h3 h4 hm3 hm4]
  exact integral_mono_ae (integrable_hermite μ h3 h4) hp
    (hsupport.mono (fun x hx => hlower x hx))

/-- Transport a pointwise upper Hermite certificate on the supported interval. -/
theorem upper_transport (p : ℕ) (μ : Measure ℝ) [IsProbabilityMeasure μ]
    {a b c0 c3 c4 m3 m4 : ℝ}
    (hsupport : ∀ᵐ x ∂μ, x ∈ Set.Icc a b)
    (h3 : Integrable (fun x : ℝ => x ^ 3) μ)
    (h4 : Integrable (fun x : ℝ => x ^ 4) μ)
    (hp : Integrable (fun x : ℝ => x ^ p) μ)
    (hm3 : moment μ 3 = m3) (hm4 : moment μ 4 = m4)
    (hupper : ∀ x ∈ Set.Icc a b, x ^ p ≤ hermite c0 c3 c4 x) :
    moment μ p ≤ c0 + c3 * m3 + c4 * m4 := by
  rw [← integral_hermite μ h3 h4 hm3 hm4]
  exact integral_mono_ae hp (integrable_hermite μ h3 h4)
    (hsupport.mono (fun x hx => hupper x hx))

/-- C02 weighted moments and C03 node contacts imply attainment by the actual measure.
No division, node-existence theorem or boundary substitution occurs in this proof. -/
theorem twoDirac_attainment (p : ℕ) {w a u c0 c3 c4 m3 m4 : ℝ}
    (hw0 : 0 ≤ w) (hw1 : w ≤ 1)
    (hm3 : (1 - w) * a ^ 3 + w * u ^ 3 = m3)
    (hm4 : (1 - w) * a ^ 4 + w * u ^ 4 = m4)
    (ha : a ^ p = hermite c0 c3 c4 a)
    (hu : u ^ p = hermite c0 c3 c4 u) :
    moment (twoDirac w a u) p = c0 + c3 * m3 + c4 * m4 := by
  letI := twoDirac_probability (a := a) (u := u) hw0 hw1
  have hmatch3 : moment (twoDirac w a u) 3 = m3 := by
    rw [moment_twoDirac 3 hw0 hw1, hm3]
  have hmatch4 : moment (twoDirac w a u) 4 = m4 := by
    rw [moment_twoDirac 4 hw0 hw1, hm4]
  calc
    moment (twoDirac w a u) p = ∫ x, hermite c0 c3 c4 x ∂twoDirac w a u := by
      rw [moment, integral_twoDirac (fun x : ℝ => x ^ p) hw0 hw1,
        integral_twoDirac (hermite c0 c3 c4) hw0 hw1, ha, hu]
    _ = c0 + c3 * m3 + c4 * m4 := integral_hermite (twoDirac w a u)
      (integrable_twoDirac _ _ _ _) (integrable_twoDirac _ _ _ _) hmatch3 hmatch4

/-- The exact probability, support, finite-moment and moment-matching class. -/
def Admissible (μ : Measure ℝ) (a b m3 m4 : ℝ) (p : ℕ) : Prop :=
  IsProbabilityMeasure μ ∧ (∀ᵐ x ∂μ, x ∈ Set.Icc a b) ∧
    Integrable (fun x : ℝ => x ^ 3) μ ∧ Integrable (fun x : ℝ => x ^ 4) μ ∧
    Integrable (fun x : ℝ => x ^ p) μ ∧ moment μ 3 = m3 ∧ moment μ 4 = m4

theorem twoDirac_admissible (p : ℕ) {w v z a b m3 m4 : ℝ}
    (hw0 : 0 ≤ w) (hw1 : w ≤ 1)
    (hv : v ∈ Set.Icc a b) (hz : z ∈ Set.Icc a b)
    (hm3 : (1 - w) * v ^ 3 + w * z ^ 3 = m3)
    (hm4 : (1 - w) * v ^ 4 + w * z ^ 4 = m4) :
    Admissible (twoDirac w v z) a b m3 m4 p := by
  refine ⟨twoDirac_probability hw0 hw1, twoDirac_supported hv hz,
    integrable_twoDirac _ _ _ _, integrable_twoDirac _ _ _ _,
    integrable_twoDirac _ _ _ _, ?_, ?_⟩
  · rw [moment_twoDirac 3 hw0 hw1, hm3]
  · rw [moment_twoDirac 4 hw0 hw1, hm4]

/-- A lower-bound transport together with its attaining, moment-matched measure. -/
def LowerComposition (p : ℕ) : Prop :=
  ∀ (μ : Measure ℝ), IsProbabilityMeasure μ →
  ∀ (a b v z w c0 c3 c4 m3 m4 : ℝ),
    (∀ᵐ x ∂μ, x ∈ Set.Icc a b) →
    Integrable (fun x : ℝ => x ^ 3) μ →
    Integrable (fun x : ℝ => x ^ 4) μ →
    Integrable (fun x : ℝ => x ^ p) μ →
    moment μ 3 = m3 → moment μ 4 = m4 →
    (∀ x ∈ Set.Icc a b, hermite c0 c3 c4 x ≤ x ^ p) →
    0 ≤ w → w ≤ 1 →
    v ∈ Set.Icc a b → z ∈ Set.Icc a b →
    (1 - w) * v ^ 3 + w * z ^ 3 = m3 →
    (1 - w) * v ^ 4 + w * z ^ 4 = m4 →
    v ^ p = hermite c0 c3 c4 v → z ^ p = hermite c0 c3 c4 z →
    c0 + c3 * m3 + c4 * m4 ≤ moment μ p ∧
      moment (twoDirac w v z) p = c0 + c3 * m3 + c4 * m4 ∧
      Admissible (twoDirac w v z) a b m3 m4 p

/-- The corresponding upper-bound transport and attainment. -/
def UpperComposition (p : ℕ) : Prop :=
  ∀ (μ : Measure ℝ), IsProbabilityMeasure μ →
  ∀ (a b v z w c0 c3 c4 m3 m4 : ℝ),
    (∀ᵐ x ∂μ, x ∈ Set.Icc a b) →
    Integrable (fun x : ℝ => x ^ 3) μ →
    Integrable (fun x : ℝ => x ^ 4) μ →
    Integrable (fun x : ℝ => x ^ p) μ →
    moment μ 3 = m3 → moment μ 4 = m4 →
    (∀ x ∈ Set.Icc a b, x ^ p ≤ hermite c0 c3 c4 x) →
    0 ≤ w → w ≤ 1 →
    v ∈ Set.Icc a b → z ∈ Set.Icc a b →
    (1 - w) * v ^ 3 + w * z ^ 3 = m3 →
    (1 - w) * v ^ 4 + w * z ^ 4 = m4 →
    v ^ p = hermite c0 c3 c4 v → z ^ p = hermite c0 c3 c4 z →
    moment μ p ≤ c0 + c3 * m3 + c4 * m4 ∧
      moment (twoDirac w v z) p = c0 + c3 * m3 + c4 * m4 ∧
      Admissible (twoDirac w v z) a b m3 m4 p

theorem lower_composition (p : ℕ) : LowerComposition p := by
  intro μ hμ a b v z w c0 c3 c4 m3 m4 hs h3 h4 hp hm3 hm4 hl hw0 hw1
    hvs hzs hnode3 hnode4 hv hz
  letI := hμ
  exact ⟨lower_transport p μ hs h3 h4 hp hm3 hm4 hl,
    twoDirac_attainment p hw0 hw1 hnode3 hnode4 hv hz,
    twoDirac_admissible p hw0 hw1 hvs hzs hnode3 hnode4⟩

theorem upper_composition (p : ℕ) : UpperComposition p := by
  intro μ hμ a b v z w c0 c3 c4 m3 m4 hs h3 h4 hp hm3 hm4 hu hw0 hw1
    hvs hzs hnode3 hnode4 hv hz
  letI := hμ
  exact ⟨upper_transport p μ hs h3 h4 hp hm3 hm4 hu,
    twoDirac_attainment p hw0 hw1 hnode3 hnode4 hv hz,
    twoDirac_admissible p hw0 hw1 hvs hzs hnode3 hnode4⟩

theorem p5_lower_composition : LowerComposition 5 := lower_composition 5
theorem p5_upper_composition : UpperComposition 5 := upper_composition 5
theorem p6_lower_composition : LowerComposition 6 := lower_composition 6
theorem p6_upper_composition : UpperComposition 6 := upper_composition 6

theorem p5_p6_measure_composition :
    LowerComposition 5 ∧ UpperComposition 5 ∧ LowerComposition 6 ∧ UpperComposition 6 :=
  ⟨p5_lower_composition, p5_upper_composition, p6_lower_composition, p6_upper_composition⟩

#check twoDirac_probability
#check integral_twoDirac
#check lower_transport
#check upper_transport
#check twoDirac_attainment
#check twoDirac_admissible
#print Admissible
#print LowerComposition
#print UpperComposition
#check p5_p6_measure_composition
#print axioms twoDirac_probability
#print axioms integral_twoDirac
#print axioms lower_transport
#print axioms upper_transport
#print axioms twoDirac_attainment
#print axioms twoDirac_admissible
#print axioms p5_p6_measure_composition

end CAS13MeasureComposition


namespace CAS13MeasureExtremizerBridge
open CAS13MeasureComposition CAS13C03

theorem hermite_q5 (A U x : ℝ) :
    hermite (c05 A U) (c35 A U) (c45 A U) x = q5 A U x := by
  unfold hermite q5
  rfl

theorem hermite_q6 (A U x : ℝ) :
    hermite (c06 A U) (c36 A U) (c46 A U) x = q6 A U x := by
  unfold hermite q6
  rfl

def LowerResult (p : ℕ) (a b u w c0 c3 c4 m3 m4 : ℝ) : Prop :=
  ∀ μ : Measure ℝ, Admissible μ a b m3 m4 p →
    c0 + c3 * m3 + c4 * m4 ≤ moment μ p ∧
    moment (twoDirac w a u) p = c0 + c3 * m3 + c4 * m4 ∧
    Admissible (twoDirac w a u) a b m3 m4 p

def UpperResult (p : ℕ) (a b d w c0 c3 c4 m3 m4 : ℝ) : Prop :=
  ∀ μ : Measure ℝ, Admissible μ a b m3 m4 p →
    moment μ p ≤ c0 + c3 * m3 + c4 * m4 ∧
    moment (twoDirac w d b) p = c0 + c3 * m3 + c4 * m4 ∧
    Admissible (twoDirac w d b) a b m3 m4 p

/-- Strict-interior moment data give actual measure bounds and attaining measures
for both exponents. C02 feasibility and C03 signs/contacts are derived, not assumed.
No relative-minimax, boundary-case, four-axis, or scientific admission is asserted. -/
theorem strictInterior_measure_extremizers {a b m3 m4 : ℝ}
    (h : CAS13C02.StrictInterior a b m3 m4) :
    ∃ u d : ℝ,
      (CAS13C02.positiveCubeRoot m3 < u ∧ u < b ∧
        (u ^ 4 - a ^ 4) / (u ^ 3 - a ^ 3) = (m4 - a ^ 4) / (m3 - a ^ 3)) ∧
      (a < d ∧ d < CAS13C02.positiveCubeRoot m3 ∧
        (b ^ 4 - d ^ 4) / (b ^ 3 - d ^ 3) = (b ^ 4 - m4) / (b ^ 3 - m3)) ∧
      LowerResult 5 a b u (CAS13C02.lowerWeight a m3 u)
        (c05 a u) (c35 a u) (c45 a u) m3 m4 ∧
      UpperResult 5 a b d (CAS13C02.upperWeight b m3 d)
        (c05 b d) (c35 b d) (c45 b d) m3 m4 ∧
      LowerResult 6 a b u (CAS13C02.lowerWeight a m3 u)
        (c06 a u) (c36 a u) (c46 a u) m3 m4 ∧
      UpperResult 6 a b d (CAS13C02.upperWeight b m3 d)
        (c06 b d) (c36 b d) (c46 b d) m3 m4 := by
  obtain ⟨u, hu, _⟩ := CAS13C02.lower_node_existsUnique h
  obtain ⟨d, hd, _⟩ := CAS13C02.upper_node_existsUnique h
  obtain ⟨hrpos, _, har, hrb, _⟩ := CAS13C02.root_properties h
  have hau : a < u := lt_trans har hu.1
  have hu0 : 0 < u := lt_trans h.a_pos hau
  have hd0 : 0 < d := lt_trans h.a_pos hd.1
  have hdb : d < b := lt_trans hd.2.1 hrb
  have hb0 : 0 < b := lt_trans h.a_pos h.a_lt_b
  have haI : a ∈ Set.Icc a b := ⟨le_rfl, h.a_lt_b.le⟩
  have hbI : b ∈ Set.Icc a b := ⟨h.a_lt_b.le, le_rfl⟩
  have huI : u ∈ Set.Icc a b := ⟨hau.le, hu.2.1.le⟩
  have hdI : d ∈ Set.Icc a b := ⟨hd.1.le, hdb.le⟩
  obtain ⟨hl0, hl1, _, hl3, hl4⟩ := CAS13C02.lower_weight_moments h hu
  obtain ⟨hu0w, hu1w, _, hu3, hu4⟩ := CAS13C02.upper_weight_moments h hd
  refine ⟨u, d, hu, hd, ?_, ?_, ?_, ?_⟩
  · intro μ hμ
    obtain ⟨hprob, hs, h3, h4, hp, hm3, hm4⟩ := hμ
    apply lower_composition 5 μ hprob a b a u
      (CAS13C02.lowerWeight a m3 u)
      (c05 a u) (c35 a u) (c45 a u) m3 m4
      hs h3 h4 hp hm3 hm4
    · intro x hx
      rw [hermite_q5]
      exact lower5 h.a_pos hau hx.1
    · exact hl0.le
    · exact hl1.le
    · exact haI
    · exact huI
    · exact hl3
    · exact hl4
    · rw [hermite_q5]
      exact (q5_at_A h.a_pos hu0).symm
    · rw [hermite_q5]
      exact (q5_at_U h.a_pos hu0).symm
  · intro μ hμ
    obtain ⟨hprob, hs, h3, h4, hp, hm3, hm4⟩ := hμ
    apply upper_composition 5 μ hprob a b d b
      (CAS13C02.upperWeight b m3 d)
      (c05 b d) (c35 b d) (c45 b d) m3 m4
      hs h3 h4 hp hm3 hm4
    · intro x hx
      rw [hermite_q5]
      exact upper5 hd0 hdb hx.2 (le_trans h.a_pos.le hx.1)
    · exact hu0w.le
    · exact hu1w.le
    · exact hdI
    · exact hbI
    · exact hu3
    · exact hu4
    · rw [hermite_q5]
      exact (q5_at_U hb0 hd0).symm
    · rw [hermite_q5]
      exact (q5_at_A hb0 hd0).symm
  · intro μ hμ
    obtain ⟨hprob, hs, h3, h4, hp, hm3, hm4⟩ := hμ
    apply lower_composition 6 μ hprob a b a u
      (CAS13C02.lowerWeight a m3 u)
      (c06 a u) (c36 a u) (c46 a u) m3 m4
      hs h3 h4 hp hm3 hm4
    · intro x hx
      rw [hermite_q6]
      exact lower6 h.a_pos hau hx.1
    · exact hl0.le
    · exact hl1.le
    · exact haI
    · exact huI
    · exact hl3
    · exact hl4
    · rw [hermite_q6]
      exact (q6_at_A h.a_pos hu0).symm
    · rw [hermite_q6]
      exact (q6_at_U h.a_pos hu0).symm
  · intro μ hμ
    obtain ⟨hprob, hs, h3, h4, hp, hm3, hm4⟩ := hμ
    apply upper_composition 6 μ hprob a b d b
      (CAS13C02.upperWeight b m3 d)
      (c06 b d) (c36 b d) (c46 b d) m3 m4
      hs h3 h4 hp hm3 hm4
    · intro x hx
      rw [hermite_q6]
      exact upper6 hd0 hdb hx.2 (le_trans h.a_pos.le hx.1)
    · exact hu0w.le
    · exact hu1w.le
    · exact hdI
    · exact hbI
    · exact hu3
    · exact hu4
    · rw [hermite_q6]
      exact (q6_at_U hb0 hd0).symm
    · rw [hermite_q6]
      exact (q6_at_A hb0 hd0).symm

end CAS13MeasureExtremizerBridge
