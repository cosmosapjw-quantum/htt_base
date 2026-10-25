# Independent review of the frozen Gaia source quotient certificate

**Disposition: scoped conditional acceptance; no blocking defect found.** The exact finite archived source Gaussian/C0 quotient, complete full13/E1 images, reported statistic enclosures, conditional Delta tail upper bound and arbitrary projected-mean ball meet this packet's acceptance. This is not physical coverage or significance, an original-campaign acceptance, or four-axis/native CAS admission. `qualified_products=[]`: the execution proposed no controller product tags.

## Binding and independence

Reviewer actual agent ID: `/root/rc_656d1d9504919fad`. Requested profile: `gpt-6-astra/xhigh`; observed runtime: `UNKNOWN`. The reviewer did not author the candidate and received no prior scientific reviewer verdict. No child agents were used. The only written directory is `/mnt/extdrive/workdir/htt_open_data/r26_gaia_quotient_blind_review/`.

- Task: `R25-GAIA-SOURCE-QUOTIENT-CERTIFICATE`, review attempt 2.
- Review packet: `656d1d9504919fad405bdf6cc8108da89ab3600edbec728fec7db56ca32ffe80`.
- Frozen input: `sha256:4df217b0798bbb247523dae173fc4026b966a6208496929477085305a44653ba`.
- Frozen task spec: `8e9913879a5e3f730b846627e384c5fe5edd52eeb7747d33c8e72e99dbc333f8`.
- Candidate manifest: `sha256:55e9d6bd8d9ca98d5736baf9327a51d00d8c01dac14fa8de63a26cb489022404`.
- Source array: `sha256:d391a5c49b9205229717d1bc9c900e180be4bea8440023bb52b2517352e8ffe5`.

The root's `QUOTIENT_REVIEW_ACTUAL_ACK.json`, timestamp `2026-10-23T20:45:42.175362+00:00`, was received before any numerical validation. Static contract/source inspection preceded ACK. All 30 packet source/candidate seals matched. Full source/tensor carriers remain present; no original fit, pair traversal, acquisition, geometry reconstruction, W reselection, production-main execution, or candidate rewrite occurred. Repository-local audit skills were checklists, not acceptance authority. No historical review was used to decide this result.

## Controlling assumptions and convention

All frozen binary64 source values are exact dyadics. Source-major tangent ordering and the 13 columns (first three g/E1, five E2 STF, five B2 STF) are preserved. H has shape 117 by 9512; W is the fixed archived 88 by 117 covariance-only projection; B has three source-spin columns. The source law is the explicitly conditional model Y~N(X beta+B omega,C0), C0=blockdiag(saved C_i), with unrestricted beta and omega. Euclidean source coordinates define the quotient metric. The fixed-W reference is dimensionless after covariance scaling; no physical optimal-weighting convention is inferred.

The archived W construction depends on covariance, not the observed response, as shown in the original `compute.py:131-146`. Selection of the archived sources remains outcome-dependent and has no supplied distributional correction. The finite working-law result therefore does not become selection-adjusted physical inference.

## Mathematical and numerical review

For exact G=B^T B>0, P_B=B G^-1 B^T is symmetric and idempotent. Q_B=I-P_B annihilates B exactly. Hence H_star=H Q_B removes every spin omega, and each row is the unique Euclidean projection onto ker(B^T); this establishes the Frobenius-nearest assertion. No floating near-zero HB residual is used for that proof. Independent exact rational evaluation of all nine spin-Gram entries and its three leading principal minors establishes positivity. The saved spin Gram and inverse intervals contain the exact/independently bounded objects.

Every one of the 4,756 source covariance blocks was exactly symmetric with positive first diagonal and determinant. The independent minimum determinant equals the recorded exact fraction 7509847833313123675422965841791/19342813113834066795298816. Thus C0 is SPD without silently symmetrizing it.

