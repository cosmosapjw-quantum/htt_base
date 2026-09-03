# Tensorized Low-Multipole CMB Inference under Conditional Isotropy Bounds and Response-Limited Identifiability

**Working theory-and-methods manuscript**  
Date: 2026-09-03  
Status: manuscript draft; no observational execution  
Repository: `cosmosapjw-quantum/htt_base`

## Abstract

Low-multipole cosmic-microwave-background analyses are frequently compressed
to a small collection of powers or scalar anomaly statistics. Such
compressions are useful summaries, but they do not preserve the full tensor
morphology of the observed multipoles and they do not, by themselves, identify
the physical origin of an anisotropy. We formulate a theory and methods
framework that keeps these two issues separate. First, we fix an orthonormal
stored-real harmonic convention and its exact maps to a symmetric trace-free
quadrupole `Q_ab` and octupole `O_abc`. On the nonzero cyclic domain we prove
that two amplitudes and an overcomplete Krylov contraction packet reconstruct a
canonical proper-oriented representative and separate `SO(3)` orbits. A signed
Krylov determinant distinguishes mirror-related configurations that share a
named four-statistic power/bispectrum compression. Second, we retain
Maartens--Ellis--Stoeger-type shear and vorticity bounds only as
premise-conditioned scalar functionals of multipole norms; rotational scalars
cannot equivariantly create tensor morphology without additional directional
input. Third, we state the finite-sample conditions under which an
observation-inclusive rank remains valid: joint exchangeability or an explicit
randomization group, and row-permutation equivariance of the complete
selection, nuisance-fitting, missingness, tie, and scoring algorithm. Fourth,
we combine an exact full-sky local-observer Lorentz response with a processed
cut-sky estimator. The resulting physical low-source response is identifiable
only modulo a declared high-source nuisance image. We prove an exact quotient
rank identity and a nested-image short circuit. For a registered continuum
wide-mask operator, source multipoles through `L=12` give exact full row rank in
the axial direction and dual-algorithm numerical full row rank in the other
five registered directions. This continuum result does not certify the finite
HEALPix implementation. We therefore derive a matrix-valued numerical-error
envelope, invariant under compensated family rescaling, and a conditional
error-whitened robust-rank theorem. The present finite-operator result remains
rank unresolved because completeness of the numerical-error class has not been
established. No corrected Planck tensorized rank, empirical observer velocity,
global matter-frame tilt, physical shear or vorticity measurement, foreground
cause, or Bianchi-family attribution is reported.

## 1. Introduction

The lowest CMB multipoles encode a finite-dimensional angular field with both
amplitude and morphology. For a real temperature anisotropy, the quadrupole and
octupole contain five and seven real degrees of freedom, respectively. Power
spectra retain only two radial combinations. A small collection of additional
scalar contractions can reveal more structure, but unless it separates the
appropriate rotation orbits it is not an information-complete representation
of the pair.

A second and logically distinct issue is physical attribution. Even a complete
observable representation need not distinguish local observer motion,
intrinsic source anisotropy, global matter-frame tilt, foreground residuals, or
other effects once masking, beam and pixel transfer, fitting, and unresolved
source multipoles are included. The relevant object is then not an isolated
statistic, but the image and quotient geometry of the complete processed
response.

This work joins these two problems while preserving their separation. The first
part corrects and tensorizes the low-multipole observable. The second part
states what conditional scalar isotropy bounds do and do not imply. The third
part gives exact finite-null validity conditions. The fourth part studies local
observer response before and after a declared processing operator. The fifth
part formalizes numerical uncertainty in that operator.

The report is intentionally observation-independent. Historical scalar-only
MES ranks and pre-correction tensor/foreground/injection results are treated as
superseded provenance rather than current scientific results. All local Planck
and simulation reruns are deferred. Native Bianchi evolution, recombination,
reionization, and Einstein--Boltzmann solver construction are outside scope.
Bianchi models enter only as an example of a physical attribution that the
present observable does not identify by itself.

