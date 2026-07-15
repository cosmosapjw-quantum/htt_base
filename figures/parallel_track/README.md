# Parallel-track figures (BASS-independent)

This directory retains only the eight unaffected historical parallel-track
plots. The active generator is fail-closed because the former mixed bundle
also emitted four CF4 P0 downstream figures. Those four exact historical
figures and their conditioned copies are frozen below `legacy/cf4_p0`; they
are `legacy_reproduction_only`, have `public_use: false`, and are not current
result or appendix inputs.

## Part A — Algebra-only (no external data)

| # | File | Physics pinned by |
|---|------|-------------------|
| 01 | `fig_01_mes_three_bounds.png` | Tier-C `htt.core.bounds` anchors |
| 05 | `fig_05_filling_fraction_scenarios.png` | Tier-A CLAUDE.md §5 F_Bayes anchor |
| 06 | `fig_06_directional_probes_mollweide.png` | Tier-B HJ-02a STANDARD_PROBES SSOT |

## Part B — Real observational data (workdir/obs_bundle/)

| # | File | Source |
|---|------|--------|
| 07 | `fig_07_planck_pr3_tt.png` | Planck PR3 TT full + binned + best-fit |
| 08 | `fig_08_planck_pr3_tt_te_ee.png` | Planck PR3 TT / TE / EE overview |
| 09 | `fig_09_planck_lowell_envelope.png` | Planck PR3 low-ℓ TT vs D₂/D₃ ΛCDM anchors |
| 11 | `fig_11_dipole_direction_comparison.png` | Dipole directions from `dipole_scalar_observations.json` |
| 12 | `fig_12_planck_act_dr4_combined.png` | Planck PR3 + ACT DR4 TT high-ℓ extension |

## Dependencies

- `htt.core.{bounds, tilted_flrw, analysis_extended, evidence_models, ssot}`
- `mio.coherence.directional` (STANDARD_PROBES + resultant_vector + coherence_chi2)
- `workdir/obs_bundle/` via `scripts/figure_env.py` path wiring
  (`OBS_BUNDLE_ROOT` env var override supported).
