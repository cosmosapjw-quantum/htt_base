# R37-04: finite physical-family compatibility

This is a source-qualified **conditional geometry-response calculation** for the
two instantaneous R36-10 spatial-Ricci witnesses. It supplies a result for the
P2/P5 methods discussion, not an observed CMB morphology or a Bianchi-family
identification. The R36-10 later publication status formally qualifies its
finite diagnostic product; its earlier immutable candidate prose still says
pending and is retained. The original publication count remains **17/42
scientific**, with a separately reported **18/42 analytic** count. This result
does not promote either count.

## Geometry and physical domain

In the R36 oriented orthonormal hypersurface-normal frame, signature
`(-,+,+,+)`, `epsilon_123=+1`, Ricci has units `u_*^2`. The retained II and
unequal-VII0 witnesses are, up to proper rotations,

`R_II = diag(1/2,-1/2,-1/2)`,
`R_VII0 = diag(-1/2,3/2,-3/2)`.

Their trace is `-1/2` in both cases, whereas `tr(R^2)` is `3/4` and `19/4`.
The trace-free quadratic values differ by the same `4`. These are actual
R36 supplied finite geometries, not a complete parameterization of either
Bianchi type. For a declared conditional family path, multiplying each
source spatial structure coefficient by the same dimensionless amplitude
`a in [0,1]` gives `R(a)=a^2 R(1)` by curvature homogeneity. The nuisance
and noise law are identical between the competing paths. At each fixed `a`,
each family permits its own proper `SO(3)` orientation. The figures sample
`a=0,1/8,...,1`; the reported separation is analytic over the full
continuous path. No source history, polarization transport, native solver,
or ODE evolution is supplied by this scaling.

For a single symmetric tensor under isotropic Frobenius error, minimizing
over proper rotations is exactly the Euclidean distance between sorted
eigenvalue triples. The source witness therefore has
`delta(a)=sqrt(2) a^2`. This is an **attained analytic minimum over
orientations**, not a finite-grid upper bound. Its global infimum over
`a in [0,1]` is zero at the common Ricci origin. The retained I and
flat-VII0 controls also give identical flat local geometry through distinct
simply transitive presentations. We preserve both labels as equivalent
presentations; the compatible output can contain both. Local Ricci spectra
alone cannot label a universal Bianchi presentation. The `a=0` statement is
only a spatial-Ricci origin overlap; it does not establish a full FLRW
spacetime, including its extrinsic geometry.

The Gauss bridge used by the imported goal-3 analysis requires the electric
Weyl tensor, anisotropic stress, normal-frame `h` and `Sigma`, density, and
cosmological term, with a common congruence and conventions. A shear tensor
alone cannot provide `R_ij`. The imported direct-index Gauss check and
independent review were read; this task did not replay their producers.

## One matched conditional law and compatible sets

The declared synthetic raw event has seven coordinates: trace divided by
`sqrt(3)`, five orthonormal STF components, and a calibration coordinate.
Noise is `N(0,sigma^2 I_7)` and the same nuisance shifts trace and calibration.
Profiling it leaves six orthonormal coordinates. At fixed `a`, all pairwise
family mean differences, including orientation orbits, lie in the five STF
coordinates. The 5D carrier preserves the full profiled family likelihood
ratios. The sixth coordinate,
`(y_trace-y_calibration)/sqrt(2)-tr(R)/sqrt(6)`, is the discarded-space
adequacy residual; retaining it permits rejection of every listed family.
If amplitude is jointly fitted rather than conditioned, its trace varies and
the sixth coordinate must enter the common response carrier. We do not use
the 5D reduction for that enlarged question.

For one common 95% six-dimensional Gaussian event, let
`r95=sqrt(chi2_6(.95))=3.5484626592`. A bounded joint deterministic
response remainder `epsilon` gives each declared family a tube of radius
`tau=r95*sigma+epsilon`. The compatible set is *all* family orbits whose
profiled distance from the same event is at most `tau`; an empty set is
allowed. When both families have that same error, their tubes are guaranteed
disjoint if `sqrt(2)a^2-2tau>0`. The plots' `epsilon=0,0.1,0.2` are
**sensitivity inputs**, not measurements of a response remainder.

| Fixed amplitude | sigma | epsilon | Exact orbit gap | Conservative exclusive margin | II-center compatible set | Orbit-midpoint set |
|---:|---:|---:|---:|---:|---|---|
| 0 | 0.12 | 0.10 | 0 | -1.05163 | II, VII0 | II, VII0 |
| 0.5 | 0.03 | 0.10 | 0.35355 | -0.05935 | II | II, VII0 |
| 0.5 | 0.12 | 0.10 | 0.35355 | -0.69808 | II, VII0 | II, VII0 |
| 1 | 0.12 | 0.10 | 1.41421 | +0.36258 | II | neither |

