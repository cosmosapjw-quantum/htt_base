import Mathlib

/-! Independent finite/local formalization of CAS-01, derivative-first convention. -/

namespace GRSTATCAS01

abbrev V := Fin 4 → ℝ
abbrev Form := Fin 4 → Fin 4 → ℝ

def eps : Fin 4 → ℝ := ![-1, 1, 1, 1]
def g (x y : V) : ℝ := ∑ i, eps i * x i * y i
def eval (S : Form) (x y : V) : ℝ := ∑ i, ∑ j, S i j * x i * y j
def flat (u : V) : V := fun i => eps i * u i
def cov (S : Form) (u : V) : V := fun i => ∑ j, S i j * u j
def B (S : Form) (u : V) : Form := fun i j => S i j + eval S u u * (if i = j then eps i else 0)
def sym (S : Form) : Prop := ∀ i j, S i j = S j i

private theorem eval_diag (x y : V) :
    eval (fun i j => if i = j then eps i else 0) x y = g x y := by
  simp [eval, g]

private theorem eval_scale_diag (a : ℝ) (x y : V) :
    eval (fun i j => a * (if i = j then eps i else 0)) x y = a * g x y := by
  simp [eval, g, Finset.mul_sum, mul_left_comm, mul_comm]

private theorem eval_add (S T : Form) (x y : V) :
    eval (fun i j => S i j + T i j) x y = eval S x y + eval T x y := by
  simp [eval, Finset.sum_add_distrib, add_mul]

def shift (S : Form) (a : ℝ) : Form :=
  fun i j => S i j + a * (if i = j then eps i else 0)

theorem B_shift (S : Form) (u : V) (a : ℝ) (hu : g u u = -1) :
    B (shift S a) u = B S u := by
  have he : eval (shift S a) u u = eval S u u - a := by
    calc
      eval (shift S a) u u = eval S u u +
          eval (fun i j => a * (if i = j then eps i else 0)) u u := by
            exact eval_add S _ u u
      _ = _ := by rw [eval_scale_diag, hu]; ring
  funext i j
  simp only [B, shift]
  rw [he]
  ring

def K (x y z : ℝ) : V := ![-1, x, y, z]

/- A symmetric quadratic form zero on every future sourceward null direction
   has exactly the metric as its one-dimensional kernel. The finite samples
   below eliminate every polynomial coefficient; the hypothesis itself is
   universal over the unit sphere. -/
theorem null_cone_kernel (T : Form) (hT : sym T)
    (hzero : ∀ x y z : ℝ, x*x + y*y + z*z = 1 →
      eval T (K x y z) (K x y z) = 0) :
    ∃ a : ℝ, T = fun i j => a * (if i = j then eps i else 0) := by
  let a : ℝ := -T 0 0
  have h100 := hzero 1 0 0 (by norm_num)
  have hm100 := hzero (-1) 0 0 (by norm_num)
  have h010 := hzero 0 1 0 (by norm_num)
  have h0m10 := hzero 0 (-1) 0 (by norm_num)
  have h001 := hzero 0 0 1 (by norm_num)
  have h00m1 := hzero 0 0 (-1) (by norm_num)
  have h340 := hzero (3/5) (4/5) 0 (by norm_num)
  have hm340 := hzero (3/5) (-4/5) 0 (by norm_num)
  have h304 := hzero (3/5) 0 (4/5) (by norm_num)
  have hm304 := hzero (3/5) 0 (-4/5) (by norm_num)
  have h034 := hzero 0 (3/5) (4/5) (by norm_num)
  have hm034 := hzero 0 (3/5) (-4/5) (by norm_num)
  simp [eval, K, Fin.sum_univ_succ] at h100 hm100 h010 h0m10 h001 h00m1 h340 hm340 h304 hm304 h034 hm034
  have d1 : T 1 1 = -T 0 0 := by linarith only [h100, hm100]
  have d2 : T 2 2 = -T 0 0 := by linarith only [h010, h0m10]
  have d3 : T 3 3 = -T 0 0 := by linarith only [h001, h00m1]
  have z01 : T 0 1 = 0 := by linarith only [h100, hm100, hT 0 1]
  have z02 : T 0 2 = 0 := by linarith only [h010, h0m10, hT 0 2]
  have z03 : T 0 3 = 0 := by linarith only [h001, h00m1, hT 0 3]
  have z12 : T 1 2 = 0 := by linarith only [h340, hm340, z02, hT 2 0, hT 1 2]
  have z13 : T 1 3 = 0 := by linarith only [h304, hm304, z03, hT 3 0, hT 1 3]
  have z23 : T 2 3 = 0 := by linarith only [h034, hm034, z03, hT 3 0, hT 2 3]
  refine ⟨a, ?_⟩
  funext i j
  fin_cases i <;> fin_cases j <;> simp [a, eps] <;>
    linarith only [d1, d2, d3, z01, z02, z03, z12, z13, z23,
      hT 0 1, hT 0 2, hT 0 3, hT 1 2, hT 1 3, hT 2 3]

