"""A22-06: marked selected-cohort law and released-distance completion frontier."""
from pathlib import Path
from collections import Counter
from decimal import Decimal
import csv
import gzip
import hashlib
import json
import re

import numpy as np
from scipy.integrate import quad
from scipy.optimize import brentq
from scipy.stats import norm

HERE = Path(__file__).resolve().parent
RAW = Path('/mnt/extdrive/workdir/htt_open_data')
UP = RAW/'cf4/upstream_20261018'
OUTCOMES = ['accepted', 'other_quality', 'confused', 'nondetection']


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def schema(readme, filename):
    part = readme.split('Byte-by-byte Description of file: '+filename+'\n',1)[1]
    part = part.split('Byte-by-byte Description of file:',1)[0].split('Note (',1)[0]
    cols={}
    for line in part.splitlines():
        m=re.match(r'^\s*(\d+)(?:-\s*(\d+))?\s+([AIF]\d+(?:\.\d+)?)\s+\S+\s+(\S+)\s+',line)
        if m:
            lo,hi,fmt,key=m.groups();cols[key]=(int(lo)-1,int(hi or lo))
    return cols


def cents(value):
    v=Decimal(str(value))*100
    if v != int(v):raise ValueError('exact centimag required')
    return int(v)


def completion(dm_cents, total, tau, delta):
    x=np.asarray(dm_cents)
    if x.ndim != 1 or x.dtype.kind not in 'iu' or total < len(x) or total <= 0:
        raise ValueError('integer centimag and complete selected cohort required')
    k=int(np.sum(x-cents(delta)>cents(tau)))
    return dict(k=k, lower=k/total, upper=(k+total-len(x))/total)


def marked_loglik(counts, probabilities):
    n,p=np.asarray(counts),np.asarray(probabilities,float)
    if n.shape!=p.shape or np.any(n<0) or np.any(p<0) or not np.isfinite(p).all() or abs(p.sum()-1)>1e-12:
        raise ValueError('normalized nonnegative marked law required')
    if np.any((n>0)&(p==0)):return -np.inf
    return float(np.sum(n[n>0]*np.log(p[n>0])))


def two_cut_normalizer(mean, covariance, cuts):
    mean,cov,cuts=np.asarray(mean,float),np.asarray(covariance,float),np.asarray(cuts,float)
    if mean.shape!=(2,) or cov.shape!=(2,2) or cuts.shape!=(2,) or not np.isfinite(mean).all() or not np.isfinite(cov).all() or np.isnan(cuts).any():
        raise ValueError('finite two-variable Gaussian, extended-real cuts required')
    if not np.allclose(cov,cov.T,rtol=1e-13,atol=0):raise ValueError('symmetric covariance required')
    np.linalg.cholesky(cov)
    sd=np.sqrt(np.diag(cov));a,b=(cuts-mean)/sd
    rho=cov[0,1]/np.prod(sd)
    if abs(rho)>=1:raise ValueError('positive definite Gaussian required')
    if np.isposinf(a) or np.isposinf(b):
        raise ArithmeticError('zero probability outside representable positive domain')
    if np.isneginf(a):value=norm.sf(b)
    elif np.isneginf(b):value=norm.sf(a)
    elif rho==0:value=norm.sf(a)*norm.sf(b)
    else:
        width=np.sqrt(1-rho*rho)
        def oriented(lower,other):
            def logf(v):return norm.logpdf(v)+norm.logsf((other-rho*v)/width)
            def derivative(v):
                t=(other-rho*v)/width
                return -v+rho/width*np.exp(norm.logpdf(t)-norm.logsf(t))
            mode=lower
            if derivative(lower)>0:
                upper=max(lower+1,1.)
                while derivative(upper)>0:
                    upper=2*upper+abs(lower)+1
                    if not np.isfinite(upper):raise ArithmeticError('unresolved Gaussian mode')
                mode=brentq(derivative,lower,upper,xtol=1e-12)
            peak=logf(mode)
            def scaled(v):return np.exp(logf(v)-peak)
            # Integrate each side of the mode, with a relative error requirement.
            right,er=quad(scaled,mode,np.inf,epsabs=0,epsrel=1e-10)
            left,el=(0.,0.) if mode==lower else quad(scaled,lower,mode,epsabs=0,epsrel=1e-10)
            area=left+right
            if area<=0 or not np.isfinite(area) or el+er>1e-8*area:
                raise ArithmeticError('selection normalizer relative quadrature unresolved')
            return float(np.exp(peak+np.log(area)))
        v1,v2=oriented(b,a),oriented(a,b)
        if not np.isclose(v1,v2,rtol=1e-8,atol=0):
            raise ArithmeticError('selection normalizer permutation check unresolved')
        value=(v1+v2)/2
    if not np.isfinite(value) or value<=0 or value>1+1e-12:
        raise ArithmeticError('selection normalizer numerically unresolved; no floor')
    return float(value)



