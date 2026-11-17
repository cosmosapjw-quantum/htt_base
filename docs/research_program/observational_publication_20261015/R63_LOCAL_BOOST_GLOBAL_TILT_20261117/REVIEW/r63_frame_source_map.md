# R63 frame/source map — R2/C2

Owner: /root/r63_frame_theory. Scope: source-to-equation mapping, no implementation, no remote writes, no new numerical or observational claim. Read-only baseline HEAD `f29bbab420a33aecb1c398ddd961fd45097f536b`, branch `research/r63-local-boost-global-tilt-20261117`, existing checkout `/home/cosmosapjw/Dropbox/bianchi/htt_base`, observed 2026-11-17. Requested profile: **gpt-6-astra/xhigh** (parent-specified); observed model/effort: **UNKNOWN**. Sources are hashed in `r63_frame_source_hashes.json`. R2/C2 source mapping complete; later derivation stages remain unauthorized at this checkpoint. Tests: **NOT_RUN**; implementation statements below mean inspected source, not newly executed verification.

Applied PhysMath 1.3.0 R2/C2 and POLICY_INTEGRATION, mathbox research-program principles, and repository local/global-discrimination, physics-math-audit, transfer-provenance instructions. Current stage boundary overrides generic continuation instructions. Preserve exact finite endpoint response, open global-history routes and R62 constraints; missing transfer is an unresolved construction obligation, not a new strong no-go.

## 1. Qualified conventions and the observed naming collision

Use signature (-,+,+,+), physical four-velocities U_X.U_X=-c², normalized u_X=U_X/c, outward source direction n=-photon propagation direction. A qualified velocity beta_{X|Y} means **X measured in the orthonormal tetrad of Y**, at a stated event; u_X=gamma_{XY}(u_Y+beta_{X|Y}^i e_i^(Y)). Gamma=-u_X.u_Y, speed=c sqrt(1-gamma^-2), rapidity chi=acosh(gamma)=atanh|beta|. All beta, chi and gamma are dimensionless; rapidity magnitude is not speed. A three-vector requires triad orientation in addition to these invariant scalars.

| Source and exact location | Existing symbol meaning | Reuse / translation |
|---|---|---|
| `htt/obsstat/publication_frame_kinematics.py:27–39,64–82` | beta_RO=O in R; beta_RM=M in R; beta_MO=O in M | beta_RO→beta_{O|R}, beta_RM→beta_{M|R}, beta_MO→beta_{O|M}. Explicit finite transform and source packet already distinguish B_W from tilt. |
| `htt/src/common/relativistic_velocity_closure.py:225–287` | beta_RM=matter relative radiation; beta_MO=observer relative matter | Same direction convention as publication module, canonical consecutive-boost triads required. |
| `htt/htt/htt/infer/r52_joint_identification.py:3–13,176–212` | beta_RM=(v_R-v_M)/c; beta_MO=(v_O-v_M)/c, **first order** | beta_RM→beta_{R|M}, opposite first-order sign to publication module. CMB design = beta_MO-beta_RM; CF4 source bulk=-c beta_RM. Do not silently flip this preserved API. |
| `htt/bass/background/tilted_bianchi_state.py:1033–1051,732–747` | v_matter,v_rad,v_obs all normal-frame; b_mr=R in M, b_mo=O in M | Bundle composes `(-b_mr,b_mo)`, so naming differs from common closure but the explicit sign is present. Finite triad transport is part of the contract. |
| `htt/bass/observer/observer_boost.py:24–89` | ObserverBoost stores nonnegative scalar rapidity and direction; speed=tanh(rapidity), gamma=cosh(rapidity) | Correctly type-distinct from cosmological species tilt; acts after cosmological output. |

The R52 sign is an explicit convention, not itself a physical error. A new R63 object should use qualified labels and adapters; an unqualified `beta_RM` across these APIs is unsafe. R52 is first order: exact finite inverse velocities are also affected by triad orientation, so a sign replacement alone is not a complete noncollinear transport map.

Geometric Bianchi tilt means beta_{M|N}, with N the homogeneous hypersurface normal; radiation–matter relative motion beta_{M|R} is a different quantity unless R=N is supplied. Normal vorticity vanishes by hypersurface orthogonality; matter congruence can have vorticity (`htt/bass/hierarchy/frame_contracts.py:37–95`). A local observer boost changes the measuring tetrad at one event; it does not specify a matter velocity field, its derivatives, or its history.

