# R2-01 implementation return

Candidate passed scoped independent implementation review. Actual-product scientific admission remains HOLD. Requested executor `gpt-6.1-sol/medium`; observed runtime `UNKNOWN`. Requested reviewer `gpt-6-astra/ultra`; observed runtime `UNKNOWN`. See `REVIEW.md` for findings and closeout.

Integrated the package's fixed-design Gaussian profile/compression in `common.structured_inference`. It uses the existing `SamplingCovariance` through additive whitening methods, keeping existing `solve`, `matmat`, estimator and likelihood interfaces. Tests compare current GLS, WLS and likelihood calls with the new core; the existing OBS01 distinction between objective weights and actual sampling covariance is retained. No production estimator or likelihood callsite was redirected.

The constructor requires observation order, selection identity, observation units, and signal/nuisance coefficient units. A content digest binds C,F,N, units and rank tolerance to each compression. Inputs are snapshotted and model/statistic arrays made read-only. Rebuild when C,F,N or selection changes. `require_identity` rejects reuse under a different identity. These are caller-declared fixed conditions, not an assertion that real data meet them.

Free linear nuisance is profiled using thin whitened projection and SVD. Its log likelihood is explicitly a profile, not marginal evidence. The separate Gaussian marginal constructor integrates an explicitly proper SPD nuisance prior into the covariance and includes the effective log determinant and nonzero prior mean. Its normalized likelihood remains conditional in the signal amplitudes. Contrast estimability, complete alias, rank tolerance, M C M.T sampling covariance, and box plus ellipsoid support are covered by dense Cholesky/joint-least-squares oracles.

Final narrow run: 91 passed. Package-equivalent full-rank, dependent nuisance, dependent signal and complete alias cases: all PASS. 38,053-row synthetic run, p=13/k=8/q=4: no n-by-n arrays, measured persistent storage and process RSS in `raw/measurement_final.json`. Whole common suite before the final unit-field addition: 245 passed and 22 legacy source-image setup errors because `MES_R7_SOURCE` is absent; raw log retained. Missing repo-local venv and missing bass import failures, then a test typo calling `loglike` instead of public `log_likelihood`, are preserved in first/attempt logs. No unrelated source changes were made to resolve these.

Use `/home/cosmosapjw/venv/bin/python` with `PYTHONPATH=htt:htt/src` and one BLAS/OMP thread. Exact commands and exit states are in `COMMANDS.md`. Source/package hashes and final candidate identities are in `RETURN.json`.

Limits: no actual CF4 fit, no new proof audit, no scientific admission. Rank is a numerical decision; exact Gaussian coverage assumes fixed known covariance and data-independent design/selection. Raw-data remainder is not universally preserved by G,s,q. The new whitening cache assumes fixed covariance arrays; StructuredLinearModel enforces a private read-only snapshot. Proper Gaussian nuisance S is currently SPD; degenerate Gaussian random effects can be supplied in the existing low-rank covariance factor.

## Targeted independent-review repair

Reviewer P1 showed D=diag(1e-34,1), U=(1,0)^T, C=I whitened to diag(0,1). Raw reproduction is retained. A first residual+modal repair then failed three expanded tests for U=(1,.4)^T; that log is retained too. Whitening now uses implicit Householder QR of D^-1/2 U, a small SVD of R, and stable attenuation in orthogonal coordinates. No observation-square Q/projector is formed. The new tests cover modal/near-span vectors, the adjoint/precision identity, fit/compression, and rotated full-span modes at extreme D scales.

Reviewer P2 showed finite inputs could overflow Gram/data norm and produce NaN compression. The constructor, compression and public computed outputs now raise ArithmeticError identifying the finite numerical domain. Rescaling is required; no validator/tolerance relaxation was made.

This intermediate repair ran **102 passing tests** and four package-equivalent cases; its synthetic benchmark was 0.086 s and 14,314,152 persistent bytes. Its review remained HOLD after the row-permutation finding. The pre-repair return is preserved in PRE_REPAIR_RETURN.json.

## Same repair: row-permutation closeout

The previous repaired candidate remains invalid for a permuted extreme-scale case; its raw wrong finite whitening/fit/q is saved in raw/row_permutation_first_failure.log. The current candidate does **not** claim Householder stability at arbitrary D/U dynamic range. Before any QR/whitening, it requires ||D^-1/2 U||_F <= 1/(n sqrt(machine epsilon)); Frobenius norm is invariant under row permutations and upper-bounds spectral modal amplification. This conservatively confines n epsilon times representation amplification to sqrt(epsilon). It is an explicit numerical-domain restriction, not a universal forward-error theorem or condition estimate of C. Violations raise ArithmeticError before a model can return wrong rank, covariance or likelihood. Stable dense C remains an explicit caller option for small summaries; no large-n dense fallback is introduced.

Both extreme row orders now fail closed for Dmin=1e-20/1e-34/1e-100 and U coupling0/1e-8/.4. Supported-range Dmin=1/1e-4/1e-8 cases, both row orders and near-span vectors, match dense at1e-10. Final targeted suite120passed, package four cases PASS, final synthetic38053 measurements in raw/domain_guard_measurement_final.json. Current hashes in RETURN.json; former candidate return preserved in PRE_DOMAIN_GUARD_RETURN.json. Independent closeout is the scoped PASS recorded in REVIEW.md.
