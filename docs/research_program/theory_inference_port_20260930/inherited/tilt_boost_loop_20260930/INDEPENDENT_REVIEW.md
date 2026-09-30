# Independent decision review: tilt, homogeneous normal, and observer boost

Date: 2026-09-29 UTC / 2026-09-30 KST. Reviewer: `/root/tilt_independent_decision`.

The corrected package receives ten conditional theory promotions and one empirical hold. The initial review required two revisions and two scope clarifications; all four were corrected by the authors and independently reread before these final decisions. Every promotion means a conditional theory result ready for formalization within its stated scope. It does not mean formal proof, empirical confirmation, new scientific discovery, or an executed classification of the actual Universe.

The reviewer did not generate these candidates or design their validation. I read CANDIDATES.json, the three findings files, RESEARCH_STATE.md, and the supplied evidence scripts and results, then reread the corrected candidate snapshot, the changed findings passages and REVIEW_CORRECTIONS.md. I independently derived the pivotal identities. A second reviewer independently checked TBO-02/03/06/07 and the derivative-versus-value issue without using the symbolic outputs. Neither reviewer edited the candidate or findings files.

## Decisions

| Claim | Decision | Accepted scope |
|---|---|---|
| TBO-01 | `PROMOTE_CONDITIONAL_THEORY` | Pointwise two-axis classification, with fixed homogeneous foliation, named material component and declared observer reference. Domain-wide claims need equality/inequality on that domain. |
| TBO-02 | `PROMOTE_CONDITIONAL_THEORY` | Exact full-angular zero-distance intercept for a smooth common source congruence and common spectral standard; conditional observer/source velocity only. |
| TBO-03 | `PROMOTE_CONDITIONAL_THEORY` | Local slope-only algebraic reconstruction from exact area-distance derivative, free intercept, geodesic U and unique future timelike eigenline. |
| TBO-04 | `PROMOTE_CONDITIONAL_THEORY` | Exact curvature-clock tilt identity on a spacelike-homogeneous region with a chosen scalar I of nonzero timelike gradient. The 3-jet assertion requires metric differential order <=2; Ricci-only clock inputs require a Ricci-built I. |
| TBO-05 | `PROMOTE_CONDITIONAL_THEORY` | The signed Codazzi and perfect-fluid inversion under the declared normal/extrinsic-curvature conventions. The interval branch requires w>0 and simultaneous bounds j_minus>=0, w_minus>0, as now explicitly supplied. |
| TBO-06 | `PROMOTE_CONDITIONAL_THEORY` | Same physical ray/source and observer event, with aberrated direction labels; luminosity-distance equality additionally assumes reciprocity and transparent propagation. |
| TBO-07 | `PROMOTE_CONDITIONAL_THEORY` | Necessary and sufficient condition for the scalar absolute blackbody temperature/intensity sky at one event, not an arbitrary full polarized radiation field. |
| TBO-08 | `PROMOTE_CONDITIONAL_THEORY` | Endpoint-only inverse-boost degeneracy within an intrinsic field family, or joint probability-law family, explicitly closed under inverse Lorentz transformations. |
| TBO-09 | `PROMOTE_CONDITIONAL_THEORY` | A velocity value does not determine its congruence derivatives. The corrected hypersurface-normal exclusion explicitly concerns field equality on a neighbourhood; pointwise vorticity exclusion additionally needs spatial symmetry inheritance, and acceleration has the stated crossing limitation. |
| TBO-10 | `PROMOTE_CONDITIONAL_THEORY` | A coverage-preserving mapping theorem conditional on an already sound joint confidence set and sound outer predictions; no confidence-set construction is delivered. |
| TBO-11 | `HOLD` | Empirical cosmic-tilt or Bianchi-type classification remains HOLD_INPUT_INCOMPLETE. |

## Proof review and reasons

### TBO-01: two independent comparisons

For future unit physical velocities, gamma_XY=-X.Y/c²≥1. The equalities U=N and O=U constrain different pairs. All four combinations are kinematically possible; a scalar U.N is unaffected by changing the observer. These are pointwise comparisons unless a domain is specified. Radiation zero flux and complete radiation isotropy are distinct properties, and the selected homogeneous action/normal must remain part of the label.

