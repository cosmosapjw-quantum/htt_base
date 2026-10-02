# CAS-01 independent SymPy finite-component proof

Input identity: `EXECUTION_CONTRACT.json` SHA-256
`edc2df3348528a699b987ae1893ab76630e96b9915d11117db7916d005c406f1`;
`COMMON_SPEC.md` SHA-256
`4714827e52acf3cb149f4014ac50ab2aa995dd4a0526f6b26ac7257807fe1897`.
The companion `run.py` performs exact SymPy matrix and polynomial checks for
the four specified finite components. No sibling derivation or result was read.

## Domain and conventions

Throughout, (g=\operatorname{diag}(-1,1,1,1)), (c>0), (u^Tgu=-1),
and (u^0>0). All displayed matrices (S,B,Q,W) have two covariant
indices. (u_\flat=gu), (H^a{}_b=\delta^a_b+u^a u_b), and
(h=g+u_\flat u_\flat^T). The shell polynomial is
(u_0^2-u_1^2-u_2^2-u_3^2-1). Exact zero assertions for generic (u)
are polynomial remainders modulo this shell. A rational chart used only for
the normalized-seed differentiation has
(u=((1+r^2),2r_1,2r_2,2r_3)/(1-r^2)), with (r^2<1).
Every future unit (u) occurs uniquely: (r_i=u^i/(u^0+1)), and
(r^2=(u^0-1)/(u^0+1)<1). Thus the chart does not specialize to rest.
The positive norm square root is selected; continuity gives a future
timelike neighborhood of the origin for each fixed finite (Q).

## CAS-01-C01

Set \(\alpha=u^TSu\) and \(B=S+\alpha g\), for arbitrary symmetric (S).
Then \(u^TBu=\alpha(1+u^Tgu)=0\). Under (S\mapsto S+a g),
\(\alpha\mapsto\alpha+a u^Tgu=\alpha-a\), so (B) is unchanged.

For the full null-cone kernel, write an arbitrary symmetric form (T) and
\(F(n)=T_{00}-2T_{0i}n_i+T_{ij}n_in_j\). If (F(n)=0) on the unit
sphere, evaluating (n=\pm e_i) gives (T_{0i}=0) and
(T_{ii}=-T_{00}), for each (i). Evaluating
(n=(e_i+e_j)/\sqrt2) gives (T_{ij}=0) for every (i<j).
Therefore (T=(-T_{00})g). Conversely (K^TgK=0) for every
(K=(-1,n)) with (n^2=1). `run.py` independently builds the nine
evaluation equations, checks their exact rank is nine, verifies (g) lies
in the kernel, and verifies the converse as a sphere-polynomial identity.

## CAS-01-C02

Let (b=Bu). From C01, (b^Tu=0). For arbitrary antisymmetric (L),
\(W=H^TLH\) is covariant skew and satisfies (Wu=0). This represents
every spatial covariant skew form: if (W^T=-W) and (Wu=0), then
\(H^TWH=W\). With
\(Q=B+b u_\flat^T-u_\flat b^T+W\),
\[
Qu=b+b(u_\flat^Tu)-u_\flat(b^Tu)+Wu=0,
\quad \frac{Q+Q^T}{2}=B,
\quad Q^Tu=b-u_\flat(b^Tu)-b(u_\flat^Tu)+W^Tu=2b.
\]
The script checks these equations as exact matrix remainders on the shell.

Set (D=H^TBH), \(\theta=\operatorname{tr}(gB)\), and
\(\sigma=D-\theta h/3\). (D) and (\sigma) annihilate (u),
\(\operatorname{tr}(gD)=\theta\), and (\sigma) is symmetric with
zero spatial trace. These are also checked exactly. In the derivative-first
convention (Q_{ab}=\nabla_a U_b), (U=cu), so
\(A_b=c u^aQ_{ab}=2c b_b\). If instead (B) is defined from
\(\nabla u\), the physical acceleration is (2c^2 Bu).
Because (x^0=ct) has length dimension, (Q,B,D,\theta,\sigma,W)
have inverse-time units, while (A) has length/time-squared units.
The stipulated spatial convention (W_{ij}=\epsilon_{ijk}\omega_k)
implies (Wx=-\omega\times x), and this derivative-first (W)
is (-c\) times the stated velocity-first book vorticity. The arbitrary
(W) remains in the kernel of the symmetric slope; no zero-slope
vorticity recovery follows.

## CAS-01-C03

At (u=o=(1,0,0,0)), (B_{00}=0), (b_i=B_{i0}), and
\(A_i=2cB_{0i}\). With (K=(-1,n)), (n^2=1),
\[
B(K,K)=B_{ij}n_in_j-2B_{0i}n_i
=\theta/3+\sigma_{ij}n_in_j-A_i n_i/c.
\]
The exact residual reduces to zero modulo (n^2-1). For general
(S_{00}=h_0\), (S_{0i}=-h_{1i}/2), and symmetric tracefree
(S_{ij}=h_{2ij}), direct expansion gives
\(S(K,K)=h_0+h_1\cdot n+h_2:nn\), checked with independent free
components of (h_2). The (h_1=-A/c) identification applies to
the observer-rest (B), not to an arbitrary boosted-frame expansion.

## CAS-01-C04

The script differentiates the actual four-component expression
\(v=u+c^{-1}gQ^Tx\) and its positive-root normalized form
\(f=v/\sqrt{-v^Tgv}\). It uses (Q=MH) for a generic (4\times4)
matrix (M). This covers every (Q) satisfying (Qu=0), because
(QH=Q+(Qu)u_\flat^T=Q). In the future-hyperboloid chart,
\(-v(0)^Tgv(0)=1\). Moreover
\(\partial_a(-v^Tgv)|_0=-2Q_{ab}u^b/c=0\). Therefore the direct
SymPy derivative has
\[
f(0)=u,\qquad \partial_a f^b|_0=g^{bd}Q_{ad}/c.
\]
The script checks all 16 derivative entries exactly after differentiating
the square-root expression. Thus (U=cf) has the prescribed covariant
first jet (\partial_a U_b|_0=Q_{ab}) in normal coordinates. The negative
unit branch is excluded by the future and positive-root conditions.

## Boundary

These results prove the four contracted finite/local components only.
The Jacobi vertex Taylor order and screen invariance need a geometric ODE
argument; smooth timelike local flow and source extension need a separate
analytic construction. Both remain **OPEN** here. No fixed Einstein matter
realization, finite catalogue inference, propagation/sourceward sign
exchange, or scientific admission is asserted.