The direct F_star=WH-(WHB)G^-1 B^T implementation is algebraically identical to WH_star. The block contraction keeps both covariance off-diagonal orientations and all 88 by 88 source-induced cross-bin/component covariance entries. This does not model unknown inter-source covariance.

The interval product proof uses a gamma_(2n) absolute dot error, with n<=9512, plus the input-radius terms |A_c|R_B+R_A|B_c|+R_A R_B. Computed absolute-product sums are corrected by 1/(1-gamma). The fixed 1+1e-8 inflation exceeds the nonnegative rounding corrections; an independent exact-rational inequality verifies that it dominates even 32 worst-length gamma factors. Actual reported nonzero operands are far above the 1e-150 floor, so their products and this candidate's bound arithmetic stay away from underflow. The frozen code checks finiteness and rejects a failed normal-product premise. Exact-zero preservation fixes the retained first control failure without suppressing a nonzero small operand.

The inverse proof is valid: if E=I-A R0 and ||E||_infinity=e<1, then A is invertible and ||A^-1-R0||_infinity <= ||R0||_infinity e/(1-e). This is an enclosure proof, not evidence from a small unconstrained floating residual. The independent reviewer forms residual entries and sums with exact Fractions, using binary64 inverses only as approximate preconditioners. For the saved full13 and E1 Gram balls, independent residual bounds are approximately 1.8464477241e-9 and 1.4770848556e-10. Each Gram interval contains the exact interval product from the saved A_star ball. Exact Gram PSD plus certified invertibility gives complete ranks 13 and 3, not thresholded ranks. Their nested images yield the rank-10 orthogonal projector Q=P_full-P_E1.

Exact rational interval propagation of z, A and the verified inverse balls produces:

- T_full in approximately [75.0786221609645, 75.0786237336359], inside the candidate's [75.07862216095263, 75.07862373364777].
- T_E1 in approximately [87.0026022174787, 87.00260235925941], inside the candidate's [87.00260221747669, 87.00260235926143].
- Delta in approximately [11.923978483842808, 11.923980198294917], inside the candidate's [11.923978483828927, 11.923980198308788].

Displayed decimals here summarize exact-rational predicates in the raw checks; they are not replacement interval endpoints. The exact maximum row sum of the saved S_star interval's distance from I is approximately 1.3599699816e-9, below the stated delta=1.3599702443948884e-9<1. Exact symmetry of S_star follows from its construction; it need not be inferred from rounded symmetry of its center. Thus (1-delta)I <= S_star <= (1+delta)I. In particular the projected covariance is nonsingular, W has row rank 88, and the 29-dimensional kernel of W in R117 remains unconstrained rather than physically absent.

Under the matching E1 mean null, Q removes the mean. The eigenvalues of the covariance restricted to range(Q) lie in [1-delta,1+delta], giving Delta <=st (1+delta)chi-square_10 by coupling independent squared Gaussian coordinates. This argument does not give independence of the residuals or an F-ratio law. Under an arbitrary projected mean, the analogous norm bound uses dimension 88 and requires no image-rank premise.

Independent exact Fraction sums confirm that the finite positive exponential Taylor sum gives a lower bound on exp(x), hence polynomial/sum gives a rigorous chi-square survival upper bound. The candidate's upward decimal 0.29017657168415 dominates the rational bound at L_Delta/(1+delta). At q=120 the df88 rational bound is approximately 0.013266378863342799 < 1/20, so q is a conservative 95% quantile upper bound. No high-precision special-function evaluation is substituted for proof. No df75/85 tail is issued.

The displayed center exactly matches the saved z_star center. Independent exact squared inequalities verify eta^2 >= sum(z_radius_i^2) and (radius-eta)^2 >= (1+delta)*120, with radius>eta. Therefore radius 10.954451326468204 is outward for the claimed conditional mean ball.

## Rounded old-covariance comparison: concern resolved on this frozen candidate

