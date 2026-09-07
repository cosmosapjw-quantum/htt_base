# HTT 모의심사 후속 연구 — 계획 완결 및 기존 연구와의 통합

Date: 2026-09-07
Owner: MAIN conversation; downstream executor: Local Codex
Status: PLANNING_COMPLETE / THEORY_FREEZE_PENDING_M1_M2_M3

## 0. 재개 기준과 문서 우선순위

원격 최종 동기화에서 이전 작업의 **PR462**와 7개 연구 파일이 이미 게시돼 있음을 확인했다. 그 결과를 새로 시작하거나 다시 열지 않는다.

고정 선행 기록: `b4d04e62d664997eb9e1858b6195c35e4ece3378`, tree `ea95984f5f1b1d977ca625dfde9a34d71202b115`, branch `research/htt-postreview-theory-first-20260907-r1`.
경로: `docs/research_program/post_review_20260907/`.
실제로 다시 읽은 핵심 파일: `IMPLEMENTATION_CONTRACT.md` (blob `b55f9e01916875b2940781e6e6fb0ebf42a7bb0e`), `CODE_DATA_REUSE.md` (blob `bef155a1bb5a032e8cb65c97c3d264292dbd8778`), `THEORY_FIRST_DAG.yaml` (blob `5afa78b7d001d0aba25c6a3aeacf40cb98ad425c`) 및 PR 설명.

**이번 PR463은 PR462를 대체하는 새 연구프로그램이 아니라 계획 완결·추가 source finding의 보완판이다.** 선행 T1–T10은 `T_CORE=DERIVED_NOT_NATIVE_TESTED`로 재사용한다. 이번 `01_DERIVATIONS_AND_REVIEW.md`에서 겹치는 직접 유도를 새 연구 성과 열 개로 다시 세지 않는다. 새로 구체적으로 읽은 constrained-realisation/affine 코드의 의미론적 반례와 구현 위험은 별도 보완이다.

활성 계획은 본 파일과 `03_PROGRAM_DAG.yaml`이다. 초기 보완 초안의 T1–T4는 이제 다음처럼 통합한다: T1은 선행 T_CORE의 정리·재검토, T2/T3은 M1/M3, T4는 M2다. `02_REUSE_AND_EXECUTION_CONTRACT.md` 안의 해당 옛 묶음 이름도 이 대응으로 읽으며, 네 개의 추가 연구 gate를 만들지 않는다. 기존 15개 회귀 oracle은 선행 `REGRESSION_ORACLES.json`을 재사용하고 이번 수학 노트 §8의 추가 oracle은 이름·내용을 대조해 중복 없이 합친다.

## 1. 결정된 연구 범위

55쪽 pedagogical report는 요청된 해설판으로 보존한다. Research article 기준의 기여도·문헌·관측 연결 요구는 새 집중 논문에서 해결한다. 기존 문서 산출물의 완료를 소급 취소하지 않는다.

핵심 질문:

> 저다중극 형태와 관측자·깊이 정보를 함께 다룰 때, 추가 관측과 부수변수 가정은 각각 어떤 식별가능성을 제공하는가?

세 물리적 목표를 유지한다.

**A. CMB 형태·응답·부수변수.** Q/O 공동 불확실성과 local-observer response를 분석하고, 무제한 결정론적·진폭 제한·Gaussian prior·추가 high-mode data로 제약한 nuisance를 같은 추론 대상에서 비교한다. 첫 후보는 기보유 PR3 SMICA와 실제 product-matched FFP10이다. PR4는 별도 intake 조건을 만족할 때 control로 추가하며, 빈 NPIPE 디렉터리를 완성된 입력으로 취급하지 않는다.

**B. Redshift/depth별 local motion과 pole coherence.** CF4 primary catalogue/명시된 reconstruction과 DESI catalogue/randoms/mocks를 통해 window-matched bulk·대칭 affine·dipole-depth를 다룬다. Carrick/CORAS/Lilow는 공유 원자료의 의존성을 가진 sensitivity controls다. ShellSourcePole, CumulativeObserverPole, RemoteDipolePole, RemoteQuadrupolePole은 구별한다. H_LOCAL/H_LSS/H_COHERENT_PHENO는 명시된 response에 한하며 H_GLOBAL_NATIVE는 별도의 실제 transfer가 없으면 대상이 아니다.

**C. 조건부 운동학적 경계.** 기존 MES 계보의 conservative bounds와 명시적 1차 복사 모형 안의 cancellation-sensitive bounds를 나란히 설명한다. Intrinsic-dipole 귀속, all-domain 확장, derivative envelope, 관측오차를 분리한다. 관측되지 않은 derivative·vorticity·global tilt를 자동 추정하지 않는다.

