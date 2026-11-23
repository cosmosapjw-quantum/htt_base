# SQ-CF4 conditional prediction on a reconstructed velocity field

At the R104 input identity, all 8,885 6dFGSv parent rows have finite 2MRS-stencil support; 7,190 enter the matched-mark outcome. The observed distance-ratio marks, reported in dex, use the 6dFGSv Gaussian-width approximation. The external reconstructed velocity template is the conditional mean inferred from 2MRS counts. Scalar velocity samples in this calculation parameterize deviations around that template. No spatial residual-field posterior or source-independent joint observation covariance is supplied. Sources: [Springob et al., Table 1 and §4.3](https://arxiv.org/abs/1409.6161), [Lilow et al.](https://doi.org/10.1051/0004-6361/202450219), [author release](https://github.com/rlilow/2MRS-NeuralNet).

The line-of-sight template is evaluated at each parent galaxy's individual CMB-frame redshift using R104's trilinear Galactic-grid interpolant and velocity growth ratio. We use a rank-at-most-two family in **radial velocity space**, with u in km/s, dimensionless alpha and source-specific v_i in km/s:

    v_if = u_f + alpha_f v_i .
    mu_if = finite_shift(z_i, atanh(v_if/c), bolometric)/(5 MAG).

This places outward velocity through the finite-redshift transformation used in R103. Nonlinear transfer need not preserve the linear rank bound in mark space. The five equally weighted u values are −300, −100, 0, +100 and +300 km/s. The five equally weighted alpha values are 0, 0.5, 1, 1.5 and 2. These discrete choices define the working alternative and ensure that alpha=0 and alpha=1 replay the fixed predecessor models. A continuum posterior would be a different model.

For a fixed field f and selection coefficients estimated only on training objects, write Y_i|f ∼ N(mu_if,s_i²) and Pr(I_i=1|Y_i)=Phi(a_i+bY_i). Integration of two independent normal deviates gives q_if=Phi[(a_i+b mu_if)/sqrt(1+b²s_i²)]. Let J_Bf be the product of the selected Gaussian densities times their inclusion probabilities and the omitted rows' 1−q_if on block B. Let D_Bf be the observed-pattern probability, the product of q_if on selected rows and 1−q_if on the rest. The coherent test-mark density is

    sum_f pi_f J_train,f J_test,f / sum_f pi_f J_train,f D_test,f .

The uniform prior is restricted and renormalized for each reported nested model. The fresh-prior comparator drops J_train in both sums. All tabulated log differences are against the zero-velocity score on the same test fold and fixed selection fit. They include the selection-pattern denominator.

For coverage, the predicted field weights given all binary indicators are proportional to pi_f J_train,f D_test,f. The selected-mark CDF for row i at its test value y is

    sum_f w_f (1/q_if) integral_{0}^{Phi[(y-mu_if)/s_i]}
                                  Phi(a_i+b(mu_if+s_i Phi^{-1}(t))) dt .

We apply 32-point Gauss–Legendre quadrature; on every seventeenth selected test object within each fold, doubling to 64 changes the PIT by at most 3.54×10⁻⁶. Marginal central 50/80/95 percent coverage uses these CDFs over held-out matched marks. Treat coverage proportions as descriptive because sources, grouping, folds, and the working field generate dependence. The inference conditions on training-only plug-in selection coefficients.

The alternative finite-field likelihood implementation reproduced all 50 stored R104 fresh-prior, shared-prior and fixed-field fold comparisons to 8.42×10⁻¹² absolute log-score. The original PGC and PGC1 test assignments differ: 1,876 row labels coincide as numbered and even the best permutation matches only 1,979 of 8,885. Thus between-linkage differences also involve distinct test sets. The JSON contains the 5×5 overlap table, hashes of sorted per-fold 6dFGSv source names and per-fold scores.

| Mean template | PGC score vs zero | PGC1 score vs zero |
|---|---:|---:|
| Shared radial offset only | 25.244 | 25.489 |
| Fixed external 2MRS | 25.500 | 25.525 |
| Fixed 2MRS with shared radial offset | 47.869 | 47.885 |
| Shared 2MRS scale only | 25.336 | 25.309 |
| Shared 2MRS scale and radial offset | 46.227 | 46.672 |

Allowing the extra scale costs 1.642 and 1.212 summed predictive log units relative to fixed alpha=1 plus a shared offset. This comparison supports retaining the unit-normalized template for these two working fits. The 25-scenario marginal coverages are 0.539/0.836/0.965 (PGC) and 0.538/0.836/0.965 (PGC1). The aggregate CV scores use overlapping training samples; they are not catalogue log-Bayes factors. A position-dependent residual velocity law, genealogy of overlap between 2MRS and distance-survey inputs, covariance of CF4 zero points, catalogue-level selection and covariance-aware independent holdout remain open.

From the production checkout run:

    PYTHONPATH=.:htt:htt/src PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 .venv/bin/python -B -m scripts.r105.cf4_field_holdout --output /tmp/r105-cf4-field.json
    PYTHONPATH=.:htt:htt/src .venv/bin/python -B -m pytest -q -p no:cacheprovider tests/obsstat/test_r105_cf4_field_holdout.py

Acceptance for numerical replay is absolute log-score error <=1e-7 per existing metric and fold. PIT refinement bound on the checked subsample is 1e-4. Three independent tests check finite-model enumeration using adaptive continuous quadrature, CDFs for both selection slope signs and fold alignment under permutation.
