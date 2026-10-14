# P04-A source recovery (flux_vector_codazzi_v1_20261014)

Repository HEAD read: `dee0acc4e21e64d0bb4247970e325ec738254128` (read-only; no git state change).
Card: `HTT_ALL_OBLIGATIONS_20261011_PACKAGE.zip` (sha256 `2d0b6da9…bc4af6f`), member
`HTT_ALL_OBLIGATIONS_20261011/tasks/P04-A.json` (extracted sha256
`5444498ebb7b68aed6eee431a730d079f05cdd52ba7aa44c19b43c1206d1430c`), source snapshot
`a30d84c7918b54238a48fa62e2ef482f7e6d36fa`.

All paths below are relative to `docs/research_program/theory_inference_port_20260930/`
unless they start with `htt/`.

## 1. Contract statement (verbatim)

`CAS_CONTRACT.json:4-5` (sha256 `904d95fe49402e9589f48bf4dcfdf69e4680a069693545580e4892e83c389fad`):
`"signature": "-+++"`, `"u_convention": "u=U/c dimensionless; u.u=-1"`.

`CAS_CONTRACT.json:50-61`, obligation CAS-04 "Fluid and Codazzi arithmetic":
* identity: `J=w gamma^2 beta; beta=2r/(1+sqrt(1+4r^2)); D_bK^b_a-D_aK=kappa J_a`
* assumptions: `single fluid w>0; K=-hh nabla n; inverse length; no multi-fluid converse`

`PORT_MAP.json:155-168` (sha256 `d0050aa3…ce5e0`), TBO-05: APIs
`homogeneous_codazzi_flux`, `perfect_fluid_normal_projection`, `flux_to_beta`, `tilt_interval`;
limit "Single-fluid enthalpy-positive inversion only; counterflows preserved".

## 2. Theory source with the exact conventions

`inherited/tilt_boost_loop_20260930/geometry_findings.md` (sha256
`070ddc3416529e6f9372b79cd5f5b8fe2e821b5449f3e8cdc3fb5d1f3930e320`):

* line 7: signature `(-,+,+,+)`, `n=N/c`, `u=U/c`.
* lines 9-10: `u = gamma (n + beta), n.beta=0, gamma = -u.n = (1-beta^2)^(-1/2)`.
* line 39: `T_ab = (epsilon+p) u_a u_b + p g_ab`.
* line 51: `h_ab=g_ab+n_a n_b`.
* line 53: `K_ab = -h_a^c h_b^d nabla_c n_d` (explicit ADM sign).
* line 57: `J_a = -h_a^b T_bc n^c`.
* line 61: `D_b K^b_a - D_a K = kappa J_a`, `kappa = 8 pi G_N/c^4` (line 59).
* line 63: "The sign can be checked in Gaussian coordinates x^0=ct: K_ij=-(1/2)partial_0 h_ij and
  G_0i=-D_j K^j_i + D_i K, whereas J_i=-T_i0. Lambda makes no contribution to this mixed projection."
* lines 67-69: `E_N = T_ab n^a n^b = (epsilon+p) gamma^2 - p`, `J_a = (epsilon+p) gamma^2 beta_a`,
  `beta_a = J_a/(E_N+p)`.
* line 71: "For epsilon+p != 0, J=0 iff beta=0. This implication fails ... for unseparated
  mixtures: the total J may vanish while individual component fluxes cancel."
* lines 73-79: homogeneous orthonormal frame reduction
  `D_b K^b_a = Gamma^b_bd K^d_a - Gamma^d_ba K^b_d`, `D_a K = 0`, `nabla_{e_i} e_j = Gamma^k_ij e_k`.
* lines 87-90: `w=epsilon+p>0`, `j=sqrt(J_a J^a)`, `r = j/w = beta/(1-beta^2)`,
  `beta = f(r) = 2r/[1+sqrt(1+4r^2)]`; line 92: `f(0)=0`.

`inherited/tilt_boost_loop_20260930/CLAIMS.json:113-139` (sha256 `9750221f…7c7b6`), TBO-05
assumptions: Einstein equation `kappa=8 pi G/c^4`; `K=-h h nabla n, n=N/c`; single perfect fluid
plus optional Lambda; `w=eps+p>0` for the quantitative branch. Limits: counterflow mixtures can have
`J_total=0` with tilted components.

`inherited/tilt_boost_loop_20260930/INDEPENDENT_REVIEW.md:51-57` (sha256 `f145a8fb…ddbc7`): with
`K_ab=-h_a^c h_b^d nabla_c n_d`, Gaussian coordinates give `K_ij=-1/2 partial_0 h_ij`,
`G_0i=-D_j K^j_i+D_i K`, `J_i=-T_i0`, hence `D_b K^b_a-D_a K=kappa J_a` with the stated sign.

`inherited/tilt_boost_loop_20260930/evidence/flux_tilt.wl:1-17`: Minkowski check with
`j=-t[[2;;4,1]]` (i.e. `J_i=-T_i0`), energy, flux, velocity and rank-one stress residuals
`stress - p I - J J/(E+p)`.

