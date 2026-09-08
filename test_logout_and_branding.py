"""Test script to verify branding replacement and logout redirection/security."""

import unittest
from app import app


class TestBrandingAndLogout(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def test_general_login_branding(self):
        res = self.client.get("/login")
        self.assertEqual(res.status_code, 200)
        html = res.get_data(as_text=True)
        self.assertIn("Academic Intelligence | Login", html)
        self.assertIn("Academic Intelligence", html)
        self.assertNotIn("APEX", html)
        self.assertNotIn("Apex", html)

    def test_teacher_login_branding(self):
        res = self.client.get("/teacher-login")
        self.assertEqual(res.status_code, 200)
        html = res.get_data(as_text=True)
        self.assertIn("Academic Intelligence | Teacher Login", html)
        self.assertNotIn("APEX", html)

    def test_teacher_dashboard_and_logout_flow(self):
        # 1. Simulate Teacher Login
        with self.client.session_transaction() as sess:
            sess["teacher_logged_in"] = True
            sess["teacher_username"] = "prof_amit"
            sess["teacher_name"] = "Prof. Amit Sharma"
            sess["teacher_id"] = "T002"

        # 2. Access Teacher Dashboard
        res_dash = self.client.get("/teacher-dashboard")
        self.assertEqual(res_dash.status_code, 200)
        html_dash = res_dash.get_data(as_text=True)
        self.assertIn("Academic Intelligence | Teacher Dashboard", html_dash)
        self.assertNotIn("APEX", html_dash)

        # 3. Trigger Teacher Logout
        res_logout = self.client.get("/teacher-logout", follow_redirects=False)
        self.assertEqual(res_logout.status_code, 302)
        # Verify redirect is directly to general login page /login
        self.assertEqual(res_logout.headers["Location"], "/login")

        # 4. Verify Session is completely cleared
        with self.client.session_transaction() as sess:
            self.assertFalse(sess.get("teacher_logged_in", False))
            self.assertIsNone(sess.get("teacher_username"))
            self.assertIsNone(sess.get("teacher_id"))
            self.assertIsNone(sess.get("teacher_name"))

        # 5. Verify protected dashboard access after logout is blocked
        res_after = self.client.get("/teacher-dashboard", follow_redirects=False)
        self.assertEqual(res_after.status_code, 302)
        self.assertIn("/teacher-login", res_after.headers["Location"])

    def test_student_dashboard_and_logout_flow(self):
        with self.client.session_transaction() as sess:
            sess["student_logged_in"] = True
            sess["student_roll"] = "IT2026001"
            sess["student_name"] = "Amaira Maharaj"

        res_dash = self.client.get("/student-dashboard")
        self.assertEqual(res_dash.status_code, 200)
        html_dash = res_dash.get_data(as_text=True)
        self.assertIn("Academic Intelligence | Student Dashboard", html_dash)
        self.assertNotIn("APEX", html_dash)

        res_logout = self.client.get("/student-logout", follow_redirects=False)
        self.assertEqual(res_logout.status_code, 302)
        self.assertEqual(res_logout.headers["Location"], "/logout")

        res_final_logout = self.client.get("/logout", follow_redirects=False)
        self.assertEqual(res_final_logout.status_code, 302)
        self.assertEqual(res_final_logout.headers["Location"], "/login")

    def test_admin_dashboard_branding_and_logout(self):
        with self.client.session_transaction() as sess:
            sess["admin_logged_in"] = True
            sess["admin_id"] = "T001"
            sess["admin_name"] = "Mr. Zeeshan Shaikh"

        res_dash = self.client.get("/")
        self.assertEqual(res_dash.status_code, 200)
        html_dash = res_dash.get_data(as_text=True)
        self.assertIn("Academic Intelligence | Admin Dashboard", html_dash)
        self.assertNotIn("APEX", html_dash)

        res_logout = self.client.get("/logout", follow_redirects=False)
        self.assertEqual(res_logout.status_code, 302)
        self.assertEqual(res_logout.headers["Location"], "/login")

    def test_question_paper_portal_branding(self):
        with self.client.session_transaction() as sess:
            sess["admin_logged_in"] = True
            sess["admin_id"] = "T001"
            sess["admin_name"] = "Mr. Zeeshan Shaikh"

        res_qp = self.client.get("/question-paper")
        self.assertEqual(res_qp.status_code, 200)
        html_qp = res_qp.get_data(as_text=True)
        self.assertIn("Academic Intelligence | Question Paper Intelligence", html_qp)
        self.assertNotIn("APEX", html_qp)


if __name__ == "__main__":
    unittest.main()
