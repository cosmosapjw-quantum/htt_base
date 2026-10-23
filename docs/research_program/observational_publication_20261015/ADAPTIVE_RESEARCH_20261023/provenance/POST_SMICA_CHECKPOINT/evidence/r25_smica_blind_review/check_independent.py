"""Independent candidate audit: no candidate module imports or execution."""
import hashlib, json, math, os, pathlib, resource, tarfile, time
from datetime import datetime, timezone
from decimal import Decimal, localcontext
from fractions import Fraction as F
from itertools import combinations, permutations
start=time.perf_counter(); started=datetime.now(timezone.utc).isoformat()
import numpy as np
root=pathlib.Path('/home/cosmosapjw/Dropbox/bianchi/htt_base')
base=root/'docs/research_program/observational_publication_20261015/ADAPTIVE_RESEARCH_20261023'
c=base/'smica_spectral_nullspace'
sha=lambda p: hashlib.file_digest(open(p,'rb'),'sha256').hexdigest()
input_path=base/'R25-SMICA-SPECTRAL-NULLSPACE_INPUT.json'
assert sha(input_path)=='69ad48a48c5f61a5314050a45077bde99af83e97ffe9b8ed270533ee9368710a'
assert sha(c/'MANIFEST.json')=='4faba983677d56b5d12705a77c0fea498bd3b3263000653ee8151462e3d064d0'
contract=json.loads(input_path.read_text()); manifest=json.loads((c/'MANIFEST.json').read_text())
for n,v in manifest['files'].items():
 assert sha(c/n)==v['sha256'] and (c/n).stat().st_size==v['size_bytes'], n
archive=pathlib.Path(contract['source']['archive'])
assert archive.stat().st_size==contract['source']['bytes'] and sha(archive)==contract['source']['sha256']
contents={}
with tarfile.open(archive,'r:gz') as t:
 for m in t:
  name=pathlib.PurePosixPath(m.name).name
  if name in contract['source']['members']:
   assert name not in contents and m.isfile()
   contents[name]=t.extractfile(m).read()
for name,h in contract['source']['members'].items(): assert hashlib.sha256(contents[name]).hexdigest()==h
# Independent source addressing uses the serialized flat source tokens.
tokens=contents['weights_EB_smica_R3.00.txt'].decode('ascii').split()
assert len(tokens)==2*7*4001
result=json.loads((c/'RESULT.json').read_text())
channels=[30,44,70,100,143,217,353]
assert result['channels_GHz']==channels
source_rows={}
for pol,p in [('E',0),('B',1)]:
 for ell in (2,3): source_rows[f'{pol}{ell}']=[tokens[(p*7+j)*4001+ell] for j in range(7)]
