"""R9 adapters on the live JointObservationLaw API.

One product's complete law is transformed once. Contrasts are diagnostic;
only Y or (Y0, HY) are returned as HTT laws. No fitted-covariance promotion.
"""
from dataclasses import replace
import numpy as np
from common.depth_path import DepthRepresentation
from common.r9_product import ProductIntake, SharedStateEmbedding
from common.r7_contracts import UnavailableLaw, finite_array, content_id
from .r7_gaussian_law import (JointObservationLaw, require_fixed_known_gaussian,
                             gaussian_acceptance, condition_gaussian)


def validate_intake(law, intake):
    if not isinstance(law, JointObservationLaw) or not isinstance(intake, ProductIntake):
        raise TypeError("bound JointObservationLaw and ProductIntake required")
    law.specification_id
    if (law.measurement_ids != intake.row_ids or tuple(law.specification['source_ids']) != intake.source_ids
            or law.scope.experiment_id != intake.product_id
            or law.specification['selection_law'] != intake.selection):
        raise ValueError("product/source/row/selection law mismatch")
    if intake.covariance_source is None or intake.covariance_row_ids is None or law.covariance is None:
        return UnavailableLaw(intake.product_id, "INPUT_UNAVAILABLE", ("complete ordered covariance unavailable",))
    if law.specification['covariance_source'] != intake.covariance_source:
        raise ValueError("covariance provenance mismatch")
    if intake.law_kind not in {"KNOWN_GAUSSIAN", "RELEASE_CONDITIONAL_GAUSSIAN"}:
        return UnavailableLaw(intake.product_id, "SCENARIO_ONLY", ("fitted/estimated law needs joint calibration",))
    require_fixed_known_gaussian(law)
    conditional = bool(law.specification.get('conditional_confidence_only'))
    if conditional != (intake.law_kind == "RELEASE_CONDITIONAL_GAUSSIAN"):
        raise ValueError("released conditional law cannot be relabelled as unconditional")
    return None


def embed_product(law, intake, embedding):
    unavailable = validate_intake(law, intake)
    if unavailable is not None:
        return unavailable
    if not isinstance(embedding, SharedStateEmbedding):
        raise TypeError("SharedStateEmbedding required")
    if (embedding.frame != intake.frame or embedding.epoch != intake.epoch
            or embedding.local_parameter_names != law.parameter_names
            or embedding.local_parameter_units != law.parameter_units
            or embedding.nuisance_names != law.shared_latent_ids):
        raise ValueError("embedding frame/epoch/parameter/nuisance identity mismatch")
    if law.jacobian_theta is None or (embedding.nuisance_names and law.jacobian_eta is None):
        raise ValueError("actual theta and active nuisance response required")
    def split(x, eta):
        if eta is not None and np.asarray(eta).size:
            raise ValueError("nuisance already belongs to the common state")
        return embedding.split(x)
    def mean(x, eta):
        return law.mean(*split(x, eta))
    def domain(x, eta):
        return law.domain_contains(*split(x, eta))
    def jacobian(x, eta):
        t, e = split(x, eta)
        jt = finite_array(law.jacobian_theta(t, e), shape=(len(law.observed), len(t)))
        je = (finite_array(law.jacobian_eta(t, e), shape=(len(law.observed), len(e)))
              if len(e) else np.empty((len(law.observed), 0)))
        return jt @ embedding.theta_map + je @ embedding.eta_map
    spec = {**law.specification, 'product_intake': intake.identity, 'shared_state_embedding': embedding.identity,
            'original_law': law.specification_id, 'shared_state_roles': embedding.state_roles}
    return replace(law, scope=replace(law.scope, law_id=content_id(spec)), specification=spec,
                   parameter_names=embedding.state_names, parameter_units=embedding.state_units,
                   mean=mean, domain_contains=domain, jacobian_theta=jacobian,
                   jacobian_eta=lambda x, e: np.empty((len(law.observed), 0)), shared_latent_ids=())


