# P03-A source recovery

Repository HEAD at read time: `4571756afa75b17ecc199bfca80fd4da0fb2a684` (read-only; no git state changed).
All paths relative to `/home/cosmosapjw/Dropbox/bianchi/htt_base`.

| Item | Source (file:line) | sha256 | Recovered meaning |
|---|---|---|---|
| Card | `HTT_ALL_OBLIGATIONS_20261011_PACKAGE.zip` → `tasks/P03-A.json` | zip `2d0b6da9…bc4af6f`, card `7c943fce…cf400679` | scope, lean_steps, acceptance, pitfalls |
| Signature, `u` convention | `docs/research_program/theory_inference_port_20260930/CAS_CONTRACT.json:4-5` | `904d95fe49402e9589f48bf4dcfdf69e4680a069693545580e4892e83c389fad` | `-+++`; `u=U/c` dimensionless; `u.u=-1` |
| CAS-03 identity/assumptions | `CAS_CONTRACT.json:38-49` | (same) | `theta=c tr(h D); sigma=c sym(hDh)-theta*h/3; omega=c antisym(hDh); A=c^2 u.D`; `D_ab=nabla_a u_b; D*u=0; u.u=-1` |
| Port limit | `docs/research_program/theory_inference_port_20260930/PORT_MAP.json:206-217` (TBO-09) | `d0050aa349b56946d39bf2751e4f4687029c98e17203ed1740ab797ad44ce5e0` | "Full velocity derivative is supplied; finite beta alone cannot give theta,sigma,omega,A" |
| Implementation | `htt/src/common/relativistic_kinematics.py:336-358` | `9ae767f9cec93358e4ca9b1a63abacf909fb1b770699c7e31be9b82ee2959d5e` | `:337` "Supplied D_ab=nabla_a u_b in inverse-length units, u=U/c"; `:340` `omega_ab=c h_a^c h_b^d D_[cd]`; `:348` rejects `‖D u‖>tol`; `:350` `ucov=METRIC@u`; `:351` `projector=I+outer(ucov,u)` (= `projDown`); `:352` `h=METRIC+outer(ucov,ucov)` (= `hDown`); `:353` `spatial=projector@d@projector.T` (= `spatialJet`); `:354` `theta=c*trace(METRIC@spatial)` (= `expansion`); `:355` `shear=c*(S+S.T)/2-theta*h/3`; `:356` `omega=c*(S-S.T)/2`; `:357` `acceleration=c*c*(u@d)` (contraction on the first, derivative index) |
| Implementation test | `htt/src/common/test_relativistic_kinematics.py:91-108` | `919b99cba44c57f267320e87136cf11ab960efd2c8848a10a32c23e02c8aea27` | rest-frame example and `d[0,0]=1` rejection (D·u≠0) |
| Common conventions | `docs/research_program/gr_statistics_loops_20260930/cas/COMMON_SPEC.md:4-12` | `4714827e52acf3cb149f4014ac50ab2aa995dd4a0526f6b26ac7257807fe1897` | `:4` `-+++`, `g(u,u)=-1`, `U=c u`, `c>0`; `:6` `Q_ab=∇_a U_b` derivative-first, indices raised with `g` inverse; `:7` `Q u=0` means `Q_ab u^b=0`, `A_b=c u^a Q_ab`; `:8` `h_ab=g_ab+u_a u_b`, `h^a_b=δ^a_b+u^a u_b`; `:11` derivative-first `W` is minus `c` times the book's velocity-first vorticity; `:12` "If differentiating unit u instead of physical U, carry the extra c: `A_cov=2c^2 sym(∇u)u`" |
| Theory | `docs/research_program/gr_statistics_loops_20260930/gr/OPTICAL_THEOREMS.md:31-33,119-123` | `5ae2b6a65a5704247bed3d7dc5f01924318063ee5443cfa95c30c452b0ea8c21` | `Q_ab=∇_a U_b`, `A_b=U^a∇_a U_b`, `h_ab=g_ab+u_a u_b`; units `Q,θ,σ,W` in s⁻¹. NOTE letter clash: there `D_ab=h h B` is the symmetric spatial part, not the contract's `D=∇u` |
| Theory | `docs/research_program/gr_statistics_loops_20260930/supplements/DOSSIER_POSITIVE_BRIDGE.md:7-8` | `00c1fcb0b786bb874f13e52442af4b7b8a125287d84decb799ea68fd03915ebd` | `∇_aU_b=D_ab+W_ab-u_aA_b/c` (here `D=(θ/3)h+σ`); proved multiplied by `c` as `reconstruction` |
| Reused Lean (P03 bridge) | `local_execution/PORT-CAS-03/velocity_jet_rest_bridge_v1_20261011/VelocityJetRest.lean` | `0d696565adc1bac4490426e0d557c1429d3a63a873cf443ebe2b4d0ffac4b684` | `physicalAcceleration`, `rest_acceleration` (imported unchanged; olean `8066e19b…c82356`) |
| Reused Lean (PORT-CAS-01) | `local_execution/PORT-CAS-01/lorentz_mass_shell_v1_20261008/lean/PortCas01.lean` | `e289039fbe8a531ccb017923d751b14c12f5c5f5f66ffdaa5dbb5d2ac91a0c7b` | `eta`, `fourVelocity`, `future_mass_shell`, `zero_fourVelocity`, `e0` (imported unchanged; olean `a83adac8…ef56bd5`) |
| Prior blocker | `local_execution/PORT-CAS-03/cas04_source_reuse_audit_v1_20261011/SOURCE_REUSE_AUDIT.json` | — | requested a source-bound covariant index/metric interface; this unit supplies it (index variance of `D` and `A`, lowering map `g *ᵥ u`, `hDh` realization) |

## Resolved conventions

1. `D_ab = ∇_a u_b`, derivative index first (CAS_CONTRACT.json:42; relativistic_kinematics.py:337; COMMON_SPEC.md:6).
2. `D*u=0` is `D_ab u^b = 0` (COMMON_SPEC.md:7; relativistic_kinematics.py:348 `d@u`). The P03 bridge's
   unsigned row condition `∑_j D i j u j = 0` is exactly this contraction when `u` holds contravariant
   components and `D` covariant ones — the interface blocker of the CAS04 reuse audit is resolved by
   this typing, and `acceleration_eq_rest` identifies `A` with the bridge's `physicalAcceleration`.
3. `A_b = c^2 u^a D_ab` (covariant). Equivalent to COMMON_SPEC.md:7 `A_b = c u^a Q_ab` with `Q = c D`
   (theorem `kinematics_in_Q`) and to COMMON_SPEC.md:12 (theorem `acceleration_eq_two_sym`).
4. `ω_ab = c h_a^c h_b^d D_[cd]` is derivative-first (relativistic_kinematics.py:340). Relative to the
   velocity-first convention `ω_ab = h h ∇_[b u_a]` it has the opposite sign (COMMON_SPEC.md:11). No
   conversion is asserted in Lean.
5. `θ`: implementation uses `c g^{ab}(hDh)_ab`; the card's `c tr(hD) = c h^{ab}D_ab` is proved equal
   (`expansion_eq_trace_hD`), and equal to `c g^{ab}D_ab` under `D·u=0` (`expansion_eq_div_of_rest`).

## Items not recovered / not needed

* No source fixes a particular connection beyond metric compatibility; T1 therefore takes an arbitrary
  metric-compatible connection (torsion allowed), which contains Levi-Civita as a special case.
* No source fixes a manifold API; T1 is chart-level (`Pt = Fin 4 → ℝ`).
