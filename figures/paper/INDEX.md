# Paper figure bundle

Paper-quality figures rendered from `htt/bass` + `htt/tsc` + `htt/mio`
code and the `dl_pipeline/obs_bundle/` observational dataset, ready
for attachment to `project/00_manuscript/`. All figures are PNG + PDF
at 300 dpi (Okabe-Ito palette, single/double-column widths from
`htt.core.plot_style`). Each figure has a matching `.caption.txt`.

Siblings under `figures/`:

- `paper/` — this tree (manuscript-grade figures with captions)
- `preliminary/` — TIER A/B/C/D preliminary figures (`make_preliminary_figures.py`)
- `physics_gallery/` — 50-plot physics diagnostic gallery (`make_physics_gallery.py`)

## Generators

| Script | Purpose | Figure count |
| --- | --- | --- |
| `scripts/make_paper_figures.py` | First wave — ch02 a–e, ch05 a–d, ch06 a–g, ch07 a–i, ch08 a–c | ~29 |
| `scripts/make_preliminary_figures.py` | Tier A (MES bounds, Colin β, Route B sentinel); copied into ch04/ch05/ch07 | 5 |
| `scripts/make_additional_figures.py` | Second wave — ch03 framework, ch04 bounds, ch05/ch06/ch07 TSC diagnostics, ch12 MIO | ~30 |
| `scripts/make_more_figures.py` | Third wave — ch02 f–j, ch03c, ch07j–l, ch08d–e, ch09 a–d, ch11a, ch12e | ~20 |
| `scripts/make_third_wave_figures.py` | Fourth wave — ch02k/l, ch05h/i/j, ch06n, ch08f, ch12 regenerations | 10 |

## Contents by chapter

### ch02 — Cosmic dipole anomaly (observational motivation) — 12 figs

| File | Source |
| --- | --- |
| `fig_ch02a_planck_tt_spectrum` | Planck PR3 TT binned + best-fit ΛCDM |
| `fig_ch02b_planck_polarization_grid` | TT/TE/EE/BB 4-panel |
| `fig_ch02c_cmb_map_commander` | Planck Commander NSIDE=16 Mollweide |
| `fig_ch02d_dipole_scenarios` | ε₁ and β bar chart across S0–S3 |
| `fig_ch02e_cf4_velocity_field` | CF4 reconstruction \|v⃗\| vs distance |
| `fig_ch02f_multi_experiment_tt` | Planck PR3 ∪ ACT DR6 TT overlay + residuals |
| `fig_ch02g_planck_polarization_ee_te` | Planck PR3 EE + TE vs ΛCDM |
| `fig_ch02h_planck_lensing_bandpowers` | Planck PR3 φφ SMICA bandpowers + CAMB |
| `fig_ch02i_planck_tt_residuals` | Planck PR3 TT pulls vs Planck 2018 best-fit |
| `fig_ch02j_h0_depth_tension` | H₀ tension vs peculiar-flow depth |
| `fig_ch02k_planck_tt_full_vs_binned` | Unbinned ell-by-ell TT + binned overlay + peaks |
| `fig_ch02l_cf4_bulk_flow_depth` | CF4 8-point bulk-flow \|v_r\| vs SG depth |

### ch03 — Framework (identified-vs-reporting split) — 3 figs

| File | Source |
| --- | --- |
| `fig_ch03a_scale_hierarchy` | Hubble radius, peculiar Jeans, sound horizon, d_S vs survey reach |
| `fig_ch03b_three_layer_ontology` | schematic x → Q = x/x_max → Π(q*) chain |
| `fig_ch03c_frame_hierarchy` | Observer-frame (O/G/M/GM) schematic |

### ch04 — Bianchi bounds (MES hierarchy) — 5 figs

| File | Source |
| --- | --- |
| `fig_MES_three_bounds` | Bσ > Bω > Bu̇ with S1/S2a/S2c markers |
| `fig_sigma_omega_contour` | σ and ω bounds in ε₁ |
| `fig_sigma_accel_contour` | σ and u̇ bounds in ε₁ |
| `fig_ch04d_type_by_type_bounds` | Bσ/Bω/Bu̇ per Bianchi type |
| `fig_ch04e_shear_source_landscape` | (n₁, n₃) S± landscape for 4 Class-A types |

### ch05 — T_eff / tilt boost kinematics — 11 figs

