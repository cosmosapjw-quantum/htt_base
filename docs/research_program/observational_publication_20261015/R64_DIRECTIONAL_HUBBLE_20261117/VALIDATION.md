# R64 validation and evidence

## Scope and provenance

Baseline: `33d87dd3e4a787e477327d37ee00b40e790211c9`.
Existing checkout: `/home/cosmosapjw/Dropbox/bianchi/htt_base`.
Branch: `research/r64-directional-hubble-20261117`.
One owner-selected integrated R1–R10/C1–C10 study of redshift- and direction-dependent Hubble factor, additive P3 companion only. Original42 node payload and previous paper acceptance remain protected. Journal submission remains `NOT_READY_TO_SUBMIT`.

The working observational law is the inherited fixed Gaussian white + Planck18 linear-z0 peculiar-velocity covariance. Its empirical shared calibration, grouping, selection and endpoint/flux qualification are not claimed. The finite distance-field mean and its nonlinear images are conditional on that law and the declared coherent-velocity decomposition.

## Executed verification

| Evidence | Actual outcome | Scope |
|---|---|---|
| `RESULTS/AFFECTED_TEST_RECEIPT.json`, `AFFECTED_TEST_01.log` | 60 passed, exit0, 1.42s | Original R64 module/runner tests and affected R58 full-likelihood/five-view tests; one primary native verification |
| `RESULTS/AUGMENTATION_TEST_RECEIPT.json` | 2 passed, exit0, 3.12s | New R8 full-covariance nuisance projection equals joint GLS; exact confounded component remains unidentified |
| `REVIEW/WOLFRAM_CHECK.json` | Seven symbolic differences exactly0 | Eta H/q map, calibration, Milne, Sachs transformation and cubic velocity-null algebra; undefined-symbol messages preserved |
| `REVIEW/SYMPY_CHECK.json` | Eight symbolic differences exactly0; SymPy1.14.0 | Same algebra plus constructive linear ODE for Y=Hcal² |
| `RESULTS/OBSERVED_EXECUTION_01.json` | Exit0, 21 initial observed-data fits | 7 operators × J1/J2/J3, full36, actual35970-group source design |
| `RESULTS/AUGMENTED_EXECUTION_02.json` | Exit0, 21 augmented fits | 68/72-row joint laws; full cross covariance, optional24 method-angular nuisance directions |
| `RESULTS/WHITENING_STABILITY.json` | PASS | Concrete sky72 condition-number risk only; alternative eigensystem whitening of saved carriers |

Total: **42 unique observed-data fits and62 passed tests**. Alternative whitening is a bounded numerical cross-check of three saved sky carriers, not three additional scientific model fits. This record does not claim admission to every historical four-axis CAS gate.

The sky72 covariance condition number is3.6496969e7 with minimum eigenvalue2.92395e-11. Alternative eigen-whitening preserves ranks21/30/39, with maximum coefficient change2.304e-10 marginal standard deviations, covariance change4.956e-11 in standardized units, and nominal p change3.36e-11. Declared tolerance was1e-5. The actual condition-number concern is resolved for these carriers; empirical covariance qualification remains separate.

Native runtime: Python3.12.3, NumPy2.5.4, SciPy1.18.1, SymPy1.14.0. Scientific commands fix `OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1` and use the existing `.venv/bin/python`; imports use `PYTHONPATH=htt/src:htt:.` when required.

## Preserved failures and bounded repairs

`RESULTS/AUGMENTED_EXECUTION_01.json` and its log record the first augmentation run's final metadata failure: a string path was passed to a helper expecting `Path`. All21 fit summaries had already printed. The one-line adapter repair and repeat are recorded in `RESULTS/AUGMENTATION_REPAIR.json`; all21 summaries were exactly equal between attempts. No scientific mean, covariance or test was modified to make this failure disappear.

`RESULTS/SUMMARY_REPAIR.json` records the separate summary-only `abs(list)` error and `np.abs` repair. Only the derived summary was rerun. These are implementation/metadata failures, not theoretical or numerical failures.

The final display labels count distance-field coefficients plus coherent V3, not39 purely optical coefficients. The summary names `field_velocity_rank` and `field_velocity_parameters` explicitly. The immutable augmentation result retains its historical boolean `optical_coefficients_identified`, which is a sufficient full-parameter-rank test; rank/parameter counts themselves include V3. No observations or fits were rerun for this wording correction.

## Reuse integrity

