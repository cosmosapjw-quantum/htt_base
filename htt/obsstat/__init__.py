"""Observer-side statistics and feature-extraction contracts."""

from __future__ import annotations

import sys as _sys

_PACKAGE_ALIASES = ("obsstat", "htt.obsstat")
_THIS_PACKAGE = _sys.modules[__name__]
if __name__ in _PACKAGE_ALIASES:
    for _alias in _PACKAGE_ALIASES:
        _sys.modules.setdefault(_alias, _THIS_PACKAGE)

from .alm_conventions import (
    AlmConvention,
    build_alm_feature,
    canonical_spin2_alm_convention,
    canonical_temperature_alm_convention,
    validate_alm_convention_metadata,
    validate_alm_feature_conventions,
)
from .biposh_features import (
    BiPoSHConventionMetadata,
    BiPoSHFeatureSummary,
    SparseBiPoSHCoefficient,
    build_biposh_feature_payload,
)
from .lowell_poles import (
    AntipodalAxis,
    LowEllPoleAnalysisSpec,
    LowEllPoleEstimate,
    MIN_NUMERICAL_GAP_TOLERANCE,
    PoleDefinition,
    PoleStatus,
    angular_momentum_power_tensor,
    estimate_lowell_pole,
    estimate_lowell_pole_from_power_tensor,
    mean_squared_multipole_alignment,
    scalar_alm_inversion_phase,
    transform_antipodal_axis_o3,
    transform_power_tensor_o3,
)
from .lowell_counterpairs import (
    CounterpairFactor,
    FeatureAvailability,
    InterventionOperator,
    LowEllCounterpairError,
    LowEllInterventionSpec,
    LowEllMorphologyFeaturePacket,
    MatchedCounterpairReport,
    MorphologyFeatureKind,
    ParityRealization,
    RegisteredMorphologyFeature,
    apply_lowell_counterpair_intervention,
    build_lowell_morphology_feature_packet,
    build_matched_counterpair,
    register_morphology_feature,
    revalidate_matched_counterpair,
)
from .shell_alms import draw_correlated_real_shell_alms
from .morphology import (
    DiagnosticMorphologyAxis,
    MorphologyAxisSummary,
    MorphologyNullCalibration,
    summarize_morphology_axes,
)
from .orbit_catalogue_v3 import (
    CatalogueProofStatus,
    OrbitActionGroup,
    OrbitCatalogueV3Error,
    OrbitCatalogueV3Report,
    OrbitCatalogueV3Spec,
    OrbitScalarParity,
    ShearOrbitStratum,
    ShearStabilizer,
    build_orbit_catalogue_v3_spec,
    evaluate_orbit_catalogue_v3,
    revalidate_orbit_catalogue_v3,
)
from .null_ensembles import (
    LookElsewhereBookkeeping,
    NullCalibratedFeature,
    NullEnsembleSpec,
    build_null_ensemble_feature_payload,
    validate_null_feature_payload,
)
from .observable_vector import (
    ObservableVector,
    build_observable_vector,
    obsstat_manifest,
)
from .scalar_lowell import (
    LowEllNullCalibration,
    LowEllScalarSummary,
    compute_cl_from_alm,
    summarize_lowell_scalars,
)
from .template_fit import (
    CovarianceAssumption,
    OrientationScanMetadata,
    TemplateFitDiagnostic,
    fit_template_diagnostic,
)
from .catalogs.cf4 import (
    Cf4Catalog,
    Cf4CatalogMetadata,
    build_cf4_catalog_from_mapping,
    load_cf4_catalog_npz,
)
from .catalogs.cf4_raw import (
    CF4_PR179_DENYLIST,
    CF4_PR179_PRIMARY_COLUMNS,
    Cf4RawGroupCatalog,
    Cf4RawInputError,
    load_authenticated_cf4_raw_groups,
    require_pr179_columns,
    require_pr179_value_access,
)
from .catalogs.redshift_selection import (
    RedshiftSelectionCorrectionSpec,
    apply_redshift_selection_correction,
)
from .catalogs.spectroscopic_dipole import (
    SpectroscopicCatalog,
    SpectroscopicCatalogMetadata,
    SpectroscopicDipoleFeature,
    build_spectroscopic_catalog_from_mapping,
    estimate_data_random_dipole,
    first_moment,
)