| File | Source |
| --- | --- |
| `fig_ch05a_tilt_boost_heatmap` | B(β, cos θ) heatmap + contours |
| `fig_ch05b_boost_directional_slice` | B(cos θ) for five β |
| `fig_ch05c_boost_linear_vs_exact` | Linearisation error (log-log) |
| `fig_ch05d_tilted_visibility` | Tilted Thomson visibility |
| `fig_ch05e_laguerre_moments` | I_n(ξ, η) BE/FD/MB moments |
| `fig_ch05f_xi_moment_ratios` | I_{n+1}/I_n moment ratios |
| `fig_ch05g_boost_mixing_matrix` | Prop-5 B_{ℓℓ'}(v) mixing matrix log-magnitude |
| `fig_ch05h_laguerre_family_portrait` | L_s^α(x) 5×4 family, weight overlay, norms |
| `fig_ch05i_doppler_boost_delta_eps` | δε_ℓ(β) kernel + R_σ^boost with VN-04 markers |
| `fig_ch05j_teff_mes_VN04_scenarios` | 2-layer R_σ decomposition at S1/S2/S3 |
| `fig_colin_beta` | Colin+2025 β_SNe(z) vs CF4 band |

### ch06 — Pipeline: FLRW background, recombination, transport — 14 figs

| File | Source |
| --- | --- |
| `fig_ch06a_species_omega` | Ω_s(z) for γ, ν, b, c, Λ |
| `fig_ch06b_hubble_geometry` | H(a) + η(z) |
| `fig_ch06c_recombination_panel` | x_e, T_m/T_γ, τ̇, g + κ |
| `fig_ch06d_reionization_tau_sweep` | τ vs z_rei,H with Planck band |
| `fig_ch06e_closure_error_vs_L` | Closure truncation error |
| `fig_ch06f_pstf_roundtrip` | PSTF σ ↔ Σ roundtrip diagnostic |
| `fig_ch06g_sigma_Sigma_conversion` | σ/H → Σ_± conversion curves |
| `fig_ch06h_route_b_mm_chart` | D_2(Σ²) Michaelis-Menten SSOT mirror + sentinel |
| `fig_ch06i_tca_conditioning` | TCA collision matrix determinant + κ |
| `fig_ch06j_lebedev_exactness` | Lebedev quadrature exactness certificate |
| `fig_ch06k_polter_recoupling_structure` | Polter ℓ=2 damping + source vector modification |
| `fig_ch06l_desi_y1_nz` | DESI Y1 weighted n(z) for 3 tracers |
| `fig_ch06m_bb_polarization_constraints` | Planck PR3 BB+EB low-ℓ vs CAMB lensed BB |
| `fig_ch06n_desi_sky_footprint` | DESI Y1 RA/Dec Mollweide (3 tracers × NGC+SGC) |

### ch07 — Main results (Bianchi shear, Route B) — 15 figs

| File | Source |
| --- | --- |
| `fig_ch07a_sigma_decay_types` | Σ²(a) for I / V / VII₀ |
| `fig_ch07b_sigma_phase_plane` | \|Σ±\|(a) + (Σ₊, Σ₋) phase plane |
| `fig_ch07c_sigma_a4_law` | Conformal shear a⁻⁴ diagnostic |
| `fig_ch07d_sigma_seed_sweep` | Σ²(a) for 5 initial sigma/H |
| `fig_ch07e_thomson_coefficients` | PSTF Thomson closure coefficients |
| `fig_ch07f_tca_polter_ratio` | Π/Θ₂ tight-coupling ratio |
| `fig_ch07g_ellis_kasner_invariants` | Kasner ε invariants diagnostic |
| `fig_ch07h_bianchi_class_a_attractors` | Σ_+(a) for Class A types |
| `fig_ch07i_hierarchy_term_prefactors` | 9-term PSTF hierarchy prefactors |
| `fig_ch07j_mes_ceilings_hierarchy` | Σ²_max / W²_max / A²_max along ε₁ |
| `fig_ch07k_entropy_invariants` | s/n and s/ρ for BE/FD/MB vs η |
| `fig_ch07l_gram_admissibility` | Teff Gram eigenvalues + κ(η) |
| `fig_ch07m_boost_order_convergence` | Prop-3 boost residual vs v; orders 1, 2 |
| `fig_ch07n_tilt_history_trajectory` | β(z), v_tilt(z) for 3 scaling ansätze (scenario study) |
| `fig_route_b_sentinel` | D₂(Σ²) Michaelis-Menten curve (Tier-A) |

### ch08 — Observational robustness — 6 figs

| File | Source |
| --- | --- |
| `fig_ch08a_desi_sky_coverage` | DESI Y1 NGC footprint + n(z) |
| `fig_ch08b_planck_lensing` | Planck PR3 φφ bandpowers + CAMB |
| `fig_ch08c_cf4_delta_vs_distance` | CF4 density contrast δ |
| `fig_ch08d_commander_minus_smica` | Planck component-separation residual map |
| `fig_ch08e_desi_y1_sky_maps` | DESI Y1 BGS/LRG/QSO Mollweide sky maps |
| `fig_ch08f_flrw_bessel_los_kernels` | j_ℓ(kr), P^E_ℓ(kr) for ℓ ∈ {2, 10, 50, 200} |

### ch09 — Discussion — 4 figs

| File | Source |
| --- | --- |
| `fig_ch09a_fbayes_gaussian_cross_check` | F_Bayes TSC MC vs closed-form agreement |
| `fig_ch09b_dipole_surveys_compilation` | Cross-survey β/ε₁ compilation |
| `fig_ch09c_depth_tomography` | β(z) depth-tomography summary |
| `fig_ch09d_quadrupole_axis_alignment` | Quadrupole-dipole alignment probability |

### ch11 — Error hierarchy — 1 fig

| File | Source |
| --- | --- |
| `fig_ch11a_error_hierarchy` | Five-level error-budget cascade (schematic, indicative amplitudes) |

### ch12 — MIO observatory results — 8 figs (5 unique + 3 regenerated)

| File | Source | Status |
| --- | --- | --- |
| `fig_ch12a_directional_coherence` | 5-probe Mollweide + resultant + χ² + p_iso (HJ-02a) | canonical |
| `fig_ch12b_redshift_drift_axes` | Synthetic-probe rendering (legacy) | superseded |
| `fig_ch12b_redshift_drift_real_probes` | SSOT probes only, no synthetic fillers | **current** |
| `fig_ch12c_sky_coverage_fsky` | Analytical f_sky demo (legacy) | superseded |
| `fig_ch12c_sky_coverage_real_mask` | Real Planck temp/pol masks, healpy-computed | **current** |
| `fig_ch12d_hj01_extraction_demo` | Fully synthetic K_ℓ + C_ℓ (legacy) | superseded |
| `fig_ch12d_hj01_extraction_real_backbone` | Real Planck TT residual + placeholder K_ℓ | **current** |
| `fig_ch12e_pairwise_separations` | 5×5 angular separation matrix | canonical |

## Regenerating

```bash
# Preliminary Tier A (MES bounds, Colin β, Route B sentinel)
venv/bin/python scripts/make_preliminary_figures.py --tier A

# First wave (ch02 a–e, ch05 a–d, ch06 a–g, ch07 a–i, ch08 a–c)
venv/bin/python scripts/make_paper_figures.py

# Second wave (ch03, ch04d/e, ch05e–g, ch06h–m, ch07j–l, ch12 a–e)
venv/bin/python scripts/make_additional_figures.py

# Third wave (ch02 f–j, ch03c, ch07j–l, ch08d–e, ch09 a–d, ch11a)
venv/bin/python scripts/make_more_figures.py

# Fourth wave (ch02k/l, ch05h–j, ch06n, ch08f, ch12 regenerations)
venv/bin/python scripts/make_third_wave_figures.py

# Physics diagnostic gallery (sibling tree)
venv/bin/python scripts/make_physics_gallery.py
```

Each `--list` flag enumerates the script's registered figure IDs, and
`--only <id>` renders a single figure for iteration. Every figure
writes `<name>.png`, `<name>.pdf`, and `<name>.caption.txt` drafted
for direct inclusion under `project/00_manuscript/`.

## Figure status — mock / placeholder taxonomy

Figures are categorised by **what would change when the bass_py low-ℓ
Boltzmann solver W10-02 V-gate is signed**. Cross-checked against
`docs/audits/AUDIT_PHASE_IND_TRACKS_W10_2026-04-19.md`,
`AUDIT_PHASE_IND_TRACKS_W11_2026-04-19.md`,
`AUDIT_PHASE_IND_TRACKS_W19_2026-04-19.md`.

### BLOCKED-ON-SOLVER (regenerate when bass_py W10-02 K_ℓ atlas lands)

Exactly one figure in the current tree is solver-dependent:

| File | What changes | Audit citation |
| --- | --- | --- |
| `ch12_mio/fig_ch12d_hj01_extraction_real_backbone` | K_ℓ template (currently power-law `ℓ^{-1.4}` placeholder) and derived Σ²_MIO(ℓ) values. Planck TT residual backbone stays identical. | `AUDIT_PHASE_IND_TRACKS_W10_2026-04-19.md` §17.3 ("K_ℓ atlas dependency on bass_py W10-02 V-gate"); `AUDIT_PHASE_IND_TRACKS_W11_2026-04-19.md` ("HJ-01 production wiring ... W10-02 K_ℓ atlas V-gate를 기다리는 것이 계획"). |

**Regeneration recipe** (once W10-02 atlas lands):

```bash
# Point the HJ-01 extractor at the real bass_py K_ℓ atlas entry.
# The function `extract_from_kl_atlas` already accepts either a dict
# or an `AtlasEntry`; only the loader call needs to be swapped.
#
# Edit scripts/make_third_wave_figures.py::fig_ch12d_hj01_extraction_real_backbone
# to replace the placeholder K_ell line with a proper AtlasEntry load:
#   from workspace.contracts.atlas_entry import load_atlas_entry
#   atlas_entry = load_atlas_entry("K_ell_v1")  # or whatever W10-02 names it
# Then:
venv/bin/python scripts/make_third_wave_figures.py --only ch12d_hj01_real_backbone
# Update caption STATUS line to "real atlas" and remove the BLOCKED tag.
```

Quickly find all BLOCKED figures programmatically:

```bash
grep -rln "STATUS: BLOCKED-ON-SOLVER" figures/
```

### INTENTIONAL-MOCK (permanent; do NOT mark for regen)

These figures are pedagogical by design — the "mock" is the
scientific point, not a temporary stand-in:

| File | Why it stays mock |
| --- | --- |
| `ch07_results/fig_ch07n_tilt_history_trajectory` | Duck-typed BG record demonstrating `extract_tilt_history` interface across three β(z) scaling ansätze (p ∈ {0, 0.5, 1}). Scenario study — no single "real" curve exists. |
| `ch09_discussion/fig_ch09a_fbayes_gaussian_cross_check` | Smoke-test validation of the F_Bayes estimator against a null-symmetric Gaussian posterior (mean=0, B=1). Tests code consistency, not a physics measurement. |
| `ch11_errors/fig_ch11a_error_hierarchy` | Schematic cascade of the five-level error budget with indicative amplitudes. When SSOT numerics stabilise in ch11 text, bars can be refreshed — but the figure is conceptually a diagram, not a data figure. |
| `ch12_mio/fig_ch12d_hj01_extraction_demo` | Fully synthetic HJ-01 extraction on injected Σ² = 10⁻⁸ signal. Validates the algorithm under controlled conditions; companion to the `real_backbone` variant above. |

### ANALYTICAL (not a mock — closed-form math)

A large body of figures (MES three-bound contours, Laguerre family,
Gram admissibility, boost mixing matrices, Bessel LOS kernels,
Michaelis-Menten sentinel, TCA conditioning, Lebedev exactness, ...)
uses closed-form identities from `htt.core.bounds`,
`tsc.charts.laguerre_basis`, `bass.los.flrw_bessel_projector`,
`bass.closure.quadrupole_tca`, etc. These do not change when the
low-ℓ Boltzmann solver output lands and are **not** mocks.

### Superseded (legacy) variants on disk

Three `ch12` figures have legacy copies retained for historical
reference; prefer the `*_real_*` variants for manuscript inclusion:

| Current (use this) | Superseded legacy |
| --- | --- |
| `fig_ch12b_redshift_drift_real_probes` | `fig_ch12b_redshift_drift_axes` (synthetic LowZ_b / MidZ_b fillers) |
| `fig_ch12c_sky_coverage_real_mask` | `fig_ch12c_sky_coverage_fsky` (half-pix analytic demo) |
| `fig_ch12d_hj01_extraction_real_backbone` | `fig_ch12d_hj01_extraction_demo` (fully synthetic C_ℓ + K_ℓ) |
