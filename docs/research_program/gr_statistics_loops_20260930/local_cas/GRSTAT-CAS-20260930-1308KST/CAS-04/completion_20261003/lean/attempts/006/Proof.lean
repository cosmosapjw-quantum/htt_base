import Mathlib

namespace GRSTATCAS04

open Finset

abbrev Arr := Fin 4 → Fin 3 → ℝ
abbrev Vec4 := Fin 4 → ℝ
abbrev Mat4 := Fin 4 → Fin 4 → ℝ

def lorentzDot (v w : Vec4) : ℝ :=
  -(v 0 * w 0) + v 1 * w 1 + v 2 * w 2 + v 3 * w 3

def matVec (t : Mat4) (v : Vec4) : Vec4 :=
  fun a => ∑ b : Fin 4, t a b * v b

def restProj (u v : Vec4) : Vec4 :=
  fun a => v a + lorentzDot u v * u a

theorem lorentzDot_add_right (u v w : Vec4) :
    lorentzDot u (v + w) = lorentzDot u v + lorentzDot u w := by
  simp [lorentzDot, Pi.add_apply]
  ring

theorem lorentzDot_smul_right (u v : Vec4) (r : ℝ) :
    lorentzDot u (r • v) = r * lorentzDot u v := by
  simp [lorentzDot, Pi.smul_apply, smul_eq_mul]
  ring

theorem restProj_add (u v w : Vec4) :
    restProj u (v + w) = restProj u v + restProj u w := by
  funext a
  simp [restProj, lorentzDot_add_right, Pi.add_apply]
  ring

theorem restProj_smul (u v : Vec4) (r : ℝ) :
    restProj u (r • v) = r • restProj u v := by
  funext a
  simp [restProj, lorentzDot_smul_right, Pi.smul_apply, smul_eq_mul]
  ring

theorem restProj_self (u : Vec4) (hn : lorentzDot u u = -1) :
    restProj u u = 0 := by
  funext a
  simp [restProj, hn]

theorem restProj_tangent (u v : Vec4) (ho : lorentzDot u v = 0) :
    restProj u v = v := by
  funext a
  simp [restProj, ho]

theorem matVec_add (t : Mat4) (v w : Vec4) :
    matVec t (v + w) = matVec t v + matVec t w := by
  funext a
  simp [matVec, Finset.sum_add_distrib, mul_add, Pi.add_apply]

theorem matVec_smul (t : Mat4) (v : Vec4) (r : ℝ) :
    matVec t (r • v) = r • matVec t v := by
  funext a
  simp [matVec, mul_comm, mul_left_comm, mul_assoc, Finset.mul_sum, Pi.smul_apply, smul_eq_mul]

theorem eigen_product_derivative
    (t : ℝ → Mat4) (u : ℝ → Vec4) (e : ℝ → ℝ)
    (t₀ : ℝ) (dt : Mat4) (du : Vec4) (de : ℝ)
    (ht : ∀ a b, HasDerivAt (fun s => t s a b) (dt a b) t₀)
    (hu : ∀ a, HasDerivAt (fun s => u s a) (du a) t₀)
    (he : HasDerivAt e de t₀)
    (hEig : ∀ s, matVec (t s) (u s) = (-e s) • u s) :
    matVec dt (u t₀) + matVec (t t₀) du =
      (-de) • u t₀ + (-e t₀) • du := by
  funext a
  have hp : HasDerivAt (fun s => matVec (t s) (u s) a)
      (∑ b : Fin 4, (dt a b * u t₀ b + t t₀ a b * du b)) t₀ := by
    simpa [matVec] using
      (HasDerivAt.fun_sum (u := Finset.univ)
        (fun b _ => (ht a b).mul (hu b)))
  have hn : HasDerivAt (fun s => matVec (t s) (u s) a)
      ((-de) * u t₀ a + (-e t₀) * du a) t₀ := by
    have h0 := he.neg.mul (hu a)
    have hf : (fun s => matVec (t s) (u s) a) =
        (fun s => (-e s) * u s a) := by
      funext s
      simpa only [Pi.smul_apply, smul_eq_mul] using congrFun (hEig s) a
    rw [hf]
    exact h0
  have huniq := hp.unique hn
  simpa [matVec, Pi.add_apply, Pi.smul_apply, smul_eq_mul, Finset.sum_add_distrib] using huniq

