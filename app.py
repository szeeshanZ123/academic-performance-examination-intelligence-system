from flask import (
    Flask,
    render_template,
    request,
    redirect,
    jsonify,
    make_response,
    session,
    flash,
    url_for
)

from utils.data_loader import (
    load_data,
    get_admin_info,
    get_semester_subjects,
    get_student_detail,
    load_teachers,
    get_teacher_info,
    get_teacher_assignments
)

from analysis.analytics import (
    dashboard_kpis,
    get_analytics_summary,
    get_teacher_subject_analytics,
    get_student_semester_trend
)

from ml.predictor import (
    predict_external_marks,
    classify_predicted_performance,
    predict_subject_performance,
    get_model_info
)

from question_paper.routes import question_paper_bp


app = Flask(__name__)

# Required for Flask sessions
app.secret_key = "academic-performance-project-secret-key"

# Register Question Paper Intelligence Blueprint
app.register_blueprint(question_paper_bp)


# =========================================================
# HOME
# =========================================================

@app.route("/admin")
@app.route("/admin-dashboard")
@app.route("/")
def home():
    """
    Institutional Admin Dashboard.
    """
    if session.get("student_logged_in"):
        flash("Access Denied: Students are not authorized to view the Admin Dashboard.", "danger")
        return redirect(url_for("student_dashboard"))
    if session.get("teacher_logged_in"):
        flash("Access Denied: Teachers are not authorized to view the Admin Dashboard.", "warning")
        return redirect(url_for("teacher_dashboard"))
    if not session.get("admin_logged_in"):
        return redirect(url_for("login"))

    semester = request.args.get("semester", "").strip()
    risk_filter = request.args.get("risk", "").strip()
    sort_by = request.args.get("sort_by", "").strip()
    sort_order = request.args.get("sort_order", "asc").strip()

    admin_df, students, marks_df, attendance_df, subject_combined = load_data()

    filtered_students = students.copy()

    # -------------------------
    # Semester Filter
    # -------------------------

    if semester:
        try:
            filtered_students = filtered_students[
                filtered_students["Semester"] == int(semester)
            ]
        except ValueError:
            pass

    # -------------------------
    # Risk Filter
    # -------------------------

    if risk_filter == "at_risk":

        filtered_students = filtered_students[
            (filtered_students["Attendance"] < 75)
            | (filtered_students["SGPI"] < 6.0)
        ]

    elif risk_filter == "honors":

        filtered_students = filtered_students[
            filtered_students["SGPI"] >= 8.5
        ]

    # -------------------------
    # Sorting
    # -------------------------

    allowed_sort_columns = [
        "Roll",
        "Name",
        "Semester",
        "SGPI",
        "Attendance"
    ]

    if sort_by in allowed_sort_columns:

        filtered_students = filtered_students.sort_values(
            by=sort_by,
            ascending=(sort_order == "asc")
        )

    # -------------------------
    # KPIs
    # -------------------------

    kpis = dashboard_kpis(filtered_students)

    # -------------------------
    # Analytics
    # -------------------------

    analytics = get_analytics_summary(
        filtered_students,
        marks_df,
        semester
    )

    admin_info = get_admin_info()

    semester_subjects = (
        get_semester_subjects(semester)
        if semester
        else []
    )

    # -------------------------
    # Student Records
    # -------------------------

    student_records = filtered_students.to_dict(
        orient="records"
    )

    # -------------------------
    # Subject Marks
    # -------------------------

    if semester and semester_subjects:

        sem_num = int(semester)

        sem_marks = marks_df[
            marks_df["Semester"] == sem_num
        ]

        pivot = (
            sem_marks
            .pivot(
                index="Roll_No",
                columns="Subject",
                values="Total"
            )
            .to_dict(orient="index")
        )

        for student in student_records:

            roll = student["Roll"]

            student_subj_marks = pivot.get(
                roll,
                {}
            )

            student["subjects"] = {
                subject: student_subj_marks.get(
                    subject,
                    "N/A"
                )
                for subject in semester_subjects
            }

    return render_template(
        "index.html",

        kpis=kpis,

        total_students=kpis["total_students"],
        average_sgpi=kpis["average_sgpi"],
        average_attendance=kpis["average_attendance"],
        at_risk=kpis["at_risk"],
        honors=kpis["honors"],
        pass_rate=kpis["pass_rate"],

        students=student_records,

        admin=admin_info,

        selected_semester=semester,
        selected_risk=risk_filter,

        sort_by=sort_by,
        sort_order=sort_order,

        semester_subjects=semester_subjects,

        subject_averages=analytics["subject_averages"],
        grade_distribution=analytics["grade_distribution"]
    )
