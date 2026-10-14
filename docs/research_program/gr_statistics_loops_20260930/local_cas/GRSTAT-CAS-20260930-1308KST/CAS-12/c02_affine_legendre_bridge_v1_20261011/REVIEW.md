# Independent review — affine shifted-Legendre bridge

Fresh read-only review, requested `gpt-6-astra/ultra`; observed runtime `UNKNOWN`.

No blocking finding.  The theorem is universal in `n`, defines the lift by
evaluation at `(x + 1) / 2`, and uses the actual interval integral from `-1`
to `1`.  Its change-of-variables call has endpoints `0` and `1` and the exact
Jacobian factor `2`.  The audit has the candidate as its prefix and reports only
`propext`, `Classical.choice`, and `Quot.sound`.

Nonblocking convention caveat: mathlib's `shiftedLegendre 1` is `1 - 2t`, so
this exact lift has degree-one value `-x`.  It is not the convention `P₁=x`
without a separate sign-normalization bridge.

Verdict: `PASS_SCOPED_REVIEW` for affine transport only; no weighted Thomson
moment, conventional normalization, sphere/Funk-Hecke bridge, CAS12-C02 closure,
or scientific admission follows.
