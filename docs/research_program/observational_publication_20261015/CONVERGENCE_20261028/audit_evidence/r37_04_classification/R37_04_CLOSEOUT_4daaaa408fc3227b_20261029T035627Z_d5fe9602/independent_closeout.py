"""Independent targeted review. Candidate reads only; no producer main or old imports."""
import csv, hashlib, importlib.util, itertools, json, math, os, subprocess, sys
from pathlib import Path
import numpy as np
from scipy.spatial.transform import Rotation
from matplotlib.figure import Figure

OUT=Path(__file__).resolve().parent
REPO=Path('/home/cosmosapjw/Dropbox/bianchi/htt_base')
PACKET=Path('/mnt/extdrive/workdir/htt_open_data/r36_controller/R37_NEXT_022_20261029.json')
P=REPO/'docs/research_program/observational_publication_20261015/CONVERGENCE_20261028/products/R37-04-CLASSIFICATION'
OLD=Path('/mnt/extdrive/workdir/htt_open_data/r36_controller/R37_04_PRE_REPAIR_1b528451805cca51_20261029T033725Z_be1f3e0b')
AGENT='/root/rc_4daaaa408fc3227b'
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def check_eq(actual, expected): assert actual==expected,(actual,expected)
def close(actual,expected,tol=2e-13): assert abs(float(actual)-float(expected)) <= tol,(actual,expected)
packet=json.loads(PACKET.read_text())
assignment=json.loads(packet['spawn_args']['message'].split('Assignment:\n',1)[1])
assert AGENT not in assignment['authors']+assignment['contributors']
manifest=json.loads((P/'ARTIFACT_MANIFEST.json').read_text())
check_eq('sha256:'+sha(P/'ARTIFACT_MANIFEST.json'),packet['candidate_identity'])
check_eq(manifest['input_identity'],packet['input_identity'])
checks={}
checks['artifact_hashes']={name:sha(P/name) for name in manifest['artifacts']}
for name,v in manifest['artifacts'].items():
    check_eq(sha(P/name),v['sha256']); check_eq((P/name).stat().st_size,v['bytes'])
checks['frozen_inputs']={}
for source in assignment['spec']['input_sources']:
    name=source['path']; actual=sha(REPO/name)
    check_eq(actual,source['sha256']);check_eq(actual,manifest['source_sha256'][name])
    checks['frozen_inputs'][name]=actual
checks['historical_receipts']={}
for h in assignment['history_refs']:
    path=h['receipt']['path'];actual=sha(path)
    check_eq(actual,h['receipt']['sha256'])
    checks['historical_receipts'][path]=actual
old_manifest=json.loads((OLD/'ARTIFACT_MANIFEST.json').read_text())
check_eq('sha256:'+sha(OLD/'ARTIFACT_MANIFEST.json'),manifest['predecessor_candidate_identity'])
for name,v in old_manifest['artifacts'].items():
    check_eq(sha(OLD/name),v['sha256']);check_eq((OLD/name).stat().st_size,v['bytes'])
