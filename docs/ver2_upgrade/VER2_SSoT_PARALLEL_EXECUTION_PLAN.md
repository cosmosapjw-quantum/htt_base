# VER2 Beyond-FLRW Upgrade Master Plan

**Status**: planning authority for the ver2 upgrade kickoff  
**Date**: 2026-04-20  
**Primary SSOT**: `docs/ver2_upgrade/*`  
**Secondary use only**: `docs/lowell_bianchi/*` and `docs/lowell_bianchi/extended_coverage/*` as formatting, audit-automation, and document-shape references only

## 0. One-line target

Turn the current `htt/bass`-centered low-`ell` beyond-FLRW stack into a direction-inclusive, artifact-first, claim-tiered research pipeline that can evolve in parallel without schema drift, commit collisions, or silent scope inflation.

## 1. Authority stack

`docs/ver2_upgrade` is the only semantic SSOT for this upgrade. If documents disagree, resolve in this order:

1. `docs/ver2_upgrade/lowell_bianchi_solver_SDD_PR_WBS_pstf_tetrad.md`
   Solver-core physics, package layout, PR/WBS order, validation gates, hard non-negotiables.
2. `docs/ver2_upgrade/lowell_bianchi_solver_core_selfcontained.md`
   Full physics/math reference for tetrad algebra, PSTF operators, background, tilt, transport, and exact electron-frame source logic.
3. `docs/ver2_upgrade/BASS_PY_HTT_TSC_MIO_RESEARCH_PLAN_v4_critical_upgraded.md`
   Program-level critical path, P0 correction packs, package roles, manuscript gating.
4. `docs/ver2_upgrade/BASS_HTT_MIO_TSC_observable_atlas_SDD_WBS_PR_plan.md`
   Shared contracts, manifests, atlas/covariance/report-card layer, manuscript exporter.
5. `docs/ver2_upgrade/TSC_active_service_SDD_WBS_PR_plan.md`
   TSC authority boundary, active-service contracts, no-overclaim overlay rules.
6. `docs/ver2_upgrade/x_Q_Pi_F_G_model_independent_framework_upgrade.md`
   Reporting semantics, MIO/HTT split, local/global discrimination semantics, `x,Q,Pi,F,G`.
7. `docs/ver2_upgrade/lowell_cmb_observables_statistics.md`
   Observer-side statistics contract only; never solver-core physics authority.
8. `docs/ver2_upgrade/mes_full_covariance_extension_self_contained.md`
   Covariance/MES theorem targets and no-claim conditions.

Secondary references may inform formatting, automation, and test/audit discipline, but may not override the above.

## 2. RE2 scan findings that must be frozen before coding

### 2.1 Load-bearing contradictions

1. Shared schema duplication already exists across the ver2 docs.
   Repeated surfaces: `Owner`, `ClaimTier`, `ImplementationScope`, `ArtifactManifest`, `SolverCoreOutput`, `MioCertificate`, `TscAdequacyOverlay`, theorem-to-test maps.
2. Phase language is inconsistent across documents.
   Solver core uses `PR-00..21`, research plan uses `Wave 0..5` and `Phase A..I`, atlas uses `PR-OA-*`, TSC uses `PR-TSC-*`.
3. Current-vs-target solver is deliberately mixed in the docs.
   `bass_py` remains the current executable research stack, while the solver SDD describes the exact beyond-FLRW target architecture.
4. TSC, HTT, and MIO boundaries are strict.
   TSC never owns runtime allow/block, HTT owns posterior/evidence, MIO owns diagnostics/certificates, BASS owns runtime/reduction and forward solver labels.
5. Artifact-first is mandatory.
   No manifest means no figure, no table, no manuscript promotion.

### 2.2 Consequence

Before any broad parallel implementation begins, a universal synchronization barrier is required:

\[
\boxed{\text{VER2-V0 schema + authority freeze}}
\]

No prompt may patch shared contracts, manuscript exports, or claim-tier logic before that barrier closes.

## 3. Semantic path freeze

The ver2 docs use semantic `src/...` paths. In this repository the actual writable mapping is:

| Semantic path in docs | Actual repo path |
|---|---|
| `src/common/*` | `htt/src/common/*` |
| `src/bass/*` | `htt/bass/*` |
| `src/tsc/*` | `htt/tsc/*` |
| `src/mio/*` | `htt/mio/*` |
| `src/htt/*` | `htt/htt/htt/*` |
| `workspace/contracts/*` | `htt/workspace/contracts/*` |
| figures / paper exports | `figures/*` |

### 3.1 Canonical shared-schema owner

Freeze this rule at VER2-V0:

- `htt/src/common/*` owns base enums, manifest primitives, claim tiers, ownership, sky-support primitives, and status snapshots.
- `htt/workspace/contracts/*` owns cross-package wrappers and transport objects that depend on multiple packages.
- No duplicate enum or manifest definitions may be introduced in `htt/bass`, `htt/tsc`, `htt/mio`, or `htt/htt/htt`.

## 4. Core principles

1. `docs/ver2_upgrade/*` is the only semantic SSOT.
2. `bass_py` is the current executable substrate; the exact solver target is still a target, not an already-earned claim.
3. Exact transport, explicit polarization, explicit frame metadata, and source/propagation split are non-negotiable.
4. TSC may diagnose or quarantine; it may not silently promote or demote solver/inference truth.
5. MIO may diagnose or certificate; it may not merge into HTT posterior/evidence.
6. Figures are downstream artifacts, never upstream design drivers.
7. A prompt may only touch files inside its assigned write scope.
8. Shared-contract files may only be touched by barrier prompts or explicitly reopened supervisor prompts.
9. Approximation claims must be explicit.
10. If literature/code/tests conflict, lower the claim tier first and escalate only after the conflict is resolved.
11. When a lane has a solver-independent shell and a solver-coupled binding stage, implement the shell first and carry the binding stage explicitly in the ledger.

## 5. Parallel-development topology

### 5.1 Decision

After comparing the doc structure, the safer topology is:

1. One supervisor prompt for `VER2-V0`.
2. After `VER2-V0`, multiple top-level prompts in parallel, each with a disjoint write set.
3. Inside each prompt, subagents are allowed only for read-only literature/code/audit reconnaissance, not for concurrent edits on overlapping files.

This is preferred over one huge prompt with many subagents because the risk here is not lack of ideation; it is schema drift and merge conflict on shared semantic surfaces.

### 5.2 Lane split

| Lane | Owns | Primary write scope |
|---|---|---|
| `C` | shared contracts and manifests | `htt/src/common/*`, selected `htt/workspace/contracts/*` |
| `S1` | algebra, geometry, constraints, background | `htt/bass/background/*`, `htt/bass/species/*`, `htt/bass/tilt/*` |
| `S2` | radiation hierarchy, collision, recombination/history | `htt/bass/hierarchy/*`, `htt/bass/transport/*`, `htt/bass/collision/*`, `htt/bass/recombination/*`, `htt/bass/closure/*` |
| `S3` | low-`ell` runtime, propagator, outputs, convergence | `htt/bass/los/*`, `htt/bass/spectrum/*`, `htt/bass/runtime/*`, `htt/bass/integration/*`, selected `htt/bass/forward/*` |
| `O` | observable atlas, covariance, MES, report cards | `htt/bass/observational/*`, selected `htt/bass/spectrum/off_diagonal_covariance.py`, selected `htt/workspace/contracts/*` |
| `T` | TSC active service | `htt/tsc/*` |
| `H` | HTT directional/model-dependent inference | `htt/htt/htt/infer/*`, `htt/htt/htt/integration/*`, selected `htt/htt/htt/bridge/*` |
| `M` | MIO model-independent observatory | `htt/mio/*` |
| `V` | theorem-to-test registry, hostile audit harness, campaign registry | selected `htt/workspace/contracts/*`, `htt/scripts/*`, top-level validation docs |
| `D` | manuscript/export/gallery/docs | `docs/ver2_upgrade/*`, `docs/manuscript/*`, `scripts/make_paper_figures.py`, `figures/*` |

### 5.3 Hotspot locks

These files or surfaces are merge hotspots and require explicit lock ownership:

- `htt/src/common/contracts.py`
- `htt/src/common/sky_geometry.py`
- `htt/src/common/mock_calibration.py`
- `htt/workspace/contracts/*`
- shared manifest exporters
- theorem-to-test registry
- top-level figure/manuscript exporters

## 6. VER2 phase crosswalk

| VER2 phase | Goal | Doc-native crosswalk | Opens parallel lanes | Promotion gate |
|---|---|---|---|---|
| `VER2-V0` | authority freeze, path reconciliation, schema barrier | v4 `Wave 0`, `P0-A..E`, `PR-C0`; solver `PR-00`; OA `PR-OA-00`; TSC `PR-TSC-00` | none | shared schema single-source, ownership firewall, manifest schema frozen |
| `VER2-V1` | algebra, geometry, constraints, background | solver `PR-01..06`; core `§2-§8` | `S1` | all-11-type algebra, Jacobi/constraint tests, no ADM relapse |
| `VER2-V2` | photon transport, PSTF radiation, Thomson, visibility, IC compatibility | solver `PR-07..12`; core `§9-§14` | `S2` | electron-frame collision exactness, frame metadata, no FLRW-only shortcut |
| `VER2-V3` | executable low-`ell` solver, propagator, runtime, outputs | solver `PR-13/14/15/16/17/18/19/20/21`; v4 `Wave 1-2` | `S3` | neutral `SolverCoreOutput`, convergence/cutoff campaigns, release-candidate runtime |
| `VER2-V4` | atlas/covariance/observables substrate | OA `PR-OA-01..05`, `PR-MES-06`, `PR-REP-07`; observables doc; MES doc | `O` | `ObservableVector`, `AtlasEntryLite`, BiPoSH/covariance no-claim logic |
| `VER2-V5` | TSC active service and overlay | TSC `PR-TSC-01..06`, `PR-TSC-11`, `PR-TSC-12`, `PR-TSC-10`, `PR-TSC-13` | `T` | no-overclaim overlay, domain/admissibility guard, source/propagation split preserved |
| `VER2-V6` | HTT directional inference and discrimination | v4 `Wave 3`, `PR-HTT-C2`; OA `PR-HTT-08`, `PR-HTT-09`, `PR-HTT-11` | `H` | directional likelihood owns model-dependent claims, no MIO/TSC truth leakage |
| `VER2-V7` | MIO observatory and `x,Q,Pi,F,G` layer | v4 `Wave 4`, `PR-MIO-C4/C5`; OA `PR-MIO-10`; x-doc `§9-§12` | `M` | certificate stays non-posterior, covariance/atlas/null-mock prerequisites enforced |
| `VER2-V8` | validation campaigns and hostile audit | solver `PR-18/19`; OA `PR-VAL-13/14`; TSC `PR-TSC-10` | `V` | theorem-to-test map, injections, null ensembles, campaign registry green |
| `VER2-V9` | figure/export/manuscript/release | OA `PR-MAN-15`; TSC `PR-TSC-13`; x-doc `§11`; v4 `Wave 5` | `D` | manifest-backed figures/tables, claim-tiered manuscript text, release pack |

## 7. Phase-specific anchors

### 7.1 VER2-V0

- Internal dev-doc anchors:
  - `BASS_PY_HTT_TSC_MIO_RESEARCH_PLAN_v4_critical_upgraded.md`
  - `BASS_HTT_MIO_TSC_observable_atlas_SDD_WBS_PR_plan.md`
  - `TSC_active_service_SDD_WBS_PR_plan.md`
  - `x_Q_Pi_F_G_model_independent_framework_upgrade.md`
- Internal literature:
  - `docs/PR_CONSTITUTION.md`
  - `htt/src/common/contracts.py`
  - `htt/workspace/contracts/*`
- External web targets:
  - Planck 2018 likelihoods `arXiv:1907.12875`
  - Planck 2018 cosmological parameters `arXiv:1807.06209`
- Allowed approximations:
  - none at schema level
- Forbidden claims:
  - any scientific promotion without manifest/claim tier

### 7.2 VER2-V1 to VER2-V3

