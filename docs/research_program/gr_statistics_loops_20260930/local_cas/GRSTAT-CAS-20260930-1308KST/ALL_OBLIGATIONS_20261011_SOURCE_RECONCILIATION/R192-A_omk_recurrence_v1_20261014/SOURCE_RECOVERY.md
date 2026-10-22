# R192-A source recovery (OMK all-order recurrence and resonance)

Repository HEAD at recovery: `7bc52116b02feb543ee464ed6954773d555ef14b` (read-only; no git state changed).
Card: `HTT_ALL_OBLIGATIONS_20261011_PACKAGE.zip` member `HTT_ALL_OBLIGATIONS_20261011/tasks/R192-A.json`
(zip sha256 `2d0b6da9308ab43e070a620f49241640b5aa7c80c277e1f0857edea22bc4af6f`; card `source_snapshot` a30d84c7).

## Card source paths

| file | sha256 | relevant lines |
|---|---|---|
| docs/codex_handoff/pr_backlog.yaml | b204c187a5b5f54e157f85994a0b13cbdc79d2193344e8789dba1edd9c78f3d7 | 6014-6054 (PR-192 entry; target line 6032-6033; kill line 6049 "coefficient/denominator disagreement") |
| docs/codex_handoff/remaining_pr_crosswalk.csv | 92b7332ae1338361b95853ce79bb664e9d9dbe4ce1385844de2420d495a3b496 | 26 ("near-FLRW expansion and remainder certificates exist" / "all-order recurrence resonance and validated non-LRS extension") |
| docs/codex_handoff/REMAINING_PR_EXECUTION_PLAN_KO.md | fdffc914abfea93fc4158af3ed1364fa84772a0e0c0266346a5e9423fec2924f | 138-142 ("OMK 일반 recurrence ... 유한 예제나 scalar response를 일반 물리 closure로 부르지 않는다") |

None of the three card sources contains the vector field. It was recovered from the
existing near-FLRW expansion (PR-131) and remainder certificate (PR-132), which the
card names as `existing_reuse`.

## Recovered OMK vector field (verbatim)

`docs/research_program/long_horizon_rescue/pr131_spec.yaml`
(sha256 7dae9316200d1f5baf9adc31e980083d892870e3c18aa30d3bea332638f935c0), lines 81-84:

```
q: 'q = (1+3w)(1-K)/2 + (3/2)(1-w) Sigma^2'
dSigma_dN: 'dSigma/dN = -K - (Sigma/2)[(1+3w)K + 3(1-w)(1-Sigma^2)]'
dK_dN: 'dK/dN = 2K(q + Sigma)'
```

Implementation, `htt/src/common/omk_near_flrw_expansion.py`
(sha256 ef6f8857c8126b0d5d4126d96799b1daecd1d522301de3916766fa867c7d0406):
docstring lines 6-8 (same three equations); code lines 72-82 (`q_exact`, `f_sigma`, `f_k`).
Introduced by commit 59b9806fa ("PR-131: derive the near-FLRW expansion and singular-boundary map").

## Invariant-graph (LRS slaved-manifold) equation

`omk_near_flrw_expansion.py` lines 106-114 (`invariance_coefficients`):
`dh/dK * F_K(h(K), K) = F_Sigma(h(K), K)` with `h(K) = kappa K + c2 K^2 + c3 K^3`,
`resid = diff(h, K) * f_k(h, K) - f_sigma(h, K)` (line 113). pr131_spec.yaml lines 98-100
(`c2_construction`). The card's `Sigma(K,w) = sum_{n>=1} c_n(w) K^n` is this graph with
zero constant term (FLRW fixed point Sigma = K = 0).

## Parameter domain

