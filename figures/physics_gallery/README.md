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
**Total**: 88 plots across 15 rendered topics + 2 reserved placeholder
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
| [04_thomson_beta_sweep_Dl.png](10_collision_and_visibility/04_thomson_beta_sweep_Dl.png) | FB-4.1 Layer-B TT proxy ratio for β_e ∈ {0, 0.1, 0.3} |
| [05_bb_from_tilted_lens_e.png](10_collision_and_visibility/05_bb_from_tilted_lens_e.png) | FB-4.2 Layer-B BB/EE amplitude ratio over β_e ∈ [0, 0.3], ℓ ∈ [2, 30] |
| [06_doppler_second_order_residual.png](10_collision_and_visibility/06_doppler_second_order_residual.png) | FB-4.3 Layer-B quadratic Doppler residual (full-linear)/full at β_e = 0.1 |

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
| [03_fb11_classA_typeI_kasner_trace.png](11_integrator/03_fb11_classA_typeI_kasner_trace.png) | FB-1.1 Type I Kasner: Σ×a² + σ×a³ invariants + ρ_σ ∝ 1/a⁶ decay |
| [04_fb11_classA_typeII_WE_attractor.png](11_integrator/04_fb11_classA_typeII_WE_attractor.png) | FB-1.1 Type II Wainwright-Ellis Table 11.1 axisymmetric source, including Σ_- ≡ 0 |
| [05_fb11_classA_typeVI0_WE_attractor.png](11_integrator/05_fb11_classA_typeVI0_WE_attractor.png) | FB-1.1 Type VI₀ Wainwright-Ellis Table 11.1 e(1,1) source with the S_- sign pattern |
| [06_fb11_classA_typeVII0_decay.png](11_integrator/06_fb11_classA_typeVII0_decay.png) | FB-1.1 Type VII₀ plane-wave line + asymmetric source |
| [07_fb12_classA_typeVIII_WE_attractor.png](11_integrator/07_fb12_classA_typeVIII_WE_attractor.png) | FB-1.2 Type VIII sl(2,ℝ) source with the S_- sign flip in (N₂² − N₃²) |
| [08_fb12_classA_typeIX_recollapse_trace.png](11_integrator/08_fb12_classA_typeIX_recollapse_trace.png) | FB-1.2 Type IX so(3) source + recollapse event smoke trajectory |
| [09_fb13_classB_typeIV_WE_source.png](11_integrator/09_fb13_classB_typeIV_WE_source.png) | FB-1.3 Type IV Class-B source, axisymmetric S_- = 0, and the A/N₃ crossover |
| [10_fb13_classB_typeVIh_WE_attractor.png](11_integrator/10_fb13_classB_typeVIh_WE_attractor.png) | FB-1.3 Type VI_h Class-B attractor with h-dependent A² prefactor 1/(1+|h|) |
| [11_fb13_classB_typeVIIh_spiral.png](11_integrator/11_fb13_classB_typeVIIh_spiral.png) | FB-1.3 Type VII_h Wainwright-Ellis + Pontzen-Challinor spiral rotation in (Σ_+, Σ_-) |
| [12_fb13_classB_typeV_shear_zero.png](11_integrator/12_fb13_classB_typeV_shear_zero.png) | FB-1.3 Type V shear-specific source identically zero with the Ellis Σ×a² invariant |
| [13_fb14_anisotropic_3curvature_per_type.png](11_integrator/13_fb14_anisotropic_3curvature_per_type.png) | FB-1.4 exit gallery: ³R_ab^aniso eigen-structure across all 11 types + FLRW |

## 14 · Observer frame (FB-8)

Observer-frame post-processing on top of the FB-7 cosmological-frame
likelihood: aligned aberration kernel, diagonal-spectrum response,
harmonic mixing, and the local-boost vs global-tilt discriminator
coverage check.

| File | Description |
|---|---|
| [01_kernel_heatmap_1p23e-3.png](14_observer_frame/01_kernel_heatmap_1p23e-3.png) | FB-8.2 aligned observer-frame aberration kernel at the Sun-dipole speed, shown both as the full matrix and the $10^3(K-I)$ residual |
| [02_Cl_ratio_before_after.png](14_observer_frame/02_Cl_ratio_before_after.png) | FB-8.3 synthetic diagonal-spectrum response $C_\ell^{\rm obs}/C_\ell^{\rm frame}$ at $\beta_{\rm obs}=1.23\times10^{-3}$ |
| [03_alm_mixing_demo.png](14_observer_frame/03_alm_mixing_demo.png) | FB-8.3 single synthetic $a_{\ell m}$ map before and after the linear observer-frame mixing kernel |
| [04_discriminator_coverage.png](14_observer_frame/04_discriminator_coverage.png) | FB-8.5 empirical-PIT coverage histograms for $\Lambda(d;H_{\rm obs},H_{\rm cosmo})$ under both truth hypotheses, including the KS-uniformity gate |

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

