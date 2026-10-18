# V02 finite delivered-fit counterfactual

Owner obsstat; C0, diagnostic-only, non-claim-bearing. Requested runtime
gpt-6.1-sol/high; observed model/effort UNKNOWN. Existing primary checkout,
one owned writer directory, no new worktree/clone or child commit/push.
Launch checkout HEAD 5450b04442a400aa08e71f11565e774691590fa9;
other lanes may advance HEAD without changing these inputs.

The controlling goal is `EXECUTION_GOALS.json` V02, with acceptance
“Matched mask/beam/input and mode leakage.” The source archive is the original
nine-T/eight-EB retained coefficient NPZ, SHA256
900e6c6fa04a6313f63753747d89e7059486bdeb88d51c91d895fcc8b4e09459.
Only its `SMICA_FULL` T vector is used. This is one observed sky.

## Definition and equation audit

The original input vector a is the simultaneous masked OLS fit retained at
ell2..5, in microK_CMB. It is not an intrinsic full-sky low-ell decomposition.
We define a new finite signed source perturbation

`s(n) = sum_{ell=2..5,m} [a_fit(ell,m)/b_INT(ell)] Y_real(ell,m,n)`.

This equation defines the surrogate's domain. It makes no assertion about
unavailable physical monopole, dipole, high multipoles, foregrounds or noise.
No positive absolute blackbody temperature is manufactured. The scalar signed
perturbation transforms by linearity with thermodynamic Doppler weight one.

For outward/sourceward directions, beta=v/c and signature (-,+,+,+),

`gamma=(1-beta²)^(-1/2)`,
`D=1/[gamma*(1-beta.n_observed)]`,
`n_source=D*[n_observed+((gamma²/(gamma+1))*(beta.n_observed)-gamma)*beta]`,
`(U_beta s)(n_observed)=D*s(n_source)`.

The finite processing experiment is

`f(beta)=retain_2..5 OLS_0..5(mask_actual * S_RING64 B_INT U_beta s)`.

Here B_INT uses the actual delivered SMICA `INT_BEAM` HDU, without substituting
a Gaussian approximation. It is applied once, after the finite boost. The source
sector b_ell is invertible; no inversion is attempted for the zero beam entries
at ell0/1. Those table entries are also projected out by the fit. The once-only
order is checked by f(0)=a_fit, and an explicitly wrong `U_beta B_INT s` control
is evaluated rather than assuming commutation.

Native common/HM/OE TMASKs are ANDed before child coverage is computed, then
coarsened by the exact NESTED2048-to-RING64 parent valid fraction. The original
T support also requires cache confidence>0.5 and parent fraction>=0.995.
The selected count must be 26,846. Reconstructing this selection does not
reproduce the native-child average of the surrogate sky: the downstream
surrogate here is synthesized at RING64 pixel centres, explicitly.

## Nuisance quotient and numerical controls

The fit simultaneously includes ell0..5 and then retains ell2..5. An independent
Frisch-Waugh-Lovell computation removes the actual selected-pixel ell0/1 image
before fitting the retained basis. This is an unweighted geometric nuisance
quotient, not covariance whitening, and supplies no foreground/calibration law.

Each harmonic output uses orthonormal real Condon-Shortley harmonics ordered
ell,m0,sqrt(2)ReY,sqrt(2)ImY. In HEALPix alm language the sine coefficient is
-sqrt(2)Im(alm). The actual selected mask's ell6..16-to-retained leakage operator
must reproduce the unchanged historical matrix from Git object c2889730.

The exact boost is quadrature-projected through ell16 using a 32x64
Gauss-Legendre/azimuth rule. Comparing a 48x96 rule and ell12/16 cutoffs is a
numerical stability diagnostic, not a certified infinite-tail bound.
Central-difference local columns use h=5e-6, checked against h=1e-5 and an
unchanged analytic first-order generator from that same historical Git object.
Finite injections test beta=.0003,.00123,.003,.01 in direction (1,2,3)/sqrt(14),
plus the three coordinate directions at .00123. These are design points,
not an estimate of the solar observer velocity.

