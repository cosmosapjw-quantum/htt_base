# 이론 및 관측 분석 전 추론 코드 이식

2026-09-30. 기준 `main`: `efbd6d39b1167afcf40f3d07af0b5552747f3611`.

이번 변경은 누적 이론을 실행 가능한 **입력이 주어진 경우의 수학 함수**와 **관측 분석 전 조건부 추론 코드**로 이식한다. 실제 카탈로그 적합, 추가 데이터 다운로드, Boltzmann/ODE/PDE solver 실행은 포함하지 않는다. 기존 702개 체크포인트와 Loop 2 게시 이력은 원격 기준 tree에 그대로 남는다. 두 최신 연구 묶음의 manifest에 포함된 모든 원문 및 필요한 이전 코드 계획을 바이트 동일하게 보존했다. 전체 대화 첨부를 새로 획득하거나 거대 DB 전체를 다시 읽었다는 의미는 아니다.

## 읽는 순서

1. [LOCAL_CODEX_PROMPT_KO.md](LOCAL_CODEX_PROMPT_KO.md): 현재 실행 지시. 과거 원문 안의 데이터 pilot 지시보다 이번 사용자의 이론 우선·분석 직전 범위를 적용한다.
2. [PORT_MAP.json](PORT_MAP.json): F1–F7, BIC, TBO 결과별 구현 함수·가정·미구현 입력.
3. [LOCAL_TASKS.json](LOCAL_TASKS.json), [CAS_CONTRACT.json](CAS_CONTRACT.json): 로컬 실행 순서와 엔진별 의무.
4. [VALIDATION.json](VALIDATION.json), [SYNTHETIC_FIXTURE.json](SYNTHETIC_FIXTURE.json), [독립 검토](implementation_review/INDEPENDENT_REVIEW.md): 이번 코드 검증의 실제 범위.
5. [SOURCE_TO_REPO.json](SOURCE_TO_REPO.json): 새로 보존한 원문과 기존 저장소 체크포인트의 연결.
6. [CLEANUP_PLAN.json](CLEANUP_PLAN.json): 보존·대체·향후 정리 구분. 이번 게시에서 삭제는 없다.

## 구현 범위

| 계층 | 추가한 계산 | 입력 또는 한계 |
|---|---|---|
| COMMON | 상대운동, redshift intercept, Hubble tensor lift, curvature clock | U/O와 U/N 구분; 정확한 입력과 분리된 고유값 필요 |
| COMMON | 전체 velocity jet의 expansion/shear/vorticity/acceleration | 속도값만으로 미분량을 만들지 않음 |
| COMMON | Codazzi flux, 단일 perfect-fluid tilt, orbit curvature, 불변 tensor eigenframe | 균질성·물질 성분·법선·미분 입력은 별도 전제 |
| COMMON | tensor functional, relative body gauge, 부호 있는 support 비율, 공동분포 pushforward | 같은 latent state의 값·기준·body를 결합; undefined 질량 보존 |
| COMMON | ellipsoid quotient/fiber, 유계 유리 polytope support | 일반 비선형 해공간 solver 아님 |
| COMMON | 부호 있는 depth transport와 전체 covariance | 변환된 통계량을 독립 자료로 다시 곱하지 않음 |
| COMMON | P2 stress-gap body, W1 약형 응답 오차 | gap·미분·적분·오차 경계가 실제 제공되어야 함 |
| HTT | 13개 자유 intercept/기울기 계수의 dense GLS 및 정규화 likelihood | 고정 독립 d_A, 알려진 Gaussian covariance, 명시적 remainder |
| HTT | 유한 posterior functional image, 두 상태의 전체 Gaussian 법칙 비교 | posterior 생성·수렴 검증·전역 식별 정리는 별도 |
| MIO | 기존 ratio 함수의 NaN/Inf·overflow 거부 | 기존 유한값 통계 및 소유권 유지 |

통계 계수는 `(zeta0,zeta_x,zeta_y,zeta_z,h0,h_x,h_y,h_z,q_xx,q_yy,q_xy,q_xz,q_yz)`이다. `q_zz=-q_xx-q_yy`; STF5의 Frobenius 정규직교 좌표와 다른 표현이므로 P2 body에 그대로 대입하지 않는다. slope 단위는 km/s/Mpc, 거리는 d_A의 Mpc, redshift/intercept는 무차원이다. 공통 기하 함수는 명시한 단위와 정규화된 `u=U/c`를 사용한다.

기존 DATA-01의 `AVAILABLE` 데이터/공분산 표시는 완전한 관측 likelihood의 적격성을 보증하지 않는다. PR179 방향 cosmography 진단과 legacy pipeline을 물리적 U 또는 N의 추론 코드로 재해석하지 않는다. 새 API는 별도로 호출하며 기존 분석 CLI가 실제 데이터를 자동 적합하도록 바꾸지 않았다.

## 판정 범위

합성 예제는 알려진 tensor jet에서 관측량을 구성하고, 13개 계수를 적합하여 조건부 intercept/slope 역변환을 확인한다. 이 예제에는 별도로 선언한 유한 toy posterior의 undefined 질량 보존 검사가 포함된다. 그 posterior는 GLS 적합에서 생성한 posterior가 아니다.

실제 자료의 finite-distance remainder, 거리 오차와 selection의 공동법칙, 알려진 covariance 또는 그 추정 오차법칙, 물리적 source congruence, 법선/곡률 미분 입력은 아직 공급되지 않았다. `NOT_CALIBRATED`는 실제 calibration을 거치지 않고 바꾸지 않는다. Floating ellipsoid의 `EMPTY_SET`은 명시한 수치 규칙 아래 계산 결과이며, formal infeasibility certificate나 BIC-06의 관측적 배제 증명이 아니다. 유리 polytope exact 결과 역시 선언한 유한 입력 영역에만 적용된다.

I2 `DEFENDED_CONDITIONAL`, I3 `HOLD_INPUT_INCOMPLETE`, BIC-07의 관측→spatial jet 미해결, 실제 tilt/Bianchi 분류 미실행 상태를 보존한다. 이번 Python 테스트 및 독립 코드 검토는 Wolfram+xAct / SymPy / Sage+Singular / Lean/mathlib 네 축의 정식 과학 판정을 대체하지 않는다.
