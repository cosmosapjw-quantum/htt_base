# L2-W1-B frozen targets (written before any proof compile)

Module: `lean/L2W1FibreImage.lean`, namespace `L2W1FibreImage`.
Imports (unchanged, reviewed): `L2W1KernelBound` (L2-W1-A), `P08EllipsoidImage` (P08-B, which
imports `P08EllipsoidFiber` (P08-A), `G08AWhitening`, `ProjectionBridge`).
Toolchain: Lean 4.31.0, Mathlib fabf563a7c95a166b8d7b6efca11c8b4dc9d911f.

## Scope mapping to the card

| Card lean_step | Targets |
|---|---|
| 1. fibre `F ∩ B⁻¹{y}` and image `P(F ∩ B⁻¹{y})` for general admissible `F` | `Fibre`, `FibreImage` (arbitrary `F : Set E`, arbitrary maps), G1–G6 |
| 2. affine-unbounded branch reduces to L2-W1-A | A1–A4 (`AffineDomain x0 V = {x | x - x0 ∈ V}`), L1, L2 |
| 3a. ellipsoid branch → P08-B exact image | E1 (definitional identity), E2–E5 (P08-B theorems transported), E6 |
| 3b. rational bounded polytope → existing support certificate | R1 (augmented rows of `rational_polytope_fiber_support`), R2 (`direction = Pᵀu`), R3–R5 (dual-certificate soundness), R6 (box ⇒ bounded), R7a–c (exact instance, equals adapter output `[0, 3/2]`) |
| 4. curved general `F`: only the source-defined image theorem + exact counterexample to the universal linear iff | general G1–G6, L2–L4 only; counterexample C1–C5 (bounded parabola arc), separation C6–C7 (unbounded parabola) |

Acceptance mapping:
- finite-domain bound vs global coercivity: distinct definitions `FiniteDomainBound (F : Set E)`
  (fibre-diameter bound on the supplied set), `DomainCoercivity (F : Set E)` and
  `GlobalCoercivity (V : Submodule ℝ E)`; `bounded_branch_separation` proves the first holds
  where the third fails.
- no general nonlinear solver obligation: none is stated; the curved branch states only the
  source-defined image theorem and counterexamples.
- pitfall: no theorem gives support or computability for curved sets beyond the ellipsoid.

Quantifiers/domains follow the sources: `E` finite-dimensional real normed (as in L2-W1-A),
`Y`, `Z` real normed; ellipsoid and polytope over `Fin n → ℝ` with exact (Euclidean dot) algebra
as in P08-B; polytope coefficients real (rational numerals in the instance, checked exactly).
The affine bounded/subsingleton statements A3/A4 are stated for an observed value `B x1` with
`x1` in the affine domain (nonempty fibre), which is the only case where the statement is
non-vacuous (empty fibres are bounded and subsingleton trivially).

Non-vacuity / negative controls: `bounded_branch_separation`, `curved_kernelInclusion_fails`,
`curved_arc_domainCoercivity`, `curved_arc_fibreImage`, `parabola_identified`,
`parabola_not_domainCoercivity`, instance R7a–c (nonempty polytope fibre with a strict interval).

Not targeted: correctness of vertex enumeration in `joint_feasible_set.exact_support` for all
inputs; a numerical (floating) link for the ellipsoid; any general nonlinear feasible-set solver;
scientific admission.

## Exact frozen signatures

