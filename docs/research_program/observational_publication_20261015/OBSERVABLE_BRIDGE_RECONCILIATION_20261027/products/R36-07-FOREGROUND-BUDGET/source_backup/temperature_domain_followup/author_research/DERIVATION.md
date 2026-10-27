# Same R36-07 issue: passive dust, temperature coordinates and survival

This is a bounded theoretical continuation by `/root/r36_foreground_fresh_review`, requested gpt-6-astra/xhigh, observed runtime UNKNOWN. It is newly authored research requiring a different independent reviewer. The fifteen-source research and its review remain frozen. Nothing here qualifies the original free-complex R31 class, changes the actual seven-band tensors or reruns native maps/noise. Physical R36-07 acceptance remains false.

## Physics/math audit verdict

A CMB temperature floor is justified for an explicitly comoving, passive radiative-equilibrium class. The corresponding observer-frame floor is not universal under unrestricted velocities. A positive justified observer-frame floor removes the previous cold-MBB counterexample and permits a finite direct nonlinear foreground-response bound, conditional on the still-missing absolute source and native response certificates. It does not bound the original linear-temperature and squared-temperature moments. A bounded inverse-temperature coordinate cannot remove these poles by relabelling them. A material- and lifetime-specific survival condition, or a separate temperature-moment tail inequality, can supply the missing control; neither is currently calibrated for the whole admitted sky.

## 1. Temperature floor, rest frame and observed frame

Let a grain have a nonnegative absorption cross section C_abs(nu,n), obey Kirchhoff's law, have a well-defined equilibrium temperature, and have no additional cooling sink. Extra heating is nonnegative. For an isotropic CMB bath at temperature T_gamma,

    integral C_abs [B_nu(T_d)-B_nu(T_gamma)] dnu dOmega = H_extra >= 0.

Since B_nu(T) increases strictly with T, and the grain couples on a set of nonzero measure, T_d<T_gamma is impossible. This does not require a global power-law opacity. It excludes stochastic-temperature grains, transient cooling and actively refrigerated or evaporatively cooled states from this exact equilibrium statement. These can be separately modelled; they are not automatically covered by the floor.

For a comoving source in the stated cosmological class, T_gamma(z)=T_CMB0(1+z), and the observed modified-blackbody color temperature is T_obs=T_d/(1+z). Consequently T_obs>=T_CMB0. The usual modified-blackbody equilibrium expression in da Cunha et al. (2013), equations 6 and 12, illustrates this. Their power-law bolometric integral requires convergence (beta>-3); the monotonicity proof above does not assume a power law to zero or infinite frequency. This is physical input defining a conditional emitter class, not an observed LOS-temperature distribution.

Kinematics must remain explicit. Write D=nu_CMBframe/nu_grainrest for the outgoing ray, with D in [D_min,D_max], D_min=1/[gamma(1+v/c)], D_max=1/D_min. Then

    T_obs = D T_rest/(1+z_cos).

The CMB is anisotropic in the grain frame. Every directional bath temperature is at least D_min T_CMB0(1+z_cos), so equilibrium gives the conservative lower bound

    T_obs >= D_min^2 T_CMB0 = [(1-v/c)/(1+v/c)] T_CMB0.

A declared speed ceiling v<=v_max<c therefore gives a strictly positive uniform floor. For example v_max/c=0.01 gives 2.67152970297 K; this is an illustrative conditional ceiling, not a velocity measurement. Any additional source-to-observer redshift or observer boost must be included rather than hidden in z_cos.

There is an explicit passive counterexample to a blanket observer-frame 2.7255 K floor. A grey grain moving through isotropic CMB has radiation energy density U'=gamma^2(1+(v/c)^2/3) U. In radiative equilibrium,

    T_rest/T_gamma = [gamma^2(1+(v/c)^2/3)]^(1/4).

Observed along the maximally receding ray,

    T_obs/T_CMB0 = [gamma^2(1+(v/c)^2/3)]^(1/4)/[gamma(1+v/c)].

This is already below one for nonzero velocity and tends to zero like gamma^(-1/2). The reproducer gives 1.72509 K at v/c=0.5 and 0.174148 K at v/c=0.9999. These are a conditional grey-grain calculation, not a proposed population of relativistic Galactic dust. The result explains why a kinematic class matters without blocking the ordinary comoving/nonrelativistic class.

Polarization transport remains tensorial. The spectral coherency matrix transforms as a positive frequency-cubed factor times a basis rotation of the rest-frame matrix, evaluated at the aberrated direction and Doppler-shifted frequency. Equivalently Q+iU carries the spin-basis phase and the same frequency-cubed factor. The angular Jacobian and all induced multipole mixing belong in the full native operator; a scalar temperature correction does not replace this transport. Challinor and van Leeuwen (2002), equations 1-5 and section III, give the applicable intensity and polarization transformation laws.

