import NonlinearRemainder

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
  ring

private theorem boostedB_symmetric (D : M3) (hD : ∀ i j, D i j = D j i)
    (beta : V3) : ∀ i j, boostedB D beta i j = boostedB D beta j i := by
  intro i j
  have hrest : (restB D).IsSymm := by
    intro k l
    cases k <;> cases l <;> simp [restB, hD]
  exact (Matrix.IsSymm.congr _).mp (by
    simpa [boostedB] using (Matrix.IsSymm.mul_left (boost beta) hrest)) i j

theorem quadrupoleCoefficient_symmetric (D : M3)
    (hD : ∀ i j, D i j = D j i) (beta : V3) :
    ∀ i j, quadrupoleCoefficient D beta i j = quadrupoleCoefficient D beta j i := by
  intro i j
  simp [quadrupoleCoefficient, spatialBlock, Matrix.sub_apply,
    Matrix.smul_apply, Matrix.one_apply, boostedB_symmetric D hD beta (some i) (some j)]
  split_ifs with h
  · subst j; rfl
  · exact False.elim (h (Eq.symm ‹_›))

theorem timeCoefficient_exact (D : M3) (beta : V3) :
    timeCoefficient D beta = gamma beta ^ 2 * sourceQuadratic D beta := by
  simp [timeCoefficient, boostedB, Matrix.mul_apply, Fintype.sum_option,
    restB, boost, sourceQuadratic, dot3, Matrix.mulVec,
    Fin.sum_univ_succ]
  ring

theorem outer_mulVec (v w x : V3) :
    (outer v w).mulVec x = (dot3 w x) • v := by
  ext i
  simp [outer, Matrix.mulVec, dotProduct, dot3, Pi.smul_apply,
    Finset.mul_sum]

theorem algebraic_sky_expansion (D : M3)
    (hD : ∀ i j, D i j = D j i) (beta n : V3) (hn : q n = 1) :
    dotProduct (observerNull n) ((boostedB D beta).mulVec (observerNull n)) =
      monopoleCoefficient D beta + dot3 (dipoleMap D beta) n +
        dot3 n ((quadrupoleCoefficient D beta).mulVec n) := by
  simp [monopoleCoefficient, quadrupoleCoefficient, spatialBlock,
    timeCoefficient, dipoleMap, dot3, q, Matrix.mulVec, dotProduct,
    Fintype.sum_option, Fin.sum_univ_succ] at hn ⊢
  have hs := boostedB_symmetric D hD beta
  fin_cases n  -- placeholder

theorem coefficientMatrix_zero (D : M3) : coefficientMatrix D 0 = D := by
  rw [coefficientMatrix_eq]
  ext i j
  simp [timeCoefficient, spatialBlock, boostedB, Matrix.mul_apply,
    Fintype.sum_option, Fin.sum_univ_succ, boost, restB, spatialL,
    gamma, boostA, q, dot3]

theorem coefficientMatrix_perturbation_exact (D : M3)
    (hD : ∀ i j, D i j = D j i) (beta : V3) :
    coefficientMatrix D beta - D =
      (gamma beta ^ 2 * sourceQuadratic D beta) • (1 : M3) +
      boostA beta • (outer beta (D.mulVec beta) + outer (D.mulVec beta) beta) +
      (boostA beta ^ 2 * sourceQuadratic D beta) • outer beta beta := by
  rw [coefficientMatrix_eq, timeCoefficient_exact]
  ext i j
  simp [spatialBlock, boostedB, outer, Matrix.mul_apply,
    Matrix.mulVec, dotProduct, Fintype.sum_option, Fin.sum_univ_succ,
    sourceQuadratic, dot3, spatialL, Matrix.add_apply, Matrix.sub_apply,
    Matrix.smul_apply]
  simp [hD]
  ring

end CoefficientMatrixBridge
