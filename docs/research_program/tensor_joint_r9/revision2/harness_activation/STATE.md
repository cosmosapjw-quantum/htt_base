# R9 revision 2 — research harness continuation state

PROJECT: HTT R9
HARNESS_VERSION: 4.0.0
LAST_UPDATED: 2026-09-13
EXECUTION_STATUS: PUBLIC_CF3_CALIBRATION_CONNECTION_INDEPENDENTLY_REVIEWED
MODEL_IDENTITY: UNKNOWN
MODEL_IDENTITY_SOURCE: no trusted executing-model metadata asserted; explicit user choice selects the GPT-6 Astra harness only
MODEL_PERFORMANCE_STATUS: NOT_EVALUATED
OWNER: root / HTT common research
CURRENT_PHASE: public selection/calibration input acquisition and independent closeout
MODE: local-validation

## Current selection/calibration continuation

Start: `51ed1e913ac358f9a2569fce8ccb5dc3c1650305`. Read ../selected_law/README.md,
input_inventory.json and final/result.json. Public CF3/SDSS PGC296 and documented
TF-exclusion294 point calibration are connected to all 36 depth features; shared
input dependence and the initial block are preserved. Tempel objID 33641 joins
match group/richness exactly, with 418 unmatched rows retained. 35 relevant tests
pass; scoped independent review passes with no blocking defect. Full selected law, group 292 calibration,
full-mock upstream refits, physical response and common coverage remain unavailable.
The original 2048-mock/DESI/reference evidence and every HOLD/budget stay unchanged.
Current runtime authority is 0f4eb82; the 0b6022e1 receipt below is historical.
Managed Qwen status READY is not local task qualification or dispatch success.

## Historical real-product continuation

The accepted starting commit is `c532862651235ed0586a0677b61a43b2e09b3c85`.
The active product/method is [SDSS PV multi-depth](../multidepth/README.md).
The consumed configuration fixes four cumulative windows and a 36-component
log-distance feature vector. The code preserves shared-catalogue cross-depth
covariance, actual angular responses and the free shared eta zero point.
The relevant repaired test suite passes 25 tests. All 2,048 released mock catalogues passed the complete archive checksum and
feature replay; training/evaluation each use 128 boxes and 1,024 catalogues.
See ../multidepth/final/result.json and final_execution.json. The targeted
independent numerical closeout passes; see the R9-MULTIDEPTH-20260913
results/repair_closeout.json and ../multidepth/PR_DELTA.md.
The existing DESI scalar execution and original reference experiments are not
rerun. Missing raw selection/group/CF3 calibration and physical common coverage
remain unavailable, with zero new alpha consumption and all scientific HOLDs.

The global runtime policy was reapplied after the user hook fix, using merged
`0b6022e1eac1807f2363080690a6f07cf306e811`. Official installers/checks match the
installed policy and hook command; actual automatic dispatch is not verified.
This does not establish runtime model identity or change old task budgets.

## Historical first-adapter scope and completion

Current continuation from `9e9539edcdbd7bbf66e458cdce685c7a112f8a04` applies
both exact archives to the actual adapters and a retained DESI conditional
product path. See [implementation contract](../implementation/CONTRACT.md),
[validation](../implementation/final_execution.json) and
[product result](../implementation/desi_product_final.json). Archive SHA256 and all
vendor-member bytes were reverified. The 55 relevant tests pass. Original
reference invariants replay successfully; SVD-coordinate random fibre support
is not the same numeric target across environments, as retained in
`../implementation/reference_comparison.json`. Independent review and targeted repair closeout pass; see ../implementation/REVIEW.md.
The scientific HOLDs and R9-25 missing observed multi-depth law remain.

The following sections preserve the earlier **package-only integration** scope
at 9e9539ed. They do not describe the new implementation as unexecuted.

Apply both exact research and coding ZIPs supplied by the user to the already published R9 revision 2. Preserve the original aim of connecting full tensor morphology, local/global responses and conditional physical inference to qualified data products. The current action resolves both missing package inputs; it does not start a new theory program, migrate production code or execute new observations. The prior user authorization covers this same branch's documents and push.

