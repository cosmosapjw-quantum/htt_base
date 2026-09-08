"""Supported external channels, with actual reference replay and rate semantics."""
from __future__ import annotations
from dataclasses import dataclass,field,fields
import numpy as np
from common.r7_contracts import UnsupportedObservable,finite_array,content_id,RadiationJet


@dataclass(frozen=True)
class ReferenceCase:
    channel: str
    arguments: tuple
    expected: object
    absolute_error: float
    relative_error: float
    source_id: str


class ExternalTransferProvider:
    def __init__(self,backend=None,*,source_id=None,mode=None,domain=None,reference_cases=()):
        self.backend=backend;self.source_id=source_id;self.mode=mode;self.domain=domain
        self.provider_id="EXTERNAL_TRANSFER:"+str(source_id)
        self.validation=[];self._supported=set()
        if backend is None:return
        if not source_id or not mode or domain is None:raise ValueError("external source, supported mode and parameter domain required")
        for case in reference_cases:
            if not isinstance(case,ReferenceCase) or not case.source_id: raise ValueError("independent source-bound reference case required")
            if case.channel not in {"harmonics","distance","radiation_jet","anisotropic_covariance"}: raise ValueError("unknown reference channel")
            function=getattr(backend,{"harmonics":"predict_harmonics","distance":"predict_distance","radiation_jet":"radiation_jet","anisotropic_covariance":"predict_covariance"}[case.channel],None)
            if not callable(function):self.validation.append({"channel":case.channel,"status":"UNSUPPORTED"});continue
            if not np.isfinite([case.absolute_error,case.relative_error]).all() or case.absolute_error<0 or case.relative_error<0:raise ValueError("finite nonnegative reference errors")
            value=function(*case.arguments)
            if case.channel=='radiation_jet':
                if not isinstance(value,RadiationJet) or not isinstance(case.expected,RadiationJet):raise ValueError('typed radiation-jet reference required')
                actual_values=[];expected_values=[]
                for item in fields(RadiationJet):
                    a=getattr(value,item.name);b=getattr(case.expected,item.name)
                    if a is None or b is None or isinstance(a,(str,bool)) or isinstance(b,(str,bool)):
                        if a!=b:raise ValueError('radiation-jet convention/premise/reference field mismatch: '+item.name)
                    else:
                        a=finite_array(a);b=finite_array(b,shape=a.shape)
                        actual_values.extend(a.ravel());expected_values.extend(b.ravel())
                actual=np.array(actual_values);expected=np.array(expected_values)
            else:
                actual=finite_array(value);expected=finite_array(case.expected,shape=actual.shape)
            passed=bool(np.all(abs(actual-expected)<=case.absolute_error+case.relative_error*abs(expected)))
            self.validation.append({"channel":case.channel,"status":"PASS" if passed else "FAIL","source":case.source_id,
                "maximum_error":float(np.max(abs(actual-expected))),"actual_id":content_id(actual)})
        channels={v['channel'] for v in self.validation}
        for channel in channels:
            if all(v['status']=='PASS' for v in self.validation if v['channel']==channel):self._supported.add(channel)

    def capabilities(self):return tuple(sorted(self._supported))

    def _call(self,channel,method,args):
        if channel not in self._supported:raise UnsupportedObservable(f"{self.provider_id} lacks validated {channel}")
        if not self.domain(args[0]): raise UnsupportedObservable("parameters/event outside external validated domain")
        result=getattr(self.backend,method)(*args)
        if channel=="radiation_jet":
            if not isinstance(result,RadiationJet):raise ValueError("external derivative jet must retain T3 conventions")
            return result
        return finite_array(result)

    def predict_harmonics(self,parameters,initial_conditions,observer):
        return self._call("harmonics","predict_harmonics",(parameters,initial_conditions,observer))

    def predict_distance(self,parameters,source,observer,direction,redshift):
        return self._call("distance","predict_distance",(parameters,source,observer,direction,redshift))

    def radiation_jet(self,event):return self._call("radiation_jet","radiation_jet",(event,))

    def predict_covariance(self,parameters):return self._call("anisotropic_covariance","predict_covariance",(parameters,))

    @staticmethod
    def shear_rate_from_metric_derivative(beta_ij_dot,*,time_coordinate,scale_factor=1.):
        value=finite_array(beta_ij_dot,shape=(3,3))
        if time_coordinate not in {"PROPER_SECONDS","CONFORMAL_SECONDS"}:raise ValueError("metric beta is not a rate; derivative time coordinate required")
        if not np.isfinite(scale_factor) or scale_factor<=0:raise ValueError("positive scale factor")
        return value if time_coordinate=="PROPER_SECONDS" else value/scale_factor


def bind_provider_factories(factories,providers,validation_points):
    """Bind and exercise each independent factory/provider scope separately."""
    from htt.infer.r7_gaussian_law import JointObservationLaw
    results=[]
    for factory in factories:
        for provider in providers:
            key=(factory.factory_id,provider.provider_id)
            try:
                law=factory.bind(provider)
                if not isinstance(law,JointObservationLaw):raise TypeError("factory did not bind a law")
                points=validation_points.get(key,())
                if not points:raise UnsupportedObservable("normalization/domain/unit validation points absent")
                for theta,eta in points:
                    if not law.domain_contains(theta,eta):raise ValueError("factory validation point outside law domain")
                    mean=finite_array(law.mean(theta,eta),shape=law.observed.shape)
                    value=law.loglik(theta,eta)
                    if np.isnan(value) or value==np.inf:raise ValueError("invalid bound density")
                results.append({"factory_id":key[0],"provider_id":key[1],"law":law,"outcome":"BOUND_LAW_VALIDATED_ON_DECLARED_POINTS"})
            except (ValueError,TypeError,UnsupportedObservable) as exc:
                results.append({"factory_id":key[0],"provider_id":key[1],"law":None,"outcome":"UNAVAILABLE","reason":str(exc)})
    return tuple(results)
