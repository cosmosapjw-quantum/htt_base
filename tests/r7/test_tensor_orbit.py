import itertools
import numpy as np
import pytest
from scipy.spatial.transform import Rotation
from common.r7_contracts import TensorRecord
from obsstat.r7_tensor_orbit import (orbit_distance_bounds,orbit_pool_scores,rational_quaternion_cover,RotationCover)

def witness():
    q=np.diag([-1.,0.,1.]);o=np.zeros((3,3,3))
    for indices,value in zip(itertools.combinations_with_replacement(range(3),3),(1,0,0,-2,1,1,1,-1,-1,1)):
        for index in set(itertools.permutations(indices)): o[index]=value
    return q*1e-5,o*1e-5

def record(id,q,o):
    return TensorRecord(id,np.zeros(32),q,o,"FRAME","p","1","fit")

def test_rotation_equivalence_mirror_and_zero_strata():
    q,o=witness();r=Rotation.from_rotvec([.2,-.3,.4]).as_matrix()
    qr=r@q@r.T;orr=np.einsum('ia,jb,kc,abc->ijk',r,r,r,o)
    cover=rational_quaternion_cover(1)
    d=orbit_distance_bounds(q,o,qr,orr,1e-5,1e-5,cover)
    assert d.lower==0 and d.upper<1e-7
    mirror=orbit_distance_bounds(q,o,q,-o,1e-5,1e-5,cover)
    assert mirror.upper>1e-3
    # The coarse cover is not claimed to resolve chirality by a positive lower bound.
    zero=orbit_distance_bounds(np.zeros_like(q),np.zeros_like(o),np.zeros_like(q),np.zeros_like(o),1e-5,1e-5,cover)
    assert zero.lower==zero.upper==0
    repeated=orbit_distance_bounds(np.diag([1.,1.,-2.])*1e-5,np.zeros_like(o),np.zeros_like(q),np.zeros_like(o),1e-5,1e-5,cover)
    assert repeated.lower<=np.sqrt(6)<=repeated.upper

def test_pool_keeps_ties_permutation_and_unresolved_rows():
    q,o=witness();rows=[record(str(i),q,o) for i in range(3)]
    rows.append(record("d",-q,o))
    pool=orbit_pool_scores(rows,2,1e-5,1e-5,1e-8)
    shuffled=orbit_pool_scores(rows[::-1],2,1e-5,1e-5,1e-8)
    assert dict(zip(pool.sample_ids,pool.scores))==dict(zip(shuffled.sample_ids,shuffled.scores))
    assert len(pool.sample_ids)==4 and pool.scores[:3]==(0.,0.,0.)
    assert pool.row_status[3]=="NUMERICALLY_UNRESOLVED"

def test_reflections_rejected():
    q,o=witness()
    cover=RotationCover(np.array([-np.eye(3)]),None,"mirror",None,None)
    with pytest.raises(ValueError,match="proper"):
        orbit_distance_bounds(q,o,-q,o,1e-5,1e-5,cover)
