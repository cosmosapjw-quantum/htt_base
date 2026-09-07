# Theory-first execution contract for the next HTT campaign

Date: 2026-09-07. Current state: THEORY_IN_PROGRESS; production/data execution release is NOT issued by this document.

The owner now wants MAIN to finish the relevant theoretical and experimental-design decisions before one direct Local Codex handoff for implementation and data analysis. This file records completed mathematical contracts, actual reuse candidates and the few remaining scientific decisions. It is not an invitation for Codex to fill in a missing likelihood, choose a preferred result, decide what 'global tilt' means, or search for a convenient data release.

The target is a finite campaign: **quantitative low-multipole morphology and response-conditioned, redshift-dependent frame diagnostics**. Completing this campaign's theory is not the impossible requirement to finish every future Bianchi, remote-CMB or cosmological inference problem first. Conversely, publishing an algebra note does not imply the entire empirical campaign has been specified.

## 1. Scientific aims and non-claims

Keep three products distinct:

1. **Observable morphology:** a complete Q/O carrier, stable derived diagnostics, orientation information and calibration under an explicitly matched sky/noise/processing law. It may report departures from that law, not a unique spacetime source.
2. **Observer-response and nuisance inference:** exact finite-beta temperature response, the difference between unbounded, bounded and stochastic nuisance assumptions, and the incremental information from measured higher modes. It may constrain declared response coordinates or models, not equate a QO projection with a true intrinsic fraction.
3. **Redshift-dependent physical tests:** frame-labelled bulk/shear response contrasts using genuinely additional distance/tracer information and cross-covariance. A free shell field, a toy 'global' profile or a radial vorticity-null mode cannot be turned into a measured global tilt.

The ideal Beta law, soft-mask theorem and retained-model improved MES envelopes are mathematical validation oracles. Their direct use as observational p-values or unconditional physical bounds is prohibited. The old scalar-MES results remain retired; CF4 P0 quarantined headlines remain quarantined. Raw data can be reconsidered under a new valid model without reviving those outputs.

## 2. Completed theory contracts ready to consume after integration

### A. Exact/model algebra

Implement the formulas in THEORY_RESULTS as small tested consumers of the existing tensor/boost code. No reimplementation of STF projection or the accepted inverse chart merely to create a new framework. Keep complete tensors before scalar summaries; values from different metrics must be explicitly adapted.

Input types:
- Q: finite symmetric trace-free 3-by-3 temperature tensor; O: finite symmetric trace-free 3-by-3-by-3 tensor, full Frobenius metric.
- Amplitudes nonnegative; zero-amplitude or unavailable cases are explicit states, not NaNs submitted to a rank function.
- beta: finite three-vector with norm below one for the exact physical transform; an unrestricted linear algebra fit is labelled an algebraic coordinate, not silently forced into that physical domain.
- Response matrices carry input/output parameter types, units, frame, retained/source multipoles, mask/transfer order and source identity. Array shape alone is not physical identity.

Required limits/oracles:
- unit-q trace inverse in [20/9,9/4]; spectra (-1,0,1)/sqrt(2) and (-1,-1,2)/sqrt(6) attain the endpoints;
- Beta CDF endpoints 0 and 1, density nonnegative, tail at 0.8 approximately 0.06979572136008738;
- Gaussian versus fixed-amplitude nulls labelled separately, both spherical relative to a fixed Q;
- exact boost at beta=0 is identity; inverse-direction sign and monopole beta-squared term checked against the specified convention;
- soft mask epsilon=0 has zero high-band boost leakage; the existing axial certificate implies L=10 full rank, without inventing finite-pixel certification;
- the model-specific cancellation and STF contraction norm use the actual operator envelopes of Appendix E, not an uncontracted derivative bound;
- known-matrix error membership plus a certified singular value above one is sufficient; no new universal preregistered numerical slack gate.

### B. Bounded/stochastic/conditioned nuisance

Expose separate functions, not one function with an undocumented prior switch:

- `minimum_nuisance_cost(d, K, S)` returns exact-model range residual, minimum norm/cost and singular scales; outside range gives an explicit infeasible result. It does not declare the range from an arbitrary tolerance without recording numerical error.
- `bounded_pair_ambiguity(theta1, theta2, A, K, S, R)` uses 2R for the difference of two nuisance states; the single-zero-reference version uses R and is differently named.
- `gaussian_joint_condition(mean, covariance, split)` uses the full joint block matrix. A Cholesky solve is preferred to explicit inversion. Singular/noiseless limits require their explicit constrained formulation rather than adding undocumented jitter.
- `mean_response_fisher(A, C)` is used only when C is independent of the fitted parameters. The full Gaussian implementation includes covariance derivatives when beta changes the mixing.

Test with equal-trace, differently oriented nuisance matrices; a covariance-trace shortcut must fail. Test C_yz=0, nonzero cross-covariance, an increasingly accurate high-mode measurement and a parameter-dependent high-mode mean. Verify the joint versus conditional likelihood relation; do not count an input twice.

### C. Redshift and statistical invariants

- A radial affine response has bulk, isotropic expansion and symmetric shear columns, but zero columns for rigid rotation about the observer. Return its nullspace explicitly.
- The simple observer/global-shell frame gauge in T9 is a required negative control. More bins must not magically remove it.
- Inverse-inclusion weights, quadrature weights, frequency counts and inverse-variance precision are different enumerated roles. A requested unsupported combination fails with a typed explanation rather than changing the likelihood silently.
- Fixed-covariance design weighting uses the sandwich uncertainty and is invariant to common positive rescaling of design weights. A genuine precision model has its own scaling, documented separately.
- Pooled-rank inputs must be finite, and the full row operation includes fitting, mask choices, anchor construction, chart policy and any scan. Null rows remain complete correlated realisations. No p=0 or significance finer than 1/(N+1).
- Common rotation of both Q and O preserves orbit invariants; it is not a useful null randomisation of those invariant scores. Relative rotation is a different conditional null and requires a symmetry argument for the actual processed data.

## 3. Three remaining MAIN theory decisions

These are genuine scientific decisions, not remaining bureaucracy or tasks to ask Codex to research.

### M1 — Freeze the CMB observation/foreground/null law

Deliver one actual mathematical specification tying the selected PR3 products to their complete ordered transform and the joint low/high likelihood or matched simulation procedure. Resolve:
- whether a quantity is an absolute processed sky, a boost difference, a pseudo-alm or a simultaneous weighted-fit coefficient;
- release dipole, kinematic-quadrupole and FFP10 boost conventions, including intensity-to-temperature effects;
- intrinsic-sky/foreground/noise covariance and the same-data high-mode cross block;
- primary morphology statistic(s), nuisance treatment, fixed scan family, null-data dependence and calibrated effect-size target;
- a justified finite source cutoff/tail and numerical error criterion for the chosen mask, rather than a universal L=30 guess.

M1 must choose a primary analysis and label sensitivity analyses separately. PR3 is the default candidate because it has a reusable paired-simulation lineage; PR4 cannot be silently substituted while its inventory is incomplete. The exact usable pairs are selected from a validated manifest, not from a directory count. A full all-strata observable carrier remains available even if the cyclic decoder abstains; the final statistic's policy must be specified in MAIN.

### M2 — Freeze the redshift physical response and likelihood

Deliver the forward law for the actually selected distance/redshift or tracer product, not just a Gaussian bulk-flow label. Resolve the distance-indicator/error convention, calibration groups, selection function, Malmquist/lognormal effects, observer-frame correction, shell windows, response parameters and their joint covariance with external density reconstructions. Decide the target functional before seeing a fitted direction.

The primary choice should use existing primary catalogue data where suitable, not multiply several correlated velocity reconstructions. A reconstructed product can enter only as a declared conditional model or sensitivity. New intrinsic-dipole versus observer-velocity separation requires an independently justified high-ell/spectral/other response; no profile chosen for software convenience may stand in for global tilt dynamics. Radial vorticity null directions remain null unless a genuinely different response is supplied.

