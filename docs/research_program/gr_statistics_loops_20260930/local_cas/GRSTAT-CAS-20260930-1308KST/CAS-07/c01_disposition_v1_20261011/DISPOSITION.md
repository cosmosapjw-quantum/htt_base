# G07-A — CAS07-C01 checked disposition

This successor does not rerun the scalar comparison proof. It binds the
original G07-A obligation to the existing C01 component evidence, while keeping
the conditional analytic synthesis as a different result. It does not repair or
close the historical C01 review lifecycle.

## Source binding

| Item | SHA-256 | Role |
|---|---|---|
| `c01_input_aligned_v1_20261005/lean/CAS07C01.lean` | `282d48caf23e01b2cdc81efa81d5bf9818df82b29a107962548660500c82dedd` | exact Lean C01 source |
| `c01_input_aligned_v1_20261005/ADMITTED_INPUTS.json` | `30bbb6fce513eedfd98a693c2acbf3308363a7098a7938f4b5abf7e9282b2e39` | original explicit target and domains |
| `c01_input_aligned_v1_20261005/RETURN.json` | `44953f05c87d3a268d05bcc2118b4ab4a633654af72678fa49726a3f888d2b11` | historical terminal receipt |
| `c01_input_aligned_v1_20261005/review/REVIEW_REPORT.json` | `607584ae45451f4545d4cd1e282595b8472323d996e57b7d3159fe7c6bf0b1b8` | original R1 review, whose mathematical finite verdict is HOLD |
| `conditional_synthesis_v1_20261008/RETURN.md` | source-bound separately | conditional supplied-function synthesis, not C01 replacement |

## Exact disposition

`CAS07C01.lean` formalizes the original positive branch
`f(k,s)=sinh(sqrt(k)*s)/sqrt(k)` for `k>0`, its initial values, derivative
and ODE, and the actual comparison integral. It separately proves the `k=0`
flat branch and the fixed-`s` right limit. The admitted input excludes the
division-by-zero substitution.

The original C01 component is therefore `REUSED_HISTORICAL_COMPONENT_PENDING_
REPAIR_REVIEW`, with historical status exactly
`C01_CAS_4AXIS_PASS_R1_REPAIRED_REVIEW_CLOSEOUT_TRANSPORT_HOLD`. The source
RETURN separately records `actual_repair_review=NOT_RUN` and
`NOT_PUBLISHED_UNREVIEWED_REPAIR`; the source review's finite mathematical
verdict is `HOLD` for R1 coverage. None of these historical states is changed
by this disposition. The later conditional synthesis consumes supplied analytic
functions and is neither an implication from C01 to the full CAS07 result nor a
replacement for its historical adjudication.

No Jacobi majorization/existence, C02/C03 result, physical distance inference,
or scientific conclusion follows from this disposition.
