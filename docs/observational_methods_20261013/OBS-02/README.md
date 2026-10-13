# OBS-02 catalogue-conditioned CF4 sensitivity

Implemented local sensitivity for 38,053 unique grouped rows. Table4 provides DMzp, e_DMzp, heliocentric Vh and J2000 directions; table3 supplies boolean method presence only. No response coefficient is fitted. No table3 distance or CMB-corrected velocity enters the diagnostic.

At fixed H=70 km/s/Mpc and zero intercept, bulk, expansion dipole and STF coefficients, fixed-calibration scenarios have numerical rank 13. Free common calibration gives rank 12. Absolute H then has an unbounded null direction and its standard error is returned as `null`, never as a finite pseudoinverse error. At this isotropic fiducial the scale tangent has delta H=H epsilon and delta kappa=a epsilon, paired with delta ln dA=-epsilon. At general nonzero expansion coefficients the full nine-dimensional expansion block scales together; the reported directional/H contrasts are local derivatives at the declared zero-anisotropy fiducial.

Declared redshift/source-motion sigmas are 30/150 or 100/300 km/s, with published e_DMzp for marginal modulus uncertainty. They are sensitivity scenarios, not measured covariance. Each group has a 3-by-2 latent Jacobian in (ln dA,z_true); the whitened left-null vector profiles that small block exactly at the linearization. The source-motion pseudo residual is a model noise penalty, not an additional observation. Optional free calibration offsets follow boolean method presence, not unobserved fractional method weights. Only thin designs and small matrices are formed.

The plot compares nuisance-projected singular spectra using fixed physical coefficient scales: 1000 km/s for intercept/bulk, 100 km/s/Mpc for expansion coefficients. Method deletion excludes every group possessing that method; it is footprint exclusion and never recomputes DMzp. Depth deletions use baseline fiducial dA, with full/central 49–51 percent and nearest/farthest-quartile deletion masks. Results share observations and are not independent repeated measurements. The package uniform dL geometry is reused as historical evidence, not equated with this latent/noise diagnostic.

`information.json` records source SHA256s, scenarios, fiducial, masks, selected-group identities, STF coefficient/covariance crosswalk, singular values and only estimable contrast sensitivities. Selection is `SELECTION_LAW_NOT_BOUND`. Physical rank and scientific admission remain `HOLD`; distance uncertainty is treated only to first order and broad errors limit that approximation. Full measured covariance, real selection normalization and physical response/remainder bridges are still absent.

Commands, both exit 0:

```sh
PYTHONPATH=htt:htt/htt:htt/src OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python -m pytest tests/htt/test_cf4_information.py tests/obsstat/test_cf4_grouped_observations.py -q
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python scripts/cf4_information_diagnostic.py
```

Twelve targeted tests cover finite-difference latent derivatives, tiny dense Schur parity, calibration scale null and rejection of finite null uncertainty, masks/scales, STF covariance crosswalk, parser identity/domain errors and optional trailing method fields. Raw first failures are preserved beside final stdout/stderr. The covariance-crosswalk test initially used zero absolute tolerance against floating zero; its first output shows 5e-17 roundoff and the final test uses 1e-14 absolute tolerance. The first catalogue run rejected legitimately omitted trailing optional fields; padding is restricted to the table3 metadata reader. The final runtime emits a matplotlib Axes3D warning; the generated plots are two-dimensional.

Owner: HTT inference and obsstat parsing. Transfer source: none. Evidence type: targeted tests and generated diagnostic. Requested executor: gpt-6.1-sol/medium; observed runtime identity: UNKNOWN. Independent review found two numerical defects and one local-fixture dependency; one bounded repair is complete and independent closeout is pending. No commit or publication performed by this implementation worker.

Bounded review repair: rank tolerance now retains the preprojection scaled signal norm with an explicit 8*eps*max-dimension projection roundoff bound, and rank is capped by the remaining residual row dimension. Completely confounded signals cannot promote cancellation roundoff into finite information. Contrast estimability uses normalized nonzero contrast direction, with an explicit zero-contrast case. The parser unit test now uses a self-contained frozen CDS schema excerpt. Twelve tests pass; the real 44-comparison diagnostic reran successfully. Pre-repair outputs/source identities and reproduced first counterexamples remain preserved. Final repair logs are `repair.tests.stdout` and `repair.run.stdout`.
