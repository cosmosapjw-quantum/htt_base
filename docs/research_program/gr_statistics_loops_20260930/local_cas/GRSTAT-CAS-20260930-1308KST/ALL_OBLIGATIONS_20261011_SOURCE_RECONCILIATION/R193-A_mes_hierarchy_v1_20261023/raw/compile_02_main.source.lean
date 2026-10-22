import Mathlib

/-!
# R193-A — MES covariant hierarchy: typed relations, raw shear / vorticity bounds,
# coefficient ledger, non-geodesic terms, adopted vs physically necessary orderings

Scope (binding): the first-order ("≃", O[2] dropped) covariant equations of
Maartens–Ellis–Stoeger 1995 (MESa, arXiv:astro-ph/9501016) at ONE event, written in an
orthonormal triad of the rest space of `u^a` (`h_ab = δ_ab`).  Rest-space tensors are typed
as `EuclideanSpace ℝ (Fin 3)^k`; the norm is the Frobenius norm, i.e. MESa's
`|Q| = (Q_{a..b} Q^{a..b})^{1/2}`.  O[2] remainders are NOT controlled.  Nothing here is a
physical admission.
-/

open scoped BigOperators Nat

namespace R193A

noncomputable section

/-! ## 0. Typed rest-space tensors -/

abbrev Idx := Fin 3
abbrev Vec := EuclideanSpace ℝ Idx
abbrev T2 := EuclideanSpace ℝ (Idx × Idx)
abbrev T3 := EuclideanSpace ℝ (Idx × Idx × Idx)
abbrev T4 := EuclideanSpace ℝ (Idx × Idx × Idx × Idx)

/-- antisymmetric part, `(asymL T)(b,a) = (T(b,a) - T(a,b))/2`. -/
def asymL : T2 →ₗ[ℝ] T2 where
  toFun T := WithLp.toLp 2 (fun p => (T (p.1, p.2) - T (p.2, p.1)) / 2)
  map_add' x y := by ext p; simp; ring
  map_smul' c x := by ext p; simp; ring

/-- symmetric trace-free part `T_{<ab>}`. -/
def stfL : T2 →ₗ[ℝ] T2 where
  toFun T := WithLp.toLp 2 (fun p => (T (p.1, p.2) + T (p.2, p.1)) / 2
      - (if p.1 = p.2 then (T (0, 0) + T (1, 1) + T (2, 2)) / 3 else 0))
  map_add' x y := by ext p; simp; split_ifs <;> ring
  map_smul' c x := by ext p; simp; split_ifs <;> ring

/-- `(contrA G)(a,b) = Σ_c G(c,c,a,b)`: for `G(d,c,a,b) = ∇̂_d ξ_{cab}` this is `∇̂^c ξ_{cab}`. -/
def contrA : T4 →ₗ[ℝ] T2 where
  toFun G := WithLp.toLp 2 (fun p => ∑ c : Idx, G (c, c, p.1, p.2))
  map_add' x y := by ext p; simp [Finset.sum_add_distrib]
  map_smul' c x := by ext p; simp [Finset.mul_sum]

/-- `(contrB G)(b,a) = Σ_c G(b,c,a,c)`: for `G(b,c,a,d) = ∇̂_b∇̂_c π_{ad}` this is `∇̂_b ∇̂^c π_{ac}`. -/
def contrB : T4 →ₗ[ℝ] T2 where
  toFun G := WithLp.toLp 2 (fun p => ∑ c : Idx, G (p.1, c, p.2, c))
  map_add' x y := by ext p; simp [Finset.sum_add_distrib]
  map_smul' c x := by ext p; simp [Finset.mul_sum]

/-- `(divL H)(a) = Σ_c H(c,c,a)`: for `H(c,a,b) = ∇̂_c π_{ab}` this is `∇̂^c π_{ca}`. -/
def divL : T3 →ₗ[ℝ] Vec where
  toFun H := WithLp.toLp 2 (fun a => ∑ c : Idx, H (c, c, a))
  map_add' x y := by ext p; simp [Finset.sum_add_distrib]
  map_smul' c x := by ext p; simp [Finset.mul_sum]

/-! ## 1. Norm lemmas for the typed operations -/

lemma le_of_sq_le_sq' {x y : ℝ} (hy : 0 ≤ y) (h : x ^ 2 ≤ y ^ 2) : x ≤ y := by
  by_contra hc
  push_neg at hc
  nlinarith [mul_pos (sub_pos.2 hc) (by linarith : (0:ℝ) < x + y)]

lemma three_sq (x : Idx → ℝ) : (∑ c, x c) ^ 2 ≤ 3 * ∑ c, x c ^ 2 := by
  simp only [Fin.sum_univ_three]
  nlinarith [sq_nonneg (x 0 - x 1), sq_nonneg (x 0 - x 2), sq_nonneg (x 1 - x 2)]

theorem norm_asymL_le (T : T2) : ‖asymL T‖ ≤ ‖T‖ := by
  apply le_of_sq_le_sq' (norm_nonneg _)
  rw [EuclideanSpace.real_norm_sq_eq, EuclideanSpace.real_norm_sq_eq]
  simp only [asymL, LinearMap.coe_mk, AddHom.coe_mk, PiLp.toLp_apply, Fintype.sum_prod_type,
    Fin.sum_univ_three]
  nlinarith [sq_nonneg (T (0,1) + T (1,0)), sq_nonneg (T (0,2) + T (2,0)),
    sq_nonneg (T (1,2) + T (2,1)), sq_nonneg (T (0,0)), sq_nonneg (T (1,1)), sq_nonneg (T (2,2))]

theorem norm_stfL_le (T : T2) : ‖stfL T‖ ≤ ‖T‖ := by
  apply le_of_sq_le_sq' (norm_nonneg _)
  rw [EuclideanSpace.real_norm_sq_eq, EuclideanSpace.real_norm_sq_eq]
  simp only [stfL, LinearMap.coe_mk, AddHom.coe_mk, PiLp.toLp_apply, Fintype.sum_prod_type,
    Fin.sum_univ_three]
  simp
  nlinarith [sq_nonneg (T (0,1) - T (1,0)), sq_nonneg (T (0,2) - T (2,0)),
    sq_nonneg (T (1,2) - T (2,1)), sq_nonneg (T (0,0) + T (1,1) + T (2,2))]

theorem norm_contrA_sq_le (G : T4) : ‖contrA G‖ ^ 2 ≤ 3 * ‖G‖ ^ 2 := by
  rw [EuclideanSpace.real_norm_sq_eq, EuclideanSpace.real_norm_sq_eq]
  simp only [contrA, LinearMap.coe_mk, AddHom.coe_mk, PiLp.toLp_apply, Fintype.sum_prod_type]
  have hswap : ∑ a : Idx, ∑ b : Idx, ∑ c : Idx, G (c, c, a, b) ^ 2
      = ∑ c : Idx, ∑ a : Idx, ∑ b : Idx, G (c, c, a, b) ^ 2 := by
    calc ∑ a : Idx, ∑ b : Idx, ∑ c : Idx, G (c, c, a, b) ^ 2
        = ∑ a : Idx, ∑ c : Idx, ∑ b : Idx, G (c, c, a, b) ^ 2 :=
          Finset.sum_congr rfl (fun a _ => Finset.sum_comm)
      _ = _ := Finset.sum_comm
  have hdiag : ∑ c : Idx, ∑ a : Idx, ∑ b : Idx, G (c, c, a, b) ^ 2
      ≤ ∑ d : Idx, ∑ c : Idx, ∑ a : Idx, ∑ b : Idx, G (d, c, a, b) ^ 2 := by
    calc ∑ c : Idx, ∑ a : Idx, ∑ b : Idx, G (c, c, a, b) ^ 2
        ≤ ∑ c : Idx, ∑ d : Idx, ∑ a : Idx, ∑ b : Idx, G (d, c, a, b) ^ 2 :=
          Finset.sum_le_sum (fun c _ =>
            Finset.single_le_sum (f := fun d => ∑ a : Idx, ∑ b : Idx, G (d, c, a, b) ^ 2)
              (fun d _ => by positivity) (Finset.mem_univ c))
      _ = _ := Finset.sum_comm
  calc ∑ a, ∑ b, (∑ c, G (c, c, a, b)) ^ 2
      ≤ ∑ a, ∑ b, 3 * ∑ c, G (c, c, a, b) ^ 2 := by
        gcongr with a _ b _; exact three_sq _
    _ = 3 * ∑ a : Idx, ∑ b : Idx, ∑ c : Idx, G (c, c, a, b) ^ 2 := by
        simp only [Finset.mul_sum]
    _ ≤ 3 * ∑ d : Idx, ∑ c : Idx, ∑ a : Idx, ∑ b : Idx, G (d, c, a, b) ^ 2 := by
        rw [hswap]; exact mul_le_mul_of_nonneg_left hdiag (by norm_num)

