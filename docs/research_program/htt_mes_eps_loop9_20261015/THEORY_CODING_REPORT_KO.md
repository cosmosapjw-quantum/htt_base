# HTT Loop 9: Planck–MES covariant epsilon bridge
2026-10-15 KST. Selected DAG task C8-OBS-MES-EPS (next after completed C8-CF4-METHOD).

## Basis and authority

Original source HEAD: 13d8d85fa470d645d008986e8f77d8d0f70fdf54.
Immediate tested parent commit: 915d8bfd22b09f4d57fa5902110bc6fd8d3aa734.
New isolated worktree: /home/cosmosapjw/worktrees/htt-planck-mes-eps-20261015
Previous uncommitted owner source remains unchanged; all raw Planck maps, native masks, and FFP10 simulation cache are READ_ONLY. SHA-256 of the three small source snapshots, two MES primary source texts, 3 native masks and FFP10 simulation cache is preserved in results_v2/result.json.

Physical claim status is withheld. This result uses the observed Planck PR3 same sky under nine processing channels, plus the previously registered gated K1 FFP10 SMICA fixed-weight conditional simulation cache. Same-sky processing products are NOT independent cosmological realizations, and FFP10 fixed-weight signal/noise simulations are not a calibrated physical Planck null.

## Exact normalization result (derived, Wolfram checked)

For orthonormal real spherical harmonics, delta T/T0=sum_lm a_lm Y_lm/T0 (observed coefficients in microK, T0=2.72548e6 microK), define

    C_l = sum_m |a_lm|^2/(2l+1),
    DeltaT_l^2 = sum_m |a_lm|^2/(4pi).

Original Stoeger–Araujo–Gebbie 1997, ApJ 476 435, Eqs 15,17–19 (including original corrected erratum):

    <tau_{A_l} tau^{A_l}> = (2l+1)*(2l)!/[2^l(l!)^2] * DeltaT_l^2/T0^2.

The root tensor norm therefore differs from the older Loop7 sqrt(C_l)/T0 by

    f_l = (2l+1)*sqrt( (2l)!/[4pi*2^l*(l!)^2] ).

f_2 = (5/2)sqrt(3/(2pi))=1.72747074735668;
f_3 = (7/2)sqrt(5/(2pi))=3.12221720326735.
Those factors were checked by Wolfram exact symbolic algebra and Python batch/analytic identities. All nine real retained Planck-source coefficients reproduce the prior Loop7 sqrt(C_l)/T0 results EXACTLY, before conversion.

Under the previously registered PR124 geodesic C1/C2 algebra,

    B_sigma=(5/3)eps1 + 3eps2 + (3/7)eps3,
    B_omega=(10/3)eps1 + (2/15)eps2,

and the conventional channel-normalized anchors Sigma2=(3/2)B_sigma^2 and W2=(3/2)B_omega^2, the hypothetical eps1=0 scenario from SMICA_HM1 changes Sigma2 from prior algebraic 7.02819281e-10 to 2.59332149e-9 (ratio 3.68988). This is NOT a cosmological shear measurement or a physical bound; intrinsic residual radiation eps1 is not measured or independently proved zero. Spatial/time derivatives of temperature multipoles across all fundamental observer worldlines are UNKNOWN (MES assumptions A1, C1/C2), as is the radiation/matter/Bianchi congruence mapping.

References:
- MES primary (1995) https://arxiv.org/abs/astro-ph/9501016
- MES companion (1996) https://arxiv.org/abs/astro-ph/9510126
- SAG 1997 http://arxiv.org/abs/astro-ph/9904346
- Official Planck 2018 component separation, A&A 641 A4 https://www.aanda.org/articles/aa/full_html/2020/09/aa33881-18/aa33881-18.html

## Observation operator and real-source computation

All nine Planck sources retained ell2..5 real harmonics on the same Galactic common T mask. Source pixels nside64 RING, 49,152 total, n_selected=26,846; T is microK. Simultaneously fit ell0..5, 36 coefficients, then keep ell2,ell3. The projection is

    a_hat = (X_M^T X_M)^-1 X_M^T y_M.

For an unmodelled high-mode input,

    a_hat_low = a_true_low
              + [(X_M^T X_M)^-1 X_M^T X_{ell>=6}]_low a_true_high.

Contained-band identity residual is ~4e-15; it does not constrain unmodelled ell>5. Calculated l6..8->estimated ell2,3 finite leak operator has spectral norm 1.47761219 on the common mask versus 0.000161498 on the full-sky nside64 pixel quadrature. This is an OPERATOR NORM, not the actual physical sky error or the total ell>8 leakage bound.

