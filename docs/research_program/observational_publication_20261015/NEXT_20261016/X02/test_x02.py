import json
from pathlib import Path
from make_x02 import validate, ROWS
P=Path(__file__).parent/'X02_NOVELTY_MATRIX.json'

def test_six_papers():
 d=json.loads(P.read_text());assert validate(d['comparison_rows'])
 assert len(d['comparison_rows'])==6

def test_negative_comparator_not_dropped():
 d=json.loads(P.read_text());p=next(x for x in d['comparison_rows'] if x['id']=='P3')
 assert any('Stiskalek' in r['title'] for r in p['sources'])
 assert any('Kalbouneh' in r['title'] for r in p['sources'])
 assert 'negative' not in p['novelty_requires'].lower() or p['novelty_requires']

def test_priors_already_cover_kinematic_rank_and_anomaly():
 d=json.loads(P.read_text());f={x['id']:x for x in d['comparison_rows']}
 assert any('Heinesen' in s['title'] for s in f['P6']['sources'])
 assert any('Herold' in s['title'] for s in f['P2']['sources'])
 assert d['physical_novelty_admitted'] is False

def test_manuscript_gate_not_claimed():
 d=json.loads(P.read_text());assert 'NOT_POSITIVE' in d['scientific_status']
 assert all('novelty_requires' in x and x['novelty_requires'] for x in d['comparison_rows'])
