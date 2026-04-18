# bass_py physics plot gallery

Structured PNG gallery of every physical quantity the bass_py codebase
can currently produce at the **post-LB-1 baseline** (species
backgrounds, FLRW geometry, HyRec-based recombination / tanh
reionization, Y-Block Bianchi shear evolution, lowell §11.3
tilt-boost kinematics, Friedmann closure, and parameter sweeps).

**Generator**: [`scripts/make_physics_gallery.py`](../../scripts/make_physics_gallery.py)
**Total**: 37 plots across 8 topics
**Regenerate**: `venv/bin/python scripts/make_physics_gallery.py`

All plots come from bass_py + the shipped HyRec fixture; no external
cosmology code is imported (per LB-0 external-code policy).

---

## 01 · Species background

Five-species (γ, ν, b, c, Λ) background evolution on the shared FLRW
η-grid from `bass.species` (LB-1).

| File | Description |
|---|---|
| [01_omega_evolution_log.png](01_species_background/01_omega_evolution_log.png) | Ω_s(z) = ρ_s/ρ_crit,0 across 24 decades — radiation/matter/Λ era shading, z_eq marker |
| [02_rho_invariance.png](01_species_background/02_rho_invariance.png) | \|ρ_s × a^{3(1+w_s)} / ⟨·⟩ − 1\| on log scale — confirms closed-form adiabats at float64 precision |
| [03_temperature_overlay.png](01_species_background/03_temperature_overlay.png) | T_γ(z), T_ν(z) = (4/11)^{1/3} T_γ, T_m(z) from HyRec — Compton decoupling band |
| [04_equality_crossover.png](01_species_background/04_equality_crossover.png) | ρ_γ+ρ_ν vs ρ_b+ρ_c around z_eq ≈ 3420 |
| [05_w_evolution.png](01_species_background/05_w_evolution.png) | Equation-of-state w_s(z) for each species |
| [06_rho_total_stack.png](01_species_background/06_rho_total_stack.png) | Stacked Ω_s(a)/Ω_tot(a) composition history |

## 02 · FLRW geometry

Scale factor, Hubble rate, and conformal distances from
`bass.species.FLRWBackgroundTable` (analytic quadrature, flat closure).

| File | Description |
|---|---|
| [01_scale_factor_vs_eta.png](02_flrw_geometry/01_scale_factor_vs_eta.png) | a(η) on log-log with η_*, η_eq, η_0 markers |
| [02_hubble_vs_a.png](02_flrw_geometry/02_hubble_vs_a.png) | H(a) with radiation / matter / de-Sitter asymptotes overlaid |
| [03_conformal_hubble.png](02_flrw_geometry/03_conformal_hubble.png) | 𝓗(η) = aH with the matter→Λ turnover minimum annotated |
| [04_eta_of_z.png](02_flrw_geometry/04_eta_of_z.png) | Conformal distance η_0 − η(z) with CMB LSS marker |
| [05_H0_sensitivity.png](02_flrw_geometry/05_H0_sensitivity.png) | η_0 and η_0 − η_* sweep over H_0 ∈ [60, 76] km/s/Mpc |
| [06_Omega_m_sensitivity.png](02_flrw_geometry/06_Omega_m_sensitivity.png) | η_0 and z_eq side-panel sweep over Ω_m |

## 03 · Recombination (HyRec fixture)

x_e(z), T_m(z), τ̇(z), κ(z), g(z) from the pre-computed HyRec-2
Planck-2018 table under `bass/recombination/fixtures/` (no reionization).

| File | Description |
|---|---|
| [01_x_e_full.png](03_recombination/01_x_e_full.png) | x_e(z) across z ∈ [1, 8000] with z_* and regime annotations |
| [02_T_m_vs_T_gamma.png](03_recombination/02_T_m_vs_T_gamma.png) | Two-panel: temperatures + T_m/T_γ ratio |
| [03_tau_dot.png](03_recombination/03_tau_dot.png) | Differential Thomson rate τ̇(z) |
| [04_kappa_cumulative.png](03_recombination/04_kappa_cumulative.png) | Cumulative optical depth κ(z) with κ=1 surface |
| [05_visibility_peak.png](03_recombination/05_visibility_peak.png) | g(z) visibility with peak position + amplitude annotation |
| [06_visibility_eta.png](03_recombination/06_visibility_eta.png) | g(η) zoom with FWHM ≈ 35 Mpc band |

## 04 · Reionization

Tanh-based reionization on top of the HyRec fixture, using
`bass.recombination.reionization.extend_table_with_reionization`.

| File | Description |
|---|---|
| [01_tanh_profile_sweep.png](04_reionization/01_tanh_profile_sweep.png) | x_e tanh profile for z_rei_H ∈ {6, 7, 7.67, 9, 11} |
| [02_combined_xe.png](04_reionization/02_combined_xe.png) | Full recomb + reion history overlaid on baseline HyRec |
| [03_tau_reion_sweep.png](04_reionization/03_tau_reion_sweep.png) | τ_reion vs z_rei_H with Planck 2018 1σ band |
| [04_HeII_on_off.png](04_reionization/04_HeII_on_off.png) | HeII second reionization effect on x_e |
| [05_visibility_with_reion.png](04_reionization/05_visibility_with_reion.png) | g(z) including reionization bump near z ≈ 7 |