The main conclusions are:

1. the corrected `Q/O` tensors preserve information absent from scalar power
   summaries;
2. on a nonzero cyclic domain, a signed Krylov packet separates proper-rotation
   orbits and reconstructs a canonical representative;
3. MES-type scalar ceilings remain one-way, premise-conditioned norm
   functionals and do not tensorize the observation;
4. finite-null ranks are exact only when the complete adaptive analysis is
   row-equivariant under the relevant null symmetry;
5. processed low-source response is identified only in a quotient by the
   declared nuisance image;
6. the continuum wide-mask nuisance response is full row rank by `L=12` at the
   registered evidence grades;
7. the corresponding finite-HEALPix rank is not yet certified, because the
   numerical-error class and its provenance are incomplete.

## 2. Conventions and the corrected real harmonic carrier

We use metric signature

\[
g_{ab}=(-,+,+,+)
\]

and spatial orientation `epsilon_123=+1`. For a photon measured by an observer
with four-velocity `u^a`,

\[
p^a=\frac{\epsilon}{c}(u^a+e^a),
\qquad e^ae_a=1,
\qquad e^au_a=0.
\]

The outward sky direction is

\[
n^a=-e^a.
\]

Let

\[
T(\hat n)=\sum_{\ell m}a_{\ell m}Y_{\ell m}(\hat n)
\]

with Condon--Shortley harmonics and reality condition

\[
a_{\ell,-m}=(-1)^m a_{\ell m}^*.
\]

For each multipole define the orthonormal stored-real carrier

\[
c_{\ell0}=a_{\ell0},
\]

\[
c_{\ell m,c}=\sqrt2\,\Re a_{\ell m},
\qquad
c_{\ell m,s}=-\sqrt2\,\Im a_{\ell m},
\qquad m>0.
\]

Then

\[
\|c_\ell\|_2^2
 =|a_{\ell0}|^2+2\sum_{m=1}^{\ell}|a_{\ell m}|^2
 =\sum_{m=-\ell}^{\ell}|a_{\ell m}|^2
 =(2\ell+1)C_\ell.
\]

This Euclidean carrier is the representation used for tensorization. A second
real coordinate appears in the processed-response code:

\[
r_{\ell0}=a_{\ell0},
\qquad
r_{\ell m,R}=\Re a_{\ell m},
\qquad
r_{\ell m,I}=\Im a_{\ell m}.
\]

It has Parseval metric

\[
G_\ell=\operatorname{diag}(1,2,2,\ldots,2).
\]

The two coordinates are related by an invertible diagonal map

\[
c_\ell=D_\ell r_\ell,
\qquad
D_\ell^TD_\ell=G_\ell.
\]

They are mathematically equivalent but not byte-identical. All metric singular
values and rank comparisons must either be performed in the `c_l` coordinate
or retain `G_l` explicitly.

## 3. Quadrupole and octupole tensors

Define

\[
T_2(\hat n)=Q_{ab}n^an^b,
\qquad
Q_{ab}=Q_{(ab)},
\qquad
Q^a{}_a=0,
\]

and

\[
T_3(\hat n)=O_{abc}n^an^bn^c,
\qquad
O_{abc}=O_{(abc)},
\qquad
O^a{}_{ac}=0.
\]

The real vector spaces have dimensions

\[
\dim\operatorname{STF}_2(\mathbb R^3)=5,
\qquad
\dim\operatorname{STF}_3(\mathbb R^3)=7.
\]

With the harmonic convention of Section 2, the linear harmonic--STF maps obey

\[
\boxed{
Q:Q=\frac{15}{8\pi}\|c_2\|_2^2
     =\frac{75}{8\pi}C_2,
}
\]

\[
\boxed{
O:O=\frac{35}{8\pi}\|c_3\|_2^2
     =\frac{245}{8\pi}C_3.
}
\]

