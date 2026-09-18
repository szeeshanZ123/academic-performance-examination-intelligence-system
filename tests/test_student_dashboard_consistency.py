"""Test student dashboard and student profile consistency across all semesters."""

import unittest
from app import app
from utils.data_loader import load_data, get_student_detail
from analysis.analytics import get_student_semester_trend


class TestStudentDataConsistency(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = app.test_client()
        _, cls.students, _, _, _ = load_data()

    def test_all_semesters_represented_and_consistent(self):
        # Test one sample student from each semester 1 to 6
        for sem in range(1, 7):
            cohort = self.students[self.students["Semester"] == sem]
            self.assertGreater(len(cohort), 0, f"Semester {sem} has no students")
            
            sample_student = cohort.iloc[0]
            roll = str(sample_student["Roll"]).strip()
            
            # Test get_student_detail
            detail = get_student_detail(roll)
            self.assertIsNotNone(detail, f"Detail missing for roll {roll}")
            self.assertGreater(len(detail["subjects_list"]), 0, f"No subjects for roll {roll}")
            self.assertGreater(detail["student"]["SGPI"], 0.0, f"SGPI 0.0 for roll {roll}")
            self.assertGreater(detail["student"]["Attendance"], 0.0, f"Attendance 0.0 for roll {roll}")
            
            # Test get_student_semester_trend
            trend = get_student_semester_trend(roll)
            self.assertEqual(len(trend["trend_data"]), sem, f"Expected {sem} trend points for roll {roll} (Sem {sem}), got {len(trend['trend_data'])}")
            self.assertGreater(trend["summary"]["current_sgpi"], 0.0)
            self.assertGreater(trend["summary"]["average_sgpi"], 0.0)
            self.assertGreater(trend["summary"]["current_attendance"], 0.0)
            self.assertGreater(trend["summary"]["overall_average_attendance"], 0.0)

    def test_specific_student_it2023058_profile(self):
        """Test the exact student from user screenshot: IT2023058 (Semester 4)."""
        roll = "IT2023058"
        detail = get_student_detail(roll)
        self.assertIsNotNone(detail)
        self.assertEqual(detail["student"]["Semester"], 4)
        
        trend = get_student_semester_trend(roll)
        self.assertEqual(len(trend["trend_data"]), 4)
        self.assertEqual(trend["summary"]["total_semesters"], 4)
        self.assertGreater(trend["summary"]["current_sgpi"], 0.0)

        # Log in as teacher and access /student/IT2023058
        with self.client.session_transaction() as sess:
            sess["teacher_logged_in"] = True
            sess["teacher_username"] = "prof_amit"
            sess["teacher_name"] = "Prof. Amit Sharma"
            sess["teacher_id"] = "T002"

        res = self.client.get(f"/student/{roll}")
        self.assertEqual(res.status_code, 200)
        html = res.get_data(as_text=True)

        # Verify predictions section is populated (not saying "Prediction is currently unavailable")
        self.assertNotIn("Prediction is currently unavailable.", html)
        self.assertIn("Predicted External Marks", html)

        # Verify trend numbers are populated and not 0.0
        self.assertIn(str(trend["summary"]["current_sgpi"]), html)
        self.assertIn(str(trend["summary"]["highest_sgpi"]), html)
        self.assertIn(f"{trend['summary']['current_attendance']}%", html)

    def test_student_dashboard_route_for_it2023058(self):
        """Test logged-in student dashboard for IT2023058."""
        roll = "IT2023058"
        with self.client.session_transaction() as sess:
            sess["student_logged_in"] = True
            sess["student_roll"] = roll
            sess["student_name"] = "Mohammed Saini"

        res = self.client.get("/student-dashboard")
        self.assertEqual(res.status_code, 200)
        html = res.get_data(as_text=True)

        self.assertNotIn("Prediction is currently unavailable.", html)
        self.assertIn("Predicted External Marks", html)
        self.assertIn("Semester Performance Trend", html)


if __name__ == "__main__":
    unittest.main()