## 17 · Perturbation k-modes (FB-5)

Mode-resolved perturbation validation on the shared low-$\ell$ CAMB
Planck-2018 oracle grid.

| File | Description |
|---|---|
| [01_harmonic_modes_per_type.png](17_perturbation_k_modes/01_harmonic_modes_per_type.png) | FB-5.1 representative harmonic-mode spectrum and family per Bianchi type |
| [02_adiabatic_seed_ic.png](17_perturbation_k_modes/02_adiabatic_seed_ic.png) | FB-5.3 CAMB-regular adiabatic seed amplitudes versus k |
| [03_k_zero_limit_recovery.png](17_perturbation_k_modes/03_k_zero_limit_recovery.png) | FB-5.4 recovery of the k→0 seed prefix against the LB-6 zero-IC anchor |
| [04_tilted_boost_seed_rule.png](17_perturbation_k_modes/04_tilted_boost_seed_rule.png) | FB-5.6 temperature and E-mode m=0 slices before and after the axisymmetric boost |
| [05_Dl_TT_vs_camb_per_k.png](17_perturbation_k_modes/05_Dl_TT_vs_camb_per_k.png) | FB-5.7 Type-I D_ℓ^TT proxy against the CAMB Planck-2018 oracle for four k values |

## 18 · 22-config regression (FB-6)

Phase-FB-6 regression summary for the explicit 22-row type×tilt matrix,
the named continuity limits, and the CAMB / Pontzen-Challinor oracle
cross-checks.

| File | Description |
|---|---|
| [plot_18_01_22_config_sigma2_decay.png](18_22_config_regression/plot_18_01_22_config_sigma2_decay.png) | FB-6.1 Σ²(η) decay across the full 22-row type × tilt regression matrix |
| [plot_18_02_cross_type_limits_grid.png](18_22_config_regression/plot_18_02_cross_type_limits_grid.png) | FB-6.2 five-panel named cross-type continuity-limit convergence grid |
| [plot_18_03_Dl_TT_11_types_vs_camb.png](18_22_config_regression/plot_18_03_Dl_TT_11_types_vs_camb.png) | FB-6.3 orthogonal-branch D_ℓ^TT overlays against the shared CAMB Planck-2018 oracle |
| [plot_18_04_pontzen_challinor_shape_match.png](18_22_config_regression/plot_18_04_pontzen_challinor_shape_match.png) | FB-6.3 Pontzen-Challinor VII_h and IX qualitative shape overlays |

## 19 · HTT likelihood (FB-7)

Line-of-sight propagation, anisotropic covariance, HTT P0-triad
resolution, cosmological-frame direction likelihood, and the
Planck-2018 FLRW-limit evidence summary for the FB-7 stack.

| File | Description |
|---|---|
| [plot_19_01_los_propagator_heatmap.png](19_htt_likelihood/plot_19_01_los_propagator_heatmap.png) | FB-7.1 LOS propagator drift heatmap across (k, ℓ) for Type VII_h |
| [plot_19_02_offdiag_covariance_IX.png](19_htt_likelihood/plot_19_02_offdiag_covariance_IX.png) | FB-7.2 Bianchi-IX off-diagonal TT covariance slice in the m=0 block |
| [plot_19_03_htt_p0_triad.png](19_htt_likelihood/plot_19_03_htt_p0_triad.png) | FB-7.3 three-panel HTT P0-triad resolution: prior, tangency, resolved axis |
| [plot_19_04_direction_likelihood_contours.png](19_htt_likelihood/plot_19_04_direction_likelihood_contours.png) | FB-7.4 cosmological-frame directional log-likelihood over Bianchi-axis longitude and latitude |
| [plot_19_05_lnB_11types_vs_FLRW.png](19_htt_likelihood/plot_19_05_lnB_11types_vs_FLRW.png) | FB-7.5 Planck-2018 ln B summary across all 11 Bianchi types versus FLRW |

---

## Regenerating specific topics

```bash
# Full gallery
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
