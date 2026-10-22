import Mathlib
import VelocityJetDecomposition

/-!
# R191-A: canonical Gauss object of a rotating (non-integrable) rest bundle

Scope: pointwise / chart level.  Everything is evaluated at one event, either in an
adapted orthonormal frame `e_0 = u`, `e_i` spatial (`η = diag(-1,1,1,1)`), or in a
chart with the reviewed P03-A projector algebra (imported unchanged).

Conventions (recovered, see `SOURCE_RECOVERY.md`):
* frame connection coefficients `γ A B C = ⟨e_A, ∇_{e_B} e_C⟩`; metric compatibility
  `γ A B C = - γ C B A` (`Compat`);
* torsion-free bracket `[e_C,e_D] = Σ_E bracket γ E C D • e_E`;
* Riemann `riem γ dγ A B C D = ⟨e_A, R(e_C,e_D) e_B⟩` from the Cartan second structure
  equation, `dγ C A D B = e_C(γ A D B)` is independent jet data;
* jet `jet γ B C = D_BC = ∇_B u_C = γ C B 0` (derivative index first, as P03-A and
  `htt/obsstat/egs3_king_ellis_frame.py:195`);
* rest-bundle connection `∇^H_X Z = h ∇_X Z`, coefficient matrices `restA γ C`;
* `curvForm` = curvature 2-form of a rest-bundle connection, evaluated with the FULL
  bracket; its vertical (`E = 0`) bracket component is the non-integrability term
  `bracket γ 0 k l = 2 ω_kl`.
* `sliceForm` drops that vertical bracket component.  It is a contrast object only and is
  NOT called slice curvature or curvature of an orthogonal metric: for `ω ≠ 0` no
  `u`-orthogonal slice exists, and `sliceForm` is shown to be frame-convention dependent.

The fibre gauge theorem (`curvForm_gauge`) works on 2-jets at the event: `O = g(p)`,
`l C = e_C(g)(p)`, `ν C D = e_C(e_D(g))(p)` for an `O(3)`-valued change `g` of the
rest-bundle triad; the transformed data `gaugeA`, `gaugeDA` are the Leibniz expansions of
`gᵀ A g + gᵀ dg`.  The 2-form slots are evaluated on a fixed direction frame.
-/

open Matrix
open scoped Matrix

namespace R191ARotatingRestGauss

open PORTCAS03VelocityJetDecomposition

/-- Rest-bundle (fibre) endomorphisms in an orthonormal spatial triad. -/
abbrev M3 := Matrix (Fin 3) (Fin 3) ℝ

/-! ## Part A. Exterior (Cartan) form of the rest-bundle curvature -/

/-- Curvature 2-form `F(e_C,e_D) = e_C(A_D) - e_D(A_C) + [A_C,A_D] - A([e_C,e_D])` with the
full bracket `[e_C,e_D] = Σ_E c E C D • e_E`. -/
def curvForm (A : Fin 4 → M3) (dA : Fin 4 → Fin 4 → M3) (c : Fin 4 → Fin 4 → Fin 4 → ℝ)
    (C D : Fin 4) : M3 :=
  dA C D - dA D C + (A C * A D - A D * A C) - ∑ E, c E C D • A E

/-- Contrast object: the same expression with the vertical (`E = 0`) bracket component
dropped.  Not a curvature of the rest-bundle connection when that component is nonzero. -/
def sliceForm (A : Fin 4 → M3) (dA : Fin 4 → Fin 4 → M3) (c : Fin 4 → Fin 4 → Fin 4 → ℝ)
    (C D : Fin 4) : M3 :=
  dA C D - dA D C + (A C * A D - A D * A C) - ∑ E : Fin 3, c E.succ C D • A E.succ

/-- Exterior derivation with the non-integrability term isolated. -/
theorem curvForm_eq_sliceForm_sub (A : Fin 4 → M3) (dA : Fin 4 → Fin 4 → M3)
    (c : Fin 4 → Fin 4 → Fin 4 → ℝ) (C D : Fin 4) :
    curvForm A dA c C D = sliceForm A dA c C D - c 0 C D • A 0 := by
  simp only [curvForm, sliceForm, Fin.sum_univ_succ (n := 3)]
  abel

/-! ## Part B. Fibre-frame change: invariant content vs convention-dependent content -/

/-- Transformed connection coefficients at the event: `gᵀ A_C g + gᵀ e_C(g)`. -/
def gaugeA (O : M3) (l A : Fin 4 → M3) (C : Fin 4) : M3 :=
  Oᵀ * A C * O + Oᵀ * l C

/-- Leibniz expansion of `e_C (gᵀ A_D g + gᵀ e_D(g))` at the event. -/
def gaugeDA (O : M3) (l : Fin 4 → M3) (ν : Fin 4 → Fin 4 → M3) (A : Fin 4 → M3)
    (dA : Fin 4 → Fin 4 → M3) (C D : Fin 4) : M3 :=
  (l C)ᵀ * A D * O + Oᵀ * dA C D * O + Oᵀ * A D * l C + (l C)ᵀ * l D + Oᵀ * ν C D

