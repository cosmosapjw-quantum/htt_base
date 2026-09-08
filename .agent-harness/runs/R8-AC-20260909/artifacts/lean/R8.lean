import Mathlib
set_option backward.isDefEq.respectTransparency false

/- Fresh R8 proofs. No old project proofs and no sibling results are imported.
   Component spectral inequalities are explicit named prerequisites per contract.
   Probability and differential-calculus gaps are recorded by the wrapper. -/
namespace R8
noncomputable section

-- Generic common-rotation combination: the SAME index r is used for both residuals.
theorem weighted_lower {I : Type*} (bq bo q o : ℝ) (Q O : I → ℝ)
    (hbq : 0 ≤ bq) (hbo : 0 ≤ bo) (hq : 0 < q) (ho : 0 < o)
    (hHW : ∀ r, bq ≤ Q r) (hMirsky : ∀ r, bo ≤ O r) (r : I) :
    Real.sqrt (bq^2/q^2 + bo^2/o^2) ≤
      Real.sqrt ((Q r)^2/q^2 + (O r)^2/o^2) := by
  apply Real.sqrt_le_sqrt
  apply add_le_add
  · exact div_le_div_of_nonneg_right (by nlinarith [hHW r]) (sq_nonneg q)
  · exact div_le_div_of_nonneg_right (by nlinarith [hMirsky r]) (sq_nonneg o)

-- Converts a pointwise lower bound to a bound on an attained minimum.
theorem bound_at_minimum {I : Type*} (f : I → ℝ) (b : ℝ)
    (hb : ∀ r, b ≤ f r) (rmin : I) : b ≤ f rmin := hb rmin

-- Full symmetric multiplicities of O111=2,O122=O133=-1.
theorem scaling_norm_fixtures :
    ((-1 : ℝ)^2 + 0^2 + 1^2 = 2) ∧
    ((2 : ℝ)^2 + 3*(-1)^2 + 3*(-1)^2 = 10) ∧
    ((2 : ℝ)^2+(-1)^2+(-1)^2 = 6) ∧
    ((-1 : ℝ)^2+(-1)^2 = 2) := by norm_num

theorem positive_scale_sqrt (a q : ℝ) (ha : 0 ≤ a) (hq : 0 < q) :
    Real.sqrt (a / q^2) = Real.sqrt a / q := by
  rw [Real.sqrt_div ha, Real.sqrt_sq_eq_abs, abs_of_pos hq]

-- Homogeneous quaternion rotation numerator. Three mutually orthogonal rows;
-- squared row norms equal squared quaternion norm squared, and determinant is cubed norm.
def rot (a b c d : ℝ) : Matrix (Fin 3) (Fin 3) ℝ :=
  !![a*a+b*b-c*c-d*d, 2*(b*c-a*d), 2*(b*d+a*c);
     2*(b*c+a*d), a*a-b*b+c*c-d*d, 2*(c*d-a*b);
     2*(b*d-a*c), 2*(c*d+a*b), a*a-b*b-c*c+d*d]

theorem quaternion_rows (a b c d : ℝ) :
    (rot a b c d) * (rot a b c d).transpose =
      (a*a+b*b+c*c+d*d)^2 • (1 : Matrix (Fin 3) (Fin 3) ℝ) := by
  ext i j
  fin_cases i <;> fin_cases j <;>
    simp [rot, Matrix.mul_apply, Fin.sum_univ_succ, Matrix.one_apply] <;> ring

theorem quaternion_det (a b c d : ℝ) :
    (rot a b c d).det = (a*a+b*b+c*c+d*d)^3 := by
  simp [rot, Matrix.det_fin_three]
  ring

-- Projection identity for the formal normalized-chart directional derivative:
-- u=(1,x), w=(0,v), s=||u||², t=u·w.  Dq[v]=(s w-u t)/s^(3/2).
theorem chart_derivative_numerator (x y z v w h : ℝ) :
    let s := 1+x*x+y*y+z*z
    let t := x*v+y*w+z*h
    (-(t))^2 + (s*v-x*t)^2 + (s*w-y*t)^2 + (s*h-z*t)^2 =
      s^2*(v*v+w*w+h*h)-s*t^2 := by dsimp; ring

