import ExactBoostMap

open ExactBoostMap

namespace NonlinearRemainder

abbrev E3 := EuclideanSpace ℝ (Fin 3)
def toE (v : V3) : E3 := WithLp.toLp 2 v
noncomputable def eNorm (v : V3) : ℝ := ‖toE v‖
noncomputable def matrixOp (D : M3) : E3 →L[ℝ] E3 :=
  (Matrix.toEuclideanLin D).toContinuousLinearMap
noncomputable def opNorm (D : M3) : ℝ := ‖matrixOp D‖
noncomputable def remainder (D : M3) (beta : V3) : V3 :=
  dipoleMap D beta + 2 • D.mulVec beta

theorem eNorm_sq (v : V3) : eNorm v ^ 2 = q v := by
  calc
    eNorm v ^ 2 = inner ℝ (toE v) (toE v) :=
      (real_inner_self_eq_norm_sq (toE v)).symm
    _ = q v := by
      rw [EuclideanSpace.inner_eq_star_dotProduct]
      simp [q, dot3, toE, dotProduct, star_trivial]

theorem matrixOp_apply (D : M3) (v : V3) :
    matrixOp D (toE v) = toE (D.mulVec v) := by
  exact Matrix.toEuclideanLin_apply_piLp_toLp D v

theorem abs_dot3_le (v w : V3) : |dot3 v w| ≤ eNorm v * eNorm w := by
  simpa [dot3, eNorm, toE, EuclideanSpace.inner_eq_star_dotProduct,
    dotProduct, star_trivial, mul_comm] using
    (abs_real_inner_le_norm (toE w) (toE v))

theorem eNorm_mulVec_le (D : M3) (v : V3) :
    eNorm (D.mulVec v) ≤ opNorm D * eNorm v := by
  simpa [eNorm, opNorm, matrixOp_apply] using
    (ContinuousLinearMap.le_opNorm (matrixOp D) (toE v))

theorem eNorm_add_le (v w : V3) : eNorm (v + w) ≤ eNorm v + eNorm w := by
  simpa [eNorm, toE] using (norm_add_le (toE v) (toE w))

theorem eNorm_smul (c : ℝ) (v : V3) : eNorm (c • v) = |c| * eNorm v := by
  simp [eNorm, toE, norm_smul, Real.norm_eq_abs]

theorem gamma_ge_one (beta : V3) (hbeta : q beta < 1) : 1 ≤ gamma beta := by
  have hq : 0 ≤ q beta := by rw [← eNorm_sq]; positivity
  have hg := gamma_sq_mul_one_sub_q beta hbeta
  have hp := gamma_pos beta hbeta
  nlinarith

theorem boostA_nonneg (beta : V3) (hbeta : q beta < 1) :
    0 ≤ boostA beta := by
  unfold boostA
  have := gamma_pos beta hbeta
  positivity

theorem gamma_sq_sub_one (beta : V3) (hbeta : q beta < 1) :
    gamma beta ^ 2 - 1 = q beta / (1 - q beta) := by
  have hg := gamma_sq_mul_one_sub_q beta hbeta
  have hd : 1 - q beta ≠ 0 := ne_of_gt (sub_pos.mpr hbeta)
  apply (eq_div_iff hd).2
  nlinarith

theorem remainder_factorization
    (D : M3) (hD : ∀ i j, D i j = D j i)
    (beta : V3) (hbeta : q beta < 1) :
    remainder D beta = (-2 * boostA beta) •
      (q beta • D.mulVec beta +
        (gamma beta * sourceQuadratic D beta) • beta) := by
  have ha := boostA_mul_q beta hbeta
  ext i
  simp only [remainder, Pi.add_apply, Pi.smul_apply, smul_eq_mul]
  rw [dipoleMap_exact D hD beta]
  simp only
  ring_nf at ha ⊢
  nlinarith [congrArg (fun x : ℝ => x * D.mulVec beta i) ha]

theorem ball_denominator (beta : V3) (r : ℝ)
    (hr0 : 0 ≤ r) (hr1 : r < 1) (hbeta : eNorm beta ≤ r) :
    0 < 1 - r ^ 2 ∧ 1 - r ^ 2 ≤ 1 - q beta := by
  rw [← eNorm_sq]
  have hb : 0 ≤ eNorm beta := norm_nonneg _
  constructor
  · nlinarith
  · have hm := mul_nonneg (sub_nonneg.mpr hbeta) (add_nonneg hr0 hb)
    nlinarith

