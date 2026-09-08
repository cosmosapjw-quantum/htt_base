#!/usr/bin/env python3
"""Execute inventory-named flow and same-sky map controls, without inference."""
from __future__ import annotations
import argparse
import csv
import hashlib
import itertools
import json
from pathlib import Path
import sys
import time

ROOT=Path(__file__).resolve().parents[2]
for p in (ROOT,ROOT/'htt',ROOT/'htt/src',ROOT/'htt/htt'):sys.path.insert(0,str(p))
import numpy as np

RAW=Path('/home/cosmosapjw/Dropbox/bianchi/htt_base/workdir/raw')
INVENTORY=RAW.parent/'asset_inventory_20260907/assets.csv'


def save(path,value):
    Path(path).write_text(json.dumps(value,indent=2,allow_nan=False)+'\n')


def source(path):
    path=Path(path).resolve();s=path.stat()
    return {'path':str(path),'size_bytes':s.st_size,'mtime_ns':s.st_mtime_ns}


def unavailable(exc):
    return {'outcome':'INPUT_UNAVAILABLE','reason':f'{type(exc).__name__}: {exc}','empirical_eligible':False}


def field_controls(directory):
    from astropy.table import Table
    from obsstat.r8_field_controls import galactic_positions,sample_field,load_carrick,load_coras,load_lilow
    from obsstat.jwst_distance_consistency import (PR319_2MRS_NEURAL_FIELD_MEMBER_SHA256,
        PR319_2MRS_HUBBLE_H,evaluate_pr319_2mrs_neural_radial_velocity)
    table_path=RAW/'cf4_full/table4.dat';readme=table_path.parent/'ReadMe'
    t=Table.read(table_path,format='ascii.cds',readme=readme)
    ids=np.array([f'CF4-GROUP-{int(v)}' for v in t['1PGC']])
    if len(np.unique(ids))!=len(ids):raise ValueError('CF4 group identity not unique')
    vcmb=np.asarray(t['V3k'],float);r=vcmb/100.
    l,b=np.asarray(t['GLON'],float),np.asarray(t['GLAT'],float)
    usable=np.isfinite(r)&(r>0)&np.isfinite(l)&np.isfinite(b)&(abs(b)<=90)
    pos=np.full((len(ids),3),np.nan);directions=np.full_like(pos,np.nan)
    pos[usable],directions[usable]=galactic_positions(l[usable],b[usable],r[usable],units='Mpc/h')
    arrays={'sample_ids':ids,'radius_proxy_hmpc':r,'positions_hmpc':pos,'directions':directions,
            'cf4_published_Vpec_km_s':np.asarray(t['Vpec'],float),
            'cf4_published_luminosity_distance_mpc':np.asarray(t['Dist'],float)}
    results={};loaded={}
    loaders={'carrick_2mpp':lambda:load_carrick(RAW/'carrick_2mpp'),
             'coras_zCMB':lambda:load_coras(RAW/'coras_2mrs/cartesian_grid_velocity_zCMB.dat'),
             'lilow_2mrs':lambda:load_lilow(RAW/'lilow_nn_2mrs')}
    for key,loader in loaders.items():
        started=time.monotonic()
        try:
            pins={}
            if key=='lilow_2mrs':
                for axis in 'xyz':
                    path=RAW/f'lilow_nn_2mrs/{axis}Velocity.npy'
                    digest='sha256:'+hashlib.sha256(path.read_bytes()).hexdigest()
                    if digest!=PR319_2MRS_NEURAL_FIELD_MEMBER_SHA256[path.name]:raise ValueError('selected PR319 immutable member mismatch')
                    pins[path.name]=digest
            field=loader();out=sample_field(field,ids,pos,directions)
            arrays[key+'_velocity_km_s']=out.velocity_km_s
            arrays[key+'_radial_km_s']=out.radial_km_s
            arrays[key+'_status']=out.status
            residual=out.radial_km_s[out.available]-arrays['cf4_published_Vpec_km_s'][out.available]
            results[key]={'outcome':'DESCRIPTIVE_CONTROL','empirical_eligible':False,'metadata':field.metadata,
                'rows':len(ids),'available_rows':int(out.available.sum()),
                'status_counts':{str(s):int(n) for s,n in zip(*np.unique(out.status,return_counts=True))},
                'residual_definition':'released field outward velocity minus published CF4 Vpec at fixed redshift-position proxy',
                'residual_quantiles_km_s':np.quantile(residual,[.1,.5,.9]).tolist() if len(residual) else None,
                'pins':pins,'elapsed_seconds':time.monotonic()-started}
            if key=='lilow_2mrs':
                rows=np.flatnonzero(out.available)[:100]
                donor=evaluate_pr319_2mrs_neural_radial_velocity(x_velocity=field.components[0],y_velocity=field.components[1],
                    z_velocity=field.components[2],galactic_l_deg=l[rows],galactic_b_deg=b[rows],
                    depth_mpc=r[rows]/PR319_2MRS_HUBBLE_H,hubble_h=PR319_2MRS_HUBBLE_H)
                error=float(np.max(abs(donor-out.radial_km_s[rows]))) if len(rows) else None
                if error is None or error>1e-8:raise ValueError(f'PR319 interpolation parity failed: {error}')
                results[key]['donor_parity']={'rows':ids[rows].tolist(),'max_abs_km_s':error,'tolerance_km_s':1e-8,
                    'coordinate_conversion':'depth_mpc=(V3k/100)/registered_h; h is not fitted or transferred to other source laws'}
            print(key,results[key]['available_rows'],'of',len(ids),'rows',flush=True)
            del field
        except Exception as exc:
            results[key]=unavailable(exc)
            arrays[key+'_velocity_km_s']=np.full((len(ids),3),np.nan)
            arrays[key+'_radial_km_s']=np.full(len(ids),np.nan)
            arrays[key+'_status']=np.full(len(ids),'PRODUCT_UNAVAILABLE',dtype='<U48')
            print(key,results[key],flush=True)
    cf4pp=RAW/'cf4/CF4pp_mean_std_grids.npz'
    try:
        with np.load(cf4pp,allow_pickle=False) as z:
            v=z['v_mean_CF4pp'];vr=z['vr_mean_CF4pp']
            if v.shape!=(3,128,128,128) or vr.shape!=(128,128,128):raise ValueError('CF4++ released grid shape changed')
            indices=np.array(list(itertools.product((12,35,62,87,113),repeat=3)))
            unit=indices-63.5;unit=unit/np.linalg.norm(unit,axis=1)[:,None]
            vector=v[(slice(None),*indices.T)].T;radial=vr[tuple(indices.T)]
            declared=np.einsum('ij,ij->i',vector,unit)
            swapped=np.einsum('ij,ij->i',vector,unit[:,[1,0,2]])
            discrepancy={'indices':indices.tolist(),'declared_xyz_rmse_km_s':float(np.sqrt(np.mean((radial-declared)**2))),
                         'xy_swapped_diagnostic_rmse_km_s':float(np.sqrt(np.mean((radial-swapped)**2))),
                         'source':source(cf4pp),'array_shapes':{'v_mean':list(v.shape),'vr_mean':list(vr.shape)}}
        results['cf4pp']={'outcome':'REFUSED_SOURCE_AXIS_AMBIGUITY','empirical_eligible':False,
            'reason':'Released radial grid and Cartesian projection disagree under published lookup axes; no unprovided permutation repair.',
            'source_documentation':'https://projets.ip2i.in2p3.fr/cosmicflows/retrieve_CF4pp_grid_values.py',
            'diagnostic':discrepancy,'rows':len(ids),'available_rows':0,
            'uncertainty':'released pointwise HMC scatter is not a full covariance'}
    except Exception as exc:results['cf4pp']=unavailable(exc)
    arrays['cf4pp_radial_km_s']=np.full(len(ids),np.nan)
    arrays['cf4pp_status']=np.full(len(ids),'SOURCE_AXIS_UNRESOLVED',dtype='<U48')
    np.savez_compressed(directory/'field_rows.npz',**arrays)
    report={'owner':'obsstat','claim_tier':'C0','scope':'OWNED_FLOW_CONTROLS','transfer_source':'released reconstructions',
        'source_catalogue':source(table_path),'readme_sha256':hashlib.sha256(readme.read_bytes()).hexdigest(),
        'row_identity':'original table4 order, dominant-galaxy PGC group identity','rows':len(ids),'positive_redshift_rows':int(usable.sum()),
        'position_policy':'r_h=published CF4 V3k/100 Mpc/h and published Galactic angles; redshift-position proxy, not inferred true distance',
        'law_status':'NONE; reconstructions can share galaxies, distances and calibration with CF4; no independent likelihood or spatial covariance',
        'caveats':['distance/velocity conversion has no propagated uncertainty law','residual quantiles are descriptive, not confidence intervals',
                   'no observed curl or physical model identification','full CF4 row set retained, including unavailable predictions'],
        'products':results,'rows_artifact':'field_rows.npz'}
    save(directory/'fields.json',report)
    return report


