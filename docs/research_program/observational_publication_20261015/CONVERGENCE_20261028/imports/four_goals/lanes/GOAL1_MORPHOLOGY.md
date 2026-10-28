# Goal 1 — Low-multipole morphology, polarization and a response-preserving MES bridge

28 October 2026. Internal constructive theory unit; no push, catalogue fit, hierarchy evolution or ODE solve.

## Scientific outcome

The useful extension is a joint response carrier, rather than an unrestricted enlargement of the state. The cold-electron Thomson **gain** depends on nine real integrated polarization components, while the instantaneous radiation-to-shear operator depends on fifteen intensity components of angular degrees 0, 2 and 4. A carrier sufficient for one of these physical questions is not sufficient for the other. Their generic joint real-linear carrier has dimension 23; if circular polarization is excluded by the declared model and measurement question, the corresponding dimension is 20.

This makes the original low-multipole programme concrete. Preserve the intensity moments that act on shear, and preserve only those polarization moments that enter the collision residual or the selected detectors. Then map a joint observational confidence event through the known instantaneous operator and an explicit derivative/remainder allowance. The matrix description adds a calculable polarized collision correction; it does not replace an unmeasured transport derivative with morphology.

The numerical experiment below verifies an exact counterexample: two positive skies have identical Thomson-scattered output, yet different shear-response operators. It also verifies the 23-dimensional union and the detector ranks, and calculates a finite shear bias from omitting linear polarization.

## Sources, scope and conventions

Applied skill context: PhysMath 1.3.0 selected R2/R3/R4/R5/R7/R9 definitions and integrated policies in `WORK_PACKET.md`; one production/check pass, followed by the parent's integrated independent review. No recursive delegation.

Sources actually read:

- MF02 attached PDF, pp. 28–30, §1.10, especially (1.10.1), (1.10.5)–(1.10.9), (1.10.17), (1.10.20); pp. 53–54, §2.5; p. 120, Proposition 10.6.1 and (10.6.2)–(10.6.3). Its gain spectrum is reused, not relabelled as a new result.
- Prior `MES_FOUNDATION.md`, §4: the exact five-dimensional positive shear operator and finite inverse-error bound. Current R36-05 interpretation and publication status, pinned at `7f3f49a6b6d95b6ae0323d5bebd3afce0067b1a7`: the nonlinear temperature-to-radiation adapter and exact rank-4 response preservation.
- Anthony Challinor, *Microwave background polarization in cosmological models*, Phys. Rev. D 62, 043004 (2000), arXiv:astro-ph/9911481. The user's supplied journal PDF was read at p. 043004-5, Eq. (3.7) and its explanatory paragraphs. It gives the intensity/E-quadrupole and circular-dipole Thomson source structure, including the separation of circular polarization. Exa and SciSpace retrievals identified and cross-checked the primary paper.
- Cyril Pitrou, *The radiative transfer at second order: a full treatment of the Boltzmann equation with polarization*, arXiv:0809.3036, primary abstract read through Exa. It locates the extension beyond the cold rest-frame model; its full second-order coefficients are not used here.
- Kamionkowski and Loeb, *Getting Around Cosmic Variance*, Phys. Rev. D 56, 4511 (1997), arXiv:astro-ph/9703118, primary text through Exa. Cluster Thomson polarization probes two projected components of the remote quadrupole, providing a prospective extra source rather than all five components at each event.

Work in one electron rest frame with $g=(-,+,+,+)$, cold unpolarized electrons, negligible recoil, and photon energy much below $m_ec^2$. The Thomson map is energy diagonal in this frame. It therefore also acts on bolometric brightness provided the same energy weights are used. Let $n$ be the photon propagation direction and $P_n=I_3-nn^T$. The Hermitian screen brightness $\mathsf F(n)$ satisfies

\[
\mathsf F=P_n\mathsf F P_n,\qquad \mathsf F\succeq0,\qquad I(n)=\operatorname{tr}\mathsf F(n).
\]

In an oriented real screen basis the convention is

\[
f=\frac12\begin{pmatrix}I+Q&U-iV\\U+iV&I-Q\end{pmatrix}.
\]

$Q\pm iU$ have spin weights $\pm2$; $I,V$ have spin weight zero, with their distinct parity. Spatial rotations act on the embedded screen tensor. A passive screen-basis change transforms state and detector components together and leaves their pairing unchanged. An actual observer boost changes energy and direction and must be included in the forward map. The finite carrier below is qualified to the stated frame.

