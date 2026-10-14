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

theorem D3_branch_simple {E : Type*} [NormedAddCommGroup E] [NormedSpace ℝ E] [CompleteSpace E]
    (n : ℕ) (hn : 1 ≤ n) (D : Set E) (hD : IsOpen D) (Sfam : E → Mat4)
    (hS : ContDiffOn ℝ n Sfam D) (hsym : ∀ q ∈ D, EtaSelfAdjoint (Sfam q))
    (q0 : E) (hq0 : q0 ∈ D) (u0 : Vec4) (s0 : ℝ)
    (he0 : matVec (Sfam q0) u0 = s0 • u0) (hn0 : lorentzDot u0 u0 = -1) (hf0 : 0 < u0 0)
    (hsimple : Module.finrank ℝ (Module.End.eigenspace (matVecL (Sfam q0)) s0) = 1) :
    ∃ (V : Set E) (u : E → Vec4) (s : E → ℝ),
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
