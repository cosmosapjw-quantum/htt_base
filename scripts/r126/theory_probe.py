"""Independent finite algebra of the dissipative quadrupole and dipole blocks."""
import json
import numpy as np
def main():
    rt=np.sqrt(6)
    C=np.array([[-.9,-rt/20,-rt/20],[-rt/10,-.7,.3],[-rt/10,.3,-.7]])
    W=np.diag([1,.5,.5]);H=-(W@C+C.T@W)
    eig=np.linalg.eigvals(C);assert np.max(abs(eig.imag))<1e-14;eig=eig.real;assert np.max(abs(np.sort(eig)-[-1,-1,-.3]))<1e-14
    assert np.max(abs(W@C-C.T@W))<1e-14
    rng=np.random.default_rng(126);err=0.;minloss=1e100
    for _ in range(100):
        og,ob=rng.uniform(.01,1,2);z=rng.normal(size=2)+1j*rng.normal(size=2)
        D=np.array([[-1,1],[4*og/(3*ob),-4*og/(3*ob)]])
        w=np.diag([4*og/3,ob]);loss=-np.vdot(z,(w@D+D.T@w)@z).real
        target=8*og/3*abs(z[0]-z[1])**2
        err=max(err,abs(loss-target));minloss=min(minloss,loss)
    assert err<1e-13 and minloss>=0
    out={"quadrupole_eigenvalues":np.sort(eig).tolist(),"weighted_symmetry_residual":float(np.max(abs(W@C-C.T@W))),"dissipation_block_eigenvalues":np.linalg.eigvalsh(H).tolist(),"dipole_complex_samples":100,"dipole_max_abs_error":err,"dipole_min_loss":minloss,"scope":"independent finite algebra; no global solver claim","execution_note":"first JSON serialization failed for complex-typed real eigenvalues; explicit imaginary-part check then real cast"}
    print(json.dumps(out,indent=2,allow_nan=False))
if __name__=="__main__":main()
