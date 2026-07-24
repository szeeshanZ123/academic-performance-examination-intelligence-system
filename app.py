from flask import Flask, render_template, request, redirect, jsonify, make_response
from utils.data_loader import load_data, get_teacher_info, get_semester_subjects, get_student_detail
from analysis.analytics import dashboard_kpis, get_analytics_summary

app = Flask(__name__)

@app.route("/")
def home():
    semester = request.args.get("semester", "").strip()
    division = request.args.get("division", "").strip()
    risk_filter = request.args.get("risk", "").strip()
    sort_by = request.args.get("sort_by", "").strip()
    sort_order = request.args.get("sort_order", "asc").strip()

    teacher, students, marks_df, attendance_df, subject_combined = load_data()

    filtered_students = students.copy()

    if semester:
        try:
            filtered_students = filtered_students[filtered_students["Semester"] == int(semester)]
        except ValueError:
            pass

    if division:
        filtered_students = filtered_students[filtered_students["Division"] == division]

    if risk_filter == "at_risk":
        filtered_students = filtered_students[
            (filtered_students["Attendance"] < 75) | (filtered_students["SGPI"] < 6.0)
        ]
    elif risk_filter == "honors":
        filtered_students = filtered_students[filtered_students["SGPI"] >= 8.5]

    if sort_by in ["Roll", "Name", "Semester", "Division", "SGPI", "Attendance"]:
        filtered_students = filtered_students.sort_values(by=sort_by, ascending=(sort_order == "asc"))

    kpis = dashboard_kpis(filtered_students)
    analytics = get_analytics_summary(filtered_students, marks_df, semester)
    teacher_info = get_teacher_info()
    semester_subjects = get_semester_subjects(semester) if semester else []

    # Map subject marks into student dicts for tabular display when a semester is selected
    student_records = filtered_students.to_dict(orient="records")
    
    if semester and semester_subjects:
        sem_num = int(semester)
        sem_marks = marks_df[marks_df["Semester"] == sem_num]
        
        # Build pivot table of totals per subject
        pivot = sem_marks.pivot(index="Roll_No", columns="Subject", values="Total").to_dict(orient="index")
        
        for student in student_records:
            roll = student["Roll"]
            student_subj_marks = pivot.get(roll, {})
            student["subjects"] = {subj: student_subj_marks.get(subj, "N/A") for subj in semester_subjects}

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
        selected_division=division,
        selected_risk=risk_filter,
        sort_by=sort_by,
        sort_order=sort_order,
        semester_subjects=semester_subjects,
        subject_averages=analytics["subject_averages"],
        grade_distribution=analytics["grade_distribution"]
    )


@app.route("/student/<roll>")
def student_profile(roll):
    detail = get_student_detail(roll)

    if not detail:
        return render_template(
            "search_not_found.html",
            query=str(roll),
            selected_semester="",
            selected_division=""
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


@app.route("/api/student/<roll>")
def student_api(roll):
    detail = get_student_detail(roll)
    if not detail:
        return jsonify({"error": "Student not found"}), 404
    return jsonify(detail)


@app.route("/search")
def search():
    query = request.args.get("query", "").strip()

    if not query:
        return redirect("/")

    _, students, _, _, _ = load_data()

    # Match exact roll first, then partial roll or name
    student = students[students["Roll"].str.lower() == query.lower()]
    if student.empty:
        student = students[students["Name"].str.lower() == query.lower()]
    if student.empty:
        student = students[students["Name"].str.lower().str.contains(query.lower(), regex=False)]
    if student.empty:
        student = students[students["Roll"].str.lower().str.contains(query.lower(), regex=False)]

    if student.empty:
        return render_template("search_not_found.html", query=query)

    return redirect(f"/student/{student.iloc[0]['Roll']}")


@app.route("/export")
def export_csv():
    semester = request.args.get("semester", "").strip()
    division = request.args.get("division", "").strip()
    risk_filter = request.args.get("risk", "").strip()
    sort_by = request.args.get("sort_by", "").strip()
    sort_order = request.args.get("sort_order", "asc").strip()

    _, students, marks_df, _, _ = load_data()

    filtered_students = students.copy()

    if semester:
        try:
            filtered_students = filtered_students[filtered_students["Semester"] == int(semester)]
        except ValueError:
            pass

    if division:
        filtered_students = filtered_students[filtered_students["Division"] == division]

    if risk_filter == "at_risk":
        filtered_students = filtered_students[
            (filtered_students["Attendance"] < 75) | (filtered_students["SGPI"] < 6.0)
        ]
    elif risk_filter == "honors":
        filtered_students = filtered_students[filtered_students["SGPI"] >= 8.5]

    if sort_by in ["Roll", "Name", "Semester", "Division", "SGPI", "Attendance"]:
        filtered_students = filtered_students.sort_values(by=sort_by, ascending=(sort_order == "asc"))

    # Export clean columns
    export_cols = ["Roll", "Name", "Gender", "DOB", "Email", "Phone", "Semester", "Division", "Attendance", "SGPI"]
    available_cols = [c for c in export_cols if c in filtered_students.columns]
    
    csv_data = filtered_students[available_cols].to_csv(index=False)
    response = make_response(csv_data)
    filename = f"student_performance_sem_{semester if semester else 'all'}.csv"
    response.headers["Content-Disposition"] = f"attachment; filename={filename}"
    response.headers["Content-Type"] = "text/csv"
    return response


if __name__ == "__main__":
    app.run(debug=True, port=5000)