### TBO-02 and TBO-03: intercept, slope, normalization and eigengap

Set o=O/c, u=U/c and K=-o+n. In the observer rest tetrad K=(-1,n), with n.n=1. The future photon momentum normalized to observed energy is p=-(E_O/c)K. Therefore E_s/E_O=K.u_s, including for accelerated source fields. At coincidence, u=gamma(o+beta_U/O), so Z(n)=gamma(1+beta_U/O.n). The monopole and dipole identify u and obey zeta0²-|zeta|²=1. This derivation fixes both the direction sign and the c normalization.

With observer-normalized length affine separation ell, d_A=ell+O(ell²). Parallel transport of K and differentiation give c dz/dd_A=K^a K^b nabla_a U_b at zero distance. Only the symmetric derivative B contributes. The free intercept is indispensable: z/d_A is not this derivative when O differs from U. Finite sources outside a virial or smoothing region do not identify the formal endpoint merely by being numerous; the continuation/remainder is an additional input.

For a symmetric form vanishing on every K=(-1,n), comparing n and -n forces its time-space components to vanish. Its spatial quadratic form is constant on the sphere, hence proportional to the Euclidean identity; its time component is the opposite constant. The kernel is exactly span(g). Thus S00=h0, S0i=-h1_i/2, Sij=qij is a valid representative. Differentiating U²=-c² yields B_ab u^b=A_a/(2c). Geodesicity supplies B.u=0, and an eigenpair S^a_b u^b=s_t u^a consequently gives B=S-s_t g.

For a realizable geodesic B, its rest-frame form is diag(0,b1,b2,b3). If all spatial bi are nonzero, the timelike eigenspace is unique, even if nonzero spatial eigenvalues repeat. If b1=0, diag(0,0,b2,b3) has timelike kernel vectors (cosh chi,sinh chi,0,0). This is a valid local geodesic kinematic jet counterexample for the slope. It does not establish identical full redshift-distance data, a complete Einstein solution family, or a no-go in the presence of an identified intercept. Vorticity does not enter the symmetric contraction; no vorticity reconstruction follows.

