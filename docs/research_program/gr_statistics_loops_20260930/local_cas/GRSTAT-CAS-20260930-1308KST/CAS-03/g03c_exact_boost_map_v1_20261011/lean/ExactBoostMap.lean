import Mathlib

namespace ExactBoostMap

abbrev V3 := Fin 3 → ℝ
abbrev I4 := Option (Fin 3)
abbrev V4 := I4 → ℝ
abbrev M3 := Matrix (Fin 3) (Fin 3) ℝ
abbrev M4 := Matrix I4 I4 ℝ

def dot3 (x y : V3) : ℝ := ∑ i, x i * y i
def q (beta : V3) : ℝ := dot3 beta beta
noncomputable def gamma (beta : V3) : ℝ := 1 / Real.sqrt (1 - q beta)
noncomputable def boostA (beta : V3) : ℝ := gamma beta ^ 2 / (gamma beta + 1)
noncomputable def spatialL (beta : V3) (i j : Fin 3) : ℝ :=
  (if i = j then 1 else 0) + boostA beta * beta i * beta j
def eta : M4 := fun i j => if i = j then (if i = none then -1 else 1) else 0
noncomputable def boost (beta : V3) : M4 := fun i j =>
  match i, j with
  | none, none => gamma beta
  | none, some k => gamma beta * beta k
  | some k, none => gamma beta * beta k
  | some k, some l => spatialL beta k l
def restB (D : M3) : M4 := fun i j =>
  match i, j with
  | some k, some l => D k l
  | _, _ => 0
noncomputable def boostedB (D : M3) (beta : V3) : M4 :=
  Matrix.transpose (boost beta) * restB D * boost beta
def sourceQuadratic (D : M3) (beta : V3) : ℝ := dot3 beta (D.mulVec beta)
noncomputable def dipoleMap (D : M3) (beta : V3) : V3 :=
  fun i => -2 * boostedB D beta none (some i)
def observerNull (n : V3) : V4 := fun
  | none => -1
  | some i => n i
noncomputable def redshiftFromBoost (beta n : V3) : ℝ :=
  -(Matrix.mulVec (boost beta) (observerNull n)) none

private theorem q_nonneg (beta : V3) : 0 ≤ q beta := by
  unfold q dot3
  apply Finset.sum_nonneg
  intro i hi
  nlinarith [sq_nonneg (beta i)]

theorem gamma_pos (beta : V3) (hbeta : q beta < 1) : 0 < gamma beta := by
  unfold gamma
  positivity

private theorem sqrt_sq (beta : V3) (hbeta : q beta < 1) :
    Real.sqrt (1 - q beta) ^ 2 = 1 - q beta := by
  exact Real.sq_sqrt (le_of_lt (sub_pos.mpr hbeta))

theorem gamma_sq_mul_one_sub_q (beta : V3) (hbeta : q beta < 1) :
    gamma beta ^ 2 * (1 - q beta) = 1 := by
  have hs : Real.sqrt (1 - q beta) ≠ 0 := ne_of_gt (Real.sqrt_pos.2 (sub_pos.mpr hbeta))
  rw [← sqrt_sq beta hbeta]
  unfold gamma
  field_simp

theorem boostA_mul_q (beta : V3) (hbeta : q beta < 1) :
    boostA beta * q beta = gamma beta - 1 := by
  have hg := gamma_sq_mul_one_sub_q beta hbeta
  have hp := gamma_pos beta hbeta
  have hn : gamma beta + 1 ≠ 0 := by positivity
  unfold boostA
  rw [div_mul_eq_mul_div]
  apply (div_eq_iff hn).2
  nlinarith

private theorem boostA_mul_gamma_add_one (beta : V3) (hbeta : q beta < 1) :
    boostA beta * (gamma beta + 1) = gamma beta ^ 2 := by
  unfold boostA
  have hn : gamma beta + 1 ≠ 0 := by have := gamma_pos beta hbeta; positivity
  field_simp

private theorem boostA_spatial_relation (beta : V3) (hbeta : q beta < 1) :
    boostA beta ^ 2 * q beta + 2 * boostA beta = gamma beta ^ 2 := by
  calc
    boostA beta ^ 2 * q beta + 2 * boostA beta =
        boostA beta * (boostA beta * q beta + 2) := by ring
    _ = boostA beta * (gamma beta + 1) := by rw [boostA_mul_q beta hbeta]; ring
    _ = gamma beta ^ 2 := boostA_mul_gamma_add_one beta hbeta

