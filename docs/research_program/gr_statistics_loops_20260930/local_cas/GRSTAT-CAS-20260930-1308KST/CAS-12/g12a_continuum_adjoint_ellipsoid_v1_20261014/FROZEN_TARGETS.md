# G12-A frozen targets (GR-CAS-12, TEFF-A3: weighted continuum adjoint and collision moment ellipsoid)

Frozen 2026-10-14 BEFORE any proof compile. Before this file only the unchanged reused modules
(`raw/compile_01..11_dep_*`) and one `#check` API probe (`raw/compile_12_probe01_api`) were compiled.
Module `G12AContinuumAdjoint` (`lean/G12AContinuumAdjoint.lean`), namespace `G12A`, Lean 4.31.0,
Mathlib `fabf563a7c95a166b8d7b6efca11c8b4dc9d911f`, Lake project `/home/cosmosapjw/lean_oracles/viii_oracle`.
Imports (unchanged; `SOURCE_RECOVERY.md` §2): `Mathlib`, `G11CWeightedEllipsoid` (→ G11-B, G11-A,
C01 v2, CAS11-C02, CAS11-C03), `G12DCardClosure` (→ G12-D interface/envelope, PlanckIR).

Source map: `SOURCE_RECOVERY.md` §1. Card lean_steps ↔ targets: step 1 ↔ T1 (+T9 instance), step 2 ↔ T2/T3
(explicit-kernel adjoint domain + bounded-kernel discharge; T10 supplementary Hilbert-adjoint packaging),
step 3 ↔ T2 `adjoint_pair`, step 4 ↔ T3 `collAdj_memLp`, T4, T5, step 5 ↔ T6, T7, T8.
Card acceptance: (1) no finite-matrix evidence — CAS12-C01 is not imported; (2) τ(E) × kernel product kept —
T7 `collAdj_eigen`, `collEvec_eigen`, T8; (3) quantifiers/domain/measure/branches — below; (4) build +
`#print axioms` here, fresh independent review is a separate lane (not claimed).

## 0. Definitions (frozen)

```lean
open MeasureTheory Set Filter Topology Matrix
open scoped ENNReal

namespace G12A
open G11A G11B G11C

section Operator
variable {Y S : Type*} [MeasurableSpace Y] [MeasurableSpace S]

/-- gain (angular redistribution) term at fixed energy: ∫ P(e,e') h(E,e') dσ(e') -/
noncomputable def gain (σ : Measure S) (P : S → S → ℝ) (h : Y × S → ℝ) : Y × S → ℝ :=
  fun x => ∫ e', P x.2 e' * h (x.1, e') ∂σ

/-- source S:133  (Lh)(E,e) = τ(E) [∫ P(e,e') h(E,e') dσ(e') − h(E,e)]  (linear, elastic, scalar) -/
noncomputable def collOp (σ : Measure S) (τ : Y → ℝ) (P : S → S → ℝ) (h : Y × S → ℝ) : Y × S → ℝ :=
  fun x => τ x.1 * (gain σ P h x - h x)

def transposeKernel (P : S → S → ℝ) : S → S → ℝ := fun e e' => P e' e

/-- the formal dν-adjoint: same rate, transposed kernel -/
noncomputable def collAdj (σ : Measure S) (τ : Y → ℝ) (P : S → S → ℝ) (K : Y × S → ℝ) : Y × S → ℝ :=
  collOp σ τ (transposeKernel P) K

/-- the kernel-product integrand of ⟨K, gain h⟩ on (ν ⊗ σ), ν = ρ ⊗ σ -/
def fubKernel (τ : Y → ℝ) (P : S → S → ℝ) (K h : Y × S → ℝ) : (Y × S) × S → ℝ :=
  fun p => (τ p.1.1 * K p.1) * (P p.1.2 p.2 * h (p.1.1, p.2))

/-- collision residual vector e_j = ⟨K_j, L(f − g)⟩_ν (card scope form) -/
noncomputable def collEvec {n : ℕ} (ρ : Measure Y) (σ : Measure S) (τ : Y → ℝ) (P : S → S → ℝ)
    (K : Fin n → Y × S → ℝ) (f g : Y × S → ℝ) : Fin n → ℝ :=
  fun j => ∫ x, K j x * collOp σ τ P (fun y => f y - g y) x ∂(ρ.prod σ)

/-- ((E,e),e') ↦ ((E,e'),e) -/
def angSwap : (Y × S) × S ≃ᵐ (Y × S) × S :=
  (MeasurableEquiv.prodAssoc.trans ((MeasurableEquiv.refl Y).prodCongr MeasurableEquiv.prodComm)).trans
    MeasurableEquiv.prodAssoc.symm
```

