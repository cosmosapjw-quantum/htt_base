import sys,io
sys.path.insert(0,'/mnt/extdrive/workdir/htt_open_data/r35_p5_reviewed_publication')
import publish
from publish import *
O=pathlib.Path('/mnt/extdrive/workdir/htt_open_data/r36_intake_serialization_repair');publish.O=O;REL='docs/research_program/observational_publication_20261015/OBSERVABLE_BRIDGE_RECONCILIATION_20261027';D=R/REL;T=REL+'/imports/v15/cas/response_frontier.csv'
assert run('HEAD_BEFORE',['git','rev-parse','HEAD']).decode().strip()=='fb2bb0ac6a9537861c2c2e2c5157fc81787922d0';run('BRANCH',['git','branch','--show-current']);run('ORIGIN',['git','remote','get-url','origin']);run('STATUS_BEFORE',['git','status','--porcelain=v1','-z']);assert not run('INDEX_BEFORE',['git','diff','--cached','--name-only','-z']);out('PROTECTION_BEFORE.json',protection())
manifest=D/'EVIDENCE_MANIFEST.json';m=json.loads(manifest.read_text());assert len(m['files'])==156
(O/'EVIDENCE_MANIFEST_BEFORE.json').write_bytes(manifest.read_bytes());(O/'GITATTRIBUTES_BEFORE').write_bytes((R/'.gitattributes').read_bytes());(O/'CSV_LF_BEFORE.csv').write_bytes((R/T).read_bytes())
run('ATTRIBUTES_BEFORE',['git','check-attr','text','eol','filter','working-tree-encoding','--',T]);run('INDEX_TARGET_BEFORE',['git','ls-files','--stage','--',T]);run('EOL_TARGET_BEFORE',['git','ls-files','--eol','--',T])
# Query canonical blobs in one read-only batch. Never write canonical objects here.
args=['git','cat-file','--batch'];p=subprocess.run(args,cwd=R,input=''.join('HEAD:'+x['path']+'\n' for x in m['files']).encode(),capture_output=True);assert p.returncode==0
buf=io.BytesIO(p.stdout);rows=[]
for x in m['files']:
 header=buf.readline().decode().strip().split();assert len(header)==3 and header[1]=='blob';n=int(header[2]);blob=buf.read(n);assert len(blob)==n and buf.read(1)==b'\n';data=(R/x['path']).read_bytes();ch=hashlib.sha256(data).hexdigest();gh=hashlib.sha256(blob).hexdigest()
 rows.append({'path':x['path'],'expected_sha256':x['sha256'],'expected_bytes':x['bytes'],'current_sha256':ch,'current_bytes':len(data),'HEAD_blob_oid':header[0],'HEAD_blob_sha256':gh,'HEAD_blob_bytes':n,'current_matches_manifest':ch==x['sha256'] and len(data)==x['bytes'],'HEAD_matches_manifest':gh==x['sha256'] and n==x['bytes'],'current_equals_HEAD_blob':data==blob})
assert not buf.read();out('ALL_156_MANIFEST_COMPARISONS.json',rows);bad=[x for x in rows if not x['current_matches_manifest'] or not x['HEAD_matches_manifest']];assert len(bad)==1 and bad[0]['path']==T and all(x['current_equals_HEAD_blob'] for x in rows)
old=(R/T).read_bytes();assert old.count(b'\r')==0 and old.count(b'\n')==241 and len(old)==25101 and hashlib.sha256(old).hexdigest()=='351154375b7916eaa016fdd894b4a9fddb5de2e4acd02db8569a7055e9483074'
restored=old.replace(b'\n',b'\r\n');expected=next(x for x in m['files'] if x['path']==T);assert len(restored)==expected['bytes']==25342 and hashlib.sha256(restored).hexdigest()==expected['sha256']=='ebd371c45b643658693c356a84efed868133bd6c47f8b796d1b2bd6af71ef751';assert restored.replace(b'\r\n',b'\n')==old
(O/'CSV_EXACT_RESTORATION_CANDIDATE.csv').write_bytes(restored)
out('DIAGNOSIS.json',{'classification':'PACKAGING_SERIALIZATION_CRLF_LOSS','manifest_entries':156,'matching_current_and_HEAD_entries':155,'only_mismatch':bad[0],'original_LF_count':241,'restored_CRLF_count':241,'byte_difference':241,'scientific_token_changes':0,'restored_exact_manifest_sha256':expected['sha256'],'restored_exact_manifest_bytes':expected['bytes'],'source_manifest_rewrite':False,'repair_allowed_by_contract':True})
print(json.dumps(json.loads((O/'DIAGNOSIS.json').read_text()),indent=2))
