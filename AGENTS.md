# AGENTS.md — `htt_base` Codex operating contract

## Mission

Upgrade `htt_base` before the external native low-ell Bianchi solver arrives. The active goal is not to fake a solver or force Bianchi family identification. The goal is to turn the current repository into a claim-tiered, manifest-backed, transfer-provenance-aware, MIO/HTT-separated observatory and inference framework that can later consume native solver outputs cleanly.

Work in the canonical DAG defined by `docs/codex_handoff/pr_backlog.yaml`; `machine_readable/pr_backlog.yaml` is a synchronized compatibility mirror. Never skip dependency gates to chase figures or headline results.

## Existing-checkout policy (owner direction, 2026-09-22)

Use the existing primary checkout for ongoing work. On the owner's machine this
is `/home/cosmosapjw/Dropbox/bianchi/htt_base`; `main` is the publication branch.
Do not create another Git worktree, clone, or full repository copy for routine
implementation, review, validation, or recovery. Use branches in this checkout,
small patches/backups, and disposable test fixtures as needed. Preserve existing
user edits and use one production writer; reviewers may work read-only here.
If a tool or frozen assignment requires another directory, report the exact
constraint instead of silently creating a checkout or rebinding its identity.
Historical worktrees, registrations, budgets and failed receipts remain evidence;
this policy does not authorize their deletion or retroactive admission. A new
worktree requires a later explicit owner exception naming its purpose.
This instruction supersedes older default-isolation recommendations for this
project. Deliver its compact form through the existing shared context pack.

## Project-wide selective readback policy

Owner-directed default (2026-09-22): apply this policy to all project agents,
harness workflows, Git publication, and artifact uploads. Do not perform
post-write content readback when authoritative remote identity, provider success,
and available integrity metadata already establish the mutation. This supersedes
older blanket post-push clone/download/readback habits in project guidance.

| Verification tier | Required evidence | Use |
|---|---|---|
| R0 | Provider success | Temporary, low-risk operations |
| R1 | Provider success, remote ID/ref, available size/hash metadata | Routine default |
| R2 | API/remote metadata plus manifest cross-check | Canonical checkpoint |
| R3 | Actual download/readback plus byte/hash verification | Recovery, release, audit, or a trigger below |

These are mutation-verification tiers, separate from scientific risk/claim tiers.
Use an existing manifest for R2; do not manufacture one solely for readback.

```yaml
readback_policy:
  default: selective
  default_tier: R1
  github:
    post_push_readback: false
    verify_remote_ref: true
    verify_commit_sha: true
    verify_tree_sha: optional
  artifact_upload:
    immediate_download_readback: false
    require:
      - provider_success_receipt
      - remote_object_id
      - size_if_available
      - sha256_if_available
  large_artifacts:
    download_for_verification: false
    retain_local_source_until_receipt: true
  force_readback_when:
    - canonical_release
    - audit
    - destructive_or_overwrite_mutation
    - restore_or_recovery
    - runtime_interruption_recovery
    - provider_reports_checksum_or_size_mismatch
    - provenance_conflict
    - authority_change
    - trust_boundary_crossing
    - external_or_untrusted_import
    - user_explicitly_requests_readback
  manual_override:
    enable_readback: true
```

The force conditions take precedence over default `false` values, including for
large artifacts. `manual_override.enable_readback` permits an explicit per-operation
override; it does not turn on readback globally. Routine non-force pushes to an
existing trusted remote remain R1; a network round trip alone is not a new trust
boundary. Release, authority replacement, or non-fast-forward overwrite is R3.
Record unavailable metadata as unavailable, never invent it or claim byte
verification from provider success alone. Missing required success/identity
evidence leaves the mutation unverified; obtain that evidence before closing it.

Preserve historical receipts and frozen task-specific acceptance requirements.
This policy changes post-write verification defaults, not scientific validation,
CAS/input/context seals, overwrite authorization, or claim-admission gates.
It is agent/harness instruction policy, not a transport hook that intercepts
arbitrary upload commands. Deliver its compact rule through the existing shared
context index and regenerate the context pack after changes; do not rewrite
historical assignments to match a new context version.

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
6. **Independent review.** Use one registered reviewer for correctness, regressions, tests, claim hygiene and maintainability. Fix concrete findings once; use current global observed-runtime routing.
7. **Commit.** Commit only after tests and scoped independent review. Commit message format: `<PR-ID>: <imperative summary>`.
8. **Update status.** Mark the PR in canonical `docs/codex_handoff/pr_status.yaml`, synchronize the `machine_readable/` compatibility mirror, update PR_DELTA, and update progress every five completed PRs.
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

# Project research skills and current runtime (v5)

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

<!-- Distribution note: AGENTS.md.fragment is a merge-only compatibility suffix. This merged AGENTS.md copy is authoritative; the fragment has no independent authority. -->

## Current Codex runtime — 2026-09-29

