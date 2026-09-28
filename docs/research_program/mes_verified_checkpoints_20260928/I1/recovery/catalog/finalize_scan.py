import csv,gzip,hashlib,json,shutil,sqlite3,subprocess,sys,time,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parent;OUT=ROOT/'exports'
s=json.loads((OUT/'scan_summary.json').read_text())
m=json.loads((ROOT/'package/manifest.json').read_text())

def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
    return h.hexdigest()

checks=[]
for name,expected in s['exports'].items():
    p=OUT/(name+'.jsonl.gz')
    with gzip.open(p,'rb') as f: n=sum(1 for line in f)
    if n!=expected['rows']:raise RuntimeError('export count mismatch: '+name)
    checks.append(dict(path=p.name,rows=n,bytes=p.stat().st_size,sha256=sha(p)))
    print(json.dumps(dict(export=name,rows=n,verified=True)),flush=True)

# These replay checks invoke only the export reader, with no SQLite connection.
replays=[]
for args in [['CF4','--limit','2'],['CF4','--topic','CF4','--limit','2'],['MES','--topic','MES_departure','--limit','2']]:
    r=subprocess.run([sys.executable,'-B',str(ROOT/'query_exports.py'),*args],capture_output=True,text=True,check=True)
    rows=[json.loads(x) for x in r.stdout.splitlines()]
    if len(rows)!=2:raise RuntimeError('portable query failed')
    replays.append(dict(args=args,exit_code=r.returncode,rows=rows))

verification=dict(package_commit=s['commit'],database_bytes=m['database_bytes'],database_sha256=m['database_sha256'],part_count=len(m['parts']),part_hashes_verified=True,sqlite_quick_check=s['quick_check'],published_counts_match=s['published_counts_match'],exports=checks,portable_query_replays=replays,original_source_execution=False,proof_verification=False)
(OUT/'verification.json').write_text(json.dumps(verification,ensure_ascii=False,indent=2)+'\n')

