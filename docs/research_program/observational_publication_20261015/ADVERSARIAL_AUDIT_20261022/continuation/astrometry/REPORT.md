# A22-05 — reported-redshift E/B and common-field nuisance experiment

Owner HTT; C0 CONDITIONAL_GAUSSIAN_EXPERIMENT; transfer none. Base d256ed4669b1ded62fa0db606929af108160ccf6.
New input: reviewed full755850-row Quaia/Gaia joint PM-covariance cache from A22-03.
New model:18 redshift-bin Cartesian E1/B1 coefficients, common l2/l3 vector modes
and seven spatial-selection-template dipole fields. Next consumers K03/K04/K05.
Independent read-only review: scoped PASS (see INDEPENDENT_REVIEW.md).
Physical original-node acceptance remains HOLD.

## Frozen experiment and actual inputs

[CONFIG.json](CONFIG.json) precedes score generation. Reported z bins [0,1),[1,2),
[2,10) contain200785/369335/185730sources. These are photometric reported-redshift
cohorts; neither precise physical distance bins nor a catastrophic-redshift model.
Every Quaia row is used, including63696outside the previously retained CRF3 cache.
No extra CRF3 membership cut or inverse relative-selection weights are applied.
Source PM/errors convert mas/yr to microas/yr once; pmra is mu_alpha*cos(delta).
Actual pmra_pmdec_corr enters each positive-definite2x2 source covariance block.
The checked input cache SHA-256 is4cd83b1e8bb9f71f89aacfc2db5daba87f9a79f2af8ccd2e7e94b0be57252dae.

E1=T*g and physical B1=T*(omega cross n), ICRS east/north components. Generic VSH
uses E=angular-gradient real Condon–Shortley harmonics, B=n cross E; this has the
opposite l1 B sign from the physical omega convention. l2/l3 complete E/B sets
are full-sky unit RMS per column. Seven producer templates are centered/scaled
on all49152equal-area ICRS/RING NSIDE64pixels and multiplied by the six physical
dipoles; each resulting vector column has unit full-sky RMS. They are not
orthogonalized against the signal or turned into inclusion probabilities.

For d=D*g+H*a+epsilon, epsilon~N(0,N), a~N(0,P), the declared covariance is
C=N+H*P*H^T. Angular blocks have P=tau_A²/q_A I (q_A=10or24); template blocks
P=tau_T²/42 I. Independent source PM blocks form N. The32declared models combine
lmax2/3 with tau_A,tau_T in{0,10,30,100}microas/yr. Each tau is total expected
field RMS, not each coefficient's standard deviation. A proper signal prior
N(0,100²I18) and uniform32-model hyperprior define normalized model mixing.
These are declared sensitivity choices, not empirically bounded covariance laws.

