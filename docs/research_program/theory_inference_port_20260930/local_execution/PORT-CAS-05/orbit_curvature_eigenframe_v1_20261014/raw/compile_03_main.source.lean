import Mathlib
import EigenframeGap

/-!
# P05-A: spatial orbit curvature and invariant-eigenframe connection (Lie-algebra model)

Finite-dimensional, orthonormal constant-frame model. Index conventions follow
`htt/src/common/relativistic_kinematics.py` (`C[k,i,j]`, `Gamma[k,i,j]`, `derivative[k,i,j]`)
and `wolfram_curvature.wl` lines 3-6. No manifold, homogeneity neighborhood, spacetime action
or rest-bundle slice is modelled here.
-/

open Matrix

namespace PORTCAS05OrbitCurvature

/-- Levi-Civita symbol on `Fin 3`, `eps3 0 1 2 = 1`. -/
def eps3 : Fin 3 → Fin 3 → Fin 3 → ℝ :=
  ![![![0, 0, 0], ![0, 0, 1], ![0, -1, 0]],
    ![![0, 0, -1], ![0, 0, 0], ![1, 0, 0]],
    ![![0, 1, 0], ![-1, 0, 0], ![0, 0, 0]]]

/-- Kronecker delta. -/
def kd {d : ℕ} (i j : Fin d) : ℝ := if i = j then 1 else 0

/-- `C^k_{ij} = eps_{ijl} n^{lk} + a_i δ^k_j - a_j δ^k_i`, with `[e_i,e_j] = Σ_k C k i j • e_k`. -/
def Cna (n : Matrix (Fin 3) (Fin 3) ℝ) (a : Fin 3 → ℝ) (k i j : Fin 3) : ℝ :=
  (∑ l, eps3 i j l * n l k) + a i * kd k j - a j * kd k i

/-- Bracket of frame-component vectors defined by structure constants. -/
def bracket {d : ℕ} (C : Fin d → Fin d → Fin d → ℝ) (x y : Fin d → ℝ) : Fin d → ℝ :=
  fun k => ∑ i, ∑ j, C k i j * x i * y j

/-- Component `i` of `[e_l,[e_j,e_k]] + [e_j,[e_k,e_l]] + [e_k,[e_l,e_j]]`. -/
def jacobiResidual {d : ℕ} (C : Fin d → Fin d → Fin d → ℝ) (i j k l : Fin d) : ℝ :=
  ∑ m, (C m j k * C i l m + C m k l * C i j m + C m l j * C i k m)

/-- Antisymmetry of structure constants in the lower indices. -/
def Antisymm {d : ℕ} (C : Fin d → Fin d → Fin d → ℝ) : Prop :=
  ∀ k i j : Fin d, C k i j = -C k j i

/-- Koszul coefficients `Γ^k_{ij} = ⟨∇_{e_i} e_j, e_k⟩` in an orthonormal constant frame. -/
def koszul {d : ℕ} (C : Fin d → Fin d → Fin d → ℝ) (k i j : Fin d) : ℝ :=
  (C k i j - C i j k + C j k i) / 2

/-- Metric compatibility in an orthonormal frame: `Γ^k_{ij} = -Γ^j_{ik}`. -/
def MetricCompatible {d : ℕ} (Γ : Fin d → Fin d → Fin d → ℝ) : Prop :=
  ∀ k i j : Fin d, Γ k i j = -Γ j i k

/-- Zero torsion: `Γ^k_{ij} - Γ^k_{ji} = C^k_{ij}`. -/
def TorsionFree {d : ℕ} (Γ C : Fin d → Fin d → Fin d → ℝ) : Prop :=
  ∀ k i j : Fin d, Γ k i j - Γ k j i = C k i j

/-- `riem C i l j k = ⟨R(e_j,e_k) e_l, e_i⟩` for the Koszul connection of `C`. -/
def riem {d : ℕ} (C : Fin d → Fin d → Fin d → ℝ) (i l j k : Fin d) : ℝ :=
  ∑ m, (koszul C m k l * koszul C i j m - koszul C m j l * koszul C i k m
        - C m j k * koszul C i m l)

