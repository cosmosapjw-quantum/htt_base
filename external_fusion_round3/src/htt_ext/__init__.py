"""External-fusion research adapters and low-ell shell-pole reference tools.

The package is deliberately lightweight.  Its core reference suite depends only on
NumPy and SciPy.  Third-party cosmology packages are optional plugins and must be
validated through explicit receipts before any scientific use.
"""

from .types import PoleDefinition, SourceModel, ShellGrid

__all__ = ["PoleDefinition", "SourceModel", "ShellGrid"]
__version__ = "0.1.0"
