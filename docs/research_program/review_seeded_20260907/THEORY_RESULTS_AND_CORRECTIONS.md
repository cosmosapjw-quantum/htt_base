# Review-seeded mathematical results and corrections

Date: 2026-09-07. Owner: MAIN. Scope: HTT observable morphology, response-limited inference and explicitly conditional kinematics.

Status: explicit direct derivations and source-level counterexamples. The scalar numerical evaluations in Section 3 were checked with the web calculator. No new Python, native decoder, symbolic kernel, Monte Carlo, data fit or independent referee execution is claimed. The current Python attempt returned ClientError; the preceding interrupted work also failed to enter the container and Wolfram kernel. Historical accepted calculations retain their existing scope. These results supply the next theory specification; they do not silently amend the accepted PDF or release production analysis.

## 1. The exact axial cutoff is ten, not twelve

Use the axisymmetric continuum weight and identity-transfer operator defined in the 55-page report. Axial boosts preserve m. The retained complex-block row counts for m=0,...,5 are (4,4,4,3,2,1). A source cutoff L provides L-6 columns in each of these blocks.

For L<=9 the m=0 block has at most three columns for four rows, so full real row rank 32 is impossible. The already printed, locally checked nonzero minors use source columns 7,8,9,10 for m=0,1,2; 7,8,9 for m=3; 7,8 for m=4; and 7 for m=5. All are present at L=10. Their nonvanishing therefore gives all six full row ranks, hence real rank 4+2(4+4+3+2+1)=32. The exact minimal axial cutoff is L=10 under precisely that continuum operator.

The old statement of full rank at L=12 remains true but is weaker. Counting columns supplies upper bounds, not the nonvanishing proof. Numerical results for six directions do not establish an all-direction theorem. No finite-HEALPix conclusion follows. The future revised text should sharpen the theorem and retain the original immutable report and certificate as historical source, not rerun a complete certificate campaign solely to change the headline cutoff.

## 2. Conditional projection law: what is actually Beta distributed

Let H3 be real STF3 with its seven-dimensional full Frobenius metric. Fix nonzero STF2 Q, define L_Q O=O:Q and B_Q b=3 STF(b tensor Q). The retained algebra is

L_Q*=B_Q/3; L_Q B_Q=M_Q; M_Q=(Q:Q)I+(6/5)Q^2; B_Q*B_Q=3M_Q.

P_Q=B_Q M_Q^{-1} L_Q is an orthogonal rank-three projector. If, conditional on Q, the coefficient vector of O is a centred seven-dimensional spherical Gaussian with covariance s_O^2 I, choose an orthonormal basis diagonalising P_Q. The squared parallel and perpendicular norms, divided by s_O^2, are independent chi-squares with 3 and 4 degrees of freedom. A change of variables from their two gamma densities to their sum and ratio gives

f_B=||P_Q O||_F^2/||O||_F^2 ~ Beta(3/2,2),
p(f)=(15/4) sqrt(f)(1-f),
F(f)=(5/2) f^(3/2)-(3/2) f^(5/2), 0<=f<=1.

The same ratio law holds after conditioning the Gaussian on any positive radius, or for an explicitly spherical seven-dimensional direction distribution. It does NOT follow from SO(3) statistical isotropy alone: SO(3) is not transitive on the six-sphere of unit STF3 tensors. A non-Gaussian isotropic ensemble may have a nonuniform distribution over octupole shapes. Correlation between Q and O, masking, reconstruction selection and anisotropic noise can also invalidate this particular conditional law.

The mean is 3/7. Calculator evaluations give P(f_B>1/2)=0.3812815664617709 and P(f_B>0.8)=0.06979572136008738. The review's approximate 0.38 and 0.07 are consistent with this law and are NOT errors. Treat f_B as a geometric projection fraction, not the fraction of the observed octupole proved to arise from a physical boost. The law is an analytic null-control fixture; it is not the null law of an arbitrary processed map.

