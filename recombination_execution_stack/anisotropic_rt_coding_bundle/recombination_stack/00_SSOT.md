# 00. SSOT — HyRec-Cov-RT

## 0. Status sentence

1. This file is the single source of truth for solver identity, naming, path authority, and implementation invariants.

## 1. Canonical solver identity

1. Solver name: `HyRec-Cov-RT`.
2. Canonical domain: primordial recombination on anisotropic / inhomogeneous backgrounds.
3. Canonical authoritative path: `EMLA + S_N + short-characteristics + ALI`.
4. Canonical reference path: `EMLA + long-characteristics` on selected snapshots.
5. Canonical fallback path: directional Sobolev only as a diagnostic or preconditioner.
6. Canonical forbidden path: Teff-like reduced spectral manifold as the production solver.

## 2. Canonical geometry conventions

1. Metric signature is `(-,+,+,+)`.
2. Primary congruence is the baryon-electron frame `u^a`.
3. Spatial projector is `h_ab = g_ab + u_a u_b`.
4. Time derivative is `dot(X) = u^a ∇_a X`.
5. Spatial derivative is `D_a X = h_a{}^b ∇_b X`.
6. Velocity-gradient split is `∇_b u_a = -A_a u_b + (1/3) Θ h_ab + σ_ab + ω_ab`.
7. Tetrad is `e_0^a = u^a`, `e_i^a` orthonormal in the rest space of `u^a`.
8. Photon momentum is `p^a = E (u^a + n^i e_i^a)` with `n^i n_i = 1`.

## 3. Canonical physics invariants

1. Hydrogen and helium are solved through an effective multilevel atom interface-state system.
2. Line-centered radiative transfer is authoritative for Lyα and He I bottleneck sectors.
3. Continuum radiation may be compressed for diagnostics but not for authoritative line transport.
4. Visibility output must be computed from `dτ/dλ = σ_T n_e (-u_a k^a)`.
5. Orthogonal and tilted Bianchi are first-class citizens and must never be represented by a silent FLRW fallback.
6. Any quantity depending on baryon-frame microphysics must be computed in the baryon frame, even if transport is executed in another frame.

## 4. Canonical code ownership

1. `geometry_cov_rt` owns metric-to-tetrad conversion, kinematic fields, and ray coefficients.
2. `line_rt_sn` owns `S_N` ordinates, short-characteristics sweeps, frequency drift/diffusion, and ALI iteration.
3. `hydrogen_emla_cov` owns hydrogen interface-state matrices and hydrogen source terms in the `x_e` equation.
4. `helium_emla_cov` owns helium interface-state matrices, H-continuum opacity coupling, and helium source terms.
5. `history_cov_rt` owns top-level orchestration, time stepping, visibility, and cached history output.
6. `reference_longchar` owns non-production long-characteristics regression snapshots only.

## 5. Canonical state vector

1. Global state is `Y_rec = {x_e, T_m, x_H_interface, x_He_interface, N_line[L,q,m,cell]}`.
2. Line state storage is authoritative for key lines only, not for every continuum block.
3. Optional diagnostic state is never allowed to overwrite authoritative state.

## 6. Canonical production-vs-reference rule

1. Production outputs come only from the authoritative path.
2. Reference calculations may falsify the production path.
3. Reference calculations may never silently replace the production path inside a nominal production run.
4. Fallback calculations may initialize or precondition the production path.
5. Fallback calculations may never be used for inference-quality outputs.

## 7. Canonical PR invariants

1. No PR may merge if it introduces a silent FLRW fallback.
2. No PR may merge if it mixes baryon-frame and normal-frame rates without an explicit transform.
3. No PR may merge if it bypasses ALI in a sector marked scattering-heavy.
4. No PR may merge if it changes module ownership without updating this SSOT.
5. No PR may merge if it introduces uncited or unexplained equations in code comments.
6. No PR may merge if new tests do not pin the new invariant being introduced.

## 8. Canonical forbidden claims

1. `Directional Sobolev is accurate enough for production by default.` is forbidden.
2. `Moment closures are equivalent to line transport here.` is forbidden.
3. `Tilt can be treated as a postprocessing boost only.` is forbidden.
4. `Helium can be postponed without affecting architecture.` is forbidden.
5. `The reference path can stand in for the production path.` is forbidden.
