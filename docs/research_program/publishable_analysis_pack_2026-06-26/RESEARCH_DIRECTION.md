# Research Direction

## Thesis

The next publishable result should not wait for the native low-ell solver. The strongest near-term paper is a three-axis data-analysis paper:

1. math/stat theory: rank-aware finite-sample calibration for low-ell and velocity observables;
2. GR/cosmology theory: visibility-kernel and Volterra-memory bounds that say what the observable channels can and cannot carry;
3. data interpretation: public Planck E2E calibration plus CF4 WF/CR realization conditioning, assembled without converting blind sectors into numbers.

The central claim should be:

> Current low-ell CMB and low-redshift velocity data can support a calibrated rank-aware comparator and named no-go sectors before any native low-ell atlas exists.

This is not a weak claim. It is a precise identifiability and calibration result. It becomes a measured data-analysis result only when K1/K5/K6 blockers close.

## Diverge

Candidate paths considered:

| Path | Novelty | Near-term executable? | Main risk | Decision |
| --- | --- | ---: | --- | --- |
| K1 public E2E max-scan | high | yes | map/mask mismatch | primary |
| CF4 WF/CR K6 posterior | high | depends on realization access | field ownership | primary after K1 |
| CF4 release-matched K5 mocks | high | depends on mock owner | release binding | primary after K1 |
| PR08-006 joint artifact | high | no until K1/K5/K6 close | premature scalar merge | downstream |
| Semi-native single-mode shear transfer | medium-high | yes | overread as atlas | theory appendix |
| Native full atlas | very high | no | absent solver | separate PR10 |
| Legacy evidence figure refresh | low | yes | stale claims | hygiene only |

## Metacognitive Filter

Keep a candidate only if it has all four properties:

- it moves a blocked measurement or theorem boundary;
- it has a falsifiable numerical check;
- it has a manifestable input/output contract;
- it preserves HTT/MIO/BASS/OBSSTAT ownership boundaries.

Reject a candidate if:

- it only changes tone;
- it hides missing data behind synthetic stand-ins;
- it depends on native solver behavior not implemented here;
- it merges MIO diagnostic variables into HTT posterior/evidence semantics.

## Verify

Minimum verification tiers:

1. package synthetic tests: `venv/bin/python -m pytest <pack>/tests -q`;
2. repo harness: smoke, collect, package;
3. research gates: PR04, PR07, EGS2, EGS3;
4. active claim scans on changed files;
5. manifest validation on every generated figure/table/result.

For real-data PRs, add:

- input manifest hash validation;
- dry-run on tiny fixture;
- full run command log;
- generated result row diff;
- independent rerun on a second checkout or clean worktree if feasible.

## Converge

Recommended execution order:

1. Hygiene PR: stale generated/provenance artifacts and invalid manifests.
2. K1 PR: public Planck E2E manifest, summary builder, max-scan output.
3. K6 PR: CF4 realization manifest and affine/curl posterior or no-go.
4. K5 PR: release-matched mocks and coverage/bias report.
5. PR08-006 PR: joint artifact with explicit blind sectors.
6. Theory appendix PR: visibility contraction and Volterra depth-memory theorem proof text plus numerical witness.

## Three-Axis Deliverable Shape

### Math/Stat Theory Axis

Strong result target:

> For a registered response operator, the reachable sector is the image of the response map and blind sectors are provably unidentifiable without additional channel rank.

Executable support:

- `candidate_experiments.py --experiment rank_evalue`
- rank, null-space, and e-value calibration checks.

### GR/Cosmology Theory Axis

Strong result target:

> For a single shear-sourced low-ell channel, the visibility-weighted line-of-sight Boltzmann response is a bounded transfer functional with explicit superhorizon scaling and Gronwall-stable Volterra memory.

Executable support:

- `candidate_experiments.py --experiment boltzmann_visibility`
- low-k scaling and visibility-contraction checks.

### Data Interpretation Axis

Strong result target:

> K1/K5/K6 become measurements only through named external input manifests; before that, the repo can publish the identifiability and calibration design plus any real rows whose input gates are closed.

Executable support:

- `validate_blocker_manifest.py`
- manifest examples for K1 E2E, CF4 realizations, and CF4 release mocks.

