# P05-A frozen targets (written before any proof compile)

Module: `lean/OrbitCurvatureEigenframe.lean`, namespace `PORTCAS05OrbitCurvature`.
Imports: `Mathlib` and the reviewed `EigenframeGap` (unchanged, sha256
`de20d2e4a76d526602a8b3696b883dd94b655d70bbc18902b6d8966433b16268`).
Toolchain: Lean 4.31.0, mathlib `fabf563a7c95a166b8d7b6efca11c8b4dc9d911f`.

## Scope of the model (read before the signatures)

Everything is a finite-dimensional Lie-algebra / orthonormal-frame-component statement. The frame
`e_1,e_2,e_3` is identified with the index set `Fin 3` (Fin d for the dimension-free lemmas). The
following readings are definitions of the model, not theorems:

* left-invariant orthonormal frame ⇒ constant structure constants and constant metric `δ_ij`;
  the Koszul formula then has no derivative terms;
* an invariant tensor `T` has frame-constant components, so `e_k(T_ij) = 0` is omitted from `DT`.

No manifold, no homogeneity neighborhood, no spacetime action, no rest-bundle slice is modelled.
"Spacelike simply transitive orbit" is the interpretation of the model and is not proved.

## Definitions (index conventions identical to `htt/src/common/relativistic_kinematics.py`)

```lean
def eps3 : Fin 3 → Fin 3 → Fin 3 → ℝ :=
  ![![![0, 0, 0], ![0, 0, 1], ![0, -1, 0]],
    ![![0, 0, -1], ![0, 0, 0], ![1, 0, 0]],
    ![![0, 1, 0], ![-1, 0, 0], ![0, 0, 0]]]
def kd {d : ℕ} (i j : Fin d) : ℝ := if i = j then 1 else 0
/-- C^k_{ij} = eps_{ijl} n^{lk} + a_i δ^k_j − a_j δ^k_i, [e_i,e_j] = Σ_k C k i j • e_k -/
def Cna (n : Matrix (Fin 3) (Fin 3) ℝ) (a : Fin 3 → ℝ) (k i j : Fin 3) : ℝ :=
  (∑ l, eps3 i j l * n l k) + a i * kd k j - a j * kd k i
def bracket {d} (C : Fin d → Fin d → Fin d → ℝ) (x y : Fin d → ℝ) : Fin d → ℝ :=
  fun k => ∑ i, ∑ j, C k i j * x i * y j
def jacobiResidual {d} (C) (i j k l : Fin d) : ℝ :=
  ∑ m, (C m j k * C i l m + C m k l * C i j m + C m l j * C i k m)
def Antisymm {d} (C) : Prop := ∀ k i j : Fin d, C k i j = -C k j i
/-- Γ^k_{ij} = ⟨∇_{e_i} e_j, e_k⟩ (Koszul, orthonormal constant frame) -/
def koszul {d} (C) (k i j : Fin d) : ℝ := (C k i j - C i j k + C j k i) / 2
def MetricCompatible {d} (Γ) : Prop := ∀ k i j : Fin d, Γ k i j = -Γ j i k
def TorsionFree {d} (Γ C) : Prop := ∀ k i j : Fin d, Γ k i j - Γ k j i = C k i j
/-- riem C i l j k = ⟨R(e_j,e_k) e_l, e_i⟩ (wolfram_curvature.wl line 5) -/
def riem {d} (C) (i l j k : Fin d) : ℝ :=
  ∑ m, (koszul C m k l * koszul C i j m - koszul C m j l * koszul C i k m
        - C m j k * koszul C i m l)
def ricci {d} (C) (l k : Fin d) : ℝ := ∑ i, riem C i l i k
def scal {d} (C) : ℝ := ∑ i, ∑ j, riem C i j i j
/-- (D_k T)_{ij} for frame-constant T -/
def DT {d} (Γ) (T : Matrix (Fin d) (Fin d) ℝ) (k i j : Fin d) : ℝ :=
  -(∑ m, Γ m k i * T m j) - (∑ m, Γ m k j * T i m)
def traceForm {d} (C) (i : Fin d) : ℝ := ∑ k, C k i k
def reconGamma {d} (D) (lam : Fin d → ℝ) (j k i : Fin d) : ℝ :=
  if i = j then 0 else D k i j / (lam i - lam j)
def reconC {d} (D) (lam) (j k i : Fin d) : ℝ := reconGamma D lam j k i - reconGamma D lam j i k
```

