# OBS-03 independent review

Decision: `SCOPED_PASS_OBS03_SYNTH_V1`, with no blocking findings or required repairs for the frozen manufactured candidate. Real CF4 likelihood, physical interpretation, and scientific admission remain `HOLD`.

The fresh reviewer was read-only and separate from the implementation author. Requested reviewer: `gpt-6-astra/xhigh`; observed runtime identity: `UNKNOWN`. Reviewed branch `obs/obs03-cf4-latent-20261013` from base `c3c2e5f00757d5e7c57d6df149db86f82dc59cfa`. The core, script, tests, contract and recorded result hashes matched at review completion.

Independent checks: seven focused tests passed in 1.92 seconds (exit 0). All 128 catalogues were regenerated without refitting; observations, anchors, labels and proposal counts matched. Stored objectives, Hessian-derived intervals, coverage (B 121/128, A 123/128), exact binomial intervals, lower-tail probabilities and bias summaries recomputed. Twelve adaptive double integrals across six rows at truth and fitted parameters agreed at maximum log-numerator error 2.14e-14 and log-selection error 1.12e-14. Two bounded order 96×72 refits were stable, with maximum relative standard-error change 2.39e-11. The actual 38,053-group descriptive analysis reproduced all nine spectra, ranks and method counts with the recorded table3/table4/ReadMe source hashes.

The reviewer confirmed the joint latent relation, parameter-dependent selection normalization, one shared calibration anchor, full joint Hessian treatment, and failure handling. Far-shell deletion remains `NUMERICAL_HOLD` at the A=-30 boundary with no interval. The local SVD uses a shell-centre/Gaussian-proxy response and is distinct from finite-width integrated likelihood information. Coverage is a coarse single-truth check of approximate marginal Wald intervals under a manufactured law. The synthetic identity observer transform avoids a second use of CMB-frame data but does not settle the real transform.

Real CF4 selection, covariance, calibration mapping, source motion, observer transformation and physical remainder inputs remain open. No actual CF4 response was fitted. The reviewer performed no publication or code edits.