M2 may decide that an unavailable physical parameter is only partially identified. That is a valid theoretical closure if the reported identified set and every additional assumption are specified; it is not an excuse to replace it by a scalar anomaly score.

### M3 — Freeze the end-to-end calibration and finite experiment

Compile M1/M2 into one finite execution table: exact estimands, masks/bins, training/validation roles, primary and secondary outputs, simulation pairing, treatment of foreground/component alternatives, fit hyperparameters, uncertainty/coverage tests and rejection/abstention branches. Preserve within-row and cross-survey dependence. No all-reconstruction majority vote or post-hoc best catalogue.

A noise-matched finite null and a posterior draw are different objects. Use exact finite ranks at their actual resolution, or a separately justified likelihood/inference method. Error-control and multiple-testing statements must refer to the full selection procedure. Planned effect/power and failure thresholds are fixed here; numerical residual tolerances are justified by conditioning/error analysis, not by a desired result. Budgets are planning estimates with cumulative accounting and reasoned adjustment; explicit owner/platform limits remain distinct.

The exit of M3 is an actual complete execution contract, not a generic 'audit passed' flag. The current pack does not yet supply those survey-specific choices, so `THEORY_FREEZE` is pending. The next MAIN work is M1, then M2/M3, reusing T1–T10 rather than repeating this whole review.

## 4. Codex campaign after THEORY_FREEZE

Only after the completed M1/M2/M3 specification is published does MAIN issue the final execution handoff. Local Codex then performs the following without choosing new science:

1. **Integrate existing code.** Resolve the explicitly selected donor commits and import paths into a clean isolated candidate. Preserve original source/evidence. Use exact native/source-equivalent distinctions, run only affected inherited tests and new regression oracles. Do not rebuild all old proof environments.
2. **Implement the frozen interfaces.** Bounded cost, joint conditioning, exact finite-beta pipeline, frame-labelled radial response and typed weighting/rank admission are code tasks under the published mathematical contract.
3. **Synthetic validation and injection.** Use fixed models, seeds and parameter grids from M3, retain coupled low/high draws and nuisance controls. Verify analytic special cases before observed fitting. Failure is diagnosed and repaired within unchanged mathematics, not by enlarging acceptance tolerances or changing the target.
4. **Intake selected data.** Consult the existing inventory first, read only selected headers/manifests and verify needed bytes/units/releases. No full 1.5 TB rehash, package census, new mass download or inference from file count. Missing required inputs cause a specific product-level stop; no alternative scientific dataset is chosen autonomously.
5. **Run the specified observed analysis.** Execute the full fixed procedure once appropriately validated, followed by its predeclared robustness/injection/coverage outputs. Compare coordinate/effect/uncertainty results, not just PASS counters. A statistically null or unidentified result is a valid outcome.
6. **Return and publish.** One source writer, one isolated branch with non-force push/Draft PR, actual readable source/diff/receipts/logs/results and `RETURN_TO_MAIN.md`. Keep large raw survey data, credentials, private corpus/style and fonts out of Git. Return immutable links to MAIN; no WORK_THREAD or manual ZIP relay.

The executor is allowed to reason about and correct ordinary code, loader, data-parsing and numerical defects. 'No additional scientific research' cannot mean 'no debugging'. A needed change to the physical model, priors, selection law, target statistic or protected claim is a precise MAIN boundary. Do not quietly choose one to make the run succeed.

## 5. State now

Completed here: critical adjudication; explicit T1–T10 derivations; scalar arithmetic checks; global structure and focused implementation audit; asset-to-lane classification; concrete semantic regression oracles; this theory-first DAG and execution boundary.

Not completed here: native code/tests/CAS, full data-content inspection, M1/M2/M3 empirical-model freeze, implementation integration or observed analysis. No completion percentage with an invented denominator, no new research-paper acceptance, and no dispatch of a local session is claimed.

The accepted 55-page educational report and 29-page evidence-integrated report remain completed document artifacts. The new campaign is scientific upgrading, not a reason to relabel those artifact tasks unfinished. Its code/data release waits for genuine theoretical specification, as requested by the owner.
