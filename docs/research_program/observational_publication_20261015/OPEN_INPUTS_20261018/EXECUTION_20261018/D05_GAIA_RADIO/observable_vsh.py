"""Observable l=1,2 tangent harmonics, not a cosmological response.

ICRS Cartesian basis, east=mu_alpha*cos(delta), north=mu_delta, microas/yr.
E1=P g; B1=omega cross n; E2=P S n; B2=n cross S n.
S is symmetric trace-free in the explicitly listed Frobenius-orthonormal basis.
No orthonormal spherical-harmonic power normalization is asserted.
"""
from pathlib import Path
import csv, gzip, hashlib, json, platform, xml.etree.ElementTree as ET
import numpy as np
from astropy.io.votable import parse_single_table
from astropy.table import Table
from astropy import units as u
from scipy.spatial import cKDTree

HERE=Path(__file__).resolve().parent
RAW=Path('/mnt/extdrive/workdir/htt_open_data/gaia/d05_full_20261018')
MEMBER=Path('/mnt/extdrive/workdir/htt_open_data/gaia/DR3/gaiadr3.gaia_crf3_xm.ecsv.gz')
RADIO=Path('/mnt/extdrive/workdir/htt_open_data/vlba/233_3')
LABELS=['E1_x','E1_y','E1_z','B1_frame_x','B1_frame_y','B1_frame_z',
        'E2_xx-yy','E2_zz','E2_xy','E2_xz','E2_yz',
        'B2_xx-yy','B2_zz','B2_xy','B2_xz','B2_yz']
S=np.array([[[1,0,0],[0,-1,0],[0,0,0]],
            [[-1,0,0],[0,-1,0],[0,0,2]],
            [[0,1,0],[1,0,0],[0,0,0]],
            [[0,0,1],[0,0,0],[1,0,0]],
            [[0,0,0],[0,0,1],[0,1,0]]],float)
S/=np.array([np.sqrt(2),np.sqrt(6),np.sqrt(2),np.sqrt(2),np.sqrt(2)])[:,None,None]
KEEP=np.array([0,1,2,*range(6,16)])
FRAME=np.array([3,4,5])

