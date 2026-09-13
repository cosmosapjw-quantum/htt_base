# Targeted repair: actual Singular residuals

The original runner is preserved. Its `singular_zero` routine sent a literal
zero polynomial and reduced it modulo `ideal(1)`, so it was an availability
probe and could not validate a residual. The repaired runner replaces that
placeholder with per-proposition residuals reduced by the actual case-sensitive
`/usr/bin/Singular` under `ideal(0)`. Every proposition also reduces the
intentionally nonzero polynomial `1` under `ideal(0)` and requires that normal
form to remain `1`.

All repaired finite checks passed at execution:

| Proposition | Sage finite result | Singular residual result | Singular negative control |
|---|---|---|---|
| D1 | symbolic scalar `H C H^T` residual is zero | scalar cross-block residual normal form is `0` | `1` |
| D3 | two scalar inverse residuals are zero; determinant is one | both inverse residual normal forms are `0` | `1` |
| D2 | rank-one supported score cleared residual is zero | cleared score residual normal form is `0` | `1` |
| D4 | scalar Schur cleared residual is zero | cleared Schur residual normal form is `0` | `1` |

The runner throws a runtime error whenever an advertised finite check or its
negative control fails. Its JSON `computed.finite_identity_checks` field exposes
the actual outcomes. Contract `checks` remain false and all D1--D4 statuses
remain `INCONCLUSIVE`: no all-dimension proof, probability-law proof,
pseudoinverse range proof, or scientific/formal admission is supplied.

Parent runner command for each matching contract:

```text
/usr/local/bin/sage -python .agent-harness/runs/R9-THEORY-20260914/artifacts/depth_sage_singular/depth_sage_singular_runner_repaired.py D1
```

Replace `D1` with the proposition identifier. Cwd is the repository root and
the contract subprocess limit remains 180 seconds.
