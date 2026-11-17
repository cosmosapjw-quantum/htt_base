# R62 tensor-series class witnesses: R5/C5 construction

Scientific baseline supplied by the parent: `c118982e56ee50d68dd0446aa10f16ffe65bd02b`;
branch `research/r62-anisotropy-classification-20261117`. The authoritative scientific
contract is `R62_DESIGN.md`. This worker wrote only the three assigned scratch files;
all remote access was read-only. The parent owns integration and actual-data runs.
Observed worker model/runtime identity: UNKNOWN.

## Domain, normalization and confidence object

Let `k=1,...,4`, and let `h` contain k tensor-major orthonormal STF5 blocks. The
basis is E0=diag(1,-1,0)/sqrt(2), E1=diag(1,1,-2)/sqrt(6), followed by xy, xz, yz
symmetrized units divided by sqrt(2). Thus E_A:E_B=delta_AB and ||K||_F=||q||_2.
This matches the read R54 `STF5_BASIS` and R61 `stf_basis` definitions. The physical
units are those of the supplied tensor coefficients; all amplitudes have the same
units, covariance has their square, orientations and Mahalanobis distances are
dimensionless. There is no metric-signature or natural-unit operation in this
Euclidean spatial STF calculation.

For one fixed positive-definite full covariance V and supplied nonnegative cutoff
c, E={x:(x-h)^T V^-1(x-h)<=c}. The caller supplies c for this carrier and its
declared sampling law. This module does not choose a confidence level, change c
between classes, assign a Wilks law or construct a Bayesian model probability.
Subsetting or taking contrasts creates a new carrier; its cutoff is supplied
separately. The optional R61 range adapter requires strictly positive c.

## Exact finite-dimensional model maps

The five sets include all their zero and repeated-eigenvalue strata:

- ZERO: K_j=0.
- SHARED_FRAME: K_j=R(a_j0 E0+a_j1 E1)R^T, R in SO(3).
- SHARED_AXIS: K_j=b_j sqrt(3/2)(u u^T-I/3), u in S2, with u and -u equivalent.
- SHARED_ZERO_EIGENVALUE_SHAPE: K_j=b_j R E0 R^T.
- SHARED_GENERAL_SHAPE: K_j=b_j S, S:S=1, trace(S)=0.

Every amplitude is unrestricted in sign. For a common frame the orthonormal
amplitudes give lambda1=a0/sqrt(2)+a1/sqrt(6),
lambda2=-a0/sqrt(2)+a1/sqrt(6), lambda3=-2a1/sqrt(6).
SHARED_GENERAL_SHAPE is rank at most one for the k-by-5 coefficient matrix;
SHARED_FRAME generally has rank two. A single tensor is always in both sets.
Zero-amplitude orientation parameters are reconstruction gauges, not measured
axes. Eigenframe permutations and sign choices are likewise gauges of the
appropriate model, with amplitudes transformed consistently.

## Linear GLS and variable projection — derived

For a fixed shape basis B (5-by-2 for a frame, 5-by-1 otherwise), the design is
D=I_k kron B. Write V=LL^T, A=L^-1 D, z=L^-1 h. The amplitude minimizer solves
min_a ||Aa-z||^2. Since V is positive definite and B has independent columns,
D and A have full column rank. Hence the mathematical minimizer is
a=(D^T V^-1 D)^-1 D^T V^-1 h. The code uses whitened QR least squares rather
than forming V^-1 or solving squared-condition normal equations.

For every evaluated orientation the witness is x=D a. Its reported objective is
recomputed from the original residual, ||L^-1(x-h)||^2. QR rank failure is reported
as an implementation/numerical failure, not changed to a rank-truncated physical
model. The residual normal equation A^T L^-1(x-h)=0 is exposed as a diagnostic.

