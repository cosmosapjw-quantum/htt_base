"""Read-only, evidence-reviewed proof lists derived from the existing catalog.

Confirmation means that an existing proof's scoped support was reviewed. This
module neither proves mathematics nor admits an old result to current science.
"""
from __future__ import annotations

from collections import Counter, defaultdict
import csv
import gzip
import hashlib
import json
from pathlib import Path
import re
from contextlib import contextmanager
import io

from .db import get_meta, identity, js, version_members

VERSION = 1
PROOF_WORDS = re.compile(r'(?<![A-Za-z])(?:proof\w*|prov(?:e|ed|ing|able)\w*|unprov\w*|theorem\w*|lemma\w*|proposition\w*|conjectur\w*|deriv(?:e|ed|ation)\w*)(?![A-Za-z])|증명|명제|추측', re.I)
PROPOSAL_WORDS = re.compile(r'(?<![A-Za-z])(?:propos\w*|conjectur\w*|todo|planned|unfinished|unprov\w*|obligation\w*|prove|establish)(?![A-Za-z])|증명.{0,15}(?:제안|필요|미완|의무)|명제|추측', re.I)
CONFIRMED = 'existing_proof_support_confirmed'
UNCONFIRMED = 'proof_completion_unconfirmed'
EXCLUDED = 'excluded_non_proposition'
REASONS = {
    'reviewed_existing_proof': '기존 증명·유도 근거와 명제 범위 대응 확인',
    'proposed_or_incomplete': '제안·미완성 또는 남은 증명 의무',
    'conditional_support_unconfirmed': '조건부 표기이며 해당 조건의 증명 완료 미확인',
    'recorded_proof_without_aligned_support': '증명·유도 표기는 있으나 적용 근거 대조 미완료',
    'declaration_without_bound_proof_record': '선언 존재만 확인; 대응하는 기존 증명 기록 미확인',
    'validation_is_not_proof': '검증·PASS 표기만으로 증명 완료를 판정할 수 없음',
    'unresolved_record': '원문에서 미해결·보류로 기록',
    'retracted_record': '철회된 버전의 기록',
    'superseded_record': '대체된 버전의 기록',
    'statement_or_support_unconfirmed': '명제 범위 또는 증명 근거 추가 대조 필요',
    'general_reference_or_tooling': '증명 관련 일반 언급·도구·실행 기록이며 명제 제안으로 확인되지 않음',
    'historical_compile_failure': '해당 소스 버전의 기존 컴파일 실패 기록',
    'source_proof_without_bound_build_record': '증명 소스는 있으나 같은 버전의 성공한 빌드 근거 미확인',
    'recorded_claim_missing_exact_proof_body': '기록상 증명 표기와 대응하는 정확한 증명 본문 미확인',
    'contract_readiness_is_not_mathematical_proof': '구현 계약의 준비 상태이며 수학 명제가 아님',
    'raw_text_proposal_unreviewed': '추가 원문 검색의 명제·증명 제안; 증명 범위 대조 미완료',
}


def digest(value):
    return hashlib.sha256(js(value).encode()).hexdigest()


def record_digest(row):
    # Only persisted catalog columns; derived evidence may not silently follow
    # a changed statement, assumption, source version or extraction.
    return digest({k: row[k] for k in ['id','file_id','local_id','kind','name','owner','language',
        'status','recorded_status','line','end_line','summary','details','source_id','path',
        'observed_commit','git_blob','content_id']})


