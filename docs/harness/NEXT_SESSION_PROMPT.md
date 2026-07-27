# Next Session Prompt

Verify the completed PR-247 closeout from the isolated worktree
`/home/cosmosapjw/Dropbox/bianchi/htt_base_prguard_p0`, branch
`changeset/pr247-publication-integrity-p0`. Do not work from or modify the
user's canonical `/home/cosmosapjw/Dropbox/bianchi/htt_base` tree.

Read first:

- `AGENTS.md`
- `.agent-harness/generated/CONTEXT_PACK.md`
- `.agents/skills/htt-dag-orchestrator/SKILL.md`
- `.agents/skills/htt-harness-engineering/SKILL.md`
- `.agents/skills/htt-scientific-code-validation/SKILL.md`
- `.agents/skills/htt-adversarial-review-loop/SKILL.md`
- `.agents/skills/htt-ssot-handoff-maintainer/SKILL.md`
- `docs/research_program/long_horizon_rescue/pr247_spec.yaml`
- `docs/harness/PUBLICATION_INTEGRITY.md`
- `docs/PR_DELTAS/pr-247.md`
- `docs/codex_handoff/pr_backlog.yaml`
- `docs/codex_handoff/pr_status.yaml`

## Current state

- Baseline commit:
  `be2d545654a5abc7af0819c72ab08d17a4c68d34`.
- Internal work unit `PR-247`, change-set
  `CS-PR247-PUBLICATION-INTEGRITY-P0`, publication group
  `PG-PR247-PUBLICATION-INTEGRITY-P0`, target
  `origin/research/pr04-multicomponent`.
- Active DAG: 194 cards, 142 complete (73.20%), dependency-weighted 79.19%,
  critical-path proxy 81.82%. There is no foreground card; PR-151 remains the
  background acquisition. PR-172 is blocked. No checkpoint is due.
- Candidate A (`c1d2716f...`, seal `b5d845...`) is invalidated. Preliminary
  structural coverage reproduced a bundled-shell classifier bypass, and
  main-writer integration inspection reproduced venv-launcher realpath loss.
  That reviewer timed out before a registered result envelope and is not final
  review evidence.
- Candidate B (`f3521b42...`, seal `0fdfe9...`) is also invalidated. Its
  complete registered FAIL review reproduced a publication bypass through
  Google's codelab-documented top-level Antigravity
  `tool_args.CommandLine` envelope.
- Candidate C (`b431da78...`, seal `4facb9...`) passed a complete registered
  read-only review and latest-target integration against `be2d545...`; receipt
  `6c7e3281...` verifies cleanly.
- PR-247 is `completed`. Its status/SSoT amendment creates a later exact Git
  candidate, so verify that the final branch HEAD has its own matching seal,
  registered PASS review, and latest-target integration receipt. Do not reuse
  candidate-C identities for the amended tree.
- The canonical user tree was not modified. One local implementation commit
  was authorized; no push, PR creation, approval, merge, publisher
  authorization, or external PR was performed.

## Authority boundary

Local commit authority was granted for this coherent change-set. Do not push,
create or mutate a GitHub PR, approve, merge, or invoke a publisher without
separate explicit authority. Ordinary agents never act as publisher.

Repository hooks are only defense in depth. Hard publication enforcement
requires administrator-managed policy or equivalent network isolation and
publisher credentials, HMAC key, and nonce ledger outside ordinary agent
sandboxes.

For the completed closeout:

1. verify the branch is clean and retains the coherent local commit message
   `PR-247: enforce change-set publication integrity`;
2. verify the current `CANDIDATE_SEAL.json` binds the exact final HEAD;
3. verify the final registered review and integration receipt against that
   same seal;
4. if any tracked byte changes, invalidate those artifacts and repeat the
   seal/review/integration cycle;
5. stop at local `READY_FOR_EXTERNAL_PUBLISHER`. Do not invoke the publisher.

The credential-isolated publisher, if separately deployed and authorized,
must collect a fresh repository-bound PR inventory, issue a short-lived
one-use authorization, consume it through the gate, push the sealed SHA
refspec, and create at most one PR for the change-set.

## Immediate verification

```bash
/home/cosmosapjw/Dropbox/bianchi/htt_base/venv/bin/python -B -m pytest -p no:cacheprovider -q scripts/codex_harness/test_harness_enforcement.py scripts/codex_harness/test_codex_assets.py scripts/codex_harness/test_publication_integrity.py
PYTHONPATH="$PWD/htt/src:$PWD/htt:$PWD" /home/cosmosapjw/Dropbox/bianchi/htt_base/venv/bin/python -B -m pytest -p no:cacheprovider --collect-only -q
/home/cosmosapjw/Dropbox/bianchi/htt_base/venv/bin/python -B .agent-harness/scripts/validate_harness.py
/home/cosmosapjw/Dropbox/bianchi/htt_base/venv/bin/python -B scripts/codex_harness/validate_pr_dag.py docs/codex_handoff/pr_backlog.yaml --strict
/home/cosmosapjw/Dropbox/bianchi/htt_base/venv/bin/python -B scripts/codex_harness/sync_pr_dag_mirrors.py --check
/home/cosmosapjw/Dropbox/bianchi/htt_base/venv/bin/python -B scripts/codex_harness/progress_report.py docs/codex_handoff/pr_backlog.yaml docs/codex_handoff/pr_status.yaml --checkpoint-every 5
git diff --check
```

Do not start PR-190 or PR-204 until the exact final PR-247 closeout artifacts
verify. Do not alter PR-151 acquisition state, run partial-mock science,
implement a native solver, or promote any scientific/transfer/family/
publication claim from this process work.
