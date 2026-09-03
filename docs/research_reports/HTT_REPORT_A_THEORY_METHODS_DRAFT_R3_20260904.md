# Tensorized Low-Multipole CMB Inference under Conditional Isotropy Bounds and Response-Limited Identifiability

**R3 flattened draft — theory and methods report**  
Date: 2026-09-04  
Repository: `cosmosapjw-quantum/htt_base`  
Status: theory/methods release candidate under audit; observational execution remains deferred.

```text
CURRENT_CORRECTED_TENSORIZED_PLANCK_RANK = NONE
CURRENT_OBSERVATIONAL_RESULT = NONE
FINITE_HEALPIX_CONTAINMENT = RANK_UNRESOLVED
```

This report is generated from the canonical 30-claim ledger, its 30-row citation/provenance matrix, the formal 17-key bibliography, and the R2/R3 independent audits. The neutral source-disposition surface contains 37 rows—36 `INCLUDED` and one `DEFERRED`—but those rows are not a count of unique theorems. The publication-facing claim surface contains 30 atomic claims with separate truth, implementation, execution, and scope fields.

## Abstract

Low-multipole cosmic-microwave-background analyses are often compressed to powers or a few scalar anomaly statistics. Such summaries can be useful, but they neither preserve the complete tensor morphology of the quadrupole and octupole nor identify the physical origin of an observed anisotropy. We develop an observation-independent theory and methods framework that separates tensor representation, conditional isotropy bounds, finite-null calibration, and processed-response identifiability.

An orthonormal stored-real harmonic carrier maps exactly to symmetric trace-free tensors \(Q_{ab}\) and \(O_{abc}\). On a declared nonzero cyclic domain, two amplitudes and an overcomplete Krylov packet reconstruct a canonical proper-oriented representative and separate \(SO(3)\) orbits for packets in the forward image. The inverse must enforce the normalized image relation

\[
\bar O:\bar Q=\mathscr K_{QO}e_0,
\qquad
O:Q=A_QA_O\,\mathscr K_{QO}e_0,
\]

as well as complete packet replay. A signed Krylov determinant distinguishes a registered mirror pair sharing a named power/cubic-bispectrum compression. No global invariant-ring or all-strata completeness statement is made.

Maartens–Ellis–Stoeger-type shear and vorticity ceilings are retained only as one-way, premise-conditioned scalar functionals of multipole norms [@MES_1995_LIMITS] [@MES_1995_IMPROVED] [@SAG_1999_COBE]. Rotational scalars cannot equivariantly generate nonzero vector or STF morphology without additional directional information.

Two finite-sample constructions are kept distinct. Jointly exchangeable observation/reference rows, together with row-permutation equivariance of the complete adaptive algorithm, yield a conservative observation-inclusive rank. A finite randomization test instead ranks a statistic over the actual orbit of a declared null-invariant transformation group, or over a valid identity-including conditional-Monte-Carlo sample of that orbit [@RANDOMIZATION_2024] [@PHIPSON_SMYTH_2010] [@HEMERIK_GOEMAN_2018]. Proper-subgroup invariance does not license comparison with arbitrary rows outside the subgroup orbit.

We combine the exact full-sky thermodynamic-temperature local-observer Lorentz response [@DAI_CHLUBA_2014] [@YASINI_PIERPAOLI_2017] with a declared processed cut-sky estimator. The low-source response is identified only modulo a high-source nuisance image. We prove an exact quotient-rank identity and a nested-image short circuit. In a registered continuum wide-mask model, high-source multipoles through \(L=12\) have exact full row rank in the axial direction and independent high-precision numerical full row rank in the other five registered directions. This continuum result does not certify finite-HEALPix full row rank; the last byte-exact matched-control finite operator remains rank unresolved.

Finally, we derive a matrix-valued numerical-error envelope for a frozen additive family-ball class. It is invariant under compensated family scaling and family-internal orthogonal mixing and gives a conditional error-whitened robust-rank lower bound. A partial singular-subspace interpretation requires a separate perturbation-to-gap bound [@CAI_ZHANG_2018] [@LI_1999] [@LYU_WANG_2020]. No current scalar-only MES rank, corrected Planck tensor rank, empirical observer velocity, boost subtraction, global matter-frame tilt, physical shear or vorticity estimate, foreground cause, or Bianchi-family attribution is reported.

