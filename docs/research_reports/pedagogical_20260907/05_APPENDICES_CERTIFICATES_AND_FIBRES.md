# Appendix A. Polynomial identities used in the angular calculation

## A.1 Legendre coefficients and their norm

Expanding Rodrigues' formula in Eq. (3.1) gives the finite expression

\[
P_\ell(x)=2^{-\ell}\sum_{j=0}^{\lfloor\ell/2\rfloor}
(-1)^j\frac{(2\ell-2j)!}{j!(\ell-j)!(\ell-2j)!}\,x^{\ell-2j}.
\tag{A.1}
\]

This formula defines every polynomial needed in the report using factorials and powers. Terms with a negative factorial argument are omitted. In particular, the leading coefficient is \((2\ell)!/[2^\ell(\ell!)^2]\), so the \(\ell\)-th derivative is \((2\ell)!/(2^\ell\ell!)\).

To obtain the norm without consulting an orthogonality table, substitute Rodrigues' formula into one factor of \(\int_{-1}^1P_\ell^2dx\) and integrate by parts \(\ell\) times. The derivatives of \((x^2-1)^\ell\) below order \(\ell\) vanish at both endpoints. Therefore

\[
\int_{-1}^1P_\ell^2dx
=\frac{(2\ell)!}{2^{2\ell}(\ell!)^2}
\int_{-1}^1(1-x^2)^\ell dx.
\tag{A.2}
\]

Let \(J_\ell\) be the final integral. Integrating the derivative of \(x(1-x^2)^\ell\) gives
\(0=J_\ell-2\ell\int x^2(1-x^2)^{\ell-1}dx\).
Since the second integral is \(J_{\ell-1}-J_\ell\),
\(J_\ell=2\ell J_{\ell-1}/(2\ell+1)\), with \(J_0=2\).
Thus
\(J_\ell=2^{2\ell+1}(\ell!)^2/(2\ell+1)!\), and Eq. (A.2) reduces to \(2/(2\ell+1)\).

