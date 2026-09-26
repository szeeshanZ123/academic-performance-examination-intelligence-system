Markdown
<div align="center">

# 🎓 Academic Performance & Examination Intelligence System

### *Turn Everyday Marks into Smart Academic Insights*

A web platform that helps schools, teachers, and students understand academic performance, predict outcomes, and spot learning gaps early.

<br>

[![Live Demo](https://img.shields.io/badge/🌐_Live_Demo-Try_It_Now-00C853?style=for-the-badge)](https://academic-performance-examination-in.vercel.app/)
[![GitHub](https://img.shields.io/badge/💻_Code-GitHub_Repo-181717?style=for-the-badge&logo=github)](https://github.com/szeeshanZ123/academic-performance-examination-intelligence-system)

<br>

![Python](https://img.shields.io/badge/Python-3776AB?style=flat-square&logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-000000?style=flat-square&logo=flask&logoColor=white)
![Scikit-Learn](https://img.shields.io/badge/Scikit--Learn-F7931E?style=flat-square&logo=scikit-learn&logoColor=white)
![Pandas](https://img.shields.io/badge/Pandas-150458?style=flat-square&logo=pandas&logoColor=white)
![Bootstrap](https://img.shields.io/badge/Bootstrap-7952B3?style=flat-square&logo=bootstrap&logoColor=white)

---

</div>

## 💡 What is this project?

Most school portals only show numbers:
> **Student → Scores → Report Card**

This system goes several steps further:
> **Student Data → Analytics → Future Predictions → At-Risk Warnings → Action Plans**

It helps answer four fundamental questions:
1. **How is the student doing right now?** (Trends & Attendance)
2. **Where are they struggling?** (Weak topics and subjects)
3. **What could happen next?** (Machine Learning score prediction)
4. **How can they improve?** (Personalized study suggestions)

---

## 📸 Screenshots

<div align="center">

### 👨‍🏫 Teacher Dashboard
*Track whole-class pass rates, spot students falling behind, and view averages at a glance.*

<img src="screenshots/teacher-dashboard.png" width="85%" alt="Teacher Dashboard">

<br><br>

### 👨‍🎓 Student Dashboard
*A clear, personal space for students to view their scores, track attendance, and follow study plans.*

<img src="screenshots/student-dashboard.png" width="85%" alt="Student Dashboard">

<br><br>

### 📄 Question Paper Analyzer
*Upload an exam PDF to extract questions, marks, and cognitive difficulty levels.*

<img src="screenshots/question-paper-analyzer.png" width="85%" alt="Question Paper Analyzer">

</div>

---

## ✨ Main Features

| 👨‍🎓 For Students | 👨‍🏫 For Teachers | 📄 Exam Intelligence |
| :--- | :--- | :--- |
| • **Clear Overview:** See overall GPA and subject marks in clean charts | • **Class KPIs:** Average marks, pass rate, and attendance summaries | • **PDF Upload:** Automatically read question papers from PDF files |
| • **Score Forecast:** Machine Learning estimates upcoming exam scores | • **At-Risk Alerts:** Instant flags for students needing extra help | • **Mark Detection:** Automatically pulls question weights and marks |
| • **Attendance Tracker:** Visual warnings if attendance drops too low | • **Student Profiles:** Deep dive into any individual student's records | • **Bloom's Taxonomy:** Tags questions by recall, understanding, or logic |
| • **Improvement Tips:** Practical advice targeted at weak subjects | • **Quick Export:** Download summary reports as PDF or CSV files | • **Topic Balance:** Checks if all chapters are covered evenly |

---

## 🔄 How It Works

### 1. The Prediction Flow (Machine Learning)
```text
Historical Marks + Attendance
           ↓
   Data Preprocessing
           ↓
Random Forest ML Model
           ↓
Predicted Next Exam Score
           ↓
Custom Study Recommendations
2. The Question Paper Flow (PDF Analyzer)
Plaintext
Upload Exam PDF
      ↓
Extract Text with PyMuPDF
      ↓
Detect Questions & Marks
      ↓
Categorize by Bloom's Taxonomy (Easy → Hard)
      ↓
Generate Exam Quality Report
🛠️ Built With
Backend: Python, Flask

Machine Learning & Data: Scikit-Learn (Random Forest), Pandas, NumPy

Frontend: HTML5, CSS3, JavaScript, Bootstrap

Document Processing: PyMuPDF (PDF text extraction), ReportLab (PDF export)

Hosting: Vercel

📁 Project Structure
Plaintext
academic-performance-system/
│
├── app.py               # Main Flask web application
├── analysis/            # Scripts for data handling and statistics
├── ml/                  # Machine learning models and prediction code
├── templates/           # Web pages (Student, Teacher, and Admin dashboards)
├── static/              # CSS styles, JavaScript, and images
├── data/                # Sample datasets (marks, students, attendance)
├── requirements.txt     # List of required Python packages
└── README.md
🚀 Quick Start Guide
Run this project on your computer in four simple steps:

1. Download the Project
Bash
git clone [https://github.com/szeeshanZ123/academic-performance-examination-intelligence-system.git](https://github.com/szeeshanZ123/academic-performance-examination-intelligence-system.git)
cd academic-performance-examination-intelligence-system
2. Create a Virtual Environment
Bash
# On Windows:
python -m venv .venv
.venv\Scripts\activate

# On Mac / Linux:
python3 -m venv .venv
source .venv/bin/activate
3. Install Packages
Bash
pip install -r requirements.txt
4. Run the App
Bash
python app.py
Open your browser and visit: http://127.0.0.1:5000

🛡️ Production Roadmap
To transition this prototype into a full institution-wide application:

[ ] Connect a secure SQL database (PostgreSQL / MySQL) instead of static CSV files.

[ ] Add secure password hashing (bcrypt) and session tokens.

[ ] Add rate limiting to stop automated login attempts.

[ ] Integrate directly with college LMS and ERP systems.

👨‍💻 Author
Zeeshan Shaikh

Data Analytics • Machine Learning • Web Development
