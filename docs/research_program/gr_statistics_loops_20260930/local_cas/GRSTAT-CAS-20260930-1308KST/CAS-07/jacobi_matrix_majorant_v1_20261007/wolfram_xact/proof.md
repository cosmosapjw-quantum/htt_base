# CAS-07 M04: two-dimensional Jacobi matrix majorant

Scope: the exact four M04 obligations only. Let (E=\mathbb R^2) with its Euclidean norm, (B=\mathcal L(E,E)) with induced operator norm, (L>0), (K\geq0), and (0\leq s\leq L). All derivatives and integrals below are in the finite-dimensional Banach space (B). The supplied regularity gives continuous (D,D_1,D_2,R), including one-sided endpoint derivatives as needed. The accepted M02 statement is the two-derivative integral Taylor formula, applied componentwise in any fixed basis of (B); no matrix product is interchanged in that application.

For every matrix entry (i,j\in\{1,2\}), M02 gives

\[
D_{ij}(s)=D_{ij}(0)+s(D_1)_{ij}(0)+\int_0^s(s-t)(D_2)_{ij}(t)\,dt.
\]

The four entrywise identities assemble into one Bochner identity because coordinate evaluation commutes with finite-dimensional integration. Insert (D(0)=0), (D_1(0)=I), and (D_2(t)=-R(t)\circ D(t)) *after* the Taylor step. Thus

\[
\boxed{D(s)=sI-\int_0^s(s-t)R(t)\circ D(t)\,dt.}
\]

Composition remains in that order. xTensor represents it as (R^a{}_cD^c{}_b v^b) on a two-dimensional screen and keeps (D^a{}_cR^c{}_b v^b) distinct. An exact (2\times2) witness has (R=\left(\begin{smallmatrix}0&1\\0&0\end{smallmatrix}\right)), (D=\left(\begin{smallmatrix}0&0\\1&0\end{smallmatrix}\right)), for which (RD\ne DR). This witness checks ordering only; it is not used to infer the universal theorem.

Set (u(s)=\|D(s)\|_{\mathrm{op}}\). Since (D) is continuous and the norm is continuous, (u) is continuous and nonnegative. The Bochner triangle inequality, (s-t\geq0), (\|I\|_{\mathrm{op}}=1), and operator-norm submultiplicativity imply

\[
\begin{aligned}
u(s)&\leq s+\int_0^s(s-t)\|R(t)\circ D(t)\|_{\mathrm{op}}\,dt\\
&\leq s+\int_0^s(s-t)\|R(t)\|_{\mathrm{op}}u(t)\,dt\\
&\leq s+K\int_0^s(s-t)u(t)\,dt.
\end{aligned}
\]

No Frobenius norm, self-adjointness, positivity of (R), or commutation is needed. This is exactly the accepted M03 scalar comparison premise on ([0,L]). Therefore M03 gives (u(s)\leq f_K(s)), where (f_0(s)=s) and (f_K(s)=\sinh(\sqrt K s)/\sqrt K) for (K>0). Wolfram verifies the exact equality (f_K(s)=s+K\int_0^s(s-t)f_K(t)\,dt) for (K>0); for (K=0) the equation reduces to (f_0=s). M03, not a finite series or sampled test, supplies the universal comparison step.

Finally subtract (sI) from the Volterra identity. The same triangle and submultiplicative inequalities, followed by (u\leq f_K), give

\[
\|D(s)-sI\|_{\mathrm{op}}
\leq K\int_0^s(s-t)u(t)\,dt
\leq K\int_0^s(s-t)f_K(t)\,dt
=f_K(s)-s.
\]

If (K=0), the operator norm bound forces (R(t)=0) throughout ([0,L]), so the Volterra identity gives (D(s)=sI) exactly and both estimates hold with equality. At (s=0), the integral vanishes and (D(0)=0=f_K(0)). The bounds have length units: (K) has inverse-length-squared units, (R) the same, and (D,s,f_K) have length units. These arguments establish only matrix Volterra and norm majorization. They do not establish determinant sign, singular values, area distance, physical transport existence, or scientific admission.

`check.wl` verifies the arbitrary-component integral Taylor identity by matching second derivatives and initial value/slope (uniqueness for the resulting scalar ODE), the ordered xTensor screen contraction and noncommuting witness, the Volterra kernel differentiation, and the exact scalar majorant integral. The norm inequalities above are the analytic certificate; the executable tests do not pretend to prove Banach norm properties by finite sampling.
