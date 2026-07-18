from utils.data_loader import load_students
from analysis.student_analysis import at_risk_students, class_summary, top_students
from analysis.student_analysis import subject_average
import visualization.charts as charts
from analysis.analytics import dashboard_kpis

students = load_students()

class_summary(students)

subject_average(students)

top_students(students)

at_risk_students(students)

charts.subject_average_chart(students)

charts.attendance_distribution_chart(students)

charts.sgpi_distribution_chart(students)

dashboard_kpis(students)