새 BASS/REI/REC solver, 모든 Bianchi family, 전체 비선형 almost-EGS, 신규 remote kSZ/pSZ 재구성, 대규모 새 다운로드는 이번 유한 campaign의 필수 경로가 아니다. ACT lensing kappa는 temperature/kSZ map이 아니고 lensing shear는 congruence shear가 아니다. 원래 장기 목표는 삭제하지 않고 실제 필요한 response가 갖춰진 후속 경로로 남긴다.

## 2. 모의심사 판정의 확정 내용

두 심사와 두 업그레이드 문서의 실제 수치 재현 주장은 해당 작성자의 보고로 남긴다. Markdown 안의 검산 ZIP 링크만으로 실행 코드·원 로그를 취득했다고 하지 않는다.

채택할 핵심은 다음과 같다.

- Multipole-vector 및 frame/invariant 계보, 2026 boost operator와의 비교가 필요하다. '파워보다 정보를 보존한다'는 일반론은 새 기여가 아니다. 이번 표현의 construction, coupled response/uncertainty와 계산적 차이를 좁게 비교한다.
- 기존 exact minors는 이미 최소 axial cutoff L=10을 증명한다. L<=9의 m=0 열 부족과 결합하면 최소성이 나온다. 비축방향 숫자는 named-direction numerical evidence와 generic-direction algebraic statement를 각각 구분한다.
- 미관측 high modes가 summary에서 제외됐다는 이유로 모든 원자료에서도 정보가 없다고 하지 않는다. 추가 high-mode 측정과 같은 자료의 cross-covariance를 이용한 비교가 핵심이다.
- beta^2 T0와 beta DeltaT의 상대 크기, source Jacobian과 velocity Jacobian, finite-pixel matrix와 continuum target, physical positivity를 명시한다.
- 통합 synthetic experiment는 bias·coverage·size·power·abstention을 평가한다. 연구 결과가 null이거나 map들 사이에 차이가 있다는 사실은 software FAIL이 아니다.

그대로 수용하지 않을 내용도 확정했다.

**Deterministic delta.** 실제 error enclosure가 유효하고 s_min>1이면 계산 후 여유폭을 보고해도 된다. Error family/radius의 부당한 선택이나 확률적 coverage의 selection 문제가 별도다. 제안서 P5의 사전 delta 강제는 첫 심사의 올바른 지적과 모순된다.

**Low-ell no-go.** 지정된 Gaussian mean model의 Fisher는 양의 정부호다. 낮은 정밀도는 모든 추정자·추가 정보에 대한 불가능성 정리가 아니다. 반대로 intrinsic O가 완전히 자유로운 deterministic nuisance이면 구조적 비식별성이 있다. 제안서의 입력과 공식으로 conditional RMS는 0.88235–0.88785이며 0.8435가 아니다.

**완전한 anomaly scan.** Orbit separation은 모든 대립에 powerful한 검정이나 통계적 충분성의 증명이 아니다. 17개 중복 packet 좌표를 독립 Gaussian 9차원으로 취급하지 않는다. |chi|는 parity-even이고, null 결과가 모든 기존 anomaly의 상한을 주지도 않는다.

**가정 사다리.** 단일 observer amplitude만으로 첫 MES 상한을 배정할 수 없다. 모든 필요한 congruence·radiation·derivative·extension premise를 적용하기 전 단계는 '상한 미도출'이다. Bianchi-specific Bayesian bound와 일반 conditional ceiling을 숫자만 비교하지 않는다.

**수치 인증.** 두 수치 경로의 일치, Nside convergence, kappa times machine epsilon만으로 error family의 포괄성을 증명하지 않는다. Gaunt/Wigner 경로도 mask coefficient·truncation·transfer·roundoff의 영향을 받는다. Toy L=30 수렴은 real masks의 보편 cutoff가 아니다.

**문헌 identity.** astro-ph/0502574는 Land–Magueijo이며 Katz–Weeks는 astro-ph/0405631이다. Generic Bianchi I/V/VII0가 모두 축대칭이라는 식의 표현도 LRS subset으로 좁혀야 한다. Reference 수 자체나 teaching register 자체를 오류로 판정하지 않는다.

## 3. 기존 결과 재사용과 이번 추가 coding-research finding

선행 PR462의 T1–T10을 재사용한다: L=10와 generic-direction argument, Beta(3/2,2), exact LS covariance/trace bound, sharper internal shear/vorticity, weighted nuisance cost, joint high-mode conditioning, soft-mask scaling, observer/free-shell gauge, radial rigid-rotation null. 이번 노트는 일부를 다시 전개하고 implementation oracle을 명시했지만 native 재검증으로 승격하지 않는다.

