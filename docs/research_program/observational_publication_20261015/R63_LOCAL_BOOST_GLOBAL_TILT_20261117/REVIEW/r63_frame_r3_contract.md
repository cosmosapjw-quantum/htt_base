# R63 R3/C3: processed endpoint response and a compensated history

Owner: /root/r63_frame_theory. Requested runtime **gpt-6-astra/xhigh**; observed model/effort **UNKNOWN**. Baseline and source hashes: `r63_frame_source_hashes.json`. Parent authorized analytic R3/C3 after accepting R2/C2. This document aligns assumptions and gives algebra needed for the design; **no implementation, numerical execution, remote mutation, R4 or R5 completion is claimed**. Status: algebraically derived under the following explicit first-order optical and material assumptions; observational source/reference qualification remains conditional.

The main reused history source is `docs/research_program/observational_publication_20261015/FRONTIER_20261020/theory/THEORY.md`, especially lines100–187 (material/IC/validity), 206–251 (constraint/history), 254–358 (optics/rank), 477–530 (remainder). It preserves the earlier conditional analytic subcase and its execution receipts; those tests were not rerun here. Its literature leaves are Beltrán Jiménez–Maroto 0811.3606v3 Eqs1,2,4,5 and Kaiser–Hudson 1411.6339v2 Eqs1,8,9. This lane read the repository source; primary-paper checking belongs to the separate literature lane.

## A. Four-velocity and endpoint contract

Signature (-,+,+,+), U_X.U_X=-c², u_X=U_X/c. The qualified beta_{X|Y} is X's dimensionless spatial velocity in Y's oriented local tetrad. Gamma_XY=-u_X.u_Y, chi_XY=acosh Gamma_XY and |beta_X|Y|=tanh chi_XY. Never identify beta_{M|R} with beta_{M|N} without R=N. Existing R52 beta_RM is R in M, whereas publication/common-closure beta_RM is M in R; existing APIs retain their declared meanings.

All first-order optical velocities below are expressed in one specified FLRW background tetrad F. For the restricted compensated model F=N, the total-energy-rest hypersurface normal to first order. In a general application, a statistical FLRW reference F is not automatically the actual photon energy-rest frame R. The outward n points from O to the source. Cosmological background z_bar, heliocentric observed z_hel and catalogue quoted z_r are distinct.

Finite local closure already exists: canonical boosts satisfy u_X=B(beta_X|F)e0 and beta_{O|M}=spatial(B(-beta_M|F)u_O)/time(...). Noncollinear products retain their Wigner rotation. The exact thermodynamic sky pullback is T_O(n_O)=T_F(n_F)/[gamma_O(1-beta_O|F.n_O)] with inverse aberration. This exact endpoint statement does not make a truncated optical/history formula exact. If two descriptions have the same endpoint tetrad and the same incident phase-space field at O, their measured sky is the same; it does not follow that global histories with those endpoint velocities generate the same incident field.

## B. Derivation at fixed measured redshift

Assume first-order peculiar velocities, a prescribed flat FLRW background, a bolometric standard candle isotropic in its rest frame, photon-number conservation and distance duality, and no additional lensing/potential/metric terms. Their presence would add sourced optical terms. Let s=n.beta_S and o=n.beta_O, both in F. Endpoint energies and aberration give

    1+z_hel=(1+z_bar)(1+s-o)+O(beta²),
    D_A,hel=Dbar_A(z_bar)(1+o)+O(beta²),
    D_L,hel=Dbar_L(z_bar)(1+2s-o)+O(beta²).

The last line follows from D_L=(1+z_hel)²D_A. The source clock factor is already in the redshift and duality; adding another would double count it. For Dbar_L(z)=(1+z)chi(z), chi'=c/H,

    A(z)=c(1+z)/[H(z)chi(z)],
    (1+z) d ln Dbar_L/dz=1+A(z).

At fixed z_hel, delta z_bar=-(1+z_hel)(s-o), hence

    delta ln D_L,hel=(1-A)s+A o,
    delta eta_hel=(A-1)s-A o,
    eta_hel=ln[Dbar_L(z_hel)/D_L,hel].                 (B1)

