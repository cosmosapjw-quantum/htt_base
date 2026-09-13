# R9-03/05 and R9-24/25 implementation slice

Owner: root, common/HTT/obsstat by operation. Starting commit:
`9e9539edcdbd7bbf66e458cdce685c7a112f8a04`, branch
`implementation/project-catalog-20260912`. Continue R9 revision 2. User scope
includes implementation, reference replay, one prepared product, independent
review, canonical state/handoff and non-force push/readback.

The exact GPT-6 Astra v4.0.0 research and coding archives were read and applied
to this implementation/validation/review/closeout. `archive_verification.json`
records fresh registered SHA256 and all vendor-member matches. Packaged states
remain unexecuted templates. No initializer or runtime-model switch was used.

## Governing definitions and bounded acceptance

- Preserve REVISION_SPEC.md and THEORY_EXTENSION.md D1–D4/F1–F3. Fixed feature
  H maps Y, mean, response and the complete C. Keep every H C H-transpose term
  and Y0 with its correlations. HTT consumes original Y or invertible T Y;
  MIO depth output is unthresholded diagnostic, never a second likelihood.
- Current R7 `JointObservationLaw`, `gaussian_acceptance`, `condition_gaussian`
  and confidence inversion are the actual consumers. The separately pinned
  donor at 6bafca66 is not merged or imported. New common depth helpers connect
  directly to the branch's R7 API; older scalar donor scores are not relabelled.
- Unknown covariance stays unavailable; known zero and off-support outcomes
  stay distinct. No jitter, rank truncation, fitted covariance/K promotion or
  unsupported Gaussian-innovation assumption. Full-past conditioning uses all
  previous blocks. Actual shared nuisance Jacobians remain active.
- Incidence maps preserve declared units/frame/epoch and physical/observable/
  nuisance/jet/anchor roles. Unit conversions require an explicit upstream map.
- Physical confidence images require one actual common region, its covered
  state/jet/anchor variables, procedure and evidence, coverage target and
  prospective product allocation. Separate marginal regions or metadata alone
  cannot create that event. Fixed-q fibre support is a numerical helper only;
  uncertain q is refused and roundoff-uncertain boundary strata stay unresolved.

## Actual product and scientific limits

The retained DESI DR1 BGS syst qiso HDF5 input has SHA256
`836a2107c1edfb655f7a5c41701607dd8542efe4dae4309737658829cfe63ba3`.
It contains one dimensionless qiso and one variance, not a tomographic law.
The original R7 decoder/API and fresh read-only mapping identified it.
The official [DESI DR1 product documentation](https://data.desi.lbl.gov/doc/releases/dr1/vac/full-shape-bao-clustering/)
was checked 2026-09-13 for HDF5 product and release semantics. The local input
was not replaced with another release. The named v1.2 is retained local source
identity, not a fresh claim that all official likelihoods use that catalogue.

Run raw HDF5 → qiso/covariance → common state → one-block depth representation
→ fixed Gaussian acceptance inversion → conditional interval. Original and
transformed laws are compared. No product has been split into artificial depths.
Full raw-catalogue selection/coverage, multi-depth covariance, physical provider
and jet coverage are unavailable. R9-25 empirical capability is therefore HOLD.

Family alpha remains 1/20; CMB, CF4, distance-calibration, DESI remain 1/80 each;
CMB internal split remains 1/160 each. The DESI interval uses its own 1/80.
Missing product alpha is not redistributed. Mock seed 20260912, 100000 draws,
numerical tolerance 1e-10 and MC comparison tolerance .005 are inherited.
This already explored product supplies conditional pipeline validation, not
new holdout, survey coverage, cosmological discovery or scientific admission.

## Validation matrix and stop

| Cell | Required observation | Evidence |
|---|---|---|
| Source | ZIP/member equality; original runner exits 0 with old evidence untouched | archive_verification.json, baseline_execution.json, baseline/ |
| Full law | cross-block/cross-step signs, level and Jacobian retention, rectangular recovery, duplicate support, missing/fitted law refusals, full-past conditioning | common tests and tests/r9/test_intake_depth.py |
| Images | joint jet/anchor event refusal, point vs full-set distinction, no plug-in uncertain anchors, zero denominator and unresolved fibre boundary | tests/r9/test_confidence_image.py and common fibre tests |
| Product | actual retained HDF5, conditional inversion, 100000 model mocks, active API tail checks | desi_product.json and initial_execution.json |
| Review/delivery | one independent review, one coherent finding-repair closeout if needed, canonical mirrors, ordinary commit/push and remote readback | REVIEW.md, registered review, delivery evidence |

One review round and one repair-closeout episode; unchanged failure retry at
most once; no recursive review or adjacent governance work. Production/CAS,
empirical and novelty admission remain HOLD, including the existing R8
STOP_INVALID, 25 unresolved pools, CF4 quarantine and PR4 skip. Existing frozen
scientific references, alpha and all old evidence are protected.

Grid/timestep/JVP checks are not applicable: this patch adds finite linear maps,
incidence and support operations, not an ODE solver or numerical differentiation.
The original reference runner was executed in a separate source copy because it
writes fixed historical evidence paths. New evidence is stored here. A changed
runtime/plot byte hash is not an automatic numerical/scientific failure.
