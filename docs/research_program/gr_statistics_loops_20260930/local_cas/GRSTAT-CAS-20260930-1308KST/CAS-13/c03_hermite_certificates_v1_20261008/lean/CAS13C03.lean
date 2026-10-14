import Mathlib

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
