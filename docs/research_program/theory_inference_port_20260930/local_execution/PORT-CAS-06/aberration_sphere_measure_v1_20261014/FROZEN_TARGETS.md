# P06-A additive closeout — frozen targets (aberration on the S² surface measure)

Frozen at 2026-10-14T02:55Z (UTC), before any compile of this unit (no `raw/compile_*`
receipt exists at freeze time).  Card: `tasks/P06-A.json`, lean_step 2 ("aberration의
sphere Jacobian과 source area/observer solid-angle 정의를 연결한다"), acceptance 2
("z=0·β=0 등 경계에서 결과 유지").  This unit is ADDITIVE to the reviewed unit
`../endpoint_optical_invariants_v1_20261014` (P06AOptics, PASS_WITH_NOTES), whose review
note 1 and controller addendum leave open exactly: "the pushforward of the S² surface
measure (`Measure.toSphere`) under `aberr` has density D⁻²".

## Context (imports and opens; module `P06ASphere`, file `lean/P06ASphere.lean`)

```lean
import Mathlib
import PortCas01
import PassiveTensorBridge
import EndpointScalarInvariant
import P06AOptics          -- reviewed, imported UNCHANGED (sha256 732fbbfd…)

open MeasureTheory Metric Set PortCas01 P06AOptics
open scoped RealInnerProductSpace ENNReal
open PORTCAS06EndpointScalarInvariant (zNew dANew endpoint_product_invariant)

namespace P06ASphere
```

`s`, `gamma`, `h`, `fourVelocity`, `e0` are PortCas01's; `doppler`, `aberr`, `photon`,
`energy`, `newComp`, `dirOf`, `areaDist`, `redshiftOf` are P06AOptics's (unchanged).

## Frozen definitions

```lean
abbrev E3 := EuclideanSpace ℝ (Fin 3)
abbrev S2 := sphere (0 : E3) 1

/-- Mathlib's surface measure on the unit sphere (same expression as the reviewed
    G15-B `σS`, CAS-15 g15b `lean/G15BSphere.lean:40`; not imported). -/
noncomputable def σS : Measure S2 := (volume : Measure E3).toSphere

noncomputable def bvec (b1 b2 b3 : ℝ) : E3 := !₂[b1, b2, b3]

/-- Doppler factor `D(n) = γ(1+β·n)` of the ray with old sourceward direction `n`. -/
noncomputable def dopS (b1 b2 b3 : ℝ) (n : E3) : ℝ := doppler b1 b2 b3 (n 0) (n 1) (n 2)

/-- The P06AOptics closed-form aberration, as a vector of `E3`. -/
noncomputable def aberrV (b1 b2 b3 : ℝ) (n : E3) : E3 :=
  !₂[aberr b1 b2 b3 (n 0) (n 1) (n 2) 0, aberr b1 b2 b3 (n 0) (n 1) (n 2) 1,
    aberr b1 b2 b3 (n 0) (n 1) (n 2) 2]

theorem aberrV_mem_sphere {b1 b2 b3 : ℝ} (hb : s b1 b2 b3 < 1) (n : S2) :
    aberrV b1 b2 b3 n ∈ S2

/-- Aberration restricted to the unit sphere: `S² → S²`. -/
noncomputable def aberrS {b1 b2 b3 : ℝ} (hb : s b1 b2 b3 < 1) (n : S2) : S2 :=
  ⟨aberrV b1 b2 b3 n, aberrV_mem_sphere hb n⟩

/-- Density `D(n)⁻²`. -/
noncomputable def dens (b1 b2 b3 : ℝ) (n : S2) : ℝ≥0∞ :=
  ENNReal.ofReal ((dopS b1 b2 b3 n ^ 2)⁻¹)

/-- New-frame solid-angle measure, pulled back to old directions:
    `solidAngleNew hb A = σS (aberrS hb '' A)` (proved, F6). -/
noncomputable def solidAngleNew {b1 b2 b3 : ℝ} (hb : s b1 b2 b3 < 1) : Measure S2 :=
  Measure.comap (aberrS hb) σS

/-- Light-cone lift of the aberration to `E3` (spatial part of the boosted null
    vector, homogeneous of degree one): used for the 3-D change of variables. -/
noncomputable def coneMap (b1 b2 b3 : ℝ) (x : E3) : E3 :=
  x + (gamma b1 b2 b3 * ‖x‖ + h b1 b2 b3 * ⟪bvec b1 b2 b3, x⟫) • bvec b1 b2 b3

/-- Its derivative at `x ≠ 0` (an explicit formula; F3 proves it is the derivative). -/
noncomputable def coneDeriv (b1 b2 b3 : ℝ) (x : E3) : E3 →L[ℝ] E3 :=
  ContinuousLinearMap.id ℝ E3 +
    (gamma b1 b2 b3 • (‖x‖⁻¹ • innerSL ℝ x) + h b1 b2 b3 • innerSL ℝ (bvec b1 b2 b3)).smulRight
      (bvec b1 b2 b3)
```

## Frozen theorem statements

F1 — same physical ray (the sphere map is the new-frame direction of the same null `k`):
```lean
theorem aberrS_same_ray {b1 b2 b3 : ℝ} (hb : s b1 b2 b3 < 1) (n : S2) {E : ℝ} (hE : 0 < E)
    (i : Fin 3) :
    (aberrS hb n : E3) i =
      dirOf (newComp b1 b2 b3 (photon E ((n : E3) 0) ((n : E3) 1) ((n : E3) 2))) i
```

F2 — the sphere map is a continuous bijection of S²:
```lean
theorem aberrS_bijective {b1 b2 b3 : ℝ} (hb : s b1 b2 b3 < 1) :
    Function.Bijective (aberrS hb) ∧ Continuous (aberrS hb)
```

F3 — derived Jacobian of the light-cone lift (no formula postulated: `coneDeriv` is shown
to be the Fréchet derivative and its determinant is computed):
```lean
theorem coneMap_jacobian {b1 b2 b3 : ℝ} (hb : s b1 b2 b3 < 1) {x : E3} (hx : x ≠ 0) :
    HasFDerivAt (coneMap b1 b2 b3) (coneDeriv b1 b2 b3 x) x ∧
      (coneDeriv b1 b2 b3 x).det = dopS b1 b2 b3 (‖x‖⁻¹ • x)

theorem coneMap_ray {b1 b2 b3 : ℝ} (hb : s b1 b2 b3 < 1) (n : S2) {r : ℝ} (hr : 0 ≤ r) :
    coneMap b1 b2 b3 (r • (n : E3)) = (r * dopS b1 b2 b3 n) • (aberrS hb n : E3)
```

F4 — MAIN (card lean_step 2 on the actual sphere measure): pushforward of
`D⁻² · σS` under the aberration is `σS`, for every `|β| < 1` (β = 0 included):
```lean
theorem aberr_pushforward {b1 b2 b3 : ℝ} (hb : s b1 b2 b3 < 1) :
    Measure.map (aberrS hb) (σS.withDensity (dens b1 b2 b3)) = σS
```

F5 — integral form for every continuous `g`:
```lean
theorem aberr_integral {b1 b2 b3 : ℝ} (hb : s b1 b2 b3 < 1) {g : S2 → ℝ} (hg : Continuous g) :
    ∫ n, g (aberrS hb n) * (dopS b1 b2 b3 n ^ 2)⁻¹ ∂σS = ∫ n, g n ∂σS
```

F6 — new-frame solid angle of the same bundle of rays: density `D⁻²` w.r.t. `σS`:
```lean
theorem solidAngleNew_eq {b1 b2 b3 : ℝ} (hb : s b1 b2 b3 < 1) :
    solidAngleNew hb = σS.withDensity (dens b1 b2 b3) ∧
      ∀ A : Set S2, MeasurableSet A →
        solidAngleNew hb A = σS (aberrS hb '' A) ∧
          σS (aberrS hb '' A) = ∫⁻ n in A, dens b1 b2 b3 n ∂σS
```

F7 — area distance with the SAME source area `dS`, new solid angle element given by the
Radon–Nikodym density of the actual measures:
```lean
theorem areaDist_sphere {b1 b2 b3 : ℝ} (hb : s b1 b2 b3 < 1) (dS dΩ : ℝ) :
    ∀ᵐ n ∂σS, areaDist dS (((solidAngleNew hb).rnDeriv σS n).toReal * dΩ) =
      dANew (areaDist dS dΩ) (dopS b1 b2 b3 n)
```

F8 — same-ray composite on the sphere measure, no `β ≠ 0` hypothesis:
```lean
theorem endpoint_optical_sphere {b1 b2 b3 : ℝ} (hb : s b1 b2 b3 < 1) {E Es dS dΩ : ℝ}
    (hE : 0 < E) :
    ∀ᵐ n ∂σS,
      redshiftOf Es (energy (fourVelocity b1 b2 b3)
          (photon E ((n : E3) 0) ((n : E3) 1) ((n : E3) 2))) =
        zNew (redshiftOf Es (energy e0 (photon E ((n : E3) 0) ((n : E3) 1) ((n : E3) 2))))
          (dopS b1 b2 b3 n) ∧
      areaDist dS (((solidAngleNew hb).rnDeriv σS n).toReal * dΩ) =
        dANew (areaDist dS dΩ) (dopS b1 b2 b3 n) ∧
      (1 + redshiftOf Es (energy (fourVelocity b1 b2 b3)
          (photon E ((n : E3) 0) ((n : E3) 1) ((n : E3) 2)))) *
          areaDist dS (((solidAngleNew hb).rnDeriv σS n).toReal * dΩ) =
        (1 + redshiftOf Es (energy e0 (photon E ((n : E3) 0) ((n : E3) 1) ((n : E3) 2)))) *
          areaDist dS dΩ
```

F9 — β = 0 composite as a corollary (acceptance 2):
```lean
theorem beta_zero_admissible : s 0 0 0 < 1

theorem endpoint_optical_sphere_beta_zero {E Es dS dΩ : ℝ} (hE : 0 < E) :
    (∀ n : S2, aberrS beta_zero_admissible n = n) ∧
      solidAngleNew beta_zero_admissible = σS ∧
      ∀ᵐ n ∂σS,
        redshiftOf Es (energy (fourVelocity 0 0 0)
            (photon E ((n : E3) 0) ((n : E3) 1) ((n : E3) 2))) =
          redshiftOf Es (energy e0 (photon E ((n : E3) 0) ((n : E3) 1) ((n : E3) 2))) ∧
        areaDist dS (((solidAngleNew beta_zero_admissible).rnDeriv σS n).toReal * dΩ) =
          areaDist dS dΩ ∧
        (1 + redshiftOf Es (energy (fourVelocity 0 0 0)
            (photon E ((n : E3) 0) ((n : E3) 1) ((n : E3) 2)))) *
            areaDist dS (((solidAngleNew beta_zero_admissible).rnDeriv σS n).toReal * dΩ) =
          (1 + redshiftOf Es (energy e0 (photon E ((n : E3) 0) ((n : E3) 1) ((n : E3) 2)))) *
            areaDist dS dΩ
```

F10 — negative control and non-vacuity: without the density the pushforward is NOT the
sphere measure (β = (0,0,3/5)), and the sphere measure is nonzero:
```lean
theorem witness_admissible : s 0 0 (3 / 5) < 1

theorem pushforward_without_density_ne :
    Measure.map (aberrS witness_admissible) σS ≠ σS ∧ σS ≠ 0
```

## Route (planned; helper lemmas are not frozen)

Light-cone lift `coneMap` (degree-one homogeneous, `coneMap (r n) = (r D(n)) aberr(n)`),
explicit inverse `coneMap(-β)`, derivative `id + ℓ ⊗ β` with `det = 1 + ℓ(β) = D(x̂)`
(3×3 determinant, `hS = γ-1`), Mathlib change of variables
`lintegral_image_eq_lintegral_abs_det_fderiv_mul` on `{0}ᶜ`, and Mathlib's polar
decomposition `measurePreserving_homeomorphUnitSphereProd`
(`volume ↦ toSphere ⊗ r² dr`) with `volumeIoiPow_apply_Iio`, applied to the indicator
of the unit cone over `A`.  The radial integral gives `D⁻³/3`, the Jacobian `D`, so
`σS A / 3 = (1/3) ∫_{aberr⁻¹A} D⁻²`.  No rotation reduction, no polar chart and no
`dΩ = dμ dφ` convention is used (so `dΩ = dμ dφ` is NOT proved here and not claimed).

## Honest scope limits (fixed at freeze time)

* Reciprocity, transparency, Planck occupation invariance: untouched (prior unit,
  hypotheses only).  No `dL` statement is added here.
* F7/F8 are σS-almost-everywhere statements (Radon–Nikodym densities are a.e. objects);
  the identity `σS (aberrS '' A) = ∫_A D⁻²` (F6) holds for every measurable `A`.
* Scalar, flat-space, single-event observer change only; no polarization / spin-2.
* Scientific admission: HOLD.
