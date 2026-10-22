# A22-04 — finite spectral source and two-redshift operator

Owner HTT, C0 DERIVED_CONDITIONAL; transfer none. Source intake: a8fd176305fb475947a46f9dacb651805d323741;
final candidate/paired generation base: d256ed4669b1ded62fa0db606929af108160ccf6.
New model: an explicitly defined rest-frame spectral time sequence, three photon
bands and four-parameter refit after a finite observer reboost. Independent read-only review: scoped PASS; empirical closure remains HOLD. Next consumers: V04/V05 and H04 source-response qualification.

With signature(-+++), sourceward n and dimensionless beta, delta=gamma(1+beta.n).
Same source events have t'=t/delta, lambda'=lambda/delta and
1+zHEL'=(1+zHEL)/delta. Spectral flux transforms as
f_lambda'(t',lambda')=delta^3 f_lambda(delta t',delta lambda'). Photon rate is
the actual band integral of T(lambda)*lambda*1e-9*f_lambda/(h*c), in photons/m²/s,
when wavelength is nm and flux density is W/m²/nm. Band definitions stay fixed
in each observer rest frame.

For f_lambda=x0/(1+zHEL)*S((t-t0)/(1+zHEL),lambda/(1+zHEL);x1,c), the exact
transported template has x0'=delta²x0, x1'=x1, c'=c, t0'=t0/delta. The source
template in [spectral.py](spectral.py) is positive on its declared250..1000nm
domain; no extrapolation is allowed. Parameters x0=2e-15 in the stated flux-density
unit, x1=.35, c=.08, t0=3days; five phases, three bands, three z and four directions
produce12cases/180paired fluxes. Four-parameter least squares begins away from the
analytic answer. Its rank and negative controls are checked.

The [SALT2 source structure](https://arxiv.org/html/astro-ph/0701828) and retained
SNANA genmag_SALT2.c lines2649..2659,2844..2845,2897..2898 qualify the photon integral
convention. The synthetic template is fully specified, rather than an empirical
SALT2-B22 realization. Actual standardization also changes alpha*x1−beta*c−bias+host.

Executed existing `.venv`: four narrow tests passed; twelve production refits
passed the predeclared1e-10 spectral/quadrature,1e-9 fit,1e-8mag amplitude,
1e-7 shape and1e-6day peak-time criteria. Maximum amplitude defect is2.48e-15mag.
Raw fixed-band magnitude defects span about−.0354..+.0295mag despite the refit's
amplitude equivariance. Missing wavelength/time transport controls fail at >1e-3
relative flux. The 128/256-node integration comparison checks numerical error.

The two-redshift comparison is R=m_corr−M−g ln[(1+zHEL)chi(zHD)]+constant,
g=5/ln10. For kappa=m_corr'−m_corr+g ln(delta), eta=zHD'−zHD,
DeltaR=kappa−g ln[chi(zHD+eta)/chi(zHD)]. Paired same-source residuals are checked.
The separate fixed-measured-data derivative uses only trial
1+zHD(s)=(1+zHD)e^s and equals−gA. Its finite difference is checked with the analytic
EdS chi; this comparison background needs no ODE and is not fitted cosmology.

## A finite component tied to an actual published correction

[Carr et al.Eqs4–7](https://arxiv.org/html/2112.01471v2) use projected radial
dimensionless q=beta.n_HEL, with b=|beta|, in C_rad=sqrt((1+q)/(1−q)). The full-vector HEL-chart correction is
C_exact=1/[gamma_b(1−q)]. Their ratio r=sqrt((1−q²)/(1−b²)) lies in[1,gamma_b].
With a fixed covariant source-PV factor this bounds one redshift-correction
component: 0<=eta<=(1+zHD)(gamma_b−1) for a reference-rest initial observer.
At369.82km/s, gamma_b−1=7.6086899e-7. The source is perpendicular to beta in the initial reference chart; aberration
gives q=b² in the HEL chart. This witness atzHD=.02
gives eta=7.7608519e-7 and EdS DeltaR=−8.3019547e-5mag. This is a finite operator
approximation bound; rounded catalogue rows are not tested for such a discrepancy.

The total empirical kappa and eta remain UNKNOWN. Needed: paired same-ID
lightcurve/spectrum/passband/MW-attenuation transport, SALT2-B22/BBC refits and
global standardization/cohort changes, plus the PV-map/group response in invariant
reference coordinates. Published parameter errors or total covariance are not
deterministic bounds on these changes. Public Pantheon total covariance was not
used again and no stochastic PV term was added.

```bash
OPENBLAS_NUM_THREADS=1 .venv/bin/python -m pytest -q docs/research_program/observational_publication_20261015/ADVERSARIAL_AUDIT_20261022/continuation/two_redshift_pipeline/test_spectral.py
OPENBLAS_NUM_THREADS=1 .venv/bin/python docs/research_program/observational_publication_20261015/ADVERSARIAL_AUDIT_20261022/continuation/two_redshift_pipeline/spectral.py
```

[Result](RESULT.json) binds thresholds and source identities; [figure](SPECTRAL.png).
V04/H04 physical acceptance remains open; the rigorous radial component does not
bound all empirical processing defects. Requested parent Sol/high and theory
Astra/xhigh; observed runtimes UNKNOWN. No old projection/history/optics run was repeated.
