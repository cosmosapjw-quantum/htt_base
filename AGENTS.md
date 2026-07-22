# AGENTS.md — `htt_base` Codex operating contract

## Mission

Upgrade `htt_base` before the external native low-ell Bianchi solver arrives. The active goal is not to fake a solver or force Bianchi family identification. The goal is to turn the current repository into a claim-tiered, manifest-backed, transfer-provenance-aware, MIO/HTT-separated observatory and inference framework that can later consume native solver outputs cleanly.

Work in the DAG defined by `docs/codex_handoff/pr_backlog.yaml` or `machine_readable/pr_backlog.yaml`. Never skip dependency gates to chase figures or headline results.

## Non-negotiable scientific boundaries

1. Do not implement or simulate the future external low-ell Bianchi Boltzmann solver in this repo. Only build adapter schemas, transfer registries, `AtlasEntryLite`, `ObservableVector`, validation harnesses, and pre-solver diagnostics.
2. Current transfer-dependent results are transfer-conditional. External or AniCLASS-calibrated transfer outputs must never be labeled native BASS/native solver results.
3. HTT owns model-dependent likelihoods, posterior bundles, evidence, local/global mixture inference, null competition, PPC, LOOCV, and posterior pushforward.
4. MIO owns model-family-independent diagnostics, `MioCertificate`, directional/depth coherence, and `(x,Q,Pi,F,G)` reports. MIO must not create posterior odds, truth certificates, or evidence terms.
5. TSC/Teff is legacy for new work. Keep old imports reproducible, but move useful guard behavior into `common.semantic_guards`. Do not let TSC own new scientific artifacts.
6. `obsstat` owns observable feature extraction only: alms, templates, covariance/BiPoSH features, low-ell scalar statistics, morphology axes, and null feature distributions. It must not own inference or certificates.
7. Scalar `x`, `Q`, `Pi`, `F`, `G`, direction coherence, or low-ell feature vectors do not identify a Bianchi family. Family-identification claims are blocked until a native low-ell morphology atlas exists and passes external null/mask/covariance/family-equivalence gates.

## Required per-PR loop

For every PR in the DAG:

1. **Start with evidence-gathering.** Read the PR card, dependencies, touched files, relevant tests, and prior PR deltas. Perform web search or documentation verification when the PR depends on external APIs, package behavior, or current tool semantics. If web is unavailable, record that explicitly in the PR delta and use repository-local evidence only.
2. **Diverge in proportion to risk.** Use only the distinct roles needed to expose a real failure class. The four-role mapper/harness/physics/claim set is reserved for R3 work, claim promotion, or an explicitly scoped harness audit; routine substantive PRs may use the main implementer plus one independent reviewer. Do not spawn differently named agents to repeat the same evidence.
3. **Prune and choose.** Use metacognitive self-ask, step-back, and adversarial review to select a patch that moves the project materially forward. Avoid tiny gate-only patches unless the PR is explicitly a gate/harness PR.
4. **Implement meaningful increments.** Do not get trapped in local minima. Prefer coherent code+tests+docs units over cosmetic edits. Large physics/statistics migrations are allowed when split into staged, testable PRs.
5. **Test.** Run the PR card’s tests and the smallest relevant smoke suite. Record commands, pass/fail, skipped optional dependencies, and failures.
6. **Self-review.** Use `/review` or spawn reviewer subagents for correctness, regression, tests, claim hygiene, and maintainability. Patch real findings before commit.
7. **Commit.** Commit only after tests and self-review. Commit message format: `<PR-ID>: <imperative summary>`.
8. **Update status.** Mark the PR in `docs/codex_handoff/pr_status.yaml` or `machine_readable/pr_status.yaml`, update PR_DELTA, and update progress every five completed PRs.
9. **Close subagents.** After each PR and after each five-PR checkpoint, explicitly close/stop completed subagent threads to avoid thread-limit accumulation.

## Five-PR checkpoint rule

