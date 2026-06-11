# PR-004 PR delta: repo-scoped Codex assets and install checks

## Goal

Make the repository-local Codex operating surface versioned and testable:
`AGENTS.md`, `.agents/skills`, `.codex/agents`, `.codex/rules/default.rules`,
install instructions, and claim-scanner guardrails. This is L0 orchestration
infrastructure only.

## Evidence read

- `AGENTS.md`
- `.agents/skills/htt-dag-orchestrator/SKILL.md`
- `.agents/skills/htt-harness-engineering/SKILL.md`
- `.agents/skills/htt-claim-firewall/SKILL.md`
- `.agents/skills/htt-claim-provenance-ledger/SKILL.md`
- `.agents/skills/htt-family-identification-gate/SKILL.md`
- `.agents/skills/htt-scientific-code-validation/SKILL.md`
- `.agents/skills/htt-ssot-handoff-maintainer/SKILL.md`
- `docs/codex_handoff/pr_backlog.yaml` PR-004 card
- `.codex/agents/*.toml`
- `.codex/rules/default.rules`
- `docs/codex_handoff/07_repo_skill_installation_guide.md`
- `docs/codex_handoff/08_skill_trigger_matrix.md`
- `scripts/install_codex_handoff.sh`
- `.gitignore`

## Web/doc checks

- WEB_CHECK_STATUS: done
- Codex AGENTS.md documentation: Codex discovers repository `AGENTS.md` and
  layers project instructions with global guidance.
  URL: https://developers.openai.com/codex/guides/agents-md
- Codex skills documentation: Codex reads repository skills from
  `.agents/skills` while walking from the current directory to the repository
  root.
  URL: https://developers.openai.com/codex/skills
- Codex rules documentation: `codex execpolicy check --pretty --rules ... --`
  validates rule files and reports matching decisions without executing the
  checked command.
  URL: https://developers.openai.com/codex/rules
- Codex CLI reference: `codex execpolicy check` accepts repeatable `--rules`
  flags and emits JSON decision output.
  URL: https://developers.openai.com/codex/cli/reference

## Subagent divergence

- code_cartographer:
  - Steelman: treat PR-004 as L0 asset verification; keep AGENTS terse, parse
    agent TOML, verify skills, and install only repo-scoped assets.
  - Attack: `.codex` was ignored, the old install guide referenced stale v3
    config, and the current test did not guard config-shape expectations.
- harness_engineer:
  - Steelman: exact-script execpolicy prefixes are the correct fix for Codex
    rule example parsing.
  - Attack: doc-snippet tests are not enough; run the installer into a temp
    target, assert no `.codex/config.toml`, and validate installed rules.
- physics_stat_auditor:
  - Steelman: AGENTS and INSTALL mostly downclaim PR-004 as orchestration only.
  - Attack: family-identification skill wording could imply C6 from external
    transfer, stale trigger docs made the family gate optional for morphology
    wording, and the claim scanner could not run.
- claim_gate_reviewer:
  - Steelman: claim reviewer and AGENTS enforce MIO/HTT separation and no
    native-solver overclaim.
  - Attack: claim scanners must run on explicit `.agents` paths before being
    cited, and solver-handoff wording should evaluate downclaiming rather than
    exclude it.
- regression_tester:
  - Steelman: focused pytest should test asset shape, installer behavior,
    execpolicy decisions, and DAG validation.
  - Attack: add a negative execpolicy regression for unmatched examples.

## Chosen plan

1. Add `scripts/codex_harness/test_codex_assets.py` as the deterministic
   PR-004 regression suite.
2. Fix `.codex/rules/default.rules` by replacing the non-matching broad harness
   prefix with exact script-token prefixes.
3. Unignore `.codex/agents/*.toml` and `.codex/rules/default.rules` while
   continuing to ignore `.codex/config.toml`.
4. Add `docs/codex_handoff/INSTALL.md` and align the older install guide away
   from stale v3 config instructions.
5. Add and test `scripts/codex_harness/validate_codex_config_shape.py`.
6. Make the installer file-operation path testable and update its message to
   v4 without copying unrelated repository docs.
7. Repair claim scanners so explicit `.agents` paths are scannable, regexes
   compile, and guardrail/prohibition wording is not a false positive.
8. Tighten family-identification, solver-handoff, trigger-matrix, and agent
   wording to keep C6 blocked until native low-ell morphology atlas plus gates.
9. Record the five-PR checkpoint using `progress_report.py --checkpoint-every 5`.

## Files changed

- `.gitignore`
- `.codex/agents/*.toml`
- `.codex/rules/default.rules`
- `.agents/skills/htt-claim-provenance-ledger/scripts/check_claim_status.py`
- `.agents/skills/htt-claim-provenance-ledger/scripts/check_forbidden_claims.py`
- `.agents/skills/htt-family-identification-gate/SKILL.md`
- `.agents/skills/htt-solver-handoff-readiness-audit/SKILL.md`
- `docs/codex_handoff/00_Codex_global_rules.md`
- `docs/codex_handoff/07_repo_skill_installation_guide.md`
- `docs/codex_handoff/08_skill_trigger_matrix.md`
- `docs/codex_handoff/INSTALL.md`
- `docs/codex_handoff/pr_status.yaml`
- `machine_readable/pr_status.yaml`
- `docs/harness/PROJECT_STATE.md`
- `docs/harness/PR_PROGRESS.md`
- `docs/harness/NEXT_SESSION_PROMPT.md`
- `docs/harness/BLOCKERS.md`
- `docs/harness/VALIDATION_LEDGER.md`
- `scripts/codex_harness/test_codex_assets.py`
- `scripts/codex_harness/validate_codex_config_shape.py`
- `scripts/install_codex_handoff.sh`

