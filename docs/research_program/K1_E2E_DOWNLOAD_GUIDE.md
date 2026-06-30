# K1 full E2E discharge — manual download + run guide

_Closes the residual of `BLOCKED_MISSING_PR4_E2E_ACCESS`: the look-elsewhere global
max-scan is already discharged on the real map under a ΛCDM null
(`scripts/k1_global_maxscan.py`, SMICA global p = 0.097); what remains is swapping
the idealised null for a **matched end-to-end (E2E) simulation ensemble** with real
instrument noise, residual foregrounds, and the component-separation transfer._

## Why this is manual

Confirmed this session by probing the sources:

- **PLA** (`https://pla.esac.esa.int/`) serves the FFP10/NPIPE simulation maps only
  through its **interactive query portal** (AJAX/session-based), not plain file URLs.
- **IRSA** (`https://irsa.ipac.caltech.edu/data/Planck/release_3/`) hosts the observed
  component-separated maps + masks at plain URLs (already in `workdir/raw/planck_data/`)
  but **no simulations** tree.
- **NERSC** (`https://portal.nersc.gov/cfs/cmb/planck2020/`) hosts NPIPE **frequency**
  maps (Light/Multi/Single-detector/Single-frequency), not component-separated CMB sims,
  and the sim ensemble needs authenticated access.
- **cobaya** installs the Blackwell–Rao **C_ℓ-level** low-ℓ TT likelihood
  (`cobaya-install planck_2018_lowl.TT` → `cov.txt` 249×249, `mu.txt`, BR tables), **not**
  a map/a_lm ensemble. The morphology statistics depend on a_lm phases, so a C_ℓ-only
  product cannot generate the null.

So the sim ensemble must be fetched by a human through the PLA portal (or NERSC auth).
Everything downstream is already built and waits for the maps.

## What to download

Pick **one** matched route. The observed map + common mask are already local
(`workdir/raw/planck_data/COM_CMB_IQU-{smica,commander}_2048_R3.00_full.fits`,
`COM_Mask_CMB-common-Mask-Int_2048_R3.00.fits`).

### Route A — FFP10 component-separated CMB simulations (recommended, matches SMICA)

From the PLA "Simulations" interface, the FFP10 component-separated CMB+noise MC for the
**same method as the observed map** (SMICA):

- `dx12_v3_smica_cmb_mc_<00000..00999>_raw.fits` — 1000 CMB realizations (signal);
- `dx12_v3_smica_noise_mc_<00000..00299>_raw.fits` — 300 noise/systematics realizations.

The honest E2E null is **CMB + noise** per realization (add a noise MC to each CMB MC, or
use the FFP10 "full" component-separated sims if the portal offers them pre-summed). Keep
the **same** component-separation method as the observed map; do not mix methods.

### Route B — NPIPE/PR4 E2E (alternative)

The ~600 NPIPE A/B end-to-end realizations (NERSC-authenticated). These are frequency-level;
a low-ℓ analysis needs a single cleaned channel or a component-separation step, so Route A
is cleaner for a morphology max-scan.

## Full download on a 2 TB nvme (the exit-gate path — recommended once disk allows)

With a dedicated 2 TB nvme the full FFP10 set fits, so Route A in full is the
strongest, exit-gate null (real CMB MC + real noise MC) — the version that flips
the `egs_results_table` K1 row `measured_partial → measured` and closes
`BLOCKED_MISSING_PR4_E2E_ACCESS`. The footprint reducers below are now optional.

**Download (PLA portal, SMICA to match the observed map):**

- `dx12_v3_smica_cmb_mc_<00000..00999>_raw.fits` — 1000 CMB (signal) MC;
- `dx12_v3_smica_noise_mc_<00000..00299>_raw.fits` — 300 noise/systematics MC.

Full IQU Nside=2048 is ~1 TB (fits a 2 TB disk with headroom for the working set).
You can keep all raw FITS this time, or still stream-downgrade (below) to keep the
nvme free for the next method (Commander) cross-check.

**Layout** (raw outside git, `workdir/raw`):

```text
workdir/raw/planck_ffp10/smica/
  cmb_mc/   dx12_v3_smica_cmb_mc_00000_raw.fits ... 00999
  noise_mc/ dx12_v3_smica_noise_mc_00000_raw.fits ... 00299
```

**Run the full E2E null (already implemented — `scripts/k1_global_maxscan.py`):**

