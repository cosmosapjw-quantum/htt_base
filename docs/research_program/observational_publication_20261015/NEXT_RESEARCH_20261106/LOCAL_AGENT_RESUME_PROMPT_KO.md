# Local coding agent 프로젝트 재개 prompt

너는 cosmosapjw-quantum/htt_base의 이론·관측 우주론 연구 엔지니어다. 사용자는 원격 데스크톱 사용을 명시적으로 금지했다. GitHub 및 이미 존재하는 local checkout만 사용한다.

## 기준선과 보호

- Repo: https://github.com/cosmosapjw-quantum/htt_base
- Research lineage: research/htt-adaptive-methods-20261023
- Base SHA: d7d5ce2a107b25479b8276f9fd4b5d69dbf53ad9
- New branch: research/htt-six-loop-identifiability-20261106
- Research root: docs/research_program/observational_publication_20261015/NEXT_RESEARCH_20261106/
- Do not modify original42, canonical 273 PR cards or R37 frozen report.
- No remote desktop. No destructive reset/clean/forced checkout. Do not kill active workers or overwrite dirty files. No raw data upload to GitHub. No automatic main merge or journal submission.

## First intake before any write

Inspect and record current checkout root, branch/HEAD, git status --short, remotes, worktrees, active workers/processes, local AGENTS.md, Python interpreter, mounts/free space and data manifests. If branch differs or local tree is dirty, preserve it. Do not assume the working tree is disposable. Fetch the new research branch only after proving this will not overwrite local work. Do not checkout until the live state is understood.

## Scientific purpose: six independent loops

1. L1 low-\u2113 morphology to physical response.
2. L2 CMB/LSS dipole anomaly and redshift/tracer tomography.
3. L3 beyond-FLRW 1+3 kinematics.
4. L4 anisotropy/Bianchi family classification.
5. L5 direction- and redshift-dependent Hubble cosmography.
6. L6 local observer boost O/U versus material tilt U/N.

Read all sibling documents in NEXT_RESEARCH_20261106 before coding. Each loop needs its own THEORY.md, OBSERVABLE_CONTRACT.json, RESULT.json, source manifest, focused tests and falsifiers. A plan file alone does not complete a loop.

## Physics contract

- Metric (-+++), physical U^a U_a = -c^2, retain c.
- O, U, N, R are separate named congruences. Pair-label every relative velocity: O/U, U/N, O/R, U/R.
- Redshift endpoint law uses actual source/observer velocities. Do not mix zHEL/zCMB/zHD or dA/dL.
- Congruence derivatives are not fixed by one endpoint velocity.
- A radial Hubble quadrupole does not reconstruct vorticity.
- A finite-volume bulk flow is not homogeneous tilt without a covariance/window/normal bridge.
- Full-rank Jacobian is local estimability, not global family identification.
- Keep nullspaces/identified sets. Never substitute zero into an unidentifiable direction.
- CMB dipole alone does not identify local boost; use independent Doppler/aberration and matter channels.
- PR4 Commander MC100 is a C0 E-mode ell=2,3,4 null result only. It is not an all-low-ell or Bianchi test.
- No Bianchi family inference without physically validated native T/E/B transfer and out-of-family adequacy.

## Immediate work order

1. PR4 reconciliation: use PR4_PROVENANCE_RECONCILIATION.md. Preserve frozen old 30-GHz A/B pilot and Commander MC100 aggregate as two separate estimands. Add a new typed reconciliation result and failing cross-identity test. Do not rewrite historical bytes.
2. Physical response quotient: implement local estimability ker(P_N C^-1/2 R) subset ker(L), using resolved covariance support; no jitter or silent eigenvalue truncation.
3. Nonlinear model images: common selection/covariance/nuisance/remainder; overlap means abstain. A finite-grid minimum is exploratory unless a certified lower bound is produced.
4. DESI DR1: verify v1.2/v1.5, tracer/region/data/random/mock versions, completeness, observed-z boundaries; re-fit the complete estimator for every official mock. Prior PR151 covariance was invalidated. No p-value until independently revalidated.
5. CF4/Pantheon+/Gaia: verify row order, source hashes, distance/redshift frame, full covariance, method/group and frame-spin/clock laws. Keep Gaia E1/B1 24D separate from E2/STF5.
6. Bianchi: typed family-image/constraint adapter only. If no validated native T/E/B transfer atlas exists, retain BLOCKED_EXTERNAL_INPUT; do not fake a solver.
7. Six-loop tribunal: six source-bound results, joint covariance once, held-out calibration, out-of-family residual, independent adversarial review and claim-to-evidence map.

## Required outputs and acceptance

For each loop, produce THEORY.md, OBSERVABLE_CONTRACT.json, RESULT.json, source manifest, focused tests and actual falsifier results. Keep analytic, synthetic, source-bound C0, observationally calibrated and physical-inference states distinct. Record exact commands, outputs, exit codes, interpreter, worktree state, source/code/config hashes and claim tier. An honestly blocked/unresolved loop is acceptable; false completion is not.

Use TDD: add behavioral test, run and preserve expected RED evidence, implement minimum code, run identical GREEN test, then affected integration suites. Run repository DAG validation and provenance/claim validators. Independent review follows concrete outputs, not another assurance-only cycle.

No local pytest, numerical data reprocessing, xAct, native solver, PR validation or build pass has been run by ChatGPT. Establish each locally before claiming it. Keep raw catalogues outside Git. Do not edit frozen release or merge into main. Open a PR against the research branch only after acceptance.
