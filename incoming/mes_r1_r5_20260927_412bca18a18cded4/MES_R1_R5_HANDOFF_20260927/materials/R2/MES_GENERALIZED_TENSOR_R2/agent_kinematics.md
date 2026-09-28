# Class-independent kinematic optical response: author derivation for R2

Status: **derived; selected local identities numerically checked**. This is candidate-author work, not an independent decision gate. It gives conditional local inverse problems and exact frame transformations. It does not establish observed cosmological kinematics, global Einstein-matter realizability, or a universal almost-FLRW theorem.

Scope follows the current user request. No repository prior research was read. The supplied Ellis–Maartens–MacCallum book and the explicitly authorized R1 shear-block derivation were consulted. The local Astra harness PROJECT_INSTRUCTIONS and physics/math validation phase were read. VIGILODE is not an input or requirement.

## 1. Conventions and dimensions

Use signature \((-+++)\), a future-directed physical four-velocity \(U^aU_a=-c^2\), and \(u^a=U^a/c\). Its rest projector is \(h_{ab}=g_{ab}+U_aU_b/c^2\). Fix a right-handed observer triad, \(\epsilon_{123}=+1\), and define

\[
\nabla_a U_b=-{U_aA_b\over c^2}+Hh_{ab}+\sigma_{ab}+\omega_{ab},
\quad H={\theta\over3},\quad A_b=U^a\nabla_aU_b,
\quad\omega_{ab}=D_{[a}U_{b]},\quad
\Omega^a={1\over2}\epsilon^{abc}\omega_{bc}.
\]

Thus \(\Omega\) is the familiar positive angular-velocity vector for an infinitesimally rigidly rotating congruence in Minkowski space: \(\Omega=(\operatorname{curl}v)/2\). Set \(a^a=A^a/c\), \(S_{ab}=\sigma_{ab}\). All entries of \((H,a,S,\Omega)\) have units s^-1. The full acceleration \(A\) has units m s^-2; \(\beta\) below is dimensionless.

**Ellis sign adapter:** the supplied book, p.82 Eq.(4.34), defines its vorticity vector as \(\omega_{\rm Ellis}=-\operatorname{curl}(u)/2\). Restoring units, our \(\Omega\) is minus the book's physical vorticity vector. Its tensor definition also reverses the antisymmetric derivative indices. Its Eqs.(5.79–5.80) agree with the formulas below after this adapter. Keeping the name \(\Omega\) prevents an unmarked sign change in the toroidal block. Norm bounds on vorticity are unaffected; signed morphology is affected.

Photons have propagation direction \(e^ae_a=1\), \(e^aU_a=0\), and

\[
p^a={E\over c^2}(U^a+ce^a),\qquad E=-p_aU^a>0.
\]

The observed outward direction on the sky is often \(n=-e\); every odd multipole and dipolar formula must be transformed consistently. Define the derivative along the photon ray, normalized to local observer time,

\[
\mathscr D=(U^a+ce^a)\nabla_a.
\]

This is not the time derivative along a fixed observer worldline and not the derivative between repeat observations of one source.

## 2. Exact local photon equations, with no Bianchi or weak-anisotropy assumption

From \(p^b\nabla_bp^a=0\),

\[
\boxed{\mathscr D\ln E=-R(e)},\qquad
\boxed{R(e)=H+a\cdot e+S:ee}.
\]

To see the factors of \(c\), contract the velocity-gradient decomposition with \((U+ce)^a(U+ce)^b/c^2\). The antisymmetric tensor disappears because the contraction is symmetric. The acceleration term contributes \(A\cdot e/c\), and the symmetric spatial terms give \(H+S:ee\).

Let \(P_e=h-ee\). The same geodesic equation gives

\[
\boxed{V^a(e):=h^a{}_b\mathscr D e^b
=-P_e{}^a{}_b(a^b+S^b{}_ce^c)-(\Omega\times e)^a}.
\]

The full derivative is \(\mathscr D e^a=R u^a+V^a\). Hence \(e\cdot V=0\), \(\mathscr D(e\cdot e)=0\), and \(\mathscr D(u\cdot e)=0\), as required. Isotropic expansion cancels from the spatial angular rate. Neither Einstein's equation nor a matter closure was used.

In an orthonormal triad \(E_i\), define the spatial triad-rotation matrix along a spacetime vector \(X\) by \(\Gamma(X)^i{}_j=E^i\cdot\nabla_X E_j\). Then the numerical angular-coordinate generator is

\[
{d e^i\over d\tau_{\rm ray}}
=V^i-\left[\Gamma(U)+c e^k\Gamma(E_k)\right]^i{}_j e^j.
\]