These identities fix the radial normalization used throughout the report. The
pair `(Q,O)` contains twelve real coordinates. On a locally free `SO(3)`
stratum the orbit dimension is three and the generic quotient dimension is
nine. This dimension count does not extend without modification to strata with
nontrivial stabilizer.

## 4. Proper-rotation orbit reconstruction on the cyclic domain

For nonzero tensors define amplitudes

\[
A_Q=\sqrt{Q:Q},
\qquad
A_O=\sqrt{O:O}
\]

and normalized tensors

\[
\bar Q=Q/A_Q,
\qquad
\bar O=O/A_O.
\]

Contract the normalized tensors to obtain

\[
v_a=\bar O_{abc}\bar Q_{bc}
\]

and define the Krylov matrix

\[
\mathscr K_{QO}
 =[v,\bar Qv,\bar Q^2v].
\]

If the eigenvalues of `Qbar` are `lambda_i` and the eigenframe components of
`v` are `v_i`, then

\[
\det\mathscr K_{QO}
 =v_1v_2v_3\prod_{i<j}(\lambda_j-\lambda_i)
\]

up to the sign fixed by the displayed column and eigenvalue ordering. Thus the
cyclic domain

\[
\mathcal D_{\rm cyc}
 =\{(Q,O):A_QA_O\det\mathscr K_{QO}\ne0\}
\]

is precisely the domain on which `Qbar` has simple spectrum and `v` has a
nonzero component along every eigen-direction. The proper-rotation stabilizer
is then trivial.

Let

\[
s_2=\operatorname{tr}\bar Q^2=1,
\qquad
s_3=\operatorname{tr}\bar Q^3,
\]

\[
\mu_r=v^T\bar Q^rv,
\qquad r=0,1,2,
\]

and

\[
\chi=\det\mathscr K_{QO}.
\]

For `0<=i<=j<=k<=2`, define ten contractions

\[
\tau_{ijk}
 =\bar O(\bar Q^iv,\bar Q^jv,\bar Q^kv).
\]

Together with the two amplitudes, these form the overcomplete packet used in
the current implementation. The trace-free Cayley--Hamilton identity

\[
\bar Q^3
 =\frac{s_2}{2}\bar Q+\frac{s_3}{3}I
\]

determines

\[
\mu_3=\frac{s_2}{2}\mu_1+\frac{s_3}{3}\mu_0,
\qquad
\mu_4=\frac{s_2}{2}\mu_2+\frac{s_3}{3}\mu_1.
\]

Hence the packet determines the Gram matrix

\[
G=\mathscr K_{QO}^T\mathscr K_{QO}
 =\begin{pmatrix}
\mu_0&\mu_1&\mu_2\\
\mu_1&\mu_2&\mu_3\\
\mu_2&\mu_3&\mu_4
\end{pmatrix},
\qquad
\det G=\chi^2.
\]

Choose a factor `B` satisfying

\[
B^TB=G,
\qquad
\det B=\chi,
\]

by taking the positive-diagonal Cholesky factor and reversing one row when the
signed volume is negative. In the Krylov basis, multiplication by `Qbar` has
companion matrix

\[
C=
\begin{pmatrix}
0&0&s_3/3\\
1&0&s_2/2\\
0&1&0
\end{pmatrix}.
\]

The reconstructed quadrupole is

\[
\bar Q_{\rm can}=BCB^{-1}.
\]

The moment identities imply `C^T G=G C`, so this matrix is symmetric; its
traces reproduce `s_2` and `s_3`. Extending the ten `tau_ijk` to a fully
symmetric coordinate tensor `T_ijk`, the reconstructed octupole is

\[
(\bar O_{\rm can})_{abc}
 =(B^{-1})_{ia}(B^{-1})_{jb}(B^{-1})_{kc}T_{ijk}.
\]

For a packet in the image of the construction, this tensor is symmetric,
trace-free, and unit-normalized.

If `K` is the original Krylov matrix and `B` is the reconstructed canonical
one, then

