import json
from pathlib import Path
from scripts.observed_runs.run_tensor_joint_r8 import Handler,execute_campaign,execute_admitted_products,write

def test_missing_present_resume_and_surviving_unrelated_scope(tmp_path):
    evidence=tmp_path/'evidence';calls=[]
    def load(attempt,preds):
        calls.append('A')
        if not evidence.is_file():return {'capabilities':[],'scientific_outcome':'INPUT_UNAVAILABLE'}
        return {'capabilities':['A'],'scientific_outcome':'METHOD_ONLY','evidence':[evidence]}
    def independent(attempt,preds):
        calls.append('B');return {'capabilities':[],'scientific_outcome':'CONTROL_ONLY'}
    def dependent(attempt,preds):
        calls.append('C');return {'capabilities':[],'scientific_outcome':'CONDITIONAL_BOUND'}
    def node(n,after,act,requires=(),produces=()):return {'id':n,'after':after,'actions':[{'action':act,'requires':list(requires),'produces':list(produces)}]}
    dag={'nodes':[node('A',[],'load',produces=['A']),node('B',[],'independent'),node('C',['A'],'dependent',[{'node':'A','capability':'A'}]),node('D',[],'not_implemented')]}
    handlers={'load':Handler(load,(evidence,)),'independent':Handler(independent),'dependent':Handler(dependent)}
    a=execute_campaign(dag,tmp_path/'run',handlers);assert a['new_attempts']==4
    b=execute_campaign(dag,tmp_path/'run',handlers,resume=True);assert b['new_attempts']==0
    evidence.write_text('current evidence')
    c=execute_campaign(dag,tmp_path/'run',handlers,resume=True);assert c['new_attempts']==2
    assert calls==['A','B','A','C']
    assert c['nodes']['D']['actions'][0]['reason']=='NOT_IMPLEMENTED_IN_INITIAL_AC_INCREMENT'
    assert not c['full_plan_accepted']
    assert len(list((tmp_path/'run/A/load').glob('attempt_*')))==2

def test_action_exception_cannot_publish_declared_outputs(tmp_path):
    def boom(attempt,preds):raise RuntimeError('failure')
    dag={'nodes':[{'id':'A','after':[],'actions':[{'action':'boom','requires':[],'produces':['CERTIFIED']}]}]}
    out=execute_campaign(dag,tmp_path,{'boom':Handler(boom)})
    assert not out['nodes']['A']['capabilities']
    assert out['nodes']['A']['actions'][0]['process_status']=='COMPLETED_FAILED_WITH_RECEIPT'

def test_generic_dispatch_supports_additional_live_law_and_failure_independence():
    from htt.infer.r8_law_registry import PartialObservationLaw,admit_product
    law=PartialObservationLaw([0.,0.],('a','b'),('fixture',),[1.,1.],lambda x:x,
         lambda x:x.shape==(2,),'R2','FIXED','GALACTIC',('K','K'),'KNOWN_GAUSSIAN_MARGINALS','KNOWN_FIXTURE',('u','v'))
    p=dict(product_id='not-qiso',observed=law.observed,measurement_ids=law.measurement_ids,source_ids=law.source_ids)
    live=admit_product(p,dict(law=law,frame=law.frame,conditioning_id=law.conditioning_id))
    out=execute_admitted_products({'valid':(live,{'null':[0.,0.],'large':[100.,100.]},None),
                                  'broken':(object(),{'null':[0.]},None)})
    assert out['valid']['candidates']['null']['membership']=='ACCEPT'
    assert out['valid']['candidates']['large']['membership']=='REJECT'
    assert out['broken']['outcome']=='VALIDATION_FAILED'

def test_malformed_product_is_isolated_and_zero_success_cannot_promote(monkeypatch,tmp_path):
    import scripts.observed_runs.run_tensor_joint_r8 as runner
    broken={'malformed':None,'broken':(object(),{'null':[0.]},None)}
    outputs=execute_admitted_products(broken)
    assert set(outputs)==set(broken) and all(v['outcome']=='VALIDATION_FAILED' for v in outputs.values())
    monkeypatch.setattr(runner,'_read_owned_laws',lambda attempt:({},broken))
    write(tmp_path/'mocks/mock5.json',{'cells':[{'law':'mixture','diagnostic_pass':False}]})
    handlers=runner.production_handlers(tmp_path)
    for action in ('nonsingular_dispatch','gaussian_observation','toy_simulator_validation'):
        result=handlers[action].execute(tmp_path,{})
        assert result['capabilities']==[]
