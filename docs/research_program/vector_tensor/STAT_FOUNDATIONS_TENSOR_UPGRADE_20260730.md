# Tensor Upgrade of the Departure Statistics

## From the scalar family (x, Q, Π, F, G_F) to a functional-indexed, orbit-resolved, conditioning-typed family

**Document id:** `STAT-FOUND-TENSOR-v1` · **Date:** 2026-07-30 · **Intended home:** `docs/research_program/`
**Predecessors (adopted, in-repo):** `STAT_FOUNDATIONS_REVIEW_20260727.md` (`STAT-FOUND-v1`), the justification companion, PR-248–252 (typed foundation), PR-253–258 (premise anchor, anchor geometry, response geometry, velocity frames, orbit catalogue v2, open-set classes)
**Audited revision:** HEAD `e7c2064` (`research/pr04-multicomponent`); PR-253–258 all merged at this revision (`machine_readable/pr_backlog.yaml` still carries a stale `PENDING` activation state for all six)
**Companion artefacts:** `tensor_foundations_oracle.py` (TF-01…TF-12, all PASS), `PROOF_REGISTRY_TWO_PILLARS_20260730.md`

**Claim posture.** Pre-solver methodology. Nothing here is a detection, a Bianchi-family identification, a geometry measurement, or a native-solver validation. Every new object is diagnostic-only or conditional; every new proposition carries its premises. Numerical statements marked ⟦V⟧ carry an oracle receipt.

---

## 0. What this document does

The programme's centre of gravity is now, correctly stated:

```
kinematic component state → O(3) orbit / type invariants → (x, Q, Π, F, G_F)
    → mask · depth · direction-conditioned partial classification
```

The typed foundation for the first arrow exists (`DepartureState`, `orbit_catalogue_v2`, `anchored_response_geometry`, `velocity_frame_decomposition`, `open_set_response_classes`). What does not yet exist is the *middle* arrow: the statistics family is still indexed by nothing — there is one `x_C`, one `Q`, one `Π`, one `F`, one `G_F` — while the state it summarises is component-native and the classification it feeds is direction- and mask-conditioned. The result is a barbell: a component-native head, a component-native tail, and a scalar waist.

This document specifies the waist. It defines a functional-indexed family `(x_φ, Q_φ, Π_φ, F_φ, G_{F,φ})` in which the legacy scalars are the single instance `φ = ⟨c, ·⟩`; it completes the invariant catalogue and states the sense in which it is now closed; it types the conditioning that `Π` has always implicitly carried; it separates two response-geometry states that are currently fused; and it makes the mask/depth ladder a sequential object with its own calibration. It closes the seven priorities of the 2026-07-30 review note in that order, and it registers what each one buys.

One framing point governs everything below. The upgrade is **not** motivated by "the scalar is wrong." The scalar is exactly right as what it is — the signed Gauss–Friedmann budget projection, preserved bit-identically under BC1. The upgrade is motivated by a counted fact: ⟦V⟧ **on the principal stratum the kinematic state has nine functionally independent SO(3)-invariant directions (twelve once four-acceleration is adjoined, fifteen once the velocity frame splits), and `x_C` resolves exactly one of them** (TF-06). Eight of the nine are not "extra detail"; they include an invariant of quadratic order — the tilt–vorticity helicity `β·ω` — along which the budget functional has exactly zero derivative (TF-07). The tensor upgrade is the recovery of a counted, bounded, pre-registrable amount of information, not an open-ended elaboration.

Two disciplines apply to that sentence and are enforced throughout. First, **resolving a direction in the invariant space is not identifying it from data**: how much of the nine is reachable is a separate question governed by the response rank (§6) and by partial identification (§4.3), and nothing here asserts that the upgrade recovers all of it. Second, the `dim − 3` count holds **on the principal stratum**, where the generic isotropy is finite; off it the count is different (a single vector alone has isotropy `U(1)`, hence one invariant rather than zero), and the oracle carries that counterexample so the rule is never applied blind.

---

## 1. The state: three layers, one convention contract

### 1.1 Why not one dataclass

`DepartureState` currently carries `σ(5) ⊕ ω(3) ⊕ β(3) ⊕ ΔΩ_k(1)` with eight metadata strings and a positional 12-D `vector` (`statistical_foundations.py:645-687`). Four-acceleration is absent from every state object in the repository; it exists only on the anchor side, as the structural-absence record `MES_G_ACCEL_ABSENCE` (`statistical_foundations.py:467-490`) and in the withheld/legacy bound layer. Meanwhile PR-256 introduced a *second* velocity layer, `β_RO = β_RM + β_MO + O(β²)`, that stands beside `DepartureState.beta_a` with no declared relation to it.

Widening the single dataclass would be the wrong repair, for a reason that is physical rather than architectural: `σ_ab`, `ω_a` and `A_a` are the kinematics **of a chosen congruence**, whereas `β_MO` is the boost **between two frames** and is not a dynamical component of the same kind. Fusing them would let a frame convention masquerade as a state component — the exact error class the typed foundation was built to prevent.

### 1.2 The three layers