/-- Ricci contraction `Ric_{lk} = Σ_i R^i_{l i k}`. -/
def ricci {d : ℕ} (C : Fin d → Fin d → Fin d → ℝ) (l k : Fin d) : ℝ := ∑ i, riem C i l i k

/-- Scalar curvature `Σ_{i,j} R^i_{j i j}`. -/
def scal {d : ℕ} (C : Fin d → Fin d → Fin d → ℝ) : ℝ := ∑ i, ∑ j, riem C i j i j

/-- `(D_k T)_{ij}` for a tensor with frame-constant components. -/
def DT {d : ℕ} (Γ : Fin d → Fin d → Fin d → ℝ) (T : Matrix (Fin d) (Fin d) ℝ) (k i j : Fin d) : ℝ :=
  -(∑ m, Γ m k i * T m j) - (∑ m, Γ m k j * T i m)

/-- Trace form `Σ_k C^k_{ik}` (unimodularity). -/
def traceForm {d : ℕ} (C : Fin d → Fin d → Fin d → ℝ) (i : Fin d) : ℝ := ∑ k, C k i k

/-- Reconstructed `Γ^j_{ki}` from eigenframe derivative data (Python line 385). -/
def reconGamma {d : ℕ} (D : Fin d → Fin d → Fin d → ℝ) (lam : Fin d → ℝ) (j k i : Fin d) : ℝ :=
  if i = j then 0 else D k i j / (lam i - lam j)

/-- Reconstructed `C^j_{ki} = Γ^j_{ki} - Γ^j_{ik}` (Python line 386). -/
def reconC {d : ℕ} (D : Fin d → Fin d → Fin d → ℝ) (lam : Fin d → ℝ) (j k i : Fin d) : ℝ :=
  reconGamma D lam j k i - reconGamma D lam j i k

/-! ## T1: Koszul connection -/

theorem koszul_metricCompatible {d : ℕ} {C : Fin d → Fin d → Fin d → ℝ} (hC : Antisymm C) :
    MetricCompatible (koszul C) := by
  intro k i j
  have h1 := hC j i k
  have h2 := hC i k j
  have h3 := hC k j i
  simp only [koszul]
  linarith

theorem koszul_torsionFree {d : ℕ} {C : Fin d → Fin d → Fin d → ℝ} (hC : Antisymm C) :
    TorsionFree (koszul C) C := by
  intro k i j
  have h1 := hC k j i
  have h2 := hC j i k
  have h3 := hC i k j
  simp only [koszul]
  linarith

theorem koszul_unique {d : ℕ} {C Γ : Fin d → Fin d → Fin d → ℝ}
    (hm : MetricCompatible Γ) (ht : TorsionFree Γ C) : Γ = koszul C := by
  funext k i j
  have t1 := ht k i j
  have t2 := ht i j k
  have t3 := ht j k i
  have m1 := hm k j i
  have m2 := hm i k j
  have m3 := hm j i k
  simp only [koszul]
  linarith

/-! ## T2-T3: structure constants, Jacobi, Lie bracket -/

theorem Cna_antisymm (n : Matrix (Fin 3) (Fin 3) ℝ) (a : Fin 3 → ℝ) : Antisymm (Cna n a) := by
  intro k i j
  fin_cases i <;> fin_cases j <;> simp [Cna, eps3, Fin.sum_univ_three] <;> ring

theorem jacobiResidual_Cna {n : Matrix (Fin 3) (Fin 3) ℝ} (hn : n.IsSymm) (a : Fin 3 → ℝ)
    (i j k l : Fin 3) :
    jacobiResidual (Cna n a) i j k l = -2 * eps3 j k l * (n *ᵥ a) i := by
  have h10 : n 1 0 = n 0 1 := hn.apply 0 1
  have h20 : n 2 0 = n 0 2 := hn.apply 0 2
  have h21 : n 2 1 = n 1 2 := hn.apply 1 2
  fin_cases i <;> fin_cases j <;> fin_cases k <;> fin_cases l <;>
    simp [jacobiResidual, Cna, eps3, kd, Fin.sum_univ_three, Matrix.mulVec, dotProduct,
      h10, h20, h21] <;> ring