assert list(result['operators'])==['E2','E3','B2','B3']
expected_targets={f'unit_{freq}':[F(int(i==j)) for i in range(7)] for j,freq in enumerate(channels)}
for j,k in combinations(range(7),2): expected_targets[f'contrast_{channels[j]}_{channels[k]}']=[F(int(i==j)-int(i==k)) for i in range(7)]
max_error=0.; max_float_annihilation=0.; decimal_summary={}; extrema={}; all_targets=0
M_exact=[[F(0) for _ in range(168)] for _ in range(24)]
input_offset=output_offset=0; kernel_columns=[]; exact_rank_minor=[]
all_permutations=list(permutations(range(7)))
for key,decimals in source_rows.items():
 row=result['operators'][key]; w=list(map(F,decimals)); w64=np.array(list(map(float,w)))
 assert row['source_decimal_weights']==decimals and row['weights']==w64.tolist()
 d=sum(x*x for x in w); assert d>0 and row['row_rank']==1 and row['kernel_dimension']==6
 assert row['target_count']==28 and [t['target'] for t in row['targets']]==list(expected_targets)
 Q,_=np.linalg.qr(w64[:,None],mode='complete'); N=Q[:,1:]; P=N@N.T
 assert np.linalg.norm(P@P-P)<1e-14 and np.linalg.norm(P-P.T)<1e-14 and abs(np.trace(P)-6)<1e-14
 assert np.linalg.norm(w64@N)<1e-14
 for target in row['targets']:
  a=expected_targets[target['target']]; assert target['target_vector']==list(map(float,a))
  aa=sum(x*x for x in a); aw=sum(x*y for x,y in zip(a,w))
  # Lagrange's identity gives the loss from 21 pairwise minors, independently of the projector formula.
  lost2=sum((w[i]*a[j]-w[j]*a[i])**2 for i,j in combinations(range(7),2))/d
  retained2=aw*aw/d
  assert lost2>0 and lost2+retained2==aa
  expected={'lost_norm':math.sqrt(float(lost2)), 'retained_projection_norm':math.sqrt(float(retained2)),
            'lost_fraction':math.sqrt(float(lost2/aa)), 'retained_fraction':math.sqrt(float(retained2/aa)),
            'lost_squared_fraction':float(lost2/aa), 'retained_squared_fraction':float(retained2/aa),
            'projection_coefficient':float(aw/d), 'least_squares_residual':math.sqrt(float(lost2))}
  for name,value in expected.items():
   err=abs(value-target[name]); max_error=max(max_error,err); assert err<1e-14,(key,target['target'],name,err)
  a64=np.array(list(map(float,a))); h64=np.array(target['witness_s1'])
  assert target['witness_s0']==[0]*7
  assert np.max(np.abs(h64-N@(N.T@a64)))<1e-14
  assert np.linalg.norm(a64-w64*np.linalg.lstsq(w64[:,None],a64,rcond=None)[0][0])-math.sqrt(float(lost2))<1e-14
  annih=abs(float(w64@h64)); max_float_annihilation=max(max_float_annihilation,annih)
  assert annih<1e-14 and abs(float(a64@h64)-float(lost2))<1e-14
  assert abs(target['witness_compressed_difference']-float(w64@h64))<1e-14
  assert abs(target['witness_target_difference']-float(lost2))<1e-14
  all_targets+=1
 exact=row['exact_witness']; h=list(map(F,exact['s1_h_exact'])); a=expected_targets[exact['target']]
 assert exact['source_decimal_weights']==decimals and exact['s0']==['0']*7
 assert sum(x*y for x,y in zip(w,h))==0
 ah=sum(x*y for x,y in zip(a,h)); hh=sum(x*x for x in h); assert ah==hh and hh>0
 assert F(exact['w_dot_h_exact'])==0 and F(exact['a_dot_h_exact'])==ah and F(exact['h_dot_h_exact'])==hh
 assert F(exact['a_dot_h_minus_h_dot_h_exact'])==0
 coeff=F(exact['projection_coefficient_exact']); assert all(a[i]-h[i]==coeff*w[i] for i in range(7))
 with localcontext() as ctx:
  ctx.prec=80
  wd=list(map(Decimal,decimals)); hd=[Decimal(x.numerator)/Decimal(x.denominator) for x in h]
  rd=sum((x*y for x,y in zip(wd,hd)),Decimal(0))
  ad=[Decimal(x.numerator)/Decimal(x.denominator) for x in a]
  sd=sum((x*y for x,y in zip(ad,hd)),Decimal(0))-sum((x*x for x in hd),Decimal(0))
  assert abs(rd)<Decimal('1e-75') and abs(sd)<Decimal('1e-75')
  assert rd==Decimal(exact['decimal_w_dot_h_residual']) and sd==Decimal(exact['decimal_a_dot_h_minus_h_dot_h_residual']) and exact['decimal_precision']==80
 decimal_summary[key]={'w_dot_h':str(rd),'a_dot_h_minus_h_dot_h':str(sd),'a_dot_h_positive':True}
 # Check all 5040 permutations for a nonzero exact witness; projection norms follow by orthogonal relabeling.
 for perm in all_permutations:
  wp=[w[i] for i in perm]; hp=[h[i] for i in perm]; ap=[a[i] for i in perm]
  assert sum(x*y for x,y in zip(wp,hp))==0
  assert sum(x*y for x,y in zip(ap,hp))==hh
  assert sum(x*x for x in hp)==hh
 # Build the tensor from independent offsets; 24 disjoint nonzero row supports prove row rank 24.
 n=2*int(key[1])+1; pivot=max(range(7),key=lambda i:abs(w[i]))
 block=result['tensor']['blocks'][list(source_rows).index(key)]
 assert block['input_start']==input_offset and block['output_start']==output_offset and block['key']==key
 assert block['input_shape']==[7,n] and block['output_shape']==[n] and block['pivot_frequency_index']==pivot
 assert block['harmonic_coordinates']==[f'm={m}' for m in range(-int(key[1]),int(key[1])+1)]
 for m in range(n):
  for j in range(7): M_exact[output_offset+m][input_offset+j*n+m]=w[j]
  exact_rank_minor.append((output_offset+m,input_offset+pivot*n+m,w[pivot]))
  for j in range(7):
   if j==pivot: continue
   v={input_offset+j*n+m:F(1),input_offset+pivot*n+m:-w[j]/w[pivot]}
   assert all(sum((rr[i]*val for i,val in v.items()),F(0))==0 for rr in M_exact[:output_offset+n])
   kernel_columns.append(v)
 input_offset+=7*n; output_offset+=n
 pair_targets=[t for t in row['targets'] if t['target'].startswith('contrast_')]
 extrema[key]={'minimum':min((t['lost_fraction'],t['target']) for t in pair_targets),'maximum':max((t['lost_fraction'],t['target']) for t in pair_targets)}