After every five completed PRs:

- run `python scripts/codex_harness/progress_report.py docs/codex_handoff/pr_backlog.yaml docs/codex_handoff/pr_status.yaml --checkpoint-every 5`,
- compute percent completion by completed PR count and by dependency-weighted critical path,
- list blockers and stalled branches,
- if progress has not increased or the same blocker recurs, perform adversarial self-ask + step-back + CRAG/web verification and revise the remaining DAG using a small dedicated PR.

## Claim language

Use these safe phrases:

- `claim-tiered observational/statistical framework`
- `transfer-conditional result`
- `diagnostic-only certificate`
- `local/global discrimination candidate`
- `morphology compatibility`, not `family identification`
- `external-transfer path`, not `native solver result`

Forbidden in production outputs before native solver validation:

- `Bianchi geometry detected`
- `Bianchi family identified`
- `model-independent truth certificate`
- `MIO posterior`
- `TSC full solver`
- `Teff full polarisation closure`
- `external transfer validated as native`

## Minimum artifact metadata

Metadata is proportional to what an artifact is used to claim.

- Exploratory figures, internal reports, literature notes, and evolving diagnostics need an owner, scope, resolvable source/release/version identities, relevant assumptions, caveats, and enough method/configuration detail for scientific interpretation. They must be labelled non-claim-bearing when they are not acceptance evidence.
- Claim-bearing frozen numerical artifacts additionally need the applicable claim tier, transfer source, exact local config/input identities when available, sky/mask status when directional, covariance/null status when statistical, generating procedure, and git commit or worktree state.
- A separate manifest is required only when a downstream consumer, frozen release, or publication build reads it. Do not manufacture one for a disposable exploratory artifact.

No manuscript number without generated source. Null, prior, PPC, or LOOCV evidence is required only when the statistical claim actually depends on it.

## Repository role map

- `common/contracts`: SSoT, manifest, claim tier, transfer spec, sky support, semantic guards.
- `obsstat`: observable features, harmonic conventions, templates, BiPoSH, morphology, null ensembles.
- `bass_py` pre-solver: transfer provenance, external adapter, future native adapter schema, atlas metadata.
- `htt`: model-dependent inference, local/global mixture, null competition, PPC, LOOCV, posterior pushforward.
- `mio`: `(x,Q,Pi,F,G)` diagnostics, certificates, direction/depth coherence, FLRW tension diagnostics.
- `tsc_legacy`: reproducibility only; no new active science ownership.
- `manuscript/docs`: generated-status consumers only.

## Preferred commands

Use harness commands when available:

```bash
python scripts/codex_harness/validate_pr_dag.py docs/codex_handoff/pr_backlog.yaml
python scripts/codex_harness/progress_report.py docs/codex_handoff/pr_backlog.yaml docs/codex_handoff/pr_status.yaml
python scripts/codex_harness/run_subset.py --list
python -m pytest -m smoke -q
python -m pytest --collect-only -q
```

Do not hide failing tests. If a failure is unrelated, record it with evidence and scope, then keep the PR focused.


---

# Augmented research-harness skills policy (v3)

## Repo skill policy

Codex must treat `.agents/skills` as the canonical repository-local skill inventory. Prefer repo-scoped skills over user/global skills when the task touches this project, because these skills encode HTT/MIO/BASS/obsstat-specific claim boundaries.

Skill activation rules:

- Use `$htt-dag-orchestrator` before starting or reordering PRs.
- Use `$htt-harness-engineering` before changing packaging, pytest, optional dependency handling, status snapshots, or install scripts.
- Use `$htt-physics-math-audit` before editing equations, GR/cosmology conventions, MES bounds, transfer functions, or local/global tilt arguments.
- Use `$htt-scientific-code-validation` after any code change that can affect numerical output, generated artifacts, tests, or scientific claims.
- Use `$htt-claim-firewall` and `$htt-claim-provenance-ledger` before updating reports, manuscripts, figure captions, result packs, or claim ledgers.
- Use `$htt-xqpi-fg-formalism` for any change involving `x`, `Q`, `Pi`, `F`, `G_F`, budgets, denominators, filling fractions, or exceedance curves.
- Use `$htt-local-global-discrimination` for local boost/global tilt/systematics separation, depth tomography, response-rank audits, and null mocks.
- Use `$htt-observable-statistics` when touching `a_lm`, templates, anisotropic covariance, BiPoSH, low-ell morphology, or observer-side statistics.
- Use `$htt-transfer-provenance` when using, replacing, or describing AniCLASS/external/native transfer functions.
- Use `$htt-latex-paper-build` before claiming manuscript buildability or figure/bibliography completeness.
- Use `$htt-manuscript-figure-audit` before public report, manuscript freeze, figure table generation, or external audit bundles.
- Use `$htt-ssot-handoff-maintainer` after every five PRs, after any architectural decision, and before handing work to another agent/session.
- Use `$htt-reviewer-mode-pre-submission` for release gates, external audit packages, manuscript readiness, or severe self-review.
- Use `$htt-adversarial-review-loop` before merging each PR: run third-party style review, address concrete findings, and record remaining risks.
- Use `$htt-physmath-audit` for evidence-locked multi-axis hostile audits,
  advocate divergence, audit evidence packaging, and referee debates. Compose
  it with `$htt-physics-math-audit`, `$htt-statistical-hardening`,
  `$htt-scientific-code-validation`, `$htt-claim-firewall`,
  `$htt-claim-provenance-ledger`, `$htt-transfer-provenance`, and manuscript
  audit/build skills when those domain actions occur; the narrower
  `$htt-physics-math-audit` alone does not route a complete multi-axis audit.

## Mandatory non-overclaim rules

- Current repo work before the external low-ell solver may build contracts, adapters, feature extractors, synthetic tests, null calibration, and result-card machinery. It must not claim native Bianchi family identification.
- MIO certificates are diagnostic reports, not posteriors or truth certificates.
- HTT owns model-dependent inference. MIO owns family-independent diagnostics. BASS/native solver owns transfer/atlas outputs when available. `common` owns semantic firewalls and manifests.
- Teff/TSC materials are legacy/scope-audit material only unless a PR explicitly edits legacy reproduction tests. Do not introduce Teff as an active science owner in the new local/global framework.
- Claim-bearing frozen numerical artifacts need `owner`, `scope`, `claim_tier`, `transfer_source`, applicable config/input identities, `sky_support_status`, `null_mock_status`, and caveats. Exploratory figures, internal reports, literature notes, and evolving research inputs may instead use resolvable source/release/version identities; exact byte hashes are optional unless byte-identical replay is material.

## Research progress and exactness boundary

- Distinguish **source identity** (what paper, release, code version, or dataset product was used), **scientific reproducibility** (whether the result or conclusion recurs within declared tolerances or distributional criteria), and **exact replay** (whether identical bytes and environment reproduce identical output). They are not interchangeable evidence grades.
- SHA-256 is a hard requirement only for internal assignment/context drift seals, CAS contracts, content-addressed evidence, explicitly frozen inputs, and local artifacts whose exact bytes matter. DOI/arXiv identifiers, dataset/product releases, code versions or commits, access dates, methods, assumptions, seeds, and tolerances are valid research provenance when exact upstream bytes are unavailable or scientifically irrelevant.
- A hash-complete run does not pass validity or novelty, and a scientifically reproducible result is not rejected merely because an upstream archive cannot be reconstructed byte-for-byte. Record the limitation and lower exact-replay provenance instead.
- `RUN-*` identifiers are bounded process questions. They do not enter the permanent scientific claim registry and cannot promote novelty, readiness, or release state.
- Do not add a mandatory field, ledger row, gate, receipt, or permanent Markdown/JSON artifact without a consuming decision and a reproduced failure it prevents. Gate count, hash completeness, PR count, and document volume are not research-progress metrics.
- After two consecutive assurance-only PRs, stop governance expansion. The next PR must deliver a named downstream scientific capability, data execution/integration, experiment, or interpretable result. Another harness/correctness repair counts only when a reproduced high-severity defect directly blocks that named task.