`(BH)` abbreviates verbatim the G11-C budget hypothesis list on ν = `ρ.prod σ`:
`(s : Stat) (f g W : Y × S → ℝ) (hf : Measurable f) (hg : Measurable g)
 (hfd : ∀ᵐ x ∂(ρ.prod σ), f x ∈ cdom s) (hgd : ∀ᵐ x ∂(ρ.prod σ), g x ∈ dom s)
 (hW : WEnvelope (ρ.prod σ) s W f g) {ε : ℝ} (hε0 : 0 ≤ ε)
 (hε : Dext (ρ.prod σ) (hS s) (hS' s) f g ≤ ENNReal.ofReal ε)`.
`(BR)` abbreviates the bounded-route hypotheses
`(w : Y → ℝ) (hwm : Measurable w) (hwpos : ∀ᵐ x ∂(ρ.prod σ), 0 < w x.1) (τ : Y → ℝ) (hτm : Measurable τ)
 {τmax : ℝ} (hτ : ∀ E, |τ E| ≤ τmax) (P : S → S → ℝ) (hPm : Measurable (Function.uncurry P)) {Pmax : ℝ}
 (hP : ∀ e e', |P e e'| ≤ Pmax)`.
`ENVSPEC` below writes these out in full in the source; the abbreviations are only for this file.

## T1 — operator, medium, dν, domain (card step 1)

```lean
theorem collAdj_eq_collOp_of_symm (σ : Measure S) (τ : Y → ℝ) {P : S → S → ℝ}
    (hP : ∀ e e', P e e' = P e' e) : collAdj σ τ P = collOp σ τ P

theorem collOp_sub_of_integrable (σ : Measure S) (τ : Y → ℝ) (P : S → S → ℝ) (f g : Y × S → ℝ)
    (x : Y × S) (hfx : Integrable (fun e' => P x.2 e' * f (x.1, e')) σ)
    (hgx : Integrable (fun e' => P x.2 e' * g (x.1, e')) σ) :
    collOp σ τ P (fun y => f y - g y) x = collOp σ τ P f x - collOp σ τ P g x

-- source (A7) form e_j = ⟨K_j, Lf − Lg⟩ under a.e. angular-section integrability
theorem collEvec_eq_sub {n : ℕ} (ρ : Measure Y) (σ : Measure S) (τ : Y → ℝ) (P : S → S → ℝ)
    (K : Fin n → Y × S → ℝ) (f g : Y × S → ℝ)
    (hsec : ∀ᵐ x ∂(ρ.prod σ), Integrable (fun e' => P x.2 e' * f (x.1, e')) σ ∧
      Integrable (fun e' => P x.2 e' * g (x.1, e')) σ) (j : Fin n) :
    collEvec ρ σ τ P K f g j = ∫ x, K j x * (collOp σ τ P f x - collOp σ τ P g x) ∂(ρ.prod σ)

end Operator

-- the source's concrete scalar elastic (Thomson-shape) kernel on the unit sphere
noncomputable def thomsonP (e e' : Sphere2) : ℝ :=
  3 * (1 + (inner ℝ (e : EuclideanSpace ℝ (Fin 3)) (e' : EuclideanSpace ℝ (Fin 3))) ^ 2) / (16 * Real.pi)
theorem thomsonP_symm (e e' : Sphere2) : thomsonP e e' = thomsonP e' e
theorem thomsonP_measurable : Measurable (Function.uncurry thomsonP)
theorem thomsonP_bounds (e e' : Sphere2) : 0 ≤ thomsonP e e' ∧ thomsonP e e' ≤ 3 / (8 * Real.pi)
```

## T2 — explicit adjoint domain and kernel-Fubini adjoint pair identity (card steps 2-3)

