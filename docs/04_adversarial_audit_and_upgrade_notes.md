# Adversarial audit of the previous handoff and improvements in this package

## What was weak before

1. The previous handoff was wave-ordered, but the DAG semantics were too implicit. This package provides a single topological order, machine-readable YAML/JSON, Mermaid and DOT graphs, and a validator script.
2. It did not provide an overwrite-ready `AGENTS.md`. This package provides `AGENTS.md` and a lower-case `agent.md` compatibility copy.
3. It lacked repo-scoped Codex skills and project subagent definitions. This package adds both.
4. It did not include enough harness engineering. This package adds DAG validation, progress reporting, status initialization, PR delta scaffolding, and test-subset routing scripts.
5. It could still encourage local-minimum gate-only patches. The new AGENTS contract requires meaningful code+tests+docs increments except for explicitly gate/harness PRs.
6. It did not enforce cleanup of subagent threads. The new protocol requires subagent closure after each PR and each five-PR checkpoint.

## New hard constraints

- No fake native low-ell solver.
- No Bianchi family identification before native morphology atlas.
- No MIO/HTT score merge.
- No external-transfer-as-native claim.
- No TSC/Teff active science ownership.
- No figures without artifact manifests.
- No status numbers not generated from the status snapshot.

## Aggressiveness without hallucination

The package explicitly allows large coherent migrations: `obsstat`, transfer registry, MIO formalism core, HTT local/global inference, full-covariance MES synthetic harness. It only blocks claims and hidden plumbing that would make the science non-auditable.
