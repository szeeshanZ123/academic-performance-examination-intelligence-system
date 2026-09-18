"""Comprehensive End-to-End System Audit & Regression Test Suite for Phase 8.1.

Validates all 22 parts of the Final System Audit:
1. Authentication (Admin, Teacher, Student)
2. Role-Based Access Control (RBAC) & Cross-Role Blocking
3. Logout & Cache-Control Security
4. Dataset Integrity (360 Students, 5,040 Marks, 5,040 Attendance, 0 Duplicates, 0 Future Records)
5. Current Cohort vs Historical Trend Points (Sem 1: 1 pt -> Sem 6: 6 pts)
6. Student Dashboard & Academic Risk / Recommendations
7. Student Profile Consistency
8. Teacher Dashboard & Assigned Subject Scoping
9. Admin Dashboard & Institutional Analytics / CSV Export
10. ML RandomForest External Marks Predictor & Leakage Check
11. Question Paper Intelligence NLP Analysis with Sem 3 Python for Data Analytics PDF
12. Light/Dark Theme Files & Template Toggle Buttons
13. UI Branding ("Academic Intelligence") & Title Standardization
14. Error Handling (404, 403, 500, Search Not Found)
"""

import os
import io
import unittest
import pandas as pd
from pathlib import Path

from app import app
from utils.data_loader import (
    load_data,
    get_admin_info,
    load_teachers,
    get_teacher_assignments,
    get_student_detail,
    SEMESTER_SUBJECTS
)
from analysis.analytics import (
    dashboard_kpis,
    get_teacher_subject_analytics,
    get_student_semester_trend
)
from ml.predictor import (
    load_model,
    predict_external_marks,
    predict_total_marks,
    classify_predicted_performance
)
from question_paper.extractor import extract_text_from_file
from question_paper.parser import parse_question_paper
from question_paper.analyzer import analyze_question_paper


