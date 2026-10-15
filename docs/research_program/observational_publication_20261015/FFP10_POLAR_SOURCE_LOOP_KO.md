# HTT P2 L01: actual Planck FFP10 polarization native-pixel pilot

Date: 2026-10-15 KST. Parent commit 02acb18116505c66eca605038bbadfc86381ee01. Original owner checkout HEAD 13d8d85fa470d645d008986e8f77d8d0f70fdf54 with 57 pre-existing dirty paths is READ_ONLY; independent branch research/htt-planck-pol-ffp10-20261015. Native subagent NOT_RUN: no spawn interface; local Codex NOT_USED.

## Question and actual recovered inputs

Can the actual FFP10 SMICA CMB and noise maps be passed through the same NSIDE64 masked physical spin-2 Q/U low-ell estimator used on actual Planck PR3, without treating nine processed observed maps as independent cosmological skies?

Source archives found locally: raw/planck_ffp10/smica/cmb_mc has 999 files and raw/planck_ffp10/smica/noise_mc has 300. Each selected FITS has 603,987,840 bytes, Nside2048 RING, INTENSITY, Q-POLARISATION and U-POLARISATION, packed 1024E, K_CMB. Crucially the FITS has no explicit COORDSYS or POLCCONV. The source frame/sign convention is not inferred from filename.

Actual observed SMICA_FULL Q/U native map is NESTED, source SHA256 60952c645eb33d151905ddf5837477e15ca02a3261feca4ceca3c3feece4f9ac. Official common PMASK, HM and OE polarization-missing masks were intersected at NSIDE2048 then reduced NESTED -> NSIDE64 RING; select precisely 30,021 polarization pixels (not the temperature 26,846 pixels).

New pixel transformer first converts each chosen nside64 RING parent to its NESTED parent index, enumerates exactly 1024 native NESTED children, then converts those child pixels to RING for source FITS sampling. Precompute selected 30,021×1024 int32 positions and bool mask, not a full 50-million-pixel matrix per simulation. All selected native fine samples are accumulated in float64 with per-parent source counts.

Independent validation: the first FFP10 CMB intensity map ID00000 reduced with NO polarization mask matches the previously registered PR150 K1 temperature cache on the same coarse selected pixels with max absolute residual 5.684341886e-14 microK. Small-grid direct RING->NESTED synthetic parent average and spin2 E/B injection tests pass. The only initial test failure was an expected float32 accumulation mismatch to healpy.ud_grade; independent exact double-precision parent averages agree and float32 tolerance is separately scoped.

## Theoretical same-sky and noise identities

For any common source linear spin2 mask operator R, a_s=R s, a_n=R n and a_pair=a_s+a_n. For each ell, the finite low-ell orthonormal real spin coefficient gives

  C_l(pair)=C_l(signal)+C_l(noise)+2 a_s(l) dot a_n(l)/(2l+1).

Actual 12 paired realizations satisfy this C_l identity to 2.493665e-17 microK² maximum absolute residual.

For two correlated split noises n1,n2, their half difference d=(n1-n2)/2 and mean nbar=(n1+n2)/2 have

  C_d=(C11+C22-C12-C21)/4,
  C_nbar=(C11+C22+C12+C21)/4,
  C_nbar-C_d=(C12+C21)/2.

Wolfram exact symbolic check and two Python PSD covariance regressions pass. HM/OE half-difference covariance must not replace mean noise covariance when cross-split noise correlation is unresolved. The eight Planck processed HM/OE/NILC/SMICA outputs remain ONE physical sky.

## Actual 12+12 source-cohort result

Raw CMB mc00000..00011 and noise mc00000..00011, unique source IDs, matching IDs paired 1:1. All 24 native full FITS file SHA-256 hashes are computed and preserved in the result JSON. Only the first 12 of 999 and 12 of 300 are run; DO NOT call this a full FFP10 null.

Finite masked source E/B real harmonic l2..5 (64D) in microK²:

| Band | Actual SMICA_FULL | CMB-only median 12 | Noise-only median 12 | Paired median 12 |
|---|---:|---:|---:|---:|
| C2_EE | .088112235 | .023874648 | .021884756 | .044152184 |
| C2_BB | .095676553 | .000343826 | .019789533 | .018982932 |
| C3_EE | .026899198 | .029773203 | .012612947 | .043486311 |
| C3_BB | .008281592 | .000773886 | .008178141 | .008007026 |

The actual SMICA_FULL C2_BB .095676553 is larger than the largest paired pilot C2_BB .040498925 microK². Descriptive comparison ONLY: NOT a primordial B-mode detection or Planck anomaly p. End-to-end simulation-vs-observed exchangeability, missing frame/polarization convention, foreground residuals, beam/filter/high-mode transfer and selection of the tail after examining data remain unqualified. If exchangeability had independently been established, 12 simulations still only have finite rank tail resolution 1/13 = .076923, insufficient for small p. No actual observed HM/OE full-mission split noise null is calibrated by only the full mission FFP10 noise bank.

The 64D noise empirical covariance rank is 11 and must not be inverted as a full Planck likelihood. The source coefficients live in result/paired_coefficients_lowell.npz, not gigantic raw FITS committed to Git. Source conditional output has per-realization band powers, file SHAs, ID, header frame flags, and exact quadratic cross term.

Source original 2+2 smoke and full 12+12 first two source samples are bit-identical for CMB, noise and paired 64D coefficients. The 24 SHA-256 file identities, source picker and correct pixel-frame matching are retained. Peak measured RSS 1,735,976 KiB (~1.66 GiB), execution 165.4 s (24 full hashes and 24 raw-Q/U projections); OpenBLAS 2 threads. This benchmark is not a verified full 1,299-source scaling estimate.

## Implementation and references

- htt/obsstat/planck_ffp10_polarized_lowell.py: source-pixel mapping, masked float64 parent aggregation, raw source header validation, physical spin2 masks, same-sky contrasts, rank-aware noise and HM/OE covariance formula.
- scripts/run_htt_planck_ffp10_polar_pilot.py: exact source read-only 12+12 pilot, create-only output, raw SHA-256.
- scripts/plot_htt_ffp10_polar_pilot.py: four-band descriptive signal-only/noise-only/paired source comparison, no p.
- tests/obsstat/test_planck_ffp10_polarized_lowell.py: six synthetic source consistency tests and exact covariance checks.
- tests/obsstat/test_ffp10_polar_pilot_source_acceptance.py: actual source identity, first2 replay, rank and physical-null HOLD tests.
- results/L01_FFP10_QU_12pair_hashed/{result.json,DESCRIPTIVE_SUMMARY.json,observed_FFP10_polarization_four_bands.png,paired_coefficients_lowell.npz,REPORT_KO.md}.
- results/L01_FFP10_QU_2pair_SMOKE: independent 2+2 numerical source replay.
- Primary: Planck 2018 IV, A&A 641 A4 https://doi.org/10.1051/0004-6361/201833881 ; Planck 2018 VII, A&A 641 A7 https://doi.org/10.1051/0004-6361/201935201 .

## Scope admission and next research

L01 makes real source/pixel/cohort progress; it is NOT complete because physical frame/beam/foreground and matched end-to-end source quality are still unqualified. L03 physical Planck null also remains BLOCKED. In the six-paper DAG P1/P3/P4/P5/P6 statuses remain unchanged. No physical BB quadrupole anomaly score, Q posterior, Bianchi family odds or published manuscript is admitted.

Next constructive unit: recover original Planck FFP10 and SMICA polarization coordinate/sign convention from first-party source release to bind observed and simulated physical spin chart. Then derive actual split-specific HM/OE polarized noise/foreground model and run a genuinely disjoint calibrated null with larger unique cohort and declared look-elsewhere/trial family. Raw FFP10 kept; do not delete. Other active repos rec_bianchi one-event screen transform and rei_bianchi frozen-gas quadrature were inspected earlier; neither is a native Planck sky likelihood.
