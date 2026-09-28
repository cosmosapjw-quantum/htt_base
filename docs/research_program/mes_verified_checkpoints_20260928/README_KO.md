# HTT/MES I1·I2 검증 체크포인트 읽기

2026-09-28. Owner: HTT research archive integration. 범위는 원문 702개 파일의 바이트 동일한 Git 등록과 현재 인계 연결이다. 이 폴더의 `I1/`, `I2/`는 역사적 스냅샷이므로 내부 절대경로와 지시를 현재 작업 지시로 해석하거나 활성 코드·하네스에 설치하지 않는다. 현재 저장소 정책은 [AGENTS.md](../../../AGENTS.md)와 [canonical DAG](../../codex_handoff/pr_backlog.yaml)를 따른다.

## 읽기 순서

1. I1 [target response 이론](I1/integration_i1/TARGET_RESPONSE_THEORY_KO.md), [코드·이론 통합](I1/integration_i1/CODE_THEORY_INTEGRATION_KO.md), [독립 판정](I1/integration_i1/INDEPENDENT_DECISION.json), [독립 검토](I1/integration_i1/INDEPENDENT_REVIEW.md), [상태](I1/integration_i1/state/), [검증 근거](I1/integration_i1/verification/)를 읽는다.
2. I2 [physical residual과 identified set](I2/integration_i2/PHYSICAL_RESIDUAL_AND_IDENTIFIED_SET_KO.md), [독립 판정](I2/integration_i2/INDEPENDENT_DECISION.json), [독립 검토](I2/integration_i2/INDEPENDENT_REVIEW.md), [상태](I2/integration_i2/state/), [검증 근거](I2/integration_i2/verification/)를 읽는다.
3. 현행 후속 연구는 이미 등록된 [I3 Gaia-CRF3 screening](../mes_i3_gaia_screening_20260928/REPORT_KO.md)과 그 [검증 기록](../mes_i3_gaia_screening_20260928/VALIDATION_KO.md)을 읽는다. I2의 [I3 다음 프롬프트](I2/HTT_MES_I3_NEXT_PROMPT_20260928_KO.md)는 당시의 역사적 계획이다.
4. 바이트 출처와 모든 Git 경로는 [702행 원본→저장소 매핑](provenance/SOURCE_TO_REPO.json), 실행 결과와 범위는 [통합 보고서](integration/INTEGRATION_REPORT_KO.md), 게시 결과는 [반환 인계](RETURN_HANDOFF_KO.md)를 확인한다.

## 출처와 판정 경계

원본은 GitHub Release `htt-mes-full-handoff-20260928`의 `HTT_MES_LOCAL_CODEX_FULL_20260928.zip`이다. 전체 ZIP SHA-256은 `740658f22e9a60be5cbefcd2ea4d6e8725f1f35585a96b02a2d845071d1af672`이며, [원본 archive 검증](../mes_full_handoff_20260928/VALIDATION_KO.md)에서 별도로 보존·복원 범위를 기록했다. I1 체크포인트 683개와 I2 체크포인트 19개만 이 디렉터리로 추출했다. 원본 백업 3개와 대용량 catalog·DB는 여기에 두지 않았다.

I1은 target response와 residual-known inverse의 조건부 이론, 코드 연결, 실패·검토 이력을 담는다. I2는 radiation-only, Λ=0, geodesic-normal Bianchi I의 제한된 branch를 다룬다. 두 독립 판정의 `DEFENDED_CONDITIONAL`은 실측, 일반 finite tilt Einstein–matter, native solver 또는 Bianchi family 식별로 확장되지 않는다. I3는 `HOLD_INPUT_INCOMPLETE`다. 이번 통합에서 과학 계산·CAS를 재실행하거나 판정을 승격하지 않았다.

`I1/harness/research/`와 스냅샷 내부 코드·과거 명령은 연구 당시의 근거다. 현재 활성 하네스와 production source는 기존 저장소 위치를 사용한다. 스냅샷 문서의 과거 `/home/...` 경로는 이 안내의 `I1/`·`I2/` 상대경로로 찾아간다.