Rotations use local SO(3) exponential coordinates R(v)=exp([v]_cross)R0.
S2 and S4 use the spherical exponential chart
s(v)=cos(||v||)s0+sinc(||v||/pi)T v, where T spans s0-perp. Normalization after
evaluation removes roundoff in the unit norm. These charts avoid bounded-angle
coordinate singularities at selected axes. Repeated eigenvalues do not require
eigenvector derivatives: eigenvectors are only finite initial proposals.

The default deterministic pool adds 64 seeded random proposals to identity,
data eigenframes, simple tensor combinations, individual normalized tensors and
SVD shapes. Zero-eigenvalue proposals enumerate the three possible assignments of
the zero eigenaxis. The best ten proposals undergo bounded local least squares,
with at most 180 function evaluations per start. The candidate list always
includes zero. Candidates from narrower classes seed the broader shared-shape
and shared-frame searches. This finite search is not an exhaustive global search.

Every returned nonlinear objective is a *feasible upper bound*. Local success
only describes the optimizer's stopping rule. A failed optimizer still leaves
the best finite proposal or the zero witness. A directly reconstructed objective
at most c establishes INTERSECTS. An outside nonlinear fit is UNRESOLVED.
ZERO is a singleton and can be EXCLUDED by its fixed objective; a small floating
boundary margin prevents promoting tiny positive rounding excess to exclusion.
Witness reconstruction, traces, eigenvalues, norms and pairwise commutators are
returned. The implementation does not attach a positive tolerance to the
intersection inequality: a candidate must satisfy the supplied cutoff itself.

## Simultaneous diagonalization and commutator enclosures — derived

For a finite family of real symmetric matrices, a shared orthonormal eigenbasis
implies pairwise commutativity. Conversely, diagonalize one matrix. If B commutes
with A, A(Bv)=B(Av)=lambda Bv for each vector v in A's lambda eigenspace, so B
preserves each eigenspace. Restrict all remaining commuting symmetric matrices
to these mutually orthogonal invariant subspaces and repeat. Each restriction is
symmetric and the restrictions still commute. Finite-dimensional induction
produces a common orthonormal basis, including repeated eigenvalues and zero
matrices. A sign reversal of one basis vector makes its determinant positive
without altering diagonal matrices. Thus an SO(3) frame exists exactly when all
pairwise commutators vanish.

For each pair i<j and component a<b, let
T_AB=(E_A E_B-E_B E_A)_{ab}. Construct the symmetric 5k-square M with blocks
M_ij=T/2, M_ji=T^T/2 and all other blocks zero. Direct multiplication gives
x^T M x=[K_i,K_j]_{ab}. A signed commutator component is quadratic; its squared
norm would be quartic. The code additionally considers the component projection
parallel to the center commutator, when nonzero.

The optional `range_solver` must implement the read R61 interface
`quadratic_ellipsoid_range(h,V,M,cutoff=c)`. Its lower/upper enclosures use the
same full ellipsoid. Any valid signed range excluding zero excludes SHARED_FRAME
and each of its four included classes. If every range contains zero, joint
commutator feasibility has not been proved and classification stays unresolved
unless a class witness is available. Solver errors are retained as unresolved
ranges. An exclusion contradicting a verified feasible class witness raises an
ArithmeticError. R61's trust-region primal/dual gaps are preserved in full;
these are numerical enclosures with floating residuals, not formal interval
certificates. No local-search objective is reused as an exclusion lower bound.

## Common calibration quotient — derived

Let D_j=K_j-K_0 for j>=1 and L be the block difference operator. Then
h_D=Lh and V_D=L V L^T, including all cross-window terms. L annihilates
1_k kron C for every common additive STF C. It also annihilates a covariance
component (1_k 1_k^T) kron W of arbitrary common calibration noise.

There exists C such that all T_j=K_j-C commute if and only if all D_j commute.
Necessity follows from D_j=T_j-T_0 and bilinearity of the commutator, because
every pair of T tensors commutes. For sufficiency choose C=K_0: T_0=0 and
T_j=D_j. The same argument with linear spans proves the common-one-dimensional-
shape equivalence: K_j-C=b_j S implies D_j=(b_j-b_0)S, and the converse uses
C=K_0. This also preserves the axisymmetric or zero-eigenvalue shape restriction
when imposed on S. This is an arbitrary-calibration quotient, not an empirical
bound on common calibration.

