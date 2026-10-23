"""D03 actual public-release graph and conditional distance diagnostics.

Conditional working errors, profiled calibration responses and designed PSD
cross-covariance sensitivities are not the unknown survey joint sampling law.
"""
from pathlib import Path
from collections import Counter, defaultdict
import csv
import hashlib
import json
import re
import numpy as np
from scipy.linalg import cholesky, solve_triangular
from scipy.spatial import cKDTree
from astropy.io import fits

HERE=Path(__file__).resolve().parent
REPO=next(p for p in HERE.parents if (p/'AGENTS.md').exists())
RAW=Path('/mnt/extdrive/workdir/htt_open_data')
PANTHEON=RAW/'pantheonplus/c447f0f'
EXTRA=RAW/'pantheonplus/d03_crosswalk_20261018'
CF4=RAW/'cf4/J_ApJ_944_94'
EXPECTED={
 PANTHEON/'Pantheon_SH0ES.dat':'1cb0fc379ef066afdc2ffd1857681cc478024570d8a3eba284fb645775198cf8',
 PANTHEON/'Pantheon_SH0ES_STAT_SYS.cov':'abf806d966485e64afdb359c87bffc0ecc00d05eff0a31ced66f247385df0fdc',
 CF4/'ReadMe':'2cfed1418147d5a626dee1fa37c47252124477c9828490508d9bbe511d34edb4',
 CF4/'table2.dat':'8e908928e68352b59292cf67020a4d70aaa6d30f278dfa6aa3e41a9df808332f',
 CF4/'table3.dat':'c2351c52de3e38a7fd80256b6f0818c550dd9f105b91e84fbcc1eb7234160b4d',
}
META={'owner':'htt','claim_tier':'C0','status':'CONDITIONAL','artifact_mode':'NON_CLAIM_BEARING_EXPLORATORY',
      'transfer_source':'none','allowed_use':'source-conditioned calibration/direction/depth sensitivity',
      'null_status':'UNKNOWN: selection simulation lacks RA/DEC; no directional null',
      'covariance_status':'Pantheon full released symmetric part; CF4/cross-survey law UNKNOWN',
      'forbidden_uses':['physical anisotropy','independent survey validation','calibrated PTE','original node admission']}


def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def sealed(path, expected):
    blob=Path(path).read_bytes()
    if hashlib.sha256(blob).hexdigest()!=expected: raise ValueError('immutable source mismatch: '+str(path))
    return blob


def schema(text,name):
    section=text.split('Byte-by-byte Description of file: '+name+'\n',1)[1].split('Note (',1)[0]
    columns={}
    for line in section.splitlines():
        m=re.match(r'^\s*(\d+)(?:-\s*(\d+))?\s+([AIF]\d+(?:\.\d+)?)\s+\S+\s+(\S+)\s+',line)
        if m:
            a,b,fmt,label=m.groups();columns[label]=(int(a)-1,int(b or a),fmt[0])
    return columns


def table(path,columns,idkey,count):
    rows={}
    for line in Path(path).read_text('ascii').splitlines():
        row={}
        for name,(a,b,kind) in columns.items():
            value=line[a:b].strip()
            row[name]=None if not value else int(value) if kind=='I' else float(value) if kind=='F' else value
        identity=row[idkey]
        if identity is None or identity in rows: raise ValueError('missing or duplicated source identity')
        rows[identity]=row
    if len(rows)!=count: raise ValueError('source count differs from primary schema')
    return rows


def direction(ra,dec):
    a,d=np.deg2rad(np.asarray([ra,dec],float))
    return np.stack([np.cos(d)*np.cos(a),np.cos(d)*np.sin(a),np.sin(d)],axis=-1)


def separation(a,b):
    return float(np.rad2deg(2*np.arcsin(min(1.,np.linalg.norm(a-b)/2)))*3600)


def aliases(records):
    by=defaultdict(list)
    for row in records:
        for key in set([row['SNID'].strip(),row['IAUC'].strip()])-set(['']): by[key].append(row)
    return by


def choose_metadata(cid,point,lookup,limit_arcsec=2.):
    candidates=lookup.get(str(cid),[])
    close=[r for r in candidates if separation(point,direction(float(r['RA']),float(r['Dec'])))<=limit_arcsec]
    if not close: return None,'alias_absent' if not candidates else 'alias_sky_disagreement'
    # Multiple explicit aliases may name the same SN. Require identical host
    # coordinates/name and corroborating sky, rather than choosing the first.
    signatures={(r['host'].strip(),r['RA_host'],r['Dec_host']) for r in close}
    if len(signatures)!=1:return None,'ambiguous_alias_host'
    return sorted(close,key=lambda r:r['SNID'])[0],'alias_and_sky'


