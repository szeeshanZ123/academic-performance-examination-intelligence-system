"""Load and combine multi-file academic dataset (students, marks, attendance, teacher).

Provides clean data accessors and helper methods for dashboard analytics and student profile pages.
"""

from pathlib import Path
import pandas as pd

DATA_DIR = Path(__file__).resolve().parents[1] / "data"

# Semester to Subjects Mapping derived from dataset
SEMESTER_SUBJECTS = {
    1: ["Python Programming", "Mathematics I", "Communication Skills", "Digital Electronics"],
    2: ["Data Structures", "Database Management Systems", "Statistics", "Web Development"],
    3: ["Python for Data Analytics", "Operating Systems", "Computer Networks", "Software Engineering"],
    4: ["Java Programming", "Data Visualization", "Cloud Computing", "Artificial Intelligence"],
    5: ["Machine Learning", "Cyber Security", "Cloud Architecture", "DevOps"],
    6: ["Big Data Analytics", "Deep Learning", "Natural Language Processing", "Capstone Project"]
}

def load_data():
    """Load admin, student, marks, and attendance datasets."""
    admin_df = pd.read_csv(DATA_DIR / "admin.csv")
    student_df = pd.read_csv(DATA_DIR / "students.csv")
    marks_df = pd.read_csv(DATA_DIR / "marks.csv")
    attendance_df = pd.read_csv(DATA_DIR / "attendance.csv")

    # Combine subject marks and subject attendance
    subject_combined = pd.merge(
        marks_df,
        attendance_df,
        on=["Roll_No", "Semester", "Subject"],
        how="left"
    )

    # Compute per-student per-semester averages
    mark_summary = (
        marks_df.groupby(["Roll_No", "Semester"], as_index=False)["Total"]
        .mean()
        .rename(columns={"Total": "_average_mark"})
    )
    
    attendance_summary = (
        attendance_df.groupby(["Roll_No", "Semester"], as_index=False)["Attendance"]
        .mean()
        .rename(columns={"Attendance": "Attendance"})
    )

    # Filter active students and merge overall performance
    students = student_df[student_df["Status"].eq("Active")].copy()
    students = students.merge(mark_summary, on=["Roll_No", "Semester"], how="left")
    students = students.merge(attendance_summary, on=["Roll_No", "Semester"], how="left")

    # Assign Division A/B (first 30 in semester -> A, next 30 -> B)
    students = students.sort_values(["Semester", "Roll_No"]).reset_index(drop=True)
    position = students.groupby("Semester").cumcount()
    students["Division"] = position.floordiv(30).map({0: "A", 1: "B"}).fillna("B")

    # Standardize column names & metrics
    students = students.rename(columns={"Roll_No": "Roll", "Student_Name": "Name"})
    students["SGPI"] = (students["_average_mark"] / 10).round(2)
    students["Attendance"] = students["Attendance"].round(2)
    students["_average_mark"] = students["_average_mark"].round(2)

    return admin_df, students, marks_df, attendance_df, subject_combined

def get_admin_info():
    """Return primary admin info dictionary."""
    admin_df = pd.read_csv(DATA_DIR / "admin.csv")
    if not admin_df.empty:
        return admin_df.iloc[0].to_dict()
    return {
        "Teacher_ID": "T001",
        "Teacher_Name": "Mrs. Archana Patil",
        "Email": "admin@college.edu",
        "Phone": "9876543210"
    }

def get_semester_subjects(semester=None):
    """Return subject list for a specific semester or all semesters dictionary."""
    if semester:
        try:
            return SEMESTER_SUBJECTS.get(int(semester), [])
        except (ValueError, TypeError):
            return []
    return SEMESTER_SUBJECTS

def get_student_detail(roll):
    """Retrieve full student profile details, subject marks breakdown, and recommendations."""
    _, students, marks_df, attendance_df, subject_combined = load_data()
    
    student_rows = students[students["Roll"].astype(str).str.lower() == str(roll).lower()]
    if student_rows.empty:
        return None

    student = student_rows.iloc[0].to_dict()
    roll_no = student["Roll"]
    semester = student["Semester"]

    # Retrieve subject breakdown
    student_subjects = subject_combined[
        (subject_combined["Roll_No"] == roll_no) & 
        (subject_combined["Semester"] == semester)
    ].copy()

    subjects_list = []
    subject_marks_dict = {}

    for _, row in student_subjects.iterrows():
        subj_name = row["Subject"]
        tot_marks = int(row["Total"])
        int_marks = int(row["Internal"])
        ext_marks = int(row["External"])
        grade = str(row["Grade"])
        att = float(row["Attendance"])

        subject_marks_dict[subj_name] = tot_marks
        subjects_list.append({
            "subject": subj_name,
            "internal": int_marks,
            "external": ext_marks,
            "total": tot_marks,
            "grade": grade,
            "attendance": round(att, 1)
        })

    if subject_marks_dict:
        strongest_subject = max(subject_marks_dict, key=subject_marks_dict.get)
        weakest_subject = min(subject_marks_dict, key=subject_marks_dict.get)
        average_marks = round(sum(subject_marks_dict.values()) / len(subject_marks_dict), 2)
    else:
        strongest_subject = "N/A"
        weakest_subject = "N/A"
        average_marks = student.get("_average_mark", 0)

    sgpi = student["SGPI"]
    attendance = student["Attendance"]

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

    recommendations = []
    if attendance < 75:
        recommendations.append("Improve attendance immediately to maintain eligibility.")
    if sgpi < 6.0:
        recommendations.append("Seek remedial tutoring and academic mentoring in weaker subjects.")
    elif sgpi < 7.5:
        recommendations.append(f"Focus on boosting performance in {weakest_subject} to improve SGPI.")
    else:
        recommendations.append("Maintain high SGPI consistency to qualify for academic honors & distinction.")
    
    recommendations.append("Practice previous semester examination question papers regularly.")
    recommendations.append("Participate in technical workshops and lab practical exercises.")

    return {
        "student": student,
        "subjects_list": subjects_list,
        "strongest_subject": strongest_subject,
        "weakest_subject": weakest_subject,
        "average_marks": average_marks,
        "overall_performance": overall_performance,
        "attendance_status": attendance_status,
        "academic_risk": academic_risk,
        "recommendations": recommendations
    }

