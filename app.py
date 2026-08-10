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
    get_teacher_info,
    get_semester_subjects,
    get_student_detail
)

from analysis.analytics import (
    dashboard_kpis,
    get_analytics_summary
)


app = Flask(__name__)

# Required for Flask sessions
app.secret_key = "academic-performance-project-secret-key"


# =========================================================
# HOME
# =========================================================

@app.route("/")
def home():
    """
    Existing Teacher Dashboard.
    """

    semester = request.args.get("semester", "").strip()
    risk_filter = request.args.get("risk", "").strip()
    sort_by = request.args.get("sort_by", "").strip()
    sort_order = request.args.get("sort_order", "asc").strip()

    teacher, students, marks_df, attendance_df, subject_combined = load_data()

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

    teacher_info = get_teacher_info()

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

        teacher=teacher_info,

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

    if request.method == "POST":

        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()

        # Load student dataset
        _, students, _, _, _ = load_data()

        # Check username and password
        student = students[
            (students["Username"].astype(str) == username) &
            (students["Password"].astype(str) == password)
        ]

        if student.empty:
            flash("Invalid username or password.", "danger")
            return redirect(url_for("student_login"))

        # Get student information
        student_info = student.iloc[0]

        # Store student identity in session
        session["student_logged_in"] = True
        session["student_roll"] = str(student_info["Roll"])
        session["student_name"] = str(student_info["Name"])

        return redirect(url_for("student_dashboard"))

    return render_template("student_login.html")

# =========================================================
# STUDENT LOGIN
# =========================================================

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        username = request.form.get(
            "username",
            ""
        ).strip()

        password = request.form.get(
            "password",
            ""
        ).strip()

        # Load student data
        _, students, _, _, _ = load_data()

        # Find matching student
        student = students[
            (students["Username"].astype(str) == username)
            &
            (students["Password"].astype(str) == password)
        ]

        if student.empty:

            flash(
                "Invalid username or password.",
                "danger"
            )

            return redirect(
                url_for("login")
            )

        # Student found
        student_info = student.iloc[0]

        # Store identity in session
        session["student_logged_in"] = True

        session["student_roll"] = str(
            student_info["Roll"]
        )

        session["student_name"] = str(
            student_info["Name"]
        )

        flash(
            f"Welcome, {student_info['Name']}!",
            "success"
        )

        return redirect(
            url_for("student_dashboard")
        )

    return render_template("login.html")


# =========================================================
# STUDENT DASHBOARD
# =========================================================

@app.route("/student-dashboard")
def student_dashboard():

    # Check login
    if not session.get("student_logged_in"):

        flash(
            "Please login first.",
            "warning"
        )

        return redirect(
            url_for("login")
        )

    # Get logged-in student's Roll_No
    roll = session.get("student_roll")

    # Get complete student information
    detail = get_student_detail(roll)

    if not detail:

        session.clear()

        flash(
            "Student record not found.",
            "danger"
        )

        return redirect(
            url_for("login")
        )

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

        recommendations=detail["recommendations"]
    )


# =========================================================
# STUDENT LOGOUT
# =========================================================

@app.route("/student-logout")
def student_logout():

    session.clear()

    flash(
        "You have been logged out successfully.",
        "info"
    )

    return redirect(
        url_for("login")
    )


# =========================================================
# STUDENT PROFILE
# =========================================================

@app.route("/student/<roll>")
def student_profile(roll):

    detail = get_student_detail(roll)

    if not detail:

        return render_template(
            "search_not_found.html",
            query=str(roll)
        )

    teacher_info = get_teacher_info()

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

        teacher=teacher_info
    )


# =========================================================
# STUDENT API
# =========================================================

@app.route("/api/student/<roll>")
def student_api(roll):

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
# RUN APPLICATION
# =========================================================

if __name__ == "__main__":

    app.run(
        debug=True,
        port=5000
    )