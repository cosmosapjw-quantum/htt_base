# CAS11-C02 v3 — independent Wolfram-axis completion

Owner: `wolfram_xact` axis, existing task
`GRSTAT-CAS11-C02-20260930T090559Z-wolfram_xact`.
Authority: `CAS11-C02-FINITE-GRAM.json`, SHA-256
`c66d7d00bf60786417336873dfeb97f5602d0e60a110c110ebacd9dff824b47a`.
This is a fresh derivation from the frozen contract and neutral axis brief.
No historical axis proof, sibling source, sibling result, or Host derivation
was read. The permitted environment description was read to locate the
Wolfram/xAct runtime; it is not mathematical evidence for this execution.

## Verdict and verification boundary

The forward theorem has a complete universal mathematical proof below, using
standard finite-dimensional real spectral theory, finite-sum induction, and
exact scalar lemmas checked by the actual Wolfram engine. The arbitrary-n
matrix theorem is **not fully formalized or kernel-certified**. Wolfram
certifies the displayed scalar implications and induction steps; the author
supplies the stated spectral reduction and induction application. There is
no unresolved mathematical case in that explicit inference chain. This is
mixed analytic/CAS verification, subject to independent Host adjudication.

The runner emits success only after all named exact certificates finish
successfully with the unchanged frozen contract and sealed source/proof
files. The runner's boolean must be interpreted with this boundary. It is
not a certificate that Wolfram proved the spectral theorem or checked the
entire proof document. No physical or scientific admission follows.

## Assumptions and conventions

Let n be an arbitrary positive integer, R an arbitrary real symmetric PSD
n-by-n matrix, e an arbitrary real n-vector, and epsilon an arbitrary real
number with epsilon >= 0. Assume

    for every a in R^n, (a^T e)^2 <= 2 epsilon (a^T R a).             (P)

Because all scalars are real, this is exactly the contract's absolute-value
square. Products and orthogonality are Euclidean. The Lorentz-signature
convention does not enter this finite theorem. R is a deterministic Gram
object, not an observational covariance. PSD is an input and is returned
unchanged as the contract's repeated PSD output. No physical residuals or
positive physical weight are constructed here.

Use precisely the contract's spectral Moore-Penrose definition: if
R = Q diag(lambda_j) Q^T with Q real orthogonal and lambda_j >= 0, define

    p_j = 1/lambda_j if lambda_j > 0, and p_j = 0 if lambda_j = 0,
    Rdagger = Q diag(p_j) Q^T.

No epsilon, zero eigenvalue, or zero sum is divided out.

## Universal proof

1. **Spectral coordinates.** The real symmetric spectral theorem gives an
   orthogonal Q and a real diagonal matrix D with R = Q D Q^T. PSD gives
   lambda_j >= 0 for every j: an eigenvector v_j has unit length, so
   lambda_j = v_j^T R v_j >= 0. Put c = Q^T e. Then e = Q c.
   For every b in R^n, choose a = Q b in (P). Orthogonality gives

       (b^T c)^2 <= 2 epsilon (b^T D b).                            (1)

   This is a universal substitution into the original premise. It does
   not replace that premise by finitely many tests.

2. **Null coordinates.** For an arbitrary index j with lambda_j = 0,
   substitute b = the j-th coordinate vector in (1). It yields c_j^2 <= 0,
   hence c_j = 0 over the reals. `null_coordinate` checks exactly this
   implication. The argument applies to each j of any finite index set;
   the number or position of zero eigenvalues is unrestricted.

3. **Spectral inverse and a range witness.** Define p_j as above and
   h_j = p_j c_j. The relation

       (lambda_j > 0 and lambda_j p_j = 1)
       or (lambda_j = 0 and p_j = 0)                               (2)

   characterizes that p_j without division on the zero branch.
   The exact certificate `spectral_reciprocal_penrose` proves under (2)
   that p_j >= 0, lambda_j p_j lambda_j = lambda_j, and
   p_j lambda_j p_j = p_j. The diagonal products are real symmetric;
   conjugating by real orthogonal Q therefore gives all four
   Moore-Penrose equations. This consistency check introduces no new
   inverse convention.

   By step 2, (lambda_j = 0) implies c_j = 0. The exact certificate
   `coordinate_range_and_quadratics` proves under (2) and that already
   derived null implication that

       lambda_j h_j = c_j,                                        (3)
       h_j c_j = p_j c_j^2,                                       (4)
       lambda_j h_j^2 = p_j c_j^2,                                (5)
       p_j c_j^2 >= 0.                                            (6)

   Thus D h = c coordinatewise. Let a_* = Q h, an ordinary real vector
   in the domain of (P). Matrix multiplication gives

       R a_* = Q D Q^T Q h = Q D h = Q c = e.

   This supplies an explicit preimage, proving e belongs to range(R).
   Range membership was not an assumption.

4. **Finite sums at arbitrary n.** Set t = sum_{j=1}^n p_j c_j^2.
   Summing (4), (5), and (6) gives

       h^T c = t,   h^T D h = t,   t >= 0.                         (7)

   The lifting is ordinary mathematical induction on the number of
   coordinates, starting at the empty sum 0. For an equality of sums,
   if S_k = T_k and the next summands u = v, then S_k+u = T_k+v;
   `finite_sum_identity_step` certifies this for arbitrary real values.
   For nonnegativity, if S_k >= 0 and u >= 0, then S_k+u >= 0;
   `finite_sum_nonnegative_step` certifies this universally. Both bases
   are respectively 0=0 and 0>=0. Induction gives (7) for every natural
   n, in particular every contracted n>0. No selected dimension,
   sample matrix, convergence limit, or rank assumption appears.

