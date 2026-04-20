# 01. Scope and Phase Map — HyRec-Cov-RT

## 0. Purpose

1. This file defines implementation scope, exclusions, and the exact phase sequence.

## 1. In scope

1. `1+3` covariant tetrad geometry kernel.
2. Hydrogen EMLA on anisotropic / inhomogeneous backgrounds.
3. Helium EMLA on anisotropic / inhomogeneous backgrounds.
4. `S_N` angular discretization for line transport.
5. Short-characteristics production sweeps.
6. Long-characteristics reference snapshots.
7. ALI for Lyα and He I scattering-heavy sectors.
8. Visibility history output.
9. Orthogonal Bianchi specialization.
10. Tilted Bianchi specialization.
11. Weakly inhomogeneous patch tests.

## 2. Out of scope

1. Full polarization transport.
2. Final `C_l` production.
3. Massive-neutrino thermal history redesign.
4. Energy-injection exotica beyond a hook/interface.
5. Arbitrary GRMHD radiation backreaction on the metric.

## 3. Phase dependency map

1. Phase 1.1 defines conventions and file layout.
2. Phase 1.2 defines the geometry kernel.
3. Phase 1.3 defines the hydrogen EMLA kernel.
4. Phase 1.4 defines the line RT toy path.
5. Phase 1.5 defines the short-characteristics production sweep.
6. Phase 1.6 defines the long-characteristics reference harness.
7. Phase 1.7 defines ALI and line-operator splitting.
8. Phase 1.8 couples hydrogen EMLA to line transport.
9. Phase 2.1 adds helium.
10. Phase 2.2 adds visibility and history orchestration.
11. Phase 2.3 adds orthogonal Bianchi production support.
12. Phase 2.4 adds tilted Bianchi production support.
13. Phase 2.5 adds weakly inhomogeneous patch mode.
14. Phase 3.1 freezes regression coverage.
15. Phase 3.2 freezes release-quality scoreboard gates.

## 4. Parallel-safe branches

1. Phase 1.3 and phase 1.4 may proceed in parallel after phase 1.2 if the interface contract in `03_DATA_MODEL_AND_APIS.md` is frozen.
2. Phase 1.6 may begin after phase 1.5 defines the line-state layout.
3. Phase 2.1 may begin once phase 1.8 freezes the hydrogen-side operator API.

## 5. Hard gates

1. Phase 1.8 must not start before phase 1.7 is green.
2. Phase 2.4 must not start before phase 2.3 passes orthogonal-limit regressions.
3. Phase 3.1 must not start before phases 1.* and 2.* modules all have explicit ownership and frozen public APIs.
