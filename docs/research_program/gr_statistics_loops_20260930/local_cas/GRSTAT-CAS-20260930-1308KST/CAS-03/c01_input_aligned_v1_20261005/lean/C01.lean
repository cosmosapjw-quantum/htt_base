import Mathlib

/-! Exact C01 algebra in the fixed (-,+,+,+) orthonormal frame. -/
namespace CAS03C01

abbrev W := Fin 3 → ℝ
abbrev V := ℝ × W

def dot (x y : W) : ℝ := ∑ i, x i * y i
def zeroW : W := fun _ => 0
def e0 : V := (1, zeroW)
def g (v : V) : V := (-v.1, v.2)
def covPair (v q : V) : ℝ := v.1 * q.1 + dot v.2 q.2
def mass (v : V) : ℝ := covPair v (g v)

structure SymCov where
  a : ℝ
  b : W
  d : Matrix (Fin 3) (Fin 3) ℝ
  d_symm : d.IsSymm

-- Every symmetric covariant 4 by 4 matrix has these components.
def fromMatrix (m : Matrix (Fin 4) (Fin 4) ℝ) (hm : m.IsSymm) : SymCov where
  a := m 0 0
  b := fun i => m 0 i.succ
  d := m.submatrix Fin.succ Fin.succ
  d_symm := hm.submatrix Fin.succ

def toMatrix (s : SymCov) : Matrix (Fin 4) (Fin 4) ℝ :=
  Fin.cases (Fin.cons s.a s.b)
    (fun i => Fin.cons (s.b i) (fun j => s.d i j))

theorem toMatrix_fromMatrix (m : Matrix (Fin 4) (Fin 4) ℝ) (hm : m.IsSymm) :
    toMatrix (fromMatrix m hm) = m := by
  ext i j
  cases i using Fin.cases with
  | zero =>
    cases j using Fin.cases with
    | zero => rfl
    | succ j => rfl
  | succ i =>
    cases j using Fin.cases with
    | zero => simpa [toMatrix, fromMatrix] using (hm.apply 0 i.succ).symm
    | succ j => rfl

def act (s : SymCov) (v : V) : V :=
  (s.a * v.1 + dot s.b v.2,
   fun i => s.b i * v.1 + ∑ j, s.d i j * v.2 j)

def st (s : SymCov) (u : V) : ℝ := -covPair u (act s u)
def bAct (s : SymCov) (u v : V) : V :=
  ((act s v).1 - st s u * (g v).1,
   fun i => (act s v).2 i - st s u * (g v).2 i)
def mixed (s : SymCov) (v : V) : V := g (act s v)
def smulV (c : ℝ) (v : V) : V := (c * v.1, fun i => c * v.2 i)
def futureUnit (v : V) : Prop := mass v = -1 ∧ 0 < v.1

theorem g_involutive (v : V) : g (g v) = v := by
  cases v with
  | mk t w => simp [g]

theorem b_zero_iff_eigen (s : SymCov) (u : V) :
    bAct s u u = (0, zeroW) ↔ mixed s u = smulV (st s u) u := by
  constructor
  · intro h
    apply Prod.ext
    · have h0 := congrArg Prod.fst h
      simp [bAct, mixed, smulV, g, zeroW] at h0 ⊢
      linarith
    · funext i
      have hi := congrArg (fun v : V => v.2 i) h
      simp [bAct, mixed, smulV, g, zeroW] at hi ⊢
      linarith
  · intro h
    apply Prod.ext
    · have h0 := congrArg Prod.fst h
      simp [bAct, mixed, smulV, g, zeroW] at h0 ⊢
      linarith
    · funext i
      have hi := congrArg (fun v : V => v.2 i) h
      simp [bAct, mixed, smulV, g, zeroW] at hi ⊢
      linarith

theorem metric_coefficient_unique (s : SymCov) (u : V) (c : ℝ)
    (hu : mass u = -1)
    (heig : mixed s u = smulV c u) : c = st s u := by
  have h0 := congrArg Prod.fst heig
  have hw := congrArg Prod.snd heig
  simp [mixed, smulV, g] at h0 hw
  have hdot : covPair u (act s u) = -c := by
    simp only [covPair, dot]
    have hs : (∑ i, u.2 i * (act s u).2 i) = c * ∑ i, u.2 i * u.2 i := by
      simp_rw [congrFun hw]
      rw [Finset.mul_sum]
      congr 1
      ext i
      ring
    rw [hs]
    have hm : -(u.1 * u.1) + (∑ i, u.2 i * u.2 i) = -1 := by
      simpa [mass, covPair, g, dot] using hu
    have h0mul : u.1 * (act s u).1 = -(c * (u.1 * u.1)) := by
      nlinarith [congrArg (fun x : ℝ => u.1 * x) h0]
    have hmmul : -(c * (u.1 * u.1)) + c * (∑ i, u.2 i * u.2 i) = -c := by
      nlinarith [congrArg (fun x : ℝ => c * x) hm]
    linarith
  simp [st, hdot]