```lean
theorem angSwap_apply (p : (Y × S) × S) : angSwap p = ((p.1.1, p.2), p.1.2)

theorem angSwap_measurePreserving (ρ : Measure Y) (σ : Measure S) [SFinite ρ] [SFinite σ] :
    MeasurePreserving angSwap ((ρ.prod σ).prod σ) ((ρ.prod σ).prod σ)

-- ⟨K, L h⟩_ν = ⟨L* K, h⟩_ν on the domain {absolute integrability of the kernel product and loss term}
theorem adjoint_pair (ρ : Measure Y) (σ : Measure S) [SFinite ρ] [SFinite σ] (τ : Y → ℝ)
    (P : S → S → ℝ) (K h : Y × S → ℝ)
    (hG : Integrable (fubKernel τ P K h) ((ρ.prod σ).prod σ))
    (hloss : Integrable (fun x => τ x.1 * K x * h x) (ρ.prod σ)) :
    Integrable (fun x => K x * collOp σ τ P h x) (ρ.prod σ) ∧
      Integrable (fun x => collAdj σ τ P K x * h x) (ρ.prod σ) ∧
      ∫ x, K x * collOp σ τ P h x ∂(ρ.prod σ) = ∫ x, collAdj σ τ P K x * h x ∂(ρ.prod σ)
```

## T3 — bounded route: the adjoint domain is discharged and L*K ∈ L²(W dν) (card steps 2, 4)

```lean
theorem sq_integral_le (σ : Measure S) [IsFiniteMeasure σ] {u : S → ℝ} (hu : Integrable u σ)
    (hu2 : Integrable (fun e => u e ^ 2) σ) :
    (∫ e, u e ∂σ) ^ 2 ≤ σ.real univ * ∫ e, u e ^ 2 ∂σ

theorem fubKernel_integrable (ρ : Measure Y) (σ : Measure S) [SFinite ρ] [IsFiniteMeasure σ]
    (w : Y → ℝ) (hwpos : ∀ᵐ x ∂(ρ.prod σ), 0 < w x.1)
    (τ : Y → ℝ) (hτm : Measurable τ) {τmax : ℝ} (hτ : ∀ E, |τ E| ≤ τmax)
    (P : S → S → ℝ) (hPm : Measurable (Function.uncurry P)) {Pmax : ℝ} (hP : ∀ e e', |P e e'| ≤ Pmax)
    (K h : Y × S → ℝ) (hKm : AEStronglyMeasurable K (ρ.prod σ))
    (hhm : AEStronglyMeasurable h (ρ.prod σ))
    (hK2 : Integrable (fun x => w x.1 * K x ^ 2) (ρ.prod σ))
    (hh2 : Integrable (fun x => h x ^ 2 / w x.1) (ρ.prod σ)) :
    Integrable (fubKernel τ P K h) ((ρ.prod σ).prod σ) ∧
      Integrable (fun x => τ x.1 * K x * h x) (ρ.prod σ)

theorem collOp_memLp (ρ : Measure Y) (σ : Measure S) [SFinite ρ] [IsFiniteMeasure σ]
    (w : Y → ℝ) (hwm : Measurable w) (hwpos : ∀ᵐ x ∂(ρ.prod σ), 0 < w x.1)
    (τ : Y → ℝ) (hτm : Measurable τ) {τmax : ℝ} (hτ : ∀ E, |τ E| ≤ τmax)
    (P : S → S → ℝ) (hPm : Measurable (Function.uncurry P)) {Pmax : ℝ} (hP : ∀ e e', |P e e'| ≤ Pmax)
    {K : Y × S → ℝ} (hK : MemLp K 2 (wmeas (ρ.prod σ) (fun x => w x.1))) :
    MemLp (collOp σ τ P K) 2 (wmeas (ρ.prod σ) (fun x => w x.1))

theorem collAdj_memLp (same hypotheses as collOp_memLp) :
    MemLp (collAdj σ τ P K) 2 (wmeas (ρ.prod σ) (fun x => w x.1))
```

## T4 — layer 1 (source-faithful conditional form of (A7)): collision residual ellipsoid

