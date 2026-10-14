# Sdss Released Mock Box Dependence Diagnostic

Owner: HTT. Diagnostic-only; scientific admission not evaluated.

Numerical results and retained identities: `result.json`. Figure: `diagnostic.png` / `diagnostic.pdf`.

- 128 training boxes; 64 complete-box bootstrap draws.
- Cluster/IID mean-variance ratio: 0.721393 to 1.19278.

- 256 boxes x8 observers; frozen even/odd box split preserved
- Cluster sandwich concerns ensemble mean, not one observed feature-vector covariance
- Box bootstrap is an empirical stability diagnostic, not exact coverage
- Released additive log-distance response is not a physical boost/global-tilt response
- No calibrated chi-square p-value, 2048-IID claim, or catalogue re-extraction
