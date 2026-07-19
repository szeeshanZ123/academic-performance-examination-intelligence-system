def dashboard_kpis(df):

    total_students = len(df)

    average_sgpi = round(df["SGPI"].mean(), 2)

    average_attendance = round(df["Attendance"].mean(), 2)

    highest_sgpi = df["SGPI"].max()

    lowest_sgpi = df["SGPI"].min()

    at_risk = len(
        df[
            (df["Attendance"] < 75) |
            (df["SGPI"] < 6)
        ]
    )

    return {
        "total_students": total_students,
        "average_sgpi": average_sgpi,
        "average_attendance": average_attendance,
        "highest_sgpi": highest_sgpi,
        "lowest_sgpi": lowest_sgpi,
        "at_risk": at_risk
    }