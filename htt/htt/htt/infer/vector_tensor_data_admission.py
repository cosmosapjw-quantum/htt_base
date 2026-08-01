"""HTT read-only consumer for future separately authorized data pilots."""

from __future__ import annotations

from common.vector_tensor_data_admission import (
    DataAdmissionError,
    DataAdmissionReport,
    NO_ADMITTED_DATA_PILOT,
)


def future_pilot_candidate_ids(
    report: DataAdmissionReport,
) -> tuple[str, ...]:
    """Return admitted IDs without executing or constructing an inference."""

    if type(report) is not DataAdmissionReport:
        raise TypeError("report must be exact DataAdmissionReport")
    report.as_payload()
    return report.admitted_candidate_ids


def require_future_pilot_eligibility(
    report: DataAdmissionReport,
) -> tuple[str, ...]:
    """Fail if no input is admitted; authorization remains a separate step."""

    candidate_ids = future_pilot_candidate_ids(report)
    if not candidate_ids:
        raise DataAdmissionError(NO_ADMITTED_DATA_PILOT)
    if not report.separate_execution_authorization_present:
        raise DataAdmissionError(
            "ADMITTED_INPUTS_AWAITING_EXECUTION_AUTHORIZATION"
        )
    return candidate_ids


__all__ = [
    "future_pilot_candidate_ids",
    "require_future_pilot_eligibility",
]
