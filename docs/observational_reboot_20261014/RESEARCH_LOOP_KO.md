# Reboot 이론·코딩 연구 루프의 실행 기록

physmath-research-loop 1.3.0과 현재 repo의 물리·통계·claim·figure·DAG 규약을 적용했다. 이번 단위는 **legacy 재독 → 통계와 물리 반응의 계약 → 실행 가능한 코드와 실제 조건부 pilot → 전체 캠페인 인계**다. 아래의 10단계 기록은 이 단위에 관한 것이며, 전체 관측 모형이나 native Bianchi 연구의 완료를 뜻하지 않는다.

## 이론 R1–R10

| 단계 | 실제 작업과 근거 | 판정 범위 |
|---|---|---|
| R1 질문·계약 | 기준 HEAD b2af 확인, legacy 재시작과 모든 실행 가능한 분석이라는 사용자 목표 반영 | morphology 검정, dipole와 local/global 구별, 조건부 family 경로 |
| R2 근거·재사용 | 36쪽 compendium 전체와 실제 legacy PPC/K1/lnB 보고서 재독. SciSpace 1회, Exa 7검색·4fetch, 9개 primary source 및 추가 Planck source 감사 | PRIMARY_SOURCES, SOURCE_INPUTS, 절별 legacy 검토. 전체 corpus를 읽었다는 주장은 없음 |
| R3 주장·전제 | PPC, finite rank, Pi, power-index와 C_l/D_l, 물리 tensor와 온도 tensor를 구별 | 역사적 숫자의 자동 승계 방지; normalization 충돌 명시 |
| R4 표현 탐색 | endpoint Lorentz, intrinsic dipole와 lensing 대안, nuisance quotient, depth response, 결정론적·공분산 family 경로 구성 | 실제 후보식과 식별 가능한 질문 |
| R5 유도 | boost Q→dipole/octupole, STF Gram, 두 shell의 rank, common-sky covariance, 제한된 Bianchi I history | THEORY_REBOOT의 명시 전제 아래 유도; 새 strong no-go 없음 |
| R6 독립 검증 | fresh-context reviewer가 부호·단위·통계·코드·그림 검토 | 최종 범위는 review/INDEPENDENT_REVIEW.md에 기록 |
| R7 계산 확인 | NumPy tensor 잔차 약 1e-15, rank 3→6; Wolfram exact projector와 information 2, 26/49; 실제 signal+noise pilot | 경량 대수·실행 근거. 다축 CAS 인증이 아님 |
| R8 결과 판정 | 새 finite rank는 전달 시뮬레이션에 조건부이며 retrospective | 물리적 식별에는 해당 provider가 필요. 막힌 경로 외 분석은 계속 |
| R9 계산 계약 | source/frame/units/response/covariance/nuisance/remainder, 고정 score와 training/calibration JSON | 23개 task, 9개 goal, 20개 추가 기회에 연결 |
| R10 보존·재개 | 결과·source·실패·다음 명령·복사용 handoff와 push | 과학적 수용과 저장소 공개 상태를 구별 |

## 코딩 C1–C10

| 단계 | 실제 작업과 근거 | 판정 범위 |
|---|---|---|
| C1 baseline | 깨끗한 b2af, 기존 checkout, 현재 runtime 확인 | 이전 61448 handoff 이후 추가된 코드 재사용 |
| C2 식↔코드 | finite_null_ranking, nuisance_rank, OLS geometry, gated cache 경로 검토 | 기존 core에 필요한 CLI와 검증 추가 |
| C3 수치 설계 | 알려진 SPD 공분산 whitening, nuisance 열 정규화, joint max rank, CP-q, 300쌍의 60/240 분리 | 추정 공분산 역행렬을 exact chi-square로 해석하지 않음 |
| C4 DAG·자원 | 실제 3개 worker와 별도 reviewer, production writer 1명, 계산 thread 1개 | 23개 PR 카드와 연속 goal 계약. 추가 기회 목록은 계속 확장 |
| C5 구현 | 통계 보정, 실제 SMICA pilot, 식별성 계산, task packet, 결과 기반 보고서 builder | 입력→수치→그림→보고서 실행 경로 |
| C6 테스트 | 24개 서로 다른 targeted test 통과. 최초 gate identity 실패와 수정 회귀 보존 | local pytest 부재는 remote 실행으로 해결 |
| C7 과학 검증 | 정확한 동점 rank, CP coverage, 종속 feature의 max, 학습 누출 거부, signal+noise cross term, OLS oracle와 단위 변경 | 선언한 통계 절차와 대수 검증. 실제 우주 귀무법칙의 수용은 별도 |
| C8 수치·재현 | source-bound pilot 약 16초, 저장 feature로 그림만 재생성, OLS identity 잔차 약 2.1e-15 | 실제 source cache hash 확인. 새로운 full-resolution simulation 실행은 없음 |
| C9 독립 검토 | 그림 제목 잘림과 nuisance 열 단위 문제 발견·수정·대상 회귀 확인 | 하나의 검토 pass와 구체적 결함 수정 |
| C10 인계 | DAG와 mirror 검증, coherent commit/push, goal queue와 다음 packet | 후속 캠페인은 pending. 이번 RB00만 범위를 한정해 완료 |

## 정책 교정과 열린 의무

- noise 지도 사이의 공간상관만으로 simulation 간 의존을 판정하지 않는다. Planck release의 독립 noise/systematics 설명과 실제 관측의 교환가능성은 서로 다른 근거다.
- 옛 `/mnt/sn850x2t/...` 경로 부재는 자료 전체의 부재가 아니다. 현재 `workdir/raw/planck_ffp10` alias에서 실제 IQU source와 K_CMB 단위를 확인했다.
- 과거 대규모 audit protocol을 모든 단계의 재귀 review로 확대하지 않았다. 현재 범위의 물리·수학, 코드·수치, 그림을 한 번의 독립 검토에 포함했다.
- NG1–NG7을 충족하는 새 strong no-go 주장은 없다. 특정 선형 반응의 rank 손실은 해당 모형의 결과다. Wolfram과 NumPy 확인을 다축 CAS나 native atlas 인증으로 승격하지 않는다.
- 다음 연구는 처리·선택·공분산·물리 반응·누락 모드·remainder를 실제 관측 법칙으로 연결하는 일이다. 추가 metadata나 기존 proof의 반복으로 그 입력을 대체하지 않는다.
