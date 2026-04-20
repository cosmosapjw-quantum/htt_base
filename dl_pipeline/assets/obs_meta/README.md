# BASS Observational Data Bundle

Reorganized from `obs_extra.zip`, `htt_extracted.zip`, and `compact_products.zip`
into a single, queryable bundle on **2026-04-16**.

## TL;DR

```python
from obs_loader import ObsCatalog
cat = ObsCatalog()                              # auto-detects obs/ root
data = cat.load("planck.pr3.tt_full")           # → Bunch with .ell, .dl, .err_lo, ...
defs = cat.load("obs_defaults.canonical")       # → dict
```

31 datasets across 8 collections, 249 MB total. All datasets discoverable through
`cat.list_ids()`; full schema in `INDEX.json`.

---

## Layout

```
obs/
├── README.md                                # this file
├── INDEX.json                               # machine-readable index, single source of truth
├── obs_loader.py                            # unified Python loader
│
├── cmb/
│   ├── powerspectra/                        # 12 datasets (Planck PR3 / ACT DR4 & DR6 / SPT-3G / BICEP-Keck)
│   │   ├── planck_pr3_tt_full.npz           # ℓ=2..2508, unbinned
│   │   ├── planck_pr3_tt_binned.npz         # ℓ=47..2499, 83 binned
│   │   ├── planck_pr3_te_full.npz           # ℓ=2..1996
│   │   ├── planck_pr3_ee_full.npz           # ℓ=2..1996
│   │   ├── planck_pr3_bb_lowl.npz           # ℓ=2..29
│   │   ├── planck_pr3_eb_lowl.npz           # ℓ=2..29
│   │   ├── act_dr4.npz                      # binning + clcmb + theory packed
│   │   ├── act_dr6_tt.npz                   # 57 bandpowers, ℓ=64..7526, PA5 f150 only
│   │   ├── act_dr6_te.npz
│   │   ├── act_dr6_ee.npz
│   │   ├── spt3g_y1.npz                     # bandpowers + cov + windows + tSZ template
│   │   └── bicep_keck_2018_bb.npz           # BK18lf full release as dict-of-arrays
│   ├── theory/
│   │   ├── planck_pr3_bestfit.npz           # TT/TE/EE/BB/PP best-fit theory
│   │   └── camb_planck2018_lensing_refs.npz # CAMB reference for lensing pipeline
│   ├── lensing/
│   │   └── planck_pr3_lensing.npz           # PR3 lensing release as dict-of-arrays (40 entries)
│   ├── maps/
│   │   ├── commander_nside16.npz            # I, Q, U at NSIDE=16, RING, μK
│   │   └── smica_nside16.npz                # ditto
│   └── masks/
│       ├── temp_nside16.npz                 # fsky=0.789
│       └── pol_nside16.npz                  # fsky=0.791
│
├── lss/
│   └── desi_y1/                             # 6 clustering catalogs, common (ra, dec, z, weight, n_hat) schema
│       ├── bgs_ngc.npz                      # 4,081,227 rows
│       ├── bgs_sgc.npz                      # 1,441,126 rows
│       ├── lrg_ngc.npz                      # 1,476,135 rows
│       ├── lrg_sgc.npz                      #   662,492 rows
│       ├── qso_ngc.npz                      #   793,219 rows
│       ├── qso_sgc.npz                      #   430,172 rows
│       └── manifest.json                    # provenance + column docs
│
├── pecvel/
│   └── cf4/
│       ├── query_single.json                # single-point reconstruction
│       └── query_batch.npz                  # hardware-adaptive batched query
│
└── scalars/
    ├── obs_defaults.json                    # CANONICAL: planck2018 + dipoles + vorticity + 6 scenarios
    ├── obs_defaults_watkins2023.json        # variant: β = 1.318±0.097e-3 (Watkins+2023 CF4 MVE)
    ├── obs_defaults_courtois2025.json       # variant: β = 1.051±0.133e-3 (Courtois+2025 CF4++ HMC)
    └── dipole_scalar_observations.json      # original consolidated file (kept for back-compat)
```

---

## Naming convention

Every dataset has a `dataset_id` of the form `<collection>.<instrument>.<spectrum_or_field>`,
which is the key used by the loader and by `INDEX.json`.

Examples: `planck.pr3.tt_full`, `act.dr6.ee`, `desi.lrg.ngc`, `cf4.query_batch`,
`obs_defaults.canonical`.