```lean
theorem collision_ellipsoid (ρ : Measure Y) (σ : Measure S) [SFinite ρ] [SFinite σ]
    (s : Stat) (f g W : Y × S → ℝ) (hf : Measurable f) (hg : Measurable g)
    (hfd : ∀ᵐ x ∂(ρ.prod σ), f x ∈ cdom s) (hgd : ∀ᵐ x ∂(ρ.prod σ), g x ∈ dom s)
    (hW : WEnvelope (ρ.prod σ) s W f g) {ε : ℝ} (hε0 : 0 ≤ ε)
    (hε : Dext (ρ.prod σ) (hS s) (hS' s) f g ≤ ENNReal.ofReal ε)
    {m n : ℕ} (φ : Fin m → Y × S → ℝ) (hφ : ∀ a, MemLp (φ a) 2 (wmeas (ρ.prod σ) W))
    (hmatch : ∀ a, ∫ x, φ a x * (f x - g x) ∂(ρ.prod σ) = 0)
    (τ : Y → ℝ) (P : S → S → ℝ) (K : Fin n → Y × S → ℝ)
    (hLK : ∀ j, MemLp (collAdj σ τ P (K j)) 2 (wmeas (ρ.prod σ) W))
    (hG : ∀ j, Integrable (fubKernel τ P (K j) (fun y => f y - g y)) ((ρ.prod σ).prod σ))
    (hloss : ∀ j, Integrable (fun x => τ x.1 * K j x * (f x - g x)) (ρ.prod σ)) :
    collEvec ρ σ τ P K f g = evec (ρ.prod σ) (fun j => collAdj σ τ P (K j)) f g ∧
      (gramR (ρ.prod σ) W φ hφ (fun j => collAdj σ τ P (K j)) hLK).PosSemidef ∧
      collEvec ρ σ τ P K f g ∈
        LinearMap.range (gramR (ρ.prod σ) W φ hφ (fun j => collAdj σ τ P (K j)) hLK).toLin' ∧
      collEvec ρ σ τ P K f g ⬝ᵥ
        (CAS11C02.spectralPinvMatrix (gramR (ρ.prod σ) W φ hφ (fun j => collAdj σ τ P (K j)) hLK)
          (gramR_posSemidef (ρ.prod σ) W φ hφ (fun j => collAdj σ τ P (K j)) hLK).isHermitian *ᵥ
          collEvec ρ σ τ P K f g) ≤ 2 * ε
```
Here `gramR … (fun j => collAdj σ τ P (K j))` is exactly R_ij = ⟪r_i, r_j⟫ with r_j = L*K_j − P_V(L*K_j) (G11-C `residuals`).

## T5 — layer 2: bounded τ, bounded measurable kernel, energy-only W (all adjoint hypotheses derived)

```lean
theorem collision_ellipsoid_bounded (ρ : Measure Y) (σ : Measure S) [SFinite ρ] [IsFiniteMeasure σ]
    (s : Stat) (f g : Y × S → ℝ) (w : Y → ℝ) (hwm : Measurable w)
    (hf : Measurable f) (hg : Measurable g)
    (hfd : ∀ᵐ x ∂(ρ.prod σ), f x ∈ cdom s) (hgd : ∀ᵐ x ∂(ρ.prod σ), g x ∈ dom s)
    (hW : WEnvelope (ρ.prod σ) s (fun x => w x.1) f g) {ε : ℝ} (hε0 : 0 ≤ ε)
    (hε : Dext (ρ.prod σ) (hS s) (hS' s) f g ≤ ENNReal.ofReal ε)
    (τ : Y → ℝ) (hτm : Measurable τ) {τmax : ℝ} (hτ : ∀ E, |τ E| ≤ τmax)
    (P : S → S → ℝ) (hPm : Measurable (Function.uncurry P)) {Pmax : ℝ} (hP : ∀ e e', |P e e'| ≤ Pmax)
    {m n : ℕ} (φ : Fin m → Y × S → ℝ) (hφ : ∀ a, MemLp (φ a) 2 (wmeas (ρ.prod σ) (fun x => w x.1)))
    (hmatch : ∀ a, ∫ x, φ a x * (f x - g x) ∂(ρ.prod σ) = 0)
    (K : Fin n → Y × S → ℝ) (hK : ∀ j, MemLp (K j) 2 (wmeas (ρ.prod σ) (fun x => w x.1))) :
    (∀ j, MemLp (collAdj σ τ P (K j)) 2 (wmeas (ρ.prod σ) (fun x => w x.1))) ∧
    (∀ j, Integrable (fubKernel τ P (K j) (fun y => f y - g y)) ((ρ.prod σ).prod σ) ∧
          Integrable (fun x => τ x.1 * K j x * (f x - g x)) (ρ.prod σ)) ∧
    ∀ hLK : (∀ j, MemLp (collAdj σ τ P (K j)) 2 (wmeas (ρ.prod σ) (fun x => w x.1))),
      collEvec ρ σ τ P K f g = evec (ρ.prod σ) (fun j => collAdj σ τ P (K j)) f g ∧
      (gramR (ρ.prod σ) (fun x => w x.1) φ hφ (fun j => collAdj σ τ P (K j)) hLK).PosSemidef ∧
      collEvec ρ σ τ P K f g ∈ LinearMap.range
        (gramR (ρ.prod σ) (fun x => w x.1) φ hφ (fun j => collAdj σ τ P (K j)) hLK).toLin' ∧
      collEvec ρ σ τ P K f g ⬝ᵥ
        (CAS11C02.spectralPinvMatrix
            (gramR (ρ.prod σ) (fun x => w x.1) φ hφ (fun j => collAdj σ τ P (K j)) hLK)
            (gramR_posSemidef (ρ.prod σ) (fun x => w x.1) φ hφ
              (fun j => collAdj σ τ P (K j)) hLK).isHermitian *ᵥ
          collEvec ρ σ τ P K f g) ≤ 2 * ε
```

