# G12-A source recovery (GR-CAS-12, TEFF-A3: weighted continuum adjoint of a fixed collision operator)

Written 2026-10-14 before `FROZEN_TARGETS.md` and before any proof compile (only the unchanged reused
modules and one API `#check` probe, `raw/probes/probe01_api.lean`, were compiled before this file).
Paths are relative to the repository root unless absolute.

* `S`  = `docs/research_program/gr_statistics_loops_20260930/supplements/TEFF_POSITIVE_BRIDGE.md`,
  sha256 `f04d96fe4b7dbee5fc946e10863d602c46399ca15723226ce6b63d4ab53ff21b`
  (equals the `research_provenance_hashes` entry of the CAS-12 contract).
* `C`  = `docs/research_program/gr_statistics_loops_20260930/cas/contracts/CAS-12.json`,
  sha256 `5a6827166fe318e37ac9e503a91d6f729155cbef48f450cd9daf0896e47fa6ae`.
* `TC` = `docs/research_program/gr_statistics_loops_20260930/supplements/TEFF_CLAIMS.json`,
  sha256 `9654e73ecab0aeaca12009eb6f81aa860e27131daca2d77e19d7fdfe8309f541`.
* `D`  = `docs/research_program/gr_statistics_loops_20260930/DECISIONS.json`,
  sha256 `a05b30535a63c9b83f449042dfd767c673f1f16f232a1e7493027e011bcd8c6c`.
* Card: `HTT_ALL_OBLIGATIONS_20261011_PACKAGE.zip:HTT_ALL_OBLIGATIONS_20261011/tasks/G12-A.json`
  (source_snapshot `a30d84c7918b54238a48fa62e2ef482f7e6d36fa`; scope_original
  "TEFF-A3: ⟨K,L(f−g)⟩=⟨L* K,f−g⟩ 및 collision ellipsoid").

## 1. Recovered definitions and statements

