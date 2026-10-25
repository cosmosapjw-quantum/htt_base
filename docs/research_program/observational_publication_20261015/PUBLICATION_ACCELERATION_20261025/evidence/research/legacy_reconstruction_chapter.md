# Reconstructing the physical meaning of HTT observables

The original HTT programme sought a physical account of departure from FLRW: which observers move relative to the radiation and matter, which congruence expands or shears, and whether these differences affect measured distances and expansion rates. Its most ambitious numerical statements concerned a tilt amplitude, a fraction of an anisotropy budget, a local Hubble correction, a characteristic convergence scale and the compatibility of Bianchi geometries with the CMB. These questions remain useful. Their reconstruction begins by giving each measured quantity its own physical meaning and then connecting the quantities through a specified response.

The 215-page monograph made this ambition explicit in its four-variable programme for shear, vorticity, acceleration and tilt, and in its discussion of distance and depth dependence. The later 36-page theory report introduced the more suitable joint state and forward map,

\[
Y=M_{\rm obs}\,T_\eta[X(\cdot)]+N\nu+\epsilon.
\]

Here the physical state and its history produce radiation or distance observables; the observation operator applies the actual estimator, mask and selection; nuisance terms and measurement fluctuations complete the model. This chapter supplies analytic examples of that connection. The figure illustrates these equations with declared parameters; none of its curves is a fit to observations.

## Velocity, convergence and an observed Hubble shift

A bulk velocity describes coherent translation over a survey window. Convergence describes how neighboring trajectories approach one another. Shear describes their directional stretching. These are different features of a velocity field, and the distinction becomes measurable once directions and distances are retained.

In a local physical spatial chart, expand the peculiar velocity as

\[
v(x)=b+A x,\qquad
A=\frac{\theta}{3}I+S+\Omega,
\]

where \(\theta=\operatorname{tr}A\), \(S\) is symmetric and trace free, and \(\Omega\) is antisymmetric. For \(x=rn\), the radial velocity is

\[
v_r(n,r)=n\cdot b+r\left(\frac{\theta}{3}+n^TSn\right).
\]

Thus a direction-dependent velocity independent of radius measures the bulk vector; an isotropic term proportional to radius measures peculiar expansion; a quadrupolar term proportional to radius measures shear. Radial data have no response to solid rotation because \(n^T\Omega n=0\). Survey directions, depths and covariance determine whether the three bulk, one expansion and five shear columns can be distinguished. This is an immediate physical use of response rank and nuisance projection.

A constant bulk has zero divergence. In particular, a speed divided by a survey depth is not a measured convergence. This matters for the monograph's conversion from bulk speed to local expansion. Consider the explicit low-redshift model

\[
cz_i=Hr_i+v_r(n_i,r_i).
\]

For known distances and a weighted slope fit through the origin,

\[
\widehat H-H=
b\cdot\frac{\sum_iw_i r_i n_i}{\sum_iw_i r_i^2}
+\frac{\theta}{3}
+\frac{\sum_iw_i r_i^2 n_i^TSn_i}{\sum_iw_i r_i^2}.
\]

This equation identifies three observable contributions. A bulk contaminates the fitted slope through the sample's angular and radial imbalance. True convergence changes the mean expansion. Shear contributes through anisotropic coverage. Balanced all-sky weights cancel the bulk and shear terms in this idealized estimator, while \(\theta/3\) remains. A directional radial Hubble estimate instead contains \((n\cdot b)/r\); it should not be assigned the volume-expansion factor \(1/3\).

The legacy expression \(\Delta H/H=\beta c/(3Hd)\) gave approximately 4% at 50 Mpc using an older velocity amplitude. With \(\beta=1.051\times10^{-3}\), \(H=67.36\,\mathrm{km\,s^{-1}\,Mpc^{-1}}\) and \(c=299792.458\,\mathrm{km\,s^{-1}}\), the same expression gives 3.118%. The more informative replacement is the survey-weighted shift above, evaluated on the actual sample. Distance errors, fitted intercepts and luminosity selection enter through their corresponding likelihood and design. They determine the measured shift rather than being summarized by one effective depth.

## A convergence scale with a measurable input

The peculiar Jeans discussion can likewise be preserved as a conditional physical test. Retain the legacy tilted-deceleration relation as the hypothesis under examination,

\[
\Delta q(\lambda)=\frac19\left(\frac{c}{H\lambda}\right)^2
\frac{\theta(\lambda)}H.
\]

The input is the peculiar divergence after filtering on scale \(\lambda\). For a decelerating background \(q>0\) and contracting flow, a zero crossing satisfies

\[
\lambda_J=\frac{c/H}{3}
\sqrt{-\frac{\theta(\lambda_J)}{qH}}.
\]

This is implicit when the measured convergence varies with scale. For the illustrative choice \(q=1/2\), \(H=67.36\), constant \(\theta/H=-0.01\) gives 209.803 Mpc; \(-0.02\) gives 296.707 Mpc. A crossing at 300 Mpc requires \(\theta/H=-0.0204464\). These statements identify the velocity-gradient measurement needed to test the proposed scale.