theorem ring_core {R : Type*} [Ring R] (O P aC aD dCD dDC lC lD nCD nDC SA Sl : R)
    (hOP : O * P = 1) :
    (-(P * lC * P) * aD * O + P * dCD * O + P * aD * lC + -(P * lC * P) * lD + P * nCD)
      - (-(P * lD * P) * aC * O + P * dDC * O + P * aC * lD + -(P * lD * P) * lC + P * nDC)
      + ((P * aC * O + P * lC) * (P * aD * O + P * lD)
          - (P * aD * O + P * lD) * (P * aC * O + P * lC))
      - (P * SA * O + P * Sl)
    = P * (dCD - dDC + (aC * aD - aD * aC) - SA) * O + P * (nCD - nDC - Sl) := by
  have h1 : (P * aC * O + P * lC) * (P * aD * O + P * lD)
      = P * aC * (O * P) * aD * O + P * aC * (O * P) * lD + P * lC * P * aD * O
        + P * lC * P * lD := by noncomm_ring
  have h2 : (P * aD * O + P * lD) * (P * aC * O + P * lC)
      = P * aD * (O * P) * aC * O + P * aD * (O * P) * lC + P * lD * P * aC * O
        + P * lD * P * lC := by noncomm_ring
  rw [h1, h2, hOP]
  noncomm_ring

theorem transpose_of_orth_jet {O L : M3} (hO : O * Oᵀ = 1) (hL : Lᵀ * O + Oᵀ * L = 0) :
    Lᵀ = -(Oᵀ * L * Oᵀ) := by
  have h : Lᵀ = (Lᵀ * O + Oᵀ * L) * Oᵀ - Oᵀ * L * Oᵀ := by
    rw [Matrix.add_mul, Matrix.mul_assoc, hO, Matrix.mul_one]; abel
  rw [h, hL, Matrix.zero_mul, zero_sub]

theorem sum_gaugeA (O : M3) (l A : Fin 4 → M3) (w : Fin 4 → ℝ) :
    ∑ E, w E • gaugeA O l A E = Oᵀ * (∑ E, w E • A E) * O + Oᵀ * (∑ E, w E • l E) := by
  rw [Finset.mul_sum, Finset.sum_mul, Finset.mul_sum, ← Finset.sum_add_distrib]
  refine Finset.sum_congr rfl fun E _ => ?_
  simp only [gaugeA, smul_add, Matrix.mul_smul, Matrix.smul_mul]

/-- Invariant content: the rest-bundle curvature 2-form transforms homogeneously under an
`O(3)` change of the rest-bundle triad (2-jet at the event). -/
theorem curvForm_gauge (O : M3) (l A : Fin 4 → M3) (ν dA : Fin 4 → Fin 4 → M3)
    (c : Fin 4 → Fin 4 → Fin 4 → ℝ) (hO : O * Oᵀ = 1)
    (hl : ∀ C, (l C)ᵀ * O + Oᵀ * l C = 0)
    (hν : ∀ C D, ν C D - ν D C = ∑ E, c E C D • l E) (C D : Fin 4) :
    curvForm (gaugeA O l A) (gaugeDA O l ν A dA) c C D = Oᵀ * curvForm A dA c C D * O := by
  have core := ring_core O Oᵀ (A C) (A D) (dA C D) (dA D C) (l C) (l D) (ν C D) (ν D C)
    (∑ E, c E C D • A E) (∑ E, c E C D • l E) hO
  rw [hν C D, sub_self, mul_zero, add_zero] at core
  unfold curvForm gaugeDA
  rw [sum_gaugeA O l A (fun E => c E C D), transpose_of_orth_jet hO (hl C),
    transpose_of_orth_jet hO (hl D)]
  unfold gaugeA
  exact core

/-- Convention-dependent content: the slice-type expression picks up exactly
`c 0 C D • Oᵀ (e_0 g)`, the vertical bracket times the triad rotation rate along `u`. -/
theorem sliceForm_gauge (O : M3) (l A : Fin 4 → M3) (ν dA : Fin 4 → Fin 4 → M3)
    (c : Fin 4 → Fin 4 → Fin 4 → ℝ) (hO : O * Oᵀ = 1)
    (hl : ∀ C, (l C)ᵀ * O + Oᵀ * l C = 0)
    (hν : ∀ C D, ν C D - ν D C = ∑ E, c E C D • l E) (C D : Fin 4) :
    sliceForm (gaugeA O l A) (gaugeDA O l ν A dA) c C D
      = Oᵀ * sliceForm A dA c C D * O + c 0 C D • (Oᵀ * l 0) := by
  have h1 := curvForm_eq_sliceForm_sub (gaugeA O l A) (gaugeDA O l ν A dA) c C D
  have h2 := curvForm_eq_sliceForm_sub A dA c C D
  rw [curvForm_gauge O l A ν dA c hO hl hν C D] at h1
  have e1 : sliceForm (gaugeA O l A) (gaugeDA O l ν A dA) c C D
      = Oᵀ * curvForm A dA c C D * O + c 0 C D • gaugeA O l A 0 :=
    sub_eq_iff_eq_add.mp h1.symm
  rw [e1, h2]
  simp only [gaugeA, Matrix.mul_sub, Matrix.sub_mul, Matrix.mul_smul, Matrix.smul_mul, smul_add]
  abel

