# SymPy depth-obligation attempt

Command runner: `depth_sympy_runner.py D1|D3|D2|D4` using the contract-pinned
`/usr/bin/python3` and SymPy 1.14.0.  Each invocation emits one JSON document
whose `checks` keys are exactly those of the selected contract.

The executable performs these exact but deliberately limited calculations:

- D1 expands the one-step symbolic block product `H C H^T` for symbolic
  compatible dimensions.
- D3 multiplies a two-step symbolic block-triangular transform by its proposed
  inverse.
- D2 reduces a two-coordinate diagonal whitening quadratic to `u^2 + v^2`.
- D4 reduces `B - B A^-1 A` to zero in the nonsingular past-covariance case.

None discharges an all-finite-depth or all-dimension proposition.  In
particular, SymPy does not provide a quantified proof of the arbitrary-depth
recursions, matrix determinant/kernel/surjectivity, PSD range/pseudoinverse
facts, Gaussian pushforward/support, chi-square law, singular conditional
Gaussian law, or innovation independence.  No finite calculation has been
promoted to a general or probabilistic PASS.  Therefore every contract check
is emitted as `false` to mean **UNVERIFIED BY THIS AXIS**.  It is not a
counterexample; `counterexample` remains null.

The generic gate maps a false check to `FAIL` during runner adjudication.  That
label reflects the gate's binary payload vocabulary, while this artifact's
per-obligation limitation is absence of an all-domain SymPy proof rather than
disproof of the theorem.

Execution records are retained as `D*.stdout`, `D*.stderr`, and `D*.exit`.
The first D1/D3 attempts are separately retained with the `.attempt1` suffix.
The pre-structural-repair runner and result envelope are preserved with the
`.pre_d3repair` suffix, and its D3 raw logs are retained with the `.attempt2`
suffix.  The residual D3 `AssertionError` was not a counterexample: SymPy
reported the individual 3 by 3 block arrays identical while its whole
`MatrixExpr` equality rejected a `BlockMatrix` versus `BlockDiagMatrix`
representation.  The repair compares those compatible block arrays directly.
D3 now runs and emits its typed unverified payload.  This confirms the
two-step structural identity calculation only; it does not establish D3's
arbitrary-depth, determinant, kernel/surjectivity, or full-law/support
obligations.  Therefore the axis result remains `inconclusive`.
