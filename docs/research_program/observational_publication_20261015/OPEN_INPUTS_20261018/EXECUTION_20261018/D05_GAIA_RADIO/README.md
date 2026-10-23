# D05: full Gaia-CRF3 and radio observable analysis

Owner `obsstat`; scope `DIAGNOSTIC_ONLY`; transfer source `none`. This packet
measures harmonics of published apparent proper motions in a specified celestial
frame. It does not supply a physical matter-congruence response for K03.
Independent review is pending; no scientific-node acceptance is asserted here.

Inputs and source identities are consumed by `observable_vsh.py` and recorded in
`RESULTS.json`. Raw rows, membership, UWS responses and radio crosswalk remain
outside Git, under `/mnt/extdrive/workdir/htt_open_data`.

The original full query in `../../GAIA_CRF3_QUERY.adql` has no TOP clause. Its
result must have only `QUERY_STATUS=OK`, unique IDs, the same number of rows as
the separate matching COUNT, and exactly the source-ID set in the official ESA
CRF3 membership release. Any failed condition stops analysis. MAXREC is
2,500,000, above the 1,614,173-member catalogue; an overflow is never accepted.

ARI UWS job metadata is stored before starting the database query. Existing
job files are reused after interruption, rather than submitting replacements.
To poll and collect the same jobs:

```bash
.venv/bin/python docs/research_program/observational_publication_20261015/OPEN_INPUTS_20261018/EXECUTION_20261018/D05_GAIA_RADIO/tap_acquire.py full --collect
.venv/bin/python docs/research_program/observational_publication_20261015/OPEN_INPUTS_20261018/EXECUTION_20261018/D05_GAIA_RADIO/tap_acquire.py count --collect
.venv/bin/python docs/research_program/observational_publication_20261015/OPEN_INPUTS_20261018/EXECUTION_20261018/D05_GAIA_RADIO/tap_acquire.py frame --collect
OMP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=2 MKL_NUM_THREADS=2 .venv/bin/python docs/research_program/observational_publication_20261015/OPEN_INPUTS_20261018/EXECUTION_20261018/D05_GAIA_RADIO/observable_vsh.py
OMP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=2 MKL_NUM_THREADS=2 .venv/bin/python docs/research_program/observational_publication_20261015/OPEN_INPUTS_20261018/EXECUTION_20261018/D05_GAIA_RADIO/plot_observable_vsh.py
.venv/bin/python -m pytest -q docs/research_program/observational_publication_20261015/OPEN_INPUTS_20261018/EXECUTION_20261018/D05_GAIA_RADIO/test_observable_vsh.py
```

The query URLs and complete collector receipts are in the external
`gaia/d05_full_20261018/*.job.json` files. Collection is capped at 2 GiB per
product and requires at least 2 GiB of additional disk reserve. A failed partial
is preserved and blocks an automatic repeat download. The membership was
acquired through the existing manifest consumer; the radio inputs were supplied
by parent D01 and were not fetched twice.

## Observable conventions and interpretation

Positions are ICRS RA/Dec in degrees at Gaia epoch J2016.0 TCB. Gaia `pmra` is
the east tangent component `mu_alpha*cos(delta)` and `pmdec` the north component,
initially in mas/year and converted to microarcseconds/year. For each source
the measured 2x2 covariance includes the published component correlation.
Position errors and position-motion correlations are retained in the raw query
but directions are conditioned on as exact in this fit. This is a working
observable fit, not a re-solution of the astrometry.
CRF3 membership was itself selected using astrometry, including proper motions.
The complete released membership is therefore an outcome-selected catalogue;
its completeness is not a claim of unbiased QSO population sampling.

The finite harmonic basis is `E1=P g`, `B1=omega cross n`, `E2=P S n`, and
`B2=n cross S n`, with `P=I-n n^T`. The five STF matrices are explicitly stored
and Frobenius orthonormal. Their coefficients are Cartesian coordinates, not
normalized scalar-Ylm coefficients or power amplitudes. Degrees l=1 and l=2
are fit jointly with all retained source component covariances. B1 spans the
same three columns as arbitrary celestial-frame spin. The Schur quotient
marginalizes those three columns and reports physical B1 as UNKNOWN, rather
than treating a near-zero in-frame spin as a cosmic constraint.

Frame-rotator source flags distinguish the spin-used and other-source subsets.
Those fits share attitude, calibration and frame construction, so their
agreement is not independent validation. DR3 and EDR3 have identical astrometry
and are not counted as independent observations. Previously completed 4,756-row
frame/correlation diagnostics are referenced and not rerun.

Twelve coarse equal-area cells (four RA quadrants times three sin-Dec intervals)
provide whole-source angular holdout. Leaving out both components of every
source in each cell avoids component leakage. The deletion envelope and block
score scatter are sensitivity diagnostics; they are not a calibrated spatial
covariance, p-value, null ensemble, or coverage guarantee. The published
per-source covariance does not supply cross-source covariance.

The 713-source radio table has marginal errors but lacks cross-component and
cross-source covariance. Missing correlations are not filled with zero. Fits
are evaluated under nonzero common-component correlation scenarios -0.9, -0.5,
+0.5 and +0.9. This finite family does not bound every allowed per-source
correlation vector. The CDS ReadMe does not explicitly distinguish RA coordinate
rate from the tangent component; both cos-Dec conventions are retained as
separate scenarios, with no data-based choice of a preferred interpretation.
Unique positional matches within 1 arcsecond and catalogue-name checks are a
crosswalk, not proof of independent errors. Radio jets, optical-radio offsets,
epoch differences, ICRF overlap and the Goddard NNR frame construction remain
material to a combined physical analysis. A missing frame transfer is not zero.

## Primary references checked 2026-10-18

- [ARI public TAP service](https://gaia.ari.uni-heidelberg.de/tap.html): ADQL service and result formats. The live server rejected `votable/binary2`; its accepted binary alias `votable/b2` was used and the error preserved.
- [IVOA UWS 1.1](https://www.ivoa.net/documents/UWS/20161024/REC-UWS-1.1-20161024.html): durable job URL, phase and result semantics.
- [Gaia-CRF3 paper, arXiv:2204.12574](https://arxiv.org/abs/2204.12574), [journal DOI](https://doi.org/10.1051/0004-6361/202243483): source selection, frame rotator, reference frame and spatial systematics.
- [Gaia DR3 survey properties](https://doi.org/10.1051/0004-6361/202243940): EDR3/DR3 astrometry reuse and celestial frame.
- [Truebenbach & Darling 2017, arXiv:1710.02099](https://arxiv.org/html/1710.02099), [CDS original ReadMe](https://cdsarc.cds.unistra.fr/ftp/J/ApJS/233/3/ReadMe): radio catalogue, coordinate table definitions, radio jets and NNR dependence.

## Kill switches and claim ceiling

Stop on a non-OK/overflow TAP status, COUNT/member mismatch, duplicate source
IDs, invalid retained covariance, missing frame columns, failed algebra test or
singular identified quotient. Preserve all failures. A publication-grade
combined physical analysis additionally needs the common-congruence response,
radio-coordinate convention, source/systematic covariance and frame/calibration
transfer. K03 remains HOLD while those inputs are unavailable. No native solver,
ODE, posterior, cosmic-curl detection, geometry or family identification follows
from this packet.
