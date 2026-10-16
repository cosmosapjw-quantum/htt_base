"""CDS J/ApJ/944/94 byte-locked original source-family and calibration audit.

Measures released method support, aggregation and linear-algebraic rank only.
It does NOT infer a physical selection function, independent measurements,
cosmological shear/tilt, or a peculiar-velocity law.
"""
from __future__ import annotations
import argparse, hashlib, json, math
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping
import numpy as np

SCHEMA = "htt.CF4_raw_source_support/1"
SOURCE = "CDS J/ApJ/944/94 original fixed-width"
LOCKED = {
    "table2": (55877, 190, "8e908928e68352b59292cf67020a4d70aaa6d30f278dfa6aa3e41a9df808332f"),
    "table3": (38053, 190, "c2351c52de3e38a7fd80256b6f0818c550dd9f105b91e84fbcc1eb7234160b4d"),
    "table4": (38053, 157, "b6edfec68bdfddeada8f3b8f11938f3bbda98a8e2894ff136a369c2ad6594e94"),
}
# CDS ReadMe 1-based inclusive coordinates translated to Python zero-based half-open.
TABLE2 = {
    "PGC":(0,7,"int"), "1PGC":(8,15,"int"), "Vcmb":(22,27,"float"),
    "DM":(28,34,"float"), "e_DM":(35,40,"float"),
    "SNIa":(41,47,"float"), "e_SNIa":(48,52,"float"),
    "TF":(53,59,"float"), "e_TF":(60,64,"float"),
    "FP":(65,71,"float"), "e_FP":(72,76,"float"),
    "SBF":(77,83,"float"), "e_SBF":(84,89,"float"),
    "SNII":(90,96,"float"), "e_SNII":(97,101,"float"),
    "TRGB":(102,107,"float"), "e_TRGB":(108,112,"float"),
    "Cepheid":(113,119,"float"), "e_Cepheid":(120,125,"float"),
    "Maser":(126,131,"float"), "e_Maser":(132,136,"float"),
    "RAdeg":(137,145,"float"),"DEdeg":(146,154,"float"),
}
TABLE3 = {
    "1PGC":(0,7,"int"), "DMzp":(8,14,"float"),"DMav":(15,21,"float"),
    "e_DMav":(22,27,"float"), "Vcmb":(28,33,"float"),
    "RAdeg":(34,42,"float"), "DEdeg":(43,51,"float"),
    "o_CAL":(88,90,"int"), "DMcal":(91,97,"float"),
    "o_SNIa":(98,99,"int"),"DMsnIa":(100,106,"float"),
    "o_FP":(113,116,"int"),"DMfp":(117,123,"float"),
    "o_TF":(130,132,"int"),"DMtf":(133,139,"float"),
    "o_SBFO":(146,149,"int"),"DMsbfo":(150,156,"float"),
    "o_SBFI":(163,164,"int"),"DMsbfi":(165,171,"float"),
    "DMsnII":(178,184,"float"),
}
TABLE4 = {"1PGC":(0,7,"int"), "DMzp":(8,14,"float"),
          "e_DMzp":(15,20,"float"), "Dist":(21,26,"float"),
          "Vh":(27,32,"float"),"V3k":(39,44,"float"),
          "RAdeg":(83,91,"float"),"DEdeg":(92,100,"float")}
T2_METHODS=("SNIa","TF","FP","SBF","SNII","TRGB","Cepheid","Maser")
T3_METHODS=("CAL","SNIa","FP","TF","SBFO","SBFI","SNII")


def decode_line(line:bytes,spec:Mapping[str,tuple],n:int,name:str)->dict:
    row=line.rstrip(b"\r\n")
    if len(row)<30 or len(row)>(190 if name!="table4" else 157):
        raise ValueError(f"bad record length {name} row {n}: {len(row)}")
    if b"\x00" in row:
        raise ValueError("NUL in ASCII source")
    out={}
    for key,(start,stop,typ) in spec.items():
        txt=row[start:stop].strip()
        if not txt:out[key]=None;continue
        try:v=int(txt) if typ=="int" else float(txt)
        except (ValueError,OverflowError) as e:
            raise ValueError(f"invalid {name} row={n} field={key} value={txt!r}") from e
        if typ=="float" and not math.isfinite(v):raise ValueError("nonfinite released source")
        out[key]=v
    if out.get("1PGC") is None or out["1PGC"]<=0:
        raise ValueError("invalid group ID")
    return out