theorem remainder_norm_le_pointwise
    (D : M3) (hD : ∀ i j, D i j = D j i)
    (beta : V3) (hbeta : q beta < 1) :
    eNorm (remainder D beta) ≤
      (2 * opNorm D / (1 - q beta)) * eNorm beta ^ 3 := by
  let b := eNorm beta
  let a := boostA beta
  let g := gamma beta
  let o := opNorm D
  have hb : 0 ≤ b := norm_nonneg _
  have ho : 0 ≤ o := norm_nonneg _
  have hq : q beta = b ^ 2 := (eNorm_sq beta).symm
  have hqn : 0 ≤ q beta := by rw [hq]; positivity
  have hg : 0 < g := gamma_pos beta hbeta
  have ha : 0 ≤ a := boostA_nonneg beta hbeta
  have hden : 0 < 1 - q beta := sub_pos.mpr hbeta
  have hsource : |sourceQuadratic D beta| ≤ o * b ^ 2 := by
    calc
      |sourceQuadratic D beta| ≤ b * eNorm (D.mulVec beta) :=
        abs_dot3_le beta (D.mulVec beta)
      _ ≤ b * (o * b) := by gcongr; exact eNorm_mulVec_le D beta
      _ = o * b ^ 2 := by ring
  have hmatrix := eNorm_mulVec_le D beta
  have htri := eNorm_add_le
      (q beta • D.mulVec beta) ((g * sourceQuadratic D beta) • beta)
  have hinner :
      eNorm (q beta • D.mulVec beta +
          (g * sourceQuadratic D beta) • beta) ≤
        q beta * o * b + g * (o * b ^ 2) * b := by
    calc
      _ ≤ eNorm (q beta • D.mulVec beta) +
            eNorm ((g * sourceQuadratic D beta) • beta) := htri
      _ = q beta * eNorm (D.mulVec beta) +
            g * |sourceQuadratic D beta| * b := by
              rw [eNorm_smul, eNorm_smul, abs_of_nonneg hqn,
                abs_mul, abs_of_nonneg (le_of_lt hg)]
      _ ≤ q beta * o * b + g * (o * b ^ 2) * b := by
        have hleft : q beta * eNorm (D.mulVec beta) ≤ q beta * (o * b) :=
          mul_le_mul_of_nonneg_left hmatrix hqn
        have hright : g * |sourceQuadratic D beta| * b ≤
            g * (o * b ^ 2) * b :=
          mul_le_mul_of_nonneg_right
            (mul_le_mul_of_nonneg_left hsource (le_of_lt hg)) hb
        nlinarith
  have hmain : eNorm (remainder D beta) ≤
      2 * a * (q beta * o * b + g * (o * b ^ 2) * b) := by
    rw [remainder_factorization D hD beta hbeta, eNorm_smul]
    have habs : |-2 * a| = 2 * a := by rw [abs_mul, abs_of_nonneg ha]; norm_num
    rw [habs]
    gcongr
  have hcoef : a * (g + 1) = g ^ 2 := by
    dsimp [a, g]
    unfold boostA
    have hn : gamma beta + 1 ≠ 0 := by have := gamma_pos beta hbeta; positivity
    field_simp
  have hgsq : g ^ 2 = 1 / (1 - q beta) := by
    apply (eq_div_iff (ne_of_gt hden)).2
    exact gamma_sq_mul_one_sub_q beta hbeta
  calc
    eNorm (remainder D beta) ≤
        2 * a * (q beta * o * b + g * (o * b ^ 2) * b) := hmain
    _ = 2 * a * ((1 + g) * o * b ^ 3) := by rw [hq]; ring
    _ = 2 * (a * (g + 1)) * o * b ^ 3 := by ring
    _ = (2 * o / (1 - q beta)) * b ^ 3 := by rw [hcoef, hgsq]; ring

theorem remainder_norm_le_cubic_ball
    (D : M3) (hD : ∀ i j, D i j = D j i)
    (beta : V3) (r : ℝ) (hr0 : 0 ≤ r) (hr1 : r < 1)
    (hbeta : eNorm beta ≤ r) :
    eNorm (remainder D beta) ≤
      (2 * opNorm D / (1 - r ^ 2)) * eNorm beta ^ 3 := by
  have hd := ball_denominator beta r hr0 hr1 hbeta
  have hq : q beta < 1 := by linarith [hd.2]
  have ho : 0 ≤ opNorm D := norm_nonneg _
  have hfrac : 2 * opNorm D / (1 - q beta) ≤
      2 * opNorm D / (1 - r ^ 2) := by
    apply (div_le_div_iff₀ (sub_pos.mpr hq) hd.1).2
    exact mul_le_mul_of_nonneg_left hd.2 (by positivity)
  calc
    eNorm (remainder D beta) ≤
        (2 * opNorm D / (1 - q beta)) * eNorm beta ^ 3 :=
      remainder_norm_le_pointwise D hD beta hq
    _ ≤ (2 * opNorm D / (1 - r ^ 2)) * eNorm beta ^ 3 := by
      have hb : 0 ≤ eNorm beta := norm_nonneg _
      exact mul_le_mul_of_nonneg_right hfrac (by positivity)

