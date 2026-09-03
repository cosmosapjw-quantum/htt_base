# T7 — Continuum wide-mask high-source response: exact z-axis and graded all-direction evidence

Date: 2026-09-03  
Observational data used: none  
Physical model: first-order local-observer thermodynamic-temperature response  
Transfer: identity  
Novelty status: unresolved

## 1. Question and scope

For a fixed unit boost direction \(\hat b\), let

\[
K_{\hat b}^{\rm cont}(L)
 : \bigoplus_{\ell=7}^{L}V_\ell
 \longrightarrow
 \bigoplus_{\ell=2}^{5}V_\ell
\]

be the continuum counterpart of the processed high-source response. It uses the
same joint fitted band `ell=0..5`, retained band `ell=2..5`, and wide
axisymmetric mask as WU-011, but replaces the finite HEALPix quadrature and
transforms by continuum spherical integrals.

The retained real carrier has dimension

\[
\sum_{\ell=2}^{5}(2\ell+1)=32.
\]

This pack asks only whether the continuum response has full row rank. It does
not certify the finite HEALPix matrix, a physical high-ell amplitude, a
stochastic covariance model, or an observational inference.

Fixed conventions are

\[
g_{ab}=(-,+,+,+),\qquad n^a=-e^a,
\]

\[
\beta_{\rm obs}=v_{\rm obs}/c,\qquad d=1,
\qquad \beta_{\rm obs}\rightarrow0.
\]

## 2. Continuum operator

The wide mask is

\[
w(\mu)=
\begin{cases}
0,&-1\le\mu\le-3/4,\\
1/2+2\mu/3,&-3/4<\mu<3/4,\\
1,&3/4\le\mu\le1.
\end{cases}
\]

For fitted harmonics \(Y_\alpha\), define

\[
N_{\alpha\beta}
 =\int_{S^2}w(\hat n)
   Y_\alpha^*(\hat n)Y_\beta(\hat n)\,d\Omega.
\]

For a source harmonic \(Y_p\) and first-order boost generator
\(\mathcal B_{\hat b}\), define

\[
R_{\alpha p}^{(\hat b)}
 =\int_{S^2}w(\hat n)
  Y_\alpha^*(\hat n)
  (\mathcal B_{\hat b}Y_p)(\hat n)\,d\Omega.
\]

The continuum fitted nuisance operator is

\[
\boxed{
K_{\hat b}^{\rm cont}(L)
 =P_{2:5}N^{-1}R_{\hat b}^{7:L}.
}
\]

For the axisymmetric mask, \(N\) is block diagonal in \(m\). The exact z-axis
construction exploits this block structure. Independent all-direction
calculations instead evaluate the full angular integrals and then adapt to the
orthonormal real carrier.

## 3. Coordinate convention

Rank is invariant under every invertible row and column scaling, so the exact
polynomial-basis pivot-minor proof may be evaluated before harmonic
normalization. Singular values are quoted only after transforming to the
orthonormal real carrier

\[
c_{\ell A}=(a_{\ell0},\sqrt2\Re a_{\ell m},-\sqrt2\Im a_{\ell m}).
\]

The WU-011 raw complex-component coordinate is related by the diagonal adapter
recorded in the notation registry. Exact rank evidence and metric singular
values must not be conflated.

## 4. Exact z-axis rank certificate

PR #446 contains an author-derived exact rational artifact for
\(\hat b=\hat z\), \(L=12\). Its weighted normal-block determinants are
nonzero, and the selected exact response minors have nonzero determinant
squares in every \(|m|\)-block.

The complex block ranks are

\[
(r_0,r_1,r_2,r_3,r_4,r_5)=(4,4,4,3,2,1).
\]

The corresponding stored-real rank is

\[
\boxed{
4+2(4+4+3+2+1)=32.
}
\]

Hence

\[
\boxed{
\operatorname{rank}_{\rm alg}
 K_{\hat z}^{\rm cont}(12)=32.
}
\]

This conclusion follows from exact nonzero minors and does not depend on an
SVD threshold.

Evidence grade:

```text
AUTHOR_DERIVED_EXACT_RATIONAL_ARTIFACT
```

The PR #446 external-package workflow itself executed no steps, so the exact
artifact is not relabelled as an independently executed GitHub verifier.

## 5. Independent local and cross-algorithm evidence

Independent calculations performed during the report audit used:

- Wolfram high-precision harmonic/Wigner construction;
- SymPy exact polynomial integration for the z blocks;
- mpmath high-precision z-axis singular values;
- SciPy piecewise Gauss--Legendre/Fourier quadrature for all six directions;
- local Octave, JAS, and Julia implementations for additional cross-language
  checks, with exact-rational z-axis checks in the algebra systems.

