# Shared Context — long-horizon rescue execution

## Project objective

- Objective: execute `PR-119..PR-166` in topological order as a claim-tiered,
  manifest-backed pre-solver observatory without fabricating native-solver or
  Bianchi-family evidence.
- Current milestone / PR: PR-122 sealed; PR-123 intake is next, followed by
  checkpoint 070.
- Governing specification: `docs/research_program/long_horizon_rescue/pr122_spec.yaml`.
- Governing roadmap: `docs/research_program/LONG_HORIZON_RESCUE_PR_ROADMAP_20260714.md`.
- Base revision: `461fe4ca8f1ca1ebdcf3571ad077aac4b5e25b38`;
  comparison target: current worktree on `research/pr04-multicomponent`.

## Current changed surface

| Area | Files / symbols | Why relevant | Evidence artifact |
|---|---|---|---|
| Claim evidence | `common.evidence_graph`, `common.release_evidence_binding`, literal release pin | Typed closure, exact receipt consumption, fail-closed claim release | `docs/generated/pr122_claim_evidence_graph.json` |
| Test execution | `common.pytest_execution_evidence`, source-only launcher | Binds exact selector, execution, environment, source, and startup state | `docs/generated/pr122_test_execution.json` |
| MES authority | `common.mes_successor_registry`, active-consumer inventory | Inventories current consumers while preserving PR-124 blockers | `docs/generated/pr122_mes_successor_scan.json` |
| Audit consumers | publication freeze and external audit package | Audit disclosure only; current PDF gate remains blocked; policy pins are schema-checked once per build-local snapshot and hash-rechecked | `docs/generated/publication_claim_freeze.md` |
| Shared-agent harness | `AGENTS.md`, `.agent-harness/`, `.codex/hooks*`, repo-local orchestrator skill | Registers all future subagent assignments and versioned context | `.agent-harness/generated/CONTEXT_PACK.md` |

## Common assumptions and conventions

- Process result, evidence status, and scientific status are orthogonal axes.
- HTT owns model-dependent inference; MIO owns diagnostic-only certificates;
  OBSSTAT owns feature extraction; BASS owns transfer/atlas interfaces.
- Current external/AniCLASS transfer results are transfer-conditional and are
  never native-solver results.
- Python evidence production uses the repository venv through the tracked
  source-only launcher with `-I -S -B` and an empty external cache.
- The checked-in PR-122 author and adjudicator are correlated internal process
  identities and cannot promote scientific status.
- No mathematical or physical claim in PR-122 requires a CAS derivation.

## Frozen scope

- In scope: PR-122 C1 release mechanics, manifests, receipts, exact test
  evidence, authority snapshot, package/freeze consumption, and harness
  integration.
- Explicit non-goals: scientific estimand validation, native solver work,
  morphology compatibility, geometry evidence, or Bianchi-family inference.
- PR3/FFP10 E2E download is complete; its analysis remains deferred to PR-150.
- PR4/NPIPE is not downloaded. PR4 download, intake, reduction, and all data
  analysis are skipped entirely by user scope; no PR4 command may run.
- All 102 remediation findings remain `OPEN`; no PR-122 mechanism may mark a
  finding `RESCUED`.

## Shared evidence pointers

| Evidence ID | Path | Produced by | SHA-256 | Supports claims |
|---|---|---|---|---|
| E-PR122-SPEC | `docs/research_program/long_horizon_rescue/pr122_spec.yaml` | reviewed repository edit | `eab2fc002d85522a33f83a3039144fc66d3cb4b5cfafc16fb66efe653d671e87` | C-PR122-MECHANICS, C-PR4-SKIP |
| E-PR122-TEST | `docs/generated/pr122_test_execution.json` | source-only graph builder | `3c93fb772c3e7cc2a78c162ac6d83a49ebcdc223c26f752f857cb8bcd2318a5f` | C-PR122-MECHANICS |
| E-PR122-GRAPH | `docs/generated/pr122_claim_evidence_graph.json` | source-only graph builder | `aba2a4285105e85720dc560e08ccbc7f9f6a384f9ffc23e4aa6872d8674e45d6` | C-PR122-MECHANICS, C-PR122-NONPROMOTION |
| E-PR122-RECEIPT | `docs/generated/pr122_release_receipt.json` | source-only graph builder | `3c40f202e6e9c46853bea1e03ffffa9881cdffaa210ed480cb2c7be45ec65012` | C-PR122-NONPROMOTION |
| E-HARNESS-ZIP | `codex_shared_context_harness_v1.zip` | user-supplied installation packet | `1f020bf290476491b07869ed40eb4d05fb99b6f38efe420453a02faf243ff94f` | C-HARNESS-INSTALL |
| E-PR122-PERF | `.agent-harness/runs/pr122-closeout-20260716/results/A-PR122-PERF.json` | registered read-only performance audit | `6c4fedbaa86667af449e70c9a8eb58712b41030def2ba4fd70655083b771cc53` | C-HARNESS-INSTALL, C-PR122-MECHANICS |

## Known disputes and open questions

| Question ID | Question | Required discriminating evidence | Owner |
|---|---|---|---|
| Q-PR123-SCOPE | Which analytic-only oracle mutations belong to PR-123 without stealing later PR ownership? | registered PR-123 assignments and exact roadmap/spec clauses | next run |