## 2. Existing exact finite endpoint response

`htt/src/common/relativistic_kinematics.py:54–73` implements active B(beta)e0=gamma(1,beta), B^-1=B(-beta). `publication_frame_kinematics.py:27–39` implements, for object b and new frame u expressed in one reference tetrad,

    beta_object|new = [b/gamma_u - u + gamma_u/(gamma_u+1) (u.b)u]/(1-u.b).

`relativistic_velocity_closure.py:225–287` implements the inverse composition,

    beta_{O|R} = [b + w_parallel + gamma_b^-1 w_perp]/(1+b.w),
    b=beta_{M|R}, w=beta_{O|M}.

Wigner orientation must accompany a product of noncollinear boosts. The closure module records a rotation; `congruence_ssot.py:120–157` separately records a full Lorentz product. Do not add rapidity vectors as if they were commuting scalars.

`htt/obsstat/lorentz_sky_pullback.py:1–15,74–141,144–205` provides exact all-orders, blackbody thermodynamic-temperature response for |beta|<1:

    D(n)=gamma(1+beta.n)=1/[gamma(1-beta.n_tilde)],
    T_tilde(n_tilde)=D T(n(n_tilde)),  dOmega_tilde=D^-2 dOmega,
    n_tilde=[n+{gamma+(gamma-1)(beta.n)/beta²}beta]/[gamma(1+beta.n)].

This is a ready endpoint Lorentz operator, not a global matter-history transfer. It transforms an existing source field at inverse-aberrated directions and preserves the input thermodynamic temperature unit. It does not itself supply intensity/bandpass, polarization-screen, foreground or catalogue-selection responses. `THEORY_REBOOT.md:27–53` contains the first-order differential response and fixed-quadrupole→dipole/octupole decomposition. Reuse with the same outward direction/Doppler-weight convention.

## 3. Actual likelihood and distance path inherited by R62

The consumed path is `scripts/r62/build_r62_source_carriers.py:63–96,113–164`, using R58 source operators and full fixed covariance, not the old unsourced physical-response likelihood:

    z = catalogue z_CMB; n = n_J2000;
    eta_i = ln[y(z_i)/d_i],  d_i=10^[(mu_i-25)/5] Mpc,
    y(z)=c(1+z) chi_hat(z), chi_hat=H0 chi/c,
    g(z)=[(1+z)/(E chi_hat)-1]/c = [A(z)-1]/c,
    A(z)=c(1+z)/[H(z) chi(z)],
    X_source = [g n, n, P_j((z-.055)/.045) (n E_A n)], j=0,...,J.

Sources: `r54_distance_estimators.py:7–22,86–95`; `r54_lcdm_body.py:208–219`; R62 builder:83–96. Code c=299792.458 km/s, g in (km/s)^-1, bulk V in km/s, all angular coefficients and g V dimensionless. Eta's h=ln H0 shorthand assumes the fixed numerical H0 unit used by the catalogue model; its anisotropic differences are dimensionless. The finite Legendre-z coefficients are phenomenological light-cone response coefficients, not automatically sigma/H, acceleration or a cosmic-time history.

For each survey/nuisance operator O_m, y_m=O_m eta, X_m=O_m X_source, and the full C_m is reused. `r58_mixed_tensor_likelihood.py:1–16,34–117` retains the Gaussian likelihood J=X^T C^-1 X, t=X^T C^-1 y, q0=y^T C^-1 y and log det C, with a stable whitened factor. It keeps mixed-vector/STF and cross-depth covariance. Singular estimator covariance is not a finite uncertainty for null directions. The R62 carrier marginalizes fitted polar nuisance through the full inverse, not by setting nuisance fixed (`R62/THEORY.md:16–29`).

The parent literature lane reports verified first-order Hui–Greene endpoint distance kernels. The next derivation should bind these explicitly to the catalogue processing before numerical use. With beta_S=source in a fixed cosmological reference, beta_O=observer in that reference, n outward, and eta residual at fixed quoted redshift, the candidate maps to derive/check are:

    raw observed z, raw D_L: delta eta=(A-1)n.beta_S-A n.beta_O;
    z-only CMB correction, raw D_L: delta eta=(A-1)n.beta_S+n.beta_O;
    z and D_L deboosted consistently: delta eta=(A-1)n.beta_S.

