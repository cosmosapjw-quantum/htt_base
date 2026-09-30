# Independent SageMath + Singular proof of CAS11-C02

This is a complete ordinary mathematical proof of the frozen finite component,
supported by exact, executable CAS certificates. It is **not a proof of the
entire theorem inside a formal proof-assistant kernel**. The standard spectral
theorem and the explicit finite-sum/order reasoning below are mathematical
dependencies; neither Sage nor Singular is represented as having proved that
theorem for arbitrary dimension. There is no unresolved mathematical step in
this argument, but independent review must assess those declared dependencies
and this inference chain in addition to the computed identities.

Authority: `CAS11-C02-FINITE-GRAM.json`, SHA-256
`c66d7d00bf60786417336873dfeb97f5602d0e60a110c110ebacd9dff824b47a`.
Run: `GRSTAT-CAS11-C02-20260930T090559Z`.
Axis task: `GRSTAT-CAS11-C02-20260930T090559Z-sage_singular`.

## Assumptions and conventions

Fix an arbitrary positive integer n. Let R be any real symmetric PSD n by n
matrix, e any real n-vector, and epsilon any real number with epsilon >= 0.
The sole additional hypothesis is

    H: for every a in R^n, (a^T e)^2 <= 2 epsilon a^T R a.

Absolute value squared equals the ordinary square over the reals. All vector
products in this component are Euclidean; no Lorentzian inner product enters
this proof. PSD is an input assumption, repeated in the output, and is not a
new certification of physical residual provenance. No physical derivative,
transfer, noise-covariance, unit conversion, or continuum premise is added.

We use exactly the contract's spectral definition of Rdagger: invert positive
eigenvalues, keep zero eigenvalues zero. We never form inverse(R) on a singular
matrix and never divide by epsilon, a component of e, or an aggregate energy.

## Universal proof

**1. Spectral coordinates.** By the real finite-dimensional spectral theorem,
choose an orthonormal basis q_1,...,q_n with R q_i = lambda_i q_i. Each
lambda_i >= 0, since q_i^T R q_i = lambda_i and R is PSD. Set z_i = q_i^T e.
Then e = sum_i z_i q_i. This theorem applies to repeated eigenvalues, zero
eigenvalues, and every finite n; no simplicity or full-rank assumption is used.

**2. Every zero-eigenvalue coordinate of e vanishes.** Instantiate H at q_i.
This yields z_i^2 <= 2 epsilon lambda_i. Set

    h_i = 2 epsilon lambda_i - z_i^2 >= 0.

If lambda_i = 0, then h_i + z_i^2 = 0. If z_i were nonzero, z_i^2 would be
strictly positive and h_i nonnegative, contradicting this equality. Hence
lambda_i = 0 implies z_i = 0. The engine certificate `null_mode_slack`
verifies the exact algebra; `null_mode_sign` checks the positive-cone
contradiction. The same argument with epsilon = 0 instead of lambda_i = 0,
certified by `epsilon_zero_slack`, gives z_i = 0 for **all** i on the
epsilon-zero branch.

Neither range membership nor a pseudoinverse bound has been assumed here.
The appearance of z=0 in later zero-branch ideals uses this already-derived
conclusion, not an extra restriction on the input vector.

**3. Construct a preimage of e.** Define

    mu_i = 1/lambda_i if lambda_i > 0, and mu_i = 0 if lambda_i = 0,
    c = sum_i mu_i z_i q_i = Rdagger e.

This is an exhaustive branch split because every lambda_i is nonnegative.
In the positive branch lambda_i mu_i = 1, so lambda_i mu_i z_i = z_i.
In the zero branch both sides equal zero, by step 2. The certificates
`positive_range` and `zero_range` verify both algebraic identities. Consequently

    R c = sum_i lambda_i mu_i z_i q_i = sum_i z_i q_i = e.

Thus c is an explicit real preimage and e belongs to range(R). Division has
occurred only by an eigenvalue in its strictly positive branch.