def main():
    ledger=RAW/'cf4/D02_HI_CF4_20261018/TARGET_JOIN_AND_OOF.csv'
    table=UP/'table4.dat'
    sealed={ledger:'c32885cd2f081ec1bcedfcb98ef18c8c53245c12ac4a5fabb64d68b27a75f48d',
            table:'f4aa0ba0efe7d7a14f044a76ef37f5a033e2788923d586c2d15ed248939455f2',
            UP/'ReadMe':'45fa3cca5346aff29bcf9785e7b08e8ab34b1d67e80b359c0d28bdbd18e42581',
            RAW/'cf4/HI_646_A113/table2.dat':'2e7e9f979aeb862ae59ac40b377953de7602c2574515b2c880c0b55cb838249c'}
    for p,h in sealed.items():
        if sha(p)!=h:raise ValueError('immutable retained cohort input changed')
    rows=list(csv.DictReader(ledger.open()))
    if len(rows)!=628 or len({r['pgc'] for r in rows})!=628:raise ValueError('target membership')
    cols=schema((UP/'ReadMe').read_text(),'table4.dat')
    dist={}
    for line in table.read_text().splitlines():
        p=int(line[slice(*cols['PGC'])]);val=line[slice(*cols['DMbest'])].strip()
        err=line[slice(*cols['e_DMbest'])].strip()
        if val and val not in ('---','--'):
            if not err or float(err)<=0:raise ValueError('released distance uncertainty')
            dist[p]=(cents(val),float(err))
    counts=np.zeros((4,2),int);values=[]
    for row in rows:
        p=int(row['pgc']);o=OUTCOMES.index(row['outcome']);r=int(p in dist)
        counts[o,r]+=1
        if r:values.append(dist[p][0])
    values=np.array(values,dtype=np.int64)
    if counts.tolist()!=[[116,269],[21,1],[26,3],[191,1]]:raise ValueError('joint mark fixture drift')
    pi=counts/628
    loglik=marked_loglik(counts,pi)
    hi=RAW/'cf4/HI_646_A113/table2.dat'
    ilow=[];imissing=[]
    for line in hi.read_text().splitlines():
        p=int(line[:7]);v=line[52:57].strip()
        if not v:imissing.append(p)
        elif float(v)<=45:ilow.append(p)
    if len(ilow)!=22 or len(imissing)!=2:raise ValueError('retained cut-discordance changed')
    six=RAW/'a22_20261023/6df'
    manifest=json.loads((HERE/'ACQUISITION_MANIFEST.json').read_text())
    sources=[]
    for s in manifest['resources']:
        p=RAW/s['path'];receipt=json.loads(Path(str(p)+'.receipt.json').read_text())
        actual=sha(p)
        if actual!=receipt['sha256'] or (s.get('sha256') and actual!=s['sha256']):raise ValueError('6dF source drift')
        sources.append(dict(id=s['id'],path=str(p),sha256=actual,bytes=p.stat().st_size))
    pv=gzip.decompress((six/'PV_table1.dat.gz').read_bytes()).decode('ascii').splitlines()
    fp=gzip.decompress((six/'FP_table8.dat.gz').read_bytes()).decode('ascii').splitlines()
    if len(pv)!=8885 or len(fp)!=11102 or any(len(x)!=74 for x in pv) or any(len(x)!=224 for x in fp):raise ValueError('6dF count/width')
    pvid={x[:15].strip() for x in pv};fpd={x[:15].strip():x for x in fp}
    if len(pvid)!=8885 or len(fpd)!=11102 or not pvid<=fpd.keys():raise ValueError('6dF name join')
    js={k for k,v in fpd.items() if v[205]=='1'}
    codes=Counter(fpd[k][198:204].strip().zfill(6) for k in pvid)
    six_result=dict(pv_rows=len(pv),fp_rows=len(fp),unique_name_join=len(pvid),
                    Js_one=len(js),PV_without_Js_one=len(pvid-js),Js_one_absent_PV=len(js-pvid),
                    Jcode_in_PV=dict(sorted(codes.items())),
                    group_absent=sum(int(x[47:51])==-1 for x in pv),
                    eta_minmax=[min(float(x[52:59]) for x in pv),max(float(x[52:59]) for x in pv)])
    if (len(js),len(pvid-js),len(js-pvid))!=(8896,12,23):raise ValueError('6dF cut membership fixture')
    curves={}
    for tau in (32,34,36,38):
        knots=np.unique(values-cents(tau))
        curves[str(tau)]=dict(at_zero=completion(values,628,tau,0),
                              delta_centimag_breakpoints=knots.tolist(),
                              at_breakpoint=[completion(values,628,tau,str(Decimal(int(k))/100)) for k in knots])
    result=dict(owner='htt',claim_tier='C0_DERIVED_CONDITIONAL',transfer_source='none',
                scope='selected-target mark law and released-DM completion sets; separate 6dF release-cohort audit',
                source_identities=[dict(path=str(p),sha256=h) for p,h in sealed.items()]+sources,
                mark_order=OUTCOMES,columns=['distance_missing','distance_present'],counts=counts.tolist(),
                probabilities=pi.tolist(),normalization=float(pi.sum()),working_mark_loglik=loglik,
                observed_distance_count=len(values),missing_distance_count=628-len(values),
                missing_distance_mass=(628-len(values))/628,prediction_domain_unknown_mass=1/628,
                physical_Q_unknown_mass=1,physical_Q_outer=[0,1],
                DMbest_range_mag=[int(values.min())/100,int(values.max())/100],
                distance_completion=curves,calibration_delta_bound='UNKNOWN; full staircase, displayed domain is illustrative',
                inclination_cut_discordance=dict(at_most_45_count=len(ilow),missing_count=len(imissing),
                    classification='DESIGN_VINTAGE_OR_MEASUREMENT_UNRESOLVED',retained_all_628=True),
                sixdf=six_result,
                gaussian_normalizer_fixture=two_cut_normalizer([0,0],np.eye(2),[0,0]),
                caveats=['Working multinomial probabilities condition on actual targets; not 5460-parent selection probabilities.',
                         'DM completion sets describe released values, not true-distance coverage or physical Pi.',
                         'Shared calibration/velocity laws, targeting history and repeated-source genealogy remain missing.',
                         '6dF released eta is already corrected; do not apply raw FP normalizer again or multiply as independent CF4 data.'])
    (HERE/'RESULT.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    import matplotlib
    matplotlib.use('Agg')
    from matplotlib import pyplot as plt
    fig,ax=plt.subplots(1,3,figsize=(13,4))
    ax[0].bar(OUTCOMES,counts[:,1],label='released DM')
    ax[0].bar(OUTCOMES,counts[:,0],bottom=counts[:,1],label='DM missing')
    ax[0].tick_params(axis='x',rotation=30);ax[0].set_ylabel('actual target count');ax[0].legend(fontsize=8)
    delta=np.linspace(-5,5,501)
    for tau in (32,34,36):
        c=[completion(values,628,tau,str(round(float(d),2))) for d in delta]
        ax[1].plot(delta,[x['lower'] for x in c],label=f'tau={tau}')
        ax[1].fill_between(delta,[x['lower'] for x in c],[x['upper'] for x in c],alpha=.1)
    ax[1].set(xlabel='declared DM shift delta (mag)',ylabel='finite-cohort completion fraction',ylim=(0,1));ax[1].legend(fontsize=8)
    ax[2].bar(['PV & Js','PV only','Js only'],[len(pvid&js),len(pvid-js),len(js-pvid)])
    ax[2].set_yscale('log');ax[2].set_ylabel('6dF exact membership count (log)')
    fig.suptitle('Selected-cohort likelihood and released-value completion; physical law UNKNOWN')
    fig.tight_layout()
    for ext in ('png','pdf'):fig.savefig(HERE/f'SELECTION.{ext}',dpi=160)
    plt.close(fig)
    print(json.dumps(dict(mark_counts=counts.tolist(),missing_distance_mass=result['missing_distance_mass'],sixdf=six_result)))


if __name__=='__main__':main()