## 1. Scope, authority, and supersession

The report is HTT-only. It composes several Git-diverged evidence lineages by exact source and content identity rather than representing them as one linear history. The tensorized \(Q/O\) semantics, local-observer response, processed-response construction, survivor extraction, numerical decoder repairs, and report control plane remain separately attributable. Detailed branch, test, and execution status is confined to the provenance appendix rather than the scientific abstract.

The scope firewall is literal:

- scalar-only MES observational ranks are historical provenance, not current scientific results;
- historical WU-006–008 tensor-rank, foreground, and carrier-injection interpretations remain withdrawn;
- no corrected tensorized Planck result exists in the present phase;
- local observer motion is not identified with global matter-frame tilt;
- no finite-HEALPix no-go theorem is claimed;
- no native BASS solver, background evolution, recombination, or reionization result enters the claim surface.

Bianchi models may appear only as examples of physical attributions that are not identified by the present observable without an independent forward model. These restrictions are `RA-SCOPE-001` and `RA-BOUNDARY-001`.

## 2. Conventions and real harmonic coordinates

We use metric signature

\[
g_{ab}=(-,+,+,+),
\qquad
\epsilon_{123}=+1.
\]

For a photon measured by a four-velocity \(u^a\),

\[
p^a=\frac{E_\gamma}{c}(u^a+e^a),
\qquad
u^a e_a=0,
\qquad
e^a e_a=1,
\]

and the outward sky direction is

\[
n^a=-e^a.
\]

For a real temperature field,

\[
T(\hat n)=\sum_{\ell m}a_{\ell m}Y_{\ell m}(\hat n),
\qquad
a_{\ell,-m}=(-1)^m a_{\ell m}^{*}.
\]

The orthonormal stored-real carrier is

\[
c_{\ell0}=a_{\ell0},
\qquad
c_{\ell m,c}=\sqrt2\,\Re a_{\ell m},
\qquad
c_{\ell m,s}=-\sqrt2\,\Im a_{\ell m},
\quad m>0.
\]

It obeys

\[
\|c_\ell\|_2^2
=\sum_{m=-\ell}^{\ell}|a_{\ell m}|^2
=(2\ell+1)C_\ell.
\]

This is `RA-REP-001`. A second raw complex-component coordinate,

\[
r_{\ell0}=a_{\ell0},
\qquad
r_{\ell m,R}=\Re a_{\ell m},
\qquad
r_{\ell m,I}=\Im a_{\ell m},
\]

has metric

\[
G_\ell=\operatorname{diag}(1,2,2,\ldots,2)
\]

and is related to the orthonormal carrier by

\[
c_\ell=D_\ell r_\ell,
\qquad
D_\ell^T D_\ell=G_\ell.
\]

This is `RA-REP-002`. The two coordinate systems are semantically equivalent but not byte-identical; raw-coordinate singular values are not compared without the metric adapter.

## 3. Exact \(Q/O\) tensorization

Define

\[
T_2(\hat n)=Q_{ab}n^a n^b,
\qquad
Q_{ab}=Q_{(ab)},
\qquad
Q^a{}_a=0,
\]

and

\[
T_3(\hat n)=O_{abc}n^a n^b n^c,
\qquad
O_{abc}=O_{(abc)},
\qquad
O^a{}_{ac}=0.
\]

The representation dimensions are

\[
\dim\mathrm{STF}_2(\mathbb R^3)=5,
\qquad
\dim\mathrm{STF}_3(\mathbb R^3)=7.
\]

With the stored-real convention,

\[
\boxed{Q:Q=\frac{15}{8\pi}\|c_2\|_2^2
=\frac{75}{8\pi}C_2},
\]

\[
\boxed{O:O=\frac{35}{8\pi}\|c_3\|_2^2
=\frac{245}{8\pi}C_3}.
\]

These identities are `RA-REP-003`. On a locally free stratum, the generic proper-rotation quotient has dimension

\[
5+7-3=9,
\]

which is the conditional statement `RA-ORBIT-001`. It is distinct from the 14-dimensional quotient of an \(\mathrm{STF}_2\oplus V_1^{\oplus4}\) representation. A dimension count is not a global orbit atlas and is not extended to singular strata.

