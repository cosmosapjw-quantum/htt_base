# L6 — Depth coherence of local-boost vs global-tilt (structural, C0)

Source: `L6_local_global_identifiability.py` → `L6_LOCAL_GLOBAL_IDENTIFIABILITY.json` (collinear scalar model; nuisance priors and noise levels are DECLARED, not measured).

| scenario | unknowns | observables | Jacobian rank | nullity | sd(τ)/β_CMB (declared priors) |
|---|---|---|---|---|---|
| S1 CMB + 1 count shell, shared τ | 5 | 2 | 2 | 3 | 0.54 |
| S2 + CMB aberration | 5 | 3 | 3 | 2 | 0.54 |
| S3 + 3 count tracers (NVSS, RACS, Quaia), shared τ | 9 | 5 | 5 | 4 | 0.29 |
| S4 same, per-shell τ_k | 11 | 5 | 5 | 6 | 0.40–0.57 |

Findings (structural): (i) every scenario has nullity > 0 — boost and tilt are not separately identified without priors on α_k and the intrinsic dipoles s_k;
(ii) more tracers help only if depth coherence (shared τ) is assumed; with free per-shell τ_k the nullity grows with the number of shells;
(iii) the posterior sd(τ) is set by the declared nuisance priors, not by data. No data enter; no claim about the real tilt.
Depth-coherence assumption is therefore a modelling choice that must be declared and tested with independent anchors (e.g. an independent β from CMB aberration, spectral indices α_k measured per tracer).
