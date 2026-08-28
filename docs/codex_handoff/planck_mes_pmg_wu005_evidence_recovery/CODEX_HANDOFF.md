# PMG-WU-005 evidence-recovery handoff

## Current DAG state

```yaml
PMG-WU-004: SUCCEEDED
PMG-WU-005_real_host_execution: COMPLETED_301_ROWS
PMG-WU-005_acceptance: BLOCKED_BY_P1
PMG-WU-005_remote_repair_code: GREEN
PMG-WU-005_local_evidence_rebind: PENDING
PMG-WU-006: NOT_STARTED_AND_FORBIDDEN
```

The map calculation is not repeated. This handoff converts the preserved result into accepted evidence by binding the exact WU-004 input graph, classifying non-reused legacy checkpoints, enforcing frozen/portable byte identities, obtaining one external zero-finding review receipt, and installing a reviewed terminal.

## Exact Git authority

```yaml
repository: cosmosapjw-quantum/htt_base
executed_result_branch: changeset/planck-mes-paired300-irrep-carrier-20260828
executed_result_sha: dded7702f319191e2dd1a88a7a25c64353ea3fb8
executed_result_tree: 318dae5fa3535d0f3d4e32c3558aa6bc8d0058bc
repair_branch: changeset/planck-mes-paired300-evidence-repair-v2-20260828
repair_sha_before_handoff_commit: 28ab4a5750550deb5b581d845e71d591e85dfa60
repair_tree_before_handoff_commit: 648872bf7dc0396ba57678df85d1329af82d9003
repair_pull_request: 430
parent_pull_request: 426
```

Always fetch and verify the current repair-branch head. The handoff commit is a descendant of `28ab4a…`; do not require the branch tip to remain at the pre-handoff SHA.

## Preserve the user's legacy cleanup

Do not switch the user's cleanup worktree to the repair branch. In that worktree, record status and a binary patch, then leave it untouched:

```bash
cd /path/to/current-cleanup-worktree
git status --porcelain=v1 > /tmp/local_legacy_cleanup_status.before.txt
git diff --binary > /tmp/local_legacy_cleanup.before.patch
```

Create a separate worktree:

```bash
cd "$(git rev-parse --show-toplevel)"
git fetch origin --prune
git worktree add \
  ../htt-planck-mes-paired300-evidence-repair-20260828 \
  origin/changeset/planck-mes-paired300-evidence-repair-v2-20260828
cd ../htt-planck-mes-paired300-evidence-repair-20260828
git switch -c local/planck-mes-paired300-evidence-recovery-20260828
```

Do not use `git reset --hard`, `git clean -fdx`, `git checkout -- .`, or a broad restore in the cleanup worktree.

## Validate the pushed repair

```bash
python -m pytest -q \
  tests/obsstat/test_planck_paired300_evidence.py \
  tests/integration/test_planck_paired300_replay_cli.py \
  tests/obsstat/test_planck_irrep_carrier.py \
  tests/integration/test_planck_irrep_carrier_execution.py

python -m py_compile \
  htt/obsstat/planck_paired300_evidence.py \
  htt/obsstat/planck_paired300_recovery.py \
  scripts/observed_runs/replay_planck_paired300_irrep_carrier.py \
  scripts/observed_runs/export_planck_paired300_irrep_carrier.py

git diff --check
```

## Local paths

```bash
export HTT_WORKDIR=/mnt/sn850x2t/htt_base_e2e/workdir
export OUTPUT_DIR="$PWD/docs/generated/planck_pr3_paired300_irrep_carrier"
export PRIVATE_CARRIER="$HTT_WORKDIR/analysis/planck_mes_irrep/paired300_carrier"
export PRIVATE_REPAIR="$HTT_WORKDIR/analysis/planck_mes_irrep/paired300_evidence_repair"
export WU004_PRIVATE="$HTT_WORKDIR/analysis/planck_mes_irrep/intake_manifest.json"
```

Preconditions:

```bash
test -d "$HTT_WORKDIR/raw"
test -f "$PRIVATE_CARRIER/execution_manifest.json"
test "$(find "$PRIVATE_CARRIER" -maxdepth 1 -name '*.npz' | wc -l)" = 301
```