General tensor-invariant and orbit-space literature supplies adjacent methods and comparison points [@OLIVE_KOLEV_AUFFRAY_2013] [@BORNSEN_VANDEVEN_2018] [@LOPATIN_FERREIRA_2018]. The current search did not find a primary source stating the exact \(Q/O\) Krylov reconstruction below. That absence is not a novelty proof.

## 4. Proper-rotation reconstruction on the nonzero cyclic chart

Let

\[
A_Q=(Q:Q)^{1/2},
\qquad
A_O=(O:O)^{1/2},
\]

and, when both are nonzero,

\[
\bar Q=Q/A_Q,
\qquad
\bar O=O/A_O.
\]

Define

\[
v_a=\bar O_{abc}\bar Q_{bc},
\qquad
\mathscr K_{QO}=[v,\bar Qv,\bar Q^2v].
\]

In an eigenframe of \(ar Q\),

\[
\det\mathscr K_{QO}
=v_1v_2v_3\prod_{i<j}(\lambda_j-\lambda_i)
\]

up to the fixed ordering convention. Hence the chart is cyclic precisely when \(ar Q\) has simple spectrum and \(v\) has a nonzero component along every eigenvector.

Let

\[
s_2=\operatorname{tr}\bar Q^2=1,
\qquad
s_3=\operatorname{tr}\bar Q^3,
\]

\[
\mu_r=v^T\bar Q^r v\quad(r=0,1,2),
\qquad
\chi=\det\mathscr K_{QO},
\]

and

\[
\tau_{ijk}=\bar O(\bar Q^iv,\bar Q^jv,\bar Q^kv),
\qquad
0\le i\le j\le k\le2.
\]

Cayley–Hamilton gives

\[
\bar Q^3=\frac{s_2}{2}\bar Q+\frac{s_3}{3}I,
\]

and therefore

\[
\mu_3=\frac{s_2}{2}\mu_1+\frac{s_3}{3}\mu_0,
\qquad
\mu_4=\frac{s_2}{2}\mu_2+\frac{s_3}{3}\mu_1.
\]

The packet determines the Krylov Gram matrix

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

Choose \(B\) with

\[
B^TB=G,
\qquad
\det B=\chi,
\]

and define

\[
C=\begin{pmatrix}
0&0&s_3/3\\
1&0&s_2/2\\
0&1&0
\end{pmatrix}.
\]

Then

\[
\bar Q_{\rm can}=BCB^{-1}.
\]

The ten symmetric trilinear entries define a coordinate tensor \(T_{ijk}\). On the exact packet image,

\[
(\bar O_{\rm can})_{abc}
=(B^{-1})_{ia}(B^{-1})_{jb}(B^{-1})_{kc}T_{ijk}
\]

is symmetric, trace-free, and unit normalized. The packet-image conditions include

\[
Ce_0=e_1,
\qquad
C^2e_0=e_2,
\]

\[
\boxed{\bar O_{\rm can}:\bar Q_{\rm can}=Be_0}.
\]

Equivalently,

\[
\boxed{\bar O:\bar Q=\mathscr K_{QO}e_0},
\qquad
\boxed{O:Q=A_QA_O\,\mathscr K_{QO}e_0}.
\]

An image-safe numerical inverse must enforce these relations and complete forward replay. A stable construction may expand the octupole in a fixed Frobenius-orthonormal STF3 basis and solve the ten trilinear equations without applying an inverse Krylov basis in all three tensor slots. The orbit-separation theorem `RA-ORBIT-002` is restricted to nonzero cyclic packets in the valid forward image; it is not a theorem about arbitrary 16-vectors.

The signed volume \(\chi\) is invariant under \(SO(3)\) and odd under improper rotations. It separates a registered cyclic mirror pair sharing

\[
(Q:Q,\ O:O,\ \operatorname{tr}Q^3,\ Q_{ij}O_{ikl}O_{jkl}),
\]

which is `RA-ORBIT-003`. This does not establish non-separation by every conceivable bispectrum. Zero, contraction-null, repeated-spectrum, noncyclic, and condition-limit cases are typed strata; the original tensors and row identity are retained rather than fabricating an axis or imputing a zero statistic. This is `RA-ORBIT-004`.

## 5. MES quantities as conditional scalar functionals

The PSTF multipole normalization gives

