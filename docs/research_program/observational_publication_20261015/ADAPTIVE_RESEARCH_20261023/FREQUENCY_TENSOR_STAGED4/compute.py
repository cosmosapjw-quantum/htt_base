#!/usr/bin/env python3
"""Bounded R25 four-frequency native spin-2 pseudo-tensor consumer."""
from __future__ import annotations
import hashlib, json, math, os, pathlib, resource, sys, time, traceback
from dataclasses import dataclass
import numpy as np
import healpy as hp
from astropy.io import fits

ROOT = pathlib.Path('/home/cosmosapjw/Dropbox/bianchi/htt_base')
OUT = pathlib.Path(__file__).resolve().parent
BASE = ROOT / 'docs/research_program/observational_publication_20261015'
NEW = BASE / 'ADAPTIVE_RESEARCH_20261023'
CONTRACT = NEW / 'R25-PR3-STAGED4-TENSOR-CONTRAST_INPUT.json'
ACK = pathlib.Path('/mnt/extdrive/workdir/htt_open_data/r25_root_space_recovery/receipts/STAGED4_ACTUAL_ACK.json')
PACKET = '58a4f9a76a227a91229b71a44a02044ca3d8978a1e12b2996e6fd19f734c5d9a'
INPUT_SHA = 'ff5db155e8266b4a913ceb48e69b60d6a6356928940305cd2d28d82fc3f690e5'
BANDS = (30,44,70,100)
CAP_S = 900.0
CAP_RSS = 4294967296
SQ2 = math.sqrt(2)


def sha(path):
    h=hashlib.sha256()
    with open(path,'rb') as f:
        for x in iter(lambda:f.read(8*1024*1024),b''): h.update(x)
    return h.hexdigest()


def atomic_json(path, value):
    tmp=path.with_suffix(path.suffix+'.tmp')
    tmp.write_text(json.dumps(value,indent=2,sort_keys=True,allow_nan=False)+'\n')
    os.replace(tmp,path)


def rss():
    with open('/proc/self/status') as f:
        for line in f:
            if line.startswith('VmRSS:'): return int(line.split()[1])*1024
    return 0


@dataclass
class Clock:
    band: int
    charged: float=0.
    started: float|None=None
    peak_rss: int=0
    def begin(self):
        assert self.started is None
        self.started=time.monotonic()
        self.check()
    def check(self):
        self.peak_rss=max(self.peak_rss,rss())
        elapsed=self.charged+(time.monotonic()-self.started if self.started is not None else 0.)
        if self.peak_rss > CAP_RSS: raise RuntimeError(f'RSS_CAP_EXCEEDED band={self.band} rss={self.peak_rss}')
        if elapsed > CAP_S: raise RuntimeError(f'TIME_CAP_EXCEEDED band={self.band} charged={elapsed}')
    def pause(self):
        self.check()
        self.charged += time.monotonic()-self.started
        self.started=None
    def record(self): return {'charged_seconds':self.charged+(time.monotonic()-self.started if self.started else 0.),'peak_rss_bytes':self.peak_rss,'cap_seconds':CAP_S,'cap_rss_bytes':CAP_RSS}


def expected_raw(product):
    return {'path':pathlib.Path(product['path']),'nside':int(product['native_nside']),'sha256':product['sha256'],'size':product['size_bytes'],'band':product['band_GHz']}


