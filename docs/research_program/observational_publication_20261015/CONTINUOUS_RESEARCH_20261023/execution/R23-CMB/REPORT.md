# R23-CMB — joint split-direction sensitivity of processed E morphology

Owner obsstat; C0 `DIAGNOSTIC_ONLY`; transfer source none. One actual observed
Planck PR3 sky, Galactic COSMO polarization, K_CMB. No p-value, physical cleaning,
independent-null count or family inference. Next consumer: L03/L04 processing
qualification. Original L03 and its physical joint null remain **HOLD**.

## Frozen experiment and source reuse

The source packet uses a8e66da28461a415f5da3b3d609c482554d2dcd1; the inspected
checkout was 855107f23fd4f25587ba242d8a5dfc1a8fc81876. The morphology kernel,
counterpair experiment and prior window calculation have no intervening science
changes. Their exact identities and the retained coefficient payload are in
[RESULT.json](RESULT.json). The source loader verifies all 15 retained E/B
NPZ/metadata pairs before selecting L128. The prior 45 window cells, original
split-ratio bank and p=.039 are reuse-only; none was regenerated.

For delivered Q/U write y_i=T_i(w_i)s+F_i(w_i)f+b_i+n_i for
i=full,hm1,hm2,oe1,oe2. The source component-separation weights/preprocessing
w_i are distinguished from this experiment's **Euclidean harmonic-power
metric**, which is not an inverse-noise covariance. Conditional noise means are
zero; N_ij=E[n_i n_j^T], and b_i retains systematic means/response errors.

The original retained operator is
z_i=R E_(ell2:4) A_spin2,L128[M_common y_i]. M_common is the existing
AND-of-three native NESTED2048 PMASK>0.5, SHA256
bfae5917211f8ecce2a99ee8b996e168dcc8df18e1a6e6d4bdee638063ae05d3.
Delivered beams stay in place: no new deconvolution or repeated original mask.
R embeds each multipole as (a_l0,sqrt(2)Re a_l1,sqrt(2)Im a_l1,...),
so ||z||²=sum_lm|a_lm|². The word `native` in the calculation identifies this
original pseudoalm operator, never a native solver.

The secondary operators reuse the retained result of
R E_(2:4) A_spin2,4[W_b S_spin2,L128,RING64(E_i,B_i)], b=20 or30 degrees.
Both E/B inputs and A22's exact strict pixel-centre windows are retained. These
are repeated operators on the same sky; the original mask is already present.
The original pseudoalm is distinct from the W=1 finite-grid roundtrip.

## Split algebra and unidentified physical remainder

Here n_i denotes the processed noise; N_ij=O_i Cov(n_i^map,n_j^map) O_jᵀ
for the applicable fixed delivered-map operator O_i. The following moments
are conditional on the stated deterministic signal/foreground/weight model.

For any processed pair z1=a1+n1,z2=a2+n2, set
S=(z1+z2)/2, D=(z1-z2)/2 and a_±=(a1±a2)/2. Then

```
S = a_+ + n_+;                  D = a_- + n_-
N_++ = (N11+N22+N12+N21)/4
N_-- = (N11+N22-N12-N21)/4
N_+- = (N11-N12+N21-N22)/4
||S||²-||D||² = z1ᵀz2
E[z1ᵀz2] = a1ᵀa2 + tr(N12).
```

The entire deterministic contribution cancels in D if and only if a_-=0.
Any component with the same processed response cancels, while differential
responses from weights, beams, foregrounds and systematics remain in a_-. Even for matched
a=g+f_common+b_common the cross-power contains ||g||²,
2gᵀ(f_common+b_common), ||f_common+b_common||² and tr(N12).
Difference-power subtraction therefore does not isolate the CMB. Cross HM/OE
noise covariance is unspecified; the splits reuse observations.

A common processed addition h leaves both difference directions unchanged.
The decomposition is ambiguous under g→g+h, f_common→f_common-h. This is a
conditional algebraic ambiguity, not a new universal no-go theorem. In
particular, the data-derived projection below may remove CMB correlated with
the realized split differences. Their geometric cosine is not an estimator of
stochastic noise covariance or evidence of independence.

## New actual-sky projection and results

For each of the three operators independently, form the 21×2 matrix
D=[(z_hm1-z_hm2)/2,(z_oe1-z_oe2)/2]. Use thin SVD, retain singular values
above 1e-10 times the largest, and set P=U_r U_rᵀ. Report
z(α)=z_full-αPz_full at fixed α=0,.25,.5,.75,1; no optimum is selected.

