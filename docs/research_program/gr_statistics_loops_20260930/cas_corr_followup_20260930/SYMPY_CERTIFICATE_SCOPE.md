# C04 SymPy certificate preparation and scope

The initial `c04_sympy_certificate.py` was authored using only the assigned
sealed C04 statement contract. Its author read no sibling implementation,
result, original proof, or prior PASS. The integrating host then read both
completed programs and changed failure reporting to omit scientific Boolean
results on all failures. The final integrated source is therefore source-informed.
No actual model identity was supplied, and none is asserted.

Preparation status: **UNEXECUTED with respect to SymPy and every mathematical
check**. No scientific package was installed or imported during preparation.
Any source syntax check or bad-contract CLI check is not a theorem run. The JSON
status `PASS_CERTIFICATE` is produced only by a later successful local run.

## Local invocation

From the directory containing the script, with SymPy already available:

```sh
python c04_sympy_certificate.py --contract intake/contracts/CAS13-C04-RELATIVE-MINIMAX.json --self-test
```

The checker first hashes the exact contract bytes using SHA-256 and requires
`0002809c73fd5de362deded39735fe884183bb953029f671552a525f74086f63`.
A missing or mismatched contract returns exit 2, writes a diagnostic to stderr,
emits no stdout scientific payload, and does not import SymPy. A missing SymPy
dependency returns exit 3. Mathematical certificate rejection returns exit 1
with stderr diagnostics and no stdout target payload. Unexpected backend errors
return exit 3 with stderr diagnostics and no stdout target payload. Neither path
is a mathematical counterexample or a scientific `checks[target]=false` result.
Successful checking returns exit 0. Preserve the actual command, process exit,
and complete raw stdout/stderr externally; self-reported metadata do not replace
those process records.

## Exact theorem and domain

For real `L,U` satisfying `0 < L <= U`, put `S=L+U`,
`a_star=2LU/S`, and `r_star=(U-L)/S`. The three checked statements are:

1. Every real `x` in `[L,U]` satisfies `abs(a_star/x-1) <= r_star`.
2. Both endpoint losses equal `r_star`.
3. Every real `a` satisfies
   `r_star <= max(abs(a/L-1), abs(a/U-1))`.

The interval proof has the additional assumptions `x-L>=0` and `U-x>=0`.
Endpoint and minimax proofs use a separate context containing only `L>0` and
`U-L>=0`. The predictor has no sign restriction. No division by `U-L`, by `a`,
or by an interval width occurs. Thus `L=U>0` and all three signs of `a` are
covered by the same chain. A changed domain, including a stronger strict-gap
condition or a positivity restriction on `a`, is rejected.

## Universal certificate chain

This is a symbolic ordered-real proof certificate, not random testing or a
claim that endpoint substitution alone proves a universal assertion.

Strict positivity is certified by nonnegative polynomial sums and products:

```text
U = L + (U-L) > 0
S = 2L + (U-L) > 0
x = L + (x-L) > 0                 [interval context only]
LS > 0, US > 0, xS > 0
```

Every rational object keeps an explicit denominator with a bound positivity
proof. Rational identities are checked by exact cross multiplication after both
denominators are proved strictly positive. SymPy's `Poly(..., domain=QQ)` checks
zero polynomials; no tolerance, floating arithmetic, sampling, `simplify()`
truth inference, or generic inequality-solver success is accepted.

For `y=a_star/x-1`, the interval certificates are:

```text
r_star-y = 2U(x-L)/(xS) >= 0
r_star+y = 2L(U-x)/(xS) >= 0
```

Each numerator is an explicitly checked positive-coefficient product of
nonnegative domain facts, and `r_star>=0` follows from `U-L>=0` and `S>0`.
The explicit absolute-value rule gives `abs(y)<=r_star`.

At the endpoints, exact rational identities show
`a_star/L-1=r_star` and `a_star/U-1=-r_star`. Together with `r_star>=0`, the
absolute-value equality rule gives both losses exactly.

For the lower bound, introduce a conservative definitional auxiliary:

```text
t = max(abs(a/L-1), abs(a/U-1)).
```

The maximum and absolute-value order rules yield
`t-(a/L-1)>=0` and `t+(a/U-1)>=0`. Clearing their separately proved positive
denominators yields the polynomial facts

```text
cL = Lt-a+L >= 0
cU = Ut+a-U >= 0.
```

The checker verifies the exact polynomial certificate

```text
S*t-(U-L) = cL+cU >= 0.
```

Division by the proved positive `S` gives `t-r_star>=0`, which is exactly the
third target after substituting the definition of `t`. No extra assumption
about `t` or the sign of `a` is introduced.

## Limited trust boundary

The trusted inference rules are:

- The declared domain statements hold over an ordered real field.
- Positive-coefficient sums of products of nonnegative facts are nonnegative.
  A product is strict when all factors are strict; a sum is strict when a term
  is strict. The empty product is `1>0`.
- Positive denominators permit cross multiplication, preserve the sign of a
  quotient numerator, and permit clearing a nonnegative quotient.
- Equality permits substitution in inequalities.
- For `r>=0`, `-r<=y<=r` implies `abs(y)<=r`, and `y=+/-r` implies `abs(y)=r`.
- `max(abs(z0),abs(z1)) >= abs(zi) >= +/-zi`.
- `t-r>=0` is equivalent to `r<=t`.

The trust boundary includes Python's implementation of these rules and SymPy's
exact rational polynomial arithmetic. It is deliberately not described as
proof-assistant kernel checking or general quantifier elimination. A local
execution can establish all three scalar targets relative to this explicit
boundary. It does not establish scientific admission, other CAS-13 components,
or a general supremum-construction theorem. The parent contract remains open.

## Callable verifier and controls

`build_certificate(sympy)` creates the data certificate;
`verify_certificate(certificate, sympy)` verifies it and returns the result
payload, raising `CertificateError` on rejection. The fixed theorem formulas
and proof rules are in the verifier, not supplied as success flags by the data.
`run_mutation_controls(sympy)` verifies rejection of:

- an incorrect positive coefficient;
- a negative coefficient asserted as nonnegative;
- weakening `L>0` to `L>=0`;
- excluding `L=U` with a strict gap;
- imposing a predictor positivity restriction;
- a denominator with a corrupted sign;
- omission of the universal minimax certificate.

With `--self-test`, all these rejection controls must succeed as well as the
valid certificate; otherwise the overall check fails. They test certificate
integrity and domain coverage, not empirical examples of the theorem. The
script never turns a rejected certificate into a purported counterexample.

Expected successful stdout has a computed Boolean under
`checks["CAS13-C04-RELATIVE-MINIMAX"]`, `domain_assumption_diff: []`,
`counterexample: null`, and detailed statement alignment, coverage, exact check
counts, sign certificates, source/contract hashes, and execution metadata.
An empty domain difference alone is never used as proof of the target.
