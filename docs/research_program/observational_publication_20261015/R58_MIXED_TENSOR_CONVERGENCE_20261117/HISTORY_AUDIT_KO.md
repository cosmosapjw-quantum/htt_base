# HTT 내부 연구 계보와 출판성 재심사

감사 기준: `77f61c17ba33ff28ff4f16a7d42621d8041e5ce4`, tree identity는 `history_coverage.json`에 기록. 기준일: 2026-11-16 UTC. 이 문서는 읽기 전용 내부 근거 감사다. 원 저장소의 파일·ref를 수정하지 않았고 분석 실행·검정 통과를 주장하지 않는다. 모든 상대 경로는 이 commit의 저장소 루트 기준이다.

**현재 판단:** 광범위한 비등방성/전역 tilt 발견 논문이나 새로운 우월 통계방법 논문으로 제출할 근거는 부족하다. 최신 R57 결정은 `BOUNDED_NOTE_EXTENDED`, claim tier C0이고, R54-L07의 경쟁 결과는 `WIN 0 / TIE 2 / LOSS 0 / NOT_COMPARABLE 7`이다. 그래도 실측 자료에서 추정량 편향, survey 영점–방향 패턴 퇴화, 공분산·nuisance 처리에 따른 주장 변화는 재현 가능한 좁은 결과 후보다. 다음 한 번의 수렴 실행은 이 결과를 **공통 상태의 tensor confidence set와 동일자료 적대적 비교**로 완결하는 데 써야 한다. 텐서화·union confidence set·support-function 수학을 새로운 발명으로 주장해서는 안 된다.

## 1. 전수조사의 실제 범위

| 층 | 이번 확인 | 한계 |
|---|---|---|
| 현재 tree | tracked entry 33,096개 path/type/git-blob 전수 | 본문 전수 독해가 아님 |
| git history | HEAD에서 도달 가능한 commit 2,177개의 부모·날짜·제목 전수 | unfetched remote branch 및 unreachable object 포함 아님 |
| GitHub PR | REST `state=all` 6페이지, 575개 고유 PR, 번호 최대 #578; merged 80, closed-unmerged 351, open 144 | 이번에는 metadata 전수; 원 PR body/diff 전수 재독 아님 |
| 현재 observational tree | 58개 최상위 directory 전수 + 루트 문서 7개 | R54의 역사적 57-directory census를 현재 수치로 오인하지 않음 |
| substantive sources | 핵심 이론·수치 보고서·최신 claim 표를 선택 실독; 정확한 파일별 full/partial scope와 sha256은 coverage JSON | 출력을 잘라 읽은 문서는 partial 또는 inventory-only로 표시 |
| 과거 PR 내용 | R39 `PR_LEGACY_AUDIT.md`의 32개 body/17개 diff 조사와 R50 `HISTORY_REUSE.md`를 직접 재독하여 재사용 | 해당 PR diff나 Library PDF를 이번에 다시 전부 읽은 것으로 세지 않음 |

별도 scratch 산출물: `history_tree_inventory.jsonl`, `history_git_log_inventory.json`, `history_pr_inventory_live.json`. 입력 commit과 inventory 생성 명령이 고정되어 있으므로 목록을 재생성할 수 있다. R50의 과거 all-ref 3,281 commits/311 branches, R54의 과거 573 PR 등은 당시 snapshot 수치이지 현재 실독 깊이의 근거가 아니다.

## 2. 회수한 실제 이론 계보

### 2.1 이미 존재했던 vector/tensor x와 물리량 likelihood

`docs/research_program/HTT_VECTOR_TENSOR_MES_TWO_PILLAR_UPGRADE_PLAN_20260730.md` §§0–2는 이미 typed physical state → SO(3) orbit/O(3) parity → premise body/response → functional/set/path-valued statistics를 명시했다. 이 문서는 당시 제안서였으므로 그 자체를 구현·과학 승인으로 읽을 수 없다. 특히 C-04가 `F`의 occupancy, pushforward, support-utilization 혼용을 이미 지적한다.

