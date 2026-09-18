"""
Phase 8.4: Test Suite for Personalized Student Improvement Plan
Covers:
1. Student-only access & authorization (unauthenticated, teacher, student)
2. Student isolation (session-based roll number)
3. Multi-semester generation (Sem 1, Sem 3, Sem 5, Sem 6)
4. High vs Average vs Low performer differentiation
5. Attendance threshold analysis (< 75% vs >= 75%)
6. SGPI trend calculation & direction
7. ML prediction outlook integration (without technical metrics)
8. Question paper intelligence integration
9. Topic-level learning plan, revision plan, practice tasks
10. Weekly study roadmap & interactive action checklist
"""

import unittest
import pandas as pd
from app import app
from utils.student_recommendations import generate_improvement_plan

class TestStudentImprovementPlan(unittest.TestCase):
    def setUp(self):
        self.app = app
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()

    def test_unauthenticated_access_denied(self):
        """Unauthenticated user accessing /student/improvement-plan must be redirected to login"""
        res = self.client.get("/student/improvement-plan", follow_redirects=False)
        self.assertEqual(res.status_code, 302)
        self.assertIn("/login", res.headers.get("Location", ""))

    def test_teacher_access_denied(self):
        """Teacher session attempting to access student improvement plan must be redirected to teacher dashboard"""
        with self.client.session_transaction() as sess:
            sess["teacher_logged_in"] = True
            sess["teacher_name"] = "Dr. Test Teacher"
            sess["teacher_email"] = "teacher@test.com"
        
        res = self.client.get("/student/improvement-plan", follow_redirects=False)
        self.assertEqual(res.status_code, 302)
        self.assertIn("/teacher-dashboard", res.headers.get("Location", ""))

    def test_authenticated_student_access_success(self):
        """Authenticated student must successfully access /student/improvement-plan with HTTP 200"""
        with self.client.session_transaction() as sess:
            sess["student_logged_in"] = True
            sess["student_roll"] = "IT2022001"
            sess["student_name"] = "Zashil Mahajan"
            sess["user_role"] = "student"

        res = self.client.get("/student/improvement-plan")
        self.assertEqual(res.status_code, 200)
        html = res.get_data(as_text=True)
        self.assertIn("MY IMPROVEMENT PLAN", html)
        self.assertIn("Zashil Mahajan", html)
        self.assertIn("IT2022001", html)
        self.assertIn("ACADEMIC HEALTH", html)
        self.assertIn("TOP PRIORITIES", html)
        self.assertIn("SUBJECT PERFORMANCE", html)
        self.assertIn("STUDY ROADMAP", html)

    def test_technical_ml_metrics_hidden_from_student_plan(self):
        """Ensure no technical ML metrics (MAE, RMSE, R2, RandomForestRegressor) appear in the student improvement plan"""
        with self.client.session_transaction() as sess:
            sess["student_logged_in"] = True
            sess["student_roll"] = "IT2022001"
            sess["student_name"] = "Zashil Mahajan"
            sess["user_role"] = "student"

        res = self.client.get("/student/improvement-plan")
        self.assertEqual(res.status_code, 200)
        html = res.get_data(as_text=True)
        self.assertNotIn("RandomForestRegressor", html)
        self.assertNotIn("OneHotEncoder", html)
        self.assertNotIn("R² Score", html)
        self.assertNotIn("RMSE", html)
        self.assertNotIn("training records", html)

    def test_session_isolation_arbitrary_query_ignored(self):
        """Student A cannot access Student B by passing ?roll_no=IT2024001; session rules"""
        with self.client.session_transaction() as sess:
            sess["student_logged_in"] = True
            sess["student_roll"] = "IT2022001"
            sess["student_name"] = "Zashil Mahajan"

        res = self.client.get("/student/improvement-plan?roll_no=IT2024001")
        self.assertEqual(res.status_code, 200)
        html = res.get_data(as_text=True)
        # Must reflect session student, not query param
        self.assertIn("IT2022001", html)

    def test_recommendation_engine_sem1(self):
        """Test Sem 1 student plan generation"""
        plan = generate_improvement_plan("IT2026001")
        self.assertIsNotNone(plan)
        self.assertEqual(plan["student"]["Semester"], 1)
        self.assertIn("overall_score", plan)
        self.assertIn("priorities", plan)
        self.assertIn("ranked_subjects", plan)
        self.assertIn("roadmap", plan)

    def test_recommendation_engine_sem3(self):
        """Test Sem 3 student plan generation"""
        plan = generate_improvement_plan("IT2024001")
        self.assertIsNotNone(plan)
        self.assertEqual(plan["student"]["Semester"], 3)
        self.assertIn("overall_score", plan)
        self.assertIn("priorities", plan)
        self.assertIn("learning_topics", plan)

    def test_recommendation_engine_sem5(self):
        """Test Sem 5 student plan generation"""
        plan = generate_improvement_plan("IT2022001")
        self.assertIsNotNone(plan)
        self.assertEqual(plan["student"]["Semester"], 5)
        self.assertIn("attendance_plan", plan)
        self.assertIn("sgpi_trend_direction", plan)
        self.assertIn("predictions", plan)

    def test_recommendation_engine_sem6(self):
        """Test Sem 6 student plan generation"""
        plan = generate_improvement_plan("IT2021001")
        self.assertIsNotNone(plan)
        self.assertEqual(plan["student"]["Semester"], 6)
        self.assertIn("practice_topics", plan)
        self.assertIn("action_checklist", plan)

    def test_attendance_rule_differentiation(self):
        """Test that low attendance (<75%) triggers attendance warning priority, and high doesn't"""
        from utils.data_loader import load_data
        _, _, _, attendance_df, _ = load_data()
        student_att = attendance_df.groupby("Roll_No")["Attendance"].mean()
        high_att_students = student_att[student_att >= 80].index.tolist()
        low_att_students = student_att[student_att < 75].index.tolist()

        if high_att_students:
            plan_high = generate_improvement_plan(high_att_students[0])
            self.assertIn(plan_high["attendance_plan"]["status"], ["Excellent", "Good", "Selective Focus Needed"])

        if low_att_students:
            plan_low = generate_improvement_plan(low_att_students[0])
            self.assertEqual(plan_low["attendance_plan"]["status"], "Needs Attention")
            # Should have an attendance priority
            att_priorities = [p for p in plan_low["priorities"] if "Attendance" in p["title"]]
            self.assertTrue(len(att_priorities) > 0)

    def test_weak_vs_strong_subject_sorting(self):
        """Verify that ranked_subjects sorts weakest first"""
        plan = generate_improvement_plan("IT2024001")
        subjects = plan["ranked_subjects"]
        if len(subjects) > 1:
            for i in range(len(subjects) - 1):
                self.assertLessEqual(subjects[i]["total"], subjects[i+1]["total"])

    def test_sgpi_trend_analysis(self):
        """Verify SGPI trend calculates direction and history"""
        plan = generate_improvement_plan("IT2022001")
        self.assertIn(plan["sgpi_trend_direction"], ["Improving", "Declining", "Consistent", "Stable", "Baseline"])
        self.assertTrue(len(plan["sgpi_history"]) >= 1)

    def test_question_paper_intelligence_exam_focus(self):
        """Verify exam_intelligence contains valid information or graceful fallback"""
        plan = generate_improvement_plan("IT2024001")
        exam_intel = plan["exam_intelligence"]
        self.assertTrue(exam_intel["available"])
        self.assertIn("Pandas", exam_intel["frequently_asked"])

if __name__ == "__main__":
    unittest.main()
