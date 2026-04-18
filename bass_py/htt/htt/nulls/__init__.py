"""HTT nulls subpackage -- structured-null library (5 families).

Modules
-------
common_interface  : NullFamily ABC, NullDataset, FalsePositiveRates
scanning_law      : Spurious dipole from survey scanning law anisotropy
mask_leakage      : Spurious dipole from Galactic mask leakage
clustering        : Three nulls: ClusteringDipoleNull, SelectionResponseNull, SurveyAxisNull

Total: 5 null families from 3 implementation files.
"""

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
    'NullFamily', 'NullDataset', 'NullFamilyResult', 'FalsePositiveRates',
    'ScanningLawNull', 'MaskLeakageNull',
    'ClusteringDipoleNull', 'SelectionResponseNull', 'SurveyAxisNull',
    'NULL_REGISTRY',
]
