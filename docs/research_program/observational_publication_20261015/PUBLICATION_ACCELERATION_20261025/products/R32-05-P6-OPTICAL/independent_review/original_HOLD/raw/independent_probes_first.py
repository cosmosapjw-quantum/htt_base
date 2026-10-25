"""Small independent review probes. No imports of candidate or repository code."""
from pathlib import Path
import csv, hashlib, itertools, json, math, re, subprocess
import numpy as np
from scipy.optimize import linprog

ROOT=Path('/home/cosmosapjw/Dropbox/bianchi/htt_base')
OUT=Path(__file__).resolve().parent
P=ROOT/'docs/research_program/observational_publication_20261015/PUBLICATION_ACCELERATION_20261025'
R=P/'products/R32-05-P6-OPTICAL/report'
records={}
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def record(name, passed, detail):
    records[name]={'passed':bool(passed),'detail':detail}
def near(a,b,tol=1e-12): return np.max(np.abs(np.asarray(a)-np.asarray(b)))<=tol

candidate=json.loads((R/'RESULT.json').read_text())
manifest=candidate['manifest']
mh=hashlib.sha256(json.dumps(manifest,sort_keys=True,separators=(',',':')).encode()).hexdigest()
record('candidate_identity',sha(R/'RESULT.json')=='343622f6bed1197dd0e08b7c64fbfabefba74f5ec02baf9a51b839dda97ae9b3',sha(R/'RESULT.json'))
record('canonical_manifest',mh=='341346452c546de7877bf839bde8e583e37c8c461703469644ab7675edba1bfd',mh)
checked=[]
for kind,base in [('sources',ROOT),('outputs',R)]:
    for x in manifest[kind]:
        p=base/x['path']; actual=sha(p)
        checked.append({'kind':kind,'path':x['path'],'sha256':actual,'bytes':p.stat().st_size,'passed':actual==x['sha256'] and p.stat().st_size==x['bytes']})
record('all_sealed_files',all(x['passed'] for x in checked),{'count':len(checked),'mismatches':[x for x in checked if not x['passed']]})
(OUT/'raw/hash_checks.json').write_text(json.dumps(checked,indent=2)+'\n')
d=json.loads((P/'evidence/research/latest_results.json').read_text());q=d['cf4_calibration_quotient']
producer=ROOT/d['units_correction']['model_path']
record('producer_source_identity',sha(producer)==d['units_correction']['actual_model_sha256'],{'path':str(producer),'actual_sha256':sha(producer),'expected_sha256':d['units_correction']['actual_model_sha256']})

# Source-basis reconstruction without importing its producer.
b=np.array(q['apparent_b_dimensionless']); C=np.array(q['working_covariance'])
S=np.array([[b[0]/np.sqrt(2)+b[1]/np.sqrt(6),b[2]/np.sqrt(2),b[3]/np.sqrt(2)],
            [b[2]/np.sqrt(2),-b[0]/np.sqrt(2)+b[1]/np.sqrt(6),b[4]/np.sqrt(2)],
            [b[3]/np.sqrt(2),b[4]/np.sqrt(2),-2*b[1]/np.sqrt(6)]])
t=np.linalg.norm(S)
record('dimensionless_tensor',near(S,q['apparent_tensor_dimensionless']) and near(t,.03265680189321492) and near(np.linalg.eigvalsh(S),q['tensor_eigenvalues_ascending']),{'norm':t,'spectrum':np.linalg.eigvalsh(S).tolist(),'second_kappa_division_would_give':t/(5/math.log(10))})
generated=json.loads((R/'generated/retained_tensor_region.json').read_text())
record('full_five_dimensional_carrier',near(generated['C'],C) and near(generated['bhat'],b) and near(generated['tensor'],S),{'C_shape':C.shape,'C_eigenvalues':np.linalg.eigvalsh(C).tolist(),'status_fields':generated['diagnostic_statuses']})

# A nondiagonal rank-two inverse, checked through independently solved LPs.
A=np.array([[1.,2.,0.],[2.,4.,0.],[0.,0.,1.],[0.,0.,0.]])
Ap=np.linalg.pinv(A); PA=A@Ap; J=np.array([[1.,2.,0.],[0.,0.,1.]])
z=np.array([1.2,2.1,-.2,.1]); radius=.3
dirs=[np.array(x) for x in [(1.,0.),(-1.,0.),(0.,1.),(.6,-.8)]]
lp=[]
for a in dirs:
    primal=linprog(-J.T@a,A_ub=np.vstack([A,-A]),b_ub=np.r_[z+radius,-z+radius],bounds=[(None,None)]*3,method='highs')
    w=-Ap.T@J.T@a
    error=linprog(-w,A_eq=np.eye(4)-PA,b_eq=(np.eye(4)-PA)@z,bounds=[(-radius,radius)]*4,method='highs')
    support=float(a@J@Ap@z-error.fun)
    lp.append({'a':a.tolist(),'primal_status':primal.status,'error_status':error.status,'primal_support':-primal.fun,'formula_support':support,'residual_max':float(np.max(np.abs(z-A@primal.x)))})
