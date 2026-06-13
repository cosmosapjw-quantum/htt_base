"""HTT nulls subpackage -- legacy scalar nulls plus depth-null gates.

Modules
-------
common_interface  : NullFamily ABC, NullDataset, FalsePositiveRates
axis_nulls        : Directional mock-calibration gates for axis claims
scanning_law      : Spurious dipole from survey scanning law anisotropy
mask_leakage      : Spurious dipole from Galactic mask leakage
clustering        : Three nulls: ClusteringDipoleNull, SelectionResponseNull, SurveyAxisNull
local_boost_depth_null : Depth-resolved local-boost null-bank FPR gate
clustering_dipole_depth : Depth-resolved local-structure clustering null bank

The legacy ``NULL_REGISTRY`` intentionally remains the original five scalar
null families from three implementation files. Depth-null gates are exported as
separate PR-061 APIs and are not inserted into that registry.
"""

from htt.nulls.axis_nulls import (
    AxisMockCalibrationGateDecision,
    AxisMockCalibrationReport,
    AxisMockCalibrationThresholds,
    build_axis_mock_calibration_report,
    evaluate_axis_mock_gate,
)
from htt.nulls.common_interface import NullFamily, NullDataset, NullFamilyResult, FalsePositiveRates
from htt.nulls.clustering_dipole_depth import ClusteringDipoleDepthNull
from htt.nulls.scanning_law import ScanningLawNull
from htt.nulls.mask_leakage import MaskLeakageNull
from htt.nulls.clustering import ClusteringDipoleNull, SelectionResponseNull, SurveyAxisNull
from htt.nulls.local_boost_depth_null import (
    DepthBinSpec,
    DepthNullMockBank,
    DepthNullSample,
    GlobalTiltLocalNullGateDecision,
    LocalBoostDepthNull,
    LocalBoostNullConfig,
    LocalBoostNullFprReport,
    build_local_boost_null_fpr_report,
    evaluate_global_tilt_local_null_gate,
)

NULL_REGISTRY = {
    'scanning_law': ScanningLawNull,
    'mask_leakage': MaskLeakageNull,
    'clustering': ClusteringDipoleNull,
    'selection_response': SelectionResponseNull,
    'survey_axis': SurveyAxisNull,
}

__all__ = [
    'AxisMockCalibrationGateDecision',
    'AxisMockCalibrationReport',
    'AxisMockCalibrationThresholds',
    'ClusteringDipoleDepthNull',
    'DepthBinSpec',
    'DepthNullMockBank',
    'DepthNullSample',
    'GlobalTiltLocalNullGateDecision',
    'LocalBoostDepthNull',
    'LocalBoostNullConfig',
    'LocalBoostNullFprReport',
    'NullFamily', 'NullDataset', 'NullFamilyResult', 'FalsePositiveRates',
    'build_local_boost_null_fpr_report',
    'build_axis_mock_calibration_report', 'evaluate_axis_mock_gate',
    'evaluate_global_tilt_local_null_gate',
    'ScanningLawNull', 'MaskLeakageNull',
    'ClusteringDipoleNull', 'SelectionResponseNull', 'SurveyAxisNull',
    'NULL_REGISTRY',
]
