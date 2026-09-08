# HTT R8 Local Codex implementation plan

> **For agentic workers:** Use `superpowers:subagent-driven-development` or `superpowers:executing-plans` where installed, under the actual current repository and workstation rules. Execute the graph task by task. Scientific production execution belongs to the workstation, not this design session.

**Goal:** Implement conservative full-tensor ranks and same-state physical confidence images, then run every qualified owned-data branch through a scientific conclusion.

**Architecture:** R8 successor adapters reuse R7 tensors, laws, confidence types, evidence binding, BASS dust and archive optics. New features are isolated by scope and validated capability; the final report consumes both successful and unavailable branches.

**Tech stack:** Existing Python/NumPy/FITS/healpy stack, current pinned exact arithmetic libraries, four independent CAS axes, existing optional kinetic/optics donors. No new general native Boltzmann solver.

**Spec:** [SCIENTIFIC_CONTRACT.md](SCIENTIFIC_CONTRACT.md), [THEORY.md](THEORY.md), [DESIGN.md](DESIGN.md), [VALIDATION_MATRIX.md](VALIDATION_MATRIX.md), and [campaign_dag.json](campaign_dag.json).

## Global constraints and intake

- Base `b7172ad904eb357fcce78eb9c5b7164d1e86a9e6`; create an isolated implementation worktree from this design publication. Verify actual branch HEAD before execution and bind any newer intentional source changes.
- Preserve R7 results, 31 donor pins, seven-obligation CAS scope, qiso historical interval and old full-plan STOP_INVALID. Import evidence only where sources/contract/law/config match; no wholesale rerun of the old Gaussian campaign.
- Follow actual `AGENTS.md`, canonical PR registration, context-pack/assignment and local bounded-work rules. Do not treat the portable research review as a native launch/stop receipt. If the documented wrong-checkout hook defect affects this run, perform the minimal proposed operational correction as a separately evidenced unit; no global bypass.
- `q0=o0=1e-5 K`, SO(3), `k=ceil(sqrt(M-1))`, single-pool alpha1/20. Joint confidence fixed allocations are CONTRACT item8. No alpha redistribution after missing-data outcomes.
- All planned modules/interfaces are in DESIGN. Input X is a pair `(Q,O)` of arrays with shapes `(3,3)` and `(3,3,3)` satisfying STF and units. `Bound.lo`, `.hi` and `.certificate` are the common bound interface; `.lo/.hi` in tests refer to computed-statistic enclosures, not sky measurement uncertainties.
- A node's `produces` entries require its actual validation and scope admission, not merely the presence of prerequisite metadata. `*_RESULTS` are scoped result collections, not automatic inferential eligibility. Every node emits a receipt on failure and settles independent scopes. Source presence alone cannot qualify a model comparison.

## Unit A — certified orbit bounds and rank decisions (R8-01/02/03/05)

**Files:** Create `htt/obsstat/r8_orbit_bounds.py`, `htt/htt/htt/infer/r8_interval_rank.py`, `tests/r8/test_orbit_bounds.py`, `tests/r8/test_interval_rank.py`. Reuse `htt/obsstat/r7_tensor_orbit.py` without altering the historical R7 method ID. Consume X/Y, dyadic input identity, prior interval and a split budget; produce `Bound` and `RankEnvelope` as DESIGN specifies.

- [ ] Record a new per-obligation CAS contract for O1–O3 and run its independent axes locally. A failure narrows this unit; it cannot inherit the old seven-obligation PASS.
- [ ] Write V01–V03 red tests. The rank helper `rank_from_score_bounds(bounds,observed,alpha)` is an internal public test entry point using the same O3 code path as `rank_envelope`; alpha is `fractions.Fraction`.

