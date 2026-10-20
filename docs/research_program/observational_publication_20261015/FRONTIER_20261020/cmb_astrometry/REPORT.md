# Bounded CMB / astrometric source frontier, 2026-10-20

Owner: obsstat research-input survey; author `/root/cmb_astrometry_sources_20261020`; parent is sole publisher. Requested backend: gpt-6.1-sol/high; observed backend: UNKNOWN. Scope: new anonymous public inputs for L03/V03/B02/K03 after `69870ee249cd98a869f35e442105d17c927d28fc`. Claim tier C0; DIAGNOSTIC_ONLY source qualification. No transfer, solver, likelihood, confidence coverage, or physical family result was generated.

The strongest new route is **Planck PR4/NPIPE**, with a real anonymous signal/residual A/B quartet verified at the FITS-header level. It is a different processing release from the cached PR3 analysis. It does not close original L03. A new Sung–Coles source archive and a real released polarized spectral likelihood were also inspected. Neither supplies a physical all-m atlas or an all-m matched null ensemble. No source-qualified new V03 or K03 executable physical response was identified in this bounded search.

## Evidence and policy read

Read fixture AGENTS.md, CURRENT_CODEX_RUNTIME.md, PUBLICATION_DAG.json, RESUME.md, PUBLICATION_ASSESSMENT_KO.md, and repo-local `htt-transfer-provenance`, `htt-claim-firewall`, `htt-claim-provenance-ledger` skills. Exa and SciSpace were used. SciSpace returned mostly known Bianchi papers and older Gaia/radio frame papers; it did not identify a new numeric physical payload. Existing Gaia 1,614,173/radio713 analysis, PR3 splits, HFI beam archive, BIANCHI temperature fixtures, AniCLASS chains/movies and previously inspected arXiv bundles were not rerun or reacquired.

## New sources and actual consumption

