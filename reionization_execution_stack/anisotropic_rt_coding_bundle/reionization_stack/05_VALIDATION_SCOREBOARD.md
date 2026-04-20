# 05. Validation Scoreboard — Anisotropic Reionization RT

## 0. Purpose

1. This file defines the scoreboard and release gates.

## 1. Scoreboard statuses

1. `LOCKED` means the design identity is frozen.
2. `GREEN` means implemented and passing required tests.
3. `YELLOW` means implemented but not yet reference-cleared.
4. `RED` means missing, broken, or non-authoritative.

## 2. SSOT scoreboard

1. 21cmFAST-like workflow preservation: `LOCKED`.
2. Authoritative-path identity: `LOCKED`.
3. Excursion-set demotion to diagnostic-only status: `LOCKED`.
4. Geometry-aware `δT_b` rule: `LOCKED`.

## 3. Implementation scoreboard

1. Geometry kernel: `RED`.
2. Source model kernel: `RED`.
3. UV transport: `RED`.
4. X-ray transport: `RED`.
5. Lyα ALI transport: `RED`.
6. Chemistry update: `RED`.
7. Thermal update: `RED`.
8. Spin-temperature update: `RED`.
9. Geometry-aware brightness output: `RED`.
10. Photon-budget diagnostics: `RED`.
11. Orthogonal Bianchi branch: `RED`.
12. Tilted Bianchi branch: `RED`.
13. Lightcone cache branch: `RED`.

## 4. Minimum test ladder

1. Homogeneous slab absorption test.
2. Point-source attenuation test.
3. FLRW transport-limit test.
4. Short-vs-long continuum comparison snapshot.
5. Lyα ALI convergence test.
6. UV/X-ray rate-compression sanity test.
7. Hydrogen-only ionization history test.
8. Hydrogen+helium test.
9. Photon-conservation diagnostic test.
10. Geometry-aware `δT_b` test.
11. Orthogonal Bianchi branch test.
12. Tilted branch frame-transform test.
13. Inhomogeneous patch shadowing test.

## 5. Freeze gates

1. Phase 1.* may freeze only if items 1 through 7 are green.
2. Phase 2.* may freeze only if items 1 through 11 are green.
3. Phase 3.* may freeze only if all items are green and photon-budget residuals remain within the frozen tolerance set.

## 6. Required regression outputs

1. Ionization histories.
2. Recombination counter histories.
3. Kinetic and spin temperature histories.
4. `δT_b` coeval boxes.
5. Lightcone slices.
6. Photon-budget residual curves.
7. Short-vs-long discrepancy metrics.
8. Orthogonal-vs-tilted continuity diagnostics as `v -> 0`.

## 7. Merge blocker rules

1. Any PR touching transport must update the short-vs-long comparison or justify why not.
2. Any PR touching chemistry must update the photon-budget diagnostic outputs.
3. Any PR touching brightness must update the geometry-aware LOS regression.
4. Any PR that reintroduces a scalar barrier as production logic is a hard blocker.