## Progress discipline

Every five completed PRs, run the DAG/progress harness and record:

1. completed PR count and percent;
2. test collection status;
3. failed/skipped validation with reasons;
4. claim-tier drift findings;
5. next DAG slice or replanned DAG edges.

If progress percentage does not advance after five PRs, perform step-back/adversarial self-ask and replan the DAG instead of making cosmetic claim gates.

## Mandatory shared-context protocol for subagent workflows

This repository uses spec-driven development and evidence-bearing subagent audits. `AGENTS.md` contains durable policy only. Volatile project state, PR state, evidence, assignments, and results live under `.agent-harness/`.

### 1. Canonical context and compulsory bootstrap

- Before spawning any subagent, the main agent MUST ensure that `.agent-harness/context/CONTEXT_INDEX.json` and `.agent-harness/generated/CONTEXT_PACK.md` are current by running:
  `python3 .agent-harness/scripts/build_context_pack.py`
- Every spawned subagent MUST receive a spawn header containing all four fields:
  `RUN_ID`, `ASSIGNMENT_ID`, `CONTEXT_VERSION`, and `INDEPENDENCE_MODE`.
- Every subagent MUST load, in this order:
  1. `.agent-harness/generated/CONTEXT_PACK.md`
  2. `.agent-harness/runs/<RUN_ID>/assignments/<ASSIGNMENT_ID>.json`
  3. only the role-specific and evidence files named by that assignment.
- The `SubagentStart` hook injects the shared context contract automatically. A subagent MUST NOT begin repo-wide exploration before validating that its assignment context version matches the current context index.
- If the spawn header or assignment file is missing, stale, or inconsistent, the subagent MUST stop substantive work and report the contract violation.

### 2. Context tiers and independence

Use explicit context tiers rather than relying on hidden parent-thread state:

- Tier 0 — shared core: specification pointer, conventions, symbol table, frozen decisions, changed-surface map, gate definitions, claim/evidence indices, tool availability, and non-goals. All subagents receive this tier.
- Tier 1 — assignment slice: claim IDs, files, symbols, tests, datasets, allowed tools, and expected output schema for one bounded task.
- Tier 2 — sibling results: withheld by default. An agent may read sibling results only when its assignment has `independence_mode = "adjudication"` or explicitly lists those result paths.

`blind-results` means that agents share the problem definition, conventions, assumptions, target form, and test vectors, but MUST NOT inspect another solver or reviewer’s derivation, verdict, or result before submitting their own.

### 3. Spawn budget and topology

- Maximum concurrently active subagents: 4.
- Maximum total subagents per run: 8.
- Maximum nesting depth: 2.
- Depth-2 delegation is allowed only when the parent assignment explicitly grants `may_spawn = true`, lists the unowned claim IDs to delegate, and registers the child assignment before spawning it.
- The main agent MUST create every assignment through `.agent-harness/scripts/new_assignment.py`; unregistered subagents are forbidden.
- A second wave is allowed when it covers new evidence, a disjoint failure class, a genuine independent derivation, or a disputed claim. A differently named reviewer repeating the same evidence and question is not a new wave.

### 4. No duplicate discovery by default

- The main agent or one designated context mapper owns repo mapping and shared evidence collection.
- Other agents MUST use the context pack and assignment slice. They MUST NOT rescan the whole repository unless the assignment sets `discovery_mode = "independent"` and explains why independent discovery is epistemically required.
- Re-reading a file is allowed when the agent verifies a cited claim, but broad rediscovery must be reported as a context defect and added to the shared evidence map rather than repeated by every agent.
- Common command output, large logs, diffs, and generated artifacts must be stored once and referenced by path plus hash; do not paste the same long output into multiple agent prompts.

