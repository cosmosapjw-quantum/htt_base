# P09-A frozen targets (frozen before any proof attempt)

Namespace `P09SignedDepth`, file `lean/P09SignedDepth.lean`, `import Mathlib` only.
Toolchain: Lean 4.31.0, Mathlib `fabf563a7c95a166b8d7b6efca11c8b4dc9d911f`.
Source definitions: see `SOURCE_RECOVERY.md`.

## Setting (definitions; not theorems)

```lean
variable {d : ℕ} {n : Fin (d+1) → ℕ}
abbrev Idx (n : Fin (d+1) → ℕ) := Σ i : Fin (d+1), Fin (n i)          -- full ordered joint index
abbrev CIdx (n : Fin (d+1) → ℕ) := Σ j : Fin d, Fin (n j.succ)         -- contrast index
abbrev Transport (n : Fin (d+1) → ℕ) :=
  (j : Fin d) → Matrix (Fin (n j.succ)) (Fin (n j.castSucc)) ℝ          -- fixed K_j
def contrast (K : Transport n) (x : Idx n → ℝ) : CIdx n → ℝ :=
  fun p => x ⟨p.1.succ, p.2⟩ - (K p.1 *ᵥ fun b => x ⟨p.1.castSucc, b⟩) p.2
def contrastLin (K) : (Idx n → ℝ) →ₗ[ℝ] (CIdx n → ℝ)      -- toFun = contrast K
noncomputable def H (K) : Matrix (CIdx n) (Idx n) ℝ := LinearMap.toMatrix' (contrastLin K)
def anchored (K) (x : Idx n → ℝ) : Idx n → ℝ                  -- block 0: x_0; block j+1: contrast j
  := fun p => Fin.cases (motive := fun i => Fin (n i) → ℝ) (fun a => x ⟨0, a⟩)
       (fun j a => contrast K x ⟨j, a⟩) p.1 p.2
def anchoredLin (K) : (Idx n → ℝ) →ₗ[ℝ] (Idx n → ℝ)
noncomputable def Tmat (K) : Matrix (Idx n) (Idx n) ℝ := LinearMap.toMatrix' (anchoredLin K)
def restoreBlock (K) (r : Idx n → ℝ) : (i : Fin (d+1)) → Fin (n i) → ℝ :=
  Fin.induction (fun a => r ⟨0, a⟩) (fun j yj a => r ⟨j.succ, a⟩ + (K j *ᵥ yj) a)
def restore (K) (r : Idx n → ℝ) : Idx n → ℝ := fun p => restoreBlock K r p.1 p.2
noncomputable def meanVec (μ : Measure Ω) (x : Ω → ι → ℝ) : ι → ℝ := fun i => ∫ ω, x ω i ∂μ
noncomputable def covMat (μ : Measure Ω) (x : Ω → ι → ℝ) : Matrix ι ι ℝ :=
  fun i j => cov[fun ω => x ω i, fun ω => x ω j; μ]                    -- ALL ordered pairs
def blockDiagPart (C : Matrix (Idx n) (Idx n) ℝ) : Matrix (Idx n) (Idx n) ℝ :=
  fun p q => if p.1 = q.1 then C p q else 0                          -- cross blocks dropped (negative control only)
```

## Q1 — T and H, block lower-triangular, all cross blocks kept, depth 0 included

