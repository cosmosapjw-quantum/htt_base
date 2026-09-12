# 명제·증명 기록 읽기

R8에 포함된 파일에서 추출한 명제 관련 레코드다. 같은 ID의 서로 다른 버전·가정과 문서 섹션도 각각 세며, 독립 명제나 증명된 정리의 개수가 아니다.

| 정적/원문 상태 분류 | R8 레코드 수 |
|---|---:|
| `candidate` | 362 |
| `declaration_present` | 257 |
| `recorded_active` | 33 |
| `recorded_conditional` | 72 |
| `recorded_proven_or_derived` | 31 |
| `recorded_retracted` | 2 |
| `recorded_superseded` | 4 |
| `recorded_unresolved` | 78 |
| `recorded_validation_claim` | 44 |
| `source_present` | 651 |
| `textual_statement` | 341 |

`recorded_proven_or_derived`는 기록상 증명·유도 주장, `recorded_conditional`은 조건부 기록, `candidate`는 후보 표기다. 철회·대체 기록과 unresolved 기록도 그대로 남는다.
`declaration_present`는 Lean 선언 등의 존재이고 `textual_statement`는 문서 명제 구절이다. 이 둘을 증명 완료 상태로 바꾸지 않는다.

## 근거를 확인하는 순서

1. `query --kind proposition`으로 ID를 얻고 `show ID`에서 원문, 가정, 정의역, source pointer와 관찰 버전을 읽는다.
2. `proof_evidence`에서 원문의 증명 주장, 참조 파일 존재, 참조 기록의 명제 ID 일치를 구별한다. 근거 파일이 없으면 `NO_BOUND_REFERENCE`로 남는다.
3. `relationships`의 버전과 `ref_membership`을 확인한다. 파일 존재와 같은 ID만으로 가정 일치나 과학적 검증을 추론하지 않는다.
4. `history ID`와 같은 registered ID의 다른 원문을 함께 읽어 조건 변경·철회·대체를 확인한다. 원문 근거가 없는 대체 관계는 미해결로 남는다.

이번 조사에서 새로 증명된 명제는 없다. 상세 정적 목록은 [생성 목록](LISTS.md), 기록을 읽는 경계는 [구조 문서](ARCHITECTURE.md)에 있다.
