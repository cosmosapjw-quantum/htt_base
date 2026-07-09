# Reviewer response skeleton: strengthening without tone-down

## General response

We thank the reviewer for identifying places where the previous draft mixed theorem scope, diagnostic scope, and observational scope too loosely. We have not weakened the claims. Instead, we have replaced informal claims by stronger formal statements with explicit estimands, exact domain conditions, and executable validation gates.

## Response to concern: diagnostic_only figures cannot support physical claims

We agree that diagnostic figures cannot be read as posterior evidence or geometry assignment. The revision makes this distinction the central contribution rather than a caveat: the paper's estimand is the signed-comparator identified set and calibrated diagnostic functional. Each figure now declares the observable vector, response rank, null/covariance policy, and claim tier. No figure is used as a posterior/evidence/family-assignment result.

## Response to concern: P31 sharpness may not be full physical sharpness

The revised theorem distinguishes sharpness over the registered component cone from sharpness over a local constrained-data realization class. We add a local realization theorem and a numerical endpoint-realization witness. This directly addresses the possibility that Einstein constraints shrink the feasible set.

## Response to concern: P36 strictness statement is false

The universal strictness sentence has been replaced by a stronger exact theorem. The joint feasible-set interval is the sharp identified interval and is always contained in the marginal quotient interval. Strict inclusion is characterized by explicit compatibility conditions; equality cases are now unit tests rather than hidden exceptions. Generic strictness is supported by a coefficient phase diagram.

## Response to concern: coverage assumes known covariance

We split the theorem into known-covariance and estimated-covariance cases. The estimated-covariance lane requires Hartlap correction or Sellentin-Heavens covariance marginalization, and every relevant statistic records p, Nsim, and correction policy.

## Response to concern: current data do not identify geometry

Correct; the paper does not claim geometry identification. It claims something stronger and more primitive: current channels identify a rank-limited response class, a signed comparator interval, and prior-exposure labels. Detailed geometry inference is deferred to the native transfer handoff and requires branch-specific likelihood evidence.