## T6 — exact retained collision moment (card step 5, first branch)

```lean
-- L*K_j ∈ V for all j ⇒ R = 0 and every collision residual vanishes
theorem collision_exact_of_retained (ρ σ) [SFinite ρ] [SFinite σ] (BH) {m n : ℕ}
    (φ : Fin m → Y × S → ℝ) (hφ : ∀ a, MemLp (φ a) 2 (wmeas (ρ.prod σ) W))
    (hmatch : ∀ a, ∫ x, φ a x * (f x - g x) ∂(ρ.prod σ) = 0)
    (τ : Y → ℝ) (P : S → S → ℝ) (K : Fin n → Y × S → ℝ)
    (hLK : ∀ j, MemLp (collAdj σ τ P (K j)) 2 (wmeas (ρ.prod σ) W))
    (hG : ∀ j, Integrable (fubKernel τ P (K j) (fun y => f y - g y)) ((ρ.prod σ).prod σ))
    (hloss : ∀ j, Integrable (fun x => τ x.1 * K j x * (f x - g x)) (ρ.prod σ))
    (hret : ∀ j, (hLK j).toLp (collAdj σ τ P (K j)) ∈ retainedSpan (ρ.prod σ) W φ hφ) :
    gramR (ρ.prod σ) W φ hφ (fun j => collAdj σ τ P (K j)) hLK = 0 ∧ collEvec ρ σ τ P K f g = 0

-- budget-free: L*K = Σ c_a φ_a a.e. ⇒ the collision moment is the same combination of retained moments
theorem collision_moment_of_representation (ρ : Measure Y) (σ : Measure S) [SFinite ρ] [SFinite σ]
    (τ : Y → ℝ) (P : S → S → ℝ) (K f g : Y × S → ℝ) {m : ℕ} (φ : Fin m → Y × S → ℝ) (c : Fin m → ℝ)
    (hG : Integrable (fubKernel τ P K (fun y => f y - g y)) ((ρ.prod σ).prod σ))
    (hloss : Integrable (fun x => τ x.1 * K x * (f x - g x)) (ρ.prod σ))
    (hφi : ∀ a, Integrable (fun x => φ a x * (f x - g x)) (ρ.prod σ))
    (hrep : collAdj σ τ P K =ᵐ[ρ.prod σ] fun x => ∑ a, c a * φ a x) :
    ∫ x, K x * collOp σ τ P (fun y => f y - g y) x ∂(ρ.prod σ) =
      ∑ a, c a * ∫ x, φ a x * (f x - g x) ∂(ρ.prod σ)
```
(`(BH)` in `collision_exact_of_retained` is the literal list of §0 with ν = `ρ.prod σ`.)

## T7 — energy-dependent τ(E) versus constant τ (card step 5, second branch; COLL-TAU)

