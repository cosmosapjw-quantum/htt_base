# SF07 independent scoped review

- Source base: `2fb4ae497eecc6d5fd73f931f250c763ee6d266d`.
- Author requested: `gpt-6.1-sol/high`; reviewer requested: fresh read-only `gpt-6-astra/xhigh`. Independently observed runtime model and effort: `UNKNOWN` for both.
- Scope: saved 4,756-source fixed estimator, declared PSD angular covariance family, operator contraction, 24 grid scenarios, plot and claim language. This review does not validate empirical Gaia cross-source covariance or physical coverage.
- Independent calculation: alternative 2×2 principal-square-root implementation and SciPy angular distances recovered the full-cohort covariance to maximum relative discrepancy `6.40e-14`, generalized eigenvalues to `3.56e-14`; all 24 six-dimensional covariances were positive definite.
- Finding: the central Gaussian reference mean needed an explicit definition. The parent added `beta_ref = M E[y]` to the report and result contract, regenerated the result, and checked all 24 grid rows and numeric controls stayed equal. The original worker result remains at `worker_result_v1.json`.
- Decision: `PASS_SCOPED` after targeted clarification. The independent calculation checks the conditional operator result, not physical Gaussian coverage or astrophysical detection.