theorem chart_derivative_squared_bound (s t vv m : ℝ)
    (hs : 0 < s) (hm : 0 < m) (hms : m^2 ≤ s) (hv : 0 ≤ vv) :
    (s^2*vv-s*t^2)/s^3 ≤ vv/m^2 := by
  have hm2 : 0 < m^2 := sq_pos_of_pos hm
  have hs3 : 0 < s^3 := pow_pos hs 3
  apply (div_le_div_iff₀ hs3 hm2).2
  have h1 : 0 ≤ s^2*vv*(s-m^2) := mul_nonneg (mul_nonneg (sq_nonneg s) hv) (sub_nonneg.mpr hms)
  have h2 : 0 ≤ s*t^2*m^2 := mul_nonneg (mul_nonneg (le_of_lt hs) (sq_nonneg t)) (sq_nonneg m)
  nlinarith

theorem grid_radius_rational : Real.sqrt 3 ≤ (7:ℝ)/4 := by
  have h := Real.sq_sqrt (show (0:ℝ) ≤ 3 by norm_num)
  have hn := Real.sqrt_nonneg (3:ℝ)
  nlinarith

-- Generic deterministic O3 interval enclosure and inclusive endpoint counts.
def countGE {n : ℕ} (s : Fin n → ℝ) (t : ℝ) : ℕ :=
    (Finset.univ.filter (fun i => t ≤ s i)).card

theorem interval_counts {n : ℕ} (L s U : Fin n → ℝ) (L0 s0 U0 : ℝ)
    (hL : ∀ i, L i ≤ s i) (hU : ∀ i, s i ≤ U i)
    (h0L : L0 ≤ s0) (h0U : s0 ≤ U0) :
    countGE L U0 ≤ countGE s s0 ∧ countGE s s0 ≤ countGE U L0 := by
  constructor <;> apply Finset.card_le_card
  · intro i hi
    simp only [Finset.mem_filter, Finset.mem_univ, true_and] at hi ⊢
    exact h0U.trans (hi.trans (hL i))
  · intro i hi
    simp only [Finset.mem_filter, Finset.mem_univ, true_and] at hi ⊢
    exact h0L.trans (hi.trans (hU i))

theorem rank_interval {n : ℕ} (L s U : Fin n → ℝ) (L0 s0 U0 : ℝ)
    (hL : ∀ i, L i ≤ s i) (hU : ∀ i, s i ≤ U i)
    (h0L : L0 ≤ s0) (h0U : s0 ≤ U0) (M : ℝ) (hM : 0 < M) :
    (1+(countGE L U0 : ℝ))/M ≤ (1+(countGE s s0 : ℝ))/M ∧
    (1+(countGE s s0 : ℝ))/M ≤ (1+(countGE U L0 : ℝ))/M := by
  obtain ⟨h1,h2⟩ := interval_counts L s U L0 s0 U0 hL hU h0L h0U
  constructor
  · exact (div_le_div_iff_of_pos_right hM).2 (by exact_mod_cast Nat.add_le_add_left h1 1)
  · exact (div_le_div_iff_of_pos_right hM).2 (by exact_mod_cast Nat.add_le_add_left h2 1)

theorem reject_1000 (c : ℕ) : (1+(c:ℚ))/1000 ≤ 1/20 ↔ c ≤ 49 := by
  constructor <;> intro h
  · have : (c:ℚ) ≤ 49 := by linarith
    exact_mod_cast this
  · have : (c:ℚ) ≤ 49 := by exact_mod_cast h
    linarith

theorem reject_301 (c : ℕ) : (1+(c:ℚ))/301 ≤ 1/20 ↔ c ≤ 14 := by
  constructor <;> intro h
  · have : (c:ℚ) < 15 := by linarith
    have : c < 15 := by exact_mod_cast this
    omega
  · have : (c:ℚ) ≤ 14 := by exact_mod_cast h
    linarith

theorem nonreject_1000 (c : ℕ) : (1:ℚ)/20 < (1+(c:ℚ))/1000 ↔ 50 ≤ c := by
  rw [← not_le, reject_1000]
  omega

theorem nonreject_301 (c : ℕ) : (1:ℚ)/20 < (1+(c:ℚ))/301 ↔ 15 ≤ c := by
  rw [← not_le, reject_301]
  omega

theorem tie_fixture (n : ℕ) : countGE (fun _ : Fin n => (0:ℝ)) 0 = n := by
  simp [countGE]

theorem wide_reference_count : countGE (fun _ : Fin 4 => (3:ℝ)) 7 = 0 := by
  norm_num [countGE]

theorem wide_rank : (1:ℚ)/5 = (1+0)/5 := by norm_num

-- Exact rank-one support experiment: B=(3/5,4/5), V=4.
def B (z : ℚ) : ℚ × ℚ := (3*z/5,4*z/5)
def leftInv (r : ℚ × ℚ) : ℚ := 3*r.1/5+4*r.2/5

