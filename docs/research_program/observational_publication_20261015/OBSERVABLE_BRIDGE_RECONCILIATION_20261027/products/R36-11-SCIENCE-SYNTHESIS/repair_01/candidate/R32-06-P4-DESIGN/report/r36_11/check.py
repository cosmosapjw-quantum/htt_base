#!/usr/bin/env python3
"""Bounded checks of an applied P4 manuscript overlay; no science producer runs."""
import argparse
import hashlib
import json
import pathlib
import re
import subprocess

HERE = pathlib.Path(__file__).resolve().parent
TARGET = HERE.parent.parent
CONTRACT = json.loads((HERE / 'SOURCE_CONTRACT.json').read_text())
EXPECTED = json.loads((HERE / 'EXPECTED_APPLIED.json').read_text())
RETAINED = json.loads((HERE / 'RETAINED_ORIGINAL.json').read_text())
MAP = json.loads((HERE / 'NUMBER_FIGURE_MAP.json').read_text())
BASE = pathlib.Path(CONTRACT['destination']['existing_root'])

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def require(condition, label):
    if not condition:
        raise AssertionError(label)

parser = argparse.ArgumentParser()
parser.add_argument('--target', type=pathlib.Path, default=TARGET)
args = parser.parse_args()
require(args.target.resolve() == TARGET.resolve(), 'wrong target path')
require(sha(HERE / 'SOURCE_CONTRACT.json') == 'a08fb04382885c4ba7f62cd213a10de6a5755e609a47ca27d982629ec0e27ebf', 'source contract drift')
for key, binding in CONTRACT['source_bindings'].items():
    source = pathlib.Path(binding['path'])
    if key in EXPECTED:
        rel = source.relative_to(BASE)
        require(sha(HERE / 'baseline' / rel) == binding['sha256'], f'baseline drift: {key}')
        require(sha(TARGET / rel) == EXPECTED[key], f'applied source drift: {key}')
    else:
        require(sha(source) == binding['sha256'], f'original source drift: {key}')
for name, expected in RETAINED.items():
    require(sha(TARGET / 'report' / name) == expected, f'old numerical or figure drift: {name}')
for name, source_key in [('pm_history_power.pdf', 'pm_power_figure'), ('pm_history_information.pdf', 'pm_information_figure')]:
    require(sha(TARGET / 'report' / name) == CONTRACT['source_bindings'][source_key]['sha256'], f'PM figure drift: {name}')
require(sha(TARGET / 'report/pm_history_supplement.json') == CONTRACT['source_bindings']['pm_result']['sha256'], 'PM supplement drift')
p = json.loads((TARGET / 'report/pm_history_supplement.json').read_text())
s = (TARGET / 'science/MANUSCRIPT.md').read_text()
tex = (TARGET / 'report/main.tex').read_text()
for key, n in [('primary_spin_glide6', 6), ('all97_sensitivity', 97)]:
    q = p['gram'][key]
    m = MAP['profiles'][key]
    require(q['profile']['rank'] == 5 and q['profile']['nuisance_rank'] == n, f'profile rank: {key}')
    require(m['coefficients'] == q['joint']['selected_sample_full5_coefficients_uasyr'], f'coefficient map: {key}')
    require(m['eigenvalues'] == q['profile']['eigenvalues'], f'eigenvalue map: {key}')
    require(m['covariances'] == q['joint']['full5_covariance'], f'full covariance: {key}')
    require(m['cross_covariance'] == q['joint']['joint_signal_nuisance_covariance'], f'cross covariance: {key}')
    require(len(m['cross_covariance']) == 5 and all(len(row) == n for row in m['cross_covariance']), f'cross covariance shape: {key}')
    line = '| ' + str(n) + ' | ' + ' | '.join(f'{x:.6f}' for x in m['coefficients']) + ' |'
    require(line in s, f'displayed signed coefficients: {key}')
require(set(re.findall(r'\\tag\{(\d+)\}', s)) == set(map(str, range(1, 36))), 'equations 1-35')
require(tex.count('\\includegraphics') == 5 and tex.count('\\begin{figure}') == 5, 'five figure inventory')
require('Markers are retained evaluated radius points' in s and 'connecting segments are visual guides, not evaluated interpolation' in s and 'numerical table and Eq. (35)' in s, 'power caption semantics')
require('\\cite{Marcori2018}' in tex and '\\bibitem{Marcori2018}' in tex, 'Marcori citation')
for rel in ['science/CLAIM_SOURCE_MAP.md', 'report/CLAIM_SOURCE_MAP.md']:
    text = (TARGET / rel).read_text()
    for locator in ['report/r36_11/SOURCE_CONTRACT.json', 'report/r36_11/NUMBER_FIGURE_MAP.json', 'report/r36_11/assemble.py', 'report/pm_history_supplement.json']:
        require(locator in text, f'locator {locator} in {rel}')
for history in p['history_images']:
    require(history['rank'] == 5 and history['null_residual_relative'] < 1e-12, 'retained history rank/null')
require(p['response']['near_limit'] == '+sigma_o' and p['response']['distant_fixed_endpoint_limit'] == '-sigma_o', 'endpoint response signs')
log = (TARGET / 'report/main.log')
if log.exists():
    require(not re.search(r'undefined|Overfull|^!', log.read_text(), re.M), 'LaTeX log errors or unresolved warning')
print('Applied P4 source, preimage, number, covariance, figure, caption and citation checks PASS')