theorem normalization_derivative
    (u : ℝ → Vec4) (t₀ : ℝ) (du : Vec4)
    (hu : ∀ a, HasDerivAt (fun s => u s a) (du a) t₀)
    (hn : ∀ s, lorentzDot (u s) (u s) = -1) :
    lorentzDot (u t₀) du = 0 := by
  have hder : HasDerivAt (fun s => lorentzDot (u s) (u s))
      (2 * lorentzDot (u t₀) du) t₀ := by
    have hraw := (((hu 0).mul (hu 0)).neg.add ((hu 1).mul (hu 1)) |>.add ((hu 2).mul (hu 2)) |>.add ((hu 3).mul (hu 3)))
    have hcoef :
        (-(du 0 * u t₀ 0 + u t₀ 0 * du 0) +
          (du 1 * u t₀ 1 + u t₀ 1 * du 1) +
          (du 2 * u t₀ 2 + u t₀ 2 * du 2) +
          (du 3 * u t₀ 3 + u t₀ 3 * du 3)) =
          2 * lorentzDot (u t₀) du := by
      dsimp [lorentzDot]
      ring
    have hraw' : HasDerivAt (fun s => lorentzDot (u s) (u s))
        (-(du 0 * u t₀ 0 + u t₀ 0 * du 0) +
          (du 1 * u t₀ 1 + u t₀ 1 * du 1) +
          (du 2 * u t₀ 2 + u t₀ 2 * du 2) +
          (du 3 * u t₀ 3 + u t₀ 3 * du 3)) t₀ := by
      simpa only [lorentzDot] using hraw
    exact hraw'.congr_deriv hcoef
  have hconst : HasDerivAt (fun s => lorentzDot (u s) (u s)) 0 t₀ := by
    have hf : (fun s => lorentzDot (u s) (u s)) = (fun _ => (-1 : ℝ)) := funext hn
    rw [hf]
    exact hasDerivAt_const t₀ (-1 : ℝ)
  have := hder.unique hconst
  linarith

theorem projected_eigen_derivative
    (t : ℝ → Mat4) (u : ℝ → Vec4) (e : ℝ → ℝ)
    (t₀ c : ℝ) (dt : Mat4) (du : Vec4) (de : ℝ)
    (hc : 0 < c)
    (ht : ∀ a b, HasDerivAt (fun s => t s a b) (dt a b) t₀)
    (hu : ∀ a, HasDerivAt (fun s => u s a) (du a) t₀)
    (he : HasDerivAt e de t₀)
    (hn : ∀ s, lorentzDot (u s) (u s) = -1)
    (hEig : ∀ s, matVec (t s) (u s) = (-e s) • u s) :
    restProj (u t₀) (matVec (t t₀) (c • du)) +
      e t₀ • (c • du) =
      (-c) • restProj (u t₀) (matVec dt (u t₀)) := by
  have hd := eigen_product_derivative t u e t₀ dt du de ht hu he hEig
  have horth := normalization_derivative u t₀ du hu hn
  have hself := restProj_self (u t₀) (hn t₀)
  have htangent := restProj_tangent (u t₀) du horth
  have hproj := congrArg (restProj (u t₀)) hd
  rw [restProj_add, restProj_add, restProj_smul, restProj_smul,
      hself, htangent] at hproj
  simp only [smul_zero, add_zero] at hproj
  rw [matVec_smul, restProj_smul]
  funext a
  have ha := congrFun hproj a
  simp only [Pi.add_apply, Pi.smul_apply, smul_eq_mul] at ha ⊢
  simp only [Pi.zero_apply, zero_add] at ha
  linear_combination c * ha

def theta (q : Arr) : ℝ := ∑ i : Fin 3, q i.succ i
noncomputable def sigma (q : Arr) (i j : Fin 3) : ℝ :=
  (q i.succ j + q j.succ i) / 2 - (if i = j then theta q / 3 else 0)
noncomputable def skew (q : Arr) (i j : Fin 3) : ℝ :=
  (q i.succ j - q j.succ i) / 2
noncomputable def omega (q : Arr) : Fin 3 → ℝ
  | 0 => skew q 1 2
  | 1 => skew q 2 0
  | 2 => skew q 0 1

theorem spatial_orthogonal_decomposition (q : Arr) :
    (theta q)^2 / 3 + (∑ i : Fin 3, ∑ j : Fin 3, (sigma q i j)^2) +
      2 * (∑ i : Fin 3, (omega q i)^2) =
      ∑ i : Fin 3, ∑ j : Fin 3, (q i.succ j)^2 := by
  simp [theta, sigma, omega, skew, Fin.sum_univ_succ]
  ring

def accel (c : ℝ) (q : Arr) (i : Fin 3) : ℝ := c * q 0 i

theorem rate_four_by_three (c : ℝ) (q : Arr) (hc : c ≠ 0) :
    (theta q)^2 / 3 + (∑ i : Fin 3, ∑ j : Fin 3, (sigma q i j)^2) +
      2 * (∑ i : Fin 3, (omega q i)^2) +
      (∑ i : Fin 3, (accel c q i)^2) / c^2 =
      ∑ μ : Fin 4, ∑ i : Fin 3, (q μ i)^2 := by
  rw [spatial_orthogonal_decomposition]
  simp [Fin.sum_univ_succ, accel]
  field_simp
  ring

noncomputable def eigenRate (c : ℝ) (d : Arr) (gap : Fin 3 → ℝ) : Arr :=
  fun μ i => -c * d μ i / gap i