## Covariance and numerical checks

The active SO(3) action is Q_AB=E_A:R E_B R^T. Q is orthogonal. With
P=I_k kron Q, h'=Ph, V'=P V P^T and x'=Px, the Mahalanobis objective is
unchanged. Tensor permutations act by the corresponding block permutation of
both h and V. Therefore the exact model-set distance is invariant. A finite
proposal/local-search result is still an upper bound and need not be identically
rotation invariant in all cases; the tests check refit agreement on named cases.

The finite assertion tested is that these model maps, full-covariance GLS
objectives, constructive witnesses, quadratic forms and status rules satisfy
analytic hand cases and independently parameterized checks. Tests include:

- orthonormal basis and active rotation/covariance parity;
- nonproportional diagonal tensors: exactly shared frame, rank two;
- isotropic best-rank-one distance sum of squared nonleading singular values;
- one tensor's spectral closest-axis distance ||K||^2-3 max(lambda_i^2)/2;
- closest zero-eigenvalue-shape distance ||K||^2-(lambda_max-lambda_min)^2/2;
- negative amplitudes, zeros, repeated eigenvalues and axis/frame gauge changes;
- independent full-covariance normal-equation refit, and a deliberately changed
  diagonal covariance yielding a different answer;
- independently parameterized simultaneous axis/amplitude nonlinear refit;
- refitted rotation and tensor-permutation invariance, plus direct quadratic
  objective evaluation using `solve(V,residual)`;
- common-offset mean and common-noise covariance cancellation;
- commutator quadratic forms versus direct matrix products;
- conservative analytic necessary-condition enclosures and error propagation;
- optimizer/solver failure never falsely excluding nonlinear classes;
- optional exact R61 adapter integration in the repository runtime;
- invalid shape, finite-value, symmetry, SPD, resource-option and cutoff checks.

The local command is
`OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python -m pytest -q test_r62_tensor_classes.py`
from `/workspace/scratch/d9b8ed2ee1cd`. Initial result: **26 passed, 1 skipped** in
1.93 s, exit 0. The skip is the repository R61 import, unavailable in this scratch
interpreter; the parent must run the same test after integration in `.venv`.
Python 3.12.14, NumPy 2.3.5, SciPy 1.17.0, pytest 9.2.0 were directly observed.
The environment emitted one unrelated anyio/pytest deprecation warning.
No actual CF4-data experiment was run by this worker. Source/output identities
and the eventual actual-data manifest belong to the parent-controlled experiment.
Passing these finite tests is implementation evidence, not proof that a local
optimizer has found global nonlinear class distances.

## Skill context actually used

- PhysMath Research Loop **1.3.0**, cloud package
  `skill://plugins_6acdfbba921881919e0c17843706aef4/physmath-research-loop`:
  `SKILL.md`, `references/POLICY_INTEGRATION.md`, selected R5 in
  `references/THEORY_LOOP.md`, selected C5 in `references/CODING_LOOP.md`, and
  `references/SUBAGENT_MODE.md`. The initially supplied suffixed package name
  was unavailable; discovery found this actual 1.3.0 source.
- Mathbox `computation-audit/SKILL.md` and `references/checklist.md`, cloud package
  `skill://plugins_6a9174204a0481918ca3798d69d2e227/computation-audit`.
- Remote repository root `AGENTS.md`, `htt/htt/AGENTS.md`,
  `.agents/skills/htt-physics-math-audit/SKILL.md`, and
  `.agents/skills/htt-scientific-code-validation/SKILL.md` were read.

Scope application: actual constructive derivations and a runnable pure feature
path; one bounded small-construction verification pass; exact unresolved/global
distinctions; no recursive delegation or fresh review; no remote writes; no
actual-data execution; no additional loop or manufactured claim-admission gate.
