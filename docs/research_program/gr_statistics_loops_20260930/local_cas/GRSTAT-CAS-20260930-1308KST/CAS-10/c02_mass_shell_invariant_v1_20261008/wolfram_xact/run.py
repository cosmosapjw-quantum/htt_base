#!/usr/bin/env python3
import hashlib,json,pathlib,subprocess,shutil,sys
from datetime import datetime,timezone
H=pathlib.Path(__file__).resolve().parent; U=H.parent
C=U/'EXECUTION_CONTRACT.json'; I=U/'ADMITTED_INPUTS.json'; S=H/'verify.wl'; O=H/'certificate.engine.json'; R=H/'result.json'
EC='c6957c9d87d416668d2f33ee94946aa04f3bf0da09aa06cac7cdb07b0eaab2ef'; EI='6f699739b3835b3bbaa02202bcabf7381a0d57860e2eb28f8441c8d392fda074'
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 if sha(C)!=EC or sha(I)!=EI: print(json.dumps({'status':'MISALIGNED_ASSUMPTIONS','checks':{'CAS-10-C02':False},'domain_assumption_diff':['frozen SHA mismatch'],'counterexample':None})); return 2
 argv=[shutil.which('wolframscript') or 'wolframscript','-file',str(S),str(O)]; pr=subprocess.run(argv,cwd=H,text=True,capture_output=True,timeout=1800)
 (H/'wolfram.stdout.log').write_text(pr.stdout); (H/'wolfram.stderr.log').write_text(pr.stderr)
 cert=json.loads(O.read_text()) if O.exists() else {}; keys=['mass_shell_algebra','rest_space_positive_identity','xact_tensor_symmetry','branches_controls']; ok=pr.returncode==0 and set(cert.get('checks',{}))==set(keys) and all(cert['checks'].values())
 d={'axis':'wolfram_xact','status':'PASS' if ok else 'FAIL','contract_sha256':sha(C),'input_sha256':sha(I),'source_sha256':sha(S),'evidence_class':'exact','completed_at':datetime.now(timezone.utc).isoformat(),'checks':{'CAS-10-C02':ok},'domain_assumption_diff':[],'counterexample':None,'internal_checks':cert.get('checks',{}),'tool_versions':{'wolfram':cert.get('wolfram_version'),'xTensor':cert.get('xtensor_version')},'commands':[{'argv':argv,'cwd':str(H),'exit_code':pr.returncode,'stdout_path':str(H/'wolfram.stdout.log'),'stderr_path':str(H/'wolfram.stderr.log')}],'statement_alignment':{'domain':'real symmetric S, future unit timelike u, c>0','branch':'positive rest-space metric on u-perp','scope':'CAS10 C02 only'},'launch_id':None,'authority_status':'UNAVAILABLE_PER_OWNER_DIRECT_LOCAL_EXECUTION','observed_model':'UNKNOWN','observed_effort':'UNKNOWN','scientific_admission':'HOLD'}
 R.write_text(json.dumps(d,indent=2,sort_keys=True)+'\n'); print(json.dumps({'status':d['status'],'checks':d['checks'],'domain_assumption_diff':[],'counterexample':None,'result_path':str(R)},separators=(',',':'))); return 0 if ok else 2
if __name__=='__main__': sys.exit(main())
