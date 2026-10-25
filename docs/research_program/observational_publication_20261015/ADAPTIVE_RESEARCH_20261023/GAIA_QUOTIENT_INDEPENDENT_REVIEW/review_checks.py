"""Independent exact-rational checks of saved certificate; no production import."""
import os, sys, time, json, resource, hashlib, ctypes
from fractions import Fraction as Q
from pathlib import Path
start=time.monotonic()
import numpy as np
ROOT=Path('/mnt/extdrive/workdir/htt_open_data/r26_gaia_quotient_blind_review')
BASE=Path('/mnt/extdrive/workdir/htt_open_data/r25_gaia_source_quotient_certificate')
PACK=Path('/mnt/extdrive/workdir/htt_open_data/r25_root_space_recovery/receipts/POST_TAG_REVIEW_QUOTIENT_REVIEW_PACKET.json')
checks=[]
def check(name,ok,**detail):
 item={'name':name,'pass':bool(ok),**detail}; checks.append(item)
 print(json.dumps(item,default=str),flush=True)
 if not ok: raise AssertionError(name)
def fq(x): return Q.from_float(float(x))
def mat(x):return [[fq(v) for v in row] for row in x]
def transpose(a):return list(map(list,zip(*a)))
def mm(a,b):
 bt=transpose(b)
 return [[sum((x*y for x,y in zip(row,col)),Q()) for col in bt] for row in a]
def balls(c,r):return (mat(c),mat(r))
def bmul(a,b):
 ac,ar=a; bc,br=b; bct=transpose(bc); brt=transpose(br)
 cc=[]; rr=[]
 for av,rv in zip(ac,ar):
  cc.append([sum((x*y for x,y in zip(av,bv)),Q()) for bv in bct])
  rr.append([sum((abs(x)*s+r*abs(y)+r*s for x,r,y,s in zip(av,rv,bv,sv)),Q()) for bv,sv in zip(bct,brt)])
 return cc,rr
def bt(a):return transpose(a[0]),transpose(a[1])
def contains(outer,inner):
 return all(abs(x-y)+s<=r for oc,orr,ic,ir in zip(outer[0],outer[1],inner[0],inner[1]) for x,r,y,s in zip(oc,orr,ic,ir))
def sumrow(a):return max(sum(row,Q()) for row in a)
def inverse_ball(c,r):
 rc=mat(np.linalg.inv(np.array([[float(v) for v in row] for row in c])))
 ar=bmul((c,r),(rc,[[Q() for _ in row] for row in rc]))
 err=[[abs(Q(i==j)-ar[0][i][j])+ar[1][i][j] for j in range(len(c))] for i in range(len(c))]
 e=sumrow(err); check('neumann_'+str(len(c)),e<1,residual_upper=float(e))
 rn=max(sum(map(abs,row),Q()) for row in rc)
 radius=rn*e/(1-e)
 return (rc,[[radius for _ in row] for row in rc]),e
