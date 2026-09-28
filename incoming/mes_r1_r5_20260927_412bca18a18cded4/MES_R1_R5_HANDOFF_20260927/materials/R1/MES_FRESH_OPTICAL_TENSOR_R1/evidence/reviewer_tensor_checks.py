"""Independent exact polynomial check of raw generator and integrated shear block."""
from fractions import Fraction as F
from pathlib import Path
import json, math
Z=(0,0,0)
def constant(c): return {Z:F(c)} if c else {}
def add(*ps):
 out={}
 for p in ps:
  for k,v in p.items(): out[k]=out.get(k,F(0))+v
 return {k:v for k,v in out.items() if v}
def scale(p,c): return {k:v*c for k,v in p.items() if v*c}
def mul(a,b):
 out={}
 for k,v in a.items():
  for l,w in b.items():
   m=tuple(k[i]+l[i] for i in range(3));out[m]=out.get(m,F(0))+v*w
 return {k:v for k,v in out.items() if v}
def derivative(p,i):
 out={}
 for k,v in p.items():
  if k[i]:
   key=list(k);key[i]-=1;out[tuple(key)]=v*k[i]
 return out
def dfact(n): return math.prod(range(n,0,-2))
def avg(p):
 ans=F(0)
 for k,v in p.items():
  if not any(j%2 for j in k):ans+=v*F(math.prod(dfact(j-1) for j in k),dfact(sum(k)+1))
 return ans
def dot(a,b):return add(*(mul(x,y) for x,y in zip(a,b)))
e=[{tuple(int(i==j) for i in range(3)):F(1)} for j in range(3)]
base=[[[1,0,0],[0,-1,0],[0,0,0]],[[1,0,0],[0,1,0],[0,0,-2]],[[0,1,0],[1,0,0],[0,0,0]],[[0,0,1],[0,0,0],[1,0,0]],[[0,0,0],[0,0,1],[0,1,0]]]
norms=[2,6,2,2,2]
def se(S):return [add(*(scale(e[j],S[i][j]) for j in range(3))) for i in range(3)]
def sp(S):return dot(e,se(S))
def generator(B,S):
 S_e=se(S);s=sp(S);w=[add(S_e[i],scale(mul(s,e[i]),-1)) for i in range(3)]
 return add(scale(dot(w,[derivative(B,i) for i in range(3)]),-1),scale(mul(s,B),4))
def direct_entry(B,S,T):return avg(mul(sp(T),generator(B,S)))
def bilinear_entry(B,S,T):return avg(mul(B,add(scale(dot(se(S),se(T)),2),scale(mul(sp(S),sp(T)),-1))))
x,y,z=e
z2=mul(z,z);z4=mul(z2,z2);z6=mul(z4,z2)
B=mul(add(constant(1),scale(z2,3)),add(constant(1),scale(z2,3)))
P6=scale(add(scale(z6,231),scale(z4,-315),scale(z2,105),constant(-5)),F(1,16))
B_more=add(B,scale(P6,F(1,10)),scale(x,F(1,10)))
residuals=[]
for b in [B,B_more]:
 residuals.append([[str(direct_entry(b,S,T)-bilinear_entry(b,S,T)) for T in base] for S in base])
mat=[[bilinear_entry(B,S,T) for T in base] for S in base]
diag=[mat[i][i]/norms[i] for i in range(5)]
m2=[[avg(mul(B,mul(e[i],e[j]))) for j in range(3)] for i in range(3)]
higher=[[str(bilinear_entry(B_more,S,T)-bilinear_entry(B,S,T)) for T in base] for S in base]
iso_diag=[bilinear_entry(constant(1),S,S)/norms[i] for i,S in enumerate(base)]
result={'method':'Independent raw angular derivative evaluated as exact sparse polynomials, then exact spherical monomial moments using Python Fraction. No numerical evolution or SymPy.', 'normalization':'sphere average; physical full-sky integral rescales all density/operators by 4pi', 'raw_generator_vs_IBP_residuals':residuals,'ell1_ell6_addition_operator_residuals':higher,'M2':[[str(v) for v in row] for row in m2],'orthonormal_L5_diagonal':[str(v) for v in diag],'isotropic_L5_diagonal':[str(v) for v in iso_diag],'coercivity_margin':str(min(diag)-min(m2[i][i] for i in range(3))),'off_diagonal_entries_zero':all(mat[i][j]==0 for i in range(5) for j in range(5) if i!=j),'all_checks_pass':all(v=='0' for b in residuals for row in b for v in row) and all(v=='0' for row in higher for v in row) and diag==[F(176,105),F(352,105),F(176,105),F(64,21),F(64,21)] and all(v==F(8,15) for v in iso_diag)}
Path(__file__).with_suffix('.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({k:v for k,v in result.items() if 'residuals' not in k},indent=2))
