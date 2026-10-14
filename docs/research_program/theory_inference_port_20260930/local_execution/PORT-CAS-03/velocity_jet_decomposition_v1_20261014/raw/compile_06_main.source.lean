import Mathlib
import VelocityJetRest
import PortCas01

/-!
# P03-A: physical kinematic decomposition of a normalized velocity jet

Source contract: `CAS_CONTRACT.json` obligation CAS-03,
`theta=c tr(h D); sigma=c sym(hDh)-theta*h/3; omega=c antisym(hDh); A=c^2 u.D`,
assumptions `D_ab=nabla_a u_b; D*u=0; u.u=-1`, signature `-+++`, `u=U/c`.
Implementation reference: `htt/src/common/relativistic_kinematics.py:336-360`.

Index conventions (fixed, derivative index first):
* `u : Fin 4 → ℝ` contravariant components `u^a`, dimensionless;
* `g` covariant metric `g_ab`, `ginv` its inverse `g^ab`;
* `D a b = D_ab = ∇_a u_b` (covariant, derivative index `a` first);
* `g *ᵥ u` is the covector `u_a`;
* `projDown g u = δ_a^c + u_a u^c` (acts on covariant indices),
  `projUp g u = δ^a_c + u^a u_c`, `hDown g u = h_ab = g_ab + u_a u_b`,
  `hUp ginv u = h^ab = g^ab + u^a u^b`;
