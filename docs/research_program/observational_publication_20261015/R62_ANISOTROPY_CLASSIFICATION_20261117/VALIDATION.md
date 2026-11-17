# R62 validation and provenance

Date: 2026-11-17. Baseline: `c118982e56ee50d68dd0446aa10f16ffe65bd02b`. Research branch: `research/r62-anisotropy-classification-20261117`. The observed native runtime was Python 3.12.3, NumPy 2.5.4 and SciPy 1.18.1 in the existing repository environment. One BLAS thread was used. Agent model requests are recorded separately from observed runtime identity; the latter is UNKNOWN where no host receipt was exposed.

## Scientific computations

| Item | Executed evidence | Scope of the check |
|---|---|---|
| Existing CF4 sources and response | `RESULTS/SOURCE_EXECUTION.json`, `RESULTS/SOURCE/SOURCE_TENSOR_RESULT.json` | 35,970 groups, seven existing nuisance operators, exact 32D carrier order, full covariance and source projection |
| Source polynomial likelihood | `RESULTS/SOURCE/SOURCE_TENSOR_CARRIERS.npz` | J2/J3 full rank 21/26, R61 affine basis-change control, precision/score/whitened likelihood factor retained |
| Class calculations | `RESULTS/CLASSIFICATION_EXECUTION.json`, 42 individual JSON records | 210 queries; all 168 structured-class queries have explicit feasible witnesses; 616 quadratic enclosures, no unresolved solver return |
| Calibration and source injection | `RESULTS/INTERPRETATION_SUMMARY.json` | Exact common-offset quotient, propagated full covariance, commuting-source/apparent-noncommuting construction through the actual operators |
| Existing SN comparator | `RESULTS/INHERITED_SN_REUSE.json` | Four inherited STF carriers calculated from qualified R36-08 released-magnitude mean and full covariance; zero inside every ellipsoid |
| Bianchi constraints | `RESULTS/BIANCHI_EXAMPLES.json` | Actual-state IX, Type V, exceptional VI_h and conditional same-H/shear examples; replayed after the physical-unit repair |
| Symbolic checks | `REVIEW/WOLFRAM_CHECK.json` | Exact Class B momentum minor and exceptional rank, physical-velocity moment Jacobian, STF discriminant identity |

The source builder took 1.312 s and the full classification run 45.875 s in the recorded environment. The likelihood covariance is inherited and fixed; these executions do not establish its empirical coverage under all cosmological or selection models.

The maximum recorded primal-dual gap is 6.74e-15. An independent SPD solve of stored witness distances agrees within 1.42e-14. These are floating-point numerical checks, not interval-arithmetic formal proofs. A feasible class witness establishes intersection without requiring proof of a global nonlinear minimum. An outside local solution alone is not used as exclusion evidence.

## Tests and the single bounded correction

The initial affected test suite returned **113 passed, exit 0**. Its command, environment and hashed log are preserved in `RESULTS/AFFECTED_TEST_RECEIPT.json` and `RESULTS/AFFECTED_TESTS.txt`. This run predates the independent review correction.

The reviewer identified **R62-FR-01**, also called R62-F1 in repair filenames: multiplying momentum by a small Einstein coupling before comparing to a unitful absolute tolerance could admit an exactly forbidden single-fluid Type-I tilt. The correction checks source-range membership before multiplication by kappa, relative to uncancelled species momentum norms, and uses equation-relative residual scales. Raw residuals and normalization scales remain available.

The targeted physical suite after this correction returned **100 passed, exit 0**, including **14 new unit/coupling regression cases**. The log and source binding are in `RESULTS/R62_F1_TEST_RECEIPT.json`. The two test runs overlap; they are not 213 distinct tests or a claimed single 127-test execution. Statistical source/classification code was unchanged by the repair, so no duplicate CF4 campaign was required.

The final reviewed `htt/bass/background/tilted_bianchi_state.py` SHA-256 is `e36dd616f4d0e2998e48e1a50ae9b67e1cd48842ef5b52ee2b1e4b94b888fe04`. `REVIEW/R62_F1_REPAIR.patch` preserves the exact correction. The pre-correction Bianchi examples and runner are retained in REVIEW; active `RESULTS/BIANCHI_EXAMPLES.json` binds the repaired implementation and reports relative residuals.

