# OBS03-SYNTH-v1: manufactured latent-modulus validation

The implementation passed the predeclared 128-replicate manufactured recovery gate. This is a coarse Monte Carlo check of approximate marginal Wald intervals under the specified synthetic law. It does not establish real-CF4 coverage, a physical forward model, or scientific admission. The far-shell-only diagnostic remains `NUMERICAL_HOLD` because its optimum reaches the prescribed A=-30 boundary; no finite interval is returned for that fit.

| Primary estimand | Covered / 128 | Coverage | Exact binomial 95% interval | Undercoverage lower-tail p | Bias Monte Carlo z |
|---|---:|---:|---:|---:|---:|
| B [km/s] | 121 | 0.9453125 | [0.890568, 0.977733] | 0.459286 | 1.146051 |
| A [km/s/Mpc] | 123 | 0.9609375 | [0.911196, 0.987197] | 0.772060 | -0.711629 |

There were zero failed, boundary, unstable-Hessian or unconverged-quadrature fits in the primary 128-replicate run. All replicates use order 64×48; each has a separate order 32×24 fit and checks at truth, initial point, optimum and interval-Hessian stencils. Maximum per-row selected log-density change was 3.3751e-14 against the frozen 1e-5 criterion. The largest total objective-call count was 27 against the cap of 600 per fit. The full validation took 88.44 seconds in the recorded environment.

## Likelihood and assumptions

[CONTRACT.json](CONTRACT.json) records the independently framed, controller-authorized manufactured contract and its pre-execution correction to the final parameter boxes. Each catalogue has 24 fixed slots: twelve icosahedron directions times two shells. Direction, shell and method labels are conditioned on. Integration uses independent uniform ell=ln(dA/Mpc) in a ±0.1 shell window and source u in [-150,150] km/s. The law z_true=(h+u)/c and dL=(1+z_true)^2 dA is applied jointly inside the integral. The quadrature measure is d ell du, so no additional c factor is inserted.

Conditional observed modulus and heliocentric velocity noises are independent Gaussian draws with the frozen synthetic sigmas. H=70 and all endpoint coefficients outside (B,A) are fixed. The observer transform is identity in the manufactured heliocentric inertial frame. No pre-corrected CMB-frame velocity is consumed and no CMB-rest-frame inference is made.

One calibration kappa is shared by all groups. One independent 0.03-mag anchor measurement enters the likelihood once per catalogue. Known method offsets are (0,0.03) mag. The synthetic anchor is not a measured CF4 calibration product or 24 independent row offsets.

Selected catalogues redraw the complete latent/noise tuple until each fixed slot satisfies its method-specific observed-modulus threshold. The likelihood includes each row's parameter-dependent selection probability integrated over the same latent law. Complete S=1 mode has normalization exactly one. The generator preserves proposal counts and fails at the frozen cap instead of dropping a slot.

Analytic likelihood scores drive bounded deterministic L-BFGS-B. The observed information is computed by central score differences with steps 0.02 and 0.01 in scaled coordinates (100 km/s,1 km/s/Mpc,0.05 mag). Both Hessians must be stably SPD and primary standard errors must change by at most 1 percent. The full 3×3 inverse retains shared calibration uncertainty; no non-SPD pseudoinverse is turned into finite intervals. Reported intervals are approximate marginal Wald intervals, without an exact Gaussian-coverage claim.

## Controls and diagnostics

`validation.json` retains all generated observations, exact slot labels, proposal counts, anchors, seed spawn keys, optimizer reports, estimates, intervals, Hessians and quadrature checks. PCG64 and SeedSequence(2026101303).spawn(128) determine the independent replicates.

Replicate 0 includes actual method0 and method1 omission refits with the same shared anchor and remaining rows' selection normalizers. Each retains twelve slots. Synthetic method means are never treated as second observations. Shell0 and shell1 are also actually refitted. The zero-shell-width controls have numerical rank two in (B,A,kappa), with only B+rA identified in the velocity block. Finite shell width can add weak information; its presence is not a guarantee of a stable fit. The shell1 boundary result is preserved in the pilot and final result.

The complete S=1 catalogue, selected catalogue with its normalizer deliberately omitted, and method1 plus 0.08-mag unmodelled mean injection are separate controls. The injected method1 groups are then actually omitted and the remaining sample refitted. Their contrasts are reported without requiring a particular noisy sign. The baseline run contains statistical noise only; the 0.08-mag injection is a fixed mean misspecification, distinct from a supplied physical remainder bound. No CAS07 remainder bound is asserted.

Truth/optimum local response SVD specializes the reviewed OBS-02 3×2 latent-block profiling to (B,A,kappa). Its source-motion RMS is a declared Gaussian proxy for the bounded uniform law's standard deviation; it is a local response diagnostic and is distinct from the integrated likelihood's observed information. Data-only and anchor-augmented observed curvature are also reported separately with scales and numerical tolerances.

`real_cf4_descriptive.png` and `.pdf` show actual method-presence/radial coverage and reviewed OBS-02 nuisance-aware sensitivity spectra. Real-CF4 source identities are recorded in `validation.json`. No actual CF4 response fit is performed. Method footprints overlap, deletion preserves DMzp, and these comparisons share groups. Real selection remains `SELECTION_LAW_NOT_BOUND`; real covariance, source-motion law, calibration mapping and physical frame/remainder gates remain HOLD.

## Execution and evidence

```sh
PYTHONPATH=htt:htt/htt:htt/src OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python -m pytest tests/htt/test_cf4_latent_modulus.py -q
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python scripts/cf4_latent_modulus_validation.py --pilot
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python scripts/cf4_latent_modulus_validation.py
```

Seven focused tests pass. They check slot geometry, reciprocity inside the latent law, normalized quadrature, analytic-vs-finite-difference scores, parameter-dependent selection/S=1/omitted-normalizer controls, the single shared anchor, domain rejection, quadrature refinement and method deletion, and the zero-width shell null. First test output is retained even though it passed. Pilot and final stdout/stderr, source hashes and command exit codes are preserved. The only runtime warning concerns unavailable matplotlib Axes3D; both requested plots are two-dimensional.

Owner: HTT. Transfer source: none. Claim tier: diagnostic only. Base commit: c3c2e5f00757d5e7c57d6df149db86f82dc59cfa. Requested coding runtime: gpt-6.1-sol/medium; observed model/effort: UNKNOWN. Independent Astra review is pending. No commit, push or publication was performed by this coding worker.