producer='RAW_RECEIPT_05d056d4e58335c3_20261029T030652434145Z.json'
check_eq(sha(P/producer),'74fc4e1dbf8b8b1cedcea64c3d9664655033045d1ba0819ec6bcd61da5841c6c')
check_eq(sha(P/producer),sha(OLD/producer))
checks['original_producer_receipt_sha256']=sha(P/producer)
check_eq(sha(P/'FAMILY_SEPARATION.csv'),sha(OLD/'FAMILY_SEPARATION.csv'))
checks['changed_artifacts']=[k for k in manifest['artifacts'] if sha(P/k)!=sha(OLD/k)]
check_eq(set(checks['changed_artifacts']),set(['classification.py','test_classification.py','FAMILY_COMPATIBILITY_RESULT.json','adequacy_residual.pdf','REPORT_DELTA.md']))
result=json.loads((P/'FAMILY_COMPATIBILITY_RESULT.json').read_text())
old_result=json.loads((OLD/'FAMILY_COMPATIBILITY_RESULT.json').read_text())
checks['changed_result_fields']=[k for k in result if result[k]!=old_result[k]]
check_eq(set(checks['changed_result_fields']),{'script_sha256','flrw_origin'})
check_eq(result['script_sha256'],sha(P/'classification.py'))
for path,h in result['input_sha256'].items():check_eq(sha(REPO/path),h)
check_eq(result['carrier'],old_result['carrier'])
check_eq(result['common_event'],old_result['common_event'])
sourcepath=next(REPO/s['path'] for s in assignment['spec']['input_sources'] if s['path'].endswith('/TABLE.json'))
source=json.loads(sourcepath.read_text())
status=json.loads(sourcepath.with_name('PUBLICATION_STATUS.json').read_text())
check_eq(status['status'],result['source_publication_status'])
checks['source_publication_status_sha256']=sha(sourcepath.with_name('PUBLICATION_STATUS.json'))
check_eq(checks['source_publication_status_sha256'],'a7b15db7743b3d745bf6b065b0a5622b9fe72f348949febfcbd3f2e3e4a6e592')
spec=importlib.util.spec_from_file_location('review_current_candidate',P/'classification.py')
c=importlib.util.module_from_spec(spec);spec.loader.exec_module(c)
ii=np.array(source['controls']['II']['ricci'])
vii=np.array(source['controls']['VII0matched']['ricci'])
np.testing.assert_array_equal(ii,np.diag([.5,-.5,-.5]))
np.testing.assert_array_equal(vii,np.diag([-.5,1.5,-1.5]))
np.testing.assert_array_equal(source['controls']['I']['ricci'],source['controls']['flatVII0']['ricci'])
K=np.array(source['controls']['I']['extrinsic'])
Kstf=K-np.trace(K)*np.eye(3)/3
assert np.linalg.norm(Kstf)>0
checks['origin_control']={'spatial_ricci_zero':True,'extrinsic_STF_norm':float(np.linalg.norm(Kstf)),
'interpretation':'Spatial Ricci origin overlap only; nonzero extrinsic STF prevents inferring full FLRW.'}

# Independently normalized 7-to-6 quotient: STF coordinates plus trace-calibration.
def pack(A):
    return np.array([np.trace(A)/math.sqrt(3),(A[0,0]-A[1,1])/math.sqrt(2),
      (A[0,0]+A[1,1]-2*A[2,2])/math.sqrt(6),math.sqrt(2)*A[0,1],
      math.sqrt(2)*A[0,2],math.sqrt(2)*A[1,2],0.])
T=np.zeros((6,7));T[:5,1:6]=np.eye(5);T[5,0]=1/math.sqrt(2);T[5,6]=-1/math.sqrt(2)
n=np.array([1.,0,0,0,0,0,1.])
np.testing.assert_allclose(T@T.T,np.eye(6),atol=3e-16,rtol=0)
np.testing.assert_array_equal(T@n,np.zeros(6))
check_eq(np.linalg.matrix_rank(T),6)
r95=result['common_event']['noise_quantile']
# Exact chi-square(6) CDF, independent of scipy.stats quantile implementation.
cdf=1-math.exp(-r95*r95/2)*(1+r95*r95/2+r95**4/8)
close(cdf,.95,1e-15)
tau=r95*.12+.1
raw_threshold=math.sqrt(2)*tau
checks['common_event']={'profiled_dimension':6,'cdf_at_declared_quantile':cdf,
 'noise_quantile':r95,'tube':tau,'raw_shift_threshold':raw_threshold}

saved={}
original_savefig=Figure.savefig
def capture(fig,destination,*args,**kwargs):
    saved[Path(destination).name]=fig
    if Path(destination).name=='adequacy_residual.pdf':
        original_savefig(fig,OUT/'adequacy_plot_replay.pdf',*args,**kwargs)
