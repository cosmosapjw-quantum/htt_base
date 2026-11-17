# R62: tensor-series classification and conditional Bianchi compatibility

Baseline: `c118982e56ee50d68dd0446aa10f16ffe65bd02b`. This study concerns anisotropy classification only. It reuses the R48/R49 algebra and R54/R58/R60/R61 observational carriers. A Bianchi type is a spatial group-action class; a symmetry of one observed tensor is a different mathematical object. The purpose is to connect the two through explicit conditional maps, including useful exclusions, without treating them as identical.

## 1. Conventions and inferential object

The spacetime signature is (-,+,+,+). Physical reconstruction formulas below retain c. Spatial tensors are represented in an oriented orthonormal frame. The CF4 carrier uses J2000 equatorial directions, observed catalogue z_CMB, velocity in km/s, and dimensionless logarithmic distance-response coefficients. These coefficients are not automatically the normal-congruence shear, acceleration, vorticity, or a Bianchi connection.

Let E_A, A=1,...,5, be the Frobenius-orthonormal STF basis

    diag(1,-1,0)/sqrt(2), diag(1,1,-2)/sqrt(6),
    (e_x e_y^T+e_y e_x^T)/sqrt(2),
    (e_x e_z^T+e_z e_x^T)/sqrt(2),
    (e_y e_z^T+e_z e_y^T)/sqrt(2).

For a series K_j=sum_A k_jA E_A, retain the signed joint vector x=vec(k_jA). Retaining only a norm, a single scalar amplitude, or independent component errors loses relative orientation and covariance. The same observed data have the linear Gaussian likelihood

    -2 log L(alpha)=alpha^T J alpha-2 t^T alpha+q0+log det C+n log(2 pi),
    J=X^T C^-1 X, t=X^T C^-1 y, q0=y^T C^-1 y.

J is called precision in code to avoid confusion with the project's F view. Existing R58 GLS supplies the score, precision and stable whitened factor; R62 does not claim a new Gaussian likelihood or extra Fisher information.

For an identified tensor marginal h,V of dimension d, use

    E_d={x:(x-h)^T V^-1(x-h)<=chi2_d(.95)}.

This is one confidence event for all symmetry questions asked of that carrier. V includes the covariance created by fitting polar nuisance parameters. This is the tensor marginal covariance, not a covariance conditioned on fixing those nuisance parameters. Equivalently, profiling the joint quadratic likelihood over the nuisance coordinates gives the displayed Mahalanobis distance. Different tensor carriers/dimensions have explicitly different confidence events; their confidence probabilities are not multiplied.

Probability claims are conditional on the fixed Gaussian C and the declared finite source mean. Estimated covariance, residual sky systematics and omitted source terms require external validation. The seven nuisance operators use the same 35,970 groups and are correlated sensitivity experiments, not seven independent data sets. A model-union statement is valid conditional on at least one declared member being adequate; it is not model-averaged posterior evidence.

## 2. Five classes and their constructive certificates

Consider the following exact subsets of the tensor coefficient space, all including zero:

* ZERO: all K_j=0.
* SHARED_FRAME: K_j=R diag(a_j,b_j,-a_j-b_j) R^T for one R in SO(3).
* SHARED_AXIS: K_j=b_j sqrt(3/2)(u u^T-I/3), for one unoriented unit axis u.
* SHARED_ZERO_EIGENVALUE_SHAPE: K_j=b_j R diag(1,-1,0)R^T/sqrt(2).
* SHARED_GENERAL_SHAPE: K_j=b_j S, where S is one unit-norm STF tensor.

Amplitudes may have either sign. Requiring positivity would impose an additional evolution model and would mishandle possible sign reversals. A vanishing tensor carries no preferred frame or axis.

SHARED_AXIS and SHARED_ZERO_EIGENVALUE_SHAPE are subsets of SHARED_GENERAL_SHAPE, which is a subset of SHARED_FRAME. The first two special shape sets intersect at zero. An ellipsoid may meet several different sets at different parameter states; this is compatibility with alternatives, not simultaneous truth of every shape.

At fixed orientation or shape, amplitudes are linear parameters. For a class design B, whiten y and B using the Cholesky factor of V and solve the full-covariance GLS projection. A bounded deterministic multistart search then supplies a feasible state x_C in the exact class. Direct reconstruction checks its membership and its distance

    q_C=(x_C-h)^T V^-1(x_C-h).

