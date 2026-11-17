# R66 source refinement and direct method comparison

This bounded parent follow-up addresses the exact Commander response and the closest actual PR4 morphology method. It is part of R7/R8 of the same study, not a new literature loop.

## S12 — Aluri & Patel, arXiv:2506.22795v1

Primary source: [Examining statistical isotropy of CMB low multipoles from Planck PR4 data](https://arxiv.org/html/2506.22795v1), Pavan K. Aluri and Sanjeet Kumar Patel, v1 28 June2025. Parent read Eqs2–6 and Sections2–3, with relevant results context. The power tensor is A_ij=[ell(ell+1)(2ell+1)]^-1 a†J_iJ_j a. Its trace equals C_ell; normalized eigenvalues define the entropy. This is a quadratic tensor and is unchanged under a→−a. R66 directly implements the ell2 formula on the **same R66 extracted coefficients**, tests trace/rotation/sign reversal and compares its outputs with the signed radiation-stress image. This is not a reproduction of that paper's inpainting/foreground/noise pipeline or quoted anomaly probabilities.

Section3 describes a native4096 observed map and100 native4096 simulation maps with nominal5arcmin beam, subsequently40arcmin/NSIDE256 and sparse inpainting. The actual public005a MC headers freshly opened in R66 say NESTED2048 and uK_CMB, whereas the observed temperature is NESTED4096 and K_CMB. Therefore the publication's100-member label alone does not identify the same source bank or qualify its effective beam for this study. R66 preserves that distinction. No error in the paper is inferred merely from this differing file description.

## S13 — Planck intermediate results LVII, NPIPE

Primary source: [A&A643 A42(2020), Joint Planck LFI and HFI data processing](https://www.aanda.org/articles/aa/full_html/2020/11/aa38073-20/aa38073-20.html), arXiv2007.04997. Parallel found the official source; parent obtained the official full text with Exa (335705-character tool text) and inspected the relevant sections. This is original collaboration documentation.

Section7.1 specifies the Commander parametric temperature model, retaining the Solar dipole in the CMB component. Eq19 uses per-channel beams, relative gains, bandpass corrections and the thermodynamic/brightness conversion. The component-separation response cannot be replaced by a guessed single channel coefficient. Section7.2's description of subtracting Solar dipole and frequency-dependent second-order quadrupole is the **SEVEM** procedure, not a release-matched Commander residual template. AppendixC, EqsC.1–C.3, gives the frequency-dependent Doppler factor q=(x/2)coth(x/2), x=h nu/(k_B T0), followed by the actual beam convolution. It supports the physical DQ source family and shows why the optical/processing operator matters; it does not provide a numeric effective residual coefficient for the exact R66 Commander map/005a pair.

The Exa fetch resolves a primary-document access failure of the general web reader. No native map or simulation download was required. The source refinement does **not** close exact upstream DQ/beam/exchangeability qualification. It prevents the stronger error of treating SEVEM text, R2.02 residual filenames, nominal5arcmin or another paper's4096 MC description as a product-specific Commander calibration.

## Actual computational checks from the requested Wolfram tool

The Wolfram context call returned MCP internal error−32603 and supplied no science evidence. A subsequent actual Wolfram Language evaluation succeeded for two exact polynomial angular integrals. In particular

    Integrate[(1+d x)^4 (x^2−1/3)/2,{x,−1,1}]
       =8d^2/15+8d^4/105.

This is the zz component of the dipole-only STF stress and agrees with R36's tensor expression (4/5+4d^2/35)STF(dd). The other integral used (1+q(x^2−1/3))^4; its linear term16q/45 is consistent with (8/15)Q_zz and Q_zz=2q/3. These two integrals do not certify the entire analysis. Separate executed Python checks cover rotations, exact boosted radiation/Landau, the dipole–octupole coefficient, finite-N statistics and shared-sky covariance.

## Interpretation change

The nearest literature comparison is now stronger than a scalar C2 comparison alone: a contemporary PR4 **tensor** morphology method also loses the overall sign required by a signed stress mean. R66 retains that information. This is a specific distinction in target and sufficient information, not a claim that all prior tensor methods lack phase information or that an invertible STF recoding improves the full harmonic likelihood.
