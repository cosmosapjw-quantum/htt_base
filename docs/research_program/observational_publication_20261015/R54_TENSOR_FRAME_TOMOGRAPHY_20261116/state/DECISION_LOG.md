# R54 decision log (2026-11-16)

| id | lane | decision | executed result | next action |
|---|---|---|---|---|
| H-C1 | CORE | PROMOTE | tests/r54 pass; ties GLS by construction (R53 theorem retained); the F view is UNAVAILABLE on both low-redshift lanes because an axis scan is not a support functional | use as the reporting layer of every lane; no novelty claim |
| H-C2 | CORE | REJECT | R53: Fisher-distance ratio 1.0000, coverage tie | never claim gain; claim typed interpretation only |
| H-C3 | CORE | HOLD | pooled chi2(A)=10.4/9 vs chi2(V)=16.2/9; after method monopoles 6.67 vs 7.26 | R54-L04 |
| H-L1a | L1 | PROMOTE | r_E(perfect fluid)=0.0711; reionization share 19%; R54-L01: masked E response e_dev = 0.0003 (IDEAL_E_RESPONSE_KEPT) | R54-L07 literature check (B09) |
| H-L1b | L1 | PROMOTE | 95% illustration values of |s0|: 1.42e-10 (perfect fluid, T+E), 6.66e-08 (massless two-mode family), 3.43e-08 (minimal normal ordering) | R54-L07 literature check |
| H-L1c | L1 | REJECT | B ell=2 tail p=9.54e-06 (SMICA), 3.96e-07 (Commander); observed rms 0.30 vs FFP10 0.11 uK; R54-L01 empirical LOO B ell=2 tail 0.00664 (SMICA), 0.00332 (Commander); E lane DIAGNOSTIC; R54-L02 adopted-covariance B ell=2 null passes in: Cosmoglobe_BeyondPlanck, Planck_PR3, WMAP9; E lane CLAIMABLE | R54-L06 (T lane; E lane as recorded) |
| H-L1d | L1 | REJECT | ell >= 3 modes enter only through covariance | family comparison beyond type I remains blocked on a source-bound transfer |
| H-L2a | L2 | REJECT | excess tails p=0.27 (Quaia), 0.46 (NVSS); common excess p=0.12; no decision at this power; R54-L03 calibrated excess tails 0.309 (Quaia), 0.421 (NVSS); H-L2a stays REJECTED for the owned estimators; R54-L03 decision check: H-L2a stays REJECTED for the owned estimators (calibrated covariance; REJECT holds for the owned estimators only) | none for the owned estimators; R54-L06 tilt closure uses the calibrated count covariance |
| H-L2b | L2 | HOLD | no number yet | R54-L03 |
| H-L2c | L2 | REOPEN | tilt closure V_CF4 + c beta_excess = 0: p=0.0895 (V only), 0.0123 (constant dipole marginalised); count side preliminary | R54-L03, R54-L06 |
| H-L3a | L3 | PROMOTE | no column added in R54 | state as an identifiability result |
| H-L3b | L3 | PROMOTE | per-family hemisphere steps are mutually consistent (p=0.867), as are the per-method dipoles (p=0.198); the common dipole itself has Wald p=0.43 | R54-L04, R54-L06 |
| H-L3c | L3 | REJECT | for a shear confined to z < 0.2 the T functional bounds a constant-sign history at 0.000227 and is blind to a sign-changing one; the E functional bounds its rms at 0.0735 (diagnostic lane; 0.0972 with the B-null floor), above the CF4 quadrupole of 2.5% of H | replaced by H-L3d |
| H-L3d | L3 | PROMOTE | late-time rms bound from E: 0.0735 (z < 0.2), 0.0113 (z < 0.5), 0.000697 (z < 2) | R54-L06 quotes the condition with every use |
| H-L4a | L4 | HOLD | CF4 constant quadrupole 2.5% of H, principal axis 9.5 deg from the equatorial pole (log estimator, exact body); family identification blocked | R54-L04, R54-L06 |
| H-L5a | L5 | REJECT | inner windows joint p=0.00558 (dipole 0.0375), outer windows joint p=3.89e-06 (dipole 0.000123); FP is 98% of the groups at z >= 0.055 and 95% of that FP sample is northern; R54-L04 decision check: REJECT (step class UNRESOLVED; robust class DEPENDS_ON_ZERO_POINT_NUISANCE_MODEL) | none (rejected by the R54-L04 decision check) |
| H-L5f | L5 | PROMOTE | R36 operator reproduced from the committed source rows; log estimator unbiased in the unit test | use R54-EQ-34 everywhere; CF4 numbers of R36, H03 and R52 are superseded |
| H-L5g | L5 | HOLD | common step -1.66 +- 0.53% of H; common-dipole Wald p=0.43; R54-L04 decision check: HOLD (step class UNRESOLVED; robust class DEPENDS_ON_ZERO_POINT_NUISANCE_MODEL) | R54-L06 joint tomography |
| H-L5c | L5 | HOLD | first pass (ideal-sky body, linear estimator): 2.8 deg, sky fraction 0.0005; after the estimator bias is subtracted the sky fraction is 0.0755; class by nuisance model: EXCESS_NOT_POLE_LOCKED / UNRESOLVED_POLE_LOCKED / LCDM_BODY_COMPATIBLE; R54-L04 decision check: HOLD (step class UNRESOLVED; robust class DEPENDS_ON_ZERO_POINT_NUISANCE_MODEL) | R54-L06 joint tomography |
| H-L5h | L5 | HOLD | 2.5% of H; R54-L04 decision check: HOLD (step class UNRESOLVED; robust class DEPENDS_ON_ZERO_POINT_NUISANCE_MODEL) | R54-L06 joint tomography |
| H-L5e | L5 | REJECT | joint null p from 0.000344 (pooled) to 0.112 (method x hemisphere steps marginalised); class DEPENDS_ON_ZERO_POINT_NUISANCE_MODEL | do not claim |
| H-L6a | L6 | HOLD | delta chi2 (V - A) = 5.8 pooled, 0.592 after method monopoles | R54-L04, R54-L06 |
| H-L6b | L6 | HOLD | velocity term after the constant term: Wald 5.42/3; closure p=0.0895 / 0.0123 (preliminary) | R54-L03, R54-L06 |
| H-L6c | L6 | HOLD | not executed; E21 and E22 enter R54-L06 as published anchors with their covariance | no new estimator; anchors only |