/-- With vanishing vertical bracket the slice-type expression is covariant too. -/
theorem sliceForm_gauge_of_vertical_zero (O : M3) (l A : Fin 4 → M3) (ν dA : Fin 4 → Fin 4 → M3)
    (c : Fin 4 → Fin 4 → Fin 4 → ℝ) (hO : O * Oᵀ = 1)
    (hl : ∀ C, (l C)ᵀ * O + Oᵀ * l C = 0)
    (hν : ∀ C D, ν C D - ν D C = ∑ E, c E C D • l E) (C D : Fin 4) (h0 : c 0 C D = 0) :
    sliceForm (gaugeA O l A) (gaugeDA O l ν A dA) c C D = Oᵀ * sliceForm A dA c C D * O := by
  rw [sliceForm_gauge O l A ν dA c hO hl hν C D, h0, zero_smul, add_zero]

/-! ## Part C. Adapted orthonormal frame: exterior object vs projected tensor -/

def etaF (A : Fin 4) : ℝ := if A = 0 then -1 else 1

@[simp] theorem etaF_zero : etaF 0 = -1 := by simp [etaF]

@[simp] theorem etaF_succ (m : Fin 3) : etaF m.succ = 1 := by simp [etaF, Fin.succ_ne_zero]

/-- Metric compatibility of the frame connection coefficients. -/
def Compat (γ : Fin 4 → Fin 4 → Fin 4 → ℝ) : Prop := ∀ A B C, γ A B C = -γ C B A

/-- Torsion-free bracket components `[e_C,e_D] = Σ_E bracket γ E C D • e_E`. -/
def bracket (γ : Fin 4 → Fin 4 → Fin 4 → ℝ) (E C D : Fin 4) : ℝ :=
  etaF E * (γ E C D - γ E D C)

/-- Spacetime Riemann `⟨e_A, R(e_C,e_D) e_B⟩` (Cartan second structure equation). -/
def riem (γ : Fin 4 → Fin 4 → Fin 4 → ℝ) (dγ : Fin 4 → Fin 4 → Fin 4 → Fin 4 → ℝ)
    (A B C D : Fin 4) : ℝ :=
  dγ C A D B - dγ D A C B + ∑ E, etaF E * (γ A C E * γ E D B - γ A D E * γ E C B)
    - ∑ E, bracket γ E C D * γ A E B

/-- Frame velocity jet `D_BC = ∇_B u_C = ⟨e_C, ∇_{e_B} u⟩` (derivative index first). -/
def jet (γ : Fin 4 → Fin 4 → Fin 4 → ℝ) : Matrix (Fin 4) (Fin 4) ℝ :=
  Matrix.of fun B C => γ C B 0

/-- Rest-bundle connection coefficients `(A_C)_ij = ⟨e_i, h∇_{e_C} e_j⟩`. -/
def restA (γ : Fin 4 → Fin 4 → Fin 4 → ℝ) : Fin 4 → M3 :=
  fun C => Matrix.of fun i j => γ i.succ C j.succ

def restDA (dγ : Fin 4 → Fin 4 → Fin 4 → Fin 4 → ℝ) : Fin 4 → Fin 4 → M3 :=
  fun C D => Matrix.of fun i j => dγ C i.succ D j.succ

/-- Canonical rest-bundle curvature (exterior derivation, full bracket). -/
def restCurv (γ : Fin 4 → Fin 4 → Fin 4 → ℝ) (dγ : Fin 4 → Fin 4 → Fin 4 → Fin 4 → ℝ)
    (C D : Fin 4) : M3 :=
  curvForm (restA γ) (restDA dγ) (bracket γ) C D

/-- Slice-type contrast expression (vertical bracket dropped). -/
def sliceCurv (γ : Fin 4 → Fin 4 → Fin 4 → ℝ) (dγ : Fin 4 → Fin 4 → Fin 4 → Fin 4 → ℝ)
    (C D : Fin 4) : M3 :=
  sliceForm (restA γ) (restDA dγ) (bracket γ) C D

/-- Spatial jet `V_kl` in the frame. -/
def restV (γ : Fin 4 → Fin 4 → Fin 4 → ℝ) : M3 := Matrix.of fun k l => jet γ k.succ l.succ

/-- Frame vorticity `ω_kl = (V_kl - V_lk)/2` (derivative-first). -/
noncomputable def restOmega (γ : Fin 4 → Fin 4 → Fin 4 → ℝ) : M3 :=
  Matrix.of fun k l => (restV γ k l - restV γ l k) / 2

