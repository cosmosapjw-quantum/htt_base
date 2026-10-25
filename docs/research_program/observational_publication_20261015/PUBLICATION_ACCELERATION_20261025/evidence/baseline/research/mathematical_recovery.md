# Mathematical recovery for manuscript integration

The following blocks use signature \((-+++)\). In the geometric block, \(c=1\), \(u^au_a=-1\), and all contractions refer to the same congruence; the observational design retains \(c\) explicitly. These are conditional mathematical statements with separate application requirements.

## Congruence, curvature contraction, and the signed comparator

Let \(h_{ab}=g_{ab}+u_au_b\), and decompose the projected velocity gradient as
\[
V_{ab}=h_a{}^ch_b{}^d\nabla_cu_d
      =\frac{\theta}{3}h_{ab}+\sigma_{ab}+\omega_{ab},
\qquad H=\theta/3.
\]
Here \(\sigma_{ab}\) is symmetric and trace free and \(\omega_{ab}\) is antisymmetric. Consequently,
\[
V_{ab}V^{ab}=\frac{\theta^2}{3}+\sigma_{ab}\sigma^{ab}
                         +\omega_{ab}\omega^{ab},\qquad
V_{ab}V^{ba}=\frac{\theta^2}{3}+\sigma_{ab}\sigma^{ab}
                         -\omega_{ab}\omega^{ab}.
\]
The distinction between these contractions matters whenever the rest distribution rotates.

In a compatible orthonormal frame, write \(A_C\) for the projected rest-bundle connection and \(c^E{}_{CD}\) for the frame bracket. Its curvature uses the full bracket:
\[
\mathcal R_{CD}
=e_CA_D-e_DA_C+[A_C,A_D]-c^E{}_{CD}A_E.
\]
Dropping the vertical bracket produces another expression, related by
\[
\mathcal R_{kl}=\mathcal R^{\rm drop}_{kl}
                   -2\omega_{kl}A_0.
\]
The full expression transforms by conjugation under a change of spatial triad. The dropped expression acquires the corresponding time-dependent triad-spin term. It therefore cannot be assigned the same intrinsic meaning when \(\omega\ne0\).

Let \(R_{\rm proj}\) denote the stated spatial double contraction of the spacetime Riemann tensor. With the curvature and slot conventions used here, the full-bracket Gauss scalar is
\[
R_{\rm rest}=R_{\rm proj}-\theta^2+V_{ab}V^{ba},
\]
whereas the same-order expression is
\[
R_{\rm same}=R_{\rm proj}-\theta^2+V_{ab}V^{ab}
            =R_{\rm rest}+2\omega_{ab}\omega^{ab}.
\]
For example, take a pure antisymmetric spatial gradient with
\(\omega_{12}=w=-\omega_{21}\). Then
\(\omega_{ab}\omega^{ab}=2w^2\), and the scalar difference is \(4w^2\).
At \(\omega=0\) the two expressions coincide.

This also specifies what is required before a signed comparator becomes an Einstein constraint identity. If the adopted Einstein contraction supplies
\(R_{\rm proj}=2\kappa\rho_u+2\Lambda\), substitution gives
\[
1=\Omega_{\rho_u}+\Omega_\Lambda+\Omega_k
        +\Sigma^2-W^2,
\quad
\Omega_k=-\frac{R_{\rm rest}}{6H^2},\quad
\Sigma^2=\frac{\sigma_{ab}\sigma^{ab}}{6H^2},\quad
W^2=\frac{\omega_{ab}\omega^{ab}}{6H^2},
\]
with \(\Omega_{\rho_u}=\kappa\rho_u/(3H^2)\) and
\(\Omega_\Lambda=\Lambda/(3H^2)\). This requires \(H\ne0\).
Writing \(\rho_u=\rho_{\rm base}+\rho_{\rm tilt}\) further requires an explicit energy split. A density deficit relative to a comparator is then obtained by subtracting the two specified constraints. The subtraction is not an identity supplied by the signed functional alone.

