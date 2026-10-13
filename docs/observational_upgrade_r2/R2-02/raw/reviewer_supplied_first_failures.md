# Reviewer-supplied first failures

Controller delivered these reproduced findings from the fresh independent reviewer. They are reviewer-reported evidence; this worker did not observe the reviewer's original command execution.

1. Real heliocentric catalogue bound to CMB/CMB provider returned the same finite log likelihood rather than refusing the mismatch.
2. N100 high-information narrow-source Gaussian limit: analytic rank-one log likelihood -297.561; former prior-centred GH32 -389.416; GH64 error -45.09; GH128 error -21.61.
3. `selected_slot_block` omitted `remainder_km_s` under a provider bound of 10 km/s and silently supplied zero, returning a finite log likelihood.

The worker independently reran regression reproductions for findings 1/2 before repair; four failures are preserved in `reviewer_regressions_first.log`. The new positive-bound omission regression now requires `ProviderUnavailable`. No former failure is promoted to success retroactively.
