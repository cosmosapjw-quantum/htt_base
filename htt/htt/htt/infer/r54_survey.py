"""R54-L04 survey labels and survey-resolved zero-point operators for the CF4 groups.

Survey labels are joined on identifiers only (group_id = PGC of the dominant galaxy, 1PGC in the CF4 tables;
galaxy PGC for the SDSS peculiar-velocity catalogue), never on row order (gate MG-L05).

Owned sources: CF4 table2 (galaxies: PGC, 1PGC, per-method distance moduli), table3 (groups), and the SDSS FP
peculiar-velocity catalogue (PGC per galaxy). The CF4 tables carry no survey column; within the FP family a galaxy is
labelled SDSS when its PGC is in the SDSS FP catalogue and NOT_SDSS otherwise. TF bands, TF source samples and SN
compilations cannot be resolved from owned files and keep one label per family.

The survey step operator (R54-L04 step 4a) fits eta = redshift-bin monopoles + s sign(dec) on one survey; dropping the
monopoles lets a monopole trend with unequal hemisphere depths masquerade as a step (gate MG-L06).
"""
from __future__ import annotations

from typing import Iterable, Mapping

import numpy as np

from htt.htt.infer import r54_distance_estimators as de

# fixed-width columns of J/ApJ/944/94 (CF4) table2.dat and table3.dat (1-based bytes in the ReadMe -> 0-based slices)
TABLE2_COLUMNS = {"PGC": (0, 7), "1PGC": (8, 15), "DMsnIa": (41, 47), "DMtf": (53, 59), "DMfp": (65, 71)}
TABLE3_COLUMNS = {"1PGC": (0, 7)}
FAMILY_SURVEYS = {"FP": ("FP_SDSS", "FP_NOT_SDSS"), "TF": ("TF_ALL",), "SN": ("SN_ALL",), "OTHER": ("OTHER_ALL",)}


def read_fixed_width(lines: Iterable[str], columns: Mapping[str, tuple[int, int]]) -> dict[str, list[str]]:
    out: dict[str, list[str]] = {k: [] for k in columns}
    for line in lines:
        for k, (a, b) in columns.items():
            out[k].append(line[a:b].strip())
    return out


def galaxy_table(lines: Iterable[str]) -> dict[str, np.ndarray]:
    """table2 rows -> PGC, group 1PGC and flags of a measured FP / TF / SN Ia distance modulus."""
    raw = read_fixed_width(lines, TABLE2_COLUMNS)
    return {"pgc": np.array([int(x) for x in raw["PGC"]], np.int64), "group": np.array([int(x) for x in raw["1PGC"]], np.int64),
            "has_fp": np.array([x != "" for x in raw["DMfp"]]), "has_tf": np.array([x != "" for x in raw["DMtf"]]),
            "has_sn": np.array([x != "" for x in raw["DMsnIa"]])}


def survey_labels(group_id: np.ndarray, family: np.ndarray, gal: Mapping[str, np.ndarray], sdss_pgc: np.ndarray) -> np.ndarray:
    """One survey label per group, joined on identifiers.

    FP groups: FP_SDSS if every FP galaxy of the group is in the SDSS FP catalogue, FP_NOT_SDSS if none is, FP_MIXED
    otherwise or when the group has no FP galaxy in table2. Other families keep their family label (<family>_ALL)."""
    group_id = np.asarray(group_id, np.int64)
    family = np.asarray(family)
    if group_id.shape != family.shape or len(set(group_id.tolist())) != group_id.size:
        raise ValueError("group_id must be unique and aligned with family")
    sdss = set(np.asarray(sdss_pgc, np.int64).tolist())
    n_fp, n_sdss = {}, {}
    for pgc, grp, fp in zip(gal["pgc"].tolist(), gal["group"].tolist(), gal["has_fp"].tolist()):
        if fp:
            n_fp[grp] = n_fp.get(grp, 0) + 1
            n_sdss[grp] = n_sdss.get(grp, 0) + (pgc in sdss)
    out = []
    for gid, fam in zip(group_id.tolist(), family.tolist()):
        if fam != "FP":
            if fam not in FAMILY_SURVEYS:
                raise ValueError(f"unknown method family {fam}")
            out.append(FAMILY_SURVEYS[fam][0])
            continue
        k, m = n_fp.get(gid, 0), n_sdss.get(gid, 0)
        out.append("FP_MIXED" if k == 0 or 0 < m < k else ("FP_SDSS" if m == k else "FP_NOT_SDSS"))
    return np.array(out)


def join_coverage(group_id: np.ndarray, table_group_ids: np.ndarray) -> float:
    """Fraction of the catalogue group_id values present in a raw table (acceptance label_join_coverage)."""
    return float(np.isin(np.asarray(group_id, np.int64), np.asarray(table_group_ids, np.int64)).mean())


def pool_small(labels: np.ndarray, family: np.ndarray, in_range: np.ndarray, min_count: int) -> np.ndarray:
    """Surveys with fewer than min_count groups inside the range are pooled into '<family>_REST' (R54-L04 step 3)."""
    labels = np.asarray(labels).astype(object)
    out = labels.copy()
    for lab in np.unique(labels):
        sel = labels == lab
        if int(np.sum(sel & in_range)) < min_count:
            fams = set(np.asarray(family)[sel].tolist())
            if len(fams) != 1:
                raise ValueError(f"survey {lab} spans several families")
            out[sel] = f"{fams.pop()}_REST"
    return out.astype(str)


def survey_step_operator(z: np.ndarray, nvec: np.ndarray, tau2: np.ndarray, select: np.ndarray, z_bins: tuple[float, ...]) -> np.ndarray:
    """Row operator of the hemisphere step s in eta = sum_b h_b 1[z in bin b] + s sign(dec), weights 1/tau2 on ``select``;
    only redshift bins occupied by the selection carry a monopole."""
    z = np.asarray(z, float)
    zbin = np.digitize(z, z_bins[1:-1])
    sel = np.asarray(select, bool)
    mono = np.column_stack([(zbin == b).astype(float) for b in range(len(z_bins) - 1) if np.any(sel & (zbin == b))])
    step = np.where(np.asarray(nvec, float)[:, 2] >= 0.0, 1.0, -1.0)
    design = np.column_stack((mono, step))
    return de.wls_operator(design, sel / np.asarray(tau2, float))[mono.shape[1]]


def survey_offset_operator(z: np.ndarray, tau2: np.ndarray, labels: np.ndarray, family_sel: np.ndarray, reference: str,
                           others: list[str], z_bins: tuple[float, ...]) -> np.ndarray:
    """Rows: offsets of each survey in ``others`` relative to ``reference`` in eta = redshift-bin monopoles + offsets (one family)."""
    z = np.asarray(z, float)
    zbin = np.digitize(z, z_bins[1:-1])
    fsel = np.asarray(family_sel, bool)
    mono = np.column_stack([(zbin == b).astype(float) for b in range(len(z_bins) - 1) if np.any(fsel & (zbin == b))])
    ind = np.column_stack([(np.asarray(labels) == s).astype(float) for s in others])
    if reference in others:
        raise ValueError("the reference survey has no offset column")
    design = np.column_stack((mono, ind))
    return de.wls_operator(design, np.asarray(family_sel, float) / np.asarray(tau2, float))[mono.shape[1]:]
