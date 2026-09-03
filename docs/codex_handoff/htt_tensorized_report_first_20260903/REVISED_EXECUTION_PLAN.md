# HTT theory-report-first execution plan — repository-wide audit revision

## Purpose

Produce an HTT-only theory/methods report from the actual repository authority surfaces before resuming observation-independent successor work. All local carrier processing, Planck/FFP10 execution, observed-rank evaluation, and statistic evaluation remain closed under `DATA_DEFERRED_BY_OWNER`.

This revision replaces the previous plan that made local map-free carrier repair the immediate next node. It also rejects a second premature assumption: the report claim surface is not yet frozen because PR #405/408 survivor rows have not been mechanically triaged and several execution grades were conflated.

## Fixed exclusions

The current programme excludes:

- scalar-only MES ranks as current science;
- old WU-006–008 Q/O, foreground, tensor-rank, and injection conclusions;
- all observation-bearing execution;
- empirical `beta` fitting or boost subtraction;
- local boost = global matter-frame tilt identification;
- physical shear/vorticity or Bianchi-family attribution;
- native BASS solver, background, recombination/reionization, and family-forward results;
- finite-HEALPix all-direction containment before numerical-error closure.

## Repository topology

There is no single “latest” source branch for Report A.

```text
merged/default framework
  research/pr04-multicomponent@50ea6d76...

vector/tensor foundation
  PR #367@6bafca66...

candidate/survivor audits
  PR #405@463f0999...
  PR #408@40dce3ab...

tensorized Q/O correction
  PR #440@68723412...

theorem wording inventory
  PR #441@04680e99...

observer-response lineage
  PR #442@29427a1f...
  PR #444@de73549c...
  PR #446@033e0d19...
  PR #447@bf6cc2dd...

report control plane
  PR #449
```

The report integrates these through an authority/evidence ledger. It must not fabricate linear Git ancestry.

## Work completed by the repository-wide audit

### A0 — repository-surface inventory

**State:** `DONE_REPORT_SCOPE`

Created:

```text
docs/research_reports/HTT_REPO_WIDE_THEORY_SURFACE_AUDIT_20260903.md
docs/codex_handoff/htt_tensorized_report_first_20260903/REPO_SURFACE_INVENTORY.yaml
```

Coverage:

- default branch and report-authority PR manifests;
- common tensor/statistics modules;
- PR #440 Q/O code and tests;
- WU-010 and WU-011 response modules, tests, artifacts, and audits;
- PR #367/405/408/441 proof and claim surfaces;
- workflow and job-step metadata.

BASS and observational paths were classified out of report scope rather than semantically imported.

### A1 — authority precedence and supersession

**State:** `DONE_PROVISIONAL`

Updated:

```text
AUTHORITY_LEDGER.yaml
CONTRADICTION_LEDGER.yaml
```

The ledger now distinguishes:

- framework architecture;
- candidate theorem inventory;
- direct derivation;
- source implementation;
- exact-head implementation verification;
- prestart/no-execution workflows;
- historical input-only artifacts;
- withdrawn and out-of-scope results.

### A3 — representation-family firewall

**State:** `DONE_CONTRACT`

The following representations are separate:

```text
STF2(Q) + STF3(O):       ambient 12, generic SO(3) quotient 9
STF2 + four vectors:     ambient 17, generic SO(3) quotient 14
```

The PR #367/408 fourteen-coordinate VT-T8 local Jacobian cannot prove the PR #440 Q/O Krylov chart.

### A4 — execution-receipt index

**State:** `DONE_INITIAL`

Created:

```text
EXECUTION_RECEIPT_INDEX.yaml
```

The index distinguishes `EXECUTED_SUCCESS`, `EXECUTED_FAILURE`, `MIXED_EXECUTED_EVIDENCE`, `PRESTART_NO_EXECUTION`, `SOURCE_ONLY`, `ARTIFACT_ONLY`, `LOCAL_NON_BYTE_EXACT`, and `SUMMARY_ONLY`.