The sign of the conservative margin is a sufficient separation certificate,
not a claim that negative margin forces the center to be ambiguous. The
midpoint uses sorted eigenvalue triples and the exact orbit metric. The
full 135-row calculation is in `FAMILY_SEPARATION.csv`; its columns distinguish
the exact analytic orbit gap from the conditional sampled grid of noise and
error values.

R36 itself provides **different, source-qualified deterministic bounds** for
the two full-tensor image sets: `0.1471034953` (II) and `0.2698726924`
(VII0), sum `0.4169761877`. Their source-set gap is at least `0.9972373747`
at `a=1` without a new noise assumption. If the same synthetic Gaussian
response law has `sigma=0.12`, the source-bound exclusive margin after two
95% noise radii remains `0.145606336` (the exact generated value is in the
result JSON). The R36 bound applies to its supplied `a=1` ellipsoids;
we do not extrapolate that bound to scaled amplitudes. The 577 old probes
per center are illustrative checks, not a covering proof; the conservative
whole-set bound is the evidence used here.

At `a=1`, the weak trace statistic cannot distinguish the witnesses.
A strong scalar comparator is the invariant `||STF(R)||_F^2`: its noiseless
values are `2/3` and `14/3`. Under the **same** STF part of the joint error
event, its exact compatible intervals follow from radii
`max(0,||STF(R)||-tau)` to `||STF(R)||+tau`, squared. The radial center gap
is `1.3437503185`, compared with the signed-tensor orbit gap `1.4142135624`.
At `a=1, sigma=0.12, epsilon=0.1`, its sufficient exclusive margin is
`0.2921192803`, also positive. Thus this particular pair does not require
the full signed tensor to separate under the stated budget. The signed
tensor remains necessary for orientation- or multi-tensor questions, and
the adequacy residual remains necessary for open-ended model checks. No
independent scalar data set or extra information beyond the joint law is
assumed.

For an explicit out-of-family control, shift the raw trace coordinate by
`1` from the II center, leaving the five STF likelihood-ratio coordinates
unchanged. Its profiled adequacy residual is `1/sqrt(2)=0.707107`, above
the `0.525816` tube at `sigma=0.12, epsilon=0.1`; both listed candidates
are rejected. On the adequacy figure's raw-shift axis, the rejection
threshold is `sqrt(2)*tau=0.7436154384`; a shift of `0.6` retains II.
Reusing the imported 50,000-draw synthetic Monte Carlo at
`a=1, epsilon=0.1`, the saved `sigma=0.12` row retained the true family in
49,960 draws and the wrong family in zero draws. These are frequencies from
the old declared Gaussian experiment, with finite binomial uncertainty;
they do not establish empirical sky null coverage.

## Fixed-Q optical sign radius and remaining gate

The imported sharp chirality witness was independently recomputed from its
fixed quadrupole and STF octupole construction. With `Q` fixed and having
simple spectrum, the ambient STF-octupole Frobenius distance to the nearest
zero-chirality hyperplane is exactly `1/sqrt(3)=0.5773502692`. An explicit
orthogonal perturbation attains a zero component and zero chirality at that
radius. This does not bound a joint error in `Q,O` or a fixed-norm `O`
sphere. The full tensor and orientation convention are retained.

The family gate remains below empirical identification: there is no qualified
full T/E/B family/mode/history/IC atlas with frame, spin, beams, masks,
cross-channel law, nulls, and equivalence checks. R36-09 recorded that input
HOLD. The finite II/VII0 result and sign radius are conditional methods
products only. No anisotropy-family posterior, native-transfer claim, or
observed geometry detection follows.

## Reproducibility and scope

The generating script checks SHA-256 of the retained R36 `TABLE.json` and
the imported goal-3 result/review before writing. The R36 table's Git blob
`1ae270fec9ae55375c01ec1f346f8755d9257049` is verified by the imported
goal-3 source record. The R36 later `PUBLICATION_STATUS.json` is read for
the qualified scoped status. The local `classification.py` contains the
pure response functions and writes only this product directory. It imports
no old producer. Rotation checks give maximum gap drift below `2e-15` over
200 random rotations, and direct full-profile versus common-carrier
squared-distance differences below `8e-15`. Four targeted local tests pass.

Each table and vector figure inherits the owner, conditional claim tier,
synthetic/null and covariance status, transfer source, allowed use, and
forbidden empirical-family use recorded under `artifact_metadata` in
`FAMILY_COMPATIBILITY_RESULT.json`. The figures are analytic/synthetic
visualizations, not likelihood results from an observed sky. This product
does not modify the campaign STATE, Git history, or any original receipt.
