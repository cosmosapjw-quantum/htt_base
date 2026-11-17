# PR-R63-LOCAL-BOOST-GLOBAL-TILT

Parent: PR-R62-ANISOTROPY-CLASSIFICATION. Baseline `f29bbab420a33aecb1c398ddd961fd45097f536b`.

## Problem and resulting behavior

Earlier endpoint-frame and tensor-inference work did not bind the compensated matter/radiation history to the actual processed CF4 distance experiment. Rank alone also left open whether a physically admitted tilt could be distinguished from a coherent bulk flow.

R63 derives the processed source/observer/calibration response, reuses the compensated physical subcase, and applies its source kernels through the actual seven CF4 operators with the original full covariance. It distinguishes a pure endpoint boost, constant coherent bulk, free history coefficient and physically tied matter/radiation history. The implementation exposes nuisance-profiled information, weak/null directions and a conditional Gaussian power upper bound.

The release also reconstructs the published additive redshift correction from raw CF4 Table4, transports its difference from a fixed logarithmic chart, and preserves unresolved method-level photometric response. It does not turn catalogue processing into an independent observer-velocity likelihood.

## Scientific delta

- Full dipole/STF data retain three history directions where dipole-only data with the same nuisance are saturated, but the physical history separation is too weak in this retained experiment.
- Corrected J2 W=0 p range 0.182325–0.713944, J3 0.277414–0.696765; no extra history is required under the declared fixed law.
- At alpha=0.1 the oracle power ceiling for the necessary compensated-speed body is 0.100000418731. This is a restricted experiment/model result, not a universal global-tilt impossibility theorem.
- Actual catalogue-chart correction changes the tied effective bulk vector by at most 0.428161 km/s.
- A source-matched remote-dipole response is derived as the finite next discrimination route. No unqualified literature amplitude is adopted as a new physical constraint.

## Validation and publication scope

54 native affected tests passed; the actual-data run and 42 chart transports completed. Exact receipts, source identities and independent review are linked by `VALIDATION.md` and `REVIEW/FINAL_REVIEW_INPUT.json`.

Canonical publication mutation adds one P4 companion card and preserves all earlier cards, original42 nodes and paper acceptance contracts. A finite manuscript plan replaces open-ended repeated CF4 fitting. C0 completion is distinct from publication readiness: P4 remains NOT_READY_TO_SUBMIT.

Only the R63 helper/scripts/tests/docs and authorized DAG/mirrors are included. Existing R62 Bianchi repairs and preexisting untracked work are preserved. No main merge, force push, automatic successor or local-agent restart prompt.