\[
\epsilon_2=\frac1{T_0}\sqrt{\frac{75C_2}{8\pi}},
\qquad
\epsilon_3=\frac1{T_0}\sqrt{\frac{245C_3}{8\pi}},
\]

which is `RA-MES-001`. A residual dipole amplitude \(\epsilon_1\) is a declared attribution scenario, not a quantity inferred from the scalar bounds.

After the explicitly declared gradient and characteristic-time estimates, the retained geodesic reduction is

\[
B_\sigma=\frac53\epsilon_1+3\epsilon_2+\frac37\epsilon_3,
\]

\[
B_\omega=\frac{10}{3}\epsilon_1+\frac{2}{15}\epsilon_2,
\]

\[
U_\sigma=\frac32B_\sigma^2,
\qquad
U_\omega=\frac32B_\omega^2.
\]

The coefficients and premises are tied to the original MES and COBE-era PSTF sources [@MES_1995_LIMITS] [@MES_1995_IMPROVED] [@SAG_1999_COBE]. They remain one-way conditional scalar functionals under a declared congruence, frame, perturbative branch, Copernican extension, derivative-hierarchy reduction, and residual-dipole scenario (`RA-MES-002`). Bound compliance does not prove those premises, FLRW geometry, or physical saturation.

There is also an exact equivariance obstruction. A map from rotational scalars to a vector or nonzero STF tensor that is equivariant under every rotation must produce an object fixed by every rotation. The only such vector or STF tensor is zero. Additional directional data are necessary (`RA-MES-003`).

## 6. Finite-null statistics

### 6.1 Exchangeable-row rank

Let

\[
Z=(Z_0,Z_1,\ldots,Z_N)
\]

contain an observation and reference rows, and let the complete analysis return

\[
S(Z)=(S_0(Z),\ldots,S_N(Z)).
\]

“Complete” includes representation construction, chart status, adaptive selection, nuisance fitting, missingness, deterministic ties, and final scoring. Suppose the rows are jointly exchangeable under the null and

\[
S_i(\pi Z)=S_{\pi^{-1}i}(Z)
\]

for every row permutation \(\pi\). Then

\[
\boxed{
p_{\rm row}(Z)
=\frac{1+\sum_{i=1}^{N}\mathbf1\{S_i(Z)\ge S_0(Z)\}}{N+1}
}
\]

is conservative and super-uniform. This is `RA-STAT-001`.

### 6.2 Finite transformation-group randomization

A randomization test is a different construction. Let \(\mathcal G\) be a finite group under which the null law is invariant. The exact orbit rank is

\[
\boxed{
p_{\mathcal G}(Z)
=\frac1{|\mathcal G|}
\sum_{g\in\mathcal G}
\mathbf1\{T(gZ)\ge T(Z)\}
}.
\]

A random subset of transformations requires a valid identity-including conditional-Monte-Carlo rule [@RANDOMIZATION_2024] [@PHIPSON_SMYTH_2010] [@HEMERIK_GOEMAN_2018]. This is `RA-STAT-004`. Null invariance under a proper subgroup does not make arbitrary rows outside that orbit exchangeable.

An exact two-state counterexample makes the boundary explicit. Give probability \(1/2\) to each of

\[
z^{(1)}=(10,0,-100,-100),
\qquad
z^{(2)}=(0,10,-100,-100).
\]

The law is invariant under the group that swaps rows 0 and 1. Ranking row 0 against all four rows gives

\[
p_{\rm all}(z^{(1)})=\frac14,
\qquad
p_{\rm all}(z^{(2)})=\frac12,
\]

so

\[
\Pr(p_{\rm all}\le\tfrac12)=1>\frac12.
\]

The actual two-element orbit rank gives \(p_{\mathcal G}=1/2\) or \(1\), which is super-uniform.

### 6.3 Adaptive selection and null fidelity

Adaptive selection is valid only if the complete operation remains row-equivariant or if selection occurs in a separately valid independent design (`RA-STAT-002`). In the registered four-row exact counterexample:

- with ties assigned to coordinate 2, 12 permutations give \(p=1/2\) and 12 give \(p=3/4\);
- with ties assigned to coordinate 1, 6 permutations give \(p=1/2\) and 18 give \(p=3/4\);
- at \(\alpha=3/4\), rejection probability is one, an exact size excess \(1/4\);
- a pooled permutation-invariant selection rule has zero maximum super-uniformity violation.

