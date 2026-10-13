"""Independent dense oracles and current bulk-flow callsite compatibility."""
import numpy as np
import pytest
from common.bulkflow_covariance import SamplingCovariance
from common.structured_inference import StructuredLinearModel
from common.bulkflow_estimator import gls_bulk_flow, wls_bulk_flow
from common.bulkflow_likelihood import BulkFlowLikelihood


def contract(p):
    return dict(observation_order_id='synthetic-row-order-v1', selection_id='all-fixed',
                observation_unit='km/s', coefficient_units=['km/s']*p)


def fixture():
    rng = np.random.default_rng(20261013)
    n = 72
    d = rng.uniform(.5, 2, n); U = rng.normal(size=(n, 4))*.2
    F = rng.normal(size=(n, 6)); N0 = rng.normal(size=(n, 2))
    N = np.column_stack((N0, N0[:, 0]+2*N0[:, 1]))
    y = rng.normal(size=n)
    return rng, d, U, F, N, y


@pytest.mark.parametrize('dense', [False, True])
def test_dense_oracle_and_support(dense):
    rng, d, U, F, N, y = fixture(); C = np.diag(d)+U@U.T
    cov = SamplingCovariance(dense=C) if dense else SamplingCovariance(diagonal=d, low_rank=U)
    model = StructuredLinearModel(F, cov, nuisance=N, nuisance_units=["km/s"]*3, **contract(6))
    # Oracle uses a dense Cholesky and joint least squares, not model projection.
    L = np.linalg.cholesky(C); X = np.linalg.solve(L, np.column_stack((F, N)))
    wy = np.linalg.solve(L, y)
    a = np.linalg.lstsq(X, wy, rcond=None)[0][:6]
    assert np.allclose(model.fit(y)['estimate'], a, atol=2e-12)
    assert np.allclose(cov.whiten_transpose(cov.whiten(F)), np.linalg.solve(C, F), atol=2e-12)
    assert np.isclose(cov.logdet(), np.linalg.slogdet(C)[1])
    comp = model.compress(y); aa = rng.normal(size=6); bb = aa+.2
    residual = np.linalg.solve(L, y-F@aa)
    eta = np.linalg.lstsq(np.linalg.solve(L, N), residual, rcond=None)[0]
    residual -= np.linalg.solve(L, N)@eta
    assert np.isclose(comp.quadratic(aa), residual@residual)
    assert np.isclose(comp.deviance_difference(aa, bb), comp.quadratic(aa)-comp.quadratic(bb))
    assert np.allclose(model.fit(y+N@rng.normal(size=3))['estimate'], a)
    M = np.stack([model.influence(g) for g in np.eye(6)])
    assert np.allclose(M@C@M.T, model.covariance, atol=2e-12)
    assert np.allclose(M@N, 0, atol=2e-12)
    g = rng.normal(size=6); ell = model.influence(g)
    box = rng.uniform(0, .2, 72); E = rng.normal(size=(72, 3)); radius=.3
    result = model.scalar_interval(y, g, box=box, envelope=E, radius=radius)
    v = E.T@ell; b = box*np.sign(ell)+radius*E@(v/np.linalg.norm(v))
    assert np.isclose(result['bias_bound'], ell@b)
    assert np.isclose(result['center'], g@a)
    assert result['variance'] == pytest.approx(ell@C@ell)
    with pytest.raises(ValueError, match='not marginal evidence'):
        comp.marginal_log_likelihood(aa)


def test_rank_alias_and_identity_snapshot():
    _, d, U, F, N, y = fixture()
    aliased = StructuredLinearModel(N, SamplingCovariance(diagonal=d), nuisance=N, nuisance_units=["km/s"]*3, **contract(3))
    assert aliased.rank == 0
    with pytest.raises(ValueError, match='not identifiable'):
        aliased.influence([1, 0, 0])
    F[:, 1] = F[:, 0]
    model = StructuredLinearModel(F, SamplingCovariance(diagonal=d, low_rank=U), **contract(6))
    assert model.rank == 5
    model.influence([1, 1, 0, 0, 0, 0])
    with pytest.raises(ValueError): model.influence([1, -1, 0, 0, 0, 0])
    original = model.fit(y)['estimate']; comp = model.compress(y)
    d *= 4; U *= 3; F *= 2
    assert np.array_equal(original, model.fit(y)['estimate'])
    changed = StructuredLinearModel(F, SamplingCovariance(diagonal=d, low_rank=U), **contract(6))
    with pytest.raises(ValueError): comp.require_identity(changed.identity)
    comp.require_identity(model.identity)
    for key, value in [('selection_id', 'different'), ('observation_order_id', 'reverse'), ('observation_unit','m/s')]:
        args = contract(6); args[key] = value
        other = StructuredLinearModel(F/2, SamplingCovariance(diagonal=d/4, low_rank=U/3), **args)
        assert model.identity != other.identity


@pytest.mark.parametrize('dense', [False, True])
def test_proper_gaussian_marginal(dense):
    _, d, U, F, N, y = fixture(); N = N[:, :2]; S = np.array([[.4,.1],[.1,.3]])
    mean = np.array([.2,-.4]); C = np.diag(d)+U@U.T
    cov = SamplingCovariance(dense=C) if dense else SamplingCovariance(diagonal=d, low_rank=U)
    model = StructuredLinearModel.gaussian_marginal(F, cov, N, S, prior_mean=mean, nuisance_units=["km/s"]*2, **contract(6))
    aa = np.arange(6)*.1; Ce = C+N@S@N.T; r=y-F@aa-N@mean
    oracle = -.5*(r@np.linalg.solve(Ce,r)+np.linalg.slogdet(Ce)[1]+72*np.log(2*np.pi))
    assert model.compress(y).marginal_log_likelihood(aa) == pytest.approx(oracle)
    with pytest.raises(ValueError): model.compress(y).profile_log_likelihood(aa)
    assert model.nuisance_rank == 0
    with pytest.raises(ValueError):
        StructuredLinearModel.gaussian_marginal(F, cov, N, -S, nuisance_units=["km/s"]*2, **contract(6))


