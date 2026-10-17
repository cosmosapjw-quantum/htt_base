import numpy as np


def test_exact_ols_mask_response_resolvent_and_certified_bound():
    rng=np.random.default_rng(20261017)
    L=rng.normal(size=(80,7))
    H=rng.normal(size=(80,12))
    w=(rng.random(80)>.2).astype(float)
    wp=w.copy();wp[[5,17,64]]=1-wp[[5,17,64]]
    G=L.T@(w[:,None]*L)
    Gp=L.T@(wp[:,None]*L)
    K=np.linalg.solve(G,L.T@(w[:,None]*H))
    Kp=np.linalg.solve(Gp,L.T@(wp[:,None]*H))
    dW=wp-w
    R=H-L@K
    exact=np.linalg.solve(Gp,L.T@(dW[:,None]*R))
    assert np.linalg.norm(Kp-K-exact,2)<4e-14
    norm_diff=np.linalg.norm(Kp-K,2)
    tight=np.linalg.norm(np.linalg.solve(Gp,L.T@(dW[:,None]*R)),2)
    bound=(1/np.linalg.eigvalsh(Gp)[0])*np.linalg.norm(L.T@(dW[:,None]*R),2)
    assert np.isclose(norm_diff,tight,atol=1e-14)
    assert norm_diff<=bound*(1+1e-12)
    print({'delta_K_operator_norm':norm_diff,'certificate_bound':bound,
           'min_eig_source_Gram':np.linalg.eigvalsh(G)[0],
           'min_eig_changed_Gram':np.linalg.eigvalsh(Gp)[0]})