Figure.savefig=capture
try:
    c.plot(np.array(result['amplitude_grid']),np.array(result['noise_grid']),
           np.array(result['joint_error_grid']),r95,[])
finally: Figure.savefig=original_savefig
check_eq(len(saved),4)
ax=saved['adequacy_residual.pdf'].axes[0]
curve=next(line for line in ax.lines if line.get_label()=='Profiled discarded-space residual')
x,y=map(np.asarray,curve.get_data())
np.testing.assert_allclose(y,np.abs(x)/math.sqrt(2),rtol=0,atol=1e-14)
marker=np.asarray(ax.collections[0].get_offsets())[0]
np.testing.assert_allclose(marker,[1,1/math.sqrt(2)],rtol=0,atol=1e-14)
horizontal=next(line for line in ax.lines if line.get_label().startswith('Joint tube'))
np.testing.assert_allclose(horizontal.get_ydata(),[tau,tau],rtol=0,atol=1e-14)
probes=[]
for shift in [-1.,-.6,0.,.6,raw_threshold-1e-8,raw_threshold+1e-8,1.]:
    datum=pack(ii);datum[0]+=shift
    independent_d_ii=float(np.linalg.norm(T@(datum-pack(ii))))
    independent_d_vii=math.hypot(math.sqrt(2),abs(shift)/math.sqrt(2))
    expected=([name for name,d in [('II',independent_d_ii),('VII0matched',independent_d_vii)] if d<=tau+1e-12])
    actual=c.exact_compatibility(datum,{'II':ii,'VII0matched':vii},tau)
    check_eq(actual,expected)
    probes.append({'shift':shift,'II_profile_distance':independent_d_ii,'compatible_set':actual})
check_eq(probes[3]['compatible_set'],['II'])
check_eq(probes[-1]['compatible_set'],[])
close(np.interp(.6,x,y),.6/math.sqrt(2),1e-14)
checks['actual_plot']={'curve_points':len(x),'x_axis_label':ax.get_xlabel(),
 'y_at_raw_shift_0p6':float(np.interp(.6,x,y)),'witness_marker':marker.tolist(),
 'threshold':tau,'raw_axis_threshold':raw_threshold,'candidate_pdf_writes':0,'probes':probes}

# All 135 rows: exact finite minimization over spectral permutations, no producer main.
perms=list(itertools.permutations(range(3)))
def projected_orbit_distance(A,B):
    ev=np.linalg.eigvalsh(B)
    return min(float(np.linalg.norm(T@(pack(A)-pack(np.diag(ev[list(p)]))))) for p in perms)
def labels(A,means,radii):
    return '|'.join(k for k,V in means.items() if projected_orbit_distance(A,V)<=radii[k]+1e-12)
rows=list(csv.DictReader((P/'FAMILY_SEPARATION.csv').open()))
check_eq(len(rows),135)
rad={k:source['images'][k]['ricci_F_bound'] for k in ['II','VII0matched']}
max_row_error=0.
for row in rows:
    a=float(row['amplitude']);sigma=float(row['noise_sigma']);eps=float(row['joint_response_error'])
    means={'II':a*a*ii,'VII0matched':a*a*vii};radius=r95*sigma+eps
    gap=math.sqrt(2)*a*a;sgap=(math.sqrt(14/3)-math.sqrt(2/3))*a*a
    expected={'joint_95_noise_radius':r95*sigma,'tube_radius':radius,
      'exact_orbit_center_separation':gap,'certified_exclusive_margin':gap-2*radius,
      'strong_quadratic_STF_norm_gap':sgap,'strong_quadratic_exclusive_margin':sgap-2*radius,
      'trace_difference':0.,'quadratic_STF_II':(2/3)*a**4,'quadratic_STF_VII0':(14/3)*a**4}
    for key,value in expected.items():
        error=abs(float(row[key])-value);max_row_error=max(max_row_error,error);assert error<2e-13,(key,error)
    mid=np.diag((np.linalg.eigvalsh(means['II'])+np.linalg.eigvalsh(means['VII0matched']))/2)
    for field,A in [('II_center_compatible',means['II']),('orbit_midpoint_compatible',mid),
                    ('source_frame_midpoint_compatible',(means['II']+means['VII0matched'])/2)]:
        check_eq(row[field],labels(A,means,dict.fromkeys(means,radius)))
    check_eq(row['R36_source_radii_applicable'],str(a==1.))
    if a==1:
        close(row['R36_source_bound_margin'],gap-sum(rad.values())-2*r95*sigma)
        check_eq(row['R36_source_II_center_compatible'],labels(means['II'],means,{k:r95*sigma+rad[k] for k in means}))
    else:
        check_eq(row['R36_source_bound_margin'],'');check_eq(row['R36_source_II_center_compatible'],'')