def graph(rows,records,galaxies,groups):
    lookup=aliases(records); gids=np.array(sorted(galaxies)); gr=[galaxies[int(i)] for i in gids]
    sky=direction([g['RAdeg'] for g in gr],[g['DEdeg'] for g in gr]); tree=cKDTree(sky)
    output=[]
    for i,r in enumerate(rows):
        point=direction(r['RA'],r['DEC']); m,status=choose_metadata(r['CID'],point,lookup)
        out={'row_index':i,'CID_literal':str(r['CID']),'IDSURVEY':int(r['IDSURVEY']),
             'IS_CALIBRATOR':int(r['IS_CALIBRATOR']),'RA':float(r['RA']),'DEC':float(r['DEC']),
             'CEPH_DIST_released_mag':float(r['CEPH_DIST']) if r['IS_CALIBRATOR'] else None,
             'USED_IN_SH0ES_HF':int(r['USED_IN_SH0ES_HF']),
             'zCMB':float(r['zCMB']),'zHD':float(r['zHD']),'MU_SH0ES':float(r['MU_SH0ES']),
             'SNID':None,'IAUC':None,'host_name':None,'PGC':None,'group_1PGC':None,
             'association_status':status,'host_separation_arcsec':None,
             'second_host_separation_arcsec':None,'cz_difference_km_s':None,
             'exact_CF4_SN_contributor_identity':'UNKNOWN_EDD_HUMAN_VERIFICATION_BARRIER',
             'upstream_calibration':'SH0ES_Cepheid_hosts+common_CF4_scale; shared ancestry UNKNOWN quantitatively'}
        if m is not None:
            out.update(SNID=m['SNID'].strip(),IAUC=m['IAUC'].strip() or None,host_name=m['host'].strip() or None)
            if not m['RA_host'] or not m['Dec_host'] or m['has_host']!='1':out['association_status']='missing_upstream_host'
            else:
                dist,j=tree.query(direction(float(m['RA_host']),float(m['Dec_host'])),k=2)
                seps=np.rad2deg(2*np.arcsin(np.minimum(1,dist/2)))*3600
                g=gr[int(j[0])]; dz=float(r['zCMB']*299792.458-g['Vcmb'])
                out.update(host_separation_arcsec=float(seps[0]),second_host_separation_arcsec=float(seps[1]),cz_difference_km_s=dz)
                if seps[0]>3:out['association_status']='no_CF4_host_within_3arcsec'
                elif seps[1]<=3:out['association_status']='ambiguous_CF4_hosts'
                elif abs(dz)>500:out['association_status']='host_coordinate_match_redshift_disagreement'
                elif g['1PGC'] not in groups:out['association_status']='host_group_missing'
                else:
                    out.update(PGC=int(gids[j[0]]),group_1PGC=g['1PGC'],association_status='unique_host_coordinate_and_redshift')
        output.append(out)
    return output


def nuisance(rows,method):
    surveys=sorted(set(map(int,rows['IDSURVEY'])))
    methods=sorted(set(method))
    labels=['common_offset','calibrator']+[f'survey_{s}' for s in surveys]+[f'method_{s}' for s in methods]
    N=np.column_stack([np.ones(len(rows)),rows['IS_CALIBRATOR']]+[(rows['IDSURVEY']==s).astype(float) for s in surveys]+[(np.array(method)==s).astype(float) for s in methods])
    return N,labels


def gls(y,V,N,T):
    """Explicit SVD nuisance quotient; no prior/ridge or chosen gauge required."""
    L=cholesky(V,lower=True);wy=solve_triangular(L,y,lower=True)
    WN=solve_triangular(L,N,lower=True);WT=solve_triangular(L,T,lower=True)
    u,s,vt=np.linalg.svd(WN,full_matrices=False)
    tol=max(WN.shape)*np.finfo(float).eps*s[0];rank=int(np.sum(s>tol));q=u[:,:rank]
    Ty=wy-q@(q.T@wy);TT=WT-q@(q.T@WT)
    b,_,trank,ts=np.linalg.lstsq(TT,Ty,rcond=None)
    nuisance_beta=vt[:rank].T@((u[:,:rank].T@(wy-WT@b))/s[:rank])
    residual=y-N@nuisance_beta-T@b
    return {'nuisance_rank':rank,'nuisance_columns':N.shape[1],
            'nuisance_nullspace_basis':vt[rank:].tolist(), 'nuisance_singular_values':s.tolist(),
            'nuisance_svd_tolerance':float(tol),'gauge':'minimum-norm representative; only N beta is identified',
            'nuisance_beta_minimum_norm':nuisance_beta.tolist(),
            'response_rank':int(trank),'response_singular_values':ts.tolist(),
            'beta_direction_depth':b.tolist(),'residual_rms_mag':float(np.sqrt(np.mean(residual**2))),
            'profiled_weighted_square_diagnostic':float(np.sum(solve_triangular(L,residual,lower=True)**2)),
            'coefficient_uncertainty':'NOT_CALIBRATED_UNKNOWN_JOINT_LAW'},residual