## 05 · Bianchi shear evolution (Y-Block)

Non-FLRW shear history from `bass.background.einstein_bianchi.solve_bianchi_background`.

| File | Description |
|---|---|
| [01_Sigma2_decay_types.png](05_bianchi_shear/01_Sigma2_decay_types.png) | Σ²(a) + ratio-to-Kasner panel for Bianchi I / V / VII₀ |
| [02_sigma_pm_timeseries.png](05_bianchi_shear/02_sigma_pm_timeseries.png) | \|Σ_+\|, \|Σ_-\|(η) for three (σ_-/σ_+) ratios on log-log |
| [03_sigma_pm_phaseplane.png](05_bianchi_shear/03_sigma_pm_phaseplane.png) | (Σ_+, Σ_-) phase-plane trajectories |
| [04_a_minus_4_law.png](05_bianchi_shear/04_a_minus_4_law.png) | Σ² × a^n vs a for n ∈ {2, 3, 4, 5, 6} — power-law diagnostic |
| [05_seed_sweep.png](05_bianchi_shear/05_seed_sweep.png) | Σ²(a) for initial (σ/H) ∈ {1e-5, …, 5e-2} |

## 06 · Tilt boost (lowell §11.3 kinematics)

Non-perturbative Lorentz-boost factor `B(β, cosθ) = cosh β + sinh β (ê·v̂_e)`
— the direction-resolved visibility correction from LB-4 Layer A.

| File | Description |
|---|---|
| [01_gamma_e_vs_beta.png](06_tilt_boost/01_gamma_e_vs_beta.png) | γ_e(β) = cosh β vs the quadratic 1 + β²/2 truncation |
| [02_boost_factor_heatmap.png](06_tilt_boost/02_boost_factor_heatmap.png) | B(β, cosθ) 2-D heatmap with B=1 contour |
| [03_boost_directional_slice.png](06_tilt_boost/03_boost_directional_slice.png) | Forward/backward asymmetry B(cosθ) for 5 rapidities |
| [04_linear_vs_exact.png](06_tilt_boost/04_linear_vs_exact.png) | Two-panel: B_exact vs B_linear + (B_lin − B_exact)/B_exact error |

## 07 · Friedmann closure

Verification of the flat-ΛCDM closure Σ Ω_s = 1 and the residual
\|H²/H_0² − Σρ_s\| across the η-grid.

| File | Description |
|---|---|
| [01_residual_vs_eta.png](07_friedmann_closure/01_residual_vs_eta.png) | Max-envelope residual (absolute + relative) — relative stays at float64 precision ≈ 10⁻¹⁶ |
| [02_omega_sum_bar.png](07_friedmann_closure/02_omega_sum_bar.png) | Planck 2018 Ω_s(0) bar chart in linear + log scale, Σ = 1.00000000 |

## 08 · Parameter sweeps

Cosmological sensitivities: z_eq, η_0, τ_reion as functions of
(Ω_m, H_0, z_rei_H, Δz).

| File | Description |
|---|---|
| [01_z_eq_vs_Omega_m.png](08_parameter_sweeps/01_z_eq_vs_Omega_m.png) | z_eq = Ω_m/Ω_r − 1 sweep, fixed Ω_r |
| [02_eta_today_vs_H0.png](08_parameter_sweeps/02_eta_today_vs_H0.png) | η_0 vs H_0 for Ω_m ∈ {0.28, 0.3153, 0.35} |
| [03_tau_reion_vs_z_rei.png](08_parameter_sweeps/03_tau_reion_vs_z_rei.png) | τ_reion vs (z_rei_H, Δz) with Planck 2018 band |

---

## Regenerating specific topics

```bash
# Full gallery (37 plots, ~15 s)
venv/bin/python scripts/make_physics_gallery.py

# Only one topic
venv/bin/python scripts/make_physics_gallery.py --only 03_recombination

# Enumerate catalog
venv/bin/python scripts/make_physics_gallery.py --list
```

---

## Physics provenance

All plots source their data from **bass_py internal machinery only**:

- Species backgrounds → `bass.species` (LB-1)
- FLRW quadrature → `bass.species.build_flrw_background_table`
- Bianchi shear → `bass.background.einstein_bianchi.solve_bianchi_background` (Y-Block)
- Recombination → HyRec-2 Planck-2018 fixture CSV (`bass.recombination.recombination_ingest`)
- Reionization → tanh machinery (`bass.recombination.reionization`)
- Constants → SSOT via `htt.htt.core.ssot.C` + Kolb-derived Ω_γ,0, Ω_ν,0

No external cosmology oracle (CAMB/CLASS/etc.) is invoked. This is
enforced by the LB-0 guard test `bass.validation.test_external_code_policy`.