## 1. What one Thomson-scattered component preserves

Define

\[
M=\int\mathsf F(n')\,d\Omega',\quad
(\mathscr G\mathsf F)(n)=\frac{3}{8\pi}P_n M P_n,
\quad C_T[\mathsf F]=\gamma_T(\mathscr G\mathsf F-\mathsf F),
\qquad\gamma_T=n_e\sigma_Tc.
\]

The map $\mathscr G$ factors through the nine-real-dimensional Hermitian matrix $M$. This is the exact scattered gain, not a nine-dimensional closure of the full collision operator: the loss term retains the incident angular field. An observed direct-plus-scattered sky also contains the direct term and its higher multipoles.

Write $M=aI_3+S+iA$, where $S$ is real symmetric trace-free and $A$ is real antisymmetric. Isotropic angular integration gives

\[
\frac{3}{8\pi}\int P_nMP_n\,d\Omega
=\frac35M+\frac1{10}M^T+\frac1{10}\operatorname{tr}(M)I_3.
\]

Thus the scalar, real STF and imaginary-antisymmetric pieces have multipliers $1,7/10,1/2$, with dimensions $1,5,3$. This reproduces MF02 Proposition 10.6.1. The image contains an intensity monopole, a linked intensity/E quadrupole, and a circular-polarization dipole. It has no independently generated B-mode source in this rest-frame Thomson limit. The separation is consistent with Challinor Eq. (3.7).

For a detector effect $R_j=P_{n_j}R_jP_{n_j}\succeq0$, its scattered signal is

\[
y_j=\operatorname{tr}[R_j(\mathscr G\mathsf F)(n_j)]
=\frac3{8\pi}\operatorname{tr}(B_jM),\qquad B_j=P_{n_j}R_jP_{n_j}.
\]

Only the span of the actual $B_j$'s is identifiable. Intensity effects and real linear-polarizer effects are blind to the imaginary antisymmetric part. Full Stokes effects can access it. The executed designs give ranks 6, 6 and 9, respectively. Nine stored matrix components therefore do not imply nine observed components.

An omitted matrix component has a direct detector error budget:

\[
|\delta y_j|\le\frac3{8\pi}\|B_j\|_F\|\delta M\|_F.
\]

With a specified joint Gaussian channel law $y\sim N(A m+N\eta,C)$, the identifiable physical directions are the image of $C^{-1/2}A$ orthogonal to $C^{-1/2}N$. This is the standard linear inverse/efficient-score construction applied to a physically explicit detector map, and does not require the full angular field to be retained for that one question.

## 2. A sufficient scattering carrier can erase kinematic information

For unpolarized radiation, $\mathsf F=IP_n/2$, define

\[
\rho=\int I\,d\Omega,\qquad
\pi=\int I(nn^T-I_3/3)\,d\Omega.
\]

Then $M=\rho I_3/3-\pi/2$. The scattered gain knows intensity degrees 0 and 2, and nothing of a pure degree-4 perturbation. In contrast, the prior exact radiation response is

\[
\mathcal L_I X=\frac{8\rho}{15}X+
\frac{10}{7}\operatorname{STF}(X\pi)-H_4:X,
\]

with the equivalent quadratic form

\[
\langle X,\mathcal L_I X\rangle
=\int I(n)\{2|Xn|^2-(n^TXn)^2\}\,d\Omega.
\]

Take $I_\pm(n)=1\pm0.6P_4(n_z)$. Both are everywhere positive, bounded below by 0.4. Orthogonality gives $M_+=M_-$, hence identical scattered output at every direction and detector. Their degree-4 moment differs, so $\mathcal L_{I_+}\ne\mathcal L_{I_-}$. The quadrature gives

\[
\|M_+-M_-\|_F=1.20\times10^{-13},\quad
\max_n\|\mathscr G\mathsf F_+-\mathscr G\mathsf F_-\|_{\max}
=1.41\times10^{-14},
\]

while

\[
\|\mathcal L_{I_+}-\mathcal L_{I_-}\|_{\rm op}=0.5744626567
\]

in the declared brightness units. This is a response-specific counterexample, not a claim that all scattering destroys all geometric information. It shows why a physical question must be fixed before using the gain's minimal carrier as the whole kinematic carrier.

## 3. The common carrier for scattering and the shear operator

Decompose the incident screen field into its unpolarized trace part, real trace-free linear-polarization part $\mathsf P_L(n)$, and circular part. Set

\[
P_* =\operatorname{STF}\operatorname{Re}\int\mathsf P_L(n)\,d\Omega,
\qquad A_* =\operatorname{Im}M.
\]

For the pair of exact outputs $(\mathscr G\mathsf F,\mathcal L_I)$, a common carrier is

\[
x_{\rm pair}=(\rho,\pi,H_4,P_*,A_*),
\qquad \dim=1+5+9+5+3=23.
\]

**Finite-dimensional statement.** On a neighbourhood of a positive unpolarized isotropic screen field, this is a minimal real-linear carrier for preserving all gain outputs and the entire five-dimensional shear operator.

**Proof.** The gain is fixed by $M=\rho I_3/3-\pi/2+P_*+iA_*$. The shear operator is fixed by $(\rho,\pi,H_4)$. The latter map is injective: the symmetric operators on STF rank 2 decompose into angular representations of degrees $0,2,4$, and each coefficient in $\mathcal L_I$ is nonzero. Equivalently, its invariant trace fixes $\rho$, its degree-2 component fixes $\pi$, and its degree-4 component fixes $H_4$. Once these fifteen quantities are fixed, the real STF and imaginary antisymmetric parts of $M$ fix the remaining eight. Small real-linear perturbations spanning these directions remain positive on the physical two-dimensional screen around a strictly positive reference, so positivity does not lower the local rank. The executed 24-by-23 response matrix has rank 23 and smallest singular value 0.5649300 in its declared, unnormalized coordinate basis. This numerical rank verifies the concrete bases; the representation argument proves the dimension.

If the model restricts $V=0$ and only intensity/linear polarization and shear are targets, the unnecessary three circular components can be omitted: the corresponding carrier has dimension 20. For an unpolarized incident family it has dimension 15. These are exact response preservation statements, not claims that those many coefficients have already been measured, nor that every component of the transport residual is present.

The shear operator is blind to all intensity degrees above 4. The scattered gain is blind to many more angular details. Consequently an angular-entropy residual can be nonzero while the selected physical responses are preserved exactly, consistent with the already executed R36-05 result.

## 4. A polarized collision correction to the MES inverse

Taking the intensity trace of the gain and integrating its quadrupole gives

\[
C_\pi=\gamma_T\left[-\pi-\frac15\operatorname{STF}\operatorname{Re}M\right]
=-\gamma_T\left(\frac9{10}\pi+\frac15P_*\right).
\]

To see the coefficient directly, $\operatorname{tr}(P_nMP_n)=\operatorname{tr}M-n^T\operatorname{Re}Mn$, and

\[
\int n_{\langle a}n_{b\rangle}n_cn_d\,d\Omega
=\frac{8\pi}{15}\delta_{c\langle a}\delta_{b\rangle d}.
\]

The unpolarized limit yields the familiar $9\gamma_T/10$ intensity-quadrupole damping. Here $P_*$ is an explicitly integrated screen tensor, not an unannounced identification with a convention-dependent $E_{ab}$ coefficient.

In the same geodesic/irrotational congruence used for the prior radiation inverse, write the noncollision derivative combination as $R_\tau$. The source equation becomes

\[
\mathcal L_I\Sigma=-(R_\tau-C_\pi).
\]

Thus a polarized collision estimate is an additive source correction in the existing physical inverse. Holding the same $I,R_\tau,\gamma_T$, ignoring $P_*$ shifts the inferred shear by

\[
\Sigma_{\rm true}-\Sigma_{\rm unpol}
=-\frac{\gamma_T}{5}\mathcal L_I^{-1}P_*,
\quad
\|\Sigma_{\rm true}-\Sigma_{\rm unpol}\|_F
\le\frac{\gamma_T}{5\lambda_{\min}(\mathcal L_I)}\|P_*\|_F.
\]

The finite experiment uses a positive screen field $P_n/2+0.12[P_nS_1P_n-\tfrac12P_n\operatorname{tr}(P_nS_1P_n)]$. Its smallest physical screen eigenvalue is 0.41563. The collision quadrupole identity has residual $1.74\times10^{-14}$. With $\gamma_T=0.4$ in the declared toy time unit, the omitted-polarization shear shift has norm 0.0072 and attains the stated bound because the intensity is isotropic. This is a physical approximation-error test under a fully specified source law, not a sky detection.

For uncertain quantities, include this correction in the same joint source event. If $\|\delta\mathcal L\|_{\rm op}\le\epsilon_L$, the uncertainty of the noncollision residual is $\epsilon_R$, and the uncertainty of $P_*$ is $\epsilon_P$, then for fixed $\gamma_T$

\[
\|\Sigma-\widehat\Sigma\|_F
\le\frac{\epsilon_R+\gamma_T\epsilon_P/5+
\epsilon_L\|\widehat\Sigma\|_F+\epsilon_{\rm other}}
{\widehat\lambda-\epsilon_L},\qquad\widehat\lambda>\epsilon_L.
\]

Here $\epsilon_{\rm other}$ explicitly includes uncertainty of the intensity-quadrupole collision term, optical-depth/rate calibration, frame conversion and any declared neglected source. Correlated uncertainties can be propagated more tightly from their common set rather than replacing it by separate balls. In particular, the parent’s `JOINT_REMAINDER.md` constructs a detector-projected error Gram that retains cancellation between derivative, collision and transfer errors; it can replace this conservative sum of radii when the common primitive error set is supplied.

## 5. How the five factors serve the original purpose

- $x$ retains the joint response carrier, or the smaller measured quotient selected by actual detector effects and nuisance. It also records the separate differentiated moments needed by $R_\tau$, when supplied.
- $F$ is the directional support of the resulting physical shear/confidence image; the support direction can be chosen by a detector or a specified shear mode.
- $Q$ uses a fixed, dimensionally consistent reference body. Positivity and causal constraints remain physical-domain conditions; a positive cone alone is not an absorbing bounded Minkowski reference body.
- $\Pi$ is a sampling/posterior probability under the common calibrated channel law. Stokes positivity, detector probability and confidence coverage are different statements.
- $G_F$ retains frame/screen comparison, sky masks and cross-window covariance. Repeated maps of one sky do not supply independent physical depths, and a passive basis rotation does not generate physical B modes.

This construction can produce a tensor-valued physical identified set now, parametrized by the remaining derivative allowance. It can also quantify the error incurred by an unpolarized or rank-2 approximation before making any observed-shear claim.

## 6. Concrete next unit and observation contract

The shortest useful application is **a joint T/E radiation-source sensitivity image**: retain the calibrated bolometric intensity degrees 0, 2 and 4, the incident linear-polarization contribution $P_*$, and their joint covariance; compute $\mathcal L_I$, $C_\pi$, and the shear support curve against a declared $R_\tau$ allowance. Use the current exact R36 temperature-to-intensity adapter and its positive moment response instead of refitting or discarding it. An intensity-only baseline gets the same source assumptions and is compared through the explicit omission-bias formula above.

The required data are signed temperature/intensity and Q/U channels with bandpass, unit, beam, mask and joint processing covariance; an energy/spectral completion if bolometric intensity is needed; and the electron/rest-frame and collision-rate model for the selected source. An E-mode sky alone does not supply these intensity moments. Stokes V is needed only if the circular response is itself a target.

For a later derivative-source programme, remote-quadrupole polarization is a meaningful external route. A single cluster measures only two projected quadrupole combinations. Distinct clusters occupy different spacetime events, and redshift differentiation along a light cone is not automatically a proper-time derivative at fixed spatial point. The proper target is therefore the identifiable combination of remote moments under a specified space/time response, with optical depth, peculiar motion and selection nuisance retained. This extends the source information constructively without calling unobserved derivatives measured or requiring a native Boltzmann solver for the current conditional response result.

## Numerical evidence and claim status

`code/goal1_thomson_response.py` executes 968-point spherical quadrature, exact finite detector-rank construction, the response-union rank, positive-sky counterexample and the polarized collision-bias test. `lanes/GOAL1_NUMERICS.json` records all numbers. `figures/goal1_thomson_carrier.{png,pdf}` presents the positive skies, unequal shear spectra and actual detector ranks. First execution completed all numerical assertions but hit a Matplotlib legend syntax error; the label-only repair is recorded in `GOAL1_EXECUTION_NOTE.txt`, and the second execution completed.

Reused/established: cold Thomson kernel and spectrum, polarization selection rules, the exact MES/HTT radiation operator, linear inverse identifiability. Derived here as a research application: the explicit pair-response counterexample, the common 23/20-component carrier statement and the polarization-induced shear-error budget in the retained framework. These are candidate application contributions; their generic linear-algebra structure is not asserted as a new universal theorem or as a completed empirical FLRW exclusion.
