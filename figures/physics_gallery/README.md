# bass_py physics plot gallery

Structured PNG gallery of every physical quantity the `htt/bass` + `htt/tsc`
codebase can currently produce at the **post-LB-2a baseline** (species
backgrounds, FLRW geometry, HyRec-based recombination / tanh
reionization, Y-Block Bianchi shear evolution, lowell §11.3
tilt-boost kinematics, Friedmann closure, parameter sweeps, and the
PSTF multipole hierarchy algebra shipped in LB-2a).

**Location:** `figures/physics_gallery/` (sibling of `figures/paper/`
and `figures/preliminary/`; moved here from `plots/physics_gallery/`
during the 2026-04-19 figure-tree consolidation).
**Generator**: [`scripts/make_physics_gallery.py`](../../scripts/make_physics_gallery.py)
**Total**: 50 plots across 11 rendered topics + 3 reserved placeholder
topics
**Regenerate**: `venv/bin/python scripts/make_physics_gallery.py`
**Cadence**: regenerated at the end of every LB-N phase; see the
[phase-boundary hook](../../.claude/hooks/check_phase_boundary_audit.py)
which reminds to refresh before any `LB-N` commit lands.

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

## 09 · PSTF multipole hierarchy (LB-2a)

Storage-layer and orthogonal-Bianchi-active subset of the 1+3
covariant PSTF multipole hierarchy implemented in
[`bass/hierarchy/`](../../bass_py/bass/hierarchy/). Every panel sources
its numbers from the shipped code — basis tensors ``Q_ℓ``, the nine-
term prefactor table, and the ``T1/T8/T9`` action on realistic
backgrounds.

| File | Description |
|---|---|
| [01_stf_dim_vs_symmetric.png](09_pstf_hierarchy/01_stf_dim_vs_symmetric.png) | dim(PSTF_ℓ) = 2ℓ+1 vs dim(Sym_ℓ) = (ℓ+1)(ℓ+2)/2 for ℓ=0..8; shaded region is the kept-trace degrees of freedom |
| [02_roundtrip_precision.png](09_pstf_hierarchy/02_roundtrip_precision.png) | Packed ↔ full-tensor round-trip ‖c − c_rt‖_∞ vs ℓ with the ε_mach × 3^ℓ reference line |
| [03_term_prefactors.png](09_pstf_hierarchy/03_term_prefactors.png) | Analytic prefactors for T1, T3, T7, T8, T9 as functions of ℓ |
| [04_stf_basis_ell2_tensors.png](09_pstf_hierarchy/04_stf_basis_ell2_tensors.png) | Five orthonormal STF basis tensors at ℓ=2 as 3×3 heatmaps (QR-ordered) |
| [05_T9_shear_quadrupole.png](09_pstf_hierarchy/05_T9_shear_quadrupole.png) | T9 at ℓ=2 — ‖T9‖_F = 4\|Σ_+\|\|Π_0\| sweep + decomposition in the QR basis |
| [06_T8_shear_spectrum.png](09_pstf_hierarchy/06_T8_shear_spectrum.png) | ‖T8‖_F acting on a unit-norm random PSTF Π_ℓ, for ℓ=1..8 |
| [07_T1_damping_history.png](09_pstf_hierarchy/07_T1_damping_history.png) | (4/3)Θ(η) expansion damping rate from BBN to today + action on a unit Π_2 |
| [08_shear_injection_over_time.png](09_pstf_hierarchy/08_shear_injection_over_time.png) | Bianchi I Σ_+(η) history → proper σ_+(η) = Σ_+/a → injected ‖T9‖ at ℓ=2 with Π_0 = 1 |

## 10 · Thomson collision + tilted visibility (LB-4)

Thomson collision coefficients (Ma-Bertschinger 1995 eq 63 /
Zaldarriaga-Seljak 1997 eq 17), TCA-limit algebraic balance, and the
lowell §11.3 direction-resolved ``Γ̃_T(η, e) = Γ_T(η) × B(η, e)``
wrapper with non-perturbative Lorentz boost ``B = cosh β + sinh β (ê·v̂)``.

| File | Description |
|---|---|
| [01_thomson_coefficient_spectrum.png](10_collision_and_visibility/01_thomson_coefficient_spectrum.png) | K_ℓ/Γ_T self-coupling (−1, −9/10, −1, …) and polter cross-coupling for temperature + E-mode |
| [02_tca_equilibrium_convergence.png](10_collision_and_visibility/02_tca_equilibrium_convergence.png) | TCA-limit (Θ_2, E_2) ∝ 1/Γ_T scaling; polter ratio E_2/Θ_2 → −√6/4 at S_E → 0 |
| [03_gamma_tilde_direction_asymmetry.png](10_collision_and_visibility/03_gamma_tilde_direction_asymmetry.png) | Layer A: forward/back/side Γ̃_T(η, e) at β=0.3 through recombination + direction/scalar ratio levels matching γ(1±β), γ |

## 11 · Unified LB-5 integrator

End-to-end ``LowellBianchiIntegrator`` trajectories combining the
background evolution, PSTF multipole hierarchy, E-mode tower, and
reduced neutrino fluid in a single ``scipy.integrate.solve_ivp``
call, plus a diagnostic of the TCA algebraic-dispatch activation
window.

| File | Description |
|---|---|
| [01_unified_trajectory_bianchi_I.png](11_integrator/01_unified_trajectory_bianchi_I.png) | ``a(η), Σ_±(η), Π_2[m=0](η), E_2[m=0](η)`` along a Type I flat trajectory with seeded Π_2 — shows Thomson damping + polter-driven E_2 transient |
| [02_tca_activation_window.png](11_integrator/02_tca_activation_window.png) | ``Γ_T / H`` across the Planck-2018 HyRec history (never crosses threshold) vs a synthetic high-``Γ_T`` override that activates the dispatch on 531/600 grid points |

## 14 · Observer frame (FB-8 placeholder)

FB-META-8 is skeleton-only, so no observer-frame PNGs are rendered yet.
The reserved topic directory
[14_observer_frame/](14_observer_frame/README.md) documents the future
target outputs and records this phase as an intentional gallery no-op.

## 15 · Massive neutrino (FB-9 placeholder)

FB-META-9 is skeleton-only, so no massive-neutrino PNGs are rendered
yet. The reserved topic directory
[15_massive_neutrino/](15_massive_neutrino/README.md) documents the
future target outputs and records this phase as an intentional gallery
no-op.

## 16 · Inference corner (FB-11 placeholder)

FB-META-11 is skeleton-only, so no inference PNGs are rendered yet. The
reserved topic directory
[16_inference_corner/](16_inference_corner/README.md) documents the
future target outputs and records this phase as an intentional gallery
no-op.

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
