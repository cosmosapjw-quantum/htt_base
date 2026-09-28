# MES intuition restarted: optical tensors and bounded dynamics

Date: 2026-09-20. Work unit: MES_FRESH_OPTICAL_TENSOR_R1.
Status: owner derivations for independent decision review; no observational fit or repository admission.

## 1. Contract and conventions

Preserve the original motivation: infer congruence kinematics from CMB observations, express a physically declared ratio to an inequality bound, and retain morphology. Numerical integration of dynamical ODE/PDE/Boltzmann systems is outside this work unit. Finite-dimensional algebra, symbolic checks, angular integration, and one-dimensional quadrature are allowed. Previous methodology and negative assessments are not premises of the argument.

Metric signature is (-,+,+,+). Proper time t is in seconds, H and sigma_ab in s^-1, acceleration A_a in m s^-2, pressure anisotropic stress pi_ab in Pa. The normalized timelike vector U obeys U.U=-1; physical kinematic rates are c times derivatives of U. A photon momentum is p=(E/c)(U+e), with propagation direction e and observed sky direction n=-e. Planck occupation is [exp(E/(k_B T))-1]^-1 and E=hbar*omega; c,hbar,k_B are not set to one. They cancel in the energy/temperature ratio used below.

General exact geometric-optics identity, per unit rest-frame path length ell:

    d ln E/d ell = -[H/c + A.e/c^2 + sigma:ee/c].

This comes from p^a p^b nabla_a U_b and the null geodesic equation. Antisymmetric vorticity drops out of this contraction; its absence is an observational-response fact, not an assumption omega=0 in a general spacetime. Collisionless Planck transport gives T_o(n)=T_e(x_e(n),e_e(n))/(1+z(n)). No inverse-square focusing factor multiplies diffuse specific intensity: I_nu/nu^3 is conserved and focusing changes the source/angular mapping.

Distinguish timelike sigma_ab, screen optical shear, endpoint image distortion, and temperature STF multipoles. The local ray generator H(e) and its drift are not themselves the observed static CMB map.

## 2. Exact endpoint optical tensor (conditional theorem)

Assumptions: Bianchi I metric ds^2=-c^2 dt^2+h_ij(t)dx^i dx^j with SPD h, synchronous comoving geodesic emitters/observer; a common emission-time hypersurface t=t_*; spatially and angularly uniform Planck temperature T_* there; collisionless propagation afterwards; no uncorrected local observer boost. These are restrictive symmetry/source assumptions, but no small-anisotropy approximation.

Translational Killing symmetries imply constant covariant momenta p_i. The measured photon energy is E(t)=c sqrt(p_i h^{ij}(t) p_j). Choose observer coframe B_o with h_o=B_o^T B_o. Then p_i=-(E_o/c)(B_o^T n)_i, so

    (E_*/E_o)^2=n^T B_o h_*^{-1} B_o^T n,
    T_o(n)^{-2}=n^T M n,
    M=T_*^{-2} B_o h_*^{-1} B_o^T >0.

M has units K^-2. Define angular average <f>=(4 pi)^-1 integral f dOmega and Y=T_o^-2. The isotropic identities <n_i n_j>=delta_ij/3 and <n_i n_j n_k n_l>=(delta_ij delta_kl+delta_ik delta_jl+delta_il delta_jk)/15 give

    M=<Y>I+(15/2)<Y(nn^T-I/3)>.

This is an algebraic inverse of the complete ideal temperature field. A symmetric matrix whose quadratic form vanishes on every unit vector is zero, establishing uniqueness. Its five shape degrees of freedom are

    R=M/(det M)^(1/3),       K=(1/2)log R,       tr K=0.

K is dimensionless and transforms as K -> O K O^T under observer triad rotations. Calibration T -> b T rescales M but leaves K invariant. In the isotropic limit M=m I and K=0. Full Y has only ell=0,2, and full T is even. Conversely any positive quadratic Y gives this endpoint temperature family; this is a family-membership statement, not unique causal attribution.

The exact diagonal forward redshift is already known: Fleury–Pitrou–Uzan (2015), Sec IV.A Eq(4.5), https://arxiv.org/pdf/1410.8473 . This note rederives an inverse/normalization for the current research purpose; no novelty claim is made. The provided optical draft gives the general endpoint framework, not an observation of H(e).

## 3. Weak limit and morphology

Write h(t)=a(t)^2 diag(exp(2 beta_i(t))) in a fixed coframe with sum beta_i=0. Then

    K=diag(beta_i(t_o)-beta_i(t_*)),
    T(n)=Tbar_scale [n^T exp(2K)n]^-1/2,
    Tbar_scale=T_* a_*/a_o.

Tbar_scale differs from the sky mean at order K^2. With s=n^T K n, r=n^T K^2 n, I2=tr K^2,

    Theta(n)=T(n)/<T>-1
            =-s-r+(3/2)s^2+(2/15)I2+O(||K||^3).

