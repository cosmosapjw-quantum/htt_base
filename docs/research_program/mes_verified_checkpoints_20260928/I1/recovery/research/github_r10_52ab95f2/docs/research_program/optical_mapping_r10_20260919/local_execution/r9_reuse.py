#!/usr/bin/env python3
"""Read source-pinned existing R9 work without rerunning its experiments."""
from pathlib import Path
import json,hashlib,subprocess
import numpy as np
from scipy.linalg import expm
OUT=Path(__file__).resolve().parent
DONOR=Path('/mnt/sn850x2t/htt_base_e2e/PROJECT-CATALOG-20260912/worktree')
PIN='870bd67af159993ccde4ede9923424a475c01375'

def main():
    actual=subprocess.check_output(['git','-C',str(DONOR),'rev-parse','HEAD'],text=True).strip();assert actual==PIN
    paths=['docs/research_program/tensor_joint_r9/revision2/selected_law/final/result.json','docs/research_program/tensor_joint_r9/revision2/multidepth/observed_initial/result.json','docs/research_program/tensor_joint_r9/revision2/depth_formal/law_support/attempt01/execution.json','docs/research_program/tensor_joint_r9/evidence/cmb_research_checks.json']
    evidence=[];data=[]
    for rel in paths:
        raw=(DONOR/rel).read_bytes(); pinned=subprocess.check_output(['git','-C',str(DONOR),'show',PIN+':'+rel]);assert raw==pinned
        d=json.loads(raw);data.append(d)
        evidence.append({'path':rel,'commit':PIN,'sha256':hashlib.sha256(raw).hexdigest(),'immutable_url':f'https://github.com/cosmosapjw-quantum/htt_base/blob/{PIN}/{rel}','status':d.get('status',d.get('scope','SCOPED_LEAN_COMPILE'))})
    # New small deterministic response discriminator independent of optical/T9
    # readiness; shares a source+calibration tuple rather than plug-in Q.
    B=np.arange(35,dtype=float).reshape(7,5)/100
    G=np.block([[np.zeros((5,5)),-B.T],[B,np.zeros((7,7))]])
    C=np.eye(12);R=expm(.01*G)
    cancelled=np.linalg.norm(R@C@R.T-C)
    assert cancelled<1e-12
    # Shared eta identical to one signal column destroys that target even when
    # both observation blocks exist; intersection must precede projection.
    shared=np.array([[1.,1.],[1.,1.]])
    nuisance=shared[:,[1]]
    target_rank=int(np.linalg.matrix_rank(shared)-np.linalg.matrix_rank(nuisance));assert target_rank==0
    selected=data[0]; observed=data[1]
    result={'scope':'SOURCE_PINNED_REUSE_PLUS_NEW_FINITE_SHARED_LAW_DISCRIMINATOR','donor_head':actual,'evidence':evidence,'reuse':{'public_overlap_rows':selected['counts']['rule_based_public294'],'selected_observation_law':selected['selected_observation_law'],'physical_response':selected['physical_local_global_response'],'joint_covariance':selected['joint_covariance_status'],'depth_counts':observed['observed_counts'],'law_support_exit':data[2]['exit_code'],'D2_D4_and_independent_admission':'NOT_ESTABLISHED_BY_D3'},'new_checks':{'C2_equals_C3_full_QO_covariance_residual':float(cancelled),'shared_eta_target_quotient_rank':target_rank,'static_QO_to_jet':'WHOLE_DOMAIN_WITHOUT_PHYSICAL_PROVIDER'},'method_execution':{'observed_methods_qualified_and_executed_this_run':[],'alpha_spent':0,'optical_common_gate':False,'CF4':'new distance-modulus selected law not supplied by reused CF3/SDSS diagnostic; P0 remains quarantined','JWST':'shared anchor selected law not established by this evidence','DESI':'compressed-law eligibility not established by this evidence','Union3':'approximate scenario only','PR3_FFP10':'unique product/realization matching not executed here; no null count inferred','PR4_NPIPE':'EXCLUDED'},'alpha':{'family':.05,'CF4':.0125,'distance_calibration':.0125,'DESI':.0125,'CMB_rank':.00625,'CMB_candidate':.00625,'redistributed':False},'admitted_capabilities':[]}
    (OUT/'r9_reuse.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result['new_checks']))
if __name__=='__main__':main()
