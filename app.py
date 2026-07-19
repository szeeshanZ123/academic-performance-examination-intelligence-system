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
        at_risk=kpis["at_risk"]
    )

if __name__ == "__main__":
    app.run(debug=True)