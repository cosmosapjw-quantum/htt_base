# Local/global response laboratory

This generated experiment uses declared dimensionless matrices and a known
correlated Gaussian covariance. It is not an observational fit. The existing HTT
`nuisance_projected_rank` code is reused.

The constant target has rank 0 after profiling local boost. The specified depth
target has rank 3; a free vector nuisance in each shell reduces its rank to 0.
The smallest singular value decreases linearly with the added depth amplitude:
formal full rank alone does not provide useful precision. The three-row exact
check gives information 2 with identity noise and 26/49 with variances (1,4,9),
matching the independent Wolfram algebra check.

![Synthetic response diagnosis](response_identifiability.png)

Physical continuation: replace these explicit example matrices with
source-bound local observer, matter-tilt and survey response derivatives. State
parameter units and scales before singular-value thresholds; validate derivatives
and truncation bounds, then test null-calibrated power. No universal no-go or
new physical identification follows from the example.
