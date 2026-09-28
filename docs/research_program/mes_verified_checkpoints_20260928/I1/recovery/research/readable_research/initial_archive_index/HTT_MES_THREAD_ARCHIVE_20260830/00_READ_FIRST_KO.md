# HTT / Planck MES — 가용 대화·자료 통합 아카이브

작성일: 2026-08-30

## 가장 먼저 확인할 점

**이 ZIP은 이 스레드의 처음부터 끝까지 모든 대화 원문을 담은 완전 export가 아니다.** 현재 접근 가능한 원본 파일, 기존 생성 패키지, 대화의 전사·발췌·요약, 그리고 누락 목록을 묶은 보존본이다. 전체 대화 원문과 일부 과거 첨부 파일은 현재 접근 범위에 없었다. 없는 내용을 요약으로 메워 원문이라고 표시하지 않았다.

## 실제 포함 범위

- 현재 runtime에서 확인한 파일 102개 / 440,778,957 bytes 중 101개 / 248,491,937 bytes를 원본 바이트 그대로 보존했다.
- 기존 ZIP/TAR, PDF, Markdown, JSON, YAML, Python, Wolfram 코드와 로그·receipt를 원래 이름/상대경로대로 `02_original_files/`에 저장했다.
- 작은 연구/하네스 패키지의 738개 내부 파일을 `03_expanded_packages/`에 별도로 풀어 바로 읽을 수 있게 했다. 이들은 원본 ZIP을 대체하지 않고, source-member→expanded-path 매핑을 제공한다.
- 대화 기록은 38개 가시 항목의 **부분 색인·전사·발췌·요약**이며 플랫폼 transcript 전체가 아니다. 각 record의 representation 필드를 확인해야 한다.
- 두 theorem 패키지, tensor/tilt 연구·coding 패키지, WU별 가용 handoff, 문헌/코드/하네스 archive를 모두 원본 형태로 보존했다.
- 마지막 GitHub branch/PR readback도 포함했으며, 이번 archive 작업은 원격 저장소를 수정하지 않았다.

## 제외·미확보

전체 채팅 export, 생략 메시지, user host의 수 TB raw 데이터/venv, 현재 mount되지 않은 일부 GitHub/로컬 보고서·carrier·checkpoint는 포함하지 못했다. 항목별 상태는 `00_index/MISSING_ITEMS.json`에 있다.

Rust binary distribution 하나는 standalone font 파일을 포함해 원본 archive를 재배포하지 않았다. 글꼴 제외 재포장 두 시도가 시간 한도 내에 끝나지 않아 partial 파일은 배포하지 않는다. 원본 자체는 변경하지 않았고 지문·detached signature·환경 스크립트는 보존했다.

## 폴더

```text
00_index/              보존/누락/해시/링크/중복·archive-member 색인
01_conversation/       부분 대화 기록, 흐름과 미완료 재개 지점
02_original_files/     확인한 원본 파일의 바이트 동일 사본
03_expanded_packages/  기존 소형 ZIP의 내부 파일(원본 ZIP도 별도 보존)
04_repository_evidence/ 마지막 원격 branch/PR 상태 readback
05_source_extracts/    원본 바이트가 없는 문서의 명시적 text extract/참조
06_derivatives/        배포 제외 toolchain의 reference-only 기록
tools/verify_archive.py 아카이브 무결성만 확인하는 stdlib 검사기
MANIFEST.sha256        최종 payload 파일별 SHA-256
```

## 검증

압축 해제 후:

```bash
python tools/verify_archive.py
```

또는 압축 파일을 직접 지정:

```bash
python tools/verify_archive.py /path/to/HTT_MES_THREAD_ARCHIVE_20260830.zip
```

이 검사는 파일 보존과 ZIP 무결성을 확인한다. **과거 과학적 결론, 78개 theorem 판정, 실행 receipt의 내용 자체를 재검증하지 않는다.** 기존 결과/철회/한계/실패를 재작성하거나 누락시키지 않았다. 역사적 문서의 PASS와 당시 정책이 현재 authority라는 뜻도 아니다.

`Canonical Memory Verifier`라는 호출 가능한 플러그인은 검색 결과에서 찾지 못했으므로, 그 도구가 이 패키지를 인증했다고 주장하지 않는다.

전체 대화 원문을 완성하려면 해당 스레드의 원문 HTML/JSON/Markdown export와 미확보 원본 첨부를 추가로 제공해야 한다.