### 5. Evidence and result contract

- Findings are keyed by stable `claim_id`; prose similarity is not a distinct finding.
- Every substantive verdict MUST include specific, resolvable evidence references, assumptions used, relevant tool/version information, and a reproducible procedure or proof artifact when applicable. Exact byte hashes are conditional on the boundary above, not universal scientific requirements.
- Each subagent writes only to its unique result path declared in the assignment. It must not edit shared context, specs, gates, or another agent’s result.
- Before stopping, every subagent MUST write a result envelope and end its final message with one line of the form:
  `HARNESS_RESULT: {"assignment_id":"...","context_version":"...","status":"pass|fail|inconclusive|error","result_path":"..."}`
- The main agent deduplicates by `(claim_id, evidence_fingerprint, verdict)`. The fingerprint must scope the finding/proposition rather than merely name a whole source; statement prose is not identity. Conflicts and cross-run resolution use the same scoped identity so paraphrasing cannot evade adjudication or inflate the ledger.

### 6. Spec and gate authority

- The current specification and gate registry are authoritative for scope, pass/fail criteria, and required evidence.
- Agents may challenge a gate, but must record the objection in the current result or review; they may not silently redefine success criteria. Do not create a permanent meta-claim or new gate unless a downstream decision actually consumes it.
- Implementation may begin only after the relevant assignment identifies its governing spec clauses and gates.
- Final acceptance of a predeclared gate or claim-promotion decision requires machine-readable gate results plus a human-readable adjudication note. Exploratory work may end with code, data, diagnostics, or a negative result without manufacturing a new gate; it simply cannot promote a claim until the relevant existing acceptance path is used.

### 7. Four-axis CAS cross-validation

For mathematical or physical claims requiring CAS verification, the four mandatory, non-collapsible axes are (canonical display order):

1. Wolfram Engine + xAct
2. SymPy, with high-precision numerical checks where useful
3. SageMath + Singular
4. Lean + mathlib or project proof libraries

All four axes share the same `CAS_CONTRACT.json` (schema v2: identity / semantics / target / per-axis obligations / independence / exceptions): mathematical statement, conventions, domains, assumptions, branch choices, target canonical form, invariants, test vectors, tolerances, and forbidden shortcuts. Until adjudication, each axis MUST NOT read another axis’s scripts, derivation, or result. Agreement without assumption/branch alignment is not counted as cross-validation.

Aggregate adjudication (`.agent-harness/scripts/cas_gate.py adjudicate`) uses exactly five states: `CAS_4AXIS_PASS` (all four PASS under one contract hash), `CAS_PASS_WITH_REGISTERED_EXCEPTION` (exception preregistered before any axis result was read, approved by a non-self approver; never described as a 4-axis pass), `CAS_CONFLICT` (post-normalization disagreement; majority vote forbidden — re-adjudicate with a minimal counterexample), `CAS_BLOCKED` (a required axis missing/blocked/unapproved exception), and `CAS_FAIL` (any valid counterexample or proof failure). Engine non-installation or timeout is a platform/resource blocker, not a computation-class exception. Toolchains run repo-pinned (Lean via `formal/lean-toolchain`). Tool readiness receipts (`cas_gate.py preflight`) are never claim validation. Cost pressure never collapses the four axes into fewer agents — reduce generic mapper/reviewer slots instead (risk-tier budgets: R0 0 / R1 ≤2 / R2 ≤4 / R3 four reserved CAS axis slots).

### 8. Write ownership

- Parallel agents may write only isolated evidence or result artifacts under their assignment directories.
- One designated main writer owns production code, shared documentation, specifications, and gate files.
- The adjudicator reads normalized result envelopes; it does not redo every full analysis unless a disputed claim requires a targeted rerun.