## 2. Exact inverse-temperature parametrization

Fix a positive observer-frame floor T_f. Set u=1/T, 0<u<=1/T_f; u=0 denotes the continuous infinite-temperature spectral limit, not a finite-temperature atom that is assigned zero old moments. For dust reference frequency nu_d=353 GHz and emissivity index beta,

    S_nu(beta,u) = (nu/nu_d)^(beta+3) expm1(a_d u)/expm1(a_nu u)
                 = r^(beta+2) g_nu(u),
    a_nu=h nu/k, r=nu/nu_d,
    g_nu(u)=f(a_d u)/f(a_nu u),  f(x)=expm1(x)/x, f(0)=1.

On every finite positive-frequency band, g is positive and continuous on the compact u interval, including g(0)=1. More specifically, q(x)=x/(1-exp(-x))-1 increases for x>0, since q'(x)=[1-exp(-x)-x exp(-x)]/[1-exp(-x)]^2>0. Therefore d log g/du=[q(a_d u)-q(a_nu u)]/u has a fixed sign. Exact uniform bounds are

    g_min(nu)=min(1,g_nu(1/T_f)),
    g_max(nu)=max(1,g_nu(1/T_f)).

No numerical minimization over T or finite-T grid proves these bounds; the derivative argument does. This removes the T->0 concentration witness once T_f is justified. It does not require a finite T_max.

For beta0=1.5 and delta=beta-beta0, a positive source passband has the pointwise lower envelope

    H_j(beta,u) >= b_d/N_j integral R_j(nu) r^(beta0+2) g_min(nu) exp[delta log r] dnu
                >= m_j exp(tbar_j delta),

where b_d=dB_nu_d(T_CMB0)/dT, m_j is the integral at delta=0, and tbar_j is its normalized mean log r. The second step is Jensen. This is uniform in arbitrary beta-temperature correlations. For two source means bracketing nu_d, define a=-tbar_minus>0, b=tbar_plus>0 and calibrated J_minus,J_plus as in the preceding research. Then all beta moments and all finite nonnegative inverse-temperature powers obey

    M_k=int |delta|^k dmu <= (k/(e a))^k J_minus+(k/(e b))^k J_plus, k>=1,
    M_0 <= J_minus^[b/(a+b)] J_plus^[a/(a+b)],
    int |delta|^k u^l dmu <= T_f^(-l) M_k.

The measure is the full positive reference-intensity measure; the complex polarized measure satisfies |deta|<=dmu. These inequalities control all corresponding complex vector/tensor moments, not just one scalar projection.

Using T_f=2.7255 K and the cached DIRBE passband gives m_plus=0.15768847104209432 MJy/sr per K_CMB353 and b=0.8974383525556258. These are lower-response table calculations under the declared interpolant, not calibrated map-to-sky lower certificates. The associated sufficient Jensen frequency interval is [0.408 GHz, approximately 866 GHz] when the lower source is treated as monochromatic Haslam; actual source/target passband qualification remains separate. Reusing the old raw map sums with the deliberately idealized kappa=1, exact-calibration assumptions gives a very loose dust-reference mass envelope of 6892.912812 K_CMB353 sr. This demonstrates finiteness of the conditional construction; it is not a measured budget.

## 3. Direct nonlinear bound preserves the full native functional

For t=log(nu/nu_d) within [-a,b], Holder gives E(t)=J_minus^[(b-t)/(a+b)] J_plus^[(a+t)/(a+b)]. Hence

    int S_nu(beta,u) dmu <= r^(beta0+2) g_max(nu) E(t).

A target passband integrates this inequality with its actual positive spectral kernel and normalization. Spectral response outside this sufficient interval, signed response portions, or other components require their own domination terms; they are not zero-filled. For monochromatic brackets an equivalent direct expression is

    S_nu = C_nu(T) S_nuL^theta S_nuH^(1-theta),
    theta=log(nuH/nu)/log(nuH/nuL),
    C_nu(T)=B_nu(T)/[B_nuL(T)^theta B_nuH(T)^(1-theta)].

The beta dependence cancels exactly. A simple rigorous, though loose, all-T>=T_f bound is

    C_nu(T) <= exp{[theta h nuL+(1-theta)h nuH]/(k T_f)},

from RJ_nu*T*exp[-h nu/(k T_f)] <= B_nu(T) <= RJ_nu*T. The reproducer checks this against finite samples; the analytic inequalities give the domain-wide guarantee.

