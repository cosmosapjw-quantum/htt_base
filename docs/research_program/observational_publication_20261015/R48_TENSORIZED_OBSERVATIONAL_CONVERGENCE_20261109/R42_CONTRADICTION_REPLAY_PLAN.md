# R42 contradiction replay plan for R48

상태: **정적 대조 완료, runtime replay NOT_RUN**  
기준 branch/head: research/r48-tensorized-observational-convergence-20261109 / afb3ab9406cf13874e2e49e40d09f3b639b01c20  
목적: R42의 과거 "Stage B repaired" 주장을 current code와 독립적으로 재판정한다. 이 계획은 기존 코드를 무조건 고치는 작업 지시가 아니라, 각 결함의 정확한 재현/반증을 위한 bounded test plan이다.

## Findings and replay gates

| ID | 현재 source evidence | 판정 | 최소 재현/수리 acceptance |
|---|---|---|---|
| C01 response factors | full_observable_x_bundle.py 143–144: fixed 3.6625/3.3200; 163–164: fixed 0.92/0.18 | BLOCKER | survey selection에서 \(x,\alpha\) 또는 직접 operator response를 추정/hash-bound하거나 UNAVAILABLE 반환. Gaia E1/E2는 physical operator, units, calibration covariance 필요. |
| C02 chain/diagnostic fabrication | run_cobaya_joint_inference.py 155–159, 219–224; receipt has no sampler-executed flag or input/config/source hashes | BLOCKER | cache-only branch는 diagnostics를 만들지 않음. sampler 실제 실행 + chain manifest/config/source/data hashes가 일치해야 convergence report 생성. missing diagnostic은 NOT_RUN. |
| C03 Planck input insufficiency | R48 ledger: observed_lowell_EB.npz 743 bytes; no raw map/full a_lm and full source-matched covariance/transfer | BLOCKER | official map/alms, masks, beams, pixel/noise/foreground/transfer, source hashes, matched simulation covariance 필요. 요약 carrier만으로 map-level inference 불가. |
| C04 Bianchi transfer unavailable | bianchi_transfer_adapter.py 120–130: native reader/external wrapper not bound; NotImplementedError | EXPECTED BLOCKED INPUT | native/external solver provenance와 validated transfer/reader 확보 전 family-dependent likelihood 실행 금지. |
| C05 HTT output semantics | T=(x,Q,Pi,F,G_F)는 joint posterior push-forward | HIGH | 같은 sample IDs와 full cross-covariance 보존. 다섯 결과를 독립 likelihood factor로 곱하지 않음. |
| C06 exact frame closure | run_cobaya_joint_inference.py 268 및 test fixture 60은 beta vector sum; full_observable_x_bundle.py는 both-nonzero conditional | HIGH | ordered Lorentz matrix oracle; collinear/non-collinear/zero-boost limits, Wigner rotation, frame/tetrad consistency. |
| C07 cross-probe covariance | cobaya_joint_five_probe.py 189–196 단순 합 | HIGH | shared sky/LSS/calibration/selection covariance를 포함하거나 조건부 독립 factorization을 source별로 정당화. |
| C08 chart/frame semantics | 17D coordinates exist but event, epoch, tetrad and physical transport not carried uniformly | HIGH | PHYSICAL_STATE_FRAME_EPOCH_CONTRACT.md의 typed manifest를 모든 source operator에 연결. |
| C09 inherited claim promotion | 과거 theory/synthetic/diagnostic headlines exceed later admitted evidence | HIGH | claim ledger historical status 유지; analytic/synthetic PASS를 observation result로 승격하지 않음. |
| C10 Bianchi labels | local equivalence/orientation/presentation can make family labels non-identifiable | HIGH | geometry 비교는 rotation/local-equivalence quotient 및 calibrated posterior predictive separation 후에만 family claim. |
| C11 null-law mislabelling | htt_five_variable_state.py 364 default MATCHED_NULL_PLANCK_MC100; 487–496 absent input creates seeded Gaussian \(1.5\times10^{-4}\); line 518 reuses supplied law name | BLOCKER | matched-null samples 없으면 Pi null output 생성 금지, BLOCKED_MISSING_MATCHED_NULL 반환. Null provenance ID/hash required. |
| C12 G_F transport label mismatch | line 370 default PHYSICAL_EXPANSION_TRANSPORT; line 551 returns factor 1 except explicit LINEAR_OPTICAL_EXPANSION | BLOCKER_FOR_PHYSICAL_DEPTH_CLAIM | shear propagation/optical equations에서 background, stress, boundary를 포함해 유도하거나 TRANSPORT_UNAVAILABLE 반환. |
| C13 source-operator hook is inert | full_observable_x_bundle.py line 84 declares source_operators but no downstream use | HIGH | typed operator dispatch를 wire하고 source identity/unit 검사, 또는 misleading availability claim 제거. silent fallback 금지. |
| C14 17D chart versus sampled dimension | Cobaya config lines 133–138 fixes all omega_i,A_i=0; DeltaOmega_k also fixed. Only 11 kinematic coordinates sampled, not a free 17D posterior. | HIGH | receipt에 free/fixed inventory와 point-mass restriction 기록. Full 17D posterior라 부르지 않음. |
| C15 test oracle blind spots | R42 test 184 generates Gaussian null and line 191 labels it Planck MC100; line 269 supplies count factors explicitly; fixture line 60 adds velocities linearly | HIGH | default/fail-closed adversarial tests; synthetic fixture provenance typed; "authentic" label 삭제. |
| C16 source SHA checks disabled | runner line 47 sets verify_sha=False; two-layer benchmark also disables operator SHA verification | BLOCKER_FOR_OBSERVED_RUN | immutable source SHA verification required; result receipt must include hashes. |

## Bounded replay order

1. Verify exact branch/head and source blob hashes before local tests.
2. Run R46 synthetic target-compression tests and R42 pure numerical/unit tests. Keep their synthetic scope explicit.
3. Add adversarial tests for C01/C02/C06/C11/C12/C13/C14/C15. No raw-data inference is needed for these.
4. Build per-probe direct likelihood oracles with verified source files and explicit nuisance/covariance. The five-probe sum is not yet a validated joint likelihood.
5. Only after G0–G4 source, physics, likelihood and numerical gates may the first observed-data pilot run. Do not begin Cobaya production sampling before those gates.
6. For Bianchi-I, use a solver-free temperature-map oracle first; no Bianchi V/VII_h inference without validated transfer.

## Tests that are explicitly not evidence

- A cached GetDist chain is not proof that a Cobaya sampler ran in this session.
- R-1=0.02 default and ESS fallback are not convergence diagnostics.
- Seeded Gaussian pseudo-null is not Planck Commander MC100.
- A successful unit test on generated samples is not source-matched coverage/FPR.
- Summing probe log-likelihoods is not a validated joint law without covariance or independence evidence.