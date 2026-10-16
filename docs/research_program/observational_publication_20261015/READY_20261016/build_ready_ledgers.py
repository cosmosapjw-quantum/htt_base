"""Source-identity and selection ledger for the authoritative HTT 6-paper overlay.

This small verifier consumes exact recovery checkpoint bytes rather than treating
Dropbox search matches or reports as observed physical response laws.
"""
from __future__ import annotations
import hashlib, json, zipfile
from pathlib import Path
import numpy as np

ROOT=Path(__file__).resolve().parent
INPUT=ROOT.parent/'inputs'
OUT=ROOT

def sha256(data:bytes)->str: return hashlib.sha256(data).hexdigest()
def canonical(obj): return json.dumps(obj,indent=2,sort_keys=True,ensure_ascii=False)+'\n'
def save(name,obj): (OUT/name).write_text(canonical(obj),encoding='utf-8')
def source_identity():
    cf4=INPUT/'htt_six_paper_h03/inputs/selected_source_observables.npz'
    t=INPUT/'source/retained_common_support_coefficients.npz'
    p=INPUT/'source/processing_coefficients.npz'
    report=INPUT/'source_sourcejson/result.json'
    for v in [cf4,t,p,report]:
        if not v.is_file():raise FileNotFoundError(str(v))
    csum=sha256(cf4.read_bytes());
    if csum!='86dfd896d5cf8f223396694dfb945137d1d28ea2227bc984665fb43f77fa376c':
        raise ValueError('FAIL_CLOSED: CF4 source SHA mismatch')
    with np.load(cf4,allow_pickle=False) as d:
        grp=d['group_id'];z=d['z_CMB'];n=d['n_J2000'];m=d['method_family'];e=d['e_dmzp']
        if len(np.unique(grp))!=len(grp) or len(grp)!=35970 or n.shape!=(35970,3):raise ValueError('CF4 group-identity or shape mismatch')
        if np.max(abs(np.linalg.norm(n,axis=1)-1.0))>1e-10:raise ValueError('CF4 nonunit sky vectors')
        if np.any(e<=0) or not np.all(np.isfinite(z)):raise ValueError('CF4 bad uncertainty/redshift')
        methods={str(k):int(v) for k,v in zip(*np.unique(m,return_counts=True),strict=True)}
    with np.load(t,allow_pickle=False) as d:
        namesT=d['names_T'];namesEB=d['names_EB'];cT=d['coeff_T'];cEB=d['coeff_EB']
        if cT.shape!=(9,32) or cEB.shape!=(8,64):raise ValueError('Planck shape mismatch')
        if set(map(str,namesEB)) - set(map(str,namesT)):raise ValueError('EB without T identity')
    with np.load(p,allow_pickle=False) as d:
        if d['observed'].shape!=(6,32) or d['paired'].shape!=(6,300,32):raise ValueError('Planck processing shape mismatch')
    data=json.loads(report.read_text())
    if data['scientific_status']!='EXECUTED_REAL_SINGLE_SKY_MULTI_PRODUCT_CONDITIONAL_ONLY':raise ValueError('Planck status mismatch')
    if (data['common_T_nside64_pixel_count'],data['common_POL_nside64_pixel_count'])!=(26846,30021):raise ValueError('Planck masks mismatch')
    return {
      'schema':'htt.six_paper_source_bindings/1','status':'SOURCE_SCOPED_ONLY',
      'authority':'cosmosapjw-quantum/htt_base PR543 eac75859f38bf223d5e5ee215ae0b65a1617ceaa; separate six-paper DAG',
      'source_units':{
         'CF4':'35,970 uniquely identified Cosmicflows-4 groups; z_CMB, dmzp, e_dmzp and n_J2000',
         'Planck':'one cosmological CMB sky, nine temperature processing variants and eight polarized E/B variants',
         'simulation':'noise/signal simulation realization identities separate from processing variants'},
      'immutable_inputs':{
        'CF4_selected_source':{'bytes':cf4.stat().st_size,'sha256':csum,'group_count':len(grp),'method_family_counts':methods,'z_min':float(z.min()),'z_max':float(z.max()),'recovered_from':'ChatGPT Library P3/H03 S2_SOURCE_CONDITIONAL_FINAL.zip; Dropbox same path present','release_parent':'Cosmicflows-4 source; selected source is local derived group NPZ, not entire raw release','independence_unit':'group_id, not method family row or depth window'},
        'Planck_same_sky_coefficients':{'bytes':t.stat().st_size,'sha256':sha256(t.read_bytes()),'names_T':list(map(str,namesT)),'names_EB':list(map(str,namesEB)),'selected_T_pixels':26846,'selected_P_pixels':30021,'common_mask':'distinct T/P mask supports','recovered_from':'ChatGPT Library P2/L01 FINITE_SOURCE.zip','independence_unit':'ONE latent CMB sky across all products'},
        'Planck_processing_paired':{'bytes':p.stat().st_size,'sha256':sha256(p.read_bytes()),'observed_shape':[6,32],'paired_shape':[6,300,32],'unverified_exchangeability':True,'independence_unit':'unverified; paired noise/processing axes are not automatically independent cosmological skies'},
        'AniCLASS_archive_discovered':{'path':'Dropbox /bianchi_phase_r_bootstrap_v1.2/bianchi_phase_r/aniclass-class_aniclass.zip','size_bytes':10616213,'dropbox_content_hash':'60948e2afe594c8b84c0d2b26b18b5d7d2a15cbb1f1bd2fe36f5d4cd258c8270','content_hash_is_NOT_SHA256':True,'bytes_read_in_current_runtime':False}}
      ,'paper_bindings':{
         'P1':{'observed_inputs':['CF4_selected_source','Planck_same_sky_coefficients'],'theory':'existing signed-Gauss/MES/PR066 code','physical_joint_signed_x_posterior':'NOT_MEASURED','MIO_certificate_consumption':False},
         'P2':{'observed_inputs':['Planck_same_sky_coefficients','Planck_processing_paired'],'T_and_P_same_sky':True,'physical_end_to_end_exchangeability':'NOT_DEMONSTRATED'},
         'P3':{'observed_inputs':['CF4_selected_source'],'windowed_estimator':'conditional WLS','true_selection_and_shared_calibration':'NOT_MEASURED'},
         'P4':{'observed_inputs':['Planck_same_sky_coefficients','CF4_selected_source'],'local_boost_response':'MATHEMATICAL_ONLY','global_history_transfer':'NOT_MEASURED'},
         'P5':{'observed_inputs':['Planck_same_sky_coefficients'],'external_transfer_archive':'FOUND_BYTES_NOT_REEXECUTED','11_type_all_m_atlas':'NOT_VERIFIED'},
         'P6':{'observed_inputs':['CF4_selected_source'],'radial_working_quad':'NOT_EQUAL_GEOMETRIC_SHEAR','physical_noncircular_optical_channels':'NOT_MEASURED'}},
      'overlap_graph':[
         {'pair':['P2','P4'],'source':'Planck','relationship':'identical latent CMB sky, not independent'},
         {'pair':['P2','P5'],'source':'Planck','relationship':'same sky and related masks'},
         {'pair':['P1','P2'],'source':'Planck','relationship':'shared processing products if reused'},
         {'pair':['P1','P3'],'source':'CF4','relationship':'shared groups if reused'},
         {'pair':['P3','P4'],'source':'CF4','relationship':'identical group catalogue if reused'},
         {'pair':['P3','P6'],'source':'CF4','relationship':'identical group catalogue if reused'},
         {'pair':['P1','P6'],'source':'CF4','relationship':'shared conditional source'},
      ],
      'not_automatically_independent':['nine T variants','eight E/B variants','four CF4 redshift windows','four CF4 method family subcatalogues','noise realizations reusing one signal map'],
      'unavailable_physical_inputs':['selection function','shared calibration covariance','global material/radiation tilt history','full polarized Bianchi all-type transfer','nonradial optical source'],
    }


