"""
Script to extract and append new student records from official lists into the dataset.
Source of Truth: 4 uploaded images containing 116 Second Year BSc IT students.
"""

import os
import random
import pandas as pd
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parents[1] / "data"

STUDENT_RECORDS = [
    # Image 2 (Sr. 1 to 42, Roll 254102 to 254163)
    {"roll": "254102", "name": "ABDUL AZIZ REHMATULLAH SHAIKH", "gender": "Male"},
    {"roll": "254103", "name": "ABDUL KARIM ABDUL GAFOOR KHAN", "gender": "Male"},
    {"roll": "254107", "name": "ADTIYA VINOD GUPTA", "gender": "Male"},
    {"roll": "254109", "name": "AFROJ RAHMATULLA KHAN", "gender": "Male"},
    {"roll": "254110", "name": "AKASH HARISH CHAUHAN", "gender": "Male"},
    {"roll": "254111", "name": "ALINA SULEMAN CHAUDHARY", "gender": "Female"},
    {"roll": "254112", "name": "ALTAMASH SHARAFAT SAYYED", "gender": "Male"},
    {"roll": "254113", "name": "AMAN HARIBANSH NISHAD", "gender": "Male"},
    {"roll": "254115", "name": "ARFIYA MOHD SHAMIM CHOUDHARY", "gender": "Female"},
    {"roll": "254118", "name": "ARYAN RAJESH VISHWAKARMA", "gender": "Male"},
    {"roll": "254119", "name": "ASHAB ZAKIR HUSSEIN SHAH", "gender": "Male"},
    {"roll": "254120", "name": "ASHISH SATISH KANOJIA", "gender": "Male"},
    {"roll": "254121", "name": "ASHUTOSH BRIKESH YADAV", "gender": "Male"},
    {"roll": "254122", "name": "ASIF ABDUL RAKIB KHAN", "gender": "Male"},
    {"roll": "254123", "name": "ASIF ATIQUE ANSARI", "gender": "Male"},
    {"roll": "254124", "name": "ASIF IBRAR KHAN", "gender": "Male"},
    {"roll": "254130", "name": "AZRA MUZAMMIL HUSSAIN KHAN", "gender": "Female"},
    {"roll": "254131", "name": "GANESH MARIDOSS BARATH", "gender": "Male"},
    {"roll": "254132", "name": "BIPINKUMAR PARAMHANS BIND", "gender": "Male"},
    {"roll": "254133", "name": "DEEPAKKUMAR SANTOSHKUMAR GUPTA", "gender": "Male"},
    {"roll": "254134", "name": "DEEPAK SANTOSH VISHWAKARMA", "gender": "Male"},
    {"roll": "254135", "name": "DHIRAJ ANANT TAMBOLI", "gender": "Male"},
    {"roll": "254136", "name": "DIYAN IRFAN SHAIKH", "gender": "Male"},
    {"roll": "254139", "name": "FIRDOS ARIF SHAIKH", "gender": "Female"},
    {"roll": "254141", "name": "HARSH MAHENDRA JAISWAR", "gender": "Male"},
    {"roll": "254143", "name": "SAYIMA MOHD ZIKRIYA KHAN", "gender": "Female"},
    {"roll": "254144", "name": "MADANI TALHA FAIYAZ AHMED SHAIKH", "gender": "Male"},
    {"roll": "254146", "name": "MARIA SRUTHI ROBINSON NADAR", "gender": "Female"},
    {"roll": "254147", "name": "MD FATEEM AHMED SHAIKH", "gender": "Male"},
    {"roll": "254148", "name": "MD REHAN MOHD SAEED SAYYED", "gender": "Male"},
    {"roll": "254149", "name": "MD SOHRAB MD KALAM .", "gender": "Male"},
    {"roll": "254150", "name": "MEDHAKSHI PRAMOD MOKAL", "gender": "Female"},
    {"roll": "254151", "name": "MERLONE ROBINSON .", "gender": "Male"},
    {"roll": "254152", "name": "MOHAMMAD AAYAN MOHD AZAM SHAIKH", "gender": "Male"},
    {"roll": "254153", "name": "MOHAMMAD JUNED MOHAMMAD DILDAR KHAN", "gender": "Male"},
    {"roll": "254154", "name": "MOHAMMAD KAIF ISTIYAQ AHMED QURESHI", "gender": "Male"},
    {"roll": "254155", "name": "MOHAMMAD SAMEER MOHAMMAD SAKEEL IDRISI", "gender": "Male"},
    {"roll": "254156", "name": "MOHAMMED ABDULLAH MOHAMMED SAOOD SHAIKH", "gender": "Male"},
    {"roll": "254159", "name": "MOHAMMED AYAN ISMAIL QURESHI", "gender": "Male"},
    {"roll": "254160", "name": "MOHAMMED BILAL MOHD RAFIQUE SHAIKH", "gender": "Male"},
    {"roll": "254161", "name": "MOHAMMED FAISAL MOHAMMED WASEEM ANSARI", "gender": "Male"},
    {"roll": "254163", "name": "MOHAMMED HASAN SUHAIL ASHRAF QURESHI", "gender": "Male"},

    # Image 1 (Sr. 43 to 64, Roll 254164 to 254190)
    {"roll": "254164", "name": "MOHAMMED HASIB AJAJ AHMED SIDDIQUI", "gender": "Male"},
    {"roll": "254165", "name": "MOHD DANISH MOHD AKIL SHAIKH", "gender": "Male"},
    {"roll": "254166", "name": "MOHAMMED TANZIL SHANAWAZ QURESHI", "gender": "Male"},
    {"roll": "254167", "name": "MOHD AFFAN MOHD ATIQUE ANSARI", "gender": "Male"},
    {"roll": "254168", "name": "MOHD ANAS NAJMUDDIN .", "gender": "Male"},
    {"roll": "254169", "name": "MOHD ARSALAN MOKHD ASIF SIDDIQUI", "gender": "Male"},
    {"roll": "254172", "name": "MOHD FARHAN IRFAN SHAIKH", "gender": "Male"},
    {"roll": "254174", "name": "MOHD HASSAN RAZA MOHD NASIM RAZA SHAH", "gender": "Male"},
    {"roll": "254175", "name": "MOHD SIDDIQ IRFAN SAYYED", "gender": "Male"},
    {"roll": "254177", "name": "MOHMMED ASIF MOHD SHAHID KHAN", "gender": "Male"},
    {"roll": "254178", "name": "NAGMA SAMIULLAH SHAH", "gender": "Female"},
    {"roll": "254179", "name": "NASHRA ABDULLAH ANSARI", "gender": "Female"},
    {"roll": "254180", "name": "PRASAD RAMCHANDRA THORAT", "gender": "Male"},
    {"roll": "254181", "name": "PRASANNAKUMAR PANDUKUMAR ERPULA", "gender": "Male"},
    {"roll": "254182", "name": "PRATIK MAHDEV GHADGE", "gender": "Male"},
    {"roll": "254183", "name": "PRIYANSHU PRAMOD RAI", "gender": "Male"},
    {"roll": "254184", "name": "RAFIYA SHAHAB AHMED SIDDIQUI", "gender": "Female"},
    {"roll": "254185", "name": "RAHUL RAMBALI PRAJAPATI", "gender": "Male"},
    {"roll": "254186", "name": "RAJ GANESH PERUMAL SARAN", "gender": "Male"},
    {"roll": "254187", "name": "REHAN ANWAR SAYYED", "gender": "Male"},
    {"roll": "254189", "name": "REHAN SHAKIL MIRAJKAR", "gender": "Male"},
    {"roll": "254190", "name": "RIMA AMIT PRASAD", "gender": "Female"},

    # Image 4 (Sr. 1 to 42, Div B, Roll 254201 to 254251)
    {"roll": "254201", "name": "RITESH MAHENDRA KANOJIYA", "gender": "Male"},
    {"roll": "254202", "name": "SADAF AFSAR SHAH", "gender": "Female"},
    {"roll": "254203", "name": "SAHID AYYUB KHAN", "gender": "Male"},
    {"roll": "254204", "name": "SAHIL ANNA MOHITE", "gender": "Male"},
    {"roll": "254205", "name": "SAHIL SUBHASH JAISWAR", "gender": "Male"},
    {"roll": "254206", "name": "SAIMA SHANAWAZ KHAN", "gender": "Female"},
    {"roll": "254207", "name": "SANDEEP OMPRATAP PANDEY", "gender": "Male"},
    {"roll": "254208", "name": "SANDESH CHANDRAKANT NARKAR", "gender": "Male"},
    {"roll": "254209", "name": "SATISH KUMAR SHITALA PRASAD GUPTA", "gender": "Male"},
    {"roll": "254210", "name": "SATYAM RAMSUBHAG YADAV", "gender": "Male"},
    {"roll": "254211", "name": "MATHEW SEBIN", "gender": "Male"},
    {"roll": "254212", "name": "SHAHBAZ SHAMSUDDIN MALIK", "gender": "Male"},
    {"roll": "254214", "name": "MOHAMMAD MOIZ ABU SAKIB SHAIKH", "gender": "Male"},
    {"roll": "254215", "name": "SIDDHARTH RANJIT BARVE", "gender": "Male"},
    {"roll": "254216", "name": "SNEHA FARHAN SHAIKH", "gender": "Female"},
    {"roll": "254217", "name": "SOGIN SANTOSH VYAWAHARE", "gender": "Male"},
    {"roll": "254219", "name": "TAIBA KHATOON MOHD ABID KHAN", "gender": "Female"},
    {"roll": "254220", "name": "TAMANNA PARVEEN ABDUL KADIR MIYA", "gender": "Female"},
    {"roll": "254221", "name": "UMAR FARUK SHAHID SHAIKH", "gender": "Male"},
    {"roll": "254224", "name": "VIVEK PRADEEP TIWARI", "gender": "Male"},
    {"roll": "254226", "name": "YASWANTH BRAHMAJI RAO MATTAPARTHI", "gender": "Male"},
    {"roll": "254227", "name": "ZAKI SHABBIR AHMED MULLA", "gender": "Male"},
    {"roll": "254228", "name": "ZEESHAN HANIF SHAIKH", "gender": "Male"},
    {"roll": "254229", "name": "MOHD SAAD MOHAMMED SOHIL SOLENKY", "gender": "Male"},
    {"roll": "254230", "name": "YASH NANDKUMAR SHINDE", "gender": "Male"},
    {"roll": "254231", "name": "MOHD HASAN RIYAZ ANWAR SHAIKH", "gender": "Male"},
    {"roll": "254232", "name": "SARIM AFAQUE AHMED KHAN", "gender": "Male"},
    {"roll": "254233", "name": "FUZAIL AHMAD MUNIR AHMAD ANSARI", "gender": "Male"},
    {"roll": "254234", "name": "SHAHWEZ ISMAIL ALI SHAIKH", "gender": "Male"},
    {"roll": "254235", "name": "MAAZ MOINUDDIN ANSARI", "gender": "Male"},
    {"roll": "254236", "name": "SHAILENDRA KUMAR RAJKUMAR PRAJAPATI", "gender": "Male"},
    {"roll": "254237", "name": "ABDUL SALAM ABDUL SAMAD SHAIKH", "gender": "Male"},
    {"roll": "254238", "name": "HASSAN AHMED SAEED AHMED SHAIKH", "gender": "Male"},
    {"roll": "254239", "name": "SHUBHAM SATYAPRAKASH YADAV", "gender": "Male"},
    {"roll": "254240", "name": "SUMIT KUMAR BIJAY KUMAR PRAJAPATI", "gender": "Male"},
    {"roll": "254241", "name": "MOHD JAID SULEMAN SHAIKH", "gender": "Male"},
    {"roll": "254242", "name": "RIZWAN MOHD NASEEM KHAN", "gender": "Male"},
    {"roll": "254244", "name": "ARYAN SUDHIR BHANDARE", "gender": "Male"},
    {"roll": "254248", "name": "SHOURY MANISH RAJBHAR", "gender": "Male"},
    {"roll": "254249", "name": "MOHIT JAGDISH AHIRE", "gender": "Male"},
    {"roll": "254250", "name": "SAKSHI SANTOSH ADAGALE", "gender": "Female"},
    {"roll": "254251", "name": "SHANI MANOJ KUMAR AGRAHARI", "gender": "Male"},

    # Image 3 (Sr. 43 to 52, Roll 254252 to 254265)
    {"roll": "254252", "name": "SAAMIA IMAAN ABDUL VASE SHAIKH", "gender": "Female"},
    {"roll": "254253", "name": "ARYAN KISHOR PANDEY", "gender": "Male"},
    {"roll": "254254", "name": "MOHAMMED WASIM MOHAMMED WAJID", "gender": "Male"},
    {"roll": "254255", "name": "AARIZ SHOAIB SHAIKH", "gender": "Male"},
    {"roll": "254258", "name": "ANAND RAMESH YADAV", "gender": "Male"},
    {"roll": "254259", "name": "MAHENOOR SAYYED FEROZ", "gender": "Female"},
    {"roll": "254262", "name": "BATUL FATHMA KALIMAHMED KHAN", "gender": "Female"},
    {"roll": "254263", "name": "HIMANSHU VINODKUMAR GUPTA", "gender": "Male"},
    {"roll": "254264", "name": "MOHD ZIDAN MOHD HANIF JHALORI", "gender": "Male"},
    {"roll": "254265", "name": "MOHSEEN MEHMOOD KHAN", "gender": "Male"},
]

