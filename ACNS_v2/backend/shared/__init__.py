"""
shared/ — Code shared by more than one feature.

Everything here must stay feature-agnostic: no imports from features/.
"""

from . import utils

__all__ = ["utils"]