assert input_offset==168 and output_offset==24 and len(kernel_columns)==144
assert len(exact_rank_minor)==24 and all(x[2]!=0 for x in exact_rank_minor)
assert all(M_exact[i][j]==(w if i==ii else 0) for ii,j,w in exact_rank_minor for i in range(24))
for v in kernel_columns: assert all(sum((rr[i]*val for i,val in v.items()),F(0))==0 for rr in M_exact)
# Each basis vector has its own nonpivot coordinate equal to 1, so all 144 are independent.
nonpivots=[next(i for i,v in col.items() if v==1) for col in kernel_columns]
assert len(set(nonpivots))==144
expected_sparse={(i,j):float(v) for i,row in enumerate(M_exact) for j,v in enumerate(row) if v}
stored_sparse={(v['output'],v['input']):v['weight'] for v in result['tensor']['nonzero_entries']}
assert len(result['tensor']['nonzero_entries'])==len(stored_sparse)==168 and stored_sparse==expected_sparse
assert result['tensor']['rank']==24 and result['tensor']['nullity']==144 and result['tensor']['input_dimension']==168 and result['tensor']['output_dimension']==24
M=np.array([[float(v) for v in rr] for rr in M_exact]); singular_values=np.linalg.svd(M,compute_uv=False)
assert len(singular_values)==24 and min(singular_values)>0.5
# Identified nontrivial case L=K M with distinct field/harmonic coefficients.
K=np.arange(1.,25.)[None,:]; L=K@M
for v in kernel_columns:
 x=np.zeros(168)
 for i,q in v.items(): x[i]=float(q)
 assert abs(float((L@x)[0]))<1e-13
# Rank-zero fixture is well-defined: M=0 identifies only L=0, with every nonzero target lost.
assert all(sum(x*x for x in a)>0 for a in expected_targets.values())
raw=json.loads((c/'RAW_RECEIPT.json').read_text())
for v in raw['raw_files'].values():
 p=pathlib.Path(v['path']); assert sha(p)==v['sha256'] and p.stat().st_size==v['size_bytes']
assert sha(c/'MANIFEST.json')=='4faba983677d56b5d12705a77c0fea498bd3b3263000653ee8151462e3d064d0'
summary={'check':'independent_no_candidate_import','started_utc':started,'ended_utc':datetime.now(timezone.utc).isoformat(),
 'wall_seconds':time.perf_counter()-start,'peak_rss_kib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
 'candidate_identity':'sha256:'+sha(c/'MANIFEST.json'),'source_hashes_verified':True,'candidate_file_hashes_verified':True,
 'raw_evidence_hashes_verified':True,'targets_verified':all_targets,'exact_witnesses_verified':4,
 'independent_loss_method':'exact pairwise minors via Lagrange identity; QR kernel projection crosscheck',
 'max_scalar_comparison_error':max_error,'max_float_annihilation':max_float_annihilation,
 'precision80_checks':decimal_summary,'permutations_checked_per_operator':len(all_permutations),
 'tensor_shape':[24,168],'exact_rank':24,'exact_nullity':144,'independent_basis_vectors':144,
 'rank_proof':'24 pivot columns form a nonsingular diagonal minor; 144 basis vectors have distinct free coordinates',
 'singular_value_range':[float(min(singular_values)),float(max(singular_values))],
 'identified_fixture':'L=K M for nonconstant K; all 144 kernel columns annihilated',
 'rank_zero_fixture':'zero row loses every nonzero target; no division', 'pair_extrema':extrema,'exit_code':0}
print(json.dumps(summary,indent=2))
