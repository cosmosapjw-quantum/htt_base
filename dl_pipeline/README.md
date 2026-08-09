# BASS Data Pipeline

Single-command download + extraction for every external observational dataset
needed by the BASS bundle. Replaces six previous scripts
(`get_planck_maps_primary.sh`, `extract_htt_data.py`, `download_obs_data.sh`,
the `external_data_recovery_v2/` kit, the `optional_catalogs_v3/` kit) with one
orchestrator and one config file.

---

## TL;DR

```bash
cd dl_pipeline/
bash run_all.sh ./workdir
# → workdir/obs_bundle/   (unpacked tree, local-dev deliverable)
# Pass BUNDLE_ZIP=1 to also emit obs_bundle.zip (off by default).
```

That's it. Everything is idempotent — re-running skips files that are already
in place. Intermediate artifacts stay under `./workdir/` for inspection.

The pipeline is wired to `../venv/bin/python` (repo-root venv). Override with
`BASS_VENV_PY=/path/to/python` if you maintain the venv elsewhere.

**Local-dev defaults (differ from the sandbox era)**

| Step | Sandbox-era default | Local-dev default (current) |
|------|---------------------|------------------------------|
| NPZ writes | `savez_compressed` | `savez` (uncompressed — saves CPU) |
| Final `.zip` | always built (deflate) | off; opt-in via `BUNDLE_ZIP=1` (store-only) |
| DESI columns | `minimal` (ra/dec/z/weight/n_hat) | `extended` (+FKP/sys/zfail, targetid, ntile, photsys) |
| ACT DR4 / SPT-3G | first-match-only per pattern | keep-all (multi-frequency covs preserved) |
| Planck maps/masks | NSIDE 2048 → 16 only | NSIDE 2048 → 16 by default; `FULL_RES_MAPS=1` also dumps full-resolution NPZs |

Override any of these via env vars on `run_all.sh` or the matching
`--planck-nside-out / --full-res-maps / --desi-mode / --bundle-zip` flags on
`scripts/fetch.py`.

---

## What it does, in order

| # | Stage | Source | Output | Size |
|---|----------------|---------------------------------------|------------------------------------------|--------|
| 1 | `env` | pip | (no artifact) | — |
| 2 | `planck_pr3` | IRSA (Planck PR3 ancillary) | `htt_extracted/planck_*.npz` | ~3.5 GB raw → ~250 KB |
| 3 | `bicep_keck` | cobaya-install | `obs_extra/bicep_keck_2018_BB.npz` | ~700 MB raw → ~58 MB |
| 4 | `planck_lensing` | cobaya-install | `obs_extra/planck_2018_lensing.npz` | ~1 MB |
| 5 | `act_dr4` | LAMBDA + GitHub | `compact_products/act_dr4_compact.npz` | ~70 MB raw → ~150 KB |
| 6 | `act_dr6` | (manual or `ACT_DR6_SACC_URL`) | `htt_extracted/act_dr6_*.npz` | depends |
| 7 | `spt3g_y1` | LAMBDA + GitHub | `compact_products/spt3g_y1_compact.npz` | ~30 MB raw → ~135 KB |
| 8 | `desi_y1` | DESI DR1 LSS | `compact_products/desi/*_minimal.npz` | ~2 GB raw → ~190 MB |
| 9 | `cf4` | (manual or `CF4_GRID_URL`) | `compact_products/cf4/query_*.{json,npz}` | depends |
| 10 | `camb_refs` | local CAMB | `compact_products/camb_planck2018_lensing_refs.npz` | ~230 KB |
| 11 | `scalars` | repo `obs_defaults*.json` | `compact_products/dipole_scalar_observations.json` | ~8 KB |
| 12 | `package` | local | `obs_bundle/` (zip opt-in via `BUNDLE_ZIP=1`) | ~250 MB |