def covariance_family(P,B,sigma,rho):
    """PSD joint covariance by a contraction, for designed sensitivity only.

    X = rho Lp U diag(sigma), U = B / ||B||2. The latent CF4 errors
    have unit covariance; its rows are shared by exact method/group keys.
    Residual covariance P+B diag(sigma²) Bᵀ-XBᵀ-BXᵀ.
    """
    if abs(rho)>1:raise ValueError('|rho| must be <=1')
    norm=float(np.linalg.svd(B,compute_uv=False)[0]);U=B/norm
    L=cholesky(P,lower=True);X=rho*(L@U)*sigma[None,:]
    V=P+(B*sigma**2)@B.T-X@B.T-B@X.T
    V=(V+V.T)/2
    unorm=float(np.linalg.svd(U,compute_uv=False)[0])
    schur=1-rho*rho*unorm*unorm
    if unorm>1+1e-12 or schur < -1e-12:raise ValueError('invalid contraction/Schur bound')
    Lr=cholesky(V,lower=True)
    return V,{'rho':rho,'U_spectral_norm':unorm,'whitened_joint_Schur_min_bound':schur,
              'residual_min_cholesky_diagonal':float(np.min(np.diag(Lr)))}


def compare(rows,C,links,galaxies,groups,mode):
    selected=[];keys=[];mu=[];sigma=[];methods=[]
    for link in links:
        if link['PGC'] is None:continue
        g=galaxies[link['PGC']];group=groups[link['group_1PGC']]
        if mode=='host_SN':r=g;idkey=link['PGC'];method='SN';field='DMsnIa'
        elif mode=='group_SN':r=group;idkey=link['group_1PGC'];method='SN';field='DMsnIa'
        else:
            r=group;idkey=link['group_1PGC']
            # A declared retrospective control, never a selection law:
            # compare TF where released, otherwise the released SN group mean.
            method='TF' if r['DMtf'] is not None else 'SN';field='DMtf' if method=='TF' else 'DMsnIa'
        val,err=r[field],r['e_'+field]
        if val is None or err is None or err<=0:continue
        selected.append(link['row_index']);keys.append((method,idkey));mu.append(val);sigma.append(err);methods.append(method)
    idx=np.array(selected,int);selected_rows=rows[idx];P=C[np.ix_(idx,idx)]
    unique=sorted(set(keys));kmap={k:i for i,k in enumerate(unique)};B=np.zeros((len(idx),len(unique)));sd=np.zeros(len(unique))
    for j,(key,err) in enumerate(zip(keys,sigma)):
        k=kmap[key];B[j,k]=1
        if sd[k] and sd[k]!=err:raise ValueError('same source measurement with inconsistent uncertainty')
        sd[k]=err
    y=selected_rows['MU_SH0ES']-mu
    N,labels=nuisance(selected_rows,methods)
    d=direction(selected_rows['RA'],selected_rows['DEC']);z=selected_rows['zCMB'];z0=float(np.median(z))
    T=np.column_stack([d,(z-z0)/.02])
    fitsout=[];residual=None;Vzero=None
    for rho in [-.75,0.,.75]:
        V,control=covariance_family(P,B,sd,rho);fit,res=gls(y,V,N,T)
        fitsout.append({**control,**fit})
        if rho==0:residual=res;Vzero=V
    # A permutation replay checks the complete row/covariance/design binding.
    perm=np.arange(len(idx))[::-1]
    replay,_=gls(y[perm],Vzero[np.ix_(perm,perm)],N[perm],T[perm])
    delta=float(np.max(np.abs(np.array(replay['beta_direction_depth'])-np.array(fitsout[1]['beta_direction_depth']))))
    if delta>1e-10:raise ValueError('row/covariance permutation replay failed')
    return ({'mode':mode,'rows':len(idx),'literal_CIDs':len(set(selected_rows['CID'])),
            'CF4_source_scale':'galaxy method distance after common-scale MCMC registration' if mode=='host_SN' else 'group method distance on arbitrary SNIa scale; absolute DMzp not substituted; free offset retained',
            'host_PGCs':len({links[int(i)]['PGC'] for i in idx}),
            'source_measurement_keys':len(unique),'calibrator_rows':int(selected_rows['IS_CALIBRATOR'].sum()),
            'method_row_counts':dict(Counter(methods)),'zCMB_range':[float(z.min()),float(z.max())],
            'raw_difference_quantiles_mag':np.quantile(y,[0,.25,.5,.75,1]).tolist(),
            'nuisance_labels':labels,'response_labels':['nx_mag','ny_mag','nz_mag','depth_mag_per_0.02_zCMB'],
            'depth_center_zCMB':z0,'permutation_beta_max_difference':delta,'fits':fitsout,
            'sensitivity_scope':'Three chosen rho values along one Cholesky-basis contraction; not exhaustive unknown-crosscov bounds or coverage',
            'shared_CF4_errors':'B diag(released_error²) B.T; independent latent keys only a conditional working choice',
            'calibration':'common+calibrator+survey+method responses jointly profiled with explicit nullspace; no independent anchor extracted'},
           {'row_index':idx,'P_full_covariance_subblock':P,'B_CF4_incidence':B,'CF4_sigma':sd,
            'y_mag':y,'nuisance_design':N,'response_design':T,'zCMB':z,'RA':selected_rows['RA'],
            'DEC':selected_rows['DEC'],'residual_rho0':residual,'source_keys':np.array([f'{m}:{i}' for m,i in unique]),
            'CF4_modulus':np.array(mu),'methods':np.array(methods)})


