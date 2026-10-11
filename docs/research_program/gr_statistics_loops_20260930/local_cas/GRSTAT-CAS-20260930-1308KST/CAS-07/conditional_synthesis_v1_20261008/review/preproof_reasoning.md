# Independent reasoning before synthesis proof inspection

Statements and exact premise structures inspected first. No RETURN.md or RESULT.md read.

1. The Euclidean operator norm controls composition with constant one and gives the Volterra inequality u(s) <= s + K integral_0^s(s-t)u(t)dt. Nonnegative-kernel iteration yields f_K(s); the deviation bound is f_K(s)-s. No symmetry or commutation is needed.
2. For s>0, f_K(s)-s=s eta_K(s). eta is nonnegative and nondecreasing. eta_K(L)<1 implies every normalized D(s)/s lies in the open operator-norm unit ball about Id. The straight path from Id is invertible throughout, so determinant has positive sign. The singular values lie in [s(1-eta),s(1+eta)], hence the determinant and its positive square root have the stated bounds. This requires the Euclidean norm preserved by matrixOf, not a default matrix norm.
3. M02 C2 witnesses on all of [0,L], including endpoint HasDerivAt, imply the scalar integral remainder; c>0 and H0=c Z1(0) identify the physical slope. Full HasDerivAt at endpoints is stronger than within-interval differentiability and must remain explicit.
4. |s-dA|<=s eta and the scalar remainder give FD1 by triangle inequality. dA>=s(1-etaL)>0 gives FD2. Multiplying FD1 by c/dA and using the local lower bound gives FD3. Absolute H0 handles either sign. Z0 must stay in every formula.
5. Let q=dA/(1-etaL), t=min(L,q). Since s<=L and s<=q, s<=t<=L. Both t and eta(t) increase the nonnegative FD1 terms, hence FD1(s)<=FD1(t). Since t<=q and eta(t)<=etaL, FD1(t)<=FD2(dA,etaL). No selection of just one min branch is needed.
6. K=0 implies R=0, D=s Id, eta=0 for s>0, dA=s, and t=s. H0=0 removes geometry coupling; M2=0 removes Taylor error; both zero give zero scalar error. No division by these constants occurs. etaL approaching 1 from below can make FD2 large but is still valid; equality 1 is excluded.
7. At s=0 the eta definition in Lean uses totalized division and equals -1, rather than its analytic limiting value 0. The main theorem explicitly excludes s=0. The separate closed-interval theorem avoids eta and distance division, so this is not a counterexample. No positive distance is claimed at zero.

No analytical counterexample found under the declared premises. Proof, finite-dimensional conversion, imported build provenance and axioms still require inspection.
