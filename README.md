
````markdown
# 🎓 Academic Performance and Examination Intelligence System

> A data-driven academic analytics platform built with Python and Flask to help educators monitor student performance, attendance, and academic risk through interactive dashboards.

---

## 📌 About the Project

The **Academic Performance and Examination Intelligence System** is a college major project designed to transform student academic data into meaningful and actionable insights.

The system analyzes:

- 📊 Academic performance
- 📚 Subject-wise marks
- 📝 Examination results
- 📅 Attendance
- 🎯 Semester-wise performance
- ⚠️ Academic risk

The platform provides separate experiences for **teachers and students**, allowing teachers to analyze class-level performance while students can view their own academic information and analytics.

The project is being developed incrementally, starting with a Flask-based analytics dashboard and gradually expanding toward authentication, advanced analytics, machine learning, and examination intelligence.

---

# 🚀 Project Vision

The long-term goal is to develop a centralized academic intelligence platform that can help institutions:

```text
Raw Academic Data
        ↓
Data Cleaning & Processing
        ↓
Data Analytics
        ↓
Interactive Dashboards
        ↓
Academic Insights
        ↓
Risk Identification
        ↓
Machine Learning
        ↓
Examination Intelligence
````

---

# ✨ Current Features

## 👨‍🏫 Teacher Dashboard

The Teacher Dashboard provides a centralized view of student academic performance.

### 📊 Dashboard Analytics

* 📊 Class Performance Summary
* 📚 Subject-wise Average Marks
* 🏆 Top Performing Students
* ⚠️ At-Risk Student Detection
* 📈 Attendance Analysis
* 🎯 Dashboard KPI Cards
* 📋 Student Records
* 🔍 Student Search
* 📤 CSV Data Export

### 🎓 Semester-wise Analysis

The current dataset contains:

* **6 Semesters**
* **60 Students per Semester**
* **360 Students Overall**

Teachers can analyze academic data according to semester.

### 👤 Student Profile

Teachers can view individual student information including:

* Personal details
* Roll Number
* Semester
* Subject-wise marks
* Grades
* Attendance
* Average performance
* Strongest subject
* Weakest subject
* Academic status
* Academic recommendations

---

# 👨‍🎓 Student Dashboard

Students can access their own academic information through the Student Dashboard.

### 🔐 Student Authentication

Students can log in using their assigned credentials.

The system uses Flask sessions to maintain the logged-in student's identity.

### 📊 Student Analytics

Students can view:

* Personal academic performance
* Subject-wise marks
* Grades
* Attendance
* Average marks
* Strongest subject
* Weakest subject
* Academic performance status
* Academic risk status
* Personalized recommendations

### 🔓 Logout

Students can securely log out of their session.

---

# 📊 Data Visualizations

The dashboard uses visualizations to make academic data easier to understand.

### Current / Implemented

* 📊 Subject Average Chart
* 📈 Performance Distribution
* 📅 Attendance Distribution
* 🏆 Top Students
* 📋 Academic KPI Cards

### Planned

* 📈 Semester Performance Trends
* 📚 Subject Performance Comparison
* 🔥 Performance Heatmap
* 📊 Advanced Academic Analytics

---

# 🗃️ Dataset

The system currently uses a multi-file academic dataset.

### Students Dataset

```text
Roll_No
Username
Password
Student_Name
Gender
DOB
Email
Phone
Semester
Admission_Year
Status
```

### Marks Dataset

```text
Roll_No
Semester
Subject
Internal
External
Total
Grade
```

### Attendance Dataset

```text
Roll_No
Semester
Subject
Attendance
```

### Teacher Dataset

Contains teacher information used by the Teacher Dashboard.

---

# 🛠️ Technology Stack

### Programming Language

* Python

### Backend

* Flask

### Data Analysis

* Pandas
* NumPy

### Visualization

* Chart.js
* Matplotlib
* Seaborn

### Frontend

* HTML5
* CSS3
* Bootstrap 5
* JavaScript

### Authentication

* Flask Sessions

### Data Storage

* CSV datasets

### Version Control

* Git
* GitHub

---

# 📂 Project Structure

```text
Academic-Performance-System/
│
├── analysis/
│   └── analytics.py
│
├── data/
│   ├── students.csv
│   ├── marks.csv
│   ├── attendance.csv
│   └── teacher.csv
│
├── static/
│   ├── css/
│   ├── js/
│   └── images/
│
├── templates/
│   ├── index.html
│   ├── student.html
│   ├── student_login.html
│   ├── student_dashboard.html
│   └── search_not_found.html
│
├── utils/
│   └── data_loader.py
│
├── app.py
├── requirements.txt
└── README.md
```

---

# 📈 Project Development Progress

## ✅ Completed

### Data & Analytics

* [x] Project structure
* [x] Academic dataset creation
* [x] 360 student records
* [x] 6-semester dataset
* [x] Marks dataset
* [x] Attendance dataset
* [x] CSV data loading
* [x] Academic performance calculations
* [x] Attendance analysis
* [x] Subject-wise analysis
* [x] At-risk student identification

### Teacher Module

* [x] Teacher Dashboard
* [x] KPI Cards
* [x] Student Records Table
* [x] Semester Filtering
* [x] Student Search
* [x] Student Profile
* [x] Subject-wise Marks
* [x] Attendance Information
* [x] Top Student Analysis
* [x] CSV Export
* [x] Interactive Charts
* [x] Responsive UI

### Student Module

* [x] Student Authentication
* [x] Student Login
* [x] Session Management
* [x] Student Dashboard
* [x] Personal Academic Analytics
* [x] Subject Performance
* [x] Attendance Information
* [x] Academic Risk Information
* [x] Logout Functionality
* [x] Password Visibility Toggle
* [x] Updated Dashboard UI

---

# 🚧 Currently Working On

The current development focus is improving the student and teacher experience and strengthening the analytics layer.

### Current Priorities

* [ ] Improve Student Dashboard Analytics
* [ ] Add Interactive Student Charts
* [ ] Improve Semester-wise Analytics
* [ ] Improve Academic Risk Analysis
* [ ] Improve Dashboard UI/UX
* [ ] Strengthen Authentication and Access Control

---

# 🔮 Future Development

## 🤖 Machine Learning

Planned Machine Learning features include:

* Student Performance Prediction
* Academic Risk Prediction
* Student Clustering
* Performance Classification
* Early Identification of Academically Struggling Students

---

## 📑 Examination Intelligence

A future examination analysis module will include:

* PDF Question Paper Upload
* Image / Question Paper Processing
* OCR-based Text Extraction
* Question Detection
* Topic Identification
* Marks Distribution Analysis
* Frequently Asked Topic Detection
* Repeated Question Detection
* Historical Examination Trend Analysis

---

## 📊 Advanced Analytics

Future analytics may include:

* Semester Performance Trends
* Student Performance Comparison
* Subject Difficulty Analysis
* Attendance-Performance Relationship
* Academic Progress Tracking
* Advanced Academic Reports

---

## 📄 Reporting

Planned reporting features:

* PDF Academic Reports
* Excel Reports
* Semester Reports
* Student Performance Reports
* At-Risk Student Reports

---

# 🎯 Project Objectives

The main objectives of this project are:

1. **Analyze academic performance** using structured student data.

2. **Monitor attendance** and identify students with attendance concerns.

3. **Identify academically at-risk students** using performance and attendance indicators.

4. **Provide teachers with interactive dashboards** for better academic decision-making.

5. **Allow students to monitor their own academic performance.**

6. **Analyze semester and subject-level performance.**

7. **Provide data-driven academic insights.**

8. **Introduce Machine Learning** for advanced prediction and classification.

9. **Analyze historical question papers** to identify examination trends.

---

# ⚙️ Installation

### 1. Clone the repository

```bash
git clone https://github.com/szeeshanZ123/Academic-Performance-System.git
```

### 2. Open the project

```bash
cd Academic-Performance-System
```

### 3. Create a virtual environment

```bash
python -m venv .venv
```

### 4. Activate the virtual environment

#### Windows

```bash
.venv\Scripts\activate
```

### 5. Install dependencies

```bash
pip install -r requirements.txt
```

### 6. Run the Flask application

```bash
python app.py
```

### 7. Open in browser

```text
http://127.0.0.1:5000
```

---

# 📸 Screenshots

Screenshots of the following modules will be added as development progresses:

* Teacher Dashboard
* Student Login
* Student Dashboard
* Academic Analytics
* Student Profile
* Data Visualizations

---

# 🔐 Authentication

The current student authentication system uses the student dataset to verify credentials and Flask sessions to maintain the logged-in student's identity.

> **Note:** This implementation is intended for the academic project prototype. Production deployment would require secure password hashing, database-backed authentication, stronger session management, and additional security controls.

---

# 📌 Development Approach

The project is being developed incrementally rather than implementing all modules at once.

```text
Phase 1
Python & Data Processing
        ↓