def cmb_controls(directory):
    from obsstat.r8_product_intake import reduce_temperature_map,fit_common_temperature_records
    from common.mes_krylov_completion import krylov16,OrbitChartUnavailable,ordinary_power_bispectrum
    from obsstat.boost_response import project_onto_boost_image
    products={
        'PR3_SMICA':RAW/'planck_data/COM_CMB_IQU-smica_2048_R3.00_full.fits',
        'PR3_COMMANDER':RAW/'planck_data/COM_CMB_IQU-commander_2048_R3.00_full.fits',
        'PR3_NILC':RAW/'planck_pr3_component_controls/COM_CMB_IQU-nilc_2048_R3.00_full.fits',
        'PR3_SEVEM':RAW/'planck_pr3_component_controls/COM_CMB_IQU-sevem_2048_R3.01_full.fits'}
    ready=[];outcomes={}
    for key,path in products.items():
        try:
            reduced=reduce_temperature_map(path,key,path.name)
            ready.append(reduced);outcomes[key]={'outcome':'MEASURED_MAP_CONTROL','valid_pixels':int(reduced.valid.sum())}
            print(key,'reduced:',int(reduced.valid.sum()),'pixels',flush=True)
        except Exception as exc:outcomes[key]=unavailable(exc)
    if not ready:
        report={'products':outcomes,'outcome':'INPUT_UNAVAILABLE','records':[],'empirical_eligible':False}
        save(directory/'cmb.json',report);return report
    records,processing=fit_common_temperature_records(ready)
    payload=[]
    for record in records:
        q,o=record.Q,record.O;denom=float(np.sum(o*o))
        try:packet={'status':'AVAILABLE','value':krylov16(q,o)}
        except OrbitChartUnavailable as exc:packet={'status':'CHART_UNAVAILABLE_TENSOR_RETAINED','reason':str(exc)}
        powers=[float(np.sum(record.retained[a:b]**2)/(2*l+1)) for l,a,b in ((2,0,5),(3,5,12),(4,12,21),(5,21,32))]
        fb=float(np.sum(project_onto_boost_image(q,o)**2)/denom) if denom and np.linalg.norm(q) else None
        payload.append({'sample_id':record.sample_id,'Q_K':q.tolist(),'O_K':o.tolist(),'retained_K':record.retained.tolist(),
            'frame':record.frame,'powers_K2':powers,'f_B':fb,'packet':packet,
            'ordinary_power_bispectrum':ordinary_power_bispectrum(q,o).tolist(),
            'measurement_covariance':None,'full_mv_status':'PENDING_SEPARATE_UNIT_B'})
    np.savez_compressed(directory/'cmb_controls.npz',sample_ids=np.array([r.sample_id for r in records]),
        Q=np.stack([r.Q for r in records]),O=np.stack([r.O for r in records]),
        retained_K=np.stack([r.retained for r in records]),
        reduced_maps_K=np.stack([p.temperature_K for p in ready]),
        common_mask=np.logical_and.reduce([p.valid for p in ready]))
    report={'owner':'obsstat','claim_tier':'C0','scope':'PR3_SAME_SKY_COMPONENT_CONTROLS','transfer_source':'released temperature maps',
        'empirical_eligible':False,'outcome':'DESCRIPTIVE_CONTROL','products':outcomes,'processing':processing,'records':payload,
        'observed_rank':'NOT_EXECUTED_PRODUCT_LAW_UNAVAILABLE','covariance':None,
        'caveats':['same sky and correlated component products; not independent constraints','no release null or beam/correction response supplied',
                   'new extraction method; historical R7 carrier bytes/processing and ranks unchanged','full MV ablation remains separate']}
    save(directory/'cmb.json',report);return report