* `spatialJet g u D = h_a^c D_cd h_b^d` (the source's `hDh`).
The pointwise algebra only uses `gᵀ = g`, `g * ginv = 1` and `g(u,u) = -1`;
it therefore holds for every symmetric nondegenerate metric, in particular for
signature `(-,+,+,+)`.

`c` is a constant real number. Where the contract requires it, `0 < c` is an
explicit hypothesis. No denominator other than the numeral `3` occurs.
-/

open Matrix Filter
open scoped Topology Matrix

namespace PORTCAS03VelocityJetDecomposition

/-! ## Pointwise definitions -/

/-- `h^a_c = δ^a_c + u^a u_c`. -/
def projUp (g : Matrix (Fin 4) (Fin 4) ℝ) (u : Fin 4 → ℝ) : Matrix (Fin 4) (Fin 4) ℝ :=
  1 + vecMulVec u (g *ᵥ u)

/-- `h_a^c = δ_a^c + u_a u^c`. -/
def projDown (g : Matrix (Fin 4) (Fin 4) ℝ) (u : Fin 4 → ℝ) : Matrix (Fin 4) (Fin 4) ℝ :=
  1 + vecMulVec (g *ᵥ u) u

/-- `h_ab = g_ab + u_a u_b`. -/
def hDown (g : Matrix (Fin 4) (Fin 4) ℝ) (u : Fin 4 → ℝ) : Matrix (Fin 4) (Fin 4) ℝ :=
  g + vecMulVec (g *ᵥ u) (g *ᵥ u)

/-- `h^ab = g^ab + u^a u^b`. -/
def hUp (ginv : Matrix (Fin 4) (Fin 4) ℝ) (u : Fin 4 → ℝ) : Matrix (Fin 4) (Fin 4) ℝ :=
  ginv + vecMulVec u u

/-- `(hDh)_ab = h_a^c D_cd h_b^d`. -/
def spatialJet (g : Matrix (Fin 4) (Fin 4) ℝ) (u : Fin 4 → ℝ)
    (D : Matrix (Fin 4) (Fin 4) ℝ) : Matrix (Fin 4) (Fin 4) ℝ :=
  projDown g u * D * (projDown g u)ᵀ

noncomputable def symPart (S : Matrix (Fin 4) (Fin 4) ℝ) : Matrix (Fin 4) (Fin 4) ℝ :=
  (1 / 2 : ℝ) • (S + Sᵀ)

noncomputable def skewPart (S : Matrix (Fin 4) (Fin 4) ℝ) : Matrix (Fin 4) (Fin 4) ℝ :=
  (1 / 2 : ℝ) • (S - Sᵀ)

/-- Full contraction `M^{ab} N_{ab}`. -/
def contract (M N : Matrix (Fin 4) (Fin 4) ℝ) : ℝ :=
  ∑ a, ∑ b, M a b * N a b

/-- Metric inner product `A_ab B^ab` with both indices raised by `ginv`. -/
def metricInner (ginv A B : Matrix (Fin 4) (Fin 4) ℝ) : ℝ :=
  trace (ginv * A * ginv * Bᵀ)

/-- `θ = c g^{ab} (hDh)_ab` (implementation form). -/
def expansion (c : ℝ) (ginv g : Matrix (Fin 4) (Fin 4) ℝ) (u : Fin 4 → ℝ)
    (D : Matrix (Fin 4) (Fin 4) ℝ) : ℝ :=
  c * contract ginv (spatialJet g u D)

/-- `σ = c sym(hDh) - θ h / 3`. -/
noncomputable def shear (c : ℝ) (ginv g : Matrix (Fin 4) (Fin 4) ℝ) (u : Fin 4 → ℝ)
    (D : Matrix (Fin 4) (Fin 4) ℝ) : Matrix (Fin 4) (Fin 4) ℝ :=
  c • symPart (spatialJet g u D) - (expansion c ginv g u D / 3) • hDown g u

/-- `ω = c antisym(hDh)` (derivative-first convention). -/
noncomputable def vorticity (c : ℝ) (g : Matrix (Fin 4) (Fin 4) ℝ) (u : Fin 4 → ℝ)
    (D : Matrix (Fin 4) (Fin 4) ℝ) : Matrix (Fin 4) (Fin 4) ℝ :=
  c • skewPart (spatialJet g u D)

/-- `A_b = c^2 u^a D_ab`. -/
def acceleration (c : ℝ) (u : Fin 4 → ℝ) (D : Matrix (Fin 4) (Fin 4) ℝ) : Fin 4 → ℝ :=
  c ^ 2 • (u ᵥ* D)

/-! ## Basic pointwise lemmas -/

section Pointwise

variable {g ginv : Matrix (Fin 4) (Fin 4) ℝ} {u : Fin 4 → ℝ}

theorem ul_dot_u (hu : u ⬝ᵥ (g *ᵥ u) = -1) : (g *ᵥ u) ⬝ᵥ u = -1 := by
  rw [dotProduct_comm]; exact hu

theorem ginv_mul_g (hinv : g * ginv = 1) : ginv * g = 1 := mul_eq_one_comm.mp hinv

theorem ginv_symm (hg : gᵀ = g) (hinv : g * ginv = 1) : ginvᵀ = ginv := by
  calc ginvᵀ = ginvᵀ * (g * ginv) := by rw [hinv, Matrix.mul_one]
    _ = (g * ginv)ᵀ * ginv := by rw [transpose_mul, hg, Matrix.mul_assoc]
    _ = ginv := by rw [hinv, transpose_one, Matrix.one_mul]

theorem g_mulVec_eq_vecMul (hg : gᵀ = g) : g *ᵥ u = u ᵥ* g := by
  rw [← vecMul_transpose, hg]

theorem ginv_mulVec_ul (hinv : g * ginv = 1) : ginv *ᵥ (g *ᵥ u) = u := by
  rw [mulVec_mulVec, ginv_mul_g hinv, one_mulVec]

theorem ul_vecMul_ginv (hg : gᵀ = g) (hinv : g * ginv = 1) : (g *ᵥ u) ᵥ* ginv = u := by
  rw [g_mulVec_eq_vecMul hg, vecMul_vecMul, hinv, vecMul_one]

theorem projDown_transpose : (projDown g u)ᵀ = projUp g u := by
  simp [projDown, projUp, transpose_add, transpose_vecMulVec]

theorem contract_eq_trace (M N : Matrix (Fin 4) (Fin 4) ℝ) :
    contract M N = trace (M * Nᵀ) := by
  simp [contract, Matrix.trace, Matrix.mul_apply, Matrix.diag]

/-! ## T2: projector, idempotence and trace three -/

theorem projUp_idem (hu : u ⬝ᵥ (g *ᵥ u) = -1) :
    projUp g u * projUp g u = projUp g u := by
  unfold projUp
  simp only [add_mul, mul_add, Matrix.one_mul, Matrix.mul_one, vecMulVec_mul_vecMulVec,
    ul_dot_u hu, neg_one_smul, vecMulVec_neg]
  abel

theorem projDown_idem (hu : u ⬝ᵥ (g *ᵥ u) = -1) :
    projDown g u * projDown g u = projDown g u := by
  unfold projDown
  simp only [add_mul, mul_add, Matrix.one_mul, Matrix.mul_one, vecMulVec_mul_vecMulVec,
    hu, neg_one_smul, vecMulVec_neg]
  abel

theorem trace_projUp (hu : u ⬝ᵥ (g *ᵥ u) = -1) : trace (projUp g u) = 3 := by
  simp [projUp, trace_add, trace_one, trace_vecMulVec, hu]
  norm_num

theorem trace_projDown (hu : u ⬝ᵥ (g *ᵥ u) = -1) : trace (projDown g u) = 3 := by
  simp [projDown, trace_add, trace_one, trace_vecMulVec, ul_dot_u hu]
  norm_num

theorem projUp_mulVec_u (hu : u ⬝ᵥ (g *ᵥ u) = -1) : projUp g u *ᵥ u = 0 := by
  simp [projUp, add_mulVec, vecMulVec_mulVec, ul_dot_u hu]

theorem u_vecMul_projDown (hu : u ⬝ᵥ (g *ᵥ u) = -1) : u ᵥ* projDown g u = 0 := by
  simp [projDown, vecMul_add, vecMul_vecMulVec, hu]

theorem hDown_eq_g_mul_projUp : hDown g u = g * projUp g u := by
  simp [hDown, projUp, Matrix.mul_add, mul_vecMulVec]

theorem hDown_symm (hg : gᵀ = g) : (hDown g u)ᵀ = hDown g u := by
  simp [hDown, transpose_add, transpose_vecMulVec, hg]

theorem hDown_mulVec_u (hu : u ⬝ᵥ (g *ᵥ u) = -1) : hDown g u *ᵥ u = 0 := by
  simp [hDown, add_mulVec, vecMulVec_mulVec, ul_dot_u hu]

theorem u_vecMul_hDown (hg : gᵀ = g) (hu : u ⬝ᵥ (g *ᵥ u) = -1) : u ᵥ* hDown g u = 0 := by
  rw [← mulVec_transpose, hDown_symm hg, hDown_mulVec_u hu]

theorem hDown_proj (hg : gᵀ = g) (hinv : g * ginv = 1) (hu : u ⬝ᵥ (g *ᵥ u) = -1) :
    hDown g u * ginv * hDown g u = hDown g u := by
  have hV : vecMulVec (g *ᵥ u) (g *ᵥ u) * ginv = vecMulVec (g *ᵥ u) u := by
    rw [vecMulVec_mul, ul_vecMul_ginv hg hinv]
  have hW : vecMulVec (g *ᵥ u) u * (g + vecMulVec (g *ᵥ u) (g *ᵥ u)) = 0 := by
    rw [vecMulVec_mul, vecMul_add, vecMul_vecMulVec, hu, ← g_mulVec_eq_vecMul hg]
    simp
  unfold hDown
  rw [add_mul, hinv, hV, add_mul, Matrix.one_mul, hW, add_zero]

theorem trace_ginv_hDown (hinv : g * ginv = 1) (hu : u ⬝ᵥ (g *ᵥ u) = -1) :
    trace (ginv * hDown g u) = 3 := by
  rw [hDown, Matrix.mul_add, ginv_mul_g hinv, mul_vecMulVec, ginv_mulVec_ul hinv, trace_add,
    trace_one, trace_vecMulVec, hu]
  norm_num

theorem ginv_hDown_ginv (hg : gᵀ = g) (hinv : g * ginv = 1) :
    ginv * hDown g u * ginv = hUp ginv u := by
  rw [hDown, Matrix.mul_add, add_mul, ginv_mul_g hinv, Matrix.one_mul, mul_vecMulVec,
    ginv_mulVec_ul hinv, vecMulVec_mul, ul_vecMul_ginv hg hinv, hUp]

theorem projUp_ginv_projDown (hg : gᵀ = g) (hinv : g * ginv = 1) (hu : u ⬝ᵥ (g *ᵥ u) = -1) :
    projUp g u * ginv * projDown g u = hUp ginv u := by
  have h1 : vecMulVec u (g *ᵥ u) * ginv = vecMulVec u u := by
    rw [vecMulVec_mul, ul_vecMul_ginv hg hinv]
  have h2 : ginv * vecMulVec (g *ᵥ u) u = vecMulVec u u := by
    rw [mul_vecMulVec, ginv_mulVec_ul hinv]
  have h3 : vecMulVec u u * vecMulVec (g *ᵥ u) u = -vecMulVec u u := by
    rw [vecMulVec_mul_vecMulVec, hu, neg_one_smul, vecMulVec_neg]
  unfold projUp projDown hUp
  rw [add_mul, Matrix.one_mul, h1, mul_add, Matrix.mul_one, add_mul, h2, h3]
  abel

/-! ## T3: trace forms -/

theorem contract_ginv_spatialJet (hg : gᵀ = g) (hinv : g * ginv = 1)
    (hu : u ⬝ᵥ (g *ᵥ u) = -1) (D : Matrix (Fin 4) (Fin 4) ℝ) :
    contract ginv (spatialJet g u D) = contract (hUp ginv u) D := by
  rw [contract_eq_trace, contract_eq_trace]
  have hS : (spatialJet g u D)ᵀ = projDown g u * (Dᵀ * projUp g u) := by
    rw [spatialJet, transpose_mul, transpose_mul, transpose_transpose, projDown_transpose]
  rw [hS, ← projUp_ginv_projDown hg hinv hu]
  rw [show ginv * (projDown g u * (Dᵀ * projUp g u)) =
      (ginv * projDown g u * Dᵀ) * projUp g u by simp only [Matrix.mul_assoc],
    trace_mul_comm]
  simp only [Matrix.mul_assoc]

theorem contract_hUp_of_rest (D : Matrix (Fin 4) (Fin 4) ℝ) (hD : D *ᵥ u = 0) :
    contract (hUp ginv u) D = contract ginv D := by
  rw [contract_eq_trace, contract_eq_trace, hUp, add_mul, trace_add, vecMulVec_mul,
    trace_vecMulVec, vecMul_transpose, hD, dotProduct_zero, add_zero]

theorem trace_ginv_transpose (hg : gᵀ = g) (hinv : g * ginv = 1)
    (S : Matrix (Fin 4) (Fin 4) ℝ) : trace (ginv * S) = trace (ginv * Sᵀ) := by
  rw [← trace_transpose (ginv * S), transpose_mul, ginv_symm hg hinv, trace_mul_comm]

/-! ## T4: trace / STF / skew decomposition of `hDh` -/

theorem decomposition (c : ℝ) (D : Matrix (Fin 4) (Fin 4) ℝ) :
    c • spatialJet g u D =
      shear c ginv g u D + (expansion c ginv g u D / 3) • hDown g u + vorticity c g u D := by
  ext i j
  simp only [shear, vorticity, symPart, skewPart, Matrix.add_apply, Matrix.sub_apply, Matrix.smul_apply,
    Matrix.transpose_apply, smul_eq_mul]
  ring

theorem shear_symm (hg : gᵀ = g) (c : ℝ) (D : Matrix (Fin 4) (Fin 4) ℝ) :
    (shear c ginv g u D)ᵀ = shear c ginv g u D := by
  ext i j
  have hh : hDown g u j i = hDown g u i j := by
    have := congrFun (congrFun (hDown_symm (u := u) hg) i) j
    simpa [Matrix.transpose_apply] using this
  simp only [shear, symPart, Matrix.transpose_apply, Matrix.sub_apply, Matrix.smul_apply, Matrix.add_apply, smul_eq_mul, hh]
  ring

theorem vorticity_skew (c : ℝ) (D : Matrix (Fin 4) (Fin 4) ℝ) :
    (vorticity c g u D)ᵀ = -vorticity c g u D := by
  ext i j
  simp only [vorticity, skewPart, Matrix.transpose_apply, Matrix.sub_apply, Matrix.smul_apply, Matrix.neg_apply,
    smul_eq_mul]
  ring

theorem shear_traceless (hg : gᵀ = g) (hinv : g * ginv = 1) (hu : u ⬝ᵥ (g *ᵥ u) = -1)
    (c : ℝ) (D : Matrix (Fin 4) (Fin 4) ℝ) :
    contract ginv (shear c ginv g u D) = 0 := by
  have hT := trace_ginv_transpose hg hinv (spatialJet g u D)
  rw [contract_eq_trace]
  simp only [shear, expansion, symPart, contract_eq_trace, transpose_sub, transpose_smul,
    transpose_add, transpose_transpose, Matrix.mul_sub, Matrix.mul_smul, Matrix.mul_add,
    trace_sub, trace_smul, trace_add, hDown_symm hg, trace_ginv_hDown hinv hu, smul_eq_mul]
  rw [hT]
  ring

theorem vorticity_traceless (hg : gᵀ = g) (hinv : g * ginv = 1) (c : ℝ)
    (D : Matrix (Fin 4) (Fin 4) ℝ) :
    contract ginv (vorticity c g u D) = 0 := by
  have hT := trace_ginv_transpose hg hinv (spatialJet g u D)
  rw [contract_eq_trace]
  simp only [vorticity, skewPart, transpose_sub, transpose_smul, transpose_transpose,
    Matrix.mul_sub, Matrix.mul_smul, trace_sub, trace_smul, smul_eq_mul]
  rw [hT]
  ring

theorem spatialJet_mulVec_u (hu : u ⬝ᵥ (g *ᵥ u) = -1) (D : Matrix (Fin 4) (Fin 4) ℝ) :
    spatialJet g u D *ᵥ u = 0 := by
  rw [spatialJet, projDown_transpose, ← mulVec_mulVec, projUp_mulVec_u hu, mulVec_zero]

theorem u_vecMul_spatialJet (hu : u ⬝ᵥ (g *ᵥ u) = -1) (D : Matrix (Fin 4) (Fin 4) ℝ) :
    u ᵥ* spatialJet g u D = 0 := by
  rw [spatialJet, ← vecMul_vecMul, ← vecMul_vecMul, u_vecMul_projDown hu, zero_vecMul,
    zero_vecMul]

theorem shear_mulVec_u (hu : u ⬝ᵥ (g *ᵥ u) = -1) (c : ℝ) (D : Matrix (Fin 4) (Fin 4) ℝ) :
    shear c ginv g u D *ᵥ u = 0 := by
  simp only [shear, symPart, sub_mulVec, smul_mulVec, add_mulVec, mulVec_transpose,
    spatialJet_mulVec_u hu, u_vecMul_spatialJet hu, hDown_mulVec_u hu, smul_zero, add_zero,
    sub_zero]

theorem u_vecMul_shear (hg : gᵀ = g) (hu : u ⬝ᵥ (g *ᵥ u) = -1) (c : ℝ)
    (D : Matrix (Fin 4) (Fin 4) ℝ) :
    u ᵥ* shear c ginv g u D = 0 := by
  simp only [shear, symPart, vecMul_sub, vecMul_smul, vecMul_add, vecMul_transpose,
    spatialJet_mulVec_u hu, u_vecMul_spatialJet hu, u_vecMul_hDown hg hu, smul_zero,
    add_zero, sub_zero]

theorem vorticity_mulVec_u (hu : u ⬝ᵥ (g *ᵥ u) = -1) (c : ℝ) (D : Matrix (Fin 4) (Fin 4) ℝ) :
    vorticity c g u D *ᵥ u = 0 := by
  simp only [vorticity, skewPart, smul_mulVec, sub_mulVec, mulVec_transpose,
    spatialJet_mulVec_u hu, u_vecMul_spatialJet hu, sub_zero, smul_zero]

theorem u_vecMul_vorticity (hu : u ⬝ᵥ (g *ᵥ u) = -1) (c : ℝ) (D : Matrix (Fin 4) (Fin 4) ℝ) :
    u ᵥ* vorticity c g u D = 0 := by
  simp only [vorticity, skewPart, vecMul_smul, vecMul_sub, vecMul_transpose,
    spatialJet_mulVec_u hu, u_vecMul_spatialJet hu, sub_zero, smul_zero]

/-- Symmetric and antisymmetric tensors are orthogonal under `A_ab B^ab`. -/
theorem metricInner_sym_skew (hginv : ginvᵀ = ginv) {X Y : Matrix (Fin 4) (Fin 4) ℝ}
    (hX : Xᵀ = X) (hY : Yᵀ = -Y) : metricInner ginv X Y = 0 := by
  unfold metricInner
  have h1 : trace (ginv * X * ginv * Yᵀ) = -trace (ginv * X * ginv * Y) := by
    rw [hY, Matrix.mul_neg, trace_neg]
  have h2 : trace (ginv * X * ginv * Yᵀ) = trace (ginv * X * ginv * Y) := by
    rw [← trace_transpose, transpose_mul, transpose_mul, transpose_mul, transpose_transpose,
      hX, hginv, trace_mul_comm Y]
    simp only [Matrix.mul_assoc]
  linarith

theorem metricInner_skew_sym (hginv : ginvᵀ = ginv) {X Y : Matrix (Fin 4) (Fin 4) ℝ}
    (hX : Xᵀ = X) (hY : Yᵀ = -Y) : metricInner ginv Y X = 0 := by
  unfold metricInner
  have h1 : trace (ginv * Y * ginv * Xᵀ) = trace (ginv * Y * ginv * X) := by rw [hX]
  have h2 : trace (ginv * Y * ginv * Xᵀ) = -trace (ginv * Y * ginv * X) := by
    rw [← trace_transpose, transpose_mul, transpose_mul, transpose_mul, transpose_transpose,
      hY, hginv, trace_mul_comm X]
    simp only [Matrix.mul_assoc, Matrix.mul_neg, Matrix.neg_mul, trace_neg]
  linarith

theorem shear_vorticity_orthogonal (hg : gᵀ = g) (hinv : g * ginv = 1) (c : ℝ)
    (D : Matrix (Fin 4) (Fin 4) ℝ) :
    metricInner ginv (shear c ginv g u D) (vorticity c g u D) = 0 :=
  metricInner_sym_skew (ginv_symm hg hinv) (shear_symm hg c D) (vorticity_skew c D)

theorem vorticity_h_orthogonal (hg : gᵀ = g) (hinv : g * ginv = 1) (c : ℝ)
    (D : Matrix (Fin 4) (Fin 4) ℝ) :
    metricInner ginv (vorticity c g u D) (hDown g u) = 0 :=
  metricInner_skew_sym (ginv_symm hg hinv) (hDown_symm hg) (vorticity_skew c D)

theorem shear_h_orthogonal (hg : gᵀ = g) (hinv : g * ginv = 1) (hu : u ⬝ᵥ (g *ᵥ u) = -1)
    (c : ℝ) (D : Matrix (Fin 4) (Fin 4) ℝ) :
    metricInner ginv (shear c ginv g u D) (hDown g u) = 0 := by
  unfold metricInner
  rw [hDown_symm hg]
  have hcyc : trace (ginv * shear c ginv g u D * ginv * hDown g u) =
      trace (shear c ginv g u D * (ginv * hDown g u * ginv)) := by
    rw [show ginv * shear c ginv g u D * ginv * hDown g u =
        ginv * (shear c ginv g u D * ginv * hDown g u) by simp only [Matrix.mul_assoc],
      trace_mul_comm ginv]
    simp only [Matrix.mul_assoc]
  have h0 := shear_traceless hg hinv hu c D
  rw [contract_eq_trace, shear_symm hg] at h0
  rw [hcyc, ginv_hDown_ginv hg hinv, hUp, Matrix.mul_add, trace_add, mul_vecMulVec,
    trace_vecMulVec, shear_mulVec_u hu, zero_dotProduct, add_zero, trace_mul_comm, h0]

/-! ## T5: physical composition with `c`, acceleration, reconstruction, `Q = c D` -/

theorem acceleration_eq_rest (c : ℝ) (D : Matrix (Fin 4) (Fin 4) ℝ) :
    acceleration c u D = PORTCAS03VelocityJetRest.physicalAcceleration u D c := by
  funext j
  simp [acceleration, PORTCAS03VelocityJetRest.physicalAcceleration, vecMul, dotProduct]

theorem acceleration_orthogonal (c : ℝ) (D : Matrix (Fin 4) (Fin 4) ℝ) (hD : D *ᵥ u = 0) :
    u ⬝ᵥ acceleration c u D = 0 := by
  have hrow : ∀ i, ∑ j, D i j * u j = 0 := fun i => by
    simpa [mulVec, dotProduct] using congrFun hD i
  have := PORTCAS03VelocityJetRest.rest_acceleration u D c hrow
  rw [acceleration_eq_rest]
  simpa [dotProduct] using this

theorem expansion_eq_trace_hD (hg : gᵀ = g) (hinv : g * ginv = 1) (hu : u ⬝ᵥ (g *ᵥ u) = -1)
    (c : ℝ) (D : Matrix (Fin 4) (Fin 4) ℝ) :
    expansion c ginv g u D = c * contract (hUp ginv u) D := by
  rw [expansion, contract_ginv_spatialJet hg hinv hu]

theorem expansion_eq_div_of_rest (hg : gᵀ = g) (hinv : g * ginv = 1)
    (hu : u ⬝ᵥ (g *ᵥ u) = -1) (c : ℝ) (D : Matrix (Fin 4) (Fin 4) ℝ) (hD : D *ᵥ u = 0) :
    expansion c ginv g u D = c * contract ginv D := by
  rw [expansion_eq_trace_hD hg hinv hu, contract_hUp_of_rest D hD]

theorem spatialJet_of_rest (D : Matrix (Fin 4) (Fin 4) ℝ) (hD : D *ᵥ u = 0) :
    spatialJet g u D = D + vecMulVec (g *ᵥ u) (u ᵥ* D) := by
  rw [spatialJet, projDown_transpose, Matrix.mul_assoc, projUp, Matrix.mul_add, Matrix.mul_one,
    mul_vecMulVec, hD, zero_vecMulVec, add_zero, projDown, add_mul, Matrix.one_mul,
    vecMulVec_mul]

/-- `c^2 D_ab = c(σ_ab + θ h_ab/3 + ω_ab) - u_a A_b`, i.e. the source decomposition
`∇_a U_b = σ_ab + θ h_ab/3 + ω_ab - u_a A_b / c` multiplied out by `c` (no division). -/
theorem reconstruction (c : ℝ) (D : Matrix (Fin 4) (Fin 4) ℝ) (hD : D *ᵥ u = 0) :
    c ^ 2 • D = c • (shear c ginv g u D + (expansion c ginv g u D / 3) • hDown g u +
      vorticity c g u D) - vecMulVec (g *ᵥ u) (acceleration c u D) := by
  rw [← decomposition, spatialJet_of_rest D hD, acceleration, vecMulVec_smul, smul_smul,
    smul_add, ← pow_two]
  abel

theorem spatialJet_smul (c : ℝ) (D : Matrix (Fin 4) (Fin 4) ℝ) :
    spatialJet g u (c • D) = c • spatialJet g u D := by
  rw [spatialJet, Matrix.mul_smul, Matrix.smul_mul, spatialJet]

theorem contract_smul_right (M N : Matrix (Fin 4) (Fin 4) ℝ) (c : ℝ) :
    contract M (c • N) = c * contract M N := by
  simp only [contract, Matrix.smul_apply, smul_eq_mul, Finset.mul_sum]
  apply Finset.sum_congr rfl; intro a _
  apply Finset.sum_congr rfl; intro b _
  ring

/-- With `U = c u` and `Q = c D` (`Q_ab = ∇_a U_b` for constant `c`), the kinematic
quantities carry no further `c`: `θ = tr(h Q)`, `σ = sym(hQh) - θ h/3`,
`ω = antisym(hQh)`, `A = U·Q`. -/
theorem kinematics_in_Q (hg : gᵀ = g) (hinv : g * ginv = 1) (hu : u ⬝ᵥ (g *ᵥ u) = -1)
    (c : ℝ) (D : Matrix (Fin 4) (Fin 4) ℝ) :
    expansion c ginv g u D = contract ginv (spatialJet g u (c • D)) ∧
    expansion c ginv g u D = contract (hUp ginv u) (c • D) ∧
    shear c ginv g u D =
      symPart (spatialJet g u (c • D)) - (expansion c ginv g u D / 3) • hDown g u ∧
    vorticity c g u D = skewPart (spatialJet g u (c • D)) ∧
    acceleration c u D = (c • u) ᵥ* (c • D) := by
  refine ⟨?_, ?_, ?_, ?_, ?_⟩
  · rw [spatialJet_smul, contract_smul_right, expansion]
  · rw [contract_smul_right, expansion_eq_trace_hD hg hinv hu]
  · rw [spatialJet_smul, shear]
    congr 1
    ext i j
    simp only [symPart, Matrix.smul_apply, Matrix.add_apply, Matrix.transpose_apply, smul_eq_mul]
    ring
  · rw [spatialJet_smul, vorticity]
    ext i j
    simp only [skewPart, Matrix.smul_apply, Matrix.sub_apply, Matrix.transpose_apply, smul_eq_mul]
    ring
  · funext j
    simp only [acceleration, vecMul, dotProduct, Pi.smul_apply, Matrix.smul_apply, smul_eq_mul,
      Finset.mul_sum]
    apply Finset.sum_congr rfl; intro i _
    ring

theorem D_eq_inv_smul_Q {c : ℝ} (hc : 0 < c) (D : Matrix (Fin 4) (Fin 4) ℝ) :
    D = c⁻¹ • (c • D) := by
  rw [smul_smul, inv_mul_cancel₀ hc.ne', one_smul]

/-- Pointwise master theorem for arbitrary unit timelike `u` (`g(u,u) = -1`) and
admissible `D` (`D_ab u^b = 0`), with explicit `0 < c`. -/
theorem pointwise_kinematics (hg : gᵀ = g) (hinv : g * ginv = 1) (hu : u ⬝ᵥ (g *ᵥ u) = -1)
    {c : ℝ} (hc : 0 < c) (D : Matrix (Fin 4) (Fin 4) ℝ) (hD : D *ᵥ u = 0) :
    expansion c ginv g u D = c * contract (hUp ginv u) D ∧
    expansion c ginv g u D = c * contract ginv D ∧
    c • spatialJet g u D =
      shear c ginv g u D + (expansion c ginv g u D / 3) • hDown g u + vorticity c g u D ∧
    (shear c ginv g u D)ᵀ = shear c ginv g u D ∧
    contract ginv (shear c ginv g u D) = 0 ∧
    shear c ginv g u D *ᵥ u = 0 ∧ u ᵥ* shear c ginv g u D = 0 ∧
    (vorticity c g u D)ᵀ = -vorticity c g u D ∧
    vorticity c g u D *ᵥ u = 0 ∧ u ᵥ* vorticity c g u D = 0 ∧
    metricInner ginv (shear c ginv g u D) (vorticity c g u D) = 0 ∧
    metricInner ginv (shear c ginv g u D) (hDown g u) = 0 ∧
    metricInner ginv (vorticity c g u D) (hDown g u) = 0 ∧
    u ⬝ᵥ acceleration c u D = 0 ∧
    c ^ 2 • D = c • (shear c ginv g u D + (expansion c ginv g u D / 3) • hDown g u +
      vorticity c g u D) - vecMulVec (g *ᵥ u) (acceleration c u D) ∧
    D = c⁻¹ • (c • D) :=
  ⟨expansion_eq_trace_hD hg hinv hu c D, expansion_eq_div_of_rest hg hinv hu c D hD,
    decomposition c D, shear_symm hg c D, shear_traceless hg hinv hu c D,
    shear_mulVec_u hu c D, u_vecMul_shear hg hu c D, vorticity_skew c D,
    vorticity_mulVec_u hu c D, u_vecMul_vorticity hu c D,
    shear_vorticity_orthogonal hg hinv c D, shear_h_orthogonal hg hinv hu c D,
    vorticity_h_orthogonal hg hinv c D, acceleration_orthogonal c D hD,
    reconstruction c D hD, D_eq_inv_smul_Q hc D⟩

end Pointwise

/-! ## T1: field-level covariant derivative and the differentiated normalization -/

/-- Coordinate space of a chart. -/
abbrev Pt := Fin 4 → ℝ

/-- Coordinate partial derivative `∂_a f (x)`, the actual Fréchet derivative. -/
noncomputable def pd (f : Pt → ℝ) (x : Pt) (a : Fin 4) : ℝ :=
  fderiv ℝ f x (Pi.single a 1)

/-- `u_b(y) = g_bc(y) u^c(y)`. -/
def lowerField (g : Pt → Matrix (Fin 4) (Fin 4) ℝ) (u : Pt → Fin 4 → ℝ) (y : Pt)
    (b : Fin 4) : ℝ :=
  ∑ c, g y b c * u y c

/-- `∇_a u^c = ∂_a u^c + Γ^c_{ad} u^d`, with `Γ x c a d = Γ^c_{ad}(x)`. -/
noncomputable def nablaUp (Γ : Pt → Fin 4 → Fin 4 → Fin 4 → ℝ) (u : Pt → Fin 4 → ℝ)
    (x : Pt) (a c : Fin 4) : ℝ :=
  pd (fun y => u y c) x a + ∑ d, Γ x c a d * u x d

/-- `D_ab = ∇_a u_b = ∂_a u_b - Γ^c_{ab} u_c` (contract convention, derivative first). -/
noncomputable def velJet (Γ : Pt → Fin 4 → Fin 4 → Fin 4 → ℝ)
    (g : Pt → Matrix (Fin 4) (Fin 4) ℝ) (u : Pt → Fin 4 → ℝ) (x : Pt) (a b : Fin 4) : ℝ :=
  pd (fun y => lowerField g u y b) x a - ∑ c, Γ x c a b * lowerField g u x c

noncomputable def velJetMatrix (Γ : Pt → Fin 4 → Fin 4 → Fin 4 → ℝ)
    (g : Pt → Matrix (Fin 4) (Fin 4) ℝ) (u : Pt → Fin 4 → ℝ) (x : Pt) :
    Matrix (Fin 4) (Fin 4) ℝ :=
  Matrix.of fun a b => velJet Γ g u x a b

/-- Metric compatibility at `x`: `∇_a g_bc = ∂_a g_bc - Γ^d_{ab} g_dc - Γ^d_{ac} g_bd = 0`.
No torsion-freeness is assumed. -/
def MetricCompatibleAt (Γ : Pt → Fin 4 → Fin 4 → Fin 4 → ℝ)
    (g : Pt → Matrix (Fin 4) (Fin 4) ℝ) (x : Pt) : Prop :=
  ∀ a b c, pd (fun y => g y b c) x a = ∑ d, (Γ x d a b * g x d c + Γ x d a c * g x b d)

def FieldDiffAt (g : Pt → Matrix (Fin 4) (Fin 4) ℝ) (u : Pt → Fin 4 → ℝ) (x : Pt) : Prop :=
  (∀ b c, DifferentiableAt ℝ (fun y => g y b c) x) ∧
    (∀ c, DifferentiableAt ℝ (fun y => u y c) x)

theorem hasFDerivAt_sum_mul {x : Pt} {f h : Fin 4 → Pt → ℝ}
    (hf : ∀ i, DifferentiableAt ℝ (f i) x) (hh : ∀ i, DifferentiableAt ℝ (h i) x) :
    HasFDerivAt (fun y => ∑ i, f i y * h i y)
      (∑ i, (f i x • fderiv ℝ (h i) x + h i x • fderiv ℝ (f i) x)) x :=
  HasFDerivAt.fun_sum (A := fun i y => f i y * h i y)
    (fun i _ => (hf i).hasFDerivAt.mul (hh i).hasFDerivAt)

theorem pd_sum_mul {x : Pt} {f h : Fin 4 → Pt → ℝ}
    (hf : ∀ i, DifferentiableAt ℝ (f i) x) (hh : ∀ i, DifferentiableAt ℝ (h i) x)
    (a : Fin 4) :
    pd (fun y => ∑ i, f i y * h i y) x a =
      ∑ i, (f i x * pd (h i) x a + h i x * pd (f i) x a) := by
  unfold pd
  rw [(hasFDerivAt_sum_mul hf hh).fderiv]
  simp

theorem lowerField_differentiableAt {g : Pt → Matrix (Fin 4) (Fin 4) ℝ}
    {u : Pt → Fin 4 → ℝ} {x : Pt} (hd : FieldDiffAt g u x) (b : Fin 4) :
    DifferentiableAt ℝ (fun y => lowerField g u y b) x :=
  (hasFDerivAt_sum_mul (f := fun c y => g y b c) (h := fun c y => u y c)
    (fun c => hd.1 b c) hd.2).differentiableAt

/-- Index convention check: `∇_a u_b = g_bc ∇_a u^c` under metric compatibility. -/
theorem velJet_eq_lower {Γ : Pt → Fin 4 → Fin 4 → Fin 4 → ℝ}
    {g : Pt → Matrix (Fin 4) (Fin 4) ℝ} {u : Pt → Fin 4 → ℝ} {x : Pt}
    (hd : FieldDiffAt g u x) (hc : MetricCompatibleAt Γ g x) (a b : Fin 4) :
    velJet Γ g u x a b = ∑ c, g x b c * nablaUp Γ u x a c := by
  unfold velJet lowerField
  rw [pd_sum_mul (f := fun c y => g y b c) (h := fun c y => u y c) (fun c => hd.1 b c) hd.2]
  simp only [hc a b]
  simp only [nablaUp, Fin.sum_univ_four]
  ring

/-- T1: the differentiated normalization.  If `g(u,u) = -1` holds on a neighbourhood of
`x`, the connection is metric compatible and `g x` is symmetric, then `D_ab u^b = 0`. -/
theorem velJet_mulVec_u {Γ : Pt → Fin 4 → Fin 4 → Fin 4 → ℝ}
    {g : Pt → Matrix (Fin 4) (Fin 4) ℝ} {u : Pt → Fin 4 → ℝ} {x : Pt}
    (hd : FieldDiffAt g u x) (hc : MetricCompatibleAt Γ g x) (hsym : (g x)ᵀ = g x)
    (hnorm : ∀ᶠ y in 𝓝 x, u y ⬝ᵥ (g y *ᵥ u y) = -1) :
    velJetMatrix Γ g u x *ᵥ u x = 0 := by
  funext a
  simp only [mulVec, dotProduct, velJetMatrix, Matrix.of_apply, Pi.zero_apply]
  have hN : (fun y => ∑ b, u y b * lowerField g u y b) =ᶠ[𝓝 x] fun _ => (-1 : ℝ) := by
    filter_upwards [hnorm] with y hy
    simpa [dotProduct, mulVec, lowerField] using hy
  have hpdN : pd (fun y => ∑ b, u y b * lowerField g u y b) x a = 0 := by
    unfold pd
    rw [Filter.EventuallyEq.fderiv_eq hN]
    simp
  rw [pd_sum_mul (f := fun b y => u y b) (h := fun b y => lowerField g u y b) hd.2
    (lowerField_differentiableAt hd) a] at hpdN
  have hdef : ∀ b, pd (fun y => lowerField g u y b) x a =
      velJet Γ g u x a b + ∑ c, Γ x c a b * lowerField g u x c := by
    intro b; unfold velJet; ring
  simp only [hdef] at hpdN
  simp only [velJet_eq_lower hd hc] at hpdN ⊢
  have hs : ∀ i j, g x i j = g x j i := fun i j => by
    have := congrFun (congrFun hsym j) i
    simpa [Matrix.transpose_apply] using this
  simp only [nablaUp, lowerField, Fin.sum_univ_four] at hpdN ⊢
  simp only [hs 1 0, hs 2 0, hs 3 0, hs 2 1, hs 3 1, hs 3 2] at hpdN ⊢
  linear_combination hpdN / 2

/-- `U = c u` with constant `c`: `Q = ∇U = c ∇u = c D`. -/
theorem velJetMatrix_smul {Γ : Pt → Fin 4 → Fin 4 → Fin 4 → ℝ}
    {g : Pt → Matrix (Fin 4) (Fin 4) ℝ} {u : Pt → Fin 4 → ℝ} {x : Pt}
    (hd : FieldDiffAt g u x) (c : ℝ) :
    velJetMatrix Γ g (fun y => c • u y) x = c • velJetMatrix Γ g u x := by
  have hL : ∀ y b, lowerField g (fun y => c • u y) y b = c * lowerField g u y b := by
    intro y b
    simp only [lowerField, Pi.smul_apply, smul_eq_mul, Finset.mul_sum]
    apply Finset.sum_congr rfl; intro i _
    ring
  ext a b
  simp only [velJetMatrix, Matrix.of_apply, Matrix.smul_apply, smul_eq_mul, velJet, hL]
  unfold pd
  rw [fderiv_const_mul (lowerField_differentiableAt hd b)]
  simp only [FunLike.coe_smul, Pi.smul_apply, smul_eq_mul, mul_sub, Finset.mul_sum]
  congr 1
  apply Finset.sum_congr rfl; intro i _
  ring

/-- T6 master theorem for an actual velocity field: every kinematic statement of CAS-03
holds for `D = ∇u` computed from the field, with `0 < c` explicit and `Q = ∇(c u) = c D`. -/
theorem velocity_jet_kinematics {Γ : Pt → Fin 4 → Fin 4 → Fin 4 → ℝ}
    {g : Pt → Matrix (Fin 4) (Fin 4) ℝ} {u : Pt → Fin 4 → ℝ} {x : Pt}
    {ginv : Matrix (Fin 4) (Fin 4) ℝ} {c : ℝ}
    (hd : FieldDiffAt g u x) (hcomp : MetricCompatibleAt Γ g x) (hsym : (g x)ᵀ = g x)
    (hinv : g x * ginv = 1) (hnorm : ∀ᶠ y in 𝓝 x, u y ⬝ᵥ (g y *ᵥ u y) = -1) (hc : 0 < c) :
    velJetMatrix Γ g u x *ᵥ u x = 0 ∧
    velJetMatrix Γ g (fun y => c • u y) x = c • velJetMatrix Γ g u x ∧
    velJetMatrix Γ g u x = c⁻¹ • velJetMatrix Γ g (fun y => c • u y) x ∧
    expansion c ginv (g x) (u x) (velJetMatrix Γ g u x) =
      c * contract (hUp ginv (u x)) (velJetMatrix Γ g u x) ∧
    c • spatialJet (g x) (u x) (velJetMatrix Γ g u x) =
      shear c ginv (g x) (u x) (velJetMatrix Γ g u x) +
        (expansion c ginv (g x) (u x) (velJetMatrix Γ g u x) / 3) • hDown (g x) (u x) +
        vorticity c (g x) (u x) (velJetMatrix Γ g u x) ∧
    (shear c ginv (g x) (u x) (velJetMatrix Γ g u x))ᵀ =
      shear c ginv (g x) (u x) (velJetMatrix Γ g u x) ∧
    contract ginv (shear c ginv (g x) (u x) (velJetMatrix Γ g u x)) = 0 ∧
    shear c ginv (g x) (u x) (velJetMatrix Γ g u x) *ᵥ u x = 0 ∧
    (vorticity c (g x) (u x) (velJetMatrix Γ g u x))ᵀ =
      -vorticity c (g x) (u x) (velJetMatrix Γ g u x) ∧
    vorticity c (g x) (u x) (velJetMatrix Γ g u x) *ᵥ u x = 0 ∧
    u x ⬝ᵥ acceleration c (u x) (velJetMatrix Γ g u x) = 0 ∧
    acceleration c (u x) (velJetMatrix Γ g u x) =
      (c • u x) ᵥ* velJetMatrix Γ g (fun y => c • u y) x ∧
    c ^ 2 • velJetMatrix Γ g u x =
      c • (shear c ginv (g x) (u x) (velJetMatrix Γ g u x) +
        (expansion c ginv (g x) (u x) (velJetMatrix Γ g u x) / 3) • hDown (g x) (u x) +
        vorticity c (g x) (u x) (velJetMatrix Γ g u x)) -
      vecMulVec (g x *ᵥ u x) (acceleration c (u x) (velJetMatrix Γ g u x)) := by
  have hu : u x ⬝ᵥ (g x *ᵥ u x) = -1 := hnorm.self_of_nhds
  have hD := velJet_mulVec_u hd hcomp hsym hnorm
  have hQ := velJetMatrix_smul (Γ := Γ) hd c
  have hP := pointwise_kinematics (ginv := ginv) hsym hinv hu hc _ hD
  refine ⟨hD, hQ, ?_, hP.1, hP.2.2.1, hP.2.2.2.1, hP.2.2.2.2.1, hP.2.2.2.2.2.1,
    hP.2.2.2.2.2.2.2.1, hP.2.2.2.2.2.2.2.2.1, hP.2.2.2.2.2.2.2.2.2.2.2.2.2.1, ?_,
    hP.2.2.2.2.2.2.2.2.2.2.2.2.2.2.1⟩
  · rw [hQ]; exact D_eq_inv_smul_Q hc _
  · rw [hQ]; exact (kinematics_in_Q hsym hinv hu c _).2.2.2.2

/-! ## T7: Minkowski instances, PORT-CAS-01 reuse, negative controls -/

/-- Constant Minkowski metric field (PORT-CAS-01 `eta`, signature `(-,+,+,+)`). -/
def gMink : Pt → Matrix (Fin 4) (Fin 4) ℝ := fun _ => PortCas01.eta

/-- Zero connection (Cartesian Minkowski chart). -/
def Γ0 : Pt → Fin 4 → Fin 4 → Fin 4 → ℝ := fun _ _ _ _ => 0

theorem eta_symm : PortCas01.etaᵀ = PortCas01.eta := by
  ext i j; fin_cases i <;> fin_cases j <;> simp [PortCas01.eta]

theorem eta_mul_eta : PortCas01.eta * PortCas01.eta = 1 := by
  ext i j; fin_cases i <;> fin_cases j <;>
    simp [PortCas01.eta, Matrix.mul_apply, Fin.sum_univ_four]

theorem mink_compatible (x : Pt) : MetricCompatibleAt Γ0 gMink x := by
  intro a b c
  simp [pd, gMink, Γ0]

/-- PORT-CAS-01 reuse: every subluminal boost four-velocity is admissible. -/
theorem boost_admissible (x y z : ℝ) (hs : PortCas01.s x y z < 1) :
    PortCas01.fourVelocity x y z ⬝ᵥ (PortCas01.eta *ᵥ PortCas01.fourVelocity x y z) = -1 :=
  (PortCas01.future_mass_shell x y z hs).2

/-- Arbitrary subluminal `β` and arbitrary admissible `D` in Minkowski space. -/
theorem boost_kinematics (x y z : ℝ) (hs : PortCas01.s x y z < 1) {c : ℝ} (hc : 0 < c)
    (D : Matrix (Fin 4) (Fin 4) ℝ) (hD : D *ᵥ PortCas01.fourVelocity x y z = 0) :
    trace (projUp PortCas01.eta (PortCas01.fourVelocity x y z)) = 3 ∧
    trace (PortCas01.eta * hDown PortCas01.eta (PortCas01.fourVelocity x y z)) = 3 ∧
    contract PortCas01.eta (shear c PortCas01.eta PortCas01.eta
      (PortCas01.fourVelocity x y z) D) = 0 ∧
    PortCas01.fourVelocity x y z ⬝ᵥ acceleration c (PortCas01.fourVelocity x y z) D = 0 ∧
    c ^ 2 • D = c • (shear c PortCas01.eta PortCas01.eta (PortCas01.fourVelocity x y z) D +
      (expansion c PortCas01.eta PortCas01.eta (PortCas01.fourVelocity x y z) D / 3) •
        hDown PortCas01.eta (PortCas01.fourVelocity x y z) +
      vorticity c PortCas01.eta (PortCas01.fourVelocity x y z) D) -
      vecMulVec (PortCas01.eta *ᵥ PortCas01.fourVelocity x y z)
        (acceleration c (PortCas01.fourVelocity x y z) D) ∧
    D = c⁻¹ • (c • D) := by
  have hu := boost_admissible x y z hs
  exact ⟨trace_projUp hu, trace_ginv_hDown eta_mul_eta hu,
    shear_traceless eta_symm eta_mul_eta hu c D, acceleration_orthogonal c D hD,
    reconstruction c D hD, D_eq_inv_smul_Q hc D⟩

/-- `β = 0`: the rest-frame projector is `diag(0,1,1,1)`; no singular denominator occurs. -/
theorem beta_zero_hDown :
    hDown PortCas01.eta (PortCas01.fourVelocity 0 0 0) = Matrix.diagonal ![0, 1, 1, 1] := by
  rw [PortCas01.zero_fourVelocity]
  ext i j; fin_cases i <;> fin_cases j <;>
    simp [hDown, PortCas01.eta, PortCas01.e0, mulVec, dotProduct, Fin.sum_univ_four,
      vecMulVec_apply, Matrix.diagonal]

/-- Rapidity field `φ(y) = 2 y⁰ + 3 y¹ + 5 y²`. -/
def phiEx (y : Pt) : ℝ := 2 * y 0 + 3 * y 1 + 5 * y 2

/-- Explicit smooth unit timelike velocity field `u = (cosh φ, sinh φ, 0, 0)`. -/
noncomputable def uEx (y : Pt) : Fin 4 → ℝ := ![Real.cosh (phiEx y), Real.sinh (phiEx y), 0, 0]

theorem hasFDerivAt_phiEx (y : Pt) :
    HasFDerivAt phiEx
      ((2 : ℝ) • ContinuousLinearMap.proj (R := ℝ) (φ := fun _ : Fin 4 => ℝ) 0 +
        (3 : ℝ) • ContinuousLinearMap.proj (R := ℝ) (φ := fun _ : Fin 4 => ℝ) 1 +
        (5 : ℝ) • ContinuousLinearMap.proj (R := ℝ) (φ := fun _ : Fin 4 => ℝ) 2) y :=
  (((hasFDerivAt_apply (𝕜 := ℝ) 0 y).const_mul 2).add
    ((hasFDerivAt_apply (𝕜 := ℝ) 1 y).const_mul 3)).add
    ((hasFDerivAt_apply (𝕜 := ℝ) 2 y).const_mul 5)

theorem uEx_comp0 : (fun y => uEx y 0) = fun y => Real.cosh (phiEx y) := by
  funext y; simp [uEx]
theorem uEx_comp1 : (fun y => uEx y 1) = fun y => Real.sinh (phiEx y) := by
  funext y; simp [uEx]
theorem uEx_comp2 : (fun y => uEx y 2) = fun _ => (0 : ℝ) := by
  funext y; simp [uEx]
theorem uEx_comp3 : (fun y => uEx y 3) = fun _ => (0 : ℝ) := by
  funext y; simp [uEx]

theorem uEx_diff (x : Pt) : FieldDiffAt gMink uEx x := by
  refine ⟨fun b c => by simp [gMink], fun c => ?_⟩
  fin_cases c
  · show DifferentiableAt ℝ (fun y => uEx y 0) x
    rw [uEx_comp0]; exact (hasFDerivAt_phiEx x).cosh.differentiableAt
  · show DifferentiableAt ℝ (fun y => uEx y 1) x
    rw [uEx_comp1]; exact (hasFDerivAt_phiEx x).sinh.differentiableAt
  · show DifferentiableAt ℝ (fun y => uEx y 2) x
    rw [uEx_comp2]; exact differentiableAt_const _
  · show DifferentiableAt ℝ (fun y => uEx y 3) x
    rw [uEx_comp3]; exact differentiableAt_const _

theorem uEx_norm (y : Pt) : uEx y ⬝ᵥ (gMink y *ᵥ uEx y) = -1 := by
  simp [uEx, gMink, PortCas01.eta, dotProduct, mulVec, Fin.sum_univ_four]
  linear_combination (-1 : ℝ) * Real.cosh_sq (phiEx y)

/-- The actual `∇u` of the explicit field obeys `D·u = 0` at every point (any `β`). -/
theorem uEx_rest (x : Pt) : velJetMatrix Γ0 gMink uEx x *ᵥ uEx x = 0 :=
  velJet_mulVec_u (uEx_diff x) (mink_compatible x) eta_symm
    (Filter.Eventually.of_forall uEx_norm)

/-- Concrete Jacobian at the origin (where `β = 0`). -/
def Dex : Matrix (Fin 4) (Fin 4) ℝ :=
  !![0, 2, 0, 0;
     0, 3, 0, 0;
     0, 5, 0, 0;
     0, 0, 0, 0]

theorem uEx_zero : uEx 0 = PortCas01.e0 := by
  funext i; fin_cases i <;> simp [uEx, phiEx, PortCas01.e0]

theorem pd_uEx0 (a : Fin 4) : pd (fun y => uEx y 0) 0 a = 0 := by
  unfold pd
  rw [uEx_comp0, ((hasFDerivAt_phiEx 0).cosh).fderiv]
  simp [phiEx]

theorem pd_uEx1 (a : Fin 4) : pd (fun y => uEx y 1) 0 a = ![2, 3, 5, 0] a := by
  unfold pd
  rw [uEx_comp1, ((hasFDerivAt_phiEx 0).sinh).fderiv]
  fin_cases a <;> simp [phiEx, Pi.single_apply]

theorem pd_uEx2 (a : Fin 4) : pd (fun y => uEx y 2) 0 a = 0 := by
  unfold pd; rw [uEx_comp2]; simp

theorem pd_uEx3 (a : Fin 4) : pd (fun y => uEx y 3) 0 a = 0 := by
  unfold pd; rw [uEx_comp3]; simp

theorem uEx_jet_zero : velJetMatrix Γ0 gMink uEx 0 = Dex := by
  ext a b
  rw [velJetMatrix, Matrix.of_apply, velJet_eq_lower (uEx_diff 0) (mink_compatible 0)]
  simp only [nablaUp, Γ0, zero_mul, Finset.sum_const_zero, add_zero, Fin.sum_univ_four,
    pd_uEx0, pd_uEx1, pd_uEx2, pd_uEx3, gMink]
  fin_cases a <;> fin_cases b <;> simp [PortCas01.eta, Dex]

theorem spatialJet_Dex :
    spatialJet PortCas01.eta PortCas01.e0 Dex =
      !![0, 0, 0, 0; 0, 3, 0, 0; 0, 5, 0, 0; 0, 0, 0, 0] := by
  ext i j; fin_cases i <;> fin_cases j <;>
    simp [spatialJet, projDown, PortCas01.eta, PortCas01.e0, Dex, Matrix.mul_apply,
      Fin.sum_univ_four, mulVec, dotProduct, vecMulVec_apply, Matrix.transpose_apply]

theorem hDown_e0 :
    hDown PortCas01.eta PortCas01.e0 = !![0, 0, 0, 0; 0, 1, 0, 0; 0, 0, 1, 0; 0, 0, 0, 1] := by
  ext i j; fin_cases i <;> fin_cases j <;>
    simp [hDown, PortCas01.eta, PortCas01.e0, mulVec, dotProduct, Fin.sum_univ_four,
      vecMulVec_apply]

/-- Concrete physical kinematics of the explicit field at the origin, `c = 2`:
`θ = 6`, `σ = [[0,0,0,0],[0,4,5,0],[0,5,-2,0],[0,0,0,-2]]`,
`ω = [[0,0,0,0],[0,0,-5,0],[0,5,0,0],[0,0,0,0]]`, `A = (0,8,0,0)`. -/
theorem uEx_kinematics_zero :
    expansion 2 PortCas01.eta PortCas01.eta (uEx 0) (velJetMatrix Γ0 gMink uEx 0) = 6 ∧
    shear 2 PortCas01.eta PortCas01.eta (uEx 0) (velJetMatrix Γ0 gMink uEx 0) =
      !![0, 0, 0, 0; 0, 4, 5, 0; 0, 5, -2, 0; 0, 0, 0, -2] ∧
    vorticity 2 PortCas01.eta (uEx 0) (velJetMatrix Γ0 gMink uEx 0) =
      !![0, 0, 0, 0; 0, 0, -5, 0; 0, 5, 0, 0; 0, 0, 0, 0] ∧
    acceleration 2 (uEx 0) (velJetMatrix Γ0 gMink uEx 0) = ![0, 8, 0, 0] := by
  rw [uEx_jet_zero, uEx_zero]
  have hθ : expansion 2 PortCas01.eta PortCas01.eta PortCas01.e0 Dex = 6 := by
    rw [expansion, spatialJet_Dex]
    simp [contract, PortCas01.eta, Fin.sum_univ_four]
    norm_num
  refine ⟨hθ, ?_, ?_, ?_⟩
  · rw [shear, hθ, spatialJet_Dex, hDown_e0]
    ext i j
    simp only [symPart, Matrix.sub_apply, Matrix.smul_apply, Matrix.add_apply,
      Matrix.transpose_apply, smul_eq_mul]
    fin_cases i <;> fin_cases j <;> norm_num
  · rw [vorticity, spatialJet_Dex]
    ext i j
    simp only [skewPart, Matrix.sub_apply, Matrix.smul_apply, Matrix.transpose_apply, smul_eq_mul]
    fin_cases i <;> fin_cases j <;> norm_num
  · funext j; fin_cases j <;>
      simp [acceleration, Dex, PortCas01.e0, vecMul, dotProduct, Fin.sum_univ_four] <;> norm_num

/-- Constant rest field `u ≡ e0`. -/
def uRest : Pt → Fin 4 → ℝ := fun _ => PortCas01.e0

theorem uRest_jet_zero : velJetMatrix Γ0 gMink uRest 0 = 0 := by
  ext a b
  simp [velJetMatrix, velJet, lowerField, uRest, gMink, Γ0, pd]

/-- Negative control (pitfall: finite velocity does not determine the jet): two admissible
fields with the same velocity at the origin have different expansion. -/
theorem same_velocity_different_jet :
    uRest 0 = uEx 0 ∧
    (∀ y, uRest y ⬝ᵥ (gMink y *ᵥ uRest y) = -1) ∧
    (∀ y, uEx y ⬝ᵥ (gMink y *ᵥ uEx y) = -1) ∧
    expansion 2 PortCas01.eta PortCas01.eta (uRest 0) (velJetMatrix Γ0 gMink uRest 0) = 0 ∧
    expansion 2 PortCas01.eta PortCas01.eta (uEx 0) (velJetMatrix Γ0 gMink uEx 0) = 6 := by
  refine ⟨uEx_zero.symm, ?_, uEx_norm, ?_, uEx_kinematics_zero.1⟩
  · intro y; simp [uRest, gMink, PortCas01.eta, PortCas01.e0, dotProduct, mulVec,
      Fin.sum_univ_four]
  · rw [uRest_jet_zero]; simp [expansion, contract, spatialJet]

/-- Non-normalized field `u = (1 + y⁰, 0, 0, 0)`; `g(u,u) = -1` holds at the origin only. -/
def uBad (y : Pt) : Fin 4 → ℝ := ![1 + y 0, 0, 0, 0]

/-- Negative control: pointwise normalization alone does not give `D·u = 0`; the
neighbourhood (differentiated) constraint is necessary. -/
theorem pointwise_normalization_insufficient :
    uBad 0 ⬝ᵥ (gMink 0 *ᵥ uBad 0) = -1 ∧
    FieldDiffAt gMink uBad 0 ∧ MetricCompatibleAt Γ0 gMink 0 ∧
    (velJetMatrix Γ0 gMink uBad 0 *ᵥ uBad 0) 0 = -1 := by
  have h0 : (fun y => uBad y 0) = fun y => 1 + y 0 := by funext y; simp [uBad]
  have hc : ∀ c : Fin 4, c ≠ 0 → (fun y => uBad y c) = fun _ => (0 : ℝ) := by
    intro c hc; funext y; fin_cases c <;> simp_all [uBad]
  have hdiff : FieldDiffAt gMink uBad 0 := by
    refine ⟨fun b c => by simp [gMink], fun c => ?_⟩
    by_cases h : c = 0
    · subst h; rw [h0]; exact ((hasFDerivAt_apply (𝕜 := ℝ) 0 (0 : Pt)).const_add 1).differentiableAt
    · rw [hc c h]; exact differentiableAt_const _
  have hpd0 : pd (fun y => uBad y 0) 0 0 = 1 := by
    unfold pd; rw [h0, ((hasFDerivAt_apply (𝕜 := ℝ) 0 (0 : Pt)).const_add 1).fderiv]
    simp
  refine ⟨?_, hdiff, mink_compatible 0, ?_⟩
  · simp [uBad, gMink, PortCas01.eta, dotProduct, mulVec, Fin.sum_univ_four]
  · have hb : uBad 0 = PortCas01.e0 := by funext i; fin_cases i <;> simp [uBad, PortCas01.e0]
    rw [hb]
    simp only [mulVec, dotProduct, velJetMatrix, Matrix.of_apply, Fin.sum_univ_four,
      PortCas01.e0]
    simp only [velJet_eq_lower hdiff (mink_compatible 0)]
    simp [nablaUp, Γ0, gMink, PortCas01.eta, Fin.sum_univ_four, hpd0]

end PORTCAS03VelocityJetDecomposition
