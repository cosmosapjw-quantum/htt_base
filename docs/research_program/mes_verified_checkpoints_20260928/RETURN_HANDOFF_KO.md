# HTT/MES I1·I2 checkout 통합 반환

2026-09-28. Owner: HTT research archive integration. 작업 전 기준 `main` commit `18bf3e09a677730280481917211ac1149178cae5`, tree `0a132de06c561459ee691274e7f2ca334d56ef8e`. I1·I2 등록 내용을 게시한 `main` commit은 [`ddf13fdc834c50c350a9d15d08321f0ee945065c`](https://github.com/cosmosapjw-quantum/htt_base/commit/ddf13fdc834c50c350a9d15d08321f0ee945065c), tree는 `922663022d76caf5e580d0605aea9c9ad2fd8ca5`다. 이 반환 문서를 완성하는 후속 commit의 SHA는 그 commit 안의 파일에 자기 참조로 기록할 수 없어 최종 응답의 고정 URL에서 확인한다.

등록 경로는 이 폴더의 `I1/`과 `I2/`이다. 원본 683/19, 합계 expected 702, stage 추적 702, 원본 byte size/SHA-256 동일 702, Git blob 동일 702, missing 0, changed 0. [702행 출처 매핑](provenance/SOURCE_TO_REPO.json), [통합 결과](integration/INTEGRATION_REPORT_KO.md), [읽기 안내](README_KO.md)를 참조한다.

검증 범위와 실제 결과: 원본 전체 ZIP과 내부 ZIP 크기·SHA-256·CRC 통과; 702개 source/worktree/index 크기·SHA-256·blob ID 일치; 등록 commit tree의 702개 blob ID도 원본과 일치; 새 상대 링크 41개 통과; strict DAG 211개 유효; canonical mirror와 replan 검증 PASS; DAG harness 42 passed; 새 문서·DAG staged diff check PASS. 원본 스냅샷의 역사적 CRLF/끝 공백은 원본 바이트 유지 때문에 수정하지 않았다.

`git push origin main`은 `18bf3e09..ddf13fdc main -> main`으로 성공했다. `git ls-remote origin refs/heads/main`이 위 commit을 반환했고 GitHub commit API의 tree가 위 tree와 일치했다. GitHub contents API의 I1 `TARGET_RESPONSE_THEORY_KO.md` blob `077beba210345296cbb1dde0390e49c51fa88aac`, I2 `PHYSICAL_RESIDUAL_AND_IDENTIFIED_SET_KO.md` blob `96405e7f0ebbd60133ba7840f774e42cea77de82`가 원본 매핑과 일치했다. 전체 재다운로드·새 clone/worktree는 수행하지 않았다.

원본 Release `htt-mes-full-handoff-20260928`의 전체 ZIP은 기존 검증·보존 상태를 유지한다. 이번 작업에서 두 내부 체크포인트 파일들을 checkout 내 개별 Git 파일로 연결했다. 이 반환 인계는 원본 ZIP이나 백업 3개의 추가 복원·재배포를 뜻하지 않는다.

과학 검증 재실행: **NO**. 과학적 판정 승격: **NO**. I2 `DEFENDED_CONDITIONAL`과 I3 `HOLD_INPUT_INCOMPLETE`, 기존 HOLD 유지. 관련 없는 기존 tracked 변경 7개, untracked 자료, production source 유지.

수락 기준 A–H에서 누락·변경·경로 충돌·링크 오류·게시 차단은 없다. 완료 조건인 원문 702개 등록, 원본 동일성, 현재 인계 연결, 원격 게시는 모두 충족했다. 미완료 blocker: 없음.
