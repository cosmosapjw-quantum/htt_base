# Host transcription of the additional theory contribution

Actual native adviser: /root/r25_statistics_theory, requested Astra/xhigh,
observed UNKNOWN. Read-only contribution, no scientific rerun or file writes by
the adviser. This is source material for separate independent review, not an
admission verdict. Pair input examined: 3e1714e9dabd04613e89021af295a9e6478597edacd2a9047d293191b3f2c1f6;
PR3 draft: 4bd8d1236f0554ce47d91f43b03cf4d68cb946c20b74b030b518d41ea5b703a0.

## Calibration geometry

Let h_u have constant first coordinate 1, t=mean_U h_u, H=[h_i] for observed
O. Hp=t,p>=0 is feasible iff t is in the convex hull of observed columns.
All p_i>0 is possible iff t is in its relative interior. For the converse,
let hbar be the uniform observed mean, extend t slightly along t-hbar within
the hull, and mix the resulting t' with hbar to obtain positive weights on
every point. Infeasibility iff a separator lambda satisfies H^T lambda>=0
and t^T lambda<0. A witness contradicts feasibility immediately. Conversely,
project t onto the hull at c; a=c-t has a^T h_i>=a^T c and
a^T t=a^T c-||a||². Subtract a^T c using the constant coordinate.

For cell masses m_c and positive observed counts n_c, minimum sum p_i²
weights are p_i=m_c/n_c, by cellwise Cauchy-Schwarz. ESS=1/sum p_i² is weight
concentration, not an independent-observation count.

For a full tensor T_u=B h_u+e_u in any finite tensor space, exact balance gives
mean_U T_u - sum_O p_i T_i = mean_U e_u - sum_O p_i e_i.
Only an additional remainder/transport assumption controls the right side.
Apply the same p to the joint twelve scalar/vector/STF carriers:
mu_p=sum p_i delta_(T_i^1,...,T_i^12). Positive weights preserve atomic support
and its convex hull but change occupancy; weighting commutes with simultaneous
rotations. Two target objects with h=1, observed T=0 and missing T=M show
that exact auxiliary balance leaves target mean M/2 unrestricted.

Current finite separators: unsupported cell gap -1/628; fine supported-frame
velocity functional zero on observations but target mean 2547/625 km/s.
The latter rules out even signed balance. Missing outcomes remain unidentified.
Primary methodological context:
https://www150.statcan.gc.ca/n1/pub/12-001-x/2005001/article/8091-eng.pdf
section2 equations3–7; sampling assumptions are additional to finite geometry.

## Pair derivative and covariance

N,V have rows n_i^T,v_i^T with unit n_i and tangent v_i. K=VN^T+NV^T and
d cos(theta_ij)/dt=a_mu K_ij, a_mu=pi/(180*3600*10^6) for the declared
microarcsecond-equivalent coordinate. The numerator exists at coincident and
antipodal directions; theta rate requires singular division by -sin(theta).

If rank N=3, K=0 iff one common rotation v_i=omega cross n_i. With
P=N(N^T N)^-1 N^T, 0=(I-P)KN=(I-P)V(N^T N), so V=NA; substitution implies
A+A^T=0. Conversely rotation cancels by the scalar triple product. Tangency
sets the diagonal to zero, so all unordered off-diagonal pairs suffice.
The rank assumption matters: planar directions permit additional normal motions.

For pair row L_ij and 13-column design X, a_ij=L_ij X,
H_b=mean a_ij^T L_ij, d_b=H_b y, D_b=H_b X. Thus E[d]=D beta, HB=0
for the common-spin design B. d is a response, not beta.
Cov(d)=H Sigma H^T for every joint source law. Under the separate block-
diagonal working C0, Cd=sum_i H_i C_i H_i^T. Shared-source pair covariance
Cov(kappa_ij,kappa_ik)=(n_j^T E_i) C_i (E_i^T n_k) is generally nonzero.
H has at most117 rows on9512 source coordinates, so dim ker H>=9395:
the rotation-only theorem does not apply after this compression.

With C0 positive definite, range(H C0 H^T)=range H, from the quadratic-form
identity ||C0^(1/2) H^T u||². Hence exact d,D lie in that support; numerical
discarding does not turn a positive/ambiguous mode into an exact null.
Under a fixed Gaussian working model and EXACT W Cd W^T=I_r, z=Wd,
M=WD and the projector P_M onto its COMPLETE image give
||(I-P_M)z||² ~ chi²_(r-rank M). For nested E1/full images the difference
z^T(P_full-P_E1)z is central chi²_(q_full-q_E1) only under the E1 mean null.
Proof: residual means vanish and the relevant projector gives independent
standard-normal coordinates on its image.

If instead a CERTIFIED bound ||W Cd W^T-I||_2<=delta<1 is known, with exact
null image/projector, the residual covariance eigenvalues are <=1+delta.
Coupling sum lambda_j Z_j² with (1+delta) sum Z_j² yields the conservative
upper tail chi²_nu(T/(1+delta)). Apply dimension r to the projected-mean ball
and nu_Delta to the nested difference under E1. Statistic/tail evaluation
also needs conservative numerical treatment. A computed residual <=1e-9 is
only a numerical check, not certification. Without a complete model image,
retain TAIL_UNRESOLVED; unrestricted coefficients can amplify discarded modes.