Source processing required an observed repair: NSIDE2048 native Planck mask pixels use NESTED ordering, while K1 common mask and the OLS design use RING ordering. First attempt without conversion selected 23,503 pixels, failed source contract and exited nonzero. Corrected native parent NESTED->RING conversion reproduced 26,846 original Loop5 pixels. Added targeted NESTED/RING regression test and reran. This is an implementation indexing error, not a change in physical hypotheses.

FFP10 simulation gate cache SHA is checked before fitting. Exactly 999 delivered CMB signals and 300 noise maps with unique IDs, paired first300 as registered, are fit using the same sky-mask projection. Full-pixel and masked CMB-only are compared PAIRWISE on identical simulated skies. To quantify the delivered noise processing response, add one delivered noise map to each of the first300 CMB maps under the same fixed operator. No source null probability is inferred.

## Actual quantitative outputs

- SMICA_FULL observed (conditional) eps2=1.070465576e-5; eps3=2.186076289e-5.
- Nine maps' same-sky processing eps2 range [1.050489447e-5,1.073558069e-5]; eps3 range [2.183186478e-5,2.202663289e-5].
- FFP10 999 matched mask versus full-pixel eps RMS difference: eps2=2.651992734e-6, eps3=3.906240887e-6.
- FFP10 300 paired noise+signal versus signal-only eps RMS difference: eps2=6.849047651e-8, eps3=9.203378397e-8.
- FFP10 CMB same-mask median eps2=1.999964664e-5 and eps3=2.652636018e-5; full-pixel median eps2=1.911318706e-5, eps3=2.486994486e-5.
- The K1 observed cache sky and independently extracted actual Planck SMICA_FULL on this common mask differ in eps2/3 by [-9.0139e-11, +2.5471e-9]. Not proof of cosmological null exchangeability.
- Across nine same-sky maps, eps1=0 conditional algebraic Sigma2 anchor range [2.510832881e-9,2.593321486e-9]. PHYSICAL ADMISSION: WITHHELD.
- Beam-only illustrative B_l=exp[-ell(ell+1)sigma_b²/2] for assumed circular Gaussian FWHM 5' and 10' is tabulated in JSON; real Planck component-separation transfer, beam/mask covariance and pixel window response are not calibrated by these scenarios.
- Runtime around 15s, peak RSS around 596 MiB, 2-thread BLAS, matrix chunks. Raw 489 MiB gated FFP cache was not copied into Git.

All exact numerical figures, hashes and source labels are in results_v2/result.json; sampled conditional epsilon arrays in results_v2/conditional_ffp10_eps_samples.npz; diagnostic PNG in results_v2/.

## Completion gate, failed branch, next work

Derived and numerically checked: SAG harmonic-to-PSTF correspondence, source normalization, finite mask high-mode response, matched FFP10 mask/noise differences and model-specific processing sensitivity.
Implementation verified: real pixel/gate/identity checks, unit injection and same-sky original sqrtCl regression, RING/NESTED regression. Native subagent NOT_RUN (no spawn tool offered); user local Codex NOT_USED.

Physical Claim HOLD: residual intrinsic dipole, all-observer Copernican multipole derivatives, actual full-sky high-l and beam response, same-congruence Boltzmann source, and joint Bianchi observation covariance. No unconditional EGS, Bianchi shear or FLRW deviation posterior, and no calibrated Planck PTE.

Next minimal scoped physics: bound or model Planck map-to-covariant multipoles with high-l/beam/cosmological radiation transfer; then certify C1–C2 and observer-frame residual radiation dipole or preserve them as unknown. Parallel geometry T8 and physical-joint C8 lanes remain BLOCKED pending their separately required actual laws.

Reproduce (machine with registered Planck masks/FFP10 cache):

    cd /home/cosmosapjw/worktrees/htt-planck-mes-eps-20261015
    OPENBLAS_NUM_THREADS=2 OMP_NUM_THREADS=2 PYTHONPATH=htt/src:htt python3 -m pytest -q tests/obsstat/test_mes_eps_measurement_bridge.py
    OPENBLAS_NUM_THREADS=2 OMP_NUM_THREADS=2 PYTHONPATH=htt/src:htt MPLBACKEND=Agg python3 scripts/run_htt_planck_mes_eps_20261015.py --output-dir docs/research_program/htt_mes_eps_loop9_20261015/results_REPLAY

All output directories are create-only. The first source-indexing failure and earlier complete run are not silently marked equivalent to the corrected run. results_v2 is the canonical corrected case.
