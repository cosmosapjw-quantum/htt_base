# R60 independent code and science review

Date: 2026-11-17. Review mode: independent, read-only source and existing data; bounded one-thread checks. **FINAL VERDICT: PASS within the declared code/science scope. F01 and F02 are CLOSED; no unresolved material finding remains.** Actual-data oracles, radial/Commander/count additions, theory and interpretation documents, small text corrections, and final regenerated provenance are complete. Initial failures and all targeted closeouts are preserved below; the final receipt at the end controls the current verdict.

## Initial verdict (superseded by targeted F01 closeout below)

**Specification: PARTIAL. Engineering: FAIL for the default legacy amplitude consumer on a reproduced valid 400-mode input.** The current R60 32-dimensional numerical products pass the independent scientific checks listed below. No physical-shear, Bianchi-family, fitted-covariance significance, global axial-minimum, or composite-null chi-square claim is established.

There is one material, confirmed Medium finding. It does not invalidate the existing 32D R60 numerical output, but it prevents an unconditional completion claim for the shared amplitude repair and its legacy consumer.

## F01 — Medium / high confidence: default global search exhausts its budget at an existing consumer's dimension

Affected sources:

- `htt/src/common/covariance_amplitude.py`: default `max_intervals=200000`; termwise upper bound and splitting at lines 67–106 in the reviewed hash.
- `htt/obsstat/cf4_growth_covariance.py`: `amplitude_mle` lines 118–133 delegates with the fixed default tolerance and search budget.
- Existing consumer scale: `tests/contracts/test_pr148_growth_covariance.py` lines 99–102 use 1,200 objects in three shells, i.e. 400 modes per shell. `joint_covariance` lines 185–201 repeatedly calls the same estimator for every mock and shell.

Minimal deterministic valid-input falsifier:

```python
rng = np.random.default_rng(600400)
lam = np.geomspace(1e-2, 1e2, 400)
p2 = (1 + lam) * rng.chisquare(1, 400)
maximize_covariance_amplitude(p2, lam)
```

These are positive eigenvalues and squared independent Gaussian coordinates under amplitude 1. On the reviewed source and `/usr/bin/python` runtime, execution ended after **37.72214473699569 s** with:

```text
RuntimeError: covariance-amplitude global objective gap unresolved at max_intervals
```

The harness caught the exception to preserve the evidence, so the remote command itself exited 0. This is an implementation/algorithmic resource failure for a valid numerical input, not an invalid-input failure or environment failure. It is not evidence that the actual PR148 catalogue shell has the same spectrum; that expensive pair-sum experiment was deliberately not rerun.

Consequence: the unchanged public legacy consumer can now raise instead of returning a fit, and it exposes no tolerance or search-budget override. Its mock covariance loop may fail or become prohibitive even though the fixed-mean Gaussian likelihood is regular.

Minimum remediation: tighten the valid interval upper bound and add this exact regression, or expose and justify an appropriate numerical tolerance/budget in the legacy path while still failing honestly when unresolved. Do not restore the invalid monotone-score or negative-boundary-score shortcut. A valid tighter bound can combine the existing separable bound with a Taylor bound using the aggregate score and a rigorous absolute-curvature bound. The author has acknowledged this finding; closeout is pending.

## Target and identities

Primary checkout: `/home/cosmosapjw/Dropbox/bianchi/htt_base` on the authorized Remote Desktop Commander device `edd1b263-56a0-4391-8a2a-677dd00eabf5`.

Observed branch: `research/r60-covariance-calibration-20261117`.
Observed baseline HEAD: `6fe19c5139004a1f281ec85c592e5ab4c7590d5f`.

| File | Observed SHA-256 |
|---|---|
| `htt/src/common/covariance_amplitude.py` | `545862e3bb03fcddd8df5c5458edf3ed8ddbb0387ddc417ca75a72d8fa5b0894` |
| `htt/obsstat/cf4_growth_covariance.py` | `8fc0229d3261a8e85141316c2fc7b1fd1848bd9a3ad670c4623156fa39e7914f` |
| `htt/htt/htt/infer/r60_covariance_calibration.py` | `40b523e2cf6073ec4c866d59155f92da520ec010b4ae8997b7ab2e5f3a91552b` |
| `htt/src/common/test_covariance_amplitude.py` | `3dd5389dead4a02720eb4b64c9b909a45ff08806dae0c9766e81c765433f9348` |
| `tests/r60/test_covariance_calibration.py` | `81489e210d734848065d3b5d75fe02750ce1088eb393463cb78965245a25c4d2` |
| `scripts/r60/run_r60_sensitivity.py` | `85bd6f56b72dfd8bb548075d4618fdae2b341067ed66a21d92d88817cc2cc3fe` |
| `scripts/r60/run_r60_axisym_witness.py` | `3e68b3514cfb49b922c31cc3c0621b231b055e4163353cd94b905c632439b02e` |
| inherited `htt/htt/htt/infer/r58_mixed_tensor_likelihood.py` | `f1c07d8ba7253f225af9354277a2973b5cab96c86febd08d4f8c5e1a11555bc0` |

Data/result identities relative to `docs/research_program/observational_publication_20261015/`:

| File | Observed SHA-256 |
|---|---|
| `R58_MIXED_TENSOR_CONVERGENCE_20261117/RESULTS/OWNED_TENSOR_CARRIERS.npz` | `42f6bc5158fdf2f876720db12c44b088bc2db9734887e0d84ae098b234a7e64d` |
| corresponding `OWNED_TENSOR_RESULT.json` | `264160d6b53112e7b21278bbeb19baaa9c45e22037b8269debc20baa294f09b9` |
| `R58_MIXED_TENSOR_CONVERGENCE_20261117/RESULTS/NATIVE_REPLAY/OWNED_TENSOR_RESULT.json` | `225e4ddd8c99552560ff8b54ad5b6c4ca5ffb52efbc5ff75d81ab2148a086711` |
| `R60_COVARIANCE_CALIBRATION_20261117/RESULTS/SENSITIVITY/SENSITIVITY_RESULT.json` | `db69e7b7b4d5c3ed798531ffa9324bfe102a98a4338d76ca6eb06f0f6268c1f2` |
| `R60_COVARIANCE_CALIBRATION_20261117/RESULTS/AXISYMMETRIC_WITNESSES.json` | `291a1554bbc320a45380f9a13380121730466af5ce887f74d07bef5f31540892` |

The sensitivity result's stored module and runner hashes match the inspected files. The axisymmetry result binds the native-replay input, whereas sensitivity binds the original input. This is not byte identity; independent comparison gives maximum scaled coefficient difference `1.547373340571312e-13` and scaled covariance-entry difference `1.5178830414797062e-14`, establishing numerical equivalence for this use.

## Governing evidence read

- Root `AGENTS.md`, `htt/htt/AGENTS.md`, `htt/src/common/AGENTS.md`; ancestor paths were checked and had no additional applicable files.
- `docs/harness/CURRENT_CODEX_RUNTIME.md` current-native section.
- Repository skills `htt-scientific-code-validation`, `htt-physics-math-audit`, `htt-statistical-hardening`, `htt-claim-firewall`, and `htt-adversarial-review-loop`.
- Generic `code-verification` skill and verification matrix.
- Exact candidate files, the inherited GLS implementation, the R54 multipole basis and log-distance convention, relevant PR148 consumers/tests, and the actual R58/R60 products.

No repo source, tests, configuration, data, untracked historical artifacts, branch, Git metadata, or external publication was mutated by this reviewer. No clone, worktree, package install, recursive review, or full cosmic pair sum was run.

## Scientific contract and mathematical checks

### Covariance amplitude: derived and implementation-checked in the scoped experiment

For a fixed mean or an amplitude-independent residual contrast, whitening gives
`Delta ell(a) = 1/2 sum_i [p_i^2 a lambda_i/(1+a lambda_i) - log(1+a lambda_i)]`.
Each summand peaks at `max(0,(p_i^2-1)/lambda_i)`. Summing its exact interval maximum therefore gives a valid real-arithmetic upper bound for the total likelihood. The total score need not be monotone. The two-mode counterexample in the new tests has a negative boundary score and a strictly better interior maximum.

The implementation labels its gap as a floating-point numerical bound, not a directed-rounding certificate or an amplitude confidence interval. Its local minimizer supplies candidate lower bounds only. The final refiner can improve the candidate without invalidating an existing upper bound.

The fixed residual basis is computed independently of amplitude. The returned residual likelihood is a contrast/REML likelihood, distinct from the normalized ordinary profile likelihood. Independent direct covariance evaluation and the REML identity with the extra `logdet(X^T C^-1 X)` term were checked for all seven variants.

### Calibration geometry: derived and numerically checked

For a unit sourceward direction `n`, calibration bias is `b(n)=d.n+n^T Q n`, with `Q` symmetric and trace-free in an orthonormal Frobenius basis. The sphere identities
`<n_i n_j>=delta_ij/3` and
`<n_i n_j n_k n_l>=(delta_ij delta_kl+delta_ik delta_jl+delta_il delta_jk)/15`
give

`rho^2 = |d|^2/3 + 2 ||Q||_F^2/15`.

The odd cross term vanishes. Hence `B8=diag(3 I3,7.5 I5)` is the correct shape matrix for the full-sky RMS log-distance budget. The distance-modulus conversion is `rho_mag=(5/ln 10) rho`; its RMS interpretation does not depend on the sign convention for the mean log-distance shift.

The minimization of `(h-b)^T C^-1(h-b)` over the calibration ellipsoid is a strictly convex trust-region problem. The Cholesky/eigendecomposition multiplier solution is consistent with its KKT conditions. All 210 stored frontier witnesses were independently checked, including all 116 positive-budget boundary cases and the zero-budget cases. Confidence thresholds use the target dimension (8, 5, or 3); they are confidence-set intersection thresholds, not a chi-square distribution for the optimized distance.

### Wald sensitivity and same-data transformations

The coefficient estimate changes with covariance, so a parameter-block Wald statistic has no general monotonicity theorem under `C=N+a S`. The new test provides an exact counterexample. The scan keeps the tested finite grid and only refines bracketed sign changes; this supports the explicitly finite-grid result and no assertion about missed roots between nodes.