```lean
-- the τ(E) × score product is kept
theorem collAdj_eigen (μ : Measure (Y × S)) (σ : Measure S) (τ : Y → ℝ) (P : S → S → ℝ)
    (K : Y × S → ℝ) (p : ℝ) (heig : ∀ᵐ x ∂μ, ∫ e', P e' x.2 * K (x.1, e') ∂σ = p * K x) :
    collAdj σ τ P K =ᵐ[μ] fun x => τ x.1 * (p - 1) * K x

-- e_j = (p_j − 1) ∫ τ(E) K_j (f − g) dν : the additional τ-weighted moment
theorem collEvec_eigen (ρ : Measure Y) (σ : Measure S) [SFinite ρ] [SFinite σ] (τ : Y → ℝ)
    (P : S → S → ℝ) {n : ℕ} (K : Fin n → Y × S → ℝ) (f g : Y × S → ℝ) (p : Fin n → ℝ)
    (hG : ∀ j, Integrable (fubKernel τ P (K j) (fun y => f y - g y)) ((ρ.prod σ).prod σ))
    (hloss : ∀ j, Integrable (fun x => τ x.1 * K j x * (f x - g x)) (ρ.prod σ))
    (heig : ∀ j, ∀ᵐ x ∂(ρ.prod σ), ∫ e', P e' x.2 * K j (x.1, e') ∂σ = p j * K j x) (j : Fin n) :
    collEvec ρ σ τ P K f g j = (p j - 1) * ∫ x, τ x.1 * K j x * (f x - g x) ∂(ρ.prod σ)

-- constant τ = t: a retained eigen-kernel has a retained adjoint
theorem constant_tau_retained (ρ : Measure Y) (σ : Measure S) (W : Y × S → ℝ) {m : ℕ}
    (φ : Fin m → Y × S → ℝ) (hφ : ∀ a, MemLp (φ a) 2 (wmeas (ρ.prod σ) W))
    (t : ℝ) (P : S → S → ℝ) (K : Y × S → ℝ) (p : ℝ)
    (heig : ∀ᵐ x ∂(ρ.prod σ), ∫ e', P e' x.2 * K (x.1, e') ∂σ = p * K x)
    (hK : MemLp K 2 (wmeas (ρ.prod σ) W))
    (hLK : MemLp (collAdj σ (fun _ => t) P K) 2 (wmeas (ρ.prod σ) W))
    (hKV : hK.toLp K ∈ retainedSpan (ρ.prod σ) W φ hφ) :
    hLK.toLp (collAdj σ (fun _ => t) P K) ∈ retainedSpan (ρ.prod σ) W φ hφ

-- constant τ, retained eigen-kernels ⇒ exact collision moments
theorem constant_tau_exact (ρ σ) [SFinite ρ] [SFinite σ] (BH) {m n : ℕ}
    (φ : Fin m → Y × S → ℝ) (hφ : ∀ a, MemLp (φ a) 2 (wmeas (ρ.prod σ) W))
    (hmatch : ∀ a, ∫ x, φ a x * (f x - g x) ∂(ρ.prod σ) = 0)
    (t : ℝ) (P : S → S → ℝ) (K : Fin n → Y × S → ℝ) (p : Fin n → ℝ)
    (heig : ∀ j, ∀ᵐ x ∂(ρ.prod σ), ∫ e', P e' x.2 * K j (x.1, e') ∂σ = p j * K j x)
    (hK : ∀ j, MemLp (K j) 2 (wmeas (ρ.prod σ) W))
    (hKV : ∀ j, (hK j).toLp (K j) ∈ retainedSpan (ρ.prod σ) W φ hφ)
    (hLK : ∀ j, MemLp (collAdj σ (fun _ => t) P (K j)) 2 (wmeas (ρ.prod σ) W))
    (hG : ∀ j, Integrable (fubKernel (fun _ => t) P (K j) (fun y => f y - g y)) ((ρ.prod σ).prod σ))
    (hloss : ∀ j, Integrable (fun x => t * K j x * (f x - g x)) (ρ.prod σ)) :
    collEvec ρ σ (fun _ => t) P K f g = 0
```

## T8 — negative control (COLL-TAU) and non-vacuity witness

