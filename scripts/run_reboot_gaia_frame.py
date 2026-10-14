#!/usr/bin/env python3
"""Gaia EDR3 in-sample frame spin/glide diagnostic with 2x2 covariance blocks."""
from __future__ import annotations
import argparse,csv,hashlib,json,time
from pathlib import Path
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'workdir/raw/gaia_edr3_spin_subset_20261014'


def design(ra_deg,dec_deg):
    ra,dec=np.deg2rad(ra_deg),np.deg2rad(dec_deg)
    if not np.isfinite(ra).all() or not np.isfinite(dec).all() or np.any(abs(dec)>np.pi/2):raise ValueError('finite sky positions required')
    a=np.stack((-np.sin(dec)*np.cos(ra),-np.sin(dec)*np.sin(ra),np.cos(dec),
                -np.sin(ra),np.cos(ra),np.zeros_like(ra)),axis=-1)
    b=np.stack((np.sin(ra),-np.cos(ra),np.zeros_like(ra),
                -np.sin(dec)*np.cos(ra),-np.sin(dec)*np.sin(ra),np.cos(dec)),axis=-1)
    return np.stack((a,b),axis=-2)


def block_fit(x,y,c):
    if any(np.iscomplexobj(v) for v in (x,y,c)):raise ValueError("real tangent coordinates and covariance required")
    x=np.asarray(x,float);y=np.asarray(y,float);c=np.asarray(c,float)
    if x.ndim!=3 or x.shape[1:]!=(2,6) or y.shape!=x.shape[:2] or c.shape!=(len(x),2,2):raise ValueError('aligned tangent design/covariance required')
    if not all(np.isfinite(a).all() for a in (x,y,c)) or not np.allclose(c,c.transpose(0,2,1),rtol=1e-12,atol=0):raise ValueError('finite symmetric blocks required')
    l=np.linalg.cholesky(c)
    wx=np.linalg.solve(l,x).reshape(-1,6);wy=np.linalg.solve(l,y[...,None])[...,0].ravel()
    u,s,vt=np.linalg.svd(wx,full_matrices=False);threshold=np.finfo(float).eps*max(wx.shape)*s[0]
    rank=int((s>threshold).sum())
    if rank!=6:raise ValueError('spin/glide design rank deficient')
    theta=vt.T@((u.T@wy)/s);cov=(vt.T/s**2)@vt
    residual=wy-wx@theta
    return {'coefficients_mas_yr':theta.tolist(),'covariance_mas2_yr2':cov.tolist(),
        'weighted_RSS':float(residual@residual),'nominal_df':len(wy)-6,'rank':rank,
        'singular_values':s.tolist(),'rank_threshold':float(threshold),'condition':float(s[0]/s[-1])}


