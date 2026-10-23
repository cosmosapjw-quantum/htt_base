"""Tiny local candidate fixtures only; no production state/candidate access."""
import copy,hashlib,json
from pathlib import Path
from test_research_controller_frontier import ConcurrentReviewTests,rc,POLICY,PROFILES

def case(inventory,after_ack):
 t=ConcurrentReviewTests();t.setUp()
 try:
  state,_=t.fixture(second=False);row=state['tasks']['CANDIDATE'];directory=Path(row['spec']['owned_paths'][0])
  artifact=directory/'compute.py';artifact.write_text('frozen implementation\n');manifest=directory/'MANIFEST.json'
  h=hashlib.sha256(artifact.read_bytes()).hexdigest();manifest.write_text(json.dumps({'task_id':'CANDIDATE','input_identity':'input-v1',inventory:{'compute.py':{'sha256':h}}}))
  row['candidate_identity']='sha256:'+hashlib.sha256(manifest.read_bytes()).hexdigest();row['candidate_products']=[]
  packet=t.plan(state)
  if after_ack:rc.acknowledge(state,packet['packet_id'],'actual-fixture-independent-reviewer')
  artifact.write_text('changed implementation\n');before=copy.deepcopy(state)
  try:
   if after_ack:t.result(state,packet,acceptance_met=True)
   else:rc.acknowledge(state,packet['packet_id'],'actual-fixture-independent-reviewer')
   return {'inventory':inventory,'after_ack':after_ack,'accepted':True,'task_state':state['tasks']['CANDIDATE']['state']}
  except rc.ControllerError as e:
   return {'inventory':inventory,'after_ack':after_ack,'accepted':False,'state_unchanged':state==before,'error':str(e)}
 finally:t.doCleanups()
print(json.dumps([case('files',False),case('products_sha256',True)],indent=2))
