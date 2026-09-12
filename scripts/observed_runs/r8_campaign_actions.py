"""Remaining R8 actions: live subset joins and source-bound terminal outcomes.

A capability names its scope. Computational scenarios never admit an observed
sampling law, and a blocked formal proof is not replaced by a software test.
"""
from fractions import Fraction as F
import hashlib
import json
from pathlib import Path
import subprocess
import numpy as np

ROOT=Path(__file__).resolve().parents[2]
ART=ROOT/'docs/generated/tensor_joint_r8'
D=ART/'jet_images/execution_20260912/results.json'
B=ART/'representations/execution_after_symmetry/mock2.json'
BO=ART/'representations/execution_after_symmetry/observed_components.json'
CMB=ART/'owned_controls/cmb/cmb.json'
FLOW=ART/'owned_controls/execution/fields.json'
R3=ART/'restricted_history/results.json'
A=ART/'orbit_continuation/summary.json'
PRODUCTS=ART/'law_followup/products.json'


def checked_json(path):
    """Validate the generating source identities of carried completed evidence."""
    path=Path(path);data=json.loads(path.read_text())
    for name,sha in data.get('source_hashes',data.get('source_sha256',{})).items():
        source=ROOT/name
        if not source.is_file() or hashlib.sha256(source.read_bytes()).hexdigest()!=sha:
            raise ValueError('stale generating source: '+name)
    return data


def r3_scopes(data,channel):
    if not all(m['detected'] for m in data['mutations']):return []
    histories={(r['kappa'],r['zeta'],r['order'],r['tolerance']) for r in data['histories'] if r['numerical_status']=='PASS'}
    if channel=='history':return [list(k) for k in sorted(histories)]
    if channel=='distance':
        return [dict(kappa=r['kappa'],zeta=r['zeta'],order=r['order'],tolerance=r['tolerance'],
                     direction=r['direction'],observer=r['observer']) for r in data['rays']
                if r['numerical_status']=='PASS' and (r['kappa'],r['zeta'],r['order'],r['tolerance']) in histories]
    if channel=='sky':
        return [r for r in data['sky'] if r['parity_error']<1e-12 and (r['kappa'],r['zeta'],128,1e-10) in histories]
    return []


