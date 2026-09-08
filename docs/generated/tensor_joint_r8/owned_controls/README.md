# Owned flow and PR3 component controls — Unit E

These are new **descriptive observed-data controls (C0)**, produced from inventory-named workstation inputs. They do not establish an independent likelihood, covariance, empirical rank, physical response, global tilt or Bianchi family. R7 numerical records and source pins are unchanged. Full R8 acceptance remains incomplete.

## Flow reconstruction controls

The original CF4 table4 order and all **38,053 unique PGC group IDs** are retained in [field_rows.npz](execution/field_rows.npz). The common query coordinates use published Galactic longitude/latitude and `r_h = V3k/100 Mpc/h`. This is a fixed **redshift-position proxy**, not an inferred true distance. Forty-nine nonpositive-redshift rows remain unavailable. Published luminosity distances and Vpec are retained separately; no uncertainty conversion or diagonal covariance is invented.

| Released field | Available rows | Status |
|---|---:|---|
| Carrick 2M++ | 23,634 | Galactic XYZ/CMB velocity, 4 Mpc/h smoothing; released beta=0.43 and external bulk already included |
| CORAS zCMB | 23,601 | Original 201^3 ASCII rows, CMB velocity, 5 Mpc/h smoothing |
| Lilow 2MRS | 23,510 | Existing PR319 selected members and grid convention, 3 Mpc/h smoothing |
| CF4++ | 0 | REFUSED_SOURCE_AXIS_AMBIGUITY; all input rows retained |

Coordinates are queried directly in Mpc/h; no common fitted h is assigned to the different source models. The existing PR319 h=0.6711 is used only in its donor parity coordinate conversion. All 23,510 available Lilow predictions agree with the old donor to **6.07e-12 km/s** in the independent check. Trilinear interpolation requires every corner to lie within released support and be finite; source padding never becomes an accepted zero velocity.

The [flow figure](execution/flow_controls.png) preserves each field's available scatter on the left. Comparative residual medians on the right use the same **23,491-row support intersection**, in fixed 25 Mpc/h depth bins. Residuals are field outward velocity minus published CF4 Vpec. They are descriptive summaries, not confidence intervals or independent goodness-of-fit tests: reconstructions can share galaxies, distances and calibration with CF4. The product-specific quantiles in [fields.json](execution/fields.json) retain each product's own support and explicitly recorded row count.

CF4++ has a concrete source inconsistency at 125 fixed asymmetric voxel indices: the published Cartesian lookup gives radial-projection RMSE **343.7593 km/s** against the released radial grid, while an x/y-swapped diagnostic projection gives **1.30e-13 km/s**. This does not identify which spatial/component convention needs repair. The adapter refuses the product; it does not silently permute axes. Pointwise HMC scatter is not a full covariance.

Source semantics were checked against the owned README/headers and [CORAS grid documentation](https://github.com/rlilow/CORAS#reconstructed-fields-on-a-grid), [CORAS original row writer](https://raw.githubusercontent.com/rlilow/CORAS/main/exe/compute_reconstructed_fields_on_cartesian_grid.cpp), [Lilow release](https://github.com/rlilow/2MRS-NeuralNet), and [CF4++ published lookup example](https://projets.ip2i.in2p3.fr/cosmicflows/retrieve_CF4pp_grid_values.py). CF4++ is the Courtois 2025 release, not the distinct Valade 2024 reconstruction. Original fields are not redistributed here.

## Same-sky PR3 component controls

Four owned released maps (SMICA R3.00, Commander R3.00, NILC R3.00 and SEVEM R3.01) were read in K_CMB, NESTED NSIDE2048, Galactic frame. Valid temperature and TMASK>=0.5 are required. Pixel averages are reduced to RING NSIDE64; a coarse pixel is valid only when all high-resolution contributors are valid. Their intersection contains **36,433 of 49,152 pixels**. A joint ell=0…5 fit is performed before retaining ell=2…5, full Q/O and absolute frame. Measurement covariance remains unavailable. Released anisotropy is not an absolute thermal sky response; no beam deconvolution or released experiment/null law is supplied.

| Product | Diagnostic f_B | C2 [K^2] | C3 [K^2] |
|---|---:|---:|---:|
| SMICA | 0.875534 | 2.996906e-10 | 4.206319e-10 |
| Commander | 0.851136 | 2.921626e-10 | 4.199319e-10 |
| NILC | 0.883147 | 2.910437e-10 | 4.236947e-10 |
| SEVEM | 0.867900 | 2.736933e-10 | 4.189283e-10 |

[Full records and processing](cmb/cmb.json) include the 16-component packet, ordinary power/bispectrum features and all retained coefficients. [Saved maps/tensors](cmb/cmb_controls.npz) support the [coefficient/f_B plot](cmb/cmb_coefficients.png) and [same-sky differences](cmb/same_sky_differences.png). All difference panels use the same symmetric +/-54.3094 microK scale with neutral zero. Component differences are correlated same-sky controls, not independent constraints. Full MV ablation is still a separate Unit B obligation. Actual rank is **NOT_EXECUTED_PRODUCT_LAW_UNAVAILABLE**.

## Validation and reproducibility

The existing workstation Python/import tree was used. Missing-implementation RED, first GREEN and final selected tests are retained in `.agent-harness/runs/R8-E-20260909/raw_logs/`. Final command:

```bash
PYTHONPATH="$PWD/htt/htt:$PWD/htt/src:$PWD/htt:$PWD" PYTHONDONTWRITEBYTECODE=1 \
/mnt/sn850x2t/htt_base_e2e/venvs/htt_base-py312-20260829/bin/python -B -m pytest \
-o addopts='' --import-mode=importlib tests/r8/test_field_controls.py \
tests/r8/test_product_intake.py tests/r7/test_cmb_product_response.py \
tests/r7/test_tensor_orbit.py -q
```

**14 passed in 3.10s.** Independent field review additionally checked all IDs, outward projections, support corners and every available Lilow row against PR319. Independent CMB review ran four tests plus a NESTED downgrade fixture, repeated all four saved-map fits exactly (rank36), and checked 13 original high-resolution parent groups per map. These checks do not certify a cut-sky continuum, beam response or sampling law.

Both reviewers identified a plotting issue: unequal/asymmetric map colors and unpaired field-support comparisons. One scoped repair fixed both, with original failure envelopes, script and initial plots preserved under `.agent-harness/runs/R8-E-20260909/artifacts/initial_render/`. Both closeout reviews pass. Parent directly opened all three final PNGs. Scientific data were not regenerated for these rendering repairs. The initial script snapshot identifies the producer of the numerical outputs; final `figures.json` binds the current renderer and saved NPZ inputs. Source identity is product/release/header/path metadata plus existing selected Lilow pins; no blanket full-FITS or whole-storage rehash was performed.

Reproduce each numerical branch in a new directory with `scripts/observed_runs/run_r8_owned_controls.py --run-dir <new-dir> --part fields|cmb`; `--part render` reads saved results only. This standalone Unit E driver has not yet been wired into all final Unit G campaign actions. Missing field/covariance/product-law outcomes remain scoped; no previous failure is erased.