\[
R=B\mathscr K_{QO}^{-1}
\]

satisfies

\[
R^TR=I,
\qquad
\det R=1.
\]

Therefore `R` is a proper rotation and maps the original normalized pair to
the canonical reconstruction. Equal packets imply equal canonical
representatives and hence the same `SO(3)` orbit on `D_cyc`.

The signed volume is an `SO(3)` scalar and `O(3)` pseudoscalar. The named
ordinary compression

\[
(Q:Q,\ O:O,\operatorname{tr}Q^3,\ Q_{ij}O_{ikl}O_{jkl})
\]

is unchanged under `O -> -O`, whereas `chi` changes sign. Every cyclic pair
therefore supplies a mirror counterexample to separation by that compression.
This does not establish non-separation of every conceivable bispectrum.

The theorem is deliberately limited. It does not characterize the intrinsic
algebraic image of every arbitrary sixteen-component packet, cover the zero,
repeated-spectrum, contraction-null, or noncyclic strata, or establish a full
polynomial invariant ring. On unavailable or numerically ill-conditioned
strata the original tensors are retained and no axis is fabricated.

## 5. Conditional MES geometry

The corrected PSTF multipole amplitudes are

\[
\epsilon_2
 =\frac1{T_0}\sqrt{\frac{75C_2}{8\pi}},
\qquad
\epsilon_3
 =\frac1{T_0}\sqrt{\frac{245C_3}{8\pi}}.
\]

Let `epsilon_1` denote a declared residual PSTF dipole norm divided by `T0`.
For the retained geodesic reduction, define

\[
B_\sigma
 =\frac53\epsilon_1+3\epsilon_2+\frac37\epsilon_3,
\]

\[
B_\omega
 =\frac{10}{3}\epsilon_1+\frac{2}{15}\epsilon_2,
\]

and

\[
U_\sigma=\frac32B_\sigma^2,
\qquad
U_\omega=\frac32B_\omega^2.
\]

These quantities are scalar functions of declared multipole norms under a
specified congruence, frame, perturbative branch, Copernican extension, and
derivative-hierarchy reduction. They provide a one-way implication from the
premises to a bound. Compliance with a bound does not prove the premises or a
converse FLRW statement. Setting `epsilon_1=0` is an attribution scenario, not
an observation that the intrinsic dipole vanishes.

There is also a representation-theoretic obstruction to promoting these
scalars into tensor morphology. If a map from rotational scalars to a vector
or nonzero STF tensor were equivariant under all rotations, its output would
have to be fixed by every rotation. The only such vector or STF tensor is zero.
Additional directional information is therefore necessary.

## 6. Finite-null ranks with adaptive tensor statistics

Let

\[
Z=(Z_0,Z_1,\ldots,Z_N)
\]

be an observation and `N` reference rows. Let the complete analysis algorithm
produce row scores

\[
S(Z)=(S_0(Z),\ldots,S_N(Z)).
\]

The algorithm includes tensor construction, coordinate or chart availability,
feature selection, nuisance fitting, missingness handling, tie conventions,
and final scoring.

Assume the pooled rows are jointly exchangeable under the null and that the
complete algorithm is row-permutation equivariant:

\[
S_i(\pi Z)=S_{\pi^{-1}i}(Z)
\]

for every row permutation `pi`. The conservative upper-tail rank

\[
p(Z)=\frac{1+\sum_{i=1}^{N}
\mathbf 1\{S_i(Z)\ge S_0(Z)\}}{N+1}
\]

is then super-uniform under the null. In a tie-free exchangeable pool it is
uniform on the finite grid `1/(N+1),...,1`.

Adaptive selection is not automatically invalid. It remains valid when the
entire selection-and-score construction commutes with row permutations, or
when selection is performed in an independent split under a separately valid
contract. Observation-specific feature selection with the reference rows held
fixed breaks the symmetry. A finite four-row counterexample in the theorem
pack rejects at level `1/4` with probability `1/2`.

