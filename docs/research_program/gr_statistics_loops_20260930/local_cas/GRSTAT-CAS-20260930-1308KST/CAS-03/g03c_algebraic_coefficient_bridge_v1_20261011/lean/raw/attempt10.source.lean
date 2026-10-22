import NonlinearRemainder

set_option maxHeartbeats 50000

open ExactBoostMap NonlinearRemainder

namespace CoefficientMatrixBridge

abbrev V3 := ExactBoostMap.V3
abbrev M3 := ExactBoostMap.M3

def outer (v w : V3) : M3 := fun i j => v i * w j
noncomputable def spatialBlock (D : M3) (beta : V3) : M3 :=
  fun i j => boostedB D beta (some i) (some j)
noncomputable def timeCoefficient (D : M3) (beta : V3) : ℝ :=
  boostedB D beta none none
noncomputable def monopoleCoefficient (D : M3) (beta : V3) : ℝ :=
  timeCoefficient D beta + (spatialBlock D beta).trace / 3
noncomputable def quadrupoleCoefficient (D : M3) (beta : V3) : M3 :=
  spatialBlock D beta - ((spatialBlock D beta).trace / 3) • (1 : M3)
noncomputable def coefficientMatrix (D : M3) (beta : V3) : M3 :=
  monopoleCoefficient D beta • (1 : M3) + quadrupoleCoefficient D beta

theorem coefficientMatrix_eq (D : M3) (beta : V3) :
    coefficientMatrix D beta = timeCoefficient D beta • (1 : M3) + spatialBlock D beta := by
  ext i j
  simp [coefficientMatrix, monopoleCoefficient, quadrupoleCoefficient,
    Matrix.add_apply, Matrix.sub_apply, Matrix.smul_apply]
  ring

theorem quadrupoleCoefficient_trace (D : M3) (beta : V3) :
    (quadrupoleCoefficient D beta).trace = 0 := by
  simp [quadrupoleCoefficient, Matrix.trace_sub, Matrix.trace_smul]

private theorem boostedB_symmetric (D : M3) (hD : ∀ i j, D i j = D j i)
    (beta : V3) : ∀ i j, boostedB D beta i j = boostedB D beta j i := by
  have hrest : (restB D).IsSymm := Matrix.IsSymm.ext (by
    intro k l
    cases k <;> cases l <;> simp [restB, hD])
  have hb : (boostedB D beta).IsSymm := by
    unfold Matrix.IsSymm boostedB at *
    simp [Matrix.transpose_mul, Matrix.mul_assoc, hrest]
  intro i j
  exact hb.apply j i

theorem quadrupoleCoefficient_symmetric (D : M3)
    (hD : ∀ i j, D i j = D j i) (beta : V3) :
    ∀ i j, quadrupoleCoefficient D beta i j = quadrupoleCoefficient D beta j i := by
  intro i j
  have hs := boostedB_symmetric D hD beta (some i) (some j)
  simp only [quadrupoleCoefficient, Matrix.sub_apply, Matrix.smul_apply,
    spatialBlock]
  rw [hs]
  simp only [Matrix.one_apply, eq_comm]

theorem timeCoefficient_exact (D : M3) (beta : V3) :
    timeCoefficient D beta = gamma beta ^ 2 * sourceQuadratic D beta := by
  simp [timeCoefficient, boostedB, Matrix.mul_apply, Fintype.sum_option,
    restB, boost, sourceQuadratic, dot3, Matrix.mulVec, dotProduct,
    Fin.sum_univ_succ]
  ring

theorem outer_mulVec (v w x : V3) :
    (outer v w).mulVec x = (dot3 w x) • v := by
  ext i
  simp only [outer, Matrix.mulVec, dotProduct, dot3, Pi.smul_apply, smul_eq_mul]
  calc
    (∑ j, v i * w j * x j) = v i * ∑ j, w j * x j := by
      rw [Finset.mul_sum]
      apply Finset.sum_congr rfl
      intro j hj
      ring
    _ = _ := by ring

