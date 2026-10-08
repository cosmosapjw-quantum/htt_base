import Mathlib

/-!
PORT-CAS-01: exact finite Lorentz boost algebra, signature (-,+,+,+).
All velocities and four-velocities here are dimensionless (u = U/c).
-/

namespace PortCas01

def s (x y z : ℝ) : ℝ := x ^ 2 + y ^ 2 + z ^ 2
noncomputable def gamma (x y z : ℝ) : ℝ := 1 / Real.sqrt (1 - s x y z)
noncomputable def h (x y z : ℝ) : ℝ := gamma x y z ^ 2 / (gamma x y z + 1)

def eta : Matrix (Fin 4) (Fin 4) ℝ :=
  !![-1, 0, 0, 0;
      0, 1, 0, 0;
      0, 0, 1, 0;
      0, 0, 0, 1]

def boost (g q x y z : ℝ) : Matrix (Fin 4) (Fin 4) ℝ :=
  !![g, g*x, g*y, g*z;
      g*x, 1+q*x*x, q*x*y, q*x*z;
      g*y, q*y*x, 1+q*y*y, q*y*z;
      g*z, q*z*x, q*z*y, 1+q*z*z]

def boostNeg (g q x y z : ℝ) : Matrix (Fin 4) (Fin 4) ℝ :=
  boost g q (-x) (-y) (-z)

def e0 : Fin 4 → ℝ := ![1, 0, 0, 0]

private theorem core_relations (x y z : ℝ) (hs : s x y z < 1) :
    0 < gamma x y z ∧
    gamma x y z ^ 2 * (1 - s x y z) = 1 ∧
    h x y z * s x y z = gamma x y z - 1 ∧
    2 * h x y z + h x y z ^ 2 * s x y z = gamma x y z ^ 2 := by
  have hp : 0 < 1 - s x y z := by linarith
  have hroot : 0 < Real.sqrt (1 - s x y z) := Real.sqrt_pos.2 hp
  have hroot2 : Real.sqrt (1 - s x y z) ^ 2 = 1 - s x y z := Real.sq_sqrt hp.le
  have hg : 0 < gamma x y z := by
    unfold gamma
    positivity
  have hgsq : gamma x y z ^ 2 * (1 - s x y z) = 1 := by
    unfold gamma
    field_simp
    nlinarith
  have hgn : gamma x y z + 1 ≠ 0 := by positivity
  have hh : h x y z * (gamma x y z + 1) = gamma x y z ^ 2 := by
    unfold h
    field_simp
  have hhs : h x y z * s x y z = gamma x y z - 1 := by
    have hsquared : gamma x y z ^ 2 * s x y z = gamma x y z ^ 2 - 1 := by
      nlinarith [hgsq]
    calc
      h x y z * s x y z = gamma x y z ^ 2 * s x y z / (gamma x y z + 1) := by
        unfold h
        ring
      _ = (gamma x y z ^ 2 - 1) / (gamma x y z + 1) := by rw [hsquared]
      _ = gamma x y z - 1 := by
        field_simp
        ring
  have hhc : 2 * h x y z + h x y z ^ 2 * s x y z = gamma x y z ^ 2 := by
    calc
      2 * h x y z + h x y z ^ 2 * s x y z =
          h x y z * (2 + h x y z * s x y z) := by ring
      _ = h x y z * (gamma x y z + 1) := by rw [hhs]; ring
      _ = gamma x y z ^ 2 := hh
  exact ⟨hg, hgsq, hhs, hhc⟩

theorem metric_identity (x y z : ℝ) (hs : s x y z < 1) :
    Matrix.transpose (boost (gamma x y z) (h x y z) x y z) * eta *
      boost (gamma x y z) (h x y z) x y z = eta := by
  obtain ⟨hg, hgsq, hhs, hhc⟩ := core_relations x y z hs
  simp only [s] at hgsq hhs hhc
  ext i j
  fin_cases i <;> fin_cases j <;>
    simp [Matrix.mul_apply, Fin.sum_univ_four, boost, eta, Matrix.transpose_apply] <;>
    first
    | linear_combination -hgsq
    | linear_combination (gamma x y z * x) * hhs
    | linear_combination (gamma x y z * y) * hhs
    | linear_combination (gamma x y z * z) * hhs
    | linear_combination (x * x) * hhc
    | linear_combination (x * y) * hhc
    | linear_combination (x * z) * hhc
    | linear_combination (y * x) * hhc
    | linear_combination (y * y) * hhc
    | linear_combination (y * z) * hhc
    | linear_combination (z * x) * hhc
    | linear_combination (z * y) * hhc
    | linear_combination (z * z) * hhc

