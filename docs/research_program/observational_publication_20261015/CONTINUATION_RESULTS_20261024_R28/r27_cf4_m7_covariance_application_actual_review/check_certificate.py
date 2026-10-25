"""One independent finite-certificate check; never imports or reruns consume.py."""
import datetime
import hashlib
import importlib.util
import itertools
import json
import math
import os
from pathlib import Path
from fractions import Fraction as Q
import sys
import traceback

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
APP = HERE.parent / 'r27_cf4_m7_covariance_application'
PRODUCTS = APP / 'actual_run/products'
INPUT = HERE.parent / 'r27_m7_covariance_application_framing/INPUT.json'
MAPS = ('nominal', 'witness_round_nearest', 'witness_one_place_outer')
EVIDENCE = {'status': 'STARTED', 'started_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'maps': {}}

def load(p):
    return json.loads(Path(p).read_text())

def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def require(condition, label):
    if not condition:
        raise AssertionError(label)

def q(v):
    return Q(int(v[0]), int(v[1]))

def mat(v):
    return [[q(x) for x in row] for row in v]

def dyad(v):
    return [[Q.from_float(float(x)) for x in row] for row in v]

def trans(a):
    return list(map(list, zip(*a)))

def mul(a, b):
    return [[sum((x*y for x,y in zip(row,col)), Q()) for col in zip(*b)] for row in a]

def eye(n):
    return [[Q(i == j) for j in range(n)] for i in range(n)]

def determinant(a):
    b = [row[:] for row in a]
    d = Q(1)
    for k in range(len(b)):
        pivot = next((i for i in range(k,len(b)) if b[i][k]), None)
        if pivot is None:
            return Q(0)
        if pivot != k:
            b[k], b[pivot] = b[pivot], b[k]
            d = -d
        v = b[k][k]
        d *= v
        for i in range(k+1,len(b)):
            t = b[i][k]/v
            for j in range(k+1,len(b)):
                b[i][j] -= t*b[k][j]
    return d

def pair(v):
    return [str(v.numerator), str(v.denominator)]

def main():
    import numpy as np
    ack = load(HERE/'ACTUAL_ACKNOWLEDGED_REVIEW_PACKET.json')
    require(ack['launch_performed'] is True and ack['packet_id'] == '9384cb661545879805df2a71a12ad2a3e6af50377bf73750eb548ba86f29fca3', 'ACK')
    require(sha(INPUT) == 'f04c2253bd33daafab55963793135b70a2aabbd35f2eeb356ad4a625a32b65db', 'input identity')
    cfg = load(INPUT)
    for key, value in cfg['sources'].items():
        require(Path(value['path']).stat().st_size == value['bytes'] and sha(value['path']) == value['sha256'], 'source:'+key)
    hashes = {k:sha(APP/k) for k in ('consume.py','run_once.py')}
    cid = hashlib.sha256(json.dumps(hashes,sort_keys=True,separators=(',',':')).encode()).hexdigest()
    require(ack['candidate_identity'] == 'sha256:'+cid, 'candidate')
    require(sha(APP/'RESULT.json') == '2f6847d4b5295f30a4744fb71186d0cf8454ec5437f8c2f0d8207dfcc9d26236', 'standard result')
    receipt = load(APP/'actual_run/RUN_RECEIPT.json')
    for key,value in receipt['product_sha256'].items():
        require(sha(PRODUCTS/key) == value, 'product:'+key)
    EVIDENCE['provenance'] = {'candidate_sha256':cid,'input_sha256':sha(INPUT),'actual_result_sha256':sha(PRODUCTS/'RESULT.json'),'source_count':len(cfg['sources']),'products':receipt['product_sha256']}
    response = load(cfg['sources']['actual_response']['path'])
    saved_e1 = load(cfg['sources']['e1_saved_result']['path'])
    cert = load(PRODUCTS/'MATRIX_CERTIFICATES.json')
    result = load(PRODUCTS/'RESULT.json')
    f = mat(cert['F_E1_dyadic'])
    cf = mat(cert['C_ref_exact_inverse'])
    require(f == dyad(saved_e1['source_comparisons']['all']['schur_fisher']) and f == trans(f), 'exact F source/symmetry')
    minors = [determinant([row[:k] for row in f[:k]]) for k in range(1,6)]
    require(minors == list(map(q,cert['F_leading_principal_minors'])) and all(v > 0 for v in minors), 'exact F SPD')
    require(mul(f,cf) == eye(5) and cf == trans(cf), 'exact C_ref inverse')
    EVIDENCE['exact_F_SPD_and_inverse'] = True
    zfile = np.load(PRODUCTS/'covariance_profiles.npz',allow_pickle=False)
    require(all(np.isfinite(zfile[k]).all() for k in zfile.files), 'finite arrays')
    require(np.array_equal(zfile['F_E1'],np.asarray(f,dtype=float)) and np.array_equal(zfile['C_ref'],np.asarray(cf,dtype=float)), 'F/C npz')
    z = zfile['z_grid']
    require(np.array_equal(z,np.linspace(0.,2.,101)), 'z grid')
    spec = importlib.util.spec_from_file_location('frozen_generic',cfg['sources']['generic_module']['path'])
    generic = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(generic)
    observed = []
    def capture(frame, event, arg):
        if event == 'return' and frame.f_code is generic.floating_directional_diagnostic.__code__:
            observed.append((frame.f_locals['exact_response'][:],frame.f_locals['exact_norm_squared']))
    def checkclose(a,b,label,record):
        a=np.asarray(a,dtype=float); b=np.asarray(b,dtype=float)
        require(a.shape==b.shape and np.isfinite(a).all() and np.isfinite(b).all(),label+':shape/finite')
        residual=float(np.linalg.norm((a-b).ravel())/max(1.,np.linalg.norm(a.ravel()),np.linalg.norm(b.ravel())))
        require(residual<=1e-10,label)
        record[label]=residual
    for name in MAPS:
        c = cert['maps'][name]; r = result['maps'][name]
        m = mat(c['M7_dyadic'])
        require(m == dyad(response['response']['maps'][name]['signed_M7_5x7']),name+':M binding')
        witness = c['first_nonzero_5x5_minor']
        columns = witness['columns_zero_based']
        require(columns == [0,1,2,3,4],name+':lexicographic first minor')
        d=determinant([[row[j] for j in columns] for row in m])
        require(d == q(witness['determinant']) and d != 0 and c['exact_rank']==r['exact_rank']==5,name+':rank')
        s=mat(c['S']); ri=mat(c['right_inverse']); gamma=mat(c['Gamma_star'])
        require(s==mul(m,trans(m)) and mul(ri,s)==trans(m) and mul(m,ri)==eye(5),name+':right inverse')
        require(gamma==mul(mul(ri,cf),trans(ri)) and gamma==trans(gamma),name+':constructive PSD lift')
        require(mul(mul(m,gamma),trans(m))==cf,name+':exact target covariance')
        tmatch=sum((gamma[i][i] for i in range(7)),Q())
        require(tmatch==q(c['t_match'])==q(r['t_match_exact']) and tmatch>0,name+':trace')
        p=mul(ri,m)
        require(p==trans(p) and mul(p,p)==p,name+':row projector for minimum trace')
        common=[[sum(row,Q())] for row in m]
        require(common==mat(c['M7_times_ones7'])==mat(c['M6_times_ones6_plus_DirectCal'])==mat(r['common_shift_dyadic_residual']),name+':common residual')
        require(any(v[0]!=0 for v in common),name+':nonzero common residual retained')
        terms=c['coefficient_28']
        require([(t['i'],t['j']) for t in terms]==list(itertools.combinations_with_replacement(range(7),2)),name+':28 terms')
        tensor=zfile[name+'_coefficient_tensor_7x7x5x5']
        for term in terms:
            i,j=term['i'],term['j']
            expected=[[m[a][i]*m[b][j] + (m[a][j]*m[b][i] if i!=j else 0) for b in range(5)] for a in range(5)]
            require(mat(term['coefficient'])==expected,name+':exact coefficient')
            require(np.array_equal(tensor[i,j],np.asarray(expected,dtype=float)) and np.array_equal(tensor[j,i],tensor[i,j]),name+':coefficient npz')
        fixture_results=[]
        for tag,g in [('identity',eye(7)),('common_shift',[[Q(1)]*7 for _ in range(7)]),('e1_minus_e7',[[Q((i==0)-(i==6))*Q((j==0)-(j==6)) for j in range(7)] for i in range(7)])]:
            expanded=[[sum((g[t['i']][t['j']]*q(t['coefficient'][a][b]) for t in terms),Q()) for b in range(5)] for a in range(5)]
            require(expanded==mul(mul(m,g),trans(m)),name+':fixture:'+tag)
            fixture_results.append(tag)
        mf=np.asarray(m,dtype=float); ff=np.asarray(f,dtype=float); cff=np.asarray(cf,dtype=float); gf=np.asarray(gamma,dtype=float)
        require(np.array_equal(zfile[name+'_M7'],mf) and np.array_equal(zfile[name+'_Gamma_star'],gf),name+':M/Gamma npz')
        direction_records=[]
        dirs=list(np.eye(5))+[np.array([1.,1.,0.,0.,0.]),np.array([1.,-1.,0.,0.,0.])]
        require(len(c['generic_diagnostics'])==len(r['generic_directions'])==7,name+':direction count')
        for di,(direction,stored,reported) in enumerate(zip(dirs,c['generic_diagnostics'],r['generic_directions'])):
            exact_response=[sum((Q.from_float(float(direction[a]))*m[a][j] for a in range(5)),Q()) for j in range(7)]
            norm=sum((v*v for v in exact_response),Q())
            require(stored==reported and norm==q(stored['exact_norm_squared']) and direction.tolist()==stored['direction'],name+':saved exact contraction')
            observed.clear(); sys.setprofile(capture)
            try:
                un=generic.floating_directional_diagnostic(mf,direction,covariance_class='unbounded_psd')
                bounded=generic.floating_directional_diagnostic(mf,direction,covariance_class='trace',tau_squared=1.)
            finally:
                sys.setprofile(None)
            require(observed==[(exact_response,norm),(exact_response,norm)],name+':generic exact response/norm')
            require(un['exact_protection_proved'] is False and bounded['exact_protection_proved'] is False,name+':protection flags')
            require(un['upper']==(math.inf if norm else 0.) and stored['unbounded_upper']==('INFINITY' if norm else 0.),name+':unbounded')
            upper=bounded['upper']
            require(upper is not None and math.isfinite(upper) and Q.from_float(upper)>=norm and upper==stored['trace_outward_upper'],name+':exact outward enclosure')
            require(un['status']==stored['unbounded_status'] and bounded['status']==stored['trace_status'],name+':generic statuses')
            direction_records.append({'direction':direction.tolist(),'exact_response':[pair(v) for v in exact_response],'exact_norm_squared':pair(norm),'captured_generic_exact_response_and_norm_agree':True,'outward_upper':upper,'exact_outward_enclosure':True})
        residuals={}
        rf=np.linalg.cholesky(ff).T; w=rf@mf; h=w@w.T
        eig=zfile[name+'_eigenvalues']; vectors=zfile[name+'_eigenvectors']; u=zfile[name+'_signed_contrasts_u']
        require(eig.shape==(5,) and np.all(eig>0) and np.all(eig[:-1]>=eig[1:]),name+':positive sorted spectrum')
        for key,expected in [('S',np.asarray(s,dtype=float)),('R',np.asarray(ri,dtype=float)),('W',w),('H',h),('signed_contrasts_u',rf.T@vectors),('channel_responses',mf.T@u)]:
            checkclose(zfile[name+'_'+key],expected,key,residuals)
        for label,a,b in [('eigen reconstruction',vectors@np.diag(eig)@vectors.T,h),('orthonormal eigenvectors',vectors.T@vectors,np.eye(5)),('eigen residual',h@vectors,vectors*eig),('contrast normalization',u.T@cff@u,np.eye(5)),('numerical covariance',mf@gf@mf.T,cff),('JSON signed modes',np.asarray(r['signed_contrasts_u']).T,u),('JSON channel responses',np.asarray(r['channel_responses']).T,mf.T@u),('JSON eigenvalues',r['working_sensitivity_eigenvalues_mag_minus2'],eig),('projectors',zfile[name+'_eigenprojectors'],np.asarray([np.outer(vectors[:,i],vectors[:,i]) for i in range(5)]))]:
            checkclose(a,b,label,residuals)
        for key,expected in [('t_match_mag2',float(tmatch)),('tau_match_mag',math.sqrt(float(tmatch))),('t_first_mag2',1/eig[0]),('tau_first_mag',math.sqrt(1/eig[0])),('t_spec_match_mag2',np.linalg.eigvalsh(gf)[-1])]:
            checkclose(r[key],expected,key,residuals)
        for prefix,jsonkey,expected in [('trace_max_eigenvalue_profile','trace_max_eigenvalue',z*z),('spectral_max_eigenvalue_profile','spectral_max_eigenvalue',z*z),('trace_total_variance_profile','trace_total_working_variance',z*z),('spectral_total_variance_profile','spectral_total_working_variance',z*z*eig.sum()/eig[0])]:
            checkclose(zfile[name+'_'+prefix],expected,prefix,residuals)
            checkclose(r['profiles'][jsonkey],expected,'JSON '+prefix,residuals)
        EVIDENCE['maps'][name]={'exact_rank':5,'exact_right_inverse_and_covariance_lift':True,'minimum_trace_row_projector':True,'exact_t_match':[str(tmatch.numerator),str(tmatch.denominator)],'common_residual_nonzero':True,'exact_28_terms_and_fixtures':fixture_results,'generic_directions':direction_records,'numerical_residuals':residuals,'max_scaled_residual':max(residuals.values())}
    require(result['physical_confidence_status']=='HOLD_MISSING_TOTAL_MEAN_COVARIANCE_RESPONSE_ASSUMPTIONS' and result['physical_x_F_Pi_Q_G_F']=='HOLD','claim holds')
    EVIDENCE.update(status='PASS',exact_input_scope='Parsed serialized binary64 entries only',prescribed_direction_count=21,generic_function_calls=42,full_cohort_recomputations=0,producer_reruns=0,coefficient_tensor_convention='Sum i<=j only; symmetric lower triangle duplicates the 28 independent coefficients',physical_confidence_status=result['physical_confidence_status'])

try:
    main()
except BaseException:
    EVIDENCE['status']='FAIL'
    EVIDENCE['first_failure']=traceback.format_exc()
    raise
finally:
    EVIDENCE['finished_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat()
    with open(HERE/'CHECK_RESULT.json','x') as stream:
        json.dump(EVIDENCE,stream,indent=2,sort_keys=True,allow_nan=False)
        stream.write('\n');stream.flush();os.fsync(stream.fileno())
    print(json.dumps({'status':EVIDENCE['status'],'completed_maps':list(EVIDENCE['maps'])}))
