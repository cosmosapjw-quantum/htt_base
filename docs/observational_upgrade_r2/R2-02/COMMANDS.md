# R2-02 commands

Cwd `/home/cosmosapjw/Dropbox/bianchi/htt_base`. Existing checkout, branch `r2/02-cf4-provider-20261014`, HEAD `4dbe588698f15eb0a93df657d5bc7b5d0acd1e06`. Dirty/untracked unrelated paths preserved.

All executions used `/home/cosmosapjw/venv/bin/python`, `OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 PYTHONPATH=htt:htt/htt:htt/src`.

- `-m pytest tests/htt/test_cf4_product_provider.py -q`: first exit 0, 10 passed; second exit 1, 11 passed/1 failed (missing R7 `capabilities` interface); third exit 0, 12 passed.
- `-m pytest tests/htt/test_cf4_product_provider.py tests/htt/test_cf4_information.py tests/htt/test_cf4_likelihood.py htt/src/common/test_structured_inference.py -q`: first and final exit 0, 63 passed. Final log `raw/tests_final2.log`.
- `scripts/r2_cf4_product_diagnostic.py`: first/final/final2 exit 0; raw stdout/stderr preserved for each. Final output `raw/diagnostic.json`, stdout `raw/diagnostic_final2.stdout`, stderr `raw/diagnostic_final2.stderr`.

No upstream proof rerun, branch operation, commit, push or unrelated repair. Factory test failure preserved unchanged.

## Review repair

- New frame/high-information eta regressions on the former candidate: exit 1, four failures; `raw/reviewer_regressions_first.log`.
- Product tests after targeted repair: exit 0, 17 passed; `raw/repair_tests_first.log`.
- Final affected four-file suite after explicit field policy and unused Hermite removal: exit 0, 69 passed; `raw/repair_tests_final2.log`.
- Three N100 dense rank-one log-likelihood comparisons: exit 0; `raw/shared_eta_repair_oracle.json`.
- Updated diagnostic: exit 0; `raw/diagnostic_repair_final.stdout`, `.stderr` and `raw/diagnostic.json`.

Former diagnostic retained at `raw/diagnostic_pre_review_repair.json`; former return retained in `PRE_REVIEW_REPAIR_RETURN.{md,json}`.

## Delayed remainder binding closeout

- Delayed block/factory omission regressions before correction: exit 1, 2 failed; `raw/delayed_remainder_first_failure.log`.
- Final affected four-file suite including exact-zero omitted factory log-density/mean: exit 0, 71 passed; `raw/delayed_remainder_final_tests2.log`.
- Actual diagnostic reused from `diagnostic_repair_final`: its remainder is explicitly numeric zero, so the omitted-sentinel correction does not alter that execution path.