## 3. Correct conditional boost-coordinate variance and the limit of the inference

Consider only the fixed-known-Q linear experiment O_obs=B_Q beta+O_int. With centred spherical Gaussian O_int of covariance s_O^2 I_7,

beta_hat=M_Q^{-1} L_Q O_obs,
Cov(beta_hat-beta | Q)=(s_O^2/3) M_Q^{-1}.

This follows by inserting L_Q L_Q*=M_Q/3. If instead O_int is conditioned to have fixed norm A_O and uniform direction, its coefficient covariance is A_O^2 I_7/7 and

Cov(beta_hat-beta | Q,A_O)=(A_O^2/21) M_Q^{-1}.

A fixed-radius sphere and a Gaussian are different experiments. The formulas coincide after identifying the Gaussian mean squared radius 7s_O^2 with A_O^2, but higher distributions need not coincide. No Cramer-Rao assertion for a fixed-radius singular-support model is being imported from the Gaussian model.

Put Q=A_Q q, q:q=1, s3=tr(q^3), M_q=I+(6/5)q^2. The already derived polynomial inverse gives

M_q^{-1}=[40I+(15/2)s3 q-30q^2]/[40+3s3^2],
tr(M_q^{-1})=90/[40+3s3^2].

To bound s3, extremise the product of the three trace-free eigenvalues at fixed sum of squares. Lagrange multipliers imply that an extremum has at most two distinct eigenvalues; spectra proportional to (-1,-1,2) saturate |s3|=1/sqrt(6). Thus

20/9 <= tr(M_q^{-1}) <= 9/4,

sqrt(20/189) (A_O/A_Q) <= rms(beta_hat-beta) <= sqrt(3/28) (A_O/A_Q).

The lower endpoint is axisymmetric; the upper endpoint is a zero eigenvalue with the other two opposite. This small range does not remove the amplitude factor.

For the review's illustrative inputs D2=226 microkelvin^2, D3=1018 microkelvin^2, use C_l=2pi D_l/[l(l+1)], not C_l=D_l. Then

A_Q=sqrt(75 D2/24)=26.575364531836623 microkelvin,
A_O=sqrt(245 D3/48)=72.08357418071517 microkelvin,
rms in [0.8823505847188882, 0.8878481493381545].

These are calculator-checked substitutions, not a new map-derived measurement. Under the proposal's stated formula and normalisations, the quoted rms 0.8435 is not in the allowed range. Its numerical example should be corrected.

This demonstrates very poor precision for this particular one-sky, fixed-Q intrinsic-octupole mean-channel estimator. It is not a universal theorem that every low-multipole velocity estimator is useless, not a statement that there is literally no boost signal, and not a proof concerning an arbitrary joint likelihood. The observation model here omits boost dependence of Q, other harmonic couplings, parameter-dependent covariance, auxiliary measurements and physical correlations. A full Gaussian model has Fisher information

F_ij = mu_,i^T C^{-1} mu_,j + (1/2) tr(C^{-1} C_,i C^{-1} C_,j).

The second term may not be discarded when boost changes the covariance. A 32-by-48 source-coordinate response is not the same Jacobian as a 32-by-3 velocity response. The published low-multipole primordial-dipole limitation and high-multipole aberration measurements must be compared in their own experiments, not merged into an estimator-independent numerical bound.

## 4. Cancel the background terms before applying a shear norm

Within the specific first-order geodesic collisionless brightness model in Appendix E, let pi_ab=(8/15)rho vartheta_ab, q_a=(4/3)rho vartheta_a, xi_abc=(8/35)rho vartheta_abc and dot(rho)=-(4/3)Theta rho in first-order products. Substitute these into the quadrupole moment equation before applying norms. The expansion terms in dot(pi)+(4/3)Theta pi cancel exactly, leaving

sigma_ab=-dot(vartheta_<ab>)-D_<a vartheta_b>-(3/7)D^c vartheta_abc.