record('finite_inverse_nondiagonal_range_support',all(v['primal_status']==0 and v['error_status']==0 and abs(v['primal_support']-v['formula_support'])<1e-12 and v['residual_max']<=radius+1e-12 for v in lp),lp)
nullprobe=linprog([-1.,0.,0.],A_ub=np.vstack([A,-A]),b_ub=np.r_[z+radius,-z+radius],bounds=[(None,None)]*3,method='highs')
badz=z.copy();badz[3]=.4
bad=linprog([-1.,0.,0.],A_ub=np.vstack([A,-A]),b_ub=np.r_[badz+radius,-badz+radius],bounds=[(None,None)]*3,method='highs')
record('kernel_support_feasible_vs_infeasible',nullprobe.status==3 and bad.status==2,{'feasible_kernel_visible_LP_status':nullprobe.status,'infeasible_kernel_visible_LP_status':bad.status,'meaning':'status 3 unbounded; status 2 infeasible'})
counterexample={'file':'science/MANUSCRIPT.md','line':172,'rendered_source':'report/main.tex:183','A':[[1,0],[0,0]],'z':[0,2],'error_set':'closed Euclidean unit ball','J':[[0,1]],'a':[1],'compatibility_requirement':'e_2=2, impossible for norm(e)<=1','E_z':'EMPTY','Theta_lin':'EMPTY','J_transpose_a':[0,1],'kernel_component':'nonzero','literal_claimed_support':'+infinity','actual_support':'-infinity under the extended-real convention; otherwise undefined, never +infinity','minimal_fix':'Require E_z nonempty before the infinite-support assertion, and state the empty-image convention.'}
records['THEOREM_2_EMPTY_SET_COUNTEREXAMPLE']={'passed':False,'detail':counterexample}

# Sampling support with nonsymmetric whitening, nuisance removal and signed rows.
W=np.array([[1.,.3,0.],[0.,2.,.2],[0.,0.,.5]])
N=np.ones((3,1));U=W@N;PN=np.eye(3)-U@np.linalg.pinv(U)
L=PN@W; ell=np.array([1.,2.,1.5]); ewidth=np.array([.02,.01,.03]);kappa=5/math.log(10);eps=.3
tail=kappa*eps**2/(2*(1-eps));aa=np.array([1.,-2.,.5])
corners=np.array(list(itertools.product([-1.,1.],repeat=3)))
values=[aa@L@(ewidth*e+tail*ell*v) for e in corners for v in corners]
formula=np.sum(ewidth*np.abs(L.T@aa))+tail*np.sum(ell*np.abs(L.T@aa))
record('sampling_outer_support_signed_window',near(max(values),formula) and near(L@N,0),{'vertex_max':max(values),'formula':formula,'nuisance_residual':float(np.linalg.norm(L@N))})

# Full-C exposed point witnesses establish projection, not a conditional section.
fd=json.loads((R/'generated/figure_data.json').read_text());angles=np.array(fd['phi'])
proj=[]
for eta in [0.,.005,.01]:
    boundary=np.array(fd['projections'][str(int(eta)) if eta==0 else str(eta)]['boundary'])
    worst=0.; outside=0.
    for i in [0,83,211,417,620,720]:
        a2=np.array([math.cos(angles[i]),math.sin(angles[i])]);a5=np.r_[a2,[0.,0.,0.]]
        e=C@a5/np.sqrt(a5@C@a5)
        full=b+e+eta*a5
        worst=max(worst,float(np.linalg.norm(full[:2]-boundary[i])))
        outside=max(outside,float(np.linalg.norm(full[2:])))
        assert near(e@np.linalg.solve(C,e),1.)
    proj.append({'eta':eta,'maximum_witness_projection_error':worst,'largest_hidden_coordinate_norm':outside})
schur=C[:2,:2]-C[:2,2:]@np.linalg.solve(C[2:,2:],C[2:,:2])
record('projected_boundaries_have_full_set_witnesses',all(x['maximum_witness_projection_error']<1e-12 for x in proj),{'witnesses':proj,'projection_x_support':float(np.sqrt(C[0,0])),'centered_section_x_support':float(np.sqrt(schur[0,0])),'absolute_zero_hidden_section_empty':bool(b[2:]@np.linalg.solve(C[2:,2:],b[2:])>1),'zero_hidden_minimum_ellipsoid_cost':float(b[2:]@np.linalg.solve(C[2:,2:],b[2:]))})

