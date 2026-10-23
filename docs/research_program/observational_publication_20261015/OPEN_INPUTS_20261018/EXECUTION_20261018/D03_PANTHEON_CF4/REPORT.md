# D03: actual Pantheon+ / CF4 host graph and conditional distance comparison

Owner `htt`; claim tier `C0`; status `CONDITIONAL`; exploratory, non-claim-bearing.
No transfer functions, native solver, ODE, physical anisotropy inference, posterior,
independent-survey validation or calibrated significance is produced. All original
H02/S02/H04/S04/K04 acceptance states remain conditional/HOLD. Independent review
is pending. The output is a concrete source-conditioned input and statistic bundle.

## Actual result

All **1,701** published Pantheon rows and their original zero-based covariance
order are retained in [OBJECT_GRAPH.csv](results/OBJECT_GRAPH.csv). There are
**1,543 literal CID strings**, not a certified count of independent supernovae.
The graph finds **654** source-coordinate/redshift host associations to **494**
CF4 galaxy PGCs in **482** groups. **559** rows connect to groups in the previously
frozen 35,970-group H02 cache; that cache is read for membership only. The old
large CF4 coefficient/Schur experiment was not repeated.

| Association status | Pantheon rows |
|---|---:|
| Unique named upstream host coordinate and CF4 redshift agreement | 654 |
| Alias absent in pinned upstream metadata | 4 |
| Upstream host missing | 673 |
| No CF4 galaxy host within 3 arcsec | 347 |
| Host-coordinate candidate disagrees in CMB velocity by over 500 km/s | 22 |
| Host PGC exists but its group is absent in the frozen group release | 1 |

The graph uses exact trimmed `SNID`/`IAUC` aliases from the same pinned Pantheon
release, corroborates SN sky coordinates within 2 arcsec, and requires a unique
CF4 galaxy within 3 arcsec of its named host coordinates. The 500 km/s check is a
conservative **association design choice**, not a targeting probability or a
measurement-error model. The source provides 575/677/706 nearest host candidates
within 1/3/10 arcsec before this redshift/group filter. The graph retains every
unresolved row, original CID, survey, calibrator flag, released Cepheid distance,
SH0ES Hubble-flow flag, named host, and nearest-host/second-host separations.
Leading-zero identifiers are retained literally. Multiple metadata aliases with
incompatible host signatures are rejected rather than silently assigned.

These links identify **host aggregates**. They do not establish which individual
supernova contributes to the CF4 SN mean when one host contains several SNe.
The exact EDD contributor list remains `UNKNOWN`. Repeated source rows, shared
hosts, shared groups, and shared calibration ancestry are not independent data.
The 77 released calibrator rows remain in the graph; 65 occur in each comparison.

## Three actual comparisons

The released distance difference is `MU_SH0ES − CF4 counterpart` in magnitudes.
No redshift-distance law or flow correction is invented. Direction is the J2000
unit vector at the supernova; depth is `(zCMB − median(zCMB))/0.02`. These are
descriptive response columns, with no physical cosmographic interpretation.

| Conditional comparison | Rows | CF4 source keys | rho=0 profiled RMS (mag) | rho=0 [nx,ny,nz] (mag) | rho=0 depth (mag / 0.02 z) |
|---|---:|---:|---:|---|---:|
| Same-host SN mean | 651 | 492 host PGCs | 0.07608 | [-0.003188, +0.000672, +0.000039] | +0.006872 |
| Same-group SN mean | 654 | 482 groups | 0.08903 | [-0.004345, -0.000218, -0.010267] | +0.005898 |
| Same-group TF when released, otherwise SN mean | 654 | 482 method/group keys | 0.26694 | [+0.000584, +0.005240, +0.005072] | +0.009486 |

The last control uses 259 TF and 395 SN rows. It is a declared retrospective
method substitution, not a model for survey selection. Different counterparts
change the apparent directional response: the group-SN `nz` coefficient is about
−0.0103 mag, while the same-host value is near zero. This is an interpretable
source/aggregation sensitivity; absent the joint sampling law it has no detection
or significance interpretation. The third control broadens raw residuals and
changes the response again. These three fits share Pantheon observations and
cannot be combined as independent validation.

