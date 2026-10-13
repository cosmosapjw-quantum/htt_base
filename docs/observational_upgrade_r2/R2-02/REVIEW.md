# R2-02 independent review

Requested reviewer: `gpt-6-astra/ultra`; observed runtime: `UNKNOWN`. The reviewer was read-only and separate from the implementation writer. Final reviewed SHA256 values are recorded in `RETURN.json` for the provider, tests, and diagnostic script.

**Verdict: scoped PASS** for the conditional grouped CF4 adapter and diagnostics. Actual-product scientific admission remains `HOLD_MISSING_ALL_METHOD_SELECTION_COVARIANCE_REMAINDER`.

The first candidate had three blocking defects: prior-centred shared-calibration quadrature returned a wrong finite likelihood for 100 high-information groups, a heliocentric catalogue accepted a CMB-frame provider without transformation, and an omitted finite-distance remainder became zero. The first repair left a delayed factory-binding route for the same remainder omission. Raw failures and intermediate returns are preserved in `raw/` and `PRE_*_RETURN.json`.

Independent closeout confirmed that a positive-bound provider now rejects the omitted remainder both in a selected block and on factory binding; explicitly exact-zero truncated-model paths remain evaluable. The 100-group analytic rank-one Gaussian log likelihood was `-297.5611584731843`; the repaired numerical result was `-297.5611584731847`. Frame mismatch remains rejected. The affected suite reran with **71 passed** in 11.68 s. An extremely narrow factory-mean integral returned `NumericalUnresolved`, which is the declared fail-closed numerical behavior.

The reviewer also reproduced the selected scalar integral to `8.88e-16` absolute agreement and independently reconstructed actual-source SVD for 38,053 full, 19,390 mid-depth and 761 narrow-depth groups; all had local scenario rank 13, with stored singular values agreeing within `1.23e-13` relative error or better. These are sensitivity and implementation checks, not calibrated CF4 posterior coverage or bias estimates. Adaptive quadrature checks are numerical diagnostics, not a formal global error certificate.