Chart failure is part of the row map. Deleting only chart-unavailable reference rows while retaining the observation changes the effective null law. A valid analysis uses a statistic defined for every row, applies a symmetric pool-level fallback, or abstains.

Null fidelity is separate from rank arithmetic. A noisy observation and noise-free CMB-only simulations are not exchangeable without an explicit matched joint law (`RA-STAT-003`). Evidence products that share one observed sky or the same simulation rows are not independent replications without a declared dependence model.

## 7. Exact full-sky local-observer response

Let the observer undergo an active local boost

\[
\widetilde u^a=\gamma(u^a+\beta_{\rm obs}^a),
\qquad
\gamma=(1-\beta_{\rm obs}^2)^{-1/2}.
\]

For thermodynamic temperature with Doppler weight \(d=1\), the exact full-sky pullback on strictly positive absolute-temperature skies can be written

\[
\widetilde T(\widetilde n)
=\frac{T(n(\widetilde n))}
{\gamma(1-\beta_{\rm obs}\cdot\widetilde n)}.
\]

At first order,

\[
\delta_\beta T
=(\beta_{\rm obs}\cdot n)T
-[\beta_{\rm obs}-(\beta_{\rm obs}\cdot n)n]\cdot\nabla_{S^2}T.
\]

The exact pullback and its domain are `RA-RESP-001`. General Doppler-weight kernels delimit the frequency-dependent scope [@YASINI_PIERPAOLI_2017], and the distinction between local boost and intrinsic large-scale structure remains an interpretation question [@ROLDAN_NOTARI_QUARTIN_2016].

For a quadrupole,

\[
\boxed{(B_Q\beta)_{abc}=3\beta_{\langle a}Q_{bc\rangle}},
\]

and the adjoint normal matrix is

\[
\boxed{M_Q=q_2I+\frac65Q^2},
\qquad
q_2=Q:Q.
\]

The trace-free eigenvalue constraints imply

\[
\boxed{\kappa_2(M_Q)\le\frac53}.
\]

These are `RA-RESP-002`. The ideal inverse leaves a four-dimensional STF3 residual orthogonal to the quadrupole-response image. That residual is a response-space object, not automatically a physical intrinsic octupole. A local observer boost is not a global matter-frame tilt.

## 8. Processed cut-sky response and quotient geometry

The processed operator is ordered as follows (`RA-PROC-001`):

```text
positive absolute thermodynamic-temperature sky
→ exact or first-order local observer boost
→ source beam and pixel-window transfer
→ spherical synthesis
→ weighted joint ell=0..5 fit
→ post-fit source/target commonization
→ retained ell=2..5 carrier
```

Partial-sky masks induce mode coupling [@MASTER_2002], and realistic filtering can require a matrix-valued transfer rather than one scalar function [@LEUNG_2022].

The low-source coordinate contains the physical monopole and raw real harmonics through \(\ell=6\); the retained output contains 32 coordinates. The first-order Jacobian has shape

\[
J\in\mathbb R^{3\times32\times49}.
\]

A physical constant monopole generates a pure dipole at first order. Because the simultaneous fit includes \(\ell=0,1\) and the retained carrier begins at \(\ell=2\), the physical \(T_0\) column is an exact structural null. Finite transform leakage is a separate replay diagnostic (`RA-PROC-002`).

For a fixed boost direction \(\hat b\), let

\[
J_{\hat b}\in\mathbb R^{32\times48}
\]

be the low-source anisotropy response and

\[
K_{\hat b}^{\rm hi}(L)
=[K_{\hat b}^{(7)}|\cdots|K_{\hat b}^{(L)}]
\]

be the unrestricted deterministic high-source response. Its column dimension is

\[
d_H(L)=(L-6)(L+8).
\]

With

\[
\mathcal H_{\hat b}(L)=\operatorname{Im}K_{\hat b}^{\rm hi}(L),
\]

the survivor is

\[
J_{\rm surv}(L)=P_{\mathcal H_{\hat b}(L)^\perp}J_{\hat b}.
\]

Finite-dimensional linear algebra gives

