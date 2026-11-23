# SQ-CF4 shared-field prediction

Springob et al. (2014), Table 1, gives 8,885 published 6dFGSv galaxy log-distance ratios, widths and CMB-frame individual and group redshifts. The authors adopt group redshifts where available. Their §4 and equations (20)–(22) describe per-object distance distributions, including a skew correction whose cubic approximation can become negative in the wings. The Gaussian mark model here reuses the Gaussian approximation in R101–R102. The CF4 crossmatch indicator labels the release-to-release match and therefore conditions a working transfer between two published products. Primary sources: https://arxiv.org/abs/1409.6161 and https://www.mso.anu.edu.au/6dfgs/vfield/3dvfield.html .

Under the R102 scenario, one field index f selects a line-of-sight radial speed shared by all galaxies. For row i, observed mark y (dex), and working width s (dex), let Y_i|f ~ N(mu_if,s_i^2), P(I_i=1|Y_i)=Phi(a_i+b_i Y_i). Linear-Gaussian marginalization gives q_if=P(I_i=1|f)=Phi((a_i+b_i mu_if)/sqrt(1+b_i^2 s_i^2)). The train-only fit supplies a_i,b_i. It uses the published parent marks, including marks unavailable to the matched-mark outcome model. For a block B of conditionally independent rows define

    A_Bf = product over matched i of normal(y_i;mu_if,s_i) Phi(a_i+b_i y_i)
           times product over unmatched i of (1-q_if),
    D_Bf = product over matched i of q_if times product over unmatched i of (1-q_if).

Training observations update the finite prior pi_f to w_f proportional to pi_f A_train,f. Conditioning the prediction also on test inclusion gives

    p(y_test,selected | y_train,selected, I_train, I_test, beta_hat)
       = sum_f w_f A_test,f / sum_f w_f D_test,f .

The fresh-prior comparison uses pi in place of w, independently in every test fold. Each expression has units of inverse dex raised to the number of matched test rows. Ratios against the same zero-speed predictive density are dimensionless. All-rejected test blocks have A=D, hence log density zero. The signed 5-fold sums are cross-validation scores; their overlapping training sets preclude reading them as a catalogue log Bayes factor. An offset common to all lines of sight remains degenerate with distance calibration. Springob et al. §5.1 describes the survey zero-point constraint.

The implemented log-space updates retain support even for underflowed linear weights. Field-independent scales are preserved in scores. Independent tests enumerate a two-field mixed-inclusion sample directly with normal PDF/CDF products, check no selected test objects, opposing 50-sigma blocks, and invalid partitions. The 7 inherited R101 tests and 4 new tests passed. The source run binds 55,877 CF4 Table-2 rows and 8,885 6dFGSv rows by SHA-256 before using the unchanged 15-arcsec/500-km/s unique-match policy. All 8,885 rows enter exactly one test fold per linkage convention. Its R102 fresh-prior baselines reproduce exactly.

Using individual cz in the transfer gives shared-field scores of 25.24373 (PGC) and 25.48934 (PGC1), versus 30.75111 and 26.70701 for fresh priors. Replacing only the transfer redshift by published group cz when available changes 2,653 rows (2,666 grouped) and yields 24.86517 and 24.92333. Matching and selection fitting still use individual galaxy cz as in R102. A frozen selection law is refitted on each training fold. These values carry no correction for selection-parameter uncertainty, raw inter-survey zero-point covariance, or a calibrated spatial PV-field prior.

Run from the active checkout:

    PYTHONPATH=.:htt:htt/src OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 .venv/bin/python -B -m scripts.r103.cf4_shared_field_holdout --output /tmp/CF4_SHARED_FIELD_HOLDOUT.json
    PYTHONPATH=.:htt:htt/src .venv/bin/python -B -m pytest -q -p no:cacheprovider htt/htt/tests/test_cf4_shared_field_holdout.py htt/htt/tests/test_cf4_predictive_response.py

Input locations and re-acquisition follow scripts/r100/source_intake.py for the 6dFGSv public Table 1 and scripts/r97/cf4_genealogy_and_partial_id.py for the CF4 catalogue. The identity comparisons use the tracked R100 receipt. Independent raw calibrator performances, selection probabilities upstream of the two released products and cross-source correlated S_PV still determine original SQ-CF4 qualification.
