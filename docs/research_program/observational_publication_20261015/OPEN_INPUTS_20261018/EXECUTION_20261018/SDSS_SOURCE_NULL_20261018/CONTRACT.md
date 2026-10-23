# Frozen SDSS source-null contract, 2026-10-18

Owner: obsstat; source-only, diagnostic, non-claim-bearing. This preserves the
Astra contract conveyed by the parent for actual execution, review and resume.
Requested executor `gpt-6.1-sol/high`; observed runtime identity UNKNOWN.
Use the sole existing checkout and canonical `.venv/bin/python`. Intake HEAD
`ad27f4cb5f84dfaccc322e53f2810ad29dc72276`; later independently authorized
HEAD advances are observed separately, never reset/rebound. No clone/worktree,
nested agents, commit or push by this worker.

## Stage 1: frozen source and actual-header approval

Acquire v1.1.0 from
`https://zenodo.org/api/records/6824749/files/mocks.tar.gz/content` outside Git,
in `/mnt/extdrive/workdir/htt_open_data/sdss_source_null_20261018/`.
Exact total 10,643,218,721 bytes, MD5 `9ba3e8876f6f08a2af00d30cbf1c6cd9`.
The framer qualified the official v1.0 archive as the same MD5/documentation;
use the frozen v1.1.0 endpoint. Inclusive HTTPS byte intervals are exactly
`[0,4294967295]`, `[4294967296,8589934591]`,
`[8589934592,10643218720]`: lengths 4294967296, 4294967296, 2053284129.
Maximum request 4 GiB, 2 GiB free reserve checked before each batch/assembly.
The parent subsequently authorized three concurrent, disjoint network streams.

Require HTTP206, exact Content-Range/length, HTTPS URL; preserve raw status,
headers, ETag if available (otherwise UNAVAILABLE), version, size and checksum.
Reject ignored Range/HTTP200 before consuming huge body. Preserve failures and
partials; resume/assembly only from identity-validated ranges, never redownload
completed chunks or reset accounting. Preserve loaded old/new source identities.
A separately authorized official UI-route probe is at most 1 MiB, not another
bulk chunk. Whole archive size/MD5 must validate before extraction; retain raw
receipts and SHA256. Mismatch here concerns immutable input identity.

Preserve original description PDFs/header files. Frozen identities:

| PDF | Bytes | MD5 | SHA256 |
|---|---:|---|---|
| mock_description.pdf | 82919 | cfa6859a65850e45d195a81993ceb5f7 | 6daf3efd3921bfca653391d4969d17970fa25b14d72ca0fd4588aa3f37fe331e |
| data_description.pdf | 74681 | cb25c71ad9078d61ebdd9882f991c7e9 | 9e167fb6f6e3d5c172e08b42d78187a427c25e2eb275b220dae2441690ae449a |

Qualified sources: Howlett arXiv:2201.03112 sections3–5, Whitford
arXiv:2306.11269v2 section2.4/Data Availability, these PDFs. Only mocks are
needed; observed SDSS data are unnecessary. Complete archive index must contain
256 box identities × eight observers from `...R19XXX.Y_err_corr`, not 2048
certified independent universes. Before scientific outcome reading, freeze exact
member names for the 64 numerically lowest distinct XXX, all with Y0. Use source
angular mask and all galaxy types. Extraction rejects traversal, symlinks and
special files; selected extracted bytes at most 2 GiB, one mock in memory.
Inspect the first selected member's actual header/delimiter/order/format and
precision, retaining a sample and actual mapping. Return to Astra before actual
mock computation if any semantics are unclear; parent/Astra actual-field
approval is required before stage2 source execution.

PDF sequence of 36 fields, **pending actual-header qualification**:

```text
ID RA Dec z_true z_obs z_obs_cen cen_flag subhalomass parenthalomass
deVMag_r gmr kcor extinction_r rtrue r er strue s es itrue i ei
x y z vxcen vycen vzcen vx vy vz nbar logdist_true logdist logdist_err logdist_alpha
```

