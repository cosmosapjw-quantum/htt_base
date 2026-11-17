# R64: likelihood and tensorized five-variable interpretation

This document consumes the canonical R39/R58 continuation, the R63 five-variable source map, and the actual R64 source-integrated full36 experiment. It does not introduce five independent data sets or five primitive fit parameters.

## Observation and parameter spaces

The observations are y_m in R^36, four overlapping observed-redshift windows of `[monopole,polar3,STF5]`, with their same jointly propagated C_m. The source mean is `eta_repo=g n.V+sum_j P_j b.a_j`. The parameter vector is theta=(V3,a0_9,...,aJ_9); the a_j include signed monopole, vector and STF components. Retaining the monopoles is necessary for distance derivatives. A norm or a chosen x_C cannot replace this carrier.

The free V coefficients multiply a first-order tangent template. The Gaussian experiment does not certify small per-source `g_i n_i.V` or a finite-amplitude response remainder. Its template-subtracted distance image is conditional on this statistical decomposition; it is not an admitted physical velocity deboost. R8 extends the same construction to68/72 correlated rows and, when selected, profiles24 method-angular nuisance directions after full-C whitening. The normalization below uses the appropriate observation dimension in each experiment; original36 is the base case displayed here.

The exact fixed-experiment linear Gaussian likelihood is

    -2 log L(theta|y_m) = ||L_m^-1(y_m-X_m theta)||^2
                          + log det C_m + 36 log(2 pi),
    X_m = O_m B_source, C_m = L_m L_m^T.

The saved carrier retains J=X^T C^-1 X, t=X^T C^-1 y, the normalization, stable whitened factor and null basis. Numerical rank uses both declared physical scales and column equilibration, as in R58. A pseudoinverse covariance describes an estimator representative; confidence sets extend without bound along genuine nulls.

This is ordinary GLS. Tensorization adds no Fisher information to a complete Gaussian likelihood. Its practical role is to keep the signed physical/observational coordinates and their dependence through calibration quotient, depth transport and nonlinear optical images. Discarding signs or cross-block covariance before those operations can lose the relevant information; giving the retained structure new names is not a new statistical theorem.

## Physical likelihood pullback

If a qualified congruence/optical model with physical variables vartheta=(Theta,sigma_ab,A_a,omega_a,beta_a,...) predicts the processed source distances and redshifts, use

    -2 log L(vartheta,gamma|y_m)
      = ||L_m^-1[y_m-O_m eta_processed(vartheta,gamma)]||^2 + normalization,

where gamma contains source calibration, selection and velocity nuisances. This requires actual endpoint frames, optical focusing and source measurement definitions. The physical model does not follow from the covariance alone. If its mean lies in the declared column space, eta_processed=B_source theta(vartheta,gamma), the finite parameter carrier can be pulled back. Otherwise the full36 observation and a newly evaluated O_m eta_processed must be used; an old model-specific score is not sufficient for arbitrary new source laws.

At a smooth same-congruence vertex, the leading directional coefficient is Hcal=Theta/3+sigma:nn-A.n/c. Vorticity is absent from this symmetric null contraction. Finite-z distance derivatives additionally involve the Sachs optical solution, as derived in THEORY.md. Thus current a_j are not automatically sigma, A or their proper-time derivatives. No extrapolation to z=0 or posterior on general physical kinematics is admitted by this experiment.

## Actual five views and their decisions

| View | R64 object | Decision it supports |
|---|---|---|
| x | Full signed theta carrier and 9-component eta(z)-eta(.04) path; corresponding H_D/q_D image only where defined | Which directional/depth combinations are measured, weak or null |
| Q | sqrt(Delta chi2 / chi2_delta-rank(.95)) for a predeclared nested radial-angular null | Statistical distance from the zero radial-angular mean in its identified quotient; no physical MES bound |
| Pi | Upper chi-square tail of that same nested LR under the fixed C Gaussian law | Conditional null compatibility; not truth probability or independent evidence |
| F | Infimum/supremum of signed linear depth functionals over the common rank-r confidence cylinder | Whether sign, finite size and derivative-denominator positivity are supported; unbounded supports remain explicit |
| G_F | Joint depth path at z=.025,.06,.08 relative to .04, with complete cross covariance and null projections | Radial coherence and transport; not a claim that G_F is universally a derivative of F |

F is the support view of the tensor continuation, not an invented sky occupancy probability. A physical anchor for support utilization is unavailable. The Q anchor is explicitly a statistical noise reference. Nonlinear H_D/q_D intervals use enclosing support boxes from one joint set, so they can be conservative but do not assume independent coordinates. They do not turn a failed positive-domain certificate into a bounded physical confidence interval.

The finite calibration action is `y -> y+O b a`, represented by a0. Common l<=2 angular offsets leave identified radial contrasts unchanged. An l=3 angular injection is applied at the real source positions to measure the failure of extending this invariance to arbitrary omitted angular functions. Redshift-dependent calibration can share the radial source columns themselves; it requires upstream information or an explicit allowed bias set.

## Comparison and inference limits

All seven operators use overlapping actual data. Modelwise results are sensitivity alternatives and cannot be multiplied. J1, J2 and J3 are distinct finite smoothness assumptions; increasing polynomial degree does not supply new observations. Fit adequacy and held-window predictions decide whether a low-order finite mean is usable. The J3 null witness concerns the declared 36-row family, not a universal impossibility of measuring directional Hubble evolution.

The observation law includes inherited distance noise and linear-z0 peculiar-velocity covariance. It does not certify actual shared calibration/group uncertainty, an empirical selection law or the full heterogeneous distance-deboost operation. A p-value here has that finite conditional interpretation. Closing those source requirements, and comparing like-for-like estimands with existing CF4 analyses, is necessary before turning this R64 result into a journal submission.