/-- Non-integrability: the vertical bracket of two spatial frame vectors is `2 ω_kl`. -/
theorem bracket_vertical {γ : Fin 4 → Fin 4 → Fin 4 → ℝ} (hc : Compat γ) (k l : Fin 3) :
    bracket γ 0 k.succ l.succ = 2 * restOmega γ k l := by
  have h1 := hc 0 k.succ l.succ
  have h2 := hc 0 l.succ k.succ
  simp only [bracket, etaF_zero, restOmega, restV, jet, Matrix.of_apply, h1, h2]
  ring

/-- Exterior derivation of the rest-bundle curvature with the `ω` term explicit. -/
theorem restCurv_exterior {γ : Fin 4 → Fin 4 → Fin 4 → ℝ} (hc : Compat γ)
    (dγ : Fin 4 → Fin 4 → Fin 4 → Fin 4 → ℝ) (k l : Fin 3) :
    restCurv γ dγ k.succ l.succ
      = sliceCurv γ dγ k.succ l.succ - (2 * restOmega γ k l) • restA γ 0 := by
  rw [restCurv, sliceCurv, curvForm_eq_sliceForm_sub, bracket_vertical hc]

/-- Gauss equation in the frame: exterior object = projected Riemann − `V_ki V_lj + V_li V_kj`. -/
theorem gauss_frame {γ : Fin 4 → Fin 4 → Fin 4 → ℝ} (hc : Compat γ)
    (dγ : Fin 4 → Fin 4 → Fin 4 → Fin 4 → ℝ) (i j k l : Fin 3) :
    restCurv γ dγ k.succ l.succ i j
      = riem γ dγ i.succ j.succ k.succ l.succ - restV γ k i * restV γ l j
        + restV γ l i * restV γ k j := by
  have h1 := hc 0 l.succ j.succ
  have h2 := hc 0 k.succ j.succ
  simp only [restCurv, curvForm, riem, restA, restDA, restV, jet, Matrix.sub_apply,
    Matrix.add_apply, Matrix.mul_apply, Matrix.of_apply, Matrix.smul_apply,
    smul_eq_mul, Fin.sum_univ_succ, Fin.sum_univ_zero, Matrix.zero_apply, etaF_zero, etaF_succ,
    h1, h2]
  ring

/-- Frame scalars. -/
def restScalar (γ : Fin 4 → Fin 4 → Fin 4 → ℝ) (dγ : Fin 4 → Fin 4 → Fin 4 → Fin 4 → ℝ) : ℝ :=
  ∑ k : Fin 3, ∑ l : Fin 3, restCurv γ dγ k.succ l.succ k l

def projRiemFrame (γ : Fin 4 → Fin 4 → Fin 4 → ℝ) (dγ : Fin 4 → Fin 4 → Fin 4 → Fin 4 → ℝ) : ℝ :=
  ∑ k : Fin 3, ∑ l : Fin 3, riem γ dγ k.succ l.succ k.succ l.succ

def traceFrame (V : M3) : ℝ := ∑ k, V k k

def sameFrame (V : M3) : ℝ := ∑ k, ∑ l, V k l * V k l

def transFrame (V : M3) : ℝ := ∑ k, ∑ l, V k l * V l k

theorem restScalar_gauss {γ : Fin 4 → Fin 4 → Fin 4 → ℝ} (hc : Compat γ)
    (dγ : Fin 4 → Fin 4 → Fin 4 → Fin 4 → ℝ) :
    restScalar γ dγ
      = projRiemFrame γ dγ - traceFrame (restV γ) ^ 2 + transFrame (restV γ) := by
  simp only [restScalar, gauss_frame hc, projRiemFrame, traceFrame, transFrame,
    Fin.sum_univ_succ, Fin.sum_univ_zero]
  ring

theorem same_sub_trans_frame (V : M3) :
    sameFrame V - transFrame V
      = 2 * sameFrame (Matrix.of fun k l => (V k l - V l k) / 2) := by
  simp only [sameFrame, transFrame, Matrix.of_apply, Fin.sum_univ_succ, Fin.sum_univ_zero]
  ring

/-! ## Part D. Chart tensor derivation (P03-A objects) and agreement -/

/-- `h^{mk} h^{nl} R_{mnkl}`. -/
def projRiemTrace (hU : Matrix (Fin 4) (Fin 4) ℝ) (R : Fin 4 → Fin 4 → Fin 4 → Fin 4 → ℝ) : ℝ :=
  ∑ m, ∑ n, ∑ k, ∑ l, hU m k * (hU n l * R m n k l)

/-- Source `_proj_riemann_trace`, SAME-ORDER Gauss product `V_ab V^ab`. -/
def gaussSame (g ginv : Matrix (Fin 4) (Fin 4) ℝ) (u : Fin 4 → ℝ) (D : Matrix (Fin 4) (Fin 4) ℝ)
    (R : Fin 4 → Fin 4 → Fin 4 → Fin 4 → ℝ) : ℝ :=
  projRiemTrace (hUp ginv u) R
    + metricInner (hUp ginv u) (spatialJet g u D) (spatialJet g u D)
    - contract (hUp ginv u) (spatialJet g u D) ^ 2

