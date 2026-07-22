from __future__ import annotations


def require_glass():
    try:
        import glass  # type: ignore
    except ImportError as exc:
        raise RuntimeError("GLASS is not installed; install the Track-I glass profile") from exc
    return glass


def smoke_import() -> dict:
    glass = require_glass()
    return {"module": "glass", "version": getattr(glass, "__version__", "unknown")}
