# Restoring the physical target of tensorized inference

Internal research note, 28 October 2026. Scope: selected R2/R3/R5 foundation pass, with source reuse from the legacy report, K1R and the R36 integration. No repository mutation, solver, ODE integration or new observational fit. Latest repository identity supplied by the parent is `7f3f49a6b6d95b6ae0323d5bebd3afce0067b1a7`; imported proof sources inspected here were pinned at `fb2bb0ac6a9537861c2c2e2c5157fc81787922d0`.

## 1. The original aim survives, with a precise physical target

The viable programme is to infer **response-qualified kinematics** from joint, signed sky information. The carrier should preserve the response of a physical parameter, not every tensor component indefinitely. MES provides conditional constraints linking radiation transport to spacetime kinematics. It does not provide a probability distribution for those kinematics. The distribution comes from an observational model, a source/transport model and a declared nuisance treatment.

The oldest useful idea can therefore be retained as

\[
Y\ \longrightarrow\ x_{\rm obs}\ \longrightarrow\
\Theta_\alpha(Y)\subset\{\sigma,\omega,A,\beta\}
\ \longrightarrow\ (F,Q,\Pi,G_F).
\tag{1}
\]

Here the middle arrow is a response-qualified inverse or confidence-set projection. It can be many-to-one or set-valued. The five labels are not five independent likelihood factors. A geometric feasible region can be calculated before a probability law is available; a calibrated likelihood can later weight that region.

