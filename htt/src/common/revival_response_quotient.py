"""PR-219: pre-solver response quotient and non-identification atlas (extends PR-127).

Family labels are the quotient classes of a DECLARED observable response: two
families with identical response rows are non-identified under that observable
set. Adding an observable row refines the quotient and raises the rank; the
"reopening requirement" is the observable direction that separates a merged
class. A zero response COLUMN is an unobserved channel, never a physical no-go;
equivalent families are one class, never ranked as separate evidence rows.
"""
from __future__ import annotations
import numpy as np

LABELS = ("BI", "BV", "BVIIh", "FLRW_tilt")
# scalar response (Sigma2, W2, Omega_tilt, DeltaOmega_k) columns
SCALAR = np.array([[1, 0, 1, 0], [1, 0, 1, 0], [1, 0, 1, 0], [0, 0, 1, 0]], float)
# enlarged response adds transverse-curvature + vorticity observable columns
ENLARGED = np.array([[1, 0, 1, 0], [1, 0, 1, 1], [1, 1, 1, 1], [0, 0, 1, 0]], float)


def quotient(labels, rows, atol=1e-12):
    """Group labels by identical response rows (the quotient classes)."""
    rows = np.asarray(rows, float)
    unused = list(range(len(labels)))
    out = []
    while unused:
        i = unused.pop(0)
        cls = [labels[i]]
        keep = []
        for j in unused:
            if np.allclose(rows[i], rows[j], atol=atol, rtol=0):
                cls.append(labels[j])
            else:
                keep.append(j)
        unused = keep
        out.append(tuple(cls))
    return tuple(out)


def quotient_via_nullspace(labels, rows, atol=1e-9):
    """P2 second lineage: two families are equivalent iff their row difference
    lies in the zero subspace (norm ~ 0)."""
    rows = np.asarray(rows, float)
    n = len(labels)
    parent = list(range(n))

    def find(a):
        while parent[a] != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a
    for i in range(n):
        for j in range(i + 1, n):
            if np.linalg.norm(rows[i] - rows[j]) < atol:
                parent[find(i)] = find(j)
    groups = {}
    for i in range(n):
        groups.setdefault(find(i), []).append(labels[i])
    return tuple(tuple(sorted(v, key=labels.index)) for v in groups.values())


def rank_lattice():
    """Rank as observables are added: scalar -> +transverse -> enlarged."""
    scalar_rank = int(np.linalg.matrix_rank(SCALAR))
    plus_transverse = int(np.linalg.matrix_rank(np.vstack([SCALAR, [0, 1, 0, 0]])))
    enlarged_rank = int(np.linalg.matrix_rank(ENLARGED))
    return [scalar_rank, plus_transverse, enlarged_rank]


def reopening_requirement():
    """Which observable set separates the scalar-merged {BI,BV,BVIIh} class."""
    scalar_q = quotient(LABELS, SCALAR)
    enlarged_q = quotient(LABELS, ENLARGED)
    merged = [c for c in scalar_q if len(c) > 1]
    return {"scalar_quotient": scalar_q, "enlarged_quotient": enlarged_q,
            "merged_classes": merged,
            "reopened_to_singletons": all(len(c) == 1 for c in enlarged_q),
            "added_observables": ["transverse_curvature", "vorticity"]}


def zero_column_is_not_a_no_go():
    """A zero response column (e.g. W2 in the scalar set) means unobserved, not
    physically forbidden -- adding a probe can reopen it."""
    scalar_w2_col = SCALAR[:, 1]
    enlarged_w2_col = ENLARGED[:, 1]
    return {"scalar_w2_all_zero": bool(np.allclose(scalar_w2_col, 0)),
            "enlarged_w2_nonzero": bool(np.any(enlarged_w2_col != 0)),
            "interpretation": "zero column is unobserved, reopened by a new probe, not a no-go"}
