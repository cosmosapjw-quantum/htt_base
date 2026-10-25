# R32-07-P5-ALGEBRA: frozen scientific build contract

External preparation only for campaign R23-whole-42-solver-free. Requested Astra/xhigh; observed runtime UNKNOWN. This is a complete analytic source/implementation contract, not a formal execution packet, independent acceptance, product or original42 completion. All retained inputs are bound in P5_SOURCE_IDENTITIES.json. No repository, Git or campaign-state mutation occurred in this preparation.

## Product and exact scope decision

Build an English solver-free algebraic note with an LRS Bianchi-V **instantaneous constraint region**, plus a separately labelled Bianchi-I **kinematic radiation equivalence example**. They answer different questions. The latter supplies the retained source's exact same-observable/different-history example; it is not a pair of Bianchi-V or specified Einstein-perfect-fluid histories. The formal scientific author must preserve this acceptance interpretation. If the formal acceptance instead requires two distinct Einstein-perfect-fluid Bianchi-V solutions sharing the same radiation observable, HOLD that stronger claim: a declared solution family, matter/evolution equations, boundary data and exact or independently validated radiation map for two solutions are missing. Do not manufacture them or hold back the already complete algebraic/design product merely for this optional stronger statement. Final qualification is the controller/reviewer's decision, not this preparation's.

Use retained sources: physical_derivations.md P9-P11; independent_physical_review.md "Metric-level LRS V check and CMB scope"; legacy_reconstruction_chapter.md "What the CMB quadrupole remembers" and "A conditional Bianchi-V consistency curve"; mathematical_recovery.md normal-congruence qualification. Independent_physical_check_result.json is historical finite supporting evidence, not a new symbolic/four-axis proof. No new external literature fact is required. Monograph page references in the retained review are secondary source locators here; do not say that this intake freshly inspected the original monograph.

## Conventions, geometry and matter

Signature (-,+,+,+), physical proper time t, c explicit. Coordinates x,y,z dimensionless and scale factors X,Y lengths; A0>0 dimensionless. Metric
 ds^2=-c^2 dt^2+X(t)^2 dz^2+Y(t)^2 exp(-2A0 z)(dx^2+dy^2).
Choose the normal orthonormal triad (ex,ey,ez) with ez pointing in the oriented +z direction. X,Y>0, A0/X>0; H=(HX+2HY)/3>0, s=(HX-HY)/3, HX=dot X/X, HY=dot Y/Y. H,s have inverse-time units. Sigma^2=s^2/H^2 because sigma/H=diag(-s/H,-s/H,2s/H).

Fixed-time warped curvature is ^3R=-6(A0/X)^2, K=(c A0/(XH))^2>0. H>0 is mean expansion; individual HX may be negative. Do not add directional expansion to the domain silently. The normal congruence is hypersurface orthogonal and has exactly omega[n]=0. The tilted matter congruence is different; its vorticity is not supplied by these instantaneous variables.

One perfect fluid has rest energy epsilon>=0, p=w epsilon, signed velocity c beta along +ez, |beta|<1, gamma=(1-beta^2)^(-1/2). Let Omega=Omega_m=8pi G epsilon/(3c^2 H^2); it is REST energy normalized with NORMAL H. Cosmological constant Omega_Lambda=Lambda c^2/(3H^2) is a separate component. For this product choose 0<=w<=1 and Omega_Lambda>=0 as explicit domain assumptions. No other matter component is permitted in this contract. Results are not claimed for negative cosmological constant, phantom matter or multiple streams.

The normal density is
 Omega_n=Omega[(1+w)gamma^2-w]=Omega(1+w beta^2)/(1-beta^2).
The oriented momentum and normal Hamiltonian constraints are
 2 sqrt(K) s/H=(1+w) Omega beta/(1-beta^2),
 1=K+Sigma^2+Omega_n+Omega_Lambda.
