"""Flask routes and API endpoints for AI Student & Study Helper.

Blueprint: ai_helper_bp
"""

import os
import tempfile
from pathlib import Path
from flask import (
    Blueprint,
    render_template,
    request,
    jsonify,
    session,
    redirect,
    url_for,
    flash
)

from utils.data_loader import get_student_detail
from ai_assistant.file_processor import process_uploaded_document, MAX_FILE_SIZE_BYTES
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

ai_helper_bp = Blueprint("ai_helper", __name__)

# Temporary in-memory cache for uploaded documents per session token
_DOCUMENT_STORE = {}


def _get_session_roll():
    """Verify and retrieve logged-in student roll."""
    if not session.get("student_logged_in"):
        return None
    return session.get("student_roll")


# ======================================================================
# 1. Full Page View: AI Student & Study Helper
# ======================================================================

@ai_helper_bp.route("/student/ai-helper", methods=["GET"])
def ai_helper_page():
    """Dedicated interactive AI Student & Study Helper page."""
    if not session.get("student_logged_in"):
        if session.get("admin_logged_in"):
            flash("AI Student Helper is customized for student accounts.", "info")
            return redirect(url_for("home"))
        if session.get("teacher_logged_in"):
            flash("AI Student Helper is customized for student accounts.", "info")
            return redirect(url_for("teacher_dashboard"))
        flash("Please log in as a student to access the AI Helper.", "warning")
        return redirect(url_for("login"))

    roll = session.get("student_roll")
    detail = get_student_detail(roll)
    if not detail:
        flash("Student profile could not be verified.", "danger")
        return redirect(url_for("login"))

    student_ctx = get_student_context_dict(roll)

    return render_template(
        "ai_helper.html",
        student=detail["student"],
        student_ctx=student_ctx,
        roll=roll,
        page_title="Academic Intelligence | AI Student & Study Helper"
    )


# ======================================================================
# 2. JSON API: Student Performance Advisor Query
# ======================================================================

@ai_helper_bp.route("/api/ai/student-query", methods=["POST"])
def api_student_query():
    """Process question about student's own academic performance."""
    roll = _get_session_roll()
    if not roll:
        return jsonify({"success": False, "error": "Unauthorized. Please log in as a student."}), 401

    data = request.get_json(silent=True) or request.form
    query = data.get("query", "").strip()

    if not query:
        return jsonify({"success": False, "error": "Please provide a valid question."}), 400

    result = answer_student_academic_query(roll, query)
    return jsonify(result)


# ======================================================================
# 3. JSON API: Study Material Upload
# ======================================================================

@ai_helper_bp.route("/api/ai/study/upload", methods=["POST"])
def api_study_upload():
    """Upload and parse study material (PDF, DOCX, TXT, Images)."""
    roll = _get_session_roll()
    if not roll:
        return jsonify({"success": False, "error": "Unauthorized. Please log in as a student."}), 401

    if "file" not in request.files:
        return jsonify({"success": False, "error": "No file was uploaded."}), 400

    file = request.files["file"]
    if not file or file.filename.strip() == "":
        return jsonify({"success": False, "error": "Please select a valid file to upload."}), 400

    # Save to temp directory safely
    temp_dir = Path(tempfile.gettempdir()) / "academic_ai_uploads"
    temp_dir.mkdir(parents=True, exist_ok=True)
    temp_path = temp_dir / f"{roll}_{file.filename}"

    try:
        file.save(str(temp_path))
        proc_result = process_uploaded_document(temp_path)

        # Clean up temp file immediately after extraction
        if temp_path.exists():
            temp_path.unlink()

        if not proc_result.get("success"):
            return jsonify({
                "success": False,
                "error": proc_result.get("error", "Failed to process document.")
            }), 400

        # Store in session document cache
        orig_name = Path(file.filename).name
        doc_data = {
            "filename": orig_name,
            "text": proc_result.get("text", ""),
            "file_type": proc_result.get("file_type", "Document"),
            "page_count": proc_result.get("page_count", 1),
            "filesize_kb": proc_result.get("filesize_kb", 0)
        }
        _DOCUMENT_STORE[roll] = doc_data

        preview_text = doc_data["text"][:350] + ("..." if len(doc_data["text"]) > 350 else "")

        return jsonify({
            "success": True,
            "filename": orig_name,
            "file_type": doc_data["file_type"],
            "page_count": doc_data["page_count"],
            "filesize_kb": doc_data["filesize_kb"],
            "word_count": len(doc_data["text"].split()),
            "preview": preview_text
        })

    except Exception as e:
        if temp_path.exists():
            temp_path.unlink()
        return jsonify({"success": False, "error": f"Upload processing error: {str(e)}"}), 500


