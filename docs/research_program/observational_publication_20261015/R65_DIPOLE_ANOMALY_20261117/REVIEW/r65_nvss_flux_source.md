# R65 R8 bounded NVSS integrated-flux source qualification

R9 terminology clarification: the active label is **provider peak (`peak_flux`)**.
The historical phrase "provider corrected peak" below described numerical
consistency with known corrections, not a verified provider extraction or
correction pipeline. All original range-read and cross-match evidence is retained;
no exact provider correction history is certified by this note.

Date2026-11-17. This lane performed read-only HTTP range/header/source reads and a ten-object nearest-coordinate comparison to the existing NVSS FITS. No complete catalogue download, production fit, native write, or test rerun was performed. Root reports current R7 completion24tests/8models/512bootstraps; this note does not independently verify or replace that result.

**Decision:** `Full_NVSS_combined_named.dat` is a concrete, feasible provider-released integrated-flux carrier, distinct from the actual raw FITS peak-intensity carrier. It is appropriate to intake and hash it for a bounded integrated-flux refinement if parent selects that extension. This closes a real choice-of-flux-estimand risk, rather than introducing a speculative source or a new source-size cut. It does not by itself certify every morphological, completeness, spectral-response, or cosmological-covariance assumption.

## Exact source and bounded read

Asset URL: https://github.com/o-oayda/cracking-into-racs-i/releases/download/v1.0.0/Full_NVSS_combined_named.dat

Read HTTP `Range: bytes=0-4095`; returned206, Content-Range `bytes 0-4095/140767191`, Content-Length4096; read4096bytes then closed. A second4096-byte range read supplied the tiny cross-match table. No full-file SHA verification is claimed here. Directly read version-pinned https://raw.githubusercontent.com/o-oayda/cracking-into-racs-i/v1.0.0/required-data.yaml binds filename to SHA256 `52eb576c1e3e71837f2fca26121789ccc0b316152cca3f25ea2f37ea8ef5a38e`.

Actual header:

```
source_name ra dec integrated_flux integrated_flux_unc peak_flux peak_flux_unc
```

Labels alone do not certify flux semantics. Two independent additional links were examined: the provider's actual flux-ratio code and original-survey authoritative documentation; an actual coordinate cross-match also rules out the existing FITS column secretly containing the same integrated quantity.

## Provider computation and units

Version-pinned source: https://raw.githubusercontent.com/o-oayda/cracking-into-racs-i/v1.0.0/scripts/figx-racs-nvss-temp.py . Directly read relevant source lines:

- Lines23–25: FLUX_MIN=15, CROSSMATCH_RADIUS=5.
- Lines104–111: `Table.read`, fallback `format='ascii'` for the text catalogue; no hidden column replacement.
- Lines129–134: `scaled_nvss_flux = common_sources['B_integrated_flux'] * (nu_RACS/1400 MHz)^(-alpha)` and ratio `A_Total_flux/scaled_nvss_flux`.
- Lines175–178: cuts on RACS `Total_flux` and NVSS `integrated_flux`, both minimum15, with no NVSS numerical unit conversion.
- README v1.0.0 lines27–40 names this file the NVSS catalogue used for Figure2 flux ratios; lines91–99 explain RACS total-flux library inputs must be mJy and mid1 Jy must first be converted to mJy.

Therefore the provider computation operationally treats named.dat `integrated_flux` as **mJy** and `peak_flux` as the separate peak field. This is an implementation/source-unit binding, not a units attribute contained in the plain-text header. The exact conversion/extraction program producing this named table from the original NVSS catalogue was not located in this bounded source check. Provider data identity and original-catalogue semantic identity remain distinct.

## Crucial direct cross-match against actual existing FITS

Reference FITS `/mnt/extdrive/workdir/raw/new_acquisitions/radio_hi/NVSS_nrao_20261110/CATALOG.FIT` was read using Astropy. First10 complete provider rows were matched by nearest RA/Dec using `SkyCoord.match_to_catalog_sky`. All separations are below.165arcsec. Values below are actual read numerical values, not inferred from column names.

