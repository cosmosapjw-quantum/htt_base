"""P-defined DESI 18-vector/refit adapter with explicit mock-law limitations."""
from __future__ import annotations
from dataclasses import asdict, replace
import numpy as np
from scipy.integrate import quad
from obsstat.desi_successor_formalism import (DESIRealization,DESISelection,fit_realization,build_mock_support,
    validate_selection,FEATURE_ORDER)
from common.r7_contracts import content_id
from .r7_gaussian_law import JointObservationLaw,ObservationLawFactory
from common.r7_contracts import UnavailableLaw


def build_desi_law(product,randoms,matched_mocks,selection):
    pid=product.get("product_id","DESI_BGS_BRIGHT")
    if not isinstance(selection,DESISelection): return UnavailableLaw(pid,"INPUT_UNAVAILABLE",("exact P BGS_BRIGHT selection unavailable",))
    validate_selection(selection)
    if randoms is None or matched_mocks is None:
        return UnavailableLaw(pid,"INPUT_UNAVAILABLE",("matched random window or mock sampling law absent",))
    if tuple(randoms["window_ids"])!=selection.window_ids or randoms["frame"]!=selection.coordinate_frame_id:
        raise ValueError("DESI window/frame mismatch")
    observed=product.get("realization")
    if not isinstance(observed,DESIRealization): return UnavailableLaw(pid,"INPUT_UNAVAILABLE",("per-row exact P realization cannot be built from supplied raw factors",))
    if observed.family!="OBSERVED": raise ValueError("observed DESI family mismatch")
    # No pre-fitted bank or invalidated PR-151 numerical payload is accepted.
    ez=tuple(matched_mocks.get("ezmock",()));ab=tuple(matched_mocks.get("abacus",()))
    if any(not isinstance(v,DESIRealization) for v in ez+ab): raise ValueError("every mock must enter the P refit as a raw realization")
    fit=fit_realization(observed,selection)
    support=build_mock_support(ez,ab,selection)
    spec={"source_ids":product["source_ids"],"selection_law":asdict(selection),"covariance_source":"P_REFITTED_EZMOCK_EMPIRICAL_SCATTER",
        "mean_definition":"P NGC/SGC x three depth bins x xyz with per-realization normalization and nuisance refit",
        "feature_order":FEATURE_ORDER,"randoms_source_id":randoms["source_id"],"observed_fit":fit.features,
        "ezmock_ids":[r.realization for r in ez],"abacus_ids":[r.realization for r in ab],
        "mock_law_id":matched_mocks["law_id"],"refit_procedure":"P fit_realization on every input"}
    builder=matched_mocks.get("normalized_law_builder")
    if builder is None:
        return UnavailableLaw(pid,"SCENARIO_ONLY",("empirical covariance/refits do not provide a normalized physical sampling law",),
            {"observed_features":fit.features,"feature_order":FEATURE_ORDER,"mock_support":asdict(support),
             "law_specification":spec,"normalization_hat":fit.alpha_hat,"nuisance_hat":fit.nuisance_hat})
    slots=tuple(matched_mocks.get("unfilled_prediction_slots",("desi_selection_response",)))
    def bind(provider):
        law=builder(fit,support,selection,provider)
        if not isinstance(law,JointObservationLaw): raise TypeError("normalized DESI builder must return JointObservationLaw")
        if tuple(law.measurement_ids)!=FEATURE_ORDER: raise ValueError("DESI law changed the registered vector")
        if law.specification.get("mock_law_id")!=matched_mocks["law_id"]: raise ValueError("DESI law dropped its matched mock law")
        return law
    return ObservationLawFactory(content_id(spec),FEATURE_ORDER,slots,spec,bind)