If q_C<=chi2_d(.95), the class intersects the confidence set. This is a constructive intersection certificate, up to the declared floating-point reconstruction tolerance. q_C is a feasible upper bound on the distance to the class. An outside local optimizer candidate cannot prove exclusion. In that case the status is UNRESOLVED unless an independent necessary-condition enclosure excludes the entire class.

No naive Wilks chi-square degree is assigned to these optimized nonlinear distances: zero amplitude and repeated eigenvalues are singular strata, orientations may be unidentified, and a nominal parameter count is insufficient. No posterior class probability is assigned to a zero-measure exact symmetry stratum without a separate discrete model/prior.

## 3. Commutators and shared-frame exclusion

Real symmetric matrices admit a simultaneous orthonormal eigenbasis if and only if they commute pairwise. Necessity follows by multiplying diagonal matrices. For sufficiency, diagonalize one tensor; commutativity makes each of its eigenspaces invariant under all other tensors. Restrict to each eigenspace and successively diagonalize the remaining symmetric restrictions. If the resulting orthogonal basis has determinant -1, reverse one basis vector, obtaining an SO(3) frame without changing any diagonal tensor.

Thus SHARED_FRAME is exactly the common zero set of [K_i,K_j]. A signed component of a commutator is a quadratic form x^T M x. With

    x=h+A u, A=sqrt(cutoff)*chol(V), ||u||<=1,

it becomes

    u^T(A^T M A)u+2(A^T M h)^T u+h^T M h.

The existing R61 trust-region solver computes its global quadratic image with a numerical primal/dual enclosure and reports witnesses and gaps, including repeated-eigenvalue hard cases. If any component enclosure excludes zero, every shared-frame state is outside E_d, and therefore so are all of its subclasses. If every component interval includes zero, that alone does not establish simultaneous commutativity: their separate witnesses may differ. A class witness inside E_d resolves that direction; otherwise the result stays UNRESOLVED. These are floating-point numerical enclosures, not formal interval-arithmetic proofs.

The commutator norm is rotationally invariant; its signed components depend on the chosen orthonormal frame, but a component interval excluding zero still gives a valid necessary-condition exclusion. A zero-containing collection of component intervals can be conservative. Frame rotation transports both x and V through the same STF representation; rotating only point tensors while leaving V fixed changes the experiment.

## 4. Common additive calibration: an exact quotient

Suppose an unknown common additive STF tensor C affects every K_j. Define D_j=K_j-K_0 and the full linear contrast L. Then

    d=L h, V_D=L V L^T.

All off-diagonal covariance blocks must be retained. The following statement is exact:

    exists C such that all K_j-C commute
       iff all differences K_j-K_0 commute.

For the forward direction set T_j=K_j-C. Differences of mutually commuting T_j commute. Conversely, choose C=K_0; then T_0=0 and every other T_j is a difference. The same construction establishes the quotient for a common one-dimensional tensor shape, including the special axial and zero-eigenvalue shapes. ZERO in the quotient means all K_j coincide before calibration removal.

This eliminates an arbitrary common tensor offset. It is not a measurement of calibration uncertainty, and cannot remove an arbitrary redshift-dependent calibration. Nor does it imply that a common source calibration creates equal tensor offsets in arbitrary survey-estimator windows: that assertion must be checked through the actual source operator.

An elementary counterexample is a commuting diagonal tensor series plus a fixed noncommuting C. The apparent tensors can fail commutativity while all their differences commute. Conversely, equal single-tensor spectra or norms do not determine a shared frame: rotate only one member of a diagonal series. All individual eigenvalues remain unchanged while the mixed commutator changes. This is a direct reason the signed tensor carrier is necessary for the present question.

## 5. The executed source-bound CF4 model

The four retained CF4 estimators are overlapping Gaussian windows centered at z=(.025,.04,.06,.08), width .012, on the same 35,970 sources. They are not disjoint physical shells. The R58 y32 packing is dipole12 first, STF20 second. The covariance C32 preserves shared measurement noise and the inherited linear z=0 LCDM cosmic covariance.

Coherent velocity leaks into the STF estimator rows through the real sky mask and source weighting. Removing or freely fitting observed dipoles alone does not remove that leakage. The R62 finite source mean is therefore constructed before the observation operator:

    eta_i = g_i n_i.V + n_i.d
            + sum_{j=0}^J P_j(t_i) n_i.K_j.n_i,
    t_i=(z_i-.055)/.045,
    X_m=O_m D_J.