# Note: Check line 254182: In Image 1, is it PRATIK MAHADEV GHADGE?
# Let's verify PRATIK MAHADEV GHADGE vs PRATIK MAHDEV GHADGE:
# In Image 1, it is PRATIK MAHADEV GHADGE. Let's ensure exact string!
for rec in STUDENT_RECORDS:
    if rec["roll"] == "254182":
        rec["name"] = "PRATIK MAHADEV GHADGE"


SEMESTER_SUBJECTS = {
    1: ["Python Programming", "Mathematics I", "Communication Skills", "Digital Electronics"],
    2: ["Data Structures", "Database Management Systems", "Statistics", "Web Development"],
    3: ["Python for Data Analytics", "Operating Systems", "Computer Networks", "Software Engineering"],
}

def calculate_grade(total):
    if total >= 90:
        return "O"
    elif total >= 80:
        return "A+"
    elif total >= 70:
        return "A"
    elif total >= 60:
        return "B+"
    elif total >= 50:
        return "B"
    elif total >= 40:
        return "C"
    else:
        return "F"

def generate_username(name):
    # Clean non-alphanumeric
    parts = [p.strip().lower() for p in name.replace(".", "").split() if p.strip()]
    if not parts:
        return "student123"
    first = "".join(c for c in parts[0] if c.isalpha())
    last_initial = parts[-1][0].upper() if len(parts) > 1 and parts[-1] else "S"
    return f"{first}{last_initial}123"