theorem weighted_rate (c : ℝ) (d : Arr) (gap : Fin 3 → ℝ)
    (hc : c ≠ 0) :
    (theta (eigenRate c d gap))^2 / 3 +
    (∑ i : Fin 3, ∑ j : Fin 3, (sigma (eigenRate c d gap) i j)^2) +
    2 * (∑ i : Fin 3, (omega (eigenRate c d gap) i)^2) +
    (∑ i : Fin 3, (accel c (eigenRate c d gap) i)^2) / c^2 =
    c^2 * (∑ μ : Fin 4, ∑ i : Fin 3, (d μ i)^2 / (gap i)^2) := by
  rw [rate_four_by_three c _ hc]
  simp [eigenRate, Fin.sum_univ_succ]
  ring

theorem gap_square_lower {δ g : ℝ} (hδ : 0 < δ) (hg : δ ≤ |g|) : δ^2 ≤ g^2 := by
  have h0 : 0 ≤ |g| := abs_nonneg g
  have hs : δ^2 ≤ |g|^2 := by nlinarith
  rwa [sq_abs] at hs

theorem component_gap_bound {δ g d : ℝ} (hδ : 0 < δ) (hg : δ ≤ |g|) :
    d^2 / g^2 ≤ d^2 / δ^2 := by
  have hgn : g ≠ 0 := by
    intro hz
    simp [hz] at hg
    linarith
  have hgsq : 0 < g^2 := sq_pos_of_ne_zero hgn
  have hδsq : 0 < δ^2 := sq_pos_of_pos hδ
  apply (div_le_div_iff₀ hgsq hδsq).2
  nlinarith [mul_nonneg (sq_nonneg d) (sub_nonneg.mpr (gap_square_lower hδ hg))]

theorem component_gap_eq_iff {δ g d : ℝ} (hδ : 0 < δ) (hg : δ ≤ |g|) :
    d^2 / g^2 = d^2 / δ^2 ↔ d = 0 ∨ |g| = δ := by
  have hgn : g ≠ 0 := by
    intro hz
    simp [hz] at hg
    linarith
  have hδn : δ ≠ 0 := ne_of_gt hδ
  constructor
  · intro heq
    by_cases hd : d = 0
    · exact Or.inl hd
    · right
      have hcross : d^2 * δ^2 = d^2 * g^2 :=
        (div_eq_div_iff (pow_ne_zero 2 hgn) (pow_ne_zero 2 hδn)).mp heq
      have hdiff : g^2 = δ^2 := by
        have hmul : d^2 * (δ^2 - g^2) = 0 := by nlinarith
        rcases mul_eq_zero.mp hmul with hzero | hzero
        · exact False.elim ((pow_ne_zero 2 hd) hzero)
        · linarith
      nlinarith [sq_abs g, abs_nonneg g]
  · rintro (rfl | habs)
    · simp
    · have hsq : g^2 = δ^2 := by nlinarith [sq_abs g]
      rw [hsq]

theorem signed_gap_sum_bound (d : Arr) (gap : Fin 3 → ℝ) (δ : ℝ)
    (hδ : 0 < δ) (hg : ∀ i, δ ≤ |gap i|) :
    (∑ μ : Fin 4, ∑ i : Fin 3, (d μ i)^2 / (gap i)^2) ≤
      (∑ μ : Fin 4, ∑ i : Fin 3, (d μ i)^2 / δ^2) := by
  apply Finset.sum_le_sum
  intro μ _
  apply Finset.sum_le_sum
  intro i _
  exact component_gap_bound hδ (hg i)

theorem signed_gap_sum_eq_iff (d : Arr) (gap : Fin 3 → ℝ) (δ : ℝ)
    (hδ : 0 < δ) (hg : ∀ i, δ ≤ |gap i|) :
    (∑ μ : Fin 4, ∑ i : Fin 3, (d μ i)^2 / (gap i)^2) =
      (∑ μ : Fin 4, ∑ i : Fin 3, (d μ i)^2 / δ^2) ↔
      ∀ μ : Fin 4, ∀ i : Fin 3, d μ i = 0 ∨ |gap i| = δ := by
  constructor
  · intro h μ i
    have hμ : (∑ j : Fin 3, (d μ j)^2 / (gap j)^2) =
        (∑ j : Fin 3, (d μ j)^2 / δ^2) :=
      (Finset.sum_eq_sum_iff_of_le (fun ν _ =>
        Finset.sum_le_sum (fun j _ => component_gap_bound hδ (hg j)))).mp h μ (Finset.mem_univ μ)
    have hi : (d μ i)^2 / (gap i)^2 = (d μ i)^2 / δ^2 :=
      (Finset.sum_eq_sum_iff_of_le (fun j _ => component_gap_bound hδ (hg j))).mp hμ i (Finset.mem_univ i)
    exact (component_gap_eq_iff hδ (hg i)).mp hi
  · intro h
    apply Finset.sum_congr rfl
    intro μ _
    apply Finset.sum_congr rfl
    intro i _
    exact (component_gap_eq_iff hδ (hg i)).mpr (h μ i)

end GRSTATCAS04