def read_table(path:Path,spec,name,*,expected=None,sha=None):
    h=hashlib.sha256(); rows=[]
    with path.open('rb') as file:
        for i,line in enumerate(file,1):
            h.update(line)
            rows.append(decode_line(line,spec,i,name))
    digest=h.hexdigest()
    if sha is not None and digest!=sha:raise ValueError(f"{name} SHA mismatch {digest} != {sha}")
    if expected is not None and len(rows)!=expected:raise ValueError(f"{name} row count {len(rows)} != {expected}")
    return rows,digest


def method_present(v,err):
    return v is not None and v>0 and err is not None and err>0


def sky_stf(ra,dec):
    r,d=np.deg2rad([ra,dec]); c=np.cos(d)
    nx,ny,nz=c*np.cos(r),c*np.sin(r),np.sin(d)
    return [nx,ny,nz,nx*nx-nz*nz,ny*ny-nz*nz,2*nx*ny,2*nx*nz,2*ny*nz]


def analyse(t2:list,t3:list,t4:list,*,sha:dict|None=None, provenance="FIXTURE"):
    by3={};by4={};galaxies_bygroup=defaultdict(list)
    t2_count=Counter(); overlap=Counter(); t3_presence=Counter()
    for row in t2:
        families=[]
        for meth in T2_METHODS:
            if method_present(row.get(meth),row.get('e_'+meth)):
                t2_count[meth]+=1;families.append(meth)
        for i,a in enumerate(families):
            for b in families[i+1:]:overlap['|'.join(sorted((a,b)))]+=1
        galaxies_bygroup[row['1PGC']].append((row['PGC'], tuple(families),row))
    for x in t3:
        if x['1PGC'] in by3:raise ValueError("duplicate Table3 group")
        by3[x['1PGC']]=x
    for x in t4:
        if x['1PGC'] in by4:raise ValueError("duplicate Table4 group")
        by4[x['1PGC']]=x
    if set(by3)!=set(by4):raise ValueError("Table3/4 1PGC sets mismatch")
    offsets=Counter();direct=[];selected=[];Z=[];X=[];direct_both=[];mismatch=[]
    for gid,row in by3.items():
        f=by4[gid]
        if abs(row['DMzp']-f['DMzp'])>0.00101:
            mismatch.append(gid)
        if method_present(row['DMav'],row['e_DMav']):
            offsets[f"{row['DMzp']-row['DMav']:.3f}"]+=1
        local_cal=[]
        for pgc,meth,r in galaxies_bygroup.get(gid,[]):
            for ch in ('TRGB','Cepheid','Maser'):
                if ch in meth:local_cal.append([pgc,ch,r[ch],r['e_'+ch]])
        if row['DMcal'] is not None and row['DMcal']>0:
            direct.append(gid)
            if row['DMav'] is not None and row['DMav']>0:direct_both.append(gid)
            if not local_cal:selected.append(gid)
        present=[]
        for meth in T3_METHODS:
            if meth=='SNII':flag=row['DMsnII'] is not None and row['DMsnII']>0
            else:flag=(row.get('o_'+meth) or 0)>0
            if flag:t3_presence[meth]+=1
            present.append(float(flag))
        if row['RAdeg'] is not None and row['DEdeg'] is not None:
            Z.append(present)
            X.append(sky_stf(row['RAdeg'],row['DEdeg']))
    Z=np.asarray(Z,dtype=float);X=np.asarray(X,dtype=float)
    if len(Z):
        rZ=int(np.linalg.matrix_rank(Z));rX=int(np.linalg.matrix_rank(X));rAll=int(np.linalg.matrix_rank(np.column_stack((Z,X))))
        projection_rank=rAll-rZ
        gram=X.T@X
        singular=np.linalg.svd(np.column_stack((Z,X)),compute_uv=False)
        shape_mean=X.mean(axis=0).tolist()
    else:rZ=rX=rAll=projection_rank=0;singular=np.array([]);shape_mean=[]
    return {
        'schema':SCHEMA,'input_identity':SOURCE,'input_digest_sha256':sha or {},
        'provenance':provenance,'n_individual_rows':len(t2),'n_group_rows':len(t3),
        'n_table4_rows':len(t4),'n_unique_1PGC':len(by3),
        'individual_method_counts':dict(t2_count),
        'individual_method_overlap_counts':dict(sorted(overlap.items())),
        'group_method_presence_counts':dict(t3_presence),
        'galaxy_1PGC_links':sum(bool(galaxies_bygroup.get(g)) for g in by3),
        'galaxy_1PGC_nonmembers_count':sum(g not in by3 for g in galaxies_bygroup),
        'direct_cal_group_count':len(direct),
        'direct_with_group_average_count':len(direct_both),
        'direct_without_galaxy_cal_link_count':len(selected),
        'direct_without_galaxy_cal_link_ids':sorted(selected),
        'group_DMzp_vs_DMav_0p001_histogram':dict(sorted(offsets.items())),
        'table3_table4_DMzp_discrepancies':mismatch,
        'angular_conditional_linear_rank':{
            'method_columns':list(T3_METHODS),'method_rank':rZ,'shape8_rank':rX,
            'joint_rank':rAll,'shape8_after_method_profile_rank':projection_rank,
            'sv_max':float(singular.max()) if len(singular) else None,
            'sv_min':float(singular.min()) if len(singular) else None,
            'directional_shape8_unweighted_mean':shape_mean,
        },
        'scientific_admission':{
            'source_group_join':'DESCRIPTION_NOT_NEW_INDEPENDENT_MEASUREMENT',
            'selection_parent_completeness':'NOT_CALIBRATED_FROM_CATALOGUE',
            'shared_calibration_covariance':'NOT_INFERRED_FROM_MARGINAL_ERROR_COLUMNS',
            'physical_kinematic_posterior':'NOT_RUN',
            'H02':'HOLD','S04':'HOLD',
        },
    }



