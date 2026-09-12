import json
from pathlib import Path
import pytest
from scripts.observed_runs.run_tensor_joint_r8 import Handler,execute_campaign,production_handlers
from scripts.observed_runs.r8_campaign_actions import checked_json,r3_scopes

ROOT=Path(__file__).resolve().parents[2]


def test_all_52_actions_have_concrete_handlers():
    dag=json.loads((ROOT/'docs/research_program/tensor_joint_r8/campaign_dag.json').read_text())
    actions={a['action'] for n in dag['nodes'] for a in n['actions']}
    assert len(actions)==52
    assert actions<=production_handlers(ROOT/'docs/generated/tensor_joint_r8/ac').keys()


def test_failed_jet_and_recession_preserve_distance_and_finite_image(tmp_path):
    evidence=tmp_path/'value';evidence.write_text('verified fixture')
    def emit(cap):
        def execute(attempt,preds):return {'capabilities':[cap],'evidence':[evidence],'capability_scopes':{cap:['valid_product']}}
        return Handler(execute)
    def fail(attempt,preds):raise RuntimeError('failing sibling')
    actions=[{'action':a,'requires':[],'produces':[c]} for a,c in (('distance','DISTANCE'),('jet','R3_JET_STATUS'),('image','IMAGE'),('recession','RECESSION'))]
    dep=lambda name,cap,scope=None:{'id':name,'after':['A'],'actions':[{'action':name,'requires':[{'node':'A','capability':cap,**({'scope':scope} if scope else {})}],'produces':[]}]}
    dag={'nodes':[{'id':'A','after':[],'actions':actions},dep('distance_compare','DISTANCE','valid_product'),
                  dep('other_product','DISTANCE','wrong_product'),dep('jet_use','R3_JET_CHANNEL'),dep('finite','IMAGE')]}
    handlers={**{a:emit(c) for a,c in (('distance','DISTANCE'),('jet','R3_JET_STATUS'),('image','IMAGE'))},'recession':Handler(fail)}
    for name in ('distance_compare','other_product','jet_use','finite'):handlers[name]=Handler(lambda a,p:{'scientific_outcome':'RAN'})
    out=execute_campaign(dag,tmp_path/'run',handlers)
    for name in ('distance_compare','finite'):assert out['nodes'][name]['actions'][0]['scientific_outcome']=='RAN'
    for name in ('other_product','jet_use'):assert out['nodes'][name]['actions'][0]['reason']=='REQUIRED_CAPABILITY_UNAVAILABLE'


def test_stale_source_evidence_refused(tmp_path):
    import hashlib
    source=tmp_path/'source';source.write_text('old')
    data=tmp_path/'data.json';data.write_text(json.dumps({'source_hashes':{str(source):hashlib.sha256(source.read_bytes()).hexdigest()}}))
    assert checked_json(data)
    source.write_text('new')
    with pytest.raises(ValueError,match='stale'):checked_json(data)


def test_failed_history_setting_cannot_qualify_optics():
    data={'mutations':[{'detected':True}], 'histories':[{'kappa':0,'zeta':0,'order':32,'tolerance':1e-6,'numerical_status':'FAIL'}],
          'rays':[{'kappa':0,'zeta':0,'order':32,'tolerance':1e-6,'numerical_status':'PASS'}]}
    assert r3_scopes(data,'distance')==[]
