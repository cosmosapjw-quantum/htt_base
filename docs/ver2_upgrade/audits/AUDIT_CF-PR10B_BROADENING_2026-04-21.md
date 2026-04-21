# AUDIT_CF-PR10B_BROADENING_2026-04-21

## Scope

- `htt/bass/forward/ver2_solver_output.py`
- `htt/bass/los/ver2_source_propagator.py`
- targeted tests under `htt/bass/{forward,los,runtime,recombination,observational}`

## Purpose

Close the next DAG-safe carry-forward items after `CF-PR10A`:

1. make the live Tier-B source builder carry the PR-10 combined polarization source rather than a mislabeled raw temperature quadrupole slot,
2. expose executable reionization on/off low-`ell` source diagnostics on the native path,
3. narrow the old generic non-Type-I propagator bucket into algebra-derived bounded families without reopening the exact PR-15 problem.

## Static audit

### Finding A — source-builder quantity mismatch

- Previous live `source_builder` emitted `pi_m*` from `result.pi_ell_m(2,m)`.
- In the live path this is the temperature quadrupole slot, not the PR-10 combined Thomson source
  `Π = Θ_2 - √6 E_2`.
- The LOS projector consumes `sources.pi` as the polarization source operand.

### Repair A

- `pi_m*` now carries the actual combined polter `Θ_2 - √6 E_2`.
- The builder also exposes explicit `theta_2_*`, `E_2_*`, and `gpi_*` channels.
- `source_builder_scope` is renamed from the old quadrupole wording to
  `theta0_plus_combined_polter_visibility_*`.

### Finding B — reionization was present in visibility but not surfaced in live source diagnostics

- `CF-PR10A` fixed visibility normalization and event markers.
- The native output still did not prove that homogeneous reionization altered the low-`ell` source on the live path.

### Repair B

- Native and Lowell neutral outputs now record:
  - `visibility_reionization_mode`
  - `visibility_reionization_detected`
  - `visibility_tau_reion`
  - `source_builder_low_z_probe_available`
  - `source_builder_low_z_gpi_m0`
  - `source_builder_visibility_peak_gpi_m0`
- Targeted regression compares `apply_default_reionization=False` vs default Planck-2018 reionized species and confirms the low-`z` weighted polarization source increases.

### Finding C — all non-Type-I structures still shared one bounded propagator family

- This was honest but too coarse for the current tetrad/algebra-first phase.
- The code already owns class-A/class-B structure constants and axis/twist metadata.

### Repair C

- Added algebra-derived bounded families:
  - `class_a_axis_matrix_approx`
  - `class_a_helical_matrix_approx`
  - `class_a_semisimple_matrix_approx`
  - `class_a_compact_matrix_approx`
  - `class_b_open_matrix_approx`
  - `class_b_twist_axis_matrix_approx`
  - `class_b_helical_matrix_approx`
- Default non-Type-I Tier-B selection now comes from algebra data rather than one generic bucket.
- This is still bounded and approximate; it does **not** claim full PR-15 exact closure.

## Verification

Executed:

```bash
venv/bin/python -m py_compile \
  htt/bass/forward/ver2_solver_output.py \
  htt/bass/los/ver2_source_propagator.py \
  htt/bass/forward/test_ver2_solver_output.py \
  htt/bass/los/test_ver2_source_propagator.py \
  htt/bass/runtime/test_ver2_tier_b_execution.py

PYTHONPATH=htt:htt/src venv/bin/python -m pytest \
  htt/bass/forward/test_ver2_solver_output.py \
  htt/bass/los/test_ver2_source_propagator.py \
  htt/bass/runtime/test_ver2_tier_b_execution.py \
  htt/bass/recombination/test_ver2_history_visibility.py -q

PYTHONPATH=htt:htt/src venv/bin/python -m pytest \
  htt/bass/test_ver2_public_surface.py \
  htt/bass/observational/test_ver2_observable_atlas.py -q
```

Results:

- packet-local regression: `32 passed`
- public/observational regression: `8 passed`
- only known warning: recombination table early-`z` coverage warning

## Remaining carry-forward

- non-Type-I exact propagator closure remains open
- off-axis generic FB-5.2 transport remains open
- direction-resolved microphysics beyond homogeneous reionization remains open
