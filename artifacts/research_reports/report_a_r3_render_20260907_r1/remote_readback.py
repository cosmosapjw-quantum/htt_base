import sys,json,base64,subprocess,hashlib,datetime,concurrent.futures
from pathlib import Path
from runner import RUN,REPO,git,ident
PUB='artifacts/research_reports/report_a_r3_render_20260907_r1'
BRANCH='docs/htt-report-a-r3-render-20260907-r1'
head=git('rev-parse','HEAD').decode().strip()
tree=git('rev-parse','HEAD^{tree}').decode().strip()
def api(path):
    return json.loads(subprocess.check_output(['gh','api','repos/cosmosapjw-quantum/htt_base/'+path],cwd=REPO,timeout=60))
entries=api('contents/'+PUB+'?ref='+head)
local={x.name for x in (REPO/PUB).iterdir() if x.is_file()}
assert {x['name'] for x in entries}==local

def check(e):
    obj=api('git/blobs/'+e['sha'])
    assert obj['encoding']=='base64'
    raw=base64.b64decode(obj['content'])
    own=(REPO/PUB/e['name']).read_bytes()
    assert own==raw,e['name']
    ids=ident(raw)
    assert ids['git_blob']==e['sha']
    return {'path':e['path'],**ids,'exact_remote_byte_match':True}
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
    checks=list(pool.map(check,entries))
ref=git('ls-remote','--heads','origin',BRANCH).decode().strip()
assert ref.split()[0]==head
result={'schema':'htt.report_a.r3.remote_readback.v1','observed_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'commit':head,'tree':tree,'remote_ref':ref,'method':'GitHub Contents API at immutable commit followed by Git Blobs API base64 decoding and complete local-byte equality','file_count':len(checks),'total_bytes':sum(x['bytes'] for x in checks),'all_pass':True,'scope':'All files present in the publication directory at this exact commit; later evidence commits are outside this observation','files':checks}
(RUN/sys.argv[1]).write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
print(json.dumps({k:v for k,v in result.items() if k!='files'},indent=2))
