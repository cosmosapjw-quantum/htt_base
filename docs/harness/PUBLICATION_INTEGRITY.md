# Change-set and publication integrity

Status: P0 implementation contract. This is internal governance material and
does not establish scientific validity or publication readiness.

## Unit boundaries

`work_unit_id` identifies one internal DAG task. `change_set_id` identifies the
coherent Git review unit. `publication_group_id` identifies its one allowed
external publication lane. A failure type becomes a finding or commit, not a
GitHub pull request. One canonical `change_set_id` may have at most one open
GitHub PR.

The unattended controller always finishes with a local `changeset/` branch,
local commits, a candidate seal when the tree is clean, review and integration
reports, and a publication recommendation. It creates zero GitHub PRs.

## State sequence

1. `init_run.py` resolves an explicit remote target or an existing
   `origin/HEAD`; it never assumes `main`.
2. Implementers work only while `candidate_binding.state=mutable`.
3. After a clean commit, `candidate_seal.py create` records the exact target,
   candidate, merge-base, tree, commit set, binary diff, changed-file set,
   remote destinations, canonical GitHub host/repository identity, and
   integration-policy bytes. Remote URLs with embedded credentials,
   query/fragment data, or ambiguous publication repositories are rejected.
4. `bind_candidate.py` changes the run to the frozen candidate exactly once.
   A repair after freeze starts a new candidate and run.
5. Read-only reviewers emit schema-v3 results and a coverage matrix bound to
   the seal. R2/R3 reviews require concrete executable-oracle argv plus an
   assignment-produced, hash-checked output artifact. Execution origin remains
   honestly `self_declared` until a platform-owned verifier exists.
6. `integration_rehearsal.py` refreshes the target, refuses target drift, uses
   a temporary detached worktree, and runs exactly the policy-registered argv.
   The portable `{python}` token resolves to the rehearsal interpreter's
   absolute path; that executable path and byte hash enter the receipt.
7. A serialized publisher obtains a live PR
   inventory with `pr_inventory.py`, which refuses a `--repo-slug` different
   from the sealed repository identity, issues a short authorization, and
   calls `pr_publication_gate.py consume`. The gate consumes a one-time nonce
   but never publishes.
8. The default external publisher immediately executes fixed, seal-derived
   push and PR creation argv. The push source is the sealed commit SHA, never
   the movable local branch name. Its credential and nonce ledger are
   unavailable to ordinary agents.
9. An attended session may instead use the registered
   `attended_pr_publisher.py` entrypoint only when the current user turn
   explicitly authorizes one PR transaction and the active policy opts into
   `attended_explicit_user`. The entrypoint consumes the same immutable
   evidence and nonce, treats the exact-SHA branch push as an internal step of
   `CREATE_REVIEW_PR`, and verifies the remote SHA and resulting PR. It never
   force-pushes, approves, merges, or changes rulesets.

Any candidate, target, remote, policy, review, integration, inventory, or
authorization drift returns to a blocked state. Normal run closure separately
requires every registered result and a fresh `MERGED_RESULTS.json`.

## Provider guardrails

- Codex: `.codex/hooks.json` runs
  `provider_publication_hook.py --provider codex` for Bash and GitHub mutation
  tools.
- Claude Code: `.claude/settings.json` runs the same classifier through a
  `PreToolUse` hook; exit code 2 blocks.
- Antigravity: `.agents/hooks.json` reads
  `toolCall.args.CommandLine` for `run_command` and returns a `deny` decision.

These repository hooks deliberately deny ordinary-agent direct publication.
There is no environment-variable bypass. The attended entrypoint is the sole
repo-registered exception and performs the complete gated transaction rather
than exposing raw push or PR-mutation authority. They are still guardrails:
project hooks can be disabled, changed, or bypassed on some providers. A hard boundary
requires an administrator-managed hook or equivalent network policy plus
publisher credentials held outside the agent OS identity and no write-capable
GitHub browser session in ordinary agent profiles.

## Provider-independent negative controls

The command classifier must deny absolute and optioned Git, `git send-pack`,
Git aliases resolving to push, non-read-only `gh`, mutating `gh api`, direct
GitHub API clients, nested shell/interpreter literals, and GitHub MCP mutations.
It permits ordinary read-only Git and documented read-only `gh` operations.
Because arbitrary executable code can synthesize network traffic, credential
isolation remains mandatory even when every negative control passes.

## Publisher inputs

The publisher consumes:

- repository-local immutable candidate seal;
- repository-local registered schema-v3 reviewer result and coverage artifact;
- repository-local latest-target integration receipt;
- external live PR inventory;
- external HMAC authorization;
- external publisher key and nonce ledger.

The authorization binds the GitHub host/repository identity, repository push
URL, target, candidate branch and SHA, SHA-sourced head refspec, exact PR
title/body/base/head/draft state, and file hashes of all four evidence
documents. The PR body must contain exactly one matching `Change-Set-ID:` and
`Publication-Group-ID:` line. Its issuance is UTC-bounded by policy and its
nonce is consumed under an exclusive file lock. The external publisher must
also serialize its GitHub transaction and verify the remote head still equals
the sealed SHA before PR creation; a point-in-time inventory cannot by itself
eliminate a concurrent create race.

The HMAC proves possession of the local publisher key only. The free-text
`approved_by` label is not a platform-authenticated human identity, scientific
provenance, or approval signature.

## Attended authorization boundary

Attended publication does not relax candidate or review gates. It is available
only after a clean committed candidate is sealed, independently reviewed,
integrated against the live target, and checked against a fresh PR inventory.
The current user turn must authorize the one review-PR transaction. The
authorization is SHA-, body-, target-, repository-, evidence-, TTL-, and
nonce-bound. A replay, second PR, branch mismatch, target drift, candidate
mutation, force-push, approval, merge, or ruleset mutation fails closed.

This attended lane uses the current authenticated GitHub identity and therefore
does not claim credential isolation. Unattended work cannot select it. The
credential-isolated external publisher remains the stronger default boundary.