\[
\boxed{
\operatorname{rank}J_{\rm surv}(L)
=\operatorname{rank}[K_{\hat b}^{\rm hi}(L)\;J_{\hat b}]
-\operatorname{rank}K_{\hat b}^{\rm hi}(L)
}.
\]

The nuisance images are nested in \(L\). Once robust containment is established, a larger cutoff cannot restore a model-free survivor. Column count alone is not a rank proof (`RA-PROC-003`).

The frozen Task-7B atlas found no registered cut-sky case satisfying all conditioning, \(\ell=6\) alias, and extended-tail gates (`RA-PROC-004`). The last byte-exact matched-control Task-7C result remains rank unresolved: 17 registered coordinates were ambiguous, one had a resolved survivor, and none was a containment candidate (`RA-PROC-005`).

## 9. Continuum wide-mask response

For the registered axisymmetric wide mask,

\[
w(\mu)=\operatorname{clip}\!\left(\frac{\mu+3/4}{3/2},0,1\right),
\]

define

\[
N_{\alpha\beta}=\int wY_\alpha^*Y_\beta\,d\Omega,
\]

\[
R_{\alpha p}^{(\hat b)}
=\int wY_\alpha^*\mathcal B_{\hat b}Y_p\,d\Omega,
\]

and

\[
K_{\hat b}^{\rm cont}(L)=P_{2:5}N^{-1}R_{\hat b}^{7:L}.
\]

For the axial direction, exact rational block ranks at \(L=12\) are

\[
(4,4,4,3,2,1),
\]

which yield stored-real row rank 32 (`RA-CONT-001`). Independent high-precision and direct-quadrature calculations give

\[
\begin{array}{c|ccc}
L&Z&X/Y&\mathrm{diagonal}\\\hline
8&20&24&24\\
9&27&29&32\\
12&32&32&32
\end{array}
\]

and at \(L=12\),

\[
\sigma_{\min}^{Z}\simeq0.00690566498,
\]

\[
\sigma_{\min}^{X/Y}\simeq0.01049033491,
\]

\[
\sigma_{\min}^{\rm diagonal}\simeq0.00851032278.
\]

The five non-axial results are multi-engine numerical evidence, not portable interval proofs (`RA-CONT-002`). Continuum full row rank does not certify finite-HEALPix full row rank; weak modes may lie below transform, quadrature, iterative-fit, or roundoff errors. This firewall is `RA-CONT-003`.

## 10. Matrix-valued numerical uncertainty

Let each frozen nonempty error family contain matrices \(E_{fi}\), with

\[
\Delta_f=\sum_i b_{fi}E_{fi},
\qquad
\|b_f\|_2\le r_f.
\]

For

\[
\Delta=\sum_{f=1}^{N_{\rm fam}}\Delta_f,
\]

family-level Cauchy–Schwarz gives

\[
\Delta\Delta^T
\preceq
N_{\rm fam}\sum_fr_f^2\sum_iE_{fi}E_{fi}^T.
\]

Define

\[
\boxed{
\Gamma_E=
N_{\rm fam}\sum_fr_f^2\sum_iE_{fi}E_{fi}^T
+\lambda_{\rm reg}^2I
}.
\]

This is the conditional Loewner theorem `RA-ERR-001`. The family partition, basis, radii, calibration set, holdout set, processing settings, and coordinate identity must be fixed before rank inspection.

Within a frozen family partition, the envelope is invariant under

\[
E_{fi}\mapsto c_fE_{fi},
\qquad
r_f\mapsto r_f/c_f,
\]

and under orthogonal mixing inside a family. An exactly zero family must be omitted or rejected because it leaves the perturbation set unchanged while changing \(N_{\rm fam}\). These are `RA-ERR-002`.

If the actual error satisfies

\[
\Delta\Delta^T\preceq\Gamma_E,
\]

then

\[
\|\Gamma_E^{-1/2}\Delta\|_2\le1.
\]

For

\[
\widetilde K_{\rm obs}=\Gamma_E^{-1/2}K_{\rm obs},
\]

singular values above one give a robust nonzero-rank lower bound; all 32 above a preregistered margin certify full row rank for the declared class (`RA-ERR-003`). This theorem does not prove that the current finite-HEALPix family registry is complete, and radii must not be tuned after inspecting the signal.

