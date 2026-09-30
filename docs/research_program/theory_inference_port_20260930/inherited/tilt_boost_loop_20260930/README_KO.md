# Tilt / non-tilt / observer boost 연구 결과

먼저 [REPORT_KO.md](REPORT_KO.md)를 읽고, local 실행에는 [LOCAL_CODEX_PROMPT_KO.md](LOCAL_CODEX_PROMPT_KO.md)를 사용한다.

- [CLAIMS.json](CLAIMS.json): 최종 독립 검토가 반영된 11개 항목. 조건부 이론 10개, 실제 우주 판정 HOLD 1개.
- [OBSERVATION_CONTRACT.schema.json](OBSERVATION_CONTRACT.schema.json): reference pair, source, normal, distance/redshift, noise/selection, normalization과 출력 계약.
- [NEXT_TASKS.json](NEXT_TASKS.json): local 작업 11개의 의존성 및 완료 기준.
- [INDEPENDENT_REVIEW.md](INDEPENDENT_REVIEW.md), [INDEPENDENT_DECISION.json](INDEPENDENT_DECISION.json): 독립 검토와 주장 범위.
- [REVIEW_CORRECTIONS.md](REVIEW_CORRECTIONS.md): 검토 중 수정한 네 가지 범위·전제.
- [CLOSEOUT.md](CLOSEOUT.md): 최종 완료 상태. RESEARCH_STATE.md는 심사 대상이었던 초기 계약 snapshot으로 보존한다.
- evidence/: 실제 실행한 Wolfram 입력 5개와 raw 출력, SciSpace discovery 기록.
- inherited/: 읽은 이전 루프의 핵심 보고서·명제와 T5/T6 근거의 바이트 동일 사본. 새 판정이 아닌 선행 자료다.
- [SOURCE_REGISTER.json](SOURCE_REGISTER.json), [PRESERVED_SOURCE_HASHES.json](PRESERVED_SOURCE_HASHES.json): 출처 및 계승 경로.

핵심 구분은 물질–균질면의 eta_UN과 관측자–물질의 eta_OU다. CMB의 eta_OR은 별도다. Boltzmann solver나 실제 관측 적합은 이 루프에서 실행하지 않았다. 이전 I2/I3와 BIC-07의 미해결 범위를 보존한다.

압축파일이 열리지 않으면 개별 보고서, 프롬프트, JSON 계약을 사용할 수 있다. Local Codex에는 보고서만이 아니라 CLAIMS, 독립 판정, 관측 schema와 task DAG도 함께 전달한다.
