---
name: htt-ssot-handoff-maintainer
summary: Maintain the single source of truth, handoff packets, status snapshots, decision logs, and next-session prompts for long HTT/MIO/BASS Codex runs.
description: Use after every five PRs, after architecture or claim-tier decisions, before external audit packages, when context is large, or whenever project state/validation/claim status changes.
---

# HTT SSOT / Handoff Maintainer Skill

## Purpose

Prevent long-running Codex work from losing context, duplicating claims, or drifting from the intended DAG.

## Required files

Prefer this repo-local structure:

```text
docs/harness/
  PROJECT_STATE.md
  CLAIM_LEDGER.md
  VALIDATION_LEDGER.md
  DECISION_LOG.md
  DEPRECATED_IDEAS.md
  NEXT_SESSION_PROMPT.md
  PR_PROGRESS.md
  BLOCKERS.md
```

Generated canonical status should live under:

```text
docs/generated/status_snapshot.json
docs/generated/claim_ledger.json
docs/generated/status_matrix.md
docs/generated/claim_ledger.md
```

## Required workflow

1. Read current PR status, DAG, and changed files.
2. Update project state with facts only.
3. Separate accepted decisions, conditional decisions, rejected/deprecated ideas, and open risks.
4. Update validation ledger with commands actually run.
5. Update claim ledger when claim status changes.
6. Write next-session prompt that includes current DAG node, blockers, required skills, and validation commands.
7. Package handoff if requested.

## Five-PR checkpoint protocol

Every five PRs, record:

- completed PR count and percent;
- changed packages;
- tests run and skipped;
- claim-tier drift findings;
- subagents used and closed;
- unresolved blockers;
- replan decisions.

## Required output

```markdown
## Updated handoff files

## Current DAG position

## Decisions recorded

## Validation recorded

## Claim-tier changes

## Open risks and blockers

## Next-session prompt
```

## Hard prohibitions

- Do not rewrite history to make failed paths look successful.
- Do not delete deprecated ideas without recording why.
- Do not manually override generated status counts in public-facing docs.
- Do not merge HTT posterior and MIO certificate status.