def run(out):
    start=time.perf_counter()
    if out.exists():raise ValueError('fresh output directory required')
    source=json.loads((SOURCE/'source.json').read_text());raw=(SOURCE/'rows.csv').read_bytes()
    if hashlib.sha256(raw).hexdigest()!=source['sha256']:raise ValueError('frozen Gaia response bytes changed')
    with (SOURCE/'rows.csv').open() as f:rows=list(csv.DictReader(f))
    ids=[int(r['source_id']) for r in rows]
    if len(set(ids))!=len(ids) or len(ids)!=source['row_count']:raise ValueError('source count or unique IDs changed')
    columns={k:np.array([float(r[k]) for r in rows]) for k in ['ra','dec','pmra','pmdec','pmra_error','pmdec_error','pmra_pmdec_corr','ref_epoch','random_index']}
    if not all(np.isfinite(v).all() for v in columns.values()) or np.any(columns['ref_epoch']!=2016.) or np.any(columns['random_index']>=20000000):raise ValueError('catalog qualification failed')
    sa,sb,rho=columns['pmra_error'],columns['pmdec_error'],columns['pmra_pmdec_corr']
    if np.any(sa<=0) or np.any(sb<=0) or np.any(abs(rho)>=1):raise ValueError('proper-motion covariance domain failed')
    x=design(columns['ra'],columns['dec']);y=np.column_stack((columns['pmra'],columns['pmdec']))
    c=np.zeros((len(rows),2,2));c[:,0,0]=sa**2;c[:,1,1]=sb**2;c[:,0,1]=c[:,1,0]=rho*sa*sb
    full=block_fit(x,y,c)
    ra,dec=np.deg2rad(columns['ra']),np.deg2rad(columns['dec'])
    n=np.column_stack((np.cos(dec)*np.cos(ra),np.cos(dec)*np.sin(ra),np.sin(dec)))
    octant=((n>=0)*np.array([1,2,4])).sum(axis=1)
    deletions=[]
    for i in range(8):
        keep=octant!=i;fit=block_fit(x[keep],y[keep],c[keep]);fit.update(octant=i,retained=int(keep.sum()),removed=int((~keep).sum()))
        fit['shift_mas_yr']=(np.array(fit['coefficients_mas_yr'])-full['coefficients_mas_yr']).tolist();deletions.append(fit)
    scaling=[]
    for scale in (1.,2.,4.):
        fit=block_fit(x,y,c*scale**2)
        np.testing.assert_allclose(fit['coefficients_mas_yr'],full['coefficients_mas_yr'],atol=1e-12)
        np.testing.assert_allclose(fit['covariance_mas2_yr2'],np.array(full['covariance_mas2_yr2'])*scale**2,rtol=1e-12,atol=1e-16)
        fit['error_scale']=scale;scaling.append(fit)
    result={'task':'RB22/AO16','owner':'HTT','scope':'IN_SAMPLE_EDR3_FRAME_SOURCE_GAUSSIAN_WORKING_MODEL',
        'source':source,'returned_rows':len(rows),'source_ids_decimal':[str(i) for i in ids],
        'coefficient_order':['spin_x','spin_y','spin_z','glide_x','glide_y','glide_z'],
        'units':'mas/year; pmra already mu_alpha*cos(dec)','frame':'ICRS, referenceJ2016.0, TCB',
        'release_window':'34 months July2014-May2017','astrometry_window':'1009 days from2014-08-22 21:00 UTC toMay2017, interruptions; no top-hat or instantaneous derivative interpretation',
        'full_fit':full,'octant_leaveout':deletions,'error_scale_sensitivity':scaling,
        'density':'independent per-source marginal pm covariance Gaussian proxy, directions conditioned fixed',
        'selection':'outcome-dependent upstream frame-spin source selection retained; query random_index subset only',
        'source_status':'queried COUNT matches4756 response rows; separate query found no non-five-parameter selected sources',
        'science_status':'DESCRIPTIVE_CONDITIONAL; NO_CALIBRATED_NULL_P_OR_EVIDENCE',
        'caveats':['in-sample frame calibration control, no independent reference-frame physics test','cross-source calibration correlations and direction-error propagation unavailable','error scaling changes proxy intervals only, does not repair source selection/correlations','no acceleration, velocity, instantaneous shear, global tilt or native geometry inference'],
        'references':['https://arxiv.org/html/2204.12574v2','https://gea.esac.esa.int/archive/documentation/GEDR3/Data_processing/chap_cu3ast/sec_cu3ast_cali/ssec_cu3ast_cali_frame.html','https://arxiv.org/abs/2012.03380']}
    out.mkdir(parents=True);(out/'result.json').write_text(json.dumps(result,indent=2)+'\n')
    np.savez(out/'qualified_rows.npz',source_id=np.array(ids,dtype=np.int64),ra=columns['ra'],dec=columns['dec'],proper_motion=y,covariance=c,octant=octant)
    import matplotlib
    matplotlib.use('Agg')
    from matplotlib import pyplot as plt
    fig,axes=plt.subplots(2,3,figsize=(10,6),sharex=True)
    for i,ax in enumerate(axes.ravel()):
        coeff=np.array([r['coefficients_mas_yr'][i] for r in deletions])*1000
        ax.plot(np.arange(8),coeff,'o',label='leave octant out')
        ax.axhline(full['coefficients_mas_yr'][i]*1000,color='C1',label='full subset')
        sigma=np.sqrt(np.array(full['covariance_mas2_yr2'])[i,i])*1000
        for scale,color in ((1,'#0072B2'),(2,'#56B4E9'),(4,'#999999')):
            ax.errorbar(8+scale/5,full['coefficients_mas_yr'][i]*1000,yerr=scale*sigma,fmt='s',color=color)
        ax.set(title=result['coefficient_order'][i],xlabel='excluded octant / full scaled errors',ylabel='microas/year proxy')
    fig.suptitle('Gaia EDR3 selected frame-source spin/glide controls');fig.tight_layout(rect=(0,0,1,.94))
    for ext in ('png','pdf'):fig.savefig(out/f'frame_controls.{ext}',dpi=170)
    plt.close(fig)
    text=f"# Gaia frame-source diagnostic\n\n{len(rows)} actual EDR3 used-spin sources selected by fixed random_index cutoff, verified with independent COUNT/solution-type queries. Full six-coordinate fit rank={full['rank']}, condition={full['condition']:.4f}, descriptive weighted RSS={full['weighted_RSS']:.3f}, nominal df={full['nominal_df']}.\n\nSpin/glide coefficients (microas/year): "+str((1000*np.array(full['coefficients_mas_yr'])).tolist())+"\n\n![frame](frame_controls.png)\n\n"+'\n'.join(result['caveats'])+'\n\n'+result['astrometry_window']+'\n\n'+', '.join(result['references'])+'\n'
    (out/'report.md').write_text(text)
    receipt={'code_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'source_csv_sha256':source['sha256'],
        'seconds':time.perf_counter()-start,'command':f'/usr/bin/python -B scripts/run_reboot_gaia_frame.py --output-dir {out}',
        'requested_parent':'gpt-6.1-sol/high','physics_requested':'gpt-6-astra/xhigh','observed':'UNKNOWN','seed':'release random_index cutoff, no new seed','batch':'4756 rows, 8 fixed octants'}
    (out/'execution_receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps({'rows':len(rows),'rank':full['rank'],'coefficients_microas_year':(1000*np.array(full['coefficients_mas_yr'])).tolist()}))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output-dir',type=Path,required=True);a=p.parse_args();run(a.output_dir)
