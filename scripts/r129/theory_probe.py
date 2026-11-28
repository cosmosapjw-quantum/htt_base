import json,numpy as np
def main():
    rng=np.random.default_rng(129);err=0.;fit=0.
    for _ in range(100):
        z=rng.normal(size=(12,4))+1j*rng.normal(size=(12,4));v=rng.normal(size=4)+1j*rng.normal(size=4)
        R=np.block([[z.real,-z.imag],[z.imag,z.real]]);y=np.r_[(z@v).real,(z@v).imag]
        err=max(err,float(np.max(abs(R@np.r_[v.real,v.imag]-y))))
        A=rng.normal(size=(24,5));u,s,vh=np.linalg.svd(R,full_matrices=False);P=u@u.T
        c=-np.linalg.lstsq(R,A,rcond=None)[0];E=A+R@c
        fit=max(fit,float(np.max(abs(E-(A-P@A)))),float(np.max(abs(R.T@E))))
    assert err<1e-13 and fit<1e-12
    print(json.dumps({"samples":100,"realification_max_abs":err,"profile_fit_max_abs":fit,"scope":"synthetic algebra; source-specific matrices in C6/C7"},indent=2))
if __name__=="__main__":main()
