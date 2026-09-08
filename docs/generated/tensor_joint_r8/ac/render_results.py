#!/usr/bin/env python3
"""Reproduce the initial A/C figures and compact tables from saved results."""
import hashlib,json,sys
from fractions import Fraction as F
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parents[4]
for p in (ROOT/'htt',ROOT/'htt/src',ROOT/'htt/htt',ROOT):sys.path.insert(0,str(p))
from obsstat.r8_orbit_bounds import initialize_pool
HERE=Path(__file__).resolve().parent
DATA=Path('/mnt/sn850x2t/htt_base_e2e/TENSOR-JOINT-R8-20260909/numerical_runs')

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(p,x):Path(p).write_text(json.dumps(x,indent=2,allow_nan=False)+'\n')

def main():
    tables=[];source_files=[];references=[]
    for m in (31,301,1000):
        path=DATA/f'mock1_{m}/mock1.json';data=json.loads(path.read_text());source_files.append(path)
        for c in data['cells']:
            with np.load(c['artifact'],allow_pickle=False) as z:
                q=z['Q'];o=z['O'];ids=z['sample_ids']
                for ref in c['reference_intervals']:
                    i,j=ref['i'],ref['j']
                    # Replay initialization for this pair only. The first-100
                    # reference inclusion was checked BEFORE refinement.
                    initial=initialize_pool(((q[i],o[i]),(q[j],o[j])),(str(ids[i]),str(ids[j]))).bounds[0,1]
                    assert F(initial[0])<=F(ref['lo'])<=F(ref['hi'])<=F(initial[1])
                    references.append({'M':m,'pool':c['pool'],**ref,'initialized_lo':float(initial[0]),
                                       'initialized_hi':float(initial[1]),'comparison_stage':'INITIALIZATION'})
            tables.append({k:v for k,v in c.items() if k!='reference_intervals'})
    write(HERE/'mocks/orbit_summary.json',{'pools':tables,'first100_pair_inclusions':3000,
         'checkpoint_scope':'One 60-second checkpoint per pool; NOT the 4 worker-hour scope cap',
         'rank_status':'30 of 30 unresolved; no size or power inference from these 30 pools',
         'source_files':{str(p):sha(p) for p in source_files}})
    write(HERE/'mocks/orbit_reference_intervals.json',references)
    plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False})
    fig,axes=plt.subplots(1,3,figsize=(11,3.6))
    for ax,m in zip(axes,(31,301,1000)):
        subset=[r for r in references if r['M']==m and r['pool']==0]
        x=np.array([r['initialized_lo'] for r in subset]);y=np.array([r['initialized_hi'] for r in subset])
        ax.scatter(x,y,s=12,alpha=.75);upper=max(y.max(),x.max());ax.plot([0,upper],[0,upper],':',color='gray')
        ax.set(title=f'M={m}, first 100 pairs',xlabel='Spectral lower bound',ylabel='Identity upper bound',xlim=(0,None),ylim=(0,None))
    fig.suptitle('Computed full-tensor SO(3) distance enclosures; q0=o0=10⁻⁵ K',fontsize=12)
    fig.tight_layout();fig.savefig(HERE/'orbit_enclosures.png',dpi=160);plt.close(fig)
    mock5=json.loads((HERE/'mocks/mock5.json').read_text());cells=mock5['cells']
    fig,ax=plt.subplots(figsize=(9,4))
    x=np.arange(len(cells));rates=np.array([c['rejections']/c['trials'] for c in cells]);upper=np.array([c['binomial_upper'] for c in cells])
    colors=['#b93c34' if not c['diagnostic_pass'] else '#247486' for c in cells]
    ax.bar(x,rates,color=colors,alpha=.8);ax.errorbar(x,rates,yerr=[np.zeros(len(x)),upper-rates],fmt='none',ecolor='black',capsize=3)
    ax.axhline(.05,color='gray',ls=':',label='Nominal alpha=0.05');ax.axhline(.085,color='#b93c34',ls='--',label='Frozen diagnostic upper limit=0.085')
    ax.set_xticks(x,[f"{c['law'].replace('_',' ')}\nμ={c['mu']:g}" for c in cells],rotation=25,ha='right')
    ax.set(ylabel='Rejection frequency / one-sided upper bound',ylim=(0,.11),title='Known toy candidate laws: 1,000 trials per cell, N=199')
    ax.legend(fontsize=9,loc='upper left');fig.tight_layout();fig.savefig(HERE/'simulator_validation.png',dpi=160);plt.close(fig)
    manifest={'owner':'HTT','scope':'R8 initial A/C computed-statistic and toy-law diagnostics',
       'claim_tier':'method_diagnostic','artifact_mode':'standard_internal','allowed_use':'External audit of actual method implementation outcomes',
       'transfer_source':'NONE','null_status':'Registered synthetic trials only; no actual CMB law qualification',
       'covariance_status':'Known toy laws; no inferred real-product covariance',
       'forbidden_uses':['Bianchi identification','isotropy proof','actual catalogue coverage claim','30-pool power claim'],
       'source_script':{'path':str(Path(__file__).relative_to(ROOT)),'sha256':sha(__file__)},
       'sources':{str(p.relative_to(ROOT)):sha(p) for p in (HERE/'mocks/orbit_reference_intervals.json',HERE/'mocks/mock5.json')},
       'figures':{p.name:{'sha256':sha(p),'caption':'INITIALIZATION distance bounds on first 100 pairs' if p.name.startswith('orbit') else 'Nine fixed toy experiments; mixture μ=-1 held by frozen criterion'} for p in (HERE/'orbit_enclosures.png',HERE/'simulator_validation.png')}}
    write(HERE/'figure_manifest.json',manifest)
    print(json.dumps({'pools':len(tables),'reference_pairs':len(references),'figures':list(manifest['figures'])}))
if __name__=='__main__':main()
