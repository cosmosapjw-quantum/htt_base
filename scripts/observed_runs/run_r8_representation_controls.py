#!/usr/bin/env python3
"""Fixed mock2 and observed full-MV/lossy-summary controls; no product ranks."""
from __future__ import annotations
import argparse
from fractions import Fraction as F
import hashlib
import itertools
import json
import math
from pathlib import Path
import sys
import time
import numpy as np
ROOT=Path(__file__).resolve().parents[2]
for path in (ROOT,ROOT/'htt',ROOT/'htt/src',ROOT/'htt/htt'):sys.path.insert(0,str(path))
from obsstat.r8_multipole_vectors import tensor_to_mv,mv_to_tensor
from obsstat.r8_orbit_bounds import initialize_pool,_sqrt
from obsstat.boost_response import quadrupole_boost_octupole,project_onto_boost_image
from common.mes_krylov_completion import krylov16,ordinary_power_bispectrum,OrbitChartUnavailable
from r8_mocks import stf_basis

SCALE=F(1,100000)


def encode(x):
    if isinstance(x,F):return {'numerator':x.numerator,'denominator':x.denominator}
    if isinstance(x,np.ndarray):return x.tolist()
    if isinstance(x,np.generic):return x.item()
    raise TypeError(type(x).__name__)


def write(path,x):path.write_text(json.dumps(x,default=encode,indent=2,allow_nan=False)+'\n')


def outward(x,direction):
    y=float(x)
    return float(np.nextafter(y,direction)) if (F(y)>x if direction<0 else F(y)<x) else y


def witness():
    q=np.diag([-1.,0.,1.])*1e-5;o=np.zeros((3,3,3))
    for indices,value in zip(itertools.combinations_with_replacement(range(3),3),(1,0,0,-2,1,1,1,-1,-1,1)):
        for index in set(itertools.permutations(indices)):o[index]=value*1e-5
    return q,o


def synthetic():
    rng=np.random.default_rng(81004);bq,bo=stf_basis();rows=[];ids=[]
    # Ten frozen random base tensors, with the same quadrupole and octupole in
    # each amplitude stratum. These are representation fixtures, not null skies.
    for i in range(10):
        q=np.einsum('a,aij->ij',rng.normal(size=5)*1e-5,bq)
        o=np.einsum('a,aijk->ijk',rng.normal(size=7)*1e-5,bo)
        for factor in (0,1,2):rows.append((q,o*factor));ids.append(f'mock2-{i:02}-O{factor}')
        rows.append((q,quadrupole_boost_octupole(q,[.1,0,0])));ids.append(f'mock2-{i:02}-boost')
    q,o=witness();r=np.array([[0.,-1,0],[1,0,0],[0,0,1]])
    rows.extend([(q,o),(q,-o),(q,np.einsum('ia,jb,kc,abc->ijk',r,r,r,o))]);ids.extend(['rational-witness','rational-parity','rational-relative-alignment'])
    repeated=np.tile([1.,0,0],(3,1))
    rows.append((mv_to_tensor(1e-5,repeated[:2],2),mv_to_tensor(1e-5,repeated,3)));ids.append('coincident-vectors')
    rows.append((np.zeros((3,3)),np.zeros((3,3,3))));ids.append('zero-tensors')
    return ids,rows


def summary(q,o,conversions):
    try:packet={'status':'AVAILABLE','value':krylov16(q,o)}
    except (OrbitChartUnavailable,ValueError) as exc:packet={'status':'UNAVAILABLE_ORIGINAL_TENSOR_RETAINED','reason':str(exc)}
    nq,no=float(np.linalg.norm(q)),float(np.linalg.norm(o))
    fb=float(np.sum(project_onto_boost_image(q,o)**2)/np.sum(o*o)) if nq and no else None
    v=np.einsum('ijk,jk->i',o/float(SCALE),q/float(SCALE));qd=q/float(SCALE)
    chi=float(np.linalg.det(np.column_stack((v,qd@v,qd@qd@v))))
    cq,co=conversions
    alignment=sorted(abs(cq.vectors@co.vectors.T).ravel().tolist()) if cq.vectors is not None and co.vectors is not None else None
    return {'power_Q_frobenius_K2':nq*nq,'power_O_frobenius_K2':no*no,'f_B':fb,
            'ordinary_power_bispectrum':ordinary_power_bispectrum(q,o).tolist(),
            'packet':packet,'normalized_mv_cross_alignment':alignment,'signed_chi':chi,
            'method_ids':{'full_mv':'R8_FULL_MV_NULL_CONE_V1','alignment':'R8_LOSSY_ABSOLUTE_CROSS_DOTS_V1',
                          'power':'R8_LOSSY_FROBENIUS_POWERS_V1','f_B':'R8_BOOST_IMAGE_FRACTION_DIAGNOSTIC_V1'}}


