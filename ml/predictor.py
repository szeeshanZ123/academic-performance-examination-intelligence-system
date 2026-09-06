"""
ml/predictor.py

Provides reusable inference functions for predicting External Examination Marks,
Total Marks, and corresponding expected Grade for a student.

Phase 10.1: Academic Performance and Examination Intelligence System.
"""

from pathlib import Path
from typing import Dict, Union, Optional
import joblib
import numpy as np
import pandas as pd

# Default model location
DEFAULT_MODEL_PATH = Path(__file__).resolve().parent / "models" / "external_marks_model.joblib"

# Cache loaded model in memory for efficiency
_CACHED_MODEL = None


def load_model(model_path: Optional[Union[str, Path]] = None):
    """
    Loads the trained scikit-learn Pipeline from disk.
    Caches the model instance in memory.
    """
    global _CACHED_MODEL
    target_path = Path(model_path) if model_path else DEFAULT_MODEL_PATH

    if _CACHED_MODEL is not None and model_path is None:
        return _CACHED_MODEL

    if not target_path.exists():
        raise FileNotFoundError(
            f"Trained model file not found at: {target_path}\n"
            f"Please run 'python ml/train_model.py' to train and save the model first."
        )

    model = joblib.load(target_path)
    if model_path is None:
        _CACHED_MODEL = model
    return model


def predict_external_marks(
    internal_marks: float,
    attendance: float,
    semester: int,
    subject: str,
    model_path: Optional[Union[str, Path]] = None,
) -> float:
    """
    Predicts expected External Examination Marks using the trained ML model.

    Parameters:
        internal_marks (float): Student's internal score (e.g., out of 30 or 20).
        attendance (float): Student's subject attendance percentage (0 - 100).
        semester (int): Academic semester (e.g., 1, 2, 3, etc.).
        subject (str): Subject name.
        model_path (str or Path, optional): Custom path to joblib model file.

    Returns:
        float: Expected external marks, rounded to 2 decimal places.
    """
    model = load_model(model_path)

    # Construct feature DataFrame with exact column names expected by pipeline
    input_df = pd.DataFrame(
        [
            {
                "Internal": float(internal_marks),
                "Attendance": float(attendance),
                "Semester": int(semester),
                "Subject": str(subject).strip(),
            }
        ]
    )

    prediction = model.predict(input_df)[0]

    # Clip to realistic academic bounds for external exams (0 to 70 marks)
    prediction = min(70.0, max(0.0, float(prediction)))
    return round(prediction, 2)


def classify_predicted_performance(predicted_total: float) -> str:
    """
    Classifies student performance based on predicted total marks:
      >= 75: 'Excellent'
      >= 60: 'Good'
      >= 50: 'Average'
      <  50: 'Needs Improvement'

    Parameters:
        predicted_total (float): Internal + Predicted External marks.

    Returns:
        str: Performance category label.
    """
    if predicted_total >= 75.0:
        return "Excellent"
    elif predicted_total >= 60.0:
        return "Good"
    elif predicted_total >= 50.0:
        return "Average"
    else:
        return "Needs Improvement"


def predict_total_marks(
    internal_marks: float,
    attendance: float,
    semester: int,
    subject: str,
    model_path: Optional[Union[str, Path]] = None,
) -> float:
    """
    Calculates Predicted Total Marks = Actual Internal Marks + Predicted External Marks.

    Parameters:
        internal_marks (float): Actual Internal marks.
        attendance (float): Attendance percentage.
        semester (int): Academic semester.
        subject (str): Subject name.
        model_path (str or Path, optional): Custom path to joblib model file.

    Returns:
        float: Predicted total marks rounded to 2 decimal places.
    """
    predicted_external = predict_external_marks(
        internal_marks=internal_marks,
        attendance=attendance,
        semester=semester,
        subject=subject,
        model_path=model_path,
    )
    predicted_total = round(float(internal_marks) + predicted_external, 2)
    return predicted_total


def calculate_predicted_grade(total_marks: float) -> str:
    """
    Maps total score to the project's existing grade distribution:
      >= 90 : 'O'
      >= 80 : 'A+'
      >= 70 : 'A'
      >= 60 : 'B+'
      >= 50 : 'B'
      >= 40 : 'C'
      <  40 : 'F'

    Parameters:
        total_marks (float): Total marks out of 100.

    Returns:
        str: Letter grade category.
    """
    if total_marks >= 90:
        return "O"
    elif total_marks >= 80:
        return "A+"
    elif total_marks >= 70:
        return "A"
    elif total_marks >= 60:
        return "B+"
    elif total_marks >= 50:
        return "B"
    elif total_marks >= 40:
        return "C"
    else:
        return "F"


def get_full_prediction(
    internal_marks: float,
    attendance: float,
    semester: int,
    subject: str,
) -> Dict[str, Union[float, str, int]]:
    """
    Convenience function returning complete prediction breakdown.

    Returns:
        dict: Breakdown with input features, predicted external, total, and grade.
    """
    pred_ext = predict_external_marks(internal_marks, attendance, semester, subject)
    pred_tot = round(float(internal_marks) + pred_ext, 2)
    pred_grade = calculate_predicted_grade(pred_tot)

    return {
        "semester": semester,
        "subject": subject,
        "internal_marks": internal_marks,
        "attendance": attendance,
        "predicted_external_marks": pred_ext,
        "predicted_total_marks": pred_tot,
        "predicted_grade": pred_grade,
    }


if __name__ == "__main__":
    print("=" * 60)
    print("TESTING ML PREDICTOR MODULE")
    print("=" * 60)

    # Test cases
    test_cases = [
        {"internal": 18, "attendance": 82, "semester": 2, "subject": "Data Structures"},
        {"internal": 28, "attendance": 95, "semester": 1, "subject": "Python Programming"},
        {"internal": 12, "attendance": 65, "semester": 3, "subject": "Operating Systems"},
    ]

    for idx, tc in enumerate(test_cases, 1):
        try:
            result = get_full_prediction(
                internal_marks=tc["internal"],
                attendance=tc["attendance"],
                semester=tc["semester"],
                subject=tc["subject"],
            )
            print(f"\nTest Case #{idx}:")
            print(f"  Input  -> Semester: {result['semester']}, Subject: '{result['subject']}'")
            print(f"  Input  -> Internal: {result['internal_marks']}, Attendance: {result['attendance']}%")
            print(f"  Output -> Predicted External Marks: {result['predicted_external_marks']}")
            print(f"  Output -> Predicted Total Marks   : {result['predicted_total_marks']}")
            print(f"  Output -> Predicted Grade         : {result['predicted_grade']}")
        except Exception as e:
            print(f"Test Case #{idx} Failed: {e}")

    print("\n" + "=" * 60)