```bash
PYTHONPATH=. venv/bin/python scripts/k1_global_maxscan.py \
    --cmb-mc-dir   workdir/raw/planck_ffp10/smica/cmb_mc \
    --noise-mc-dir workdir/raw/planck_ffp10/smica/noise_mc \
    --method smica --max-sims 1000
# -> docs/generated/k1_global_maxscan_e2e_full.json
#    null_model = ffp10_cmb_plus_noise_e2e ; global p under the matched E2E ensemble
```

It downgrades each CMB+noise pair on read to NSIDE=16, computes the six registered
statistics, and runs the frozen max-scan against the real SMICA observed 6-vector.
Pairing is `cmb_mc[i] + noise_mc[i mod n_noise]` (300 noise cycled across 1000 CMB,
matching the Planck-2018 permutation scheme). Repeat with `--method commander` for
the cross-check; **report the two side by side, do not average**. Then flip the K1
row per "Exit gate" below. The canonical GRF artifact and the route-4 noise-only
artifact are left untouched (separate files).

## Reducing the ~1 TB footprint (optional — only if disk is tight)

Downloading all `dx12_v3_smica_cmb_mc_<00000..00999>` + `..._noise_mc_<00000..00299>`
at full IQU Nside=2048 is ~1 TB. None of that volume is needed for an Nside=16,
ℓ=2–8 morphology max-scan. Four reducers, compounding:

1. **Use 300 sims, not 1300.** The Planck-2018 anomaly pipeline uses **300** E2E
   realizations — only 300 noise MC exist; the 1000 CMB MC are *permuted* with them
   (Planck 2018 VII, A&A 641 A7). Download 300 CMB + 300 noise, not 1000+300. (~4×.)
2. **Temperature only.** K1 is a TT-morphology statistic; read/keep only the I Stokes
   field. The `smica_dx12` simulation library serves μK temperature maps directly. (~3×
   vs IQU.)
3. **Stream + downgrade-on-read — the disk constraint disappears.** Process one file at
   a time: download → `hp.ud_grade(m, 16)` → compute the six statistics → **delete the
   raw map**. Peak disk = one map (~200 MB), not the full set, so the 300 GB nvme is
   never the limit — only network transfer is. Total summaries committed: a few hundred KB.
4. **[lightest real route] Noise-only + local ΛCDM signal.** Download **only the 300
   `smica_noise_mc`** (the irreplaceable real ingredient) and synthesise the CMB signal
   locally with `hp.synfast(_fiducial_cl(LMAX), nside=16)` (the ΛCDM `C_ℓ` already used
   in `make_lowell_morphology_real_map._fiducial_cl`), summing signal+noise per
   realization. **Why this is valid:** at ℓ=2–8 the *signal* is cosmic-variance-dominated,
   so any ΛCDM realization is statistically equivalent to an FFP10 CMB MC; the part the
   current isotropic-GRF null *lacks* is the real **anisotropic noise + mask coupling +
   residual foregrounds**, which the SMICA noise MC supplies. This roughly halves the
   download and is the lightest honest upgrade over the present ΛCDM-only null.

Compounded footprints (stream-downgraded, so stored ≈ a few hundred KB either way):

| Route | Files | Transfer (I-only / IQU) | Runner |
| --- | ---: | --- | --- |
| **Full Route A (1000 CMB + 300 noise)** | **1300** | **~1 TB (IQU)** | `--cmb-mc-dir --noise-mc-dir` |
| 300 CMB + 300 noise, T-only, streamed | 600 | ~85 GB / ~250 GB | `--cmb-mc-dir --noise-mc-dir --max-sims 300` |
| 300 noise-only + local ΛCDM, T-only, streamed | 300 | ~40 GB / ~125 GB | `--noise-mc-dir` (alone) |

With a 2 TB nvme, **full Route A** is the recommendation: it is the exit-gate null
(real CMB + real noise) that flips K1 `measured_partial → measured`. Route 4
(noise-only + local ΛCDM) remains the lighter fallback if disk is tight — it
upgrades the GRF null with real noise but is not the full E2E, so K1 stays
`measured_partial`. Both modes are implemented in `k1_global_maxscan.py` and write
separate artifacts (`k1_global_maxscan_e2e_full.json` / `..._e2e_noise.json`).

## Storage layout (outside git)

Keep raw maps out of git (`workdir/raw` is the convention; only compact summaries are
committed):

