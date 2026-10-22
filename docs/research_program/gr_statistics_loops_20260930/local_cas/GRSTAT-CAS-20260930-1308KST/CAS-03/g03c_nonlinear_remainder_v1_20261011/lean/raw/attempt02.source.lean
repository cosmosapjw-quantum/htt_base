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
  simpa [eNorm, toE, q, dot3, EuclideanSpace.inner_eq_star_dotProduct,
    dotProduct, star_trivial] using (real_inner_self_eq_norm_sq (toE v)).symm

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

end NonlinearRemainder
