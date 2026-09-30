# Pre-data formalism mapping, 2026-09-30

Read-only scout findings for the primary writer. No production edits, test executions, scientific suites, external datasets, or new scientific admission were performed here. Reviewed source was initially the `3aeecb100d9b938bfffdade093ae8938d84efcfd` subset. The current work subset rooted at `/workspace/scratch/83eeacddad29/htt_port_20260930/work` was subsequently byte-compared for the two AGENTS files and the ten central anchor/statistical/response/depth/law/pushforward modules; all compared files were unchanged. Root owns verification of remote `efbd6d39b1167afcf40f3d07af0b5552747f3611` and its DATA-01 delta.

## Decision

None of the proposed F1–F7 named general adapters is implemented under its proposed name in the reviewed subset. Most of their hard numerical foundations already exist. The useful change is a small, executable adapter layer around existing geometry and HTT laws, with finite explicit domains and synthetic acceptance examples. It is not another approval/registry layer.

The prior map's data-first rollout is historical planning, not a reason to ignore the owner's newly authorized pre-data code inheritance. Implement bounded supplied-input calculations now; actual observational providers and numerical analysis remain absent. Preserve I2 `DEFENDED_CONDITIONAL`, I3 `HOLD_INPUT_INCOMPLETE`, and unavailable observational Q/F/Pi/G_F/MES percentages.

## Evidence read

- Root `AGENTS.md`, `htt/src/common/AGENTS.md`; repository skills `htt-xqpi-fg-formalism`, `htt-statistical-hardening`, `htt-local-global-discrimination`, `htt-claim-firewall`.
- `analysis/formalism_map.md` and `analysis/formalism_map.json` from the 2026-09-29 preparation; these include historical caller evidence, not a substitute for current code.
- Full `depth_path.py`, `tensor_functionals.py`, `joint_feasible_set.py`, `r7_gaussian_law.py`, `r9_depth_law.py`, `physical_pushforward.py`, `r8_jet_set.py`, direct R9 depth/fiber tests, PR04 pushforward tests.
- Relevant typed-body construction, gauge, margin, finite-family and J1/J2 sections of `anchor_geometry.py`; covariance support, normalizer, response API and identified-set contraction sections of `anchored_response_geometry.py`.
- Relevant anchor, state, finite-generator support, sector-stress and quadratic result sections of `statistical_foundations.py`; sample and builder sections of HTT `posterior_pushforward.py`; ExceedanceCurve constructor and measure/threshold APIs; PR142 `mio_joint_measure.py` definitions; current fixed `conditional_source_image.py` facade and algorithm.
- Full `typefree_loop2_20260928/source/RESEARCH_ARCHITECTURE_KO.md`, `ADJUDICATED_AMENDMENTS_KO.md`, and closeout `ERRATA_F1_W1_KO.md`, `ERRATA_F3_LEAN_SCOPE_KO.md`, `CLAIM_CLOSEOUT.json`.

This is a targeted implementation read, not a whole-repository or all-lines read of every large historical module.

## Implemented versus missing

| Task | Existing executable capability | Smallest missing increment |
|---|---|---|
| F1 paired functionals | Metadata-rich legacy scalar and irreducible states; fixed TensorRecord/RadiationJet/PhysicalState; immutable numeric-array utility | Generic immutable functional definition and per-latent output/reference/body binding, with explicit legacy adapter |
| F2 body/gauge/support | Product balls, PD quadratic ellipsoid, symmetric bounded H-polytope; gauge; signed margin; finite body families | Same-latent pairing, support evaluation, explicit relative-span and zero-span branches |
| F3 joint image | Finite nonnegative MIO exceedance and weighted HTT legacy scalar summaries; normalized Gaussian law | Finite joint-law/set image preserving undefined atoms and their mass; strict scalarized exceedance without survivor renormalization |
| F4 constrained fiber | Fixed 3x7 STF contraction fiber; rational bounded-polytope support; vertex/recession support | General finite linear ellipsoid fiber and quotient witness, bounded rational polytope equality slice |
| F5 signed depth | Invertible initial-plus-contrast map; all cross covariance blocks; original-law transformation; whole-past innovations | Functional semantics, signed contrast/coherence output, thin HTT integration |
| F6 full-law control | `JointObservationLaw` supports mean, covariance at state, domain and normalized log density | Gaussian pair comparison with domain checks; synthetic same-mean/different-covariance and duplicate-depth negative controls |
| F7 P2/W1 | Legacy MES sector anchors, typed jets and derived first-jet material | Supplied stress-gap conditional body; supplied-integral weak response and finite error arithmetic, linked to F4 |

