# 01. Scope and Phase Map — Anisotropic Reionization RT

## 0. Purpose

1. This file freezes scope boundaries and phase dependencies.

## 1. In scope

1. Tetrad-based geometry kernel.
2. UV continuum transport.
3. X-ray continuum transport.
4. Lyα transport with ALI.
5. Ionization and thermal chemistry.
6. Spin temperature evolution.
7. Geometry-aware 21-cm optical depth and brightness.
8. Orthogonal Bianchi support.
9. Tilted Bianchi support.
10. Weakly inhomogeneous and patchy box mode.
11. Lightcone-friendly cached stepping.

## 2. Out of scope

1. Final parameter inference.
2. Full polarization.
3. Full Monte Carlo production transport.
4. Survey mask or telescope systematics.
5. Recombination-era primordial line physics inside this stack.

## 3. Phase dependency map

1. Phase 1.1 defines the repository subtree and SSOT freeze.
2. Phase 1.2 defines geometry and source-field interfaces.
3. Phase 1.3 defines UV/X-ray transport on a minimal slab.
4. Phase 1.4 defines production short-characteristics sweeps.
5. Phase 1.5 defines photon-budget accounting.
6. Phase 1.6 defines chemistry and recombination counters.
7. Phase 1.7 defines X-ray heating and kinetic temperature.
8. Phase 1.8 defines Lyα + ALI.
9. Phase 1.9 defines spin temperature.
10. Phase 2.1 defines geometry-aware `δT_b`.
11. Phase 2.2 defines orthogonal Bianchi support.
12. Phase 2.3 defines tilted Bianchi support.
13. Phase 2.4 defines inhomogeneous patch and lightcone cache support.
14. Phase 3.1 freezes reference comparisons.
15. Phase 3.2 freezes scoreboard and release gates.

## 4. Parallel-safe branches

1. Phase 1.5 may begin after phase 1.4 freezes the radiation-state layout.
2. Phase 1.7 may begin after phase 1.3 freezes the continuum rate interface.
3. Phase 2.1 may begin after phase 1.9 freezes `Ts` and `Tk` interfaces.

## 5. Hard gates

1. Phase 1.8 must not start before phase 1.4 is green.
2. Phase 2.3 must not start before phase 2.2 passes orthogonal-limit regressions.
3. Phase 3.* must not start before all authoritative modules have explicit ownership and no silent barrier fallback remains.
