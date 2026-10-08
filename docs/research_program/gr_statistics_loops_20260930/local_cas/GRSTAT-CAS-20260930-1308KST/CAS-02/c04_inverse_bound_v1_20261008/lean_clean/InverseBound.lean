import Mathlib

open scoped Matrix.Norms.Frobenius

namespace CAS02C04

abbrev Vec4 := EuclideanSpace ℝ (Fin 4)
abbrev Vec3 := EuclideanSpace ℝ (Fin 3)
abbrev Mat4 := Matrix (Fin 4) (Fin 4) ℝ

def metric : Mat4 := Matrix.diagonal ![-1, 1, 1, 1]

theorem metric_frobenius_norm : ‖metric‖ = 2 := by
  simp [metric, Matrix.frobenius_norm_diagonal, PiLp.norm_eq_of_L2,
    Fin.sum_univ_four]
  norm_num

noncomputable def future (d : Vec3) : Vec4 :=
  (EuclideanSpace.equiv (Fin 4) ℝ).symm ![Real.sqrt (1 + ‖d‖ ^ 2), d 0, d 1, d 2]

theorem future_norm_sq (d : Vec3) : ‖future d‖ ^ 2 = 1 + 2 * ‖d‖ ^ 2 := by
  simp only [EuclideanSpace.real_norm_sq_eq]
  simp [future, Fin.sum_univ_four, Fin.sum_univ_three]
  rw [Real.sq_sqrt (by positivity)]
  rw [EuclideanSpace.real_norm_sq_eq d]
  simp only [Fin.sum_univ_three]
  ring

noncomputable def rapidityCap (R : ℝ) : ℝ := Real.sqrt (Real.cosh (2 * R))

theorem rapidity_nonneg_of_admitted (d : Vec3) (R : ℝ)
    (hd : ‖d‖ ≤ Real.sinh R) : 0 ≤ R := by
  exact Real.sinh_nonneg_iff.mp ((norm_nonneg d).trans hd)

theorem future_norm_le_cap (d : Vec3) (R : ℝ)
    (hd : ‖d‖ ≤ Real.sinh R) : ‖future d‖ ≤ rapidityCap R := by
  have hR := rapidity_nonneg_of_admitted d R hd
  have hs : 0 ≤ Real.sinh R := Real.sinh_nonneg_iff.mpr hR
  have hsq : ‖d‖ ^ 2 ≤ (Real.sinh R) ^ 2 := by
    nlinarith [mul_nonneg (sub_nonneg.mpr hd) (add_nonneg (norm_nonneg d) hs)]
  have hc : Real.cosh (2 * R) = 1 + 2 * (Real.sinh R) ^ 2 := by
    nlinarith [Real.cosh_two_mul R, Real.cosh_sq_sub_sinh_sq R]
  have hm : (rapidityCap R) ^ 2 = Real.cosh (2 * R) := by
    exact Real.sq_sqrt (le_of_lt (Real.cosh_pos _))
  have hmn : 0 ≤ rapidityCap R := Real.sqrt_nonneg _
  nlinarith [future_norm_sq d, norm_nonneg (future d)]

def col (u : Vec4) : Matrix (Fin 4) (Fin 1) ℝ := Matrix.replicateCol (Fin 1) u
def row (u : Vec4) : Matrix (Fin 1) (Fin 4) ℝ := Matrix.replicateRow (Fin 1) u

def quad (S : Mat4) (u : Vec4) : ℝ := (row u * (S * col u)) 0 0

noncomputable def spectral (S : Mat4) : ℝ :=
  @norm Mat4 Matrix.instL2OpNormedAddCommGroup.toNorm S

noncomputable def lin (S : Mat4) : Vec4 →L[ℝ] Vec4 :=
  (Matrix.toEuclideanCLM (n := Fin 4) (𝕜 := ℝ)) S

theorem quad_inner (S : Mat4) (u : Vec4) :
    quad S u = inner ℝ u ((EuclideanSpace.equiv (Fin 4) ℝ).symm (Matrix.mulVec S u)) := by
  simp [quad, row, col, Matrix.mul_apply, Matrix.mulVec, dotProduct,
    PiLp.inner_apply]
  exact Finset.sum_congr rfl (fun i _ => mul_comm (u i) _)