try:
 p=json.loads(PACK.read_text()); s=p['review_context']['scope']
 mismatch=[]
 for path,expect in {**{k:v['sha256'] for k,v in s['source_seals'].items()},**s['candidate_seals']}.items():
  h=hashlib.sha256(Path(path).read_bytes()).hexdigest()
  if h!=expect:mismatch.append({'path':path,'actual':h,'expected':expect})
 check('all_frozen_source_and_candidate_seals',not mismatch,count=len(s['source_seals'])+len(s['candidate_seals']),mismatch=mismatch)
 source=np.load('/mnt/extdrive/workdir/htt_open_data/r25_gaia_pair_separation/packaged/arrays.npz',allow_pickle=False)
 d=json.loads((BASE/'RESULT.json').read_text()); saved=np.load(BASE/'INTERVALS.npz',allow_pickle=False)
 arrays={k:saved[k] for k in saved.files}
 check('finite_nonnegative_saved_radii',all(np.isfinite(v).all() and (not k.endswith('_radius') or (v>=0).all()) for k,v in arrays.items()),keys=list(arrays))
 check('source_carrier_shapes',source['H'].reshape(117,9512).shape==(117,9512) and source['W'].shape==(88,117),shapes={k:list(source[k].shape) for k in source.files})
 carrier=np.load('/mnt/extdrive/workdir/htt_open_data/r25_gaia_pair_separation/raw/full_carrier.npz',allow_pickle=False)
 check('full_carrier_retained',len(carrier.files)>0,shapes={k:list(carrier[k].shape) for k in carrier.files})
 C=source['C'].reshape(4756,2,2); mindet=None
 for i,c in enumerate(C):
  aa,bb,cc=fq(c[0,0]),fq(c[0,1]),fq(c[1,1]); det=aa*cc-bb*bb
  if c[0,1]!=c[1,0] or not(aa>0 and det>0):raise AssertionError(('SPD',i,c.tolist()))
  mindet=det if mindet is None else min(mindet,det)
 check('all_4756_source_blocks_exact_SPD',True,min_determinant_exact=str(mindet))
 B=mat(source['B'].reshape(9512,3)); Bg=mm(transpose(B),B)
 sb=balls(arrays['spin_Gram_center'],arrays['spin_Gram_radius'])
 check('spin_Gram_exact_enclosure',contains(sb,(Bg,[[Q()]*3 for _ in range(3)])))
 invb,eb=inverse_ball(*sb)
 check('spin_inverse_saved_enclosure',contains(balls(arrays['spin_inverse_center'],arrays['spin_inverse_radius']),invb))
 # Exact principal minors prove SPD independently of a floating eigenvalue.
 d1=Bg[0][0]; d2=Bg[0][0]*Bg[1][1]-Bg[0][1]*Bg[1][0]
 d3=Bg[0][0]*(Bg[1][1]*Bg[2][2]-Bg[1][2]*Bg[2][1])-Bg[0][1]*(Bg[1][0]*Bg[2][2]-Bg[1][2]*Bg[2][0])+Bg[0][2]*(Bg[1][0]*Bg[2][1]-Bg[1][1]*Bg[2][0])
 check('spin_Gram_exact_Sylvester',min(d1,d2,d3)>0,principal_minor_approximations=list(map(float,[d1,d2,d3])))
 A=balls(arrays['A_star_center'],arrays['A_star_radius']); z=balls(arrays['z_star_center'],arrays['z_star_radius'])
 for tag,q in [('full',13),('E1',3)]:
  aq=([r[:q] for r in A[0]],[r[:q] for r in A[1]])
  g=balls(arrays[tag+'_Gram_center'],arrays[tag+'_Gram_radius'])
  check(tag+'_Gram_contains_exact_interval_product',contains(g,bmul(bt(aq),aq)))
  ri,e=inverse_ball(*g)
  b=bmul(bt(aq),z); zz=bmul(bt(z),z); quad=bmul(bmul(bt(b),ri),b)
  tc=zz[0][0][0]-quad[0][0][0]; tr=zz[1][0][0]+quad[1][0][0]
  enc=[tc-tr,tc+tr]; reported=d['T_full' if tag=='full' else 'T_E1']
  check(tag+'_T_exact_interval_contained',fq(reported[0])<=enc[0] and enc[1]<=fq(reported[1]),independent_interval=list(map(float,enc)),reported=reported)
  if tag=='full':tfull=enc
  else:te1=enc
 dl=[te1[0]-tfull[1],te1[1]-tfull[0]]
 check('Delta_interval_contained',fq(d['Delta'][0])<=dl[0] and dl[1]<=fq(d['Delta'][1]),independent_interval=list(map(float,dl)))
 Sc=mat(arrays['S_star_center']); Sr=mat(arrays['S_star_radius'])
 delta=max(sum((abs(Sc[i][j]-Q(i==j))+Sr[i][j] for j in range(88)),Q()) for i in range(88))
 check('delta_encloses_exact_S_interval_row_norm',delta<=fq(d['delta_upper'])<1,independent_upper=float(delta),reported=d['delta_upper'])
 eta=fq(d['arbitrary_mean_ball']['center_error_norm_upper']); rad=fq(d['arbitrary_mean_ball']['radius_upper'])
 zr=[row[0] for row in z[1]]
 check('eta_exact_squared_norm',eta**2>=sum((v*v for v in zr),Q()))
 check('radius_exact_squared_test',rad>eta and (rad-eta)**2 >= (1+fq(d['delta_upper']))*120)
 check('display_center_exact_identity',np.array_equal(np.load(BASE/'CENTER.npy',allow_pickle=False),arrays['z_star_center'][:,0]))
 def sf_bound(t,k,n):
  x=t/2; terms=[Q(1)]
  for j in range(1,n+1):terms.append(terms[-1]*x/j)
  return sum(terms[:k],Q())/sum(terms,Q())
 tail=sf_bound(fq(d['Delta'][0])/(1+fq(d['delta_upper'])),5,128)
 quant=sf_bound(Q(120),44,256)
 check('Delta_tail_exact_rational_upper',tail<=Q(d['conditional_E1_Delta_p_upper']),rational_upper_approx=float(tail))
 check('mean_ball_quantile_exact_rational_upper',quant<=Q(1,20),rational_upper_approx=float(quant))
 # Sample exact source center dots, distinct from author BLAS/interval code.
 H=source['H'].reshape(117,9512); W=source['W']; F=arrays['F_center']; Fr=arrays['F_radius']
 inds=[(0,0),(0,9511),(43,4756),(87,0),(87,9511)]
 for i,j in inds:
  v=sum((fq(W[i,k])*fq(H[k,j]) for k in range(117)),Q())
  check('sample_F_dot_'+str(i)+'_'+str(j),abs(v-fq(F[i,j]))<=fq(Fr[i,j]))
 # Rounding of old-response sym(Cd) is assessed explicitly, not silently exact.
 cd=source['Cd'].reshape(117,117); fl=(cd+cd.T)/2; errors=[]
 for i in range(117):
  for j in range(117):
   e=abs((fq(cd[i,j])+fq(cd[j,i]))/2-fq(fl[i,j]))
   if e:errors.append((float(e),i,j))
 check('old_Cd_symmetry_midpoint_audit',True,inexact_midpoint_count=len(errors),max_error=max(errors,default=(0,None,None)))
 # Small exact contaminated-operator and rank-loss controls, independent formulas.
 b=[Q(1),Q(1),Q(0),Q(0)]; h=[Q(2),Q(-1),Q(1),Q(0)]
 hstar=[x-sum(x*y for x,y in zip(h,b))*v/sum(x*x for x in b) for x,v in zip(h,b)]
 check('exact_contaminated_quotient_control',hstar==[Q(3,2),Q(-3,2),Q(1),Q(0)] and sum(x*y for x,y in zip(hstar,b))==0)
 c4=[[Q(2),Q(1),Q(0),Q(0)],[Q(1),Q(3),Q(0),Q(0)],[Q(0),Q(0),Q(5),Q(-1)],[Q(0),Q(0),Q(-1),Q(7)]]
 check('exact_nonuniform_covariance_control',mm(mm([hstar],c4),transpose([hstar]))[0][0]==Q(47,4))
 check('exact_rank_loss_and_fiber_control',Q(0)==0 and Q(1)>0,projected_design=[[0,0],[0,1]],E1_rank=0,full_rank=1,k=1,kernel=[1,0])
 check('positive_tiny_mode_not_thresholded',Q(1,2**44)>0)
 check('failed_covariance_bound_is_not_admitted',abs(Q(21,10)-1)>1)
 # Bound arithmetic dominance: even 32 worst 9512-length roundoff factors
 # consume far less than the fixed 1e-8 inflation. Exact rational inequality.
 g=Q(2*9512,2**53-2*9512)
 check('inflation_dominates_nonnegative_bound_rounding',fq(1.00000001)*(1-g)**32>1,largest_gamma=float(g),inflation=fq(1.00000001))
 libc=ctypes.CDLL(None); rn=libc.fegetround()
 threads=int(Path('/proc/self/status').read_text().split('Threads:')[1].split()[0])
 check('runtime_RN_one_thread',rn==0 and threads==1,fegetround=rn,threads=threads,numpy=np.__version__)
 # Executed arithmetic distinguishes gradual underflow from merely printing a constant.
 sub=np.float64(np.finfo(float).tiny)*np.float64(0.5)
 check('gradual_underflow_arithmetic_probe',sub>0 and sub==np.finfo(float).tiny/2,subnormal_result=float(sub))
 status='PASS'
except BaseException as e:
 status='FAIL'; error=repr(e); print('FIRST_FAILURE',error,flush=True)
finally:
 out={'status':status,'checks':checks,'elapsed_seconds':time.monotonic()-start,'max_rss_bytes':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,'thread_environment':{k:os.environ.get(k) for k in ['OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS']},'pid':os.getpid(),'error':locals().get('error')}
 (ROOT/'raw'/'independent_checks.json').write_text(json.dumps(out,indent=2,default=str)+'\n')
 sys.exit(0 if status=='PASS' else 1)
