# PR-270 Pillar T orbit, response, and realizability record

Status: `CAS_BLOCKED`

Claim ceiling: `diagnostic_only`

Source proof-adjudication status: `NOT_ADJUDICATED`

PR-270 freezes one R3 `CAS_CONTRACT.json` for the exact algebraic cores of
VT-T5 through VT-T8 and the restricted invariant chain-rule core of VT-T13.
It separately verifies the conditional finite-dimensional statements VT-T11
and VT-T12 and preserves the VT-T14 external-geometry refusal. The current
runner-observed aggregate is not a proof verdict: Wolfram Engine+xAct is
blocked by an unactivated/license state, while SymPy, SageMath+Singular, and
Lean pass the byte-identical contract. Majority vote is forbidden, so the
only aggregate is `CAS_BLOCKED`.

No source theorem status is rewritten. No local chart is promoted to global
orbit completeness, no 1+3 evolution law is invented, and no geometry,
native-solver, morphology-atlas, or family-identification conclusion follows.

<a id="vt-t5"></a>
## VT-T5 — shear-shape discriminant

For real eigenvalues \(\lambda_1+\lambda_2+\lambda_3=0\), define

\[
I_2=\sum_i\lambda_i^2,\qquad I_3=\sum_i\lambda_i^3 .
\]

The contract checks exactly

\[
\Delta=\frac{I_2^3}{2}-3I_3^2
       =\prod_{i<j}(\lambda_i-\lambda_j)^2
       =\frac{I_2^3}{2}(1-J_\sigma^2),
\quad
J_\sigma^2=\frac{6I_3^2}{I_2^3}.
\]

The square form gives \(\Delta\ge 0\) on the real STF domain. Repeated
eigenvalues give \(\Delta=0\) and \(|J_\sigma|=1\). The zero-shear point is
outside the normalized-shape branch. These identities pass three executed
axes but retain `CAS_BLOCKED_REQUIRED_AXIS` until Wolfram+xAct executes.

<a id="vt-t6"></a>
## VT-T6 — trace-free Cayley–Hamilton reduction

For a real trace-free \(3\times3\) matrix,

\[
\sigma^3=\frac{\operatorname{tr}(\sigma^2)}{2}\sigma
         +\frac{\operatorname{tr}(\sigma^3)}{3}I .
\]

Multiplication by \(\sigma\) reduces the fourth power, and recursive
multiplication reduces every higher vector–shear contraction to powers
zero, one, and two. SymPy and Sage use a generic symmetric STF matrix; Lean
kernel-checks the same five-parameter matrix. The required fourth axis has
not executed, so this PR records no four-axis proof promotion.

<a id="vt-t7"></a>
## VT-T7 — Krylov cyclicity

In a shear eigenframe,

\[
\det[v,\sigma v,\sigma^2v]
=v_1v_2v_3\prod_{i<j}(\lambda_j-\lambda_i),
\]

and its square equals the corresponding Gram determinant. A reference vector
is cyclic exactly on the simple-spectrum, nonzero-component stratum. The
registered principal witness has determinant 16 and Gram determinant 256;
the repeated-spectrum and zero-component mutations vanish exactly.

<a id="vt-t8"></a>
## VT-T8 — restricted generic local chart

Order the fourteen variables as
\((\lambda_1,\lambda_2,v_0,v_1,v_2,v_3)\). The Jacobian of
\((I_2,I_3,m_{jp})\), with
\(m_{jp}=v_0^\mathsf{T}\sigma^p v_j\), is block lower triangular.
Its upper five-dimensional block splits into an invariant derivative block
and a self-moment block. The remaining three diagonal blocks are the same
Krylov moment matrix. Writing

\[
g=(\lambda_1-\lambda_2)
  (\lambda_1+2\lambda_2)(2\lambda_1+\lambda_2),
\]

the exact block determinants are

\[
\det D(I_2,I_3)=-6g,\quad
\det D_{v_0}(m_{00},m_{01},m_{02})=-8v_{01}v_{02}v_{03}g,
\]

