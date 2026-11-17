"""Close the completed R61 record and hash the finite release artifacts."""
from __future__ import annotations
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
import subprocess

root = Path(__file__).resolve().parents[2]
folder = root / 'docs/research_program/observational_publication_20261015/R61_KINEMATIC_MEASUREMENT_20261117'
def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()
validation = json.loads((folder / 'DAG_VALIDATION.json').read_text())
assert validation['status'] == 'PASS_SCOPED'
assert all(c['exit_code'] == 0 for c in validation['commands'])
test_text = (folder / 'RESULTS/FINAL_CURRENT_TESTS.log').read_text()
assert '34 passed' in test_text, test_text[-1000:]

record_path = folder / 'RESEARCH_RECORD.json'
record = json.loads(record_path.read_text())
record['status'] = 'COMPLETE_SCOPED_C0'
record['updated_utc'] = datetime.now(timezone.utc).isoformat()
record['stages'][-1]['status'] = 'complete_scoped'
record['stage5']['mixed_component_local_validation'] = '28 actual-input cases converged to endpoint gap <=1e-10; native production execution confirmed in stage7 and RESULTS/MIXED.'
record['stage7']['execution_evidence'] = 'RESULTS/IMAGES, original RESULTS/DEPTH and active RESULTS/DEPTH_CORRECTED, RESULTS/MIXED; original three runners and targeted corrected depth run exited zero.'
record['stage10'] = {
    'status': 'complete_scoped',
    'evidence': ['RESEARCH_DAG.json', 'RESEARCH_PLAN_KO.md', 'DAG_UPDATE_RECEIPT.json', 'DAG_VALIDATION.json', 'ARTIFACT_MANIFEST.json'],
    'current_tree_tests': '34 passed; actual single final run in RESULTS/FINAL_CURRENT_TESTS.log',
    'canonical_cards': 285, 'previous_284_cards_unchanged': True,
    'original_42_science_nodes_unchanged': True,
    'release_branch': 'research/r61-kinematic-measurement-20261117',
    'release_identity': 'The containing Git commit identifies this artifact. Remote publication is verified separately against that commit; no self-referential commit hash is embedded.',
    'submission_status': 'NOT_READY_TO_SUBMIT',
    'automatic_successor': False, 'local_agent_prompt_created': False}
record_path.write_text(json.dumps(record, indent=2, ensure_ascii=False) + '\n')

validation_path = folder / 'VALIDATION.md'
text = validation_path.read_text()
old = 'The 24 and 10 tests are separate recorded runs, not an invented single 34-test transcript. The original images test run separately reported 13 passed after correcting the independent oracle scaling; it is not counted again.'
new = 'The original 24 and 10 tests remain separate historical runs. The final current-tree run independently reports **34 passed** in RESULTS/FINAL_CURRENT_TESTS.log (exit0, 19.37 seconds). These are the same 34 cases, not 68 independent checks. The original images test run separately reported 13 passed after correcting the independent oracle scaling; it is not counted again.'
assert old in text
text = text.replace(old, new)
row = '| Saved-result table generation | completed without refitting | RESULTS/NUMERICAL_SUMMARY.json; RESULTS/NUMERICAL_TABLES.md |'
text = text.replace(row, '| Final current-tree tests | 34 passed; process exit0 | RESULTS/FINAL_CURRENT_TESTS.log; DAG_VALIDATION.json |\n| Canonical and publication DAG gates | all six structural commands exit0; 285 cards, original42 nodes preserved | DAG_VALIDATION.json |\n' + row)
validation_path.write_text(text)

report_path = folder / 'REPORT_KO.md'
text = report_path.read_text()
replacements = {
    '(K(0.08)-K(0.02))': '$K(0.08)-K(0.02)$',
    '(z=0)': '$z=0$',
    '(0.01<z<0.10)': '$0.01<z<0.10$',
    '(C=N+S)': '$C=N+S$', '(S)': '$S$',
    '((-+++))': '$(-,+,+,+)$',
    r'(U^aU_a=-c^2)': r'$U^aU_a=-c^2$',
    r'(H=\Theta/3>0)': r'$H=\Theta/3>0$',
    r'(D_L=cz/\mathfrak H_o(n)+O(z^2))': r'$D_L=cz/\mathfrak H_o(n)+O(z^2)$',
    '(d_H=-a+d_{cal})': '$d_H=-a+d_{cal}$',
    r'(t=\chi^2_{11}(.95)=19.67513757268249)': r'$t=\chi^2_{11}(.95)=19.67513757268249$',
    r'(H,\Theta)': r'$H,\Theta$',
    '(p_{11}=0.0153427383)': '$p_{11}=0.0153427383$',
    r'(v_A=\beta^TE_A\beta$': r'$v_A=\beta^TE_A\beta$',
    '(10^{-10})': '$10^{-10}$',
    r'(9.9974\times10^{-11})': r'$9.9974\times10^{-11}$',
    r'(4.90\times10^{-17})': r'$4.90\times10^{-17}$',
    '(D_L=D_{L,fid}/(1+h(n)))': '$D_L=D_{L,fid}/(1+h(n))$',
    '적합된 (1+h(n))의': '적합된 $1+h(n)$의',
    r'(b^TV^{-1}b\le\|C^{-1/2}\delta y\|^2)': r'$b^TV^{-1}b\le\|C^{-1/2}\delta y\|^2$',
}
for before, after in replacements.items():
    text = text.replace(before, after)
