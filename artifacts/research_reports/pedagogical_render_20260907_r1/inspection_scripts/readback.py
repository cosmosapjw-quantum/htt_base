from runner import *
import base64,concurrent.futures,sys
ref=sys.argv[1]
name=sys.argv[2]
D=REPO/'artifacts/research_reports/pedagogical_render_20260907_r1'
prefix=str(D.relative_to(REPO))
def api(endpoint):
    return json.loads(subprocess.check_output(['gh','api','repos/cosmosapjw-quantum/htt_base/'+endpoint],cwd=REPO,timeout=90))
c=api('git/commits/'+ref)
assert c['sha']==ref
tree=api('git/trees/'+c['tree']['sha']+'?recursive=1')
assert not tree.get('truncated')
remote={x['path']:x for x in tree['tree'] if x['type']=='blob'}
entries=[]
for line in git('ls-tree','-r',ref,'--',prefix,'docs/research_reports/pedagogical_20260907',str(BIB.relative_to(REPO))).decode().splitlines():
    meta,path=line.split('\t',1);blob=meta.split()[2]
    assert remote[path]['sha']==blob
    entries.append((path,blob))
def fetch(item):
    path,blob=item
    data=api('git/blobs/'+blob)
    assert data['encoding']=='base64'
    raw=base64.b64decode(data['content'])
    expected=git('show',ref+':'+path)
    assert raw==expected,(path,'byte mismatch')
    return {'path':path,'git_blob':blob,'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest(),'byte_equal':True}
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
    results=list(pool.map(fetch,entries))
# Contents endpoints also bind three decisive paths directly to the pinned ref.
contents=[]
from urllib.parse import quote
for filename in ['FROM_A_CMB_SKY_MAP_TO_PHYSICAL_CONSTRAINTS.pdf','RENDER_RECEIPT.json','RETURN_TO_MAIN.md']:
    path=prefix+'/'+filename
    data=api('contents/'+quote(path,safe='/')+'?ref='+ref)
    assert data['sha']==remote[path]['sha'] and data['encoding']=='base64'
    assert base64.b64decode(data['content'])==git('show',ref+':'+path)
    contents.append(path)
head=git('ls-remote','origin','refs/heads/docs/htt-pedagogical-render-20260907-r1').decode().split()[0]
assert head==ref
write(name,{'overall':'PASS_REMOTE_BYTE_READBACK','commit':ref,'tree':c['tree']['sha'],'branch_head_matches':True,'remote_git_tree_not_truncated':True,'files_compared':len(results),'total_bytes_compared':sum(x['bytes'] for x in results),'contents_api_additional_path_readback':contents,'files':results,'scope':'Entire artifact directory plus all pedagogical source/helper/README files and fixed bibliography; no claim of other historical repository files','time_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()})
print('PASS_REMOTE_BYTE_READBACK',ref,c['tree']['sha'],len(results),'files')
