# HTT Figure Scripts

24 standalone figure generation scripts for the Bianchi defect framework manuscript.

## Usage

Each script is run directly:
```bash
cd htt/htt/figures/
python fig_MES_three_bounds.py
```

Or use the workspace runner to generate all:
```bash
python workspace/scripts/generate_all_figures.py
```

## Figure Table

| Script | Description | Data Dependencies |
|--------|-------------|-------------------|
| `fig_3D_constraint_volume.py` | 3D constraint space visualization | none |
| `fig_4D_projection_atlas.py` | 4D projection atlas | none |
| `fig_MES_three_bounds.py` | MES three-bound hierarchy (B_σ, B_ω, B_u̇) | none |
| `fig_cf4pp_sensitivity.py` | CF4++ sensitivity analysis | none |
| `fig_channel_ablation_heatmap.py` | Channel ablation heatmap | robustness_sweeps |
| `fig_colin_beta.py` | Colin et al. β constraints | none |
| `fig_departure_summary.py` | Departure posterior summary | FLRW_tilt_results |
| `fig_direction_posterior.py` | Directional posterior | none |
| `fig_equiv_class_evidence.py` | Equivalence class evidence | none |
| `fig_evidence_decomposition.py` | Evidence decomposition | FLRW_tilt_results |
| `fig_experiment_timeline.py` | Experimental timeline | none |
| `fig_nonlinear_heatmap_vorticity_accel.py` | Nonlinear vorticity/acceleration heatmap | none |
| `fig_peculiar_jeans.py` | Peculiar Jeans length | none |
| `fig_q0_pushforward.py` | q₀ pushforward | FLRW_tilt_results |
| `fig_q_decomposition.py` | Deceleration parameter decomposition | none |
| `fig_rho_sweep.py` | Prior width sweep | robustness_sweeps |
| `fig_scale_hierarchy.py` | Scale hierarchy | none |
| `fig_sigma_accel_contour.py` | σ–acceleration contour | none |
| `fig_sigma_omega_contour.py` | σ–ω contour | none |
| `fig_tilted_H0_depth.py` | Tilted H₀ depth profile | none |
| `fig_tilted_dictionary.py` | Tilted cosmology dictionary | none |
| `fig_type_by_type_summary.py` | Type-by-type summary | none |
| `fig_v_pushforward.py` | Velocity pushforward | FLRW_tilt_results |
| `fig_vorticity_hierarchy.py` | Vorticity hierarchy | none |

## Notes
- Scripts use `sys.path` hacks for standalone execution (P2 cosmetic, to be cleaned in production)
- Output: 300 DPI PNG with Wong (2011) colorblind-friendly palette
- Font sizes: 18pt titles, 16pt axis labels, 14pt tick marks