- Internal dev-doc anchors:
  - `lowell_bianchi_solver_SDD_PR_WBS_pstf_tetrad.md`
  - `lowell_bianchi_solver_core_selfcontained.md`
- Internal literature:
  - `htt/docs/lowell_bianchi_solver_reference.md`
  - `htt/docs/ellis-relativistic-cosmology.pdf`
- External web targets:
  - Pontzen & Challinor 2007, MNRAS 380, 1387, DOI `10.1111/j.1365-2966.2007.12221.x`
  - Ma & Bertschinger 1995, ApJ 455, 7, DOI `10.1086/176550`
  - Wainwright & Ellis, *Dynamical Systems in Cosmology* for Bianchi background classification
- Allowed approximations:
  - low-`ell` truncation, explicit tier split, isotropic scalar recombination first pass
- Forbidden claims:
  - FLRW-only collision shortcut
  - implicit suppression of class-B terms
  - observational interpretation in solver output

### 7.3 VER2-V4

- Internal dev-doc anchors:
  - `lowell_cmb_observables_statistics.md`
  - `mes_full_covariance_extension_self_contained.md`
  - `BASS_HTT_MIO_TSC_observable_atlas_SDD_WBS_PR_plan.md`
- Internal literature:
  - existing `htt/workspace/contracts/*`
  - current `htt/bass/spectrum/off_diagonal_covariance.py`
- External web targets:
  - BiPoSH representation papers by Hajian/Souradeep and later formal summaries
  - isotropy-violation / covariance papers using BiPoSH
- Allowed approximations:
  - sparse covariance truncation, low-`ell` feature subsets
- Forbidden claims:
  - diagonal `C_ell` treated as sufficient compression for anisotropic families

### 7.4 VER2-V5

- Internal dev-doc anchors:
  - `TSC_active_service_SDD_WBS_PR_plan.md`
  - `BASS_PY_HTT_TSC_MIO_RESEARCH_PLAN_v4_critical_upgraded.md`
- Internal literature:
  - current `htt/tsc/*`
  - current `htt/bass/runtime/*`
- External web targets:
  - admissibility / realizability references as needed for chart-domain checks
- Allowed approximations:
  - metadata-level no-overclaim lint before full active-service depth
- Forbidden claims:
  - TSC validated full polarization
  - TSC validated Bianchi family

### 7.5 VER2-V6 to VER2-V7

- Internal dev-doc anchors:
  - `x_Q_Pi_F_G_model_independent_framework_upgrade.md`
  - `BASS_PY_HTT_TSC_MIO_RESEARCH_PLAN_v4_critical_upgraded.md`
  - `BASS_HTT_MIO_TSC_observable_atlas_SDD_WBS_PR_plan.md`
- Internal literature:
  - `htt/htt/htt/infer/*`
  - `htt/mio/*`
- External web targets:
  - Planck low-`ell` likelihood and directional-anomaly references
  - local-boost / statistical-isotropy-violation / BipoSH discrimination references
- Allowed approximations:
  - diagnostic-only promotion if covariance or null mocks are missing
- Forbidden claims:
  - MIO certificate merged with HTT posterior/evidence
  - geometry/family detection from scalar summary alone

### 7.6 VER2-V8 to VER2-V9

- Internal dev-doc anchors:
  - `BASS_HTT_MIO_TSC_observable_atlas_SDD_WBS_PR_plan.md`
  - `TSC_active_service_SDD_WBS_PR_plan.md`
  - v4 manuscript correction sections
- Internal literature:
  - `docs/lowell_bianchi/extended_coverage/SELF_AUDIT_AUTOMATION.md` for shape only
- External web targets:
  - any paper cited in the figures/manuscript pack must be verified during the phase
- Allowed approximations:
  - none for manifest/export discipline
- Forbidden claims:
  - figure-first or caption-first science

## 8. Hallucination and local-minima guards

Every packet and phase must use this protocol:

1. `RE2`
   Read the assigned authority docs twice before editing.
2. `Self-discover`
   Reconstruct contracts and write-scope from the docs and local code.
3. `Step-back`
   Separate current-state constraints from target-state claims.
4. `Metacognitive self-ask`
   List hidden assumptions, placeholders, surrogate paths, and silent approximations.
