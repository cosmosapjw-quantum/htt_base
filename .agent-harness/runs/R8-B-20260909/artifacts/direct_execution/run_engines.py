"""Direct replay of existing CAS drafts plus the already compiled Lean repair.
No independent-four-axis capability is issued by this operational report.
"""
import concurrent.futures,hashlib,json,pathlib,subprocess,time
ROOT=pathlib.Path(__file__).resolve().parents[5];HERE=pathlib.Path(__file__).resolve().parent
run=ROOT/'.agent-harness/runs/R8-B-20260909';spec=json.loads((run/'artifacts/observed_cas/run_spec.json').read_text())
contract=json.loads((run/'CAS_CONTRACT.json').read_text());obligations=contract['target']['exact_test_obligations']
def execute(item):
    axis,entry=item;t=time.monotonic()
    r=subprocess.run(entry['argv'],cwd=ROOT,capture_output=True,text=True,timeout=entry['timeout_seconds'])
    (HERE/(axis+'_stdout.json')).write_text(r.stdout);(HERE/(axis+'_stderr.txt')).write_text(r.stderr)
    data=json.loads(r.stdout)
    good=r.returncode==0 and all(data.get('checks',{}).get(key) is True for key in obligations) and not data.get('domain_assumption_diff') and data.get('counterexample') is None
    return axis,{'status':'PASS' if good else 'FAIL','argv':entry['argv'],'exit_code':r.returncode,'elapsed_seconds':time.monotonic()-t,'checks':data.get('checks'),'tool_versions':data.get('tool_versions'),'stdout_sha256':hashlib.sha256(r.stdout.encode()).hexdigest()}
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:results=dict(pool.map(execute,spec['axes'].items()))
lean=json.loads((HERE/'lean_direct_receipt.json').read_text());log=(HERE/'lean_direct.log').read_text()
assert lean['source_sha256']==hashlib.sha256((HERE/'O4.lean').read_bytes()).hexdigest()
expected=['q_trace','q_swap','q_sign','q_zero','o_trace','o_vector_perm','o_index_perm','o_sign','o_zero','null_cone','q_real_null','o_real_null']
lean_good=lean['exit_code']==0 and 'sorryAx' not in log and ': error:' not in log and all("'R8O4."+t+"' depends on axioms:" in log for t in expected) and (HERE/'O4.olean').is_file()
results['lean']={'status':'PASS' if lean_good else 'FAIL','checks':{key:lean_good for key in obligations},'source_sha256':lean['source_sha256'],'receipt':'lean_direct_receipt.json','compiled_sha256':hashlib.sha256((HERE/'O4.olean').read_bytes()).hexdigest(),'independence':'HOST_REPAIRED_PREVIOUS_INDEPENDENT_DRAFT'}
out={'status':'FOUR_ENGINE_CHECKS_PASS' if all(x['status']=='PASS' for x in results.values()) else 'CHECK_FAILURE','contract_sha256':hashlib.sha256((run/'CAS_CONTRACT.json').read_bytes()).hexdigest(),'axes':results,'independence':'THREE_BLIND_DRAFTS_PLUS_HOST_LEAN_COMPLETION','four_axis_independent_capability':False,'scientific_claim_promotion':False,'scope':'O4 STF2/STF3 trace/sign/permutation and complex bilinear null cone identities only','prior_cas_adjudication':'Original CAS_BLOCKED retained; this report does not replace it'}
(HERE/'engine_results.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2));raise SystemExit(0 if out['status']=='FOUR_ENGINE_CHECKS_PASS' else 1)
