# From measured tensors to physical quantities

### Local affine motion and the optical expansion tensor

At one event, use an orthonormal rest frame and proper separation \(r n\), with \(n\cdot n=1\). The first spatial jet of a smooth velocity field has the form
\[
v(rn)=b+r(HI+S+\Omega)n+O(r^2),\qquad S^T=S,\quad\operatorname{tr}S=0,\quad\Omega^T=-\Omega.
\]
Here \(b\) is a velocity and \(H,S,\Omega\) are rates. The radial channel is
\[
v_r=b\cdot n+r[H+n^TSn]+O(r^2).
\tag{P1}
\]
Antisymmetry gives \(n^T\Omega n=0\). Radial motion therefore measures translation, volume expansion and shape deformation in this local model. It does not measure rigid rotation. The transverse channel contains \(r^{-1}P_n b+P_nSn+\Omega n\), with \(P_n=I-nn^T\); its common rotation is degenerate with an uncalibrated rotation of the astrometric frame. This is a useful physical reading of the optical nullspace and source-spin quotient: each removes a motion to which its particular observable is insensitive.

For an expanding material congruence, the principal rates \(H+s_i\), where \(s_i\) are the eigenvalues of \(S\), give the instantaneous growth rates of three orthogonal infinitesimal separations. Their sum is \(3H\). Positive \(s_i\) means expansion faster than the mean, not necessarily absolute acceleration; negative \(s_i\) means slower expansion, not necessarily contraction. The dimensionless energy-like shear coordinate is
\[
\Sigma^2=\frac{S:S}{6H^2},\qquad
\left\langle\left(\frac{n^TSn}{H}\right)^2\right\rangle_{S^2}
=\frac{2S:S}{15H^2}=\frac45\Sigma^2.
\tag{P2}
\]
The second equality follows from \(\langle n_i n_j n_k n_l\rangle=(\delta_{ij}\delta_{kl}+\delta_{ik}\delta_{jl}+\delta_{il}\delta_{jk})/15\). It converts a tensor norm into the rms directional expansion contrast. This deterministic conversion is also meaningful for an apparent fitted rate tensor, provided the result is named as that fitted quantity.

The general-relativistic local optical coefficient is a distinct observation map. With signature \((-+++)\), unit timelike \(u\), proper length \(s=c\tau\), and observer-to-source direction \(n\),
\[
\mathcal H_u(n)=H-\frac{A\cdot n}{c}+\sigma:nn.
\tag{P3}
\]
It enters \(d_L=cz/\mathcal H_u(n)+O(z^2)\) for emitters and observer following the stated congruence. Thus a same-congruence local optical dipole has acceleration units after multiplication by \(-c\), while the finite-distance translation contribution in (P1) scales as \(b/r\). These are distinct mechanisms with different radial responses. A catalogue window generally mixes them, finite-redshift terms, selection and calibration.

For \(q=d\cdot n+T:nn\), \(d=-A/(cH)\), \(T=\sigma/H\), the local magnitude response is \(f=-\kappa\log(1+q)\), \(\kappa=5/\ln10\), provided \(1+q>0\). At linear order the magnitude STF tensor is \(B_\mu=-\kappa T\), whereas a rate tensor is \(B_H=H T\). A producer can instead fit \(T\) directly by placing \(-\kappa\) in the design matrix. Its numerical coefficient then has no magnitude unit. The three representations are physically related by a map, not by equality of their recorded numbers.

### The Hubble shift measured by a particular estimator

Consider a weighted through-origin slope
\[
\widehat H=\frac{\sum_i w_i r_i v_{r,i}}{\sum_i w_i r_i^2}.
\]
Let the peculiar velocity relative to a reference expansion be \(v_p=b+r[(\vartheta/3)I+S]n\) on the fitted domain. Substitution, without a sky-symmetry assumption, gives
\[
\delta\widehat H=b\cdot m_W+\frac{\vartheta}{3}+S:Q_W,\quad
m_W=\frac{\sum_iw_ir_in_i}{\sum_iw_ir_i^2},\quad
Q_W=\frac{\sum_iw_ir_i^2n_in_i^T}{\sum_iw_ir_i^2}.
\tag{P4}
\]
The units are \([m_W]=\mathrm{length}^{-1}\) and \([Q_W]=1\). A normalized isotropic directional window has \(m_W=0\), \(Q_W=I/3\), so both bulk and trace-free shear cancel from this monopole estimator. For a real survey they can leak into it. Equation (P4) specifies exactly how an observed bulk vector can affect a measured Hubble slope: the missing object in a scalar \(v/r\) argument is the estimator's angular-depth window. It also explains why method-dependent distance calibration can imitate a monopole or quadrupole when different methods occupy different sky/depth regions.

