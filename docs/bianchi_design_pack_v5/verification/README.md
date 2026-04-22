# Verification Bundle

Run:

```bash
python run_all_verifications.py
```

This executes:

1. `symbolic_verify.py` — SymPy derivations and simplifications,
2. `numeric_verify.py` — independent numerical checks,
3. `crosscheck.py` — compares both result bundles and issues a pass/fail verdict.

Artifacts:
- `symbolic_results.json`
- `numeric_results.json`
- `crosscheck_results.json`
- `run_all_stdout.json`
