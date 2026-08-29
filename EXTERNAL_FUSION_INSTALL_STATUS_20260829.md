# External fusion installation, data, and use status — 2026-08-29

## Read this first

This is an operational handoff for the external data, code bundle, isolated
software environments, and bounded science-readiness checks available to
`htt_base` on the host `cosmosapjw`. It is written so that another local
repository or a third-party operator on the same host can locate and open the
held products without relying on the `htt_base/workdir` symlink layer.

The evidence precedence used here is scoped by lane:

1. `SCIENCE-CONSUMER-20260829T155108Z-88d569` for the executed admitted-data
   scalar consumer and its diagnostic figure;
2. `COMMANDER-FFP10-DOWNLOAD-20260829T144340Z-64adad` for exact Commander
   product binding, transfer, local integrity, storage, and unchanged science
   admission;
3. `EXTERNAL-FUSION-RESOLUTION-20260829` receipts, resolution ledger, and
   readiness matrix v2;
4. `EXTERNAL-FUSION-FOLLOWUP-20260829` science-readiness matrix;
5. `EXTERNAL-FUSION-INSTALL-20260829` installation and holdings ledger.

The newer scoped evidence supersedes the older installation document only for
the lane it actually executed. In particular, `sbibm==1.1.0` has a working
isolated core benchmark lane but its installed distribution still has unmet
declared dependencies; CONCEPT remains unavailable; and Commander `00002`
through `00006` now have verified official PLA object bindings and complete
locally verified candidate downloads without science admission.

```yaml
document_role: OPERATIONAL_HANDOFF_ONLY
updated_at: 2026-08-30T01:15:48+09:00
canonical_repository: /home/cosmosapjw/Dropbox/bianchi/htt_base
documentation_checkout: /home/cosmosapjw/Dropbox/bianchi/htt_base
documentation_update_base_commit: f5ae09d03ef01740977d41ad61df5a2964c75b85
retired_documentation_worktree: /home/cosmosapjw/worktrees/htt-xfi-status-doc-20260829
physical_external_workdir: /mnt/sn850x2t/htt_base_e2e/workdir
main_htt_base_venv: /mnt/sn850x2t/htt_base_e2e/venvs/htt_base-py312-20260829
main_venv_status: PRESERVED_PIP_CHECK_PASS
sbibm_functional_result: SBIBM_ISOLATED_CORE_PASS
sbibm_distribution_result: PACKAGE_DEPENDENCIES_INCOMPLETE
concept_result: CONCEPT_CONTAINER_BLOCKED_RUNTIME_OR_STORAGE
native_bianchi_result: WAIT_FOR_USER_NATIVE_SOLVER
commander_result: OFFICIAL_PLA_OBJECTS_DOWNLOADED_CANDIDATE_ONLY
latest_science_consumer_result: SCIENCE_CONSUMER_NUMERICAL_PASS
latest_science_consumer_claim_tier: C2_CONDITIONAL_DIAGNOSTIC
dataset_readiness_counts:
  ready_for_bounded_current_consumer: 5
  partially_resolved: 9
  blocked_by_existing_admission_scope: 1
scientific_claim_promotion: false
native_solver_validation: false
publication_readiness_claim: false
```

`READY` in this document means that a representative local payload could be
read and a bounded current consumer or tiny operation completed. It does not
mean that a likelihood, covariance model, transfer correction, systematics
model, cosmological inference, or Bianchi-family claim has been validated.

## Canonical roots and path rules

Use these read-only shell variables in another repository or shell session:

```bash
export HTT_REPO=/home/cosmosapjw/Dropbox/bianchi/htt_base
export HTT_XFI_ROOT=/mnt/sn850x2t/htt_base_e2e
export HTT_XFI_WORKDIR="$HTT_XFI_ROOT/workdir"
export HTT_XFI_BUNDLE="$HTT_XFI_WORKDIR/external_fusion_round3"
export HTT_XFI_ENVS="$HTT_XFI_WORKDIR/external_fusion_round3_20260722_envs"
export HTT_MAIN_VENV="$HTT_XFI_ROOT/venvs/htt_base-py312-20260829"
export HTT_SBIBM_ENV="$HTT_XFI_WORKDIR/external_tools/sbibm-core"
```

Then verify the host binding before use:

```bash
test -d "$HTT_XFI_WORKDIR"
test -r "$HTT_XFI_BUNDLE/MANIFEST.json"
test -x "$HTT_MAIN_VENV/bin/python"
test -x "$HTT_SBIBM_ENV/bin/python"
df -B1 "$HTT_XFI_ROOT"
```

Path interpretation:

- `$HTT_XFI_WORKDIR` is the physical storage authority. Use it from another
  repository, from this documentation worktree, or from third-party scripts.
- `$HTT_REPO/workdir/...` is the canonical `htt_base` convenience link layer.
  Its children resolve to `$HTT_XFI_WORKDIR/...` and are ignored by Git.
- The prior documentation-only worktree
  `/home/cosmosapjw/worktrees/htt-xfi-status-doc-20260829` has been retired and
  is not the current report authority. The current report lives in the
  canonical checkout, whose `workdir/` link layer remains valid.
- Large payloads must not be copied into another checkout merely to satisfy a
  relative-path convention. Pass the physical absolute path or create a
  project-specific symlink only after checking that project’s policy.

The canonical link layer passed `workdir/verify_workdir_links.sh` with zero
path-literal regressions. The repository `workdir/` has
`user.com.dropbox.ignored=1`; the Dropbox remote
`/bianchi/htt_base/workdir` was absent at installation closeout.

## Storage and acquisition status

### Fixed holdings snapshot

The exhaustive inventory completed at 2026-08-29 14:14 KST, before the
isolated environment tree was added. It enumerated 18,256 unique regular files
and 1,185,632,921,952 logical bytes with no traversal errors or broken
symlinks. This fixed inventory has not been silently relabelled as a live
rescan.

| Category | Logical bytes | Decimal GB | Admission |
|---|---:|---:|---|
| Observational inputs | 120,042,470,154 | 120.04 | retained |
| Mock and simulation data | 937,273,565,097 | 937.27 | retained |
| Commander quarantined partials | 1,365,789,644 | 1.366 | excluded from science use |
| Code, archives, outputs, logs, manifests, and auxiliary material | 126,951,097,057 | 126.95 | retained |
| **Total fixed snapshot** | **1,185,632,921,952** | **1,185.63** | byte-conserving total |

The five completed Commander candidate downloads described below occurred
after this fixed snapshot. They are deliberately not folded back into its
category totals; their later allocation is recorded separately from the
immutable inventory measurement.

The exhaustive inventory JSON cited below is the per-file authority. The main
roots from that same fixed snapshot are indexed here so that simulation and
auxiliary holdings are not hidden behind the admitted-dataset table:

