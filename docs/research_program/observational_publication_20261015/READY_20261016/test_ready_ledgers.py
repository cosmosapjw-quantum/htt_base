import json, numpy as np, pytest
from pathlib import Path
from build_ready_ledgers import source_identity,selection_ledger,bianchi_registry,sha256

def test_source_pins():
 s=source_identity();assert s['immutable_inputs']['CF4_selected_source']['sha256']=='86dfd896d5cf8f223396694dfb945137d1d28ea2227bc984665fb43f77fa376c'

def test_cross_release_shapes_and_independence():
 s=source_identity();assert len(s['immutable_inputs']['Planck_same_sky_coefficients']['names_T'])==9
 assert len(s['immutable_inputs']['Planck_same_sky_coefficients']['names_EB'])==8
 assert s['immutable_inputs']['Planck_same_sky_coefficients']['independence_unit'].startswith('ONE latent')

def test_cf4_method_counts():
 s=source_identity();counts=s['immutable_inputs']['CF4_selected_source']['method_family_counts'];assert counts=={'FP':26916,'OTHER':740,'SN':700,'TF':7614}

def test_six_papers_mapped():
 s=source_identity();assert set(s['paper_bindings'])=={'P1','P2','P3','P4','P5','P6'}
 assert s['paper_bindings']['P5']['11_type_all_m_atlas']=='NOT_VERIFIED'

def test_archive_metadata_does_not_become_sha256():
 s=source_identity();a=s['immutable_inputs']['AniCLASS_archive_discovered'];assert a['content_hash_is_NOT_SHA256'] and not a['bytes_read_in_current_runtime']

def test_selection_cannot_retrovalidate_pvalue():
 s=selection_ledger();assert s['historical_findings']['p_0039']['permitted_confirmatory'] is False
 assert s['prospective_new_null']['current_state']=='NOT_REGISTERED_FOR_NEW_OBSERVATIONAL_NULL'

def test_selection_includes_sky_radial_method_tails():
 s=selection_ledger();h=s['historical_findings'];assert h['Planck_lowell']['ell_range']==[2,5] and len(h['CF4_tomography']['centers_z'])==4
 assert s['prospective_new_null']['tail_rule'].startswith('>')

def test_bianchi_classification_unique():
 a=bianchi_registry();t=a['canonical_types'];assert len(t)==11 and len(set(x['type'] for x in t))==11
 assert sum(x['class']=='A' for x in t)==6 and sum(x['class']=='B' for x in t)==5

def test_exceptional_VI_no_twelfth():
 a=bianchi_registry();assert not a['exceptional_VI_minus_1_over_9']['distinct_twelfth_type']
 assert a['exceptional_VI_minus_1_over_9']['base_type']=='VI_h'

def test_aniclass_subset_only():
 a=bianchi_registry();near={x['type'] for x in a['canonical_types'] if x['aniCLASS_nearlyFLRW_documented']};assert near=={'I','V','VII_0','VII_h','IX'}
 assert all(x['T_E_B_high_l_all_m_qualified'] is False for x in a['canonical_types'])



def test_jacobi_sign_patterns_and_VI_class():
 a=bianchi_registry();z={x['type']:x for x in a['canonical_types']}
 for t,x in z.items():
  assert sum(n*b for n,b in zip(x['Lie_sign_representative_n_diag'],x['Lie_axis_representative_a']))==0
 assert z['III']['h_branch']=='h=-1' and z['VI_0']['class']=='A'
 assert z['VI_h']['h_branch'].startswith('h<0')
