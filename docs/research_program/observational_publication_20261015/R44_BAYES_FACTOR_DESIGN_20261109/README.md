# R44: exact model evidence and c-optimal redshift design

This package is the next research increment after R43. It adds an exact Bayes-factor preservation theorem for a common deterministic statistic, a restricted Gaussian common-covariance sufficiency theorem, counterexamples when covariance or readout information changes, and a nuisance-projected c-optimal redshift/anchor design experiment.

## Files

- `R44_THEORY_AND_MOCK_RESULTS_KO.md`: definitions, theorem proofs, scope, literature, and results.
- `R44_MOCK_SPEC.yaml`: exact synthetic model/configuration contract.
- `R44_MOCK_RESULTS.json`: machine-readable results from 500 common-covariance BF replications and 3000 shell-design calibration replications.
- `LOCAL_AGENT_RESTART_PROMPT_KO.md`: copyable task prompt for actual source-bound local execution.
- `LOCAL_AGENT_EXECUTION_DAG.yaml`: pending local execution DAG.
- `LOCAL_AGENT_IO_CONTRACT.yaml`: required data/chain/source provenance fields.
- `R44_RUN_RECORD.json`: command, tests, environment, hashes and unrun scope.

## Reproduce

Run from repository root:

```bash
python scripts/r44/run_bayes_factor_design_mock.py --seed 20261109 --replications 500 --design-replications 3000 --output docs/research_program/observational_publication_20261015/R44_BAYES_FACTOR_DESIGN_20261109/R44_MOCK_RESULTS.json
pytest -q tests/r44
python -m compileall -q scripts/r44 tests/r44
```

R44 is synthetic/statistical methodology only. It does not use observed catalogues, physical Bianchi transfer, Planck/Gaia end-to-end MC, or Cobaya production sampling. It does not promote empirical publication claims.