IDs lexical; cen_flag integer0/1. RA/Dec released equatorial degrees, epoch
UNKNOWN, never relabel J2000. z_obs released CMB observed redshift.
logdist_true=log10[d(z_obs)/d(z_true)]. logdist/logdist_err are the skew-normal
distribution mean/SD, not location/scale. err_corr suffix is unqualified and
must not become observed group-richness logdist_corr. x/y/z are full-box,
not observer-relative. Y0=(250,260,300) h^-1Mpc. Retain source-fitted SDSS
mask/selection/FP-error process; separate-box seed-ledger independence remains
NOT_CERTIFIED. Full CF4 TF+6dF joint mocks are author-request-only; SDSS mocks
cannot replace that joint law. Source flatLCDM Omega_m=.31, H0=100h; no
cosmology computation or peculiar-velocity conversion.

## Stage 2: predeclared mathematics and controls

After actual-field approval use only .01<=z_obs<=.1 for frozen64Y0, all galaxy
types. No added residual/magnitude/other cuts, invalid-row dropping, zero fill
or mock replacement. Reject invalid required values/errors<=0 and noninteger
or non0/1 cen_flag. e_mu=-5*(logdist-logdist_true), sigma_mu=5*logdist_err,
in magnitudes. n=(cosdec cosra, cosdec sinra, sindec), with degree conversion.
Pure D07 basis, parity-tested without importing/running its campaign:
`[nx,ny,nz,nx²-nz²,ny²-nz²,2nxny,2nxnz,2nynz]`.

Exactly k0=1 and k1=exp[-.5*((z_obs-.06)/.012)^2]. Each fit has eight slopes
with profiled free intercept, weights k/sigma_mu²; stack uniform then Gaussian
into16 coefficients/box. Retain weighted scalar mean errors and intercepts.
Reject rank deficiency without ridge. If A_w maps row errors to slopes,
full joint working covariance C_ww'=A_w diag(sigma_mu²) A_w'^T. Gaussian
window covariance is not inverse Gram; windows share rows and are not independent.
This is DIAGONAL_WORKING, not complete source covariance; actual64 box vectors
empirically measure fit/shared-velocity effects.

Output all64 residual vectors and16×16 working covariances; actual coefficient
means/bias and scatter; empirical16×16 covariance; cross-window correlations;
empirical/mean-working diagonal variance ratios. T=max_j|coefficient_j|/sqrt(C_jj),
descriptive threshold norm.ppf(1-.05/32). K/64 is descriptive, not calibrated
physical95% or H02 coverage. No ensemble bias centering, error inflation or
window retuning. Empirical covariance around the sample mean does not recenter
the coefficient vectors used in T.

Controls on designated first selected mock; frozen tolerance 1e-10mag absolute
+1e-8 relative: measuredeta=trueeta gives zero errors/slopes; measuredeta+.01dex
shifts scalar means -.05mag with slopes unchanged; measuredeta+.002nx shifts
nx slope -.01mag in both windows and no other slope; independent full-intercept
weighted QR/SVD agrees; retain soft-window crosscov; reject rank deficiency.

## Limits and handoff

600 seconds cumulative science, separate from network/archive qualification;
one BLAS/OpenMP/MKL thread and one mock in memory. Parent authorized finite
kernel preparation/tests while downloading: charge pure math-test subprocess
wall time to the same SCIENTIFIC_BUDGET.jsonl; six acquisition-boundary tests
are not a mock campaign. Every launched scientific unit/failure counts. Preserve
first failures and partial outcomes at cap/timeout; no resets, replacements,
hidden reruns or tolerance relaxation. Reconcile incomplete budget entries
before continuation. Actual-source execution remains barred before header approval.

Then preserve code/tests/raw outcomes, PNG+PDF/report/candidate for fresh
read-only Astra review. No ODE/MCMC/new mock generation/FP refit/PV conversion,
D07 rerun or nativeBianchi; original D07 97/97 remains intact. Do not execute
upstream Measuring_bulkflows helper fc818a... (known error-weight dimensional bug).
Fixture PASS is not actual-source validation or scientific admission. Original
42-task completion, H02 coverage, CF4 joint law and broader admission stay HOLD;
source-only partials cannot promote them or identify Bianchi families.
