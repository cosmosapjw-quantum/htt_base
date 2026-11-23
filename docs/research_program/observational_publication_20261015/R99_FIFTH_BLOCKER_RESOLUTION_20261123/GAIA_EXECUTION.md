# R99 Gaia shared-field execution

The R99 field model uses the full-source R98 sufficient statistics, with a SHA-verified cache and all ten fit definitions. No raw catalogue rescan was required. This explicitly preserves the shared sky between source selections and four Quaia redshift bins. `scripts/r99/gaia_shared_field.py` writes the result and the complete model covariance arrays.

Commands (cwd `/home/cosmosapjw/Dropbox/bianchi/htt_base`, OMP_NUM_THREADS=OPENBLAS_NUM_THREADS=MKL_NUM_THREADS=1, PYTHONDONTWRITEBYTECODE=1):

```
.venv/bin/python -B -m pytest -q -p no:cacheprovider tests/obsstat/test_r99_gaia_shared_field.py
.venv/bin/python -B -m scripts.r99.gaia_shared_field
```

Both exited 0. Twelve tests passed in 0.30 s. Tests include direct perturbed normal equations, constant-field cancellation, independent finite random-field covariance, rigid sky rotation, PSD, forbidden negative kernel and singular design, and an explicitly nonzero unsupported covariance-nullspace component. Production computation took 0.0497 s after loading dependencies. Commands, thread environment and elapsed observations are in GAIA_VALIDATION.json; stdout is preserved in GAIA_unit.log and GAIA_full_source_statistics.log.

Actual source RHS refits and J response agree to 5.3291e-15 microas/year across ten fits. The common constant field cancels between the lowest/highest redshift fit with maximum coefficient-response error 4.0766e-16. Chord-kernel scales 15, 30 and 60 degrees were evaluated with one microas/year per Cartesian glide/spin component. Resulting covariance contributions are in GAIA_SHARED_FIELD_COVARIANCES.npz and their interpreted summaries in GAIA_SHARED_FIELD_RESULTS.json.

At scale 30 degrees, the low/high redshift contrast has systematic variance trace 0.00280152 times the independent-field construction. This is an exact contrast within the declared coarse field family, not an empirically calibrated error bar. An E2 coefficient difference of the observed norm matches the scenario field RMS only for coefficient amplitude 61.4193 microas/year; the corresponding B2 value is 50.5739. These matching amplitudes are neither parameter estimates nor detections. Intra-patch correlation and source AGN offsets remain outside the model.

The original 160D patch covariance has rank 47. Its supported quadratic form reproduces 524.5928366832661. The observed coefficient vector has Euclidean norm 33.2032 microas/year; its unsupported component has norm 14.4109, or 18.8374% of squared Euclidean coefficient norm. That part of the vector is absent from the quadratic-form test. This percentage is a coefficient-space geometric fact, not a fraction of physical sky power. No covariance inverse or chi-square probability was assigned to the omitted subspace.

C_sys is NOT added to the spatial jackknife covariance: the latter may already contain the same scan/sky variation. A calibrated total source law needs independent measurement cross-covariance, externally constrained spatial parameters and AGN effects. The present result removes the implementation gap for a common angular nuisance response and identifies its exact common-mode cancellation, while D04/M05 source qualification remains open.

## C9 targeted repair

The single independent review reproduced a unit-dependence defect in supported_subspace: the absolute 1e-30 eigenvalue floor changed rank when coefficients and covariance were rescaled by t and t^2. The repair uses a strictly positive largest eigenvalue for a relative cut, an explicit zero-covariance branch, standardized projection/sqrt(eigenvalue) terms, and stable Euclidean norms. Regressions cover t=1e-21, 1 and 1e21 and the zero covariance.

Thirteen tests passed in 0.34 s after the repair. The production source-statistics run was repeated to bind the repaired code SHA; all actual-source scenario results are unchanged, rank remains 47, and the supported quadratic form changes only from 524.5928366832661 to 524.5928366832662 at roundoff. GAIA_C9_REPAIR.json records commands, exit0 and timings; GAIA_C9_unit.log and GAIA_C9_full_source_statistics.log preserve output. The independent reviewer also reproduced the real unsupported norm and quadratic form using SVD of the 48 delete-one vectors, without the production eigenvalue path.
