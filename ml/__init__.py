"""
Machine Learning Module for Academic Performance and Examination Intelligence System.
Phase 10.1: External Examination Marks Prediction.
"""

from .predictor import (
    predict_external_marks,
    predict_total_marks,
    calculate_predicted_grade,
    classify_predicted_performance,
)
from .model import build_regression_pipeline

__all__ = [
    "predict_external_marks",
    "predict_total_marks",
    "calculate_predicted_grade",
    "classify_predicted_performance",
    "build_regression_pipeline",
]
