# Independent review — all-degree scalar Thomson moment

Fresh read-only review requested `gpt-6-astra/ultra`; observed runtime `UNKNOWN`.
Verdict: `PASS_SCOPED_REVIEW`.

The candidate quantifies over every natural degree and proves the actual
`[-1,1]` interval integral with factor `3/8`.  Degrees `0`, `1`, and `2` are
direct actual monomial integrals (`8/3`, `0`, `4/15`).  For every degree at
least `3`, it transports both endpoints and factor `2` to `[0,1]`, keeps the
explicit sign, and applies the lower-degree Rodrigues result to
`1+(2t-1)^2`, whose degree is at most two.  No desired moment is assumed.

Source bindings, exact candidate audit prefix, and recorded hashes match.  The
audit reports only `propext`, `Classical.choice`, and `Quot.sound`.

This accepts only the scalar all-natural interval moment for the explicitly
defined `standardLift`.  It does not establish a separate conventional-polynomial
identification, sphere/Funk-Hecke transport, spin/collision results, complete
CAS12-C02, historical four-axis acceptance, or scientific admission.