def fits_meta(product):
    info=expected_raw(product); p=info['path']; band=info['band']; nside=info['nside']
    if not p.is_file() or p.stat().st_size != info['size']: raise RuntimeError(f'PRODUCT_SIZE_OR_PRESENCE band={band}')
    actual_sha=sha(p)
    if actual_sha != info['sha256']: raise RuntimeError(f'PRODUCT_SHA band={band} actual={actual_sha}')
    for key in ('receipt','header_metadata'):
        aux=product[key]
        if sha(aux['path']) != aux['sha256']: raise RuntimeError(f'{key.upper()}_SHA band={band}')
    with fits.open(p,memmap=True,lazy_load_hdus=True) as hdul:
        h=hdul[1].header
        assert h['XTENSION']=='BINTABLE' and h['NAXIS2']==12*nside*nside
        assert h['NAXIS1']==40 and h['TFIELDS']==10
        assert h['TTYPE2'].strip()=='Q_STOKES' and h['TTYPE3'].strip()=='U_STOKES'
        assert h['TFORM2'].strip()=='E' and h['TFORM3'].strip()=='E'
        assert h['NSIDE']==nside and h['ORDERING'].strip()=='NESTED'
        assert h['COORDSYS'].strip()=='GALACTIC'
        polkey='POLCCONV' if band==100 else 'POLCONV'
        assert h[polkey].strip()=='COSMO'
        unit=h['TUNIT2'].strip()
        assert unit in ('K_CMB','Kcmb') and h['TUNIT3'].strip()==unit
        if 'FILENAME' in h: assert h['FILENAME'].strip()==p.name
        assert str(h['FREQ']).strip()==str(band)
        sentinel=np.float32(h['BAD_DATA'])
        offset=hdul[1]._data_offset
        hist=[str(x) for x in h.get('HISTORY',[]) ]
    return {'band_GHz':band,'path':str(p),'sha256':actual_sha,'size_bytes':info['size'],
            'qualification':'QUALIFIED_FOR_STAGED4','nside':nside,'ordering':'NESTED','coordsys':'GALACTIC',
            'polarization_keyword':polkey,'polarization_value':'COSMO','unit_raw':unit,'unit_normalized':'K_CMB',
            'bad_data_header':float(h['BAD_DATA']),'bad_data_native_float32':float(sentinel),
            'data_offset_bytes':offset,'row_bytes':40,'history_cards':hist,'source_url':product['source_url']}


def raw_views(meta):
    dt=np.dtype({'names':['Q','U'],'formats':['>f4','>f4'],'offsets':[4,8],'itemsize':40})
    mm=np.memmap(meta['path'],dtype=dt,mode='r',offset=meta['data_offset_bytes'],shape=(12*meta['nside']**2,))
    return mm,mm['Q'],mm['U']


