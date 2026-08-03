# PR-278 Tier-A adjudication source manifest

This is a receipt inventory and review queue, not a capability or publication grant.

## Exact counts

- family rows: 28
- author-side candidates: 20
- reviewable now: 19
- non-terminal candidate holds: 1
- event-gated families: 8
- dual-axis rows: 62
- exact dual-axis terminal-receipt crosswalks: 0
- dual-axis INCONCLUSIVE dispositions: 62
- CF4 P0 rescues: 0

## Family queue

| Family | Source status | Reviewable | Pre-disposition | Blocker |
|---|---|---:|---|---|
| D-ACT | PROMOTABLE_ON_SINGLE_INDEPENDENCE_ADJUDICATION | yes | PENDING_NON_AUTHOR | none |
| D-CF4 | PROMOTABLE_ON_SINGLE_INDEPENDENCE_ADJUDICATION | yes | PENDING_NON_AUTHOR | none |
| D-DESI | BLOCKED_ON_DATA_PR151 | no | HOLD | data_acquisition_pr151 |
| D-K1 | PROMOTABLE_ON_SINGLE_INDEPENDENCE_ADJUDICATION | yes | PENDING_NON_AUTHOR | none |
| D-TEFF | BLOCKED_ON_NATIVE_SOLVER | no | HOLD | native_solver |
| II-NATIVE | BLOCKED_ON_NATIVE_SOLVER | no | HOLD | native_solver |
| M-CLUSTER | PROMOTABLE_ON_SINGLE_INDEPENDENCE_ADJUDICATION | yes | PENDING_NON_AUTHOR | none |
| M-DISCRIM | PROMOTABLE_ON_SINGLE_INDEPENDENCE_ADJUDICATION | yes | PENDING_NON_AUTHOR | none |
| M-DUALAXIS | PROCESS_GATE_NO_LITERATURE_AXIS | no | HOLD | process_only_no_literature_axis |
| M-ESTCOV | GENUINELY_INCOMPLETE | no | HOLD | genuinely_incomplete |
| M-EVALUE | PROMOTABLE_ON_SINGLE_INDEPENDENCE_ADJUDICATION | yes | PENDING_NON_AUTHOR | none |
| M-EVIDENCE | PROMOTABLE_ON_SINGLE_INDEPENDENCE_ADJUDICATION | yes | PENDING_NON_AUTHOR | none |
| M-PARTIALID | GENUINELY_INCOMPLETE | no | HOLD | genuinely_incomplete |
| P-LEGACY | PROMOTABLE_ON_SINGLE_INDEPENDENCE_ADJUDICATION | yes | PENDING_NON_AUTHOR | none |
| T-BIANCHI | PROMOTABLE_ON_SINGLE_INDEPENDENCE_ADJUDICATION | yes | PENDING_NON_AUTHOR | none |
| T-BRIDGE | PROMOTABLE_ON_SINGLE_INDEPENDENCE_ADJUDICATION | yes | PENDING_NON_AUTHOR | none |
| T-EGS | PROMOTABLE_ON_SINGLE_INDEPENDENCE_ADJUDICATION | yes | PENDING_NON_AUTHOR | none |
| T-FRAME | PROMOTABLE_ON_SINGLE_INDEPENDENCE_ADJUDICATION | yes | PENDING_NON_AUTHOR | none |
| T-JOINT | PROMOTABLE_ON_SINGLE_INDEPENDENCE_ADJUDICATION | yes | PENDING_NON_AUTHOR | none |
| T-KE | GENUINELY_INCOMPLETE | no | HOLD | genuinely_incomplete |
| T-MES | PROMOTABLE_ON_SINGLE_INDEPENDENCE_ADJUDICATION | yes | PENDING_NON_AUTHOR | none |
| T-MULTIFLUID | PROMOTABLE_ON_SINGLE_INDEPENDENCE_ADJUDICATION | yes | PENDING_NON_AUTHOR | none |
| T-OMK | PROMOTABLE_ON_SINGLE_INDEPENDENCE_ADJUDICATION | no | HOLD | PR-192 |
| T-PARITY | PROMOTABLE_ON_SINGLE_INDEPENDENCE_ADJUDICATION | yes | PENDING_NON_AUTHOR | none |
| T-RANK2 | PROMOTABLE_ON_SINGLE_INDEPENDENCE_ADJUDICATION | yes | PENDING_NON_AUTHOR | none |
| T-SHARP | BLOCKED_ON_NATIVE_SOLVER | no | HOLD | native_solver |
| T-W2 | PROMOTABLE_ON_SINGLE_INDEPENDENCE_ADJUDICATION | yes | PENDING_NON_AUTHOR | none |
| T-XC | PROMOTABLE_ON_SINGLE_INDEPENDENCE_ADJUDICATION | yes | PENDING_NON_AUTHOR | none |

## Dual-axis negative mapping result

All 62 registered rows retain individual `INCONCLUSIVE` dispositions because no exact terminal-receipt crosswalk exists. Semantic similarity is not a crosswalk.

Final aggregation remains PR-157. `capability_effect=NONE_PENDING_PR157`, `public_use=false`, and the claim ceiling remains `diagnostic_only`.