theorem quad_clm (S : Mat4) (u : Vec4) :
    quad S u = inner ℝ u (lin S u) := by
  rw [quad_inner]
  rfl

theorem spectral_eq_clm_norm (S : Mat4) :
    spectral S = ‖lin S‖ := by
  rfl

theorem quad_sub_matrix (S T : Mat4) (u : Vec4) :
    quad (S - T) u = quad S u - quad T u := by
  simp [quad_clm, lin, map_sub, sub_apply, inner_sub_right]

theorem quad_difference_fixed (S : Mat4) (u v : Vec4) :
    quad S u - quad S v =
      inner ℝ (u - v) (lin S u) +
      inner ℝ v (lin S (u - v)) := by
  simp only [quad_clm, inner_sub_left, map_sub, inner_sub_right]
  ring

theorem one_by_one_norm (A : Matrix (Fin 1) (Fin 1) ℝ) : ‖A‖ = |A 0 0| := by
  rw [Matrix.frobenius_norm_def]
  simp only [Fin.sum_univ_one, Real.norm_eq_abs]
  rw [← Real.sqrt_eq_rpow]
  simpa [abs_abs] using (Real.sqrt_sq_eq_abs |A 0 0|)

theorem col_norm (u : Vec4) : ‖col u‖ = ‖u‖ := by
  exact Matrix.frobenius_norm_replicateCol u

theorem row_norm (u : Vec4) : ‖row u‖ = ‖u‖ := by
  exact Matrix.frobenius_norm_replicateRow u

theorem quad_frobenius_bound (S : Mat4) (u : Vec4) :
    |quad S u| ≤ ‖S‖ * ‖u‖ ^ 2 := by
  have h1 := Matrix.frobenius_norm_mul (row u) (S * col u)
  have h2 := Matrix.frobenius_norm_mul S (col u)
  rw [one_by_one_norm, ← quad] at h1
  rw [row_norm] at h1
  rw [col_norm] at h2
  nlinarith [mul_nonneg (sub_nonneg.mpr h2) (norm_nonneg u)]

theorem quad_spectral_bound (S : Mat4) (u : Vec4) :
    |quad S u| ≤ spectral S * ‖u‖ ^ 2 := by
  let w : Vec4 := (EuclideanSpace.equiv (Fin 4) ℝ).symm (Matrix.mulVec S u)
  have hinner : |quad S u| ≤ ‖u‖ * ‖w‖ := by
    rw [quad_inner]
    exact abs_real_inner_le_norm u w
  have hm : ‖w‖ ≤ spectral S * ‖u‖ := by
    letI : NormedAddCommGroup Mat4 := Matrix.instL2OpNormedAddCommGroup
    simpa only [w, spectral] using (Matrix.l2_opNorm_mulVec S u)
  nlinarith [mul_nonneg (sub_nonneg.mpr hm) (norm_nonneg u)]

theorem quad_fixed_lipschitz (S : Mat4) (u v : Vec4) :
    |quad S u - quad S v| ≤ spectral S * (‖u‖ + ‖v‖) * ‖u - v‖ := by
  let T := lin S
  have hTu : ‖T u‖ ≤ spectral S * ‖u‖ := by
    simpa [T, spectral_eq_clm_norm] using (T.le_opNorm u)
  have hTd : ‖T (u - v)‖ ≤ spectral S * ‖u - v‖ := by
    simpa [T, spectral_eq_clm_norm] using (T.le_opNorm (u - v))
  have h1 := abs_real_inner_le_norm (u - v) (T u)
  have h2 := abs_real_inner_le_norm v (T (u - v))
  have h1' : |inner ℝ (u - v) (T u)| ≤ ‖u - v‖ * (spectral S * ‖u‖) :=
    h1.trans (mul_le_mul_of_nonneg_left hTu (norm_nonneg _))
  have h2' : |inner ℝ v (T (u - v))| ≤ ‖v‖ * (spectral S * ‖u - v‖) :=
    h2.trans (mul_le_mul_of_nonneg_left hTd (norm_nonneg _))
  rw [quad_difference_fixed]
  calc
    |inner ℝ (u - v) (T u) + inner ℝ v (T (u - v))| ≤
        |inner ℝ (u - v) (T u)| + |inner ℝ v (T (u - v))| := abs_add_le _ _
    _ ≤ ‖u - v‖ * (spectral S * ‖u‖) + ‖v‖ * (spectral S * ‖u - v‖) :=
      add_le_add h1' h2'
    _ = spectral S * (‖u‖ + ‖v‖) * ‖u - v‖ := by ring