def discover_records(c, supplemental=()):
    """Account for all propositions plus explicit proof-related discovery hits.

    SQL narrows the large table; Python handles token boundaries and Korean.
    Names, excerpts and structured details are searched, not only FTS paths.
    """
    clauses = ["kind='proposition'"]
    for term in ['proof','prov','theorem','lemma','proposition','conjectur','deriv','증명','명제','추측']:
        clauses.append("instr(lower(name||' '||summary||' '||details), '" + term + "')>0")
    for raw in c.execute('SELECT * FROM catalog WHERE ' + ' OR '.join(clauses) + ' ORDER BY id'):
        row = dict(raw)
        if row['kind'] == 'proposition' or PROOF_WORDS.search(row['name']+' '+row['summary']+' '+row['details']):
            yield row
    for candidate in supplemental:
        for raw in c.execute('SELECT * FROM files WHERE content_id=? ORDER BY id', (candidate['content_id'],)):
            f = dict(raw)
            yield dict(f, id='discovery:'+identity(candidate['candidate_id'],f['id']), file_id=f['id'],
                root_file_id=f['root_file_id'] or f['id'], local_id=candidate['candidate_id'],
                kind='annotation', name=candidate['title'], owner='UNKNOWN',
                status='raw_text_proposal' if candidate['is_proposal'] else 'general_reference',
                recorded_status='', line=candidate['line'], end_line=candidate['line'],
                summary=candidate['text'], details=js({'extraction':'supplemental_raw_source_search',
                    'source_pointer':candidate['locator'],'candidate_id':candidate['candidate_id'],
                    'excerpt_truncated':candidate['excerpt_truncated']}),evidence_level='raw_source_text')


def default_classification(row):
    details = json.loads(row['details'])
    if details.get('extraction') == 'supplemental_raw_source_search':
        return (UNCONFIRMED,'raw_text_proposal_unreviewed') if row['status']=='raw_text_proposal' else (EXCLUDED,'general_reference_or_tooling')
    if row['kind'] != 'proposition':
        text = row['name'] + ' ' + row['summary']
        # Code implementing a test/prover is not itself a proposition. Explicit
        # docstring/comment obligations remain review candidates.
        proposed = PROPOSAL_WORDS.search(text) and row['kind'] in {'plan','annotation','document','evidence','feature','code'}
        if not proposed and not details.get('proof_obligations'):
            return EXCLUDED, 'general_reference_or_tooling'
    reasons = {
        'recorded_retracted': 'retracted_record', 'recorded_superseded': 'superseded_record',
        'recorded_unresolved': 'unresolved_record', 'candidate': 'proposed_or_incomplete',
        'recorded_conditional': 'conditional_support_unconfirmed',
        'recorded_proven_or_derived': 'recorded_proof_without_aligned_support',
        'declaration_present': 'declaration_without_bound_proof_record',
        'recorded_validation_claim': 'validation_is_not_proof',
    }
    return UNCONFIRMED, reasons.get(row['status'], 'statement_or_support_unconfirmed')


def load_reviews(c, path):
    payload = json.loads(Path(path).read_text()) if path else {'schema_version':1,'reviews':[]}
    if payload.get('schema_version') != VERSION:
        raise ValueError('unsupported proof review schema')
    if payload.get('baseline') and payload['baseline'] != get_meta(c, 'baseline'):
        raise ValueError('proof review baseline differs from catalog')
    indexed = {}
    for review in payload['reviews']:
        verdict = review.get('classification')
        if verdict not in {CONFIRMED, UNCONFIRMED, EXCLUDED}:
            raise ValueError('unregistered proof classification')
        if not review.get('review_id') or not review.get('reason') or not review.get('bindings'):
            raise ValueError('review needs identity, reason and exact bindings')
        if verdict == CONFIRMED:
            for field in ['statement','assumptions','domain','conventions','scope','alignment','limitations','evidence']:
                if not review.get(field):
                    raise ValueError('confirmed review missing ' + field)
            if not any(e.get('kind') in {'proof_text','compiled_proof_source'} for e in review['evidence']):
                raise ValueError('file/status/receipt existence is not a proof anchor')
        for evidence in review.get('evidence', []):
            f = c.execute('SELECT * FROM files WHERE id=?', (evidence['file_id'],)).fetchone()
            if f is None or not f['content_id'] or f['content_id'].split(':')[0] != evidence['content_sha256']:
                raise ValueError('evidence source is absent or has changed')
            if evidence.get('text') is not None:
                if hashlib.sha256(evidence['text'].encode()).hexdigest() != evidence['excerpt_sha256']:
                    raise ValueError('evidence excerpt differs from reviewed text')
            if not evidence.get('locator'):
                raise ValueError('evidence needs a scoped line/section/pointer locator')
        for binding in review['bindings']:
            row = c.execute('SELECT * FROM catalog WHERE id=?', (binding['record_id'],)).fetchone()
            if row is None or record_digest(dict(row)) != binding['record_sha256']:
                raise ValueError('proof review record binding is absent or has changed')
            if row['id'] in indexed:
                raise ValueError('conflicting/duplicate proof reviews for one record')
            if verdict == CONFIRMED and row['status'] in {'recorded_retracted','recorded_superseded'}:
                raise ValueError('withdrawn/superseded occurrence cannot be confirmed')
            indexed[row['id']] = review
    return payload, indexed