Thus Q_ab^T=-K_ab+O(K^2), where Theta_2=Q_ab^T n^a n^b; <Theta_2^2>=(2/15)Q^T:Q^T. At second order the ell=4 coefficient is (3/2)K_<ab K_cd>. The ell=4 relation is a conditional model check; for ||K||~10^-5 it is order 10^-10, so no claim of useful present-data discrimination follows. Independent primordial multipoles are not removed by this algebra.

Morphology invariants:

    I2=tr K^2,
    chi=sqrt(6) tr K^3/(tr K^2)^(3/2),       -1 <= chi <= 1.

The range follows from the discriminant of lambda^3-(I2/2)lambda-I3/3. Keep K itself, not only these scalars; eigenvectors carry observed orientation and are not unique inside degenerate eigenspaces. diag(1,-1,0) and diag(1,1,-2)/sqrt(3) have the same I2=2 but chi=0,-1. Squaring K loses K versus -K, so a PSD tensor alone is not a complete morphology carrier.

## 4. A precise bridge to dynamics without numerical evolution

In the fixed-axis diagonal sector sigma_i=dot beta_i, hence K=integral sigma(t) dt. Commuting principal axes are sufficient for this identity. General noncommuting histories require transport/order information; no necessity claim about coaxiality is made.

For Einstein gravity in this diagonal Bianchi I sector, with pi the total spatial STF pressure in the same orthonormal axes,

    dot sigma+3H sigma=P,       P=(8 pi G_N/c^2)pi.

Normalize a_o=1 and set

    I=integral_[t_*,t_o] a(t)^-3 dt >0,
    W(s)=a(s)^3 integral_[t_*,s] a(t)^-3 dt,
    J=integral_[t_*,t_o] W(s)P(s) ds.

Multiplying the differential law by a^3, integrating backwards, then exchanging the triangular integration order gives exactly

    K=I sigma_o-J,       sigma_o=(K+J)/I.

I is in seconds, W in seconds, P in s^-2, J and K dimensionless. This retains actual dynamical content rather than merely renaming a static sky tensor.

If ||P(s)||_F <= p(s), a declared stress budget, then

    ||sigma_o-K/I||_F <= R_pi/I,
    R_pi=integral W(s)p(s) ds,
    max(0,||K||_F-R_pi)/I <= ||sigma_o||_F
                           <= (||K||_F+R_pi)/I.

This is a finite-residual inequality with no integration of a shear evolution equation. It is conditional on the chosen a(t), stress budget, axes and source model. An outer bound is not a theorem that every point in the ball is an Einstein–matter realization. If K is an uncertainty set, propagate that set jointly with I,J rather than substituting one best fit.

For P=0, sigma_o=K/I and Sigma_o=sigma_o/H_o=K/(H_o I). With a declared isotropic expansion history and a=1/(1+z_bg), I=integral_0^z_* (1+z_bg)^2/H_bg(z_bg) dz_bg. z_bg is a volume-scale label, not the direction-dependent observed Bianchi redshift. A fixed FLRW H is only a perturbative background when its consistency with anisotropic stress and shear backreaction is controlled. Replacing it by a measured H interval is another conditional input.

Crucial physical limit: collisionless photons acquire anisotropic stress in an anisotropic geometry. P=0 is not generally exact for a self-gravitating anisotropic CMB. It requires a test-radiation idealization or a justified total-stress approximation. The finite R_pi branch is the intended route for relaxing that idealization.

Analytic toy (dimensionless time): t in [1,2], a=(t/2)^(2/3), P=C constant STF. Then sigma(t)=[4 sigma_o-C(8-t^3)/3]/t^2, I=2, J=5C/6, K=2 sigma_o-5C/6. This checks the sign and weight in the sourced relation without solving an ODE numerically.

## 5. What an endpoint observation leaves open

To diagnose the missing information freshly, let an interval have length L and change a shear history by Delta sigma(t)=C[2(t-t_*)/L-1]. Its time integral is zero while Delta sigma(t_o)=C. Equivalently delta beta vanishes at both endpoints but has nonzero final derivative. Thus endpoint optical strain alone does not uniquely determine current shear when the source/dynamics is free. This is a kinematic construction, not a dust or fixed-stress Einstein solution; the finite-residual dynamic law above states exactly what restricts it.

Even without field equations, if tensors are compared in one fixed/transported frame and ||dot sigma||<=L_sigma over the interval, then

    ||sigma_o-K/L|| <= (L_sigma L)/2.

This follows by averaging ||sigma_o-sigma(t)||<=L_sigma(t_o-t). Equality can be attained by a linearly changing fixed-direction tensor. For a generic spacetime K need not be the unweighted shear integral; this inequality applies only after the transport/response identity is established.

## 6. Percentages and the x,Q,Pi,F,G_F bridge

The existing 2026-04-20 document defines a signed bundle projection x=Sigma_std^2-W_std^2+Omega_tilt+Omega_k, Q=N(x)/U, Pi(q)=P_nu(Q>q), F=x/U only in an admitted nonnegative bounded sector, and G_F=F(z_a)/F(z_b). We reuse these definitions, not old methodological verdicts. New pilot quantities must not silently replace the multi-component x.

