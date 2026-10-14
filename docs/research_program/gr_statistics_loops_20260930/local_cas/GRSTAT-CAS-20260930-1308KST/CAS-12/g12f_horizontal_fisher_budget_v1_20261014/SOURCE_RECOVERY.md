# G12-F source recovery

Card: `HTT_ALL_OBLIGATIONS_20261011/tasks/G12-F.json` (inside
`HTT_ALL_OBLIGATIONS_20261011_PACKAGE.zip`, package sha256
`2d0b6da9308ab43e070a620f49241640b5aa7c80c277e1f0857edea22bc4af6f`; extracted card sha256
`43e787f290a815ff2aa825feff6b9bac0dc45184842c9aaa809e17a432e35c5b`).
Title: "Horizontal Fisher budget에서 실제 derivative observable 경계" (claim TEFF-A4 scope line,
parent GR-CAS-12). Scope: `|D_X∫Kf| ≤ √J_X √∫K²f(1+f)` plus kernel/measure derivative terms.

All paths below are relative to `docs/research_program/gr_statistics_loops_20260930/`
unless absolute.

## 1. Verbatim source statement

`supplements/TEFF_POSITIVE_BRIDGE.md` (sha256 `f04d96fe4b7dbee5fc946e10863d602c46399ca15723226ce6b63d4ab53ff21b`):

* `:37-39` the one-event, one-observer massless measure `dν = C E² dE dΩ`.
* `:145-147` "Spacetime derivatives require a distinct input": a static entropy budget does not
  bound spacetime derivatives (G12-E counterexample).
* `:149-151` the horizontal-transport Fisher budget, verbatim
  `∫ |𝒟_X f|² / (f(1+f)) dν ≤ J_X`.
* `:153-158` verbatim: "In a parallel local tetrad at the event, after controlling kernel and
  measure differentiation, a fixed stress kernel K then satisfies
  `|𝒟_X ∫ K f dν| ≤ √J_X [∫ K² f(1+f) dν]^{1/2}`."
* `:160` "These derivative inputs can feed the GR energy-frame gap bound. They are additional
  spacetime information; static TEFF entropy or angular Fisher information does not supply them."
* `:76-87` the proof pattern of Prop. A (weighted Cauchy–Schwarz against the weight
  `z(1+ξz)`), reused here with the Fisher weight.
* `:96-100` (A5) BE envelope `0 ≤ f ≤ F_b = 1/(e^{bE}−1)`, `W = F_b(1+F_b)`; bounded angular
  kernels times nonnegative powers of `E` have finite weighted norms.
* `:238` disposition: "Static entropy implies spacetime derivative bound — Hold / false without
  extra hypotheses — Explicit transport derivative information J_X".

## 2. Horizontal derivative / parallel local tetrad

* `supplements/DOSSIER_POSITIVE_BRIDGE.md:86` (sha256
  `00c1fcb0b786bb874f13e52442af4b7b8a125287d84decb799ea68fd03915ebd`): "use the rest-bundle
  connection obtained by projecting the spacetime connection: a horizontal comparison of a unit
  spatial direction obeys `h∇_X e = 0` … Let `∇^H` denote this horizontal derivative, at fixed
  u-measured energy". So `𝒟_X f` is the derivative of the occupation along `X` with the momentum
  fibre identified by horizontal (parallel) transport at fixed energy `E` and parallel direction
  `e`.
* `supplements/DOSSIER_POSITIVE_BRIDGE.md:104` derivatives must come from independent
  nearby-event information.
* `cas/COMMON_SPEC.md:21-22` energy frame `T^a_b u^b = −ε u^a`, `D_X = h(∇_X T)u`;
  `cas/COMMON_SPEC.md:28-29` derivative inputs are independent supplied quantities and a generic
  tensor is not silently identified with stress `T_ab`.
* `DECISIONS.json:600-605` and `reviews/POSITIVE_EXTENSION_DECISION.json:189-193` (TEFF-H1
  conditions), verbatim: "Constructive derivative bound additionally assumes an actual horizontal
  Fisher budget." / "Kernel/measure derivative contributions vanish in the stated parallel local
  construction, or are added separately."
