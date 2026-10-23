# PR4 NPIPE one-realization observational design and diagnostic

Date: 2026-10-20. Owner: `obsstat`. Scope: Planck PR4/NPIPE 30 GHz MC00200 A/B CMB and residual product intake. Claim tier: `C0`, `DIAGNOSTIC_ONLY`; transfer source: none. The handoff preferred `gpt-6.1-sol/high`; the actual native worker request was `gpt-6-sol/high`; independently observed runtime: `UNKNOWN`. Base checkout: `7703dbf5b5aee38f50c348fde6a05f3ed77fbd7e`, branch `research/htt-open-input-theory-20261018`. This is a separate PR4 release lane; original PR3 L03 stays `HOLD`.

## Source and acquisition decision

The selected products are the exact four `NPIPE_030_{CMB,NOISE}_{A,B}_00200` IDs in [the frontier acquisition manifest](../ACQUISITION_MANIFEST.json). The four public PLA endpoints had already returned real FITS prefixes, and [the frame addendum](FRAME_BINDING_ADDENDUM.md) ties the intended cache producer to a Galactic HEALPix/COSMO convention. That binding is a source-supported inference; the exact producer cache to PLA packaging edge has not been demonstrated. [Planck's NPIPE release page](https://portal.nersc.gov/project/cmb/planck2020/) and [official simulation documentation](https://wiki.cosmos.esa.int/planck-legacy-archive/index.php/Simulation_data) provide the processing context. [The NPIPE release paper, section 4.1](https://doi.org/10.1051/0004-6361/202038073) supplies the release-wide K_CMB unit statement; the CMB FITS headers themselves omit `COORDSYS` and `TUNIT`.

The four maps are necessary for a one-realization, full-file schema and coordinate-index diagnostic. The selection does not initiate a 100-realization bank. The Planck release describes a fixed foreground realization and approximate preprocessing of simulations, so the quartet alone cannot calibrate foreground or statistic-specific coverage. All raw FITS files and create-only transport receipts stay under `/mnt/extdrive/workdir/htt_open_data/frontier20261020/planck/quartet/`, outside Git.

## Separate release-specific operator

The deterministic diagnostic is [pr4_quartet_diagnostic.py](pr4_quartet_diagnostic.py). It opens all four complete FITS products, checks each full file against the previously recorded 11,520-byte prefix, checks T/Q/U schema, NSIDE, pixel count and ordering, hashes the files, and samples 100,000 uniformly spaced **RING sky positions**. CMB columns are indexed by `healpy.ring2nest(1024, ring_index)` because their stored ordering is NESTED; residual columns use the RING index directly. The index round trip is checked. The script reports A/B means, standard deviations, correlations and difference RMS separately for CMB and residual, for each T/Q/U component. It additionally compares every stored A/B float32 pixel bit pattern in fixed 1,048,576-pixel chunks. It does not add a NESTED array to a RING array, form an observed-minus-simulation statistic, infer a noise-only null, or fit a model.

Run command:

```bash
.venv/bin/python docs/research_program/observational_publication_20261015/FRONTIER_20261020/cmb_astrometry/pr4_quartet_diagnostic.py --output docs/research_program/observational_publication_20261015/FRONTIER_20261020/cmb_astrometry/pr4_quartet_diagnostic.json
```

The resulting JSON is a descriptive analysis of one common CMB sky and one residual processing realization. A/B correlations cannot be read as independent-sky evidence. Pixel statistics are given the release-wide K_CMB and Galactic/COSMO **conditional** bindings, without converting them to a physical Bianchi transfer or using them for a p-value.

The [PNG](PR4_QUARTET.png) and [PDF](PR4_QUARTET.pdf) plot only the stored unequal-pixel fractions from this JSON; [PLOT_RECEIPT.json](PLOT_RECEIPT.json) binds the source and allowed use. Generate them with `.venv/bin/python docs/research_program/observational_publication_20261015/FRONTIER_20261020/cmb_astrometry/plot_pr4_quartet.py`; no FITS file is reread by the plotting step. `N−1` in the figure means one of the 12,582,912 T residual pixels has the same stored bit pattern in A and B. This plot is descriptive, not a null calibration.

## Observed one-realization result

The fetch completed with HTTP200 and create-only outside-Git receipts. Every file is exactly 151,001,280 bytes (604,005,120 bytes total); full-file hashes, prior-prefix hashes, FITS schema and all 12,582,912 T/Q/U pixels per product were checked. The complete hashes and numeric values are in [pr4_quartet_diagnostic.json](pr4_quartet_diagnostic.json). The four full SHA-256 values, in CMB A/B then residual A/B order, are `d3e7ce6f030b83353d772ef7fb0182d47026eb339e8c4fb0189f58f3605f4a4a`, `e439fb5e334adad0a9ac4d88a48edb00e3721a8e15b63ff5d912533097be6111`, `233f014d1bae1205617df652492df7cc02babdeced4e9a38e93c6a11f6d50dfa`, and `e2e3251ba113cf96eeec5afe732c32e66b8239a753ba838b2146891ac06bb443`.

| Field | CMB A/B unequal float32 patterns across 12,582,912 pixels | Residual A/B unequal patterns | Residual A/B Pearson correlation on 100,000 matched pixels |
|---|---:|---:|---:|
| T | 0 | 12,582,911 | 0.00960584 |
| Q | 0 | 12,582,912 | 0.00485033 |
| U | 0 | 12,582,912 | 0.00314281 |

All pixels in all six A/B field comparisons were finite and below the sentinel threshold. The delivered CMB T/Q/U arrays are bit-identical between A and B; the complete FITS files differ because their metadata include respective `030Ax030A` and `030Bx030B` QuickPol BL/WL paths. Shared CMB pixels are compatible with an intentional common realization. This observation alone does not determine whether the two beam functions are numerically equal or how the separately processed total maps respond. The residual values differ but their small single-realization sample correlations do **not** establish stochastic independence, matched foreground uncertainty, or coverage.

## Required contract before a PR4 null analysis

| Element | Current binding | Required next evidence |
|---|---|---|
| Index and polarization | Exact FITS ordering is CMB NESTED, residual RING; producer-code lineage supports Galactic/COSMO Q/U | Keep RING/NESTED conversion explicit; obtain exact delivered-product convention if a frozen acceptance needs it. No unmotivated U sign flip. |
| Simulation identity | MC00200 and 30 GHz A/B filenames and full-file receipts | Source-qualified pairing of CMB, residual, processed total and foreground terms; specify shared sky and fixed foreground. |
| Observed map | [NERSC observed Single-frequency index](https://portal.nersc.gov/cfs/cmb/planck2020/frequency_maps/Single-frequency/) lists 30 GHz full and ringhalf maps, but no exact equivalence to simulation A/B is established here | Identify actual PR4 A/B observed products with the same detector/split operator or derive and validate the mapping. Do not relabel ringhalf-1/2 as A/B. |
| Mask and weights | A [LoLLiPoP mask](https://portal.nersc.gov/cfs/cmb/planck2020/misc/) exists for its spectral pipeline; no 30 GHz A/B morphology mask is selected | Choose a statistic-specific observed/simulation common mask, apodization, weighting and selection rule. |
| Beam and transfer | CMB FITS BL/WL header paths refer to split QuickPol kernels; symmetric/asymmetric reference-map relationship is source described | Obtain the applicable 30 GHz A/B beam/window products and propagate mismatch through the exact operator. |
| Foreground and null | The official simulation description includes one foreground realization and approximate preprocessing | Obtain matched processed total/component products or a justified foreground uncertainty model; test correlation, held-out injection, noise reuse and coverage at the chosen statistic. |

The public [LoLLiPoP archive](https://portal.nersc.gov/cfs/cmb/planck2020/likelihoods/planck_2020_lollipop.tar.gz) is a separate EE/BB/EB spectral comparator. Its compressed spectra and covariance cannot stand in for these all-m maps or the joint null law. The [multi-detector index](https://portal.nersc.gov/cfs/cmb/planck2020/frequency_maps/Multi-detector/) lists some observed detector combinations but establishes no exact 30 GHz A/B observed match in this intake.

## Claim audit and stopping rule

| Claim | Owner / evidence | Status and limit |
|---|---|---|
| Public MC00200 quartet is physically readable and has mismatched stored ordering | `obsstat`; complete FITS and hashes | `DIAGNOSTIC_ONLY`; transport/schema/pixel sample only. |
| Intended Galactic/COSMO convention and K_CMB units | `obsstat`; pinned producer and official release metadata | `CONDITIONAL`; exact cache to PLA packaging and absent header cards remain explicit. |
| PR4 null adequacy or original PR3 L03 acceptance | `obsstat`; no matching observed/foreground/selection/coverage experiment | `HOLD`; no promotion from this diagnostic. |
| Physical polarized Bianchi all-m atlas for B02 | `bass_py`/external solver; bounded source search | `HOLD`; the PR4 CMB maps and Sung figures are not a Bianchi transfer atlas. |

No original DAG node is marked complete. The next PR4 action is an observed A/B and processing-contract source intake followed by a preregistered single-statistic pilot. Stop before numerical null claims if any observed split, mask, beam, foreground, or selection binding remains missing. Do not repeat the existing PR3 eight-row bank or the B02 temperature-only fixture.
