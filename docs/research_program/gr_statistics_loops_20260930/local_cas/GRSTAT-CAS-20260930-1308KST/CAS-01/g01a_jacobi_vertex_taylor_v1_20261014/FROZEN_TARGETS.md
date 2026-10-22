# G01-A frozen Lean targets (frozen before any proof compile)

Frozen: 2026-10-14, before compile attempt 01. Module: `lean/G01AJacobiVertex.lean`,
namespace `G01A`. Imports exactly one reviewed module, unchanged:
`CAS07M05Accepted` (= CAS-07 `determinant_distance_bridge_v1_20261007/lean/Main.lean`),
which in turn imports the accepted oracle oleans `CAS07M01Accepted`,
`CAS07M04Accepted`, `CAS07C02Accepted`.

Abbreviations used below (all from the reused accepted modules):
`Plane := EuclideanSpace ℝ (Fin 2)`, `Op := Plane →L[ℝ] Plane` (Cas07M04),
`id₂ := ContinuousLinearMap.id ℝ Plane`, `matrixOf` (CAS07M05),
`dA(D) := Real.sqrt (Matrix.det (CAS07M05.matrixOf D))`.

## Interpretation boundary (binding)

* **Frame level only.** The objects below are the *recovered source definition*
  (FINITE_DISTANCE_THEOREM.md §Definitions; OPTICAL_THEOREMS.md §1 eq. (1) and the
  proof of (4)) stated in a fixed parallel orthonormal screen frame: an affine
  parameter interval `[0,L]`, `L>0`, and an optical tidal operator field
  `R : ℝ → Op`, continuous on `[0,L]`, with the segment bound `‖R t‖ ≤ K`.
  Nothing here constructs a Lorentzian manifold, a null geodesic, a screen
  bundle or parallel transport; the equivalence
  "Lorentzian geometry ⇒ this frame data" is **NOT_PROVED** (residual R1–R3).
* **Sign.** Frozen to FINITE_DISTANCE's `D'' = -Ropt D` (the `jacobi` field of
  `CAS07M05.JacobiPremises`). OPTICAL_THEOREMS writes `J'' = ℛ J`; the bridge is a
  *definition* `ℛ := -Ropt` (target T0), never an identification of symbols.
* **No symmetry assumed.** The optical tidal matrix is symmetric in the source;
  every theorem below holds for arbitrary (not necessarily symmetric) `R`, which is
  a weakening of hypotheses, not a strengthening.
* **Affine parameter.** The parameter `s` is the source's length-valued affine
  parameter with `o·K(0)=1`. The only reparametrisations treated are constant
  affine rescalings `s = c σ`, `c>0` (T9); no arbitrary parameter is substituted.

## Frozen signatures