## Tests run

| Command | CWD | Result | Notes |
| --- | --- | --- | --- |
| `venv/bin/python -m pytest scripts/codex_harness/test_codex_assets.py -q` before implementation | repo root | FAIL | Red phase: broken execpolicy examples and missing `INSTALL.md`. |
| `venv/bin/python -m pytest scripts/codex_harness/test_codex_assets.py -q` | repo root | PASS | `10 passed`; covers AGENTS size, skills, agent TOML, `.gitignore`, execpolicy, installer, config validator, claim scanners, and install doc. |
| `codex execpolicy check --pretty --rules .codex/rules/default.rules -- python -m pytest -q` | repo root | PASS | Decision `allow`; validates PR-card command shape without running pytest. |
| `codex execpolicy check --pretty --rules .codex/rules/default.rules -- python scripts/codex_harness/validate_pr_dag.py docs/codex_handoff/pr_backlog.yaml` | repo root | PASS | Decision `allow`; exact script prefix matches. |
| `codex execpolicy check --pretty --rules .codex/rules/default.rules -- rm -rf /tmp/foo` | repo root | PASS | Decision `forbidden`. |
| `python scripts/codex_harness/verify_skill_layout.py .` | repo root | PASS | `18 skills OK`. |
| `python scripts/codex_harness/validate_codex_config_shape.py .` | repo root | PASS | No project-local `.codex/config.toml` present. |
| `python scripts/codex_harness/validate_pr_dag.py docs/codex_handoff/pr_backlog.yaml` | repo root | PASS | `OK: 62 PRs, DAG valid`. |
| Explicit `check_forbidden_claims.py` over PR-004 claim-sensitive asset/docs paths | repo root | PASS | No forbidden claim patterns detected after false-positive regex fix. |
| Explicit `check_claim_status.py` over PR-004 claim-sensitive asset/docs paths | repo root | PASS | No unmarked strong claims detected after frontmatter/heading handling. |
| `python scripts/codex_harness/progress_report.py docs/codex_handoff/pr_backlog.yaml docs/codex_handoff/pr_status.yaml --checkpoint-every 5` | repo root | PASS | `Completed 5/62 = 8.06%`; dependency-weighted `7.69%`; critical path `14.29%`; checkpoint due. |

## Review findings and fixes

- Finding: `.codex` was ignored, so PR-004 assets would not be versioned. Fix:
  add `.gitignore` exceptions for `.codex/agents/*.toml` and
  `.codex/rules/default.rules`, while keeping `.codex/config.toml` ignored.
- Finding: `default.rules` failed parse-time example validation. Fix: replace
  the broad `["python", "scripts/codex_harness"]` prefix with exact script
  prefixes and add a negative regression.
- Finding: install instructions were not tested as file operations. Fix: run
  `scripts/install_codex_handoff.sh` into a temp target and validate copied
  skills, agents, rules, absence of project config, and installed execpolicy.
- Finding: installer copied the entire repository `docs/` tree into
  `docs/codex_handoff/`, creating nested and unrelated install output. Fix:
  copy only `docs/codex_handoff/` and assert the temp install lacks nested
  `codex_handoff`, `PR_DELTAS`, and generated docs directories.
- Finding: stale install guide referenced v3 and `.codex/config.toml`. Fix:
  point to current `INSTALL.md` and state that project-local config is not
  installed.
- Finding: claim scanners crashed or ignored explicit `.agents` paths. Fix:
  compile-safe regexes, explicit path handling, frontmatter/heading handling,
  and tests.
- Finding: family-identification wording could imply C6 with external transfer.
  Fix: C6 now requires native low-ell morphology atlas plus null/mask/
  covariance/equivalence/rank/PPC gates; external transfer can only support
  explicitly transfer-conditional C5 morphology compatibility.

## Five-PR checkpoint

- Completed: 5/62 = 8.06%.
- Dependency-weighted completion: 7.69%.
- Critical path completion: 3/21 = 14.29%.
- Blocked PRs: none.
- Unblocked next: PR-005, PR-020, PR-010.
- Progress advanced since the prior checkpoint baseline; no replan PR is
  needed.

## Claim hygiene and scientific scope

PR-004 is COMMON L0 orchestration infrastructure. It verifies repo-scoped
Codex assets, install operations, rules, skills, custom agents, and claim
scanner behavior. It does not implement or validate native solver behavior,
transfer calibration, HTT posterior/evidence implementations, MIO diagnostic
reports, null calibration, morphology compatibility, or Bianchi family
identification.

## Residual risks

- Project `.codex` layers still require project trust in Codex clients; the PR
  documents explicit verification commands for that case.
- Full repository pytest was not run; PR-004 verified focused Codex-asset,
  DAG, skill, execpolicy, installer, and claim-scanner behavior.

## Commit

Commit message:

`PR-004: verify repo Codex assets`