Chart failure is part of the row map. Deleting only reference rows whose
Krylov chart is unavailable changes the effective null law and invalidates the
simple exchangeable-rank argument. A valid analysis must use a statistic
defined for every row, apply a symmetric pool-level rule, or abstain.

Finally, null fidelity is separate from rank arithmetic. A noisy observed map
and noise-free CMB-only simulations are not exchangeable merely because the
same scalar score is evaluated. Evidence products sharing the same observed
sky or simulation rows cannot be multiplied as independent without a declared
dependence model.

## 7. Exact full-sky local-observer response

Let the observer undergo an active local boost

\[
\widetilde u^a=\gamma(u^a+\beta_{\rm obs}^a),
\qquad
\gamma=(1-\beta_{\rm obs}^2)^{-1/2}.
\]

For thermodynamic temperature with Doppler weight one, the exact full-sky
pullback can be written

\[
\widetilde T(\widetilde n)
 =\frac{T(n(\widetilde n))}
 {\gamma(1-\beta_{\rm obs}\cdot\widetilde n)}
\]

on strictly positive absolute-temperature skies, with the appropriate inverse
aberration map `n(n_tilde)`. At first order,

\[
\delta_\beta T
 =(\beta_{\rm obs}\cdot n)T
 -[\beta_{\rm obs}
 -(\beta_{\rm obs}\cdot n)n]\cdot\nabla_{S^2}T.
\]

For a quadrupole `Q_ab`, the induced STF3 response is

\[
\boxed{
(B_Q\beta)_{abc}
 =3\beta_{\langle a}Q_{bc\rangle}.
}
\]

Its adjoint normal matrix is

\[
\boxed{
M_Q=q_2I+\frac65Q^2,
\qquad q_2=Q:Q.
}
\]

The eigenvalue constraints of a trace-free symmetric `3x3` tensor imply the
sharp nonzero condition bound

\[
\boxed{\kappa_2(M_Q)\le\frac53.}
\]

The algebraic inverse yields the ideal full-sky local-observer component, while
an orthogonal four-dimensional STF3 residual remains outside the quadrupole
boost image. This residual is a response-space object, not automatically an
intrinsic physical octupole.

A local observer boost is not a global radiation--matter tilt. The two require
different state variables and forward models.

## 8. Processed cut-sky response

The finite processed operator uses the fixed order

```text
positive absolute thermodynamic-temperature sky
→ finite or first-order local observer boost
→ source beam and pixel-window transfer
→ HEALPix synthesis
→ weighted joint ell=0..5 fit
→ post-fit target/source commonization
→ retained ell=2..5 carrier.
```

The low-source coordinate contains physical `T0` and raw real harmonic
coordinates through `ell=6`, giving 49 columns. The retained output has 32
coordinates. The first-order Jacobian has shape

\[
J\in\mathbb R^{3\times32\times49}.
\]

A constant physical monopole produces a pure dipole at first order. Because the
joint fit includes `ell=0,1` and the retained output starts at `ell=2`, the
physical `T0` column is an exact structural null. Finite HEALPix replay leakage
is recorded separately.

Using the source and retained Parseval metrics, the full-sky anisotropy response
has source-sector squared singular values

\[
\left\{
\frac83,\frac{27}{5},13,21,
\frac{125}{11},\frac{216}{13}
\right\}
\]

with multiplicities `(3,5,7,9,11,13)`. The anisotropy rank is 48 and the
nonzero-subspace condition number is

\[
\sqrt{63/8}=2.80624304008\ldots.
\]

For a fixed boost direction `bhat`, let

\[
J_{\hat b}\in\mathbb R^{32\times48}
\]

be the low-source response after removing the structural monopole null. Let

\[
K_{\hat b}^{\rm hi}(L)
 = [K_{\hat b}^{(7)}|\cdots|K_{\hat b}^{(L)}]
\]

be the response of unrestricted deterministic source multipoles `7<=ell<=L`.
The high-source dimension is