## Targets

| id | Lean name | statement | card link |
|---|---|---|---|
| T1a | `koszul_metricCompatible` | `{d} {C} (hC : Antisymm C) : MetricCompatible (koszul C)` | lean_steps[1] Koszul |
| T1b | `koszul_torsionFree` | `{d} {C} (hC : Antisymm C) : TorsionFree (koszul C) C` | lean_steps[1] |
| T1c | `koszul_unique` | `{d} {C Γ} (hm : MetricCompatible Γ) (ht : TorsionFree Γ C) : Γ = koszul C` | derivation of Koszul (not postulated) |
| T2 | `Cna_antisymm` | `(n a) : Antisymm (Cna n a)` | lean_steps[0] |
| T3a | `jacobiResidual_Cna` | `{n} (hn : n.IsSymm) (a) (i j k l) : jacobiResidual (Cna n a) i j k l = -2 * eps3 j k l * (n *ᵥ a) i` | acceptance[0]: where n a = 0 enters |
| T3b | `jacobi_iff_na_zero` | `{n} (hn : n.IsSymm) (a) : (∀ i j k l, jacobiResidual (Cna n a) i j k l = 0) ↔ n *ᵥ a = 0` | acceptance[0] |
| T3c | `bracket_antisymm` | `{d} {C} (hC : Antisymm C) (x y) : bracket C x y = -bracket C y x` | Lie algebra |
| T3d | `bracket_jacobi` | `{n} (hn : n.IsSymm) {a} (hna : n *ᵥ a = 0) (x y z) : bracket (Cna n a) x (bracket (Cna n a) y z) + bracket (Cna n a) y (bracket (Cna n a) z x) + bracket (Cna n a) z (bracket (Cna n a) x y) = 0` | Lie algebra |
| T4 | `scal_Cna` | `{n} (hn : n.IsSymm) {a} (hna : n *ᵥ a = 0) : scal (Cna n a) = -trace (n * n) + (trace n) ^ 2 / 2 - 6 * (a ⬝ᵥ a)` | CAS-05 identity, card quantifiers |
| T4' | `scal_Cna_of_symm` | `{n} (hn : n.IsSymm) (a) : scal (Cna n a) = -trace (n * n) + (trace n) ^ 2 / 2 - 6 * (a ⬝ᵥ a)` | records that n a = 0 is NOT used in the scalar contraction (explicitly weaker hypothesis, same conclusion) |
| T4b | `ricci_antisymm_Cna` | `{n} (hn : n.IsSymm) (a) (p q) : ricci (Cna n a) p q - ricci (Cna n a) q p = 2 * ∑ r, eps3 p q r * (n *ᵥ a) r` | acceptance[0] |
| T4c | `ricci_symm_iff_na_zero` | `{n} (hn : n.IsSymm) (a) : (∀ p q, ricci (Cna n a) p q = ricci (Cna n a) q p) ↔ n *ᵥ a = 0` | acceptance[0] |
| T4n | `scal_nonsymm_control` | for `n0 = !![0,1,0;0,0,0;0,0,0]`, `a = 0`: `¬ n0.IsSymm ∧ n0 *ᵥ 0 = 0 ∧ scal (Cna n0 0) = -2 ∧ -trace (n0*n0) + (trace n0)^2/2 - 6*((0:Fin 3→ℝ) ⬝ᵥ 0) = 0` | negative control: symmetry is load-bearing |
| T5 | `scal_scaling` | `{n} (hn : n.IsSymm) (a) (s : ℝ) : scal (Cna (s • n) (s • a)) = s ^ 2 * scal (Cna n a)` | units: n,a ~ 1/length ⇒ R3 ~ 1/length² |
| T6 | `DT_diagonal` | `{d} {Γ} (hm : MetricCompatible Γ) (lam : Fin d → ℝ) (k i j) : DT Γ (diagonal lam) k i j = (lam i - lam j) * Γ j k i` | lean_steps[2] |
| T6' | `DT_diagonal_Cna` | `(n a) (lam : Fin 3 → ℝ) (k i j) : DT (koszul (Cna n a)) (diagonal lam) k i j = (lam i - lam j) * koszul (Cna n a) j k i` | lean_steps[2] on the orbit algebra |
| T7 | `gamma_eq_DT_div` | `{d} {Γ} (hm : MetricCompatible Γ) (lam) {k i j} (hij : i ≠ j) (hgap : lam i ≠ lam j) : Γ j k i = DT Γ (diagonal lam) k i j / (lam i - lam j)` | lean_steps[3], CAS-05 second identity |
| T7w | `gap_nonvacuous` | with `lam = ![0,1,2]`: `koszul (Cna 1 0) 2 0 1 = DT (koszul (Cna 1 0)) (diagonal lam) 0 1 2 / (lam 1 - lam 2) ∧ koszul (Cna 1 0) 2 0 1 = 1/2 ∧ lam 1 ≠ lam 2` | non-vacuity witness |
| T8 | `DT_collision` | `{d} {Γ} (hm : MetricCompatible Γ) (lam) {k i j} (heq : lam i = lam j) : DT Γ (diagonal lam) k i j = 0` | acceptance[1] collision branch |
| T8w | `collision_witness` | `(∀ k i j, DT (koszul (Cna 0 0)) (diagonal fun _ => 1) k i j = DT (koszul (Cna 1 0)) (diagonal fun _ => 1) k i j) ∧ koszul (Cna 0 0) 2 0 1 = 0 ∧ koszul (Cna 1 0) 2 0 1 = 1/2` | negative control: inverse formula inapplicable (types I and IX, same T = identity, same DT, different Γ) |
| T9a | `structure_from_DT` | `{d} {C} (hC : Antisymm C) {lam} (hlam : Function.Injective lam) (j k i) : C j k i = reconC (DT (koszul C) (diagonal lam)) lam j k i` | BIC-03b reconstruction, Python lines 380-386 |
| T9b | `structure_unique_simple` | `{d} {C C'} (hC : Antisymm C) (hC' : Antisymm C') {lam} (hlam : Function.Injective lam) (hD : DT (koszul C) (diagonal lam) = DT (koszul C') (diagonal lam)) : C = C'` | simple spectrum ⇒ unique |
| T9c | `abelian_of_DT_zero` | `{d} {C} (hC : Antisymm C) {lam} (hlam : Function.Injective lam) (hD : ∀ k i j, DT (koszul C) (diagonal lam) k i j = 0) : C = fun _ _ _ => 0` | BIC-03b corollary |
| T10a | `same_R3_I_VII0` | `Cna 0 0 = (fun _ _ _ => 0) ∧ Cna (diagonal ![1,1,0]) 0 0 1 2 ≠ 0 ∧ (diagonal ![1,1,0]) *ᵥ (0:Fin 3→ℝ) = 0 ∧ scal (Cna 0 0) = 0 ∧ scal (Cna (diagonal ![1,1,0]) 0) = 0` | pitfall control: one R3 value, two classes (abelian vs non-abelian) |
| T10b | `same_R3_IX_V` | `scal (Cna (diagonal ![1,1,6]) 0) = -6 ∧ scal (Cna 0 ![1,0,0]) = -6 ∧ traceForm (Cna (diagonal ![1,1,6]) 0) = (fun _ => 0) ∧ traceForm (Cna 0 ![1,0,0]) 0 = 2 ∧ (0 : Matrix (Fin 3) (Fin 3) ℝ) *ᵥ ![1,0,0] = 0` | pitfall control: unimodular IX vs class-B V share R3 |
| T10c | `IX_R3_both_signs` | `scal (Cna 1 0) = 3/2 ∧ scal (Cna (diagonal ![1,1,5]) 0) = -5/2` | matches Wolfram evidence; IX does not force R3 > 0 |

Branch faithfulness: T7 keeps both `i ≠ j` and `lam i ≠ lam j` exactly as the card states
(`i ≠ j` is implied by the gap; it is kept, not strengthened). T8 is the explicit branch where the
inverse formula does not apply. T4 is stated with the card's hypotheses; T4' is an additional,
separately named lemma with fewer hypotheses.

Allowed axioms: `propext`, `Classical.choice`, `Quot.sound`. Forbidden: `sorry`, `admit`,
`native_decide`, new axioms.

Not targeted: R3 > 0 ⇒ IX (BIC-02 implication), Lie-isomorphism invariance of the label witnesses,
manifold Levi-Civita, homogeneity neighborhood, identification with rotating rest-bundle slices,
sky-morphology correspondence, numerical stability near collisions, scientific admission.