The seven data operators are transforms of the same observations. The implementation uses an envelope (maximum per-model p-value and union of confidence sets), not a product of probabilities or cross-operator likelihood odds. Its conditional validity requires a correct included model/covariance and declared deterministic budget; post-hoc selection remains outside calibration.

### Axisymmetry: feasible-witness interpretation verified

The candidate `K=a sqrt(3/2)(n n^T-I/3)` is STF and has Frobenius norm `|a|`; two eigenvalues coincide. Every stored candidate was independently reconstructed from its axis and amplitude and checked against the retained five-dimensional covariance and full-state profile lift.

Distances range from `1.091064492017686` to `5.028793300415738`, all below `chi2_5(.95)=11.070497693516351`. The smallest margin is `6.041704393100614`. This establishes existence of an axisymmetric apparent STF inside each conditional marginal confidence ellipsoid, regardless of whether the local optimizer found a global optimum.

A precision point for the pending prose: the same quadratic cutoff projects/lifts exactly between marginal and full parameter coordinates. A marginal 95% five-dimensional cutoff and a joint 95% eleven-dimensional cutoff are different numbers. The code records both and does not equate their coverage. Do not describe the marginal 95% region as the exact projection of the joint 95% region.

## Fresh execution evidence

### Existing focused tests

Cwd: primary checkout. Command:

```bash
PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=htt:htt/src python -m pytest -p no:cacheprovider htt/src/common/test_covariance_amplitude.py tests/r60/test_covariance_calibration.py -q
```

Observed output: **18 passed in 21.32s**, exit 0. Remote process PID `1022584`.

Observed reviewer environment: Python `3.12.3`, executable `/usr/bin/python`, NumPy `2.4.2`, SciPy `1.17.0`. The stored products were generated under Python `3.12.3`, NumPy `2.5.4`, SciPy `1.18.1`. Thus these checks are an additional cross-version validation, not a claimed replay of the author's environment. The author subsequently identified production interpreter `.venv/bin/python`; final repair closeout should use that interpreter.

### Independent actual-data oracle

The separate oracle is saved in shared scratch as `final_science_review_actual_oracle.py`, with machine-readable observed output `final_science_review_actual_evidence.json`. It imports NumPy/SciPy only and reads frozen source/results; it does not import the R60 implementation. Its GLS uses pivoted QR (`lstsq(..., lapack_driver="gelsy")`), then directly evaluates residuals, covariance log determinants, KKT conditions, and axial tensor identities.

Executed by a Python heredoc with the same one-thread environment, remote process PID `1031340`, exit 0, runtime 1.45s.

| Independent quantity | Maximum discrepancy |
|---|---:|
| GLS estimate in declared parameter scales | `1.0061396160665481e-14` |
| Scaled GLS covariance relative error | `6.231314646719261e-15` |
| Block Wald vs independent profiled residual LR | `6.394884621840902e-14` |
| Direct Gaussian log-likelihood gain | `1.7053025658242404e-13` |
| Contrast gain vs full REML determinant identity | `9.237055564881302e-14` |
| Independent contrast mean annihilation | `1.1355379921581982e-17` |
| Calibration witness budget excess | `6.938893903907228e-17` |
| Calibration distance discrepancy | `7.460698725481052e-14` |
| Calibration relative KKT or threshold error | `7.135434600880987e-12` |
| Axial reconstructed matrix entry error | `6.938893903907228e-18` |
| Full-state vs marginal witness quadratic distance | `1.7763568394002505e-15` |

Every retained design has rank 11. At amplitude 1, full data-covariance condition numbers are 127.54–951.92, scaled information-matrix condition numbers 54.31–146.87, and angular covariance condition numbers 9.62–30.00. The noise and signal are positive definite for all seven retained carriers. These observed numbers do not suggest a conditioning problem for the present products.

### Recorded command failure without scientific consequence

One exploratory `rg` command included a nonexistent glob `htt/obsstat/tests/*growth*`; `rg` returned a path error and therefore prevented an `&&`-chained read from running. The necessary files were subsequently read directly. This was a review-command path error, not a repository test failure.

## Required closeout

1. Resolve F01 on the exact deterministic 400-mode case, preserving the valid global-gap semantics, and execute affected focused tests with the production interpreter.
2. Bind closeout to the final changed source hashes.
3. Read the author's final report and any explicitly added finite radial-velocity extension in this same bounded review; check interpretation against its output.
4. Stop optional testing once these concrete remaining risks are resolved. No new review ladder or expensive survey regeneration is required.


## Targeted F01 repair closeout — CLOSED

The author changed the interval upper bound to the minimum of the original separable bound and a midpoint Taylor bound. For `f=sum_i f_i`, midpoint `m`, interval half-width `r`, and
`M=.5 sum_i [lambda_i/(1+lo lambda_i)]^2 [1+2 p_i^2/(1+lo lambda_i)]`,
the derivative identity implies `|f''(a)|<=M` throughout the interval. Thus
`f(a)<=f(m)+|f'(m)| r + M r^2/2`.
This bound uses the aggregate score cancellation near the maximum and requires no total-score monotonicity. Taking the minimum of two valid bounds preserves the real-arithmetic upper bound. The implementation retains the numerical (not interval-arithmetic) interpretation and a roundoff guard.