theorem B_unit (S : Form) (u : V) (hu : g u u = -1) :
    eval (B S u) u u = 0 := by
  have h : eval (B S u) u u = eval S u u + eval S u u * g u u := by
    calc
      eval (B S u) u u = eval S u u +
          eval (fun i j => eval S u u * (if i = j then eps i else 0)) u u := by
            simp [eval, B, Finset.sum_add_distrib, add_mul]
      _ = _ := by rw [eval_scale_diag]
  rw [h, hu]
  ring

theorem B_symmetric (S : Form) (u : V) (hS : sym S) : sym (B S u) := by
  intro i j
  simp only [B]
  rw [hS i j]
  by_cases hij : i = j
  · subst j; rfl
  · simp [hij, Ne.symm hij]

def skew (W : Form) : Prop := ∀ i j, W i j = -W j i
def spatial (W : Form) (u : V) : Prop := ∀ i, cov W u i = 0
def contractL (T : Form) (u : V) : V := fun j => ∑ i, u i * T i j
def Q (T W : Form) (u : V) : Form := fun i j =>
  T i j + cov T u i * flat u j - flat u i * cov T u j + W i j
noncomputable def symPart (T : Form) : Form := fun i j => (T i j + T j i) / 2

private theorem cov_flat (u : V) : (∑ j, flat u j * u j) = g u u := by
  simp [flat, g, mul_assoc, mul_left_comm, mul_comm]

private theorem cov_contract (T : Form) (u : V) :
    (∑ i, cov T u i * u i) = eval T u u := by
  simp only [cov, eval]
  congr 1
  ext i
  rw [Finset.sum_mul]
  congr 1
  ext j
  ring

private theorem contractL_sym (T : Form) (u : V) (hT : sym T) (j : Fin 4) :
    contractL T u j = cov T u j := by
  simp only [contractL, cov]
  apply Finset.sum_congr rfl
  intro i _
  rw [hT i j]
  ring

private theorem contractL_skew (W : Form) (u : V)
    (hW : skew W) (hsp : spatial W u) (j : Fin 4) :
    contractL W u j = 0 := by
  calc
    contractL W u j = -cov W u j := by
      simp only [contractL, cov, ← Finset.sum_neg_distrib]
      apply Finset.sum_congr rfl
      intro i _
      rw [hW i j]
      ring
    _ = 0 := by rw [hsp j]; ring

theorem Q_right_null (T W : Form) (u : V)
    (hu : g u u = -1) (hTu : eval T u u = 0)
    (hW : spatial W u) : ∀ i, cov (Q T W u) u i = 0 := by
  intro i
  have h : cov (Q T W u) u i = cov T u i +
      cov T u i * g u u - flat u i * eval T u u + cov W u i := by
    have h1 : (∑ j, (cov T u i * flat u j) * u j) = cov T u i * g u u := by
      rw [← cov_flat u]
      simp [Finset.mul_sum, mul_assoc]
    have h2 : (∑ j, (flat u i * cov T u j) * u j) = flat u i * eval T u u := by
      rw [← cov_contract T u]
      simp [Finset.mul_sum, mul_assoc]
    simp only [cov, Q, add_mul, sub_mul, Finset.sum_add_distrib,
      Finset.sum_sub_distrib]
    simp only [cov] at h1 h2
    rw [h1, h2]
  rw [h, hu, hTu, hW i]
  ring