## Current next node

# A2 — Registered survivor-surface triage

**Goal:** mechanically determine which observation-independent claims may enter Report A.

**Inputs:**

- PR #367 source/evidence rows and 28 VT obligations;
- PR #405 complete 157-candidate matrix;
- PR #408 eligible broad/scoped rows and P0 audit;
- PR #441 78-row theorem wording inventory;
- WU-010 and WU-011 claims added after those audits;
- current explicit scalar-retirement and data-deferral policy.

**Output:**

```text
docs/codex_handoff/htt_tensorized_report_first_20260903/
  PROVISIONAL_CLAIM_SURVIVOR_LEDGER.yaml
```

The current file is an initial report-centred ledger. A2 is complete only after every eligible PR #405/408 source row has one of:

```text
INCLUDE_CORE
INCLUDE_LIMITED
FRAMEWORK_ONLY
DEFER_PROOF
UNRESOLVED
EXCLUDE_WITHDRAWN
EXCLUDE_SCOPE
```

### A2 procedure

1. Read all PR #405 matrix rows and extract every broad `PASS`/scoped child, exact negative obstruction, and preregistered synthetic positive cell.
2. Read PR #408 WU-001 eligibility rules without inheriting its provisional eight-survivor selection.
3. Normalize duplicate IDs and parent/child relations.
4. Map each row to its actual mathematical representation:
   - Q/O temperature pair;
   - joint vector/tensor observatory;
   - local-observer response;
   - processed-response/numerical uncertainty;
   - unrelated/out-of-scope.
5. Assign evidence status independently of the old role label.
6. Record exact source path/head and allowed wording.
7. Record novelty status as `ASSESSED`, `UNASSESSED`, or `NOT_APPLICABLE`; novelty never determines theorem truth.
8. Fail if any eligible row is missing or double-counted.

### A2 acceptance

```text
candidate-universe coverage: complete
eligible-row coverage: complete
unknown dispositions: zero
duplicate claim families without linkage: zero
claims admitted solely from PR441 summary labels: zero
PR367_VT_T8 to PR440_QO substitution: zero
observational claims: zero
```

### A2 stop conditions

Stop with a typed blocker if:

- a row’s exact source is missing;
- two sources make incompatible statements and no supersession exists;
- an alleged Q/O theorem belongs to the fourteen-dimensional vector/tensor representation;
- an execution status cannot be distinguished from source presence;
- a claim depends on observational output while the data gate is closed.

## A5 — contradiction and notation closure

**Depends on:** A2, A3, A4.

Required outputs:

```text
final CONTRADICTION_LEDGER.yaml
NOTATION_AND_CONVENTION_REGISTRY.yaml
REPORT_SECTION_CLAIM_MAP.yaml
```

Minimum convention registry:

- metric and Levi-Civita conventions where applicable;
- outward sky direction and active/passive boost convention;
- harmonic phase and stored-real layout;
- STF normalization and Euclidean/Frobenius metrics;
- O(3) versus SO(3), parity, chirality, and stabilizer vocabulary;
- local observer velocity versus global matter-frame tilt;
- exact, finite-sample, asymptotic, conditional, numerical, and implementation evidence labels.

## Theory packs after A5

### T1 — stored-real/STF representation

Derive the harmonic/STF isometry, inverse map, norm identities, rotation and parity adapters. The map-free data runner is not executed.

### T2 — Q/O orbit chart and strata

Prove or narrow the PR #440 Krylov16 reconstruction on the declared cyclic conditioned chart. Produce an explicit mirror/non-separation counterexample and classify singular strata. Do not borrow VT-T8.

### T3 — MES conditional geometry

Re-derive the PSTF epsilon normalization and one-way shear/vorticity ceiling functions. Create a premise table and prove the scalar-to-tensor equivariance no-go.

### T4 — finite-null theory

State exact finite-rank validity under joint exchangeability and row equivariance; handle ties, monotone tails, data-dependent symmetric selection, typed missingness, null mismatch, and shared-data dependence. Read and cite primary sources directly before freeze.