needle = '기본 새 모듈의 unit/integration 검증 24개와 별도 box-extremum 수학 검증 10개가 통과했다.'
assert needle in text
text = text.replace(needle, needle + ' 최종 현재 코드에서 같은 34개를 한 번에 다시 실행하여 **34 passed**를 기록했다. [최종 검증](DAG_VALIDATION.json)에 종료 코드와 로그 해시가 있다.')
report_path.write_text(text)

plan_path = folder / 'RESEARCH_PLAN_KO.md'
text = plan_path.read_text().replace('(z=0)', '$z=0$')
text = text.replace(r'(b^TV^{-1}b\le\|C^{-1/2}\delta y\|^2)', r'$b^TV^{-1}b\le\|C^{-1/2}\delta y\|^2$')
text = text.replace('전자는 K1 contrast에서 소거되지만, 후자는 남는다.', '깊이에 무관한 공통 angular calibration은 K1 contrast에서 소거되지만, 깊이에 따라 변하는 calibration은 남는다.')
plan_path.write_text(text)

owned_roots = [folder, root / 'scripts/r61', root / 'tests/r61']
modules = [root / ('htt/htt/htt/infer/' + name) for name in
    ('r61_kinematic_images.py', 'r61_mixed_invariant.py', 'r61_box_comparison.py')]
integration_paths = [root / path for path in (
    'docs/codex_handoff/pr_backlog.yaml', 'docs/codex_handoff/pr_backlog.json',
    'docs/codex_handoff/pr_status.yaml', 'machine_readable/pr_backlog.yaml',
    'machine_readable/pr_backlog.json', 'machine_readable/pr_status.yaml',
    'docs/research_program/observational_publication_20261015/README.md',
    'docs/research_program/observational_publication_20261015/PUBLICATION_DAG.json',
    'docs/research_program/observational_publication_20261015/READY_QUEUE.json')]
files = set(modules + integration_paths)
for directory in owned_roots:
    files.update(path for path in directory.rglob('*') if path.is_file()
                 and '__pycache__' not in path.parts and path.name != 'ARTIFACT_MANIFEST.json')
artifacts = [{'path': str(path.relative_to(root)), 'bytes': path.stat().st_size,
              'sha256': digest(path)} for path in sorted(files)]
figure_groups = [
    ('RESULTS/FIGURES', 'RESULTS/IMAGES/KINEMATIC_IMAGES.json', 'scripts/r61/render_r61_constraint_figure.py', 'active main norm figure'),
    ('RESULTS/IMAGES', 'RESULTS/IMAGES/KINEMATIC_IMAGES.json', 'scripts/r61/run_r61_kinematic_images.py', 'computed norm and sky figures'),
    ('RESULTS/DEPTH_CORRECTED', 'RESULTS/DEPTH_CORRECTED/KINEMATIC_DEPTH.json', 'scripts/r61/run_r61_depth_measurement.py', 'active corrected depth evidence'),
    ('RESULTS/DEPTH', 'RESULTS/DEPTH/KINEMATIC_DEPTH.json', str((folder/'REVIEW/executed_depth_runner_before_R61_F1.py').relative_to(root)), 'historical pre-correction evidence; original numerical values unchanged'),
    ('RESULTS/MIXED', 'RESULTS/MIXED/R61_MIXED_INVARIANT_RESULT.json', 'scripts/r61/run_r61_mixed_invariant.py', 'mixed enclosing intervals')]
figures = []
for directory, source, renderer, role in figure_groups:
    for path in sorted((folder / directory).iterdir()):
        if path.suffix.lower() not in ('.png', '.pdf'):
            continue
        figures.append({'figure': str(path.relative_to(root)), 'figure_sha256': digest(path),
            'source': str((folder/source).relative_to(root)), 'source_sha256': digest(folder/source),
            'renderer': renderer, 'renderer_sha256': digest(root/renderer), 'role': role})
manifest = {'schema': 'htt.r61.artifact_manifest/1',
    'baseline_commit': record['baseline_commit'],
    'branch': record['stage10']['release_branch'],
    'identity': 'Containing Git commit plus each artifact byte hash; manifest excludes itself.',
    'active_depth_result': 'RESULTS/DEPTH_CORRECTED/KINEMATIC_DEPTH.json',
    'original_depth_evidence_preserved': True,
    'publication_status': 'NOT_READY_TO_SUBMIT',
    'artifact_count': len(artifacts), 'artifacts': artifacts, 'figure_provenance': figures}
(folder / 'ARTIFACT_MANIFEST.json').write_text(json.dumps(manifest, indent=2) + '\n')
subprocess.run(['git', 'diff', '--check'], cwd=root, check=True)
print(json.dumps({'stage_count': len(record['stages']), 'status': record['status'],
    'final_tests': '34 passed', 'artifacts_hashed': len(artifacts), 'figure_links': len(figures),
    'git_diff_check': 'PASS'}, indent=2))
