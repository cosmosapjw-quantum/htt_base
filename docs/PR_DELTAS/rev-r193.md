# REV-R193 — EXT-DESI flipped blocked → measured (window-corrected number-count dipole)

## Context

The DESI DR1 BGS random catalogues were downloaded via the REV-R192 fetcher
(`fetch.py --desi-randoms`: NGC_0 1.58 GB + SGC_0 0.65 GB). With the randoms
in place the EXT-DESI number-count-dipole lane can deconvolve the survey
selection function and flip from blocked to measured.

## The measurement

`scripts/desi_dipole_measure.py` → `docs/generated/desi_dipole_card.json`
(deterministic, `--check`): the window-corrected overdensity dipole

    delta_pix = (D_pix - alpha R_pix) / (alpha R_pix),   alpha = sum w_D / sum w_R

per cap, then the linear estimator D = 3⟨delta n̂⟩_R over NGC+SGC (fsky 0.28):

- **D = 9.49×10⁻³**, direction (l,b) = (172.5°, −44.7°), 122° from the CMB
  dipole.
- A **224× suppression** of the raw footprint value (2.13) down to the
  kinematic scale (~7×10⁻³) — the randoms remove the survey window that
  dominated the raw estimate.

## Honest scope (diagnostic-only)

- The BGS sample is low-z (z<0.5), so the measured dipole **mixes the local
  large-scale-structure (clustering) dipole with the kinematic dipole** — it
  is not a clean kinematic signal.
- The fsky~0.28 partial-sky mask couples multipoles, so a calibrated amplitude
  and significance still need **release-matched mocks** (residual gate).
- Model-independent kinematic descriptor; no anisotropy, geometry, family, or
  inference claim; no data-detection headline.

## Wiring

- `htt/obsstat/egs3_external_lanes.py` DESI lane reads the card when present →
  status `MEASURED_WINDOW_CORRECTED` (keeps the mock-verified estimator +
  raw-footprint contrast); falls back to `BLOCKED_MISSING_DESI_RANDOMS` when
  the card is absent.
- `external_lanes_seal.json` regenerated (PASS); gate
  `test_egs3_axis_h_external_lanes.py` +1 (window-corrected test), 7 total.
- Results table v9 EXT-DESI row → `measured_diagnostic`; ticket →
  `randoms_downloaded_window_corrected_measured`; BLOCKERS.md
  `BLOCKED_MISSING_DESI_RANDOMS` → **DISCHARGED**; open-items ledger rank-8 →
  residual mock-significance; CLAIM_LEDGER egs3.external_lanes →
  DESI_MEASURED_ACT_BLOCKED.

## Status

- **EXT-DESI: MEASURED** (window-corrected, diagnostic).
- **EXT-ACT: still blocked** — the ACT DR6 lensing sim ensemble is downloading
  (`fetch.py --act-sims`, tmux, ~227/400 at commit time); EXT-ACT flips when
  the mean field is available.
- v9 report untouched (reads the v8 results table). Compact DESI npz verified
  byte-identical after the fetch (extraction deterministic).
