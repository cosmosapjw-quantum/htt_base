#!/usr/bin/env python3
"""Workstation R7 scientific executors. Every emitted capability has a receipt.

The public entry point is run_r7_campaign.py. Product readers use the two
existing inventories, named files and selected Git/archive members only.
"""
from __future__ import annotations
import csv
import hashlib
import io
import inspect
import json
import math
import os
from pathlib import Path
import subprocess
import sys
import tarfile
import numpy as np

ROOT=Path(__file__).resolve().parents[2]
for path in (ROOT/'htt/src',ROOT/'htt',ROOT/'htt/htt',ROOT):
    if str(path) not in sys.path:sys.path.insert(0,str(path))
from common.r7_contracts import BranchResult,TensorRecord,json_value,content_id
from common.r7_asset_use import intake_inventory,verify_selected_sources
from common.r7_evidence import cas_evidence_binding,review_evidence_binding,evidence_dependencies
from scripts.observed_runs.run_r7_campaign import _write,_sha,synthesize_campaign

DATA=Path('/mnt/sn850x2t/htt_base_e2e/workdir')
INVENTORY=Path('/home/cosmosapjw/Dropbox/bianchi/htt_base/workdir/asset_inventory_20260907/assets.csv')
EXTERNAL_INVENTORY=Path('/mnt/sn850x2t/htt_base_e2e/inventories/EXTERNAL_ASSETS_20260907T071735Z')
HDF_PYTHON=DATA/'external_fusion_round3_20260722_envs/lowell/bin/python'
RUN_ID='TENSOR-JOINT-R7-20260908'


def _finish(node,details,capabilities=(),outcome='NOT_EVALUATED',reasons=(),extra_evidence=()):
    module_paths={name:str(Path(module.__file__).resolve()) for name,module in sys.modules.items()
        if name.startswith(('common.r7','htt.infer.r7','obsstat.r7','bass.transfer.r7')) and getattr(module,'__file__',None)}
    if any(not Path(path).is_relative_to(ROOT) for path in module_paths.values()):raise ValueError('driver imported a historical installed R7 module')
    details={**details,'actual_driver_module_paths':module_paths}
    artifact=node['_attempt_dir']/'science.json';_write(artifact,details)
    scope=details.get('scope','R7 method/diagnostic scope; no inherited empirical eligibility')
    bindings={c:{'scope':scope,'artifacts':[str(artifact),*map(str,extra_evidence)]} for c in capabilities}
    return BranchResult(node['id'],'COMPLETED_SUCCESS',outcome,tuple(capabilities),evidence=(str(artifact),*map(str,extra_evidence)),
        reasons=tuple(reasons),product_results={**details,'capability_evidence':bindings},
        next_discriminator=details.get('next_discriminator'))


def _tests(node,paths,extra=()):
    command=[sys.executable,'-B','-m','pytest','-o','addopts=','--import-mode=importlib','-q',*paths,*extra]
    process=subprocess.run(command,cwd=ROOT,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,
        env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1','OMP_NUM_THREADS':'1','OPENBLAS_NUM_THREADS':'1',
             'PYTHONPATH':os.pathsep.join(map(str,(ROOT/'htt/htt',ROOT/'htt/src',ROOT/'htt',ROOT)))})
    log=node['_attempt_dir']/'validation.log';log.write_text(process.stdout)
    receipt={'command':command,'exit_code':process.returncode,'log':str(log),'log_sha256':_sha(log),
        'source_python':sys.executable,'test_sources':{p:_sha(ROOT/p) for p in paths if (ROOT/p).is_file()}}
    _write(node['_attempt_dir']/'validation.json',receipt)
    if process.returncode:raise RuntimeError('required numerical validation failed: '+str(log))
    return receipt


def _read_result(results,node_id):
    return results[node_id].product_results


def _isolated(name,fn):
    try:return fn()
    except Exception as exc:return {'product_id':name,'outcome':'INPUT_UNAVAILABLE' if isinstance(exc,FileNotFoundError) else 'VALIDATION_FAILED',
        'reason':f'{type(exc).__name__}: {exc}'}


def source_intake(node,results):
    bindings=json.loads((ROOT/'docs/generated/tensor_joint_r7/source_bindings.json').read_text())
    failed=verify_selected_sources(ROOT,bindings)
    records={r.product_key:r.to_dict() for r in intake_inventory(INVENTORY)}
    # Consume the second supplied inventory's existing receipt, never rescan it.
    external_files=sorted(EXTERNAL_INVENTORY.glob('*.json'))
    external=[{'path':str(p),'sha256':_sha(p)} for p in external_files if p.stat().st_size<2_000_000]
    caps=['SOURCE_BINDINGS']  # resolved per-file dispositions, including unavailable donors
    routing={'pr3_smica':'PR3_INPUT','cf4_full':'CF4_INPUT','desi_bgs_bright_mocks':'DESI_INPUT',
        'jwst_anchors':'JWST_INPUT','wmap9':'SKY_CONTROL_INPUT','cf4_reconstruction':'FLOW_CONTROL_INPUT',
        'desi_compressed':'BACKGROUND_AUX_INPUT','union3':'DISTANCE_AUX_INPUT','hsc':'PROJECTED_AUX_INPUT'}
    for product,cap in routing.items():
        if records[product]['product_locator'] and records[product]['disposition'].value!='UNAVAILABLE_PRODUCT_OR_LAW':caps.append(cap)
    for key,record in records.items():
        if key in {'hsc','kids','act_dr6_kappa','act_dr6_sims','cosmos_web'}:
            record['reason']='Different observable or small-area selection; no normalized lensing/count law or R7 physical response bound in supplied intake.'
        elif key in {'beyondplanck_v2','cosmoglobe_dr1'}:
            record['reason']='Posterior product requires its analysis prior and dependence law; it cannot be used as independent Gaussian temperature draws.'
        elif key in {'wmap7_simulation','quijote','class_observatory'}:
            record['reason']='Release/frequency/observable-specific control; no cross-release covariance or WMAP9/PR3 exchangeability law supplied.'
    return _finish(node,{'asset_uses':records,'source_binding_failures':failed,'selected_source_binding':bindings,
        'external_inventory_receipts':external,'scope':'PRODUCT_KEYED_INTAKE_ONLY'},caps,
        reasons=('Product existence does not award a likelihood or its calibration.',))


