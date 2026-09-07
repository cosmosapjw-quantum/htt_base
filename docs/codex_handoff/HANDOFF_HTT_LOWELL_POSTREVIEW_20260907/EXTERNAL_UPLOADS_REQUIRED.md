# EXTERNAL UPLOADS / WORKSTATION ITEMS REQUIRED

## Fresh MAIN-thread start

**No manual upload is required if GitHub access is available.** The active master/DAG, reused theory and source/data addendum are durable Git artifacts.

## Before M1/M2 can be fully frozen

| Item | Why needed | Expected filename/path | Version/hash | Acquisition/source | Required before |
|---|---|---|---|---|---|
| Existing local asset inventory | resolve product-level eligibility without re-scanning storage | `/home/cosmosapjw/Dropbox/bianchi/htt_base/workdir/asset_inventory_20260907`; `/mnt/sn850x2t/htt_base_e2e/inventories/EXTERNAL_ASSETS_20260907T071735Z` | owner inventory 2026-09-07; full archive hash NOT ASSERTED | existing workstation | final M1/M2 product freeze |
| Selected PR3 product headers/metadata | units, beam, pixel window, component-separation, coordinate and correction semantics | under `W/raw/planck_data` | exact product ID to be resolved | existing local data | M1 |
| Product-matched FFP10 manifest/headers | valid null pairing and unique realisation IDs | under `W/raw/planck_ffp10` | do not infer from 1312 paths | existing local data | M1/M3 |
| Selected CF4 raw/group metadata | native distance likelihood, grouping, calibration and selection | `W/raw/cf4*` | exact release/product to be resolved | existing local data | M2 |
| Selected DESI catalogue/random/mock metadata | window/selection/frame response | `W/raw/desi*`, `desi_dr1_mocks` | exact tracer/release/cap to be resolved | existing local data | M2/M3 |

## Optional private editorial inputs — not scientific runtime dependencies

The current conversation/File Library contains:

- `prog_repo_ver1.0.pdf` — older author research report used as writing corpus.
- `01_AUTHORIAL_STYLE_SHEET_v3.0.md`
- `02_MATH_PHYS_COPYEDITING_PROTOCOL_v3.0.md`
- `03_WRITING_AND_RESEARCH_STYLOMETRIC_PROFILE_v3.0.md`

These are private authorial/editorial inputs. **Do not publish them to Git.** Reuse them only if a fresh thread is explicitly editing prose and cannot access the current File Library.

## Large-file policy

Do not put observational datasets, simulation dumps, virtual environments, caches, package archives, model weights, credentials or private corpus files into this handoff. Preserve immutable local paths/manifests and hash only the selected inputs actually consumed by the frozen experiment.

No new mass download is an automatic blocker or default next action.
