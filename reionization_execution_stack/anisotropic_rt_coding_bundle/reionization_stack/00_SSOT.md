# 00. SSOT — Anisotropic Reionization RT

## 0. Status sentence

1. This file is the single source of truth for authoritative-path identity, workflow invariants, and forbidden shortcuts.

## 1. Canonical solver identity

1. Solver name: `Anisotropic-Reionization-RT`.
2. Canonical authoritative path: `S_N + short-characteristics + ALI for Lyα + local chemistry + geometry-aware brightness`.
3. Canonical reference path: `long-characteristics` on selected benchmark snapshots.
4. Canonical diagnostic path: excursion-set or photon-budget compression diagnostics only.
5. Canonical forbidden path: pure excursion-set barrier as the authoritative ionization solver.

## 2. Canonical workflow identity

1. The workflow is `ICs -> density/velocity/source fields -> UV/X-ray/Lyα transport -> chemistry/heating -> spin temperature -> δT_b -> lightcone output`.
2. This workflow is preserved even when the transport kernel is replaced.
3. `ionize_box`-style logic is replaced by an authoritative retarded directional photon-budget update law.
4. `compute_spin_temperature`-style logic is preserved as a module boundary but fed by transport-resolved radiation fields.

## 3. Canonical geometry conventions

1. Metric signature is `(-,+,+,+)`.
2. Primary congruence is the baryon rest frame `u^a`.
3. Radiation transport uses a tetrad basis built from the local geometry state.
4. The line-of-sight 21-cm expansion scalar is `Xi_21 = s^a s^b ∇_a u_b`.
5. Orthogonal and tilted branches must be explicit and must never be hidden inside a scalar `H(z)` surrogate.

## 4. Canonical physics invariants

1. Ionization and heating rates must be computed from transported radiation fields.
2. Lyα pumping must not be reduced to a fixed local table when the authoritative path is active.
3. Photon conservation is a first-class diagnostic and acceptance gate.
4. `δT_b` must use geometry-aware line-of-sight expansion, not only FLRW-style `H + ∂_r v_r` unless that is explicitly the chosen limit branch.
5. The production path may compress outputs after transport, but not before authoritative rate construction.

## 5. Canonical module ownership

1. `geometry_cov_rt` owns geometry and ray coefficients.
2. `source_model_rt` owns emissivity generation from halos or source fields.
3. `continuum_rt_sn` owns UV/X-ray transport.
4. `lya_rt_ali` owns Lyα scattering-heavy transport and ALI.
5. `chemistry_reion_cov` owns ionization fractions, recombination counters, and thermal updates.
6. `spin_temp_cov` owns `x_alpha`, `x_c`, `T_s`.
7. `brightness_21cm_cov` owns optical depth and `δT_b`.
8. `reference_longchar_rt` owns validation-only long-characteristics solutions.

## 6. Canonical state vector

1. Global state is `{geometry, source_fields, I_uv, I_x, I_lya, xHII, xHeII, xHeIII, Nrec, Tk, Ts, diagnostics}`.
2. Radiation state may use streaming buffers for continuum sectors, but Lyα state is authoritative and persistent.
3. Any subgrid sink or self-shielding model must be explicit in state or parameters, not hidden inside opacity kernels.

## 7. Canonical forbidden claims

1. `Photon conservation can be repaired later by a fit.` is forbidden.
2. `M1 is equivalent to ray transport here.` is forbidden.
3. `Geometry only matters in postprocessing δT_b.` is forbidden.
4. `Excursion-set barrier is still the authoritative ionization kernel.` is forbidden.
5. `Tilt is a cosmetic boost that can be added after the transport solve.` is forbidden.
