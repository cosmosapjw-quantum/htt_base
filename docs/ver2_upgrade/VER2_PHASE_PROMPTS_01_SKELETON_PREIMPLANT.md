# VER2 Prompt List 01

## Skeleton / Pseudocode / Contract Pre-Implantation

**Status**: execution packet list  
**Authority**: `docs/ver2_upgrade/*`  
**Use case**: run these prompts before major implementation so that skeletons, dataclasses, tests, audit hooks, and documentation scaffolds exist with the correct ownership and no commit conflicts

## 0. Operating rule

Run `SK-00` alone first. After it lands, run the remaining packets in parallel only if their write scopes do not overlap.

## 1. Common prompt contract

Every packet below must include the following workflow.

### 1.1 Mandatory execution sequence

1. Read assigned ver2 authority docs twice (`RE2`).
2. Reconcile semantic doc paths to actual repo paths.
3. Scan the current local code in the assigned write scope.
4. Run three separate verification lanes and report them separately:
   - internal dev docs + internal literature,
   - web CRAG using primary sources,
   - silent CoT + integrated phys-math-code audit.
5. Generate at least three candidate skeleton layouts.
6. Choose one by divergence -> verification -> convergence.
7. Implant skeleton code and pseudocode only.
8. Add or update skeleton tests, audit hooks, and doc stubs.
9. Record findings in the phase ledger and audit note.
10. If issues remain, repair and re-audit up to five loops.
11. Commit with the assigned prefix.

### 1.2 Mandatory audit protocol

Perform the following silently and output only auditable results:

- `self-discover`
- `step-back`
- `metacognitive self-ask`
- `CoVe`
- `adversarial self-ask`
- `CCoT`
- `Parallel-Distill-Refine`

Use the integrated audit template below as a required output section in the audit note:

1. Audit target reconstruction
2. Contract/interface table
3. Phys-math audit ledger
4. Equation-to-code mapping audit
5. Numerical/pipeline audit
6. Ranked failure modes
7. Verifier results
8. Minimal repair plan
9. Minimal test set
10. Final verdict

### 1.3 Hard packet bans

- Do not widen the packet write scope.
- Do not implement final physics if the packet is skeleton-only.
- Do not introduce duplicate shared enums or manifests.
- Do not promote diagnostic-only paths to production.
- Do not merge MIO certificate semantics into HTT or BASS.
- Do not let TSC own runtime allow/block.
- Do not emit figures or manuscript tables from non-manifest artifacts.

### 1.4 Required docs updates

Every packet updates:

- `docs/ver2_upgrade/VER2_EXECUTION_LEDGER.md`
- `docs/ver2_upgrade/VER2_CARRY_FORWARD_LEDGER.md`
- `docs/ver2_upgrade/NEXT_SESSION_PROMPT_VER2.md`
- `docs/ver2_upgrade/audits/AUDIT_<packet_id>_<YYYY-MM-DD>.md`

## 2. Packet table

| Packet | Phase | Parallel after | Lane | Commit prefix |
|---|---|---|---|---|
| `SK-00` | `VER2-V0` | none | supervisor | `V2-C0:` |
| `SK-01C` | `VER2-V0/V4` | `SK-00` | `C` | `V2-C0:` |
| `SK-01S1` | `VER2-V1` | `SK-00` | `S1` | `V2-S1:` |
| `SK-02S2` | `VER2-V2` | `SK-01S1` | `S2` | `V2-S2:` |
| `SK-03S3` | `VER2-V3` | `SK-02S2` | `S3` | `V2-S3:` |
| `SK-04O` | `VER2-V4` | `SK-03S3`,`SK-01C` | `O` | `V2-O1:` |
| `SK-05T` | `VER2-V5` | `SK-00`,`SK-01C` | `T` | `V2-T1:` |
| `SK-06H` | `VER2-V6` | `SK-01C` | `H` | `V2-H1:` |
| `SK-07M` | `VER2-V7` | `SK-01C` | `M` | `V2-M1:` |
| `SK-08V` | `VER2-V8` | any two executable lanes | `V` | `V2-V1:` |
| `SK-09D` | `VER2-V9` | `SK-01C` | `D` | `V2-D1:` |

## 3. Packet prompts

