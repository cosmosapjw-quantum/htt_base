# Shared Context — long-horizon rescue execution

## Project objective

- Objective: execute `PR-119..PR-183` in topological order as a claim-tiered,
  manifest-backed pre-solver observatory without fabricating native-solver or
  Bianchi-family evidence.
- Current milestone / PR: PR-123 completed at attempt 6 after attempts 1-5 were
  invalidated as false-greens; checkpoint 070 is sealed and execution is paused.
- Governing specification: `docs/research_program/long_horizon_rescue/pr123_spec.yaml`.
- Governing roadmap: `docs/research_program/LONG_HORIZON_RESCUE_PR_ROADMAP_20260714.md`.
- Base revision: `e77510170424eecd49112ed6c33424ce455b154c`;
  comparison target: current worktree on `research/pr04-multicomponent`.

## Current changed surface

| Area | Files / symbols | Why relevant | Evidence artifact |
|---|---|---|---|
| Claim evidence | `common.evidence_graph`, `common.release_evidence_binding`, literal release pin | Typed closure, exact receipt consumption, fail-closed claim release | `docs/generated/pr122_claim_evidence_graph.json` |
| Test execution | `common.pytest_execution_evidence`, source-only launcher | Binds exact selector, execution, environment, source, and startup state | `docs/generated/pr122_test_execution.json` |
| MES authority | `common.mes_successor_registry`, active-consumer inventory | Inventories current consumers while preserving PR-124 blockers | `docs/generated/pr122_mes_successor_scan.json` |
| Audit consumers | publication freeze and external audit package | Audit disclosure only; current PDF gate remains blocked; policy pins are schema-checked once per build-local snapshot and hash-rechecked | `docs/generated/publication_claim_freeze.md` |
| Shared-agent harness | `AGENTS.md`, `.agent-harness/`, `.codex/hooks*`, repo-local orchestrator skill | Registers all future subagent assignments and versioned context | `.agent-harness/generated/CONTEXT_PACK.md` |
| PR-123 oracle lab | `common` oracle contracts, mutation lab, K6 catalog-independent continuum branch | Attempts 1-5 are retained as invalid; attempt 6 passed bounded C2 mechanics review with scientific status OPEN | `docs/generated/pr123_attempt_history.json` |

## Common assumptions and conventions

- Process result, evidence status, and scientific status are orthogonal axes.
- HTT owns model-dependent inference; MIO owns diagnostic-only certificates;
  OBSSTAT owns feature extraction; BASS owns transfer/atlas interfaces.
- Current external/AniCLASS transfer results are transfer-conditional and are
  never native-solver results.
- Python evidence production uses the repository venv through the tracked
  source-only launcher with `-I -S -B` and an empty external cache.
- Internal author/reviewer identities are correlated process evidence and
  cannot independently promote scientific status.
- PR-123 references must be smaller than production, use distinct algorithm
  lineage, and record shared equations, fixtures, authors, and random streams.

## Frozen scope

- In scope: analytic and manufactured references, registered known mutations,
  multi-seed properties/coverage, K6 continuum-order and upper-bound mechanics,
  oracle lineage, surviving-mutation reports, and no-empirical-consumer gates.
- Explicit non-goals: production defect remediation owned by later cards,
  observed-data inference, matched catalog/null/covariance promotion, native
  solver work, morphology compatibility, or geometry/family conclusions.
- PR3/FFP10 E2E download is complete; its analysis remains deferred to PR-150.
- PR4/NPIPE is not downloaded. PR4 download, intake, reduction, and all data
  analysis are skipped entirely by user scope; no PR4 command may run.
- All 102 remediation findings remain `OPEN`; a mechanics mutation kill does
  not mark a finding `RESCUED`.
- The integrated roadmap contains 130 actual cards through PR-183. The current
  machine-readable DAG contains 113 cards through PR-166; PR-167 is the frozen
  intake card that later registers PR-167..183, so progress reports must show
  integrated-roadmap and registered-DAG denominators separately.

## Shared evidence pointers