5. `CoVe`
   Generate verification questions from contracts and answer them using code/docs/web sources.
6. `Adversarial self-ask`
   Attempt to prove the current plan wrong via ownership, scope, claim-tier, or frame/normalization violations.
7. `CCoT`
   Silently compare at least three repair candidates and choose one; output only the selected rationale, not raw chain-of-thought.
8. `Parallel-Distill-Refine`
   Use subagents only for read-only tri-audit or literature extraction; distill conflicts before editing.
9. `Max 5 repair loops`
   If the packet still fails after five repair loops, stop, document blockers, and do not widen the write scope.

Additional hard guards:

- Search explicitly for `toy`, `naive`, `surrogate`, `placeholder`, `mock`, `diagnostic-only`, `temporary`, `Route B`, `pretend`, `approximate`, `FLRW-only`.
- Reject the first “docs-only” or “tests-only” repair if the problem is actually semantic or physics-bearing.
- If web search and local docs disagree, prefer lower claim tier and record the discrepancy.

## 9. Validation checklist

Every phase must close all five checklist rows before promotion:

1. `Contract`
   Inputs, outputs, units, sign conventions, metadata, and owner are explicit.
2. `Physics/math`
   Known limits, normalization, frame split, positivity/admissibility, and special-case behavior are checked.
3. `Code mapping`
   Equation-to-code and doc-to-code mapping is explicit; no dead placeholder is silently on the production path.
4. `Numerics/pipeline`
   Convergence or stability expectations, deterministic behavior, cache/state leakage, and promotion gates are explicit.
5. `Claim hygiene`
   Artifact manifest, claim tier, caveats, and forbidden claims are attached.

## 10. Commit namespace and merge discipline

Use unique phase/lane commit prefixes:

- `V2-C0:` shared contract/schema barrier
- `V2-S1:` solver algebra/geometry/background
- `V2-S2:` radiation/collision/history
- `V2-S3:` runtime/propagator/output
- `V2-O1:` atlas/covariance/report cards
- `V2-T1:` TSC active service
- `V2-H1:` HTT directional inference
- `V2-M1:` MIO observatory
- `V2-V1:` validation campaigns / audit registry
- `V2-D1:` figures/manuscript/export

Rules:

1. One logical object per commit.
2. No cross-lane edits in the same commit.
3. No amend unless explicitly requested.
4. If shared schemas must reopen, do it in a supervisor packet with a new `V2-C0:` commit.

## 11. Required per-packet documentation updates

Every prompt that lands a change must also update:

- `docs/ver2_upgrade/VER2_EXECUTION_LEDGER.md`
- `docs/ver2_upgrade/VER2_CARRY_FORWARD_LEDGER.md`
- `docs/ver2_upgrade/NEXT_SESSION_PROMPT_VER2.md`
- one audit note under `docs/ver2_upgrade/audits/`

If a packet does not update the ledger, it is not considered complete.

## 12. Immediate execution order

1. Close `VER2-V0` first.
2. Start `C` immediately after the shared schema barrier closes.
3. Front-load solver-independent shells in `T`, `H`, `M`, and `D` after `C`.
4. Start `S1` after the barrier closes, but treat it as lower urgency than `C/T/H/M/D` if the goal is to maximize non-solver progress first.
5. Start `S2` only after `S1` publishes stable geometry/background contracts.
6. Start `S3` only after `S2` publishes stable neutral solver outputs.
7. Start solver-coupled binding work in `O`, `H`, and `M` only after `S3` and `C` publish stable `SolverCoreOutput` and manifest semantics.
8. Start `V` once at least one lane in `S3/O/T/H/M` is executable.
9. Final figure generation remains last, except for docs/export scaffolding and ledger maintenance.

## 13. Final recommendation

Treat the ver2 upgrade as a synchronized multi-lane program with one hard schema barrier and many bounded write scopes. Do not optimize for maximum prompt count. Optimize for:

1. semantic consistency,
2. disjoint write scopes,
3. artifact-first promotion,
4. explicit claim-tiering,
5. beyond-FLRW physics authority staying in the solver-core docs rather than leaking into observer/statistics layers.