## Prepare map-free evidence

Use the stable code/tests/docs repair commit as the exact implementation
head and tree:

```bash
REPAIR_HEAD=$(git rev-parse HEAD)
REPAIR_TREE=$(git rev-parse HEAD^{tree})

python scripts/observed_runs/replay_planck_paired300_irrep_carrier.py \
  --prepare \
  --output-dir "$OUTPUT_DIR" \
  --frozen-scalar-package docs/generated/pr315_planck_smica_feature_replay.npz \
  --frozen-scalar-metadata docs/generated/pr315_planck_smica_feature_replay.json \
  --wu004-portable-dir docs/generated/planck_mes_irrep_inventory \
  --wu004-private-manifest "$WU004_PRIVATE" \
  --execution-manifest "$PRIVATE_CARRIER/execution_manifest.json" \
  --checkpoint-dir "$PRIVATE_CARRIER" \
  --private-evidence-dir "$PRIVATE_REPAIR" \
  --base-git-head dded7702f319191e2dd1a88a7a25c64353ea3fb8 \
  --implementation-git-head "$REPAIR_HEAD" \
  --implementation-git-tree "$REPAIR_TREE"
```

This command must not open a raw map. It creates:

```text
private:
  processed_input_ledger.json
  checkpoint_disposition.json
portable:
  artifact_manifest.json
  terminal.pending.json
```

The preserved checkpoints are explicitly classified as non-authoritative for future reuse because `checkpoint_reused_count=0`; this does not invalidate the already assembled carrier.

## External fresh review

Start from a fresh context and inspect only:

- `dded770..REPAIR_HEAD` diff;
- `RECOVERY_CONTRACT.yaml` and threat matrix;
- focused test logs;
- private processed-ledger report and checkpoint disposition;
- portable artifact manifest and pending terminal;
- map-free carrier/scalar/rank replay evidence.

Copy `FRESH_REVIEW_RECEIPT_TEMPLATE.json` outside the repository, fill the exact candidate head/tree and artifact-manifest content ID, and record findings. Do not expose chain-of-thought. PASS requires `state=PASS`, `P0=0`, `P1=0`, `independent_read_only_first_pass=true`, and `repair_rounds_used=1`. No second repair is authorized by this handoff.

## Finalize and install

```bash
python scripts/observed_runs/replay_planck_paired300_irrep_carrier.py \
  --finalize \
  --output-dir "$OUTPUT_DIR" \
  --frozen-scalar-package docs/generated/pr315_planck_smica_feature_replay.npz \
  --fresh-review-receipt /absolute/path/to/fresh_review.receipt.json

python scripts/observed_runs/replay_planck_paired300_irrep_carrier.py \
  --install-reviewed-terminal \
  --output-dir "$OUTPUT_DIR" \
  --frozen-scalar-package docs/generated/pr315_planck_smica_feature_replay.npz \
  --private-terminal-archive-dir "$PRIVATE_REPAIR"

python scripts/observed_runs/export_planck_paired300_irrep_carrier.py \
  --replay-committed
```

The old self-attested terminal is archived privately as `terminal.pre_review_rejected.json`. The final `terminal.json` must use format `PLANCK_PR3_PAIRED300_REVIEWED_TERMINAL_V1`.

## Final checks and commit

```bash
python scripts/check_claim_language.py --strict-missing \
  "$OUTPUT_DIR/metadata.json" \
  "$OUTPUT_DIR/scalar_closure.json" \
  "$OUTPUT_DIR/input_identity_receipt.json" \
  "$OUTPUT_DIR/replay.json" \
  "$OUTPUT_DIR/terminal.json"

git diff --check
git status --porcelain=v1

git diff --name-only dded7702f319191e2dd1a88a7a25c64353ea3fb8..HEAD
```

Do not stage any path under `$HTT_WORKDIR`, any raw data, or unrelated legacy docs/plots cleanup. Commit the reviewed portable evidence and repair code, push to the existing repair branch, and update PR #430. After remote readback and exact-head focused CI, update PR #426. Only then may PMG-WU-006 begin.
