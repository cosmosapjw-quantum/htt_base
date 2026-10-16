import importlib.util,sys,hashlib
from pathlib import Path
import numpy as np
import pytest
SRC=Path(__file__).resolve().parents[1]/'src/cf4_raw_audit.py'
spec=importlib.util.spec_from_file_location('cf4_raw_audit',SRC)
mod=importlib.util.module_from_spec(spec);sys.modules[spec.name]=mod;spec.loader.exec_module(mod)

def row(spec, **fields):
    width=157 if spec is mod.TABLE4 else 190
    b=bytearray(b' '*width)
    for k,v in fields.items():
        l,r,t=spec[k];w=r-l
        s=str(v).rjust(w)
        assert len(s)<=w,(k,v)
        b[l:r]=s.encode('ascii')
    return bytes(b)+b'\n'

def fixtures(tmp_path):
    a=[row(mod.TABLE2,PGC=20,**{'1PGC':100},SNIa='32.2',e_SNIa='0.10',TF='32.4',e_TF='0.42',RAdeg='130.0',DEdeg='30.0'),
       row(mod.TABLE2,PGC=21,**{'1PGC':100},TRGB='30.1',e_TRGB='0.05',RAdeg='131.0',DEdeg='30.0'),
       row(mod.TABLE2,PGC=22,**{'1PGC':101},FP='33.2',e_FP='0.5',RAdeg='200.0',DEdeg='-11.0')]
    b=[row(mod.TABLE3,**{'1PGC':100},DMzp='30.100',DMav='30.247',e_DMav='0.18',RAdeg='130.0',DEdeg='30.0',o_CAL=1,DMcal='30.10',o_SNIa=1,DMsnIa='32.200',o_TF=1,DMtf='32.4'),
       row(mod.TABLE3,**{'1PGC':101},DMzp='33.853',DMav='34.000',e_DMav='0.50',RAdeg='200.0',DEdeg='-11.0',o_FP=1,DMfp='34.00')]
    c=[row(mod.TABLE4,**{'1PGC':101},DMzp='33.853',e_DMzp='0.5',Vh=4500,V3k=5000,RAdeg='200.0',DEdeg='-11.0'),
       row(mod.TABLE4,**{'1PGC':100},DMzp='30.100',e_DMzp='0.2',Vh=1500,V3k=1900,RAdeg='130.0',DEdeg='30.0')]
    arr={};digest={};
    for name,s,sp in zip(['table2','table3','table4'],[a,b,c],[mod.TABLE2,mod.TABLE3,mod.TABLE4]):
        path=tmp_path/f'{name}.dat';path.write_bytes(b''.join(s))
        digest[name]=hashlib.sha256(path.read_bytes()).hexdigest()
        arr[name]=mod.read_table(path,sp,name,expected=len(s),sha=digest[name])[0]
    return arr,digest

def test_fixed_width_offsets_and_method_domains(tmp_path):
    arr,_=fixtures(tmp_path)
    assert arr['table2'][0]['TF']==32.4
    assert arr['table2'][0]['SNIa']==32.2
    assert arr['table2'][0]['TRGB'] is None
    assert arr['table3'][0]['o_CAL']==1
    assert arr['table4'][0]['V3k']==5000

def test_byte_lock_mismatch_failclosed(tmp_path):
    arr,d=fixtures(tmp_path)
    with pytest.raises(ValueError,match='SHA mismatch'):
        mod.read_table(tmp_path/'table2.dat',mod.TABLE2,'table2',sha='0'*64)
    with pytest.raises(ValueError,match='row count'):
        mod.read_table(tmp_path/'table2.dat',mod.TABLE2,'table2',expected=4)

def test_method_overlap_and_direct_cal_join(tmp_path):
    a,d=fixtures(tmp_path)
    result=mod.analyse(a['table2'],a['table3'],a['table4'],sha=d)
    assert result['n_group_rows']==2
    assert result['n_individual_rows']==3
    assert result['individual_method_overlap_counts']['SNIa|TF']==1
    assert result['individual_method_counts']['TRGB']==1
    assert result['direct_cal_group_count']==1
    assert result['direct_without_galaxy_cal_link_count']==0
    assert result['group_DMzp_vs_DMav_0p001_histogram']=={'-0.147':2}
    assert result['scientific_admission']['H02']=='HOLD'

def test_group_order_fully_matched_by_id(tmp_path):
    a,_=fixtures(tmp_path)
    assert mod.analyse(*[a[k] for k in ('table2','table3','table4')])['table3_table4_DMzp_discrepancies']==[]

def test_nonmatching_group_sets_refused(tmp_path):
    a,_=fixtures(tmp_path)
    a['table4'][0]['1PGC']=999
    with pytest.raises(ValueError,match='sets mismatch'):
        mod.analyse(a['table2'],a['table3'],a['table4'])

def test_group_dmzp_mismatch_not_silent(tmp_path):
    a,_=fixtures(tmp_path)
    a['table4'][0]['DMzp']+=0.12
    result=mod.analyse(a['table2'],a['table3'],a['table4'])
    assert result['table3_table4_DMzp_discrepancies']==[101]

def test_method_present_requires_positive_error_and_value():
    assert mod.method_present(33.,0.2)
    assert not mod.method_present(None,0.2)
    assert not mod.method_present(33.,None)
    assert not mod.method_present(33.,0)
    assert not mod.method_present(0,0.1)

def test_original_sky_direction_sign():
    assert np.allclose(mod.sky_stf(0.,0.)[:3],[1.,0.,0.],atol=1e-14)
    assert np.allclose(mod.sky_stf(90.,0.)[:3],[0.,1.,0.],atol=1e-14)

def test_invalid_nan_and_bad_group_refused():
    raw=row(mod.TABLE3,**{'1PGC':0},DMav='32.4',e_DMav='0.2')
    with pytest.raises(ValueError,match='invalid group ID'):
        mod.decode_line(raw,mod.TABLE3,1,'table3')
    raw=row(mod.TABLE2,PGC=1,**{'1PGC':23},DM='nan')
    with pytest.raises(ValueError,match='nonfinite'):
        mod.decode_line(raw,mod.TABLE2,1,'table2')

def test_subset_crosswalk_digest_rejects_fabricated_npz(tmp_path):
    a,_=fixtures(tmp_path)
    f=tmp_path/'fake.npz';f.write_bytes(b'not the original selected CF4')
    with pytest.raises(ValueError,match='selected NPZ source digest mismatch'):
        mod.compare_selected_source(a['table4'],f)