/-- TRANSPOSED Gauss product `V_ab V^ba`. -/
def gaussTrans (g ginv : Matrix (Fin 4) (Fin 4) ℝ) (u : Fin 4 → ℝ) (D : Matrix (Fin 4) (Fin 4) ℝ)
    (R : Fin 4 → Fin 4 → Fin 4 → Fin 4 → ℝ) : ℝ :=
  projRiemTrace (hUp ginv u) R
    + metricInner (hUp ginv u) (spatialJet g u D) (spatialJet g u D)ᵀ
    - contract (hUp ginv u) (spatialJet g u D) ^ 2

/-- Projected 4-index Gauss tensor `h h h h R_pqrs − V_ca V_db + V_da V_cb`. -/
def gaussTensor (g : Matrix (Fin 4) (Fin 4) ℝ) (u : Fin 4 → ℝ) (D : Matrix (Fin 4) (Fin 4) ℝ)
    (R : Fin 4 → Fin 4 → Fin 4 → Fin 4 → ℝ) (a b c d : Fin 4) : ℝ :=
  (∑ p, ∑ q, ∑ r, ∑ s, projDown g u a p * (projDown g u b q * (projDown g u c r
      * (projDown g u d s * R p q r s))))
    - spatialJet g u D c a * spatialJet g u D d b + spatialJet g u D d a * spatialJet g u D c b

theorem hUp_symm {ginv : Matrix (Fin 4) (Fin 4) ℝ} (hginv : ginvᵀ = ginv) (u : Fin 4 → ℝ) :
    (hUp ginv u)ᵀ = hUp ginv u := by
  simp [hUp, transpose_add, transpose_vecMulVec, hginv]

theorem metricInner_sym_add_skew {H S W : Matrix (Fin 4) (Fin 4) ℝ} (hH : Hᵀ = H)
    (hS : Sᵀ = S) (hW : Wᵀ = -W) :
    metricInner H (S + W) (S + W) - metricInner H (S + W) (S + W)ᵀ
      = 2 * metricInner H W W := by
  have h0 := metricInner_sym_skew hH hS hW
  unfold metricInner at h0 ⊢
  simp only [transpose_add, transpose_neg, neg_neg, hS, hW, Matrix.mul_add,
    Matrix.add_mul, Matrix.mul_neg, trace_add, trace_neg] at h0 ⊢
  linarith

theorem metricInner_same_sub_trans {H : Matrix (Fin 4) (Fin 4) ℝ} (hH : Hᵀ = H)
    (V : Matrix (Fin 4) (Fin 4) ℝ) :
    metricInner H V V - metricInner H V Vᵀ = 2 * metricInner H (skewPart V) (skewPart V) := by
  have hS : (symPart V)ᵀ = symPart V := by
    ext a b; simp [symPart]; ring
  have hW : (skewPart V)ᵀ = -skewPart V := by
    ext a b; simp [skewPart]; ring
  have hV : V = symPart V + skewPart V := by
    ext a b; simp [symPart, skewPart]; ring
  have key := metricInner_sym_add_skew hH hS hW
  rw [← hV] at key
  exact key

/-- Ordering theorem (any symmetric `ginv`): same-order minus transposed is `2 ω_ab ω^ab`. -/
theorem gaussSame_sub_gaussTrans {g ginv : Matrix (Fin 4) (Fin 4) ℝ} (hginv : ginvᵀ = ginv)
    (u : Fin 4 → ℝ) (D : Matrix (Fin 4) (Fin 4) ℝ) (R : Fin 4 → Fin 4 → Fin 4 → Fin 4 → ℝ) :
    gaussSame g ginv u D R - gaussTrans g ginv u D R
      = 2 * metricInner (hUp ginv u) (vorticity 1 g u D) (vorticity 1 g u D) := by
  have h := metricInner_same_sub_trans (hUp_symm hginv u) (spatialJet g u D)
  simp only [gaussSame, gaussTrans, vorticity, one_smul]
  linarith

/-! ### Frame evaluation of the P03-A objects -/

/-- Spatial projector in the adapted frame: `diag(0,1,1,1)`. -/
def Pi4 : Matrix (Fin 4) (Fin 4) ℝ := Matrix.diagonal ![0, 1, 1, 1]

theorem hUp_eta_e0 : hUp PortCas01.eta PortCas01.e0 = Pi4 := by
  ext a b
  fin_cases a <;> fin_cases b <;> simp [hUp, PortCas01.eta, PortCas01.e0, vecMulVec, Pi4]

theorem projDown_eta_e0 : projDown PortCas01.eta PortCas01.e0 = Pi4 := by
  ext a b
  fin_cases a <;> fin_cases b <;>
    simp [projDown, PortCas01.eta, PortCas01.e0, vecMulVec, Pi4, mulVec, dotProduct,
      Fin.sum_univ_succ]

theorem spatialJet_eta_e0 (D : Matrix (Fin 4) (Fin 4) ℝ) :
    spatialJet PortCas01.eta PortCas01.e0 D = Pi4 * D * Pi4 := by
  rw [spatialJet, projDown_eta_e0, Pi4, diagonal_transpose]