def algebra(node,results):
    validation=_tests(node,['tests/r7/test_conventions.py','tests/r7/test_extended_algebra.py'])
    cas=ROOT/'.agent-harness/runs'/RUN_ID/'cas_adjudication.json'
    contract=cas.with_name('CAS_CONTRACT.json')
    cas_data,cas_binding=cas_evidence_binding(ROOT,cas,contract)
    # The separately reused certificate has exact rational block minors; the
    # four-axis contract validates their implication, not a rebuilt operator.
    certificate=ROOT/'docs/generated/tensor_joint_r7/axial_certificate_source.json'
    caps=['ALGEBRA_VERIFIED']
    if cas_binding['eligible']:caps+=['FOUR_AXIS_CAS','CONTINUUM_CERTIFIED']
    return _finish(node,{'validation':validation,'cas':cas_data,'cas_binding':cas_binding,'accepted_certificate':str(certificate),
        'mask_status':'FINITE_MATRIX_IDENTITY_VERIFIED; continuum norm theorem proof uses stated sup norm; pixel error certificate unavailable',
        'cas_scope':'Seven fixed algebra/certificate implications only; no empirical/physical closure or full continuum operator recomputation'},
        caps,extra_evidence=[p for p in [*evidence_dependencies(ROOT,cas,contract),certificate] if p.is_file()])


def donor_integration(node,results):
    # Each named donor product validates and terminates independently. A source
    # binding or optional decoder failure cannot remove another donor product.
    # Recheck at consumption even if the predecessor came from a cache.
    binding=json.loads((ROOT/'docs/generated/tensor_joint_r7/source_bindings.json').read_text())
    current_failures=verify_selected_sources(ROOT,binding)
    failed={p for paths in current_failures.values() for p in paths}
    original=binding['records']
    donor_paths=lambda tag:[r['path'] for r in original if r['donor']==tag]
    catalogue='tests/r7/test_catalogue_laws.py'
    routes=[
      ('krylov','DONOR_KRYLOV',donor_paths('Q'),['tests/r7/test_source_composition.py','tests/common/test_mes_krylov_completion.py'],()),
      ('boost','DONOR_BOOST',donor_paths('B'),['htt/test_wu010_audit_closure.py'],()),
      ('tensor','DONOR_TENSOR',donor_paths('D'),['tests/obsstat/test_mes_directional_moments.py','tests/common/test_mes_directional_state.py'],()),
      ('anchor','DONOR_ANCHOR',donor_paths('A'),['tests/pr_cards/test_pr_254_normalizer_anchor_geometry.py'],
       ('-k','counterexamples_force or benchmark_serialization or zero_denominator_status or gaussian_likelihood_probe or active_module')),
      ('cf4','DONOR_CF4',['htt/obsstat/cf4_current_stack.py','htt/src/common/data_identity.py'],[catalogue],('-k','cf4 or selected_latent')),
      ('desi','DONOR_DESI',['htt/obsstat/desi_successor_formalism.py','scripts/observed_runs/run_desi_bgs_bright.py'],[catalogue],('-k','desi')),
      ('jwst','DONOR_JWST',['htt/obsstat/jwst_distance_consistency.py','scripts/observed_runs/run_jwst_sn.py'],[catalogue],('-k','jwst or student')),
      ('gf','DONOR_GF',[],['research_gates/egs3/tests/test_egs3_axis_e_gf_v8.py','research_gates/egs3/tests/test_egs3_axis_e_fractional_program.py'],()),
      ('dynamics','DONOR_DYNAMICS',[],['htt/bass/collision/test_thomson_pstf.py','htt/bass/transport/test_ver2_geodesics.py','tests/r7/test_physical_providers.py'],()),
      ('processed_error',None,['htt/obsstat/processed_boost_error_envelope.py'],['htt/test_wu011_task7c_error_envelope.py'],())]
    records={};caps=[];evidence=[]
    for name,cap,required,tests,extra in routes:
        sub=dict(node);sub['_attempt_dir']=node['_attempt_dir']/name;sub['_attempt_dir'].mkdir()
        if failed.intersection(required):
            records[name]={'status':'SOURCE_UNAVAILABLE','paths':sorted(failed.intersection(required))};continue
        try:
            validation=_tests(sub,tests,extra)
            records[name]={'status':'PASS','validation':validation,'selected_paths':required}
            evidence.append(validation['log'])
            if cap:caps.append(cap)
        except Exception as exc:
            records[name]={'status':'VALIDATION_FAILED','reason':str(exc),'log':str(sub['_attempt_dir']/'validation.log')}
    return _finish(node,{'donor_capability_records':records,'source_binding_failures':current_failures,
        'selective_port_validation_limits':'The full donor run recorded 10 compatibility/evidence-path omissions after selective porting. These are not established baseline failures; some tests did not reach scientific assertions. Selected route passes do not discharge every donor benchmark obligation.'},
        caps,extra_evidence=evidence)


def radiation(node,results):
    return _finish(node,{'validation':_tests(node,['tests/r7/test_mes_region.py']),
        'physical_status':'First-order geodesic collisionless T3 model; measured derivative jets unavailable'},['MES_TENSOR_MODEL'])


def thermal(node,results):
    from obsstat.r7_cmb_product_response import build_product_response
    validation=_tests(node,['tests/r7/test_cmb_product_response.py'])
    product=dict(product_id='POSITIVE_THERMAL_MONOPOLE',release='R7_SCENARIO',frame='OUTWARD',units='K',
        correction='NONE',channel_convention='BLACKBODY_WEIGHT_ONE',beam='IDENTITY')
    source=dict(source_id='DECLARED_2.7255_K_MONOPOLE',units='K',temperature=lambda n:np.full(len(n),2.7255))
    responses=[build_product_response(product,source,[0.,0.,b],{}) for b in (0.,.0005,.001,.002)]
    return _finish(node,{'validation':validation,'thermal_responses':responses,
        'released_response':'UNAVAILABLE: released correction/channel/selection/covariance operator has not been justified'},['THERMAL_RESPONSE'],'SCENARIO_ONLY')


