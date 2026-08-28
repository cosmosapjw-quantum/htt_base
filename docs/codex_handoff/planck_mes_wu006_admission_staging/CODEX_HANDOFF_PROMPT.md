# Codex — PMG-WU-006 admission staging, after exact RB2 CI

Repository: `cosmosapjw-quantum/htt_base`
Existing delivery branch: `changeset/planck-mes-wu006-admission-staging-20260829`
Package: `docs/codex_handoff/planck_mes_wu006_admission_staging/`

Read `WORK_UNIT.yaml`, `IMPLEMENTATION_STATUS.json`, `GUIDE_BINDING.md`, and this
prompt. These replace the older instructions to redo WU005 recovery. **RB2 is
already complete. Do not run its prepare/finalize again.**

## Authority and scope

```yaml
RB2_head: 0ae0e70791273c13c7b80ac835232c3c63555c5b
RB2_tree: 680795842feafa8028b8e2b9fe8e1086c5f12280
RB2_reviewed_code_head: 32c9b828ef92a569b36067a8daedcef8f11b4c30
RB2_reviewed_code_tree: 57cbbe79107404c069389b90363a747ff6bc4bf4
RB2_PR: 430
provisional_WU006_head: 67a8e08cc24836130c89bab5c1be26ef71d19ca8
provisional_WU006_PR: 431
raw_maps_or_downloads_required: false
WU006_execution_before_RB2_CI: forbidden
WU007_execution_in_this_unit: forbidden
```

The code is already implemented. Do not recreate the pipeline, invent another
plan, change a frozen tolerance/rank, or repeat completed WU004/WU005 work.
The new boundary tests ran here; full repository and actual numerical replay
are explicitly pending the CI gate. Source modules copied from PR431 retain
exact Git blob identity. Ten scientific/plot function ASTs in the runner are
unchanged. No observed result was regenerated in this delivery.

## 1. Separate worktree and live CI

Leave the existing cleanup and recovery worktrees untouched. Create a separate
worktree from the existing remote delivery branch, with no reset/clean/restore
of the user's original worktree. If an identical worktree already exists, verify
it and reuse it instead of replacing it.

```bash
git fetch origin --prune
git worktree add --detach ../htt-wu006-admission-20260829 \
  origin/changeset/planck-mes-wu006-admission-staging-20260829
cd ../htt-wu006-admission-20260829
git switch -c local/planck-mes-wu006-admission-20260829
RB2=0ae0e70791273c13c7b80ac835232c3c63555c5b
git merge-base --is-ancestor "$RB2" HEAD
test "$(git rev-parse "$RB2^{tree}")" = 680795842feafa8028b8e2b9fe8e1086c5f12280
```

Billing/payment/spending changes belong to the owner. Do not change them, alter
branch protection, disable checks, or create fake successful status records.
After the owner resolves the billing issue, rerun the existing workflows once:

```bash
gh run rerun 33213165196 --repo cosmosapjw-quantum/htt_base
gh run rerun 33213165167 --repo cosmosapjw-quantum/htt_base
gh run rerun 33213165204 --repo cosmosapjw-quantum/htt_base
python scripts/observed_runs/check_planck_mes_rb2_ci.py --head "$RB2"
```

Proceed only for exit 0, `state=PASS`, `transition_open=true`. The checker uses
live read-only GitHub records, all pages, latest run/attempt, exact SHA and the
8 required job names. Missing, skipped, stale or unstarted jobs never count as
PASS. If billing is still blocked, STOP with the measured state. Do not poll
indefinitely or turn nonexecution into a candidate failure.

## 2. Focused verification, after CI

```bash
python -m pytest -q \
  tests/obsstat/test_planck_mes_rb2_ci.py \
  tests/obsstat/test_planck_mes_wu006_admission.py \
  tests/integration/test_planck_mes_wu006_control_boundary.py
python -m pytest -q \
  tests/obsstat/test_observable_irrep_orbit.py \
  tests/obsstat/test_planck_lowell_irrep_projection.py
python -m pytest -q tests/integration/test_planck_mes_irrep_analysis.py \
  -k predecessor_acceptance
```

Do not launch the whole repository suite. The remaining old integration tests
are retained as regressions, not silently deleted; the actual map-free replay
below is the direct numerical integration check for this work unit.

## 3. Preserve and rebind the existing WU006 output

The staging branch deliberately contains no WU006 generated result. Its
provisional output remains at exact commit `67a8e08...`. Do not regenerate maps
or add the old self-attested terminal as accepted evidence.

