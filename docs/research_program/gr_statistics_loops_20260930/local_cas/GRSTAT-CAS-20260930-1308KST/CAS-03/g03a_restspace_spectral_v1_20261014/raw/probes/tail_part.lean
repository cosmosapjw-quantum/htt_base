def e0T : Timelike := ⟨ofV CAS03C01.e0, by
  rw [ofV_mass]
  norm_num [CAS03C01.mass, CAS03C01.covPair, CAS03C01.g, CAS03C01.e0, CAS03C01.dot,
    CAS03C01.zeroW]⟩

theorem C4_C01_rest_eigen (s : CAS03C01.SymCov)
    (hrest : CAS03C01.bAct s CAS03C01.e0 CAS03C01.e0 = (0, CAS03C01.zeroW)) :
    matVec (toMixed s) e0T.vec = CAS03C01.st s CAS03C01.e0 • e0T.vec := by
  show matVec (toMixed s) (ofV CAS03C01.e0) = CAS03C01.st s CAS03C01.e0 • ofV CAS03C01.e0
  rw [toMixed_matVec, (CAS03C01.b_zero_iff_eigen s CAS03C01.e0).1 hrest, ofV_smulV]

/-- Spatial embedding `w ↦ (0, w)` of the C01 rest frame. -/
def ofW (w : CAS03C01.W) : Vec4 := ofV (0, w)

theorem ofW_add (w w' : CAS03C01.W) : ofW (w + w') = ofW w + ofW w' := by
  funext a
  cases a using Fin.cases with
  | zero => simp [ofW, ofV]
  | succ i => simp [ofW, ofV]

theorem ofW_smul (r : ℝ) (w : CAS03C01.W) : ofW (r • w) = r • ofW w := by
  funext a
  cases a using Fin.cases with
  | zero => simp [ofW, ofV]
  | succ i => simp [ofW, ofV]

theorem ofW_injective : Function.Injective ofW := by
  intro w w' h
  have := ofV_injective h
  exact congrArg Prod.snd this

theorem e0T_orth (w : CAS03C01.W) : lorentzDot e0T.vec (ofW w) = 0 := by
  show lorentzDot (ofV CAS03C01.e0) (ofV (0, w)) = 0
  simp [lorentzDot, ofV, Fin.sum_univ_succ, CAS03C01.e0, CAS03C01.zeroW]

theorem mem_kerDSub (s : CAS03C01.SymCov) (w : CAS03C01.W) :
    w ∈ kerDSub s ↔ CAS03C01.kerD s w := Iff.rfl

theorem kerD_iff_mixed (s : CAS03C01.SymCov)
    (hrest : CAS03C01.bAct s CAS03C01.e0 CAS03C01.e0 = (0, CAS03C01.zeroW)) (w : CAS03C01.W) :
    CAS03C01.kerD s w ↔
      CAS03C01.mixed s (0, w) = CAS03C01.smulV (CAS03C01.st s CAS03C01.e0) (0, w) := by
  obtain ⟨_, hb⟩ := CAS03C01.rest_time_column s hrest
  have hD : ∀ i, CAS03C01.Dact s CAS03C01.e0 w i =
      (∑ j, s.d i j * w j) - CAS03C01.st s CAS03C01.e0 * w i := by
    intro i
    simp [CAS03C01.Dact, CAS03C01.restD, sub_mul, Finset.sum_sub_distrib]
  constructor
  · intro hk
    apply Prod.ext
    · simp [CAS03C01.mixed, CAS03C01.g, CAS03C01.act, CAS03C01.smulV, hb, CAS03C01.dot,
        CAS03C01.zeroW]
    · funext i
      have h1 := congrFun hk i
      rw [hD] at h1
      simp only [CAS03C01.zeroW] at h1
      simp [CAS03C01.mixed, CAS03C01.g, CAS03C01.act, CAS03C01.smulV, hb, CAS03C01.zeroW]
      linarith
  · intro hm
    funext i
    have h1 := congrFun (congrArg Prod.snd hm) i
    simp [CAS03C01.mixed, CAS03C01.g, CAS03C01.act, CAS03C01.smulV, hb, CAS03C01.zeroW] at h1
    show CAS03C01.Dact s CAS03C01.e0 w i = 0
    rw [hD]; linarith

theorem kerD_iff_eig (s : CAS03C01.SymCov)
    (hrest : CAS03C01.bAct s CAS03C01.e0 CAS03C01.e0 = (0, CAS03C01.zeroW)) (w : CAS03C01.W) :
    CAS03C01.kerD s w ↔
      matVec (toMixed s) (ofW w) = CAS03C01.st s CAS03C01.e0 • ofW w := by
  rw [kerD_iff_mixed s hrest]
  constructor
  · intro h
    show matVec (toMixed s) (ofV (0, w)) = _ • ofV (0, w)
    rw [toMixed_matVec, h, ofV_smulV]
  · intro h
    apply ofV_injective
    rw [← toMixed_matVec, ofV_smulV]; exact h

/-- Linear identification of the C01 rest kernel with the rest kernel of `S - s_t`. -/
noncomputable def kerMap (s : CAS03C01.SymCov)
    (hrest : CAS03C01.bAct s CAS03C01.e0 CAS03C01.e0 = (0, CAS03C01.zeroW)) :
    kerDSub s →ₗ[ℝ] Module.End.eigenspace (restOp e0T (toMixed s) (CAS03C01.st s CAS03C01.e0)
      (toMixed_selfAdjoint s) (C4_C01_rest_eigen s hrest)) (CAS03C01.st s CAS03C01.e0) where
  toFun w := ⟨RestSpace.mk (ofW w.1) (e0T_orth w.1), by
    rw [mem_restEig_iff, RestSpace.mk_val]
    exact (kerD_iff_eig s hrest w.1).1 ((mem_kerDSub s w.1).1 w.2)⟩
  map_add' w w' := by
    apply Subtype.ext; apply B2_val_injective
    simp only [Submodule.coe_add, RestSpace.val_add, RestSpace.mk_val, ofW_add]
  map_smul' r w := by
    apply Subtype.ext; apply B2_val_injective
    simp only [Submodule.coe_smul, RestSpace.val_smul, RestSpace.mk_val, ofW_smul,
      RingHom.id_apply]