def depth_law(law, intake, representation, *, view="INITIAL_AND_CONTRASTS"):
    unavailable = validate_intake(law, intake)
    if unavailable is not None:
        return unavailable
    if not isinstance(representation, DepthRepresentation):
        raise TypeError("typed DepthRepresentation required")
    if representation.feature_ids != law.measurement_ids:
        raise ValueError("depth order differs from original observation")
    if representation.transport_policy != "FIXED_BEFORE_OBSERVATION":
        return UnavailableLaw(intake.product_id, "SCENARIO_ONLY", ("fitted transport needs full repeated pipeline or conditional law",))
    if view not in {"ORIGINAL", "INITIAL_AND_CONTRASTS"}:
        raise ValueError("HTT requires original Y or (Y0, HY); contrasts alone erase level information")
    transform = np.eye(len(law.observed)) if view == "ORIGINAL" else representation.T
    spec = {**law.specification, 'original_law': law.specification_id, 'depth_representation': representation.identity,
            'view': view, 'transform': transform, 'not_an_independent_measurement': True}
    ids = law.measurement_ids if view == "ORIGINAL" else tuple(
        ('initial:' if i < representation.dimensions[0] else 'contrast:') + name
        for i, name in enumerate(law.measurement_ids))
    def mapped_jacobian(fn):
        if fn is None:
            return None
        return lambda t, e: transform @ fn(t, e)
    return replace(law, scope=replace(law.scope, law_id=content_id(spec)), specification=spec,
                   observed=transform @ law.observed, covariance=transform @ law.covariance @ transform.T,
                   measurement_ids=ids, mean=lambda t, e: transform @ law.mean(t, e),
                   jacobian_theta=mapped_jacobian(law.jacobian_theta),
                   jacobian_eta=mapped_jacobian(law.jacobian_eta))


def depth_diagnostic(law, intake, representation, theta, eta=None):
    transformed = depth_law(law, intake, representation)
    if isinstance(transformed, UnavailableLaw):
        return transformed
    h = representation.H
    if not len(h):
        return {'status': 'NO_DEPTH_CONTRASTS', 'probability': None, 'owner': 'MIO', 'independent_likelihood': False}
    residual = h @ (law.observed-law.mean(theta, eta))
    covariance = h @ law.covariance @ h.T
    # Existing support/rank policy; alpha is irrelevant to this unthresholded
    # diagnostic. No new family test or probability is exposed.
    result = gaussian_acceptance(residual, covariance, .05, law.support_tol)
    return {'status': result.numeric_status if result.inside_support else
            ('OUTSIDE_DETERMINISTIC_SUPPORT' if result.numeric_status == 'RESOLVED' else result.numeric_status),
            'owner': 'MIO', 'residual': residual, 'mean': h @ law.mean(theta, eta),
            'covariance': covariance, 'rank': result.rank,
            'quadratic': result.quadratic if result.inside_support else None,
            'probability': None, 'independent_likelihood': False}


def full_past_innovations(law, intake, representation, theta, eta=None):
    transformed = depth_law(law, intake, representation)
    if isinstance(transformed, UnavailableLaw):
        return transformed
    mu = finite_array(law.mean(theta, eta), shape=law.observed.shape)
    original_support = gaussian_acceptance(law.observed-mu, law.covariance, .05, law.support_tol)
    if original_support.numeric_status != 'RESOLVED':
        return UnavailableLaw(intake.product_id, 'NUMERICALLY_UNRESOLVED',
                              ('original joint support/rank unresolved',))
    if not original_support.inside_support:
        raise ValueError('original observation lies outside deterministic support')
    offsets = np.cumsum((0, *representation.dimensions)); result = []
    for j in range(1, len(representation.dimensions)):
        start, end = offsets[j:j+2]
        conditional = condition_gaussian(mu[start:end], mu[:start], law.covariance[start:end, start:end],
                                         law.covariance[start:end, :start], law.covariance[:start, :start], law.observed[:start])
        result.append({'past_blocks': j, 'residual': law.observed[start:end]-conditional.mean,
                       'covariance': conditional.covariance, 'gain': conditional.gain,
                       'status': conditional.numeric_status})
    return tuple(result)
