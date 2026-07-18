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