theorem kerMap_bijective (s : CAS03C01.SymCov)
    (hrest : CAS03C01.bAct s CAS03C01.e0 CAS03C01.e0 = (0, CAS03C01.zeroW)) :
    Function.Bijective (kerMap s hrest) := by
  constructor
  · intro w w' h
    have h1 : ((kerMap s hrest w : RestSpace e0T)).val =
        ((kerMap s hrest w' : RestSpace e0T)).val := by rw [h]
    change ofW w.1 = ofW w'.1 at h1
    exact Subtype.ext (ofW_injective h1)
  · rintro ⟨x, hx⟩
    rw [mem_restEig_iff] at hx
    have hx0 : x.val 0 = 0 := by
      have h := B2_val_mem e0T x
      change lorentzDot (ofV CAS03C01.e0) x.val = 0 at h
      simp [lorentzDot, ofV, Fin.sum_univ_succ, CAS03C01.e0, CAS03C01.zeroW, eta] at h
      exact h
    set w : CAS03C01.W := fun i => x.val i.succ with hw
    have hxw : ofW w = x.val := by
      funext a
      cases a using Fin.cases with
      | zero => simp [ofW, ofV, hx0]
      | succ i => rfl
    have hk : CAS03C01.kerD s w := (kerD_iff_eig s hrest w).2 (by rw [hxw]; exact hx)
    refine ⟨⟨w, (mem_kerDSub s w).2 hk⟩, ?_⟩
    apply Subtype.ext; apply B2_val_injective
    simp only [kerMap, LinearMap.coe_mk, AddHom.coe_mk, RestSpace.mk_val]
    exact hxw

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
      1 + Module.finrank ℝ (kerDSub s) := by
  obtain ⟨hf1, hf2⟩ := C2_finrank e0T (toMixed s) (CAS03C01.st s CAS03C01.e0)
    (toMixed_selfAdjoint s) (C4_C01_rest_eigen s hrest)
  have hiso := LinearEquiv.finrank_eq (LinearEquiv.ofBijective _ (kerMap_bijective s hrest))
  refine ⟨fun w => ⟨fun hk => ?_, ?_⟩, by rw [hiso, hf2], by rw [hf1, hiso]⟩
  · refine ⟨RestSpace.mk (ofW w) (e0T_orth w), ?_, rfl⟩
    rw [mem_restEig_iff, RestSpace.mk_val]
    exact (kerD_iff_eig s hrest w).1 hk
  · rintro ⟨x, hx, hxv⟩
    rw [mem_restEig_iff, hxv] at hx
    exact (kerD_iff_eig s hrest w).2 hx

theorem C4_C01_fibre (s : CAS03C01.SymCov)
    (hrest : CAS03C01.bAct s CAS03C01.e0 CAS03C01.e0 = (0, CAS03C01.zeroW))
    (hexp : CAS03C01.zeroExpansion s CAS03C01.e0) (v : CAS03C01.V) :
    CAS03C01.fibre s v ↔ ∃ w : CAS03C01.W, w ∈ kerDSub s ∧ v = CAS03C01.phi w := by
  rw [CAS03C01.fibre_chart s hrest hexp v]
  rfl

theorem C5_C01_isolation_iff_unique_velocity (s : CAS03C01.SymCov)
    (hrest : CAS03C01.bAct s CAS03C01.e0 CAS03C01.e0 = (0, CAS03C01.zeroW))
    (hexp : CAS03C01.zeroExpansion s CAS03C01.e0) :
    RestGapInjective (toMixed s) e0T.vec (-(CAS03C01.st s CAS03C01.e0)) ↔
      ∀ v, CAS03C01.fibre s v ↔ v = CAS03C01.e0 := by
  obtain ⟨_, hfin, _⟩ := C4_C01_kernel_bridge s hrest
  obtain ⟨_, hf2⟩ := C2_finrank e0T (toMixed s) (CAS03C01.st s CAS03C01.e0)
    (toMixed_selfAdjoint s) (C4_C01_rest_eigen s hrest)
  have h1 := (C3_isolation_iff e0T (toMixed s) (CAS03C01.st s CAS03C01.e0)
    (toMixed_selfAdjoint s) (C4_C01_rest_eigen s hrest)).1
  have h2 : RestGapInjective (toMixed s) e0T.vec (-(CAS03C01.st s CAS03C01.e0)) ↔
      kerDSub s = ⊥ := by
    rw [h1, ← Submodule.finrank_eq_zero, ← Submodule.finrank_eq_zero (S := kerDSub s), hf2, hfin]
  rw [h2, Submodule.eq_bot_iff]
  constructor
  · intro h v
    exact CAS03C01.zero_kernel_control s (fun w hw => h w ((mem_kerDSub s w).2 hw)) hrest hexp v
  · intro h w hw
    have hf : CAS03C01.fibre s (CAS03C01.phi w) :=
      (CAS03C01.fibre_chart s hrest hexp _).2 ⟨w, (mem_kerDSub s w).1 hw, rfl⟩
    have := congrArg Prod.snd ((h _).1 hf)
    have h3 : w = CAS03C01.zeroW := by simpa [CAS03C01.phi, CAS03C01.e0] using this
    exact h3

theorem C6_C01_controls :
    RestGapInjective (toMixed (CAS03C01.diagonalExample CAS03C01.qPoint)) e0T.vec
      (-(CAS03C01.st (CAS03C01.diagonalExample CAS03C01.qPoint) CAS03C01.e0)) ∧
    ¬ RestGapInjective (toMixed (CAS03C01.diagonalExample CAS03C01.qLine)) e0T.vec
      (-(CAS03C01.st (CAS03C01.diagonalExample CAS03C01.qLine) CAS03C01.e0)) ∧
    Module.finrank ℝ (Module.End.eigenspace (matVecL (toMixed (CAS03C01.diagonalExample CAS03C01.qLine)))
      (CAS03C01.st (CAS03C01.diagonalExample CAS03C01.qLine) CAS03C01.e0)) = 2 := by
  refine ⟨?_, ?_, ?_⟩
  · exact (C5_C01_isolation_iff_unique_velocity _ (CAS03C01.diagonalExample_rest _)
      CAS03C01.qPoint_trace).2 CAS03C01.qPoint_fibre
  · intro hg
    have h := (C5_C01_isolation_iff_unique_velocity _ (CAS03C01.diagonalExample_rest _)
      CAS03C01.qLine_trace).1 hg
    set w : CAS03C01.W := Pi.single 0 1 with hw
    have hk : CAS03C01.kerD (CAS03C01.diagonalExample CAS03C01.qLine) w :=
      (CAS03C01.qLine_kernel w).2 (by simp [hw])
    have hf : CAS03C01.fibre (CAS03C01.diagonalExample CAS03C01.qLine) (CAS03C01.phi w) :=
      (CAS03C01.fibre_chart _ (CAS03C01.diagonalExample_rest _) CAS03C01.qLine_trace _).2
        ⟨w, hk, rfl⟩
    have h2 := congrFun (congrArg Prod.snd ((h _).1 hf)) 0
    simp [CAS03C01.phi, CAS03C01.e0, CAS03C01.zeroW, hw] at h2
  · obtain ⟨_, _, h3⟩ := C4_C01_kernel_bridge (CAS03C01.diagonalExample CAS03C01.qLine)
      (CAS03C01.diagonalExample_rest _)
    rw [h3]
    have hspan : kerDSub (CAS03C01.diagonalExample CAS03C01.qLine) =
        Submodule.span ℝ {(Pi.single 0 1 : CAS03C01.W)} := by
      ext w
      rw [mem_kerDSub, CAS03C01.qLine_kernel, Submodule.mem_span_singleton]
      constructor
      · rintro ⟨h1, h2⟩
        refine ⟨w 0, ?_⟩
        funext i
        fin_cases i <;> simp [h1, h2]
      · rintro ⟨a, rfl⟩
        simp
    rw [hspan, finrank_span_singleton]
    intro h
    have := congrFun h 0
    simp at this

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

/-- The bordered eigen-system over an arbitrary parameter space:
`(q, (v, μ)) ↦ (S(q) v − μ v, η(v,v) + 1)`. -/
def borderedE {E : Type*} (Sfam : E → Mat4) (q : E × (Vec4 × ℝ)) : Vec4 × ℝ :=
  (matVec (Sfam q.1) q.2.1 - q.2.2 • q.2.1, lorentzDot q.2.1 q.2.1 + 1)

theorem borderedE_contDiffAt {E : Type*} [NormedAddCommGroup E] [NormedSpace ℝ E]
    {n : ℕ} {Sfam : E → Mat4} {x : E} (hT : ContDiffAt ℝ n Sfam x)
    (y : Vec4 × ℝ) : ContDiffAt ℝ n (borderedE Sfam) (x, y) := by
  have hTab : ∀ a b, ContDiffAt ℝ n (fun q : E × (Vec4 × ℝ) => Sfam q.1 a b) (x, y) := by
    intro a b
    have h1 : ContDiffAt ℝ n (fun z => Sfam z a b) x := contDiffAt_pi.1 (contDiffAt_pi.1 hT a) b
    exact h1.comp (x, y) contDiffAt_fst
  have hv : ∀ b, ContDiffAt ℝ n (fun q : E × (Vec4 × ℝ) => q.2.1 b) (x, y) := by
    intro b
    exact ((contDiff_apply ℝ ℝ b).contDiffAt).comp (x, y)
      (contDiffAt_fst.comp (x, y) contDiffAt_snd)
  have hm : ContDiffAt ℝ n (fun q : E × (Vec4 × ℝ) => q.2.2) (x, y) :=
    contDiffAt_snd.comp (x, y) contDiffAt_snd
  refine ContDiffAt.prodMk ?_ ?_
  · refine contDiffAt_pi.2 (fun a => ?_)
    have : (fun q : E × (Vec4 × ℝ) => (matVec (Sfam q.1) q.2.1 - q.2.2 • q.2.1) a) =
        fun q => (∑ b : Fin 4, Sfam q.1 a b * q.2.1 b) - q.2.2 * q.2.1 a := by
      funext q; simp [matVec]
    rw [this]
    exact (ContDiffAt.sum fun b _ => (hTab a b).mul (hv b)).sub (hm.mul (hv a))
  · have : (fun q : E × (Vec4 × ℝ) => lorentzDot q.2.1 q.2.1 + 1) =
        fun q => (∑ i : Fin 4, eta i * q.2.1 i * q.2.1 i) + 1 := by
      funext q; simp [lorentzDot]
    rw [this]
    exact (ContDiffAt.sum fun i _ => (contDiffAt_const.mul (hv i)).mul (hv i)).add contDiffAt_const

theorem borderedE_fderiv_inr {E : Type*} [NormedAddCommGroup E] [NormedSpace ℝ E]
    {Sfam : E → Mat4} {x : E} {y : Vec4 × ℝ}
    (hd : DifferentiableAt ℝ (borderedE Sfam) (x, y)) (w : Vec4) (m : ℝ) :
    (fderiv ℝ (borderedE Sfam) (x, y) ∘L ContinuousLinearMap.inr ℝ E (Vec4 × ℝ)) (w, m) =
      (matVec (Sfam x) w - y.2 • w - m • y.1, 2 * lorentzDot y.1 w) := by
  rw [ContinuousLinearMap.comp_apply, ContinuousLinearMap.inr_apply]
  set d : E × (Vec4 × ℝ) := (0, (w, m))
  have hline : HasDerivAt (fun s : ℝ => ((x, y) : E × (Vec4 × ℝ)) + s • d) d 0 := by
    simpa using ((hasDerivAt_id (0 : ℝ)).smul_const d).const_add ((x, y) : E × (Vec4 × ℝ))
  have h1 := hd.hasFDerivAt.comp_hasDerivAt_of_eq (0 : ℝ) hline (by simp)
  have h2 : HasDerivAt (borderedE Sfam ∘ fun s : ℝ => ((x, y) : E × (Vec4 × ℝ)) + s • d)
      (matVec (Sfam x) w - y.2 • w - m • y.1, 2 * lorentzDot y.1 w) 0 := by
    have hfun : (borderedE Sfam ∘ fun s : ℝ => ((x, y) : E × (Vec4 × ℝ)) + s • d) =
        fun s => (matVec (Sfam x) (y.1 + s • w) - (y.2 + s * m) • (y.1 + s • w),
          lorentzDot (y.1 + s • w) (y.1 + s • w) + 1) := by
      funext s; simp [borderedE, d]
    rw [hfun]
    refine HasDerivAt.prodMk ?_ ?_
    · refine hasDerivAt_pi.2 (fun a => ?_)
      have hc : (fun s : ℝ => (matVec (Sfam x) (y.1 + s • w) - (y.2 + s * m) • (y.1 + s • w)) a) =
          fun s => ((∑ b : Fin 4, Sfam x a b * y.1 b) - y.2 * y.1 a) +
            ((∑ b : Fin 4, Sfam x a b * w b) - y.2 * w a - m * y.1 a) * s + (-(m * w a)) * s ^ 2 := by
        funext s; simp [matVec, Fin.sum_univ_four]; ring
      rw [hc]
      have := quad_hasDerivAt ((∑ b : Fin 4, Sfam x a b * y.1 b) - y.2 * y.1 a)
        ((∑ b : Fin 4, Sfam x a b * w b) - y.2 * w a - m * y.1 a) (-(m * w a))
      exact this.congr_deriv (by simp [matVec])
    · have hc : (fun s : ℝ => lorentzDot (y.1 + s • w) (y.1 + s • w) + 1) =
          fun s => (lorentzDot y.1 y.1 + 1) + (2 * lorentzDot y.1 w) * s +
            (lorentzDot w w) * s ^ 2 := by
        funext s; simp only [lorentzDot_expand, Pi.add_apply, Pi.smul_apply, smul_eq_mul]; ring
      rw [hc]
      exact quad_hasDerivAt _ _ _
  exact h1.unique h2

theorem D1_branch {E : Type*} [NormedAddCommGroup E] [NormedSpace ℝ E] [CompleteSpace E]
    (n : ℕ) (hn : 1 ≤ n) (D : Set E) (hD : IsOpen D) (Sfam : E → Mat4)
    (hS : ContDiffOn ℝ n Sfam D) (hsym : ∀ q ∈ D, EtaSelfAdjoint (Sfam q))
    (q0 : E) (hq0 : q0 ∈ D) (u0 : Vec4) (s0 : ℝ)
    (he0 : matVec (Sfam q0) u0 = s0 • u0) (hn0 : lorentzDot u0 u0 = -1) (hf0 : 0 < u0 0)
    (hiso : RestGapInjective (Sfam q0) u0 (-s0)) :
    ∃ (V : Set E) (u : E → Vec4) (s : E → ℝ),
      q0 ∈ V ∧ V ⊆ D ∧ u q0 = u0 ∧ s q0 = s0 ∧ TimelikeBranch n Sfam V u s := by
  have hn0' : ((n : ℕ∞ω)) ≠ 0 := by exact_mod_cast (show n ≠ 0 by omega)
  have hninf : ((n : ℕ∞ω)) ≠ ∞ := by simp
  have hTat : ∀ x ∈ D, ContDiffAt ℝ n Sfam x := fun x hx => hS.contDiffAt (hD.mem_nhds hx)
  set p0 : E × (Vec4 × ℝ) := (q0, (u0, s0)) with hp0
  have hcd : ContDiffAt ℝ n (borderedE Sfam) p0 := borderedE_contDiffAt (hTat q0 hq0) _
  have hdiff : ∀ x ∈ D, ∀ y, DifferentiableAt ℝ (borderedE Sfam) (x, y) :=
    fun x hx y => (borderedE_contDiffAt (hTat x hx) y).differentiableAt (by exact_mod_cast hn0')
  have hinv : (fderiv ℝ (borderedE Sfam) p0 ∘L
      ContinuousLinearMap.inr ℝ E (Vec4 × ℝ)).IsInvertible := by
    apply isInvertible_of_injective
    rw [injective_iff_map_eq_zero]
    rintro ⟨w, m⟩ hwm
    rw [borderedE_fderiv_inr (hdiff q0 hq0 _)] at hwm
    have hwm' : ((matVec (Sfam q0) w - (-(-s0)) • w - m • u0, 2 * lorentzDot u0 w) :
        Vec4 × ℝ) = 0 := by rw [neg_neg]; exact hwm
    obtain ⟨hw, hm⟩ := bordered_inj (hsym q0 hq0) (by rw [neg_neg]; exact he0) hn0 hiso w m hwm'
    simp [hw, hm]
  set ψ := hcd.implicitFunction hn0' hinv with hψdef
  have hψ0 : ψ q0 = (u0, s0) := hcd.implicitFunction_apply_self hn0' hinv
  have hψcd : ContDiffAt ℝ n ψ q0 := hcd.contDiffAt_implicitFunction hn0' hinv
  have ev1 : ∀ᶠ x in 𝓝 q0, borderedE Sfam (x, ψ x) = borderedE Sfam p0 :=
    hcd.eventually_apply_implicitFunction hn0' hinv
  have ev2 : ∀ᶠ x in 𝓝 q0, ContDiffAt ℝ n ψ x := hψcd.eventually hninf
  have ev3 : ∀ᶠ x in 𝓝 q0, 0 < (ψ x).1 0 := by
    have hc : ContinuousAt (fun x => (ψ x).1 0) q0 :=
      (continuous_apply 0).continuousAt.comp (continuousAt_fst.comp hψcd.continuousAt)
    have ht := hc.tendsto
    simp only [hψ0] at ht
    exact ht.eventually_const_lt hf0
  have ev4 : ∀ᶠ x in 𝓝 q0, x ∈ D := hD.mem_nhds hq0
  have ev5 : ∀ᶠ x in 𝓝 q0,
      (fderiv ℝ (borderedE Sfam) (x, ψ x) ∘L
        ContinuousLinearMap.inr ℝ E (Vec4 × ℝ)).IsInvertible := by
    have hc : ContinuousAt (fun x =>
        fderiv ℝ (borderedE Sfam) (x, ψ x) ∘L ContinuousLinearMap.inr ℝ E (Vec4 × ℝ)) q0 := by
      have hpair : ContinuousAt (fun x => (x, ψ x)) q0 :=
        continuousAt_id.prodMk hψcd.continuousAt
      have hfd : ContinuousAt (fderiv ℝ (borderedE Sfam)) (q0, ψ q0) := by
        rw [hψ0]; exact hcd.continuousAt_fderiv hn0'
      exact (ContinuousAt.comp (f := fun x => (x, ψ x)) hfd hpair).clm_comp continuousAt_const
    have hmem : Set.range ((↑) : ((Vec4 × ℝ) ≃L[ℝ] (Vec4 × ℝ)) → (Vec4 × ℝ) →L[ℝ] (Vec4 × ℝ)) ∈
        𝓝 (fderiv ℝ (borderedE Sfam) (q0, ψ q0) ∘L ContinuousLinearMap.inr ℝ E (Vec4 × ℝ)) := by
      apply ContinuousLinearEquiv.isOpen.mem_nhds
      rw [hψ0]; exact hinv
    exact hc.preimage_mem_nhds hmem
  obtain ⟨V, hVprop, hVopen, hq0V⟩ :=
    eventually_nhds_iff.1 (ev1.and (ev2.and (ev3.and (ev4.and ev5))))
  have hVD : V ⊆ D := fun x hx => (hVprop x hx).2.2.2.1
  have hbp0 : borderedE Sfam p0 = 0 := by
    simp only [borderedE, hp0, he0, sub_self, hn0]
    ext <;> simp
  have heig : ∀ x ∈ V, matVec (Sfam x) (ψ x).1 = (ψ x).2 • (ψ x).1 := by
    intro x hx
    have hb := (hVprop x hx).1
    rw [hbp0] at hb
    exact sub_eq_zero.mp (congrArg Prod.fst hb)
  have hunit : ∀ x ∈ V, lorentzDot (ψ x).1 (ψ x).1 = -1 := by
    intro x hx
    have hb := (hVprop x hx).1
    rw [hbp0] at hb
    have hb2 : lorentzDot (ψ x).1 (ψ x).1 + 1 = 0 := congrArg Prod.snd hb
    linarith
  have hfut : ∀ x ∈ V, 0 < (ψ x).1 0 := fun x hx => (hVprop x hx).2.2.1
  have hgap : ∀ x ∈ V, RestGapInjective (Sfam x) (ψ x).1 (-(ψ x).2) := by
    intro x hx w ho hL
    have hxD := hVD hx
    have hTw : lorentzDot (ψ x).1 (matVec (Sfam x) w) = 0 := by
      rw [selfAdj_dot (hsym x hxD), heig x hx, lorentzDot_smul_left, ho, mul_zero]
    rw [restProj_tangent _ _ hTw] at hL
    have hinj := ((hVprop x hx).2.2.2.2).injective
    have hz : (fderiv ℝ (borderedE Sfam) (x, ψ x) ∘L ContinuousLinearMap.inr ℝ E (Vec4 × ℝ))
        (w, 0) =
        (fderiv ℝ (borderedE Sfam) (x, ψ x) ∘L ContinuousLinearMap.inr ℝ E (Vec4 × ℝ)) 0 := by
      rw [map_zero, borderedE_fderiv_inr (hdiff x hxD _)]
      have e1 : matVec (Sfam x) w - (ψ x).2 • w - (0 : ℝ) • (ψ x).1 =
          matVec (Sfam x) w + (-(ψ x).2) • w := by
        funext a; simp; ring
      rw [e1, hL, ho]; simp
    have := hinj hz
    exact congrArg Prod.fst this
  refine ⟨V, fun x => (ψ x).1, fun x => (ψ x).2, hq0V, hVD, by simp [hψ0], by simp [hψ0], ?_⟩
  refine ⟨hVopen, ?_, ?_, heig, hunit, hfut, hgap, ?_⟩
  · intro x hx
    exact (contDiffAt_fst.comp x (hVprop x hx).2.1).contDiffWithinAt
  · intro x hx
    exact (contDiffAt_snd.comp x (hVprop x hx).2.1).contDiffWithinAt
  · intro x hx v μ hv hvn hvf
    have hu : FutureUnitEigen (Sfam x) (ψ x).1 (-(ψ x).2) :=
      ⟨by rw [neg_neg]; exact heig x hx, hunit x hx, hfut x hx⟩
    have hv' : FutureUnitEigen (Sfam x) v (-μ) := ⟨by rw [neg_neg]; exact hv, hvn, hvf⟩
    obtain ⟨h1, h2⟩ := E1u_unique (Sfam x) (ψ x).1 v (-(ψ x).2) (-μ) (hsym x (hVD hx)) hu
      (hgap x hx) hv'
    exact ⟨h1, neg_inj.mp h2⟩

theorem D2_branch_vec4_via_G04A (n : ℕ) (hn : 1 ≤ n) (D : Set Vec4) (hD : IsOpen D)
    (Sfam : Vec4 → Mat4) (hS : ContDiffOn ℝ n Sfam D) (hsym : ∀ q ∈ D, EtaSelfAdjoint (Sfam q))
    (q0 : Vec4) (hq0 : q0 ∈ D) (u0 : Vec4) (s0 : ℝ)
    (he0 : matVec (Sfam q0) u0 = s0 • u0) (hn0 : lorentzDot u0 u0 = -1) (hf0 : 0 < u0 0)
    (hiso : RestGapInjective (Sfam q0) u0 (-s0)) :
    ∃ (V : Set Vec4) (u : Vec4 → Vec4) (s : Vec4 → ℝ),
      q0 ∈ V ∧ V ⊆ D ∧ u q0 = u0 ∧ s q0 = s0 ∧ TimelikeBranch n Sfam V u s := by
  obtain ⟨V, u, ε, hq0V, hVD, hu0, hε0, hF⟩ :=
    E1_smooth_eigenline n hn D hD Sfam hS hsym q0 hq0 u0 (-s0)
      ⟨by rw [neg_neg]; exact he0, hn0, hf0⟩ hiso
  refine ⟨V, u, fun q => -ε q, hq0V, hVD, hu0, by simp [hε0], ?_⟩
  have hgap : ∀ q ∈ V, RestGapInjective (Sfam q) (u q) (-(-ε q)) := by
    intro q hq; rw [neg_neg]; exact hF.gap q hq
  refine ⟨hF.isOpen, hF.smooth_u, hF.smooth_ε.neg, fun q hq => (hF.eigen q hq).1,
    fun q hq => (hF.eigen q hq).2.1, fun q hq => (hF.eigen q hq).2.2, hgap, ?_⟩
  intro q hq v μ hv hvn hvf
  have hv' : FutureUnitEigen (Sfam q) v (-μ) := ⟨by rw [neg_neg]; exact hv, hvn, hvf⟩
  obtain ⟨h1, h2⟩ := E1u_unique (Sfam q) (u q) v (ε q) (-μ) (hF.selfAdj q hq) (hF.eigen q hq)
    (hF.gap q hq) hv'
  refine ⟨h1, ?_⟩
  show μ = -ε q
  linarith

theorem D3_branch_simple {E : Type*} [NormedAddCommGroup E] [NormedSpace ℝ E] [CompleteSpace E]
    (n : ℕ) (hn : 1 ≤ n) (D : Set E) (hD : IsOpen D) (Sfam : E → Mat4)
    (hS : ContDiffOn ℝ n Sfam D) (hsym : ∀ q ∈ D, EtaSelfAdjoint (Sfam q))
    (q0 : E) (hq0 : q0 ∈ D) (u0 : Vec4) (s0 : ℝ)
    (he0 : matVec (Sfam q0) u0 = s0 • u0) (hn0 : lorentzDot u0 u0 = -1) (hf0 : 0 < u0 0)
    (hsimple : Module.finrank ℝ (Module.End.eigenspace (matVecL (Sfam q0)) s0) = 1) :
    ∃ (V : Set E) (u : E → Vec4) (s : E → ℝ),
      q0 ∈ V ∧ V ⊆ D ∧ u q0 = u0 ∧ s q0 = s0 ∧ TimelikeBranch n Sfam V u s := by
  let τ0 : Timelike := ⟨u0, by rw [hn0]; norm_num⟩
  have hiso : RestGapInjective (Sfam q0) u0 (-s0) :=
    ((C3_isolation_iff τ0 (Sfam q0) s0 (hsym q0 hq0) he0).2.2).2 hsimple
  exact D1_branch n hn D hD Sfam hS hsym q0 hq0 u0 s0 he0 hn0 hf0 hiso

/-! ## E: controls separating rest-eigenvalue collision from loss of timelike isolation -/

def e0v : Vec4 := coordVec 0

def Rrot : Mat4 := ![![0, -1, 0, 0], ![1, 0, 0, 0], ![0, 0, 0, 0], ![0, 0, 0, 0]]

def Srot (q : Vec4) : Mat4 := q 1 • Rrot

def Pdiag : Mat4 := ![![0, 0, 0, 0], ![0, 1, 0, 0], ![0, 0, 1, 0], ![0, 0, 0, 1]]
def M1 : Mat4 := ![![0, 0, 0, 0], ![0, 1, 0, 0], ![0, 0, -1, 0], ![0, 0, 0, 0]]
def M2 : Mat4 := ![![0, 0, 0, 0], ![0, 0, 1, 0], ![0, 1, 0, 0], ![0, 0, 0, 0]]
def M3 : Mat4 := ![![0, 0, 0, 0], ![0, 0, 0, 0], ![0, 0, 0, 1], ![0, 0, 1, 0]]

def Scol (q : Vec4) : Mat4 := Pdiag + q 1 • M1 + q 2 • M2 + q 3 • M3

theorem e0v_apply (a : Fin 4) : e0v a = if a = 0 then 1 else 0 := by
  simp [e0v, coordVec, Pi.single_apply]

theorem lorentzDot_e0v (w : Vec4) : lorentzDot e0v w = -(w 0) := by
  rw [lorentzDot_expand]; simp [e0v_apply]

theorem Srot_matVec (q v : Vec4) :
    matVec (Srot q) v = ![-(q 1 * v 1), q 1 * v 0, 0, 0] := by
  funext a
  fin_cases a <;> simp [matVec, Srot, Rrot, Fin.sum_univ_four]

theorem Scol_matVec (q x : Vec4) :
    matVec (Scol q) x = ![0, x 1 + q 1 * x 1 + q 2 * x 2,
      x 2 - q 1 * x 2 + q 2 * x 1 + q 3 * x 3, x 3 + q 3 * x 2] := by
  funext a
  fin_cases a <;> simp [matVec, Scol, Pdiag, M1, M2, M3, Fin.sum_univ_four] <;> ring

/-- Points `t • e_a` with `t ≠ 0` accumulate at `0`; a continuous quantity that vanishes there
vanishes at `0`. -/
theorem axis_limit (v : Vec4 → Vec4) (hv : ContinuousAt v 0) (P : Vec4 → Prop)
    (hP : ∀ᶠ q in 𝓝 (0 : Vec4), P q) (a : Fin 4) (F : Vec4 → ℝ) (hF : Continuous F)
    (hz : ∀ t : ℝ, t ≠ 0 → P (t • coordVec a) → F (v (t • coordVec a)) = 0) :
    F (v 0) = 0 := by
  have hγc : Continuous (fun t : ℝ => t • coordVec a) := continuous_id.smul continuous_const
  have hγ : Filter.Tendsto (fun t : ℝ => t • coordVec a) (𝓝 0) (𝓝 (0 : Vec4)) := by
    simpa using hγc.tendsto 0
  have hlim : Filter.Tendsto (fun t : ℝ => F (v (t • coordVec a))) (𝓝[≠] 0) (𝓝 (F (v 0))) := by
    have h1 : Filter.Tendsto (fun t : ℝ => v (t • coordVec a)) (𝓝 0) (𝓝 (v 0)) :=
      hv.tendsto.comp hγ
    exact ((hF.tendsto _).comp h1).mono_left nhdsWithin_le_nhds
  have hev : ∀ᶠ t in 𝓝[≠] (0 : ℝ), F (v (t • coordVec a)) = 0 := by
    have h1 : ∀ᶠ t in 𝓝 (0 : ℝ), P (t • coordVec a) := hγ.eventually hP
    filter_upwards [h1.filter_mono nhdsWithin_le_nhds, self_mem_nhdsWithin] with t ht ht0
    exact hz t ht0 ht
  have hlim0 : Filter.Tendsto (fun t : ℝ => F (v (t • coordVec a))) (𝓝[≠] 0) (𝓝 0) :=
    tendsto_const_nhds.congr' (hev.mono fun t ht => ht.symm)
  exact tendsto_nhds_unique hlim hlim0

theorem E1_isolation_needed (n : ℕ) :
    ContDiff ℝ n Srot ∧ (∀ q, EtaSelfAdjoint (Srot q)) ∧
    matVec (Srot 0) e0v = (0 : ℝ) • e0v ∧ lorentzDot e0v e0v = -1 ∧ 0 < e0v 0 ∧
    ¬ RestGapInjective (Srot 0) e0v (-(0 : ℝ)) ∧
    ¬ ∃ V ∈ 𝓝 (0 : Vec4), ∀ q ∈ V, ∃ (v : Vec4) (μ : ℝ),
        lorentzDot v v < 0 ∧ matVec (Srot q) v = μ • v := by
  refine ⟨?_, ?_, ?_, ?_, ?_, ?_, ?_⟩
  · exact (contDiff_apply ℝ ℝ (1 : Fin 4)).smul contDiff_const
  · intro q a b
    fin_cases a <;> fin_cases b <;> simp [Srot, Rrot, eta]
  · rw [Srot_matVec]; funext a; fin_cases a <;> simp [e0v_apply]
  · rw [lorentzDot_e0v]; simp [e0v_apply]
  · simp [e0v_apply]
  · intro hg
    have h := hg (coordVec 1) (by rw [lorentzDot_e0v]; simp [coordVec])
      (by
        rw [Srot_matVec]
        funext a
        fin_cases a <;> simp [restProj, lorentzDot_e0v, coordVec])
    have := congrFun h 1
    simp [coordVec] at this
  · rintro ⟨V, hV, hall⟩
    have hγc : Continuous (fun t : ℝ => t • coordVec 1) := continuous_id.smul continuous_const
    have hγ : Filter.Tendsto (fun t : ℝ => t • coordVec 1) (𝓝 0) (𝓝 (0 : Vec4)) := by
      simpa using hγc.tendsto 0
    have hev : ∀ᶠ t in 𝓝[≠] (0 : ℝ), t • coordVec 1 ∈ V ∧ t ≠ 0 :=
      ((hγ.eventually hV).filter_mono nhdsWithin_le_nhds).and self_mem_nhdsWithin
    obtain ⟨t, htV, ht0⟩ := hev.exists
    obtain ⟨v, μ, hv, he⟩ := hall _ htV
    have hq1 : (t • coordVec 1 : Vec4) 1 = t := by simp [coordVec]
    have h0 : -(t * v 1) = μ * v 0 := by
      have := congrFun he 0
      rw [Srot_matVec, hq1] at this
      simpa using this
    have h1 : t * v 0 = μ * v 1 := by
      have := congrFun he 1
      rw [Srot_matVec, hq1] at this
      simpa using this
    have h2 : t * (v 0 ^ 2 + v 1 ^ 2) = 0 := by linear_combination v 0 * h1 - v 1 * h0
    have h3 : v 0 ^ 2 + v 1 ^ 2 = 0 := (mul_eq_zero.1 h2).resolve_left ht0
    rw [lorentzDot_expand] at hv
    nlinarith [sq_nonneg (v 0), sq_nonneg (v 1), mul_self_nonneg (v 2), mul_self_nonneg (v 3)]

theorem Scol_rest_identity (w : Vec4) (hw : lorentzDot e0v w = 0) : matVec (Scol 0) w = w := by
  rw [lorentzDot_e0v] at hw
  rw [Scol_matVec]
  funext a
  fin_cases a <;> simp <;> linarith

theorem E2_collision_branch_exists (n : ℕ) (hn : 1 ≤ n) :
    ContDiff ℝ n Scol ∧ (∀ q, EtaSelfAdjoint (Scol q)) ∧
    (∀ w, lorentzDot e0v w = 0 → matVec (Scol 0) w = w) ∧
    RestGapInjective (Scol 0) e0v (-(0 : ℝ)) ∧
    ∃ (V : Set Vec4) (u : Vec4 → Vec4) (s : Vec4 → ℝ),
      (0 : Vec4) ∈ V ∧ u 0 = e0v ∧ s 0 = 0 ∧ TimelikeBranch n Scol V u s := by
  have hcd : ContDiff ℝ n Scol := by
    unfold Scol
    exact ((contDiff_const.add ((contDiff_apply ℝ ℝ (1 : Fin 4)).smul contDiff_const)).add
      ((contDiff_apply ℝ ℝ (2 : Fin 4)).smul contDiff_const)).add
      ((contDiff_apply ℝ ℝ (3 : Fin 4)).smul contDiff_const)
  have hsa : ∀ q, EtaSelfAdjoint (Scol q) := by
    intro q a b
    fin_cases a <;> fin_cases b <;> simp [Scol, Pdiag, M1, M2, M3, eta]
  have hgap : RestGapInjective (Scol 0) e0v (-(0 : ℝ)) := by
    intro w ho heq
    rw [Scol_rest_identity w ho, restProj_tangent _ _ ho] at heq
    simpa using heq
  have he0 : matVec (Scol 0) e0v = (0 : ℝ) • e0v := by
    rw [Scol_matVec]; funext a; fin_cases a <;> simp [e0v_apply]
  have hn0 : lorentzDot e0v e0v = -1 := by rw [lorentzDot_e0v]; simp [e0v_apply]
  have hf0 : 0 < e0v 0 := by simp [e0v_apply]
  refine ⟨hcd, hsa, Scol_rest_identity, hgap, ?_⟩
  obtain ⟨V, u, s, h0V, _, hu0, hs0, hB⟩ :=
    D1_branch n hn Set.univ isOpen_univ Scol hcd.contDiffOn (fun q _ => hsa q) 0
      (Set.mem_univ _) e0v 0 he0 hn0 hf0 hgap
  exact ⟨V, u, s, h0V, hu0, hs0, hB⟩

theorem E3_no_continuous_rest_eigenvector :
    ¬ ∃ v : Vec4 → Vec4, ContinuousAt v 0 ∧ ∀ᶠ q in 𝓝 (0 : Vec4),
      lorentzDot e0v (v q) = 0 ∧ lorentzDot (v q) (v q) = 1 ∧
        ∃ μ : ℝ, matVec (Scol q) (v q) = μ • v q := by
  rintro ⟨v, hv, hP⟩
  -- axis 1: q = t e_1 gives x1 * x2 = 0
  have hA : v 0 1 * v 0 2 = 0 := by
    refine axis_limit v hv _ hP 1 (fun x => x 1 * x 2) (by fun_prop) ?_
    rintro t ht0 ⟨_, _, μ, he⟩
    set x := v (t • coordVec 1)
    have hq1 : (t • coordVec 1 : Vec4) 1 = t := by simp [coordVec]
    have hq2 : (t • coordVec 1 : Vec4) 2 = 0 := by simp [coordVec]
    have hq3 : (t • coordVec 1 : Vec4) 3 = 0 := by simp [coordVec]
    have h1 : x 1 + t * x 1 = μ * x 1 := by
      have := congrFun he 1
      rw [Scol_matVec, hq1, hq2] at this
      simp at this; linarith
    have h2 : x 2 - t * x 2 = μ * x 2 := by
      have := congrFun he 2
      rw [Scol_matVec, hq1, hq2, hq3] at this
      simp at this; linarith
    have h3 : t * (2 * (x 1 * x 2)) = 0 := by linear_combination x 2 * h1 - x 1 * h2
    have := (mul_eq_zero.1 h3).resolve_left ht0
    show x 1 * x 2 = 0
    linarith
  -- axis 2: q = t e_2 gives x1^2 = x2^2
  have hB : v 0 1 ^ 2 - v 0 2 ^ 2 = 0 := by
    refine axis_limit v hv _ hP 2 (fun x => x 1 ^ 2 - x 2 ^ 2) (by fun_prop) ?_
    rintro t ht0 ⟨_, _, μ, he⟩
    set x := v (t • coordVec 2)
    have hq1 : (t • coordVec 2 : Vec4) 1 = 0 := by simp [coordVec]
    have hq2 : (t • coordVec 2 : Vec4) 2 = t := by simp [coordVec]
    have hq3 : (t • coordVec 2 : Vec4) 3 = 0 := by simp [coordVec]
    have h1 : x 1 + t * x 2 = μ * x 1 := by
      have := congrFun he 1
      rw [Scol_matVec, hq1, hq2] at this
      simp at this; linarith
    have h2 : x 2 + t * x 1 = μ * x 2 := by
      have := congrFun he 2
      rw [Scol_matVec, hq1, hq2, hq3] at this
      simp at this; linarith
    have h3 : t * (x 2 ^ 2 - x 1 ^ 2) = 0 := by linear_combination x 2 * h1 - x 1 * h2
    have := (mul_eq_zero.1 h3).resolve_left ht0
    show x 1 ^ 2 - x 2 ^ 2 = 0
    linarith
  -- axis 3: q = t e_3 gives x2^2 = x3^2
  have hC : v 0 2 ^ 2 - v 0 3 ^ 2 = 0 := by
    refine axis_limit v hv _ hP 3 (fun x => x 2 ^ 2 - x 3 ^ 2) (by fun_prop) ?_
    rintro t ht0 ⟨_, _, μ, he⟩
    set x := v (t • coordVec 3)
    have hq1 : (t • coordVec 3 : Vec4) 1 = 0 := by simp [coordVec]
    have hq2 : (t • coordVec 3 : Vec4) 2 = 0 := by simp [coordVec]
    have hq3 : (t • coordVec 3 : Vec4) 3 = t := by simp [coordVec]
    have h2 : x 2 + t * x 3 = μ * x 2 := by
      have := congrFun he 2
      rw [Scol_matVec, hq1, hq2, hq3] at this
      simp at this; linarith
    have h3' : x 3 + t * x 2 = μ * x 3 := by
      have := congrFun he 3
      rw [Scol_matVec, hq3] at this
      simp at this; linarith
    have h3 : t * (x 3 ^ 2 - x 2 ^ 2) = 0 := by linear_combination x 3 * h2 - x 2 * h3'
    have := (mul_eq_zero.1 h3).resolve_left ht0
    show x 2 ^ 2 - x 3 ^ 2 = 0
    linarith
  obtain ⟨hr, hu, _⟩ := hP.self_of_nhds
  rw [lorentzDot_e0v] at hr
  rw [lorentzDot_expand] at hu
  set x := v 0
  have hx0 : x 0 = 0 := by linarith
  have h4 : x 1 ^ 2 * x 1 ^ 2 = 0 := by
    have : x 1 ^ 2 = x 2 ^ 2 := by linarith
    calc x 1 ^ 2 * x 1 ^ 2 = x 1 ^ 2 * x 2 ^ 2 := by rw [← this]
      _ = (x 1 * x 2) ^ 2 := by ring
      _ = 0 := by rw [hA]; ring
  have hx1 : x 1 ^ 2 = 0 := mul_self_eq_zero.1 h4
  have hx2 : x 2 ^ 2 = 0 := by linarith
  have hx3 : x 3 ^ 2 = 0 := by linarith
  rw [hx0] at hu
  nlinarith [hx1, hx2, hx3]

end G03A