[Lindegren et al. §5.6](https://arxiv.org/html/2012.03380) gives angular covariance
scale context, and [Gaia-CRF3](https://arxiv.org/html/2204.12574) documents higher
E/B structure. Neither source proves this finite family brackets Gaia systematics.
Cross-source classifier and calibration dependence remain unqualified. The output
mixture weights are conditional on the declared family, not empirical model odds.

Woodbury integration uses an explicit PSD prior factor L and
R=L*(I+L^T*G*L)^(-1)*L^T, G=Z^T*N^(-1)*Z. Zero prior modes are exact zero.
Gaussian determinant terms and proper signal prior are included before mixing;
common d^T*N^(-1)*d/logdetN terms cancel only across this same-data family.
Mixture covariance includes both within- and between-model terms. GLS with known
nuisance covariance is also emitted separately. Cross-bin differences use the
full18x18covariance. Exact Gaussian-mixture coordinate quantiles are stored;
plotted +/-1.96moment-SD bars are explicitly moment intervals.

## Results and an explicit failure of robustness

The full scaled84-column Gram has numerical rank84, smallest/largest eigenvalues
1.08528e-5/6.69041; the threshold is relative1e-10 on the scaled Gram. This is
normal-equation precision, not a raw-design singular-value claim. Conditional
scaled signal-information condition numbers span2.03..91.37. Local and cosmic
common E1 columns duplicate:6columns have rank3 and null(delta,-delta). B1 retains
the frame-spin degeneracy. These statistics do not identify cosmic acceleration.

Full-cohort E1 posterior means (x,y,z), microas/yr:

| reported-z | mean E1 | marginal moment SD |
|---|---|---|
|0..1|(1.685,-3.036,-5.012)|(1.249,1.295,1.340)|
|1..2|(.104,-4.200,-4.045)|(1.237,1.286,1.333)|
|2..10|(1.840,-3.464,-4.992)|(1.344,1.370,1.421)|

Low-minus-high E1=(-.1553,.4281,-.0200)microas/yr; its full3x3covariance is emitted. Exact mixture intervals for the18
individual signal coordinates (not for this contrast) are in [RESULT.json](RESULT.json). Conditional family weight
is .28646 on(lmax3,tau_A10,tau_T10) and .71354 on(3,10,30); other weight is tiny.
The prior/field/selection choices must accompany any use of these values.

Quaia applies measured-PM cut r(G)=1000*10^(.4*(G-18.25))microas/yr. The producer
code/Eq in the paper disagree with a nearby prose example; A22-03 preserves this.
On the compact domain ||g_bin||<=100, mean tangential norm <=100*sqrt(2). For the
largest per-source marginal covariance eigenvalue lambda_i, Gaussian radial-tail
and union bounds give Q=sum exp[-(r_i-b_i)_+²/(2lambda_i)], and if Q<1 then
0<=-log A_cut<=-log(1-Q). Dependence among sources does not invalidate this union
bound. This is only the known radial-cut factor, not classifier selection.

A second cohort is selected solely by G/errors/design, requiring each worst-grid
margin sufficient for n0/.01. It retains558407sources (134766/279241/144400), with
Q=.00025656685694 and -log A_cut<=.0002565998. Full-cohort Q=3729.22 gives no useful
bound. Margin-cohort E1 means are(3.329,-4.646,-3.972),(-.382,-6.210,-2.696),
(2.205,-5.249,-4.052). Different cohorts differ conditionally; the bounded-cut
factor does not certify the untruncated working posterior or its unbounded prior
tails. Unknown classifier selection remains in both cohorts.

Whole-field Gaussian mocks draw shared field coefficients and score noise, using
score covariance G; no iid-source bootstrap. Twelve known-covariance joint18
coverage cases use1024draws each and give .93652..95898, with exact binomial95
intervals retained. The actual finite-mixture prior-predictive coordinate coverage
uses2048draws and is .94775/.95557/.95654 for low/mid/high Ex. This is calibration
under the declared Gaussian experiment, not empirical Gaia selection coverage.

Misspecification controls with1024draws each show:

| omitted/changed field | joint18 coverage |
|---|---:|
|l4 E/B RMS12microas/yr omitted|.28418|
|unequal E/B at same total RMS|.96387|
|template-correlated mean100microas/yr|0|

For omitted l4 the exact95binomial interval is[.25672,.31289]; for template mean
it is[0,.003596]. Poor coverage is preserved as a failed robustness control.
It prevents presenting the narrow conditional intervals as empirical coverage.

## Validation, replay and limits

Six focused tests passed: small dense-C/Woodbury means/covariances/determinants,
non-diagonal PSD and zero priors, basis transport, score root/chunk-order checks,
full-sky VSH quadrature, donor dipole equivalence, radial bound and singular design.
First test run had5PASS/1FAIL: a covariance reference subtracted two ~10000-scale
matrices, producing maxabs3.34043149e-9/maxrel8.56857535e-7 cancellation error. The
reference was replaced by direct active-prior precision solve; tolerances stayed
unchanged. Dense observation-space mean/logdet and GLS comparisons remain.
Actual full-data accumulation plus mocks completed once in84.61s. Outside-Git
full_stats.npz/margin_stats.npz and their hashes are bound in RESULT; use these for
affected downstream calculations instead of replaying the row stream.

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q docs/research_program/observational_publication_20261015/ADVERSARIAL_AUDIT_20261022/continuation/astrometry/test_model.py
# Initial production command; completed. Do not repeat unchanged accumulation.
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 .venv/bin/python docs/research_program/observational_publication_20261015/ADVERSARIAL_AUDIT_20261022/continuation/astrometry/model.py
```

[Figure](ASTROMETRY.png) and numerical result retain prior/processing/selection
conditions. Original K03/K05 still need a same-congruence PM/NNR/clock response and
joint error law; this observer field model does not supply it. Original K04 also
needs qualified common distance/velocity/calibration and genealogy. No Pantheon
covariance or extra stochastic PV term was used. No old Gaia fit/envelope,
projection, LP or Planck split analysis was replayed. Requested parent Sol/high,
theory Astra/xhigh; observed UNKNOWN. No solver/ODE or four-axis CAS admission.
