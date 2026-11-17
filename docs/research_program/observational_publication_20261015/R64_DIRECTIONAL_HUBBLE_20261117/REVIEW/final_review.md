# R64 independent final scientific/code review — final closeout

Review date: 2026-11-17 UTC. Reviewer: `/root/r64_final_review`. Requested model/effort: `gpt-6-astra/xhigh`; observed model/effort: `UNKNOWN/UNKNOWN`. Existing native checkout: `/home/cosmosapjw/Dropbox/bianchi/htt_base`; branch `research/r64-directional-hubble-20261117`; inspected HEAD/baseline `33d87dd3e4a787e477327d37ee00b40e790211c9`.

**Final verdict: PASS.** Both LOW wording/display findings are CLOSED after one bounded correction episode; there are no open findings. No mathematical, statistical, or implementation defect requiring a changed fit or test rerun was identified. **Journal submission: NOT_READY_TO_SUBMIT.** This submission status is distinct from acceptance of the completed scoped research integration.

The reviewer performed this one fresh final review, independently read the frozen native artifacts, and inspected byte-identical scratch copies of all ten R64 Python source/test files after observing their native SHA256 values. The reviewer was remote read-only, made no clone/worktree, launched no agents, reran no scientific pipeline/test suite, and added no successor research loop. The only targeted numerical inspection beyond reading existing results was a norm extraction from already-saved V estimates to resolve the concrete tangent-response interpretation question. It did not evaluate a new fit.

## Findings and bounded closeout

### R64-FR-01 — LOW, CLOSED: explicitly bound the physical interpretation of the first-order velocity template

Locations: `REPORT_KO.md` §5; `THEORY.md` equation (10); `TENSOR_LIKELIHOOD.md` observation/physical pullback discussion; corresponding plan/validation scope.

The implemented mean contains `g(z) n.V`, the inherited first-order source-velocity tangent response, but V is free over the full linear parameter space. Some identified augmented J3 solutions have large norms: `log_sky__J3__common_field` gives 5788.052449 km/s and `split_method__J3__method_angular_nuisance` gives 5292.453810 km/s. The largest initial J3 norm, 21168.238488 km/s in `log_mono_galactic`, is instead a gauge-dependent representative of a singular fit and must not be reported as a measured velocity.

At the catalogue minimum z≈0.0100036, the first identified value gives the scale ||V||/(c z_min)≈1.93. That is an upper-bound scale, not an observed radial value at a particular source; it does not prove every source violates perturbativity. It nevertheless makes clear that a small physical response/remainder domain has not been certified by permitting this free template.

The report already says that the H_D/q_D polynomial image excludes the declared nuisance and is not a validated physical PV reconstruction. Add the concrete qualification that no small-response or higher-order velocity-remainder domain was imposed/certified. The subtraction defines a conditional polynomial distance-field image, not a physically validated velocity deboost. This correction does not change the exact stated linear Gaussian experiment, its rank results, its working-law p-values, or its conditional confidence images. No fit, prior, or source cut needs to be introduced during this closeout.

### R64-FR-02 — LOW, CLOSED: identify the illustrative operator on the information-recovery figure

Location: `scripts/r64/summarize_r64_augmented.py`, generated `RESULTS/INFORMATION_RECOVERY.png/.pdf`.

The adequacy panel uses the specific `mono_method` case: `log_mono36 + method32`, compared with `log_mono36`. Its title/legend currently reads generically enough to be mistaken for the behavior of all augmentation operators. This matters because `log_method +24`, J3 has adequacy p=0.01619, while the plotted `mono_method +24` case has p=0.40431. Label the illustrative case directly in the figure and retain the inherited fixed working-covariance qualification. The full report already preserves the other operators, so this is a display clarification, not a result-selection defect or request for another analysis.

**Closure of R64-FR-01:** Native REPORT_KO.md line107, THEORY.md line96, TENSOR_LIKELIHOOD.md line9, RESEARCH_PLAN_KO.md line103 and VALIDATION.md line61 now state the required validity boundary and the distinction between large identified fits and singular representatives. These changed paragraphs were read directly. The physical interpretation is correctly limited without altering the linear experiment.

**Closure of R64-FR-02:** Final generator lines74–75 and the rendered figure explicitly identify `mono_method = log_mono36 + method32` and the inherited working covariance. The final PNG was visually inspected; its legend is clear of the curves and its caption is readable.

Initial finding records remain preserved as `r64_final_review_initial.md/json`. `REVIEW/R9_CORRECTION.json` records one correction episode, no fit reruns and no test reruns. The summary SHA256 remains `1c60c95c6f60e480520ef5045684fb11055c05ddee3c74160e11d801979205c9` before and after the display update. The final figure-generator SHA256 is `1a0424bca6777ae3408a0c946f9a569b0ad901c88a42fbf380c31b60b3c172ae`; final PNG/PDF identities and corrected document hashes are retained in the JSON. This was a narrow closure of the two reported items, not another full review.

## Scientific/code assessment

The sign and units of Hcal=Theta/3+sigma_nn−A.n/c are consistent with sourceward n, physical U.U=−c², and the past-directed affine ray ell=E(−u+n). The Sachs equation, Etherington conversion R=(1+z)D_A, transformed R equation, and linear first-order equation for Y=Hcal² follow with the stated affine normalization and vertex assumptions. The coefficient singularity at an angular-diameter-distance extremum is explicitly retained. The Milne example correctly separates distance-defined H_D/q_D from physical congruence H/q. These are scoped identities and counterexamples, not a physical closure inferred from CF4.