The final `obs_bundle/` directory mirrors the `obs/` layout established by the
prior reorganization (`cmb/{powerspectra,theory,lensing,maps,masks}/`,
`lss/desi_y1/`, `pecvel/cf4/`, `scalars/`) and ships with `README.md`,
`INDEX.json`, and `obs_loader.py` baked in.

---

## Requirements

- Python ≥ 3.10
- `curl` (preferred) or fall back to `urllib`
- ~6 GB free disk space for raw downloads (or ~3 GB if `SKIP_LARGE_MAPS=1`)
- Network access to: `irsa.ipac.caltech.edu`, `lambda.gsfc.nasa.gov`,
  `github.com`, `data.desi.lbl.gov`

The `env` stage installs everything from `requirements.txt` **into the active
venv** (it refuses to run outside one). To set up the repo-local venv manually:

```bash
python3 -m venv ../venv
../venv/bin/pip install -r requirements.txt
```

All downstream scripts are invoked through `sys.executable`, so once
`run_all.sh` picks up `../venv/bin/python` every stage inherits the same
interpreter. Nothing ever touches the system/global Python.

---

## Two manual steps

Two datasets cannot be auto-downloaded because they live behind off-tree URLs:

### ACT DR6 (`act_dr6` stage)

The DR6 sacc release is not at a stable public URL Anthropic-side. Either:

```bash
# Option A: known mirror
ACT_DR6_SACC_URL="https://..." bash run_all.sh

# Option B: manual placement
cp /path/to/dr6_data.fits ./workdir/raw/act_data/
bash run_all.sh   # planck_pr3 stage will pick it up
```

If neither is provided, the stage logs the missing-file path and continues —
the rest of the pipeline still works, the final bundle just lacks ACT DR6.

### CF4++ grid (`cf4` stage)

The `cf4` stage now tries the canonical CF4++ NPZ URL automatically:

```text
https://projets.ip2i.in2p3.fr//cosmicflows/CF4pp_mean_std_grids.npz
```

So the default path is just:

```bash
bash run_all.sh
```

If you want to override that URL or if the built-in one fails, use:

```bash
CF4_GRID_URL="https://..." bash run_all.sh

# Or place it manually
cp /path/to/CF4pp_mean_std_grids.npz ./workdir/raw/cf4/
bash run_all.sh
```

The expected NPZ keys are listed in `config/sources.json` under `cf4.expected_keys`.

---

## Where the data physically lands

Every stage still addresses its outputs as `<workdir>/...`, but bulk data is
written to an external volume and linked back, so the repository checkout (on
the system NVMe, inside a Dropbox tree) never carries hundreds of gigabytes.

The redirect is applied by `scripts/external_store.py` when a directory is
first created, on the children of `workdir/` and of `workdir/raw/`:

```
workdir/raw/planck_data  ->  /mnt/sn850x2t/htt_base_e2e/workdir/raw/planck_data
```

`workdir/` and `workdir/raw/` themselves stay real directories: the former
carries the `com.dropbox.ignored` attribute that keeps the Dropbox daemon out,
and the latter holds acquisitions that are deliberately not exposed to the
repository. `workdir/logs/` also stays local.

| variable | effect |
| --- | --- |
| `HTT_EXTERNAL_DATA_ROOT=<path>` | use `<path>` as the external store |
| `HTT_EXTERNAL_DATA_ROOT=` (empty, or `off`) | disable; write inside the repo |
| unset | use `/mnt/sn850x2t/htt_base_e2e/workdir` if that volume is mounted, else write inside the repo |

A checkout on a machine without the external volume therefore behaves exactly
as it did before. If a redirect link exists but its target is unreachable — an
unmounted volume — the pipeline fails closed instead of silently refilling the
system disk.

---

## Layout of `dl_pipeline/`

