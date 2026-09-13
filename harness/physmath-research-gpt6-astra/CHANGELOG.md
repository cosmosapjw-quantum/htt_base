# Changelog

## 4.0.0 — 2026-09-08

- GPT-6 Astra 대상 단일 owner·필요 문맥 로딩·승인 내 연속 실행을 명시.
- 고정 후보/검색 횟수 cap을 제거하고 탐색 동기와 수렴 criterion을 보존.
- 실제 판별 검증 실행, 근거 유형, identity/authority, 독립 검토 상태를 구분.
- 리뷰 재귀를 제한하면서 같은 범위의 증거 기반 수정은 완료기준까지 허용.
- `.agents/skills/` 원본 byte 보존. 모델간 실증 성능은 `NOT_EVALUATED`.

## 3.1.0 — 2026-07-12

- GPT-5.6 outcome/constraint/evidence/completion-bar 방식으로 프롬프트를 경량화.
- Project source와 durable state 문서를 중심으로 연구 상태를 외부화.
- evidence acquisition, claim-source audit, hypothesis construction, independent review,
  physics/mathematics validation, decision gate, survivor-only formalization을 분리.
- Deep Research, Work, Projects, repo-scoped skills를 위한 사용 경로 추가.
- 자동 검증 스크립트와 초기화 도구 추가.
