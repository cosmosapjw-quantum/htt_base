# Independent review of the frozen Gaia release-tag association

Decision: **HOLD / blocker; frozen acceptance not met.** The saved conditional calculation passes the independent numerical checks performed here. Two prescribed implementation controls were not performed before the observed proper-motion fits. Retrospective validation cannot establish the missing historical pre-PM condition.

Reviewer: `/root/rc_429068ee8ebbdff0`; requested `gpt-6-astra/xhigh`, observed runtime `UNKNOWN`. This reviewer did not author the candidate, received no prior result-review verdict, spawned no children, and wrote only this external review directory. The prospective method/criteria documents were treated as frozen task inputs, not as an earlier verdict on this candidate. Repository skills and harness labels supply no approval authority. Historical memory/outcome searches were not used, to preserve the bounded blind context.

Packet: `429068ee8ebbdff0324a8fbc31f33d0d87ce35431c8350fc428a8d46876e49f2`.
Task: `R25-GAIA-RELEASE-TAG-ASSOCIATION`.
Input: `sha256:00209480018bcb19f29c3c22a2d847c26560bcf950045978f10579967314e39f`.
Candidate MANIFEST: `sha256:3d2e96774c28cb5c3aa4d00757e022d61d1d696f50ff50e1b4dcdd31fc181793`.
Spec identity: `56a29a0ed26cdad3ebb819c6fe255acff92f384f1d5d51fff0da768566206423`.
ACK: `/mnt/extdrive/workdir/htt_open_data/r25_root_space_recovery/receipts/GAIA_TAG_REVIEW_ACTUAL_ACK.json`, status `ACTUAL_NATIVE_REVIEW_ACK`, same packet/task/reviewer. Numerical validation began after the root's ACK grant.

## Blocking finding: incomplete pre-PM controls

The input's `operative_independent_criteria_verbatim`, section “One deterministic fixture family and tolerances”, requires converting the full fixture to mas/year and back without changing the recovered physical contrast or covariance. It also requires the stated 24-direction sphere quadrature, with z weights `(5/18,4/9,5/18)` and azimuth weights `1/8`, whenever the optional sphere RMS is emitted. Its execution transition requires shared domain/toy checks before proper-motion access. These requirements were frozen before the fits; they are not new reviewer preferences.

At candidate `execute.py:206-207`, the only unit test sets `Fmas=F/1000`, `Cmas=C/1e6`, `Ymas=Y/1000`, then multiplies them back and checks array equality within rounding. It never runs the unit-converted estimator or tests its recovered coefficients/covariance. This check would also pass for an estimator with a missing covariance unit factor because that estimator is not called.

The entire `toys()` function (`execute.py:154-226`) has no sphere quadrature or weighted spherical integral. Nevertheless, `execute.py:301-303` calculates and emits the RMS summary in both observed products. `TOY_CONTROLS.json` has no corresponding quadrature metric.

At `execute.py:280-281`, `PRE_PM_FROZEN.json` is written with `shared_controls=PASS`. At `execute.py:287`, proper motions are then opened, and `execute.py:295-297` consumes the two observed solves. The shared PASS therefore overstates completion of the frozen controls. The raw receipt records two consumed observed attempts, which must remain two.

**Exact missing historical evidence:** an immutable pre-PM execution record, bound to this source/input identity, showing (1) recovered physical coefficients and covariance invariant through the unit conversion at the frozen tolerances, and (2) the optional RMS matching the prescribed sphere quadrature at the frozen tolerance, executed before the two recorded solve starts. Neither the sealed code nor its sealed controls contain these computations. No present rerun can manufacture that historical evidence.

The reviewer independently performed both missing controls now; they pass. This is retrospective numerical evidence only. Do not overwrite the historical controls, relabel the late tests pre-PM, weaken the original criterion, rerun an observed fit, reset the task/budget, or mark the frozen task accepted. A separately defined conditional certification of already saved operators may be researched by the controller while retaining this original HOLD.

## Independently verified numerical components

`validate.py` ran once. `ARITHMETIC_FIRST.json` retains 133 entries, with no failing check or script exception. It used one scientific process with every observed BLAS pool at one thread; process highwater was 588,845,056 bytes. Numerical execution including imports, identity checks and all tests took 9.785289878025651 seconds. No `proper_motion` NPZ member was accessed; no observed solve, production replay, catalogue query, bootstrap, empirical-null draw, ODE/native solver or ultra use occurred.

The reviewer verified every sealed source/candidate hash and every MANIFEST file size/hash. All 4,756 canonical integer IDs match the frozen astrometric source order. Independent raw VOTable parsing agrees with the accepted literal AGN and wire-null values and host fields. Counts remain AGN 3,216 versus wire null 1,540; host 3/5/6/null strata remain unmerged. Null is an absent released label, not an astrophysical non-AGN class. Host flags 1/2 remain absent.