```
dl_pipeline/
├── run_all.sh                          ← single entry point
├── requirements.txt                    ← Python deps
├── README.md                           ← this file
├── config/
│   ├── sources.json                    ← SSOT: every URL, every output filename
│   └── planck2018_camb_params.json     ← Planck 2018 best-fit cosmology for CAMB
├── scripts/
│   ├── fetch.py                        ← orchestrator (reads sources.json, runs stages)
│   ├── external_store.py               ← places bulk data on the external NVMe, links it back
│   ├── extract_htt_data.py             ← Planck PR3 + ACT DR6 → compact NPZ (440 lines, validated)
│   ├── extract_cmb_like_products.py    ← ACT DR4 + SPT-3G Y1 → compact NPZ
│   ├── extract_desi_compact.py         ← DESI clustering FITS → minimal NPZ
│   ├── cf4_grid_adapter.py             ← CF4++ grid query (single + batch)
│   ├── generate_cf4_targets_from_desi.py ← benchmark local CF4 throughput, then build adaptive DESI BGS target CSV
│   ├── pack_cobaya_install.py          ← BICEP/Keck + Planck-lensing → NPZ
│   ├── generate_camb_lensing_refs.py   ← run CAMB → reference Cls
│   ├── package_dipole_observations.py  ← assemble dipole_scalar_observations.json
│   └── package_obs_bundle.py           ← final mapping → obs_bundle/ + .zip
├── assets/
│   ├── targets_cf4_from_desi_bgs.csv   ← bundled fallback input for CF4 batch query
│   └── obs_meta/                       ← README, INDEX, obs_loader baked into final bundle
│       ├── README.md
│       ├── INDEX.json
│       └── obs_loader.py
└── logs/                               ← per-run timestamped logs
```

---

## Common operations

```bash
# Just see what would run, no downloads
../venv/bin/python scripts/fetch.py --root ./workdir --all --dry-run

# Run a single stage
../venv/bin/python scripts/fetch.py --root ./workdir --stages planck_pr3

# Run a couple stages
../venv/bin/python scripts/fetch.py --root ./workdir --stages desi_y1,cf4,package

# Force re-download everything
FORCE=1 bash run_all.sh

# Skip the giant maps if disk is tight
SKIP_LARGE_MAPS=1 bash run_all.sh

# Also emit the zip bundle (off by default; local-dev reads obs_bundle/ directly)
BUNDLE_ZIP=1 bash run_all.sh

# Keep the full-resolution (NSIDE=2048) Planck maps/masks alongside the downgrade
FULL_RES_MAPS=1 bash run_all.sh

# Downgrade Planck maps to a higher NSIDE (e.g. 128 for ℓ≲500 analyses)
PLANCK_NSIDE_OUT=128 bash run_all.sh

# Strip DESI back to the sandbox minimal columns
DESI_MODE=minimal bash run_all.sh

# List stages with descriptions
../venv/bin/python scripts/fetch.py --root ./workdir --list
```

---

## Idempotency rules

- **Downloads**: skipped if `dst.exists()` and `!FORCE`. Size and content not
  re-checked (curl handles partial-resume on its own).
- **Extractions**: most extractors are run-to-completion idempotent — they
  overwrite their NPZ outputs. Re-running is cheap (~seconds per stage once
  raw files are local).
- **Packaging**: `package_obs_bundle.py` does a fast-eq check (size + first-1KB
  SHA-1) and skips identical files. The `.zip` is opt-in (`--zip` /
  `BUNDLE_ZIP=1`) and uses `ZIP_STORED` (no deflate) when requested — local
  disk is assumed cheaper than CPU spent on compression.

---

## Provenance and audit

Every run writes a timestamped log to `logs/fetch_YYYYMMDD_HHMMSS.log` and
`obs_bundle/_packaging_log.json` records every copy decision. The full URL list
is `config/sources.json`; nothing is hardcoded in scripts.

---

## Recovery from partial state

If the network drops mid-download, just re-run. `curl --retry 4` handles
short-term blips inline; for longer outages, the next `run_all.sh` invocation
picks up where it left off because every stage is gated by file existence.

If a stage fails permanently (e.g. an upstream URL is dead), the orchestrator
logs `[FAIL]` and continues with the next stage. The exit code is non-zero so
CI can catch it, but downstream stages still attempt to do whatever they can.