Test budgets are finite numerical checks: original K max delta<=1e-10,
zero-beta replay max delta<=1e-9 microK, FWL/joint-fit max delta<=1e-8
microK/beta, h refinement operator delta<=1e-4 microK/beta, analytic derivative
relative delta<=1e-7. They were not taken from physical covariance errors.
`FIRST_FAILURE.txt` preserves the initial new-unit-test roundoff failures;
original task acceptance and frozen references are unchanged.

## Exact original criteria and scoped evidence

Original objective: “Inject finite local observer boost through the actual
processed Planck source.” Original output: “local response columns with
covariance/error envelopes.” Original acceptance: “Matched mask/beam/input and
mode leakage.” These criteria are preserved. No full physical-null qualification
is added to V02; statistical significance and later global-history competition
have their own downstream gates.

| Consuming decision | Evidence provided | Status |
|---|---|---|
| Defined finite delivered-fit source | Original coefficients, explicit construction, f(0) replay | executable preparation |
| Original mask and finite mode leakage | TMASK/cache identities, actual support, historical K replay | executable preparation |
| Beam order in that surrogate | Actual INT_BEAM, once-only beam, wrong-order counterexample | executable preparation |
| Pixel monopole/dipole quotient | Joint OLS/FWL equality | executable preparation |
| Physical observer response upstream of Planck processing | Frequency/bandpass-dependent injection, component-separation/calibration/frame mapping absent | HOLD |
| Physical uncertainty/identified response rank | No covariance or complete foreground/calibration nuisance image supplied; numerical finite-response diagnostics are reported separately | UNKNOWN |
| Native-child source coarsening | Available operation but not executed in this counterfactual | NOT_RUN; not external missing input |
| Polarization, physical high-mode tails, global source history | Not supplied by this scalar finite source definition | UNBOUNDED/UNKNOWN |

The author does not close original V02 from this surrogate; fresh review must
assess the original criteria and the scope supported by these inputs. A numerical three-column
rank refers to this finite geometric map only, not local/global discrimination,
physical velocity inference or a physical observer-response rank. V03's
independent physical global-history response is not generated here. No posterior,
p-value, cosmic B attribution or native Bianchi result follows. The result's
missing signal/noise/foreground simulation law is a downstream qualification
limitation, not an additional V02 gate. Native-child averaging is an executable
processing extension rather than an external-input blocker.

## Primary-source check

[Planck 2018 IV](https://www.aanda.org/articles/aa/full_html/2020/09/aa33881-18/aa33881-18.html)
describes component-separation preprocessing, beam correction, masking and
calibration. [Planck XXVII](https://doi.org/10.1051/0004-6361/201321556)
distinguishes aberration from frequency-dependent modulation in released
intensity-derived maps. The scalar weight-one counterfactual does not supply
those pipeline-specific factors.

The project-local `RESEARCH_LOOP_KO.md` records the dossier§12.2 processing order
boost→beam/window→projection. The original extracted dossier text was not located
in this task; no claim is made that it was reread here. The exact local formulas
and implementation above are independently checkable and keep that order.

## Reproduction

From the repository root, with the existing .venv and external source files:

```sh
OPENBLAS_NUM_THREADS=2 OMP_NUM_THREADS=2 MKL_NUM_THREADS=2 .venv/bin/python -m pytest -q docs/research_program/observational_publication_20261015/CONTINUATION_20261018/V02_EXECUTION_20261018/test_v02_response.py
OPENBLAS_NUM_THREADS=2 OMP_NUM_THREADS=2 MKL_NUM_THREADS=2 .venv/bin/python docs/research_program/observational_publication_20261015/CONTINUATION_20261018/V02_EXECUTION_20261018/run_v02.py
OPENBLAS_NUM_THREADS=2 OMP_NUM_THREADS=2 MKL_NUM_THREADS=2 .venv/bin/python docs/research_program/observational_publication_20261015/CONTINUATION_20261018/V02_EXECUTION_20261018/verify_generator.py
OPENBLAS_NUM_THREADS=2 OMP_NUM_THREADS=2 MKL_NUM_THREADS=2 .venv/bin/python docs/research_program/observational_publication_20261015/CONTINUATION_20261018/V02_EXECUTION_20261018/plot_v02.py
```

The result and figure generators are create-only. Reuse completed outputs; do
not rerun this scientific experiment merely to check the environment. Parent
performs the fresh independent review and any publication/status integration.
