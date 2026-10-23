# Radio conditional scalar covariance envelope

Executed the one authorized 713-row pass for all eight frozen D05 maps:
104 scalar coordinate maxima, with all focused controls passing beforehand.
Independent fresh read-only Astra review remains PENDING.

The conditional SD envelopes span 1.95361 to 8.95381 microarcsec/year;
their ratios to the old working SD span 16.3578 to 62.6936.
All 104 values and all eight newly accumulated normal matrices are in RESULTS.json.
PNG and PDF show every coordinate in the fixed scenario order, with separate
units for envelope magnitude and the dimensionless working-reference ratio.

For flattened scalar marginals, PSD implies |Sigma_ab| <= sigma_a sigma_b.
Therefore ell Sigma ell^T <= (sum |ell_a| sigma_a)^2. The rank-one covariance
u u^T, u_a = sigma_a sign(ell_a), attains this maximum for each coordinate
separately; either sign is allowed at zero weight. Positive-definite restriction
has the same supremum, by approaching this witness with a diagonal mixture.
This scalar-marginal result differs from the earlier Gaia fixed-block question.

The estimator map uses the full 16-column cached covariance before selecting the
13 retained coordinates. The frame quotient leaves physical B1 UNKNOWN.
Maximum |V N - I|: 6.27657e-15.
Maximum |sum L_i X_i - R|: 4.83447e-14.
Maximum relative working-variance residual: 2.11036e-14.
Motion errors are already microarcsec/year, without factors 15 or 1000.
The position RA hour conversion alone uses 15 degrees/hour. Released J2000
directions refer to the most recent VLBA observing epoch; no propagation occurred.

Owner obsstat; claim tier C0; DIAGNOSTIC_ONLY; transfer source none.
True joint covariance and empirical null are UNKNOWN/NOT_AVAILABLE.
Working rho defines each fixed map, not a restriction on the true correlations.
Published marginal errors are a working hypothesis for this selected catalogue.
Bias is unmeasured: these are centered-variance envelopes, not MSE bounds.
Frame/NNR constraints may exclude the maximizing covariance. Coordinate maxima
need not be jointly attained and their diagonal is neither a joint covariance
nor a Loewner upper bound. Neither RA interpretation is preferred or resolved.
These are not confidence error bars or coverage statements. No p-value,
Gaia-radio independence, cosmic curl, matter vorticity, native solver, family
identification or K03 admission follows. Original 17/42 and all six
NOT_READY_TO_SUBMIT states remain unchanged.

Sources, hashes, method, environment and rows are bound in RESULTS.json;
plot hashes and plotted matrices are in PLOT_PROVENANCE.json. No source rows,
motions, RHS, fitted coefficients, holdouts or row-level weights are stored here.
Requested author gpt-6.1-sol/high; observed model/effort UNKNOWN.
NUMERICAL_USAGE.jsonl records every numerical command, resource samples, exit
and cumulative wall time, including this cached plot step; the fixed cap is 60s.

Claim audit: only conditional scalar variance maxima are asserted, supported by
focused controls and the generated artifact. No scientific status promotion or
permanent claim-ledger update is made. Source failure, invalid rows, map failure,
nonfinite values or resource exhaustion require STOP/HOLD under CONTRACT.md.
