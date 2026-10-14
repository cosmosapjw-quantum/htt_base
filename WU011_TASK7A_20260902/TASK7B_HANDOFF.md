# PMG-WU-011 Task-7B handoff

## Node

`PMG-WU-011-TASK7B-CUTSKY-IDENTIFIABILITY-AND-SENSITIVITY-ATLAS`

## Why this node is mandatory

Task-7A closed deterministic evidence generation but found that the registered
reference cut-sky operator is strongly alias-dominated:

- metric-whitened response condition: `407.914947`
- FWL Schur condition: `15415.6425`
- physical source-ell6 to output-ell5 neighbour norm: `11.9668365`
- processed raised-ell7 alias norm: `257.027636`
- alias/neighbour: `21.4783276`

Changing equations or adding regularization before locating the singular
source directions would be premature.

## Frozen authority

- source head: `b2422d9435eafbebd2584b747cb4b4ef9716caaf`
- artifact commit: `db8c0f4a1bbce86a0fa82ba5941aaef0e6f040cf`
- manifest SHA-256: `eb9617d1d0947cc4bb2c87c2d4f5e22f9804af55a7d26f4db731f6cbbea763f0`
- report content ID: `sha256:1a8fcf04ac2ea3da4b92512ad51d25e680682e035b0d3cd4fe5783dcb9b690db`
- Jira owner: `BASS-21`
- separate repository-determinism blocker: GitHub `#445`, Jira `BASS-25`

## Required sensitivity grid

Use a bounded factorial design before any estimator patch.

### Mask geometry

1. full sky;
2. north/south apodized-z reference mask;
3. at least three apodization widths at fixed sky fraction;
4. at least three sky fractions at fixed apodization profile;
5. one rotated copy of every non-full mask to test coordinate/orientation dependence.

### Numerical resolution

- `nside = 8,16,32`; add `64` only for the surviving configurations;
- `processing_lmax = 7,9,12`; include one higher value only if cutoff drift is not closed;
- fixed `healpy==1.20.0`, deterministic thread environment, and exact source head.

### Transfer choices

1. identity source and target transfer;
2. reference Gaussian source/target transfer;
3. matched source=target transfer;
4. source-only smoothing;
5. target-commonization-only variation.

## Required diagnostics per configuration

1. scientific and raw-replay Jacobian content IDs;
2. metric-whitened singular spectrum and condition;
3. smallest right singular vectors decomposed by source `ell=1..6`;
4. smallest left singular vectors decomposed by retained `ell=2..5`;
5. physical `ell=6->5` neighbour norm;
6. processed raised-`ell=7` alias norm;
7. alias/neighbour ratio;
8. numerical decomposition residual;
9. physical-`T0` replay leakage;
10. FWL Schur spectrum and condition;
11. finite-minus-linear and mutation gates;
12. wall time and memory as secondary diagnostics only.

## Hypotheses to discriminate

H1. The large condition number is mainly a mask-sky-fraction effect and
improves monotonically with sky fraction/apodization.

H2. The dominant singular directions are raised source bands, especially
`ell=6 -> ell=7 -> retained`, so explicit high-ell marginalization or basis
augmentation is required.

H3. Source/target transfer noncommutation amplifies otherwise moderate mask
mixing; matched transfers substantially reduce the alias.

H4. The large FWL Schur condition is primarily a nuisance/retained design
problem rather than the boost generator itself.

Do not select among H1--H4 before singular-vector and factorial evidence.

## Kill tests

- A proposed mask fix fails if it lowers one scalar condition number but moves
the unstable singular vector into another source sector without reducing
prediction error.
- Basis augmentation fails if full-sky limits or FWL parity change.
- High-ell marginalization fails if the physical `ell=6->5` neighbour is
silently projected away with the alias.
- Transfer simplification fails if it changes the declared physical transfer
rather than only the estimator representation.
- Any candidate fails if sign, transfer-order, finite-linear, or historical
parity mutations cease to discriminate.

## Decision outputs

Classify the surviving route as exactly one of:

1. `IDENTIFIABLE_WITH_REGISTERED_MASK_AND_TRANSFER`;
2. `IDENTIFIABLE_ONLY_AFTER_BASIS_AUGMENTATION`;
3. `IDENTIFIABLE_ONLY_AFTER_HIGH_ELL_MARGINALIZATION`;
4. `DEVELOPMENT_ONLY_CONDITIONING_UNRESOLVED`;
5. `FITTING_REFUSED_FOR_CURRENT_OPERATOR`.

## Forbidden changes now

- no empirical beta fitting;
- no boost subtraction;
- no claim that cut-sky alias is a physical geometry signal;
- no global tilt or Bianchi attribution;
- no performance-first refactor;
- no loosening of exact full-sky, mutation, FWL, or checksum gates;
- no replacement of byte identity with semantic identity for the PR-315
  reproducibility anomaly.

## Completion gate

Task 7B closes only after a deterministic matrix/plot/receipt package identifies
which singular sectors drive the condition number and yields a stable decision
under mask rotation, resolution, cutoff, and transfer variations. Task 8 may
then perform fresh dual audit and hostile figure review.