@app.route("/student-login", methods=["GET", "POST"])
def student_login():
    return redirect(url_for("login"))

# =========================================================
# AUTHENTICATION (ADMIN, TEACHER, STUDENT)
# =========================================================

@app.route("/login", methods=["GET", "POST"])
def login():
    if session.get("admin_logged_in"):
        return redirect(url_for("home"))
    if session.get("teacher_logged_in"):
        return redirect(url_for("teacher_dashboard"))
    if session.get("student_logged_in"):
        return redirect(url_for("student_dashboard"))

    initial_role = request.args.get("role", "student").strip().lower()
    if initial_role not in ["student", "teacher", "admin"]:
        initial_role = "student"

    if request.method == "POST":
        role = request.form.get("role", "student").strip().lower()
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()

        admin_df, students_df, _, _, _ = load_data()

        if role == "admin":
            admin_df["Username_str"] = admin_df["Username"].astype(str).str.strip()
            admin_df["Teacher_ID_str"] = admin_df["Teacher_ID"].astype(str).str.strip()
            match = admin_df[
                ((admin_df["Username_str"].str.lower() == username.lower()) |
                 (admin_df["Teacher_ID_str"].str.lower() == username.lower())) &
                (admin_df["Password"].astype(str) == password)
            ]
            if match.empty:
                flash("Invalid administrator credentials.", "danger")
                return redirect(url_for("login", role="admin"))

            admin_info = match.iloc[0]
            session.clear()
            session["admin_logged_in"] = True
            session["admin_id"] = str(admin_info["Teacher_ID"])
            session["admin_name"] = str(admin_info["Teacher_Name"])

            flash(f"Welcome, {admin_info['Teacher_Name']}!", "success")
            return redirect(url_for("home"))

        elif role == "teacher":
            teacher_df = load_teachers()
            if teacher_df.empty:
                flash("Teacher database unavailable.", "danger")
                return redirect(url_for("login", role="teacher"))

            teacher_df["Username_str"] = teacher_df["Username"].astype(str).str.strip()
            teacher_df["Teacher_ID_str"] = teacher_df["Teacher_ID"].astype(str).str.strip()
            teacher_df["Password_str"] = teacher_df["Password"].astype(str).str.strip()
            teacher_df["Status_str"] = teacher_df["Status"].astype(str).str.strip().str.capitalize()

            match = teacher_df[
                ((teacher_df["Username_str"].str.lower() == username.lower()) |
                 (teacher_df["Teacher_ID_str"].str.lower() == username.lower())) &
                (teacher_df["Password_str"] == password) &
                (teacher_df["Status_str"] == "Active")
            ]
            if match.empty:
                flash("Invalid teacher credentials or account inactive.", "danger")
                return redirect(url_for("login", role="teacher"))

            teacher_info = match.iloc[0]
            session.clear()
            session["teacher_logged_in"] = True
            session["teacher_id"] = str(teacher_info["Teacher_ID"])
            session["teacher_username"] = str(teacher_info["Username"])
            session["teacher_name"] = str(teacher_info["Teacher_Name"])

            flash(f"Welcome, {teacher_info['Teacher_Name']}!", "success")
            return redirect(url_for("teacher_dashboard"))

        else:  # role == "student"
            students_df["Username_str"] = students_df["Username"].astype(str).str.strip()
            students_df["Roll_str"] = students_df["Roll"].astype(str).str.strip()
            match = students_df[
                ((students_df["Username_str"].str.lower() == username.lower()) |
                 (students_df["Roll_str"].str.lower() == username.lower())) &
                (students_df["Password"].astype(str) == password)
            ]
            if match.empty:
                flash("Invalid student credentials.", "danger")
                return redirect(url_for("login", role="student"))

            student_info = match.iloc[0]
            session.clear()
            session["student_logged_in"] = True
            session["student_roll"] = str(student_info["Roll"])
            session["student_name"] = str(student_info["Name"])

            flash(f"Welcome, {student_info['Name']}!", "success")
            return redirect(url_for("student_dashboard"))

    return render_template("login.html", initial_role=initial_role, page_title="Academic Intelligence | Login")


