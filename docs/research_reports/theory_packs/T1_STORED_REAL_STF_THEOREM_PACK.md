# T1 — Stored-real harmonic to Cartesian STF representation theorem

Date: 2026-09-03  
Evidence grade: `DERIVED` with independent exact Wolfram validation  
Implementation status: PR #440 source present; exact-head runtime unobserved  
Observational data used: none

## 1. Conventions

Use orthonormal Condon--Shortley harmonics and the reality condition

\[
a_{\ell,-m}=(-1)^m a_{\ell m}^*.
\]

The stored-real coefficients are

\[
c_{\ell0}=a_{\ell0},\qquad
c_{\ell m,c}=\sqrt2\,\Re a_{\ell m},\qquad
c_{\ell m,s}=-\sqrt2\,\Im a_{\ell m} \quad(m>0),
\]

with real basis functions

\[
Y^R_{\ell0}=Y_{\ell0},\qquad
Y^R_{\ell m,c}=\sqrt2\,\Re Y_{\ell m},\qquad
Y^R_{\ell m,s}=\sqrt2\,\Im Y_{\ell m}.
\]

For `a=x+iy` and `Y=u+iv`, the paired complex contribution is

\[
aY+(-1)^ma^*Y_{\ell,-m}=2\Re(aY)=2xu-2yv,
\]

which fixes the negative sine-slot convention. The real basis is orthonormal,
so

\[
\|c_\ell\|_2^2=\sum_m|a_{\ell m}|^2=(2\ell+1)C_\ell.
\]

Thus the stored carrier metric is Euclidean.

## 2. STF projection maps

For

\[
T_2(n)=Q_{ij}n^in^j,
\qquad
T_3(n)=O_{ijk}n^in^jn^k,
\]

sphere moments give

\[
\boxed{Q_{ij}=\frac{15}{8\pi}\int T_2(n)n_{\langle i}n_{j\rangle}d\Omega},
\]

\[
\boxed{O_{ijk}=\frac{35}{8\pi}\int T_3(n)n_{\langle i}n_jn_{k\rangle}d\Omega}.
\]

The coefficients follow from the fourth- and sixth-order isotropic sphere
moments. For the rank-three case, only the six pairings connecting source and
target indices survive contraction with an STF tensor.

## 3. Exact quadrupole basis

Let

\[
\alpha=\sqrt{\frac5{16\pi}},\qquad b=\sqrt{\frac{15}{16\pi}}.
\]

In stored order `(20,21c,21s,22c,22s)`, `Q=sum_A c_{2A}B_A^(2)` with

\[
B_{20}^{(2)}=\alpha\,\mathrm{diag}(-1,-1,2),
\]

\[
B_{21c}^{(2)}=\begin{pmatrix}0&0&-b\\0&0&0\\-b&0&0\end{pmatrix},
\quad
B_{21s}^{(2)}=\begin{pmatrix}0&0&0\\0&0&-b\\0&-b&0\end{pmatrix},
\]

\[
B_{22c}^{(2)}=b\,\mathrm{diag}(1,-1,0),
\quad
B_{22s}^{(2)}=\begin{pmatrix}0&b&0\\b&0&0\\0&0&0\end{pmatrix}.
\]

These reproduce the five real harmonic polynomials

\[
\alpha(3z^2-r^2),\ -2bxz,\ -2byz,\ b(x^2-y^2),\ 2bxy.
\]

They are symmetric, trace-free, and satisfy

\[
B_A^{(2)}:B_B^{(2)}=\frac{15}{8\pi}\delta_{AB}.
\]

## 4. Exact octupole basis

Let

\[
a_0=\sqrt{\frac7{16\pi}},\quad
 a_1=\sqrt{\frac{21}{32\pi}},\quad
 a_2=\sqrt{\frac{105}{16\pi}},\quad
 a_3=\sqrt{\frac{35}{32\pi}}.
\]

All unlisted components vanish and listed components are extended by full
index symmetry:

\[
\begin{array}{c|l}
30 & B_{zzz}=2a_0,\ B_{xxz}=B_{yyz}=-a_0\\
31c & B_{xxx}=a_1,\ B_{xyy}=a_1/3,\ B_{xzz}=-4a_1/3\\
31s & B_{yyy}=a_1,\ B_{xxy}=a_1/3,\ B_{yzz}=-4a_1/3\\
32c & B_{xxz}=a_2/3,\ B_{yyz}=-a_2/3\\
32s & B_{xyz}=a_2/3\\
33c & B_{xxx}=-a_3,\ B_{xyy}=a_3\\
33s & B_{xxy}=-a_3,\ B_{yyy}=a_3.
\end{array}
\]

The corresponding polynomials are

\[
\begin{array}{ll}
a_0(5z^3-3zr^2),&-a_1x(5z^2-r^2),\\
-a_1y(5z^2-r^2),&a_2z(x^2-y^2),\\
2a_2xyz,&-a_3(x^3-3xy^2),\\
&-a_3(3x^2y-y^3).
\end{array}
\]

Every tensor is fully symmetric and trace-free, with

\[
B_A^{(3)}:B_B^{(3)}=\frac{35}{8\pi}\delta_{AB}.
\]

## 5. Bijectivity, inverse maps, and norms

The flattened basis families have ranks five and seven. The inverse maps are

\[
\boxed{c_{2A}=\frac{8\pi}{15}B_A^{(2)}:Q},
\qquad
\boxed{c_{3A}=\frac{8\pi}{35}B_A^{(3)}:O}.
\]

Consequently,

\[
\boxed{Q:Q=\frac{15}{8\pi}\|c_2\|_2^2=\frac{75}{8\pi}C_2},
\]

\[
\boxed{O:O=\frac{35}{8\pi}\|c_3\|_2^2=\frac{245}{8\pi}C_3}.
\]

The correspondence is regular at zero amplitude. Zero is singular only for a
later normalized orbit chart.

## 6. Rotation and parity

For the active sky action `(R.T)(n)=T(R^{-1}n)`, uniqueness of the two
expansions gives

\[
Q\mapsto RQR^T,
\qquad
O_{abc}\mapsto R_a{}^dR_b{}^eR_c{}^fO_{def}.
\]

Hence the harmonic/STF maps intertwine the real Wigner representation and the
Cartesian tensor representation. Spatial inversion leaves the quadrupole even
and flips the octupole.

## 7. Dimensional and implementation checks

`a_lm`, `c_lA`, `Q`, and `O` have temperature units; `C_l` has temperature
squared; basis tensors and Gram constants are dimensionless.

PR #440 constructs the same maps from independent sphere quadrature with
factors `15/(8 pi)` and `35/(8 pi)`, removes numerical traces, and verifies the
radial identities row by row. That is source consistency, not accepted
exact-head runtime evidence.

## 8. Independent exact validation

Fresh Wolfram construction returned:

```yaml
Q_symmetric: true
Q_traces: all_zero
O_trace_vectors: all_zero
Q_polynomial_residuals: all_zero
O_polynomial_residuals: all_zero
Q_Gram_residual: zero_5_by_5
O_Gram_residual: zero_7_by_7
Q_map_rank: 5
O_map_rank: 7
```

The receipt is `T1_WOLFRAM_EXACT_RECEIPT.json`.

## 9. Terminal

```text
PASS_STORED_REAL_STF_REPRESENTATION_THEORY
```

This closes the representation theorem. It does not certify the PR #440
runtime, Q/O orbit reconstruction, a statistical result, or physical-source
attribution.