def build_compressed_bao_law(payload):
    """Official qiso likelihood as its declared fixed Gaussian summary model.

    Its confidence is conditional on this published approximation being the
    sampling law. This does not prove true raw-catalogue coverage, or supply an
    angular response, raw-selection law, or independence from DESI raw rows.
    """
    from common.r7_contracts import ScopeKey,content_id,finite_array
    from .r7_gaussian_law import JointObservationLaw,decompose_covariance
    if payload['likelihood_name']!='gaussian_likelihood' or payload['parameter']!='qiso':
        raise ValueError('unsupported released compressed likelihood')
    y=finite_array(payload['observed'],shape=(1,));c=decompose_covariance(payload['covariance'])
    window=finite_array(payload['window'],shape=(1,1))
    if not c.resolved or c.rank!=1 or c.covariance.shape!=(1,1) or window[0,0]!=1:
        raise ValueError('qiso covariance/window not the supported scalar law')
    if payload['DV_over_rd_fid']<=0 or payload['zeff']<=0:raise ValueError('positive fiducial scale and redshift required')
    spec=dict(source_ids=[payload['source_id']],selection_law='RELEASED_BGS_BRIGHT_Z0.1_0.4_COMPRESSION',
        covariance_source=payload['source_id']+':covariance/value',mean_definition='qiso=DV/rd divided by released fiducial DV/rd',
        observed_parameter='qiso',fiducial=payload['DV_over_rd_fid'],zeff=payload['zeff'],window=window,
        covariance=c.covariance,model_assumption='fixed published Gaussian summary law, not verified true catalogue covariance',
        conditional_confidence_only=True)
    return JointObservationLaw(ScopeKey('DESI_DR1_BGS_COMPRESSED_SYST',content_id(spec),'RELEASED_GAUSSIAN_QISO',
        (payload['source_id'],),method_config_id=content_id({'selection':'syst alternative only','alpha':.05})),
        y,('BGS_BRIGHT_GCcomb_qiso',),('qiso',),('1',),lambda t,e:finite_array(t,shape=(1,)),c.covariance,spec,
        'POSITIVE_QISO',lambda t,e:np.asarray(t).shape==(1,) and np.isfinite(t[0]) and t[0]>0,
        jacobian_theta=lambda t,e:np.ones((1,1)),jacobian_eta=lambda t,e:np.empty((1,0)),
        conditioning_target='PUBLISHED_GAUSSIAN_SUMMARY_MODEL_WITH_FIXED_RELEASED_COVARIANCE',
        approximation='CONDITIONAL_ON_RELEASED_GAUSSIAN_SUMMARY_LAW')


def flat_lcdm_qiso(omega_m, h0_rd_km_s, *, zeff, dv_over_rd_fid):
    """Scalar BAO response in flat matter+Lambda FLRW, with free H0*r_d.

    This late-time response does not calculate the sound horizon. The product
    H0*r_d has km/s units and is an explicit physical input. The released
    scalar qiso has no angular response.
    """
    values=np.asarray((omega_m,h0_rd_km_s,zeff,dv_over_rd_fid),dtype=float)
    if (not np.isfinite(values).all() or not 0 < omega_m < 1 or h0_rd_km_s <= 0
            or zeff <= 0 or dv_over_rd_fid <= 0):
        raise ValueError('flat-LCDM qiso requires 0<Omega_m<1 and positive finite scales/redshift')
    def inv_e(z):
        return 1/np.sqrt(omega_m*(1+z)**3+1-omega_m)
    radial,error=quad(inv_e,0,zeff,epsabs=1e-12,epsrel=1e-12)
    if error > 1e-10*radial:
        raise ValueError('radial-distance quadrature did not meet requested tolerance')
    e_z=1/inv_e(zeff)
    shape=np.cbrt(zeff*radial*radial/e_z)
    return float((299792.458/h0_rd_km_s)*shape/dv_over_rd_fid)


def build_flat_lcdm_bao_law(payload):
    """Rebind one released Gaussian datum to an explicit flat-LCDM response.

    Original released-summary conditioning and covariance are retained. This
    two-parameter conditional likelihood is not a posterior or catalogue refit.
    """
    base=build_compressed_bao_law(payload)
    fid=float(payload['DV_over_rd_fid']); z=float(payload['zeff'])
    spec=dict(base.specification,
              mean_definition='qiso=(flat-LCDM D_V(z_eff)/r_d)/(released fiducial D_V/r_d)',
              physical_response='FLAT_MATTER_PLUS_LAMBDA_FLRW_FREE_H0_RD',
              response_units={'Omega_m':'1','H0_r_d':'km/s'},
              sound_horizon_status='EXTERNAL_FREE_PRODUCT_NOT_CALCULATED',
              angular_response_status='UNAVAILABLE_FROM_SCALAR_QISO')
    def domain(theta,eta):
        t=np.asarray(theta,dtype=float)
        return t.shape==(2,) and np.isfinite(t).all() and 0<t[0]<1 and t[1]>0 and eta is None
    def mean(theta,eta):
        return np.asarray([flat_lcdm_qiso(float(theta[0]),float(theta[1]),
                                            zeff=z,dv_over_rd_fid=fid)])
    return replace(base,scope=replace(base.scope,model_id='FLAT_LCDM_FREE_H0_RD',law_id=content_id(spec)),
                   parameter_names=('Omega_m','H0_r_d'),parameter_units=('1','km/s'),
                   mean=mean,specification=spec,domain_id='FLAT_LCDM_0_LT_OMEGA_M_LT_1_H0_RD_POSITIVE',
                   domain_contains=domain,jacobian_theta=None,jacobian_eta=None,
                   approximation='FLAT_LCDM_NUMERIC_DISTANCE_CONDITIONAL_ON_RELEASED_GAUSSIAN_SUMMARY')
