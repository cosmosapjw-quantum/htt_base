# 정적 조사와 배포 작업 기록

작업: `PR-CATALOG-001`. 비교 기준: R8
`efc5f30666b96782f946375551f0068bb3a30f74`.
브랜치: `implementation/project-catalog-20260912`.
원본 `codex_emergency` 체크아웃은 수정하지 않고 별도 작업트리에서 수행했다.

## 수행 범위

- 현재 HTT 전체 로컬 Git 이력 2,005개 커밋과 이력 정리 이전 백업 839개 커밋.
- 구·신 커밋 대응 839개, 외부 연구 저장소와 설치 의존성의 버전 정보.
- 등록 작업트리, 연결된 코드·설계·아카이브·데이터 제품 위치, 미커밋 자료의 정적 추출.
- 연구 코드·연구 테스트 수집·분석·CAS·Lean 증명은 실행하지 않았다.
- 자동 추출의 상태·근거 수준은 원문 과학적 상태와 별도로 보존했다.

최종 건수는 [summary.json](summary.json), 모든 처리 사유는
[coverage_gaps.csv](coverage_gaps.csv), 해석은 [COVERAGE.md](COVERAGE.md)에 있다.
원본 미커밋 파일과 외부 원자료는 배포 파일로 복사하지 않았다. DB에는 탐색을 위한
정적 선언, 서명, 원문 발췌, 위치와 버전 정보가 들어 있다.

## 검수

카탈로그 전용 테스트 **27 passed**. 테스트는 임시 Git 저장소·텍스트·아카이브
fixture만 사용한다. [실제 출력](review/catalog_tests.txt)과
[독립 검토·수정 기록](REVIEW.md)을 보존했다.

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 PYTHONDONTWRITEBYTECODE=1 \
  python3 -B -m pytest -c /dev/null -p no:cacheprovider \
  --confcutdir=tests/project_catalog tests/project_catalog -q
python3 -B scripts/codex_harness/validate_pr_dag.py docs/codex_handoff/pr_backlog.yaml
```

DAG 검증은 195개 PR에 대해 통과했다. 과학적 PR의 완료·보류·차단 상태는 유지한다.
독립 전체 재생성 fixture에서는 sources/commits/refs/trees/contents/files/records/
edges/filesystem/gaps/commit_aliases/snapshots/members의 모든 행이 동일했다.

실제 전체 DB 검사에서는 처리 상태 누락, 파일 버전이 없는 Git leaf, 버전에 연결되지
않은 관찰 정규 파일, dangling 참조, 아카이브 root 누락, FTS 개수 불일치가 모두 0이었다.
DB 구조 검사 PASS는 과학적 주장이나 증명 PASS가 아니다.

## 사용한 생성·조회 명령

실제 연구 호스트에서는 `--db`에 작업 디렉터리의 `catalog.sqlite`를 지정했다.
아래는 저장소에서 같은 CLI 경로로 재현하는 명령이다.

```bash
python3 -B scripts/project_catalog.py scan --scope docs/project_catalog/sources.json
python3 -B scripts/project_catalog.py export --docs docs/project_catalog
python3 -B scripts/project_catalog.py query --kind analysis --q CF4
python3 -B scripts/project_catalog.py query --kind code --source htt_base \
  --ref origin/research/pr04-multicomponent --not-in-ref baseline
python3 -B scripts/project_catalog.py query --kind proposition --status recorded_proven_or_derived
python3 -B scripts/project_catalog.py query --kind port --ref all
python3 -B scripts/project_catalog.py query --needs-update
python3 -B scripts/project_catalog.py check
python3 -B scripts/project_catalog.py export --package docs/project_catalog/database
```

기본 원격 브랜치는 `git ls-remote --symref origin HEAD`로 확인했다.
2026-09-12 조회값은 `research/pr04-multicomponent` /
`50ea6d76ace70dec57b8794ab0d1cf9b8fab42cb`이며, R8과 다르다.

## 실제 증분 갱신 확인

처음 재수집에서 추가된 파일 버전 17개는 모두 자동 에이전트 실행 캐시였다.
해당 캐시의 본문을 제외하고 과거 위치 메타데이터를 남긴 뒤 전체 범위를 다시
수집했다. 결과는 **parsed_new=0, parsed_cached=0**, 337.327초였으며 파일·레코드·
참조와 상태별 건수 비교가 모두 동일했다. [기계 판독 결과](incremental_check.json).
고정 fixture의 독립 전체 재생성은 모든 논리 행의 동일성도 확인한다.

이후 원문 상태를 바꾸지 않는 토큰 분류 보정 275개를 적용했다. PROVENANCE의
오분류 1개와 명시적 후보·미평가 표기를 바로잡은 내역은 REVIEW에 남겼다.
최종 건수와 조회는 이 보정까지 반영한다.

## 로컬 배포본

[대표 질의 9개](representative_queries.json), 명제 상세·이력, CSV 내보내기와
최종 DB 검사 모두 통과했다. [DB 검사](checks.json)의 모든 결함 계수는 0이다.
GitHub에서 접근 가능한 R8 목록 링크는 R8 자체 커밋에 고정했다.

DB는 57개 gzip 조각으로 구성된다. 각 조각은 최대 40 MiB이며 압축 총량은
2.19 GiB, 복원 크기는 10.08 GiB다. 큰 Git 전송을 나누기 위해 도구·문서 커밋과
두 DB 분할 커밋을 준비하고 차례로 일반 push한다. 전체 DB가 준비된 후 게시한다.

## 진행 중인 최종 배포 확인

실제 전체 범위 증분 수집, 최종 대표 질의 대조, 압축 DB 게시와 별도 원격 체크아웃의
복원 결과를 완료 후 이 절에 기록한다. 원격 게시 전에는 배포 완료를 주장하지 않는다.