### T5 — WU-010 synthesis

Import the scoped closed result, reproduce its derivations, and condense its exact-head evidence. Do not reopen or dilute its domain conditions.

### T6 — WU-011 processed-response quotient

State the operator factorization, quotient-rank identity, nested nuisance images, Task-7A/7B negative results, matched-control unresolved terminal, and finite-HEALPix boundary.

### T7 — continuum proof strengthening

Review the exact z-axis pivot-minor artifact and the all-direction multi-engine numerical lineages. Seek a portable interval/ball seal, but permit the report terminal `Z exact + five-direction high-precision numerical` if the wording remains graded.

### T8 — numerical-error theory

Prove the Loewner envelope, scaling and orthogonal-mixing invariances, zero-family guard, generalized singular-value condition, and completeness premise. Keep partial-rank Wedin analysis in a separate lane.

## Report assembly

### T9 — integrated claim ledger

Merge T1–T8 only after all claims have unique authority and evidence fields. Run contradiction, notation, citation, and scope scans.

### R1 — Theory and Methods Report A

Write the manuscript around one scientific argument:

> Tensorization preserves low-multipole morphology discarded by scalar summaries, while processed-response overlap and numerical uncertainty limit physical attribution.

No observational result table is created. The current corrected Planck rank is explicitly `NONE`.

### R2 — four-axis audit

1. PHYS–MATH;
2. STATISTICS;
3. PHYS–MATH–CODE;
4. PROVENANCE/PUBLICATION.

### R3 — blind referee audit and bounded revision

Audit title, abstract, theorem wording, tables, captions, continuum/discrete separation, and absence of silently restored data claims.

### R4 — report freeze

Bind source, PDF, figures, claim ledger, verifier receipts, and unresolved items. Merge/publication remains a separate owner decision.

## Observation-independent post-report successors

After R4, run in parallel where independent:

- `P1`: WU-011 finite-operator numerical-error closeout;
- `P2`: ideal inverse, intrinsic-octupole nuisance, and noisy-estimation theory;
- `P3`: depth, local/global, and remote-field identifiability theory.

Then perform `P4` publication split decision.

## Closed observational gate

```yaml
D0: DATA_DEFERRED_BY_OWNER
O1_corrected_carrier_repair: BLOCKED
O2_observation_blind_statistic_registry: BLOCKED
O3_corrected_Planck_FFP10_run: BLOCKED
O4_observation_report: BLOCKED
```

No theory task may silently open D0.

## Current completion estimate

| Workstream | Readiness after audit |
|---|---:|
| repository-surface inventory | 100% for Report A scope |
| authority/supersession reconstruction | 95% |
| execution-receipt classification | 95% initial |
| representation-family firewall | 100% |
| registered survivor triage | 35–45% |
| contradiction/notation closure | 45–55% |
| stored-real/STF theory | 85–90% |
| Q/O orbit-chart proof | 65–75% |
| conditional MES theory | 80–90% |
| finite-null theory | 70–80% |
| WU-010 synthesis | 95% |
| WU-011 quotient/no-go synthesis | 85–90% |
| continuum evidence | 90–95% numerical; z exact |
| all-direction interval proof | 25–40% |
| numerical-error theorem | 85–90% mathematics; runtime/provenance lower |
| integrated claim ledger | 45–55% |
| Report A working prose | 55–65% |
| Report A audited release candidate | 0% |
| observation result | 0%, intentionally deferred |

## Current terminal

```text
REPO_WIDE_REPORT_SURFACE_AUDIT_COMPLETE
/
AUTHORITY_FEDERATION_RECONSTRUCTED
/
REPRESENTATION_FAMILY_FIREWALL_CLOSED
/
EXECUTION_RECEIPTS_RECLASSIFIED
/
REGISTERED_SURVIVOR_TRIAGE_ACTIVE
/
OBSERVATIONAL_DATA_DEFERRED
/
NO_MERGE_OR_CLAIM_PROMOTION
```