theorem norm_contrB_sq_le (G : T4) : ‖contrB G‖ ^ 2 ≤ 3 * ‖G‖ ^ 2 := by
  rw [EuclideanSpace.real_norm_sq_eq, EuclideanSpace.real_norm_sq_eq]
  simp only [contrB, LinearMap.coe_mk, AddHom.coe_mk, PiLp.toLp_apply, Fintype.sum_prod_type]
  calc ∑ b, ∑ a, (∑ c, G (b, c, a, c)) ^ 2
      ≤ ∑ b, ∑ a, 3 * ∑ c, G (b, c, a, c) ^ 2 := by
        gcongr with b _ a _; exact three_sq _
    _ ≤ ∑ b, ∑ a, 3 * ∑ c, ∑ d, G (b, c, a, d) ^ 2 := by
        gcongr with b _ a _ c _
        exact Finset.single_le_sum (f := fun d => G (b, c, a, d) ^ 2)
          (fun d _ => by positivity) (Finset.mem_univ c)
    _ = 3 * ∑ b, ∑ c, ∑ a, ∑ d, G (b, c, a, d) ^ 2 := by
        simp only [← Finset.mul_sum]; congr 1
        refine Finset.sum_congr rfl (fun b _ => ?_)
        rw [Finset.sum_comm]

theorem norm_divL_sq_le (H : T3) : ‖divL H‖ ^ 2 ≤ 3 * ‖H‖ ^ 2 := by
  rw [EuclideanSpace.real_norm_sq_eq, EuclideanSpace.real_norm_sq_eq]
  simp only [divL, LinearMap.coe_mk, AddHom.coe_mk, PiLp.toLp_apply, Fintype.sum_prod_type]
  have hdiag : ∑ c : Idx, ∑ a : Idx, H (c, c, a) ^ 2
      ≤ ∑ d : Idx, ∑ c : Idx, ∑ a : Idx, H (d, c, a) ^ 2 := by
    calc ∑ c : Idx, ∑ a : Idx, H (c, c, a) ^ 2
        ≤ ∑ c : Idx, ∑ d : Idx, ∑ a : Idx, H (d, c, a) ^ 2 :=
          Finset.sum_le_sum (fun c _ =>
            Finset.single_le_sum (f := fun d => ∑ a : Idx, H (d, c, a) ^ 2)
              (fun d _ => by positivity) (Finset.mem_univ c))
      _ = _ := Finset.sum_comm
  calc ∑ a, (∑ c, H (c, c, a)) ^ 2
      ≤ ∑ a, 3 * ∑ c, H (c, c, a) ^ 2 := by
        gcongr with a _; exact three_sq _
    _ = 3 * ∑ c : Idx, ∑ a : Idx, H (c, c, a) ^ 2 := by
        rw [← Finset.mul_sum, Finset.sum_comm]
    _ ≤ 3 * ∑ d : Idx, ∑ c : Idx, ∑ a : Idx, H (d, c, a) ^ 2 :=
        mul_le_mul_of_nonneg_left hdiag (by norm_num)

lemma sqrt3_nonneg : (0:ℝ) ≤ √3 := Real.sqrt_nonneg 3

lemma sqrt3_le_three : √3 ≤ (3:ℝ) := by
  rw [Real.sqrt_le_left (by norm_num)]; norm_num

lemma le_sqrt3_mul_of_sq {x y : ℝ} (hy : 0 ≤ y) (h : x ^ 2 ≤ 3 * y ^ 2) : x ≤ √3 * y := by
  apply le_of_sq_le_sq' (mul_nonneg sqrt3_nonneg hy)
  rw [mul_pow, Real.sq_sqrt (by norm_num)]; exact h

/-- Cauchy–Schwarz contraction bound (valid for every rest-space tensor). -/
theorem norm_contrA_le (G : T4) : ‖contrA G‖ ≤ √3 * ‖G‖ :=
  le_sqrt3_mul_of_sq (norm_nonneg _) (norm_contrA_sq_le G)
theorem norm_contrB_le (G : T4) : ‖contrB G‖ ≤ √3 * ‖G‖ :=
  le_sqrt3_mul_of_sq (norm_nonneg _) (norm_contrB_sq_le G)
theorem norm_divL_le (H : T3) : ‖divL H‖ ≤ √3 * ‖H‖ :=
  le_sqrt3_mul_of_sq (norm_nonneg _) (norm_divL_sq_le H)

/-! ## 2. Coefficient ledger: angular constant, moment normalisations, SAG erratum -/

/-- angular moment constant `κ_L = L!/(2L+1)‼` (MESa (5)–(7): normalisation `4π κ_L`). -/
def angK (L : ℕ) : ℚ := (L ! : ℚ) / ((2 * L + 1)‼ : ℚ)
/-- MESa (46): `|X_L| < momentCoeff L · μ ε_L` with `X_1 = q, X_2 = π, X_3 = ξ`. -/
def momentCoeff (L : ℕ) : ℚ := 4 * angK L
/-- MESa (41): `τ_{A_L} = tauCoeff L · X_{A_L}/μ`. -/
def tauCoeff (L : ℕ) : ℚ := 1 / (4 * angK L)
/-- corrected SAG 1997 eq (17) factor `(2ℓ+1)(2ℓ)!/(2^ℓ(ℓ!)²)`. -/
def sagFactor (L : ℕ) : ℚ := ((2 * L + 1 : ℕ) : ℚ) * ((2 * L)! : ℚ) / (2 ^ L * (L ! : ℚ) ^ 2)
/-- moment-hierarchy coupling of `∇̂_<a X_{L-1}>` in the `X_L` equation (coefficient 1 in the
harmonic equation, rescaled by the normalisations). -/
def gradCoupling (L : ℕ) : ℚ := angK (L + 1) / angK L
/-- moment-hierarchy coupling of `∇̂·X_{L+1}` in the `X_L` equation (harmonic coefficient
`(L+1)/(2L+3)`, rescaled). -/
def divCoupling (L : ℕ) : ℚ := ((L + 1 : ℚ) / (2 * L + 3)) * angK L / angK (L + 1)

lemma doubleFactorial_odd_pos (L : ℕ) : (0 : ℚ) < ((2 * L + 1)‼ : ℚ) := by
  exact_mod_cast Nat.doubleFactorial_pos _

lemma angK_pos (L : ℕ) : 0 < angK L := by
  unfold angK; exact div_pos (by exact_mod_cast Nat.factorial_pos L) (doubleFactorial_odd_pos L)

theorem angK_succ (L : ℕ) : angK (L + 1) = angK L * ((L + 1 : ℚ) / (2 * L + 3)) := by
  unfold angK
  have h1 : (2 * (L + 1) + 1) = (2 * L + 1) + 2 := by ring
  rw [h1, Nat.doubleFactorial_add_two, Nat.factorial_succ]
  have hd := doubleFactorial_odd_pos L
  push_cast
  field_simp
  ring