theorem inverse_identity (x y z : ℝ) (hs : s x y z < 1) :
    boost (gamma x y z) (h x y z) x y z *
      boostNeg (gamma x y z) (h x y z) x y z = 1 := by
  obtain ⟨hg, hgsq, hhs, hhc⟩ := core_relations x y z hs
  simp only [s] at hgsq hhs hhc
  ext i j
  fin_cases i <;> fin_cases j <;>
    simp [Matrix.mul_apply, Fin.sum_univ_four, boost, boostNeg] <;>
    first
    | linear_combination hgsq
    | linear_combination -hgsq
    | linear_combination (gamma x y z * x) * hhs
    | linear_combination (gamma x y z * y) * hhs
    | linear_combination (gamma x y z * z) * hhs
    | linear_combination -(gamma x y z * x) * hhs
    | linear_combination -(gamma x y z * y) * hhs
    | linear_combination -(gamma x y z * z) * hhs
    | linear_combination (x * x) * hhc
    | linear_combination (x * y) * hhc
    | linear_combination (x * z) * hhc
    | linear_combination (y * x) * hhc
    | linear_combination (y * y) * hhc
    | linear_combination (y * z) * hhc
    | linear_combination (z * x) * hhc
    | linear_combination (z * y) * hhc
    | linear_combination (z * z) * hhc

noncomputable def fourVelocity (x y z : ℝ) : Fin 4 → ℝ :=
  Matrix.mulVec (boost (gamma x y z) (h x y z) x y z) e0

theorem fourVelocity_components (x y z : ℝ) :
    fourVelocity x y z =
      ![gamma x y z, gamma x y z * x, gamma x y z * y, gamma x y z * z] := by
  funext i
  fin_cases i <;>
    simp [fourVelocity, Matrix.mulVec, dotProduct, Fin.sum_univ_four, boost, e0]

theorem future_mass_shell (x y z : ℝ) (hs : s x y z < 1) :
    0 < fourVelocity x y z 0 ∧
    dotProduct (fourVelocity x y z) (Matrix.mulVec eta (fourVelocity x y z)) = -1 := by
  obtain ⟨hg, hgsq, _, _⟩ := core_relations x y z hs
  rw [fourVelocity_components]
  constructor
  · simpa using hg
  · simp [Matrix.mulVec, dotProduct, Fin.sum_univ_four, eta, s] at *
    nlinarith [hgsq]

theorem future_converse (t x y z : ℝ)
    (ht : 1 ≤ t) (hshell : t ^ 2 - s x y z = 1) :
    s (x / t) (y / t) (z / t) < 1 ∧
    fourVelocity (x / t) (y / t) (z / t) = ![t, x, y, z] := by
  have htpos : 0 < t := by linarith
  have htnz : t ≠ 0 := ne_of_gt htpos
  have htsq : 0 < t ^ 2 := sq_pos_of_pos htpos
  have hbeta : s (x / t) (y / t) (z / t) = s x y z / t ^ 2 := by
    unfold s
    field_simp
  have hone : 1 - s (x / t) (y / t) (z / t) = (1 / t) ^ 2 := by
    rw [hbeta]
    field_simp
    nlinarith [hshell]
  have hb : s (x / t) (y / t) (z / t) < 1 := by
    rw [← sub_pos]
    rw [hone]
    positivity
  have hgam : gamma (x / t) (y / t) (z / t) = t := by
    unfold gamma
    rw [hone, Real.sqrt_sq_eq_abs, abs_of_pos (one_div_pos.mpr htpos)]
    field_simp
  refine ⟨hb, ?_⟩
  rw [fourVelocity_components, hgam]
  funext i
  fin_cases i <;> simp <;> field_simp

theorem zero_boost : boost (gamma 0 0 0) (h 0 0 0) 0 0 0 = 1 := by
  ext i j
  fin_cases i <;> fin_cases j <;>
    norm_num [boost, gamma, h, s]

theorem zero_fourVelocity : fourVelocity 0 0 0 = e0 := by
  rw [fourVelocity_components]
  funext i
  fin_cases i <;> norm_num [gamma, s, e0]

end PortCas01

#print axioms PortCas01.metric_identity
#print axioms PortCas01.inverse_identity
#print axioms PortCas01.future_mass_shell
#print axioms PortCas01.future_converse
#print axioms PortCas01.zero_boost
#print axioms PortCas01.zero_fourVelocity
