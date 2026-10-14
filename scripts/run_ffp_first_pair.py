#!/usr/bin/env python3
"""Bounded FFP10 first-pair native-pixel formal spin-2 audit.

The delivered frame and polarization convention are unspecified. U+ and U-
are formal HEALPix RING angular-chart/COSMO-tangent-basis scenarios only.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import traceback

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
HEADER_RESULT = ROOT/'docs/observational_reboot_20261014/results/spectra_ffp10_headers_v1/result.json'
OUT_DEFAULT = ROOT/'docs/observational_reboot_20261014/results/spectra_ffp10_first_pair_v1'
RSS_CAP = 6*1024**3
PROFILE_SECONDS = 300
TOTAL_SECONDS = 900
LMAX = MMAX = 16
ELL = np.arange(2, 17)
EXPECTED_HEADER_SHA = '534a399d3ce7e37407720552b5da9dab8520b28480b7eeef13bcd924d304e559'
EXPECTED_NAMES = ('INTENSITY','Q-POLARISATION','U-POLARISATION')
EXPECTED_FORMATS = ('1024E',)*3
EXPECTED_UNITS = ('K_CMB',)*3
PIXELS = 12*2048**2


def digest(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda:f.read(4*1024*1024), b''):
            h.update(block)
    return h.hexdigest()


def code_hash():
    return digest(__file__)


def header_record(path):
    from astropy.io import fits
    with fits.open(path, memmap=True, lazy_load_hdus=True) as h:
        table=h[1]
        keys={key:table.header.get(key,'UNSPECIFIED') for key in
              ('PIXTYPE','ORDERING','NSIDE','COORDSYS','POLCCONV','INDXSCHM','NAXIS1','NAXIS2')}
        cols=[{'name':c.name,'format':c.format,'unit':c.unit} for c in table.columns]
        header_sha=hashlib.sha256(table.header.tostring().encode()).hexdigest()
    record={'path':str(Path(path).resolve()),'size_bytes':Path(path).stat().st_size,
            'header_sha256':header_sha,'keys':keys,'columns':cols}
    if (record['size_bytes']!=603987840 or header_sha!=EXPECTED_HEADER_SHA or
        keys!={'PIXTYPE':'HEALPIX','ORDERING':'RING','NSIDE':2048,
               'COORDSYS':'UNSPECIFIED','POLCCONV':'UNSPECIFIED',
               'INDXSCHM':'IMPLICIT','NAXIS1':12288,'NAXIS2':49152} or
        tuple(c['name'] for c in cols)!=EXPECTED_NAMES or
        tuple(c['format'] for c in cols)!=EXPECTED_FORMATS or
        tuple(c['unit'] for c in cols)!=EXPECTED_UNITS):
        raise ValueError('SOURCE_HEADER_LAYOUT_IDENTITY_MISMATCH')
    return record


def sources(root=ROOT, intake=HEADER_RESULT):
    original=json.loads(Path(intake).read_text())
    if (original.get('scope')!='FFP10_EXPLICIT_QU_HEADER_INTAKE_ONLY'
            or original.get('status')!='HOLD_FRAME_POLCONV_PROCESSING_SOURCE_BRIDGE'
            or len(original.get('headers',[]))!=2):
        raise ValueError('HEADER_INTAKE_CONTRACT_MISMATCH')
    base=Path(root)/'workdir/raw/planck_ffp10/smica'
    paths=(base/'cmb_mc/dx12_v3_smica_cmb_mc_00000_raw.fits',
           base/'noise_mc/dx12_v3_smica_noise_mc_00000_raw.fits')
    result=[]
    for p, prior in zip(paths, original['headers']):
        row=header_record(p)
        if (prior['path']!=str(p) or prior['size_bytes']!=row['size_bytes'] or
                prior['header_sha256']!=row['header_sha256'] or
                prior['keys']!=row['keys'] or prior['columns']!=row['columns']):
            raise ValueError('SOURCE_HEADER_INTAKE_IDENTITY_MISMATCH')
        result.append(row)
    return tuple(paths),result


def load_qu(path):
    """Read exact named packed columns; reject every invalid full-sky pixel."""
    import healpy as hp
    from astropy.io import fits
    header_record(path)
    with fits.open(path,memmap=True) as h:
        table=h[1]
        q=np.asarray(table.data['Q-POLARISATION'], dtype=np.float64).reshape(-1).copy()
        u=np.asarray(table.data['U-POLARISATION'], dtype=np.float64).reshape(-1).copy()
    if q.shape!=(PIXELS,) or u.shape!=(PIXELS,):
        raise ValueError('FULL_SKY_HOLD_PIXEL_COUNT')
    if (not np.isfinite(q).all() or not np.isfinite(u).all() or
            np.any(hp.mask_bad(q)) or np.any(hp.mask_bad(u))):
        raise ValueError('FULL_SKY_HOLD_NONFINITE_OR_UNSEEN')
    return q,u


def spin_alms(q,u,sign):
    import healpy as hp
    if sign not in (1,-1) or q.shape!=u.shape or q.shape!=(PIXELS,):
        raise ValueError('native full-resolution aligned Q/U required')
    ae,ab=hp.map2alm_spin([q,sign*u],spin=2,lmax=LMAX,mmax=MMAX)
    if len(ae)!=153 or len(ab)!=153 or not np.isfinite(ae).all() or not np.isfinite(ab).all():
        raise ValueError('invalid 153 packed spin-2 coefficients')
    return np.asarray(ae),np.asarray(ab)


def manual_cl(alm1,alm2=None,lmax=LMAX):
    """Packed m>=0 complex alm power, m=0 once and m>0 twice."""
    import healpy as hp
    a=np.asarray(alm1)
    b=a if alm2 is None else np.asarray(alm2)
    if a.shape!=(hp.Alm.getsize(lmax,lmax),) or b.shape!=a.shape:
        raise ValueError('packed alm length')
    result=np.zeros(lmax+1)
    for ell in range(lmax+1):
        z=a[hp.Alm.getidx(lmax,ell,0)]*np.conj(b[hp.Alm.getidx(lmax,ell,0)])
        for m in range(1,ell+1):
            i=hp.Alm.getidx(lmax,ell,m)
            z+=2*a[i]*np.conj(b[i])
        result[ell]=z.real/(2*ell+1)
    return result


def spectra(ae,ab):
    import healpy as hp
    ee=hp.alm2cl(ae,lmax=LMAX,mmax=MMAX)
    bb=hp.alm2cl(ab,lmax=LMAX,mmax=MMAX)
    if (not np.allclose(ee,manual_cl(ae),rtol=1e-12,atol=1e-20) or
            not np.allclose(bb,manual_cl(ab),rtol=1e-12,atol=1e-20)):
        raise ArithmeticError('packed-m power and healpy alm2cl disagree')
    return {'EE_K_CMB2':ee[2:], 'BB_K_CMB2':bb[2:]}


def cross_spectra(sa,na):
    import healpy as hp
    return {'EE_K_CMB2':hp.alm2cl(sa[0],na[0],lmax=LMAX,mmax=MMAX)[2:],
            'BB_K_CMB2':hp.alm2cl(sa[1],na[1],lmax=LMAX,mmax=MMAX)[2:]}


def parity_checks(signal,noise,total,signal_spectra,noise_spectra,total_spectra,cross):
    expected=np.r_[signal[0]+noise[0],signal[1]+noise[1]]
    actual=np.r_[total[0],total[1]]
    den=np.linalg.norm(expected); num=np.linalg.norm(actual-expected)
    linearity=0. if den==0 and num==0 else np.inf if den==0 else float(num/den)
    rows={}
    for kind in ('EE_K_CMB2','BB_K_CMB2'):
        s=signal_spectra[kind];n=noise_spectra[kind];t=total_spectra[kind];x=cross[kind]
        residual=t-s-n-2*x
        scale=s+n+2*np.abs(x)
        relative=np.empty_like(scale)
        np.divide(np.abs(residual),scale,out=relative,where=scale!=0)
        relative[scale==0]=np.where(residual[scale==0]==0,0,np.inf)
        rows[kind]={'max_relative_closure':float(np.max(relative)),
                    'zero_denominator_count':int(np.sum(scale==0))}
    status='PASS' if linearity<=1e-9 and all(x['max_relative_closure']<=1e-9 for x in rows.values()) else 'FAIL'
    return {'status':status,'sum_alm_relative_norm':linearity,'spectra':rows,
            'tolerance':1e-9,'zero_denominator_policy':'exact zero residual required'}


def json_write(path,value):
    def cast(x):
        if isinstance(x,np.ndarray):return x.tolist()
        if isinstance(x,np.generic):return x.item()
        raise TypeError(type(x).__name__)
    p=Path(path);temp=p.with_suffix(p.suffix+'.tmp')
    temp.write_text(json.dumps(value,default=cast,indent=2,allow_nan=False)+'\n')
    temp.replace(p)


def save_npz(path,**values):
    p=Path(path);temp=p.with_suffix('.tmp.npz')
    np.savez_compressed(temp,**values)
    temp.replace(p)
    return digest(p)


def read_checkpoint(outdir,signal_source,code):
    p=Path(outdir)/'profile.json';alm=Path(outdir)/'signal_alm.npz'
    if not p.exists() or not alm.exists():return None
    receipt=json.loads(p.read_text())
    if (receipt.get('status')!='PROFILE_PASS' or receipt.get('code_sha256')!=code or
            receipt.get('signal_source')!=signal_source or
            receipt.get('signal_alm_sha256')!=digest(alm)):
        raise ValueError('PROFILE_CHECKPOINT_IDENTITY_MISMATCH')
    return receipt


def profile_worker(root,outdir):
    started=time.monotonic();outdir=Path(outdir);outdir.mkdir(parents=True,exist_ok=True)
    paths,heads=sources(root,Path(root)/HEADER_RESULT.relative_to(ROOT))
    code=code_hash();signal_source=dict(heads[0],full_sha256=digest(paths[0]))
    previous=read_checkpoint(outdir,signal_source,code)
    if previous is not None:return previous
    partial_file=outdir/'signal_partial_plus.npz'
    partial_receipt=outdir/'partial_signal.json'
    alms={}
    if partial_file.exists() or partial_receipt.exists():
        if not partial_file.exists() or not partial_receipt.exists():
            raise ValueError('PARTIAL_SIGNAL_CHECKPOINT_INCOMPLETE')
        partial=json.loads(partial_receipt.read_text())
        if (partial.get('status')!='PARTIAL_SIGNAL_U_PLUS' or
                partial.get('code_sha256')!=code or partial.get('signal_source')!=signal_source
                or partial.get('alm_sha256')!=digest(partial_file)):
            raise ValueError('PARTIAL_SIGNAL_CHECKPOINT_IDENTITY_MISMATCH')
        with np.load(partial_file,allow_pickle=False) as stored:
            alms['E_plus']=stored['E_plus'].copy()
            alms['B_plus']=stored['B_plus'].copy()
    q,u=load_qu(paths[0])
    if not alms:
        ae,ab=spin_alms(q,u,1)
        alms['E_plus']=ae;alms['B_plus']=ab
        partial_sha=save_npz(partial_file,E_plus=ae,B_plus=ab)
        json_write(partial_receipt,{'status':'PARTIAL_SIGNAL_U_PLUS',
                   'code_sha256':code,'signal_source':signal_source,
                   'alm_sha256':partial_sha,'transforms_completed':1})
    ae,ab=spin_alms(q,u,-1)
    alms['E_minus']=ae;alms['B_minus']=ab
    archive_sha=save_npz(outdir/'signal_alm.npz',**alms)
    receipt={'owner':'OBSSTAT','scope':'FFP10_FIRST_PAIR_FORMAL_SPIN2_PROFILE',
             'status':'PROFILE_PASS','code_sha256':code,'signal_source':signal_source,
             'signal_alm_sha256':archive_sha,'transforms':2,
             'lmax':LMAX,'mmax':MMAX,'packed_coefficients_each':153,
             'ell_range':[2,16],'native_unit':'K_CMB',
             'formal_chart':'HEALPIX_RING_COSMO_TANGENT_BASIS',
             'source_frame':'UNSPECIFIED','source_polconv':'UNSPECIFIED',
             'elapsed_seconds':time.monotonic()-started,
             'scientific_admission':'HOLD_FRAME_POLCONV_PROCESSING_SOURCE_BRIDGE',
             'requested_author_runtime':'gpt-6-sol/high',
             'observed_author_runtime':'UNKNOWN'}
    json_write(outdir/'profile.json',receipt)
    return receipt


def make_plot(result,outdir):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig,axs=plt.subplots(2,2,figsize=(12,8),sharex=True)
    for row,label in enumerate(('plus','minus')):
        case=result['signs'][label]
        for col,kind in enumerate(('EE_K_CMB2','BB_K_CMB2')):
            ax=axs[row,col]
            for obj,fmt in (('signal','o-'),('noise','s-'),('sum','^-')):
                ax.plot(ELL,np.asarray(case['spectra'][obj][kind])*1e12,fmt,label=obj,ms=3)
            ax.plot(ELL,2*np.asarray(case['spectra']['cross'][kind])*1e12,'k--',
                    label='signed 2×cross',linewidth=.8)
            ax.axhline(0,color='gray',linewidth=.5)
            ax.set_title(f'U {"+" if label=="plus" else "−"}: {kind[:2]}')
            ax.set_ylabel('C_ell (microK_CMB²)')
            ax.set_xlabel('ell')
            ax.legend(fontsize=7)
    fig.suptitle('FFP10 first pair: formal RING/COSMO tangent-basis spin-2 audit')
    fig.tight_layout()
    for ext in ('png','pdf'):fig.savefig(Path(outdir)/('diagnostic.'+ext),dpi=150)
    plt.close(fig)


def pair_worker(root,outdir):
    started=time.monotonic();outdir=Path(outdir)
    paths,heads=sources(root,Path(root)/HEADER_RESULT.relative_to(ROOT))
    code=code_hash();signal_source=dict(heads[0],full_sha256=digest(paths[0]))
    profile=read_checkpoint(outdir,signal_source,code)
    if profile is None:raise ValueError('PROFILE_FIRST_REQUIRED')
    noise_source=dict(heads[1],full_sha256=digest(paths[1]))
    result_path=outdir/'result.json'
    if result_path.exists():
        old=json.loads(result_path.read_text())
        archive=outdir/'pair_alm.npz'
        if (old.get('code_sha256')==code and old.get('sources')==[signal_source,noise_source]
                and old.get('status')=='FORMAL_OPERATOR_PASS_SOURCE_BRIDGE_HOLD'
                and archive.exists() and old.get('pair_alm_sha256')==digest(archive)
                and all((outdir/name).exists() for name in ('diagnostic.png','diagnostic.pdf','report.md'))):
            return old
        raise ValueError('PAIR_RESULT_IDENTITY_CONFLICT')
    with np.load(outdir/'signal_alm.npz',allow_pickle=False) as stored:
        signal={label:(stored['E_'+label].copy(),stored['B_'+label].copy())
                for label in ('plus','minus')}
    def checkpoint(kind,label):
        archive=outdir/f'{kind}_{label}.npz'
        receipt_file=outdir/f'{kind}_{label}.json'
        if archive.exists() or receipt_file.exists():
            if not archive.exists() or not receipt_file.exists():
                raise ValueError('PAIR_ALM_CHECKPOINT_INCOMPLETE')
            receipt=json.loads(receipt_file.read_text())
            if (receipt.get('status')!='ALM_COMPLETE' or
                    receipt.get('code_sha256')!=code or
                    receipt.get('sources')!=[signal_source,noise_source] or
                    receipt.get('alm_sha256')!=digest(archive)):
                raise ValueError('PAIR_ALM_CHECKPOINT_IDENTITY_MISMATCH')
            with np.load(archive,allow_pickle=False) as stored:
                return stored['E'].copy(),stored['B'].copy()
        return None
    stored={(kind,label):checkpoint(kind,label) for kind in ('noise','sum')
            for label in ('plus','minus')}
    need_maps=any(value is None for value in stored.values())
    if need_maps:
        qsig,usig=load_qu(paths[0]);qnoise,unoise=load_qu(paths[1])
    def complete(kind,label,sign):
        value=stored[(kind,label)]
        if value is not None:return value
        if kind=='noise':value=spin_alms(qnoise,unoise,sign)
        else:value=spin_alms(qsig+qnoise,usig+unoise,sign)
        archive=outdir/f'{kind}_{label}.npz'
        archive_sha=save_npz(archive,E=value[0],B=value[1])
        json_write(outdir/f'{kind}_{label}.json',{'status':'ALM_COMPLETE',
                   'kind':kind,'sign':label,'code_sha256':code,
                   'sources':[signal_source,noise_source],
                   'alm_sha256':archive_sha})
        return value
    pair_alms={};scenarios={}
    for sign,label in ((1,'plus'),(-1,'minus')):
        n=complete('noise',label,sign)
        # The sum transform is computed from explicit native-pixel Q/U addition.
        total=complete('sum',label,sign)
        pair_alms.update({'noise_E_'+label:n[0],'noise_B_'+label:n[1],
                          'sum_E_'+label:total[0],'sum_B_'+label:total[1]})
        s=signal[label]
        sp=spectra(*s);npow=spectra(*n);tpow=spectra(*total);cross=cross_spectra(s,n)
        check=parity_checks(s,n,total,sp,npow,tpow,cross)
        scenarios[label]={'spectra':{'signal':sp,'noise':npow,'sum':tpow,'cross':cross},
                          'closure':check}
    archive_sha=save_npz(outdir/'pair_alm.npz',**pair_alms)
    passed=all(row['closure']['status']=='PASS' for row in scenarios.values())
    result={'owner':'OBSSTAT','scope':'FFP10_FIRST_PAIR_FORMAL_SPIN2_AUDIT',
            'status':'FORMAL_OPERATOR_PASS_SOURCE_BRIDGE_HOLD' if passed else 'FORMAL_OPERATOR_FAIL',
            'claim_tier':'DIAGNOSTIC_ONLY','scientific_admission':'HOLD',
            'transfer_source':'RELEASED_PLANCK_FFP10_RAW_PROCESSING; NO_NATIVE_SOLVER',
            'primary_source':'https://irsa.ipac.caltech.edu/data/Planck/release_3/ancillary-data/',
            'requested_author_runtime':'gpt-6-sol/high',
            'observed_author_runtime':'UNKNOWN',
            'code_sha256':code,'sources':[signal_source,noise_source],
            'profile_sha256':digest(outdir/'profile.json'),
            'signal_alm_sha256':profile['signal_alm_sha256'],'pair_alm_sha256':archive_sha,
            'nside':2048,'ordering':'RING','ell':ELL,'lmax':LMAX,'mmax':MMAX,
            'packed_coefficients_each':153,'native_map_unit':'K_CMB',
            'spectrum_unit':'K_CMB^2','plot_unit':'microK_CMB^2',
            'plot_conversion':1e12,'transforms_total':6,
            'formal_chart':'HEALPIX_RING_COSMO_TANGENT_BASIS',
            'source_frame':'UNSPECIFIED','source_polconv':'UNSPECIFIED',
            'signs':scenarios,'elapsed_pair_seconds':time.monotonic()-started,
            'caveats':['U+ and U- are formal sign scenarios, not established physical conventions or exhaustive uncertainty',
                       'Same ID does not establish independent skies or a pairing sampling law',
                       'No pixel downgrade, beam deconvolution, mask, or monopole removal',
                       'No null calibration, p value, shear, physical interpretation, or native solver claim',
                       'Raw versus processed 005a source bridge remains HOLD']}
    make_plot(result,outdir)
    report=['# FFP10 first-pair formal spin-2 audit','',
            f"Status: `{result['status']}`. Owner: OBSSTAT. Diagnostic only.",'',
            'Full-resolution RING Q/U in K_CMB were transformed at lmax=mmax=16.',
            'The four panels display EE and BB for U+ and U− with signal, noise, explicit pixel sum and signed twice-cross spectra.','',
            'The source headers omit COORDSYS and POLCCONV. Both sign cases use a formal HEALPix/COSMO tangent basis; they do not establish the delivered physical convention.','',
            'Source bytes, header layout, code, profile and coefficient archive hashes are in result.json.','',
            'No catalogue/null inference, p value, shear or physical interpretation. Raw versus processed 005a bridge remains HOLD.','']
    (outdir/'report.md').write_text('\n'.join(report))
    json_write(result_path,result)
    return result


def worker(stage,root,outdir):
    try:
        result=profile_worker(root,outdir) if stage=='profile' else pair_worker(root,outdir)
        print(json.dumps({'status':result['status'],'stage':stage}))
        return 0 if result['status'] in ('PROFILE_PASS','FORMAL_OPERATOR_PASS_SOURCE_BRIDGE_HOLD') else 2
    except Exception:
        Path(outdir).mkdir(parents=True,exist_ok=True)
        (Path(outdir)/(stage+'_failure.log')).write_text(traceback.format_exc())
        raise


def supervise(stage,root,outdir):
    import psutil
    root=Path(root).resolve();outdir=Path(outdir).resolve()
    outdir.mkdir(parents=True,exist_ok=True)
    budget_file=outdir/'runtime_budget.json'
    budget=json.loads(budget_file.read_text()) if budget_file.exists() else {
        'profile_seconds_used':0.,'pair_seconds_used':0.}
    used_profile=float(budget['profile_seconds_used'])
    used_pair=float(budget['pair_seconds_used'])
    avail=psutil.virtual_memory().available
    if avail<RSS_CAP:
        raise RuntimeError(f'AVAILABLE_RAM_PREFLIGHT_HOLD: {avail} < {RSS_CAP}')
    if stage=='pair' and not (outdir/'profile.json').exists():
        raise ValueError('PROFILE_FIRST_REQUIRED')
    limit=(PROFILE_SECONDS-used_profile if stage=='profile' else
           TOTAL_SECONDS-used_profile-used_pair)
    if limit<=0:raise TimeoutError('CUMULATIVE_TIME_CAP_EXHAUSTED')
    cmd=[sys.executable,str(Path(__file__).resolve()),'--worker-stage',stage,
         '--root',str(root),'--outdir',str(outdir)]
    env=os.environ.copy();env['OMP_NUM_THREADS']='1';env['OPENBLAS_NUM_THREADS']='1'
    env['HTT_FFP_SUPERVISED_WORKER']='1'
    process=subprocess.Popen(cmd,env=env)
    ps=psutil.Process(process.pid);begin=time.monotonic();maxrss=0;reason=None
    while process.poll() is None:
        elapsed=time.monotonic()-begin
        try:rss=ps.memory_info().rss
        except psutil.NoSuchProcess:rss=0
        maxrss=max(maxrss,rss)
        if rss>RSS_CAP or elapsed>limit:
            reason='RSS_6GIB_CAP' if rss>RSS_CAP else 'TIME_CAP'
            process.kill();process.wait()
            break
        time.sleep(.2)
    elapsed=time.monotonic()-begin
    key=stage+'_seconds_used';budget[key]=float(budget[key])+elapsed
    json_write(budget_file,budget)
    receipt={'stage':stage,'exit_code':process.returncode,'max_rss_bytes':maxrss,
             'elapsed_seconds':elapsed,'cumulative_budget':budget,
             'available_ram_preflight_bytes':avail,'rss_cap_bytes':RSS_CAP,
             'time_cap_seconds_this_attempt':limit,
             'status':'HOLD_'+reason if reason else 'COMPLETED' if process.returncode==0 else 'WORKER_FAILED',
             'requested_author_runtime':'gpt-6-sol/high',
             'observed_author_runtime':'UNKNOWN','observed_executor_runtime':'UNKNOWN'}
    json_write(outdir/(stage+'_supervisor.json'),receipt)
    return 3 if reason else process.returncode


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--stage',choices=('profile','pair'))
    p.add_argument('--worker-stage',choices=('profile','pair'))
    p.add_argument('--root',type=Path,default=ROOT)
    p.add_argument('--outdir',type=Path,default=OUT_DEFAULT)
    a=p.parse_args()
    if bool(a.stage)==bool(a.worker_stage):p.error('exactly one stage required')
    if a.worker_stage and os.environ.get('HTT_FFP_SUPERVISED_WORKER')!='1':
        p.error('worker stage requires bounded supervisor')
    return worker(a.worker_stage,a.root,a.outdir) if a.worker_stage else supervise(a.stage,a.root,a.outdir)

if __name__=='__main__':raise SystemExit(main())
