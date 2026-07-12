# REV-R194 — EXT-ACT flipped blocked → measured (mean-field-debiased low-ℓ κ isotropy)

## Context

The ACT DR6 lensing baseline simulation ensemble (400 × 152.7 MB = 59.7 GB)
was downloaded via the REV-R192 fetcher (`fetch.py --act-sims`, aria2 to the
off-Dropbox NVMe). With the sims in place the EXT-ACT lane can form the
reconstruction mean field and flip from blocked to measured.

## The measurement

`scripts/act_kappa_isotropy_measure.py` → `docs/generated/act_kappa_card.json`
(deterministic; streams the 400 sim alms, ~10 min — run standalone, not in the
gate): forms the mean field MF = ⟨κ_alm_sim⟩ over the 400 sims, subtracts it
from the data and each sim, and compares the ℓ=2..10 debiased band power

    S = Σ_{ℓ=2..10} Σ_m |a_ℓm − MF_ℓm|²

of the data to the sim (isotropic) null:

- **p = 0.35** (data band statistic 7×10⁻⁶ = the sim median) → **CONSISTENT
  with the isotropic ΛCDM sims** — the expected null result for an
  independent-instrument (ACT, not Planck) low-multipole lensing isotropy
  cross-check.
- Per-ℓ debiased C_ℓ (ℓ=2..10) all ~1×10⁻⁷, consistent with the sim mean.

## Honest scope (diagnostic-only)

- The ACT reconstruction does **not measure ℓ=0,1** (monopole + dipole are NaN,
  degenerate with the mean field), so the cross-check is **ℓ=2..10 only** —
  there is no ACT κ dipole.
- N0/N1 realisation-dependent biases are not separately debiased (the sim
  ensemble is used directly as the isotropic null); the κ low-multipole band is
  reconstruction-noise-dominated, so consistency is the expected result.
- Independent-instrument low-multipole κ isotropy cross-check; no anisotropy,
  geometry, family, or inference claim.

## Wiring

- `htt/obsstat/egs3_external_lanes.py` ACT lane reads the card when present →
  status `MEASURED_MEAN_FIELD_DEBIASED` (falls back to
  `BLOCKED_MISSING_ACT_LENSING_SIMS` when absent).
- `external_lanes_seal.json` regenerated (PASS, both DESI + ACT measured); gate
  `test_egs3_axis_h_external_lanes.py` +1 (ACT isotropy-measured test), 8 total.
- Results table v9 EXT-ACT → `measured_diagnostic`; ticket →
  `sims_downloaded_mean_field_debiased_isotropy_measured`; BLOCKERS.md
  `BLOCKED_MISSING_ACT_LENSING_SIMS` → **DISCHARGED**; open-items ledger rank-9
  → residual N0/N1; CLAIM_LEDGER egs3.external_lanes → DESI_AND_ACT_MEASURED.

## Status — both EXT lanes now measured

- **EXT-DESI**: window-corrected number-count dipole D=9.49×10⁻³ (R193).
- **EXT-ACT**: mean-field-debiased ℓ=2..10 κ isotropy, p=0.35 CONSISTENT (this
  cycle).
- **EXT-JWST**: connected forecast.

All three acquired datasets are now real measurements/connections in the
framework. Both companion downloads (DESI randoms, ACT sims) landed and were
used. v9 report untouched (reads the v8 results table). Data on
gitignored workdir / off-Dropbox NVMe, not git.
