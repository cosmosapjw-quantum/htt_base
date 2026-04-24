# Parallel-track figures (BASS-independent)

Produced by `scripts/make_parallel_track_figures.py` — every figure here is
derivable **without** the BASS forward solver. Re-run:

    venv/bin/python scripts/make_parallel_track_figures.py

All 12 plots use the Wong 2011 colourblind palette at 300 DPI. Anchor
values referenced in the plots are pinned in the Tier A/B/C/D regression
suites (`htt/tests/test_*_anchors.py`, `mio/tests/test_*_anchors.py`,
`tsc/admissibility/test_admissibility_anchors.py`).

## Part A — Algebra-only (no external data)

| # | File | Physics pinned by |
|---|------|-------------------|
| 01 | `fig_01_mes_three_bounds.png` | Tier-C `htt.core.bounds` anchors |
| 02 | `fig_02_tilted_flrw_dictionary.png` | Tier-C `htt.core.tilted_flrw` anchors (D26) |
| 03 | `fig_03_colin_beta_translation.png` | Tier-C `beta_from_colin` anchor (D27) |
| 04 | `fig_04_flrw_tilt_posterior.png` | Tier-A CLAUDE.md §5 ln B / β anchors |
| 05 | `fig_05_filling_fraction_scenarios.png` | Tier-A CLAUDE.md §5 F_Bayes anchor |
| 06 | `fig_06_directional_probes_mollweide.png` | Tier-B HJ-02a STANDARD_PROBES SSOT |

## Part B — Real observational data (workdir/obs_bundle/)

| # | File | Source |
|---|------|--------|
| 07 | `fig_07_planck_pr3_tt.png` | Planck PR3 TT full + binned + best-fit |
| 08 | `fig_08_planck_pr3_tt_te_ee.png` | Planck PR3 TT / TE / EE overview |
| 09 | `fig_09_planck_lowell_envelope.png` | Planck PR3 low-ℓ TT vs D₂/D₃ ΛCDM anchors |
| 10 | `fig_10_cf4_beta_variants.png` | CF4 β across Watkins2009/2023/Courtois2025 |
| 11 | `fig_11_dipole_direction_comparison.png` | Dipole directions from `dipole_scalar_observations.json` |
| 12 | `fig_12_planck_act_dr4_combined.png` | Planck PR3 + ACT DR4 TT high-ℓ extension |

## Dependencies

- `htt.core.{bounds, tilted_flrw, analysis_extended, evidence_models, ssot}`
- `mio.coherence.directional` (STANDARD_PROBES + resultant_vector + coherence_chi2)
- `workdir/obs_bundle/` via `scripts/figure_env.py` path wiring
  (`OBS_BUNDLE_ROOT` env var override supported).