## F1: minimal shared pairing surface

`common/typefree_functionals.py` is a sensible initial owner for immutable shared values and mathematical transforms. Keep HTT law/posterior integrations under HTT; common must not import HTT or MIO.

Suggested core contracts:

```python
FunctionalSpec(definition_id, output_shape, coordinate_labels, rank, parity,
               basis, units, frame, epoch, domain_id)
FunctionalRecord(latent_id, spec, values, reference, body, status)
```

Raw tensor values must remain available; flattening into a declared basis is an explicit operation. `values` and `reference` have exactly the same shape. Their same record binds the body to that latent state. Prefer carrying the typed body itself (plus ID) over separate positional arrays whose independent permutations create false pairing. Missing values/reference/body have typed status, never a zero surrogate. Reject nonfinite available values and duplicate latent IDs in one joint source. Tuple storage or owned immutable bytes prevents caller mutation.

No new 18-component physical carrier is required in this scout's slice; coordinate with the first-jet/observables writer. The old `DepartureState` has 12 coordinates (sigma5, omega3, beta3, curvature1), not the new 18 representation coordinates. Do not assert a physical inversion or the unresolved equality between old scalar x and every new functional.

Definition IDs must distinguish at least legacy signed x_C, legacy scalar Q, legacy samplewise F, PR142 RMS F/first-moment Pi/feasible-range GF, successor gauge Q, support-utilization F, declared-law exceedance Pi, and signed transport G_F. A shared letter is not a conversion. Keep R2 tensor outer product/tensor-tail/F_rad/G_rad as separate derived aliases.

Acceptance: an existing MIO scalar consumer exports unchanged values with its legacy definition ID; arbitrary record permutation does not cross-pair values/reference/body; incompatible spec/frame/units fail closed. Actual consumer integration matters more than an unused registry.

## F2: reuse gauge, add relative body and support

Critical convention: `AnchorBodySpec.quadratic_form` is Q in `{y:y^T Q y<=1}`, and the current gauge is `sqrt(y^T Q y)`. `matrix_budget_radius(samples,budget)` instead interprets budget as PSD shape U and returns **squared** `y^T U^+ y`. Its direct test pins `[1.5,2]` for x=`[[1,2],[2,0]]`, U=`diag(2,4)`. Preserve that API.

An economical relative-body representation is an explicit orthonormal column embedding S and an existing full-dimensional body in its relative coordinates. Validate channel metadata; then check `y` belongs to `range(S)` before evaluating `S.T @ y`. Do not discard a nonzero residual merely because the pseudoinverse gives zero. Floating membership near the numerical error bound is unresolved, not certified membership. An explicitly declared exact structural support is preferable to silently discovering physical support with a configurable eigenvalue truncation.

- Zero columns: y=0 has gauge 0 and membership true, but directional profile is `NO_DIRECTIONS`; y!=0 is `OUTSIDE_RELATIVE_SPAN`.
- A PSD shape adapter first establishes relative span, then uses Q=(S^T U S)^-1 inside it. Do not replace Q with U.
- Product-ball support is `sum_j radius_j * norm(direction[block_j])`.
- PD ellipsoid support is `sqrt(u^T Q^-1 u)`.
- H-polytope support can use `joint_feasible_set.exact_support` on exact rational representations of the supplied coefficients, with boundedness already established by the body contract. A floating LP may cross-check but is not the exact authority.
- Signed utilization is `(u dot (value-reference))/support`. No absolute value of the numerator, no clamp to [0,1], and no denominator floor. If u has zero restriction to the relative span, support is zero and the ratio is undefined.
- The additive margin is 1-gauge and remains negative outside the body. Existing raw excess `max(gauge-1,0)` is a distinct quantity.