Differentiating the Legendre equation \((1-x^2)P_\ell''-2xP_\ell'+\ell(\ell+1)P_\ell=0\) successively gives the weighted derivative identity

\[
\frac{d^m}{dx^m}\left[(1-x^2)^mP_\ell^{(m)}(x)\right]
=(-1)^m\frac{(\ell+m)!}{(\ell-m)!}P_\ell(x).
\tag{A.3}
\]

It can also be checked term by term using Eq. (A.1): differentiate each monomial, multiply by the binomial expansion of \((1-x^2)^m\), and collect equal powers. The resulting coefficient of each \(x^{\ell-2j}\) is the coefficient in Eq. (A.1) multiplied by the common factor in Eq. (A.3). Integration by parts \(m\) times therefore gives

\[
\int_{-1}^1(1-x^2)^m[P_\ell^{(m)}]^2dx
=\frac{(\ell+m)!}{(\ell-m)!}\int_{-1}^1P_\ell^2dx.
\tag{A.4}
\]

All endpoint terms vanish, because the weighted polynomial and its first \(m-1\) derivatives have the corresponding zeros. This proves the normalisation in Eq. (3.3). The Legendre equation itself follows by substituting Eq. (A.1) and equating adjacent powers. Thus no infinite-series or unproved completeness assertion is needed for these finite-band calculations.

## A.2 Associated recurrences and axial boost coefficients

Write \(F_{\ell m}=P_\ell^m\). The two identities needed for the axial derivative are

\[
(2\ell+1)xF_{\ell m}
=(\ell-m+1)F_{\ell+1,m}+(\ell+m)F_{\ell-1,m},
\]

\[
(1-x^2)F_{\ell m}'
=-\ell xF_{\ell m}+(\ell+m)F_{\ell-1,m}.
\tag{A.5}
\]

Both are finite polynomial identities after dividing out the common factor \((-1)^m(1-x^2)^{m/2}\). For example, the second becomes

\[
(1-x^2)P_\ell^{(m+1)}
+(\ell-m)xP_\ell^{(m)}
-(\ell+m)P_{\ell-1}^{(m)}=0.
\tag{A.6}
\]

Equation (A.1) verifies it by matching the coefficient of every \(x^{\ell-m+1-2j}\); the leading powers cancel and the remaining two factorial ratios give the adjacent \(j\) term. The first identity follows in the same way with \(P_{\ell+1}^{(m)}\), \(P_\ell^{(m)}\) and \(P_{\ell-1}^{(m)}\). These formulas include the vanishing terms when \(\ell-1<m\).

Multiplying by the normalisation in Eq. (3.2), the coefficient of \(Y_{\ell-1,m}\) in the first identity is

\[
\frac{\ell+m}{2\ell+1}
\sqrt{\frac{(2\ell+1)(\ell-m)!/(\ell+m)!}
{(2\ell-1)(\ell-1-m)!/(\ell-1+m)!}}
=\sqrt{\frac{\ell^2-m^2}{(2\ell-1)(2\ell+1)}}.
\tag{A.7}
\]

The upper coefficient is obtained with \(\ell+1\). Insert those two coefficients into the second identity to obtain Eq. (11.5), and then Eq. (11.6). This displays the sign and normalisation of the nearest-neighbour boost coupling explicitly.

# Appendix B. Exact axial certificate in finite arithmetic

## B.1 All matrix entries from rational power integrals

Let \(a=-3/4\), \(b=3/4\), and define the weighted moment for any nonnegative integer \(k\):

\[
J_k=\int_{-1}^1w(x)x^kdx
=\frac{b^{k+1}-a^{k+1}}{2(k+1)}
+\frac{2(b^{k+2}-a^{k+2})}{3(k+2)}
+\frac{1-b^{k+1}}{k+1}.
\tag{B.1}
\]

This is simply the integral on each nonzero piece of the weight. If
\((1-x^2)^mP_\ell^{(m)}P_k^{(m)}=\sum_j c_jx^j\), its integral in Eq. (11.7) is \(\sum_jc_jJ_j\). Equations (A.1) and (B.1) therefore determine every entry using finitely many rational operations and the displayed harmonic square roots.

One can avoid square roots during elimination. Set

\[
\widetilde N_{\ell k}=\int_{-1}^1w(x)P_\ell^m(x)P_k^m(x)dx,
\qquad
d_{\ell m}=\frac{(2\ell+1)(\ell-m)!}{2(\ell+m)!}.
\tag{B.2}
\]

The integral is rational by the common-factor cancellation in Eq. (11.7). In this unnormalised basis,

\[
\widetilde R_{\ell p}
=-\frac{p(p+m)}{2p+1}\widetilde N_{\ell,p-1}
+\frac{(p+1)(p-m+1)}{2p+1}\widetilde N_{\ell,p+1}.
\tag{B.3}
\]

These coefficients follow directly by inserting Eq. (A.5) into \(xP_p^m-(1-x^2)(P_p^m)'\). With diagonal matrices \(D_{\rm fit}\) and \(D_{\rm src}\) whose entries are \(\sqrt{d_{\ell m}}\), the normalised matrices satisfy

\[
N_m=D_{\rm fit}\widetilde N_mD_{\rm fit},\qquad
R_m=D_{\rm fit}\widetilde R_mD_{\rm src},
\]

\[
N_m^{-1}R_m
=D_{\rm fit}^{-1}\widetilde N_m^{-1}\widetilde R_mD_{\rm src}.
\tag{B.4}
\]

For a selected square retained minor \(\widetilde K_{I,J}\),

\[
\det(K_{I,J})^2
=\det(\widetilde K_{I,J})^2
\frac{\prod_{p\in J}d_{pm}}{\prod_{\ell\in I}d_{\ell m}}.
\tag{B.5}
\]

The right side is rational. This is a complete arithmetic prescription for the squares tabulated below. The inverse can be computed by rational elimination, or by the adjugate formula: the \((i,j)\) entry of \(\operatorname{adj}A\) is \((-1)^{i+j}\) times the determinant obtained by deleting row \(j\) and column \(i\), and \(A^{-1}=\operatorname{adj}A/\det A\). Every determinant is the finite sum \(\sum_\pi\operatorname{sgn}(\pi)\prod_iA_{i,\pi(i)}\). Thus the certificate is defined without an external software package or unpublished matrix.

## B.2 Nonzero normal determinants

In order \(m=0,1,2,3,4,5\), the normalised normal-block determinants are the following exact fractions:

```text
m=0:
2371221567616482963655661538277
/ 124939643158494289811515067921858560

m=1:
1784012728720795037550100553
/ 1743019575313815427057966907392

m=2:
10945595347193184954026503331
/ 871509787656907713528983453696

m=3:
104531461379720327
/ 1585267068834414592

m=4:
665044625583572687
/ 3170534137668829184

m=5:
1 / 2
```

The division slash joins the numerator and denominator across the displayed line break. No rounding is used. Positivity also follows independently from Section 11.1; these values make the finite certificate explicit.

## B.3 Nonzero retained minors

For each \(m\), retain rows \(\ell=\max(m,2),\ldots,5\). Select the first as many source columns as there are rows. The following values are the exact squared determinants in the normalised coordinate convention of Eq. (11.7).

```text
m=0; source columns 7,8,9,10:
13854851227718467321621702138503980744130367185396095166590753194419819749485140749388736644495507
/ 2946385964528764001602729286917704836323445407941374503789674365768429551770231683936450693300224

m=1; source columns 7,8,9,10:
45897747416692690585791274614572327208356017181052125887012037607944001265218344300648587575
/ 11439368869955288869320571209776405550745656790554396265529415077685155349137762741139313524736

m=2; source columns 7,8,9,10:
39493718757090374514153222808257755001282326150716790292260982205042519060828776367475925
/ 215305412825852519355010761635586687254061841359588806014692042617344168936576686059039460687872

m=3; source columns 7,8,9:
3965156020663594870880515310630136258902710414400775484668459177
/ 613649291260366690751581334535331511253026015611909498783126158409990144

m=4; source columns 7,8:
33648590107505417977636161099564743354425815
/ 321031865290431140061490488646804497908163936256

m=5; source column 7:
1654580299939355708034129
/ 1995199839012425102786560
```

These are the retained exact tabulation, not newly rounded numerical determinants. Every fraction is positive, proving the needed nonvanishing once calculated by Eqs. (A.1), (B.1)–(B.5). The proof does not require the determinant squares to be large. It requires them to be nonzero. Their numerical scale cannot, however, substitute for a finite-precision error analysis.

The same construction defines blocks at other cutoffs, but the table is the certificate used for the stated \(L=12\) conclusion. We do not claim that printing these values supplies an interval certificate for nonaxial directions or for a finite pixelisation.

# Appendix C. What remains when only a contraction is retained?

This appendix explains two related geometric results in full rather than directing the reader to separate research notes. They concern normalised observable tensors at fixed quadrupole. They are not new empirical estimates or extensions of the physical MES assumptions.

## C.1 The contraction map and its minimum-norm solution

Fix a real unit STF2 tensor \(q\), and define \(L_qo=o:q\) on the seven-dimensional STF3 space. Proposition 9.1 gives

\[
L_q^*=\tfrac13B_q,\qquad L_qB_q=M_q,
\qquad M_q=I+\tfrac65q^2\succ0.
\tag{C.1}
\]

Thus \(L_qL_q^*=M_q/3\) is invertible, the contraction map is onto \(\mathbb R^3\), and its kernel \(N\) has dimension four. Its minimum-norm right inverse is

\[
R_q=B_qM_q^{-1}.
\tag{C.2}
\]

Indeed, \(L_qR_q=I\). For \(z\in N\), adjointness gives
\(\langle R_qv,z\rangle=3\langle M_q^{-1}v,L_qz\rangle=0\).
Every solution to \(L_qo=v\) is consequently

\[
o=R_qv+z,\qquad z\in N,
\qquad
\|o\|_F^2=3v^TM_q^{-1}v+\|z\|_F^2.
\tag{C.3}
\]

The first term is the unique minimum-norm solution; no nullspace vector can reduce its norm because the two summands are orthogonal.

## C.2 The exact unit-norm fibre

Define \(\eta_v=3v^TM_q^{-1}v\). By Eq. (C.3),

\[
F_q(v)=\{o:\|o\|_F=1,\ L_qo=v\}
=\begin{cases}
\varnothing,&\eta_v>1,\\
\{R_qv\},&\eta_v=1,\\
R_qv+\sqrt{1-\eta_v}\,S(N),&0\le\eta_v<1,
\end{cases}
\tag{C.4}
\]

where \(S(N)=\{z\in N:\|z\|_F=1\}\) is a three-sphere in a four-dimensional linear space. Existence, uniqueness at the boundary, and the sphere radius all follow by solving the final scalar norm equation in Eq. (C.3). There is no additional rotational quotient in this statement: \(q\) and \(v\) are fixed in a declared frame.

The image of the unit STF3 sphere under contraction is therefore the filled ellipsoid \(\eta_v\le1\), not merely its boundary. Interior points are possible because the nonzero kernel supplies the rest of the unit norm. Knowing \(q\), \(v\) and the norm generally leaves three continuous degrees of octupole morphology.

For a unit \(q\), Cayley–Hamilton gives \(q^3=q/2+(s_3/3)I\). Multiplication and reduction of \(q^3,q^4\) verify

\[
M_q^{-1}=\frac{40I+(15/2)s_3q-30q^2}{40+3s_3^2},
\qquad
\eta_v=\frac{120\mu_0+(45/2)s_3\mu_1-90\mu_2}{40+3s_3^2}.
\tag{C.5}
\]

To display the cancellation, multiplying the numerator matrix by \(I+(6/5)q^2\) produces
\(40I+(15/2)s_3q+18q^2+9s_3q^3-36q^4\).
Use \(q^4=q^2/2+(s_3/3)q\); the nonconstant terms cancel, leaving \((40+3s_3^2)I\). The moment formula then follows from \(\mu_j=v^Tq^jv\). The denominator is strictly positive.

This criterion is sufficient only for the reduced contraction-and-norm problem. Arbitrary trilinears in a full packet may still disagree with every member of this fibre. Equation (4.13) and forward replay are not replaced by a single scalar check.

## C.3 A sharp contraction bound

The squared operator norm of \(L_q\) is \(\lambda_{\max}(M_q)/3\). If \(a,b,c\) are eigenvalues of unit trace-free \(q\), then \(b+c=-a\) and
\(1=a^2+b^2+c^2\ge a^2+(b+c)^2/2=3a^2/2\).
Thus the largest squared eigenvalue is at most \(2/3\), giving

\[
\|o:q\|^2\le\frac35\|o\|_F^2,
\qquad
\boxed{\|O:Q\|^2\le\frac35(Q:Q)(O:O)}.
\tag{C.6}
\]

The second formula restores the physical temperature amplitudes; both sides have fourth-power temperature units. The bound is sharp. Take \(q=\operatorname{diag}(-1,-1,2)/\sqrt6\), let \(e_3\) be its third eigenvector and set \(o=B_qe_3/\|B_qe_3\|_F\). Proposition 9.1 gives \(\|B_qe_3\|_F^2=3(9/5)\), and contraction then has squared norm \((9/5)/3=3/5\). This example has repeated quadrupole eigenvalues and is not a cyclic inverse-chart example.

## C.4 Distances to the fibre

Let \(P=R_qL_q\), the orthogonal projector onto the complement of \(N\), and let \(\widehat o\) be any STF3 candidate. Put \(r=L_q\widehat o-v\). The least change needed to meet the affine contraction condition is \(R_qr\), since it lies orthogonal to every allowed nullspace displacement. Hence

\[
\operatorname{dist}(\widehat o,\{o:L_qo=v\})^2
=3r^TM_q^{-1}r.
\tag{C.7}
\]

If \(\eta_v\le1\), the unit-norm condition adds the distance within the kernel to the sphere of radius \(\sqrt{1-\eta_v}\). Orthogonality gives

\[
\operatorname{dist}(\widehat o,F_q(v))^2
=3r^TM_q^{-1}r+
\left(\|(I-P)\widehat o\|_F-\sqrt{1-\eta_v}\right)^2.
\tag{C.8}
\]

The distance from a vector of norm \(a\) to a centred sphere of radius \(b\) is \(|a-b|\): the reverse triangle inequality is a lower bound and the radial point attains it. If the vector is zero, every point on that sphere is equally near. This proves Eq. (C.8), including the zero-radius boundary case. It is a diagnostic distance, not permission to replace a malformed observed packet by a projected one.

## C.5 Hausdorff distance and boundary sensitivity

For nonempty compact sets, the Hausdorff distance is the larger of the two greatest nearest-point distances from one set to the other. For two feasible contractions at the same \(q\), define \(\rho_v=\sqrt{1-\eta_v}\) and \(\rho_w=\sqrt{1-\eta_w}\). Their centres differ in \(N^\perp\), and both spheres lie in translates of the same \(N\). For unit \(z,z'\in N\),

\[
\|R_q(v-w)+\rho_vz-\rho_wz'\|_F^2
=\|R_q(v-w)\|_F^2+\|\rho_vz-\rho_wz'\|_F^2.
\]

For any fixed \(z\), the second term has minimum \((\rho_v-\rho_w)^2\), independent of \(z\). The same holds with the roles reversed, including either zero radius. We have therefore proved

\[
\boxed{d_H(F_q(v),F_q(w))^2
=3(v-w)^TM_q^{-1}(v-w)
+(\sqrt{1-\eta_v}-\sqrt{1-\eta_w})^2.}
\tag{C.9}
\]

Write \(\|a\|_q=\sqrt{3a^TM_q^{-1}a}\), and let \(s=\|v-w\|_q\). On the feasible ellipsoid,
\(|\eta_v-\eta_w|\le(\|v\|_q+\|w\|_q)s\le2s\).
Since \(|\sqrt a-\sqrt b|^2\le|a-b|\) for nonnegative \(a,b\),

\[
d_H(F_q(v),F_q(w))\le\sqrt{s^2+2s}.
\tag{C.10}
\]

If both \(\eta_v,\eta_w\le1-\delta\) for \(\delta>0\), divide their difference by \(\rho_v+\rho_w\ge2\sqrt\delta\) and use \(\|v\|_q+\|w\|_q\le2\sqrt{1-\delta}\). Equation (C.9) then gives

\[
d_H(F_q(v),F_q(w))\le\delta^{-1/2}\|v-w\|_q.
\tag{C.11}
\]

This is Lipschitz control away from saturation. Near the boundary, the square-root exponent is exact. Choose \(v_*\) with \(\eta_*=1\) and set \(v_t=(1-t)v_*\), \(0<t<1\). Then \(\|v_t-v_*\|_q=t\) and \(\rho_t^2=2t-t^2\), so

\[
\boxed{d_H(F_q(v_t),F_q(v_*))=\sqrt{2t}.}
\tag{C.12}
\]

The ratio to \(t^\alpha\) diverges for every \(\alpha>1/2\). Thus no uniform Lipschitz bound extends to this boundary. This concerns feasible perturbations; an outward perturbation can make the set empty, where the stated nonempty-set distance no longer applies.

The effect is not restricted to a singular quadrupole. Take

\[
q=\frac1{\sqrt2}\operatorname{diag}(-1,0,1),\quad
v_*=(\sqrt{8/45},1/3,\sqrt{8/45})^T.
\tag{C.13}
\]

Here \(M_q=\operatorname{diag}(8/5,1,8/5)\), \(\eta_*=1\), and

\[
K_*^TK_*=\frac1{45}
\begin{pmatrix}21&0&8\\0&8&0\\8&0&4\end{pmatrix},
\qquad
\det K_*=\frac{4\sqrt2}{135}>0.
\tag{C.14}
\]

The Gram eigenvalues are \((25-\sqrt{545})/90\), \(8/45\), and \((25+\sqrt{545})/90\). Hence \(\kappa_2(K_*)=\sqrt{(25+\sqrt{545})/(25-\sqrt{545})}\), approximately 5.40516. Along \(v_t\), \(K_t=(1-t)K_*\), so this relative condition number is constant. The linear contraction matrix is also well conditioned, with \(\kappa_2(M_q)=8/5\). The square-root sensitivity arises from the unit-norm boundary, not from a singular frame.

An explicit unit kernel tensor has the six permutations of component 123 equal to \(1/\sqrt6\), all other entries zero. It is STF and contracts to zero with this diagonal \(q\). Writing it as \(z\), the tensors
\(o_t=(1-t)R_qv_*+\sqrt{2t-t^2}z\) verify Eq. (C.12) directly.

This is not a counterexample to complete packet reconstruction. The trilinear coordinates in the changing frame satisfy
\(\tau_t=(1-t)^3[(1-t)A_*R_qv_*+\sqrt{2t-t^2}A_*z]\),
where \(A_*\) evaluates a tensor on triples of \(K_*\)'s columns. Since that basis is invertible, \(A_*\) is injective and \(A_*z\ne0\). The full packet therefore already changes at square-root order. Discarding those coordinates changes the information problem.

# Appendix D. Notation and the status of statements

| Symbol or term | Meaning in this report |
|---|---|
| \(T(n),T_0\) | Directional thermodynamic temperature and its sphere average |
| \(Y_{\ell m},a_{\ell m},C_\ell\) | Normalised spherical harmonic, its coefficient, and the specified sky's multipole power |
| \(c_\ell,r_\ell,G_\ell\) | Orthonormal real coefficients, raw real/imaginary coefficients, and their coordinate metric |
| \(Q,O\) | Temperature quadrupole STF2 and octupole STF3 tensors |
| \(A_Q,A_O,q,o\) | Frobenius amplitudes and unit-normalised observable tensors |
| \(v=o:q\) | Dimensionless observable contraction vector; never a physical velocity in this use |
| \(K,G,\chi\) | Krylov basis matrix, its Gram matrix, and its signed determinant |
| \(s_3,\mu_r,\tau_{ijk}\) | Cubic quadrupole invariant, contraction moments, and symmetric trilinear coordinates |
| \(u,h,D,A,\Theta,H_g,\sigma,\omega\) | Observer, rest-space metric, projected derivative, acceleration, geometric expansion/Hubble rate, shear and vorticity |
| \(E_\gamma,e,n\) | Photon energy, propagation direction and outward sky direction \(n=-e\) |
| \(\beta\) | A specifically labelled physical relative velocity divided by \(c\) |
| \(\epsilon_\ell,\epsilon_\ell',\epsilon_\ell^*\) | Multipole and normalised derivative envelopes in physical input M |
| \(B_\sigma,B_\omega,U_\sigma,U_\omega\) | Conditional MES norm ceilings and their quadratic versions |
| \(\rho_B\) | Gauge of a specified admissible body, not a p-value |
| \(\mathcal R,\Theta(y;\eta)\) | Declared response and realised compatible physical states |
| \(p_i,p_{\mathcal G}\) | Exchangeable-row and finite-group ranks, with different reference objects |
| \(B_Q,M_Q\) | STF quadrupole-to-octupole response map and one third of its normal matrix |
| \(N,R,K^{\rm cont}\) | Continuum fit normal matrix, generator overlap and retained response; distinguished by section from the right inverse \(R_q\) |
| \(H, P_H, J_{\rm surv}\) | Nuisance image, its orthogonal projector and surviving response |
| \(E_{fi},r_f,\Gamma_E,W\) | Error directions, family radii, positive error envelope and whitening map |
| \(F_q(v),\eta_v,d_H\) | Fixed-quadrupole unit-contraction fibre, its minimum squared norm and Hausdorff distance |

A theorem in the text is a conditional mathematical statement proved under the hypotheses written with it. Physical input M is an imported radiation–geometry premise and its scale estimates; no proof of the entire spacetime theorem is claimed. The finite-direction rank ladder and finite-pixel outcomes are reported computations with stated domains, not universal theorems. The exact axial minor certificate contains both its defining arithmetic and its tabulated values. The fibre appendix is a direct finite-dimensional derivation, not an empirical velocity analysis.

The mathematical exposition is independent of repository issue numbers, private execution paths or a claim ledger. Its conceptual lineage includes covariant cosmology, conditional isotropy bounds, tensor invariants, partial identification, randomisation inference and matrix perturbation theory. The invariant-theory literature provides context for separating orbit information; it does not replace the constructive cyclic proof in Section 4. [@OLIVE_KOLEV_AUFFRAY_2013; @BORNSEN_VANDEVEN_2018; @LOPATIN_FERREIRA_2018]

The older report's complete proof of the global almost-isotropy result is not silently supplied by elementary tensor algebra. A reader can use the present report to understand the stated physical assumptions, every subsequent inference and the explicit limitations. A reader wishing to derive the imported bounds from the full Einstein–Liouville hierarchy will still need that separate physical derivation. This is the only intended theory-source dependency of the main conditional construction; it is stated here so that self-contained deductions are not confused with an unproved foundational input.

# References
