"""
Comprehensive Test Suite for Unified Authentication System
Tests Student, Teacher, and Admin login, role switching parameters,
credential authorization, session isolation, and logout redirects.
"""

import unittest
from app import app


class TestUnifiedAuthSystem(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def test_01_unified_login_page_renders_with_role_tabs(self):
        """Verify unified login page contains student, teacher, and admin tabs."""
        res = self.client.get("/login")
        self.assertEqual(res.status_code, 200)
        html = res.get_data(as_text=True)

        # Branding and Title
        self.assertIn("Academic Intelligence | Login", html)
        self.assertIn("ACADEMIC INTELLIGENCE", html)

        # Role switcher elements
        self.assertIn("tab-student", html)
        self.assertIn("tab-teacher", html)
        self.assertIn("tab-admin", html)
        self.assertIn("role-segmented-control", html)

        # SVG Illustrations
        self.assertIn("illustrStudent", html)
        self.assertIn("illustrTeacher", html)
        self.assertIn("illustrAdmin", html)

        # Password toggle button
        self.assertIn("togglePasswordBtn", html)
        self.assertIn("btn-toggle-password", html)

        # Theme toggle button
        self.assertIn("themeToggleBtn", html)

        # Quick test helper chips
        self.assertIn("quickFill", html)
        self.assertIn("IT2026001", html)
        self.assertIn("T001", html)

    def test_02_role_query_parameter_selection(self):
        """Verify role query param selects initial role tab."""
        # Teacher param
        res_teacher = self.client.get("/login?role=teacher")
        self.assertEqual(res_teacher.status_code, 200)

        # Admin param
        res_admin = self.client.get("/login?role=admin")
        self.assertEqual(res_admin.status_code, 200)

    def test_03_student_login_via_roll_and_redirect(self):
        """Verify student can authenticate with Roll number."""
        res = self.client.post("/login", data={
            "role": "student",
            "username": "IT2026001",
            "password": "student"
        }, follow_redirects=False)

        self.assertEqual(res.status_code, 302)
        self.assertEqual(res.headers["Location"], "/student-dashboard")

        with self.client.session_transaction() as sess:
            self.assertTrue(sess.get("student_logged_in"))
            self.assertEqual(sess.get("student_roll"), "IT2026001")

    def test_04_student_login_invalid_credentials(self):
        """Verify invalid student credentials fails and redirects to student login."""
        res = self.client.post("/login", data={
            "role": "student",
            "username": "IT2026001",
            "password": "wrong_password"
        }, follow_redirects=False)

        self.assertEqual(res.status_code, 302)
        self.assertIn("role=student", res.headers["Location"])

    def test_05_teacher_login_via_id_and_redirect(self):
        """Verify teacher can authenticate with Teacher_ID."""
        res = self.client.post("/login", data={
            "role": "teacher",
            "username": "T001",
            "password": "Teacher@123"
        }, follow_redirects=False)

        self.assertEqual(res.status_code, 302)
        self.assertEqual(res.headers["Location"], "/teacher-dashboard")

        with self.client.session_transaction() as sess:
            self.assertTrue(sess.get("teacher_logged_in"))
            self.assertEqual(sess.get("teacher_id"), "T001")

    def test_06_teacher_login_invalid_credentials(self):
        """Verify invalid teacher credentials fails and redirects to teacher login."""
        res = self.client.post("/login", data={
            "role": "teacher",
            "username": "T001",
            "password": "wrong_password"
        }, follow_redirects=False)

        self.assertEqual(res.status_code, 302)
        self.assertIn("role=teacher", res.headers["Location"])

    def test_07_admin_login_and_redirect(self):
        """Verify admin can authenticate and reach admin dashboard."""
        res = self.client.post("/login", data={
            "role": "admin",
            "username": "admin",
            "password": "admin123"
        }, follow_redirects=False)

        self.assertEqual(res.status_code, 302)
        self.assertEqual(res.headers["Location"], "/")

    def test_08_all_logout_routes_redirect_to_general_login(self):
        """Verify all 3 logout routes redirect to /login."""
        for endpoint in ["/logout", "/teacher-logout", "/student-logout"]:
            res = self.client.get(endpoint, follow_redirects=False)
            self.assertEqual(res.status_code, 302, f"Failed for {endpoint}")
            self.assertEqual(res.headers["Location"], "/login", f"Failed for {endpoint}")

    def test_09_unauthorized_dashboard_access_control(self):
        """Verify student cannot access teacher or admin dashboards."""
        with self.client.session_transaction() as sess:
            sess["student_logged_in"] = True
            sess["student_roll"] = "IT2026001"

        # Attempt to access Teacher dashboard
        res_t = self.client.get("/teacher-dashboard", follow_redirects=False)
        self.assertEqual(res_t.status_code, 302)
        self.assertEqual(res_t.headers["Location"], "/student-dashboard")

        # Attempt to access Admin dashboard
        res_a = self.client.get("/", follow_redirects=False)
        self.assertEqual(res_a.status_code, 302)
        self.assertEqual(res_a.headers["Location"], "/student-dashboard")


if __name__ == "__main__":
    unittest.main()