def law_kernels(node,results):
    return _finish(node,{'validation':_tests(node,['tests/r7/test_gaussian_law.py']),
        'coverage':'Fixed true-parameter residual on known Gaussian support; chi-square covariance rank. No Wilks subtraction.'},['LAW_KERNELS_VERIFIED'])


def _carrier_records(directory):
    from scripts.observed_runs import rebuild_mes_tensor_carriers as donor
    from obsstat.boost_response import project_onto_boost_image
    ledger={};arms={};matrices=donor.harmonic_stf_matrices()
    for name,path in (('paired300',donor.PAIRED),('cmbonly999',donor.CMBONLY)):
        data=donor._blob(ROOT,path,ledger)
        with np.load(io.BytesIO(data),allow_pickle=False) as z:
            rows=np.vstack((z['observed_real_alm'],z['null_real_alm'])) if name=='paired300' else z['carrier_rows'].copy()
            ids=z['row_ids'].copy()
        expected=[donor.OBSERVATION_ID]+([f'FFP10-SMICA-CMBNOISE-{i:05d}' for i in range(300)] if name=='paired300'
            else [f'FFP10-SMICA-CMB-{i:05d}' for i in range(1000) if i!=970])
        if ids.tolist()!=expected:raise ValueError('carrier row identity/order changed')
        q,o,powers=donor.project_carrier(rows,matrices);q*=1e-6;o*=1e-6;rows*=1e-6;powers*=1e-12
        fb=[]
        for a,b in zip(q,o):
            fb.append(float(np.linalg.norm(project_onto_boost_image(a,b))**2/np.linalg.norm(b)**2) if np.linalg.norm(a) and np.linalg.norm(b) else None)
        file=directory/(name+'_tensors.npz')
        np.savez_compressed(file,retained=rows,Q=q,O=o,powers_K2=powers,sample_ids=ids,f_B=np.asarray(fb,dtype=float))
        arms[name]={'artifact':str(file),'sha256':_sha(file),'rows':len(rows),'source_commit':donor.SOURCE_HEAD,
            'units':'K','frame':'GALACTIC','layout':'ORTHONORMAL_REAL_M0_COS_SIN','observed_f_B':fb[0],
            'observed_powers_K2':powers[0].tolist(),'measurement_covariance':None,
            'law_status':'DIAGNOSTIC_ONLY; matched true signal/noise/product likelihood and pool exchangeability unprovided',
            'processing_id':'joint_weighted_l0_l5_fit_then_retain_l2_l5_and_declared_commonization',
            'mask_id':'sha256:34390a5c2d9c1462af87d51a9a3e88971781b23054d923563723531b7f30ea94'}
    metadata_path='docs/generated/planck_pr3_paired300_irrep_carrier/metadata.json'
    metadata=json.loads(donor._blob(ROOT,metadata_path,ledger))
    return {'arms':arms,'source_bindings':ledger,'released_processing_metadata':metadata}


def _wmap_control(directory):
    import healpy as hp
    from astropy.io import fits
    from obsstat.r7_cmb_product_response import pixel_fit_geometry,build_tensor_record
    path=DATA/'raw/wmap_9yr/core/wmap_ilc_9yr_v5.fits'
    with fits.open(path,memmap=True) as h:
        header=h[1].header
        if 'mK' not in header['TUNIT1'] or header['NSIDE']!=512:raise ValueError('WMAP release units/resolution changed')
        source=np.array(h[1].data['TEMPERATURE'],dtype=float)*1e-3
        order=header['ORDERING'].strip()
    sky=hp.ud_grade(source,64,order_in=order,order_out='RING',pess=True)
    n,y=pixel_fit_geometry();valid=np.isfinite(sky)&(sky!=hp.UNSEEN)
    coef,_,rank,_=np.linalg.lstsq(y[valid],sky[valid],rcond=None)
    if rank!=36:raise ValueError('WMAP fit rank deficient')
    meta=dict(sample_id='WMAP9_ILC_OBS',units='K',harmonic_layout='ORTHONORMAL_REAL_M0_COS_SIN',frame='GALACTIC',
        product_id='WMAP9_ILC',release='v5',processing_id='NEST512_TO_RING64_UDGRADE_ALL_L0_L5_LSTSQ',mask_id='FINITE_FULL_SKY')
    record=build_tensor_record(coef[4:],meta,None);file=directory/'wmap9_tensor.npz'
    np.savez_compressed(file,retained=record.retained,Q=record.Q,O=record.O)
    return {'outcome':'SCENARIO_ONLY','source':str(path),'artifact':str(file),'sha256':_sha(file),'units':'K',
        'rank':int(rank),'retained':record.retained,'Q':record.Q,'O':record.O,'valid_pixels':int(valid.sum()),
        'interpretation':'Descriptive WMAP9 native ILC control; release-matched covariance/null unavailable. No WMAP7 calibration transfer.'}


def cmb_records(node,results):
    carrier=_isolated('PR3_CARRIERS',lambda:_carrier_records(node['_attempt_dir']))
    wmap=_isolated('WMAP9_ILC',lambda:_wmap_control(node['_attempt_dir']))
    caps=[]
    if 'arms' in carrier:caps.append('CMB_RECORDS')
    if 'Q' in wmap:caps.append('CMB_CONTROL_RECORDS')
    files=[a['artifact'] for a in carrier.get('arms',{}).values()]
    if 'artifact' in wmap:files.append(wmap['artifact'])
    return _finish(node,{'carriers':carrier,'wmap9':wmap},caps,'SCENARIO_ONLY',extra_evidence=files)


