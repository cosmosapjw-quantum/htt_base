# R50: 관측 carrier 재분석과 출판가능성 재심사

기준: GitHub PR #575 HEAD `36bd9030a0759c5563e273dd83836b40034dcda3`.
사용자 기준일 2026-11-15 (Asia/Seoul). 실제 실행 호스트의 UTC 시간과 혼동하지 않는다.
이번 단위: R1–R10/C1–C10을 현재 단위에 적용한 source audit, 세 가지 수치/통계 교정, 기존 실제 Gaia sufficient-statistics 분석, 다음 3개 턴 설계. 전체 우주론 연구 완료를 뜻하지 않는다.

## 판정

현재 R49의 24D 공동 posterior를 **물리적 일반 tilted-Bianchi 관측 제약으로 출판하기에는 major revision이 필요**하다. 배경 상태/제약/진화 구현의 통과한 범위는 보존한다. 그러나 전달함수의 미유도 계수, 관측자 속도 null의 잘못된 구성, probe 응답의 임의 변환, 실자료 PPC 실패가 물리적 해석을 막는다. 체인 수렴은 이 문제들을 해결하지 않는다.

논문화할 가장 짧은 경로는 source-matched signed vector/tensor carrier에서 물리 estimand를 정하고, nuisance·frame·covariance 처리에 따른 정보 보존/손실과 부분 식별을 관측자료로 입증하는 방법론+관측 분석이다. generic tensorization, Gaussian Schur complement, score sufficiency, 일반 Bianchi 분류의 재서술을 novelty로 세우지 않는다. 완전한 raw/optimal-score likelihood와의 동률을 명시해야 한다.

## 확인한 연구사와 범위

- Git fetch로 311 remote branches(+symbolic origin/HEAD), 3,281 reachable commits, 32,943 tracked files를 확보했다. 이것은 inventory이며 전 파일 정독/모든 PR diff 심사가 아니다.
- 기존 `RESEARCH_LOOP_20261022/PR_INDEX.json`: #561까지 558 PR metadata. #1/#445/#448 누락. R48의 `HISTORICAL_SOURCE_MATRIX.json`는 568 PR/307 branch 및 이전 35개 근거를 연결한다.
- 이번에는 최근 100 PR metadata, #565–575 계보, R48/R49 코드·DAG·실행 receipt와 핵심 이전 tensor/kinematics 문서를 대조했다. R49 PR body/README는 오래되었고 최신 커밋은 PR574 수리와 실행 결과를 포함한다.
- Library 원문에서 5변수 정의, 10월 독립 이론 5개 루프, signed joint carrier 및 PM history 결과를 복구했다. 구체 자료는 HISTORY_REUSE.md. Personal Context는 unavailable이므로 모든 과거 대화 전수 확보를 주장하지 않는다.
- 사용자의 현재 요청에 따라 remote desktop은 사용하지 않았다. 현재 호스트에 checkout이 없어서 GitHub에서 단일 checkout을 만들었으며 사용자의 로컬 checkout/worktree는 건드리지 않았다.
- 이전 강제 4-CAS 일괄 규칙은 이번 유한 Gaussian 계산의 정리 인정 조건으로 추가하지 않았다. 요청된 constructive 연구 규약에 따라 NumPy/SciPy 독립 계산과 Wolfram 검산, 독립 코드 심사를 기록한다. 4-axis PASS나 새 no-go는 주장하지 않는다.

## 실제 오류와 처리

