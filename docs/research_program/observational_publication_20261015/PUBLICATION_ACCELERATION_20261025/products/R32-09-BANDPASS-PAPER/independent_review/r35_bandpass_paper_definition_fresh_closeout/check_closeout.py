from pathlib import Path
import datetime, difflib, hashlib, json, re, subprocess, time

START = time.monotonic()
OUT = Path(__file__).resolve().parent
REPO = Path('/home/cosmosapjw/Dropbox/bianchi/htt_base')
BASE = REPO / 'docs/research_program/observational_publication_20261015/PUBLICATION_ACCELERATION_20261025/products/R32-09-BANDPASS-PAPER'
NEW = BASE / 'repair_01'
PACKET = Path('/mnt/extdrive/workdir/htt_open_data/r35_publication_acceleration_controller/NEXT_AFTER_BANDPASS_PAPER_DEFINITION_REPAIR.json')
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
load = lambda p: json.loads(p.read_text())
checks = {}
packet = load(PACKET)
checks['packet_binding'] = {k: packet[k] for k in ('packet_id','task_id','input_identity','candidate_identity')}
checks['agent_id'] = '/root/rc_1862a4246299c380'
checks['started_utc'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
assert packet['packet_id'] == '1862a4246299c380be0a475024d891fba39cdaeed822820a379b52e2cc23235f'
assert packet['input_identity'] == 'sha256:2cae6d43b4647b33db316df0ebd28efef8cc0e7882fe33bcfbbfff20719fe94c'
assert packet['candidate_identity'] == 'sha256:58bbadbdeb8577702b2c376b612bafe5f3c417bfbf1d1b76283763d57abfd3fc'
checks['candidate_sha256'] = sha(NEW / 'ARTIFACT_MANIFEST.json')
assert 'sha256:' + checks['candidate_sha256'] == packet['candidate_identity']
checks['base_sha256'] = sha(BASE / 'ARTIFACT_MANIFEST.json')
assert checks['base_sha256'] == 'e550dd06518c162e4ee0dc8c8d08f37e1951058dbe8bc36076a8e8de0cb57020'
for key,root,expected_count in [('base_entries',BASE,168),('candidate_entries',NEW,68)]:
    manifest = load(root/'ARTIFACT_MANIFEST.json')
    assert manifest['file_count'] == len(manifest['files']) == expected_count
    records = []
    for row in manifest['files']:
        p = root / row['path']
        actual = {'path': row['path'], 'sha256':sha(p), 'size_bytes':p.stat().st_size}
        assert actual == row, (key,row['path'],actual,row)
        records.append(actual)
    checks[key] = {'all_match': True, 'count': len(records)}
    (OUT/(key+'.json')).write_text(json.dumps(records,indent=2)+'\n')
expected_paths = sorted([str(p.relative_to(NEW)) for sub in ['data','report/generated','report/figures'] for p in (NEW/sub).rglob('*') if p.is_file()] + ['consumer.py','publication.py','test_consumer.py','test_publication.py','reproduce.py','SOURCE_BINDINGS.json','report/references.bib'])
parity = load(NEW/'NUMERICAL_ASSET_PARITY.json')
assert sorted(x['path'] for x in parity['files']) == expected_paths
assert len(expected_paths) == 33
parity_rows = []
for rel in expected_paths:
    h0,h1 = sha(BASE/rel),sha(NEW/rel)
    assert h0 == h1, rel
    parity_rows.append({'path':rel,'base_sha256':h0,'repair_sha256':h1})
(OUT/'independent_asset_parity.json').write_text(json.dumps(parity_rows,indent=2)+'\n')
checks['unchanged_assets'] = {'count':33,'all_byte_identical':True,'list_independently_enumerated':True}
checks['contract_sha256'] = sha(NEW/'data/SPECTRAL_ONLY_CONTRACT.md')
assert checks['contract_sha256'] == 'fb137b19b2ec901604691f5d4aa62f05a29e5cbe86404c3c748bf8c8c40386df'
tex = (NEW/'report/main.tex').read_text()
old_tex = (BASE/'report/main.tex').read_text()
(OUT/'manuscript.diff').write_text(''.join(difflib.unified_diff(old_tex.splitlines(True),tex.splitlines(True),fromfile='base/report/main.tex',tofile='repair_01/report/main.tex')))
defs = {
 'planck_intensity': r'B_\nu(T)=\frac{2h\nu^3}{c^2[\exp(h\nu/(k_BT))-1]}',
 'synchrotron_normalization': r'S_s(\nu,\beta)=b_{\nu_s}\left(\frac{\nu}{\nu_s}\right)^{\beta+2}',
 'dust_varying_temperature_ratio': r'\frac{B_\nu(T)}{B_{\nu_d}(T)}',
 'varying_temperature_explicit': 'The dust denominator uses the same varying $T$ as the numerator before differentiation; it is not held at $T_d$.',
 'lfi_effective_transmission': r'\tau_i(\nu)=g_i(\nu)\left(\frac{\nu_{{\rm ref},i}}{\nu}\right)^2',
 'half_bin_shift': r'\Delta\nu_i=\frac{\nu_{i,\mathrm{last}}-\nu_{i,\mathrm{first}}}{2(N_i-1)}',
 'hfi_flag_threshold': r'\texttt{FLAG} exactly \texttt{F} and transmission above $B_T$',
 'second_derivative_definition': r'$T_d^2\partial_T^2$ at the pivot, not $(T\partial_T)^2$',
 'signed_carrier': r'$E_2(5),E_3(7),B_2(5),B_3(7)$',
 'temperature_separate': 'A scalar temperature coefficient is a different observable and is not appended to this carrier.',
 'data_availability': r'\section*{Data availability}',
}
checks['source_definition_presence'] = {k: v in tex for k,v in defs.items()}
assert all(checks['source_definition_presence'].values())
refs = re.findall(r'\\(?:input|includegraphics)(?:\[[^\]]*\])?\{([^}]+)\}',tex)
assert all((NEW/'report'/p).is_file() for p in refs)
checks['included_assets'] = refs
receipt=load(NEW/'raw/latexmk_repair.receipt.json')
assert receipt['exit_code'] == 0
assert receipt['main_tex_sha256'] == sha(NEW/'report/main.tex')
assert receipt['references_bib_sha256'] == sha(NEW/'report/references.bib')
log=(NEW/'report/main.log').read_text()
stdout=(NEW/'raw/latexmk_repair.stdout').read_text()
bad_patterns=[r'^!',r'undefined',r'Overfull',r'Underfull',r'multiply defined',r'No file ',r'not found']
issues=[line for line in log.splitlines() if any(re.search(p,line,re.I) for p in bad_patterns)]
assert not issues,issues
assert 'Latexmk: All targets (main.pdf) are up-to-date' in stdout
assert 'Output written on main.pdf (11 pages, 356626 bytes).' in log
assert (NEW/'report/main.pdf').stat().st_size == 356626
checks['reused_actual_build']={'receipt':str(NEW/'raw/latexmk_repair.receipt.json'),'exit_code':0,'source_binding_match':True,'clean_final_log':True,'warning_lines':[line for line in log.splitlines() if 'Warning:' in line],'initial_pass_warnings_retained':True,'new_build_invoked':False}
commands=[['git','status','--short','--branch'],['git','rev-parse','HEAD'],['git','remote','get-url','origin'],['pdfinfo',str(NEW/'report/main.pdf')],['pdftotext','-layout',str(NEW/'report/main.pdf'),str(OUT/'main.layout.txt')],['pdftoppm','-scale-to','900','-png',str(NEW/'report/main.pdf'),str(OUT/'page')]]
cmd_results=[]
for i,command in enumerate(commands):
    t=time.monotonic();p=subprocess.run(command,cwd=REPO,capture_output=True,text=True)
    (OUT/f'command_{i:02d}.stdout').write_text(p.stdout)
    (OUT/f'command_{i:02d}.stderr').write_text(p.stderr)
    cmd_results.append({'command':command,'exit_code':p.returncode,'elapsed_seconds':time.monotonic()-t,'stdout':str(OUT/f'command_{i:02d}.stdout'),'stderr':str(OUT/f'command_{i:02d}.stderr')})
    assert p.returncode == 0,command
checks['commands']=cmd_results
assert re.search(r'Pages:\s+11\b',(OUT/'command_03.stdout').read_text())
pdf_text=(OUT/'main.layout.txt').read_text()
assert '??' not in pdf_text
assert 'The dust denominator uses the same varying' in pdf_text
checks['pdf']={'pages':11,'unresolved_reference_markers':False,'source_text_present':True,'rendered_pages':len(list(OUT.glob('page-*.png'))),'sha256':sha(NEW/'report/main.pdf')}
assert checks['pdf']['rendered_pages']==11
checks['elapsed_seconds']=time.monotonic()-START
checks['status']='PASS'
(OUT/'CHECKS.json').write_text(json.dumps(checks,indent=2)+'\n')
print(json.dumps({k:v for k,v in checks.items() if k not in ['commands','included_assets']},indent=2))
