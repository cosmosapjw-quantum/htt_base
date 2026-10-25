# R32-06-P4-DESIGN: frozen scientific build contract

External preparation for campaign R23-whole-42-solver-free. This file is a scientific specification and proof draft, not a formal execute packet, production product, independent decision, or task-state mutation. Requested author route Astra/xhigh; observed runtime UNKNOWN. Source hashes are in P4_SOURCE_IDENTITIES.json. Repository is read-only during this preparation. The controller's later formal execute packet owns actual output paths and limits.

## Scope and source obligations

Build an English response-design note, deterministic numerical tables/figures, a runnable consumer, RESULT.json and a claim-to-source map under the existing R32-06 path only after formal dispatch. Reuse the retained rank theorem; do not rerun historical CAS or adjacent producers. The exact new object below is a **conditional finite response design**. Additional channels are hypothetical measurement functionals; no actual survey, external transfer, native transfer, physical covariance, null or history provider is supplied. Original V03 and all original42 acceptances are unchanged.

Sources actually read: mathematical_recovery.md section "Two radii separate angular nuisance and depth response"; independent_review.md section on the rational rank design; NATIVE_INFERENCE_THEOREMS.md section 6; theory_synthesis_20260913/REPORT.md section 13 and 13.1; physical_derivations.md P1/P5/P11; theorem_physical_chapter.md nuisance quotient/anchor coordinate discussion. The last two give physical interpretation, not empirical qualification of the design chosen here. The cached source identities and supplied excerpts suffice; no new external fact or literature claim is needed. Cite source filenames and locators in research notes. Do not label this conditional construction novel without a separate prior-art assessment.

## Fixed frame, units, observation and parameters

Signature (-,+,+,+). Work in one declared nonrotating orthonormal spatial frame of an expanding fiducial normal observer, with positions r*n, n unit, c=299792.458 km/s. This local response is a first-order stipulated design, not a covariant finite-redshift transfer. Fix R*=100 Mpc, v*=300 km/s, beta*=v*/c, h*=v*/R*=3 km/s/Mpc. Dimensionless data are y=(c/v*) delta_z. Fix r1=R*, r2=q R*, nominal q=2. All additional data below are expressed in the same dimensionless y-equivalent units by their explicitly declared gain; numerical row-error scales belong to this design metric only.

Let theta=(ell[3], b[3], m[1], g0[3], s[5], g1[3]) in that order, total 18. Observer velocity is v*ell; coherent source bulk is v*b. The observer sign is negative because a positive observer velocity toward n reduces radial redshift at first order. The scalar rate is h_* m. STF rate tensor is h_* S, with h_*=v*/R* and S=sum s_a F_a. The **hypothesized** matter-tilt history is beta_G(tau)=beta*[g0+(2*tau-1)g1], 0<=tau<=1, resolved along the same frame. Its chosen linear response is rho*n dot integral W(tau) beta_G/beta* d tau, rho=r/R*. This is an explicit sensitivity design, not a derived universal tilt/rate relation. The label g0 does not identify acceleration, expansion or geometric shear. The separately specified response coefficient rho may be changed only under a new scientific contract.

Use an orthonormal STF basis in full Frobenius norm:
F1=diag(1,-1,0)/sqrt(2), F2=diag(1,1,-2)/sqrt(6),
F3=(ex ey^T+ey ex^T)/sqrt(2), F4=(ex ez^T+ez ex^T)/sqrt(2), F5=(ey ez^T+ez ey^T)/sqrt(2).
Thus ||S||_F^2=sum s_a^2. Keep the whole matrix/tensor and all signed vector coordinates in outputs.

For illustration only use coefficient domain [-1,1]^18. This guarantees ||beta_G||<=2 sqrt(3) beta*<1; it is a chosen sensitivity domain, not a prior or cosmological admissible body. Local response linearity remains stipulated. No inference coverage is claimed from this box.

## Rows and nuisance: literal forward equations

Ordered nine directions: ex,-ex,ey,-ey,ez,-ez,(3/5,4/5,0),(3/5,0,4/5),(0,3/5,4/5), all at rho=1. Append ex,-ex,ey,ez at rho=q. Define E3 rows n^T; Q5 rows (n^T F1 n,...,n^T F5 n); E9=[1,E3,Q5]; E4=[1,E3]. Let R=diag(rho_i).