theorem spectral_nonneg (S : Mat4) : 0 ≤ spectral S := by
  rw [spectral_eq_clm_norm]
  exact norm_nonneg _

theorem quad_pair_bound (S₁ S₂ : Mat4) (u₁ u₂ : Vec4) (M : ℝ)
    (h₁ : ‖u₁‖ ≤ M) (h₂ : ‖u₂‖ ≤ M) :
    |quad S₂ u₂ - quad S₁ u₁| ≤
      ‖S₂ - S₁‖ * M ^ 2 +
      2 * M * min (spectral S₁) (spectral S₂) * ‖u₂ - u₁‖ := by
  have hM : 0 ≤ M := (norm_nonneg u₁).trans h₁
  have hsum : ‖u₂‖ + ‖u₁‖ ≤ 2 * M := by linarith
  have hsq₁ : ‖u₁‖ ^ 2 ≤ M ^ 2 := by gcongr
  have hsq₂ : ‖u₂‖ ^ 2 ≤ M ^ 2 := by gcongr
  rcases le_total (spectral S₁) (spectral S₂) with hmin | hmin
  · rw [min_eq_left hmin]
    have hid : quad S₂ u₂ - quad S₁ u₁ =
        quad (S₂ - S₁) u₂ + (quad S₁ u₂ - quad S₁ u₁) := by
      rw [quad_sub_matrix]
      ring
    rw [hid]
    calc
      |quad (S₂ - S₁) u₂ + (quad S₁ u₂ - quad S₁ u₁)| ≤
          |quad (S₂ - S₁) u₂| + |quad S₁ u₂ - quad S₁ u₁| := abs_add_le _ _
      _ ≤ ‖S₂ - S₁‖ * ‖u₂‖ ^ 2 +
          spectral S₁ * (‖u₂‖ + ‖u₁‖) * ‖u₂ - u₁‖ :=
        add_le_add (quad_frobenius_bound _ _) (quad_fixed_lipschitz _ _ _)
      _ ≤ ‖S₂ - S₁‖ * M ^ 2 + 2 * M * spectral S₁ * ‖u₂ - u₁‖ := by
        have ha := mul_le_mul_of_nonneg_left hsq₂ (norm_nonneg (S₂ - S₁))
        have hb := mul_le_mul_of_nonneg_right
          (mul_le_mul_of_nonneg_left hsum (spectral_nonneg S₁)) (norm_nonneg (u₂ - u₁))
        nlinarith
  · rw [min_eq_right hmin]
    have hid : quad S₂ u₂ - quad S₁ u₁ =
        quad (S₂ - S₁) u₁ + (quad S₂ u₂ - quad S₂ u₁) := by
      rw [quad_sub_matrix]
      ring
    rw [hid]
    calc
      |quad (S₂ - S₁) u₁ + (quad S₂ u₂ - quad S₂ u₁)| ≤
          |quad (S₂ - S₁) u₁| + |quad S₂ u₂ - quad S₂ u₁| := abs_add_le _ _
      _ ≤ ‖S₂ - S₁‖ * ‖u₁‖ ^ 2 +
          spectral S₂ * (‖u₂‖ + ‖u₁‖) * ‖u₂ - u₁‖ :=
        add_le_add (quad_frobenius_bound _ _) (quad_fixed_lipschitz _ _ _)
      _ ≤ ‖S₂ - S₁‖ * M ^ 2 + 2 * M * spectral S₂ * ‖u₂ - u₁‖ := by
        have ha := mul_le_mul_of_nonneg_left hsq₁ (norm_nonneg (S₂ - S₁))
        have hb := mul_le_mul_of_nonneg_right
          (mul_le_mul_of_nonneg_left hsum (spectral_nonneg S₂)) (norm_nonneg (u₂ - u₁))
        nlinarith

