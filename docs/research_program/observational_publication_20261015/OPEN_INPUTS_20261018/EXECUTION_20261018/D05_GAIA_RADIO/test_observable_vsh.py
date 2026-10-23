import numpy as np
import pytest
from observable_vsh import design,tangent,precision,normal,solve,S,KEEP
import observable_vsh

def fixture():
    # Deterministic all-sky geometry, with nontrivial within-source correlation.
    ra=np.linspace(0,360,101,endpoint=False)
    dec=np.rad2deg(np.arcsin(np.linspace(-.97,.97,101)))
    X=design(ra,dec);b=np.linspace(-3,5,16)
    return X,b,np.einsum('nip,p->ni',X,b)

def test_exact_harmonic_recovery_and_frame_quotient():
    X,b,y=fixture();w=precision(np.full(101,2.),np.full(101,3.),np.full(101,.3))
    fit=solve(normal(X,y,w))
    np.testing.assert_allclose(fit['coefficient_uasyr'],b,rtol=1e-11,atol=1e-11)
    np.testing.assert_allclose(fit['frame_projected']['coefficient_uasyr'],b[KEEP],atol=1e-11)
    assert fit['frame_projected']['rank']==13
    assert fit['frame_projected']['B1_physical_components']==['UNKNOWN']*3

def test_tangent_rotation_signs_and_STF():
    X=design(np.array([0.]),np.array([0.]))
    # At +x: omega_z cross n points +east, omega_y cross n points -north.
    assert X[0,0,5]==1
    assert X[0,1,4]==-1
    np.testing.assert_allclose(np.einsum('pij,qij->pq',S,S),np.eye(5),atol=1e-15)
    np.testing.assert_allclose(np.trace(S,axis1=1,axis2=2),0,atol=1e-15)

def test_precision_really_inverts_full_covariance():
    sa=np.array([2.,3.]);sd=np.array([4.,5.]);rho=np.array([.6,-.7])
    c=np.zeros((2,2,2));c[:,0,0]=sa**2;c[:,1,1]=sd**2
    c[:,0,1]=c[:,1,0]=rho*sa*sd
    np.testing.assert_allclose(precision(sa,sd,rho),np.linalg.inv(c))
    with pytest.raises(ValueError):precision(sa,sd,np.ones(2))

def test_frame_addition_does_not_change_identified_quotient():
    X,b,y=fixture();w=precision(np.full(101,2.),np.full(101,3.),np.full(101,-.4))
    delta=np.zeros(16);delta[3:6]=[100.,-300.,200.]
    f=solve(normal(X,y+np.einsum('nip,p->ni',X,delta),w))
    np.testing.assert_allclose(f['frame_projected']['coefficient_uasyr'],b[KEEP],atol=1e-10)

def test_chunk_additivity_and_dense_gls():
    X,b,y=fixture();w=precision(np.full(101,2.),np.full(101,3.),np.full(101,.6))
    n,h,_,_=normal(X,y,w)
    a=normal(X[:30],y[:30],w[:30]);c=normal(X[30:],y[30:],w[30:])
    np.testing.assert_allclose(a[0]+c[0],n,atol=1e-12)
    np.testing.assert_allclose(a[1]+c[1],h,atol=1e-12)
    dense=np.zeros((202,202))
    for i in range(101):dense[2*i:2*i+2,2*i:2*i+2]=w[i]
    flat=X.reshape(202,16)
    np.testing.assert_allclose(n,flat.T@dense@flat,atol=1e-12)

@pytest.mark.parametrize('status',['OVERFLOW','ERROR'])
def test_post_table_non_ok_status_is_rejected(tmp_path,monkeypatch,status):
    monkeypatch.setattr(observable_vsh,'RAW',tmp_path)
    (tmp_path/'cut.vot').write_text('<VOTABLE><RESOURCE><INFO name="QUERY_STATUS" value="OK"/>'
        '<TABLE/><INFO name="QUERY_STATUS" value="'+status+'"/></RESOURCE></VOTABLE>')
    with pytest.raises(ValueError,match='Non-complete VOTable'):
        observable_vsh.read_vot('cut')