# =========================================================
# TEACHER AUTHENTICATION & DASHBOARD
# =========================================================

@app.route("/teacher-login", methods=["GET", "POST"])
def teacher_login():
    if session.get("teacher_logged_in"):
        return redirect(url_for("teacher_dashboard"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()

        teacher_df = load_teachers()
        if teacher_df.empty:
            flash("Teacher database is unavailable.", "danger")
            return redirect(url_for("login", role="teacher"))

        teacher_df["Username_str"] = teacher_df["Username"].astype(str).str.strip()
        teacher_df["Teacher_ID_str"] = teacher_df["Teacher_ID"].astype(str).str.strip()
        teacher_df["Password_str"] = teacher_df["Password"].astype(str).str.strip()
        teacher_df["Status_str"] = teacher_df["Status"].astype(str).str.strip().str.capitalize()

        match = teacher_df[
            ((teacher_df["Username_str"].str.lower() == username.lower()) |
             (teacher_df["Teacher_ID_str"].str.lower() == username.lower())) &
            (teacher_df["Password_str"] == password) &
            (teacher_df["Status_str"] == "Active")
        ]

        if match.empty:
            flash("Invalid teacher credentials or account is inactive.", "danger")
            return redirect(url_for("login", role="teacher"))

        teacher_info = match.iloc[0]
        session.clear()
        session["teacher_logged_in"] = True
        session["teacher_id"] = str(teacher_info["Teacher_ID"])
        session["teacher_username"] = str(teacher_info["Username"])
        session["teacher_name"] = str(teacher_info["Teacher_Name"])

        flash(f"Welcome, {teacher_info['Teacher_Name']}!", "success")
        return redirect(url_for("teacher_dashboard"))

    return render_template("login.html", initial_role="teacher", page_title="Academic Intelligence | Teacher Login")


@app.route("/teacher")
@app.route("/teacher-dashboard")
def teacher_dashboard():
    if session.get("student_logged_in"):
        flash("Access Denied: Students are not authorized to view the Teacher Dashboard.", "danger")
        return redirect(url_for("student_dashboard"))
    if not session.get("teacher_logged_in"):
        flash("Please log in as a teacher first.", "warning")
        return redirect(url_for("login"))

    teacher_username = session.get("teacher_username")
    assignments = get_teacher_assignments(teacher_username)

    if not assignments:
        flash("No active teaching assignments found for your account.", "warning")
        return render_template(
            "teacher_dashboard.html",
            teacher_name=session.get("teacher_name"),
            teacher_id=session.get("teacher_id"),
            teacher_email="",
            assignments=[],
            selected_subject="",
            selected_semester="",
            kpis={
                "total_students": 0,
                "average_marks": 0,
                "highest_marks": 0,
                "lowest_marks": 0,
                "average_attendance": 0,
                "pass_percentage": 0,
                "at_risk_count": 0,
                "honors_count": 0
            },
            grade_distribution={},
            marks_distribution={},
            attendance_distribution={},
            at_risk_students=[],
            students=[]
        )

    # Requested Subject & Semester
    req_subject = request.args.get("subject", "").strip()
    req_semester = request.args.get("semester", "").strip()

    # Security / Access Control Check:
    # Verify requested (subject, semester) against teacher's assigned subjects
    selected_assignment = None
    if req_subject and req_semester:
        try:
            req_sem_int = int(req_semester)
        except ValueError:
            req_sem_int = req_semester

        for item in assignments:
            if (item["Subject"].strip().lower() == req_subject.strip().lower()) and (item["Semester"] == req_sem_int):
                selected_assignment = item
                break

    # If requested assignment is invalid or unauthorized, default to first assigned subject
    if not selected_assignment:
        if req_subject or req_semester:
            flash(f"Access Denied: You are not assigned to {req_subject} (Semester {req_semester}). Defaulting to your assigned class.", "warning")
        selected_assignment = assignments[0]

    sel_subject = selected_assignment["Subject"]
    sel_semester = selected_assignment["Semester"]
    teacher_email = selected_assignment.get("Email", "")

    _, students_df, marks_df, attendance_df, _ = load_data()

    analytics_data = get_teacher_subject_analytics(
        sel_subject,
        sel_semester,
        marks_df,
        attendance_df,
        students_df
    )

    return render_template(
        "teacher_dashboard.html",
        teacher_name=session.get("teacher_name"),
        teacher_id=session.get("teacher_id"),
        teacher_email=teacher_email,
        assignments=assignments,
        selected_subject=sel_subject,
        selected_semester=sel_semester,
        kpis=analytics_data["kpis"],
        grade_distribution=analytics_data["grade_distribution"],
        marks_distribution=analytics_data["marks_distribution"],
        attendance_distribution=analytics_data["attendance_distribution"],
        at_risk_students=analytics_data["at_risk_students"],
        students=analytics_data["students"]
    )


@app.route("/teacher-logout")
def teacher_logout():
    session.clear()
    flash("You have been logged out successfully.", "info")
    return redirect(url_for("login"))


# =========================================================
# STUDENT DASHBOARD
# =========================================================

@app.route("/student")
@app.route("/student-dashboard")
def student_dashboard():
    if not session.get("student_logged_in"):
        if session.get("admin_logged_in"):
            return redirect(url_for("home"))
        if session.get("teacher_logged_in"):
            return redirect(url_for("teacher_dashboard"))
        flash("Please login first.", "warning")
        return redirect(url_for("login"))

    roll = session.get("student_roll")
    detail = get_student_detail(roll)

    if not detail:
        session.clear()
        flash("Student record not found.", "danger")
        return redirect(url_for("login"))

    # Generate AI-Based External Marks Predictions for current semester subjects
    predictions = []
    prediction_available = False
    model_info = get_model_info()

    try:
        current_semester = int(detail["student"]["Semester"])
        for subj in detail["subjects_list"]:
            subj_name = str(subj.get("subject", "")).strip()
            int_marks = subj.get("internal")
            att = subj.get("attendance")
            act_ext = subj.get("external")

            # Predict safely using per-subject pipeline
            pred_record = predict_subject_performance(
                internal_marks=int_marks,
                attendance=att,
                semester=current_semester,
                subject=subj_name,
                actual_external=act_ext,
            )
            predictions.append(pred_record)

        if any(p.get("available") for p in predictions):
            prediction_available = True
    except Exception as e:
        app.logger.warning(f"ML prediction error for student {roll}: {e}")
        prediction_available = False

    # Generate Semester Performance & Attendance Trend Analytics
    trend_info = get_student_semester_trend(roll)

    return render_template(
        "student_dashboard.html",
        student=detail["student"],
        subjects_list=detail["subjects_list"],
        strongest_subject=detail["strongest_subject"],
        weakest_subject=detail["weakest_subject"],
        average_marks=detail["average_marks"],
        overall_performance=detail["overall_performance"],
        attendance_status=detail["attendance_status"],
        academic_risk=detail["academic_risk"],
        recommendations=detail["recommendations"],
        predictions=predictions,
        prediction_available=prediction_available,
        model_info=model_info,
        trend_summary=trend_info["summary"],
        trend_labels=trend_info["labels"],
        sgpi_trend=trend_info["sgpi_trend"],
        attendance_trend=trend_info["attendance_trend"],
        has_multiple_semesters=trend_info["has_multiple_semesters"],
    )

# =========================================================
# LOGOUT
# =========================================================

@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out successfully.", "info")
    return redirect(url_for("login"))

@app.route("/student-logout")
def student_logout():
    session.clear()
    flash("You have been logged out successfully.", "info")
    return redirect(url_for("login"))



# =========================================================
# STUDENT PROFILE
# =========================================================

@app.route("/student/<roll>")
def student_profile(roll):
    if session.get("student_logged_in"):
        if str(session.get("student_roll")).strip().lower() != str(roll).strip().lower():
            flash("Access Denied: Students cannot view other students' profiles.", "danger")
            return redirect(url_for("student_dashboard"))
    elif not session.get("admin_logged_in") and not session.get("teacher_logged_in"):
        flash("Please log in first to view student profiles.", "warning")
        return redirect(url_for("login"))

    detail = get_student_detail(roll)

    if not detail:
        return render_template(
            "search_not_found.html",
            query=str(roll)
        )

    # Generate AI-Based External Marks Predictions for current semester subjects
    predictions = []
    prediction_available = False
    model_info = get_model_info()

    try:
        current_semester = int(detail["student"]["Semester"])
        for subj in detail["subjects_list"]:
            subj_name = str(subj.get("subject", "")).strip()
            int_marks = subj.get("internal")
            att = subj.get("attendance")
            act_ext = subj.get("external")

            # Predict safely using per-subject pipeline
            pred_record = predict_subject_performance(
                internal_marks=int_marks,
                attendance=att,
                semester=current_semester,
                subject=subj_name,
                actual_external=act_ext,
            )
            predictions.append(pred_record)

        if any(p.get("available") for p in predictions):
            prediction_available = True
    except Exception as e:
        app.logger.warning(f"ML prediction error for student profile {roll}: {e}")
        prediction_available = False

    # Generate Semester Performance & Attendance Trend Analytics
    trend_info = get_student_semester_trend(roll)
    admin_info = get_admin_info()

    return render_template(
        "student.html",
        student=detail["student"],
        subjects_list=detail["subjects_list"],
        strongest_subject=detail["strongest_subject"],
        weakest_subject=detail["weakest_subject"],
        average_marks=detail["average_marks"],
        overall_performance=detail["overall_performance"],
        attendance_status=detail["attendance_status"],
        academic_risk=detail["academic_risk"],
        recommendations=detail["recommendations"],
        admin=admin_info,
        predictions=predictions,
        prediction_available=prediction_available,
        model_info=model_info,
        trend_summary=trend_info["summary"],
        trend_labels=trend_info["labels"],
        sgpi_trend=trend_info["sgpi_trend"],
        attendance_trend=trend_info["attendance_trend"],
        has_multiple_semesters=trend_info["has_multiple_semesters"],
    )


# =========================================================
# STUDENT API
# =========================================================

@app.route("/api/student/<roll>")
def student_api(roll):
    if not session.get("admin_logged_in") and not session.get("teacher_logged_in"):
        if not session.get("student_logged_in"):
            return jsonify({"error": "Unauthorized"}), 401
        if str(session.get("student_roll")).strip().lower() != str(roll).strip().lower():
            return jsonify({"error": "Forbidden: Cannot access other student records"}), 403

    detail = get_student_detail(roll)

    if not detail:

        return jsonify({
            "error": "Student not found"
        }), 404

    return jsonify(detail)


# =========================================================
# SEARCH
# =========================================================

@app.route("/search")
def search():
    if not session.get("admin_logged_in"):
        flash("Please log in as an admin first.", "warning")
        return redirect(url_for("login"))

    query = request.args.get(
        "query",
        ""
    ).strip()

    if not query:
        return redirect("/")

    _, students, _, _, _ = load_data()

    # Exact Roll Number
    student = students[
        students["Roll"]
        .astype(str)
        .str.lower()
        == query.lower()
    ]

    # Exact Name
    if student.empty:

        student = students[
            students["Name"]
            .astype(str)
            .str.lower()
            == query.lower()
        ]

    # Partial Name
    if student.empty:

        student = students[
            students["Name"]
            .astype(str)
            .str.contains(
                query,
                case=False,
                na=False,
                regex=False
            )
        ]

    # Partial Roll
    if student.empty:

        student = students[
            students["Roll"]
            .astype(str)
            .str.contains(
                query,
                case=False,
                na=False,
                regex=False
            )
        ]

    if student.empty:

        return render_template(
            "search_not_found.html",
            query=query
        )

    return redirect(
        url_for(
            "student_profile",
            roll=student.iloc[0]["Roll"]
        )
    )


# =========================================================
# EXPORT CSV
# =========================================================

@app.route("/export")
def export_csv():
    if not session.get("admin_logged_in"):
        flash("Please log in as an admin first.", "warning")
        return redirect(url_for("login"))

    semester = request.args.get(
        "semester",
        ""
    ).strip()

    risk_filter = request.args.get(
        "risk",
        ""
    ).strip()

    sort_by = request.args.get(
        "sort_by",
        ""
    ).strip()

    sort_order = request.args.get(
        "sort_order",
        "asc"
    ).strip()

    _, students, _, _, _ = load_data()

    filtered_students = students.copy()

    # Semester
    if semester:

        try:

            filtered_students = filtered_students[
                filtered_students["Semester"]
                == int(semester)
            ]

        except ValueError:
            pass

    # Risk
    if risk_filter == "at_risk":

        filtered_students = filtered_students[
            (filtered_students["Attendance"] < 75)
            |
            (filtered_students["SGPI"] < 6.0)
        ]

    elif risk_filter == "honors":

        filtered_students = filtered_students[
            filtered_students["SGPI"] >= 8.5
        ]

    # Sorting
    allowed_sort_columns = [
        "Roll",
        "Name",
        "Semester",
        "SGPI",
        "Attendance"
    ]

    if sort_by in allowed_sort_columns:

        filtered_students = filtered_students.sort_values(
            by=sort_by,
            ascending=(sort_order == "asc")
        )

    # Export columns
    export_cols = [
        "Roll",
        "Name",
        "Gender",
        "DOB",
        "Email",
        "Phone",
        "Semester",
        "Attendance",
        "SGPI"
    ]

    available_cols = [
        column
        for column in export_cols
        if column in filtered_students.columns
    ]

    csv_data = filtered_students[
        available_cols
    ].to_csv(index=False)

    response = make_response(csv_data)

    filename = (
        f"student_performance_"
        f"sem_{semester if semester else 'all'}.csv"
    )

    response.headers[
        "Content-Disposition"
    ] = f"attachment; filename={filename}"

    response.headers[
        "Content-Type"
    ] = "text/csv"

    return response


# =========================================================
# CACHE CONTROL, SECURITY HEADERS & ERROR HANDLERS
# =========================================================

@app.after_request
def add_security_and_cache_headers(response):
    """
    Ensure browser back button cannot restore authenticated session data
    after logout, and protect against stale cached responses.
    """
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "SAMEORIGIN"
    return response


@app.errorhandler(404)
def not_found_error(error):
    return render_template(
        "error.html",
        error_code=404,
        error_title="Page Not Found",
        error_message="The page or resource you requested does not exist or has been moved."
    ), 404


@app.errorhandler(403)
def forbidden_error(error):
    return render_template(
        "error.html",
        error_code=403,
        error_title="Access Forbidden",
        error_message="You do not have the required permissions to access this page or record."
    ), 403


@app.errorhandler(500)
def internal_server_error(error):
    return render_template(
        "error.html",
        error_code=500,
        error_title="Internal System Error",
        error_message="A server-side error occurred. Please return to your portal or try again later."
    ), 500


# =========================================================
# RUN APPLICATION
# =========================================================

if __name__ == "__main__":

    app.run(
        debug=True,
        port=5000
    )