def shoes_input():
    paths=[EXTRA/'allc_shoes_ceph_topantheonwt6.0_112221.fits',EXTRA/'alll_shoes_ceph_topantheonwt6.0_112221.fits.lfs_pointer',EXTRA/'ally_shoes_ceph_topantheonwt6.0_112221.fits.lfs_pointer']
    pointer=(EXTRA/(paths[0].name+'.lfs_pointer')).read_text();fields=dict(line.split(' ',1) for line in pointer.splitlines()[1:])
    assert paths[0].stat().st_size==int(fields['size']) and sha(paths[0])==fields['oid'].split(':')[1]
    C,L,y=[np.asarray(fits.getdata(p),float) for p in paths]
    assert C.shape==(len(y),len(y)) and L.shape[1]==len(y) and np.isfinite(C).all() and np.isfinite(L).all() and np.isfinite(y).all()
    asym=float(np.max(np.abs(C-C.T)));Lc=cholesky((C+C.T)/2,lower=True)
    fields=Counter()
    for line in (EXTRA/'SH0ES_table2.tex').read_text().splitlines():
        if not line or line.startswith(('\\','%')):continue
        parts=line.split('&')
        if len(parts)==11:
            try:float(parts[1]);float(parts[2])
            except ValueError:continue
            fields[parts[0].strip()]+=1
    return {'source_commit':'c447f0fea703fcd0fff57de5000947b5ca81286b',
            'files':{p.name:{'path':str(p),'sha256':sha(p),'bytes':p.stat().st_size} for p in paths},
            'LFS_C_SHA_size':'MATCH','C_shape':list(C.shape),'L_stored_shape':list(L.shape),'y_shape':list(y.shape),
            'C_max_asymmetry':asym,'C_symmetric_part_cholesky_min':float(np.diag(Lc).min()),
            'published_table2_Cepheid_field_counts':dict(fields),
            'use':'INPUT_QUALIFIED_ONLY_NOT_REFIT; no upstream code executed',
            'cross_survey_crosscov':'UNKNOWN; this ladder C is not a CF4 joint covariance',
            'host_parameter_mapping':'NOT_ADOPTED_WITHOUT_AUTHORITATIVE_LABEL_ORDER; table2 field names/sky ancestry retained'}