The cube-root formula in the monograph follows after imposing \(\theta/H=-\beta(c/H)/\lambda\). That assumption describes a particular converging flow and supplies information absent from a bulk amplitude alone. A uniform translation gives no correction through this divergence term. An already accelerating background also changes the sign-crossing question. HTT can therefore report a convergence-dependent correction curve and its crossing interval, with the background and filtering convention attached, rather than treating approximately 300 Mpc as a universal boundary.

## What the CMB quadrupole remembers

The CMB supplies a different kind of physical measurement: accumulated directional redshift. A collisionless Bianchi-I example makes the distinction from instantaneous shear transparent. Take

\[
ds^2=-c^2dt^2+a(t)^2\sum_i e^{2b_i(t)}(dx^i)^2,
\qquad\sum_i b_i=0,
\]

with initially isotropic Planck radiation and \(b_i(t_i)=0\). The orthonormal shear components are \(\sigma_{ij}=\dot b_i\delta_{ij}\). Conservation of spatial photon momenta gives the normal observer's temperature,

\[
T(n,t)=\frac{T_i a_i}{a(t)}
\left[\sum_i e^{2b_i(t)}n_i^2\right]^{-1/2}.
\]

For weak anisotropy, monopole subtraction gives

\[
\frac{Q_{ij}}{T_0}=-B_{ij}+O(B^2),\qquad
B_{ij}=\int_{t_i}^{t}\sigma_{ij}(s)\,ds.
\]

The temperature quadrupole therefore measures an integrated shear history in this branch. To infer the present shear, one must specify the history response. Constant shear gives \(B=\Delta t\,\sigma\); a growing, decaying or sourced history gives a different conversion.

Figure A contrasts two commuting diagonal histories. In normalized time \(\tau\in[0,1]\), their shear amplitudes are proportional to \(1\) and \(1+0.8(2\tau-1)\). Their integrals agree, but their endpoint amplitudes differ by 80%. With the same initial and mean-scale-factor normalization they produce the same final temperature pattern in this idealized collisionless construction. These are kinematic examples, not new Einstein-matter solutions. They explain precisely why a measured quadrupole can constrain accumulated anisotropy while leaving instantaneous shear dependent on a physical history model.

This interpretation gives the tensor machinery a direct role. Full Q/O coordinates preserve the measured sky. Orbit distances compare its predicted shape under a common rotation. Relative directions connect that pattern to measured flows. A registered radiation response then transports these measurements into a permitted shear-history set, with uncertainty and residuals retained.

## A conditional Bianchi-V consistency curve

The legacy Bianchi-V exclusion can be reconstructed around its useful geometric content. For the declared LRS single-perfect-fluid branch, write

\[
ds^2=-c^2dt^2+X(t)^2dz^2+
Y(t)^2e^{-2A_0z}(dx^2+dy^2),
\quad X=ae^{2b},\quad Y=ae^{-b}.
\]

Let \(H=\dot a/a\) and \(s_b=\dot b\). The normal observer has shear \(\operatorname{diag}(-s_b,-s_b,2s_b)\), so

\[
\Sigma^2=\frac{\sigma:\sigma}{6H^2}
=\frac{s_b^2}{H^2}
=\frac{(H_\parallel-H_\perp)^2}{9H^2}.
\]

On a fixed-time slice, set \(s=Xz\) and \(f(s)=Y e^{-A_0s/X}\). Its curvature follows directly:

\[
{}^{(3)}R=-4f''/f-2(f'/f)^2=-6(A_0/X)^2,
\qquad
K=-\frac{c^2{}^{(3)}R}{6H^2}
=\left(\frac{cA_0}{XH}\right)^2>0.
\]

The positive \(K\) denotes open spatial curvature in the usual density-parameter convention. The normal Hamiltonian constraint is

\[
1=\Omega_n+\Omega_\Lambda+\Sigma^2+K,
\qquad \Omega_\Lambda=\frac{\Lambda c^2}{3H^2}.
\]

For rest-frame energy density \(\varepsilon\), pressure \(p=w\varepsilon\), and tilt rapidity \(\chi\), define \(\Omega_m=8\pi G\varepsilon/(3c^2H^2)\). The normal density is \(\Omega_n=\Omega_m[1+(1+w)\sinh^2\chi]\). Choosing the corresponding orientation of the tilt axis, the momentum constraint gives

\[
2\sqrt K\,\frac{s_b}H
=(1+w)\Omega_m\sinh\chi\cosh\chi,
\]

and hence

\[
\Sigma^2=
\frac{[(1+w)\Omega_m]^2\sinh^2\chi\cosh^2\chi}{4K}.
\]

This retains the physically interesting inverse-curvature coupling: at fixed matter and tilt, smaller curvature requires larger shear. A source-matched allowed shear \(\Sigma_{\max}^2\) gives the conditional constraint

\[
|\sinh\chi\cosh\chi|
\le\frac{2\sqrt{K\Sigma_{\max}^2}}{|(1+w)\Omega_m|}.
\]

The observational question is whether this curve intersects the joint allowed set for matter, curvature, velocity and shear. A family-specific radiation response connects that intersection to Q/O or polarization. The normal observer is hypersurface orthogonal and has zero vorticity; fluid-frame vorticity requires its own transformation. This resolves the frame and curvature ambiguity before testing compatibility and preserves the model's falsifiable prediction.

## An exact brightness check and a reusable normalization

Nonlinear temperature moments can be calibrated without a transport solver. For the declared axisymmetric brightness field

\[
\Theta(\mu)=1+A\mu+Q P_2(\mu),\qquad
\langle f\rangle=\frac12\int_{-1}^{1}f(\mu)d\mu,
\]

where \(Q\) here is a scalar Legendre coefficient, exact integration yields

\[
\begin{aligned}
\langle\Theta^4\rangle={}&1+2A^2+\frac65Q^2
+\frac85A^2Q+\frac8{35}Q^3\\
&+\frac15A^4+\frac{22}{35}A^2Q^2+\frac3{35}Q^4.
\end{aligned}
\]

The mixed cubic coefficient is \(8/5\). The monograph used the integral \(\int\mu^2P_2\,d\mu=4/15\) as a sphere average; the average is \(2/15\). Figure C isolates the observable mixed contribution and shows the effect of doubling that coefficient. The polynomial is an exact brightness identity. Assigning its amplitudes to acceleration, tilt or shear additionally requires the corresponding physical response and an absolute-temperature/bandpass model.

Temperature normalizers need the same care. With \(C_\ell=2\pi D_\ell/[\ell(\ell+1)]\), the later report's Frobenius conventions are

\[
Q_{ab}Q^{ab}=\frac{75}{8\pi}C_2,
\qquad O_{abc}O^{abc}=\frac{245}{8\pi}C_3.
\]

The supplied \(D_2=225.9\), \(D_3=936.9\,\mu\mathrm K^2\) give tensor norms 26.5695 and 69.1527 microkelvin. These differ from \(\sqrt{C_\ell}\); their associated dimensionless amplitudes cannot share an unqualified epsilon label. Likewise, use \(\beta=v/c\) and \(\chi=\operatorname{artanh}\beta\), and distinguish inverse-time rates from geometric inverse-length rates through \(H_g=H/c\). Such adapters allow the same physical state to pass consistently through the constraint, sky response and likelihood.

## Reading the reconstructed quantities together

These examples suggest a common experimental sequence. Start with the actual distance and angular support of each velocity sample, estimate its bulk and gradient response, and carry the full covariance between shells. Extract the measured temperature tensors with their unit and harmonic convention. Specify which part of the prediction is an endpoint observer transformation and which part is a matter or geometry history. The resulting joint model predicts velocities, sky coefficients and distance residuals in their measured units before any normalization by an allowed budget.

For example, a coherent bulk accompanied by little measured convergence can still produce a directional distance residual on an uneven sky. It need not produce the convergence-driven deceleration correction. Conversely, opposing streams can have a small bulk but a nonzero quadratic stress that sources shear. A quadrupole consistent with an integrated shear history then supplies a different physical constraint from the bulk measurement. Keeping these channels together allows HTT to describe such configurations without forcing every signal into one tilt amplitude.

A conditional MES body can express how large the kinematic channels may be under its radiation and derivative premises. Its gauge asks how much the inferred state uses those allowed channel radii; its directional support asks which components of the permitted state remain largest. Neither operation replaces the dimensional outputs. Reporting a velocity interval in kilometers per second, a shear or convergence interval in inverse time, and a predicted Hubble-estimator shift makes the normalized result physically readable. Shared cosmology, calibration and response uncertainty must remain shared when taking their joint image.

Statistical comparison then addresses a defined competition: can a local flow and observer motion explain the joint observations, or does a registered global history improve their predicted direction and depth dependence? The comparison uses each model's actual response and sampling law. A confidence set or posterior can be pushed into the survey Hubble shift, a Bianchi-V consistency interval, or an integrated shear amplitude. This gives each mathematical summary a common scientific destination while retaining the distinctions that make the destination testable.

The resulting HTT analysis has a concrete experimental object: a joint depth-dependent velocity and sky pattern, its predicted distance residuals, and the physical states compatible with them. Tensor support, conditional bounds and statistical comparisons then describe which channels remain allowed and which additional observations distinguish their histories.

**Page provenance.** Monograph printed pp.25–27 motivate the programme; pp.54–56 and 151 give the convergence closure; pp.153–154 give the Hubble estimate; pp.75–76,148–149,197–198 give the Bianchi-V metric and inconsistent legacy conventions; pp.92–93 give the brightness mixed term; p.105 lists scalar normalizers. The later report's printed pp.2–6,7,12–15,21–23 provide frame, tensor, radial-response and joint-state definitions. Monograph PDF page = printed page + 1; report PDF page = printed page + 3. All new calculations here are analytic illustrative constructions, not reanalyses of survey data.

**Figure.** `figures/legacy_physical_analytic_examples.pdf` and its PNG export: A, equal integrated shear with different endpoint amplitudes; B, conditional convergence crossing scale; C, exact mixed brightness moment and the doubled-cubic comparison. The generating script uses algebraic curves and polynomial quadrature, with no ODE or cosmological solver.
