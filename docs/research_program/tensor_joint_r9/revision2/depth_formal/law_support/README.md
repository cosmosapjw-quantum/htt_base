# D3 law/support/moment bridge

This is a Host-authored, source-bound Lean assembly of the already proved
heterogeneous transform. It imports `formal/R9Depth/BlockBridge.lean` and
`formal/R9Depth/Covariance.lean`; it does not re-prove determinant, recursion,
kernel, or covariance algebra.

The module proves the exact measurable-equivalence round trips for an arbitrary
measure and pointwise parameter family, generic topological support transport
under a homeomorphism, affine covariance-range transport for singular and zero
matrices, and the existing D1 mean/covariance specialization for the full
retained transform. Initial coordinates and all cross-covariance entries remain
in the transformed vector/matrix.

The Gaussian characterization `supp N(μ,C) = μ + Im C`, pseudoinverse
chi-square law, and D4 conditional innovation remain separate obligations.
This artifact therefore does not promote `FORMAL_DEPTH` or four-axis CAS
admission.

Reproduction is `python3 compile.py --output attemptNN`; the checked run is in
`attempt01/execution.json`.