추가로 실제 읽은 두 구현에서 다음을 확인했다.

1. `htt/obsstat/constrained_realizations.py`는 d=s+n 모형의 scalar Gaussian conditional sampler다. d=0이어도 posterior variance는 SN/(S+N)다. 이것은 H=0의 '관측 감도 없음'일 때 variance S인 것과 다르다. S=1,N=0.5에서 1/3과 1을 구별하는 정확한 회귀 조건을 추가한다. 기존 sampler의 H=1 수식이 틀린 것이 아니라 'zero data = no constraint'라는 해석·활용 계약이 잘못될 수 있다.
2. `affine_flow.py`의 shear amplitude는 sqrt(0.5 sigma:sigma)이고 보고서 MES norm은 sqrt(sigma:sigma)다. 명시적 adapter가 필요하다. n_cells>=4만으로 affine design full rank가 보장되지 않는다. Cell bootstrap은 correlated field의 calibrated covariance도, 항상 성립하는 lower bound도 아니다.

선행 source risks도 유지한다: selection weight와 precision의 혼동, active count와 response rank 혼동, NaN이 minimum rank로 통과할 위험, diagonal-whitening skeleton을 실제 joint likelihood로 사용하는 오류. **CF4 P0 quarantine은 유지**하며, 새 원자료 availability가 refuted headlines를 복권하지 않는다.

## 4. 남은 MAIN 연구는 원래의 세 계약으로 한정한다

계획 작업은 닫았다. 다음은 아래 계약을 수식·검증 사례로 완성하는 연구이며, 별도의 계획을 다시 쓰는 작업이 아니다.

| 단계 | 고정할 내용 | 실제 종료 조건 |
|---|---|---|
| M1_CMB_MODEL | 주 PR3 product와 ordered observation operator; foreground/noise/low-high joint law; primary score; mask/tail/numerical policy | 데이터 identity를 기계적으로 resolve할 조건과 실패 분기까지 명시. Statistic·prior·missing-response 선택을 Codex에 남기지 않음 |
| M2_REDSHIFT_MODEL | 선택 distance/redshift observable의 likelihood; calibration/selection/frame; shell windows; supported/unidentified physical functionals | 각 product의 observation operator, covariance, prior dependence가 수식으로 닫힘. Toy profile을 native global tilt로 바꾸지 않음 |
| M3_EXPERIMENT | M1/M2를 exact estimand/input/algorithm/output, masks/bins, training/calibration/test, null/alternative, multiplicity/coverage와 실행표로 결합 | '적절한 값 선택'이 아니라 값·규칙·reference가 포함된 단일 실행 계약. Missing input, singular model, insufficient null, scientific discrepancy마다 처리 결정 명시 |

M1과 M2는 이론적으로 독립 진행 가능하고 M3에서 합친다. 새 T1–T4를 또 수행하는 것으로 세지 않는다. 지금 발표한 algebra notes만으로 M1/M2의 실제 경험적 모형이 확정된 척하지 않는다. Exact product byte paths, installed imports와 지원되는 realisation ID는 frozen semantic predicate에 따라 Codex가 기계적으로 확인할 수 있지만, physical likelihood와 hypothesis는 MAIN에서 정해야 한다.

## 5. Theory freeze 뒤 한 번의 Local Codex campaign

```text
PR462 T_CORE + REUSE + 이번 source 보완
               |                 |
          M1 CMB model       M2 depth model
               +--------+--------+
                        M3 experiment
                             |
                       THEORY_FREEZE
                             |
                C0 integrate selected donors
                    /                 \
           C1 implement          C3 selected-data intake
                 |                     |
           C2 synthetic validation     |
                    \                 /
                       C4 observed analysis
                     /                      \
               CMB results               depth results
                     \                      /
                   C5 readable Git return
                             |
                     MAIN interpretation
```

성공 의존 DAG와 별도로 **어느 실행 노드에서든 중단·부분 결과를 C5_RETURN으로 보낼 수 있다.** Downstream observed analysis 성공까지 기다려야 실패를 반환하는 구조로 만들지 않는다. 자료 부족은 그 data branch를 막고, 다른 admitted branch와 이론/synthetic 결과는 보존한다. 제외된 branch까지 전체완료로 세지 않는다.

구현은 기존 common/OBSSTAT/HTT/MIO 소유권을 유지한다. Exact boost/STF, accepted decoder, processed fit/error algebra, finite-null ranking, CF4/DESI builders와 shell code를 선택적으로 통합한다. 함수를 다시 만드는 것보다 실제 import identity·의미·affected regression을 먼저 확인한다. 기존 코드가 없는 부분만 새 numerical consumer로 작성한다.

