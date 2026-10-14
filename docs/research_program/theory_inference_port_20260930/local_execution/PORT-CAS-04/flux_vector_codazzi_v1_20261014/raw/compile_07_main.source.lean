import Mathlib
import PortCas01
import VelocityJetRest
import VelocityJetDecomposition
import FluxScalarInverse

/-!
# P04-A: single-fluid momentum flux, its inverse, and the contracted Codazzi constraint

Source contract: `CAS_CONTRACT.json` obligation CAS-04,
`J=w gamma^2 beta; beta=2r/(1+sqrt(1+4r^2)); D_bK^b_a-D_aK=kappa J_a`,
assumptions `single fluid w>0; K=-hh nabla n; inverse length; no multi-fluid converse`,
signature `-+++`, `u=U/c`.
Theory source: `inherited/tilt_boost_loop_20260930/geometry_findings.md` lines 7-92.
Implementation reference: `htt/src/common/relativistic_kinematics.py:177-206, 262-289`.

Conventions (verbatim from the source):
* `T_ab = (ε+p) u_a u_b + p g_ab`, `w = ε + p`;
* `u = γ (n + β)`, `n·β = 0`;
* `h_a^b = δ_a^b + n_a n^b`, `J_a = -h_a^b T_bc n^c`, `E_N = T_ab n^a n^b`;
* `K_ab = -h_a^c h_b^d ∇_c n_d`, `D_b K^b_a - D_a K = κ J_a`.
Index conventions of P03-A (`VelocityJetDecomposition`) are reused unchanged:
`Γ x c a b = Γ^c_{ab}`, `velJet Γ g u x a b = ∇_a u_b` (derivative index first).
Curvature convention (not fixed by the source, fixed here; the source equation
`G_0i = -D_j K^j_i + D_i K` is then *derived*, target E3):
`R^a_{bcd} = ∂_c Γ^a_{db} - ∂_d Γ^a_{cb} + Γ^a_{ce} Γ^e_{db} - Γ^a_{de} Γ^e_{cb}`,
`R_bd = R^a_{bad}`, `G_ab = R_ab - R g_ab / 2`.
-/

open Matrix Filter
open scoped Topology Matrix

namespace PORTCAS04FluxVectorCodazzi

open PORTCAS03VelocityJetDecomposition PORTCAS04FluxScalarInverse

abbrev M := Matrix (Fin 4) (Fin 4) ℝ
abbrev V := Fin 4 → ℝ

/-! ## Pointwise definitions -/

/-- `T_ab = w u_a u_b + p g_ab` with `w = ε + p`. -/
def perfectFluid (g : M) (w p : ℝ) (u : V) : M :=
  w • vecMulVec (g *ᵥ u) (g *ᵥ u) + p • g

/-- `J_a = -h_a^b T_bc n^c`. -/
def normalFlux (g : M) (n : V) (T : M) : V := -((projDown g n * T) *ᵥ n)

/-- `E_N = T_ab n^a n^b`. -/
def normalEnergy (n : V) (T : M) : ℝ := n ⬝ᵥ (T *ᵥ n)

/-- `S_ab = h_a^c h_b^d T_cd`. -/
def normalStress (g : M) (n : V) (T : M) : M := projDown g n * T * (projDown g n)ᵀ

/-- `j = sqrt (J_a J^a)`. -/
noncomputable def fluxNorm (ginv : M) (J : V) : ℝ := Real.sqrt (J ⬝ᵥ (ginv *ᵥ J))

open Classical in
/-- Vector inverse: zero branch and nonzero-direction branch. -/
noncomputable def betaVector (ginv : M) (w : ℝ) (J : V) : V :=
  if J = 0 then 0 else (betaOfRatio (fluxNorm ginv J / w) / fluxNorm ginv J) • J

/-! ## Generic algebra -/

theorem vmv_mulVec (a b v : V) : vecMulVec a b *ᵥ v = (b ⬝ᵥ v) • a := by
  ext i
  simp only [mulVec, dotProduct, vecMulVec_apply, Pi.smul_apply, smul_eq_mul, Finset.sum_mul]
  apply Finset.sum_congr rfl
  intro j _
  ring

theorem perfectFluid_mulVec (g : M) (w p : ℝ) (u v : V) :
    perfectFluid g w p u *ᵥ v = (w * ((g *ᵥ u) ⬝ᵥ v)) • (g *ᵥ u) + p • (g *ᵥ v) := by
  rw [perfectFluid, add_mulVec, smul_mulVec, smul_mulVec, vmv_mulVec, smul_smul]

theorem projDown_mulVec (g : M) (n v : V) :
    projDown g n *ᵥ v = v + (n ⬝ᵥ v) • (g *ᵥ n) := by
  rw [projDown, add_mulVec, one_mulVec, vmv_mulVec]

theorem normalFlux_eq (g : M) (n : V) (T : M) :
    normalFlux g n T = -(T *ᵥ n + (n ⬝ᵥ (T *ᵥ n)) • (g *ᵥ n)) := by
  rw [normalFlux, ← mulVec_mulVec, projDown_mulVec]

theorem perfectFluid_symm {g : M} (hg : gᵀ = g) (w p : ℝ) (u : V) :
    (perfectFluid g w p u)ᵀ = perfectFluid g w p u := by
  simp [perfectFluid, transpose_add, transpose_smul, transpose_vecMulVec, hg]

section Pointwise

variable {g ginv : M} {n β : V}

theorem n_dot_ul (hn : n ⬝ᵥ (g *ᵥ n) = -1) (hβ : n ⬝ᵥ (g *ᵥ β) = 0) (γ : ℝ) :
    n ⬝ᵥ (g *ᵥ (γ • (n + β))) = -γ := by
  rw [mulVec_smul, mulVec_add, dotProduct_smul, dotProduct_add, hn, hβ]
  simp

theorem ul_dot_n (hn : n ⬝ᵥ (g *ᵥ n) = -1) (hβ : n ⬝ᵥ (g *ᵥ β) = 0) (γ : ℝ) :
    (g *ᵥ (γ • (n + β))) ⬝ᵥ n = -γ := by
  rw [dotProduct_comm]
  exact n_dot_ul hn hβ γ

theorem beta_dot_n (hg : gᵀ = g) (hβ : n ⬝ᵥ (g *ᵥ β) = 0) : β ⬝ᵥ (g *ᵥ n) = 0 := by
  rw [dotProduct_mulVec, ← g_mulVec_eq_vecMul hg, dotProduct_comm]
  exact hβ

theorem quad (hg : gᵀ = g) (hn : n ⬝ᵥ (g *ᵥ n) = -1) (hβ : n ⬝ᵥ (g *ᵥ β) = 0) (γ : ℝ) :
    (γ • (n + β)) ⬝ᵥ (g *ᵥ (γ • (n + β))) = γ ^ 2 * (β ⬝ᵥ (g *ᵥ β) - 1) := by
  rw [mulVec_smul, mulVec_add, smul_dotProduct, dotProduct_smul, add_dotProduct, dotProduct_add,
    dotProduct_add, hn, hβ, beta_dot_n hg hβ]
  simp only [smul_eq_mul]
  ring

/-! ### A. Perfect-fluid normal projection -/

/-- A1: exact `γ²` coefficient, `J_a = w γ² β_a`. -/
theorem normalFlux_perfectFluid (hg : gᵀ = g) (hn : n ⬝ᵥ (g *ᵥ n) = -1)
    (hβ : n ⬝ᵥ (g *ᵥ β) = 0) (w p γ : ℝ) :
    normalFlux g n (perfectFluid g w p (γ • (n + β))) = (w * γ ^ 2) • (g *ᵥ β) := by
  rw [normalFlux_eq, perfectFluid_mulVec, ul_dot_n hn hβ, dotProduct_add, dotProduct_smul,
    dotProduct_smul, n_dot_ul hn hβ, hn, mulVec_smul, mulVec_add]
  funext a
  simp only [Pi.neg_apply, Pi.add_apply, Pi.smul_apply, smul_eq_mul]
  ring

/-- A2: `E_N = w γ² - p`. -/
theorem normalEnergy_perfectFluid (hg : gᵀ = g) (hn : n ⬝ᵥ (g *ᵥ n) = -1)
    (hβ : n ⬝ᵥ (g *ᵥ β) = 0) (w p γ : ℝ) :
    normalEnergy n (perfectFluid g w p (γ • (n + β))) = w * γ ^ 2 - p := by
  rw [normalEnergy, perfectFluid_mulVec, ul_dot_n hn hβ, dotProduct_add, dotProduct_smul,
    dotProduct_smul, n_dot_ul hn hβ, hn]
  simp only [smul_eq_mul]
  ring

theorem projDown_ul (hn : n ⬝ᵥ (g *ᵥ n) = -1) (hβ : n ⬝ᵥ (g *ᵥ β) = 0) (γ : ℝ) :
    projDown g n *ᵥ (g *ᵥ (γ • (n + β))) = γ • (g *ᵥ β) := by
  rw [projDown_mulVec, n_dot_ul hn hβ, mulVec_smul, mulVec_add]
  funext a
  simp only [Pi.add_apply, Pi.smul_apply, smul_eq_mul]
  ring

theorem projDown_g_projDownT (hg : gᵀ = g) (hn : n ⬝ᵥ (g *ᵥ n) = -1) :
    projDown g n * g * (projDown g n)ᵀ = hDown g n := by
  rw [projDown_transpose]
  have h1 : projDown g n * g = hDown g n := by
    rw [projDown, add_mul, Matrix.one_mul, vecMulVec_mul, ← g_mulVec_eq_vecMul hg, hDown]
  rw [h1, hDown, projUp, mul_add, Matrix.mul_one, add_mul, mul_vecMulVec,
    vecMulVec_mul_vecMulVec, ul_dot_u hn, neg_one_smul, vecMulVec_neg]
  abel