## Independent final review

`REVIEW/final_review.md` and `.json` record one fresh review and its bounded closeout. The verdict is **PASS / APPROVED_FOR_SCOPED_RESEARCH_BRANCH**. The reviewer independently checked all 42 carriers and 210 witnesses, 14 source GLS fits using QR, four inherited SN zero witnesses, actual IX and exceptional VI_h examples, and the original physical-unit counterexample after repair. The finding is CLOSED; no new review tree is requested.

The review did not reprocess the raw CF4 catalogue, calibrate the covariance, reread every historical PR diff, certify the entire legacy BASS API, or approve journal submission. The original and repaired counterexample calculations, exact file identities and numerical runtime are preserved in the JSON. `REVIEW/R62_F1_CLOSURE.json` indexes that evidence without replacing the review.

## Publication DAG

`DAG_UPDATE_RECEIPT.json` records the additive canonical R62 card: backlog 285 → 286; completed cards 220 → 221. All preceding card payloads are preserved. The original 42 scientific nodes retain canonical payload SHA-256 `e3264e105cabf78ddac37addc36cacc3cfa05ee942e33e54b431b22e3e87de0d`; P5's original acceptance contracts are unchanged.

`DAG_VALIDATION.json` records actual mirror synchronization, publication export, canonical PR-DAG validation, mirror consistency check and scientific publication-DAG validation. The original queue has no ready cards and seven external blockers; these inherited campaign conditions are not changed by completing this scoped companion study. The R62 DAG contains exactly ten completed sequential tasks and a finite, explicitly inactive future paper plan.

## Preserved failures and limits

The first classification launch failed before producing science results because of one omitted einsum operand. The failed runner, log, receipt and correction are retained in REVIEW/RESULTS. The repaired full run succeeded. This was an implementation failure, not a failed physical hypothesis or a remote-environment blocker.

The active Codazzi convention is documented and tested. The opposite-sign neighboring legacy `constraints.py` path remains migration debt outside this change. Likewise, old familywide IX statements and the squared-component-versus-physical-velocity Jacobian confusion are historical defects corrected in the active code; old receipts are not rewritten to appear as if the repairs had always existed.

CF4 tensors are phenomenological log-distance response coefficients. SN tensors use released magnitude residuals. Neither becomes physical normal shear by renaming it. Physical frame, source/observer response, shared peculiar velocities, stress closure, external calibration and covariance coverage must be admitted before stronger geometric inference. No CF4/SN independent-product likelihood or measured Bianchi type/tilt/rotation is claimed.

Every class question within one carrier uses the same declared 95% ellipsoid. Different nuisance treatments, source orders and carriers are correlated; the collection is not a simultaneous 95% confidence statement over all 42 experiments. The original manuscript status is **NOT_READY_TO_SUBMIT**.

## Reproduction and release identity

Use the existing `.venv/bin/python`, `PYTHONPATH=htt/src:htt:.`, `PYTHONDONTWRITEBYTECODE=1`, and one BLAS thread. Scripts under `scripts/r62/` expose their arguments. Scientific replay must use fresh output directories because the runners protect existing results. `finalize_dag.py` is a one-shot authorized metadata migration and is not a scientific replay step.

`ARTIFACT_MANIFEST.json` binds R62 code, tests, documentation, result receipts and canonical DAG products at release preparation. `PACKAGE_VALIDATION.json` records source-review hash parity, result counts, preserved original science nodes, owned-path boundaries and the actual whitespace check. Git commit identity is supplied by the containing commit and the verified remote branch; no circular self-hash is asserted. Preexisting unrelated untracked files are not staged by this release.

The full staged whitespace scan records formatting diagnostics in generated SVG path data, CSV CRLF, unified-diff context lines and two preserved agent-note final blank lines. Those seven exact artifacts retain their original bytes. A separately recorded scan of every other staged file passed; no scientific result or source code was altered for this formatting check.