Required pre-execution pair contract correction: describe ordinary tails and
the95% projected-mean region as NUMERICAL_WORKING_CHI_SQUARE_APPROXIMATION
unless exact whitening is established; certified delta permits the conservative
(1+delta) correction. No new certification algorithm is required; approximate
descriptive references remain executable. Preserve all unprojected/discarded
modes. Sources:
https://arxiv.org/html/2204.12574v2#A5 (within-source covariance only);
https://arxiv.org/html/1808.07103v1#S3 (shared objects);
https://arxiv.org/pdf/1310.0500 (angular construction);
https://academic.oup.com/biomet/article-abstract/57/3/567/253370 (quadratic forms).

## Conditional evidence

For training sigma-field T_j, normalized training-measurable density q_j and
D_j >= sup_(theta in H0) p_theta,j(.|T_j), E_j=q_j(Y_j|T_j)/D_j obeys
E_theta[E_j|T_j]<=integral q_j=1. Set ratio0 when D=infinity and specify
null-measure-zero zero-denominator cases. Fixed convex fold averages remain
e-valid by linearity regardless of dependence. Union nulls require max_s
sup_theta p_s, not an average of denominators. Products or selected maxima
of dependent e-values need not have expectation<=1.

For Gaussian shape V_s, A_s=V_JT V_TT^-1,
S_s=V_JJ-V_JT V_TT^-1 V_TJ, r_s=y_J-A_s y_T,
Z_s=X_A,J-A_s X_A,T. Let R_s=min_beta (r_s-Z_s beta)^T S_s^-1
(r_s-Z_s beta). For S_s>0,R_s>0,m=|J|,
sigmahat²=R_s/m and
log sup p_s = -.5[m{log(2pi)+1+log(R_s/m)}+logdet S_s].
R_s=0 gives infinite unrestricted-scale supremum and E=0. Singular S requires
a separately specified measure/support, not a silent pseudodensity.

Training-fit uncertainty is NOT required for the conditional argument:
any training-measurable normalized q suffices, while accuracy affects power.
Remove that item from reasons for invalidity in the current candidate report
through its actual review/repair path. Real limitations remain the unqualified
selected/adaptive experiment and lack of an outward-certified null-density bound.
All20 stored null fits have rank10 across listed thresholds; no actual truncated
null direction was found. Choosing a point-mass q after seeing a fair Bernoulli
test outcome gives E=2 always despite each q being normalized.
Primary source: https://arxiv.org/html/1912.11436 sections5–6. This is an
application of standard universal inference, not a novelty claim.

## E-to-B perturbation certificate

Computed A_E,A_B are12x2; y_E,y_B have12 coordinates. Suppose exact delivered
quantities differ by certified operator/vector bounds eps_AE,eps_AB,eps_yE,
eps_yB. Let s<=sigma_min(A_E), s>eps_AE>=0,
R_E>=||y_E-A_E ctilde||, U_B>=||A_B||, with certified upper evaluations.
If one c* satisfies A_E* c*=y_E* and A_B* c*=y_B*, then
C=(upper||y_E||+eps_yE)/(s-eps_AE) bounds ||c*||,
Delta_c=(eps_yE+eps_AE C+R_E)/s bounds ||c*-ctilde||, and
||y_B-A_B ctilde|| <= tau0=eps_yB+eps_AB C+U_B Delta_c.
Proof: ||A_E* c||>=(s-eps_AE)||c||;
A_E(c*-ctilde)=(y_E*-y_E)+(A_E-A_E*)c*+(y_E-A_E ctilde);
y_B-A_B ctilde=(y_B-y_B*)+(A_B*-A_B)c*+A_B(c*-ctilde).
Apply triangle inequalities. No error-independence assumption is needed.
With residual-evaluation error eps_eval, observed residual>tau0+eps_eval
refutes the exact relation under the bounds. The draft additionally uses a
certified lower residual against this threshold, conservative but redundant.
Failure to exceed is not evidence of equality. Missing bounds or
s<=eps_AE leave this certificate unresolved.

Example A_E=a[u,u+eta v], A_B=a[p,q], orthonormal pairs,
a=1e-5,eta=1e-7: a5e-13 v E-target perturbation changes coefficients
(0,1) to(-.5,1.5), causing B discrepancy a/sqrt2=7.07e-6 K_CMB despite
singular-value ratio>1e-8. Agreement/conditioning screens are not error bounds.
Primary context https://link.springer.com/article/10.1007/BF01933494;
the elementary proof above is not attributed to an unchecked paper equation.

## Full tensor interpretation

Keep all joint scalar/vector/STF carriers, source IDs, operators, covariance,
rank and polar/axial conventions. A scalar phi(Z) is an image of this joint
state. A valid joint region C gives simultaneous images phi(C); it cannot create
coverage absent from C. F distinguishes set/support from occupancy under a named
measure; an ellipsoid is not a distribution on its interior. Q requires its
matching declared anchor/gauge; physical MES anchors remain unavailable.
Pi_mu(phi,t)=mu{q_phi>t} distinguishes weighted empirical, Gaussian working and
physical selected-source laws. An e-ratio is neither Pi nor posterior probability.
G_F requires actual supported depth; angle bins, frequency indices and folds are
not depth. Original17/42, alternate18/42, old allocations/one-use and R9 UNKNOWN
are unchanged.