```
CongruenceKinematics                      # kinematics OF a declared congruence
    sigma_ab      : STF5   (polar rank-2, trace-free)
    omega_a       : 3      (AXIAL)
    acceleration_a: 3 | MISSING_COMPONENT (POLAR)
    congruence_id, frame, epoch_window, averaging_scale, basis, units,
    parity_contract, perturbative_order, acceleration_normalization

VelocityFrameBundle                       # relations BETWEEN frames (PR-256, extant)
    beta_RO, beta_RM, beta_MO  (polar; any may be MISSING_COMPONENT)
    closure contract  beta_RO = beta_RM + beta_MO + O(beta^2)

JointAnisotropyState                      # composition by reference, never by copy
    kinematics_ref : content id of a CongruenceKinematics
    velocity_ref   : content id of a VelocityFrameBundle
    curvature      : delta_omega_k (signed scalar)
    weyl_ref       : optional, NEEDS_NATIVE at this stage
    beta_semantic_role : which velocity the legacy DepartureState.beta_a denotes
```

`DepartureState` is retained unchanged as the **legacy projection** of `JointAnisotropyState`, exactly as `x_C` is the legacy projection of the state. The mandatory `beta_semantic_role` field is what stops the current silent identification of `DepartureState.beta_a` with one of the three PR-256 velocities; an adapter that cannot fill it must fail closed rather than guess.

### 1.3 The acceleration convention, stated once

The repository currently distinguishes `A/(cΘ)` from `A/Θ` nowhere: the only acceleration-over-expansion quantity, `MESBounds.udot_over_Theta`, carries no units metadata, and `DepartureState.units` is the bare string `"dimensionless"`. With `u^a u_a = −c²` the natural dimensionless acceleration is `Â_a = A_a/(cΘ)`; in the `c = 1` sectors of the code it is `A_a/Θ`. These differ by a factor of `c` and must never be mixed silently.

**Requirement.** `CongruenceKinematics.acceleration_normalization ∈ {A_OVER_C_THETA, A_OVER_THETA_C_EQUALS_ONE}`, mandatory whenever `acceleration_a` is present, folded into the state content identity, and part of the `channel_key` of any acceleration stress. A state whose acceleration normalization is absent yields `MISSING_COMPONENT`, never a zero. This mirrors the treatment `velocity_frame_decomposition.py:406-416` already gives to `units == "dimensionless_beta_c_equals_1"`.

### 1.4 The acceleration sector: slaved, not free, and anchored by a different authority

⟦V⟧ TF-12. For a perfect fluid the 1+3 momentum equation `(μ+p)A_a = −D_a p` slaves the four-acceleration to the pressure gradient. With `c_s² = dp/dμ` and a dimensionless gradient bound `|D_a ln μ|/Θ ≤ ε_g`, and using the standard normalisation `A²_std = A_aA^a/(6H²) = (3/2)|A/Θ|²`:

```
A²_max^Euler(w) = (3/2) · [ c_s² / (1+w) ]² · ε_g² .
```

Three consequences, in decreasing order of robustness.

**(i) The geodesic premise becomes a derived late-time limit rather than an assumption.** For pressureless matter `c_s² → 0` gives `A²_max → 0`: the `u̇ = 0` premise under which the registered MES shear and vorticity anchors are verified is *recovered*, with an explicit remainder, instead of being imposed. The slaving factor is exactly `1/4` in the radiation era and monotone in `c_s²`. This is the part of the result that depends on no unregistered input.

**(ii) The sector currently carrying `NO_MES_ANCHOR` can acquire a typed, epoch-conditional ceiling from a different authority** — the momentum constraint, not MES — with its own `AnchorAuthorityKind` and its own premise set (perfect fluid; no frame heat flux; no anisotropic stress; barotropic or constant `w`). It is not, and must not be presented as, a rehabilitation of the refuted non-geodesic MES triple, and it does not touch the `MES ACCEL` withholding.

**(iii) The acceleration sector is congruence-typed by construction.** The same spacetime has `A = 0` for the matter congruence and `A ≠ 0` for the photon–baryon congruence before decoupling. This is *why* the state must carry `congruence`, and why an acceleration saturation reported without its congruence and epoch is meaningless.

**Provenance warning, load-bearing.** **No `ε_g` is registered anywhere in the repository.** The oracle's default is an explicit placeholder numerically equal to `C.eps2` — a `ΔT/T` temperature-quadrupole amplitude, which is *not* a bound on `|D_a ln μ|/Θ` and carries no MES or other authority. What TF-12 establishes is the **shape** of the result — the `[c_s²/(1+w)]²` factor and its exact zero at `c_s² = 0` — not any absolute ceiling value. Deriving and registering `ε_g` with its own premises is a prerequisite of PR-259 shipping any acceleration number, and `gradient_regularity_registered` is set to `False` until it exists.

---

## 2. The functional-indexed statistics family

### 2.1 The generalisation

Every legacy statistic is one instance of a family indexed by a **registered functional** `φ` of the state:

| legacy | generalised | meaning |
| --- | --- | --- |
| `x_C = ⟨c, g⟩` | `x_φ = φ[𝒦]` | the value of a registered functional on the state |
| `Q = x/x_max` | `Q_φ = N_φ(x_φ)/U_φ` | numerator policy over a typed denominator |
| `F` | `F_φ` | occupancy, **admissible only when φ is sign-definite and anchored** |
| `Π(c)` | `Π_φ(c \| η)` | conditional exceedance, `η` typed (§4) |
| `G_F` | `G_{F,φ}` | depth/redshift contrast of `F_φ` (canonical spelling stays `G_F`; `F_G` appears in no Python identifier and survives only as a legacy filename token under `docs/ver2_upgrade/` — it must not be reintroduced into code) |