labels={'CF4':'CF4·flow 자료','CMB_product_law':'CMB 제품·모의 법칙','full_QO_morphology':'Full Q/O·형태','MES_departure':'MES·departure','local_global':'Local/global·식별','JWST_calibration':'JWST·보정','DESI_Union3':'DESI·Union3','Teff_error':'Teff·근사 오차'}
rows='\n'.join('| '+labels[k]+' | '+format(v['records'],',')+' | '+format(v.get('baseline_records',0),',')+' | '+format(v['files'],',')+' |' for k,v in s['topics'].items())
report=f'''# HTT 카탈로그 다운로드·복원·읽기 전용 스캔

2026-09-12 · owner: HTT catalog review · scope: 정적 검색·후속 원문 취득 준비

고정 배포 커밋: `{s['commit']}`  
카탈로그의 R8 비교 기준: `{s['baseline']['commit']}`

## 실행 결과

- 압축 조각 57개, {sum(p['bytes'] for p in m['parts']):,} bytes를 다운로드했다. 모든 크기·SHA-256이 manifest와 일치했고 재전송은 없었다.
- SQLite {m['database_bytes']:,} bytes를 복원했다. 전체 SHA-256은 `{m['database_sha256']}`이며 기대값과 일치한다.
- SQLite `quick_check`는 `ok`, FTS 레코드 건수는 본 레코드 건수와 일치했다. 전체 `integrity_check`나 과학 코드 실행으로 확대해서 표현하지 않는다.
- 출처 99개, 파일 버전 305,527개, 레코드 1,675,716개, 관계 10,901,211개, 누락 기록 268개를 확인했다. 비교한 게시 건수는 모두 일치한다.
- 다운로드·복원은 약 241초였다. 첫 색인 내보내기는 공간 보호 기준으로 중단되었고, 원인을 정리한 뒤 재개한 스캔은 약 78초였다. 확인된 검사·완료된 내보내기는 재사용했다.

## 공간 사건과 처리

복원 후 임시 디렉터리에 원본·복사 형태의 큰 임시 파일이 남아 가용 공간이 약 2.8 GiB까지 감소했다. 공간 보호가 내보내기를 중단했다. 해당 경로를 열고 있는 프로세스가 없음을 확인한 뒤 이번 복원에서 만든 임시 디렉터리만 삭제해 약 16.4 GiB로 회복했다. 임시 파일이 남은 원인은 확정하지 않았으며 SQLite 손상으로 분류하지 않는다. `space_incident.json`, `space_cleanup.json`에 관찰을 보존했다.

원본 package 복원 함수의 실행 사본은 전송 과정에서 마지막 LF 하나가 추가되었다. 함수·문장 내용은 같고, LF 하나를 제거한 Git blob은 원격 source와 일치한다. 실행 사본의 실제 SHA-256과 원격 identity는 `source_binding.json`에 구분했다.

## 실제 조회 범위

| 주제 | 일치 레코드 | 그중 R8 소속 | 일치 파일 버전 |
|---|---:|---:|---:|
{rows}

주제 사이에 레코드가 중복되므로 행을 합산한 값을 고유 성과 수로 사용하지 않는다. 검색식은 `exports/scan_summary.json`에 보존했다. 코드의 모든 호출·원 논문·관측 원자료를 다시 조사한 것이 아니다. `analysis`, `proposition`, `plan`, `feature`, `evidence`, `port`, `update`, `document` 종류의 일치 항목을 내보냈다. `code` 선언 전체의 본문·모든 검색어에 대한 색인을 새로 만든 것은 아니다.

R8 소속은 고정 baseline의 `members` 및 archive root identity로 판정했다. `observed_commit`은 대표 관찰 버전이고 최초 도입일이나 최신 버전이라는 뜻이 아니다.

## 후속 취득 자료

초기 기계 선정 파일 {s['selected_topic_files']}개와 직접 의존·아카이브 부모를 포함한 {s['acquisition_files']}개 파일 버전을 `acquisition_candidates.csv` 및 JSONL에 담았다. 순서는 검색 편의를 위한 휴리스틱이며 과학적 중요도·검증 상태·필수 다운로드 목록의 확정이 아니다. 코드 자체보다 보고서 생성 스크립트가 높게 잡히는 경우가 있어 원문 단계에서 재선별해야 한다.

- 전체 `files` 305,527행, 출처·참조·커밋·트리·snapshot membership·filesystem·gaps를 별도 압축 JSONL로 보존했다.
- 선정 파일의 관계 47,477개도 보존했다. 이는 전체 10,901,211개 관계의 완전한 대체가 아니다.
- 원문 취득용 경로·source·origin·대표 commit·Git blob·내용 hash(존재하는 경우)·크기·archive container/root를 유지했다.
- 선택한 주제의 요약은 4,000문자까지이며 잘림 여부를 별도 필드로 기록했다. 원문이나 모든 `contents.parsed`를 포함하는 백업은 아니다.
- BASS solver 개발은 HTT 후속 핵심의 대체 목표로 삼지 않는다. 관련 파일이 의존·원문 출처로 포함될 수 있다.
- 로컬 전용 출처와 metadata-only 파일의 실제 원문 가용성은 미확인이다. 원문 검토 후 추가 의존성이 발견될 수 있다.

## DB 없이 사용하는 방법

패키지를 풀고 그 루트에서 다음을 실행한다. Python 표준 라이브러리만 사용한다.

```bash
python3 -B query_exports.py CF4 --limit 20
python3 -B query_exports.py MES --topic MES_departure --limit 20
python3 -B query_exports.py "local boost" --topic local_global --limit 20
```

전체 경로 또는 보존한 주제 발췌에 대한 검색이다. 원래 SQLite FTS 전체와 동일한 기능은 아니다. 실제 DB를 열지 않는 3개 대표 검색을 실행했고 모두 결과를 반환했다. 모든 압축 JSONL의 행 수·gzip 읽기·SHA-256을 검증했다.

`exports/files.jsonl.gz`가 전체 파일 위치 색인이다. 기존 CLI의 `export --kind file`은 `records.kind=file`만 반환하므로 이를 전체 위치 목록의 대용으로 쓰지 않았다.

## 해석 경계

이번 결과의 상태는 **다운로드·복원·카탈로그 조회 확인 완료**다. 원문의 `PASS`, `derived`, `active`는 기록된 주장으로 유지한다. 과학적 타당성, 출판 가능성, 관측 우도 승인 또는 실제 구현 실행 성공을 새로 판정하지 않았다. 추가 연구 원문·관측 원자료는 다운로드하지 않았다. 다음 작업은 후보에서 원문·consumer·현재 수락 상태를 대조하는 것이다.

DB 공간 정리와 최종 저장 상태는 함께 제공되는 `storage_state.json`이 기록한다.
'''
(ROOT/'HTT_CATALOG_SCAN_57ecfe21_KO.md').write_text(report,encoding='utf-8')
(ROOT/'verification_before_storage.json').write_text(json.dumps(dict(verified_exports=len(checks),export_compressed_bytes=sum(x['bytes'] for x in checks),portable_replays=len(replays),time=time.time()),indent=2))
print('FINALIZE_CHECKS_COMPLETE',flush=True)