def load_discovery(c, payload, reviews_path):
    info = payload.get('supplemental_discovery')
    if not info:
        return [], None
    raw = (Path(reviews_path).parent/info['file']).read_bytes()
    if hashlib.sha256(raw).hexdigest() != info['sha256']:
        raise ValueError('supplemental source discovery has changed')
    data = json.loads(gzip.decompress(raw) if info['file'].endswith('.gz') else raw)
    for x in data['candidates']:
        if not c.execute('SELECT 1 FROM contents WHERE id=?',(x['content_id'],)).fetchone():
            raise ValueError('supplemental discovery source missing from catalog')
    return data['candidates'],data['summary']


def source_link(row):
    if row['source_id'] == 'htt_base' and row['observed_commit'] and '!/' not in row['path']:
        from urllib.parse import quote
        return 'https://github.com/cosmosapjw-quantum/htt_base/blob/' + row['observed_commit'] + '/' + quote(row['path']) + (f"#L{row['line']}" if row.get('line') else '')
    return ''


def build_lists(c, reviews_path=None):
    review_payload, reviews = load_reviews(c, reviews_path)
    supplemental, source_scan = load_discovery(c,review_payload,reviews_path)
    baseline = get_meta(c, 'baseline', {})
    baseline_ids = set(version_members(c, baseline['source_id'], baseline['commit'])) if baseline else set()
    edges = defaultdict(list)
    for e in c.execute("SELECT * FROM edges WHERE relation IN ('references','supersedes','superseded_by') ORDER BY id"):
        edges[e['from_id']].append({k:e[k] for k in ['relation','target','target_id','resolution']})
    groups, occurrences = {}, []
    counters = Counter()
    seen_reviews = set()
    for row in discover_records(c,supplemental):
        counters['discovery_records'] += 1
        counters['original_proposition_records' if row['kind']=='proposition' else 'additional_discovery_records'] += 1
        details = json.loads(row['details'])
        review = reviews.get(row['id'])
        classification, reason = default_classification(row)
        if review:
            seen_reviews.add(row['id'])
            classification, reason = review['classification'], review['reason']
        counters[classification+'_records'] += 1
        conditions = {k:details[k] for k in ['assumptions','conditions','domain','conventions','units','scope','claim_tier','transfer_source'] if k in details}
        statement = review['statement'] if review and review.get('statement') else row['summary'] or row['name']
        if classification==EXCLUDED:
            statement=statement[:500]
        # Exact source-local identity, not semantic similarity: no same-ID or
        # same-title merging across edited statements/assumptions/evidence.
        group_key = [row['content_id'] or row['file_id'], row['kind'], row['local_id'],row['language'],
            row['name'], row['summary'], row['recorded_status'], row['details'],
            classification, reason, digest({k:v for k,v in review.items() if k not in {'review_id','bindings'}}) if review else None,
            sorted((e['relation'],e['target'],e['target_id'] or '',e['resolution']) for e in edges[row['id']])]
        gid = identity('proof-list-v1', *group_key)
        if gid not in groups:
            groups[gid] = {
                'item_id':gid,'registered_id':details.get('registered_id'), 'title':row['name'],
                'classification':classification,'reason':reason,'reason_ko':REASONS.get(reason,reason),
                'owner':row['owner'],'language':row['language'],'statement':statement,
                'owners':[],
                'statement_completeness':'excluded_search_hit_excerpt' if classification==EXCLUDED else 'reviewed_exact_scope' if review and review.get('statement') else 'catalog_excerpt; full_statement_not_guaranteed',
                'conditions':conditions,'recorded_status':row['recorded_status'],'catalog_status':row['status'],
                'conditions_completeness':'reviewed_literal_scope' if review and review.get('assumptions') else 'NOT_FULLY_REVIEWED',
                'source_record_excerpt':details.get('source_record_excerpt',''),
                'proof_obligations':details.get('proof_obligations',[]),
                'followup':review.get('followup') if review else '명제 전체·가정·대상 버전과 해당 범위의 증명 원문을 대조하고, 남은 의무/상충 기록을 확인한다.',
                'review_id':review['review_id'] if review else None,
                'reviewed_support':{k:review[k] for k in ['assumptions','domain','conventions','scope','alignment','limitations','evidence','proof_method'] if k in review} if review else None,
                'proof_reexecution':'NOT_EXECUTED','scientific_admission':'NOT_EVALUATED',
                'r8_source_present':False,'r8_proof_applicability':'NOT_ESTABLISHED_BY_MEMBERSHIP',
                'occurrence_ids':[],
            }
        item = groups[gid]
        if row['owner'] not in item['owners']:item['owners'].append(row['owner']);item['owners'].sort()
        in_r8 = row['root_file_id'] in baseline_ids
        item['r8_source_present'] |= in_r8
        item['occurrence_ids'].append(row['id'])
        occurrences.append({'record_id':row['id'],'item_id':gid,'file_id':row['file_id'],
            'kind':row['kind'],'classification':classification,'source_id':row['source_id'],
            'owner':row['owner'],'language':row['language'],
            'path':row['path'],'line':row['line'],'source_pointer':details.get('source_pointer',''),
            'observed_commit':row['observed_commit'],'git_blob':row['git_blob'],
            'content_id':row['content_id'],'r8_source_present':in_r8,'source_url':source_link(row),
            'relationships':edges[row['id']]})
    if seen_reviews != set(reviews):
        raise ValueError('review contains a record outside declared discovery')
    items = sorted(groups.values(), key=lambda x:(x['title'],x['item_id']))
    total_prop = c.execute("SELECT count(*) FROM records WHERE kind='proposition'").fetchone()[0]
    if counters['original_proposition_records'] != total_prop:
        raise ValueError('proposition coverage mismatch')
    counters.update({state+'_items':sum(x['classification']==state for x in items) for state in [CONFIRMED,UNCONFIRMED,EXCLUDED]})
    summary = {'schema_version':VERSION,'baseline':baseline,'counts':dict(sorted(counters.items())),
        'unconfirmed_reasons':dict(sorted(Counter(x['reason'] for x in items if x['classification']==UNCONFIRMED).items())),
        'unconfirmed_reason_labels':{k:REASONS[k] for k in sorted({x['reason'] for x in items if x['classification']==UNCONFIRMED})},
        'reviewed_records':len(reviews),'reviewed_units':len(review_payload['reviews']),
        'raw_source_discovery':source_scan,
        'confirmed_proof_methods':dict(sorted(Counter(x['reviewed_support'].get('proof_method','written_derivation') for x in items if x['classification']==CONFIRMED).items())),
        'r8_source_present_items':dict(sorted(Counter(x['classification'] for x in items if x['r8_source_present']).items())),
        'original_recorded_proven_records':c.execute("SELECT count(*) FROM records WHERE kind='proposition' AND status='recorded_proven_or_derived'").fetchone()[0],
        'deduplication':'exact source-content/local-record/status/evidence grouping; not a count of mathematically distinct theorems',
        'proof_reexecution':'NOT_EXECUTED','scientific_admission':'NOT_EVALUATED',
        'scope':'all catalog versions; additional proof-related names, excerpts and structured fields; no acquisition CSV restriction',
        'checks':{'all_proposition_records_accounted':True,'all_discovery_records_accounted':sum(len(x['occurrence_ids']) for x in items)==counters['discovery_records'],
                  'review_bindings_valid':True,'unique_occurrence_partition':len({x['record_id'] for x in occurrences})==len(occurrences)}}
    return items, occurrences, summary