Completion requires archive/member identity, actual reading of the entrypoints/core/selected policies, application to these current state and evidence distinctions, package checks with raw exits, a focused independent review, and publication/readback. The copied package state remains an unexecuted template. This file is the active state adapter; the scientific SSOT stays ../../RESEARCH_STATE.json, ../../REVISION_SPEC.md and ../THEORY_EXTENSION.md. No package template is used as prior research evidence.

## Evidence and decisions

| Item | Evidence status | Controlling evidence / scope |
|---|---|---|
| Research package identity and selection | implementation-verified | ACTIVATION.json; evidence/member_hashes.json; packaging and router logs |
| D1–D4/F1–F3 | derived; numerically checked in the predecessor session | ../THEORY_EXTENSION.md and ../evidence/research_checks.json at 247de8d232b401974d0deab2f9e9111974a0fbbb; not rerun here |
| Scoped design handoff | predecessor independent review | ../evidence/decision.json at that same commit; no new science promotion |
| GPT-6 model-performance advantage | unresolved | package manifest NOT_EVALUATED; no comparative execution |
| Coding package | implementation-verified at package/tool level; read and applied to scoped integration | ACTIVATION.json; CODING_CONTRACT.md; coding_evidence/; production adapter not implemented |
| Production, empirical, novelty, four-axis CAS | HOLD / unresolved or blocked as recorded | ../../RESEARCH_STATE.json; package checks grant none of these |

The existing experimental assumptions, seeds, tolerances, counterexamples, physical frames, units and error budgets are unchanged. Their definitions stay in the frozen revision specification and theory. The 30-node campaign DAG is unchanged; no graph capability follows from loading a ZIP.

## Recovery and boundaries

Workspace maintenance removed the old checkout. A fresh sparse clone restored the published 247de8d2 tree; this is source/evidence recovery, not recovery of an old live process. The old R9-REV2-20260912 whole-run aggregate remains NOT_A_WHOLE_CURRENT_RUN_PASS. Its assignments and results are historical at the pinned commit; changes to current handoff text do not retroactively repair their seals. The old package-unavailable fact remains in historical_harness_activation and the predecessor review. No four-axis CAS, mock science, observation or model benchmark is rerun in this intake.

The root has applied PROJECT_INSTRUCTIONS plus the integrated contract, phase gates and Phase 10: reused the completed derivations; reconciled evidence labels and state; separated current acquisition from prior execution; preserved failure classes and approvals; and updated the executable handoff. Independent review is limited to package application and history preservation; the followup covers new user-supplied evidence rather than repeating the scientific review. The research-only result is preserved at commit 543b76b2f36084c555ecd113ae3c608472912313 under .agent-harness/runs/R9-HARNESS-20260913/results/activation_review.json. The same reviewer handles a new registered followup for the newly supplied coding package and combined state at .agent-harness/runs/R9-HARNESS-BOTH-20260913/results/coding_followup.json; no authenticated hook/profile or independent-model claim is made.

## Next action and stop

Both harnesses are now locally available at harness/physmath-research-gpt6-astra and harness/physmath-coding-gpt6-astra with exact archives under harness/archives. Read its START_HERE.md, PROJECT_INSTRUCTIONS.md and this state, then ../../HANDOFF_PROMPT.md. Continue the real product observation-law work in the current handoff; the c532 scoped R9-03/05 and R9-24/25 implementation is already complete. Read CODING_CONTRACT.md and the coding START_HERE/AGENTS before the next coding phase; neither ZIP needs to be requested again. Stop this attachment-recovery task once the focused delivery checks and remote readback are complete; no new science claim is admitted.

The coding core was applied using its staging/merge policy and task/validation/closeout contract. Root AGENTS and old packages were preserved; no initializer reset project files. Packaged tool tests and protected-source comparisons are the current acceptance evidence. Scientific validation rows are not applicable to this package-only diff and remain required for the later numerical/production changes where relevant.
