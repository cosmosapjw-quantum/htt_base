# Independent delta review: Planck morphology and Hubble coupling

26 October 2026. **PASS_SCOPED_AFTER_TARGETED_REPAIR.** One low-severity wording finding is closed; no open mathematical blocker remains.

This review covers HUBBLE_PROTOCOL.md/.json, PLANCK_EXAMPLE.md/.json, and the numerical portion and saved result of planck_hubble_controls.py. APPLICATION_BRIDGE.md received a bounded consistency skim. The preceding radiation-stress review is not reopened. Only APPLICATION_REVIEW.md and APPLICATION_REVIEW.json were written by this reviewer. No child reviewer, broad literature search, raw-map extraction, dynamical solver or push was used.

## Finding and closeout

**APP-01, low severity, closed.** The initial Planck note said that no new null simulation had been run while the addition included a fresh ideal Gaussian Monte Carlo benchmark. The revised opening explicitly says that it combines local-source verification with a fresh ideal Gaussian benchmark, and excludes only a processed-Planck null simulation. The final benchmark paragraph, JSON and synthesis retain the difference between the new reference calculation and the unverified historical percentile. The corrected text was inspected directly.

## Hubble response and error budget

The physical definitions are consistent with the retained R32-01 manuscript. The vector d=-A/(cH) is dimensionless acceleration of the declared common observer/emitter congruence. It is not a CMB temperature or arbitrary velocity dipole. S=sigma/H is the directional Hubble-slope shear; Q_mu=-kappa S plus its stated nonlinear remainder is the magnitude quadrupole. H and sigma here have inverse-time units. The coupling and its error terms have magnitude units, and the inverse returns dimensionless d.

The stated lift is exactly the STF projection of the symmetric tensor product dS. Its adjoint on STF3 is contraction with S, and

\[
L_T^*L_T=\frac{T:T}{3}\mathrm{Id}+\frac25T^2.
\]

Therefore

\[
\|L_T\|_{op}^2=\frac{\|T\|_F^2}{3}+\frac25\|T\|_{op}^2
\le\frac35\|T\|_F^2.
\]

The last step uses the tracefree three-dimensional bound ||T||op squared <=(2/3)||T||F squared. The factor sqrt(3/5) is attained: T=diag(-1,-1,2)/sqrt(6) has Frobenius norm one and the largest lift singular value sqrt(3/5). Thus the uncertain-shear contribution |kappa|sqrt(3/5)e_S D_max is valid, including its constant. The optional calibration extension correctly writes the change as kappa_true L_deltaS plus (kappa_true-kappa_hat)L_Shat; it includes the cross-effect through kappa_max rather than dropping it. All bounds must hold over the same joint admissible region, as the note states.

The finite-redshift correction has the correct order. A distance remainder O(z squared) is divided by the leading distance proportional to z before taking a logarithm. The relative correction is generally O(z), and hence so is the magnitude correction. The displayed kappa z a1 term and the full-sphere projection bound for a bounded relative-distance remainder follow directly. An O(z squared) magnitude claim needs the first relative correction removed or a separate cancellation. The angular logarithm remainder E3 alone does not bound finite-depth, selection or frame errors.

For fixed nonzero S_hat, M_hat is positive definite. The pseudoinverse and perpendicular component in H8 are correct. Orthogonality of image and kernel gives exactly

\[
\|\widehat O-\widehat\kappa L_{\widehat S}d_{obs}\|^2
=\|\widehat O_\perp\|^2+
\widehat\kappa^2(\widehat d-d_{obs})^T\widehat M(\widehat d-d_{obs}).
\]

Both necessary component tests use the same residual; passing them separately does not imply membership in the common error ball. The candidate's profile over a direct-vector ball is a convex quadratic minimization in three variables. Its value is a conservative necessary test when B is an enlarged outer error envelope. It is not automatically a sharp acceptance region for the original correlated errors or sufficient attribution to a physical mechanism. The note explicitly retains D_max, directional positivity, joint nuisance errors, cross-window covariance, the S=0 singular sector and the B=0 exact-membership case.

## Conditional ideal law for utilization

Fix nonzero simple-spectrum Q and an octupole with positive norm o. The contraction C_Q from the seven-dimensional STF3 space to three-dimensional vectors has rank three, since C_Q C_Q^*=M_Q is positive definite. In its singular coordinates,

\[
v_i=s_i o z_i,\qquad \sum_{i=1}^7z_i^2=1.
\]

