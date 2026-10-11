## Physics/math audit verdict

PASS_SCOPED for the dimensionless scalar inversion only; scientific admission is
HOLD.

## Assumptions and conventions

The frozen source uses signature `(-,+,+,+)`, one perfect fluid, positive
enthalpy `w = epsilon + p`, and `r = |J|/w`. This Lean unit starts only after
that reduction: `0 <= b < 1` and `r = b/(1-b^2)`. It keeps no hidden `c`, `G`,
or frame conversion because both `r` and `b` are dimensionless scalars.

## Equation and definition audit

| Item | Status | Issue | Required fix |
|---|---:|---|---|
| `1-b^2` denominator | PASS | Strictly positive on the supplied branch | Proven in `flux_denominator_pos` |
| Square-root branch | PASS | Positive, not negative, root must be selected | `flux_sqrt` discharges both positivity conditions |
| `b=0` limit | PASS | No division by `b` occurs | Included in theorem hypotheses |
| Vector/Codazzi identification | HOLD | No vector direction or geometric projection is encoded | Keep as a later source-bound obligation |
| Multifluid converse | EXCLUDED | Total flux cancellation is not component untilt | Not stated |

## Dimensional/sign/limit checks

At zero tilt, `r=0` and the identity returns `b=0`. The endpoint `b=1` is
excluded, so the divergent flux branch is not silently included. The scalar
algebra neither derives nor changes the frozen `K=-h h nabla n` Codazzi sign.

## Claim-tier implications

Kernel-checked scalar algebra is available for the declared conditional
single-fluid branch. It is not a geometry/family claim, a full Codazzi proof,
or an observational inference result.

## Fatal blockers

None for this scalar theorem. Full P04 remains blocked on the source-bound
vector projection and Codazzi-geometry interfaces.

## Safe claims

For every real `0 <= b < 1`, the stated rationalized inverse returns `b` from
`b/(1-b^2)` exactly.

## Required tests or artifacts

`raw/compile_axiom_audit.json` preserves the first Lean codegen-marker failure
and final pass. Narrow Python regression: `PYTHONPATH=src python -m pytest
src/common/test_relativistic_kinematics.py -q` exited 0 with 10 passed.