5. **Bound from the one constructed vector.** Apply (P) at a_* = Q h.
   Orthogonality and (7) give

       a_*^T e = h^T c = t,
       a_*^T R a_* = h^T D h = t,
       t^2 <= 2 epsilon t.                                        (8)

   `terminal_scalar_bound` is exact real quantifier elimination for

       forall real t,epsilon:
       epsilon >= 0 and t >= 0 and t^2 <= 2 epsilon t
       imply t <= 2 epsilon.                                     (9)

   It retains both t=0 and t>0, and both epsilon=0 and epsilon>0.
   In elementary terms, t>2 epsilon with epsilon>=0 would force
   t>0 and t(t-2 epsilon)>0, contradicting (8). No cancellation
   assumes t or epsilon is nonzero.

6. **Identify the requested quadratic form.** By the specified spectral
   definition and orthogonality,

       e^T Rdagger e
       = (Q c)^T Q diag(p_j) Q^T (Q c)
       = c^T diag(p_j) c
       = sum_{j=1}^n p_j c_j^2 = t <= 2 epsilon.

   Together with step 3 and the input PSD property this is the complete
   contracted conclusion, with no additional domain assumptions.

## Branch coverage

| Branch | Reason it is covered |
|---|---|
| R positive definite, epsilon>0 | All lambda_j>0; steps 3–6 apply. |
| R positive definite, epsilon=0 | The same proof gives t=0; independently, (1) at every coordinate gives c_j^2<=0. |
| R singular nonzero, epsilon>0 | Step 2 handles every zero coordinate; positive coordinates obey the other disjunct of (2). |
| R singular nonzero, epsilon=0 | Both coordinate disjuncts remain present; `zero_epsilon_coordinate` and `zero_epsilon_terminal` check the exact zero-bound implications. |
| R=0, epsilon>0 | All c_j=0 by step 2; p_j=h_j=0, so e=0 and t=0. |
| R=0, epsilon=0 | The preceding zero-matrix argument gives e=0 and the exact bound 0<=0. |

For the zero-matrix branch, the base and `finite_sum_zero_step` lift all
zero summands to t=0 for arbitrary n; `zero_matrix_target` verifies
t=0 <= 2 epsilon for every epsilon>=0. These redundant branch certificates
do not substitute for the universal proof. The n=1 case is included by the
same induction. Repeated eigenvalues, arbitrary rank, and arbitrary real
orthogonal eigenbasis changes introduce no new cases.

Every finite real PSD R also has a finite real Gram representation:
B = diag(sqrt(lambda_j)) Q^T gives B^T B = R. This standard consequence of
the same spectral theorem explains the contract's domain statement; no
physical residual-Gram provenance is inferred from that representation.

## Dependencies and exact division of responsibility

| Dependency | Status and use |
|---|---|
| Finite real symmetric spectral theorem | Standard mathematical theorem, invoked analytically in step 1; not proved or imported as a formal lemma by Wolfram. |
| PSD eigenvalues are nonnegative | Derived in step 1 from the PSD definition and the eigenvector equation. |
| Matrix multiplication, transpose, orthogonal identities | Standard finite-sum algebra, used analytically in steps 1, 3, 5, 6; no arbitrary-dimension matrix formalization is claimed. |
| Coordinatewise vector equality and definition of range | Standard definitions; the preimage a_* is displayed explicitly. |
| Induction over finite index sets and empty sum 0 | Standard induction rule, applied analytically in step 4; its scalar recurrence steps are exactly checked by Wolfram. |
| Real ordered field arithmetic and quantifier elimination | Actual Wolfram `Resolve[..., Reals]` checks every named scalar implication. No floating-point calculation is used. |
| Spectral Moore-Penrose definition | The frozen contract's definition; its coordinate Penrose identities are additionally checked. No target-equivalent assumption is introduced. |
| Wolfram Engine and xAct/xTensor/xPerm | Loaded versions and source identities are captured in raw logs/report. xAct is loaded to bind the declared axis environment; this Euclidean scalar reduction needs no tensor canonicalization. xAct is not credited with proving the theorem. |
| Python standard library | Invocation, hashing, logs, process cleanup and protocol only; no mathematical computation or alternate CAS. |

There is no general-n matrix library proof artifact and no proof-assistant
kernel check for this axis. The complete proof's mathematical validity
therefore includes the explicit analytic inference chain above. A consumer
whose acceptance requires full kernel formalization must classify that
stronger requirement as unmet; the runner does not establish it.

## Reproduction and evidence

From the exact repository root, invoke:

```text
/usr/bin/python3 docs/research_program/gr_statistics_loops_20260930/local_cas/GRSTAT-CAS11-C02-20260930T090559Z/wolfram_xact/completion/run_axis.py
```

Each invocation preserves its own `runs/<UTC>/source_seal.json` before
starting `/usr/bin/wolframscript -file .../verify.wls`. Complete banners,
certificate statements/results, stdout/stderr, engine/package versions,
actual argv/cwd/exit, package-source hashes and kernel cleanup observation
remain in that attempt directory. `latest_run.json` points to the most
recent successful invocation. Historical evidence elsewhere is untouched.

No tests or validators are modified. No tolerance or precision is used.
No numerical spot checks are being promoted to universal proof.

## Claim-tier implications and limitations

The only defended claim is the finite real algebraic component under the
frozen assumptions. CAS-11-C01/C03 and the original parent contract are
unchanged. Physical derivative bounds, continuum closure, Taylor/Bregman
integrals, noise covariance, observation, inference, novelty, and scientific
admission are outside this proof. The existing scientific HOLD remains.