### `SK-00` Supervisor Barrier Prompt

**Write scope**

- `docs/ver2_upgrade/*`
- `htt/src/common/*`
- selected `htt/workspace/contracts/*`

**Prompt**

```text
Use `docs/ver2_upgrade/*` as the only semantic SSOT.

Task: close VER2-V0. Do not implement science features. Freeze the authority stack, semantic-path reconciliation, shared schema owner, phase crosswalk, write-lock table, and packet execution ledger. Read the assigned authority docs twice before editing.

Authority docs:
- docs/ver2_upgrade/lowell_bianchi_solver_SDD_PR_WBS_pstf_tetrad.md
- docs/ver2_upgrade/BASS_PY_HTT_TSC_MIO_RESEARCH_PLAN_critical_upgraded.md
- docs/ver2_upgrade/BASS_HTT_MIO_TSC_observable_atlas_SDD_WBS_PR_plan.md
- docs/ver2_upgrade/TSC_active_service_SDD_WBS_PR_plan.md
- docs/ver2_upgrade/x_Q_Pi_F_G_model_independent_framework_upgrade.md

Actual repo mapping:
- src/common -> htt/src/common
- src/bass -> htt/bass
- src/tsc -> htt/tsc
- src/mio -> htt/mio
- src/htt -> htt/htt/htt
- workspace/contracts -> htt/workspace/contracts

Deliverables:
1. shared-schema freeze in the canonical common path,
2. machine-readable or at least explicit phase crosswalk,
3. execution ledger stub,
4. carry-forward ledger stub,
5. next-session prompt stub,
6. audit note for VER2-V0,
7. skeleton tests proving duplicate-schema and owner-violation paths are blocked.

Run three verification lanes separately:
- internal docs/internal literature,
- web CRAG on primary sources,
- silent CoT + integrated phys-math-code audit.

Use max 5 repair loops. After green static audit, commit with prefix `V2-C0:`.
```

### `SK-01C` Shared Contracts Skeleton Prompt

**Write scope**

- `htt/src/common/*`
- `htt/workspace/contracts/*`
- related tests only

**Internal anchors**

- ver2 atlas contracts `§3`
- TSC contracts `§4`
- x-doc `§9.1`
- research plan v4 `P0-A`, `P0-B`, `P0-C`

**Prompt**

```text
Close the shared contract skeleton layer only. Do not implement solver physics.

Build skeletons and tests for:
- Owner / ClaimTier / ImplementationScope / ProductionStatus,
- ArtifactManifest,
- SolverCoreOutput,
- ObservableVector,
- AtlasEntryLite,
- DepartureReport or equivalent xQPiFG wrapper,
- MioCertificate wrapper hook,
- TscAdequacyOverlay wrapper hook,
- status snapshot / claim ledger / sky support stubs.

Requirements:
- read authority docs twice,
- reconcile all duplicate schema definitions into one canonical owner path,
- keep wrappers thin and package-neutral,
- add tests blocking schema duplication and owner drift,
- update the execution ledger and audit note,
- commit as `V2-C0: ...`.

Verification lanes required:
- internal docs + local code,
- web CRAG for external field names or likelihood metadata if needed,
- silent integrated phys-math-code audit.
```

### `SK-01S1` Solver Algebra/Geometry/Background Skeleton Prompt

**Write scope**

- `htt/bass/background/*`
- `htt/bass/species/*`
- `htt/bass/tilt/*`
- local tests only

**Internal anchors**

- solver SDD `PR-01..06`, `§5`, `§11`, `§15`
- solver core `§2-§8`, `§15-§17`
- local `htt/docs/lowell_bianchi_solver_reference.md`

**Prompt**

```text
Implant skeletons and pseudocode for algebra, geometry, constraints, and background only.

Required skeleton surfaces:
- Bianchi algebra registry for all eleven types,
- structure constants / Jacobi checks,
- tetrad connection and curvature operators,
- constraint-evaluation stubs,
- orthogonal and tilted IC-builder interfaces,
- background RHS assembly interfaces,
- Weyl / Bianchi-identity diagnostic hooks.

Do not implement observer statistics, likelihoods, or final numerics.
Do not drop class-B terms.
Do not reintroduce ADM-primary state language.

Verification lanes:
- internal docs and local reference notes,
- web CRAG for Pontzen-Challinor, Wainwright-Ellis, Ma-Bertschinger,
- silent integrated phys-math-code audit.

Run up to 5 repair loops, update ledgers, then commit `V2-S1:`.
```

### `SK-02S2` Radiation/Collision/History Skeleton Prompt

**Write scope**

- `htt/bass/hierarchy/*`
- `htt/bass/transport/*`
- `htt/bass/collision/*`
- `htt/bass/recombination/*`
- `htt/bass/closure/*`
- local tests only

**Internal anchors**

- solver SDD `PR-07..12`
- solver core `§9-§14`
- research plan `P0-E`

**Prompt**

```text
Implant skeletons and pseudocode for photon transport, PSTF hierarchy, electron-frame Thomson source, visibility/reionization wiring, and IC compatibility.

Requirements:
- transport must remain n^a-frame,
- collision/source/visibility must remain electron-frame,
- low-ell truncation allowed,
- scalar recombination history first pass allowed,
- no FLRW-only collision shortcut,
- no hidden closure promotion.

Deliver skeletons, interface tests, and metadata propagation stubs only.
Do not claim production physics yet.

Run the three verification lanes and the integrated audit. Repair up to 5 loops. Commit `V2-S2:`.
```

### `SK-03S3` Executable Solver/Runtime/Output Skeleton Prompt

**Write scope**

- `htt/bass/los/*`
- `htt/bass/spectrum/*`
- `htt/bass/runtime/*`
- `htt/bass/integration/*`
- selected `htt/bass/forward/*`
- local tests only

**Internal anchors**

- solver SDD `PR-13..21`
- observables stats `§6-§7`
- atlas contracts `SolverCoreOutput`

**Prompt**

```text
Implant skeletons for Tier A / Tier B solver orchestration, propagator, runtime controls, neutral outputs, convergence/cutoff campaign hooks, and release metadata.

Requirements:
- `SolverCoreOutput` must remain observer-neutral,
- required metadata must always be attached,
- no observational interpretation inside BASS runtime,
- convergence hooks and cutoff campaign hooks must exist as first-class objects,
- exact/approximate/disabled flags must be explicit, never inferred.

This packet may create executor and campaign scaffolds but not final tuned numerics.
Run internal docs, web CRAG, and integrated audit separately. Commit `V2-S3:`.
```

### `SK-04O` Observable Atlas / Covariance Skeleton Prompt

**Write scope**

- `htt/bass/observational/*`
- selected `htt/bass/spectrum/off_diagonal_covariance.py`
- selected `htt/workspace/contracts/*`
- local tests only

**Internal anchors**

- observables stats doc
- MES extension doc
- OA `PR-OA-01..05`, `PR-MES-06`, `PR-REP-07`

**Prompt**

```text
Implant skeletons for ObservableVector extraction, AtlasEntryLite, sparse BiPoSH/covariance builder, FullCovMESReport, and xQPiFG report-card plumbing.

Hard rules:
- diagonal C_ell is not sufficient compression,
- rank failure returns no-claim, not weak evidence,
- report cards are descriptive unless claim gates are passed,
- all objects must carry manifests and sky-support metadata.

Do not implement final inference or manuscript exporters in this packet.
Run the three verification lanes and integrated audit. Commit `V2-O1:`.
```

### `SK-05T` TSC Active-Service Skeleton Prompt

**Write scope**

- `htt/tsc/*`
- related tests only

**Internal anchors**

- TSC doc `§3-§5`, `§7`, `§13-§16`
- research plan `P0-D`, `P0-E`

**Prompt**

```text
Implant skeletons for TscDomainReport, TscResidualReport, TscSourceBridgeReport, TscChannelAdequacyBudget, TscUpgradeRecommendation, TscAdequacyOverlay, and no-overclaim lint.

Requirements:
- TSC never owns final allow/block,
- TSC never emits full-polarization or Bianchi-family truth labels,
- source / propagation / observable split must remain explicit,
- every serious artifact eventually attaches either TSC overlay or explicit TSC-not-applicable.

Skeletons only; add domain and vocabulary tests. Separate the three verification lanes and run up to 5 repair loops. Commit `V2-T1:`.
```

### `SK-06H` HTT Directional Inference Skeleton Prompt

**Write scope**

- `htt/htt/htt/infer/*`
- `htt/htt/htt/integration/*`
- selected `htt/htt/htt/bridge/*`
- local tests only

**Internal anchors**

- research plan `Wave 3`, `PR-HTT-C2`
- OA `PR-HTT-08`, `PR-HTT-09`, `PR-HTT-11`
- x-doc `§5-§8`

**Prompt**

```text
Implant skeletons for directional likelihood inputs, local-boost/global-tilt discrimination, matched-complexity/null-competition hooks, and production axis gating.

Hard rules:
- HTT owns posterior/evidence,
- diagnostic axes cannot become production axes without gates,
- no MIO certificate merge,
- no TSC posterior correction.

Skeleton interfaces, gate tests, and audit docs only. Do not wait for live solver outputs; bind only to common contracts and carry solver-coupled wiring forward explicitly. Use the required three verification lanes and commit `V2-H1:`.
```

### `SK-07M` MIO Observatory Skeleton Prompt

**Write scope**

- `htt/mio/*`
- local tests only

**Internal anchors**

- x-doc `§4-§10`, `§12-§14`
- research plan `Wave 4`, `PR-MIO-C4/C5`
- OA `PR-MIO-10`

**Prompt**

```text
Implant skeletons for directional coherence, non-parametric shear extraction, FLRW tension, evidence anatomy, residual atlas, and MioCertificate production-status labeling.

Rules:
- every MIO output must declare whether it is diagnostic-only or production-grade,
- covariance/atlas/null-mock prerequisites must be explicit,
- MIO is not posterior, not evidence, not truth certificate.

Do not implement final algorithms yet. Build status/caveat plumbing, tests, and audits. Solver-coupled estimators may remain stubbed if they are recorded explicitly in the carry-forward ledger. Commit `V2-M1:`.
```

### `SK-08V` Validation / Hostile Audit Skeleton Prompt

**Write scope**

- selected `htt/workspace/contracts/*`
- `htt/scripts/*`
- validation docs only

**Internal anchors**

- OA `PR-VAL-13/14`
- TSC `PR-TSC-10`
- MES `§14-§16`

**Prompt**

```text
Implant skeletons for theorem-to-test map, validation campaign registry, null/injection campaign manifests, and hostile-audit runbooks.

Requirements:
- cross-link theorem claims to tests,
- record no-claim conditions explicitly,
- separate baseline reproduction, adversarial edge, physics sanity, numerical stability, and regression tests,
- keep campaign registry package-neutral.

Do not generate final science results in this packet. Commit `V2-V1:`.
```

### `SK-09D` Docs / Export / Manuscript Skeleton Prompt

**Write scope**

- `docs/ver2_upgrade/*`
- selected `docs/manuscript/*`
- selected `figures/*`
- selected exporters only

**Internal anchors**

- v4 manuscript corrections
- OA `PR-MAN-15`
- TSC `PR-TSC-13`

**Prompt**

```text
Implant skeletons for artifact-to-manuscript export, figure/table manifest checks, chapter insertion points, and ver2 audit/ledger documents.

Rules:
- no figure without manifest,
- no caption beyond claim tier,
- docs must pull status from the shared snapshot rather than manual counts,
- every phase gets a placeholder audit entry and carry-forward section.

Skeleton docs/exporters only. This packet is intentionally solver-independent at this stage. Commit `V2-D1:`.
```

## 4. Recommended parallel batches

### Batch A

- `SK-00`

### Batch B

- `SK-01C`

### Batch C

- `SK-05T`
- `SK-06H`
- `SK-07M`
- `SK-09D`

### Batch D

- `SK-01S1`

### Batch E

- `SK-02S2`

### Batch F

- `SK-03S3`

### Batch G

- `SK-04O`

### Batch H

- `SK-08V`

## 5. Exit condition for prompt list 01

Prompt list 01 is complete only when:

1. every lane has a skeleton owner and audit note,
2. shared contracts exist in one canonical place only,
3. write scopes are frozen,
4. theorem-to-test scaffolds exist,
5. the repository is ready for actual implementation without schema conflict.