| Source | What was actually checked | Decision |
|---|---|---|
| [Official NPIPE simulations](https://wiki.cosmos.esa.int/planck-legacy-archive/index.php/Simulation_data), [release paper](https://arxiv.org/abs/2007.04997), [NERSC release](https://portal.nersc.gov/cfs/cmb/planck2020/) | Official simulation documentation; anonymous prefixes of five actual FITS products, including paired 30GHz MC00200 CMB A/B and residual A/B | New alternative release route; semantic qualification before any bulk acquisition |
| [Official LoLLiPoP data](https://portal.nersc.gov/cfs/cmb/planck2020/likelihoods/planck_2020_lollipop.tar.gz), [author code documentation](https://github.com/planck-npipe/lollipop) | Full 6,217,890-byte archive, three members; real table and covariance parsed | Spectral likelihood source only; no all-m data or ensemble |
| [Sung–Coles 1004.0957v2](https://arxiv.org/abs/1004.0957v2) | New 5,714,113-byte source bundle, gzip CRC and 71-member archive inventory | 64 PostScript figures + 7 TeX/style files; no serialized map/alm/history payload in this bundle |
| [Karbon–Nothnagel A&A630 A101](https://www.aanda.org/articles/aa/full_html/2019/10/aa36083-19/aa36083-19.html), [CDS ReadMe](https://cdsarc.cds.unistra.fr/ftp/J/A+A/630/A101/ReadMe) | Primary paper, anonymous directory and ReadMe | Genuine full cross-source *position* covariance; not the radio proper-motion/Gaia joint calibration law required by K03 |
| [CMB-S4 PR4 lowres portal](https://data.cmb-s4.org/planck_pr4-lowres.html) | Exact linked manifest and one 143GHz ns16 map requested | Both HTTP404 on 2026-10-20; no data acquired, no alternative path guessed |

Public access is separate from licensing. Anonymous HTTP200 was actually observed for the NPIPE prefixes and LoLLiPoP archive. A LoLLiPoP code GPLv3 badge does not establish the separate data licence. The source licences for NPIPE products, Sung source and CDS products were not independently established in this survey. No login/session was used and no access restriction was bypassed.

## NPIPE quartet: concrete qualification result

`minimal_acquisition_candidate.json` gives exact anonymous URLs with `auto_fetch:false`. The successfully probed quartet is `npipe6v20_{cmb,noise}_030_{A,B}_mc_00200.fits`. Each request specified Range 0–11519, but the server returned HTTP200 chunked responses rather than HTTP206. The reader stopped after 11,520 bytes per request; these are prefix probes, not complete-file or numerical-map validations.

All four first BINTABLEs contain TEMPERATURE, Q_POLARISATION and U_POLARISATION, float32, NSIDE1024, 12,582,912 pixels. **CMB uses NESTED ordering; residual uses RING.** Residual headers explicitly say Galactic. First CMB headers omit COORDSYS and TUNIT; official NPIPE release paper §4.1 and the NPIPE subsection of [Frequency_maps](https://wiki.cosmos.esa.int/planck-legacy-archive/index.php/Frequency_maps) state NPIPE maps are in thermodynamic kelvins. Application of that release-wide unit statement to these particular simulation products must remain explicit; a CMB frame/polarization convention binding is still needed before numerical combination. Header dimensions imply first-table file extent 151,001,280 bytes each, or 604,005,120 bytes for four first-table extents. These are not remotely measured complete file sizes and are not a whole-experiment download budget.

The official simulation description gives 600 generated realizations, of which 100 are supplied through PLA, including A/B splits. It says full simulations contain beam-convolved CMB, Commander foregrounds, zodiacal and bandpass terms, gain fluctuations and correlated noise, processed with the same reprocessing module. Preprocessing is approximated by measured noise PSDs. **The foreground sky has one fixed realization.** Residual maps remove regressed input signals; they are not automatically a sample of all foreground uncertainty. An A/B pair shares the physical sky; two splits do not become independent skies.

The official wiki says matching SEVEM-processed CMB/noise products exist but does not provide an exact SEVEM filename template in its NPIPE section. The Commander template mixes four/five-digit realization examples and includes an example outside the stated 0200–0299 interval. One literal ns16/0200 instantiation returned404. This failure is specific to that attempted URL, not an absence result for Commander products. NERSC anonymous directories inspected here list observed frequency maps, not the requested component-separated simulation ensemble. Existing Commander/SEVEM maps and simulations are discussed in 2024–2025 papers, but discussion alone is not verified payload access.

The minimal next decision is a **semantic intake task**, not 100-realization bulk acquisition: bind the CMB coordinate and Q/U convention, release units and asymmetric/symmetric beam relation; identify actual total-output/foreground or component-separated products and their paired indices; specify the same observed PR4 A/B maps, masks, transfer treatment and cleaning selection. Only then decide a bounded one-realization experiment and its additional byte budget. No observed30GHzA/B filenames are certified by this report. The experiment also needs observed maps, masks, beams and foreground controls beyond this quartet. Same-processing and statistic-specific coverage remain original requirements. Replacing PR3 observations with PR4 must be an explicit alternative lane, preserving original L03 HOLD.

## LoLLiPoP numerical payload inspection

The archive contains `cl_lolEB_NPIPE.dat` (30,186 bytes), `clcov_lolEB_NPIPE.fits` (6,442,560 bytes), and a fiducial spectrum (29,900 bytes). Actual table:299 rows, four columns, ell2–300, all finite. Actual covariance:897×897 big-endian float64 image, all finite, exactly symmetric in stored double values. Diagonal range 9.514689600904137e-10 to0.0016849076716009212. Positive-definiteness and the likelihood were NOT_RUN. The author documentation associates this likelihood with EE/BB/EB cross-spectra from Commander applied separately to detector-set splits. This is lossily compressed spectral information; it cannot restore m-dependent tensor morphology, A/B map response, or a joint foreground ensemble. The diagnostic establishes payload content, not cosmological likelihood validity.

## B02/V03 and K03 limits

The new Sung source expands the checked public release surface to models I/V/VII0/VIIh/IX, but its rendering assets cannot be relabelled sampled physical coefficients. The source came as a 5,000,000-byte prefix plus a714,113-byte HTTP206 suffix. gzip CRC passes and all71 entries parse. Range responses had differing opaque `sha256:` ETags; the locally computed complete SHA is internal integrity metadata, not a verified upstream ETag match. No exact upstream-byte identity claim follows. No solver, ODE, image digitization or figure-to-atlas conversion was run.

CDS releases the Karbon–Nothnagel covariance as decomposed lower triangles, odd rows RA and even rows declination, units mas², for4567/4617 source positions. Directory sizes are388M/397M compressed, so matrices were not downloaded under the20MB cap. This could support a distinct positional frame comparison. It does not supply proper-motion cross-source errors, Gaia–radio joint errors, source-matched NNR transfer, clocks, or the same-congruence nonradial kernel. No positional data were substituted for K03 inputs.

## Claim audit and handoff

| Claim | Owner | Status / evidence | Required limitation |
|---|---|---|---|
| Anonymous PR4 quartet endpoints and differing ordering | obsstat | DIAGNOSTIC_ONLY / actual prefix metadata | Full-map numerical and semantic agreement not tested |
| Released LoLLiPoP table/covariance content | obsstat | DIAGNOSTIC_ONLY / actual finite parsing | No all-m/null coverage inference |
| No numeric atlas in this Sung source bundle | bass_py research intake | DIAGNOSTIC_ONLY / bounded archive inventory | Not universal public absence |
| Public multifrequency positional covariance | obsstat | DIAGNOSTIC_ONLY / primary documentation | Not K03 proper-motion law |

No scientific claim was upgraded or downgraded; no permanent claim ledger or original DAG state was changed. Original17/42 completion and L03/V03/B02/K03 HOLD remain. The proposed changes are a source registry, bounded acquisition decision and report; tests performed are archive/format/finite/header checks only. Kill switches: wrong processing release, unbound frame or units, ignored ordering, no matching foreground product, or statistic coverage not justified. No further numerical rerun is recommended from these inputs alone. The bounded failure to find a new physical atlas/global-history or K03 response is not a universal nonexistence or no-go assertion.

Incremental direct successful response bodies materialized/read in this worker:12,695,326 bytes, including metadata pages and five11,520-byte map prefixes. This excludes connector-internal transfers and unavailable error-body sizes. New numeric/source archives:11,932,003 bytes; new map-prefix reads57,600 bytes. Cached scientific payload reacquisition:0 bytes. Some local files duplicate prefixes/reassembled sources, so local disk usage is not the network total. Raw archives, maps and full upstream HTML/code are excluded from the publication file list.