| Root below `$HTT_XFI_WORKDIR` | Snapshot logical bytes | Content class |
|---|---:|---|
| `raw/planck_ffp10` | 787,154,151,326 | FFP10 simulations, manifests, and quarantined Commander partials |
| `raw/desi_dr1_mocks` | 130,151,093,887 | DESI DR1 mock realizations |
| `raw/cosmos_web_dr1` | 70,141,163,958 | COSMOS-Web observations and auxiliary archives |
| `data/external` | 73,731,226,598 | mixed external inputs; inspect the per-file inventory before admission |
| `raw/act_dr6_lensing` | 25,116,660,530 | ACT DR6 lensing maps, spectra, simulations/products, and likelihood payloads |
| `raw/hsc_kids` | 25,023,101,093 | HSC and KiDS observations/releases |
| `raw/beyondplanck_v2` | 16,372,086,944 | BeyondPlanck observational/product holdings |
| `raw/wmap_7yr_e2e_sim` | 14,496,057,017 | WMAP seven-year end-to-end simulations |
| `raw/cosmoglobe_dr1` | 8,657,231,040 | Cosmoglobe DR1 observational/product holdings |
| `raw/websky_selected` | 6,874,522,560 | selected WebSky simulation fields and completion metadata |
| `raw/planck_data` | 4,027,302,337 | Planck PR3 maps, masks, and spectra |
| `raw/planck_pr3_component_controls` | 3,623,973,120 | Planck PR3 NILC/SEVEM component controls |
| `rrss_observational_inputs/PR4` | 3,271,645,440 | nine selected 30–857 GHz PR4 frequency maps |
| `raw/desi` | 3,317,325,120 | DESI observational products |
| `raw/wmap_9yr` | 3,078,190,892 | WMAP nine-year observations/products |
| `raw/quijote_mfi_dr1` | 2,145,745,296 | QUIJOTE MFI DR1 observations and documentation |

Roots in this index that do not appear in the 15-family readiness table below
are inventory holdings only. This document does not invent a consumer or
readiness PASS for them; consult the per-file inventory before selecting one.

After the isolated environments were installed, the measured external-workdir
allocation was 1,202,027,061,248 bytes. The later resolution work downloaded
only three official WebSky metadata files: 5,430 logical bytes, 12,288 allocated
bytes. Its total retained task artifacts were 487,424 bytes and its measured
peak increase was 495,616 bytes. No large science payload, OCI image, or
container layer was pulled during that resolution.

The subsequent bounded Commander acquisition wrote five new candidate FITS
objects sequentially to the external NVMe. Their total logical size is
3,019,939,200 bytes, end allocation is 3,019,964,416 bytes, and peak attributable
allocation was 3,020,152,832 bytes. External free space moved from
478,761,304,064 to 475,741,343,744 bytes during that run; main-NVMe payload
allocation was zero. These bytes are complete local candidates, not admitted
null-pool members.

### Live capacity recheck for this document

| Filesystem | Free bytes | Use |
|---|---:|---:|
| Main NVMe `/` | 145,843,662,848 | 85% |
| External 2 TB NVMe `/mnt/sn850x2t` | 475,741,278,208 | 76% |

This document update performed no acquisition, installation, relocation,
cache deletion, process termination, or daemon change. It also did not inspect
or stop neighboring parallel research jobs.

### Rules for any future acquisition

From the canonical repository, prepare the destination before downloading:

```bash
cd "$HTT_REPO"
workdir/prepare_external_download_dir.sh raw/NEW_DATASET_NAME
```

Replace `NEW_DATASET_NAME` with one safe relative directory name; do not pass
an absolute path or a path containing `..`.

The current guardrails are: keep at least 300 GiB free on the external NVMe;
at most 100 GiB newly retained, 20 GiB transient, and 120 GiB peak growth per
bounded acquisition; keep the first small batch at or below 20 GiB. Count
archives, extracted files, caches, OCI layers, and outputs. No new acquisition
larger than about 10 GiB is admitted without a named consuming analysis,
scientific question, complementary held dataset, duplication check, size, and
immediate value. The whole CMB-S4 PanEx release is not an admitted download.

### Held-set completeness at the latest closeout

- FFP10 SMICA CMB: 999 admitted maps. ID `00970` is the one explicitly
  recorded upstream absence. SMICA `00818` is 1,218 bytes shorter than the
  common padded FITS size, but Astropy reads all 49,152 rows and the final
  record is finite; this remains a packaging warning, not an automatically
  promoted scientific-integrity failure.
- FFP10 SMICA noise: 300/300 complete.
- DESI BGS acquisition queue: 17/17 files match their recorded aria2 SHA-256
  expectations.
- Planck PR3 Commander/SMICA/NILC/SEVEM inputs and masks are present; the PR4
  directory holds nine selected frequency maps, but the current PR4 numeric
  admission gate remains closed.
- Commander `00002`--`00006` are additionally present as five complete
  official-PLA-bound candidate files, each 603,987,840 bytes. Their original
  partial files remain preserved; publisher checksum verification is absent
  and the frozen science-admission gate remains unchanged.
- KiDS candidate archives match their local receipts. WebSky retains seven
  selected science components plus the newly downloaded official metadata.
- At resolution closeout no large transfer was running. This documentation
  update did not classify or terminate any subsequently started parallel job.

## Data catalog and current readiness

Every path below is relative to `$HTT_XFI_WORKDIR`; prepend that physical root
when operating outside the canonical repository. The five `READY` rows retain
the bounded FOLLOWUP result. For the other ten rows, the newer resolution
matrix v2 is authoritative.