| 항목 | 직접 근거 | 처리 |
|---|---|---|
| velocity null | R49는 T21r,T21i,T22r을 20/T_CMB로 확대해 beta_MO null로 사용 | 캐시 생성·소비 제거. raw null 인수 거부. common의 숨은 RandomState(42) fallback도 제거. 같은 추정량의 joint-null 반복을 만들 때까지 matched Pi 없음 |
| Bianchi label floor | a=n=0, Omega_k=0의 동일 입력에서 I/V T-map 상대차 0.1306422425 | 정확한 abelian 경계에서 동일 type-I 계산. I/V/VII0/VIIh/IX T/Q/U 비교 통과. 유한 곡률 전달함수의 물리적 타당성은 별도 미완료 |
| 92.9% 정보손실 | rank-one carrier에도 13/14 출력 | coordinate_reduction_fraction으로 분리, information_loss_ratio_dof=null. 실제 정보손실은 F와 대상 응답으로 계산 |
| Q/F anchor 충돌 | Q의 shear bound는 unavailable인데 F에서 1e-4 재생성 | shear anchor support/occupancy=None, 실제 signed support는 유지 |
| 임의 probe response | DESI cap contrast*0.02를 sigma5처럼 사용; 0.1 A,0.5 A 등 | R51에서 physical-response 식 또는 명시적 phenomenological coefficient로 분리. 현재 결과를 물리제약에 쓰지 않음 |
| mean/covariance 분리 | 동일 모드에서 mu(theta),C(theta)를 금지 | R51 교정 대상. 하나의 normalized Gaussian에서 둘을 함께 계산하는 것은 정당하다. 같은 데이터의 두 likelihood를 독립 곱하는 경우가 중복 계상 |
| finite MC covariance | N=300,p=135 표본 covariance를 정확한 C처럼 사용 | Gaussian/Wishart 조건에서 inverse bias=299/163=1.83436. R51에서 유효 조건을 확인한 t law 또는 독립 검증된 shrinkage/coverage. 숫자만 Hartlap 보정하고 완료하지 않음 |

원심사: INDEPENDENT_R49_AUDIT.json. PRE/POST_REPAIR_FALSIFIERS.json은 전후 실행 결과.
R49 저장 receipt의 Gaia chi2/dof=47.035, CMB=2.015, CF4 약2.75는 모델 적합성 조사 대상이다. 데이터 오류, 응답 오류, covariance 오규정을 분리해서 조사하며 새 물리 발견으로 해석하지 않는다.

## 이번 관측자료 계산

Git에 보존된 Gaia 755,850 source의 G(102x102), b(102)를 실제로 읽었다.
SHA256=`4d9406de69546e72dff79d4fc611703e8eb450944c4dcc254f8484c98a22d5da`.
새 raw catalogue 다운로드/재집계는 하지 않았다. 기존 보고 marginal 2x2 PM noise와 source간 독립 가정을 그대로 둔다. 실제 공간상관·선택효과·물질과 광학 중심의 차이는 미확정이다.

관측 설계 Z=[J,N], normal carrier (G,b)에 대해
$$
F=J^TGJ-J^TGN(N^TGN)^{-1}N^TGJ,\qquad
t=J^Tb-J^TGN(N^TGN)^{-1}N^Tb,
$$
$$
\log L(s)-\log L(0)=s^Tt-\tfrac12s^TFs,\qquad
\widehat s=F^{-1}t,\quad C_s=F^{-1}.
$$
s는 orthonormal STF5 proper-motion response, 단위 microarcsecond/year.
sigma/H로 재명명하지 않는다. 이전 물리적 대응은
$$
A_{\rm PM}=2c(B_o-B_s)/D-\dot B_o.
$$
한 거리에서 두 history/current tensor를 각각 식별하는 대신 다섯 선형조합을 측정한다.

| nuisance 가정 | E2=0의 조건부 chi2 (5 dof) | 조건부 working-law tail |
|---|---:|---:|
| common spin/glide 6개 | 110.4207199652 | 3.33876e-22 |
| 다른 97개 VSH column 모두 | 144.6221609333 | 1.86142e-29 |

두 추정 STF vector 차이 norm은 **7.0625206695 microarcsecond/year**다.
이 수치는 선택된 catalogue와 working law의 residual E2 및 nuisance 민감도를 보여 준다.
공간계통·물리적 source history가 해결되지 않았으므로 우주론적 shear 검출 유의도로 쓰지 않는다.

- full nuisance-profiled Gaussian과 5D tensor carrier log-likelihood ratio 오차: 각각 4.30e-13 / 8.10e-13.
- 올바른 5D optimal linear score와는 **동률**이다. 더 큰 Fisher 정보를 창출하지 않는다.
- 고정 단일 선형 성분으로 줄이면 generalized Fisher retention eigenvalues는 (1,0,0,0,0)이다.
- 사전 고정한 ±1 microarcsecond/year STF 축 대안에서 full signed carrier의 logLR은 모두 계산 가능하다. even norm summary는 T(-y)=T(y)이므로 두 대안의 분포가 같아 logLR=0이다. 방향을 관측값에 맞춰 골라 유의도를 증폭하지 않았다.
- 이 Gaussian 관계는 기존 통계의 재사용이다. 이번 추가 기여는 실제 보존된 관측 carrier를 통한 측정·nuisance 민감도·잘못된 scalar 우월성 주장 교정이다. 이것만으로 문헌 대비 publication novelty가 확보됐다고 판정하지 않는다.

