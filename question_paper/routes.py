"""Flask routes and views for Question Paper Intelligence.

Provides upload, validation, security checks, NLP analysis invocation,
and dashboard rendering for Admins and Teachers.
"""

import os
import tempfile
from pathlib import Path
from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    session,
    flash,
    jsonify,
    current_app
)
from werkzeug.utils import secure_filename

from utils.data_loader import (
    SEMESTER_SUBJECTS,
    get_admin_info,
    get_teacher_assignments,
    get_teacher_info
)
from .extractor import extract_text_from_file
from .parser import parse_question_paper
from .analyzer import analyze_question_paper


question_paper_bp = Blueprint(
    "question_paper",
    __name__,
    template_folder="../templates"
)

ALLOWED_EXTENSIONS = {".pdf", ".docx", ".txt"}
MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB


def check_auth():
    """Verify session is an authenticated Admin or Teacher. Reject Students or anonymous."""
    if session.get("student_logged_in"):
        flash("Access Denied: Students are not authorized to access Question Paper Intelligence.", "danger")
        return "student_blocked"
    if session.get("admin_logged_in"):
        return "admin"
    if session.get("teacher_logged_in"):
        return "teacher"
    return "unauthenticated"


def get_user_context():
    """Retrieve role-specific user metadata and available subject/semester options."""
    role = check_auth()
    if role == "admin":
        admin_info = get_admin_info()
        return {
            "role": "admin",
            "user_name": session.get("admin_name", admin_info.get("Teacher_Name", "Administrator")),
            "user_id": session.get("admin_id", "Admin"),
            "semester_subjects": SEMESTER_SUBJECTS,
            "assignments": []
        }
    elif role == "teacher":
        username = session.get("teacher_username")
        assignments = get_teacher_assignments(username)
        return {
            "role": "teacher",
            "user_name": session.get("teacher_name", "Teacher"),
            "user_id": session.get("teacher_id", "Teacher"),
            "semester_subjects": {},
            "assignments": assignments
        }
    return None


@question_paper_bp.route("/question-paper", methods=["GET"])
def index():
    """Display the Question Paper Intelligence upload portal and initial state."""
    auth_status = check_auth()
    if auth_status == "student_blocked":
        return redirect(url_for("student_dashboard"))
    if auth_status == "unauthenticated":
        flash("Please log in as an Admin or Teacher to access Question Paper Intelligence.", "warning")
        return redirect(url_for("login"))

    ctx = get_user_context()
    return render_template(
        "question_paper.html",
        user_role=ctx["role"],
        user_name=ctx["user_name"],
        user_id=ctx["user_id"],
        semester_subjects=ctx["semester_subjects"],
        assignments=ctx["assignments"],
        has_analysis=False,
        result=None,
        selected_subject="",
        selected_semester=""
    )


