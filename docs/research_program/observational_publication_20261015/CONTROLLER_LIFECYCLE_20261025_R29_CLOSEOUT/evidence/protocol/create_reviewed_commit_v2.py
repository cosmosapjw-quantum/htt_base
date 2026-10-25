from pathlib import Path
import json,hashlib,os,subprocess,time,traceback
import prepare_publication as m
import protocol_baseline_v2 as baseline
O=m.O;sha=m.sha;save=m.save;commands=[]
def git(args,env=m.base,data=None,ok=(0,)):
 assert args[0] in ('config','var','rev-parse','ls-remote','status','commit-tree','cat-file')
 if args[0]=='commit-tree':assert env is m.write and 'GIT_ALTERNATE_OBJECT_DIRECTORIES' not in env
 x=subprocess.run(['git',*args],cwd=m.R,env=env,input=data,capture_output=True,timeout=180)
 commands.append({'argv':['git',*args],'environment_kind':'ISOLATED_NO_ALTERNATES' if env is m.write else 'ALTERNATE_READ_ONLY' if env is m.read else 'CANONICAL_READ_ONLY','exit_code':x.returncode,'stdout':x.stdout.decode(errors='replace'),'stderr':x.stderr.decode(errors='replace')});save('COMMIT_RAW_COMMANDS.json',commands)
 assert x.returncode in ok,commands[-1]
 return x.stdout

def main():
 assert not any((O/n).exists() for n in ('COMMIT_PREPARATION_RETURN.json','FIRST_COMMIT_FAILURE.json')),'no blind commit retry'
 a=json.loads((O/'APPROVED_COMMIT_INPUT_V2.json').read_text());assert a['status']=='ROOT_GO_REVIEWED_EXACT_TREE_COMMIT'
 t=json.loads((O/'PREPARATION_RETURN.json').read_text());TREE=t['tree'];assert a['tree']==TREE and a['parent']==m.PARENT and a['manifest_sha256']==sha(O/'FILE_MANIFEST.json')
 assert a['review_seals'],'sealed independent approval/root exact binding required'
 for s in a['review_seals']:assert sha(s['path'])==s['sha256']
 before=m.snapshot();baseline.validate_action(a,'commit',before,m);save('CANONICAL_METADATA_BEFORE_COMMIT.json',before)
 st=git(['status','--porcelain=v1','--untracked-files=normal']);assert st==(O/'STATUS_BEFORE.bin').read_bytes()
 assert git(['rev-parse','HEAD']).decode().strip()==m.LOCAL;assert git(['ls-remote','--exit-code',m.URL,m.REF]).decode().strip().split()==[m.PARENT,m.REF]
 sign=git(['config','--bool','--get','commit.gpgsign'],ok=(0,1)).decode().strip();assert sign in ('','false')
 author=git(['var','GIT_AUTHOR_IDENT']).decode().strip();committer=git(['var','GIT_COMMITTER_IDENT']).decode().strip()
 def setident(kind,v):
  identity,ts,zone=v.rsplit(' ',2);name,email=identity.rsplit(' <',1);m.write.update({f'GIT_{kind}_NAME':name,f'GIT_{kind}_EMAIL':email[:-1],f'GIT_{kind}_DATE':ts+' '+zone})
 setident('AUTHOR',author);setident('COMMITTER',committer)
 message='R29: Preserve controller state and bounded repair continuation\n';(O/'COMMIT_MESSAGE.txt').write_text(message)
 baseline.validate_action(a,'commit',m.snapshot(),m);assert m.snapshot()==before
 save('COMMIT_PREPARATION_RETURN.json',{'status':'STARTED','tree':TREE,'parent':m.PARENT,'push_performed':False})
 commit=git(['commit-tree',TREE,'-p',m.PARENT,'-F',str(O/'COMMIT_MESSAGE.txt')],env=m.write).decode().strip()
 cp=git(['cat-file','commit',commit],env=m.read);assert hashlib.sha1(b'commit '+str(len(cp)).encode()+b'\0'+cp).hexdigest()==commit
 headers,body=cp.split(b'\n\n',1);assert [l for l in headers.decode().splitlines() if l.startswith('tree ')]==['tree '+TREE];assert [l for l in headers.decode().splitlines() if l.startswith('parent ')]==['parent '+m.PARENT];assert body.decode()==message
 (O/'CANDIDATE_COMMIT_PAYLOAD.txt').write_bytes(cp)
 hookcfg=git(['config','--path','--get','core.hooksPath'],ok=(0,1)).decode().strip();hd=Path(hookcfg) if hookcfg else m.G/'hooks';hd=hd if hd.is_absolute() else m.R/hd;hp=hd/'pre-push';hook=None
 if hp.exists() or hp.is_symlink():
  assert hp.is_file() and os.access(hp,os.X_OK);hook={'path':str(hp.resolve()),'sha256':sha(hp)}
 guard=m.B/'r25_enospc_publication_plan_repair/hooks/pre-push';assert sha(guard)=='d6a2e8993a3e1fdf4b5969d2be60e7f796aaef14cacf51fcfad2183cc4b9f150' and os.access(guard,os.X_OK)
 save('PUBLICATION_GUARD_BINDING.json',{'remote_url':m.URL,'target_ref':m.REF,'parent':m.PARENT,'candidate':commit,'existing_hook':hook})
 after=m.snapshot();save('CANONICAL_METADATA_AFTER_COMMIT.json',after);assert before==after;assert git(['status','--porcelain=v1','--untracked-files=normal'])==st
 packet={'status':'EXACT_COMMIT_READY_FOR_ROOT_BINDING_BEFORE_PUSH','commit':commit,'tree':TREE,'sole_parent':m.PARENT,'manifest_sha256':sha(O/'FILE_MANIFEST.json'),'payload_sha256':sha(O/'CANDIDATE_COMMIT_PAYLOAD.txt'),'guard_binding_sha256':sha(O/'PUBLICATION_GUARD_BINDING.json'),'review_seals':a['review_seals'],'author':author,'committer':committer,'message':message,'canonical_after_commit_sha256':sha(O/'CANONICAL_METADATA_AFTER_COMMIT.json'),'canonical_metadata_unchanged':True,'canonical_status_unchanged':True,'writer_alternates_absent':True,'existing_hook':hook,'push_performed':False,'requested_runtime':'gpt-6.1-sol/medium','observed_runtime':'UNKNOWN'}
 save('CANDIDATE_COMMIT_REVIEW_PACKET.json',packet);save('COMMIT_PREPARATION_RETURN.json',packet);print(json.dumps(packet,indent=2))
if __name__=='__main__':
 try:main()
 except Exception as e:save('FIRST_COMMIT_FAILURE.json',{'error':str(e),'traceback':traceback.format_exc()});raise
