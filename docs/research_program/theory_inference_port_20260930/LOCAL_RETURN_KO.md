# 관측 분석 직전 반환 인계

- 게시 통합: 기존 `main`을 `origin/main` `bc45fb9292a4cfb095d7b61d4e5c02a32fb39c5c`으로 fast-forward. 초기 사용자 수정 4개와 미추적 경로를 보존했고 새 worktree/clone은 만들지 않았다. 보존 원문 66개 SHA-256 일치.
- 이론 코드: 지정 공통 테스트 29개 통과. `-+++`, `u=U/c`, U/O와 U/N, 기존 `x,Q,Pi,F,G_F` 정의 경계는 원문 매핑 범위로 유지한다.
- 로컬 CAS: Wolfram Engine 15.0+xAct xTensor 1.3.0, SymPy 1.14.0, Sage 10.9+Singular 4.3.2, Lean 4.31.0+Mathlib을 실제 실행했다. CAS-07과 CAS-09의 유한 부분 명제만 확인했다. 나머지 10개 의무와 CAS-09 covariance의 Lean/Singular 범위 등은 HOLD. 전체 `CAS_4AXIS_PASS`나 과학적 판정은 없다. 정확한 입력·출력 해시는 [engine_matrix.json](local_execution/engine_matrix.json)에 있다.
- HTT 추론 코드: 지정 신규·기존 회귀 테스트 47개 통과. 합성 fixture는 13 자유 계수와 dense covariance를 사용했고 최대 복구오차 1.46e-12 < 1e-8, 실제 자료 사용 없음. DAG 212개 유효, mirror 일치. 과거 PR254 suite는 별도 8실패·5통과이며 authority/fixture 불일치를 수정하거나 science status를 올리지 않았다.
- 독립 리뷰: 전역 reviewer 등록이 `HARNESS_REGISTERED_ASSIGNMENT_REQUIRED`로 실패했다. 기존 게시물의 독립 검토와 이번 로컬 실행의 독립 검토를 구별한다. 현재 실행은 `PRE_DATA_IMPLEMENTATION_TESTED_REVIEW_HOLD`.
- 실제 분석 전 필요: 이번 실행의 독립 리뷰, 미완료 CAS 의무, 고정 독립 d_A/선택 또는 공동 오차법칙, finite-distance remainder, covariance/null/calibration, 물리적 source congruence와 법선·미분 입력. I2 `DEFENDED_CONDITIONAL`, I3 `HOLD_INPUT_INCOMPLETE`, BIC-07 HOLD, 실제 tilt/Bianchi 판정 NOT_RUN. 관측 카탈로그 적합·다운로드·solver 실행은 하지 않았다.

기계 판정과 파일 해시는 [LOCAL_RETURN.json](LOCAL_RETURN.json), 원시 엔진 로그는 `local_execution/engine_artifacts/`에 있다.