STF projection cannot increase Frobenius norm, and contraction of the gradient over three spatial directions gives the safe bound sqrt(3). Therefore

||sigma||/Theta <= epsilon2_star + epsilon1_prime + (3sqrt(3)/7)epsilon3_prime.

Under the report's explicit derivative-envelope estimates this is at most

epsilon2/3 + epsilon1/3 + (sqrt(3)/7)epsilon3.

The original triangle-before-cancellation inequality was a valid but much looser sufficient bound in this model. Keep the conventional literature MES application and this cancellation-preserving model-specific estimate as different named branches with their own premises. Do not advertise the latter as a general nonlinear improvement of the original almost-EGS theorem. All-observer extension, congruence, rate convention, perturbative order and the exact contracted derivative operators remain required.

A local amplitude bound cannot generate a derivative bound: f_k(x)=epsilon sin(kx) has uniform amplitude epsilon and derivative amplitude k epsilon. This elementary family explains why a table of accurate local C_l values alone cannot give a model-independent spacetime shear/vorticity ceiling. Redshift-dependent galaxy or integrated ISW information is not automatically a measurement of the local radiation-multipole derivative in this equation; a response relating them must first be derived.

## 5. Deterministic rank margins may be reported after computation

Suppose actual numerical containment has been proved: Delta Delta^T <= Gamma, Gamma positive definite, and W=Gamma^{-1/2}. If Kobs=Ktrue+Delta then ||WDelta||_2<=1, so s_min(WKtrue)>=s_min(WKobs)-1.

If a rigorous lower enclosure a for s_min(WKobs) obeys a>1, then choosing and reporting delta=(a-1)/2 AFTER inspecting a gives a valid deterministic margin. No probability argument requires advance registration of this descriptive margin. The previous teaching text's blanket restriction on post-inspection delta is too strong and should be corrected in a new version/erratum.

What does require justification is containment itself, and any statistical coverage or selection rule claimed for a data-dependent Gamma. A floating estimate above one without a rounding enclosure is also not an exact deterministic certificate. Separate deterministic numerical margins from preregistered inferential thresholds. Cross-code convergence is useful evidence, not by itself a proof that every error is in the proposed envelope.

## 6. Rank-zero nuisance quotient does not mean zero statistical information

For y=A theta+K h+n in fixed metric, distinguish four declared models.

1. Unrestricted deterministic h: only the quotient of Im(A) by Im(K) is identifiable. Full row rank K removes this quotient.
2. Bounded h^T S^{-1}h<=r^2 with S positive definite: for d in Im(K), the minimum squared cost is d^T(KSK^T)^+d. With full row rank, replace the pseudoinverse by the inverse. Proof: set h=S^(1/2)g and solve the minimum Euclidean norm constrained problem by SVD. Components outside Im(K) remain impossible, not zero cost.
3. Independent centred Gaussian h with covariance S and noise covariance N: C=N+KSK^T, so linear mean information is A^T C^{-1}A. This is prior-conditioned information, not the deterministic quotient.
4. Auxiliary data from the same sky: let y=A_y theta+Kh+n_y and z=A_z theta+Hh+n_z, with joint noise covariance N. Then

Cyy=Nyy+KSK^T,
Cyz=Nyz+KSH^T,
Czz=Nzz+HSH^T,
C_y|z=Cyy-Cyz Czz^{-1}Czy,
mu_y|z=A_y theta+Cyz Czz^{-1}(z-A_z theta).

The conditional mean Jacobian is A_y-Cyz Czz^{-1}A_z only if the covariance blocks are parameter independent; otherwise differentiate the complete expression. Joint inference is p(z|theta)p(y|z,theta), not p(z|theta)p(y|theta). Gaussian conditioning follows by completing the quadratic form (or block elimination). Use linear solves, not explicit inverse evaluation, computationally. Positivity of the joint covariance and a matched definition of all rows are required.