theorem Q_symmetric_part (T W : Form) (u : V)
    (hT : sym T) (hW : skew W) : symPart (Q T W u) = T := by
  funext i j
  simp only [symPart, Q]
  rw [hT j i, hW j i]
  ring

theorem Q_left_acceleration (T W : Form) (u : V) (c : ℝ)
    (hT : sym T) (hW : skew W) (hsp : spatial W u)
    (hu : g u u = -1) (hTu : eval T u u = 0) :
    ∀ j, c * contractL (Q T W u) u j = 2*c*cov T u j := by
  intro j
  have h : contractL (Q T W u) u j = contractL T u j +
      eval T u u * flat u j - g u u * cov T u j + contractL W u j := by
    have h1 : (∑ i, u i * (cov T u i * flat u j)) =
        eval T u u * flat u j := by
      rw [← cov_contract T u]
      rw [Finset.sum_mul]
      apply Finset.sum_congr rfl
      intro i _
      ring
    have h2 : (∑ i, u i * (flat u i * cov T u j)) =
        g u u * cov T u j := by
      rw [← cov_flat u]
      rw [Finset.sum_mul]
      apply Finset.sum_congr rfl
      intro i _
      ring
    simp only [contractL, Q, mul_add, mul_sub, Finset.sum_add_distrib,
      Finset.sum_sub_distrib]
    rw [h1, h2]
  rw [h, contractL_sym T u hT j, hTu, hu,
    contractL_skew W u hW hsp j]
  ring

def hcov (u : V) : Form := fun i j =>
  (if i = j then eps i else 0) + flat u i * flat u j
def D (T : Form) (u : V) : Form := fun i j =>
  T i j + flat u i * cov T u j + cov T u i * flat u j
def traceg (T : Form) : ℝ := ∑ i, eps i * T i i
noncomputable def sigma (T : Form) (u : V) : Form := fun i j =>
  D T u i j - traceg T / 3 * hcov u i j

theorem D_spatial (T : Form) (u : V)
    (hu : g u u = -1) (hTu : eval T u u = 0) :
    ∀ i, cov (D T u) u i = 0 := by
  intro i
  have h1 : (∑ j, (flat u i * cov T u j) * u j) =
      flat u i * eval T u u := by
    rw [← cov_contract T u]
    simp [Finset.mul_sum, mul_assoc]
  have h2 : (∑ j, (cov T u i * flat u j) * u j) =
      cov T u i * g u u := by
    rw [← cov_flat u]
    simp [Finset.mul_sum, mul_assoc]
  simp only [cov, D, add_mul, Finset.sum_add_distrib]
  simp only [cov] at h1 h2
  rw [h1, h2]
  simp [hTu, hu]

theorem D_symmetric (T : Form) (u : V) (hT : sym T) : sym (D T u) := by
  intro i j
  simp only [D]
  rw [hT i j]
  ring

private theorem trace_flat_cov (T : Form) (u : V) :
    (∑ i, eps i * (flat u i * cov T u i)) = eval T u u := by
  have hi : ∀ i : Fin 4, eps i * flat u i = u i := by
    intro i; fin_cases i <;> simp [eps, flat] <;> ring
  simp_rw [← mul_assoc, hi]
  rw [← cov_contract T u]
  apply Finset.sum_congr rfl
  intro i _
  ring

theorem trace_D (T : Form) (u : V) (hTu : eval T u u = 0) :
    traceg (D T u) = traceg T := by
  simp only [traceg, D, mul_add, Finset.sum_add_distrib]
  rw [trace_flat_cov T u]
  have h2 : (∑ i, eps i * (cov T u i * flat u i)) = eval T u u := by
    convert trace_flat_cov T u using 1
    apply Finset.sum_congr rfl
    intro i _
    ring
  rw [h2, hTu]
  ring

theorem hcov_spatial (u : V) (hu : g u u = -1) :
    ∀ i, cov (hcov u) u i = 0 := by
  intro i
  have h1 : (∑ j, (if i = j then eps i else 0) * u j) = flat u i := by
    simp [flat]
  have h2 : (∑ j, (flat u i * flat u j) * u j) = flat u i * g u u := by
    rw [← cov_flat u]
    simp [Finset.mul_sum, mul_assoc]
  simp only [cov, hcov, add_mul, Finset.sum_add_distrib]
  rw [h1, h2, hu]
  ring

