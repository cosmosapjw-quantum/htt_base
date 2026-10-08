import Mathlib

/- PORT-CAS-02, exact pointwise algebra. Indices 0,1,2,3; 0 is time.
   Metric signature (-,+,+,+), with K contravariant=(-1,n).
   No claim of eigenline existence or geodesicity is encoded. -/
namespace PortCAS02

abbrev V3 := Fin 3 → ℝ
abbrev V4 := Fin 4 → ℝ
abbrev Cov2 := Fin 4 → Fin 4 → ℝ

def g (a b : Fin 4) : ℝ :=
  if a = b then (if a = 0 then -1 else 1) else 0

def K (n : V3) : V4 := fun a =>
  if h : a = 0 then -1 else n (a.pred h)

noncomputable def S (h0 : ℝ) (h1 : V3) (q : Fin 3 → Fin 3 → ℝ) : Cov2 :=
  fun a b =>
    if ha : a = 0 then
      if hb : b = 0 then h0 else -(h1 (b.pred hb)) / 2
    else if hb : b = 0 then -(h1 (a.pred ha)) / 2 else q (a.pred ha) (b.pred hb)

def B (T : Cov2) (st : ℝ) : Cov2 := fun a b => T a b - st * g a b
def gauge (T : Cov2) (α : ℝ) : Cov2 := fun a b => T a b + α * g a b
def contraction (T : Cov2) (v w : V4) : ℝ := ∑ a : Fin 4, ∑ b : Fin 4, T a b * v a * w b
def covAction (T : Cov2) (u : V4) : V4 := fun a => ∑ b : Fin 4, T a b * u b
def mixedAction (T : Cov2) (u : V4) : V4 := fun a => ∑ c : Fin 4, g a c * covAction T u c
def quad (q : Fin 3 → Fin 3 → ℝ) (n : V3) : ℝ :=
  ∑ i : Fin 3, ∑ j : Fin 3, q i j * n i * n j
def dot (v w : V3) : ℝ := ∑ i : Fin 3, v i * w i
def spatialTrace (q : Fin 3 → Fin 3 → ℝ) : ℝ := ∑ i : Fin 3, q i i

theorem g_symm (a b : Fin 4) : g a b = g b a := by
  unfold g
  by_cases h : a = b <;> simp [h, eq_comm]

theorem S_symm (h0 : ℝ) (h1 : V3) (q : Fin 3 → Fin 3 → ℝ)
    (hq : ∀ i j, q i j = q j i) (a b : Fin 4) :
    S h0 h1 q a b = S h0 h1 q b a := by
  unfold S
  by_cases ha : a = 0 <;> by_cases hb : b = 0
  · subst a; subst b; simp
  · subst a; simp [hb]
  · subst b; simp [ha]
  · simp [ha, hb, hq]

theorem B_symm (T : Cov2) (st : ℝ)
    (hT : ∀ a b, T a b = T b a) (a b : Fin 4) :
    B T st a b = B T st b a := by
  simp [B, hT, g_symm]

theorem null_metric (n : V3) (hn : dot n n = 1) :
    contraction g (K n) (K n) = 0 := by
  simp only [dot, Fin.sum_univ_succ] at hn
  simp [contraction, Fin.sum_univ_succ, g, K] at *
  nlinarith

theorem null_S (h0 : ℝ) (h1 : V3) (q : Fin 3 → Fin 3 → ℝ)
    (n : V3) :
    contraction (S h0 h1 q) (K n) (K n) =
      h0 + dot h1 n + quad q n := by
  simp [contraction, dot, quad, Fin.sum_univ_succ, S, K]
  ring

theorem contraction_B (T : Cov2) (st : ℝ) (n : V3)
    (hn : dot n n = 1) :
    contraction (B T st) (K n) (K n) = contraction T (K n) (K n) := by
  simp [dot, Fin.sum_univ_succ] at hn
  simp [contraction, B, g, K, Fin.sum_univ_succ]
  linear_combination -st * hn

theorem gauge_B (T : Cov2) (st α : ℝ) :
    B (gauge T α) (st + α) = B T st := by
  funext a b
  simp [B, gauge]
  ring

theorem gauge_null (T : Cov2) (α : ℝ) (n : V3)
    (hn : dot n n = 1) :
    contraction (gauge T α) (K n) (K n) = contraction T (K n) (K n) := by
  have hB := contraction_B (gauge T α) α n hn
  have heq : B (gauge T α) α = T := by
    funext a b
    simp [B, gauge]
  rw [heq] at hB
  exact hB.symm

theorem tracefree_monopole (q : Fin 3 → Fin 3 → ℝ)
    (hq : spatialTrace q = 0) : spatialTrace q / 3 = 0 := by
  rw [hq]; ring

theorem metric_action (u : V4) (a : Fin 4) :
    covAction g u a = (if a = 0 then -u a else u a) := by
  fin_cases a <;> simp [covAction, g]

theorem raise_lower (u : V4) (a : Fin 4) :
    mixedAction g u a = u a := by
  fin_cases a <;> simp [mixedAction, covAction, g, Fin.sum_univ_succ]

theorem metric_involution (v : V4) (a : Fin 4) :
    (∑ c : Fin 4, g a c * (∑ b : Fin 4, g c b * v b)) = v a := by
  fin_cases a <;> simp [g, Fin.sum_univ_succ]