Let A(theta) be the actual stacked native response mapping two real polarization components into all 7x24 real coefficients, including bandpasses, beams, masks, rotations/aberration and thermodynamic conversion. For any direction v in this full output space,

    |v^T Y_fg| <= int ||A(theta)^T v||_2 dmu(theta).

A positive source dual satisfying ||A(theta)^T v||_2 <= sum_j q_j(v) R_j(theta) bounds that support. The collection for every v defines a full-vector bound; choosing one v alone does not. Alternatively ||A(theta)||op <= sum q_j R_j(theta) directly yields ||Y_fg||_2<=sum q_j Z_j. No original polarization coordinate is removed. A conservative operator-norm envelope may be loose, but it still retains the entire functional. The existing native response certificates are not supplied by this theorem.

The coordinate change u=1/T is exact if the entire nonlinear S and its pushforward measure are retained. A truncated u expansion is a different finite approximation with a new coefficient matrix, metric and remainder. It cannot be substituted into the old R31/R32 F,D objects as if they were unchanged. Temperature-class restrictions, such as radiative equilibrium or a survival condition, also narrow the original free-complex nuisance class; they must be explicit conditions of a new physical subset.

Near the CMB floor, a physically complete transfer model can involve B_nu(T)-B_nu(T_CMB) rather than intrinsic B_nu(T): equilibrium dust emits and absorbs the background. In the comoving case the contrast is nonnegative and vanishes at equality. Replacing the old B-based family with this contrast family is not an exact coordinate relabeling. A direct native response can retain the emission/absorption terms explicitly or bound their remainder, with coherency matrices and background transport intact. No inferred dust mass or intrinsic moment is claimed from a vanishing contrast.

## 4. Why the original nine moments still need temperature-tail control

The original temperature coordinate is t_d=(T-20 K)/(20 K). In the u chart,

    t_d=(1/(20 K u))-1,

so the original t_d, delta*t_d and t_d^2/2 weights have poles at u=0. Bounded u moments cannot bound these reciprocal moments. Take fixed beta and a fixed nonzero complex polarization atom at a sky location. Let its reference amplitude be fixed and T_n->infinity. All finite-band MBB responses converge, and the 24-vector response is preserved. In the common harmonic example the atom's vector norm is sqrt(3/pi) times its amplitude, so ||U_t|| grows linearly with T_n and ||U_tt|| quadratically. The reproducer records this full-vector witness. The original temperature-free dust rows and all bounded-u rows may stay finite simultaneously.

For all nine original coordinates, the three synchrotron rows can use the previous synchrotron envelope. The six dust rows, in order A, delta_beta, t_d, delta_beta^2/2, delta_beta*t_d, t_d^2/2, need a finite M_t2=int t_d^2 dmu in addition to M0,M1,M2 for delta_beta. Then the respective total-variation row bounds are

    [M0, M1, sqrt(M0*M_t2), M2/2, sqrt(M2*M_t2), M_t2/2].

The mixed bound is Cauchy-Schwarz for the same positive measure and permits arbitrary beta-temperature correlation. Multiplying each by the full harmonic/operator norm and applying the unchanged diagonal D gives a conservative Frobenius bound on the whole old tensor. This is a conditional formula, not permission to fill absent dust rows with zero.

A finite T_max is sufficient: with t_abs=max(|T_f-20|,|T_max-20|)/20, M_t2<=t_abs^2 M0. It is not necessary. A separately justified B2=int T^2 dmu suffices via M_t2<=B2/(20 K)^2+M0. These alternatives state exactly which tail quantity is missing.

## 5. Source-grounded conditional survival ceiling

Waxman and Draine (2000), equations 10-12, use the approximate thermal erosion law

    da/dtau = -v0 exp[-B_K/T_rest],
    v0=nu_attempt (m/rho)^(1/3).

Their representative refractory values are nu_attempt=10^15 s^-1, rho/m=10^23 cm^-3 and B_K=7x10^4 K. Suppose a material class has initial radius <=a_max, no accretion/replenishment, and approximately constant rest temperature for at least tau_min. Survival requires

    v0 tau_min exp[-B_K/T_rest] < a_max,
    T_rest < B_K/log(v0 tau_min/a_max),

when the logarithm is positive. A rigorous class bound would use validated v0>=v_min and B_K<=B_max, replacing the RHS with B_max/log(v_min tau_min/a_max). Doppler/redshift factors then convert the rest ceiling to the observed one. It is a material/lifetime/kinematics condition, not a fitted LOS rectangle.

For the representative rate model and a_max=0.1 micrometre, the limiting rest temperatures are 2280.046 K for 10 s, 1760.329 K for one day, 1532.873 K for one year, and 1176.839 K for one million years. These are conditional numerical examples from the approximate rate equation. They are not certified universal thresholds, and adopting size, duration, pressure and parameter bounds for the actual foreground remains a physical-class decision.