theorem trace_hcov (u : V) (hu : g u u = -1) :
    traceg (hcov u) = 3 := by
  have h1 : (∑ i, eps i * (flat u i * flat u i)) = g u u := by
    simp [flat, g, Fin.sum_univ_succ, eps]
  simp only [traceg, hcov, mul_add, Finset.sum_add_distrib]
  rw [h1, hu]
  norm_num [Fin.sum_univ_succ, eps]

theorem sigma_spatial (T : Form) (u : V)
    (hu : g u u = -1) (hTu : eval T u u = 0) :
    ∀ i, cov (sigma T u) u i = 0 := by
  intro i
  have h1 := D_spatial T u hu hTu i
  have h2 := hcov_spatial u hu i
  have h3 : (∑ j, (traceg T / 3 * hcov u i j) * u j) =
      traceg T / 3 * cov (hcov u) u i := by
    simp [cov, Finset.mul_sum, mul_assoc]
  simp only [cov, sigma, sub_mul, Finset.sum_sub_distrib]
  simp only [cov] at h1 h2 h3
  rw [h3, h1, h2]
  ring

theorem sigma_tracefree (T : Form) (u : V)
    (hu : g u u = -1) (hTu : eval T u u = 0) :
    traceg (sigma T u) = 0 := by
  have h1 := trace_D T u hTu
  have h2 := trace_hcov u hu
  have h3 : (∑ i, eps i * (traceg T / 3 * hcov u i i)) =
      traceg T / 3 * traceg (hcov u) := by
    simp [traceg, Finset.mul_sum, mul_assoc, mul_left_comm, mul_comm]
  simp only [traceg, sigma, mul_sub, Finset.sum_sub_distrib]
  simp only [traceg] at h3
  rw [h3]
  change traceg (D T u) - traceg T / 3 * traceg (hcov u) = 0
  rw [h1, h2]
  ring

def mixedProj (u : V) : Form := fun i k =>
  (if i = k then 1 else 0) + flat u i * u k
def projected (T : Form) (u : V) : Form := fun i j =>
  ∑ k, ∑ l, mixedProj u i k * mixedProj u j l * T k l

private theorem projected_expand (T : Form) (u : V) (i j : Fin 4) :
    projected T u i j = T i j + flat u i * contractL T u j +
      flat u j * cov T u i + flat u i * flat u j * eval T u u := by
  simp [projected, mixedProj, contractL, cov, eval,
    Finset.sum_add_distrib, add_mul, mul_add, Finset.mul_sum,
    Finset.sum_mul, mul_assoc, mul_left_comm, mul_comm]
  ring

theorem projected_eq_D (T : Form) (u : V)
    (hT : sym T) (hTu : eval T u u = 0) :
    projected T u = D T u := by
  funext i j
  rw [projected_expand, contractL_sym T u hT j, hTu]
  simp [D, mul_comm, mul_left_comm, mul_assoc]

theorem C02_from_symmetric_source (S W : Form) (u : V) (c : ℝ)
    (hS : sym S) (hu : g u u = -1) (_hfuture : 0 < u 0)
    (_hc : 0 < c) (hW : skew W) (hsp : spatial W u) :
    (∀ i, cov (Q (B S u) W u) u i = 0) ∧
    symPart (Q (B S u) W u) = B S u ∧
    (∀ j, c * contractL (Q (B S u) W u) u j = 2*c*cov (B S u) u j) ∧
    projected (B S u) u = D (B S u) u ∧
    (∀ i, cov (sigma (B S u) u) u i = 0) ∧
    traceg (sigma (B S u) u) = 0 := by
  have hB := B_unit S u hu
  have hBs := B_symmetric S u hS
  exact ⟨Q_right_null (B S u) W u hu hB hsp,
    Q_symmetric_part (B S u) W u hBs hW,
    Q_left_acceleration (B S u) W u c hBs hW hsp hu hB,
    projected_eq_D (B S u) u hBs hB,
    sigma_spatial (B S u) u hu hB,
    sigma_tracefree (B S u) u hu hB⟩

