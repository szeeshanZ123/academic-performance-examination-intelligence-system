import matplotlib.pyplot as plt
import numpy as np
  
def subject_average_chart(df):

    subjects = ["Python", "DBMS", "Statistics"]

    averages = []

    for subject in subjects:
        averages.append(df[subject].mean())

    plt.figure(figsize=(8,5))

    plt.bar(subjects, averages)

    plt.title("Average Marks by Subject")

    plt.xlabel("Subjects")

    plt.ylabel("Average Marks")

    plt.ylim(0,100)

    plt.savefig("reports/subject_average.png")

    plt.show()

def attendance_distribution_chart(df):
    low=len(df[df['Attendance']<75])

    medium=len(df[(df['Attendance']>=75) & (df['Attendance']<90)])

    high=len(df[df['Attendance']>=90])

    categories=['Low (<75%)', 'Medium (75%-90%)', 'High (>90%)']
    counts=[low,medium,high]
    plt.figure(figsize=(8,5))
    plt.bar(categories, counts)
    plt.title("Attendance Distribution")
    plt.xlabel("Attendance Category")
    plt.ylabel("Number of Students")
    plt.savefig("reports/attendance_distribution.png")
    plt.show()