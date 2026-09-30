# GR·통계 연구 결과의 저장소 통합과 CAS 재검증

2026-09-30. 이 문서는 이번 저장소 반영의 시작점이다.

## 현재 상태

- 원래 연구 묶음 39개 파일을 바이트 변경 없이 보존했다. `publication/SOURCE_TO_REPO.json`에 출처와 저장소 경로·SHA-256·Git blob을 기록했다.
- `REPORT_KO.md`, `DECISIONS.json`, 세 독립 검토 기록은 당시의 분석적 유도와 제한을 보존한다. 45개 조건부 분석 판정과 1개 HOLD는 새로운 정리 45개 또는 CAS 검증 완료를 뜻하지 않는다.
- 원본 `RESEARCH_HANDOFF.json`의 `repository_modified: false` 등은 연구 회차 당시의 이력이다. 현재 저장소 통합 상태는 이 문서와 `publication/` 기록을 따른다. 원본 이력을 덮어쓰지 않았다.
- 네 축 CAS는 이번 게시에서 실행하지 않았다. 기존 경량 Wolfram 결과는 과거 계산 근거이며 xAct·SymPy·Sage/Singular·Lean 교차검증으로 재분류하지 않는다.
- 원문 PDF, 추출 전문, 데이터베이스, 실행환경, 관측 데이터는 추가하지 않았다. 수학 명세와 원문 identity만 전달한다.

## 읽는 순서

1. 실행 담당: `LOCAL_CODEX_PROMPT_KO.md`, `cas/EXECUTION_INDEX.json`, 각 task의 `cas/contracts/` 계약.
2. 연구 해석 담당: `REPORT_KO.md`, `DECISIONS.json`, `reviews/`의 최종 판정. 후보 문서의 pending 표기는 작성 시점의 기록이다.
3. CAS 축 작성자: 공통 계약과 명시적으로 허용된 중립 명세만 읽는다. 연구 증명 본문·기존 Wolfram script/result·다른 축 산출물은 판정 전 읽지 않는다.
4. 반환 담당: `LOCAL_CODEX_RETURN_SCHEMA.json`과 `LOCAL_CODEX_RETURN_PROMPT_KO.md`.

## 기존 코드와의 관계

부모 커밋 `bc45fb9292a4cfb095d7b61d4e5c02a32fb39c5c`의 supplied-input 이론·추론 모듈은 유지한다. 이 변경은 새 유도 결과를 생산 코드에 자동 이식하거나 기존 함수의 의미를 바꾸지 않는다. 특히 geodesic 전용 inverse와 가속도를 허용하는 joint inverse를 같은 함수로 취급하지 않는다. 이전 이식 handoff는 `../theory_inference_port_20260930/`에 있다.

TEFF는 제공된 문헌의 이름이다. 이번 entropy/moment 명제의 연구상 활용은 `tsc_legacy`를 새로운 과학 모듈의 소유자로 복구하는 결정이 아니다. 추후 구현 시 공통 물리 계약은 `common`, 관측 feature는 `obsstat`, 추론은 `htt`, 진단은 `mio`의 기존 경계를 따른다.

## 검증 범위

각 CAS task는 finite algebra, 해석적 extension, 보류 문제를 구별한다. 유한 차원 항등식의 네 축 통과가 local existence, 무한 차원 적분 부등식, 통계 coverage 또는 원전 우선권 전체의 증명을 대신하지 않는다. 각 계약은 실제로 닫을 수학적 성분을 적고, 바깥의 해석적 의무를 남긴다.

`CAS_4AXIS_PASS`는 동일 계약 hash에 묶인 네 축을 현재 runner가 실제 실행해 관찰했을 때만 사용한다. `preflight` 또는 저장된 JSON inspection은 과학적 통과가 아니다. Lean에는 진술의 충실성과 kernel proof, Wolfram에는 실제 xAct 사용이 필요한 tensor 의무, Sage에는 명시된 Singular 의무를 별도로 확인한다.

모형 독립성은 특정 Bianchi type과 진화 solver를 선택하지 않은 국소 조건부 명제의 의미다. 추가 미분·보정·orbit normal을 실제 관측에서 확보했다는 뜻이 아니다. 기존 R9 실패·OUTCOME_UNKNOWN·배정 예산과 I2/I3 HOLD, novelty와 관측적 수락 상태는 유지한다.

## 완료 조건과 다음 작업

이번 게시의 완료 조건은 원문 보존, 실행 가능한 인계 문서, DAG·mirror 일치, 범위 검토, 비강제 원격 게시 확인이다. local CAS 완료 조건은 각 계약의 실제 네 축 결과와 판정 기록이다. 이후 코드 이식과 CF4/Union3 관측 분석은 별도 작업이며 이번 CAS 지시에는 포함되지 않는다.

되돌리기는 해당 문서 게시 커밋을 revert하는 방식이다. 데이터 migration은 없으며, 이후 의존 작업이 생기면 이를 먼저 확인한다.