Existing `AnchorFamily.FINITE_CONDITIONAL` evaluates many bodies against **one fixed vector**. It does not implement paired body/vector uncertainty. Evaluate per record and only then aggregate. Finite extrema are extrema of the supplied finite source; do not call them a continuous supremum.

Acceptance: U=diag(4,1), y=(2,0) gives gauge1/radius_sq1; y=(4,0) gives gauge2/radius_sq4 and margin-1. U=diag(1,0), y=(0,1) is outside support. Same Euclidean norm along two anisotropic directions produces distinct utilization. Origin in zero-span gives `NO_DIRECTIONS`. Reproduce J2 equal-marginal different-coupling exceedance.

## F3: finite joint pushforward with undefined mass

Implement the finite interface honestly: one finite weighted joint measure or one finite set is mapped point by point. This does not construct a calibrated law from covariance or make a finite sample the exact image of a continuous confidence set.

Suggested result retains `joint_id`, `law_kind`, ordered `latent_id`, mapped value or undefined status, original normalized mass, definition ID and declared target/domain. Normalize the **original** nonnegative finite weights once using the complete source total. Preserve zero-denominator/nonfinite-transform/missing-anchor atoms and their original mass. Do not silently drop them and renormalize. For `>` exceedance report known event mass and undefined mass separately; an event-probability interval is [known mass, known mass+undefined mass] unless the event assigns an explicit value to the undefined atom. If all map values are defined this collapses to ordinary strict exceedance.

A finite joint draw/atom table already represents dependence. It does **not** require an additional covariance to carry pairing. Complete cross covariance is required only when building a covariance-based joint source; do not add an unnecessary covariance gate to empirical finite atoms. Independently paired marginal arrays are not a joint source.

An empty finite set has `EMPTY_SET` image. An empty probability measure is invalid/unavailable, not a zero-probability empirical law. A positive-denominator restricted domain must retain its changed target and, for a probability law, its conditioning mass. Never advertise unconditional coverage after conditioning.

The existing HTT `PosteriorPushforwardSample` accepts F only in [0,1], G_F strictly positive and finite x/Q; it cannot represent successor signed support F, undefined atoms, or zero directions. Do not stretch that frozen legacy contract. Add a thin HTT posterior functional adapter to the shared pure transform, leaving existing legacy report behavior intact. Likewise MIO `ExceedanceCurve` is an unweighted nonnegative diagnostic scalar consumer and rejects HTT posterior source kinds.

Repair `mio.formalism.physical_pushforward.ratio_pushforward` narrowly: validate finite input and finite output and finite nonnegative zero_guard; return a blocked nonfinite status instead of `OK` with NaN. Preserve its finite broadcasting, zero_guard semantics, and existing tests. The generic joint-law transform handles partial undefined mass; the legacy summarizer need not be redesigned.

Acceptance: ratios (1/1,2/2) have strict >1 mass0, ratios (1/2,2/1) mass1/2 under identical marginals. Mean of sample ratios differs from ratio of means. Values [1,undefined] at weights [.25,.75] retain undefined mass .75 and known >0 mass .25, not 1. NaN is never OK. Strict equality to threshold is not an exceedance.

## F4: actual finite fibers and minimum-gauge witness

The local response geometry API's `global_feasible_set_status` is literally `NOT_COMPUTED_NO_FEASIBLE_SET_INPUT`. Keep that meaning; new F4 is an actual separate computation.

For an ellipsoid K={c+Lz:||z||<=1}, observation Bx=y, and target P:

1. Set A=B L and b=y-Bc. Require b in range(A); otherwise the fiber is empty.
2. Compute the minimum norm solution z0=A^+b and eta=||z0||². eta>1 with resolved error is empty. A numerically ambiguous rank or eta≈1 is unresolved unless an exact structural boundary is supplied.
3. Let N have orthonormal columns spanning ker(A). Target image center is `P@(c+L@z0)` and shape is `(1-eta)*P@L@N@N.T@L.T@P.T`.
4. Support in direction u is `u dot center + sqrt(u.T @ shape @ u)`. Return a feasible lift witness for requested support directions where resolved.

For quotient body with shape U and actual linear output map p: V=p U p^T, require v in range(V); `gamma²=v^T V^+ v`, minimal lift `U p^T V^+ v`. Return the witness and numerical support/rank status. Unit disk p(x,y)=x yields gamma=abs(v), lift=(v,0); hidden lifts can have larger gauge. The algebraic body minimum is not identification of the physical hidden state.

For a bounded rational H-polytope K={Ax<=b}, append Bx<=y and -Bx<=-y. Target support direction u is old exact support at P^T u. Existing `exact_support` enumerates vertices and has a **boundedness precondition**; its no-vertex exception says empty or unbounded. Only call no vertices `EMPTY_SET` if the original K is already known bounded. Do not use `identified_set.numeric_engine` big-M clipping as an unboundedness certificate. Keep existing 3x7 fixed-STF contract unchanged.

Corrected W1 boundary: for unconstrained/affine variation spaces only, kernel inclusion gives a uniform operator bound. For general bounded K, directly evaluate `P(K intersect B^-1{y})`. B=0,P=id,K=[-1,1] is bounded but nonsingleton. It does not fail merely because the ambient kernel inclusion fails.

Acceptance: unit disk projection/minimum witness; bounded interval with B=0; impossible equality gives EMPTY_SET; zero-dimensional quotient gives gauge0 and `NO_DIRECTIONS`; unsupported curved/nonlinear K gives unavailable. A separate unconstrained affine helper may report unboundedness only from an explicit recession/null witness, never from finite big-M bounds.

## F5: signed transport and covariance once

`DepthRepresentation` already constructs H of adjacent `next-K@previous` contrasts and invertible T=(initial,H). `full_covariance_blocks` requires **every ordered block**, including explicit transpose blocks, and returns None for missing blocks. `r9_depth_law.depth_law` transforms one original full law with T, never creates an independent contrast likelihood. `full_past_innovations` conditions on all earlier original blocks, not only the adjacent block.

Common's thin functional adapter can return H@values, H@reference, H@C@H.T, and optionally T@values/T@C@T.T, attached to functional and paired latent IDs. A signed coherence statistic may be the declared normalized inner product between K_j y_j and y_(j+1); this is -1 for exact reversal and is undefined at zero norm. Its uncertainty must come from the same joint draws or explicitly declared nonlinear propagation, not a covariance magically treated as a full distribution. Do not estimate tensor transport from labels.

HTT integration stays under HTT and invokes the existing R9 functions. Fixed transport is eligible under the supplied known law; `FITTED_REQUIRES_JOINT_LAW` remains scenario-only in the current R9 adapter. Arbitrary path reorder is not an invariance by itself: permutation covariance/operator must represent the same physical edges and reference. Test simultaneous coordinate/permutation changes with that meaning.

Acceptance: identity map, retained signed reversal, consistent map/value/covariance permutation, one missing cross block blocks joint covariance output. Keep G_rad for q(L)=sL separate: its squared norm ratio is (L/L0)² for L0>0. No elapsed time or evolution law from redshift-bin names.

## F6: full law, not response rank

Smallest executable HTT helper: compare one `JointObservationLaw` at two supplied states and nuisances, first checking both belong to its `domain_contains`. For a declared Gaussian law, compare both mean and covariance on the same ordered observation contract. Exact structural/equal-array equality is a conservative finite computation; `allclose` is not proof of equal laws. Near equal but numerically undecidable results should remain unresolved. Non-Gaussian normalized density callables need their own equivalence argument, not a few evaluated log densities.