The matrix in brackets is antisymmetric on spatial indices. Its first part is the chosen triad's rotation relative to gyroscopes; its second part is a spatial connection along the ray. Dropping it without declaring a frame would conflate vorticity with coordinate rotation. The coordinate generator is not observed source proper motion. Proper motion needs endpoint worldlines, the connecting null family, and the observer's physical screen/reference frame.

For an actual connecting null ray, parameterized by \(dx^a/d\tau_{\rm ray}=U^a+ce^a\),

\[
\ln(1+z)=\int_{\rm emitter}^{\rm observer}R(e,x)\,d\tau_{\rm ray}.
\]

An observed finite redshift gives this integral, not its local integrand. Even an exactly known integral does not identify the local shear, acceleration, or expansion without additional structure.

## 3. A complete local optical target and a bounded inverse

Let \(\langle f\rangle=(4\pi)^{-1}\int_{S^2}f\,d\Omega\) and \(E_{ij}(e)=e_ie_j-\delta_{ij}/3\). Sphere moment identities give the exact inverses

\[
\boxed{H=\langle R\rangle,\quad a=3\langle eR\rangle,
\quad S={15\over2}\langle ER\rangle,
\quad\Omega=-{3\over2}\langle e\times V\rangle.}
\]

Angular data alone also give

\[
a=-{3\over2}\langle V\rangle,\qquad
S_{ij}=-5\langle e_{\langle i}V_{j\rangle}\rangle.
\]

Thus \(k=(H,a,S,\Omega)\mapsto(R,V)\) is an injective linear map from the 12-dimensional local kinematic space into a finite angular subspace. \(R\) alone has precisely the three-dimensional vorticity kernel. \(V\) alone has precisely the one-dimensional expansion kernel. This is an exact statement about ideal **local ray data**, not an identification result from a static CMB map.

The angular decomposition is especially transparent:

\[
V=-\nabla_{S^2}(a\cdot e)-{1\over2}\nabla_{S^2}(S:ee)
 +e\times\nabla_{S^2}(\Omega\cdot e).
\]

The acceleration is a polar/gradient \(\ell=1\) sector, shear a gradient \(\ell=2\) sector, and vorticity an axial/toroidal \(\ell=1\) sector. Expansion has no angular sector. For scalar curl defined by the usual outward sphere orientation,

\[
\operatorname{div}_{S^2}V=2a\cdot e+3S:ee,
\quad \operatorname{curl}_{S^2}V=-2\Omega\cdot e.
\]

The finite-dimensional image is orthogonal in the following sense:

\[
\langle R^2\rangle=H^2+{1\over3}|a|^2+{2\over15}\|S\|_F^2,
\]
\[
\langle |V|^2\rangle={2\over3}|a|^2+{1\over5}\|S\|_F^2+{2\over3}|\Omega|^2.
\]

For noisy functions \((R+\delta R,V+\delta V)\), use the equal-weight product norm \(\|(\delta R,\delta V)\|^2=\langle\delta R^2+|\delta V|^2\rangle\). The Moore–Penrose/least-squares reconstruction is

\[
\hat H=\langle R\rangle,\quad
\hat a=\langle eR-V\rangle,\quad
\hat S_{ij}=3\langle E_{ij}R-e_{\langle i}V_{j\rangle}\rangle,
\quad\hat\Omega=-{3\over2}\langle e\times V\rangle.
\]

For the parameter norm \(H^2+|a|^2+\|S\|_F^2+|\Omega|^2\), the squared singular values by sector are \(1,1,1/3,2/3\). Consequently

\[
\boxed{\|\delta k\|\le\sqrt3\,\|(\delta R,\delta V)\|.}
\]

Separately, the redshift-only inverse has error constants \(1,\sqrt3,\sqrt{15/2}\) for \(H,a,S\), respectively; the direction-only inverse has constants \(\sqrt{3/2},\sqrt5,\sqrt{3/2}\) for \(a,S,\Omega\). These are operator-norm bounds for arbitrary square-integrable perturbations and require no angular derivatives of noisy data. The equal scalar/vector weighting is a mathematical convention, not a universal observational fairness measure; actual likelihoods must use the actual joint covariance and transfer functions.

This theorem gives a useful prospective generalized \(T_{A_n}\): the covariant finite collection of scalar \(\ell=0,1,2\) coefficients of \(R\) and gradient/toroidal coefficients of \(V\). It does not pretend that \(T_{\ell m}(a_{\ell m}^{X},z)\) is currently observable without the missing optical derivative information.

## 4. Exact all-kinematics weak Boltzmann block

