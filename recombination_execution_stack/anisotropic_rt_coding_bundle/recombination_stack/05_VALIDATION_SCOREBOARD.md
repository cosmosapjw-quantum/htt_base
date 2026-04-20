# 05. Validation Scoreboard — HyRec-Cov-RT

## 0. Purpose

1. This file defines the scoreboard, acceptance gates, and freeze conditions.

## 1. Scoreboard statuses

1. `LOCKED` means the design choice is frozen and must not be silently altered.
2. `GREEN` means the implementation exists and passes required tests.
3. `YELLOW` means the implementation exists but the reference or stress tests are incomplete.
4. `RED` means missing, broken, or inference-forbidden.

## 2. SSOT scoreboard

1. Authoritative path identity: `LOCKED`.
2. Reference path identity: `LOCKED`.
3. Teff-free production rule: `LOCKED`.
4. Module ownership map: `LOCKED`.

## 3. Implementation scoreboard

1. Geometry kernel: `RED`.
2. Hydrogen EMLA kernel: `RED`.
3. Helium EMLA kernel: `RED`.
4. Short-characteristics line sweep: `RED`.
5. Long-characteristics reference harness: `RED`.
6. ALI driver: `RED`.
7. Visibility output: `RED`.
8. Orthogonal Bianchi branch: `RED`.
9. Tilted Bianchi branch: `RED`.
10. Weakly inhomogeneous patch mode: `RED`.

## 4. Minimum test ladder

1. FLRW recovery test.
2. Directional Sobolev sanity check as a diagnostic-only test.
3. Short-vs-long snapshot comparison test.
4. Hydrogen-only history regression test.
5. Helium-on history regression test.
6. Orthogonal Bianchi regression test.
7. Tilted Bianchi frame-transform regression test.
8. NaN/Inf guard test.
9. Admissible-range guard test for populations and `x_e`.
10. Visibility-peak sanity test.

## 5. Freeze gates

1. Phase 1.* may freeze only if items 1 through 5 of the minimum test ladder are green.
2. Phase 2.* may freeze only if items 1 through 8 are green.
3. Phase 3.* may freeze only if all items are green and the short-vs-long comparison remains within the chosen tolerance across the frozen snapshot set.

## 6. Required regression outputs

1. `x_e(z)` history.
2. `T_m(z)` history.
3. Visibility `g(η)`.
4. Line-state norms for each authoritative line.
5. Short-vs-long discrepancy metrics.
6. Orthogonal-vs-tilted consistency diagnostics in the `v -> 0` limit.
7. Inhomogeneous patch asymmetry diagnostics.

## 7. Merge blocker rules

1. Any `RED` item touched by a PR must either turn `GREEN` or be accompanied by a narrower scope statement in the PR.
2. Any regression drift without an attached explanation is a merge blocker.
3. Any silent change to the meaning of `authoritative path` is a merge blocker.
