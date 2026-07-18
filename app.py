from utils.data_loader import load_students
from analysis.student_analysis import at_risk_students, class_summary, top_students
from analysis.student_analysis import subject_average
from visualization.charts import subject_average_chart

students = load_students()

class_summary(students)

subject_average(students)

top_students(students)

at_risk_students(students)

subject_average_chart(students)