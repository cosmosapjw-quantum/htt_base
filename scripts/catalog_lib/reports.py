"""Generate navigation documents from the same SQLite snapshot as CLI queries."""
from __future__ import annotations

import csv
import json
from pathlib import Path
from urllib.parse import quote

from .db import counts, get_meta, identity, js, reindex
from .query import query, check
from .scan import Scanner


def cell(value, limit=220):
    value=str(value or '').replace('|','\\|').replace('\n',' ')
    return value if len(value)<=limit else value[:limit]+'…'


def add_curation(c, path):
    """Curated guides remain annotated source summaries, not scientific verdicts."""
    path=Path(path)
    if not path.exists():return
    payload=json.loads(path.read_text())
    scope=get_meta(c,'scope',{})
    scanner=Scanner(c,scope)
    if get_meta(c,'record_view_version')!='2':
        scanner.refresh_record_views()
        scanner.resolve_edges()
    scanner.refresh_record_states()
    scanner.source('navigation_annotations','curated_navigation',str(path),history_scope='catalog_annotation')
    fid=scanner.material('navigation_annotations','curation.json',path.read_bytes())
    for card in payload['cards']:
        rid=identity(fid,'analysis',card['id'])
        c.execute('INSERT OR REPLACE INTO records VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)',
            (rid,fid,card['id'],'analysis',card['title'],card['owner'],'korean',
             'curated_navigation_candidate','',card['evidence_level'],None,None,card['question'],js(card)))
        for ref in card['source_refs']:
            targets=c.execute('SELECT f.id FROM files f JOIN members m ON f.id=m.file_id WHERE m.source_id=? AND m.commit_sha=? AND f.path=?',
                (scope['baseline_source'],scope['baseline_commit'],ref)).fetchall()
            scanner.edge(rid,'references',ref,'baseline_source_file_present' if len(targets)==1 else 'unresolved_at_source_version',
                         targets[0][0] if len(targets)==1 else None,bound_commit=scope['baseline_commit'])
    reindex(c);c.commit()


def source_link(c,row,commit=None):
    source=c.execute('SELECT origin,kind FROM sources WHERE id=?',(row['source_id'],)).fetchone()
    path=row['path']
    commit=commit or row.get('observed_commit')
    if source and source['origin'] and commit and '!/' not in path:
        origin=source['origin'].removesuffix('.git')
        if origin.startswith('https://github.com/'):
            link=origin+'/blob/'+commit+'/'+quote(path,safe='/')
            if row.get('line') and row['line']>1:link+='#L'+str(row['line'])
            return f'[{cell(path,150)}]({link})'
    return '`'+cell(row['source_id']+':'+path,170)+'`'


