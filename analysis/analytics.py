import pandas as pd

def dashboard_kpis(df):
    """Calculate core KPI metrics for the given student DataFrame."""
    total_students = len(df)

    if df.empty:
        return {
            "total_students": 0,
            "average_sgpi": 0,
            "average_attendance": 0,
            "highest_sgpi": 0,
            "lowest_sgpi": 0,
            "at_risk": 0,
            "honors": 0,
            "pass_rate": 0
        }

    average_sgpi = round(df["SGPI"].mean(), 2)
    average_attendance = round(df["Attendance"].mean(), 2)
    highest_sgpi = round(df["SGPI"].max(), 2)
    lowest_sgpi = round(df["SGPI"].min(), 2)

    at_risk = len(
        df[
            (df["Attendance"] < 75) |
            (df["SGPI"] < 6.0)
        ]
    )

    honors = len(df[df["SGPI"] >= 8.5])
    passing_students = len(df[df["SGPI"] >= 4.0])
    pass_rate = round((passing_students / total_students) * 100, 1) if total_students > 0 else 0

    return {
        "total_students": total_students,
        "average_sgpi": average_sgpi,
        "average_attendance": average_attendance,
        "highest_sgpi": highest_sgpi,
        "lowest_sgpi": lowest_sgpi,
        "at_risk": at_risk,
        "honors": honors,
        "pass_rate": pass_rate
    }


def get_analytics_summary(students_df, marks_df, selected_semester=None):
    """Compute data summaries for Chart.js graphics on the dashboard."""
    if selected_semester:
        try:
            sem_num = int(selected_semester)
            sem_marks = marks_df[marks_df["Semester"] == sem_num]
        except (ValueError, TypeError):
            sem_marks = marks_df
    else:
        sem_marks = marks_df

    # Subject performance averages
    if not sem_marks.empty:
        subj_avg = (
            sem_marks.groupby("Subject")["Total"]
            .mean()
            .round(2)
            .to_dict()
        )
        grade_dist = (
            sem_marks["Grade"]
            .value_counts()
            .to_dict()
        )
    else:
        subj_avg = {}
        grade_dist = {}

    return {
        "subject_averages": subj_avg,
        "grade_distribution": grade_dist
    }