def restD (s : SymCov) (u : V) : Matrix (Fin 3) (Fin 3) ℝ :=
  fun i j => s.d i j - if i = j then st s u else 0
def Dact (s : SymCov) (u : V) (w : W) : W :=
  fun i => ∑ j, restD s u i j * w j
def zeroExpansion (s : SymCov) (u : V) : Prop := ∑ i, restD s u i i = 0

theorem rest_time_column (s : SymCov) (h : bAct s e0 e0 = (0, zeroW)) :
    s.a + st s e0 = 0 ∧ s.b = zeroW := by
  have h0 := congrArg Prod.fst h
  have hw := congrArg Prod.snd h
  constructor
  · simpa [bAct, act, e0, g, dot, zeroW] using h0
  · funext i
    have hi := congrArg (fun w : W => w i) hw
    simpa [bAct, act, e0, g, dot, zeroW] using hi

theorem rest_block (s : SymCov) (h : bAct s e0 e0 = (0, zeroW)) (v : V) :
    bAct s e0 v = (0, Dact s e0 v.2) := by
  obtain ⟨ha, hb⟩ := rest_time_column s h
  apply Prod.ext
  · simp [bAct, act, g, dot, hb, zeroW]
    calc
      s.a * v.1 + st s e0 * v.1 = (s.a + st s e0) * v.1 := by ring
      _ = 0 := by rw [ha]; ring
  · funext i
    simp [bAct, act, g, Dact, restD, hb, zeroW,
      Finset.sum_sub_distrib, sub_mul]

noncomputable def phi (w : W) : V := (Real.sqrt (1 + dot w w), w)
def kerD (s : SymCov) (w : W) : Prop := Dact s e0 w = zeroW
def fibre (s : SymCov) (v : V) : Prop :=
  bAct s e0 v = (0, zeroW) ∧ futureUnit v

theorem phi_future (w : W) : futureUnit (phi w) := by
  have hn : 0 ≤ dot w w := Finset.sum_nonneg (fun i hi => mul_self_nonneg (w i))
  have hp : 0 < 1 + dot w w := by linarith
  have hs : (Real.sqrt (1 + dot w w)) ^ 2 = 1 + dot w w := Real.sq_sqrt (le_of_lt hp)
  constructor
  · simp [mass, covPair, g, phi, dot] at *
    nlinarith
  · simpa [phi] using Real.sqrt_pos.2 hp

theorem fibre_chart (s : SymCov)
    (hrest : bAct s e0 e0 = (0, zeroW))
    (_hexp : zeroExpansion s e0) (v : V) :
    fibre s v ↔ ∃ w : W, kerD s w ∧ v = phi w := by
  constructor
  · intro hv
    refine ⟨v.2, ?_, ?_⟩
    · have hb := (rest_block s hrest v).symm.trans hv.1
      exact congrArg Prod.snd hb
    · apply Prod.ext
      · have hm := hv.2.1
        have hp := hv.2.2
        have hn : 0 ≤ 1 + dot v.2 v.2 := by
          have : 0 ≤ dot v.2 v.2 := Finset.sum_nonneg (fun i hi => mul_self_nonneg (v.2 i))
          linarith
        have hs : v.1 ^ 2 = 1 + dot v.2 v.2 := by
          simp [mass, covPair, g, dot] at hm
          simp only [dot]
          nlinarith
        have hsq := Real.sq_sqrt hn
        have hpos := Real.sqrt_nonneg (1 + dot v.2 v.2)
        dsimp [phi]
        nlinarith
      · rfl
  · rintro ⟨w, hw, rfl⟩
    constructor
    · rw [rest_block s hrest]
      simp [kerD] at hw
      simp [phi, hw]
    · exact phi_future w

theorem phi_injective : Function.Injective phi := by
  intro x y h
  exact congrArg Prod.snd h

theorem spatial_inverse (v : V) (hv : futureUnit v) : phi v.2 = v := by
  apply Prod.ext
  · have hm := hv.1
    have hp := hv.2
    have hn : 0 ≤ 1 + dot v.2 v.2 := by
      have : 0 ≤ dot v.2 v.2 := Finset.sum_nonneg (fun i hi => mul_self_nonneg (v.2 i))
      linarith
    have hs : v.1 ^ 2 = 1 + dot v.2 v.2 := by
      simp [mass, covPair, g, dot] at hm
      simp only [dot]
      nlinarith
    have hsq := Real.sq_sqrt hn
    have hpos := Real.sqrt_nonneg (1 + dot v.2 v.2)
    dsimp [phi]
    nlinarith
  · rfl

theorem full_kernel_control (s : SymCov)
    (hrest : bAct s e0 e0 = (0, zeroW))
    (hD : ∀ i j, restD s e0 i j = 0) (w : W) : kerD s w := by
  funext i
  simp [kerD, Dact, hD, zeroW]