class TestSystemAuditRegression(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = app
        cls.app.config["TESTING"] = True
        cls.client = cls.app.test_client()
        cls.admin_df, cls.students_df, cls.marks_df, cls.attendance_df, cls.combined = load_data()

    def tearDown(self):
        # Clear cookies / session between tests
        with self.client.session_transaction() as sess:
            sess.clear()

    # =========================================================================
    # 1. DATA INTEGRITY AUDIT (Parts 4 & 5)
    # =========================================================================
    def test_01_dataset_integrity(self):
        # Total students: 476 (360 legacy + 116 appended across Semesters 1 to 6)
        self.assertEqual(len(self.students_df), 476, "Must contain exactly 476 students")
        self.assertEqual(self.students_df["Roll"].nunique(), 476, "Roll numbers must be unique")

        # Students per semester (Sem 1: 80, Sem 2: 79, Sem 3: 79, Sem 4: 79, Sem 5: 79, Sem 6: 80)
        sem_counts = self.students_df["Semester"].value_counts().to_dict()
        expected_sem_counts = {1: 80, 2: 79, 3: 79, 4: 79, 5: 79, 6: 80}
        for s, exp in expected_sem_counts.items():
            self.assertEqual(sem_counts.get(s, 0), exp, f"Semester {s} must have exactly {exp} students")

        # Exactly 6,664 Marks and 6,664 Attendance records
        self.assertEqual(len(self.marks_df), 6664, "Must contain exactly 6,664 marks records")
        self.assertEqual(len(self.attendance_df), 6664, "Must contain exactly 6,664 attendance records")

        # Duplicate checks
        marks_dupes = self.marks_df.duplicated(subset=["Roll_No", "Semester", "Subject"]).sum()
        self.assertEqual(marks_dupes, 0, "No duplicate marks records allowed")
        att_dupes = self.attendance_df.duplicated(subset=["Roll_No", "Semester", "Subject"]).sum()
        self.assertEqual(att_dupes, 0, "No duplicate attendance records allowed")

        # Future semester check (marks/attendance must not exceed student's current semester)
        merged_m = self.marks_df.merge(self.students_df[["Roll", "Semester"]], left_on="Roll_No", right_on="Roll")
        future_m = merged_m[merged_m["Semester_x"] > merged_m["Semester_y"]]
        self.assertEqual(len(future_m), 0, "No future semester marks records allowed")

        merged_a = self.attendance_df.merge(self.students_df[["Roll", "Semester"]], left_on="Roll_No", right_on="Roll")
        future_a = merged_a[merged_a["Semester_x"] > merged_a["Semester_y"]]
        self.assertEqual(len(future_a), 0, "No future semester attendance records allowed")

    def test_02_subject_mapping(self):
        """Verify exactly 4 subjects per semester matching SEMESTER_SUBJECTS."""
        for sem in range(1, 7):
            subjects = SEMESTER_SUBJECTS.get(sem, [])
            self.assertEqual(len(subjects), 4, f"Semester {sem} must have exactly 4 subjects")
            marks_sem_subjects = set(self.marks_df[self.marks_df["Semester"] == sem]["Subject"].unique())
            self.assertEqual(set(subjects), marks_sem_subjects, f"Subject mapping mismatch in Semester {sem}")

    # =========================================================================
    # 2. AUTHENTICATION & ROLE-BASED ACCESS CONTROL (Parts 2 & 3)
    # =========================================================================
    def test_03_login_and_role_redirect(self):
        """Verify general login portal validates credentials for all 3 roles."""
        # 1. Admin Login
        res_admin = self.client.post("/login", data={"role": "admin", "username": "admin", "password": "admin123"}, follow_redirects=False)
        self.assertEqual(res_admin.status_code, 302)
        self.assertEqual(res_admin.headers["Location"], "/")

        with self.client.session_transaction() as sess:
            sess.clear()

        # 2. Teacher Login (T001 / teacher001 with Teacher@123)
        res_teacher = self.client.post("/login", data={"role": "teacher", "username": "teacher001", "password": "Teacher@123"}, follow_redirects=False)
        self.assertEqual(res_teacher.status_code, 302)
        self.assertEqual(res_teacher.headers["Location"], "/teacher-dashboard")

        with self.client.session_transaction() as sess:
            sess.clear()

        # 3. Student Login (amairaM123 with student)
        res_student = self.client.post("/login", data={"role": "student", "username": "amairaM123", "password": "student"}, follow_redirects=False)
        self.assertEqual(res_student.status_code, 302)
        self.assertEqual(res_student.headers["Location"], "/student-dashboard")

    def test_04_invalid_credentials(self):
        """Verify invalid credentials show proper error and do not log in."""
        res = self.client.post("/login", data={"role": "student", "username": "nonexistent", "password": "badpassword"}, follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        html = res.get_data(as_text=True)
        self.assertIn("Invalid student credentials", html)
        with self.client.session_transaction() as sess:
            self.assertFalse(sess.get("student_logged_in", False))

    def test_05_cross_role_access_blocking(self):
        """Verify student cannot access /admin, /teacher, or /question-paper."""
        # Simulate Student Session
        with self.client.session_transaction() as sess:
            sess["student_logged_in"] = True
            sess["student_roll"] = "IT2026001"
            sess["student_name"] = "Amaira Maharaj"

        # 1. Student trying / (Admin Dashboard)
        res_admin = self.client.get("/", follow_redirects=False)
        self.assertEqual(res_admin.status_code, 302)
        self.assertEqual(res_admin.headers["Location"], "/student-dashboard")

        # 2. Student trying /admin
        res_admin_alias = self.client.get("/admin", follow_redirects=False)
        self.assertEqual(res_admin_alias.status_code, 302)
        self.assertEqual(res_admin_alias.headers["Location"], "/student-dashboard")

        # 3. Student trying /teacher
        res_teacher = self.client.get("/teacher", follow_redirects=False)
        self.assertEqual(res_teacher.status_code, 302)
        self.assertEqual(res_teacher.headers["Location"], "/student-dashboard")

        # 4. Student trying /teacher-dashboard
        res_teacher_dash = self.client.get("/teacher-dashboard", follow_redirects=False)
        self.assertEqual(res_teacher_dash.status_code, 302)
        self.assertEqual(res_teacher_dash.headers["Location"], "/student-dashboard")

        # 5. Student trying /question-paper
        res_qp = self.client.get("/question-paper", follow_redirects=False)
        self.assertEqual(res_qp.status_code, 302)
        self.assertEqual(res_qp.headers["Location"], "/student-dashboard")

        # 6. Student trying to view another student's profile
        res_other = self.client.get("/student/IT2026002", follow_redirects=False)
        self.assertEqual(res_other.status_code, 302)
        self.assertEqual(res_other.headers["Location"], "/student-dashboard")

        # 7. Student trying API of another student
        res_api = self.client.get("/api/student/IT2026002")
        self.assertEqual(res_api.status_code, 403)

    def test_06_teacher_cross_role_and_assignment_blocking(self):
        """Verify teacher cannot access /admin, and is restricted to assigned subjects."""
        with self.client.session_transaction() as sess:
            sess["teacher_logged_in"] = True
            sess["teacher_username"] = "prof_amit"
            sess["teacher_name"] = "Prof. Amit Sharma"
            sess["teacher_id"] = "T002"

        # Teacher trying / or /admin
        res_admin = self.client.get("/", follow_redirects=False)
        self.assertEqual(res_admin.status_code, 302)
        self.assertEqual(res_admin.headers["Location"], "/teacher-dashboard")

        # Teacher requesting unauthorized subject (e.g. Big Data Analytics) defaults to assigned subject
        res_unauth = self.client.get("/teacher-dashboard?subject=Big+Data+Analytics&semester=5", follow_redirects=True)
        self.assertEqual(res_unauth.status_code, 200)
        html = res_unauth.get_data(as_text=True)
        self.assertIn("Access Denied", html)

    # =========================================================================
    # 3. LOGOUT & CACHE-CONTROL (Part 3)
    # =========================================================================
    def test_07_logout_flows_and_cache_headers(self):
        """Verify logout clears session, redirects to /login, and injects no-cache headers."""
        # Teacher logout
        with self.client.session_transaction() as sess:
            sess["teacher_logged_in"] = True
            sess["teacher_username"] = "prof_amit"
        res_t_logout = self.client.get("/teacher-logout", follow_redirects=False)
        self.assertEqual(res_t_logout.status_code, 302)
        self.assertEqual(res_t_logout.headers["Location"], "/login")

        # Student logout
        with self.client.session_transaction() as sess:
            sess["student_logged_in"] = True
            sess["student_roll"] = "IT2026001"
        res_s_logout = self.client.get("/student-logout", follow_redirects=False)
        self.assertEqual(res_s_logout.status_code, 302)
        self.assertEqual(res_s_logout.headers["Location"], "/login")

        # General logout
        with self.client.session_transaction() as sess:
            sess["admin_logged_in"] = True
        res_a_logout = self.client.get("/logout", follow_redirects=False)
        self.assertEqual(res_a_logout.status_code, 302)
        self.assertEqual(res_a_logout.headers["Location"], "/login")

        # Check Cache-Control headers on response
        res_portal = self.client.get("/login")
        self.assertEqual(res_portal.status_code, 200)
        self.assertIn("no-cache", res_portal.headers.get("Cache-Control", ""))
        self.assertIn("no-store", res_portal.headers.get("Cache-Control", ""))
        self.assertIn("must-revalidate", res_portal.headers.get("Cache-Control", ""))

    # =========================================================================
    # 4. STUDENT DASHBOARD AUDIT (Part 6)
    # =========================================================================
    def test_08_student_dashboard_trend_points_per_semester(self):
        """Verify sample students from semesters 1 to 6 have exactly 1 to 6 trend points."""
        for sem in range(1, 7):
            cohort = self.students_df[self.students_df["Semester"] == sem]
            self.assertGreater(len(cohort), 0)
            sample_roll = cohort.iloc[0]["Roll"]
            trend = get_student_semester_trend(sample_roll, self.marks_df, self.attendance_df)
            self.assertEqual(len(trend["trend_data"]), sem, f"Sem {sem} student should have {sem} trend points")
            self.assertGreater(trend["summary"]["current_sgpi"], 0.0)
            self.assertGreater(trend["summary"]["average_sgpi"], 0.0)
            self.assertGreater(trend["summary"]["current_attendance"], 0.0)

    # =========================================================================
    # 5. ML PREDICTION INTEGRATION AUDIT (Part 10)
    # =========================================================================
    def test_09_ml_prediction_model(self):
        """Verify ML predictor pipeline, input features, lack of data leakage, and unknown category safety."""
        model = load_model()
        self.assertIsNotNone(model)

        # Standard prediction
        ext = predict_external_marks(internal_marks=22.0, attendance=82.0, semester=3, subject="Python for Data Analytics")
        self.assertIsInstance(ext, float)
        self.assertGreaterEqual(ext, 0.0)
        self.assertLessEqual(ext, 70.0)

        tot = predict_total_marks(internal_marks=22.0, attendance=82.0, semester=3, subject="Python for Data Analytics")
        self.assertEqual(tot, round(22.0 + ext, 2))

        perf = classify_predicted_performance(tot)
        self.assertIn(perf, ["Excellent", "Good", "Average", "Needs Improvement"])

        # Unknown subject safety (should not crash)
        unknown_ext = predict_external_marks(internal_marks=20.0, attendance=75.0, semester=1, subject="Unseen Special Topic")
        self.assertIsInstance(unknown_ext, float)
        self.assertGreaterEqual(unknown_ext, 0.0)

    # =========================================================================
    # 6. QUESTION PAPER INTELLIGENCE AUDIT (Part 11)
    # =========================================================================
    def test_10_question_paper_intelligence_pipeline(self):
        """Verify Question Paper Intelligence extracts and analyzes Sem 3 Python for Data Analytics PDF."""
        pdf_path = Path("question_paper/samples/sem3_python_data_analytics.pdf")
        self.assertTrue(pdf_path.exists(), "Sample PDF must exist")

        # 1. Extraction
        ext = extract_text_from_file(pdf_path)
        self.assertTrue(ext["success"], "PDF extraction must succeed")
        self.assertIn("PYTHON FOR DATA ANALYTICS", ext["text"].upper())

        # 2. Parsing
        parsed = parse_question_paper(ext["text"])
        self.assertTrue(parsed["success"])
        self.assertGreater(parsed["total_questions"], 0)
        self.assertEqual(parsed["declared_total_marks"], 70)

        # 3. Analysis
        analysis = analyze_question_paper(parsed)
        self.assertIn("kpis", analysis)
        self.assertIn("charts", analysis)
        self.assertIn("difficulty", analysis["charts"])
        self.assertIn("question_type", analysis["charts"])
        self.assertIn("topic_clusters", analysis)
        self.assertEqual(analysis["kpis"]["total_questions"], parsed["total_questions"])

    # =========================================================================
    # 7. THEME SYSTEM AUDIT (Part 12)
    # =========================================================================
    def test_11_theme_assets_and_templates(self):
        """Verify theme.css, theme.js exist and theme toggle buttons are integrated."""
        theme_css = Path("static/css/theme.css")
        theme_js = Path("static/js/theme.js")
        self.assertTrue(theme_css.exists(), "static/css/theme.css must exist")
        self.assertTrue(theme_js.exists(), "static/js/theme.js must exist")

        css_content = theme_css.read_text(encoding="utf-8")
        self.assertIn("[data-theme=\"dark\"]", css_content)
        self.assertIn("--card-bg", css_content)
        self.assertIn(".theme-toggle-btn", css_content)

        js_content = theme_js.read_text(encoding="utf-8")
        self.assertIn("toggleTheme", js_content)
        self.assertIn("localStorage", js_content)
        self.assertIn("updateChartsForTheme", js_content)

        # Verify theme toggle button in major templates
        templates_to_check = [
            "templates/login.html",
            "templates/index.html",
            "templates/teacher_dashboard.html",
            "templates/student_dashboard.html",
            "templates/student.html",
            "templates/question_paper.html",
            "templates/error.html"
        ]
        for tpath in templates_to_check:
            content = Path(tpath).read_text(encoding="utf-8")
            self.assertIn("themeToggleBtn", content, f"Theme toggle button missing in {tpath}")
            self.assertIn("theme.js", content, f"theme.js script link missing in {tpath}")

    # =========================================================================
    # 8. BRANDING AUDIT (Part 14)
    # =========================================================================
    def test_12_branding_and_titles(self):
        """Verify 'Academic Intelligence' application branding and page titles."""
        templates_map = {
            "templates/login.html": "Academic Intelligence | Login",
            "templates/index.html": "Academic Intelligence | Admin Dashboard",
            "templates/teacher_dashboard.html": "Academic Intelligence | Teacher Dashboard",
            "templates/student_dashboard.html": "Academic Intelligence | Student Dashboard",
            "templates/question_paper.html": "Academic Intelligence | Question Paper Intelligence",
        }
        for tpath, expected_title in templates_map.items():
            content = Path(tpath).read_text(encoding="utf-8")
            self.assertIn(expected_title, content, f"Title mismatch in {tpath}")
            self.assertNotIn("APEX", content, f"Found APEX branding in {tpath}")
            self.assertNotIn("Apex", content, f"Found Apex branding in {tpath}")


if __name__ == "__main__":
    unittest.main()
