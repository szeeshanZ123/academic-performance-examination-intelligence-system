from flask import Flask, render_template, request, redirect
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

    return render_template("student.html", student=student.iloc[0])


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
        return "Student Not Found"

    return redirect(f"/student/{student.iloc[0]['Roll']}")


if __name__ == "__main__":
    app.run(debug=True)