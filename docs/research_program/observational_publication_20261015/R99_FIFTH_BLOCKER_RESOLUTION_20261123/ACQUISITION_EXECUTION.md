# R99 acquisition and outer-footprint execution receipt

## Completed execution

The C1–C8 data lane was executed on 2026-11-23 in
`/home/cosmosapjw/Dropbox/bianchi/htt_base`.
Source baseline: `eee33d7ed33e1af10d7c6a3c453810ecb227e461`.
Theory handoff: `575ff4811b6a5ae12d7c14bf7cd8ecadef7e58aa`.

| Component | Actual evidence | Outcome and boundary |
|---|---|---|
| Initial metadata + outer support | Remote PID3867708; exit0; wall runtime27.42s | Thirteen source responses saved; 1,580 mosaic polygons rasterized at three NSIDEs |
| Final producer replay | Remote PID3870942; exit0; finished2026-11-23T04:29:37.969554+00:00 | Hash-verified snapshots reused; same output NPZ byte identity |
| Final targeted tests | Same PID3870942; `7 passed in 0.68s` | Transfer, exact-ID, mock genealogy, geometry and exposure contracts passed |
| Explicit bounded selector | PID3870254; exit0 | 20,927,710-byte SDSS+6dFGSv future subset, downloaded_bytes0 |
| Saved selector comparison | PID3872249; exit0 | Both bounded first subset and HTTP202-deferred auxiliary selection saved in `inputs/dry_run_selections.json` |

The final producer command was:

```bash
cd /home/cosmosapjw/Dropbox/bianchi/htt_base
OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 .venv/bin/python -m scripts.r99.acquisition all
OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 .venv/bin/python -m pytest tests/obsstat/test_r99_acquisition.py -q
```

The initial and final source runs used identical science inputs. The final footprint calculation itself reported 0.798211313s; this excludes the initial network capture and the pytest runtime. Python3.12.3, NumPy2.5.4, healpy1.19.0; OMP and OpenBLAS thread settings were both1.

## File identity

| Artifact | SHA256 |
|---|---|
| `scripts/r99/acquisition.py` | fe794b47a4b0aec8e1319319323ef70b4b2ba2c4eb9a41edb3a42a053e3ab386 |
| `tests/obsstat/test_r99_acquisition.py` | 5dcaf96373478a617095f434843f41e1e0a0ee7c5095f9b9108e948e0bdca8a5 |
| `inputs/lotss_mosaics.csv` | 8671fa69f744a32f71904a2cc89919a3cf1021d7d030816d0adb218b34227572 |
| `inputs/lotss_outer_exposure_nside16.npz` | 562c8e0904d506814a50a2dcca1cd95d03dd75a1bc0d05fd77d470e221e4458d |
| R98 `radio_full_maps.npz` | 989a0f9a6d5c30b4c2468bf2d159d8b644b137e654104e32714a58201e68f6bd |
| R98 `radio_full_maps_sources.json` | 156bf2dd62acbadba451d55738a2673a39085b24e1c77e765eb2300541649398 |
| Original R89 source reader | 4ced76ad7f56e3832620b374df08cb24d96e432389783896d346dbea1ea5b940 |

The full provider source receipt is `inputs/source_receipts.json`. The producer checks the CSV, map, receipt and reader hashes plus the six original raw-file size/mtime/inode fingerprints before using the old maps. It does not re-hash or re-scan the large source catalogues. This is reuse of the R98 full-hash evidence conditional on unchanged storage identity.

The output NPZ is 14,269 bytes. Three cached NESTED fine masks in
`/home/cosmosapjw/Downloads/htt_r99/` total1,032,576 bytes. Their individual paths and SHA256 values are in `ACQUISITION_RESULTS.json`. Input responses total847,746 bytes, including17,408 bytes of bounded science prefixes. Whole scientific products transferred: **zero**.

## Tests and numerical checks

The seven tests exercise concrete failure and scientific contracts:

1. HTTP202 JSON, HTML200 and incorrect full length cannot be admitted as science files.
2. A resume range must return HTTP206 with exactly matching interval, body length and release total.
3. Large SDSS identifiers preserve all digits; floats and nonintegral IDs fail. Observer views of the same box share one mock holdout group.
4. Selectors reject implicit/duplicate/unknown products and inadequate byte budgets; a deferred product remains deferred.
5. A four-corner polygon crossing RA0 has the expected interior/exterior, is invariant under repeated union and reversed winding, and matches an independent full NSIDE32 spherical halfspace map.
6. A spherical octant has solid angle pi/2 within the declared NSIDE64 discretization tolerance; aggregation conserves total solid angle.
7. Zero-count cells inside supplied exposure remain supported; positive counts outside support, nonfinite fractions and invalid exposure fail.

The actual all-mosaic run also checked4,096 deterministic sampled centers at each of NSIDE64,128,256 against a separate spherical-halfspace implementation, with0 mismatches. It used Boolean union and did not sum overlaps.

Area results are22,480.480287,22,464.533708,22,475.129790deg². The L1 change decreased from0.0214757310sr to0.0108337393sr across successive refinements; the last maximum individual target-cell fraction change is0.046875. These are resolution diagnostics, not a mathematical error certificate.

All cached20/50/100mJy source counts lie inside the final support. The1771-cell outer support retains195/195/204 zero-count cells at the respective cuts; whether they have valid observational weight remains unverified. Every one of the old966 density-mask cells has f=1, and805 additional outer-support cells are available. Old Galactic and H I cuts explain part of this difference.

## Blocker delta

| Input blocker | Concrete progress | Remaining condition |
|---|---|---|
| D01 calibration | Exact native SDSS/6dFGSv products and ID/group/zero-point contracts prepared | Actual CF4 joint prior/likelihood and overlapping anchor genealogy |
| D02 selection | SDSS random/mocks manifests, native FP fields and holdout grouping pinned | Parent selection/rejection records, CF4 selection normalization and grouping rules |
| D05 positive-source footprint dependence | Independent1580-mosaic geometric union executed, validated and exported as exposure and fixed offset | Internal weight/RMS support, source completeness, flux/size/association/SED/LSS model |
| D05 bulk RMS data | Two exact auxiliary manifests; one deferred202 and one historical HEAD200 retained | Fresh availability, bounded authorized acquisition, checksum and internal member qualification |
| Missing exact Commander noise | Exact PR3/FFP10 ID00000 603,987,840-byte job reused from R98 | Full acquisition and enough matched signal/noise realizations for the intended null |

The newly available geometric exposure must not be promoted to a completed selection function. The existing no-Pi/GF and nonpublishable boundaries remain. This lane did not change canonical DAGs, old solver code, branches or commits; parent integration owns the final review and Git actions.

## Reuse contract for the next count likelihood

```python
import numpy as np
with np.load("docs/research_program/observational_publication_20261015/"
             "R99_FIFTH_BLOCKER_RESOLUTION_20261123/inputs/"
             "lotss_outer_exposure_nside16.npz", allow_pickle=False) as data:
    geometric_support = data["support"]
    outer_exposure_sr = data["exposure_sr"]
    outer_log_offset = data["log_exposure_sr"]
    counts = data["counts_flux20mJy"]
```

Arrays are ICRS NSIDE16 RING. The future validated mask should intersect independent coverage, valid weights/RMS and explicit scientific cuts. The historical source-density mask is retained solely for comparison. The fitted mean uses `exposure_sr*exp(X beta)` with a fixed log offset; count zeros cannot be discarded because they are inconvenient. Any refined exposure that excludes positive-count cells must stop for a source/coverage reconciliation.
