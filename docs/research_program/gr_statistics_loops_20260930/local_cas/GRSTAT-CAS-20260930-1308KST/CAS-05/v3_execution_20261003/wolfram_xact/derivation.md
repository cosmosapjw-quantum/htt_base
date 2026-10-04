# CAS-05 v3: Wolfram Engine + xAct finite component derivation

## Physics/math audit verdict

The executed Wolfram/xCoba source checks the finite C01–C03 component under the
neutral input and contract. Its typed envelope records `PASS` for these three
components only. This is computational evidence for the specified mathematical
component, with scientific admission held for the parent adjudication and the
separate analytical obligations.

## Assumptions and conventions

Coordinates are `(t,x,y,z)` with `t=x0=c times physical time`; all four have
length units. Signature is `(-,+,+,+)` and the curvature convention is the one
in `NEUTRAL_INPUT.json`. The parameters obey `b>0`, `Lambda<3b`, `kappa>0`,
`c>0`; `lambda` is any finite real. The stress is Einstein-defined:
`T_ab=(G_ab+Lambda*g_ab)/kappa`. No equation of state is assumed. `S=sym M`
and `W=skew M` are coefficient matrices, not kinematic tensors. The branch at
the origin is future `u0>0` with `g(u,u)=-1`.

## Equation and definition audit

| Item | Status | Equation and check |
|---|---|---|
| C01 curvature | Executed exact | xCoba computes Christoffel, Ricci and Einstein from `g=exp(2phi) eta`. The source separately verifies `G=Ricci-g R/2`, then compares the computed Einstein tensor to the displayed conformal expression. |
| C01 energy frame | Executed exact | At the origin `G=diag(6b,0,0,0)`, `T=diag((6b-Lambda)/kappa,Lambda/kappa,Lambda/kappa,Lambda/kappa)`. The gap is `6b/kappa`. |
| C02 ray | Executed exact | The frame contractions give `kappa(epsilon+p2)=exp(b s^2)(6b-2lambda s)`. The `lambda=0` case and the finite root for `lambda!=0` are checked separately. |
| C03 cubic jet | Executed exact | Every component of `H` and each first and second coordinate derivative vanish at the origin. All 40 first Einstein coefficients, all twelve coefficient-basis images, the four contracted Bianchi coefficients, and the right inverse are computed. |

The coordinate connection derived from the conformal metric is
`Gamma^a_bc=delta^a_b phi_c+delta^a_c phi_b-eta_bc eta^ad phi_d`.
Consequently the Ricci tensor calculated from that connection is
`R_ab=-2phi_ab+2phi_a phi_b-eta_ab Box_phi-2eta_ab(phi_c phi^c)`,
and its contraction gives
`G_ab=-2phi_ab+2phi_a phi_b+2eta_ab Box_phi+eta_ab(phi_c phi^c)`.
The executable source obtains `G` from xCoba's metric curvature first and uses
this formula only as a residual comparison. At the origin, `phi_a=0`,
`phi_00=-2b`, `phi_ii=-b`; the cubic `lambda*t^2*x/2` contributes no second
derivative there. `epsilon=(6b-Lambda)/kappa`, `p_i=Lambda/kappa`, and
`epsilon+p_i=6b/kappa`. With the stated domain, `epsilon>|p_i|` at the point.

For the finite eigenvector derivative, first differentiate the normalization
`g_ab u^a u^b=-1` at `u(0)=(1,0,0,0)`. It gives
`partial_mu g_00-2 partial_mu u^0=0`. The xCoba metric has
`partial_mu g_00(0)=0` for all four `mu`, hence each temporal derivative
`partial_mu u^0(0)=0`. The source records those four normalization residuals.

Next use the full mixed stress `T^a_b=g^{ac}T_cb`, calculated from the xCoba
Einstein tensor, and differentiate `T^a_b u^b=-epsilon u^a`. Its sixteen
point equations are
`partial_mu T^a_0+(T^a_b+epsilon delta^a_b) partial_mu u^b
+delta^a_0 partial_mu epsilon=0` for every `mu,a=0,1,2,3`.
The normalized `E0=exp(-phi)partial_0` contraction gives the first energy
derivative at this point: `partial_mu epsilon=0` for all `mu`. This agrees with
`-partial_mu T^0_0` in all four temporal equations. The spatial column has
`partial_t T^1_0=-2lambda/kappa` and all other entries zero. Solving its
nonzero-gap equations gives `partial_t u^1=lambda/(3b)` and every other
`partial_mu u^i=0`. Substitution back into the complete sixteen-component
mixed equation yields sixteen exact zero residuals. Since the connection
vanishes at the origin, `nabla_t u^1=lambda/(3b)` and
`A^a=(0,c^2 lambda/(3b),0,0)`. This is a finite differentiated equation at
the point; it does not assert a smooth eigenfield in a neighborhood.