Here the literature verification is parent-relayed, not an independently opened paper in this source-only lane. Current code g is the source coefficient (A-1)/c. An observer coefficient cannot be assumed from the word `z_CMB`; actual luminosity-distance/photometric processing determines which row applies. In the z-only case a free source angular dipole absorbs the constant observer term. Its absorption does not mean the underlying photon endpoint response vanishes.

## 4. Existing full-covariance quotient and exact scope of calibration

`THEORY_REBOOT.md:55–81` already states y=mu0+J_L beta_L+J_G g+N nu+epsilon, whitener W, P=I-(WN)(WN)^+, and information after nuisance projection. `r54_identifiability.py:173–196` implements the two-depth-law Schur complement including a full 3K×3K covariance. `r62_tensor_classes.py:108–132` has K_j-K_reference and V→L V L^T for an arbitrary additive common **STF coefficient**.

For a declared nuisance response N and SPD C, the reusable identified experiment is

    y_bar=P W(y-mu0), J_bar=P W J,
    I=J^T W^T P W J,
    ker J_bar = physical response directions absorbed by N or absent from data.

Use an orthonormal basis Q of im(P) to form non-singular quotient coordinates Q^T W y if a normalized density is needed; covariance there is I. Keeping P W y as an ambient vector gives covariance P, not ambient identity. For comparing local and history blocks, profile the local block too: I_G|L=Jbar_G^T[I-Jbar_L Jbar_L^+]Jbar_G. Parameter scale and numerical rank threshold must be stated; check a smallest singular value against response error, rather than merely counting columns.

R62's actual source calibration test is finite-dimensional: angular=n and nE_A n, eight columns (`build_r62_source_carriers.py:92,111–141`). Arbitrary coefficients in this span shift the constant source coefficients and preserve varying STF coefficients. `R62/THEORY.md:108` explicitly excludes arbitrary nonconstant calibration. A literal unconstrained angular function a(n) evaluated at distinct catalogue directions can interpolate arbitrary sample values; its finite-sample nuisance image can be all of R^N. Thus no unconditional claim of calibration immunity follows from redshift dependence alone. This is a precise limit of that stipulated nuisance class, not a new universal no-go. A useful extension declares a harmonic bandwidth, angular smoothness/budget, repeated-direction observation, shared calibration model, or known nuisance operator and computes the resulting quotient. Higher angular leakage under incomplete sky coverage must be propagated through the actual O_m; subtracting apparent-bin tensors alone is insufficient.

## 5. Existing global-history content and the bridge still needed

R2 reuse sources support several distinct nonzero history responses:

* `r51_source_bound_response.py:46–69,208–227`: in restricted Bianchi I with a fixed shear eigenframe, integrated Sigma=int sigma dt, delta T/T=-n Sigma n to first order; exact collisionless T/Tbar=(n^T exp(2Sigma)n)^-1/2. Today sigma/H and integrated Sigma are different parameters. The conditional no-anisotropic-stress history sigma a³=constant is explicitly limited.
* `THEORY_REBOOT.md:117–137`: global history enters source/collision/transport evolution before the local endpoint boost. Its restricted LRS I example gives b(t)=int S dt and a quadrupole; matched endpoint velocities do not force those history integrals equal.
* `r51_source_bound_response.py:139–180`: the prior Gaia E2=shear shortcut was quarantined; the intended proper-motion response is the endpoint/history operator 2c(B_o-B_s)/D-dot B_o. Static velocity alone gives static aberration, while drift contains observer acceleration a_obs/c.
* R62 `THEORY.md:167–194`: tilt moments (v²,v n v,v n² v) have physical Jacobian 2[v^T;(nv)^T;(n²v)^T]; moment-matrix rank is not the v-Jacobian rank. Stabilizers of a repeated eigenspace are quotient freedom; even moments may omit discrete oriented information.

Geometric reconstruction additionally needs the correct congruence. R62 `THEORY.md:179–188` assumes geodesic homogeneous normals, a Fermi frame and proper time, and gives

    R3=(16 pi G/c^4) epsilon_N+2 Lambda-6H²/c²+(sigma:sigma)/c²,
    S3_ab=(8 pi G/c^4) pi_Nab-(D_t sigma_ab+3H sigma_ab)/c².