* `supplements/TEFF_CLAIMS.json:133-138` (TEFF-H1 constructive replacement: "Add a
  horizontal-transport Fisher budget J_X; weighted Cauchy-Schwarz then bounds stress derivatives
  and can feed the GR spectral-gap theorem").
* `cas/contracts/CAS-12.json:48,63,83` assumption "Actual horizontal Fisherbudget J_X for positive
  derivative bound"; `:258` uncontracted research target
  "`|D_X∫Kf|<=sqrt(J_X)sqrt(∫K^2f(1+f))` plus controlledkernel/measure terms"; `:250-254`
  additional analytic obligation "q existence and derivative integral conditions".

### Formal modelling recovered from these sources

In the parallel local tetrad the momentum fibres at points `γ(t)` of an integral curve of `X`
are identified with one fixed fibre `(E, e)`; the occupation becomes a one-parameter family
`t ↦ f(t, ·)` on a fixed measure space, and `𝒟_X f|_{x0} = ∂_t f(t, ·)|_{t=x0}` pointwise.
In that trivialization the kernel and measure are `t`-independent (the source's "kernel/measure
derivative contributions vanish"). In any other trivialization (non-parallel frame, moving
measure density, `t`-dependent kernel) the observable is `O(t) = ∫ K_t f_t ρ_t dμ` with a fixed
reference measure `μ` and density `ρ_t` of `dν_t`, and the kernel and measure terms appear
explicitly ("or are added separately"). The differential-geometric identification of the
horizontal derivative with `∂_t` in a parallel trivialization is **not** formalized; it is the
modelling input recorded in FROZEN_TARGETS.md.

## 3. Statistics, weights and Fisher form

* `CAS-11/g11a_integral_bregman_v1_20261013/lean/G11AIntegralBregman.lean` (reviewed,
  sha256 `85993ce761d3d5546e362ec3debd765617da1cfb542675c6da2aea3e85b11e9a`):
  `:216-220` `Stat`, `:222-226` `xi` (MB 0, BE 1, FD −1), `:243` `hess s f = 1/(f(1+ξf))`
  (Paper I (14)), `:246-256` `dom`, `cdom`, `:275` `dom_pos`, `:361-370` `Sphere2`, `dOmega`,
  `nu`. The source weight `f(1+f)` is the BE case `f(1+ξf)`, `ξ = 1`.
* Lean junk value: `hess s 0 = 1/0 = 0`. The real-valued Fisher integrand `d²·hess s f`
  therefore silently drops points of zero occupation (and FD saturation `f = 1`). G12-F uses an
  extended `[0,∞]`-valued Fisher density with the conventions `d²/w` for `w > 0`, `0` if
  `w ≤ 0, d = 0`, `+∞` if `w ≤ 0, d ≠ 0` (standard Fisher convention `0/0 = 0`, `a/0 = ∞`), and
  proves the bridge to the G11A/G12E real form on the open domain `dom s`.
* `CAS-12/g12e_moment_null_counterexample_v1_20261014/lean/G12ECounterexample.lean:188-193`
  (reviewed, sha256 `6d4b776f829effc875407393e93d0918861d62d98aeb5f1cf602213b3f3b4f6c`)
  `fisher_unbounded`: the horizontal Fisher form `∫ (a n q)² hess s (family … n 0 z) dν` of the
  G12-E family diverges. G12-E `FROZEN_TARGETS.md` non-claims: "the positive replacement bound
  (weighted Cauchy–Schwarz with J_X) is not proved here".

## 4. Envelope, weight and kernel integrability (G12-D, reviewed)

`CAS-12/g12d_reexecution_closeout_v1_20261014/lean/`:
* `G12DInterface.lean:11-12` `occupation β η E = (exp(βE−η)−1)⁻¹`; `:21-23`
  `energyAngularMeasure μ = (volume.restrict (Ioi 0)).prod μ`; `:25-26`
  `kernelDensity b C E = C E² weight b E`.
* `PlanckIR.lean:7-8` `weight b E = e^{bE}/(e^{bE}−1)²`.
* `G12DCardClosure.lean:83-92` `angular_bounded_rpow_kernel_integrable` (bounded angular factor
  times `E^p`, `p ≥ 0`, finite angular measure); `:109-113` `between_states_weight_bound`
  `z(1+z) ≤ W` for `z` between two states under the envelope; `:134-137`
  `no_nonpositive_energy_mass`.
* `G12DUVIntegrabilityEnvelope.lean:28` `weight_eq_occupation`, `:240`
  `occupation_envelope`.

## 5. Abstract derivative identity (card `existing_reuse`: "G12-C04 abstract derivative identity")

`CAS-12/c04_oscillatory_derivative_bridge_v1_20261011/OscillatoryDerivative.lean:12-32`
(sha256 `0f0082138f0be18711221a068921f4b2dda21ebf6f3a137a35d9ea68bd6e5d2d`): pointwise product
rule only, explicitly "no exchange of differentiation and integration". G12-F supplies the
interchange by dominated differentiation (Mathlib
`hasDerivAt_integral_of_dominated_loc_of_deriv_le`,
`Mathlib/Analysis/Calculus/ParametricIntegral.lean:288`).

## 6. Stress kernels and units (card step 5)

Massless kinetic stress at an event in an orthonormal tetrad:
`T^{ab} = ∫ p^a p^b f d³p/p^0`; with `p = E(1, e)` (units `c = 1` in the tetrad components,
`E` the u-measured energy) and `d³p = E² dE dΩ` this is `∫ E n^a n^b f E² dE dΩ`, `n = (1, e)`.
Hence the stress kernel relative to `dν = C E² dE dΩ` is `K^{ab}(E, e) = E n^a n^b` up to the
overall constant absorbed in `C` (source `:39` leaves `C` unspecified; recovering the constant
`g_s/(h³ c³)` and the factors of `c` is outside the source and is not claimed). Units: `f` is
dimensionless; `[D_X f] = 1/[length]`; `[J_X] = [ν]/[length]²`; `[∫K²f(1+f)dν] = [K]²[ν]`; so
`√J_X·√(∫K²f(1+f)dν)` has units `[K][ν]/[length] = [D_X ∫K f dν]`. This dimensional check is
recorded here only; it is not a Lean statement. The energy-frame gap bound that would consume
these derivative inputs (COMMON_SPEC `:21-22`) is a separate card and is not proved here.

## 7. Searches for missing definitions

* `grep -rn "J_X\|horizontal\|parallel local tetrad\|TEFF-A4"` over
  `docs/research_program/gr_statistics_loops_20260930` (excluding `local_cas`) — results cited
  above; no further definition of `𝒟_X` beyond DOSSIER `:86`.
* `htt/`: no occurrence of `J_X` or "horizontal Fisher" (grep, empty).
* `git log -i --grep "G12-F\|horizontal Fisher"` and `git log -- '*g12f*'`: no prior commit.

Unrecoverable from the sources (recorded as exact missing items; independent sub-targets are
still proved):
* M1: an explicit construction of the parallel local tetrad trivialization of the momentum
  bundle along `X` and the proof that it makes the measure density and the stress kernel
  `t`-independent. Searched: TEFF_POSITIVE_BRIDGE.md, DOSSIER_POSITIVE_BRIDGE.md, COMMON_SPEC.md,
  DECISIONS.json, CAS-12 contract. Unlock: a source/contract fixing the bundle, connection and
  fibre measure in a form a Lean statement can quantify over (e.g. a typed frame-bundle
  interface). The general theorem with explicit kernel and measure terms (T7) covers any
  trivialization in which the three derivatives exist.
* M2: the normalisation constant `C` and the factors of `c` in the stress kernel. Unlock: a
  source fixing `C`.
