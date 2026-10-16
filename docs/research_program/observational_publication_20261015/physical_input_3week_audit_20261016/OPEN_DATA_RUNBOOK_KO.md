# 공개 자료 수집 실행계약: 최소 자료 세트, 로컬/외부 분할

날짜 2026-10-16; DB/API 검색으로 확인된 파일명이나 릴리스만 입력하며 원 출처 다운로드를 아직 완료했다고 주장하지 않는다.

## H02 우선

- 공개 VizieR catalog `J/ApJ/944/94`, `table2.dat` (55,877 individual galaxies), `table3.dat`, `table4.dat` (각 38,053 group). 공식 readme `https://cdsarc.cds.unistra.fr/viz-bin/ReadMe/J/ApJ/944/94`에서 column offsets, `1PGC`, RA/Dec, DMzp/eDMzp, Vh, V3k 및 Tully–Fisher, FP, SN, calibrator flags 확인. 실다운로드 후 file bytes SHA256 and table lengths.
- Method group overlap graph 1PGC and galaxy member IDs; only attach table4 derived Dist/Vpec as reporting variables, not independent truth labels.
- Public frame/selection: photometric survey W1/FP and observational method completeness references; data releases lacking measured completeness -> selection model family and explicit unresolved status. Prerequisite raw catalogue does not itself solve H02.
- Existing code `htt/htt/htt/infer/cf4_product_provider.py`, `r7_joint_experiment.py`, `htt/src/common/structured_inference.py`. Execute subset 50–500 source groups first, then 38,053 streaming; compare source 35,970. Controlled negative-test removal of selection normalization, method zero-point degeneracy, cross-covariance zeroing to detect false precision.

## L03 next

- PLA official PR3 component maps full/HM/OE T/Q/U (as released per method), *exact separately issued* temperature/polarization confidence masks, effective beam transfer and HEALPix pixel window, component-separation specifications. From `https://wiki.cosmos.esa.int/planck-legacy-archive/index.php/CMB_maps`.
- FFP10 one independent CMB realization per simulation ID, mapped component separation products 999 CMB (`*_cmb_mc_?????_raw.fits`) + 300 E2E residual/noise (`*_noise*mc_?????_raw.fits`), match instrument/product/split. `https://wiki.cosmos.esa.int/planck-legacy-archive/index.php/Simulation_data`.
- Start 8-32 validated independent CMB realization IDs & 8-32 residual IDs for pipeline smoke and coverage diagnostic only, then 300+999 candidate bank on external disk/HPC. Full systematic/null admission requires instrument-matched set, not small smoke sample. Do not multiply splits into independent sky count.
- T NSIDE64 RING 26,846 selected vs old R2 support 36,433: archived transforms and mask hashes; E/B genuine spin-2 native parity/check high-ell.
- Alternative independent release NPIPE 2020 600 available simulation realisations, **separate** processing/mask/beam conventions; not silently pooled with PR3.

## B02 physics subset

- AniCLASS GitHub `https://github.com/CyrilPitrou/aniclass` + archive already retained in connected Dropbox (10,616,213 bytes, Dropbox content hash only). Record commit SHA and archive content SHA256, actual compilation, `bianchi.ini` version; five near-FLRW branches only.
- `https://github.com/lesgourg/class_public` FLRW benchmark; recombination history and polarized LoS spin conventions; mode-specific IC and ell/step convergence/injection.
- Accept five-type verified subset separately if target paper scope explicitly changed, never auto-complete whole eleven-type original B02 claim.

## K03/V03/K04/S04 ancillary

- Gaia DR3 quasar CRF3 proper-motion VSH, covariance/frame systematics and quasar IDs (observer solar acceleration calibration only), open DR3 catalogue URL and ADQL query locked at execution. Sourceward convention and distance to transverse velocity not supplied by Gaia quasar alone.
- Pantheon+ DataRelease `Pantheon+_Data/4_DISTANCES_AND_COVAR`, `2_CALIBRATION`, released simulations (`https://github.com/PantheonPlusSH0ES/DataRelease`); existing CF4 overlap resolved by shared source IDs; do not assume public full Biascor independent mocks available.
- DESI DR1 public BGS group VAC and EZmock/Abacus realized windows at `https://data.desi.lbl.gov/doc/releases/dr1/` for independent cross-check, not a CF4 selection surrogate.
- ACT DR6 `https://act.princeton.edu/act-dr6-data-products` T/Q/U and cross/null maps; kSZ remote dipole requires electron optical depth astrophysical model and cluster/tracer catalog, no generic tilt inference from T map.
- Optical source model: exact same congruence `H=θ/3`, sourceward acceleration dipole -A.n/c and shear STF2; K04 finite-z affine Jacobi/observer/source velocities/distance selection. Only certified, open kernels can promote posterior; missing sectors unbounded rather than zero.

## Reproducibility and storage contracts

Inputs pinned by `source_uri`, release, logical observation identifier, downloaded filename, byte count, SHA256, FITS/HDU/mask/beam ordering/unit/frequency, physical frame, license, `selection_id`, and correlated split membership. Recorded source assertions cannot be replaced by filenames. Start under 4GB retained small cuts; external data footprint determined only after actual file count/size HEAD or returned archive metadata. Heavy Planck/high-resolution product banks streamed or delegated to user-provided HPC, not assumed in present ChatGPT sandbox. User has approved research, not main merge or journal submission.

Positive gate needs exact original likelihood or justifiable partial identification set, source selection and systematics, physical response, expected calibration, independent heldout injection/recovery, and a primary publication comparator. Failure state remains `UNRESOLVED_PHYSICAL_INPUT` without declaring strong no-go.