Final inspected repair identities:

| File | SHA-256 |
|---|---|
| `htt/src/common/covariance_amplitude.py` | `911217a7ec77df26794da149ad1207c9565bc63b73d68cdf6958ad3420b2b1bd` |
| `htt/src/common/test_covariance_amplitude.py` | `ca272443c48102bbebe2f8d60e38bd730c30660d658531c3cc6a0d5105ec3bff` |

Independent closeout command, in the primary checkout:

```bash
PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=htt/src:htt:. .venv/bin/python -m pytest -p no:cacheprovider htt/src/common/test_covariance_amplitude.py tests/r60/test_covariance_calibration.py -q
```

Observed: **19 passed in 1.81s**, remote process PID `1048595`, combined command exit 0. The exact F01 input was separately evaluated through both the helper and the public legacy wrapper in the same process command.

| Closeout quantity | Observed value |
|---|---:|
| Python executable | `/home/cosmosapjw/Dropbox/bianchi/htt_base/.venv/bin/python` |
| Python / NumPy / SciPy | `3.12.3 / 2.5.4 / 1.18.1` |
| Fitted amplitude | `0.9498014836917934` |
| Local Fisher variance | `0.01161475273539168` |
| Log-likelihood gain | `1693.7848941992715` |
| Numerical objective gap | `4.256662577972747e-9` |
| Intervals | `54` |
| Objective evaluations | `84` |
| Directly observed helper time | `0.031411087984452024 s` |
| Legacy-wrapper amplitude difference | `0.0` |

The new regression asserts the objective against an independent dense-grid lower bound, numerical gap <=1e-8, and fewer than 5,000 intervals. The negative-boundary-score counterexample and other focused cases still pass. This closes the reproduced valid-input failure without reinstating the invalid monotonicity assumption.

**Current core-code verdict: PASS for the explicitly tested R60/legacy repair scope, with no unresolved material finding.** The original 32D products' independent oracle remains valid for unchanged GLS/calibration/axis code; final regenerated product identity and pending author report/finite radial extension still require the already agreed same-pass inspection. This is not a blanket validation of every legacy mock run or all possible floating-point scales.


## Same-pass changed-dependency review: radial-velocity extension

This extension was explicitly supplied by the author after the core review. Its new public helper and scientific product are included in this same bounded pass; it is not a recursive review.

Inspected identities:

| File | SHA-256 |
|---|---|
| `scripts/r60/run_r60_radial_velocity.py` | `2e23b6a3a041dccef742a3be5f80dbd589859718abfa1286cfafdaa56af3e8dd` |
| `htt/htt/htt/infer/r60_covariance_calibration.py` with initial linear-budget helper | `1c80356cd8f9bc76a5104853be879619c6a2282aa7794c2584f4140884a90ff2` |
| `tests/r60/test_covariance_calibration.py` with rank-2 oracle | `6913662934ecbee25e26c27ab20d6fd86a426e642faabdd76c1e882222bde752` |
| `RESULTS/RADIAL/RADIAL_VELOCITY_RESULT.json` | `4c7f9d28b204c59a30aeb06a02a282c27835f0613a17d376f0b9f729772a882a` |
| `RESULTS/RADIAL/RADIAL_RESPONSE_CARRIERS.npz` | `e79f4d65ce39af662fccb434ffccaa99004ca045384d072fadc881f6328fd502` |

### F02 — Medium / high confidence, new helper API only: fixed relative rank truncation can falsely exclude a feasible bounded nuisance

Location: `linear_budget_distance`, initial reviewed module lines 142–147.

Exact falsifier:

```python
linear_budget_distance(
    [0., 3.], np.eye(2), np.diag([1e13, 1.]), 3.
)
```

Observed result: `distance2=9.0`, `image_rank=1`, nuisance witness `[0,0]`.
But `v=[0,3]` is feasible with norm 3 and `H v=[0,3]=h`, so the exact minimum is zero. The implementation silently discards a nonzero singular value because of the fixed relative threshold. This is sufficient to invert a confidence-set intersection decision (for example against the 95% two-dimensional chi-square threshold). It is not an invalid input under the advertised function contract.

The current R60 product is **unaffected**: all 21 actual whitened nuisance maps have minimum-to-maximum singular-value ratios in `[0.14949092191673388,0.8317942167576551]`. None is near the truncation threshold. The problem concerns the new shared helper's general mathematical promise, not the observed radial scientific result.

Minimum remediation: reject unresolved nonzero image directions explicitly when their finite-budget effect matters, or use a stable trust-region algorithm retaining all relevant modes with a scale-aware multiplier solve. Merely changing the filter to `s>0` can expose an absolute multiplier-root tolerance problem for very ill-scaled singular values; a clear fail-closed numerical-domain check is sufficient for this scoped API. Preserve the exact rank-deficient geometric test.

### Radial scientific construction

The source defines `V(z)=V0+V1*z/zstar` with `zstar=.05`, in km/s. It uses the same fixed Gaussian 32D experiment and reconstructs only pinned data operators; it does not regenerate cosmic pair sums.

