# PR-MES-FULL-HANDOFF — 원본 전체 ZIP 검증·등록

2026-09-28. Owner HTT research archive intake; C0 archival/reproducibility claim, no transfer. 사용자 요청에 따라 I3 결과 등록 뒤 별도의 원본 전체 인계 ZIP을 검증했다. 원본 735 MiB asset을 Git blob으로 중복 보관하지 않고, Git에는 manifest/복원 코드/실제 receipt/검증 기록을 등록하며 byte-identical archive는 `htt-mes-full-handoff-20260928` prerelease asset으로 게시한다.

## 실행 결과

전체 SHA-256 `740658f22e9a60be5cbefcd2ea4d6e8725f1f35585a96b02a2d845071d1af672`; 외부 ZIP 19개 member CRC 통과, manifest 17개 size/SHA 통과, 직접 포함된 backup 3개와 checkpoint 2개 CRC 통과. 추가로 고유 중첩 ZIP 63개(깊이 4까지) CRC 오류 0. 복원 도구 11개 테스트 통과; 새 임시 경로에 `--catalog` 실제 복원 성공, DB/기존 repo 변경 없음. `VALIDATION_KO.md`와 `RESTORE_RECEIPT.json`에 범위와 counts를 적었다.

과거 `build_i2_delivery.py`는 재생성 입력을 소비하는 패키징 도구이므로 실행하지 않았다. 백업 속 역사적 연구 스크립트의 일괄 실행도 수행하지 않았다. I1/I2의 수학·물리 판정은 archive byte 검증으로 승격되지 않는다. R9 및 기존 사용자 변경은 유지했다.

## 검토·검증

Host의 archive/restore/claim/publication self-review 1회. 원본 경로와 임시 복원 경로를 분리했고 원본 DB 삭제·기존 checkout 덮어쓰기가 없음을 확인했다. `python3 -B scripts/codex_harness/validate_pr_dag.py docs/codex_handoff/pr_backlog.yaml --status docs/codex_handoff/pr_status.yaml --strict-rescue-slice`, mirror/replan 검증, 42개 DAG harness 회귀와 staged diff check를 실행한다. 배포는 일반 main push R1과 외부 archive asset R3 byte readback을 분리한다. Independent scientific decision은 이번 PR에 포함되지 않는다.

게시 결과: `main`의 등록 커밋 `933db195de6dba4b829a6c501649aca103a837b9`는 공식 검증 도구에서 `VERIFIED_R1`. 같은 커밋을 가리키는 prerelease의 원본 ZIP asset은 769,808,802바이트이며, 별도 다운로드 SHA-256이 원본과 정확히 같아 `VERIFIED_R3_BYTE_READBACK`. `PUBLICATION_RECEIPT.json`에 원격 URL과 identity를 보존했다. 출판 확인은 과학적 admission이 아니다.
