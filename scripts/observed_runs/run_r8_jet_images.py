#!/usr/bin/env python3
"""Execute fixed mock6 jet images; no observed radiation-jet law is inferred."""
from __future__ import annotations

import argparse
from dataclasses import asdict
from decimal import Decimal, localcontext
from fractions import Fraction as F
import hashlib
import json
import math
from pathlib import Path
import platform
import subprocess
import sys
import time

import numpy as np

ROOT=Path(__file__).resolve().parents[2]
for p in (ROOT,ROOT/'htt',ROOT/'htt/src',ROOT/'htt/htt'):sys.path.insert(0,str(p))
from common.r8_jet_set import JetDomain,jet_image,support,p1_operator
from common.r7_contracts import AcceptanceResult
from htt.infer.r7_confidence import PhysicalDomain,PhysicalRegion
from htt.infer.r7_mes_region import AffineRatioFunctional
from htt.infer.r8_confidence_image import (
    CompatibleTuple,outer_region,project,LinearTarget,recession_certificate,
    closure_frontier,FIXED_INTEGRATED_ALLOCATION,
)

RHOS=(F(0),F(1,4),F(1,2),F(1),F(2),F(4))
REMAINDERS=((F(0),F(0)),(F(3,10),F(3,5)))
DIAGONAL=(1,2,1,2,1,2,1,2)


def serial(x):
    if isinstance(x,F):return {'numerator':x.numerator,'denominator':x.denominator}
    if isinstance(x,np.ndarray):return serial(x.tolist())
    if isinstance(x,np.generic):return serial(x.item())
    if isinstance(x,float) and not math.isfinite(x):return 'POSITIVE_INFINITY' if x>0 else 'NEGATIVE_INFINITY'
    if isinstance(x,dict):return {k:serial(v) for k,v in x.items()}
    if isinstance(x,(tuple,list)):return [serial(v) for v in x]
    return x


def write(path,value):path.write_text(json.dumps(serial(value),indent=2,allow_nan=False)+'\n')
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def dec(x):return Decimal(x.numerator)/Decimal(x.denominator) if isinstance(x,F) else Decimal(x)


def reference(rho,remainder,direction):
    """Separate 110-digit P2 formula; no production map/support/root calls."""
    if rho==math.inf:return Decimal('Infinity')
    with localcontext() as ctx:
        ctx.prec=110
        if direction=='normalized_ones':
            return (dec(rho)*Decimal(20).sqrt()+dec(remainder[0]/3)*Decimal(5).sqrt()
                    +dec(remainder[1]/3)*Decimal(3).sqrt())/Decimal(8).sqrt()
        i=int(direction[1:]);return dec(rho)*DIAGONAL[i]+dec(remainder[i>=5]/3)