Hence
 Sigma^2=[(1+w)Omega]^2 beta^2/[4K(1-beta^2)^2].
Retain the signed first equation as well as its square. Squaring alone loses the shear/tilt orientation constraint.

Source derivation: for this metric G_0z=-6 A0 s and T_0z=-c X(epsilon+p)gamma^2 beta. Their Einstein equation yields 6(A0/X)(s/c)=(8pi G/c^4)(epsilon+p)gamma^2 beta and the displayed factor two. The spatial warped curvature and Hamiltonian normalization are retained independently checked source statements. No fresh four-axis execution is asserted.

## Algebraically admissible set and an exact parameterization

For fixed (K,beta,w), define
 B=(1+w beta^2)/(1-beta^2)>0,
 A=(1+w)^2 beta^2/[4K(1-beta^2)^2]>=0,
 D=1-K.
The nonnegative-cosmological-constant constraint is A Omega^2+B Omega<=D. Therefore the entire set is empty for K>1; for 0<K<=1,
 0<=Omega<=Omega_max,
 Omega_max=2D/[B+sqrt(B^2+4AD)],
 Sigma^2=A Omega^2,
 s/H=(1+w)Omega beta/[2sqrt(K)(1-beta^2)],
 Omega_n=B Omega,
 Omega_Lambda=D-B Omega-A Omega^2.
This expression is stable at A=0 and gives Omega_max=D/B, including beta=0, and Omega_max=0 at K=1. The denominator remains positive. Do not evaluate the unstable difference of quadratic roots.

Proof: f(Omega)=A Omega^2+B Omega is strictly increasing for Omega>=0. f(0)=0 and its unique nonnegative root at level D is the displayed rationalized root. Thus the inequality is equivalent to the interval. Conversely every such Omega determines nonnegative Omega_Lambda and satisfies both constraints with the SIGNED s/H above. This proves necessary and sufficient algebraic constraint compatibility in the stipulated LRS, single-fluid sector; it does not prove existence or global behavior of a matter evolution.

Parameterize the region without rejection sampling: u in [0,1], Omega=u Omega_max. The deterministic joint image is the tuple (K,beta,w,Omega,sigma/H,Omega_n,Omega_Lambda,normal flux,normal stress). Images of this SAME tuple retain dependence. Independent scalar ranges are only projections and cannot be recombined as if every Cartesian corner were admissible.

An instantaneous metric witness for every accepted tuple: choose any H>0, A0>0 and Y>0; set X=c A0/(H sqrt K), HX=H(1+2s/H), HY=H(1-s/H), dot X=HX X, dot Y=HY Y, epsilon=3c^2 H^2 Omega/(8pi G), p=w epsilon, Lambda=3H^2 Omega_Lambda/c^2, and the signed tilted fluid velocity. These data realize the stated constraints at an event/slice in the ansatz. Do not turn this witness into a time history, assume fixed free parameters stay fixed under evolution, or call arbitrary interpolation an Einstein solution.

## Full normal-frame carrier, avoiding scalar substitution

Use epsilon_crit=3c^2 H^2/(8pi G). The dimensionless fluid flux along ez is f_z=(1+w)Omega gamma^2 beta=2sqrt K s/H; this is a vector component, not a scalar velocity estimate. Define E_tilt=(1+w)Omega gamma^2 beta^2. Then
 rho_n/epsilon_crit=Omega+E_tilt=Omega_n,
 p_n/epsilon_crit=w Omega+E_tilt/3,
 pi_ij/epsilon_crit=E_tilt diag(-1/3,-1/3,2/3),
 sigma_ij/H=(s/H)diag(-1,-1,2),
 beta^i=(0,0,beta).
These full tensors/vectors must be retained, with the shared axis; do not replace them by separately optimized norms. Under beta -> -beta, s/H and flux reverse, while Sigma^2, density, pressure and anisotropic stress are unchanged. Thus even this simple scalar image forgets an orientation.