```lean
-- energy-dependent τ: K retained and matched, symmetric kernel, eigen-kernel, Fubini hypotheses hold,
-- yet the collision moment is NOT determined (≠ 0); the same data with constant τ give 0.
theorem energy_dependent_tau_counterexample :
    ∃ (τ : Bool → ℝ) (P : Bool → Bool → ℝ) (K f g : Bool × Bool → ℝ) (p : ℝ),
      τ true ≠ τ false ∧ (∀ e e', P e e' = P e' e) ∧ (∀ x, 0 < f x ∧ 0 < g x) ∧
      (∀ x, ∫ e', P e' x.2 * K (x.1, e') ∂(Measure.count : Measure Bool) = p * K x) ∧
      Integrable (fubKernel τ P K (fun y => f y - g y))
        (((Measure.count : Measure Bool).prod (Measure.count : Measure Bool)).prod
          (Measure.count : Measure Bool)) ∧
      Integrable (fun x => τ x.1 * K x * (f x - g x))
        ((Measure.count : Measure Bool).prod (Measure.count : Measure Bool)) ∧
      ∫ x, K x * (f x - g x) ∂((Measure.count : Measure Bool).prod (Measure.count : Measure Bool)) = 0 ∧
      collEvec (Measure.count : Measure Bool) (Measure.count : Measure Bool) τ P
        (fun _ : Fin 1 => K) f g 0 ≠ 0 ∧
      collEvec (Measure.count : Measure Bool) (Measure.count : Measure Bool) (fun _ => τ true) P
        (fun _ : Fin 1 => K) f g 0 = 0

-- non-vacuity: every hypothesis of T5 (with m = 0) holds on a finite model and the collision residual ≠ 0
theorem nonvacuity_bounded_witness :
    ∃ (f g : Bool × Bool → ℝ) (w τ : Bool → ℝ) (P : Bool → Bool → ℝ)
      (K : Fin 1 → Bool × Bool → ℝ) (ε : ℝ),
      Measurable f ∧ Measurable g ∧ Measurable w ∧ Measurable τ ∧ Measurable (Function.uncurry P) ∧
      (∀ᵐ x ∂((Measure.count : Measure Bool).prod (Measure.count : Measure Bool)), f x ∈ cdom .MB) ∧
      (∀ᵐ x ∂((Measure.count : Measure Bool).prod (Measure.count : Measure Bool)), g x ∈ dom .MB) ∧
      WEnvelope ((Measure.count : Measure Bool).prod (Measure.count : Measure Bool)) .MB
        (fun x => w x.1) f g ∧
      0 ≤ ε ∧
      Dext ((Measure.count : Measure Bool).prod (Measure.count : Measure Bool)) (hS .MB) (hS' .MB) f g
        ≤ ENNReal.ofReal ε ∧
      (∀ E, |τ E| ≤ 1) ∧ (∀ e e', |P e e'| ≤ 1) ∧
      (∀ j, MemLp (K j) 2
        (wmeas ((Measure.count : Measure Bool).prod (Measure.count : Measure Bool)) (fun x => w x.1))) ∧
      f ≠ g ∧
      collEvec (Measure.count : Measure Bool) (Measure.count : Measure Bool) τ P K f g ≠ 0
```

## T9 — the source instance: dν = C E² dE dΩ on (0,∞) × S², Thomson-shape kernel, photon envelope (A5)

```lean
noncomputable def energyMeasure (C : ℝ) : Measure ℝ :=
  (volume.restrict (Ioi (0 : ℝ))).withDensity (fun E => ENNReal.ofReal (C * E ^ 2))
theorem nu_eq_prod (C : ℝ) : nu C = (energyMeasure C).prod dOmega
noncomputable def photonW (b : ℝ) : ℝ × Sphere2 → ℝ := fun x => CAS12PlanckIR.weight b x.1

theorem photon_envelope (C b : ℝ) (hb : 0 < b) (f g : ℝ × Sphere2 → ℝ)
    (hfF : ∀ᵐ x ∂nu C, 0 ≤ f x ∧ f x ≤ G12D.occupation b 0 x.1)
    (hgF : ∀ᵐ x ∂nu C, 0 < g x ∧ g x ≤ G12D.occupation b 0 x.1) :
    (∀ᵐ x ∂nu C, f x ∈ cdom .BE) ∧ (∀ᵐ x ∂nu C, g x ∈ dom .BE) ∧
      WEnvelope (nu C) .BE (photonW b) f g

theorem photon_thomson_collision_ellipsoid (C b : ℝ) (hb : 0 < b) (f g : ℝ × Sphere2 → ℝ)
    (hf : Measurable f) (hg : Measurable g)
    (hfF : ∀ᵐ x ∂nu C, 0 ≤ f x ∧ f x ≤ G12D.occupation b 0 x.1)
    (hgF : ∀ᵐ x ∂nu C, 0 < g x ∧ g x ≤ G12D.occupation b 0 x.1)
    {ε : ℝ} (hε0 : 0 ≤ ε) (hε : Dext (nu C) (hS .BE) (hS' .BE) f g ≤ ENNReal.ofReal ε)
    (τ : ℝ → ℝ) (hτm : Measurable τ) {τmax : ℝ} (hτ : ∀ E, |τ E| ≤ τmax)
    {m n : ℕ} (φ : Fin m → ℝ × Sphere2 → ℝ) (hφ : ∀ a, MemLp (φ a) 2 (wmeas (nu C) (photonW b)))
    (hmatch : ∀ a, ∫ x, φ a x * (f x - g x) ∂nu C = 0)
    (K : Fin n → ℝ × Sphere2 → ℝ) (hK : ∀ j, MemLp (K j) 2 (wmeas (nu C) (photonW b))) :
    collAdj dOmega τ thomsonP = collOp dOmega τ thomsonP ∧
    (∀ j, MemLp (collOp dOmega τ thomsonP (K j)) 2 (wmeas (nu C) (photonW b))) ∧
    ∀ hLK : (∀ j, MemLp (collOp dOmega τ thomsonP (K j)) 2 (wmeas (nu C) (photonW b))),
      collEvec (energyMeasure C) dOmega τ thomsonP K f g =
          evec (nu C) (fun j => collOp dOmega τ thomsonP (K j)) f g ∧
        (gramR (nu C) (photonW b) φ hφ (fun j => collOp dOmega τ thomsonP (K j)) hLK).PosSemidef ∧
        collEvec (energyMeasure C) dOmega τ thomsonP K f g ∈ LinearMap.range
          (gramR (nu C) (photonW b) φ hφ (fun j => collOp dOmega τ thomsonP (K j)) hLK).toLin' ∧
        collEvec (energyMeasure C) dOmega τ thomsonP K f g ⬝ᵥ
          (CAS11C02.spectralPinvMatrix
              (gramR (nu C) (photonW b) φ hφ (fun j => collOp dOmega τ thomsonP (K j)) hLK)
              (gramR_posSemidef (nu C) (photonW b) φ hφ
                (fun j => collOp dOmega τ thomsonP (K j)) hLK).isHermitian *ᵥ
            collEvec (energyMeasure C) dOmega τ thomsonP K f g) ≤ 2 * ε
```

