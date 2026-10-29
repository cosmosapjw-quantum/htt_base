# R37-02 independent candidate review

Decision: **HOLD for one bounded targeted scientific repair**. No product is qualified by this review.

Candidate: `sha256:0ccd0c62ce9d76420258fc96f0bb164931100d7a8a138d293617ee8c85e1e73d`. Packet: `d2d26dac023854c2177f17c8a408484f7236d425d92655d63bb3c231b4a107c2`. Reviewer: `/root/rc_d2d26dac023854c2`. Requested Astra/xhigh; observed model/effort UNKNOWN. The reviewer is distinct from the recorded sole author and made no repository, STATE or Git writes.

## Blocking findings

**R37-02-F1 (P1) — Restore the source endpoint-difference estimand.** `docs/research_program/observational_publication_20261015/CONVERGENCE_20261028/products/R37-02-KINEMATICS/REPORT_DELTA.md:15`

The report identifies k B_o-dot B_o, but the frozen R36 contract defines A=k q-s with q=(B_o-B_s)/T_ref, s=dot B_o and k=2cT_ref/D. B is dimensionless; q,s,A share rate units. Dropping B_s and T_ref changes the physical estimand although the numerical matrix [kI,-I] retains rank five. The candidate labels must be bound to q,s, not an unnormalized observer endpoint. A weak endpoint witness with B_o=dot B_o=0, B_s=-1e-4 T, c=T_ref=1,D=2 gives A=1e-4 T while the reported expression gives zero.

Fix: Name and define q,s,k and A consistently in JSON/CSV/prose, preserve delta s=k delta q and distinguish the additional common-endpoint nullspace if B_o and B_s are separately introduced. No new depth moments.

**R37-02-F2 (P1) — Propagate a declared physical remainder norm rather than multiplying two rate scales.** `docs/research_program/observational_publication_20261015/CONVERGENCE_20261028/products/R37-02-KINEMATICS/kinematic_image.py:134`

The source Fisher eigenvalues have units (uas/year)^-2. The plotted r/sqrt(lambda(F)) is valid when r is a dimensionless whitened-data residual radius; the candidate labels r as a physical PM rate and calls the output an identified-combination radius. That gives squared-rate dimensions and fails unit equivariance. At r=1 uas/year it returns 0.6405874815; converting the same inputs to mas/year produces 6.405874815e-7 rather than the converted 6.405874815e-4. No response or norm was supplied that repairs this scaling.

Fix: Declare an assumed STF5 coefficient-level physical remainder e in A with Frobenius norm <=r in uas/year and propagate it through the identified quotient. Keep statistical whitening distinct. For the saved Gaussian confidence ellipsoid use directional support sqrt(q95*v^T F^-1 v)+r*||v||, centred on saved A_hat; equivalently present the deterministic remainder-only shift r separately. Preserve unbounded null fibres. Retaining r/sqrt(lambda) requires relabeling that auxiliary calculation as a dimensionless whitened residual and cannot replace the required physical-remainder image.

**R37-02-F3 (P2) — Do not classify representable nonzero S as exact zero after norm underflow.** `docs/research_program/observational_publication_20261015/CONVERGENCE_20261028/products/R37-02-KINEMATICS/REPORT_DELTA.md:21`

The candidate repeats that arbitrarily small nonzero S retains the inverse, but the inherited joint_test branches on np.linalg.norm(S)==0 before its scaling fix. For 1e-200*S_saved all nine entries are nonzero; the norm underflows and returns S_ZERO_DIRECT_MEMBERSHIP with inverse_d null, while a scale-safe inverse is finite with maximum component 1.327797572e198. The existing 1e-8 control passes and does not test this failure.

Fix: Within the new owned consumer, distinguish exact zero using maxabs or elementwise zero and use a scaled inverse/decomposition for representable nonzero S; explicitly reject nonrepresentable inverse outputs. Do not alter the frozen R36 source. Alternatively a precisely declared numerical domain with explicit rejection outside it must replace the arbitrary-small implementation claim; silently returning the exact-zero branch is forbidden.

**R37-02-F4 (P3) — Distinguish seven ambient octupole coordinates from four perpendicular degrees of freedom.** `docs/research_program/observational_publication_20261015/CONVERGENCE_20261028/products/R37-02-KINEMATICS/REPORT_DELTA.md:19`

At fixed nonzero S the lift is 7x3 of rank three, so its orthogonal complement has dimension four. Calling the perpendicular residual seven-dimensional is misleading; it is a seven-component vector constrained to a four-dimensional subspace.

Fix: Use seven-component residual with a four-dimensional perpendicular subspace for nonzero S; all seven are perpendicular at S=0.

**R37-02-F5 (P3) — Point trial-count provenance to the JSON that actually retains it.** `docs/research_program/observational_publication_20261015/CONVERGENCE_20261028/products/R37-02-KINEMATICS/REPORT_DELTA.md:9`

The report says exact trial counts are retained in information_comparison.csv, whose only columns are method, coverage95, MCSE, power_at_2p5. Counts, power MCSE and binomial intervals are retained in the JSON instead.

Fix: Correct the source pointer or include the claimed columns; no MC rerun.

## Matched numerical and claim checks