| Family | Canonical local payload | Representation and bounded consumer | Current result and ceiling |
|---|---|---|---|
| Planck PR3 | `raw/planck_data/COM_CMB_IQU-smica_2048_R3.00_full.fits`; common intensity mask in the same directory; saved scalar checkpoint under `analysis/planck_mes_irrep/paired300_carrier` | HEALPix NSIDE 2048, NESTED, Galactic I/Q/U in K_CMB; low-resolution read smoke plus a saved-feature scalar consumer paired with 300 admitted FFP10 SMICA CMB+noise rows | `READY`; the added result is C2 conditional/diagnostic-only and does not establish physical shear/vorticity, likelihood validity, or a geometry/family claim |
| Planck FFP10 | readiness smoke: `raw/planck_ffp10/commander/cmb_mc/dx12_v3_commander_cmb_mc_00000_raw.fits`; admitted scalar consumer: paired SMICA CMB+noise rows recorded under `analysis/planck_mes_irrep/paired300_carrier` | Smoke payload is HEALPix NSIDE 2048, RING, I/Q/U K_CMB; the executed scalar consumer loaded only saved `features` for one Planck PR3 observation plus 300 exact paired FFP10 SMICA CMB+noise rows | `READY` for the bounded existing consumers; Commander candidate IDs 00002–00006 and their preserved partials remain excluded from science admission |
| DESI observations | `compact_products/desi/BGS_ANY_NGC_clustering_extended.npz` | 4,081,227 BGS_ANY NGC rows; sky vectors, redshift, and weights; current consumer `htt/obsstat/egs3_external_lanes.py` | `READY`; footprint/selection and estimator inference are outside this read smoke |
| DESI mocks | `raw/desi_dr1_mocks/EZmock/bright/v1/mock605/BGS_ffa_NGC_clustering.dat.fits` | FITS LSS table, 219,290 rows; RA/DEC, Z/TRUEZ, number density, weights, and tile metadata | `READY`; one realization and one cap, not ensemble validation |
| CF4/local structure | `raw/cf4/CF4pp_mean_std_grids.npz` | 128 cubed density/velocity mean and standard-deviation grids in a 1000 Mpc supergalactic Cartesian box; velocities in km/s; consumers `scripts/k6_cf4_curl_posterior.py` and `scripts/make_cf4_affine_flow.py` | `READY`; reconstruction-conditioned access only, without curl, bulk-flow, or cosmological inference |
| HSC S19A Y3 Fourier cosmic shear | `data/external/hsc_s19a_y3/dalal23/hsc_y3_fourier_space_data_vector.sacc` plus `ppcorr_psf_all_ells_lmax_1800_catalog2.npz` and `psf_transform_matrix_lmax_1800_catalog2.npz` | SACC 2.4: 170-value EE vector, finite symmetric 170x170 covariance, four tracer n(z), and readable PSF arrays | `PARTIALLY_RESOLVED`; legacy SACC ordering warning, no BB/EB test, calibration, or persistent HTT likelihood adapter |
| CLASS 40 GHz DR1 observations | `raw/class_dr1/class_dr1_40GHz_skymap_n128.fits`, `class_dr1_40GHz_dX_mask_n128.fits`, `class_dr1_40GHz_VEB_transfer_matrix_lmax383_hits.hdf5`, and `class_dr1_40GHz_bl.csv` | HEALPix map with exact `V_POLARISATION`, `Q_POLARISATION`, `U_POLARISATION` fields; released d0 mask and sentinel exclusion; 1152x1152 transfer matrix in VV/EE/BB block order | `PARTIALLY_RESOLVED`; map/mask/transfer structural operation passed, but no transfer-corrected observed spectrum, noise ensemble, or persistent HTT adapter |
| ACT DR6 lensing | `raw/act_dr6_lensing/dr6_lensing_release/maps/baseline/kappa_alm_data_act_dr6_lensing_v1_baseline.fits` and `raw/act_dr6_lensing/ACT_dr6_likelihood_v1.2/v1.2` | Complex convergence a_lm through lmax 4000 plus the v1.2 vector/covariance/binning payload; current reader `htt.obsstat.egs3_external_lanes.act_kappa_auto_bandpower` | `PARTIALLY_RESOLVED`; official likelihood runtime was not run, and no fresh simulation or phi/kappa normalization validation was done |
| ACT DR6.02 primary CMB | `raw/act_data/dr6_data.fits` and `raw/act_data/act_dr6_02_acquisition_manifest.json` | SACC 2.4 loaded 6,840 data values and a 6840x6840 covariance | `PARTIALLY_RESOLVED`; legacy warning remains; no beam/calibration propagation, covariance conditioning, persistent likelihood adapter, or likelihood result |
| WMAP nine-year ILC | `raw/wmap_9yr/core/wmap_ilc_9yr_v5.fits` and `raw/wmap_9yr/core/wmap_analysis_masks_9yr_v5.tar.gz` | HEALPix NSIDE 512 NESTED temperature in thermodynamic mK; held KQ75 mask produced a bounded masked moment | `PARTIALLY_RESOLVED`; temperature-only, no effective beam/bandpass, polarization/covariance path, or persistent HTT adapter |
| QUIJOTE MFI DR1 | `raw/quijote_mfi_dr1/quijote_mfi_skymap_11ghz_512_dr1.fits`, `quijote_mfi_skymap_11ghz_512_dr1_half1.fits`, `quijote_mfi_skymap_11ghz_512_dr1_half2.fits`, `mask_quijote_ncp_lowdec_satband_nside512.fits`, and `rimo_quijote_mfi_beamtf_dr1.fits` | HEALPix NSIDE 512 RING, Galactic I/Q/U in mK_CMB plus hits/weights; mask, split difference, and beam-table reads passed | `PARTIALLY_RESOLVED`; official filtering correction, matched spectrum, split-noise calibration, and persistent HTT adapter remain absent |
| Planck PR4 selected LFI 30 GHz | `rrss_observational_inputs/PR4/frequencyMaps/LFI_SkyMap_030-BPassCorrected-field-IQU_1024_R4.00_full.fits` | Held HEALPix NSIDE 1024 NESTED Galactic I/Q/U map | `BLOCKED_BY_EXISTING_ADMISSION_SCOPE`; the fixed PR-150 gate forbids new PR4 numeric analysis or PR3+PR4 output, so no new numerical smoke was claimed |
| KiDS-Legacy DR5 cosmic shear | `raw/hsc_kids/kids_dr5_candidate/KiDS_Legacy_cosmic_shear_data_release.tar.gz` | Streamed `KiDS_Legacy_bandpowers.fits`: concatenated E/B vector length 336, exact-symmetric 336x336 covariance, and six n(z) columns | `PARTIALLY_RESOLVED`; response/selection calibration, scale cuts, IA/redshift priors, persistent adapter, and likelihood execution remain absent |
| COSMOS-Web v1.1 | `raw/cosmos_web_dr1/COSMOSWeb_mastercatalog_v1.1.fits`, `cosmos_web_psfs_v5.0.tar.gz`, `segmentation_maps.tar.gz`, and `cosmos_web_starmask_jwst.tar.gz` | 784,016-row catalog; bounded F444W S/N and morphology selection plus one streamed auxiliary member from each archive | `PARTIALLY_RESOLVED`; e1/e2 are morphology, not calibrated shear; tile/WCS association, corrected-photometry science checks, photo-z validation, and persistent adapter remain absent |
| WebSky selected fields | `raw/websky_selected/kap.fits`; same directory also holds `isw.fits`, `ksz.fits`, `ksz_patchy.fits`, `cib_nu0143.fits`, `cib_nu0353.fits`, `lensed_alm.fits`, `README.txt`, `UPDATES.txt`, and `cosmology.py` | Dimensionless HEALPix RING kappa map; `healpy` read, NSIDE 64 downgrade, and lmax 16 `anafast` completed | `PARTIALLY_RESOLVED`; tiny transform is not spectrum validation; units remain component-specific and no persistent component-aware adapter exists |

### Executed admitted-data consumer: PR3/FFP10 scalar MES dependence

Run `SCIENCE-CONSUMER-20260829T155108Z-88d569` consumed the already admitted
saved scalar features for one Planck PR3 SMICA observation and 300 exact paired
FFP10 SMICA CMB+noise rows. Its question was whether the two registered
one-way scalar MES ceiling coordinates are strongly dependent on the same
rows, and where the observation lies under the unchanged finite-pool reducer.

```text
feature checkpoint root:
  $HTT_XFI_WORKDIR/analysis/planck_mes_irrep/paired300_carrier
execution manifest SHA-256:
  6e2acaa4b695ad422cca5099c4d91e9a7dfc741f6e41b461d10da4ec52c36831
301-file NPZ-set SHA-256:
  7df706993246102fca54547deecec8de026b7d4aa9c82c5d4b73faa5e72d7723
301-file row-metadata-set SHA-256:
  87a1d75f3801753e9d6694fd8d0d267d708e1d97211d9f0d28533f63ef4cb822
operator identity:
  sha256:53c250dd1b3fe614ad2b5fd1d9a1003bf65253e9d432a6b67913c047d43f5014
```

Despite the checkpoint directory name, the consumer loaded only the
12-element `features` arrays and used indices 0 and 1 (`C2`, `C3`). It did not
load or numerically use the withdrawn `carrier` arrays. Commander candidates
were not inputs. The frozen settings were Galactic, HEALPix Nside 16, RING,
the Planck PR3 common temperature mask, `T0=2.72548e6 microkelvin`, residual
cosmological `epsilon_1=0`, the registered scalar MES formulae, and the
all-row leave-one-out absolute-median rank with conservative `>=` ties.

