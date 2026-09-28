# 다음 조사에서 유지할 상태

- 원래 목표: 모든 접근 가능한 branch/history의 HTT/MIO/obsstat/BASS legacy/native·코드·JSON·문서·결과를 독립 판정. 내부 claim ceiling을 평가 규칙으로 채택하지 않는다.
- 과학 실행은 사용자의 Local Codex에 위임한다. 이 환경에서는 정적 읽기·이론·원문 대조와 감사 산출물 작성만 한다.
- 고정 주 ref: 5702024e06eff4979087f07f86ee7131d13961ac.
- parallel affine ref: 5a3825f903546891fd90e3d708481707d59babf4.
- 182 refs의 도달 가능한 2,061 commits와 2,003 root trees를 목록으로 확보했다. historical unique blobs 18,885 / paths 11,379. branch-head blobs 8,630.
- 전문 읽기 누적 213 unique blobs, 신규51. 전체 정독 미완료. `read_ledger_cumulative.json`에서 `read_level=full`만 인정하고 SHA로 중복 제거한다.
- R3까지의 GF unrestricted API 반례는 맞지만, v8/v9 수리와 actual caller가 이미 존재한다. R4의 적용 범위 교정을 유지한다.
- CF4 PR145/148의 MLE·nested comparison·결과값 거부 문제와 parallel current-stack의 유효한 affine GLS를 구별한다. 후자의 관측 적용은 미확인이지 부재 증명이 아니다.
- N1–N5 scalar proxy·문헌 귀속·생성 covariance 문제와 PR062의 개선된 방향/깊이 구조를 구별한다.

## 다음 정독 우선순위

1. 이전 partial인 tensorized MES authority·anchor geometry의 나머지와 실제 적용 caller.
2. MIO reference_scale·pair 역할 규칙의 branch/history successor와 영향받는 관측 결과.
3. DESI·JWST·radio·CatWISE의 실제 result producer/manifest 및 figure-to-data 연결.
4. 긴 BASS hierarchy/closure 문서의 미독 부분, 조기 Rust의 repaired successor.
5. historical-only 10,255 blobs의 삭제·수정 계보와 기존 headline의 증거.

## 목록 checkpoint 사용법

`census/history_tree_deltas.json`의 순서대로 읽는다. 각 항목의 `base_tree`가 가리키는 평탄화 snapshot을 복사하고 `changes`를 적용한다. `[path,null,null]`은 삭제이고 나머지는 `[path,blob_sha,byte_size]`다. path 순으로 정렬한 triple 배열을 UTF-8 JSON(`ensure_ascii=false`, 공백 없는 separators)으로 직렬화한 SHA-256이 `normalized_manifest_sha256`와 같아야 한다. 이 방식으로 2,003개 snapshot의 모든 path/blob/size 대응을 재구성할 수 있다.

이 checkpoint는 원래 Git mode·subtree object·raw blob payload를 복원하지 않는다. 새 source는 path/ref 또는 blob SHA로 fetch한 뒤 전문을 실제 읽고 바이트를 확인해야 한다. 단순 inventory·diff·grep은 전문 읽기로 승격하지 않는다.
