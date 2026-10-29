# R37-03 fresh independent scientific review

Verdict: SCOPED_CONDITIONAL_PASS. No blocking finding. Reviewer /root/rc_3dab57f35de21656 did not author the candidate. Requested gpt-6-astra/xhigh; observed runtime UNKNOWN.

Packet 3dab57f35de216561506e56a9b5a018e4683c2a883c0931d10da5d3b17c33830; task R37-03-HUBBLE; input sha256:15d9b17d0852724f6774adf53e09a32627ead44ead7d7b5c705e7a26254df47f; candidate sha256:a9cec4e49645247b15a8ccebb3cee992db04f9526882291dc886e06a081ded77.

## Evidence and scope

Read the packet assignment, seven pinned source artifacts, DATA_ANALYSIS_CONTRACTS.md, the complete candidate compute_hubble.py/test_compute_hubble.py, all candidate tables and report metadata, and source-specific R36-08/R36-01 result and publication-status records. Inspected the retained R36-08 consumer and saved RESULT_RAW.json for source basis, original row indices, retained coefficients, selection and covariance provenance. No catalogue was fit, no old producer main was executed, and no native solver or ODE ran. The immutable candidate manifest, all 14 listed artifacts and all seven input sources matched their hashes. Checked the original CBL first-derivative identity against Clarkson, Bassett and Lu, arXiv:0712.3457v2, equations (2)-(3) and the separate-H(z) discussion: https://arxiv.org/pdf/0712.3457 . The new opacity substitution was checked independently by de-attenuating d_r and d_r prime before applying that identity.

## Assumptions and conventions

The 490-row primary selected law and overlapping 705-row sensitivity retain 342/148 and 557/148 low/high rows, respectively, with 62/114 duplicate-CID excess rows. The former is a subset of the latter; their high-row identities coincide. Each cohort has its own conditional fixed-design Gaussian signed16 event. The primary and sensitivity are not independent confirmations, and there is no asserted joint 95 percent guarantee over both fitted cohorts. Empirical null coverage remains unknown.

STF coordinates are Frobenius normalized in the retained RA/DEC Cartesian chart; physical sky frame is unknown. The SN source uses zHD in its fixed-background dimensionless distance integral and zHEL in its luminosity factor. These are source-qualified released-magnitude contrasts, conditional on the fixed background and nuisance law. CF4 retains outward ICRS J2000 directions, z_CMB metadata, km/s/Mpc coefficients and their squared covariance units; no joint SN/CF4 inference is made. The synthetic CBL uses c=299792.458 km/s, H=70 km/s/Mpc and length-valued d, so kappa has Mpc^-2 units. Metric signature is (-,+,+,+).

## Equation and definition audit

