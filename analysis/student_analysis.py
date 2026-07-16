import pandas as pd


def class_summary(df):

    print("\n===== CLASS SUMMARY =====")

    print("Total Students :", len(df))

    print("Average SGPI :", round(df["SGPI"].mean(), 2))

    print("Average Attendance :", round(df["Attendance"].mean(), 2))

    print("Highest SGPI :", df["SGPI"].max())

    print("Lowest SGPI :", df["SGPI"].min())
  