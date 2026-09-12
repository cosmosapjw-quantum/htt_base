"""Offline historical research-role views; neither a prover nor a novelty judge.

The reviewed input binds roles to exact source passages and existing list items.
Same titles/IDs in another version never inherit a role without a new binding.
"""
from __future__ import annotations

from collections import Counter, defaultdict
import csv
import gzip
import hashlib
import json
from pathlib import Path
import re

from .proofs import cell, compressed_text, digest, write_json

ROLE_LABELS = {
    'research_proposal_candidate': '과거 연구제안의 구체적 정리·증명 후보',
    'internal_auxiliary': '내부 보조명제·검증 보조정리',
    'supporting_known_result': '기존 결과를 재사용한 기초·보조명제',
    'mixed_role': '제안 후보이면서 보조 역할도 확인',
    'unresolved': '역할 판단 보류',
    'non_proposition_hit': '독립 명제가 아닌 검색 조각',
}
PROOF_LABELS = {
    'existing_proof_support_confirmed': '기존 증명 근거 확인',
    'proof_completion_unconfirmed': '증명 완료 미확인',
}


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for part in iter(lambda: f.read(1024 * 1024), b''):
            h.update(part)
    return h.hexdigest()


def read_inputs(proof_dir):
    p = Path(proof_dir)
    rows = []
    for stem in ('confirmed', 'unconfirmed'):
        rows.extend(json.loads((p / (stem + '.json')).read_text()))
    by_id = {r['item_id']: r for r in rows}
    if len(by_id) != len(rows):
        raise ValueError('duplicate input item ID')
    paths = [p / 'confirmed.json', p / 'unconfirmed.json', p / 'occurrences/index.json']
    index = json.loads(paths[-1].read_text())
    occurrences = defaultdict(list)
    for part in index['parts']:
        path = p / 'occurrences' / part['file']
        if sha(path) != part['sha256']:
            raise ValueError('source occurrence shard changed')
        count = 0
        with gzip.open(path, 'rt') as f:
            for row in map(json.loads, f):
                count += 1
                if row['item_id'] in by_id:
                    occurrences[row['item_id']].append(row)
        if count != part['rows']:
            raise ValueError('source occurrence count differs')
    for item_id, row in by_id.items():
        actual = [o['record_id'] for o in occurrences[item_id]]
        if len(actual) != len(set(actual)) or set(actual) != set(row['occurrence_ids']):
            raise ValueError('input occurrence partition differs')
    return rows, occurrences, {str(f.relative_to(p)): sha(f) for f in paths}


def validate_evidence(payload, rows, occurrences, inputs):
    if payload.get('schema_version') != 1 or payload.get('input_sha256') != inputs:
        raise ValueError('role evidence does not match proof-list snapshot')
    by_id = {r['item_id']: r for r in rows}
    anchors = {}
    for a in payload['anchors']:
        key = a['anchor_id']
        if key in anchors or a['role'] not in ROLE_LABELS or not a.get('rationale_ko'):
            raise ValueError('invalid or duplicate role anchor')
        if not a.get('source') or not a.get('excerpt'):
            raise ValueError('role requires source and concrete excerpt')
        if a['excerpt_sha256'] != hashlib.sha256(a['excerpt'].encode()).hexdigest():
            raise ValueError('role excerpt changed')
        if not a['source'].get('content_id') or not 1 <= a['line_start'] <= a['line_end']:
            raise ValueError('role requires exact source version and line span')
        if a['role'] == 'research_proposal_candidate' and not a.get('proposal_context'):
            raise ValueError('proposal requires evidence of proposal intent')
        if a.get('proposal_context'):
            cx = a['proposal_context']
            if (not 1 <= cx['line_start'] <= cx['line_end'] or not cx['text'] or
                    cx['sha256'] != hashlib.sha256(cx['text'].encode()).hexdigest()):
                raise ValueError('proposal context changed')
        anchors[key] = a
    assigned = defaultdict(list)
    for b in payload['bindings']:
        item_id = b['item_id']
        if item_id not in by_id or digest(by_id[item_id]) != b['item_sha256']:
            raise ValueError('role binding belongs to another item/scope/version')
        a = anchors[b['anchor_id']]
        if not b.get('alignment_ko') or b['match'] not in {'same_source_section', 'reviewed_cross_reference', 'exact_declaration'}:
            raise ValueError('role needs explicit alignment method')
        if b['match'] in {'same_source_section', 'exact_declaration'}:
            if not any(o['content_id'] == a['source']['content_id'] and
                       a['line_start'] <= (o.get('line') or 0) <= a['line_end']
                       for o in occurrences[item_id]):
                raise ValueError('role source span does not contain the item')
        else:
            # Cross references need a second, independently source-bound anchor,
            # not a title/ID similarity or a borrowed proof-status conclusion.
            ref = anchors[b['reference_anchor_id']]
            if not any(o['content_id'] == ref['source']['content_id'] and
                       ref['line_start'] <= (o.get('line') or 0) <= ref['line_end']
                       for o in occurrences[item_id]):
                raise ValueError('cross-reference source differs from item')
        if b['anchor_id'] in {x['anchor_id'] for x in assigned[item_id]}:
            raise ValueError('duplicate item/anchor binding')
        assigned[item_id].append(b)
    return anchors, assigned


