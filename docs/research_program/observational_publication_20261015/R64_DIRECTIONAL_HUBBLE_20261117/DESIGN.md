# R64: source-integrated directional Hubble evolution

Baseline: `33d87dd3e4a787e477327d37ee00b40e790211c9`; existing checkout only. One owner-selected, sequential ten-stage theory/coding loop. Selected paper P3. No successor loop or local coding-agent prompt. No change to the original 42 science gates.

## R1/C1 — question and completion contract

Can the owned Cosmicflows-4 distance-modulus experiment constrain the redshift evolution of directional distance-defined expansion, after preserving its actual angular/window response, shared covariance, constant angular calibration fibre and coherent velocity nuisance? Produce a finite actual-data answer, the null/weak directions, a publication decision and an executable next-data plan. Do not equate a distance derivative to a general spacetime expansion scalar.

## R2/C2 — reused evidence and novelty boundary

Reuse H01/H03 four-window Hubble operators, H02 source joins and internal holdouts, R32/R37 optical and apparent-Hubble derivations, R54 exact cached covariance and seven calibration operators, R58 original full36 carriers, R61 calibration-invariant depth contrasts and R63 published-redshift chart correction. R58's original `OWNED_TENSOR_CARRIERS.npz` SHA256 is `42f6bc5158fdf2f876720db12c44b088bc2db9734887e0d84ae098b234a7e64d`. Preserve all four monopoles: packing is four blocks `[monopole, polar3, STF5]`.

Log-distance Gaussian inference, harmonic/STF decomposition, radial bins, calibration invariance and distance-derivative H/q reconstruction are not new methods. Relevant primary comparisons include Kalbouneh et al. arXiv:2510.02510v2; Vicente et al. arXiv:2607.07821; Salzano et al. arXiv:2512.02526v2; Seikel et al. arXiv:1204.2832v2; Clarkson et al. arXiv:0712.3457v2. The possible contribution is a concrete source-matched identification/resolution result with reproducible joint confidence images, not the five-view names or generic GLS.

## R3/C3 — definitions and finite mean family

Use signature (-,+,+,+), sourceward observed ICRS n, observed catalogue z, c=299792.458 km/s. The owned numerical eta is ln[c(1+z) chi_hat(z)/D_L(Mpc)], with numerical H units km/s/Mpc. Thus eta_relative=eta_repo-ln(H_ref,0). This normalization is essential for absolute H_D.

Define D_M=D_L/(1+z), H_D=c/(partial_z D_M). For a flat reference chi'=c/H_ref, B=H_ref chi/c=E chi_hat,

    H_D/H_ref = exp(eta_relative)/(1-B eta_z).

The map is evaluated only on D=1-B eta_z>0. An arbitrary z-independent angular zero point multiplies H_D by a direction-dependent constant. Same-direction radial H ratios and q_D=-1+(1+z) partial_z ln H_D are invariant at the uncompressed field level. The finite estimator cancels only calibration functions represented by its nuisance span; omitted higher multipoles and radial calibration are not covered.

For the selected finite source model, use t=(z-.055)/.045 and Legendre P_j(t):

    eta_repo(z,n) = sum_{j=0}^J P_j(t) b(n).a_j + g(z) n.V,
    b(n) = [1,n_x,n_y,n_z,n.E_1.n,...,n.E_5.n].

V is a free coherent velocity nuisance in km/s; the fixed body already includes stochastic linear peculiar velocities. The optical/background eta field whose H_D image is reported excludes this declared nuisance term. Therefore this image is conditional on the velocity decomposition. The complete fitted distance field can also be evaluated, but has a different estimand. Both are separate from general physical congruence expansion.

For each operator m, X_m=O_m B_source, y_m=O_m eta_repo and C_m=C_white+C_body from original R58. Do not evaluate source templates only at window centres. Do not treat different O_m experiments as independent or compare their normalized likelihoods as model odds.

## R4/C4 — bounded implementation and decision plan

1. Predeclared models J=1 (21 parameters), J=2 (30), J=3 (39) with V3. Four windows give 36 rows. J3 is a resolution stress, not a default identifiable 39-parameter estimate. Seven existing operators are sensitivities, not seven independent replications. `log_mono_radial` explicitly projects out source z, so some derivative functionals must remain unidentified.
2. Fit using existing scaled-SVD full-covariance `r58_mixed_tensor_likelihood.fit_linear`. Retain whitened factor, score, precision, null basis, covariance and both rank diagnostics. Report adequacy, not only parameter significance.
3. Test no radial angular evolution: keep a_0 all9, each higher-j monopole and V3, set higher-j dipole/STF to zero. Use nested response rank differences and the same fixed covariance. This is a conditional linear-mean null, not isotropy of the Universe.
4. Evaluate predeclared z=(.025,.04,.06,.08), reference z*=.04 and six Cartesian directions plus a fixed 48-point Fibonacci grid. These directions are diagnostics; no post-selection claim from a discovered preferred axis. Report eta(z)-eta(z*) jointly before its nonlinear H_D/q_D image.
5. For H_D radial ratios, use the same fitted joint region. Exact linear-support bounds on eta differences and each derivative denominator give a conservative enclosing interval if every required lower denominator bound is positive. Otherwise report DOMAIN_NOT_CERTIFIED (not a finite Gaussian error bar). A null-space component makes a functional UNIDENTIFIED. A finite grid certificate does not certify an unsampled continuum.
6. Report five views of the same experiment: signed vector/STF x; a named statistical reference Q; named-law Pi; signed support intervals/utilization F; full correlated depth path G_F. No invented physical MES ceiling, occupancy law or independent multiplication of views.
7. Use four leave-one-window conditional innovation checks for J1: fit retained 27 rows, predict the held 9 using full cross covariance and parameter-estimation variance. They are correlated internal predictive checks on overlapping windows, not independent catalogue/indicator holdouts. J2/J3 do not have an identified 30/39-parameter fit in 27 training rows, so no fabricated predictive score.
8. Reuse R63 actual q correction as deterministic first-order offset with unchanged O,C,X, and compare target shifts. Do not create a second observer measurement. Source-selected arbitrary angular l=3 calibration injection will demonstrate the boundary of the l<=2 invariance claim.

## R5–R10 / C5–C10 — execution and stop rule

Derive the optical/congruence relation and curved-FLRW counterexample; implement small auditable functions and actual source integration; execute one affected verification pass including normalization, null-space, zero-point invariance, domain and covariance cases; perform independent Wolfram/SymPy algebra checks (not a four-axis legacy PASS); execute actual data; judge rank, adequacy, stability and publication scope; close one fresh independent review and at most one bounded correction episode; update P3 companion/DAG and non-force push. Stop after this loop.

The finite Gaussian law is a working law. Actual shared group/calibration covariance, empirical selection and heterogeneous distance transformations remain external source requirements. A strong anomaly under an inadequate finite mean is not evidence for a physical Hubble anisotropy. If flexible models or admitted radial calibration erase identification, retain the measured window/contrast result and revise the paper around finite-resolution information rather than assert a universal no-go.