`docs/research_program/observational_publication_20261015/OBSERVATIONAL_CONVERGENCE_R39_20261107/VECTOR_TENSOR_X_FRAMEWORK.md:207–222`는 사용자가 지금 요청한 형태를 정확히 담고 있다. 상태에는 직접적인 `sigma_ab, omega_a, A_a, beta_RM, beta_MO`가 들어가고, x는 그 성분·정규화·혼합 contraction·예측 harmonic/VSH/distance carrier의 **typed functional bundle**이다. 하나의 `p(D|theta,psi,eta)`와 공통 posterior/confidence set에서 다섯 view를 유도하며, view 다섯 개를 독립 likelihood factor로 곱하지 않는다. `KINEMATICAL_LIKELIHOOD_MODEL.md`는 physical state와 observable STF가 같은 표현형이어도 동일 물리량이 아님, STF5 좌표의 비정규 Gram, frame/congruence/epoch, shared latent covariance를 명시한다.

따라서 지금 미완료인 것은 “스칼라를 처음 텐서로 확장하는 이론”이 아니라 **이미 있는 계약을 실제 검증된 데이터 연산자에 적용하여 어떤 물리적/현상론적 functional이 식별되는지 끝내는 것**이다. R39의 설계 상태와 이후 실제 실행 R50–R54를 구분해야 한다.

### 2.2 R7–R9에서 바로 재사용할 수학

아래는 새 theorem이 아니라 현재 구현의 donor다.

| 원문 locator | 재사용할 진술 | R58에서 소비하는 결정 |
|---|---|---|
| `tensor_joint_r7/THEORY.md:121` | maintained model confidence set은 union, 동일상태 측정은 intersection. valid model-wise p의 max가 union null을 검사 | 가장 유리한 nuisance p를 골라 발견하지 않는다 |
| `tensor_joint_r8/THEORY.md:115–126` J1 | `C(Y)=union_nu [D_nu intersect intersection_j A_j,nu(Y_j)]`; true admitted tuple + sum alpha로 임의 cross-dependence 하에서도 coverage | nuisance law·covariance·calibration을 서로 모순되는 tuple로 조합하지 않는다 |
| `tensor_joint_r8/THEORY.md:189–195` P2 | nested budget `D(rho)`에서 set image 단조 확장, `rho_crit=inf{rho:g0 in I_g(rho)}` | zero-point budget에 대한 민감도 경계; rho posterior라고 부르지 않는다 |
| `tensor_joint_r9/THEORY.md:27–49` T2 | nuisance를 한 번 투영한 `y=D theta+b'+epsilon`; finite target iff `ell ker(D)=0`; support는 방향성 discrepancy를 유지 | unidentified physical direction을 prior로 숨기지 않는다; projected residual은 별도 적합성 관측량 |
| `tensor_joint_r9/revision2/THEORY_EXTENSION.md:7–28` D1 | 인접 depth contrast도 off-diagonal covariance를 갖는다; 대각화 반례 명목5%→실제5.95427643% | cross-depth 및 polar–STF 공분산 삭제를 통제된 오염 ablation으로만 사용 |
| 같은 파일 `:44–64` D3 | `(Y_0,HY)`는 가역적으로 원 path 보존, contrast만 남기면 common signal 소실 | raw depth path와 initial/common level을 보존 |
| 같은 파일 `:79–87` F1 | 한 유효 simultaneous confidence event의 여러 functional image는 함께 유효 | axis/shape/amplitude를 공통 set에서 pushforward; 개별 95% interval을 동시집합으로 오인하지 않음 |

R9 T2의 실행형 식은, 고정된 whitening과 nuisance projection 후 `D=U^T A`, `P=D D^+`, `r=rank D`일 때