The same xCoba tensor yields `partial_x epsilon=0` and
`partial_x p2=-2lambda/kappa` at the origin. For `lambda!=0`, these finite
derivatives exclude a differentiable scalar barotropic relation `p2=p2(epsilon)`
along this direction at the point; no stronger matter-model conclusion follows.

On `t=y=z=0, x=s`, `E_a=exp(-phi) partial_a` is the stated orthonormal frame.
The cosmological terms cancel in `T(E0,E0)+T(E2,E2)`, so the xCoba components
give `exp(-2phi)(G_00+G_22)=exp(b s^2)(6b-2lambda s)`. For `lambda=0` this
is positive for all real finite `s`. For `lambda!=0` it vanishes at
`s=3b/lambda`; at that point this pressure gap is lost and no unique
eigenframe is inferred.

For C03, differentiating the metric connection at a point where `H`, `dH`
and `d²H` vanish reduces the first curvature variation to the flat linear
expression

`delta R_ab = (partial_c partial_a H^c_b + partial_c partial_b H^c_a - Box H_ab - partial_a partial_b tr_eta H)/2`,

`delta G_ab=delta R_ab-eta_ab tr_eta(delta R)/2`.

Background curvature times `H` or its lower derivatives vanishes in this
first jet. The baseline conformal metric has zero first Einstein derivative
at the origin, verified from the xCoba tensor. xCoba also computes each
coefficient basis directly from the polynomial metric `eta+H`; its exact
coordinate Taylor degree-three simplifier retains every term that can enter
`dG(0)` and removes only higher coordinate degrees. The twelve direct xCoba
jets equal the independent linear expression in all 40 entries, with zero
residuals recorded individually in `result.json`.

Writing `tr M=M11+M22+M33`, the complete 40-coefficient jet has the compact
universal form

`partial_0 G_00=tr M`, `partial_0 G_0i=q_i`,
`partial_0 G_ij=(S_ij-delta_ij tr M)/2`,
`partial_k G_00=0`, `partial_k G_0i=M_ik`, and
`partial_k G_ij=(delta_ik q_j+delta_jk q_i)/2-delta_ij q_k`.

These cover all ten symmetric Einstein components for each of four coordinate
derivatives. The machine-readable four `4x4` matrices and twelve `4x4x4`
basis images are in the computed evidence of `result.json`. Contracting gives
`partial^a G_a0=-tr M+sum_i M_ii=0` and, for each spatial `i`,
`partial^a G_ai=-q_i+sum_j partial_j G_ji=0`. Since `dg(0)=0`, these are also
the four required `kappa partial^a T_ab=0` coefficients.

The explicit universal real right inverse for arbitrary `q_i,M_ij` and
`b>0` is `k_0i=-q_i/(6b)` and `k_ji=-M_ij/(6b)` for every `i,j=1,2,3`.
Substitution recovers `q_i=-6b k_0i`, `M_ij=-6b k_ji`, the target
`delta G_0i=q_i*t+sum_j M_ij*xj`, and the induced finite eigenvector jet
`nabla_mu u_i=k_mu_i`. No tracefree restriction is placed on `S`.

## Dimensional/sign/limit checks

`b,Lambda` have length `^-2`; `lambda,q,M,S,W` length `^-3`; `k` length
`^-1`. The gap has energy-density units, and `A=c²lambda/(3b)` has
acceleration units in the length-valued `x0` convention. The `lambda=0`
baseline, the `s=3b/lambda` gap-loss point when defined, all twelve basis
vectors, and the zero density-gradient/nonzero pressure-gradient local jet
are represented in the exact computed outputs. The xCoba `SetCMetric::old`
warning in the preserved exploratory first run led to explicit
`UnsetCMetric[gconf]` before basis metrics; the final run has no warnings.

## Claim-tier implications

The scope is the specified finite/local algebraic component. This axis does
not establish a Lorentzian or strict-DEC neighborhood, a smooth isolated
eigenframe by the implicit-function theorem, a uniform radius, an equation
of state, CAS-06, or full scientific admission. The parent retains independent
four-axis adjudication and all claim decisions.

## Fatal blockers

None were observed for this axis's finite C01–C03 checks in the executed run.

## Safe claims

All three frozen finite component checks have an executed exact Wolfram/xAct
axis result. The `check-axis` tool accepts the stored envelope structurally;
its message explicitly says `STORED_ENVELOPE_ONLY`, so current-run four-axis
eligibility awaits the parent-run adjudicator.

## Required tests or artifacts

`axis.wl` is the independent mathematical source; `run.py` launches a fresh
`wolframscript -file axis.wl` process on every invocation. Each invocation
retains raw stdout/stderr and a typed result under `runs/`, and writes the
latest `result.json`. The wrapper verifies the three frozen input SHA-256
identities before execution. Its stdout is exactly one JSON document with
the three boolean checks, domain-assumption difference list, counterexample,
and computed evidence. The executed command, exit, version, source hashes,
cwd, timestamp and log paths are in the envelope.