The eigenvalue Vandermonde and three singular values multiply |z1 z2 z3| in |chi|. The sharp fixed-Q envelope has the identical prefactor divided by 3sqrt(3), because the product reaches 1/(3sqrt(3)) at equal squared image coordinates and zero kernel coordinates. The ratio is consequently

\[
U=3\sqrt3|z_1z_2z_3|.
\]

If the conditional octupole coefficients are independent centered Gaussians with a common variance in a Frobenius-orthonormal basis, their normalized direction is uniform on S6. Grouping squared coordinates gives Dirichlet parameters (1/2,1/2,1/2,2), and hence

\[
\mathbb E U^s=(3\sqrt3)^s
\frac{\Gamma(7/2)\Gamma((1+s)/2)^3}
{\Gamma(7/2+3s/2)\Gamma(1/2)^3},\qquad s>-1.
\]

This proves the asserted shape independence under that conditional law and yields E U=15sqrt(3)/(64pi) and E U squared=3/77. Repeated quadrupole eigenvalues make the normalized chirality envelope degenerate and are correctly excluded. A random spatial rotation of a fixed octupole does not generate a uniform direction in seven-dimensional coefficient space. Likewise, a masked pseudo-alm covariance need not be isotropic in that space. The candidate does not extend the ideal law to either case.

## Pinned Planck example and scope

The local compact source S1, sections 4.1–4.3 and Appendix B, directly confirms the P / cutoff 32 / zero-window / FULL row: r=0.0582918, C=-0.0967707, U=0.1197448, and the rounded envelope 0.808141. Independent rounded arithmetic gives E(r)=0.8081410859025434 and |C|/E=0.11974480902913767. The cached-pilot C-source row is different and is correctly distinguished. The source footnote attributes the retained calculation to commit 10f3ea585c6608e794900efe7e4f8f42c0747a3b. This is a check of the saved source and its attribution, not a reproduction of the original map extraction or commit-history reconstruction; source hashes are retained in the review JSON.

S1 confirms all 60 individual sign certificates at the hypothetical relative radius 1e-6, with passing counts 60,60,39,0,0,0 over the listed radii. The 60 carriers are processed views of one sky, and their signs are not all equal. The full-tensor Frobenius norm, exact computational scales and completed-tensor contractions are correctly specified. Source equation (13) is the joint Planck-carrier ball certificate; R32-01 equation (35) is the separate optical determinant bound. The historical 63.1% U-CDF receipt remains unverified. The two inherited family-statistic ranks 0.4581298828125 and 0.45513916015625 are correctly kept separate.

The E-mode carrier is a processed polarization morphology field, not positive bolometric intensity or an absolute thermal temperature. Its nonzero pseudoscalar is a realized parity-odd morphology, not by itself statistical parity violation. The final notes do not apply the temperature-to-intensity fourth-power map to E, or infer radiation stress, matter shear, vorticity or Bianchi geometry from its chirality.

## Executed numerical evidence

The reviewer reexecuted the numerical portion of planck_hubble_controls.py in memory, omitting figure and result-file writes. Its results exactly match the saved receipt:

| Quantity | Reproduced value |
|---|---:|
| Gaussian benchmark seed | 20261026 |
| Draws | 1,048,576 |
| Count at or below U=0.1197448 | 662,397 |
| Ideal-reference empirical CDF | 0.6317110061645508 |
| Binomial Monte Carlo 95% interval | [0.63078695394418, 0.6326343307835368] |
| Empirical upper tail | 0.3682889938354492 |
| Sample mean; exact mean | 0.12916766184475767; 0.1292177098644825 |
| Sample second moment; exact second moment | 0.03894416412868046; 0.03896103896103896 |
| Hubble separate ratios | 0.8000000000000003; 0.8 |
| Hubble joint ratio | 1.1313708498984762 |
| Orthogonal identity absolute residual | 4.963083675318166e-24 |

Independent Dirichlet moment evaluation and axisymmetric attainment of the uncertain-S constant also passed. The finite Hubble control verifies the fixed-S, zero-direct-error case; it does not claim an executed general trust-region fit. The Monte Carlo interval quantifies simulation sampling error under the stipulated ideal law. It is not a processed-Planck p-value, a cosmological confidence interval, or proof that the historical simulation was recovered.

## Final disposition

The application delta passes after the single wording repair. The compact synthesis uses the same formulas and numbers and keeps polarization morphology, intensity stress and optical kinematics as separate physical carriers. No change to the closed radiation-stress result is needed. The new benchmark and joint-budget construction are mathematically supported within their domains. Claims of improved measured constraints or physical attribution still require the stated common-data comparison and calibrated joint observation/processing model.
