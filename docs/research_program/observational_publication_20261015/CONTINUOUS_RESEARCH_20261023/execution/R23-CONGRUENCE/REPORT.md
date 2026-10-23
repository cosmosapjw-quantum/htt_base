# R23-CONGRUENCE: compensated history through the measured-data quotient

Owner HTT; claim tier C0; status DERIVED_CONDITIONAL, non-claim-bearing; transfer source none. Packet 91c52db37de66cb64934232cb6f7c729d3ebed5d56e230c97ec9ed4671071eef; input identity sha256:a9cf00213dbeb740d3bd74e9954db4f00580675e902e692a87a578f5787bd367. Packet source a8e66da28461a415f5da3b3d609c482554d2dcd1; inspected starting checkout 855107f23fd4f25587ba242d8a5dfc1a8fc81876. During the stdout-only algebra check the parent advanced the same branch to 39cdfb01969bcf9b5897cfd6c3d8256d5e6fcac0; individual science inputs are bound in the raw receipt. Requested author Astra/xhigh; observed runtime UNKNOWN. Author /root/rc_91c52db37de66cb6 performed read-only theory and one finite algebra calculation. Parent mechanically assembles files; independent review remains separate.

The new result is the composition of the reviewed compensated history with the actual two-redshift residual and a common-parameter nuisance image. In a fixed external reference the ideal history column becomes B=(1+z)(1−A)=h−A. Whenever the declared nuisance space already contains the local A column, B and h have exactly the same observable quotient. This preserves a conditional route to history-sensitive combinations. The actual additional source-processing columns and physical PM/NNR/clock maps remain unqualified, so their retained-design rank is NOT_EVALUATED.

## Evidence and conventions

Reuse FRONTIER_20261020/theory/THEORY.md, CLAIMS_AND_TRANSFER.json and independent review; FRONTIER_20261020/projection/REPORT.md and RESULT.json; A22 theory/THEORY_AUDIT.md and continuation/two_redshift_pipeline/REPORT.md; current R23-Q and R23-SN returns. No 651-row projection, 54-history/432-optical campaign, Gaia catalogue fit or ODE is rerun. The retained 651-row zCMB remains a fiducial depth, not a newly qualified normal-frame measured redshift.

Read the actual legacy Git blobs dcd0562c693652e02f19e68600364f9f319c78b8 (unconstrained 13-column local optical design), 0cd5945e70d73d2429ea75cfde9a5cc825352735 (processed local CMB-boost Jacobian), and c518cdd0dcdd3ca628c71f6dd9e6a75e174ba805 (exact local Lorentz pullback). The old GitHub 404 entries do not imply those local blobs are absent. Their response algebra is reusable; the 13-coordinate design does not impose the physical mass-shell/frame constraints, and a local observer pullback does not supply matter history or a cosmic proper-motion response.