theorem jacobi_iff_na_zero {n : Matrix (Fin 3) (Fin 3) ℝ} (hn : n.IsSymm) (a : Fin 3 → ℝ) :
    (∀ i j k l, jacobiResidual (Cna n a) i j k l = 0) ↔ n *ᵥ a = 0 := by
  constructor
  · intro h
    funext i
    have h' := h i 0 1 2
    have e : eps3 0 1 2 = 1 := by simp [eps3]
    rw [jacobiResidual_Cna hn, e] at h'
    simp only [Pi.zero_apply]
    linarith
  · intro hna i j k l
    rw [jacobiResidual_Cna hn, hna]
    simp

theorem bracket_antisymm {d : ℕ} {C : Fin d → Fin d → Fin d → ℝ} (hC : Antisymm C)
    (x y : Fin d → ℝ) : bracket C x y = -bracket C y x := by
  funext k
  simp only [bracket, Pi.neg_apply]
  conv_rhs => rw [Finset.sum_comm]
  rw [← Finset.sum_neg_distrib]
  refine Finset.sum_congr rfl (fun i _ => ?_)
  rw [← Finset.sum_neg_distrib]
  refine Finset.sum_congr rfl (fun j _ => ?_)
  rw [hC k i j]
  ring

theorem bracket_jacobi {n : Matrix (Fin 3) (Fin 3) ℝ} (hn : n.IsSymm) {a : Fin 3 → ℝ}
    (hna : n *ᵥ a = 0) (x y z : Fin 3 → ℝ) :
    bracket (Cna n a) x (bracket (Cna n a) y z) + bracket (Cna n a) y (bracket (Cna n a) z x)
      + bracket (Cna n a) z (bracket (Cna n a) x y) = 0 := by
  have h10 : n 1 0 = n 0 1 := hn.apply 0 1
  have h20 : n 2 0 = n 0 2 := hn.apply 0 2
  have h21 : n 2 1 = n 1 2 := hn.apply 1 2
  have e0 : n 0 0 * a 0 + n 0 1 * a 1 + n 0 2 * a 2 = 0 := by
    simpa [Matrix.mulVec, dotProduct, Fin.sum_univ_three] using congrFun hna 0
  have e1 : n 0 1 * a 0 + n 1 1 * a 1 + n 1 2 * a 2 = 0 := by
    simpa [Matrix.mulVec, dotProduct, Fin.sum_univ_three, h10] using congrFun hna 1
  have e2 : n 0 2 * a 0 + n 1 2 * a 1 + n 2 2 * a 2 = 0 := by
    simpa [Matrix.mulVec, dotProduct, Fin.sum_univ_three, h20, h21] using congrFun hna 2
  set D := x 0 * (y 1 * z 2 - y 2 * z 1) - x 1 * (y 0 * z 2 - y 2 * z 0)
    + x 2 * (y 0 * z 1 - y 1 * z 0) with hD
  funext k
  fin_cases k
  · simp [bracket, Cna, eps3, kd, Fin.sum_univ_three, h10, h20, h21]
    linear_combination (-2 * D) * e0
  · simp [bracket, Cna, eps3, kd, Fin.sum_univ_three, h10, h20, h21]
    linear_combination (-2 * D) * e1
  · simp [bracket, Cna, eps3, kd, Fin.sum_univ_three, h10, h20, h21]
    linear_combination (-2 * D) * e2

/-! ## T4-T5: scalar curvature, Ricci symmetry, units -/