@[simp] theorem vec111_apply (k : Fin 3) : (![1, 1, 1] : Fin 3 → ℝ) k = 1 := by
  fin_cases k <;> rfl

theorem PiDPi_apply (D : Matrix (Fin 4) (Fin 4) ℝ) (a b : Fin 4) :
    (Pi4 * D * Pi4) a b = ![0, 1, 1, 1] a * D a b * ![0, 1, 1, 1] b := by
  rw [Pi4, mul_diagonal, diagonal_mul]

theorem metricInner_Pi4 (X Y : Matrix (Fin 4) (Fin 4) ℝ) :
    metricInner Pi4 X Y = ∑ k : Fin 3, ∑ l : Fin 3, X k.succ l.succ * Y k.succ l.succ := by
  simp [metricInner, Pi4, Matrix.trace, Matrix.mul_apply, Fin.sum_univ_succ]

theorem contract_Pi4 (X : Matrix (Fin 4) (Fin 4) ℝ) :
    contract Pi4 X = ∑ k : Fin 3, X k.succ k.succ := by
  simp [contract, Pi4, diagonal_apply, Fin.sum_univ_succ]

theorem projRiemTrace_Pi4 (R : Fin 4 → Fin 4 → Fin 4 → Fin 4 → ℝ) :
    projRiemTrace Pi4 R = ∑ k : Fin 3, ∑ l : Fin 3, R k.succ l.succ k.succ l.succ := by
  simp [projRiemTrace, Pi4, diagonal_apply, Fin.sum_univ_succ]

theorem vorticity_frame_apply (γ : Fin 4 → Fin 4 → Fin 4 → ℝ) (k l : Fin 3) :
    vorticity 1 PortCas01.eta PortCas01.e0 (jet γ) k.succ l.succ = restOmega γ k l := by
  simp only [vorticity, skewPart, one_smul, spatialJet_eta_e0, Matrix.smul_apply,
    Matrix.sub_apply, Matrix.transpose_apply, PiDPi_apply, restOmega, restV, Matrix.of_apply,
    smul_eq_mul]
  simp
  ring

theorem metricInner_omega_frame (γ : Fin 4 → Fin 4 → Fin 4 → ℝ) :
    metricInner (hUp PortCas01.eta PortCas01.e0) (vorticity 1 PortCas01.eta PortCas01.e0 (jet γ))
      (vorticity 1 PortCas01.eta PortCas01.e0 (jet γ)) = sameFrame (restOmega γ) := by
  rw [hUp_eta_e0, metricInner_Pi4]
  simp only [vorticity_frame_apply, sameFrame]

/-- Two derivations agree: the exterior rest-bundle scalar equals the chart tensor
expression with the TRANSPOSED Gauss product. -/
theorem exterior_eq_tensor {γ : Fin 4 → Fin 4 → Fin 4 → ℝ} (hc : Compat γ)
    (dγ : Fin 4 → Fin 4 → Fin 4 → Fin 4 → ℝ) :
    restScalar γ dγ
      = gaussTrans PortCas01.eta PortCas01.eta PortCas01.e0 (jet γ) (riem γ dγ) := by
  rw [restScalar_gauss hc, gaussTrans, hUp_eta_e0, spatialJet_eta_e0, projRiemTrace_Pi4,
    metricInner_Pi4, contract_Pi4]
  simp only [PiDPi_apply, Matrix.transpose_apply, projRiemFrame, traceFrame, transFrame, restV,
    Matrix.of_apply]
  simp
  ring

/-- Exact `ω²` sign/order: exterior scalar = same-order source scalar − `2 ω_ab ω^ab`. -/
theorem exterior_eq_tensor_same {γ : Fin 4 → Fin 4 → Fin 4 → ℝ} (hc : Compat γ)
    (dγ : Fin 4 → Fin 4 → Fin 4 → Fin 4 → ℝ) :
    restScalar γ dγ
      = gaussSame PortCas01.eta PortCas01.eta PortCas01.e0 (jet γ) (riem γ dγ)
        - 2 * metricInner (hUp PortCas01.eta PortCas01.e0)
            (vorticity 1 PortCas01.eta PortCas01.e0 (jet γ))
            (vorticity 1 PortCas01.eta PortCas01.e0 (jet γ)) := by
  have h1 := exterior_eq_tensor hc dγ
  have h2 := gaussSame_sub_gaussTrans (g := PortCas01.eta) eta_symm PortCas01.e0 (jet γ)
    (riem γ dγ)
  linarith

/-- 4-index canonical tensor theorem in the frame. -/
theorem gaussTensor_frame {γ : Fin 4 → Fin 4 → Fin 4 → ℝ} (hc : Compat γ)
    (dγ : Fin 4 → Fin 4 → Fin 4 → Fin 4 → ℝ) (i j k l : Fin 3) :
    gaussTensor PortCas01.eta PortCas01.e0 (jet γ) (riem γ dγ) i.succ j.succ k.succ l.succ
      = restCurv γ dγ k.succ l.succ i j := by
  rw [gauss_frame hc, gaussTensor, projDown_eta_e0, spatialJet_eta_e0]
  simp only [PiDPi_apply, restV, Matrix.of_apply]
  simp [Pi4, diagonal_apply]

