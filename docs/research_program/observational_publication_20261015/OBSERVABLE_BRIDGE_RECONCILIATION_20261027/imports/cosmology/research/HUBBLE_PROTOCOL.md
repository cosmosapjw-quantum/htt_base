# Source-bound Hubble coupling inverse and a joint error-budget test

Internal constructive repair, 2026-10-26. Sources: pinned R32-01 `products/R32-01-QO-METHODS/science/MANUSCRIPT.md`, §§4–6, eqs. (20)–(32), (36), (38)–(41), and `evidence/baseline/research/theory_expansion.md`, T1–T15, under the preserved `PUBLICATION_ACCELERATION_20261025` source tree. This note binds and extends that protocol; it does not start another full research loop or alter a source.

## 1. What the inferred vector and shear mean

In the pinned manuscript, \(u^2=-1\), \(s=c\tau\), and \(n\) points toward the source. \(H,\sigma\) are physical inverse-time expansion/shear rates and \(A\) is physical acceleration in length/time². For smooth emitters and observer in the **same declared congruence**, with regular local geometric optics,
\[
\mathcal H(n)=H-A\cdot n/c+\sigma:nn
=H[1+d\cdot n+S:nn],\qquad
 d=-A/(cH),\quad S=\sigma/H.
\tag{H1}
\]
Assume \(H>0\), real STF \(S\), and \(\sup_n|q(n)|\le\epsilon<1\), where \(q=d\cdot n+S:nn\). Then the local angular magnitude field is
\[
f_\mu(n)=-\kappa\ln[1+q(n)],\qquad\kappa=5/\ln10>0.
\]
Thus \(d\) is normalized congruence acceleration, not a peculiar-velocity or CMB-temperature dipole. Recovering \(A=-cHd\) and \(\sigma=HS\) additionally requires the common rate normalization \(H\).

\(S\) is the quadrupole of the **directional Hubble slope**, not the measured magnitude quadrupole \(Q_\mu\). The manuscript's eq. (36) states
\[
Q_\mu=-\kappa S+R_2,\quad
\|R_2\|_F\le E_2(\epsilon)
=\sqrt{15/2}\frac{\kappa\epsilon^2}{2(1-\epsilon)}.
\tag{H2}
\]
If \(\widehat S=-\widehat Q_\mu/\kappa\) is used, its error radius must include \([E_2+e_Q+B_{z,2}+B_{sel,2}]/\kappa\), plus declared calibration/frame errors. The magnitude dipole likewise is not exactly \(-\kappa d\). The ideal complete-field inverse, manuscript (38)–(39), first normalizes \(r=e^{-f_\mu/\kappa}/\langle e^{-f_\mu/\kappa}\rangle\), then recovers \(d=3\langle rn\rangle\) and \(S=(15/2)\langle r(nn-I/3)\rangle\). Finite selected/noisy harmonics require their own response rather than exact exponentiation of that fit.

## 2. Retained response and finite-redshift order

The optical octupole is \(O_{abc}=(35/2)\langle f_\mu n_{\langle a}n_bn_{c\rangle}\rangle\), in magnitude units. With Frobenius norms,
\[
O=\kappa L_Sd+R_3,\quad
\|R_3\|\le E_3(\epsilon)
=\sqrt{35/2}\frac{\kappa\epsilon^3}{3(1-\epsilon)},
\tag{H3}
\]
\[
(L_Sd)_{abc}=d_{(a}S_{bc)}
-\frac2{15}[\delta_{ab}(Sd)_c+\delta_{ac}(Sd)_b+\delta_{bc}(Sd)_a].
\]
This is Proposition 3/(26) and T6–T8: it controls the angular logarithm's remainder. It does not include finite distance or selection.

The pinned distance statement is \(d_L=cz/\mathcal H+O(z^2)\). Its **magnitude** correction is generally \(O(z)\), because taking a ratio first divides by the leading \(z\): if
\[
d_L=\frac{cz}{H(1+q)}[1+z a_1(n)+O(z^2)],
\]
then
\[
5\log_{10}\frac{d_L}{cz/H}
=-\kappa\ln(1+q)+\kappa z a_1(n)+O(z^2).
\tag{H4}
\]
An \(O(z^2)\) magnitude remainder requires subtraction/modeling of the \(za_1\) term or an additional cancellation. For example, a uniform relative-distance bound \(|d_L/d_L^{(1)}-1|\le\alpha z_{max}<1\) gives
\[
B_z\le\sqrt{35/2}\,\frac{|\kappa|\alpha z_{max}}{1-\alpha z_{max}}
\tag{H5}
\]
for an ideal full-sphere octupole. A real estimator's norm and depth weights replace that projection factor as required. Without a bound on the finite-distance coefficient, the manuscript's angular \(E_3\) does not supply a numerical \(B_z\).

Similarly, \(B_{sel}\) bounds the octupole displacement produced by the actual sky mask, depth selection, calibration and fitting operator relative to the declared target response. It must come from that operator on a registered signal/nuisance class. Full-sphere orthogonality alone does not provide it.