```lean
theorem H_mulVec (K : Transport n) (x : Idx n → ℝ) : H K *ᵥ x = contrast K x
theorem H_apply_succ (K) (j : Fin d) (a b : Fin (n j.succ)) :
    H K ⟨j, a⟩ ⟨j.succ, b⟩ = if a = b then 1 else 0
theorem H_apply_castSucc (K) (j : Fin d) (a : Fin (n j.succ)) (b : Fin (n j.castSucc)) :
    H K ⟨j, a⟩ ⟨j.castSucc, b⟩ = -K j a b
theorem H_apply_other (K) (j : Fin d) (i : Fin (d+1)) (a : Fin (n j.succ)) (b : Fin (n i))
    (h1 : i ≠ j.succ) (h2 : i ≠ j.castSucc) : H K ⟨j, a⟩ ⟨i, b⟩ = 0
theorem Tmat_mulVec (K) (x) : Tmat K *ᵥ x = anchored K x
theorem Tmat_apply_zero (K) (a : Fin (n 0)) (q : Idx n) :
    Tmat K ⟨0, a⟩ q = if q = ⟨0, a⟩ then 1 else 0
theorem Tmat_apply_succ (K) (j : Fin d) (a : Fin (n j.succ)) (q : Idx n) :
    Tmat K ⟨j.succ, a⟩ q = H K ⟨j, a⟩ q
theorem Tmat_apply_diag (K) (i : Fin (d+1)) (a b : Fin (n i)) :
    Tmat K ⟨i, a⟩ ⟨i, b⟩ = if a = b then 1 else 0
theorem Tmat_apply_upper (K) (i i' : Fin (d+1)) (a : Fin (n i)) (b : Fin (n i')) (h : i < i') :
    Tmat K ⟨i, a⟩ ⟨i', b⟩ = 0
theorem Tmat_blockTriangular (K) :
    (Tmat K).BlockTriangular (fun p : Idx n => OrderDual.toDual p.1)   -- lower block triangular
theorem anchored_depth_zero (n : Fin 1 → ℕ) (K : Transport n) : anchored K = id
theorem Tmat_depth_zero (n : Fin 1 → ℕ) (K : Transport n) : Tmat K = 1
```
Stretch (Q1s, non-blocking): `theorem Tmat_det (K) : (Tmat K).det = 1`.

## Q2 — explicit recursive inverse; bijection at every finite depth (incl. d = 0)

```lean
theorem anchored_restore (K : Transport n) (r : Idx n → ℝ) : anchored K (restore K r) = r
theorem restore_anchored (K : Transport n) (x : Idx n → ℝ) : restore K (anchored K x) = x
theorem anchored_bijective (K : Transport n) : Function.Bijective (anchored K)
def Tequiv (K : Transport n) : (Idx n → ℝ) ≃ₗ[ℝ] (Idx n → ℝ)       -- toFun anchored, invFun restore
noncomputable def Rmat (K) : Matrix (Idx n) (Idx n) ℝ := LinearMap.toMatrix' (Tequiv K).symm.toLinearMap
theorem Tmat_mul_Rmat (K) : Tmat K * Rmat K = 1
theorem Rmat_mul_Tmat (K) : Rmat K * Tmat K = 1
theorem restore_succ (K) (r) (j : Fin d) (a : Fin (n j.succ)) :
    restore K r ⟨j.succ, a⟩ = r ⟨j.succ, a⟩ + (K j *ᵥ fun b => restore K r ⟨j.castSucc, b⟩) a
theorem bijective_depth_zero (n : Fin 1 → ℕ) (K : Transport n) : Function.Bijective (anchored K)
```

## Q3 — mean and FULL covariance of a linear image of an actual L² random vector

```lean
variable {Ω : Type*} [MeasurableSpace Ω] {μ : Measure Ω} {ι κ : Type*} [Fintype ι] [Fintype κ]
theorem mean_mulVec (H : Matrix κ ι ℝ) (x : Ω → ι → ℝ)
    (hx : ∀ i, Integrable (fun ω => x ω i) μ) :
    meanVec μ (fun ω => H *ᵥ x ω) = H *ᵥ meanVec μ x
theorem covMat_mulVec [IsFiniteMeasure μ] (H : Matrix κ ι ℝ) (x : Ω → ι → ℝ)
    (hx : ∀ i, MemLp (fun ω => x ω i) 2 μ) :
    covMat μ (fun ω => H *ᵥ x ω) = H * covMat μ x * Hᵀ
theorem contrast_moments [IsProbabilityMeasure μ] (K : Transport n) (x : Ω → Idx n → ℝ)
    (hx : ∀ p, MemLp (fun ω => x ω p) 2 μ) :
    meanVec μ (fun ω => contrast K (x ω)) = H K *ᵥ meanVec μ x ∧
    covMat μ (fun ω => contrast K (x ω)) = H K * covMat μ x * (H K)ᵀ
theorem anchored_moments [IsProbabilityMeasure μ] (K : Transport n) (x : Ω → Idx n → ℝ)
    (hx : ∀ p, MemLp (fun ω => x ω p) 2 μ) :
    meanVec μ (fun ω => anchored K (x ω)) = Tmat K *ᵥ meanVec μ x ∧
    covMat μ (fun ω => anchored K (x ω)) = Tmat K * covMat μ x * (Tmat K)ᵀ
theorem HCHt_apply (K : Transport n) (C : Matrix (Idx n) (Idx n) ℝ) (j k : Fin d)
    (a : Fin (n j.succ)) (b : Fin (n k.succ)) :
    (H K * C * (H K)ᵀ) ⟨j, a⟩ ⟨k, b⟩ =
      C ⟨j.succ, a⟩ ⟨k.succ, b⟩
      - ∑ e, C ⟨j.succ, a⟩ ⟨k.castSucc, e⟩ * K k b e
      - ∑ c, K j a c * C ⟨j.castSucc, c⟩ ⟨k.succ, b⟩
      + ∑ c, ∑ e, K j a c * C ⟨j.castSucc, c⟩ ⟨k.castSucc, e⟩ * K k b e   -- D1 cross-block formula
```