def write_json(path, value):
    Path(path).write_text(json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':'))+'\n')


def cell(value):
    return str(value or '').replace('|','\\|').replace('\n',' ').replace('[','\\[').replace(']','\\]').replace('<','&lt;').replace('>','&gt;')


@contextmanager
def compressed_text(path):
    # No filename or timestamp in the gzip header: repeat exports are identical.
    with Path(path).open('wb') as raw:
        with gzip.GzipFile(fileobj=raw,mode='wb',filename='',mtime=0,compresslevel=6) as stream:
            with io.TextIOWrapper(stream,encoding='utf-8',newline='') as text:
                yield text


def write_occurrence_parts(directory, rows, limit=32*1024**2):
    directory=Path(directory);directory.mkdir(parents=True,exist_ok=True)
    parts=[];pending=[];size=0
    def flush():
        name=f'part-{len(parts)+1:04d}.jsonl.gz'
        with compressed_text(directory/name) as f:f.writelines(pending)
        parts.append({'file':name,'rows':len(pending),'uncompressed_bytes':size,
            'sha256':hashlib.sha256((directory/name).read_bytes()).hexdigest()})
    for row in rows:
        line=js(row)+'\n';length=len(line.encode('utf-8'))
        if length>limit:raise ValueError('single occurrence exceeds part size limit')
        if pending and size+length>limit:flush();pending=[];size=0
        pending.append(line);size+=length
    if pending:flush()
    wanted={p['file'] for p in parts}
    for p in directory.glob('part-*.jsonl.gz'):
        if p.name not in wanted:p.unlink()
    write_json(directory/'index.json',{'parts':parts,'rows':sum(p['rows'] for p in parts)})