def cf4_records(node,results):
    from astropy.table import Table
    directory=DATA/'raw/cf4_full';tables={}
    for number in (2,3,4):
        path=directory/f'table{number}.dat';t=Table.read(path,format='ascii.cds',readme=directory/'ReadMe')
        names=['PGC','Vcmb','DM','e_DM','GLON','GLAT'] if number==2 else (['1PGC','DMzp','DMav','e_DMav','Vcmb','GLON','GLAT'] if number==3 else ['1PGC','Dist','V3k','Vpec','GLON','GLAT'])
        cols={n:np.asarray(t[n],dtype=float) for n in names}
        output=node['_attempt_dir']/f'cf4_table{number}.npz';np.savez_compressed(output,**cols)
        tables[str(number)]={'source':str(path),'rows':len(t),'columns':names,'units':{n:str(t[n].unit) for n in names},
            'artifact':str(output),'sha256':_sha(output),'order':'original CDS table order retained',
            'summary':{n:{'minimum':float(np.nanmin(v)),'median':float(np.nanmedian(v)),'maximum':float(np.nanmax(v))} for n,v in cols.items() if n not in {'PGC','1PGC'}}}
    return _finish(node,{'tables':tables,'validation':_tests(node,['tests/r7/test_catalogue_laws.py']),
        'law_status':'INPUT_UNAVAILABLE: no full covariance in original selected group order; conditional affine adapter remains usable when supplied',
        'next_discriminator':'Provide the source-bound full CF4 group covariance and its declared sampling/conditioning law.'},['CF4_RECORDS'],'INPUT_UNAVAILABLE',
        extra_evidence=[v['artifact'] for v in tables.values()])


def _compressed_bao(directory):
    path=DATA/'raw/desi_dr1_fullshape_bgs_bright_v1.2/likelihood/likelihood_bao-recon_syst_BGS_BRIGHT-21.5_GCcomb_z0.1-0.4.h5'
    code="""import h5py,json,sys
with h5py.File(sys.argv[1]) as f:
 g=f['observable/baorecon'];q=g['qiso']
 print(json.dumps(dict(likelihood_name=f['name'][()].decode(),parameter='qiso',observed=q['value'][()].tolist(),covariance=f['covariance/value'][()].tolist(),window=f['window/value'][()].tolist(),zeff=float(g.attrs['zeff']),DV_over_rd_fid=float(q.attrs['DV_over_rd_fid']))))
"""
    p=subprocess.run([str(HDF_PYTHON),'-c',code,str(path)],check=True,capture_output=True,text=True)
    payload=json.loads(p.stdout);payload.update(source_id='DESI_DR1_FULLSHAPE_BGS_v1.2:'+_sha(path),source_path=str(path),
        decoder=str(HDF_PYTHON),alternative='syst selected in implementation; stat-only is not multiplied')
    from htt.infer.r7_desi_law import build_compressed_bao_law
    law=build_compressed_bao_law(payload)
    _write(directory/'compressed_bao.json',payload)
    return {'payload':payload,'law_scope':json_value(law.scope),'law_specification_id':law.specification_id,
        'artifact':str(directory/'compressed_bao.json'),'eligibility':'CONDITIONAL_RELEASED_GAUSSIAN_SUMMARY_ONLY',
        'interpretation':'Background qiso likelihood, conditional on released Gaussian compression. True catalogue coverage and angular response unverified.'}


def desi_records(node,results):
    from astropy.io import fits
    raw=[]
    for cap in ('NGC','SGC'):
        path=DATA/f'raw/desi_dr1_mocks/observed/v1.5/BGS_BRIGHT-21.5_{cap}_clustering.dat.fits'
        def read(path=path):
            with fits.open(path,memmap=True) as h:
                table=h[1].data;names=list(h[1].columns.names)
                return {'source':str(path),'rows':len(table),'columns':names,'z_range':[float(np.min(table['Z'])),float(np.max(table['Z']))],
                    'missing_P_columns':sorted({'R_MAG_APP','R_MAG_ABS'}-set(names)),
                    'law_status':'P sample/selection and tomographic random normalization must be bound before raw 18-vector execution'}
        raw.append(_isolated('DESI_RAW_'+cap,read))
    compressed=_isolated('DESI_COMPRESSED',lambda:_compressed_bao(node['_attempt_dir']))
    caps=['BACKGROUND_CONTROL_RECORDS'] if 'payload' in compressed else []
    if 'payload' in compressed:caps.append('BACKGROUND_LAW')
    if any('rows' in r for r in raw):caps.append('DESI_RECORDS')
    return _finish(node,{'raw':raw,'compressed':compressed,'validation':_tests(node,['tests/r7/test_catalogue_laws.py']),
        'scope':'Raw BGS P adapter separate from released compressed Gaussian background likelihood'},caps,'CONDITIONAL_BOUND' if 'payload' in compressed else 'INPUT_UNAVAILABLE',
        extra_evidence=[compressed['artifact']] if 'artifact' in compressed else [])


def jwst_records(node,results):
    from astropy.io import fits
    manifest_path=DATA/'raw/jwst_anchors/jwst_anchors_manifest.json';manifest=json.loads(manifest_path.read_text())
    datasets=[]
    for receipt in manifest['transcription_receipts']:
        if 'host' not in receipt['exact_cells'][0]:continue
        source=next(v for v in manifest['fetched'] if v['label']==receipt['source_label'])
        archive=manifest_path.parent/source['path']
        with tarfile.open(archive) as tar:
            raw=tar.extractfile(receipt['source_member']).read()
        if 'sha256:'+hashlib.sha256(raw).hexdigest()!=receipt['source_member_sha256']:raise ValueError('JWST immutable source member changed')
        rows=receipt['exact_cells'];delta=np.array([float(r['mu_a_mag'])-float(r['mu_b_mag']) for r in rows])
        variances=np.array([float(r['sigma_a_mag'])**2+float(r['sigma_b_mag'])**2 for r in rows])
        weights=1/variances;mean=float(weights@delta/weights.sum());se=float(1/np.sqrt(weights.sum()))
        datasets.append({'dataset':receipt['dataset'],'rows':rows,'host_count':len(rows),'delta_mag':delta,
            'source_member':receipt['source_member'],'source_member_sha256':receipt['source_member_sha256'],
            'descriptive_mean_mag':float(delta.mean()),'scenario_fitted_offset_mag':mean,'scenario_standard_error_mag':se,
            'scenario_residual_quadratic':float(np.sum((delta-mean)**2/variances)),
            'law':'Independent Gaussian quoted measurement errors, zero cross-host/cross-method covariance ASSUMED SCENARIO',
            'outcome':'SCENARIO_ONLY','physical_response':'same-host geometry cancels; no competitor amplitude inferred from preparation'})
    union=DATA/'rrss_observational_inputs/union3_release-main/mu_mat_union3_cosmo=2_mu.fits'
    def read_union():
        with fits.open(union,memmap=False) as h:matrix=np.array(h[0].data)
        return {'source':str(union),'shape':matrix.shape,'finite':bool(np.isfinite(matrix).all()),
            'outcome':'INPUT_UNAVAILABLE','reason':'Matrix meaning, units and ordered distance/redshift likelihood are not specified by the inspected FITS header; no angular reconstruction.'}
    u=_isolated('UNION3',read_union)
    return _finish(node,{'jwst':datasets,'source_manifest':str(manifest_path),'source_manifest_sha256':_sha(manifest_path),
        'union3':u,'validation':_tests(node,['tests/r7/test_catalogue_laws.py'])},['JWST_RECORDS','JWST_SCENARIO','AUX_DISTANCE_RECORDS'],
        'SCENARIO_ONLY')