theorem factor_full_rank (x y : ℚ) (h : B x = B y) : x = y := by
  have h1 := congrArg Prod.fst h
  dsimp [B] at h1
  linarith

theorem factor_left_inverse (z : ℚ) : leftInv (B z) = z := by
  dsimp [B,leftInv]; ring

theorem factor_support : B 2 = (6/5,8/5) ∧ leftInv (B 2)^2/4 = 1 := by
  norm_num [B,leftInv]

theorem factor_off_support : ¬ ∃ z : ℚ, B z = (2/5,11/5) := by
  rintro ⟨z,h⟩
  have hx := congrArg Prod.fst h
  have hy := congrArg Prod.snd h
  dsimp [B] at hx hy
  linarith

theorem factor_covariance :
    (4*(3:ℚ)/5*(3/5),4*(3:ℚ)/5*(4/5),4*(4:ℚ)/5*(4/5)) =
    (36/25,48/25,64/25) := by norm_num

-- Pointwise sign-mixture support and moments are algebra only. The distribution
-- construction and Gaussian law implications remain unresolved, not assumptions.
theorem sign_mixture_support (z s : ℝ) (hs : s = 1 ∨ s = -1) :
    (s*z)^2 = z^2 ∧ (z+s*z = 0 ∨ z-s*z = 0) := by
  rcases hs with rfl | rfl <;> constructor <;> ring_nf <;> simp

-- Genuine calculus identification for every homogeneous-chart coordinate along
-- every direction; A=1,B=0 gives the fixed coordinate, A=x_j,B=v_j the others.
theorem normalized_chart_coordinate_derivative (x y z v w h A B : ℝ) :
    HasDerivAt
      (fun t : ℝ => (A+t*B) / Real.sqrt (1+(x+t*v)^2+(y+t*w)^2+(z+t*h)^2))
      ((B*Real.sqrt (1+x^2+y^2+z^2) -
         A*((2*(x*v+y*w+z*h))/(2*Real.sqrt (1+x^2+y^2+z^2)))) /
        (Real.sqrt (1+x^2+y^2+z^2))^2) 0 := by
  have hx : HasDerivAt (fun t : ℝ => x+t*v) v 0 := by
    convert! (hasDerivAt_const (0:ℝ) x).add ((hasDerivAt_id (0:ℝ)).mul_const v) using 1 <;> simp
  have hy : HasDerivAt (fun t : ℝ => y+t*w) w 0 := by
    convert! (hasDerivAt_const (0:ℝ) y).add ((hasDerivAt_id (0:ℝ)).mul_const w) using 1 <;> simp
  have hz : HasDerivAt (fun t : ℝ => z+t*h) h 0 := by
    convert! (hasDerivAt_const (0:ℝ) z).add ((hasDerivAt_id (0:ℝ)).mul_const h) using 1 <;> simp
  have hs : HasDerivAt (fun t : ℝ => 1+(x+t*v)^2+(y+t*w)^2+(z+t*h)^2)
      (2*(x*v+y*w+z*h)) 0 := by
    convert! (((hasDerivAt_const (0:ℝ) (1:ℝ)).add (hx.pow 2)).add (hy.pow 2)).add (hz.pow 2) using 1 <;> try { ext; rfl } <;> try dsimp <;> ring
  have hp : 0 < 1+x^2+y^2+z^2 := by nlinarith [sq_nonneg x,sq_nonneg y,sq_nonneg z]
  have hn : HasDerivAt (fun t : ℝ => A+t*B) B 0 := by
    convert! (hasDerivAt_const (0:ℝ) A).add ((hasDerivAt_id (0:ℝ)).mul_const B) using 1 <;> simp
  convert! hn.div (hs.sqrt (by simpa using ne_of_gt hp))
    (by simpa using ne_of_gt (Real.sqrt_pos.2 hp)) using 1 <;> simp

theorem chart_derivative_simplification (s t A B : ℝ) (hs : 0 < s) :
    (B*Real.sqrt s-A*((2*t)/(2*Real.sqrt s)))/(Real.sqrt s)^2 =
    (s*B-A*t)/(s*Real.sqrt s) := by
  have hsq := Real.sq_sqrt (le_of_lt hs)
  have hn : Real.sqrt s ≠ 0 := ne_of_gt (Real.sqrt_pos.2 hs)
  field_simp
  rw [hsq]
  ring


end
end R8
