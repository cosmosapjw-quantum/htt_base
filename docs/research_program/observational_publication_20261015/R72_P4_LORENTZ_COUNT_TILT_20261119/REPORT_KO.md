# R72 / P4 · Radio dipole–observer boost–global tilt: physical five-view theory R1–R10

2026-11-19 KST. Research branch \`research/r69-observable-physics-bridges-20261118\`. Initial HEAD \`34fb4fcac2d26bdfa5aea1ac890e15c4db770402\`. Original R63/R65 data, R69/R70/R71 theory and six-paper/42 science DAG remain unchanged. Focus = **fourth P4 paper**, whose two scientific axes are radio/source counts (R65) and local observer boost vs global matter–radiation tilt (R63). Boundaries: source-specific theoretical derivation + actual retained data geometry/readout; NOT a new CMB/radio excess detection, kinematic velocity posterior, Bianchi family or tilt claim.

## Primary conclusions

**1. Physical Lorentz-count tensor depends on TWO selection responses, not one.** For isotropic rest-frame unresolved radio point sources, a fixed spectral index \(S_\nu\propto\nu^{-\alpha}\), sharp flux interval \([L,U]\), and boost Doppler \(\delta=[\gamma(1-\beta\cdot n)]^{-1}\),
\[
\mathcal N'(n)=\delta^2\int_{L\delta^{-(1+\alpha)}}^{U\delta^{-(1+\alpha)}}g(S)dS .
\]
Set \(t=\log\delta\), \(k=d_t\ln\mathcal N|_0\), \(\kappa=d_t^2\ln\mathcal N|_0\). Then the count-density dipole and signed STF quadrupole are, to second order:
\[
\boxed{d_i=k\beta_i,\qquad Q_{ij}^{\rm count}=\frac{k^2+k+\kappa}{2}\beta_{\langle i}\beta_{j\rangle}
=\frac{k^2+k+\kappa}{2k^2}d_{\langle i}d_{j\rangle},\ (k\ne0).}
\]
The log-count quadrupole is instead \((k+\kappa)\mathrm{STF}(\beta\beta)/2\). A pure powerlaw count population gives \(\kappa=0,k=2+x(1+\alpha)\); heterogeneous populations and finite bins can give \(\kappa\ne0\), so an Ellis–Baldwin \(k\) alone does NOT calibrate quadrupole morphology.

**2. Positive mixture closure counterexample.** Pure \(k=4,\kappa=0\) and equal mixture \(k_1=3,k_2=5\) with effective \(k=4,\kappa=1\) have the same first-order dipole \(d=4\beta\) for the same observer. Yet the physical count STF coefficients are 10 versus 10.5 times \(\mathrm{STF}(\beta\beta)\). Exact finite-bin mixtures [20,80] with \(\alpha=0.75\) give a Legendre \(\ell=2\) coefficient at \(\beta=369.82/299792.458\) of \(1.01449031\times10^{-5}\) (pure) and \(1.06521497\times10^{-5}\) (mixture). This is derived and checked, not independent radio observation.

**3. Pure-boost geometry and hemisphere parity.** A positive \(Q=A\mathrm{STF}(\beta\beta)\) has signed shape \(\chi=+1\) and intrinsic positive-quadrupole solid-angle \(F_{\Omega,2}=1-1/\sqrt3=0.42265\). Amplitude can evolve without changing either description. Full round-sky antipodal hemispheres have no even-quadrupole mean-density difference. With a real sky mask,
\[
\Delta_{\rm mask}^{(2)}=Q:(M_+-M_-)_{\rm STF},\qquad
|\Delta_{\rm mask}^{(2)}|\le\|Q\|_F\|M_+-M_-\|_F.
\]
This is *morphological explanatory geometry*, not extra likelihood or physical \(G_F\).

**4. Exact flux-bin transverse separation and its practical failure.** For R65 count carrier \(v_b^\perp=k_b\beta_\perp+a_\perp+\epsilon_b\) with covariance C, the physical common beta/residual profile Fisher is
\[
\mathcal I_{\beta|a}=D^T[C^{-1}-C^{-1}H(H^TC^{-1}H)^{-1}H^TC^{-1}]D,\quad
D=(k_b)\otimes I_2,\ H=\mathbf1\otimes I_2 .
\]
Formally rank2 iff k_b vary. Actual R65 k=(3.35802935,3.52179743,4.13330545) at *assumed* spectral α=.75 gives four algebraic parameters, but \(\beta_\perp\) conditional SD~(.010367,.011715), vastly larger than β_CMB~.001234 and nearly degenerate with common residual. Declination-ring normalization makes the equatorial z component an exact null in the log-link first-order model; physical nonlinear \(1+d\cdot n\) may weakly identify it beyond first order. No general velocity no-go is claimed.

**5. Local observer boost is not physical matter–radiation tilt.** \(\Gamma_{MR}=-g(U_M,U_R)/c^2\) is a local invariant; a radio dipole \(d_b=k_b\beta_{O|S}+u_b\) is observer/flux/selection-dependent. One radio dipole admits distinct observer boosts and intrinsic source patterns with different \(\Gamma_{MR}\). Rest-isotropic radiation boosted into the *electron frame* has \(m_\gamma=4\beta_{R|M}/(3+\beta^2)\) and \(S_\gamma=4\mathrm{STF}(\beta\beta)/(3+\beta^2)\), with β the **radiation velocity seen by electrons**, not our observer boost. These electron-frame moments and remote kSZ may reduce degeneracy if source transfer is available. This relation is valid in any local spacetime; Bianchi Class A/B Lie \(Na=0\), normal Codazzi and Einstein matter evolution determine whether a proposed global history is a solution. Non-tilted Type I is NOT presumed.

## Actual radio/Cosmology results, exactly scoped

The R65 mask is the actual 33,000 pixel NSIDE64 selected NVSS footprint (~67.14% sky), 185 declination rings, used read-only. Original sourceward CMB direction Galactic (264.021°,48.253°) is ICRS (RA~167.941903°, Dec~−6.944260°). CMB-hemisphere retained pixel counts are 16,799/16,201. A unit STF template \(q=(n\cdot p)^2-1/3\) leaks \(-0.02010943263\) into masked hemisphere mean difference, with \(\|M_+-M_-\|_F=0.16820549\). A purely **injected** boost quadrupole from historical illustrative k≈3.82543 and β_CMB has coefficient \(1.40451\times10^{-5}\) and resulting masked even→odd hemisphere mean leakage only \(-2.82439\times10^{-7}\). This is not a measured astrophysical quadrupole or bound on total selection/LSS residual.

The actual R65 observed peak-proxy bins [20,40],[40,80],[80,∞] mJy/beam contain 115,906 / 65,260 / 55,581 selected components in this mask. Raw CMB hemispherical count fractions = 0.511984 / 0.512795 / 0.511344, whereas equal-area selected pixel fraction = 0.509061. Raw fractions are **not** the intrinsic cosmic hemisphere occupancy nor source-conditioned Poisson significance.

The actual same-provider *integrated-minus-peak* selected transverse coefficient difference is \((-0.0016440241,+0.0055246718)\). Registered source overlap is 241,892 components (integrated selection 263,158). Correct shared-source Poisson influence covariance produces conditional Wald 30.98947; incorrectly independent covariance produces 1.31544. Neither figure is a physical global cosmological anomaly p-value, and difference alone does not identify instrument bias versus source population/morphology selection.

The R63 restricted compensated matter–radiation tilt versus constant bulk CF4 working comparison uses 35,970 selected groups, retained same-source 32D and a fixed mean/covariance family; its computed max power 0.100000418731 at size 0.1 is *not* a universal global tilt exclusion. The distinct physical route is remote electron-frame photon dipole/kSZ with an actually matched Thomson/optical redshift source, not a second look at the same CF4 catalogue.

## Six-paper / seven-combination physical transfer

Each original P1–P6 track and PHY-01..07 conditional research combination is preserved **with exact equations, reference frames, x/Q/Pi/F/G_F definitions, source requirements and blocker** in APPLICATIONS.json. Main physical connectivities:
- P1: optical signed STF is not a radio count STF without complete source/frame transfer.
- P2: photon rest-isotropic Lorentz stress and radio count STF share a rank-one axis only if the same relative β is physically established; radio-to-photon coefficient involves \((k^2+k+\kappa)\).
- P3: distance-derived H_D requires joint Doppler/aberration/redshift transform, not substitution of d_radio/k into local Hcal.
- P4: source-selected radio dipole and \(\Gamma_{MR}\) require distinct tests; use actual count flux response.
- P5: general Bianchi Lie, total normal tilted momentum and optical source are not our local observer boost.
- P6: Gaia E1/E2/B1/B2 vector-harmonic information is frame/physical-source dependent; do not identify it with radio scalar low-ell without actual transfer.
The seven PHY bridges cover Hubble hemispheres, photon–GR–Bianchi moments, pure-boost CMB stress, Gaia/observer sky drift, Bianchi normal momentum, shared fossil tensor with kinetic closure, and radio–CF4 odd/even mask coupling. They are **not seven independent observed fits**.

## Five-view scientific interpretation

\(x\) is full signed R65 selected source carrier with joint covariance and source/flux/mask metadata; \(Q_\mathrm{stat}\) is a working coefficient/null ellipsoid gauge while physical \(Q_\mathrm{caus}=|\beta|\) requires an identified **3D physical source-rest-frame velocity**; \(\Pi\) is a working ring-conditioned multinomial/Poisson or explicitly fixed Gaussian tail, NOT a cosmological truth probability; \(F\) is a specified finite selected-count event with sky/exposure measure, or (if only geometry is relevant) a clearly auxiliary signed STF shape/solid-angle area; physical \(G_F\) requires a matched population time/redshift transport and is not peak→integrated or a flux-threshold shift. The statistics cannot increase information beyond their source likelihood.

## Verification and limits

SymPy and independent Wolfram symbolic expansions matched T1 exactly to β². Original R65 full source geometry and R63/R65 published manifest readout reproduced with matched keys; finite-bin quadrature and positive mixture counterexample passed, mask tensor/H+ parity contraction passed, cross-source covariance and Wald reproduced, synthetic Schur rank/coefficients verified. Existing focused R63/R65 57 tests PASSED. Reproducible source script: verify_p4.py; exact output: RESULTS.json. The parent performed one bounded adversarial review; native subagents unavailable. No full 4-axis CAS PASS, no raw radio refit, no empirical LSS simulation, no cosmological p-value, no observer β posterior, no Bianchi global Einstein-Boltzmann solution and no independent scientific refereeing.

**R8 convergence:** The most useful immediate source-specific empirical task is calibrating k_b,κ_b and beam/morphology/spectral response for **the same provider source IDs** under both peak and integrated selection, propagating artificial boost through original R65 ring mask, and comparing source-matched paired covariance and heldout transitions. Separate physically remote kSZ is the path to observer-vs-global-tilt source separation. If data missing, report conditional effect, not strong impossible/no-go. Publication decision P4 remains NOT_READY_TO_SUBMIT; original 42 science nodes untouched.

**R1–R10:** R1 contract, R2 source/literature, R3 frames/view types, R4 seven divergent physics routes, R5 five constructive results, R6 adversarial restrictions, R7 symbolic/actual NVSS/CMB/CF4 finite checks, R8 convergent scientific decisions, R9 six-paper/seven-bridge formalism, R10 frozen Git/provenance/handoff. Each substantive stage committed and pushed on the existing research branch. Native subagent NOT_RUN. Do not auto-launch coding or next fifth paper loop.
