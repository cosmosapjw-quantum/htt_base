# R45: Model-posterior information loss

R45 extends R44's deterministic Bayes-factor sufficiency result to the complete posterior over a finite model index. Its core diagnostic is

`E KL[p(M|Y) || p(M|S)] = I(M;Y|S) = I(M;Y)-I(M;S)`.

It also separates model-index posterior preservation from within-model continuous-parameter posterior preservation, and validates the difference using Gaussian synthetic experiments.

- Theory and numerical analysis: [R45_THEORY_AND_MOCK_RESULTS_KO.md](R45_THEORY_AND_MOCK_RESULTS_KO.md)
- Mock specification: [R45_MOCK_SPEC.yaml](R45_MOCK_SPEC.yaml)
- Machine-readable results: [R45_MOCK_RESULTS.json](R45_MOCK_RESULTS.json)
- Run record: [R45_RUN_RECORD.json](R45_RUN_RECORD.json)
- Local-agent restart: [LOCAL_AGENT_RESTART_PROMPT_KO.md](LOCAL_AGENT_RESTART_PROMPT_KO.md)
- Execution DAG: [LOCAL_AGENT_EXECUTION_DAG.yaml](LOCAL_AGENT_EXECUTION_DAG.yaml)
- I/O and provenance contract: [LOCAL_AGENT_IO_CONTRACT.yaml](LOCAL_AGENT_IO_CONTRACT.yaml)

## Scope guard

All experiments are synthetic and finite-dimensional. No real survey data, physical Bianchi transfer, Cobaya production run, or cosmological model identification is performed. The theorem is a direct information-theoretic identity, not claimed as a novel result. The next local-agent action is a clean checkout of the pushed R45 head and execution of its exact test suite before mapping the information-loss diagnostic onto the HTT five-variable joint posterior push-forward.