theorem traceg_rest (T : Form) (h00 : T 0 0 = 0) :
    traceg T = T 1 1 + T 2 2 + T 3 3 := by
  simp [traceg, Fin.sum_univ_succ, eps, h00]
  ring


def rest : V := ![1, 0, 0, 0]
theorem rest_unit : g rest rest = -1 := by
  norm_num [g, rest, eps, Fin.sum_univ_succ]

theorem cov_rest (T : Form) (i : Fin 4) : cov T rest i = T i 0 := by
  simp [cov, rest, Fin.sum_univ_succ]
def thetaRest (T : Form) : ℝ := T 1 1 + T 2 2 + T 3 3
noncomputable def sigmaRest (T : Form) : Form := fun i j =>
  T i j - (thetaRest T / 3) * (if i = j then eps i else 0)

theorem rest_H_decomposition (T : Form) (c x y z : ℝ) (hc : 0 < c)
    (hT : sym T) (h00 : T 0 0 = 0)
    (hn : x*x + y*y + z*z = 1) :
    eval T (K x y z) (K x y z) = thetaRest T / 3 +
      (sigmaRest T 1 1 * x*x + sigmaRest T 2 2 * y*y + sigmaRest T 3 3 * z*z +
       2*sigmaRest T 1 2*x*y + 2*sigmaRest T 1 3*x*z + 2*sigmaRest T 2 3*y*z) -
      ((2*c*T 1 0)*x + (2*c*T 2 0)*y + (2*c*T 3 0)*z)/c := by
  simp [eval, K, thetaRest, sigmaRest, Fin.sum_univ_succ]
  rw [h00, hT 1 0, hT 2 0, hT 3 0, hT 2 1, hT 3 1, hT 3 2]
  simp [eps]
  field_simp
  linear_combination (T 1 1 + T 2 2 + T 3 3) * hn

theorem C03_B_rest (S : Form) (c x y z : ℝ)
    (hS : sym S) (hc : 0 < c) (hn : x*x + y*y + z*z = 1) :
    eval (B S rest) (K x y z) (K x y z) =
      thetaRest (B S rest) / 3 +
      (sigmaRest (B S rest) 1 1 * x*x +
       sigmaRest (B S rest) 2 2 * y*y +
       sigmaRest (B S rest) 3 3 * z*z +
       2*sigmaRest (B S rest) 1 2*x*y +
       2*sigmaRest (B S rest) 1 3*x*z +
       2*sigmaRest (B S rest) 2 3*y*z) -
      ((2*c*(B S rest) 1 0)*x + (2*c*(B S rest) 2 0)*y +
       (2*c*(B S rest) 3 0)*z)/c := by
  have h00 : B S rest 0 0 = 0 := by
    have hb := B_unit S rest rest_unit
    simpa [eval, rest, Fin.sum_univ_succ] using hb
  exact rest_H_decomposition (B S rest) c x y z hc (B_symmetric S rest hS) h00 hn

noncomputable def sourceS (h0 h1x h1y h1z hxx hyy hzz hxy hxz hyz : ℝ) : Form :=
  ![![h0, -h1x/2, -h1y/2, -h1z/2],
    ![-h1x/2, hxx, hxy, hxz],
    ![-h1y/2, hxy, hyy, hyz],
    ![-h1z/2, hxz, hyz, hzz]]

theorem general_sourceward_harmonics
    (h0 h1x h1y h1z hxx hyy hzz hxy hxz hyz x y z : ℝ)
    (hSTF : hxx + hyy + hzz = 0) :
    eval (sourceS h0 h1x h1y h1z hxx hyy hzz hxy hxz hyz)
      (K x y z) (K x y z) =
      h0 + h1x*x + h1y*y + h1z*z +
      (hxx*x*x + hyy*y*y + hzz*z*z +
       2*hxy*x*y + 2*hxz*x*z + 2*hyz*y*z) := by
  simp [eval, sourceS, K, Fin.sum_univ_succ]
  ring

noncomputable def seedDirection (Q : Form) (c : ℝ) (k : Fin 4) : V :=
  fun b => eps b * Q k b / c