def compare_selected_source(table4_rows, npz_path:Path):
    """Reconcile earlier 35,970 selected group keys and DMzp with complete raw Table4.

    Fail closed on source digest but retain source differences for scientific
    review rather than assuming an archive subset is byte-identical to raw rows.
    """
    import hashlib
    source_sha='86dfd896d5cf8f223396694dfb945137d1d28ea2227bc984665fb43f77fa376c'
    h=hashlib.sha256(npz_path.read_bytes()).hexdigest()
    if h!=source_sha:raise ValueError('selected NPZ source digest mismatch')
    z=np.load(npz_path,allow_pickle=False)
    try:
        ids=z['group_id'];mods=z['dmzp'];err=z['e_dmzp'];n=z['n_J2000']
        if len(ids)!=35970 or len(set(ids.tolist()))!=35970:raise ValueError('selected unique ID count mismatch')
        source={r['1PGC']:r for r in table4_rows}
        missing=[];diffs=[];es=[];sky=[]
        for id_,mu,sg,direc in zip(ids,mods,err,n):
            r=source.get(int(id_))
            if r is None:missing.append(int(id_));continue
            if r['DMzp'] is not None and r['e_DMzp'] is not None:
                diffs.append(abs(float(mu)-r['DMzp']))
                es.append(abs(float(sg)-r['e_DMzp']))
            if r['RAdeg'] is not None and r['DEdeg'] is not None:
                ra,de=np.deg2rad([r['RAdeg'],r['DEdeg']]);v=np.array([np.cos(de)*np.cos(ra),np.cos(de)*np.sin(ra),np.sin(de)])
                sky.append(float(np.linalg.norm(direc-v)))
        return {'status':'SOURCE_CROSSWALK_CHECK_NOT_PHYSICAL_VALIDATION','selected_count':len(ids),
            'missing_id_count':len(missing),'missing_ids_sample':missing[:30],
            'max_dmzp_abs_mag':max(diffs) if diffs else None,
            'max_e_dmzp_abs_mag':max(es) if es else None,
            'max_sky_unit_vector_delta':max(sky) if sky else None,
            'selected_sha256':source_sha,'source_total_rows':len(table4_rows)}
    finally:z.close()


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root',type=Path,default=Path('/mnt/extdrive/workdir/htt_open_data'))
    p.add_argument('--output',type=Path,default=None)
    p.add_argument('--selected-npz',type=Path,default=None,help='compare previous 35970-source sample by 1PGC identity')
    args=p.parse_args(argv)
    base=args.root/'cf4/J_ApJ_944_94'
    arrays={};sha={}
    for key,spec in [('table2',TABLE2),('table3',TABLE3),('table4',TABLE4)]:
        N,L,D=LOCKED[key]
        arr,hashv=read_table(base/f'{key}.dat',spec,key,expected=N,sha=D)
        arrays[key]=arr;sha[key]=hashv
    res=analyse(arrays['table2'],arrays['table3'],arrays['table4'],sha=sha,provenance='BYTES_REHASHED_IN_THIS_EXECUTION')
    if args.selected_npz:
        res['selected_vs_full_source_crosswalk']=compare_selected_source(arrays['table4'],args.selected_npz)
    out=args.output or args.root/'provenance/CF4_RAW_FULL_SOURCE_AUDIT.json'
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(res,ensure_ascii=False,sort_keys=True,indent=2)+'\n')
    print(json.dumps({'status':'SOURCE_LOCKED_AUDIT_DONE','result':str(out),'joined':res['galaxy_1PGC_links'],'direct_cal':res['direct_cal_group_count'],'group_zp_hist':res['group_DMzp_vs_DMav_0p001_histogram'],'H02':'HOLD'},ensure_ascii=False))

if __name__=='__main__':main()