In the pure-shear pilot define Sigma=sigma/H and x_sigma=tr(Sigma^2)/6, using sigma_scalar^2=sigma_ab sigma^ab/2. If a same-state MES bound is B_sigma on ||sigma||_F/theta with theta=3H>0, it implies

    x_sigma <= U_sigma=(3/2)B_sigma^2.

Under the compact MES assumptions B_sigma=(5/3)epsilon_1+3epsilon_2+(3/7)epsilon_3, with epsilon_l bounds on PSTF temperature-tensor norms, not sky RMS. The specific derivative, all-observer and geodesic assumptions must be stated; observed multipole estimates alone are not these domain-wide bounds.

A morphology-preserving lift is the signed normalized STF amplitude

    A_sigma=Sigma/sqrt(6 U_sigma),
    Q_sigma=tr(A_sigma^2)=x_sigma/U_sigma.

The report carries A_sigma and the scalar Q_sigma together. A positive-sector F_sigma equals Q_sigma only when the physical target and U_sigma bound actually apply, with 0<=F_sigma<=1. A U_sigma borrowed outside MES assumptions is a reference scale and produces a reference-normalized score, not a new MES theorem. Percent 100 F_sigma is a quadratic-budget ratio; 100 sqrt(F_sigma) is the corresponding norm-bound ratio. Neither is the fraction of all spacetime geometry that is non-FLRW. A proven upper bound need not be a sharp attainable maximum.

Pi_sigma(q)=P_nu(F_sigma>q) requires an explicitly chosen joint posterior or measurement law, propagating correlations between numerator and denominator. A same-sky ratio is not automatically invalid, but neither cancellation of amplitudes nor the ratio itself creates independent information. No probability is computed in this work unit.

For genuine two-depth tensors in a common specified frame, retain G_F=F_a/F_b where F_b>0, plus rho_ab=tr(Sigma_a R Sigma_b R^T)/(||Sigma_a|| ||Sigma_b||), and Delta A=A_a-R A_b R^T. R is a physical frame comparison, not an orientation chosen after observing the data. These reveal rotation/shape changes at unchanged F. One CMB last-scattering screen does not supply two pointwise epochs; additional observations or explicit dynamics are required. At zero amplitude report directional quantities undefined rather than inventing axes.

Keep full measured Q^T_ab,O^T_abc as sky morphology carriers. In this homogeneous isotropic-emission pilot O^T=0 geometrically; actual observed octupole may be primordial or a different component, so its presence does not itself exclude a subdominant shear contribution.

## 7. Observable estimation and competing constructive paths

For an observed temperature map fit the forward model T_model(n)=A/[n^T exp(2K)n]^(1/2), with calibration, local boost, source anisotropy, mask, beam and noise stated. Do not take inverse squares of unbounded Gaussian noisy pixel temperatures: the reciprocal moments need not exist. Fit in temperature space or use a justified positive bounded error model. The exact inverse is an ideal theorem and a validation fixture, not an unbiased noisy estimator.

At first order in a weak endpoint strain one may use a finite-dimensional likelihood y=A_response k+b_source+n, k the five STF coefficients. A published or independently justified covariance for b_source+n makes a conditional statistical analysis possible without running a new Boltzmann solver. Arbitrary unconstrained b_source removes that identification; assuming it zero is a physical source assumption. Low-ell fitting alone cannot uniquely attribute a quadrupole to homogeneous shear, and covariance/primordial-source uncertainty must not be called instrumental error.

Constructive alternative: local directional cosmography. With n the outward sky direction, H_obs(n)=H-A.n/c+sigma:nn and D_L(z,n)=cz/H_obs(n)+O(z^2). The nine monopole/dipole/quadrupole components can be estimated from a suitable low-z distance-redshift sample without selecting a Bianchi family or integrating evolution. This gives a local kinematic anchor to compare with CMB endpoint strain, but is not CMB-only, needs peculiar-motion/calibration control and a controlled redshift expansion. Source: Heinesen (2021), https://arxiv.org/pdf/2010.06534 , Eqs(2.11),(3.10), sections4–5.

Other paths retained for later research: tensor-valued MES residual domains before triangle-inequality compression; finite-basis shear histories with analytic response integrals; weak-form transport moments with boundary/derivative data. They exchange explicit regularity/source assumptions for solvability. They are candidates, not proved global replacements of MES.

## 8. Provisional decision target

Select the exact endpoint optical tensor plus finite-stress dynamic interval as the first constructive theoretical pilot. Keep MES as a conditional benchmark and local cosmography as a complementary path to current shear. The step selected is further analytic/statistical-method development, not empirical validation, publication novelty, full anisotropic coverage, or scientific admission in htt_base.

Independent reviewer should assess: exact endpoint inverse and conventions; source-history assumptions; sourced identity and stress-ball bound; percentage units/normalization; preservation of full tensor morphology; no accidental full-geometry or data claim. An independent review of this isolated note does not resolve the separate native client/production audit.