Test linear mean mu0+Rk+Neta with Rh=Nc: state pair (k,eta),(k+h,eta-c) has identical Gaussian law when covariance is the same and both are admissible. State-dependent covariance provides the negative control. Duplicating identical depth response rows preserves the same parameter kernel. Domain constraints can exclude the compensating state.

Existing R7 singular support must remain exact-support aware: a small covariance eigenvalue inside the error enclosure is unresolved, and null residuals cannot be repaired with jitter. Anchored response geometry intentionally uses a different correlation-standardized user-declared support quotient. Do not combine these rank policies as if interchangeable.

Confidence-diameter lower bound `max(0,1-2alpha)` can be evaluated as conditional arithmetic only when the two distinct admissible target values share the same full law and each coverage premise is supplied. It is not validation of actual calibration. The historical Lean proof covers selected set/measure/union-bound pieces, not this entire inference stack.

## F7: supplied-input calculations, not physical providers

P2 can be useful code now even though its observational inputs are absent. Given finite positive c and delta_star, finite nonnegative d_star and a declared same-state smooth symmetric stress/eigenbranch contract, compute B_star=c*d_star/delta_star. In coordinate order (theta,sigma5,omega3,A3), the rate quadratic is:

`theta²/3 + sum(sigma²) + 2*sum(omega²) + sum(A²)/c²`.

For B_star>0, the body has Q=diag(1/3,1×5,2×3,1/c²×3)/B_star². For d_star=0 the body is zero-dimensional, handled by F2 rather than dividing by zero. The norm of D is the positive observer norm across all 4 derivative directions and 3 spatial components, not a Lorentzian contraction. Missing gap/derivative budget gives unavailable. A helper receiving upper bounds computes a conditional body; it does not verify that those upper bounds hold physically.

Keep this external conditional stress body separate from original geodesic MES anchors. `registered_geodesic_mes_anchors` intentionally returns `NO_MES_ANCHOR` for acceleration and curvature. Total Einstein energy-frame stress need not be dust/matter congruence. Cross-body use requires component/frame/congruence/epoch/units/same-state compatibility.

The smallest honest W1 interface accepts actual supplied finite-window integrals and endpoint traces:

```python
weak_window_from_integrals(Abar, integral_ws, integral_wprime_m,
                          wa_ma, wb_mb, variation_integral, L, ...)
```

Return K_w=integral_ws+integral_wprime_m-(wb_mb-wa_ma), epsilon=L*variation_integral, where variation_integral is ∫|w| ||A|| |t-t0|. Supplied quadrature/numerical errors add to epsilon rather than disappearing. An optional coefficient perturbation integral ∫|w| ||delta A|| requires finite supplied M_k bounding ||k|| and adds M_k times that integral. Without M_k it cannot become a finite residual error. Hand the resulting linear response/residual set to F4 when supported.

If integrating sampled functions instead, label the chosen quadrature approximation and require its error bound before treating it as the continuous weak identity. Do not claim trapezoid evaluation alone proves the integration-by-parts equality. Zero window endpoints remove only the boundary term; they do not eliminate source or moment integrals. L=0 eliminates only the variation error, not the response kernel or other supplied error.

Acceptance: supplied constant/polynomial examples verify signs and endpoint subtraction; zero endpoints; missing derivative/source/gap returns unavailable; finite uncertain-A error only with finite k bound. No optics, Boltzmann, ODE/PDE closure, actual source law or sky inversion is introduced.

## Focused validation and stop boundary

No tests were run by this mapper. Primary writer should execute the new direct common tests and the smallest affected legacy consumer tests: PR04 physical pushforward, existing anchor geometry PR254, direct R9 depth/fiber tests, affected HTT R9/full-law tests, and the actual new MIO/HTT adapters. Broader scientific suites, observed-run scripts and external-data loaders are outside this port.

Stop numerical output at unsupported domain, undefined atom, missing body/cross block, unresolved support/rank, fitted transport without its joint law, or missing physical provider. Preserve historical claims and raw evidence. Completion is executable supplied-input behavior plus focused acceptance, not a new science verdict or a new admission bureaucracy.
