# A compensated matter–radiation history response at finite observed redshift

Date: 2026-10-20. Owner: `htt`. Base repository identity:
`cosmosapjw-quantum/htt_base`, branch
`research/htt-open-input-theory-20261018`,
commit `69870ee249cd98a869f35e442105d17c927d28fc`.
Requested author runtime: `gpt-6-astra/xhigh`; observed backend: `UNKNOWN`.
Status: **DERIVED, CONDITIONAL, C0 analytic subcase; independent review pending**.

The constructed response is

\[
 {d_L(z,\boldsymbol n)-\bar d_L(z)\over\bar d_L(z)}
 =\boldsymbol n\cdot
 \left[A(z)\boldsymbol\ell+h(z)\boldsymbol b\right]+r(z,\boldsymbol n),
 \quad
 A={c(1+z)\over H(z)\chi(z)},\qquad
 h=1+z-zA.                                                   \tag{1}
\]

Here \(\boldsymbol\ell\) is the observer's instantaneous velocity relative to
the local dust, divided by \(c\); \(\boldsymbol b\) is the present dust velocity
relative to the total-energy normal frame, divided by \(c\). The dust velocity
at emission is \((1+z)\boldsymbol b\) to the required order. A compensating
radiation velocity makes this a consistent first-order homogeneous physical
mode. Its different depth response follows from the conserved source history,
including its observer endpoint. Equation (1) supplies a concrete restricted
input for the V03 research lane. Its remainder and observational qualification
are specified below; the original V03 acceptance remains open.

