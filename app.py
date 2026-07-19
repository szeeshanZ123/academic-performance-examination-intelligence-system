from flask import Flask, render_template
from utils.data_loader import load_students
from analysis.analytics import dashboard_kpis

app = Flask(__name__)

students = load_students()


@app.route("/")
def home():

    kpis = dashboard_kpis(students)

    return render_template(
        "index.html",
        total_students=kpis["total_students"],
        average_sgpi=kpis["average_sgpi"],
        average_attendance=kpis["average_attendance"],
        at_risk=kpis["at_risk"],
        students=students.head(10).to_dict(orient="records")
    )


@app.route("/student/<int:roll>")
def student_profile(roll):

    student = students[students["Roll"] == roll]

    if student.empty:
        return "Student Not Found"

    student = student.iloc[0]

    return render_template(
        "student.html",
        student=student
    )


if __name__ == "__main__":
    app.run(debug=True)