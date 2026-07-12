# REV-R191 — connect the acquired external datasets (DESI / ACT DR6 / JWST) into lanes

## Context

Owner ask: the datasets already on disk but not wired into any analysis lane
should be connected. Inventory found three: DESI DR1 BGS clustering, ACT DR6
CMB lensing, JWST distance anchors. Each is connected through a real loader +
real estimator, with the analysis-critical companion product (which is NOT on
disk) recorded as a registered blocker — the same discipline as K1/K5/K6.

## What connects, and what each still needs

| Lane | Data on disk | Estimator | Blocker (missing companion) |
|------|--------------|-----------|-----------------------------|
| **EXT-DESI** | BGS_ANY_NGC compact npz (4.08M gal, n̂ + sys/FKP weights) | linear number-count dipole D=3⟨n̂⟩_w, mock-verified | `BLOCKED_MISSING_DESI_RANDOMS` (window deconvolution) |
| **EXT-ACT** | κ a_lm (lmax=4000) + N_L + mask (fsky 0.234) | masked auto-bandpower C_L^κκ readout | `BLOCKED_MISSING_ACT_LENSING_SIMS` (mean field + N0/N1) |
| **EXT-JWST** | 14 Cepheid/TRGB/maser anchors, CF4-matched | already feeds the Ω_tilt forecast | — (`CONNECTED_FORECAST`) |

## DESI number-count dipole (Ω_tilt-sector cross-check)

- The linear estimator is **verified on a full-sky mock**: injects a 0.02
  dipole, recovers 0.0196 at 6.9° (SNR set above the √(3/N) shot-noise floor).
- Applied to the **real footprint** it returns D≈2.1 at fsky≈0.19 — this is
  **survey-window dominated, NOT a cosmological dipole** (the cosmological
  number-count dipole scale is ~7×10⁻³, comparable to the CMB kinematic
  dipole). It is flagged window-dominated and explicitly **not claimed**.
- The cosmological measurement needs the DESI random catalogues (angular +
  radial selection) → `BLOCKED_MISSING_DESI_RANDOMS`.

## ACT DR6 κ lensing (independent-instrument isotropy cross-check)

- The released κ a_lm + N_L + mask load; a raw masked auto-bandpower is
  computed as a data-integrity readout.
- A low-multipole κ isotropy statistic (ℓ≲10) is reconstruction-mean-field
  dominated; a sound version needs the ACT lensing simulation ensemble →
  `BLOCKED_MISSING_ACT_LENSING_SIMS`.

## Artifacts

- `htt/obsstat/egs3_external_lanes.py` + `scripts/run_external_lanes.py` →
  `docs/generated/external_lanes_seal.json` (deterministic, --check).
- Gate `research_gates/egs3/tests/test_egs3_axis_h_external_lanes.py` (6),
  auto-discovered by `make egs3-gates`.
- Results table v9 +3 rows (EXT-DESI/EXT-ACT/EXT-JWST, DATA owner); BLOCKERS.md
  +2 codes; tickets `desi_number_count_dipole.yaml` + `act_dr6_kappa_isotropy.yaml`;
  open-items ledger → 10 items (ranks 8/9); CLAIM_LEDGER +egs3.external_lanes.

## Discipline

Diagnostic-only; model-independent kinematic descriptors; no anisotropy,
geometry, family, or inference claim; no substitute estimate beyond the
labelled mock; the DESI footprint dipole is explicitly not a cosmological
dipole. The v9 report is untouched (it reads the v8 results table; the external
lanes live in BLOCKERS + the open-items ledger). Nothing under `project/`;
frozen surfaces untouched.

## Note on the two long-run companions still to download

A **sound** measurement on either lane needs a companion download that is not a
1 TB job: the DESI BGS randoms (~1–2 GB) and the ACT DR6 lensing sim ensemble.
These are the exit gates; the estimators are wired and mock-verified and run the
moment the companion products land (mirrors the FFP10 SMICA E2E download already
in flight for K1).
