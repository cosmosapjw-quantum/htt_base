#!/usr/bin/env python3
"""Seal only this bounded repair candidate. Do not edit R32 production or campaign state."""
import hashlib
import json
import pathlib

HERE = pathlib.Path(__file__).resolve().parent

def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

result = json.loads((HERE/'RESULT.json').read_text())
files=[]
for path in sorted(HERE.rglob('*')):
    if path.is_file() and path.name not in ('ARTIFACT_MANIFEST.json','RETURN.json') and '__pycache__' not in path.parts:
        files.append({'path':str(path.relative_to(HERE)),'sha256':sha(path),'bytes':path.stat().st_size})
manifest={'schema':'htt.r36.science_synthesis_repair_artifacts/1','task_id':result['task_id'],'packet_id':result['packet_id'],'input_identity':result['input_identity'],'prior_candidate_identity':result['prior_candidate_identity'],'source_contract_sha256':sha(HERE/'candidate/R32-06-P4-DESIGN/report/r36_11/SOURCE_CONTRACT.json'),'candidate_pdf_sha256':sha(HERE/'candidate/R32-06-P4-DESIGN/report/main.pdf'),'application_plan_sha256':sha(HERE/'APPLICATION_PLAN.json'),'artifacts':files,'acceptance_met':False,'qualification_status':'PROPOSED_ONLY','scientific_admission':'HOLD_PENDING_INDEPENDENT_REVIEW','raw_receipt':result['raw_receipt']}
(HERE/'ARTIFACT_MANIFEST.json').write_text(json.dumps(manifest,indent=2)+'\n')
print('sha256:'+sha(HERE/'ARTIFACT_MANIFEST.json'))