def classify(item, bindings, anchors):
    # A closing delimiter occurrence is not a separate theorem, even if the
    # discovery window around it contains mathematical context.
    if re.fullmatch(r'\s*\\(?:begin|end)\{(?:theorem|lemma|proposition|corollary|proof)\}\s*', item['title']):
        return 'non_proposition_hit', '검색의 일치 지점이 LaTeX 환경 경계다. 주변 본문은 원본 항목에 보존하며 독립 명제로 세지 않는다.'
    roles = {anchors[b['anchor_id']]['role'] for b in bindings} - {'unresolved'}
    if not roles:
        reasons = [anchors[b['anchor_id']]['rationale_ko'] for b in bindings]
        return 'unresolved', ' / '.join(dict.fromkeys(reasons)) if reasons else '구체적 제안 의도 또는 보조 사용을 해당 내용 버전에 연결할 근거가 부족하다. 제안 이력이 없다는 뜻은 아니다.'
    if len(roles) > 1:
        if roles <= {'internal_auxiliary', 'supporting_known_result'}:
            return 'supporting_known_result', '기존 결과의 보조 사용 근거가 함께 확인된다.'
        return 'mixed_role', '동일 원본 항목에 복수 역할이 연결된다. 하나의 역할로 덮어쓰지 않는다.'
    role = next(iter(roles))
    return role, ' / '.join(dict.fromkeys(anchors[b['anchor_id']]['rationale_ko'] for b in bindings))


def build_roles(items, occurrences, payload, inputs):
    anchors, bindings = validate_evidence(payload, items, occurrences, inputs)
    result = []
    for x in sorted(items, key=lambda r: (r['title'], r['item_id'])):
        bs = bindings[x['item_id']]
        role, reason = classify(x, bs, anchors)
        result.append({
            'item_id': x['item_id'], 'registered_id': x.get('registered_id'),
            'title': x['title'], 'role': role, 'role_ko': ROLE_LABELS[role],
            'role_reason_ko': reason, 'role_bindings': bs,
            'proof_classification': x['classification'], 'proof_reason': x['reason'],
            'recorded_status': x['recorded_status'], 'owners': x['owners'],
            'statement': x['statement'], 'conditions': x['conditions'],
            'statement_completeness': x['statement_completeness'],
            'r8_source_present': x['r8_source_present'],
            'r8_proof_applicability': x['r8_proof_applicability'],
            'occurrence_ids': x['occurrence_ids'],
            'source_locations': [{k: o.get(k) for k in ('file_id', 'source_id', 'content_id', 'path', 'line', 'observed_commit', 'git_blob', 'source_url')} for o in occurrences[x['item_id']]],
            'novelty_assessment': 'NOT_EVALUATED',
            'role_scope': 'historical documented role; no universal absence claim',
        })
    counts = Counter(r['role'] for r in result)
    cross = {role: dict(Counter(r['proof_classification'] for r in result if r['role'] == role)) for role in ROLE_LABELS}
    summary = {
        'schema_version': 1, 'input_items': len(items),
        'input_occurrences': sum(len(r['occurrence_ids']) for r in items),
        'role_items': {role: counts[role] for role in ROLE_LABELS},
        'role_occurrences': {role: sum(len(r['occurrence_ids']) for r in result if r['role'] == role) for role in ROLE_LABELS},
        'proof_status_by_role': cross,
        'anchors_by_role': dict(Counter(a['role'] for a in anchors.values())),
        'mapped_anchors': len({b['anchor_id'] for bs in bindings.values() for b in bs}),
        'input_sha256': inputs, 'all_items_accounted': len(result) == len(items) == len({r['item_id'] for r in result}),
        'proof_status_unchanged': all(r['proof_classification'] == next_x['classification'] for r, next_x in zip(result, sorted(items, key=lambda x: (x['title'], x['item_id'])))),
        'source_review': payload.get('source_review', {}),
        'proof_reexecution': 'NOT_EXECUTED', 'novelty_assessment': 'NOT_EVALUATED',
        'semantic_equivalence': 'NOT_ADJUDICATED',
    }
    return result, summary