theorem scal_Cna_of_symm {n : Matrix (Fin 3) (Fin 3) ℝ} (hn : n.IsSymm) (a : Fin 3 → ℝ) :
    scal (Cna n a) = -trace (n * n) + (trace n) ^ 2 / 2 - 6 * (a ⬝ᵥ a) := by
  have h10 : n 1 0 = n 0 1 := hn.apply 0 1
  have h20 : n 2 0 = n 0 2 := hn.apply 0 2
  have h21 : n 2 1 = n 1 2 := hn.apply 1 2
  simp [scal, riem, koszul, Cna, eps3, kd, Fin.sum_univ_three, Matrix.trace, Matrix.mul_apply,
    dotProduct, h10, h20, h21]
  ring

theorem scal_Cna {n : Matrix (Fin 3) (Fin 3) ℝ} (hn : n.IsSymm) {a : Fin 3 → ℝ}
    (hna : n *ᵥ a = 0) :
    scal (Cna n a) = -trace (n * n) + (trace n) ^ 2 / 2 - 6 * (a ⬝ᵥ a) :=
  scal_Cna_of_symm hn a

theorem ricci_antisymm_01 {n : Matrix (Fin 3) (Fin 3) ℝ} (hn : n.IsSymm) (a : Fin 3 → ℝ) :
    ricci (Cna n a) 0 1 - ricci (Cna n a) 1 0 = 2 * (n *ᵥ a) 2 := by
  have h10 : n 1 0 = n 0 1 := hn.apply 0 1
  have h20 : n 2 0 = n 0 2 := hn.apply 0 2
  have h21 : n 2 1 = n 1 2 := hn.apply 1 2
  simp [ricci, riem, koszul, Cna, eps3, kd, Fin.sum_univ_three, Matrix.mulVec, dotProduct,
    h10, h20, h21]
  ring

theorem ricci_antisymm_02 {n : Matrix (Fin 3) (Fin 3) ℝ} (hn : n.IsSymm) (a : Fin 3 → ℝ) :
    ricci (Cna n a) 0 2 - ricci (Cna n a) 2 0 = -(2 * (n *ᵥ a) 1) := by
  have h10 : n 1 0 = n 0 1 := hn.apply 0 1
  have h20 : n 2 0 = n 0 2 := hn.apply 0 2
  have h21 : n 2 1 = n 1 2 := hn.apply 1 2
  simp [ricci, riem, koszul, Cna, eps3, kd, Fin.sum_univ_three, Matrix.mulVec, dotProduct,
    h10, h20, h21]
  ring

theorem ricci_antisymm_12 {n : Matrix (Fin 3) (Fin 3) ℝ} (hn : n.IsSymm) (a : Fin 3 → ℝ) :
    ricci (Cna n a) 1 2 - ricci (Cna n a) 2 1 = 2 * (n *ᵥ a) 0 := by
  have h10 : n 1 0 = n 0 1 := hn.apply 0 1
  have h20 : n 2 0 = n 0 2 := hn.apply 0 2
  have h21 : n 2 1 = n 1 2 := hn.apply 1 2
  simp [ricci, riem, koszul, Cna, eps3, kd, Fin.sum_univ_three, Matrix.mulVec, dotProduct,
    h10, h20, h21]
  ring

theorem ricci_antisymm_Cna {n : Matrix (Fin 3) (Fin 3) ℝ} (hn : n.IsSymm) (a : Fin 3 → ℝ)
    (p q : Fin 3) :
    ricci (Cna n a) p q - ricci (Cna n a) q p = 2 * ∑ r, eps3 p q r * (n *ᵥ a) r := by
  have r01 := ricci_antisymm_01 hn a
  have r02 := ricci_antisymm_02 hn a
  have r12 := ricci_antisymm_12 hn a
  fin_cases p <;> fin_cases q <;> simp [eps3, Fin.sum_univ_three] <;> linarith

