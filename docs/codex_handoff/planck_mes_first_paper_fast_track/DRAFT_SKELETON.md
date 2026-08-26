# Draft manuscript skeleton — NONAUTHORITATIVE

## Working title

**Finite-null calibration of MES-anchored low-multipole morphology in Planck PR3**

> Status: first observational-analysis draft skeleton. Numerical claims below
> are limited to the frozen Planck PR3 SMICA observation and the exact 300
> ordered paired FFP10 CMB+noise rows. This file is not a publication-ready
> claim surface.

## Abstract

The large-angle cosmic microwave background provides unusually direct
constraints on departures from an almost-Friedmann–Lemaître–Robertson–Walker
geometry, but the resulting Maartens–Ellis–Stoeger (MES) bounds are one-way,
premise-dependent limits rather than measurements of shear, vorticity, or
geometric family. We apply typed geodesic MES ceiling coordinates to corrected
Planck PR3 SMICA low-multipole features and calibrate them with the same frozen
operator on 300 ordered paired FFP10 CMB+noise realizations. The analysis uses
two realization-conditional MES amplitude coordinates and eight
dimensionless irreducible morphology coordinates, with observation-inclusive
leave-one-out finite ranks and a row-wise family maximum. The resulting family
rank is \(98/301 \simeq 0.326\), compared with \(133/301 \simeq 0.442\) for a
separately frozen generic twelve-feature benchmark. The smallest coordinate
rank is \(16/301 \simeq 0.053\), arising from an octupole multipole-vector
internal-product coordinate; the shear and vorticity MES-anchor coordinates
each have rank \(74/301 \simeq 0.246\). Thus the present result is not an
anchor-driven anomaly and provides no statistically compelling departure in
the frozen ensemble. We use a preregistered family decomposition to separate
the effects of amplitude-coordinate transformation from feature-family
reduction. The result is a conditional finite-null methods application: it
does not identify physical shear or vorticity, distinguish a local boost from
a global tilt, or select a Bianchi geometry.

## 1. Introduction and scope

The MES programme derives comparatively model-independent, one-way bounds on
large-scale anisotropy and inhomogeneity from CMB multipoles. Its scientific
role differs from a conventional model-selection pipeline: a small CMB
anisotropy can restrict admissible kinematic departures under stated
almost-EGS assumptions, but it does not establish the converse, identify a
geometric family, or supply a posterior probability for anisotropy.

Large-angle CMB anomaly studies also face a distinct statistical problem.
Several correlated statistics can be inspected on a single observed sky, and
their apparent significance can depend on foreground cleaning, masking, and
the selected family of statistics. We therefore formulate the present
application as an exact finite-ensemble calibration under one frozen row
operator rather than as a search for a novel low-\(\ell\) anomaly.

Our goals are deliberately narrow:

1. construct typed realization-conditional geodesic MES coordinates from the
   corrected \(C_2\) and \(C_3\) of every observation/null row;
2. combine those coordinates with a frozen irreducible morphology registry;
3. calibrate the full family by an observation-inclusive finite rank;
4. decompose the difference between the generic and MES families without
   selecting a preferred operator from the observed outcome;
5. state precisely which physical conclusions remain unidentified.

## 2. Planck PR3 observation and paired FFP10 ensemble

The primary data product is the Planck PR3 SMICA temperature map, reduced by
the preregistered joint cut-sky low-\(\ell\) operator. The null ensemble contains
300 ordered paired FFP10 SMICA CMB+noise rows. Observation and null rows share
the same mask, harmonic convention, beam/pixel commonization, feature order,
and numerical operator.

The portable feature package contains one observed row and 300 null rows with
the twelve ordered features

\[
(C_2,C_3,C_4,C_5,\mathcal P,G_2,G_3,
 d_2,d_{3,0},d_{3,1},d_{3,2},A_{23}),
\]

where \(\mathcal P\) is the even/odd parity ratio over
\(\ell=2,\ldots,5\), \(G_\ell\) are power-tensor gaps, \(d\) denotes
multipole-vector internal absolute products, and \(A_{23}\) is the maximum
quadrupole–octupole plane alignment.

