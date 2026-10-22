import G17ACore
import G01AJacobiVertex

/-!
# G17-A optics: constant-scale laws for the optical tidal operator, `d_A`,
# `Kc`, `M2`, `L`, the native remainder domains and the calibration offset
# (CAS17-C02)

Reuses unchanged the reviewed frame-level G01-A module (`G01A.rescale`,
`G01A.jacobi_unique`, `G01A.rescale_area_distance`, `G01A.eta_rescale_invariant`)
and the accepted CAS-07 `JacobiPremises`, `matrixOf`, `eta`.

Sources: NATIVE_INFERENCE_THEOREMS.md:29-35,51-65,114-119;
FINITE_DISTANCE_THEOREM.md:7-18; OPTICAL_THEOREMS.md:17,48;
ADDED_BOOK_INTEGRATION.md:56,66-77.
-/

/- Same typeclass budget as the reused G01-A / CAS-07 M04 modules (operators on
`EuclideanSpace ℝ (Fin 2)`); it raises a resource limit only. -/
set_option synthInstance.maxHeartbeats 400000

noncomputable section

open Finset Set

namespace G17A

/-- Optical tidal matrix in a screen frame `E_A` (`A : Fin 2`):
`ℛ_AB = g(E_A, R(E_B, K) K)` with `R(X,Y)Z^e = R^e_{bcd} Z^b X^c Y^d`. -/
def tidalMat {n : ℕ} (G : Arr2 n) (Rm : Fin n → Fin n → Fin n → Fin n → ℝ)
    (E : Fin 2 → Pt n) (K : Pt n) : Matrix (Fin 2) (Fin 2) ℝ :=
  fun A B => ∑ a, ∑ e, G a e * E A a * (∑ b, ∑ c, ∑ d, Rm e b c d * K b * E B c * K d)

/-- Native remainder bound `E_i` of NATIVE_INFERENCE_THEOREMS.md (5). -/
def remBound (M2 H c r ηL : ℝ) : ℝ :=
  M2 * r ^ 2 / (2 * (1 - ηL) ^ 2) + |H| * r * ηL / (c * (1 - ηL))

/-- Conservative domain (5). -/
def Dom5 (Kc M2 L c H r ρ : ℝ) : Prop :=
  0 < r ∧ r ≤ L * (1 + CAS07M01.eta Kc L) ∧ |ρ| ≤ remBound M2 H c r (CAS07M01.eta Kc L)

/-- Tighter domain (6) with latent affine `s`. -/
def Dom6 (Kc M2 L c H r s ρ : ℝ) : Prop :=
  0 < s ∧ s ≤ L ∧ s * (1 - CAS07M01.eta Kc s) ≤ r ∧ r ≤ s * (1 + CAS07M01.eta Kc s) ∧
    |ρ| ≤ M2 * s ^ 2 / 2 + |H| * s * CAS07M01.eta Kc s / c

/-- Distance modulus with free offset `κ`; `ℓ` is `10 pc` in the unit of `r`. -/
def modulus (r Z ℓ κ : ℝ) : ℝ := 5 * Real.logb 10 (r * Z ^ 2 / ℓ) + κ

/-- Native redshift mean `Z0 + (r/c) H + ρ`. -/
def zMean (Z0 r c H ρ : ℝ) : ℝ := Z0 + (r / c) * H + ρ

/-! ## Tidal operator -/