def run():
    out=HERE/'results';out.mkdir(exist_ok=True)
    for path,expected in EXPECTED.items():sealed(path,expected)
    acq=json.loads((EXTRA/'ACQUISITION.json').read_text())
    primary=next(a for a in acq if a['name']=='all_redshifts_PVs.csv' and 'sha256' in a)
    sealed(EXTRA/'all_redshifts_PVs.csv',primary['sha256'])
    records=list(csv.DictReader((EXTRA/'all_redshifts_PVs.csv').open()))
    rows=np.genfromtxt(PANTHEON/'Pantheon_SH0ES.dat',names=True,dtype=None,encoding='utf-8')
    raw=np.loadtxt(PANTHEON/'Pantheon_SH0ES_STAT_SYS.cov');n=int(raw[0]);Craw=raw[1:].reshape(n,n)
    if n!=1701 or len(rows)!=n:raise ValueError('1701 row/full matrix contract failed')
    C=(Craw+Craw.T)/2;cholesky(C,lower=True)
    readme=(CF4/'ReadMe').read_text('ascii')
    galaxies=table(CF4/'table2.dat',schema(readme,'table2.dat'),'PGC',55877)
    groups=table(CF4/'table3.dat',schema(readme,'table3.dat'),'1PGC',38053)
    links=graph(rows,records,galaxies,groups)
    prior=REPO/'docs/research_program/theory_obs_application_20261015/loop6_kinematics/results/cf4_rawgroup_appHubble_STF2_pooled_methods_v2/selected_source_observables.npz'
    prior_sha='86dfd896d5cf8f223396694dfb945137d1d28ea2227bc984665fb43f77fa376c'
    sealed(prior,prior_sha)
    with np.load(prior,allow_pickle=False) as old:selected_ids=set(map(int,old['group_id']))
    for link in links:link['in_previous_H02_selected_groups']=link['group_1PGC'] in selected_ids if link['group_1PGC'] is not None else None
    with (out/'OBJECT_GRAPH.csv').open('w',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=list(links[0]));writer.writeheader();writer.writerows(links)
    comparisons=[]
    for mode in ['host_SN','group_SN','group_TF_else_SN']:
        summary,arrays=compare(rows,C,links,galaxies,groups,mode)
        comparisons.append(summary);np.savez_compressed(out/(mode+'.npz'),**arrays)
    result={'metadata':META,'source_identities':{str(p):sha(p) for p in EXPECTED},
            'pantheon_metadata':primary,'graph_counts':{'all_rows_retained':len(links),
            'literal_CID_strings':len(set(rows['CID'])),'calibrator_rows':int(rows['IS_CALIBRATOR'].sum()),
            'status':dict(Counter(l['association_status'] for l in links)),
            'matched_PGCs':len({l['PGC'] for l in links if l['PGC'] is not None}),
            'matched_groups':len({l['group_1PGC'] for l in links if l['group_1PGC'] is not None}),
            'previous_H02_selected_group_associations':sum(l['in_previous_H02_selected_groups'] is True for l in links),
            'host_coordinate_radius_design_arcsec':3,'redshift_agreement_design_km_s':500,
            'source_alias_sky_agreement_design_arcsec':2,
            'host_radius_counts_1_3_10arcsec':{str(k):sum(l['host_separation_arcsec'] is not None and l['host_separation_arcsec']<=k for l in links) for k in [1,3,10]},
            'claim':'unique source-coordinate associations, not proved exact CF4 individual SN contributor identities'},
            'covariance':{'units':'mag^2','raw_max_asymmetry':float(np.max(np.abs(Craw-Craw.T))),
            'adopted_for_conditional_diagnostics':'(C_raw+C_raw.T)/2; raw unchanged',
            'row_order':'literal 0-based published order; all selected subblocks by exact row indices',
            'row_identity_sha256':hashlib.sha256('\n'.join(f'{i}|{r["CID"]}|{r["IDSURVEY"]}' for i,r in enumerate(rows)).encode()).hexdigest()},
            'SH0ES_actual_full_input':shoes_input(),'comparisons':comparisons,
            'reused_previous_H02_cache':{'path':str(prior),'sha256':prior_sha,'selected_groups':len(selected_ids),'use':'membership only; no prior coefficient experiment rerun'},
            'unresolved':['Exact EDD SNIa/PGC contributor aliases behind human verification',
                          'CF4 within/across-method joint covariance and Pantheon–CF4 crosscovariance',
                          'Full upstream SH0ES ladder host-label mapping and CF4 calibration response',
                          'Actual targeting/selection and matched directional null law'],
            'scientific_node_status':{'H02':'HOLD','H04':'HOLD','S04':'HOLD','K04':'HOLD'},
            'review':'PENDING_FRESH_INDEPENDENT_REVIEW','input_source_count_is_not_independent_SN_count':True}
    (out/'D03_RESULT.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    print(json.dumps({'graph_counts':result['graph_counts'],'comparisons':[{k:c[k] for k in ['mode','rows','host_PGCs','source_measurement_keys','method_row_counts']} for c in comparisons],'SH0ES_C':result['SH0ES_actual_full_input']['C_shape']}))


if __name__=='__main__':run()
