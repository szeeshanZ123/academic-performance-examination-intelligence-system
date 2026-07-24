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
