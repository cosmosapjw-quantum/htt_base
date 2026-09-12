# R9: response, nuisance and conditional physical inference

> **Current revision 2**: report-seeded upgrade from `5e4e899c` on the `d514eabd` catalog base. Read [model-to-data design](revision2/MODEL_TO_DATA.md), [new derivations](revision2/THEORY_EXTENSION.md), and [revision review](revision2/REVIEW.md) first. The 30-node DAG preserves R9-00…23 and adds R9-24…29. Original R9 evidence below remains historical. This revision ran reference experiments, not production or observations; exact GPT-6 archive activation is blocked in this session.

Evidence class: explicit conditional derivations and the bounded checks referenced below. These are research results for implementation design, not formal four-axis admission or an empirical detection. Standard linear-model, set-inversion and union-bound ingredients are not claimed as new mathematics. The project contribution being tested is their source-bound composition and its physical discriminators.

## T1. Depth distinguishes response ratios, not sample counts

Source: `htt/htt/htt/infer/r7_depth_response.py` at R8 baseline, fixed **observed** redshift, outward directions, velocities in v/c, flat FLRW, positive H, first order in velocities. Its source coefficient K is the declared coherent source-velocity parameter; identifying it with global matter congruence tilt needs a separate physical response.

Let I(z)=integral_0^z du/H(u), f_o=(1+z)/(H(z)I(z)), and f_s=(1+z)(1-f_o). For C^1 positive H and z>0,

\[
R(z)=f_s/f_o=H(z)I(z)-(1+z),\qquad R'(z)=H'(z)I(z).
\]

This follows by the fundamental theorem of calculus, I'=1/H. Therefore H'=0 throughout a depth interval makes R constant there; globally constant H gives R=-1 and the entire first-order response measures beta_observer-K only. If H' has a definite nonzero sign on an interval, R is strictly monotone there. Two distinct redshifts in that interval give two independent radial kernels. This is sufficient only when angular support and nuisance projection also preserve the relevant directions.

For one fixed angular component, independent Gaussian errors of weights w_i>0 give an unprojected two-parameter information matrix F. Cauchy–Binet gives

\[
\det F=\sum_{i<j}w_iw_j f_{o,i}^2 f_{o,j}^2(R_j-R_i)^2.
\]

The common factor (5/ln10)^4 enters if the magnitude response is used. With H(z)=H0(1+a z+O(z^2)), R=-1+(a/2)z^2+O(z^3). Thus low-redshift shape separation starts quadratically even though each Doppler kernel grows as 1/z. More rows at the same response ratio improve precision on the measured combination without identifying its decomposition. For three-vector parameters, inspect the full direction-and-depth matrix after *shared* nuisance handling; radial variation alone does not prove six-column rank. The quoted expansion of R is not an error bound for the physical first-order velocity approximation. The r7 code's quadrature error does not bound omitted velocity, selection or calibration terms.

## T2. Project nuisance once, retain identifiable targets

Assume a fixed selected experiment z=A theta+N eta+b+epsilon with epsilon~N(0,I_n), fixed A,N, eta unrestricted, and true discrepancy b in a declared set B. Known covariance whitening must be performed on a justified joint Gaussian law; marginal Gaussianity plus covariance does not establish this law. Let U have orthonormal columns spanning col(N)^perp. Write y=U^T z, D=U^T A, B'=U^T B, r=rank(D), and P=D D^+.

With c_r=sqrt(chi2_{r,1-alpha}), define

