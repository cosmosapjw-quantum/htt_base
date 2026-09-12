# HTT 프로젝트 길잡이와 전체 이력 카탈로그

이 자료는 **정적 조사로 만든 검색용 데이터베이스**다. 기능의 코드, 설계,
분석 절차, 명제, 저장된 증명·실행 기록을 버전과 함께 찾는 데 사용한다.
원본 레지스트리의 과학적 권위를 대체하지 않는다.

## 먼저 사용할 명령

저장소 루트에서 실행한다. 조회에는 Python 3.11 이상과 SQLite FTS5를 사용한다.
전체 재수집에는 PyYAML이 추가로 필요하고, PDF 본문 추출에는 `pdftotext`를 사용한다.
조회 시 외부 연구 환경, 데이터 원본, CAS 도구는 필요하지 않다.

```bash
# 첫 조회가 배포된 압축 DB를 .cache/project_catalog/ 아래에 자동 복원한다.
python3 -B scripts/project_catalog.py query --kind analysis --q CF4
python3 -B scripts/project_catalog.py query --kind proposition --status candidate
python3 -B scripts/project_catalog.py query --kind plan --ref all --q transfer
python3 -B scripts/project_catalog.py query --kind port --ref all
python3 -B scripts/project_catalog.py query --needs-update --ref baseline
python3 -B scripts/project_catalog.py check
```

기본 조회 버전은 R8 `efc5f30666b96782f946375551f0068bb3a30f74`다. `--ref all`은
수집된 모든 버전, `--ref working`은 조사 시점에 관찰된 작업트리·연결 자산이다.
`--ref <브랜치 또는 커밋>`으로 특정 버전을 지정한다. 여러 저장소에 같은 이름이
있으면 `--source`로 구분한다. 비교 기준 R8은 기본 원격 브랜치와 동일하다는 뜻이 아니다.

2026-09-12 원격 HEAD 조회에서 기본 브랜치는 `research/pr04-multicomponent`,
커밋은 `50ea6d76ace70dec57b8794ab0d1cf9b8fab42cb`였다. 카탈로그에는 이 원격
참조와 같은 이름의 로컬 브랜치를 별도로 보존한다. 기본 브랜치는 향후 바뀔 수 있다.

```bash
# 조사 시점의 기본 원격 브랜치
python3 -B scripts/project_catalog.py query --kind feature --source htt_base --ref origin/research/pr04-multicomponent --limit 20

# 같은 경로·내용이 R8에 없는 버전
python3 -B scripts/project_catalog.py query --kind code --ref all --not-in-ref baseline --limit 30

# 과거 코드와 R8의 바이트 동일성 검색: 이식의 역사적 증명과는 구분한다.
python3 -B scripts/project_catalog.py query --kind feature --ref all --port-status byte-identical --q legacy

# 상세 정보: 반환된 전체 id를 사용한다.
python3 -B scripts/project_catalog.py show RECORD_ID
python3 -B scripts/project_catalog.py history RECORD_ID --format json
python3 -B scripts/project_catalog.py history htt/src/common/theorem_registry.py

# 전체 목록 내보내기. 기본 limit는 50이며 -1이 전체다.
python3 -B scripts/project_catalog.py export --kind proposition --ref all --limit -1 --format csv --output /tmp/htt-propositions.csv
python3 -B scripts/project_catalog.py query --kind gap --limit 30
python3 -B scripts/project_catalog.py query --kind asset --q cf4 --limit 30
```

## 읽는 순서

1. [구조와 해석 방법](ARCHITECTURE.md): 소스·버전·코드·분석·명제의 관계와 상태 의미.
2. [기능·분석 길잡이](CAPABILITIES.md): 연구 질문별 입력·처리·출력·주의점.
3. [생성 목록](LISTS.md): 기준 버전의 기능·분석·명제·계획·업데이트 목록.
   명제는 [상태별 안내](PROPOSITIONS.md)와 함께 읽는다.
4. [조사 범위와 누락](COVERAGE.md): 실제 건수, 처리 상태, 미지원·누락·제한.
5. [이식·구버전·업데이트 안내](PORTS_AND_UPDATES.md): 기록, 차이, 후속 확인의 구분.
6. [SQL 예제](queries.sql): SQLite 직접 조회와 버전 비교.

## 상태를 읽는 방법