| Source suffix (all NVSS J) | Separation arcsec | FITS PEAK INT×1000 | named peak_flux | named integrated_flux |
|---|---:|---:|---:|---:|
| 000000.09-340709.5 | .164464 | 2.482695 | 2.7 | 2.7 |
| 000000.13-382628.5 | .087153 | 2.387630 | 3.1 | 3.1 |
| 000000.16-040242.3 | .101488 | 104.102530 | 106.8 | 106.8 |
| 000000.18+321233.3 | .093845 | 3.575946 | 3.7 | 3.7 |
| 000000.19+491812.6 | .103465 | 2.024677 | 2.4 | 2.4 |
| 000000.25-200448.8 | .128421 | 4.077286 | 4.3 | 7.6 |
| 000000.39+004100.0 | .129123 | 82.667351 | 82.9 | 149.5 |
| 000000.40-181729.3 | .126277 | 2.104166 | 2.3 | 2.3 |
| 000000.69-325929.1 | .125029 | 3.444414 | 3.9 | 3.9 |
| 000000.71-102244.8 | .121829 | 2.336496 | 2.7 | 2.7 |

The two resolved examples are decisive against the interpretation that raw `PEAK INT` secretly stores integrated flux. For J000000.39+004100.0 the existing FITS peak82.667mJy/beam is close to the provider corrected peak82.9, whereas integrated149.5 is substantially larger. The slight raw-versus-provider peak differences are consistent with survey bias correction and numerical rounding, but no exact correction formula was fitted/validated here. Raw and provider catalogue positions also differ slightly, so row-index or exact-coordinate equality is not the appropriate identity claim.

Current FITS header independently has `EXTNAME='AIPS VL'`, PEAK INT `JY/BEAM`, MAJOR AX/MINOR AX `DEGREE`,1810672rows. This is additional evidence, not the sole semantic argument.

## Authoritative original-survey semantics

Directly retrieved NRAO survey authors' catalogue help:
https://www.cv.nrao.edu/NVSS/NVSShelp.html

Read sections introductory Gaussian components, raw/fitted/deconvolved modes, and Sizes. It explicitly distinguishes raw/fitted component peak brightness from deconvolved component integrated flux; raw values lack amplitude-bias correction. Extended astrophysical objects may be represented by multiple Gaussian components. Consequently the provider integrated value is a source/component total-flux quantity under that catalogue convention, not a promise that all lobes/components of one physical galaxy have been grouped.

NRAO survey authors' main page https://www.cv.nrao.edu/nvss/ says source catalogues were constructed by elliptical-Gaussian fitting and that browser/NVSSlist correct raw entries for known biases using Condon1997. Catalogue description link resolves to `catalog.ps`, which the web renderer cannot parse; no claim is made to have read that PostScript. Official search help above was successfully read and supplies the needed distinction.

NASA/HEASARC survey ingest documentation https://heasarc.gsfc.nasa.gov/W3Browse/catalog/nvss.html identifies its original `NVSSCatalog.text.gz` provenance and defines Flux_20_cm as integrated1.4-GHz flux in mJy. This is corroborating survey documentation, not proof that named.dat was produced from that exact HEASARC ingest. Its historical June2009 digit-ingest correction must not silently be attributed to provider table production.

## R8 refinement admission and limits

- **Established by direct data comparison:** current R65 baseline is genuinely raw peak-intensity selected; the named release contains a numerically distinct integrated field. No reclassification of existing PEAK INT as integrated is justified.
- **Source/implementation supported:** the provider release treats that integrated field as mJy in the physical RACS/NVSS flux-ratio calculation and pins exact full-file SHA.
- **Admissible next action:** parent may intake the140767191-byte release, verify SHA, preserve it separately, and run the same fixed quotient/bin experiment with integrated-flux selection as an explicitly new input/estimand. Keep the peak-intensity result for comparison, do not overwrite/relabel it. Use the named integrated-versus-peak columns for paired comparisons on matched objects where relevant.
- **Not automatically resolved:** beam-convolved source selection/morphology, the parent catalogue's peak-brightness detection threshold, flux-bias correction, unresolved multi-component grouping, spectral-alpha response, and LSS/cross-survey covariance. Integrated flux is the appropriate starting observable for the point-source Ellis–Baldwin flux transformation, but sample completeness and angular-size/morphology changes can still modify actual selection response. No new source-size restriction is introduced in this note.
- **Prior R2 wording clarification:** “NVSS has no integrated-flux column” applies to the current18-column raw FITS, not to every public NVSS product. It must not be used as a universal unavailable-input claim. The source gap is concretely repairable with this release. Exact original extraction provenance remains inherited provider provenance, not an excuse to stop the bounded actual-data sensitivity calculation.