Read `docs/harness/CURRENT_CODEX_RUNTIME.md` for executable commands and installation.
Read the merged authority selected by `~/.codex/runtime/global-execution-policy.json`.
Global CUH-G owns model routing, child lifecycle, adaptive budgeting, context recovery,
and MLflow spooling. Project hooks deliver project context only; duplicate project
SubagentStart/SubagentStop policy is disabled. Do not invent an author model/effort
from a requested profile: use observed session/turn metadata via the global runtime
observer. Missing metadata stays unknown; reconstruct its source before routing.

### New and ongoing work

- Default to the existing repo root; use a new isolation worktree only after explicit
  owner approval of the reason. Preserve dirty files and one owner per edited file.
- Before execution select the cheapest adequate deterministic/local/native route.
  Keep task IDs and costs on continuation. Soft targets require replanning, not
  science termination; explicit hard limits and frozen one-use allocations remain.
- Bonsai CPU is the context manager. On outage use verified summaries and original
  references. MLflow metadata uses durable spooling and never blocks research.
- Native children are registered through the installed global CLI, pin model AND
  effort, use fresh context, and cannot spawn nested children. Pass only task inputs,
  assumptions, paths and frozen validators. Keep at most four active agents and
  respect the current bounded task's cumulative dispatch/review limits.
- Review is independent quality control. A reviewer receives the diff, contract and
  tests but no prior verdict. Record actual author/reviewer runtime separately from
  requested settings. Use the current router's observed-tier rule and explicit Astra
  blind-review exception; do not invent higher-tier identity.
- One review and one targeted repair closeout per bounded unit. A passed gate must
  lead to its next executable action; no recurring process-only review ladder.

### Historical shared-context/CAS assignments

`.agent-harness/context/CONTEXT_INDEX.json` describes project context;
`.agent-harness/generated/CONTEXT_PACK.md` is its generated delivery view.
New tasks use `CURRENT_CONTEXT_INDEX.json` and `CURRENT_CONTEXT_PACK.md`.
Build only these with `python3 .agent-harness/scripts/build_context_pack.py --current`.
The historical index and pack remain untouched for frozen active runs. The 12,000-character total delivery bound is
retained: bootstrap, role slice, then compact shared core. Long historical context
is reference-only and is read on demand.

Existing frozen assignments retain RUN_ID, ASSIGNMENT_ID, CONTEXT_VERSION,
INDEPENDENCE_MODE, result envelopes and original validators. Their replay protocol
is in `docs/harness/LEGACY_SHARED_CONTEXT_V1.md`; preserved hooks are in
`harness_templates/legacy_hooks/`. Do not restart, rebind, silently close or promote
an old run merely to activate the new runtime. In particular, active R9 and
OUTCOME_UNKNOWN states are untouched. Ordinary global children do not create a
second project assignment/lifecycle solely to satisfy obsolete startup text.

### 7. Four-axis CAS cross-validation

For mathematical or physical claims requiring CAS verification, the four mandatory, non-collapsible axes are (canonical display order):

1. Wolfram Engine + xAct
2. SymPy, with high-precision numerical checks where useful
3. SageMath + Singular
4. Lean + mathlib or project proof libraries

All four axes share the same `CAS_CONTRACT.json` (schema v2: identity / semantics / target / per-axis obligations / independence / exceptions): mathematical statement, conventions, domains, assumptions, branch choices, target canonical form, invariants, test vectors, tolerances, and forbidden shortcuts. Until adjudication, each axis MUST NOT read another axis’s scripts, derivation, or result. Agreement without assumption/branch alignment is not counted as cross-validation.

For the four-axis R3 contract, observed execution adjudication (`.agent-harness/scripts/cas_gate.py run-adjudicate`) uses these states: `CAS_4AXIS_PASS` (all four PASS under one contract hash), `CAS_PASS_WITH_REGISTERED_EXCEPTION` (exception preregistered before any axis result was read, approved by a non-self approver; never described as a 4-axis pass), `CAS_CONFLICT` (post-normalization disagreement; majority vote forbidden — re-adjudicate with a minimal counterexample), `CAS_BLOCKED` (a required axis missing/blocked/unapproved exception), and `CAS_FAIL` (any valid counterexample or proof failure). The separate `adjudicate` command inspects stored envelopes: its primary result remains `CAS_BLOCKED`, with any historical aggregate reported separately. It cannot issue new observed-execution eligibility. Consumers must check exact structured status, current contract/source binding, required axis evidence and eligibility; a status word in explanatory text is never a verdict. These checks concern the contracted mathematical component only, not overall scientific admission. Engine non-installation or timeout is a platform/resource blocker, not a computation-class exception. Toolchains run repo-pinned (Lean via `formal/lean-toolchain`). Tool readiness receipts (`cas_gate.py preflight`) are never claim validation. Cost pressure never collapses the four axes into fewer agents — reduce generic mapper/reviewer slots instead (risk-tier budgets: R0 0 / R1 ≤2 / R2 ≤4 / R3 four reserved CAS axis slots).

### Evidence and ownership

Keep raw failures and exact source/input references. Missing inputs remain HOLD
or UNKNOWN, never zero-filled. Tests, runtime observations, review, publication and
installation are separate evidence stages. No automatic scientific admission.
Parallel writers own disjoint files; reviewers are read-only. Use targeted evidence,
not duplicate repository-wide discovery or copied full parent transcripts.
