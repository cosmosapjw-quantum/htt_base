#!/usr/bin/env python3
"""Resumable, selected-column COSMOS-Web v1.1 descriptive controls.

Read raw fixed-width big-endian FITS windows, avoiding whole-table conversion.
Selection retention is not population completeness or an angular cosmology law.
"""
from __future__ import annotations
import argparse,hashlib,json,resource,time
from pathlib import Path
import numpy as np
from astropy.io import fits

ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'workdir/raw/cosmos_web_dr1/COSMOSWeb_mastercatalog_v1.1.fits'
PHOTO=('id','ra','dec','tile','flag_star','flag_blend','warn_flag','snr_f444w','wht_f444w')
REDSHIFT=('zfinal','zpdf_med','zpdf_l68','zpdf_u68')
Z_EDGES=np.array([0,.5,1,2,3,4,6,8,10,15.])
WIDTH_EDGES=np.linspace(0,2,41)


def table_spec(hdu):
    if hdu.header.get('PCOUNT',0)!=0:raise ValueError('fixed-width table without variable heap required')
    dtype=hdu.columns.dtype.newbyteorder('>')
    if dtype.itemsize!=hdu.header['NAXIS1']:raise ValueError('FITS row dtype/width mismatch')
    return {'offset':hdu.fileinfo()['datLoc'],'dtype':dtype,'rows':hdu.header['NAXIS2'],
            'formats':{c.name:c.format for c in hdu.columns},
            'scaled':[c.name for c in hdu.columns if c.bscale not in (None,1) or c.bzero not in (None,0)]}


def read_window(path,spec,start,stop,names):
    if set(names)&set(spec['scaled']):raise ValueError('selected scaled columns need explicit conversion')
    mapped=np.memmap(path,mode='r',offset=spec['offset']+start*spec['dtype'].itemsize,
                     dtype=spec['dtype'],shape=(stop-start,))
    answer={name:mapped[name].copy() for name in names}
    mapped._mmap.close()
    for name in names:
        if spec['formats'][name]=='L':
            raw=answer[name]
            if not np.isin(raw,[70,84]).all():raise ValueError('unknown FITS logical flag')
            answer[name]=raw==84
    return answer


def summarize_chunk(photo,z):
    n=len(photo['id']);goodz=np.isfinite(z['zfinal'])&(z['zfinal']>=0)&(z['zfinal']<=15)
    phot=np.isfinite(photo['snr_f444w'])&np.isfinite(photo['wht_f444w'])&(photo['wht_f444w']>0)
    secure=photo['warn_flag']==0
    clear=secure&(~photo['flag_star'])&(~photo['flag_blend'])
    scenarios=[]
    for quality,mask in [('warn_zero',secure),('warn_zero_unflagged',clear)]:
        for snr in (5,10,20):
            selected=mask&phot&(photo['snr_f444w']>=snr)
            valid=selected&goodz
            width=(z['zpdf_u68']-z['zpdf_l68'])/(1+z['zpdf_med'])
            validw=valid&np.isfinite(width)&(width>=0)&np.isfinite(z['zpdf_med'])&(z['zpdf_med']>=0)
            scenarios.append({'quality':quality,'snr_min':snr,'selected':int(selected.sum()),
                'valid_z':int(valid.sum()),'invalid_z':int((selected&~goodz).sum()),
                'z_hist':np.histogram(z['zfinal'][valid],Z_EDGES)[0].tolist(),
                'width_hist':np.histogram(width[validw],WIDTH_EDGES)[0].tolist(),
                'width_above_2':int((validw&(width>2)).sum()),'valid_width':int(validw.sum())})
    tiles={}
    for tile in np.unique(photo['tile']):
        mask=photo['tile']==tile;name=bytes(tile).decode('ascii').strip()
        tiles[name]={'rows':int(mask.sum()),'warn_zero':int((mask&secure).sum()),
                     'valid_z':int((mask&goodz).sum())}
    return {'rows':n,'warn_zero':int(secure.sum()),'star_flagged':int(photo['flag_star'].sum()),
            'blend_flagged':int(photo['flag_blend'].sum()),'valid_z':int(goodz.sum()),
            'scenarios':scenarios,'tiles':tiles}


def merge(total,part):
    for key in ('rows','warn_zero','star_flagged','blend_flagged','valid_z'):total[key]+=part[key]
    for a,b in zip(total['scenarios'],part['scenarios']):
        for key in ('selected','valid_z','invalid_z','width_above_2','valid_width'):a[key]+=b[key]
        for key in ('z_hist','width_hist'):a[key]=(np.array(a[key])+b[key]).tolist()
    for tile,counts in part['tiles'].items():
        old=total['tiles'].setdefault(tile,{key:0 for key in counts})
        for key,value in counts.items():old[key]+=value