“MES equality” needs two names. Maartens–Ellis–Stoeger derive evolution/constraint equalities and turn these into norm inequalities under additional assumptions. The equalities retain signed couplings; the inequalities give an outer envelope. Dividing by that envelope is a useful coordinate choice, but does not turn the envelope into an empirical posterior. The primary sources are MES, [Phys. Rev. D 51, 1525 (1995)](https://doi.org/10.1103/PhysRevD.51.1525), its [1996 explanatory letter](https://arxiv.org/abs/astro-ph/9510126), and the [corrected COBE implementation](https://arxiv.org/abs/astro-ph/9904346).

## 2. Four distinct axes

| Axis | Object retained | Physical consequence |
|---|---|---|
| Symmetry and redundancy | Coordinate chart, spatial triad, harmonic phase convention; joint rotation of all relevant tensors | Passive changes of basis leave the experiment unchanged. Relative orientations remain relevant. A change of observer is a physical response transformation, not merely removal of a coordinate redundancy. |
| Invariants | Tensor norms, eigenvalues, contractions and relative-orientation invariants, with the transformation group stated | A scalar invariant is useful only for the question it preserves. A rotational norm can erase a signed response in a calibrated frame. |
| Observables | Detector maps, calibrated harmonic coefficients, signed proper motions and distance coefficients, with their joint law | Their values are tied to beam, mask, selection, frequency, distance and reference frame. A sky STF2 is not automatically matter shear. |
| Physical quantities | Kinematics of a specified congruence, radiation stress, relative velocity of specified fluids, spatial curvature | These are inferred through an explicit forward response. Their physical meaning cannot be supplied by normalization alone. |

Adopt signature \((-+++ )\). Let \(U^2=-1\), let \(\tau\) be physical proper time, and let \(\dot{}=U\cdot\nabla\) differentiate per proper length \(s=c\tau\). The geometrical tensors \((\Theta,\sigma^{(g)},\omega^{(g)},a^{(g)})\) have inverse-length units. Define physical rates and acceleration by

\[
H=\frac{c\Theta}{3},\qquad \Sigma=c\sigma^{(g)},\qquad
\Omega=c\omega^{(g)},\qquad A=c^2a^{(g)}.
\tag{2}
\]

In the fundamental comoving congruence of exact FLRW, \(\Sigma=\Omega=A=0\). A radiation–matter relative velocity \(\beta_{RM}\) also vanishes for the isotropic common-rest-frame radiation/matter model. The velocity \(\beta_{MO}\) of our observer relative to matter can be nonzero in exact FLRW. The measured radiation dipole generally mixes \(\beta_{MO}\), radiation–matter motion and intrinsic radiation structure. A single symbol \(\beta\) must be assigned one of these meanings before inference.

The local kinematic null is a useful **necessary** property of the specified FLRW model. It is not, alone, a complete characterization of FLRW geometry. Curvature, gradients and evolution contain further information. Conversely, perturbations of an FLRW background produce local shear, velocities and radiation anisotropies: rejecting a zero local tensor is different from rejecting the usual stochastic perturbed-FLRW cosmological model. Both questions can be posed, with separate nulls.

## 3. A usable MES normalization

For the matter/dust branch and derivative assumptions used by the corrected MES application, define the conventional temperature-multipole bounds \(\epsilon_\ell\). Its simplified envelopes are

\[
B_\sigma=\frac53\epsilon_1+3\epsilon_2+\frac37\epsilon_3,
\qquad
B_\omega=\frac{10}{3}\epsilon_1+\frac{2}{15}\epsilon_2.
\tag{3}
\]

They bound \(\|\sigma^{(g)}\|_F/\Theta\) and the full antisymmetric-tensor norm \(\|\omega^{(g)}_{ab}\|_F/\Theta\), respectively. Their scope includes the almost-isotropy/Copernican use of radiation constraints and control of derivatives. Small multipoles at one event do not alone bound their spatial or temporal derivatives. The more explicit shear expression in the explanatory letter, Eq. (6), retains derivative allowances:

\[
\frac{\|\sigma^{(g)}\|_F}{\Theta}
<\frac83\epsilon_2+\epsilon_2^*+5\epsilon_1^\dagger
+\frac97\epsilon_3^\dagger.
\tag{4}
\]

The conversion from Eq. (4) to Eq. (3) uses further derivative-timescale assumptions; those should remain parameters of the reference family. A much tighter spatially homogeneous/Bianchi-I specialization is a different branch, not a replacement for Eq. (3).

For \(H>0\), positive declared reference values and the vorticity vector \(\Omega_a=\tfrac12\varepsilon_{abc}\Omega^{bc}\), a dimensionless parameter carrier is

\[
x_{\rm kin}=
\left(
\frac{\Sigma}{3HB_\sigma},\quad
\frac{\sqrt2\,\Omega}{3HB_\omega},\quad
\frac{A}{cH a_*},\quad
\frac{\beta_{RM}}{b_*}
\right).
\tag{5}
\]

The \(\sqrt2\) follows from \(\Omega_{ab}\Omega^{ab}=2\Omega_a\Omega^a\). There is no MES authority for arbitrary \(a_*\) or \(b_*\): these are separate declared reference scales unless supplied by a further theorem. In the geodesic branch, \(A=0\) is a domain restriction, rather than division by a zero acceleration radius. At a zero or inapplicable MES radius retain the unnormalized component and an explicit domain label. Nonlinear observables should be evaluated jointly from the same carrier; appending a squared norm does not create another independent measurement.

For a product of rotational norm balls, the body gauge is the maximum of the normalized sector norms. A response-feasible region generally couples sectors and need not be a product. Its support function supplies directional information that the original norm ceilings discarded. If \(B_\sigma\) or \(B_\omega\) is estimated from the same sky used in the likelihood, propagate the numerator and denominator jointly; multiplying a separate “MES likelihood” by the same-data sky likelihood would double count evidence.

The sky convention can be checked exactly. If \(\vartheta(n)=\sum a_{\ell m}Y_{\ell m}(n)/T_0=\sum\tau_{A_\ell}n^{\langle A_\ell\rangle}\), then

\[
\|\tau_{A_\ell}\|_F^2
=\frac{(2\ell+1)!!}{4\pi\ell!}\sum_m|a_{\ell m}/T_0|^2.
\tag{6}
\]

For the realized \(\widehat C_\ell=(2\ell+1)^{-1}\sum_m|a_{\ell m}/T_0|^2\), the coefficients at \(\ell=1,2,3,4\) are \(9/(4\pi),75/(8\pi),245/(8\pi),2835/(32\pi)\). A realized power and an ensemble expectation are distinct objects. The unit and tensor/vector conversion was independently checked in exact rational arithmetic and Wolfram; receipts accompany this note.

## 4. Recovering signed shear information from radiation

The retained Loop A result gives a useful direct realization of the original aim. Let \(I(e)\ge0\) be bolometric radiation energy density per solid angle in the specified congruence, and set

\[
\rho=\int I\,d\Omega,\quad q_a=\int Ie_a\,d\Omega,
\quad\pi_{ab}=\int Ie_{\langle a}e_{b\rangle}\,d\Omega,
\quad H_{A_\ell}=\int Ie_{\langle A_\ell\rangle}\,d\Omega.
\tag{7}
\]

The physical energy flux is \(cq\). All these moments have energy-density units. Propagation direction is \(e=-n\), where \(n\) is outward sky direction. For a direction-dependent exact Planck spectrum, \(I=\pi k_B^4T^4/(60\hbar^3c^3)\). The fourth power must precede angular projection: temperature dipole/quadrupole and bolometric stress are not interchangeable. Polarization E/B coefficients are not the unpolarized intensity moments in Eq. (7).

In the geodesic, irrotational, collisionless branch, the retained exact relation in physical-time units is

\[
\mathcal L_I\Sigma=-R_\tau,
\quad R_\tau=\partial_\tau\pi_{\langle ab\rangle}
+4H\pi_{ab}+\frac{2c}{5}D_{\langle a}q_{b\rangle}
+cD^dH_{abd},
\tag{8}
\]

\[
\mathcal L_I S=\frac{8\rho}{15}S+
\frac{10}{7}\operatorname{STF}(S\pi)-H_4:S.
\tag{9}
\]

This is an algebraic inverse once the local transport residual is supplied. It needs no Boltzmann integration. The positive-operator proof, reused from Loop A, is

\[
\langle S,\mathcal L_I S\rangle
=\int I\{2|Se|^2-(e^TSe)^2\}\,d\Omega
\ge\lambda_{\min}(\rho I_3/3+\pi)\|S\|_F^2.
\tag{10}
\]

The response matrix is only five-dimensional and uses brightness ranks 0, 2 and 4. The residual uses differentiated ranks 1, 2 and 3. Thus the operator can be completed from a sky product before the residual product exists. This is a concrete response-based completion rule and a natural role for tensorized compression.

**Directional constraint derived in this pass.** Suppose \(\mathcal L_I\) is fixed and invertible and the residual belongs to a closed convex set \(\mathcal R\). Then the exact feasible shear set for Eq. (8) is

\[
\mathcal S_I=-\mathcal L_I^{-1}\mathcal R,
\qquad h_{\mathcal S_I}(u)=h_{\mathcal R}(-\mathcal L_I^{-T}u).
\tag{11}
\]

This follows directly by maximizing \(\langle u,-\mathcal L_I^{-1}r\rangle\) over \(r\in\mathcal R\). For \(\mathcal R=r_0+\epsilon_R B_2\), the center is \(-\mathcal L_I^{-1}r_0\) and the half-width in direction \(u\) is \(\epsilon_R\|\mathcal L_I^{-T}u\|\). A scalar MES ball keeps only a common outer radius; Eq. (11) preserves physically relevant anisotropic uncertainty. Its intersection with a MES body is legitimate when both apply to the same congruence, source and derivative premises.

If instead \(\widehat R_\tau\mid\Sigma\sim N(-\mathcal L_I\Sigma,C_R)\), with fixed known \(\mathcal L_I\) and qualified covariance, then

\[
L(\Sigma\mid\widehat R_\tau,I)\propto
\exp\left[-\frac12(\widehat R_\tau+\mathcal L_I\Sigma)^T
C_R^{-1}(\widehat R_\tau+\mathcal L_I\Sigma)\right].
\tag{12}
\]

Equation (12), rather than the MES radius, supplies a likelihood. It is a specified conditional experiment, not a newly measured shear constraint. If \(I\) and \(R\) are uncertain and correlated, they belong in one errors-in-variables law.

The reused finite-error inversion remains useful without Gaussian assumptions. If \(\|\mathcal L_I-\widehat{\mathcal L}\|\le\epsilon_L\), \(\|R_\tau-\widehat R_\tau\|\le\epsilon_R\), \(\widehat\lambda=\lambda_{\min}(\widehat{\mathcal L})>\epsilon_L\), and \(\widehat\Sigma=-\widehat{\mathcal L}^{-1}\widehat R_\tau\), then

\[
\|\Sigma-\widehat\Sigma\|_F
\le\frac{\epsilon_R+\epsilon_L\|\widehat\Sigma\|_F}
{\widehat\lambda-\epsilon_L}.
\tag{13}
\]

This supplies a finite, testable input contract. If only one sky's moment values are known, report \(\mathcal L_I\) and the family of Eq. (11) as a function of derivative allowance. A derivative prior, an external response/history, remote-radiation information or another qualified source can later supply \(\mathcal R\). Nothing here requires every unrelated observation branch to wait for that input.

## 5. The physical outcomes available before a transport history

Radiation stress itself is already a physical quantity. The integrated R36 result uses \(f=q/\rho\), \(P=\pi/\rho\) in the energy-density convention of Eq. (7), and defines

\[
\mathscr D=P-\frac{3}{2+\sqrt{4-3|f|^2}}
\operatorname{STF}(ff^T),\qquad \rho>0,\ |f|<1.
\tag{14}
\]

Under the physical positive-stress assumptions, \(\mathscr D=0\) characterizes a perfect radiation stress tensor in some timelike rest frame. A confidence image for \(\mathscr D\) tests whether an observer boost alone can account for the measured stress anisotropy. It does not test whether all higher radiation moments vanish, and it does not yet measure matter shear. It is nevertheless a direct physical use of low-order morphology, with neither ODEs nor a complete hierarchy solution. Frequency completion, intensity calibration and positivity are the actual data inputs. Existing Planck E-mode morphology cannot be substituted for intensity in Eq. (14).

The second direct route is the retained common-congruence optical inverse. For calibrated, nearby sources and observer sharing one smooth congruence,

\[
d(n)=\lim_{r\to0}\frac{cz}{r}=H+\Sigma:nn-\frac{A\cdot n}{c},
\qquad
\mu(n)=(I-nn^T)\Sigma n+n\times\Omega.
\tag{15}
\]

With a fixed nonrotating triad and full-sky ideal averages,

\[
H=\langle d\rangle,\quad A/c=-3\langle dn\rangle,\quad
\Sigma=\frac{15}{2}\langle d(nn-I_3/3)\rangle
=5\langle\mu_{(i}n_{j)}\rangle,\quad
\Omega=-\frac32\langle n\times\mu\rangle.
\tag{16}
\]

The convention for the axial vector is fixed by Eq. (15). An unknown catalogue-frame spin has exactly the same transverse B1 pattern and must be calibrated or retained as a joint degeneracy. Distant-quasar secular aberration uses a different source/observer response. It cannot simply inherit the common-congruence acceleration interpretation. The existing Gaia Gaussian carrier is an excellent test of information retention and nuisance handling, while the physical adapter determines which combinations of kinematics it measures.

### Latest branch advances beyond the older Gaia proposal

The latest qualified R36-03 product supplies a more direct physical comparison than the older 24D E1/B1 compression proposal. For a weak homogeneous fixed-axis Bianchi-I kinematic branch, its signed common E2 response is

\[
\mathcal A_{\rm PM}=\frac{2c}{D}(B_o-B_s)-\dot B_o,
\qquad \mu=P_n\mathcal A_{\rm PM}n.
\tag{16a}
\]

Here \(B\) is dimensionless STF anisotropy, the dot is cosmic proper time, and \(D=a_oc\int dt/a\) is the supplied distance. The selected 102×102 cached Gram preserves the complete common five-component E2 response and its nuisance cross blocks. With six common spin/glide nuisance parameters, its information eigenvalues are approximately \(2.43693,2.65563,3.17145,3.67145,4.95102\) in \((\mu\mathrm{as}/\mathrm{yr})^{-2}\). Profiling all 97 non-E2 columns leaves five positive eigenvalues \(0.503015,0.629927,1.13946,1.46083,2.38294\). Under the stipulated working Gaussian law, the primary best/worst 80% power radii are 1.60963 and 2.29431 \(\mu\mathrm{as}/\mathrm{yr}\) at size 0.05. These are already calculated selected-design sensitivities, not a proposed future forecast.

For a common distance, write \(q=(B_o-B_s)/T_{\rm ref}\), \(s=\dot B_o\), \(k=2cT_{\rm ref}/D\). The ten-parameter history map \(\mathcal A_{\rm PM}=kq-s\) has rank five and kernel \(\delta s=k\delta q\). Tensorization retains the five observable combinations and their sign; it does not split endpoint history and present shear without another response or a declared family. In the nearby affine limit Eq. (16a) tends to \(+\Sigma\); when the endpoint term is negligible it tends to \(-\dot B_o\). Preserving sign and distance dependence is physically consequential here. The latest branch's formal status is qualified conditional response; it does not supply the missing centroid-to-matter, depth/history or empirical spatial-covariance model.

The qualified R36-05 product also already performs the exact-versus-linear radiation comparison on common synthetic inputs. In its \(a=0,\beta=0.00123\) case, exact and linear physical-target coverage of \(\mathscr D\) are 94.53% and 74.10%; the corresponding rest-stress coverage is 95.56% and 37.72%. At \(\beta=0.3\), the exact coverage remains near 95% while the linear physical-target coverage is zero. Each case used 4,096 independent test skies after 8,191 calibration skies. The linear adapter still covers its own approximate target near 95%, identifying forward-map bias as the cause. This demonstrates a real methods advantage of preserving the nonlinear physical adapter under its authored input law. It is neither a generic advantage over optimal GLS nor an empirical Planck interval. Its rank-4 moment reconstruction preserves the full operator to \(3.34\times10^{-16}\rho_0\), although unresolved angular entropy remains positive. This existing result should be central to the foundation argument rather than rediscovered in another toy experiment.

## 6. Likelihood, morphology factors and the FLRW question

There are two distinct carriers: measured \(x_{\rm obs}=T(Y)\), and normalized parameter \(x_{\rm kin}\) in Eq. (5). Their relation is the forward law. For a transformation independent of unknown parameters, its induced law is the pushforward of the original data law. Tensorization preserves information only when the chosen carrier preserves the responses needed by the physical question. It does not manufacture a likelihood for unknown derivatives or restore information lost before ingestion.

The proposed five-object interpretation is therefore:

- **\(x\):** a typed joint carrier, including signed tensors and the response-relevant nuisance dependence.
- **\(F\):** the directional geometry of the physical feasible/confidence image. The support profile in Eq. (11) is a concrete example. Occupancy under a measure is a different, explicitly labelled definition.
- **\(Q\):** distance or gauge relative to a declared reference body. The zero-FLRW set is not a nonzero denominator; a MES body is one conditional scale reference.
- **\(\Pi\):** probability of a specified finite event under the named sampling, null or posterior law. With a continuous posterior, \(P(\theta\ne0\mid Y)=1\) almost automatically; useful targets are finite-tolerance exceedance, exclusion of the null from a joint confidence set, or explicitly defined model odds.
- **\(G_F\):** how the same physical quantities and support geometry vary with depth, with cross-bin covariance, frame transport and source evolution retained. Independent binwise fits do not determine a joint depth process.

A useful practical output is a collection of named constraints,
\(\|\Sigma\|/H\), \(\|\Omega\|/H\), \(\|A\|/(cH)\), \(\|\beta_{RM}\|\), together with the joint confidence region and response assumptions. A single weighted sum can summarize a declared task, but there is no canonical universal scalar “distance from FLRW” supplied by these four quantities.

For Bianchi comparison, let \(\mathcal M_k\) be the set of physical states or forward responses admitted by a specified model family, with constraints and equivalent presentations handled. A confidence-qualified compatibility set is

\[
\mathcal K_\alpha(Y)=\{k:\Theta_\alpha(Y)\cap\mathcal M_k\ne\varnothing\}.
\tag{17}
\]

This can exclude inconsistent families when the common physical response is supplied. It does not assign a Bianchi label from a morphology axis. The reused II/VII\(_0\) initial-data witness explicitly shows why shear, expansion and scalar curvature alone need not identify a homogeneous spatial geometry: their spatial-Ricci spectra can differ while those quantities agree. Geometry compatibility can be computed now; a CMB family classification additionally consumes its qualified transfer output.

## 7. What has advanced and what should be executed next

| Scientific product | Present status | Smallest useful next input or calculation |
|---|---|---|
| MES-scaled physical coordinates | Defined with corrected units and vector/tensor normalization | Carry derivative assumptions and same-data anchor covariance into the statistical contract. |
| Brightness-to-shear response | Existing exact positive 5D operator, finite-error inverse; directional support image derived here | Export 0/2/4 moment response and its spectrum; sweep physically declared derivative budgets rather than waiting for every external history. |
| Radiation-rest stress anisotropy | Existing exact physical null independent of transport evolution | Apply a joint calibrated intensity moment region, including spectral/foreground completion, to Eq. (14). |
| Optical kinematics | Existing local radial/transverse algebra and joint inversion | Supply a catalogue-specific source/clock/frame adapter and finite-distance remainder. |
| Gaia compression comparison | Latest qualified full-five E2 history response and selected 102D Gram sensitivity already available | Compare compression on that physical response as well as the older 24D E1/B1 law; keep the rank-five history combination distinct from its ten input parameters. |
| Bianchi discrimination | Algebraic compatibility and ambiguity witnesses ready | Use qualified curvature/transfer subsets; report a compatibility set and the extra observable separating surviving models. |

The most valuable foundation result is not a claim that a tensor always beats an optimal scalar score. It is the explicit statement of **which physical response is preserved**, followed by a comparator at equal data, nuisance and uncertainty. The radiation operator provides an exact finite sufficient moment subspace; the optical inverse provides a finite signed response; the Gaia experiment tests the inferential consequences of compression. Together these reconnect the user's original physical programme without claiming an empirical kinematic detection from morphology alone.

## 8. Source and calculation audit

The attached `project_sources/20-report-1-.pdf` was extracted and read around its MES, identified-set and five-factor definitions. K1R, Loop A and Loop C were read from pinned source files. The parent-supplied R36 internal integration and current R36-03/R36-05 interpretations plus formal publication status were read for the latest stress, optical, geometric and PM advances. The immutable candidate prose still says review pending; the later identity-bound publication files record qualification. No earlier proof or numerical result is relabelled a new result here.

Primary documents inspected: MES [1995 paper](https://arxiv.org/pdf/astro-ph/9501016); MES [1996 letter](https://arxiv.org/pdf/astro-ph/9510126), especially Eqs. (6)–(7); Stoeger–Araujo–Gebbie [corrected COBE application](https://arxiv.org/pdf/astro-ph/9904346), Eqs. (3)–(4), (15)–(16); Maartens–Gebbie–Ellis [nonlinear hierarchy](https://arxiv.org/abs/astro-ph/9808163), used with the retained Loop A derivation and source-coefficient audit.

The archived 1995 preprint text extraction displays a quadrupole gradient coefficient `2` in Eq. (14), while its moment definitions and hierarchy give `2/5`. This pass did not establish a journal erratum. The implementation coefficient was checked directly: the dipole contribution to the raw third moment is \((\delta_{ij}q_k+\delta_{ik}q_j+\delta_{jk}q_i)/5\), whose STF divergence is \((2/5)D_{\langle i}q_{j\rangle}\). Exact Wolfram evaluation returned a zero 3×3 residual. Historical MES norm bounds are retained as stated in their source, not silently recomputed from this transcription issue. The separate `2/7` versus `10/7` shear–stress discrepancy was already resolved by the retained Loop A angular derivation.

One Wolfram attempt failed because the assigned matrix symbol was also used as its own array head. The repaired call changed only the local variable names and returned the expected zero matrix and rational coefficients. Both receipts are preserved; the failed attempt is not counted as a verification. SymPy was unavailable; the independent normalization check used Python's exact `fractions` module. No xAct execution is claimed in this lane.

New result scope: Eqs. (5), (11)–(12) and their placement in the original physical inference objective are a constructive foundation/inference specification. The support-image lemma is elementary linear/convex geometry, not a claim of new general mathematics. Empirical inputs and all original acceptance counts are unchanged.
