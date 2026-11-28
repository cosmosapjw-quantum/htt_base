import numpy as np,json
from scipy.linalg import expm
def main():
    rng=np.random.default_rng(128);e=0.;rank=[]
    for _ in range(100):
        t=rng.uniform(.01,5,5);M=np.diag(t/t.sum());P=np.eye(5)-np.outer(np.ones(5),t)/t.sum()
        e=max(e,np.max(abs(t@P)),np.max(abs(P@P-P)),np.max(abs(M@P-P.T@M)))
        rank.append(int(np.linalg.matrix_rank(P)))
    # Two equal-duration blocks with same integrated opacity and different order.
    A=np.array([[0.,1.],[-.3,0.]]);C=np.diag([0.,-2.])
    y=np.array([1.,.3]);early=expm(A*.5)@expm((A+2*C)*.5)@y
    late=expm((A+2*C)*.5)@expm(A*.5)@y
    assert e<1e-13 and set(rank)=={4} and np.linalg.norm(early-late)>.01
    print(json.dumps({"samples":100,"max_projector_error":float(e),"ranks":sorted(set(rank)),"equal_depth_noncommuting_toy_gap":float(np.linalg.norm(early-late)),"commutator_norm":float(np.linalg.norm(A@C-C@A)),"scope":"synthetic algebra and constructive noncommutation example; not Bianchi result"},indent=2))
if __name__=="__main__":main()
