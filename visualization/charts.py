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

    plt.savefig("static/images/subject_average.png")

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
    plt.savefig("static/images/attendance_distribution.png")
    plt.show()

def sgpi_distribution_chart(df):
    plt.figure(figsize=(8,5))
    plt.hist(df['SGPI'],bins=10)
    plt.grid(axis="y", linestyle="--", alpha=0.7)
    plt.title("SGPI Distribution")
    plt.xlabel("SGPI")
    plt.ylabel("Number of Students")
    plt.savefig("static/images/sgpi_distribution.png")
    plt.show()

def top_students_chart(df):
    top_students=df.nlargest(10,'SGPI')
    names=top_students['Name']
    sgpi=top_students['SGPI']
    plt.figure(figsize=(10,6))
    plt.bar(names, sgpi)
    plt.title("Top 10 Students by SGPI")
    plt.xlabel("Student Names")
    plt.ylabel("SGPI")
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig("static/images/top_students.png")
    plt.show()