def execute(ids,rows,directory,label):
    started=time.monotonic();reports=[];reconstructed=[];errors=[];converted=[]
    for sid,(q,o) in zip(ids,rows):
        ts=time.monotonic();conversions=(tensor_to_mv(q,2),tensor_to_mv(o,3))
        restored=[];squared=F(0);good=True;records=[]
        for original,c in zip((q,o),conversions):
            if c.reconstruction_enclosure is None:
                good=False;restored.append(original.copy())
            else:
                restored.append(mv_to_tensor(c.amplitude,c.vectors,c.l))
                squared+=(c.reconstruction_enclosure.hi/SCALE)**2
            records.append({'l':c.l,'amplitude_K':c.amplitude,'vectors':c.vectors,'status':c.status,
                'reconstruction_norm_K':None if c.reconstruction_enclosure is None else {'lo':c.reconstruction_enclosure.lo,'hi':c.reconstruction_enclosure.hi,'certificate':c.reconstruction_enclosure.certificate},
                'conversion_certificate':c.certificate})
        # Refused irrep uses original tensor only to retain the common score
        # pool. The row is explicitly an INCOMPLETE ablation, not a full MV row.
        errors.append(_sqrt(squared,256)[1]);converted.append(good);reconstructed.append(tuple(restored))
        reports.append({'sample_id':sid,'conversion_seconds':time.monotonic()-ts,'full_mv_available':good,
            'metric_input_status':'FULL_MV_RECONSTRUCTION' if good else 'ORIGINAL_IRREP_FALLBACK_INCOMPLETE_ABLATION',
            'conversion':records,'summaries':summary(q,o,conversions)})
    conversion_time=time.monotonic()-started
    ts=time.monotonic();tensor_pool=initialize_pool(rows,ids);tensor_time=time.monotonic()-ts
    ts=time.monotonic();mv_pool=initialize_pool(reconstructed,ids);mv_time=time.monotonic()-ts
    expanded=np.zeros_like(mv_pool.bounds);overlap=True;checks=0
    for i in range(len(ids)):
        for j in range(i+1,len(ids)):
            error=errors[i]+errors[j]
            lo=max(F(0),F(float(mv_pool.bounds[i,j,0]))-error)
            hi=F(float(mv_pool.bounds[i,j,1]))+error
            expanded[i,j]=expanded[j,i]=[outward(lo,-np.inf),outward(hi,np.inf)]
            overlap &= lo<=F(float(tensor_pool.bounds[i,j,1])) and F(float(tensor_pool.bounds[i,j,0]))<=hi
            checks+=1
    if not overlap:raise AssertionError('tensor/MV metric enclosure mismatch after conversion error')
    k=math.ceil(math.sqrt(len(ids)-1));scores=[]
    for i in range(len(ids)):
        keep=np.arange(len(ids))!=i
        a=np.sort(tensor_pool.bounds[i,keep],axis=0)[k-1]
        b=np.sort(expanded[i,keep],axis=0)[k-1]
        if max(a[0],b[0])>min(a[1],b[1]):raise AssertionError('score enclosure mismatch')
        scores.append({'sample_id':ids[i],'tensor_score':a.tolist(),'mv_error_expanded_score':b.tolist(),
                       'ablation_complete':bool(all(converted))})
    np.savez_compressed(directory/(label+'_rows.npz'),sample_ids=np.array(ids),
        Q=np.stack([x[0] for x in rows]),O=np.stack([x[1] for x in rows]),
        reconstructed_Q=np.stack([x[0] for x in reconstructed]),reconstructed_O=np.stack([x[1] for x in reconstructed]),
        full_mv_available=np.array(converted),tensor_pair_bounds=tensor_pool.bounds,mv_pair_bounds=mv_pool.bounds,
        mv_error_expanded_pair_bounds=expanded)
    out={'owner':'obsstat','claim_tier':'C0','scope':label,'rows':reports,'scores':scores,
        'M':len(ids),'k':k,'q0_K':str(SCALE),'o0_K':str(SCALE),'pair_checks':checks,'all_pair_and_score_enclosures_overlap':bool(overlap),
        'converted_rows':sum(converted),'incomplete_rows':len(ids)-sum(converted),
        'pool_ablation_status':'COMPLETE_NUMERICAL_RECONSTRUCTION' if all(converted) else 'INCOMPLETE_ABLATION_TENSORS_RETAINED',
        'timing_seconds':{'conversion':conversion_time,'tensor_pool':tensor_time,'reconstructed_pool':mv_time},
        'error_transport':'Original dyadic tensors and returned reconstruction differ by certified Frobenius norm; triangle inequality expands each pair by the sum of weighted row errors.',
        'computational_advantage':'NOT_ESTABLISHED; timings are one execution with spectral caching, not controlled benchmark',
        'empirical_rank':'NOT_EXECUTED_PRODUCT_LAW_UNAVAILABLE','empirical_eligible':False,
        'caveats':['MV roots are numerical proposals, not certified root isolation','near repeated-root refusal does not remove any original tensor',
                   'full-MV reconstructs the same complete tensor information; no information gain claimed',
                   'lossy powers/absolute cross-dot alignments/f_B use separate method IDs','enclosures concern a computed statistic, not sky uncertainty'],
        'source_hashes':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [ROOT/'htt/obsstat/r8_multipole_vectors.py',Path(__file__)]}}
    write(directory/(label+'.json'),out);return out


