# Appendix E. Covariant observer, photon, boost, and numerical-domain conventions

This appendix is part of the Report-A source authority. It makes explicit the domain assumptions already used by the local-observer and numerical-error theorems; it introduces no new observational result.

We use metric signature

\[
g_{ab}=(-,+,+,+).
\]

The observer field is future-directed and unit timelike,

\[
u^a u_a=-1.
\]

A photon momentum is future-directed and null,

\[
p^a p_a=0,
\]

and its energy measured by \(u^a\) is

\[
E_\gamma=-c\,p_a u^a>0.
\]

The spatial propagation direction \(e^a\) is defined by

\[
p^a=\frac{E_\gamma}{c}(u^a+e^a),
\qquad
u_a e^a=0,
\qquad
e_a e^a=1.
\]

These relations imply both \(p^a p_a=0\) and \(E_\gamma=-c p_a u^a\). The outward sky direction used throughout the report is

\[
n^a=-e^a.
\]

A local observer boost is represented by a spatial dimensionless vector

\[
\beta_{\rm obs}^a=\frac{v_{\rm obs}^a}{c},
\qquad
u_a\beta_{\rm obs}^a=0,
\qquad
0\leq\beta_{\rm obs}^2<1.
\]

The boosted observer is

\[
\widetilde u^a=\gamma(u^a+\beta_{\rm obs}^a),
\qquad
\gamma=(1-\beta_{\rm obs}^2)^{-1/2},
\]

and therefore

\[
\widetilde u^a\widetilde u_a=-1.
\]

This is a local-observer Lorentz transformation. It is not identified with a global matter-frame tilt or with any Bianchi-family parameter.

The report keeps two finite-sample constructions separate. For an observation-plus-reference pool, joint exchangeability of the rows, complete row-permutation equivariance of the full adaptive analysis, and a fixed tie/tail rule imply a conservative observation-inclusive rank. A finite randomisation test is instead defined relative to a declared null-invariant transformation group and ranks the statistic over the actual group orbit, or over a valid identity-including conditional-Monte-Carlo sample of that orbit. Proper-subgroup invariance does not make arbitrary rows outside the subgroup orbit exchangeable.

For the numerical-error theorem, every registered error family is nonempty, each family radius satisfies

\[
r_f>0,
\]

and

\[
\lambda_{\rm reg}>0
\]

is fixed before inspecting any rank or holdout result. Hence

\[
\Gamma_E=N_{\rm fam}\sum_f r_f^2\sum_i E_{fi}E_{fi}^{T}+\lambda_{\rm reg}^2 I
\]

is positive definite and \(\Gamma_E^{-1/2}\) is well defined. The resulting robust-rank statement remains conditional on the actual numerical error belonging to the frozen declared family-ball class.

These conventions add no observation-bearing result. The corrected tensorised Planck rank remains absent, finite-HEALPix containment remains rank-unresolved, and native BASS solver claims remain outside the report.

## Source and review boundary

The covariant observer/photon decomposition is standard in the 1+3 formalism; the report retains its own sign, energy, and sky-direction conventions explicitly. The exchangeable-row and group-orbit statements are separate finite-sample constructions. The paragraph sequence and conservative British English spelling in this appendix were independently checked by the Academic Writing Toolkit with no reported issue. Fresh Wolfram evaluation was attempted during R4A1N and returned an upstream HTTP 502, so it is not counted as a verification pass.
