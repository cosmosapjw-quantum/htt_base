import hashlib
import numpy as np
import pytest
from common.r7_contracts import UnsupportedObservable
from bass.transfer.r7_benchmark_provider import RestrictedR3Provider
from bass.transfer.r7_external_provider import ExternalTransferProvider,ReferenceCase
from bass.transfer.native_adapter import default_native_lowell_adapter_stub
from bass.background.bi_continuation.dynamics import BIState,rhs,shear_rhs_from_physical
from bass.background.bi_continuation.moments import SpeciesPrimitive,total_projection


def test_missing_restricted_source_closes_only_provider_and_native_stays_unavailable(tmp_path):
    p=RestrictedR3Provider(tmp_path)
    assert p.capabilities()==() and set(p.source_status().values())=={'SOURCE_UNAVAILABLE'}
    with pytest.raises(UnsupportedObservable):p.predict_harmonics({},None,None)
    with pytest.raises(UnsupportedObservable):p.predict_distance({},None,None,None,.1)
    with pytest.raises(NotImplementedError):default_native_lowell_adapter_stub().evaluate()


def test_H_dust_donor_conserves_rapidity_momentum_and_compensates_flux():
    H=2.;S=.2;beta=.3;gamma=1/np.sqrt(1-beta**2)
    species=(SpeciesPrimitive(1.,0.,np.array([0.,0.,beta]),'plus'),SpeciesPrimitive(1.,0.,np.array([0.,0.,-beta]),'minus'))
    state=BIState(1.,H,np.diag([-S,-S,2*S]),species)
    derivative=rhs(state)
    expected=-(H+2*S)*beta*(1-beta**2)
    assert abs(derivative.velocity_dot[0][2]-expected)<1e-14
    assert abs((H+2*S)*gamma*beta+gamma**3*expected)<1e-14
    # Legacy rapidity -H_parallel*sinh(chi)*cosh(chi) violates the Killing invariant.
    wrong_chi=-(H+2*S)*gamma**2*beta
    assert abs((H+2*S)*gamma*beta+gamma*wrong_chi)>.01
    total=total_projection(species)
    np.testing.assert_allclose(total.flux,np.zeros(3),atol=0)
    np.testing.assert_allclose(shear_rhs_from_physical(H,np.diag([-S,-S,2*S]),total.anisotropic_stress),derivative.sigmadot)


def test_external_channels_require_actual_reference_replay_and_never_zero_fill():
    class Fixture:
        def predict_harmonics(self,p,initial,observer):return np.array([2*p[0],0.])
    empty=ExternalTransferProvider()
    assert empty.capabilities()==()
    p=ExternalTransferProvider(Fixture(),source_id='SCENARIO_FIXTURE',mode='linear fixture',domain=lambda p:abs(p[0])<=1,
        reference_cases=(ReferenceCase('harmonics',([.5],None,None),[1.,0.],0.,0.,'independent arithmetic fixture'),))
    assert p.capabilities()==('harmonics',)
    with pytest.raises(UnsupportedObservable):p.predict_distance([0.],None,None,None,.1)
    with pytest.raises(UnsupportedObservable):p.predict_covariance([0.])
    with pytest.raises(UnsupportedObservable):p.predict_harmonics([2.],None,None)
    derivative=np.diag([1.,1.,-2.])
    np.testing.assert_equal(p.shear_rate_from_metric_derivative(derivative,time_coordinate='CONFORMAL_SECONDS',scale_factor=.5),2*derivative)


def test_typed_external_radiation_jet_reference_and_event_domain():
    from common.r7_contracts import RadiationJet,UnsupportedObservable
    from bass.transfer.r7_external_provider import ReferenceCase,ExternalTransferProvider
    jet=RadiationJet(3.,2.7,'OUTWARD','FRAME','DOMAIN')
    class Backend:
        def radiation_jet(self,event):return jet
    provider=ExternalTransferProvider(Backend(),source_id='fixture',mode='JET',domain=lambda e:e=='event',
        reference_cases=(ReferenceCase('radiation_jet',('event',),jet,0.,0.,'independent fixture'),))
    assert provider.capabilities()==('radiation_jet',)
    assert provider.radiation_jet('event') is jet
    with pytest.raises(UnsupportedObservable):provider.radiation_jet('different event')