theorem tidal_scale {n : ℕ} (G : Arr2 n) (Rm : Fin n → Fin n → Fin n → Fin n → ℝ)
    (E : Fin 2 → Pt n) (K : Pt n) (lam : ℝ) (hlam : lam ≠ 0) (A B : Fin 2) :
    tidalMat (lam ^ 2 • G) Rm (fun A => lam⁻¹ • E A) (lam⁻¹ • K) A B =
      (lam⁻¹) ^ 2 * tidalMat G Rm E K A B := by
  unfold tidalMat
  have inner : ∀ e, ∑ b, ∑ c, ∑ d, Rm e b c d * (lam⁻¹ • K) b * (lam⁻¹ • E B) c * (lam⁻¹ • K) d
      = (lam⁻¹) ^ 3 * ∑ b, ∑ c, ∑ d, Rm e b c d * K b * E B c * K d := by
    intro e
    rw [Finset.mul_sum]
    refine Finset.sum_congr rfl fun b _ => ?_
    rw [Finset.mul_sum]
    refine Finset.sum_congr rfl fun c _ => ?_
    rw [Finset.mul_sum]
    refine Finset.sum_congr rfl fun d _ => ?_
    simp only [Pi.smul_apply, smul_eq_mul]
    ring
  simp only [inner]
  rw [Finset.mul_sum]
  refine Finset.sum_congr rfl fun a _ => ?_
  rw [Finset.mul_sum]
  refine Finset.sum_congr rfl fun e _ => ?_
  simp only [Pi.smul_apply, smul_eq_mul]
  field_simp

theorem matrixOf_injective : Function.Injective CAS07M05.matrixOf := by
  intro S T h
  unfold CAS07M05.matrixOf at h
  have h1 := (Matrix.toEuclideanLin (𝕜 := ℝ) (n := Fin 2)).symm.injective h
  exact ContinuousLinearMap.coe_injective h1

theorem tidal_op_scale {n : ℕ} {Kc L Kc' L' : ℝ} (J : CAS07M05.JacobiPremises Kc L)
    (Jl : CAS07M05.JacobiPremises Kc' L') (lam : ℝ) (hlam : lam ≠ 0)
    (G : ℝ → Arr2 n) (Rm : ℝ → Fin n → Fin n → Fin n → Fin n → ℝ) (E : ℝ → Fin 2 → Pt n)
    (K : ℝ → Pt n)
    (hJ : ∀ s, CAS07M05.matrixOf (J.R s) = tidalMat (G s) (Rm s) (E s) (K s))
    (hJl : ∀ σ, CAS07M05.matrixOf (Jl.R σ) =
      tidalMat (lam ^ 2 • G (lam⁻¹ * σ)) (Rm (lam⁻¹ * σ)) (fun A => lam⁻¹ • E (lam⁻¹ * σ) A)
        (lam⁻¹ • K (lam⁻¹ * σ))) :
    ∀ σ, Jl.R σ = (lam⁻¹) ^ 2 • J.R (lam⁻¹ * σ) := by
  intro σ
  apply matrixOf_injective
  rw [hJl σ, G01A.matrixOf_smul, hJ (lam⁻¹ * σ)]
  ext A B
  rw [tidal_scale _ _ _ _ lam hlam A B]
  rfl

/-! ## Area distance, `Kc`, `L` -/

theorem dA_scale {Kc L : ℝ} (lam : ℝ) (hlam : 0 < lam) (J : CAS07M05.JacobiPremises Kc L)
    (Jl : CAS07M05.JacobiPremises ((lam⁻¹) ^ 2 * Kc) (L / lam⁻¹))
    (hR : ∀ σ ∈ Icc 0 (L / lam⁻¹), Jl.R σ = (lam⁻¹) ^ 2 • J.R (lam⁻¹ * σ)) :
    ∀ s ∈ Icc 0 L, Jl.D (lam * s) = lam • J.D s ∧
      Real.sqrt (Matrix.det (CAS07M05.matrixOf (Jl.D (lam * s)))) =
        lam * Real.sqrt (Matrix.det (CAS07M05.matrixOf (J.D s))) := by
  have hc : 0 < lam⁻¹ := inv_pos.mpr hlam
  have hl : lam ≠ 0 := hlam.ne'
  intro s hs
  have hσ : lam * s ∈ Icc 0 (L / lam⁻¹) := by
    rw [div_inv_eq_mul]
    exact ⟨mul_nonneg hlam.le hs.1, by nlinarith [hs.2]⟩
  have hU := G01A.jacobi_unique Jl (G01A.rescale lam⁻¹ hc J) (fun t ht => hR t ht) (lam * s) hσ
  have hss : lam⁻¹ * (lam * s) = s := by field_simp
  have hD : Jl.D (lam * s) = lam • J.D s := by
    rw [hU.1]
    show (lam⁻¹)⁻¹ • J.D (lam⁻¹ * (lam * s)) = lam • J.D s
    rw [inv_inv, hss]
  refine ⟨hD, ?_⟩
  rw [hU.1, G01A.rescale_area_distance hc J (lam * s), hss, div_inv_eq_mul, mul_comm]