def summary_tables(summary):
    counts=summary['counts']
    lines=['','## 중복 정리 전후와 R8','','| 분류 | 원본 레코드 | 항목 묶음 | R8 원문 포함 묶음 |','|---|---:|---:|---:|']
    for state,label in [(CONFIRMED,'근거 확인'),(UNCONFIRMED,'완료 미확인'),(EXCLUDED,'일반 언급 등 제외')]:
        lines.append(f"| {label} | {counts[state+'_records']:,} | {counts[state+'_items']:,} | {summary['r8_source_present_items'].get(state,0):,} |")
    lines+=['',f"검토 입력 {summary['reviewed_units']:,}개 단위가 원본 {summary['reviewed_records']:,}개 레코드에 직접 연결된다. 나머지는 보수적 추출 규칙에 따른 미확인 또는 제외다. 모든 문장을 사람이 개별 수학 심사했다는 뜻이 아니다.",'']
    if summary.get('raw_source_discovery'):
        scan=summary['raw_source_discovery']
        lines += [f"추가 원문 검색: 내용 버전 {scan['content_versions']:,}개, 파일 위치·버전 {scan['file_occurrences']:,}개, 추가 검색 문장 구간 {scan['candidate_windows']:,}개.",
            f"원문 재독 불가/변경 {scan.get('source_unavailable_or_changed',0):,}개, 빈 비문서 등 미지원 내용 {scan.get('unsupported_binary',0):,}개. PDF는 텍스트 대조에 한정한다. `source_scan.csv`의 오류 열은 최초 오류도 보존하며 최종 판정은 처리 상태 열을 사용한다.",'']
    return '\n'.join(lines)+'\n'