theorem ricci_symm_iff_na_zero {n : Matrix (Fin 3) (Fin 3) ℝ} (hn : n.IsSymm) (a : Fin 3 → ℝ) :
    (∀ p q, ricci (Cna n a) p q = ricci (Cna n a) q p) ↔ n *ᵥ a = 0 := by
  constructor
  · intro h
    have key : ∀ p q, 2 * ∑ r, eps3 p q r * (n *ᵥ a) r = 0 := fun p q => by
      rw [← ricci_antisymm_Cna hn a p q, h p q, sub_self]
    have h0 := key 1 2
    have h1 := key 2 0
    have h2 := key 0 1
    simp [eps3, Fin.sum_univ_three] at h0 h1 h2
    funext r
    fin_cases r <;> simp [h0, h1, h2]
  · intro hna p q
    have h := ricci_antisymm_Cna hn a p q
    rw [hna] at h
    simp only [Pi.zero_apply, mul_zero, Finset.sum_const_zero] at h
    linarith

theorem scal_nonsymm_control :
    ¬ (!![0, 1, 0; 0, 0, 0; 0, 0, 0] : Matrix (Fin 3) (Fin 3) ℝ).IsSymm ∧
    (!![0, 1, 0; 0, 0, 0; 0, 0, 0] : Matrix (Fin 3) (Fin 3) ℝ) *ᵥ (0 : Fin 3 → ℝ) = 0 ∧
    scal (Cna !![0, 1, 0; 0, 0, 0; 0, 0, 0] 0) = -2 ∧
    -trace ((!![0, 1, 0; 0, 0, 0; 0, 0, 0] : Matrix (Fin 3) (Fin 3) ℝ) *
        !![0, 1, 0; 0, 0, 0; 0, 0, 0])
      + (trace (!![0, 1, 0; 0, 0, 0; 0, 0, 0] : Matrix (Fin 3) (Fin 3) ℝ)) ^ 2 / 2
      - 6 * ((0 : Fin 3 → ℝ) ⬝ᵥ 0) = 0 := by
  refine ⟨?_, ?_, ?_, ?_⟩
  · intro h
    have := h.apply 0 1
    simp at this
  · simp
  · simp [scal, riem, koszul, Cna, eps3, kd, Fin.sum_univ_three]
    norm_num
  · simp [Matrix.trace, Matrix.mul_apply, Fin.sum_univ_three]

theorem scal_scaling {n : Matrix (Fin 3) (Fin 3) ℝ} (hn : n.IsSymm) (a : Fin 3 → ℝ) (s : ℝ) :
    scal (Cna (s • n) (s • a)) = s ^ 2 * scal (Cna n a) := by
  rw [scal_Cna_of_symm (hn.smul s), scal_Cna_of_symm hn]
  simp [Matrix.trace, Matrix.mul_apply, dotProduct, Fin.sum_univ_three]
  ring

/-! ## T6-T9: invariant tensor in its eigenframe -/

theorem DT_diagonal {d : ℕ} {Γ : Fin d → Fin d → Fin d → ℝ} (hm : MetricCompatible Γ)
    (lam : Fin d → ℝ) (k i j : Fin d) :
    DT Γ (diagonal lam) k i j = (lam i - lam j) * Γ j k i := by
  simp only [DT, Matrix.diagonal_apply, mul_ite, mul_zero, Finset.sum_ite_eq',
    Finset.sum_ite_eq, Finset.mem_univ, if_true]
  rw [hm i k j]
  ring

theorem DT_diagonal_Cna (n : Matrix (Fin 3) (Fin 3) ℝ) (a : Fin 3 → ℝ) (lam : Fin 3 → ℝ)
    (k i j : Fin 3) :
    DT (koszul (Cna n a)) (diagonal lam) k i j = (lam i - lam j) * koszul (Cna n a) j k i :=
  DT_diagonal (koszul_metricCompatible (Cna_antisymm n a)) lam k i j

theorem gamma_eq_DT_div {d : ℕ} {Γ : Fin d → Fin d → Fin d → ℝ} (hm : MetricCompatible Γ)
    (lam : Fin d → ℝ) {k i j : Fin d} (hij : i ≠ j) (hgap : lam i ≠ lam j) :
    Γ j k i = DT Γ (diagonal lam) k i j / (lam i - lam j) :=
  PORTCAS05EigenframeGap.recover_coefficient (lam i) (lam j) (Γ j k i)
    (DT Γ (diagonal lam) k i j) hgap (DT_diagonal hm lam k i j)

