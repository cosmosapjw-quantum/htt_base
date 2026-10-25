# Independent review: scoped finite conditional PASS

The new WMAP plus fixed Planck F2 extension meets its finite conditional acceptance. All 12 response conventions, each with 12 and 17 rows, resolve nuisance rank 9 and augmented rank 10. Original L03/H02/H04 and all actual-sky acceptances remain HOLD. This decision is bound to the exact producer and checker identities in RESULT.json; internal harness labels were not treated as scientific verdicts.

## Assumptions and conventions

Owner obsstat; claim tier C0; transfer source none. The model uses nine free signed foreground moments, exact accepted binary64 old seven rows, released signed WMAP detector samples, separately CMB-normalized detector responses, stipulated equal detector/radiometer/DA means, and a common spatial response factored as frequency tensor I24. Frequencies are SI Hz, reference responses are dimensionless per K_CMB, and the inherited E2,E3,B2,B3 signed coordinate order is preserved. Metric/tetrad/ODE conventions are not invoked. W0 is literal; W1 uniformly scales nodes using the official center correction as a sensitivity proxy. Neither branch supplies measured map response or a physical uncertainty envelope.

## Equation and definition audit

| Item | Decision | Evidence |
|---|---|---|
| RJ conversion and normalization | PASS | g/nu^2 enters numerator and CMB denominator; all 201 nodes and signed tails retained. Positive finite denominators and CMB unity verified in stored execution. |
| Detector grouping | PASS | 40 detectors from 20 radiometer files; normalize each detector before averaging; 10 DA and 5 band rows in fixed order. |
| Foreground derivatives | PASS | With D=g(x)-g(xd), E=xg'(x)-xdg'(xd), the t derivative is dust*D and second t derivative dust*(D^2-D-E); independent differentiation and pivot zero controls pass. |
| Stable quotient | PASS | For G=USV^T, Z=U[:,r:], z=Z^T a, rho=norm(z), w=Z(z/rho)/rho. Since Z^T Z=I, w^T a=1 and G^T w=0; Cauchy-Schwarz gives the minimum Euclidean norm. This is the specified quotient without subtractive binary64 projection. |
| Compression and lift | PASS | F12=C F17 and a12=C a17; C^T w12 has the same action in 17 rows. Stored controls and an independent exact-input residual probe pass. |
| Full24 | PASS conditional on factorization | H A=I24 and H B=0 reduce to the saved scalar/vector factors repeated over the complete 24 target and 216 nuisance bases. These are operator controls, not 24 sky measurements. |
| Synthetic boundaries | PASS | Duplicate columns lose rank; injected common-blackbody nuisance exactly absorbs all target coordinates; prescribed rescaling retains rank. |

## Numerical evidence and closed finding

All sealed input hashes match. The independently executed 80/120-digit checker reconstructs the new WMAP integrals without importing producer science code and promotes old Planck floats exactly. Its source change is precisely output-path relocation plus mp.one/mp.zero replaced by mp.mpf(1)/mp.mpf(0). Historical producer assertion and checker AttributeError remain preserved.

Across 24 systems, minimum nuisance singular value is 2.006100347e-6 and minimum augmented singular value 2.566572999e-7, well above the frozen 1e-10 resolved boundary; minimum principal-angle sine is 3.628399453e-5. Maximum retained condition is 1.067851692e6. All branch classifications agree at binary64/80/120 precision. The maximum 80/120 response comparison is 1.980e-81 and producer/120 comparison 6.012e-16.

The checker originally validated its own newly calculated weights rather than directly checking the exported producer weights. Under explicit root authorization, EXPORTED_WEIGHT_PROBE.py closes this coverage gap using Decimal120 arithmetic on exact binary64 stored weights and matrices. It performs no integration, SVD, or weight solve. All 24 producer weights and 12 stored lifts pass: maximum unity residual 1.901e-12, raw nuisance norm 2.662e-12, normalized nuisance norm 2.655e-12, below unchanged 1e-9 gates. Differences from binary64 reported residual values are ordinary summation rounding and do not change any gate. The original checker result remains unchanged.

## Claim-tier implications and residual risks

Safe claim: both stipulated five-band and ten-DA extensions numerically resolve the CMB direction outside this fixed F2 span across all twelve conventions; the conditional tensor quotient has target rank 24. Within-band distinctions are not necessary for that finite result. No exact-rank theorem, method novelty, real-noise benefit, polarized-map equivalence, foreground completeness, family identification, native solver output, or posterior follows.

Maximum Euclidean weight norm is 7955.991019: small nominal residuals do not establish useful noise or response stability. Norm bounds such as abs(w^T delta_y)<=norm(w)*norm(delta_y) require actual perturbation bounds before interpretation. Higher foreground moments, unknown response, noncommon spatial response, and a free common-blackbody contaminant can invalidate separation. The unused checker confounding branch was not numerically exercised by this all-quotient candidate and receives no separate qualification.

x and observed quotient tensor remain NOT_MEASURED; physical F NOT_EVALUABLE; Pi NOT_CALIBRATED; Q NOT_EVALUATED; G_F NOT_APPLICABLE. Actual polarized maps, joint noise/calibration/systematic covariance, common component operators, and physical foreground/remainder qualification remain missing as specified by the contract.

## Fatal blockers and next action

No unresolved blocker remains for this finite conditional component. Actual-sky and original acceptance blockers remain unchanged. Root may consume this review under the existing packet and request the next dependency-safe executable checkpoint; this review does not modify the canonical 42-node acceptances. No additional numerical execution is requested.

## Review scope and resources

Review was read-only outside this new review directory; no repository/Git/STATE mutation, new integration/SVD, producer/checker rerun, native solver, ODE, CAS4-axis execution, or subagent occurred. Cached official source documentation was inspected; no external fetch was needed. A targeted memory search supplied no task-specific evidence and was not used for the decision. Requested runtime gpt-6-astra/xhigh; observed runtime UNKNOWN. The full authorized 20-second command envelope is charged conservatively by root across the existing seven banks, including reads, the tiny arithmetic probe, and closeout. This is not a measured 20-second scientific run.