noncomputable def seedLine (u : V) (Q : Form) (c : ℝ)
    (k : Fin 4) (t : ℝ) : V := fun b => u b + t * seedDirection Q c k b
noncomputable def normSeedLine (u : V) (Q : Form) (c : ℝ)
    (k : Fin 4) (t : ℝ) : V := fun b =>
  seedLine u Q c k t b / Real.sqrt (-g (seedLine u Q c k t) (seedLine u Q c k t))

theorem seedLine_at_origin (u : V) (Q : Form) (c : ℝ) (k : Fin 4) :
    seedLine u Q c k 0 = u := by
  funext b
  simp [seedLine]

theorem normalized_at_origin (u : V) (Q : Form) (c : ℝ) (k : Fin 4)
    (hu : g u u = -1) : normSeedLine u Q c k 0 = u := by
  funext b
  simp [normSeedLine, seedLine_at_origin, hu]

private theorem g_line (u d : V) (t : ℝ) :
    g (fun b => u b + t*d b) (fun b => u b + t*d b) =
      g u u + 2*t*g u d + t*t*g d d := by
  calc
    _ = ∑ i, (eps i * u i * u i + 2*t*eps i*u i*d i + t*t*eps i*d i*d i) := by
      apply Finset.sum_congr rfl
      intro i _
      dsimp [g]
      ring
    _ = _ := by
      simp [g, Finset.sum_add_distrib, Finset.mul_sum,
        mul_assoc, mul_left_comm, mul_comm]

private theorem seed_direction_orthogonal (u : V) (Q : Form) (c : ℝ)
    (k : Fin 4) (hc : 0 < c) (hQ : cov Q u k = 0) :
    g u (seedDirection Q c k) = 0 := by
  have hi : ∀ i : Fin 4,
      eps i * u i * seedDirection Q c k i = (Q k i * u i) / c := by
    intro i
    fin_cases i <;> simp [eps, seedDirection] <;> ring
  calc
    g u (seedDirection Q c k) = ∑ i, (Q k i * u i) / c := by
      simp only [g]
      apply Finset.sum_congr rfl
      intro i _
      exact hi i
    _ = (cov Q u k) / c := by simp [cov, Finset.sum_div]
    _ = 0 := by rw [hQ]; ring

private theorem normalized_line_derivative (u d : V) (b : Fin 4)
    (hu : g u u = -1) (hud : g u d = 0) :
    HasDerivAt
      (fun t : ℝ => (u b + t*d b) /
        Real.sqrt (-g (fun i => u i + t*d i) (fun i => u i + t*d i)))
      (d b) 0 := by
  have hn : (fun t : ℝ => -g (fun i => u i + t*d i) (fun i => u i + t*d i)) =
      (fun t : ℝ => 1 - t*t*g d d) := by
    funext t
    rw [g_line, hu, hud]
    ring
  have hv : HasDerivAt (fun t : ℝ => u b + t*d b) (d b) 0 := by
    simpa using ((hasDerivAt_id (0:ℝ)).mul_const (d b)).const_add (u b)
  have hp : HasDerivAt (fun t : ℝ => t*t) 0 0 := by
    convert (hasDerivAt_id (0:ℝ)).mul (hasDerivAt_id (0:ℝ)) using 1 <;>
      first | rfl | (funext t; rfl) | norm_num
  have hin : HasDerivAt (fun t : ℝ => 1 - t*t*g d d) 0 0 := by
    simpa using (hp.mul_const (g d d)).const_sub (1:ℝ)
  have hs : HasDerivAt (fun t : ℝ => Real.sqrt (1 - t*t*g d d)) 0 0 := by
    simpa using hin.sqrt (by norm_num)
  have hdiv : HasDerivAt
      (fun t : ℝ => (u b + t*d b) / Real.sqrt (1 - t*t*g d d))
      (d b) 0 := by
    convert hv.div hs (by norm_num) using 1 <;>
      first | rfl | (funext t; rfl) | norm_num
  have heval (t : ℝ) :
      -g (fun i => u i + t*d i) (fun i => u i + t*d i) = 1 - t*t*g d d :=
    congrFun hn t
  convert hdiv using 1
  funext t
  rw [heval t]

