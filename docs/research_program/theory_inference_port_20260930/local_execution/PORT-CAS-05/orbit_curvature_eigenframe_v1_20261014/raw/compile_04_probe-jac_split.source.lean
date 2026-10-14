import Mathlib

/-!
# P05-A: spatial orbit curvature and invariant-eigenframe connection (Lie-algebra model)

Finite-dimensional, orthonormal constant-frame model. Index conventions follow
`htt/src/common/relativistic_kinematics.py` (`C[k,i,j]`, `Gamma[k,i,j]`, `derivative[k,i,j]`)
and `wolfram_curvature.wl` lines 3-6. No manifold, homogeneity neighborhood, spacetime action
or rest-bundle slice is modelled here.
-/

open Matrix

noncomputable section

namespace PORTCAS05OrbitCurvature

namespace Probe

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


theorem jac_01 {n : Matrix (Fin 3) (Fin 3) ℝ} (hn : n.IsSymm) (a : Fin 3 → ℝ) (i l : Fin 3) :
    jacobiResidual (Cna n a) i 0 1 l = -2 * eps3 0 1 l * (n *ᵥ a) i := by
  have h10 : n 1 0 = n 0 1 := hn.apply 0 1
  have h20 : n 2 0 = n 0 2 := hn.apply 0 2
  have h21 : n 2 1 = n 1 2 := hn.apply 1 2
  fin_cases i <;> fin_cases l <;>
    simp [jacobiResidual, Cna, eps3, kd, Fin.sum_univ_three, Matrix.mulVec, dotProduct,
      h10, h20, h21] <;> ring

end Probe
end PORTCAS05OrbitCurvature