If beta changes K, H or their covariance, use the full Fisher expression in Section 3. Do not call tr(KSK^T)/tr(N+KSK^T) an information-loss fraction or a universal detection bound. A trace ratio ignores the alignment of signal and nuisance eigenspaces.

For a fixed finite harmonic model and w_epsilon=1-epsilon m with bounded m, N_epsilon=I-epsilon G. Full-sky nearest-neighbour selection makes the high-source-to-retained boost overlap vanish at epsilon=0. If the normal inverse remains bounded, K_epsilon=epsilon K1+O(epsilon^2). Gaussian nuisance covariance is consequently O(epsilon^2), while a compensating nuisance of fixed-output magnitude costs O(epsilon^-2) when the relevant K1 has full row rank. Nonzero rank for every epsilon>0 can therefore coexist with arbitrarily weak practical contamination. This result is for a specified path of masks, not a theorem that f_sky alone controls leakage.

For the first-order operator with fitted l<=5 and source l<=L, products with boosted modes have mask harmonic support at most L+6 by the Gaunt triangle rule. This is an exact finite-band reduction of the continuum formula, not permission to drop map tails without a bound. Computing those mask harmonics and solving a conditioned normal matrix still carry error.

## 7. The monopole must be retained to adequate boost order

For thermodynamic temperature in the stated outward-sky convention,

T_beta(n)=T0/[gamma(1-beta dot n)] for a pure monopole.

Expanding yields T0[1+beta dot n+(beta dot n)^2-beta^2/2]+O(beta^3 T0), with quadrupole

Q_kin=T0 STF(beta tensor beta), ||Q_kin||_F=sqrt(2/3)T0 beta^2.

At the review's illustrative T0=2.7255 K and beta=0.001234 this norm is 3.3886824717088606 microkelvin. This is a scale calculation, not a new empirical determination. Retaining beta times the small anisotropy while dropping beta^2 times the large monopole is not justified merely by beta<<1. The science specification will use the exact blackbody monopole transformation and a consistently controlled anisotropy transformation. Maps already corrected for a kinematic quadrupole require their documented preprocessing, not a second subtraction.

Frequency-channel intensity maps and linearly converted temperature maps are not automatically exact thermodynamic d=1 fields. The full transfer includes the product's unit conversion and component-separation convention; the comparison with Chluba–Ravenni and Ferreira–Quartin is an explicit remaining forward-model task.

## 8. Redshift information has its own null directions

In a local, low-z Euclidean expansion write the velocity field u(x)=u0+A x and a radial observation n dot u(rn). The antisymmetric part Omega=(A-A^T)/2 gives n^T Omega n=0. Radial data at this order therefore constrain u0 and the symmetric velocity gradient, not the local rotational component. This is an exact algebraic null statement within the local approximation, not a theorem that all light-cone observations are forever insensitive to vorticity.

A spatial velocity gradient fitted to a reconstructed galaxy field is not automatically the shear of a specified cosmological congruence. Grouping, distance likelihood, calibration, selection, reconstruction priors and light-cone corrections need explicit treatment. A redshift trend in a phenomenological dipole is not by itself global cosmological tilt.

At linear frame order beta_RO=beta_RM+beta_MO. A dipole temperature contains an intrinsic component as well as T0 beta_RO; that one vector cannot identify all three physical frame velocities. Independent aberration/modulation information and a calibrated matter-frame measurement can supply complementary constraints, under their stated models. Shared structures and calibrators require joint covariance. High-multipole boost evidence is useful but is not automatically free of primordial-potential degeneracies; compare the primary references below.

## 9. Concrete code-research result: a masked DESI moment is not a deconvolved dipole

At default source 50ea6d76ace70dec57b8794ab0d1cf9b8fab42cb, scripts/desi_dipole_measure.py computes Dhat=3<delta n>_R and describes a window-corrected dipole. The catalogue normalization alpha is fitted from the same selected sample. For a true weak dipole density 1+d dot n and weighted mask means, to first order