theorem DT_collision {d : ℕ} {Γ : Fin d → Fin d → Fin d → ℝ} (hm : MetricCompatible Γ)
    (lam : Fin d → ℝ) {k i j : Fin d} (heq : lam i = lam j) :
    DT Γ (diagonal lam) k i j = 0 := by
  rw [DT_diagonal hm, heq, sub_self, zero_mul]

theorem gap_nonvacuous :
    koszul (Cna 1 0) 2 0 1
        = DT (koszul (Cna 1 0)) (diagonal (![0, 1, 2] : Fin 3 → ℝ)) 0 1 2
          / ((![0, 1, 2] : Fin 3 → ℝ) 1 - (![0, 1, 2] : Fin 3 → ℝ) 2) ∧
    koszul (Cna 1 0) 2 0 1 = 1 / 2 ∧
    (![0, 1, 2] : Fin 3 → ℝ) 1 ≠ (![0, 1, 2] : Fin 3 → ℝ) 2 := by
  have hl1 : (![0, 1, 2] : Fin 3 → ℝ) 1 = 1 := rfl
  have hl2 : (![0, 1, 2] : Fin 3 → ℝ) 2 = 2 := rfl
  refine ⟨?_, ?_, ?_⟩
  · exact gamma_eq_DT_div (koszul_metricCompatible (Cna_antisymm 1 0)) _ (by decide)
      (by rw [hl1, hl2]; norm_num)
  · simp [koszul, Cna, eps3, kd, Matrix.one_apply]
  · rw [hl1, hl2]; norm_num

theorem collision_witness :
    (∀ k i j, DT (koszul (Cna 0 0)) (diagonal fun _ => (1 : ℝ)) k i j
        = DT (koszul (Cna 1 0)) (diagonal fun _ => (1 : ℝ)) k i j) ∧
    koszul (Cna 0 0) 2 0 1 = 0 ∧ koszul (Cna 1 0) 2 0 1 = 1 / 2 := by
  refine ⟨?_, ?_, ?_⟩
  · intro k i j
    rw [DT_collision (koszul_metricCompatible (Cna_antisymm 0 0)) (fun _ => (1 : ℝ))
        (k := k) (i := i) (j := j) rfl,
      DT_collision (koszul_metricCompatible (Cna_antisymm 1 0)) (fun _ => (1 : ℝ))
        (k := k) (i := i) (j := j) rfl]
  · simp [koszul, Cna, eps3, kd]
  · simp [koszul, Cna, eps3, kd, Matrix.one_apply]

theorem reconGamma_eq {d : ℕ} {C : Fin d → Fin d → Fin d → ℝ} (hC : Antisymm C)
    {lam : Fin d → ℝ} (hlam : Function.Injective lam) (j k i : Fin d) :
    reconGamma (DT (koszul C) (diagonal lam)) lam j k i = koszul C j k i := by
  have hm := koszul_metricCompatible hC
  unfold reconGamma
  by_cases hij : i = j
  · subst hij
    rw [if_pos rfl]
    have := hm i k i
    linarith
  · rw [if_neg hij]
    exact (gamma_eq_DT_div hm lam hij (fun h => hij (hlam h))).symm

theorem structure_from_DT {d : ℕ} {C : Fin d → Fin d → Fin d → ℝ} (hC : Antisymm C)
    {lam : Fin d → ℝ} (hlam : Function.Injective lam) (j k i : Fin d) :
    C j k i = reconC (DT (koszul C) (diagonal lam)) lam j k i := by
  unfold reconC
  rw [reconGamma_eq hC hlam, reconGamma_eq hC hlam]
  exact (koszul_torsionFree hC j k i).symm