theorem algebraic_sky_expansion (D : M3)
    (hD : ∀ i j, D i j = D j i) (beta n : V3) (hn : q n = 1) :
    dotProduct (observerNull n) ((boostedB D beta).mulVec (observerNull n)) =
      monopoleCoefficient D beta + dot3 (dipoleMap D beta) n +
        dot3 n ((quadrupoleCoefficient D beta).mulVec n) := by
  simp [monopoleCoefficient, quadrupoleCoefficient, spatialBlock, observerNull,
    timeCoefficient, dipoleMap, dot3, q, Matrix.mulVec, dotProduct,
    Fintype.sum_option, Fin.sum_univ_succ] at hn ⊢
  have hs := boostedB_symmetric D hD beta
  have htrace := congrArg (fun x : ℝ =>
      (spatialBlock D beta).trace / 3 * x) hn
  rw [hs (some 0) none, hs (some 1) none, hs (some 2) none]
  nlinarith

theorem coefficientMatrix_zero (D : M3) : coefficientMatrix D 0 = D := by
  rw [coefficientMatrix_eq]
  ext i j
  simp [timeCoefficient, spatialBlock, boostedB, Matrix.mul_apply,
    Fintype.sum_option, Fin.sum_univ_succ, boost, restB, spatialL,
    gamma, boostA, q, dot3]

set_option maxHeartbeats 2000000 in
theorem coefficientMatrix_perturbation_exact (D : M3)
    (hD : ∀ i j, D i j = D j i) (beta : V3) :
    coefficientMatrix D beta - D =
      (gamma beta ^ 2 * sourceQuadratic D beta) • (1 : M3) +
      boostA beta • (outer beta (D.mulVec beta) + outer (D.mulVec beta) beta) +
      (boostA beta ^ 2 * sourceQuadratic D beta) • outer beta beta := by
  rw [coefficientMatrix_eq, timeCoefficient_exact]
  ext i j
  fin_cases i <;> fin_cases j <;>
    simp [spatialBlock, boostedB, outer, Matrix.mul_apply,
    Matrix.mulVec, dotProduct, Fintype.sum_option, Fin.sum_univ_succ,
    sourceQuadratic, dot3, spatialL, boost, restB,
    Matrix.add_apply, Matrix.sub_apply, Matrix.smul_apply, hD] <;> ring

theorem opNorm_le_of_mulVec_bound (M : M3) (k : ℝ) (hk : 0 ≤ k)
    (h : ∀ v : V3, eNorm (M.mulVec v) ≤ k * eNorm v) : opNorm M ≤ k := by
  unfold opNorm
  apply ContinuousLinearMap.opNorm_le_bound _ hk
  intro x
  let v : V3 := WithLp.ofLp x
  have hv : toE v = x := by simp [toE, v]
  simpa [← hv, eNorm, matrixOp_apply] using h v

private theorem opNorm_add_le (A B : M3) :
    opNorm (A + B) ≤ opNorm A + opNorm B := by
  have hm : matrixOp (A + B) = matrixOp A + matrixOp B := by
    simp [matrixOp, map_add]
  simpa [opNorm, hm] using norm_add_le (matrixOp A) (matrixOp B)

private theorem opNorm_smul (c : ℝ) (A : M3) :
    opNorm (c • A) = |c| * opNorm A := by
  have hm : matrixOp (c • A) = c • matrixOp A := by
    simp [matrixOp, map_smul]
  simp [opNorm, hm, norm_smul, Real.norm_eq_abs]

private theorem opNorm_one : opNorm (1 : M3) = 1 := by
  have hm : matrixOp (1 : M3) = ContinuousLinearMap.id ℝ E3 := by
    ext x
    let v : V3 := WithLp.ofLp x
    have hv : toE v = x := by simp [toE, v]
    simpa [← hv, matrixOp_apply] using congrArg toE (Matrix.one_mulVec v)
  simp [opNorm, hm]

private theorem opNorm_outer_le (v w : V3) :
    opNorm (outer v w) ≤ eNorm v * eNorm w := by
  apply opNorm_le_of_mulVec_bound _ _ (mul_nonneg (norm_nonneg _) (norm_nonneg _))
  intro x
  rw [outer_mulVec, eNorm_smul]
  have hdot := abs_dot3_le w x
  have hv : 0 ≤ eNorm v := norm_nonneg _
  calc
    |dot3 w x| * eNorm v ≤ (eNorm w * eNorm x) * eNorm v :=
      mul_le_mul_of_nonneg_right hdot hv
    _ = (eNorm v * eNorm w) * eNorm x := by ring

