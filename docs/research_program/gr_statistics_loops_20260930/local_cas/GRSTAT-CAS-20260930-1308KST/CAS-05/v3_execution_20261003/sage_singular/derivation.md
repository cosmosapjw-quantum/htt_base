# Independent SageMath/Singular finite CAS-05 v3 axis

The only mathematical inputs are `EXECUTION_CONTRACT_V3.json` (SHA-256
`a67bf54921c80d35865d28dfce86d0ff9670270a807d5f2f45f25e3e7029537f`),
`NEUTRAL_INPUT.json` (`0868c1f15226e71926dad034319b85c73a9ca9c7d3c72064e06ff65d0112b27b`),
and `COMMON_SPEC.md` (`4714827e52acf3cb149f4014ac50ab2aa995dd4a0526f6b26ac7257807fe1897`).
Here (x^0=t=c,t_{\rm physical}), signature is ((-+++)), (b>0),
\(\Lambda<3b\), \(\kappa=8\pi G_N/c^4>0\), (c>0), and \(\lambda\) is any
finite real. The statement `semantics.exact_statement[2]` is C03; index 3 does
not exist. Coefficient matrices (S=(M+M^T)/2), (W=(M-M^T)/2) are not
kinematic shear/vorticity tensors.

## C01: metric, stress and finite normalized eigenvector jet

The Sage code starts from (g_{ab}=E\eta_{ab}), (E=e^{2\phi}>0),
(g^{ab}=E^{-1}\eta^{ab}), and
(\partial_\mu g_{ab}=2E\phi_\mu\eta_{ab}). It constructs
(\Gamma^a{}_{bc}=g^{ad}(\partial_b g_{dc}+\partial_c g_{db}-\partial_d g_{bc})/2),
differentiates that connection with the formal independent variables
(\phi_a,\phi_{ab}), and forms (R_{ab}) and (G_{ab}) with the declared
curvature sign. The exact residual against

\[
G_{ab}=-2\phi_{ab}+2\phi_a\phi_b+2\eta_{ab}\Box_\eta\phi
       +\eta_{ab}(\partial\phi)^2_\eta
\]

is zero in every component. The displayed expression is a derived comparison,
not a starting definition. For
(\phi=-bt^2-br^2/2+\lambda t^2x/2), the origin result is
(G_{00}=6b\), all other (G_{ab}=0). Its only nonzero first derivatives are
(\partial_0G_{01}=\partial_0G_{10}=-2\lambda\) and
(\partial_1G_{11}=\partial_1G_{22}=\partial_1G_{33}=-2\lambda\).
Consequently (\epsilon=(6b-\Lambda)/\kappa),
(p_1=p_2=p_3=\Lambda/\kappa), and
(\epsilon+p_i=6b/\kappa>0). This is an Einstein-defined stress, with no EOS.

At the origin (u=(1,0,0,0)), future normalized. Differentiating
(T^a{}_b u^b=-\epsilon u^a) gives all 16 residuals
(\partial_\mu T^a{}_0+(T^a{}_a+\epsilon)\partial_\mu u^a
+(\partial_\mu\epsilon)\delta^a_0=0\); differentiating (g(u,u)=-1)
gives (\partial_\mu u^0=0). Sage evaluates every one of these residuals to
zero with (\partial_0u^1=\lambda/(3b)) and the other eleven spatial rates
zero. Thus the finite origin acceleration is (A^1=c^2\lambda/(3b)).
The exact non-EOS witness is (\partial_1\epsilon=0) and
(\partial_1p_2=-2\lambda/\kappa\), nonzero when (\lambda\ne0).
For (\lambda=0) this witness vanishes; the contracted equalities still hold.

## C02: orthonormal ray contraction

On (t=y=z=0,x=s), (\phi=-bs^2/2). The code first derives the coordinate
contraction (G_{00}+G_{22}=6b-2\lambda s), then applies
(E_a=e^{-\phi}\partial_a) to both frame legs. The \(\Lambda g\) terms cancel,
and its exact symbolic frame residual is

\[
\kappa(\epsilon+p_2)=e^{bs^2}(6b-2\lambda s).
\]

The exponential is positive for real (s,b). At \(\lambda=0\), the
parenthesis is (6b>0) for all finite (s). For \(\lambda\ne0\), its zero is
(s=3b/\lambda); this is the member-dependent gap-loss location, not a
uniform neighborhood radius. The frame quantities here are the stipulated ray
contractions. No smooth eigenframe on that ray is inferred.

