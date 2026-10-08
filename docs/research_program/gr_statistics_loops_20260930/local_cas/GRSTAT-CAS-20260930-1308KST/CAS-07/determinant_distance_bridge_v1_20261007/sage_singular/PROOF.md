# CAS-07 M05 Sage+Singular proof

## Scope and authority

This is the owner-authorized direct local fallback for the Sage+Singular axis.
The dedicated `cas_sage_singular` role refused before scientific execution
because its hidden registration requirement could not be met and the global
descriptor was absent.  Per the owner's instruction, `전역 하네스 없이 진행해줘`,
this execution does not restore, register, or emulate the global harness.
`launch_id` is null, `authority_status` is `UNAVAILABLE`, and the observed
model and effort are `UNKNOWN`.

The proof uses only the frozen execution contract, admitted inputs,
`COMMON_SPEC.md`, and the literal accepted M01, M04, and C02 statements.  It
does not inspect sibling-axis files, dependency proof sources, dependency
results, or historical answer scripts.

## Assumptions and conventions

- `K>=0`, `L>0`, and `0<s<=L`.
- `eta_K(L)<1`.
- The exact admitted M04 Jacobi premises hold.
- `E=R^2` has the standard Euclidean norm; the matrix norm is its induced
  operator norm.
- `D(s)` is an arbitrary real `2 x 2` linear map.  No symmetry, normality,
  definiteness, diagonalizability, or commutation assumption is introduced.
- `dA(s)` denotes the positive square root of `det(D(s))` only after C02 has
  yielded `det(D(s))>0`.

## Exact rewrite

On `s>0`, the admitted definition is

`eta_K(s) = f_K(s)/s - 1`.

Multiplying by positive, nonzero `s` gives

`s eta_K(s) = f_K(s) - s`.

Sage verifies this in the exact rational polynomial quotient by
`s*eta-(f-s)` and directly on the symbolic `K>0` hyperbolic branch.  Singular
independently reduces `(f-s)-s*eta` to zero modulo the same cross-multiplied
definition.  No finite sampling or series approximation is used.

## C02 premises

The accepted M01 statement gives

`0 <= eta_K(s) <= eta_K(L) < 1`.

Hence `0<=eta_K(s)`.  Moreover,

`1-eta_K(s) = (1-eta_K(L)) + (eta_K(L)-eta_K(s)) > 0`,

because its first summand is positive and its second is nonnegative.  Therefore
`eta_K(s)<1`.  Sage and Singular both verify the displayed gap identity exactly.

The accepted M04 statement and the exact rewrite give

`||D(s)-s Id||op <= f_K(s)-s = s eta_K(s)`.

Thus every hypothesis of the accepted arbitrary-real-`2 x 2` C02 theorem is
met: `s>0`, `0<=eta_K(s)<1`, and the induced Euclidean operator-norm bound.

## Determinant sign and distance bound

Apply accepted C02 with `eta=eta_K(s)` to the same arbitrary, potentially
nonsymmetric `D(s)`.  C02 yields, without a determinant premise,

`det(D(s))>0`.

The positive branch `dA(s)=sqrt(det(D(s)))` is therefore defined and C02 also
yields

`s(1-eta_K(s)) <= dA(s) <= s(1+eta_K(s))`.

The Sage and Singular rings keep the off-diagonal entries algebraically
independent; in particular, `b-c` is not zero.  This guards against accidentally
specializing C02 to a symmetric or commuting matrix class.

## Boundary case K=0

For `K=0`, `f_K(s)=s` and `eta_K(s)=0`.  Both exact engines verify that the
rewrite residual vanishes and both C02 distance endpoints collapse to `s`.
C02 then gives `det(D(s))>0` and `dA(s)=s`; equivalently M04 has zero norm
deviation.  The excluded point `s=0` is not used.

## Verdict and claim ceiling

The four contracted M05 obligations close for this Sage+Singular axis by exact
dependency composition.  This is a component result only.  M04's independent
admission/review gate and the parent four-axis adjudication remain external to
this axis; scientific admission remains `HOLD`.