set_option maxHeartbeats 2000000 in
theorem coefficientMatrix_perturbation_norm_pointwise (D : M3)
    (hD : ∀ i j, D i j = D j i) (beta : V3) (hbeta : q beta < 1) :
    opNorm (coefficientMatrix D beta - D) ≤
      (2 * opNorm D / (1 - q beta)) * eNorm beta ^ 2 := by
  let b := eNorm beta
  let o := opNorm D
  let a := boostA beta
  let g := gamma beta
  let s := sourceQuadratic D beta
  have hb : 0 ≤ b := norm_nonneg _
  have ho : 0 ≤ o := norm_nonneg _
  have ha : 0 ≤ a := boostA_nonneg beta hbeta
  have hg : 0 < g := gamma_pos beta hbeta
  have hq : q beta = b ^ 2 := (eNorm_sq beta).symm
  have hden : 0 < 1 - q beta := sub_pos.mpr hbeta
  have hsource : |s| ≤ o * b ^ 2 := by
    calc
      |s| ≤ b * eNorm (D.mulVec beta) := abs_dot3_le beta (D.mulVec beta)
      _ ≤ b * (o * b) := by gcongr; exact eNorm_mulVec_le D beta
      _ = o * b ^ 2 := by ring
  have houter1 : opNorm (outer beta (D.mulVec beta)) ≤ o * b ^ 2 := by
    calc
      _ ≤ b * eNorm (D.mulVec beta) := opNorm_outer_le _ _
      _ ≤ b * (o * b) := by gcongr; exact eNorm_mulVec_le D beta
      _ = o * b ^ 2 := by ring
  have houter2 : opNorm (outer (D.mulVec beta) beta) ≤ o * b ^ 2 := by
    calc
      _ ≤ eNorm (D.mulVec beta) * b := opNorm_outer_le _ _
      _ ≤ (o * b) * b := by gcongr; exact eNorm_mulVec_le D beta
      _ = o * b ^ 2 := by ring
  have houter12 :
      opNorm (outer beta (D.mulVec beta) + outer (D.mulVec beta) beta) ≤
        2 * o * b ^ 2 := by
    calc
      _ ≤ opNorm (outer beta (D.mulVec beta)) +
          opNorm (outer (D.mulVec beta) beta) := opNorm_add_le _ _
      _ ≤ o * b ^ 2 + o * b ^ 2 := add_le_add houter1 houter2
      _ = 2 * o * b ^ 2 := by ring
  have houterbb : opNorm (outer beta beta) ≤ b ^ 2 := by
    simpa [pow_two] using opNorm_outer_le beta beta
  have hterm1 : opNorm ((g ^ 2 * s) • (1 : M3)) ≤ g ^ 2 * o * b ^ 2 := by
    rw [opNorm_smul, opNorm_one, mul_one, abs_mul,
      abs_of_nonneg (sq_nonneg g)]
    nlinarith [mul_nonneg (sub_nonneg.mpr hsource) (sq_nonneg g)]
  have hterm2 :
      opNorm (a • (outer beta (D.mulVec beta) + outer (D.mulVec beta) beta)) ≤
        2 * a * o * b ^ 2 := by
    rw [opNorm_smul, abs_of_nonneg ha]
    nlinarith [mul_nonneg (sub_nonneg.mpr houter12) ha]
  have hterm3 : opNorm ((a ^ 2 * s) • outer beta beta) ≤
      a ^ 2 * o * b ^ 4 := by
    rw [opNorm_smul, abs_mul, abs_of_nonneg (sq_nonneg a)]
    have hmult := mul_le_mul hsource houterbb
      (norm_nonneg _) (mul_nonneg ho (sq_nonneg b))
    nlinarith [mul_nonneg (sub_nonneg.mpr hsource) (sq_nonneg a),
      mul_nonneg (sub_nonneg.mpr houterbb) (sq_nonneg a), hmult]
  have hmain : opNorm (coefficientMatrix D beta - D) ≤
      g ^ 2 * o * b ^ 2 + 2 * a * o * b ^ 2 + a ^ 2 * o * b ^ 4 := by
    rw [coefficientMatrix_perturbation_exact D hD beta]
    calc
      _ ≤ opNorm ((g ^ 2 * s) • (1 : M3) +
            a • (outer beta (D.mulVec beta) + outer (D.mulVec beta) beta)) +
          opNorm ((a ^ 2 * s) • outer beta beta) := opNorm_add_le _ _
      _ ≤ opNorm ((g ^ 2 * s) • (1 : M3)) +
            opNorm (a • (outer beta (D.mulVec beta) + outer (D.mulVec beta) beta)) +
          opNorm ((a ^ 2 * s) • outer beta beta) := by
            gcongr
            exact opNorm_add_le _ _
      _ ≤ _ := by nlinarith [hterm1, hterm2, hterm3]
  have ha1 : a * q beta = g - 1 := boostA_mul_q beta hbeta
  have ha2 : a * (g + 1) = g ^ 2 := by
    dsimp [a, g]
    unfold boostA
    have hn : gamma beta + 1 ≠ 0 := by have := gamma_pos beta hbeta; positivity
    field_simp
  have hcoef : a ^ 2 * q beta + 2 * a = g ^ 2 := by
    nlinarith [congrArg (fun x : ℝ => a * x) ha1]
  have hgsq : g ^ 2 = 1 / (1 - q beta) := by
    apply (eq_div_iff (ne_of_gt hden)).2
    exact gamma_sq_mul_one_sub_q beta hbeta
  calc
    opNorm (coefficientMatrix D beta - D) ≤
        g ^ 2 * o * b ^ 2 + 2 * a * o * b ^ 2 + a ^ 2 * o * b ^ 4 := hmain
    _ = 2 * g ^ 2 * o * b ^ 2 := by
      have hh := congrArg (fun x : ℝ => x * o * b ^ 2) hcoef
      rw [hq] at hh
      nlinarith
    _ = (2 * o / (1 - q beta)) * b ^ 2 := by rw [hgsq]; ring