Filenames on disk are lowercase snake_case mirrors of the id. The loader is the
preferred entry point — paths may move, ids will not.

---

## Loader API

`obs_loader.ObsCatalog` — single class, three usage modes.

| Method                              | Returns                                         | Use case                            |
| :---------------------------------- | :---------------------------------------------- | :---------------------------------- |
| `cat.list_ids()`                    | `list[str]`                                     | discover everything                 |
| `cat.collections()`                 | `list[str]`                                     | top-level groupings                 |
| `cat.ids_in("cmb.powerspectra")`    | `list[str]`                                     | datasets in one collection          |
| `cat.meta(dataset_id)`              | `dict` (INDEX entry)                            | inspect schema before loading       |
| `cat.load(dataset_id)`              | `Bunch` (NPZ) or `dict` (JSON)                  | load data                           |
| `cat.find(spectrum="TT")`           | `list[str]`                                     | filter by spectrum or instrument    |
| `cat.normalize_spectrum(b)`         | `Bunch(ell, dl, sigma)`                         | uniform Planck/ACT view             |

`Bunch` is a dict with attribute access: `b.ell` and `b["ell"]` both work. NPZ
0-d string arrays (`source`, `tracer1`, …) are decoded to plain `str`.

A bundled `_meta` key carries the INDEX entry alongside the data, so the dataset
remains self-describing once loaded.

---

## Conventions

| Item                  | Convention                                                                 |
| :-------------------- | :------------------------------------------------------------------------- |
| Power spectra         | $D_\ell = \ell(\ell+1)C_\ell/(2\pi)$ in $\mu\mathrm{K}^2$                  |
| Planck error columns  | `err_lo`, `err_hi` (asymmetric); usually equal for Planck PR3              |
| ACT error column      | `dl_err` (symmetric, single column)                                        |
| Healpix maps          | RING ordering (healpy default), $N_\mathrm{side}=16$, 3072 pixels          |
| Map units             | $\mu\mathrm{K}_\mathrm{CMB}$                                               |
| DESI catalog dtype    | `float32` throughout                                                       |
| DESI sky direction    | `n_hat` is unit Cartesian 3-vector (already $|\hat n|=1$)                  |
| CF4 coordinates       | supergalactic Cartesian, Mpc/h; velocities km/s                            |

---

## Provenance and validation

The bundle was produced from three uploaded archives. A consistency check at
build time confirmed that the canonical SSOT scalars match the underlying data:

```
obs_defaults.canonical D2 = 225.9     vs   planck.pr3.tt_full @ ℓ=2 = 225.895   ✓
obs_defaults.canonical D3 = 936.9     vs   planck.pr3.tt_full @ ℓ=3 = 936.920   ✓
planck.pr3.bestfit  D_TT @ ℓ=2 = 1016.73   vs   camb.planck2018 = 1022.82   (<1%)  ✓
```

Three CF4 variants are kept distinct because the `β` value differs by up to 25%:

| File                              | CF4 source              | β (× 10⁻³) | Catalog size      |
| :-------------------------------- | :---------------------- | :--------- | :---------------- |
| `obs_defaults.json` (canonical)   | Watkins+2009 COMPOSITE  | 1.334      | 4,481 galaxies    |
| `obs_defaults_watkins2023.json`   | Watkins+2023 CF4 MVE    | 1.318      | 38,058 groups     |
| `obs_defaults_courtois2025.json`  | Courtois+2025 CF4++ HMC | 1.051      | 65,518 galaxies   |

Pick the variant the analysis demands; do not mix.

---

## Caveats worth surfacing

`act.dr6.*` carries both `dl` and `cl` columns. The `dl` values are large
because the sacc-file extraction inherits a different normalisation from the
DR6 release; use `cl` (in $\mu\mathrm{K}^2$) for cross-checks against Planck.

`bicep_keck.2018.bb` and `planck.pr3.lensing` are dict-of-arrays NPZs that
preserve the upstream release's file layout (e.g. `BK18lf_cl_hat.dat`,
`smica_g30_ftl_full_pp_bandpowers.dat`). The `file_list` key inside each NPZ
enumerates all entries.

The `bestfit` column in the Planck PR3 spectrum NPZs (full TT, TE, EE, BB, EB)
is zero. For best-fit theory, load `planck.pr3.bestfit` or
`camb.planck2018.lensing_refs` instead.