| Operator | Rank | Removed power at α=1 | HM/OE coefficients | Singular ratio |
|---|---:|---:|---|---:|
| Original pseudoalm |2|0.0766476324|0.6709011, -0.3640551|0.7721418|
| Secondary 20°, L128 |2|0.0968572520|0.6889043, -0.8079359|0.6772945|
| Secondary 30°, L128 |2|0.0186941857|0.2661453, -0.3972018|0.7178194|

Original-pseudoalm signed J234 changes -0.01501419→-0.07525857 and
alignment23 squared changes .67950074→.45631847. The 20° alignment changes
.79473989→.43085984; the 30° path is nonmonotonic,
.04692717→.02320666→.00042353→.10787025→.36748348.
All 15 points have defined axes; the minimum normalized axis gap is
.02711776356. These are sensitivity results, without a calibrated null.

Removed power means ||Pz_full||²/||z_full||² at α=1. At general α the
relative total power removed is (2α-α²) times that fraction; α itself is an
amplitude coefficient. [Figure](SPLIT_PROJECTION.png) and
[PDF](SPLIT_PROJECTION.pdf) render exact stored rows, with no error bars or
significance stars. Category `DIAGNOSTIC`; deterministic rendering, no seed.

Original full-minus-HM/OE-halfsum relative norms are .5357738/.5609396,
with denominator ||z_full||. Delivered full must not be replaced by the
arithmetic half-sum. These discrepancies do not identify their physical cause.

## Validation, execution and next input

Each operator passes seven arithmetic controls at the predeclared 1e-12
criterion: projector idempotence, residual orthogonality, reconstruction,
invariance under D[[0,-2],[3,0]], complete-m real-embedding power and both
split sum/difference reconstruction identities. Maximum residual is
4.1335e-16. This is author-stage finite algebra, not independent review or
CAS four-axis adjudication. [VALIDATION.json](VALIDATION.json) also compares
the host's exact-program replay with the Astra-returned values. No old
45-cell experiment was replayed.

The scientific author ran a read-only stdin calculation and supplied its exact
program. The lower-tier parent persisted it as [projection.py](projection.py),
replayed that new calculation and assembled [plot.py](plot.py). Requested
scientific author Astra/xhigh; requested parent gpt-6.1-sol/medium; observed
backends **UNKNOWN**. RESULT's requested-model strings are inherited author
recipe metadata, not observation of the parent's replay model. Actual commands,
execution roles and exit codes are recorded in [RAW_RECEIPT.json](RAW_RECEIPT.json).
Independent candidate review remains separate.

Primary source lookup: [Planck2018 IV §3.5 and Appendix D.2](https://www.aanda.org/articles/aa/full_html/2020/09/aa33881-18/aa33881-18.html)
describes fixed observed weights for separate CMB/noise simulation propagation
and E/B processing; the [IRSA PR3 map page](https://irsa.ipac.caltech.edu/data/Planck/release_3/all-sky-maps/matrix_cmb.html)
documents full/HM/OE products and half-difference interpretation caveats.
The author's search retrieved primary-source excerpts; direct A&A open returned
403 and the ESA simulation wiki timed out. This is not full-page readback.

The separate [NPIPE source](https://doi.org/10.1051/0004-6361/202038073) and
[release index](https://portal.nersc.gov/project/cmb/planck2020/) concern PR4,
not a replacement PR3 null. Existing PR4 observed restriction uses native1024
NESTED Q/U and 1,273 RING16 mask parents after explicit nest2ring, uniform
pixel weight 1/5,214,208. MC00200 CMB is NESTED and residual is RING. Exact
processed-total/foreground subtraction and producer/PLA packaging remain
unqualified: do not reconstruct a processed total as CMB+residual, even after
ordering reconciliation, without the missing component/subtraction law.
Do not transport PR4 calibration to PR3.

Exact remaining input for L03: a source-matched PR3 full/HM/OE joint processed
CMB+foreground+noise law with fixed weights/beam/mask/operator, realization
genealogy/cross-split covariance and statistic-specific whole-sky calibration.
Until supplied and independently reviewed, no null p, L03 completion or
physical morphology attribution follows.

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 .venv/bin/python -B docs/research_program/observational_publication_20261015/CONTINUOUS_RESEARCH_20261023/execution/R23-CMB/projection.py > /tmp/r23_cmb_replay.json
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 .venv/bin/python -B docs/research_program/observational_publication_20261015/CONTINUOUS_RESEARCH_20261023/execution/R23-CMB/plot.py
```