`certify.py:238` constructs `bm((Cd+Cd.T)/2)` after binary64 rounding. This operation alone does not establish an exact interval for sym(Cd). The independent audit found 5,970 inexact midpoint entries; the largest midpoint rounding error is 8.881784197001252e-16, including zero-based entry (106,93). This was investigated as a potential defect rather than assumed harmless.

The reviewer then computed the entire 88 by 88 W sym(Cd) W^T exactly using integer-scaled dyadic matrix contractions, without calling author code. For every one of 7,744 entries, the exact shifted S_star interval lies inside the saved mandatory correction interval. The largest required/stored radius ratio is 0.9991017008089714. Thus the saved correction is rigorous for this specific frozen candidate despite the omitted intermediary rounding term. This independent inclusion evidence is part of the acceptance; it does not establish a generic guarantee for future inputs passed through that rounded construction.

All other mandatory corrections were checked independently: A_star-WD and z_star-Wd by exact dyadic contractions, and z_star-WHy by exact interval propagation through the saved F enclosure. Worst radius ratios are respectively 0.9997484612229015, 0.999959162392415, and 0.8929925192373028. Exact sampled F, A_star and z_star source contractions passed. These samples are falsifiers, not a claim to have recomputed every production contraction; the full propagation is justified by the reviewed algorithm, frozen successful execution, and stated arithmetic model.

## Controls, backend premises, and limitations

Independent exact fixtures cover spin contamination removal, nonuniform covariance propagation (variance 47/4), rank loss with a noncompact coefficient fiber, a small strictly positive model mode, and a covariance-inflation bound that must not be admitted. The author program catches a failed inverse or failed bound as HOLD; it does not silently delete a mode. The archived first normal-product control failure remains intact and charged. No reviewer arithmetic command failed.

The candidate records NumPy/OpenBLAS and IEEE binary64 round-to-nearest assumptions. The reviewer observed fegetround=0, an executed gradual-underflow multiplication, and one OS thread. The candidate's gamma proof remains conditional on its declared CPU binary64 dot-operation model (ordinary multiplication/addition or FMA with at most the stated operation bound). Configuration and these probes are not formal hardware or BLAS-kernel verification, and no four-axis CAS or machine-verified arithmetic claim is made. Exact downstream predicate checks reduce dependence on floating bound assembly but do not replace that explicit backend premise for every production source contraction.

Actual cross-source covariance, selected-source Gaussian law, physical significance/coverage, unrounded analytic pair geometry, and bin clearance remain UNKNOWN/NOT_ESTABLISHED. There is no physical MES anchor, calibrated physical Pi, cosmological depth, G_F, or family identification. The 17/42 original count, analytic 18/42 alternative, historical 48/baseline62/one-use-ultra allocations, and R9 UNKNOWN remain unchanged. The 29 discarded response directions are not exact physical nulls. The result is an HTT finite working-law statistical statement, not a MIO posterior or truth certificate.

## Resources and next transition

Measured arithmetic commands: 9.13 s and 3.68 s, total 12.81 s. Maximum observed process RSS is 259,664 KiB (265,895,936 bytes), below both the frozen 1 GiB RSS budget and the root-authorized 2 GiB address-space limit. Both numerical commands used one thread; their timeouts were 45 s and 35 s. Raw stdout, stderr, GNU time, and structured outcomes are retained under `raw/`.

The incoming debit is 47.00 s original work plus 15.89 s certificate plus 22.35 s plots = 85.24 s parent and 38.24 s incremental. This review additionally debits 12.81 s measured arithmetic plus 5.00 s conservative preparation/inspection/assembly allowance; actual assembly GNU time is retained separately. Total review debit is 17.81 s. Resulting parent debit is 103.05/300 s and incremental debit 56.05/120 s, leaving at least 196.95 s and 63.95 s respectively. No allowance is reset or renamed. The raw receipt separates measured execution from conservative accounting.

The controller can record this exact candidate's scoped conditional success and request the next authorized dependency-safe checkpoint. No publication or original scientific admission is performed by this reviewer.
