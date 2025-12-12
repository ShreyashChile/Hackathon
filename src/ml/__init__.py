"""
ML analysis modules for inventory optimization.
"""

from .demand_shift import DemandShiftDetector
from .non_moving import NonMovingDetector
from .segmentation import SKUSegmentation
from .scoring import RiskScorer

__all__ = [
    "DemandShiftDetector",
    "NonMovingDetector",
    "SKUSegmentation",
    "RiskScorer"
]