```bash
PROVISIONAL=67a8e08cc24836130c89bab5c1be26ef71d19ca8
OUTPUT=docs/generated/planck_mes_irrep_analysis
git cat-file -e "$PROVISIONAL^{commit}" 2>/dev/null || git fetch origin "$PROVISIONAL"
test ! -e "$OUTPUT"
git archive "$PROVISIONAL" "$OUTPUT" | tar -x
CODE_HEAD=$(git rev-parse HEAD)
CODE_TREE=$(git rev-parse HEAD^{tree})
PRIVATE=/mnt/sn850x2t/htt_base_e2e/workdir/analysis/planck_mes_irrep/wu006_admission_${CODE_HEAD}
test ! -e "$PRIVATE"
mkdir -p "$PRIVATE"
python - "$OUTPUT" "$PRIVATE/scientific_before.json" <<'PYCODE'
import hashlib,json,sys
from pathlib import Path
out=Path(sys.argv[1]); changed={'result.json','replay.json','plot_audit.json','terminal.json'}
record={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in out.iterdir() if p.name not in changed}
assert len(record)==11
Path(sys.argv[2]).write_text(json.dumps(record,sort_keys=True)+'\n')
PYCODE
python scripts/observed_runs/run_planck_mes_irrep_analysis.py \
  --rebind-preserved --output-dir "$OUTPUT" \
  --private-archive-dir "$PRIVATE/rejected_provisional_evidence"
python scripts/observed_runs/run_planck_mes_irrep_analysis.py \
  --replay-committed --output-dir "$OUTPUT"
python - "$OUTPUT" "$PRIVATE/scientific_before.json" <<'PYCODE'
import hashlib,json,sys,csv
from pathlib import Path
out=Path(sys.argv[1]); before=json.loads(Path(sys.argv[2]).read_text())
assert before=={name:hashlib.sha256((out/name).read_bytes()).hexdigest() for name in before}
rows=list(csv.DictReader((out/'family_table.csv').open()))
assert [r['global_rank'] for r in rows]==['27/301','27/301','34/301','33/301']
assert json.loads((out/'terminal.json').read_text())['state']=='EXECUTED_PENDING_REVIEW'
print('PRESERVED_11_SCIENTIFIC_FILES_AND_RANKS')
PYCODE
```

The implemented rebind changes only four JSON evidence objects and archives
their original bytes privately. Numerical NPZ, tables, registry and PDFs remain
unchanged. Replay rebuilds a numerical reference without rendering new PDFs.
The private archive and old cleanup files must never enter Git.

## 4. One new external review

The review candidate is the current committed code HEAD/tree. All source/test/
contract changes must be committed before review. Only generated output files
may be dirty. Do not review the old `67a8e08...` code and reuse that receipt.

Give the reviewer the base SHA, candidate SHA/tree, actual diff, this contract,
verification logs, predecessor terminal and exact output files. Use
`FRESH_REVIEW_RECEIPT_TEMPLATE.json` outside the repository. The reviewer must
inspect the four existing PDFs at 3.3-inch and 6.8-inch widths. Do not infer
visual PASS from successful plotting or a historical report.

Receipt bindings are exactly:

```text
format = PLANCK_MES_WU006_FRESH_REVIEW_V1
work_unit = PMG-WU-006
candidate_git_head/tree = current committed code HEAD/tree
result_content_id = result.json content_id
predecessor_terminal_sha256 = result.json predecessor_admission.terminal_sha256
objective_output_sha256 = SHA256 of the 14 files other than terminal.json
independent_read_only_first_pass = true
P0 = integer 0; P1 = integer 0
repair_rounds_used = integer 0 or 1
findings = [] or nonblocking P2/P3 findings only
visual_inspection = exact four PDF names, both width statuses PASS
```

These are review outputs, not values the implementer may self-issue. At most
one targeted repair is allowed after a reproduced current-task P0/P1. A repair
requires a new code commit and new external receipt for that exact candidate.
Do not restart an upstream audit or create review-of-review machinery.

## 5. Finalization and publication

```bash
REVIEW="$PRIVATE/fresh_review.json"  # produced by the independent reviewer
python scripts/observed_runs/run_planck_mes_irrep_analysis.py \
  --finalize-reviewed --output-dir "$OUTPUT" --fresh-review-receipt "$REVIEW"
python scripts/observed_runs/run_planck_mes_irrep_analysis.py \
  --replay-committed --output-dir "$OUTPUT"
git diff --check
git status --porcelain=v1
```

The finalizer preserves the external receipt bytes and does not auto-set visual
PASS in the generator's `plot_audit.json`. Actual visual admission is explicitly
`visual_admission_source=fresh_review.json` and is bound to the exact PDFs.

Verify `SUCCEEDED`, P0=P1=0, receipt SHA, clean-code candidate head/tree,
predecessor SHA, and unchanged scientific files. Stage only the WU006 generated
output directory. Its scientific files are preserved imports, not new science.
No source/test changes are permitted after the reviewed code commit.

Push normally to the existing delivery branch, without force or another PR:

```bash
git add -- "$OUTPUT"
git diff --cached --name-only
git commit -m "PMG-WU-006: bind reviewed result to accepted RB2 predecessor"
git push origin HEAD:changeset/planck-mes-wu006-admission-staging-20260829
python scripts/observed_runs/check_planck_mes_rb2_ci.py --head "$(git rev-parse HEAD)"
```

If exact-new-head CI is not yet complete, report `PENDING_CI`, not failure or
accepted transition. Update the existing delivery draft PR and PR430/426 with
actual evidence. Preserve PR431 as provisional historical evidence; do not
force-push, merge, approve, or delete it. WU007 is outside this work unit.

Return the final head/tree, local versus remote CI states, replay and unchanged
scientific-file results, fresh-review SHA, remaining blockers and the next
existing executable contract. Do not report WU006 complete from the staging
code or synthetic test results alone.
