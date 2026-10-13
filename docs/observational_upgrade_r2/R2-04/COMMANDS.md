# Executed validation commands

Cwd: /home/cosmosapjw/Dropbox/bianchi/htt_base. Interpreter: /usr/bin/python.

Initial collection attempts (exit 4), preserved in raw/tests_first.log and raw/tests_affected.log, used the same affected tests with PYTHONPATH=htt/htt:htt/src and then default import paths. Failure: ModuleNotFoundError bass in outer shim.

```sh
PYTHONPATH=htt:htt/htt:htt/src /usr/bin/python -m pytest tests/htt/test_conditional_legacy_pushforward.py htt/src/common/test_typefree_functionals.py htt/src/common/test_typefree_depth.py -q
PYTHONPATH=htt:htt/htt:htt/src /usr/bin/python scripts/r2_04_conditional_diagnostic.py
PYTHONPATH=docs/observational_upgrade_r2/R2-04/sources/code /usr/bin/python docs/observational_upgrade_r2/R2-04/sources/code/test_legacy_adapter.py
```

Affected suite was run once before and once after adding the missing depth mass regression. No completed adjacent scientific task was rerun. Raw logs retain the first failures and both passing outcomes.

Bounded reviewer repair: ran the new `-k "cross_draw or multidraw"` tests against the pre-repair candidate (8 semantic FAIL plus 1 floating assertion FAIL), preserving raw failures; then reran the same full affected suite after the immutable cross-draw specification check. The first repaired run retained the floating assertion failure in raw/repair_tests_affected.log; the final run uses abs=2e-16, rtol=0 only for weight normalization comparisons and is retained in raw/repair_tests_final.log.
