import Mathlib
import C01
import Proof
import G04AEigenline

/-! Pre-freeze signature probe: definitions and statement stubs only (`sorry` bodies).
This file is NOT a proof; it only checks that the frozen statements elaborate. -/

namespace G03A
open GRSTATCAS04 G04A
open scoped Topology ContDiff RealInnerProductSpace

/-! ## Bridge between the CAS-03-C01 representation and Vec4/Mat4 -/

def ofV (v : CAS03C01.V) : Vec4 := Fin.cons v.1 v.2

def toMixed (s : CAS03C01.SymCov) : Mat4 := fun a b => eta a * CAS03C01.toMatrix s a b

def matVecL (t : Mat4) : Vec4 →ₗ[ℝ] Vec4 where
  toFun := matVec t
  map_add' := matVec_add t
  map_smul' := fun r v => matVec_smul t v r

def DactL (s : CAS03C01.SymCov) : CAS03C01.W →ₗ[ℝ] CAS03C01.W where
  toFun := CAS03C01.Dact s CAS03C01.e0
  map_add' := sorry
  map_smul' := sorry

def kerDSub (s : CAS03C01.SymCov) : Submodule ℝ CAS03C01.W := LinearMap.ker (DactL s)

theorem toMixed_selfAdjoint (s : CAS03C01.SymCov) : EtaSelfAdjoint (toMixed s) := sorry

theorem toMixed_matVec (s : CAS03C01.SymCov) (v : CAS03C01.V) :
    matVec (toMixed s) (ofV v) = ofV (CAS03C01.mixed s v) := sorry

theorem ofV_mass (v : CAS03C01.V) : lorentzDot (ofV v) (ofV v) = CAS03C01.mass v := sorry

/-! ## A: the source premise -/

def TimelikeEigenPremise (s : CAS03C01.SymCov) : Prop :=
  ∃ (v : CAS03C01.V) (c : ℝ), CAS03C01.mass v < 0 ∧ CAS03C01.mixed s v = CAS03C01.smulV c v

theorem A1_premise_iff_geodesic (s : CAS03C01.SymCov) :
    TimelikeEigenPremise s ↔
      ∃ u : CAS03C01.V, CAS03C01.futureUnit u ∧ CAS03C01.bAct s u u = (0, CAS03C01.zeroW) := sorry

theorem A1_premise_iff_mixed (s : CAS03C01.SymCov) :
    TimelikeEigenPremise s ↔
      ∃ (v : Vec4) (c : ℝ), lorentzDot v v < 0 ∧ matVec (toMixed s) v = c • v := sorry

theorem A2_normalize (t : Mat4) (v : Vec4) (μ : ℝ) (hv : lorentzDot v v < 0)
    (he : matVec t v = μ • v) :
    ∃ (u : Vec4) (k : ℝ), k ≠ 0 ∧ u = k • v ∧ matVec t u = μ • u ∧
      lorentzDot u u = -1 ∧ 0 < u 0 := sorry