A robust rank lower bound is not a robust singular-subspace orientation. A partial nuisance projector needs perturbation control and a positive singular-value gap, through Wedin/Davis–Kahan-type results [@CAI_ZHANG_2018] [@LI_1999] [@LYU_WANG_2020]. This boundary is `RA-ERR-004`.

## 11. Integrated interpretation

The report separates three questions.

1. **Representation.** Tensorization retains morphology that scalar powers do not. On the declared cyclic domain, the \(Q/O\) packet separates proper rotations, but only on its valid forward image and with typed singular strata.
2. **Conditional physics.** MES quantities are scalar norm bounds under explicit premises. They neither reconstruct a tensor nor identify a physical spacetime source.
3. **Identifiability.** A complete observable representation can remain nonidentifying after masking, transfer, fitting, unresolved source modes, and numerical error. The appropriate object is a response quotient or identified set, not a forced point estimate.

The continuum calculation shows that an unrestricted deterministic high-source band can span the retained carrier in the registered continuum model at the stated evidence grades. It does not assert that physical high multipoles have unbounded amplitude. A physical covariance or prior, polarization, frequency, more angular modes, or independent depth information may refine the quotient, but each requires its own response and statistical contract.

## 12. Evidence status and deferred observation lane

```text
stored-real/STF normalization        DERIVED_EXACT; source implemented
Q/O cyclic reconstruction            DERIVED_EXACT on valid forward-image domain
stable Q/O decoder repair             SOURCE_PRESENT; local source-equivalent evidence
conditional MES functions            DERIVED_CONDITIONAL; primary-source supported
exchangeable-row finite rank          DERIVED_CONDITIONAL
finite group-orbit randomization      DERIVED_CONDITIONAL
WU-010 local-observer response        IMPLEMENTATION_VERIFIED at frozen scope
WU-011 quotient identities            DERIVED_EXACT
Task-7B registered atlas              IMPLEMENTATION_VERIFIED negative result
finite Task-7C matched control        IMPLEMENTATION_VERIFIED; RANK_UNRESOLVED
continuum L=12 axial result           DERIVED_EXACT author artifact
continuum other directions            NUMERICALLY_CHECKED; local non-byte-exact
matrix error envelope                 DERIVED_EXACT; source implemented
finite-HEALPix robust containment     UNRESOLVED
neutral survivor extraction           SOURCE_PRESENT; exact-head runtime unsealed
```

The observational gate remains closed:

```text
CURRENT_CORRECTED_TENSORIZED_PLANCK_RANK = NONE
PLANCK_OR_FFP10_EXECUTION = DEFERRED_BY_OWNER
```

## 13. Conclusions

The corrected real harmonic carrier maps exactly to the CMB quadrupole and octupole tensors. On the declared nonzero cyclic chart, a signed Krylov packet preserves proper-rotation morphology absent from a small scalar compression. The theorem is confined to valid forward-image packets and typed singular strata. Conditional MES ceilings remain scalar, one-way, and premise-bound.

Finite-null calibration requires the symmetry appropriate to the actual reference construction. Joint exchangeability supports an observation-plus-reference row rank only when the complete adaptive analysis is row-equivariant. A finite randomization group supports an orbit test, not arbitrary additional reference rows. This distinction is essential for valid tensor-statistic adaptation.

The exact full-sky local-observer response is well conditioned at the quadrupole-to-octupole level. After processing, identifiability is governed by the quotient of the low-source response by a high-source nuisance image. The continuum wide-mask operator is full row rank at \(L=12\) at the stated exact/numerical grades, while the finite-HEALPix matched-control result remains unresolved. A matrix-valued uncertainty envelope gives a conditional path to robust rank but does not replace proof that the actual numerical error belongs to the declared class.

The central conclusion is limited but substantive: tensorization preserves observable morphology, whereas physical attribution remains controlled by the full processed response, nuisance class, numerical-error model, and finite-null design. Corrected observational analysis is a separate future step.

---

# Appendix A. Canonical 30-claim map

