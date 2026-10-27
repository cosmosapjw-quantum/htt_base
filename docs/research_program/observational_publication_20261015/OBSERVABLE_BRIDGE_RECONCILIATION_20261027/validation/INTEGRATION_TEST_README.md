# Reproducing the selected-file integration review

`RESULTS.json` is the final 14/14 receipt. `R32_REGISTRATION_REPAIR.json` records the exact metadata repair; `strict_comparison_final.json` records the remaining full-strict boundary. The unchanged controller and router are executed, including the actual append-frontier CLI, solely against disposable fixtures.

Run with the selected-file baseline snapshot at commit `a55036ad09c53a9215dee3282e425d37cfb95443` and the candidate overlay:

```bash
python verify_overlay.py --baseline /path/to/selected-baseline --patch /path/to/candidate-overlay --work /path/to/disposable-verification
```

The work directory must be disjoint from both inputs. The script writes fixtures, logs and receipts there. It does not read or activate the owner campaign. This archived package does not contain the full baseline snapshot or repository; provide the two input trees explicitly outside the original audit workspace. The pinned `pr167_intake_contract.py` import dependency is supplied in `deps/` when absent from the selected baseline.

For full strict verification in the actual owner checkout, use its original historical receipt:

```bash
python scripts/codex_harness/validate_pr_dag.py docs/codex_handoff/pr_backlog.yaml --status docs/codex_handoff/pr_status.yaml --strict-rescue-slice
```

The selected-file snapshot stops at the missing `docs/generated/pr167_pre_intake_semantic_receipt.json`. Full strict PASS, actual dispatch, scientific qualification and whole-repository CI are not claimed.