def render(directory,reports):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig,axes=plt.subplots(1,3,figsize=(14,4.2));mock=reports['mock2'];observed=reports['observed_components']
    for report,color,label in [(mock,'C0','mock2'),(observed,'C1','PR3 components')]:
        errors=[float(c['reconstruction_norm_K']['hi']) for r in report['rows'] for c in r['conversion'] if c['reconstruction_norm_K'] is not None and c['reconstruction_norm_K']['hi']>0]
        axes[0].scatter(np.arange(len(errors)),errors,s=18,label=label,color=color)
    axes[0].set_yscale('log');axes[0].set_xlabel('Successful nonzero irrep conversion');axes[0].set_ylabel('Certified reconstruction error upper bound [K]');axes[0].legend(fontsize=8)
    first=mock['rows'][:4];labels=['O=0','O×1','O×2','B_Q beta']
    axes[1].bar(range(4),[r['summaries']['power_O_frobenius_K2']/1e-10 for r in first]);axes[1].set_xticks(range(4),labels,rotation=20);axes[1].set_ylabel('Octupole squared Frobenius norm [1e-10 K²]')
    fb=[r['summaries']['f_B'] for r in first]
    axes[2].bar(range(4),[x if x is not None else 0 for x in fb]);axes[2].set_xticks(range(4),labels,rotation=20);axes[2].set_ylabel('f_B diagnostic');axes[2].set_ylim(0,1.08)
    for i,value in enumerate(fb):
        if value is None:axes[2].text(i,.1,'undefined',rotation=90,ha='center')
    for ax in axes:ax.grid(alpha=.15)
    fig.suptitle('Full-MV reconstruction and separate lossy summaries · fixed rows, no empirical p-value')
    fig.tight_layout();fig.savefig(directory/'representation_controls.png',dpi=160);plt.close(fig)
    write(directory/'figure.json',{'owner':'obsstat','scope':'DESCRIPTIVE_REPRESENTATION_COMPARISON','claim_tier':'C0',
        'inputs':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in directory.glob('*_rows.npz')},
        'source_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'visual_inspection':'PENDING',
        'zero_errors':'exact zero conversions omitted from log plot; all rows retained in numerical artifacts',
        'f_B_missing':'undefined zero-octupole annotated, not a physical prediction of zero'})


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--run-dir',type=Path,required=True);a=parser.parse_args()
    a.run_dir.mkdir(parents=True,exist_ok=False)
    ids,rows=synthetic();reports={'mock2':execute(ids,rows,a.run_dir,'mock2')}
    reports['mock2']['seed']=81004;write(a.run_dir/'mock2.json',reports['mock2'])
    input_path=ROOT/'docs/generated/tensor_joint_r8/owned_controls/cmb/cmb_controls.npz'
    with np.load(input_path,allow_pickle=False) as data:
        reports['observed_components']=execute(data['sample_ids'].tolist(),list(zip(data['Q'],data['O'])),a.run_dir,'observed_components')
    reports['observed_components']['input_npz_sha256']=hashlib.sha256(input_path.read_bytes()).hexdigest();write(a.run_dir/'observed_components.json',reports['observed_components'])
    render(a.run_dir,reports)
    print(json.dumps({k:{'rows':v['M'],'converted':v['converted_rows'],'pairs':v['pair_checks'],'status':v['pool_ablation_status']} for k,v in reports.items()},indent=2))


if __name__=='__main__':main()
