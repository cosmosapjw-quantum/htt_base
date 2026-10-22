# CAS-07 M02 SymPy axis: universal scalar argument

The frozen inputs assume real `L>0`, `0<=s<=L`, `c>0`, `M2>=0`, and a real
function `Z` on an open neighborhood of `[0,L]` with derivative witnesses
`Z1=Z'`, `Z2=Z1'`, continuous `Z2` on `[0,L]`, and `|Z2(t)|<=M2` there.
Write `Z0=Z(0)` and `H0=c Z1(0)`. These hypotheses make the products and
Riemann integrals below well defined. SymPy checks the product rule, both FTC
integrals, and the exact weight integral for an arbitrary symbolic function
`Z(t)`; see `check.py` and the raw run output.

For fixed admissible `s`, the product rule gives

`d[(s-t)Z1(t)]/dt = -Z1(t)+(s-t)Z2(t)`.

Integrate this equality from `0` to `s`. The first fundamental theorem of
calculus applied to `(s-t)Z1(t)` gives the boundary term
`[(s-t)Z1(t)]_0^s=-s Z1(0)`. The FTC applied to `Z1=Z'` gives
`integral_0^s Z1(t)dt=Z(s)-Z(0)`. Rearranging yields

`integral_0^s (s-t)Z2(t)dt = Z(s)-Z(0)-s Z1(0)
                             = Z(s)-Z0-H0*s/c`.

This derivation does not assume the remainder identity. At `s=0`, both
sides equal zero.

For every `t` in `[0,s]`, `s-t>=0` and `|Z2(t)|<=M2`. The absolute-integral
triangle inequality and order preservation of the integral therefore give,
for every admissible function and every admissible `s`,

`|Z(s)-Z0-H0*s/c|
 = |integral_0^s (s-t)Z2(t)dt|
 <= integral_0^s |(s-t)Z2(t)|dt
 = integral_0^s (s-t)|Z2(t)|dt
 <= integral_0^s M2(s-t)dt
 = M2*s^2/2`.

The last equality follows from the exact antiderivative `s*t-t^2/2`,
evaluated at `0` and `s`; SymPy independently returns `s**2/2` for the
weight integral. If `M2=0`, continuity and the pointwise bound force
`Z2=0` throughout `[0,s]`, so the remainder and bound are both zero.
Affine functions realize this case. A quadratic with constant `Z2=M2`
saturates the upper bound, but these examples are only checks of boundary
behavior. The proof above applies to every `Z` in the frozen domain.

This establishes only the contracted integral Taylor prerequisite. It does
not address the remaining analytic, physical, observational, or scientific
claims; scientific admission remains `HOLD`.
