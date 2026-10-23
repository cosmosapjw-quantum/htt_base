# PR4 observed-input intake, 2026-10-22

Scope: source and payload qualification only for the L03 observational lane. This does not run a morphology statistic, combine splits, calibrate a null law, supply a Bianchi/global-history T/E/B transfer, or change original scientific acceptance. Raw products and create-only receipts are under `/mnt/extdrive/workdir/htt_open_data/research20261022/pr4/`; the additive [acquisition manifest](../ACQUISITION_MANIFEST.json) uses expected byte identities without per-file or aggregate download caps. The external drive was mounted read-write with `df -h` reporting 2.3T available; the fetcher enforced its 2 GiB free-space reserve before and during streaming.

The [IRSA LFI product index](https://irsa.ipac.caltech.edu/data/Planck/release_3/ancillary-data/LFI_Products.html) directly lists two R4.00 observed year maps. Their FITS extension comments identify the producer inputs as `npipe6v20A_030_map.fits` and `npipe6v20B_030_map.fits` respectively, both with `FREQ=30` and `POLCCONV=COSMO`. The filenames say `year-1-3` and `year-2-4`; the [NPIPE primary paper, Table 5](https://doi.org/10.1051/0004-6361/202038073) describes the 30 GHz A split as years 1 and 3 and B as years 2, 4 and the start of 5. Keep that producer/file-label specificity visible rather than silently treating the filename as an exhaustive observing-time contract.

| Exact source and product | Bytes; SHA-256 | FITS schema and inspected data |
|---|---|---|
| [IRSA A, `year-1-3`](https://irsa.ipac.caltech.edu/data/Planck/release_3/all-sky-maps/maps/LFI_SkyMap_030_1024_R4.00_year-1-3.fits) | 503,326,080; `7dc8414835f5041ad51373505e15a17f3fb286fac1f41a48e72f09f46aa901b0` | HEALPix `NSIDE=1024`, NESTED, Galactic, COSMO polarization, 10 fields, `I/Q/U_STOKES` each `1024E`, `K_CMB`; each Stokes has 12,582,912 finite non-sentinel pixels |
| [IRSA B, `year-2-4`](https://irsa.ipac.caltech.edu/data/Planck/release_3/all-sky-maps/maps/LFI_SkyMap_030_1024_R4.00_year-2-4.fits) | 503,326,080; `b7de3e4fbafb2553db26d2c24b5d91f68dd42b86135e989c25d095a63e611c8f` | Same schema/count; FITS comment names `npipe6v20B_030_map.fits` |
| [NERSC Lollipop low-ell mask](https://portal.nersc.gov/cfs/cmb/planck2020/misc/mask_PR4_Lollipop_ns16.fits) | 20,160; `7d7df63e77066a7739cc7faed3a005593bb3612af6cdeea2ed48a37fb600946d` | HEALPix `NSIDE=16`, RING, Galactic, one `T` field; 3,072 finite pixels, 1,273 ones and 1,799 zeros. Mask/statistic compatibility remains unproved. |

[verify_pr4.py](verify_pr4.py) checks SHA/receipt/expected size, FITS block length, source split comments, dimensions, ordering, coordinates, polarization convention, units, and full I/Q/U finite/sentinel counts using memory-mapped rows. The exact read-only output is [VALIDATION.json](VALIDATION.json). It passed under `.venv/bin/python` with no fit, null combination or upstream code execution. The `HITS` and six per-pixel covariance columns are present in schema but are not independently calibrated by this intake.

The [CMB-S4 Quickpol page](https://data.cmb-s4.org/planck_pr4-quickpol.html) lists `Bl_TEB_npipe6v20_030Ax030B.fits`, `Wl_npipe6v20_030Ax030B.fits` and a manifest. Their linked unauthenticated Globus URLs returned HTTP 404 `PATH_NOT_FOUND` on HEAD and a single diagnostic Range GET; no payload was acquired from that path. This failed route is preserved, with no further Globus retry.

An independently accessible [official NERSC PR4 RIMO transfer archive](https://portal.nersc.gov/cfs/cmb/planck2020/misc/PLANCK_RIMO_TF_R4.00.tar.gz) supplied those **exact two named products** as tar members, without extraction. Archive: 235,039,576 bytes, SHA-256 `fd964fdb48829b506089c80d85626c03b55e47467e01ed420861940052e86bf9`, 1,026 tar members. Relevant members:

| Member under `simulated_maps/npipe_aux/beam_window_functions/AB/` | Bytes; SHA-256 | In-memory FITS check |
|---|---|---|
| `Bl_TEB_npipe6v20_030Ax030B.fits` | 195,840; `d505872b306e65c480b9fd52f9832e6f6f4976fb71bd769a20bb6701fb5d695c` | `WINDOW FUNCTIONS` ASCII table, 4,097 rows, finite T/E/B columns |
| `Wl_npipe6v20_030Ax030B.fits` | 624,960; `49d9bebdf82243712a10880401ce2d487c56ecd16afa03aa3e455527c492566a` | TT/EE/BB/TE extensions, each nine `4097E` finite coupling fields |

These are effective multipole/spectrum beam windows. Their schema does not give a full pixel/harmonic map operator, a foreground separation law, mask/statistic transfer, or the required null distribution. Archive membership and finiteness close exact paired **availability**, not scientific beam correction or L03 admission.

The observed A/B URL availability, payload schema, and exact paired spectrum-window availability sub-blockers are resolved. L03's map/covariance/mask/beam/foreground alignment and statistic-specific null law, along with the distinct physical T/E/B atlas, remain unresolved. No historical PR3, quartet, Gaia, radio or ODE campaign was repeated.
