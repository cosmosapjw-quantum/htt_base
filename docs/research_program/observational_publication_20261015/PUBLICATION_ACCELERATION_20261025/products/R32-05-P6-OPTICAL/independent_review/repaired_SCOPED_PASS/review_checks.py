"""Independent read-only, affected-scope checks for the sealed P6 repair.

Writes only this review's external output directory. Does not execute the
candidate consumer, build, validator, packaging script, or historical suite.
"""
from pathlib import Path
from fractions import Fraction as F
import difflib
import hashlib
import json
import re
import subprocess

OUT = Path(__file__).resolve().parent
REPO = Path('/home/cosmosapjw/Dropbox/bianchi/htt_base')
BASE = REPO / 'docs/research_program/observational_publication_20261015/PUBLICATION_ACCELERATION_20261025/products/R32-05-P6-OPTICAL'
CAND = BASE / 'repair_01'
REPORT = CAND / 'report'
RAW = OUT / 'raw'

def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def save(name, data):
    (RAW / name).write_text(json.dumps(data, indent=2, allow_nan=False) + '\n')

def load(p):
    return json.loads(p.read_text())

result = load(REPORT / 'RESULT.json')
manifest = result['manifest']
canonical = hashlib.sha256(json.dumps(manifest, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
assert sha(REPORT / 'RESULT.json') == '5cf41f57a4eae068ce25bcd98ed508e1a9df92c5a938be333023c7431aa46ecd'
assert canonical == result['manifest_canonical_json_sha256'] == '7e35f553fb41c9cba9e90272e9731ad5cf3235314a2fc723c1aee59b0c62bfcc'
entries = []
for kind, root in [('sources', REPO), ('outputs', CAND)]:
    for entry in manifest[kind]:
        path = root / entry['path']
        digest = sha(path)
        size = path.stat().st_size
        assert digest == entry['sha256'] and size == entry['bytes'], str(path)
        entries.append({'kind': kind, 'path': str(path), 'sha256': digest, 'bytes': size, 'match': True})
assert sha(CAND / 'science/MANUSCRIPT.md') == 'ee6d35bd8b4b571b7ec672b809d10df6b0f5c981dbf0c6d1bc88fa3b77eb59e1'
assert sha(REPORT / 'main.tex') == '4bb9ef46647f77baee40d6c9254ff8939caa2b0dde407fbe0135a7e8bdf95704'
assert sha(BASE / 'report/RESULT.json') == '343622f6bed1197dd0e08b7c64fbfabefba74f5ec02baf9a51b839dda97ae9b3'
save('identity_checks.json', {'candidate': canonical, 'candidate_result_sha256': sha(REPORT / 'RESULT.json'), 'source_count': len(manifest['sources']), 'output_count': len(manifest['outputs']), 'mismatches': 0, 'entries': entries})

reuse = load(REPORT / 'raw/reuse_parity.json')
assert len(reuse['artifacts']) == 9
for x in reuse['artifacts']:
    assert sha(Path(x['base_path'])) == sha(Path(x['repair_path'])) == x['sha256']
assert reuse['prior_checks_reused_count'] == 61 and reuse['consumer_runs_this_repair'] == 0
save('reuse_checks.json', {'artifacts': reuse['artifacts'], 'byte_exact_artifacts': 9, 'historical_checks_reused': 61, 'numerical_consumer_rerun_by_reviewer': False})

source = (CAND / 'science/MANUSCRIPT.md').read_text()
tex = (REPORT / 'main.tex').read_text()
diffs = {}
for name in ['science/MANUSCRIPT.md', 'report/main.tex', 'report/reproduce.py', 'report/validate_candidate.py', 'report/build_source.py', 'science/BUILD_CONTRACT.md', 'science/RESEARCH_NOTE.md']:
    before = (BASE / name).read_text()
    after = (CAND / name).read_text()
    diffs[name] = ''.join(difflib.unified_diff(before.splitlines(True), after.splitlines(True), fromfile='base/' + name, tofile='repair/' + name))
for text in [source, tex]:
    assert r'h_{\varnothing}(a)=-\infty' in text
    assert r'If \(\mathcal E_z\ne\varnothing\) and \(J^{\mathsf T}a\)' in text
    assert r'choose a feasible \(\theta_0\in\Theta_{\rm lin}(z)\)' in text
for name in ['report/build_source.py', 'science/BUILD_CONTRACT.md', 'science/RESEARCH_NOTE.md']:
    assert not diffs[name]
old_consumer = (BASE / 'report/reproduce.py').read_text()
assert (REPORT / 'reproduce.py').read_text() == old_consumer.replace('P=R.parents[2]', 'P=R.parents[3]')
for name in ['science/MANUSCRIPT.md', 'report/main.tex']:
    old = (BASE / name).read_text()
    new = (CAND / name).read_text()
    assert re.findall(r'\\tag\{\d+\}', old) == re.findall(r'\\tag\{\d+\}', new)
    assert len(re.findall(r'\\tag\{\d+\}', new)) == 35
save('affected_diff.json', diffs)

# Independent exact fixture, derived from A theta + e = z itself.
# For A=diag(1,0), compatibility is e2=z2. Thus min ||e||^2=z2^2.
# For feasible z, e=(0,z2), theta=(z1,t) supplies every real t.
A = ((F(1), F(0)), (F(0), F(0)))
J = (F(0), F(1))
def mv(v):
    return tuple(sum(x*y for x,y in zip(row,v)) for row in A)
cases = []
for z in [(F(0),F(2)), (F(0),F(0)), (F(3,2),F(1)), (F(-1),F(-1))]:
    minimum_error_norm_squared = z[1]**2
    feasible = minimum_error_norm_squared <= 1
    witnesses = []
    if feasible:
        for t in [F(-10), F(0), F(10), F(1000000)]:
            theta = (z[0],t)
            e = tuple(x-y for x,y in zip(z,mv(theta)))
            assert sum(x*x for x in e) <= 1
            assert sum(x*y for x,y in zip(J,theta)) == t
            witnesses.append({'t': str(t), 'theta': list(map(str,theta)), 'e': list(map(str,e))})
    cases.append({'z': list(map(str,z)), 'minimum_error_norm_squared': str(minimum_error_norm_squared), 'feasible': feasible, 'support_a_1': '+infinity' if feasible else '-infinity', 'support_a_0': '0' if feasible else '-infinity', 'witnesses': witnesses})
assert mv((F(0),F(1))) == (0,0)
assert sum(x*y for x,y in zip(J,(F(0),F(1)))) == 1
save('independent_exact_cases.json', {'cases': cases, 'general_proof': 'If E_z is nonempty choose theta0. Let k be the orthogonal projection of J^T a onto ker A; if nonzero, a^T J k=||k||^2>0. A(theta0+t k)=A theta0 and the objective grows linearly for t>=0. If E_z is empty, Theta and its image are empty for every J and every a; sup empty=-infinity, including a=0. For an identifiable carrier equation (18) remains finite+(-infinity)=-infinity in that branch.', 'scope': 'Exact fixture and affected mathematical branch only; no empirical error law, numerical consumer or full proof-suite replay.'})

base_result = load(BASE / 'report/RESULT.json')
for key in ['diagnostic_statuses', 'sky_support_status', 'null_mock_status']:
    assert result[key] == base_result[key]
assert result['claim_tier'] == 'C0'
assert result['acceptance_passed'] is False and result['qualified_products'] == []
data = load(REPORT / 'generated/retained_tensor_region.json')
assert data['source_statistics']['tensor_frobenius_norm'] == 0.03265680189321492
receipts = load(REPORT / 'raw/commands.json')
assert {x['stage'] for x in receipts} >= {'regression','source_build','latexmk','candidate_audit','package_repair'}
repair = load(REPORT / 'raw/repair_receipt.json')
assert result['packet_id'] == repair['packet_id'] == '9c3ccfd20d64ff55c67e5f0c3aad1852d1bcb0f4a7c25b95f698b2deb9721db3'
assert repair['actual_agent_id'] == '/root/rc_9c3ccfd20d64ff55'
assert result['assignment_input_identity'] == repair['input_identity'] == 'sha256:f900ec93d972751795cdd825ee0f362eabed3a2aae60b59e4c24d265ee6ec132'
assert result['phase'] == 'repair' and result['attempt'] == 4
save('scope_and_provenance.json', {'repair_packet': result['packet_id'], 'input_identity': result['assignment_input_identity'], 'phase': result['phase'], 'attempt': result['attempt'], 'actual_repair_agent': repair['actual_agent_id'], 'diagnostic_statuses_unchanged': True, 'cf4_dimensionless_norm': data['source_statistics']['tensor_frobenius_norm'], 'claim_tier': result['claim_tier'], 'numerical_consumer_changed_only_for_parent_path': True, 'historical_contract_and_research_note_unchanged': True, 'candidate_acceptance_remains_false': True, 'recorded_actual_commands': receipts})

commands = []
def run(cmd, stdout_name):
    p = subprocess.run(cmd, capture_output=True, text=True)
    (RAW/stdout_name).write_text(p.stdout)
    (RAW/(stdout_name+'.stderr')).write_text(p.stderr)
    commands.append({'command': cmd, 'exit_code': p.returncode, 'stdout': stdout_name})
    assert p.returncode == 0
    return p.stdout
info = run(['pdfinfo', str(REPORT/'main.pdf')], 'pdfinfo.txt')
assert re.search(r'Pages:\s+13\b', info)
run(['pdftotext', '-layout', str(REPORT/'main.pdf'), str(RAW/'candidate.txt')], 'pdftotext.stdout')
for page in [5,6,13]:
    run(['pdftoppm','-f',str(page),'-l',str(page),'-r','120','-png','-singlefile',str(REPORT/'main.pdf'),str(RAW/f'page-{page:02d}')], f'page-{page:02d}.stdout')
save('independent_commands.json', commands)
summary = {'candidate_identity': 'sha256:'+canonical, 'manifest_sources_verified': len(manifest['sources']), 'manifest_outputs_verified': len(manifest['outputs']), 'byte_exact_reused_artifacts': 9, 'independent_exact_cases': len(cases), 'equation_tags_unchanged': 35, 'pdf_pages': 13, 'rendered_pages': [5,6,13], 'repository_mutated': False, 'formal_controller_binding_pending': True}
save('check_summary.json', summary)
print(json.dumps(summary, indent=2))
