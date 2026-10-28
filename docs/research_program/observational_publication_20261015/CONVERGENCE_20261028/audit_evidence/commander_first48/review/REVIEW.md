# Independent review of fixed Commander first48 conditional location

## Findings first

1. **MEDIUM, not blocking this frozen result — exact zero displacement falsely abstains.** `compute.py:163-170` evaluates the normalized residual as 0/0 when `mu0` equals the sample mean. A positive-definite centered sample then returns `NOT_EVALUABLE`, although T2=0 is well-defined. The current result has nonzero mean and finite residual, so it is unaffected. Before general reuse, handle finite exact-zero displacement explicitly and test it. The minimal witness is static; no rerun was performed.
2. **LOW, not blocking this frozen result — positive signed-m fixture is not independent.** `test_compute.py:19-34` reuses the same conversion for its positive comparison. Negative reality witnesses and norm checks are present, but a hand-built complex row with independently specified coordinate signs/order is absent. Static code inspection matches the contract. Add the stronger fixture at the next authorized change; do not claim it already ran.

## Scoped verdict

**SCOPED_PASS_CONDITIONAL_EXPLORATORY_RESULT** for the exact sealed first48 candidate. This admits the auxiliary descriptive ensemble mean/full sample covariance and the nominal Hotelling construction under its explicitly declared working law. It is not a reusable-library acceptance or publication decision. Original R36-07 remains **UNCHANGED_HOLD** and all original 42 acceptances remain **UNCHANGED**. Requested reviewer: gpt-6-astra/xhigh; observed model/effort: **UNKNOWN / NOT_INDEPENDENTLY_OBSERVED**.

The reviewer neither framed nor implemented this candidate and read no prior independent verdict. No input or candidate was changed; no candidate computation, scientific reanalysis, FITS load, spin transform or 2000-batch repetition was performed. Only this unique review directory was written. Git/state and the source acquisition were untouched. Stored successful/failed execution evidence was inspected, not represented as a fresh test execution.

## Source, selection and full-carrier audit

All 28 artifact/source/RETURN hash and available size checks pass. All 48 JSON rows match their frozen hashes, genealogy, map identity declarations and mask; IDs are exactly 300 through 347 without replacements. This verifies the supplied small-row boundary. The review did not independently re-read upstream FITS bytes or revalidate their producer; map-level provenance remains inherited from the frozen rows.

The source law is delivered Commander FULL005a after the fixed GALACTIC/COSMO, lifted binary NS16 Lollipop mask and native NS2048 spin-2 ellmax4 extraction. The MC conversion of 1e-6 to K_CMB is enforced explicitly; the shared manifest's observed conversion 1.0 is not accidentally applied to MC inputs. No beam correction, noise subtraction or transfer cancellation is present.

The basis keeps all 2*(5+7+9)=42 real degrees of freedom: m=0 once, then sqrt(2) Re and negative sqrt(2) Im for positive m, with negative m used only for reality validation. Full signs/phases are retained. RESULT stores 42 labels/means, the complete 42x42 covariance and 42 eigenvalues; CSV has exactly matching labels and means. This completeness is limited to the chosen processed-map band-limited carrier, not the original physical nine-moment tensor, a sky inverse response, or all multipoles.

The first48 timing follows partial exposure and availability. Its ID rule is fixed in the supplied contract, but no independent proof of historical outcome-blind stopping exists. The candidate correctly claims neither preregistration nor selective coverage. Extending to 100 is a different, dependent question and cannot silently replace this result.

## Statistical and numerical audit