theorem kernel_eigen_iff (T : Cov2) (st : ℝ) (u : V4) :
    (∀ a, covAction (B T st) u a = 0) ↔
    (∀ a, mixedAction T u a = st * u a) := by
  constructor
  · intro h a
    fin_cases a
    · have hh := h 0
      simp [covAction, mixedAction, B, g, Fin.sum_univ_succ] at hh ⊢
      linarith
    · have hh := h 1
      simp [covAction, mixedAction, B, g, Fin.sum_univ_succ] at hh ⊢
      linarith
    · have hh := h 2
      simp [covAction, mixedAction, B, g, Fin.sum_univ_succ] at hh ⊢
      linarith
    · have hh := h 3
      simp [covAction, mixedAction, B, g, Fin.sum_univ_succ] at hh ⊢
      linarith
  · intro h a
    fin_cases a
    · have hh := h 0
      simp [covAction, mixedAction, B, g, Fin.sum_univ_succ] at hh ⊢
      linarith
    · have hh := h 1
      simp [covAction, mixedAction, B, g, Fin.sum_univ_succ] at hh ⊢
      linarith
    · have hh := h 2
      simp [covAction, mixedAction, B, g, Fin.sum_univ_succ] at hh ⊢
      linarith
    · have hh := h 3
      simp [covAction, mixedAction, B, g, Fin.sum_univ_succ] at hh ⊢
      linarith

/-- The finite statement in the admitted domain. The future/unit branch is
    a premise; its existence is not asserted here. -/
def FutureUnit (u : V4) : Prop := 0 < u 0 ∧ contraction g u u = -1

theorem domain_null_form (h0 st : ℝ) (h1 : V3)
    (q : Fin 3 → Fin 3 → ℝ) (n : V3)
    (hqSym : ∀ i j, q i j = q j i)
    (hqTrace : spatialTrace q = 0) (hn : dot n n = 1) :
    contraction g (K n) (K n) = 0 ∧
    contraction (S h0 h1 q) (K n) (K n) = h0 + dot h1 n + quad q n ∧
    contraction (B (S h0 h1 q) st) (K n) (K n) = h0 + dot h1 n + quad q n ∧
    (∀ a b, B (S h0 h1 q) st a b = B (S h0 h1 q) st b a) ∧
    spatialTrace q / 3 = 0 := by
  refine ⟨null_metric n hn, null_S h0 h1 q n, ?_, ?_, tracefree_monopole q hqTrace⟩
  · rw [contraction_B _ _ _ hn, null_S]
  · intro a b
    exact B_symm _ _ (S_symm h0 h1 q hqSym) a b

theorem future_unit_kernel_eigen_iff (T : Cov2) (st : ℝ) (u : V4)
    (_hu : FutureUnit u) :
    (∀ a, covAction (B T st) u a = 0) ↔
    (∀ a, mixedAction T u a = st * u a) :=
  kernel_eigen_iff T st u

theorem gauge_eigen_iff (T : Cov2) (st α : ℝ) (u : V4) :
    (∀ a, mixedAction (gauge T α) u a = (st + α) * u a) ↔
    (∀ a, mixedAction T u a = st * u a) := by
  rw [← kernel_eigen_iff, ← kernel_eigen_iff, gauge_B]

/-- An antisymmetric covariant component cannot be seen by any diagonal
    quadratic contraction, including the null direction. -/
theorem skew_contraction_zero (A : Cov2)
    (hA : ∀ a b, A a b = -A b a) (v : V4) :
    contraction A v v = 0 := by
  have hneg : contraction A v v = -contraction A v v := by
    unfold contraction
    calc
      (∑ a : Fin 4, ∑ b : Fin 4, A a b * v a * v b)
          = ∑ b : Fin 4, ∑ a : Fin 4, A a b * v a * v b := Finset.sum_comm
      _ = ∑ b : Fin 4, ∑ a : Fin 4, -(A b a * v b * v a) := by
        apply Finset.sum_congr rfl
        intro b _
        apply Finset.sum_congr rfl
        intro a _
        rw [hA a b]
        ring
      _ = -(∑ b : Fin 4, ∑ a : Fin 4, A b a * v b * v a) := by
        simp [Finset.sum_neg_distrib]
  linarith

def exampleN : V3 := fun i => if i = 0 then 1 else 0
def exampleH1 : V3 := fun i => if i = 0 then 1 else if i = 1 then -2 else 3
def exampleQ : Fin 3 → Fin 3 → ℝ := fun i j =>
  if i = j then (if i = 0 then 1 else if i = 1 then -1 else 0) else 0

theorem exact_test_vector :
    contraction (S 2 exampleH1 exampleQ) (K exampleN) (K exampleN) = 4 := by
  rw [null_S]
  norm_num [dot, quad, exampleN, exampleH1, exampleQ, Fin.sum_univ_succ]

theorem metric_multiple_zero (st : ℝ) :
    B (fun a b => st * g a b) st = fun _ _ => 0 := by
  funext a b
  simp [B]

#print axioms null_metric
#print axioms null_S
#print axioms contraction_B
#print axioms kernel_eigen_iff
#print axioms gauge_B
#print axioms gauge_null
#print axioms gauge_eigen_iff
#print axioms domain_null_form
#print axioms skew_contraction_zero
#print axioms exact_test_vector
#print axioms metric_multiple_zero

end PortCAS02