The equation is also the anisotropic part of the implemented eta=ln[y(z)/d], since y=H0 Dbar_L and the unknown log H0 is a monopole. A and eta are dimensionless. A pure observer moving toward the source gives a negative eta at fixed measured z, consistent with the signs above.

Apply fixed catalogue corrections in the same frame/chart:

    delta ln(1+z_r)=n.V_r/c,
    D_corr=D_L,hel exp(n.V_d/c).

To first order, with a residual additive angular dipole b_cal,

    eta_r=(A-1)n.V_S/c-A n.V_O/c
          +(A+1)n.V_r/c-n.V_d/c+n.b_cal
         =g(z) n.(V_S-V_O+V_r)
          +n.[b_cal+(2V_r-V_O-V_d)/c],
    g(z)=(A-1)/c.                                    (B2)

The A+1 redshift coefficient is necessary: one power comes from the luminosity-distance (1+z) factor, the other contribution from chi. This gives the useful special cases:

| Processing | Linear eta response |
|---|---|
| raw z_hel and raw distance | (A-1)n.beta_S-A n.beta_O |
| z-only correction V_r=V_O, V_d=0, into F | (A-1)n.beta_S+n.beta_O |
| redshift and distance consistently deboosted V_r=V_d=V_O | (A-1)n.beta_S |

An actual catalogue named z_CMB does not establish either equality V_r=V_O or V_r=V_O-V_R. The exact reference and photometric correction are inputs, not conclusions from a fit.

For fixed design and deterministic additional corrections (delta V_r,delta V_d), the affine action is

    V_eff -> V_eff+delta V_r,
    d -> d+(2delta V_r-delta V_d)/c,
    eta -> eta+g n.delta V_r+n.(2delta V_r-delta V_d)/c.       (B3)

Its deterministic translation leaves noise covariance unchanged. This statement is within the first-order fixed-experiment model; changed redshift cuts, windows, directions, masks or weights require their actual new operator. If the correction vector is uncertain and correlated with y, a linear y'=y+K delta produces C'=C+K C_delta K^T+C_y,delta K^T+K C_delta,y. It cannot be inserted as an independent extra velocity measurement from the same catalogue without its cross-covariance.

## C. A physical history that supplies the z g column

Assume a finite post-decoupling interval a_i<=a<=1, dust plus one separately conserved compensating radiation component with p_r=epsilon_r/3, positive background energies, common dust velocity, no drag/collisions, no independent density or metric perturbation, and no first-order shear. The radiation is a perfect fluid or a homogeneous collisionless distribution with only a first-order dipole. A cosmological constant carries no momentum. These are the FRONTIER assumptions; no primordial tight-coupling generation mechanism is supplied.

Write R=3 epsilon_m0/(4 epsilon_r0)>0. Homogeneous conservation a^4(epsilon+p) beta=constant gives

    beta_m(a)=b/a,  beta_r(a)=-R b,
    epsilon_m=epsilon_m0 a^-3, epsilon_r=epsilon_r0 a^-4,
    Q_m+Q_r=epsilon_m beta_m+(4/3)epsilon_r beta_r=0.          (C1)

Here Q=T^(0i) has energy-density units; physical energy flux is c Q and momentum density is Q/c. The older source uses q for momentum density, so its displayed q differs by c. Zero first-order total momentum and no first-order stress/density perturbations permit the unperturbed FLRW metric at that order. At O(beta²), pi=sum(epsilon+p)gamma²STF(beta beta) is generally nonzero; exact finite-amplitude FLRW is not claimed.

Let ell=observer velocity relative to present dust divided by c, so beta_O=b+ell. Emitters follow the dust: beta_S(z)=(1+z)b+O(beta²). The raw distance result (B1) is

    delta D_L/Dbar_L = n.[A ell+h b],
    h=1+z-zA,
    h/A=H chi/c-z,
    d(h/A)/dz=H' chi/c.                                  (C2)

The derivative follows from chi'=c/H, so the +1 cancels the derivative of z. For flat positive dust+radiation+Lambda, H'=H0²[3Omega_m(1+z)²+4Omega_r(1+z)³]/(2H)>0; the earlier ideal two-shell [A,h] columns are distinct. That result precedes angular calibration and does not establish actual profiled rank.

Insert the same history into the **processed** chart (B2):

    W=c b,
    V_p=V_r-c ell=V_r-V_O+W,
    d=b_cal+(2V_r-V_O-V_d)/c,
    eta_r=g n.V_p+z g n.W+n.d.                            (C3)