The exact scope is conditional on this SMICA product and these 300 paired
rows. Commander, Planck PR4, and a 999-row CMB-only ensemble are deferred
robustness tiers and are not used in the primary draft.

## 3. Corrected joint cut-sky low-\(\ell\) features

The corrected estimator fits all real harmonics with
\(0\leq\ell\leq5\) simultaneously on the weighted cut sky. The monopole and
dipole are nuisance coefficients in the same linear fit as the retained
\(\ell=2,\ldots,5\) modes. Only after the masked fit are the retained
coefficients mapped to the common beam/pixel convention. This ordering avoids
a sequential nuisance-removal path in which masked monopole/dipole leakage can
contaminate retained modes.

For the frozen SMICA mask the registered operator has condition number
\(6.2075\) and relative singular floor \(0.15999\). The corrected generic
twelve-feature family reproduces the benchmark family rank \(133/301\), while
individual feature values and ranks change under the corrected operator.

## 4. Typed MES realization-conditional coordinates

For each row, the dimensionless multipole amplitudes are

\[
\epsilon_\ell =
\frac{1}{T_0}
\left[\frac{(2\ell+1)C_\ell}{4\pi}\right]^{1/2}.
\]

We adopt the declared SAG observer-motion branch in which the residual
cosmological dipole bound is \(\epsilon_1=0\). The active geodesic MES
coordinates are then

\[
\Sigma_{2,\max}
 = \frac{3}{2}
   \left(3\epsilon_2+\frac{3}{7}\epsilon_3\right)^2,
\qquad
W_{2,\max}
 = \frac{3}{2}
   \left(\frac{2}{15}\epsilon_2\right)^2.
\]

These are typed one-way ceiling coordinates under the registered linear
almost-EGS assumptions. They are not observed values of physical shear or
vorticity. Because they are deterministic functions of the same row's
\(C_2\) and \(C_3\), they have shared data dependence and add no independent
information.

The primary MES family replaces the four raw power coordinates by these two
ceiling coordinates and retains the eight morphology coordinates:

\[
(\Sigma_{2,\max},W_{2,\max},
 \mathcal P,G_2,G_3,d_2,d_{3,0},d_{3,1},d_{3,2},A_{23}).
\]

## 5. Observation-inclusive finite-null statistic

Let \(X_{ij}\) be coordinate \(j\) of row \(i\), with \(N=301\). For each
two-sided coordinate, row \(i\) receives a leave-one-out center
\(m_{ij}\), and

\[
D_{ij}=|X_{ij}-m_{ij}|.
\]

The exact pooled local rank is

\[
p_{ij}=\frac{1}{N}\sum_{k=1}^{N}
 \mathbf 1(D_{kj}\geq D_{ij}),
\]

including the row itself and using conservative ties. Define
\(r_i=\min_j p_{ij}\). The family-level observation-inclusive finite rank is

\[
p_{\rm fam}
 =\frac{1}{N}\sum_{i=1}^{N}\mathbf 1(r_i\leq r_{\rm obs}).
\]

The construction is permutation-equivariant in the complete row pool.
Throughout we call this a finite rank conditional on the frozen ensemble; we
do not treat it as an unconditional cosmological probability.

## 6. Results

### 6.1 Coordinate-wise ranks

| Coordinate | Observed value | Finite rank |
|---|---:|---:|
| \(\Sigma_{2,\max}\) | \(2.4000870\times10^{-10}\) | \(74/301\) |
| \(W_{2,\max}\) | \(3.0061888\times10^{-13}\) | \(74/301\) |
| parity | 0.553365 | \(95/301\) |
| \(G_2\) | 0.449993 | \(182/301\) |
| \(G_3\) | 0.560137 | \(35/301\) |
| \(d_2\) | 0.133173 | \(177/301\) |
| \(d_{3,0}\) | 0.398744 | \(16/301\) |
| \(d_{3,1}\) | 0.433858 | \(155/301\) |
| \(d_{3,2}\) | 0.436828 | \(174/301\) |
| \(A_{23}\) | 0.940239 | \(135/301\) |

