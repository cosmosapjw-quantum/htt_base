# CF4 source-law execution, C1–C8

Derived maps, conventions, assumptions and proofs are in THEORY_CF4.md at the theory checkpoint 575ff4811b6a5ae12d7c14bf7cd8ecadef7e58aa. C1–C8 implements comparisons on the same 35,970 groups in the R98 four-window design. The check against R98 is a paired change of units in one component of the covariance. The three other transport calculations are distinct choices of the indicator observable.

## Production entry point and evidence

Run in the primary repository checkout:

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -B -m scripts.r99.cf4_source_law
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -B -m pytest -p no:cacheprovider -q tests/obsstat/test_r99_cf4_source_law.py
```

The producer completed with exit 0 (28.39 s). The focused suite gave 11 passed in 1.15 s. Python 3.12.3, NumPy 2.5.4, SciPy 1.18.1 and FINUFFT 2.5.0 were used; native FINUFFT threads and all requested BLAS/OpenMP thread counts were one. Inputs were read from R98/R30 paths and the mounted target inventory, with identity comparisons against the archived result. The JSON contains hashes of the actual data, operator grid, predecessor code and source-law code.

|Deliverable|SHA-256|
|---|---|
|scripts/r99/cf4_source_law.py|11c0369c379efcf1d7873affbb5d0ff208cfeceebd0cd28806677b94b7dfc831|
|tests/obsstat/test_r99_cf4_source_law.py|f4488e24df9731efe0218d21b7973c52c42e738918868c9f131bac3adb75f012|
|CF4_RESULTS.json|9e52eff735227df05445a757e995fc1c56119f8979bbcac254b0c24e8480baeb|

## C2–C6. Paired repair and numerical implementation

The code binds the sorted group IDs and modulus to the H03 source, re-creates the R98 window estimators and reproduces the four fitted means. The magnitude tilt experiment keeps the depth design and weight matrix fixed while refitting all 35,970 shifted source moduli. Its observed maximum coefficient change was 0.006797015. The typed magnitude Jacobian predicted this change to 4.94e−16; the historical additive log-distance tilt gives a discrepancy of 0.02155654 in the same experiment. The seven-column covariance trace changes from 0.006579350 to 0.001395322. Boundary trace 0.0000529972 and calibration trace 0.006559248 were computed separately.

The original R=5 WF model with 150 km/s diagonal dispersion and its 18-dimensional inner-to-outer prediction were replayed to a maximum absolute difference of 3.04e−13 in log density/chi-square. Changing only the units of the 0.05-mag tilt gives:

|Matched R=5 covariance|Predictive chi-square|Log predictive density (nat)|
|---|---:|---:|
|Historical numeric log-distance tilt|11.99528442|64.56989644|
|Magnitude tilt as specified|12.11632063|65.69895559|

Both covariance scores refer to overlapping windows of the same registered catalogue. An improved density in this exercise is not an external calibration measurement.

## C7–C8. Finite-distance transport and validation

Assume the R30 flat background and R=5 Mpc/h Gaussian smoothing. The latent shared velocity uses the R98 EH98 no-wiggle band [0.005,0.05] h/Mpc, Kaiser linear growth and the observed-redshift fiducial source positions. A 150 km/s independent Gaussian dispersion enters the latent variable once. Total latent standard deviation ranges from 247.68 to 248.50 km/s. The largest one-point upper-tail mass removed by the rapidity marginal cut is 9.91e−34 on this cohort. The positive-background support and the Gaussian copula are explicit assumptions. Their combination does not implement the joint-truncated correlated Gaussian prior of a different latent-population model.

All three typed finite maps were evaluated on every source; probabilists' Hermite orders 16 and 32 agreed within 1.89e−15 in absolute coefficient/moment units. At fixed observed redshift the centered ±1 km/s derivative has max relative difference 3.78e−8 from its analytic expression. Input observable type changes the sign of the finite source-Doppler contribution; the term cancels for the native comoving definition. The code stores the full 36D projected mean, 36×36 first-chaos velocity covariance and 36 diagonal upper bounds on the omitted nonlinear variance for each type. With constant-zero-mean underlying rapidities to numerical precision, the three means coincide to roundoff and their largest absolute projected mean is 0.00074118.

|Hypothesized estimator|Coherent first-chaos trace|Independent first-chaos trace|Largest source fraction of variance above order 1|Largest projected residual bound / first-chaos variance, coordinatewise|
|---|---:|---:|---:|---:|
|Background luminosity proxy|0.00348513|0.00002051|0.34786%|4.5836%|
|Native comoving log ratio (natural log)|0.00326311|0.00001879|0.35473%|4.7833%|
|Bolometric flux in the assumed observer frame|0.00305041|0.00001717|0.36180%|4.9961%|

Each projection reused all 39,282 frequencies/directions without forming a source-by-source full covariance. The largest direct check on the sampled modes was 2.07e−13 relative. Stage B vs C radial quadrature discrepancy was at most 1.05e−11 relative in covariance Frobenius norm across the three transports. The 20-source geometry check directly evaluated the angular Fourier factors and separately used the existing closed isotropic longitudinal/transverse velocity kernel. It gave relative Frobenius deviation 1.91e−6, max absolute 0.103 (km/s)² and relative diagonal discrepancy 1.85e−8. The independent test uses matched R30 power and h-unit conversion; no stochastic small-scale or magnitude term belongs in that cosmological pair check.

The smoothed **one-point linear velocity variance** integrated over [0.0001,1] h/Mpc has 2.659% below the inherited band, 55.763% inside and 41.578% above. These fractions depend on the chosen h units, window, integration interval and power prescription. A given coefficient or cross-window covariance has a different angular and radial window, and dynamically nonlinear velocity contributions require their own source model.

## D01/D02 scope and likelihood evidence

The selected-Gaussian/probit utility computes native-mark likelihood numerator and inclusion denominator before averaging over the pre-selection shared field. A two-target test numerically integrated the original probability density with two alternative field values. The joint result agrees with that independent integral; replacing the field prior by fixed pre-selection weights *after* individual conditional normalization fails this test. Other tests cover zero and finite radial shifts, units/sign, the physical positive-distance boundary, invalid density parameters, sharp event bound witnesses, two-source correlated Gaussian covariance and the projected residual inequality.

An explicitly hypothetical registered-mark scenario ran on all 35,970 groups. Its marks were treated as bolometric with measurement standard deviations from released modulus errors; common fields ±100 km/s have equal pre-selection probability; per-target probit limit is fiducial FLRW modulus +0.5 mag and softness is 0.25 mag. Its joint selected density was −27424.19947 log units versus −27060.95186 for zero field. Requiring **all identified targets** to be included reweights the field extremely strongly in this artificial design. The mixtures do not describe the historical survey selection. On the pooled descriptive event “released modulus above its fiducial background value” the observed fraction is 0.49619. A stipulated full-support relative inverse-inclusion range of 2 gives the sharp bounds [0.32996,0.66327]. The bound has no population interpretation if unseen strata or completely excluded mark regions have unrestricted mass.

Qualified upstream multi-indicator calibration/holdout (D01), actual rejected-target or validated native inclusion law (D02), and source-matched full-spectrum dynamics/likelihood (M01) remain open. The producer provides a conditional catalogue prediction and three velocity moment scenarios. Physical Pi remains null, and the original 42 publication gates retain their states.

A second full run of the identical production command exited 0 in 28.41 s and reproduced the JSON byte-for-byte at SHA-256 9e52eff735227df05445a757e995fc1c56119f8979bbcac254b0c24e8480baeb.

## C9 targeted repair: zero-variance source

Independent review reproduced an input-domain mismatch in the original Hermite helper. The theory defines deterministic sources at zero velocity dispersion, whereas the first implementation rejected them before quadrature. All 35,970 original production rows had strictly positive dispersion. The original file hashes and the two byte-identical C8 runs above document the pre-repair implementation.

The helper now returns exactly zero for all four moments and all three observable types on zero-dispersion sources. It quadratures only positive-dispersion sources in mixed inputs. A regression checks all-zero and mixed vectors, identical results on the positive subset, zero outputs without floating-point division warnings, and rejection of negative and nonfinite dispersions. The same targeted pytest command now reports 12 passed in 1.19 s.

The full producer embeds its own code SHA, so it was re-executed through its normal module entry point with one thread (exit 0, 29.32 s). A direct comparison parsed the saved original JSON and the new result, removed only inputs_sha256.R99_code from each, and asserted exact structural equality of every remaining field, including all arrays and all scientific values. Updated code, test and result SHA-256 values are, respectively:

- scripts/r99/cf4_source_law.py: 058084e07ef086bb0bc2dcaa3a38fb78d986265b3ba45f0116ec1ebbb4efed66
- tests/obsstat/test_r99_cf4_source_law.py: 4d685fc674942aebf352e65824ccf831a577f15accdf7844f0d4b8a8a3114ae4
- CF4_RESULTS.json: 89b52693582041ebc07308edb0773a88ed15c5e1d5876fedf120b9564e4a15eb