The same observation can be read through linear-theory mass conservation, when pressureless growing-mode perturbations about FLRW are explicitly adopted. Here \(\vartheta=\nabla_r\cdot v_p=-Hf\delta\) is the proper-coordinate divergence used in (P4), while \(\nabla_x\cdot v_p=-aHf\delta\) uses comoving coordinates \(r=ax\). The local slope shift is then \(-Hf\delta/3\) for an isotropic window. This is a model-dependent density interpretation of a measured divergence. It is not obtained from the bulk speed alone: a spatially constant nonzero \(b\) has zero divergence.

### A finite response comparison using the actual four-window dipoles

The saved H03 carrier supplies twelve dipole coordinates \(y=(D_1,\ldots,D_4)\), their full \(12\times12\) covariance \(C\), and the actual window response \(R_w\) of the fitted dipole to a constant input bulk velocity. Retain these matrices instead of replacing each window by its central redshift. Three reduced source-response hypotheses are
\[
\mathcal A_b:\ D_w=R_w b,\qquad
\mathcal A_d:\ D_w=d_0,\qquad
\mathcal A_{bd}:\ D_w=R_w b+d_0.
\tag{P5}
\]
The first tests one common translation through the delivered window response. The second tests one depth-independent rate dipole. The third permits both. The rate dipole can be associated with acceleration only after the optical and frame conditions of (P3) are supplied. A fit of (P5) is not a test of every local-flow or global-tilt history.

For any of these design matrices \(X\), whiten with \(C=LL^T\), solve \(\widehat\theta=\arg\min\|L^{-1}(y-X\theta)\|^2\), and set \(T=\|L^{-1}(y-X\widehat\theta)\|^2\). If the specified mean model is true and this fixed covariance is the Gaussian sampling covariance, \(T\sim\chi^2_{12-\operatorname{rank}X}\). The calculation is executed on the actual saved dipoles; this distribution is conditional on the inherited working law.

There is also an exact deterministic interpretation of the failure size. Write \(P\) for the orthogonal projection onto \(\operatorname{col}(L^{-1}X)\). For an added mean discrepancy \(e\) satisfying \(\|L^{-1}e\|\le\eta\),
\[
\min_e\min_\theta\|L^{-1}(y-e-X\theta)\|^2
=\bigl[\max(0,\sqrt T-\eta)\bigr]^2.
\tag{P6}
\]
The triangle inequality gives the lower bound, and choosing the discrepancy along \((I-P)L^{-1}y\) attains it. Thus \(\eta_{95}=\max(0,\sqrt T-\sqrt{\chi^2_{12-p,.95}})\) is the smallest whitened mean correction that reaches the stated residual threshold within this unrestricted twelve-dimensional error ball. For an error restricted by a physical response, it is a necessary lower budget; sufficiency additionally requires that the residual direction is attainable. It is an error-budget requirement, not a measured systematic. A separate sensitivity calculation adds \(\tau^2I\) to the covariance of these twelve summary coordinates and refits. Its crossing scale describes covariance sensitivity, not an inferred extra galaxy scatter.

### Physical bounds with an explicit response-error budget

Suppose the desired physical rate tensor obeys \(\widehat Q=\sigma+E\), with \(\|E\|_F\le r_Q\), and the true positive monopole obeys \(|H-\widehat H|\le r_H<\widehat H\). Then
\[
\frac{(\|\widehat Q\|_F-r_Q)_+}{\sqrt6(\widehat H+r_H)}
\le\Sigma\le
\frac{\|\widehat Q\|_F+r_Q}{\sqrt6(\widehat H-r_H)}.
\tag{P7}
\]
This follows from the norm triangle inequalities and monotonicity of division by a positive monopole. It remains valid when \(r_Q\) is a sum of statistical, calibration, finite-redshift and frame-response radii on one common event. A joint event is needed before attaching simultaneous coverage. If a fixed Gaussian coefficient law supplies an ellipsoid of squared radius \(q\), in Frobenius-orthonormal tensor coordinates a conservative block norm radius is \(\sqrt{q\lambda_{\max}(C_Q)}\), and the monopole radius is \(\sqrt{qC_{HH}}\). Other coordinates require their tensor metric. The deterministic source-response radius is then added, rather than silently assumed to be zero.

For ordered principal rates, Weyl's inequality gives
\[
|\lambda_i(\sigma)-\lambda_i(\widehat Q)|\le\|E\|_{\mathrm{op}}\le r_Q.
\tag{P8}
\]
Consequently a principal direction is demonstrably faster than the local mean if its positive eigenvalue exceeds the applicable response error. A nonzero lower shear bound survives only while the total radius is smaller than \(\|\widehat Q\|_F\). This turns an unspecified physical bridge into a numerical qualification target: one must bound a concrete response error below a stated scale. It does not require every inaccessible feature of a source model to be known exactly.