def remaining_handlers(runner,evidence_dir):
    Handler=runner.Handler;write=runner.write
    def receipt(attempt,name,data,caps=(),outcome='SCENARIO_ONLY',sources=(),scope=None):
        p=attempt/(name+'.json');write(p,data)
        return {'scientific_outcome':outcome,'capabilities':list(caps),'evidence':[p,*sources],
                'capability_scopes':{cap:scope or [data.get('scope',outcome)] for cap in caps},'results':data}
    def carry(action,path,cap,outcome,keys=None):
        def execute(attempt,preds):
            data=checked_json(path)
            if keys is not None:data={k:data[k] for k in keys}
            return receipt(attempt,action,data,[cap],outcome,[path])
        return Handler(execute,(path,),action+'_V1')
    def proof(attempt,preds):
        p=ROOT/'.agent-harness/runs/R8-B-20260910/artifacts'
        paths=list(p.glob('**/*adjudication*.json'))
        return receipt(attempt,'representation_proof',{
            'status':'INDEPENDENT_ACCEPTANCE_UNFULFILLED','scope':'O4 direct finite representation checks',
            'reason':'Completed host-assisted O4 checks do not satisfy independently executed four-axis admission.',
            'direct_evidence_paths':[str(x) for x in paths],
            'computational_comparison':{'mock':checked_json(B)['pool_ablation_status'],'observed':checked_json(BO)['pool_ablation_status']}},
            outcome='PROOF_PARTIALLY_UNRESOLVED',sources=[B,BO,*paths])
    def bounds(attempt,preds):
        d=checked_json(A);cells=d['cells']
        if len(cells)!=30 or any(c['mean_width']>c['old_mean_width'] for c in cells):raise ValueError('invalid continuation bank')
        return receipt(attempt,'bounds',{'scope':'computed fixed mock1 banks','pools':len(cells),'all_monotone':True},['PAIR_BOUNDS'],'NUMERICAL_ENCLOSURES',[A])
    def rank(attempt,preds):
        from htt.infer.r8_interval_rank import rank_from_score_bounds
        a=rank_from_score_bounds([(0,3)]*4+[(7,10)],4,F(1,20))
        b=rank_from_score_bounds([(0,1)]+[(0,0)]*30,0,F(1,20))
        if a.p_lower!=F(1,5) or b.p_upper!=1:raise ValueError('rank controls failed')
        return receipt(attempt,'rank_controls',{'scope':'V03 software invariants','broad_rank':a,'inclusive_tie':b},['INTERVAL_RANK'],'METHOD_ONLY')
    def no_cmb_law(attempt,preds):
        d=checked_json(CMB)
        return receipt(attempt,'cmb_law',{ 'scope':d['scope'],'processing':d['processing'],
            'reason':'Four reconstructions of the same sky are correlated controls. No fixed signal/noise pool with matched masks/calibration response or candidate experiment is supplied.',
            'covariance':d['covariance'],'observed_rank':d['observed_rank']},outcome='INPUT_UNAVAILABLE',sources=[CMB])
    def unavailable_product(kind):
        def execute(attempt,preds):
            records,_=runner._read_owned_laws(attempt)
            return receipt(attempt,kind,{'scope':kind,'products':records,
                'reason':'The inspected releases do not supply this selected sampling law; no law can be synthesized from covariance, quoted errors, or posterior samples alone.'},outcome='INPUT_UNAVAILABLE',sources=[PRODUCTS])
        return Handler(execute,(PRODUCTS,),kind+'_V1')
    def outer(attempt,preds):
        from htt.infer.r8_law_registry import bind_method,run_scope
        from common.r7_contracts import json_value
        records,live=runner._read_owned_laws(attempt);subsets={}
        for product,(law,queries,procedure) in live.items():
            try:
                method=bind_method(law,F(1,80))
                subsets[product]={'alpha':'1/80','candidates':{name:json_value(run_scope(law,method,x)) for name,x in queries.items()},
                                   'confidence':runner._compressed_confidence(law,alpha=F(1,80)) if product=='desi_compressed' else None}
            except Exception as exc:subsets[product]={'outcome':'VALIDATION_FAILED','reason':str(exc)}
        return receipt(attempt,'outer_family',{'scope':'fixed four-block allocation; missing blocks are whole domain',
            'allocation':{'CMB':'1/80','CF4':'1/80','distance_calibration':'1/80','DESI':'1/80'},
            'subsets':subsets,'missing_blocks':['CMB','CF4','distance_calibration'],
            'physical_region':'WHOLE_DECLARED_DOMAIN: no admitted observation-to-jet response',
            'alternative_laws':'UNION; compatible constraints INTERSECTION; no cross-product independence used'},
            ['OUTER_FAMILY'],'CONDITIONAL_BOUND' if subsets else 'INPUT_UNAVAILABLE')
    def physical(attempt,preds):
        data=checked_json(D)
        return receipt(attempt,'physical_images',{'scope':'conditional closure sensitivity; not empirical physical confidence',
            'query_count':data['query_count'],'finite_query_count':data['finite_query_count'],
            'frontiers':data['frontiers'],'physical_scope':data['physical_scope'],
            'empirical_region':'WHOLE_DECLARED_DOMAIN; no CMB sampling/derivative law',
            'independent_four_axis_status':data['independent_four_axis_status']},['PHYSICAL_IMAGE'],'CONDITIONAL_BOUND',[D])
    def r3_action(channel,cap):
        def execute(attempt,preds):
            d=checked_json(R3);scopes=r3_scopes(d,channel)
            return receipt(attempt,channel,{'scope':'RESTRICTED_R3_NUMERICAL_BENCHMARK','channel':channel,
                'event':'observer a=2, positive-stream source a=1','frame':'normal LRS triad plus declared independent observer boost',
                'units':d['units'],'supported_settings':scopes,'failed_history_settings':len(d['histories'])-len(r3_scopes(d,'history')),
                'scientific_admission':d['scientific_admission'],'jet_status':d['jet_status'],
                'assumptions':d['limitations']},[cap] if scopes else [],'SCENARIO_ONLY' if scopes else 'VALIDATION_FAILED',[R3],scope=['FIXED_R3_BENCHMARK'])
        return Handler(execute,(R3,),channel+'_V1')
    def jet_status(attempt,preds):
        return receipt(attempt,'r3_jet_unavailable',{'scope':'radiation derivative/remainder channel','status':'INPUT_UNAVAILABLE',
            'reason':'No validated dotQ, STFgrad_d, divO, dotC, E or joint derivative/remainder domain is exported by the optical calculation.'},['R3_JET_STATUS'],'INPUT_UNAVAILABLE')
    def factory(channel,cap):
        def execute(attempt,preds):
            d=checked_json(R3);scopes=r3_scopes(d,channel)
            products=checked_json(PRODUCTS)['products']
            return receipt(attempt,channel+'_factory',{'scope':'R3 observed factory binding attempt','numerically_supported_settings':len(scopes),
                'products':{k:v['outcome'] for k,v in products.items()},
                'status':'INPUT_UNAVAILABLE','reason':('No beam/mask/bandpass/noise stochastic law for this thermal sky.' if channel=='sky' else
                'CF4 lacks selected error/selection law; JWST shared-host geometry cancels; Union3 is a nonangular compressed approximate scenario; DESI scalar qiso has no validated anisotropic R3 compression response.')},outcome='INPUT_UNAVAILABLE',sources=[R3,PRODUCTS])
        return Handler(execute,(R3,PRODUCTS),channel+'_FACTORY_V1')
    def external(attempt,preds):
        from bass.transfer.r7_external_provider import ExternalTransferProvider
        from scripts.observed_runs.run_tensor_joint_r7 import INVENTORY
        provider=ExternalTransferProvider()
        return receipt(attempt,'external_binding',{'scope':'external-transfer path','capabilities':provider.capabilities(),
            'selected_inventory':str(INVENTORY),'status':'INPUT_UNAVAILABLE',
            'reason':'No source-bound supported external backend, parameter domain and independent reference cases are registered for the R8 product factories. Archive/code presence does not provide a transfer prediction.'},outcome='INPUT_UNAVAILABLE',sources=[ROOT/'htt/bass/transfer/r7_external_provider.py'])
    def comparison(attempt,preds):
        records,live=runner._read_owned_laws(attempt)
        observed=runner.execute_admitted_products(live,include_confidence=True)
        d=checked_json(D);u=checked_json(PRODUCTS)['products']['union3']
        return receipt(attempt,'p0_p1_comparison',{'scope':'model-specific conditional comparison; no Bayes odds',
            'P0':{'desi_released_reference':observed,'union3_flat_lcdm':u},
            'P1':{'conditional_frontiers':d['frontiers'],'physical_scope':d['physical_scope'],
                  'CMB_informed_physical_bound':'INPUT_UNAVAILABLE'},
            'P2':'Restricted physical predictions are available; observed factory missing.',
            'P3':'External supported factory missing.'},['P0_P1_RESULTS'],'CONDITIONAL_BOUND',[D,PRODUCTS])
    def hook(attempt,preds):
        head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
        root=subprocess.check_output(['git','rev-parse','--show-toplevel'],cwd=ROOT,text=True).strip()
        expected='/mnt/sn850x2t/htt_base_e2e/TENSOR-JOINT-R8-20260909/worktree'
        if root!=expected:raise ValueError('wrong execution checkout')
        return receipt(attempt,'local_context',{'scope':'operational checkout only','root':root,'head':head,
            'native_dispatch':'NONE: standing owner requested direct execution','prior_hook_repair':'carried unchanged'},['OPERATIONAL_CONTEXT_RESULT'],'OPERATIONAL_ONLY',[ART/'hook/README.md'])
    def synthesis(attempt,preds):
        # Terminal action receipts, including unavailable siblings, are the inputs.
        rows=[{'node':node,'action':a['action'],'outcome':a['scientific_outcome'],'capabilities':a['capabilities'],
               'reason':a.get('reason'),'artifacts':a['artifacts']} for node,p in preds.items() for a in p['actions']]
        return receipt(attempt,'scientific_synthesis',{'scope':'R8 full terminal execution; scientific admission separate',
            'actions':rows,'branches':{
                'orbit':checked_json(A),'representations':{k:checked_json(B)[k] for k in ('M','converted_rows','incomplete_rows','pool_ablation_status')},
                'conditional_jet':{k:checked_json(D)[k] for k in ('query_count','finite_query_count','physical_scope','independent_four_axis_status')},
                'restricted_R3':{'history_pass':len(r3_scopes(checked_json(R3),'history')),'distance_pass':len(r3_scopes(checked_json(R3),'distance'))},
                'products':checked_json(PRODUCTS)},
            'claim_ceiling':'No native family identification, independent CAS acceptance, empirical physical confidence or posterior odds.'},['SYNTHESIS'],'SCOPED_SYNTHESIS',[A,B,D,R3,PRODUCTS])
    result={
        'representation_obligations':Handler(proof,(B,BO)),
        'certified_bounds':Handler(bounds,(A,)), 'interval_rank':Handler(rank),
        'full_mv':carry('full_mv',B,'MV_ABLATION','DESCRIPTIVE_CONTROL'),
        'orbit_rank_mocks':carry('orbit_rank_mocks',A,'ORBIT_METHOD_QUALIFIED','NUMERICAL_UNRESOLVED'),
        'mv_comparison':carry('mv_comparison',BO,'MV_COMPARISON_QUALIFIED','DESCRIPTIVE_CONTROL'),
        'extract_valid_tensors':carry('extract_valid_tensors',CMB,'CMB_TENSORS','DESCRIPTIVE_CONTROL'),
        'qualify_pool_law':Handler(no_cmb_law,(CMB,)), 'qualify_candidate_cmb_law':Handler(no_cmb_law,(CMB,)),
        'descriptive_morphology':carry('descriptive_morphology',BO,'CMB_DESCRIPTIVE','DESCRIPTIVE_CONTROL'),
        'observed_rank':Handler(no_cmb_law,(CMB,)), 'candidate_state_acceptance':Handler(no_cmb_law,(CMB,)),
        'outer_family':Handler(outer,(PRODUCTS,)),
        'jet_set':carry('jet_set',D,'JET_IMAGE','CONDITIONAL_METHOD'),
        'recession_certificates':carry('recession_certificates',D,'NONID_METHOD','LOCAL_CERTIFICATE_ONLY',('recession','caveats')),
        'closure_mocks':carry('closure_mocks',D,'CLOSURE_METHOD','CONDITIONAL_METHOD'),
        'recession_mocks':carry('recession_mocks',D,'NONID_QUALIFIED','LOCAL_CERTIFICATE_ONLY',('recession','caveats')),
        'conditional_physical_image':Handler(physical,(D,)),
        'nonidentification_result':carry('nonidentification_result',D,'NONID_RESULTS','LOCAL_CERTIFICATE_ONLY',('recession','physical_scope')),
        'field_and_map_controls':carry('field_and_map_controls',FLOW,'CONTROL_RESULTS','DESCRIPTIVE_CONTROL'),
        'restricted_stress':r3_action('history','R3_HISTORY'),
        'photon_channel':r3_action('sky','R3_SKY_CHANNEL'), 'distance_channel':r3_action('distance','R3_DISTANCE_CHANNEL'),
        'record_radiation_jet_unavailable':Handler(jet_status),
        'restricted_sky_factory':factory('sky','R3_SKY_FACTORY'), 'restricted_distance_factory':factory('distance','R3_DISTANCE_FACTORY'),
        'external_channel_factory':Handler(external), 'p0_p1_comparison':Handler(comparison,(D,PRODUCTS)),
        'p2_sky_comparison':factory('sky','P2_SKY_RESULTS'), 'p2_distance_comparison':factory('distance','P2_DISTANCE_RESULTS'),
        'p3_supported_comparison':Handler(external), 'check_local_hook_context':Handler(hook),
        'receipt_synthesis':Handler(synthesis,(A,B,D,R3,PRODUCTS)),
    }
    for name in ('singular_dispatch','partial_dispatch','singular_observation','partial_observation','real_candidate_simulator','simulator_observation'):
        result[name]=unavailable_product(name)
    return result
