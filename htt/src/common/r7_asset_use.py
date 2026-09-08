"""Product-keyed R7 intake. Existence and scientific eligibility are separate."""
from __future__ import annotations

from dataclasses import dataclass, asdict
from enum import Enum
from pathlib import Path
import csv
import hashlib


class Disposition(str, Enum):
    QUALIFIED_LIKELIHOOD = "QUALIFIED_LIKELIHOOD"
    QUALIFIED_CONDITIONAL_LAW = "QUALIFIED_CONDITIONAL_LAW"
    LAW_FACTORY = "LAW_FACTORY"
    CONTROL_ONLY = "CONTROL_ONLY"
    SCENARIO_ONLY = "SCENARIO_ONLY"
    UNAVAILABLE_PRODUCT_OR_LAW = "UNAVAILABLE_PRODUCT_OR_LAW"
    SKIPPED_BY_USER_SCOPE = "SKIPPED_BY_USER_SCOPE"


# One row per independently usable product, including excluded products.
# Values name existing inventory entries; they do not select a primary by data.
PRODUCTS = {
    "pr3_smica": ("planck_data", "temperature", ("R7-04", "R7-06")),
    "pr3_components": ("planck_pr3_component_controls", "temperature_control", ("R7-06", "R7-21")),
    "ffp10": ("planck_ffp10", "simulation_bank", ("R7-06", "R7-18")),
    "pr4_npipe": (None, "excluded", ("R7-00",)),
    "wmap9": ("wmap_9yr", "temperature_control", ("R7-06", "R7-21")),
    "wmap7_simulation": ("wmap_7yr_e2e_sim", "simulation_control", ("R7-06", "R7-21")),
    "beyondplanck_v2": ("beyondplanck_v2", "posterior_control", ("R7-06", "R7-21")),
    "cosmoglobe_dr1": ("cosmoglobe_dr1", "posterior_control", ("R7-06", "R7-21")),
    "act_dr6_kappa": ("act_dr6_lensing", "lensing_kappa", ("R7-06", "R7-21")),
    "act_dr6_sims": ("act_dr6_lensing_sims", "kappa_simulation", ("R7-06", "R7-21")),
    "cf4_full": ("cf4_full", "distance_velocity", ("R7-07", "R7-14")),
    "cf4_reconstruction": ("cf4", "reconstruction_control", ("R7-07", "R7-21")),
    "cf4pp": ("cf4", "velocity_field_control", ("R7-07", "R7-21")),
    "carrick_2mpp": ("carrick_2mpp", "velocity_field_control", ("R7-07", "R7-21")),
    "coras": ("coras_2mrs", "velocity_field_control", ("R7-07", "R7-21")),
    "lilow": ("lilow_nn_2mrs", "velocity_field_control", ("R7-07", "R7-21")),
    "desi_raw": ("desi", "catalogue", ("R7-08",)),
    "desi_bgs_bright_mocks": ("desi_dr1_mocks", "catalogue_mock_bank", ("R7-08", "R7-18")),
    "desi_compressed": ("desi_dr1_fullshape_bgs_bright_v1.2", "compressed_likelihood", ("R7-08", "R7-21")),
    "union3": ("union3_release-main", "distance_redshift", ("R7-09", "R7-21")),
    "jwst_anchors": ("jwst_anchors", "host_calibration", ("R7-09", "R7-10")),
    "jwst_sn": ("jwst_sn", "host_distance", ("R7-09", "R7-10")),
    "hsc": ("hsc_s19a_y3", "lensing_shear", ("R7-09", "R7-21")),
    "kids": ("hsc_kids", "lensing_shear", ("R7-09", "R7-21")),
    "cosmos_web": ("cosmos_web_dr1", "small_area_catalogue", ("R7-09", "R7-21")),
    "quijote": ("quijote_mfi_dr1", "foreground_control", ("R7-06", "R7-21")),
    "class_observatory": ("class_dr1", "polarization_control", ("R7-06", "R7-21")),
    "compact_carriers": ("compact_products", "derived_carrier", ("R7-02", "R7-06")),
}


@dataclass(frozen=True)
class AssetUseRecord:
    product_key: str
    inventory_locator: str
    product_locator: str | None
    observable_type: str
    disposition: Disposition
    consumers: tuple[str, ...]
    reason: str
    release: str | None = None
    units: str | None = None
    frame: str | None = None
    processing: str | None = None
    row_ids: tuple[str, ...] = ()
    raw_ancestry: tuple[str, ...] = ()
    uncertainty_law: str | None = None
    law_scope: str | None = None
    fallback: str = "PRODUCT_SPECIFIC_CONTROL_OR_UNAVAILABLE"

    def __post_init__(self):
        if not self.product_key or not self.reason:
            raise ValueError("product identity and disposition reason are required")
        if self.disposition in {Disposition.QUALIFIED_LIKELIHOOD,
                                Disposition.QUALIFIED_CONDITIONAL_LAW}:
            if not all((self.law_scope, self.uncertainty_law, self.units, self.frame)):
                raise ValueError("qualified law requires bound scope, law, units and frame")

    def to_dict(self):
        return asdict(self)


def intake_inventory(inventory: str | Path) -> tuple[AssetUseRecord, ...]:
    """Read the existing inventory, without enumerating or hashing its products.

    Product factors remain unqualified until an HTT adapter validates their law.
    The excluded product is handled before any filesystem access to its locator.
    """
    path = Path(inventory)
    with path.open(newline="") as stream:
        rows = {}
        for row in csv.DictReader(stream):
            # Repeated names may identify raw and historical analysis copies.
            # Select the raw source by path role, never by its observed values.
            previous=rows.get(row['name'])
            if previous is None or '/raw/' in row.get('physical_path',''):
                rows[row['name']]=row
    records = []
    for key, (name, kind, consumers) in PRODUCTS.items():
        if key == "pr4_npipe":
            records.append(AssetUseRecord(key, str(path), None, kind,
                Disposition.SKIPPED_BY_USER_SCOPE, consumers, "PR4/NPIPE excluded by owner"))
            continue
        row = rows.get(name)
        locator = row.get("workdir_path") or row.get("physical_path") if row else None
        exists = bool(locator and Path(locator).exists())
        records.append(AssetUseRecord(key, str(path), locator, kind,
            Disposition.CONTROL_ONLY if exists else Disposition.UNAVAILABLE_PRODUCT_OR_LAW,
            consumers, "Product located; sampling/response law requires adapter validation"
            if exists else "No existing locator resolved in the supplied inventory"))
    return tuple(records)


def verify_selected_sources(root: str | Path, bindings: dict) -> dict[str, list[str]]:
    """Verify selected source identity per donor; this does not award capability."""
    failures: dict[str, list[str]] = {}
    for item in bindings["records"]:
        file = Path(root) / item["path"]
        valid = file.is_file() and hashlib.sha256(file.read_bytes()).hexdigest() == item["selected_sha256"]
        if not valid:
            failures.setdefault(item["donor"], []).append(item["path"])
    return failures