CF4 galaxy-method distances are registered to the common MCMC scale. Group
method distances are supplied on the arbitrary SN scale described in the primary
ReadMe; the absolute `DMzp` is not substituted. A free common offset is profiled
jointly in each model, so raw offset differences between rows of this table are
not new absolute calibration measurements. Group averaging also changes the
counterpart; no individual SN equality is assumed from a group match.

## Covariance and calibration model

The original Pantheon matrix is untouched. Its maximum asymmetry is
**3.0000000000038676e-8 mag²**. Every calculation explicitly uses its symmetric
part `(C_raw + C_raw.T)/2`, with exact matched-row subblocks in original order.
No published plotting-only diagonal uncertainty is fitted in place of the full
matrix. The selected NPZs retain the full subblocks and exact row indices; tests
compare every element back to the actual released full matrix.

For each conditional model, `B` maps repeated Pantheon rows to their exact CF4
host or method/group measurement key. The **working** CF4 covariance is
`B diag(released_error²) B.T`: repetitions share the same latent released error.
Missing/nonpositive published errors exclude that counterpart and remain unknown;
no zero or error floor is inserted. Independence between different CF4 latent
keys is a conditional modelling choice, not knowledge of the catalogue joint law.
Unknown cross-method/group calibration correlations remain missing evidence.

The nuisance design contains a common offset, calibrator indicator, all observed
survey indicators, and method indicators. All are profiled jointly. The duplicated
one-hot intercept directions are handled by an explicit SVD quotient, with ranks,
singular values, nullspace basis, tolerance, and a labelled minimum-norm parameter
representative recorded for every fit. Rank is 16/18 columns for the two SN
comparisons and 17/19 for the method-substitution comparison; the four direction/
depth response columns retain rank four. No ridge, prior, or hidden gauge is used.
Only the combined nuisance response is identified. No independent angular anchor
is extracted after profiling these calibration variables. The unprojected
response/nuisance designs and raw differences are retained for a later D07 joint
calibration analysis.

The Pantheon–CF4 crosscovariance is **UNKNOWN**, including for shared SN and
Cepheid ancestry. The rho=0 fit is one explicitly chosen working reference, not
zero imputation of a known missing covariance. A designed positive-semidefinite
sensitivity family sets `X = rho Lp U diag(sigma)`, where `Lp Lp.T = P` and
`U = B / ||B||2`. The covariance of differences is
`P + B diag(sigma²) B.T − X B.T − B X.T`. The spectral norm of U is at most one;
the whitened joint Schur lower bound is `1 − rho² ||U||²`. It is 0.4375 for the
chosen rho=±0.75 controls and 1 for rho=0. All residual covariance Cholesky checks
pass; tests independently construct the explicit joint covariance and verify its
PSD property and induced difference matrix, including rho=±1 finite fixtures.

The three chosen values explore **one fixed-order Cholesky-basis family only**.
They are not inferred correlations, confidence intervals, bounds on every possible
unknown crossblock, or a coverage guarantee. The host-SN depth coefficient spans
0.006410–0.006872, group-SN 0.005104–0.005898, and method-control
0.007097–0.009923 mag per 0.02 z in this design. No calibrated coefficient errors,
PTE, p-value, independent-survey statistic, or physical law is claimed.

## Upstream SH0ES ancestry and actual full covariance