```lean
-- recovered source definition (frame level)
structure ScreenFrameData (K L : ℝ) where
  R : ℝ → Op
  continuous_R : ContinuousOn R (Set.Icc 0 L)
  curvature_bound : ∀ t ∈ Set.Icc 0 L, ‖R t‖ ≤ K

-- T0 sign-notation bridge (definition ℛ := -Ropt)
theorem optical_sign_bridge (Ropt : ℝ → Op) (D2 D : Op) (t : ℝ) :
    D2 = (-(Ropt t)).comp D ↔ D2 = -(Ropt t).comp D

-- T1 first-order system ⇔ second-order Jacobi equation (on [0,L])
def jacobiField (R : ℝ → Op) (t : ℝ) (Y : Op × Op) : Op × Op := (Y.2, -(R t).comp Y.1)
theorem first_order_iff {L : ℝ} (R D D1 : ℝ → Op) :
    (∀ t ∈ Set.Icc 0 L, HasDerivWithinAt D (D1 t) (Set.Icc 0 L) t ∧
        HasDerivWithinAt D1 (-(R t).comp (D t)) (Set.Icc 0 L) t) ↔
      ∀ t ∈ Set.Icc 0 L,
        HasDerivWithinAt (fun u => (D u, D1 u)) (jacobiField R t (D t, D1 t)) (Set.Icc 0 L) t

-- T1b matrix ⇒ vector Jacobi fields (columns)
theorem column_jacobi_field {K L : ℝ} (J : CAS07M05.JacobiPremises K L) (v : Plane) :
    (J.D 0 v = 0 ∧ J.D1 0 v = v) ∧
    ∀ t ∈ Set.Icc 0 L, HasDerivWithinAt (fun u => J.D u v) (J.D1 t v) (Set.Icc 0 L) t ∧
      HasDerivWithinAt (fun u => J.D1 u v) (-(J.R t) (J.D t v)) (Set.Icc 0 L) t

-- T2 existence: frame data ↦ every field of CAS07M05.JacobiPremises (R unchanged)
theorem exists_jacobi {K L : ℝ} (F : ScreenFrameData K L) (hL : 0 < L) :
    ∃ J : CAS07M05.JacobiPremises K L, J.R = F.R

-- T3 uniqueness on [0,L]
theorem jacobi_unique {K L : ℝ} (J₁ J₂ : CAS07M05.JacobiPremises K L)
    (hR : ∀ t ∈ Set.Icc 0 L, J₁.R t = J₂.R t) :
    ∀ t ∈ Set.Icc 0 L, J₁.D t = J₂.D t ∧ J₁.D1 t = J₂.D1 t ∧ J₁.D2 t = J₂.D2 t

-- T4 vertex jet derived from the ODE (no quadratic term)
theorem vertex_jet {K L : ℝ} (J : CAS07M05.JacobiPremises K L) (hL : 0 ≤ L) :
    J.D 0 = 0 ∧ J.D1 0 = id₂ ∧ J.D2 0 = 0

-- T5 exact integral remainder (Volterra form, reused from accepted M04)
theorem integral_remainder {K L : ℝ} (J : CAS07M05.JacobiPremises K L) :
    ∀ s ∈ Set.Icc 0 L, J.D s = s • id₂ - ∫ t in (0:ℝ)..s, (s - t) • (J.R t).comp (J.D t)

-- T6 required Taylor order: D(s) = s I + O(s^3), explicit cubic constant
theorem cubic_bound {K L : ℝ} (J : CAS07M05.JacobiPremises K L) (hK : 0 ≤ K) :
    ∃ C : ℝ, 0 ≤ C ∧ ∀ s ∈ Set.Icc 0 L, ‖J.D s - s • id₂‖ ≤ C * s ^ 3

-- T7 cubic vertex coefficient with exact integral remainder and o(s^3) bound
theorem cubic_jet_identity {K L : ℝ} (J : CAS07M05.JacobiPremises K L) :
    ∀ s ∈ Set.Icc 0 L, J.D s - s • id₂ + (s ^ 3 / 6) • J.R 0 =
      -∫ t in (0:ℝ)..s, (s - t) • ((J.R t).comp (J.D t) - t • J.R 0)
theorem cubic_jet {K L : ℝ} (J : CAS07M05.JacobiPremises K L) (hK : 0 ≤ K) (hL : 0 < L) :
    ∀ ε > 0, ∃ δ > 0, ∀ s ∈ Set.Icc 0 L, s < δ →
      ‖J.D s - s • id₂ + (s ^ 3 / 6) • J.R 0‖ ≤ ε * s ^ 3

-- T8 area distance vertex order on the positive branch: dA(s) = s + O(s^3), det>0 derived
theorem area_distance_vertex {K L : ℝ} (J : CAS07M05.JacobiPremises K L) (hK : 0 ≤ K) :
    ∃ C : ℝ, 0 ≤ C ∧ ∃ δ > 0, ∀ s, 0 < s → s ≤ L → s < δ →
      0 < Matrix.det (CAS07M05.matrixOf (J.D s)) ∧
      |Real.sqrt (Matrix.det (CAS07M05.matrixOf (J.D s))) - s| ≤ C * s ^ 3

-- T9 screen transition (constant O ∈ O(2) between two parallel orthonormal frames)
def conj (O : Plane ≃ₗᵢ[ℝ] Plane) (A : Op) : Op
  -- := (O : Op) ∘ A ∘ (O.symm : Op)
def JacobiPremises.rotate {K L} (O) (J : CAS07M05.JacobiPremises K L) : CAS07M05.JacobiPremises K L
  -- fields D,D1,D2,R all conjugated by O
theorem det_conj (O : Plane ≃ₗᵢ[ℝ] Plane) (A : Op) :
    Matrix.det (CAS07M05.matrixOf (conj O A)) = Matrix.det (CAS07M05.matrixOf A)
theorem screen_transition {K L : ℝ} (O : Plane ≃ₗᵢ[ℝ] Plane)
    (J J' : CAS07M05.JacobiPremises K L)
    (hR : ∀ t ∈ Set.Icc 0 L, J'.R t = conj O (J.R t)) :
    ∀ t ∈ Set.Icc 0 L, J'.D t = conj O (J.D t) ∧
      Real.sqrt (Matrix.det (CAS07M05.matrixOf (J'.D t))) =
        Real.sqrt (Matrix.det (CAS07M05.matrixOf (J.D t)))

-- T10 affine rescaling s = c σ (separate normalization theorem)
def JacobiPremises.rescale {K L} (c : ℝ) (hc : 0 < c) (J : CAS07M05.JacobiPremises K L) :
    CAS07M05.JacobiPremises (c ^ 2 * K) (L / c)
  -- D' σ = c⁻¹ • D (c σ), D1' σ = D1 (c σ), D2' σ = c • D2 (c σ), R' σ = c^2 • R (c σ)
theorem rescale_area_distance {K L c : ℝ} (hc : 0 < c) (J : CAS07M05.JacobiPremises K L) (σ : ℝ) :
    Real.sqrt (Matrix.det (CAS07M05.matrixOf ((J.rescale c hc).D σ))) =
      Real.sqrt (Matrix.det (CAS07M05.matrixOf (J.D (c * σ)))) / c
theorem eta_rescale_invariant {K L c : ℝ} (hK : 0 ≤ K) (hc : 0 < c) :
    CAS07M01.eta (c ^ 2 * K) (L / c) = CAS07M01.eta K L

-- T11 observer normalization fixes the affine scale (tangent-space algebra at p)
theorem observer_normalization {V : Type*} [AddCommGroup V] [Module ℝ V]
    (B : LinearMap.BilinForm ℝ V) (hB : B.IsSymm) (o n : V)
    (hoo : B o o = -1) (hnn : B n n = 1) (hon : B o n = 0) :
    B (-o + n) (-o + n) = 0 ∧ B o (-o + n) = 1 ∧ ∀ c : ℝ, B o (c • (-o + n)) = 1 ↔ c = 1

-- T12 mapping theorem: frame data + separate hypotheses ⇒ CAS07M05 determinant-distance bridge
theorem frame_determinant_distance {K L s : ℝ} (F : ScreenFrameData K L)
    (hK : 0 ≤ K) (hL : 0 < L) (hs : 0 < s) (hsL : s ≤ L) (hEtaL : CAS07M01.eta K L < 1) :
    ∃ J : CAS07M05.JacobiPremises K L, J.R = F.R ∧
      0 < Matrix.det (CAS07M05.matrixOf (J.D s)) ∧
      s * (1 - CAS07M01.eta K s) ≤ Real.sqrt (Matrix.det (CAS07M05.matrixOf (J.D s))) ∧
      Real.sqrt (Matrix.det (CAS07M05.matrixOf (J.D s))) ≤ s * (1 + CAS07M01.eta K s)

-- Non-vacuity witness and negative control
def flatJacobi (L : ℝ) : CAS07M05.JacobiPremises 0 L   -- R = 0, D s = s • id₂
theorem flatJacobi_D (L s : ℝ) : (flatJacobi L).D s = s • id₂
theorem negative_control {K L : ℝ} (J : CAS07M05.JacobiPremises K L) (hK : 0 ≤ K) (hL : 0 < L)
    (hflat : ∀ s ∈ Set.Icc 0 L, J.D s = s • id₂) : J.R 0 = 0
```