The primary cosmography paper explicitly imposes geodesic dust and negligible vorticity and distinguishes source and observer frames. Its distance relations support the endpoint conventions. The extension of the local symmetric-contraction argument to nonzero vorticity is justified by the derivation above, not attributed to the paper. See [Maartens et al.](https://arxiv.org/html/2312.09875v3), §§2–4, especially Eqs. 27, 62–68.

### TBO-04: clock identity and corrected differential-order premise

For every Killing generator X tangent to a homogeneous orbit, X(I)=0. A nonzero timelike dI therefore spans the orbit's one-dimensional normal complement. Choosing the future sign fixes N. Substituting dI proportional to the unit normal into the U-rest-space projector immediately gives Xi=gamma_UN²-1. Symmetry inheritance by U extends the result over the orbit, not automatically over cosmic history.

For one perfect fluid with epsilon+p!=0, the timelike and spatial stress eigenvalues differ, so the Ricci mixed endomorphism selects a unique timelike eigenline. A cosmological constant and the trace term do not change eigendirections. In multiple-component matter, this argument does not identify each material component.

The initial candidate said “curvature-order <=2”, while the actual sufficient premise is **metric differential order <=2**. The initial findings also claimed Ricci and its first derivative suffice for arbitrary such I. That was too broad: an algebraic Weyl/Riemann scalar can require full Riemann and its covariant derivative. A metric 3-jet still suffices. A Ricci-built clock is the subclass for which Ricci and its derivative suffice. The corrected candidate and findings now state these restrictions explicitly; the correction is accepted and TBO-04 is promoted within that scope. Constant/zero or non-timelike gradients disable this route and do not prove that all other routes fail.

### TBO-05: sign, dimensions, matter restriction and interval premise

With K_ab=-h_a^c h_b^d nabla_c n_d, Gaussian coordinates x0=ct give K_ij=-1/2 partial_0 h_ij. The mixed Einstein projection has G_0i=-D_j K^j_i+D_i K, while J_i=-T_i0. Hence D_b K^b_a-D_a K=kappa J_a has the stated sign. K has inverse-length units; J is energy density, cJ is physical energy flux, and J/c is momentum density.

Direct perfect-fluid projection gives E_N+p=w gamma² and J=w gamma² beta. Thus beta=J/(E_N+p), and for w!=0 vanishing J is equivalent to vanishing tilt in the single-fluid model. In a genuine homogeneous invariant orthonormal frame, derivatives of K reduce to connection contractions computed from the Lie brackets. C=0 therefore forces total J=0. It does not force separately tilted component fluxes to vanish. [Sandin](https://arxiv.org/html/0901.0800v1), §2 and Eq. 20b, explicitly exhibits the counter-tilted two-fluid case.

For the quantitative branch w>0, r=j/w=beta/(1-beta²), whose nonnegative solution is f(r)=2r/(1+sqrt(1+4r²)). This function is increasing. The interval expression is valid for simultaneous bounds 0<=j_minus<=j_plus and **0<w_minus<=w_plus**. The initial candidate's “with w->0” could not stand as this premise. Allowing w_minus=0 removes a finite subluminal upper certificate; it must not be silently divided by. The corrected candidate now explicitly supplies j_minus>=0 and w_minus>0, matching the findings. The correction is accepted and TBO-05 is promoted within that scope.

### TBO-06: endpoint invariants

For sourceward sky n and an observer boost, D=gamma(1+beta.n)>0. Photon energy scaling gives (1+z)'=(1+z)/D. Aberration has dOmega'=D^-2 dOmega. The same infinitesimal physical source screen therefore gives d_A'=D d_A; reciprocity yields d_L'=d_L/D. The asserted R and same-generator ratios follow. They are invariants after reindexing directions and retaining the same source identities, not invariants at unrelated pixel or redshift-bin labels.

The finite-angle bound follows from |log a-log b|<=|a-b|/min(a,b), a=1+beta.n1, b=1+beta.n2, and |n1-n2|=2 sin(delta/2). It is a conservative observer-factor bound only. Remaining source Dopplers, propagation and selection prevent interpreting these controls as automatic tilt measurements. R differs from the distance d_L/(1+z)²=d_A used in the Hubble derivative.

### TBO-07: inverse-temperature iff and direction convention

At fixed observer coordinates, the radiation rest velocity has components beta_R/O and 1/T_O(n)=gamma(1+beta_R/O.n)/T0. Thus b/a=beta_R/O. In axes related by the standard aligned boost, reverse components are beta_O/R=-b/a. These are not the same spatial four-vector in two rest spaces.

Conversely a>|b| makes the reconstructed inverse-temperature four-vector future timelike and yields T0=1/sqrt(a²-|b|²); its rest frame supplies an isotropic positive temperature. This proves the iff for the scalar absolute blackbody temperature/intensity sky. It does not check arbitrary polarization; calling it full radiation-field isotropy requires that additional restriction. The corrected candidate now explicitly limits the null to scalar temperature/intensity and disclaims arbitrary polarization isotropy. The criterion also does not imply matter non-tilt or any Bianchi type. Intrinsic anisotropy, foregrounds, absent monopole, and instrument processing change the hypothesis and need a forward statistical model.

### TBO-08: admissible-law qualification is essential

A reversible boost of a full intrinsic field yields the inverse construction immediately. For a random field, choose the inverse-pushforward of its entire joint latent law, then apply the same forward boost and the same observation/noise kernel. That proves equality of the complete observed law. Matching one realization, mean, or covariance alone is weaker. Cross-frequency and cross-pixel laws must transform together.

The admissible intrinsic family must include these inverse images. Arbitrary inverse sky algebra does not prove a globally realizable Einstein/matter/Bianchi state. A fixed isotropic covariance family can remove this degeneracy, and independent matter or geometric information lies outside the endpoint-only no-identification statement. Invertible rescaling cannot add information, but that statement must be applied to the whole declared data law and normalization.

### TBO-09: values do not fix derivatives; pointwise exclusion must be bounded

Direct differentiation of the submitted rapidity example gives its theta, acceleration norm, shear norm and zero vorticity. At r=0, changing r_prime already changes acceleration while preserving the same velocity. At nonzero fixed r it also changes expansion and shear. This establishes the stated derivative dependence for test congruences; it is not an Einstein-Euler solution family.

The accepted hypersurface-normal statement is about equality of **fields on a neighbourhood**. Nonzero omega_U(p) can coexist with U(p)=N(p): in Minkowski space U=gamma(1,-Omega y,Omega x,0) equals N=(1,0,0,0) at the rotation centre while omega_xy=Omega. If U and N inherit the same transitive spatial symmetry, equality at a point extends over its orbit and their projected tangential derivatives agree, so the vorticity exclusion can be strengthened to pointwise equality under that added premise.

Acceleration does not gain the same pointwise implication from homogeneity alone. The homogeneous field U(t)=(cosh eta(t),sinh eta(t),0,0), with eta(t0)=0 and eta_prime(t0)!=0, equals N on the entire t0 orbit but has nonzero A_U there. A nonzero A_U rules out neighbourhood equality with a geodesic normal, not instantaneous equality without extra dynamics. The corrected candidate and accompanying findings now preserve these qualifications wherever using the shortcut; that scope correction was independently reread and accepted.

### TBO-10: set mapping, normalization and exact zero

The coverage result is an event inclusion: when theta_true belongs to the joint state confidence set, every designated true label is retained by its image. Sound outer predictions preserve exclusion safety; a nonempty intersection is not an existence proof. If enclosure soundness is probabilistic, its failure probability must also be included. These statements do not build or calibrate the confidence set.

A lower tilt bound above zero excludes exact non-tilt within the declared model. An upper bound below a preregistered tolerance gives practical equivalence. An interval merely containing zero does not establish exact non-tilt. Joint nuisances and state-dependent normalization must remain in the same model; separately optimized incompatible extrema and a percentage of a bound are not confidence probabilities. Bianchi action/normal ambiguity and the component/observer reference tags must remain attached to the mapped labels.

### TBO-11: empirical hold

No catalogue-level response, selection/covariance, extrapolation remainder, normal reconstruction, or calibrated actual-data fit has been supplied. Consequently actual cosmic tilt and Bianchi-type classification remain HOLD_INPUT_INCOMPLETE. Accepting the mathematical routes above does not fill those observational inputs.

## Evidence strength and preserved state

The Wolfram outputs corroborate finite algebraic calculations. They do not prove every premise, physical realization, general classification, or statistical coverage. In particular, endpoint scripts assume the transformation laws rather than prove them; the independent derivation above supplies that review. The first temperature result retains an unsimplified residual, while the follow-up explicitly substitutes gamma and obtains zero. The Hubble check uses a boosted diagonal representative, so the general null-kernel and eigenline reasoning remains necessary. The flux check does not itself verify the geometric Codazzi convention. The discovery search output is not used as proof or authoritative bibliography.

Preserve **I2 DEFENDED_CONDITIONAL**, **I3 HOLD_INPUT_INCOMPLETE**, and **BIC-07 open** for the observational spatial-jet inverse problem. No new repository HEAD audit, full-data scientific classification, formal-kernel verification, or novelty determination is claimed.

## Final snapshot and correction audit

The final decision applies to CANDIDATES.json SHA-256 `07228bed04b9b9cb5903dea9b47313bcdc28d8c9deeee262d0063eddc4bf8998`. The initial text was reviewed before corrections, but its byte hash was not captured; the first artifact-write hash already reflected the authors' concurrent correction. Both rounds and the final reviewed input hashes are recorded in INDEPENDENT_DECISION.json. R1 (clock differential order and Ricci scope), R2 (strict lower enthalpy bound), S1 (field versus point equality), and S2 (scalar temperature versus polarization) are resolved. No required revision remains open in the eleven reviewed claims; the empirical classification and BIC-07 observational inverse problem remain open.