for _submodule in (
    "alm_conventions",
    "biposh_features",
    "catalogs",
    "catalogs.cf4",
    "catalogs.cf4_raw",
    "catalogs.redshift_selection",
    "catalogs.spectroscopic_dipole",
    "lowell_counterpairs",
    "lowell_poles",
    "morphology",
    "null_ensembles",
    "observable_vector",
    "orbit_catalogue_v3",
    "scalar_lowell",
    "shell_alms",
    "template_fit",
):
    _loaded = _sys.modules.get(f"{__name__}.{_submodule}")
    if _loaded is not None:
        for _alias in _PACKAGE_ALIASES:
            _sys.modules.setdefault(f"{_alias}.{_submodule}", _loaded)

__all__ = [
    "AlmConvention",
    "AntipodalAxis",
    "BiPoSHConventionMetadata",
    "BiPoSHFeatureSummary",
    "CatalogueProofStatus",
    "Cf4Catalog",
    "Cf4CatalogMetadata",
    "Cf4RawGroupCatalog",
    "Cf4RawInputError",
    "CF4_PR179_DENYLIST",
    "CF4_PR179_PRIMARY_COLUMNS",
    "CounterpairFactor",
    "CovarianceAssumption",
    "DiagnosticMorphologyAxis",
    "FeatureAvailability",
    "InterventionOperator",
    "LowEllCounterpairError",
    "LowEllInterventionSpec",
    "LowEllMorphologyFeaturePacket",
    "LowEllNullCalibration",
    "LowEllPoleAnalysisSpec",
    "LowEllPoleEstimate",
    "LowEllScalarSummary",
    "LookElsewhereBookkeeping",
    "MIN_NUMERICAL_GAP_TOLERANCE",
    "MatchedCounterpairReport",
    "MorphologyAxisSummary",
    "MorphologyFeatureKind",
    "MorphologyNullCalibration",
    "NullCalibratedFeature",
    "NullEnsembleSpec",
    "ObservableVector",
    "OrbitActionGroup",
    "OrbitCatalogueV3Error",
    "OrbitCatalogueV3Report",
    "OrbitCatalogueV3Spec",
    "OrbitScalarParity",
    "OrientationScanMetadata",
    "ParityRealization",
    "PoleDefinition",
    "PoleStatus",
    "RedshiftSelectionCorrectionSpec",
    "RegisteredMorphologyFeature",
    "SparseBiPoSHCoefficient",
    "SpectroscopicCatalog",
    "SpectroscopicCatalogMetadata",
    "SpectroscopicDipoleFeature",
    "ShearOrbitStratum",
    "ShearStabilizer",
    "TemplateFitDiagnostic",
    "apply_redshift_selection_correction",
    "apply_lowell_counterpair_intervention",
    "angular_momentum_power_tensor",
    "build_alm_feature",
    "build_biposh_feature_payload",
    "build_lowell_morphology_feature_packet",
    "build_matched_counterpair",
    "build_cf4_catalog_from_mapping",
    "build_null_ensemble_feature_payload",
    "build_observable_vector",
    "build_orbit_catalogue_v3_spec",
    "evaluate_orbit_catalogue_v3",
    "build_spectroscopic_catalog_from_mapping",
    "compute_cl_from_alm",
    "canonical_spin2_alm_convention",
    "canonical_temperature_alm_convention",
    "fit_template_diagnostic",
    "estimate_data_random_dipole",
    "draw_correlated_real_shell_alms",
    "estimate_lowell_pole",
    "estimate_lowell_pole_from_power_tensor",
    "mean_squared_multipole_alignment",
    "scalar_alm_inversion_phase",
    "first_moment",
    "load_cf4_catalog_npz",
    "load_authenticated_cf4_raw_groups",
    "obsstat_manifest",
    "register_morphology_feature",
    "revalidate_matched_counterpair",
    "revalidate_orbit_catalogue_v3",
    "summarize_morphology_axes",
    "summarize_lowell_scalars",
    "transform_antipodal_axis_o3",
    "transform_power_tensor_o3",
    "validate_alm_convention_metadata",
    "validate_alm_feature_conventions",
    "validate_null_feature_payload",
    "require_pr179_columns",
    "require_pr179_value_access",
]