\[
\mathcal C_\alpha(y)=\{\theta:\exists b'\in\mathcal B',\;\|P(y-D\theta-b')\|\le c_r\},\qquad c_r^2=\chi^2_{r,1-\alpha}.
\]

식별되는 선형 functional `ell theta`에 대해 `t=ell D^+`이면

\[
h_{\ell\mathcal C}=t y+h_{\mathcal B'}(-t)+c_r\|t\|.
\]

이 식의 유효성은 known justified joint Gaussian law, fixed design/nuisance/budget에 조건부다. 실제 자료에서 정한 nuisance family, estimated covariance, selection은 각각 추가 조건을 필요로 한다. 유한 모델 목록의 max p는 **그 목록**에 대한 union null일 뿐, 모든 연속 calibration 또는 모든 물리모형에 대한 supremum이 아니다.

### 2.3 회수하되 이번 실행에서 넓히지 않을 경로

- R7 T3 / R8 P1의 radiation-jet MES는 `vec(S,W)=Kj+r`의 set-valued inference다. `a_lm` 한 장으로 공간/시간 미분 jet가 측정되지는 않는다. 기존 sky의 morphology를 shear/omega 값으로 즉시 바꾸지 않는다. 물리적 derivative/remainder budgets를 독립적으로 제한할 때만 본체를 만들 수 있다.
- R7 T6의 shared-calibration Schur 정보 이득은 calibration-only 자료가 **실제로 같은 nuisance와 연결될 때** 성립한다. 임의 소스들을 함께 넣은 뒤 연관성을 가정하는 근거가 아니다.
- R7 T9 / R8 P2 / R9 T1의 observer/global radial response 비는 낮은 z에서 차이가 O(z²)부터 생긴다. bin 수 증가만으로 분해가 가능해지지 않으며 실제 창·공분산·nuisance 후 rank와 conditioning이 필요하다.
- R50 HISTORY_REUSE의 radiation operator `L_I S=(8rho/15)S+(10/7)STF(S pi)-H4:S`는 이미 존재하는 물리적 route다. 실제 residual에 필요한 differentiated multipoles가 없으므로 소유 데이터만으로 이번 논문을 끝내는 최단 경로가 아니다.
- R39가 지목한 #442–444 local-boost full-sky/processed response, #548–559 Planck/CF4 source-window·mask/beam work는 재사용할 선행 구현이다. 새로운 병렬 boost kernel·native Bianchi solver를 만드는 것은 이번 CF4 수렴 작업에서 제외한다.

## 3. 현재 출판성 판단의 근거

최종 수치 근거는 `R54_TENSOR_FRAME_TOMOGRAPHY_20261116/MANUSCRIPT_CLAIM_TABLE_R54.md`, `FINAL_DECISION_R57.md`, `RESULTS/R54_L07_BENCHMARK.json`이다. `THEORY_LOOPS.md`와 `R54_REPORT_KO.md`에는 초회 수치와 최종 대체 수치가 함께 있어 앞부분의 강한 p-value를 최종 결과로 선택하면 안 된다.

| 연구 주제 | 현재 결론 | 수렴시킬 후속작업 |
|---|---|---|
| low-ell morphology→physical observables | T/E는 shear history의 서로 다른 kernel functional. 현재 shear는 history/model 의존. T pipeline shift ≤0.34 sd. E B-null은 FFP-only p=0.00664/0.00332이고 같은 자료에서 만든10.6배 floor로만 통과하므로 diagnostic | T-only conditional result와 history null-space 정리를 분리. E로 새로운 limit를 만들지 않음 |
| dipole anomaly | owned catalogues receipt-systematic tails Quaia0.309, NVSS0.421; doubled dipole power0.20이므로 anomaly 부재나 외부 결과 반박 아님 | 동일 estimator/같은 mask·law·nuisance의 benchmark를 완료; 새 catalog acquisition은 안 함 |
| beyond-FLRW kinematics | first-order omega column 없음; acceleration-type dipole은 calibration dipole과 퇴화. polar rank15/18 | `theta`의 물리명과 실제 response-identified parameter를 구분; null directions·mixed-functional 식별성 보고 |
| anisotropy/Bianchi classification | STF amplitude/shape/frame는 분류 가능한 observable 구조. family-native transfer 없이 Bianchi family identification 불가 | 공통 tensor confidence set의 eigenvalue/shape admissible 범위를 보고; eigen-axis 불안정이면 axis claim 중단 |
| H(z,n) | log estimator로 R36의14–40% pole-dipole bias 교정; exact body std 증가; survey offset -0.074±0.026mag. nuisance 따라 p=.00457–.0653 이상으로 변화 | 기존 CF432차원 polar+STF carrier에서 full covariance, nuisance union, 동일자료 ablations 수행 |
| local boost/global tilt | global-tilt p=.0832, closure p=.0865, independent frames p=.158; calibration+countoffset p=.531. 현재 분리력 부족 | 실제 direction/depth/nuisance Jacobian의 식별 contrast만 보고. 광범위 global-tilt 발견·배제 대신 허용 set과 calibration sensitivity frontier |

R54의 상수 quadrupole 2.2–2.6% H는 통계량을 초회 자료 관찰 뒤에 선택했으므로 `HOLD`다. 더 작은 p-value를 산출해도 이 history는 사라지지 않는다. CF4 북쪽 FP_SDSS 비율 .96, 비SDSS 북쪽 비율 .01이라는 support 비대칭은 physical direction과 survey zero point를 분리하기 어렵게 한다. 반구 step 공통값 -1.65±.55% H 및 scan-corrected tail .0339은 **서로 다른 scope의 검정**이며, 다른 window excess와 같은 발견으로 합치면 안 된다.

Broad methods paper의 치명적 약점은 (1) exact likelihood보다 우월할 수 없다는 본인의 sufficiency 결과, (2) scalar 약한 baseline과 비교한 gain을 full-information competitor gain으로 과장할 위험, (3) source-specific nuisance·selection·finite-MC law가 같은지 불명확한 benchmark다. 현 결과는 제한된 실행/견고성 note로 검토할 수준이며 저널 적합성·acceptance는 아직 확정할 수 없다.

## 4. `x,Q,Pi,F,G_F` 정의의 drift와 수리 범위

| 항목 | 재사용할 정확한 의미 | 발견한 혼용과 수정 규칙 |
|---|---|---|
| x | typed `phi_alpha(Z)`; physical direct/mixed functional, predicted carrier, observed carrier 역할 구분 | R54 x가 `(F,t)` precision carrier로 좁아짐. 저장 carrier와 출력 functional x를 서로 다른 schema로 선언 |
| precision | Gaussian `J_precision=A^T C^-1 A`, score t, 필요시 q0 및 normalized-law 상수 | R54 문헌의 precision F는 다섯 view 중 F와 충돌. 새 코드는 `J_precision` 사용 |
| Q | 이름 붙은 convex anchor/body의 gauge 또는 acceptance normalization | shape 없는 scalar ceiling을 자동 물리 prior로 만들지 않음 |
| F | `F_support(u)=h_C(u)/h_K0(u)`는 directional support-utilization | `common/htt_five_variable_state.py:48–53,235`의 `occupancy_ratios` 이름은 같은 비를 occupancy라 부름. 새로운 결과에서 occupancy라고 부르지 않고 definition_id 명시 |
| Pi | 명명한 sampling/posterior law에서의 exceedance/tail | confidence set만 있으면 probability 없음. model p, posterior probability, support bound를 섞지 않음 |
| G_F | full depth path+transport+full covariance+initial/common level | R54 `THEORY_LOOPS.md:43`에서는 GLS chi² 하나로 좁아짐. `GF_transport_chi2`는 파생 readout으로 보존하되 `raw_depth_path`를 대체하지 않음 |

R51은 finite-MC likelihood에서 `(J,t)`만 남기면 충분하지 않고 `q0`까지 필요함을 실제 로그비 오차로 보였다: 이전104.4 → q0 보존9.9e-14. R58의 known-Gaussian mean inference에서는 `(J,t)`가 충분하더라도 **model adequacy에는 q0**, 서로 covariance가 다른 model/evidence 비교에는 determinant·normalization 및 각 model에 필요한 공통 statistic이 필요하다. raw data 또는 충분한 공통 carrier 없이 각 model별 score를 임의 비교하지 않는다.

명명된 상대속도에도 drift가 있다. R39 kinematic contract는 `beta_RO=beta_RM+beta_MO`, R54 L2는 `CMB dipole=beta_MO-beta_RM`라고 쓴다. 이는 endpoint/sign convention을 확인하기 전에는 같은 beta 이름끼리 직접 연결할 수 없다는 뜻이다. R54 T9처럼 `v_O,v_R,v_j`에서 방향을 먼저 정의하고 유도해야 한다. 이번 CF4-only 데이터 회귀에는 새 multi-probe frame 조립이 필요하지 않다.

## 5. 최신 R54-THM의 처리

HEAD의 `THEOREMS.md`와 `RESULTS/R54_A2_ATTRIBUTION.json`까지 확인했다. R54-A2는 T6를 `LOW (searched)`, T8을 `LOW-MODERATE (searched)`로 표시하며 attributed re-derivation으로 인용하도록 한다. 검색에서 동일 문장을 찾지 못했다는 사실은 우선권 증명이 아니다. T6의 O(3) rank organization과 T8의 classical T/E kernels에 대한 Chebyshev sign-change 적용은 해석을 명확히 하지만 단독 broad novelty 근거로 부족하다.

후속 코드/문서가 그대로 상속하면 안 되는 문장은 다음과 같다.

1. T3의 정확한 항등은 `p(nu|iota,y)=p(nu|iota)`다. `iota` posterior가 집중되고 prior 상관구조가 있으면 marginal `nu` posterior 폭이 바뀔 수 있으므로 “비식별 방향의 posterior 폭은 자료로 전혀 줄지 않는다”는 일반 표현은 과도하다. 유한 prior interval이 uniform frequentist coverage를 얻지 못한다는 결론과 구분한다.
2. T8의 무상한은 **unrestricted infinite-dimensional shear history**에 대한 결과다. “모든 upper limit는 ≤2 parameter family 또는 sign restriction이어야 한다”는 consequence는 compact norm/regularity/derivative budget 등 다른 충분한 제한을 배제하여 지나치게 강하다. 실제 no-go statement의 가정을 좁혀야 한다.
3. T6의 vorticity-blindness는 observer-local/homogeneous first-order equivariance와 parity assumptions에 조건부다. finite-wavelength/spatial gradients, parity-breaking chain, higher-order products까지 없는 것으로 확대하지 않는다.

이 감사는 해당 theorem tests를 실행하지 않았다. 고치는 경우 담당 수학 검토자가 최소 반례/가정 검사를 수행해야 하며, 새 데이터 결과와 unrelated 전체 theorem 재감사로 scope를 넓힐 필요는 없다.

## 6. 권고하는 한 번의 다음 루프: 공통 tensor set의 nuisance 견고성

**질문:** 이미 소유한 CF4 log-distance 4-window × (polar3+STF5) 32차원 carrier에서, full polar–STF 및 cross-depth covariance와 기존 admissible calibration variants를 함께 유지하면 어떤 방향·깊이 functional의 null exclusion/허용 범위가 남는가? scalar norm이나 block-diagonal simplification은 실제로 어떤 결론을 잃거나 왜곡하는가?

직접 실행 우선순위는 (i)32×32 전체 covariance와 row order 재사용, (ii)동일 mean/covariance/nuisance에서 exact Gaussian likelihood와 tensor carrier logLR tie, (iii)각 유지 model의 동시 confidence set과 그 union, (iv)등록된 direct/mixed functional의 image 또는 엄밀 outer bound, (v)raw-likelihood/score/tensor/scalar/block-diagonal ablation이다. 새로운 물리법칙을 만들기보다 기존 formalism이 **실제 데이터에서 calibration 민감성을 숨기지 않는 해석 도구로 얼마나 유용한지** 측정한다.

이때 모델별 null p의 max는 `ROBUST_OVER_DECLARED_FINITE_MODEL_LIST`로만 부른다. 이미 데이터로 model들을 설계한 history를 유지하고, 재사용 자료의 model 선택 효과를 무시한 confirmatory discovery로 격상하지 않는다. 서로 다른 covariance로 만든 각 valid set은 동일 물리/현상론적 parameter space로 embedding한 뒤 union해야 한다. nonconvex union을 ellipsoid나 convex hull로 바꾼 경우 exact set과 outer hull을 구분하며, support만으로 holes/chirality를 복원했다고 말하지 않는다.

같은 carrier에서 exact score tie가 나오는 것은 성공적인 구현 검증이지 방법 우월성 WIN이 아니다. scalar compression 대비 더 많은 identifiable functional/상대방향 정보를 회복하면 그 baseline에 한정한 유용성이고, weak baseline을 골라 novelty를 만들지 않는다. competitor가 단순 GLS에 같은 full carrier를 넣어 동일한 robust decision을 얻으면 이를 TIE로 보고한다.

**완결 조건:** 생성된 관측 결과가 claim table과 연결되고, 모든 모델/ablation이 동일 데이터·row order·law·normalization·nuisance 계약을 지키며, 하나의 제한된 결론을 선택한다. 유의성이 없어지면 “유지한 calibration models에서 anomaly claim은 견고하지 않았다”로 끝낸다. 일부 기능만 견고하면 해당 window-functional과 모델 목록만 한정하여 보고한다. 모든 경로가 기존 GLS와 실질적으로 동률이고 새 데이터 해석도 없다면 신규성 확보 실패를 기록하고, 새 theorem/감사/DAG 문서만 늘리면서 루프를 재개하지 않는다.
