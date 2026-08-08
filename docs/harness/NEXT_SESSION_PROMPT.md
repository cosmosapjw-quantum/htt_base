# Next Session Prompt

PR-295 is canonically complete in the isolated worktree
`/home/cosmosapjw/worktrees/htt-pr295-external-boundary-20260808` on branch
`changeset/pr295-external-boundary-repair`.

## Authority and current state

- Entry target: `eaaff9db2636099e8286fb81acc1e652b018fbc5`.
- PR-295 content commit: `824a0c40ba63e130ae2eeb35b93b1ece6fc16e88`.
- Canonical DAG: 244 valid cards; 175 completed; 37 pending; three terminal
  blocked; 28 dormant; no foreground card; PR-151 background-only.
- Completion: 71.72%; dependency-weighted: 74.09%; critical path: 98.70%.
- PR-296 and PR-297 are dependency-ready. Execute PR-296 first, then PR-297.
- PR-280 remains `COMPLETED_FAILED_WITH_RECEIPT`; its aggregate success flag is
  false until both remaining successors pass. PR-281--294 remain held.

## Closed PR-295 result

- The CAMB 1.6.6 visibility oracle moved from the installed BASS tree to
  `scripts/oracles/egs2_camb_visibility.py`.
- Production scanner, direct runner, exact CAMB-absence classification,
  numerical/internal failure classification, clean/dirty wheel identity,
  editable wheel, symlink guard, and deleted-module wheel absence all pass.
- Historical seal SHA-256 `43d4d88b...` and blob `55b26999...` remain
  byte-identical.
- Final exact staged fingerprint `9d12f3b9...` passed strict adjudication at
  `.agent-harness/runs/pr295-postfix-review-20260808/results/pr295_final_candidate_review_20260808.json`.
- Scientific status remains `OPEN_UNCHANGED`; transfer source is
  `external_transfer`; artifact mode is governance/diagnostic; observed-data
  execution and public use are false.

## PR-151 background acquisition

- Resume target: `/mnt/sn850x2t/htt_base_e2e/workdir/raw/desi_dr1_mocks`.
- tmux session: `pr151_acquire_20260808`.
- Checkpoint state: 540/1000 EZmocks complete, batch 55 active, 0/25 Abacus,
  about 736 GiB free.
- Recent cadence implies roughly 2.5--3 days for remaining EZmock batches.
- Do not restart from zero, start finalize, or use partial files scientifically.

## Next DAG slice: PR-296

1. Rebuild the shared context and read the exact PR-296 card and PR-280
   terminal receipt.
2. Reproduce only
   `htt.bass.spectrum.test_d2_pstf_progressive_closure::test_python_pstf_closure_does_not_regress`
   on the latest merged target.
3. Use `$htt-dag-orchestrator`, `$htt-physics-math-audit`,
   `$htt-scientific-code-validation`, and `$htt-adversarial-review-loop`;
   add harness/claim skills only if touched surfaces require them.
4. Keep PR-296 isolated from PR-297 and from PR-151 data. Preserve the raw
   failure, derive the smallest meaningful physics repair, run the PR card and
   adjacent smoke tests, obtain exact independent review, then commit/PR/CI/merge.
5. Proceed to PR-297 only after PR-296 is merged and the remote target is
   re-resolved.

## Required PR-295 closeout verification

```bash
PYTHONPATH=htt/src:htt:htt/htt python -m pytest \
  -p no:cacheprovider -o addopts= -q \
  htt/bass/validation/test_external_code_policy.py
PYTHONPATH=htt/src:htt:htt/htt python -m pytest \
  -p no:cacheprovider -o addopts= -q \
  research_gates/egs2/tests/test_egs2_camb_crosscheck.py
PYTHONPATH=htt/src:htt:htt/htt python \
  scripts/run_egs2_camb_crosscheck_seal.py --check
python scripts/codex_harness/validate_pr_dag.py \
  docs/codex_handoff/pr_backlog.yaml
python scripts/codex_harness/sync_pr_dag_mirrors.py --check
python scripts/codex_harness/progress_report.py \
  docs/codex_handoff/pr_backlog.yaml docs/codex_handoff/pr_status.yaml \
  --checkpoint-every 5
```

## Hard stops

- Any production external-code import, scanner exemption, stale deleted module
  in a wheel, or cleanup outside the guarded project build tree.
- Any CAMB internal/numerical failure relabelled tool unavailable.
- Any mutation of the frozen numerical seal or historical audit manifests
  without an explicit successor receipt.
- Any external-to-native promotion, observed-data use, HTT/MIO ownership
  collapse, geometry detection, or pre-native family identification.
- Any partial PR-151 file used before terminal acquisition/admission.
