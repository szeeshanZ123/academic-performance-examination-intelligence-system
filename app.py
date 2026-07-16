from utils.data_loader import load_students
from analysis.student_analysis import class_summary

students = load_students()

class_summary(students)