한 번의 인계 뒤 Codex는 ordinary implementation/numerical/parsing/plotting/packaging defects를 자율 수리한다. 새 물리모형·prior·statistics를 고르거나 보호된 의미를 바꿔야 할 때만 정확한 science boundary를 반환한다. '과학적 선택 없이 실행'은 debugging을 금지한다는 뜻이 아니다.

## 6. 자산·비용·성과 판정

사용자 inventory의179bundles/약1.499TB는 presence metadata다. C3는 기존 inventory와 선택 inputs만 읽고, 전체 재다운로드·재해시·패키지 전수조사를 하지 않는다.

PR3/FFP10을 첫 후보로 유지한다. 1312 file paths는1312independent skies가 아니다. Dedicated PR4 경로는 빈 것으로 보고돼 있고 RRSS PR4의9개 product는 별도다. Posterior draws와 null realisations, WMAP7sims와 WMAP9data, ACT lensing과 temperature를 구별한다. 이미 있는 CF4/2MRS reconstructions는 독립 anchor가 아니다.

관측 성공 조건은 신호검출이나 지도일치가 아니라, 명시된 추론이 실제 입력/모형을 충실히 평가했다는 것이다. Coverage, size, power, numerical uncertainty와 abstention을 보고한다. A covariance trace ratio alone is not information loss. 무리한 'complete anomaly'나 전 우주론적 no-go 결론은 없다.

월 단위 ETA는 실측 없이 고정하지 않는다. 남은 이론은3단위, 그 뒤 기존 DAG의 C0–C5를 하나의 campaign으로 묶는다. C0/C3의 작은 처리량·메모리 측정으로 production batch/time을 산정한다. Planning budget은 누적사용과 변경 이유를 남기며 조정한다. 명시적 owner/platform/privilege 제한은 보존한다.

## 7. 현재 상태와 검증 한계

완료: 두 심사·제안의 판별, 선행 PR462 재사용 확인, 계획의 범위·우선순위·reuse·DAG·stop/return 정책 정리, 추가 source-level counterexample와 oracle. 선행 직접 유도는 그대로 derived 등급이다.

미완료: M1–M3의 최종 과학 명세, native 신규 test/CAS/Monte Carlo, data-content admission, 실제 데이터 분석. 현재 `execution_release=false`이며 이 계획은 즉시 Codex를 시작시키는 handoff가 아니다. 29/55쪽 report artifact 완료, canonical30/corecandidate40, PR284deferred와 finite-pixel unresolved는 유지된다.

이번 shell/Python은 ClientError로 끝났고 새 native 실행은 없다. 일부 상수만 웹 계산기로 확인했다. 원격 core/default/decoder 경로를 조사했지만 모든 source·branch·로그를 전수 실행감사하지 않았다. 큰 JSON tree는 잘렸으므로 '전역 구조+핵심 경로'와 '모든 파일 읽기'를 구별한다. YAML의 dependency 구조는 직접 검토했으나 native parser 실행은 주장하지 않는다.

## 8. 확인한 주요 문헌

- Copi–Huterer–Starkman, arXiv:astro-ph/0310511, PRD70 043515 (2004): 기존 완전 multipole-vector 표현.
- Katz–Weeks, arXiv:astro-ph/0405631, PRD70 063527: 다항식 construction/uniqueness.
- Land–Magueijo, arXiv:astro-ph/0502574, MNRAS362838 (2005): frame과 invariants 분리.
- Chluba–Ravenni, arXiv:2505.02080; MNRAS548(3)stag698, 14April2026: boost operator와 low-multipole/primordial-dipole 해석. 검출불능을 모든정보·모든모형으로 확장하지 않음.
- Saadeh et al., arXiv:1605.07178: mode/model-specific Bianchi constraints.
- Clarkson–Barrett, arXiv:gr-qc/9906097: isotropic radiation/Copernican과 acceleration 등의 premise.
- Planck NPIPE, arXiv:2007.04997: 제품과 시뮬레이션 대응은 실제 local intake로 확인.
- Aluri–Patel, arXiv:2506.22795; Nofi et al., arXiv:2509.03718, ApJ1005 144 (2026): 최신 low-ell/작은-mask 비교 배경, mandatory acquisition은 아님.
- Cayuso–Johnson–Mertens, arXiv:1806.01290; Krywonos et al., arXiv:2607.16071: remote-field response와 현재 pSZ non-detection의 구분.

문헌은 primary arXiv/저널 페이지로 확인했다. SciSpace는 discovery에 사용했으며 metadata 오류나 ingestiondate를 출판정보로 복사하지 않았다. 유도된 결과의 최초성·게재승인은 아직 확정하지 않았다.