def _bao_law(results):
    from htt.infer.r7_desi_law import build_compressed_bao_law
    return build_compressed_bao_law(results['R7-08'].product_results['compressed']['payload'])


def joint(node,results):
    from htt.infer.r7_joint_experiment import compose_joint_law,compare_p0_p1
    law=_bao_law(results);partition=compose_joint_law([law],[],None)
    direct=compare_p0_p1(law,[1.],[[1.]],'RELEASED_QISO_SCALAR_COLUMN',('delta_qiso',))
    return _finish(node,{'validation':_tests(node,['tests/r7/test_joint_experiment.py']),
        'scope':json_value(law.scope),'admitted_laws':[json_value(law.scope)],'joint_components':1,
        'P0_P1_before_provider_execution':direct,'conditioning_target':law.conditioning_target,
        'unresolved_cross_links':'No calibrated CF4/JWST/CMB marginal law; no product multiplication',
        'fixed_family_alpha_allocation':{'DESI_COMPRESSED':.05},'partition_law_count':len(partition.admitted_laws)},
        ['ADMITTED_EXPERIMENTS','SUBSET_LAWS'],'CONDITIONAL_BOUND')


def shape(node,results):
    from obsstat.r7_tensor_orbit import orbit_pool_scores
    from common.mes_krylov_completion import krylov16,reconstruct_krylov16,OrbitChartUnavailable,OrbitInputError
    arms=results['R7-06'].product_results['carriers']['arms'];pools={}
    for name,arm in arms.items():
        with np.load(arm['artifact'],allow_pickle=False) as z:
            records=[TensorRecord(str(s),row,q,o,'GALACTIC',name,'PR3',arm['processing_id'],mask_id=arm['mask_id'])
                for s,row,q,o in zip(z['sample_ids'],z['retained'],z['Q'],z['O'])]
        recovery=[]
        for record in records:
            item={'sample_id':record.sample_id}
            try:
                packet=krylov16(record.Q,record.O);qrep,orep=reconstruct_krylov16(packet);replayed=krylov16(qrep,orep)
                item.update(status='RECONSTRUCTED',condition=packet['measured_k_condition'],
                    packet_replay_error=float(np.linalg.norm(np.asarray(packet['values'])-replayed['values'])),
                    Q_amplitude_error_K=abs(np.linalg.norm(qrep)-np.linalg.norm(record.Q)),
                    O_amplitude_error_K=abs(np.linalg.norm(orep)-np.linalg.norm(record.O)))
            except OrbitChartUnavailable as exc:item.update(status='CHART_UNAVAILABLE',reason=str(exc))
            except OrbitInputError as exc:item.update(status='NUMERICALLY_UNRESOLVED',reason=str(exc))
            recovery.append(item)
        recovery_path=node['_attempt_dir']/(name+'_packet_recovery.json');_write(recovery_path,recovery)
        pool=orbit_pool_scores(records,math.ceil(math.sqrt(len(records)-1)),1e-5,1e-5,1e-5)
        path=node['_attempt_dir']/(name+'_scores.json');_write(path,pool)
        pools[name]={'artifact':str(path),'packet_recovery_artifact':str(recovery_path),'rows':len(records),'resolved_rows':pool.row_status.count('RESOLVED_INTERVAL'),
            'k':pool.k,'method_id':pool.method_id,'outcome':'NUMERICALLY_UNRESOLVED' if None in pool.scores else 'SCENARIO_ONLY',
            'reason':'Complete symmetric interval pool; exact ranks withheld when enclosures overlap'}
    return _finish(node,{'pools':pools,'validation':_tests(node,['tests/r7/test_tensor_orbit.py']),
        'scope':'q0=o0=1e-5 K; k=ceil(sqrt(N)); fixed symmetric resource policy; no product calibration'},['SHAPE_METHOD'],
        'NUMERICALLY_UNRESOLVED',extra_evidence=[f for p in pools.values() for f in (p['artifact'],p['packet_recovery_artifact'])])


def high_source(node,results):
    from htt.infer.r7_high_source import cancellation_cost
    from scripts.observed_runs.r7_scenarios import high_source_regions,finite_mask_scenario,mes_scenarios
    costs=[]
    for eps in (1.,.1,.01,.001):
        cost=cancellation_cost([[eps]],[[1.]],[1.],0.)
        costs.append({'epsilon':eps,'cost':json_value(cost)})
    return _finish(node,{'validation':_tests(node,['tests/r7/test_high_source.py']),'mask_cost_scenario':costs,'H0_H3_regions':high_source_regions(),'finite_mask':finite_mask_scenario(),'MES_scenarios':mes_scenarios(),
        'scope':'Declared finite Gaussian/ellipsoid linear scenarios; no observed high-source budget inferred'},['HIGH_SOURCE_METHODS'],'SCENARIO_ONLY')


def mes(node,results):
    return _finish(node,{'validation':_tests(node,['tests/r7/test_mes_region.py']),
        'law_scope':json_value(_bao_law(results).scope),'jet_status':'MISSING_RADIATION_JET',
        'physical_projection':'UNDEFINED: the admitted qiso-only background law supplies no T3 radiation jet; generic same-state method verified'},
        (), 'INPUT_UNAVAILABLE',reasons=('No supported radiation-jet law for this admitted background experiment.',))