The inherited L05 joint cache has SHA256 `f0acb8e1be3f09d212303967ff7678178fd59364ec0131ab12ba3f5149879cae`. Its288-row layout contains log/log_mono/log_split36, method32 and sky36 cross blocks used here. Method32 and sky36 add no independent galaxies. Separate L04/L05 caches were not joined with an invented zero cross covariance. The stored cosmic body already includes the velocity response; it was not multiplied by g again.

The reconstructed whole velocity-stack byte fingerprint differs from the historical cache fingerprint; this is retained explicitly in `AUGMENTED_RESULT.json` and the summary. The selected log-eta rows are pinned and checked numerically: existing36 mean/covariance parity at about3e-15/2.2e-19; old method dipole mean/standard-deviation parity exactly0. Do not relabel this as exact whole-stack byte reproduction. Historical uncached288-row linear+damped pair-sum cost was721.1717s; cached R64 runtime is not a new uncached benchmark.

Current relevant44 sources have hash and baseline-blob records in `REVIEW/r64_history_sources.json`. The historical573-PR inventory is a dated reused artifact, not a claim of a new complete read of every current GitHub PR.

## Scientific claim status

| Claim | Evidence state | Allowed interpretation |
|---|---|---|
| Hcal, H_D and finite H_W differ in general | Literature-supported and derived; Milne numerically/algebraically checked | A qualified optical/endpoint map is required for physical Hcal inference |
| Same-ray H_D ratios and q_D remove z-independent angular calibration | Derived; represented l<=2 implementation-verified | Finite-estimator invariance holds in the represented nuisance span; actual l3 leakage witness retained |
| Initial36 J3 rank36/39 | Numerically checked and implementation-verified | Scope is the chosen compression and mean family |
| Existing correlated method/sky rows recover J3 rank39/39 | Numerically checked and implementation-verified | True even after profiling24 method-angular offsets; not a fundamental new source or precise derivative measurement |
| Source-dependent mean freedom changes adequacy | Actual-data conditional result | Full operator table retained; no causal calibration-error discovery or global significance |
| H_D/q_D images are broad or domain-uncertified | Actual common-region enclosures | Domain-certificate failure is not by itself a proof that the exact nonlinear image is unbounded |
| Physical H(z,n), anisotropic acceleration or general congruence parameters measured | Unresolved | Not claimed |
| Standalone publication novelty | Conditional candidate | Source-matched information recovery and derivative resolution require fair matched-method comparison and observational qualification |

## Fresh independent review and release

The bounded R9 clarification explicitly distinguishes the first-order velocity tangent template from a physically validated finite deboost. No small-response or nonlinear-remainder domain was imposed on the free coefficients. Saved identified augmented fits reach ||V||=5788.052km/s, with low-z scale ||V||/(c z_min) about1.93; the largest initial J3 representative,21168.238km/s, is also gauge-dependent. This changes no mean, covariance, fit or confidence image. The information-recovery figure now names its illustrative `mono_method = log_mono36 + method32` experiment and inherited working covariance explicitly. The exact correction files and final reviewer closure are recorded in the review artifacts.

The one fresh independent final review is recorded in `REVIEW/final_review.md` and `REVIEW/final_review.json`. At the creation of this validation file it has not yet been completed; its actual verdict and any bounded correction closure will be appended below. This is not a submission-ready declaration.

Canonical DAG mutation, mirror synchronization, required DAG validators and non-force publication will be recorded only after review closure in `DAG_UPDATE_RECEIPT.json`, `DAG_VALIDATION.json`, and the final Git commit. Original42 hash must remain `e3264e105cabf78ddac37addc36cacc3cfa05ee942e33e54b431b22e3e87de0d`. No automatic successor or local coding-agent prompt is created.

### R9 final closure

The one fresh independent review returned **PASS** after one bounded documentation/display correction episode. Both LOW findings R64-FR-01 and R64-FR-02 are CLOSED; zero findings remain open. No scientific fit or test was rerun for this correction. The science summary remained byte-identical at SHA256 `1c60c95c6f60e480520ef5045684fb11055c05ddee3c74160e11d801979205c9`. Initial findings and the final decision are both preserved. Journal submission remains NOT_READY_TO_SUBMIT.

### R10 integration closure

Canonical PR-DAG validation, explicit mirror write/check, and publication-DAG validation all returned exit0. The backlog now has288 entries and223 completed entries; the original42 payload hash and all original paper contracts are unchanged. The scoped R1-R10/C1-C10 integration is complete. Final commit identity and remote equality are verified at transport time, after the hash-closed files below are committed. The release preserves1084 preexisting untracked files and stages only owned R64 paths plus the eight canonical DAG/mirror files.