/-! ## Part E. ω = 0 hypersurface branch -/

/-- Pointwise Frobenius condition: vertical brackets vanish iff `ω = 0`. -/
theorem frobenius_pointwise {γ : Fin 4 → Fin 4 → Fin 4 → ℝ} (hc : Compat γ) :
    (∀ k l : Fin 3, bracket γ 0 k.succ l.succ = 0) ↔ restOmega γ = 0 := by
  constructor
  · intro h
    ext k l
    have := h k l
    rw [bracket_vertical hc] at this
    simp only [Matrix.zero_apply]
    linarith
  · intro h k l
    rw [bracket_vertical hc, h, Matrix.zero_apply, mul_zero]

theorem omega_zero_rest_eq_slice {γ : Fin 4 → Fin 4 → Fin 4 → ℝ} (hc : Compat γ)
    (hω : restOmega γ = 0) (dγ : Fin 4 → Fin 4 → Fin 4 → Fin 4 → ℝ) (k l : Fin 3) :
    restCurv γ dγ k.succ l.succ = sliceCurv γ dγ k.succ l.succ := by
  rw [restCurv_exterior hc, hω, Matrix.zero_apply, mul_zero, zero_smul, sub_zero]

theorem omega_zero_scalar {γ : Fin 4 → Fin 4 → Fin 4 → ℝ} (hc : Compat γ)
    (hω : restOmega γ = 0) (dγ : Fin 4 → Fin 4 → Fin 4 → Fin 4 → ℝ) :
    restScalar γ dγ
        = gaussSame PortCas01.eta PortCas01.eta PortCas01.e0 (jet γ) (riem γ dγ)
      ∧ restScalar γ dγ
        = gaussTrans PortCas01.eta PortCas01.eta PortCas01.e0 (jet γ) (riem γ dγ) := by
  refine ⟨?_, exterior_eq_tensor hc dγ⟩
  rw [exterior_eq_tensor_same hc, metricInner_omega_frame, hω]
  simp [sameFrame]

theorem gaussSame_eq_gaussTrans_of_vorticity_zero {g ginv : Matrix (Fin 4) (Fin 4) ℝ}
    (hginv : ginvᵀ = ginv) (u : Fin 4 → ℝ) (D : Matrix (Fin 4) (Fin 4) ℝ)
    (R : Fin 4 → Fin 4 → Fin 4 → Fin 4 → ℝ) (hω : vorticity 1 g u D = 0) :
    gaussSame g ginv u D R = gaussTrans g ginv u D R := by
  have h := gaussSame_sub_gaussTrans (g := g) hginv u D R
  rw [hω] at h
  simp [metricInner] at h
  linarith

/-! ## Part F. Index-order convention (derivative-first vs velocity-first) -/

theorem spatialJet_transpose (g : Matrix (Fin 4) (Fin 4) ℝ) (u : Fin 4 → ℝ)
    (D : Matrix (Fin 4) (Fin 4) ℝ) : spatialJet g u Dᵀ = (spatialJet g u D)ᵀ := by
  simp [spatialJet, Matrix.transpose_mul, Matrix.mul_assoc]

theorem vorticity_transpose_jet (c : ℝ) (g : Matrix (Fin 4) (Fin 4) ℝ) (u : Fin 4 → ℝ)
    (D : Matrix (Fin 4) (Fin 4) ℝ) : vorticity c g u Dᵀ = -vorticity c g u D := by
  rw [vorticity, vorticity, spatialJet_transpose]
  ext a b
  simp [skewPart]
  ring

theorem metricInner_transpose_both {H : Matrix (Fin 4) (Fin 4) ℝ} (hH : Hᵀ = H)
    (X Y : Matrix (Fin 4) (Fin 4) ℝ) : metricInner H Xᵀ Yᵀ = metricInner H X Y := by
  unfold metricInner
  rw [← trace_transpose (H * X * H * Yᵀ)]
  simp only [transpose_mul, transpose_transpose, hH, Matrix.mul_assoc]
  rw [trace_mul_comm Y]
  simp only [Matrix.mul_assoc]

theorem contract_transpose {H : Matrix (Fin 4) (Fin 4) ℝ} (hH : Hᵀ = H)
    (X : Matrix (Fin 4) (Fin 4) ℝ) : contract H Xᵀ = contract H X := by
  rw [contract_eq_trace, contract_eq_trace, transpose_transpose, ← trace_transpose (H * Xᵀ),
    transpose_mul, transpose_transpose, hH, trace_mul_comm]

