"""CF4 conditional affine and supplied normalized latent-distance experiments."""
from __future__ import annotations
from dataclasses import dataclass
import math
import numpy as np
from scipy.integrate import nquad
from common.r7_contracts import ScopeKey, CONVENTIONS, VERSION, finite_array, content_id, NumericalUnresolved
from obsstat.cf4_current_stack import Cf4OperatorInputs,build_cf4_affine_design,galactic_unit_vectors
from .r7_gaussian_law import JointObservationLaw,ObservationLawFactory,decompose_covariance


CF4_PARAMETERS=("trace_over_3","Bx","By","Bz","Sxx","Syy","Sxy","Sxz","Syz")
CF4_UNITS=("km/s/Mpc","km/s","km/s","km/s","km/s/Mpc","km/s/Mpc","km/s/Mpc","km/s/Mpc","km/s/Mpc")


from common.r7_contracts import UnavailableLaw


@dataclass(frozen=True)
class SelectedLatentBlock:
    """Supplied joint measurement density and source intensity, conditional on Z.

    Measurement and latent integration domains are physical inputs. This handles
    a correlated measurement block as one block, with shared eta conditioned
    once. It never factorizes a correlated catalogue or estimates a selection
    function from observed weights. The count law is explicitly conditional on
    this one selected block. Population Poisson counts need a separate adapter.
    """
    latent_bounds: tuple
    measurement_bounds: tuple
    intensity: object
    measurement_density: object
    selection: object
    source_id: str
    relative_error: float = 1e-8
    absolute_error: float = 1e-10

    def _integral(self,f,bounds):
        value,error=nquad(f,bounds,opts={"epsabs":self.absolute_error,"epsrel":0.})
        if not math.isfinite(value) or not math.isfinite(error) or value<0 or error>self.absolute_error:
            raise NumericalUnresolved("selected latent normalization integration unresolved")
        return value,error

    def intensity_at(self,y,theta,eta,provider):
        s=float(self.selection(y))
        if not math.isfinite(s) or not 0<=s<=1: raise ValueError("selection probability must be in [0,1]")
        def integrand(*xi):
            intensity=float(self.intensity(np.array(xi),theta,eta,provider))
            density=float(self.measurement_density(y,np.array(xi),theta,eta,provider))
            if not all(math.isfinite(v) and v>=0 for v in (intensity,density)): raise ValueError("nonnegative finite intensity and density required")
            return intensity*density
        value,error=self._integral(integrand,self.latent_bounds)
        return s*value,s*error

    def loglik(self,y,theta,eta,provider):
        if len(y)!=len(self.measurement_bounds): raise ValueError("joint selected measurement dimension")
        if any(v<a or v>b for v,(a,b) in zip(y,self.measurement_bounds)): return -math.inf
        value,error=self.intensity_at(y,theta,eta,provider)
        normalization,outer_error=self._integral(lambda *obs:self.intensity_at(np.array(obs),theta,eta,provider)[0],self.measurement_bounds)
        # Nested quadrature's reported outer error excludes inner integration
        # error. Use the requested absolute budget as an operational estimate;
        # QUADPACK error estimates are not certified confidence bounds.
        volume=math.prod(b-a for a,b in self.measurement_bounds)
        if not math.isfinite(volume): raise NumericalUnresolved("finite selected domain required for nested error estimate")
        total_error=outer_error+volume*self.absolute_error
        if normalization<=total_error or value<=error:
            if value==0 and error==0: return -math.inf
            raise NumericalUnresolved("density or selection normalization unresolved")
        return math.log(value)-math.log(normalization)


