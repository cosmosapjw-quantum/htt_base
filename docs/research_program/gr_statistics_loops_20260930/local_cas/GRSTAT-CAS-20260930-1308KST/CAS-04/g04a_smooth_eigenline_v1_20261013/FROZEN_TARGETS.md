# G04-A frozen targets (frozen 2026-10-13T11:22Z, before any proof attempt)

Package task: G04-A (GR-CAS-04) "connect the rest-basis budget to a smooth energy eigenline".
Author lane: single Lean coding author (claude-opus-5-5). Status of this file: FROZEN.
Any later change to a statement below must be recorded in the "Amendments" section with reason;
the final Lean file must contain these statements verbatim (up to `:= by <proof>`).

## Source recovery (what the source states, and the choices made)

* `gr/ENERGYFRAME_THEOREMS.md` (sha256 dd66030a…6855) EF1: "Let T^a_b be a C^1, g-self-adjoint stress
  endomorphism with a normalized future timelike eigenvector field u: Tu = -εu. Write S = hT|_{u⊥},
  L = S + εI, and assume L is invertible. ... δ = min_i |ε + p_i| > 0 where p_i are the spatial
  eigenvalues." Line 91 (EF2 neighbourhood assertion): "An isolated timelike eigenline depends smoothly
  on a smooth g-self-adjoint endomorphism near a point where L is invertible; this also follows directly
  from the normalized eigenvector equation and the implicit function theorem, whose spatial linearization
  is L. Timelikeness persists." Conventions §0: signature (-,+,+,+), u = U/c, g(u,u) = -1,
  h = δ + u⊗u, future orthonormal frame E_0 = u, E_i; positive Euclidean rest norms.
* `cas/contracts/CAS-04.json` (sha256 139c4b5b…0895) assumptions: "T u=-epsilon u, smooth selected future
  eigenline; rest L=S_T+epsilon I invertible"; "delta=min|epsilon+p_i|>0".
* Accepted scoped Lean `completion_20261003/lean/Proof.lean` (sha256 8a870e4e…8144, namespace
  GRSTATCAS04) is imported UNCHANGED (compiled to raw/imports/Proof.olean). Its statements used here:
  C01 `projected_eigen_derivative` (path hypotheses hEig/hn for ALL s : ℝ), C02
  `weighted_rate_from_eigenbasis` (premise `hproj : ∀ μ i, gap i * q μ i = -c * d μ i`),
  C03 `physical_gap_bound_and_equality`, C04 `euler_from_actual_conservation` (path hypotheses for all s).

Recorded modelling choices (scope, not hidden assumptions):
1. Metric: flat Minkowski η = diag(-1,1,1,1) in global inertial coordinates x ∈ ℝ⁴ (`Vec4`), exactly the
   `eta`/`lorentzDot` of Proof.lean. Covariant derivative = coordinate derivative (`fderiv`). A general
   C^k Lorentzian metric with connection terms is NOT covered (recorded as not claimed).
2. Regularity: T : Vec4 → Mat4 (mixed components T^a_b, acting by `matVec`) is C^n on an open set S,
   n : ℕ finite, 1 ≤ n ("C^k" with finite k ≥ 1; C^∞/analytic not claimed).
