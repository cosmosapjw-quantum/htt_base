# CAS-07 M03: scalar Volterra comparison

This proof uses precisely the admitted premises. Let
\(g(x)=x\) and \((Tv)(x)=K\int_0^x(x-t)v(t)\,dt\) on \([0,L]\), where
\(K\geq0\), \(L>0\), and \(u\) is continuous, nonnegative, and satisfies
\(u\leq g+Tu\) pointwise. The kernel is nonnegative, so \(T\) preserves
pointwise order on continuous functions. No derivative of \(u\) is used.

For every integer \(n\geq1\), Fubini's theorem for continuous integrands
and the beta integral give the exact iterate

\[
 (T^n v)(x)=\frac{K^n}{(2n-1)!}
       \int_0^x(x-t)^{2n-1}v(t)\,dt.                 \tag{1}
\]

The base case is the definition of \(T\). If (1) holds at \(n\), then
interchanging integration over \(0\leq t\leq s\leq x\) leaves the inner
coefficient
\[
 \frac1{(2n-1)!}\int_t^x(x-s)(s-t)^{2n-1}ds
 =\frac{(x-t)^{2n+1}}{(2n+1)!}.
\]
Thus (1) holds at \(n+1\), including \(K=0\) without dividing by \(K\).
Applying (1) to \(g(t)=t\), and taking \(T^0g=g\), yields
\[
 (T^j g)(x)=\frac{K^j x^{2j+1}}{(2j+1)!}
       \quad(j\geq0).                              \tag{2}
\]

Order preservation and the given inequality imply, by functional
induction, for every integer \(n\geq1\),
\[
 u(x)\leq\sum_{j=0}^{n-1}(T^jg)(x)+(T^nu)(x).       \tag{3}
\]
Indeed the case \(n=1\) is the premise. Applying \(T^n\) to
\(u\leq g+Tu\) replaces the remainder \(T^nu\) in (3) by
\(T^ng+T^{n+1}u\). This step is valid for the given arbitrary continuous
\(u\), with no restriction to polynomial or differentiable functions.

Compactness gives a finite \(M=\max_{[0,L]}u\geq0\). By (1), for all
\(x\in[0,L]\) and \(n\geq1\),
\[
 0\leq(T^nu)(x)\leq
 M\frac{K^n x^{2n}}{(2n)!}
 \leq M\frac{(K L^2)^n}{(2n)!}.                     \tag{4}
\]
If \(K>0\), consecutive right-hand factors have ratio
\(K L^2/((2n+2)(2n+1))\to0\), so (4) tends to zero uniformly.
The same ratio argument proves absolute, uniform convergence of the
nonnegative series in (2) on \([0,L]\): successive series terms at
\(L\) have ratio \(K L^2/((2j+3)(2j+2))\to0\). Taking \(n\to\infty\) in (3)
therefore gives
\[
 u(x)\leq\sum_{j=0}^{\infty}
 \frac{K^j x^{2j+1}}{(2j+1)!}
 =\frac{\sinh(\sqrt K\,x)}{\sqrt K}\quad(K>0).
\]
The equality is the entire power series for \(\sinh\), with the positive
square root. If \(K=0\), \(T=0\) and the original premise directly gives
\(u(x)\leq x=f_0(x)\). At \(x=0\), nonnegativity and the premise give
\(u(0)=0=f_K(0)\). The zero function and the equality solution
\(u=f_K\) obey the same boundary treatment. Uniform convergence permits
termwise application of \(T\) to the series, yielding \(f_K=x+Tf_K\);
this supplies the exact equality control.

The Wolfram execution verifies the beta coefficient, (2), the kernel
mass in (4), the ratio limit, the exact entire series, the separate
zero-\(K\) branch, and the vertex. xTensor defines a one-dimensional
positive-signature metric and checks the symmetry of its genuine
\(h_{ab}v^a w^b\) contraction, including a weighted norm with correctly
contracted dummy indices. In an orthonormal frame on this positive
one-dimensional metric, \(h_{ab}v^av^b=(v^1)^2\geq0\). The Volterra weight \(K(x-t)\) is
nonnegative on the integration domain, as separately verified by
real quantifier elimination. Thus a positive one-dimensional norm
contraction is compatible with the scalar majorant; the xTensor check
does not purport to prove functional induction or positivity of an
indefinite spacetime norm.

This proves only the scalar comparison under the admitted inequality.
The matrix Jacobi-to-scalar step and the full physical theorem remain
outside this contract; scientific admission remains HOLD.