| Item | Source (file:line, gist) | Lean (this unit, namespace `G12A`) |
|---|---|---|
| measure dν = C E² dE dΩ at one event/observer | S:37-39 | generic product `ρ.prod σ` (energy measure ρ, angular measure σ); instance `G11A.nu C = (energyMeasure C).prod G11A.dOmega` (definitional, reused G11-A) |
| occupations f, g; δ = f − g; budget D_H(f‖g) ≤ ε < ∞; exact retained moments ∫φ_a δ dν = 0; V = span{φ_a} | S:41-46 (A1) | the G11-C budget hypotheses `(BH)` verbatim and `hmatch`; V = `G11C.retainedSpan` |
| positive measurable W with sup_{z between f,g} z(1+ξz) ≤ W a.e. | S:46-51 (A2) | `G11A.WEnvelope` (reused unchanged) |
| kernels in L²(W dν) and the ellipsoid (A3)/(A4) | S:53-74 | reused `G11C.weighted_residual_ellipsoid` (all n, every rank, R† = accepted C02 spectral pseudoinverse) |
| photon envelope 0 ≤ f, g ≤ F_b(E) = 1/(e^{bE}−1), b > 0, W = F_b(1+F_b) | S:93-98 (A5) | `G12D.occupation b 0 E`, `CAS12PlanckIR.weight b E`; reused `G12DClosure.between_states_weight_bound` (z(1+z) ≤ W between the states) |
| "Let L be a specified fixed linear collision operator with adjoint for dν. If L* K_j satisfies the weighted integrability assumptions, apply the same theorem with r_j = L*K_j − P_V(L*K_j), e_j = ⟨K_j, Lf − Lg⟩." | S:120-126 (A7) | layer-1 theorem `collision_ellipsoid` with `collEvec` (⟨K_j, L(f−g)⟩, card form) and the linearity lemma connecting ⟨K_j, Lf − Lg⟩ |
| "The resulting R gives exactly (A4) for the collision residual vector. If L* K belongs to V, its collision moment is determined exactly by the retained data." | S:128 | `collision_ellipsoid`, `collision_exact_of_retained`, `collision_moment_of_representation` |
| the source's concrete fixed operator: (Lf)(E,e) = τ(E)[∫ P(e,e') f(E,e') dΩ' − f(E,e)], P = 3[1+(e·e')²]/(16π) | S:130-135 | `collOp σ τ P` (generic bounded measurable kernel P on an angular space) and `thomsonP` on `G11A.Sphere2` with σ = `G11A.dOmega` |
| "The kernel is symmetric and normalized" | S:137 | symmetry: `thomsonP_symm` ⇒ L* = L (`collAdj_eq_collOp_of_symm`). Normalization ∫P dΩ' = 1 is NOT used by any G12-A theorem (the adjoint/ellipsoid statements hold for every bounded measurable kernel); it is not re-proved here |
| harmonic eigenvalues p_0 = 1, p_2 = 1/10, p_l = 0; L*[B(E)Y_lm] = τ(E)(p_l − 1)B(E)Y_lm | S:137-139 | the eigenvalue VALUES belong to G12-B / CAS12-C02 and are not re-derived; G12-A takes the eigen-relation ∫P(e',e)K(E,e')dΩ' = p K(E,e) as the definition of an angular eigen-kernel and proves L*K = τ(E)(p − 1)K (`collAdj_eigen`) |
| "For constant τ, retaining that spectral/angular moment exactly determines its collision contribution. For energy-dependent τ, add its weighted moment or use (A7)." | S:141 | `constant_tau_retained`, `constant_tau_exact` (exact branch); `collEvec_eigen` (τ(E) × score product kept: e_j = (p_j − 1)∫τ K_j δ dν); negative control `energy_dependent_tau_counterexample` |
| "unpolarized, elastic, fixed-scatterer-rest-frame model … not a guarantee for polarized or frequency-redistributing CMB transfer. Nonlinear collisions … need their own kernels" | S:141 | scope guard: L acts only on the angle at fixed energy, linear in h, scalar; nothing polarized / frequency-redistributing / nonlinear is defined |
| medium | S:141 ("fixed-scatterer-rest-frame"), C:46,61,81 ("Specified fixed linear L and correct adjoint/medium") | the medium enters only through the specified rate τ(E) (a fixed measurable function of energy) and the fixed kernel P in the scatterer rest frame; no electron distribution is modelled |
| contract assumptions | C:44-48 ("Specified fixed linear L and correct adjoint/medium"; "Both f,g ≤ F_b, b>0, no condensate; measure CE²dEdΩ") | hypotheses of the layer-1/2 theorems and of the photon instance |
| singular loci | C:73-77 (COLL-NONLINEAR no fixed adjoint; COLL-TAU energy-dependent τ changes retained kernel) | COLL-TAU: `collEvec_eigen` + negative control; COLL-NONLINEAR: out of scope (no nonlinear operator defined; card pitfall) |
| additional analytic obligation "Weighted adjoint existence" | C:249 | layer-1 adjoint pair identity `adjoint_pair` (kernel Fubini, explicit adjoint domain) and the bounded-route discharge `collAdj_memLp`, `fubKernel_integrable` |
| uncontracted research target "Use L*K and prior moment ellipsoid; retained L*K gives exact moment" | C:254 | T4-T7 |
| TEFF-A3 accepted statement and conditions ("specified linear operator and adjoint", "controlled scatterer/medium inputs", "adjoint kernels satisfy weighted integrability") | TC:64-80; D:517-534 | layer-1 hypotheses `hLK` (weighted integrability of L*K_j) and Fubini integrability; layer 2 derives them from bounded τ, bounded measurable P, energy-only W and K_j ∈ L²(W dν) |

### Choice of route (card lean_step 2)

The pairing in (A7) is the dν pairing ⟨K, h⟩ = ∫K h dν between K ∈ L²(W dν) and δ = f − g with
δ/W ∈ L²(W dν) (i.e. δ ∈ L²(W⁻¹dν), G11-B/G11-C). Since W ~ E⁻² near E = 0 and decays exponentially
(S:100), neither K nor δ need lie in L²(dν); the L²(dν) Hilbert adjoint therefore does not apply to the
pairing directly. G12-A uses the explicit-kernel route: the dν-adjoint is the transposed-kernel operator
`collAdj`, the adjoint identity is proved by Fubini on the explicit domain of absolutely integrable
kernel products (layer 1), and the bounded-kernel hypotheses (|τ| ≤ τmax, |P| ≤ Pmax, finite σ,
W = w(E)) discharge that domain and prove L*K ∈ L²(W dν) (layer 2, Schur-type AM-GM / finite-measure
Cauchy bounds). A ContinuousLinearMap packaging on L²(W dν) with Mathlib's Hilbert adjoint is a
supplementary target (T10) only.

## 2. Reused accepted Lean sources (imported unchanged; recompiled from their original paths into `raw/imports`)

| Module | Path | sha256 | Status record |
|---|---|---|---|
| `BregmanThreePoint` | `.../CAS-11/c01_bregman_three_point_v2_20261008/lean/BregmanThreePoint.lean` | `12f3dd682db93f0966fd3547f10f25eb4fca9e8506ff58fc7c1ba6ac7cf9975c` | dependency of G11-A |
| `G11AIntegralBregman` | `.../CAS-11/g11a_integral_bregman_v1_20261013/lean/G11AIntegralBregman.lean` | `85993ce761d3d5546e362ec3debd765617da1cfb542675c6da2aea3e85b11e9a` | G11-A FORMALLY_CHECKED_SCOPED |
| `G11AGuarded` | `.../CAS-11/g11a_integral_bregman_v1_20261013/lean/G11AGuarded.lean` | `92758d9a0be6ba596461eddb322dd49f397d067ca52b5fe8e656aded10752b77` | idem |
| `G11BHessianEnvelope` | `.../CAS-11/g11b_hessian_envelope_energy_v1_20261013/lean/G11BHessianEnvelope.lean` | `ba1bc644a2b13ac82fff23b5c66645efa596ef72f6e132da2fd76a018be68f27` | G11-B FORMALLY_CHECKED_SCOPED |
| `FiniteGram` (`CAS11C02`) | `docs/research_program/gr_statistics_loops_20260930/local_cas/GRSTAT-CAS11-C02-20260930T090559Z/lean/FiniteGram.lean` | `af91ec609dbd79746f148e67c40cbe39eb0405ea390432b44eb1102918468ffc` | CAS11-C02 CAS_4AXIS_PASS |
| `WeightedProjection` (`CAS11C03`) | `docs/research_program/gr_statistics_loops_20260930/local_cas/GRSTAT-CAS11-C03-20261001T020800Z/lean/WeightedProjection.lean` | `94f8b2139782f21f0b1455079d018a831bb357055b0029c2164512eca7df29da` | CAS11-C03 CAS_4AXIS_PASS |
| `G11CWeightedEllipsoid` | `.../CAS-11/g11c_weighted_residual_ellipsoid_v1_20261014/lean/G11CWeightedEllipsoid.lean` | `732645ad657b32fd32b2c8bb58332f70d0b3c48e1eebab581bdf1493ab976081` | G11-C FORMALLY_CHECKED_SCOPED, review PASS_WITH_NOTES (RETURN.json) |
| `PlanckIR` | `.../CAS-12/g12d_reexecution_closeout_v1_20261014/lean/PlanckIR.lean` | `5ae963f5a7fd584e038856a0f3da627db6dc2b60c57b9e070fc27f67979995a3` | G12-D FORMALLY_CHECKED_SCOPED, review PASS_WITH_NOTES |
| `G12DInterface` | `.../CAS-12/g12d_reexecution_closeout_v1_20261014/lean/G12DInterface.lean` | `340d348ebd41799865731771c6d9cf21677af846c075292a80b510d217f5edff` | idem |
| `G12DUVIntegrabilityEnvelope` | `.../CAS-12/g12d_reexecution_closeout_v1_20261014/lean/G12DUVIntegrabilityEnvelope.lean` | `77fed344f590155fdbdb35a4bceb55b5470a2a40aa5c4bd41c2bec1f0cbc560b` | idem |
| `G12DCardClosure` | `.../CAS-12/g12d_reexecution_closeout_v1_20261014/lean/G12DCardClosure.lean` | `85426b0420639f2103e13c63381459e9947e80e70d589c43043e3444dec90bbd` | idem |

Reuse scope:
* `G11C.weighted_residual_ellipsoid`, `G11C.all_retained`, `G11C.z_memLp`, `G11C.integrable_wmeas_iff`
  are applied to the kernels L*K_j; nothing in them is re-proved.
* `G12DClosure.between_states_weight_bound` supplies (A2) for the photon envelope (A5).
* CAS12-C01 (`c01_finite_adjoint_bridge_v1_20261010`, PASS_SCOPED, finite-dimensional
  `LinearMap.adjoint`) is NOT imported and NOT used as evidence for the continuum adjoint (card
  acceptance 1). The continuum identity is proved from Fubini on the actual product measure.

## 3. Items not recoverable / not in scope

* The numerical values p_0 = 1, p_2 = 1/10, p_l = 0 (S:137) and the normalization ∫P dΩ' = 1 are owned by
  G12-B / CAS12-C02 (Legendre/Funk–Hecke); they are not needed for, and not re-proved in, G12-A. No
  sphere spherical-harmonic (Y_lm) API is built here; the τ-branch is stated for an arbitrary angular
  eigen-kernel (∫P(e',e)K(E,e')dσ(e') = p K(E,e) a.e.).
* Physical certification of τ(E), of the medium/electron rest frame, of ε, of W and of the actual
  channel kernels is data/physics input (S:104, S:141), not a mathematical definition; not claimed.
* Polarized, frequency-redistributing and nonlinear collision operators (S:141, card pitfall,
  C:70 / C:73 COLL-NONLINEAR) are excluded; no definition is attempted.
* No missing definition blocks a G12-A sub-target.