def support_for_product(meta,clock,selected_nest64):
    nside=meta['nside']; child=(nside//64)**2; np64=12*64**2
    valid64=np.ones(np64,dtype=bool)
    reasons={'Q_nonfinite':0,'U_nonfinite':0,'Q_sentinel':0,'U_sentinel':0,'invalid_native_pixel_union':0,'invalid_parent_cells':0}
    mm,q,u=raw_views(meta); sentinel=np.float32(meta['bad_data_native_float32'])
    try:
        for lo in range(0,np64,512):
            hi=min(lo+512,np64); start=lo*child; stop=hi*child
            qv=np.asarray(q[start:stop],dtype=np.float32); uv=np.asarray(u[start:stop],dtype=np.float32)
            qf=np.isfinite(qv); uf=np.isfinite(uv); qs=qv==sentinel; us=uv==sentinel
            ok=qf & uf & ~qs & ~us
            valid64[lo:hi]=ok.reshape(hi-lo,child).all(axis=1)
            reasons['Q_nonfinite']+=int((~qf).sum());reasons['U_nonfinite']+=int((~uf).sum())
            reasons['Q_sentinel']+=int(qs.sum());reasons['U_sentinel']+=int(us.sum())
            reasons['invalid_native_pixel_union']+=int((~ok).sum())
            clock.check()
    finally:
        del mm,q,u
    reasons['invalid_parent_cells']=int((~valid64).sum())
    reasons['selected_parent_cells_invalid']=int((selected_nest64 & ~valid64).sum())
    return valid64,reasons


def d_terms(l,mp,m):
    fac=math.factorial; pref=math.sqrt(fac(l+mp)*fac(l-mp)*fac(l+m)*fac(l-m))
    out=[]
    for k in range(max(0,m-mp),min(l+m,l-mp)+1):
        den=fac(l+m-k)*fac(k)*fac(mp-m+k)*fac(l-mp-k)
        out.append(((-1)**(k-mp+m)*pref/den,2*l+m-mp-2*k,mp-m+2*k))
    return out


def spin_y(l,m,s,ct,st,phase):
    d=np.zeros_like(ct)
    for coef,a,b in d_terms(l,m,-s): d += coef * ct**a * st**b
    return math.sqrt((2*l+1)/(4*math.pi))*d*phase


def low_sum(q,u,nside,chunk=262144):
    """Independent finite Wigner-d quadrature, no healpy transform or downgraded Q/U."""
    plus=np.zeros((4,4),complex);minus=np.zeros((4,4),complex)
    altp=np.zeros((4,4),complex);altm=np.zeros((4,4),complex)
    area=4*math.pi/len(q)
    n=len(q)
    for lo in range(0,n,chunk):
        hi=min(lo+chunk,n)
        loc=np.flatnonzero((q[lo:hi]!=0)|(u[lo:hi]!=0))
        if len(loc)==0: continue
        idx=loc+lo
        theta,phi=hp.pix2ang(nside,idx,nest=False)
        ct=np.cos(theta/2);st=np.sin(theta/2)
        qq=q[idx];uu=u[idx]; zp=qq+1j*uu;zm=qq-1j*uu
        for l in (2,3):
            for m in range(l+1):
                phase=np.exp(1j*m*phi)
                yp=spin_y(l,m,2,ct,st,phase)
                ym=spin_y(l,m,-2,ct,st,phase)
                vp=zp*np.conj(yp);vm=zm*np.conj(ym)
                plus[l,m]+=area*np.sum(vp);minus[l,m]+=area*np.sum(vm)
                half=len(vp)//2
                altp[l,m]+=area*(np.sum(vp[:half])+np.sum(vp[half:]))
                altm[l,m]+=area*(np.sum(vm[:half])+np.sum(vm[half:]))
    E=-(plus+minus)/2; B=1j*(plus-minus)/2
    Ealt=-(altp+altm)/2;Balt=1j*(altp-altm)/2
    return E,B,Ealt,Balt


def canonical(e,b):
    parts=[]
    for alm in (e,b):
        for l in (2,3):
            parts.append(float(alm[hp.Alm.getidx(3,l,0)].real))
            for m in range(1,l+1):
                z=alm[hp.Alm.getidx(3,l,m)]
                parts.extend((SQ2*float(z.real),-SQ2*float(z.imag)))
    return np.asarray(parts,dtype=np.float64)


def canonical_grid(e,b):
    out=[]
    for a in (e,b):
        for l in (2,3):
            out.append(float(a[l,0].real))
            for m in range(1,l+1): out.extend((SQ2*float(a[l,m].real),-SQ2*float(a[l,m].imag)))
    return np.asarray(out)


def decode(c):
    sys.path.insert(0,str(ROOT/'htt'))
    sys.path.insert(0,str(ROOT/'htt/src'))
    from obsstat.planck_lowell_irrep_projection import real_harmonic_l2_to_stf,real_harmonic_l3_to_stf
    arrays=[]
    for start,l in ((0,2),(5,3),(12,2),(17,3)):
        x=c[start:start+2*l+1].copy()
        x[1::2]/=SQ2;x[2::2]/=-SQ2
        arrays.append(real_harmonic_l2_to_stf(x) if l==2 else real_harmonic_l3_to_stf(x))
    return arrays


def project_product(meta,s4nest,clock):
    nside=meta['nside'];n=12*nside*nside;child=(nside//64)**2
    qring=np.zeros(n,dtype=np.float64);uring=np.zeros(n,dtype=np.float64)
    mm,q,u=raw_views(meta);sentinel=np.float32(meta['bad_data_native_float32'])
    try:
        for lo in range(0,n,1048576):
            hi=min(lo+1048576,n)
            nested=np.arange(lo,hi,dtype=np.int64)
            ring=hp.nest2ring(nside,nested)
            selected=s4nest[nested//child]
            qv=np.asarray(q[lo:hi],dtype=np.float32);uv=np.asarray(u[lo:hi],dtype=np.float32)
            valid=selected & np.isfinite(qv) & np.isfinite(uv) & (qv!=sentinel) & (uv!=sentinel)
            if np.any(selected & ~valid): raise RuntimeError(f'S4_NATIVE_INVALID band={meta["band_GHz"]}')
            qring[ring]=np.where(valid,qv,0).astype(np.float64)
            uring[ring]=np.where(valid,uv,0).astype(np.float64)
            clock.check()
    finally: del mm,q,u
    # Original native pixelization, no smoothing, downgrade or response inversion.
    ae,ab=hp.map2alm_spin([qring,uring],spin=2,lmax=3,mmax=3)
    clock.check()
    c=canonical(ae,ab)
    ie,ib,iae,iab=low_sum(qring,uring,nside)
    clock.check()
    independent=canonical_grid(ie,ib); alt=canonical_grid(iae,iab)
    err=np.abs(c-independent)
    tol=1e-12+1e-9*np.abs(c)
    if not np.all(err<=tol): raise RuntimeError(f'NATIVE_INDEPENDENT_SPIN_SUM band={meta["band_GHz"]} max={float(err.max())} index={int(np.argmax(err))}')
    if not np.all(np.abs(independent-alt)<=tol): raise RuntimeError(f'REDUCTION_ORDER band={meta["band_GHz"]}')
    # Exact permutation and where-zeroing controls on the actual support.
    sample=np.arange(0,n,max(1,n//5000),dtype=np.int64)
    ns=hp.ring2nest(nside,sample)
    if not np.array_equal(hp.nest2ring(nside,ns),sample): raise RuntimeError('RING_NEST_PERMUTATION')
    if not np.all(qring[sample][~s4nest[ns//child]]==0) or not np.all(uring[sample][~s4nest[ns//child]]==0):
        raise RuntimeError('MASK_APPLICATION')
    # Linearity of the fixed-mask transform on actual field.
    half_e,half_b=hp.map2alm_spin([qring*0.5,uring*0.5],spin=2,lmax=3,mmax=3)
    lc=canonical(half_e,half_b)
    linerr=float(np.max(np.abs(c-2*lc)))
    if linerr>1e-12+1e-9*float(np.max(np.abs(c))): raise RuntimeError('LINEARITY')
    stf=decode(c)
    for x in stf:
        if not np.allclose(x,x.swapaxes(0,1),rtol=0,atol=1e-14): raise RuntimeError('STF_SYMMETRY')
        if x.ndim==2 and abs(np.trace(x))>1e-14: raise RuntimeError('STF_TRACE2')
        if x.ndim==3 and np.max(np.abs(np.trace(x,axis1=0,axis2=1)))>1e-14:raise RuntimeError('STF_TRACE3')
    return c,stf,{'independent_max_abs_K_CMB':float(err.max()),'reduction_max_abs_K_CMB':float(np.max(np.abs(independent-alt))),
                 'linearity_max_abs_K_CMB':linerr,'native_npix':n,'nonzero_ring_pixels':int(np.count_nonzero((qring!=0)|(uring!=0)))}


def run():
    if os.environ.get('OMP_NUM_THREADS')!='1' or os.environ.get('OPENBLAS_NUM_THREADS')!='1': raise RuntimeError('THREAD_ENV_NOT_ONE')
    if sha(CONTRACT)!=INPUT_SHA: raise RuntimeError('INPUT_SHA')
    ack=json.loads(ACK.read_text())
    if ack['status']!='ACTUAL_NATIVE_LAUNCH_ACKNOWLEDGED' or ack['packet_id']!=PACKET or ack['agent_id']!='/root/rc_58a4f9a76a227a91': raise RuntimeError('ACTUAL_ACK_BINDING')
    cfg=json.loads(CONTRACT.read_text())
    support_cfg=cfg['support']['base'];support_path=ROOT/support_cfg['path']
    if sha(support_path)!=support_cfg['sha256']: raise RuntimeError('BASE_SUPPORT_SHA')
    with np.load(support_path) as z: selected=np.asarray(z[support_cfg['key']],dtype=bool)
    assert selected.shape==(49152,) and int(selected.sum())==30021
    nest64=hp.nest2ring(64,np.arange(49152,dtype=np.int64))
    selected_nest=selected[nest64]
    clocks={b:Clock(b) for b in BANDS}; decisions=[]; valids=[]
    prior=json.loads((OUT/'RAW_RECEIPT.json').read_text()) if (OUT/'RAW_RECEIPT.json').exists() else None
    if prior is not None:
        if prior.get('packet_id')!=PACKET or prior.get('input_identity')!='sha256:'+INPUT_SHA: raise RuntimeError('PRIOR_RECEIPT_IDENTITY')
        for band,rec in prior.get('product_accounting',{}).items():
            clocks[int(band)].charged=float(rec['charged_seconds']);clocks[int(band)].peak_rss=int(rec['peak_rss_bytes'])
    raw={'schema':'htt.staged4_raw_receipt/1','packet_id':PACKET,'task_id':cfg['task_id'],'input_identity':'sha256:'+INPUT_SHA,
         'agent_id':'/root/rc_58a4f9a76a227a91','requested_model_effort':'gpt-6-sol/high','observed_runtime':'UNKNOWN',
         'ack_path':str(ACK),'ack_sha256':sha(ACK),'started_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),
         'product_accounting':prior.get('product_accounting',{}) if prior else {},'first_failures':prior.get('first_failures',[]) if prior else [],'stage_status':'IN_PROGRESS'}
    atomic_json(OUT/'RAW_RECEIPT.json',raw)
    try:
        if (OUT/'PRODUCT_QUALIFICATION_DECISIONS.json').exists() and (OUT/'COMMON_SUPPORT_S4.npz').exists():
            saved=json.loads((OUT/'PRODUCT_QUALIFICATION_DECISIONS.json').read_text())
            decisions=saved['decisions']
            if [d['band_GHz'] for d in decisions]!=list(BANDS): raise RuntimeError('SAVED_QUALIFICATION_BAND_IDENTITY')
            with np.load(OUT/'COMMON_SUPPORT_S4.npz') as z:
                s4ring=np.asarray(z['s4_mask_ring64'],dtype=bool)
                valids=[np.asarray(z[f'valid_{b}_nest64'],dtype=bool) for b in BANDS]
            if int(s4ring.sum())!=saved['s4_count']: raise RuntimeError('SAVED_SUPPORT_COUNT')
            s4nest=s4ring[nest64]
            support_sha=sha(OUT/'COMMON_SUPPORT_S4.npz')
            if support_sha!=saved['common_support_s4_sha256']: raise RuntimeError('SAVED_SUPPORT_SHA')
        else:
            for product in cfg['input_products']:
                b=product['band_GHz'];clock=clocks[b];clock.begin()
                meta=fits_meta(product)
                valid,reasons=support_for_product(meta,clock,selected_nest)
                clock.pause();meta['validity_reasons']=reasons;meta['valid_parent_count']=int(valid.sum());decisions.append(meta);valids.append(valid)
                raw['product_accounting'][str(b)]=clock.record();atomic_json(OUT/'RAW_RECEIPT.json',raw)
            shared_start=time.monotonic()
            s4nest=selected_nest.copy()
            for x in valids:s4nest &= x
            s4ring=np.zeros(49152,dtype=bool);s4ring[nest64]=s4nest
            if not np.any(s4nest):raise RuntimeError('EMPTY_S4_SUPPORT')
            support_removed=np.flatnonzero(selected & ~s4ring);support_retained=np.flatnonzero(s4ring)
            np.savez_compressed(OUT/'COMMON_SUPPORT_S4.npz',selected_mask_ring64=selected,s4_mask_ring64=s4ring,
                retained_ring64=support_retained,removed_ring64=support_removed,
                valid_30_nest64=valids[0],valid_44_nest64=valids[1],valid_70_nest64=valids[2],valid_100_nest64=valids[3])
            support_sha=sha(OUT/'COMMON_SUPPORT_S4.npz')
            atomic_json(OUT/'PRODUCT_QUALIFICATION_DECISIONS.json',{'decisions':decisions,'all_four':'QUALIFIED_FOR_STAGED4',
                'common_support_s4_sha256':support_sha,'selected_count':int(selected.sum()),'s4_count':int(s4ring.sum()),
                'retained_ring64':support_retained.tolist(),'removed_ring64':support_removed.tolist()})
            shared_elapsed=time.monotonic()-shared_start
            for clock in clocks.values():
                clock.charged+=shared_elapsed/4;clock.check()
        carriers=[];stfs=[];controls={}
        for meta in decisions:
            b=meta['band_GHz'];clock=clocks[b];clock.begin()
            c,t,ctl=project_product(meta,s4nest,clock)
            carriers.append(c);stfs.append(t);controls[str(b)]=ctl
            np.savez_compressed(OUT/f'PARTIAL_{b}.npz',canonical24=c,E2=t[0],E3=t[1],B2=t[2],B3=t[3])
            clock.pause();raw['product_accounting'][str(b)]=clock.record();atomic_json(OUT/'RAW_RECEIPT.json',raw)
        shared_start=time.monotonic()
        carriers=np.stack(carriers);pair_idx=np.asarray([(0,1),(0,2),(0,3),(1,2),(1,3),(2,3)],dtype=np.int64)
        contrasts=carriers[pair_idx[:,0]]-carriers[pair_idx[:,1]]
        pair_stfs=[[decode(x) for x in contrasts][j] for j in range(6)]
        Q=np.sqrt(np.sum((carriers/1e-5)**2,axis=1))
        np.savez_compressed(OUT/'FULL_CARRIER_AND_CONTRASTS.npz',bands_GHz=np.asarray(BANDS),carrier_canonical_96=carriers,
            pair_bands_GHz=np.asarray([(BANDS[i],BANDS[j]) for i,j in pair_idx]),pair_contrasts_canonical_6x24=contrasts,
            E2_stf=np.stack([t[0] for t in stfs]),E3_stf=np.stack([t[1] for t in stfs]),B2_stf=np.stack([t[2] for t in stfs]),B3_stf=np.stack([t[3] for t in stfs]),
            pair_E2_stf=np.stack([t[0] for t in pair_stfs]),pair_E3_stf=np.stack([t[1] for t in pair_stfs]),
            pair_B2_stf=np.stack([t[2] for t in pair_stfs]),pair_B3_stf=np.stack([t[3] for t in pair_stfs]),Q_computational=Q)
        result={'schema':'htt.staged4_tensor_result/1','task_id':cfg['task_id'],'packet_id':PACKET,'input_identity':'sha256:'+INPUT_SHA,
            'support_name':'S4','support_count':int(s4ring.sum()),'original_selected_count':int(selected.sum()),
            'bands_GHz':list(BANDS),'carrier_shape':list(carriers.shape),'pair_contrasts_shape':list(contrasts.shape),
            'canonical_coordinates':'a_l0,sqrt(2)Re(a_lm),-sqrt(2)Im(a_lm); E2,E3,B2,B3',
            'Q_computational':dict(zip(map(str,BANDS),map(float,Q))),'Q_denominators_K_CMB':{'ell2':1e-5,'ell3':1e-5},
            'F_frequency_empirical':{'measure':'four frequencies, mass 1/4 each','ordered_thresholds':sorted(map(float,Q)),
                  'cdf_rule':'F(t)=count(Q_nu<=t)/4','interpretation':'descriptive computational frequency occupancy'},
            'Pi':'NOT_CALIBRATED','physical_F':'NOT_EVALUABLE','physical_MES':'NOT_EVALUABLE','G_F':'NOT_APPLICABLE: frequency is not depth',
            'joint_covariance_or_law':'NOT_CALIBRATED','claim_ceiling':cfg['claim_ceiling'],
            'controls':controls,'product_accounting':{str(b):clocks[b].record() for b in BANDS},
            'independent_review':'REQUIRED','scientific_admission':'HOLD'}
        atomic_json(OUT/'RESULT.json',result)
        (OUT/'REPORT.md').write_text('# R25 staged four-frequency native pseudo-tensors\n\n'+
            'Four delivered Galactic COSMO maps are projected at their native NSIDE on the common validity-only S4 support. '+
            'The result retains all 96 E2/E3/B2/B3 canonical coordinates, complete STF tensors, and six oriented 24-coordinate contrasts. '+
            'See RESULT.json and FULL_CARRIER_AND_CONTRASTS.npz for exact values and controls.\n\n'+
            'These are descriptive pseudo-modes with delivered beam, mapmaking, pixelization, common mask, leakage and instrumental differences. '+
            'The four-point frequency CDF is computational only. Physical MES/F are NOT_EVALUABLE; Pi is NOT_CALIBRATED. '+
            'Independent review and scientific admission remain pending.\n')
        shared_elapsed=time.monotonic()-shared_start
        for clock in clocks.values():
            clock.charged+=shared_elapsed/4;clock.check()
        raw['stage_status']='CANDIDATE_COMPLETE_REVIEW_REQUIRED';raw['finished_utc']=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())
        raw['product_accounting']={str(b):clocks[b].record() for b in BANDS};atomic_json(OUT/'RAW_RECEIPT.json',raw)
        inventory={p.name:sha(p) for p in sorted(OUT.iterdir()) if p.is_file() and p.name not in ('MANIFEST.json','RETURN.json')}
        manifest={'schema':'htt.staged4_manifest/1','task_id':cfg['task_id'],'packet_id':PACKET,'input_identity':'sha256:'+INPUT_SHA,
                  'source_head':'d93605e66adfececa89b90681124b232a5f90220','files_sha256':inventory,
                  'input_products_sha256':{str(d['band_GHz']):d['sha256'] for d in decisions},
                  'base_support_sha256':support_cfg['sha256'],'decoder_sha256':cfg['carrier']['tensor_decoder']['sha256'],
                  'support_sha256':support_sha,'validation_evidence':{'native_independent':controls,'per_product_accounting':raw['product_accounting']},
                  'claim_tier':'descriptive transfer-conditional','independent_review':'REQUIRED'}
        atomic_json(OUT/'MANIFEST.json',manifest)
        candidate='sha256:'+sha(OUT/'MANIFEST.json')
        ret={'packet_id':PACKET,'task_id':cfg['task_id'],'input_identity':'sha256:'+INPUT_SHA,'candidate_identity':candidate,
             'status':'CANDIDATE_COMPLETE_REVIEW_REQUIRED','proposed_qualified_products':['pr3_frequency_30_44_70_100_native_tensor_staged4'],
             'raw_receipt':str(OUT/'RAW_RECEIPT.json'),'manifest':str(OUT/'MANIFEST.json'),'independent_review':'REQUIRED','scientific_admission':'HOLD'}
        atomic_json(OUT/'RETURN.json',ret)
        print(json.dumps(ret,sort_keys=True),flush=True)
    except Exception as exc:
        raw['stage_status']='HOLD_FIRST_FAILURE';raw['first_failures'].append({'exception':repr(exc),'traceback':traceback.format_exc(),
            'utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())})
        raw['product_accounting']={str(b):clocks[b].record() for b in BANDS}
        atomic_json(OUT/'RAW_RECEIPT.json',raw)
        raise

if __name__=='__main__':run()
