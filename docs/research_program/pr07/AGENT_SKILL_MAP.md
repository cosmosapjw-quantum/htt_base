# PR07 CoVe Protocol → Repo Agents & Skills

The audit's 10-lane CoVe (chain-of-verification) reviewer protocol is executed
with the repo's own `.claude` agents and `htt-*` skills — no new agents are
created. Each lane owns a registered artifact and emits only an evidence table
(concise chain of checks), never a private reasoning transcript.

| Audit lane | Owns | Repo `.claude/agents` | Repo `htt-*` skills | Artifact |
|---|---|---|---|---|
| router | scope, hard stops, DAG | `convergence-director` | `htt-dag-orchestrator`, `htt-revision-planner` | `PR_LIST.md`, `pr_registry.yaml` |
| archive auditor | paths, hashes, lineage | `code-cartographer` | `htt-claim-provenance-ledger` | lineage table |
| GR/xAct | frames, units, tensor identities, branches | `physics-stat-auditor` | `htt-physics-math-audit`, `htt-xqpi-fg-formalism` | `docs/generated/pr07_wolfram_proofs.json` |
| numerical dynamics | independent RHS, conservation, integrators | `regression-tester`, `harness-engineer` | `htt-scientific-code-validation` | `pr07_paper_b.json` |
| statistics | likelihood, nuisance, covariance, finite-mock | `physics-stat-auditor` | `htt-observable-statistics`, `htt-statistical-hardening`, `htt-local-global-discrimination` | `pr07_k5_hierarchical_synthetic.json` |
| CMB calibration | E2E pipeline, adaptive scan, global p | (delegated) `physics-stat-auditor` | `htt-local-global-discrimination` | ticket `PR08-001` |
| CF4 reconstruction | selection, grouping, realizations, curl prior | (delegated) `physics-stat-auditor` | `htt-observable-statistics` | tickets `PR08-003/004` |
| reproducibility | clean env, entrypoints, manifests, hashes | `harness-engineer` | `htt-harness-engineering` | CI report |
| red team | zero branches, rank loss, claim leakage | `claim-gate-reviewer` | `htt-adversarial-review-loop`, `htt-family-identification-gate` | `pr07_cove_report.json` |
| consensus editor | claim registry, merge decision | `convergence-director`, `claim-lane-reviewer` | `htt-claim-firewall`, `htt-reviewer-mode-pre-submission` | consensus / claim registry |
| web CRAG | external facts, novelty boundary | `web-crag-researcher`, `docs-citation-auditor` | `htt-web-crag-researcher`, `htt-transfer-provenance` | `WEB_CRAG_LEDGER.md` |

## Operating rule (every PR)

1. Drive the matching skill for the work.
2. Before each substantial commit: run `htt-adversarial-review-loop`.
3. Route claim / manuscript text through `htt-claim-firewall` +
   `scripts/pdf_claim_lint.py` / `scripts/check_claim_language.py`.
4. Route figures through `htt-plot-provenance` / `htt-manuscript-figure-audit`.

## Concise chain-of-checks schema (per claim/measurement)

```yaml
claim_id:
hypotheses:
units_and_frame:
primary_calculation:
independent_check:      # different owner / implementation where possible
boundary_cases:
counterexample:
result:
claim_tier:             # diagnostic_only | program_theorem_synthetic | transfer_conditional
unresolved:             # registered blocker codes if any
```

## CoVe cycle

Register the exact claim + hypotheses → list independent verification questions →
answer each with a different owner/implementation → compare symbolic / numerical /
dimensional results → run counterexamples & boundary branches → downgrade or
**block** when one required answer is missing → emit only the final evidence
table and unresolved obligations.
