# CAS-10-C04 Sage/Singular exact component

For `F(t)=1-10t^3+15t^4-6t^5`, exact differentiation gives
`F'(t)=-30t^2(1-t)^2`, `F''(t)=-60t(2t-1)(t-1)`, and
`F'''(t)=-60(6t^2-6t+1)`. Sage checks the endpoint jets directly. Singular
independently returns zero for each factorization remainder and for
`3(F'')^2-100` modulo `6t^2-6t+1`.

On the real compact interval `[0,1]`, the absolute maximum of either
derivative occurs at an endpoint, at a zero (value zero), or at a stationary
point. For `F'`, the only interior stationary point is `1/2`, where
`|F'|=15/8`; endpoint values are zero. For `F''`, the two interior stationary
points are `(3-sqrt(3))/6` and `(3+sqrt(3))/6`, both strictly in `(0,1)`.
Their exact values are `-10/sqrt(3)` and `10/sqrt(3)`; endpoint values are
zero. Sage checks the positive real square-root branch and these equalities
in its exact real algebraic field. Thus both stated equality loci are exact.

Exact rational arithmetic yields
`(25/24)(14/15+9/400)=1147/1152<1`. The stated exponential and square-root
auxiliary bounds are inputs only. This finite component makes no mollifier,
probability, or scientific claim.
