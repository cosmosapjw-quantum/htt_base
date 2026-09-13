# Calibration connection independent review

Reviewed at `2026-09-13T08:59:48Z` against worktree
`/mnt/sn850x2t/htt_base_e2e/PROJECT-CATALOG-20260912/worktree`, HEAD
`51ed1e913ac358f9a2569fce8ccb5dc3c1650305`.  This is a scoped native
review of the public-input diagnostic, not a selected-observation-law,
Gaussian-acceptance, four-axis, or scientific-admission result.

## Verdict

`PASS_SCOPED`: no concrete blocking defect was reproduced in the final public
calibration connection.  The public-data point estimate, the saved
coefficients, Tempel input join, operator algebra, and stated non-admission
boundaries agree with the reviewed sources.

## Primary-source and implementation checks

* The assigned production/result SHA-256 identities exactly match the
  registered assignment.  The public SDSS source has 34,059 rows.  Its release
  description defines `logdist` as the mean log-distance-ratio from the one
  full-sample FP fit and `logdist_err` as its standard deviation; it labels
  `logdist_corr` as the group-richness multiple-FP quantity and requires
  group-level zero-point treatment for that latter quantity
  (`data_description.pdf`, rendered lines 45-60).
* CF3 table3 defines individual `Dist` as luminosity distance in Mpc, `DM` as
  luminosity distance modulus, `e_DM` as one-standard-deviation modulus
  uncertainty, and `r_Dist` as the tracer source
  (`CF3_ReadMe.txt:139-149`).  The H and I tracer labels are both
  Tully-Fisher (`CF3_ReadMe.txt:269-280`).  Thus the implementation's
  `D_L/Mpc = 10**((DM-25)/5)`, `D_com=D_L/(1+z)` comparison, `e_DM/5` dex
  conversion, and H/I exclusion agree with the catalog definitions.
* Tempel table1 specifies objID bytes 28-46, GroupID bytes 48-53, Ngal bytes
  57-59, with GroupID zero denoting an isolated galaxy
  (`Tempel2017_ReadMe.txt:53-67`).  The completed join therefore correctly
  treats every zero group ID as an individual singleton instead of aggregating
  them.
* Howlett et al. 2022 section 5.3 says the published corrected ratios use
  separate FP fits by group richness; section 5.4 specifies individual
  redshifts for CF3-modulus conversion, reports the 296 individual overlap,
  excludes two TF cases, and reserves the official value for a 292-group
  consensus with corrected SDSS ratios.  The paper's Data Availability section
  says the exact queries, other code, and data are only available on reasonable
  request.  These facts support the retained `UNAVAILABLE` states and the
  refusal to identify the public 294-row diagnostic with Eq. 25/group-292.
  Source: https://arxiv.org/html/2201.03112 (sections 5.3, 5.4, Data
  Availability).

## Independent numerical evidence

An independent parser of the two raw catalogues, with adaptive quadrature for
the specified flat `Omega_m=0.31`, `H0=75 km/s/Mpc` comoving distance, found:

* exact PGC overlap: 296;
* H/I exclusions: PGC 39712 and 59838; retained: 294;
* public individual diagnostic offset:
  `+0.0004386223475760956 dex`, differing from the saved
  `+0.00043862234757611747 dex` by `2.1846673775582914e-17`;
* all-296 value: `-0.00023510213623531304 dex`, differing from saved by
  `1.883801274693564e-17`;
* maximum saved CF3-eta difference: `2.3592239273284576e-16`;
* saved PGC ordering and H/I mask: exact; saved pair weights and `l`:
  maximum absolute difference `1.734723475976807e-18`; SDSS and CF3 blocks
  of independent `l` sum to `-1.0` and `+0.9999999999999999`.

An independent fixed-width Tempel table1 join found 33,641 matches, 418
unmatched SDSS rows, zero duplicate matches, and zero GroupID/Ngal mismatches.
This is an input correspondence only, not a CF3--Tempel complete crosswalk.

A fresh run of the final runner on the frozen raw inputs produced the same
status, counts, offsets, input/code identities, and exactly equal saved NPZ
arrays.  This verifies artifact-to-input/code replay, while the separate
`execution.json` command/exit receipt does not durably bind the supplied
`CUHG_LAUNCH_ID`; authenticated-launch status is therefore `UNVERIFIED`.

## Covariance and depth-operator review

`calibrate_shared_offset` accepts only an explicitly supplied `[SDSS, CF3]`
joint covariance, transforms cross terms through `D Sigma D^T`, and never
constructs covariance from row errors (`htt/htt/htt/infer/sdss_cf3_calibration.py:170-205`).
`group_consensus_operator` uses errors only for consensus coefficients and
keeps GroupID zero per-row (`htt/htt/htt/infer/sdss_cf3_calibration.py:150-167`).  The R7
PSD decomposition is used at the boundary; unresolved rank, indefinite
covariance, and a singular/unsupported difference law are refused without
jitter or a diagonal replacement (`htt/htt/htt/infer/sdss_cf3_calibration.py:238-254`,
`htt/htt/htt/infer/r7_gaussian_law.py:44-57`).

Direct checks showed an exact-PSD-singular joint law with positive-definite
difference law is usable; a shared-error law whose difference covariance is
singular is refused; and an eigensolver-rank-ambiguous law is refused.  A
separate synthetic full-cross-term calculation confirmed normalized
group-consensus rows, covariance propagation, the shared-SDSS coefficient
construction, and
`G=[M,0]+(M 1)l^T`: zero-row-sum contrasts eliminate its CF3/shared-offset
block, whereas an initial level retains it.  The production runner also
preserves the observed initial-level shift and reports contrast cancellation
(`scripts/observed_runs/run_sdss_cf3_calibration.py:77-107`; saved result
`depth` fields).

## Executed checks

* `OPENBLAS_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -q tests/r9 htt/src/common/test_r9_depth_path.py htt/src/common/test_r9_tensor_functionals.py`
  -> `35 passed in 0.92s`.
* Fresh `run_sdss_cf3_calibration.py` invocation using the assigned SDSS/CF3
  raw paths and frozen CF3 SHA-256 -> exit 0; `result.json` key checks true and
  every `rows_and_coefficients.npz` array exactly equal to final.
* Independent raw parser/adaptive-quadrature point estimate, direct Tempel
  join, and synthetic covariance/operator checks described above -> PASS.

No repair is requested.  The remaining unavailable inputs are correctly
preserved: exact selected survey law and upstream refit, official 292-group
calibration/crosswalk and shared-anchor covariance, physical local/global
response, and a common state-jet-anchor coverage event.
