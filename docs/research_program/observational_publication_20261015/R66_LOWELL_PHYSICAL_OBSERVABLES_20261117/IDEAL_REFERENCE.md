# Executed ideal reference and source-repair contract

The observed PR3/PR4 Commander temperatures are actual data. The primary statistical reference in the final R66 analysis is an explicitly declared Gaussian model, not an end-to-end Commander simulation population. Its covariance is analytically known;4096 draws validate it and train/check the exploratory paired estimator. No physical significance is inferred from those artificial draws.

## Why the originally selected bank was rejected

All100 public `npipe6v20_commander_cmb_2048_mc_0300_005a.fits` through0399 were read and freshly hashed against their original receipts. Their temperature carriers are identicallyzero. Raw spot checks at300,349,399 also give I=0 with nonzero Q/U. The analysis rejected the singular covariance. This is a product-selection/source-content failure. The100 valid polarization-use files have not become invalid E/B files; only their proposed use as temperature reference was rejected. The original extraction metadata, zero-temperature arrays, source snapshots and failed analysis log are preserved.

The distinct public bare products `npipe6v20_commander_cmb_mc_0200.fits` through0299 are scalar T, RING, NSIDE4096,1024D cells. Their TUNIT1 field is blank. The complete PLA catalogue identifies them; the original NPIPE article and Aluri–Patel discussion do not product-bind the bare files' numerical units. A bounded16-file attempt was chosen before coefficient inspection, but parallel HTTP streams ended prematurely. Partial files were never counted as realizations. A separately started0200 download is inspected as content only. No covariance or PTE uses this unqualified pilot.

`UNIT_FREE_DIRECTION.md` gives an angular predictive law insensitive to a shared positive unit scale, with explicit zero-mean and common-shape assumptions. It is implemented and numerically tested. An insufficient actual temperature bank cannot be made sufficient by this transformation; no actual-data angular significance was calculated from the content pilot.

## Fixed ideal sky-generating model

The archived reference is `COM_PowerSpect_CMB-base-plikHM-TTTEEE-lowl-lowE-lensing-minimum-theory_R3.01.txt`,205647bytes, SHA256 `50eecd4422e22026070bdacf9fa8a7e7ef3badf4fa50fffea040df669715cf51`. R49 previously used this exact spectrum. The first columns are ell and TT D_ell in microkelvin squared; C_ell=2pi D_ell/[ell(ell+1)]. The reference fixes this spectrum and does not integrate cosmological parameter uncertainty.

For each of the three actual extraction operators let E_a act on the common native-mask-first parent averages. Its five quadrupole rows can be written as weights w_ap on the NSIDE128 parent map, by distributing NSIDE64 weights according to the actual retained native-child counts. No mask, U, estimator or weight is fitted to the synthetic rows.

For ell>=3 the declared random map is a Gaussian sky evaluated at the NSIDE128 pixel centres, multiplied by a5arcmin Gaussian beam and the HEALPix128 pixel window. It is band limited at Lref=256. Controls Lref=64,128 test only this ideal model's high-mode cutoff. This is an explicit approximation to native averaging and component separation; it is not called an exact Commander response.

For real w,

    A_a,lm = sum_p w_ap Y_lm*(n_p).

`healpy.map2alm(w/pixel_area,iter=0)` with ordinary equal-area weighting evaluates this finite sum. The reality condition gives

    C_ab(ell>=3)=sum_l C_l B_l^2 p_l^2 [A_a,l0 A_b,l0 +2 sum_(m>0) Re(A_a,lm A_b,lm*)].

The quadrupole is included separately using its exact native-averaged polynomial columns. Let K_a be the measured STF injection response. Then

    C_ab(ell2) = 15 C2 B2^2/(8pi) K_a K_b^T.

All three K_a agree with I5 to1.23e-15. The same quadrupole realization is therefore shared across all operator blocks. No additional HEALPix128 window is applied to this already native-averaged component. Monopole/dipole are projected by the actual estimator and are not stochastic carriers in this reference.

The resulting15x15 C is positive definite. The exact-in-model primary four-dimensional Gaussian law uses C_perp=U^T C_5 U. The reported lower-tail diagnostic is P(chi-square4 <= s^T C_perp^-1 s). With an observed PR4 primary s this is0.0984010544. This number is conditional on the entire ideal model; it is not a source-qualified Commander anomaly probability.

## Draws, heldout check and limits

4096 synthetic15-vectors use seed6620261117. The first2048 train the paired GLS weights. The last2048 check its covariance. The selected likelihood uses the known C, rather than discarding analytic knowledge to estimate it from the draws. The finite-N Student/F law is retained as an independently tested alternative for a future actual covariance-estimation bank.

Primary quotient covariance traces for Lref64,128,256 are2678.869244,2679.696542,2680.139025microK². The64 cutoff differs from256 by0.04738%;128 differs by0.01651%. This stability concerns the ideal population law. It does not erase the real-data66.6% vector shift between fitted bands6and8, nor bind foregrounds, beam, spectral distortions or native transfer.

This reference has no instrument noise, no component-separation residual, no foreground uncertainty, no map-specific DQ transfer, no higherell>256 and no parameter uncertainty. Cosmic variance is a population scatter, not a measurement-error bar on the realized sky. Source-qualified absolute physical significance remains unresolved.