At Omega=0 the fluid stress and flux vanish. A beta label may remain in the coordinate chart but a physical velocity of absent matter is UNDEFINED, not a measurement or a family distinction. Likewise at beta=0 the momentum equation forces s=0 in this K>0 single-fluid branch. Do not use the formula to assert that all non-tilted Bianchi geometries must be shear free.

## Useful sharp one-dimensional images

Fixed K,w,beta: as Omega ranges from zero to Omega_max, Sigma^2 covers exactly [0,A Omega_max^2]. Signed s/H covers the corresponding signed interval, attained by the parameterization. Omega_n covers [0,B Omega_max]; Omega_Lambda decreases continuously from D to zero. These are coupled intervals.

For fixed K,Omega>0,w and free Omega_Lambda>=0, let C=(1+w)Omega, a=C^2/(4K), b=C+a, d=1-K-Omega. No state exists if d<0. Write t=sinh^2 chi=beta^2/(1-beta^2)>=0. The constraint becomes a t^2+b t<=d. Its exact upper root is
 t_max=2d/[b+sqrt(b^2+4ad)],
 |beta|<=sqrt(t_max/(1+t_max)).
Proof: Omega_n=Omega+C t and Sigma^2=a t(1+t), giving the polynomial; a,b>0 ensure monotonicity. At d=0 only beta=0 is allowed. At Omega=0 this division is invalid: use the vacuum rule above. For a fixed nonnegative Omega_Lambda, replace d by 1-K-Omega-Omega_Lambda and require equality in the polynomial; this gives the unique |beta| for that fixed tuple, when it exists.

A frame-consistent shear-ceiling implication from the retained source is |beta|<=2a0/[1+sqrt(1+4a0^2)] for a0=2sqrt(K_max) Sigma_max/[(1+w)Omega_min], w>-1, Omega_min>0. It is a necessary conservative implication for a nonempty joint domain; it is not a substitute for the normal constraint and does not turn a temperature quadrupole into Sigma_max.

There is a useful curvature envelope for the chosen 0<=w<=1 domain. For Omega>0,
 r=|f|/Omega_n=(1+w)|beta|/(1+w beta^2)<1.
Indeed 1+w beta^2-(1+w)|beta|=(1-|beta|)(1-w|beta|)>0. Therefore
 2sqrt K |s/H|<=Omega_n<=1-K-(s/H)^2,
 so |s/H|<=1-sqrt K and Sigma^2<=(1-sqrt K)^2.
For fixed K in (0,1), the boundary is a supremum as |beta|->1 and Omega->0 at finite normal energy; finite timelike matter with nonzero shear has a strict inequality. Never plot that limiting null/ultrarelativistic boundary as an attained finite-beta state. It is attained at the vacuum K=1 endpoint only in the trivial zero-shear sense.

On a compact displayed beta range |beta|<=beta_max<1, the sharper fixed-K,w shear maximum occurs at |beta|=beta_max and Omega_Lambda=0. To see this, r increases strictly with |beta| because dr/d|beta|=(1+w)(1-w beta^2)/(1+w beta^2)^2>0. With lambda=0 the largest z=|s/H| solves z^2+2sqrt K z/r=1-K, hence
 z_max=r(1-K)/[sqrt(K+r^2(1-K))+sqrt K].
For beta=0, r=0 and z_max=0. This formula equals sqrt(A)*Omega_max. For w in [0,1], r increases with w (derivative |beta|(1-beta^2)/(1+w beta^2)^2), so the largest envelope over that w interval is w=1. This is an algebraic image, not a posterior or population weighting.

## Exact same-observable/different-history counterexample from retained theory

This separate theorem uses the retained collisionless **kinematic Bianchi-I metric class**, not the constrained Bianchi-V perfect-fluid class above:
 ds^2=-c^2dt^2+a(t)^2 sum_i exp(2b_i(t))(dx^i)^2, sum_i b_i=0.
