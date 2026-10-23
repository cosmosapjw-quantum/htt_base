"""A22-08 secondary discrete QU windows; same observed sky, no null inference."""
from pathlib import Path
import hashlib
import importlib.util
import json
import sys

import healpy as hp
import numpy as np

HERE=Path(__file__).resolve().parent
s=importlib.util.spec_from_file_location('a22_morphology',HERE.parent/'cmb_counterpairs/morphology.py')
m=importlib.util.module_from_spec(s);sys.modules[s.name]=m;s.loader.exec_module(m)
OUT=Path('/mnt/extdrive/workdir/htt_open_data/a22_20261023/cmb_pilot')


def windows():
    pix=np.arange(hp.nside2npix(64));lon,lat=hp.pix2ang(64,pix,lonlat=True,nest=False)
    rings=hp.pix2ring(64,pix,nest=False).astype(np.int64)
    distance=abs(128-rings);polar=(rings<64)|(rings>192)
    maps={0:np.ones(len(pix)),
          20:(polar|(2*distance>192*np.sin(np.deg2rad(20)))).astype(float),
          30:(polar|(4*distance>192)).astype(float)}
    if (int(maps[20].sum()),int(maps[30].sum()))!=(32512,24320):raise ValueError('exact ring-window support')
    antipode=hp.ang2pix(64,(lon+180)%360,-lat,lonlat=True,nest=False)
    for w in maps.values():
        if not np.isin(w,[0,1]).all() or not np.array_equal(w,w[antipode]):raise ValueError('nonbinary/nonantipodal window')
    if np.any(maps[30]>maps[20]):raise ValueError('nonnested geometric windows')
    return maps


def repack(a,old,new,low=0):
    result=np.zeros(hp.Alm.getsize(new),complex)
    for l in range(low,min(old,new)+1):
        for k in range(l+1):result[hp.Alm.getidx(new,l,k)]=a[hp.Alm.getidx(old,l,k)]
    return result


def checked_pair(e,b,lmax):
    for a in (e,b):
        if a.shape!=(hp.Alm.getsize(lmax),) or not np.isfinite(a).all():raise ValueError('both packed E/B arrays required')
        if max(abs(a[hp.Alm.getidx(lmax,l,0)].imag) for l in range(lmax+1))>1e-12*max(float(np.linalg.norm(a)),1e-300):raise ValueError('m0 reality')
        if any(a[hp.Alm.getidx(lmax,l,k)]!=0 for l in (0,1) for k in range(l+1)):raise ValueError('spin2 undefined monopole/dipole')


def transform(e,b,lmax,window):
    checked_pair(e,b,lmax)
    maps=hp.alm2map_spin([e,b],64,2,lmax=lmax,mmax=lmax)
    alms=hp.map2alm_spin([maps[0]*window,maps[1]*window],2,lmax=4,mmax=4)
    if not np.isfinite(alms).all():raise ArithmeticError('nonfinite discrete transform')
    return np.array(alms)


def parity(a,lmax,magnetic=False):
    out=a.copy()
    for l in range(lmax+1):
        for k in range(l+1):out[hp.Alm.getidx(lmax,l,k)]*=(-1)**(l+int(magnetic))
    return out


def dense(a):
    result={}
    for l in (2,3,4):
        for k in range(l+1):
            value=complex(a[hp.Alm.getidx(4,l,k)]);result[l,k]=value
            if k:result[l,-k]=(-1)**k*value.conjugate()
    return result


def normalized_residual(error,*operands):
    denominator=sum(float(np.linalg.norm(a)) for a in operands)
    if denominator<=0:raise ValueError('nonzero arithmetic reference needed')
    return float(np.linalg.norm(error)/denominator)