theorem bound_indices (Kc L lam : ℝ) (hlam : lam ≠ 0) :
    (lam⁻¹) ^ 2 * Kc = Kc / lam ^ 2 ∧ L / lam⁻¹ = lam * L := by
  constructor
  · field_simp
  · rw [div_inv_eq_mul, mul_comm]

theorem eta_scale (Kc s lam : ℝ) (hK : 0 ≤ Kc) (hlam : 0 < lam) :
    CAS07M01.eta (Kc / lam ^ 2) (lam * s) = CAS07M01.eta Kc s := by
  have h := G01A.eta_rescale_invariant (K := Kc) (L := s) hK (inv_pos.mpr hlam)
  rwa [(bound_indices Kc s lam hlam.ne').1, (bound_indices Kc s lam hlam.ne').2] at h

/-! ## `M2`: second affine derivative of `Z = 1+z` -/

theorem M2_identity (Z : ℝ → ℝ) (lam t : ℝ) :
    deriv (deriv (fun t => Z (lam⁻¹ * t))) t = (lam⁻¹) ^ 2 * deriv (deriv Z) (lam⁻¹ * t) := by
  have hd1 : deriv (fun t => Z (lam⁻¹ * t)) = fun t => lam⁻¹ * deriv Z (lam⁻¹ * t) := by
    funext t
    rw [deriv_comp_mul_left lam⁻¹ Z t, smul_eq_mul]
  rw [hd1, deriv_const_mul_field, deriv_comp_mul_left, smul_eq_mul]
  ring

theorem M2_scale (Z : ℝ → ℝ) (lam L M2 : ℝ) (hlam : 0 < lam)
    (hM : ∀ s ∈ Icc 0 L, |deriv (deriv Z) s| ≤ M2) :
    ∀ t ∈ Icc 0 (lam * L), |deriv (deriv (fun t => Z (lam⁻¹ * t))) t| ≤ M2 / lam ^ 2 := by
  intro t ht
  have hl : lam ≠ 0 := hlam.ne'
  have hmem : lam⁻¹ * t ∈ Icc 0 L := by
    refine ⟨mul_nonneg (inv_nonneg.mpr hlam.le) ht.1, ?_⟩
    rw [inv_mul_le_iff₀ hlam]
    linarith [ht.2]
  rw [M2_identity, abs_mul, abs_of_nonneg (by positivity)]
  have := hM _ hmem
  calc (lam⁻¹) ^ 2 * |deriv (deriv Z) (lam⁻¹ * t)| ≤ (lam⁻¹) ^ 2 * M2 :=
        mul_le_mul_of_nonneg_left this (by positivity)
    _ = M2 / lam ^ 2 := by field_simp

/-! ## Native remainder domains -/

theorem remBound_scale (M2 H c r ηL lam : ℝ) (hlam : 0 < lam) :
    remBound (M2 / lam ^ 2) (H / lam) c (lam * r) ηL = remBound M2 H c r ηL := by
  unfold remBound
  rw [abs_div, abs_of_pos hlam]
  have hl : lam ≠ 0 := hlam.ne'
  congr 1
  · field_simp
  · rcases eq_or_ne (c * (1 - ηL)) 0 with h | h
    · simp [h]
    · field_simp