Primary checks performed 2026-10-23: [Horstmann et al., arXiv:2111.03055v2](https://arxiv.org/html/2111.03055v2), section 2, supplies the endpoint Doppler/aberration and distance-duality convention. [Guy et al., SALT2](https://arxiv.org/html/astro-ph/0701828), section 2 equation (1), specifies an empirical phase/wavelength spectral model with amplitude, shape and colour parameters. Neither establishes equivariance of the actual Pantheon+ producer pipeline. Established optical/history results are reused; the residual and quotient compositions below are direct algebra under those stated premises.

Use signature (−,+,+,+), c explicit, sourceward unit n, normal-frame physical velocities β=v/c, a_o=1, positive finite redshift and χ>0. The reviewed finite-interval first-order model has β_m=b/a, β_r=−ρb with ρ=3ε_m0/(4ε_r0), source following the dust and observer β_o=b+ell. All participating velocities, including ρb, must be small; Doppler displacement must be small on the distance-redshift variation scale. The source luminosity is bolometric energy per source proper time. No numerical nonlinear/remainder bound is supplied by the first-order notation.

## 1. Compose endpoints before differentiating

Let z̄ be the normal-frame background depth. Define radial scalars s=n·β_s, o=n·β_o, r=n·β_R for the declared comparison reference. Define p positively as the dimensionless radial source-velocity correction that is removed from the reference-frame redshift. To first order,

1+z_H=(1+z̄)(1+s−o),
1+z_D=(1+z̄)(1+s−r−p),
D_L=(1+z̄)χ(z̄)(1+2s−o).

The comparison distance is D_cat=(1+z_H)χ(z_D), not (1+z_D)χ(z_D). With g=5/ln(10), A=c(1+z̄)/(Hχ) and the actual standardized magnitude offset e_m relative to the bolometric ideal, expansion gives

R = g[(1−A)s + A r + A p] + e_m + r_phys.

Here r_phys denotes physical/processing terms without a supplied bound not represented in the displayed first-order model; it is not set to zero. The observer endpoint cancels because the same z_H multiplies χ(z_D). This is a physical-data transport statement for the stated optical comparison, not a zero derivative with respect to a trial reference used on fixed data.

For s=(1+z̄)n·b, p=0, define B=(1+z̄)(1−A). Then:

* Fixed external reference β_R independent of b,ell: the history response is g B n·b, plus the specified reference term; the ideal instantaneous observer term cancels.
* Same-observer reference β_R=β_o=b+ell: R=g n·[h b+A ell], h=1+z̄−z̄A=B+A, recovering the reviewed one-redshift response.
* Physical radiation reference β_R=−ρb: R=g[B−ρA] n·b. This conditional parameter map supplies no measured CMB-frame identification.

For any declared β_R=T_b b+T_ell ell+β_R0, the ideal response matrices are H_b=g[diag(B)N+diag(A)N T_b] and H_ell=g diag(A)N T_ell, where row i of N is n_i^T. The actual release must qualify T_b,T_ell and the redshift/source correction before this is an empirical design.

Three experiments stay distinct. Passive same-source observer reboost transports measured m and z_H while holding the same fixed-reference z_D; its bolometric residual is invariant. Fixed-data trial-frame inference holds m,z_H,n fixed and changes 1+z_D→(1+z_D)e^q, yielding ∂R/∂q=−gA. Physical source-history variation changes source and observer endpoints and source processing and uses the composed rows above. A reference-velocity coordinate has the opposite sign from q when q=o−r−p; this explains ∂R/∂r=+gA without a convention conflict.

The proper-time ratio dτ_s/dτ_o=(1+z_H)^−1 is already included in redshift and distance duality. Adding another source-clock factor would double count it.

## 2. Spectral, calibration and PV nuisance image

For primitive measured outputs (m,z_H,z_D), the exact differential of the residual is

dR=dm−D_H dz_H−D_D dz_D,
D_H=diag[g/(1+z_H)], D_D=diag[gχ′(z_D)/χ(z_D)].

Thus one common nuisance parameter vector a with pipeline Jacobians J_m,J_H,J_D contributes the single column image

U=J_m−D_H J_H−D_D J_D.

Terms driven by the same a must be summed before profiling. They must not become independently free nuisance parameters merely because they occur in different pipeline stages.

For the A22 passive test, correctly transported z_H is accounted for analytically, κ=m′−m+g lnδ and η=z_D′−z_D. Its exact finite defect is ΔR=κ−g ln[χ(z_D+η)/χ(z_D)]. Its tangent nuisance is U_proc=K−D_D E when κ=Ka and η=Ea. This tests observer equivariance; its K,E do not by themselves give the physical source-history derivative. A source-normalization/standardization law must also connect the actual source population to the bolometric ideal.

The local spectral law f′_λ(t′,λ′)=δ³ f_λ(δt′,δλ′) implies the fixed-coordinate generator (3+t∂_t+λ∂_λ)f_λ. A paired sample has t′=t/δ; the sampling-time derivative must then be included, cancelling the explicit t∂_t term along transported epochs. Photon counts integrate the spectrum against the same specified passband weight T(λ)λ/(hc), with compatible wavelength units. Therefore an actual spectral-response Jacobian must transport wavelengths, epochs, passbands, attenuation and the refit/standardization operations together. A bolometric multiplier or raw fixed-band slope alone does not supply it.

If physical radial source deviations V_s a, reference deviations V_R a and removed source-PV corrections V_p a are modeled explicitly, their endpoint image is

U_end=g[(I−diag(A))V_s+diag(A)V_R+diag(A)V_p].

Photometric calibration, spectral standardization and extra pipeline redshift defects enter through the same residual differential. Define any extra E after excluding the already represented V_p correction, so the same PV effect is not included twice. For example, if one parameter produces source radial motion v and its correction removes exactly that same v, its image is g[(1−A)+A]v=g v. Treating the source term and its correction as independent free flows would change the nuisance space. The released Pantheon total covariance remains one working metric; these deterministic mean responses do not authorize an extra stochastic PV covariance or its subtraction.

A new exact rational falsifier makes the issue concrete: K=(1,0)^T, E=(0,1)^T, D_D=diag(2,3). The single-parameter response K−D_D E=(1,−3)^T has rank 1, leaving contrast (3,1) that annihilates it. Incorrectly splitting K and −D_D E into two independent parameters has rank 2 and destroys that contrast. This is an algebra witness, not an observational rank result.

## 3. Observable quotient and surviving combinations

For a fixed selected-cohort mean model d=Hθ+Ua+ε+r and fixed positive definite working C, let W satisfy WCW^T=I, Z=WU and P=I−ZZ^+. The physical mean quotient is E_q=PWH. A parameter combination l^Tθ is estimable under that declared linear model exactly when l belongs to row(E_q). For such l, a_l=(E_q^+)^T l gives the contrast a_l^T P W d; if Cov(ε)=C, its conditional variance is ||a_l||². Its deterministic physical bias is a_l^T P W r. For v=W^T P a_l, a supplied remainder set R gives signed bias interval [−h_R(−v), h_R(v)]; an absolute bound is max{h_R(v),h_R(−v)}. No finite physical error bar follows while the required remainder set is unknown.

The new history relation yields a direct reuse lemma. Let H_A=g diag(A)N, H_h=g diag(h)N and H_B=g diag(B)N=H_h−H_A. If col(H_A) is contained in col(U), then

P W H_B = P W H_h.

The same algebra works after any common linear compression. It does not assume full-sky orthogonality, and it does not imply equality after substituting different source-processing/nuisance definitions.

The existing 651-row conditional report uses a free calibration dipole and a frozen redshift-distance flow K=−g(1+A)/c. Their span contains H_A. Under that historical design, the full six-column optical quotient has rank 3/6; the three nonzero singular values are 0.04650048310294896, 0.03129560401347088 and 0.023467959581088344. Local residual column norms are at most 2.249713137887459e−11. These are reused stored results, not new computations. The B/history quotient is algebraically the same within precisely that declared design. After adding actually qualified processing nuisance columns the surviving history rank can decrease; its value is currently unknown. The old flow kernel lacks complete optical source/observer transport, so this equality does not qualify a common physical likelihood.

A separate retained observable survives in R23-Q: six low-minus-high and middle-minus-high E1 Cartesian coefficient contrasts in measured-redshift bins, with their full conditional covariance. Those contrasts remain proper-motion coefficients (µas/yr), not b, cosmic A_a or a common-congruence clock signal. Mapping them to θ requires their own J_mu plus frame/NNR/source response, and joint use requires applicable cross-covariances. The selected-source residual spatial covariance and classifier law remain unknown.

## 4. Rows that cannot be substituted

Measured redshift is a dimensionless endpoint frequency ratio. Proper motion is a tangent angular rate per observer proper time and requires moving-source, moving-ray and observer/frame derivatives. An independent clock/drift experiment requires its clock standard, epochs, trajectories and time-transfer response. Their units and derivative experiments differ; a copied A or h radial column does not connect them.

The reviewed β_m=b/a is geodesic dust in the restricted model: the derivative of its peculiar coordinate-frame velocity is not the dust four-acceleration. Existing Gaia E1 supplies observer aberrational a_obs/c; it does not supply the cosmic congruence A_a. Spin/NNR restrictions and source transverse motion are separate inputs. A clock frequency ratio derived from the same z_H is not an independent datum. No missing PM or clock row is zero-filled or replaced by position covariance.

## 5. Validation and exact remaining input

One genuinely new stdout-only calculation in the repository .venv passed nine exact algebra residuals: observer cancellation; same-observer, fixed-reference and radiation-reference endpoint compositions; B=h−A; PV correction sign; and finite quotient annihilation/equivalence. The rational common-nuisance versus incorrectly split nuisance ranks are 1 and 2. Python 3.12.3, SymPy 1.14.0; exit 0. This is author-side finite algebra, not four-axis CAS or independent review. Original campaigns were reused without replay.

New empirical response/rank is NOT_EVALUATED because the following inputs remain missing:

1. The nominal observed SN source model/fit binding and producer parity, followed by same-ID spectral/lightcurve/passband/attenuation/refit/global-standardization response. R23-SN's public conditional covariance fit has χ²/19≈0.89843 but still fails all four frozen published-parameter parity bounds. Its pinned release-tree inventory found neither nominal PS1.nml nor out_train_v7_1_bd17fix and no observed nominal FITRES. That existing source-exhaustion receipt is the concrete SN blocker, not a new failed fit.
2. The actual zHEL/zHD/reference/PV-group correction map and its common-parameter derivatives or finite bounds, with source-row identities and declared physical source/reference congruence. The 651-row zCMB fiducial design does not supply this map. Total covariance and published parameter errors do not bound κ or η.
3. Same-congruence proper-motion, NNR/frame and independent clock/drift response, units, source classes, selected-row identities and applicable covariance. Existing R23-Q observables and Gaia a_obs are useful components but do not furnish these physical maps.
4. A finite physical remainder for the chosen application domain: nonlinear/second-order stress and optical terms of the compensated mode; additional metric/lensing/source terms where relevant; source standardization and PV/reference-map defects; and the measured-depth/selection/cohort error required by any population interpretation. These are not bounded by an algebraic O(β²) label. No signed four-sector x_C or S04 interval is inferred by zero-filling the missing sectors.

The immediate executable transition is source acquisition/reconciliation for items 1–3, then evaluate only the newly qualified response/nuisance columns against retained sufficient statistics or retained selected rows, with the same covariance counted once. Preserve the old rank result; report newly surviving row-space combinations and propagate a declared remainder set. K04/S04 original acceptance and broader physical admission remain HOLD. This result does not establish a global-tilt identification or a universal impossibility.

## Claim audit

| Claim | Owner | State | Evidence | Remaining condition |
|---|---|---|---|---|
| Endpoint composition and B=h−A | HTT | DERIVED_CONDITIONAL, C0 | Reviewed endpoint premises; displayed derivation; new exact algebra checks | Actual source/reference map |
| Combined nuisance U=J_m−D_H J_H−D_D J_D | HTT | DERIVED_CONDITIONAL, C0 | Residual differential and rank-1/rank-2 falsifier | Qualified common-parameter Jacobians |
| Equality of h and B quotients when A is nuisance | HTT | DERIVED_CONDITIONAL, C0 | Linear proof and exact finite witness | Same declared rows, metric and nuisance space |
| Three historical design directions and six R23-Q contrasts | HTT | DIAGNOSTIC_ONLY reuse | Existing stored results | No new physical interpretation |
| New physical rank, finite physical bias or signed-sector bound | HTT | HOLD | Required inputs absent | Items 1–4 above |

No original claim is upgraded, no acceptance is relaxed, and no publication or dispatch is asserted. The physics/math, local/global, observable-statistics, scientific-validation, claim-firewall and claim-provenance skills were applied. Within the physmath R/C map: existing premises were reused, the new composition was derived and author-checked, and the finite execution handoff is complete; independent review and empirical application are still open.

## Mechanical assembly and reproduction

The parent persisted the author's exact executed [stdin](algebra.py) and
[stdout](RESULT.json), without rerunning the algebra merely to save files.
[RAW_RECEIPT.json](RAW_RECEIPT.json) contains both and the actual native author's
command/exit/source metadata. The parent checked all seven supplied source
identities and generated the [diagnostic PNG](QUOTIENT_WITNESS.png) and
[PDF](QUOTIENT_WITNESS.pdf) with [plot.py](plot.py), using the author's exact
rational witness recipe. The plotted coordinates are arbitrary algebraic units,
with no sky frame, seed, uncertainty or significance interpretation. Category
DIAGNOSTIC; HTT C0; transfer none. Actual source-processing Jacobians and retained
physical rank remain UNKNOWN. Requested parent gpt-6.1-sol/medium, observed UNKNOWN.

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 .venv/bin/python -B docs/research_program/observational_publication_20261015/CONTINUOUS_RESEARCH_20261023/execution/R23-CONGRUENCE/algebra.py
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 .venv/bin/python -B docs/research_program/observational_publication_20261015/CONTINUOUS_RESEARCH_20261023/execution/R23-CONGRUENCE/plot.py
```