# ======================================================================
# 4. JSON API: Execute Study Action
# ======================================================================

@ai_helper_bp.route("/api/ai/study/action", methods=["POST"])
def api_study_action():
    """Execute action on loaded study material (summarize, explain, mcqs, five_mark, quiz, ask)."""
    roll = _get_session_roll()
    if not roll:
        return jsonify({"success": False, "error": "Unauthorized. Please log in as a student."}), 401

    doc = _DOCUMENT_STORE.get(roll)
    if not doc or not doc.get("text"):
        return jsonify({
            "success": False,
            "error": "No study material is currently loaded. Please upload notes, a question paper, or a document first."
        }), 400

    data = request.get_json(silent=True) or request.form
    action = data.get("action", "summarize").strip().lower()
    doc_text = doc["text"]
    filename = doc["filename"]

    if action == "summarize":
        res = summarize_study_material(doc_text, filename)
    elif action in ["explain", "explain_simply"]:
        res = explain_simply_study_material(doc_text, filename)
    elif action in ["mcq", "mcqs", "generate_mcqs"]:
        res = generate_mcqs_study_material(doc_text, filename)
    elif action in ["five_mark", "5_mark", "generate_five_mark"]:
        res = generate_five_mark_answers_study_material(doc_text, filename)
    elif action in ["quiz", "quiz_me"]:
        res = generate_interactive_quiz(doc_text, filename)
    elif action in ["ask", "ask_questions", "question"]:
        user_q = data.get("question", "").strip()
        if not user_q:
            return jsonify({"success": False, "error": "Please provide a question about the document."}), 400
        res = answer_custom_question_on_material(doc_text, filename, user_q)
    else:
        return jsonify({"success": False, "error": f"Unknown study action '{action}'."}), 400

    return jsonify(res)


# ======================================================================
# 5. JSON API: Quiz Evaluation
# ======================================================================

@ai_helper_bp.route("/api/ai/study/quiz-submit", methods=["POST"])
def api_quiz_submit():
    """Evaluate single question response during interactive quiz."""
    roll = _get_session_roll()
    if not roll:
        return jsonify({"success": False, "error": "Unauthorized."}), 401

    data = request.get_json(silent=True) or request.form
    selected_idx = data.get("selected_index")
    correct_idx = data.get("correct_index")
    explanation = data.get("explanation", "")
    correct_answer = data.get("correct_answer", "")

    try:
        is_correct = int(selected_idx) == int(correct_idx)
    except (ValueError, TypeError):
        is_correct = False

    return jsonify({
        "success": True,
        "is_correct": is_correct,
        "correct_answer": correct_answer,
        "explanation": explanation
    })


# ======================================================================
# 6. JSON API: Clear Document Session
# ======================================================================

@ai_helper_bp.route("/api/ai/study/clear", methods=["POST"])
def api_study_clear():
    """Clear currently loaded study material."""
    roll = _get_session_roll()
    if roll and roll in _DOCUMENT_STORE:
        del _DOCUMENT_STORE[roll]
    return jsonify({"success": True, "message": "Study session cleared."})
