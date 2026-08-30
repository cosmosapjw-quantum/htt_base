# PMG-WU-009 full-replay theorem reconciliation implementation plan

Status: approved for implementation  
Date: 2026-08-30 UTC  
Approved design: `docs/superpowers/specs/2026-08-30-planck-mes-wu009-full-replay-theorem-reconciliation-design.md`  
Remote design head: `bda8e489bff7c26fb5fb03fba59360028d01a2fe`  
Remote design tree: `aa734e7933efc6f763d49aaf9f0d9c1bdad6b3b1`  
Scientific base: `5e81ed1635b8fe6fc944829a9fab7ab8d5b8c654`  

## 1. Delivery boundary

Implement every map-free, source-backed part of the approved WU-009 design in
this branch.  Do not alter WU-006, WU-007, or WU-008 generated artifacts; do
not reopen raw maps; do not invent the unavailable formal theorem dossier; do
not regenerate claim-bearing paper artifacts from an unsealed successor
result; and do not merge the scientific pull request.

The implementation must preserve these distinctions:

- theorem statement versus materialized proof evidence;
- representation identification versus physical-cause identification;
- historical finite-pool ranks versus a corrected successor result;
- same-sky robustness versus independent replication;
- deterministic polarization morphology versus calibrated E/B inference;
- executable map-free checks versus local-only raw/CAS replay.

`FORMAL_DOSSIER_PENDING`, typed abstention, and
`NO_ADMISSIBLE_NEW_RESULT` are valid outcomes.  A more extreme observed rank
is not a success criterion.

## 2. Protected paths and mutation policy

The following paths are read-only inputs for this work:

- `docs/generated/planck_pr3_paired300_irrep_carrier/`
- `docs/generated/planck_mes_irrep_analysis/`
- `docs/generated/planck_mes_smica_cmbonly_999_irrep/`
- `docs/generated/planck_mes_irrep_injection_power/`
- `docs/generated/planck_mes_first_paper/`
- `papers/planck_mes_first_observation/main.tex`
- every raw Planck, FFP10, WMAP, CosmoGlobe, CLASS, or QUIJOTE root

All WU-009 outputs use new paths.  Source edits use `apply_patch`; generated
text artifacts must be deterministically reproducible.  No binary or large
carrier artifact is added to the branch.

## Task 1 — typed theorem authority and executable contracts

### Files

- Create
  `docs/research_program/post_pr327/planck_mes_wu009_theorem_adjudication.json`.
- Create `scripts/observed_runs/planck_mes_wu009_contracts.py`.
- Create
  `tests/contracts/test_planck_mes_wu009_theorem_reconciliation.py`.

### Required behavior

1. Encode exactly 78 unique rows: A01-A14, B01-B22, C01-C18, D01-D08,
   E01-E16.
2. Require per-row verdict, assumptions/domain, withdrawn-or-narrowed claim,
   replacement statement, summary proof reference, executable-test IDs,
   affected claims/files, evidence status, and release status.
3. Bind the whole ledger to `USER_SUPPLIED_SUMMARY` and
   `FORMAL_DOSSIER_PENDING`; no row may claim a locally replayed P01-P27 proof.
4. Implement pure, typed checks for the bounded Gate-B contracts, including:
   STF cubic saturation, generic-stratum abstention, finite-rank
   superuniformity with ties, decreasing-transform tail swap, selection
   symmetry, conditional e-increment composition, boost response condition
   bound, positive-quadratic strict-positivity domain, and refusal of
   unweighted inverse-square fitting under untruncated Gaussian direct-T
   noise.
5. Include negative controls for mirror chirality loss, broken row
   equivariance, marginal-only e-value multiplication, bounded-body/cone
   confusion, and missing absolute temperature information.

### Red/green verification

Run the test module before its implementation exists and record the expected
import/contract failure.  Then run:

```bash
python -m unittest tests.contracts.test_planck_mes_wu009_theorem_reconciliation -v
python scripts/observed_runs/planck_mes_wu009_contracts.py \
  --ledger docs/research_program/post_pr327/planck_mes_wu009_theorem_adjudication.json \
  --self-check
python -m py_compile \
  scripts/observed_runs/planck_mes_wu009_contracts.py \
  tests/contracts/test_planck_mes_wu009_theorem_reconciliation.py
```

## Task 2 — committed-carrier reconciliation and durable local handoff

### Files

- Create
  `scripts/observed_runs/run_planck_mes_wu009_reconciliation.py`.
- Create `tests/integration/test_planck_mes_wu009_reconciliation.py`.
- Create `docs/generated/planck_mes_wu009_reconciliation/` containing only
  deterministic JSON/text manifests and receipts.
- Create
  `docs/codex_handoff/planck_mes_pmg_wu009_full_replay_local_execution/`.
- Create `scripts/validate_planck_mes_pmg_wu009_full_replay.py`.
- Create
  `tests/contracts/test_planck_mes_pmg_wu009_full_replay.py`.

### Required behavior

1. Consume only whitelisted committed JSON/CSV/text artifacts and verify their
   exact identities before reading scientific values.
2. Preserve WU-006 `27/301` family and `4/301` local ranks as historical,
   WU-007 `61/1000` and `55/1000` as null-pool sensitivity, and WU-008 as
   observation-blind method power.  Reconcile stale internal status fields
   without rewriting predecessors.
