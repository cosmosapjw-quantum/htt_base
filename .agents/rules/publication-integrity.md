# Publication integrity

Internal DAG cards are work units, not GitHub pull requests. One failure type
produces a finding or commit; one coherent, frozen change-set may produce at
most one GitHub PR.

Ordinary agents stop at local branches, commits, candidate seals, review
coverage, and integration reports. They must not run `git push`, Git transport
equivalents, `gh`/GitHub API PR mutations, or GitHub MCP mutation actions.
The normal unattended outcome is zero GitHub PRs.

Publication is performed only by a serialized process outside the ordinary
agent workspace. That process owns unavailable credentials and a nonce ledger,
refreshes the target and open-PR inventory, and consumes the exact candidate
seal, read-only review, latest-target integration receipt, and short-lived
authorization. Workspace rules and hooks are guardrails; credential isolation
and a managed policy boundary provide the capability separation.
