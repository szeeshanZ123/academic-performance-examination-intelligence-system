import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import unittest
import pandas as pd
from app import app
from utils.data_loader import load_data, get_student_detail
from analysis.analytics import get_student_semester_trend, get_teacher_subject_analytics
from utils.student_recommendations import generate_improvement_plan
from ml.predictor import predict_subject_performance

class TestNewStudentIntegrity(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()
        self.app_ctx = app.app_context()
        self.app_ctx.push()

    def tearDown(self):
        self.app_ctx.pop()

    def test_total_counts_and_uniqueness(self):
        admin_df, students, marks_df, attendance_df, subject_combined = load_data(force_reload=True)
        
        # Total student count: 360 existing + 116 new = 476
        self.assertEqual(len(students), 476)
        
        # Uniqueness of Roll Number
        self.assertEqual(len(students["Roll"].unique()), 476)
        
        # Check specific new students exist
        self.assertTrue((students["Roll"] == "254102").any())
        self.assertTrue((students["Roll"] == "254190").any())
        self.assertTrue((students["Roll"] == "254201").any())
        self.assertTrue((students["Roll"] == "254228").any())
        self.assertTrue((students["Roll"] == "254265").any())

        # Check exact names preserved
        student_254201 = students[students["Roll"] == "254201"].iloc[0]
        self.assertEqual(student_254201["Name"], "RITESH MAHENDRA KANOJIYA")
        self.assertEqual(student_254201["Division"], "B")

        student_254228 = students[students["Roll"] == "254228"].iloc[0]
        self.assertEqual(student_254228["Name"], "ZEESHAN HANIF SHAIKH")
        self.assertEqual(student_254228["Division"], "B")

        student_254102 = students[students["Roll"] == "254102"].iloc[0]
        self.assertEqual(student_254102["Name"], "ABDUL AZIZ REHMATULLAH SHAIKH")
        self.assertEqual(student_254102["Division"], "A")

        # Existing student integrity preserved
        student_it2026001 = students[students["Roll"] == "IT2026001"].iloc[0]
        self.assertEqual(student_it2026001["Name"], "Amaira Maharaj")

    def test_student_login_and_dashboard(self):
        # 1. Login with Roll Number 254228
        res = self.client.post("/login", data={
            "role": "student",
            "username": "254228",
            "password": "student"
        }, follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"ZEESHAN HANIF SHAIKH", res.data)
        self.assertIn(b"254228", res.data)

        # 2. Verify student dashboard content (254228 is in Semester 5)
        res_dash = self.client.get("/student-dashboard")
        self.assertEqual(res_dash.status_code, 200)
        self.assertIn(b"ZEESHAN HANIF SHAIKH", res_dash.data)
        self.assertIn(b"DIVISION B", res_dash.data)
        self.assertIn(b"Machine Learning", res_dash.data)
        self.assertIn(b"Cyber Security", res_dash.data)

        # 3. Verify personalized improvement plan
        res_plan = self.client.get("/student/improvement-plan")
        self.assertEqual(res_plan.status_code, 200)
        self.assertIn(b"MY IMPROVEMENT PLAN", res_plan.data)
        self.assertIn(b"ZEESHAN HANIF SHAIKH", res_plan.data)

    def test_another_new_student_isolation(self):
        # 1. Login with Roll Number 254102 (Semester 1, Div A)
        res = self.client.post("/login", data={
            "role": "student",
            "username": "254102",
            "password": "student"
        }, follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"ABDUL AZIZ REHMATULLAH SHAIKH", res.data)
        self.assertIn(b"254102", res.data)
        self.assertIn(b"Python Programming", res.data)
        # Verify isolation: should NOT contain Zeeshan's name
        self.assertNotIn(b"ZEESHAN HANIF SHAIKH", res.data)

    def test_teacher_dashboard_sees_new_students(self):
        # Login as teacher (Amit Patil teaches Machine Learning Sem 5 and Operating Systems Sem 3)
        res_login = self.client.post("/login", data={
            "role": "teacher",
            "username": "teacher001",
            "password": "Teacher@123"
        }, follow_redirects=True)
        self.assertEqual(res_login.status_code, 200)

        # Check Machine Learning in Semester 5
        res = self.client.get("/teacher-dashboard?subject=Machine+Learning&semester=5")
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"Machine Learning", res.data)
        self.assertIn(b"ZEESHAN HANIF SHAIKH", res.data)
        self.assertIn(b"254228", res.data)

    def test_admin_dashboard_and_reports(self):
        # Login as admin
        res_login = self.client.post("/login", data={
            "role": "admin",
            "username": "admin",
            "password": "admin123"
        }, follow_redirects=True)
        self.assertEqual(res_login.status_code, 200)

        res = self.client.get("/")
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"476", res.data)  # Total students count updated to 476

        res_rep = self.client.get("/reports")
        self.assertEqual(res_rep.status_code, 200)

if __name__ == "__main__":
    unittest.main()
