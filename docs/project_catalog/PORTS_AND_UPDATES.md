# 이식·구버전·업데이트를 찾는 방법

이 카탈로그는 파일 버전과 원문에 기록된 변경 사유를 보존한다. 오래되었다는 이유로
코드 수정이 필요하다고 판정하지 않는다. 업데이트 목록은 실제 스텁 본문, 원문이
지정한 후속 항목, 길잡이 카드의 구체적인 입력·가정 차이를 출발점으로 삼는다.

## 이식 근거의 세 종류

| 조회 | 확인하는 사실 | 추가로 확인할 내용 |
|---|---|---|
| `query --kind port --ref all` | 추출된 원문이 port/migration/이식을 언급 | 계획인지 완료인지, 원본·대상과 변경 내용 |
| `query --port-status byte-identical --ref all` | R8에 바이트가 동일한 내용 존재 | 동일 내용의 존재가 실제 이식 경로나 방향을 증명하지 않음 |
| `query --not-in-ref baseline --ref all` | 같은 경로·내용 조합이 R8에 없음 | 의도된 구버전인지, 다른 브랜치 전용인지, 이식이 필요한지 |

이식 언급에는 거절된 migration도 남는다. 이름이 비슷하다는 이유로 대체·이식
완료 관계를 만들지 않는다. `show ID`의 근거 경로, 관찰 커밋, 브랜치 포함 여부를
함께 읽는다. `history ID`는 같은 선언과 바이트 별칭을 보여 주며, Git rename의
의도나 처음 도입된 날짜를 자동 판정하지 않는다.

## 확인 가능한 예: TSC의 일반 guard 동작을 COMMON으로 분리

[PR-031 원문](https://github.com/cosmosapjw-quantum/htt_base/blob/efc5f30666b96782f946375551f0068bb3a30f74/docs/PR_DELTAS/pr-031.md)은
TSC legacy의 source/propagation/observable adequacy guard 동작을
`common.semantic_guards` 소유로 분리한 작업을 기록한다.

- 원본 맥락: `htt/tsc/contracts.py`, `htt/tsc/budget/source_to_channel.py`와
  TSC adapter/report 경계. 원문 Evidence read 절에서 확인할 수 있다.
- 대상: `htt/src/common/semantic_guards/admissibility_status.py`,
  `source_propagation_status.py`, `__init__.py`의 공개 인터페이스.
- 변경: adequacy 상태를 분리한 기록과 caveat 첨부 API를 도입했다. TSC 전체
  dataclass의 이동이나 TSC validation을 COMMON으로 승격한 작업은 아니다.
- 후속 확인: 기존 소비자가 이 일반 guard 동작을 필요로 하는 경우 import/API와
  상태 해석을 대조한다. legacy 재현용 코드를 연식 때문에 일괄 변경하지 않는다.
- 확인 방법: `query --kind feature --q semantic_guards`, 해당 코드의 `show`,
  PR-031에 기록된 테스트 경로. 이 카탈로그 조사에서는 테스트를 재실행하지 않았다.

## 업데이트 우선순위

| 순서 | 조건 | 필요한 수정·확인 | 선행 조건과 검증 방법 |
|---|---|---|---|
| 1 | 사용하려는 분석의 입력 경로·버전이 불명확 | 데이터 제품·release와 설정 경로를 대응 | 분석 카드와 asset 목록 대조 후 별도 실행 작업에서 입력 검증 |
| 2 | 실제 소비자가 필요한 함수가 `stub` | 본문 구현 또는 의도된 인터페이스 여부 확인 | `show`의 signature/calls, 소비자별 계약·테스트 정의 |
| 3 | 원문이 `superseded_by`를 지정 | 후속 항목의 가정·정의역·출력 차이를 비교 | 원본·후속 버전 기록 모두 읽고 소비자 참조 변경 여부 결정 |
| 4 | R8과 경로·내용이 다른 별도 브랜치 | 필요한 기능과 API 차이를 식별 | `history`와 버전별 symbol/record 비교; 차이 자체는 결함이 아님 |

자동 업데이트 항목의 `details`에는 사유·필요 행동·확인 방법이 있으며, 대상 버전은
같은 레코드의 `source_id`/`observed_commit`이다. 구체적 최종 수정은 사용하려는
소비자가 정해져야 확정할 수 있다. 과학적 기준이나 reference tolerance를 이
목록만으로 바꾸지 않는다.

```bash
python3 -B scripts/project_catalog.py query --kind code --status stub --ref all --limit 30
python3 -B scripts/project_catalog.py query --needs-update --ref baseline --limit 30
python3 -B scripts/project_catalog.py query --kind plan --ref all --status candidate --limit 30
python3 -B scripts/project_catalog.py query --kind code --ref all --not-in-ref baseline --limit 30
```

“설계만 존재하는 기능”을 찾을 때에는 `queries.sql`의
`NO_BOUND_IMPLEMENTATION_REFERENCE` 조회를 시작점으로 삼는다. 이는 이 정적
조사에서 구현 파일 연결이 확인되지 않은 계획이라는 뜻이다. 다른 이름으로 등록된
구현이나 동적 연결까지 없다는 판정은 아니며, 오래된 계획 상태가 완료 기록보다
늦게 갱신되지 않았을 가능성도 원문 버전으로 확인해야 한다.
