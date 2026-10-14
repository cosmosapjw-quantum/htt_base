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
  have hv : toE v = x := WithLp.toLp_ofLp x
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
    have hv : toE v = x := WithLp.toLp_ofLp x
    simpa [← hv, matrixOp_apply] using congrArg toE (Matrix.one_mulVec v)
  simp [opNorm, hm]

private theorem opNorm_outer_le (v w : V3) :
    opNorm (outer v w) ≤ eNorm v * eNorm w := by
  apply opNorm_le_of_mulVec_bound _ _ (mul_nonneg (norm_nonneg _) (norm_nonneg _))
  intro x
  rw [outer_mulVec, eNorm_smul]
  have hdot := abs_dot3_le w x
  have hv : 0 ≤ eNorm v := norm_nonneg _
  nlinarith [mul_nonneg (sub_nonneg.mpr hdot) hv]

end CoefficientMatrixBridge
