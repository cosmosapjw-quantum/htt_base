#!/usr/bin/env python3
"""One-shot independent R33 finite F2 checker. Run only after controller CHECK_GO."""
import argparse
import hashlib
import json
import math
import os
import resource
import signal
import sys
import time
import traceback
from pathlib import Path

ROOT = Path('/mnt/extdrive/workdir/htt_open_data')
OUT = ROOT / 'r35_cmb_checker_api_fix'
SOURCE = ROOT / 'r33_cmb_additional_frequency_framing'
CONTRACT = SOURCE / 'WMAP_PLANCK_F2_CONTRACT.md'
PRIOR = ROOT / 'r30_cmb_spectral_response_framing/SPECTRAL_ONLY_CONTRACT.md'
INPUT = ROOT / 'r33_wmap_planck_dispatch/INPUT.json'
OLD = ROOT / 'r30_cmb_spectral_response_numeric/attempt_38cdf6b948a41ee9/RESULT.json'
PROD = ROOT / 'r33_cmb_wmap_planck_numeric/stable_complement_repair/attempt_1b0195cebb59f27a/RESULT.json'
META = SOURCE / 'BANDPASS_SOURCE_METADATA.json'
ARCHIVE = SOURCE / 'sources/wmap_bandpass_v5.tar.gz'
SEALS = {CONTRACT:'986e558508ef7691d3286e9eb6cab48a38c9ded6645fe8c3e1486280a2e14686',PRIOR:'fb137b19b2ec901604691f5d4aa62f05a29e5cbe86404c3c748bf8c8c40386df',INPUT:'d1ef7598449adff41ba8f950d048b5290efaf0f66ae056e61c8549544c763ce1',OLD:'b4c20f3595fc1148ff387df3b012ce7fd87dae4098be16a0d24dd914d183291f',PROD:'c29360ba14d7bcf72d85be285ea61228c16148d35472c9dd4759e06c1eea0ee8',META:'06f2449ec8041dd968e1b9f85bf81649434dc93763dc8931ceb562a6ef6801f1',ARCHIVE:'5f3a3d29dd2346a31f7d4d215f3d7564c0a11b5af283737a6c14edfe6f152feb'}
DA = ['K1','Ka1','Q1','Q2','V1','V2','W1','W2','W3','W4']
BANDS = {'K':['K1'],'Ka':['Ka1'],'Q':['Q1','Q2'],'V':['V1','V2'],'W':['W1','W2','W3','W4']}
DRIFT = {'K':'0.0013','Ka':'0.0012','Q':'0.0011','V':'0.0006','W':'0'}
BRANCHES = ['A_BT_1e-07','A_BT_1e-08','A_BT_1e-06','B_BT_1e-07','B_BT_1e-08','B_BT_1e-06']
now = time.monotonic()
raw = {'task_id':'R33-CMB-WMAP-PLANCK-F2-EXTENSION','role':'INDEPENDENT_NUMERIC_CHECKER','status':'STARTED','started_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),'first_failure':None,'checkpoints':[]}
def put(name, data):
    p = OUT / name
    q = p.with_suffix(p.suffix + '.tmp')
    q.write_text(json.dumps(data,indent=2,allow_nan=False,default=str)+'\n')
    os.replace(q,p)
def checkpoint(stage):
    raw['checkpoints'].append({'stage':stage,'elapsed_seconds':time.monotonic()-now,'peak_rss_kib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss})
    put('RAW.json',raw)
def require(cond, message):
    if not cond: raise AssertionError(message)
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def rel(a,b):
    import mpmath as mp
    aa=[mp.mpf(x) for x in a];bb=[mp.mpf(x) for x in b]
    require(len(aa)==len(bb),'relative comparison lengths')
    return mp.sqrt(mp.fsum((x-y)**2 for x,y in zip(aa,bb)))/max(1,mp.sqrt(mp.fsum(y*y for y in bb)))
def flat(x):
    if isinstance(x,list):
        for y in x: yield from flat(y)
    else: yield x
def band(da): return 'Ka' if da.startswith('Ka') else da[0]
def source_rows():
    import tarfile
    metadata=json.loads(META.read_text())
    with tarfile.open(ARCHIVE) as tf:
        members={Path(x.name).name:x for x in tf.getmembers() if x.isfile()}
        out=[]
        for e in metadata['entries']:
            p=SOURCE/'sources/bandpasses'/e['file']
            data=p.read_bytes()
            require(hashlib.sha256(data).hexdigest()==e['sha256'],'source hash '+e['file'])
            require(e['file'] in members and tf.extractfile(members[e['file']]).read()==data,'archive member '+e['file'])
            lines=[z.split() for z in data.decode('ascii').splitlines() if z.strip() and not z.lstrip().startswith('#')]
            require(len(lines)==201 and all(len(z)==3 for z in lines),'201x3 '+e['file'])
            out.append((e['file'],lines))
    require(len(out)==20,'20 radiometer files')
    return out
def response(mp,rows,which):
    h,k,c=map(mp.mpf,['6.62607015e-34','1.380649e-23','299792458'])
    tc,td,ns,nd=map(mp.mpf,['2.7255','20','30000000000','353000000000'])
    def B(n,T): return 2*h*n**3/(c*c*mp.expm1(h*n/(k*T)))
    def bb(n):
        x=h*n/(k*tc)
        return B(n,tc)*x/(tc*(-mp.expm1(-x)))
    bs,bd=bb(ns),bb(nd)
    def spectra(n):
        ls=mp.log(n/ns); ld=mp.log(n/nd)
        ss=bs*(n/ns)**(-1)
        sd=bd*(n/nd)**mp.mpf('1.5')*B(n,td)/B(nd,td)
        x=h*n/(k*td); xd=h*nd/(k*td)
        def g(z): return z/(-mp.expm1(-z))
        def gp(z):
            q=mp.exp(-z); return 1/(1-q)-z*q/(1-q)**2
        D=g(x)-g(xd); E=x*gp(x)-xd*gp(xd)
        return [ss,ss*ls,sd,sd*ld,sd*D,ss*ls**2,sd*ld**2,sd*D*ld,sd*(D**2-D-E)]
    det=[]; dens=[]; canc=[]; unity=[]; files=[]
    for fname,tokens in rows:
        d=band(fname.removeprefix('wmap_bandpass_'))
        shift=1+mp.mpf(DRIFT[d]) if which=='W1_CENTER_DRIFT_PROXY' else mp.mpf(1)
        nu=[mp.mpf(z[0])*10**9/shift for z in tokens]
        require(all(nu[i]<nu[i+1] for i in range(200)),'frequency order '+fname)
        b=[bb(n) for n in nu]
        sp=[spectra(n) for n in nu]
        for col in (1,2):
            g=[mp.mpf(z[col]) for z in tokens]
            weighted=[g[i]*b[i]/nu[i]**2 for i in range(201)]
            widths=[(nu[i+1]-nu[i])/2 for i in range(200)]
            den=mp.fsum(widths[i]*(weighted[i]+weighted[i+1]) for i in range(200))
            absolute=mp.fsum(widths[i]*(abs(weighted[i])+abs(weighted[i+1])) for i in range(200))
            require(den>0 and mp.isfinite(den),'positive finite denominator '+fname+':'+str(col))
            vec=[]
            for j in range(9):
                v=[g[i]*sp[i][j]/nu[i]**2 for i in range(201)]
                vec.append(mp.fsum(widths[i]*(v[i]+v[i+1]) for i in range(200))/den)
            det.append(vec);dens.append(den);canc.append(absolute/abs(den));unity.append(den/den);files.append(fname+':'+str(col))
    require(len(det)==40,'40 detectors')
    da=[]
    for name in DA:
        indices=[i for i,f in enumerate(files) if Path(f.split(':')[0]).name.startswith('wmap_bandpass_'+name) and Path(f.split(':')[0]).stem.removeprefix('wmap_bandpass_').removesuffix('_v5') in (name+'1',name+'2')]
        require(len(indices)==4,'four detectors '+name+':'+str(indices))
        da.append([mp.fsum(det[i][j] for i in indices)/4 for j in range(9)])
    bands=[[mp.fsum(da[DA.index(name)][j] for name in names)/len(names) for j in range(9)] for names in BANDS.values()]
    return {'detector':det,'DA':da,'band':bands,'denominators':dens,'cancellation':canc,'unity':unity,'detector_labels':files}
def derivative_controls(mp):
    h,k,c=map(mp.mpf,['6.62607015e-34','1.380649e-23','299792458'])
    td=mp.mpf(20); nd=mp.mpf(353)*10**9
    def B(n,T): return 2*h*n**3/(c*c*mp.expm1(h*n/(k*T)))
    out=[]
    for ghz in [20,30,70,100,217,353,600]:
        n=mp.mpf(ghz)*10**9; ld=mp.log(n/nd);x=h*n/(k*td);xd=h*nd/(k*td)
        def g(z):return z/(-mp.expm1(-z))
        def gp(z):
            q=mp.exp(-z);return 1/(1-q)-z*q/(1-q)**2
        D=g(x)-g(xd);E=x*gp(x)-xd*gp(xd)
        def dust(t,beta):return (n/nd)**beta*B(n,td*(1+t))/B(nd,td*(1+t))
        s=dust(mp.mpf(0),mp.mpf('1.5'))
        pairs=[('dust_t',s*D,mp.diff(lambda t:dust(t,mp.mpf('1.5')),mp.mpf(0))),('dust_tt',s*(D*D-D-E),mp.diff(lambda t:dust(t,mp.mpf('1.5')),mp.mpf(0),2)),('dust_beta_t',s*D*ld,mp.diff(lambda t:dust(t,mp.mpf('1.5'))*ld,mp.mpf(0)))]
        for name,a,b in pairs:
            err=abs(a-b)/max(1,abs(b));out.append({'ghz':ghz,'control':name,'scaled_error':float(err)})
            require(err<=mp.mpf('1e-30'),'derivative '+name+' '+str(ghz))
        if ghz==353: require(D==0 and ld==0,'dust reference zeros')
        if ghz==30: require(mp.log(n/(mp.mpf(30)*10**9))==0,'synch reference zero')
    return out
def analyze(mp,rows,producer,controls=True):
    n=len(rows);F=mp.matrix(rows);a=mp.matrix([1]*n)
    scales=[mp.sqrt(mp.fsum(F[i,j]**2 for i in range(n))) for j in range(9)]
    require(all(x>0 for x in scales),'nonzero nuisance norm')
    N=mp.matrix([[F[i,j]/scales[j] for j in range(9)] for i in range(n)])
    U,s,V=mp.svd_r(N);aa=mp.matrix([[N[i,j] for j in range(9)]+[1/mp.sqrt(n)] for i in range(n)])
    _,sa,_=mp.svd_r(aa)
    s=list(s);sa=list(sa)
    def cls(x):return 'RESOLVED' if x>=mp.mpf('1e-10') else 'UNRESOLVED' if x<=mp.mpf('1e-12') else 'HOLD'
    classes=list(map(cls,s));augclasses=list(map(cls,sa))
    rank=classes.count('RESOLVED');arank=augclasses.count('RESOLVED')
    # SVD U spans the nuisance columns; use orthogonal factors, never I-FF+.
    q=a.copy()
    for j in range(rank):
        coeff=mp.fsum(U[i,j]*a[i] for i in range(n))
        for i in range(n):q[i]-=U[i,j]*coeff
    d=mp.norm(q)/mp.sqrt(n)
    result={'raw_matrix':[[float(F[i,j]) for j in range(9)] for i in range(n)],'raw_matrix_120':[[str(F[i,j]) for j in range(9)] for i in range(n)] if controls else None,'column_scales':[str(x) for x in scales], 'nuisance_singular_values':[str(x) for x in s], 'augmented_singular_values':[str(x) for x in sa], 'nuisance_classes':classes,'augmented_classes':augclasses,'nuisance_rank':rank,'augmented_rank':arank,'rank_increments_from_accepted_7':[rank-7,arank-7],'principal_angle_sine':str(d),'principal_angle_rad':str(mp.asin(d)),'resolved_condition':str(s[0]/s[rank-1]) if rank else None}
    require(all(x!='HOLD' for x in classes+augclasses),'ambiguous singular threshold')
    ps=producer['normalized_singular_values'];pas=producer['normalized_augmented_singular_values']
    for label,vals,ref in [('nuisance',s,ps),('augmented',sa,pas)]:
        require(len(vals)==len(ref),'spectrum length '+label)
        for i,(x,y) in enumerate(zip(vals,ref)):
            require(cls(x)==cls(mp.mpf(float(y))),'producer classification '+label+':'+str(i))
            if cls(x)=='RESOLVED':require(abs(x-mp.mpf(float(y)))<=mp.mpf('1e-10') or abs(x-mp.mpf(float(y)))/abs(x)<=mp.mpf('1e-8'),'producer singular '+label+':'+str(i))
    if rank==9 and arank==10 and d>=mp.mpf('1e-10'):
        denom=mp.fsum(a[i]*q[i] for i in range(n));require(denom>0,'positive quotient denominator')
        w=q/denom;wa=mp.fsum(w[i]*a[i] for i in range(n));wf=[mp.fsum(w[i]*F[i,j] for i in range(n)) for j in range(9)];wn=[wf[j]/scales[j] for j in range(9)]
        require(abs(wa-1)<=mp.mpf('1e-9') and mp.norm(mp.matrix(wn))<=mp.mpf('1e-9'),'quotient residual')
        result.update({'status':'RESOLVED_FINITE_F2_QUOTIENT','w':[str(w[i]) for i in range(n)],'wTa':str(wa),'wTF_raw':[str(x) for x in wf],'wTF_normalized':[str(x) for x in wn],'w_norm2':str(mp.norm(w)),'w_norm1':str(mp.fsum(abs(x) for x in w)),'w_norminf':str(max(abs(x) for x in w)),'full24_HA_column_residuals':[str(abs(wa-1))]*24,'full24_HB_column_residuals':[[str(abs(x)) for x in wf] for _ in range(24)],'full24_identified_target_rank':24})
    elif arank==rank and d<=mp.mpf('1e-12') and rank==9:
        c=mp.lu_solve(F.T*F,F.T*a);res=mp.norm(F*c-a)/mp.sqrt(n)
        require(res<=mp.mpf('1e-10'),'confounding witness residual')
        result.update({'status':'NUMERICAL_F2_CONFOUNDING','coefficients_9':[str(x) for x in c],'relative_residual':str(res),'full24_cancellation_residuals':[str(res)]*24,'full24_identified_target_rank':0})
    else:result['status']='NUMERIC_RANK_HOLD'
    # Synthetic controls use exact column identities and a separate rank probe.
    if controls:
        dup=mp.matrix([[N[i,j] if j!=8 else N[i,0] for j in range(9)] for i in range(n)])
        _,sd,_=mp.svd_r(dup)
        duplicate_rank=sum(cls(x)=='RESOLVED' for x in sd)
        require(duplicate_rank<rank,'duplicate nuisance rank loss')
        blackbody_witness=[str(a[i]-a[i]) for i in range(n)]
        require(max(abs(mp.mpf(x)) for x in blackbody_witness)==0,'blackbody exact cancellation')
        resc=mp.matrix([[N[i,j]*(j+1) for j in range(9)] for i in range(n)])
        _,sr,_=mp.svd_r(resc)
        require(sum(cls(x)=='RESOLVED' for x in sr)==rank,'rescaling rank')
        result['synthetic_controls']={'duplicate_rank':duplicate_rank,'blackbody_full24_residuals':['0']*24,'column_rescaling_rank':rank,'synthetic_only':True}
    return result
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--check-go',required=True);args=ap.parse_args()
    go=Path(args.check_go);require(go.is_file(),'controller CHECK_GO absent')
    g=json.loads(go.read_text());require(g.get('decision')=='CHECK_GO' and g.get('task_id')=='R33-CMB-WMAP-PLANCK-F2-EXTENSION','CHECK_GO invalid')
    for p,h in SEALS.items():require(sha(p)==h,'input seal '+str(p))
    require(g.get('candidate_sha256')==SEALS[PROD] and g.get('contract_sha256')==SEALS[CONTRACT] and g.get('input_sha256')==SEALS[INPUT] and g.get('source_sha256')==sha(Path(__file__)),'GO seals')
    require(not (OUT/'RESULT.json').exists(),'one-shot result already exists')
    def interrupted(signum, frame): raise TimeoutError('checker signal '+str(signum))
    signal.signal(signal.SIGALRM,interrupted)
    signal.signal(signal.SIGTERM,interrupted)
    signal.alarm(174)
    resource.setrlimit(resource.RLIMIT_AS,(1073741824,1073741824))
    os.environ['OPENBLAS_NUM_THREADS']='1';os.environ['OMP_NUM_THREADS']='1';os.environ['MKL_NUM_THREADS']='1'
    import mpmath as mp
    import numpy as np
    raw['environment']={'python':sys.version.split()[0],'mpmath':mp.__version__,'numpy':np.__version__}
    checkpoint('seals_and_environment')
    source=source_rows();old=json.loads(OLD.read_text());prod=json.loads(PROD.read_text())
    require(set(prod['branches'])=={b+'__'+w for b in BRANCHES for w in DRIFT_W},'24 matrix conventions')
    by_precision={}
    for precision in [80,120]:
        mp.mp.dps=precision
        by_precision[precision]={}
        for w in DRIFT_W:
            by_precision[precision][w]=response(mp,source,w)
            checkpoint('WMAP_'+str(precision)+'_'+w)
    mp.mp.dps=120
    derivative=derivative_controls(mp);checkpoint('derivatives')
    wmap={}
    for w in DRIFT_W:
        high=by_precision[120][w];low=by_precision[80][w];p=prod['wmap_branches'][w]
        comparisons={}
        for field,prodfield in [('detector','detector_matrix_40x9'),('DA','DA_matrix_10x9'),('band','band_matrix_5x9')]:
            err=rel(list(flat(low[field])),list(flat(high[field])))
            perr=rel(list(flat(p[prodfield])),list(flat(high[field])))
            require(err<=mp.mpf('1e-50'),'80/120 '+w+' '+field+':'+str(err))
            require(perr<=mp.mpf('1e-11'),'producer/120 '+w+' '+field+':'+str(perr))
            comparisons[field]={'mp80_mp120_relative_frobenius':str(err),'producer_mp120_relative_frobenius':str(perr)}
        require(len(high['unity'])==40 and all(x==1 for x in high['unity']),'40 detector CMB unity')
        wmap[w]={'comparisons':comparisons,'detector_matrix_40x9':[[str(x) for x in row] for row in high['detector']],'DA_matrix_10x9':[[str(x) for x in row] for row in high['DA']],'band_matrix_5x9':[[str(x) for x in row] for row in high['band']],'detector_denominators':[str(x) for x in high['denominators']],'denominator_cancellation_factors':[str(x) for x in high['cancellation']],'detector_CMB_unity':[str(x) for x in high['unity']]}
    checkpoint('response_comparisons')
    branches={}
    for w in DRIFT_W:
        high=by_precision[120][w];low=by_precision[80][w]
        for b in BRANCHES:
            key=b+'__'+w;p=prod['branches'][key]
            oldrows=old['branches'][b]['F2']['matrix_7xk']
            require(oldrows==p['Planck_rows_exact_binary64'],'old seven binary64 exact producer reuse '+key)
            require(len(oldrows)==7 and all(len(row)==9 for row in oldrows),'old seven shape '+key)
            result={}
            for name,new in [('F17',high['DA']),('F12',high['band'])]:
                matrix=[[mp.mpf(float(x)) for x in row] for row in oldrows]+new
                reference=p[name]
                own=analyze(mp,matrix,reference)
                require(own['status']==reference['status'],'status disagreement '+key+' '+name)
                result[name]=own
                # Same 80-digit source response, exact binary64 Planck rows.
                lownew=low['DA'] if name=='F17' else low['band']
                lowmatrix=[[mp.mpf(float(x)) for x in row] for row in oldrows]+lownew
                mp.mp.dps=80
                lowans=analyze(mp,lowmatrix,reference,controls=False)
                mp.mp.dps=120
                require(lowans['status']==own['status'],'80/120 classification '+key+' '+name)
                require(lowans['nuisance_classes']==own['nuisance_classes'] and lowans['augmented_classes']==own['augmented_classes'],'80/120 singular classification '+key+' '+name)
                result[name]['precision80_classification']=lowans['status']
                result[name]['precision80_spectra']={'nuisance':lowans['nuisance_singular_values'],'augmented':lowans['augmented_singular_values']}
                for spec in ['nuisance_singular_values','augmented_singular_values']:
                    for hi,lo in zip(own[spec],lowans[spec]):
                        hi=mp.mpf(hi);lo=mp.mpf(lo)
                        for threshold in (mp.mpf('1e-10'),mp.mpf('1e-12')):
                            require(abs(hi-threshold)>abs(hi-lo),'precision straddles rank boundary '+key+' '+name+' '+spec)
                require(rel(list(flat(p[name]['raw_matrix'])),list(flat(own['raw_matrix_120'])))<=mp.mpf('1e-11'),'producer raw matrix '+key+' '+name)
            f17=result['F17']['raw_matrix'];f12=result['F12']['raw_matrix']
            compressed=f17[:7]+[[sum(f17[7+DA.index(x)][j] for x in group)/len(group) for j in range(9)] for group in BANDS.values()]
            ce=rel(list(flat(compressed)),list(flat(f12)))
            require(ce<=mp.mpf('1e-13'),'C compression '+key)
            result['compression_relative_frobenius']=str(ce)
            if result['F12']['status']=='RESOLVED_FINITE_F2_QUOTIENT':
                ww=[mp.mpf(x) for x in result['F12']['w']]
                lifted=ww[:7]+[ww[7+list(BANDS).index(band(name))]/len(BANDS[band(name)]) for name in DA]
                vector=[mp.fsum(lifted[i]*mp.mpf(f17[i][j]) for i in range(17)) for j in range(9)]
                require(abs(mp.fsum(lifted)-1)<=mp.mpf('1e-9') and mp.norm(mp.matrix(vector))<=mp.mpf('1e-9'),'lifted weights '+key)
                result['lifted_compressed_weight']={'w17':[str(x) for x in lifted],'full24_HA_column_residuals':[str(abs(mp.fsum(lifted)-1))]*24,'full24_HB_column_residuals':[[str(abs(x)) for x in vector] for _ in range(24)]}
            branches[key]=result
            checkpoint('branch_'+key)
    out={'task_id':raw['task_id'],'status':'INDEPENDENT_NUMERIC_CHECK_PASS','independent_scientific_admission':'PENDING_FRESH_ASTRA','claim_tier':'C0','actual_sky':'NOT_CONSUMED','old_Planck_reintegration':False,'sealed_inputs':{str(p):h for p,h in SEALS.items()},'environment':raw['environment'],'derivative_controls':derivative,'wmap_branches':wmap,'branches':branches,'diagnostic_bundle':{'x':'NOT_MEASURED','F_physical':'NOT_EVALUABLE','Pi':'NOT_CALIBRATED','Q':'NOT_EVALUATED','G_F':'NOT_APPLICABLE'},'elapsed_seconds':time.monotonic()-now,'peak_rss_kib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}
    put('RESULT.json',out);raw['status']='PASS';checkpoint('complete')
DRIFT_W=['W0_LITERAL','W1_CENTER_DRIFT_PROXY']
if __name__=='__main__':
    try:main()
    except BaseException as e:
        raw['status']='FAILED';raw['first_failure']={'type':type(e).__name__,'message':str(e),'traceback':traceback.format_exc()};checkpoint('failed')
        print(traceback.format_exc(),file=sys.stderr);sys.exit(1)