def depth(node,results):
    from htt.infer.r7_depth_response import depth_response
    z=np.linspace(.01,.3,60);directions=np.tile([1.,0.,0.],(len(z),1))
    r=depth_response(z,directions,dict(source_id='DECLARED_FLAT_OM0.3_H070',spatial_curvature=0,
        H=lambda z:70*np.sqrt(.3*(1+z)**3+.7)),dict(redshift='OBSERVED',direction='OUTWARD',velocity_units='v/c',maximum_velocity_frame_shift=1e-5))
    return _finish(node,{'validation':_tests(node,['tests/r7/test_joint_experiment.py']),'z':z,
        'observer_kernel':r.observer_kernel,'source_kernel':r.source_kernel,'scope':'Restricted flat FLRW low-speed scenario; no supplied cross-probe calibration link'},
        ['DEPTH_CALIBRATION_METHOD'],'SCENARIO_ONLY')


def restricted_provider(node,results):
    return _finish(node,{'validation':_tests(node,['tests/r7/test_physical_providers.py']),
        'outcome':'INPUT_UNAVAILABLE','reason':'Exact review87 freestream.py/Bose-Einstein/Jacobi donor members absent in named inventory; R3 adaptation and physical validation remain unexecuted'},(), 'INPUT_UNAVAILABLE')


def external_provider(node,results):
    return _finish(node,{'validation':_tests(node,['tests/r7/test_physical_providers.py']),
        'reason':'No actual supported external reference-mode outputs found; native adapter stays unavailable'},(), 'INPUT_UNAVAILABLE')


def model_comparison(node,results):
    from htt.infer.r7_joint_experiment import compare_p0_p1
    law=_bao_law(results)
    comparison=compare_p0_p1(law,[1.],[[1.]],'RELEASED_QISO_SCALAR_COLUMN',('delta_qiso',))
    return _finish(node,{'scope':json_value(law.scope),'P0':'released fiducial qiso=1','P1':'free positive scalar qiso',
        'comparison':comparison,'physical_provider_status':'R3 and external anisotropic transfer unavailable; qiso is a background estimand'},
        ['PHYSICAL_MODEL_METHODS'],'CONDITIONAL_BOUND')


def calibration(node,results):
    from htt.infer.r7_calibration import gaussian_operational_stress,registered_gaussian_cells
    validation=_tests(node,['tests/r7/test_calibration_scopes.py'])
    stress=gaussian_operational_stress(registered_gaussian_cells())
    exact=[]
    if 'R7-10' in results and 'ADMITTED_EXPERIMENTS' in results['R7-10'].capabilities:
        law=_bao_law(results);method,record=_calibrated_bao(law,stress)
        exact.append({'scope':json_value(record.scope),'law_specification_id':record.law_specification_id,
            'method_implementation_id':record.method_implementation_id,'supported_domain_id':record.supported_domain_id,
            'mechanism':record.mechanism,'validity':record.validity,'conditioning_target':record.conditioning_target,
            'numerical_obligations':record.numerical_obligations,'evidence':record.evidence})
    return _finish(node,{'validation':validation,'operational_cells':stress,'calibrations':exact,
        'scope':'Synthetic Gaussian cells and exact acceptance proof for the explicitly conditional released qiso law; product pool laws separate'},
        ['CALIBRATED_METHODS'] if exact else [],'CONDITIONAL_BOUND' if exact else 'SCENARIO_ONLY')


def _calibrated_bao(law,stress=()):
    from htt.infer.r7_calibration import GaussianMethod,calibrate_method
    method=GaussianMethod(dict(statistic='FULL_RESIDUAL_CHISQUARE_WITH_SUPPORT',alpha=.05,nuisance_policy='FIXED_RELEASED_SUMMARY',
        fitting_procedure='NONE_FOR_ACCEPTANCE;P1_FREE_QISO_REPORTED_SEPARATELY',selection_procedure='RELEASED_BGS_BRIGHT_SYST_ONLY',
        null_parameter=[1.],hypothesis_id='QISO_EQUALS_RELEASED_FIDUCIAL_ONE'))
    record=calibrate_method(method,law,dict(mechanism='EXACT_ACCEPTANCE_PROOF',proof_source=str(ROOT/'htt/htt/htt/infer/r7_confidence.py')),stress)
    return method,record


def observed(node,results):
    from htt.infer.r7_calibration import run_observed_scope
    from scipy.stats import norm
    law=_bao_law(results);method,record=_calibrated_bao(law)
    serialized=results['R7-18'].product_results.get('calibrations',())
    matching=[r for r in serialized if r.get('scope')==json_value(record.scope) and r.get('law_specification_id')==record.law_specification_id
        and r.get('method_implementation_id')==record.method_implementation_id and r.get('supported_domain_id')==record.supported_domain_id
        and r.get('conditioning_target')==record.conditioning_target and r.get('mechanism')==record.mechanism and r.get('validity')==record.validity]
    if len(matching)!=1:raise ValueError('R7-18 has no unique calibration matching the full observed scope, implementation and domain')
    actual=run_observed_scope(method,law,record);z=norm.ppf(.975);se=float(np.sqrt(law.covariance[0,0]));q=float(law.observed[0])
    interval=[max(0.,q-z*se),q+z*se];fid=law.specification['fiducial']
    scope={'scope':json_value(record.scope),'empirical':True,'outcome':'CONDITIONAL_BOUND','data_estimate_qiso':q,
        'qiso_CI95':interval,'DV_over_rd':q*fid,'DV_over_rd_CI95':[v*fid for v in interval],
        'acceptance_of_fiducial':json_value(actual.product_results['acceptance']),
        'conditioning_target':law.conditioning_target,'uncertainty_type':'CONFIDENCE_CONDITIONAL_ON_RELEASED_GAUSSIAN_SUMMARY',
        'scope_limit':'This exact interval covers under the declared fixed Gaussian summary model. True raw-catalogue coverage has not been independently established.',
        'prior':None,'physical_identification':None}
    return _finish(node,{'scope_results':[scope],'scope':json_value(record.scope),'calibration_identity':record.law_specification_id},
        ['OBSERVED_RESULTS'],'CONDITIONAL_BOUND')