def test_current_gls_wls_likelihood_calls():
    rng, d, U, F, _, y = fixture(); X = F[:,:3]; X /= np.linalg.norm(X,axis=1)[:,None]
    cov = SamplingCovariance(diagonal=d,low_rank=U)
    model = StructuredLinearModel(X,cov,**contract(3)); fit=model.fit(y)
    old = gls_bulk_flow(X,y,sampling_covariance=cov)
    assert np.allclose(old.V_hat,fit['estimate']); assert np.allclose(old.cov,fit['covariance'])
    like = BulkFlowLikelihood(X,y,np.sqrt(d),np.ones(72),np.ones(72),sampling_covariance=cov)
    assert like.log_likelihood([.2,.4,.1]) == pytest.approx(model.compress(y).profile_log_likelihood([.2,.4,.1]))
    # OBS01: objective weights do not redefine sampling covariance.
    weights=rng.uniform(.1,3,72); oldw=wls_bulk_flow(X,y,weights,sampling_covariance=cov)
    M=np.linalg.solve(X.T@(weights[:,None]*X),X.T*weights)
    assert np.allclose(oldw.cov,M@cov.matmat(M.T))
    assert not np.allclose(oldw.cov,np.linalg.inv(X.T@(weights[:,None]*X)))


def test_rank_tolerance_and_invalid_inputs():
    _, d, _, F, _, y = fixture()
    for value in [-1,1,float('nan')]:
        with pytest.raises(ValueError): StructuredLinearModel(F,d,rank_rtol=value,**contract(6))
    model=StructuredLinearModel(F,d,**contract(6))
    for kwargs in [dict(box=-np.ones(72)),dict(envelope=np.ones((72,2)),radius=-1),dict(alpha=0)]:
        with pytest.raises(ValueError): model.scalar_interval(y,np.ones(6),**kwargs)
    F[:,5]*=1e-10
    assert StructuredLinearModel(F,d,rank_rtol=1e-8,**contract(6)).rank==5
    assert StructuredLinearModel(F,d,rank_rtol=1e-12,**contract(6)).rank==6

@pytest.mark.parametrize('tiny', [1e-20, 1e-34, 1e-100])
@pytest.mark.parametrize('coupling', [0., 1e-8, .4])
@pytest.mark.parametrize('permutation', [[0,1], [1,0]])
def test_extreme_diagonal_low_rank_fails_closed(tiny, coupling, permutation):
    d=np.array([tiny,1.])[permutation]; U=np.array([[1.],[coupling]])[permutation]
    cov=SamplingCovariance(diagonal=d,low_rank=U)
    with pytest.raises(ArithmeticError, match='dynamic range is unresolved'):
        cov.whiten(np.eye(2))
    with pytest.raises(ArithmeticError, match='dynamic range is unresolved'):
        cov.whiten_transpose(np.eye(2))
    with pytest.raises(ArithmeticError, match='dynamic range is unresolved'):
        StructuredLinearModel(np.eye(2),cov,**contract(2))


@pytest.mark.parametrize('tiny', [1.,1e-4,1e-8])
@pytest.mark.parametrize('coupling', [0.,1e-8,.4])
def test_whitening_row_permutation_dense_oracle(tiny,coupling):
    d=np.array([tiny,1.]); U=np.array([[1.],[coupling]])
    C=np.diag(d)+U@U.T; vectors=np.column_stack((np.eye(2),U[:,0]+[1e-8,-1e-8]))
    precisions=[]
    for permutation in ([0,1],[1,0]):
        cov=SamplingCovariance(diagonal=d[permutation],low_rank=U[permutation])
        W=cov.whiten(np.eye(2)); Cp=C[np.ix_(permutation,permutation)]
        assert np.allclose(W@Cp@W.T,np.eye(2),rtol=1e-10,atol=1e-10)
        actual=cov.whiten_transpose(cov.whiten(vectors[permutation]))
        oracle=np.linalg.solve(Cp,vectors[permutation])
        assert np.allclose(actual,oracle,rtol=1e-10,atol=1e-10)
        precisions.append(actual[np.argsort(permutation)])
        model=StructuredLinearModel(np.eye(2)[permutation],cov,**contract(2))
        assert np.allclose(model.fit(np.array([1.,2.])[permutation])['estimate'],[1.,2.],atol=1e-10)
    assert np.allclose(*precisions,rtol=1e-10,atol=1e-10)


def test_extreme_full_modal_span_fails_closed():
    U=np.array([[1.,.4],[-.2,1.]])
    cov=SamplingCovariance(diagonal=np.full(2,1e-34),low_rank=U)
    with pytest.raises(ArithmeticError,match='dynamic range is unresolved'):
        cov.whiten(np.eye(2))


def test_finite_inputs_overflow_fail_explicitly():
    with pytest.raises(ArithmeticError, match='finite numerical domain'):
        StructuredLinearModel(np.full((2,1),1e154),np.ones(2),**contract(1))
    model=StructuredLinearModel(np.ones((2,1)),np.ones(2),**contract(1))
    with pytest.raises(ArithmeticError, match='finite numerical domain'):
        model.compress(np.full(2,1e154))
    comp=model.compress(np.ones(2))
    with pytest.raises(ArithmeticError, match='finite numerical domain'):
        comp.quadratic([1e308])