Exact field-by-field map in T2: `D := (α ·).1`, `D1 := (α ·).2`,
`D2 t := -(R t) ∘ D t`, `R := F.R` (unchanged), where `α` solves the first-order
system `Y' = jacobiField R̃ t Y`, `Y(0) = (0, id₂)` on `[0,L]`, and `R̃` is the
clamp extension of `F.R` (equal to `F.R` on `[0,L]`). `deriv_D`, `deriv_D1`,
`continuous_D2`, `continuous_R`, `D_zero`, `D1_zero`, `jacobi`,
`curvature_bound` are each discharged in the proof; none is assumed.
T12's hypotheses `0 ≤ K`, `0 < L`, `0 < s ≤ L`, `eta K L < 1` are exactly the
separate hypotheses of `CAS07M05.determinant_distance_bridge`; its conclusion is
not assumed.

## Not targeted (residuals, NOT_PROVED)

* R1: Lorentzian manifold / Levi-Civita connection / Riemann sign, and the
  definition `Ropt_ab = R_{a K K b}` in a screen frame (Mathlib has no
  pseudo-Riemannian curvature API).
* R2: existence of the affine null geodesic `γ` with `γ'(0) = -o+n`, the screen
  bundle, and parallel transport of the orthonormal screen frame; equivalence of
  the geometric Jacobi (geodesic-deviation) field with the matrix solution of T2.
* R3: the source-level screen-representative change "by multiples of K"
  (quotient screen); T9 covers only the frame-level change between two parallel
  orthonormal frames, which is a constant O ∈ O(2) *by the (unproved) property
  that parallel transport preserves orthonormality*.
* Scientific admission: HOLD.
