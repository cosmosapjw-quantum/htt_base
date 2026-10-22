# Public SN010010 — actual light-curve fit and conditional spectral response

Owner HTT, C0 PUBLIC_MODEL_CONDITIONAL_RESPONSE, transfer none. Base120c8a74.
New inputs: publicly released individual PS1MD photometry, compiled KCOR, nominal
MODEL000 surfaces and source-specific overrides/configuration. Next consumers
A22-04/V04/H04 source-processing qualification. Original acceptance remains HOLD.
Independent review pending.

## Actual release, acquisition and frozen contract

The positive source route was found while other remaining inputs were being
checked. The pinned [Pantheon+ release](https://github.com/PantheonPlusSH0ES/DataRelease/tree/c447f0fea703fcd0fff57de5000947b5ca81286b/Pantheon%2B_Data)
contains actual public light curves, filters, KCOR, header overrides and trained
SALT2 surfaces. They must not continue to be called unavailable. CID010010 AND
IDSURVEY15 uniquely identify the published row and photometry SNID010010/PS1MD.
All59measurement rows are retained in input accounting. The36excluded rows are
listed by predeclared band-centre or fixed phase-domain reason;23gri rows enter
this fit. Negative FLUXCAL is not censored; the supplied MAG column is not fitted.

The existing downloader acquired34files/5637453bytes anonymously, preserving2GiB
reserve/stream checks and no per-file/cumulative caps. Raw and decoded model files
are outside Git. Length, gzip CRC, every SHA256 receipt AND Git-blob SHA1 match the
fixed upstream commit. [Source identities](SOURCE_IDENTITIES.json) and
[manifest](ACQUISITION_MANIFEST.json) bind exact bytes. Existing published summary
cache was reused. Six header overrides are read; e.g. HOST_LOGMASS9.50285 replaces
the stale raw header10.104. No cosmological quantity is inferred from this change.

[CONFIG.json](CONFIG.json) was frozen before fitting after read-only Astra source
intake. Use zHEL=.0984 and times relative to MJD55238.9, not divided absolute MJD.
Fixed original gri filter centres/rest in3000..7000A and published-anchor rest
phase[-15,45], t0 within±5observer days, stay inside MODEL000 phase[-20,50]. Entire
nonzero transmission support must remain in actual surface wavelength[2000,9200]A.
The3000..7000range is a filter-centre requirement, not a spectral truncation.

`sncosmo.SALT2Source`2.13.1 applies its1e-12surface scale once. It does not consume
SALT2.INFO. We explicitly apply INFO MAG_OFFSET=.27 as10^(-.4*.27), and use compiled
original PS1-g/r/i transmissions and primary magnitudes−.0342/−.0377/−.0264.
The `*PS1` columns are wavelength-shift duplicates and are excluded. Compiled AB
primary SED integrals define the FLUXCAL normalization; differences from a3631Jy
analytic AB reference are measured, not hidden. A calibration-only primary probe
returns10^(.4*(27.5−p_band)); the SALT-only.27offset is not applied to that probe.
Photon weighting uses lambda*T(lambda) with common hc cancelling against the
same primary integral. Actual wavelength is Angstrom, flux density erg/cm²/s/A.

Public PPLUS.yml MWSTUFF specifies F99,Rv3.1,MWEBV_SCALE.86: E(B−V)=.0204*.86=.017544,
applied once. Source genmag_SALT2.c qualifies MAG_OFFSET and filter-centre semantics.
The released directory says B21 while the [data paper](https://arxiv.org/abs/2112.03863)
describes B22b training; those names are not equated. Exact MODEL000 files bind this
experiment. Unreleased PS1.nml/private nominal-model path and observed FITRES are
absent, so released-pipeline parity is an explicit separate question.

## Working likelihood and failed empirical-baseline screen

Fit(t0-relative,lnx0,x1,c) with diagonal measurement FLUXCALERR chi-square. Bounds
and stopping/rank criteria are frozen. No model covariance, INFO error floor,
global calibration perturbation, host/BBC correction or PV term is added. The fit
is a declared working model; producer likelihood parity is not assumed.

All numerical convergence/interior/objective/rank checks pass. With23rows/19dof,
chi-square=61.41424 and reduced chi-square=3.2323283. This FAILS the predeclared
<=3adequacy screen: **BASELINE_ADEQUACY_HOLD**. No error inflation, clipping,
calibration tuning or cut change was made. Published summary chi-square=12.4905
is not reproduced by this different working likelihood.

Relative to the published summary, fitted x0 differs by−1.03098%, x1 by−.120571,
c by+.0104245, t0 by+.006872day. The frozen parity screens(x0 .1%, shape.001,
t0 .01day) yield **PARITY_NOT_REPRODUCED**. Missing model-error configuration and
private fit inputs prevent attributing that difference to a specific producer
component. The model may still be transported as an explicitly inadequate
conditional spectral fit; it is not an empirical release reconstruction.

## Paired finite transport and a processing nonidentity

Freeze delta={.99,.999,1,1.001,1.01}. The transformed target is generated from the
entire fitted attenuated SED: f'_lambda(t',lambda')=delta³*f_lambda(delta*t',delta*lambda'),
with all times relative to the common anchor. It is not obtained by transporting
observed broadband residuals or treating them as spectra. Passbands/calibration
stay fixed. Original errors are only a deterministic weighting norm, not measured
boosted errors. Global alpha,beta,host,BBC and PV responses remain absent/symbolic.

The covariant refit evaluates MW attenuation at delta*lambda', uses
1+zHEL'=(1+zHEL)/delta and recovers x0'=delta²*x0, unchanged x1/c, and
relative t0'=t0/delta. Maximum amplitude defect<=9.65e-16mag. A second deliberately
frozen-observer-MW experiment evaluates attenuation at lambda' instead. It gives:

| delta | conditional amplitude defect (mag) |
|---:|---:|
|.99|+.0007938532|
|.999|+.0000795718|
|1|0|
|1.001|−.0000796124|
|1.01|−.0007977986|

This response belongs to this source-model/calibration/MW operator, not a bound on
Pantheon total kappa. Changed x1,c,t0 are stored; any standardized-magnitude
response still has symbolic alpha*Delta x1−beta*Delta c and missing global terms.
The no-boost control is zero. The.5A→.25A quadrature comparison gives6.47e-8maximum
relative photon difference. At delta1.01 the frozen-MW refinement shifts ln x0 by
7.89e-12, versus a measured amplitude defect~8e-4mag, resolving this conditional
nonidentity well beyond ten times measured refinement uncertainty. It does not
resolve the inadequate baseline or empirical global pipeline response.

## Validation and preserved failures

Three narrow tests pass in8.66s: full source/row/override identity, primary-flux
normalization, finite covariant photon transport, frozen-MW negative control,
extrapolation rejection and quadrature refinement. Initial parser failures are
preserved: first1FAIL/2PASS on empty END: metadata value(IndexError); after fixing
empty-value parsing,1FAIL/2PASS on override schema(SN: prefix). The second repair
parses exact SN:/CID/value triples while preserving unique-ID enforcement. No
scientific tolerance was relaxed. Final15Astropy warnings concern unchanged
upstream `*PS1-*` column names; these excluded shifted columns are preserved.

The initial outside-Git SNCosmo import failed on missingh5py; installing its
requiredh5py/looseversion dependencies there resolved the import. Runtime packages
sncosmo2.13.1,extinction.4.9,h5py3.16.0,looseversion1.3.0 are outside the repo venv
and imported explicitly. This is not a native Bianchi solver or evolution run.

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q docs/research_program/observational_publication_20261015/ADVERSARIAL_AUDIT_20261022/continuation/sn010010/test_refit.py
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 .venv/bin/python docs/research_program/observational_publication_20261015/ADVERSARIAL_AUDIT_20261022/continuation/sn010010/refit.py
```

[Result](RESULT.json), [figure](REFIT.png). Full BBC biascor requires author-contact
per release README, PS1.nml and nominal private model binding/FITRES are absent,
and PV/group correction under reboost has no qualified joint source law. These are
specific remaining payloads/formulas. No Pantheon total covariance was reused and
no stochastic PV variance added. Original V04/H04 and all paper gates remain open.
Requested parent Sol/high, framing/review Astra/xhigh; observed UNKNOWN.
