# G13-E fixed-prior actual-measure bridge — independent review

- Verdict: `PASS_SCOPED`
- Requested reviewer runtime: `gpt-6-astra/ultra`
- Independently observed runtime: `UNKNOWN`
- Review mode: fresh, read-only; reviewer did not author or compile the candidate
- Final source SHA-256: `e40510a41998f4bac99799976318bcf158bceeb41d85d39105db86249e7fd692`
- Contract SHA-256: `d015a07aee15cba13aa9c36b166c579c86e4443c7235826c0454911a9598ec8a`
- Final author/controller olean SHA-256: `d40a011fdcb3c7ce0cbb8cbcda35a840760dcc9e97aeb8654d9171e14d67cd5d`

## Findings

No blocking correctness or scope findings.

One P3 evidence limitation is retained: `lean/raw/parent_compile.combined.log`
is a controller summary referring to the complete author stdout rather than a
separate raw parent compiler transcript. The reviewer verified the parent receipt,
the matching fresh temporary olean, and the author raw compiler/type/axiom stream.
The summary is not described as an independently inspected parent raw transcript.

## Mathematical review

- All six `StrictInterior` conditions are proved. The real-rpower inequality is
  reduced using positive rational data and the exact comparison `M3^4 < M4^3`.
- The rational witness cubic is converted to the lower-node secant equation only
  after proving the relevant denominators nonzero. `lower_node_existsUnique`
  identifies it with the node used by G13-A.
- One actual `twoDirac` probability measure is proved admissible for both `p=5`
  and `p=6`; the fibre exclusion is not vacuous.
- The actual atomic moments are identified with the two rational responses, then
  composed as `frame < response = lower bound <= moment mu` for every actual
  corresponding admissible measure with identical fixed data.
- Separate and joint no-attainment results follow from the strict inequalities,
  not from the changed amplitude alone.
- The exact matched temperature ratio, amplitude, powers, positivity, interior
  bounds, logarithm identity, and negative log shift are correct.

The imported definitions use `Measure ℝ`, probability mass, almost-everywhere
support on the fixed interval, Bochner integrability, and exact retained moments.
All final and import hashes match the frozen inputs. All nine target types match
the contract, and every axiom audit lists only `propext`, `Classical.choice`, and
`Quot.sound`. No `sorry`, `admit`, custom axiom, or unsafe declaration occurs in
the final source or the two exact imported source bodies. Failed attempts and their
source snapshots remain preserved.

## Scope

This verdict covers the bounded fixed-support, fixed-`M3`/`M4` actual-measure
fibre exclusion for exponents 5 and 6 and the exact matched-parameter algebra.

It excludes entropy optimality, occupation-function equality, FD/BE inversion,
measured rates or CMB kernels, general real exponents, boundary cases, CAS13-C04,
historical four-axis promotion, and scientific admission. Scientific admission
remains `HOLD`.
