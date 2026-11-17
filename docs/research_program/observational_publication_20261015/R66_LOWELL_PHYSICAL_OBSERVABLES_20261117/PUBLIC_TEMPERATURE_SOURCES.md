# R66 R8 public Commander temperature simulation lookup

Task date 2026-11-17. Bounded lookup only; no full simulation/map download, no account/login, no restricted NERSC filesystem access, no SEVEM bank. This is an input-scope/product-selection issue, not a mathematical no-go.

## Concrete result from complementary public catalogue evidence

Parent/history agent reports the actual full public PLA catalogue contains **100 additional Commander files**
\`npipe6v20_commander_cmb_mc_0200.fits\` through
\`npipe6v20_commander_cmb_mc_0299.fits\`,
each **1,610,622,720 bytes**. The exact public retrieval scheme, using the already-established PLA product API, is:

- First row: https://pla.esac.esa.int/pla/aio/product-action?SIMULATED_MAP.FILE_ID=npipe6v20_commander_cmb_mc_0200.fits
- Last row: https://pla.esac.esa.int/pla/aio/product-action?SIMULATED_MAP.FILE_ID=npipe6v20_commander_cmb_mc_0299.fits

**Evidence state:** exact names and byte sizes are catalogue evidence reported by the parent/history agent, not independently re-fetched by this worker. Root is range-reading the 0200 FITS header and verifying its temperature content. This worker intentionally did not duplicate that read. Attach root's resulting HDU/NSIDE/TTYPE/TUNIT and raw-value receipt before calling these implementation-verified temperature simulations. Byte size alone does not prove NSIDE, numeric representation, units, or nonzero T.

These exact filenames differ from the already processed bank in *both* realization range and naming:
\`npipe6v20_commander_cmb_2048_mc_0300_005a.fits\` through0399
is not the same product. Do not silently reinterpret its zero T placeholder as a usable temperature null.

## Independent primary/documentary comparison

1. **Aluri & Patel, arXiv2506.22795v1, §3 and AppendixA**, full text actually read:
   https://arxiv.org/html/2506.22795v1 .
   It states that the observed Commander temperature map is HEALPix NSIDE4096, Gaussian FWHM5arcmin, and retains the dipole; their100 complementary Commander temperature simulations have the **same4096/5arcmin resolution**. The paper states these mock data are available at NERSC and does **not** give the exact simulation basename. It therefore supports the expected *physical/data class* but does not by itself identify the public0200 filename. Their5000 ideal CMB realizations are separately generated, not replacements for a matched component-separated E2E null bank.

2. **Official ESA PLA CMB_maps documentation**, NPIPE section, actually read:
   https://wiki.cosmos.esa.int/planck-legacy-archive/index.php/CMB_maps .
   It explicitly distinguishes Commander **temperature4096 from polarization2048**: observed map HDU1 is the single T map; HDU2 contains Q/U. This makes a2048 polarization product with zero temperature column a plausible product-class explanation, but the actual zero-column statement comes from root's direct data audit. Do not elevate this plausibility to an independently verified simulation header description.

3. **Official ESA PLA Simulation_data documentation**, NPIPE simulation section, actually read:
   https://wiki.cosmos.esa.int/planck-legacy-archive/index.php/Simulation_data .
   It gives a Commander simulation template with an NSIDE field and optional resolution suffix and uses
   \`npipe6v20_commander_cmb_2048_mc_0300_005a.fits\`
   as its concrete link. The same section inconsistently describes realization0200–0299 and introduces foreground-subtracted frequency/subset language. Therefore it is insufficient as a sole product selector. The full catalogue plus actual header/data must outrank this ambiguous prose.

4. The public NPIPE landing page
   https://portal.nersc.gov/cfs/cmb/planck2020/
   was read as a public webpage only. It distinguishes “some” publicly exposed products from full NERSC filesystem access, and its top-level links do not identify the desired Commander0200 bank. No NERSC account, login or restricted filesystem was accessed.

## Negative checks, carefully bounded

Before the full catalogue finding arrived, HEAD requests were made only to four schematic4096 replacements:
\`npipe6v20_commander_cmb_4096_mc_0300_005a.fits\`,
\`npipe6v20_commander_cmb_4096_mc_0300.fits\`,
\`npipe6v20_commander_cmb_4096_mc_0200_005a.fits\`,
\`npipe6v20_commander_cmb_4096_mc_0200.fits\`.
All returned404. A HEAD control for the known2048_0300_005a product returned200 and FITS Content-Type. No bodies were downloaded. These checks show only that those four guessed basenames are wrong, **not** that temperature simulations are absent. The subsequently located exact public basename has **no4096 token**.

Exa and a bounded independent web search did not index the exact desired public filename. This was a search/catalogue gap, not evidence of nonexistence. A malformed/unsupported public metadata API probe returned errors; no conclusion about catalogue content was drawn from it.

## Acceptance handoff

The minimal scientific completion is to bind catalogue identity to root's real header/raw-T receipt for0200, establish T nonzero and correct native units/NSIDE/order/beam and whether scalar-only or signal+noise/systematics, then process exactly the chosen public100 rows through the same native common-sky operator as the observed Commander map. Preserve the0300–0399 bank's zero-T failure as a product-scope rejection. It is not a failure of STF geometry, photon stress mapping, quotient construction, or covariance algebra.

No additional literature or broad product search is required after this catalogue+header route succeeds.


## Addendum: root header and units-specific check

Root subsequently reports exact0200 public product opens with HTTP200. Its FITS layout is RING, NSIDE4096, one \`I_Stokes\` column, \`TFORM1=1024D\`,196608 rows,1,610,622,720bytes; \`TUNIT1\` is blank. These are root's direct header findings, not a duplicate read here.

The official NPIPE paper, Planck intermediate results LVII, [A&A643,A42(2020), §4.1](https://www.aanda.org/articles/aa/full_html/2020/11/aa38073-20/aa38073-20.html), states that all NPIPE maps are calibrated to thermodynamic kelvins(K_CMB). The nearby text covers frequency-map products and857GHz conversion. This is authoritative general release calibration evidence, but the exact bare Commander temperature MC product is not named in that unit statement.

An exact producer-code caveat exists. The official [planck-npipe/toast-npipe](https://github.com/planck-npipe/toast-npipe) tree at commit \`669becf0c52ec10731318076e7909d2d015c1a94\` contains:
[transfer_function/measure_bias_commander.py](https://github.com/planck-npipe/toast-npipe/blob/669becf0c52ec10731318076e7909d2d015c1a94/transfer_function/measure_bias_commander.py).
Lines100–111 load the **different** product
\`npipe6v20_commander_cmb_mc_{:04}_005a_2048.fits\`
and multiply its map by \`1e-6\`. Line112 then replaces its temperature column with a dipole template. This is direct implementation evidence for microkelvin-to-kelvin conversion in that2048polarization-oriented product. It does **not** establish units of \`npipe6v20_commander_cmb_mc_0200.fits\`, whose native4096 scalar T representation is different.

Therefore: **the exact bare4096T product's numeric unit remains unresolved by the primary/code evidence found here**. General NPIPE K_CMB prose and the other product's1e-6 conversion must not be conflated. A measured amplitude or C_l consistency check can discriminate an implementation mistake and should be retained, but should be labelled numerical/semantic calibration evidence rather than an explicit producer declaration. If no stronger provenance is available, retain the unit choice as a stated source-qualified assumption with its evidence, rather than claim exact product metadata verified it.