\[
C_\alpha(y)=\{\theta:\exists b'\in B',\ \|P(y-D\theta-b')\|\le c_r\}.
\]

At the truth, the particular b'_0 is feasible and the squared residual is ||P U^T epsilon||^2~chi2_r. Hence P(theta0 in C)>=1-alpha. This is coverage of the fixed true theta (and of any projected true target), not simultaneous coverage of every observationally equivalent parameter. Use r=0 as an explicitly information-free parameter branch: C is the whole parameter domain if B' is nonempty; a chi-square quantile routine is not called at zero degrees of freedom.

For unrestricted theta, compact B', and a linear target ell theta, finiteness holds exactly when ell annihilates ker(D). Put t=ell D^+. The support is

\[
\sup_{\theta\in C}\ell\theta=t y+h_{B'}(-t)+c_r\|t\|.
\]

Proof: D theta spans col(D); along that space write Dtheta=P(y-b')+e with ||e||<=c_r. The target is t(y-b')+t e and maximization gives the stated support. If ell does not annihilate the kernel, arbitrary kernel translations leave the observation unchanged but move the target without bound. Physical constraints can make a target finite despite matrix rank deficiency; then solve on the declared constrained fibre instead of using the unconstrained criterion as a no-go theorem.

For B'={G^(1/2)u:||u||<=sqrt(2 Dbar)}, the discrepancy term is sqrt(2 Dbar * t G t^T), retaining orientation. Replacing it by sqrt(2 Dbar lambda_max(G))*||t|| is valid but potentially much looser. The prior Teff report supplies a possible route to G only if the actual matched moments, observable kernel, measure, weight envelope and entropy bound satisfy that report's premises. No such HTT consumer is currently admitted; this formula works equally for other independently bounded response errors.

The component (I-P)y is a **separate lack-of-fit observable**. Discarding it during parameter inference loses evidence about response misspecification. If used for acceptance, keep the same b' across the response and residual constraints and allocate error probabilities explicitly (or use a justified joint test). Separate minimizers for separate constraints generally describe a larger, less informative set. Data-dependent A,N,B', estimated covariance or post-selection needs its own law; this pivot cannot be reused silently.

## T3. Join product sets before projecting common calibration

For product j let C_j(Y_j) be a confidence set on the SAME tuple x=(theta,eta_shared,eta_j), with P(x0 notin C_j)<=alpha_j under its admitted marginal experiment. Cross-product independence is unnecessary:

\[
\Pr\{x_0\in\cap_j C_j\}\ge1-\sum_j\alpha_j.
\]

Missing blocks contribute the entire declared domain and retain their unused alpha. The physical parameter set is projection_theta(intersection_j C_j), followed by the permitted physical response image. Alternative plausible laws give a union of their sets; compatible constraints give intersections. A prior/covariance scenario and an exact selected sampling law retain distinct labels.

In general projection(intersection) is a strict subset of intersection(projections). Example: mu1=theta+eta, mu2=theta+2eta. Each product alone with free eta leaves every theta possible, but joined exact means give theta=2mu1-mu2. Gaussian marginal confidence intervals with Bonferroni levels produce a finite conservative interval for theta under arbitrary dependence. The inference gain comes from a shared response/calibration relation, not an assumed increase in independent sample size.

Same-host differences eliminate a common distance signal. They can still inform a calibration nuisance that also appears in another product, if that equality of calibration parameters is scientifically justified. They cannot directly identify a distance dipole whose column is annihilated by the contrast. A response identity or shared anchor selected only to make the data agree is not a qualification.

Certified emptiness of the shared feasible set rejects that *joint model and its admitted premises* at the allocated level. It does not select a unique replacement cause. Numerical failure or lack of a witness is not certified emptiness. A local optimizer's feasible point proves nonemptiness, whereas a rigorous outer bound or dual infeasibility certificate is required to exclude states. Unresolved cells are retained.

## T4. Conditional MES and signed departure

Let a confidence set for the required observed radiation jet and all shared nuisance/closure variables be J(Y). If the physical equations and remainder assumptions define a relation F between that tuple and physical state p, its outer image contains the true p whenever J contains the true tuple and the relation holds. A finite fixture image is no evidence for an observed jet law. Missing derivatives may leave the image unbounded even when low multipoles are accurately known.

For Theta=3H, initial Hamiltonian S_H=(sigma:sigma)/(6H^2) equals 3*s2, where R8 s2=(sigma:sigma)/(2Theta^2). This normalization is a prerequisite for using the initial report's conditional formula

\[
x_C=(S_H+K_C+r\Omega_F)/(1+r),\quad r=(1+w)\sinh^2\zeta.
\]

Its sign-clean bounds require their stated nonnegative terms; x_C is a signed comparison coordinate. The zeta in this constrained state is not the fitted local observer beta. A same-state response and frame relation must connect them. No new physical departure interval is issued in this run.
