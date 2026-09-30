# SymPy axis: complete finite-dimensional reduction

Owner: `GRSTAT-CAS11-C02-20260930T090559Z-sympy`.
Contract: `CAS11-C02-FINITE-GRAM.json`, version 3, SHA-256
`c66d7d00bf60786417336873dfeb97f5602d0e60a110c110ebacd9dff824b47a`.
Scope: the finite mathematical component only; no scientific admission.

## Statement alignment

Let `n` be any positive integer, `R` any real symmetric positive-semidefinite
`n` by `n` matrix, `e` any real `n`-vector, and `epsilon >= 0`. Assume

    (a^T e)^2 <= 2 epsilon (a^T R a), for every real n-vector a.       (H)

Real absolute value squared equals the square used here. We prove that `e` is
in `range(R)` and that `e^T Rdagger e <= 2 epsilon`. `Rdagger` has precisely the
contract's spectral definition. Positive semidefiniteness is an input assumption,
not a conclusion inferred from (H) and not a physical-provenance assertion.
All inner products in this component are Euclidean; no Lorentz contraction is
used. `2 epsilon` retains the contract's normalization.

## Dependencies and their status

1. **Finite real spectral theorem (standard mathematical dependency).** Every
   real symmetric finite matrix admits `R = U D U^T` with `U^T U = U U^T = I`
   and `D` real diagonal. Its eigenvalues are nonnegative if `R` is PSD: for a
   unit eigenvector `u`, `lambda = u^T R u >= 0`. The theorem applies to every
   finite `n`, including repeated eigenvalues and zero eigenvalues. We use this
   standard theorem analytically; SymPy does not kernel-prove it here.
2. **Finite matrix multiplication and finite-sum rules (definitions and standard
   algebra).** A diagonal matrix acts coordinatewise, and equal summands yield
   equal finite sums. The latter follows by induction on the number of terms:
   empty sums agree; adding equal next terms preserves equality. A finite sum
   of nonnegative terms is nonnegative by the same induction. Empty rank-zero
   sums are zero. These statements impose no upper bound on `n` or the rank.
3. **Real ordered-field facts and logic (standard dependencies).** Squares are
   nonnegative; a nonpositive real square is zero; positive factors have a
   positive product; and `S > c` implies `S = c + delta` for `delta = S-c > 0`.
   A universal statement can be instantiated with any real vector, including
   one constructed from its input data. SymPy additionally solves the square
   inequality and checks the positivity expressions used below.
4. **Moore-Penrose inverse (contract definition).** The diagonal value is
   `1/lambda` for `lambda > 0` and zero for `lambda = 0`; transform back by `U`.
   No target-equivalent range/bound lemma or inverse-of-singular-matrix rule
   is imported.

The engine-executed portion consists of arbitrary-coordinate rational
identities, the scalar inequality certificate, and matrix-expression identities
with symbolic positive-integer dimension `n`. Their use with the standard
dependencies above is a complete analytic proof of the contracted statement.
It is **not a full theorem-kernel certification**. Finite examples and numerical
checks are supplementary falsifiers, never the universal argument.

## Proof for arbitrary dimension and arbitrary rank

Choose the spectral decomposition from dependency 1. Write `f = U^T e`, so
`e = U f`. Set `a = U b` in (H), where `b` is any real `n`-vector. Orthogonality
and matrix multiplication give

    (b^T f)^2 <= 2 epsilon sum_i lambda_i b_i^2, for every b.        (1)

`arbitrary_n_dot_transform`, `arbitrary_n_quadratic_transform`, and
`orthogonal_coordinate_reconstruction` execute those identities with symbolic
dimension. Orthogonality is justified by the spectral theorem, not by the target.

**Nullspace coordinates.** For each index `i` with `lambda_i = 0`, instantiate
(1) with the `i`th unit coordinate vector. This gives `f_i^2 <= 0`, hence
`f_i = 0`. `kernel_square_nonpositive_iff_zero` computes the complete real
solution set `{0}`. The index is arbitrary: applying this argument separately
to every zero eigenvalue proves vanishing on the entire nullspace. No assertion
about range membership has been assumed.

Define vectors and diagonal entries coordinatewise:

    mu_i = 1/lambda_i and z_i = f_i/lambda_i  if lambda_i > 0;
    mu_i = 0          and z_i = 0           if lambda_i = 0.

These branches exhaust the nonnegative eigenvalues. Division occurs only on a
strictly positive eigenvalue branch. Put `M = diag(mu_i)` and `Rdagger = U M U^T`.
This is the spectral pseudoinverse in the contract. The executed coordinate
identities `lambda mu lambda = lambda` and `mu lambda mu = mu`, together with
diagonality and the orthogonal transform, also verify its Moore-Penrose equations.
Real diagonal matrices are symmetric and their products commute, so the other
two Moore-Penrose requirements are symmetry of `R Rdagger` and `Rdagger R`.