```python
def test_broad_intervals_can_determine_rank():
    from fractions import Fraction
    from htt.infer.r8_interval_rank import rank_from_score_bounds
    out = rank_from_score_bounds([(0,3)]*4+[(7,10)], observed=4,
                                 alpha=Fraction(1,20))
    assert out.p_lower == out.p_upper == Fraction(1,5)
    assert out.decision == 'NON_REJECT'

def test_inclusive_tie_is_not_upper_endpoint_rank():
    from fractions import Fraction
    from htt.infer.r8_interval_rank import rank_from_score_bounds
    out = rank_from_score_bounds([(0,1)]+[(0,0)]*30, observed=0,
                                 alpha=Fraction(1,20))
    assert out.p_upper == 1
```

- [ ] Run `python -m pytest tests/r8/test_orbit_bounds.py tests/r8/test_interval_rank.py -q` in the repo's established import environment; confirm missing implementation failure before implementation, not a silently deselected test.
- [ ] Implement the O1/O2 interval arithmetic, rational chart branch-and-bound and monotone pair cache. Implement kth bounds and exact integer thresholds. Pass V01–V03 and negative mutations; a local optimizer contributes only a feasible upper witness.
- [ ] Execute mock1 and mock3 exactly as the matrix specifies. Record unresolved cases/runtime as outcomes. Independently review the arithmetic enclosure boundary; commit a coherent validated capability.

## Unit B — complete representation and lossy ablations (R8-01/04/05)

**Files:** Create `htt/obsstat/r8_multipole_vectors.py`, `tests/r8/test_multipole_vectors.py`; extend new R8 reporting only. Consume STF tensors or amplitude+vectors; produce reconstruction enclosures and same-row comparison. Unit A does not wait for this unit's success.

- [ ] Write sign/permutation, rank2/3 trace subtraction and zero-amplitude tests, including this identity.

```python
def test_vector_sign_has_amplitude_compensation():
    import numpy as np
    from obsstat.r8_multipole_vectors import mv_to_tensor
    v = np.eye(3)
    w = v.copy(); w[0] *= -1
    assert np.allclose(mv_to_tensor(2.,v,3), mv_to_tensor(-2.,w,3))
    assert np.all(mv_to_tensor(0.,v,3) == 0)
```

- [ ] Run `python -m pytest tests/r8/test_multipole_vectors.py -q` for RED; implement null-cone polynomial/root pairing with amplitude normalization and repeated-root outcomes; run for GREEN.
- [ ] Execute mock2 and V04, retaining every tensor row on MV/packet refusal. Full-MV and tensor metrics must overlap within reconstruction bounds. Power/f_B/normalized alignments are named alternative statistics; do not claim a representation information gain.
- [ ] Record observed ablation only after the corresponding tensor product intake; commit this independent capability or an explicit incomplete-ablation receipt.

## Unit C — singular support, partial laws and actual generic dispatch (R8-08–12)

**Files:** Create `htt/htt/htt/infer/r8_support.py`, `r8_partial_law.py`, `r8_law_registry.py`, `r8_simulator_calibration.py`; create `tests/r8/test_support.py`, `test_partial_law.py`, `test_law_registry.py`, `test_simulator_calibration.py`. Reuse R7 factory/law/conditioning/contrast types. Modify the new runner, not old R7-19 evidence records.

- [ ] Add factor-support test: B=(3,4)^T/5, V=(4), on-support quadratic1 and off-support rejection from V06. Include rounded-support uncertainty as UNRESOLVED rather than exact rejection. Register normalized laws only with actual measurement/conditioning provenance.
- [ ] Add the following exact dependence counterexample to prevent marginal Gaussian information from selecting a joint Gaussian pivot: `Y=(Z,S*Z)`, Z standard normal, S fair independent sign. Covariance I and Gaussian marginals do not make the pair jointly Gaussian. J2a/J2b are admissible; automatic chi-square2 is refused.
- [ ] Run `python -m pytest tests/r8/test_support.py tests/r8/test_partial_law.py tests/r8/test_law_registry.py -q` for RED; implement normalized reduced support, fixed marginal allocation and moment acceptance; run GREEN.
- [ ] Implement product-keyed dispatch for CF4/JWST/Union3/DESI. The old qiso live-law join is the regression donor; no hardcoded result node ID. A changed law object cannot consume another object's calibration record even when string IDs match. Only law-authorized transformations of the original sampling variable enter a method.
- [ ] Write and run V09 toy selected/Student/mixture tests; implement candidate-experiment simulator ranks; execute mock4/5. Keep finite-grid/domain limits. Actual CF4/JWST simulator factories need their real selected law and shared latent distribution; passing the toy family does not qualify them.
- [ ] Run each admitted observed subset. Missing covariance may route to known marginal or moment laws only if their independent premises are supplied. Otherwise produce scenario/unavailable for that product and continue others. Commit tested dispatch and scoped results.

