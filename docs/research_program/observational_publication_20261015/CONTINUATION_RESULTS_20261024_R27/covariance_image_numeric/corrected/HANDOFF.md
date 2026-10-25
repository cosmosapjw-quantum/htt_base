# R26 covariance-image finite-check preparation

Status: **REPAIR_SOURCE_PREPARED; NOT_DISPATCHED; NOT_RUN**. This directory contains a
synthetic mathematical interface and a single bounded execution entry point. It
has not evaluated a qualified seven-channel operator or any physical input. The
controller must issue a genuine GO packet and matching `ACK.json` before the
runner may be invoked. `PREPARATION.json` gives the exact one-command handoff.

## Controlling assumptions and scope

`DERIVATION.md` and `LOWER_PROOF_FINITE_CHECK_CONTRACT.md` in the sibling
`r26_tensor_covariance_cone_theory` directory control the formulas. Matrices are
finite-dimensional, real, and exact in the SymPy interface; covariance matrices
are symmetric PSD. The synthetic channel/output unit in the relevant tests is
`mag`/`mag`, making output covariance `mag^2`. The trace cap uses the fixed
Euclidean channel coordinate convention. A nonorthogonal channel change would
also have to transform the class metric. No STF basis normalization, physical
frame, velocity map, source-qualified `M7`, mean law, or empirical covariance is
provided here.

`covariance_image.py` returns the complete covariance or a full latent lift,
never a diagonal replacement. `joint_congruence` requires the complete PSD joint
block and its class/units. Its result is a covariance image only. The exact
interface rejects floating entries. Its NumPy diagnostic retains a tiny
nonzero response as unbounded under the unbounded class even when the response
lies below its diagnostic threshold. A literal floating zero is reported with
`exact_protection_proved=False`: structural protection requires exact evidence.

The status vocabulary distinguishes `EXACT_ALGEBRAIC_NULL`,
`NUMERICAL_NEAR_NULL`, `ABSENT_COVARIANCE_BOUND`,
`UNAVAILABLE_PHYSICAL_MAP`, `UNDEFINED_INPUT_DOMAIN`, and `UNBOUNDED`.
`UNDEFINED_INPUT_DOMAIN` is raised on malformed or undecidable exact inputs;
`UNAVAILABLE_PHYSICAL_MAP` is returned at the optional physical-response
boundary. No covariance matrix supplies a probability law or `Pi`.

## Finite fixture to proposition map

| Contracted proposition | Synthetic finite falsifier / witness |
|---|---|
| PSD/range necessity and pseudoinverse sufficiency | Zero map, singular diagonal map, out-of-range `C`; rectangular rational rank-deficient map |
| Fixed row-space block and unique minimum-trace PSD lift | `[1,1]` canonical lift plus explicit null projector family; orthogonal row/column permutation |
| Singular Loewner-image converse | `G=diag(4,0)` image membership, rejection, and constructed lift |
| Right-null gauge differs from left-null contrast | `[I_5,0,-1_5]`, seven-channel constant mode, five-dimensional full row rank |
| Trace, spectral, Loewner, and unbounded full-matrix support | Indefinite/negative/zero `H`, attaining covariances, explicit unbounded ray, nonattainable trace-class joint envelope |
| Complete joint PSD and cross-block preservation | `rho=-1,0,1`; pairwise PSD but full indefinite three-block matrix |
| Known-marginal upper/lower bounds and pointwise attainment | Scalar triples `(1,4,9)` and `(16,1,1)` with rank-one PSD completions; opposite vector correlations by direction |
| Covariance-law nonuniqueness | Two exact centered variance-one discrete laws with strict-tail values zero and one-half |
| Exact null versus numerical near-null | Rational `10^-12` response, unbounded exact ray, NumPy near-null diagnostic |

These finite fixtures can falsify implementation mistakes. They do not prove
the general propositions, qualify an actual response, perform four-axis CAS
validation, close H02, or admit a statistical/physical claim. In particular,
unknown means, finite-second-moment law shape, physical response/domain, and
coverage remain separate. A completed run needs its raw first output, resource
receipt, and a fresh read-only Astra review of this candidate before any scoped
generic-interface decision. On a substantive mathematical counterexample or
ambiguous scientific convention, stop and return to the theory owner. One
bounded repair needs the controller/reviewer-defined finding and remaining
cumulative budget.

## Validation and stop conditions

Preparation used source reading, byte hashes, and standard-library AST parsing
only. Numerical package availability, fixture execution, resource behavior, and
test outcomes remain **NOT_RUN**. The single runner is capped at 60 cumulative
seconds, 512 MiB observed RSS and one BLAS thread, subject to a stricter
controller ACK. It writes `RAW_STDOUT.txt`, `RAW_STDERR.txt`, and
`RAW_RECEIPT.json` once, preserving the first result. A stopped or failed run
must be reviewed as such; no tolerance is widened to obtain a pass.

The next scientific input after a generic-interface decision is a separately
qualified signed `M7` and a stated bounded `Gamma`/`Omega` source. Any physical
functional continuation additionally needs a qualified joint response, law,
and domain. The original source-response allocations and holds are unaffected.

## Repair 1 superseding notes

This is a source-only repair preparation. The original 13 fixture result and
independent first counterexample are preserved at their original paths. The
floating diagnostic contracts the supplied binary floats as exact rational
numbers before deciding a covariance bound. A nonzero contraction is unbounded
under the unbounded PSD class even if floating norm or dot product underflows.
A zero contraction is certified only for those stored binary floats and retains
`exact_protection_proved=False`; no physical structural null is inferred. A
positive trace bound that cannot be represented as a finite nonzero float returns
`NUMERICAL_BOUND_UNREPRESENTABLE` with no numeric upper. The exact interface
rejects free symbols without explicit branch proof support. The rectangular
fixture has independent minimum trace 26/5.

Repair execution remains NOT_RUN until a genuine controller repair packet and
matching ACK are issued. The same 60-second bank has 4.368010953767225 seconds
already charged and 55.631989046232775 seconds remaining before any further
check. The copied runner uses Linux wait4 child lifetime high-water RSS for the
512 MiB cap, with sampled proc VmRSS for early stop, and one BLAS thread. Its
new raw paths are inside repair1; it does not rewrite the original receipts.
A fresh independent actual-result review is required after one bounded run.
