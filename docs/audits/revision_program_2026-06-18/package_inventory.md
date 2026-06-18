# Revision Program Package Inventory

owner: COMMON
implementation_scope: common
claim_tier: diagnostic_only
transfer_source: none
sky_support_status: not_directional
null_mock_status: not_statistical
generating_command: `venv/bin/python scripts/inventory_revision_program_packages.py --write`

## Packages

| Package | SHA256 | Entries | Role |
| --- | --- | ---: | --- |
| `HTT_Bianchi_revision_program.zip` | `56a4e517946f4e1ca1eccf819953c7e7bee68a88f12d210e76622d04c585b7c3` | 18 | external_revision_input |
| `htt_revision_upgrade_package_2026-06-17.zip` | `407892716cdecacc120559921fee6b07c165aef5d3533e0bba53c0c5f7f1b496` | 90 | external_revision_input |

## Smoke Tests

| Check | Status | Package | Verified SHA256 | Current SHA256 | Exit Code | Evidence Mode | Command |
| --- | --- | --- | --- | --- | ---: | --- | --- |
| `revision_program_run_all` | `passed` | `HTT_Bianchi_revision_program.zip` | `56a4e517946f4e1ca1eccf819953c7e7bee68a88f12d210e76622d04c585b7c3` | `56a4e517946f4e1ca1eccf819953c7e7bee68a88f12d210e76622d04c585b7c3` | 0 | `recorded_prior_smoke_result_hash_bound` | `REPO_ROOT=$(pwd); rm -rf /tmp/htt_revision_program_analysis && mkdir -p /tmp/htt_revision_program_analysis && unzip -q "$REPO_ROOT/HTT_Bianchi_revision_program.zip" -d /tmp/htt_revision_program_analysis && cd /tmp/htt_revision_program_analysis/revision_program/code && "$REPO_ROOT/venv/bin/python" run_all.py` |
| `upgrade_package_pytest` | `passed` | `htt_revision_upgrade_package_2026-06-17.zip` | `407892716cdecacc120559921fee6b07c165aef5d3533e0bba53c0c5f7f1b496` | `407892716cdecacc120559921fee6b07c165aef5d3533e0bba53c0c5f7f1b496` | 0 | `recorded_prior_smoke_result_hash_bound` | `REPO_ROOT=$(pwd); rm -rf /tmp/htt_revision_upgrade_package_analysis && mkdir -p /tmp/htt_revision_upgrade_package_analysis && unzip -q "$REPO_ROOT/htt_revision_upgrade_package_2026-06-17.zip" -d /tmp/htt_revision_upgrade_package_analysis && PYTHONPATH=/tmp/htt_revision_upgrade_package_analysis/htt_revision_upgrade_package_2026-06-17/src "$REPO_ROOT/venv/bin/python" -m pytest /tmp/htt_revision_upgrade_package_analysis/htt_revision_upgrade_package_2026-06-17/tests/test_framework.py -q` |

## Caveats

- synthetic/analytic scaffold
- not publication evidence
- adapt concepts into repo-local generators before manuscript promotion