# A singular PSD shape and a nonidentity response still attain the support.
Cs=np.diag([4.,0.,1.]);rootCs=np.diag([2.,0.,1.]);G=np.array([[1.,2.],[0.,1.],[1.,0.]])
a=np.array([.2,-.4,.7]);rho=.3;eta=.2
u=rho*(rootCs@a)/np.linalg.norm(rootCs@a);v=eta*(G.T@a)/np.linalg.norm(G.T@a)
actual=a@(rootCs@u+G@v);bound=rho*np.sqrt(a@Cs@a)+eta*np.linalg.norm(G.T@a)
record('singular_shape_product_support',near(actual,bound),{'witness':actual,'support':bound})

# Rate bounds tested at attaining tensors; H must multiply dimensionless S.
frontier=list(csv.DictReader((R/'generated/frontier.csv').open()));intervals=[]
for row in frontier:
    r=float(row['assumed_r_Q']); Slow=S*max(0,1-r/t);Shigh=S*(1+r/t)
    low=np.linalg.norm(Slow)/math.sqrt(6);high=np.linalg.norm(Shigh)/math.sqrt(6)
    rate_low=.9*low;rate_high=1.1*high
    vals=[low,high,rate_low,rate_high]
    saved=[float(row[k]) for k in ['Sigma_lower','Sigma_upper','rate_over_Hstar_lower_deltaH0.1','rate_over_Hstar_upper_deltaH0.1']]
    intervals.append({'r_Q':r,'endpoint_error':float(np.max(np.abs(np.array(vals)-saved))),'lower_positive':low>0,'expected_positive':r<t})
record('frontier_attaining_tensor_witnesses',all(v['endpoint_error']<1e-12 and v['lower_positive']==v['expected_positive'] for v in intervals),intervals)
record('rate_units_scaling',near(np.linalg.norm(7*S)/math.sqrt(6),7*t/math.sqrt(6)),{'H_ratio':7,'dimensional_rate_ratio':float(np.linalg.norm(7*S)/t),'normalized_Sigma':float(t/math.sqrt(6))})

# Direct local rest-frame contraction checks acceleration sign and vorticity kernel.
c=3.;H=.7;acc=np.array([.2,-.3,.4]);n=np.array([2.,-1.,2.])/3
sig=np.array([[.1,.02,0.],[.02,-.03,.01],[0.,.01,-.07]])
om=np.array([[0.,.03,-.04],[-.03,0.,.07],[.04,-.07,0.]])
der=np.zeros((4,4));der[0,1:]=acc/c**2;der[1:,1:]=(H*np.eye(3)+sig+om)/c
ell4=np.r_[-1.,n];contract=c*ell4@der@ell4;expected=H-acc@n/c+n@sig@n
record('local_optical_units_sign',near(contract,expected),{'contraction':contract,'H_minus_A_dot_n_over_c_plus_shear':expected,'vorticity_contraction':float(n@om@n)})

# Finite pointwise and two-weight probes only: no spherical quadrature/integration.
qvals=np.array([-.29,-.1,0.,.1,.29]);remainder=-kappa*np.log1p(qvals)+kappa*qvals
record('log_remainder_pointwise',np.max(np.abs(remainder))<=tail,{'max_remainder':float(np.max(np.abs(remainder))),'outer_bound':tail})
weights=np.array([.4,.6]);rr=np.array([.7,1.2]);delta=.1;noise=np.array([-delta,delta]);norm=weights@(rr*np.exp(-noise/kappa));ratio=np.exp(-noise/kappa)/norm
record('positive_normalized_field_error_ratio',near(weights@rr,1.) and np.all(ratio>=np.exp(-2*delta/kappa)) and np.all(ratio<=np.exp(2*delta/kappa)),{'ratios':ratio.tolist(),'bounds':[np.exp(-2*delta/kappa),np.exp(2*delta/kappa)],'scope':'finite positive-weight inequality probe, not spherical reconstruction'})

checks=json.loads((R/'generated/checks.json').read_text())['checks']
record('recorded_61_check_receipt',len(checks)==61 and all(v['passed'] for v in checks.values()),{'count':len(checks),'scope':'inspected receipt and implementation, not independent proof'})
recovery=json.loads((R/'raw/misplaced_file_recovery.json').read_text());headread=subprocess.run(['git','show','HEAD:README.md'],cwd=ROOT,capture_output=True,check=True).stdout
record('packaging_recovery_current_evidence',sha(ROOT/'README.md')==hashlib.sha256(headread).hexdigest()==recovery['README_original_HEAD_sha256'] and not (ROOT/'BUILD_REPORT.md').exists() and not (ROOT/'finalize.py').exists(),{'root_README_sha256':sha(ROOT/'README.md'),'HEAD_README_sha256':hashlib.sha256(headread).hexdigest(),'restoration_diff_bytes':(R/'raw/root_README_restoration.diff').stat().st_size,'scope':'current restoration and retained recovery; no claim of independent observation of historical pre-mutation state'})
(OUT/'raw/probe_results.json').write_text(json.dumps(records,indent=2,allow_nan=False)+'\n')
print(json.dumps({'probes':len(records),'passed':sum(v['passed'] for v in records.values()),'findings':[k for k,v in records.items() if not v['passed']]},indent=2))