J=2 is the declared primary response and has 6+15=21 parameters. J=3 is a 26-parameter response-order sensitivity. The polar block is the same coherent V and angular dipole d used by R58/R61. Legendre polynomials improve numerical conditioning but do not add a dynamical assumption. The model is phenomenological in observed z; it is not a proper-time shear history, a full cosmographic expansion, or an Einstein solution. Spatial-homogeneity and line-of-sight evolution have not been inferred from it.

The actual source/operator product is checked against the owned R58 y32 and response32x11. The J=1 model is exactly the R61 affine model under

    K0_new=Kpivot_R61+.1 K1_R61,
    K1_new=.9 K1_R61.

Matching the means and covariances under this transformation is a control for basis and ordering errors. Rank must equal 21 or 26 in both declared physical scales and a column-equilibrated chart. No ridge regularization is introduced. Nested J1/J2/J3 comparisons are linear fixed-Gaussian tests with an exact five-dimensional Wald/LR identity; these are distinct from nonlinear class-distance tests.

If the coefficient tensors share a frame, K(z) does so for every z in the polynomial model. Conversely, commuting K(z) at enough independent redshifts implies commuting coefficients by invertible linear interpolation. A shared general shape is precisely rank one in the matrix whose rows are the STF coefficient vectors. The tests retain their covariance and do not use an unweighted SVD as a likelihood.

Adding a constant source angular tensor changes only K0; removing its coefficient yields a calibration-invariant varying part. This is checked by injecting the calibration through O_m and refitting. It does not remove velocity responses with unmodelled radial dependence or arbitrary nonconstant calibration.

A separate, noise-free injection uses three nonproportional diagonal STF tensors in one rotated frame. Passing that source through the actual O_m may produce noncommuting apparent window tensors. Recovering the original source coefficients with X_m demonstrates the distinction between estimator morphology and source morphology. This is a constructed injection through actual survey operators, not a cosmological simulation or a claimed measured rotation.

## 6. Relation to the tensorized five-variable programme

The existing five views are operationally linked to the same carrier; none supplies extra independent information.

| View | R62 use | Boundary |
|---|---|---|
| x | Signed mixed polar/STF source carrier and its precision, score and stable likelihood factor; tensor-series subcarriers retain cross-depth covariance | No scalar compression before joint symmetry questions |
| Q | Norm/gauge images on the same ellipsoid, with explicit tensor units and chosen norm | Absolute norm is available; a dimensionless physical ceiling is not supplied |
| F_support | Directional supports of linear tensor responses, and necessary quadratic commutator enclosures as an explicitly separate image calculation | No occupancy fraction without a physical body and measure |
| Pi | Named fixed-Gaussian zero and nested linear tails; common confidence-set class compatibility | No nonlinear class posterior or naive Wilks p-value |
| G_F / transport | Full-covariance depth contrasts and source-coefficient shape/frame transport, with the common-offset quotient | No inference of time evolution from a redshift label alone |

The methodological contribution being assessed is a concrete covariance-preserving observation-to-class interface, calibration quotient and conditional constraint fibre. Variable projection, confidence-set inversion, simultaneous diagonalization, invariant tensor algebra and GLS are established mathematics. A paper must compare against those methods and demonstrate a useful new observable constraint or robust classification result; renaming them as five variables does not establish novelty.

## 7. Bianchi constraints depend on the actual state

Reuse the oriented structure convention

    C^k_ij=a_i delta^k_j-a_j delta^k_i+epsilon_ijm n^mk,
    n=n^T, n a=0.

The active BASS implementation works in a declared geometrized fixture convention. Its exact momentum divergence is

    D_i=-(sigma_jk epsilon_kil n_lj+3 sigma_ij a_j),
    D_i+kappa q_i=0.

The sign must be read with this exact bracket and q convention. A neighboring legacy implementation uses another sign; R62 changes only the active constructor and adjacent documentation, and preserves that separate legacy migration debt.

The fresh review identified a scale-dependent acceptance defect in the initially proposed range guard: multiplying q by a small Einstein coupling before comparison with a unitful absolute tolerance could admit impossible momentum. R62-F1 tests range membership in source coordinates, relative to the sum of the individual species momentum norms, so a common coupling or source-unit change does not erase the condition and multi-fluid cancellations retain a numerical tolerance. The evaluator compares Jacobi, curvature, Hamiltonian, Codazzi and shear residuals to their corresponding equation scales; raw residuals, scales and normalized residuals are all retained. There is no implicit max(1,...) unit floor. A nondimensional chart with length L0 and energy density E0 has H_code=H_time*L0/c, sigma_code=sigma_time*L0/c, (a,n)_code=L0*(a,n), rho_code=rho/E0 and kappa_code=(8*pi*G/c^4)*E0*L0^2. Unit-equivalent IX states and forbidden/compensated Type-I momentum are covered by the targeted review regressions. This numerical contract does not certify every legacy background API at arbitrary physical scales.

