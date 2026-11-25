# R115: T1–T5 theoretical resolution and coding handoff

Theory R1–R10 only. No production code changes, no R78 promotion.
Basis: R114 HOLD specification and RESULTS_KO, exact owner pins:
htt_base 5c373cc2e7925f4569ba90c5ec6ea9152989ef6d;
BASS 4abb1d3b81a68711aa3438570f5a80f8cca42216;
REC 6ad757d232a9833e984d18657d169766b27e33a4;
REI 503508f1c82a968bebc57900d43a65135c3db185.
All four verified remote branch refs. R114 existing pytest 6 passed (2.19 s).
Native subagents not exposed; serial derivation and independent calculation paths.
No new production validation. See R114 prior C1–C6 for inherited evidence.

## T1: correct thermal/species equations

Signature (-,+,+,+), c=1 for tetrad geometry; SI reaction/thermal rates.
eta=ln(a/a_emit), H>0, beta=v/c. D_i v^i=-2 a_i v^i, A=a/H.
u_b=gamma(n+beta), Theta_b=H(3 gamma+gamma'-2 gamma A.beta).
Proper n_H'/n_H=-Theta_b/(gamma H), exact homogeneous continuity.
Fractions per H nucleus; xe=xp+xHeII+2xHeIII; chi=1+fHe+xe.
Thermal energy 3/2 nH chi kB T, pressure nH chi kB T.
Energy balance gives
 T'= -2 Theta_b T/(3 gamma H) -T xe'/chi + 2 Q_th/(3 kB nH chi gamma H).
Prefer W=chi T: W'=-2 Theta_b W/(3 gamma H)+2 Q_th/(3 kB nH gamma H).
Adiabatic W nH^(-2/3) constant, not generic T proportional to a^-2.
No standalone shear heating for a perfect isotropic gas; add actual viscous
stress or heat source when supported. Thermal and binding energy, photon
exchange enter total T_ab if active; otherwise label tracer thermochemistry.
Do not count cold Thomson bulk recoil as thermal heating.
Isotropic Kompaneets closure Q_C=4 sigma_T c n_e U_gamma kB(T_C-T_m)/(m_e c^2);
kB T_C=(1/4) integral E^4 f(1+f)/integral E^3 f.
Angle-averaged closure is not exact anisotropic polarized thermal Compton.

Hydrogen recombination flux alpha_B n_H xp xe (not xp^2).
xHeI=fHe-xHeII-xHeIII.
R1=xHeI I1-n_e xHeII alpha1; R2=xHeII I2-n_e xHeIII alpha2.
HeI,HeII,HeIII derivatives=(-R1,R1-R2,R2)/(gamma H).
Require species simplex, W>0, nuclei/charge conservation; excited-state
populations and radiative feedback, signed energy/number ledger, source coverage.
REC he_singlet.rs gives He584/IR BB, bound-free and pair point sources, not
complete helium chemistry. Use spectral occupation and correct measure,
including common material Maxwell frame; MissingAuthority remains explicit.
R114 matched reference clips total xe to X_MAX, not true xp; replace.
Existing REC 4cffa8a0 CSV contains z,xe,Tm_K,Tm_Tr_ratio; BASS 9f10e114
HYREC2 history contains z,xe,Tm. c1_visibility_hyrec.py discards Tm.
REC src/full_bianchi_hyrec/trajectory/primordial_2012_helium.py already
provides high-z species history (z,xe,xHII,xHeI,xHeII,xHeIII,Tm_K);
source-lock and verify coverage and fHe convention before reference assembly.
Use full HeIII prehistory or explicit initial state; z=1800 alone not full HeIII.
REC/REI exact join: transfer species, temperature, spectrum, nuclei; do not
carry an unqualified permanent offset across source-owner boundary.

## T2: coupled second order

delta=y-y_ref; delta'=R(y_ref+delta,Z)/(gamma H)-R_ref(y_ref,Z_ref)/H_ref.
Use matched eta-stage reference values (including W_ref). Identical physics
and zero initial difference gives zero stage residual, not an accuracy proof.
Additive matching is not necessarily inward at boundaries; reject, use
validated Saha limit or positive calibrated reaction flux, not clipping.
Joint SDIRK2 g=1-1/sqrt(2), A=[[g,0],[1-g,g]], b=(1-g,g), c=(g,1).
All geometry, photon, dust, chemistry, thermal and opacity sources use
same stage. beta'=(I-beta beta^T)p'/gamma, not lagged endpoint difference.
Converge stage solve to preserve O(h^3) LTE. Split at reference/model joins,
keep predictor and accepted history separate. Alternative Strang chemistry
half, BASS full, chemistry half, freeze explicit time at midpoint for smooth
nonautonomous operators, second-order subsolvers. L-stable SDIRK2 not exactly
time reversible; stiffness/order reduction and positivity checked separately.
Manufactured stiff model in THEORY_CHECKS.json is not Bianchi production.

## T3: exact grid-free finite bulk tilt cold Thomson

D=gamma(1-beta.e); I_u=D^4 J I_n J^T, dOmega_u=D^-2 dOmega_n.
S=M I_n=integral D^2 J I_n J^T dOmega_n. Rest gain=3/(8pi) P_u S P_u.
C_n=kappa_eta(G M-D) I_n; G=D^-3 inverse-screen transform of rest gain.
Gain rank <=6 (real symmetric coherency), NOT finite output bandwidth.
Loss acts at all l. Align boost z, meridian screen no extra phase.
mu'=(mu-beta)/(1-beta mu), spin s=0,+/-2, j0=max(|m|,|s|).
Spin harmonic endpoint factors (1-mu)^(|m+s|/2)(1+mu)^(|m-s|/2)
times Jacobi polynomial degree j-j0. Pullback has denominator
(1-beta mu)^j. D^2 cancels for j<=2, leaving polynomial degree <=2-j0.
Thus M depends exactly on normal l<=2 for bolometric intensity.
G output has denominator power j+3, all l. Wigner rotation handles arbitrary
orientation. Exact projection via Euler beta-hypergeometric integral
 integral_0^1 t^(p-1)(1-t)^(q-1)(1-r t)^(-k) dt
 = B(p,q) 2F1(k,p;p+q;r), r=2beta/(1+beta).
At high l/beta use stable recurrences, not cancellation-prone polynomial
coefficients. Optional Taylor bound for D^-4 alone, gamma exact:
 gamma^-4 binom(K+4,3) beta^(K+1)/(1-beta)^(K+5).
Not a full collision error bound; no need for small-beta gate in exact route.
Pole is algebraic, not essential.
Galerkin C_L=P_L C P_L: loss tridiagonal fixed m, rank-six gain Woodbury.
Preferred continuum cell for ray replay: R=(1+d D)^-1,
 f1=R(f0+d G S1), S1=(I-d M R G)^-1 M R f0.
d is bare proper depth. Positive map d M R G contracts trace norm by
max dD/(1+dD)<1 (continuum angular integral normalization), hence invertible.
Rational integrals have poles 1-beta mu and 1+d gamma(1-beta mu).
SDIRK2 second input f0+((1-g)/g)(f1-f0); retain full rational f1 until
final projection. Do not conflate projected generator resolvent and
projected continuum resolvent. Continuum gain_map=identity; refined
quadrature limit comparison, not bitwise old grid equality.
Integral D tr(C_n) dOmega=0 implies Delta E=beta.Delta q. Discrete
recoil beta=(p0+p1)/(gamma0+gamma1), p1=p0-Delta q/M gives opposite
material energy change. L>=1 retains low energy/momentum, L>=2 M.
Projection can violate PSD; BE continuum positive, SDIRK not guaranteed.
Adaptive L/reject; separate replay, time/angular convergence and PSD gates.

## T4: exact cold Thomson spectral moment carriers

Matrix measure F(nu,e)=integral dP_e(xi) n_Pl(nu,T_* exp xi), xi=ln(T/T_*),
positive screen measure for Planck-mixture IC; elastic scattering and
geodesic shift preserve cone. Fixed T_*; R=d ln E/deta.
Raw log moments M_k=integral xi^k dP evolve with k R M_(k-1), screen
congruence and material collision; boost binomial log-D shift. Closed
lower-order hierarchy under cold Thomson only. Exact Mellin carriers
B_p=integral exp(p xi)dP evolve with pR, boost D^p; p=3 number, p=4 energy.
General p gain rank six but input not necessarily low-l; p=4 special.
Proposed integral nu^3(nu partial_nu)^2 f=16 integral nu^3 f (boundary decay);
not independent y carrier. Keep full coherency including trace.
For scalar normalized measure variance v=Var(xi), y=v/2 leading order.
Doppler shift preserves central variance; mixing adds nonnegative increment
relative to weighted incoming variances, not always relative to old ray.
Jensen B4>=B3^(4/3); y_M=(ln B4-4/3 ln B3)/4>=0, y_M=v/2+higher cumulants.
D_T=T partial_T; at log-mean n=nPl+y D_T^2 nPl+O(E|delta xi|^3).
At number temperature shape D_T^2-3D_T, at bolo T D_T^2-4D_T.
Wien correction at bolo temperature y(x^2-5x) exp(-x), x=E/kB T_B.
Linear rate functional same derivative, remainder bounded by third absolute
central moment times sup third derivative/6 on known support (log mean).
Equal B4 and v do not determine Wien rate (checked counterexample).
Exact atomic rates use spectral occupation and cross sections, not Planck
fit with ad hoc y substitution. Thermal Compton and atomic line/emission
break pure mixture closure; frequency-resolved occupation and conservative
energy/number flux ledger needed. Detector/bandpass conversion is separate.

## T5: native transfer ownership

sky_spectrum.rs documents BOTH HEALPix E=-E_Dossier and B=-B_Dossier;
native already HEALPix, no double flip. Outward s=-e, theta same, phi flips,
U flips. Full signed modes (L+1)^2, reality a_l,-m=(-1)^m conj(a_lm),
m0 real, spin l<2 zero. Packed m>=0 is storage only; no sqrt2 rescale.
C_l use 2 Re for m>0; TE/TB flip under convention, EB unchanged.
SO(3) rotate N,Sigma,A,R,matter/observer and screen basis together; a_l
transforms by Wigner unitary, C_l invariant, C_lm frame-dependent.
h only applicable strata; type IV no ill-defined h. Existing AtlasEntryLite
metadata-only, explicitly rejects native value-bearing and inference input.
New typed NativeRustLieSkyArtifact + adapter, proposed distinct
TRANSFER_CONDITIONAL_NATIVE_RUST_TEMPLATE tier. Record exact source/binary/
input/output hashes, units, frame, route, ell_max, IC/constraints, solver
and owner history, convergence scope; authorize deterministic synthesis and
registered projection only. Reuse signed-mode parsing from commander_native.
Do not change legacy near-FLRW, STRONG_FAMILIES or R78 science gates.
Separate physical signed x (tensor/alm), Q only if physical metric/scale;
Pi,F,G_F absent without qualified null, measure and transport. Native
deterministic template not ensemble covariance, likelihood or attribution.

## R8–R10 decision

T1 derived thermal/species skeleton; full source-qualified helium and
thermal coupling still open. T2 derived, manufactured convergence checked;
production convergence pending. T3 exact analytic operator derived and
coefficient checked; production high-l stability/recoil/PSD pending.
T4 exact cold moment transport derived, insufficiency counterexample checked;
frequency-resolved microphysics open. T5 contract ready, current guards pass;
adapter implementation pending. No claim of full blocker implementation.
Next: R116-NATIVE-COLD-THOMSON-HARMONIC-EXACT-01 (continuum rational cell,
6x6 solve, strong-tilt/off-axis, replay, angular/time refinement, positivity).
Parallel: R116-REC-SPECIES-THERMAL-01; then coupled SDIRK2, spectral and HTT
native dispatch. Do not gate bounded bolometric collision on full spectral REC.
References: https://arxiv.org/abs/1011.3758; https://doi.org/10.1103/PhysRevD.82.063521;
https://arxiv.org/html/1110.0247v2; https://doi.org/10.1103/PhysRevD.89.123504;
https://arxiv.org/abs/astro-ph/0703541; https://doi.org/10.1088/1475-7516/2010/07/019.