def write_markdown(directory, by_id, state, stem, title, subset):
    lines=[f'# {title}','',f'항목 묶음 {len(subset):,}개. 전체 원문 레코드·버전 연결은 `occurrences/index.json`의 압축 조각, 상세 조건과 근거는 `{stem}.json'+('.gz' if state==EXCLUDED else '')+'`을 참조한다.',
        '', '기존 증명 근거의 정적 대조 결과다. 이번 작업에서 재증명·연구 실행·과학적 승격을 수행하지 않았다.',
        'R8 원문 포함 여부는 R8에서의 증명 적용성 판정과 다르다. 미확인은 반증이나 거짓을 뜻하지 않는다.','',
        '| ID | 명제·제안 | 원문 상태 | R8 원문 | 분류 사유 | 원문/근거 |',
        '|---|---|---|---|---|---|']
    for item in (subset if state!=EXCLUDED else []):
        occurrence=by_id[item['occurrence_ids'][0]]
        link=f"[{cell(occurrence['path'])}]({occurrence['source_url']})" if occurrence['source_url'] else cell(occurrence['path'])
        item_link=item['item_id']
        if state==CONFIRMED:
            source_hash=item['reviewed_support']['evidence'][0]['content_sha256'][:16]
            item_link=f"[{item['item_id']}](confirmed_details/{source_hash}.md#{item['item_id']})"
        lines.append('| '+' | '.join([item_link,cell(item['title']),cell(item['recorded_status']),
            '포함' if item['r8_source_present'] else '미포함',cell(item['reason_ko']),link])+' |')
    if state==CONFIRMED:
        detail_pages={}
        for item in subset:
            support=item['reviewed_support']
            source_hash=support['evidence'][0]['content_sha256'][:16]
            detail=detail_pages.setdefault(source_hash,['# 기존 증명 근거의 버전별 상세','',
                '[확인 목록으로 돌아가기](../confirmed.md)','',
                '고정 입력 계산이나 조건부 보조정리를 더 넓은 연구 명제의 완료로 해석하지 않는다. 이번 작업에서 증명 도구를 재실행하지 않았다.',''])
            detail += [f'<a id="{item["item_id"]}"></a>',f"### {cell(item['title'])} — {item['item_id']}", '',
                '```lean',item['statement'],'```','',
                f"- 소속: {item['owner']}; 원문 상태: {cell(item['recorded_status']) or '(미기재)'}.",
                '- 근거 방식: '+support.get('proof_method','written_derivation')+'.',
                '- 적용 범위: '+cell(support['scope']),
                '- 가정: '+cell(support['assumptions']),
                '- 제한: '+cell(support['limitations']),
                '- 후속 확인: '+cell(item['followup']), '', '기존 증명 및 기록:', '']
            for e in support['evidence']:
                detail.append(f"- `{e.get('path',e['file_id'])}` — {e['locator']}; 파일 ID `{e['file_id']}`; 소스 SHA-256 `{e['content_sha256']}`; 관찰 커밋 `{e.get('observed_commit') or '해당 없음'}`.")
            detail += ['']
        (directory/'confirmed_details').mkdir(exist_ok=True)
        for key,detail in detail_pages.items():(directory/'confirmed_details'/(key+'.md')).write_text('\n'.join(detail)+'\n')
    if state==UNCONFIRMED and len(subset)>250:
        header=lines[:9];table_rows=lines[9:]
        pages=directory/'unconfirmed_pages';pages.mkdir(exist_ok=True)
        lines=lines[:7]+['## 전체 목록 페이지','', '각 페이지는 제목순 최대 250개 항목을 담는다. 전체 데이터는 [CSV](unconfirmed.csv), [JSON](unconfirmed.json)에 있다.','']
        for start in range(0,len(table_rows),250):
            name=f'part-{start//250+1:04d}.md'
            (pages/name).write_text('\n'.join(header+table_rows[start:start+250])+ '\n')
            lines.append(f'- [{start+1:,}–{min(start+250,len(subset)):,}번 항목](unconfirmed_pages/{name})')
    if state==EXCLUDED:
        lines += ['', '전체 제외 항목과 사유·원본 레코드 ID는 [CSV](excluded.csv.gz)와 [JSON](excluded.json.gz)에 빠짐없이 담았다.',
            '일반 코드·환경·검증 도구의 proof/derived 언급을 수학 명제 수에 포함하지 않는다. 압축은 배포 크기만 줄이며 행을 생략하지 않는다.', '', '| 제외 사유 | 항목 묶음 수 |','|---|---:|']
        lines += [f'| {REASONS.get(k,k)} | {v:,} |' for k,v in sorted(Counter(x['reason'] for x in subset).items())]
    (directory/(stem+'.md')).write_text('\n'.join(lines)+'\n')


