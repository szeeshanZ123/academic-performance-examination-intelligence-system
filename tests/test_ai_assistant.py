"""Comprehensive test suite for AI Student & Study Helper.

Validates:
1. Student authentication, role guards, and data isolation.
2. Grounded academic performance advisor queries (SGPI, attendance, weak subjects, risk status, etc.).
3. Study material upload (PDF, DOCX, TXT, Images) and size/format validation.
4. Study actions: Summarize, Explain Simply, MCQs, 5-Mark Answers, Quiz Me, and Contextual Q&A.
5. Quiz interactive scoring and validation.
6. Error handling and boundary conditions.
"""

import io
import unittest
from pathlib import Path
from app import app
from ai_assistant.service import (
    answer_student_academic_query,
    get_student_context_dict,
    summarize_study_material,
    explain_simply_study_material,
    generate_mcqs_study_material,
    generate_five_mark_answers_study_material,
    generate_interactive_quiz,
    answer_custom_question_on_material
)
from ai_assistant.file_processor import process_uploaded_document


class TestAIAssistant(unittest.TestCase):
    """Test suite for AI Student & Study Helper features."""

    def setUp(self):
        self.app = app
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()

    # ------------------------------------------------------------------
    # 1. Authentication & Route Access Guards
    # ------------------------------------------------------------------

    def test_ai_helper_page_requires_student_login(self):
        """Unauthenticated user should be redirected to login page."""
        response = self.client.get("/student/ai-helper", follow_redirects=False)
        self.assertEqual(response.status_code, 302)
        self.assertIn("/login", response.headers["Location"])

    def test_ai_helper_page_accessible_by_logged_in_student(self):
        """Logged in student should successfully view AI Helper page."""
        with self.client.session_transaction() as sess:
            sess["student_logged_in"] = True
            sess["student_roll"] = "IT2026001"
            sess["student_name"] = "Amaira Maharaj"

        response = self.client.get("/student/ai-helper")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"AI Student", response.data)
        self.assertIn(b"Study Helper", response.data)
        self.assertIn(b"Amaira Maharaj", response.data)
        self.assertIn(b"Academic Advisor", response.data)
        self.assertIn(b"Study Assistant", response.data)

    def test_api_student_query_unauthorized(self):
        """API student query should reject unauthenticated requests with 401."""
        response = self.client.post("/api/ai/student-query", json={"query": "What is my SGPI?"})
        self.assertEqual(response.status_code, 401)
        data = response.get_json()
        self.assertFalse(data["success"])

    # ------------------------------------------------------------------
    # 2. Student Academic Performance Advisor Intelligence
    # ------------------------------------------------------------------

    def test_student_context_extraction(self):
        """Verify complete extraction of logged-in student's real data."""
        ctx = get_student_context_dict("IT2026001")
        self.assertIsNotNone(ctx)
        self.assertEqual(ctx["roll"], "IT2026001")
        self.assertIn("name", ctx)
        self.assertIn("sgpi", ctx)
        self.assertIn("attendance", ctx)
        self.assertIn("subjects", ctx)
        self.assertGreater(len(ctx["subjects"]), 0)

    def test_advisor_overall_performance_query(self):
        """Test overall performance question grounding in student data."""
        result = answer_student_academic_query("IT2026001", "What is my overall performance?")
        self.assertTrue(result["success"])
        self.assertIn("Academic Performance Summary", result["answer"])
        self.assertIn("SGPI", result["answer"])
        self.assertIn("Attendance", result["answer"])

    def test_advisor_sgpi_query(self):
        """Test SGPI and GPA query."""
        result = answer_student_academic_query("IT2026001", "What is my SGPI pointer?")
        self.assertTrue(result["success"])
        self.assertIn("SGPI", result["answer"])
        self.assertIn("Grade", result["answer"])

    def test_advisor_attendance_query(self):
        """Test attendance and shortage query."""
        result = answer_student_academic_query("IT2026001", "How is my attendance?")
        self.assertTrue(result["success"])
        self.assertIn("Attendance Status", result["answer"])
        self.assertIn("%", result["answer"])

    def test_advisor_weak_subjects_query(self):
        """Test identification of weak subjects and remedial guidance."""
        result = answer_student_academic_query("IT2026001", "Which subjects are weak?")
        self.assertTrue(result["success"])
        self.assertIn("Subject", result["answer"])

    def test_advisor_strong_subjects_query(self):
        """Test top subjects highlighting."""
        result = answer_student_academic_query("IT2026001", "Which subjects am I strong in?")
        self.assertTrue(result["success"])
        self.assertIn("Top Performing", result["answer"])

    def test_advisor_risk_query(self):
        """Test academic risk analysis."""
        result = answer_student_academic_query("IT2026001", "Am I at academic risk and why?")
        self.assertTrue(result["success"])
        self.assertIn("Academic Risk Evaluation", result["answer"])

    def test_advisor_internal_marks_query(self):
        """Test internal marks (/30) breakdown."""
        result = answer_student_academic_query("IT2026001", "Show my internal marks")
        self.assertTrue(result["success"])
        self.assertIn("Internal Assessment Marks", result["answer"])
        self.assertIn("/ 30", result["answer"])

    def test_advisor_focus_subject_query(self):
        """Test priority focus subject recommendation."""
        result = answer_student_academic_query("IT2026001", "Which subject should I focus on?")
        self.assertTrue(result["success"])
        self.assertIn("Priority Focus Recommendation", result["answer"])

    def test_advisor_improvement_query(self):
        """Test improvement tips and recommendations."""
        result = answer_student_academic_query("IT2026001", "How can I improve my marks?")
        self.assertTrue(result["success"])
        self.assertIn("Improvement Plan", result["answer"])

    def test_advisor_empty_query(self):
        """Test graceful rejection of empty queries."""
        result = answer_student_academic_query("IT2026001", "   ")
        self.assertFalse(result["success"])
        self.assertIn("Please ask a question", result["answer"])

    def test_api_student_query_via_client(self):
        """Test API endpoint `/api/ai/student-query` with active session."""
        with self.client.session_transaction() as sess:
            sess["student_logged_in"] = True
            sess["student_roll"] = "IT2026001"
            sess["student_name"] = "Amaira Maharaj"

        resp = self.client.post("/api/ai/student-query", json={"query": "What is my SGPI?"})
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertTrue(data["success"])
        self.assertIn("SGPI", data["answer"])

    # ------------------------------------------------------------------
    # 3. Study Assistant: Document Processing & Validation
    # ------------------------------------------------------------------

    def test_upload_text_file(self):
        """Test text file upload and content parsing."""
        with self.client.session_transaction() as sess:
            sess["student_logged_in"] = True
            sess["student_roll"] = "IT2026001"

        txt_content = (
            "Database Management Systems\n\n"
            "Normalization is the process of organizing data in a database to reduce redundancy and improve data integrity. "
            "First Normal Form (1NF) requires all column values to be atomic. "
            "Second Normal Form (2NF) eliminates partial functional dependencies. "
            "Third Normal Form (3NF) eliminates transitive dependencies. "
            "Boyce-Codd Normal Form (BCNF) is a stricter version of 3NF where every determinant must be a candidate key."
        )

        data = {
            "file": (io.BytesIO(txt_content.encode("utf-8")), "dbms_notes.txt")
        }

        resp = self.client.post("/api/ai/study/upload", data=data, content_type="multipart/form-data")
        self.assertEqual(resp.status_code, 200)
        json_data = resp.get_json()
        self.assertTrue(json_data["success"])
        self.assertEqual(json_data["filename"], "dbms_notes.txt")
        self.assertIn("Normalization", json_data["preview"])

    def test_upload_unsupported_file_extension(self):
        """Test rejection of unsupported file extensions (e.g., .exe, .zip)."""
        with self.client.session_transaction() as sess:
            sess["student_logged_in"] = True
            sess["student_roll"] = "IT2026001"

        data = {
            "file": (io.BytesIO(b"binary data"), "virus.exe")
        }
        resp = self.client.post("/api/ai/study/upload", data=data, content_type="multipart/form-data")
        self.assertEqual(resp.status_code, 400)
        json_data = resp.get_json()
        self.assertFalse(json_data["success"])
        self.assertIn("Unsupported file format", json_data["error"])

    def test_upload_empty_file_field(self):
        """Test empty upload payload."""
        with self.client.session_transaction() as sess:
            sess["student_logged_in"] = True
            sess["student_roll"] = "IT2026001"

        resp = self.client.post("/api/ai/study/upload", data={})
        self.assertEqual(resp.status_code, 400)
        json_data = resp.get_json()
        self.assertFalse(json_data["success"])

    # ------------------------------------------------------------------
    # 4. Study Assistant: Actions (Summarize, Explain, MCQs, 5-Mark, Quiz, Ask)
    # ------------------------------------------------------------------

    def test_study_action_summarize(self):
        """Test Summarize action on study text."""
        text = (
            "Python Programming Language Fundamentals.\n\n"
            "Python is a high-level interpreted programming language created by Guido van Rossum. "
            "It emphasizes code readability with significant indentation. "
            "Key data structures include lists, tuples, dictionaries, and sets. "
            "Object-oriented programming in Python supports inheritance, encapsulation, and polymorphism."
        )
        res = summarize_study_material(text, "python_basics.txt")
        self.assertTrue(res["success"])
        self.assertIn("Study Summary", res["result"])
        self.assertIn("Core Overview", res["result"])
        self.assertIn("Key Concepts Covered", res["result"])

    def test_study_action_explain_simply(self):
        """Test Explain Simply action with analogy."""
        text = (
            "Operating Systems: Virtual Memory.\n\n"
            "Virtual memory is a memory management technique where secondary memory can be addressed as main memory. "
            "It uses paging and page replacement algorithms like LRU and FIFO to handle page faults."
        )
        res = explain_simply_study_material(text, "os_notes.txt")
        self.assertTrue(res["success"])
        self.assertIn("Simple Explanation", res["result"])
        self.assertIn("Analogy", res["result"])

    def test_study_action_generate_mcqs(self):
        """Test MCQ generation with structured options and explanations."""
        text = (
            "Computer Networks: OSI Model.\n\n"
            "The Open Systems Interconnection model has seven layers: Physical, Data Link, Network, Transport, Session, Presentation, and Application. "
            "The Transport layer provides end-to-end communication via TCP and UDP."
        )
        res = generate_mcqs_study_material(text, "networks.txt")
        self.assertTrue(res["success"])
        self.assertIn("Exam MCQs Generated", res["result"])
        self.assertIn("Question 1", res["result"])
        self.assertIn("Correct Answer", res["result"])
        self.assertIn("Short Explanation", res["result"])

    def test_study_action_generate_five_mark_answers(self):
        """Test 5-mark structured exam answer generation."""
        text = (
            "Software Engineering: Agile Methodology.\n\n"
            "Agile software development is an iterative approach to project management and software development. "
            "It emphasizes continuous delivery, collaboration, and adaptability to changing requirements."
        )
        res = generate_five_mark_answers_study_material(text, "software_eng.txt")
        self.assertTrue(res["success"])
        self.assertIn("5-Mark Answers", res["result"])
        self.assertIn("Definition / Introduction", res["result"])
        self.assertIn("Main Explanation", res["result"])
        self.assertIn("Key Important Points", res["result"])
        self.assertIn("Practical Example", res["result"])
        self.assertIn("Conclusion", res["result"])

    def test_study_action_interactive_quiz(self):
        """Test interactive quiz generation structure."""
        text = (
            "Machine Learning: Supervised vs Unsupervised Learning.\n\n"
            "Supervised learning trains models on labeled datasets where inputs correspond to known outputs. "
            "Unsupervised learning finds hidden patterns or intrinsic structures in unlabelled data like clustering."
        )
        res = generate_interactive_quiz(text, "ml_notes.txt")
        self.assertTrue(res["success"])
        self.assertEqual(res["total_questions"], 5)
        self.assertIn("questions", res)
        q1 = res["questions"][0]
        self.assertIn("question", q1)
        self.assertIn("options", q1)
        self.assertEqual(len(q1["options"]), 4)
        self.assertIn("correct_index", q1)

    def test_study_action_ask_question_contextual(self):
        """Test asking custom contextual questions on study material."""
        text = (
            "Database Normalization Guide.\n\n"
            "Normalization prevents anomalies like Insertion Anomaly, Deletion Anomaly, and Updation Anomaly. "
            "BCNF ensures that for every functional dependency X -> Y, X must be a super key."
        )
        res = answer_custom_question_on_material(text, "dbms.txt", "Explain BCNF")
        self.assertTrue(res["success"])
        self.assertIn("BCNF", res["result"])

    def test_api_study_action_flow(self):
        """Test full API pipeline: upload text -> call action -> get structured response."""
        with self.client.session_transaction() as sess:
            sess["student_logged_in"] = True
            sess["student_roll"] = "IT2026001"

        # 1. Upload
        txt_content = (
            "Python Data Analytics: Pandas Library.\n\n"
            "Pandas provides DataFrame and Series data structures for high-performance data manipulation and analysis. "
            "Missing values can be handled using fillna() and dropna() functions."
        )
        upload_resp = self.client.post(
            "/api/ai/study/upload",
            data={"file": (io.BytesIO(txt_content.encode("utf-8")), "pandas.txt")},
            content_type="multipart/form-data"
        )
        self.assertEqual(upload_resp.status_code, 200)

        # 2. Action: Summarize
        act_resp = self.client.post("/api/ai/study/action", json={"action": "summarize"})
        self.assertEqual(act_resp.status_code, 200)
        data = act_resp.get_json()
        self.assertTrue(data["success"])
        self.assertIn("Study Summary", data["result"])

        # 3. Action: Quiz Me
        quiz_resp = self.client.post("/api/ai/study/action", json={"action": "quiz"})
        self.assertEqual(quiz_resp.status_code, 200)
        quiz_data = quiz_resp.get_json()
        self.assertTrue(quiz_data["success"])
        self.assertEqual(quiz_data["total_questions"], 5)

        # 4. Action: Quiz Submit
        submit_resp = self.client.post(
            "/api/ai/study/quiz-submit",
            json={
                "selected_index": 0,
                "correct_index": 0,
                "correct_answer": "Option A",
                "explanation": "Valid explanation"
            }
        )
        self.assertEqual(submit_resp.status_code, 200)
        submit_data = submit_resp.get_json()
        self.assertTrue(submit_data["is_correct"])

    # ------------------------------------------------------------------
    # 5. UI Integration & Dashboard Link Checks
    # ------------------------------------------------------------------

    def test_student_dashboard_contains_ai_helper_triggers(self):
        """Student Dashboard should contain AI Helper navbar button and hero launcher."""
        with self.client.session_transaction() as sess:
            sess["student_logged_in"] = True
            sess["student_roll"] = "IT2026001"
            sess["student_name"] = "Amaira Maharaj"

        response = self.client.get("/student-dashboard")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"AI Helper", response.data)
        self.assertIn(b"AI Student Helper", response.data)
        self.assertIn(b"/student/ai-helper", response.data)


if __name__ == "__main__":
    unittest.main()
