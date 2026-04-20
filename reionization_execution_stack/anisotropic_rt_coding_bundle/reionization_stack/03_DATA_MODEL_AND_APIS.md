# 03. Data Model and APIs — Anisotropic Reionization RT

## 0. Purpose

1. This file freezes code-facing structures and module interfaces.

## 1. Core data structures

1. `GeometryState`
   1. Holds tetrad basis, ray coefficients, `Theta`, `sigma_ab`, `omega_ab`, `A_a`.
2. `SourceState`
   1. Holds UV, X-ray, and Lyα emissivity fields.
3. `RadiationState`
   1. Holds continuum or line intensity blocks.
4. `ChemistryState`
   1. Holds `xHII`, `xHeII`, `xHeIII`, `Nrec`.
5. `ThermalState`
   1. Holds `Tk`, heating channels, and optional cooling diagnostics.
6. `SpinTempState`
   1. Holds `xalpha`, `xc`, `Ts`.
7. `BrightnessState`
   1. Holds `tau21`, `deltaTb`, LOS diagnostics.
8. `PhotonBudgetState`
   1. Holds emitted, absorbed, escaped, and residual counters.
9. `LightconeCache`
   1. Holds cached previous slices and interpolation metadata.

## 2. Public module APIs

1. `geometry_cov_rt.build_geometry(background_input) -> GeometryState`
2. `source_model_rt.build_sources(halo_input, astro_params, geometry) -> SourceState`
3. `continuum_rt_sn.solve_uv(prev_state, source_state, geometry, grid) -> RadiationState`
4. `continuum_rt_sn.solve_xray(prev_state, source_state, geometry, grid) -> RadiationState`
5. `lya_rt_ali.solve(prev_state, source_state, geometry, line_grid) -> RadiationState`
6. `continuum_rt_sn.compress_rates(rad_state, chemistry_state, geometry) -> RateBundle`
7. `chemistry_reion_cov.update_ionization(chem_state, rate_bundle, geometry, dt) -> ChemistryState`
8. `chemistry_reion_cov.update_temperature(therm_state, rate_bundle, geometry, dt) -> ThermalState`
9. `spin_temp_cov.update(spin_state, chem_state, therm_state, lya_state, geometry) -> SpinTempState`
10. `brightness_21cm_cov.compute(bright_state, chem_state, therm_state, spin_state, geometry, observer_dirs) -> BrightnessState`
11. `diagnostics_rt.compute_photon_budget(source_state, rad_state, chem_state, geometry, dt) -> PhotonBudgetState`
12. `reference_longchar_rt.solve_snapshot(snapshot_input) -> RadiationState or comparison report`

## 3. Required helper APIs

1. `geometry_cov_rt.make_direction_traversal(ordinate, grid, geometry)`.
2. `continuum_rt_sn.compute_group_opacity(cell, group, chemistry_state, geometry)`.
3. `continuum_rt_sn.interpolate_upwind_intensity(rad_state, cell, group, angle)`.
4. `lya_rt_ali.build_lambda_star(line_grid, geometry, coeff)`.
5. `spin_temp_cov.compute_xalpha(lya_state, geometry)`.
6. `brightness_21cm_cov.compute_xi21(geometry, observer_dir, cell)`.
7. `diagnostics_rt.assert_photon_conservation(photon_budget_state)`.

## 4. File layout freeze

1. `src/aniso_reion_rt/geometry_cov_rt.py`
2. `src/aniso_reion_rt/source_model_rt.py`
3. `src/aniso_reion_rt/continuum_rt_sn.py`
4. `src/aniso_reion_rt/lya_rt_ali.py`
5. `src/aniso_reion_rt/chemistry_reion_cov.py`
6. `src/aniso_reion_rt/spin_temp_cov.py`
7. `src/aniso_reion_rt/brightness_21cm_cov.py`
8. `src/aniso_reion_rt/diagnostics_rt.py`
9. `src/aniso_reion_rt/reference_longchar_rt.py`
10. `tests/test_geometry_cov_rt.py`
11. `tests/test_source_model_rt.py`
12. `tests/test_continuum_rt_sn.py`
13. `tests/test_lya_rt_ali.py`
14. `tests/test_chemistry_reion_cov.py`
15. `tests/test_spin_temp_cov.py`
16. `tests/test_brightness_21cm_cov.py`
17. `tests/test_diagnostics_rt.py`

## 5. Public API invariants

1. No chemistry update may accept source fields directly when a transported rate bundle is required.
2. No brightness computation may accept a scalar Hubble surrogate when geometry is available unless the caller explicitly requests the FLRW limit branch.
3. Lyα solves must expose their convergence status explicitly.
4. Photon-budget diagnostics must expose emitted, absorbed, escaped, and residual tallies explicitly.
5. Lightcone caching must never mutate authoritative coeval outputs in place.

## 6. Required diagnostics on returned objects

1. `status`.
2. `converged`.
3. `nan_guard_passed`.
4. `authoritative_path_tag`.
5. `photon_conservation_status`.
6. `geometry_branch`.
7. `notes`.
