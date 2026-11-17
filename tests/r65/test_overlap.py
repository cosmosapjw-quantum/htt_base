"""Independent event-Gram and profile-information checks; no science fixtures."""
import numpy as np
import pytest

try:
    from htt.htt.infer import r65_overlap as r
    from htt.htt.infer.r65_count_quotient import RingLikelihood
except ImportError:
    import r65_overlap as r
    from r65_count_quotient import RingLikelihood


def event_fixture():
    # Each tuple is ONE actual source: left bin,right bin,pixel. -1=unselected.
    events=[(0,0,0),(0,1,0),(1,1,1),(0,-1,2),(-1,0,1),
            (1,0,2),(1,0,2),(-1,1,2),(0,0,1)]
    a=np.array([[[1.,2],[3,1],[-1,2]],[[2,0],[1,-2],[4,1]]])
    b=np.array([[[1.,0,2],[3,-1,0],[1,1,1]],[[2,2,1],[0,1,2],[-1,0,1]]])
    nl=np.zeros((2,3),int);nr=np.zeros((2,3),int);s=np.zeros((2,2,3),int);rows=[]
    for left,right,pix in events:
        if left>=0:nl[left,pix]+=1
        if right>=0:nr[right,pix]+=1
        if left>=0 and right>=0:s[left,right,pix]+=1
        rows.append(np.r_[a[left,pix] if left>=0 else np.zeros(2),b[right,pix] if right>=0 else np.zeros(3)])
    rows=np.array(rows)
    return a,nl,b,nr,s,rows


def test_actual_shared_and_unmatched_event_gram_oracle():
    a,nl,b,nr,s,rows=event_fixture()
    out=r.source_overlap_sandwich(a,nl,b,nr,s)
    np.testing.assert_allclose(out['covariance_joint'],rows.T@rows,rtol=0,atol=1e-13)
    assert out['n_shared']==6
    assert out['n_unmatched_left']==1
    assert out['n_unmatched_right']==2
    assert out['covariance_contrast'] is None
    assert out['joint_diagnostics']['positive_semidefinite_within_roundoff']


def test_identical_selection_exactly_zero_paired_variance():
    a=np.arange(12,dtype=float).reshape(2,3,2)/7
    n=np.array([[2,0,4],[1,3,2]])
    s=np.zeros((2,2,3),int);s[0,0]=n[0];s[1,1]=n[1]
    out=r.paired_common_covariance(a,n,a,n,s)
    np.testing.assert_allclose(out['covariance_cross'],out['covariance_left'],atol=1e-13)
    np.testing.assert_allclose(out['covariance_contrast'],0,atol=1e-13)
    assert out['ridge_added']==0
    assert out['joint_diagnostics']['rank']==2


def test_disjoint_objects_give_variance_sum_without_cross_block():
    a=np.array([[[1.,2],[3,4]]]);b=a+1;n=np.array([[5,2]])
    out=r.paired_common_covariance(a,n,b,n,np.zeros((1,1,2),int))
    np.testing.assert_array_equal(out['covariance_cross'],0)
    np.testing.assert_allclose(out['covariance_contrast'],out['covariance_left']+out['covariance_right'])


@pytest.mark.parametrize('mode',['negative','fractional','nan','left_overcount','right_overcount','shape','influence_nan'])
def test_invalid_membership_contract_rejected(mode):
    a=np.ones((2,2,2));b=np.ones((2,2,2));nl=np.ones((2,2));nr=np.ones((2,2));s=np.zeros((2,2,2))
    if mode=='negative':nl[0,0]=-1
    elif mode=='fractional':nr[0,0]=.5
    elif mode=='nan':s[0,0,0]=np.nan
    elif mode=='left_overcount':s[0,:,0]=1
    elif mode=='right_overcount':s[:,0,0]=1
    elif mode=='shape':s=np.zeros((2,2,3))
    elif mode=='influence_nan':a[0,0,0]=np.nan
    with pytest.raises(ValueError):r.source_overlap_sandwich(a,nl,b,nr,s)


def test_coordinate_transport_full_joint_covariance():
    a,nl,b,nr,s,_=event_fixture()
    out=r.source_overlap_sandwich(a,nl,b,nr,s)
    left=np.array([[2.,1],[-1,3]])
    right=np.array([[1.,2,0],[0,1,-1],[2,0,1]])
    transformed=r.source_overlap_sandwich(a@left.T,nl,b@right.T,nr,s)
    t=np.zeros((5,5));t[:2,:2]=left;t[2:,2:]=right
    np.testing.assert_allclose(transformed['covariance_joint'],t@out['covariance_joint']@t.T,atol=1e-12)


def test_conditional_profile_information_identity_and_ring_offset_invariance():
    # Uniform four-direction ring with integer expected counts. Fit-free known
    # exponential-family state: information20I, inverse information .05I.
    f=np.array([[1.,0],[0,1],[-1,0],[0,-1]])
    exp=RingLikelihood(np.full(4,10),f,np.zeros(4,dtype=int))
    cov=np.eye(2)/20
    fit={'covariance':cov,'per_experiment_estimates':[np.zeros(2)]}
    a=r.common_influences([exp],fit,[np.eye(2)])
    out=r.source_overlap_sandwich(a,exp.counts[None,:],a,exp.counts[None,:],exp.counts[None,None,:])
    np.testing.assert_allclose(out['covariance_left'],cov,atol=1e-15)
    shifted=RingLikelihood(np.full(4,10),f+[100.,-57.],np.zeros(4,dtype=int))
    a2=r.common_influences([shifted],fit,[np.eye(2)])
    np.testing.assert_allclose(a2,a,atol=1e-14)


def test_zero_membership_covariance_keeps_true_rank_zero():
    a=np.ones((1,2,2));n=np.zeros((1,2),int)
    out=r.source_overlap_sandwich(a,n,a,n,np.zeros((1,1,2),int))
    assert out['joint_diagnostics']['rank']==0
    assert out['joint_diagnostics']['min_eigenvalue']==0
    np.testing.assert_array_equal(out['covariance_joint'],np.zeros((4,4)))