## Unit D — physical jet images and integrated confidence (R8-13–16)

**Files:** Create `htt/src/common/r8_jet_set.py`, `htt/htt/htt/infer/r8_confidence_image.py`, `tests/r8/test_jet_set.py`, `test_joint_region.py`. Consume the shared state, candidate acceptance interfaces and explicit compatible law/closure tuples. Produce certified outer regions, target-specific bounds and frontiers.

- [ ] Encode P1 first-order FLRW ordering and explicit finite-amplitude remainders in the new contract. R7 center-only return is preserved as a historical function, not reinterpreted as the image.
- [ ] Test zero jet/nonzero remainder, P2 support values, nesting in rho, unknown cross-dependence with fixed allocations, missing scope=whole domain, and law alternatives=union. `project()` includes every UNRESOLVED candidate in its outer result. A lower/upper optimization witness without global enclosure cannot exclude states.
- [ ] Run `python -m pytest tests/r8/test_jet_set.py tests/r8/test_joint_region.py -q` for RED; implement the declared ellipsoid/remainder support and exact affine/recession cases; run GREEN. General nonlinear projection requires interval/global optimization bounds; otherwise report unresolved outer bounds instead of fitting a nominal minimizer.
- [ ] Execute mock6; register the new independent P/J CAS obligations. Evaluate the fixed rho grid `{0,0.25,0.5,1,2,4}` plus unrestricted domain. More refined rho queries can tighten certified bracketing without changing the sensitivity family or treating rho as a fitted prior.
- [ ] Join only actual candidate-state acceptances from CMB and distance laws. If no CMB response/jet data exist, report the remaining subset and conditional closure image, not a CMB-informed physical interval. Convert legacy `x_C`, F and G_F through their actual normalization/denominator code and same-state definitions. Commit the independent image capability/results.

## Unit E — owned data and controls (R8-06/07/17)

**Files:** New runner intake/reporting and `htt/obsstat/r8_field_controls.py`; `tests/r8/test_product_intake.py`, `test_field_controls.py`. Reuse the inventory and exact adapters in ASSET_REUSE.

- [ ] Bind PR3 units/processing, fixed signal/noise IDs and removal/calibration response. Preserve observed carrier bytes if compatible; changed extraction creates a new method/input scope. Run V12 fixtures before actual tensors.
- [ ] Execute observed orbit bounds/rank only with law-qualified pools. Otherwise return descriptive Q/O/MV/packet/power/f_B comparisons and a law-specific refusal. Do not let a rank numerical PASS stand in for exchangeability.
- [ ] Read previously inventory-only PR3 components and owned flow products at common positions. Use matching PR319 grid semantics for its compatible released field; implement separately documented loaders for other formats. Out-of-support entries stay unavailable, not zero velocity. Verify unit, Galactic Cartesian axes, h scaling and outward radial sign with constant Cartesian field fixture `v=(1,0,0)`, giving radial projection `cos(b)cos(l)`.
- [ ] Run `python -m pytest tests/r8/test_product_intake.py tests/r8/test_field_controls.py -q`, inspect resulting same-sky and depth plots locally, and commit the useful controls even if no additional inferential law is admitted.

## Unit F — restricted physical provider (R8-18–20)

