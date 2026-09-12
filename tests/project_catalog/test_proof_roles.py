"""Research roles are source-bound metadata, independent of proof status."""
import copy
import hashlib
import json
from pathlib import Path
import subprocess
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'scripts'))
from catalog_lib.proofs import digest, write_occurrence_parts
from catalog_lib.proof_roles import build_roles, export_roles, read_inputs


@pytest.fixture
def role_inputs(tmp_path):
    root = tmp_path / 'proofs'
    root.mkdir()
    rows, occurrences = [], []
    for i, status in enumerate(['existing_proof_support_confirmed', 'proof_completion_unconfirmed']):
        rows.append(dict(item_id=f'item-{i}', registered_id='T1', title='Same named theorem',
                         classification=status, reason='fixture', recorded_status='ACTIVE', owners=['COMMON'],
                         statement='x = x', conditions={'domain': ['Real', 'Complex'][i]},
                         statement_completeness='fixture', r8_source_present=i == 0,
                         r8_proof_applicability='NOT_ESTABLISHED_BY_MEMBERSHIP', occurrence_ids=[f'record-{i}']))
        occurrences.append(dict(item_id=f'item-{i}', record_id=f'record-{i}', content_id=f'source-{i}',
                                file_id=f'file-{i}', source_id='fixture', path='proposal.md', line=5,
                                observed_commit=str(i), git_blob=None, source_url=''))
    (root / 'confirmed.json').write_text(json.dumps(rows[:1]))
    (root / 'unconfirmed.json').write_text(json.dumps(rows[1:]))
    write_occurrence_parts(root / 'occurrences', occurrences)
    items, occ, hashes = read_inputs(root)
    text = '## T1. A concrete theorem proposal'
    a = dict(anchor_id='a1', title='T1', role='research_proposal_candidate',
             rationale_ko='후보로 명시', source={'content_id': 'source-0', 'path': 'proposal.md'},
             line_start=5, line_end=6, excerpt=text,
             excerpt_sha256=hashlib.sha256(text.encode()).hexdigest(),
             proposal_context=dict(line_start=1, line_end=1, text='Proposal', sha256=hashlib.sha256(b'Proposal').hexdigest()))
    b = dict(item_id='item-0', item_sha256=digest(rows[0]), anchor_id='a1',
             match='same_source_section', alignment_ko='같은 내용 버전의 후보 구간')
    payload = dict(schema_version=1, input_sha256=hashes, anchors=[a], bindings=[b])
    evidence = tmp_path / 'roles.json'
    evidence.write_text(json.dumps(payload))
    return root, evidence, items, occ, hashes, payload


def test_role_does_not_follow_same_id_or_proof_status(role_inputs):
    _, _, items, occ, hashes, payload = role_inputs
    rows, s = build_roles(items, occ, payload, hashes)
    assert [r['role'] for r in rows] == ['research_proposal_candidate', 'unresolved']
    assert s['all_items_accounted'] and s['proof_status_unchanged']
    assert [r['conditions'] for r in rows] == [r['conditions'] for r in items]
    assert all(r['novelty_assessment'] == 'NOT_EVALUATED' for r in rows)


@pytest.mark.parametrize('mutation', ['scope', 'line', 'excerpt', 'intent', 'input', 'duplicate', 'unbound_reference'])
def test_stale_unsupported_roles_rejected(role_inputs, mutation):
    _, _, items, occ, hashes, payload = role_inputs
    p = copy.deepcopy(payload)
    if mutation == 'scope':
        items[0]['conditions'] = {'domain': 'changed'}
    elif mutation == 'line':
        p['anchors'][0]['line_start'] = 6
    elif mutation == 'excerpt':
        p['anchors'][0]['excerpt'] += ' changed'
    elif mutation == 'intent':
        del p['anchors'][0]['proposal_context']
    elif mutation == 'input':
        p['input_sha256'] = {}
    elif mutation == 'duplicate':
        p['bindings'].append(p['bindings'][0])
    elif mutation == 'unbound_reference':
        p['bindings'][0].update(item_id='item-1', item_sha256=digest(items[1]),
                                match='reviewed_cross_reference', reference_anchor_id='a1')
    with pytest.raises(ValueError):
        build_roles(items, occ, p, hashes)


def test_dual_role_and_structural_hits_preserved(role_inputs):
    _, _, items, occ, hashes, payload = role_inputs
    a = copy.deepcopy(payload['anchors'][0])
    a.update(anchor_id='a2', role='internal_auxiliary')
    payload['anchors'].append(a)
    b = dict(payload['bindings'][0], anchor_id='a2')
    payload['bindings'].append(b)
    items[1]['title'] = r'\end{theorem}'
    rows, _ = build_roles(items, occ, payload, hashes)
    assert {r['role'] for r in rows} == {'mixed_role', 'non_proposition_hit'}
    assert sum(len(r['occurrence_ids']) for r in rows) == 2


def test_offline_export_repeats_without_db_or_sources(role_inputs, tmp_path):
    root, evidence, *_ = role_inputs
    a, b = tmp_path / 'a', tmp_path / 'b'
    before = {p: p.read_bytes() for p in root.rglob('*') if p.is_file()}
    export_roles(root, a, evidence)
    export_roles(root, b, evidence)
    assert {p.relative_to(a): p.read_bytes() for p in a.rglob('*') if p.is_file()} == {p.relative_to(b): p.read_bytes() for p in b.rglob('*') if p.is_file()}
    assert all(p.read_bytes() == data for p, data in before.items())
    cli = Path(__file__).resolve().parents[2] / 'scripts/project_catalog.py'
    result = subprocess.run([sys.executable, '-S', '-B', str(cli), '--db', str(tmp_path / 'absent.sqlite'),
                             'export', '--proof-roles', str(tmp_path / 'cli'), '--proof-inputs', str(root),
                             '--role-evidence', str(evidence)], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    assert not (tmp_path / 'absent.sqlite').exists()


def test_unmapped_proposal_survives_as_a_concrete_unit(role_inputs, tmp_path):
    root, evidence, _, _, _, payload = role_inputs
    a = copy.deepcopy(payload['anchors'][0])
    a.update(anchor_id='unmapped', title='Second proposed result', line_start=10, line_end=12)
    payload['anchors'].append(a)
    evidence.write_text(json.dumps(payload))
    target = tmp_path / 'export'
    summary = export_roles(root, target, evidence)
    proposals = json.loads((target / 'research_proposals.json').read_text())
    assert len(proposals) == 2
    assert summary['proposal_units_without_prior_item'] == 1
    assert next(a for a in proposals if a['anchor_id'] == 'unmapped')['linked_item_ids'] == []
    assert all(a['proof_support'] == 'NOT_ESTABLISHED_FOR_THIS_PROPOSAL' for a in proposals)
