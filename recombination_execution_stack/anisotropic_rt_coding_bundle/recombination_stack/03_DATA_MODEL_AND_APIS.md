# 03. Data Model and APIs — HyRec-Cov-RT

## 0. Purpose

1. This file freezes the code-facing structures and public interfaces.

## 1. Core data structures

1. `GeometryState`
   1. Holds metric metadata, tetrad basis, connection coefficients, `Theta`, `sigma_ab`, `omega_ab`, `A_a`.
2. `LineGrid`
   1. Holds line IDs, frequency grids, quadrature ordinates, weights, and cell traversal order.
3. `LineState`
   1. Holds authoritative `N[L,q,m,cell]`.
4. `HydrogenState`
   1. Holds `x_e`, hydrogen interface populations, hydrogen diagnostics, and effective-rate caches.
5. `HeliumState`
   1. Holds helium interface populations and helium diagnostics.
6. `ThermalState`
   1. Holds `T_m`, optional heating/cooling channels, and Compton-rate cache.
7. `HistoryState`
   1. Holds the complete recombination state for a time slice plus visibility output.
8. `ReferenceState`
   1. Holds long-characteristics snapshot results and comparison metrics only.

## 2. Public module APIs

1. `geometry_cov_rt.build_geometry(background_input) -> GeometryState`
2. `line_rt_sn.build_line_grid(config, geometry) -> LineGrid`
3. `line_rt_sn.shortchar_sweep(line_state, line_coeff, geometry, grid) -> LineState`
4. `line_rt_sn.solve_frequency_diffusion(line_state, line_coeff, geometry, grid) -> LineState`
5. `line_rt_sn.ali_iterate(line_state, populations, line_coeff, geometry, grid) -> LineState`
6. `line_rt_sn.compress_escape_ops(line_state, geometry, grid) -> EscapeOps`
7. `hydrogen_emla_cov.build_system(history_state, escape_ops, geometry) -> LinearSystem`
8. `hydrogen_emla_cov.solve_interface(system) -> HydrogenInterfaceState`
9. `helium_emla_cov.build_system(history_state, escape_ops, geometry) -> LinearSystem`
10. `helium_emla_cov.solve_interface(system) -> HeliumInterfaceState`
11. `history_cov_rt.rhs_xe(history_state, hydro_if, he_if, escape_ops, geometry) -> float or field`
12. `history_cov_rt.rhs_tm(history_state, hydro_if, he_if, escape_ops, geometry) -> float or field`
13. `history_cov_rt.update_visibility(history_state, geometry) -> VisibilityState`
14. `reference_longchar.solve_snapshot(snapshot_input) -> ReferenceState`

## 3. Required internal helper APIs

1. `geometry_cov_rt.tracefree_project(tensor)`.
2. `geometry_cov_rt.transform_normal_to_baryon(rad_state, tilt_state)`.
3. `line_rt_sn.make_ordered_upwind_traversal(geometry, grid_shape, ordinate)`.
4. `line_rt_sn.compute_cell_optical_depth(line_coeff, geometry, cell, q, m)`.
5. `line_rt_sn.interpolate_upwind_intensity(line_state, cell, q, m)`.
6. `line_rt_sn.build_lambda_star(line_coeff, geometry, grid)`.
7. `history_cov_rt.assert_no_silent_flrw_fallback(history_state, geometry)`.

## 4. File layout freeze

1. `src/hyrec_cov_rt/geometry_cov_rt.py`
2. `src/hyrec_cov_rt/line_rt_sn.py`
3. `src/hyrec_cov_rt/hydrogen_emla_cov.py`
4. `src/hyrec_cov_rt/helium_emla_cov.py`
5. `src/hyrec_cov_rt/history_cov_rt.py`
6. `src/hyrec_cov_rt/reference_longchar.py`
7. `tests/test_geometry_cov_rt.py`
8. `tests/test_line_rt_sn.py`
9. `tests/test_hydrogen_emla_cov.py`
10. `tests/test_helium_emla_cov.py`
11. `tests/test_history_cov_rt.py`
12. `tests/test_reference_longchar.py`

## 5. Public API invariants

1. All public APIs must accept explicit geometry input and may not reconstruct geometry silently.
2. All public APIs that depend on line transport must accept an explicit `EscapeOps` object rather than recomputing hidden scalars internally.
3. All public APIs that mutate authoritative state must return the mutated state explicitly.
4. All long-characteristics APIs must be namespaced under `reference_longchar`.
5. All APIs must support both orthogonal and tilted branches by explicit branch handling, not by branch suppression.

## 6. Required diagnostics on every returned object

1. `status`.
2. `converged`.
3. `nan_guard_passed`.
4. `frame`.
5. `production_path_tag`.
6. `diagnostic_notes`.