def selection_ledger():
 return {
  'schema':'htt.six_paper_selection_ledger/1','as_of':'2026-10-16 KST','status':'LOCK_PREEXISTING_EXPLORATION_NOT_PREREGISTRATION',
  'historical_findings':{
     'p_0039':{'p':0.039,'status':'RETROSPECTIVE_EXPLORATORY','permitted_confirmatory':False},
     'Planck_lowell':{'T_methods':9,'EB_methods':8,'ell_range':[2,5],'additional_T_ell_leakage':[6,32],'native_masks':'NSIDE2048 NESTED -> NSIDE64 RING; different T/P supports','selection_status':'historically chosen/not prespecified before data'},
     'CF4_tomography':{'centers_z':[0.025,0.040,0.060,0.080],'gaussian_sigma_z':0.012,'H_ref_km_s_Mpc':70.,'peculiar_velocity_scale_km_s':250.,'method_families':['FP','TF','SN','OTHER'],'patch_loo':12,'method_loo':4,'selection_status':'historically chosen; do not retroactively promote'},
  },
  'prospective_new_null':{
    'current_state':'NOT_REGISTERED_FOR_NEW_OBSERVATIONAL_NULL',
    'required_before_new_null':['exact planck release/split and beam IDs','T/P sky mask IDs and order','ell selection, tensor projection, angular axes','multiplicity/trial family and tail convention','independent CMB realization ID and processing path','CF4 group selection and method weight/distance/redshift bins','source-matched likelihood and nuisance covariance','holdout split', 'unblinding timestamp'],
    'tail_rule':'> (not >=) where Pi is used','selection_dependency':'Each new test must name prior exploratory views and be registered before its own null-generation',
    'no_artificial_promotion':True},
  'claim_policy':{'physical_detection':False,'all_six_submission':'NOT_READY_TO_SUBMIT','p_historical_use':'context only','multitest_correction':'MUST_BIND_ACTUAL_FAMILY_NOT_GUESSED'}
 }


