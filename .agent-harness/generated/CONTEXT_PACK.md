# Canonical Shared Context Pack

Context version: `86126dd80915defb7dad67dfa416ed66acd4dcbca1edcd4801ccdd3b85aade9c`
Built at: `2026-07-16T14:55:04+00:00`

This pack contains only the shared Tier-0 context. Assignment-specific context and sibling results are intentionally excluded.

---

## Source: `.agent-harness/context/SHARED_CONTEXT.md`

SHA-256: `1aa03bc2dd5be288901b32921e16672cfcbe432d4e2d3a1e3b7d39b5207ca565`

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

---

## Source: `.agent-harness/context/SYMBOLS.md`

SHA-256: `5c51f848f93430c8b49d46bd66219162409f06b35fdf778ea9f44c0bf5d214cb`

# Symbol and Interface Table

| Symbol / interface | Definition | Domain / type | Units / dimensions | Sign / branch convention | Source of truth |
|---|---|---|---|---|---|
| `EvidenceAxes` | Orthogonal process, evidence, and scientific status tuple | typed enum triple | dimensionless | no axis may promote another | `htt/src/common/evidence_graph.py` |
| `EvidenceGraph` | Typed acyclic content-addressed claim/evidence graph | immutable graph record | dimensionless | SHA-256 canonical JSON identity | `htt/src/common/evidence_graph.py` |
| `TestExecution` | Exact collected/executed/outcome/environment receipt | typed pytest evidence record | counts and SHA-256 refs | skipped/xfail are not passes | `htt/src/common/evidence_graph.py` |
| `ReleaseEvidencePin` | Typed view of literal-only fixed-point fields | repository-relative paths and SHA-256 refs | dimensionless | parsed without importing pin module | `htt/src/common/release_evidence_binding.py` |
| `AuthorityRegistry` | Exact principal/role/scope verifier registry | immutable principal records | dimensionless | correlated internal identities cannot promote science | `htt/src/common/remediation_state.py` |
| `MatchedNullCompetitionReport` | Canonical HTT matched-null adequacy report | exact typed report | report-defined | caller scalar or duck type is non-authoritative | `htt/htt/htt/infer/null_competition.py` |
| PR4 scope firewall | User-directed ban on PR4 download/intake/reduction/analysis | execution policy | zero commands | complete skip, not inferred completion | `docs/research_program/long_horizon_rescue/pr122_spec.yaml` |

Record overloaded symbols explicitly. A CAS axis may introduce internal names,
but its result must map them back to this table.

---

## Source: `.agent-harness/context/FROZEN_DECISIONS.md`

SHA-256: `82be3a48c424f2f831705f66214b616ac875d6a209e648c6c4d75dd68ee0dd9c`

# Frozen Decisions and Rejected Alternatives

| Decision ID | Decision | Rationale/evidence | Scope | Reopen condition |
|---|---|---|---|---|
| D-PR4-SKIP | Skip PR4 download, intake, reduction, and all data analysis | Explicit user instruction; PR4 data is absent | Entire roadmap execution | New explicit user direction plus authenticated inputs |
| D-NATIVE-BOUNDARY | Do not implement or simulate the future native low-ell solver | Repository mission and claim firewall | Pre-solver roadmap | Independently authenticated external delivery |
| D-PIN-LITERAL | Keep PR-122 release-pin fields literal-only and parse without module execution | Breaks verifier/graph fixed-point cycle while exposing a reviewable trust root | PR-122 release consumption | A stronger acyclic trust-root design with equivalent exact tests |
| D-AUTH-SNAPSHOT | Consume an immutable PR-122 exact-scope authority snapshot | Later global principal registration must not invalidate historical receipts | PR-122 only | Explicit migration with preserved historical verification |
| D-SINGLE-WRITER | Main agent alone edits production code, specs, shared gates, and shared context | Shared-context harness write-ownership rule | All multi-agent runs | Never within a run; only ownership reassignment before work |
| D-CLAIM-OPEN | Keep all 102 remediation findings OPEN and claim release false | PR-122 supplies mechanics, not scientific authority | PR-122 | Downstream gate evidence under its owning PR |

Agents must not silently reopen a frozen decision. A proposed reversal is a
meta-finding with new evidence and an explicit reopen condition.

---

## Source: `.agent-harness/context/GATE_REGISTRY.json`

SHA-256: `403b10160b7c8057031de32cb5b2f8ac28295acde28703c33854dc0cba325cb2`

{
  "schema_version": 1,
  "gates": [
    {
      "gate_id": "G-PR122-TEST",
      "spec_refs": ["docs/research_program/long_horizon_rescue/pr122_spec.yaml#mutation_execution_matrix"],
      "statement": "Every registered PR-122 mutation maps to an exact executed passing node in the source-only receipt.",
      "required_evidence": ["E-PR122-TEST"],
      "pass_condition": "132 collected, 132 executed, 132 passed, and 56/56 exact mutation mappings.",
      "fail_condition": "Any missing, non-executed, non-passing, or semantically mismapped node.",
      "owner": "main",
      "status": "pass"
    },
    {
      "gate_id": "G-PR122-FIXED-POINT",
      "spec_refs": ["docs/research_program/long_horizon_rescue/pr122_spec.yaml#release_policy"],
      "statement": "Graph, receipts, closure, manifest, verifier, and literal pin form one exact fixed point.",
      "required_evidence": ["E-PR122-GRAPH", "E-PR122-RECEIPT"],
      "pass_condition": "Source-only graph --check and audit-disclosure consumption pass while claim release is false.",
      "fail_condition": "Any stale hash/ref or claim_release_allowed=true.",
      "owner": "main",
      "status": "pass"
    },
    {
      "gate_id": "G-HARNESS-INSTALL",
      "spec_refs": ["AGENTS.md#mandatory-shared-context-protocol-for-subagent-workflows"],
      "statement": "The shared-context harness is installed, versioned, and valid before new subagent work.",
      "required_evidence": ["E-HARNESS-ZIP"],
      "pass_condition": "Context pack builds; validate_harness reports ok; all future assignments are registered with four-field headers.",
      "fail_condition": "Stale context, unregistered assignment, invalid result envelope, or budget violation.",
      "owner": "main",
      "status": "pass"
    },
    {
      "gate_id": "G-PR4-SKIP",
      "spec_refs": ["docs/research_program/long_horizon_rescue/pr122_spec.yaml#data_scope"],
      "statement": "PR4 download, intake, reduction, and analysis remain entirely skipped.",
      "required_evidence": ["E-PR122-SPEC", "E-PR122-GRAPH"],
      "pass_condition": "PR4 commands_run=0 and no PR4-derived artifact or claim.",
      "fail_condition": "Any PR4 data command, derived value, or inferred joint PR3+PR4 result.",
      "owner": "main",
      "status": "pass"
    },
    {
      "gate_id": "G-PR122-FINAL-CONSUMERS",
      "spec_refs": ["docs/research_program/long_horizon_rescue/pr122_spec.yaml#acceptance"],
      "statement": "Harness integration leaves quarantine, freeze, package, and consumer tests current.",
      "required_evidence": ["E-PR122-GRAPH"],
      "pass_condition": "Harness validation, CF4 quarantine, freeze, package, smoke, collection, and PR-122 integration checks pass with only the documented PDF blocker.",
      "fail_condition": "Any unexpected failure, stale artifact, claim drift, or PR4 execution.",
      "owner": "main",
      "status": "pass"
    }
  ]
}