def execute(directory):
    directory.mkdir(parents=True,exist_ok=False)
    started=time.monotonic()
    domain=JetDomain('R8_MOCK6_IDENTITY_MAP','GALACTIC',np.eye(8),
        ('specified deterministic algebra fixture; not a realized radiation history',
         'orthonormal STF5/antisymmetric3 coordinates; Theta=3 in declared rate units'))
    def factory(rho,rem):return jet_image(np.zeros(8),np.diag(DIAGONAL),rho,rem,3,domain)
    directions=[(f'{sign}{i}',np.eye(8)[i]*(1 if sign=='+' else -1),False)
                for i in range(8) for sign in ('+','-')]+[('normalized_ones',np.ones(8),True)]
    queries=[];projections=[];frontiers=[]
    with localcontext() as ctx:
        ctx.prec=110
        for rem in REMAINDERS:
            for rho in (*RHOS,math.inf):
                im=factory(rho,rem)
                for name,a,normalize in directions:
                    b=support(im,a,normalize=normalize);ref=reference(rho,rem,name)
                    if rho==math.inf:passed=b.lo==b.hi==math.inf
                    else:passed=dec(b.lo)<=ref<=dec(b.hi)
                    queries.append({'rho':rho,'remainder_rate_radii':rem,'direction':name,
                        'support':asdict(b),'reference_decimal_110':str(ref),'reference_enclosed':passed})
                projections.append({'rho':rho,'remainder_rate_radii':rem,
                    's2':asdict(project(im,'s2')),'w2':asdict(project(im,'w2')),
                    'S1':asdict(project(im,LinearTarget('S1',np.eye(8)[0]))),
                    'W1':asdict(project(im,LinearTarget('W1',np.eye(8)[5])))})
            for name,i in (('S1',0),('W1',5)):
                frontiers.append({'target':name,'threshold':F(1),'remainder_rate_radii':rem,
                    **closure_frontier(lambda rho:factory(rho,rem),LinearTarget(name,np.eye(8)[i]),1,RHOS)})
    # V08 tests one supplied ray; actual constraints remove the same ray.
    v=np.eye(8)[7];R=np.eye(8)[:4];K=np.eye(8)
    rays={'unrestricted':recession_certificate(R,K,v,domain_A=np.zeros((0,8)),target=v),
          'compact_coordinate':recession_certificate(R,K,v,domain_A=np.array([v,-v]),target=v),
          'unaffected_target':recession_certificate(R,K,v,domain_A=np.zeros((0,8)),target=np.eye(8)[0])}
    # A deterministic example of J1, never an empirical coverage claim.
    d=PhysicalDomain('R8_D_SET_ALGEBRA',('shared_x',),lambda x,e:True,((-2,3),))
    def fixture(rule):
        return PhysicalRegion(None,d,None,lambda x,e:AcceptanceResult(True,None,None,None,rule(x[0]),'RESOLVED'),
                              .99,'DECLARED_SET_ALGEBRA_FIXTURE',('fixture',))
    left,right=fixture(lambda x:x<=0),fixture(lambda x:x>=1)
    tuples=(CompatibleTuple('joint',d,{'CMB':'left','CF4':'right'}),)
    joined=outer_region({'left':left,'right':right},tuples,FIXED_INTEGRATED_ALLOCATION)
    missing=outer_region({'left':left},tuples,FIXED_INTEGRATED_ALLOCATION)
    alternative=outer_region({'left':left,'right':right},
        (CompatibleTuple('left-law',d,{'CMB':'left'}),CompatibleTuple('right-law',d,{'CMB':'right'})),FIXED_INTEGRATED_ALLOCATION)
    states=[-2,-1,0,1,2,3]
    composition={'allocation':FIXED_INTEGRATED_ALLOCATION,'coverage_lower_compatibility_view':missing.coverage_lower,
        'states':states,'intersection':[joined.contains([x]) for x in states],
        'missing_scope':[missing.contains([x]) for x in states],
        'alternative_union':[alternative.contains([x]) for x in states],
        'scope':'set algebra only; acceptance predicates here are deterministic fixtures without observed coverage evidence'}
    # The actual existing shared-state ratio implementation is exercised on an
    # explicitly illustrative positive box, not on invented physical data.
    dpos=PhysicalDomain('R8_D_RATIO_FIXTURE',('shared_x',),lambda x,e:True,((0,1),))
    rpos=PhysicalRegion(None,dpos,None,lambda x,e:AcceptanceResult(True,0,0,0,True,'RESOLVED'),.99,'FIXTURE',('ratio-fixture',))
    ratio=AffineRatioFunctional('F_ratio_fixture',F(1),F(2),(F(1),),(F(1),))
    zero=AffineRatioFunctional('zero_denominator_fixture',F(1),F(0),(F(1),),(F(1),))
    im=factory(F(1),REMAINDERS[1])
    physical={'scientific_outcome':'CONDITIONAL_BOUND','empirical_physical_confidence':'INPUT_UNAVAILABLE',
        'reason':'No admitted candidate-state CMB jet/response, same-state tilt/curvature, or F/G_F denominator and depth domain is supplied.',
        'x_C':asdict(project(im,'x_C')),'F':asdict(project(im,'F')),'G_F':asdict(project(im,'G_F')),
        'positive_ratio_fixture':asdict(project(rpos,ratio)),
        'zero_denominator_fixture':asdict(project(rpos,zero)),
        'legacy_code':'htt/htt/htt/infer/r7_mes_region.py::affine_box_gf_bound -> obsstat.egs3_gf_interval_v8::exact_joint_interval_v8',
        'legacy_x_C':'signed comparator needs its own normalization and same-state tilt/curvature; no value substituted from tensor norm bounds'}
    source_paths=['htt/src/common/r8_jet_set.py','htt/htt/htt/infer/r8_confidence_image.py',
        'htt/htt/htt/infer/r7_confidence.py','htt/htt/htt/infer/r7_mes_region.py',
        'scripts/observed_runs/run_r8_jet_images.py','docs/research_program/tensor_joint_r8/SCIENTIFIC_CONTRACT.md',
        'docs/research_program/tensor_joint_r8/VALIDATION_MATRIX.md']
    payload={'owner':'htt','scope':'Unit D fixed mock6 and same-state conditional set algebra','claim_tier':'C0',
        'transfer_source':'none','sky_support_status':'NOT_APPLICABLE_MATHEMATICAL_FIXTURES',
        'null_mock_status':'DETERMINISTIC_FIXTURES_NOT_OBSERVATIONAL_CALIBRATION',
        'generator':{'algorithm':'fully specified deterministic matrix cases; no random draws','seed_design_label':81010,
            'numpy':np.__version__,'python':platform.python_version()},
        'source_head':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
        'source_worktree':'explicit source hashes include uncommitted Unit D candidate',
        'source_sha256':{p:sha(ROOT/p) for p in source_paths},
        'method':'P1 scalar block map; exact-rational P2 with 256-bit outward root brackets; same-state convex outer images',
        'query_count':len(queries),'finite_query_count':sum(q['rho']!=math.inf for q in queries),
        'reference_checks_pass':all(q['reference_enclosed'] for q in queries),
        'queries':queries,'projections':projections,'frontiers':frontiers,'recession':rays,
        'set_composition':composition,'physical_scope':physical,
        'independent_four_axis_status':'NOT_PERFORMED_OWNER_AUTHORIZED_DIRECT_ROUTE',
        'caveats':['L is a deterministic budget operator, not a covariance.',
            'The identity-map cases do not demonstrate radiation histories or observed physical constraints.',
            'Norm bounds can be conservative; all targets use one joint declared set.',
            'The 110-digit reference check is host-authored, not an independent review.']}
    write(directory/'results.json',payload)
    plot(directory,payload)
    write(directory/'execution.json',{'argv':sys.argv,'cwd':str(ROOT),'elapsed_seconds':time.monotonic()-started,
        'result_sha256':sha(directory/'results.json'),'reference_checks_pass':payload['reference_checks_pass']})
    if not payload['reference_checks_pass']:raise AssertionError('mock6 support differs from reference; preserve output')
    print(json.dumps({'queries':len(queries),'finite_queries':payload['finite_query_count'],
                      'reference_checks_pass':True,'output':str(directory)},indent=2))