def export_proof_lists(c, directory, reviews_path=None):
    directory = Path(directory)
    inputs={}
    if reviews_path:
        source=Path(reviews_path)
        review_bytes=source.read_bytes();payload=json.loads(review_bytes)
        linked=list(payload.get('associated_review_files',[]))
        if payload.get('supplemental_discovery'):linked.append(payload['supplemental_discovery']['file'])
        inputs={name:(source.parent/name).read_bytes() for name in linked}
        inputs['reviewed_evidence.json']=review_bytes
    items, occurrences, summary = build_lists(c, reviews_path)
    if reviews_path:
        if source.read_bytes()!=review_bytes or any((source.parent/name).read_bytes()!=inputs[name] for name in linked):
            raise ValueError('proof export inputs changed during generation')
    directory.mkdir(parents=True,exist_ok=True)
    for name,data in inputs.items():(directory/name).write_bytes(data)
    write_json(directory/'summary.json',summary)
    write_occurrence_parts(directory/'occurrences',occurrences)
    by_id = {r['record_id']:r for r in occurrences}
    names = [(CONFIRMED,'confirmed','기존 증명 근거 확인 목록'),
             (UNCONFIRMED,'unconfirmed','증명 완료 미확인 목록'),
             (EXCLUDED,'excluded','명제 제안으로 확인되지 않은 검색 결과')]
    columns = ['item_id','registered_id','title','owner','owners','classification','reason','reason_ko','recorded_status',
        'statement','conditions','proof_obligations','followup','r8_source_present','r8_proof_applicability',
        'reviewed_support','occurrence_ids']
    for state, stem, title in names:
        subset = [x for x in items if x['classification']==state]
        if state==EXCLUDED:
            # General keyword hits do not need repeated long scientific excerpts;
            # every original record stays resolvable through its occurrence ID.
            with compressed_text(directory/'excluded.json.gz') as f:
                json.dump(subset,f,ensure_ascii=False,sort_keys=True,separators=(',',':'));f.write('\n')
        else:
            write_json(directory/(stem+'.json'),subset)
        with (compressed_text(directory/(stem+'.csv.gz')) if state==EXCLUDED else (directory/(stem+'.csv')).open('w',newline='')) as f:
            w=csv.DictWriter(f,fieldnames=columns,lineterminator='\n');w.writeheader()
            for item in subset:
                w.writerow({k:js(item[k]) if isinstance(item[k],(list,dict)) else item[k] for k in columns})
        write_markdown(directory,by_id,state,stem,title,subset)
    counts=summary['counts']
    (directory/'README.md').write_text(f'''# 전체 이력의 명제·증명 제안 목록

이 목록은 기존 증명 근거와 명제의 범위를 대조한 **검색용 파생 자료**다.
원문 레지스트리와 과학적 승인 상태를 바꾸지 않는다. 연구 코드·CAS·Lean은 실행하지 않았다.

- [기존 증명 근거 확인 목록](confirmed.md): {counts[CONFIRMED+'_items']:,}개 항목 묶음.
- [증명 완료 미확인 목록](unconfirmed.md): {counts[UNCONFIRMED+'_items']:,}개 항목 묶음.
- [일반 언급·도구 등 제외 기록](excluded.md): {counts[EXCLUDED+'_items']:,}개 항목 묶음.

각 목록에 같은 이름의 CSV·JSON이 있다. JSON에 원문, 조건, 기존 증명 발췌와
버전·가정 대조 이유, 한계, 후속 확인 사항을 담았다. 모든 원본 레코드의 위치와
대표 관찰 커밋은 `occurrences/part-*.jsonl.gz`에서 `item_id`로 연결한다.
부피가 큰 제외 기록과 원본 연결표는 gzip으로 보존한다. Python 표준 라이브러리로 바로 읽을 수 있다.

## 범위와 해석

전체 명제 레코드 {counts['original_proposition_records']:,}개와 추가 검색 결과
{counts['additional_discovery_records']:,}개를 모두 처리했다. 같은 원문 내용·로컬 항목·상태·근거를
가진 출처 사본만 묶는다. 같은 명제 ID의 다른 가정·버전은 자동으로 합치지 않는다.
묶음 수는 수학적으로 독립인 정리 수가 아니다. 검색은 DB에 담긴 명제 전체와
이름·본문 발췌·구조화 필드의 proof/prove/theorem/lemma/proposition/conjecture/derivation/증명/명제/추측을
대상으로 한다. 미수집 원문과 파서의 발췌 한계는 기존 DB의 범위 제한을 그대로 가진다.
추가 원문 검색은 내용 버전별로 수행하며 `source_scan.csv`에 읽기 상태와 누락을 남긴다.
원문에서 추가로 발견한 문장도 정리 여부·증명 완료를 자동 확정하지 않는다.

`ACTIVE`, 테스트 PASS, Lean 선언, 참조 파일 존재만으로 확인 목록에 넣지 않았다.
조건부 증명은 그 가정 아래의 명시된 범위만 기록한다. 전체 CAS 의무가 미완료인
기록에서 개별 보조정리 근거를 확인해도 전체 CAS PASS로 바꾸지 않는다.
`native_evaluation_in_trusted_base`는 소스 파일에 `native_decide`가 포함된 경우다.
이 계산 근거는 확장된 평가 신뢰 기반을 사용하며, 모든 항목이 커널 환원만으로 증명됐다는 뜻이 아니다.
`r8_source_present`는 R8에 원문이 있다는 뜻이고 증명 적용성을 보증하지 않는다.
대표 관찰 커밋은 최초 도입 커밋이 아니다. 철회·대체와 버전별 원문 상태를 보존한다.

## 재생성

```bash
python3 -B scripts/project_catalog.py export --proof-lists /tmp/htt-proof-lists
```

기존 DB와 `reviewed_evidence.json` 및 함께 배포된 정적 검색 입력만 읽는다. 외부 원문 접근·연구 환경·네트워크·PyYAML 없이
동일 결과를 재생성한다. 근거 대조 내용은 자동 증명기가 작성한 결과가 아니며,
수동 검토를 담은 파생 입력이다. 원문·근거의 DB 식별자가 바뀌면 기존 대응을 거부한다.
분류 세부 건수와 전수 대응 검사는 `summary.json`에 있다.
''')
    with (directory/'README.md').open('a') as f:
        f.write('\n## 미확인 사유별 집계\n\n| 사유 | 항목 묶음 수 |\n|---|---:|\n')
        for k,v in summary['unconfirmed_reasons'].items():f.write(f'| {REASONS.get(k,k)} | {v:,} |\n')
        f.write('\n## 근거와 버전 조회\n\n```python\nimport gzip, json\nfrom pathlib import Path\nmatches = []\nfor part in sorted(Path("docs/project_catalog/proofs/occurrences").glob("part-*.jsonl.gz")):\n    with gzip.open(part, "rt") as f:\n        matches.extend(r for r in map(json.loads, f) if r["item_id"] == "ITEM_ID")\n```\n\n')
        f.write('`record_id`가 `discovery:`로 시작하면 추가 원문 검색 항목이며 기존 DB 레코드를 수정하거나 새로 삽입한 것이 아니다. 해당 `file_id`·내용 ID·줄 위치로 원문을 찾는다. 다른 ID는 기존 CLI의 `show RECORD_ID`, 전체 버전은 `history PATH --format json`으로 조회한다.\n')
        f.write(summary_tables(summary))
    return summary