This is the direct source equation for the existing source/operator pipeline. W is present dust velocity relative to the total-energy normal. V_p is the effective endpoint/reference combination. They are not the same estimand.

The exact response identity is

    h=1-c z g,   z g=(1-h)/c.                             (C4)

After profiling an arbitrary common angular **dipole** n.d, the z g history column is equivalent to -h/c. Replacing z by z-z_p changes it by -z_p g, hence only reparametrizes V_p. The quotient information for W is invariant under this pivot change when V_p is free.

For E(z)=H/H0=1+e1 z+O(z²), e1=(3Omega_m+4Omega_r)/2,

    A=1/z+1-e1/2+O(z),
    g=1/(cz)-(3Omega_m+4Omega_r)/(4c)+O(z/c),
    h=(3Omega_m+4Omega_r)z/4+O(z²).                       (C5)

Thus an O(W/c) constant angular term in z g is absorbed exactly by calibration; the surviving low-z history response is O(z W/c), additionally profiled against g. Near-aliasing is quantitative weak information, not automatic exact non-identifiability. In the formal pure de Sitter background g=1/(cz) and z g=1/c, so this history column is exactly calibration-degenerate; that background lacks the positive two-fluid source assumed in C1. For actual finite angular/depth support, use the actual projected design and covariance.

## D. Photon energy rest frame and the physically tied subcase

Suppose the absolute blackbody temperature in F has T(n)=T0[1+Delta_int.n] to first order. Bolometric intensity is proportional to T^4. Since photon momentum propagates along -n,

    Q_F = -4 epsilon_gamma Delta_int/3,
    beta_{R|F}=Q_F/(epsilon_gamma+p_gamma)=-Delta_int,
    Delta_CMB,O=beta_{O|F}+Delta_int=beta_{O|R}+O(beta²).     (D1)

Here R is the actual photon energy-rest frame. An intrinsic temperature dipole in F is not an additional freely specified dipole in R's energy distribution at this order. A dipole-subtracted/component-separated product is not the absolute flux distribution required by this construction. Non-blackbody spectra, higher-order effects, foregrounds and processed dipoles need their own map.

If a catalogue adopts V_r/c=Delta_CMB,O while F is an arbitrary statistical reference, (B2) gives V_eff/c=beta_S+Delta_int. Its fitted source coefficient therefore includes the chosen reference's intrinsic dipole. This is a coordinate/reference fact, not a measurement of observer speed alone.

For C1, assume additionally that the compensating radiation includes the photons defining V_r and all included radiation species share that velocity. Then Delta_int=R b and beta_O=b+ell. If the reference contract **V_r=c Delta_CMB,O** is admitted,

    V_r/c=ell+(1+R)b,
    U=(1+R)W=V_p,
    eta_r=g(z)[1+z/(1+R)] n.U+n.d.                       (D2)

The free [g V_p+z g W] model is a useful endpoint/history diagnostic; D2 is the smaller physically closed compensation subcase. The constant-g U comparator is an effective constant source/reference velocity, not proof of a pure observer boost. At large R, D2 differs from it only by the suppressed z g/(1+R) response. A 300 km/s U is **not** a 300 km/s W: W=U/(1+R). For example, the explicitly illustrative ratio Omega_r/Omega_m=3e-4 gives R=2500 and W=300/2501≈0.120 km/s; the radiation speed is approximately 300 km/s and remains small relative to c. This arithmetic example is not an adopted cosmological input or data result.

Use a fixed declared R/background grid if appropriate. Do not infer Omega_r or the photon reference from the weak shape difference, and do not claim D2 applies to CF4 solely from the `z_CMB` label. If photons and neutrinos do not share the compensating velocity, their individual momentum and reference maps must be supplied; the total-radiation density alone does not determine the photon dipole.

## E. Validity body and background transport

For the finite physical interval ending today, with z_i=a_i^-1-1 and prescribed beta_*<<1, require

    max{(1+z_i)|W|/c, R|W|/c, |V_O|/c} <= beta_*,         (E1)