For completeness, the `positive_mp_one`, `positive_mp_two`, `zero_mp_one`,
and `zero_mp_two` certificates verify lambda mu lambda=lambda and
mu lambda mu=mu in both spectral branches. Together with the symmetry of the
real diagonal spectral factors, these also agree with the Moore-Penrose
equations. The controlling definition remains the contract's spectral one.

**4. The three scalar expressions coincide.** Put

    s = e^T Rdagger e = sum_i mu_i z_i^2.

Orthonormality gives c^T e = sum_i (mu_i z_i) z_i = s. Also

    c^T R c = sum_i lambda_i (mu_i z_i)^2 = sum_i mu_i z_i^2 = s.

The last termwise equality is `positive_energy` when lambda_i>0 and
`zero_energy` when lambda_i=0. `dot_energy` is the other termwise identity.
No division by s is involved; s=0 is allowed. Its nonnegativity also follows
from mu_i>=0, but that additional fact is not needed in the final argument.

**5. Instantiate the hypothesis at the constructed vector.** Since H holds
for every real a, it applies to c. Step 4 then gives

    s^2 <= 2 epsilon s.

Let h = 2 epsilon s - s^2 >= 0. Suppose, for contradiction, that
s > 2 epsilon and set d = s - 2 epsilon > 0. The exact polynomial identity

    h + d^2 + 2 epsilon d
      = (h - 2 epsilon s + s^2) + (d+s)(d-s+2 epsilon)

has right-hand side zero. Its left-hand side is strictly positive: h>=0,
d^2>0, and 2 epsilon d>=0. This is impossible. `bound_contradiction`
certifies the identity and `bound_sign` checks the positive-cone witness.
Therefore s <= 2 epsilon, proving e^T Rdagger e <= 2 epsilon.

This proves exactly the assigned forward implication. No reverse implication
or target-equivalent hypothesis is used.

## Why this covers arbitrary dimension and rank

The index i above is arbitrary, not a sampled coordinate. The two eigenvalue
branches exhaust each of the n indices for any n. Scalar identities lift to
finite sums by induction: the empty-sum base is 0=0; if A=B and x=y, then
(A+x)-(B+y)=(A-B)+(x-y)=0. Both the base and this symbolic induction step are
checked in the two engines (`sum_base`, `sum_step`). Their variables are
indeterminate scalars, not fixed-dimension matrices. Matrix action and inner
products distribute over these finite sums by their ordinary definitions.
The spectral theorem supplies an orthonormal basis for the arbitrary n fixed
at the start. Accordingly, there is no finite-dimension experiment being
promoted to a universal proof.

| R branch | epsilon > 0 | epsilon = 0 |
|---|---|---|
| Positive definite, rank n | Steps 1-5 with positive eigenvalues | `epsilon_zero_slack` forces e=0; steps 1-5 also apply |
| Singular nonzero, rank 1,...,n-1 | Zero coordinates vanish; both spectral branches apply | Every coordinate vanishes, so e=0; both spectral branches remain valid |
| R=0, rank 0 | All z_i=0, hence e=0, Rdagger=0, and 0<=2 epsilon | e=0, Rdagger=0, and 0<=0 |

For n=1 the singular-nonzero interval is empty, as it should be. The zero
matrix and epsilon-zero intersection is included explicitly. Every division
is confined to a positive eigenvalue, including these boundary cases.

## Exact machine certificates and their limits

`engine.py` uses Sage's exact QQ polynomial ring. Each ideal-membership
certificate computes both an explicit multiplier identity and a Groebner
normal form. `certificates.sing` separately sends the same named mathematical
identities to the actual `/usr/bin/Singular` engine. It does not read Sage's
outputs. All polynomial residuals and normal forms must be zero. Identities
over QQ remain valid upon substitution of arbitrary real values, including
irrational eigenvalues and eigenvector coordinates.

