# 🎓 Academic Performance and Examination Intelligence System

> A comprehensive, data-driven academic intelligence platform built with Python, Flask, Scikit-learn, and ReportLab. Provides role-based dashboards (Admin, Teacher, Student), ML-powered external mark predictions, syllabus-grounded Question Paper Intelligence, personalized improvement plans, and institutional PDF/CSV reporting with full Light & Dark mode support.

---

## 📌 Project Overview

The **Academic Performance and Examination Intelligence System** transforms institutional academic records into actionable intelligence for educators, administrators, and students.

### Key Capabilities:
- 🏛️ **Role-Based Portals**: Unified authentication with dedicated interfaces for Administrator, Faculty/Teacher, and Student roles.
- 🤖 **ML External Marks Prediction**: Multi-feature regression model predicting external semester marks, total score, and expected grade without data leakage.
- 📄 **Question Paper Intelligence**: Automated PDF text extraction, question classification, marks weighting, and Bloom's taxonomy difficulty analytics.
- 🎯 **Personalized Improvement Plan**: Acts as a personal academic coach with syllabus-grounded topics, weak-subject ranking, and interactive study roadmaps.
- 📊 **Institutional Reporting**: Dynamic multi-semester KPI analytics, filterable audit tables, and instant PDF/CSV export.
- 🌓 **Adaptive UI**: Responsive design with light and dark mode toggle built with vanilla CSS design tokens.

---

## 🏗️ System Architecture & Modules

```text
Academic-Performance-System/
│
├── .github/                 # CI/CD Workflows
│   └── workflows/
│       └── python-app.yml
│
├── analysis/                # Analytical computation engine
│   ├── __init__.py
│   └── analytics.py         # KPIs, distributions, and trend calculations
│
├── data/                    # Production CSV Datasets
│   ├── admin.csv            # Administrator credentials
│   ├── attendance.csv       # Multi-semester subject attendance records
│   ├── marks.csv            # Internal, External, Total marks, and Grades
│   ├── students.csv         # Student profiles, credentials, and cohorts
│   └── teacher.csv          # Faculty credentials and subject assignments
│
├── ml/                      # Machine Learning Subsystem
│   ├── models/
│   │   └── external_marks_model.joblib  # Trained RandomForest pipeline
│   ├── __init__.py
│   ├── model.py             # Feature pipeline & model architecture
│   ├── predictor.py         # Safe runtime inference engine
│   └── train_model.py       # Reproducible training & evaluation script
│
├── question_paper/          # Question Paper Intelligence Subsystem
│   ├── samples/             # Sample examination papers
│   ├── __init__.py
│   ├── analyzer.py          # Bloom taxonomy & difficulty analytics
│   ├── extractor.py         # PyMuPDF text extraction
│   ├── parser.py            # Question detection & marks parsing
│   └── routes.py            # Blueprint routes & UI handling
│
├── reports/                 # Reporting Engine
│   ├── __init__.py
│   ├── csv_export.py        # Streaming CSV exports
│   ├── pdf_export.py        # ReportLab institutional PDF generator
│   └── report_service.py    # Report data compilation
│
├── static/                  # Static Assets
│   ├── css/theme.css        # Light/Dark design system tokens
│   ├── js/theme.js          # Theme switching & persistence
│   └── images/              # Chart output assets
│
├── templates/               # Jinja2 HTML Templates
│   ├── admin_reports.html
│   ├── error.html
│   ├── improvement_plan.html
│   ├── index.html           # Admin Dashboard
│   ├── login.html           # Unified Authentication Portal
│   ├── question_paper.html  # Exam Intelligence
│   ├── search_not_found.html
│   ├── student.html         # Public Profile View
│   ├── student_dashboard.html
│   ├── student_login.html
│   ├── student_report.html
│   ├── teacher_dashboard.html
│   ├── teacher_login.html
│   └── teacher_reports.html
│
├── tests/                   # Automated Regression Test Suite
│   ├── __init__.py
│   ├── test_global_blue_theme.py
│   ├── test_improvement_plan.py
│   ├── test_logout_and_branding.py
│   ├── test_ml_finalization.py
│   ├── test_question_paper.py
│   ├── test_reports_system.py
│   ├── test_student_dashboard_consistency.py
│   ├── test_system_audit_regression.py
│   └── test_unified_auth_flow.py
│
├── utils/                   # Shared Utilities
│   ├── data_loader.py       # Data loader & cohort caching
│   └── student_recommendations.py # Rule-based coaching engine
│
├── visualization/           # Visualization Utilities
│   └── charts.py            # Matplotlib chart generators
│
├── .gitignore
├── app.py                   # Main Flask application
├── README.md                # System documentation
└── requirements.txt         # Production dependencies
```

---

## 🛠️ Technology Stack

| Layer | Technology |
|:---|:---|
| **Backend Framework** | Python 3.10+, Flask |
| **Data Processing** | Pandas, NumPy |
| **Machine Learning** | Scikit-learn (RandomForestRegressor, ColumnTransformer, OneHotEncoder), Joblib |
| **Document Processing** | PyMuPDF (fitz), python-docx, ReportLab |
| **Frontend & UI** | HTML5, Vanilla CSS Design System, Bootstrap 5 Icons, Chart.js |
| **Testing & CI** | Python `unittest`, GitHub Actions |

---

## 🚀 Quick Start & Installation

### 1. Clone the Repository
```bash
git clone https://github.com/szeeshanZ123/academic-performance-examination-intelligence-system.git
cd academic-performance-examination-intelligence-system
```

### 2. Set Up Virtual Environment
```bash
python -m venv .venv

# On Windows
.venv\Scripts\activate

# On Linux/macOS
source .venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Run the Application
```bash
python app.py
```
Open [http://127.0.0.1:5000](http://127.0.0.1:5000) in your web browser.

---

## 🧪 Running Automated Tests

The test suite covers authentication flows, role-based access, student dashboards, reports export, ML prediction pipelines, and question paper parsing.

```bash
python -m unittest discover tests
```

---

## 🔐 Default Demo Accounts

| Role | Username | Password |
|:---|:---|:---|
| **Administrator** | `admin` | `admin123` |
| **Faculty (Teacher)** | `teacher001` (Amit Patil) | `Teacher@123` |
| **Student** | `254228` (or Roll Number) | `student` |

---

## 📄 License
This project is developed for academic evaluation and institutional intelligence research.
