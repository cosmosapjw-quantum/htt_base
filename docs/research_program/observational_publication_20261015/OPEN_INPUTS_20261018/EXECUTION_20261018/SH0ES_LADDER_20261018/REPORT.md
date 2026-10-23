# Source-conditioned full SH0ES ladder and host covariance

Owner `htt`; claim tier `C0`; `CONDITIONAL`, independent review pending.
Scope: one finite GLS reproduction of the released linear Gaussian ladder,
including all 3,492 rows and all 47 parameters. No transfer functions are used.
This new campaign is distinct from D07; D07's completed 97/97 allocation and all
42 original acceptance states remain unchanged. No registry or DAG node is added.

The result is **H0 = 73.042819102 ± 1.007147851 km/s/Mpc** under the released
Gaussian model, using first-order propagation from `5 log10 H0`. This is a
baseline reproduction diagnostic. The formal **1.007** uncertainty is not the
broader published **1.04** uncertainty: no extra error component is inferred,
removed or tuned to reproduce that number. It is not a full CF4 posterior or a
physical eta anchor. The Pantheon+/CF4 joint sampling/calibration law is UNKNOWN.

## Source identity and explicit composite mapping

The numerical inputs are official [DataRelease commit
c447f0fea703fcd0fff57de5000947b5ca81286b](https://github.com/PantheonPlusSH0ES/DataRelease/tree/c447f0fea703fcd0fff57de5000947b5ca81286b).
The official [README](https://github.com/PantheonPlusSH0ES/DataRelease/blob/c447f0fea703fcd0fff57de5000947b5ca81286b/SH0ES_Data/README.md)
identifies C, L and y but does not provide the adopted named parameter dictionary.
That dictionary is explicitly a **COMPOSITE source binding**: released matrices,
the ordered 47-parameter vector in [arXiv:2208.11169v3 §2.1](https://arxiv.org/html/2208.11169v3#S2.SS1),
and the same reanalysis's **named Table 3 Y intervals**. It is not represented as
an original authoritative Riess/SH0ES parameter dictionary. No names are inferred
from fitted parameter values or from Table 2 ordering.

All 37 host indicator supports match their named Table 3 intervals exactly.
The parser reads the versioned primary HTML Table 3 cells, converts the published
one-based inclusive `[first,last]` to zero-based half-open `[first-1,last)`, and
checks every entry. These intervals partition the first 2,150 rows. Additional
released indicator columns are checked over N4258 `[2150,2593)`, M31
`[2593,2648)`, LMC/SMC `[2648,3130)`, calibrator SNe `[3130,3207)`, external
constraints `[3207,3215)`, and Hubble-flow SNe `[3215,3492)`.

Zero-based parameter indices 0–36 are the 37 named host distance moduli in the
order stored in RESULT and NPZ. Indices 37–46 are `Delta_mu_N4258, M_H_W,
Delta_mu_LMC, mu_M31, Delta_b_W, M_B, Z_W, dummy_X, Delta_zp, five_log10_H0`.
The eight external selectors are `[38,38,43,44,45,41,37,39]` exactly. The
dummy column is retained and has its only entry, one, at row 3210. Its actual
covariance diagonal is **9.999999717180685e-10 mag²**; the corresponding standard
deviation is **3.162277615450719e-5 mag**. Its off-diagonal covariance is exactly
zero. A rounded standard deviation in a paper is not substituted for this variance.

The official [read_chains_example.py](https://github.com/PantheonPlusSH0ES/DataRelease/blob/c447f0fea703fcd0fff57de5000947b5ca81286b/SH0ES_Data/read_chains_example.py)
selects parameter 46 and transforms the last coordinate as `10**(q/5)`.
Official [MCMC_utils.py](https://github.com/PantheonPlusSH0ES/DataRelease/blob/c447f0fea703fcd0fff57de5000947b5ca81286b/SH0ES_Data/MCMC_utils.py)
uses `y - q @ L`, confirming the stored L orientation. These files are inspected
as source text; none of their code or MCMC is executed. Official least squares
initialization is not used as an exact numerical oracle.

The README's slope baseline is −3.285; the reanalysis gives −3.286. The result
reports **Delta_b_W = −0.013524447842 mag/dex** and preserves this unresolved
convention discrepancy. Neither baseline is silently chosen to report a total slope.

Raw C/L/y remain in the existing external D03 directory. Their exact prior seals
are verified before reading. L/y have historical `.fits.lfs_pointer` filename
suffixes but are actual FITS, with `SIMPLE` headers and 659,520/17,280 bytes;
the C FITS is 48,781,440 bytes. The separate 133-byte C pointer is not fitted.
The versioned HTML and two official source files are stored only outside Git in
`/mnt/extdrive/workdir/htt_open_data/pantheonplus/shoes_ladder_20261018/`.
RESULT includes resolvable URLs, sizes and SHA-256 values for this review handoff.

## Numerical method and observed acceptance

Use `A = L.T`, preserving actual C exactly (finite, exactly symmetric). Cholesky
whitening solves triangular systems for A and y; columns of the whitened A are
scaled to unit Euclidean norm. Economic QR yields all 47 parameters, and the
inverse triangular factor gives the full 47×47 parameter covariance. The large C
inverse is never formed. A separate SVD of the same scaled whitened inputs gives
a second parameter solution. No reference result determines the solution or tolerances.

| Acceptance quantity | Observed | Frozen requirement |
|---|---:|---:|
| Design rank | 47 | 47 |
| Normalized normal residual | 4.2441670e-16 | ≤1e-10 |
| Relative QR/SVD parameter difference | 1.9790297e-15 | ≤1e-8 |
| Covariance factor reconstruction error | 7.5357993e-16 | ≤1e-10 |
| Residual chi-square / residual degrees of freedom | 3552.7593303 / 3445 | diagnostic only |

The normalized normal residual is `||B.T r|| / (||B||2 ||yw||2)` for scaled
whitened design B and whitened residual r. The covariance reconstruction check is
`||R (D V D) R.T − I||F / sqrt(47)`, where D contains column scales. These exact
definitions, column scales and singular values are retained in RESULT. Chi-square
is not converted into a p-value, independent-survey validation or tension significance.

For the 37-host marginal block Vhost, apply the arithmetic common-mode quotient
`P = I − 11.T/37`. The bundle retains `P qhost`, `P Vhost P.T`, and the unprojected
host mean/covariance. P preserves every host difference and removes one shared
offset. It does not remove all source systematics or establish a physical angular
anchor. The centered covariance is positive semidefinite with rank **36**;
its minimum/maximum eigenvalues are 1.63e-18 and 0.0207253883 mag².
The checks `||P1||`, scaled idempotence, relative covariance asymmetry, and scaled
common-offset invariance are respectively 1.81e-15, 5.08e-16, 1.10e-16, and
1.19e-16, all below the frozen 1e-12 threshold.

## Execution, tests and artifacts

The one campaign completed in **21.479 seconds**, including **7 passing focused
tests**, with two BLAS/OMP/MKL threads and a 300-second total execution cap.
The receipt records raw command stdout/stderr and exit codes. The tests reject
transposed L, swapped named intervals, treating dummy sigma as variance and
nonzero dummy off-diagonals; verify actual block selectors, correlated-covariance
QR/SVD on a separate finite fixture, common-host-offset invariance, and saved
actual covariance dimensions/rank. No optional dependencies were skipped.

The interpreter is the existing `.venv/bin/python`: Python 3.12.3, NumPy 2.5.4,
SciPy 1.18.1, Astropy 8.0.2. The actual campaign HEAD is
`ad27f4cb5f84dfaccc322e53f2810ad29dc72276`, equal to the observed intake HEAD.
The intake branch is `research/htt-open-input-theory-20261018`; origin is the
existing `cosmosapjw-quantum/htt_base` repository. Requested execution identity is
`gpt-6.1-sol/high`; observed model/effort remain `UNKNOWN`.

- `ladder.py`, `test_ladder.py`, `run_campaign.py`: finite implementation and checks.
- `RESULT.json`: source-labelled parameters, units, uncertainties and diagnostics.
- `HOST_COVARIANCE.npz`: 47-vector/covariance, independent SVD vector, named
  37-host marginal and centered arrays, and centered eigenvalues (magnitudes/mag²).
- `HOST_COVARIANCE.png` and `.pdf`: generated covariance heatmap; PNG visually
  inspected for legible labels, units and C0/joint-law caveats.
- `RUN_RECEIPT.json`: one actual execution, raw outputs, code seals and total time.
- `FIRST_FAILURE.txt`: initial source filename 404 and absent optional parser
  diagnostic, both before the successful numerical campaign; no solver failure hidden.
- `CANDIDATE.json`: hashes of this concrete review bundle, excluding the later
  review record; it is a review handoff, not a permanent scientific registry.

Original invocation (do not rerun a completed campaign):

```bash
.venv/bin/python docs/research_program/observational_publication_20261015/OPEN_INPUTS_20261018/EXECUTION_20261018/SH0ES_LADDER_20261018/run_campaign.py
```

## Scoped physics and claim audit

Assumptions: fixed released linear model, released Gaussian covariance, composite
parameter/source mapping, and no additional physical calibration/selection law.
Distances are distance moduli in mag, period and metallicity slopes in mag/dex;
H0 is in km/s/Mpc. No metric, tetrad, sky/redshift reconstruction or transfer
convention is introduced. The sign of the Hubble-flow coefficient is checked as
−1 on `five_log10_H0`. The zero/common-host-offset limit is tested explicitly.

The implemented capability is a source-conditioned ladder covariance and its
36-dimensional host-difference quotient. This is conditional finite numerical
evidence, not an independent measurement of geometry, eta, a CF4 joint posterior,
or a native Bianchi result. Tests do not promote the 42 original acceptance states.
Physical interpretation remains HOLD pending the missing joint law and an
authorized scientific model. Fresh read-only Astra review is required before any
scoped admission/publication decision. No commit, push or global status change
was performed by the implementation worker.
