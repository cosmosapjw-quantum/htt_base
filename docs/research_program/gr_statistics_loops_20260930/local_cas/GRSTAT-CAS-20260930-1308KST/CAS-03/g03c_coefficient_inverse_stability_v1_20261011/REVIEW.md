# G03-C coefficient inverse stability — independent review

- Verdict: `PASS_SCOPED`
- Requested reviewer runtime: `gpt-6-astra/ultra`
- Independently observed runtime: `UNKNOWN`
- Review mode: fresh, read-only; reviewer did not author or compile the candidate
- Final source SHA-256: `cefb2c07d5de5c46fe8ed949206b6e3830669c210db58c3b631a37114dc552ed`
- Final olean SHA-256: `72fdea7c35f16c15d0feabaebe62d1c59f9fa7cd1b64d12f4dbf8342c35aab39`
- Corrected parent compile receipt SHA-256: `e0be39e97d6fc5775a9fc69fa8cc66aabdc0982cae4a948ef00c7fa2fc548159`

## Findings

No open blocking findings.

One low-severity packaging finding was resolved during review. The parent receipt
originally named `raw/parent_compile.combined.log`; the actual receipt-relative
path is `lean/raw/parent_compile.combined.log`. The corrected receipt hash is the
one recorded above. The mathematical source and compiled output did not change.

## Mathematical review

- The generic perturbation theorem proves `mulVec` injectivity from the strict
  Euclidean induced-operator-norm gap, derives `det A != 0`, and only then uses
  inverse identities. Lean's total inverse is not used circularly.
- The noncommutative identity has the correct order:
  `A^-1 - D^-1 = A^-1 * (D-A) * D^-1`.
- The coefficient identity gives
  `A beta = -(1/2) • h1 + timeCoefficient • beta`, so the exact defect has the
  positive sign `beta - estimate = timeCoefficient • A^-1 beta`.
- The inverse-difference constant is
  `2*||D^-1||^2*||D|| / ((1-rho)*(1-r^2))`, multiplying `||beta||^2`.
  The velocity constant is
  `||D^-1||*||D|| / ((1-rho)*(1-r^2))`, multiplying `||beta||^3`, with the
  stated `r*||beta||^2` corollary. Both denominators are proved positive.
- The explicit radius proves `(1+2*kappa)*r^2 = 1/4`, `0 < r`, `r < 1`, and
  the strict perturbation gap. It does not claim invertibility for singular `D`.
- The `diag(1,1,-2)` specialization has `H=0`, determinant `-2`, symmetry, and
  the inverse neighborhood without any `H != 0`, positivity, or weak-shear premise.
- Norms remain the Euclidean vector norm and induced operator norm. No Frobenius
  or function-sup norm is substituted.

All seven printed target types match the frozen contract. Their axiom lists are
exactly `propext`, `Classical.choice`, and `Quot.sound`. The final source and its
five transitive project imports contain no `sorry`, `admit`, custom axiom, or
unsafe declaration. Preserved attempt snapshots and their recorded failures were
also checked against their hashes.

## Scope

This verdict covers ideal algebraic full-sky coefficients, coefficient-matrix
invertibility on the explicit conditioning neighborhood, inverse difference, and
the local velocity error bound, including the invertible `H=0` control.

It does not cover measured/noisy/masked coefficient binding, finite-distance or
catalogue guarantees, weak-shear promotion, historical four-axis promotion, or
scientific admission. Scientific admission and historical four-axis state remain
`HOLD`.