## 다섯 변수의 역할

x는 signed joint carrier와 그 법칙이다. theta=(sigma_ab,omega_a,A_a,beta_RM)와 beta_MO를 frame/epoch/unit별로 분리한다.
Q는 명시적 K0의 gauge, F는 방향 support utilization 또는 지정한 measure의 occupancy이며 서로 구분한다.
Pi는 선언된 law 아래 exceedance, G_F는 cross-depth law를 보존하는 contrast/transport다.
하나의 L(data|theta,nu,M)와 prior에서 생성한 공동 posterior를 push forward한다. 다섯 함수를 독립 likelihood로 곱하지 않는다. anchor·null·depth law가 없으면 해당 출력은 unavailable로 남긴다.

## 선행연구와 판별할 기여

- Alsing & Wandelt (2018), arXiv:1712.00012v2: score compression의 Fisher 보존, Gaussian mean/covariance 공동 의존. HTT의 기준선이며 단순 텐서화 자체로 우월성을 주장하지 않는다.
- Heinesen (2021), arXiv:2010.06534v2: 방향 Hubble 및 고차 cosmography. 부호 convention을 맞춰 H_dir=Theta/3-a.e+sigma:ee를 쓴다.
- Maartens et al. (2024), arXiv:2312.09875v3: 관측자 boost와 covariant cosmography. redshift만 CMB frame으로 옮기는 비교를 baseline으로 쓰지 않는다.
- Kalbouneh et al. (2024), arXiv:2401.12291v2: expansion-rate fluctuation multipoles와 motion/metric 비교.
- Saadeh et al. (2016), arXiv:1604.01024v3: deterministic Bianchi template와 stochastic CMB의 normalized likelihood. 정확히 같은 원시 carrier·mask·covariance·prior로 비교한다.
- Ferreira & Quartin (2021), arXiv:2011.08385v2: Doppler/aberration과 intrinsic dipole 분리. 제거된 release-map dipole을 전체 관측 dipole로 해석하지 않는다.

필요한 차별성은 동일 입력·동일 가정에서 target posterior, model comparison, nuisance robustness를 보존/개선하는 관측적 실증이다. score와 동률인 영역, scalar보다 낫지만 systematics가 지배하는 영역, 물리적 model이 미비해 비교 불가능한 영역을 함께 보고한다.

## PR4 bypass와 이후

현재 보유 카탈로그는 PR3 maps/FFP10, CF4, Gaia/Quaia, NVSS/RACS, Pantheon+, DESI를 포함한다.
R49가 실행한 SMICA lane은 역사적 결과로 유지한다. 사용자의 Commander 일관성 정책은 primary로 설정하고 실제 보유 Commander map+matching MC+mask 계약을 확인한다. 매칭 자료가 없으면 SMICA를 Commander의 대체 calibration으로 자동 사용하지 않고, 기존 SMICA 결과는 그 이름의 별도 diagnostic으로 유지하며 Gaia/CF4를 계속한다.

NPIPE/PR4는 optional robustness이고 어느 critical-path dependency에도 두지 않는다. 추가 다운로드를 하지 않는다. PR3 FFP10으로 PR4 null을 꾸미지 않는다. release별 removed dipole/kinematic quadrupole, mask, beam, harmonic convention을 바인딩한다.

RESEARCH_DAG.json은 R50→R51→R52→R53의 짧은 DAG 및 여섯 독립 과학 lane을 담는다.
R51은 response·covariance 교정과 보유 PR3 관측 재분석, R52는 kinematic/depth/boost 분리, R53은 적대적 benchmark와 유한한 논문 주제 판정이다.
로컬 원자료·체인이 필요한 실행만 LOCAL_AGENT_RESTART_PROMPT.txt에 위임한다. 여기서 가능한 단위는 실제 실행했다.


## 실행 및 다음 시작점

52 tests passed (14.08 s), canonical DAG 277 cards valid, mirrors synchronized. 독립 심사에서 발견된 숨은 null fallback을 교정하고 재검증했다. VALIDATION.json 및 TEST_LOG.txt를 참조한다. 원자료/chain 경로가 이 호스트에 없으므로 신규 full CMB map ingestion, 전체 R49 chain 재실행은 하지 않았다. 다음 노드는 R51이며 로컬 실행 규약은 LOCAL_AGENT_RESTART_PROMPT.txt다.