The same construction works for a dimensionless coefficient \(\widehat T\), replacing \(\Sigma\) by \(\|T\|_F/\sqrt6\) and omitting the monopole division. For magnitude coefficients the conversion is \(T=-B_\mu/\kappa\), with the corresponding transformed covariance and response-error radius. Units and the producer's design matrix decide which version applies.

### A conditional geometric test for the locally rotationally symmetric Bianchi V example

For the legacy metric \(ds^2=-c^2dt^2+X^2dz^2+Y^2e^{-2A_0z}(dx^2+dy^2)\), take the hypersurface normal and define \(H=(H_X+2H_Y)/3\), \(s=(H_X-H_Y)/3\). Its normal-frame shear is \(\operatorname{diag}(-s,-s,2s)\), and therefore \(\Sigma^2=s^2/H^2\). At fixed time, the coordinate \(r=Xz\) gives a warped spatial metric whose sectional curvatures are all \(-(A_0/X)^2\); hence \({}^{(3)}R=-6(A_0/X)^2\) and \(K=-c^2{}^{(3)}R/(6H^2)>0\).

Under the perfect-fluid momentum constraint used for this LRS family, take an expanding normal frame \(H>0\), take an expanding normal frame \(H>0\), take an expanding normal frame \(H>0\), take an expanding normal frame \(H>0\), take an expanding normal frame \(H>0\), orient the axis so that \(A_0/X>0\), use signed \(\beta\) along this axis, and define the normal-frame Hubble normalization of rest energy \(\Omega_m=8\pi G\varepsilon/(3c^2H^2)\), \(p=w\varepsilon\), and \(\beta=\tanh\chi\). Then
\[
2\sqrt K\,\frac{s}{H}=(1+w)\Omega_m\gamma^2\beta,
\qquad
\Sigma^2=\frac{[(1+w)\Omega_m]^2\beta^2}{4K(1-\beta^2)^2}.
\tag{P9}
\]
This is an explicit geometry-dependent shear–tilt relation. In the following speed bound write \(\beta=|v|/c\ge0\). For \(1+w>0\), a qualified shear ceiling \(\Sigma_{\max}\), curvature ceiling \(K_{\max}\), and rest-energy floor \(\Omega_{\min}>0\) imply
\[
\frac{\beta}{1-\beta^2}\le a,
\quad a=\frac{2\sqrt{K_{\max}}\Sigma_{\max}}{(1+w)\Omega_{\min}},
\quad
\beta\le\frac{2a}{1+\sqrt{1+4a^2}}.
\tag{P10}
\]
The last expression is the numerically stable positive root and tends to \(a\) at small \(a\). The limits must belong to the same frame and compatible family state; the normal constraint and nonnegative matter/other components must also hold. A CMB quadrupole amplitude becomes the needed shear ceiling only through a specified history response. Equations (P9)–(P10) retain the legacy programme's concrete geometric ambition while replacing a family-wide exclusion by a testable conditional curve.

### CMB anisotropy as a time-weighted deformation

For freely propagating photons in a non-tilted geodesic homogeneous frame, the exact energy equation is \(d\ln\epsilon/dt=-H-\sigma_{ab}n^an^b\). In the small-anisotropy approximation with the path direction fixed to leading order, isotropic emission, and no collision or endpoint terms, the temperature quadrupole tensor satisfies
\[
Q_T=-\int_{t_*}^{t_0}\sigma(t)\,dt.
\tag{P11}
\]
This is a dimensionless integrated-deformation tensor, not an instantaneous shear. It yields \(\|Q_T\|_F\le\int\|\sigma(t)\|_Fdt\): a measured quadrupole supplies a lower requirement on total deformation in this simplified isolated-source model. An upper instantaneous-shear limit instead needs a time profile and control of cancellations. If \(\sigma(t)=H_0s_0g(t)\) in a fixed eigenframe, with \(H_0=H(t_0)\) and with \(H_0=H(t_0)\) and with \(H_0=H(t_0)\) and with \(H_0=H(t_0)\) and with \(H_0=H(t_0)\) and normalized by \(g(t_0)=1\), with known nonzero \(J=H_0\int g(t)dt\), then \(s_0=-Q_T/J\) and \(\Sigma_0=\|Q_T\|_F/(\sqrt6|J|)\). More generally a supplied linear response \(\mathcal T\) gives \(a=\mathcal T s+e\); its singular values and kernel determine the constrained physical combinations. This is the physical role of rank, nullspace and spectral conditioning in the repository.

For actual CMB analyses, scattering, polarization, stochastic primordial anisotropy, evolving ray directions and observer terms enter the response. A finite bandpass decomposition isolates spectral combinations; it does not supply the temporal response in (P11). A blackbody-spectrum secondary signal can remain indistinguishable from primary CMB by frequency alone while retaining a distinguishable correlation with a lens or tracer. This separates two useful routes: a spectral quotient and a physically targeted cross-correlation.
