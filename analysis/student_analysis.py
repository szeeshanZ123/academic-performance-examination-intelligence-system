import pandas as pd


def class_summary(df):

    print("\n===== CLASS SUMMARY =====")

    print("Total Students :", len(df))

    print("Average SGPI :", round(df["SGPI"].mean(), 2))

    print("Average Attendance :", round(df["Attendance"].mean(), 2))

    print("Highest SGPI :", df["SGPI"].max())

    print("Lowest SGPI :", df["SGPI"].min())
  

def subject_average(df):

    print("\n===== SUBJECT AVERAGES =====")

    subjects = ["Python", "DBMS", "Statistics"]

    for subject in subjects:
        average = df[subject].mean()
        print(f"{subject}: {average:.2f}")


def top_students(df):
    print("\n===== TOP STUDENTS =====")

    top_students_df = df.nlargest(5, "SGPI")

    for rank, (_, row) in enumerate(top_students_df.iterrows(), start=1):
        print(f"{rank}. {row['Name']} - SGPI: {row['SGPI']:.2f}")

def at_risk_students(df):
    print("\n===== AT-RISK STUDENTS =====")

    at_risk_students_df = df[
        (df["Attendance"] < 75) | (df["SGPI"] < 6.0)
    ].sort_values(by="Attendance")

    for _, row in at_risk_students_df.iterrows():

        reason = []

        if row["Attendance"] < 75:
            reason.append("Low Attendance")

        if row["SGPI"] < 6.0:
            reason.append("Low SGPI")

        print(f"""
Name       : {row['Name']}
Attendance : {row['Attendance']}%
SGPI       : {row['SGPI']:.2f}
Reason     : {", ".join(reason)}
---------------------------------
""")