The PR #447 repository contains Octave/JAS/Julia verifier source, but its GitHub
jobs ended before runner assignment. The thread-local executions are therefore
classified `LOCAL_NON_BYTE_EXACT`, not repository-executed proof.

## 6. Rank ladder

The independently computed continuum ranks are:

| Source cutoff | z direction | x/y class | diagonal class |
|---:|---:|---:|---:|
| 8 | 20 | 24 | 24 |
| 9 | 27 | 29 | 32 |
| 12 | 32 | 32 | 32 |

At \(L=8\), the high-source dimension equals 32 but the operator is not
surjective. This is a direct counterexample to replacing an actual rank
calculation by column counting.

At \(L=9\), the diagonal class is already full row rank, while the axial and
transverse classes retain exact or numerical deficiencies.

At \(L=12\), every registered direction is numerically full row rank.

## 7. L=12 singular values

In the orthonormal retained/source metric, the reported smallest singular
values are

\[
\sigma_{32}^{X/Y}
 =0.010490334912761,
\]

\[
\sigma_{32}^{Z}
 =0.006905664979696537,
\]

\[
\sigma_{32}^{\rm diagonal}
 =0.008510322776380.
\]

The corresponding condition numbers are approximately

\[
\kappa_2^{X/Y}=2736.33,
\qquad
\kappa_2^Z=8448.34,
\qquad
\kappa_2^{\rm diagonal}=4822.15.
\]

Wolfram and direct SciPy quadrature agree on these smallest singular values at
roughly \(10^{-13}\) relative scale in the available local receipts. These are
strong numerical checks, not interval enclosures.

Evidence grades:

```text
z direction:
  exact algebraic row-rank certificate
  plus high-precision numerical spectrum

other five registered directions:
  dual-algorithm high-precision numerical row-rank evidence
  plus source-level external verifier implementations
```

## 8. Continuum surjectivity consequence

For every direction whose continuum matrix is full row rank,

\[
\operatorname{Im}K_{\hat b}^{\rm cont}(12)=\mathbb R^{32}.
\]

Therefore every continuum low-source response satisfies

\[
P_{\operatorname{Im}K_{\hat b}^{\rm cont}(12)^\perp}
J_{\hat b}^{\rm cont}=0.
\]

This is a deterministic unrestricted-high-source nonidentifiability statement
for the continuum processed operator. It does not say that high-source modes
have arbitrary physical amplitudes, or that statistical information vanishes
under a declared covariance/prior model.

## 9. Nested-image short circuit

Because the cumulative source spaces are nested,

\[
\operatorname{Im}K_{\hat b}^{\rm cont}(L)
\subseteq
\operatorname{Im}K_{\hat b}^{\rm cont}(L+1),
\]

full row rank at \(L=12\) persists at every larger cutoff. Thus no additional
\(L=16\) or \(L=20\) calculation is required for the continuum deterministic
rank question.

Higher cutoffs remain relevant for a physical covariance or tail-amplitude
model, which is a different problem.

## 10. Finite-HEALPix firewall

The last accepted finite-operator WU-011 result is

```text
PASS_TASK7C_MATCHED_CONTROL_RANK_UNRESOLVED.
```

The continuum rank result cannot replace it. A finite quadrature/transform,
weighted solve, resolution, iteration count, and mask sampling introduce a
matrix perturbation that must be bounded in the directions relevant to the
weak singular modes.

A scalar replay-floor norm was too coarse. The required finite-operator bridge
is the T8 matrix-valued numerical-error theorem plus a complete calibrated
error-family registry. Until that bridge closes,

```text
CONTINUUM_SURJECTIVE
```

and

```text
FINITE_HEALPIX_RANK_UNRESOLVED
```

are compatible statements about different operators.

## 11. Literature boundary

The retrieved literature supports:

- nearest-neighbour first-order full-sky boost coupling;
- mask-induced harmonic mixing;
- matrix-valued rather than scalar transfer modelling for general filtering;
- the need for controlled numerical linear algebra in ill-conditioned
  spherical inverse problems.

It does not supply the project-specific wide-mask rank calculation. The exact
z minors and the declared numerical lineages provide that evidence.

## 12. T7 terminal

```text
PASS_CONTINUUM_L12_SURJECTIVITY_EVIDENCE
/
Z_DIRECTION_EXACT_ALGEBRAIC_RANK_32
/
OTHER_FIVE_DIRECTIONS_DUAL_ALGORITHM_NUMERICAL_RANK_32
/
ALL_DIRECTION_INTERVAL_CERTIFICATE_NOT_OBTAINED
/
FINITE_HEALPIX_RANK_REMAINS_UNRESOLVED
```

This terminal is sufficient for Report A if every sentence preserves the
evidence grades above. It does not authorize a portable all-direction formal
certificate, observational execution, empirical beta, source subtraction,
global-tilt identification, physical source attribution, publication, or
merge.