Using \(R_{\rm same}\) instead changes the curvature parameter:
\(\Omega_k^{\rm same}=\Omega_k-2W^2\). With that parameter the same constraint reads
\[
1=\Omega_{\rho_u}+\Omega_\Lambda+
                   \Omega_k^{\rm same}+\Sigma^2+W^2.
\]
Thus a change of contraction cannot leave both the curvature definition and the displayed vorticity sign untouched. These formulas are direct consequences of the declared conventions, rather than interchangeable curvature notations.

There is a separate restriction for a hypersurface normal. If
\(n_a=-N\partial_at\), \(N\ne0\), the Hessian of \(t\) is symmetric and the connection is torsion free. Hence
\[
\nabla_{[a}n_{b]}=(\partial_{[a}\log N)n_{b]},
\qquad h_a{}^ch_b{}^dn_d=0,
\]
so \(\omega_{ab}[n]=0\). A comparator defined on \(n\) cannot independently vary its vorticity sector.

For a concrete illustration, the algebraic box
\[
\Sigma^2=.12,\quad W^2\in[0,.04],\quad
\Omega_{\rm tilt}=.03,\quad \Omega_k\in[0,.02]
\]
gives \(x_C=\Sigma^2-W^2+\Omega_{\rm tilt}+\Omega_k\in[.11,.17]\).
For the specified hypersurface-normal constraint construction, however,
\(W^2[n]=0\), so values below \(.15\) are excluded before evolution is considered. The algebraic lower corner cannot be restored by replacing vorticity with another sector. An instantaneous Bianchi-V constraint witness realizes the upper value \(.17\); local or global development requires additional dynamical arguments. The rotating matter congruence \(u\) is a different construction and requires a frame-consistent bridge.

*Source: full-bracket finite-jet Gauss statements and reviewed comparator construction, commits c6d82121731c59916d21f6ec071c7a8e2a076bcd and 85c2219cb9acf333dd3ff96d02561622c6273141; exact paths in the accompanying source index. The Einstein-normalized display above is an explicit algebraic specialization under the stated Einstein contraction, not a separately executed formal theorem. The source Gauss proof is at one-event frame/connection-jet scope.*

## A bulk-flow window retains a stochastic residual

Suppose \(v(x)=v_0+u(x)\) almost everywhere and define
\[
B_W[v]=\int W(x)v(x)\,d\nu(x).
\]
Integrability immediately gives
\[
B_W[v]=\left(\int W\,d\nu\right)v_0+B_W[u].
\]
Thus a normalized window has unit homogeneous-mode gain, but its measured value still contains \(B_W[u]\).

