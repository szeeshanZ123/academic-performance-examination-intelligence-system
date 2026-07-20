from flask import Flask, render_template, request, redirect, make_response
from utils.data_loader import load_students
from analysis.analytics import dashboard_kpis

app = Flask(__name__)
teacher = pd.read_csv("data/teacher.csv")
students = pd.read_csv("data/students.csv")
marks = pd.read_csv("data/marks.csv")
attendance = pd.read_csv("data/attendance.csv")

@app.route("/")
def home():
    semester = request.args.get("semester", "")
    division = request.args.get("division", "")
    sort_by = request.args.get("sort_by", "")
    sort_order = request.args.get("sort_order", "asc")

    filtered_students = students

    if semester:
        filtered_students = filtered_students[filtered_students["Semester"] == int(semester)]
    if division:
        filtered_students = filtered_students[filtered_students["Division"] == division]

    if sort_by in ["Roll", "Name", "SGPI", "Attendance"]:
        filtered_students = filtered_students.sort_values(by=sort_by, ascending=(sort_order == "asc"))

    kpis = dashboard_kpis(filtered_students)

    return render_template(
        "index.html",
        total_students=kpis["total_students"],
        average_sgpi=kpis["average_sgpi"],
        average_attendance=kpis["average_attendance"],
        at_risk=kpis["at_risk"],
        students=filtered_students.to_dict(orient="records"),
        selected_semester=semester,
        selected_division=division,
        sort_by=sort_by,
        sort_order=sort_order
    )


@app.route("/student/<int:roll>")
def student_profile(roll):
    student = students[students["Roll"] == roll]

    if student.empty:
        return render_template(
            "search_not_found.html",
            query=str(roll),
            selected_semester="",
            selected_division=""
        )

    subjects = {
        "Python": student.iloc[0]["Python"],
        "DBMS": student.iloc[0]["DBMS"],
        "Statistics": student.iloc[0]["Statistics"]
    }

    strongest_subject = max(subjects, key=subjects.get)
    weakest_subject = min(subjects, key=subjects.get)
    average_marks = round(sum(subjects.values()) / len(subjects), 2)

    sgpi = student.iloc[0]["SGPI"]
    attendance = student.iloc[0]["Attendance"]

    if sgpi >= 8.5:
        overall_performance = "Excellent"
    elif sgpi >= 7.0:
        overall_performance = "Good"
    elif sgpi >= 6.0:
        overall_performance = "Average"
    else:
        overall_performance = "Needs Improvement"

    if attendance >= 90:
        attendance_status = "Excellent"
    elif attendance >= 75:
        attendance_status = "Good"
    else:
        attendance_status = "Low (At Risk)"

    if attendance < 75 or sgpi < 6.0:
        academic_risk = "High"
    elif sgpi < 7.0:
        academic_risk = "Medium"
    else:
        academic_risk = "Low"

    if sgpi >= 8.5:
        recommendation_text = "Maintain your SGPI above 8.5 to achieve academic distinction."
    elif sgpi >= 7.0:
        recommendation_text = "Focus on weak subjects to boost your SGPI above 8.5."
    else:
        recommendation_text = "Seek additional guidance and improve attendance & subject performance."

    return render_template(
        "student.html",
        student=student.iloc[0],
        strongest_subject=strongest_subject,
        weakest_subject=weakest_subject,
        average_marks=average_marks,
        overall_performance=overall_performance,
        attendance_status=attendance_status,
        academic_risk=academic_risk,
        recommendation_text=recommendation_text,
        selected_semester="",
        selected_division=""
    )


@app.route("/search")
def search():
    query = request.args.get("query", "").strip()

    if not query:
        return redirect("/")

    if query.isdigit():
        student = students[students["Roll"] == int(query)]
    else:
        student = students[students["Name"].str.lower() == query.lower()]

    if student.empty:
        return render_template("search_not_found.html", query=query)

    return redirect(f"/student/{student.iloc[0]['Roll']}")


@app.route("/filter")
def filter_students():
    return redirect(f"/?{request.query_string.decode('utf-8')}")


@app.route("/export")
def export_csv():
    semester = request.args.get("semester", "")
    division = request.args.get("division", "")
    sort_by = request.args.get("sort_by", "")
    sort_order = request.args.get("sort_order", "asc")

    filtered_students = students

    if semester:
        filtered_students = filtered_students[filtered_students["Semester"] == int(semester)]
    if division:
        filtered_students = filtered_students[filtered_students["Division"] == division]

    if sort_by in ["Roll", "Name", "SGPI", "Attendance"]:
        filtered_students = filtered_students.sort_values(by=sort_by, ascending=(sort_order == "asc"))

    csv_data = filtered_students.to_csv(index=False)
    response = make_response(csv_data)
    response.headers["Content-Disposition"] = "attachment; filename=students.csv"
    response.headers["Content-Type"] = "text/csv"
    return response


if __name__ == "__main__":
    app.run(debug=True)