# HTT post-review research: from morphology to quantitative identification

2026-09-07 — MAIN research pack, not a new observational result.

## 이번에 얻은 결론

두 모의심사의 핵심 문제 제기는 유효하다. 완성된 교육용 보고서와 독창성·검출력·실제 데이터 근거를 갖춘 연구논문은 다르다. 그러나 제안서의 모든 수치와 해석을 그대로 받아들이지는 않는다. 기존 artifact 완료 상태는 보존하고, 새로운 연구를 **관측 morphology → 명시된 nuisance 아래의 정보 → 독립적인 redshift/frame response**라는 세 단계로 재구성한다.

실제로 진행한 수학은 다음과 같다.

- 기존 exact axial certificate로 최소 full-rank cutoff가 L=10임을 유도했다. 일반 방향에 대해서는 다항식 논증으로 거의 모든 방향의 full rank를 얻지만 모든 방향 또는 수치 안정성으로 과장하지 않는다.
- 이상적인 spherical STF3 null에서 boost projection fraction의 Beta(3/2,2) 분포와 LS covariance를 유도했다. 제안서의 예시 입력으로 RMS는 0.88235–0.88785이며, 0.8435와 일치하지 않는다. 이것은 실제 속도 추정이 아니다.
- 명시된 1차 radiation model에서 배경항을 먼저 소거해 더 강한 shear/vorticity 부등식을 얻었다. STF derivative contraction의 sharp norm은 sqrt(7/5)다. 일반 MES 전체나 all-observer 전제를 관측으로 증명한 것은 아니다.
- bounded nuisance의 최소 비용, 두 admissible 상태를 비교할 때의 2R 인자, Gaussian marginalisation과 같은 데이터의 high-mode conditioning을 분리했다.
- soft-mask family에서는 거의 모든 nonzero mask amplitude에서 algebraic full rank가 유지돼도 nuisance norm은 O(epsilon), covariance는 O(epsilon squared)로 줄어드는 정리를 유도했다. 무제한 nuisance no-go와 실제 정보 손실은 같지 않다.
- redshift bin 수를 늘려도 free shell velocity와 observer shift의 gauge가 사라지지 않는 예, radial-only rigid rotation의 정확한 null을 제시했다.
- 기존 bulk-flow likelihood의 selection/precision weight 혼동, active row 수와 design rank의 혼동, finite-null score의 NaN 처리 위험을 source 수준에서 찾아 후속 회귀 입력과 정답을 지정했다.

## 문서

| 파일 | 산출물 |
|---|---|
| [REVIEW_ADJUDICATION.md](REVIEW_ADJUDICATION.md) | 심사·제안의 채택/수정/거부와 근거 등급 |
| [THEORY_RESULTS.md](THEORY_RESULTS.md) | T1–T10 정의·전제·유도·계산형·한계 |
| [CODE_DATA_REUSE.md](CODE_DATA_REUSE.md) | 실제 repo 구조/branch 조사, 재사용 모듈과 보호할 legacy lane, 첨부 asset inventory의 데이터 역할 |
| [IMPLEMENTATION_CONTRACT.md](IMPLEMENTATION_CONTRACT.md) | 이미 결정한 함수/통계 계약과 아직 MAIN에서 닫아야 할 세 가지 과학적 선택 |
| [THEORY_FIRST_DAG.yaml](THEORY_FIRST_DAG.yaml) | 이론 우선, 이후 한 Codex campaign의 의존성 |
| [REGRESSION_ORACLES.json](REGRESSION_ORACLES.json) | 구현이 따라야 할 명시적 반례·입력·정답. Native PASS 기록은 아님 |

## 실제 검증 범위

기존 보고서의 source/certificate와 이번에 읽은 code가 입력이다. 새 T1–T10은 직접 유도다. Beta tail, LS RMS와 monopole beta-squared scale은 web calculator로 검산했다. Python/container는 실행 전 ClientError, Wolfram context/evaluator는 MCP/SSE404였으므로 새 native tests·CAS·Monte Carlo·data run은 없다. 리뷰어가 언급한 sandbox ZIP와 대규모 재현 수치는 실제 원 파일/실행 근거를 취득하기 전까지 reviewer-reported다.

