"""MIO report-card surfaces for diagnostic x/Q/Pi/F/G bookkeeping."""
from __future__ import annotations

from .departure_report import (
    DepartureReport,
    DepartureReportSection,
    build_departure_report,
)

__all__ = [
    "DepartureReport",
    "DepartureReportSection",
    "build_departure_report",
]