checks['numerical_rows']={'count':len(rows),'byte_identical_to_pre_repair':True,
 'sha256':sha(P/'FAMILY_SEPARATION.csv'),'maximum_numeric_error':max_row_error,'membership_discrepancies':0}

# Deterministic rotations and nuisance shifts: no Monte Carlo.
rotation_vectors=[(0,0,0),(.1,.2,.3),(.6,-.3,.2),(-.5,.8,.2),(1.,.2,-.6)]
rots=[Rotation.from_rotvec(v).as_matrix() for v in rotation_vectors]
max_lr=0.;num=0
for a in [0.,.5,1.]:
    for r in rots:
        for s in rots:
            m1=pack(a*a*(r@ii@r.T));m2=pack(a*a*(s@vii@s.T))
            yy=np.array([.2,-.1,.5,.4,-.7,.6,-.3])
            full=np.linalg.norm(T@(yy-m2))**2-np.linalg.norm(T@(yy-m1))**2
            carrier=np.linalg.norm(yy[1:6]-m2[1:6])**2-np.linalg.norm(yy[1:6]-m1[1:6])**2
            max_lr=max(max_lr,abs(full-carrier));num+=1
            np.testing.assert_allclose(T@(yy+3*n-m1),T@(yy-m1),rtol=0,atol=1e-15)
            raw=pack(a*a*(r@ii@r.T))+3*n
            check_eq(c.exact_compatibility(raw,{'II':a*a*ii,'VII0matched':a*a*vii},tau),
                     ['II','VII0matched'] if math.sqrt(2)*a*a<=tau+1e-12 else ['II'])
assert max_lr<1e-13
m1=pack(ii);m2=pack(.25*vii);yy=np.zeros(7)
varying_delta=(np.linalg.norm(T@(yy-m2))**2-np.linalg.norm(T@(yy-m1))**2
 -np.linalg.norm(yy[1:6]-m2[1:6])**2+np.linalg.norm(yy[1:6]-m1[1:6])**2)
assert abs(varying_delta)>1e-3
checks['carrier_adequacy']={'fixed_amplitude_comparisons':num,'max_LR_difference':max_lr,
 'varying_amplitude_5D_LR_failure':float(varying_delta),
 'interpretation':'5D STF preserves fixed-common-amplitude pairwise LR only; trace-calibration adequacy remains in all compatibility tubes.'}
report=(P/'REPORT_DELTA.md').read_text()
assert 'only a spatial-Ricci origin overlap' in report
assert 'If amplitude is jointly fitted rather than conditioned' in report
assert 'same dimensionless amplitude' in report
assert 'does not establish a full FLRW' in result['flrw_origin']
check_eq(result['original42'],'17/42 scientific; separate analytic 18/42; no promotion by this product')
# Final candidate hash is unchanged after all pure-function/plot-only checks.
check_eq('sha256:'+sha(P/'ARTIFACT_MANIFEST.json'),packet['candidate_identity'])
for name,value in manifest['artifacts'].items():check_eq(sha(P/name),value['sha256'])
print(json.dumps(checks,indent=2))