theorem remainder_norm_le_quadratic_ball
    (D : M3) (hD : ∀ i j, D i j = D j i)
    (beta : V3) (r : ℝ) (hr0 : 0 ≤ r) (hr1 : r < 1)
    (hbeta : eNorm beta ≤ r) :
    eNorm (remainder D beta) ≤
      (2 * r * opNorm D / (1 - r ^ 2)) * eNorm beta ^ 2 := by
  have hd := ball_denominator beta r hr0 hr1 hbeta
  have ho : 0 ≤ opNorm D := norm_nonneg _
  have hcoef : 0 ≤ 2 * opNorm D / (1 - r ^ 2) :=
    div_nonneg (mul_nonneg (by norm_num) ho) (le_of_lt hd.1)
  have hb2 : 0 ≤ eNorm beta ^ 2 := by positivity
  have hb3 : eNorm beta ^ 3 ≤ r * eNorm beta ^ 2 := by
    calc
      eNorm beta ^ 3 = eNorm beta * eNorm beta ^ 2 := by ring
      _ ≤ r * eNorm beta ^ 2 := mul_le_mul_of_nonneg_right hbeta hb2
  calc
    eNorm (remainder D beta) ≤
        (2 * opNorm D / (1 - r ^ 2)) * eNorm beta ^ 3 :=
      remainder_norm_le_cubic_ball D hD beta r hr0 hr1 hbeta
    _ ≤ (2 * opNorm D / (1 - r ^ 2)) * (r * eNorm beta ^ 2) := by
      exact mul_le_mul_of_nonneg_left hb3 hcoef
    _ = (2 * r * opNorm D / (1 - r ^ 2)) * eNorm beta ^ 2 := by ring

theorem remainder_norm_le_half
    (D : M3) (hD : ∀ i j, D i j = D j i)
    (beta : V3) (hbeta : eNorm beta ≤ (1 / 2 : ℝ)) :
    eNorm (remainder D beta) ≤
      (8 / 3 : ℝ) * opNorm D * eNorm beta ^ 3 ∧
    eNorm (remainder D beta) ≤
      (4 / 3 : ℝ) * opNorm D * eNorm beta ^ 2 := by
  constructor
  · calc
      eNorm (remainder D beta) ≤
          (2 * opNorm D / (1 - (1 / 2 : ℝ) ^ 2)) * eNorm beta ^ 3 :=
        remainder_norm_le_cubic_ball D hD beta (1 / 2) (by norm_num) (by norm_num) hbeta
      _ = (8 / 3 : ℝ) * opNorm D * eNorm beta ^ 3 := by
        have hc : (2 : ℝ) / (1 - (1 / 2 : ℝ) ^ 2) = 8 / 3 := by norm_num
        calc
          _ = ((2 : ℝ) / (1 - (1 / 2 : ℝ) ^ 2)) * opNorm D * eNorm beta ^ 3 := by ring
          _ = _ := by rw [hc]
  · calc
      eNorm (remainder D beta) ≤
          (2 * (1 / 2 : ℝ) * opNorm D / (1 - (1 / 2 : ℝ) ^ 2)) *
            eNorm beta ^ 2 :=
        remainder_norm_le_quadratic_ball D hD beta (1 / 2) (by norm_num) (by norm_num) hbeta
      _ = (4 / 3 : ℝ) * opNorm D * eNorm beta ^ 2 := by
        have hc : (2 * (1 / 2 : ℝ)) / (1 - (1 / 2 : ℝ) ^ 2) = 4 / 3 := by norm_num
        calc
          _ = ((2 * (1 / 2 : ℝ)) / (1 - (1 / 2 : ℝ) ^ 2)) * opNorm D *
                eNorm beta ^ 2 := by ring
          _ = _ := by rw [hc]

#check remainder_factorization
#print axioms remainder_factorization
#check remainder_norm_le_pointwise
#print axioms remainder_norm_le_pointwise
#check remainder_norm_le_cubic_ball
#print axioms remainder_norm_le_cubic_ball
#check remainder_norm_le_quadratic_ball
#print axioms remainder_norm_le_quadratic_ball
#check remainder_norm_le_half
#print axioms remainder_norm_le_half

end NonlinearRemainder
