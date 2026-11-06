# Six-loop observable identifiability: implementation plan

> **For agentic workers:** Execute each task in the existing local checkout only after inspecting its actual live state. Preserve dirty changes and make independently reviewable commits.

**Goal:** Convert six conditional theory loops into source-bound estimators and calibrated multi-probe analysis distinguishing observer boost, global material tilt and geometric anisotropy where the data support it.

**Architecture:** obsstat extracts source-bound features; common owns frame/source/row-order/covariance contracts; htt owns physical response, nuisance quotient and model comparison; bass owns native transfer validation. Each scientific loop writes separate outputs; common synthesis consumes qualified outputs only.

**Tech stack:** Existing Python/NumPy/SciPy/Healpy, repository pytest/codex harness, targeted Wolfram/xAct checks. No invented native Boltzmann solver.

## Global constraints

Baseline d7d5ce2a107b25479b8276f9fd4b5d69dbf53ad9; branch research/htt-six-loop-identifiability-20261106. Inspect local AGENTS.md, branch, HEAD, dirty tree, workers, mounts and interpreter before any write. No reset/clean/forced checkout, no remote desktop, no raw data in Git, no automatic main merge. Keep original42, canonical 273 cards and R37 frozen release unchanged. Use (-+++), four-velocity norm -c², retain c. Do not merge E1/B1 24D and E2/STF5. No source/covariance duplication. Keep nullspace/identified sets; do not fill lost slopes with zero. No Bianchi family identification without validated T/E/B transfer.

### Task 1: PR4 source/estimand reconciliation

**Files:** create new append-only reconciliation JSON and tests/pr_cards/test_pr4_commander_mc100_estimand_reconciliation.py; read R36-06 RESULT, INTERPRETATION, COMMANDER_MC100_AGGREGATE, REPORT_DELTA, INDEPENDENT_REVIEW and manifests.

- [ ] Add failing tests: the two estimand branches PR4_30GHz_AB_PILOT and PR4_COMMANDER_MC100_E_LOWELL validate separately; cross-branch pipeline/source/null/p-value substitution fails.
- [ ] Run focused pytest and preserve the actual RED receipt.
- [ ] Implement a read-only semantic validator; do not edit frozen historical files.
- [ ] GREEN: MC IDs 300–399, feature values and plus-one rank p-values agree across aggregate/review/report delta; old pilot remains separate.
- [ ] Run affected PR4 morphology tests and artifact hash checks.
- [ ] Commit only new reconciliation artifact, validator and test.

### Task 2: physical target response quotient

**Proposed files:** htt/htt/htt/infer/frame_response_quotient.py, tests/htt/test_frame_response_quotient.py.

**Interface:** observable labels, covariance C, physical response R, nuisance response N, target map L, explicit rank tolerance/error policy. Output covariance support/rank, nuisance rank, projected singular spectrum, parameter null basis, target estimability and abstention reason.

- [ ] Test independent boost/tilt columns, collinear columns where only their sum is estimable, target row that annihilates/does not annihilate null direction, singular covariance support, response outside support, nuisance column duplicating a physical column.
- [ ] Run RED.
- [ ] Whiten only resolved positive covariance support, project nuisance via SVD/QR, test ker(P_N C^-1/2 R) subset ker(L). No jitter or silent truncation of unresolved eigenvalues.
- [ ] Run identical focused tests GREEN. Keep assertions unchanged.
- [ ] Independently symbolically check one nontrivial fixture.
- [ ] Commit module/test separately.

### Task 3: nonlinear common model-image and remainder comparison

**Proposed files:** htt/htt/htt/infer/frame_model_images.py, tests/htt/test_frame_model_images.py.

- [ ] Test intersecting/disjoint compact mean images, bounded remainder inflation, unbounded nuisance abstention, and out-of-family residual.
- [ ] Run RED; implement common covariance-whitened norm with typed bounded parameter/remainder sets; run GREEN.
- [ ] Finite-grid minima are exploratory. Do not call a sampled minimum a certified lower bound without a rigorous optimization enclosure.
- [ ] Gaussian noise distributions have common support; mean-image distance is not a perfect classifier. Calibrate power/FPR separately.
- [ ] Commit module and tests separately.

### Task 4: DESI DR1 exact-selection dipole tomography

**Existing code to read:** htt/obsstat/number_count_dipole.py, htt/obsstat/catalogs/spectroscopic_dipole.py, PR151/178/203 contracts.

- [ ] Pin exact DR1 version (v1.2/v1.5), tracer, region, data, randoms, completeness/weights, mocks and data model.
- [ ] Add tests for data/random version mismatch, incomplete randoms, selection mismatch, observed-z migration, duplicate mock use and row-order error.
- [ ] Implement observed-z migration response. Refit full dipole estimator separately in every mock.
- [ ] Verify cross-bin/tracer covariance and finite-mock uncertainty; use held-out mocks and independent tracer holdout.
- [ ] Do not reuse the historically invalidated PR151 covariance unless a new independent review validates this exact estimator.
- [ ] If a gate fails, preserve BLOCKED_INPUT and produce no p-value.

### Task 5: CF4/Pantheon+/Gaia common-frame kinematics

**Existing code:** htt/obsstat/directional_cosmography.py, htt/htt/htt/infer/endpoint_cosmography.py, R36-01..04 results, Pantheon+ source contract and Gaia E1/B1/E2/STF5 artefacts.

- [ ] Verify actual local source bytes, row order, calibration, selection, z definition, distance, covariance and frame.
- [ ] Tests: zHEL/zCMB/zHD mixing, distance/redshift mismatch, row-order mismatch, duplicate covariance, missing frame-spin nuisance, finite-distance remainder UNKNOWN.
- [ ] Keep E1/B1 24D and E2/STF5 distinct. Use existing optical joint operator and finite-distance remainder; no ODE.
- [ ] Fit directional monopole/dipole/STF2 only where identifiable; return PM/radial closure and identified set.
- [ ] Group/method/survey holdout and full cross-window covariance. Raw catalogues remain outside Git.

### Task 6: Bianchi family compatibility / native transfer gate

**Existing code:** htt/bass/background/bianchi_types.py, einstein_bianchi.py, htt/bass/los/bianchi_propagator.py and their tests.

- [ ] Tests: structure-constant validity, constraints, family overlap at FLRW, frame-transform invariance, out-of-family residual, missing-transfer rejection.
- [ ] Implement a typed family-image adapter for supplied family response; do not implement an unvalidated solver.
- [ ] Check Gauss/Codazzi, spatial Ricci, electric/magnetic Weyl, q_a, pi_ab, IC/history and T/E/B transfer provenance.
- [ ] If native validated T/E/B transfer is absent, keep sky-family identification blocked.

### Task 7: six-loop tribunal and synthesis

- [ ] One source-bound result/claim-evidence map per loop.
- [ ] Tests reject missing loop result, duplicate sky/covariance, uncalibrated p-value, unqualified transfer, claim-tier drift and forced label under rank deficiency.
- [ ] Build one common joint covariance; no duplicate likelihood terms.
- [ ] One independent adversarial review after concrete results exist.
- [ ] Prepare manuscript candidate(s) only with a source/prior-art difference table. No journal submission or main merge.

## Commands

At intake run git status --short, git rev-parse HEAD, git branch --show-current, git worktree list; inspect local instructions and exact interpreter. Use repository validate_pr_dag.py and focused pytest commands from current project guidance. Record stdout/stderr, exit code, interpreter, branch/HEAD, config/source hashes and whether the result is actual-data, synthetic or analytic. This plan does not claim any local test has run.
