# GR-CAS-01 로컬 순차 검증 반환

상태는 **불완전 증거 보존**이다. 네 축의 독립 실행 결과 파일은 모두 동일 계약 해시 아래 유한 성분 C01-C04를 PASS로 기록하고 최종 소스 해시와 일치한다. 그러나 실제 `run-adjudicate` 집계는 Wolfram 작업 디렉터리와 Sage 인터프리터 설정 실패 때문에 `CAS_CONFLICT`이며, Wolfram과 Sage가 `INCONCLUSIVE`이다. 수학적 반례는 발견되지 않았지만 `CAS_4AXIS_PASS`는 성립하지 않았다.

독립 검토는 이 불완전 상태를 명시하여 게시하는 것에 한해 `PASS_WITH_FINDINGS`를 반환했다. 집계 실행 설정, Lean lifecycle 종료 영수증 부재, 일부 개발 실패 raw의 불완전 보존이 남아 있다. 이것들은 유한 성분의 독립 결과를 반증하지 않지만 전체 네 축 완료를 허용하지 않는다.

따라서 다음 경계를 유지한다.

- 유한 성분: 네 개의 standalone PASS envelope와 현재 소스 결합을 보존한다.
- 네 축 집계: `NOT_PASSED`; 다수결이나 standalone 결과로 승격하지 않는다.
- 전체 해석적 증명: `HOLD_NOT_ESTABLISHED`.
- 물리·관측 적용과 과학적 admission: `HOLD_NOT_ESTABLISHED` / false.
- 남은 해석 의무: Jacobi vertex Taylor order와 screen invariance의 ODE 증명, smooth timelike neighborhood/local flow/source extension.

C01은 v4 채택이 확인되지 않아 해당 의존 범위만 HOLD이다. C02/C03는 새 수학 finding이 없어 재실행하지 않았다. C04 launch `cl_000fce20034122657b6cdf509703df23`와 R9는 변경하지 않았다. 다음 독립 실행 후보는 DAG상 GR-CAS-05이다.

게시 commit과 R1 원격 ref는 push 뒤 별도 영수증으로 보고한다. 이 문서는 과학적 claim-bearing 결과가 아니다.
