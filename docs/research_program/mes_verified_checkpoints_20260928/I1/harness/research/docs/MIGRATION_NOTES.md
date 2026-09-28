# GPT-5.6 v3.1.0 → GPT-6 Astra v4.0.0

원본의 evidence acquisition, claim audit, hypothesis, review, validation, decision, formalization 구분과 원래 물리·수학 연구 목적을 보존했다. `.agents/skills/`의 원본 bytes는 바꾸지 않았다.

운영 변경:

- 전체 상태·모든 phase 일괄 로딩을 core+active state+필요 source로 바꿨다.
- 한 실행자가 전체 목표를 소유하며 phase 종료를 사용자 승인 대기로 오인하지 않도록 했다.
- 고정 hypothesis 수와 targeted fallback 최대 2회 같은 임의 상한을 제거했다. 사용자 명시 예산은 유지한다.
- 리뷰 재귀·증거 없는 재시도를 제한하고, 같은 범위의 증거 기반 수정은 완료기준까지 허용했다.
- 탐색 중 진단 유도·toy check를 허용하고 최종 연구서사의 승격과 구분했다.
- 검증 설계에서 끝나던 경로를 실제 가용·승인된 실행과 raw evidence로 연결했다.
- owner self review와 실제 independent review, source identity와 scientific authority를 분리했다. 원본의 최종 PROMOTE 독립성은 유지한다. 후보 생성·검증 설계에 참여하지 않은 실제 독립 decision reviewer가 승격을 판정하며, 없으면 HOLD + INDEPENDENT_REVIEW_UNAVAILABLE로 남긴다.
- 모델 routing·호스트 capability·검증 상태를 명시했다. v4.0.0은 모델간 실증 성능 우위를 주장하지 않는다.

기존 source 목록은 `docs/RESEARCH_BASIS.md`에 미검증 inherited 자료로 남겼다. 새로 확인된 근거와 claim 대응은 `docs/MIGRATION_EVIDENCE.md`, 모델간 평가는 `docs/MODEL_REGRESSION.md`를 따른다.