The eta normalization and numerical chart are handled consistently: eta_repo includes ln of the numerical H0, so H_D=E exp(eta_repo)/(1−E chi_hat eta_z) in km/s/Mpc. The observed mean receives O ln(chi_GL64/chi_legacy), while O, C and the inherited response convention remain fixed. The reported maximum source offset 1.62003566e−9 agrees with the saved result. All polynomial derivatives are taken from the stated Legendre source family, not from four plotted window centers or the piecewise-linear reference table.

The source design is genuinely X=O B_source, retains the full signed angular basis, and places the V3 coefficients before 9(J+1) polynomial coefficients. The H_D/q_D rows explicitly zero the V entries while fitting their covariance jointly. The nested null retains V, all constant angular coefficients, and every radial monopole. Degrees of freedom use actual rank differences. The code therefore tests additional radial-angular mean structure, not absence of all anisotropy or physical isotropy.

The augmented covariance selects jointly cached rows and their cross blocks from the pinned L05 cache and adds the jointly propagated white covariance. It does not combine separate L04/L05 caches as independent and does not multiply the cached PV body by g a second time. The whole-stack fingerprint mismatch is reported honestly. Selected original36 mean/covariance parity and original method dipole mean/SD parity support the declared numerical compatibility, not whole-stack byte identity.

Nuisance profiling whitens the complete covariance before taking an orthonormal complement. The optional 24 method-angular directions are separately counted. The inherited GLS implementation preserves scaled/equilibrated rank checks, null directions, and confidence cylinders. Correlated holdout/additional-row predictions use the Schur noise plus parameter-estimation variance and reject nonestimable training predictions. The two targeted augmentation tests specifically compare profile and full joint GLS and preserve a confounded signal component.

The nonlinear interval code computes linear supports from one rank-r joint region, then forms conservative enclosures. It does not assume coordinate independence or silently substitute scalar chi-square cutoffs. Null ingredients, denominator certificate failure, and numerical range errors remain distinct. Equal-redshift identity is treated separately. DOMAIN_NOT_CERTIFIED is correctly not promoted to proof that the exact nonlinear image is unbounded.

The observed result and report agree on initial21 + augmented21 unique fits, 35970 groups, initial J3 rank36/39, augmented J3 rank39/39 including optional nuisance profiling, and no new independent sources/pair sums. The mono_method J2 common p=0.00764188449, +24 p=0.58476525044, and nominal nested LR p=0.00138168617 agree. The illustrative J2 H_D(.08)/H_D(.04) enclosure [0.17340136,7.52099117] and q_D(.08) enclosure [−250.63767,167.66709] agree. The J3 +24 mono_method count 53 finite ratio enclosures /109 domain-uncertified points is preserved as a finite-grid result.

The report distinguishes represented l<=2 calibration invariance from actual l=3 injection leakage; it retains the latter's maximum depth bias≈0.0059235 rather than generalizing the quotient to arbitrary angular calibration. It also preserves the nontrivial source-dependent inadequacy exposed by augmentation and the operator-to-operator variation. Five named views remain functions of one GLS law and do not claim new Fisher information, independent likelihood factors, physical MES limits, or novel general Gaussian inference.

## Reviewed evidence and limitations

Substantively reviewed: `THEORY.md`, `TENSOR_LIKELIHOOD.md`, `REPORT_KO.md`, `RESEARCH_PLAN_KO.md`, `DESIGN.md`, `R8_RESOLUTION_AMENDMENT.md`, `VALIDATION.md`, `RESEARCH_RECORD.json`; historical/literature notes and selected source-register entries; both saved result JSON files, their compact interpretation summary, and selected NPZ carrier arrays; all ten R64 source/test Python files; relevant native R58 fit/interval/cache-reuse code and R54 operator construction.

Existing execution evidence inspected: primary60 and augmentation2 test receipts, symbolic7 Wolfram/8 SymPy zero-difference receipts, observed/augmented execution receipts, metadata/summary repair records, and saved sky72 whitening-stability receipt. The alternative whitening discrepancy is <2.4e−10 marginal standard deviations despite condition number≈3.65e7. These are reviewed existing executions, not newly rerun tests, and do not amount to empirical covariance or legacy four-axis CAS admission.

Primary web spot checks independently reopened Heinesen 2010.06534v2 equations11/14/16, Clarkson–Bassett–Lu 0712.3457v2 equations1–3, and Kalbouneh 2510.02510v2. A fresh generic fetch of Vicente2607.07821 was unavailable; its source assessment here uses the saved prior primary-text record. The reviewer did not independently re-read every source or every historical PR. No fresh external novelty theorem is claimed.

Remaining scientific limitations are appropriately retained: unqualified shared calibration/group/selection law; a finite polynomial and first-order velocity-template decomposition; broad derivative uncertainty and incomplete positive-domain certificates; no validated optical/congruence pullback; no independent-tracer confirmation; and no matched end-to-end competitor reproduction. These restrict publication/physical interpretation but do not by themselves invalidate this finite conditional integration. The planned additive DAG finalization and publication have not yet occurred and are outside this scientific verdict.