Kama, Min and Dominik (2009), section 3.2, explicitly model sublimation as a function of material and vapour partial pressure. Their analysis prevents treating a customary 1500 K value as a universal ceiling. Accretion can balance evaporation, large grains last longer, and transiently heated grains need not share a steady temperature. The primary sources therefore provide a defensible route to a conditional material class, but do not by themselves bound every emitter along the observed LOS.

For varying temperature, survival alone gives only

    integral exp[-B_max/T(tau)] d tau <= a_max/v_min.

It does not control every instantaneous maximum or a T^2 occupation moment: increasingly brief arbitrarily hot spikes can satisfy erosion while their squared-temperature integral grows. The reproducer gives an explicit sequence with hot dwell proportional to 1/T and verifies the erosion inequality without integrating an ODE. A population-level intensity-weighted tail needs an additional heating-energy/duty-cycle/size/opacity condition; grain lifetime alone does not manufacture it. A stationary sky population across epochs does not establish that individual grains survive the same interval, because replenishment can maintain a steady population.

A noncompact alternative is physically interpretable when an actual heating/bolometric-intensity bound and an opacity class are supplied. For an ideal grey class, reference intensity A at nu_d has

    R_bol(T)=[sigma_SB T^4/pi]/B_nu_d(T)
             >= [sigma_SB c^2/(2 pi k nu_d^2)] T^3 := C3 T^3,

using the RJ upper bound. If a genuine positive bolometric functional E_bol bounds b_d int R_bol(T) dmu, then int T^3 dmu<=E_bol/(b_d C3), and Holder gives

    int T^2 dmu <= [E_bol/(b_d C3)]^(2/3) M0^(1/3).

More general material envelopes can replace the grey condition. This is an explicit noncompact tail mechanism; the one DIRBE band is not a bolometric bound and is not used as one. No arbitrary opacity extrapolation or universal thermal ceiling follows from the acquired maps.

## Equation audit and outcome

| Question | Answer | Remaining condition |
|---|---|---|
| CMB floor for comoving radiative equilibrium | Yes, T_obs>=T_CMB0 | Positive absorption, Kirchhoff equilibrium, no extra cooling sink, cosmological frame stated |
| Same floor for unrestricted moving grains | No; explicit grey-grain counterexample | A declared kinematic bound gives a weaker positive floor |
| Positive floor removes cold-MBB concentration | Yes within that conditional class | Actual intrinsic/contrast transfer and frame must be retained |
| Inverse-temperature/direct native formulation finite | Yes conditionally via positive source domination | Calibrated aggregate source response, full target operator, spectral class |
| Inverse-temperature bounds every old nine-moment coordinate | No | Old reciprocal-u temperature moments need T_max or a T^2 tail bound |
| Grain physics supplies a universal 1500 K cutoff | No | Material, pressure, size, duration, replenishment and parameter uncertainty |
| Conditional physical survival/tail route exists | Yes, explicit equations and finite examples above | Actual class/population or bolometric payload still absent |
| Operational physical lower-tier contract now possible | No | Source aggregate flux-loss and native certificates are still absent; whole-sky survival/tail class not specified |

The next executable physical checkpoint remains on the same R36-07 issue: supply the calibrated source upper/aggregate response certificate and choose either (A) a supported observer-temperature floor plus the direct nonlinear full-vector formulation, or (B) additionally a material/lifetime T_max or intensity-weighted T^2 tail bound to retain all nine old moments. Freeze that actual payload for lower-tier integration without rerunning completed native maps/noise. The conditional theorem and numeric witnesses can be reviewed now. Original free-complex unboundedness and all acceptance HOLD states are unchanged.

## Primary references and reproducibility

* [da Cunha et al. 2013](https://arxiv.org/abs/1302.0844), equilibrium equations 6, 12 and CMB contrast equation 18.
* [Challinor and van Leeuwen 2002](https://arxiv.org/abs/astro-ph/0112457), Doppler/aberration and full polarization transport.
* [Waxman and Draine 2000](https://arxiv.org/abs/astro-ph/9909020), erosion and survival equations 10-12.
* [Kama, Min and Dominik 2009](https://arxiv.org/abs/0908.1692), section 3.2 and material/pressure dependence.

Three new primary PDFs are retained in this subdirectory's source intake; the kinematic paper was inspected through the web tool. Cached DIRBE response and prior map statistics are read only. `reproduce.py` generates `NUMERIC_WITNESSES.json` and preserves run stdout/stderr. The numerical checks illustrate and falsify finite cases; the displayed analytic inequalities, rather than a numerical grid, establish the stated conditional domains. No formal four-axis or independent review status is asserted by this author.
