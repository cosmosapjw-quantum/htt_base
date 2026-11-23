# R99 acquisition sources and independent radio outer support

## Scope and evidence state

This C1–C8 lane prepares D01/D02/D05 data acquisition and executes the independent outer-footprint calculation specified in `THEORY_CROSS_DATA.md`. The source baseline is `eee33d7ed33e1af10d7c6a3c453810ecb227e461`; the completed theory handoff is `575ff4811b6a5ae12d7c14bf7cd8ecadef7e58aa`.

**Implementation-verified:** stable acquisition jobs, bounded provider source capture, exact identifier handling, deferred-response rejection, polygon union, HEALPix exposure, comparison to the existing sealed R98 source-count maps. **Unresolved:** CF4 upstream joint calibration likelihood, historical selection and rejected-target genealogy, LoTSS valid-weight/RMS holes and completeness, and a matched Commander joint null. No physical Pi, GF, cosmological p-value or publishable dataset gate is promoted.

The actual 13 saved responses total **847,746 bytes**, including **17,408 bytes of science-file prefixes**. No whole raw science catalogue, mock archive, RMS archive or Commander FITS was downloaded. Published checksum values below are provider assertions; only the saved response bytes have locally verified SHA256 values. `inputs/source_receipts.json` records each stable URL, UTC time, status, selected headers, byte count and local SHA256.

## D01/D02: SDSS PV v1.1.0