**Files:** Create `htt/bass/transfer/r8_restricted_history.py`, tests `tests/r8/test_r3_stress.py`, `test_r3_optics.py`. Adapt the three hash-identified archive members through an HTT wrapper and document license/version attribution; reuse exact dust/geodesic code. No generic native solver is introduced.

- [ ] Read R3_MODEL_REFERENCE N1–N29 and the exact donor headers. Replace the perfect-fluid optical history derivatives with the coupled R3 source. Do not silently alter the archived donor bytes; adapters keep provenance explicit.
- [ ] Write V10 wrong-rapidity and wrong-pi-scale controls, V11 flat/FLRW optics and reverse-ray tests. Run `python -m pytest tests/r8/test_r3_stress.py tests/r8/test_r3_optics.py -q` to establish RED, then implement stress history and channel adapters and run GREEN.
- [ ] Execute mock7 with stated units, energy fractions, grid and tolerances. The independent Einstein residual must reject pi_scale mutations that K3 cannot see. Test actual reverse rays; an endpoint algebraic identity is insufficient.
- [ ] Admit sky and distance channels separately with event/frame/domain/accuracy. Radiation derivative-jet export is explicitly INPUT_UNAVAILABLE in this bounded successor: emit `r3_jet_unavailable.json`, not a jet capability from optical tests. It needs the separately specified derivative/remainder validation described in DESIGN JetBoundary before a future scope can admit it. This does not block distance-model inference or generic closure sensitivity. Zero coherent odd multipoles and zero vorticity are expected model properties. Add stochastic sky only through a separate declared law. External providers get their own supported-channel comparison and never inherit R3 success.
- [ ] Commit the validated subset or no-channel receipt. Units A–E continue regardless of R3 outcome.

## Unit G — campaign runner, comparison and final scientific report (R8-00/21–23)

**Files:** Create `scripts/observed_runs/run_tensor_joint_r8.py`, `tests/r8/test_campaign_routes.py`; generated results under `docs/generated/tensor_joint_r8/<run_id>/`. Use current `r7_evidence` dependency binding rather than reproducing the earlier bug.

- [ ] Before dispatch, implement a dry plan mode that displays the fixed product/law scopes, capabilities, actions, allocations and intended output directory. It does not generate scientific PASS results.
- [ ] Test success, single-provider failure, input-all-unavailable and stale/missing current evidence. Every branch must settle with a receipt; synthesis consumes the receipts. A node's action guards are scheduling prerequisites; its own V tests and law admission still determine whether outputs gain eligibility.
- [ ] Test sibling survival at action/product level: valid distance plus unavailable jet still permits distance comparison; V07-valid finite images survive a failed V08 recession method; one missing CF4 covariance does not suppress an admitted DESI law. A jet-status receipt must never satisfy a derivative capability request.
- [ ] Run `python -m pytest tests/r8/test_campaign_routes.py -q`; then execute the ready scientific units in graph order with progress/checkpoints. Use branch-local bounded review/repair, not repeated assurance-only waves.
- [ ] Compare local-only/coherent/systematic and supported physical models with their actual response rank and full law. Rejected conjunctions, conditional bounds and nonidentification are valid outcomes. No model receives a likelihood from a failed competitor. Common data are consumed once.
- [ ] Generate the methods and scientific synthesis from current scoped results. Include historical qiso only under its unchanged conditional interpretation; report new observations separately. Inspect actual plots/PDF and apply the supplied figure audits locally. Record incomplete MV, law or provider routes accurately. Commit/push the resulting implementation branch according to the user's existing authorization and actual local policy; do not merge by default.

## First runnable instruction

Read this package, bind the source/evidence and actual local context, register the formal successor replan, then start **Unit A and Unit C** as independent useful capabilities. Unit D's exact set algebra can proceed in parallel; empirical physical images wait for qualified laws. The old wrong-checkout hook issue is corrected only if it actually blocks this local run. No request for a new research decision is needed for ordinary missing inputs: follow the named weaker/scenario/unavailable branches. A genuinely new physical assumption requires an explicit new scoped method/contract rather than an undocumented substitute.