The stable chart is correctly related to the physical coefficient chart by
`d_eff=dH+V1/(c*zstar)`.
The residual slope column is `g(z)z/zstar-1/(c*zstar)`, and the reported physical estimate/covariance are correctly pulled back using `T`. The direct physical and conditioned response matrices represent the same model. The low-redshift expansion follows directly from `E(z)=1+(1+q0)z+O(z^2)` and `chi(z)=z-(1+q0)z^2/2+O(z^3)`, giving
`c z g(z)=1-(1+q0)z/2+O(z^2)`.

For a fixed omitted slope, the old coefficient estimator obeys
`alpha_hat=alpha_true+H V1+Gaussian error`,
with `H=(X^T C^-1 X)^-1 X^T C^-1 Z`.
Its marginal target confidence set enlarged by `-H ball_b` therefore has the stated conservative coverage conditional on the fixed linear experiment and bounded slope. Ignoring residual information enlarges the allowed set and does not create a new optimized-distance chi-square law. The image body can have lower rank than the target space, so the orthogonal residual component must remain; the actual-data checks confirm that it does.

### Independent radial execution

Production interpreter, one BLAS thread. The focused test command recorded above, now including the new rank-2 test, produced **20 passed in 2.26s**, remote PID `1080105`, exit 0.

Independent QR/geometry oracle, remote PID `1087127`, exit 0, is saved as `final_science_review_radial_oracle.py`; observed metrics and the F02 counterexample are saved as `final_science_review_radial_evidence.json`.

| Check | Maximum discrepancy |
|---|---:|
| Scaled physical/chart response identity | `2.439454888092385e-17` |
| Independent QR physical coefficient estimate, scaled | `1.354472090042691e-12` |
| Physical covariance relative error, scaled | `4.028455306935918e-15` |
| Block Wald vs separately constrained QR residual LR | `4.908216055810044e-10` |
| Independent QR bias-map construction | `7.034303695085953e-15` |
| Relative finite-budget feasibility excess, 84 witnesses | `5.684341886080802e-16` |
| Direct quadratic distance, 84 witnesses | `3.019806626980426e-13` |
| Relative KKT residual, 84 witnesses | `2.306500974105172e-12` |
| Critical threshold from independent SLSQP, 8 positive roots | `3.0386893001832505e-10` |
| Independently recomputed endpoint speed/c | `1.3322676295501878e-15` |

The unrestricted fitted velocity histories reach speed/c `0.1587639159743127` to `0.5305708264523733`. Accordingly the full 14D result is a formal local linear-response/conditioning diagnostic, not a validated physical velocity-history or tilt fit. Its original physical dipole standard errors increase by factors `125.57–141.05`. The maximum conditional nested-model p-value is `0.8577034023498985`; the source's p-value labels are conditional, and no discovery interpretation is warranted.

At the declared bounded slope radius 3,000 km/s, every quadrupole target still has distance greater than `chi2_5(.95)`; the smallest is `12.48971747762098` versus `11.070497693516351`. The formal minimum critical slope is approximately 22,506 km/s. Because at the observed upper redshift `z≈.1` this slope contribution alone reaches approximately 0.15c, that critical value must remain a **formal linear-model extrapolation**, not an inferred or relativistically valid physical threshold. The meaningful bounded-sensitivity claim is the behavior on the explicitly declared 0–3,000 km/s budgets.

**Current extension verdict:** the actual-data radial calculations and conservative finite-budget construction pass the independent checks. F02 is an unresolved general-helper numerical-contract finding pending the author's targeted closeout. Final report prose and final result provenance remain to be inspected.


### F02 first repair check: cutoff fixture closed, multiplier-boundary failure remains

The first author repair added an explicit error for discarded nonzero singular modes. The original `diag([1e13,1]), radius=3` counterexample now correctly raises `ValueError`. Observed module hash was `47203ba8ea7af3d5bf0e947e55c9beb519a17f133d84bd577d5d7910d31ac101`; test hash was `e36e11a8eccf38aa9faf6efbc462a230d31a88b002ca3a21026c8d0c49a3cb45`.

The previously identified multiplier-tolerance concern was then checked directly on a retained singular direction:

```python
linear_budget_distance([0.,3.], np.eye(2), np.diag([1e8,1.]), 2.)
```

Observed under the production interpreter: `distance2=0.0`, `nuisance_witness=[0,3]`, `budget_used=3.0`, `image_rank=2`. The declared budget is 2. The exact minimizer is `[0,2]` with distance squared 1. This is the same F02 numerical-domain issue, now caused by `xtol=1e-14` in a multiplier whose relevant scale is around `1e-16`, rather than the rank filter.

A minimal valid repair is to enforce the active-boundary norm residual after root solving and fail closed when the declared relative tolerance is not met. Silently clipping a poor multiplier solution is insufficient to establish the optimum. This check executed in remote process PID `1100809`, exit 0 (exceptions were intentionally captured for the first case). Current R60 data remain unaffected by either F02 edge.

## Limited deterministic Commander morphology check

This addition was explicitly requested for an obvious sign, norm, and source check; no new stochastic or CMB-wide audit was performed.

