from pathlib import Path
import os,json,hashlib,subprocess,datetime,traceback,time
import prepare_publication as m
import protocol_baseline_v2 as baseline
O=m.O;save=m.save;sha=m.sha;commands=[]
def git(args,env=m.base,ok=(0,)):
 assert args[0] in ('status','rev-parse','for-each-ref','config','ls-remote','cat-file','-c')
 x=subprocess.run(['git',*args],cwd=m.R,env=env,capture_output=True,timeout=240)
 commands.append({'argv':['git',*args],'environment_kind':'EXTERNAL_READ_TRAVERSAL_OR_APPROVED_PUSH' if env is not m.base else 'CANONICAL_READ_ONLY','exit_code':x.returncode,'stdout':x.stdout.decode(errors='replace'),'stderr':x.stderr.decode(errors='replace')});save('PUSH_RAW_COMMANDS.json',commands)
 assert x.returncode in ok,commands[-1]
 return x

def main():
 assert not any((O/n).exists() for n in ('PUSH_ATTEMPT_STARTED.json','FIRST_PUSH_FAILURE.json')),'no blind push retry'
 a=json.loads((O/'APPROVED_PUSH_INPUT_V2.json').read_text());assert a['status']=='ROOT_GO_EXACT_REVIEWED_COMMIT_PUSH'
 packet=json.loads((O/'CANDIDATE_COMMIT_REVIEW_PACKET.json').read_text());C=packet['commit'];TREE=packet['tree'];assert a['commit']==C and a['tree']==TREE and a['sole_parent']==m.PARENT
 assert a['candidate_packet_sha256']==sha(O/'CANDIDATE_COMMIT_REVIEW_PACKET.json')
 assert a['review_seals'],'sealed independent approval/root exact binding required'
 for s in a['review_seals']:assert sha(s['path'])==s['sha256']
 assert packet['manifest_sha256']==sha(O/'FILE_MANIFEST.json') and packet['payload_sha256']==sha(O/'CANDIDATE_COMMIT_PAYLOAD.txt')
 binding=O/'PUBLICATION_GUARD_BINDING.json';assert packet['guard_binding_sha256']==sha(binding)
 guard=m.B/'r25_enospc_publication_plan_repair/hooks/pre-push';assert sha(guard)=='d6a2e8993a3e1fdf4b5969d2be60e7f796aaef14cacf51fcfad2183cc4b9f150' and os.access(guard,os.X_OK)
 before=m.snapshot();baseline.validate_action(a,'push',before,m);save('CANONICAL_METADATA_BEFORE_PUSH.json',before)
 st=git(['status','--porcelain=v1','--untracked-files=normal']).stdout;assert st==(O/'STATUS_BEFORE.bin').read_bytes();(O/'STATUS_BEFORE_PUSH.bin').write_bytes(st)
 assert git(['rev-parse','HEAD']).stdout.decode().strip()==m.LOCAL
 assert not(m.G/'shallow').exists() and not(m.G/'info/grafts').exists();assert not git(['for-each-ref','--format=%(refname)','refs/replace']).stdout.strip()
 hc=git(['config','--path','--get','core.hooksPath'],ok=(0,1)).stdout.decode().strip();hd=Path(hc) if hc else m.G/'hooks';hd=hd if hd.is_absolute() else m.R/hd;hp=hd/'pre-push';hook=None
 if hp.exists() or hp.is_symlink():assert hp.is_file() and os.access(hp,os.X_OK);hook={'path':str(hp.resolve()),'sha256':sha(hp)}
 assert json.loads(binding.read_text())=={'remote_url':m.URL,'target_ref':m.REF,'parent':m.PARENT,'candidate':C,'existing_hook':hook}
 cfg=git(['config','--get-regexp',r'^(url\..*\.(insteadof|pushinsteadof)|remote\..*\.(url|pushurl)|core\.hookspath|push\.|submodule\.)'],ok=(0,1)).stdout
 assert not any(b'.insteadof ' in l.lower() or b'.pushinsteadof ' in l.lower() for l in cfg.splitlines())
 advertised=git(['ls-remote','--exit-code',m.URL,m.REF]).stdout.decode().strip().split();assert advertised==[m.PARENT,m.REF]
 assert git(['cat-file','commit',C],env=m.read).stdout==(O/'CANDIDATE_COMMIT_PAYLOAD.txt').read_bytes()
 pushenv=dict(m.read,R25_PUSH_GUARD_BINDING=str(binding),R25_PUSH_GUARD_BINDING_SHA256=sha(binding));args=['-c','core.hooksPath='+str(guard.parent),'push','--porcelain','--no-follow-tags','--recurse-submodules=no',m.URL,C+':'+m.REF]
 baseline.validate_action(a,'push',m.snapshot(),m);assert m.snapshot()==before
 save('PUSH_ATTEMPT_STARTED.json',{'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'command':['git',*args],'approval_sha256':sha(O/'APPROVED_PUSH_INPUT_V2.json'),'expected_advertised_parent':m.PARENT,'guard_binding_sha256':sha(binding)})
 x=git(args,env=pushenv,ok=tuple(range(256)));(O/'PUSH_STDOUT.txt').write_bytes(x.stdout);(O/'PUSH_STDERR.txt').write_bytes(x.stderr)
 ret={'status':'PROVIDER_RETURNED','commit':C,'tree':TREE,'sole_parent':m.PARENT,'provider_exit_code':x.returncode,'provider_success':x.returncode==0,'push_performed':True,'remote_url':m.URL,'remote_ref':m.REF};save('PUBLICATION_RETURN.json',ret)
 remote=git(['ls-remote','--exit-code',m.URL,m.REF]).stdout.decode().strip().split();ret['remote_verification']=remote;save('PUBLICATION_RETURN.json',ret)
 assert x.returncode==0,'provider push failure; no automatic retry';assert remote==[C,m.REF]
 after=m.snapshot();save('CANONICAL_METADATA_AFTER_PUSH.json',after);assert before==after
 sta=git(['status','--porcelain=v1','--untracked-files=normal']).stdout;(O/'STATUS_AFTER_PUSH.bin').write_bytes(sta);assert st==sta;assert git(['rev-parse','HEAD']).stdout.decode().strip()==m.LOCAL
 mf=json.loads((O/'FILE_MANIFEST.json').read_text());ret.update(status='PUSHED_VERIFIED_R1_CANONICAL_METADATA_PRESERVED',commit_url='https://github.com/cosmosapjw-quantum/htt_base/commit/'+C,files=mf['file_count'],bytes=mf['total_bytes'],verification_tier='R1_PROVIDER_EXIT0_AND_EXACT_REMOTE_REF_OID',post_push_content_download=False,canonical_metadata_unchanged=True,canonical_status_unchanged=True,local_HEAD=m.LOCAL,local_checkout_synchronized=False,scientific_admission='UNCHANGED',no_merge_or_submission=True,requested_runtime='gpt-6.1-sol/medium',observed_runtime='UNKNOWN',guard_binding_sha256=sha(binding),review_seals=a['review_seals'],candidate_packet_sha256=sha(O/'CANDIDATE_COMMIT_REVIEW_PACKET.json'),manifest_sha256=sha(O/'FILE_MANIFEST.json'),canonical_before_sha256=sha(O/'CANONICAL_METADATA_BEFORE_PUSH.json'),canonical_after_sha256=sha(O/'CANONICAL_METADATA_AFTER_PUSH.json'),ownership_released=True)
 save('PUBLICATION_RETURN.json',ret);print(json.dumps(ret,indent=2))
if __name__=='__main__':
 try:main()
 except Exception as e:save('FIRST_PUSH_FAILURE.json',{'error':str(e),'traceback':traceback.format_exc()});raise