`x_C` is `φ = ⟨c, ·⟩`; every historical number is preserved as that instance under BC1, and BC2 forbids the family's existence from promoting any of them.

### 2.2 The functional identity — the field that makes the family safe

Every registered functional carries, and every derived statistic inherits:

```
functional_id        source_state_id     output_rank        tensor_degree
O3_parity            frame               congruence         epoch_window
averaging_scale      normalization       anchor_id          perturbative_order
```

Three of these do real work and are new:

* **`tensor_degree`** is the polynomial degree in the state, and it is what lets the family mechanise TF-07: budget semantics are admissible only for functionals of the four budget invariants `{tr σ², ω², β², ΔΩ_k}`, so a functional such as `tr σ³` or `β·ω` that claims a budget contribution is rejected at construction. (The gate is *factorisation through those four*, not a bare degree cut — see §3.1's statement of TF-07, which is deliberately weaker than a grading claim because `Ω_tilt = (1+w)Ω_m sinh²β` is an even function of `β·β` rather than the monomial `β²`.)
* **`O3_parity ∈ {SCALAR, PSEUDOSCALAR}`** decides which statistics are even definable (§2.3) and which test applies (§5).
* **`anchor_id`** is the existing channel-key gate; a functional without a matching anchor gets `ANCHOR_UNAVAILABLE`, never a fabricated ceiling.

### 2.3 Which statistic each functional may carry

This table is the well-posedness rule of the whole family, and it is where the R1–R3 conditions of `STAT-FOUND-v1` become mechanical.

| functional class | example | `x_φ` | `Q_φ` | `F_φ` | `Π_φ` | `G_{F,φ}` |
| --- | --- | --- | --- | --- | --- | --- |
| sign-definite, anchored | `‖σ‖²`, `‖ω‖²`, `β²` | ✔ | ✔ | ✔ | ✔ | ✔ |
| sign-definite, no anchor | `‖A‖²` (MES), `ΔΩ_k` | ✔ | `ANCHOR_UNAVAILABLE` | ✘ | ✔ vs registered null | ✘ |
| signed even scalar | `tr σ³`, `β·σβ` | ✔ | signed `Q_φ` only | **✘** | ✔ | ✘ |
| pseudoscalar | `det[β,σβ,σ²β]`, `β·ω` | ✔ | signed `Q_φ` only | **✘** | ✔, **exact** (§5) | ✘ |
| scale-free shape | `J_σ` (degree 0) | ✔ | ✘ (already normalised) | ✘ | ✔ | ✔ (drift) |
| homogeneous shape amplitude | `Δ_σ` (degree 6) | ✔ | signed `Q_φ` only | ✘ | ✔ | ✔ (drift) |
| budget projection | `x_C` | ✔ | BC1 legacy | BC1 legacy | BC1 legacy | BC1 legacy |

Two rules are load-bearing and both were derivable from the foundation but were not enforceable before the functional identity existed:

> **No filling fraction on a signed functional.** `F_φ` requires `φ ≥ 0` on the admissible set. `tr σ³` is signed; attaching an occupancy to it reproduces the `defect_negative` pathology in a new coordinate. The correct pairing for signed functionals is a signed `Q_φ` and an exceedance `Π_φ`.
>
> **No occupancy without an anchor of matching channel key.** Unchanged from `STAT-FOUND-v1`; now mechanised by `anchor_id` rather than by review.

### 2.4 The vector saturation and its canonical scalar summary

The obvious objection to a vector of saturations is that comparison requires collapsing it, and collapsing reintroduces a convention. It does not. For a product of per-sector balls — which is exactly the shape of the registered admissible set, per `PA-THM-PRODUCT-BALL` — the Minkowski gauge of the product body is the **maximum** of the per-sector saturations:

```
ρ_A(u) = max_j ‖u_j‖ / B_j ,        E = max(ρ_A − 1, 0)        ⟦V⟧ TF-08
```

So the scalar summary of a vector saturation is forced, and it is an L^∞ combination, not a signed sum. This is the precise sense in which the tensor upgrade repairs the original sin of `x_C`: the legacy scalar combined sectors by a signed sum, in which a large shear and a large vorticity cancel; the gauge combines them by a maximum, in which nothing cancels and a multi-sector exceedance is refuted by its worst sector and by nothing else. TF-08 verifies the identity against a bisection evaluation of the gauge definition rather than assuming it.

### 2.5 What the budget can and cannot see

⟦V⟧ TF-07. The Gauss–Friedmann budget functional **factors through** the four invariants `{tr σ², ω², β², ΔΩ_k}`. It therefore has exactly zero derivative along the remaining quadratic invariant — the tilt–vorticity helicity `β·ω` — and along every direction transverse to their common level set.

The statement is deliberately a factorisation and not a polynomial-grading claim, because the repository's tilt term is `Ω_tilt = (1+w)Ω_m sinh²β`, an even function of `β·β` rather than the monomial `β²`; the budget therefore *does* depend on higher even powers of `β·β`, and a claim that it "vanishes on every invariant of degree ≥ 3" would be false. What survives — and is what the programme needs — is that the budget is a function of four invariant coordinates out of nine.

Two consequences. First, the blindness of `x_C` is **structural and counted**, not an estimator defect: the constraint itself cannot see morphology, and the invisible directions begin already at quadratic order. Second, because the budget factors through a four-dimensional subalgebra, the morphology programme is not competing with it for the same information; budget and morphology can be reported side by side without double counting. Verification is by two independent routes — an explicit witness that moves the helicity while holding all four budget invariants (hence `x_C`) exactly fixed, and a computed gradient test showing the budget gradient lies in the span of the four invariant gradients (max relative residual `9.5e-11`) while the helicity gradient does not (transverse fraction ≥ 0.38).

---

## 3. The invariant catalogue: completion, stratification, closure

### 3.1 What PR-257 established and what it left open

PR-257 froze twelve degree-bounded polynomials for `V₂^σ ⊕ V₁^{ω,axial} ⊕ V₁^{β,polar}`, proved their parity typing, the trace-free Cayley–Hamilton identity and the β-Krylov Gram syzygy on four CAS axes, and — with exemplary discipline — hard-pinned `generic_orbit_separation_status` and `degree_completeness_status` to `UNPROVEN`, registering an exact non-separation witness: with `β = 0`, `σ = diag(1,2,−3)`, the states `ω = (1,2,3)` and `ω = (−1,−2,−3)` receive identical values from all twelve polynomials.

### 3.2 The witness is closed — on the stratum where it lives

⟦V⟧ TF-01/TF-02. The generator that resolves it is the **axial Krylov determinant**

```
K_ω := det[ ω , σω , σ²ω ] .
```

Its parity is the point. With `ω` axial each of the three columns carries a factor `det(R)` and the stacked determinant carries a fourth, so `K_ω → det(R)⁴ K_ω = K_ω`: **`K_ω` is a genuine O(3) scalar**, not a pseudoscalar — unlike its polar counterpart `K_β = det[β,σβ,σ²β]`, which is the reflection-odd invariant PR-257 already carries. And `K_ω` is odd under `ω → −ω`. On the registered witness it takes the values `+120` and `−120`, separating exactly the pair the twelve could not; the stabiliser of `diag(1,2,−3)` in SO(3) is computed (not asserted) from the commutant to be the Klein four-group of even sign flips, none of which maps `ω` to `−ω`, so the two states genuinely lie in distinct orbits and the failure was a real incompleteness rather than an artefact.

**Scope, stated because it is easy to over-read.** The registered witness has `β = 0` — it lies *off* the principal stratum of §3.5, precisely because `β` is not cyclic there. Exhaustive checking of the residual gauge shows that for generic `β` the v2 catalogue already separates SO(3) orbits, and adding `K_ω` does not raise the Jacobian rank (both give 8 on the 11-dimensional `(σ,ω,β)` space, as the syzygy of §3.3 requires). So `K_ω` is **not** a missing generic generator: it supplies a sign bit exactly where a vector fails to be cyclic for `σ`.

The correct claim is therefore narrower than "the catalogue was incomplete" and more useful than it sounds: **`K_ω` closes the registered non-generic witness, and the same exhaustive check is positive evidence for the still-unproved generic separation conjecture (I-2.7).** `generic_orbit_separation_status` and `degree_completeness_status` remain `UNPROVEN` and are unchanged by this document.

### 3.3 What the new generator does and does not add

⟦V⟧ TF-03. `K_ω² = det Gram(ω, σω, σ²ω)`, and by the Cayley–Hamilton reductions (TF-04) that Gram determinant is a polynomial in the five even invariants of `(σ, ω)`. Hence:

> **The magnitude of a Krylov determinant carries no information beyond the even catalogue. Its entire new content is one bit: the sign — the handedness of the vector relative to the shear eigenframe.**

This is a sharp and useful statement in both directions. It bounds the completion (one bit per vector sector, not a new continuum — which is also why §3.2's `K_ω` cannot and does not raise the functional rank), and it identifies precisely which quantity is exactly testable in §5.

### 3.4 Catalogue v3: generators, and the generation rule

Do not enumerate by hand. Generate (this section is the specification `K_ω` of §3.2 belongs to, one Krylov determinant per vector sector):

```
Gram–Krylov generators   G^{(ij)}_{vw} = (σ^i v)·(σ^j w),  i,j ∈ {0,1,2},
                         v, w ∈ { β_RM , β_MO , A , ω } ,
Krylov determinants      K_v = det[v, σv, σ²v]           (one per vector),
Triple determinants      det[v, w, σ^i v] , det[v, w, σ^i w] , det[v, w, z] ,
Shear scalars            tr σ² , tr σ³ ,
Curvature                ΔΩ_k .
```

Parity assignment is mechanical: `β_RM, β_MO, A` are polar, `ω` is axial, and a monomial is reflection-odd iff (number of `ω` factors + number of ε-tensor factors) is odd. The registered catalogue is then the degree-bounded closure of this generating set, deduplicated by the syzygies, with an explicit **Jacobian-rank acceptance test**: the generating set must attain the transcendence degree ⟦V⟧ TF-06 — 9 for `(σ, ω, β, ΔΩ_k)`, 12 with acceleration, 15 with the velocity split — or the catalogue is rejected as functionally incomplete before any parity or syzygy check runs.

### 3.5 The honest separation statement

Separation of orbits by the completed catalogue holds on the **principal stratum** — `σ` with distinct eigenvalues and the participating vectors cyclic for `σ`. Off it, the residual isotropy group is nontrivial (a `U(1)` for axisymmetric `σ`, larger at `σ = 0`) and the correct statement is separation modulo that isotropy. This is not a caveat to be minimised; it is the **stratification that defines the kinematic type ladder** of §7, and it is why `J_σ = ±1` (⟦V⟧ TF-05: exactly the repeated-eigenvalue locus, since `Δ_σ = (I₂³/2)(1 − J_σ²)`) is a type boundary rather than a number near an endpoint.

`generic_orbit_separation_status` may move from `UNPROVEN` to `PROVEN_ON_PRINCIPAL_STRATUM` only when the completed catalogue passes its own four-axis CAS contract; `degree_completeness_status` stays `UNPROVEN` until a Molien/Hilbert-series argument is registered, and no claim in this document depends on it.

### 3.6 `tr σ³` is a type coordinate, not a bigger amplitude

⟦V⟧ TF-05. With `I₂ = tr σ²`, `I₃ = tr σ³`:

```
J_σ = √6 · I₃ / I₂^{3/2} ∈ [−1, 1] ,     Δ_σ = ½I₂³ − 3I₃² = ½ I₂³ (1 − J_σ²) ,
J_σ = +1 prolate axisymmetric   J_σ = −1 oblate axisymmetric   J_σ = 0 at (λ, −λ, 0) ,
```

`Δ_σ` being exactly the discriminant of the characteristic polynomial, and `J_σ` being scale-free. This is the object that lets a shear morphology class be named without reference to any Bianchi family: `J_σ` is an anisotropy **type** coordinate, `I₂` is the amplitude, and only the amplitude is anchored by MES. The separation of these two roles is the tensor-level statement of the amplitude/shape firewall:

> **MES amplitude anchor ≠ tensor morphology classifier.**

---

## 4. The conditional exceedance surface

### 4.1 What `Π` has always been missing

`ExceedanceCurve` (`mio/formalism/exceedance.py:473`) records a curve over thresholds for `Q` or `F`, with threshold policy, look-elsewhere trials and null-status metadata — but with no conditioning coordinates and no declaration of the sampling law that the probability is taken under. The object the programme actually needs is

```
Π_φ( c | β_MO(z), β_RM, 𝒲, ν ) = P_ν[ X_φ(D; 𝒲) > c | β_MO(z), β_RM ] ,
```

where `𝒲` carries radial window, selection, ZoA mask, smoothing and averaging scale.

### 4.2 The contract

```
ConditionalExceedanceSurface(
    functional_id, threshold_grid,
    beta_local_coordinates, beta_global_coordinates,
    redshift_windows, mask_or_zoa_ids,
    values, sampling_law, conditioning_source,
    covariance_id, coverage_report )
```

**`sampling_law`** must be one of `FIXED_INJECTION_MOCK`, `BOOTSTRAP_RESAMPLING`, `PROFILE_LIKELIHOOD`, `POSTERIOR_PREDICTIVE`, `OBSERVATIONAL_POSTERIOR_PUSHFORWARD`. The same number under five different laws is five different statements, and the current type cannot tell them apart.

**`conditioning_source`** must be one of `INJECTED`, `EXTERNALLY_ESTIMATED`, `PROFILED`, `POSTERIOR`, `IDENTIFIED_SET`.

**Ownership.** MIO may own the mock-calibrated surface; a posterior-conditioned probability is HTT-owned. The existing firewall is unchanged.

### 4.3 The envelope, and why it is the interesting case

When `(β_RM, β_MO)` are not point-identified — the generic situation until a boost-only channel is registered (§6) — a single `Π` is not a defined object. The surface must report

```
Π̲_φ(c) = inf_{η ∈ 𝔍_β} Π_φ(c | η) ,      Π̄_φ(c) = sup_{η ∈ 𝔍_β} Π_φ(c | η) .
```

This is the point where the local/global no-go stops being a paragraph and becomes an interval. Two structural facts make it computable rather than aspirational — with a condition that must be stated exactly, because the natural half-remembered version of it is false:

1. `IdentifiedDepartureSet` already carries a **vertex + recession** representation with exact `Fraction` support computations (`statistical_foundations.py:779-885`). Vertex enumeration returns the envelope endpoints when `𝔍_β` is convex **and bounded** (no active recession direction — `support()` returns `math.inf` on one) and the conditional map is **monotone in `η`**, or more generally when it is quasi-convex *for the upper endpoint* and quasi-concave *for the lower*. Bauer's maximum principle places the **supremum** of a quasi-convex function at an extreme point; the **infimum** of a quasi-convex function is generically interior (`Π = η²` on `conv{−1,+1}` has infimum 0 at `η = 0`, while vertex enumeration returns 1). Assuming quasi-convexity alone would silently return a wrong lower envelope, which is exactly the direction that matters — `Π̲` is the conservative endpoint.
2. Whenever the geometric conditions above are not certified, the surface must return `OPTIMIZER_REQUIRED` rather than a silently sampled envelope. `anchor_geometry` already established exactly this refusal for continuous conditional families (PR-254); the same status is reused rather than reinvented.

**Reporting rule.** An envelope with `Π̲ > 0` at a registered threshold is a partial-identification statement of real content; a single `Π` published without its conditioning coordinates and sampling law is not interpretable and must fail closed.

---

## 5. Two exactly calibrated tests the tensor layer makes available

These are the additional statistical analyses the upgrade buys that the scalar layer could not host. Both are positive capabilities, and both are cheap precisely where the rest of the programme is expensive.

### 5.1 The parity sign test — exact, model-free, mask-robust

⟦V⟧ TF-09. Let `ψ` be any reflection-odd invariant (`K_β`, `β·ω`, `β·σω`, `β·σ²ω`). Suppose

* **(H1)** the null law is invariant under a reflection `P` that also fixes the analysis geometry (mask, weighting, pixelisation);
* **(H2)** the **estimator** is exactly `P`-equivariant, `ψ̂ ∘ P = −ψ̂`, including mask deconvolution, regularisation and weighting;
* **(H3)** `P(ψ̂ = 0) = 0` under the null.

Then the law of `ψ̂` is symmetric about zero, and therefore

```
sign(ψ̂) ~ Bernoulli(1/2)   exactly,   and   sign(ψ̂) ⫫ |ψ̂| .
```

No covariance model, no mock ensemble, no asymptotics, no look-elsewhere over a nuisance family.

The reason this is not a curiosity: reflection through the Galactic plane fixes any latitude-symmetric mask `|b| > b_cut`, and it fixes any parity-symmetric noise or foreground-variance model. **Under (H1)–(H3) the exactness therefore survives precisely the modelling failures — mask coupling, anisotropic noise, misspecified covariance scale — that make every even statistic in this programme conditional on a null ensemble.** The oracle demonstrates the contrast directly: across an isotropic null and two strongly anisotropic but reflection-symmetric nulls, the sign statistic holds `P(ψ̂ > 0) = 0.500 ± 0.002` in all three, while the even statistic's *scale* moves by a factor of 36.5 (sd `3.18 → 116.0`). Its mean stays zero by symmetry — the calibration failure that this induces is in the **tails**, not the centre, which is exactly where a null-ensemble-calibrated even statistic makes its claims.

Three scope disciplines, stated with the result rather than after it.

**(a) The binding practical hypothesis is (H2), not (H1).** Real selection functions (depth versus declination) and point-source holes are *not* `b → −b` symmetric. Any such asymmetry must be carried as a declared violation of (H2), not assumed away; the honest version of this test ships with an equivariance audit of its own estimator.

**(b) (H3) fails on named strata and the test must abstain there.** On the axisymmetric locus `Δ_σ = 0` the Krylov chain of any vector is rank-deficient and `K_β` vanishes identically (⟦V⟧ max `|K_β| = 2.1e-14` over 2000 draws), and any sector carrying `MISSING_COMPONENT` gives `ψ̂ = 0` for every listed pseudoscalar. An atom at zero destroys both the Bernoulli(1/2) calibration and the independence, so the correct output there is abstention, never a sign.

**(c) Signs across rungs are not independent, and must not be pooled binomially.** Independence of sign from magnitude is a statement about *one* statistic. Nested mask rungs generate a filtration — §5.2 is precisely the proof that they are maximally dependent — so pooling rung signs as `Binomial(n, ½)` is invalid and anti-conservative. Combination must go through a dependence-agnostic combiner: the registered arithmetic-mean e-value merge, which is valid under arbitrary dependence and is already in the codebase for exactly this reason.

The test addresses exactly the one bit TF-03 identified as new per vector sector; it is not a test of amplitude, and a null result constrains handedness only. A detected asymmetry localises either to genuine chirality or to a **parity-asymmetric systematic** — a dichotomy sharper than any even statistic delivers, and one whose second horn is a concrete, checkable pipeline defect rather than a shrug.

### 5.2 The nested-mask path as a reverse martingale

⟦V⟧ TF-11. A nested mask ladder generates a decreasing filtration. If — and only if — every rung reports the conditional expectation of the **same full-sky target** given the data it retains, the ladder is a reverse martingale, the reversed finite sequence is an ordinary martingale, and Doob's inequality calibrates the entire path for free:

```
P( max_j |M_j| ≥ λ · sd(M_full) ) ≤ 1/λ² .
```

The design trap this closes is the current practice: fitting each cut independently and renormalising each rung to its own rung-specific target destroys the martingale property, and the observed path excursions then violate the bound by a wide margin (⟦V⟧ empirical `P(sup ≥ 3) = 0.60` against a bound of `0.111`). A ZoA morphology path is therefore not a plot of independently fitted cuts; it is a sequential object whose calibration is free if it is built correctly and absent if it is not. This is the single most consequential implementation detail in §8.

---

## 6. Response-geometry status refinement

`measure_source_response_geometry` currently returns `SUM_ONLY` for two states that are not the same:

* **exact structural degeneracy** — `rank[R_L, R_G] < rank R_L + rank R_G`; the tangent spaces genuinely overlap;
* **full rank, weak identification** — the direct sum holds but `ψ_min ≪ 1` or `s_min ≪ 1`.

⟦V⟧ TF-10 exhibits the ladder explicitly. With a dipole channel alone the response has rank 3 against 6 parameters — `NON_IDENTIFIED`. Adding a boost-only channel restores rank 6. As that channel's amplitude falls from 0.85 to 0.001 the rank stays 6 while the minimum principal angle falls from 0.704 rad to 0.001 rad and the condition number rises from 3.8 to 2.3 × 10³. Reporting those cells as `SUM_ONLY` conflates "the geometry forbids separation" with "this dataset barely achieves it" — a difference that determines whether more data helps.

**The two boost-only channels are not interchangeable, and the difference is an order in `β`.** Aberration is a genuine **linear** effect: the `ℓ↔ℓ+1` coupling is `O(β)` and legitimately populates a linear response, which is what the rank-6 statement above rests on. The kinematic quadrupole is `O(β²)` — the repository types this explicitly (`frame_typed_algebra.py`: `kinematic_quadrupole_leading_order() → 2`) — so about `β = 0` its Jacobian vanishes and it contributes no linear rank at all. It becomes informative only when expanded about a fiducial `β_MO ≠ 0`, where its relative amplitude is `O(β_MO) ≈ 1.2 × 10⁻³` — i.e. the *bottom* rung of the ladder above, squarely in the `WEAKLY_IDENTIFIED` regime with `κ ≈ 2 × 10³`. A specification that lists the two channels together without this distinction would license an identification claim the second channel cannot support.

**Required status set** (`WEAKLY_IDENTIFIED` already exists at `statistical_foundations.py:64` and is currently dead code with zero call sites — it is free to define):

```
MISSING_RESPONSE_PROVIDER  NON_IDENTIFIED  SUM_ONLY  WEAKLY_IDENTIFIED  SEPARABLE_CANDIDATE
```

**Required gate.** Not the minimum principal angle alone, but the tuple `(ψ_min, s_min, κ, held-out wrong-source rate)`, with the held-out rate the arbiter when the geometric quantities disagree. PR-256's six-method benchmark already produces exactly that held-out quantity; the refinement wires it into the status rather than leaving it in the report body.

**The positive half.** The same proposition is the identification result for research axis (a): the local-boost sector is *over-determined* once a boost-only channel is registered — the observer boost fixes the dipole, the aberration coupling and (at second order) the kinematic quadrupole with **locked relative coefficients and no free parameter** — so the global tilt is identified as the residual rather than removed by a subtraction convention. Linear identification rests on aberration; the quadrupole is an over-determination check, not a second independent linear channel. The zero-parameter boost residual machinery already exists (`boost_biposh_residual.py`, `ExactBoostOperator`); what the upgrade adds is the rank statement that says what it buys and the status that says when it has bought it.

---

## 7. The type ladder and the classification output

### 7.1 Three levels, named

```
𝖪   kinematic orbit type          — the completed invariant catalogue (§3)
𝖬   observable morphology type    — low-ℓ harmonic / BiPoSH / directional features
𝖦   geometric-dynamical type      — requires E_ab, H_ab, ³R_⟨ab⟩, π_ab
```

PR-251/257 operate at 𝖪 and 𝖬. 𝖦 requires the native transfer and remains the hard ceiling. Stating the ladder explicitly is what allows the programme to say "we classify anisotropy type" without the sentence being read as a Bianchi-family claim: the object classified is `[𝒦]_{O(3)}` on a declared stratum, not a spacetime.

### 7.2 The output object

```
AnisotropyTypeReport(
    kinematic_stratum,                # principal / axisymmetric / degenerate
    orbit_invariant_intervals,        # partial identification per invariant
    parity_class,                     # incl. the exact sign statistics of §5.1
    shear_multiplicity,               # from Delta_sigma / J_sigma
    vector_support_pattern,           # which eigendirections each vector loads
    local_global_identification_status,   # the five-status set of §6
    compatible_response_classes,      # PR-258 equivalence class, or TYPE_UNIDENTIFIED
    zoa_stability_class,              # from the calibrated mask path of §5.2
    lowell_morphology_class,
    uncovered_directions,             # what the registered response cannot reach
    assumptions )
```

`uncovered_directions` is not decoration: it is the field that keeps an open-set classifier honest, and it is computable — it is the null space of the registered anchored response, which `anchored_response_geometry` already returns.

---

## 8. Migration, chokepoints, and what fails closed

The repository is unusually well defended, which means an upgrade must be planned against its exact-match validators rather than discovered by them.

| chokepoint | constraint | required action |
| --- | --- | --- |
| `statistical_foundations.py:660,663,666` | hard-coded arities 5/3/3 | new layer, not widened dataclass (§1.2) |
| `statistical_foundations.py:687` | positional untagged `vector` | keep for BC1; new layers expose named blocks |
| `orbit_nonlinearity.py:73,437,574` | `DEPARTURE_O3_PARITY` string equality | new parity contract string, versioned |
| `orbit_nonlinearity.py:478` | names must equal `PR251_INVARIANT_NAMES` | v3 spec is a new type, v1 frozen |
| `orbit_catalogue_v2.py:175,265` | frozen 12-tuple, exactly 12 values | v3 is additive and separately identified |
| `orbit_catalogue_v2.py:130-144,291` | `state_id` binds all floats + 8 metadata strings | `_state_payload` **must** be versioned, else every stored `state_id` silently invalidates |
| `mio/formalism/component_breakdown.py:32-41` | exact 4-key set, extras rejected | stays 4-key; the family lives beside it, not inside |
| `graded_nonid.py:40,50` | `SECTORS` 4-tuple, `EXPECTED_RANK = 2` | rank-2 is the *scalar-sector* statement; the tensor rank statement is a new registered quantity |
| `open_set_response_classes.py:749-766` | gate requires exactly `{LOCAL_BOOST, GLOBAL_TILT}` | the five-status refinement must extend `SourceSeparationGateStatus` in lockstep |
| `statistical_foundations.py:64` | `WEAKLY_IDENTIFIED` unused | free to define; wire per §6 |

Two migration rules govern all of it. **BC1**: every legacy statistic is preserved as the `φ = ⟨c,·⟩` instance, bit-identically, and the historical artefacts are untouched. **BC2**: a more expressive representation cannot promote a claim tier; the family's existence is tier-neutral until new channels or new data arrive.

---

## 9. Sequencing

| card | scope | depends | ceiling |
| --- | --- | --- | --- |
| **PR-259** | `CongruenceKinematics` + acceleration + convention typing + `JointAnisotropyState` adapter with mandatory `beta_semantic_role` | PR-252, PR-256 | `diagnostic_only` / C1 |
| **PR-260** | Catalogue v3: generation rule, Jacobian-rank acceptance, `K_ω` completion, stratification, four-axis CAS contract | PR-257, PR-259 | `conditional` / C2 |
| **PR-261** | Functional identity + `(x_φ, Q_φ, F_φ, Π_φ, G_{F,φ})` family with the §2.3 well-posedness table | PR-259, PR-260 | `diagnostic_only` / C2 |
| **PR-262** | `ConditionalExceedanceSurface` + partial-identification envelope + `OPTIMIZER_REQUIRED` refusal | PR-261, PR-250 | `diagnostic_only` / C2 |
| **PR-263** | Response-geometry status refinement (`WEAKLY_IDENTIFIED`), joint gate, `SourceSeparationGateStatus` extension | PR-256, PR-258 | `diagnostic_only` / C2 |
| **PR-264** | ZoA morphology path as a calibrated reverse-martingale sequential object + joint cross-cut covariance | PR-262, PR-263 | `diagnostic_only` / C2 |
| **PR-265** | Exact parity-sign test lane + `AnisotropyTypeReport` open-set fusion | PR-260, PR-264, PR-258 | `diagnostic_only` / C2 |

Each card inherits the established kill discipline: a missing component never becomes zero; an untyped conditioning is never accepted; a rank gain is never manufactured by scaling; a stress is never converted into an attribution; and no card consumes PR-151 partial acquisition data.

---

## Appendix A — Oracle receipts

`tensor_foundations_oracle.py`, seed `20260730`, twelve propositions, all `ok = True`, wall time ≈ 12 s.

**TF-01** parity typing — axial max abs error `1.47e-14`, polar `5.8e-15`, over 600 proper and improper transforms. **TF-02** witness closure — all twelve v2 polynomials identical on the witness; `K_ω = ±120`; candidate SO(3)-invariance verified (`4.3e-13`) *before* it is allowed to separate; commutant dimension computed as 3, stabiliser order 4 verified, zero spurious stabiliser elements in 2000 random rotations; scope recorded as non-generic-witness only, both `UNPROVEN` statuses unchanged. **TF-03** Krylov syzygy — max relative error `< 1e-8` over 400 samples, both against the Gram determinant and against its expression in the five even invariants. **TF-04** Cayley–Hamilton reductions. **TF-05** shape/discriminant — numeric identity residual plus an exact **symbolic** corroboration (sympy: discriminant residual `0`, gauge-identity residual `0`); empirical `J ∈ [−1, 1]` over 2 × 10⁵ draws with exact endpoints `±1` and `0`. **TF-06** invariant dimension — ranks `9/9/9/9/9` (12-dim), `12/12/12/12/12` (15-dim), `15/15/15/15/15` (18-dim velocity split), plus the off-stratum counterexample (single vector: naive `dim−3 = 0`, actual `1`). **TF-07** budget factorisation — gradient residual `9.5e-11`, helicity transverse fraction `≥ 0.38`, explicit witness. **TF-08** product gauge = max, bisection-verified. **TF-09** parity sign exactness — `P(ψ̂>0) = 0.4988 / 0.4980 / 0.5022` across the three nulls, even-statistic sd `3.18 → 54.8 → 116.0` (scale ratio 36.5), and the (H3) failure demonstration on `Δ_σ = 0` (max `|K_β| = 2.1e-14`). **TF-10** local/global ladder. **TF-11** mask path — direct conditional martingale test (defect `0.0070` for the correct path versus `0.153` for a deliberately non-martingale shrunk control), centred target verified, Doob bound holds at every λ for the correct normalisation and is violated by the naive per-rung renormalisation. **TF-12** acceleration Euler slaving — geodesic limit recovered exactly, radiation slaving factor exactly `1/4`, monotone in `c_s²`, with `gradient_regularity_registered = False` and the placeholder provenance recorded in the payload.