For zero-mean scalar components \(a,b\), assume the joint integrability needed for Fubini and the cross-spectrum representation
\[
\mathbb E[a(x)b(y)]
 =\int e^{ik\cdot(x-y)}p_{ab}(k)\,d\mu(k).
\]
With \(\widehat W(k)=\int e^{-ik\cdot x}W(x)\,d\nu(x)\),
\[
{\rm Cov}(B_W[a],B_{W'}[b])
 =\int \overline{\widehat W(k)}
              \widehat W'(k)p_{ab}(k)\,d\mu(k).
\]
The proof substitutes the cross-spectrum into the double window integral and interchanges integrals. Every pair of windows contributes; overlapping or related windows do not become independent by using different depth labels.

A small example makes the residual explicit. Give the four fields
\(\cos x,-\sin x,-\cos x,\sin x\) equal probability. Their mean is zero and their covariance is \(\cos(x-y)/2\). Point windows at \(0\) and \(1\) have residual variance \(1/2\) and cross covariance \(\cos(1)/2\ne0\). A measured bulk value therefore cannot be substituted pointwise for the homogeneous mode, even though its expectation can equal that mode.

Calling the residual “finite-\(k\)” additionally requires exclusion of spectral mass at \(k=0\); otherwise it contains a constant component degenerate with \(v_0\). The spectral representation, integrability, frame, and selection/calibration remainder bounds must be supplied for an observational application.

*Source: commit 06895b6bcede654601dcbd7d6fe180cdb7ba4142; the finite algebraic catalogue estimator and continuous window theorem are separate source statements.*

## Two radii separate angular nuisance and depth response

Consider
\[
y_i=E_4(n_i)a+\frac{r_i}{c}E_9(n_i)h,
\qquad X=[E_4,D E_9],\quad D={\rm diag}(r_i/c).
\]
The four columns of \(E_4\) span \(1,n_x,n_y,n_z\). The nine columns of \(E_9\) span degrees at most two, including the five STF coordinates, and include \(E_4\). Let \(L\) embed the four coefficients so that \(E_9L=E_4\).

Take nine unisolvent directions at \(R_1>0\), and repeat four of them at \(R_2>0\). Suppose \(c>0\), \(R_1\ne R_2\), the nine-direction \(E_9\) matrix is invertible, and the repeated four-direction \(E_4\) matrix is invertible. The first nine equations of \(X(a,h)=0\) give
\[
h=-\frac{c}{R_1}La.
\]
The remaining four equations reduce to
\[
(1-R_2/R_1)E_{4,{\rm repeat}}a=0.
\]
The hypotheses force \(a=0\), then \(h=0\); hence \(X\) has rank thirteen. Equal radii instead retain the four-dimensional ambiguity \(h=-(c/R_1)La\), giving rank at most nine.

A rational example uses the six signed coordinate axes and
\((.6,.8,0),(.6,0,.8),(0,.6,.8)\), with repeated directions
\(e_1,-e_1,e_2,e_3\). In the stated basis,
\(\det E_9=331776/15625\), \(\det E_{4,{\rm repeat}}=-2\), and elimination gives
\[
\det X=\frac{R_1^5(R_1-R_2)^4}{c^9}
              \det E_9\det E_{4,{\rm repeat}}.
\]
Rank is a structural condition. As the radii approach equality, the inverse problem can become poorly conditioned despite retaining rank thirteen. Precision therefore also needs source covariance, signal scale and conditioning in declared coordinates.

*Source: commit 15c5723005a1aa4eb3be888398160bf6ffd2b4f8. The rational determinant and conditioning illustration are separately reproduced in the accompanying rank-design calculation.*

## Proper motion and orbit tilt carry different calibration requirements

A covariant derivative channel is \(J=h\nabla_XU\), with
\(J-h\partial_XU=h\Gamma_XU\). It is not automatically a measured proper motion. In a declared flat, instantaneous, low-velocity model at distance \(D>0\), the tangential drift is
\[
\mu=P_n(Sn)+(\omega-\Omega_{\rm frame})\times n
                       +D^{-1}P_ne.
\]
Thus isotropic expansion is invisible, intrinsic rotation is degenerate with frame spin, and non-comoving residuals introduce inverse-distance dependence. Optical propagation and relativistic corrections need their own remainder control; the source does not supply an empirical calibration.

Orbit-normal tilt instead uses independently supplied spacelike generators with positive-definite Gram matrix, their future unit normal \(N\), and future unit \(u\):
\[
\gamma_{uN}=-g(u,N),\qquad
\beta_{uN}^2=1-\gamma_{uN}^{-2}.
\]
Reverse Lorentz Cauchy–Schwarz gives
\(\gamma_{uN}=1\iff\beta_{uN}=0\iff u=N\).
A passive common coordinate change preserves this contraction. Changing the physical vector is a different operation. For example, \(\gamma_{uN}=5/3\) and \(\beta_{uN}^2=16/25\) can coexist with \(\gamma_{uo}=1\) for another observer \(o=u\). Observer-relative speed therefore cannot replace orbit-normal tilt. Pointwise generators and a tilt value do not by themselves establish a Bianchi family.

*Sources: commits b3a0fc8b81c10c026b860010ffcf6485e48358b2 and 5d7a27bf7f83a0defceb3195c00b9f0022567d31; flat proper-motion and single-event orbit assumptions are retained.*