The positive-branch relation lambda mu - 1 = 0 follows from the explicitly
nonzero inverse definition. The zero-branch relations lambda=0, mu=0, z=0
follow respectively from the case condition, the definition, and step 2.
The bound relations h-2 epsilon s+s^2=0 and d-s+2 epsilon=0 are definitions
of the hypothesis slack and the putative violation. These are not the target
or an equivalent form inserted into the assumptions.

The Sage sign checker enumerates the nonzero monomials of each of two
polynomials. A positive rational coefficient times nonnegative factors is
nonnegative; an even power of a nonzero real is positive; a sum containing a
positive monomial and only nonnegative others is positive. It confirms the
following **conditional** witnesses:

| Polynomial | Derived or contradiction premises | Strictly positive term |
|---|---|---|
| h + z^2 | h>=0, z!=0 | z^2 |
| h + d^2 + 2 epsilon d | h>=0, d>0, epsilon>=0 | d^2 |

The sign rules themselves are ordinary ordered-real facts, and their checker
is transparent code, not a separately verified proof kernel. Singular checks
the algebraic equality underlying each contradiction, not an inequality
decision procedure. Actual engine execution is required even though the
mathematical proof is readable without the software.

The following dependencies are not proved by these CAS runs:

1. The real finite-dimensional spectral theorem and orthonormal expansion.
2. Finite-sum bilinearity and ordinary finite induction.
3. Ordered-field rules, universal instantiation, and contradiction reasoning.
4. The contract's spectral definition of the Moore-Penrose inverse.
5. Preservation of rational polynomial identities under real substitution.

They are stated standard mathematical results/rules, not newly posited
target-equivalent axioms. The explicit proof above performs the lifting.
Machine verification alone establishes the listed algebra and sign
certificates; the completed axis proof additionally uses these dependencies.

## Execution and evidence

From the bound repository root, run:

```sh
/usr/bin/python3 docs/research_program/gr_statistics_loops_20260930/local_cas/GRSTAT-CAS11-C02-20260930T090559Z/sage_singular/completion/run_axis.py
```

The runner checks the frozen contract identity and seals the five own-axis
source/coverage files plus the contract and neutral brief **before starting
any engine process**. Each execution creates a new `observations/` child;
previous executions and failures are retained. Complete version banners and
raw stdout/stderr are stored separately for Sage and Singular. `invocation.json`
records each actual argv, cwd, exit code, duration, and raw-log identity.
Sage records every multiplier, generator, residual, normal form, and sign
witness in `sage_certificates.json`; Singular prints targets, residuals and
normal forms in `singular.stdout.txt`.

Only after both engines complete all required computations and source hashes
remain unchanged does the runner emit exactly one JSON object on stdout with
the requested obligation key. Missing engines, failed identities, incomplete
certificate sets, stale source, or unresolved coverage produce a nonzero exit
and no success payload. The success object refers to this complete argument
with its declared standard dependencies, not to an engine-only universal
theorem proof. Host adjudication and independent review remain distinct.

## Physics/math audit verdict and claim ceiling

| Item | Result | Scope |
|---|---|---|
| Assumptions | Aligned | Real symmetric PSD R; epsilon>=0; H universal |
| Metric/sign | Aligned | Positive Euclidean finite components; no Lorentz calculation |
| Normalization | Aligned | The factor 2 epsilon is preserved exactly |
| Singular and zero limits | Covered | No full matrix inverse, no epsilon or energy division |
| PSD output | Assumed | No physical Gram provenance is inferred |
| Range and bound | Proved by the argument above | Engine-certified algebra plus declared standard mathematics |

The only safe claim is the finite contracted implication under its stated
assumptions. This result does not certify CAS11-C01, CAS11-C03, complete CAS-11,
continuum closure, physical derivative bounds, observational inference, a noise
covariance interpretation, novelty, or scientific admission. No fatal
mathematical blocker is identified within this target; broader claims remain
outside it.