def negative(node,results):
    synthesis=synthesize_campaign(results)
    return _finish(node,{'negative_and_unresolved':[r for r in synthesis.node_outcomes if r['scientific_outcome'] in
        {'INPUT_UNAVAILABLE','VALIDATION_FAILED','NONIDENTIFIED','NUMERICALLY_UNRESOLVED'}],
        'scope_limits':['No native Bianchi family identification','No true PR3 product likelihood or exchangeable full-shape rank calibration',
        'No full CF4 covariance','JWST cross-method/host covariance missing','R3 review87 source absent','External reference transfer absent'],
        'next_discriminator':'Supply the exact full CF4 group covariance and sampling-law sidecar; this enables an independent conditional affine branch.'},['NEGATIVE_RESULTS'])


def comparison(node,results):
    import copy
    assets=copy.deepcopy(results['R7-00'].product_results.get('asset_uses',{}))
    for record in assets.values():record['execution_status']='INVENTORY_ONLY'
    for key,parent in [('pr3_smica','R7-06'),('ffp10','R7-06'),('wmap9','R7-06'),('cf4_full','R7-07'),
                       ('desi_bgs_bright_mocks','R7-08'),('jwst_anchors','R7-09'),('union3','R7-09')]:
        if key in assets and parent in results:
            assets[key]['execution_status']='PRODUCT_SPECIFIC_READ_OR_ANALYSIS';assets[key]['result_evidence']=results[parent].evidence
    if 'jwst_anchors' in assets:
        assets['jwst_anchors'].update(disposition='SCENARIO_ONLY',units='mag',reason='Source-verified host differences; fitted offsets assume independent quoted Gaussian errors. Shared covariance unavailable.')
    compressed=results.get('R7-08')
    if compressed and 'BACKGROUND_LAW' in compressed.capabilities:
        law=_bao_law(results)
        assets['desi_compressed'].update(disposition='QUALIFIED_CONDITIONAL_LAW',law_scope=law.scope.identity,
            uncertainty_law=law.conditioning_target,units='dimensionless qiso',frame='NONANGULAR_BACKGROUND_COMPRESSION',
            execution_status='CONDITIONAL_LAW_EXECUTED',reason='Official syst compressed qiso Gaussian model; true raw-catalogue coverage unverified.',
            result_evidence=compressed.evidence)
    return _finish(node,{'asset_uses':assets,'scope_results':[r for p in results.values() for r in p.product_results.get('scope_results',())],
        'data_contributions':{i:{'capabilities':r.capabilities,'outcome':r.scientific_outcome} for i,r in results.items() if i in {'R7-06','R7-07','R7-08','R7-09','R7-10'}},
        'shared_calibration_information_oracle':{'old_information':0.,'new_information':.2,'variance':5.,'scope':'analytic independent-noise scalar scenario only'},
        'alternative_laws':'never multiply stat-only and syst compressed DESI alternatives, or unknown-dependent products'},['COMPARISON_RESULTS'])


def figures(node,results):
    from scripts.observed_runs.r7_report import render_figures
    products=render_figures(node['_attempt_dir'],results)
    review_path=node['_run_dir']/'visual_review.json'
    review=json.loads(review_path.read_text()) if review_path.exists() else {}
    reviewed=review.get('status')=='PASS' and all(review.get('figures',{}).get(Path(f['path']).name)==f['sha256'] for f in products['figures'])
    if reviewed:products['visual_audit']='PASS_BOUND_TO_IMAGE_CONTENT'
    return _finish(node,products,['FIGURE_REVIEW'] if reviewed else [],
        reasons=() if reviewed else ('Rendered figures require the separately recorded visual and source audit before figure-review capability.',),
        extra_evidence=[f['path'] for f in products['figures']]+([review_path] if reviewed else []))


def audit(node,results):
    path=node['_run_dir']/'independent_review.json'
    if not path.exists():return _finish(node,{'audit_status':'NOT_EXECUTED','reason':'Independent reviews pending'},(), 'NOT_EVALUATED')
    review,binding=review_evidence_binding(ROOT,path)
    caps=['FINAL_AUDIT'] if binding['eligible'] else []
    return _finish(node,{'independent_review':review,'review_binding':binding},caps,'NOT_EVALUATED',
        extra_evidence=[p for p in evidence_dependencies(ROOT,path) if p.is_file()])


def manuscript(node,results):
    from scripts.observed_runs.r7_report import write_manuscript
    package=write_manuscript(node['_attempt_dir'],results)
    return _finish(node,package,['MANUSCRIPT_PACKAGE'] if package['build_status']=='PASS' else [],
        extra_evidence=package['artifacts'])


def conclusion(node,results):
    synthesis=synthesize_campaign(results)
    return _finish(node,{'conclusion':json_value(synthesis),'next_discriminator':synthesis.missing_discriminators[0] if synthesis.missing_discriminators else None},
        ['CAMPAIGN_CONCLUSION'])


