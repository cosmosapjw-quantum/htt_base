# Pruning·cleanup 계획

작업용 데이터베이스와 활성 코드의 삭제 판단을 구분한다. 이곳의 증명 DB는 작업 공간 자동 정리 후 이미 없었으므로 새로 삭제한 증명 파일은 0개다. 코드 DB의 57 transport 조각·실패한 임시 파일을 정리했고, 코드/파일 목록을 저장한 뒤 10,820,591,616-byte 작업용 SQLite도 제거했다. 게시 저장소·사용자 local 원본·원본 Release ZIP은 건드리지 않았다.

## 지금 정리할 대상

| 대상 | 조치 | 근거/완료 조건 |
|---|---|---|
| 작업용 DB·검증된 다운로드 임시본 | 이번 준비 공간에서 제거 | hash 검증·전체 스캔·인덱스 보존·고정 원본 복원 가능 |
| `htt/README.md`의 옛 active 현황, core docstring | 현행 설명으로 수정 | 현재 ownership/runtime과 일치; 과거 이력은 Git 보존 |
| `htt/test_ownership_freeze.py`의 낡은 허용 목록 | 테스트 분류 수정 | 실제 유효 packaging/test 파일을 삭제하지 않음 |
| 새 분석에서의 broad figure driver 호출 | 선택적 수치 분석 entrypoint로 이전 | CMB-only 요청이 DESI/CF4 longrun을 실행하지 않음 |
| 중복 raw/compact/full/binned 분석 factor | 분석 graph에서 중복 사용 제거 | 파일 삭제와 다름; 같은 source lineage와 변환 확인 |
| 확인된 local build/cache | exact allowlist로 조건부 제거 | 실제 존재·현재 미사용·재생성 가능·미커밋 사용자 파일 아님 |

## 새 분석 경로에서 제외할 해석

- `normalize_spectrum().sigma` proxy를 원래 비대칭 likelihood로 간주하는 해석.
- 빠진 오차/bestfit를 0으로 채우고 정상 관측으로 사용하는 경로.
- ACT 단일 tracer 대각 오차를 전체 실험 joint covariance라고 부르는 경로.
- CF4 reconstruction query 행을 서로 독립인 raw galaxy velocity로 취급하는 경로.
- 나열된 scalar reference·compact 중복·같은 sky map을 독립 표본으로 추가하는 경로.
- heuristic feature-support score를 실제 물리 response/likelihood로 바꾸는 해석.
- squared pseudoinverse 값을 정의역 검사 없이 새 gauge로 사용하는 경로.
- 기존 F/Pi/G_F 정의를 새 tensor 정의와 이름만으로 동일시하는 경로.

이 해석들을 새 consumer에서 제외하되, 과거 함수·artifact를 삭제하거나 역사적 수치를 다시 쓰지 않는다.

## 당장 삭제하지 않을 대상

`htt/src/common`은 활성 공유 구현이다. `htt/__init__.py`, `htt/htt/__init__.py`와 workspace contract wrapper는 실제 identity 호환 경로다. 오래된 `evidence_models_R03a`에는 동적 transfer 소비자가 있다. rank/whitening 구현들은 support 정책이 서로 달라 단순 중복이 아니다. scalar/axis/tensor 알고리즘도 다른 추정량이며 파일 수가 많다는 이유로 합칠 수 없다.

원본 관측 데이터, raw와 compact의 원본-파생 계보, immutable proof/decision 근거, 실패한 CAS/runtime 기록, R8/R9와 OUTCOME_UNKNOWN, frozen context, 원본 ZIP, 기존 Bianchi/native source·stub, 설치된 도구와 vendor archive는 보존한다. 타입 의존 연구를 주 경로에서 제외하는 결정은 그 코드의 삭제 허가가 아니다.

## 나중에 검토할 대용량 정리

`docs/project_catalog/database`의 압축 transport는 약 2.35GB다. 별도 승인된 작업에서 versioned release/object store로 옮기고 다운로드·독립 복원을 검증한 뒤 working tree 중복을 제거할 수 있다. manifest·query·build 도구는 남긴다. 일반 commit으로 파일을 제거해도 과거 Git object 용량은 줄지 않는다. `filter-repo`, force push, history rewrite는 이 계획에 포함되지 않는다.

관측 compact 파일의 물리 삭제는 실제 대체 경로·현행 호출자·동등성·복구본을 확인한 이후에만 제안한다. 지금은 canonical 분석 표현 하나를 선택해 계산·메모리 중복을 줄이는 것으로 충분하다. DESI 대용량 배열은 bounded chunk와 필요한 열만 읽고, raw 데이터를 agent별로 복사하지 않는다.

각 cleanup 작업은 `대상 exact path → 사용 근거 → 대체 consumer → dry-run 목록 → 동등성/참조 검사 → 변경 → 복구 확인`을 기록한다. 실행하지 않은 후보는 `NOT_EXECUTED`로 남긴다. 사용자 dirty/untracked를 정리하거나 `git clean/reset --hard`로 상태를 맞추지 않는다.