theorem gradCoupling_eq (L : ℕ) : gradCoupling L = (L + 1 : ℚ) / (2 * L + 3) := by
  unfold gradCoupling; rw [angK_succ]; field_simp [(angK_pos L).ne']

theorem divCoupling_eq_one (L : ℕ) : divCoupling L = 1 := by
  unfold divCoupling; rw [angK_succ]
  have h1 := (angK_pos L).ne'
  have h2 : (2 * (L:ℚ) + 3) ≠ 0 := by positivity
  have h3 : ((L:ℚ) + 1) ≠ 0 := by positivity
  field_simp

theorem angK_vals : angK 0 = 1 ∧ angK 1 = 1/3 ∧ angK 2 = 2/15 ∧ angK 3 = 2/35 := by
  refine ⟨?_, ?_, ?_, ?_⟩ <;> simp [angK, Nat.doubleFactorial, Nat.factorial] <;> norm_num

theorem momentCoeff_vals : momentCoeff 1 = 4/3 ∧ momentCoeff 2 = 8/15 ∧ momentCoeff 3 = 8/35 := by
  obtain ⟨-, h1, h2, h3⟩ := angK_vals
  refine ⟨?_, ?_, ?_⟩ <;> simp [momentCoeff, h1, h2, h3] <;> norm_num

theorem tauCoeff_vals : tauCoeff 1 = 3/4 ∧ tauCoeff 2 = 15/8 ∧ tauCoeff 3 = 35/8 := by
  obtain ⟨-, h1, h2, h3⟩ := angK_vals
  refine ⟨?_, ?_, ?_⟩ <;> simp [tauCoeff, h1, h2, h3] <;> norm_num

/-- MESa (40) with the normalisation (5)–(7) gives (41): `τ = tauCoeff L · X / μ`
(componentwise; `I = ∫E³F_{A_L} dE`). -/
theorem tau_from_moment (L : ℕ) (μ I X τ : ℝ) (hμ : μ ≠ 0)
    (hX : X = 4 * Real.pi * (angK L : ℝ) * I) (hτ : τ = 1 / (4 * μ) * (4 * Real.pi * I)) :
    τ = (tauCoeff L : ℝ) * X / μ := by
  have hk : (angK L : ℝ) ≠ 0 := by exact_mod_cast (angK_pos L).ne'
  rw [hτ, hX, tauCoeff]; push_cast; field_simp

/-- SAG erratum eq (17) factor equals `(2L+1)‼/L! = 1/κ_L` for every `L`. -/
theorem sagFactor_eq (L : ℕ) : sagFactor L = 1 / angK L := by
  unfold sagFactor angK
  have key : (2 * L + 1) * (2 * L)! = (2 * L + 1)‼ * (2 ^ L * L !) := by
    rw [← Nat.doubleFactorial_two_mul, ← Nat.factorial_eq_mul_doubleFactorial, Nat.factorial_succ]
  have hkey : ((2 * L + 1 : ℕ) : ℚ) * ((2 * L)! : ℚ) = ((2 * L + 1)‼ : ℚ) * (2 ^ L * (L ! : ℚ)) := by
    exact_mod_cast key
  have hf : (L ! : ℚ) ≠ 0 := by exact_mod_cast (Nat.factorial_pos L).ne'
  have hd := (doubleFactorial_odd_pos L).ne'
  rw [hkey]; field_simp

theorem sag_eq_four_tauCoeff (L : ℕ) : sagFactor L = 4 * tauCoeff L := by
  rw [sagFactor_eq, tauCoeff]; have := (angK_pos L).ne'; field_simp

theorem sagFactor_two : sagFactor 2 = 15/2 := by
  rw [sagFactor_eq, angK_vals.2.2.1]; norm_num
theorem sagFactor_three : sagFactor 3 = 35/2 := by
  rw [sagFactor_eq, angK_vals.2.2.2]; norm_num

/-- negative control: dropping the `(2ℓ+1)` prefactor does not give SAG (18). -/
theorem sag_without_prefactor_fails : ((2 * 2)! : ℚ) / (2 ^ 2 * ((2:ℕ)! : ℚ) ^ 2) ≠ 15/2 := by
  simp [Nat.factorial]; norm_num

/-- ledger for the MESa moment hierarchy (8)–(10) → (12)–(14):
`(1/3)∇̂μ` and `∇̂·q` in (12)/(13), `∇̂·π` in (13), `∇̂·ξ` in (14) all close with the printed
values; the `∇̂_<a q_b>` coupling in (14) is `2/5`, NOT the printed `2`. -/
theorem eq14_grad_coupling :
    gradCoupling 0 = 1/3 ∧ gradCoupling 1 = 2/5 ∧ (2/5 : ℚ) ≠ 2 ∧
    divCoupling 0 = 1 ∧ divCoupling 1 = 1 ∧ divCoupling 2 = 1 := by
  refine ⟨?_, ?_, by norm_num, divCoupling_eq_one 0, divCoupling_eq_one 1, divCoupling_eq_one 2⟩
  · rw [gradCoupling_eq]; norm_num
  · rw [gradCoupling_eq]; norm_num

/-- acceleration coupling in the non-geodesic (13): `-E² u̇_a ∂_E F` integrated with weight
`4π κ_1 E²` gives `4 κ_1/κ_0 · μ u̇_a = (4/3) μ u̇_a`; shear coupling in (14) is `4 κ_2 = 8/15`. -/
theorem accel_coupling : 4 * angK 1 / angK 0 = 4/3 ∧ 4 * angK 2 = 8/15 := by
  obtain ⟨h0, h1, h2, -⟩ := angK_vals
  rw [h0, h1, h2]; norm_num

/-! ## 3. Shear: MESa (14) ⇒ raw (51) -/

/-- one-event 1-jet of the radiation/kinematic fields relevant to (14).  `udot` (acceleration)
is carried but deliberately unconstrained: (14) has no O[1] acceleration term. -/
structure ShearJet where
  Th : ℝ
  mu : ℝ
  mudot0 : ℝ
  udot : Vec
  tau1 : Vec
  tau1dot : Vec
  gradtau1 : T2
  tau2 : T2
  tau2dot : T2
  tau3 : T3
  gradtau3 : T4
  q : Vec
  gradq : T2
  pi2 : T2
  pi2dot : T2
  xi : T3
  gradxi : T4
  sigma : T2

/-- typed linearised relations: (12) at O[0], (41)/(46) and their first-order derivatives,
and (14) with `∇̂_<a q_b>` coupling `kq` (printed: `2`; Boltzmann-consistent: `2/5`). -/
structure ShearRel (kq : ℝ) (s : ShearJet) : Prop where
  hTh : 0 < s.Th
  hmu : 0 < s.mu
  r12 : s.mudot0 = -(4/3) * s.Th * s.mu
  r41q : s.q = ((4/3) * s.mu) • s.tau1
  r41p : s.pi2 = ((8/15) * s.mu) • s.tau2
  r41x : s.xi = ((8/35) * s.mu) • s.tau3
  dq : s.gradq = ((4/3) * s.mu) • s.gradtau1
  dp : s.pi2dot = (8/15 : ℝ) • (s.mudot0 • s.tau2 + s.mu • s.tau2dot)
  dx : s.gradxi = ((8/35) * s.mu) • s.gradtau3
  r14 : s.pi2dot + ((4/3) * s.Th) • s.pi2 + ((8/15) * s.mu) • s.sigma
        + kq • stfL s.gradq + contrA s.gradxi = 0

/-- B1–B3 bounds entering (51). -/
structure ShearBounds (s : ShearJet) (e2 e2s e1p e3p : ℝ) : Prop where
  b2 : ‖s.tau2‖ < e2
  b2s : ‖s.tau2dot‖ < e2s * s.Th
  b1p : ‖s.gradtau1‖ < e1p * s.Th
  b3p : ‖s.gradtau3‖ < e3p * s.Th

/-- S1: no-cancellation triangle route with the valid Cauchy–Schwarz contraction factor `√3`. -/
theorem shear_raw_general (kq : ℝ) (hkq : 0 ≤ kq) (s : ShearJet) (h : ShearRel kq s)
    {e2 e2s e1p e3p : ℝ} (b : ShearBounds s e2 e2s e1p e3p) :
    ‖s.sigma‖ / s.Th < 8/3 * e2 + e2s + kq * (5/2) * e1p + √3 * (3/7) * e3p := by
  have hTh := h.hTh; have hmu := h.hmu
  have hsig : ((8/15) * s.mu) • s.sigma =
      -(s.pi2dot + ((4/3) * s.Th) • s.pi2 + kq • stfL s.gradq + contrA s.gradxi) := by
    rw [eq_neg_iff_add_eq_zero, ← h.r14]; abel
  have hn : (8/15) * s.mu * ‖s.sigma‖ ≤ ‖s.pi2dot‖ + (4/3) * s.Th * ‖s.pi2‖
      + kq * ‖stfL s.gradq‖ + ‖contrA s.gradxi‖ := by
    have e1 : ‖((8/15) * s.mu) • s.sigma‖ = (8/15) * s.mu * ‖s.sigma‖ := by
      rw [norm_smul, Real.norm_of_nonneg (by positivity)]
    rw [← e1, hsig, norm_neg]
    refine (norm_add_le _ _).trans ?_
    refine add_le_add ((norm_add_le _ _).trans (add_le_add ((norm_add_le _ _).trans
      (add_le_add le_rfl ?_)) ?_)) le_rfl
    · rw [norm_smul, Real.norm_of_nonneg (by positivity)]
    · rw [norm_smul, Real.norm_of_nonneg hkq]
  have hpd : ‖s.pi2dot‖ ≤ (8/15) * ((4/3) * s.Th * s.mu * ‖s.tau2‖ + s.mu * ‖s.tau2dot‖) := by
    rw [h.dp, norm_smul, Real.norm_of_nonneg (by norm_num)]
    gcongr
    refine (norm_add_le _ _).trans (le_of_eq ?_)
    rw [norm_smul, norm_smul, h.r12, Real.norm_eq_abs, Real.norm_of_nonneg hmu.le,
      abs_of_neg (by nlinarith)]
    ring
  have hp : ‖s.pi2‖ = (8/15) * s.mu * ‖s.tau2‖ := by
    rw [h.r41p, norm_smul, Real.norm_of_nonneg (by positivity)]
  have hq : ‖stfL s.gradq‖ ≤ (4/3) * s.mu * ‖s.gradtau1‖ := by
    refine (norm_stfL_le _).trans (le_of_eq ?_)
    rw [h.dq, norm_smul, Real.norm_of_nonneg (by positivity)]
  have hx : ‖contrA s.gradxi‖ ≤ √3 * ((8/35) * s.mu * ‖s.gradtau3‖) := by
    refine (norm_contrA_le _).trans (le_of_eq ?_)
    rw [h.dx, norm_smul, Real.norm_of_nonneg (by positivity)]
  have t1 : s.Th * s.mu * ‖s.tau2‖ < s.Th * s.mu * e2 :=
    mul_lt_mul_of_pos_left b.b2 (by positivity)
  have t2 : s.mu * ‖s.tau2dot‖ < s.mu * (e2s * s.Th) := mul_lt_mul_of_pos_left b.b2s hmu
  have t3 : kq * (s.mu * ‖s.gradtau1‖) ≤ kq * (s.mu * (e1p * s.Th)) :=
    mul_le_mul_of_nonneg_left (mul_le_mul_of_nonneg_left b.b1p.le hmu.le) hkq
  have t4 : √3 * (s.mu * ‖s.gradtau3‖) ≤ √3 * (s.mu * (e3p * s.Th)) :=
    mul_le_mul_of_nonneg_left (mul_le_mul_of_nonneg_left b.b3p.le hmu.le) sqrt3_nonneg
  have key : (8/15) * s.mu * ‖s.sigma‖ <
      (8/15) * s.mu * ((8/3 * e2 + e2s + kq * (5/2) * e1p + √3 * (3/7) * e3p) * s.Th) := by
    nlinarith
  rw [div_lt_iff₀ hTh]
  exact lt_of_mul_lt_mul_left key (by positivity)

/-- S1-source: MESa (51) with its printed coefficients `(8/3, 1, 5, 9/7)`, reproduced exactly
by the route with printed `kq = 2` and slice-wise contraction factor `3` (`√3 ≤ 3`). -/
theorem shear_raw_source_eq51 (s : ShearJet) (h : ShearRel 2 s)
    {e2 e2s e1p e3p : ℝ} (b : ShearBounds s e2 e2s e1p e3p) :
    ‖s.sigma‖ / s.Th < 8/3 * e2 + e2s + 5 * e1p + 9/7 * e3p := by
  have h1 := shear_raw_general 2 (by norm_num) s h b
  have he3 : 0 ≤ e3p := by
    have := b.b3p; have := h.hTh; by_contra hc; push_neg at hc
    nlinarith [norm_nonneg s.gradtau3]
  have : √3 * (3/7) * e3p ≤ 9/7 * e3p := by nlinarith [sqrt3_le_three]
  linarith

/-- the route constants are exactly the printed MESa (51) coefficients. -/
theorem eq51_route_constants :
    (4/3 + 4/3 : ℚ) = 8/3 ∧ (2 : ℚ) * momentCoeff 1 / momentCoeff 2 = 5 ∧
    (3 : ℚ) * momentCoeff 3 / momentCoeff 2 = 9/7 ∧ momentCoeff 3 / momentCoeff 2 = 3/7 := by
  obtain ⟨h1, h2, h3⟩ := momentCoeff_vals
  rw [h1, h2, h3]; norm_num

/-- S2: sharp route (uses `π̇ + (4/3)Θπ = (8/15)μ τ̇₂`, exact at first order). -/
theorem shear_raw_sharp (kq : ℝ) (hkq : 0 ≤ kq) (s : ShearJet) (h : ShearRel kq s)
    {e2 e2s e1p e3p : ℝ} (b : ShearBounds s e2 e2s e1p e3p) :
    ‖s.sigma‖ / s.Th < e2s + kq * (5/2) * e1p + √3 * (3/7) * e3p := by
  have hTh := h.hTh; have hmu := h.hmu
  have hcanc : s.pi2dot + ((4/3) * s.Th) • s.pi2 = ((8/15) * s.mu) • s.tau2dot := by
    rw [h.dp, h.r41p, h.r12]; module
  have hsig : ((8/15) * s.mu) • s.sigma =
      -(((8/15) * s.mu) • s.tau2dot + kq • stfL s.gradq + contrA s.gradxi) := by
    rw [← hcanc, eq_neg_iff_add_eq_zero, ← h.r14]; abel
  have hn : (8/15) * s.mu * ‖s.sigma‖ ≤ (8/15) * s.mu * ‖s.tau2dot‖
      + kq * ‖stfL s.gradq‖ + ‖contrA s.gradxi‖ := by
    have e1 : ‖((8/15) * s.mu) • s.sigma‖ = (8/15) * s.mu * ‖s.sigma‖ := by
      rw [norm_smul, Real.norm_of_nonneg (by positivity)]
    rw [← e1, hsig, norm_neg]
    refine (norm_add_le _ _).trans (add_le_add ((norm_add_le _ _).trans (add_le_add ?_ ?_)) le_rfl)
    · rw [norm_smul, Real.norm_of_nonneg (by positivity)]
    · rw [norm_smul, Real.norm_of_nonneg hkq]
  have hq : ‖stfL s.gradq‖ ≤ (4/3) * s.mu * ‖s.gradtau1‖ := by
    refine (norm_stfL_le _).trans (le_of_eq ?_)
    rw [h.dq, norm_smul, Real.norm_of_nonneg (by positivity)]
  have hx : ‖contrA s.gradxi‖ ≤ √3 * ((8/35) * s.mu * ‖s.gradtau3‖) := by
    refine (norm_contrA_le _).trans (le_of_eq ?_)
    rw [h.dx, norm_smul, Real.norm_of_nonneg (by positivity)]
  have t2 : s.mu * ‖s.tau2dot‖ < s.mu * (e2s * s.Th) := mul_lt_mul_of_pos_left b.b2s hmu
  have t3 : kq * (s.mu * ‖s.gradtau1‖) ≤ kq * (s.mu * (e1p * s.Th)) :=
    mul_le_mul_of_nonneg_left (mul_le_mul_of_nonneg_left b.b1p.le hmu.le) hkq
  have t4 : √3 * (s.mu * ‖s.gradtau3‖) ≤ √3 * (s.mu * (e3p * s.Th)) :=
    mul_le_mul_of_nonneg_left (mul_le_mul_of_nonneg_left b.b3p.le hmu.le) sqrt3_nonneg
  have key : (8/15) * s.mu * ‖s.sigma‖ <
      (8/15) * s.mu * ((e2s + kq * (5/2) * e1p + √3 * (3/7) * e3p) * s.Th) := by
    nlinarith
  rw [div_lt_iff₀ hTh]
  exact lt_of_mul_lt_mul_left key (by positivity)

/-- S3: with the Boltzmann-consistent coupling `kq = 2/5` the sharp bound is
`ε*₂ + ε'₁ + (3√3/7) ε'₃`, and it implies the printed MESa (51). -/
theorem shear_boltzmann_implies_eq51 (s : ShearJet) (h : ShearRel (2/5) s)
    {e2 e2s e1p e3p : ℝ} (b : ShearBounds s e2 e2s e1p e3p) :
    ‖s.sigma‖ / s.Th < e2s + e1p + √3 * (3/7) * e3p ∧
    ‖s.sigma‖ / s.Th < 8/3 * e2 + e2s + 5 * e1p + 9/7 * e3p := by
  have h1 := shear_raw_sharp (2/5) (by norm_num) s h b
  have hTh := h.hTh
  have he2 : 0 < e2 := lt_of_le_of_lt (norm_nonneg _) b.b2
  have he1 : 0 ≤ e1p := by
    by_contra hc; push_neg at hc; nlinarith [b.b1p, norm_nonneg s.gradtau1]
  have he3 : 0 ≤ e3p := by
    by_contra hc; push_neg at hc; nlinarith [b.b3p, norm_nonneg s.gradtau3]
  have : √3 * (3/7) * e3p ≤ 9/7 * e3p := by nlinarith [sqrt3_le_three]
  constructor
  · have : (2/5 : ℝ) * (5/2) * e1p = e1p := by ring
    linarith
  · nlinarith

/-! ## 4. Vorticity: MESa (27) + ∇̂(13) + (26) ⇒ raw (52); non-geodesic term -/

/-- one-event jet for (52).  Index order: derivative index first. -/
structure VortJet where
  Th : ℝ
  mu : ℝ
  mudot0 : ℝ
  gradtau1 : T2
  gradtau1dot : T2
  hesstau2 : T4
  gradq : T2
  gradqDot : T2
  gradqdot : T2
  hesspi : T4
  gradudot : T2
  hessmu : T2
  omega : T2

/-- typed relations: (12) at O[0]; ∇̂ and (∇̂·)˙ of (41); (26) for the O[1] vector `q`;
∇̂_b of the NON-GEODESIC (13) (`+(4/3)μ u̇_a`, see `accel_coupling`); (27) (exact). -/
structure VortRel (s : VortJet) : Prop where
  hTh : 0 < s.Th
  hmu : 0 < s.mu
  r12 : s.mudot0 = -(4/3) * s.Th * s.mu
  dq : s.gradq = ((4/3) * s.mu) • s.gradtau1
  dqdot : s.gradqDot = (4/3 : ℝ) • (s.mudot0 • s.gradtau1 + s.mu • s.gradtau1dot)
  r26 : s.gradqdot = s.gradqDot + (s.Th / 3) • s.gradq
  dpi : s.hesspi = ((8/15) * s.mu) • s.hesstau2
  r13 : s.hessmu = (-3 : ℝ) • (s.gradqdot + ((4/3) * s.Th) • s.gradq
        + ((4/3) * s.mu) • s.gradudot + contrB s.hesspi)
  r27 : asymL s.hessmu = (-s.mudot0) • s.omega

structure VortBounds (s : VortJet) (e1p e1ps e2pp α : ℝ) : Prop where
  b1p : ‖s.gradtau1‖ < e1p * s.Th
  b1ps : ‖s.gradtau1dot‖ < e1ps * s.Th ^ 2
  b2pp : ‖s.hesstau2‖ < e2pp * s.Th ^ 2
  bacc : ‖asymL s.gradudot‖ ≤ α * s.Th ^ 2

lemma omega_norm_eq (s : VortJet) (h : VortRel s) :
    (4/3) * s.Th * s.mu * ‖s.omega‖ = 3 * ‖asymL (s.gradqdot + ((4/3) * s.Th) • s.gradq)
      + ((4/3) * s.mu) • asymL s.gradudot + asymL (contrB s.hesspi)‖ := by
  have hTh := h.hTh; have hmu := h.hmu
  have e1 : ‖asymL s.hessmu‖ = (4/3) * s.Th * s.mu * ‖s.omega‖ := by
    rw [h.r27, norm_smul, h.r12, Real.norm_of_nonneg (by nlinarith)]; ring
  rw [← e1, h.r13, map_smul, norm_smul, map_add, map_add, map_smul]
  norm_num

/-- W1: source route (no cancellation) with the valid contraction factor `√3`, including the
non-geodesic acceleration-curl term `3 α`. -/
theorem vort_raw_general (s : VortJet) (h : VortRel s) {e1p e1ps e2pp α : ℝ}
    (b : VortBounds s e1p e1ps e2pp α) :
    ‖s.omega‖ / s.Th < 9 * e1p + 3 * e1ps + √3 * (6/5) * e2pp + 3 * α := by
  have hTh := h.hTh; have hmu := h.hmu
  have hE := omega_norm_eq s h
  have hsplit : ‖asymL (s.gradqdot + ((4/3) * s.Th) • s.gradq)
      + ((4/3) * s.mu) • asymL s.gradudot + asymL (contrB s.hesspi)‖ ≤
      ‖s.gradqdot‖ + (4/3) * s.Th * ‖s.gradq‖ + (4/3) * s.mu * ‖asymL s.gradudot‖
      + ‖contrB s.hesspi‖ := by
    refine (norm_add_le _ _).trans (add_le_add ((norm_add_le _ _).trans (add_le_add ?_ ?_)) ?_)
    · refine (norm_asymL_le _).trans ((norm_add_le _ _).trans (le_of_eq ?_))
      rw [norm_smul, Real.norm_of_nonneg (by positivity)]
    · rw [norm_smul, Real.norm_of_nonneg (by positivity)]
    · exact norm_asymL_le _
  have hgq : ‖s.gradq‖ = (4/3) * s.mu * ‖s.gradtau1‖ := by
    rw [h.dq, norm_smul, Real.norm_of_nonneg (by positivity)]
  have hgqD : ‖s.gradqDot‖ ≤ (4/3) * ((4/3) * s.Th * s.mu * ‖s.gradtau1‖
      + s.mu * ‖s.gradtau1dot‖) := by
    rw [h.dqdot, norm_smul, Real.norm_of_nonneg (by norm_num)]
    gcongr
    refine (norm_add_le _ _).trans (le_of_eq ?_)
    rw [norm_smul, norm_smul, h.r12, Real.norm_eq_abs, Real.norm_of_nonneg hmu.le,
      abs_of_neg (by nlinarith)]
    ring
  have hgqd : ‖s.gradqdot‖ ≤ ‖s.gradqDot‖ + s.Th / 3 * ‖s.gradq‖ := by
    rw [h.r26]; refine (norm_add_le _ _).trans (le_of_eq ?_)
    rw [norm_smul, Real.norm_of_nonneg (by positivity)]
  have hpi : ‖contrB s.hesspi‖ ≤ √3 * ((8/15) * s.mu * ‖s.hesstau2‖) := by
    refine (norm_contrB_le _).trans (le_of_eq ?_)
    rw [h.dpi, norm_smul, Real.norm_of_nonneg (by positivity)]
  have t1 : s.Th * s.mu * ‖s.gradtau1‖ < s.Th * s.mu * (e1p * s.Th) :=
    mul_lt_mul_of_pos_left b.b1p (by positivity)
  have t2 : s.mu * ‖s.gradtau1dot‖ < s.mu * (e1ps * s.Th ^ 2) :=
    mul_lt_mul_of_pos_left b.b1ps hmu
  have t3 : √3 * (s.mu * ‖s.hesstau2‖) ≤ √3 * (s.mu * (e2pp * s.Th ^ 2)) :=
    mul_le_mul_of_nonneg_left (mul_le_mul_of_nonneg_left b.b2pp.le hmu.le) sqrt3_nonneg
  have t4 : s.mu * ‖asymL s.gradudot‖ ≤ s.mu * (α * s.Th ^ 2) :=
    mul_le_mul_of_nonneg_left b.bacc hmu.le
  have key : (4/3) * s.Th * s.mu * ‖s.omega‖ <
      (4/3) * s.Th * s.mu * ((9 * e1p + 3 * e1ps + √3 * (6/5) * e2pp + 3 * α) * s.Th) := by
    nlinarith
  rw [div_lt_iff₀ hTh]
  exact lt_of_mul_lt_mul_left key (by positivity)

/-- W1-geodesic: with `u̇ = 0` the exactly source-equal ε'₁, ε'*₁ coefficients `9, 3` and the
valid `(6/5)√3` ε''₂ coefficient. -/
theorem vort_raw_geodesic (s : VortJet) (h : VortRel s) (hg : s.gradudot = 0)
    {e1p e1ps e2pp : ℝ} (b1p : ‖s.gradtau1‖ < e1p * s.Th)
    (b1ps : ‖s.gradtau1dot‖ < e1ps * s.Th ^ 2) (b2pp : ‖s.hesstau2‖ < e2pp * s.Th ^ 2) :
    ‖s.omega‖ / s.Th < 9 * e1p + 3 * e1ps + √3 * (6/5) * e2pp := by
  have := vort_raw_general s h (α := 0) ⟨b1p, b1ps, b2pp, by rw [hg, map_zero]; simp⟩
  simpa using this

/-- W2: sharp route (uses `∇̂q̇ + (4/3)Θ∇̂q = (4/3)μ((∇̂τ₁)˙ + (Θ/3)∇̂τ₁)`). -/
theorem vort_raw_sharp (s : VortJet) (h : VortRel s) {e1p e1ps e2pp α : ℝ}
    (b : VortBounds s e1p e1ps e2pp α) :
    ‖s.omega‖ / s.Th < e1p + 3 * e1ps + √3 * (6/5) * e2pp + 3 * α := by
  have hTh := h.hTh; have hmu := h.hmu
  have hE := omega_norm_eq s h
  have hcanc : s.gradqdot + ((4/3) * s.Th) • s.gradq =
      ((4/3) * s.mu) • (s.gradtau1dot + (s.Th / 3) • s.gradtau1) := by
    rw [h.r26, h.dqdot, h.dq, h.r12]; module
  have hsplit : ‖asymL (s.gradqdot + ((4/3) * s.Th) • s.gradq)
      + ((4/3) * s.mu) • asymL s.gradudot + asymL (contrB s.hesspi)‖ ≤
      (4/3) * s.mu * (‖s.gradtau1dot‖ + s.Th / 3 * ‖s.gradtau1‖)
      + (4/3) * s.mu * ‖asymL s.gradudot‖ + ‖contrB s.hesspi‖ := by
    refine (norm_add_le _ _).trans (add_le_add ((norm_add_le _ _).trans (add_le_add ?_ ?_)) ?_)
    · refine (norm_asymL_le _).trans ?_
      rw [hcanc, norm_smul, Real.norm_of_nonneg (by positivity)]
      gcongr
      refine (norm_add_le _ _).trans (le_of_eq ?_)
      rw [norm_smul, Real.norm_of_nonneg (by positivity)]
    · rw [norm_smul, Real.norm_of_nonneg (by positivity)]
    · exact norm_asymL_le _
  have hpi : ‖contrB s.hesspi‖ ≤ √3 * ((8/15) * s.mu * ‖s.hesstau2‖) := by
    refine (norm_contrB_le _).trans (le_of_eq ?_)
    rw [h.dpi, norm_smul, Real.norm_of_nonneg (by positivity)]
  have t1 : s.Th * s.mu * ‖s.gradtau1‖ < s.Th * s.mu * (e1p * s.Th) :=
    mul_lt_mul_of_pos_left b.b1p (by positivity)
  have t2 : s.mu * ‖s.gradtau1dot‖ < s.mu * (e1ps * s.Th ^ 2) :=
    mul_lt_mul_of_pos_left b.b1ps hmu
  have t3 : √3 * (s.mu * ‖s.hesstau2‖) ≤ √3 * (s.mu * (e2pp * s.Th ^ 2)) :=
    mul_le_mul_of_nonneg_left (mul_le_mul_of_nonneg_left b.b2pp.le hmu.le) sqrt3_nonneg
  have t4 : s.mu * ‖asymL s.gradudot‖ ≤ s.mu * (α * s.Th ^ 2) :=
    mul_le_mul_of_nonneg_left b.bacc hmu.le
  have key : (4/3) * s.Th * s.mu * ‖s.omega‖ <
      (4/3) * s.Th * s.mu * ((e1p + 3 * e1ps + √3 * (6/5) * e2pp + 3 * α) * s.Th) := by
    nlinarith
  rw [div_lt_iff₀ hTh]
  exact lt_of_mul_lt_mul_left key (by positivity)

/-- the explicit type-admissible witness tensor (second gradient of an STF rank-2 field in a
flat chart: symmetric in the derivative pair, symmetric trace-free in the tensor pair). -/
def gw : Idx → Idx → Idx → Idx → ℝ :=
  ![![![![0, 0, -2], ![0, 0, 0], ![-2, 0, 0]],
      ![![0, 0, 0], ![0, 0, -1], ![0, -1, 0]],
      ![![2, 0, 0], ![0, 0, 0], ![0, 0, -2]]],
    ![![![0, 0, 0], ![0, 0, -1], ![0, -1, 0]],
      ![![0, 0, 0], ![0, 0, 0], ![0, 0, 0]],
      ![![0, 1, 0], ![1, 0, 0], ![0, 0, 0]]],
    ![![![2, 0, 0], ![0, 0, 0], ![0, 0, -2]],
      ![![0, 1, 0], ![1, 0, 0], ![0, 0, 0]],
      ![![0, 0, 2], ![0, 0, 0], ![2, 0, 0]]]]

def Gw : T4 := WithLp.toLp 2 (fun p => gw p.1 p.2.1 p.2.2.1 p.2.2.2)

theorem Gw_typed :
    (∀ b c a d, gw b c a d = gw c b a d) ∧ (∀ b c a d, gw b c a d = gw b c d a) ∧
    (∀ b c, gw b c 0 0 + gw b c 1 1 + gw b c 2 2 = 0) := by
  refine ⟨?_, ?_, ?_⟩
  · intro b c a d; fin_cases b <;> fin_cases c <;> fin_cases a <;> fin_cases d <;> simp [gw]
  · intro b c a d; fin_cases b <;> fin_cases c <;> fin_cases a <;> fin_cases d <;> simp [gw]
  · intro b c; fin_cases b <;> fin_cases c <;> simp [gw] <;> norm_num

theorem Gw_norm_sq : ‖Gw‖ ^ 2 = 40 := by
  rw [EuclideanSpace.real_norm_sq_eq]
  simp [Gw, gw, Fintype.sum_prod_type, Fin.sum_univ_three]
  norm_num

theorem asym_contrB_Gw_norm_sq : ‖asymL (contrB Gw)‖ ^ 2 = 50 := by
  rw [EuclideanSpace.real_norm_sq_eq]
  simp [asymL, contrB, Gw, gw, Fintype.sum_prod_type, Fin.sum_univ_three]
  norm_num

/-- the step `‖∇̂_[b ∇̂^c π_{a]c}‖ ≤ ‖∇̂∇̂π‖` needed for the printed `6/5` fails on type-admissible
tensors. -/
theorem contraction_factor_one_fails : ‖Gw‖ < ‖asymL (contrB Gw)‖ := by
  apply lt_of_pow_lt_pow_left₀ 2 (norm_nonneg _)
  rw [Gw_norm_sq, asym_contrB_Gw_norm_sq]; norm_num

/-- W3: a geodesic jet satisfying every relation used for (52) whose vorticity violates the
printed (52) bound `9ε'₁ + 3ε'*₁ + (6/5)ε''₂`.  (Relative to the formalised relation set
`VortRel`; not a solution of the full Einstein–Boltzmann system.) -/
theorem eq52_eps2_branch_not_implied :
    ∃ s : VortJet, VortRel s ∧ s.gradudot = 0 ∧
      ‖s.gradtau1‖ < (1/100) * s.Th ∧ ‖s.gradtau1dot‖ < (1/100) * s.Th ^ 2 ∧
      ‖s.hesstau2‖ < (13/2) * s.Th ^ 2 ∧
      9 * (1/100) + 3 * (1/100) + 6/5 * (13/2) < ‖s.omega‖ / s.Th := by
  let hm : T2 := (-3 : ℝ) • ((0 : T2) + ((4/3) * (1:ℝ)) • (0 : T2) + ((4/3) * (1:ℝ)) • (0 : T2)
    + contrB (((8/15) * (1:ℝ)) • Gw))
  refine ⟨⟨1, 1, -(4/3), 0, 0, Gw, 0, 0, 0, ((8/15) * (1:ℝ)) • Gw, 0, hm, (3/4 : ℝ) • asymL hm⟩,
    ⟨by norm_num, by norm_num, by norm_num, by simp, by simp, by simp, rfl, rfl, ?_⟩,
    rfl, by simp, by simp, ?_, ?_⟩
  · simp only [smul_smul]; norm_num
  · have h40 := Gw_norm_sq
    have : ‖Gw‖ < 13/2 := by
      apply lt_of_pow_lt_pow_left₀ 2 (by norm_num); rw [h40]; norm_num
    simpa using this
  · have hom : (3/4 : ℝ) • asymL hm = (-(6/5) : ℝ) • asymL (contrB Gw) := by
      simp only [hm, map_smul, map_add, map_zero, smul_zero, zero_add, smul_smul]; norm_num
    have hn : ‖(3/4 : ℝ) • asymL hm‖ ^ 2 = 72 := by
      rw [hom, norm_smul, mul_pow, asym_contrB_Gw_norm_sq]; norm_num
    show _ < ‖(3/4 : ℝ) • asymL hm‖ / 1
    rw [div_one]
    apply lt_of_pow_lt_pow_left₀ 2 (norm_nonneg _)
    rw [hn]; norm_num

/-! ## 5. Acceleration: non-geodesic (13) -/

structure MomJet where
  Th : ℝ
  mu : ℝ
  mudot0 : ℝ
  tau1 : Vec
  tau1dot : Vec
  gradtau2 : T3
  q : Vec
  qdot : Vec
  gradpi : T3
  gradmu : Vec
  udot : Vec

/-- non-geodesic radiation momentum conservation (13') with acceleration coupling `(4/3)μ`. -/
structure MomRel (s : MomJet) : Prop where
  hTh : 0 < s.Th
  hmu : 0 < s.mu
  r12 : s.mudot0 = -(4/3) * s.Th * s.mu
  r41q : s.q = ((4/3) * s.mu) • s.tau1
  dq : s.qdot = (4/3 : ℝ) • (s.mudot0 • s.tau1 + s.mu • s.tau1dot)
  dpi : s.gradpi = ((8/15) * s.mu) • s.gradtau2
  r13 : s.qdot + ((4/3) * s.Th) • s.q + (1/3 : ℝ) • s.gradmu + ((4/3) * s.mu) • s.udot
        + divL s.gradpi = 0

/-- A1: only the combination `∇̂μ + 4μ u̇` is bounded by the multipole jets. -/
theorem accel_combination_bound (s : MomJet) (h : MomRel s) {e1s e2p : ℝ}
    (b1 : ‖s.tau1dot‖ < e1s * s.Th) (b2 : ‖s.gradtau2‖ < e2p * s.Th) :
    ‖s.gradmu + (4 * s.mu) • s.udot‖ < s.mu * s.Th * (4 * e1s + √3 * (8/5) * e2p) := by
  have hTh := h.hTh; have hmu := h.hmu
  have hcomb : s.gradmu + (4 * s.mu) • s.udot =
      (-3 : ℝ) • (((4/3) * s.mu) • s.tau1dot + divL s.gradpi) := by
    have h13 := h.r13
    rw [h.dq, h.r41q, h.r12] at h13
    have : s.gradmu + (4 * s.mu) • s.udot = (3:ℝ) • ((1/3 : ℝ) • s.gradmu
        + ((4/3) * s.mu) • s.udot) := by module
    rw [this]
    have h2 : (1/3 : ℝ) • s.gradmu + ((4/3) * s.mu) • s.udot =
        -(((4/3) * s.mu) • s.tau1dot + divL s.gradpi) := by
      rw [eq_neg_iff_add_eq_zero, ← h13]; module
    rw [h2]; module
  have hd : ‖divL s.gradpi‖ ≤ √3 * ((8/15) * s.mu * ‖s.gradtau2‖) := by
    refine (norm_divL_le _).trans (le_of_eq ?_)
    rw [h.dpi, norm_smul, Real.norm_of_nonneg (by positivity)]
  have hn : ‖s.gradmu + (4 * s.mu) • s.udot‖ ≤
      3 * ((4/3) * s.mu * ‖s.tau1dot‖ + √3 * ((8/15) * s.mu * ‖s.gradtau2‖)) := by
    rw [hcomb, norm_smul, Real.norm_eq_abs, abs_of_neg (by norm_num : (-3:ℝ) < 0), neg_neg]
    apply mul_le_mul_of_nonneg_left _ (by norm_num)
    refine (norm_add_le _ _).trans (add_le_add (le_of_eq ?_) hd)
    rw [norm_smul, Real.norm_of_nonneg (by positivity)]
  have t1 : s.mu * ‖s.tau1dot‖ < s.mu * (e1s * s.Th) := mul_lt_mul_of_pos_left b1 hmu
  have t2 : √3 * (s.mu * ‖s.gradtau2‖) ≤ √3 * (s.mu * (e2p * s.Th)) :=
    mul_le_mul_of_nonneg_left (mul_le_mul_of_nonneg_left b2.le hmu.le) sqrt3_nonneg
  nlinarith

/-- A2: no acceleration ceiling follows from the radiation hierarchy and multipole bounds:
with all multipole jets zero, `‖u̇‖` is unbounded. -/
theorem no_accel_ceiling (M : ℝ) :
    ∃ s : MomJet, MomRel s ∧ s.tau1 = 0 ∧ s.tau1dot = 0 ∧ s.gradtau2 = 0 ∧ M < ‖s.udot‖ := by
  let u : Vec := (|M| + 1) • EuclideanSpace.single 0 (1:ℝ)
  refine ⟨⟨1, 1, -(4/3), 0, 0, 0, 0, 0, 0, (-4 : ℝ) • u, u⟩,
    ⟨by norm_num, by norm_num, by norm_num, by simp, by simp, by simp, ?_⟩, rfl, rfl, rfl, ?_⟩
  · simp only [smul_zero, add_zero, zero_add, map_zero, smul_smul]; norm_num
  · show M < ‖u‖
    rw [norm_smul, EuclideanSpace.norm_single, norm_one, mul_one, Real.norm_eq_abs,
      abs_of_pos (by positivity)]
    linarith [le_abs_self M]

/-! ## 6. Physical necessity (derived) vs adopted hierarchy assumptions (typed separately) -/

/-- PHYSICAL NECESSITY: non-interacting dust (MESa (11)) has `ρ u̇_a = 0`, hence geodesic flow. -/
theorem dust_forces_geodesic (rho : ℝ) (udot : Vec) (hρ : 0 < rho) (hmom : rho • udot = 0) :
    udot = 0 := by
  rcases smul_eq_zero.mp hmom with h | h
  · exact absurd h hρ.ne'
  · exact h

/-- PHYSICAL NECESSITY: from (36) `Ṫ = -(Θ/3)T` the characteristic time obeys `Θ t_R = 3`
(the "3" of C2 is derived; the estimate `ε* ≃ ε/(Θ t_R)` itself is adopted). -/
theorem theta_tR_eq_three (Th T Tdot : ℝ) (hT : 0 < T) (hTh : 0 < Th)
    (h36 : Tdot = -(Th / 3) * T) : Th * (T / |Tdot|) = 3 := by
  have : |Tdot| = Th / 3 * T := by
    rw [h36, abs_of_neg (by nlinarith)]; ring
  rw [this]; field_simp

/-- PHYSICAL NECESSITY: `μ̇⁽⁰⁾ < 0`, so (27) can be solved for `ω`. -/
theorem mudot0_neg (Th mu mudot0 : ℝ) (hTh : 0 < Th) (hmu : 0 < mu)
    (h : mudot0 = -(4/3) * Th * mu) : mudot0 < 0 := by
  rw [h]; nlinarith [mul_pos hTh hmu]

/-- ADOPTED (not physical): C1 for the dipole jet, spatial gradient ≤ time derivative. -/
def AdoptedC1Jet (s : ShearJet) : Prop := ‖s.gradtau1‖ ≤ ‖s.tau1dot‖
/-- ADOPTED (not physical): C2 estimate for the quadrupole jet, `‖τ̇₂‖ = ‖τ₂‖ Θ/3`. -/
def AdoptedC2Jet (s : ShearJet) : Prop := ‖s.tau2dot‖ = ‖s.tau2‖ * s.Th / 3
/-- ADOPTED (not physical): SAG convention ε₁ = 0. -/
def AdoptedEps1Zero (e1 : ℝ) : Prop := e1 = 0

def rawSigma (e2 e2s e1p e3p : ℝ) : ℝ := 8/3 * e2 + e2s + 5 * e1p + 9/7 * e3p
def rawOmega (e1p e1ps e2pp : ℝ) : ℝ := 9 * e1p + 3 * e1ps + 6/5 * e2pp
def Bsigma (e1 e2 e3 : ℝ) : ℝ := 5/3 * e1 + 3 * e2 + 3/7 * e3
def Bomega (e1 e2 : ℝ) : ℝ := 10/3 * e1 + 2/15 * e2
/-- ADOPTED (not physical): the registry's strict geodesic ordering `B_σ > B_ω > 0`. -/
def AdoptedStrictHierarchy (e1 e2 e3 : ℝ) : Prop := Bomega e1 e2 < Bsigma e1 e2 e3 ∧ 0 < Bomega e1 e2

/-- C1/C2 reduction (51) → (59). -/
theorem reduce_sigma {e1 e2 e3 e1p e1s e2s e3p e3s : ℝ} (c1a : e1p ≤ e1s) (c1b : e3p ≤ e3s)
    (c2a : e1s = e1 / 3) (c2b : e2s = e2 / 3) (c2c : e3s = e3 / 3) :
    rawSigma e2 e2s e1p e3p ≤ Bsigma e1 e2 e3 := by
  unfold rawSigma Bsigma; subst c2a c2b c2c; linarith
theorem reduce_sigma_tight (e1 e2 e3 : ℝ) : rawSigma e2 (e2/3) (e1/3) (e3/3) = Bsigma e1 e2 e3 := by
  unfold rawSigma Bsigma; ring
/-- C1/C2 reduction (52) → (60). -/
theorem reduce_omega {e1 e2 e1p e1s e1ps e1ss e2pp e2ss : ℝ} (c1a : e1p ≤ e1s)
    (c1b : e1ps ≤ e1ss) (c1c : e2pp ≤ e2ss)
    (c2a : e1s = e1 / 3) (c2b : e1ss = e1 / 9) (c2c : e2ss = e2 / 9) :
    rawOmega e1p e1ps e2pp ≤ Bomega e1 e2 := by
  unfold rawOmega Bomega; subst c2a c2b c2c; linarith
theorem reduce_omega_tight (e1 e2 : ℝ) : rawOmega (e1/3) (e1/9) (e2/9) = Bomega e1 e2 := by
  unfold rawOmega Bomega; ring

/-- transcription adjudication for (51)/(52) via the triple-sourced reduced coefficients. -/
theorem transcription_adjudication :
    (∀ c : ℝ, c + 1/3 = 3 ↔ c = 8/3) ∧ (3/8 + 1/3 : ℝ) ≠ 3 ∧
    (∀ c : ℝ, c * (1/3) = 3/7 ↔ c = 9/7) ∧ (7/9 * (1/3) : ℝ) ≠ 3/7 ∧
    (∀ c : ℝ, c * (1/9) = 2/15 ↔ c = 6/5) ∧ (5/6 * (1/9) : ℝ) ≠ 2/15 := by
  refine ⟨fun c => ⟨fun h => by linarith, fun h => by rw [h]; norm_num⟩, by norm_num,
    fun c => ⟨fun h => by linarith, fun h => by rw [h]; norm_num⟩, by norm_num,
    fun c => ⟨fun h => by linarith, fun h => by rw [h]; norm_num⟩, by norm_num⟩

/-- the registry ordering `B_ω < B_σ` holds iff `ε₁ < (43/25)ε₂ + (9/35)ε₃`. -/
theorem hierarchy_strict_iff (e1 e2 e3 : ℝ) :
    Bomega e1 e2 < Bsigma e1 e2 e3 ↔ e1 < 43/25 * e2 + 9/35 * e3 := by
  unfold Bomega Bsigma; constructor <;> intro h <;> linarith

theorem Bomega_pos_iff {e1 e2 : ℝ} (h1 : 0 ≤ e1) (h2 : 0 ≤ e2) :
    0 < Bomega e1 e2 ↔ 0 < e1 ∨ 0 < e2 := by
  unfold Bomega; constructor
  · intro h; by_contra hc; push_neg at hc; linarith [hc.1, hc.2]
  · rintro (h | h) <;> linarith

/-- the adopted ordering is NOT forced by the hierarchy relations: a state satisfying `ShearRel 2`
whose minimal bound constants `(1, 1/100, 1/100)` violate it. -/
theorem strict_hierarchy_not_forced :
    ∃ s : ShearJet, ShearRel 2 s ∧ ‖s.tau1‖ < 1 ∧ ‖s.tau2‖ < 1/100 ∧ ‖s.tau3‖ < 1/100 ∧
      ¬ AdoptedStrictHierarchy 1 (1/100) (1/100) := by
  let t1 : Vec := (1/2 : ℝ) • EuclideanSpace.single 0 (1:ℝ)
  refine ⟨⟨1, 1, -(4/3), 0, t1, 0, 0, 0, 0, 0, 0, ((4/3) * (1:ℝ)) • t1, 0, 0, 0, 0, 0, 0⟩,
    ⟨by norm_num, by norm_num, by norm_num, rfl, by simp, by simp, by simp, by simp, by simp, ?_⟩,
    ?_, by simp, by simp, ?_⟩
  · simp
  · show ‖t1‖ < 1
    rw [norm_smul, EuclideanSpace.norm_single, norm_one]; norm_num
  · unfold AdoptedStrictHierarchy Bomega Bsigma; norm_num

/-- ε₁ = 0 is not forced: a hierarchy state with nonzero dipole. -/
theorem eps1_zero_not_forced : ∃ s : ShearJet, ShearRel 2 s ∧ ShearRel (2/5) s ∧ s.tau1 ≠ 0 := by
  let t1 : Vec := EuclideanSpace.single 0 (1:ℝ)
  refine ⟨⟨1, 1, -(4/3), 0, t1, 0, 0, 0, 0, 0, 0, ((4/3) * (1:ℝ)) • t1, 0, 0, 0, 0, 0, 0⟩,
    ⟨by norm_num, by norm_num, by norm_num, rfl, by simp, by simp, by simp, by simp, by simp, by simp⟩,
    ⟨by norm_num, by norm_num, by norm_num, rfl, by simp, by simp, by simp, by simp, by simp, by simp⟩,
    ?_⟩
  show t1 ≠ 0
  intro h
  have := congrArg (fun v : Vec => ‖v‖) h
  simp [t1, EuclideanSpace.norm_single] at this

/-- the admissible ε₁ interval is nondegenerate whenever ε₂ > 0 (so ε₁ = 0 is a choice). -/
theorem eps1_interval_nondegenerate {e2 e3 : ℝ} (h2 : 0 < e2) (h3 : 0 ≤ e3) :
    0 < 43/25 * e2 + 9/35 * e3 ∧ ∀ e1, 0 ≤ e1 → e1 < 43/25 * e2 + 9/35 * e3 →
      AdoptedStrictHierarchy e1 e2 e3 := by
  refine ⟨by positivity, fun e1 h1 hc => ⟨(hierarchy_strict_iff e1 e2 e3).2 hc, ?_⟩⟩
  exact (Bomega_pos_iff h1 h2.le).2 (Or.inr h2)

/-- C1 is not forced: a state satisfying `ShearRel 2` with `‖∇̂τ₁‖ > ‖τ̇₁‖`. -/
theorem C1_not_forced : ∃ s : ShearJet, ShearRel 2 s ∧ ¬ AdoptedC1Jet s := by
  let g : T2 := EuclideanSpace.single (0, 1) (1:ℝ) - EuclideanSpace.single (1, 0) (1:ℝ)
  have hstf : stfL g = 0 := by
    ext p; rcases p with ⟨a, b⟩
    fin_cases a <;> fin_cases b <;> simp [g, stfL]
  refine ⟨⟨1, 1, -(4/3), 0, 0, 0, g, 0, 0, 0, 0, 0, ((4/3) * (1:ℝ)) • g, 0, 0, 0, 0, 0⟩,
    ⟨by norm_num, by norm_num, by norm_num, by simp, by simp, by simp, rfl, by simp, by simp, ?_⟩, ?_⟩
  · simp [map_smul, hstf]
  · unfold AdoptedC1Jet
    show ¬ ‖g‖ ≤ ‖(0 : Vec)‖
    rw [norm_zero, not_le, norm_pos_iff]
    intro hg
    have := congrArg (fun T : T2 => T (0, 1)) hg
    simp [g] at this

/-- C2 is not forced: a state satisfying `ShearRel 2` with `τ₂ ≠ 0`, `τ̇₂ = 0`. -/
theorem C2_not_forced : ∃ s : ShearJet, ShearRel 2 s ∧ ¬ AdoptedC2Jet s := by
  let t2 : T2 := EuclideanSpace.single (0, 1) (1:ℝ)
  refine ⟨⟨1, 1, -(4/3), 0, 0, 0, 0, t2, 0, 0, 0, 0, 0, ((8/15) * (1:ℝ)) • t2,
      (8/15 : ℝ) • ((-(4/3) : ℝ) • t2 + (1:ℝ) • (0 : T2)), 0, 0, 0⟩,
    ⟨by norm_num, by norm_num, by norm_num, by simp, rfl, by simp, by simp, rfl, by simp, ?_⟩, ?_⟩
  · simp only [smul_zero, add_zero, map_zero, smul_smul]; module
  · unfold AdoptedC2Jet
    show ¬ ‖(0 : T2)‖ = ‖t2‖ * 1 / 3
    rw [norm_zero, EuclideanSpace.norm_single, norm_one]; norm_num

/-! ## 7. Ceiling map (PR-186 convention `W² = ω_abω^ab/(6H²)`, `Θ = 3H`) -/

theorem ceiling_map (x Th H B : ℝ) (hx : 0 ≤ x) (hH : 0 < H) (hTh : Th = 3 * H)
    (hb : x / Th < B) : x ^ 2 / (6 * H ^ 2) < 3/2 * B ^ 2 := by
  subst hTh
  have h3 : x < B * (3 * H) := by rwa [div_lt_iff₀ (by positivity)] at hb
  have hB : 0 ≤ B * (3 * H) := le_trans hx h3.le
  have hsq : x ^ 2 < (B * (3 * H)) ^ 2 := by nlinarith
  rw [div_lt_iff₀ (by positivity)]; nlinarith

/-- the ε₂ coefficient of the geodesic ω ceiling under the valid contraction factor: the W²
ceiling at ε₁ = 0 scales by exactly 3 relative to the printed `2/15`. -/
theorem cs_ceiling_factor (e2 : ℝ) :
    3/2 * (√3 * (2/15) * e2) ^ 2 = 3 * (3/2 * (2/15 * e2) ^ 2) := by
  rw [mul_pow, mul_pow, Real.sq_sqrt (by norm_num)]; ring

end

end R193A