Each term has m^-2. Matter-frame shear cannot replace normal-frame shear, and a matter-perfect fluid tilted relative to N has nonzero normal anisotropic stress. Exact Lorentz projection is already in `tilted_bianchi_state.py:352–384`: for a perfect fluid with beta=beta_{M|N}, epsilon_N=gamma²(epsilon+p)-p, q_N=gamma²(epsilon+p)beta, pi_N=gamma²(epsilon+p)STF(beta beta). This q is an energy-density momentum-flux coordinate with normalized u; physical energy flux is c q.

The active constraint convention is C^k_ij=a_i delta^k_j-a_j delta^k_i+epsilon_ijm n^mk, n a=0, D_i=-(sigma_jk epsilon_kil n_lj+3sigma_ij a_j), D_i+kappa q_i=0 (`R62/THEORY.md:126–157`; `tilted_bianchi_state.py:797ff`). Type-I total q=0 can be supplied by compensating fluids; it is not a blanket no-tilt rule for every species. IX rank depends on the actual n eigenvalue gaps. Do not import canonical-fixture rank as a typewide theorem.

## 6. Concrete misidentifications, classified by current relevance

| Object | Observed issue | Smallest constructive correction / present relevance |
|---|---|---|
| Cross-module beta_RM | Opposite explicit directions in R52 and publication/common closure | Qualified beta_{X|Y} interface and provenance-preserving adapters; **current R63 integration risk**. |
| CF4 bulk coefficient | Source/light-cone residual in z_CMB product is readily mislabeled observer speed or global tilt | Bind endpoint corrections and g(z) history map first; **current R63 target**. |
| R62 calibration invariance | Valid for finite common dipole/STF source span; arbitrary a(n) is a larger nuisance image | Declare N before the quotient; **current R63 target**. |
| Phenomenological tensor-z coefficients | Not sigma_N(t), and redshift is not by itself cosmic time | Source/geometry/optical response map; **open constructive obligation**. |
| Older R49 response terms | Registry already quarantines 0.18 polarization gain, finite-curvature profiles, today/integrated shear conflation, Gaia velocity/drift and SN shortcuts (`r51_source_bound_response.py:70–165`) | Do not resurrect for R63. No current R62 consumer found; **preserved historical debt**. |
| `bass/hierarchy/tilt_kinematics.py:133–150,209–229` | Placeholder gamma²v added to gamma²Hv and gamma²sigma v, while eta is Mpc and proper shear carries inverse length; no v-dot supplied | Not a physical four-acceleration without a declared nondimensional rate map. R63 must use actual congruence derivatives or sourced evolution, not this placeholder. No R62 consumer found; **not a reason to block source mapping**. |
| Old kinematic quadrupole helper | Search exposed 1/2 STF(beta beta) convention in `common/kinematic_response.py:252–257`, unlike exact thermodynamic-temperature expansion | Use exact pullback with explicit observable normalization; scoped discrepancy not audited here and not a R62 consumed path. |

## 7. Next bounded derivation, after parent stage authorization

1. Derive the three fixed-redshift eta endpoint formulas above from redshift and distance transformations, fixing source/observer sign and catalogue correction status. Derive A(z), its low-z expansion and g(z)=(A-1)/c with units.
2. For V(z)=V_p+t(z)W and a free angular dipole d, build [g n, g t n, n], retaining actual full covariance. Show when g t lies in or near span{g,1}; distinguish exact gauge from weak information. For flat LCDM, parent-requested low-z target is g=1/(cz)-3 Omega_m/(4c)+O(z); derive before using it.
3. Compare two explicitly different questions: (i) alternative decompositions with the same endpoint four-velocities and same source field, which share the endpoint Lorentz law; (ii) genuinely different admissible global histories, whose source, optical, collision and covariance responses can differ despite equal endpoints. Construct a restricted history kernel example or state exact unsolved transfer leaf. No inference from equal endpoints to equality of all global observables.
4. Express inference on im(P W[J_L,J_G]), with the full source/operator covariance and a declared angular calibration image. Check exact null directions, scale-conditioned singular values and resulting identified combinations. Do not call a finite g n bulk fit a universal global-tilt measurement.

No implementation or new numerical verification was performed in this R2/C2 lane. The next stage should return derivations and a qualified inferential contract; implementation remains separately authorized by the parent.