The smallest local rank is \(16/301\simeq0.053\), associated with
\(d_{3,0}\), not with either MES coordinate. No coordinate rank is below
0.05 in this finite ensemble.

### 6.2 Family result

For the frozen ten-coordinate MES family,

\[
p_{\rm MES,fam}=\frac{98}{301}=\frac{14}{43}\simeq0.326.
\]

The separately frozen generic twelve-feature benchmark gives

\[
p_{\rm generic,fam}=\frac{133}{301}=\frac{19}{43}\simeq0.442.
\]

These two fractions are paired outputs of different predeclared row operators.
Their numerical difference is not itself a significance test and is not
evidence that the MES coordinates reveal an additional signal.

### 6.3 Preregistered family decomposition

The following table must be generated by the map-free paper builder before the
draft is considered complete.

| Family | Purpose | Global rank | Minimum coordinate |
|---|---|---:|---|
| GENERIC_12 | frozen generic benchmark | \(133/301\) | TO_BE_COMPUTED |
| RAW_REDUCED_10 | isolate removal of \(C_4,C_5\) | TO_BE_COMPUTED | TO_BE_COMPUTED |
| EPS_REDUCED_10 | isolate \(C_\ell\to\epsilon_\ell\) | TO_BE_COMPUTED | TO_BE_COMPUTED |
| MES_10 | primary MES family | \(98/301\) | \(d_{3,0}\) |
| ANCHORS_ONLY_2 | anchor-only extremeness | TO_BE_COMPUTED | TO_BE_COMPUTED |
| MORPHOLOGY_ONLY_8 | morphology contribution | TO_BE_COMPUTED | TO_BE_COMPUTED |

Also insert the two-anchor Pearson/Spearman correlations, anchor-block
condition number, and paired row-score correlations between family variants.

## 7. Interpretation and limitations

The current result is a null result in the frozen finite ensemble. It supports
the operational use of typed MES ceiling coordinates and demonstrates that
they can be calibrated without reopening sky maps once the corrected feature
pool is frozen. It does not support a physical detection of shear or vorticity.

The result is also not primarily driven by the MES coordinates: each anchor has
local rank \(74/301\), whereas the most extreme coordinate is an octupole
multipole-vector morphology statistic at \(16/301\). The family-rank change
relative to the generic benchmark must therefore be interpreted through the
predeclared decomposition, not as increased evidence for anisotropic physics.

The primary limitations are:

1. a single SMICA component-separation product;
2. 300 paired CMB+noise null rows;
3. realization-conditional same-row anchors;
4. no direction-indexed source field or harmonic phase in the portable package;
5. no physical local/global response;
6. no native-solver morphology atlas.

None of these limitations prevents the present narrow methods/application
draft. They constrain its claims and define later robustness and physical
interpretation work.

## 8. Conclusion

We have constructed a typed, row-equivariant finite-null application of
geodesic MES ceiling coordinates to Planck PR3 low-multipole morphology. In
the frozen SMICA plus 300 paired FFP10 ensemble, the ten-coordinate family rank
is \(98/301\), with no coordinate below the 5% finite-rank threshold. The
smallest coordinate rank is morphology-driven rather than anchor-driven.
Accordingly, the current analysis provides a calibrated null result and a
reproducible methodological bridge, not evidence for physical shear,
vorticity, global tilt, or a Bianchi geometry.

## Appendix A. Frozen feature and family registry

TO_BE_GENERATED_FROM_ANALYSIS_SUMMARY.

## Appendix B. Map-free replay and availability

The primary analysis can be replayed from the committed numeric feature
packages without reopening the raw Planck maps. Raw Planck PR3 and FFP10 files
are retained externally for later robustness work. The first draft uses only
the frozen map-free packages and does not redistribute restricted or large raw
products.