- Seven assignment input SHA256s, five consumed-source hashes, the exact candidate manifest and all 16 artifact hashes/sizes match.
- Gaia free-bin slope/covariance agrees with direct nuisance Schur-complement GLS; 24-to-18 loses all six free-bin slopes. The constrained 18D law is explicitly a different estimand; g/g2 union rank is 12 and nine deterministic vectors preserve profiled LR to 2.8e-16. Observed LR agrees with independent normal equations to 5.1e-11.
- Stored matched Gaussian MC rates are reused without new draws. Separate-bin nominal covariance is a misspecified control, sandwich is the corrected comparator; correct tensor/GLS and scalar energy omnibus information are not exceeded. Exact scalar noncentral-chi-square powers match to 2.3e-16.
- Saved E2 information and [kI,-I] maps have rank five with five null directions at all five supplied k values. Free E2 nuisance remains rank zero. Numerical rank preservation does not fix the incorrect physical labels or physical remainder units.
- Optical full 10x10 covariance and residual pushforward match; the 95% chi-square10 radius is explicitly a newly stipulated Gaussian control. One shared budget is 0.0018721604870877494, direct uncertainty appears once in the profiled ball, and an independent Lagrange-multiplier solution matches the profile residual within 1.8e-12. The outer-product marginal balls are conservative projections of the same joint event, not an exact covariance-optimal joint confidence image.
- Fixed-Q contraction Gram identity agrees to 3.4e-16 and the ambient STF3 sign boundary is attained at 0.5773502691896255; initial chirality determinant is nonzero and boundary determinant is approximately -2.5e-18. This reuses the fixed simple-Q scope; no joint-Q, fixed-norm-O or new four-axis CAS admission.
- Four vector PDFs render and were visually inspected. Their plotted values agree with JSON/CSV; the PM axis/formula defect is visible in the rendered physical-region panel.
- The existing focused pytest suite passes: 3 passed in 1.15s. It omits the falsified parameter, unit and underflow controls.
- No invented E1/B1-E2 cross-law, common-congruence detection, physical vorticity claim, native solver claim, or original42 promotion found; the erroneous PM estimand remains a blocking physical interpretation defect.

## Receipt and runtime provenance

The recorded RAW_RECEIPT is restored exactly to `88aea924ac224d5f1f0fe2290042c7ebc9939b78cbb6338d1bba222170d5d46f`. The separately retained corrected receipt is `7ed3fe5474c749da2d919973537a1fc38938d778d7530c44fb002d6aa6d30e83`. The two differ only in timestamp, environment and the supersedes-receipt field; candidate identity is unchanged. Current `.venv/bin/python` reports Python 3.12.3, NumPy 2.5.4, SciPy 1.18.1, Matplotlib 3.11.2, pytest 9.1.1, matching the correction. This is a live review-environment observation, not a recovered contemporaneous producer observation. Requested agent model is not runtime evidence.

The parent reports that the earliest pre-scope-correction receipt (`794032c4...`) and manifest (`d3b6f854...`) were overwritten before controller recording. Their exact bytes are unavailable and their changes cannot be independently compared. This is a real historical exact-replay limitation. They are not current source or admission evidence, and all current frozen sources/candidate artifacts independently match, so this history does not independently block the present candidate. It must stay visible; it does not justify rewriting any accepted receipt or claiming the missing draft was verified.

## Bounded repair

One bounded repair confined to docs/research_program/observational_publication_20261015/CONVERGENCE_20261028/products/R37-02-KINEMATICS/; preserve this failed candidate and receipts before writing a new candidate. (1) Restore the exact R36 physical parameterization A=k q-s, q=(B_o-B_s)/T_ref, s=dot B_o, k=2cT_ref/D, with q and s in the saved rate units. Retain all five null directions delta s=k delta q and the free-E2 rank-zero result; k=0 is the distant fixed-endpoint limit. (2) Freeze an explicitly assumed coefficient-level STF5 Frobenius remainder body ||e||<=r in microarcsec/year, with a=u+e and u=kq-s; this is a conditional sensitivity, never a measured bound. Reuse the saved primary selected_sample_full5_coefficients_uasyr as a_hat, F and the existing 5D chi-square 95% threshold 11.070497693516351. Compute the quotient identified image E95(a_hat,F) plus B5(r), with directional support v^T a_hat +/- [sqrt(q95 v^T F^-1 v)+r||v||]; eigenmode halfwidths are sqrt(q95/lambda_i)+r. Expose the full ten-parameter inverse fibre, retaining its five unbounded null directions. Do not relabel a whitened residual as a physical rate. If retaining the previous r/sqrt(lambda) diagnostic, label its r dimensionless and keep it separate. (3) Add a consumer-local safe optical call/branch or a narrowly declared numerical-domain guard. Exact zero must use maxabs==0 or equivalent, not a squared norm; representable small nonzero inverses use scaled S. Cover S=0, 1e-8*S_saved and 1e-200*S_saved, and explicitly reject nonfinite/unrepresentable inverse arithmetic rather than returning an exact-zero result. Frozen R36 files are read-only. (4) Correct the perpendicular-space dimension and trial-count source pointer; update affected JSON/CSV/prose/figure and candidate manifest consistently. (5) Run targeted tests of microarcsec-to-milliarcsec equivariance, the endpoint-difference witness, unit and zero physical remainder, support attainment/monotonicity, null-fibre invariance, and small-S branch behavior, plus the existing three tests. Reuse saved laws, MC rates and producer outputs; no catalogue fit, new MC, solver/ODE, original42 promotion or upstream source edits. Preserve first failures and the separate environment-correction receipt. Return a new candidate for fresh independent review; this plan does not itself admit it.

No old producers or MC were rerun. No new draws, solver/ODE, source-law merging, publication, STATE or Git mutation were performed. Fixed-Q checks are scoped algebra/numerics and do not replace historical CAS gates. The optical inverse/source interpretation remains conditional; original42 remains unchanged.