3. Emit one manifest-bound successor receipt with explicit tested, untested,
   blocked, and local-only lanes.  If retained carriers needed by Gate C are
   absent, emit `NOT_IDENTIFIED_FROM_COMMITTED_CARRIER` rather than imputing
   them.
4. Exercise synthetic/exhaustive row-equivariance, tail-swap, nuisance, and
   inverse-domain negative controls through the Task-1 pure contracts.  Do not
   calculate a new observed rank from unavailable carrier arrays.
5. Build a self-contained local package with authority binding, data inventory,
   sealed D.9 recipe template, lane-terminal registry, execution contract,
   read-first handoff, exact prompt, package index, and machine validator.
6. The validator must require explicit roots, forbid recursive raw-root scans
   and writes, bind the theorem-dossier locator and SHA-256, require the
   absolute-temperature/monopole/dipole gate, enforce I/Q/U spin-2 and
   cut-sky E/B operator/null requirements, and accept only the approved typed
   terminal states.  It must refuse product substitution and same-sky
   independence claims.

### Red/green verification

```bash
python -m unittest tests.integration.test_planck_mes_wu009_reconciliation -v
python -m unittest tests.contracts.test_planck_mes_pmg_wu009_full_replay -v
python scripts/observed_runs/run_planck_mes_wu009_reconciliation.py --check
python scripts/validate_planck_mes_pmg_wu009_full_replay.py --mode package
python -m py_compile \
  scripts/observed_runs/run_planck_mes_wu009_reconciliation.py \
  scripts/validate_planck_mes_pmg_wu009_full_replay.py
```

## Task 3 — Paper A claim firewall and delivery integration

### Files

- Modify `scripts/paper/build_planck_mes_first_paper.py` only at a bounded
  WU-009 claim-boundary interface.
- Create or extend a focused Paper-A contract test without changing frozen
  numerical expectations.
- Create
  `docs/research_program/post_pr327/planck_mes_wu009_implementation_status.json`.
- Update the WU-009 local handoff and package manifest after final verification.

### Required behavior

1. Add a fail-closed optional WU-009 receipt loader/validator.  Absence of a
   sealed successor leaves the existing paper analysis unchanged.
2. Expose corrected claim-boundary language from the typed ledger/receipt:
   superuniform finite rank, decreasing-tail swap, representation-only
   positive-quadratic inverse, formal-dossier pending, matched joint
   polarization-null prerequisite, same-sky robustness, and exploratory-only
   cross-field/joint/conditional diagnostics.
3. Reject or omit O(3)-only completeness, global full-frame, ordinary
   bispectrum completeness, orthogonal-nuisance nonidentifiability,
   unconditional Wasserstein, selection-independence necessity, unmatched
   E/B rank, causal Bianchi-family attribution, and shared-data marginal
   e-value multiplication.
4. Do not regenerate `main.tex` or the existing paper generated directory until
   a Gate-E successor is sealed.  The implementation status must explicitly
   name this local-only/blocked state.

### Red/green verification

```bash
python -m unittest tests.paper.test_planck_mes_wu009_claim_boundary -v
python -m py_compile scripts/paper/build_planck_mes_first_paper.py
```

The pre-existing pytest suite is additionally required on a host with pytest:

```bash
python -m pytest -q \
  tests/contracts/test_planck_mes_wu009_theorem_reconciliation.py \
  tests/integration/test_planck_mes_wu009_reconciliation.py \
  tests/contracts/test_planck_mes_pmg_wu009_full_replay.py \
  tests/paper/test_planck_mes_wu009_claim_boundary.py \
  tests/paper/test_planck_mes_first_paper.py
```

The current work host lacks `pytest`; the attempted isolated installation was
not authorized by the environment.  This is a declared host limitation, not a
passing test result.  Every new test must therefore also run through standard
library `unittest` here.

## 6. Final review and shipping gates

1. Run all standard-library test modules and deterministic validators from a
   clean worktree.
2. Verify protected predecessor hashes are unchanged and inspect the exact
   local diff for secrets, binaries, generated noise, stale paths, and claim
   promotion.
3. Obtain a fresh independent diff review with explicit P0/P1 findings and
   resolve every P0/P1 item.
4. Recheck that the remote design branch is still exactly
   `bda8e489bff7c26fb5fb03fba59360028d01a2fe` before publication.
5. Build GitHub blobs/tree/commit on remote tree
   `aa734e7933efc6f763d49aaf9f0d9c1bdad6b3b1`, update the existing design
   branch by non-forced fast-forward, and byte-compare every changed file.
6. Open a draft PR from the WU-009 branch to
   `changeset/planck-mes-wu008-injection-power-20260829`.  Do not merge and do
   not trigger a new canary.
7. Report exact commit/tree, tests executed, unrun pytest/local raw/CAS gates,
   expected local terminal states, and direct links to the PR, implementation
   status, and local handoff prompt.

## 7. Acceptance mapping

- Design criteria 1-2: Task 1 ledger, contracts, and negative controls.
- Criteria 3-4: Task 2 map-free receipt and typed stops.
- Criteria 5: Task 3 bounded builder claim interface.
- Criteria 6 and 9-15: Task 2 local handoff, D.9 recipe, lane registry, and
  validator.
- Criteria 7: per-task review plus final clean-context verification.
- Criterion 8: non-forced publication and draft PR only.
