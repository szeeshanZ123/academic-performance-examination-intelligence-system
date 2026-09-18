"""Comprehensive Test Suite for Phase 8.5 — Reports & Export System.

Covers:
1. Admin Reports Center & Filters (Overall, Performance, Attendance, At-Risk, Semester, Subject)
2. Admin CSV and PDF Exports
3. Teacher Reports Center & Assigned Scoping
4. Teacher CSV and PDF Exports
5. Student 'My Academic Report' Preview & Sections
6. Student CSV and PDF Exports
7. Strict RBAC & Security (Cross-Student 403, Cross-Role 403, Unassigned Subject 403)
8. Data Consistency Validation (Dashboard KPIs == Report KPIs)
"""

import io
import unittest
from pathlib import Path
from app import app
from utils.data_loader import load_data, get_student_detail, get_teacher_assignments
from analysis.analytics import dashboard_kpis
from reports.report_service import get_admin_reports_data, get_teacher_reports_data, get_student_report_data
from reports.csv_export import export_admin_csv, export_teacher_csv, export_student_csv
from reports.pdf_export import generate_student_pdf, generate_teacher_pdf, generate_admin_pdf


class TestReportsSystem(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = app
        cls.app.config["TESTING"] = True
        cls.client = cls.app.test_client()
        cls.admin_df, cls.students_df, cls.marks_df, cls.attendance_df, cls.combined = load_data()

    def setUp(self):
        # Fresh test client per test
        self.client = self.app.test_client()

    # =========================================================================
    # 1. ADMIN REPORTS TESTS
    # =========================================================================

    def test_01_admin_reports_access_and_filters(self):
        """Admin can access reports center with filters."""
        with self.client.session_transaction() as sess:
            sess["admin_logged_in"] = True
            sess["admin_name"] = "Mr. Zeeshan Shaikh"

        # 1. All records
        res = self.client.get("/admin/reports")
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"Institutional Report Center", res.data)
        self.assertIn(b"TOTAL STUDENTS", res.data)

        # 2. Semester filter
        res_sem3 = self.client.get("/admin/reports?semester=3&report_type=performance")
        self.assertEqual(res_sem3.status_code, 200)
        self.assertIn(b"Sem 3", res_sem3.data)

        # 3. Subject filter
        res_subj = self.client.get("/admin/reports?subject=Python+for+Data+Analytics&report_type=performance")
        self.assertEqual(res_subj.status_code, 200)
        self.assertIn(b"Python for Data Analytics", res_subj.data)

        # 4. At-risk report tab
        res_risk = self.client.get("/admin/reports?report_type=at_risk")
        self.assertEqual(res_risk.status_code, 200)
        self.assertIn(b"Identified Risk Reasons", res_risk.data)

        # 5. Attendance tab
        res_att = self.client.get("/admin/reports?report_type=attendance")
        self.assertEqual(res_att.status_code, 200)
        self.assertIn(b"Attendance", res_att.data)

    def test_02_admin_csv_and_pdf_exports(self):
        """Admin can export filter-compliant CSV and PDF."""
        with self.client.session_transaction() as sess:
            sess["admin_logged_in"] = True

        # CSV Export
        res_csv = self.client.get("/admin/reports/export-csv?semester=3&report_type=performance")
        self.assertEqual(res_csv.status_code, 200)
        self.assertEqual(res_csv.mimetype, "text/csv")
        self.assertIn('filename="admin_performance_report_sem3.csv"', res_csv.headers.get("Content-Disposition", ""))
        csv_text = res_csv.data.decode("utf-8")
        self.assertIn("Roll_No,Student_Name,Semester,Subject", csv_text)

        # PDF Export
        res_pdf = self.client.get("/admin/reports/export-pdf?semester=3&report_type=overall")
        self.assertEqual(res_pdf.status_code, 200)
        self.assertEqual(res_pdf.mimetype, "application/pdf")
        self.assertTrue(res_pdf.data.startswith(b"%PDF"))
        self.assertGreater(len(res_pdf.data), 5000)

    # =========================================================================
    # 2. TEACHER REPORTS TESTS
    # =========================================================================

    def test_03_teacher_assigned_subject_report(self):
        """Teacher can access reports for assigned subject/semester."""
        # Teacher 'teacher001' is assigned 'Operating Systems' in Semester 3
        with self.client.session_transaction() as sess:
            sess["teacher_logged_in"] = True
            sess["teacher_id"] = "T001"
            sess["teacher_username"] = "teacher001"
            sess["teacher_name"] = "Amit Patil"

        res = self.client.get("/teacher/reports?subject=Operating+Systems&semester=3")
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"Operating Systems", res.data)
        self.assertIn(b"Semester 3", res.data)
        self.assertIn(b"CLASS AVERAGE MARKS", res.data)

        # CSV export
        res_csv = self.client.get("/teacher/reports/export-csv?subject=Operating+Systems&semester=3")
        self.assertEqual(res_csv.status_code, 200)
        self.assertEqual(res_csv.mimetype, "text/csv")
        self.assertIn(b"Roll_No,Student_Name,Internal,External,Total,Grade,Attendance,Status", res_csv.data)

        # PDF export
        res_pdf = self.client.get("/teacher/reports/export-pdf?subject=Operating+Systems&semester=3")
        self.assertEqual(res_pdf.status_code, 200)
        self.assertEqual(res_pdf.mimetype, "application/pdf")
        self.assertTrue(res_pdf.data.startswith(b"%PDF"))

    def test_04_teacher_unauthorized_subject_blocked(self):
        """Teacher accessing an unassigned subject is blocked with HTTP 403."""
        with self.client.session_transaction() as sess:
            sess["teacher_logged_in"] = True
            sess["teacher_id"] = "T001"
            sess["teacher_username"] = "teacher001"
            sess["teacher_name"] = "Amit Patil"

        # teacher001 is NOT assigned to "Communication Skills" (Semester 1)
        res = self.client.get("/teacher/reports?subject=Communication+Skills&semester=1")
        self.assertEqual(res.status_code, 403)

        # CSV export for unassigned subject blocked
        res_csv = self.client.get("/teacher/reports/export-csv?subject=Communication+Skills&semester=1")
        self.assertEqual(res_csv.status_code, 403)

        # PDF export for unassigned subject blocked
        res_pdf = self.client.get("/teacher/reports/export-pdf?subject=Communication+Skills&semester=1")
        self.assertEqual(res_pdf.status_code, 403)

    # =========================================================================
    # 3. STUDENT REPORT TESTS
    # =========================================================================

    def test_05_student_own_report_preview_and_exports(self):
        """Student can view own report with all required sections and export."""
        with self.client.session_transaction() as sess:
            sess["student_logged_in"] = True
            sess["student_roll"] = "IT2024001"
            sess["student_name"] = "Vidhi Sagar"

        res = self.client.get("/student/report")
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"My Academic Report", res.data)
        self.assertIn(b"Vidhi Sagar", res.data)
        self.assertIn(b"IT2024001", res.data)
        self.assertIn(b"Academic Performance", res.data)
        self.assertIn(b"Attendance Compliance", res.data)
        self.assertIn(b"Academic Progression History", res.data)
        self.assertIn(b"AI Performance Outlook", res.data)
        self.assertIn(b"Personalized Improvement Plan Summary", res.data)

        # CSV Export
        res_csv = self.client.get("/student/report/export-csv")
        self.assertEqual(res_csv.status_code, 200)
        self.assertEqual(res_csv.mimetype, "text/csv")
        self.assertIn('filename="student_academic_report_IT2024001.csv"', res_csv.headers.get("Content-Disposition", ""))
        self.assertIn(b"STUDENT ACADEMIC REPORT", res_csv.data)
        self.assertIn(b"IT2024001", res_csv.data)

        # PDF Export
        res_pdf = self.client.get("/student/report/export-pdf")
        self.assertEqual(res_pdf.status_code, 200)
        self.assertEqual(res_pdf.mimetype, "application/pdf")
        self.assertTrue(res_pdf.data.startswith(b"%PDF"))
        self.assertGreater(len(res_pdf.data), 8000)

    # =========================================================================
    # 4. SECURITY & CROSS-ROLE AUTHORIZATION (Part 31)
    # =========================================================================

    def test_06_student_cross_student_access_blocked(self):
        """Student A attempting to access Student B report must be blocked with HTTP 403."""
        with self.client.session_transaction() as sess:
            sess["student_logged_in"] = True
            sess["student_roll"] = "IT2024001"
            sess["student_name"] = "Vidhi Sagar"

        # Attempting to view IT2024002 report
        res = self.client.get("/student/report?student=IT2024002")
        self.assertEqual(res.status_code, 403)

        # Attempting to export IT2024002 CSV
        res_csv = self.client.get("/student/report/export-csv?student=IT2024002")
        self.assertEqual(res_csv.status_code, 403)

        # Attempting to export IT2024002 PDF
        res_pdf = self.client.get("/student/report/export-pdf?student=IT2024002")
        self.assertEqual(res_pdf.status_code, 403)

    def test_07_student_cannot_access_admin_or_teacher_reports(self):
        """Student attempting to access admin or teacher reports must be blocked with HTTP 403."""
        with self.client.session_transaction() as sess:
            sess["student_logged_in"] = True
            sess["student_roll"] = "IT2024001"

        res_admin = self.client.get("/admin/reports")
        self.assertEqual(res_admin.status_code, 403)

        res_admin_csv = self.client.get("/admin/reports/export-csv")
        self.assertEqual(res_admin_csv.status_code, 403)

        res_teacher = self.client.get("/teacher/reports?subject=Operating+Systems&semester=3")
        self.assertEqual(res_teacher.status_code, 403)

        res_teacher_csv = self.client.get("/teacher/reports/export-csv?subject=Operating+Systems&semester=3")
        self.assertEqual(res_teacher_csv.status_code, 403)

    def test_08_teacher_cannot_access_admin_reports(self):
        """Teacher attempting to access admin reports must be blocked with HTTP 403."""
        with self.client.session_transaction() as sess:
            sess["teacher_logged_in"] = True
            sess["teacher_username"] = "teacher001"

        res_admin = self.client.get("/admin/reports")
        self.assertEqual(res_admin.status_code, 403)

        res_admin_csv = self.client.get("/admin/reports/export-csv")
        self.assertEqual(res_admin_csv.status_code, 403)

        res_admin_pdf = self.client.get("/admin/reports/export-pdf")
        self.assertEqual(res_admin_pdf.status_code, 403)

    # =========================================================================
    # 5. DATA CONSISTENCY CHECK (Part 29)
    # =========================================================================

    def test_09_data_consistency_dashboard_vs_reports(self):
        """Verify complete metric consistency between dashboards and report services."""
        # Admin Dashboard KPIs vs Admin Report Data
        kpis_db = dashboard_kpis(self.students_df)
        report_data = get_admin_reports_data()
        kpis_rep = report_data["kpis"]

        self.assertEqual(kpis_db["total_students"], kpis_rep["total_students"])
        self.assertEqual(kpis_db["average_attendance"], kpis_rep["average_attendance"])
        self.assertEqual(kpis_db["average_sgpi"], kpis_rep["average_sgpi"])
        self.assertEqual(kpis_db["at_risk"], kpis_rep["at_risk_count"])
        self.assertEqual(kpis_db["honors"], kpis_rep["top_performers"])

        # Student Dashboard metrics vs Student Report Data
        roll = "IT2024001"
        detail = get_student_detail(roll)
        stu_rep = get_student_report_data(roll)

        self.assertEqual(detail["student"]["SGPI"], stu_rep["overall_summary"]["sgpi"])
        self.assertEqual(detail["student"]["Attendance"], stu_rep["overall_summary"]["attendance"])
        self.assertEqual(detail["average_marks"], stu_rep["overall_summary"]["average_marks"])
        self.assertEqual(detail["attendance_status"], stu_rep["attendance_status"])
        self.assertEqual(len(detail["subjects_list"]), len(stu_rep["academic_performance"]))


if __name__ == "__main__":
    unittest.main()