def run_append():
    random.seed(42)  # Deterministic realistic data generation

    students_df = pd.read_csv(DATA_DIR / "students.csv")
    marks_df = pd.read_csv(DATA_DIR / "marks.csv")
    attendance_df = pd.read_csv(DATA_DIR / "attendance.csv")

    existing_rolls = set(students_df["Roll_No"].astype(str).str.strip())
    existing_marks_rolls = set(marks_df["Roll_No"].astype(str).str.strip())
    existing_att_rolls = set(attendance_df["Roll_No"].astype(str).str.strip())

    print(f"Existing students count: {len(students_df)}")
    print(f"Existing marks count: {len(marks_df)}")
    print(f"Existing attendance count: {len(attendance_df)}")

    new_student_rows = []
    new_marks_rows = []
    new_att_rows = []
    skipped_count = 0

    for idx, item in enumerate(STUDENT_RECORDS):
        roll = str(item["roll"]).strip()
        name = str(item["name"]).strip()
        gender = item["gender"]

        if roll in existing_rolls:
            print(f"Skipping duplicate roll: {roll} ({name})")
            skipped_count += 1
            continue

        username = generate_username(name)
        password = "student"
        email = f"it{roll}@college.edu"
        
        # Phone: realistic 10-digit number
        phone_prefix = random.choice(["98", "97", "96", "95", "91", "88", "87", "77"])
        phone = f"{phone_prefix}{random.randint(10000000, 99999999)}"

        # DOB: between 2004-01-01 and 2005-12-31
        year = random.choice([2004, 2005])
        month = f"{random.randint(1, 12):02d}"
        day = f"{random.randint(1, 28):02d}"
        dob = f"{year}-{month}-{day}"

        # Current semester for Second Year BSc IT is 3
        semester = 3
        admission_year = 2024
        status = "Active"

        new_student_rows.append({
            "Roll_No": roll,
            "Username": username,
            "Password": password,
            "Student_Name": name,
            "Gender": gender,
            "DOB": dob,
            "Email": email,
            "Phone": phone,
            "Semester": semester,
            "Admission_Year": admission_year,
            "Status": status
        })

        # Base performance profile for student (high performer, average, or struggling)
        # 15% high performers (80-95), 70% average (55-78), 15% at risk/struggling (35-55)
        prof_rand = random.random()
        if prof_rand < 0.15:
            base_internal_mean = 26
            base_external_mean = 58
            base_att_mean = 91.0
        elif prof_rand < 0.85:
            base_internal_mean = 20
            base_external_mean = 44
            base_att_mean = 81.0
        else:
            base_internal_mean = 14
            base_external_mean = 28
            base_att_mean = 68.0

        # Generate marks and attendance for Semester 1, 2, and 3
        for sem in [1, 2, 3]:
            subjects = SEMESTER_SUBJECTS[sem]
            for subj in subjects:
                # Internal marks (0-30, realistic 10-29)
                internal = int(min(30, max(10, round(random.gauss(base_internal_mean, 2.5)))))
                # External marks (0-70, realistic 20-68)
                external = int(min(70, max(15, round(random.gauss(base_external_mean, 6.0)))))
                total = internal + external
                grade = calculate_grade(total)

                # Attendance (55.0 to 98.0)
                att = round(min(98.0, max(56.0, random.gauss(base_att_mean, 5.0))), 1)

                new_marks_rows.append({
                    "Roll_No": roll,
                    "Semester": sem,
                    "Subject": subj,
                    "Internal": internal,
                    "External": external,
                    "Total": total,
                    "Grade": grade
                })

                new_att_rows.append({
                    "Roll_No": roll,
                    "Semester": sem,
                    "Subject": subj,
                    "Attendance": att
                })

    print(f"\n--- Verification of Data to Append ---")
    print(f"Total students to add: {len(new_student_rows)}")
    print(f"Total marks rows to add: {len(new_marks_rows)} ({len(new_student_rows)} students * 12 subjects)")
    print(f"Total attendance rows to add: {len(new_att_rows)} ({len(new_student_rows)} students * 12 subjects)")
    print(f"Skipped duplicates: {skipped_count}")

    # Append to DataFrames
    new_students_df = pd.DataFrame(new_student_rows)
    new_marks_df = pd.DataFrame(new_marks_rows)
    new_att_df = pd.DataFrame(new_att_rows)

    combined_students = pd.concat([students_df, new_students_df], ignore_index=True)
    combined_marks = pd.concat([marks_df, new_marks_df], ignore_index=True)
    combined_att = pd.concat([attendance_df, new_att_df], ignore_index=True)

    # Save to CSV files
    combined_students.to_csv(DATA_DIR / "students.csv", index=False)
    combined_marks.to_csv(DATA_DIR / "marks.csv", index=False)
    combined_att.to_csv(DATA_DIR / "attendance.csv", index=False)

    print("\nSuccessfully updated students.csv, marks.csv, and attendance.csv!")
    print(f"Final students count: {len(combined_students)} (was {len(students_df)})")
    print(f"Final marks count: {len(combined_marks)} (was {len(marks_df)})")
    print(f"Final attendance count: {len(combined_att)} (was {len(attendance_df)})")

if __name__ == "__main__":
    run_append()