```text
workdir/raw/planck_ffp10/smica/
  cmb_mc/    dx12_v3_smica_cmb_mc_00000_raw.fits ... 00999   # --cmb-mc-dir
  noise_mc/  dx12_v3_smica_noise_mc_00000_raw.fits ... 00299 # --noise-mc-dir
  MANIFEST.json        # one row per sim: id, method, cmb/noise paths, URL, sha256
```

The runner globs `*.fits`/`*.fits.gz` (and `*.npz`) sorted by name in each dir, so
keep the CMB MC and noise MC in the two separate subdirs above; it pairs them
`cmb_mc[i] + noise_mc[i mod n_noise]`.

Record, per simulation: `simulation_id`, `release_family` (FFP10/NPIPE_PR4),
`component_method` (SMICA), `cmb_path`, `noise_path`, `beam_fwhm_arcmin`, `input_nside`,
`analysis_nside` (16), `mask_path` + hash, `source_url`, `sha256`. The schema/validator is
`docs/research_program/publishable_analysis_pack_2026-06-26/scripts/validate_blocker_manifest.py`
(+ `examples/k1_e2e_manifest.example.json`).

## Run (everything below is already implemented)

The frozen pipeline is identical to the observed-map path
(`scripts/make_lowell_morphology_real_map.py`): downgrade each sim to **NSIDE=16**, apply
the **matched low-ℓ mask**, compute the **six registered statistics**
(`s_one_half, parity_even_over_odd_ratio, parity_asymmetry, planarity_mean,
qo_axis_alignment_deg, axis_to_cmb_dipole_deg`), then feed the observed 6-vector + the
sim N×6 matrix to the max-scan.

1. **Validate the manifest** before processing:

   ```bash
   PACK=docs/research_program/publishable_analysis_pack_2026-06-26
   venv/bin/python "$PACK/scripts/validate_blocker_manifest.py" workdir/raw/planck_ffp10/MANIFEST.json
   ```

2. **Build summaries + run the max-scan** — now a single implemented command
   (`scripts/k1_global_maxscan.py`, rev-r136). It downgrades each sim on read
   (`hp.ud_grade(m, 16)`), computes the six statistics, and runs the frozen max-scan;
   raw maps are streamed/discarded, only the compact JSON artifact is written.

   ```bash
   # Full Route A (real CMB + real noise) -- the exit-gate null:
   PYTHONPATH=. venv/bin/python scripts/k1_global_maxscan.py \
       --cmb-mc-dir   workdir/raw/planck_ffp10/smica/cmb_mc \
       --noise-mc-dir workdir/raw/planck_ffp10/smica/noise_mc \
       --method smica --max-sims 1000
   # -> docs/generated/k1_global_maxscan_e2e_full.json (null_model ffp10_cmb_plus_noise_e2e)

   # Route 4 fallback (noise-only + local LambdaCDM), stays measured_partial:
   PYTHONPATH=. venv/bin/python scripts/k1_global_maxscan.py \
       --noise-mc-dir workdir/raw/planck_ffp10/smica/noise_mc --method smica
   # -> docs/generated/k1_global_maxscan_e2e_noise.json
   ```

   (The lower-level `e2e_maxscan_from_summaries` in
   `htt.obsstat.lowell_global_calibration` remains available if you precompute summaries
   separately; the command above is the wired path.)

4. **Flip the row** through the generator:

   ```bash
   venv/bin/python scripts/build_egs_results_table.py   # K1: measured_partial -> measured
   ```

   and add the E2E provenance (map IDs, mask, beam, NSIDE, method, config hash, input
   hashes) to `docs/generated/k1_global_maxscan.json` (set `null_model: ffp10_e2e`).

## Exit gate

- global rank p-value under the **matched E2E** ensemble (not ΛCDM);
- matched-pipeline config hash bound to {statistic list, mask, beam, ℓ-range, method};
- ensemble provenance manifest (map IDs, URLs, sha256, NSIDE, method);
- `egs_results_table` K1 row flips `measured_partial → measured` **through the generator**;
- `BLOCKED_MISSING_PR4_E2E_ACCESS` closes.

## Kill switches (per `BLOCKER_RESOLUTION_PLAN.md`)

Stop if: the map/mask/beam path differs between the observed map and the sims; component
methods are mixed without labels; fewer sims are available than declared; the p-value is
recomputed with an unfrozen statistic set; or any text claims E2E global significance
without the matched provenance.
