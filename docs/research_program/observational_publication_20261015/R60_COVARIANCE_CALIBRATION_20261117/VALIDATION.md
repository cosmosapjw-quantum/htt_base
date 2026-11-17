# R60 validation and implementation record

The scientific candidate was checked against baseline 6fe19c5139004a1f281ec85c592e5ab4c7590d5f in the owner's existing checkout. R58/R59 scientific artifacts and pre-existing untracked work were preserved. Final generated products bind the final candidate source hashes below; their source_read_head remains the honest pre-commit baseline, because execution preceded the release commit.

## Actual final execution

Production environment: Python3.12, NumPy2.5.4, SciPy1.18.1, one BLAS/OMP thread, PYTHONPATH set to htt/src:htt:. (repository root). Full argv, timestamps, exit status, logs, preceding generated-output hashes and failure recovery are in [EXECUTION_RECORD.json](EXECUTION_RECORD.json).

| Execution | Final observed status |
|---|---|
| CF4 covariance/calibration sensitivity | exit0; final module and amplitude hashes match |
| Raw-operator finite radial response and bounded budgets | exit0; final module hash matches |
| Commander deterministic morphology from owned carrier | exit0 |
| Quaia/NVSS sensitivity from owned R54 result | exit0 |
| Focused changes plus R58 mean-likelihood/five-view regression | **56 passed in1.55s**, exit0 |
| Independent fixed-C/calibration/axial oracle on final products | exit0 after serialization-only repair |
| Independent radial/physical-chart/budget oracle on final products | exit0 |
| Existing axial-witness result | reused under unchanged code/source; all witnesses rechecked by final oracle |

The actual pytest argv was:

    OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 PYTHONPATH=htt/src:htt:. \
      .venv/bin/python -B -m pytest \
      htt/src/common/test_covariance_amplitude.py tests/r60 \
      tests/r58/test_mixed_tensor_likelihood.py tests/r58/test_five_views.py -q

This is a focused scientific regression suite, not a claim that every test in the repository or every legacy downstream result has been rerun. Existing consumers of the repaired amplitude estimator outside the tested scope may require recomputation before their old reported values are used.

## Final implementation identities

| Path | SHA-256 |
|---|---|
| htt/src/common/covariance_amplitude.py | 911217a7ec77df26794da149ad1207c9565bc63b73d68cdf6958ad3420b2b1bd |
| htt/htt/htt/infer/r60_covariance_calibration.py | df627106d768a17c0a7942baa18afe4793f9226b41232839c2005dce9270c310 |
| tests/r60/test_covariance_calibration.py | 4d99dc6fd61bf866e2fe23f734efdaecc2df5606138aa71697f88e888f22c700 |

The source manifest is computed after artifact assembly. It excludes itself to avoid a circular hash. The eventual Git commit provides the immutable package identity.

## Independent numerical evidence

The reviewer initially used Python3.12.3/NumPy2.4.2/SciPy1.17.0, then verified the repaired edge cases in the production environment. Its actual-data oracle implements pivoted-QR GLS, direct logdet likelihood and constrained checks independently of the new R60 module.

Final production replay of that independent oracle found:

| Identity | Maximum error |
|---|---:|
| Scaled fixed-C estimate vs independent QR | 9.03e-15 |
| Scaled covariance relative error | 9.65e-15 |
| Block Wald vs profiled residual LR | 6.40e-14 |
| Direct covariance-amplitude log-likelihood gain | 1.71e-13 |
| Fixed contrast vs REML determinant identity | 5.69e-14 |
| Physical radial design/chart identity | 2.44e-17 |
| Physical14D estimate vs independent QR, scaled | 1.36e-12 |
| Radial covariance relative error | 4.03e-15 |
| Radial block Wald vs LR | 4.91e-10 |
| Finite nuisance-budget KKT relative residual | 2.31e-12 |
| Independent radial critical-threshold error | 3.04e-10 |

The scalar calibration run contains210 witnesses and the radial run84 finite-budget witnesses. The actual oracle JSONs contain the individual checks, feasible budgets and source identities. These are finite floating-point checks, not formal interval arithmetic.

Commander normalization was independently checked with Cartesian harmonic polynomials, complex-harmonic synthesis, the retained source template and angular quadrature. The main5x5/3x3 representation is deterministic; no Commander null distribution was fabricated. Count-dipole endpoints exactly reproduce the saved nominal Gaussian values; original finite-mock tail objects remain unchanged.

## Failures, repairs and scope

1. **Inherited implementation/numerical error:** amplitude_mle assumed a monotone score and returned0 for nonpositive boundary score. An exact two-mode counterexample has an interior global maximum. The production consumer now calls a bounded global numerical objective solver.
2. **F01 — resource convergence:** the first separable interval bound exhausted200,000 intervals on a valid400-mode input. Adding an aggregate-score midpoint Taylor bound resolved the same case in54 intervals with objective gap4.26e-9. The regression and the failed/successful observations are preserved in the independent review.
3. **Root-boundary rounding:** a calibration outer endpoint straddled an equivalent norm by1ulp. Feasible boundary handling repairs the bracketing error. The first actual execution failure log is retained.
4. **F02 — unresolved nuisance mode and multiplier accuracy:** a small but nonzero mode cannot be silently removed when a finite nuisance budget makes it relevant. Unresolved modes now raise. Active multiplier solves use smallest positive xtol, relative tolerance1e-13, maxiter256 and an explicit budget-residual check. diag(1e8,1), radius2 now gives witness(0,2), distance²1; diag(1e13,1), radius3 fails closed.
5. **Runtime serialization compatibility:** final replay of the review oracle completed numerical calculations but JSON serialization rejected SciPy1.18.1's numpy.int64 rank. Casting rank to Python int repairs output serialization. The failure log and recovery are separate entries in EXECUTION_RECORD; the mathematical oracle is unchanged.
6. **Physical approximation boundary:** the free14D velocity-slope fit required0.159–0.531c. It is retained as a formal response/identification diagnostic. The physically interpretable sensitivity statement uses declared finite budgets and keeps their assumptions explicit.

No permission or network blocker prevented the code/data work above. The remaining physical limitations concern input laws and transfers, rather than a test runner failure.

## Reproduction

Run from repository root with the same environment. Every result generator writes a separate requested output. CF4 sensitivity and radial generators refuse nonempty output directories.

    .venv/bin/python -B scripts/r60/run_r60_sensitivity.py --output /tmp/r60_sensitivity_replay
    .venv/bin/python -B scripts/r60/run_r60_radial_velocity.py --output /tmp/r60_radial_replay
    .venv/bin/python -B scripts/r60/run_r60_axisym_witness.py --repository-root . --output /tmp/r60_axisym.json
    .venv/bin/python -B scripts/r60/run_r60_commander_morphology.py --repo-root . --out /tmp/r60_commander.json
    .venv/bin/python -B scripts/r60/run_r60_count_dipole_sensitivity.py --repository-root . --output /tmp/r60_counts.json

The independent oracle scripts run from repository root against the recorded R60 output paths. Their historical filenames record reviewer provenance; they are not a new production likelihood implementation.

## Structural validation

Canonical PR backlog/status, machine-readable mirrors and publication-DAG pointer changes use the existing validators. Their actual outputs are stored separately as DAG_VALIDATION.json and logs. The original six publication tracks and42 scientific node states are unchanged. Completing PR-R60 means the scoped science package is complete, not that those original physical/publication gates have all passed.

A visual inspection of the generated covariance/calibration figure confirmed its axes, legends, target dimensions and finite sensitivity interpretation. No generated illustrative image is used for quantitative data.