theorem zero_kernel_control (s : SymCov)
    (hker : ∀ w : W, kerD s w → w = zeroW)
    (hrest : bAct s e0 e0 = (0, zeroW))
    (hexp : zeroExpansion s e0) (v : V) :
    fibre s v ↔ v = e0 := by
  constructor
  · intro hv
    obtain ⟨w, hw, rfl⟩ := (fibre_chart s hrest hexp v).1 hv
    rw [hker w hw]
    simp [phi, e0, dot, zeroW]
  · intro hv
    subst v
    constructor
    · exact hrest
    · simp [futureUnit, mass, covPair, g, e0, dot, zeroW]

-- The three frozen diagonal controls are trace-free, including the singular cases.
def diagonalExample (q : W) : SymCov where
  a := 0
  b := zeroW
  d := Matrix.diagonal q
  d_symm := Matrix.isSymm_diagonal q

theorem diagonalExample_rest (q : W) :
    bAct (diagonalExample q) e0 e0 = (0, zeroW) := by
  apply Prod.ext
  · simp [bAct, diagonalExample, act, st, covPair, dot, e0, zeroW, g]
  · funext i
    simp [bAct, diagonalExample, act, st, covPair, dot, e0, zeroW, g]

theorem diagonalExample_D (q w : W) :
    Dact (diagonalExample q) e0 w = fun i => q i * w i := by
  funext i
  simp [Dact, restD, diagonalExample, st, covPair, dot, act, e0,
    zeroW, Matrix.diagonal, g]

def qFull : W := fun _ => 0
def qLine : W := ![0, 1, -1]
def qPoint : W := ![1, 1, -2]

theorem qFull_trace : zeroExpansion (diagonalExample qFull) e0 := by
  norm_num [zeroExpansion, restD, diagonalExample, st, covPair,
    act, e0, dot, zeroW, g, Matrix.diagonal, qFull, Fin.sum_univ_succ]

theorem qLine_trace : zeroExpansion (diagonalExample qLine) e0 := by
  norm_num [zeroExpansion, restD, diagonalExample, st, covPair,
    act, e0, dot, zeroW, g, Matrix.diagonal, qLine, Fin.sum_univ_succ]

theorem qPoint_trace : zeroExpansion (diagonalExample qPoint) e0 := by
  norm_num [zeroExpansion, restD, diagonalExample, st, covPair,
    act, e0, dot, zeroW, g, Matrix.diagonal, qPoint, Fin.sum_univ_succ]

theorem qFull_kernel (w : W) : kerD (diagonalExample qFull) w := by
  rw [kerD, diagonalExample_D]
  funext i
  simp [qFull, zeroW]

theorem qLine_kernel (w : W) :
    kerD (diagonalExample qLine) w ↔ w 1 = 0 ∧ w 2 = 0 := by
  rw [kerD, diagonalExample_D]
  constructor
  · intro h
    have h1 := congrFun h 1
    have h2 := congrFun h 2
    simpa [qLine, zeroW] using And.intro h1 h2
  · rintro ⟨h1, h2⟩
    funext i
    fin_cases i <;> simp [qLine, zeroW, h1, h2]

theorem qPoint_kernel (w : W) :
    kerD (diagonalExample qPoint) w ↔ w = zeroW := by
  rw [kerD, diagonalExample_D]
  constructor
  · intro h
    funext i
    have hi := congrFun h i
    fin_cases i <;> norm_num [qPoint, zeroW] at hi ⊢ <;> linarith
  · intro h
    subst w
    funext i
    simp [zeroW]

theorem qFull_fibre (v : V) :
    fibre (diagonalExample qFull) v ↔ ∃ w : W, v = phi w := by
  rw [fibre_chart (diagonalExample qFull) (diagonalExample_rest qFull) qFull_trace]
  simp [qFull_kernel]

theorem qLine_fibre (v : V) :
    fibre (diagonalExample qLine) v ↔
      ∃ w : W, w 1 = 0 ∧ w 2 = 0 ∧ v = phi w := by
  rw [fibre_chart (diagonalExample qLine) (diagonalExample_rest qLine) qLine_trace]
  simp [qLine_kernel, and_assoc]

theorem qPoint_fibre (v : V) : fibre (diagonalExample qPoint) v ↔ v = e0 := by
  apply zero_kernel_control (diagonalExample qPoint)
    (fun w hw => (qPoint_kernel w).1 hw)
    (diagonalExample_rest qPoint) qPoint_trace

end CAS03C01

#print axioms CAS03C01.toMatrix_fromMatrix
#print axioms CAS03C01.b_zero_iff_eigen
#print axioms CAS03C01.metric_coefficient_unique
#print axioms CAS03C01.rest_time_column
#print axioms CAS03C01.rest_block
#print axioms CAS03C01.phi_future
#print axioms CAS03C01.fibre_chart
#print axioms CAS03C01.phi_injective
#print axioms CAS03C01.spatial_inverse
#print axioms CAS03C01.qFull_fibre
#print axioms CAS03C01.qLine_fibre
#print axioms CAS03C01.qPoint_fibre