An independently constructed analytic ICRS spin design and Cartesian STF/tangent design verify all three glide, five electric quadrupole and five magnetic quadrupole coordinates, including opposite cross-product conventions for spin and B2. Every saved 32-coordinate M0 and 80-coordinate M1 joint map satisfies its full design identity. Maximum absolute errors are 6.32e-16 and 1.12e-15; corresponding all-13 target map errors are below 2.67e-15. The metadata correction in `COEFFICIENT_ORDER.json` correctly describes M1's four 16-coordinate host baselines followed by one shared spin and one shared FULL13 tag contrast.

Both pre-PM support spectra, scales, residual floors, all prescribed rank thresholds, source leverage and octant shares agree with independently formed designs. Augmented condition numbers are 8.2272 and 9.2499. Minimum scaled residual singular values are 0.31387 and 0.30836, well above the frozen 1e-8 floor. This establishes numerical resolvability for these fixed designs; it does not establish physical identifiability or complete sky overlap. Flag 5 has only 36 tagged and 7 null sources; no arbitrary quota was imposed or stratum removed.

Full identifiable joint covariance, all FULL13 cross terms, the physical/whitened maps, both signed STF tensors, and coefficient ordering agree across saved products. The computed same-data cross-covariance agrees with `V01=V00` at relative 1.67e-15; the direct `(T1-T0)(T1-T0)^T` difference covariance and its equivalent joint-covariance expression agree. The estimates cannot be treated as independent replications. Observed coefficients were inspected for saved-product/order consistency; they were not re-estimated from raw proper motions.

The independent 192-source deterministic fixture checks every M0/M1 coefficient individually plus the specified composite. It compares the candidate's residualized-SVD target map with a separately formed full-model QR map and triangular-solve joint covariance. It covers common and differential spins, all FULL13 signs, exact duplicate nuisance removal, zero exposure, within-host aliasing, a 13-direction near-alias example, tangent rotation, unit-converted coefficient and full/target covariance recovery, nonzero cross-covariance, difference covariance, and all 13 sphere-coordinate probes plus the composite. No tolerance changed. Relative unit-converted covariance errors are at most 3.02e-15; the sphere squared-RMS discrepancy is 3.34e-16 against a ceiling of 1e-11.

The descriptive quadratics and RMS values also agree with saved-coefficient arithmetic. This agreement is not a null test or physical coverage assessment.

## Statistical/source-law review and limits

For fixed design and valid working second moments C0, the target map gives `Cov(delta_hat)=T T^T`; Gaussianity additionally gives a Gaussian sampling law. For the actual catalogue, the covariance is `A C_true A^T`, and selected-sample distributional coverage additionally requires a justified selection law. Neither follows from the marginal 2-by-2 blocks, full rank, toy recovery, or retained hashes. Unknown cross-source blocks cannot be repaired by a scalar RSS rescaling.

The retained sample was selected through frame processing using astrometric information. The Gaia-CRF3 source paper describes astrometric filtering and frame-rotator use; the result is an in-sample selected-source diagnostic, not an independent reference-frame physics test. [Gaia-CRF3 paper](https://arxiv.org/html/2204.12574v2)

General variability classification and SOS-AGN are different processing products. The latter applies parallax/proper-motion, environment and scan-related filters; it must not be represented as a PM-independent validation channel, nor may all general AGN tags be assumed to have passed those SOS filters. [Gaia DR3 extragalactic content](https://arxiv.org/html/2206.05681v1), [Gaia variable AGN catalogue](https://arxiv.org/html/2207.06849v1)

The ESA general-classification documentation and AIP QSO-table page timed out in this review. Those attempts are recorded as unavailable, not as successful live verification. The decisive source-law caveats are independently supported by the primary papers above and the frozen source-selection code. No literature value was used to alter the frozen numerical thresholds.

The released tag can track source properties, pipeline selection or angular/model misspecification. M1 assumes a common tag contrast across its four processing strata and is a distinct weighted projection under heterogeneity. It does not isolate a causal photocentre mechanism. Signed E2/B2 coefficient tensors are observable field coordinates; no spacetime tensor, causal transfer, global/local tilt or Bianchi-family claim follows. The fixed unit `u0=1 microarcsecond/year` makes x dimensionless but supplies no physical MES anchor. Q remains NOT_EVALUABLE, F UNBOUND_NOT_EXECUTED, Pi conditional C0 Gaussian only with physical coverage NOT_CALIBRATED, and G_F DEPTH_UNAVAILABLE.

Original 17/42, alternate 18/42, historical 48, consumed one-use/ultra histories and R9 UNKNOWN remain unchanged. No product is qualified by this blocked review. The author proposed no product names in its `qualified_products` list; this review adds none.

The exact final arithmetic and packaging accounting, findings, controller result and raw evidence bindings are in `RAW_RECEIPT.json` and `RESULT.json`. The remaining executable checkpoint is controller research on whether an explicitly different, retrospective saved-operator certification is useful, while preserving this frozen task's HOLD and continuing independent ready branches. It is not another observed fit.
