"""
test_ml_finalization.py

Comprehensive regression and unit tests for Phase 8.2: ML Finalization & Production Integration.
Tests:
1. Model loading, pipeline steps, and leakage protection.
2. Input validation (ranges, types, NaN, missing values).
3. Output bounds and clamping (external 0-70, total 0-100).
4. Actual vs. Predicted marks distinction.
5. Per-subject fault tolerance (partial data does not crash other subjects).
6. Transparent model metadata and technically accurate R² explanations.
7. Student isolation and semester-specific data across Semesters 1 to 6.
8. Flask route integration and UI rendering for student dashboard.
"""

from pathlib import Path
import pytest
from flask import session
import pandas as pd

from app import app
from ml.predictor import (
    load_model,
    predict_external_marks,
    predict_total_marks,
    classify_predicted_performance,
    calculate_predicted_grade,
    predict_subject_performance,
    get_model_info,
    validate_prediction_inputs,
    DEFAULT_MODEL_PATH,
)
from utils.data_loader import load_data, get_student_detail


# ----------------------------------------------------------------------
# 1. MODEL INTEGRITY & PIPELINE ARCHITECTURE TESTS
# ----------------------------------------------------------------------

def test_model_file_exists_and_loads():
    """Verify external_marks_model.joblib exists and loads as a Pipeline."""
    assert DEFAULT_MODEL_PATH.exists(), f"Model file missing at {DEFAULT_MODEL_PATH}"
    pipeline = load_model()
    assert hasattr(pipeline, "predict"), "Model object must implement .predict()"
    assert "preprocessor" in pipeline.named_steps, "Pipeline must contain preprocessor"
    assert "regressor" in pipeline.named_steps, "Pipeline must contain regressor"


def test_data_leakage_protection():
    """Ensure prediction feature vector strictly forbids post-exam columns."""
    from ml.model import ALL_FEATURES
    forbidden_columns = ["Total", "Grade", "SGPI", "External", "Academic_Risk"]
    for col in forbidden_columns:
        assert col not in ALL_FEATURES, f"Data leakage detected! Forbidden column '{col}' in features."
    assert ALL_FEATURES == ["Internal", "Attendance", "Semester", "Subject"]


# ----------------------------------------------------------------------
# 2. INPUT VALIDATION TESTS
# ----------------------------------------------------------------------

def test_validate_prediction_inputs_valid():
    """Valid inputs must pass validation without error."""
    is_valid, msg = validate_prediction_inputs(24, 82, 3, "Python for Data Analytics")
    assert is_valid is True
    assert msg == ""


@pytest.mark.parametrize(
    "internal,attendance,semester,subject",
    [
        (-1, 80, 3, "Math"),          # Internal < 0
        (35, 80, 3, "Math"),          # Internal > 30
        ("invalid", 80, 3, "Math"),   # Non-numeric internal
        (None, 80, 3, "Math"),        # Missing internal
        (20, -5, 3, "Math"),          # Attendance < 0
        (20, 105, 3, "Math"),         # Attendance > 100
        (20, "abc", 3, "Math"),       # Non-numeric attendance
        (20, None, 3, "Math"),        # Missing attendance
        (20, 80, 0, "Math"),          # Semester < 1
        (20, 80, 8, "Math"),          # Semester > 6
        (20, 80, None, "Math"),       # Missing semester
        (20, 80, 3, ""),              # Empty subject
        (20, 80, 3, "   "),           # Whitespace subject
        (20, 80, 3, None),            # Missing subject
        (float("nan"), 80, 3, "Math"),# NaN internal
        (20, float("nan"), 3, "Math"),# NaN attendance
    ],
)
def test_validate_prediction_inputs_invalid(internal, attendance, semester, subject):
    """Invalid or out-of-range inputs must fail validation with helpful message."""
    is_valid, msg = validate_prediction_inputs(internal, attendance, semester, subject)
    assert is_valid is False
    assert len(msg) > 0