delta(n)=d dot (n-<n>_R),
E[Dhat]=3[<nn^T>_R-<n>_R<n>_R^T]d.

The response is identity only for the appropriate full-sky moments, not for an arbitrary footprint. A uniform northern hemisphere has <n>=(0,0,1/2), <nn^T>=I/3, hence the response diag(1,1,1/4). Its axial dipole is suppressed by four even in this noiseless elementary control. Dividing data counts by random counts removes the mean selection pattern; it does not automatically invert all angular-mode mixing. Multiple independently normalised caps need their own normalization columns.

The same pinned source compares its direction to hp.ang2vec of Galactic (l,b) and labels the output Galactic, while dl_pipeline/scripts/extract_desi_compact.py builds n_hat directly from RA/Dec, and the random loader does the same. No equatorial-to-Galactic rotation appears on this path. This is a source-level coordinate mismatch, not an observed numerical estimate of the induced angular error. The exact affected source blobs are recorded in REUSE_AND_DATA_MAP.md.

Future reuse retains the ingestion/random-count primitives, not those amplitude/direction claims. Supply an explicit coordinate transform and a joint angular design including per-cap normalization and retained nuisance multipoles, with its covariance/rank checks. Tests must inject a known equatorial vector, recover it under joint data/template rotation, and reproduce the hemisphere response above; a zero dipole must have undefined direction rather than NaNs being reported as a physical axis. Existing immutable cards remain historical. No source patch or native run was made in this review.

## 10. Primary literature checked for this plan

The following are external primary sources, not evidence that their data are present locally. Web abstract/metadata/source pages were checked on 2026-09-07; the entire contents of every linked paper were not rederived.

- Land & Magueijo, The Multipole Vectors of WMAP, and their frames and invariants: https://arxiv.org/abs/astro-ph/0502574 . The mock review's attribution of this identifier to Katz & Weeks is incorrect.
- Katz & Weeks, Polynomial Interpretation of Multipole Vectors: https://arxiv.org/abs/astro-ph/0405631 . Multipole vectors also retain complete multipole information when scale, sign conventions and relative frames are retained; no uniqueness claim for the HTT approach is inferred.
- Chluba & Ravenni, The boost operator: properties, computation, and applications, MNRAS 548 (2026) stag698, DOI 10.1093/mnras/stag698; https://arxiv.org/abs/2505.02080 . This must be compared before claiming a novel low-multipole primordial-dipole result.
- Planck Collaboration, Doppler boosting of the CMB: Eppur si muove, https://arxiv.org/abs/1303.5087 . High-multipole aberration/modulation is a different observed response from the Q-to-O mean channel.
- Roldan, Notari & Quartin, https://arxiv.org/abs/1603.02664 ; Ferreira & Quartin, https://arxiv.org/abs/2107.10846 . Both require care in separating boost, intrinsic dipole, potential effects and temperature conversion.
- Planck NPIPE, https://arxiv.org/abs/2007.04997 . It describes 600 complete signal/noise/systematics simulations, not a promise that an arbitrary local PR4 directory includes them.
- Tully et al., Cosmicflows-4, https://arxiv.org/abs/2209.11238 . Distances/grouping are the data; derived peculiar-velocity grids inherit reconstruction assumptions.
- DESI DR1 product definitions: https://data.desi.lbl.gov/doc/releases/dr1/ . Clustering catalogues, randoms, mock catalogues and compressed cosmology products are distinct.
- Saadeh et al., https://arxiv.org/abs/1605.07178 . Its Bianchi-model posterior limits and MES conditional inequalities do not have interchangeable assumption sets or meanings.

Novelty remains to be assessed at the concrete combined-response result level. None of the scalar calculator checks is represented as a new map analysis, code execution or independent proof of the full programme.