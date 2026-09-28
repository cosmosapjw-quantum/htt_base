# R1–R5 통합 인계 패킷

이 ZIP 하나를 local Codex에 첨부하고 CODEX_HANDOFF_PROMPT_KO.md를 실행 지시로 사용한다. 이 패킷은 repo 통합용 자료이며 새로운 과학 판정이나 repository 반영 완료를 뜻하지 않는다.

## 포함 범위

| 단계 | 날짜 | 제공 자료 |
|---|---|---|
| R1 | 2026-09-20 | 원본 ZIP, 전체 펼친 내용, 보고서·증명·code/raw·판정 |
| R2 | 2026-09-20 | 원본 ZIP, 전체 펼친 내용, 보고서·증명·code/raw·판정 |
| R3 | 2026-09-27 | 전체 보고서; 별도 raw/독립 판정 파일은 이번 수집에서 미확보 |
| R4 | 2026-09-27 | 원본 ZIP, 전체 펼친 내용, 보고서·증명·code/raw·판정 |
| R5 | 2026-09-27 | 원본 ZIP, 전체 펼친 내용, 보고서·증명·code/raw·판정 |

R1–R5의 주요 보고서 원문은 모두 들어 있다. 다섯 단계 모두의 원시 실행 증거가 완비됐다는 뜻은 아니다. R3의 원문에 기록된 검산·판정은 별도 raw 확보 상태와 구별한다.

## 읽기 순서

1. CODEX_HANDOFF_PROMPT_KO.md
2. INTEGRATION_NOTES_KO.md
3. INPUT_INVENTORY.json와 PACKAGE_VALIDATION.json
4. reports/의 다섯 보고서 및 materials/의 상세 근거

originals/는 원본 byte를 보존한다. materials/는 원본 내부 경로를 유지해 펼친 사본이다. reports/는 주요 보고서를 쉽게 열 수 있도록 만든 동일 byte 사본이다. 중복은 의도적이며 새 버전으로 오해하지 않는다.

R1/R2의 이미 유도된 exact operator/weak form을 R5의 신규 후보 HOLD와 구별한다. 다음 연구를 정하기 전에 INTEGRATION_NOTES_KO.md의 계승 관계를 대조한다. 기존 NEXT_PROMPT들은 역사적 원본으로 보존했으며 자동 실행하지 않는다.

이번 조립에서는 원본 네 ZIP의 manifest 총 131개 항목과 CRC를 확인했다. R3 보고서는 기존 고정 SHA-256과 일치한다. 새 과학 계산은 실행하지 않았다. MANIFEST.sha256은 이 통합 패킷의 파일 integrity를 확인하며 자기 자신은 제외한다. 외부 ZIP hash는 별도 .sha256 파일로 제공한다.