def test_predict_external_marks_rejects_invalid_inputs():
    """Calling predict_external_marks with invalid inputs must raise ValueError."""
    with pytest.raises(ValueError):
        predict_external_marks(internal_marks=35, attendance=85, semester=3, subject="Data Analytics")


# ----------------------------------------------------------------------
# 3. OUTPUT CLAMPING & TOTAL CALCULATION TESTS
# ----------------------------------------------------------------------

def test_predicted_external_bounds():
    """Predicted external marks must stay strictly within [0.0, 70.0]."""
    # High marks scenario
    pred_high = predict_external_marks(30, 100, 1, "Python Programming")
    assert 0.0 <= pred_high <= 70.0

    # Low marks scenario
    pred_low = predict_external_marks(2, 20, 1, "Python Programming")
    assert 0.0 <= pred_low <= 70.0


def test_predicted_total_bounds():
    """Predicted total marks must stay strictly within [0.0, 100.0]."""
    pred_tot = predict_total_marks(25, 90, 2, "Data Structures")
    assert 0.0 <= pred_tot <= 100.0


def test_performance_classification():
    """Check that performance classification maps cleanly."""
    assert classify_predicted_performance(85.0) == "Excellent"
    assert classify_predicted_performance(75.0) == "Excellent"
    assert classify_predicted_performance(68.0) == "Good"
    assert classify_predicted_performance(52.0) == "Average"
    assert classify_predicted_performance(38.0) == "Needs Improvement"


def test_predicted_grade():
    """Check predicted letter grades."""
    assert calculate_predicted_grade(92.0) == "O"
    assert calculate_predicted_grade(82.0) == "A+"
    assert calculate_predicted_grade(72.0) == "A"
    assert calculate_predicted_grade(62.0) == "B+"
    assert calculate_predicted_grade(52.0) == "B"
    assert calculate_predicted_grade(42.0) == "C"
    assert calculate_predicted_grade(35.0) == "F"


# ----------------------------------------------------------------------
# 4. SUBJECT-LEVEL PER-ROW FAULT TOLERANCE
# ----------------------------------------------------------------------

def test_predict_subject_performance_valid():
    """Valid subject data returns complete prediction record with actual distinction."""
    res = predict_subject_performance(
        internal_marks=24,
        attendance=82,
        semester=3,
        subject="Python for Data Analytics",
        actual_external=46,
    )
    assert res["available"] is True
    assert res["error_message"] is None
    assert res["actual_external"] == 46.0
    assert 0.0 <= res["predicted_external"] <= 70.0
    assert res["predicted_total"] == round(24.0 + res["predicted_external"], 1)
    assert res["performance"] in ("Excellent", "Good", "Average", "Needs Improvement")


def test_predict_subject_performance_insufficient_data():
    """Insufficient or invalid data returns clean unavailable state without crashing."""
    res = predict_subject_performance(
        internal_marks=None,
        attendance=82,
        semester=3,
        subject="Python for Data Analytics",
        actual_external=None,
    )
    assert res["available"] is False
    assert "insufficient academic data" in res["error_message"].lower()
    assert res["predicted_external"] is None
    assert res["predicted_total"] is None


# ----------------------------------------------------------------------
# 5. MODEL METADATA & EVALUATION SPECS
# ----------------------------------------------------------------------

def test_get_model_info_metrics():
    """Model information must accurately reflect the trained Pipeline and evaluation."""
    info = get_model_info()
    assert info["model_name"] == "Random Forest Regressor"
    assert info["target"] == "External"
    assert info["features"] == ["Internal", "Attendance", "Semester", "Subject"]
    assert info["model_mae"] == 4.72
    assert info["rmse"] == 5.77
    assert info["r2_score"] == 0.71
    assert info["baseline_mae"] == 8.84
    assert info["improvement_pct"] == 46.58
    assert "71% accurate" not in info["r2_explanation"].lower()