Let \(B(x,e)\ge0\) be bolometric energy density per solid angle, in J m^-3 sr^-1, obtained from the energy moment \(\int E^3f\,dE\). Require the endpoint term \(E^4 f\to0\) at both energy boundaries. The kinetic equation in a covariant/horizontal direction convention is

\[
\mathscr D_{\rm hor} B+\mathcal A_kB=\mathcal C,
\qquad
\mathcal A_kB=-[P_e(a+Se)+\Omega\times e]\cdot\nabla_{S^2}B
 +4[H+S:ee+a\cdot e]B.
\]

The coefficient 4 is from integrating \(-R E\partial_Ef\) by parts. This bolometric identity does not assume a Planck spectrum; identifying \(B=a_RT(e)^4/(4\pi)\) does assume a directionwise blackbody, with \(a_R=\pi^2k_B^4/(15\hbar^3c^3)\). General polarized transport additionally has the screen-basis connection; a scalar intensity derivation cannot silently certify that spin-2 operator.

For any smooth angular test tensor \(\psi(e)\), integration by parts gives

\[
\boxed{\int\psi\,\mathcal A_kB\,d\Omega
=\int B\{[P_e(a+Se)+\Omega\times e]\cdot\nabla_{S^2}\psi
 +(4H+S:ee+2a\cdot e)\psi\}\,d\Omega.}
\]

Here \(\operatorname{div}_{S^2}P_ea=-2a\cdot e\), \(\operatorname{div}_{S^2}P_eSe=-3S:ee\), and the rotation field has zero divergence. The formula is also valid weakly for angular positive measures when the test function and all moments exist.

For \(\psi_{A_\ell}=e_{\langle A_\ell\rangle}\), take the **homogeneous STF polynomial extension** to ambient \(\mathbb R^3\). Euler's identity then yields

\[
\boxed{J_{A_\ell}(k)=\int B\left\{(a+Se+\Omega\times e)\cdot\partial_e\psi_{A_\ell}
 +[4H+(1-\ell)S:ee+(2-\ell)a\cdot e]\psi_{A_\ell}\right\}d\Omega.}
\]

Using an arbitrary off-sphere extension, or confusing \(\partial_e\) with \(\nabla_{S^2}\), changes the apparent coefficients. The previous equation in purely sphere notation avoids that ambiguity.

Define \(M_r=\int Be^{\otimes r}d\Omega\), \(\rho=M_0\), and \(\Pi=M_2-\rho I/3\). Let \(R_\Omega v=\Omega\times v\). The first three blocks are

\[
J_0=4H\rho+S:M_2+2a\cdot M_1,
\]
\[
J_1=4HM_1+SM_1+\Omega\times M_1+(\rho I+M_2)a,
\]
\[
\boxed{J_2=4H\Pi+\mathcal L_B(S)+2a_{\langle i}M_{1j\rangle}
 +[R_\Omega,M_2],}
\]
\[
\mathcal L_B(S)=SM_2+M_2S-M_4:S-{I\over3}(S:M_2).
\]

These retain all signed components. The \(\ell=2\) coupling to the acceleration octupole cancels exactly, because \(2-\ell=0\). Vorticity acts within a fixed \(\ell\) by its rotation representation; acceleration uses \(\ell\pm1\), and shear uses \(\ell,\ell\pm2\). The supplied Ellis book states these general couplings after Eq.(5.84), p.106.

Writing \(r_\ell=\int\psi_\ell(\mathcal C-\mathscr D_{\rm hor}B)d\Omega\), any retained set of moments defines a joint linear feasibility relation

\[
\mathbb J_B k=r.
\]

Unknowns in \(r\), including spatial/temporal radiation derivatives, collisions, emission, and screen transfer, must remain unknown. If \(r\in\mathcal R\), the kinematic compatible set is \(\{k:\mathbb J_Bk\in\mathcal R\}\), possibly intersected with physically declared algebraic/constraint conditions. This supports joint MES-style residual bounds while exposing rank defects and morphology. Positive definiteness of the shear subblock does not imply invertibility of the full 12-column joint block.

At isotropic \(B=\rho/(4\pi)\),

\[
J_0=4\rho H,\quad J_1={4\rho\over3}a,
\quad J_2={8\rho\over15}S,
\quad J_\ell^{(\Omega)}=0\quad\hbox{for all }\ell.
\]

An isotropic radiation field has no angular texture to rotate. Thus vorticity is genuinely absent from the instantaneous radiative angular operator, even though it is present in the ideal ray-direction field \(V\). On an axisymmetric sky, rotation about the symmetry axis is also a null direction. Higher generic multipoles may lift such radiative texture nullspaces, but the missing residual problem remains.