| Evidence ID | Path | Produced by | SHA-256 | Supports claims |
|---|---|---|---|---|
| E-PR122-SPEC | `docs/research_program/long_horizon_rescue/pr122_spec.yaml` | reviewed repository edit | `eab2fc002d85522a33f83a3039144fc66d3cb4b5cfafc16fb66efe653d671e87` | C-PR122-MECHANICS, C-PR4-SKIP |
| E-PR122-TEST | `docs/generated/pr122_test_execution.json` | source-only graph builder | `3c93fb772c3e7cc2a78c162ac6d83a49ebcdc223c26f752f857cb8bcd2318a5f` | C-PR122-MECHANICS |
| E-PR122-GRAPH | `docs/generated/pr122_claim_evidence_graph.json` | source-only graph builder | `aba2a4285105e85720dc560e08ccbc7f9f6a384f9ffc23e4aa6872d8674e45d6` | C-PR122-MECHANICS, C-PR122-NONPROMOTION |
| E-PR122-RECEIPT | `docs/generated/pr122_release_receipt.json` | source-only graph builder | `3c40f202e6e9c46853bea1e03ffffa9881cdffaa210ed480cb2c7be45ec65012` | C-PR122-NONPROMOTION |
| E-HARNESS-ZIP | `codex_shared_context_harness_v1.zip` | user-supplied installation packet | `1f020bf290476491b07869ed40eb4d05fb99b6f38efe420453a02faf243ff94f` | C-HARNESS-INSTALL |
| E-PR122-PERF | `.agent-harness/runs/pr122-closeout-20260716/results/A-PR122-PERF.json` | registered read-only performance audit | `6c4fedbaa86667af449e70c9a8eb58712b41030def2ba4fd70655083b771cc53` | C-HARNESS-INSTALL, C-PR122-MECHANICS |
| E-PR123-CARD | `docs/codex_handoff/pr_backlog.yaml` | PR-119 DAG intake | `dec20a60c32a15c1e65bbaff859e52cf51d89299e33dacc1fa60efbcbf16eb50` | C-PR123-MECHANICS, C-PR4-SKIP |
| E-PR123-SPEC | `docs/research_program/long_horizon_rescue/pr123_spec.yaml` | four-role intake, five invalidating hostile reviews, and main-thread v6 adjudication | `6356835da8099c4714a847864b849f8885a2bccda5e536f0f4c8dc508e282184` | C-PR123-MECHANICS, C-PR4-SKIP |
| E-PR123-LINEAGE | `docs/generated/pr123_oracle_lineage_manifest.json` | source-only PR-123 builder | `dffb8851397cd713ff8240fd832feb3c28771b0a71bf9ffaa7b5d2c331a95ee6` | C-PR123-MECHANICS |
| E-PR123-MUTATIONS | `docs/generated/pr123_mutation_lab_report.json` | source-only PR-123 builder | `9f9a69382427082d424bd260543d006b0fbf72e18be7e9c19e30946e98f51e14` | C-PR123-MECHANICS, C-PR4-SKIP |
| E-PR123-K6 | `docs/generated/pr123_k6_continuum_card.json` | source-only PR-123 builder | `4d1e15919259e67ba856a8b2e0966147f3c293a2756c080b795c1a65d72c7b54` | C-PR123-MECHANICS |
| E-PR123-ATTEMPTS | `docs/generated/pr123_attempt_history.json` | source-only PR-123 builder | `e19dd322c2d3435ecbed9193ef22880fe8acc733e033ab6cff74ce1c0f90aac2` | C-PR123-MECHANICS |
| E-PR123-MANIFEST | `docs/generated/pr123_artifact_manifest.json` | source-only PR-123 builder | `a1e2ce4eecb22ec43b947ec0b95f88d9e3d271be78cdd7bd06454636c7705869` | C-PR123-MECHANICS, C-PR4-SKIP |
| E-PR123-REVIEW2 | `.agent-harness/runs/pr123-final-hostile-review-20260716/MERGED_RESULTS.json` | registered blind hostile replay | `12c7316f435251810956d2f4b6c641977364abc96f5366737a057a732ddca076` | C-PR123-MECHANICS |
| E-PR123-REVIEW3 | `.agent-harness/runs/pr123-attempt3-final-review-20260716/MERGED_RESULTS.json` | registered blind hostile replay | `b30f9039af6b2cec157f8e4881957ef3294c1631db0fb70cd702aae35c2615ff` | C-PR123-MECHANICS |
| E-PR123-REVIEW4 | `.agent-harness/runs/pr123-attempt4-closeout-review-20260717/MERGED_RESULTS.json` | registered blind hostile replay | `976605182c888f278dc6d6f02275e1cdb0bfac744433ddcfb5cb598ea07732f1` | C-PR123-MECHANICS |
| E-PR123-REVIEW5 | `.agent-harness/runs/pr123-attempt5-closeout-review-20260717/MERGED_RESULTS.json` | registered blind hostile replay | `6c6f5f1499400a410ad46cfc00a5900fb09d435b6df5814faffb4be0d84327f2` | C-PR123-MECHANICS |
| E-PR123-REVIEW6 | `.agent-harness/runs/pr123-attempt6-final-scanner-review-20260717/MERGED_RESULTS.json` | registered bounded hostile replay | `0999233e21828a9cbffa99eda2ea061a3f140f91c5cf0b163b976ec1d61ade99` | C-PR123-MECHANICS |

## Known disputes and open questions

| Question ID | Question | Required discriminating evidence | Owner |
|---|---|---|---|
No unresolved PR-123 P1 dispute remains inside the finite registered contract.
The static scanner remains a bounded fail-closed check plus disclosed manual
adjudication, not a proof of arbitrary Python-program independence.