For every coordinate, `lambda_i z_i = f_i`. For a positive eigenvalue this is
`positive_coordinate_range`; for a zero eigenvalue both sides vanish by the
nullspace argument above, as checked in `zero_coordinate_range`. Consequently
`D z = f` and

    R (U z) = U D U^T U z = U D z = U f = e.                       (2)

Thus `U z` is an explicit preimage of `e`, proving `e in range(R)` for every
rank, including rank zero. `arbitrary_n_range_transform` executes the matrix
identity preceding substitution of the proved coordinate equation `D z = f`.

Define the finite sum

    S = sum_{i: lambda_i > 0} f_i^2/lambda_i.

Each summand is nonnegative and thus `S >= 0`. Empty sums are zero. The executed
`positive_coordinate_dot` and `positive_coordinate_quadratic` identities, with
their zero-coordinate counterparts, give the pointwise equalities

    z_i f_i = lambda_i z_i^2 = mu_i f_i^2.

Finite-sum lifting (dependency 2) therefore proves, for unrestricted `n` and rank,

    z^T f = z^T D z = f^T M f = S.                                (3)

The last term is also `e^T Rdagger e`, by orthogonality; that matrix reduction
is executed as `arbitrary_n_pseudoinverse_energy`. Now instantiate (1) with
`b = z`. It is a legitimate finite real vector, constructed after (H), with
no division by a zero eigenvalue. By (3),

    S^2 <= 2 epsilon S.                                           (4)

Set `c = 2 epsilon >= 0`. Suppose for contradiction that `S > c`, and put
`delta = S-c > 0`. The scalar residual in (4) is

    S^2 - c S = (c+delta)^2 - c(c+delta) = delta(c+delta) > 0.

SymPy verifies the polynomial equality and that its final expression is strictly
positive for `c >= 0`, `delta > 0`. This contradicts (4), so `S <= c`, proving
the desired bound. This argument does not divide by `S` or `epsilon`; it directly
covers equality, zero error, zero rank, and `epsilon = 0`.

## Branch coverage

| Matrix branch | `epsilon = 0` | `epsilon > 0` |
|---|---|---|
| Positive definite, rank `n` | No zero coordinates; (4) forces `S = 0`, hence `e = 0` | Equations (2)-(4) and the scalar bound apply |
| Singular nonzero, `0 < rank < n` | Null coordinates vanish, `S = 0` forces the remaining coordinates to vanish | Null coordinates vanish; positive coordinates obey the same finite sum proof |
| Zero matrix, rank `0` | Every coordinate vanishes; `e = 0`, `S = 0` | Every coordinate vanishes; `e = 0`, `S = 0 <= 2 epsilon` |

In the first two zero-epsilon cells, `S = 0` is a finite sum of nonnegative
terms, so every term is zero; positive denominators then imply every remaining
`f_i = 0`. This is a consequence, not an extra assumption. Dimension `n = 1`,
repeated eigenvalues, and arbitrary nullspace multiplicity require no separate
regularity assumption. The statement excludes `n = 0`, as required.

Every PSD matrix also has a finite Gram representation, for example columns of
`D^(1/2) U^T`, because their Gram matrix is `U D U^T`. Positive square-root
squaring is executed; the zero square root is zero. This observation does not
claim that physical residuals or a weighted inner product have been supplied.

## Verification and limits

`run_axis.py` executes the symbolic certificates and supplementary exact/numeric
checks. Its source and this proof note are sealed before the recorded invocation.
Each certificate emits its computed result to raw stderr. An exception or false
certificate exits nonzero without a success JSON payload. Successful stdout is
exactly one JSON object with the contracted obligation key.

Negative controls exhibit explicit violations of (H) for nullspace error,
range error above the bound, nonzero error with zero `R`, and nonzero error
with zero `epsilon`. Exact fixtures cover all six matrix/epsilon intersections.
A rotated singular four-dimensional fixture has positive eigenvalues
`10^-80, 1, 10^40`, allowing a 220-decimal-digit check of cancellation-sensitive
identities. Its `10^-70` numerical threshold is a supplementary regression
criterion; all mathematical identities and theorem decisions are exact.

No mathematical gap remains in the stated analytic reduction with the standard
dependencies listed above. Those dependencies and the logical lifting have not
been formalized in a proof kernel by this axis. No sibling sources/results, old
proofs/results, or Host derivations were read. This completion preserves historical
evidence and task identity, and does not reset costs or establish observed model
identity. The finite result does not certify C01, C03, a continuum estimate,
physical derivative bounds, noise covariance, inference, novelty, or scientific
admission. Host adjudication and independent review remain separate stages.