theorem coefficientMatrix_perturbation_norm_ball (D : M3)
    (hD : ∀ i j, D i j = D j i) (beta : V3) (r : ℝ)
    (hr0 : 0 ≤ r) (hr1 : r < 1) (hbeta : eNorm beta ≤ r) :
    opNorm (coefficientMatrix D beta - D) ≤
      (2 * opNorm D / (1 - r ^ 2)) * eNorm beta ^ 2 := by
  have hd := ball_denominator beta r hr0 hr1 hbeta
  have hq : q beta < 1 := by linarith [hd.2]
  have ho : 0 ≤ opNorm D := norm_nonneg _
  have hfrac : 2 * opNorm D / (1 - q beta) ≤
      2 * opNorm D / (1 - r ^ 2) := by
    apply (div_le_div_iff₀ (sub_pos.mpr hq) hd.1).2
    exact mul_le_mul_of_nonneg_left hd.2 (by positivity)
  calc
    opNorm (coefficientMatrix D beta - D) ≤
        (2 * opNorm D / (1 - q beta)) * eNorm beta ^ 2 :=
      coefficientMatrix_perturbation_norm_pointwise D hD beta hq
    _ ≤ (2 * opNorm D / (1 - r ^ 2)) * eNorm beta ^ 2 := by
      exact mul_le_mul_of_nonneg_right hfrac (by positivity)

#check coefficientMatrix_eq
#print axioms coefficientMatrix_eq
#check quadrupoleCoefficient_trace
#print axioms quadrupoleCoefficient_trace
#check quadrupoleCoefficient_symmetric
#print axioms quadrupoleCoefficient_symmetric
#check algebraic_sky_expansion
#print axioms algebraic_sky_expansion
#check coefficientMatrix_zero
#print axioms coefficientMatrix_zero
#check coefficientMatrix_perturbation_exact
#print axioms coefficientMatrix_perturbation_exact
#check coefficientMatrix_perturbation_norm_pointwise
#print axioms coefficientMatrix_perturbation_norm_pointwise
#check coefficientMatrix_perturbation_norm_ball
#print axioms coefficientMatrix_perturbation_norm_ball

end CoefficientMatrixBridge