## 3. Rigorous uncertain-shear repair

Let \(\|S-\widehat S\|_F\le e_S\), \(|d|\le D_{max}\), and suppose all input bounds hold on one joint event or deterministic feasible set. The pinned identity \(L_T^*L_T=M_T=(T:T)I/3+2T^2/5\) gives
\[
\|L_{\Delta S}\|_{op}^2
=\frac{\|\Delta S\|_F^2}{3}+\frac25\|\Delta S\|_{op}^2
\le\frac35e_S^2,
\tag{H6}
\]
because an STF three-by-three tensor obeys \(\|T\|_{op}^2\le2\|T\|_F^2/3\). Therefore, with exact \(\kappa\),
\[
\widehat O=\kappa L_{\widehat S}d+\widetilde r,\qquad
\|\widetilde r\|\le
\boxed{B=E_3+e_O+B_z+B_{sel}
+|\kappa|\sqrt{3/5}\,e_SD_{max}.}
\tag{H7}
\]
Here \(e_O\) is the remaining observational octupole error; terms are included once, according to their declared ownership. Uncertainty in the slope normalization/frame also belongs in the joint \(d,S\) region. An admissible choice of \(\epsilon\) must cover that whole region, not just the central estimates; \(D_{max}+\|\widehat S\|_{op}+e_S<1\) is a simple sufficient choice.

The mathematical \(\kappa=5/\ln10\) is exact. If a separate multiplicative magnitude calibration is represented by \(|\kappa_{true}-\widehat\kappa|\le e_\kappa\), \(\widehat\kappa\ne0\), replace the final term of (H7) by
\[
\kappa_{max}\sqrt{3/5}e_SD_{max}
+e_\kappa\|L_{\widehat S}\|_{op}D_{max},
\quad\kappa_{max}=|\widehat\kappa|+e_\kappa,
\]
and evaluate \(E_3\) with \(\kappa_{max}\). This is a calibration extension, not an additional cosmological parameter.

For \(\widehat S\ne0\), define
\[
\widehat M=M_{\widehat S},\quad
\widehat d=\widehat\kappa^{-1}\widehat M^{-1}(\widehat O:\widehat S),\quad
\widehat O_\perp=\widehat O-\widehat\kappa L_{\widehat S}\widehat d.
\tag{H8}
\]
Then
\[
|\widehat d-d|\le\frac{B}{|\widehat\kappa|s_{min}(L_{\widehat S})},\quad
\|\widehat O_\perp\|\le B.
\tag{H9}
\]
For a separate estimate \(|d-d_{obs}|\le e_d\), add \(e_d\) to the vector bound. These are conservative necessary tests. As \(\widehat S\to0\), the absolute inverse gain diverges; use direct response-set testing near that sector, with the pure-dipole cubic response (27) if its premises apply. If \(B=0\), use exact membership rather than dividing by zero.

## 4. One joint test uses the same seven-component budget

The vector and perpendicular inequalities share \(\widetilde r\). They are not two independent confirmations, and passing both need not satisfy their common bound. For fixed \(\widehat S,\widehat\kappa\) and \(e_d=0\), orthogonality gives the exact identity
\[
\|\widehat O-\widehat\kappa L_{\widehat S}d_{obs}\|^2
=\|\widehat O_\perp\|^2+
\widehat\kappa^2(\widehat d-d_{obs})^T
\widehat M(\widehat d-d_{obs}).
\tag{H10}
\]
The single requirement is that (H10) be at most \(B^2\). For example, orthogonal contributions each equal to \(0.8B\) pass the separate unit thresholds but have joint norm \(\sqrt{1.28}B>B\).

With \(e_d>0\), define the conservative profiled score
\[
Q_{joint,min}^2=\frac1{B^2}\left[\|\widehat O_\perp\|^2+
\widehat\kappa^2
\min_{|d-d_{obs}|\le e_d}
(\widehat d-d)^T\widehat M(\widehat d-d)\right].
\tag{H11}
\]
This is a three-dimensional convex trust-region problem, not a dynamical integration. Require \(Q_{joint,min}\le1\); also impose \(|d|\le D_{max}\) and directional positivity when constructing the physical feasible set. The familiar \(Q_{cpl}=\|\widehat O_\perp\|/B\le1\) is only its perpendicular necessary condition. For correlated/non-spherical observational errors, replace the ball envelope by the original joint error body/law and profile \(S,d\) and nuisances together. The enlarged ball (H7) preserves a valid outer bound but does not reproduce all those correlations or a sharp acceptance region.

Across depth windows, keep shared \(d,S\), calibration and finite-redshift response parameters only where the same-event model warrants them; retain cross-window covariance or a joint deterministic error set. Compatibility means the single joint response image intersects the observed joint region. A discrepancy can reject that specified response/error model. Compatibility alone does not attribute the octupole to acceleration–shear rather than finite distance, selection or observer/source mismatch; comparison requires their distinct registered depth and processing responses. No independent-test multiplication or causal assignment follows from the two scalar inequalities.