/-- A3: `S_ab = p h_ab + w γ² β_a β_b`. -/
theorem normalStress_perfectFluid (hg : gᵀ = g) (hn : n ⬝ᵥ (g *ᵥ n) = -1)
    (hβ : n ⬝ᵥ (g *ᵥ β) = 0) (w p γ : ℝ) :
    normalStress g n (perfectFluid g w p (γ • (n + β))) =
      p • hDown g n + (w * γ ^ 2) • vecMulVec (g *ᵥ β) (g *ᵥ β) := by
  have hP : ∀ a b : V, projDown g n * vecMulVec a b * (projDown g n)ᵀ =
      vecMulVec (projDown g n *ᵥ a) (projDown g n *ᵥ b) := by
    intro a b
    rw [mul_vecMulVec, vecMulVec_mul, vecMul_transpose]
  rw [normalStress, perfectFluid, Matrix.mul_add, add_mul, Matrix.mul_smul, Matrix.smul_mul,
    Matrix.mul_smul, Matrix.smul_mul, hP, projDown_ul hn hβ, projDown_g_projDownT hg hn]
  ext i j
  simp only [Matrix.add_apply, Matrix.smul_apply, vecMulVec_apply, Pi.smul_apply, smul_eq_mul]
  ring

/-- A4: normalization `u·u = -1` of `u = γ(n+β)` forces `β² < 1` and `γ² = 1/(1-β²)`. -/
theorem gamma_sq_of_normalized {γ : ℝ} (hg : gᵀ = g) (hn : n ⬝ᵥ (g *ᵥ n) = -1)
    (hβ : n ⬝ᵥ (g *ᵥ β) = 0) (hu : (γ • (n + β)) ⬝ᵥ (g *ᵥ (γ • (n + β))) = -1) :
    β ⬝ᵥ (g *ᵥ β) < 1 ∧ γ ^ 2 = 1 / (1 - β ⬝ᵥ (g *ᵥ β)) := by
  rw [quad hg hn hβ] at hu
  have h1 : γ ^ 2 * (1 - β ⬝ᵥ (g *ᵥ β)) = 1 := by linear_combination -hu
  have hlt : β ⬝ᵥ (g *ᵥ β) < 1 := by
    by_contra hc
    push_neg at hc
    have : γ ^ 2 * (1 - β ⬝ᵥ (g *ᵥ β)) ≤ 0 :=
      mul_nonpos_of_nonneg_of_nonpos (sq_nonneg γ) (by linarith)
    linarith
  refine ⟨hlt, ?_⟩
  rw [eq_div_iff (sub_pos.mpr hlt).ne']
  exact h1

theorem gamma_ne_zero {γ : ℝ} (hg : gᵀ = g) (hn : n ⬝ᵥ (g *ᵥ n) = -1)
    (hβ : n ⬝ᵥ (g *ᵥ β) = 0) (hu : (γ • (n + β)) ⬝ᵥ (g *ᵥ (γ • (n + β))) = -1) : γ ≠ 0 := by
  intro h0
  rw [quad hg hn hβ, h0] at hu
  norm_num at hu

/-- A5: `J = w/(1-β²) β`. -/
theorem flux_exact_coefficient {γ : ℝ} (hg : gᵀ = g) (hn : n ⬝ᵥ (g *ᵥ n) = -1)
    (hβ : n ⬝ᵥ (g *ᵥ β) = 0) (hu : (γ • (n + β)) ⬝ᵥ (g *ᵥ (γ • (n + β))) = -1) (w p : ℝ) :
    normalFlux g n (perfectFluid g w p (γ • (n + β))) =
      (w / (1 - β ⬝ᵥ (g *ᵥ β))) • (g *ᵥ β) := by
  rw [normalFlux_perfectFluid hg hn hβ, (gamma_sq_of_normalized hg hn hβ hu).2, mul_one_div]

/-- A6: `β_a = J_a/(E_N + p)`. -/
theorem beta_eq_flux_div_enthalpy {γ w : ℝ} (hg : gᵀ = g) (hn : n ⬝ᵥ (g *ᵥ n) = -1)
    (hβ : n ⬝ᵥ (g *ᵥ β) = 0) (hu : (γ • (n + β)) ⬝ᵥ (g *ᵥ (γ • (n + β))) = -1)
    (hw : w ≠ 0) (p : ℝ) :
    g *ᵥ β = (normalEnergy n (perfectFluid g w p (γ • (n + β))) + p)⁻¹ •
      normalFlux g n (perfectFluid g w p (γ • (n + β))) := by
  have hγ := gamma_ne_zero hg hn hβ hu
  rw [normalEnergy_perfectFluid hg hn hβ, normalFlux_perfectFluid hg hn hβ, smul_smul,
    sub_add_cancel, inv_mul_cancel₀ (mul_ne_zero hw (pow_ne_zero 2 hγ)), one_smul]

/-- A7: rank-one stress `S = p h + J J/(E_N + p)`. -/
theorem normalStress_rank_one {γ w : ℝ} (hg : gᵀ = g) (hn : n ⬝ᵥ (g *ᵥ n) = -1)
    (hβ : n ⬝ᵥ (g *ᵥ β) = 0) (hu : (γ • (n + β)) ⬝ᵥ (g *ᵥ (γ • (n + β))) = -1)
    (hw : w ≠ 0) (p : ℝ) :
    normalStress g n (perfectFluid g w p (γ • (n + β))) =
      p • hDown g n + (normalEnergy n (perfectFluid g w p (γ • (n + β))) + p)⁻¹ •
        vecMulVec (normalFlux g n (perfectFluid g w p (γ • (n + β))))
          (normalFlux g n (perfectFluid g w p (γ • (n + β)))) := by
  have hγ := gamma_ne_zero hg hn hβ hu
  have hc : w * γ ^ 2 ≠ 0 := mul_ne_zero hw (pow_ne_zero 2 hγ)
  rw [normalStress_perfectFluid hg hn hβ, normalEnergy_perfectFluid hg hn hβ,
    normalFlux_perfectFluid hg hn hβ, sub_add_cancel]
  ext i j
  simp only [Matrix.add_apply, Matrix.smul_apply, vecMulVec_apply, Pi.smul_apply, smul_eq_mul]
  field_simp

end Pointwise

/-! ### B. Scalar inverse `r = |J|/w` -/

/-- B1: the square-root denominator is positive for every real `r`. -/
theorem betaOfRatio_denominator_pos (r : ℝ) : 0 < 1 + Real.sqrt (1 + 4 * r ^ 2) := by
  positivity

/-- B2: `r = 0` branch. -/
theorem betaOfRatio_zero : betaOfRatio 0 = 0 := by
  simp [betaOfRatio]

/-- B3: `0 ≤ β < 1` on `r ≥ 0`. -/
theorem betaOfRatio_mem {r : ℝ} (hr : 0 ≤ r) : 0 ≤ betaOfRatio r ∧ betaOfRatio r < 1 := by
  have hd := betaOfRatio_denominator_pos r
  have hlt : 2 * r < Real.sqrt (1 + 4 * r ^ 2) := by
    rw [Real.lt_sqrt (by positivity)]
    nlinarith
  unfold betaOfRatio
  refine ⟨div_nonneg (by positivity) hd.le, ?_⟩
  rw [div_lt_one hd]
  linarith

/-- B4: `β = f(r)` solves `β/(1-β²) = r`. -/
theorem betaOfRatio_solves {r : ℝ} (hr : 0 ≤ r) : betaOfRatio r / (1 - betaOfRatio r ^ 2) = r := by
  have hd := betaOfRatio_denominator_pos r
  unfold betaOfRatio
  set s := Real.sqrt (1 + 4 * r ^ 2) with hs
  have hs2 : s ^ 2 = 1 + 4 * r ^ 2 := Real.sq_sqrt (by positivity)
  have hne : 1 + s ≠ 0 := hd.ne'
  have e1 : (1 + s) ^ 2 - (2 * r) ^ 2 = 2 * (1 + s) := by linear_combination hs2
  have h1 : 1 - (2 * r / (1 + s)) ^ 2 = 2 / (1 + s) := by
    rw [div_pow, one_sub_div (pow_ne_zero 2 hne), e1, pow_two, mul_div_mul_right _ _ hne]
  rw [h1]
  field_simp

/-- B5: uniqueness of the root on `[0,1)`. -/
theorem betaOfRatio_unique {b r : ℝ} (hb0 : 0 ≤ b) (hb1 : b < 1) (h : b / (1 - b ^ 2) = r) :
    b = betaOfRatio r := by
  rw [← h]
  exact (betaOfRatio_flux b hb0 hb1).symm

section PointwiseInverse

variable {g ginv : M} {n β : V}

/-- B6: `|J| = w γ² |β|`. -/
theorem fluxNorm_perfectFluid {γ w : ℝ} (hg : gᵀ = g) (hinv : g * ginv = 1)
    (hn : n ⬝ᵥ (g *ᵥ n) = -1) (hβ : n ⬝ᵥ (g *ᵥ β) = 0)
    (hu : (γ • (n + β)) ⬝ᵥ (g *ᵥ (γ • (n + β))) = -1) (hw : 0 ≤ w) (p : ℝ) :
    fluxNorm ginv (normalFlux g n (perfectFluid g w p (γ • (n + β)))) =
      w * γ ^ 2 * Real.sqrt (β ⬝ᵥ (g *ᵥ β)) := by
  have hc : 0 ≤ w * γ ^ 2 := by positivity
  have hdot : (w * γ ^ 2) • (g *ᵥ β) ⬝ᵥ (ginv *ᵥ ((w * γ ^ 2) • (g *ᵥ β))) =
      (w * γ ^ 2) ^ 2 * (β ⬝ᵥ (g *ᵥ β)) := by
    rw [mulVec_smul, ginv_mulVec_ul hinv, smul_dotProduct, dotProduct_smul, dotProduct_comm]
    simp only [smul_eq_mul]
    ring
  rw [normalFlux_perfectFluid hg hn hβ, fluxNorm, hdot, Real.sqrt_mul (sq_nonneg _),
    Real.sqrt_sq hc]

/-- B7: scalar inverse `f(|J|/w) = |β|`. -/
theorem scalar_flux_inverse {γ w : ℝ} (hg : gᵀ = g) (hinv : g * ginv = 1)
    (hn : n ⬝ᵥ (g *ᵥ n) = -1) (hβ : n ⬝ᵥ (g *ᵥ β) = 0)
    (hu : (γ • (n + β)) ⬝ᵥ (g *ᵥ (γ • (n + β))) = -1) (hw : 0 < w)
    (hβnn : 0 ≤ β ⬝ᵥ (g *ᵥ β)) (p : ℝ) :
    betaOfRatio (fluxNorm ginv (normalFlux g n (perfectFluid g w p (γ • (n + β)))) / w) =
      Real.sqrt (β ⬝ᵥ (g *ᵥ β)) := by
  obtain ⟨hlt, hγ2⟩ := gamma_sq_of_normalized hg hn hβ hu
  rw [fluxNorm_perfectFluid hg hinv hn hβ hu hw.le]
  have hb0 : 0 ≤ Real.sqrt (β ⬝ᵥ (g *ᵥ β)) := Real.sqrt_nonneg _
  have hb2 : Real.sqrt (β ⬝ᵥ (g *ᵥ β)) ^ 2 = β ⬝ᵥ (g *ᵥ β) := Real.sq_sqrt hβnn
  have hb1 : Real.sqrt (β ⬝ᵥ (g *ᵥ β)) < 1 := by nlinarith
  have hw0 : w ≠ 0 := hw.ne'
  have hd : 1 - β ⬝ᵥ (g *ᵥ β) ≠ 0 := (sub_pos.mpr hlt).ne'
  have hr : w * γ ^ 2 * Real.sqrt (β ⬝ᵥ (g *ᵥ β)) / w =
      Real.sqrt (β ⬝ᵥ (g *ᵥ β)) / (1 - Real.sqrt (β ⬝ᵥ (g *ᵥ β)) ^ 2) := by
    rw [hb2, hγ2]
    field_simp
  rw [hr]
  exact betaOfRatio_flux _ hb0 hb1

/-- B8: for `w ≠ 0`, `J = 0 ↔ β = 0` (single fluid only). -/
theorem flux_zero_iff {γ w : ℝ} (hg : gᵀ = g) (hinv : g * ginv = 1)
    (hn : n ⬝ᵥ (g *ᵥ n) = -1) (hβ : n ⬝ᵥ (g *ᵥ β) = 0)
    (hu : (γ • (n + β)) ⬝ᵥ (g *ᵥ (γ • (n + β))) = -1) (hw : w ≠ 0) (p : ℝ) :
    normalFlux g n (perfectFluid g w p (γ • (n + β))) = 0 ↔ β = 0 := by
  have hγ := gamma_ne_zero hg hn hβ hu
  rw [normalFlux_perfectFluid hg hn hβ, smul_eq_zero]
  constructor
  · rintro (h | h)
    · exact absurd h (mul_ne_zero hw (pow_ne_zero 2 hγ))
    · have h2 := congrArg (fun v => ginv *ᵥ v) h
      simpa [ginv_mulVec_ul hinv] using h2
  · intro h
    right
    rw [h, mulVec_zero]

/-! ### C. Vector inverse -/

/-- C1: zero branch. -/
theorem betaVector_zero (ginv : M) (w : ℝ) : betaVector ginv w 0 = 0 := by
  simp [betaVector]

/-- C2: nonzero-direction branch. -/
theorem betaVector_of_ne {ginv : M} {w : ℝ} {J : V} (hJ : J ≠ 0) :
    betaVector ginv w J = (betaOfRatio (fluxNorm ginv J / w) / fluxNorm ginv J) • J := by
  rw [betaVector, if_neg hJ]

/-- C3: vector inverse recovers `β_a` and `β^a`. -/
theorem vector_flux_inverse {γ w : ℝ} (hg : gᵀ = g) (hinv : g * ginv = 1)
    (hn : n ⬝ᵥ (g *ᵥ n) = -1) (hβ : n ⬝ᵥ (g *ᵥ β) = 0)
    (hu : (γ • (n + β)) ⬝ᵥ (g *ᵥ (γ • (n + β))) = -1) (hw : 0 < w)
    (hpos : β ≠ 0 → 0 < β ⬝ᵥ (g *ᵥ β)) (p : ℝ) :
    betaVector ginv w (normalFlux g n (perfectFluid g w p (γ • (n + β)))) = g *ᵥ β ∧
    ginv *ᵥ betaVector ginv w (normalFlux g n (perfectFluid g w p (γ • (n + β)))) = β := by
  have key : betaVector ginv w (normalFlux g n (perfectFluid g w p (γ • (n + β)))) =
      g *ᵥ β := by
    by_cases hb : β = 0
    · rw [normalFlux_perfectFluid hg hn hβ, hb, mulVec_zero, smul_zero, betaVector_zero]
    · have hJ : normalFlux g n (perfectFluid g w p (γ • (n + β))) ≠ 0 := fun h =>
        hb ((flux_zero_iff hg hinv hn hβ hu hw.ne' p).1 h)
      have hγ := gamma_ne_zero hg hn hβ hu
      have hs : 0 < Real.sqrt (β ⬝ᵥ (g *ᵥ β)) := Real.sqrt_pos.2 (hpos hb)
      have hs0 := hs.ne'
      have hw0 : w ≠ 0 := hw.ne'
      rw [betaVector_of_ne hJ, scalar_flux_inverse hg hinv hn hβ hu hw (hpos hb).le p,
        fluxNorm_perfectFluid hg hinv hn hβ hu hw.le p, normalFlux_perfectFluid hg hn hβ,
        smul_smul]
      have hone : Real.sqrt (β ⬝ᵥ (g *ᵥ β)) / (w * γ ^ 2 * Real.sqrt (β ⬝ᵥ (g *ᵥ β))) *
          (w * γ ^ 2) = 1 := by
        field_simp
      rw [hone, one_smul]
  exact ⟨key, by rw [key, ginv_mulVec_ul hinv]⟩

end PointwiseInverse

/-- C4: Minkowski instance through the reviewed PORT-CAS-01 boost four-velocity. -/
theorem minkowski_flux_inverse (x y z : ℝ) (hs : PortCas01.s x y z < 1) {w : ℝ} (hw : 0 < w)
    (p : ℝ) :
    PortCas01.fourVelocity x y z = PortCas01.gamma x y z • (PortCas01.e0 + ![0, x, y, z]) ∧
    normalFlux PortCas01.eta PortCas01.e0
        (perfectFluid PortCas01.eta w p (PortCas01.fourVelocity x y z)) =
      (w * PortCas01.gamma x y z ^ 2) • ![0, x, y, z] ∧
    betaVector PortCas01.eta w (normalFlux PortCas01.eta PortCas01.e0
        (perfectFluid PortCas01.eta w p (PortCas01.fourVelocity x y z))) = ![0, x, y, z] ∧
    betaOfRatio (fluxNorm PortCas01.eta (normalFlux PortCas01.eta PortCas01.e0
        (perfectFluid PortCas01.eta w p (PortCas01.fourVelocity x y z))) / w) =
      Real.sqrt (PortCas01.s x y z) := by
  have hfv : PortCas01.fourVelocity x y z =
      PortCas01.gamma x y z • (PortCas01.e0 + ![0, x, y, z]) := by
    rw [PortCas01.fourVelocity_components]
    funext i
    fin_cases i <;> simp [PortCas01.e0]
  have hn : PortCas01.e0 ⬝ᵥ (PortCas01.eta *ᵥ PortCas01.e0) = -1 := by
    simp [PortCas01.e0, PortCas01.eta, dotProduct, mulVec, Fin.sum_univ_four]
  have hη : PortCas01.eta *ᵥ ![0, x, y, z] = ![0, x, y, z] := by
    funext i
    fin_cases i <;> simp [PortCas01.eta, mulVec, dotProduct, Fin.sum_univ_four]
  have hβ : PortCas01.e0 ⬝ᵥ (PortCas01.eta *ᵥ ![0, x, y, z]) = 0 := by
    rw [hη]
    simp [PortCas01.e0, dotProduct, Fin.sum_univ_four]
  have hbb : ![0, x, y, z] ⬝ᵥ (PortCas01.eta *ᵥ ![0, x, y, z]) = PortCas01.s x y z := by
    rw [hη]
    simp [dotProduct, Fin.sum_univ_four, PortCas01.s]
    ring
  have hu : (PortCas01.gamma x y z • (PortCas01.e0 + ![0, x, y, z])) ⬝ᵥ
      (PortCas01.eta *ᵥ (PortCas01.gamma x y z • (PortCas01.e0 + ![0, x, y, z]))) = -1 := by
    rw [← hfv]
    exact (PortCas01.future_mass_shell x y z hs).2
  have hpos : (![0, x, y, z] : V) ≠ 0 →
      0 < ![0, x, y, z] ⬝ᵥ (PortCas01.eta *ᵥ ![0, x, y, z]) := by
    intro hne
    rw [hbb]
    unfold PortCas01.s
    by_contra hle
    push_neg at hle
    apply hne
    have hx2 : x ^ 2 = 0 := by nlinarith [sq_nonneg x, sq_nonneg y, sq_nonneg z]
    have hy2 : y ^ 2 = 0 := by nlinarith [sq_nonneg x, sq_nonneg y, sq_nonneg z]
    have hz2 : z ^ 2 = 0 := by nlinarith [sq_nonneg x, sq_nonneg y, sq_nonneg z]
    have hx : x = 0 := pow_eq_zero_iff (n := 2) (by norm_num) |>.mp hx2
    have hy : y = 0 := pow_eq_zero_iff (n := 2) (by norm_num) |>.mp hy2
    have hz : z = 0 := pow_eq_zero_iff (n := 2) (by norm_num) |>.mp hz2
    funext i
    fin_cases i <;> simp [hx, hy, hz]
  have hsnn : 0 ≤ ![0, x, y, z] ⬝ᵥ (PortCas01.eta *ᵥ ![0, x, y, z]) := by
    rw [hbb]
    unfold PortCas01.s
    positivity
  rw [hfv]
  refine ⟨rfl, ?_, ?_, ?_⟩
  · rw [normalFlux_perfectFluid eta_symm hn hβ, hη]
  · rw [(vector_flux_inverse eta_symm eta_mul_eta hn hβ hu hw hpos p).1, hη]
  · rw [scalar_flux_inverse eta_symm eta_mul_eta hn hβ hu hw hsnn p, hbb]

/-! ### D. Multi-fluid negative control -/

/-- D1: the normal flux is additive in the stress tensor. -/
theorem normalFlux_add (g : M) (n : V) (T₁ T₂ : M) :
    normalFlux g n (T₁ + T₂) = normalFlux g n T₁ + normalFlux g n T₂ := by
  simp only [normalFlux, Matrix.mul_add, add_mulVec, neg_add]

theorem counterflow_gamma_sq : (2 / Real.sqrt 3) ^ 2 = (4 / 3 : ℝ) := by
  rw [div_pow, Real.sq_sqrt (by norm_num)]
  norm_num

/-- D2: explicit counterflow: two normalized, oppositely tilted unit-enthalpy dust components
with vanishing total flux but nonvanishing component flux. -/
theorem counterflow_control :
    ((2 / Real.sqrt 3) • (PortCas01.e0 + ![0, 1 / 2, 0, 0])) ⬝ᵥ
        (PortCas01.eta *ᵥ ((2 / Real.sqrt 3) • (PortCas01.e0 + ![0, 1 / 2, 0, 0]))) = -1 ∧
    ((2 / Real.sqrt 3) • (PortCas01.e0 + -![0, 1 / 2, 0, 0])) ⬝ᵥ
        (PortCas01.eta *ᵥ ((2 / Real.sqrt 3) • (PortCas01.e0 + -![0, 1 / 2, 0, 0]))) = -1 ∧
    normalFlux PortCas01.eta PortCas01.e0
        (perfectFluid PortCas01.eta 1 0 ((2 / Real.sqrt 3) • (PortCas01.e0 + ![0, 1 / 2, 0, 0])) +
          perfectFluid PortCas01.eta 1 0
            ((2 / Real.sqrt 3) • (PortCas01.e0 + -![0, 1 / 2, 0, 0]))) = 0 ∧
    (![0, 1 / 2, 0, 0] : V) ≠ 0 ∧
    normalFlux PortCas01.eta PortCas01.e0
        (perfectFluid PortCas01.eta 1 0
          ((2 / Real.sqrt 3) • (PortCas01.e0 + ![0, 1 / 2, 0, 0]))) ≠ 0 := by
  have hn : PortCas01.e0 ⬝ᵥ (PortCas01.eta *ᵥ PortCas01.e0) = -1 := by
    simp [PortCas01.e0, PortCas01.eta, dotProduct, mulVec, Fin.sum_univ_four]
  have hη : PortCas01.eta *ᵥ (![0, 1 / 2, 0, 0] : V) = ![0, 1 / 2, 0, 0] := by
    funext i
    fin_cases i <;> simp [PortCas01.eta, mulVec, dotProduct, Fin.sum_univ_four]
  have hβ₁ : PortCas01.e0 ⬝ᵥ (PortCas01.eta *ᵥ (![0, 1 / 2, 0, 0] : V)) = 0 := by
    rw [hη]
    simp [PortCas01.e0, dotProduct, Fin.sum_univ_four]
  have hβ₂ : PortCas01.e0 ⬝ᵥ (PortCas01.eta *ᵥ (-![0, 1 / 2, 0, 0] : V)) = 0 := by
    rw [mulVec_neg, dotProduct_neg, hβ₁, neg_zero]
  have hbb₁ : (![0, 1 / 2, 0, 0] : V) ⬝ᵥ (PortCas01.eta *ᵥ ![0, 1 / 2, 0, 0]) = 1 / 4 := by
    rw [hη]
    simp [dotProduct, Fin.sum_univ_four]
    norm_num
  have hbb₂ : (-![0, 1 / 2, 0, 0] : V) ⬝ᵥ (PortCas01.eta *ᵥ (-![0, 1 / 2, 0, 0])) = 1 / 4 := by
    rw [mulVec_neg, neg_dotProduct, dotProduct_neg, neg_neg, hbb₁]
  refine ⟨?_, ?_, ?_, ?_, ?_⟩
  · rw [quad eta_symm hn hβ₁, hbb₁, counterflow_gamma_sq]
    norm_num
  · rw [quad eta_symm hn hβ₂, hbb₂, counterflow_gamma_sq]
    norm_num
  · rw [normalFlux_add, normalFlux_perfectFluid eta_symm hn hβ₁,
      normalFlux_perfectFluid eta_symm hn hβ₂, mulVec_neg, smul_neg, add_neg_cancel]
  · intro h
    have h1 := congrFun h 1
    norm_num at h1
  · rw [normalFlux_perfectFluid eta_symm hn hβ₁, hη, counterflow_gamma_sq]
    intro h
    have h1 := congrFun h 1
    norm_num at h1

/-- D3: no `J_total = 0 ⇒ untilted` converse for unseparated two-fluid mixtures. -/
theorem not_total_flux_zero_implies_untilted :
    ¬ ∀ (w₁ w₂ p₁ p₂ γ₁ γ₂ : ℝ) (β₁ β₂ : V), 0 < w₁ → 0 < w₂ →
      PortCas01.e0 ⬝ᵥ (PortCas01.eta *ᵥ β₁) = 0 → PortCas01.e0 ⬝ᵥ (PortCas01.eta *ᵥ β₂) = 0 →
      (γ₁ • (PortCas01.e0 + β₁)) ⬝ᵥ (PortCas01.eta *ᵥ (γ₁ • (PortCas01.e0 + β₁))) = -1 →
      (γ₂ • (PortCas01.e0 + β₂)) ⬝ᵥ (PortCas01.eta *ᵥ (γ₂ • (PortCas01.e0 + β₂))) = -1 →
      normalFlux PortCas01.eta PortCas01.e0
          (perfectFluid PortCas01.eta w₁ p₁ (γ₁ • (PortCas01.e0 + β₁)) +
            perfectFluid PortCas01.eta w₂ p₂ (γ₂ • (PortCas01.e0 + β₂))) = 0 →
      β₁ = 0 := by
  intro h
  obtain ⟨h1, h2, h3, h4, _⟩ := counterflow_control
  have hη : PortCas01.eta *ᵥ (![0, 1 / 2, 0, 0] : V) = ![0, 1 / 2, 0, 0] := by
    funext i
    fin_cases i <;> simp [PortCas01.eta, mulVec, dotProduct, Fin.sum_univ_four]
  have hβ₁ : PortCas01.e0 ⬝ᵥ (PortCas01.eta *ᵥ (![0, 1 / 2, 0, 0] : V)) = 0 := by
    rw [hη]
    simp [PortCas01.e0, dotProduct, Fin.sum_univ_four]
  have hβ₂ : PortCas01.e0 ⬝ᵥ (PortCas01.eta *ᵥ (-![0, 1 / 2, 0, 0] : V)) = 0 := by
    rw [mulVec_neg, dotProduct_neg, hβ₁, neg_zero]
  exact h4 (h 1 1 0 0 _ _ _ _ one_pos one_pos hβ₁ hβ₂ h1 h2 h3)

/-! ## E. Chart-level contracted Codazzi constraint -/

/-- Levi-Civita symbols `Γ^a_{bc} = ½ g^{ad}(∂_b g_dc + ∂_c g_db - ∂_d g_bc)`. -/
noncomputable def christoffel (g ginv : Pt → M) (y : Pt) (a b c : Fin 4) : ℝ :=
  (1 / 2) * ∑ d, ginv y a d * (pd (fun z => g z d c) y b + pd (fun z => g z d b) y c
    - pd (fun z => g z b c) y d)

/-- `R_bd = R^a_{bad}`. -/
noncomputable def ricci (Γ : Pt → Fin 4 → Fin 4 → Fin 4 → ℝ) (x : Pt) (b d : Fin 4) : ℝ :=
  ∑ a, pd (fun y => Γ y a d b) x a - ∑ a, pd (fun y => Γ y a a b) x d
    + ∑ a, ∑ e, Γ x a a e * Γ x e d b - ∑ a, ∑ e, Γ x a d e * Γ x e a b

noncomputable def scalarCurvature (Γ : Pt → Fin 4 → Fin 4 → Fin 4 → ℝ) (ginv : Pt → M)
    (x : Pt) : ℝ :=
  ∑ b, ∑ d, ginv x b d * ricci Γ x b d

noncomputable def einstein (Γ : Pt → Fin 4 → Fin 4 → Fin 4 → ℝ) (g ginv : Pt → M) (x : Pt)
    (b d : Fin 4) : ℝ :=
  ricci Γ x b d - (1 / 2) * scalarCurvature Γ ginv x * g x b d

/-- Future unit normal of the `x^0 = const` slicing: `n_b = -δ_b^0/√(-g^00)`, `n^a = g^{ab} n_b`. -/
noncomputable def sliceNormal (ginv : Pt → M) (y : Pt) : V :=
  fun a => -ginv y a 0 / Real.sqrt (-ginv y 0 0)

/-- `K_ab = -h_a^c h_b^d ∇_c n_d`. -/
noncomputable def extrinsicDown (g ginv : Pt → M) (y : Pt) : M :=
  -spatialJet (g y) (sliceNormal ginv y) (velJetMatrix (christoffel g ginv) g (sliceNormal ginv) y)

/-- `K^b_a = g^{bc} K_ca`. -/
noncomputable def extrinsicMixed (g ginv : Pt → M) (y : Pt) : M :=
  ginv y * extrinsicDown g ginv y

/-- `K = K^a_a`. -/
noncomputable def meanCurvature (g ginv : Pt → M) (y : Pt) : ℝ :=
  trace (extrinsicMixed g ginv y)

/-- `∇_r K^p_q`. -/
noncomputable def nablaMixed (Γ : Pt → Fin 4 → Fin 4 → Fin 4 → ℝ) (Km : Pt → M) (x : Pt)
    (r p q : Fin 4) : ℝ :=
  pd (fun y => Km y p q) x r + ∑ s, Γ x p r s * Km x s q - ∑ s, Γ x s r q * Km x p s

/-- `D_b K^b_a = h^b_p h^q_a h^r_b ∇_r K^p_q`. -/
noncomputable def codazziDiv (g ginv : Pt → M) (x : Pt) (a : Fin 4) : ℝ :=
  ∑ b, ∑ p, ∑ q, ∑ r, projUp (g x) (sliceNormal ginv x) b p *
    projUp (g x) (sliceNormal ginv x) q a * projUp (g x) (sliceNormal ginv x) r b *
      nablaMixed (christoffel g ginv) (extrinsicMixed g ginv) x r p q

/-- `D_a K = h^r_a ∂_r K`. -/
noncomputable def codazziGrad (g ginv : Pt → M) (x : Pt) (a : Fin 4) : ℝ :=
  ∑ r, projUp (g x) (sliceNormal ginv x) r a * pd (meanCurvature g ginv) x r

/-- `D_b K^b_a - D_a K`. -/
noncomputable def codazziLHS (g ginv : Pt → M) (x : Pt) (a : Fin 4) : ℝ :=
  codazziDiv g ginv x a - codazziGrad g ginv x a

/-- Gaussian normal chart on an open set `U`: `g_00 = -1`, `g_0i = 0`. -/
structure GaussianChart (g ginv : Pt → M) (U : Set Pt) : Prop where
  isOpen : IsOpen U
  symm : ∀ y ∈ U, (g y)ᵀ = g y
  inv : ∀ y ∈ U, g y * ginv y = 1
  g00 : ∀ y ∈ U, g y 0 0 = -1
  g0i : ∀ y ∈ U, ∀ i : Fin 4, i ≠ 0 → g y 0 i = 0

/-! ### Derivative helpers -/

theorem pd_congr {f f' : Pt → ℝ} {x : Pt} (h : f =ᶠ[𝓝 x] f') (r : Fin 4) :
    pd f x r = pd f' x r := by
  unfold pd
  rw [h.fderiv_eq]

theorem pd_const (c : ℝ) (x : Pt) (r : Fin 4) : pd (fun _ => c) x r = 0 := by
  simp [pd]

theorem pd_neg (f : Pt → ℝ) (x : Pt) (r : Fin 4) : pd (fun y => -f y) x r = -pd f x r := by
  unfold pd
  rw [fderiv_fun_neg]
  rfl

theorem pd_sum {f : Fin 4 → Pt → ℝ} {x : Pt} (hf : ∀ i, DifferentiableAt ℝ (f i) x)
    (r : Fin 4) : pd (fun y => ∑ i, f i y) x r = ∑ i, pd (f i) x r := by
  unfold pd
  rw [fderiv_fun_sum (fun i _ => hf i)]
  simp

/-! ### E1: unit normal -/

/-- E1: the slice normal is unit timelike and future directed whenever `g^00 < 0`. -/
theorem sliceNormal_unit {g ginv : Pt → M} {y : Pt} (hinv : g y * ginv y = 1)
    (h00 : ginv y 0 0 < 0) :
    sliceNormal ginv y ⬝ᵥ (g y *ᵥ sliceNormal ginv y) = -1 ∧ 0 < sliceNormal ginv y 0 := by
  have hpos : 0 < -ginv y 0 0 := by linarith
  set s := Real.sqrt (-ginv y 0 0) with hsdef
  have hs : 0 < s := Real.sqrt_pos.2 hpos
  have hs2 : s ^ 2 = -ginv y 0 0 := Real.sq_sqrt hpos.le
  have ht : s⁻¹ ^ 2 * s ^ 2 = 1 := by rw [← mul_pow, inv_mul_cancel₀ hs.ne', one_pow]
  have key : ∀ a, ∑ b, g y a b * ginv y b 0 = if a = 0 then 1 else 0 := by
    intro a
    have := congrFun (congrFun hinv a) 0
    simpa [Matrix.mul_apply, Matrix.one_apply] using this
  have k0 : g y 0 0 * ginv y 0 0 + g y 0 1 * ginv y 1 0 + g y 0 2 * ginv y 2 0 +
      g y 0 3 * ginv y 3 0 = 1 := by simpa [Fin.sum_univ_four] using key 0
  have k1 : g y 1 0 * ginv y 0 0 + g y 1 1 * ginv y 1 0 + g y 1 2 * ginv y 2 0 +
      g y 1 3 * ginv y 3 0 = 0 := by simpa [Fin.sum_univ_four] using key 1
  have k2 : g y 2 0 * ginv y 0 0 + g y 2 1 * ginv y 1 0 + g y 2 2 * ginv y 2 0 +
      g y 2 3 * ginv y 3 0 = 0 := by simpa [Fin.sum_univ_four] using key 2
  have k3 : g y 3 0 * ginv y 0 0 + g y 3 1 * ginv y 1 0 + g y 3 2 * ginv y 2 0 +
      g y 3 3 * ginv y 3 0 = 0 := by simpa [Fin.sum_univ_four] using key 3
  constructor
  · simp only [sliceNormal, dotProduct, mulVec, Fin.sum_univ_four, div_eq_mul_inv]
    rw [← hsdef]
    linear_combination s⁻¹ ^ 2 * (ginv y 0 0 * k0 + ginv y 1 0 * k1 + ginv y 2 0 * k2 +
      ginv y 3 0 * k3) + s⁻¹ ^ 2 * hs2 - ht
  · simp only [sliceNormal]
    rw [← hsdef]
    exact div_pos hpos hs

section Gaussian

variable {g ginv : Pt → M} {U : Set Pt}

theorem gauss_sym (hG : GaussianChart g ginv U) {y : Pt} (hy : y ∈ U) (i j : Fin 4) :
    g y i j = g y j i := by
  have := congrFun (congrFun (hG.symm y hy) j) i
  simpa [Matrix.transpose_apply] using this

theorem gauss_g (hG : GaussianChart g ginv U) {y : Pt} (hy : y ∈ U) :
    g y 0 0 = -1 ∧ g y 0 1 = 0 ∧ g y 0 2 = 0 ∧ g y 0 3 = 0 ∧
      g y 1 0 = 0 ∧ g y 2 0 = 0 ∧ g y 3 0 = 0 := by
  have h1 := hG.g0i y hy 1 (by decide)
  have h2 := hG.g0i y hy 2 (by decide)
  have h3 := hG.g0i y hy 3 (by decide)
  refine ⟨hG.g00 y hy, h1, h2, h3, ?_, ?_, ?_⟩
  · rw [gauss_sym hG hy]; exact h1
  · rw [gauss_sym hG hy]; exact h2
  · rw [gauss_sym hG hy]; exact h3

theorem gauss_ginv (hG : GaussianChart g ginv U) {y : Pt} (hy : y ∈ U) :
    ginv y 0 0 = -1 ∧ ginv y 0 1 = 0 ∧ ginv y 0 2 = 0 ∧ ginv y 0 3 = 0 ∧
      ginv y 1 0 = 0 ∧ ginv y 2 0 = 0 ∧ ginv y 3 0 = 0 := by
  obtain ⟨a0, a1, a2, a3, b1, b2, b3⟩ := gauss_g hG hy
  have hinv := hG.inv y hy
  have hinv' : ginv y * g y = 1 := mul_eq_one_comm.mp hinv
  have r : ∀ j, (g y * ginv y) 0 j = (1 : M) 0 j := fun j => by rw [hinv]
  have c : ∀ j, (ginv y * g y) j 0 = (1 : M) j 0 := fun j => by rw [hinv']
  have r0 := r 0
  have r1 := r 1
  have r2 := r 2
  have r3 := r 3
  have c1 := c 1
  have c2 := c 2
  have c3 := c 3
  simp only [Matrix.mul_apply, Fin.sum_univ_four, a0, a1, a2, a3, b1, b2, b3,
    Matrix.one_apply] at r0 r1 r2 r3 c1 c2 c3
  norm_num at r0 r1 r2 r3 c1 c2 c3
  refine ⟨by linarith, by linarith, by linarith, by linarith, by linarith, by linarith,
    by linarith⟩

theorem gauss_col0 (hG : GaussianChart g ginv U) {y : Pt} (hy : y ∈ U) (b : Fin 4) :
    g y b 0 = if b = 0 then -1 else 0 := by
  obtain ⟨a0, -, -, -, b1, b2, b3⟩ := gauss_g hG hy
  fin_cases b <;> simp [a0, b1, b2, b3]

theorem gauss_row0 (hG : GaussianChart g ginv U) {y : Pt} (hy : y ∈ U) (c : Fin 4) :
    g y 0 c = if c = 0 then -1 else 0 := by
  rw [gauss_sym hG hy]
  exact gauss_col0 hG hy c

theorem gauss_pd_row0 (hG : GaussianChart g ginv U) {y : Pt} (hy : y ∈ U) (c r : Fin 4) :
    pd (fun z => g z 0 c) y r = 0 := by
  have hev : (fun z => g z 0 c) =ᶠ[𝓝 y] fun _ => (if c = 0 then -1 else 0 : ℝ) := by
    filter_upwards [hG.isOpen.mem_nhds hy] with z hz
    exact gauss_row0 hG hz c
  rw [pd_congr hev, pd_const]

theorem gauss_pd_col0 (hG : GaussianChart g ginv U) {y : Pt} (hy : y ∈ U) (c r : Fin 4) :
    pd (fun z => g z c 0) y r = 0 := by
  have hev : (fun z => g z c 0) =ᶠ[𝓝 y] fun _ => (if c = 0 then -1 else 0 : ℝ) := by
    filter_upwards [hG.isOpen.mem_nhds hy] with z hz
    exact gauss_col0 hG hz c
  rw [pd_congr hev, pd_const]

theorem gauss_pd_symm (hG : GaussianChart g ginv U) {y : Pt} (hy : y ∈ U) (b c r : Fin 4) :
    pd (fun z => g z b c) y r = pd (fun z => g z c b) y r := by
  apply pd_congr
  filter_upwards [hG.isOpen.mem_nhds hy] with z hz
  exact gauss_sym hG hz b c

/-- E1': in a Gaussian chart the slice normal is `∂_0`. -/
theorem sliceNormal_gaussian (hG : GaussianChart g ginv U) {y : Pt} (hy : y ∈ U) :
    sliceNormal ginv y = Pi.single 0 1 := by
  obtain ⟨a0, -, -, -, b1, b2, b3⟩ := gauss_ginv hG hy
  funext a
  fin_cases a <;> simp [sliceNormal, a0, b1, b2, b3]

theorem gauss_gn (hG : GaussianChart g ginv U) {y : Pt} (hy : y ∈ U) :
    g y *ᵥ (Pi.single 0 1 : V) = ![-1, 0, 0, 0] := by
  obtain ⟨a0, -, -, -, b1, b2, b3⟩ := gauss_g hG hy
  funext a
  fin_cases a <;> simp [mulVec, dotProduct, Fin.sum_univ_four, a0, b1, b2, b3]

theorem gauss_projDown (hG : GaussianChart g ginv U) {y : Pt} (hy : y ∈ U) :
    projDown (g y) (Pi.single 0 1) = diagonal ![0, 1, 1, 1] := by
  rw [projDown, gauss_gn hG hy]
  ext i j
  fin_cases i <;> fin_cases j <;> simp [vecMulVec_apply, Matrix.one_apply, diagonal_apply]

theorem gauss_projUp (hG : GaussianChart g ginv U) {y : Pt} (hy : y ∈ U) :
    projUp (g y) (Pi.single 0 1) = diagonal ![0, 1, 1, 1] := by
  rw [projUp, gauss_gn hG hy]
  ext i j
  fin_cases i <;> fin_cases j <;> simp [vecMulVec_apply, Matrix.one_apply, diagonal_apply]

/-! ### Christoffel symbols in a Gaussian chart -/

theorem chr_0 (hG : GaussianChart g ginv U) {y : Pt} (hy : y ∈ U) (b c : Fin 4) :
    christoffel g ginv y 0 b c = (1 / 2) * pd (fun z => g z b c) y 0 := by
  obtain ⟨a0, a1, a2, a3, -, -, -⟩ := gauss_ginv hG hy
  simp only [christoffel, Fin.sum_univ_four, a0, a1, a2, a3, gauss_pd_row0 hG hy]
  ring

theorem chr_p0q (hG : GaussianChart g ginv U) {y : Pt} (hy : y ∈ U) (p q : Fin 4) :
    christoffel g ginv y p 0 q = (1 / 2) * ∑ d, ginv y p d * pd (fun z => g z d q) y 0 := by
  simp only [christoffel, gauss_pd_row0 hG hy, gauss_pd_col0 hG hy, add_zero, sub_zero]

theorem chr_pq0 (hG : GaussianChart g ginv U) {y : Pt} (hy : y ∈ U) (p q : Fin 4) :
    christoffel g ginv y p q 0 = (1 / 2) * ∑ d, ginv y p d * pd (fun z => g z d q) y 0 := by
  simp only [christoffel, gauss_pd_col0 hG hy, zero_add, sub_zero]

theorem chr_symm (hG : GaussianChart g ginv U) {y : Pt} (hy : y ∈ U) (a b c : Fin 4) :
    christoffel g ginv y a b c = christoffel g ginv y a c b := by
  unfold christoffel
  congr 1
  apply Finset.sum_congr rfl
  intro d _
  rw [gauss_pd_symm hG hy b c d]
  ring

theorem gauss_velJet (hG : GaussianChart g ginv U) {y : Pt} (hy : y ∈ U) (a b : Fin 4) :
    velJetMatrix (christoffel g ginv) g (sliceNormal ginv) y a b = christoffel g ginv y 0 a b := by
  simp only [velJetMatrix, Matrix.of_apply, velJet]
  have hL : (fun z => lowerField g (sliceNormal ginv) z b) =ᶠ[𝓝 y]
      fun _ => (if b = 0 then -1 else 0 : ℝ) := by
    filter_upwards [hG.isOpen.mem_nhds hy] with z hz
    simp only [lowerField, sliceNormal_gaussian hG hz, Fin.sum_univ_four]
    rw [← gauss_col0 hG hz b]
    simp
  rw [pd_congr hL, pd_const]
  simp only [lowerField, sliceNormal_gaussian hG hy, Fin.sum_univ_four]
  obtain ⟨a0, -, -, -, b1, b2, b3⟩ := gauss_g hG hy
  simp [a0, b1, b2, b3]

/-- E2: `K_ab = -½ ∂_0 g_ab` in a Gaussian normal chart. -/
theorem extrinsic_gaussian (hG : GaussianChart g ginv U) {y : Pt} (hy : y ∈ U) (a b : Fin 4) :
    extrinsicDown g ginv y a b = -(1 / 2) * pd (fun z => g z a b) y 0 := by
  have hD : ∀ c d, velJetMatrix (christoffel g ginv) g (sliceNormal ginv) y c d =
      (1 / 2) * pd (fun z => g z c d) y 0 := fun c d => by
    rw [gauss_velJet hG hy, chr_0 hG hy]
  simp only [extrinsicDown, Matrix.neg_apply, spatialJet, sliceNormal_gaussian hG hy,
    gauss_projDown hG hy, diagonal_transpose, mul_diagonal, diagonal_mul, hD]
  fin_cases a <;> fin_cases b <;> simp [gauss_pd_row0 hG hy, gauss_pd_col0 hG hy] <;> ring

theorem extrinsicMixed_gauss (hG : GaussianChart g ginv U) {y : Pt} (hy : y ∈ U)
    (p q : Fin 4) : extrinsicMixed g ginv y p q = -christoffel g ginv y p 0 q := by
  simp only [extrinsicMixed, Matrix.mul_apply, extrinsic_gaussian hG hy, chr_p0q hG hy,
    Fin.sum_univ_four]
  ring

theorem extrinsicMixed_gauss' (hG : GaussianChart g ginv U) {y : Pt} (hy : y ∈ U)
    (p q : Fin 4) : extrinsicMixed g ginv y p q = -christoffel g ginv y p q 0 := by
  rw [extrinsicMixed_gauss hG hy, chr_p0q hG hy, chr_pq0 hG hy]

theorem extrinsicMixed_0q (hG : GaussianChart g ginv U) {y : Pt} (hy : y ∈ U) (q : Fin 4) :
    extrinsicMixed g ginv y 0 q = 0 := by
  rw [extrinsicMixed_gauss hG hy, chr_0 hG hy, gauss_pd_row0 hG hy]
  ring

theorem extrinsicMixed_p0 (hG : GaussianChart g ginv U) {y : Pt} (hy : y ∈ U) (p : Fin 4) :
    extrinsicMixed g ginv y p 0 = 0 := by
  rw [extrinsicMixed_gauss hG hy, chr_p0q hG hy]
  simp [gauss_pd_col0 hG hy]

/-! ### Derivatives of `K` at `x` -/

theorem dK_eq (hG : GaussianChart g ginv U) {x : Pt} (hx : x ∈ U) (r p q : Fin 4) :
    pd (fun y => extrinsicMixed g ginv y p q) x r =
      -pd (fun y => christoffel g ginv y p 0 q) x r := by
  have hev : (fun y => extrinsicMixed g ginv y p q) =ᶠ[𝓝 x]
      fun y => -christoffel g ginv y p 0 q := by
    filter_upwards [hG.isOpen.mem_nhds hx] with z hz
    exact extrinsicMixed_gauss hG hz p q
  rw [pd_congr hev, pd_neg (fun y => christoffel g ginv y p 0 q)]

theorem dK_eq' (hG : GaussianChart g ginv U) {x : Pt} (hx : x ∈ U) (r p q : Fin 4) :
    pd (fun y => extrinsicMixed g ginv y p q) x r =
      -pd (fun y => christoffel g ginv y p q 0) x r := by
  have hev : (fun y => extrinsicMixed g ginv y p q) =ᶠ[𝓝 x]
      fun y => -christoffel g ginv y p q 0 := by
    filter_upwards [hG.isOpen.mem_nhds hx] with z hz
    exact extrinsicMixed_gauss' hG hz p q
  rw [pd_congr hev, pd_neg (fun y => christoffel g ginv y p q 0)]

theorem dK_0q (hG : GaussianChart g ginv U) {x : Pt} (hx : x ∈ U) (r q : Fin 4) :
    pd (fun y => extrinsicMixed g ginv y 0 q) x r = 0 := by
  have hev : (fun y => extrinsicMixed g ginv y 0 q) =ᶠ[𝓝 x] fun _ => (0 : ℝ) := by
    filter_upwards [hG.isOpen.mem_nhds hx] with z hz
    exact extrinsicMixed_0q hG hz q
  rw [pd_congr hev, pd_const]

theorem dH_eq (hG : GaussianChart g ginv U) {x : Pt} (hx : x ∈ U)
    (hdiff : ∀ a b c, DifferentiableAt ℝ (fun y => christoffel g ginv y a b c) x) (r : Fin 4) :
    pd (meanCurvature g ginv) x r = ∑ p, pd (fun y => extrinsicMixed g ginv y p p) x r := by
  have hev : meanCurvature g ginv =ᶠ[𝓝 x] fun y => ∑ p, -christoffel g ginv y p 0 p := by
    filter_upwards [hG.isOpen.mem_nhds hx] with z hz
    simp only [meanCurvature, Matrix.trace, Matrix.diag]
    exact Finset.sum_congr rfl (fun p _ => extrinsicMixed_gauss hG hz p p)
  rw [pd_congr hev, pd_sum (f := fun p y => -christoffel g ginv y p 0 p)
    (fun p => (hdiff p 0 p).neg)]
  apply Finset.sum_congr rfl
  intro p _
  rw [dK_eq hG hx, pd_neg (fun y => christoffel g ginv y p 0 p)]

end Gaussian

/-! ### Pure algebraic cores -/

/-- Algebraic core of E3: Gaussian-chart relations between `Γ`, `K` and their partials. -/
theorem codazzi_core (G : Fin 4 → Fin 4 → Fin 4 → ℝ) (dG : Fin 4 → Fin 4 → Fin 4 → Fin 4 → ℝ)
    (K : Fin 4 → Fin 4 → ℝ) (dK : Fin 4 → Fin 4 → Fin 4 → ℝ) (dH : Fin 4 → ℝ)
    (hsym : ∀ a b c, G a b c = G a c b)
    (hG0 : ∀ p q, G p 0 q = -K p q) (hGq0 : ∀ p q, G p q 0 = -K p q)
    (hdGq0 : ∀ r p q, dG r p q 0 = -dK r p q)
    (hK0 : ∀ q, K 0 q = 0) (hKp0 : ∀ p, K p 0 = 0) (hdK0 : ∀ r q, dK r 0 q = 0)
    (hH : ∀ r, dH r = ∑ p, dK r p p) (i : Fin 4) (hi : i ≠ 0) :
    (∑ a, dG a a i 0 - ∑ a, dG i a a 0 + ∑ a, ∑ e, G a a e * G e i 0
        - ∑ a, ∑ e, G a i e * G e a 0) =
      -((∑ b, ∑ p, ∑ q, ∑ r, diagonal ![(0 : ℝ), 1, 1, 1] b p *
          diagonal ![(0 : ℝ), 1, 1, 1] q i * diagonal ![(0 : ℝ), 1, 1, 1] r b *
            (dK r p q + ∑ s, G p r s * K s q - ∑ s, G s r q * K p s)) -
        ∑ r, diagonal ![(0 : ℝ), 1, 1, 1] r i * dH r) := by
  have s21 : ∀ a, G a 2 1 = G a 1 2 := fun a => hsym a 2 1
  have s31 : ∀ a, G a 3 1 = G a 1 3 := fun a => hsym a 3 1
  have s32 : ∀ a, G a 3 2 = G a 2 3 := fun a => hsym a 3 2
  have v1 : ![(0 : ℝ), 1, 1, 1] 1 = 1 := rfl
  have v2 : ![(0 : ℝ), 1, 1, 1] 2 = 1 := rfl
  have v3 : ![(0 : ℝ), 1, 1, 1] 3 = 1 := rfl
  have hi3 : i = 1 ∨ i = 2 ∨ i = 3 := by
    fin_cases i <;> simp_all
  simp only [diagonal_apply, ite_mul, zero_mul, mul_ite, mul_zero, Finset.sum_ite_eq,
    Finset.sum_ite_eq', Finset.mem_univ, if_true]
  rcases hi3 with rfl | rfl | rfl
  all_goals
    simp only [Fin.sum_univ_four, hH, hdGq0, hG0, hGq0, hK0, hKp0, hdK0, s21,
      s31, s32, v1, v2, v3]
    norm_num
    ring

/-- Algebraic core of E7 (spatially homogeneous reduction). -/
theorem homogeneous_core (G : Fin 4 → Fin 4 → Fin 4 → ℝ) (K : Fin 4 → Fin 4 → ℝ)
    (dK : Fin 4 → Fin 4 → Fin 4 → ℝ) (dH : Fin 4 → ℝ)
    (hG00 : ∀ d, G 0 0 d = 0) (hK0 : ∀ d, K 0 d = 0)
    (hdK : ∀ r, r ≠ 0 → ∀ p q, dK r p q = 0) (hdH : ∀ r, r ≠ 0 → dH r = 0)
    (i : Fin 4) (hi : i ≠ 0) :
    (∑ b, ∑ p, ∑ q, ∑ r, diagonal ![(0 : ℝ), 1, 1, 1] b p *
          diagonal ![(0 : ℝ), 1, 1, 1] q i * diagonal ![(0 : ℝ), 1, 1, 1] r b *
            (dK r p q + ∑ s, G p r s * K s q - ∑ s, G s r q * K p s)) -
        ∑ r, diagonal ![(0 : ℝ), 1, 1, 1] r i * dH r =
      ∑ b, ∑ d, G b b d * K d i - ∑ b, ∑ d, G d b i * K b d := by
  have d1 := hdK 1 (by decide)
  have d2 := hdK 2 (by decide)
  have d3 := hdK 3 (by decide)
  have h1 := hdH 1 (by decide)
  have h2 := hdH 2 (by decide)
  have h3 := hdH 3 (by decide)
  have v1 : ![(0 : ℝ), 1, 1, 1] 1 = 1 := rfl
  have v2 : ![(0 : ℝ), 1, 1, 1] 2 = 1 := rfl
  have v3 : ![(0 : ℝ), 1, 1, 1] 3 = 1 := rfl
  have hi3 : i = 1 ∨ i = 2 ∨ i = 3 := by
    fin_cases i <;> simp_all
  simp only [diagonal_apply, ite_mul, zero_mul, mul_ite, mul_zero, Finset.sum_ite_eq,
    Finset.sum_ite_eq', Finset.mem_univ, if_true]
  rcases hi3 with rfl | rfl | rfl
  all_goals
    simp only [Fin.sum_univ_four, d1, d2, d3, h1, h2, h3, hG00, hK0, v1, v2, v3]
    norm_num
    ring

theorem vec0111_ne {a : Fin 4} (ha : a ≠ 0) : ![(0 : ℝ), 1, 1, 1] a = 1 := by
  fin_cases a <;> simp_all

theorem diag0111_col0 (q : Fin 4) : diagonal ![(0 : ℝ), 1, 1, 1] q 0 = 0 := by
  fin_cases q <;> simp [diagonal_apply]

theorem diag0111_row0 (q : Fin 4) : diagonal ![(0 : ℝ), 1, 1, 1] 0 q = 0 := by
  fin_cases q <;> simp [diagonal_apply]

theorem sum_diag0111 (a : Fin 4) (f : Fin 4 → ℝ) :
    ∑ b, diagonal ![(0 : ℝ), 1, 1, 1] a b * f b = ![(0 : ℝ), 1, 1, 1] a * f a := by
  fin_cases a <;> simp [Fin.sum_univ_four, diagonal_apply]

theorem sum_single0 (f : Fin 4 → ℝ) : ∑ c, (Pi.single 0 1 : V) c * f c = f 0 := by
  simp [Fin.sum_univ_four, Pi.single_apply]

section GaussianCodazzi

variable {g ginv : Pt → M} {U : Set Pt}

theorem codazziLHS_unfold (g ginv : Pt → M) (x : Pt) (a : Fin 4) :
    codazziLHS g ginv x a =
      (∑ b, ∑ p, ∑ q, ∑ r, projUp (g x) (sliceNormal ginv x) b p *
        projUp (g x) (sliceNormal ginv x) q a * projUp (g x) (sliceNormal ginv x) r b *
          (pd (fun y => extrinsicMixed g ginv y p q) x r +
            ∑ s, christoffel g ginv x p r s * extrinsicMixed g ginv x s q -
            ∑ s, christoffel g ginv x s r q * extrinsicMixed g ginv x p s)) -
      ∑ r, projUp (g x) (sliceNormal ginv x) r a * pd (meanCurvature g ginv) x r := rfl

theorem codazziLHS_zero (hG : GaussianChart g ginv U) {x : Pt} (hx : x ∈ U) :
    codazziLHS g ginv x 0 = 0 := by
  rw [codazziLHS_unfold, sliceNormal_gaussian hG hx, gauss_projUp hG hx]
  simp [diag0111_col0]

/-- E3: `G_0i = -D_j K^j_i + D_i K` (derived, not assumed). -/
theorem einstein_mixed_gaussian (hG : GaussianChart g ginv U) {x : Pt} (hx : x ∈ U)
    (hdiff : ∀ a b c, DifferentiableAt ℝ (fun y => christoffel g ginv y a b c) x)
    (i : Fin 4) (hi : i ≠ 0) :
    einstein (christoffel g ginv) g ginv x 0 i = -codazziLHS g ginv x i := by
  rw [einstein, hG.g0i x hx i hi, mul_zero, sub_zero, codazziLHS_unfold,
    sliceNormal_gaussian hG hx, gauss_projUp hG hx]
  unfold ricci
  exact codazzi_core (christoffel g ginv x)
    (fun r a b c => pd (fun y => christoffel g ginv y a b c) x r)
    (extrinsicMixed g ginv x) (fun r p q => pd (fun y => extrinsicMixed g ginv y p q) x r)
    (fun r => pd (meanCurvature g ginv) x r)
    (chr_symm hG hx)
    (fun p q => by simp only [extrinsicMixed_gauss hG hx p q, neg_neg])
    (fun p q => by simp only [extrinsicMixed_gauss' hG hx p q, neg_neg])
    (fun r p q => by simp only [dK_eq' hG hx r p q, neg_neg])
    (extrinsicMixed_0q hG hx) (extrinsicMixed_p0 hG hx) (dK_0q hG hx) (dH_eq hG hx hdiff) i hi

/-- E4: contracted Codazzi in projector form, `D_b K^b_a - D_a K = -h_a^b n^c R_cb`. -/
theorem contracted_codazzi_gaussian (hG : GaussianChart g ginv U) {x : Pt} (hx : x ∈ U)
    (hdiff : ∀ a b c, DifferentiableAt ℝ (fun y => christoffel g ginv y a b c) x) (a : Fin 4) :
    codazziLHS g ginv x a =
      -∑ b, projDown (g x) (sliceNormal ginv x) a b *
        ∑ c, sliceNormal ginv x c * ricci (christoffel g ginv) x c b := by
  by_cases ha : a = 0
  · subst ha
    rw [codazziLHS_zero hG hx, sliceNormal_gaussian hG hx, gauss_projDown hG hx]
    simp [diag0111_row0]
  · have hE := einstein_mixed_gaussian hG hx hdiff a ha
    rw [einstein, hG.g0i x hx a ha, mul_zero, sub_zero] at hE
    rw [sliceNormal_gaussian hG hx, gauss_projDown hG hx]
    simp only [sum_single0]
    rw [sum_diag0111, vec0111_ne ha, one_mul]
    linarith

theorem normalFlux_gauss (hG : GaussianChart g ginv U) {y : Pt} (hy : y ∈ U) (T : M)
    (a : Fin 4) :
    normalFlux (g y) (Pi.single 0 1) T a = -(![(0 : ℝ), 1, 1, 1] a * T a 0) := by
  rw [normalFlux, gauss_projDown hG hy]
  simp [mulVec, dotProduct, Fin.sum_univ_four, diagonal_mul]

/-- E5: momentum constraint `D_b K^b_a - D_a K = κ J_a` from an explicit Einstein hypothesis. -/
theorem momentum_constraint (hG : GaussianChart g ginv U) {x : Pt} (hx : x ∈ U)
    (hdiff : ∀ a b c, DifferentiableAt ℝ (fun y => christoffel g ginv y a b c) x)
    (κ Λ : ℝ) (T : M) (hT : Tᵀ = T)
    (hE : ∀ b d, einstein (christoffel g ginv) g ginv x b d + Λ * g x b d = κ * T b d)
    (a : Fin 4) :
    codazziLHS g ginv x a = κ * normalFlux (g x) (sliceNormal ginv x) T a := by
  rw [sliceNormal_gaussian hG hx, normalFlux_gauss hG hx]
  by_cases ha : a = 0
  · subst ha
    rw [codazziLHS_zero hG hx]
    simp
  · have h1 := einstein_mixed_gaussian hG hx hdiff a ha
    have h2 := hE 0 a
    rw [hG.g0i x hx a ha, mul_zero, add_zero, h1] at h2
    have hTs : T a 0 = T 0 a := by
      have := congrFun (congrFun hT 0) a
      simpa [Matrix.transpose_apply] using this
    rw [hTs, vec0111_ne ha]
    linear_combination -h2

/-- E6: Codazzi + Einstein + single perfect fluid: the extrinsic-curvature combination fixes the
tilt through the vector and scalar inverses. -/
theorem codazzi_perfect_fluid_tilt (hG : GaussianChart g ginv U) {x : Pt} (hx : x ∈ U)
    (hdiff : ∀ a b c, DifferentiableAt ℝ (fun y => christoffel g ginv y a b c) x)
    {κ : ℝ} (hκ : κ ≠ 0) (Λ : ℝ) {w : ℝ} (hw : 0 < w) (p γ : ℝ) (β : V)
    (hβ : sliceNormal ginv x ⬝ᵥ (g x *ᵥ β) = 0)
    (hu : (γ • (sliceNormal ginv x + β)) ⬝ᵥ (g x *ᵥ (γ • (sliceNormal ginv x + β))) = -1)
    (hpos : β ≠ 0 → 0 < β ⬝ᵥ (g x *ᵥ β))
    (hE : ∀ b d, einstein (christoffel g ginv) g ginv x b d + Λ * g x b d =
      κ * perfectFluid (g x) w p (γ • (sliceNormal ginv x + β)) b d) :
    codazziLHS g ginv x = (κ * (w * γ ^ 2)) • (g x *ᵥ β) ∧
    betaVector (ginv x) w (κ⁻¹ • codazziLHS g ginv x) = g x *ᵥ β ∧
    betaOfRatio (fluxNorm (ginv x) (κ⁻¹ • codazziLHS g ginv x) / w) =
      Real.sqrt (β ⬝ᵥ (g x *ᵥ β)) := by
  have hg := hG.symm x hx
  have hinv := hG.inv x hx
  have hn : sliceNormal ginv x ⬝ᵥ (g x *ᵥ sliceNormal ginv x) = -1 :=
    (sliceNormal_unit hinv (by rw [(gauss_ginv hG hx).1]; norm_num)).1
  have hT := perfectFluid_symm hg w p (γ • (sliceNormal ginv x + β))
  have hC : codazziLHS g ginv x =
      κ • normalFlux (g x) (sliceNormal ginv x) (perfectFluid (g x) w p (γ • (sliceNormal ginv x + β))) := by
    funext a
    rw [momentum_constraint hG hx hdiff κ Λ _ hT hE a]
    rfl
  have hJ : κ⁻¹ • codazziLHS g ginv x =
      normalFlux (g x) (sliceNormal ginv x) (perfectFluid (g x) w p (γ • (sliceNormal ginv x + β))) := by
    rw [hC, inv_smul_smul₀ hκ]
  have hβnn : 0 ≤ β ⬝ᵥ (g x *ᵥ β) := by
    by_cases hb : β = 0
    · rw [hb]; simp
    · exact (hpos hb).le
  refine ⟨?_, ?_, ?_⟩
  · rw [hC, normalFlux_perfectFluid hg hn hβ, smul_smul]
  · rw [hJ]
    exact (vector_flux_inverse hg hinv hn hβ hu hw hpos p).1
  · rw [hJ]
    exact scalar_flux_inverse hg hinv hn hβ hu hw hβnn p

/-- E7: chart analogue of the implementation's homogeneous-frame einsum
`Γ[b,b,d] K[d,a] - Γ[d,b,a] K[b,d]` when all spatial partials of `K^p_q` and `K` vanish at `x`. -/
theorem codazzi_homogeneous_reduction (hG : GaussianChart g ginv U) {x : Pt} (hx : x ∈ U)
    (hK : ∀ r, r ≠ 0 → ∀ p q, pd (fun y => extrinsicMixed g ginv y p q) x r = 0)
    (hH : ∀ r, r ≠ 0 → pd (meanCurvature g ginv) x r = 0) (i : Fin 4) (hi : i ≠ 0) :
    codazziLHS g ginv x i =
      ∑ b, ∑ d, christoffel g ginv x b b d * extrinsicMixed g ginv x d i -
        ∑ b, ∑ d, christoffel g ginv x d b i * extrinsicMixed g ginv x b d := by
  rw [codazziLHS_unfold, sliceNormal_gaussian hG hx, gauss_projUp hG hx]
  exact homogeneous_core (christoffel g ginv x) (extrinsicMixed g ginv x)
    (fun r p q => pd (fun y => extrinsicMixed g ginv y p q) x r)
    (fun r => pd (meanCurvature g ginv) x r)
    (fun d => by
      have h1 := extrinsicMixed_gauss hG hx 0 d
      rw [extrinsicMixed_0q hG hx] at h1
      linarith)
    (extrinsicMixed_0q hG hx) hK hH i hi

end GaussianCodazzi

/-- E8: non-vacuity: the Minkowski chart is Gaussian, has a differentiable connection, and
satisfies the Einstein hypothesis of E5 with `T = 0`, `Λ = 0`. -/
theorem minkowski_codazzi_witness (κ : ℝ) (x : Pt) :
    GaussianChart gMink gMink Set.univ ∧
    (∀ a b c, DifferentiableAt ℝ (fun y => christoffel gMink gMink y a b c) x) ∧
    (∀ b d, einstein (christoffel gMink gMink) gMink gMink x b d + 0 * gMink x b d =
      κ * (0 : M) b d) := by
  have hΓ : christoffel gMink gMink = fun _ _ _ _ => 0 := by
    funext y a b c
    simp [christoffel, pd, gMink]
  refine ⟨⟨isOpen_univ, fun _ _ => eta_symm, fun _ _ => eta_mul_eta, fun _ _ => by
    simp [gMink, PortCas01.eta], fun _ _ i hi => by
      fin_cases i <;> simp_all [gMink, PortCas01.eta]⟩, ?_, ?_⟩
  · intro a b c
    rw [hΓ]
    exact differentiableAt_const _
  · intro b d
    rw [hΓ]
    simp [einstein, scalarCurvature, ricci, pd]

end PORTCAS04FluxVectorCodazzi