def run(out,chunk,resume,stop_after):
    started=time.perf_counter();code=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    with fits.open(SOURCE,memmap=True,lazy_load_hdus=True) as h:
        specs=[table_spec(h[i]) for i in (1,2)]
    if specs[0]['rows']!=specs[1]['rows']:raise ValueError('parallel release row counts mismatch')
    identity={'release':'COSMOSWeb_mastercatalog_v1.1','source_bytes':SOURCE.stat().st_size,
              'source_mtime_ns':SOURCE.stat().st_mtime_ns,'rows':specs[0]['rows']}
    if resume:
        state=json.loads((out/'checkpoint.json').read_text())
        if state['source']!=identity or state['code_sha256']!=code or state['chunk_size']!=chunk:
            raise ValueError('resume source/code/chunk contract changed')
    else:
        out.mkdir(parents=True,exist_ok=False)
        state={'source':identity,'code_sha256':code,'chunk_size':chunk,'next_row':0,'batches':[],
               'total':None,'status':'RUNNING','elapsed_seconds':0.,'next_command':f'/usr/bin/python -B scripts/run_reboot_cosmos_selection.py --output-dir {out} --chunk-size {chunk} --resume'}
    count=0
    while state['next_row']<identity['rows']:
        start=state['next_row'];stop=min(start+chunk,identity['rows']);tick=time.perf_counter()
        photo=read_window(SOURCE,specs[0],start,stop,PHOTO);z=read_window(SOURCE,specs[1],start,stop,REDSHIFT)
        if not np.array_equal(photo['id'],np.arange(start,stop)):raise ValueError('source ID/parallel-row convention mismatch')
        part=summarize_chunk(photo,z)
        if state['total'] is None:state['total']=part
        else:merge(state['total'],part)
        digest=hashlib.sha256()
        for values in list(photo.values())+list(z.values()):digest.update(values.tobytes())
        state['batches'].append({'start':start,'stop':stop,'selected_column_sha256':digest.hexdigest(),'seconds':time.perf_counter()-tick})
        state['next_row']=stop;count+=1
        state['elapsed_seconds']+=time.perf_counter()-tick
        state['peak_rss_kib']=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        (out/'checkpoint.json').write_text(json.dumps(state,indent=2)+'\n')
        del photo,z
        if stop_after and count>=stop_after:break
    if state['next_row']<identity['rows']:
        print(json.dumps({'status':'PROFILE_CHECKPOINT','next_row':state['next_row'],'elapsed_seconds':state['elapsed_seconds'],'next_command':state['next_command']}));return
    state['status']='COMPLETE';(out/'checkpoint.json').write_text(json.dumps(state,indent=2)+'\n')
    result={'task':'RB22/AO17','owner':'obsstat','scope':'SMALL_AREA_DESCRIPTIVE_SELECTION_RETENTION_AND_REDSHIFT_INTERVAL_CONTROLS',
        'source':identity,'counts':state['total'],'z_edges':Z_EDGES.tolist(),'width_edges':WIDTH_EDGES.tolist(),
        'alignment':'release parallel-row convention per tutorial; id equals row index checked throughout; no independent crossmatch of a second catalogue',
        'sources':['https://cosmos2025.iap.fr/catalog.html','https://cosmos2025.iap.fr/tutorials/catalog_usage_tutorial.html'],
        'scope_limits':['selected retention is not completeness without injection/selection law','released zfinal in-range values include zero placeholders for stars/artifacts; not a galaxy photo-z population; 68% photo-z intervals descriptive, full 28GB PDF-z not read','no all-sky dipole/global tilt/posterior or independent host anchor'],
        'statistic_vs_bias':'counts/retention/interval widths only; no bias estimator or coverage calibration',
        'coverage_scope':'all784016 released rows scanned; finite quality/SNR grid, no full photometric/population analysis'}
    (out/'result.json').write_text(json.dumps(result,indent=2)+'\n')
    import matplotlib
    matplotlib.use('Agg')
    from matplotlib import pyplot as plt
    fig,axes=plt.subplots(1,2,figsize=(10,4))
    for s in result['counts']['scenarios']:
        if s['quality']=='warn_zero':axes[0].stairs(s['z_hist'],Z_EDGES,label=f"SNR >= {s['snr_min']}")
    axes[0].set(xlabel='released zfinal (zero placeholders included)',ylabel='retained count');axes[0].legend()
    tiles=sorted(result['counts']['tiles']);axes[1].bar(tiles,[result['counts']['tiles'][t]['warn_zero']/result['counts']['tiles'][t]['rows'] for t in tiles])
    axes[1].set(ylabel='warn_flag=0 retained fraction',xlabel='release tile');axes[1].tick_params(axis='x',rotation=90)
    fig.suptitle('COSMOS-Web v1.1 descriptive selection sensitivity');fig.tight_layout()
    for ext in ('png','pdf'):fig.savefig(out/f'selection_redshift.{ext}',dpi=170)
    plt.close(fig)
    (out/'report.md').write_text(f"# COSMOS-Web selection controls\n\n{state['total']['rows']} rows scanned in {state['elapsed_seconds']:.2f}s of batch processing, peak RSS {state['peak_rss_kib']/1024:.1f}MiB. warn_flag=0 count {state['total']['warn_zero']}; in-range released 0<=zfinal<=15 count {state['total']['valid_z']}. FITS big-endian and logical flags decoded explicitly; row IDs and parallel release ordering checked.\n\n![selection](selection_redshift.png)\n\n"+'\n'.join(result['scope_limits'])+'\n\nSource definitions: '+', '.join(result['sources'])+'\n')
    (out/'execution_receipt.json').write_text(json.dumps({'code_sha256':code,'command':state['next_command'],
        'thread_environment':'OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1','requested_parent':'gpt-6.1-sol/high','observed':'UNKNOWN',
        'elapsed_finalization_seconds':time.perf_counter()-started,'batches':len(state['batches']),'finalization_checkpoint_written':True},indent=2)+'\n')
    print(json.dumps({'status':'COMPLETE','rows':state['total']['rows'],'batches':len(state['batches'])}))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output-dir',type=Path,required=True);p.add_argument('--chunk-size',type=int,default=10000)
    p.add_argument('--resume',action='store_true');p.add_argument('--stop-after-batches',type=int,default=0)
    a=p.parse_args()
    if not 1<=a.chunk_size<=50000:raise ValueError('chunk1..50000 required')
    run(a.output_dir,a.chunk_size,a.resume,a.stop_after_batches)