3. g-self-adjointness: `EtaSelfAdjoint t := ∀ a b, eta a * t a b = eta b * t b a` (T_ab symmetric).
4. Simplicity / spectral separation at the base point, literally the source's "L = S_T + εI invertible on
   the rest space": `RestGapInjective t u ε := ∀ w, η(u,w)=0 → h(T w) + ε w = 0 → w = 0`
   (finite-dimensional: injective ⇔ invertible). E0 proves it is equivalent to "all ε + p_i ≠ 0" for any
   orthonormal rest eigenbasis (the source's eigenvalue form).
5. Future: `0 < u 0` (time component of the unit timelike vector).
6. Path-hypothesis mismatch with Proof.lean: C01/C04 there require the eigen/normalization hypotheses
   along a path for ALL s ∈ ℝ, while a local eigenfield exists only on V. Bridge: bounded paths
   s ↦ x + (r sin s)•X that stay in V for all s, then rescale by r (no change to Proof.lean).

## Frozen Lean definitions and statements (namespace G04A; `open GRSTATCAS04`)

```lean
def EtaSelfAdjoint (t : Mat4) : Prop := ∀ a b : Fin 4, eta a * t a b = eta b * t b a

def RestGapInjective (t : Mat4) (u : Vec4) (ε : ℝ) : Prop :=
  ∀ w : Vec4, lorentzDot u w = 0 → restProj u (matVec t w) + ε • w = 0 → w = 0

def FutureUnitEigen (t : Mat4) (u : Vec4) (ε : ℝ) : Prop :=
  matVec t u = (-ε) • u ∧ lorentzDot u u = -1 ∧ 0 < u 0

def RestEigenbasis (t : Mat4) (u : Vec4) (e : Fin 3 → Vec4) (p : Fin 3 → ℝ) : Prop :=
  (∀ i j, lorentzDot (e i) (e j) = if i = j then 1 else 0) ∧
  (∀ i, lorentzDot u (e i) = 0) ∧ (∀ i, matVec t (e i) = p i • e i)

structure SmoothEnergyFrame (n : ℕ) (T : Vec4 → Mat4) (V : Set Vec4)
    (u : Vec4 → Vec4) (ε : Vec4 → ℝ) : Prop where
  isOpen : IsOpen V
  smooth_T : ContDiffOn ℝ n T V
  smooth_u : ContDiffOn ℝ n u V
  smooth_ε : ContDiffOn ℝ n ε V
  selfAdj : ∀ x ∈ V, EtaSelfAdjoint (T x)
  eigen : ∀ x ∈ V, FutureUnitEigen (T x) (u x) (ε x)
  gap : ∀ x ∈ V, RestGapInjective (T x) (u x) (ε x)

def frameVec (u : Vec4) (e : Fin 3 → Vec4) : Fin 4 → Vec4 := Fin.cons u e

noncomputable def rateArr (c : ℝ) (u : Vec4 → Vec4) (x : Vec4) (e : Fin 3 → Vec4) : Arr :=
  fun μ i => lorentzDot (e i) (c • fderiv ℝ u x (frameVec (u x) e μ))

noncomputable def sourceArr (T : Vec4 → Mat4) (u : Vec4 → Vec4) (x : Vec4)
    (e : Fin 3 → Vec4) : Arr :=
  fun μ i => lorentzDot (e i) (restProj (u x) (matVec (fderiv ℝ T x (frameVec (u x) e μ)) (u x)))

noncomputable def rateBudget (c : ℝ) (q : Arr) : ℝ :=
  (theta q)^2 / 3 + (∑ i : Fin 3, ∑ j : Fin 3, (sigma q i j)^2) +
    2 * (∑ i : Fin 3, (omega q i)^2) + (∑ i : Fin 3, (accel c q i)^2) / c^2

noncomputable def minGap (ε : ℝ) (p : Fin 3 → ℝ) : ℝ :=
  Finset.univ.inf' Finset.univ_nonempty (fun i => |ε + p i|)

def fluidMixed (e p : ℝ) (w : Vec4) : Mat4 :=
  fun a b => (e + p) * w a * (eta b * w b) + (if a = b then p else 0)

def coordVec (a : Fin 4) : Vec4 := Pi.single a 1

theorem E0_gap_iff_eigenvalues (t : Mat4) (u : Vec4) (ε : ℝ) (e : Fin 3 → Vec4)
    (p : Fin 3 → ℝ) (hn : lorentzDot u u = -1) (hB : RestEigenbasis t u e p) :
    RestGapInjective t u ε ↔ ∀ i, ε + p i ≠ 0 := by <proof>

theorem E1u_unique (t : Mat4) (u v : Vec4) (ε μ : ℝ) (hsym : EtaSelfAdjoint t)
    (hu : FutureUnitEigen t u ε) (hgap : RestGapInjective t u ε)
    (hv : FutureUnitEigen t v μ) : v = u ∧ μ = ε := by <proof>

theorem E1_smooth_eigenline (n : ℕ) (hn : 1 ≤ n) (S : Set Vec4) (hS : IsOpen S)
    (T : Vec4 → Mat4) (hT : ContDiffOn ℝ n T S) (hsym : ∀ x ∈ S, EtaSelfAdjoint (T x))
    (x0 : Vec4) (hx0 : x0 ∈ S) (u0 : Vec4) (ε0 : ℝ)
    (h0 : FutureUnitEigen (T x0) u0 ε0) (hgap0 : RestGapInjective (T x0) u0 ε0) :
    ∃ (V : Set Vec4) (u : Vec4 → Vec4) (ε : Vec4 → ℝ),
      x0 ∈ V ∧ V ⊆ S ∧ u x0 = u0 ∧ ε x0 = ε0 ∧ SmoothEnergyFrame n T V u ε := by <proof>

theorem E2_directional_C01 {n : ℕ} (hn : 1 ≤ n) {T : Vec4 → Mat4} {V : Set Vec4}
    {u : Vec4 → Vec4} {ε : Vec4 → ℝ} (hF : SmoothEnergyFrame n T V u ε)
    (c : ℝ) (hc : 0 < c) (x : Vec4) (hx : x ∈ V) (X : Vec4) :
    restProj (u x) (matVec (T x) (c • fderiv ℝ u x X)) + ε x • (c • fderiv ℝ u x X) =
      (-c) • restProj (u x) (matVec (fderiv ℝ T x X) (u x)) := by <proof>

theorem E2_path_C01 {n : ℕ} (hn : 1 ≤ n) {T : Vec4 → Mat4} {V : Set Vec4}
    {u : Vec4 → Vec4} {ε : Vec4 → ℝ} (hF : SmoothEnergyFrame n T V u ε)
    (c : ℝ) (hc : 0 < c) (γ : ℝ → Vec4) (s0 : ℝ) (X : Vec4) (hγ : HasDerivAt γ X s0)
    (hγV : γ s0 ∈ V) (du : Vec4) (dt : Mat4)
    (hdu : HasDerivAt (fun s => u (γ s)) du s0) (hdt : HasDerivAt (fun s => T (γ s)) dt s0) :
    restProj (u (γ s0)) (matVec (T (γ s0)) (c • du)) + ε (γ s0) • (c • du) =
      (-c) • restProj (u (γ s0)) (matVec dt (u (γ s0))) := by <proof>

theorem E3_restbasis_exists (t : Mat4) (u : Vec4) (ε : ℝ) (hsym : EtaSelfAdjoint t)
    (hu : FutureUnitEigen t u ε) : ∃ (e : Fin 3 → Vec4) (p : Fin 3 → ℝ), RestEigenbasis t u e p := by <proof>

theorem E3_hproj {n : ℕ} (hn : 1 ≤ n) {T : Vec4 → Mat4} {V : Set Vec4}
    {u : Vec4 → Vec4} {ε : Vec4 → ℝ} (hF : SmoothEnergyFrame n T V u ε)
    (c : ℝ) (hc : 0 < c) (x : Vec4) (hx : x ∈ V) (e : Fin 3 → Vec4) (p : Fin 3 → ℝ)
    (hB : RestEigenbasis (T x) (u x) e p) :
    (∀ i, ε x + p i ≠ 0) ∧
    ∀ μ i, (fun j => ε x + p j) i * rateArr c u x e μ i = -c * sourceArr T u x e μ i := by <proof>

theorem E3_weighted_rate {n : ℕ} (hn : 1 ≤ n) {T : Vec4 → Mat4} {V : Set Vec4}
    {u : Vec4 → Vec4} {ε : Vec4 → ℝ} (hF : SmoothEnergyFrame n T V u ε)
    (c : ℝ) (hc : 0 < c) (x : Vec4) (hx : x ∈ V) :
    ∃ (e : Fin 3 → Vec4) (p : Fin 3 → ℝ), RestEigenbasis (T x) (u x) e p ∧
      (∀ i, ε x + p i ≠ 0) ∧
      (∀ μ i, (ε x + p i) * rateArr c u x e μ i = -c * sourceArr T u x e μ i) ∧
      rateBudget c (rateArr c u x e) =
        c^2 * (∑ μ : Fin 4, ∑ i : Fin 3, (sourceArr T u x e μ i)^2 / (ε x + p i)^2) := by <proof>

theorem E4_gap_budget {n : ℕ} (hn : 1 ≤ n) {T : Vec4 → Mat4} {V : Set Vec4}
    {u : Vec4 → Vec4} {ε : Vec4 → ℝ} (hF : SmoothEnergyFrame n T V u ε)
    (c : ℝ) (hc : 0 < c) (x : Vec4) (hx : x ∈ V) (e : Fin 3 → Vec4) (p : Fin 3 → ℝ)
    (hB : RestEigenbasis (T x) (u x) e p) :
    0 < minGap (ε x) p ∧
    rateBudget c (rateArr c u x e) =
      c^2 * (∑ μ : Fin 4, ∑ i : Fin 3, (sourceArr T u x e μ i)^2 / (ε x + p i)^2) ∧
    rateBudget c (rateArr c u x e) ≤
      c^2 * (∑ μ : Fin 4, ∑ i : Fin 3, (sourceArr T u x e μ i)^2 / (minGap (ε x) p)^2) ∧
    (rateBudget c (rateArr c u x e) =
      c^2 * (∑ μ : Fin 4, ∑ i : Fin 3, (sourceArr T u x e μ i)^2 / (minGap (ε x) p)^2) ↔
      ∀ μ i, sourceArr T u x e μ i = 0 ∨ |ε x + p i| = minGap (ε x) p) := by <proof>

theorem E4_euler_actual {n : ℕ} (hn : 1 ≤ n) {T : Vec4 → Mat4} {V : Set Vec4}
    {u : Vec4 → Vec4} {ε : Vec4 → ℝ} (hF : SmoothEnergyFrame n T V u ε)
    (eF pF : Vec4 → ℝ) (w : Vec4 → Vec4)
    (hfluid : ∀ y ∈ V, T y = fluidMixed (eF y) (pF y) (w y))
    (hw : ∀ y ∈ V, lorentzDot (w y) (w y) = -1 ∧ 0 < w y 0)
    (x : Vec4) (hx : x ∈ V) (hpd : DifferentiableAt ℝ pF x)
    (hcons : ∀ b, ∑ a : Fin 4, fderiv ℝ (fun y => T y a b * eta b) x (coordVec a) = 0)
    (c : ℝ) (hc : 0 < c) :
    (∀ y ∈ V, w y = u y ∧ eF y = ε y) ∧ ε x + pF x ≠ 0 ∧
    c^2 • accJet (u x) (fun a => fderiv ℝ u x (coordVec a)) =
      (-c^2 / (ε x + pF x)) • restProj (u x) (raiseGrad (fun a => fderiv ℝ pF x (coordVec a))) :=
  by <proof>

end G04A
```

## Target map
* E0 `E0_gap_iff_eigenvalues`: source's two forms of the spectral separation agree.
* E1 `E1_smooth_eigenline` (+ `E1u_unique`): IFT on the bordered system (v, μ) ↦ (T v − μ v, η(v,v)+1)
  at (u0, −ε0); C^n normalized future eigenfield with u x0 = u0 on an open V, and L invertible persists
  on V; pointwise uniqueness of the future unit timelike eigenvector wherever L is invertible.
  `SmoothEnergyFrame` is only a bundle of E1's conclusions (E1 proves it; it is not an extra premise).
* E2 `E2_directional_C01`, `E2_path_C01`: the actual field's derivative obeys Proof.lean's C01 formula;
  proof must invoke `GRSTATCAS04.projected_eigen_derivative`.
* E3 `E3_restbasis_exists` (pointwise rest inner product/orthonormal eigenbasis via boost frame +
  real symmetric 3×3 spectral theorem), `E3_hproj` (Proof.lean's C02 premise hproj DERIVED with
  gap i = ε x + p i, q = rateArr, d = sourceArr), `E3_weighted_rate` (C02 conclusion at the actual field
  via `GRSTATCAS04.weighted_rate_from_eigenbasis`).
* E4 `E4_gap_budget` (C03 at the actual fields, δ = min_i |ε + p_i|, equality support preserved, via
  `GRSTATCAS04.physical_gap_bound_and_equality`), `E4_euler_actual` (C04 at the actual fields for a
  conserved perfect-fluid T, via `GRSTATCAS04.euler_from_actual_conservation`; the fluid velocity is
  proved to be the selected eigenfield by E1u, and ε + p ≠ 0 is derived from the gap).

## Forbidden
sorry/admit/sorryAx/native_decide/new axioms; assuming hproj, the eigenfield's existence or smoothness,
or any conclusion. Accepted axioms: propext, Classical.choice, Quot.sound.

## Amendments
(none at freeze time)