def inverse (S : Mat4) (u : Vec4) : Mat4 := S + quad S u • metric

theorem inverse_pair_bound (S₁ S₂ : Mat4) (u₁ u₂ : Vec4) (M : ℝ)
    (h₁ : ‖u₁‖ ≤ M) (h₂ : ‖u₂‖ ≤ M) :
    ‖inverse S₂ u₂ - inverse S₁ u₁‖ ≤
      (1 + 2 * M ^ 2) * ‖S₂ - S₁‖ +
      4 * M * min (spectral S₁) (spectral S₂) * ‖u₂ - u₁‖ := by
  have hid : inverse S₂ u₂ - inverse S₁ u₁ =
      (S₂ - S₁) + (quad S₂ u₂ - quad S₁ u₁) • metric := by
    simp [inverse, sub_smul]
    abel
  rw [hid]
  calc
    ‖(S₂ - S₁) + (quad S₂ u₂ - quad S₁ u₁) • metric‖ ≤
        ‖S₂ - S₁‖ + ‖(quad S₂ u₂ - quad S₁ u₁) • metric‖ := norm_add_le _ _
    _ = ‖S₂ - S₁‖ + 2 * |quad S₂ u₂ - quad S₁ u₁| := by
      rw [norm_smul, metric_frobenius_norm, Real.norm_eq_abs]
      ring
    _ ≤ ‖S₂ - S₁‖ + 2 *
        (‖S₂ - S₁‖ * M ^ 2 +
          2 * M * min (spectral S₁) (spectral S₂) * ‖u₂ - u₁‖) := by
      gcongr
      exact quad_pair_bound S₁ S₂ u₁ u₂ M h₁ h₂
    _ = (1 + 2 * M ^ 2) * ‖S₂ - S₁‖ +
        4 * M * min (spectral S₁) (spectral S₂) * ‖u₂ - u₁‖ := by ring

theorem CAS_02_C04 (S₁ S₂ : Mat4) (d₁ d₂ : Vec3) (R : ℝ)
    (hd₁ : ‖d₁‖ ≤ Real.sinh R) (hd₂ : ‖d₂‖ ≤ Real.sinh R) :
    ‖inverse S₂ (future d₂) - inverse S₁ (future d₁)‖ ≤
      (1 + 2 * (rapidityCap R) ^ 2) * ‖S₂ - S₁‖ +
      4 * rapidityCap R * min (spectral S₁) (spectral S₂) *
        ‖future d₂ - future d₁‖ := by
  exact inverse_pair_bound S₁ S₂ (future d₁) (future d₂) (rapidityCap R)
    (future_norm_le_cap d₁ R hd₁) (future_norm_le_cap d₂ R hd₂)

theorem rapidity_zero_forces_d_zero (d : Vec3)
    (hd : ‖d‖ ≤ Real.sinh 0) : d = 0 := by
  have hz : ‖d‖ = 0 := le_antisymm (by simpa using hd) (norm_nonneg d)
  exact norm_eq_zero.mp hz

theorem epsilonH_zero_forces_S_equal (S₁ S₂ : Mat4)
    (h : ‖S₂ - S₁‖ = 0) : S₂ = S₁ := by
  exact sub_eq_zero.mp (norm_eq_zero.mp h)

theorem epsilonZ_zero_forces_u_equal (u₁ u₂ : Vec4)
    (h : ‖u₂ - u₁‖ = 0) : u₂ = u₁ := by
  exact sub_eq_zero.mp (norm_eq_zero.mp h)

#print axioms CAS02C04.CAS_02_C04

end CAS02C04