The exact executed command was:

```bash
cd "$HTT_REPO"
"$HTT_MAIN_VENV/bin/python" \
  .agent-harness/runs/SCIENCE-CONSUMER-20260829T155108Z-88d569.pending/artifacts/RUN_CONSUMER.py \
  --config .agent-harness/runs/SCIENCE-CONSUMER-20260829T155108Z-88d569.pending/artifacts/INPUT_AND_RUN_CONFIG.json
```

The first attempt exited before producing outputs because a run-local success
check treated the intentionally false field `carrier_numerically_accessed`
as a required true boolean. The single bounded repair renamed the positive
check to `carrier_excluded=true`; no input, formula, reducer, pool, tolerance,
expected value, or claim setting changed. The second attempt exited 0 and an
independent host recomputation passed.

| Quantity | Executed result |
|---|---:|
| observed `C2` | `210.46184716646644 microkelvin^2` |
| observed `C3` | `482.02081141805786 microkelvin^2` |
| `Sigma2_max` | `2.4000870221758445e-10` |
| `W2_max` | `3.0061887930898035e-13` |
| local finite-pool ranks | `74/301` for each coordinate |
| complete-pool Pearson / Spearman | `0.9948739661` / `0.9937383116` |
| standardized two-coordinate condition number | `389.1651913` |
| first principal-component variance fraction | `0.9974369830` |

The numerical result is
`$HTT_REPO/.agent-harness/runs/SCIENCE-CONSUMER-20260829T155108Z-88d569.pending/artifacts/NUMERICAL_RESULT.json`.
The readable two-panel diagnostic is `DIAGNOSTIC_FIGURE.png` in the same
directory, SHA-256
`d700a29ffb7193b5f4f886f76d11355913931ed105020f9339dfee24de8dffa5`;
its provenance is `FIGURE_PROVENANCE.json`. Because the historical command
refuses to overwrite existing outputs, third-party consumers should inspect
these results directly rather than rerunning into the same run directory:

```bash
jq '.status, .results, .interpretation' \
  "$HTT_REPO/.agent-harness/runs/SCIENCE-CONSUMER-20260829T155108Z-88d569.pending/artifacts/NUMERICAL_RESULT.json"
```

| Claim ID | Owner | Status | Evidence | Transfer source | Tier | Caveat |
|---|---|---|---|---|---|---|
| `XFI-PR3-FFP10-SCALAR-MES-DEPENDENCE-20260829` | `obsstat` | `CONDITIONAL` | numerical artifact plus independent recomputation and diagnostic figure | `none` | C2 | `DIAGNOSTIC_ONLY`; fixed admitted 301-row pool and registered premises only; not physical shear/vorticity, unconditional significance, local/global attribution, geometry, or family identification |

The result supports strong same-row dependence and exact finite-pool position
under the unchanged reducer. It does not create two independent evidence
channels, a likelihood, posterior, Bayes factor, detection, physical
shear/vorticity state, Bianchi geometry, or family identification. No claim
ledger status was promoted by recording this already-scoped result.

### Publisher and release locators

These are source/release locators, not a statement that a publisher checksum
was available. Existing local files were reused unless the acquisition table
above explicitly records new bytes.