Phase 2
Academic Dataset & Analytics
        ↓
Phase 3
Teacher Dashboard
        ↓
Phase 4
Student Authentication
        ↓
Phase 5
Student Dashboard
        ↓
Phase 6
Advanced Analytics
        ↓
Phase 7
Machine Learning
        ↓
Phase 8
Question Paper Intelligence
        ↓
Phase 9
Reporting & Final System
```

---

# 🤝 Contributing

This project is primarily developed as a college major project and portfolio project.

Suggestions, improvements, and feedback are welcome.

To contribute:

1. Fork the repository
2. Create a new branch
3. Make your changes
4. Commit your changes
5. Push the branch
6. Open a Pull Request

---

# 📜 License

This project is developed for **educational and portfolio purposes**.

---

# 👨‍💻 Developer

## Zeeshan Hanif Shaikh

🎓 **B.Sc. Information Technology**

📊 **Aspiring Data Analyst | Data Scientist**

### Connect With Me

📧 Email:
[shaikhzeeshan7554@gmail.com](mailto:shaikhzeeshan7554@gmail.com)

🔗 LinkedIn:
[https://www.linkedin.com/in/zeeshan-shaikh-6b3a753a1/](https://www.linkedin.com/in/zeeshan-shaikh-6b3a753a1/)

💻 GitHub:
[https://github.com/szeeshanZ123](https://github.com/szeeshanZ123)

---

# ⭐ Project Status

**🚧 Active Development**

The core Teacher Dashboard and initial Student Dashboard are functional. New analytics, authentication improvements, Machine Learning, and Examination Intelligence modules will be developed progressively.

```
```

