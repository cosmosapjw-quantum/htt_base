# CAS14 finite vorticity inverse: Sage and Singular axis

This proof uses only `ADMITTED_INPUTS.json` and `EXECUTION_CONTRACT.json` at the
frozen hashes recorded in `result.json`. Let every (x_m\in\mathbb R^3) have
unit Euclidean norm and (w_m>0). The convention is
(W_{ij}=\epsilon_{ijk}\omega_k), (\epsilon_{123}=+1). Thus

\[
W=\begin{pmatrix}0&\omega_3&-\omega_2\\-\omega_3&0&\omega_1\\
\omega_2&-\omega_1&0\end{pmatrix},\qquad
Wx=-\omega\times x,\quad y=-Wx=\omega\times x.
\]

The vector triple-product identity gives
(x\times y=x\times(\omega\times x)=
(x\cdot x)\omega-(x\cdot\omega)x=(I-xx^T)\omega).
Summing after multiplication by (w_m) gives (b=G\omega).
The Sage and Singular unit-sphere ideal reductions separately return zero
for all three component residuals. The sign is fixed by the displayed matrix.

For the C02 stack (A_m=\sqrt{w_m}[x_m]_\times), where
([x]_\times v=x\times v), the exact polynomial identity
([x]_\times^T[x]_\times=(x\cdot x)I-xx^T) gives (A^TA=G).
For every (v\in\mathbb R^3),

\[
v^TGv=\sum_m w_m|v\times x_m|^2\geq0.
\]

Because all weights are strictly positive, this sum vanishes exactly when
(v\times x_m=0) for every (m), equivalently
(v\in\bigcap_m\operatorname{span}(x_m)). Two nonparallel directions have
trivial intersection, so (G\) is positive definite and invertible. The C01
normal equation then gives (\omega=G^{-1}b). For two directions (x,z)
with weights (a,b>0), the independently reduced polynomial identity is
(\det G=ab(a+b)|x\times z|^2>0) when (x,z) are not parallel.
If all directions are parallel, their common line is a kernel. At
(x_1=e_1,x_2=e_2,w_1=a,w_2=b), (G=\mathrm{diag}(b,a,a+b)).

For C03, a full-column-rank real matrix (A) has (A^\dagger A=I), and
the Euclidean singular-value theorem gives
(\|A^\dagger\|_{\rm op}=1/\sigma_{\min}(A)\leq1/\sigma_*).
For (\hat y=A\omega+e), therefore

\[
\hat\omega-\omega=A^\dagger e,
\qquad \|\hat\omega-\omega\|
\leq\epsilon_y/\sigma_*.
\]

For the independently stated perturbed operator (\hat A), with its own
full-column-rank premise and (\sigma_{\min}(\hat A)\geq\hat\sigma_*>0),

\[
\hat\omega-\omega
=\hat A^\dagger\{e+(A-\hat A)\omega\},\quad
\|\hat\omega-\omega\|
\leq\frac{\epsilon_y+\epsilon_A\Omega_*}{\hat\sigma_*}.
\]

The second line uses, in order, the left-inverse identity, triangle
inequality, induced operator-norm inequality, and the admitted amplitude
bound (\|\omega\|\leq\Omega_*). It does not hold uniformly after removing
that amplitude premise. For an exact counterfamily to that *uncontracted*
strengthening, use two unit directions (e_1,e_2), unit weights,
(A=( [e_1]_\times;[e_2]_\times )), (\hat A=2A), (e=0),
and (\omega=T e_1). Then (A^TA=\mathrm{diag}(1,1,2)),
(\epsilon_A=\sqrt2), (\hat\sigma_*=2), and
(\|\hat\omega-\omega\|=T/2\) for (T>0). In the admitted statement this
family requires (\Omega_*\geq T), and the displayed bound holds.
Zero data error, zero operator error, and (\Omega_*=0) follow by the same
identities without division by zero.

Finally, the six off-diagonal entries of (\delta W) are two signed copies
of each (\delta\omega_i); hence
(\|\delta W\|_F^2=2\|\delta\omega\|^2), and taking the nonnegative
square root gives the requested norm identity. Sage and Singular separately
reduce the polynomial square residual to zero.

The C01 source data (y_m=\omega\times x_m) are the negatives of the C02
stack blocks (A_m\omega=\sqrt{w_m}(x_m\times\omega)). To apply C03 to
these data one must use the corresponding sign-adjusted weighted stack.
C03 itself states an abstract (\hat y=A\omega+e) model; no observed
velocity-derivative channel follows here.
