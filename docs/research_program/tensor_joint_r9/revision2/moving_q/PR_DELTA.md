# PR-R9-MOVING-Q

The fixed-q fibre result did not control uncertainty in q. MQ1/MQ2 now give
explicit bounds for two nonempty fibres in the same ambient STF space with the
full Frobenius inner product. They separate the changes in minimum-norm centre,
kernel projection and radius without choosing a global kernel basis.

With epsilon=||q-q'||F+||v-v'||2 and A=3 sqrt(2/5), MQ1 gives
`d_H <= 2 A epsilon + sqrt(2 A) sqrt(epsilon)`. If both eta values are at most
1-delta, 0<delta<=1, MQ2 gives
`d_H <= A [2+sqrt((1-delta)/delta)] epsilon`.

| Item | Assumptions / obligation | Result and evidence ceiling |
|---|---|---|
| MQ1 | Unit real STF2 q,q'; unit STF3 fibres; both eta<=1; same fixed ambient frame | Direct analytic uniform upper bound; scoped independent review PASS; no four-axis admission. |
| MQ2 | MQ1 plus both eta<=1-delta, 0<delta<=1 | Explicit interior Lipschitz constant; delta^(-1/2) growth order checked. |
| Boundary sharpness | Prior fixed-q S55 path approaching eta=1 | Reused prior example forces exponent 1/2; not a newly discovered counterexample. |
| Raw-Q transfer | Both ||Q||F,||Q'||F >= a0>0; contraction error bounded separately | Normalization identity gives ||q-q'||F <= ||Q-Q'||F/a0. Q=0 and O=0 normalized shapes remain undefined. |
| Whole fibre | eta<1 sphere; eta=1 singleton; eta>1 empty | Empty fibres excluded from finite comparisons; support alone is not reconstruction of the nonconvex fibre. |

Validation and review:

- New synthetic execution checks 360 moving-q pairs, 96 direction witnesses per
  fibre, kernel/centre/radius bounds, four inherited sharpness cases, and
  infeasible/undefined branches at the unchanged 1e-10 numerical tolerance.
- First execution failed only at NumPy-boolean JSON serialization. Source,
  partial output and stderr are preserved. The serialization-only repair passed;
  all mathematical cases, constants, seed and tolerance were unchanged.
- Independent review checked the derivation and actual source diff. It reproduced
  the new result and separately used a seven-dimensional Moore–Penrose
  construction, nonunit STF controls and 80 pairs with 2048 directions per side.
  No bound violation or blocking proof defect was found. Raw commands/output and
  the valid registered review envelope are preserved. Evidence-only closeout
  retained those commands without rerunning the searches.
- Sampled distances are lower witnesses, not certificates of a Hausdorff upper
  bound. The upper bound is established by the analytic set argument. No CAS or
  observational coverage promotion follows from numerical replay or review.
- Final DAG/mirror checks and progress are in `delivery_validation.json` and
  `progress.txt`. The prior 150-completed checkpoint is preserved; these two
  increments do not trigger the next five-PR checkpoint. No old experiment or
  production test suite is repeated for this research-only change.

The scientific DAG adds an independent theory node within revision 2. It does
not consume or grant FORMAL_DEPTH, JOINT_DEPTH_LAW, a physical response or common
coverage. Full selection/FP/group/CF3 law, validated kinematics and common
state–jet–anchor coverage remain unavailable. Existing HOLDs, quarantines,
STOP_INVALID, unresolved outcomes and all alpha allocations are preserved.

The next single task is the reverse heterogeneous-block reconstruction proof in
pinned Lean core. That task remains useful without external data acquisition.

The original failed partial JSON retains its unfinished field and trailing space.
The staged whitespace check reports that raw evidence line; every other staged
file passes. The original failure bytes are preserved rather than reformatted.
