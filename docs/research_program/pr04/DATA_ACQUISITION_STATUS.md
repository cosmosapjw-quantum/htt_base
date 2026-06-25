# Raw-data acquisition status (LR-06 data track)

Date: 2026-06-25. Branch `research/pr04-multicomponent`.

The `dl_pipeline/` (SSoT `dl_pipeline/config/sources.json`) owns: Planck **PR3**
spectra/maps/masks/lensing, ACT DR4/DR6, SPT-3G Y1, BICEP/Keck 2018, DESI Y1 LSS,
the **CF4++ grid** (single mean/std grid), and CAMB references. `workdir/obs_bundle/`
already holds the PR3 NSIDE=16 maps/masks/spectra and the CF4++ batch used by
REV-R102/R103. Disk free: ~508 GB.

A background refresh of the available products (`cf4`, `camb_refs`) was started
(`artifacts/pr04/fetch_cf4_camb.log`). The available stages do **not** own the
delegated inputs the data tickets require, so refreshing them does not unblock
LR-06D–G. The honest mapping:

| Ticket | Required delegated input | In `dl_pipeline`? | Status | Blocker |
| --- | --- | --- | --- | --- |
| LR-06D | **Full CF4 release** with method/group/selection covariance hierarchy and a fixed release binding | No — only the single CF4++ grid NPZ | **blocked** | `BLOCKED_MISSING_FULL_RELEASE_BINDING` |
| LR-06E | Planck **PR4/NPIPE** maps + **end-to-end simulations** + mask/cleaning operator | No — pipeline is PR3 only; no E2E sims | **blocked** | `BLOCKED_MISSING_E2E_SIMULATIONS` |
| LR-06F | Constrained/posterior **3D velocity-field realizations** | No | **blocked** | `BLOCKED_MISSING_FIELD_REALIZATIONS` |
| LR-06G | Validated **ray-tracing / transfer** artifacts + independent temporal kernels | No (also depends on LR-06C) | **blocked** | `BLOCKED_UPSTREAM_TRANSFER` |

These are valid terminal states per `RAW_DATA_DELEGATION.md`: a missing input is
terminal, and no proxy/compact/legacy product may be substituted for the missing
full release. The CF4++ grid present locally is sufficient for the **schema/row**
gate scaffolding of LR-06D but not for its full-release method/group/selection
hierarchy, so LR-06D cannot advance past the schema stage.

## To unblock (owner actions, outside `dl_pipeline`)

- LR-06D: bind a fixed CF4 full release (group catalog + method/group/selection
  covariance), add a `cf4_full_release` stage to `sources.json` with a release hash.
- LR-06E: obtain PR4/NPIPE maps + the matched end-to-end simulation set; add an
  E2E-sim stage and a boost-injection harness.
- LR-06F: obtain a constrained velocity-field ensemble (e.g. 2M++/CF4 posterior
  realizations) with cross-cell covariance.
- LR-06G: stand up a validated light-cone/ray-tracing or transfer owner (ties to
  the LR-06L native solver) before the tensor kernel can be validated.