\[
\det B=-v_{01}v_{02}v_{03}g.
\]

Therefore

\[
\det J=-48v_{01}^4v_{02}^4v_{03}^4
(\lambda_1-\lambda_2)^5
(\lambda_1+2\lambda_2)^5
(2\lambda_1+\lambda_2)^5.
\]

The registered rational witness evaluates to 50,331,648. This is a local
principal/cyclic chart result only. It does not establish global separation,
invariant-ring completeness, or a morphology atlas.

<a id="vt-t11"></a>
## VT-T11 — supported nuisance quotient

After covariance support has already been selected, a full-column-rank
nuisance tangent \(N\) defines

\[
P_N=N(N^\mathsf{T}N)^{-1}N^\mathsf{T},\qquad
R_\perp=(I-P_N)R.
\]

The executable witness rejects rank-deficient nuisance columns and checks
symmetry, idempotence, complementarity, and the quotient rank. Covariance-null
directions remain an upstream support decision and cannot be silently
relabelled as nuisance projection.

<a id="vt-t12"></a>
## VT-T12 — Schur/principal-angle identity

For orthonormal local and global bases \(L,G\) in the same supported whitened
space,

\[
S=G^\mathsf{T}(I-LL^\mathsf{T})G
\]

has eigenvalues \(\sin^2\theta_i\), with unit eigenvalues appended when the
global subspace has unmatched dimensions. \(S\) is positive definite exactly
when no global direction lies in the local tangent. A small positive angle is
reported as weak identification rather than rank deficiency.

<a id="vt-t13"></a>
## VT-T13 — invariant chain-rule core only

The exact differential

\[
d\!\left(\frac{6I_3^2}{I_2^3}\right)
=\frac{12I_2I_3\,dI_3-18I_3^2\,dI_2}{I_2^4}
\]

is checked after clearing denominators. The requested decomposition through
\(E_{ab}\), \(H_{ab}\), \(\pi_{ab}\), \(A_a\), and \(\omega_a\) remains
`INCONCLUSIVE_MISSING_TYPED_EVOLUTION_LAW`: the frozen inputs do not select
one sign, branch, frame, and domain convention for that equation.

<a id="vt-t14"></a>
## VT-T14 — native geometry gate

Without an admitted Weyl/three-curvature/anisotropic-stress payload and the
future externally validated native morphology atlas, the typed result is
`INCONCLUSIVE_NATIVE_GEOMETRY_GATE`. Only a partial kinematic diagnostic
report is permitted.

## Runner-observed four-axis state

| Axis | Preflight | Solver executed | Contract result |
|---|---|---:|---|
| Wolfram Engine+xAct | `BLOCKED_PLATFORM_OR_LICENSE` | no | blocked |
| SymPy 1.14.0 | pass | yes | pass |
| SageMath 10.9 + Singular 4.4.1 | pass | yes | pass |
| Lean 4.31.0 | pass | yes | pass |

The Wolfram transcript reports that the engine is not activated or has a
license-related problem and requests an explicit activation operation.
Activation requires external user/license authority and was not attempted.
No computation-class exception was preregistered. Thus the aggregate is
`CAS_BLOCKED`, the PR-270 success dependency is false, and PR-273 remains
closed even after PR-272 completes.

## Reproduction

```bash
python3 .agent-harness/scripts/cas_gate.py preflight --all
python3 .agent-harness/scripts/cas_gate.py run-adjudicate \
  --contract docs/research_program/vector_tensor/cas/CAS_CONTRACT.json \
  --run-spec docs/research_program/vector_tensor/cas/CAS_RUN_SPEC.json \
  --out /tmp/PR270_CAS_ADJUDICATION.json
PYTHONPATH=.:htt/src:htt python3 -B -m pytest -p no:cacheprovider -q \
  tests/contracts/test_pillar_t_cas.py
```

Both CAS commands currently exit 2 because the mandatory Wolfram axis is
blocked. That nonzero exit is the expected fail-closed result, not a hidden
test failure.