| 항목 | 의미 |
|---|---|
| `recorded_status` | 원문에 적힌 상태. 현재 작업의 검증 결과가 아니다. |
| `definition_present` | Python AST에서 정의를 확인했다. 호출·실행 성공은 미검증이다. |
| `static_entrypoint_candidate` | 실행 진입점이 정적으로 발견됐다. 분석 사용 가능성은 미검증이다. |
| `stub` / `abstract_interface` | 구현 본문이 없는 함수와 의도된 추상 인터페이스를 구분한다. |
| `recorded_port_mention` | 원문에 이식·migration이 언급됐다. 계획·거절·완료 여부는 원문을 확인한다. |
| `candidate` | 원문에서 계획·제안·후보로 표시한 항목이다. |
| `recorded_active` / `recorded_conditional` | 해당 버전의 레지스트리 표기를 보존한다. |
| `recorded_proven_or_derived` | 원문이 증명·유도를 주장한다. 이번 조사에서 재증명하지 않았다. |
| `recorded_validation_claim` | PASS/VALIDATED 기록이 있다. 무엇을 검증했는지는 원문을 확인한다. |
| `recorded_retracted` / `recorded_superseded` | 원문에 철회·대체가 기록됐다. 이전 버전도 남아 있다. |
| `same_version_file_present` | 대표 관찰 커밋에서 참조 파일을 찾았다. 명제의 증명 성립을 뜻하지 않는다. |
| `lexical_partial` / `pdf_text_partial` | 선언·본문 일부를 정적으로 추출했다. 컴파일·수식·시각 검증은 수행하지 않았다. |

모든 연구 실행 상태는 `NOT_EXECUTED`, 증명 재확인 상태는 `NOT_RECHECKED`다.
테스트 PASS, Lean 선언, CAS 결과 파일, ACTIVE 표기는 서로 다른 종류의 근거다.
스칼라 진단량으로 Bianchi family identification을 주장하거나 MIO 진단을 HTT
posterior로 합치는 해석은 허용되지 않는다. 외부 transfer의 조건도 원문과 함께 확인한다.

## 갱신과 배포

```bash
# sources.json에 기록된 경로가 있는 연구 호스트에서 증분 갱신
python3 -B scripts/project_catalog.py scan --scope docs/project_catalog/sources.json

# 기존 DB를 보존하고 별도 위치에 전체 재생성
python3 -B scripts/project_catalog.py --db /tmp/new-catalog.sqlite scan --full --scope docs/project_catalog/sources.json

# 배포 DB를 명시적으로 다른 위치에 복원
python3 -B scripts/project_catalog.py --db /tmp/restored-catalog.sqlite restore

# 같은 DB에서 길잡이와 목록 갱신 (PyYAML 필요)
python3 -B scripts/project_catalog.py export --docs docs/project_catalog

# 수정된 DB의 배포본 생성
python3 -B scripts/project_catalog.py export --package docs/project_catalog/database
```

텍스트·아카이브 크기 또는 중첩 깊이 제한을 바꾸면 새 `--db` 경로에서
`scan --full`을 실행해야 한다. 기존 DB는 이전 조사 범위의 결과로 남는다.

압축 조각과 manifest는 DB 운반을 위해 제공한다. 체크섬은 전송 바이트 확인용이며
과학적 타당성의 근거가 아니다. `sources.json`은 실제 조사 호스트의 경로를 보존한다.
다른 호스트에서는 경로를 대응시켜 재수집하거나, 원본 없이 배포 DB만 조회할 수 있다.

전체 생성 절차와 검수·push 결과는 [작업 기록](EXECUTION.md)에 기록한다.

자동 에이전트 기억·실행 캐시인 `.remember`는 재귀 조사 대상에서 제외한다.
이전에 관찰한 경로는 `agent_context_cache_metadata_only`로 남지만 본문과
의미 레코드는 배포 DB에 포함하지 않는다.

배포 DB는 압축 2.19 GiB(57개 조각, 조각당 최대 40 MiB), 복원 후 약 10.08 GiB다.
첫 조회에는 다운로드된 조각의 검증·압축 해제 시간이 필요하며 이후에는 로컬 SQLite를 조회한다.
R8 생성 목록의 소스 링크는 R8 커밋에 고정했다. `show`/`history`의 대표 관찰 커밋은 별도 정보다.
