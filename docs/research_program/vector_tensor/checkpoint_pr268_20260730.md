# Vector/tensor phase checkpoint after PR-268

Date: 2026-07-30

This is the phase checkpoint required after PR-268 by the vector/tensor
execution plan. It does not replace the immutable global
`checkpoint_<N>.md` series; the canonical progress harness reports that the
next global five-count checkpoint is 165 and is not yet due.

## Canonical bookkeeping

- Completed: `163/222 = 73.42%`
- Dependency-weighted completion: `80.39%`
- Critical-path proxy: `71/77 = 92.21%`
- Canonical DAG/status: `222 PRs, DAG valid`
- Canonical and `machine_readable/` mirrors: synchronized
- Newly dependency-ready programme nodes: `PR-269`, `PR-271`

The PR-269/271 start gate remains closed until the exact PR-268 closeout
candidate has a valid independent `PASS` result at
`.agent-harness/runs/pr268-final-review-20260730-r1/RUN_SUMMARY.json`.

## Registry and oracle integrity

- Registered v3 obligations: 123 disjoint rows.
- Owner-requested 65 alias: legacy signature inventory, true partition
  `31 T + 34 S`.
- Owner-requested 58 alias: proposal inventory, true partition
  `30 I + 24 II + 4 BRIDGE`.
- Proof classes: the source-preserving `U/TC/ST` value on every row.
- Proof adjudication: all 123 rows remain `NOT_ADJUDICATED`.
- Typed legacy signatures: 12; source-not-typed legacy signatures: 53.
- Tensor-foundation links: 12 one-to-one proposition-to-proposal-row links.
- Stable oracle mode: full mode at seed `20260730`, deterministic all-pass.
- Supplied fast mode: retained as
  `REPRODUCED_NON_STABLE_TF11_AT_REGISTERED_SEED`.
- Mutation vectors: six, all refused.

The frozen v2 registry and loader, PR-260 intake, supplied two-pillar
registry, and supplied oracle retain their registered hashes. The production
oracle is byte-identical to the supplied proposal. Raw row cardinality and
oracle output are forbidden as theorem-count or proof-adjudication evidence.

## Validation

- PR-268 focused contract: `21 passed`
- Adjacent regression: `101 passed`
- Smoke: `6 passed`, `10353 deselected`
- Full collection: `10300/10359 collected`, `59 deselected`
- Strict DAG/mirror, generator check, claim lints, compileall, `pip check`,
  and whitespace checks: pass

Two historical tests remain failing exactly as on the PR-267 base:
`SOURCE_HASH_MISMATCH mio.formalism.namespace` and stale historical theorem
extension metadata/config hashes. They are recorded in the PR delta and do
not authorize modification of frozen sources in PR-268.

The first registered evidence-map run stopped on its own stale assignment
input and is preserved as non-acceptance process evidence. A fresh,
exact-candidate review is required.

## Claim drift and next slice

- Claim drift: none.
- `TF-02` completeness remains `UNPROVEN`.
- `TF-06` remains principal-stratum only and cannot identify a family.
- `TF-12` remains conditional on its complete premise block.
- MIO/HTT ownership and the pre-native family gate are unchanged.
- No new gate or replan PR is warranted.

After exact PR-268 acceptance, PR-269 and PR-271 are the permitted parallel
pair. One main writer still owns shared production and registry files.
