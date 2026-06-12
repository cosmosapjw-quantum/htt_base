"""HTT nulls subpackage -- structured-null library (5 families).

Modules
-------
common_interface  : NullFamily ABC, NullDataset, FalsePositiveRates
axis_nulls        : Directional mock-calibration gates for axis claims
scanning_law      : Spurious dipole from survey scanning law anisotropy
mask_leakage      : Spurious dipole from Galactic mask leakage
clustering        : Three nulls: ClusteringDipoleNull, SelectionResponseNull, SurveyAxisNull

Total: 5 null families from 3 implementation files, plus axis calibration gates.
"""

from htt.nulls.axis_nulls import (
    AxisMockCalibrationGateDecision,
    AxisMockCalibrationReport,
    AxisMockCalibrationThresholds,
    build_axis_mock_calibration_report,
    evaluate_axis_mock_gate,
)
from htt.nulls.common_interface import NullFamily, NullDataset, NullFamilyResult, FalsePositiveRates
from htt.nulls.scanning_law import ScanningLawNull
from htt.nulls.mask_leakage import MaskLeakageNull
from htt.nulls.clustering import ClusteringDipoleNull, SelectionResponseNull, SurveyAxisNull

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
    'NullFamily', 'NullDataset', 'NullFamilyResult', 'FalsePositiveRates',
    'build_axis_mock_calibration_report', 'evaluate_axis_mock_gate',
    'ScanningLawNull', 'MaskLeakageNull',
    'ClusteringDipoleNull', 'SelectionResponseNull', 'SurveyAxisNull',
    'NULL_REGISTRY',
]
