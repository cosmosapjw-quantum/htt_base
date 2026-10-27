"""Exact finite response rank check for LOOP C; Python stdlib only."""
from fractions import Fraction as Q
import json
from pathlib import Path


def dot(a, b): return sum(x*y for x, y in zip(a,b))
def cross(a,b): return [a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0]]
def rank(rows):
    a=[[Q(v) for v in r] for r in rows]; k=0
    for j in range(len(a[0])):
        pivot=next((i for i in range(k,len(a)) if a[i][j]),None)
        if pivot is None: continue
        a[k],a[pivot]=a[pivot],a[k]; p=a[k][j]; a[k]=[x/p for x in a[k]]
        for i in range(k+1,len(a)):
            p=a[i][j]; a[i]=[x-p*y for x,y in zip(a[i],a[k])]
        k+=1
        if k==len(a): break
    return k

axes=[[Q(i==j) for i in range(3)] for j in range(3)]
points=axes+[[Q(3,5),Q(4,5),Q(0)],[Q(3,5),Q(0),Q(4,5)],[Q(0),Q(3,5),Q(4,5)]]
points += [[-x for x in p] for p in points]
S=[[[1,0,0],[0,0,0],[0,0,-1]],[[0,0,0],[0,1,0],[0,0,-1]],[[0,1,0],[1,0,0],[0,0,0]],[[0,0,1],[0,0,0],[1,0,0]],[[0,0,0],[0,0,1],[0,1,0]]]
radial=[]; proper=[]; augmented=[]
for n in points:
    assert dot(n,n)==1
    sn=[[dot(row,n) for row in mat] for mat in S]
    r=[Q(1)]+[dot(n,v) for v in sn]+[-x for x in n]+[Q(0)]*3
    cs=[[v[i]-n[i]*dot(n,v) for i in range(3)] for v in sn]
    cb=[cross(n,e) for e in axes]
    m=[[Q(0)]+[v[i] for v in cs]+[Q(0)]*3+[v[i] for v in cb] for i in range(3)]
    radial.append(r); proper+=m; augmented.append(r+[Q(0)]*3)
    augmented += [row+row[9:12] for row in m]
results={'radial_rank':rank(radial),'proper_motion_rank':rank(proper),'joint_rank':rank(radial+proper),'joint_with_frame_spin_rank':rank(augmented),'joint_with_frame_spin_nullity':15-rank(augmented)}
assert results=={'radial_rank':9,'proper_motion_rank':8,'joint_rank':12,'joint_with_frame_spin_rank':12,'joint_with_frame_spin_nullity':3},results
receipt={'method':'Exact Fraction Gaussian elimination; 12 rational unit directions; 3 Cartesian proper-motion rows per source (one tangency dependence).','results':results,'directions':[[str(x) for x in p] for p in points],'scope':'Finite angular design example, not rank guarantee for an arbitrary catalogue.','earlier_optional_check':'System Python import of SymPy failed (ModuleNotFoundError); replaced by dependency-free exact rational calculation.'}
Path(__file__).with_name('loop_c_python_receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps(results))