def campaign_executors(root,run_dir):
    from scripts.observed_runs.r7_mlflow import configured_tracer
    functions=[source_intake,algebra,donor_integration,radiation,thermal,law_kernels,cmb_records,cf4_records,desi_records,jwst_records,
        joint,shape,high_source,mes,depth,restricted_provider,external_provider,model_comparison,calibration,observed,
        negative,comparison,figures,audit,manuscript,conclusion]
    executors={f'R7-{i:02d}':fn for i,fn in enumerate(functions)}
    # Source slices and exact local dependencies define the affected resume set.
    common=[ROOT/'htt/src/common/r7_contracts.py']
    base='htt/htt/htt/infer/'
    module_names={
      0:['htt/src/common/r7_asset_use.py','docs/generated/tensor_joint_r7/source_bindings.json'],
      1:['htt/src/common/mes_krylov_completion.py','htt/obsstat/boost_response.py'],
      2:[r['path'] for r in json.loads((ROOT/'docs/generated/tensor_joint_r7/source_bindings.json').read_text())['records']]+[
          'htt/bass/background/bi_continuation/dynamics.py','htt/bass/transport/geodesics.py','htt/bass/collision/thomson_pstf.py','htt/obsstat/egs3_gf_interval_v8.py'],
      3:['htt/src/common/r7_radiation_jet.py',base+'r7_mes_region.py',base+'r7_confidence.py',base+'r7_gaussian_law.py'],
      4:['htt/obsstat/r7_cmb_product_response.py','htt/obsstat/lorentz_sky_pullback.py'],
      5:[base+'r7_gaussian_law.py',base+'r7_confidence.py'],
      6:['htt/obsstat/r7_cmb_product_response.py','htt/obsstat/boost_response.py','scripts/observed_runs/rebuild_mes_tensor_carriers.py'],
      7:[base+'r7_cf4_law.py',base+'r7_gaussian_law.py','htt/obsstat/cf4_current_stack.py'],
      8:[base+'r7_desi_law.py',base+'r7_gaussian_law.py','htt/obsstat/desi_successor_formalism.py'],
      9:[base+'r7_jwst_law.py',base+'r7_gaussian_law.py','htt/obsstat/jwst_distance_consistency.py'],
      10:[base+'r7_joint_experiment.py',base+'r7_gaussian_law.py',base+'r7_desi_law.py'],
      11:['htt/obsstat/r7_tensor_orbit.py','htt/src/common/mes_krylov_completion.py'],
      12:[base+'r7_high_source.py',base+'r7_gaussian_law.py','scripts/observed_runs/r7_scenarios.py',
          'htt/src/common/r7_radiation_jet.py',base+'r7_mes_region.py',base+'r7_confidence.py'],
      13:['htt/src/common/r7_radiation_jet.py',base+'r7_mes_region.py',base+'r7_confidence.py',base+'r7_gaussian_law.py'],
      14:[base+'r7_depth_response.py',base+'r7_joint_experiment.py'],
      15:['htt/bass/transfer/r7_benchmark_provider.py','htt/bass/background/bi_continuation/dynamics.py'],
      16:['htt/bass/transfer/r7_external_provider.py'],
      17:[base+'r7_joint_experiment.py',base+'r7_gaussian_law.py',base+'r7_desi_law.py',
          'htt/bass/transfer/r7_external_provider.py','htt/bass/transfer/r7_benchmark_provider.py'],
      18:[base+'r7_calibration.py',base+'r7_gaussian_law.py',base+'r7_desi_law.py'],
      19:[base+'r7_calibration.py',base+'r7_gaussian_law.py',base+'r7_desi_law.py'],
      22:['scripts/observed_runs/r7_report.py'],24:['scripts/observed_runs/r7_report.py']}
    sources={key:common+[ROOT/p for p in module_names.get(i,())] for i,key in enumerate(executors)}
    # Pins, optional evidence and its named source identities must participate
    # even when absent, so arrival can reopen a previously terminal branch.
    manifest=ROOT/'docs/generated/tensor_joint_r7/source_bindings.json'
    donor_files=[ROOT/r['path'] for r in json.loads(manifest.read_text())['records']]
    sources['R7-00']+=donor_files
    sources['R7-02'].append(manifest)
    cas=ROOT/'.agent-harness/runs'/RUN_ID/'cas_adjudication.json'
    sources['R7-01']+=evidence_dependencies(ROOT,cas,cas.with_name('CAS_CONTRACT.json'))
    sources['R7-23']+=evidence_dependencies(ROOT,run_dir/'independent_review.json')
    for key in ('R7-01','R7-23'):
        sources[key].append(ROOT/'htt/src/common/r7_evidence.py')
    helpers={6:[_carrier_records,_wmap_control],8:[_compressed_bao],10:[_bao_law],13:[_bao_law],17:[_bao_law],
        18:[_bao_law,_calibrated_bao],19:[_bao_law,_calibrated_bao],21:[_bao_law]}
    inputs={key:{'source_design':'89a9a901e950cb186dcfedb95a250493fe4fd6fa',
        'executor_source':content_id([inspect.getsource(f) for f in [fn,_finish,_tests,_isolated,*helpers.get(i,())]]),
        'environment':{'python':sys.version,'interpreter':sys.executable,'numpy':np.__version__}}
        for i,(key,fn) in enumerate(executors.items())}
    # Test source changes also invalidate the specific method validation receipt.
    for i,fn in enumerate(functions):
        import re
        for name in re.findall(r"['\"]([^'\"]+(?:test_[^'\"]+|test[^'\"]*)\.py)['\"]",inspect.getsource(fn)):
            path=ROOT/name
            if path.is_file():sources[f'R7-{i:02d}'].append(path)
    inputs['R7-00'].update(inventory_sha256=_sha(INVENTORY),external_inventory=str(EXTERNAL_INVENTORY))
    data_files={6:[DATA/'raw/wmap_9yr/core/wmap_ilc_9yr_v5.fits'],
      7:[DATA/'raw/cf4_full'/name for name in ('ReadMe','table2.dat','table3.dat','table4.dat')],
      8:[DATA/'raw/desi_dr1_fullshape_bgs_bright_v1.2/likelihood/likelihood_bao-recon_syst_BGS_BRIGHT-21.5_GCcomb_z0.1-0.4.h5']+
        [DATA/f'raw/desi_dr1_mocks/observed/v1.5/BGS_BRIGHT-21.5_{cap}_clustering.dat.fits' for cap in ('NGC','SGC')],
      9:[DATA/'raw/jwst_anchors'/name for name in ('jwst_anchors_manifest.json','arxiv_2408.06153.src.tar.gz','arxiv_2509.01667.src.tar.gz')]+
        [DATA/'rrss_observational_inputs/union3_release-main/mu_mat_union3_cosmo=2_mu.fits']}
    for i,paths in data_files.items():
        inputs[f'R7-{i:02d}']['named_source_file_state']={str(p):{'bytes':p.stat().st_size,'mtime_ns':p.stat().st_mtime_ns}
            if p.exists() else {'status':'MISSING'} for p in paths}
    review=run_dir/'independent_review.json';inputs['R7-23']['review_sha256']=_sha(review) if review.exists() else None
    visual=run_dir/'visual_review.json';inputs['R7-22']['visual_review_sha256']=_sha(visual) if visual.exists() else None
    tracer,status=configured_tracer();_write(run_dir/'tracing_status.json',status)
    return executors,inputs,sources,tracer
