"""Exact vector and 2-axis covariance row selection with persisted source-key maps.

Phase C of HTT-R38 Observational Convergence.
Enforces identical row selection on data vectors and both covariance axes,
verifies source-ID uniqueness, persists SHA-256 row-order manifests,
and checks positive-definiteness of the subsetted block.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Sequence, Any
import numpy as np

from common.covariance_validator import (
    validate_covariance,
    CovarianceAudit,
    CovarianceValidationError,
)

class RowSelectionError(ValueError):
    """Base exception for row selection and alignment errors."""
    pass

class DuplicateSourceIdError(RowSelectionError):
    """Raised when duplicate source IDs are present under strict uniqueness policy."""
    pass

class SubsettingMismatchError(RowSelectionError):
    """Raised when data vector, covariance axes, or source IDs have mismatched dimensions."""
    pass


@dataclass(frozen=True)
class RowSelectionResult:
    """Result container for exact row selection."""
    selected_indices: np.ndarray
    selected_vector: np.ndarray
    selected_covariance: np.ndarray
    cholesky_factor: np.ndarray
    covariance_audit: CovarianceAudit
    row_key_sha256: str
    original_count: int
    selected_count: int
    selected_ids: tuple[Any, ...]


class ExactRowSelector:
    """Rigorous 2-axis covariance and vector row selector.
    
    Parameters
    ----------
    source_ids : Sequence
        Stable identifiers for each row (e.g. galaxy PGC ID, SN CID, quasar ID).
    data_vector : np.ndarray
        1D or 2D observational vector of length N.
    covariance : np.ndarray
        N x N covariance matrix.
    allow_duplicates : bool
        If False, raises DuplicateSourceIdError if source_ids has duplicates.
    name : str
        Label for diagnostics.
    """
    def __init__(
        self,
        source_ids: Sequence[Any],
        data_vector: np.ndarray,
        covariance: np.ndarray,
        allow_duplicates: bool = False,
        atol: float = 1e-7,
        rtol: float = 1e-8,
        name: str = "row_selector",
    ):
        self.name = name
        self.ids = list(source_ids)
        self.y = np.asarray(data_vector, dtype=np.float64)
        self.C = np.asarray(covariance, dtype=np.float64)
        self.n = len(self.ids)
        self.atol = atol
        self.rtol = rtol
        
        # Verify dimension matching
        if self.y.shape[0] != self.n:
            raise SubsettingMismatchError(
                f"{name}: data_vector length ({self.y.shape[0]}) does not match source_ids count ({self.n})"
            )
        if self.C.ndim != 2 or self.C.shape[0] != self.n or self.C.shape[1] != self.n:
            raise SubsettingMismatchError(
                f"{name}: covariance shape ({self.C.shape}) does not match source_ids count ({self.n})"
            )
            
        # Check duplicate IDs if not allowed
        if not allow_duplicates:
            unique_ids = set(self.ids)
            if len(unique_ids) != self.n:
                num_dup = self.n - len(unique_ids)
                raise DuplicateSourceIdError(
                    f"{name}: found {num_dup} duplicate source IDs under strict uniqueness policy"
                )
                
        # Validate baseline full covariance
        self.C_sym, self.L, self.baseline_audit = validate_covariance(
            self.C, name=f"{name}_full_cov", rtol=self.rtol, atol=self.atol, check_positive_definite=True
        )

    def select_by_mask(
        self,
        mask: np.ndarray | Sequence[bool],
        selection_label: str = "mask_selection",
    ) -> RowSelectionResult:
        """Select subset by boolean mask.
        
        Parameters
        ----------
        mask : array-like of bool
            Boolean array of length N.
        selection_label : str
            Tag for the selection.
            
        Returns
        -------
        RowSelectionResult
            Container with subsetted vector, subsetted covariance, Cholesky factor,
            row-order hash, and audit report.
        """
        mask_arr = np.asarray(mask, dtype=bool)
        if mask_arr.shape != (self.n,):
            raise SubsettingMismatchError(
                f"{self.name}: mask shape {mask_arr.shape} does not match catalog dimension {self.n}"
            )
        indices = np.flatnonzero(mask_arr)
        return self._build_subset(indices, selection_label)

    def select_by_indices(
        self,
        indices: np.ndarray | Sequence[int],
        selection_label: str = "index_selection",
    ) -> RowSelectionResult:
        """Select subset by integer indices."""
        idx_arr = np.asarray(indices, dtype=int)
        if len(idx_arr) == 0:
            raise RowSelectionError(f"{self.name}: cannot select empty subset")
        if np.any(idx_arr < 0) or np.any(idx_arr >= self.n):
            raise IndexError(f"{self.name}: indices out of bounds [0, {self.n - 1}]")
        return self._build_subset(idx_arr, selection_label)

    def select_by_id_list(
        self,
        target_ids: Sequence[Any],
        preserve_target_order: bool = True,
        selection_label: str = "id_selection",
    ) -> RowSelectionResult:
        """Select subset matching a given sequence of source IDs."""
        id_to_idx = {sid: i for i, sid in enumerate(self.ids)}
        missing = [tid for tid in target_ids if tid not in id_to_idx]
        if missing:
            raise KeyError(
                f"{self.name}: {len(missing)} target IDs not found in source catalog (e.g. {missing[:3]})"
            )
        if preserve_target_order:
            indices = np.array([id_to_idx[tid] for tid in target_ids], dtype=int)
        else:
            target_set = set(target_ids)
            indices = np.array([i for i, sid in enumerate(self.ids) if sid in target_set], dtype=int)
        return self._build_subset(indices, selection_label)

    def _build_subset(self, indices: np.ndarray, label: str) -> RowSelectionResult:
        n_sub = len(indices)
        if n_sub == 0:
            raise RowSelectionError(f"{self.name} ({label}): selection resulted in 0 rows")
            
        y_sub = self.y[indices]
        C_sub = self.C_sym[np.ix_(indices, indices)]
        sub_ids = tuple(self.ids[i] for i in indices)
        
        # Compute reproducible row-key hash
        row_key_string = "\n".join(f"{k}|{sid}" for k, sid in enumerate(sub_ids))
        row_key_sha256 = hashlib.sha256(row_key_string.encode("utf-8")).hexdigest()
        
        # Strict validation of subset covariance
        C_sub_sym, L_sub, audit = validate_covariance(
            C_sub, name=f"{self.name}_{label}_subcov", rtol=self.rtol, atol=self.atol, check_positive_definite=True
        )
        
        return RowSelectionResult(
            selected_indices=indices,
            selected_vector=y_sub,
            selected_covariance=C_sub_sym,
            cholesky_factor=L_sub,
            covariance_audit=audit,
            row_key_sha256=row_key_sha256,
            original_count=self.n,
            selected_count=n_sub,
            selected_ids=sub_ids,
        )