theorem normalized_seed_jet (u : V) (Q : Form) (c : ℝ) (k b : Fin 4)
    (hc : 0 < c) (hu : g u u = -1) (hQ : cov Q u k = 0) :
    HasDerivAt (fun t : ℝ => normSeedLine u Q c k t b)
      (eps b * Q k b / c) 0 := by
  have hd := seed_direction_orthogonal u Q c k hc hQ
  change HasDerivAt
    (fun t : ℝ => (u b + t*seedDirection Q c k b) /
      Real.sqrt (-g (fun i => u i+t*seedDirection Q c k i)
        (fun i => u i+t*seedDirection Q c k i)))
    (seedDirection Q c k b) 0
  exact normalized_line_derivative u (seedDirection Q c k) b hu hd

noncomputable def fullSeed (u : V) (Q : Form) (c : ℝ) (x : V) : V :=
  fun b => u b + ∑ a, x a * (eps b * Q a b / c)
noncomputable def fullNormalized (u : V) (Q : Form) (c : ℝ) (x : V) : V :=
  fun b => fullSeed u Q c x b / Real.sqrt (-g (fullSeed u Q c x) (fullSeed u Q c x))
def coordinateLine (k : Fin 4) (t : ℝ) : V := fun a => if a = k then t else 0

theorem fullSeed_coordinateLine (u : V) (Q : Form) (c : ℝ)
    (k : Fin 4) (t : ℝ) :
    fullSeed u Q c (coordinateLine k t) = seedLine u Q c k t := by
  funext b
  simp [fullSeed, coordinateLine, seedLine, seedDirection]

theorem fullNormalized_origin (u : V) (Q : Form) (c : ℝ)
    (hu : g u u = -1) :
    fullNormalized u Q c (fun _ => 0) = u := by
  have hseed : fullSeed u Q c (fun _ => 0) = u := by
    funext i
    simp [fullSeed]
  funext b
  simp [fullNormalized, hseed, hu]

theorem fullNormalized_coordinate_derivative
    (u : V) (Q : Form) (c : ℝ) (k b : Fin 4)
    (hc : 0 < c) (hu : g u u = -1) (hQ : cov Q u k = 0) :
    HasDerivAt (fun t : ℝ => fullNormalized u Q c (coordinateLine k t) b)
      (eps b * Q k b / c) 0 := by
  have he : ∀ t : ℝ, fullNormalized u Q c (coordinateLine k t) =
      normSeedLine u Q c k t := by
    intro t
    funext i
    simp [fullNormalized, normSeedLine, fullSeed_coordinateLine]
  simpa only [he] using normalized_seed_jet u Q c k b hc hu hQ

theorem C04_from_symmetric_source (S W : Form) (u : V) (c : ℝ)
    (_hS : sym S) (hu : g u u = -1) (_hfuture : 0 < u 0)
    (hc : 0 < c) (_hskew : skew W) (hsp : spatial W u) :
    fullNormalized u (Q (B S u) W u) c (fun _ => 0) = u ∧
      ∀ k b, HasDerivAt
        (fun t : ℝ => fullNormalized u (Q (B S u) W u) c
          (coordinateLine k t) b)
        (eps b * Q (B S u) W u k b / c) 0 := by
  refine ⟨fullNormalized_origin u _ c hu, ?_⟩
  intro k b
  exact fullNormalized_coordinate_derivative u _ c k b hc hu
    (Q_right_null (B S u) W u hu (B_unit S u hu) hsp k)

#print axioms B_unit
#print axioms B_shift
#print axioms B_symmetric
#print axioms null_cone_kernel
#print axioms Q_right_null
#print axioms Q_symmetric_part
#print axioms Q_left_acceleration
#print axioms C02_from_symmetric_source
#print axioms D_spatial
#print axioms sigma_spatial
#print axioms sigma_tracefree
#print axioms projected_eq_D
#print axioms traceg_rest
#print axioms cov_rest
#print axioms rest_H_decomposition
#print axioms C03_B_rest
#print axioms general_sourceward_harmonics
#print axioms fullNormalized_origin
#print axioms fullNormalized_coordinate_derivative
#print axioms C04_from_symmetric_source

end GRSTATCAS01