set_option maxHeartbeats 2000000 in
theorem boost_lorentz (beta : V3) (hbeta : q beta < 1) :
    Matrix.transpose (boost beta) * eta * boost beta = eta := by
  have hg := gamma_sq_mul_one_sub_q beta hbeta
  have ha := boostA_mul_q beta hbeta
  have hs := boostA_spatial_relation beta hbeta
  simp [q, dot3, Fin.sum_univ_succ] at hg ha hs
  have ha0 := congrArg (fun x : ℝ => gamma beta * beta 0 * x) ha
  have ha1 := congrArg (fun x : ℝ => gamma beta * beta 1 * x) ha
  have ha2 := congrArg (fun x : ℝ => gamma beta * beta 2 * x) ha
  have hs00 := congrArg (fun x : ℝ => beta 0 * beta 0 * x) hs
  have hs01 := congrArg (fun x : ℝ => beta 0 * beta 1 * x) hs
  have hs02 := congrArg (fun x : ℝ => beta 0 * beta 2 * x) hs
  have hs11 := congrArg (fun x : ℝ => beta 1 * beta 1 * x) hs
  have hs12 := congrArg (fun x : ℝ => beta 1 * beta 2 * x) hs
  have hs22 := congrArg (fun x : ℝ => beta 2 * beta 2 * x) hs
  ext i j
  fin_cases i <;> fin_cases j <;>
    simp [Matrix.mul_apply, Fintype.sum_option, Fin.sum_univ_succ,
      boost, eta, spatialL] <;>
    nlinarith [hg, ha0, ha1, ha2, hs00, hs01, hs02, hs11, hs12, hs22]

theorem redshiftFromBoost_eq (beta n : V3) :
    redshiftFromBoost beta n = gamma beta * (1 - dot3 beta n) := by
  simp [redshiftFromBoost, Matrix.mulVec, dotProduct,
    Fintype.sum_option, dot3, observerNull, boost, Fin.sum_univ_succ]
  ring

private theorem time_rest_none (D : M3) (beta : V3) :
    (Matrix.transpose (boost beta) * restB D) none none = 0 := by
  change (∑ k : I4, boost beta k none * restB D k none) = 0
  apply Finset.sum_eq_zero
  intro k hk
  cases k <;> simp [restB]

private theorem time_rest_some
    (D : M3) (hD : ∀ i j, D i j = D j i)
    (beta : V3) (j : Fin 3) :
    (Matrix.transpose (boost beta) * restB D) none (some j) =
      gamma beta * D.mulVec beta j := by
  change
    (∑ k : I4, boost beta k none * restB D k (some j)) =
      gamma beta * ∑ k : Fin 3, D j k * beta k
  rw [Fintype.sum_option]
  simp only [boost, restB, mul_zero, zero_add, add_zero]
  rw [Finset.mul_sum]
  apply Finset.sum_congr rfl
  intro k hk
  rw [hD k j]
  ring

private theorem sum_mul_spatialL
    (v beta : V3) (i : Fin 3) :
    (∑ j, v j * spatialL beta j i) =
      v i + boostA beta * beta i * dot3 beta v := by
  classical
  simp only [spatialL, mul_add, Finset.sum_add_distrib]
  have hdiag :
      (∑ j : Fin 3, v j * (if j = i then (1 : ℝ) else 0)) =
        v i := by
    simp
  rw [hdiag]
  congr 1
  unfold dot3
  rw [Finset.mul_sum]
  apply Finset.sum_congr rfl
  intro j hj
  ring

private theorem boostedB_time_space
    (D : M3) (hD : ∀ i j, D i j = D j i)
    (beta : V3) (i : Fin 3) :
    boostedB D beta none (some i) =
      gamma beta *
        (D.mulVec beta i +
          boostA beta * beta i * sourceQuadratic D beta) := by
  change
    (∑ k : I4,
      (Matrix.transpose (boost beta) * restB D) none k *
        boost beta k (some i)) = _
  rw [Fintype.sum_option]
  simp only [time_rest_none, time_rest_some D hD beta,
    zero_mul, zero_add, add_zero, boost]
  calc
    _ = gamma beta *
        (∑ k : Fin 3, D.mulVec beta k * spatialL beta k i) := by
          rw [Finset.mul_sum]
          apply Finset.sum_congr rfl
          intro k hk
          ring
    _ = _ := by
      rw [sum_mul_spatialL]
      rfl

theorem dipoleMap_exact (D : M3) (hD : ∀ i j, D i j = D j i) (beta : V3) :
    dipoleMap D beta = fun i =>
      -2 * gamma beta * (D.mulVec beta i +
        boostA beta * beta i * sourceQuadratic D beta) := by
  funext i
  dsimp only [dipoleMap]
  rw [boostedB_time_space D hD beta i]
  ring

#print axioms gamma_pos
#print axioms gamma_sq_mul_one_sub_q
#print axioms boostA_mul_q
#print axioms boost_lorentz
#print axioms redshiftFromBoost_eq
#print axioms dipoleMap_exact

end ExactBoostMap
