"""P1 matrix-valued STF5 response identification and rotation-type null modes.
Geometry from CF4 table4 direction rows, input optical transfer G assumed toy.
No physical GR source qualification.
"""
import json
import numpy as np
from scipy.spatial.transform import Rotation
from verify_physics import read_cf4, gal_to_icrs, E

def stf_rotation(R):
    return np.einsum("aij,bji->ab",E,np.einsum("ik,bkl,jl->bij",R,E,R))

def A(a,low,high):
    n=gal_to_icrs(a[(a[:,1]>=low)&(a[:,1]<high),2:])
    B=np.einsum("ni,aij,nj->na",n,E,n)
    return B.T@B

def f_eff(A1,A2,G1,G2):
    L=np.linalg.inv(np.linalg.inv(A1)+np.linalg.inv(A2))
    D=G2-G1
    return D.T@L@D

def ranked(F,base_scale):
    eigen=np.linalg.eigvalsh(F)
    # Judge null directions against the unprofiled source-geometry scale.
    # A rank test relative only to max(F) would misclassify an all-zero Fisher.
    return {"eig":eigen.tolist(),"rank":int(np.sum(eigen>1e-10*base_scale))}

def main():
    a=read_cf4();A1=A(a,40,80);A2=A(a,80,140)
    base_scale=float(np.max(np.linalg.eigvalsh(A1+A2)))
    I=np.eye(5);R0=np.eye(3)
    rank_table=[]
    for angle in [0.,0.37,np.pi]:
        R=Rotation.from_rotvec([0.,0.,angle]).as_matrix()
        D=stf_rotation(R)
        np.testing.assert_allclose(D.T@D,I,atol=5e-15)
        v=ranked(f_eff(A1,A2,I,D),base_scale)
        rank_table.append({"axis_z_rotation_radians":angle,"effective_rank":v["rank"],
                           "fisher_eigenvalues":v["eig"]})
    assert [e["effective_rank"] for e in rank_table]==[0,4,2]
    nontrivial=stf_rotation(Rotation.from_rotvec([0.,0.,.37]).as_matrix())
    a1=ranked(f_eff(A1,A2,I,1.1*nontrivial),base_scale)
    assert a1["rank"]==5
    # Matrix identity: Schur complement for B1(b+G1s), B2(b+G2s).
    G1=stf_rotation(Rotation.from_rotvec([.2,-.1,.3]).as_matrix())
    G2=0.8*stf_rotation(Rotation.from_rotvec([-.3,.1,.4]).as_matrix())
    cross=A1@G1+A2@G2
    full=G1.T@A1@G1+G2.T@A2@G2
    profiled=full-cross.T@np.linalg.solve(A1+A2,cross)
    formula=f_eff(A1,A2,G1,G2)
    np.testing.assert_allclose(profiled,formula,rtol=5e-12,atol=7e-10)
    return {"schema":"htt.r69.p1_matrix_transfer_identifiability/1",
            "source":"CF4 table4 40-80 and 80-140 Mpc sky positions, unit weight",
            "theorem":"profiled Fisher=(G2-G1)^T(A1^-1+A2^-1)^-1(G2-G1)",
            "two_depth_G_case_rotation_only":rank_table,
            "two_depth_G_case_rotation_with_10pct_amplitude_change":a1,
            "general_matrix_schur_residual_Frob":float(np.linalg.norm(profiled-formula)),
            "qualification":"R matrices only illustrative source-response operators; pure tetrad coordinate rotation is gauge, not a physical signal; no actual shear posterior"}
if __name__=="__main__":
    print(json.dumps(main(),indent=2))