Fix t_i=0, t_f=Delta>0, tau=t/Delta, a(t)=a_i exp(t/Delta), H=1/Delta>0, and initial isotropic Planck radiation T_i in the normal frame with b_i(0)=0. There are no collisions, emission terms after t_i, observer boosts or fluid/Einstein evolution assumptions. Spatial photon momenta are conserved.

Let Lambda_tensor=epsilon diag(-1,-1,2), epsilon=1/50, and alpha=4/5. Define
 B_A(tau)=tau Lambda_tensor,
 B_B(tau)=[(1-alpha)tau+alpha tau^2] Lambda_tensor,
 where B=diag(b_i).
Both have B(0)=0 and B(1)=Lambda_tensor but differ throughout 0<tau<1. Their shear tensors are
 sigma_A=Lambda_tensor/Delta,
 sigma_B=[1-alpha+2alpha tau] Lambda_tensor/Delta.
At t_f the latter is (1+alpha)=9/5 times the former; their integrated shear tensors both equal Lambda_tensor. At tau=1/2 the deformations are Lambda_tensor/2 and 3Lambda_tensor/10. Both metric histories are smooth, expanding in the mean and Lorentzian, with positive scale factors. They have NOT been asserted to satisfy Einstein equations for any specified matter law.

The exact radiation observable is the entire final normal-observer temperature function on the sphere, divided by T0=T_i a_i/a(t_f):
 O[B,a](n)=T(n,t_f)/T0=[sum_i exp(2b_i(t_f)) n_i^2]^(-1/2)
 =[exp(-2epsilon)(n_x^2+n_y^2)+exp(4epsilon)n_z^2]^(-1/2).
Proof: at t_f a photon observed with energy E and direction n has conserved spatial momenta p_i proportional to a(t_f)exp(b_i(t_f)) E n_i. At emission, b_i=0, so E_i/E=(a_f/a_i)[sum_i exp(2b_i(t_f))n_i^2]^(1/2). Liouville transport of the same Planck distribution gives the formula. Both histories have the same endpoints and mean scale factor, hence exactly the same full final angular temperature for all n. Equality is not merely a leading quadrupole approximation. The shear histories and final instantaneous shear differ explicitly. Endpoint shear invariants are Sigma_A^2=epsilon^2=1/2500 and Sigma_B^2=(9/5)^2 epsilon^2=81/62500.

The exact counterexample establishes noninjectivity of this specified kinematic radiation observation map. It does not establish degeneracy of Einstein-perfect-fluid Bianchi-V solutions, all-m T/E/B prediction, matter tilt, or family identification. No polarization map, native transfer or mode atlas is constructed. A plot of the exact axial temperature function and the two shear/deformation histories is enough.

An added endpoint shear measurement separates this pair by ||sigma_B-sigma_A||_F/H=alpha sqrt(6) epsilon. If each candidate is assigned a deterministic full-Frobenius measurement-error ball of radius r, those balls are disjoint exactly when 2r<alpha sqrt(6)epsilon; at equality they touch. This is an error-radius geometry statement, not power or confidence coverage. An intermediate-time temperature also differs since B_A(1/2)!=B_B(1/2), but no actual such channel is claimed available.

## Frozen rendering choices and later verification criteria

No numerical producer, plot or TeX build is authorized for this intake. The later coding worker implements the formulas verbatim and preserves raw failures. Use binary64, dimensionless computations before unit conversion.

