# CAS-06-C03-SCALAR: positive-real scalar calculus

Assume real `X>0`, fixed `Pstar>0`, and `0<alpha<1`. Define
`s=(1+alpha)/(2alpha)` and `P(X)=Pstar exp(s log X)` on the positive-real
branch. Sage differentiates this expression directly to obtain
`P'=Pstar s X^(s-1)` and `P''=Pstar s(s-1) X^(s-2)`; the run log records the
actual expressions and exact equality checks.

Algebraically, `E=2XP'-P=(2s-1)P`, and
`D=P'+2XP''=Pstar s(2s-1)X^(s-1)`.
Because `alpha>0`, `s=(1+alpha)/(2alpha)>0` and `2s-1=1/alpha>0`.
Together with `Pstar>0` and `X>0`, every factor of `D` is strictly positive.
Division by `D`, `s`, and `2alpha` is therefore justified and yields
`P'/D=1/(2s-1)=alpha`. Singular reduces the exact numerator polynomials
`alpha(2s-1)-1` and `s-alpha s(2s-1)` modulo
`2alpha s-alpha-1`; the recorded quotient checks additionally establish the
identities in the full rational polynomial ring before domain-restricted
division. The denominator sign is an analytic domain argument, not a CAS
inequality inference.

This verifies only the contracted scalar calculus. `E` is an algebraic
definition here; no stress tensor, scalar current, TOV equation, physical
sound speed, full C03, or scientific admission follows. The background metric
conventions in `COMMON_SPEC.md` are not used by this scalar subtarget.
