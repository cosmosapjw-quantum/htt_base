# HTT 독립 감사 R4 근거 묶음

2026-09-08. 이 묶음은 전수조사 진행 중 GF·CF4·관측 nuisance 후속 계열의 정적 감사와 원문 대조를 보존한다. 전체 repository의 전문 정독 완료본은 아니다.

먼저 `outputs/HTT_HISTORY_AND_SUCCESSOR_AUDIT_R4_KO_20260908.pdf`를 읽는다. 원문은 `audit_v4/report-source.md`다. 이전 감사의 GF 비판은 R4에서 확인한 v8·v9 수리 및 정의역에 따라 적용 범위를 좁혀야 한다. 이전 보고서는 역사 기록으로 포함하며 소급 수정하지 않았다.

| 위치 | 내용 |
|---|---|
| `audit_v4/CLAIM_SOURCE_LEDGER.md` | 주장과 고정 source·result·문헌의 대응 |
| `audit_v4/INDEPENDENT_REVIEW_RECORD_KO.md` | 독립 정적 검토의 범위와 반영 사항 |
| `audit_v4/WEB_SOURCE_LEDGER.md` | 원논문·공식 자료의 버전과 사용 범위 |
| `audit_v4/read_ledger_v4.json` | 이번에 전문을 읽은 53개 기록; 새 고유 내용은 51개 |
| `audit_v4/read_ledger_cumulative.json` | 누적 전문·부분·변경분 읽기 기록 |
| `audit_v4/coverage.json` | 중복과 부분 읽기를 제외한 누적 전문 읽기 213개 |
| `audit_v4/sources/` | 이번 source의 정확한 바이트와 취득 기록 |
| `audit_v4/census/` | 전 이력 목록·모든 평탄화 tree의 delta checkpoint |
| `audit_v4/CONTINUE_AUDIT_KO.md` | 미완료 조사 범위와 재개 방법 |
| `audit_v4/document_qa.json` | 최종 PDF의 문서 검증 기록 |
| `audit_v2/sources/`, `audit_v3/sources/` | 이전 조사에서 보존한 source cache |
| `recovery_audit_v1/extracted/census/` | 기존 고정 refs·commit graph 등 원본 목록 근거 |
| `MANIFEST_SHA256.json` | 자체 파일을 제외한 묶음 내 파일의 SHA-256 |

182개 고정 refs에서 도달하는 2,061 commits와 2,003 root trees의 목록에는 고유 blob 18,885개가 있다. 이는 당시 확보한 참조의 범위이며 새로 이동한 모든 원격 ref를 재수집한 결과는 아니다. 목록 확보·hash 확인·JSON 파싱을 전문 읽기로 세지 않는다. 전문 읽기 집계는 `read_level == "full"`만 택하고 Git blob SHA로 중복 제거한다.

`history_tree_deltas.json`은 모든 확보된 snapshot의 path/blob SHA/byte length 대응을 손실 없이 보존한다. 원래 Git mode·하위 tree 객체·전체 blob payload를 담지는 않는다. 재구성 방법과 검증 hash는 `CONTINUE_AUDIT_KO.md`에 있다. 원시 tree cache를 반복해서 넣은 대형 이전 ZIP은 중첩하지 않았다.

이번 53개 읽기 기록의 source payload는 모두 들어 있다. 누적 213개 전문 읽기 기록 전체의 payload가 이 묶음 하나에 모두 들어 있다는 주장은 하지 않는다. 과거 cache의 절대경로는 당시 workspace를 가리킬 수 있으므로 이동 시 상대경로 및 고정 ref/blob을 사용한다.

포함한 Python 파일은 목록·원장·문서·압축 파일을 보존하는 감사 보조 스크립트다. CF4·CMB 등의 과학 코드나 수치 분석을 실행한 것은 아니다. 과학 코드의 재실행과 실제 자료 분석은 사용자의 워크스테이션 Local Codex에 남아 있다.

PDF 재생성에는 Pandoc, XeLaTeX, Noto Sans KR, DejaVu Sans Mono가 필요하다. `header.tex`의 글꼴 경로는 작성 당시 환경을 반영한다. 보고서 PDF 자체에는 글꼴이 포함되어 있다.