Repository default의 현재 commit은 50ea6d76ace70dec57b8794ab0d1cf9b8fab42cb로 읽었다. Root/global structure와 complete common subtree, 관련 donor branches 및 핵심 코드 본문을 조사했다. 모든 historical 파일 본문이나 로컬 1.5 TB를 전수 실행/해시한 것은 아니다. 첨부 자산조사는 metadata이며, FFP10 path 수를 independent simulation 수로 읽지 않는다. PR4 dedicated directory, posterior samples, lensing simulation, correlated velocity reconstruction의 역할도 구별했다.

새 branch는 accepted pedagogical artifact 9c86759f4ac7054d01d88689290a658e8ffd5863에서 분리했다. 코드 audit 기준 default commit과 연구문서 base는 서로 다른 identity다. 기존 source, PDF, receipt, canonical ledger와 scientific branch ref는 변경하지 않는다. 새 파일은 연구 pack뿐이다.

## 다음 순서: 지금은 전체 Codex 데이터 실행을 시작하지 않는다

```text
심사 비판 + T1–T10 + 실제 코드/데이터 역할 조사 [이번 산출물]
                         |
               +---------+---------+
               |                   |
     M1 CMB joint model      M2 redshift physical likelihood
               |                   |
               +---------+---------+
                         |
             M3 finite experiment/calibration
                         |
           MAIN THEORY_FREEZE + complete handoff
                         |
          Codex integration / implementation
                         |
       synthetic verification + selected asset intake
                         |
        frozen observed analysis and robustness runs
                         |
            non-force Git return -> MAIN review
```

현재 M1/M2/M3는 미완이다. 모델·foreground/null law·survey likelihood·primary statistic을 Codex가 임의로 결정하게 하지 않기 위해 남은 과학적 선택을 명시했다. 다음 MAIN 작업은 **M1: 실제 PR3 제품/처리/low-high covariance/null 통계의 닫힌 계약**이다. M2는 CF4/거리/selection/frame law와 진짜 식별가능한 redshift functional, M3는 이 둘의 최종 실험과 calibration을 고정한다. 이 세 작업을 끝내면 implementation부터 데이터 분석까지 한 번의 Local Codex campaign으로 넘긴다. 전체 우주론 연구가 끝날 때까지 무한정 미루는 gate가 아니라, 이 유한한 campaign의 과학적 선택을 먼저 닫는 것이다.

DAG의 requires는 성공 경로 의존성이다. 어떤 local 단계에서든 진짜 scope/runtime/input boundary로 종료되면, 후속 observed 분석을 실행하지 않고 현재까지의 실제 실패/부분 결과를 동일한 Git-return 경로로 반환한다. 실패 때문에 반환이 C4 성공을 기다리는 구조가 아니다. 동일 범위의 일반 코드 결함은 수정·재검증하며, 과학적 의미를 바꿔야 할 경우만 MAIN에 반환한다.

## 정책 경계

MAIN↔Local Codex, single source writer, Git-first handoff와 실제 결과, 유연한 planning budget 및 누적 사용량을 유지한다. 추가 work 스레드, 반복된 무의미한 감사, 데이터 전체 재다운로드는 만들지 않는다. 현재는 새 production 코드/데이터 실행을 허가하는 handoff가 아니라 그 이전 이론 연구 산출물이다.

기존 29쪽 R3와 55쪽 교육용 보고서는 완성 artifact로 유지된다. 이번에는 더 강한 연구 결과와 실증 방법을 만드는 새 단계다. Canonical T9 v4/30, 원 core candidate 40, PR284 deferred, finite-HEALPix unresolved와 CF4 quarantine는 자동 변경하지 않는다. 기존 scalar-MES observational headline을 복원하거나 native BASS/REC/REI solver를 구현하지 않는다. Merge·ready·공개 배포·관측적 발견·과학적 승격은 이 pack의 게시로 승인되지 않는다.
