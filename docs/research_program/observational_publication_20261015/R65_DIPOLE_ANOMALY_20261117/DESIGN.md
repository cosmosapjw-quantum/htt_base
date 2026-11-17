# R65: a finite dipole-anomaly investigation

Baseline d76ef3a4e9b33c4703a02647b3aa850004d04253. Branch research/r65-dipole-anomaly-20261117.
Question: which signed number-count dipole components survive explicitly admitted
declination selection and angular-morphology nuisance, and what do modern released
radio inference products say about the same transverse directions?

## R1–R4 decision before new science fits

This is one owner-selected ten-stage integrated theory/coding study, an additive
P4 companion. Original42 nodes and P4 acceptances are preserved. Earlier L2/R54/R60
count results and R63 source-normalization obligations remain distinguishable.
R54's existing 573-PR inventory is reused; R2 inspected the relevant source code,
data identities and superseding results, not every PR diff anew.

Three possible routes were evaluated. CMB aberration plus remote kSZ needs an
owned full-vector law/source normalization absent from current carriers. Quaia
has useful aggregate data, but no qualified incremental magnitude-bin selection
map; subtracting completeness maps is invalid. NVSS has source rows and a precise
declination nuisance, and the October2026 RACS release now has weighted joint
posteriors. The finite selected route uses those two actual carriers.

## Locked observed NVSS experiment

Source: existing NRAO CATALOG.FIT. PEAK INT is Jy/beam, not integrated Jy.
Use disjoint peak-intensity bins [20,40),[40,80),[80,infinity) mJy/beam.
Coordinates are ICRS/J2000 sourceward unit vectors. c=299792.458 km/s; beta=v/c.
Catalogue rows are binned in RING HEALPix; cuts operate on retained pixel centres,
and all sources in each retained pixel enter its count. Source masks and this
pixel-centre mask are distinct, recorded constructions.

Primary geometry: NSIDE64, pixel dec>-37deg, |Galactic b|>10deg.
Prespecified sensitivity geometries: NSIDE32 with the same cuts; NSIDE64 with
|b|>20deg; NSIDE64 with the base cuts plus the three Wagenveld sky boxes and
conservative whole-pixel excision of every disc intersecting radius0.3deg around
catalogue peak>=2.5Jy/beam sources. The bright-source criterion is a peak proxy,
and is a diagnostic, not exact replay of a published total-flux mask.

Fit each geometry with (a) transverse log dipole and (b) transverse log dipole
plus four non-axisymmetric orthonormal-STF quadrupole components. Each bin has
its own ring totals and nuisance morphology. Fixed ring exposure is uniform over
retained equal-area pixels; arbitrary RA-dependent selection is not eliminated.
No empirical variance is assigned to the omitted axial dipole. The m=0 dipole
and quadrupole are exact nulls of the discrete loglinear experiment.

The physical linear-density dipole 1+d.n is a different model: for nonzero
transverse dipole it can have second-order dz sensitivity. This study proves no
all-orders physical no-go. NSIDE change tests a particular discretization
sensitivity; it does not validate the entire selection or astrophysical null.

## Fixed comparisons and probability laws

Within each geometry and morphology model, retain all signed bin coefficients,
the full per-bin covariance, and the exact conditional partition functions.
Compare independent bin dipoles with a common two-vector (nested df4 test).
For the primary dipole+STF fit, simulate512 conditional multinomial catalogues
under the fitted common-vector null, refitting identical nuisance models. This
calibrates a conditional Poisson working question, not cosmological LSS.

Compare the exact conditional MLE with the matched one-step Fisher score under
the same support/nuisance: this conventional baseline is not claimed to contain
less information. Quantify quadrupole profiling, signed covariance, correlated
flux-path contrasts and discretization/mask changes. Report Pearson overdispersion
as an adequacy diagnostic, without pretending a scalar rescaling models LSS.

An explicitly conditional unresolved-source/peak-proxy response can be explored:
k_b=2+(1+alpha)[S_lo n(S_lo)-S_hi n(S_hi)]/N_b, alpha=.5,.75,1.
Estimate boundary log-density with prespecified symmetric log half-width0.10
and retain counts and units; response is held fixed in each working fit.
Compare shared beta and fixed CMB template with the independent-bin model.
Common-u and shared-beta models are nonnested when k varies: never give their
likelihood difference a Wilks df. These response fits are not physical speed
measurements because source size, peak extraction and spectral response remain
unqualified. Measured dipoles and conditional response diagnostics are reported
separately. No scan-selected best cut or largest significance is the headline.

No per-bin NVSS radial distributions/bias or cross-bin cosmological covariance
have been supplied. Disjoint events remove Poisson overlap, not LSS covariance.
The inherited aggregate C1 and R60 covariance interpolation do not solve this
input and will not be repackaged as new results. No joint NVSS–RACS p-value is
formed from independent-error assumptions.

## RACS data reuse

Released inference_products.zip v1.0.0, SHA256
143cdcf32d85479ee171c8d5bc5da814178dd7123024ba12e5b5d9f9b9c94fc7,
32,883,631bytes. Use low3/mid1 fiducial, no-clustering and no-temperature chains;
verify nested archive identity, preserve nested weights, actual priors and source
model metadata. observer_speed is v/(369.82km/s), direction is Galactic degrees.
Transform the full vector to ICRS and retain xy, CMB-parallel/perpendicular
projections, full weighted covariance and nuisance correlations. This is a
pushforward of a released source-conditional posterior, not a new likelihood,
new RACS fit, independent bootstrap or new survey observation. Source multiplicity
in its pseudo-clustering model is not a full cosmological cross-survey LSS law.

## Five-variable role and novelty gate

Use canonical (x,Q,Pi,F,G_F). x keeps the signed vector/STF carrier and its exact
conditional likelihood. Q is a statistical reference ellipsoid with no physical
MES claim. Pi states its null/posterior/working-law identity. F keeps simultaneous
support and antipodes. G_F retains the common level and signed adjacent-bin
contrasts with full transformed covariance. A flux path is not a time derivative.
Five views are pushforwards of one experiment, not independent factors.

Ellis–Baldwin1984, Rubart–Schwarz2013 and Siewert etal2021 already give radio
dipole/2D declination-resistant methods. Takeuchi2026 gives general selection
response; Mittal–Lewis2026 gives disjoint-flux fitting. Conditioning, score/Fisher,
Schur profiling and invertible covariance transport are standard mathematics.
Potential publication contribution is the actual source-specific joint
morphology/calibration result, supported components and measured information
change, plus careful modern released-posterior comparison. Do not claim a new
cosmological anomaly, universal obstruction or estimator priority from this loop.

## Completion and stopping rule

Complete actual code, semantic checks, the fixed data experiments, one fresh
independent final review, one bounded correction episode if needed, a finite
paper plan, additive DAG update and authorized non-force branch publication.
Report the observed novelty decision. Do not launch another loop or write a local
coding-agent restart prompt. Source qualification obligations remain concrete
future paper gates rather than fictitious completed measurements.
