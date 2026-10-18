# HTT next coding loop C1–C10: core observation-source acquisition and coherent laws

## C1–C2: Baseline and source mapping

Source checkout: /home/cosmosapjw/Dropbox/bianchi/htt_base.
Starting branch obs/solver-free-dossier-20261014 at
13d8d85fa470d645d008986e8f77d8d0f70fdf54.
Existing user/earlier-loop uncommitted files preserved.

External raw: /mnt/extdrive/workdir/raw; untouched originals.
Official new HM1/HM2/HM-missing intensity source files
acquired create-only to
/mnt/extdrive/workdir/raw/planck_pr3_smica_hm_20261015.
Planck official matrix:
https://irsa.ipac.caltech.edu/data/Planck/release_3/all-sky-maps/matrix_cmb.html
Official mask:
https://irsa.ipac.caltech.edu/data/Planck/release_3/ancillary-data/
CF4 official grouped raw:
https://cdsarc.u-strasbg.fr/viz-bin/ReadMe/J/ApJ/944/94?format=html&tex=true

## C3–C5: Implementation

- htt/obsstat/cf4_shared_selected_law.py:
  exact rank-one shared zero-point Gaussian marginal;
  preselection vs slot-conditioned normalized Gaussian
  truncated likelihood with Gauss-Hermite integration;
  absolute scale/free-offset gauge; velocity error
  broadening scenario; angular WLS morphology.
- scripts/run_htt_cf4_shared_calibration_law_20261015.py:
  authenticated raw table3/4 source, exact 24 group IDs,
  method-specific SN Ia DMsnIa vs dependent DMzp source
  comparison, free-offset gauge, toy velocity/calibration
  sensitivity and selected sampling illustration.
- htt/obsstat/planck_split_joint_law.py:
  exact correlated joint half-mission covariance algebra,
  Schur conditional covariance, validated NESTED
  fine-to-RING coarse map reduction with true missing-mask.
- scripts/run_htt_planck_pr3_halfmission_joint_20261015.py:
  the official 3 source files, source headers/units/coverage,
  exact common support and retained ell2..5 fitted
  coefficient cross, half-sum/diff/full comparison.
- tests/obsstat/test_cf4_shared_selected_law.py and
  tests/obsstat/test_planck_split_joint_law.py:
  Woodbury vs dense Gaussian; both selected experiments;
  scale gauge; independent split covariance and shared
  residual blindness; unit sky HEALPix geometry and
  missing-pixel coarsening.

## C6–C8: Executed validation and numerical evidence

New source files have URL, byte-size and SHA-256 contracts.
Only NEW filenames are written to the external source path.
A source file with mismatched length/header/units fails
before scientific output. FITS sky coordinates/order/
unit held explicitly, no fabricated half-mission noise
ensemble, no full-mission E2E physical null claim.

CF4 actual 24 group results are in
results/cf4_shared_selected_v1: dependent calibration
histogram; four fixed velocity-variance scenarios;
exact free calibration gauge profile; counterfactual
selected-law comparison. This is a scenario study
and source-mapping result, not a new cosmological endpoint.

Planck HM results are in
results/planck_hm_split_v1: HM1/HM2 real
split vector/auto/cross descriptors with proper official
HM missing-pixel mask and past matched K1 full
observed map; one observed sky cannot certify sampling
covariance or PTE.

## C9–C10: Verification, status and next action

The current observed numerical computation checks
mathematical sampling-law normalization and
exact finite-dimensional identities, source hashes,
FITS format, actual map common-pixel counts, and
reported input method group selection. No full end-to-end
Planck instrument/foreground or survey cosmographic
normalization is claimed.

The actual test counts/source digest results
and bounded follow-up tasks are in MANIFEST.json
and INPUT_ACQUISITION.json.
No user raw file was overwritten; only new official
split products are created under their own external folder.
Original PR179 q gate and previous Planck/CF4
blocker registration remain unchanged.

## Expanded C2/C5/C7: release-wide CF4 source audits

scripts/audit_htt_cf4_calibration_mapping_20261015.py:
authenticated Table3 release, complete DMav-to-DMzp
global shift 37,825 groups, direct-only 228 groups,
source-qualified 108 direct-calibrator overlaps and
the original 24 SN Ia-only group method discrepancies.
Authoritative v2 output in results/cf4_release_source_map_v2.

scripts/audit_htt_cf4_individual_calibrators_20261015.py:
authenticates Table2/3 and ReadMe source bytes,
discovers actual marginal direct TRGB, Cepheid, maser
errors and one-to-many group associations, 311 of
336 available direct group IDs connected, 25 unresolved.
Naive inverse-reported-error aggregates agree
to 0.001 mag for only 257 of the 311 joined groups.
Actual aggregator and covariance remain OPEN.
Source result in results/cf4_galaxy_calibrator_join_v1.

htt/obsstat/cf4_shared_selected_law.py additionally
implements a low-rank correlated multi-method
Gaussian with a positive semidefinite shared-offset
prior. Independent tests against a dense Gaussian
and the one-offset reduced case were executed.
This does not supply an actual CF4 K_eta or
complete method-selection likelihood.

New Planck half-mission FITS files were written
create-only under a dedicated external raw directory.
Existing primary raw observations were not modified.
Expected release sizes, actual SHA-256, FITS
NESTED K_CMB unit and official HM missing mask
were checked before observational fitting.


## Source code discovery and execution status

Primary code links and exact applicability contracts are
registered in INPUT_ACQUISITION.json. plancklens and
Volume_Prior are located and examined as literature/code
candidates, but were NOT run as native source-response or
CF4 covariance/selection providers in this loop. No external
repository's scientific result was promoted into an
observed-data posterior.
