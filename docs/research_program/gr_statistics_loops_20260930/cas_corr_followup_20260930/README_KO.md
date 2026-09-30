# GRSTAT 정정 반환 후속 인계

1. `FOLLOWUP_REPORT_KO.md`에서 정정 수용 범위와 C04 일반 증명을 읽는다.
2. local Codex에 `NEXT_LOCAL_PROMPT_KO.md`와 이 폴더를 함께 전달한다.
3. 새 실행 대상은 폴더 최상단의 `c04_sympy_certificate.py`, `c04_sage_certificate.py`다.
4. `intake/`는 이번에 실제 열람한 이전 반환의 선택적 원본 근거다. 그 안의 옛 스크립트·PASS·CONFLICT는 새 실행 결과가 아니다. 원 run의 466개 전체를 재수집한 백업이 아니다.
5. `FOLLOWUP_STATUS.json`은 기계 판독 상태, `PREPARATION_CHECKS.json`은 구문·오류경로 검사다. 수학 엔진 실행은 미수행이다. 각 새 소스의 자체 변조 검사는 로컬에서 실행해야 한다.

현재 관측 aggregate는 CAS_CONFLICT이며 과학적 conditional/HOLD는 유지한다. 등록 reviewer 완료 상태도 변경하지 않았다. 이번 묶음은 Git commit/push를 수행하지 않았다.

`ARTIFACT_MANIFEST.json`은 ZIP 안의 나머지 파일 바이트를 기록한다. 경로와 파일명은 압축 해제 위치에 대해 상대적이다. `intake/contracts/CAS13-C04-RELATIVE-MINIMAX.json`의 고정 해시는 두 새 실행 프로그램이 요구하는 값과 같다.