For a=0 and diagonal n, the map from STF sigma to D has components proportional to the eigenvalue differences times the off-diagonal shear. Hence its rank depends on repeated eigenvalues of n, not only the Bianchi label. IX means definite n, not n proportional to I. The canonical n=I fixture has rank zero; a general definite n with distinct eigenvalues has rank three. A typewide IX no-tilt rule inferred from the canonical fixture is false.

In the normalized convention of Hewitt, Bridson and Wainwright, take A=0, N=diag(1,2,3), Sigma12=Sigma21=s. Then

    curvature K=-2/3, Sigma^2=s^2/3,
    Omega=(5-s^2)/3, Q=(0,0,-s).

For dust, v=(0,0,-s/(5-s^2)). For sufficiently small nonzero s, density is positive and tilt subluminal. These are constraint-admissible initial data; an entire spacetime history requires solving the evolution system. General tilted-dust IX is also established in Kwidzinski and Piechocki (2019).

For Class B, a=(a,0,0), n=diag(0,n2,n3), the active divergence map on coordinates (sigma11,sigma22,sigma12,sigma13,sigma23) is

    [-3a, 0,  0,   0, n3-n2]
    [  0, 0,-3a, -n3,      0]
    [  0, 0, n2, -3a,      0].

For a nonzero, its rank is three except n2*n3=-9a^2, when it is two. The latter is the exceptional VI_h stratum h=-1/9 in this h convention. The relevant range condition is on the actual source q and actual state map. A family label or a generic rank is insufficient at exceptional strata. The symbolic minor and Jacobian identities were independently evaluated with Wolfram Language and preserved in REVIEW/WOLFRAM_CHECK.json.

For untilted Type V, n=0, a nonzero and total q=0 imply sigma a=0. If a is unknown, det(sigma)=0 is necessary and sufficient for this momentum equation alone; choose a in the kernel. The STF spectrum is then {lambda,-lambda,0}. For fixed a its direction must agree with that kernel. Hamiltonian/positive-source constraints remain separate. Tilt or compensating source momentum changes the condition. This is the exact restricted physical motivation for the zero-eigenvalue shape class; applying it to CF4 response tensors requires an independently admitted shear response.

There is also a useful history-level implication under a stronger explicit closure. For geodesic homogeneous normals, a Fermi frame and zero normal-frame anisotropic stress, both I and V have S3=0. The shear evolution equation therefore integrates to

    sigma(t)=b(t)^(-3) S_star,  d log b/dt=H,

with a constant STF S_star. Type I permits any such shape at this level; untilted V additionally requires det(S_star)=0 and the structure vector in its kernel. Dividing by a nonzero H changes only the scalar amplitude, so the normalized shear still has fixed shape. SHARED_GENERAL_SHAPE is consequently a necessary history condition for this restricted I/V closure, and the zero-eigenvalue subclass is necessary for V. This does not extend unchanged to tilted normal-frame sources, anisotropic stress, or arbitrary higher-curvature families. A source-response coefficient series can be used for this test only after its common-frame shear/light-cone transfer has been admitted; the present phenomenological CF4 coefficients alone do not satisfy that additional premise.

## 8. Tilt moments and orbit quotient

For p=(v.v, v.n v, v.n^2 v),

    D_v p=2 [v^T; (n v)^T; (n^2 v)^T].

In a diagonal frame it is 2 M diag(v1,v2,v3), with M the Vandermonde matrix in the eigenvalues. Rank(M) measures recovery of squared-component moments, not the differential in physical v. For distinct eigenvalues and v=(t,0,0), the two ranks are three and one; at v=0 the physical Jacobian rank is zero. Rank is the number of distinct eigenspaces occupied by nonzero v projections.

Within a repeated eigenspace, rotations that preserve n are stabilizer freedom in the simultaneous rotation quotient. Calling these azimuths distinct physical geometries overstates nonidentifiability. Conversely, these three even moments alone can omit discrete orientation information in an oriented SO(3) quotient. They are diagnostic moments, not a complete universal orbit separator. A claim of a complete separator must specify orientation/parity, the full tuple including a, and all needed pseudoscalars.