| File | SHA-256 |
|---|---|
| `scripts/r60/run_r60_commander_morphology.py` | `71d34e17474b2d05902fa032ceca1e3491c92ad38e51bad8bd72cc2f2c8a2c69` |
| `RESULTS/COMMANDER_MORPHOLOGY.json` | `cf2ad8f63e1f93fe2d5344625c8eb0d37c0cc306b7289674d938a868389a0e70` |
| Original R51 `observed_carrier.npz` | `f0c08a115854a6f287d39eddf984291f676e6f7bb79bb2324eb92cd6eb2c0dca` |

The source carrier hash was independently recomputed and matches the product. Its Commander and SMICA quadrupole entries match the product exactly. The real-mode convention is consistent with Condon–Shortley harmonics and the stated STF basis. An independent Cartesian polynomial construction gave the same temperature tensors without importing the new script:

`T2(n)=sqrt(5/(16pi)) d0 (3z^2-1) - sqrt(15/(4pi)) z(d1r x+d1i y) + sqrt(15/(16pi))[d2r(x^2-y^2)+2 d2i x y]`.

The polynomial implies the stated map
`q=[d2r,-d0,d2i,-d1r,-d1i]/sqrt(8pi/15)`.
It also gives `<T2^2>=2 tr(Q^2)/15=5 C2/(4pi)`, confirming the temperature units and normalization.

Independent one-thread production command, remote PID `1101280`, exit 0:

| Quantity | Maximum discrepancy or independently reproduced value |
|---|---:|
| Source packed coefficients | `0` |
| Temperature tensor matrix entries | `1.7763568394002505e-15 microK` |
| Eigenvalues | `3.552713678800501e-15 microK` |
| Eigenaxis projectors | `6.106226635438361e-16` |
| RMS/power identity | `2.842170943040401e-14 microK^2` |
| Relative tensor difference | `0.08273935443647602` |
| Matched ordered eigenaxis angles | `2.0665168657513004, 2.430275813992629, 2.5077272057188105 deg` |
| Absolute-extremum-selector angle | `88.49933998223969 deg` |
| Absolute-extremum indices | Commander `0`, SMICA `2` |

The apparently large principal-axis change is therefore correctly identified as a selector branch switch. For a traceless three-dimensional tensor, the sign of the middle eigenvalue determines which extremal eigenvalue has the larger absolute magnitude; that selection can switch while corresponding eigenaxes remain close.

The matched-axis perturbation bound uses the residual inequality with spectral norm of the tensor difference divided by separation from the other comparison eigenvalues. Its stated application is valid here, and the measured matched angles lie below the recorded approximately 4.76–5.01 degree bounds.

No sign or normalization defect was found. The reported object remains a tensor representation of the stored masked-estimator coefficients, with inherited beam/leakage/foreground/kinematic-quadrupole caveats. The output explicitly does not construct a Commander covariance, confidence interval, p-value, shear inference, or family identification. The auxiliary stored-template inverse is labeled an operator-equivalent reference using the SMICA-beam template, which is the appropriate restriction for that deterministic calculation.


## Targeted F02 final closeout — CLOSED

The author kept the explicit fail-closed behavior for unresolved nonzero singular directions and changed both calibration multiplier solvers to the smallest positive floating `xtol`, relative tolerance `1e-13`, and `maxiter=256`. An active-boundary norm residual greater than `1e-9*radius` now raises explicitly. No simple clipping was substituted for optimization.

Final inspected identities:

| File | SHA-256 |
|---|---|
| `htt/htt/htt/infer/r60_covariance_calibration.py` | `df627106d768a17c0a7942baa18afe4793f9226b41232839c2005dce9270c310` |
| `tests/r60/test_covariance_calibration.py` | `4d99dc6fd61bf866e2fe23f734efdaecc2df5606138aa71697f88e888f22c700` |

Production one-thread focused tests: **22 passed in 3.65s**, remote PID `1117970`, combined command exit 0. Independent direct calls in the same command confirmed:

- `H=diag(1e13,1), radius=3`: explicit `ValueError: numerically unresolved nonzero nuisance mode`.
- `H=diag(1e8,1), radius=2`: witness `[0,2]`, budget used `2`, squared distance `1`.

Both reproduced F02 failure mechanisms are closed. The earlier actual-data oracle remains informative because its nuisance-map singular ratios are far from the rejected domain. Final generated products still need to bind this final module identity.

## Limited count-dipole sensitivity check

| File | SHA-256 |
|---|---|
| `scripts/r60/run_r60_count_dipole_sensitivity.py` | `0d834adbce28572d77ab3f03b29682112862950042b8a457c4ac06e4278184a4` |
| `RESULTS/COUNT_DIPOLE_SENSITIVITY.json` | `76b7103a7c73fb1e9b4a6a24d79e0739de20b3dc85428929191b7679f3f0f419` |
| Inherited `R54_L03_RESULT.json` source | `0df35f1d30505cea66a6087d341904fdcb2be07787ec413288b59a3a60fa0125` |

The code holds the excess vector fixed and changes covariance by a PSD increment. In this situation the derivative `d(e^T C^-1 e)/d lambda=-(C^-1e)^T S(C^-1e)<=0` is valid; it does not conflict with the absence of general monotonicity for the refitted CF4 Wald statistic.