The official [pinned Pantheon release](https://github.com/PantheonPlusSH0ES/DataRelease/tree/c447f0fea703fcd0fff57de5000947b5ca81286b)
provides the SNID/IAUC/host metadata and the SH0ES high-level ladder inputs.
The SH0ES covariance raw endpoint contains an LFS pointer. The official GitHub
media route returned the actual **48,781,440-byte, 3,492×3,492 C FITS**; SHA-256
`a42778672d25df7a559bd2949b1e412b99b2e35dd9a36895f6b38828be019172`
matches the pointer exactly. Its C is finite, exactly symmetric as stored, and
passes Cholesky. Actual `L` is stored as 47×3,492 and `y` has 3,492 entries;
both are finite. L/y are actual FITS from raw GitHub, not LFS pointers, even though
their preserved acquisition filenames end in `.lfs_pointer` (first-failure history).

The same pinned release supplies Table 2 Cepheid field names/positions and its
warning that table-only errors omit off-diagonal covariance. All 41 field counts
are extracted in the result. The released Pantheon `IS_CALIBRATOR`, `CEPH_DIST`
and `USED_IN_SH0ES_HF` edges are retained. This establishes resolvable upstream
source ancestry, not a justified numerical mapping from every ladder parameter
to a CF4 calibration variable. The author-labelled parameter/host order has not
been adopted without authoritative mapping. No SH0ES ladder covariance is
mistaken for a Pantheon–CF4 joint covariance, and no upstream code is executed.

The official [EDD schema](https://edd.ifa.hawaii.edu/describe_columns.php?table=kcf4snia)
defines `SNIa` as potentially several SN IDs separated by `/`, lists shared
Pantheon+/SH0ES columns, and describes CF4 common-scale registration. Verified
HTTPS first failed on its certificate chain; the certificate is expired since
2026-07-02. An owner-authorized **transport-unverified exploratory schema**
snapshot was retained, then the ordinary public query returned an explicit
human-verification challenge. That challenge was not bypassed. The EDD response
is never parsed as data, and no scientific admission rests on it. Actual graph
associations use verified HTTPS Pantheon source bytes and the frozen CDS CF4
release, whose byte-by-byte [ReadMe](https://cdsarc.cds.unistra.fr/ftp/J/ApJ/944/94/ReadMe)
defines all PGC/group/method/coordinate fields.

## Verification and reproducible artifacts

Run from the existing repository checkout with the existing `.venv/bin/python`:

```bash
OPENBLAS_NUM_THREADS=2 OMP_NUM_THREADS=2 .venv/bin/python docs/research_program/observational_publication_20261015/OPEN_INPUTS_20261018/EXECUTION_20261018/D03_PANTHEON_CF4/run_validation.py
```

The final actual execution completed analysis, **11 focused tests**, and PNG/PDF
generation with exit zero. Tests cover literal alias preservation, sky mismatch,
ambiguous host aliases, primary ReadMe slices, complete actual row ordering,
all selected full covariance blocks, source hash tamper, shared measurement errors,
PSD/Schur construction, out-of-domain rho rejection, and rank-deficient nuisance
profiling. Reversing the actual data/design/covariance order changes the fitted
responses by at most 1.91e-17 mag. No optional dependency is skipped.

[RUN_RECEIPT.json](RUN_RECEIPT.json) retains real commands, stdout/stderr, interpreter,
packages, two-thread settings, source/candidate identities, and historical first
failure runs. Requested runtime is Sol/high; observed model/effort remain UNKNOWN.
[FIRST_FAILURE.txt](FIRST_FAILURE.txt) preserves the initial EDD TLS failure,
LFS/raw-FITS classification error, ordinary EDD human-verification response, and
the initial figure-file race. Successful analysis was not rerun just to render
the missing figure; the final rerun was justified by added H02 membership and
source-scale/SH0ES ancestry metadata plus a new actual-input validation test.

The [generated JSON](results/D03_RESULT.json), [PNG](results/D03_COMPARISON.png),
[PDF](results/D03_COMPARISON.pdf), graph CSV and three NPZs are the review bundle.
Raw source downloads remain outside Git under the unique D03 external directory.
The source-provided SIM_0001 FITRES has no RA/DEC and is not a directional null.
The PNG is visually inspected before handoff. The manifest is for this independent
review handoff only; no permanent scientific claim/status registry was expanded.

## Claim audit and stopping conditions

| Claim | Owner/status | Evidence | Allowed limit |
|---|---|---|---|
| All published Pantheon rows/full covariance ordering preserved | htt / implemented, tested | actual row/block tests | input bookkeeping |
| 654 coordinate/redshift source associations | htt / conditional | pinned alias+sky+host/CF4 fields | host aggregates only; exact contributor UNKNOWN |
| Counterpart and covariance design alter apparent responses | htt / conditional | actual full-block GLS and three controls | descriptive, no sampling significance |
| Full SH0ES C/L/y is accessible and finite | htt / input-qualified | LFS size/hash, FITS schema and Cholesky | not a CF4 joint likelihood |
| Original H02/S02/H04 acceptance satisfied | none / forbidden | missing joint laws and exact contributor ancestry | HOLD retained |

Resume exact-contributor work only with an actual public export or source-author
snapshot of EDD SNIa aliases/PGC/host/group columns, with normal source identity
checks. Resume physical/calibrated comparison only with a defensible joint
calibration/selection/velocity law or a scientifically justified identified set.
The existing candidate arrays already support such work without repeating source
discovery or the 35,970-group fit.