theorem A2_timelike_eigenvalue_unique (t : Mat4) (hsym : EtaSelfAdjoint t) (v v' : Vec4)
    (μ μ' : ℝ) (hv : lorentzDot v v < 0) (hv' : lorentzDot v' v' < 0)
    (he : matVec t v = μ • v) (he' : matVec t v' = μ' • v') : μ = μ' := sorry

def sRot : CAS03C01.SymCov where
  a := 0
  b := ![1, 0, 0]
  d := 0
  d_symm := Matrix.isSymm_zero

def sNull : CAS03C01.SymCov where
  a := 1
  b := ![1, 0, 0]
  d := Matrix.diagonal ![1, 0, 0]
  d_symm := Matrix.isSymm_diagonal _

theorem A3_rot_no_timelike : EtaSelfAdjoint (toMixed sRot) ∧ ¬ TimelikeEigenPremise sRot := sorry

theorem A3_null_no_timelike : EtaSelfAdjoint (toMixed sNull) ∧ ¬ TimelikeEigenPremise sNull := sorry

theorem A3_selfadjoint_insufficient :
    ∃ s : CAS03C01.SymCov, EtaSelfAdjoint (toMixed s) ∧ ¬ TimelikeEigenPremise s := sorry

/-! ## B: the rest space of a timelike vector is a genuine inner-product space -/

structure Timelike where
  vec : Vec4
  timelike : lorentzDot vec vec < 0

def lorentzFormL (u : Vec4) : Vec4 →ₗ[ℝ] ℝ where
  toFun := lorentzDot u
  map_add' := lorentzDot_add_right u
  map_smul' := fun r v => by simp [lorentzDot_smul_right]

def restSub (u : Vec4) : Submodule ℝ Vec4 := LinearMap.ker (lorentzFormL u)

def RestSpace (τ : Timelike) : Type := ↥(restSub τ.vec)

instance (τ : Timelike) : AddCommGroup (RestSpace τ) :=
  inferInstanceAs (AddCommGroup ↥(restSub τ.vec))

instance (τ : Timelike) : Module ℝ (RestSpace τ) :=
  inferInstanceAs (Module ℝ ↥(restSub τ.vec))

instance (τ : Timelike) : FiniteDimensional ℝ (RestSpace τ) :=
  inferInstanceAs (FiniteDimensional ℝ ↥(restSub τ.vec))

def RestSpace.val {τ : Timelike} (x : RestSpace τ) : Vec4 :=
  Subtype.val (p := fun w => w ∈ restSub τ.vec) x

def RestSpace.mk {τ : Timelike} (w : Vec4) (h : lorentzDot τ.vec w = 0) : RestSpace τ :=
  (⟨w, h⟩ : ↥(restSub τ.vec))

theorem B1_rest_posdef (u w : Vec4) (hu : lorentzDot u u < 0) (ho : lorentzDot u w = 0)
    (hw : w ≠ 0) : 0 < lorentzDot w w := sorry

instance (τ : Timelike) : Inner ℝ (RestSpace τ) := ⟨fun x y => lorentzDot x.val y.val⟩

def restCore (τ : Timelike) : InnerProductSpace.Core ℝ (RestSpace τ) where
  toInner := inferInstance
  conj_inner_symm := sorry
  re_inner_nonneg := sorry
  add_left := sorry
  smul_left := sorry
  definite := sorry

noncomputable instance (τ : Timelike) : NormedAddCommGroup (RestSpace τ) :=
  @InnerProductSpace.Core.toNormedAddCommGroup ℝ (RestSpace τ) _ _ _ (restCore τ)

noncomputable instance (τ : Timelike) : InnerProductSpace ℝ (RestSpace τ) :=
  InnerProductSpace.ofCore _

theorem B2_inner_eq (τ : Timelike) (x y : RestSpace τ) : ⟪x, y⟫_ℝ = lorentzDot x.val y.val := sorry

theorem B2_posdef (τ : Timelike) (x : RestSpace τ) (hx : x ≠ 0) : 0 < ⟪x, x⟫_ℝ := sorry

theorem B2_finrank (τ : Timelike) : Module.finrank ℝ (RestSpace τ) = 3 := sorry

theorem B2_val_injective (τ : Timelike) : Function.Injective (RestSpace.val (τ := τ)) := sorry

theorem B2_val_mem (τ : Timelike) (x : RestSpace τ) : lorentzDot τ.vec x.val = 0 := sorry

/-! ## C: restricted self-adjoint operator, orthonormal eigenbasis, kernel dimension -/

theorem restOp_mem (τ : Timelike) (t : Mat4) (s : ℝ) (hsym : EtaSelfAdjoint t)
    (he : matVec t τ.vec = s • τ.vec) (w : Vec4) (hw : lorentzDot τ.vec w = 0) :
    lorentzDot τ.vec (matVec t w) = 0 := sorry

def restOp (τ : Timelike) (t : Mat4) (s : ℝ) (hsym : EtaSelfAdjoint t)
    (he : matVec t τ.vec = s • τ.vec) : RestSpace τ →ₗ[ℝ] RestSpace τ where
  toFun x := RestSpace.mk (matVec t x.val) (restOp_mem τ t s hsym he x.val (B2_val_mem τ x))
  map_add' := sorry
  map_smul' := sorry

theorem C0_restOp_val (τ : Timelike) (t : Mat4) (s : ℝ) (hsym : EtaSelfAdjoint t)
    (he : matVec t τ.vec = s • τ.vec) (x : RestSpace τ) :
    (restOp τ t s hsym he x).val = matVec t x.val := sorry

theorem C1_restOp_symmetric (τ : Timelike) (t : Mat4) (s : ℝ) (hsym : EtaSelfAdjoint t)
    (he : matVec t τ.vec = s • τ.vec) : (restOp τ t s hsym he).IsSymmetric := sorry

noncomputable def restEigenbasis (τ : Timelike) (t : Mat4) (s : ℝ) (hsym : EtaSelfAdjoint t)
    (he : matVec t τ.vec = s • τ.vec) : OrthonormalBasis (Fin 3) ℝ (RestSpace τ) :=
  (C1_restOp_symmetric τ t s hsym he).eigenvectorBasis (B2_finrank τ)

noncomputable def restEigenvalues (τ : Timelike) (t : Mat4) (s : ℝ) (hsym : EtaSelfAdjoint t)
    (he : matVec t τ.vec = s • τ.vec) : Fin 3 → ℝ :=
  (C1_restOp_symmetric τ t s hsym he).eigenvalues (B2_finrank τ)

theorem C1_rest_spectral (τ : Timelike) (t : Mat4) (s : ℝ) (hsym : EtaSelfAdjoint t)
    (he : matVec t τ.vec = s • τ.vec) :
    (∀ i, matVec t (restEigenbasis τ t s hsym he i).val =
      restEigenvalues τ t s hsym he i • (restEigenbasis τ t s hsym he i).val) ∧
    (∀ i j, lorentzDot (restEigenbasis τ t s hsym he i).val (restEigenbasis τ t s hsym he j).val =
      if i = j then 1 else 0) ∧
    (∀ i, lorentzDot τ.vec (restEigenbasis τ t s hsym he i).val = 0) := sorry

theorem C1_restEigenbasis_G04A (τ : Timelike) (t : Mat4) (s : ℝ) (hsym : EtaSelfAdjoint t)
    (he : matVec t τ.vec = s • τ.vec) :
    RestEigenbasis t τ.vec (fun i => (restEigenbasis τ t s hsym he i).val)
      (restEigenvalues τ t s hsym he) := sorry

theorem C2_eigenspace_split (τ : Timelike) (t : Mat4) (s : ℝ) (hsym : EtaSelfAdjoint t)
    (he : matVec t τ.vec = s • τ.vec) (v : Vec4) :
    v ∈ Module.End.eigenspace (matVecL t) s ↔
      ∃ (a : ℝ) (w : RestSpace τ), w ∈ Module.End.eigenspace (restOp τ t s hsym he) s ∧
        v = a • τ.vec + w.val := sorry

theorem C2_finrank (τ : Timelike) (t : Mat4) (s : ℝ) (hsym : EtaSelfAdjoint t)
    (he : matVec t τ.vec = s • τ.vec) :
    Module.finrank ℝ (Module.End.eigenspace (matVecL t) s) =
      1 + Module.finrank ℝ (Module.End.eigenspace (restOp τ t s hsym he) s) ∧
    Module.finrank ℝ (Module.End.eigenspace (restOp τ t s hsym he) s) =
      (Finset.univ.filter fun i => restEigenvalues τ t s hsym he i = s).card := sorry

theorem C3_isolation_iff (τ : Timelike) (t : Mat4) (s : ℝ) (hsym : EtaSelfAdjoint t)
    (he : matVec t τ.vec = s • τ.vec) :
    (RestGapInjective t τ.vec (-s) ↔ Module.End.eigenspace (restOp τ t s hsym he) s = ⊥) ∧
    (RestGapInjective t τ.vec (-s) ↔ ∀ i, restEigenvalues τ t s hsym he i ≠ s) ∧
    (RestGapInjective t τ.vec (-s) ↔
      Module.finrank ℝ (Module.End.eigenspace (matVecL t) s) = 1) := sorry

def e0T : Timelike := ⟨ofV CAS03C01.e0, sorry⟩

theorem C4_C01_rest_eigen (s : CAS03C01.SymCov)
    (hrest : CAS03C01.bAct s CAS03C01.e0 CAS03C01.e0 = (0, CAS03C01.zeroW)) :
    matVec (toMixed s) e0T.vec = CAS03C01.st s CAS03C01.e0 • e0T.vec := sorry

theorem C4_C01_kernel_bridge (s : CAS03C01.SymCov)
    (hrest : CAS03C01.bAct s CAS03C01.e0 CAS03C01.e0 = (0, CAS03C01.zeroW)) :
    (∀ w : CAS03C01.W, CAS03C01.kerD s w ↔
      ∃ x ∈ Module.End.eigenspace (restOp e0T (toMixed s) (CAS03C01.st s CAS03C01.e0)
          (toMixed_selfAdjoint s) (C4_C01_rest_eigen s hrest)) (CAS03C01.st s CAS03C01.e0),
        x.val = ofV (0, w)) ∧
    Module.finrank ℝ (kerDSub s) =
      (Finset.univ.filter fun i => restEigenvalues e0T (toMixed s) (CAS03C01.st s CAS03C01.e0)
          (toMixed_selfAdjoint s) (C4_C01_rest_eigen s hrest) i = CAS03C01.st s CAS03C01.e0).card ∧
    Module.finrank ℝ (Module.End.eigenspace (matVecL (toMixed s)) (CAS03C01.st s CAS03C01.e0)) =
      1 + Module.finrank ℝ (kerDSub s) := sorry

theorem C4_C01_fibre (s : CAS03C01.SymCov)
    (hrest : CAS03C01.bAct s CAS03C01.e0 CAS03C01.e0 = (0, CAS03C01.zeroW))
    (hexp : CAS03C01.zeroExpansion s CAS03C01.e0) (v : CAS03C01.V) :
    CAS03C01.fibre s v ↔ ∃ w : CAS03C01.W, w ∈ kerDSub s ∧ v = CAS03C01.phi w := sorry

theorem C5_C01_isolation_iff_unique_velocity (s : CAS03C01.SymCov)
    (hrest : CAS03C01.bAct s CAS03C01.e0 CAS03C01.e0 = (0, CAS03C01.zeroW))
    (hexp : CAS03C01.zeroExpansion s CAS03C01.e0) :
    RestGapInjective (toMixed s) e0T.vec (-(CAS03C01.st s CAS03C01.e0)) ↔
      ∀ v, CAS03C01.fibre s v ↔ v = CAS03C01.e0 := sorry

theorem C6_C01_controls :
    RestGapInjective (toMixed (CAS03C01.diagonalExample CAS03C01.qPoint)) e0T.vec
      (-(CAS03C01.st (CAS03C01.diagonalExample CAS03C01.qPoint) CAS03C01.e0)) ∧
    ¬ RestGapInjective (toMixed (CAS03C01.diagonalExample CAS03C01.qLine)) e0T.vec
      (-(CAS03C01.st (CAS03C01.diagonalExample CAS03C01.qLine) CAS03C01.e0)) ∧
    Module.finrank ℝ (Module.End.eigenspace (matVecL (toMixed (CAS03C01.diagonalExample CAS03C01.qLine)))
      (CAS03C01.st (CAS03C01.diagonalExample CAS03C01.qLine) CAS03C01.e0)) = 2 := sorry

/-! ## D: conditional smooth local branch at an isolated (simple) timelike eigenvalue -/

structure TimelikeBranch {E : Type*} [NormedAddCommGroup E] [NormedSpace ℝ E]
    (n : ℕ) (Sfam : E → Mat4) (V : Set E) (u : E → Vec4) (s : E → ℝ) : Prop where
  isOpen : IsOpen V
  smooth_u : ContDiffOn ℝ n u V
  smooth_s : ContDiffOn ℝ n s V
  eigen : ∀ q ∈ V, matVec (Sfam q) (u q) = s q • u q
  unit : ∀ q ∈ V, lorentzDot (u q) (u q) = -1
  future : ∀ q ∈ V, 0 < u q 0
  isolated : ∀ q ∈ V, RestGapInjective (Sfam q) (u q) (-(s q))
  unique : ∀ q ∈ V, ∀ (v : Vec4) (μ : ℝ), matVec (Sfam q) v = μ • v →
    lorentzDot v v = -1 → 0 < v 0 → v = u q ∧ μ = s q

theorem D1_branch {E : Type*} [NormedAddCommGroup E] [NormedSpace ℝ E] [CompleteSpace E]
    (n : ℕ) (hn : 1 ≤ n) (D : Set E) (hD : IsOpen D) (Sfam : E → Mat4)
    (hS : ContDiffOn ℝ n Sfam D) (hsym : ∀ q ∈ D, EtaSelfAdjoint (Sfam q))
    (q0 : E) (hq0 : q0 ∈ D) (u0 : Vec4) (s0 : ℝ)
    (he0 : matVec (Sfam q0) u0 = s0 • u0) (hn0 : lorentzDot u0 u0 = -1) (hf0 : 0 < u0 0)
    (hiso : RestGapInjective (Sfam q0) u0 (-s0)) :
    ∃ (V : Set E) (u : E → Vec4) (s : E → ℝ),
      q0 ∈ V ∧ V ⊆ D ∧ u q0 = u0 ∧ s q0 = s0 ∧ TimelikeBranch n Sfam V u s := sorry

theorem D2_branch_vec4_via_G04A (n : ℕ) (hn : 1 ≤ n) (D : Set Vec4) (hD : IsOpen D)
    (Sfam : Vec4 → Mat4) (hS : ContDiffOn ℝ n Sfam D) (hsym : ∀ q ∈ D, EtaSelfAdjoint (Sfam q))
    (q0 : Vec4) (hq0 : q0 ∈ D) (u0 : Vec4) (s0 : ℝ)
    (he0 : matVec (Sfam q0) u0 = s0 • u0) (hn0 : lorentzDot u0 u0 = -1) (hf0 : 0 < u0 0)
    (hiso : RestGapInjective (Sfam q0) u0 (-s0)) :
    ∃ (V : Set Vec4) (u : Vec4 → Vec4) (s : Vec4 → ℝ),
      q0 ∈ V ∧ V ⊆ D ∧ u q0 = u0 ∧ s q0 = s0 ∧ TimelikeBranch n Sfam V u s := sorry

/-! ## E: controls separating rest-eigenvalue collision from loss of timelike isolation -/

def e0v : Vec4 := coordVec 0

def Rrot : Mat4 := ![![0, -1, 0, 0], ![1, 0, 0, 0], ![0, 0, 0, 0], ![0, 0, 0, 0]]

def Srot (q : Vec4) : Mat4 := q 1 • Rrot

def Pdiag : Mat4 := ![![0, 0, 0, 0], ![0, 1, 0, 0], ![0, 0, 1, 0], ![0, 0, 0, 1]]
def M1 : Mat4 := ![![0, 0, 0, 0], ![0, 1, 0, 0], ![0, 0, -1, 0], ![0, 0, 0, 0]]
def M2 : Mat4 := ![![0, 0, 0, 0], ![0, 0, 1, 0], ![0, 1, 0, 0], ![0, 0, 0, 0]]
def M3 : Mat4 := ![![0, 0, 0, 0], ![0, 0, 0, 0], ![0, 0, 0, 1], ![0, 0, 1, 0]]

def Scol (q : Vec4) : Mat4 := Pdiag + q 1 • M1 + q 2 • M2 + q 3 • M3

theorem E1_isolation_needed (n : ℕ) :
    ContDiff ℝ n Srot ∧ (∀ q, EtaSelfAdjoint (Srot q)) ∧
    matVec (Srot 0) e0v = (0 : ℝ) • e0v ∧ lorentzDot e0v e0v = -1 ∧ 0 < e0v 0 ∧
    ¬ RestGapInjective (Srot 0) e0v (-(0 : ℝ)) ∧
    ¬ ∃ V ∈ 𝓝 (0 : Vec4), ∀ q ∈ V, ∃ (v : Vec4) (μ : ℝ),
        lorentzDot v v < 0 ∧ matVec (Srot q) v = μ • v := sorry

theorem E2_collision_branch_exists (n : ℕ) (hn : 1 ≤ n) :
    ContDiff ℝ n Scol ∧ (∀ q, EtaSelfAdjoint (Scol q)) ∧
    (∀ w, lorentzDot e0v w = 0 → matVec (Scol 0) w = w) ∧
    RestGapInjective (Scol 0) e0v (-(0 : ℝ)) ∧
    ∃ (V : Set Vec4) (u : Vec4 → Vec4) (s : Vec4 → ℝ),
      (0 : Vec4) ∈ V ∧ u 0 = e0v ∧ s 0 = 0 ∧ TimelikeBranch n Scol V u s := sorry

theorem E3_no_continuous_rest_eigenvector :
    ¬ ∃ v : Vec4 → Vec4, ContinuousAt v 0 ∧ ∀ᶠ q in 𝓝 (0 : Vec4),
      lorentzDot e0v (v q) = 0 ∧ lorentzDot (v q) (v q) = 1 ∧
        ∃ μ : ℝ, matVec (Scol q) (v q) = μ • v q := sorry

end G03A
