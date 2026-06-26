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

## Storage layout (outside git)

Keep raw maps out of git (`workdir/raw` is the convention; only compact summaries are
committed):

```text
workdir/raw/planck_ffp10/
  smica_cmb_mc_00000_raw.fits
  ...
  smica_noise_mc_00000_raw.fits
  ...
  MANIFEST.json        # one row per sim: id, method, cmb/noise paths, URL, sha256
```

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

2. **Build per-sim summaries** (downgrade-on-read; emit compact JSON, discard raw): extend
   `scripts/k1_global_maxscan.py` to read each sim FITS via `healpy.read_map` →
   `hp.ud_grade(m, 16)` → apply mask + beam → `compute_map_statistics` (imported from
   `make_lowell_morphology_real_map`), instead of the `hp.synfast` ΛCDM null in
   `_build_null_distribution`. Write `workdir/raw/k1_summaries/<id>.json` per sim.

3. **Run the max-scan** on the real E2E summaries (the mechanics already exist):

   ```python
   from htt.obsstat.lowell_global_calibration import e2e_maxscan_from_summaries
   # observed: (6,) from the real SMICA map; e2e: (N,6) from the sim summaries;
   # directions: from TAILS (lower->'low', upper->'high')
   result = e2e_maxscan_from_summaries(observed, e2e_summaries, directions)
   # result['global_p'] is the matched-E2E look-elsewhere global p-value
   ```

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