/-- Invariant content of the index-order convention: both Gauss scalars are unchanged
when the jet is transposed (velocity-first convention), although `ω` flips sign. -/
theorem gauss_scalars_transpose_jet {g ginv : Matrix (Fin 4) (Fin 4) ℝ} (hginv : ginvᵀ = ginv)
    (u : Fin 4 → ℝ) (D : Matrix (Fin 4) (Fin 4) ℝ) (R : Fin 4 → Fin 4 → Fin 4 → Fin 4 → ℝ) :
    gaussSame g ginv u Dᵀ R = gaussSame g ginv u D R
      ∧ gaussTrans g ginv u Dᵀ R = gaussTrans g ginv u D R := by
  have hH := hUp_symm hginv u
  refine ⟨?_, ?_⟩
  · rw [gaussSame, gaussSame, spatialJet_transpose, metricInner_transpose_both hH,
      contract_transpose hH]
  · rw [gaussTrans, gaussTrans, spatialJet_transpose, metricInner_transpose_both hH,
      contract_transpose hH]

/-! ## Part G. Non-vacuity witnesses and negative controls -/

/-- A rotating frame: `ω_12 ≠ 0` and the triad rotates along `u` (`γ_{1 0 2} ≠ 0`). -/
def γW (A B C : Fin 4) : ℝ :=
  if A = 2 ∧ B = 1 ∧ C = 0 then 1 else
  if A = 0 ∧ B = 1 ∧ C = 2 then -1 else
  if A = 1 ∧ B = 0 ∧ C = 2 then 1 else
  if A = 2 ∧ B = 0 ∧ C = 1 then -1 else 0

theorem compat_γW : Compat γW := by
  intro A B C
  fin_cases A <;> fin_cases B <;> fin_cases C <;> simp [γW]

theorem γW_nonintegrable : bracket γW 0 1 2 = 1 ∧ restOmega γW 0 1 = 1 / 2 := by
  constructor
  · simp [bracket, γW]
  · simp [restOmega, restV, jet, γW]

/-- Negative control: for `ω ≠ 0` the canonical object differs from the slice-type one. -/
theorem γW_rest_ne_slice (dγ : Fin 4 → Fin 4 → Fin 4 → Fin 4 → ℝ) :
    (restCurv γW dγ (Fin.succ 0) (Fin.succ 1) - sliceCurv γW dγ (Fin.succ 0) (Fin.succ 1)) 0 1
      = -1 := by
  rw [restCurv_exterior compat_γW]
  simp [restOmega, restV, restA, jet, γW]

theorem sameFrame_omega_γW : sameFrame (restOmega γW) = 1 / 2 := by
  simp [sameFrame, restOmega, restV, jet, γW, Fin.sum_univ_succ]
  norm_num

/-- Negative control: for `ω ≠ 0` the same-order source scalar is NOT the canonical one. -/
theorem γW_ordering_gap (dγ : Fin 4 → Fin 4 → Fin 4 → Fin 4 → ℝ) :
    gaussSame PortCas01.eta PortCas01.eta PortCas01.e0 (jet γW) (riem γW dγ)
      - restScalar γW dγ = 1 := by
  rw [exterior_eq_tensor_same compat_γW, metricInner_omega_frame, sameFrame_omega_γW]
  ring

/-- Gauge witness data. -/
def lW : Fin 4 → M3 := fun C => if C = 0 then !![0, 1, 0; -1, 0, 0; 0, 0, 0] else 0

def cW (E C D : Fin 4) : ℝ :=
  if E = 0 ∧ C = 1 ∧ D = 2 then 2 else if E = 0 ∧ C = 2 ∧ D = 1 then -2 else 0

def νW (C D : Fin 4) : M3 := if C = 1 ∧ D = 2 then (2 : ℝ) • lW 0 else 0

theorem gauge_witness_hyps :
    (1 : M3) * (1 : M3)ᵀ = 1 ∧ (∀ C, (lW C)ᵀ * 1 + (1 : M3)ᵀ * lW C = 0)
      ∧ (∀ C D, νW C D - νW D C = ∑ E, cW E C D • lW E) := by
  refine ⟨by simp, ?_, ?_⟩
  · intro C
    fin_cases C <;> ext i j <;> fin_cases i <;> fin_cases j <;> simp [lW]
  · intro C D
    fin_cases C <;> fin_cases D <;> simp [νW, cW, lW]

/-- Negative control: the slice-type expression is not invariant under a triad change
when the vertical bracket is nonzero, while the canonical curvature is covariant. -/
theorem slice_not_frame_invariant :
    sliceForm (gaugeA 1 lW 0) (gaugeDA 1 lW νW 0 0) cW 1 2
        ≠ (1 : M3)ᵀ * sliceForm 0 0 cW 1 2 * 1
      ∧ curvForm (gaugeA 1 lW 0) (gaugeDA 1 lW νW 0 0) cW 1 2
        = (1 : M3)ᵀ * curvForm 0 0 cW 1 2 * 1 := by
  obtain ⟨hO, hl, hν⟩ := gauge_witness_hyps
  refine ⟨?_, curvForm_gauge 1 lW 0 νW 0 cW hO hl hν 1 2⟩
  rw [sliceForm_gauge 1 lW 0 νW 0 cW hO hl hν 1 2]
  intro h
  have h' := congrFun (congrFun (add_eq_left.mp h) 0) 1
  simp [cW, lW] at h'

end R191ARotatingRestGauss