theorem dom5_scale (Kc M2 L c H r ρ lam : ℝ) (hK : 0 ≤ Kc) (hlam : 0 < lam) :
    Dom5 (Kc / lam ^ 2) (M2 / lam ^ 2) (lam * L) c (H / lam) (lam * r) ρ ↔
      Dom5 Kc M2 L c H r ρ := by
  unfold Dom5
  rw [eta_scale Kc L lam hK hlam, remBound_scale M2 H c r _ lam hlam]
  have e1 : 0 < lam * r ↔ 0 < r := ⟨fun h => pos_of_mul_pos_right h hlam.le,
    fun h => mul_pos hlam h⟩
  have e2 : lam * r ≤ lam * L * (1 + CAS07M01.eta Kc L) ↔ r ≤ L * (1 + CAS07M01.eta Kc L) := by
    rw [mul_assoc]
    exact mul_le_mul_iff_of_pos_left hlam
  rw [e1, e2]

theorem dom6_scale (Kc M2 L c H r s ρ lam : ℝ) (hK : 0 ≤ Kc) (hlam : 0 < lam) :
    Dom6 (Kc / lam ^ 2) (M2 / lam ^ 2) (lam * L) c (H / lam) (lam * r) (lam * s) ρ ↔
      Dom6 Kc M2 L c H r s ρ := by
  unfold Dom6
  rw [eta_scale Kc s lam hK hlam]
  have hl : lam ≠ 0 := hlam.ne'
  have e1 : 0 < lam * s ↔ 0 < s := ⟨fun h => pos_of_mul_pos_right h hlam.le,
    fun h => mul_pos hlam h⟩
  have e2 : lam * s ≤ lam * L ↔ s ≤ L := mul_le_mul_iff_of_pos_left hlam
  have e3 : lam * s * (1 - CAS07M01.eta Kc s) ≤ lam * r ↔
      s * (1 - CAS07M01.eta Kc s) ≤ r := by
    rw [mul_assoc]
    exact mul_le_mul_iff_of_pos_left hlam
  have e4 : lam * r ≤ lam * s * (1 + CAS07M01.eta Kc s) ↔
      r ≤ s * (1 + CAS07M01.eta Kc s) := by
    rw [mul_assoc]
    exact mul_le_mul_iff_of_pos_left hlam
  have e5 : M2 / lam ^ 2 * (lam * s) ^ 2 / 2 + |H / lam| * (lam * s) * CAS07M01.eta Kc s / c =
      M2 * s ^ 2 / 2 + |H| * s * CAS07M01.eta Kc s / c := by
    rw [abs_div, abs_of_pos hlam]
    field_simp
  rw [e1, e2, e3, e4, e5]

/-! ## Calibration offset -/

theorem modulus_offset_invariant (lam r Z ℓ κ : ℝ) (hlam : 0 < lam) (hr : 0 < r) (hZ : Z ≠ 0)
    (hℓ : 0 < ℓ) :
    modulus (lam * r) Z ℓ (κ - 5 * Real.logb 10 lam) = modulus r Z ℓ κ := by
  unfold modulus
  have hpos : r * Z ^ 2 / ℓ ≠ 0 := by positivity
  rw [show lam * r * Z ^ 2 / ℓ = lam * (r * Z ^ 2 / ℓ) by ring,
    Real.logb_mul hlam.ne' hpos]
  ring

theorem zMean_invariant (Z0 r c H ρ lam : ℝ) (hlam : lam ≠ 0) :
    zMean Z0 (lam * r) c (H / lam) ρ = zMean Z0 r c H ρ := by
  unfold zMean
  rcases eq_or_ne c 0 with h | h
  · simp [h]
  · field_simp

/-! ## Negative control: fixed bounds break domain invariance (SCALE-FIXEDBOUND) -/

theorem eta_zero_one : CAS07M01.eta 0 1 = 0 := by
  simp [CAS07M01.eta, CAS07M01.fd]

theorem fixed_bound_breaks_domain : Dom5 0 0 1 1 0 1 0 ∧ ¬ Dom5 0 0 1 1 0 (2 * 1) 0 := by
  unfold Dom5 remBound
  rw [eta_zero_one]
  norm_num

end G17A