\[
d_H(L)=(L-6)(L+8).
\]

Define

\[
\mathcal L_{\hat b}=\operatorname{Im}J_{\hat b},
\qquad
\mathcal H_{\hat b}(L)=
\operatorname{Im}K_{\hat b}^{\rm hi}(L).
\]

The model-free surviving response is

\[
J_{\rm surv}(L)
 =P_{\mathcal H_{\hat b}(L)^\perp}J_{\hat b}.
\]

Finite-dimensional linear algebra gives

\[
\boxed{
\operatorname{rank}J_{\rm surv}(L)
 =\operatorname{rank}[K_{\hat b}^{\rm hi}(L)\ J_{\hat b}]
  -\operatorname{rank}K_{\hat b}^{\rm hi}(L).
}
\]

The cumulative nuisance images are nested in `L`. Once robust containment is
certified at a finite cutoff, larger cutoffs cannot restore a model-free
survivor. Column count alone is not a rank proof.

A frozen seven-case cut-sky atlas found no candidate satisfying all registered
conditioning, source-`ell=6` alias, and high-source-tail gates. The wide
apodization substantially improved conditioning but retained alias and tail
ratios above unity. A subsequent matched-control analysis produced 17
rank-ambiguous direction/cutoff coordinates, one resolved coordinate with an
11-dimensional survivor, no containment candidate, and unstable control-factor
sensitivity. The finite-operator terminal is therefore rank unresolved.

## 9. Continuum high-source response

For the wide axisymmetric mask, define the continuum weighted normal matrix

\[
N_{\alpha\beta}
 =\int wY_\alpha^*Y_\beta\,d\Omega
\]

and boost-response right-hand side

\[
R_{\alpha p}^{(\hat b)}
 =\int wY_\alpha^*\mathcal B_{\hat b}Y_p\,d\Omega.
\]

The continuum processed high-source matrix is

\[
K_{\hat b}^{\rm cont}(L)
 =P_{2:5}N^{-1}R_{\hat b}^{7:L}.
\]

For the axial direction, exact rational weighted integrals and nonzero block
minors give complex block ranks

\[
(4,4,4,3,2,1)
\]

at `L=12`, hence stored-real rank 32. Independent high-precision Wolfram and
direct piecewise quadrature calculations give the rank ladder

\[
\begin{array}{c|ccc}
L&Z&X/Y&\mathrm{diagonal}\\\hline
8&20&24&24\\
9&27&29&32\\
12&32&32&32
\end{array}.
\]

At `L=12`, the smallest metric singular values are approximately

\[
0.00690566498\quad(Z),
\]

\[
0.01049033491\quad(X/Y),
\]

\[
0.00851032278\quad(\mathrm{diagonal}).
\]

The axial rank is exact. The other five directions have dual-algorithm
high-precision numerical evidence but no portable interval enclosure. On the
continuum operator, the registered high-source band therefore spans the
retained carrier at the stated evidence grades. Nestedness makes larger cutoffs
unnecessary for this deterministic continuum rank question.

The conclusion does not pass automatically to finite HEALPix. Weak continuum
singular modes can lie below the error of a discretized transform and weighted
solve. The continuum and finite-operator results are therefore compatible:
continuum surjectivity is strongly supported, while finite-operator robust rank
remains unresolved.

## 10. Matrix-valued numerical uncertainty

Let each frozen numerical-error family contain matrices `E_fi`, with
deterministic coefficient ball

\[
\Delta_f=\sum_i b_{fi}E_{fi},
\qquad
\|b_f\|_2\le r_f.
\]

For

\[
\Delta=\sum_{f=1}^{N_{\rm fam}}\Delta_f,
\]

Cauchy--Schwarz at the matrix-family and family levels gives

\[
\Delta\Delta^T
\preceq
N_{\rm fam}\sum_fr_f^2\sum_iE_{fi}E_{fi}^T.
\]

Define