## 3. Implementation (must agree with the Lean definitions)

`htt/src/common/relativistic_kinematics.py` (sha256
`9ae767f9cec93358e4ca9b1a63abacf909fb1b770699c7e31be9b82ee2959d5e`):
* line 3: tetrad signature `(-+++)`, `c=1` for normalized four-velocities.
* lines 177-191 `perfect_fluid_normal_projection`: `wgamma2=(epsilon+pressure)*u[0]**2`,
  `E = wgamma2 - p`, `J = wgamma2*beta`, `S = p I + wgamma2 beta beta^T`.
* lines 194-206 `flux_to_beta`: inverts `|J| = w beta/(1-beta^2)` on `w>0` via
  `js/(ws/2+hypot(ws/2,js))`, algebraically equal to `2r/(1+sqrt(1+4r^2))`, `r=j/w`.
* lines 280-289 `homogeneous_codazzi_flux`: `J_a=(D_b K^b_a-D_a trK)/kappa`,
  `K_ADM=-h h nabla n`, einsum `Gamma[b,b,d]K[d,a] - Gamma[d,b,a]K[b,d]` with
  `Gamma[k,i,j]=Gamma^k_ij` (lines 262-277, orthonormal homogeneous frame).
* `htt/src/common/test_relativistic_kinematics.py:52-53,81`: projection→inverse round trip and
  Bianchi I zero-flux test.

## 4. Reused reviewed Lean (imported unchanged)

| Module | Path (under `local_execution/`) | Role |
|---|---|---|
| `PortCas01` | `PORT-CAS-01/lorentz_mass_shell_v1_20261008/lean/PortCas01.lean` | `eta`, `e0`, `fourVelocity`, `gamma`, `future_mass_shell` |
| `VelocityJetRest` | `PORT-CAS-03/velocity_jet_rest_bridge_v1_20261011/VelocityJetRest.lean` | dependency of P03-A |
| `VelocityJetDecomposition` | `PORT-CAS-03/velocity_jet_decomposition_v1_20261014/lean/VelocityJetDecomposition.lean` | `Pt`, `pd`, `lowerField`, `velJet` (`∇_a u_b`, derivative index first, `Γ x c a b = Γ^c_{ab}`), `projUp`, `projDown`, `hDown`, `spatialJet` (`h_a^c D_cd h_b^d`), `projUp_idem`, `gMink`, `eta_symm`, `eta_mul_eta` |
| `FluxScalarInverse` | `PORT-CAS-04/flux_scalar_inverse_v1_20261011/FluxScalarInverse.lean` | `betaOfRatio r = 2r/(1+sqrt(1+4r^2))`, `betaOfRatio_flux` |

Hashes of the sources and the produced `.olean` files are recorded in `AUTHOR_RETURN.json`.

## 5. Definitions that the source does not fix, and how they are fixed here

* **Riemann/Ricci convention.** The source fixes only the end result `G_0i=-D_j K^j_i + D_i K`
  (geometry_findings.md:63). We use
  `R^a_{bcd} = ∂_c Γ^a_{db} - ∂_d Γ^a_{cb} + Γ^a_{ce} Γ^e_{db} - Γ^a_{de} Γ^e_{cb}`,
  `R_bd = R^a_{bad}`, `G_ab = R_ab - R g_ab/2` (MTW sign class). The source equation
  `G_0i=-D_j K^j_i + D_i K` is then *derived* (target E3), which pins agreement; it is not assumed.
* **Christoffel symbols** are the Levi-Civita symbols of the chart metric,
  `Γ^a_{bc} = ½ g^{ad}(∂_b g_dc + ∂_c g_db - ∂_d g_bc)`, computed from actual Fréchet partials.
* **Spatial derivative D** is the projected covariant derivative
  `D_c T^d_e = h^d_p h^q_e h^r_c ∇_r T^p_q`, `D_a K = h^r_a ∂_r K` (standard induced connection on a
  spatial tensor); `K^b_a = g^{bc} K_ca`, `K = K^a_a`.
* **Normal.** `n` is the future unit normal of the `x^0 = const` slicing:
  `n_a = -δ_a^0/sqrt(-g^{00})`, `n^a = g^{ab} n_b`.
* **Chart scope.** The chart-level derivation is carried out in a Gaussian normal chart
  (`g_00=-1`, `g_0i=g_i0=0` on an open set), exactly the chart named by the source
  (geometry_findings.md:63, INDEPENDENT_REVIEW.md:53). Coordinate invariance / existence of such a
  chart is not formalized.

## 6. Searched and not reused

* `GR-04` ("energy-frame rate budget · Euler constraint", `gr_statistics_loops_20260930/
  local_sequential_verification_20261001/PR_LIST_KO.md:36`, `PR_PLAN.json:324`) — the card's
  "GR04 conservation finite theorem" reuse hint. No Lean module of GR-04 relevant to the
  normal projection or Codazzi identity was found; nothing imported from it.
* The orthonormal-frame structure-constant form (implementation lines 262-289) is a *frame*
  connection; only its chart analogue (target E5) is proved here.
