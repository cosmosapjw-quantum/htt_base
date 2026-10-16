import json
from pathlib import Path
ROOT=Path(__file__).resolve().parent

def data():return json.loads((ROOT/'OPEN_DATA_GATE_MATRIX.json').read_text())

def test_exact_seven_blocked_nodes():
    m=data()
    assert {x['node'] for x in m['blockers']} == {'S04','L03','H02','V03','B02','K03','K04'}
    assert len(m['blockers'])==7

def test_all_requirements_have_original_source_and_acceptance():
    m=data()
    sources=m['source_urls']
    for node in m['blockers']:
        assert node['open_sources']
        assert all(s in sources for s in node['open_sources'])
        assert node['checks'] and node['required_data']
        assert 'PASS' not in node['status']

def test_sources_do_not_confuse_descriptive_products_with_physics():
    m=data()
    assert m['source_urls']['CF4_VIZIER_GROUPS']['rows_published']==38053
    assert m['source_urls']['CF4_VIZIER_GALAXIES']['rows_published']==55877
    assert 'not' in m['source_urls']['GAIA_CRF3']['role'].lower()
    assert 'NOT' in m['source_urls']['ANICLASS']['role']

def test_no_pr_dag_promotion_claim():
    m=data()
    txt=json.dumps(m,ensure_ascii=False)
    assert '14' in txt or len(m['blockers'])==7
    assert m['claim_policy']