def write_csv(path, rows):
    fields = ['item_id', 'registered_id', 'title', 'role', 'role_ko', 'proof_classification',
              'recorded_status', 'r8_source_present', 'role_reason_ko', 'role_bindings',
              'conditions', 'source_locations', 'occurrence_ids']
    with compressed_text(path) as f:
        w = csv.DictWriter(f, fieldnames=fields, lineterminator='\n')
        w.writeheader()
        for r in rows:
            w.writerow({k: json.dumps(r[k], ensure_ascii=False, sort_keys=True) if isinstance(r[k], (list, dict)) else r[k] for k in fields})


def export_roles(proof_dir, output, evidence_path):
    output = Path(output)
    evidence_path = Path(evidence_path)
    evidence_bytes = evidence_path.read_bytes()
    payload = json.loads(evidence_bytes)
    inventory_bytes = None
    inventory_info = payload.get('source_review', {})
    if inventory_info.get('inventory_sha256'):
        inventory_path = evidence_path.parent / inventory_info['inventory_file']
        inventory_bytes = inventory_path.read_bytes()
        if hashlib.sha256(inventory_bytes).hexdigest() != inventory_info['inventory_sha256']:
            raise ValueError('source review inventory changed')
    items, occurrences, inputs = read_inputs(proof_dir)
    rows, summary = build_roles(items, occurrences, payload, inputs)
    if evidence_path.read_bytes() != evidence_bytes:
        raise ValueError('role evidence changed during export')
    output.mkdir(parents=True, exist_ok=True)
    (output / 'role_evidence.json').write_bytes(evidence_bytes)
    if inventory_bytes is not None:
        (output / 'source_review.json').write_bytes(inventory_bytes)
    write_json(output / 'summary.json', summary)
    with compressed_text(output / 'all_roles.json.gz') as f:
        json.dump(rows, f, ensure_ascii=False, sort_keys=True, separators=(',', ':'))
        f.write('\n')
    write_csv(output / 'all_roles.csv.gz', rows)
    for role, label in ROLE_LABELS.items():
        selected = [r for r in rows if r['role'] == role]
        with compressed_text(output / (role + '.json.gz')) as f:
            json.dump(selected, f, ensure_ascii=False, sort_keys=True, separators=(',', ':'))
            f.write('\n')
        write_csv(output / (role + '.csv.gz'), selected)
        lines = [f'# {label}', '', f'기존 목록의 항목 묶음 {len(selected):,}개. 수학적 동치로 통합한 정리 수가 아니다.', '',
                 f'전체 상세: [{role}.csv.gz]({role}.csv.gz), [{role}.json.gz]({role}.json.gz).', '',
                 '| 항목 ID | 제목 | 증명 근거 상태 | 역할 근거 |', '|---|---|---|---|']
        # Large unresolved/search-noise views remain complete in machine lists.
        shown = selected if role not in {'unresolved', 'non_proposition_hit'} else selected[:50]
        for r in shown:
            links = ' '.join(f"[{b['anchor_id']}](evidence.md#{b['anchor_id']})" for b in r['role_bindings'])
            lines.append(f"| `{r['item_id']}` | {cell(r['title'])} | {PROOF_LABELS[r['proof_classification']]} | {links or cell(r['role_reason_ko'])} |")
        if len(shown) != len(selected):
            lines += ['', '본문에는 처음 50개만 표시한다. CSV·JSON에는 전 항목이 있다.']
        (output / (role + '.md')).write_text('\n'.join(lines) + '\n')
    by_anchor = defaultdict(list)
    for r in rows:
        for b in r['role_bindings']:
            by_anchor[b['anchor_id']].append(r['item_id'])
    # The original keyword list sometimes only retained a document title. Keep
    # every newly read concrete proposal section, even without a prior item at
    # its start line. A missing binding cannot manufacture confirmed support.
    row_index = {r['item_id']: r for r in rows}
    units = []
    for a in payload['anchors']:
        linked = by_anchor[a['anchor_id']]
        units.append(dict(a, linked_item_ids=linked,
                          prior_proof_statuses=dict(Counter(row_index[i]['proof_classification'] for i in linked)),
                          proof_support='existing_support_at_exact_declaration' if a['role'] == 'internal_auxiliary' and any(row_index[i]['proof_classification'] == 'existing_proof_support_confirmed' and any(b['anchor_id'] == a['anchor_id'] and b['match'] == 'exact_declaration' for b in row_index[i]['role_bindings']) for i in linked) else 'NOT_ESTABLISHED_FOR_THIS_PROPOSAL',
                          novelty_assessment='NOT_EVALUATED'))
    summary['reviewed_units'] = len(units)
    summary['proposal_units_without_prior_item'] = sum(a['role'] == 'research_proposal_candidate' and not a['linked_item_ids'] for a in units)
    write_json(output / 'summary.json', summary)
    for stem, role_set, label in [
        ('research_proposals', {'research_proposal_candidate'}, '연구제안서의 구체적 정리·증명 목표'),
        ('auxiliary_propositions', {'internal_auxiliary', 'supporting_known_result'}, '내부 보조명제와 명시적 문헌 이식 결과'),
    ]:
        selected = [a for a in units if a['role'] in role_set]
        write_json(output / (stem + '.json'), selected)
        fields = ['anchor_id', 'proposed_id', 'title', 'role', 'rationale_ko', 'source', 'line_start', 'line_end', 'excerpt', 'linked_item_ids', 'prior_proof_statuses', 'proof_support', 'novelty_assessment']
        with (output / (stem + '.csv')).open('w', newline='') as f:
            w = csv.DictWriter(f, fieldnames=fields, lineterminator='\n')
            w.writeheader()
            for a in selected:
                w.writerow({k: json.dumps(a.get(k), ensure_ascii=False, sort_keys=True) if isinstance(a.get(k), (list, dict)) else a.get(k) for k in fields})
        lines = [f'# {label}', '', f'출처·내용 버전을 보존한 구체적 구간 {len(selected):,}개. 수학적 동치 통합이나 학술 신규성 판정은 하지 않았다.', '',
                 f'원문·조건·출처·기존 목록 연결: [{stem}.json]({stem}.json), [{stem}.csv]({stem}.csv).', '',
                 '| 제안 ID / 선언 | 구체적인 제목 | 원문 근거 | 기존 증명 근거 |', '|---|---|---|---|']
        for a in selected:
            label = a.get('proposed_id') or a['title']
            proof = '해당 보조 선언의 저장 근거 확인' if a['proof_support'] == 'existing_support_at_exact_declaration' else '이 제안 전체의 완료 미확인'
            lines.append(f"| {cell(label)} | {cell(a['title'])} | [{cell(a['source']['path'])}:{a['line_start']}](evidence.md#{a['anchor_id']}) | {proof} |")
        (output / (stem + '.md')).write_text('\n'.join(lines) + '\n')
    lines = ['# 역할 분류의 원문 근거', '', '제안 당시의 의도와 내부 사용 역할을 읽은 기록이다. 학술적 신규성이나 증명 완료를 새로 판정하지 않는다.', '']
    for a in payload['anchors']:
        f = a['source']
        lines += [f"<a id=\"{a['anchor_id']}\"></a>", f"## {a['anchor_id']} — {a['title']}", '',
                  f"- 역할: {ROLE_LABELS[a['role']]}", f"- 출처: `{f['path']}` {a['line_start']}–{a['line_end']}행",
                  f"- 내용 버전: `{f['content_id']}`; 관찰 커밋: `{f.get('observed_commit') or '없음/로컬·아카이브'}`",
                  f"- 이유: {a['rationale_ko']}", f"- 연결 항목: {', '.join('`'+i+'`' for i in by_anchor[a['anchor_id']]) or '기존 두 목록에 직접 대응하는 검색 항목 없음'}", '',
                  '~~~~text', a['excerpt'], '~~~~', '']
        if a.get('proposal_context'):
            cx = a['proposal_context']
            context_path = cx.get('source', f)['path']
            lines += [f"제안 의도 문맥 (`{context_path}` {cx['line_start']}–{cx['line_end']}행):", '', '~~~~text', cx['text'], '~~~~', '']
        if a.get('usage_context'):
            cx = a['usage_context']
            lines += [f"같은 소스의 사용 문맥 ({cx['line_start']}–{cx['line_end']}행):", '', '~~~~text', cx['text'], '~~~~', '']
    (output / 'evidence.md').write_text('\n'.join(lines) + '\n')
    n_proposal = sum(a['role'] == 'research_proposal_candidate' for a in units)
    n_auxiliary = sum(a['role'] == 'internal_auxiliary' for a in units)
    n_known = sum(a['role'] == 'supporting_known_result' for a in units)
    guide = f'''# 연구제안 정리 후보와 내부 보조명제

과거 연구제안서가 구체적인 증명 목표로 내놓은 항목과 프로젝트 구현·검증에서
보조 역할을 하는 명제를 구별한 검색용 파생 목록이다. **제안 당시의 역할**을
분류하며, 학술적 신규성·참/거짓·최신 버전의 증명 적용성을 새로 판단하지 않는다.
Owner: COMMON. Scope: static historical research-role navigation.

## 먼저 읽을 목록

| 목록 | 출처·버전을 보존한 구간 수 | 내용 |
|---|---:|---|
| [연구제안의 정리·증명 목표](research_proposals.md) | {n_proposal:,} | 구체적인 후보 진술, 가정, 증명 경로·남은 의무의 원문 |
| [내부 보조명제·문헌 이식](auxiliary_propositions.md) | {n_auxiliary+n_known:,} | 내부 보조 선언 {n_auxiliary:,}개와 명시적 문헌 이식 {n_known:,}개 |

각 목록에 같은 이름의 CSV·JSON이 있다. [원문 근거](evidence.md)와
[검토 입력](role_evidence.json)에 정확한 파일·행·내용 버전, 제안 의도 및
기존 DB의 원본 레코드 연결을 보존한다. JSON의 `catalog_source_records`는
해당 구간에 시작하는 원본 DB 기록이며, 증명 완료를 승계하는 연결은 아니다.

구체적인 예는 T-A1의 signed comparator 상쇄/비식별성, NT2-A1의 다중 multipole
Fisher–Cramér–Rao 하한, T-P1의 pole 회전 공변성, T-P18의 공통 latent joint region이다.
보조명제에는 `PR257Orbit.mm_assoc`, 고정 예제 `fixed_beta2`, 상태 논리
`completeness_not_promoted` 등이 있다. 심사 보강안의 T7은 원문이
‘문헌 이식’이라고 명시하므로 기존 결과를 사용하는 항목으로 분리했다.

## 두 종류의 건수를 섞지 않기

위 표는 **직접 읽은 명제 구간** 단위다. 아래 표는 이전 증명 목록의
**검색 항목 묶음** 단위다. 같은 구간에서 여러 검색 항목이 나올 수 있고,
이전 목록이 문서 제목만 보유한 경우도 있다. 제안 목표 중
{summary['proposal_units_without_prior_item']:,}개 구간에는 시작 위치가 대응하는 기존 검색 항목이 없어,
이번에 원문 구간과 DB 기록을 직접 연결했다. 이들을 빠뜨리거나 문서 전체를
정리 하나로 세지 않는다. 원본 증명 목록과 SQLite는 변경하지 않았다.

| 기존 검색 묶음의 역할 | 묶음 수 |
|---|---:|
'''
    guide += '\n'.join(f'| [{label}]({role}.md) | {summary["role_items"][role]:,} |' for role, label in ROLE_LABELS.items())
    guide += f'''

기존 {summary['input_items']:,}개 묶음 / {summary['input_occurrences']:,}개 출처 발생 기록을 모두 보존했다.
[전체 JSON](all_roles.json.gz), [전체 CSV](all_roles.csv.gz), [집계](summary.json)에서 조회할 수 있다.
건수는 수학적으로 독립이거나 새로운 정리 수가 아니다.

## 판정 기준과 한계

- 연구제안 후보는 제안서의 구체적인 진술과 제안 의도가 함께 있는 경우다.
  제안서가 새로운 증명 목표로 내놓은 보조정리도 여기에 들어갈 수 있다.
- 내부 보조명제는 선언·고정 예제·사용 문맥을 읽어 역할을 확인한 항목이다.
  제안 근거를 찾지 못했다는 사실만으로 이 범주에 넣지 않았다.
- 데이터 실행 티켓, 문서 경계 표식, 상태 표기는 정리와 구별한다.
- 같은 ID라도 다른 문서·가정·버전에는 역할을 자동 전파하지 않는다.
  철회·대체 기록도 삭제하지 않는다. 제안 역할과 현재 유효성은 별개다.
- 검토한 {inventory_info.get('content_versions_read', 0):,}개 내용 버전의
  {inventory_info.get('source_occurrences_read', 0):,}개 경로·버전 사본은
  [원문 검토 목록](source_review.json)에 있다. 명시적 후보 문서, 정리 backlog,
  구판 연구계획과 레지스트리, 저장된 증명 근거의 보조 선언을 표적 대조했다.
- **역할 보류 {summary['role_items']['unresolved']:,}개는 추가 대조가 필요하다.**
  모든 과거 제안·내부 사용 관계의 의미 검토가 완료됐다는 뜻은 아니다.
  ‘연구제안에 없었다’거나 ‘명제가 거짓이다’라는 판단도 아니다.
- R8 원문 포함 여부와 R8 증명 적용성을 구별한다. 기존 증명 분류는 그대로다.
  제안서의 ‘proved/완전 증명’ 문구만으로 새 후보 전체를 증명 확인으로 승격하지 않는다.
  연구 코드·연구 테스트·CAS·Lean은 실행하지 않았다.

## 재생성 및 조회

SQLite 복원이나 외부 원문 다운로드 없이 배포된 목록과 검토 입력으로 재생성한다.

```bash
python3 -S -B scripts/project_catalog.py export --proof-roles /tmp/htt-proof-roles
```

다른 입력 묶음은 `--proof-inputs PATH --role-evidence PATH/role_evidence.json`으로 지정한다.
입력 내용이나 출처 연결이 바뀌면 기존 검토를 재사용하지 않고 오류를 낸다.

```python
import gzip, json
from pathlib import Path
p = Path("docs/project_catalog/proofs/roles")
proposals = json.loads((p / "research_proposals.json").read_text())
print([(r["proposed_id"], r["title"]) for r in proposals
       if "T-P" in (r["proposed_id"] or "")])
with gzip.open(p / "all_roles.json.gz", "rt") as f:
    rows = json.load(f)
print([r["title"] for r in rows if r["role"] == "internal_auxiliary"
       and r["proof_classification"] == "existing_proof_support_confirmed"])
```
'''
    (output / 'README.md').write_text(guide)
    return summary
