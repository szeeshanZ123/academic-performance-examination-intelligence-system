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
import unittest
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


class TestMLFinalization(unittest.TestCase):
    # ----------------------------------------------------------------------
    # 1. MODEL INTEGRITY & PIPELINE ARCHITECTURE TESTS
    # ----------------------------------------------------------------------

    def test_model_file_exists_and_loads(self):
        """Verify external_marks_model.joblib exists and loads as a Pipeline."""
        self.assertTrue(DEFAULT_MODEL_PATH.exists(), f"Model file missing at {DEFAULT_MODEL_PATH}")
        pipeline = load_model()
        self.assertTrue(hasattr(pipeline, "predict"), "Model object must implement .predict()")
        self.assertIn("preprocessor", pipeline.named_steps, "Pipeline must contain preprocessor")
        self.assertIn("regressor", pipeline.named_steps, "Pipeline must contain regressor")

    def test_data_leakage_protection(self):
        """Ensure prediction feature vector strictly forbids post-exam columns."""
        from ml.model import ALL_FEATURES
        forbidden_columns = ["Total", "Grade", "SGPI", "External", "Academic_Risk"]
        for col in forbidden_columns:
            self.assertNotIn(col, ALL_FEATURES, f"Data leakage detected! Forbidden column '{col}' in features.")
        self.assertEqual(ALL_FEATURES, ["Internal", "Attendance", "Semester", "Subject"])

    # ----------------------------------------------------------------------
    # 2. INPUT VALIDATION TESTS
    # ----------------------------------------------------------------------

    def test_validate_prediction_inputs_valid(self):
        """Valid inputs must pass validation without error."""
        is_valid, msg = validate_prediction_inputs(24, 82, 3, "Python for Data Analytics")
        self.assertTrue(is_valid)
        self.assertEqual(msg, "")

    def test_validate_prediction_inputs_invalid(self):
        """Invalid or out-of-range inputs must fail validation with helpful message."""
        test_cases = [
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
        ]
        for internal, attendance, semester, subject in test_cases:
            is_valid, msg = validate_prediction_inputs(internal, attendance, semester, subject)
            self.assertFalse(is_valid, f"Expected validation failure for: ({internal}, {attendance}, {semester}, {subject})")
            self.assertTrue(len(msg) > 0)

    def test_predict_external_marks_rejects_invalid_inputs(self):
        """Calling predict_external_marks with invalid inputs must raise ValueError."""
        with self.assertRaises(ValueError):
            predict_external_marks(internal_marks=35, attendance=85, semester=3, subject="Data Analytics")

    # ----------------------------------------------------------------------
    # 3. OUTPUT CLAMPING & TOTAL CALCULATION TESTS
    # ----------------------------------------------------------------------

    def test_predicted_external_bounds(self):
        """Predicted external marks must stay strictly within [0.0, 70.0]."""
        pred_high = predict_external_marks(30, 100, 1, "Python Programming")
        self.assertTrue(0.0 <= pred_high <= 70.0)

        pred_low = predict_external_marks(2, 20, 1, "Python Programming")
        self.assertTrue(0.0 <= pred_low <= 70.0)

    def test_predicted_total_bounds(self):
        """Predicted total marks must stay strictly within [0.0, 100.0]."""
        pred_tot = predict_total_marks(25, 90, 2, "Data Structures")
        self.assertTrue(0.0 <= pred_tot <= 100.0)

    def test_performance_classification(self):
        """Check that performance classification maps cleanly."""
        self.assertEqual(classify_predicted_performance(85.0), "Excellent")
        self.assertEqual(classify_predicted_performance(75.0), "Excellent")
        self.assertEqual(classify_predicted_performance(68.0), "Good")
        self.assertEqual(classify_predicted_performance(52.0), "Average")
        self.assertEqual(classify_predicted_performance(38.0), "Needs Improvement")

    def test_predicted_grade(self):
        """Check predicted letter grades."""
        self.assertEqual(calculate_predicted_grade(92.0), "O")
        self.assertEqual(calculate_predicted_grade(82.0), "A+")
        self.assertEqual(calculate_predicted_grade(72.0), "A")
        self.assertEqual(calculate_predicted_grade(62.0), "B+")
        self.assertEqual(calculate_predicted_grade(52.0), "B")
        self.assertEqual(calculate_predicted_grade(42.0), "C")
        self.assertEqual(calculate_predicted_grade(35.0), "F")

    # ----------------------------------------------------------------------
    # 4. SUBJECT-LEVEL PER-ROW FAULT TOLERANCE
    # ----------------------------------------------------------------------

    def test_predict_subject_performance_valid(self):
        """Valid subject data returns complete prediction record with actual distinction."""
        res = predict_subject_performance(
            internal_marks=24,
            attendance=82,
            semester=3,
            subject="Python for Data Analytics",
            actual_external=46,
        )
        self.assertTrue(res["available"])
        self.assertIsNone(res["error_message"])
        self.assertEqual(res["actual_external"], 46.0)
        self.assertTrue(0.0 <= res["predicted_external"] <= 70.0)
        self.assertEqual(res["predicted_total"], round(24.0 + res["predicted_external"], 1))
        self.assertIn(res["performance"], ("Excellent", "Good", "Average", "Needs Improvement"))

    def test_predict_subject_performance_insufficient_data(self):
        """Insufficient or invalid data returns clean unavailable state without crashing."""
        res = predict_subject_performance(
            internal_marks=None,
            attendance=82,
            semester=3,
            subject="Python for Data Analytics",
            actual_external=None,
        )
        self.assertFalse(res["available"])
        self.assertIn("insufficient academic data", res["error_message"].lower())
        self.assertIsNone(res["predicted_external"])
        self.assertIsNone(res["predicted_total"])

    # ----------------------------------------------------------------------
    # 5. MODEL METADATA & EVALUATION SPECS
    # ----------------------------------------------------------------------

    def test_get_model_info_metrics(self):
        """Model information must accurately reflect the trained Pipeline and evaluation."""
        info = get_model_info()
        self.assertEqual(info["model_name"], "Random Forest Regressor")
        self.assertEqual(info["target"], "External")
        self.assertEqual(info["features"], ["Internal", "Attendance", "Semester", "Subject"])
        self.assertEqual(info["model_mae"], 4.72)
        self.assertEqual(info["rmse"], 5.77)
        self.assertEqual(info["r2_score"], 0.71)
        self.assertEqual(info["baseline_mae"], 8.84)
        self.assertEqual(info["improvement_pct"], 46.58)
        self.assertNotIn("71% accurate", info["r2_explanation"].lower())

    # ----------------------------------------------------------------------
    # 6. STUDENT ISOLATION & SEMESTER DIVERSITY (SEMESTERS 1 TO 6)
    # ----------------------------------------------------------------------

    def test_predictions_across_all_semesters(self):
        """Test that students across Semesters 1 to 6 can generate predictions."""
        _, students, _, _, _ = load_data()
        for sem in range(1, 7):
            sem_students = students[students["Semester"] == sem]
            self.assertFalse(sem_students.empty, f"No active students found in Semester {sem}")
            sample_roll = sem_students.iloc[0]["Roll"]

            detail = get_student_detail(sample_roll)
            self.assertIsNotNone(detail)
            self.assertEqual(int(detail["student"]["Semester"]), sem)
            self.assertTrue(len(detail["subjects_list"]) > 0)

            for subj in detail["subjects_list"]:
                pred = predict_subject_performance(
                    internal_marks=subj["internal"],
                    attendance=subj["attendance"],
                    semester=sem,
                    subject=subj["subject"],
                    actual_external=subj.get("external"),
                )
                self.assertTrue(pred["available"])
                self.assertTrue(0.0 <= pred["predicted_external"] <= 70.0)

    def test_predictions_differ_with_different_inputs(self):
        """Predictions should dynamically respond to varying internal marks and attendance."""
        pred_high = predict_external_marks(internal_marks=28, attendance=95, semester=3, subject="Operating Systems")
        pred_low = predict_external_marks(internal_marks=10, attendance=45, semester=3, subject="Operating Systems")
        self.assertNotEqual(pred_high, pred_low)
        self.assertTrue(pred_high > pred_low)

    # ----------------------------------------------------------------------
    # 7. FLASK ROUTE & STUDENT DASHBOARD UI INTEGRATION
    # ----------------------------------------------------------------------

    def test_student_dashboard_renders_ml_section_without_technical_telemetry(self):
        """Authenticated student accessing /student-dashboard must see user-facing predictions only, with no technical ML telemetry."""
        client = app.test_client()
        _, students, _, _, _ = load_data()
        sample_roll = students.iloc[0]["Roll"]

        with client.session_transaction() as sess:
            sess["student_logged_in"] = True
            sess["student_roll"] = sample_roll
            sess["student_name"] = students.iloc[0]["Name"]

        resp = client.get("/student-dashboard")
        self.assertEqual(resp.status_code, 200)
        html = resp.data.decode("utf-8")

        # User-facing prediction elements MUST be present
        self.assertIn("ai-prediction-section", html)
        self.assertIn("AI Performance Prediction", html)
        self.assertIn("Actual External", html)
        self.assertIn("AI Predicted External Marks", html)
        self.assertIn("Predicted Total", html)
        self.assertIn("Performance Status", html)

        # Technical ML evaluation details MUST NOT be displayed anywhere on Student Dashboard
        self.assertNotIn("AI Model Information", html)
        self.assertNotIn("Random Forest Regressor", html)
        self.assertNotIn("OneHotEncoder", html)
        self.assertNotIn("Baseline Improvement", html)
        self.assertNotIn("MAE:", html)
        self.assertNotIn("RMSE:", html)
        self.assertNotIn("R² =", html)
        self.assertNotIn("Academic Result Integrity", html)

    def test_student_profile_renders_technical_ml_section_only_for_admin(self):
        """Admin viewing a student profile can access model evaluation, while student cannot."""
        client = app.test_client()
        _, students, _, _, _ = load_data()
        sample_roll = students.iloc[0]["Roll"]

        # 1. Admin login -> can view technical metrics
        with client.session_transaction() as sess:
            sess["admin_logged_in"] = True
            sess["admin_user"] = "admin"

        resp_admin = client.get(f"/student/{sample_roll}")
        self.assertEqual(resp_admin.status_code, 200)
        html_admin = resp_admin.data.decode("utf-8")

        self.assertIn("ai-prediction-section", html_admin)
        self.assertIn("AI Performance Prediction", html_admin)
        self.assertIn("Random Forest Regressor", html_admin)
        self.assertIn("AI Model Information & Evaluation Metrics (Admin View)", html_admin)
        self.assertIn("R² = 0.71", html_admin)

        # 2. Student login -> sees user-facing predictions only, no technical evaluation
        with client.session_transaction() as sess:
            sess.clear()
            sess["student_logged_in"] = True
            sess["student_roll"] = sample_roll
            sess["student_name"] = students.iloc[0]["Name"]

        resp_student = client.get(f"/student/{sample_roll}")
        self.assertEqual(resp_student.status_code, 200)
        html_student = resp_student.data.decode("utf-8")

        self.assertIn("ai-prediction-section", html_student)
        self.assertIn("AI Performance Prediction", html_student)
        self.assertNotIn("AI Model Information", html_student)
        self.assertNotIn("Random Forest Regressor", html_student)
        self.assertNotIn("R² =", html_student)

    def test_student_cannot_view_other_student_profile(self):
        """Role-based authorization: Student A cannot view Student B's profile."""
        client = app.test_client()
        with client.session_transaction() as sess:
            sess["student_logged_in"] = True
            sess["student_roll"] = "STUDENT_A"

        resp = client.get("/student/STUDENT_B", follow_redirects=False)
        self.assertEqual(resp.status_code, 302)
        self.assertTrue(resp.headers["Location"].endswith("/student-dashboard") or "/student" in resp.headers["Location"])


if __name__ == "__main__":
    unittest.main()