@question_paper_bp.route("/question-paper/analyze", methods=["POST"])
def analyze():
    """Handle paper upload, authorization validation, extraction, and NLP analysis."""
    auth_status = check_auth()
    if auth_status == "student_blocked":
        return redirect(url_for("student_dashboard"))
    if auth_status == "unauthenticated":
        flash("Please log in as an Admin or Teacher to access Question Paper Intelligence.", "warning")
        return redirect(url_for("login"))

    ctx = get_user_context()
    
    # 1. Subject and Semester validation
    req_subject = request.form.get("subject", "").strip()
    req_semester_raw = request.form.get("semester", "").strip()

    try:
        req_semester = int(req_semester_raw)
    except (ValueError, TypeError):
        req_semester = None

    if not req_subject or not req_semester:
        flash("Please select both a valid Subject and Semester for the paper.", "warning")
        return render_template(
            "question_paper.html",
            user_role=ctx["role"],
            user_name=ctx["user_name"],
            user_id=ctx["user_id"],
            semester_subjects=ctx["semester_subjects"],
            assignments=ctx["assignments"],
            has_analysis=False,
            result=None,
            selected_subject=req_subject,
            selected_semester=req_semester_raw
        )

    # 2. Teacher Authorization Check
    if ctx["role"] == "teacher":
        is_assigned = False
        for item in ctx["assignments"]:
            if (item["Subject"].strip().lower() == req_subject.strip().lower()) and (int(item["Semester"]) == req_semester):
                is_assigned = True
                break
        
        if not is_assigned:
            flash(
                f"Authorization Error: You are only authorized to analyze question papers for your assigned courses. "
                f"('{req_subject}' in Semester {req_semester} is not assigned to your account).",
                "danger"
            )
            return render_template(
                "question_paper.html",
                user_role=ctx["role"],
                user_name=ctx["user_name"],
                user_id=ctx["user_id"],
                semester_subjects=ctx["semester_subjects"],
                assignments=ctx["assignments"],
                has_analysis=False,
                result=None,
                selected_subject="",
                selected_semester=""
            )

    # 3. Handle Demo Sample Paper or Uploaded File
    demo_sample = request.form.get("demo_sample", "").strip()
    extracted_data = None
    original_filename = ""

    if demo_sample:
        sample_path = Path(__file__).parent / "samples" / f"{demo_sample}.txt"
        if sample_path.exists():
            original_filename = sample_path.name
            extracted_data = extract_text_from_file(sample_path)
        else:
            flash(f"Sample paper '{demo_sample}' not found.", "warning")

    if not extracted_data:
        if "paper_file" not in request.files:
            flash("No file was selected for upload.", "warning")
            return redirect(url_for("question_paper.index"))

        file = request.files["paper_file"]
        if not file or file.filename == "":
            flash("Please choose a valid file (.pdf, .docx, or .txt).", "warning")
            return redirect(url_for("question_paper.index"))

        original_filename = secure_filename(file.filename)
        file_ext = Path(original_filename).suffix.lower()

        if file_ext not in ALLOWED_EXTENSIONS:
            flash(f"Unsupported file format '{file_ext}'. Allowed formats: PDF (.pdf), Word (.docx), Plain Text (.txt).", "danger")
            return redirect(url_for("question_paper.index"))

        # Save to temporary file for safe processing
        temp_fd, temp_path = tempfile.mkstemp(suffix=file_ext)
        os.close(temp_fd)
        
        try:
            file.save(temp_path)
            # Check file size limit
            if os.path.getsize(temp_path) > MAX_FILE_SIZE_BYTES:
                flash("File exceeds maximum allowed size limit of 10 MB.", "danger")
                return redirect(url_for("question_paper.index"))

            # Extract text
            extracted_data = extract_text_from_file(temp_path)
        finally:
            # Always clean up temporary file
            if os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except Exception:
                    pass

    # 4. Check extraction result
    if not extracted_data or not extracted_data.get("success"):
        error_msg = extracted_data.get("error", "Failed to extract text from document.") if extracted_data else "Extraction failed."
        flash(f"Document Extraction Notice: {error_msg}", "warning" if extracted_data and extracted_data.get("is_scanned") else "danger")
        return render_template(
            "question_paper.html",
            user_role=ctx["role"],
            user_name=ctx["user_name"],
            user_id=ctx["user_id"],
            semester_subjects=ctx["semester_subjects"],
            assignments=ctx["assignments"],
            has_analysis=False,
            result=None,
            is_scanned=extracted_data.get("is_scanned", False) if extracted_data else False,
            extraction_error=error_msg,
            selected_subject=req_subject,
            selected_semester=req_semester
        )

    # 5. Parse questions & marks
    raw_text = extracted_data.get("text", "")
    parsed_info = parse_question_paper(raw_text)

    if not parsed_info.get("success") or parsed_info.get("total_questions", 0) == 0:
        flash("No identifiable questions could be detected. Please ensure questions follow standard numbering (e.g. Q1, 1., a)).", "warning")
        return render_template(
            "question_paper.html",
            user_role=ctx["role"],
            user_name=ctx["user_name"],
            user_id=ctx["user_id"],
            semester_subjects=ctx["semester_subjects"],
            assignments=ctx["assignments"],
            has_analysis=False,
            result=None,
            selected_subject=req_subject,
            selected_semester=req_semester
        )

    # 6. Analyze questions (NLP, TF-IDF topic clustering, Rule classification, Difficulty)
    analysis_result = analyze_question_paper(parsed_info)
    analysis_result["document_meta"] = {
        "filename": original_filename,
        "file_type": extracted_data.get("file_type", "Document"),
        "page_count": extracted_data.get("page_count", 1),
        "subject": req_subject,
        "semester": req_semester
    }

    flash(
        f"Question paper analysis successfully completed for {req_subject} (Semester {req_semester}): "
        f"{analysis_result['kpis']['total_questions']} questions detected.",
        "success"
    )

    return render_template(
        "question_paper.html",
        user_role=ctx["role"],
        user_name=ctx["user_name"],
        user_id=ctx["user_id"],
        semester_subjects=ctx["semester_subjects"],
        assignments=ctx["assignments"],
        has_analysis=True,
        result=analysis_result,
        selected_subject=req_subject,
        selected_semester=req_semester
    )