The minimum Euclidean offset solves a convex constrained problem. Its KKT relation is
`b=tau C^-1(e-b)`, hence the eigen-coordinate expression `b_i=tau e_i/(c_i+tau)`. The source retains the original finite-mock tail payload unchanged and labels every new covariance-conditioned Gaussian tail and confidence ellipsoid as nominal.

Independent one-thread production check, remote PID `1118591`, exit 0, recomputed source hashes, all 101 covariance-path points per catalogue, the threshold crossing, and the calibration KKT relation.

| Quantity | Quaia G20 | NVSS |
|---|---:|---:|
| Original mock count | 500 | 500 |
| Finite-mock payload matches source | true | true |
| Nominal Gaussian p at lambda 0 | `0.00041702301794998057` | `0.3227920348190415` |
| Nominal Gaussian p at lambda 1 | `0.309208812103659` | `0.42116777851279785` |
| Maximum recomputed path discrepancy | 0 | 0 |
| Independent nominal 0.05 crossing | `0.25368911086800666` | no crossing; already compatible |
| Minimum offset norm | `0.0038996227210868497` | 0 |
| KKT residual norm | `1.9873754096201567e-18` | 0 |

The positive-offset residual quadratic differs from `chi2_3(.95)` by only `2.6645352591003757e-15`. No covariance was relabeled as known, no finite-mock probability was replaced, and no velocity or global-tilt inference was made. No material issue was found in this narrow addition.

## Main report interpretation review

Read complete shared-scratch `REPORT_KO.md`, SHA-256 `35ff4f6e3bd6b162ba7c7568f1a808bd9bdc51efc103c9e9800685c003167d9e`.

The reported numerical values and distinctions agree with the independently checked products: different null dimensions, same-data confidence union, variance versus standard-deviation multiplier, adversarially oriented full-sky RMS calibration, marginal versus joint confidence cutoff, formal unrestricted radial fit, physically bounded sensitivity inputs, deterministic Commander comparison and eigenaxis branch switch, and nominal Gaussian versus original finite-mock count tails.

The physical claim restrictions are appropriately stated. The local `-A.n/c` sign is consistent with sourceward directions and, for example, the first-order redshift in a static accelerated/Rindler congruence. The report explicitly limits the local kinematic map to its low-redshift leading term and does not infer vorticity from the absent distance column.

No material interpretation finding was identified in this report. Its history-inventory and external-literature claims belong to the separately assigned source/history review, and are not claimed independently verified by this numerical reviewer. The detailed theory/physical-likelihood/plan documents and final regenerated provenance remain the last agreed same-pass items.


## Detailed theory, physical-likelihood, and plan interpretation

Read the complete final-draft documents in shared scratch:

| Document | Inspected SHA-256 |
|---|---|
| `THEORY_LOOPS.md` | `cf4e73184d6a5709cec50aefc399ba969f717449f9181c63d0f9c2d9def5aa13` |
| `TENSOR_PHYSICAL_LIKELIHOOD.md` | `a95672f36bb860843a741e0cc7b9be459d25b4a2d0f2840123bfc201a2b4a10f` |
| `RESEARCH_PLAN_KO.md` | `8752ad9d931d721b8be632ea2f1ae59755aeea57b5f9e099520bced3582c74b9` |

No material mathematical or interpretation defect was found in the scoped new synthesis.

- The normalized state has 22 coordinates, response rank 11, and an 11-dimensional nullspace comprising three unconstrained vorticity coordinates, three acceleration/calibration shifts, and five shear/calibration shifts. The physical sign map and component units are consistent.
- The condition on a nonlinear functional's differential is explicitly necessary and local, so it is not promoted to global identification of a multibranch model.
- The physical support map `T=diag(I3/c,-I3,I5)` and `K xi=(0,d_cal,-q_cal)` correctly implement `beta=V/c`, `a=-d+d_cal`, and `s=kappa-q_cal`. Its full-state confidence support uses the 11D cutoff; the text separately requires the appropriate marginal cutoff for 8D/5D statements.
- A finite union and its convex support hull are distinguished. The five views remain dependent functions of one declared experiment or identified set, and occupancy is not invented from support.
- The covariance-dependent Gaussian score includes the mean, quadratic covariance, and log-determinant derivative terms with the correct signs. Exact fixed-covariance linear sufficiency is not extended to raw catalogue sufficiency or a general nonlinear model.
- The theory labels the six units as scoped calculations, preserves inherited transfer/covariance limitations, and does not claim that all six physical research programs or a universal no-go theorem are solved.
- The future plan makes matched raw-source comparison and empirical calibration/coverage the primary dependencies, while keeping independent Commander calibration, velocity/source-frame responses, and Bianchi transfer obligations conditional on the corresponding physical claim.

A nonblocking plan-edit issue was sent to the author: some dependency references still used `P1/P2/P6` while the defined node IDs are `NEXT-01/NEXT-02/NEXT-06` (including `NEXT-01+P2` and `NEXT-04–P6`). These should be normalized before publication so the plan refers to its actual nodes. The main report also reused `N_m` for both a nuisance mean design and the noise covariance; the author agreed to rename the mean design `M_m`.

