# Start full Codex PR DAG automation for `htt_base`

You are working in `htt_base`. Read `AGENTS.md`, `.agents/skills`, `.codex/agents`, `docs/codex_handoff/pr_backlog.yaml`, and `docs/codex_handoff/pr_status.yaml` before editing.

Work through the PR DAG in logical topological order without stopping after the first easy patch. Be ambitious about the original research goal: upgrade the current repository into a claim-tiered, manifest-backed, transfer-provenance-aware, MIO/HTT-separated observatory and inference framework before the external native low-ell solver arrives. Do not fake the native solver and do not make Bianchi family-identification claims before native morphology atlas support exists.

For every PR:

1. Start with brainstorming that includes web/documentation search when available. Verify current APIs, package behavior, or Codex mechanics before relying on them. If web is unavailable, record that explicitly and continue with repo-local evidence.
2. Use multiple subagents with non-overlapping roles. At minimum spawn or simulate: code cartographer, harness engineer, physics/statistics auditor, claim-gate reviewer, and regression tester. For each, first steelman its position, then make it attack alternatives.
3. Apply divergence -> metacognition -> verification -> convergence. Do not hallucinate missing APIs, files, or scientific results. Use repository evidence, tests, and generated artifacts.
4. Avoid local minima. Do not only add minimal gates or placeholder wrappers unless the current PR is explicitly a gate/harness PR. Prefer meaningful code+test+docs increments. Large physics/statistics migrations are allowed if staged and validated.
5. Prevent redundant evidence plumbing. Do not merge MIO certificates into HTT evidence. Do not label external transfer as native. Do not let scalar x/Q/F/G imply geometry or family identification.
6. Implement, test, self-review via `/review` or reviewer subagents, fix findings, then commit with message `<PR-ID>: <summary>`.
7. Update `docs/codex_handoff/pr_status.yaml`, PR_DELTA, and any generated manifests. Every five completed PRs, run the progress report, calculate percent complete, and if progress stalls, perform adversarial self-ask / step-back / CRAG with web verification and actively replan the DAG.
8. Regularly close completed subagent threads to avoid thread-limit problems.

Begin with PR-000. Continue through the DAG until blocked by a real dependency, missing permission, or failing test that requires user decision. When blocked, produce a blocker report with exact file, command, failure, attempted fixes, and recommended next PR.
