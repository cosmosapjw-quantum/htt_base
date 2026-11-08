"""Test suite for typed ObservationOperator contract layer (R41-02).

Validates protocol conformance across all five source-bound observational operators,
fail-closed behaviors on synthetic data, missing files, dimension mismatches,
and positive definiteness of covariance matrices.
"""

import os
import pytest
import numpy as np

from common.observation_operator_contract import (
    ObservationOperator,
    ObservationSourceMetadata,
    PhysicalFunctionalSpec,
    CoordinateFrame,
    EstimatorType,
    ContractViolationError,
    verify_operator_contract,
)
from common.source_bound_pantheon_operator import SourceBoundPantheonOperator, PANTHEON_DATA_PATH
from common.source_bound_quaia_operator import SourceBoundQuaiaDipoleOperator, QUAIA_CAT_PATH
from common.source_bound_nvss_operator import SourceBoundNVSSOperator, NVSS_CAT_PATH
from common.source_bound_gaia_vsh_operator import SourceBoundGaiaVSHOperator, GAIA_NPZ_PATH
from common.source_bound_planck_lowell_operator import SourceBoundPlanckLowEllOperator, PLANCK_OBS_PATH


class DummyValidOperator:
    """Mock operator with valid contracts for unit testing."""
    def __init__(self, data_path: str):
        self._data_path = data_path

    @property
    def metadata(self) -> ObservationSourceMetadata:
        return ObservationSourceMetadata(
            source_id="Test_Probe",
            product_name="Test Product",
            catalog_or_data_path=self._data_path,
            covariance_path=None,
            n_total_objects=100,
            n_selected_objects=100,
            selection_rule="all",
            coordinate_frame=CoordinateFrame.ICRS,
            units="dimensionless",
            estimator_type=EstimatorType.COUNT_DIPOLE_ELLIS_BALDWIN,
            window_or_mask_id="mask_test",
            covariance_id="cov_test",
            verified_sha256="abc123sha",
            is_synthetic=False,
        )

    @property
    def functional_spec(self) -> PhysicalFunctionalSpec:
        return PhysicalFunctionalSpec(
            name="test_functional",
            tensor_rank=1,
            parity="odd",
            so3_representation="1-",
            units="dimensionless",
            parameter_dependence=("beta_MO",),
        )

    def evaluate_model(self, theta_K: np.ndarray, psi=None):
        return 0.0, 0.0

    def evaluate_likelihood(self, theta_K: np.ndarray, psi=None):
        return 0.0, 0.0

    def get_data_vector(self) -> np.ndarray:
        return np.array([1.0, 2.0, 3.0])

    def get_covariance_matrix(self) -> np.ndarray:
        return np.diag([0.1, 0.2, 0.3])


def test_protocol_type_checking():
    """Verify runtime checkable protocol conformance."""
    dummy = DummyValidOperator(__file__)
    assert isinstance(dummy, ObservationOperator)
    assert verify_operator_contract(dummy) is True


def test_fail_closed_synthetic_data():
    """Verify that synthetic data is strictly rejected in production observation paths."""
    meta = ObservationSourceMetadata(
        source_id="Synthetic_Test",
        product_name="Synthetic Product",
        catalog_or_data_path=__file__,
        covariance_path=None,
        n_total_objects=10,
        n_selected_objects=10,
        selection_rule="none",
        coordinate_frame=CoordinateFrame.ICRS,
        units="mag",
        estimator_type=EstimatorType.ANALYTIC_MARGINALIZED_DISTANCE,
        window_or_mask_id="w_test",
        covariance_id="c_test",
        verified_sha256="dummy_hash",
        is_synthetic=True,  # STRICT PROHIBITION
    )
    with pytest.raises(ContractViolationError, match="Synthetic data forbidden in production"):
        meta.fail_closed_check()