## C03: full metric-derived cubic jet

With (r^2=x^2+y^2+z^2), the source is exactly
(H_{00}=0\), (H_{0i}=-tr^2q_i/2-r^2W_{ij}x^j/5\),
(H_{ij}=-\delta_{ij}tS_{kl}x^kx^l/2\). Sage and Singular independently
differentiate every symmetric (H) component and confirm all its origin
derivatives through order two vanish. The metric representative
(\eta+2\phi_0\eta+H) has the same derivatives through order three as
(e^{2\phi_0}\eta+H), because \(\phi_0\) is quadratic and the exponential
remainder starts at coordinate order four.

Sage computes the origin and first Einstein derivatives directly from the
representative metric's connection, Ricci tensor and scalar, including the
background. Since \(\partial g(0)=0\), the connection is zero there; product
terms and derivatives of the inverse metric first affect higher coordinate
order. Separately it computes the flat linearized Einstein operator on (H)
and requires equality of all 40 first-derivative coefficients. Singular
independently builds that polynomial operator from the ten (H_{ab}) entries;
the wrapper requires exact coefficient parity in all 40 entries.

Writing \(J_\mu=\partial_\mu\delta G(0)\), the complete symmetric matrices are

\[
J_0=\begin{pmatrix}
\mathrm{tr}M&q_1&q_2&q_3\\
q_1&-(m_{22}+m_{33})/2&(m_{12}+m_{21})/4&(m_{13}+m_{31})/4\\
q_2&(m_{12}+m_{21})/4&-(m_{11}+m_{33})/2&(m_{23}+m_{32})/4\\
q_3&(m_{13}+m_{31})/4&(m_{23}+m_{32})/4&-(m_{11}+m_{22})/2
\end{pmatrix},
\]

\[
J_1=\begin{pmatrix}
0&m_{11}&m_{21}&m_{31}\\m_{11}&0&q_2/2&q_3/2\\
m_{21}&q_2/2&-q_1&0\\m_{31}&q_3/2&0&-q_1
\end{pmatrix},\quad
J_2=\begin{pmatrix}
0&m_{12}&m_{22}&m_{32}\\m_{12}&-q_2&q_1/2&0\\
m_{22}&q_1/2&0&q_3/2\\m_{32}&0&q_3/2&-q_2
\end{pmatrix},
\]

\[
J_3=\begin{pmatrix}
0&m_{13}&m_{23}&m_{33}\\m_{13}&-q_3&0&q_1/2\\
m_{23}&0&-q_3&q_2/2\\m_{33}&q_1/2&q_2/2&0
\end{pmatrix}.
\]

`result.json` contains the computed 40 coefficients and the full 40-entry
image for each of the twelve ordered basis vectors (k_{01},\dots,k_{33}).
The basis substitution explicitly honors the transpose
(q_i=-6bk_{0i}), (M_{ij}=-6bk_{ji}); for example (k_{12}) selects
(M_{21}), not (M_{12}). Thus (\delta G_{0i}=q_it+M_{ij}x^j\).
The explicit right inverse, valid for (b>0), is
(k_{0i}=-q_i/(6b)), (k_{ji}=-M_{ij}/(6b)).
Sage checks every arbitrary-(k) normalized induced-eigenvector residual
(6b,k_{\mu i}+\partial_\mu\delta G_{0i}=0) and all twelve basis projections.
Singular checks all twelve inverse remainders with a Groebner basis containing
(6bB-1\), so the inverse is certified in the declared nonzero-(b) locus.
Finally both engines calculate all four origin Bianchi contractions
(\sum_a\eta^{aa}\partial_a\delta G_{ab}=0). Their four exact remainders
are zero. This is a finite origin check, not a neighborhood identity.

The algebra uses dimensionless (g,H,\phi,u); (b,\Lambda) carry
length\(^{-2}\), \(\lambda,q,M\) length\(^{-3}\), (k) length\(^{-1}\),
and (G\) length\(^{-2}\). Positive norms are not invoked.
The axis result is a specified mathematical-component calculation. Smooth
isolated eigenfields, IFT, a Lorentzian/strict-DEC neighborhood, an EOS/action,
CAS-06, nonlinear away-from-origin realizability, full theorem, and scientific
admission remain outside its executed scope.