| Family | Source/release locator used by the current receipts |
|---|---|
| Planck PR3 | [ESA Planck 2018 release DOI](https://doi.org/10.5270/esa-zfx8b4s) |
| HSC S19A Y3 | [HSC S19A shape catalog/PDR3 documentation](https://hsc-release.mtk.nao.ac.jp/doc/index.php/s19a-shape-catalog-pdr3/) |
| CLASS 40 GHz DR1 | [NASA LAMBDA CLASS product table](https://lambda.gsfc.nasa.gov/product/class/class_prod_table.html) |
| ACT DR6 lensing | [NASA LAMBDA ACT DR6 lensing likelihood page](https://lambda.gsfc.nasa.gov/product/act/actadv_dr6_lensing_lh_get.html) |
| ACT DR6.02 primary | [NASA LAMBDA ACT DR6.02 page](https://lambda.gsfc.nasa.gov/product/act/act_dr6.02/index.html) |
| WMAP nine-year | [NASA LAMBDA WMAP nine-year products](https://lambda.gsfc.nasa.gov/product/wmap/dr5/m_products.html) |
| QUIJOTE MFI DR1 | [NASA LAMBDA QUIJOTE MFI information](https://lambda.gsfc.nasa.gov/product/quijote/quijote_mfi_data_info.html) |
| Planck PR4/NPIPE | [NERSC Planck 2020 portal](https://portal.nersc.gov/project/cmb/planck2020/); held-map identity only, with matched simulation identity unresolved |
| KiDS-Legacy DR5 | [KiDS DR5 legacy weak-lensing release](https://kids.strw.leidenuniv.nl/DR5/legacy_wl.php) |
| COSMOS-Web v1.1 | [COSMOS2025/COSMOS-Web distribution portal](https://cosmos2025.iap.fr/) |
| WebSky | [NASA LAMBDA mock-simulation index](https://lambda.gsfc.nasa.gov/simulation/mocks_data.html) |
| Commander `00002`--`00006` | Exact basenames resolve through the official [Planck Legacy Archive](https://pla.esac.esa.int/) `product-action?SIMULATED_MAP.FILE_ID=<basename>` route and returned matching FITS objects; the HTTP responses did not state a release identity or expose publisher checksums |

The three newly acquired WebSky metadata objects were downloaded directly to
the external NVMe and atomically renamed on that filesystem:

| Local file | Source URL | Bytes | Local SHA-256 (not publisher checksum) |
|---|---|---:|---|
| `raw/websky_selected/README.txt` | `https://lambda.gsfc.nasa.gov/data/simulation/cmb_mocks/README.txt` | 1,858 | `7b222273dd1b6be2be918195ef9e942afaa36d2ba05a52cf88e2b5e95cac37cf` |
| `raw/websky_selected/UPDATES.txt` | `https://lambda.gsfc.nasa.gov/data/simulation/cmb_mocks/UPDATES.txt` | 3,183 | `823cd10c24e84510f032775ad739a4929ee65ad6712cd80bc44ed6db4b8c89df` |
| `raw/websky_selected/cosmology.py` | `https://lambda.gsfc.nasa.gov/data/simulation/cmb_mocks/cosmology.py` | 389 | `43d2a45a9b8244cef62d2566904759c1d1e5246d1a0baadbdace72b86a7598d8` |

### Missing-file, missing-consumer, and validation-gap split

This split prevents a missing software adapter from being misreported as a
missing publisher payload.

| Lane | Missing or externally gated file | Missing consuming code | Remaining validation gap |
|---|---|---|---|
| HSC | none for the selected EE SACC lane | persistent HSC selection/likelihood adapter | legacy ordering, BB/EB, responsivity, multiplicative/additive and selection calibration |
| CLASS 40 GHz | none for the admitted map/mask/beam/transfer set | persistent CLASS observation adapter | corrected observed spectrum, noise ensemble, polarization-basis cross-check |
| ACT lensing | none for the selected vector/covariance/binning lane | admitted official `act_dr6_lenslike` runtime | likelihood execution, simulation validation, phi/kappa normalization |
| ACT primary | none for the selected SACC payload | persistent primary-CMB likelihood adapter | likelihood, beam/calibration, covariance conditioning |
| WMAP | no new file admitted; effective beam/polarization/covariance auxiliaries remain unbound | persistent WMAP adapter | coordinate/beam/bandpass and Q/U covariance treatment |
| QUIJOTE | none for the selected full/split/mask/beam set | persistent adapter with explicit filtering convention | filtering, beam/pixel-window matched spectrum, split-noise calibration |
| PR4 | matched beam/transfer/mask and authorized matched split/simulation set are not admitted | none may be added under the fixed gate | all PR4 numeric use remains prohibited by the existing scope gate |
| KiDS-Legacy | none for the held tar release | persistent statistic/likelihood adapter | shear/selection calibration, cuts, priors, likelihood |
| COSMOS-Web | no additional large product admitted; the 28.3 GB LePhare PDF-z pickle was intentionally not opened | persistent tile-aware adapter | corrected photometry, tile/WCS, photo-z, and shear calibration |
| WebSky | no extra component admitted | persistent component-aware adapter | units, same-realization normalization, reference spectrum comparison |

### Minimal read/use recipes

These commands are intentionally small. They demonstrate how to reach the
held bytes; they are not commands for a full scientific campaign.

Inspect any FITS header without loading a full map into RAM:

```bash
export FITS_PATH="$HTT_XFI_WORKDIR/raw/planck_data/COM_CMB_IQU-smica_2048_R3.00_full.fits"
"$HTT_MAIN_VENV/bin/python" - <<'PY'
import os
from astropy.io import fits
with fits.open(os.environ["FITS_PATH"], memmap=True) as hdul:
    print(len(hdul), hdul[1].header.get("NSIDE"), hdul[1].header.get("ORDERING"))
    print(hdul[1].columns.names)
PY
```

Run the bundle’s Planck low-ell quicklook against the held PR3 map and mask:

```bash
cd "$HTT_XFI_BUNDLE"
PYTHONPATH=src "$HTT_XFI_ENVS/lowell/bin/python" \
  experiments/planck_lowell_poles.py \
  "$HTT_XFI_WORKDIR/raw/planck_data/COM_CMB_IQU-smica_2048_R3.00_full.fits" \
  --mask-fits "$HTT_XFI_WORKDIR/raw/planck_data/COM_Mask_CMB-common-Mask-Int_2048_R3.00.fits"
```

That script is a quicklook adapter. Matched mask, foreground, covariance, and
null calibration are still required for claim-bearing use.

Load the HSC or ACT SACC payload in the isolated inference profile:

```bash
export SACC_PATH="$HTT_XFI_WORKDIR/data/external/hsc_s19a_y3/dalal23/hsc_y3_fourier_space_data_vector.sacc"
"$HTT_XFI_ENVS/inference/bin/python" - <<'PY'
import os
import sacc
s = sacc.Sacc.load_fits(os.environ["SACC_PATH"])
print("ndata", len(s.mean), "covariance", s.covariance.covmat.shape)
print("tracers", sorted(s.tracers))
PY
```

For ACT DR6.02, set `SACC_PATH` to
`$HTT_XFI_WORKDIR/raw/act_data/dr6_data.fits`. A successful load is not a
likelihood evaluation.

Invoke the current ACT lensing consumer from the canonical repository, whose
module resolves its admitted `workdir/` path:

```bash
cd "$HTT_REPO"
"$HTT_MAIN_VENV/bin/python" - <<'PY'
from htt.obsstat.egs3_external_lanes import act_kappa_auto_bandpower
print(act_kappa_auto_bandpower())
PY
```

Inspect the compact DESI and CF4 NPZ products without copying them:

```bash
"$HTT_MAIN_VENV/bin/python" - <<'PY'
import os
import numpy as np
wd = os.environ["HTT_XFI_WORKDIR"]
for rel in [
    "compact_products/desi/BGS_ANY_NGC_clustering_extended.npz",
    "raw/cf4/CF4pp_mean_std_grids.npz",
]:
    with np.load(os.path.join(wd, rel), mmap_mode="r") as data:
        print(rel, sorted(data.files))
PY
```

List, but do not bulk-extract, a held archive:

```bash
tar -tf "$HTT_XFI_WORKDIR/raw/hsc_kids/kids_dr5_candidate/KiDS_Legacy_cosmic_shear_data_release.tar.gz" | head
```

## External-fusion code bundle

### Bundle identity and layout

The received archive identity recorded by the installation receipt is:

```text
archive name: htt_external_fusion_round3_20260722.zip
archive SHA-256: 1511fcf247c3ee7d3ed09a99aed0b9086401989c4995df8108ddf69db03e1491
complete installed bundle: /mnt/sn850x2t/htt_base_e2e/workdir/external_fusion_round3
installed file count: 139
installed logical bytes: 5,515,954
```

The original ZIP is not asserted to remain at a stable local path; use the
manifest-bound installed bundle. Important subpaths are:

| Subpath | Contents and use |
|---|---|
| `src/htt_ext/` | `htt-external-fusion` reference package: low-ell types, shell/pole operations, rank/statistics, remote fields, and fail-closed optional plugin registry |
| `experiments/` | 14 current reference/quicklook executables including rotation covariance, shell poles, Planck adapters, source discrimination, response rank, and Track-I/Track-II boundary checks |
| `tools/` | bundle verifier, manifest builder, planning-doc generator, and non-destructive overlay installer |
| `configs/` | data recipes, external ecosystem ledger, and low-ell pole program |
| `schemas/` | plugin, pole-bundle, and native solver delivery receipt schemas |
| `pr_cards/` | PR-247 through PR-282 planning cards; planning authority, not evidence that those PRs ran |
| `outputs/` | retained bundle-mechanics/reference-DGP smoke outputs; not observational or native-solver results |

Run the already-installed core reference suite without modifying the main
repository environment:

```bash
cd "$HTT_XFI_BUNDLE"
PYTHONPATH=src "$HTT_XFI_ENVS/core/bin/python" experiments/run_all.py
PYTHONPATH=src "$HTT_XFI_ENVS/core/bin/python" experiments/plugin_probe.py
```

The core suite previously reported 9 pytest passes and 10/10 reference demos.
These are bundle-mechanics and transparent reference-DGP checks only.

### Isolated profile environments

Each profile is self-contained at `$HTT_XFI_ENVS/<profile>`; invoke its
`bin/python` directly to avoid accidentally mixing environments.

| Profile | Python | Installed, currently reachable components | Intended entry point |
|---|---:|---|---|
| `core` | 3.11.15 | `htt-external-fusion` 0.1.0, NumPy 2.4.6, SciPy 1.17.1 | bundle reference suite and fail-closed plugin registry |
| `lowell` | 3.11.15 | CAMB 1.6.6, CLASS/classy 3.3.4.0, GLASS 2026.2, healpy 1.20.0, pymaster 3.0, PySM3 3.4.6, lenspyx 2.0.52 | FLRW transfer cross-checks, HEALPix/alm work, masked-sky and foreground quicklooks |
| `morphology` | 3.12.3 | JAX 0.11.1, healpy 1.20.0, S2FFT 1.4.0, CVXPY 1.9.2, CVXPYlayers 1.2.0 | differentiable harmonics and convex morphology work without S2WAV |
| `morphology_s2wav` | 3.11.15 | torch 2.13.0+cu132, JAX 0.10.2, S2FFT 1.4.0, S2WAV 1.0.4 | GPU-capable directional wavelet lane |
| `inference` | 3.12.3 | torch 2.13.0+cu132, JAX 0.11.1, SACC 2.4, sbi 0.27.0, NumPyro 0.21.0, Cobaya 3.6.2, CVXPY 1.9.2, CVXPYlayers 1.2.0 | GPU-capable inference and SACC inspection; does not contain `sbibm` |
| `firecrown` | 3.11.16 | Firecrown 1.15.2, SACC 2.4, Cobaya 3.6.2, pyccl 3.3.6, and local recipe repair `lsstdesc-crow` 1.0.12 | Firecrown/likelihood framework isolation |
| `survey` | 3.11.15 | GLASS 2026.2, pyccl 3.3.4, pycorr 1.0.0 at `518cb61529f0b8f54649ac046baed7295410d794`, pypower 1.0.0 at `4b0f6f25f2c6976eb22ed5e172db5b0223a1ad1d`, Snakemake 9.26.1, Corrfunc 2.5.3 | LSS, window/random-aware estimators, workflows, and pair-counts |
| `survey_coffe` | 3.11.15 | COFFE 3.0.1 with NumPy 1.26.4 | isolated relativistic/wide-angle correlation templates |
| `nbody` | 3.11.15 | JAX 0.10.2, JaxPM 0.0.2 | differentiable PM reachability; no validated N-body campaign |
| `pspy` | 3.11.15 | healpy 1.20.0, pspy 1.8.4 | CAR/HEALPix spectrum utilities |
| `pysco` | 3.11.15 | `pysco-nbody` 1.0.9 | PySCo import/runtime lane; no N-body validation claim |
| `prose` | 3.11.15 | `htt-legacy-revival-core` 0.2.0 | historical `revival_core` overlay only |

Examples:

```bash
"$HTT_XFI_ENVS/lowell/bin/python" -c 'import camb, classy, healpy, pymaster; print(camb.__version__)'
"$HTT_XFI_ENVS/morphology_s2wav/bin/python" -c 'import torch, s2wav; print(torch.cuda.is_available(), torch.cuda.get_device_name(0))'
"$HTT_XFI_ENVS/firecrown/bin/python" -c 'import firecrown, firecrown.likelihood, sacc'
"$HTT_XFI_ENVS/survey/bin/python" -c 'import pyccl, pycorr, pypower, Corrfunc'
"$HTT_XFI_ENVS/pysco/bin/python" -c 'import pysco; print(pysco.__file__)'
```

The `inference` and `morphology_s2wav` profiles executed a CUDA tensor
reduction on the NVIDIA GeForce RTX 3090 with the CUDA 13.2 PyTorch build. That
proves GPU reachability only, not inference or morphology correctness.

### Source builds and historical code

| Identity | Exact location | Identity/status | Minimal use |
|---|---|---|---|
| nanoCMB | `$HTT_XFI_ENVS/sources/nanoCMB` | commit `ee18ff2f3d270b56c0836e35f1c430345aec7268`; generated `nanocmb_output.npz` has finite flat-LCDM oracle arrays | `cd .../nanoCMB && "$HTT_XFI_ENVS/core/bin/python" nanocmb.py`; use only as a readable flat-LCDM oracle |
| HEALPix reference C++ | `$HTT_XFI_ENVS/sources/Healpix_3.83` | version 3.83; official archive SHA-256 `0af69190d688fe53f2b2b1e85a28a1ee32f936c3e0e715d9ca9ab6a45ab3c765`; prior `hpxtest` exit 0 | executables such as `anafast_cxx`, `alm2map_cxx`, and `udgrade_cxx` are in its `bin/` directory |
| CFITSIO | `$HTT_XFI_ENVS/native-prefix/cfitsio-4.7.0` | local-prefix dependency for the HEALPix build | add its `bin/` or `lib/` only to the command that needs it; do not install globally |
| GSL | `$HTT_XFI_ENVS/native-prefix/gsl-2.8` | local-prefix dependency for the HEALPix build | use its `bin/gsl-config` or local libraries explicitly |
| CONCEPT source checkout | `$HTT_XFI_ENVS/sources/concept-1.0.1` | upstream commit `46241595ddc12dd5c8bd1e0034be8ef78d686229`; source present, runtime not installed | inspection only; there is no admitted `concept` executable |

## Main `htt_base` environment

The accepted repository venv remains externalized and unchanged by the
resolution work:

```text
/home/cosmosapjw/Dropbox/bianchi/htt_base/venv
  -> /mnt/sn850x2t/htt_base_e2e/venvs/htt_base-py312-20260829
```

It uses Python 3.12.3. The documentation-time check reports NumPy 2.4.6,
SciPy 1.18.1, healpy 1.20.0, SACC 2.4, CAMB 1.6.6, CLASS/classy 3.3.4.0, and
`pip check: No broken requirements found`. It intentionally does not carry
PyTorch, `sbi`, pymaster, or pyccl; those belong to isolated external profiles.

Activation and verification:

```bash
deactivate 2>/dev/null || true
cd "$HTT_REPO"
source venv/bin/activate
python -m pip check
python -c 'import bass_py, htt, mio; print("repository imports reachable")'
```

The earlier focused repository smoke reported 6 passes. BASS/HTT/MIO are
current repository packages. TSC/Teff/`tsc_legacy` imports are retained for
legacy reproduction only and must not become new science owners. No completed
profile requires a root/system package install.

## `sbibm==1.1.0`: functional core, incomplete distribution

The older `BLOCKED_EXTERNAL` classification is superseded by the bounded
isolated-core result below. Do not merge this environment with `inference`, add
ELFI/GPy to it, or downgrade NumPy/SciPy in another SBI environment.

```text
environment: /mnt/sn850x2t/htt_base_e2e/workdir/external_tools/sbibm-core
Python: 3.11.15
sbibm: 1.1.0
torch: 2.13.0+cu132
CUDA device smoke: NVIDIA GeForce RTX 3090
functional result: SBIBM_ISOLATED_CORE_PASS
distribution result: PACKAGE_DEPENDENCIES_INCOMPLETE
```

Reproduce the small functional API smoke:

```bash
"$HTT_SBIBM_ENV/bin/python" - <<'PY'
import sbibm
from sbibm.metrics import c2st

print(sbibm.get_available_tasks())
task = sbibm.get_task("two_moons")
theta = task.get_prior()(num_samples=1)
x = task.get_simulator()(theta)
reference = task.get_reference_posterior_samples(num_observation=1)
score = c2st(reference[:256], reference[256:512])
print("theta", tuple(theta.shape), "x", tuple(x.shape))
print("reference", tuple(reference.shape), "C2ST smoke", float(score))
PY
```

The environment intentionally has no `pip` module. Its distribution check is:

```bash
uv pip check --python "$HTT_SBIBM_ENV/bin/python"
```

That check exits 1 because installed `sbibm` METADATA declares the following
currently missing dependencies: `elfi>=0.7.6`, `deneb`, `diffeqtorch`,
`pyabc>=0.10.8`, `pyabcranger>=0.0.48`, and `sbi>=0.20.0,<0.22.0`. The METADATA
is at
`$HTT_SBIBM_ENV/lib/python3.11/site-packages/sbibm-1.1.0.dist-info/METADATA`.
The functional smoke did not import ELFI or GPy. Therefore the allowed claim is
only task listing, `two_moons` prior/simulator, packaged reference posterior,
C2ST, and torch reachability—not a dependency-complete distribution, BOLFI
lane, benchmark-quality result, or scientific validation.

## Typed external blockers

### CONCEPT 1.0.1

Status: `CONCEPT_CONTAINER_BLOCKED_RUNTIME_OR_STORAGE`.

- The two permitted native installation attempts are consumed. No third
  native attempt and no Dockerfile rebuild was performed.
- The incomplete native runtime was removed; only source and failure evidence
  remain. There is no `concept` executable to invoke.
- The official `jmddk/concept:1.0.1` linux/amd64 manifest resolves to
  `sha256:3ded3cf789974a725c6d8fa8e851f10eca2e27c031cea34e6046f68e8ace69b4`.
  Its reported compressed layers total 170,047,202 bytes.
- No image was pulled and no container or sample run was created. Docker uses
  `/var/lib/docker` and containerd uses `/var/lib/containerd`, both on the
  main NVMe. That fails the prerequisite that image, snapshotter, cache,
  temporary files, and output all reside on the external NVMe.
- No force-free example was run, and none is represented as gravity-solver
  validation.

The next CONCEPT operation is not another install command. A pre-existing
container runtime with all persistent and transient roots bound under
`/mnt/sn850x2t` must first be supplied or authorized as a separate system
operation. Only then may a new bounded pull/sample work unit be considered.

### Native Bianchi Boltzmann / BASS solver input

Status: `WAIT_FOR_USER_NATIVE_SOLVER`.

No authenticated solver package or `SolverDeliveryReceipt` is present. The
repository’s existing `bass-py` package is not a substitute for the missing
user-supplied native solver. No solver was invented, fetched as an equivalent,
or reconstructed. When the exact package and receipt arrive, validate them in
a separate bounded ingestion using
`$HTT_XFI_BUNDLE/schemas/solver_delivery_receipt.schema.json`. This blocker
does not stop Track-I data or runtime use.

### FFP10 Commander `00002`--`00006` completed candidates

Status: `OFFICIAL_PLA_OBJECTS_DOWNLOADED_CANDIDATE_ONLY`.

The five exact basenames were queried directly through the official PLA
product endpoint. For each object, bounded HEAD plus GET/Range inspection and
the full transfer returned FITS content with a matching
`Content-Disposition` basename. A failed HEAD was never treated by itself as
product absence, and no HTML response was accepted as FITS. The server did not
state a release identity, ETag, Last-Modified validator, content length, or
publisher checksum. Those absences remain distinct from the verified official
object connection and from the locally computed SHA-256 values.

Candidate root:

```text
$HTT_XFI_WORKDIR/raw/planck_ffp10/commander/candidates/
  COMMANDER-FFP10-DOWNLOAD-20260829T144340Z-64adad
```

| Basename | Bytes | Local full SHA-256 | Product / transfer / FITS integrity | Publisher checksum | Science admission |
|---|---:|---|---|---|---|
| `dx12_v3_commander_cmb_mc_00002_raw.fits` | 603,987,840 | `f60ca3eb2bb358dc7decc1eed40478dc03b81c6b65ab188323d05b94e2c6371f` | `VERIFIED_OFFICIAL_PLA_OBJECT / PASS / PASS` | `NOT_PUBLISHED_OR_NOT_EXPOSED` | `NOT_ADMITTED_CANDIDATE_ONLY_FROZEN_GATE_UNCHANGED` |
| `dx12_v3_commander_cmb_mc_00003_raw.fits` | 603,987,840 | `ae7e5c38b23ba0b7e6f1aeba194ac95907d71b78d7723544fc0ad2ef678f7628` | `VERIFIED_OFFICIAL_PLA_OBJECT / PASS / PASS` | `NOT_PUBLISHED_OR_NOT_EXPOSED` | `NOT_ADMITTED_CANDIDATE_ONLY_FROZEN_GATE_UNCHANGED` |
| `dx12_v3_commander_cmb_mc_00004_raw.fits` | 603,987,840 | `db158f6087f1c2c2892849e25ee5fff5612b2dc5c28647bed5fbb64f90eb5fd9` | `VERIFIED_OFFICIAL_PLA_OBJECT / PASS / PASS` | `NOT_PUBLISHED_OR_NOT_EXPOSED` | `NOT_ADMITTED_CANDIDATE_ONLY_FROZEN_GATE_UNCHANGED` |
| `dx12_v3_commander_cmb_mc_00005_raw.fits` | 603,987,840 | `020dada034c0f2da0fa18d27f7a53628a705463c7dc37f62ea7578f69822dbf5` | `VERIFIED_OFFICIAL_PLA_OBJECT / PASS / PASS` | `NOT_PUBLISHED_OR_NOT_EXPOSED` | `NOT_ADMITTED_CANDIDATE_ONLY_FROZEN_GATE_UNCHANGED` |
| `dx12_v3_commander_cmb_mc_00006_raw.fits` | 603,987,840 | `749fbb82fc69bc05d729a9e78e743ae110c4901d1b4b8a86a96f8f9408d50354` | `VERIFIED_OFFICIAL_PLA_OBJECT / PASS / PASS` | `NOT_PUBLISHED_OR_NOT_EXPOSED` | `NOT_ADMITTED_CANDIDATE_ONLY_FROZEN_GATE_UNCHANGED` |

Every transfer started from byte zero because the server exposed no validator
that could prove an existing partial represented the same remote object. Full
local SHA-256 and Astropy FITS structure/data-access checks passed before
same-filesystem atomic rename. These locally computed hashes are not called
publisher checksums. The exact release remains `UNSTATED_BY_RESPONSE`.

The five pre-existing `.partial` files under
`$HTT_XFI_WORKDIR/raw/planck_ffp10/commander/cmb_mc` remain untouched:

| Preserved partial basename | Bytes |
|---|---:|
| `dx12_v3_commander_cmb_mc_00002_raw.fits.partial` | 600,042,444 |
| `dx12_v3_commander_cmb_mc_00003_raw.fits.partial` | 262,115,328 |
| `dx12_v3_commander_cmb_mc_00004_raw.fits.partial` | 314,126,336 |
| `dx12_v3_commander_cmb_mc_00005_raw.fits.partial` | 112,553,984 |
| `dx12_v3_commander_cmb_mc_00006_raw.fits.partial` | 76,951,552 |

Independent preservation verification rechecked all four predecessor receipt
hashes, all five partial sizes/inodes/devices/mtimes/first-64-KiB hashes, and
all five candidate sizes. No candidate was added to the current null pool and
the fixed science-admission gate was not modified. This optional candidate
lane does not block analysis using already admitted data.

## Receipts and machine-readable evidence

These paths are host-local execution evidence. Copying this Markdown file to
another machine does not transfer the data, environments, or receipts.

| Evidence | Local path | SHA-256 |
|---|---|---|
| Latest resolution report | `$HTT_REPO/.agent-harness/runs/EXTERNAL-FUSION-RESOLUTION-20260829.pending/artifacts/RESOLUTION_REPORT.md` | `d7fdfc4ef5d8de17f918312d2c0e892450525178829476e6df4614409e5ac7e8` |
| Resolution ledger | `$HTT_REPO/.agent-harness/runs/EXTERNAL-FUSION-RESOLUTION-20260829.pending/artifacts/RESOLUTION_LEDGER.json` | `43b924fa32400b8240b6ee55980d9ae26fae2b69ab72ed2e6af15a7e5cad3385` |
| Readiness matrix v2 | `$HTT_REPO/.agent-harness/runs/EXTERNAL-FUSION-RESOLUTION-20260829.pending/artifacts/SCIENCE_READINESS_MATRIX_v2.json` | `31c94a2eebd7aa7d40ce9b1fc33bc756956dca55cfa4bd56ed2c48ad0b9db214` |
| Download decisions | `$HTT_REPO/.agent-harness/runs/EXTERNAL-FUSION-RESOLUTION-20260829.pending/artifacts/DOWNLOAD_DECISIONS.json` | `d96a411f302c7b8b3fc420469384e6622131277906dfd45d1e6bb6d5a0e2b3b0` |
| Baseline readiness matrix | `$HTT_REPO/.agent-harness/runs/EXTERNAL-FUSION-FOLLOWUP-20260829/artifacts/SCIENCE_READINESS_MATRIX.json` | `9aed29dc801b7a6f3ce8e71951877c8a26b7d5048be0ab73a53ce10328a5bccf` |
| Installation/holdings ledger | `$HTT_REPO/.agent-harness/runs/EXTERNAL-FUSION-INSTALL-20260829/artifacts/XFI-INSTALL-LEDGER.md` | `6b575be2b4767d5f045c6bf0a40d91e46082bfeb9aa665d53af15ff01e748380` |
| Exhaustive fixed inventory | `$HTT_REPO/.agent-harness/runs/EXTERNAL-FUSION-INSTALL-20260829/artifacts/XFI-WORKDIR-001.inventory.json` | `71e8792d2dc3dd0dd7d8b7b2c19a3709d66945600f396f2851cfe4545724297b` |
| `sbibm` receipt | `$HTT_XFI_WORKDIR/external_tools/logs/external-fusion-resolution-20260829/sbibm/RECEIPT.json` | `09f39a94e4aee17dcf90ae15a0c608beefad38419cf59e2cf34aa463d2fa4105` |
| CONCEPT receipt | `$HTT_XFI_WORKDIR/external_tools/logs/external-fusion-resolution-20260829/concept/RECEIPT.json` | `8fbd5775ca3b15c2047d1ec00657833fc45f53c8032437e29ff7cf7556e83ed7` |
| Commander receipt | `$HTT_XFI_WORKDIR/external_tools/logs/external-fusion-resolution-20260829/commander/RECEIPT.json` | `c5f6202a95124afcd9b0e58497ad7f9f0f65afff17ccbc69e7c18d12b63a2777` |
| Commander exact product binding | `$HTT_REPO/.agent-harness/runs/COMMANDER-FFP10-DOWNLOAD-20260829T144340Z-64adad.pending/artifacts/COMMANDER_PRODUCT_BINDING.json` | `309d1d3e419f276b6311cc69103d6e2346810944edd79502f82e80e8aa198852` |
| Commander download receipt | `$HTT_REPO/.agent-harness/runs/COMMANDER-FFP10-DOWNLOAD-20260829T144340Z-64adad.pending/artifacts/COMMANDER_DOWNLOAD_RECEIPT.json` | `5b3da1e0501784fafb90202892592048351b0cc33eb9b8724f8a630f00b2216e` |
| Commander storage receipt | `$HTT_REPO/.agent-harness/runs/COMMANDER-FFP10-DOWNLOAD-20260829T144340Z-64adad.pending/artifacts/COMMANDER_STORAGE_RECEIPT.json` | `36a11df0da9088c94b528fccfd7b84e92a3409f7d4bfc8ff302f597937ca9a6f` |
| Commander bounded closeout | `$HTT_REPO/.agent-harness/runs/COMMANDER-FFP10-DOWNLOAD-20260829T144340Z-64adad.pending/artifacts/COMMANDER_CLOSEOUT.md` | `cca95feaa49a5ef398da0e12237da13d85b24dcac1e428adfaa3d9d35fb81e12` |
| Scalar-consumer selection | `$HTT_REPO/.agent-harness/runs/SCIENCE-CONSUMER-20260829T155108Z-88d569.pending/artifacts/ANALYSIS_SELECTION.json` | `454419556ae888c172e98b01d0acc6bbddc539c24f66bb380533123b02950e0e` |
| Scalar-consumer frozen config | `$HTT_REPO/.agent-harness/runs/SCIENCE-CONSUMER-20260829T155108Z-88d569.pending/artifacts/INPUT_AND_RUN_CONFIG.json` | `69682a10a2d0800c026d73c0246bc5cfde7d1ce18b7e59076cfb95baecab19a3` |
| Scalar-consumer numerical result | `$HTT_REPO/.agent-harness/runs/SCIENCE-CONSUMER-20260829T155108Z-88d569.pending/artifacts/NUMERICAL_RESULT.json` | `560f81358b42d539b998383d00541689ca9dc56bf73b06f2733e21452fead215` |
| Scalar-consumer generating script | `$HTT_REPO/.agent-harness/runs/SCIENCE-CONSUMER-20260829T155108Z-88d569.pending/artifacts/RUN_CONSUMER.py` | `b1e1b8d5c02422923df671b0e941a0ab5eb75dd2802c05f67a55aca27d2bef2b` |
| Scalar-consumer diagnostic figure | `$HTT_REPO/.agent-harness/runs/SCIENCE-CONSUMER-20260829T155108Z-88d569.pending/artifacts/DIAGNOSTIC_FIGURE.png` | `d700a29ffb7193b5f4f886f76d11355913931ed105020f9339dfee24de8dffa5` |
| Scalar-consumer figure provenance | `$HTT_REPO/.agent-harness/runs/SCIENCE-CONSUMER-20260829T155108Z-88d569.pending/artifacts/FIGURE_PROVENANCE.json` | `1b84be4c6dbb7e1f7fea2e70c3f6392b88a91516d71781af0fd3fe5a067011d9` |
| Scalar-consumer closeout | `$HTT_REPO/.agent-harness/runs/SCIENCE-CONSUMER-20260829T155108Z-88d569.pending/artifacts/SCIENCE_CONSUMER_CLOSEOUT.md` | `e3b4635207a466a4129587957a081546146b1b7ce622fa0e9336f7da2d0638e1` |

The resolution artifacts are under a `.pending` run directory because a
different parallel active-run pointer already existed. “Pending” here is a
run-registration/storage fact, not a scientific PASS or FAIL classification.

## Claim boundary and safe next use

Installation, import, CUDA, header, schema, SACC, transfer, and tiny-operation
results in this document remain C0 operational evidence. The executed
PR3/FFP10 scalar consumer is the sole added C2 result and remains explicitly
`CONDITIONAL / DIAGNOSTIC_ONLY` under its fixed pool, mask, scalar formulae,
and rank operator. It does not establish native BASS transfer validity,
Bianchi geometry or family identification, physical shear/vorticity,
unconditional significance, model evidence, likelihood validity, cosmological
inference, or publication readiness. Transfer-dependent outputs remain
transfer-conditional. MIO certificates remain diagnostic-only, and HTT retains
ownership of model-dependent inference.

Further scientific use should continue with one already-ready family or a
specifically justified partially resolved lane using its exact admitted path
and consumer. The completed Commander candidates do not create a reason for
another general installation, bulk acquisition campaign, or silent null-pool
expansion.
