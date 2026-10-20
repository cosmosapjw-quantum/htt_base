# Focused NPIPE frame and Q/U source binding

Owner obsstat; C0 / DIAGNOSTIC_ONLY source qualification, 2026-10-20. Exact target: `npipe6v20_cmb_030_A_mc_00200.fits`. No map acquisition, simulation, solver, statistic or physical claim was run.

**Galactic frame with HEALPix/COSMO Q/U is the source-supported intended convention.** This is a release/producer-lineage inference, not a direct reading of the omitted COORDSYS/POLCCONV keywords. The missing keywords alone need not be treated as evidence for a different frame or an IAU sign convention. A literal public-product-to-cache packaging identity was not established by the inspected sources.

I first re-examined the already downloaded official Simulation_data page. Its explicit Galactic/COSMO table rows are in the older FFP8/FFP9 section, so those rows alone do not establish the exact PR4 product convention. Its NPIPE section does establish the shared PR3 CMB realization lineage and the asymmetric-beam / reference-map distinction. The earlier verified release-wide K_CMB unit statement remains applicable metadata; this addendum does not infer units from a missing TUNIT card.

One new source route was inspected: the official [planck-npipe/toast-npipe repository](https://github.com/planck-npipe/toast-npipe), selected files only, pinned commit `669becf0c52ec10731318076e7909d2d015c1a94` (2022-08-31; Git tree `2bcf6ea76d74377ed09cedb5769399603a7c2ff3`; listing not truncated). No clone or upstream execution occurred. Resolvable blob identities, line locations and limited code evidence are recorded in `frame_binding_receipt.json`.

| Source at pinned commit | Source-bound fact | Implication and limit |
|---|---|---|
| `pipelines/cache_cmb.2019.py` | Actual loop includes MC200 and30GHz; loads FFP10 scalar and tensor alms; uses separate030A/030B QuickPol beams, NSIDE1024, polarized HEALPix synthesis; then RING→NESTED reorder and direct map write | The intended reference cache is a T/Q/U map in the input harmonic frame; the writer introduces neither sky-coordinate rotation nor U sign flip. Pixel reordering changes indexing, not physical frame or polarization convention. |
| Same cache writer | BL/WL path format uses the same `npipe6v20/quickpol` and030A beam names seen in the actual public prefix | Corroborates this producer path; not a unique content checksum or packaging receipt |
| `toast_planck/tod.py` | Default target coordinate is Galactic; detector pointing is transformed from ecliptic into that target | Establishes the pipeline's intended sampling coordinate frame |
| `toast_planck/signal_sim.py` and `preproc_modules/mapsampler.py` | Cached CMB map is sampled against detector sky positions without a map-coordinate conversion; sampler explicitly requires matching map and pointing frames | The reference map is intended to share the Galactic pointing frame, rather than remain ecliptic/equatorial |
| `toast_planck/pointing.py` | Polarized response uses Q cos(2ψ) plus U sin(2ψ) with the same pointing angles; cache synthesis is HEALPix polarized synthesis | Supports the standard HEALPix/COSMO Q/U lineage, with no inspected cache conversion to IAU |

The precise unresolved identity edge is now narrow: the writer names its30A cache `ffp10_cmb_030A_alm_mc_0200_nside1024_quickpol.fits`, while PLA supplies `npipe6v20_cmb_030_A_mc_00200.fits`. The inspected repository tree does not contain a delivery manifest or rename/packaging script connecting those two exact names. It also does not prove that this pinned snapshot was the exact historic executable that emitted the delivered bytes. Neither limitation is a reason to pretend that all frame information is absent; both are reasons to label the binding as source-supported inference rather than immutable exact-producer certification.

For an exploratory semantic intake, a declared Galactic/COSMO binding with these primary-source references is defensible. If a downstream frozen acceptance demands proof specifically for the exact delivered product, the remaining input is either an authoritative release declaration explicitly covering these simulation products or the cache→PLA packaging identity. This survey did not obtain that final edge and therefore does not mark exact-product frame proof PASS.

The actual NESTED-versus-RING difference remains mandatory: a future combination must put CMB and residual into the same pixel ordering, without introducing an IAU U sign flip. Units, pixel indexing and physical polarization convention are separate metadata. This addendum supplies no foreground uncertainty law, observed PR4 matching products, transfer/beam closure or statistic-specific coverage. Original L03 and all other original nodes remain HOLD.

No additional scientific payload or direct shell-network body was downloaded. The new transfers were GitHub connector metadata and selected source files; connector transport byte count is unavailable. This addendum and its receipt are the only new publication artifacts for this follow-up.