```lean
def Fibre (F : Set E) (B : E → Y) (y : Y) : Set E := …

def FibreImage (F : Set E) (B : E → Y) (P : E → Z) (y : Y) : Set Z := …

theorem mem_fibreImage (F : Set E) (B : E → Y) (P : E → Z) (y : Y) (z : Z) :
    z ∈ FibreImage F B P y ↔ ∃ x ∈ F, B x = y ∧ P x = z := …

theorem fibreImage_subset_image (F : Set E) (B : E → Y) (P : E → Z) (y : Y) :
    FibreImage F B P y ⊆ P '' F := …

theorem iUnion_fibreImage (F : Set E) (B : E → Y) (P : E → Z) :
    ⋃ y, FibreImage F B P y = P '' F := …

theorem fibreImage_mono {F F' : Set E} (h : F ⊆ F') (B : E → Y) (P : E → Z) (y : Y) :
    FibreImage F B P y ⊆ FibreImage F' B P y := …

theorem fibreImage_nonempty_iff (F : Set E) (B : E → Y) (P : E → Z) (y : Y) :
    (FibreImage F B P y).Nonempty ↔ y ∈ B '' F := …

theorem fibreImage_subsingleton_iff (F : Set E) (B : E → Y) (P : E → Z) :
    (∀ y, (FibreImage F B P y).Subsingleton) ↔
      ∀ x ∈ F, ∀ x' ∈ F, B x = B x' → P x = P x' := …

def FiniteDomainBound [SeminormedAddCommGroup Z] (F : Set E) (B : E → Y) (P : E → Z) : Prop := …

def DomainCoercivity [SeminormedAddCommGroup Y] [SeminormedAddCommGroup Z]
    (F : Set E) (B : E → Y) (P : E → Z) : Prop := …

def GlobalCoercivity [AddCommGroup E] [Module ℝ E] [SeminormedAddCommGroup Y] [Module ℝ Y]
    [SeminormedAddCommGroup Z] [Module ℝ Z]
    (V : Submodule ℝ E) (B : E →ₗ[ℝ] Y) (P : E →ₗ[ℝ] Z) : Prop := …

def KernelInclusion [AddCommGroup E] [Module ℝ E] [AddCommGroup Y] [Module ℝ Y]
    [AddCommGroup Z] [Module ℝ Z]
    (V : Submodule ℝ E) (B : E →ₗ[ℝ] Y) (P : E →ₗ[ℝ] Z) : Prop := …

theorem finiteDomainBound_of_isBounded_image [SeminormedAddCommGroup Z]
    (F : Set E) (B : E → Y) (P : E → Z) (h : Bornology.IsBounded (P '' F)) :
    FiniteDomainBound F B P := …

theorem domainCoercivity_subsingleton [SeminormedAddCommGroup Y] [NormedAddCommGroup Z]
    (F : Set E) (B : E → Y) (P : E → Z) (h : DomainCoercivity F B P) (y : Y) :
    (FibreImage F B P y).Subsingleton := …

theorem globalCoercivity_iff (V : Submodule ℝ E) (B : E →ₗ[ℝ] Y) (P : E →ₗ[ℝ] Z) :
    GlobalCoercivity V B P ↔ KernelInclusion V B P := …

theorem kernelInclusion_domainCoercivity (B : E →ₗ[ℝ] Y) (P : E →ₗ[ℝ] Z)
    (h : KernelInclusion ⊤ B P) (F : Set E) : DomainCoercivity F B P := …

theorem isBounded_fibreImage (F : Set E) (hF : Bornology.IsBounded F) (B : E → Y)
    (P : E →ₗ[ℝ] Z) (y : Y) : Bornology.IsBounded (FibreImage F B P y) := …

theorem isBounded_finiteDomainBound (F : Set E) (hF : Bornology.IsBounded F) (B : E → Y)
    (P : E →ₗ[ℝ] Z) : FiniteDomainBound F B P := …

def AffineDomain (x0 : E) (V : Submodule ℝ E) : Set E := …

theorem affine_domainCoercivity_iff_global (V : Submodule ℝ E) (B : E →ₗ[ℝ] Y)
    (P : E →ₗ[ℝ] Z) (x0 : E) :
    DomainCoercivity (AffineDomain x0 V) B P ↔ GlobalCoercivity V B P := …

theorem affine_branch_iff (V : Submodule ℝ E) (B : E →ₗ[ℝ] Y) (P : E →ₗ[ℝ] Z) (x0 : E) :
    DomainCoercivity (AffineDomain x0 V) B P ↔ KernelInclusion V B P := …

theorem affine_fibreImage_subset_singleton (V : Submodule ℝ E) (B : E →ₗ[ℝ] Y)
    (P : E →ₗ[ℝ] Z) (x0 x1 : E) (hx1 : x1 - x0 ∈ V) (hker : KernelInclusion V B P) :
    FibreImage (AffineDomain x0 V) B P (B x1) ⊆ {P x1} := …

theorem affine_fibreImage_isBounded_iff (V : Submodule ℝ E) (B : E →ₗ[ℝ] Y)
    (P : E →ₗ[ℝ] Z) (x0 x1 : E) (hx1 : x1 - x0 ∈ V) :
    Bornology.IsBounded (FibreImage (AffineDomain x0 V) B P (B x1)) ↔
      KernelInclusion V B P := …

theorem affine_fibreImage_subsingleton_iff (V : Submodule ℝ E) (B : E →ₗ[ℝ] Y)
    (P : E →ₗ[ℝ] Z) (x0 x1 : E) (hx1 : x1 - x0 ∈ V) :
    (FibreImage (AffineDomain x0 V) B P (B x1)).Subsingleton ↔ KernelInclusion V B P := …

theorem bounded_branch_separation :
    FiniteDomainBound (Icc (-1 : ℝ) 1) (0 : ℝ →ₗ[ℝ] ℝ) (LinearMap.id : ℝ →ₗ[ℝ] ℝ) ∧
      ¬ GlobalCoercivity (⊤ : Submodule ℝ ℝ) (0 : ℝ →ₗ[ℝ] ℝ) (LinearMap.id : ℝ →ₗ[ℝ] ℝ) ∧
      ¬ KernelInclusion (⊤ : Submodule ℝ ℝ) (0 : ℝ →ₗ[ℝ] ℝ) (LinearMap.id : ℝ →ₗ[ℝ] ℝ) := …

theorem ellipsoid_fibreImage_eq_P08 (c : Fin n → ℝ) (L : Matrix (Fin n) (Fin r) ℝ)
    (B : Matrix (Fin m) (Fin n) ℝ) (P : Matrix (Fin q) (Fin n) ℝ) (y : Fin m → ℝ) :
    FibreImage (P08EllipsoidImage.Ell c L) (fun x => B *ᵥ x) (fun x => P *ᵥ x) y =
      P08EllipsoidImage.FibreImage c L B P y := …

theorem ellipsoid_branch (c : Fin n → ℝ) (L : Matrix (Fin n) (Fin r) ℝ)
    (B : Matrix (Fin m) (Fin n) ℝ) (P : Matrix (Fin q) (Fin n) ℝ) (y : Fin m → ℝ)
    (X : Matrix (Fin r) (Fin m) ℝ) (N : Matrix (Fin r) (Fin d) ℝ)
    (hX : G08AWhitening.IsMoorePenrose (B * L) X)
    (hcomp : ∃ z, (B * L) *ᵥ z = y - B *ᵥ c) (hN : P08EllipsoidImage.IsKerONB (B * L) N)
    (hη : (X *ᵥ (y - B *ᵥ c)) ⬝ᵥ (X *ᵥ (y - B *ᵥ c)) ≤ 1) :
    FibreImage (P08EllipsoidImage.Ell c L) (fun x => B *ᵥ x) (fun x => P *ᵥ x) y =
      P08EllipsoidImage.EllImage (P *ᵥ (c + L *ᵥ (X *ᵥ (y - B *ᵥ c))))
        (Real.sqrt (1 - (X *ᵥ (y - B *ᵥ c)) ⬝ᵥ (X *ᵥ (y - B *ᵥ c)))) (P * L * N) := …

theorem ellipsoid_branch_boundary (c : Fin n → ℝ) (L : Matrix (Fin n) (Fin r) ℝ)
    (B : Matrix (Fin m) (Fin n) ℝ) (P : Matrix (Fin q) (Fin n) ℝ) (y : Fin m → ℝ)
    (X : Matrix (Fin r) (Fin m) ℝ) (hX : G08AWhitening.IsMoorePenrose (B * L) X) :
    ((∃ z, (B * L) *ᵥ z = y - B *ᵥ c) →
        (X *ᵥ (y - B *ᵥ c)) ⬝ᵥ (X *ᵥ (y - B *ᵥ c)) = 1 →
        FibreImage (P08EllipsoidImage.Ell c L) (fun x => B *ᵥ x) (fun x => P *ᵥ x) y =
          {P *ᵥ (c + L *ᵥ (X *ᵥ (y - B *ᵥ c)))}) ∧
      ((∃ z, (B * L) *ᵥ z = y - B *ᵥ c) →
        1 < (X *ᵥ (y - B *ᵥ c)) ⬝ᵥ (X *ᵥ (y - B *ᵥ c)) →
        FibreImage (P08EllipsoidImage.Ell c L) (fun x => B *ᵥ x) (fun x => P *ᵥ x) y = ∅) ∧
      ((¬ ∃ z, (B * L) *ᵥ z = y - B *ᵥ c) →
        FibreImage (P08EllipsoidImage.Ell c L) (fun x => B *ᵥ x) (fun x => P *ᵥ x) y = ∅) := …

theorem ellipsoid_branch_nonempty_iff (c : Fin n → ℝ) (L : Matrix (Fin n) (Fin r) ℝ)
    (B : Matrix (Fin m) (Fin n) ℝ) (P : Matrix (Fin q) (Fin n) ℝ) (y : Fin m → ℝ)
    (X : Matrix (Fin r) (Fin m) ℝ) (hX : G08AWhitening.IsMoorePenrose (B * L) X) :
    (FibreImage (P08EllipsoidImage.Ell c L) (fun x => B *ᵥ x) (fun x => P *ᵥ x) y).Nonempty ↔
      (∃ z, (B * L) *ᵥ z = y - B *ᵥ c) ∧
        (X *ᵥ (y - B *ᵥ c)) ⬝ᵥ (X *ᵥ (y - B *ᵥ c)) ≤ 1 := …

theorem ellipsoid_branch_support (c : Fin n → ℝ) (L : Matrix (Fin n) (Fin r) ℝ)
    (B : Matrix (Fin m) (Fin n) ℝ) (P : Matrix (Fin q) (Fin n) ℝ) (y : Fin m → ℝ)
    (X : Matrix (Fin r) (Fin m) ℝ) (N : Matrix (Fin r) (Fin d) ℝ)
    (hX : G08AWhitening.IsMoorePenrose (B * L) X)
    (hcomp : ∃ z, (B * L) *ᵥ z = y - B *ᵥ c) (hN : P08EllipsoidImage.IsKerONB (B * L) N)
    (hη : (X *ᵥ (y - B *ᵥ c)) ⬝ᵥ (X *ᵥ (y - B *ᵥ c)) ≤ 1) (w : Fin q → ℝ) :
    IsGreatest ((fun θ => w ⬝ᵥ θ) ''
        FibreImage (P08EllipsoidImage.Ell c L) (fun x => B *ᵥ x) (fun x => P *ᵥ x) y)
      (w ⬝ᵥ (P *ᵥ (c + L *ᵥ (X *ᵥ (y - B *ᵥ c)))) +
        Real.sqrt (1 - (X *ᵥ (y - B *ᵥ c)) ⬝ᵥ (X *ᵥ (y - B *ᵥ c))) *
          Real.sqrt (((P * L * N)ᵀ *ᵥ w) ⬝ᵥ ((P * L * N)ᵀ *ᵥ w))) := …

theorem unitBall_subset_box (z : Fin r → ℝ) (hz : z ⬝ᵥ z ≤ 1) :
    z ∈ Icc (-1 : Fin r → ℝ) 1 := …

theorem ellipsoid_finiteDomainBound (c : Fin n → ℝ) (L : Matrix (Fin n) (Fin r) ℝ)
    (B : Matrix (Fin m) (Fin n) ℝ) (P : Matrix (Fin q) (Fin n) ℝ) :
    FiniteDomainBound (P08EllipsoidImage.Ell c L) (fun x => B *ᵥ x) (fun x => P *ᵥ x) := …

def BoxPoly (A : Matrix (Fin k) (Fin n) ℝ) (b : Fin k → ℝ) (lo hi : Fin n → ℝ) :
    Set (Fin n → ℝ) := …

def HPoly {ι : Type*} (M : Matrix ι (Fin n) ℝ) (h : ι → ℝ) : Set (Fin n → ℝ) := …

abbrev AugIdx (k n m : ℕ) := …

def augMat (A : Matrix (Fin k) (Fin n) ℝ) (B : Matrix (Fin m) (Fin n) ℝ) :
    Matrix (AugIdx k n m) (Fin n) ℝ := …

def augRhs (b : Fin k → ℝ) (lo hi : Fin n → ℝ) (y : Fin m → ℝ) : AugIdx k n m → ℝ := …

theorem polytope_fibre_eq_aug (A : Matrix (Fin k) (Fin n) ℝ) (b : Fin k → ℝ)
    (lo hi : Fin n → ℝ) (B : Matrix (Fin m) (Fin n) ℝ) (y : Fin m → ℝ) :
    Fibre (BoxPoly A b lo hi) (fun x => B *ᵥ x) y = HPoly (augMat A B) (augRhs b lo hi y) := …

theorem dot_mulVec_eq {ι κ : Type*} [Fintype ι] [Fintype κ] (P : Matrix ι κ ℝ) (w : ι → ℝ)
    (x : κ → ℝ) : w ⬝ᵥ (P *ᵥ x) = (Pᵀ *ᵥ w) ⬝ᵥ x := …

theorem support_transport {Y : Type*} (F : Set (Fin n → ℝ)) (B : (Fin n → ℝ) → Y) (y : Y)
    (P : Matrix (Fin q) (Fin n) ℝ) (w : Fin q → ℝ) :
    (fun θ => w ⬝ᵥ θ) '' FibreImage F B (fun x => P *ᵥ x) y =
      (fun x => (Pᵀ *ᵥ w) ⬝ᵥ x) '' Fibre F B y := …

theorem dual_certificate_upper {ι : Type*} [Fintype ι] (M : Matrix ι (Fin n) ℝ) (h : ι → ℝ)
    (c : Fin n → ℝ) (lam : ι → ℝ) (hlam : 0 ≤ lam) (hdual : Mᵀ *ᵥ lam = c) :
    ∀ x ∈ HPoly M h, c ⬝ᵥ x ≤ lam ⬝ᵥ h := …

theorem dual_certificate_isGreatest {ι : Type*} [Fintype ι] (M : Matrix ι (Fin n) ℝ)
    (h : ι → ℝ) (c : Fin n → ℝ) (lam : ι → ℝ) (hlam : 0 ≤ lam) (hdual : Mᵀ *ᵥ lam = c)
    (xs : Fin n → ℝ) (hxs : xs ∈ HPoly M h) (hval : c ⬝ᵥ xs = lam ⬝ᵥ h) :
    IsGreatest ((fun x => c ⬝ᵥ x) '' HPoly M h) (lam ⬝ᵥ h) := …

theorem dual_certificate_isLeast {ι : Type*} [Fintype ι] (M : Matrix ι (Fin n) ℝ)
    (h : ι → ℝ) (c : Fin n → ℝ) (lam : ι → ℝ) (hlam : 0 ≤ lam) (hdual : Mᵀ *ᵥ lam = -c)
    (xs : Fin n → ℝ) (hxs : xs ∈ HPoly M h) (hval : c ⬝ᵥ xs = -(lam ⬝ᵥ h)) :
    IsLeast ((fun x => c ⬝ᵥ x) '' HPoly M h) (-(lam ⬝ᵥ h)) := …

theorem polytope_finiteDomainBound (A : Matrix (Fin k) (Fin n) ℝ) (b : Fin k → ℝ)
    (lo hi : Fin n → ℝ) (B : Matrix (Fin m) (Fin n) ℝ) (P : Matrix (Fin q) (Fin n) ℝ) :
    FiniteDomainBound (BoxPoly A b lo hi) (fun x => B *ᵥ x) (fun x => P *ᵥ x) := …

def A₁ : Matrix (Fin 1) (Fin 2) ℝ := …

def b₁ : Fin 1 → ℝ := …

def lo₁ : Fin 2 → ℝ := …

def hi₁ : Fin 2 → ℝ := …

def B₁ : Matrix (Fin 1) (Fin 2) ℝ := …

def y₁ : Fin 1 → ℝ := …

def P₁ : Matrix (Fin 1) (Fin 2) ℝ := …

def w₁ : Fin 1 → ℝ := …

def lamMax : AugIdx 1 2 1 → ℝ := …

def lamMin : AugIdx 1 2 1 → ℝ := …

theorem instance_fibreImage_eq :
    FibreImage (BoxPoly A₁ b₁ lo₁ hi₁) (fun x => B₁ *ᵥ x) (fun x => P₁ *ᵥ x) y₁ =
      {θ | 0 ≤ θ 0 ∧ θ 0 ≤ 3 / 2} := …

theorem instance_support_max :
    IsGreatest ((fun θ => w₁ ⬝ᵥ θ) ''
      FibreImage (BoxPoly A₁ b₁ lo₁ hi₁) (fun x => B₁ *ᵥ x) (fun x => P₁ *ᵥ x) y₁) (3 / 2) := …

theorem instance_support_min :
    IsLeast ((fun θ => w₁ ⬝ᵥ θ) ''
      FibreImage (BoxPoly A₁ b₁ lo₁ hi₁) (fun x => B₁ *ᵥ x) (fun x => P₁ *ᵥ x) y₁) 0 := …

def arc : Set (Fin 2 → ℝ) := …

def parabola : Set (Fin 2 → ℝ) := …

def Bc : (Fin 2 → ℝ) →ₗ[ℝ] ℝ := …

def Pc : (Fin 2 → ℝ) →ₗ[ℝ] ℝ := …

theorem curved_kernelInclusion_fails :
    ¬ KernelInclusion (⊤ : Submodule ℝ (Fin 2 → ℝ)) Bc Pc := …

theorem curved_arc_domainCoercivity : DomainCoercivity arc Bc Pc := …

theorem curved_arc_fibreImage (y : ℝ) :
    (y ∈ Icc (-1 : ℝ) 1 → FibreImage arc Bc Pc y = {y ^ 2}) ∧
      (y ∉ Icc (-1 : ℝ) 1 → FibreImage arc Bc Pc y = ∅) := …

theorem curved_linear_iff_fails :
    ¬ (DomainCoercivity arc Bc Pc ↔ KernelInclusion (⊤ : Submodule ℝ (Fin 2 → ℝ)) Bc Pc) := …

theorem universal_linear_iff_false :
    ¬ ∀ (F : Set (Fin 2 → ℝ)) (B P : (Fin 2 → ℝ) →ₗ[ℝ] ℝ),
      (DomainCoercivity F B P ↔ KernelInclusion (⊤ : Submodule ℝ (Fin 2 → ℝ)) B P) := …

theorem parabola_identified (y : ℝ) : (FibreImage parabola Bc Pc y).Subsingleton := …

theorem parabola_not_domainCoercivity : ¬ DomainCoercivity parabola Bc Pc := …
```