## T10 (SUPPLEMENTARY; reported NOT_REACHED if not proved) — Hilbert-adjoint packaging on L²(w(E) dν)

```lean
structure BoundedRoute (ρ : Measure Y) (σ : Measure S) (w τ : Y → ℝ) (P : S → S → ℝ) : Prop where
  hwm : Measurable w
  hwpos : ∀ᵐ x ∂(ρ.prod σ), 0 < w x.1
  hτm : Measurable τ
  τbd : ∃ τmax, ∀ E, |τ E| ≤ τmax
  hPm : Measurable (Function.uncurry P)
  Pbd : ∃ Pmax, ∀ e e', |P e e'| ≤ Pmax

theorem BoundedRoute.transpose (hB : BoundedRoute ρ σ w τ P) : BoundedRoute ρ σ w τ (transposeKernel P)

noncomputable def collCLM (ρ : Measure Y) (σ : Measure S) [SFinite ρ] [IsFiniteMeasure σ]
    (w τ : Y → ℝ) (P : S → S → ℝ) (hB : BoundedRoute ρ σ w τ P) :
    L2W (ρ.prod σ) (fun x => w x.1) →L[ℝ] L2W (ρ.prod σ) (fun x => w x.1)

theorem collCLM_coeFn ... (F : L2W (ρ.prod σ) (fun x => w x.1)) :
    (collCLM ρ σ w τ P hB F : Y × S → ℝ) =ᵐ[wmeas (ρ.prod σ) (fun x => w x.1)] collOp σ τ P F

theorem collCLM_adjoint ... :
    ContinuousLinearMap.adjoint (collCLM ρ σ w τ P hB) = collCLM ρ σ w τ (transposeKernel P) hB.transpose
```

## Discipline

* No conclusion is assumed: the adjoint identity is derived by Fubini + the measure-preserving angle swap
  (T2); in layer 2 the adjoint-domain integrability and L*K ∈ L²(W dν) are derived (T3); the ellipsoid is
  the reused G11-C theorem applied to L*K_j (no re-proof, no new hypothesis on e).
* Layer 1 keeps the source's conditional hypotheses ("L*K_j satisfies the weighted integrability
  assumptions", S:120) explicit as `hLK`, plus the kernel-Fubini integrability (card step 3).
* Layer 2 hypotheses are sufficient conditions, stated explicitly: W = w(E) energy-only (as in (A5)),
  w measurable, |τ| ≤ τmax everywhere, P jointly measurable with |P| ≤ Pmax, σ finite, ρ s-finite.
  Symmetry and normalization of P are NOT assumed by T2-T7 (weaker hypotheses than the source model).
* τ(E) × kernel product is never dropped (T7, T8). Constant-τ exactness is a separate theorem.
* CAS12-C01 finite adjoint is not imported. No nonlinear / polarized / frequency-redistributing operator.
* Allowed axioms: propext, Classical.choice, Quot.sound only.