Official record: [Zenodo 6824749](https://zenodo.org/records/6824749), DOI `10.5281/zenodo.6824749`. The version in the captured [record API](https://zenodo.org/api/records/6824749) is **1.1.0**. Version 1.0 rounded `specObjID`; do not combine that damaged identifier column with v1.1.0 without an explicit correction.

| Job/product | Stable content URL | Exact bytes | Provider MD5 | Current evidence |
|---|---|---:|---|---|
| `sdss_pv_v1_1` | https://zenodo.org/api/records/6824749/files/SDSS_PV_public.dat/content | 20,231,640 | b5b6e31caf7ea469c2ac2cb775fa8d14 | HTTP206 prefix bytes0–8191 |
| `sdss_randoms_v1_1` | https://zenodo.org/api/records/6824749/files/SDSS_randoms_public.dat/content | 284,000,071 | 8627b4063e8a71572e333e0ac65d6657 | HTTP206 prefix bytes0–1023 |
| `sdss_mocks_v1_1` | https://zenodo.org/api/records/6824749/files/mocks.tar.gz/content | 10,643,218,721 | 9ba3e8876f6f08a2af00d30cbf1c6cd9 | Metadata only |
| Data description | https://zenodo.org/api/records/6824749/files/data_description.pdf/content | 74,681 | cb25c71ad9078d61ebdd9882f991c7e9 | Full small PDF saved |
| Mock description | https://zenodo.org/api/records/6824749/files/mock_description.pdf/content | 82,919 | cfa6859a65850e45d195a81993ceb5f7 | Full small PDF saved |

The actual catalogue header, retained in `inputs/sdss_pv_prefix.txt`, is:

```text
PGC coords objid specObjID plate RA Dec l b
deVMag_g deVMagErr_g deVMag_r deVMagErr_r deVRad_r deVRadErr_r
deVAB_r deVABErr_r extinction_g extinction_r kcor_r kcor_g absmag_r
zhelio zhelioerr zcmb SIGMA_STARS SIGMA_STARS_ERR
IDgroupT17 NgroupT17 zcmb_group M in_mask nbar
r er i ei s es Sn
logdist logdist_err logdist_alpha
logdist_corr logdist_corr_err logdist_corr_alpha
```

The random header is `RA Dec zcmb nbar`. Identifier lexemes must be parsed as exact integers or decimal strings; `exact_identifier` rejects an already rounded floating-point input. The author documentation recommends matching photometric `objid` to spectroscopic `bestobjid`; the original `objid` was unaffected by the v1.0 spectroscopic-ID defect.

The captured data description fixes the following interpretation:

- `r=log10(Re/[h^-1 kpc])`, `i=log10(I/[L_sun pc^-2])`, `s=log10(sigma/[km s^-1])`; the explicit h convention must survive conversion.
- `Sn` is the FP selection weight of the referenced equations 16 and 18. It is not automatically the CF4 union-survey inclusion probability.
- `in_mask=1` identifies the SDSS NYU-VAGC DR7 LSS angular mask. Use this flag for comparisons with the released randoms.
- `NgroupT17` can include members absent from the PV catalogue. The released group labels therefore do not imply complete group membership in this table.
- The authors prefer `logdist_corr`, with the group-richness correction. Their zero-point calibration is applied **at group level**. Treating each galaxy as an independent zero-point anchor would miscount shared information.
- The quoted `logdist*_err` is a standard deviation and the accompanying location statistic is a mean of a skew-normal law; these are not directly its location and scale parameters.

The captured mock description states **256 dark-matter simulation boxes × eight observer viewpoints = 2,048 mock catalogues**. The documented `...R19XXX.Y_err_corr...` syntax identifies box XXX and observer Y. `mock_genealogy` retains both and makes the box the holdout group. Eight views of a common box are not eight independent cosmological realizations. The mock fields include observed and true redshift/distance/FP quantities, halo information, positions and velocities; the archive member list and bulk payload have not been acquired.

### CF4/EDD calibration and selection boundary

The native SDSS release is useful upstream evidence, but it is not a recovery of the full CF4 inter-survey posterior. The parent fifth-cycle derivation (`THEORY_CF4.md`, D01/D02) traces the CF3-tied SDSS scale, common distance anchors and the distinction between native and CF4-retained rows. It records native SDSS 34,059 vs CF4 34,045, and native 6dFGSv 8,885 vs CF4 7,099, from the primary releases and CF4 Table 1. The group/modulus tables distributed through [EDD catalogues](https://edd.ifa.hawaii.edu/catalogs/) do not by themselves provide every pre-intercalibration zero point, covariance, rejection or joint inclusion decision. The primary CF4 source is [Tully et al., arXiv:2209.11238](https://arxiv.org/pdf/2209.11238).

Use explicit PGC/host aliases, group roles, shared anchors and overlap genealogy when connecting these upstream data to CF4. Preserve ambiguous matches. An apparent discrepancy between native and CF4 counts is a reconciliation task, not evidence that all differences share a single cut. A post-registration residual contrast remains conditional on the adopted published scale.

## D01/D02: 6dFGSv exact upstream table

Official page: [6dFGSv distances and velocities](https://www.mso.anu.edu.au/6dfgs/vfield/3dvfield.html), saved as `inputs/sixdf_release.html`. It describes 8,885 galaxies.

| Job/product | Exact stable URL | Exact bytes | Checksum state | Direct observation |
|---|---|---:|---|---|
| `sixdf_pv_table1` | https://www.mso.anu.edu.au/6dfgs/vfield/table1.txt | 696,070 | No provider checksum found | HTTP206 bytes0–8191/696070; prefix saved |
| `sixdf_reconstruction_mocks` | https://www.mso.anu.edu.au/6dfgs/mocks/6dFGSRecon_Files.tar.gz | 17,344,070,928 | No provider checksum found | R2 HEAD200, Accept-Ranges bytes; no archive body |

The table prefix SHA256 is `1038dbc0dfacd70648a3b068780998bd3ec1b7dd0b1ec9e6eefedde4fb3789c8`; this is **not** a checksum of the 696,070-byte full table. Its Last-Modified was `Fri, 19 Sep 2014 07:43:07 GMT`.

Nine fields are `6dFGSid ra dec cz_gal cz_group Groupid delta_d epsilon_d alpha`. Coordinates are J2000 degrees, galaxy/group cz is in the CMB frame in km/s, and the log-distance ratio is in dex, `delta_d=log10(D_z/D_H)`, with error and skewness. Ungrouped entries use `-1` for group cz and group ID. Do not feed those sentinels to a redshift conversion.

The native compact table does not include every raw FP observable or its selection denominator. The [survey parent](https://www.mso.anu.edu.au/6dfgs/) links the [FP data paper](https://www.mso.anu.edu.au/6dfgs/Publications/REFEREED/fpdata.pdf). The [mock directory](https://www.mso.anu.edu.au/6dfgs/mocks/) is saved. Its reconstruction archive had Last-Modified `Thu, 08 Mar 2018 00:13:45 GMT`. Internal archive names, exact sampling law and applicability to the FP/PV selections have **not** been inspected; a large archive being publicly available does not establish a matched PV null.

## D05: official LoTSS mosaic geometry and RMS auxiliary manifests

The official [mosaic search](https://vo.astron.nl/lotss_dr3/q/query_mosaics/form) exposes table `lotss_dr3.mosaics` through [ASTRON TAP](https://vo.astron.nl/tap/sync). The script saves the actual CSV response and table-column descriptions. The query is:

```sql
SELECT mosaic_id,centeralpha,centerdelta,coverage,wcs_projection,
       wcs_refpixel,wcs_refvalues,wcs_cdmatrix,pixelsize,record_id,
       md5,accsize,related_products
FROM lotss_dr3.mosaics
```

The exact encoded stable URL is in `inputs/source_receipts.json`. This is an all-row metadata query, not a positive-source query. It returned HTTP200, **611,955 bytes, 1,580 unique mosaic IDs and nonempty coverage polygons**, SHA256:

```text
8671fa69f744a32f71904a2cc89919a3cf1021d7d030816d0adb218b34227572
```

The sum of declared high-resolution mosaic sizes is 1,615,309,211,520 bytes; those mosaics were not downloaded. The four `coverage` corners and WCS metadata define independent outer image support, including RA wrap and polar images. They do not establish positive weights, finite RMS or detection completeness inside each rectangle.

Auxiliary records are pinned to their official SURF manifests:

| Job | Official record | Stable content URL | Exact bytes | Published MD5 | Observed availability |
|---|---|---|---:|---|---|
| `lotss_aux_1078` | [zxsna-nk223](https://repository.surf.nl/records/zxsna-nk223) | https://repository.surf.nl/api/records/zxsna-nk223/files/HP-misc-1078.tar/content | 4,507,238,400 | 578f0063bd88f50f0c066d97f1686a7b | R2 HEAD202, JSON, length349: deferred |
| `lotss_aux_355` | [9syjm-kpz72](https://repository.surf.nl/records/9syjm-kpz72) | https://repository.surf.nl/api/records/9syjm-kpz72/files/HP-misc-355.tar/content | 6,025,820,160 | 6279374775bbea70db562e76dbec9207 | R2 HEAD200, octet-stream, exact length, byte ranges |

Captured record APIs are `inputs/lotss_hp1078.json` and `inputs/lotss_hp355.json`. Both have metadata storage class `M`. The previous HP-1078 Online description did not agree with its actual HTTP202 response. Conversely the previously offline HP-355 page showed three Online labels and content HEAD200 during R2. **Availability is a time-dependent response property; record labels and storage class do not prove it.** The planner preserves these observations, not a claim of current transfer readiness. Future transfers require a fresh response check. The HTTP202 body is not a successful scientific product. No explicit staging request was sent, and no signed redirect URL is stored.

The saved [HP-264 DataLink response](https://vo.astron.nl/lotss_dr3/q/dlmosaic/dlmeta?ID=ivo%3A%2F%2Fastron.nl%2F~%3FLoTSS-DR3%2FHP-264) describes the auxiliary product classes: 6 arcsec PyBDSF source mask, source model, residual and RMS, and 6/20 arcsec weight images. Its generic tape description and rounded size do not override exact SURF file metadata. Tar-member names have not been verified and are not fabricated in the plan.

### Executed independent outer exposure

For fine NESTED HEALPix pixels, a Boolean OR of all 1,580 spherical quadrilaterals gives `union`. Overlap is counted once. Equal-area child averages give a target NSIDE16 RING fraction f_p. The output is:

```text
inputs/lotss_outer_exposure_nside16.npz
sha256: 562c8e0904d506814a50a2dcca1cd95d03dd75a1bc0d05fd77d470e221e4458d
```

It contains `fraction_fine64`, `fraction_fine128`, `fraction_fine256`, the final `fraction`, `exposure_sr`, `log_exposure_sr`, `support`, target/fine NSIDEs, the original density mask, and cached 20/50/100 mJy count maps. The proposed count mean is `mu_p=exposure_sr[p]*exp(X_p beta)`; `log_exposure_sr` has fixed coefficient one. Zero-support values are negative infinity and must be excluded through `support`; positive counts outside support fail the input contract. Zero counts *inside* independent outer support remain in the supplied arrays.

| Fine NSIDE | Union area (deg²) | NSIDE16 supported cells | Fractional cells | L1 area change from preceding resolution (sr) |
|---:|---:|---:|---:|---:|
| 64 | 22,480.480287 | 1,762 | 174 | — |
| 128 | 22,464.533708 | 1,771 | 183 | 0.0214757310 |
| 256 | 22,475.129790 | 1,771 | 184 | 0.0108337393 |

Each resolution independently checked 4,096 deterministic random HEALPix centers against a spherical halfspace algorithm; all had zero mismatches. The 128→256 L1 difference is about 0.158% of the final area and maximum individual target-cell fraction change is 0.046875. Total area differences are not monotone, so these values are discretization diagnostics, not a certified continuum error bound.

The sealed R98 maps retain every cached LoTSS source at the three cuts inside this outer support:

| Flux cut (mJy) | Cached sources | Occupied cells | Zero-count cells inside outer support | Positive sources outside support |
|---:|---:|---:|---:|---:|
| 20 | 659,841 | 1,576 | 195 | 0 |
| 50 | 339,865 | 1,576 | 195 | 0 |
| 100 | 194,914 | 1,567 | 204 | 0 |

These zero-count cells are not yet certified as observed empty sky: some can contain internal weight/RMS holes. They are retained for a later valid-coverage likelihood. The old `LoTSS_DR3_int1500` mask has 966 cells, all with final f=1; the outer support adds 805 cells. The old mask also applied Galactic latitude and H I cuts, so the 805-cell difference cannot all be attributed to its density threshold.

The cached counts are reused without scanning the 3,047,958,720-byte LoTSS catalogue. Cache maps, source receipt and original reader hashes are checked; source size/mtime/inode fingerprints remain unchanged. `ACQUISITION_RESULTS.json` records their exact identities and all comparisons.

## Commander exact-release pending job

The manifest reuses `scripts/r98/acquisition_preflight.py::archive_job` for:

```text
dx12_v3_commander_noise_mc_00000_raw.fits
603987840 bytes
https://pla.esac.esa.int/pla/aio/product-action?SIMULATED_MAP.FILE_ID=dx12_v3_commander_noise_mc_00000_raw.fits
```

This is the PR3/FFP10 Commander fullmission noise realization matching the already considered signal ID00000. The state is **R98 header-verified, full payload pending**, with no public checksum recorded. PR4/NPIPE is not substituted. One future signal/noise pair would be an execution smoke check; it would not establish a sufficiently large, matched joint null ensemble.

## Runnable acquisition contract

Run from the repository root with `OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1`:

```bash
.venv/bin/python -m scripts.r99.acquisition prepare
.venv/bin/python -m scripts.r99.acquisition footprint --fine-nsides 64 128 256 --target-nside 16
.venv/bin/python -m scripts.r99.acquisition plan --ids sdss_pv_v1_1 sixdf_pv_table1 --max-bytes 22000000
.venv/bin/python -m scripts.r99.acquisition plan --ids lotss_aux_1078 --max-bytes 5000000000
```

`all` runs `prepare` and `footprint`. `prepare` reuses exact hashed small snapshots, and fails if their bytes changed. The `plan` command has no network or product-download action. It requires a unique explicit subset and sufficient declared byte budget. The first bounded subset is 20,927,710 bytes. Deferred products remain deferred; an undersized budget, unknown ID, duplicate ID, mismatched range/release size, or HTTP202 file response is rejected.

A later authorized downloader can reuse the exact R98 transfer mechanics with this manifest after fresh availability, range, size and content checks. Download to a temporary file, verify provider checksum where present and compute local SHA256 before admitting a science payload. Never treat a prefix digest as a full digest. Do not infer completeness from these checks: CF4 calibration/selection and LoTSS internal valid coverage still require their respective likelihood inputs.

## Skill and source trace

Applied physmath-research-loop 1.3.0, R2/THEORY_LOOP, CODING_LOOP, POLICY_INTEGRATION and SUBAGENT_MODE; repository scientific-code-validation, observable-statistics, claim-firewall and claim-provenance-ledger policies were read. The lane follows definition → geometric derivation → computational form → implementation → measured validation. Existing failure is retained as missing input or scope, not converted to an impossibility claim. No further reviewer recursion or production cosmology was added.
