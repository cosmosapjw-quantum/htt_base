"""Independent algebra: relative nodal response and exact scalar B derivative."""
import json,numpy as np
def main():
    rng=np.random.default_rng(127);err=0.;part=0.;fd=0.
    t,w=np.polynomial.legendre.leggauss(12);t=(t+1)/2;w=w/2
    for _ in range(100):
        x=rng.uniform(.01,1,2);a=rng.normal(size=2);h=np.stack((1-t,t),axis=1)
        y=h@x;d=h@(x*a);r=(h*x)/y[:,None]
        part=max(part,float(np.max(abs(r.sum(axis=1)-1))))
        err=max(err,float(np.max(abs(y*(r@a)-d))))
        tau=float(w@y);dt=float(w@d);e=1e-5
        obs=lambda u:np.exp(-(tau+u*dt))
        fd=max(fd,abs((obs(e)-obs(-e))/(2*e)+dt*obs(0)))
    assert max(err,part)<1e-13 and fd<1e-8
    print(json.dumps({"samples":100,"partition_max":part,"relative_hat_identity_max":err,"scalar_B_derivative_fd_max_abs":fd,"scope":"synthetic algebra controls only; source knots bound at C2"},indent=2))
if __name__=="__main__":main()
