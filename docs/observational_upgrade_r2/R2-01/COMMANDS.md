# Commands and raw outcomes

Cwd: `/home/cosmosapjw/Dropbox/bianchi/htt_base`. Base HEAD `9ece0708617ec3649465f4a417c07aa9addad756`; branch `r2/01-structured-core-20261014`. Existing dirty/untracked state preserved.

1. `OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 venv/bin/python -m pytest htt/src/common/test_structured_inference.py htt/src/common/test_bulkflow_estimator.py htt/src/common/test_bulkflow_likelihood.py -q` — exit 127, `raw/first_tests.log`.
2. Same suite using `/home/cosmosapjw/venv/bin/python` — exit 4, `raw/tests_attempt2.log`, missing bass import.
3. Same suite adding `PYTHONPATH=htt:htt/src` — exit 1, `raw/tests_attempt3.log`, test called nonexistent loglike.
4. Public API test corrected to log_likelihood, same command — exit 0, `raw/tests_attempt4.log`, 91 passed.
5. `OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 PYTHONPATH=htt:htt/src /home/cosmosapjw/venv/bin/python docs/observational_upgrade_r2/R2-01/measure_and_compare.py` — exit 0, `raw/measurement.json` and stderr.
6. `OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 PYTHONPATH=htt:htt/src /home/cosmosapjw/venv/bin/python -m pytest htt/src/common -q` — exit 1, `raw/common_tests.log`, 245 passed, 22 missing MES_R7_SOURCE setup errors.
7. Final explicit nuisance-unit validation: `OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 PYTHONPATH=htt:htt/src /home/cosmosapjw/venv/bin/python -m pytest htt/src/common/test_structured_inference.py htt/src/common/test_bulkflow_estimator.py htt/src/common/test_bulkflow_likelihood.py -q` — exit 0, `raw/tests_final.log`, 91 passed.
8. Final measurement with command 5 — exit 0, `raw/measurement_final.json`, empty `raw/measurement_final.stderr`.

No external library APIs were changed; source/package and repository-local numerical oracles govern this integration. No Wolfram/Sage/Lean execution was necessary.

9. Reviewer aligned covariance reproduction using existing interpreter/PYTHONPATH — exit0, `raw/reviewer_first_failure.log`, wrong whitening/rank before repair.
10. First residual/modal repair with expanded extreme covariance tests, same targeted pytest command — exit1, `raw/repair_tests_first.log`,3failed/99passed; retained.
11. Implicit Householder repair, same targeted pytest command — exit0, `raw/repair_tests_second.log`,102passed.
12. Final computed-output guards, same targeted pytest command — exit0, `raw/repair_tests_final.log`,102passed.
13. Final measurement with command5 — exit0, `raw/measurement_repair.json`, empty stderr; four equivalent cases PASS, synthetic38053 measurement.

14. Row-permutation reviewer counterexample reproduction — exit0 with wrong finite W/fit/q, raw/row_permutation_first_failure.log retained.
15. Same targeted pytest command after conservative range guard — exit0,120passed, raw/domain_guard_tests.log. Measurement command5 — exit0, raw/domain_guard_measurement.json.
16. Final pre-QR Frobenius range guard, same targeted pytest command — exit0,120passed, raw/domain_guard_tests_final.log. Measurement command5 — exit0, raw/domain_guard_measurement_final.json, empty stderr.