def get_teacher_subject_analytics(subject, semester, marks_df, attendance_df, students_df):
    """
    Compute specific analytics, KPIs, distributions, and student lists
    strictly for a single Subject + Semester assignment.
    """
    try:
        sem_num = int(semester)
    except (ValueError, TypeError):
        sem_num = semester

    # Filter marks for this specific Subject & Semester
    subj_marks = marks_df[
        (marks_df["Semester"] == sem_num) &
        (marks_df["Subject"].astype(str).str.strip().str.lower() == str(subject).strip().lower())
    ].copy()

    # Filter attendance for this specific Subject & Semester
    subj_att = attendance_df[
        (attendance_df["Semester"] == sem_num) &
        (attendance_df["Subject"].astype(str).str.strip().str.lower() == str(subject).strip().lower())
    ].copy()

    # If no marks found
    if subj_marks.empty:
        return {
            "kpis": {
                "total_students": 0,
                "average_marks": 0,
                "highest_marks": 0,
                "lowest_marks": 0,
                "average_attendance": 0,
                "pass_percentage": 0,
                "at_risk_count": 0,
                "honors_count": 0
            },
            "grade_distribution": {},
            "marks_distribution": {
                "<40 (Fail)": 0,
                "40-59 (Average)": 0,
                "60-74 (Good)": 0,
                "75-89 (Distinction)": 0,
                "90-100 (Outstanding)": 0
            },
            "attendance_distribution": {
                "< 75% (At Risk)": 0,
                "75% - 89% (Good)": 0,
                "90% - 100% (Excellent)": 0
            },
            "at_risk_students": [],
            "students": []
        }

    # Merge marks and attendance
    merged = pd.merge(
        subj_marks,
        subj_att[["Roll_No", "Semester", "Subject", "Attendance"]],
        on=["Roll_No", "Semester", "Subject"],
        how="left"
    )

    # Merge student names
    # students_df columns: Roll or Roll_No, Name or Student_Name
    name_col = "Name" if "Name" in students_df.columns else "Student_Name"
    roll_col = "Roll" if "Roll" in students_df.columns else "Roll_No"
    
    student_lookup = students_df[[roll_col, name_col]].drop_duplicates()
    student_lookup = student_lookup.rename(columns={roll_col: "Roll_No", name_col: "Student_Name"})

    merged = pd.merge(merged, student_lookup, on="Roll_No", how="left")
    merged["Student_Name"] = merged["Student_Name"].fillna("Unknown Student")
    merged["Attendance"] = pd.to_numeric(merged["Attendance"], errors="coerce").fillna(0).round(1)
    merged["Total"] = pd.to_numeric(merged["Total"], errors="coerce").fillna(0)
    merged["Internal"] = pd.to_numeric(merged["Internal"], errors="coerce").fillna(0)
    merged["External"] = pd.to_numeric(merged["External"], errors="coerce").fillna(0)

    total_students = len(merged)
    average_marks = round(float(merged["Total"].mean()), 2) if total_students > 0 else 0
    highest_marks = int(merged["Total"].max()) if total_students > 0 else 0
    lowest_marks = int(merged["Total"].min()) if total_students > 0 else 0
    average_attendance = round(float(merged["Attendance"].mean()), 2) if total_students > 0 else 0

    passing_count = len(merged[merged["Total"] >= 40])
    pass_percentage = round((passing_count / total_students) * 100, 1) if total_students > 0 else 0

    honors_count = len(merged[merged["Total"] >= 85])

    # Grade distribution in standardized order
    grade_order = ["O", "A+", "A", "B+", "B", "C", "P", "F"]
    actual_grade_counts = merged["Grade"].astype(str).value_counts().to_dict()
    grade_distribution = {g: actual_grade_counts.get(g, 0) for g in grade_order if g in actual_grade_counts or actual_grade_counts.get(g, 0) > 0}
    # If standard keys missing, include all present
    for g, count in actual_grade_counts.items():
        if g not in grade_distribution:
            grade_distribution[g] = count

    # Marks distribution bins
    marks_distribution = {
        "<40 (Fail)": int(len(merged[merged["Total"] < 40])),
        "40-59 (Average)": int(len(merged[(merged["Total"] >= 40) & (merged["Total"] < 60)])),
        "60-74 (Good)": int(len(merged[(merged["Total"] >= 60) & (merged["Total"] < 75)])),
        "75-89 (Distinction)": int(len(merged[(merged["Total"] >= 75) & (merged["Total"] < 90)])),
        "90-100 (Outstanding)": int(len(merged[merged["Total"] >= 90]))
    }

    # Attendance distribution bins
    attendance_distribution = {
        "< 75% (At Risk)": int(len(merged[merged["Attendance"] < 75])),
        "75% - 89% (Good)": int(len(merged[(merged["Attendance"] >= 75) & (merged["Attendance"] < 90)])),
        "90% - 100% (Excellent)": int(len(merged[merged["Attendance"] >= 90]))
    }

    # Build student list and at-risk list
    student_records = []
    at_risk_students = []

    for _, row in merged.iterrows():
        total = int(row["Total"])
        att = float(row["Attendance"])
        grade = str(row["Grade"])
        internal = int(row["Internal"])
        external = int(row["External"])
        roll = str(row["Roll_No"])
        name = str(row["Student_Name"])

        is_risk = (att < 75) or (total < 40)
        risk_reason = []
        if att < 75:
            risk_reason.append(f"Low Attendance ({att}%)")
        if total < 40:
            risk_reason.append(f"Failing Marks ({total}/100)")
        
        risk_str = " & ".join(risk_reason) if risk_reason else "Normal"
        
        status = "At Risk" if is_risk else ("Honors" if total >= 85 else "Good")

        rec = {
            "Roll": roll,
            "Name": name,
            "Internal": internal,
            "External": external,
            "Total": total,
            "Grade": grade,
            "Attendance": att,
            "is_risk": is_risk,
            "risk_reason": risk_str,
            "status": status
        }

        student_records.append(rec)
        if is_risk:
            at_risk_students.append(rec)

    at_risk_count = len(at_risk_students)

    kpis = {
        "total_students": total_students,
        "average_marks": average_marks,
        "highest_marks": highest_marks,
        "lowest_marks": lowest_marks,
        "average_attendance": average_attendance,
        "pass_percentage": pass_percentage,
        "at_risk_count": at_risk_count,
        "honors_count": honors_count
    }

    return {
        "kpis": kpis,
        "grade_distribution": grade_distribution,
        "marks_distribution": marks_distribution,
        "attendance_distribution": attendance_distribution,
        "at_risk_students": at_risk_students,
        "students": student_records
    }