## 5. Finite local boost versus a global tilted congruence

Let \(\beta^aU_a=0\), \(\beta^2<1\), and

\[
\widetilde U^a=\gamma(U^a+c\beta^a),\qquad
\gamma=(1-\beta^2)^{-1/2}.
\]

At one event define \(D=\gamma(1-\beta\cdot e)>0\). The exact transformations are

\[
\widetilde E=DE,\qquad
\widetilde e^a={u^a+e^a\over D}-\gamma(u^a+\beta^a),
\qquad d\widetilde\Omega=D^{-2}d\Omega,
\qquad\widetilde B(\widetilde e)=D^4B(e).
\]

For a directionwise blackbody, \(\widetilde T(\widetilde e)=DT(e)\); a boost preserves the Planck form of each ray. Frequency-dependent or polarized observables need their exact response and screen transformations. A single \(\beta\) is enough for this local transformation and for its harmonic/STF mixing.

With spatial components compared using the standard infinitesimally boosted triad, the first-order action at a fixed new sky coordinate is

\[
\delta_\beta B=P_e\beta\cdot\nabla_{S^2}B-4(\beta\cdot e)B
=-\mathcal A_{\rm acc,\beta}B.
\]

Here \(\mathcal A_{\rm acc,\beta}\) means the acceleration-shaped angular operator with its coefficient replaced by dimensionless \(\beta\), not an equation identifying \(\beta=A/c\). The first-order boost and acceleration transport have the same angular generator with opposite signs but different physical/time dimensions. A likelihood that treats both as unrelated single-sky templates may therefore introduce an artificial rank degeneracy or double count the observer's frame change. Time baselines, source-frame assumptions, and the derivative relation between observer velocity and acceleration supply the distinction.

For a **field** \(\beta(x)\), its derivatives change the physical congruence kinematics:

\[
\nabla_a\widetilde U_b
=\gamma(\nabla_aU_b+c\nabla_a\beta_b)
 +(U_b+c\beta_b)\nabla_a\gamma,
\quad\nabla_a\gamma=\gamma^3\beta^b\nabla_a\beta_b.
\]

The exact projected deformation tensor simplifies to

\[
\boxed{\widetilde K_{ab}
=\gamma\widetilde h_a{}^c\widetilde h_b{}^d
(\nabla_cU_d+c\nabla_c\beta_d),}
\]

because the derivative-of-\(\gamma\) term is parallel to \(\widetilde U_d\) and is projected out. Its trace, symmetric tracefree part, and antisymmetric part give \(\widetilde\theta,\widetilde\sigma,\widetilde\omega\). The acceleration is independently

\[
\widetilde A_b=\widetilde U^a\nabla_a\widetilde U_b.
\]

Therefore \(\beta\) at a point does not fix global tilt kinematics. In a joint model one must either use reference-congruence kinematics plus local observer \(\beta\) as a frame nuisance, or use reference geometry plus a global \(\beta\) field whose jets determine tilted kinematics. Treating all those as independent unconstrained physical fields would double count degrees of freedom.

Endpoint shifts obey

\[
\boxed{1+\widetilde z={D_s\over D_o}(1+z).}
\]

A single observer boost gives one common \(D_o(n)\) angular map for every source population before selection/frequency effects. A global tilt may give source-dependent \(D_s(x_s)\), affect the physical congruence along the ray, and alter matter/scattering source terms. But redshift variation by itself is not a universal proof of global tilt: intrinsic source velocities, selection effects, and geometrical/emission differences can mimic it. A suitable constant field or endpoint-only dataset can remain exactly degenerate with a local boost hypothesis.

## 6. General Lie algebra without a selected Bianchi type

Take an arbitrary spatially homogeneous invariant basis \(E_i\), satisfying

\[
[E_i,E_j]=C_{ij}{}^kE_k,\quad C_{ij}{}^k=-C_{ji}{}^k,
\quad C_{[ij}{}^m C_{k]m}{}^l=0.
\]

No label/type needs to be assigned. An invariant spatial metric \(g_{ij}(t)\), however, must still be given to turn the algebra into geometry. With invariant dual forms \(\omega^i\), a zero-shift representation is

\[
ds^2=-c^2N(t)^2dt^2+g_{ij}(t)\omega^i\omega^j,
\qquad d\omega^k=-\tfrac12 C_{ij}{}^k\omega^i\wedge\omega^j.
\]

The spatial connection follows from Koszul:

\[
2g(\nabla^{(3)}_{E_i}E_j,E_k)
=C_{ij}{}^l g_{lk}-C_{jk}{}^l g_{li}+C_{ki}{}^l g_{lj}.
\]

For the hypersurface normal congruence \(U_n=N^{-1}\partial_t\),

\[
K_{ij}={1\over2N}\dot g_{ij},\quad
\theta_n=g^{ij}K_{ij},\quad
\sigma^{(n)}_{ij}=K_{ij}-\theta_n g_{ij}/3,
\quad\omega_n=0,\quad A_n=c^2D\ln N=0
\]

when the homogeneous lapse has no spatial dependence. The last equalities hold for this normal congruence; a tilted matter congruence can have nonzero vorticity and acceleration even in a homogeneous geometry. Invariant components \(\beta^i(t)\) can have nonzero **covariant** spatial derivatives from the connection, although their ordinary \(E_i\) derivatives vanish.

What \(C\) alone does not supply: \(g_{ij}\), \(\dot g_{ij}\), a lapse/triad convention, tilt and its derivatives, curvature scale, stress-energy, emission/collision terms, or a globally realizable Einstein solution. Jacobi and algebraic metric/tilt data make local operators computable without a named Bianchi class. Einstein constraints and local conservation can restrict allowable jets without numerical time evolution, but they require their physical fields and boundary/initial data; they do not become predictions from the structure constants alone.

## 7. Identifiability boundary and useful no-evolution routes

For a measured static sky \(B(e)\) at one event and unrestricted spacetime radiation derivatives, any chosen \(k\) can satisfy the local Boltzmann equation by defining \(\mathscr D_{\rm hor}B=\mathcal C-\mathcal A_kB\). This is a direct local-jet degeneracy. It prevents a model-independent inference of all kinematic quantities from that sky alone. More harmonic precision does not remove an unspecified residual.

Other exact degeneracies are: redshift-rate blindness to vorticity; isotropic/axisymmetric brightness blindness to some rotations; normalized-map insensitivity to absolute expansion without amplitude/time information; and boost/intrinsic-sky degeneracy, since for every admissible \(\beta\) the exact inverse boost produces an equally positive unboosted sky.

Productive conditional routes do not require numerical ODE/PDE evolution:

1. **Analytic local-jet inversion:** parameterize finite covariant optical/radiation jets; impose actual optical, Einstein, conservation, and matter constraints algebraically; keep unresolved jets as bounded nuisance tensors. No automatic global realization is claimed.
2. **Integral endpoint constraints:** infer line-of-sight integrated kinematic functionals from redshift/temperature ratios and analytically bounded source terms; do not rename them local present-time shear or vorticity.
3. **Cross-observable/redshift likelihood:** combine CMB, redshift-distance information, repeat-observation redshift drift, astrometric direction changes, and remote-scattering dipole/quadrupole projections through their correct kernels. These can supply independent constraints on residuals and endpoint motion. A galaxy redshift shell is not a full remote CMB sky; kSZ/polarization remote signals depend on electron density, optical depth, and astrophysics and do not constitute direct unweighted local multipoles.
4. **Generic-algebra local patches:** provide \(C,g,K,\beta,\nabla\beta\) and algebraic stress/curvature constraints, evaluate the finite operators and their nullspaces, and compare the shared-data likelihood in normalized tensor space. This covers a family of classes without building a full all-Bianchi evolution solver.

## 8. Validation and source limits

The executable agent_kinematics_checks.py integrates over a 48×96 Gauss–Legendre/uniform-azimuth sphere. It verifies all inverse and norm identities, compares direct angular differentiation with the explicit \(\ell=0,1,2\) joint weak blocks for a positive non-polynomial anisotropic brightness, and verifies finite boost normalization, orthogonality, and photon reconstruction. Actual maximum errors were approximately \(5.94\times10^{-15}\) for inverse maps, \(7.77\times10^{-16}\) for norm identities, \(4.26\times10^{-14}\) for weak blocks, and \(8.88\times10^{-16}\) for boost normalization. It is an author-side bounded numerical check, not independent proof or observed-data analysis.

Primary supplied source: Ellis, Maartens & MacCallum, Relativistic Cosmology, excerpts actually read from local mes_fresh/inputs/ellis.txt: p.81 Eqs.(4.30–4.33), p.82 Eq.(4.34), pp.105–106 Eqs.(5.79–5.84), pp.293–294 Eqs.(11.50–11.57), and pp.286–287 discussion of the almost-EGS derivative assumptions. Their units and vorticity convention differ from this note and have been adapted explicitly. The exact inverse/weak-form results above are direct derivations in the declared conventions; novelty has not been surveyed.