def build_cf4_law(product,selection,calibration,physical_provider=None):
    pid=product.get("product_id","CF4")
    if selection is None or calibration is None:
        return UnavailableLaw(pid,"INPUT_UNAVAILABLE",("selection/conditioning or calibration law absent",))
    if isinstance(selection.get("latent_block"),SelectedLatentBlock):
        block=selection["latent_block"]
        required=("observed","measurement_ids","parameter_names","parameter_units","mean","domain_id","domain_contains","source_id")
        if any(k not in product for k in required): return UnavailableLaw(pid,"INPUT_UNAVAILABLE",("raw latent product/model slots missing",))
        specification={"source_ids":[product["source_id"],block.source_id],"selection_law":"NORMALIZED_SELECTED_JOINT_LATENT_BLOCK",
            "covariance_source":calibration["source_id"],"mean_definition":product.get("mean_id","physical_distance"),
            "normalized_density_definition":"integral lambda(xi|theta,Z) p(y|xi,theta,eta,Z) S(y) dxi / integral_selected_joint_y",
            "conditioning":"fixed joint block count and latent field Z; shared eta once"}
        def bind(provider):
            scope=ScopeKey(pid,content_id(specification),provider.provider_id,(product["source_id"],),CONVENTIONS,VERSION,
                "latent_selected_acceptance",content_id({"selection":selection["selection_id"],"calibration":calibration["source_id"]}))
            return JointObservationLaw(scope,product["observed"],tuple(product["measurement_ids"]),tuple(product["parameter_names"]),
                tuple(product["parameter_units"]),lambda t,e:product["mean"](t,e,provider),None,specification,
                product["domain_id"],product["domain_contains"],conditioning_target="SELECTED_JOINT_BLOCK_GIVEN_LATENT_FIELD_AND_COUNT",
                approximation="NUMERICALLY_NORMALIZED_LATENT_LAW_WITH_QUADRATURE_ERROR",transfer_source=provider.provider_id,
                log_density=lambda t,e:block.loglik(product["observed"],t,e,provider))
        factory=ObservationLawFactory(pid+":raw_distance",tuple(product["measurement_ids"]),("distance",),specification,bind)
        return factory if physical_provider is None else factory.bind(physical_provider)
    inputs=product.get("operator_inputs")
    if not isinstance(inputs,Cf4OperatorInputs):
        return UnavailableLaw(pid,"INPUT_UNAVAILABLE",("ordered affine rows and full covariance are absent",))
    if calibration.get("sampling_law")!="KNOWN_GAUSSIAN_CONDITIONAL":
        return UnavailableLaw(pid,"SCENARIO_ONLY",("conditional covariance/measurement sampling law not justified",))
    ids=tuple(str(x) for x in inputs.group_ids)
    if len(ids)!=len(set(ids)) or tuple(str(x) for x in inputs.covariance_group_ids)!=ids:
        raise ValueError("CF4 full covariance row/group order mismatch")
    selected=tuple(str(x) for x in inputs.selected_group_ids)
    if tuple(selection["ordered_group_ids"])!=selected or not set(selected)<=set(ids): raise ValueError("selection order mismatch")
    position={value:i for i,value in enumerate(ids)}
    index=np.array([position[i] for i in selected],dtype=int)
    c=decompose_covariance(inputs.covariance_km2_s2).covariance
    if c.shape!=(len(ids),len(ids)): raise ValueError("full original CF4 covariance required")
    c=c[np.ix_(index,index)]
    directions=galactic_unit_vectors(inputs.galactic_longitude_deg,inputs.galactic_latitude_deg)
    design=build_cf4_affine_design(directions,inputs.distance_mpc)[index]
    y=finite_array(inputs.cmb_velocity_km_s,shape=(len(ids),))[index]
    spec={"source_ids":[product["source_id"],calibration["source_id"]],"selection_law":selection["selection_id"],
        "covariance_source":calibration["covariance_source"],"mean_definition":"P exact fixed-distance 9-column affine radial design",
        "design":design,"covariance":c,"row_ids":selected,"conditioning":"observed directions/distances and fixed selection",
        "parameter_names":CF4_PARAMETERS,"frame":"GALACTIC_CMB_VELOCITY","units":CF4_UNITS}
    scope=ScopeKey(pid,content_id(spec),"CF4_CONDITIONAL_AFFINE",(product["source_id"],),CONVENTIONS,VERSION,
        "gaussian_acceptance",content_id({"alpha":.05,"design":"P_AFFINE_9","selection":selection["selection_id"]}))
    return JointObservationLaw(scope,y,tuple(f"{pid}:group:{i}" for i in selected),CF4_PARAMETERS,CF4_UNITS,
        lambda t,e:design@finite_array(t,shape=(9,)),c,spec,"CF4_AFFINE_R9",lambda t,e:np.asarray(t).shape==(9,),
        jacobian_theta=lambda t,e:design,jacobian_eta=lambda t,e:np.empty((len(y),0)),
        conditioning_target="VELOCITY_GIVEN_FIXED_DISTANCE_DIRECTION_SELECTION",approximation="KNOWN_GAUSSIAN_CONDITIONAL_AFFINE_MODEL")
