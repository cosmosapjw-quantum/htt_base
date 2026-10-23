# Released Pantheon+ source-response contract — 2026-10-18

Framer `/root/pantheon_source_null_contract`, requested `gpt-6-astra/xhigh`,
observed UNKNOWN. Lower-tier execution requested `gpt-6.1-sol/high`, observed
UNKNOWN until independently observed. Base3528fd248bb8dc92105703a7bc91e40d45e3646d;
sole primary checkout and current branch retained. Original42/17completed and
all six NOT_READY_TO_SUBMIT unchanged. Source-conditioned diagnostic only.

Question: within the released LambdaCDM/BS21 selected simulations, how do fitted
stretch/color respond to paired generator state, across source survey, redshift,
realization and genuinely recovered released directions? This is NOT pure
measurement-error calibration or a complete directional selection/null law.

## Sources and hard limits

- DataRelease c447f0fea703fcd0fff57de5000947b5ca81286b, 10 FITRES products
  (5203596bytes) and50 HEAD.FITS.gz products (7006672bytes). Reuse verified
  SIM_0001 and framing acquisitions; raw files outside Git only.
- HEAD groups DES/FOUND/HST/LOWZ/PS1 each10; SDSS/SNLS headers absent from this
  pinned tree. Their absent directions remain unavailable, not inferred.
- Acquire small actual LOGS/SIMLOGS.tar.gz products where present; never execute
  commands or upstream code. All source acquisition<=20000000bytes INCLUDING
  framing acquisitions. No PHOT, SIMLIB regeneration, cosmological fit or new MC.
- Preserve source metadata under external pantheonplus/source_null_20261018/.
  Existing source tree, LOWZ HEAD/log and pinned SNANA code are framing evidence.
- One science execution, cumulative hard timeout120s, <=2numerical threads.
  Preserve first failures and partial results. No window/cut/tolerance retuning.
- Do not touch concurrent SDSS acquisition, its source contract or consumed
  0.322395558/600science ledger; do not rerun D07(97/97), CF4 fits or sky streams.

SNANA v11_04e=3871158844627b3f976e3c0261c466578d6b0a39. Generator SIM_c/x0/mB
are pre-host-dust SALT2 parameters; extinction is separately applied to spectral
flux. BS21/Popovic2112.04456v2 equations3–5 gives E=AV/RV and c_pred=SIM_c+E.
That predictor is NOT noiseless photometry refitted with SALT2. SIM_beta is not
observed beta_SALT2. No naive Tripp or 3D fit-minus-SIM chi-square is authorized.

Actual LOWZ log, not generic INPUT: global magnitude offset−.12, VPEC sigma/error0,
SALT2.MODEL000, seed12359; C11 scale polynomial(c)=0,0. Generic INPUT's G10,
300km/s and seed28473 do not describe this run. Do not apply LOWZ offsets to
other surveys; mB measurement-calibration remains HOLD. Preserve all actual
available source run configurations and seed provenance, not guessed defaults.

## Parsing, identities and direction matching

Parse named VARNAMES (0001has58fields); never assume numeric offsets. Retain
(realization,FITRES path,original row index,CID,IDSURVEY). Candidate HEAD rows
require same realization, literal CID/SNID, exact SIM_LIBID and SIM_NGEN_LIBID.
Check every available paired truth: SIM_ZCMB/REDSHIFT_CMB, SIM_DLMAG/DLMU,
SIM_PKMJD/PEAKMJD, SIM_x0/x1/c/mB/alpha/beta/gammaDM versus actual named
SIM_SALT2 fields, SIM_AV/RV/VPEC. Bind actual field names, not guessed aliases.

Numeric tolerance=half FITRES token's last decimal place plus one ULP of actual
FITS storage dtype at the value. Exact integer fields match exactly. No relative
percent tolerance/nearest matching. Accept exactly one truth-agreeing candidate.
Keep distinct zero-candidate/truth-disagreement/multiple-agreeing statuses. Count
unmatched HEAD rows, all missing FITRES headers, ambiguities and repeated IDs.
Record source SUBSURVEY↔numeric IDSURVEY crosswalk and nonunique mappings.

Preliminary framing probe matched277LOWZ rows in realization0001 with a subset
of truth checks; this is not an oracle for final full-field matching. Realization
0001has21repeated CID occurrences, so CID alone is insufficient.

Matched RA/DEC: finite, 0<=RA<360,−90<=DEC<=90, agree with SIM_RA/DEC within
actual storage precision. Sentinels/mismatches remain unavailable, not normalized.
Label native released RA/DEC; no unverified ICRS/equinox or external rotation.
They are released simulated cadence positions, not a complete angular law.

## Frozen quantities and working covariance

For every otherwise eligible FITRES row, including unavailable directions:
E=SIM_AV/SIM_RV; rx=x1−SIM_x1; rc0=c−SIM_c; rc=c−SIM_c−E. Retain all four;
no optimized coefficients, offset subtraction or clipping. Residual includes
model/source response, not exclusively measurement noise.

Working covariance in order(x1,c): [[x1ERR²,COV_x1_c],[COV_x1_c,cERR²]].
Standardized components and r^T C^-1 r are descriptive discrepancies only, not
Gaussian-calibrated residuals, likelihood terms, p-values or H02 coverage.

Eligibility: ERRFLAG_FIT==0, (CUTFLAG_SNANA &2)!=0, finite required fields,
positive errors, SIM_RV>0, SIM_AV>=0. Preserve every excluded count. No extra
fitted-color/stretch/FITPROB cuts. For quadratic form require positive-definite
dimensionless correlation matrix with mineigenvalue>1e-10. Otherwise retain raw
residual and mark quadratic form numerically unevaluable. No jitter/clipping/
inflation. Serialization/units/field disagreements stop affected claims only;
continue qualified rows and permitted descriptive summaries.

## Prespecified summaries, controls and deliverables

Summaries: all rows, per realization and per numeric survey; truth-redshift bins
[0,.03),[.03,.1),[.1,infinity). Direction-qualified: fixed RAquadrants×north/south
hemispheres, counts and response medians. Fixed statistics count/mean/median/SD/
16th/84thpercentiles for raw and standardized response. Retain per-realization
results and range; no independence assertion or1/sqrt(10)uncertainty reduction.
Record repeated LIBIDs/CIDs across surveys/realizations and known actual seeds.

Deterministic controls: reordered columns; duplicate CID across surveys; ambiguous
candidate; altered truth field; serialization boundary/ULP; invalid RV/errors;
singular covariance; analytic2x2quadratic oracle; zero dust rc==rc0. Fixture PASS
is never physical validation.

Outputs: row-level response/join table; compact summaryJSON; source/config/
acquisition identities and actual command/timing/HEAD; report; PNG/PDF showing
raw/dust-predictor color bysurvey/redshift, stretch/color working-covariance
benchmark, and qualified released sky coverage/color-response sectors. No bogus
direction for missing surveys. Explicit owner/scope/C0/diagnostic/null/working-
covariance/selection-dependence/caveats/mB-HOLD/H02-S02-HOLD metadata. Fresh
separate read-only review precedes scoped publication; code/tests/results/plots/
report may go to existing draft#561 only. No main merge or journal submission.