pr131_spec.yaml line 160: `declared_domain: 'w in (-1/3, 1) OPEN at both ends'`;
`omk_near_flrw_expansion.py` line 44 `DECLARED_DOMAIN = (Fraction(-1, 3), Fraction(1))`.
Single fluid, fixed w; K > 0 Bianchi III, K < 0 Kantowski-Sachs mirror (same RHS,
pr131_spec.yaml 85-90). PR-132 compact sub-domain `|K| <= 1/10, w in [0,1/2]`
(pr132_spec.yaml) is not used here (no remainder claim in R192-A).

## Existing finite coefficients and singular map

- `omk_near_flrw_expansion.py` lines 46-50: `KAPPA_EXACT = -2/(3w+5)`,
  `C2_EXACT = -2(9w^2+18w+13)/((3w+5)^2 (9w+7))`,
  `C3_EXACT = -2(81w^4+324w^3+594w^2+460w+141)/((3w+5)^3 (5w+3)(9w+7))`.
- pr131_spec.yaml line 96 (kappa), 101 (`c2 = kappa (g/2 - 2 kappa)/(2g - s)`, g = 1+3w,
  s = -(3/2)(1-w)), 157 (c3), 134-155 (singular map entries and resonance family `w_n = -(2n+3)/(6n-3)`, n >= 1).
- `docs/generated/pr131_coefficients.json` (sha256 c3499a25ef59eeb808ba52eba0bae662b677e0ed1510b3bcd25129cb53a15e56):
  dust (-2/5, -26/175, -94/875), radiation (-1/3, -1/9, -2/27).
- `omk_near_flrw_expansion.py` lines 335-340 (`resonance_w`), 343-381 (`singular_map`; marginal
  entries w = -1/3, w = 1).

## The "exact Sigma = kappa K" claim (card acceptance item 2)

`htt/obsstat/egs3_omega_k_reopening.py` (sha256 e31414269373cf81e445e01d45184f03fb622e443244ceefef5db9d9ee41308a)
lines 39-41: `Sigma = kappa K , kappa = -1/(2 + q0) (exact)`; lines 257-259 (linear slaving
solution). With q0 = (1+3w)/2, -1/(2+q0) = -2/(5+3w), equal to KAPPA_EXACT. The word
"exact" there refers to the linear slaving coefficient; as an equality of the invariant
graph it is false whenever c2 != 0 (Lean targets T10-T12 below). That module is
v7/v8 SOURCE_FILES-frozen (k5 ticket) and is NOT edited by this task.

## Derivation (hand + sympy, before Lean)

With g = 1+3w, a = (3/2)(1-w): `F_K(S,K) = K(g(1-K) + 2aS^2 + 2S)`,
`F_Sigma(S,K) = -K - (g/2)KS - aS + aS^3`. Coefficient comparison of
`h' F_K(h,X) - F_Sigma(h,X)` at X^n (h = sum c_n X^n, c_0 = 0) gives

`(n g + a) c_n = -[n=1] + (g(n-1) - g/2) c_{n-1} - 2 sum_{i+j=n} i c_i c_j
                 - 2a sum_{i+j+l=n} i c_i c_j c_l + a sum_{i+j+l=n} c_i c_j c_l`.

Denominator `n g + a = n lambda_K - lambda_Sigma = ((6n-3) w + (2n+3))/2`; zero iff
`w = -(2n+3)/(6n-3)` (the registered family). Sympy check of this recurrence against
C2_EXACT/C3_EXACT and of the series residual through order 7:
`raw/probes/sympy_recurrence_check.py` / `.stdout` (scratch probe; not a proof).

## Reused Lean sources

None. No accepted Lean module in the earlier units of this reconciliation directory or
under `local_cas/**` formalizes the OMK system (searched `grep -il "omk\|invariance"` over
`*.lean`). The `raw/imports` directory therefore contains only this task's own olean.

## PR-187 dependency

PR-187 (pr_backlog.yaml 5660-5680, frame-indexed component algebra / signed-curvature
carrier) is an external dependency of PR-192 but not of the R192-A recurrence statement:
the recurrence is a statement about the registered single-frame reduced system only and
makes no cross-frame arithmetic. Not consumed, not claimed.