For iid N_42(mu,Sigma) with positive-definite Sigma, n=48, S=C^T C/47 and T2=48*(ybar-mu)^T S^-1*(ybar-mu), the pivot is (48-42)T2/[42*47] ~ F(42,6). The code uses this finite-sample factor, not an asymptotic chi-square. The one-sample scaling agrees with [NIST](https://www.itl.nist.gov/div898/handbook/pmc/section5/pmc543.htm).

The normal/Wishart result requires iid multivariate normal rows and a fixed sampling rule. The paper's nonlinear reprocessing and fixed observation-derived mixing matrices support the conditioning description, but establish neither output Gaussianity nor observed/MC exchangeability. [Planck NPIPE, Sections 5 and 7.7](https://doi.org/10.1051/0004-6361/202038073). Current DOI/A&A fetch returned 403; primary-source search excerpts and the saved paper HTML were inspected. Skewness, kurtosis and leave-one-out summaries are descriptive; no pass of those diagnostics proves the working law.

Reported rank is 42. The smallest centered singular value 0.004235447770197365 microK exceeds the frozen cutoff 6.974853710255073e-13 by many orders of magnitude. All covariance eigenvalues are positive; condition number 58283.90902009615 is below 1e10. Cholesky normalized residual is 8.795923874997615e-17; full-SVD T2 difference is 6.048139766789973e-10, below the prescribed 1e-8*(1+abs(T2)) tolerance. No pseudoinverse, truncated modes, shrinkage or dimensional reduction is used. These checks establish arithmetic admissibility of this candidate, not a well-estimated population covariance at n-p=6.

Stored results are T2=3877.4728610810052, c=1240.1317051427611, F0=11.7856317965988 and nominal Gaussian tail 0.0025424677607337525. They are exploratory model contrasts, not foreground-detection or physical p-values. Mean norm is 0.07020268582105542 microK_CMB; the conservative norm interval is [0,0.8283228083190148] microK_CMB.

The ellipsoid projection half-width sqrt(c*S_jj/n) and enclosing norm radius sqrt(c*lambda_max(S)/n) are correct. Their coverage is at least the nominal ellipsoid coverage under the working model; neither is an exact 95% marginal interval. Zero being excluded by the joint ellipsoid is consistent with every coordinate interval and the loose norm interval containing zero. Do not reinterpret the conservative lower zero as joint compatibility with zero.

Stored tests report 5/5 pass, including actual-row permutation/unit/orthogonal controls, scalar finite-n and deliberate missing-n/ddof witnesses, singular abstention, and attribution counterexample. One prescribed Gaussian batch reports 1886/2000=0.943 within [0.925,0.975]. This tests Gaussian implementation behavior, not the real pipeline law. Initial syntax and manifest-key failures and later file-close warning history remain sealed. Both compute failures occur before the coverage loop; no evidence of seed selection or successful-batch repetition was found.

## Physical and claim audit

The mean is the total delivered-output location conditional on fixed foreground, fitted mixing and processing settings. The decomposition mu=f+b is not identifiable: replacing (f,b) by (f+h,b-h) leaves all Y unchanged, and arbitrarily large h makes foreground norm unbounded without an independently justified bound on b. The stored two-attribution witness and UNKNOWN bias bound respect this limit. No physical nine-moment radius follows from the 42-vector norm.

The observed contrast was omitted because its extra identical-independent conditional law is not established. x, F, Pi, Q and G_F remain UNKNOWN. No posterior/evidence, native solver, Bianchi family or physical detection claim is admitted. The figure was visually inspected: all 42 means/projections and eigenvalues are visible; the embedded caption states after-exposure Gaussian-working-law scope, six denominator degrees of freedom and absent foreground attribution. Companion caption metadata preserves owner, transfer, covariance, null and forbidden-use information.

## Next action and stopping rule

The controller may use this exact sealed result as the auxiliary conditional diagnostic while retaining its assumptions and all original holds. No repeat first48 or synthetic batch is required for this decision. F1/F2 should be repaired in a separate bounded code change before general reuse, without rewriting frozen inputs or historical failures. The scientific next step remains an independent externally justified bias/response/truth input or already-authorized separate campaign work; increasing process evidence cannot identify foreground attribution.

See REVIEW.json for exact candidate hashes and IDENTITY_AND_SAVED_EVIDENCE_CHECKS.json for per-file/row checks. No ledger or acceptance state was edited.