def main():
    cfg=HERE/'EXPERIMENT.json';ex=json.loads(cfg.read_text());source=m.HERE/'EXPERIMENT.json'
    if m.digest(source)!=ex['source_experiment_sha256']:raise ValueError('source experiment drift')
    inputs=json.loads(source.read_text())['products'];win=windows();rows=[];outputs={};pairs={};controls=[]
    for limit in (32,64,128):m.validate_link([r for r in inputs if r['lmax']==limit])
    for entry in inputs:
        p=Path(entry['payload_path']);meta=Path(entry['metadata_path']);limit=entry['lmax'];name=entry['product']
        if m.digest(p)!=entry['payload_sha256'] or m.digest(meta)!=entry['metadata_sha256']:raise ValueError('input drift')
        live=json.loads(meta.read_text())
        if live['contract']!=entry['contract']:raise ValueError('processing metadata drift')
        with np.load(p,allow_pickle=False) as f:
            if set(f.files)!={'E','B'}:raise ValueError('processed schema')
            e,b=np.array(f['E']),np.array(f['B'])
        checked_pair(e,b,limit);pairs[name,limit]=(e,b)
        for w in (0,20,30):
            transformed=transform(e,b,limit,win[w]);outputs[name,limit,w]=transformed
            feat=m.features(dense(transformed[0]));rows.append(dict(product=name,lmax=limit,secondary_window_degrees=w,features=feat))
            eo=transform(e,b*0,limit,win[w]);bo=transform(e*0,b,limit,win[w])
            res=normalized_residual(transformed-eo-bo,transformed,eo,bo,e,b)
            par=transform(parity(e,limit),parity(b,limit,True),limit,win[w])
            expected=np.array([parity(transformed[0],4),parity(transformed[1],4,True)])
            pres=normalized_residual(par-expected,transformed,e,b)
            if max(res,pres)>1e-10:raise ArithmeticError('linear/physical parity control failed')
            if w==0:roundtrip=normalized_residual(transformed-np.array([repack(e,limit,4),repack(b,limit,4)]),e,b)
            else:roundtrip=None
            controls.append(dict(product=name,lmax=limit,window=w,EB_decomposition_residual=res,
                                 physical_parity_residual=pres,no_window_roundtrip_defect=roundtrip,
                                 B_input_to_E_low_norm_K_CMB=float(np.linalg.norm(bo[0]))))
    bands=[]
    for name in m.PRODUCTS:
        for lo,hi in ((32,64),(64,128)):
            e,b=pairs[name,hi];el,bl=pairs[name,lo]
            added_e=e-repack(el,lo,hi);added_b=b-repack(bl,lo,hi)
            for w in (20,30):
                delta=outputs[name,hi,w]-outputs[name,lo,w]
                direct=transform(added_e,added_b,hi,win[w])
                no_window=transform(added_e,added_b,hi,win[0])
                residual=normalized_residual(delta-direct,outputs[name,hi,w],outputs[name,lo,w],e,b)
                if residual>1e-10:raise ArithmeticError('band-extension repacking/linearity failed')
                bands.append(dict(product=name,low=lo,high=hi,window=w,closure_residual=residual,
                                  added_output_norm_K_CMB=float(np.linalg.norm(direct)),
                                  added_window_excess_norm_K_CMB=float(np.linalg.norm(direct-no_window))))
    selected=[r for r in rows if r['secondary_window_degrees'] in (20,30)]
    joint=m.joint_score([r['features'] for r in selected])
    maxima={}
    for feature,absolute in (('J234',True),('alignment23_squared',False)):
        if any(r['features'][feature] is None for r in selected):maxima[feature]=None;continue
        winner=max(selected,key=lambda r:abs(r['features'][feature]) if absolute else r['features'][feature])
        maxima[feature]=dict(value=winner['features'][feature],product=winner['product'],lmax=winner['lmax'],window=winner['secondary_window_degrees'])
    OUT.mkdir(parents=True,exist_ok=True)
    payload=OUT/'secondary_window_alms.npz'
    np.savez_compressed(payload,**{f'{name}_L{l}_w{w}':a for (name,l,w),a in outputs.items()})
    result=dict(owner='obsstat',claim_tier=ex['claim_tier'],transfer_source='none',experiment_sha256=m.digest(cfg),code_sha256=m.digest(Path(__file__)),
                raw_processed_output=dict(path=str(payload),sha256=m.digest(payload),bytes=payload.stat().st_size),
                window_pixels={str(w):int(mask.sum()) for w,mask in win.items()},
                rows=rows,controls=controls,band_extensions=bands,joint_descriptive_score=joint,separate_maxima=maxima,
                independent_observed_skies=1,p_value=None,physical_null_status='HOLD',
                scope='Discrete secondary-window response of already processed bandlimited QU; no physical sky-cut/null coverage')
    (HERE/'RESULT.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    import matplotlib
    matplotlib.use('Agg')
    from matplotlib import pyplot as plt
    fig,ax=plt.subplots(1,2,figsize=(11,4))
    for w in (0,20,30):
        for l in (32,128):
            rr=[r for r in rows if r['secondary_window_degrees']==w and r['lmax']==l]
            for a,k in zip(ax,['J234','alignment23_squared']):a.plot(m.PRODUCTS,[r['features'][k] for r in rr],marker='o' if l==32 else 'x',label=(f'W=1, L{l}' if w==0 else f'|b|>{w}, L{l}'))
    ax[0].set_ylabel('signed J234');ax[1].set_ylabel('largest-axis alignment squared');ax[1].set_ylim(0,1)
    for a in ax:a.legend(fontsize=6);a.tick_params(axis='x',rotation=20)
    fig.suptitle('Secondary RING64 QU windows on one processed PR3 sky; physical null HOLD');fig.tight_layout()
    for ext in ('png','pdf'):fig.savefig(HERE/f'OPERATOR.{ext}',dpi=160)
    plt.close(fig)
    print(json.dumps(dict(joint=joint,maxima=maxima,max_band_closure=max(r['closure_residual'] for r in bands))))


if __name__=='__main__':main()
