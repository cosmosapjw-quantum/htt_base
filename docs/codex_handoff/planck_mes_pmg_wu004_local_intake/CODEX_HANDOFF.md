# PMG-WU-004 local execution handoff

## Exact authority

```yaml
repository: cosmosapjw-quantum/htt_base
work_unit: PMG-WU-004
accepted_predecessor_branch: changeset/planck-mes-coordinate-mechanism-audit-20260828
accepted_predecessor_sha: 03f002d97deb31648f47a9a5bdc0e7706354909e
accepted_predecessor_tree: 1d4447dbf90e0a7170fbe68e5db287e91e4d0391
accepted_predecessor_pr: 422
implementation_branch: changeset/planck-mes-irrep-data-intake-20260828
raw_root: /mnt/sn850x2t/htt_base_e2e/workdir/raw
```

This is a host-execution handoff for the already-compiled PMG-WU-004 contract. It is not a successor research plan. Do not generate another package, audit architecture, or review layer.

## First commands

```bash
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"
git fetch origin --prune
git switch changeset/planck-mes-irrep-data-intake-20260828
git pull --ff-only

git cat-file -e 03f002d97deb31648f47a9a5bdc0e7706354909e^{commit}
test "$(git rev-parse 03f002d97deb31648f47a9a5bdc0e7706354909e^{tree})" = "1d4447dbf90e0a7170fbe68e5db287e91e4d0391"
git merge-base --is-ancestor 03f002d97deb31648f47a9a5bdc0e7706354909e HEAD

python - <<'PY'
import json
from pathlib import Path
p = json.loads(Path("docs/generated/planck_mes_coordinate_audit/terminal.json").read_text())
assert p["state"] == "SUCCEEDED"
assert p["replay_status"] == "MATCH"
assert p["next_executable_action"] == "PMG-WU-004"
PY

export HTT_WORKDIR=/mnt/sn850x2t/htt_base_e2e/workdir
test -d "$HTT_WORKDIR/raw"
mkdir -p "$HTT_WORKDIR/analysis/planck_mes_irrep"
git status --short
```

If the exact predecessor is unavailable or its tree differs, stop with `BLOCKED_BY_MOVED_AUTHORITY`. A later PR-base tip by itself is not a blocker when this exact predecessor remains reachable.

## Implement exactly these surfaces

```text
scripts/observed_runs/inspect_planck_mes_irrep_data.py
tests/integration/test_planck_mes_irrep_inventory.py
docs/generated/planck_mes_irrep_inventory/**
```

Do not modify Planck scientific outputs, reducers, paper sources, carrier code, or raw data.

## TDD sequence

1. Write RED tests for exact inventories, quarantine, containment, no staging, row 00818 semantic validation, strict metadata, and pre/post immutability.
2. Preserve the RED output.
3. Implement the smallest read-only inspector.
4. Execute it against the real host.
5. Generate all four portable outputs and the one private full manifest.
6. Run the focused, negative, and admission-preparation regression commands.
7. Run `git diff --check` and verify no forbidden path is staged.
8. Run one read-only fresh review and at most one bounded repair.
9. Push the branch and update the draft PR.
10. On PASS, start PMG-WU-005 immediately.

## Exact inventory

```text
SMICA CMB MC:   00000..00999 except 00970 = 999 complete
SMICA noise MC: 00000..00299 = 300 complete
Commander CMB:  00000..00002 complete
Commander:      00003..00006 .fits.partial, quarantine before FITS open
SMICA 00818:    semantic FITS validation + streaming digest; size-only forbidden
NPIPE/PR4:      unavailable
hsc_kids root:  KiDS payloads only; no HSC/SACC admission
```

Use metadata and existing sidecars before hashing. Do not prehash the unrelated 910-GiB tree. Hash row 00818 during adjudication; downstream scientific inputs are stream-hashed on first scientific read.

## Required portable outputs

```text
docs/generated/planck_mes_irrep_inventory/intake_summary.json
docs/generated/planck_mes_irrep_inventory/route_receipt.json
docs/generated/planck_mes_irrep_inventory/selected_input_manifest.json
docs/generated/planck_mes_irrep_inventory/terminal.json
```

Private output:

```text
/mnt/sn850x2t/htt_base_e2e/workdir/analysis/planck_mes_irrep/intake_manifest.json
```

The private manifest and all raw/downloaded payloads must remain outside Git.

## PASS semantics

PASS requires actual real-host execution and all required outputs. A script, test suite, inventory scaffold, or user-reported snapshot alone is `PARTIAL`.

The terminal must keep:

```yaml
claim_promotion: false
science_rank_generated: false
raw_data_mutation: false
next_executable_action: PMG-WU-005
```