theorem structure_unique_simple {d : ℕ} {C C' : Fin d → Fin d → Fin d → ℝ}
    (hC : Antisymm C) (hC' : Antisymm C') {lam : Fin d → ℝ} (hlam : Function.Injective lam)
    (hD : DT (koszul C) (diagonal lam) = DT (koszul C') (diagonal lam)) : C = C' := by
  funext j k i
  rw [structure_from_DT hC hlam, structure_from_DT hC' hlam, hD]

theorem abelian_of_DT_zero {d : ℕ} {C : Fin d → Fin d → Fin d → ℝ} (hC : Antisymm C)
    {lam : Fin d → ℝ} (hlam : Function.Injective lam)
    (hD : ∀ k i j, DT (koszul C) (diagonal lam) k i j = 0) : C = fun _ _ _ => 0 := by
  have hz : DT (koszul C) (diagonal lam) = fun _ _ _ => 0 := by
    funext k i j
    exact hD k i j
  funext j k i
  rw [structure_from_DT hC hlam, hz]
  simp [reconC, reconGamma]

/-! ## T10: one R3 value does not fix a class -/

theorem same_R3_I_VII0 :
    Cna 0 0 = (fun _ _ _ => 0) ∧
    Cna (diagonal (![1, 1, 0] : Fin 3 → ℝ)) 0 0 1 2 ≠ 0 ∧
    (diagonal (![1, 1, 0] : Fin 3 → ℝ)) *ᵥ (0 : Fin 3 → ℝ) = 0 ∧
    scal (Cna 0 0) = 0 ∧
    scal (Cna (diagonal (![1, 1, 0] : Fin 3 → ℝ)) 0) = 0 := by
  refine ⟨?_, ?_, ?_, ?_, ?_⟩
  · funext k i j
    simp [Cna]
  · simp [Cna, eps3, Fin.sum_univ_three]
  · simp
  · rw [scal_Cna_of_symm isSymm_zero]
    simp
  · rw [scal_Cna_of_symm (isSymm_diagonal _)]
    simp [Matrix.trace, Fin.sum_univ_three]
    norm_num

theorem same_R3_IX_V :
    scal (Cna (diagonal (![1, 1, 6] : Fin 3 → ℝ)) 0) = -6 ∧
    scal (Cna 0 (![1, 0, 0] : Fin 3 → ℝ)) = -6 ∧
    traceForm (Cna (diagonal (![1, 1, 6] : Fin 3 → ℝ)) 0) = (fun _ => 0) ∧
    traceForm (Cna 0 (![1, 0, 0] : Fin 3 → ℝ)) 0 = 2 ∧
    (0 : Matrix (Fin 3) (Fin 3) ℝ) *ᵥ (![1, 0, 0] : Fin 3 → ℝ) = 0 := by
  refine ⟨?_, ?_, ?_, ?_, ?_⟩
  · rw [scal_Cna_of_symm (isSymm_diagonal _)]
    simp [Matrix.trace, Fin.sum_univ_three]
    norm_num
  · rw [scal_Cna_of_symm isSymm_zero]
    simp [dotProduct, Fin.sum_univ_three]
  · funext i
    fin_cases i <;> simp [traceForm, Cna, eps3, kd, Fin.sum_univ_three, Matrix.diagonal_apply]
  · simp [traceForm, Cna, eps3, kd, Fin.sum_univ_three]
    norm_num
  · simp

theorem IX_R3_both_signs :
    scal (Cna 1 0) = 3 / 2 ∧
    scal (Cna (diagonal (![1, 1, 5] : Fin 3 → ℝ)) 0) = -5 / 2 := by
  refine ⟨?_, ?_⟩
  · rw [scal_Cna_of_symm isSymm_one]
    simp [Matrix.trace, Fin.sum_univ_three]
    norm_num
  · rw [scal_Cna_of_symm (isSymm_diagonal _)]
    simp [Matrix.trace, Fin.sum_univ_three]
    norm_num

end PORTCAS05OrbitCurvature
