"""Optional dependency registry for harness attribution.

This module is COMMON-owned harness metadata. It records whether optional
packages are present and how missing packages should be handled by tests and
reports. Availability is not scientific validation evidence.
"""
from __future__ import annotations

from dataclasses import dataclass
import importlib.util
from typing import Callable, Literal


MissingPolicy = Literal["skip", "documented_blocker"]
DependencyState = Literal[
    "available",
    "missing_skip",
    "missing_documented_blocker",
]


@dataclass(frozen=True)
class OptionalDependency:
    key: str
    import_name: str
    purpose: str
    owner: str
    missing_policy: MissingPolicy
    pytest_marker: str | None = None
    attribution_paths: tuple[str, ...] = ()

    def skip_reason(self) -> str:
        if self.pytest_marker is None:
            raise ValueError(f"{self.key} has no pytest marker skip policy")
        return (
            f"optional dependency '{self.import_name}' not installed; "
            f"install it to run tests marked {self.pytest_marker}"
        )


@dataclass(frozen=True)
class OptionalDependencyStatus:
    key: str
    import_name: str
    available: bool
    status: DependencyState
    missing_policy: MissingPolicy
    pytest_marker: str | None
    purpose: str
    owner: str
    attribution_paths: tuple[str, ...]
    explanation: str


OPTIONAL_DEPENDENCIES: tuple[OptionalDependency, ...] = (
    OptionalDependency(
        key="healpy",
        import_name="healpy",
        purpose="HEALPix map production and alm-to-map regression tests",
        owner="BASS",
        missing_policy="skip",
        pytest_marker="requires_healpy",
        attribution_paths=("htt/bass/forward/test_map_producer.py",),
    ),
    OptionalDependency(
        key="dynesty",
        import_name="dynesty",
        purpose="nested-evidence cross-checks and posterior-adapter exercises",
        owner="HTT",
        missing_policy="skip",
        pytest_marker="requires_dynesty",
        attribution_paths=("htt/bass/inference/test_fb113_bayes_factor_skeleton.py",),
    ),
    OptionalDependency(
        key="astropy",
        import_name="astropy",
        purpose="external data and FITS/coordinate utilities",
        owner="COMMON",
        missing_policy="documented_blocker",
        attribution_paths=(
            "dl_pipeline/scripts/dl_fits_utils.py",
            "dl_pipeline/scripts/extract_htt_data.py",
        ),
    ),
    OptionalDependency(
        key="camb",
        import_name="camb",
        purpose="external FLRW golden-file and regular-adiabatic seed checks",
        owner="BASS",
        missing_policy="documented_blocker",
        attribution_paths=(
            "htt/bass/spectrum/test_flrw_external_camb.py",
            "htt/bass/perturbation/test_fb53_regular_adiabatic_ic_skeleton.py",
        ),
    ),
)

OPTIONAL_DEPENDENCY_MARKERS: dict[str, str] = {
    dependency.pytest_marker: dependency.import_name
    for dependency in OPTIONAL_DEPENDENCIES
    if dependency.pytest_marker is not None
}


def dependency_status(
    dependency: OptionalDependency,
    *,
    finder: Callable[[str], object | None] = importlib.util.find_spec,
) -> OptionalDependencyStatus:
    available = finder(dependency.import_name) is not None
    if available:
        state: DependencyState = "available"
        explanation = "installed in the current Python environment"
    elif dependency.missing_policy == "skip":
        state = "missing_skip"
        explanation = dependency.skip_reason()
    else:
        state = "missing_documented_blocker"
        explanation = (
            f"optional dependency '{dependency.import_name}' not installed; "
            "documented blocker for tests or scripts that require it"
        )
    return OptionalDependencyStatus(
        key=dependency.key,
        import_name=dependency.import_name,
        available=available,
        status=state,
        missing_policy=dependency.missing_policy,
        pytest_marker=dependency.pytest_marker,
        purpose=dependency.purpose,
        owner=dependency.owner,
        attribution_paths=dependency.attribution_paths,
        explanation=explanation,
    )


def dependency_statuses(
    *,
    finder: Callable[[str], object | None] = importlib.util.find_spec,
) -> tuple[OptionalDependencyStatus, ...]:
    return tuple(
        dependency_status(dependency, finder=finder)
        for dependency in OPTIONAL_DEPENDENCIES
    )
