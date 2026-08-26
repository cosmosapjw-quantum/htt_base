# Planck MES Extended-Data Execution Plan

## A. Authority and Scope

Canonical base is `changeset/pr324-mes-methodology-stack-20260826@3cdeaba39e164c911a26c5daa37f0e15b29614d3` with tree `47bdbb72aae62ca4280a96897f80028b1b910c20`. This package is planning-only and changes no canonical DAG, status mirror, primary scientific output, or raw data. The latest user-reported host inventory is accepted as a planning input but must be independently replayed by `PED-WU-001`.

The immediate scope is deliberately narrow:

1. verify the local data inventory read-only;
2. execute the separate 999-CMB-only SMICA robustness lane;
3. execute a Commander observation-only same-operator comparison;
4. cleanly rebind provenance and add a bounded Paper A robustness supplement.

ACT, CF4, DESI, KiDS, JWST, SPT, BICEP/Keck, and theory archives are routed in `DATA_ROUTE_MATRIX.yaml`; they are not silently merged into Paper A.

## B. P0/P1 Threat Catalogue

The controlling catalogue is `P0_P1_THREAT_CATALOG.json`. It contains 8 P0 and 8 P1 failure classes. Every class has an executable detector or an explicit blocked gate. The load-bearing guards prevent raw-data mutation, malformed/partial data admission, FFP10 order drift, primary/null-model substitution, Commander pseudo-calibration, operator mismatch, claim inflation, unexecuted manuscript values, and process starvation.

## C. Invariant/Test Matrix

`INVARIANT_TEST_MATRIX.yaml` maps every failure mode to one invariant, one detector, one work unit, and one positive `PASS -> next executable action` transition. Coverage must be exact: no threat may disappear and no unmapped matrix row may appear.

## D. Ordered Work Units

1. `PED-WU-001` — content-bound local intake and quarantine.
2. `PED-WU-002` — real SMICA 999-CMB-only robustness execution.
3. `PED-WU-003` — real Commander observation-only descriptive comparison.
4. `PED-WU-004` — clean provenance rebind and bounded paper supplement.

These aliases are not canonical PR/DAG IDs. Each implementation unit gets its own branch/PR and objective output. The sequence cannot be replaced by another planning package.

## E. Fresh-Context Review Contract

`FRESH_CONTEXT_REVIEW_CONTRACT.yaml` requires a read-only first pass using only base/final identity, diff, compiled contract, test logs, terminals/replays, and blockers. Pass requires `P0=0`, `P1=0`. One targeted repair is allowed; another review cycle requires a newly reproduced current-task blocker.

## F. Final Differential Audit Contract

`FINAL_DIFFERENTIAL_AUDIT_CONTRACT.yaml` audits only the implementation delta and asks whether the compiled contract was violated or missed a new P0/P1. It must not reopen the entire MES program, primary rank analysis, deferred datasets, or the verification framework.

## G. Unresolved Specification Boundaries

No user decision blocks `PED-WU-001` or `PED-WU-002`.

Runtime-resolved boundaries are:

- whether FFP10 realization 00818 passes semantic FITS/checksum validation;
- whether Commander observation admission uses an exactly identical operator projection;
- the numerical robustness values themselves.

Commander finite-null calibration remains blocked by only three complete simulations. NPIPE/PR4 and HSC are unavailable in the reported roots. Alternate-mask semantics are not invented from the one common temperature mask.

## H. Process-Cost Assessment

The plan reuses existing Planck admission, joint cut-sky, MES, and paper test surfaces. It forbids a full 910-GiB preflight hash sweep, full-suite reassurance, new DAG nodes, duplicate provenance, and review-of-review. Selected Planck files are stream-hashed during their first scientific read; unrelated datasets are not rehashed. Passing each gate advances directly to the next executable action.