| Claim ID | Report location | Role |
|---|---|---|
| `RA-SCOPE-001` | Sec. 1 | scope and supersession |
| `RA-REP-001` | Sec. 2 | orthonormal real carrier |
| `RA-REP-002` | Sec. 2 | raw-coordinate metric adapter |
| `RA-REP-003` | Sec. 3 | \(Q/O\) norm identities |
| `RA-ORBIT-001` | Sec. 3 | generic quotient dimension |
| `RA-ORBIT-002` | Sec. 4 | cyclic-domain reconstruction |
| `RA-ORBIT-003` | Sec. 4 | mirror non-separation result |
| `RA-ORBIT-004` | Sec. 4 | typed singular strata |
| `RA-MES-001` | Sec. 5 | PSTF normalization |
| `RA-MES-002` | Sec. 5 | one-way conditional bounds |
| `RA-MES-003` | Sec. 5 | scalar-to-tensor no-go |
| `RA-STAT-001` | Sec. 6.1 | exchangeable-row finite rank |
| `RA-STAT-002` | Sec. 6.3 | adaptive-selection boundary |
| `RA-STAT-003` | Sec. 6.3 | null-fidelity boundary |
| `RA-STAT-004` | Sec. 6.2 | finite group-orbit randomization |
| `RA-RESP-001` | Sec. 7 | exact local boost |
| `RA-RESP-002` | Sec. 7 | STF response and conditioning |
| `RA-PROC-001` | Sec. 8 | processed operator order |
| `RA-PROC-002` | Sec. 8 | physical monopole null |
| `RA-PROC-003` | Sec. 8 | quotient rank and nesting |
| `RA-PROC-004` | Sec. 8 | registered no-candidate atlas |
| `RA-PROC-005` | Sec. 8 | finite rank-unresolved boundary |
| `RA-CONT-001` | Sec. 9 | exact axial continuum rank |
| `RA-CONT-002` | Sec. 9 | five-direction numerical rank |
| `RA-CONT-003` | Sec. 9 | continuum/discrete firewall |
| `RA-ERR-001` | Sec. 10 | Loewner family-ball envelope |
| `RA-ERR-002` | Sec. 10 | registry invariances |
| `RA-ERR-003` | Sec. 10 | robust rank lower bound |
| `RA-ERR-004` | Sec. 10 | partial-subspace gap boundary |
| `RA-BOUNDARY-001` | Sec. 1 and 12 | no observation-bearing result |

# Appendix B. Claim and rank vocabulary

We distinguish

\[
\operatorname{rank}_{\rm alg}(M),
\qquad
\operatorname{rank}_{\rm num}(M;\tau),
\qquad
\operatorname{rank}_{\rm rob}(M;\Gamma_E),
\]

\[
\operatorname{rank}_{\rm quot}(J\mid K)
=\operatorname{rank}[K\;J]-\operatorname{rank}K,
\]

and finite-pool order ranks. The word *rank* is not used without qualification when more than one meaning is in scope.

# Appendix C. Authority and execution provenance

The scientific report uses source/content identities from Git-diverged lineages. Detailed branch heads, test counts, execution grades, prestart CI receipts, and supersession history are maintained in:

```text
docs/research_reports/appendices/HTT_REPORT_A_AUTHORITY_AND_EXECUTION_PROVENANCE.md
```

Source-only and local source-equivalent evidence are never labelled byte-exact implementation verification. The last accepted finite-operator scientific terminal remains the frozen rank-unresolved result.

# Appendix D. Bibliography authority

The sole rendered bibliography authority is:

```text
docs/research_reports/HTT_REPORT_A_REFERENCES.bib
```

Citation roles and direct-versus-adjacent provenance are maintained in:

```text
docs/codex_handoff/htt_tensorized_report_first_20260903/
REPORT_A_CITATION_PROVENANCE_MATRIX_V2.yaml
```

No manual reference list is a competing authority. Adjacent invariant-theory sources are not used as proofs of the repository-specific \(Q/O\) Krylov theorem, and novelty remains unresolved.

# Appendix E. Open gates before report freeze

1. supported-runtime validation of the 30-claim ledger, citation matrix, and flattened manuscript contracts;
2. fresh exact-head referee review of this flattened source and formal bibliography;
3. typeset PDF build, visual inspection, and source/PDF/evidence hash freeze;
4. explicit owner publication and merge decision.

Exact-head execution of the active repair branches and a portable all-direction interval certificate remain desirable evidence upgrades. The complete finite-HEALPix error-family proof remains a post-report theory/computation programme. None is silently converted into an observational claim or a false completed theorem.