| Item | Status | Evidence and interpretation |
|---|---|---|
| Signed16 common event | PASS | The source-profiled covariance is used once. All six cross-depth rows reproduce L C L^T including cross blocks. The primary x-versus-z depth-contrast SE is 0.07737715494933327 mag; independent-bin deletion gives 0.0778288813953658 mag. |
| Log-H ratio and interval quantifiers | PASS | For E={theta: (theta-theta_hat)^T C^-1 (theta-theta_hat)<=q}, q=chi2_16(0.95), k=ln(10)/5 and L=feature(n)-feature(z), put b=bg+bt/2 and B=k sqrt(q L C L^T)+b. Every theta in E and every allowed signed remainder obey exp(-k L theta_hat-B)<=H_u(n)/H_u(z)<=exp(-k L theta_hat+B). Each scalar endpoint is attained at the appropriate ellipsoid support point and signed budget endpoint. This is not a claim that all displayed endpoints occur jointly. |
| Ratio denominator | PASS, conditional positive branch | With any unknown positive common scale Hstar, H_F(z)=Hstar exp(-k feature(z) theta) is positive. Intercepts cancel from the ratio. The minimum normalized reference factor on the inspected events is 0.9021581671713473; this is not an absolute lower bound on H0 or an empirical physical-congruence positivity measurement. There is no noisy linear denominator or separate numerator/denominator uncertainty inflation. |
| Same-input scalar comparator | PASS | Scalar and tensor-coordinate means and standard errors match for all comparator rows. Independently reconstructed scalar confidence regions including all four opacity/remainder budgets match the corresponding table rows. There is no additional information claim over correct joint GLS. |
| Opacity and finite-distance signs | PASS | Delta ln H_u=-k Delta m+Delta r_g+Delta tau/2 follows from D_L,r=cz/H_u exp(r_g+tau/2). The code adds declared absolute difference bounds, not a second covariance or measured opacity posterior. |
| Grey versus dichroic transmission | PASS | Q_in eigenvalues 1/9 and 1/25 give sqrt(tmin/lambda_min)<=D_L<=sqrt(tmax/lambda_max). Both endpoints satisfy the operator transmission bounds; values outside fail. Xi is invariant under grey scaling, so it cannot determine the missing grey factor. |
| First-derivative CBL | PASS, finite synthetic only | De-attenuation gives d=e^(-tau/2)d_r and d'=e^(-tau/2)(d_r'-tau' d_r/2). Standard curvature then gives [(H/c)^2(d_r'-tau'd_r/2)^2-exp(tau)]/d_r^2. Reconstructed all table extrema on the declared 251-point family and found a=0.2 to be the common four-window minimizer, with zero spread. Zero opacity has spread 5.997144030085523e-7 Mpc^-2. |
| Empirical curvature | HOLD retained | Angular coefficients do not supply radial distance derivatives, independently qualified overlapping H(z), or their joint law. The finite control is not an empirical curvature measurement or a general continuous-family identification claim. |

## Dimensional, sign, limit and numerical checks

Independent script completed 343 checks. All 48 local-H rows match independently reconstructed means, standard errors, common-event bounds, opacity expansions and exponentials. Extremizers lie on the same ellipsoid and reproduce endpoints to maximum absolute ratio residual 2.220446049250313e-16. The normalization scale remains unmeasured. The zero/equal-direction and STF trace checks, cross-bin covariance falsifier and opacity control all pass the candidate's three focused tests. CBL windows exclude d=0. The finite source covariance is positive definite; source full1701 validation remains explicitly absent. Retained diagonal standard errors are display summaries, not extra noise terms.

Both one-page PDFs were rendered to the external review directory and visually inspected. Labels and plotted order agree with the CSV values; the H ratio plot is marked conditional 95 percent outer interval, and the optical plot uses synthetic length units. The plotted line segments visualize the finite evaluated scan; the quantitative acceptance is the saved rows and declared model.

## Claim-tier implications and residual risks

Qualify only opacity_qualified_optical_result as a conditional released-observable sensitivity product plus finite synthetic method control. No absolute H0, empirical curvature, physical shear, Bianchi-family label, native-solver result or independent SN/CF4 joint significance is admitted. Original42 remains unchanged, as does its separate analytic-alternate accounting. Physical budgets, local positive branch, source response and opacity family are supplied assumptions. Neither empirical coverage nor source-model correctness is established by these finite checks. Exact endpoint attainability is per scalar functional; the collection of plotted intervals is an outer image of the common event, not a rectangular joint identification set with every corner attainable.

## Fatal blockers and proposed changes

None for the frozen scoped acceptance. No candidate change is proposed. Invalidating the source identity, selected covariance qualification, fixed-law assumptions or physical remainder bounds invalidates the corresponding interpretation. A future empirical curvature claim would require the held radial-distance/H(z)/derivative inputs and joint uncertainty law.

## Required artifacts and status updates

This external REVIEW.md, independent_checks.py, INDEPENDENT_CHECKS.json, COMMANDS.json, captured stdout/stderr, rendered figures, RESULT.json and RAW_RECEIPT.json support the controller decision. No repository, STATE or Git mutation was performed by the reviewer. The controller owns recording this scoped acceptance and advancing its next authorized packet.