With W0(tau)=1, integral W0=1 and integral W0(2tau-1)=0. The 13 baseline means are
 y_i=alpha+n_i dot(b-ell)+rho_i[m+n_i dot g0+n_i^T S n_i],
where alpha is the sole free additive scalar calibration nuisance. In column order above,
 J0=[-E3,E3,R*1,R*E3,R*Q5,0_(13x3)], N0=1_13.
Here R*1 is matrix R acting on ones, NOT the physical reference radius R*; code should name it radial_monopole to avoid notation ambiguity.

Two hypothetical independently calibrated three-coordinate additions:
 z_L=ell+e_L;
 z_G=integral_0^1 2tau beta_G(tau)/beta* d tau+e_G=g0+g1/3+e_G.
The second is a different normalized history window, W1=2tau, with all components in the same transported frame. It is not a newly observed remote velocity or available Bianchi transfer. Its nuisance coupling is stipulated zero; an actual implementation with unknown calibration would require extra nuisance columns and renewed rank analysis. Appended design rows are respectively [I3,0,...,0] and [0,0,0,I3,0,I3/3]. Appended nuisance entries are zero: N=[1_13,0_6]^T. Derive the common quotient ONCE from this N and apply it to every column and the data; do not separately quotient endpoint and history responses.

Default row metric W=I19. Sensitivity cases W=diag(I13,sigma_L^-1 I3,sigma_G^-1 I3), sigma_L,sigma_G in {1/2,1,2,4}, each finite/positive. These are declared deterministic precision weights, not a measured noise covariance or independent Gaussian sampling law. For baseline-only use the first 13 rows. Set P=I-(WN)(WN)^T/||WN||^2. A=P W J; ybar=P W y. The full joint physical covariance remains NOT_SUPPLIED. If a Gaussian demonstration is added later it must be explicitly stipulated and is not required here.

## Exact rank and nullspace proof

For q!=1, retained theorem gives rank[E4,R E9]=13: first nine null equations force the degree<=2 slope polynomial to equal minus the degree<=1 intercept polynomial; four repeated directions at q then force their intercept to vanish. E4 evaluated at ex,-ex,ey,ez has nonzero determinant; E9 is unisolvent for the nine directions. An invertible change from retained polynomial coordinates to the orthonormal STF coordinates preserves this rank. Do not copy its raw determinant number as the determinant of the changed basis.

Consequently rank(P0[-E3,E3,R E9])=12, because the full 13-dimensional output image contains the scalar nuisance. Baseline J0 has rank 12 after quotient and exactly six kernel dimensions:
 k_split(v)=(v,v,0,0,0,0), v in R3;
 k_hist(w)=(0,0,0,0,0,w), w in R3.
To prove completeness, quotient-null means J0 theta=alpha' 1. Independence of [1,E3,R E9] forces b-ell=0 and all nine rate/mean-history/STF coefficients zero; g1 is unrestricted. The observable combinations are b-ell, m, g0 and all five signed s coordinates. Rank is structural; these named combinations are not an orthonormal SVD basis. The finite builder must also report the right singular vectors/projectors and associated combinations in the declared scaled coordinates.

Adding z_L removes all split modes: its value on k_split(v) is v. Adding z_G removes all history modes: its value on k_hist(w) is w/3. Joint augmentation has rank 18 after the same scalar quotient, and either augmentation separately has rank 15. Because W is invertible, positive finite row weights do not change rank. At q=1 the original unconstrained rank is nine, quotient rank eight; baseline rank eight and augmentation rank fourteen. Four radial/intercept degeneracies remain even after both additions. Explicit ones: at q=1, choose any dipole d, change b by -d and g0 by d, g1 by -3d, ell fixed; baseline and both additions are unchanged. A monopole change m compensated by alpha is the fourth direction. This is a required negative control.

## Coordinate normalization and numerical sensitivity

Use fixed physical units above first. At nominal q=2, sigma_L=sigma_G=1, compute d_j=||P J_aug e_j||_2 and L=diag(1/d_j). Every d_j is strictly positive because the augmented response is injective. Write theta=L z. Freeze this SAME L for baseline, single-addition, augmented and radius/precision scans. Thus nominal augmented columns have unit norm, baseline g1 columns remain zero, and the design comparison does not renormalize weak data away. Report physical scales, all d_j, L and both unscaled/scaled singular spectra. Do not normalize baseline zero columns by zero.