Inherited literature/source equations, including the previously audited Thomson-kernel and Bianchi source material, were checked for consistency of use and stated scope here, not rerun as a new external-literature audit. The external literature/history and independent theory source checks remain separately attributed.

At this point both material numerical findings are CLOSED and all supplied scientific additions/prose have been reviewed. The only remaining review action is to bind the regenerated result products to the final source hashes and record the two small text corrections; no broader numerical or physical audit is needed.


## Final receipt and scoped verdict — PASS

**Specification PASS; engineering PASS within the explicitly reviewed scope. F01 and F02 are CLOSED. No unresolved material finding remains.** The two small text corrections are also complete. The conditional scientific limitations are part of the accepted result, not hidden failures or claims of physical identification.

The final source files were rehashed directly after regeneration and match the tested/inspected identities:

- Shared amplitude helper: `911217a7ec77df26794da149ad1207c9565bc63b73d68cdf6958ad3420b2b1bd`.
- Calibration/linear-budget module: `df627106d768a17c0a7942baa18afe4793f9226b41232839c2005dce9270c310`.
- Amplitude test file: `ca272443c48102bbebe2f8d60e38bd730c30660d658531c3cc6a0d5105ec3bff`.
- Calibration test file: `4d99dc6fd61bf866e2fe23f734efdaecc2df5606138aa71697f88e888f22c700`.

The final products explicitly bind those source identities:

| Final artifact | SHA-256 |
|---|---|
| `RESULTS/SENSITIVITY/SENSITIVITY_RESULT.json` | `4cdcac8a635a9bda49ef50fa5a597508280d5fa0643861b78e2821947502b1cb` |
| `RESULTS/RADIAL/RADIAL_VELOCITY_RESULT.json` | `ff6488bfbcb38e3e030e7cd2636325eaf3f616ce3e8c4709f89f015618577348` |
| `RESULTS/FINAL_ACTUAL_ORACLE.json` | `449fad13373b8e94731d76e864f229e0a53420b0ecc65cf98cf3991ba5707b4c` |
| `RESULTS/FINAL_RADIAL_ORACLE.json` | `82ddd9b978b5eb28f17c078161bb8ba3de140410d509bc6230d44a2cd4567847` |

The final sensitivity metadata names the final calibration module `df6271...` and final amplitude helper `911217...`. The radial metadata names the same final calibration module. The final radial oracle binds the regenerated radial JSON hash `ff6488...`; its response-carrier hash is unchanged `e79f4d...`.

The author reran the independently written oracles under the production environment. Their full persisted JSON outputs were read directly by this reviewer. Final actual-data discrepancies remain within the previously established numerical scale: scaled GLS estimate `9.020562075079397e-15`, covariance relative discrepancy `9.648487194920146e-15`, block-Wald/LR difference `6.394884621840902e-14`, direct likelihood gain `1.7053025658242404e-13`, and calibration relative KKT/threshold discrepancy `7.134311390505081e-12`. All 210 calibration and 84 radial-budget witness checks remain consistent. The radial oracle metrics are unchanged.

### Preserved oracle serialization failure and recovery

The production replay initially reached `json.dumps` and failed because the SciPy/NumPy result represented rank as `numpy.int64`. The actual traceback was inspected in `RESULTS/FINAL_ACTUAL_ORACLE_SERIALIZATION_FAILURE.log`; its terminal exception is `TypeError: Object of type int64 is not JSON serializable`. This is a review-harness serialization compatibility failure, not a physical, statistical, or numerical-fit failure.

The oracle's sole correction is an explicit `int(rank)` at JSON assembly. Its final source SHA-256 is `962f41c365913e08685d2facb37d7fbcea9cece1952a163eefc68f9e549835ba`. The corrected final JSON has production runtime `Python 3.12.3 / NumPy 2.5.4 / SciPy 1.18.1` and the successful numerical evidence described above. The original failure remains evidence; no scientific algorithm was modified to obtain success.

### Final prose identities and corrections

- `REPORT_KO.md`: `1a750b4b3c29d56a5199ad77a775144576a44013aea5e7f977c944bde0720c94`; nuisance mean design now uses `M_{m,i}`.
- `RESEARCH_PLAN_KO.md`: `8e5d7adaff7f125d9bd0db47ac0a3caff6c18e9f62f05ee8cf835a2385c5d6dd`; no undefined `P1/P2/P6` shorthand remains.
- `THEORY_LOOPS.md`: unchanged `cf4e73184d6a5709cec50aefc399ba969f717449f9181c63d0f9c2d9def5aa13`.
- `TENSOR_PHYSICAL_LIKELIHOOD.md`: unchanged `a95672f36bb860843a741e0cc7b9be459d25b4a2d0f2840123bfc201a2b4a10f`.

The work can proceed to the already authorized assembly/commit/publication steps. This review does not certify Git publication, a new survey selection/coverage law, matched Commander simulations, a measured physical shear/tilt, or Bianchi family identification. Those activities and claims retain their separately stated evidence requirements. No further review loop or optional testing is requested.