def write_reports(c, directory, curation=None):
    out=Path(directory);out.mkdir(parents=True,exist_ok=True)
    base=get_meta(c,'baseline');summary=counts(c);scope=get_meta(c,'scope',{})
    summary['unique_commit_objects']=c.execute('SELECT count(DISTINCT sha) FROM commits').fetchone()[0]
    summary['commit_aliases']=c.execute('SELECT count(*) FROM commit_aliases').fetchone()[0]
    summary['registered_worktrees']=len(scope.get('worktrees',[]))
    summary['main_project_commits']=c.execute('SELECT count(*) FROM commits WHERE source_id=?',(base['source_id'],)).fetchone()[0]
    summary['pre_rewrite_commits']=c.execute("SELECT count(*) FROM commits WHERE source_id='htt_pre_rewrite'").fetchone()[0]
    summary['unique_content_bytes']=c.execute("SELECT count(DISTINCT substr(id,1,64)) FROM contents").fetchone()[0]
    summary['physical_file_locations']=c.execute("SELECT count(*) FROM filesystem WHERE kind='file'").fetchone()[0]
    summary['distinct_regular_file_inodes']=c.execute("SELECT count(*) FROM (SELECT DISTINCT device,inode FROM filesystem WHERE kind='file')").fetchone()[0]
    summary['physical_alias_locations']=c.execute("SELECT count(*) FROM filesystem fs JOIN files f ON fs.file_id=f.id WHERE fs.source_id<>f.source_id").fetchone()[0]
    summary['baseline_file_count']=c.execute('SELECT count(*) FROM members WHERE source_id=? AND commit_sha=?',(base['source_id'],base['commit'])).fetchone()[0]
    summary['baseline_record_counts']=dict(c.execute('SELECT r.kind,count(*) FROM records r JOIN files f ON r.file_id=f.id JOIN members m ON m.file_id=COALESCE(f.root_file_id,f.id) WHERE m.source_id=? AND m.commit_sha=? GROUP BY r.kind',(base['source_id'],base['commit'])).fetchall())
    summary['scope_note']='Counts distinguish logical file versions, code/claim records, physical locations and dependency metadata; none count proven science.'
    (out/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')

    lines=['# 조사 범위와 누락','',f"기준 비교 버전: `{base['source_id']}:{base['commit']}`.",'',
      '아래 수치는 카탈로그 레코드/버전/위치의 수다. 독립 구현 수나 증명된 명제 수를 뜻하지 않는다.','',
      '| 구분 | 수 |','|---|---:|']
    for title,key in [('현재 HTT Git 커밋','main_project_commits'),('이력 정리 이전 커밋','pre_rewrite_commits'),
                      ('구·신 커밋 대응','commit_aliases'),('등록 작업트리','registered_worktrees'),
                      ('의존성·외부 저장소 포함 커밋 기록','commits'),('서로 다른 커밋 객체','unique_commit_objects'),
                      ('추출된 파일 버전과 자산 항목','files'),('서로 다른 본문 바이트','unique_content_bytes'),
                      ('기준 버전 추적 파일','baseline_file_count'),('물리 파일 위치','physical_file_locations'),
                      ('물리 정규 파일 inode','distinct_regular_file_inodes'),('기존 코드 버전에 연결된 물리 별칭','physical_alias_locations'),
                      ('의미별 레코드','records'),('참조/호출/대체 관계','edges'),('별도 사유가 있는 처리 항목','gaps')]:
        lines.append(f'| {title} | {summary[key]:,} |')
    for title,key in [('파일 처리 상태','files_by_status'),('레코드 종류','records_by_kind'),('기준 R8 레코드','baseline_record_counts'),('누락·제한 사유','gaps_by_status'),('관계 해석 상태','edges_by_resolution')]:
        lines+=['',f'## {title}','','| 상태 | 수 |','|---|---:|']
        lines += [f'| `{k}` | {v:,} |' for k,v in sorted(summary[key].items())]
    lines+=['','## 출처별 범위','','| 출처 | 종류 | Git 커밋 기록 | 경로 |','|---|---|---:|---|']
    for row in c.execute('SELECT s.*,count(c.sha) AS n FROM sources s LEFT JOIN commits c ON s.id=c.source_id GROUP BY s.id ORDER BY s.id'):
        lines.append(f"| `{row['id']}` | {row['kind']} | {row['n']:,} | `{cell(row['locator'],230)}` |")
    lines+=['','## 분모와 처리 한계','',
      '- Git 이력은 선언된 로컬 객체에서 조사했다. 설치된 일반 Lean 의존성은 커밋·참조·버전 정보이며 내부 구현을 HTT 코드/명제로 세지 않는다.',
      '- 아카이브 내부 경로는 `archive.zip!/member`로 표시한다. 제한·암호화·손상·구문 오류는 원문을 수정하지 않고 남긴다.',
      f"- 텍스트 상한 {scope.get('text_limit_bytes',0):,} bytes, 아카이브 상한 {scope.get('archive_limit_bytes',0):,} bytes, 중첩 깊이 {scope.get('archive_depth')}이다. 상한 초과는 파일 존재 목록에 남는다.",
      '- PDF는 텍스트만 추출했다. 도형·수식의 정확성, OCR, 렌더링은 검수하지 않았다.',
      '- Python 외 언어는 선언 중심 lexical 추출이다. 매크로·주석·복잡한 스코프의 해석 한계가 있으며 컴파일 성공을 의미하지 않는다.',
      '- 미커밋 자료는 조사 시점의 원문과 메타데이터다. 재수집 때 변할 수 있으며 원문은 이 배포에 복사하지 않는다.',
      '- 파일 수집 완료율과 명제 의미 해석의 완전성은 다르다. 선언을 추출하지 못한 파일도 상태와 경로로 찾을 수 있다.',
      '- 생성 카탈로그와 캐시를 다시 읽지 않도록 이번 카탈로그 작업 디렉터리를 제외했다. 도구 자체 소스는 배포 Git 브랜치에서 확인한다.',
      '- 오래된 소스의 실제 구문 오류·누락 참조는 원문 상태로 보존했다. 이 카탈로그 작업에서 연구 코드를 고치거나 재실행하지 않았다.',
      '', '전체 사유는 `coverage_gaps.csv`, 모든 물리 위치는 DB `filesystem`, 파일 버전은 `files`에서 조회한다.','']
    (out/'COVERAGE.md').write_text('\n'.join(lines))
    with (out/'coverage_gaps.csv').open('w',newline='') as f:
        rows=c.execute('SELECT * FROM gaps ORDER BY source_id,path,operation');w=csv.writer(f,lineterminator='\n')
        w.writerow([x[0] for x in rows.description]);w.writerows(rows)

    index=['# 생성 목록','', '기준 R8의 정적 목록이다. 모든 버전은 CLI의 `--ref all`과 `--limit -1`로 조회한다.',
           '표의 ID는 `show`/`history`의 인자다. 상태는 원문 기록 또는 정적 분류이며 실행·증명 완료 판정이 아니다.','']
    listing_dir=out/'lists';listing_dir.mkdir(exist_ok=True)
    for kind,title in [('feature','모듈과 기능'),('port','이식·마이그레이션 원문 기록'),('analysis','분석 진입점 후보'),('proposition','명제·증명 기록·후보'),('plan','계획·예비 구현'),('update','구체적 후속 확인 항목')]:
        rows=query(c,kind=kind,ref='baseline',limit=-1)
        index.append(f'- {title}: {len(rows):,}개 버전 레코드')
        for part in range(0,len(rows),100):
            name=f'{kind}-{part//100+1:03d}.md'
            index.append(f'  - [{part+1}–{min(part+100,len(rows))}](lists/{name})')
            page=[f'# {title} {part+1}–{min(part+100,len(rows))}','', '[목록으로 돌아가기](../LISTS.md)','',
                  '| ID | 이름 | 정적 상태 / 원문 상태 | 출처 |','|---|---|---|---|']
            for row in rows[part:part+100]:
                page.append(f"| `{row['id']}` | {cell(row['name'])} | `{row['status']}` / {cell(row['recorded_status'],90)} | {source_link(c,row,base['commit'])} |")
            (listing_dir/name).write_text('\n'.join(page)+'\n')
    index+=['','전체 코드 심볼은 용량과 탐색성을 위해 DB/CSV로 제공한다. 예:', '',
            '```bash','python3 -B scripts/project_catalog.py export --kind code --ref all --limit -1 --format csv --output /tmp/all-code-versions.csv','```','']
    (out/'LISTS.md').write_text('\n'.join(index))

    propositions=query(c,kind='proposition',ref='baseline',limit=-1)
    from collections import Counter
    grouped=Counter(r['status'] for r in propositions)
    proof_guide=['# 명제·증명 기록 읽기','',
        'R8에 포함된 파일에서 추출한 명제 관련 레코드다. 같은 ID의 서로 다른 버전·가정과 문서 섹션도 각각 세며, 독립 명제나 증명된 정리의 개수가 아니다.','',
        '| 정적/원문 상태 분류 | R8 레코드 수 |','|---|---:|']
    proof_guide += [f'| `{status}` | {n:,} |' for status,n in sorted(grouped.items())]
    proof_guide += ['',
        '`recorded_proven_or_derived`는 기록상 증명·유도 주장, `recorded_conditional`은 조건부 기록, `candidate`는 후보 표기다. 철회·대체 기록과 unresolved 기록도 그대로 남는다.',
        '`declaration_present`는 Lean 선언 등의 존재이고 `textual_statement`는 문서 명제 구절이다. 이 둘을 증명 완료 상태로 바꾸지 않는다.',
        '', '## 근거를 확인하는 순서','',
        '1. `query --kind proposition`으로 ID를 얻고 `show ID`에서 원문, 가정, 정의역, source pointer와 관찰 버전을 읽는다.',
        '2. `proof_evidence`에서 원문의 증명 주장, 참조 파일 존재, 참조 기록의 명제 ID 일치를 구별한다. 근거 파일이 없으면 `NO_BOUND_REFERENCE`로 남는다.',
        '3. `relationships`의 버전과 `ref_membership`을 확인한다. 파일 존재와 같은 ID만으로 가정 일치나 과학적 검증을 추론하지 않는다.',
        '4. `history ID`와 같은 registered ID의 다른 원문을 함께 읽어 조건 변경·철회·대체를 확인한다. 원문 근거가 없는 대체 관계는 미해결로 남는다.',
        '', '이번 조사에서 새로 증명된 명제는 없다. 상세 정적 목록은 [생성 목록](LISTS.md), 기록을 읽는 경계는 [구조 문서](ARCHITECTURE.md)에 있다.','']
    (out/'PROPOSITIONS.md').write_text('\n'.join(proof_guide))

    cards=json.loads(Path(curation).read_text())['cards'] if curation else []
    guide=['# 기능·분석 길잡이','',
      '아래 카드는 소스의 연구 질문과 입력·출력을 연결하는 탐색 안내다. 레지스트리에 남은 오래된 주장도 포함하므로 각 카드의 버전·가정을 함께 읽는다.',
      '연구 코드·분석·증명 도구는 실행하지 않았다. 현재 실행 가능성이 확인된 분석 목록으로 사용하지 않는다.','']
    for card in cards:
        guide += [f"## {card['id']} — {card['title']}",'',card['question'],'',
          f"- 소유 표기: {card['owner']}",f"- 입력: {'; '.join(card['inputs'])}",
          f"- 출력·등록 결과: {'; '.join(card['outputs'])}",f"- 실행 정보: {card['command']}",
          f"- 상태와 한계: {card['status_caveats']}",f"- 후속 확인: {'; '.join(card['update_needs'])}",
          '- 원문: '+', '.join(f'[{p}](https://github.com/cosmosapjw-quantum/htt_base/blob/{card["basis_commit"]}/{quote(p,safe="/")})' for p in card['source_refs']),
          '', '관련 코드·기록 조회:', '', '```bash']
        for term in card['search_terms'][:3]:guide.append(f'python3 -B scripts/project_catalog.py query --ref baseline --q "{term}" --limit 15')
        guide+=['```','']
    (out/'CAPABILITIES.md').write_text('\n'.join(guide))
    (out/'checks.json').write_text(json.dumps(check(c),ensure_ascii=False,indent=2)+'\n')
    return summary
