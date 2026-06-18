# Revision Plan Crosswalk

owner: COMMON
implementation_scope: common
claim_tier: diagnostic_only
transfer_source: none
sky_support_status: not_directional
null_mock_status: not_statistical
caveats:
- external/proxy transfer is not native transfer
- family identification remains blocked until native morphology atlas support exists
- scaffold package outputs are not publication evidence


## Relation To Existing Plan

The conservative repair plan clears external-audit rejection triggers. This upgrade adds novelty preservation, experiment staging, literature CRAG, and a supplemental R-DAG.

## Novelty To Experiment Map

| Novelty | Experiments | Manuscript home |
| --- | --- | --- |
| N1 | E3 | Chapter 3 framework and Chapter 7 occupancy repair |
| N2 | literature CRAG | Introduction and discussion |
| N3 | E2,E7,E8 roadmap | Dipole anomaly and results caveat boxes |
| N4 | conservative-plan closure correction | Chapter 5 |
| N5 | claim lanes and audit package | Methods and appendices |
| N6 | E3 | Results and appendix table |
| N7 | E5 | Future and forecast results |

## Experiment List

- E1: Prior floor and ceiling sensitivity surface plus fractional/intrinsic Bayes factor. Owner: HTT. Guard: conditional candidate only after prior/null/PPC status exists.
- E2: Bulk-flow sigma-beta uncertainty band plus look-elsewhere correction. Owner: HTT. Guard: conditional on external/proxy transfer provenance.
- E3: Per-channel occupancy vector across model rows. Owner: MIO. Guard: diagnostic_only; no posterior or truth language.
- E4: Deterministic quadrupole template likelihood versus stochastic covariance treatment. Owner: HTT. Guard: requires matched covariance/null status before evidence wording.
- E5: Tomographic degeneracy-breaking forecast for local boost and global tilt. Owner: HTT/obsstat. Guard: forecast lane only.
- E6: Posterior-predictive and LOOCV adequacy checks for any evidence-grade HTT wording. Owner: HTT. Guard: blocks promotion until passed.
- E7: Cross-survey covariance model for shared clustering-dipole uncertainty. Owner: obsstat/HTT. Guard: conditional on covariance implementation.
- E8: Native low-ell morphology atlas roadmap only; no implementation in this repo state. Owner: BASS_native. Guard: specified future interface; no native-transfer claim.

## Supplemental PR Slice

- PR-R000: Promotion-model audit over existing ArtifactMode and AllowedUse; depends: none; status: proposed
- PR-R001: Status snapshot lane propagation; depends: PR-R000; status: proposed
- PR-R002: Figure manifest lane and forbidden-use fields; depends: PR-R000; status: proposed
- PR-R003: PDF-level claim lint integration; depends: PR-R001; status: proposed
- PR-R004: Revision claim freeze rows for safe framework wording; depends: PR-R001, PR-R003; status: proposed
- PR-R010: Prior support sensitivity surface; depends: PR-R002; status: proposed
- PR-R011: Bulk-flow uncertainty propagation band; depends: PR-R002; status: proposed
- PR-R012: Rule-of-three FPR intervals; depends: PR-R002; status: proposed
- PR-R013: MES algebraic ceiling versus observational-bound calibration; depends: PR-R002; status: proposed
- PR-R020: Per-channel occupancy vector; depends: PR-R000; status: proposed
- PR-R021: Certified filling status and invalid-sector handling; depends: PR-R020; status: proposed
- PR-R022: Depth-gap G_F epsilon floor and uncertainty kind; depends: PR-R021; status: proposed
- PR-R023: Component filling anatomy; depends: PR-R021; status: proposed
- PR-R030: Local/global response-rank audit; depends: PR-R002; status: proposed
- PR-R031: Local boost-only G_F null; depends: PR-R022, PR-R030; status: proposed
- PR-R032: Global-tilt injection recovery; depends: PR-R022, PR-R030; status: proposed
- PR-R033: Survey-axis and selection-response nulls; depends: PR-R031; status: proposed
- PR-R034: Cross-survey covariance model; depends: PR-R033; status: proposed
- PR-R040: Deterministic-template likelihood branch; depends: PR-R002; status: proposed
- PR-R041: Stochastic covariance likelihood branch; depends: PR-R002; status: proposed
- PR-R042: Template-versus-covariance sensitivity report; depends: PR-R040, PR-R041; status: proposed
- PR-R043: Scalar equivalence-class graph with family identification blocked; depends: PR-R020, PR-R042; status: proposed
- PR-R050: Posterior-predictive checks; depends: PR-R034, PR-R042; status: proposed
- PR-R051: LOOCV held-out probe test; depends: PR-R034; status: proposed
- PR-R052: Prior covariance null sensitivity dashboard; depends: PR-R010, PR-R011, PR-R012, PR-R034; status: proposed
- PR-R053: Manuscript strong-evidence wording replacement; depends: PR-R003, PR-R052; status: proposed
- PR-R060: Regenerate figure suite with manifests and source JSON; depends: PR-R052, PR-R053; status: proposed
- PR-R061: Build reviewer packet; depends: PR-R060; status: proposed
- PR-R062: Independent CoVe run and final response table; depends: PR-R061; status: proposed

Supplemental row count: 29 proposed PR rows spanning PR-R000 through PR-R062.
