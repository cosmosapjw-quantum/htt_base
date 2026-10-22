"""Frozen processed-output E pseudoalm experiment; no empirical null p-value."""
from pathlib import Path
from functools import lru_cache
from enum import Enum
from types import SimpleNamespace
import ast
import hashlib
import importlib.util
import json
import math
import subprocess
import sys

import healpy as hp
import numpy as np
from sympy.physics.wigner import wigner_3j

HERE=Path(__file__).resolve().parent
REPO=HERE.parents[5]
sp=importlib.util.spec_from_file_location('a22_power_tensor',REPO/'htt/obsstat/lowell_poles.py')
poles=importlib.util.module_from_spec(sp);sys.modules[sp.name]=poles;sp.loader.exec_module(poles)
PRODUCTS=('full','hm1','hm2','oe1','oe2')


def digest(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()


class Factor(Enum):
    PARITY='parity'
    ORIENTATION='orientation'
    PHASE='phase'


def intervention(alm,factor,angle=0.):
    factor=Factor(factor)
    out={}
    for (ell,m),value in alm.items():
        if factor==Factor.PARITY:mult=(-1)**ell
        elif factor==Factor.ORIENTATION:mult=np.exp(-1j*m*angle)
        else:mult=np.exp(1j*(0 if m==0 else math.copysign(1,m)*m*m*angle))
        out[ell,m]=complex(value*mult)
    return out


def donor_intervention(alm,factor,angle=0.):
    """Extract the single pinned algebra oracle, never import the donor workflow."""
    blob='16b1b623a4f74fe7690bde5fc95d29e6d8e1bc9a'
    source=subprocess.check_output(['git','cat-file','blob',blob],cwd=REPO,text=True)
    fn=next(n for n in ast.parse(source).body if isinstance(n,ast.FunctionDef) and n.name=='_apply_intervention_to_alm')
    env=dict(np=np,math=math,LowEllInterventionSpec=SimpleNamespace,CounterpairFactor=Factor)
    exec(compile(ast.Module(body=[fn],type_ignores=[]),blob,'exec'),env)
    entries=tuple((ell,m,a.real,a.imag) for (ell,m),a in sorted(alm.items()))
    return env[fn.name](entries,SimpleNamespace(factor=Factor(factor),angle_radians=angle))


@lru_cache(None)
def contraction():
    return tuple((m,n,-m-n,float(wigner_3j(2,3,4,m,n,-m-n)))
                 for m in range(-2,3) for n in range(-3,4) if abs(m+n)<=4)


def normalized(alm):
    vectors={};powers={}
    for ell in (2,3,4):
        x=np.array([alm[ell,m] for m in range(-ell,ell+1)],complex)
        if not np.isfinite(x).all():raise ValueError('nonfinite harmonic coefficient')
        scale=float(np.max(abs(x)))
        if scale<=0:raise ValueError('zero multipole')
        x=x/scale
        for m in range(ell+1):
            if abs(x[ell-m]-(-1)**m*x[ell+m].conjugate())>1e-12:raise ValueError('real E scalar reality violation')
        n=float(np.linalg.norm(x));powers[ell]=(scale*n)**2
        if not np.isfinite(powers[ell]) or powers[ell]<=0:raise ValueError('unrepresentable physical power')
        vectors[ell]=x/n
    return vectors,powers


def features(alm):
    vectors,powers=normalized(alm)
    b=sum(w*vectors[2][m+2]*vectors[3][n+3]*vectors[4][p+4] for m,n,p,w in contraction())
    if abs(b.real)>1e-12:raise ArithmeticError('odd-sum Wigner contraction is not imaginary')
    tensors=[];axes=[];gaps=[]
    unit={(ell,m):v[m+ell] for ell,v in vectors.items() for m in range(-ell,ell+1)}
    for ell in (2,3):
        t=poles.angular_momentum_power_tensor(alm_by_lm=unit,ell=ell)
        ev,v=np.linalg.eigh(t);gap=float(ev[-1]-ev[-2]);gaps.append(gap)
        tensors.append(t);axes.append(None if gap<=1e-10 else v[:,-1])
    alignment=None if any(v is None for v in axes) else float(np.clip(np.dot(*axes)**2,0,1))
    component=[(0,0),(0,1),(0,2),(1,1),(1,2),(2,2)]
    return dict(C_ell_K_CMB2={str(l):powers[l]/(2*l+1) for l in (2,3,4)},J234=float(b.imag),
                alignment23_squared=alignment,axis_status='ABSTAIN' if alignment is None else 'DEFINED',
                largest_axis_gaps=gaps,
                tensor2=[float(tensors[0][i,j]) for i,j in component],
                tensor3=[float(tensors[1][i,j]) for i,j in component])


def joint_score(rows):
    if any(r['alignment23_squared'] is None for r in rows):return None
    return max(max(abs(r['J234']),r['alignment23_squared']) for r in rows)


def validate_link(entries):
    if len(entries)!=5 or {r['product'] for r in entries}!=set(PRODUCTS):raise ValueError('exact five unique products required')
    if {r['underlying_sky_id'] for r in entries}!={'actual-Planck-PR3-observed-sky'}:raise ValueError('whole-sky identity mismatch')
    if len({r['contract']['source_sha256'] for r in entries})!=5:raise ValueError('split source identities duplicated')
    for key in ('release','frame','units','QU','coefficients'):
        if len({r[key] for r in entries})!=1:raise ValueError('source convention mismatch')
    for key in ('native_window_sha256','processing','lmax','nside_out','mask_order','native_window'):
        if len({r['contract'][key] for r in entries})!=1:raise ValueError('processing linkage mismatch')


def load_fields(experiment):
    fields=[];identities={}
    for limit in (32,64,128):
        entries=[e for e in experiment['products'] if e['lmax']==limit];validate_link(entries)
        for e in entries:
            name=e['product'];path=Path(e['payload_path']);meta=Path(e['metadata_path'])
            if digest(path)!=e['payload_sha256'] or digest(meta)!=e['metadata_sha256']:raise ValueError('frozen processed input drift')
            live=json.loads(meta.read_text())
            if live['contract']!=e['contract'] or live['alms_npz_sha256']!=e['payload_sha256']:raise ValueError('metadata/source binding drift')
            pin=e['contract']['source_sha256']
            if name in identities and identities[name]!=pin:raise ValueError('source changed across lmax')
            identities[name]=pin
            with np.load(path,allow_pickle=False) as f:
                if set(f.files)!={'E','B'}:raise ValueError('processed E/B schema')
                a=f['E']
                if a.shape!=(hp.Alm.getsize(limit),) or not np.isfinite(a).all():raise ValueError('packed alm schema')
                alm={}
                for l in (2,3,4):
                    for m in range(0,l+1):
                        v=complex(a[hp.Alm.getidx(limit,l,m)]);alm[l,m]=v
                        if m:alm[l,-m]=(-1)**m*v.conjugate()
            fields.append((e,alm))
    return fields


def main():
    frozen=HERE/'EXPERIMENT.json';ex=json.loads(frozen.read_text());rows=[]
    for e,a in load_fields(ex):
        primary=features(a);controls={}
        for factor,angle in ((Factor.PARITY,0.),(Factor.ORIENTATION,.41),(Factor.PHASE,.37)):
            f=features(intervention(a,factor,angle))
            clres=max(abs(f['C_ell_K_CMB2'][str(l)]/primary['C_ell_K_CMB2'][str(l)]-1) for l in (2,3,4))
            if clres>1e-12:raise ArithmeticError('intervention changed power')
            if factor==Factor.PARITY and abs(f['J234']+primary['J234'])>1e-12:raise ArithmeticError('parity sign')
            if factor==Factor.ORIENTATION and abs(f['J234']-primary['J234'])>1e-12:raise ArithmeticError('proper rotation J')
            if factor!=Factor.PHASE and primary['alignment23_squared'] is not None and abs(f['alignment23_squared']-primary['alignment23_squared'])>1e-12:raise ArithmeticError('alignment invariance')
            delta=max(abs(f['J234']-primary['J234']),max(abs(np.array(f['tensor2'])-primary['tensor2'])),max(abs(np.array(f['tensor3'])-primary['tensor3'])))
            controls[factor.value]=dict(features=f,power_relative_residual=clres,feature_separates=bool(delta>1e-12),max_feature_change=delta)
        rows.append(dict(product=e['product'],lmax=e['lmax'],features=primary,controls=controls))
    scores={str(l):joint_score([r['features'] for r in rows if r['lmax']==l]) for l in (32,64,128)}
    sensitivity=[]
    for name in PRODUCTS:
        r=[x for x in rows if x['product']==name];ref=r[0]['features']
        sensitivity.append(dict(product=name,max_J_shift=max(abs(x['features']['J234']-ref['J234']) for x in r),
            max_alignment_shift=None if any(x['features']['alignment23_squared'] is None for x in r) else max(abs(x['features']['alignment23_squared']-ref['alignment23_squared']) for x in r)))
    result=dict(owner='obsstat',claim_tier='C0_PROCESSED_MAP_DIAGNOSTIC',transfer_source='none',
        experiment_sha256=digest(frozen),code_sha256=digest(Path(__file__)),power_tensor_kernel_sha256=digest(REPO/'htt/obsstat/lowell_poles.py'),
        rows=rows,descriptive_joint_score=scores,processing_sensitivity=sensitivity,
        independent_skies=1,p_value=None,physical_null_status='HOLD_NO_MATCHED_JOINT_TOTAL_FIELD_LAW',
        caveats=['E pseudoalm of common masked delivered QU, not cosmic E.',
                 'Output-space counterpairs do not represent physical sky-before-fixed-mask interventions.',
                 'L32/64/128 and five products are repeated views of one sky, not null ensemble.',
                 'Joint max is parity-even, unscaled components have unequal ranges; no observed significance or family identification.'])
    (HERE/'RESULT.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    import matplotlib
    matplotlib.use('Agg')
    from matplotlib import pyplot as plt
    fig,ax=plt.subplots(1,3,figsize=(13,4))
    for l,marker in ((32,'o'),(64,'x'),(128,'+')):
        selected=[r for r in rows if r['lmax']==l]
        ax[0].plot(PRODUCTS,[r['features']['J234'] for r in selected],marker=marker,label=f'L{l}')
        ax[1].plot(PRODUCTS,[r['features']['alignment23_squared'] for r in selected],marker=marker,label=f'L{l}')
    ref=[r for r in rows if r['lmax']==32]
    ax[2].plot(PRODUCTS,[r['features']['J234'] for r in ref],'o-',label='original')
    for name in ('parity','phase','orientation'):ax[2].plot(PRODUCTS,[r['controls'][name]['features']['J234'] for r in ref],'.--',label=name)
    ax[0].set_ylabel('signed ordered J234');ax[1].set_ylabel('largest-axis alignment squared');ax[1].set_ylim(0,1)
    ax[2].set_ylabel('L32 signed J234, output interventions')
    for a in ax:a.legend(fontsize=7);a.tick_params(axis='x',rotation=25)
    fig.suptitle('One PR3 observed sky; processed E pseudoalm diagnostic, no calibrated p')
    fig.tight_layout()
    for ext in ('png','pdf'):fig.savefig(HERE/f'MORPHOLOGY.{ext}',dpi=160)
    plt.close(fig)
    print(json.dumps(dict(joint_score=scores,processing_sensitivity=sensitivity)))


if __name__=='__main__':main()
