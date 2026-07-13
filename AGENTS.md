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
2. **Diverge with distinct roles.** Spawn or simulate at least four non-overlapping roles before implementation: code mapper, harness engineer, physics/statistics auditor, and claim-gate reviewer. Each role must steelman its own approach before objecting to alternatives.
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

Every generated artifact, report, figure, table, or result card must carry:

- owner,
- implementation scope,
- claim tier,
- transfer source,
- config hash,
- input hash list,
- sky support / mask status when directional,
- covariance/null mock status when statistical,
- caveats,
- generating command,
- git commit or worktree state.

No figure without manifest. No manuscript number without generated source. No evidence without matched null and prior/PPC/LOOCV status.

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
- Every result artifact needs: `owner`, `scope`, `claim_tier`, `transfer_source`, `config_hash`, `input_hashes`, `sky_support_status`, `null_mock_status`, and caveats.

## Progress discipline

Every five completed PRs, run the DAG/progress harness and record:

1. completed PR count and percent;
2. test collection status;
3. failed/skipped validation with reasons;
4. claim-tier drift findings;
5. next DAG slice or replanned DAG edges.

If progress percentage does not advance after five PRs, perform step-back/adversarial self-ask and replan the DAG instead of making cosmetic claim gates.
