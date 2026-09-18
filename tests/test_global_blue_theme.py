"""
Comprehensive test suite verifying the Global Blue Design System implementation
across Academic Intelligence.
"""
import re
import unittest
from app import app


class TestGlobalBlueTheme(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        app.testing = True
        cls.client = app.test_client()

        with open("static/css/theme.css", "r", encoding="utf-8") as f:
            cls.css_content = f.read()

        with open("static/js/theme.js", "r", encoding="utf-8") as f:
            cls.js_content = f.read()

    def setUp(self):
        with self.client.session_transaction() as sess:
            sess.clear()

    # 1. Global Color System & Design Tokens
    def test_light_mode_tokens(self):
        """Verify Light Mode color tokens match the master prompt requirements."""
        self.assertIn("--bg-primary: #FFFFFF;", self.css_content)
        self.assertIn("--bg-secondary: #F0F8FF;", self.css_content)
        self.assertIn("--bg-tertiary: #DBEAFE;", self.css_content)
        self.assertIn("--primary: #2563EB;", self.css_content)
        self.assertIn("--primary-hover: #1E40AF;", self.css_content)
        self.assertIn("--secondary: #3B82F6;", self.css_content)
        self.assertIn("--success: #16A34A;", self.css_content)
        self.assertIn("--warning: #F59E0B;", self.css_content)
        self.assertIn("--danger: #DC2626;", self.css_content)
        self.assertIn("--text-primary: #0F172A;", self.css_content)
        self.assertIn("--text-secondary: #475569;", self.css_content)
        self.assertIn("--border: #E2E8F0;", self.css_content)

    def test_dark_mode_tokens(self):
        """Verify Dark Mode color tokens match the master prompt requirements."""
        self.assertIn("--bg-primary: #0A1428;", self.css_content)
        self.assertIn("--bg-secondary: #112240;", self.css_content)
        self.assertIn("--bg-tertiary: #1E3A5F;", self.css_content)
        self.assertIn("--primary: #3B82F6;", self.css_content)
        self.assertIn("--primary-hover: #60A5FA;", self.css_content)
        self.assertIn("--secondary: #93C5FD;", self.css_content)
        self.assertIn("--success: #22C55E;", self.css_content)
        self.assertIn("--warning: #FBBF24;", self.css_content)
        self.assertIn("--danger: #F87171;", self.css_content)
        self.assertIn("--text-primary: #F1F5F9;", self.css_content)
        self.assertIn("--text-secondary: #94A3B8;", self.css_content)
        self.assertIn("--border: #1E293B;", self.css_content)

    # 2. Button Classes
    def test_global_button_classes(self):
        """Verify global button classes conform to design tokens."""
        self.assertIn(".btn-primary", self.css_content)
        self.assertIn(".btn-secondary", self.css_content)
        self.assertIn(".btn-danger", self.css_content)
        self.assertIn(".btn-success", self.css_content)
        self.assertIn(".btn-warning", self.css_content)

    # 3. Chart Palette & Theme JS
    def test_chart_palette_tokens(self):
        """Verify Chart.js color palette matches Global Blue tokens."""
        self.assertIn("#2563EB", self.js_content)
        self.assertIn("#3B82F6", self.js_content)
        self.assertIn("#93C5FD", self.js_content)
        self.assertIn("#16A34A", self.js_content)
        self.assertIn("#F59E0B", self.js_content)
        self.assertIn("#DC2626", self.js_content)

    def test_theme_toggle_persistence(self):
        """Verify theme toggle uses localStorage for cross-page persistence."""
        self.assertIn('localStorage.setItem("theme"', self.js_content)
        self.assertIn('localStorage.getItem("theme")', self.js_content)

    # 4. Zero Legacy Purple/Violet/Indigo
    def test_no_legacy_purple_or_apex(self):
        """Verify no legacy purple hex codes or APEX branding remain in CSS/JS."""
        forbidden_hex = ["#4f46e5", "#6366f1", "#8b5cf6", "#a855f7", "#7c3aed", "#9333ea"]
        for hex_code in forbidden_hex:
            self.assertNotIn(hex_code, self.css_content.lower())
            self.assertNotIn(hex_code, self.js_content.lower())
        self.assertNotIn("apex", self.css_content.lower())
        self.assertNotIn("apex", self.js_content.lower())

    # 5. Route Integration & Theme Asset Linking
    def test_login_page_renders_theme_assets(self):
        response = self.client.get("/login")
        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        self.assertIn("theme.css", html)
        self.assertIn("theme.js", html)
        self.assertIn("Academic Intelligence", html)
        self.assertNotIn("APEX", html)

    def test_admin_dashboard_renders_theme_assets(self):
        with self.client.session_transaction() as sess:
            sess["admin_logged_in"] = True
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        self.assertIn("theme.css", html)
        self.assertIn("theme.js", html)
        self.assertIn("Academic Intelligence", html)

    def test_teacher_dashboard_renders_theme_assets(self):
        with self.client.session_transaction() as sess:
            sess["teacher_logged_in"] = True
            sess["teacher_id"] = "T001"
        response = self.client.get("/teacher-dashboard")
        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        self.assertIn("theme.css", html)
        self.assertIn("theme.js", html)
        self.assertIn("Academic Intelligence", html)

    def test_student_dashboard_renders_theme_assets(self):
        with self.client.session_transaction() as sess:
            sess["student_logged_in"] = True
            sess["student_roll"] = "IT2024001"
        response = self.client.get("/student-dashboard")
        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        self.assertIn("theme.css", html)
        self.assertIn("theme.js", html)
        self.assertIn("Academic Intelligence", html)

    def test_student_profile_renders_theme_assets(self):
        with self.client.session_transaction() as sess:
            sess["admin_logged_in"] = True
        response = self.client.get("/student/IT2024001")
        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        self.assertIn("theme.css", html)
        self.assertIn("theme.js", html)
        self.assertIn("Academic Intelligence", html)

    def test_question_paper_renders_theme_assets(self):
        with self.client.session_transaction() as sess:
            sess["admin_logged_in"] = True
        response = self.client.get("/question-paper")
        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        self.assertIn("theme.css", html)
        self.assertIn("theme.js", html)
        self.assertIn("Academic Intelligence", html)


if __name__ == "__main__":
    unittest.main()
