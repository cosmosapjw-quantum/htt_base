#!/usr/bin/env python3
"""CLASS DR1 transfer geometry and conditional split-noise half-difference control.

Transfer matrix diagnostics are never applied to the raw masked Q/U statistic.
The latter uses a declared independently paired split-noise approximation.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
from pathlib import Path
import platform
import re
import subprocess
import sys
import tarfile
import time
import traceback

import numpy as np

ROOT=Path(__file__).resolve().parents[1]
BASE_REL='workdir/raw/class_dr1'
SOURCE_URLS={
 'transfer':'https://lambda.gsfc.nasa.gov/product/class/class_dr1_map_xfer_func_info.html',
 'noise':'https://lambda.gsfc.nasa.gov/product/class/class_dr1_sims_info.html',
 'pipeline':'https://arxiv.org/abs/2305.01045',
 'spectra':'https://arxiv.org/abs/2309.00675',
}
MASKS=('d0','s0')
LMAX=32
BAND=(5,30)
SEED=20261014
MEMBER=re.compile(r'^class_dr1_40GHz_skymap_noise_sim_(\d{3})_(m[12])_n128\.fits$')


def sha256(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda:f.read(1<<20),b''):h.update(block)
    return h.hexdigest()


def write_json(path,payload):
    Path(path).write_text(json.dumps(payload,indent=2,allow_nan=False,default=lambda x:
        x.item() if isinstance(x,np.generic) else x.tolist() if isinstance(x,np.ndarray) else str(x))+'\n')


def transfer_geometry(matrix,n_ell=384,low=5,high=30):
    """Rows are output, columns input; V/E/B contiguous ell blocks."""
    f=np.asarray(matrix,dtype=float)
    if f.shape!=(3*n_ell,3*n_ell) or not np.isfinite(f).all():
        raise ValueError('finite VEB square transfer matrix required')
    if not 0<=low<=high<n_ell:
        raise ValueError('bounded multipole slice required')
    sel=np.arange(low,high+1)
    outside=np.r_[0:low,high+1:n_ell]
    names='VEB'
    blocks={};leakage={}
    for out_i,out_name in enumerate(names):
        for in_i,in_name in enumerate(names):
            x=f[np.ix_(out_i*n_ell+sel,in_i*n_ell+sel)]
            singular=np.linalg.svd(x,compute_uv=False)
            tol=max(x.shape)*np.finfo(float).eps*singular[0]
            key=out_name+'<-'+in_name
            col_all=f[np.ix_(out_i*n_ell+np.arange(n_ell),in_i*n_ell+sel)]
            col_outside=f[np.ix_(out_i*n_ell+outside,in_i*n_ell+sel)]
            blocks[key]={'shape':list(x.shape),'singular_values':singular.tolist(),
                         'svd_rank_at_machine_tolerance':int((singular>tol).sum()),
                         'frobenius_norm_low_output':float(np.linalg.norm(x)),
                         'frobenius_norm_all_output_0_383':float(np.linalg.norm(col_all)),
                         'frobenius_norm_outside_output_band':float(np.linalg.norm(col_outside)),
                         'outside_fraction_of_all_output_norm':float(np.linalg.norm(col_outside)/np.linalg.norm(col_all)) if np.linalg.norm(col_all)>0 else None}
    ee=blocks['E<-E']['frobenius_norm_low_output']
    be=blocks['B<-E']['frobenius_norm_low_output']
    leakage={'E_to_B_low_block_frobenius':be,'E_to_E_low_block_frobenius':ee,
             'E_to_B_over_E_to_E_norm':be/ee if ee>0 else None}
    return {'matrix_action':'C_out=F C_in','rows':'output','columns':'input',
            'block_order':'VEB, ell=0..383 in each block','low_input_band':[low,high],
            'all_output_multipoles_inspected':[0,n_ell-1],
            'blocks':blocks,'leakage_geometry':leakage,
            'status':'NUMERIC_GEOMETRY_ONLY_NO_INVERSE',
            'caveats':['Band-limited input leaks to output multipoles outside the displayed band',
                       'Other zero entries reflect release approximation, not known physical zeros',
                       'Beam transfer is separate and unapplied',
                       'Official pseudo-Cl transfer calibration only supported above ell=4',
                       'F is not applied to the raw masked Q/U half-difference control']}


def transfer_stage(base):
    import h5py  # intentional lazy import: transfer venv does not have astropy
    files=[];results={}
    for weight in ('hits','uniform'):
        path=base/f'class_dr1_40GHz_VEB_transfer_matrix_lmax383_{weight}.hdf5'
        with h5py.File(path) as h:
            if set(h.keys())!={'F'} or h['F'].shape!=(1152,1152) or int(h.attrs['lmax'])!=383 or h.attrs['order']!='VEB':
                raise ValueError('CLASS delivered HDF5 transfer structure changed')
            results[weight]=transfer_geometry(h['F'][:])
            results[weight]['hdf5_attributes']={k:str(v) for k,v in h.attrs.items()}
        files.append(path)
    return {'owner':'OBSSTAT','claim_tier':'DIAGNOSTIC_ONLY','scope':'CLASS_DR1_TRANSFER_NUMERIC_GEOMETRY',
            'weightings':results,'beam_status':'SEPARATE_NOT_APPLIED','noise_status':'NOT_USED',
            'source_urls':SOURCE_URLS},files


def pairing(n=200,seed=SEED):
    rng=np.random.default_rng(seed)
    p=rng.permutation(n)
    if len(np.unique(p))!=n or np.any(p<0) or np.any(p>=n):
        raise ValueError('one-to-one noise pairing failed')
    return np.column_stack((np.arange(n),p))


def half_difference(a1,a2):
    a1=np.asarray(a1);a2=np.asarray(a2)
    if a1.shape!=a2.shape:
        raise ValueError('split alm shapes differ')
    return (a1-a2)/2


def feature_vector(coefficients,low=5,high=30):
    import healpy as hp
    output=[]
    for mask in MASKS:
        e,b=(np.asarray(coefficients[mask+'_'+kind]) for kind in ('E','B'))
        ee=np.real(hp.alm2cl(e));bb=np.real(hp.alm2cl(b))
        eb=np.real(hp.alm2cl(e,b))
        if min(len(ee),len(bb),len(eb))<=high:
            raise ValueError('lmax below fixed feature band')
        output.extend([float(ee[low:high+1].mean()),float(bb[low:high+1].mean()),
                       float(np.abs(eb[low:high+1]).mean())])
    if not np.isfinite(output).all():
        raise ValueError('nonfinite pseudo-Cl feature')
    return np.array(output)


def max_statistic(observed,training,calibration):
    observed=np.asarray(observed,float);training=np.asarray(training,float);calibration=np.asarray(calibration,float)
    if observed.shape!=(6,) or training.shape!=(40,6) or calibration.shape!=(160,6):
        raise ValueError('fixed observed/train40/cal160 feature shapes required')
    center=training.mean(axis=0);scale=training.std(axis=0,ddof=1)
    if np.any(scale<=0) or not np.isfinite(scale).all():
        return {'status':'HOLD_ZERO_TRAINING_SCALE','center':center.tolist(),'scale':scale.tolist()}
    score=lambda rows:np.max(np.abs((rows-center)/scale),axis=-1)
    obs=float(score(observed));cal=score(calibration)
    exceed=int(np.count_nonzero(cal>=obs))
    return {'status':'CONDITIONAL_SPLIT_NOISE_MAX_RANK','observed_max_abs_z':obs,
            'calibration_max_abs_z':cal.tolist(),'train_center':center.tolist(),
            'train_scale':scale.tolist(),'exceedances':exceed,'rank_p':(1+exceed)/161,
            'rank_floor':1/161,'training_rows':40,'calibration_rows':160,
            'null_scope':'independently paired split-noise approximation with fixed masks and operator'}


def reader_helpers(root):
    sys.path.insert(0,str(root))
    from scripts.reboot_spectra_polarization import read_qu,read_binary_mask
    return read_qu,read_binary_mask


def checked_qu(source,reader):
    from astropy.io import fits
    payload=source.getvalue() if isinstance(source,io.BytesIO) else None
    with fits.open(io.BytesIO(payload) if payload is not None else source,memmap=False) as hdus:
        h=hdus[1].header
        if h.get('TEMPTYPE')!='THERMO' or h.get('COORDSYS')!='C' or h.get('POLCCONV')!='COSMO':
            raise ValueError('CLASS native THERMO/C/COSMO header mismatch')
    q,u,valid,meta=reader(io.BytesIO(payload) if payload is not None else source,
                          expected_nside=128,expected_coords='C')
    if meta['native_unit']!='K':
        raise ValueError('CLASS native K map unit changed')
    meta['temperature_type']='THERMO'
    return q,u,valid,meta


def spin_coefficients(q,u,valid,masks):
    import healpy as hp
    out={}
    for name,mask in masks.items():
        keep=mask&valid
        if not keep.any():raise ValueError('empty CLASS retained mask')
        e,b=hp.map2alm_spin([np.where(keep,q,0.),np.where(keep,u,0.)],2,lmax=LMAX)
        out[name+'_E']=e;out[name+'_B']=b
    return out


def paired_coefficients(first,second):
    return {key:half_difference(first[key],second[key]) for key in first}


def cache_split(archive_path,split,wanted,cache,masks,reader,source_sha,mask_sha,script_sha,expected_valid):
    cache.mkdir(parents=True,exist_ok=True)
    found=set()
    # Stream gzip once; each FITS member is bounded to one map in memory.
    with tarfile.open(archive_path,mode='r|gz') as archive:
        for member in archive:
            match=MEMBER.fullmatch(member.name)
            if not match or match.group(2)!=split:raise ValueError('unexpected CLASS noise archive member '+member.name)
            index=int(match.group(1))
            if index in found or not 0<=index<200:raise ValueError('duplicate/out-of-range noise ID')
            found.add(index)
            if index not in wanted:continue
            target=cache/f'{split}_{index:03d}.npz'
            if target.exists():
                with np.load(target,allow_pickle=False) as z:
                    if str(z['member'].item())!=member.name or str(z['archive_sha'].item())!=source_sha or \
                       str(z['mask_sha'].item())!=mask_sha or str(z['script_sha'].item())!=script_sha or \
                       int(z['lmax'].item())!=LMAX:
                        raise ValueError('cached coefficient identity mismatch '+str(target))
                continue
            raw=archive.extractfile(member).read()
            q,u,valid,meta=checked_qu(io.BytesIO(raw),reader)
            if not np.array_equal(valid,expected_valid):
                raise ValueError('noise valid-pixel support differs from observed split support')
            coeff=spin_coefficients(q,u,valid,masks)
            tmp=target.with_name(target.name+'.tmp.npz')
            np.savez_compressed(tmp,**coeff,member=member.name,member_sha=hashlib.sha256(raw).hexdigest(),
                                archive_sha=source_sha,mask_sha=mask_sha,script_sha=script_sha,
                                lmax=LMAX,header_meta=json.dumps(meta))
            os.replace(tmp,target)
    if found!=set(range(200)):
        raise ValueError('CLASS archive does not contain exactly IDs000..199')


def load_cached(cache,split,index):
    with np.load(cache/f'{split}_{index:03d}.npz',allow_pickle=False) as z:
        return {name:z[name] for name in (f'{mask}_{kind}' for mask in MASKS for kind in ('E','B'))}


def noise_stage(base,root,output,limit,resume):
    if limit not in (4,200):raise ValueError('noise stage only accepts profile4 or full200')
    read_qu,read_mask=reader_helpers(root)
    maskpaths={name:base/f'class_dr1_40GHz_{name[0]}X_mask_n128.fits' for name in MASKS}
    masks={name:read_mask(path,name,128) for name,path in maskpaths.items()}
    mask_sha={name:sha256(path) for name,path in maskpaths.items()}
    mask_identity=json.dumps(mask_sha,sort_keys=True)
    maps=[base/f'class_dr1_40GHz_skymap_{split}_n128.fits' for split in ('m1','m2')]
    data=[checked_qu(path,read_qu) for path in maps]
    if not np.array_equal(data[0][2],data[1][2]):
        raise ValueError('observed split valid-pixel support differs')
    obs=paired_coefficients(spin_coefficients(*data[0][:3],masks),spin_coefficients(*data[1][:3],masks))
    obs_features=feature_vector(obs)
    pairs=pairing();pairs=pairs[:limit]
    if len(set(map(tuple,pairs)))!=limit or len(set(pairs[:,0]))!=limit or len(set(pairs[:,1]))!=limit:
        raise ValueError('noise pair reuse')
    archives={split:base/f'class_dr1_40GHz_skymap_noise_sim_{split}.tar.gz' for split in ('m1','m2')}
    archive_sha={name:sha256(path) for name,path in archives.items()}
    script_sha=sha256(Path(__file__))
    cache=output/'coefficient_cache'
    for split,column in (('m1',0),('m2',1)):
        cache_split(archives[split],split,set(map(int,pairs[:,column])),cache,masks,read_qu,
                    archive_sha[split],mask_identity,script_sha,data[0][2])
    rows=[]
    for first,second in pairs:
        coef=paired_coefficients(load_cached(cache,'m1',int(first)),
                                 load_cached(cache,'m2',int(second)))
        rows.append({'m1_id':int(first),'m2_id':int(second),
                     'm1_member':f'class_dr1_40GHz_skymap_noise_sim_{int(first):03d}_m1_n128.fits',
                     'm2_member':f'class_dr1_40GHz_skymap_noise_sim_{int(second):03d}_m2_n128.fits',
                     'features':feature_vector(coef).tolist()})
    result={'owner':'OBSSTAT','claim_tier':'DIAGNOSTIC_ONLY','scope':'CLASS_DR1_RAW_SPLIT_NOISE_CONDITIONAL_CONTROL',
            'status':'PROFILE_4_ONLY' if limit==4 else 'CONDITIONAL_NOISE_RANK',
            'coordinate_frame':'Celestial C','unit':'microK_CMB converted from native K THERMO',
            'polarization_convention':'COSMO','nside':128,'ordering':'RING',
            'operator':'mask Q/U identically, spin2 map2alm_spin lmax32, subtract alms then divide by2, pseudo Cl band5..30',
            'feature_order':[f'{mask}_{kind}' for mask in MASKS for kind in ('EE','BB','mean_abs_Re_EB')],
            'observed_half_difference_features':obs_features.tolist(),
            'pairs':rows,'pair_seed':SEED,'pair_law':'one-to-one deterministic permutation of m2 IDs; no same-ID physical pairing',
            'source_headers':[x[3] for x in data],
            'source_sha256':{'maps':{p.name:sha256(p) for p in maps},'masks':mask_sha,'noise_archives':archive_sha},
            'source_urls':SOURCE_URLS,
            'caveats':['Independent split-noise pairing is an approximation, not a released joint noise law',
                       'Observed half-difference is same-sky; signal cancellation only approximate',
                       'Foreground and systematic residual interpretation remains HOLD',
                       'Raw masked pseudo spectra do not use the transfer F, beam, or PolSpice estimator',
                       'No physical null, primordial BB, family, or global-tilt admission']}
    if limit==200:
        result['calibration']=max_statistic(obs_features,
            np.array([r['features'] for r in rows[:40]]),
            np.array([r['features'] for r in rows[40:]]))
    return result,[*maps,*maskpaths.values(),*archives.values()]


def plot(output,result):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    if 'weightings' in result:
        fig,axes=plt.subplots(1,2,figsize=(10,4))
        for ax,(weight,data) in zip(axes,result['weightings'].items()):
            for name in ('E<-E','B<-E','B<-B'):
                ax.semilogy(data['blocks'][name]['singular_values'],label=name)
            ax.set_title(weight);ax.set_xlabel('singular index');ax.set_ylabel('low-block singular value');ax.legend()
    else:
        fig,axes=plt.subplots(1,2,figsize=(10,4))
        rows=np.array([r['features'] for r in result['pairs']])
        for i,name in enumerate(MASKS):
            axes[i].plot(rows[:,3*i+1],'.',label='noise BB')
            axes[i].axhline(result['observed_half_difference_features'][3*i+1],color='r',label='observed half-diff')
            axes[i].set_title(name);axes[i].set_xlabel('paired noise index');axes[i].set_ylabel('masked pseudo BB (microK squared)');axes[i].legend()
    fig.suptitle(result['scope'].replace('_',' ').lower(),fontsize=9);fig.tight_layout()
    for suffix in ('png','pdf'):fig.savefig(output/('diagnostic.'+suffix),dpi=150)
    plt.close(fig)


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--stage',choices=('transfer','noise'),required=True)
    p.add_argument('--repo-root',type=Path,default=ROOT)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--limit',type=int,choices=(4,200),default=4)
    p.add_argument('--resume',action='store_true')
    args=p.parse_args(argv);root=args.repo_root.resolve();base=root/BASE_REL;output=args.output.resolve()
    if args.resume:
        if not output.is_dir():raise ValueError('resume requires existing output directory')
    else:output.mkdir(parents=True,exist_ok=False)
    attempt=0
    if args.resume:
        attempt=1
        while (output/f'execution_receipt_resume_{attempt:03d}.json').exists():
            attempt+=1
    receipt_path=output/('execution_receipt.json' if attempt==0 else f'execution_receipt_resume_{attempt:03d}.json')
    failure_path=output/('failure.log' if attempt==0 else f'failure_resume_{attempt:03d}.log')
    receipt={'stage':args.stage,'command':sys.argv,'cwd':os.getcwd(),'python':sys.version,
             'numpy':np.__version__,'platform':platform.platform(),
             'requested_author_runtime':'gpt-6-sol/high','observed_author_runtime':'UNKNOWN',
             'scientific_admission':'NOT_EVALUATED'}
    for key,cmd in (('git_head',['rev-parse','HEAD']),('git_status',['status','--porcelain=v1'])):
        proc=subprocess.run(['git','-C',str(root),*cmd],capture_output=True,text=True)
        receipt[key]=proc.stdout.strip() if proc.returncode==0 else 'UNAVAILABLE'
    start=time.monotonic()
    try:
        if args.stage=='transfer':result,files=transfer_stage(base)
        else:result,files=noise_stage(base,root,output,args.limit,args.resume)
        receipt['sources']=[{'path':str(path.relative_to(root)),'size_bytes':path.stat().st_size,
                             'sha256':sha256(path)} for path in files]
        write_json(output/'result.json',result)
        plot(output,result)
        report='# '+result['scope'].replace('_',' ')+'\n\n'
        report+='Owner OBSSTAT. Diagnostic-only. Exact source IDs, method, limitations and conditional results are in result.json and execution_receipt.json.\n\n'
        report+='Transfer geometry is separate from raw masked Q/U noise statistics. No inverse, beam correction, PolSpice parity or physical null admission is implied.\n\n'
        report+='\n'.join('- '+x for x in result.get('caveats',[]))+'\n'
        (output/'report.md').write_text(report)
        receipt['exit_code']=0
    except Exception as exc:
        receipt['exit_code']=1;receipt['error']=type(exc).__name__+': '+str(exc)
        failure_path.write_text(traceback.format_exc())
    receipt['elapsed_seconds']=time.monotonic()-start
    receipt['code_sha256']=sha256(Path(__file__))
    write_json(receipt_path,receipt)
    print(json.dumps({'stage':args.stage,'exit_code':receipt['exit_code'],
                      'elapsed_seconds':receipt['elapsed_seconds'],'output':str(output)}))
    return receipt['exit_code']

if __name__=='__main__':raise SystemExit(main())
