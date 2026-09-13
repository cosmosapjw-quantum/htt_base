## Physics/math audit verdict

**Scoped PASS.** The MQ1/MQ2 moving-q bounds follow under the declared real
unit-STF2, fixed-Euclidean-frame, full-Frobenius, and both-fibres-nonempty
assumptions. I found no counterexample to the constants, the projection/centre/
radius steps, the degenerate branches, or the raw-Q normalization statement.
This review does not promote a formal/CAS, statistical, physical, or scientific
claim.

## Assumptions and conventions

- `q,q'` are real unit STF2 tensors, `v,v'` are dimensionless contractions,
  and `E=STF3(R3)` has the full Frobenius metric.
- `L_q o=o:q`, `B_q w=3 STF(w tensor q)`, and `R_q=B_q M_q^{-1}` use the
  inherited T5 factor of three: `L_q L_q^*=M_q/3`.
- Hausdorff comparisons exclude empty fibres; radius-zero fibres are
  singletons. No rotating frame, global kernel basis, physical velocity, or
  probability interpretation is used.

## Equation and definition audit

| Item | Status | Issue | Required fix |
|---|---:|---|---|
| T5 adjoint/normalization | PASS | `L_q^*=B_q/3` gives `L_qL_q^*=M_q/3`; the moving-q note retains the factor. | None |
| General `L_s` bound | PASS | For traceless symmetric `s`, `||s||op^2 <= 2||s||F^2/3`; hence `||L_s||^2 <= 3||s||F^2/5`. | None |
| Kernel motion | PASS | The two projection cross-terms have orthogonal domain and range pieces, yielding `||P-P'|| <= min(1,kh)` without a kernel basis. | None |
| Centre and radius | PASS | Orthogonal centre components give `||c-c'|| <= D`; feasibility supplies the two unit-norm centre bounds needed for the square-root step. | None |
| Entire nonconvex fibres | PASS | Matching unit directions in both directed distances and placing the radial difference along the other direction gives the stated `min(rho,rho')` coefficient. This is a set argument, not a support-function argument. | None |
| MQ2 interior branch | PASS | Dividing `|eta-eta'|` by `rho+rho'` gives the displayed `sqrt((1-delta)/delta)` factor; `delta=1` is valid. | None |
| Boundary and unavailable branches | PASS | `eta=1`, `eta>1`, `Q=0`, and `O=0` retain distinct singleton, empty, or unavailable statuses. | None |
| Raw-Q normalization | PASS | The exact amplitude identity implies `h <= ||Q-Q'||F/a0` only when both amplitudes have the asserted positive lower bound. | None |

## Dimensional/sign/limit checks

All objects in MQ1/MQ2 are normalized observable shapes and dimensionless
contractions. The note keeps them separate from shear, vorticity, beta, and
global tilt. No sign-sensitive cosmological expression is introduced.

The fixed-q path `v_t=(1-t)v_*` gives exactly `d_H=sqrt(2t)` and remains a
subfamily when q is allowed to move, so it correctly rules out a uniform
exponent above one half. The interior radial pair has the stated
`delta^(-1/2)` lower-order behavior. Both are explicitly reused source
examples, not new discoveries.

## Numerical/code audit

`check_moving_q.py` passes its deterministic 360-pair synthetic run, four
reused sharpness checks, undefined/infeasible guards, and the centre-only
kernel-motion control. Its output is byte-identical to the sealed
`synthetic.json` (`2e7b8dbf...efb2e72`). Sampling is accurately labelled as a
lower witness for the Hausdorff distance.

An independent seven-dimensional Moore-Penrose realization, built from the
contraction rows rather than `B_q`, agreed over 100 random unit STF2 cases:
maximum projection, centre, eta, and normal-matrix discrepancies were
`8.84e-16`, `2.12e-15`, `1.07e-14`, and `7.78e-16`. A separate 80-trial
nonunit-STF2 normal-matrix check had maximum operator residual `5.21e-15`.
An 80-pair, 2048-directions-per-side stress search produced no bound violation;
the largest sampled/global, separated, interior, projection, and centre ratios
were `0.4091`, `0.6028`, `0.3583`, `0.9929`, and `0.9842`.

## Claim-tier implications

The appropriate status remains `DIRECT_DERIVATION` and `DIAGNOSTIC_ONLY`.
These deterministic fibre bounds do not supply observed inference, coverage,
transfer validation, a physical kinematic response, a Bianchi-family claim, or
formal/CAS admission.

## Fatal blockers

None within the assigned MQ1/MQ2 scope.

## Safe claims

- MQ1 is an explicit sufficient global half-Holder upper bound for the full
  nonconvex unit fibres, conditioned on both fibres being nonempty.
- MQ2 is an explicit sufficient interior Lipschitz upper bound, conditioned on
  the stated delta separation.
- The existing fixed-q evidence remains source-scoped and is not promoted by
  the moving-q synthetic checks.

## Required tests or artifacts

- Reexecution artifact: `check_moving_q_reexecution.json`.
- This report records the analytic review and independent numerical checks;
  neither artifact is a formal or scientific acceptance result.
