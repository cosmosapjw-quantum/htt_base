import Mathlib

namespace GRSTATCAS04

open Finset

abbrev Arr := Fin 4 → Fin 3 → ℝ
abbrev Vec4 := Fin 4 → ℝ
abbrev Mat4 := Fin 4 → Fin 4 → ℝ

def eta (i : Fin 4) : ℝ := if i = 0 then -1 else 1

def lorentzDot (v w : Vec4) : ℝ :=
  ∑ i : Fin 4, eta i * v i * w i

def matVec (t : Mat4) (v : Vec4) : Vec4 :=
  fun a => ∑ b : Fin 4, t a b * v b

def restProj (u v : Vec4) : Vec4 :=
  fun a => v a + lorentzDot u v * u a

theorem lorentzDot_add_right (u v w : Vec4) :
    lorentzDot u (v + w) = lorentzDot u v + lorentzDot u w := by
  simp [lorentzDot, Pi.add_apply, mul_add, Finset.sum_add_distrib]

theorem lorentzDot_smul_right (u v : Vec4) (r : ℝ) :
    lorentzDot u (r • v) = r * lorentzDot u v := by
  simp [lorentzDot, Pi.smul_apply, smul_eq_mul, Finset.mul_sum, mul_comm, mul_left_comm, mul_assoc]

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
    have hraw : HasDerivAt (fun s => lorentzDot (u s) (u s))
        (∑ i : Fin 4, eta i * (du i * u t₀ i + u t₀ i * du i)) t₀ := by
      simpa [lorentzDot, mul_assoc] using
        (HasDerivAt.fun_sum (u := Finset.univ) (fun i _ =>
          (((hu i).mul (hu i)).const_mul (eta i))))
    have hcoef : (∑ i : Fin 4, eta i * (du i * u t₀ i + u t₀ i * du i)) =
        2 * lorentzDot (u t₀) du := by
      simp [lorentzDot, Fin.sum_univ_succ, eta]
      ring
    exact hraw.congr_deriv hcoef
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

def accJet (u : Vec4) (du : Fin 4 → Vec4) : Vec4 :=
  fun b => ∑ a : Fin 4, u a * du a b

def raiseGrad (dp : Vec4) : Vec4 := fun b => eta b * dp b

def fluidDiv (e p : ℝ) (u de dp : Vec4) (du : Fin 4 → Vec4) : Vec4 :=
  fun b => ((∑ a : Fin 4, (de a + dp a) * u a) +
    (e + p) * (∑ a : Fin 4, du a a)) * u b +
    (e + p) * accJet u du b + raiseGrad dp b

theorem accJet_tangent (u : Vec4) (du : Fin 4 → Vec4)
    (hdu : ∀ a, lorentzDot u (du a) = 0) :
    lorentzDot u (accJet u du) = 0 := by
  have hs : lorentzDot u (accJet u du) =
      ∑ a : Fin 4, u a * lorentzDot u (du a) := by
    simp [lorentzDot, accJet, Fin.sum_univ_succ, eta]
    ring
  rw [hs]
  simp [hdu]

theorem euler_from_conservation
    (e p c : ℝ) (u de dp : Vec4) (du : Fin 4 → Vec4)
    (hc : 0 < c) (hgap : e + p ≠ 0)
    (hn : lorentzDot u u = -1)
    (hdu : ∀ a, lorentzDot u (du a) = 0)
    (hcons : fluidDiv e p u de dp du = 0) :
    c^2 • accJet u du = (-c^2 / (e + p)) • restProj u (raiseGrad dp) := by
  have ha := accJet_tangent u du hdu
  have hu := restProj_self u hn
  have hacc := restProj_tangent u (accJet u du) ha
  have hp := congrArg (restProj u) hcons
  have hdiv : fluidDiv e p u de dp du =
      (((∑ a : Fin 4, (de a + dp a) * u a) +
        (e + p) * (∑ a : Fin 4, du a a)) • u) +
        ((e + p) • accJet u du) + raiseGrad dp := by
    funext b
    simp [fluidDiv, Pi.add_apply, Pi.smul_apply, smul_eq_mul]
  rw [hdiv, restProj_add, restProj_add, restProj_smul, restProj_smul,
      hu, hacc] at hp
  simp only [smul_zero, zero_add] at hp
  have hz : restProj u 0 = 0 := by
    funext b
    simp [restProj, lorentzDot]
  rw [hz] at hp
  have hp0 : (e + p) • accJet u du + restProj u (raiseGrad dp) = 0 := by
    exact hp
  funext b
  have hb := congrFun hp0 b
  simp only [Pi.add_apply, Pi.zero_apply, Pi.smul_apply, smul_eq_mul] at hb ⊢
  have hsolve : accJet u du b = -restProj u (raiseGrad dp) b / (e + p) := by
    apply (eq_div_iff hgap).2
    linear_combination hb
  rw [hsolve]
  ring

theorem barotropic_euler
    (e p c cs2 : ℝ) (u de dp : Vec4) (du : Fin 4 → Vec4)
    (hc : 0 < c) (hgap : e + p ≠ 0)
    (hn : lorentzDot u u = -1)
    (hdu : ∀ a, lorentzDot u (du a) = 0)
    (hcons : fluidDiv e p u de dp du = 0)
    (heos : ∀ b, dp b = (cs2 / c^2) * de b) :
    c^2 • accJet u du = (-cs2 / (e + p)) • restProj u (raiseGrad de) := by
  rw [euler_from_conservation e p c u de dp du hc hgap hn hdu hcons]
  have hdpeq : raiseGrad dp = (cs2 / c^2) • raiseGrad de := by
    funext b
    simp [raiseGrad, heos b, Pi.smul_apply, smul_eq_mul]
    ring
  rw [hdpeq, restProj_smul]
  funext b
  simp only [Pi.smul_apply, smul_eq_mul]
  have hcn : c^2 ≠ 0 := pow_ne_zero 2 (ne_of_gt hc)
  field_simp <;> ring

theorem positive_dust_acceleration_zero
    (e c : ℝ) (u de : Vec4) (du : Fin 4 → Vec4)
    (he : 0 < e) (hc : 0 < c)
    (hn : lorentzDot u u = -1)
    (hdu : ∀ a, lorentzDot u (du a) = 0)
    (hcons : fluidDiv e 0 u de 0 du = 0) :
    c^2 • accJet u du = 0 := by
  have hgap : e + (0 : ℝ) ≠ 0 := by linarith
  have hA := euler_from_conservation e 0 c u de 0 du hc hgap hn hdu hcons
  have hz : restProj u (raiseGrad 0) = 0 := by
    funext b
    simp [restProj, raiseGrad, lorentzDot]
  rw [hA, hz]
  exact smul_zero _

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