def digest(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for b in iter(lambda:f.read(1024**2),b''):h.update(b)
    return h.hexdigest()

def tangent(ra,dec):
    a,d=np.deg2rad(ra),np.deg2rad(dec)
    n=np.stack([np.cos(d)*np.cos(a),np.cos(d)*np.sin(a),np.sin(d)],axis=-1)
    east=np.stack([-np.sin(a),np.cos(a),np.zeros_like(a)],axis=-1)
    north=np.stack([-np.sin(d)*np.cos(a),-np.sin(d)*np.sin(a),np.cos(d)],axis=-1)
    return n,np.stack([east,north],axis=1)

def design(ra,dec):
    n,T=tangent(ra,dec)
    e1=np.broadcast_to(np.eye(3),(len(n),3,3))-n[:,:,None]*n[:,None,:]
    b1=np.cross(np.eye(3)[None,:,:],n[:,None,:]).transpose(0,2,1)
    sn=np.einsum('pij,nj->npi',S,n)
    e2=sn-n[:,None,:]*np.einsum('ni,npi->np',n,sn)[:,:,None]
    b2=np.cross(n[:,None,:],sn)
    cart=np.concatenate([e1,b1,e2.transpose(0,2,1),b2.transpose(0,2,1)],axis=2)
    return np.einsum('nki,nip->nkp',T,cart)

def precision(sa,sd,rho):
    sa,sd,rho=np.broadcast_arrays(sa,sd,rho)
    if not np.all(np.isfinite([sa,sd,rho])) or np.any(sa<=0) or np.any(sd<=0) or np.any(np.abs(rho)>=1):
        raise ValueError('Covariance requires positive finite errors and abs(rho)<1')
    w=np.empty(sa.shape+(2,2));scale=1/(1-rho*rho)
    w[...,0,0]=scale/sa**2;w[...,1,1]=scale/sd**2
    w[...,0,1]=w[...,1,0]=-scale*rho/(sa*sd)
    return w

def normal(X,y,w):
    wx=np.einsum('nij,njp->nip',w,X)
    wy=np.einsum('nij,nj->ni',w,y)
    return (np.einsum('nip,niq->pq',X,wx),np.einsum('nip,ni->p',X,wy),
            float(np.einsum('ni,ni->',y,wy)),len(y))

def combine(parts):
    return tuple(sum(p[i] for p in parts) for i in range(4))

def solve(stats):
    N,h,ywy,n=stats;b=np.linalg.solve(N,h);cov=np.linalg.inv(N)
    nf=N[np.ix_(FRAME,FRAME)];nq=N[np.ix_(KEEP,FRAME)]
    schur=N[np.ix_(KEEP,KEEP)]-nq@np.linalg.solve(nf,nq.T)
    rhs=h[KEEP]-nq@np.linalg.solve(nf,h[FRAME])
    bp=np.linalg.solve(schur,rhs)
    return dict(n=int(n),rank=int(np.linalg.matrix_rank(N)),condition_number=float(np.linalg.cond(N)),
                coefficient_uasyr=b.tolist(),formal_sigma_uasyr=np.sqrt(np.diag(cov)).tolist(),
                formal_covariance_uas2yr2=cov.tolist(),
                working_reduced_chi2=float((ywy-b@h)/(2*n-len(b))),
                frame_projected=dict(rank=int(np.linalg.matrix_rank(schur)),
                    coefficient_order=[LABELS[i] for i in KEEP],coefficient_uasyr=bp.tolist(),
                    covariance_uas2yr2=np.linalg.inv(schur).tolist(),
                    max_joint_fit_difference=float(np.max(np.abs(bp-b[KEEP]))),
                    B1_physical_components=['UNKNOWN','UNKNOWN','UNKNOWN'],
                    reason='Arbitrary frame spin is exactly degenerate with all three B1 columns'))

def read_vot(name):
    path=RAW/(name+'.vot')
    jobmeta=json.loads((RAW/(name+'.job.json')).read_text()) if (RAW/(name+'.job.json')).exists() else {}
    actual_hash=digest(path)
    if jobmeta.get('sha256') and actual_hash!=jobmeta['sha256']:
        raise ValueError('Collected source byte identity mismatch')
    uwspath=RAW/(name+'.uws.xml')
    provider_size=None
    if uwspath.exists():
        job=ET.parse(uwspath).getroot()
        if job.findtext('{*}phase')!='COMPLETED':raise ValueError('UWS job not complete')
        result=job.find('.//{*}result')
        provider_size=int(result.get('size')) if result is not None and result.get('size') else None
        if provider_size is not None and path.stat().st_size!=provider_size:raise ValueError('UWS advertised size mismatch')
    # Parse XML status without loading the base64 data into a second full tree.
    status=[]
    for _,elem in ET.iterparse(path,events=('end',)):
        if elem.tag.endswith('INFO') and elem.get('name')=='QUERY_STATUS':status.append(elem.get('value'))
        elem.clear()
    if not status or any(s!='OK' for s in status):raise ValueError('Non-complete VOTable: '+str(status))
    tab=parse_single_table(path).to_table()
    return tab,dict(path=str(path),sha256=actual_hash,bytes=path.stat().st_size,
                    rows=len(tab),query_status=status,overflow=False,provider_result_bytes=provider_size,
                    job={k:jobmeta.get(k) for k in ('job_url','job_id','query','query_sha256','format','maxrec','phase','result_url')},
                    fields={n:dict(unit=str(tab[n].unit),description=tab[n].description) for n in tab.colnames})

def members():
    source_hash=digest(MEMBER)
    cache=RAW/'membership_selected_bound.npz'
    names=RAW/'membership_radio_names_bound.json'
    if cache.exists():
        z=np.load(cache)
        if str(z['membership_sha256'])!=source_hash or str(z['names_sha256'])!=digest(names):
            raise ValueError('Derived membership cache source/name binding mismatch')
        return z['ids'],z['icrf'],json.loads(names.read_text())
    ids=[];icrf=[];rows=[]
    with gzip.open(MEMBER,'rt') as f:
        it=(line for line in f if not line.startswith('#'))
        for row in csv.DictReader(it):
            ids.append(int(row['source_id']))
            isradio=any(row[x]=='True' for x in ('icrf3sx','icrf3k','icrf3xka'))
            icrf.append(isradio)
            if isradio or row['ocars']=='True':
                rows.append({k:row[k] for k in ('source_id','iers_name','icrf_name','ocars_name')})
    ids=np.asarray(ids,dtype=np.int64);icrf=np.asarray(icrf)
    names.write_text(json.dumps(rows))
    np.savez(cache,ids=ids,icrf=icrf,membership_sha256=source_hash,names_sha256=digest(names))
    return ids,icrf,rows

def radio_rows():
    # Original CDS byte ranges are one-based inclusive. Coordinates are degrees.
    rows=[]
    for l in (RADIO/'table6.dat').read_text().splitlines():
        if not l.strip():continue
        ra=15*(float(l[9:11])+float(l[12:14])/60+float(l[15:24])/3600)
        dec=(float(l[33:35])+float(l[36:38])/60+float(l[39:48])/3600)*(-1 if l[32]=='-' else 1)
        rows.append((l[:8].strip(),ra,dec,float(l[56:64]),float(l[84:91]),float(l[65:72]),float(l[92:99])))
    return rows

def crosswalk(tab,member_names):
    rows=radio_rows();gids=np.array(tab['source_id']);pos={int(x):i for i,x in enumerate(gids)}
    lookup={}
    for r in member_names:
        for k in ('iers_name','ocars_name'):
            key=r[k].strip()
            if key:lookup.setdefault(key,set()).add(int(r['source_id']))
    n,T=tangent(np.array(tab['ra']),np.array(tab['dec']));tree=cKDTree(n)
    matches=[]
    for name,ra,dec,*_ in rows:
        v,_=tangent(np.array([ra]),np.array([dec]));dist,ix=tree.query(v,k=2)
        sep=np.rad2deg(2*np.arcsin(np.minimum(dist[0]/2,1)))*3600
        name_ids=lookup.get(name,set());candidates=[int(gids[j]) for j,s in zip(ix[0],sep) if s<=1.0]
        sid=candidates[0] if len(candidates)==1 else None
        exact=list(name_ids & set(candidates))
        matches.append(dict(radio_name=name,name_ids=sorted(name_ids),nearest_separation_arcsec=float(sep[0]),
            second_separation_arcsec=float(sep[1]),candidate_ids=candidates,accepted_source_id=sid,
            exact_name_position_agreement=bool(exact),method='Unique positional match within 1 arcsec; names as independent cross-check'))
    # Row-level crosswalk remains external.
    (RAW/'radio_crosswalk.json').write_text(json.dumps(matches,indent=2)+'\n')
    matched=[m for m in matches if m['accepted_source_id'] is not None]
    return dict(total_radio=len(rows),matched_1arcsec=len(matched),
                ambiguous_1arcsec=sum(len(m['candidate_ids'])>1 for m in matches),
                unmatched_1arcsec=sum(not m['candidate_ids'] for m in matches),
                matches_with_exact_name_agreement=sum(m['exact_name_position_agreement'] for m in matched),
                unique_gaia_matches=len({m['accepted_source_id'] for m in matched}),
                matched_at_0p1arcsec=sum(m['nearest_separation_arcsec']<.1 for m in matches),
                raw_crosswalk=str(RAW/'radio_crosswalk.json'),
                raw_crosswalk_sha256=digest(RAW/'radio_crosswalk.json'),
                interpretation='Crosswalk is positional compatibility, not proof of independent radio/optical errors; radio epoch and optical structure can alter offsets')

def radio_sensitivity():
    r=radio_rows();ra=np.array([x[1] for x in r]);dec=np.array([x[2] for x in r])
    y0=np.array([[x[3],x[4]] for x in r]);e0=np.array([[x[5],x[6]] for x in r])
    out=[];X=design(ra,dec)
    # CDS calls this pmRA without an explicit cos(delta) statement. Carry both
    # conventions until the original table convention is resolved; never choose
    # the convention by which one gives a preferred scientific coefficient.
    for convention in ('published_pmRA_is_tangent','published_pmRA_is_coordinate_rate'):
        y=y0.copy();e=e0.copy()
        if convention.endswith('coordinate_rate'):
            y[:,0]*=np.cos(np.deg2rad(dec));e[:,0]*=np.cos(np.deg2rad(dec))
        for rho in (-.9,-.5,.5,.9):
            fit=solve(normal(X,y,precision(e[:,0],e[:,1],rho)))
            out.append(dict(convention=convention,assumed_missing_component_rho=rho,**fit))
    return dict(rows=len(r),cross_component_covariance='MISSING_NOT_ZERO',
                convention_status='CDS ReadMe does not explicitly distinguish coordinate rate from tangent component; both sensitivity branches retained',
                sensitivity_grid=out,correlation_scope='Common-rho illustrative family only, not exhaustive unknown 713-dimensional rho-vector or cross-source covariance bound',
                independence='NOT_ESTABLISHED: ICRF overlap, radio jets, NNR and shared celestial axes',
                NNR='Goddard 2017a five overlapping solutions relaxed NNR over successive quarters of ICRF2 defining sources; transfer of removed dipoles is unavailable')

def main():
    tab,identity=read_vot('full');ct,ci=read_vot('count');frame,fi=read_vot('frame')
    for name in ('ra','dec'):
        if tab[name].unit!=u.deg:raise ValueError('Unexpected angular unit for '+name)
    for name in ('pmra','pmdec','pmra_error','pmdec_error'):
        if tab[name].unit!=u.mas/u.yr:raise ValueError('Unexpected proper-motion unit for '+name)
    mids,micrf,mnames=members();ids=np.asarray(tab['source_id'],dtype=np.int64)
    if len(ids)!=len(np.unique(ids)) or len(mids)!=len(np.unique(mids)):raise ValueError('Duplicate membership/source ID')
    if int(ct[0][0])!=len(ids) or not np.array_equal(np.sort(ids),np.sort(mids)):raise ValueError('Full COUNT/member set mismatch')
    # Do not coerce masked values to valid numerical data.
    cols=['ra','dec','pmra','pmdec','pmra_error','pmdec_error','pmra_pmdec_corr']
    valid=np.ones(len(ids),bool)
    for c in cols:valid &= ~np.ma.getmaskarray(tab[c]) & np.isfinite(np.asarray(tab[c]))
    valid &= (np.asarray(tab['pmra_error'])>0)&(np.asarray(tab['pmdec_error'])>0)&(np.abs(np.asarray(tab['pmra_pmdec_corr']))<1)
    a={c:np.asarray(tab[c],dtype=float)[valid] for c in cols};vids=ids[valid]
    fids=np.asarray(frame['source_id'],dtype=np.int64)
    fs=np.isin(vids,fids[np.asarray(frame['used_for_reference_frame_spin'],bool)])
    fo=np.isin(vids,fids[np.asarray(frame['used_for_reference_frame_orientation'],bool)])
    n,T=tangent(a['ra'],a['dec'])
    sky=np.minimum((a['ra']//90).astype(int),3)+4*np.minimum(((n[:,2]+1)*1.5).astype(int),2)
    parts=[];spinparts=[];notspinparts=[]
    # Finite chunking only changes accumulation; no random or outcome-based cuts.
    for j in range(12):
        p=[];sp=[];np_=[];where=np.flatnonzero(sky==j)
        for off in range(0,len(where),50000):
            ix=where[off:off+50000];X=design(a['ra'][ix],a['dec'][ix])
            y=np.stack([a['pmra'][ix],a['pmdec'][ix]],axis=1)*1000
            w=precision(a['pmra_error'][ix]*1000,a['pmdec_error'][ix]*1000,a['pmra_pmdec_corr'][ix])
            p.append(normal(X,y,w));use=fs[ix]
            if np.any(use):sp.append(normal(X[use],y[use],w[use]))
            if np.any(~use):np_.append(normal(X[~use],y[~use],w[~use]))
        parts.append(combine(p));spinparts.extend(sp);notspinparts.extend(np_)
    allstats=combine(parts);fit=solve(allstats);b=np.array(fit['coefficient_uasyr'])
    heldout=[]
    for j,hold in enumerate(parts):
        train=combine([p for k,p in enumerate(parts) if k!=j]);trainfit=solve(train)
        bt=np.asarray(trainfit['coefficient_uasyr']);N,h,ywy,nj=hold
        heldout.append(dict(cell=j,heldout_sources=nj,train_sources=train[3],
            coefficient_uasyr=bt.tolist(),
            heldout_working_mean_chi2_per_component=float((ywy-2*bt@h+bt@N@bt)/(2*nj)),
            heldout_null_mean_chi2_per_component=float(ywy/(2*nj))))
    deleted=np.array([x['coefficient_uasyr'] for x in heldout])
    # Block score sandwich is a sensitivity diagnostic with only 12 blocks,
    # never a coverage-calibrated uncertainty or an empirical full sky law.
    N,h,_,_=allstats;inv=np.linalg.inv(N)
    scores=np.array([p[1]-p[0]@b for p in parts]);sand=inv@(scores.T@scores)@inv*12/11
    result=dict(schema='htt.D05.observable_vsh/1',owner='obsstat',scope='Actual full Gaia-CRF3 l1+l2 observable VSH, conditional on published astrometry and working covariance',
       claim_tier='DIAGNOSTIC_ONLY',transfer_source='none',artifact_mode='OBSERVABLE_FIT_AND_SENSITIVITY',
       sky_support_status='Complete public CRF3 membership; retained source directions conditioned exact',
       null_mock_status='NOT_AVAILABLE: no empirical joint sky/frame/calibration null',
       allowed_use='Catalogue observable coefficients, frame quotient and conditional sensitivity only',
       generating_command='OMP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=2 MKL_NUM_THREADS=2 .venv/bin/python '+str(Path(__file__).relative_to(Path.cwd())),
       K03_status='HOLD_PHYSICAL_CONGRUENCE_RESPONSE_AND_JOINT_SYSTEMATICS_MISSING',
       runtime=dict(requested_model='gpt-6-sol',requested_effort='high',observed_model='UNKNOWN',observed_effort='UNKNOWN',python=platform.python_version(),numpy=np.__version__,threads=2),
       source_commit='1528ebd3c4ace48a561b9dcaa6d5f891121a22a5',code_sha256=digest(__file__),
       source_identity=dict(full=identity,count=ci,frame=fi,membership_sha256=digest(MEMBER),membership_bytes=MEMBER.stat().st_size,
            radio_table_sha256=digest(RADIO/'table6.dat'),radio_ReadMe_sha256=digest(RADIO/'ReadMe')),
       completeness=dict(returned_rows=len(ids),count=int(ct[0][0]),membership_rows=len(mids),source_id_sets_equal=True,unique_source_ids=True,MAXREC=2500000,overflow=False),
       retention=dict(valid_sources=int(valid.sum()),rejected_sources=int((~valid).sum()),rule='Finite unmasked RA/Dec, both pm and positive errors, abs(correlation)<1; no proper-motion cut or RUWE cut',
            upstream_selection='CRF3 itself was astrometrically filtered, including proper motions; results are conditioned on that released selection, not an unbiased unselected QSO population',
            five_parameter=int(np.sum(np.asarray(tab['astrometric_params_solved'])[valid]==31)),six_parameter=int(np.sum(np.asarray(tab['astrometric_params_solved'])[valid]==95))),
       covariance=dict(within_source='C=[[sra^2,rho*sra*sdec],[rho*sra*sdec,sdec^2]], input mas^2/yr^2 converted to uas^2/yr^2',
            spatial='NOT_PROVIDED: working fits do not assert cross-source independence as an empirical fact',
            correlation_min=float(a['pmra_pmdec_corr'].min()),correlation_max=float(a['pmra_pmdec_corr'].max())),
       convention=dict(coordinates='ICRS RA,DEC in degrees, reference epoch J2016.0 (TCB)',proper_motion='east=pmra=mu_alpha*cos(delta); north=pmdec=mu_delta',units='microarcseconds/year',
            coefficient_order=LABELS,STF_basis=S.tolist(),normalization='Cartesian dipole and Frobenius-orthonormal STF matrix coordinates; not normalized scalar-Ylm coefficients/powers'),
       all=fit,frame_subset=dict(spin_used_sources=int(fs.sum()),orientation_used_sources=int(fo.sum()),frame_table_rows=len(frame),
            spin_used=solve(combine(spinparts)),not_spin_used=solve(combine(notspinparts)),
            independence='Not independent: common attitude/calibration and source/frame selection; Gaia DR3 and EDR3 astrometry are identical observations'),
       spatial_sensitivity=dict(partition='12 equal-area cells: 4 RA quadrants x 3 equal sin(dec) bins',
            method='Whole-source angular holdout; no splitting pm components or resampling duplicated observations',heldout=heldout,
            deletion_min_uasyr=deleted.min(axis=0).tolist(),deletion_max_uasyr=deleted.max(axis=0).tolist(),
            cluster_score_sigma_uasyr=np.sqrt(np.diag(sand)).tolist(),
            caveat='Coarse partition sensitivity only; not a fitted spatial correlation kernel, independent null simulation, or coverage guarantee'),
       radio_crosswalk=crosswalk(tab,mnames),radio=radio_sensitivity(),
       ceilings=['No cosmic curl or matter vorticity inference','No native Bianchi transfer or family identification','No p-value, posterior odds, independent Gaia/radio validation or physical K03 admission'],
       reused_not_rerun=['docs/observational_reboot_20261014/results/gaia_frame_v1/result.json (4756 spin-selected EDR3 sources)',
          'docs/solver_free_research_20261014/results/gaia_correlation/result.json (4756-row declared-kernel sensitivity)'])
    (HERE/'RESULTS.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    # Sufficient statistics are derived, compact, and contain no source rows.
    np.savez(HERE/'sufficient_statistics.npz',normal=N,rhs=h,cell_normal=np.stack([p[0] for p in parts]),cell_rhs=np.stack([p[1] for p in parts]),cell_ywy=np.array([p[2] for p in parts]),cell_n=np.array([p[3] for p in parts]))
    print(json.dumps(dict(completeness=result['completeness'],retention=result['retention'],radio_crosswalk=result['radio_crosswalk'],coefficients_uasyr=fit['coefficient_uasyr'])),flush=True)

if __name__=='__main__':main()
