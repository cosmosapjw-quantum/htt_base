import ast,hashlib,json,pathlib
ROOT=pathlib.Path(__file__).parent
CONTRACT=pathlib.Path('/mnt/extdrive/workdir/htt_open_data/r36_pr4_concurrency_framing/IMPLEMENTATION_CONTRACT.json')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(CONTRACT)=='223fde11036657cea437313e06f26a94190f3eda27d40680bc689f0da38e1ac2'
c=json.loads(CONTRACT.read_text());base=pathlib.Path(c['source_bindings']['active_helper']['path']);old=base.read_bytes();new=(ROOT/'fetch_commander_mc.py').read_bytes();reverse=new
assert sha(base)=='7d0c3ee5a2afe9655f86f674052323a69da0fc64d920d3eb2cb81c3eb2e6a2ee'
for r in c['production_source_allowlist']['only_two_lines']:
 assert reverse.count(r['new'].encode())==1
 reverse=reverse.replace(r['new'].encode(),r['old'].encode())
assert reverse==old
assert ast.dump(ast.parse(reverse))==ast.dump(ast.parse(old))
# Only accepted normalized delta: help keyword and upper guard/message 4->16.
import test_affected_controls as affected
assert pathlib.Path(affected.m.__file__)==ROOT/'fetch_commander_mc.py'
expected=sha(ROOT/'fetch_commander_mc.py')
observations=[]
for p in ROOT.glob('concurrent-*/OBSERVATION.json'):
 v=json.loads(p.read_text());assert len(v['requests'])==16;assert len({r['url'] for r in v['requests']})==16
 assert len(v['batch']['results'])==18
 assert [r['status'] for r in v['batch']['results']]==['INTERRUPTED']*18
 assert v['batch']['network_bytes']==16*16384
 assert all(r['source_sha256']==expected for r in v['batch']['results'])
 live=json.loads((p.parent/'LIVE_16_BEFORE_SIGNAL.json').read_text());assert len(live['live_children'])==16;assert live['queued']==2
 for child in live['live_children']:assert not pathlib.Path('/proc',str(child['pid'])).exists()
 observations.append({'path':str(p),'signal':v['signal'],'active':16,'queued':2,'retained_decoded_bytes':v['batch']['network_bytes']})
assert sorted(v['signal'] for v in observations)==[2,15]
# First failed fixture's exact owned PIDs must also all have exited.
for start in ROOT.glob('concurrent-*/attempts/**/CURL_START.json'):
 assert not pathlib.Path('/proc',str(json.loads(start.read_text())['pid'])).exists()
print(json.dumps({'source_invariance':'PASS','active_helper_unchanged_sha256':sha(base),'candidate_sha256':expected,'normalized_AST_equal':True,'affected_control_import':affected.m.__file__,'real_16_active_observations':observations,'all_fixture_owned_children_absent':True},indent=2))