def test_fail_closed_missing_file():
    """Verify that non-existent data files trigger ContractViolationError."""
    meta = ObservationSourceMetadata(
        source_id="Missing_Test",
        product_name="Missing Product",
        catalog_or_data_path="/path/that/does/not/exist.dat",
        covariance_path=None,
        n_total_objects=10,
        n_selected_objects=10,
        selection_rule="none",
        coordinate_frame=CoordinateFrame.ICRS,
        units="mag",
        estimator_type=EstimatorType.ANALYTIC_MARGINALIZED_DISTANCE,
        window_or_mask_id="w_test",
        covariance_id="c_test",
        verified_sha256="dummy_hash",
        is_synthetic=False,
    )
    with pytest.raises(ContractViolationError, match="Required primary source file not found"):
        meta.fail_closed_check()


def test_fail_closed_non_positive_definite_covariance():
    """Verify that non-positive definite covariance matrices fail closed."""
    class BadCovOperator(DummyValidOperator):
        def get_covariance_matrix(self) -> np.ndarray:
            return np.diag([1.0, -0.5, 2.0])  # Negative eigenvalue

    bad_op = BadCovOperator(__file__)
    with pytest.raises(ContractViolationError, match="is not positive definite"):
        verify_operator_contract(bad_op)


def test_fail_closed_dimension_mismatch():
    """Verify that dimension mismatches between data and covariance fail closed."""
    class MismatchOperator(DummyValidOperator):
        def get_data_vector(self) -> np.ndarray:
            return np.array([1.0, 2.0])  # len 2 != cov shape (3,3)

    bad_op = MismatchOperator(__file__)
    with pytest.raises(ContractViolationError, match="Dimension mismatch"):
        verify_operator_contract(bad_op)


@pytest.mark.skipif(not os.path.exists(PANTHEON_DATA_PATH), reason="Pantheon+ dataset not found")
def test_pantheon_operator_contract_compliance():
    """Verify Pantheon+ operator strictly complies with ObservationOperator protocol."""
    op = SourceBoundPantheonOperator(verify_sha=False)
    assert isinstance(op, ObservationOperator)
    assert verify_operator_contract(op) is True
    assert op.metadata.source_id == "Pantheon_Plus_SH0ES"
    assert op.metadata.n_selected_objects == 1580


@pytest.mark.skipif(not os.path.exists(QUAIA_CAT_PATH), reason="Quaia catalog not found")
def test_quaia_operator_contract_compliance():
    """Verify Quaia operator strictly complies with ObservationOperator protocol."""
    op = SourceBoundQuaiaDipoleOperator(verify_sha=False)
    assert isinstance(op, ObservationOperator)
    assert verify_operator_contract(op) is True
    assert op.metadata.source_id == "Quaia_DR1_G20.0"
    assert op.metadata.n_selected_objects == 755850


@pytest.mark.skipif(not os.path.exists(NVSS_CAT_PATH), reason="NVSS catalog not found")
def test_nvss_operator_contract_compliance():
    """Verify NVSS operator strictly complies with ObservationOperator protocol."""
    op = SourceBoundNVSSOperator()
    assert isinstance(op, ObservationOperator)
    assert verify_operator_contract(op) is True
    assert op.metadata.source_id == "NVSS_1.4GHz"
    assert op.metadata.n_selected_objects == 270387


@pytest.mark.skipif(not os.path.exists(GAIA_NPZ_PATH), reason="Gaia NPZ dataset not found")
def test_gaia_operator_contract_compliance():
    """Verify Gaia operator strictly complies with ObservationOperator protocol."""
    op = SourceBoundGaiaVSHOperator(verify_sha=False)
    assert isinstance(op, ObservationOperator)
    assert verify_operator_contract(op) is True
    assert op.metadata.source_id == "Gaia_DR3_CRF3_Astrometry"
    assert op.metadata.n_selected_objects == 634233


@pytest.mark.skipif(not os.path.exists(PLANCK_OBS_PATH), reason="Planck observed carrier not found")
def test_planck_operator_contract_compliance():
    """Verify Planck operator strictly complies with ObservationOperator protocol."""
    op = SourceBoundPlanckLowEllOperator(verify_sha=False)
    assert isinstance(op, ObservationOperator)
    assert verify_operator_contract(op) is True
    assert op.metadata.source_id == "Planck_PR4_LowEll_EB"
    assert op.metadata.n_selected_objects == 10
