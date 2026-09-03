# Scientific contract — existing theory survivor closeout

## Scientific objective

Produce a current, source-bound release overlay for already established
observation-independent results. Preserve broad unresolved or failed parent
claims, distinguish supporting lemmas and synthetic validation, and avoid
developing new theory.

## Governing objects

```yaml
campaign_disposition:
  PROMOTED | REFUTED | UNRESOLVED | DEFERRED | NOT_ATTEMPTED

campaign_disposition_source:
  exact historical campaign receipt | exact current closeout receipt

historical_campaign_disposition:
  optional comparison field copied from frozen historical evidence

truth_status:
  ESTABLISHED | REFUTED | OPEN | NOT_ASSESSED

evidence_modality:
  HAND_DERIVATION
  | EXACT_FINITE_ENUMERATION
  | EXACT_SYMBOLIC_IDENTITY
  | FORMAL_KERNEL_PROOF
  | FORMAL_ARITHMETIC_REPLAY
  | EXACT_COUNTEREXAMPLE
  | PREREGISTERED_SYNTHETIC_EXPERIMENT
  | INCOMPLETE
  | UNAVAILABLE

replay_status:
  CURRENT_PASS
  | HISTORICAL_PASS_CURRENT_INCOMPLETE
  | CURRENT_BLOCKED
  | CURRENT_FAIL
  | NOT_RUN

novelty_status:
  NOVEL | APPLICATION_SPECIFIC | KNOWN_OR_STANDARD | UNASSESSED

survivor_release_status:
  ELIGIBLE | BLOCKED | NOT_APPLICABLE

campaign_completion_status:
  OPEN | COMPLETE
```

Machine outputs must use the canonical enum values above. Narrative audit labels
`EXACT_ENGINE_REPLAY` and `HAND_DERIVATION_AND_EXACT_COUNTEREXAMPLE` are
descriptive aliases only and normalize respectively to
`EXACT_SYMBOLIC_IDENTITY` and the ordered pair
`[HAND_DERIVATION, EXACT_COUNTEREXAMPLE]`.

No field is automatically derived from another. In particular:

```text
truth ESTABLISHED does not create or rewrite campaign disposition;
campaign OPEN does not block release of an eligible survivor;
engine availability does not change truth;
synthetic validation is not a theorem.
```

## Conventions and domains

- Matrix/tensor algebra is exact over real symmetric trace-free \(3\times3\)
  tensors unless a source states otherwise.
- The VT-T8 chart is an active \(SO(3)\) local quotient statement on the
  simple-spectrum cyclic locus. \(O(3)\) parity and global reconstruction are
  separate.
- The VT-T13 quotient chain rule requires \(I_2>0\).
- PR-190 is restricted to the registered homogeneous Bianchi-I
  hypersurface-normal frame.
- PR-284 is one equal-weight four-atom fixture and uses the inclusive event.
- Units are dimensionless for orbit-shape algebra. For the PR-284 probability
  fixture, squared quantities share the square of the unit of \(X\).

## Required invariants

1. exact historical artifacts are byte-preserved;
2. every current survivor has a source-bound exact statement;
3. broad parent and narrow child are different candidate IDs;
4. evidence is acquired and validated before status projection;
5. truth, replay, novelty, release, and historical campaign state are
   independent;
6. no universal candidate-universe claim is emitted;
7. survivor release is independent of unrelated unattempted proposals;
8. no new theorem is required on the core closeout path;
9. existing DAG nodes and edges remain an exact prefix;
10. every P0/P1 has a regression, assertion, or typed STOP.

## Known exact cases

| Case | Expected result |
|---|---|
| PR-284 event probability | \(1/2\) |
| PR-284 bound | \(25/36\) |
| PR-284 slack | \(7/36\) |
| VT-T8 quotient dimension | 14 |
| VT-T8 registered witness determinant | 50331648 |
| VT-T13 \(\dot I_2\) | \(2\operatorname{tr}(\sigma\dot\sigma)\) |
| VT-T13 \(\dot I_3\) | \(3\operatorname{tr}(\sigma^2\dot\sigma)\) |

## Failure semantics

The following never count as successful closeout:

- missing source treated as attempted proof;
- historical release block treated as mathematical refutation;
- exact truth treated as automatic campaign promotion;
- registered surface called the universe of all mathematical subclaims;
- unresolved new-theory work silently implemented;
- synthetic validation counted as theorem;
- novelty left unassessed while publication-ready is claimed;
- failed or inconclusive broad parent hidden by a narrow child;
- generic CI quoted for tests it did not execute.

## Change control

Changing a statement, domain, frame, proof obligation, historical disposition,
novelty classification, or release claim requires a new explicit scientific
review. Expected values or tolerances may not be changed to fit an
implementation.