def bianchi_registry():
 types=['I','II','III','IV','V','VI_0','VI_h','VII_0','VII_h','VIII','IX']
 near={'I','V','VII_0','VII_h','IX'}
 class_a={'I','II','VI_0','VII_0','VIII','IX'}
 normalized_signs={
  'I':(0,0,0),'II':(0,0,+1),'III':(0,+1,-1),
  'IV':(0,0,+1),'V':(0,0,0),'VI_0':(0,+1,-1),
  'VI_h':(0,+1,-1),'VII_0':(0,+1,+1),'VII_h':(0,+1,+1),
  'VIII':(+1,+1,-1),'IX':(+1,+1,+1),
 }
 h_conditions={'III':'h=-1', 'VI_h':'h<0, excluding h=0; h=-1/9 exceptional within this class', 'VII_h':'h>0'}
 entries=[]
 for t in types:
  sign_pattern=normalized_signs[t]
  a_axis=(0,0,0) if t in class_a else (+1,0,0)
  assert sum(int(a and n) for a,n in zip(a_axis,sign_pattern))==0
  entries.append({'type':t,'class':'A' if t in class_a else 'B',
    'Lie_sign_representative_n_diag':list(sign_pattern),
    'Lie_axis_representative_a':list(a_axis),
    'Jacobi_a_dot_n_zero':True,
    'h_branch':h_conditions.get(t,'not_applicable'),
    'caveat':'Sign-pattern representative, not fixed metric curvature scalar or full initial data',
    'aniCLASS_nearlyFLRW_documented':t in near,
    'status':'DOCUMENTED_EXTERNAL_IMPLEMENTATION_NOT_REEXECUTED' if t in near else 'NO_VERIFIED_CURRENT_SOLVER',
    'required_IC':'admissible metric/shear/matter/tilt and primordial mode specification',
    'T_E_B_high_l_all_m_qualified':False,
    'curvature_and_Lie_constraints':'MUST_VERIFY_BRANCH_PARAMETERS_AND_CLASS_SIGN',
    'parity_orientations':'SO(3) and O(3) equivalences not presumed distinct cosmological families'})
 return {'schema':'htt.bianchi_atlas_inventory/1','canonical_count':11,'canonical_types':entries,
     'exceptional_VI_minus_1_over_9':{'base_type':'VI_h','h':'-1/9','distinct_twelfth_type':False,'extra_dynamical_branch_review_required':True},
     'AniCLASS_scope':{'nearFLRW_5':sorted(near),'origin':'https://github.com/CyrilPitrou/aniclass/wiki','small_shear':'required','pol':'E/B documented','all_m_full_Bianchi_nonlinear_atlas':'NOT_CLAIMED'},
     'raw_code_archives':{'existing_aniclass_zip_path':'Dropbox /bianchi_phase_r_bootstrap_v1.2/bianchi_phase_r/aniclass-class_aniclass.zip','exists_metadata':True,'downloaded_in_this_sandbox':False},
     'physics_sources':['https://arxiv.org/html/0706.2075v2','https://doi.org/10.1103/PhysRevLett.117.131302','https://doi.org/10.1103/PhysRevD.100.123535','https://doi.org/10.1103/PhysRevD.100.123534'],
     'B02_precondition':'Native physical all-m polarized transfer and IC/curvature sign regression from exact code revision plus Planck response are not yet verified',
     'inventoried_not_validated':True}


def main():
 sources=source_identity();save('X01_SOURCE_BINDINGS.json',sources)
 selection=selection_ledger();save('X03_CLAIM_SELECTION_LEDGER.json',selection)
 atlas=bianchi_registry();save('B01_BIANCHI_ATLAS_REGISTRY.json',atlas)
 print(canonical({'X01_methods':sources['immutable_inputs']['CF4_selected_source']['method_family_counts'],'Planck_T':len(sources['immutable_inputs']['Planck_same_sky_coefficients']['names_T']),'Planck_EB':len(sources['immutable_inputs']['Planck_same_sky_coefficients']['names_EB']),'B01_total':len(atlas['canonical_types']),'B01_nearFLRW':sum(t['aniCLASS_nearlyFLRW_documented'] for t in atlas['canonical_types']),'X03_history':'RETROSPECTIVE'}))
if __name__=='__main__':main()
