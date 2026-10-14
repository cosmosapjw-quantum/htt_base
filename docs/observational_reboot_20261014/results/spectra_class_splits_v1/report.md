# Class Dr1 Native Unit Split And Coadd Contrasts

Owner: OBSSTAT. Diagnostic-only; scientific admission not evaluated.

Source: [release documentation](https://lambda.gsfc.nasa.gov/product/class/class_dr1_pol_maps_info.html). Exact methods, arrays and limitations: `result.json`; source/code/runtime receipt: `execution_receipt.json`.

- 40GHz filtered frequency maps; not foreground-cleaned CMB
- Header K converted by scale only; antenna versus thermodynamic convention not inferred
- M1/M2 are approximately balanced base splits; half difference is a descriptive contrast, not a certified noise covariance
- Coadd is compared with half sum, not assumed to equal it
- QQ/QU/UU fields are hits in seconds, not Kelvin-squared noise covariance
- No spin transform, HDF5 transfer inversion, noise ensemble, or calibrated significance
- h5py unavailable in inspected environment; transfer decode remains separate