def render(directory):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    import healpy as hp
    paths=[]
    field_path=directory/'field_rows.npz'
    if field_path.is_file():
        with np.load(field_path,allow_pickle=False) as a:
            fig,axes=plt.subplots(1,2,figsize=(12,4.3))
            radius=a['radius_proxy_hmpc'];ref=a['cf4_published_Vpec_km_s'];bins=np.arange(0,201,25)
            for key,label in [('carrick_2mpp','Carrick 2M++'),('coras_zCMB','CORAS zCMB'),('lilow_2mrs','Lilow 2MRS')]:
                ok=a[key+'_status']=='AVAILABLE_CONTROL';v=a[key+'_radial_km_s']
                axes[0].scatter(radius[ok],v[ok],s=2,alpha=.12,label=f'{label} (n={ok.sum():,})',rasterized=True)
                med=[]
                for low,high in zip(bins[:-1],bins[1:]):
                    keep=ok&(radius>=low)&(radius<high)
                    med.append(float(np.median(v[keep]-ref[keep])) if keep.any() else np.nan)
                axes[1].plot((bins[:-1]+bins[1:])/2,med,'o-',label=label)
            for ax in axes:ax.set_xlabel('Fixed redshift-position radius V3k/100 [Mpc/h]');ax.grid(alpha=.2);ax.legend(fontsize=8)
            axes[0].set_ylabel('Outward released field velocity [km/s]')
            axes[1].set_ylabel('Median(field − published CF4 Vpec) [km/s]')
            fig.suptitle('Owned flow controls at the same CF4 group positions — no likelihood or covariance')
            fig.tight_layout();fig.savefig(directory/'flow_controls.png',dpi=160);plt.close(fig);paths.append('flow_controls.png')
    cmb_path=directory/'cmb_controls.npz'
    if cmb_path.is_file():
        report=json.loads((directory/'cmb.json').read_text())
        with np.load(cmb_path,allow_pickle=False) as a:
            fig,axes=plt.subplots(1,2,figsize=(12,4.2))
            for i,name in enumerate(a['sample_ids']):
                axes[0].plot(np.arange(12),a['retained_K'][i,:12]*1e6,'o-',label=str(name))
            axes[0].set_xticks(range(12));axes[0].set_xlabel('Ordered real coefficients: ell2 (0–4), ell3 (5–11)')
            axes[0].set_ylabel('Measured coefficient [microK]');axes[0].legend(fontsize=8);axes[0].grid(alpha=.2)
            axes[1].bar(range(len(report['records'])),[r['f_B'] for r in report['records']])
            axes[1].set_xticks(range(len(a['sample_ids'])),a['sample_ids'],rotation=25);axes[1].set_ylabel('Boost-image fraction f_B (diagnostic)');axes[1].set_ylim(0,1)
            fig.suptitle('PR3 same-sky components: common mask, joint ell0…5 fit, full Q/O retained')
            fig.tight_layout();fig.savefig(directory/'cmb_coefficients.png',dpi=160);plt.close(fig);paths.append('cmb_coefficients.png')
            if len(a['sample_ids'])>1:
                fig=plt.figure(figsize=(13,3.4));base=a['reduced_maps_K'][0]
                for j,name in enumerate(a['sample_ids'][1:]):
                    delta=(a['reduced_maps_K'][j+1]-base)*1e6;delta=np.where(a['common_mask'],delta,hp.UNSEEN)
                    hp.mollview(delta,fig=fig.number,sub=(1,len(a['sample_ids'])-1,j+1),title=f'{name} − {a["sample_ids"][0]}',unit='microK',cmap='coolwarm')
                fig.savefig(directory/'same_sky_differences.png',dpi=160,bbox_inches='tight');plt.close(fig);paths.append('same_sky_differences.png')
    save(directory/'figures.json',{'owner':'obsstat','scope':'DESCRIPTIVE_OWNED_CONTROLS','claim_tier':'C0','figures':paths,
        'inputs':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in [field_path,cmb_path] if p.is_file()},
        'render_source_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'visual_inspection':'PENDING','caveats':['no empirical p-value/confidence/posterior','missing field rows retained in input with typed status']})


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--run-dir',type=Path,required=True)
    p.add_argument('--part',choices=['fields','cmb','all','render'],default='all');a=p.parse_args()
    a.run_dir.mkdir(parents=True,exist_ok=True)
    if a.part!='render':
        inventory=list(csv.DictReader(INVENTORY.open()))
        expected={'carrick_2mpp','coras_2mrs','lilow_nn_2mrs','cf4_full','planck_pr3_component_controls','planck_data'}
        present={r['name'] for r in inventory}
        if not expected<=present:raise ValueError('required known inventory rows missing')
        for name,action in [('fields',field_controls),('cmb',cmb_controls)]:
            if a.part not in {'all',name}:continue
            if (a.run_dir/(name+'.json')).exists():raise FileExistsError('preserve prior results: choose a new run directory')
            try:action(a.run_dir)
            except Exception as exc:save(a.run_dir/(name+'.json'),unavailable(exc));print(name,unavailable(exc),flush=True)
    render(a.run_dir)


if __name__=='__main__':main()