A. Domain heat maps: w in {0,1/3}; K_j=0.02+0.96 j/160 for j=0..160; beta_k=-0.9+1.8 k/180 for k=0..180. Plot Omega_max and signed s/H at Omega=Omega_max, with lambda=0 contour interpretation. Never clip an inadmissible point into the domain.
B. Joint-image curves: K in {0.05,0.2,0.5,0.8}, beta in {0,0.2,0.5,0.8}, w in {0,1/3}, u in {0,1/4,1/2,3/4,1}; preserve full tuples and tensor arrays. Show signed mirror branches explicitly, using beta +/- where nonzero.
C. Fixed-matter tilt bounds: Omega in {0.1,0.3,0.6}, same w values and K grid, mark K+Omega>1 as EMPTY_DOMAIN; compare exact beta_max curve with the display cap 0.9. Boundary equality must reproduce lambda=0 without negative-density clipping.
D. Curvature/shear figure: compact beta_max=0.9 envelopes versus the strict limiting envelope (1-sqrt K)^2; label finite-timelike versus supremum correctly.
E. History figure: tau in {j/200: j=0..200}; plot signed tensor coefficient sigma_zz/H (not only its magnitude), b_zz, and final exact T/T0 against mu=n_z in [-1,1]. Both final curves coincide analytically. Keep both three-by-three tensors and sample arrays; no T/E/B atlas.
F. Degeneracy/error figure: r from 0 to 0.02 in 101 points, with exact separation threshold alpha sqrt(6)epsilon/2. Label deterministic feasible-ball intersection, no probability.

Required checks: normal constraint absolute residual<=2e-12; signed momentum residual<=2e-12; STF trace/full norm identities<=2e-12; Omega_max polynomial residual<=2e-12; fixed-Omega tilt boundary residual<=5e-12; mirrored signed outputs equal/opposite within 2e-12; beta=0 and K=1 exact analytic branches; invalid K<=0 or |beta|>=1 rejected/marked OUTSIDE_DOMAIN, not zero-filled; Omega=0 tilt status undefined. Numerical values near theoretical boundaries within roundoff are classified using the analytic parameterization; do not silently mutate underlying tuples. If tolerance failures exceed these limits, retain them and return for scientific interpretation.

For the history pair, compare exact endpoint tensor equality and analytic temperature formula; sampled residual<=2e-14 is a code check, while the all-direction claim rests on the proof. Shear endpoint ratio is exactly 9/5 and squared norm ratio81/25. Numerically integrate nothing: polynomial primitives are explicit. No solver/ODE, CAS rerun, new atlas or external data acquisition is required.

## Claim map and undefined sectors

Claim A: oriented LRS-V signed constraint and instantaneous admissible region — DERIVED under the single-fluid/nonnegative-Lambda domain; retained metric source plus this monotone-root proof. Claim B: joint carrier/compact images — analytic specification, later generated finite illustrations. Claim C: exact radiation-history noninjectivity — DERIVED for smooth kinematic collisionless Bianchi-I metrics; retained exact endpoint formula plus explicit polynomial witnesses. Claim D: stronger Bianchi-V Einstein-fluid history equivalence — NOT_ESTABLISHED; exact missing inputs given above.

For all claims preserve full tensors and fields before summaries. Sigma^2 is a defined geometric scalar here; it is not an observed shear estimate. x_C needs a fixed same-frame comparator and curvature/energy subtraction, which are NOT_SUPPLIED; do not equate x_C with Sigma^2+E_tilt+K by convention-free shorthand. A physical Q score needs a declared anchor/body and denominator, F an explicit support/occupancy measure and suitable ceiling, Pi a probability law, G_F supported depth-F reports and their dependence. Those are NOT_EVALUABLE in this deterministic contract. Q_T if mentioned denotes the radiation quadrupole tensor and must never be conflated with the normalized Q score. Normal vorticity is exactly zero by Frobenius; matter-frame vorticity is NOT_DETERMINED. No missing carrier component or probability is replaced by zero.

Final manuscript and result record must state the source identities, owner/scope, no empirical sky support, no empirical covariance/null, and no transfer source beyond the stipulated analytic radiation map. Formal execution plus one independent final review remain necessary to qualify bianchi_algebra_note. This preparation adds zero original42 completions.