For rectangular baseline A0=P0 J0 L, a thin SVD gives only 13 singular values; explicitly report six right-kernel dimensions and the full 18-coordinate null basis/projector. A thin SVD zero count alone undercounts the nullspace. Sort singular values descending; right-vector signs and bases in degenerate singular subspaces are arbitrary. Compare subspace projectors/response residuals, not individual singular-vector signs.

For declared scaled response A, observed design perturbation Delta with ||Delta||2<=eta and projected data error ||e||2<=epsilon, Weyl gives s_min(A+Delta)>=s_min(A)-eta. If s_min(A)>eta, least squares using A+Delta obeys
 ||z_hat-z||2 <= [epsilon+eta||z||2]/[s_min(A)-eta].
This follows from (A+Delta)(z_hat-z) being projected e-Delta z and ||(A+Delta)^+||2<=1/[s_min(A)-eta]. For rank-deficient designs apply the fixed-operator statement only to identified combinations; no uniform whole-parameter bound exists. If eta>=s_min, report NOT_CERTIFIED_BY_THIS_BOUND, never set error to zero.

An especially transparent history sensitivity is g1=3(z_G-g0): if ||delta z_G||<=e_G and ||delta g0||<=e_0 then ||delta g1||<=3(e_G+e_0). b=(b-ell)+z_L has bound e_difference+e_L. These deterministic bounds require no independence. Report them beside SVD gain so the new history window's factor-three penalty remains visible.

## Frozen design grid, outputs and acceptance criteria

1. Main table: q=2; baseline, +endpoint, +history, +both; ranks 12,15,15,18; kernel dimensions 6,3,3,0; all singular values in fixed L coordinates.
2. Radial-leverage grid q=1+d, d in {0,1e-4,1e-3,1e-2,1e-1,1,3}; compare q=1 exact rank 8/14 controls, positive-gap full ranks. Plot nonzero smallest singular values/inverse gains; zero singular values shown explicitly, never logged as finite gains.
3. Additional-channel precision grid sigma_L,sigma_G in {1/2,1,2,4}, same frozen L; report augmented s_min and condition number. Fixed-eta plot eta/s_min in {0,0.1,0.25,0.5,0.75,0.9,1,1.1}, epsilon=1e-3, ||z||<=1, illustrating certification loss at one.
4. Explicit witness v=(1,0,0)/4 and w=(0,1,0)/4 at theta=0: baseline identical, z_L changes by v and z_G by w/3; all states stay in the chosen box. Retain full signed predicted arrays.
5. Numerical precision binary64, analytic rank is authoritative. Check orthonormal basis and null residuals absolute <=1e-12. Rank-count relative cutoffs {1e-12,1e-10,1e-8} at q=2 must all match analytic ranks. Near equality list threshold dependence and never contradict exact rank because a small singular value falls below a chosen numerical cutoff. Reconstruction/residual bound checks <=1e-10 relative or <=1e-12 absolute for unit-scale synthetic data. If any mismatch occurs, preserve raw failure and return to scientific author; do not relax thresholds.
6. The main manuscript must include the exact equations, rank proof, explicit witnesses and error bounds, plus normalized singular spectrum and leverage/precision plots generated by the later builder. Source rank condition numbers are raw-basis historical results; they must not be reused as normalized new-design values.

## Complete carrier and claim status

Carrier: signed observer/bulk/history vectors plus full STF S, scalar m, complete response and deterministic joint error set. Derived observable map/linear algebra is CONDITIONAL/DERIVED; implementation currently SPECIFIED. No family identification, physical tilt detection or native result. These conditional rows do not determine a physical x_C, physical Q score, occupancy F, exceedance Pi or depth functional G_F. Report each as NOT_EVALUABLE_WITH_THIS_RESPONSE unless a separate fully specified map/anchor/law is supplied. The zero g1 response is a proven kernel, not zero physical history. No vorticity measurement exists in this radial design; retain NOT_MEASURED, not zero. A chosen normal congruence's exact irrotationality and an unmeasured matter vorticity are different statements.

Kill switches: missing or changed immutable source bytes; builder silently treating the response as physical/empirical; changing windows/scales/nuisance to obtain rank; normalizing away zero columns; inventing Gaussian independence or omitted covariance; promoting original42/V03. Later independent review must inspect actual final diff and numerical outcomes. This preparation does not satisfy that review or qualify response_design_note.
