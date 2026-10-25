"""Single bounded application of frozen M7/F_E1 inputs; invoked only by run_once.py."""
import argparse
import hashlib
import importlib.util
import itertools
import json
import math
import os
import sys
from fractions import Fraction
from pathlib import Path

sys.dont_write_bytecode = True
import numpy as np
import sympy as sp

MAPS = ('nominal', 'witness_round_nearest', 'witness_one_place_outer')
CHANNELS = ('SNIa', 'FP', 'TFR', 'SBFm', 'SBFir', 'SNII', 'DirectCal')
INPUT_SHA = 'f04c2253bd33daafab55963793135b70a2aabbd35f2eeb356ad4a625a32b65db'
CONTRACT_SHA = '54006747ecd39827ed9022031a9f03aaf0c1f90474f014dcf22e37a5b49c13e6'

def fail(message):
    raise RuntimeError(message)

def digest(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()

def exact_float(value):
    if type(value) not in (float, int) or not math.isfinite(float(value)):
        fail('nonfinite or nonnumeric serialized matrix entry')
    f = Fraction.from_float(float(value))
    return sp.Rational(f.numerator, f.denominator)

def matrix(data, shape):
    a = np.asarray(data, dtype=np.float64)
    if a.shape != shape or not np.isfinite(a).all():
        fail(f'matrix shape/finite failure, wanted {shape}, got {a.shape}')
    return sp.Matrix(shape[0], shape[1], [exact_float(float(x)) for x in a.flat])

def rat(x):
    q = sp.Rational(x)
    return [str(q.p), str(q.q)]

def rats(mat):
    return [[rat(mat[i,j]) for j in range(mat.cols)] for i in range(mat.rows)]

def rel(a,b):
    return float(np.linalg.norm(a-b, 'fro') / max(1., np.linalg.norm(a,'fro'), np.linalg.norm(b,'fro')))

def exact_rank(m):
    for cols in itertools.combinations(range(7), 5):
        d = m[:, list(cols)].det(method='domain-ge')
        if d != 0:
            return 5, {'columns_zero_based':list(cols), 'determinant':rat(d)}
    return int(m.rank()), None

def import_generic(path):
    spec = importlib.util.spec_from_file_location('accepted_covariance_image', path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--input',required=True)
    ap.add_argument('--output',required=True)
    ns=ap.parse_args()
    inp=Path(ns.input); out=Path(ns.output)
    if digest(inp)!=INPUT_SHA: fail('INPUT_SHA_MISMATCH')
    cfg=json.loads(inp.read_text())
    if cfg['sources']['consumer_contract']['sha256'] != CONTRACT_SHA: fail('CONTRACT_BINDING_MISMATCH')
    for name,src in cfg['sources'].items():
        p=Path(src['path'])
        if not p.is_file() or p.stat().st_size!=src['bytes'] or digest(p)!=src['sha256']:
            fail(f'SOURCE_IDENTITY_MISMATCH:{name}:{p}')
    if cfg['accepted_candidate_identities']['actual_response']!='sha256:'+cfg['sources']['actual_response']['sha256'] or cfg['accepted_candidate_identities']['actual_response_review_raw']!='sha256:'+cfg['sources']['actual_response_review_raw']['sha256']:
        fail('REVIEW_BINDING_MISMATCH')
    response=json.loads(Path(cfg['sources']['actual_response']['path']).read_text())
    e1=json.loads(Path(cfg['sources']['e1_saved_result']['path']).read_text())
    locked=json.loads(Path(cfg['sources']['locked_parameters']['path']).read_text())
    fb=cfg['field_bindings']
    if tuple(fb['map_names'])!=MAPS or tuple(fb['channel_order'])!=CHANNELS or fb['nuisances']!=14 or fb['selected_rows']!=35970: fail('FIELD_BINDING_MISMATCH')
    if tuple(response['response']['channel_names'])!=CHANNELS or response['response']['n']!=35970 or set(response['response']['maps'])!=set(MAPS): fail('RESPONSE_METADATA_MISMATCH')
    if e1['source_comparisons']['all']['n']!=35970 or e1['source_comparisons']['all']['nuisance_rank']!=14 or e1['reference']['H0_km_s_Mpc']!=74.6 or e1['reference']['Omega_m']!=0.3153: fail('E1_SOURCE_CONTEXT_MISMATCH')
    with np.load(cfg['sources']['group_operator']['path'],allow_pickle=False) as z:
        if tuple(z['channel_names'].tolist())!=CHANNELS or tuple(z['width_names'].tolist())!=('round_nearest','one_place_outer') or z['selected_pgc'].shape!=(35970,) or hashlib.sha256(z['selected_pgc'].tobytes()).hexdigest()!=fb['selected_order_sha256'] or z['selected_nominal_A7'].shape!=(35970,7) or z['selected_witness_A7'].shape!=(35970,2,7):
            fail('GROUP_OPERATOR_METADATA_MISMATCH')
    f=matrix(e1['source_comparisons']['all']['schur_fisher'],(5,5))
    if f!=f.T: fail('F_EXACT_ASYMMETRIC')
    minors=[f[:k,:k].det(method='domain-ge') for k in range(1,6)]
    if any(d<=0 for d in minors): fail('F_EXACT_NOT_SPD')
    cref=f.inv()
    mod=import_generic(cfg['sources']['generic_module']['path'])
    cert={'source_input_sha256':INPUT_SHA,'source_hashes':{k:v['sha256'] for k,v in cfg['sources'].items()},'F_E1_dyadic':rats(f),'F_leading_principal_minors':[rat(x) for x in minors],'C_ref_exact_inverse':rats(cref),'maps':{}}
    result={'status':'SCOPED_APPLICATION_CANDIDATE','claim_tier':'transfer-free finite serialized-input algebra and working numerical profiles','source_input_sha256':INPUT_SHA,'reference':'C_ref = exact inverse of saved source_comparisons.all.schur_fisher; working comparison only','units':{'M':'dimensionless','F_E1':'mag^-2','C_ref':'mag^2','Gamma':'mag^2','tau':'mag'},'channel_order':CHANNELS,'selected_rows':35970,'nuisances':14,'map_order':MAPS,'maps':{},'full_covariance_candidate':'Cov(theta)=[K,M,K J_v] Omega [K,M,K J_v]^T, including measurement-calibration, measurement-PV and calibration-PV cross blocks and their transposes','physical_confidence_status':'HOLD_MISSING_TOTAL_MEAN_COVARIANCE_RESPONSE_ASSUMPTIONS','physical_x_F_Pi_Q_G_F':'HOLD','historical_accounting':'UNCHANGED'}
    arrays={'F_E1':np.array(f,dtype=float),'C_ref':np.array(cref,dtype=float),'z_grid':np.linspace(0.,2.,101)}
    for name in MAPS:
        m=matrix(response['response']['maps'][name]['signed_M7_5x7'],(5,7))
        rank,witness=exact_rank(m)
        one=sp.ones(7,1)
        common=m*one
        split=m[:,:6]*sp.ones(6,1)+m[:,6]
        cols=[m[:,j] for j in range(7)]
        terms=[]
        tensor=np.zeros((7,7,5,5),dtype=float)
        for i in range(7):
            for j in range(i,7):
                c=cols[i]*cols[j].T if i==j else cols[i]*cols[j].T+cols[j]*cols[i].T
                terms.append({'i':i,'j':j,'coefficient':rats(c)})
                tensor[i,j]=np.array(c,dtype=float)
                if i!=j: tensor[j,i]=tensor[i,j]
        def reconstruct(g):
            return sum((sp.Rational(int(g[i,j])) * (cols[i]*cols[j].T if i==j else cols[i]*cols[j].T+cols[j]*cols[i].T) for i in range(7) for j in range(i,7)),sp.zeros(5))
        for tag,g in [('identity',sp.eye(7)),('common_shift',sp.ones(7,7)),('e1_minus_e7',(sp.eye(7)[:,0]-sp.eye(7)[:,6])*(sp.eye(7)[:,0]-sp.eye(7)[:,6]).T)]:
            if reconstruct(g)!=m*g*m.T: fail(f'28_TERM_RECONSTRUCTION:{name}:{tag}')
        directions=[np.eye(5)[i] for i in range(5)]
        directions += [np.array([1.,1.,0.,0.,0.]),np.array([1.,-1.,0.,0.,0.])]
        diagnostics=[]
        for d in directions:
            ed=sp.Matrix([exact_float(float(v)) for v in d])
            norm2=(ed.T*m*m.T*ed)[0]
            un=mod.floating_directional_diagnostic(np.array(m,dtype=float),d,covariance_class='unbounded_psd')
            tr=mod.floating_directional_diagnostic(np.array(m,dtype=float),d,covariance_class='trace',tau_squared=1.0)
            if un.get('exact_protection_proved') is not False or tr.get('exact_protection_proved') is not False: fail(f'GENERIC_PROTECTION_FLAG:{name}')
            if (norm2==0 and un.get('upper')!=0.) or (norm2!=0 and un.get('upper')!=math.inf): fail(f'GENERIC_UNBOUNDED:{name}')
            upper=tr.get('upper')
            if upper is None or Fraction.from_float(float(upper))<Fraction(int(norm2.p),int(norm2.q)): fail(f'GENERIC_TRACE_BOUND:{name}')
            diagnostics.append({'direction':d.tolist(),'exact_norm_squared':rat(norm2),'unbounded_status':un['status'],'unbounded_upper':('INFINITY' if un['upper']==math.inf else un['upper']),'trace_status':tr['status'],'trace_outward_upper':upper,'exact_protection_proved':False})
        c={'M7_dyadic':rats(m),'exact_rank':rank,'first_nonzero_5x5_minor':witness,'M7_times_ones7':rats(common),'M6_times_ones6_plus_DirectCal':rats(split),'coefficient_28':terms,'generic_diagnostics':diagnostics}
        arrays[name+'_M7']=np.array(m,dtype=float); arrays[name+'_coefficient_tensor_7x7x5x5']=tensor
        rr={'exact_rank':rank,'image':('ALL_PSD_5X5' if rank==5 else 'PSD_RANGE_RESTRICTED'),'first_nonzero_minor':witness,'common_shift_dyadic_residual':rats(common),'generic_directions':diagnostics,'inherited_rank_at_scaled_1e_10':response['response']['maps'][name]['M_rank_at_1e_10']}
        if rank==5:
            s=m*m.T; rinv=m.T*s.inv(); gam=rinv*cref*rinv.T; tmatch=sp.trace(gam)
            if m*rinv!=sp.eye(5) or m*gam*m.T!=cref or tmatch<=0: fail(f'EXACT_LIFT_IDENTITY:{name}')
            c.update({'S':rats(s),'right_inverse':rats(rinv),'Gamma_star':rats(gam),'t_match':rat(tmatch),'right_inverse_identity':True,'target_covariance_identity':True})
            mf=np.array(m,dtype=float); ff=np.array(f,dtype=float); cf=np.array(cref,dtype=float); gf=np.array(gam,dtype=float)
            rf=np.linalg.cholesky(ff).T; w=rf@mf; h=w@w.T
            eig,q=np.linalg.eigh(h); order=np.argsort(eig)[::-1]; eig=eig[order]; q=q[:,order]
            if not np.isfinite(eig).all() or np.min(eig)<=0: fail(f'NUMERICAL_MODE_HOLD:{name}')
            for k in range(5):
                pivot=np.argmax(np.abs(q[:,k]))
                if q[pivot,k]<0: q[:,k]*=-1
            u=rf.T@q; resp=mf.T@u
            proj=np.array([np.outer(q[:,k],q[:,k]) for k in range(5)])
            if rel(h,q@np.diag(eig)@q.T)>1e-10 or rel(cf,mf@gf@mf.T)>1e-10 or rel(np.eye(5),u.T@cf@u)>1e-10:
                fail(f'NUMERICAL_RECONSTRUCTION_HOLD:{name}')
            for k in range(5):
                if np.linalg.norm(h@q[:,k]-eig[k]*q[:,k])/max(1.,np.linalg.norm(h),abs(eig[k]))>1e-10: fail(f'EIGEN_RESIDUAL_HOLD:{name}:{k}')
            tfirst=1./eig[0]; spec=float(np.linalg.eigvalsh(gf)[-1]); tau_first=math.sqrt(tfirst); tau_match=math.sqrt(float(tmatch))
            z=arrays['z_grid']; trace_max=z*z; spectral_max=z*z; trace_total=z*z; spectral_total=z*z*eig.sum()/eig[0]
            arrays.update({name+'_S':np.array(s,dtype=float),name+'_R':np.array(rinv,dtype=float),name+'_Gamma_star':gf,name+'_W':w,name+'_H':h,name+'_eigenvalues':eig,name+'_eigenvectors':q,name+'_eigenprojectors':proj,name+'_signed_contrasts_u':u,name+'_channel_responses':resp,name+'_trace_max_eigenvalue_profile':trace_max,name+'_spectral_max_eigenvalue_profile':spectral_max,name+'_trace_total_variance_profile':trace_total,name+'_spectral_total_variance_profile':spectral_total})
            rr.update({'t_match_mag2':float(tmatch),'t_match_exact':rat(tmatch),'tau_match_mag':tau_match,'t_first_mag2':tfirst,'tau_first_mag':tau_first,'t_spec_match_mag2':spec,'working_sensitivity_eigenvalues_mag_minus2':eig.tolist(),'signed_contrasts_u':u.T.tolist(),'channel_responses':resp.T.tolist(),'relative_residuals':{'H_eigendecomposition':rel(h,q@np.diag(eig)@q.T),'target_covariance':rel(cf,mf@gf@mf.T),'contrast_normalization':rel(np.eye(5),u.T@cf@u)},'profiles':{'z':z.tolist(),'trace_max_eigenvalue':trace_max.tolist(),'spectral_max_eigenvalue':spectral_max.tolist(),'trace_total_working_variance':trace_total.tolist(),'spectral_total_working_variance':spectral_total.tolist()}})
        else:
            rr.update({'t_match':'INFEASIBLE','t_first':'UNAVAILABLE','profile_status':'RANK_DEFICIENT_RESTRICTED_RANGE','range_basis_exact':rats(m.columnspace() and sp.Matrix.hstack(*m.columnspace()) or sp.zeros(5,0))})
        cert['maps'][name]=c; result['maps'][name]=rr
    out.mkdir(parents=True,exist_ok=False)
    (out/'MATRIX_CERTIFICATES.json').write_text(json.dumps(cert,indent=2)+'\n')
    (out/'RESULT.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    np.savez_compressed(out/'covariance_profiles.npz',**arrays)
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_pdf import PdfPages
    fig,axs=plt.subplots(2,3,figsize=(15,9)); colors=['#3157a4','#c55a21','#487f56']
    for idx,name in enumerate(MAPS):
        rr=result['maps'][name]; label=name.replace('witness_','')
        if rr['exact_rank']!=5: continue
        eig=np.array(rr['working_sensitivity_eigenvalues_mag_minus2']); z=arrays['z_grid']
        axs[0,0].plot(np.arange(1,6),eig,marker='o',color=colors[idx],label=label)
        axs[0,1].plot(z,arrays[name+'_trace_max_eigenvalue_profile'],color=colors[idx],label=label+' max / trace total')
        axs[0,1].plot(z,arrays[name+'_spectral_max_eigenvalue_profile'],color=colors[idx],linestyle='-.',alpha=.5)
        axs[0,1].plot(z,arrays[name+'_spectral_total_variance_profile'],color=colors[idx],linestyle='--',label=label+' spectral total')
    axs[0,0].set(xlabel='mode index',ylabel='working sensitivity (mag^-2)',title='Five modes for each actual map');axs[0,0].legend(fontsize=7)
    axs[0,1].set(xlabel='z = tau / tau_first',ylabel='max eigenvalue / total variance',title='Illustrative cap profiles, 0 <= z <= 2');axs[0,1].legend(fontsize=6)
    axs[0,2].axis('off'); rows=[]
    for name in MAPS:
        rr=result['maps'][name]; rows.append([name.replace('witness_',''),f"{rr.get('t_first_mag2',float('nan')):.3g}",f"{rr.get('t_match_mag2',float('nan')):.3g}",f"{rr.get('t_spec_match_mag2',float('nan')):.3g}"])
    axs[0,2].table(cellText=rows,colLabels=['map','t_first','t_match','t_spec'],loc='center',fontsize=8)
    axs[0,2].set_title('Working budgets (mag²)')
    for j,name in enumerate(MAPS):
        ax=axs[1,j]
        if result['maps'][name]['exact_rank']==5:
            im=ax.imshow(arrays[name+'_Gamma_star'],cmap='RdBu_r');fig.colorbar(im,ax=ax,label='mag²');ax.set_title('Signed Gamma*: '+name)
        else: ax.text(.5,.5,'restricted range',ha='center',va='center')
    fig.tight_layout();fig.savefig(out/'sensitivity.pdf');plt.close(fig)
    lines=['# Actual CF4 M7 covariance application','','Serialized binary64 inputs were lifted to exact dyadic rationals. Exact identities and ranks apply only to those frozen entries. Numerical eigenvalues and square roots are diagnostics, without a rigorous radius.','', '| Map | Exact rank | t_first (mag²) | t_match (mag²) | t_spec_match (mag²) |','|---|---:|---:|---:|---:|']
    for name in MAPS:
        rr=result['maps'][name]; lines.append(f"| {name} | {rr['exact_rank']} | {rr.get('t_first_mag2','unavailable')} | {rr.get('t_match_mag2','infeasible')} | {rr.get('t_spec_match_mag2','unavailable')} |")
    lines += ['','The 28 exact coefficients preserve signed channel cross terms. The unit trace cap is an illustrative mag² normalization, not an observed bound. The common-shift fixture retains its exact binary residual. The full covariance candidate retains measurement-calibration, measurement-PV, calibration-PV and all transpose blocks. J_v, empirical Gamma, residual anchor correlations, total mean/covariance, bias set, law and physical response remain unresolved.','', 'Physical confidence: HOLD_MISSING_TOTAL_MEAN_COVARIANCE_RESPONSE_ASSUMPTIONS. Physical x, F, Pi, Q and G_F remain HOLD. Historical R9 UNKNOWN, original 17/42 and alternative 18/42, 48-task and one-use allocations remain unchanged.']
    (out/'REPORT.md').write_text('\n'.join(lines)+'\n')
    print(json.dumps({'status':'DONE','maps':{k:{'exact_rank':v['exact_rank'],'t_match_mag2':v.get('t_match_mag2')} for k,v in result['maps'].items()},'products':sorted(p.name for p in out.iterdir())},sort_keys=True))
if __name__=='__main__': main()