# ----------------------------------------------------------------------
# 6. STUDENT ISOLATION & SEMESTER DIVERSITY (SEMESTERS 1 TO 6)
# ----------------------------------------------------------------------

def test_predictions_across_all_semesters():
    """Test that students across Semesters 1 to 6 can generate predictions."""
    _, students, _, _, _ = load_data()
    for sem in range(1, 7):
        sem_students = students[students["Semester"] == sem]
        assert not sem_students.empty, f"No active students found in Semester {sem}"
        sample_roll = sem_students.iloc[0]["Roll"]

        detail = get_student_detail(sample_roll)
        assert detail is not None
        assert int(detail["student"]["Semester"]) == sem
        assert len(detail["subjects_list"]) > 0

        # Verify each subject in current semester
        for subj in detail["subjects_list"]:
            pred = predict_subject_performance(
                internal_marks=subj["internal"],
                attendance=subj["attendance"],
                semester=sem,
                subject=subj["subject"],
                actual_external=subj.get("external"),
            )
            assert pred["available"] is True
            assert 0.0 <= pred["predicted_external"] <= 70.0


def test_predictions_differ_with_different_inputs():
    """Predictions should dynamically respond to varying internal marks and attendance."""
    pred_high = predict_external_marks(internal_marks=28, attendance=95, semester=3, subject="Operating Systems")
    pred_low = predict_external_marks(internal_marks=10, attendance=45, semester=3, subject="Operating Systems")
    assert pred_high != pred_low
    assert pred_high > pred_low


# ----------------------------------------------------------------------
# 7. FLASK ROUTE & STUDENT DASHBOARD UI INTEGRATION
# ----------------------------------------------------------------------

def test_student_dashboard_renders_ml_section():
    """Authenticated student accessing /student-dashboard must see the complete ML section."""
    client = app.test_client()
    _, students, _, _, _ = load_data()
    sample_roll = students.iloc[0]["Roll"]

    with client.session_transaction() as sess:
        sess["student_logged_in"] = True
        sess["student_roll"] = sample_roll
        sess["student_name"] = students.iloc[0]["Name"]

    resp = client.get("/student-dashboard")
    assert resp.status_code == 200
    html = resp.data.decode("utf-8")

    # Check key section elements
    assert "ai-prediction-section" in html
    assert "AI Performance Prediction" in html
    assert "Random Forest Regressor" in html
    assert "Actual External" in html
    assert "AI Predicted External" in html
    assert "Predicted Total" in html
    assert "Academic Result Integrity" in html
    assert "AI Model Information &amp; Evaluation Metrics" in html or "AI Model Information & Evaluation Metrics" in html
    assert "R² = 0.71" in html


def test_student_profile_renders_ml_section_for_admin():
    """Admin viewing a student's profile must see the same robust ML prediction section."""
    client = app.test_client()
    _, students, _, _, _ = load_data()
    sample_roll = students.iloc[0]["Roll"]

    with client.session_transaction() as sess:
        sess["admin_logged_in"] = True
        sess["admin_user"] = "admin"

    resp = client.get(f"/student/{sample_roll}")
    assert resp.status_code == 200
    html = resp.data.decode("utf-8")

    assert "ai-prediction-section" in html
    assert "AI Performance Prediction" in html
    assert "Random Forest Regressor" in html
    assert "Academic Result Integrity" in html


def test_student_cannot_view_other_student_profile():
    """Role-based authorization: Student A cannot view Student B's profile."""
    client = app.test_client()
    with client.session_transaction() as sess:
        sess["student_logged_in"] = True
        sess["student_roll"] = "STUDENT_A"

    resp = client.get("/student/STUDENT_B", follow_redirects=False)
    assert resp.status_code == 302
    assert resp.headers["Location"].endswith("/student-dashboard") or "/student" in resp.headers["Location"]
