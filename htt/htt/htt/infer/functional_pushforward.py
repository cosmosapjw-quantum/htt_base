"""HTT-owned finite posterior functional image; legacy scalar reports unchanged."""
from common.typefree_functionals import FiniteJointSource, finite_joint_pushforward


def posterior_functional_image(records, transform, *, weights=None, joint_id,
                               conditioning_domain_id, target_domain_id, definition_id):
    """Retain coupled draws and undefined mass from a supplied finite posterior.

    The caller supplies the already justified posterior/draw weights. This
    function evaluates its finite representation; it neither constructs a
    likelihood nor asserts Monte Carlo convergence or frequentist coverage.
    A missing anchor/reference is retained by the transform as UndefinedValue.
    New signed quantities are not coerced into legacy F in [0,1] or G_F>0.
    """
    source = FiniteJointSource(joint_id, tuple(records), "POSTERIOR",
                               conditioning_domain_id, weights)
    return finite_joint_pushforward(source, transform, definition_id=definition_id,
                                    target_domain_id=target_domain_id)