def plot(directory,payload):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False})
    fig,axes=plt.subplots(1,3,figsize=(13,4),layout='constrained')
    for rem,style in zip(REMAINDERS,('-', '--')):
        label=f'rate remainders ({float(rem[0]):g}, {float(rem[1]):g})'
        for ax,target in zip(axes[:2],('S1','W1')):
            rows=[p for p in payload['projections'] if p['remainder_rate_radii']==rem and p['rho']!=math.inf]
            x=[float(p['rho']) for p in rows]
            ax.plot(x,[float(p[target]['bounds'][1]) for p in rows],style,label=label)
            ax.plot(x,[float(p[target]['bounds'][0]) for p in rows],style,color=ax.lines[-1].get_color())
            ax.set(xlabel='Deterministic radius rho',ylabel=f'{target} coordinate range')
            ax.axhline(0,color='.8',lw=.6)
    axes[0].legend(fontsize=8)
    for i,f in enumerate(payload['frontiers']):
        axes[2].plot([float(f['rho_lower']),float(f['rho_upper'])],[i,i],lw=5,solid_capstyle='butt')
    axes[2].set(yticks=range(4),yticklabels=['S1 / zero remainder','W1 / zero remainder','S1 / bounded remainder','W1 / bounded remainder'],
                xlabel='Certified bracket for rho critical',title='Target coordinate = 1')
    fig.suptitle('Declared jet-set sensitivity | mock6 algebra fixtures | no observed jet law',fontsize=12)
    fig.savefig(directory/'jet_support_frontiers.png',dpi=160)
    fig.savefig(directory/'jet_support_frontiers.pdf')
    plt.close(fig)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run-dir',type=Path,required=True)
    execute(parser.parse_args().run_dir)