in addition to the optical expansion condition. In the tied U chart,

    W=U/(1+R),
    V_O=V_r-R U/(1+R),
    ell=(V_r-U)/c,
    max{(1+z_i)|U|/[c(1+R)], R|U|/[c(1+R)],
        |V_r-R U/(1+R)|/c} <= beta_*.                     (E2)

The first term applies to the earliest declared physical interval, which may precede the largest observed z. The bound can be reported as a physical subcase validity body, not a prior secretly inserted into a nominal Gaussian tail. For the processed redshift chart, also require

    (1+z)|n.V_eff(z)|/(c z) << 1,
    V_eff(z)=V_p+z W,

plus analogous control for any intermediate heliocentric Taylor transformation if used. A numerical beta_* ceiling alone does not certify the optical Taylor remainder at z approaching zero. At fixed z_min>0, neglected endpoint/metric terms are formally higher order; their accumulated optical bound is not established by this algebra. Compensated O(beta) momentum does not cancel O(beta²) stress. Identical primordial dust/radiation velocities plus zero total momentum would force this mode to zero; independent post-decoupling initial velocities are an explicit assumption.

If the physical background includes fixed Omega_r>0 while the existing R54 experiment used Omega_r=0 at the same Omega_m, preserve flatness by setting Omega_Lambda=1-Omega_m-Omega_r. Let y_0(z) be the old source background and y_r(z)=c(1+z)chi_hat_r(z) the new one. The exact deterministic response-coordinate relation is

    eta_0=eta_r+a_bg(z),  a_bg(z)=ln[y_0(z)/y_r(z)],
    E_r²=Omega_m(1+z)³+Omega_r(1+z)^4+1-Omega_m-Omega_r,
    g_r=[(1+z)/(E_r chi_hat_r)-1]/c.                     (E3)

For the retained fixed source operator O_m and covariance C_m, either fit y_old with known offset O_m a_bg and physical design O_m[g_r n, z g_r n,...], or subtract O_m a_bg from y_old and use that same design. This is an affine re-expression of a fixed experiment. Reusing C_m is an explicit fixed-covariance conditional likelihood; it is not a recomputation of peculiar-velocity covariance in the new physical background. Changing cuts/weights/O_m defines a new experiment and needs its own covariance. A scalar depth offset can leak into apparent angular coefficients through the actual survey operator; propagate it before compression rather than assuming it is an annihilated monopole.

At fixed Omega_m and small Omega_r, E3 gives a_bg(z)=Omega_r z+O(Omega_r z²,Omega_r²) and g_r-g_0=-Omega_r/c+O(Omega_r z/c). These are low-z order checks, not an argument to discard the exact known offset.

## F. Full-covariance identified experiment and design handoff

Retain actual source directions, z values, source operator O_m, vector/tensor ordering and full C_m. For the free model use X_p=O_m[g_r n], X_W=O_m[z g_r n], and N containing O_m[n] plus the chosen KJ2/KJ3 STF source columns and any other declared nuisance. For the tied model use X_U=X_p+X_W/(1+R). A source calibration described as arbitrary common angular dipole means arbitrary three coefficients d; it does not mean an arbitrary function of n or arbitrary independent depth dipoles.

With C=LL^T, let Z=L^-1 N, P_N=I-Z Z^+, and A_p=P_N L^-1 X_p, A_W=P_N L^-1 X_W. The information on W after V_p is profiled is

    I_W|p=A_W^T[I-A_p A_p^+]A_W.                         (F1)

This treats mixed polar/STF and cross-depth covariance exactly within the fixed Gaussian design. Exact algebraic identity C4 survives O_m and these projections: the projected history column is -O_m[h n]/c modulo calibration. Near-zero singular values indicate weak responses only at their declared parameter scale and response accuracy. The quotient can be represented in an orthonormal basis of im(P_N); its covariance is then identity, whereas the ambient projected vector has covariance P_N. Singular estimator representatives do not bound unidentifiable directions.

Remaining source/reference obligations are concrete: bind actual V_r and V_d including uncertainty, specify whether CMB correction denotes the photon energy-rest frame, choose the compensating radiation content and R, declare the finite physical interval/velocity ceiling, preserve the fixed-covariance qualification, and propagate the exact background offset. R4 design can compare the free diagnostic, the tied physical subcase and constant effective-velocity response. This document does not select an observational winner or manufacture a global-tilt no-go.
