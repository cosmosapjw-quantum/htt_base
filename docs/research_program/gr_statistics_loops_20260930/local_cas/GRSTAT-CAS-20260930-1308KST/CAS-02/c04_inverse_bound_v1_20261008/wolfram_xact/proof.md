# CAS-02-C04: finite inverse bound, Wolfram/xTensor axis

Let all entries be real in the one fixed orthonormal observer frame, and use
positive Euclidean vector, Frobenius matrix, and induced spectral norms.  Write
`D=S2-S1`, `v=u2-u1`, `qj=uj^T Sj uj`, and `g=diag(-1,1,1,1)`.  The admitted
inverse definition gives the exact identity

`B2-B1 = D + (q2-q1) g`.

The rapidity condition is satisfiable only if `sinh(R)>=0`, hence `R>=0`.
For either `j`, the positive-root chart gives

`||uj||_2^2 = (sqrt(1+||dj||_2^2))^2+||dj||_2^2
             = 1+2||dj||_2^2
            <= 1+2 sinh(R)^2 = cosh(2R) = M^2`.

This includes `dj=0` and `R=0`, where both `dj` vanish and `M=1`.

There are exactly two amplitude cases.  If `||S1||op<=||S2||op`, then `L=||S1||op`
and the first identity below uses the smaller anchor.  Otherwise `L=||S2||op`
and the second identity uses it.  Equality belongs to the first case.

`q2-q1 = u2^T D u2 + v^T S1 u2 + u1^T S1 v`

`q2-q1 = u1^T D u1 + v^T S2 u2 + u1^T S2 v`.

For real vectors and matrices, `|x^T A y| <= ||x||_2 ||A||op ||y||_2`
by Euclidean Cauchy–Schwarz and the definition of the induced norm;
`||D||op<=||D||F` follows from Cauchy–Schwarz on each row (equivalently,
the sum-of-squares formula).  Thus each selected identity yields

`|q2-q1| <= M^2 epsilonH + 2 M L epsilonZ`.

The Frobenius triangle inequality and `||g||F=sqrt(4)=2` yield

`||B2-B1||F <= epsilonH + 2|q2-q1|
             <= (1+2M^2)epsilonH + 4ML epsilonZ`.

When `epsilonH=0`, the selected anchor leaves only the velocity terms;
when `epsilonZ=0`, they vanish.  Both cases preserve the stated bound.  The
statement is finite-dimensional and exact.  It does not establish projection
nonexpansiveness, a global mean-value/Lipschitz extension, statistical
calibration, or physical application.  Scientific admission remains HOLD.

`run.wl` checks the generic polynomial identities with independent symbolic
entries, chart/hyperbolic identities and boundary controls, the Frobenius
metric factor, and the exhaustive real amplitude order.  These executable
checks supplement the displayed universal norm argument; no sampled vectors
are used as a universal proof.
