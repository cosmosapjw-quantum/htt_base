"""Fisher-information diagnostics for covariance compression."""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from numpy.typing import ArrayLike, NDArray


def _derivative_stack(derivatives: ArrayLike) -> NDArray[np.float64]:
    array = np.asarray(derivatives, dtype=float)
    if array.ndim == 2:
        array = array[None, :, :]
    if array.ndim != 3 or array.shape[1] != array.shape[2]:
        raise ValueError("derivatives must be square matrices")
    if not np.all(np.isfinite(array)):
        raise ValueError("derivatives must contain finite values")
    return np.asarray([(item + item.T) / 2.0 for item in array], dtype=float)


def _covariance_fisher_at_identity(derivatives: NDArray[np.float64]) -> NDArray[np.float64]:
    count = derivatives.shape[0]
    fisher = np.empty((count, count), dtype=float)
    for i in range(count):
        for j in range(count):
            fisher[i, j] = 0.5 * float(np.trace(derivatives[i] @ derivatives[j]))
    return fisher


@dataclass(frozen=True)
class FisherCompressionAudit:
    """Diagnostic comparison of full covariance Fisher and diagonal compression."""

    full_fisher: NDArray[np.float64]
    diagonal_fisher: NDArray[np.float64]
    information_loss: NDArray[np.float64]
    diagonal_compression_loses_information: bool
    owner: str = "HTT"
    implementation_scope: str = "htt"
    claim_tier: str = "diagnostic_only"
    transfer_source: str = "none"
    native_solver_result: bool = False

    def as_payload(self) -> dict[str, object]:
        return {
            "owner": self.owner,
            "implementation_scope": self.implementation_scope,
            "claim_tier": self.claim_tier,
            "transfer_source": self.transfer_source,
            "native_solver_result": self.native_solver_result,
            "full_fisher": self.full_fisher.tolist(),
            "diagonal_fisher": self.diagonal_fisher.tolist(),
            "information_loss": self.information_loss.tolist(),
            "diagonal_compression_loses_information": (
                self.diagonal_compression_loses_information
            ),
            "definition": "F_ij = 1/2 Tr(D_i D_j) at C=I",
            "caveats": [
                "diagnostic covariance-compression audit only",
                "not evidence",
                "not native solver validation",
                "not family or geometry evidence",
            ],
        }


def gaussian_covariance_fisher_full_and_diag(
    derivatives: ArrayLike,
    tolerance: float = 1.0e-12,
) -> FisherCompressionAudit:
    """Return full and diagonal Fisher matrices for covariance derivatives."""

    stack = _derivative_stack(derivatives)
    full = _covariance_fisher_at_identity(stack)
    diag_stack = np.asarray([np.diag(np.diag(item)) for item in stack], dtype=float)
    diag = _covariance_fisher_at_identity(diag_stack)
    loss = (full - diag + (full - diag).T) / 2.0
    loses = bool(np.any(np.linalg.eigvalsh(loss) > float(tolerance)))
    return FisherCompressionAudit(
        full_fisher=full,
        diagonal_fisher=diag,
        information_loss=loss,
        diagonal_compression_loses_information=loses,
    )


__all__ = ["FisherCompressionAudit", "gaussian_covariance_fisher_full_and_diag"]
