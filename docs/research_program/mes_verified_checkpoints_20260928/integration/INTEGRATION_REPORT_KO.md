# I1·I2 원문 Git 통합 보고서

2026-09-28. Owner: HTT research archive integration. Claim tier C0 archival/reproducibility; 과학 재심사 없음. 기준 `main` commit `18bf3e09a677730280481917211ac1149178cae5`, tree `0a132de06c561459ee691274e7f2ca334d56ef8e`. 시작 시 `git fetch origin main` 결과 `origin/main`도 같은 commit이었다. 기존 tracked 사용자 변경 7개와 별도 untracked 입력을 보존했다.

원본 전체 ZIP 769,808,802 bytes / SHA-256 `740658f22e9a60be5cbefcd2ea4d6e8725f1f35585a96b02a2d845071d1af672`를 로컬에서 확인했다. 내부 I1 ZIP 8,946,669 bytes / `912210ac85eee1295c20e03b0ecfa0a4bfb198fb3aafbf0f0860f930233be911`, I2 ZIP 39,863 bytes / `f77dc89497450bacae67ad432fc863111c6ec7820b3fc3af2e618e3f05cd745a`를 확인했다. 두 내부 ZIP의 CRC, 경로 이탈, symlink, 중복·대소문자 충돌을 검사한 뒤 해당 두 checkpoint만 추출했다.

| 체크포인트 | 원본 파일 | Git 추적 경로 | byte size/SHA 동일 | Git blob 동일 | 누락/변경 |
|---|---:|---:|---:|---:|---:|
| I1 | 683 | 683 | 683 | 683 | 0/0 |
| I2 | 19 | 19 | 19 | 19 | 0/0 |
| 합계 | **702** | **702** | **702** | **702** | **0/0** |

[파일별 매핑](../provenance/SOURCE_TO_REPO.json)은 각 원본 내부 상대경로, 저장소 경로, 크기, SHA-256과 원본 바이트로 계산한 Git SHA-1 blob ID를 기록한다. 시작 시 현행 HEAD 전체 Git blob 중 I1과 동일한 것은 218/683, I2는 0/19였다. 목적 경로에는 중복 등록 파일이 없었다. 702개 경로를 개별 ignore 검사하고 그 경로만 stage했다. stage 0의 702개 Git blob ID는 원본 계산값과 전부 일치했다. 최종 commit tree와 원격 ref 검증은 [반환 인계](../RETURN_HANDOFF_KO.md)에 기록한다.

I1/I2 안의 원문·실패 기록·과거 후보·독립 검토·상태·검증·GPT-6 하네스는 한 바이트도 고치지 않았다. 활성 production 코드, solver, 원본 DB는 수정하지 않았다. I2 `DEFENDED_CONDITIONAL`, I3 `HOLD_INPUT_INCOMPLETE`, 기존 과학적 HOLD를 유지한다. 이번 검증은 파일 동일성·연결성에만 해당하며 Wolfram/CAS·수치계산과 과학적 판정 재실행은 `NO`다. 예외: 없음.

## 실제 파일 통합 검증

- 로컬 원본 전체 ZIP과 내부 I1/I2를 다시 읽어 702개 원본 바이트의 크기·SHA-256·raw Git blob ID를 계산하고 worktree와 index를 대조: `702/702/702`, 누락·변경·추가 0.
- 새로 작성하거나 수정한 Markdown의 상대 링크 검사: 41개 대상 모두 존재.
- `validate_pr_dag.py --status ... --strict-rescue-slice --write-mermaid ...`: 211개 PR, DAG valid.
- `sync_pr_dag_mirrors.py --check`와 `validate_remaining_pr_replan.py`: 둘 다 PASS.
- `pytest scripts/codex_harness/test_pr_dag_harness.py`: 42 passed.
- 작성 문서·DAG의 staged `git diff --check`: PASS. 역사적 I1/I2 원문에는 원래 CRLF와 끝 공백이 있어 전체 staged diff에는 whitespace 경고가 있다. 원본 바이트 동일성이 수락 기준이므로 이 파일들을 공백 교정하지 않았다.

Host 자체 검토에서 원본/매핑 유일성, Git filter 영향, 기존 사용자 변경, claim 문구, 상대 링크를 확인했다. 추가 과학 감사 루프는 실행하지 않았다.