\[
\boxed{
\Gamma_E
 =N_{\rm fam}\sum_fr_f^2\sum_iE_{fi}E_{fi}^T
  +\lambda_{\rm reg}^2I.
}
\]

The envelope is invariant under compensated family rescaling

\[
E_{fi}\mapsto c_fE_{fi},
\qquad
r_f\mapsto r_f/c_f,
\]

and under orthogonal basis mixing inside a family. An exactly zero family must
be omitted or rejected because it leaves the perturbation set unchanged while
changing `N_fam`.

If the true numerical error obeys

\[
\Delta\Delta^T\preceq\Gamma_E,
\]

then

\[
\|\Gamma_E^{-1/2}\Delta\|_2\le1.
\]

For

\[
\widetilde K_{\rm obs}
 =\Gamma_E^{-1/2}K_{\rm obs},
\]

Weyl's inequality gives

\[
\sigma_j(\Gamma_E^{-1/2}K_{\rm true})
\ge
\sigma_j(\widetilde K_{\rm obs})-1.
\]

Every error-whitened singular value above a preregistered margin `1+delta_g`
contributes one robust rank lower bound. All 32 above the margin certify full
row rank for the declared error class.

This is a conditional theorem. The family partition, basis, radii,
regularization, calibration set, holdout set, coordinate identities, and
processing settings must be content-bound before the rank outcome is inspected.
A finite holdout pass tests only that finite registry. It does not prove that
all unobserved numerical errors belong to the class.

A partial robust rank lower bound also does not identify a stable singular
subspace. A Wedin-type perturbation theorem requires a positive singular-value
gap and yields a projector-angle bound. Only if the observed survivor exceeds
the propagated projector uncertainty may a true partial survivor be certified.

The current source implements the envelope and typed rank/holdout machinery,
but its exact-head workflows did not start. More importantly, the actual
finite-HEALPix error-family completeness and radii are not scientifically
sealed. The finite-operator conclusion therefore remains unresolved.

## 11. Integrated interpretation

The framework separates three levels that are often conflated.

First, **observable representation** asks whether a coordinate system preserves
the morphology present in the sky. The corrected `Q/O` tensors and cyclic-domain
Krylov packet retain proper-rotation information absent from a small scalar
compression.

Second, **conditional physical bounds** ask what follows after a congruence,
frame, perturbative branch, derivative hierarchy, and attribution scenario are
declared. MES-type functionals bound norm combinations under those premises;
they do not infer a tensor field from scalar power.

Third, **identifiability** asks whether distinct source hypotheses induce
distinct processed observables. Even a complete tensor representation can lose
identifiability when high-source response occupies the same retained carrier.
The appropriate result is then a quotient or an identified set, not a forced
point estimate.

The continuum calculation shows that an unrestricted deterministic high-source
band can span the retained carrier in the registered wide-mask model. This is
a statement about the declared response class, not a statement that real
high-multipole skies have unbounded amplitude. Physical covariance or prior
models, polarization, frequency dependence, additional angular modes, and
independent depth or remote-field information can refine the quotient. Their
information content must be demonstrated under their own response and
statistical contracts.

Local observer motion and global matter-frame tilt remain different physical
hypotheses. Neither the tensorized morphology nor the response quotient licenses
Bianchi-family attribution without a separate forward model.

## 12. Current evidence status and deferred observations

The current theory status is:

```text
corrected harmonic/STF representation: derived and exact-Wolfram checked
Q/O cyclic-domain orbit reconstruction: derived and exact-Wolfram checked
conditional MES geometry: derived/literature-supported at typed premises
finite-null theorem: derived at explicit symmetry premises
WU010 local-observer response: implementation-verified at frozen scope
WU011 quotient theory: derived; frozen Task7B/7C numerical evidence retained
continuum L12 response: z exact, other five directions numerical
matrix numerical-error theorem: derived; actual error-class completeness open
finite-HEALPix robust containment: unresolved
```

The observational gate is closed:

```text
CURRENT_CORRECTED_TENSORIZED_PLANCK_RANK = NONE
PLANCK_OR_FFP10_EXECUTION = DEFERRED_BY_OWNER
```

No placeholder anomaly rank is inserted. Historical scalar or withdrawn tensor
results are not used as substitutes.

## 13. Conclusions

We have constructed a theory-first framework for low-multipole CMB inference
that separates representation, conditional bounds, finite-sample calibration,
and processed-response identifiability.

The corrected stored-real carrier maps isometrically to the temperature
quadrupole and octupole. On a nonzero cyclic domain, a signed Krylov packet
reconstructs a canonical proper-oriented representative and separates `SO(3)`
orbits, while preserving typed singular strata outside its domain. MES-type
shear and vorticity functions remain one-way scalar bounds under explicit
premises and cannot replace tensor morphology. Observation-inclusive finite
ranks require symmetry of the complete adaptive analysis, not merely reuse of
the same final formula.

An exact full-sky local-observer response is well conditioned at the
quadrupole-to-octupole level, but masking and unresolved source modes change the
identifiability problem. The processed response is naturally a quotient by a
high-source nuisance image. The registered continuum nuisance response becomes
full row rank by `L=12` at the stated exact/numerical evidence grades. The
finite-HEALPix implementation remains unresolved because numerical-error
completeness has not been certified. A matrix-valued error envelope gives a
conditional route to robust rank without collapsing directional numerical
structure to one scalar floor.

The report therefore supports a strong but limited conclusion: tensorization
preserves observable morphology, whereas physical attribution is controlled by
the full processed response and its uncertainty class. Corrected observational
analysis is a separate future step.

---

# Appendix A. Evidence and claim taxonomy

Every statement used in the final manuscript is assigned separate fields for:

```text
mathematical truth
primary literature support
direct derivation
numerical verification
source implementation
accepted runtime
scientific terminal
novelty
publication status
```

A source file, passing local transcription, GitHub workflow, scientific result,
and publishable claim are not synonyms.

# Appendix B. Typed strata and abstention

The Q/O cyclic chart refuses zero amplitudes, contraction-null configurations,
repeated quadrupole spectra, noncyclic contraction vectors, and numerical
condition-limit violations. A finite-null analysis must use a row-equivariant
fallback or abstain at the pool level. Chart failure is never imputed as a zero
statistic.

# Appendix C. Response-rank vocabulary

We distinguish:

\[
\operatorname{rank}_{\rm alg}(M),
\quad
\operatorname{rank}_{\rm num}(M;\tau),
\quad
\operatorname{rank}_{\rm rob}(M;\Gamma_E),
\]

\[
\operatorname{rank}_{\rm quot}(J|K)
 =\operatorname{rank}[K\ J]-\operatorname{rank}K,
\]

and the finite-pool order rank used in randomization inference. Bare `rank` is
avoided where more than one meaning is in scope.

# Appendix D. Citation and novelty work still required

Before release, every literature-supported statement must be bound to an exact
primary source and matched assumptions. In particular:

- the MES coefficient and premise matrix requires page/equation-level primary
  binding;
- the Q/O Krylov theorem requires a dedicated novelty comparison with invariant
  theory for `V_2 direct-sum V_3`;
- the finite-null theorem requires exact randomization/exchangeability
  citations;
- the partial-subspace section requires a precise Wedin-type theorem statement;
- masked boost and transfer claims require direct harmonic-response sources.

Failure to find a directly matching Q/O reconstruction source will be reported
as `no direct match found in the searched corpus`, not as proof of novelty.

# Appendix E. Reproducibility boundary

The theorem and evidence packs are stored under

```text
docs/research_reports/theory_packs/
docs/codex_handoff/htt_tensorized_report_first_20260903/
```

with explicit Git authority identities. The final report must flatten the T9
claim-count correction overlay into a self-contained ledger, bind every source
and figure hash, rerun supported-runtime checks where available, and preserve
all unresolved execution blockers.