The ideal radial columns are distinct whenever \(H'(z)>0\):

\[
 {h\over A}={H\chi\over c}-z,\qquad
 {d\over dz}{h\over A}={H'\chi\over c}>0\quad(z>0).             \tag{2}
\]

This is a useful analytic rank criterion before applying actual angular
selection, calibration and covariance. The finite calculation passed 14 checks;
Wolfram independently reduced the main algebraic residuals to zero.

## R1 — Research position and acceptance

The task permits finite algebra and established conservation first integrals.
No evolution equation is solved, no native or substitute Boltzmann solver is
introduced, and no existing campaign is repeated. The actual executable only
evaluates algebraic functions, rational identities, Lorentz endpoint factors,
and finite differences used as derivative falsifiers.

The selected `PUBLICATION_DAG.json` requires:

| Node | Original acceptance | Contribution of this unit | Remaining acceptance |
|---|---|---|---|
| V03 | Same-frame, different radial/temporal transfer and exact source units; original output is external Einstein–Boltzmann history response and validation | A literature-bound first-order analytic distance response with physical compensating component, IC, source/observer frames and a distinct radial law | Qualify the relevant observational source class, background/IC and remainder; supply the original general history/transport payload or separately adjudicate an explicitly restricted subcase |
| S02 | One joint source, exact normalized weights; preserve unknown posterior mass | A possible response ingredient for one homogeneous dipole subspace | Source-match the actual optical field and common congruence, finite-redshift/flow/calibration bounds and selected joint law; existing unknown physical mass stays 1 |
| K03 | Independently qualified nonradial physical response | No nonradial observable is constructed in this unit | Proper-motion/clock/frame or kSZ/polarization response, NNR/calibration and matching covariance remain required |

No original node changes status. Original accounting stays 17/42 complete,
8 direct external blockers and 17 dependent unfinished nodes; all six papers
remain `NOT_READY_TO_SUBMIT`. The current completed Gaia, radio, SDSS, Planck,
CF4 and historical 54-history/432-optical campaigns are unchanged.

## R2 — Evidence and reuse

Primary source equations and exact URLs are recorded in `SOURCES.json`.

* **Beltrán Jiménez–Maroto, arXiv:0811.3606v3**, Eqs. (1), (2), (4), (5),
  supplies the centre-of-mass constraint and constant-\(w\) velocity first
  integrals. Its mechanism for generating motion before decoupling involves
  moving dark energy. Only its first integrals are reused here; this unit
  prescribes independent post-decoupling IC.
* **Kaiser–Hudson, arXiv:1411.6339v2**, Eqs. (1), (8), (9), provides the
  fixed-observed-redshift Doppler distance formula, the decaying-velocity
  substitution and the low-redshift cancellation check. Equation (1) above is a
  specialization and rearrangement of that established optical result.
* **Horstmann–Pietschke–Schwarz, arXiv:2111.03055v2**, Eqs. (7), (9)–(11),
  (13), provides an independent Doppler/aberration derivation. Its Eq. (6)
  is not used as an exact arbitrary-vector velocity-composition formula.
* **Jose–Leblanc–Faraoni, EPJC 82, 557 (2022)**, Eqs. (6), (51)–(58),
  (65), (69), supplies the FLRW background densities, distances and the
  elementary dust/radiation distance case. Only the flat case is used.
* **Attached HTT theory dossier, 2026-09-13**, PDF `20-report-1-.pdf`,
  §§4, 13, 15, supplies the project distinction between compensated momentum
  and quadratic stress, depth-response overlap and common-error obligations.
  Its §15 counterstreaming dust model and numerical campaign are a different
  material/perturbation problem and are not re-executed.

SciSpace was used twice on 2026-10-20. The broad first search had poor
precision. The focused search recovered the 2007 Beltrán Jiménez–Maroto
primary-paper DOI; its index incorrectly labels some arXiv entries as 2022.
Publication years here come from the primary identity. The original 2007 PDF
and ar5iv endpoint were unavailable through the web tool; the authors'
0811.3606v3 PDF was directly accessible and contains the needed equations.
No unavailable text is represented as read. No source payload was downloaded
to disk in this unit.

This is a new repository input/synthesis, not a claim of a new velocity law,
new Doppler-distance theorem, or established journal novelty.

## R3 — Assumptions, units, frames and initial conditions

Use signature \((-+++)\), physical time \(t\), dimensionless \(a(t_o)=1\), and
flat FLRW metric to first order,

\[
 ds^2=-c^2dt^2+a^2(t)\delta_{ij}dx^i dx^j.
                                                               \tag{3}
\]

The coordinates \(x^i\) have length units. The normal orthonormal tetrad is
\(e_{\hat0}=c^{-1}\partial_t,\ e_{\hat i}=a^{-1}\partial_i\).
For any material component,

\[
 U^\mu U_\mu=-c^2,\qquad
 U^{\hat a}=c\gamma(1,\boldsymbol\beta),\qquad
 \boldsymbol v_{\rm physical}=c\boldsymbol\beta
 =a\,{d\boldsymbol x\over dt}.
                                                               \tag{4}
\]

Thus a physical dust velocity proportional to \(a^{-1}\) has coordinate
velocity proportional to \(a^{-2}\); confusing the two changes the response.

The material model on a **finite** post-decoupling interval \(a_i\le a\le1\)
has two separately conserved positive-energy components: pressureless dust
and radiation with \(p_r=\epsilon_r/3\). Baryons and dark matter, if both
included in the dust, share its velocity. There is one radiation velocity;
additional independently moving radiation species require additional inputs.
A cosmological constant may contribute to the background but carries no
momentum. No collisions, drag, pressure perturbations, independent density
perturbations, metric modes, lensing structures or intrinsic source-luminosity
anisotropies are added in this restricted model.

Radiation can be a perfect fluid, or a collisionless homogeneous distribution
whose first-order perturbation is only a dipole about an isotropic spectrum.
For the latter, spatial homogeneity and the absence of a first-order metric
anisotropy leave that dipole with no first-order quadrupole. This is an IC and
linear-order statement, not a finite-multipole nonlinear closure.

Choose the normal frame to be the total-energy rest frame at first order.
The background scalings are
\(\epsilon_m=\epsilon_{m0}a^{-3}\) and
\(\epsilon_r=\epsilon_{r0}a^{-4}\).
Energy densities \(\epsilon,p\) have units J m\(^{-3}\).
The normal momentum density is
\(\boldsymbol q_\alpha=(\epsilon_\alpha+p_\alpha)
\boldsymbol\beta_\alpha/c+O(\beta^3)\), units kg m\(^{-2}\) s\(^{-1}\);
the corresponding energy flux is \(c^2\boldsymbol q_\alpha\).

Let

\[
 R={3\epsilon_{m0}\over4\epsilon_{r0}},\quad
 \boldsymbol\beta_m(a_i)={\boldsymbol b\over a_i},\quad
 \boldsymbol\beta_r(a_i)=-R\boldsymbol b.                       \tag{5}
\]

Set the first-order density, pressure, scalar/vector/tensor metric and shear
perturbations to zero at \(a_i\). The homogeneous radiation dipole is fixed by
(5); its monopole is the declared background. The observer is a test observer
with \(\boldsymbol\beta_o=\boldsymbol b+\boldsymbol\ell\) at observation;
each bolometric standard candle follows the dust congruence. Its rest-frame
luminosity is energy per **source proper time**.

The quantitative velocity restriction is

\[
 \max\{|\boldsymbol b|/a_i,\ R|\boldsymbol b|,
             |\boldsymbol b+\boldsymbol\ell|\}\le\beta_* \ll1.
                                                               \tag{6}
\]

The finite tests use \(\beta_*=0.01\) only as an explicit input rejection
ceiling, not as a certified fractional-distance tolerance. At a given small
redshift, also require the Doppler displacement to be small relative to the
background distance-redshift variation:
\((1+z)|\boldsymbol n\cdot(\boldsymbol\beta_s-\boldsymbol\beta_o)|\ll z\).
In particular \(|\ell|\ll z\) is needed near zero. The response coefficients
have well-defined formal limits even where a finite-amplitude truncation is
not uniform.

Independent post-decoupling IC are essential. If one additionally imposes
identical dust/radiation velocities at \(a_i\), the positive-energy
zero-total-momentum constraint forces their common velocity to vanish.
This unit supplies no mechanism that generates (5) from a tightly coupled
adiabatic primordial state.

## R4 — Choice of the physical subcase

A single moving gravitating dust component on unchanged FLRW would violate
the first-order momentum constraint. Duplicating the local observer column
would carry no source history. Two dust streams with equal decay laws are a
useful benchmark but add no dust/radiation relative decay here.

The selected two-fluid IC makes the matter source physically admissible at
linear order and provides distinct dust and radiation histories using
established first integrals. The relative velocity
\(\boldsymbol\beta_m-\boldsymbol\beta_r\) is invariant under a common
first-order frame velocity shift. It is a physical relative-motion mode.
The chosen normal frame, source congruence and observer endpoint remain
separate; no matter frame is silently called the CMB frame.

## R5 — Constructive derivation

### 5.1 Constraint and conserved history

The spatial translation Killing fields of (3) imply the homogeneous
momentum first integral. Equivalently, the cited fluid result gives
\(a^4(\epsilon_\alpha+p_\alpha)\boldsymbol\beta_\alpha
=\boldsymbol C_\alpha\) in the zero-shift normal frame. This established
first integral is evaluated algebraically, without integrating an ODE:

\[
 \boldsymbol\beta_m(a)={\boldsymbol b\over a},\qquad
 \boldsymbol\beta_r(a)=-R\boldsymbol b,\qquad
 \boldsymbol C_m=\epsilon_{m0}\boldsymbol b,\quad
 \boldsymbol C_r=-\epsilon_{m0}\boldsymbol b.                   \tag{7}
\]

The normal momentum constraint therefore holds throughout the interval:

\[
 c(\boldsymbol q_m+\boldsymbol q_r)
 ={1\over a^4}\left(\epsilon_{m0}\boldsymbol b
             -{4\over3}\epsilon_{r0}R\boldsymbol b\right)=0.
                                                               \tag{8}
\]

At first order, boosted perfect-fluid energy/pressure corrections and
anisotropic stresses are zero; only the individually nonzero momenta could
source the metric. Equation (8) cancels them. The homogeneous linear
Einstein Hamiltonian and momentum constraints and spatial equations thus
have zero perturbative source, and zero metric perturbations satisfy them.
The separate energy conservations retain their background forms because
the spatial velocity divergence is zero. Together with (7), these checks
establish a consistent linear Einstein–matter perturbation.

At finite amplitude the stress
\[
 \pi^{\hat i\hat j}=\sum_\alpha(\epsilon_\alpha+p_\alpha)
 \gamma_\alpha^2\beta_\alpha^{\langle i}\beta_\alpha^{j\rangle}
                                                               \tag{9}
\]
does not generally cancel. For collinear motion its leading coefficient is
\[
 \left[\epsilon_{m0}a^{-5}
       +{4\over3}\epsilon_{r0}R^2a^{-4}\right]
 b^{\langle i}b^{j\rangle}.
\]
The linear metric is not promoted to an exact finite-amplitude FLRW solution.
This preserves the dossier §4/§15 distinction.

### 5.2 Endpoint signs and fixed observed redshift

Let \(\boldsymbol n\) point from observer to source. It is the background
line-of-sight direction; replacing it by the measured direction changes
linear dipole expressions only at second order. Define
\(s=\boldsymbol n\cdot\boldsymbol\beta_s\) and
\(o=\boldsymbol n\cdot\boldsymbol\beta_o\) in this subsection only.

The measured photon energy is \(-U_\mu k^\mu\). Thus, with
\(D_s=\gamma_s(1+s)\) and \(D_o=\gamma_o(1+o)\),
\[
 1+z=(1+\bar z){D_s\over D_o}
       =(1+\bar z)[1+s-o]+O(\beta^2).                         \tag{10}
\]
The photon propagates along \(-\boldsymbol n\), which fixes the plus signs
inside \(D_s,D_o\). Observer aberration gives
\(d_A=\bar d_A(\bar z)(1+o)+O(\beta^2)\).
Etherington duality, using the same measured redshift and rest luminosity,
then gives
\[
 d_L=\bar d_L(\bar z)[1+2s-o]+O(\beta^2).                    \tag{11}
\]
Source proper time and observer proper time obey
\(d\tau_s/d\tau_o=(1+z)^{-1}\) along successive wavefronts. This clock
conversion is already present in (10) and duality; no extra source-time
factor should be added. Individual \(d\tau/dt=1+O(\beta^2)\) is consistent
with retaining first-order endpoint Doppler rates.

At fixed **observed** \(z\),
\(\bar z-z=-(1+z)(s-o)+O(\beta^2)\). For
\(\bar d_L=(1+z)\chi(z)\), \(\chi'(z)=c/H(z)\),
\[
 (1+z){d\ln\bar d_L\over dz}=1+A.
\]
Combining the Taylor shift with (11) yields
\[
 {\delta d_L\over\bar d_L}
 =2s-o-(1+A)(s-o)=(1-A)s+Ao.                                \tag{12}
\]
It has the independent checks \(A\boldsymbol n\cdot\beta_o\) for a pure
observer boost and \((1-A)\boldsymbol n\cdot\beta_s\) for a source-only
velocity. Using the same-\(z\) background in both distances is crucial.

The emitting dust has
\(\boldsymbol\beta_s=\boldsymbol b/a_s
=(1+z)\boldsymbol b+O(\beta^2)\).
Here replacing \(\bar z\) by \(z\) changes this already first-order
velocity only at second order. Substituting it and
\(\beta_o=b+\ell\) into (12) produces (1).

The relative matter–radiation velocity today is
\(\boldsymbol w=(1+R)\boldsymbol b\). If that is the desired parameter,
the history column is \(h/(1+R)\), with \(\ell\) still defined relative
to local matter. If instead the observer parameter is its velocity
\(\boldsymbol u=\beta_o-\beta_r=\ell+(1+R)b\) relative to radiation,
the algebraic response is
\[
 {\delta d_L\over\bar d_L}
 =\boldsymbol n\cdot\{A\boldsymbol u+
              [h/(1+R)-A]\boldsymbol w\}.                    \tag{13}
\]
These are invertible parameter changes for finite positive \(R\), not extra
data. No measured CMB dipole is inserted as \(\boldsymbol u\).

### 5.3 Low-redshift limit and the radial rank theorem

For a smooth flat background,
\(H/H_0=1+(1+q_0)z+O(z^2)\) and
\(H_0\chi/c=z-(1+q_0)z^2/2+O(z^3)\). Consequently
\[
 A={1\over z}+{1-q_0\over2}+O(z),\qquad
 h={1+q_0\over2}z+O(z^2).                                   \tag{14}
\]
The history contribution for an observer sharing the current dust flow
vanishes as \(z\to0\). Freezing the emitting dust velocity to its current
value would instead produce a spurious constant coefficient 1.
This cancellation agrees with Kaiser–Hudson's same-time check.

For two ideal shell dipole components \(d_j=A_j\ell+h_j b\),
\[
 \det\begin{pmatrix}A_1&h_1\\A_2&h_2\end{pmatrix}
 =A_1A_2[F(z_2)-F(z_1)],\quad F=h/A.
                                                               \tag{15}
\]
Differentiating the standard distance identity gives (2).
In flat dust+radiation+\(\Lambda\),
\[
 H^2=H_0^2[\Omega_m(1+z)^3+\Omega_r(1+z)^4+\Omega_\Lambda],
 \quad
 H'={H_0^2[3\Omega_m(1+z)^2+4\Omega_r(1+z)^3]\over2H}>0.
\]
Thus (15) is strictly positive for \(0<z_1<z_2\), positive dust/radiation
and \(H>0\). This proof establishes the ideal radial result without
evaluating a background integral. Identical depths are rank deficient.
The empty de Sitter formal limit has \(H'=0\) and loses this strictness,
but does not contain the assumed positive two-fluid compensated mode.

An explicit observer-cancelling contrast is
\[
 {d_2\over A_2}-{d_1\over A_1}
       =[F(z_2)-F(z_1)]b.                                    \tag{16}
\]
Applied componentwise to full ideal shell dipoles, it recovers the three
components of \(b\). Actual angular completeness or a measured shell dipole
is not assumed from this algebra.

### 5.4 An entirely algebraic background benchmark

For the flat \(\Lambda=0\) two-fluid member, put
\(y=1+z\), \(\Omega_m+\Omega_r=1\), \(0<\Omega_r<1\), and
\(s_b=\sqrt{\Omega_r+\Omega_m/y}\). The standard elementary distance
relation has the equivalent rationalized form
\[
 H=H_0y^2s_b,\qquad
 \chi={2c\over H_0\Omega_m}(1-s_b)
     ={2cz\over H_0y(1+s_b)}.                                \tag{17}
\]
Its normalization \(\chi(0)=0\) and derivative
\(\chi'=c/H\) are verified algebraically. No time evolution \(a(t)\) or
optical ODE is solved. The rationalized version avoids small-\(z\)
subtraction. It yields
\[
 A={1+s_b\over2zs_b},\qquad
 h=z\left[1-{\Omega_m\over2ys_b(1+s_b)}\right].                \tag{18}
\]
The finite examples use synthetic
\(\Omega_r=10^{-4},\Omega_m=0.9999,H_0=70\) km s\(^{-1}\) Mpc\(^{-1}\),
\(c=299792.458\) km s\(^{-1}\); these are not a fit to the observed universe.

| Observed \(z\) | Local \(A\) | History \(h\) |
|---:|---:|---:|
| 0.01 | 100.249352981 | 0.007506470191 |
| 0.05 | 20.246925149 | 0.037653742566 |
| 0.10 | 10.244018021 | 0.075598197917 |
| 0.50 | 2.224714254 | 0.387642873041 |
| 1.00 | 1.207071428 | 0.792928571501 |
| 2.00 | 0.682969407 | 1.634061185768 |

The \(z=0.05,0.5\) determinant is 7.764807417080288; the contrast coefficient
in (16) is 0.17238416681469013. All numbers are generated in `RESULTS.json`.
The compensation ratio is \(R=7499.25\). Hence even a modest radiation
velocity ceiling strongly restricts \(b\); a 300 km/s coherent dust speed
cannot simply be inserted into this synthetic compensated mode.

`history_response.png` and `history_response.pdf` plot these exact algebraic
coefficients and their low-redshift limits on \(10^{-4}\le z\le2\).
The plot explicitly labels the hypothetical background and absence of an
observational fit; it does not assign a finite physical velocity to every
plotted redshift. The PNG was visually inspected: labels, limits and legends
are readable and no content is clipped.

## R6 — Independent falsifiers and physics audit

Two logically distinct constructions check the optical signs: the published
fixed-\(z\) expression (12), and a direct exact endpoint Lorentz/duality
calculation on a prescribed FLRW metric. The executable starts at \(\bar z\),
forms exact \(D_s,D_o\), obtains
\(z_{\rm obs}=(1+\bar z)D_s/D_o-1\) and
\(d_L=\bar d_L(\bar z)D_s^2/D_o\), then evaluates its odd derivative at zero
velocity against (1). Its finite-amplitude metric is a kinematic testbed,
not the nonlinear coupled two-fluid spacetime.

Wolfram checked the derivative of (17), (18)'s \(A\) identity, the expansion
coefficient \((3+\Omega_r)/4\), momentum cancellation, fixed-\(z\) signs,
the kernel rearrangement and (2). All requested residuals returned zero.
The kernel emitted undefined-symbol and intermediate infinity warnings from
symbolic evaluation; these are preserved in `WOLFRAM_CHECK.json`, not hidden.
Its exact returned finite identities are used within their stated positive
domains. This is one external symbolic check, not a four-axis CAS result.

| Audit item | Outcome | Scope or remaining condition |
|---|---|---|
| Linear Einstein constraint | Satisfied by (8) and zero first-order stress perturbations | Two separately conserved components, specified IC |
| Gauge/frame | Relative velocity preserved under common first-order frame shift | Metric shift and component velocities must transform together |
| Units | \(A,h,\beta,\delta d_L/\bar d_L\) dimensionless; \(H\chi/c\) dimensionless | \(\epsilon\) is energy density, not mass density |
| Source clock | Encoded in measured energy ratio and distance duality | Rest-frame bolometric standard candle |
| Zero velocity | Zero response | Checked |
| Source/observer signs | \(1-A\) and \(A\) | Checked by independent Lorentz derivative |
| Same-time/coherent low-\(z\) flow | \(h\to0\) | Finite-amplitude local boost still needs \(|\ell|\ll z\) |
| Endpoint-copy falsifier | \(h\ne A\); frozen-source coefficient 1 fails | Checked at declared depths |
| Radiation linearity | Requires \(R|b|\ll1\) | Explicit rejection example retained |
| Rank | Ideal two-depth radial determinant positive | Selected nuisance-projected rank remains conditional |
| Finite-amplitude GR | Quadratic stress remains | Optical/dynamic remainder not computed |
| Source/data matching | Not performed | Original optical and nonradial data gates remain open |

This mode has no independent first-order shear, vorticity or dust
four-acceleration: dust is geodesic, spatially homogeneous, and the first-order
projected velocity gradient adds no shear or curl. Its nonzero finite-depth
distance dipole is therefore not a measurement of those sectors. In particular
it cannot populate every physical unknown in S02 or serve as K03's nonradial
curl/acceleration kernel.

## R7 — Actual finite execution

Command:

```sh
/opt/codex/runtimes/codex-primary-runtime/dependencies/python/bin/python \
  verify_history_kernel.py
```

Execution was from the selected scratch fixture, using Python 3.12.14 and
standard-library modules only. It ran once: **14 tests, zero failures/errors,
0.0007854470022721216 seconds** measured for the suite, exit 0. No worker
threads, data downloads or old calculations were started. The separate
Wolfram call had a 20-second kernel limit and a reported 14.0-second tool wall
time. Both calculations are below the requested lightweight bound.

The new 400-point algebraic plot ran once with one-thread numerical-library
environment pins: 1.4111500090002664 seconds measured inside the plotting
script, exit 0. `PLOT_RECEIPT.json` records Matplotlib 3.10.8 and NumPy 2.3.5.
Reported tool wall times include 3.0805 seconds for plotting and 0.0487
seconds for the combined dossier read/test command. There was no repeated
test or plot calculation.

The checks cover exact rational conservation; zero-total-momentum failure
without radiation; relative-frame invariance; exact Lorentz endpoint
derivatives; signs and zero velocity; the low-\(z\) cancellation; distinct
and duplicate depth ranks; the local-annihilating contrast; nuisance
annihilation of the history column; rejection of endpoint copying;
perturbative-domain rejection; unit rescaling; and a deterministic
two-bin remainder bound. No p-value or sampling coverage is calculated.

## R8 — Interpretation, residual bounds and kill switches

For real selected data the relevant linear design is
\[
 X_i=[A(z_i)\boldsymbol n_i^{T},\ h(z_i)\boldsymbol n_i^{T}],
 \qquad \boldsymbol y=X(\ell,b)+N\nu+\boldsymbol r.             \tag{19}
\]
A specified linear nuisance-removing operator \(P_N\) gives the actual
rank question \(\operatorname{rank}(P_NX)=6\), together with adequate
conditioning in the declared noise metric. Equation (2) alone does not
establish this. The executable includes the exact counterexample where
the nuisance space contains the history column and its projection is zero.
Arbitrary independent calibration dipoles at each depth can absorb the
entire signal. Overlapping shells require their cross-covariance as in
dossier §13.2; shell count is not independent-draw count.

The remainder is kept explicitly. For finite residual endpoint velocities
bounded by \(B_s,B_o\), optical/metric error \(B_{\rm opt}\), source
luminosity/calibration error \(B_{\rm cal}\) and selection/modelling
error \(B_{\rm sel}\), the declared first-order additive model gives
\[
 |r_i|\le |1-A_i|B_{s,i}+|A_i|B_{o,i}
                +B_{{\rm opt},i}+B_{{\rm cal},i}+B_{{\rm sel},i}.
                                                               \tag{20}
\]
The finite-amplitude GR/Taylor truncation contribution belongs inside
\(B_{\rm opt}\) with its defined convention; it is not silently removed.
For fixed smooth background and fixed \(z_{\min}>0\) the neglected formal
terms are second order in velocities, but that order notation supplies
neither a uniform numerical constant nor a measured error law.

As a limited instantaneous statement, if all speeds are at most \(\beta_*\),
the boosted perfect-fluid stress obeys the algebraic bound
\[
 \|\pi\|_F\le \sqrt{2/3}\,
       {\beta_*^2\over1-\beta_*^2}
       \sum_\alpha(\epsilon_\alpha+p_\alpha).                 \tag{21}
\]
This follows from
\(\|\beta^{\langle i}\beta^{j\rangle}\|_F=\sqrt{2/3}|\beta|^2\)
and the triangle inequality. It does not give an accumulated optical
bound without the corresponding propagation/IC control.

If two shell residuals satisfy specified finite bounds
\(|r_j|\le e_j\), (16) gives the sharp elementary bound
\[
 |\widehat b-b|
 \le {e_2/|A_2|+e_1/|A_1|\over |F_2-F_1|}.                  \tag{22}
\]
Likewise a chosen left inverse of \(P_NX\) propagates any supplied residual
set into a parameter set. The actual \(e_j,B_{\rm opt},B_{\rm cal},B_{\rm sel}\)
are **UNKNOWN** for the selected observational sources. They have not been
assigned finite numbers or zero. Equation (22) is a conditional deterministic
error statement, not a confidence interval.

Kill switches are violated compensation, absent source-frame matching,
uncontrolled primordial extrapolation, radiation speeds outside (6),
redshift displacement comparable to \(z\), missing calibrated remainders,
or deficient/ill-conditioned \(P_NX\). Each restricts the relevant application,
without erasing the completed linear derivation.

The result is constructive. No new strong no-go theorem is proposed.
The duplicate-depth and nuisance counterexamples apply only to their named
linear designs. NG1–NG7 do not authorize a claim about every global-history
model from these local examples.

## R9 — Transfer/provenance and claim handoff

`CLAIMS_AND_TRANSFER.json` records a descriptive `TransferFunctionSpec`-style
analytic input contract. It is not asserted to have passed an unavailable
repository schema validator. The contract identifies material content, IC,
normal/source/observer frames, units, perturbative order, background,
source equations and residual status. `transfer_source: none` means no
AniCLASS or BASS transfer is consumed; the separate `response_kind` identifies
the source-bound analytic response. No native output is fabricated.

HTT owns any later model-dependent inference consuming (19). MIO can report
response overlap and coherence diagnostics with their exact assumptions.
No posterior, physical \(x,Q,F,G\), family identity or morphological atlas is
produced here. The constructed mode is a restricted multi-fluid perturbation;
it is not a family-independent model of all cosmic tilt.

## R10 — Decision and continuation

**Author decision:** adopt equations (1), (5)–(8), (15)–(18) as a constructive,
source-bound analytic V03 subcase, subject to the separately assigned
independent review. No original 42-node completion is requested.

The next scientifically distinct action is to select an actual source
population and its existing measured-\(z\)/distance convention, then bind
(19) to its real angular/depth design and nuisance blocks. Before any physical
inference, provide the omitted flow/metric/IC and selected-error inputs or
justified finite bounds. A purely algebraic design projection can be useful
once those source identities exist; a rerun of completed catalogue fits is
not part of this handoff. The original general V03 payload, S02's joint
physical pushforward and K03's nonradial transfer remain open.

Parent is the sole publisher. Proposed repository destination:
`docs/research_program/observational_publication_20261015/OPEN_INPUTS_20261018/EXECUTION_20261018/COMPENSATED_HISTORY_20261020/`.
Local deliverables and their proposed destinations are in `MANIFEST.json`.
No commit, push, merge or manuscript-readiness claim is made by the author.