## 9. A constructive Boltzmann-free geometric route

Assume a geodesic homogeneous hypersurface-normal congruence, a Fermi-propagated orthonormal frame, proper time in seconds, H and sigma in s^-1, normal energy density epsilon_N and anisotropic stress pi_N in energy per volume. The Hamiltonian and tracefree evolution equations give

    R3 = (16 pi G/c^4) epsilon_N + 2 Lambda
         - 6 H^2/c^2 + sigma:sigma/c^2,
    S3_ab = (8 pi G/c^4) pi_Nab
            - (D_t sigma_ab+3H sigma_ab)/c^2.

Every term has dimension m^-2. The second equation follows by undoing Hubble normalization in the standard homogeneous shear-evolution equation. Non-Fermi frames need the frame-rotation term. Accelerated normals need the corresponding acceleration/lapse-Hessian terms. Matter-frame shear cannot silently replace normal-frame shear. A matter-rest-frame perfect fluid generally has nonzero normal-frame anisotropic stress when tilted.

Thus reconstructed H,sigma,D_t sigma,epsilon_N,pi_N can determine intrinsic Ricci without a Boltzmann solver. Unknown pi_N leaves a curvature/stress degeneracy; unknown density/Lambda affects the scalar. These are established equations in an explicit observational input contract, not a new geometric theorem.

Generic intrinsic Bianchi action classification additionally needs spatial connection or curvature-derivative information. Ferrando and Saez (2020, Theorem7) uses spatial Ricci derivatives in the algebraically general/maximal-G3 case; Saez, Mengual and Ferrando (2024, Theorems3-4) identifies the spacelike homogeneous orbits from suitable spacetime curvature concomitants before constructing their structure tensor. Ricci at one worldline is not automatically this derivative data. Alternatively, one may solve a finite candidate-set inverse problem constrained by homogeneous evolution and source equations, explicitly stating the closure.

Intrinsic flat geometry admits I and VII0 actions; negative constant-curvature geometry admits V and VIIh actions. These known group-action degeneracies require a set-valued result unless extrinsic/source/connection information selects an action. An axial eigenvalue degeneracy of one shear tensor is also insufficient for full LRS, which requires a common axis of all relevant curvature, source and derivative quantities. No universal theorem excluding every solver-free inference is asserted.

The finite research route is therefore: observed response carrier -> joint morphology classes -> admitted normal-frame kinematic/source likelihood -> constraint-compatible (a,n,tilt) fibres -> candidate-set comparison, with action equivalences retained. R62 implements and executes the first step, corrects the actual constraint fibres needed for the third, and identifies the concrete missing observations and response contracts for the intervening step.

## Primary references

* Ferrando and Saez (2020), https://arxiv.org/abs/2004.01877v1, DOI 10.1088/1361-6382/ab9880, Eqs6-13 and Theorems4,7.
* Saez, Mengual and Ferrando (2024), https://arxiv.org/abs/2409.15854v1, DOI 10.1088/1361-6382/ad7664, Eqs39-41 and Theorems3-4.
* Hewitt, Bridson and Wainwright (2001), https://arxiv.org/abs/gr-qc/0008037v1, DOI 10.1023/A:1002075902953, general AppendixA before the II specialization.
* Kwidzinski and Piechocki (2019), https://arxiv.org/abs/1901.01790v2, DOI 10.1140/epjc/s10052-019-6701-z.
* Betschart and Clarkson (2004), https://arxiv.org/abs/gr-qc/0404116v3, DOI 10.1088/0264-9381/21/23/018, section3.
* Sung and Coles (2010), https://arxiv.org/abs/1004.0957v2, Eqs63-68 and their near-FRW limitations.
* Pontzen (2009), https://arxiv.org/abs/0901.2122v2, DOI 10.1103/PhysRevD.79.103518.
* Marcori, Pitrou, Uzan and Pereira (2018), https://arxiv.org/abs/1805.12121v1, DOI 10.1103/PhysRevD.98.023517.
* Golub and Pereyra (1973), https://epubs.siam.org/doi/10.1137/0710036, variable projection for nonlinear least squares with separable linear amplitudes.

The source audit in REVIEW/literature_map.md records the exact assumptions, versions and limitations. Repository-specific formulas and numerical outcomes are traceable to the corresponding source, tests and result receipts; historic quarantined physical posteriors are not promoted by this work.