## Q4 — law of Hx is the pushforward of the FULL joint law (no independence)

Measurable structure on `ι → ℝ` is Mathlib's `MeasurableSpace.pi` (Borel on each coordinate).
```lean
theorem law_mulVec (H : Matrix κ ι ℝ) (x : Ω → ι → ℝ) (hx : AEMeasurable x μ) :
    μ.map (fun ω => H *ᵥ x ω) = (μ.map x).map (fun v => H *ᵥ v)
theorem contrast_law (K : Transport n) (x : Ω → Idx n → ℝ) (hx : AEMeasurable x μ) :
    μ.map (fun ω => contrast K (x ω)) = (μ.map x).map (fun v => H K *ᵥ v)
theorem contrast_law_congr {Ω' : Type*} [MeasurableSpace Ω'] {ν : Measure Ω'}
    (K : Transport n) (x : Ω → Idx n → ℝ) (y : Ω' → Idx n → ℝ)
    (hx : AEMeasurable x μ) (hy : AEMeasurable y ν) (hlaw : μ.map x = ν.map y) :
    μ.map (fun ω => contrast K (x ω)) = ν.map (fun ω => contrast K (y ω))
theorem contrast_law_marginal_of_anchored (K : Transport n) (x : Ω → Idx n → ℝ)
    (hx : AEMeasurable x μ) :
    μ.map (fun ω => contrast K (x ω)) =
      (μ.map (fun ω => anchored K (x ω))).map (fun y => fun p : CIdx n => y ⟨p.1.succ, p.2⟩)
```

## Q5 — negative control: dropping cross blocks changes the covariance

Concrete depth 2, unit blocks `n₁ := fun _ : Fin 3 => 1`, `K₁ : Transport n₁ := fun _ => 1`,
`ones : Matrix (Idx n₁) (Idx n₁) ℝ := fun _ _ => 1` (three copies of one variable).
```lean
theorem ones_contrast_cov_zero : H K₁ * ones * (H K₁)ᵀ = 0
theorem blockDiag_contrast_cov_00 : (H K₁ * blockDiagPart ones * (H K₁)ᵀ) ⟨0, 0⟩ ⟨0, 0⟩ = 2
theorem blockDiag_contrast_cov_01 : (H K₁ * blockDiagPart ones * (H K₁)ᵀ) ⟨0, 0⟩ ⟨1, 0⟩ = -1
theorem dropping_cross_blocks_changes_cov :
    H K₁ * blockDiagPart ones * (H K₁)ᵀ ≠ H K₁ * ones * (H K₁)ᵀ
```
`blockDiag_contrast_cov_01` also records that block-independent inputs give correlated contrasts
(so contrast independence is never automatic).

Optional probabilistic form (Q5p, non-blocking): for any `Z : Ω → ℝ` with `MemLp Z 2 μ`, the
copy vector `x ω := fun _ => Z ω` has `covMat μ x = fun _ _ => Var[Z; μ]` and
`H K₁ * covMat μ x * (H K₁)ᵀ = 0`.

## Forbidden

`sorry`, `admit`, `sorryAx`, `native_decide`, new `axiom`, hypotheses equal to a conclusion, any
independence hypothesis. Accepted axioms: `propext`, `Classical.choice`, `Quot.sound`.
