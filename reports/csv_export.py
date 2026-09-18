"""CSV Export Engine for Academic Intelligence.

Produces standardized, filter-respecting UTF-8 CSV reports with preserved
numerical values, appropriate column headers, and sanitized dynamic filenames.
"""

import io
import re
import csv
from typing import Dict, Any, Tuple, Optional
import pandas as pd


def sanitize_filename(filename: str) -> str:
    """Sanitize filename to prevent unsafe paths and invalid characters."""
    clean = re.sub(r'[^a-zA-Z0-9_\-\.]', '_', filename)
    clean = re.sub(r'_+', '_', clean).strip('_')
    return clean or "report"


# =========================================================================
# ADMIN CSV EXPORTERS
# =========================================================================

def export_admin_csv(report_data: Dict[str, Any], report_type: str = "performance") -> Tuple[str, str]:
    """
    Generate CSV content and dynamic filename for Admin reports.
    
    Supported report_type:
      - 'performance': Detailed student performance records
      - 'attendance': Attendance status records
      - 'at_risk': At-risk students with prioritized reasons
      - 'overall': High-level Institutional Academic KPIs
      - 'semester': Semester performance summary
      - 'subject': Subject performance summary
    
    Returns:
      (csv_string, filename)
    """
    filters = report_data.get("filters", {})
    sem = filters.get("semester", "")
    sem_suffix = f"_sem{sem}" if sem else "_all_sem"

    output = io.StringIO()

    if report_type == "attendance":
        records = report_data.get("attendance_records", [])
        headers = ["Roll_No", "Student_Name", "Semester", "Subject", "Attendance_Percentage", "Status"]
        writer = csv.DictWriter(output, fieldnames=headers)
        writer.writeheader()
        for r in records:
            writer.writerow({
                "Roll_No": r["roll"],
                "Student_Name": r["name"],
                "Semester": r["semester"],
                "Subject": r["subject"],
                "Attendance_Percentage": r["attendance"],
                "Status": r["status"]
            })
        fname = sanitize_filename(f"admin_attendance_report{sem_suffix}.csv")

    elif report_type == "at_risk":
        records = report_data.get("at_risk_records", [])
        headers = ["Roll_No", "Student_Name", "Semester", "Attendance_Percentage", "SGPI", "Risk_Reason", "Priority"]
        writer = csv.DictWriter(output, fieldnames=headers)
        writer.writeheader()
        for r in records:
            writer.writerow({
                "Roll_No": r["roll"],
                "Student_Name": r["name"],
                "Semester": r["semester"],
                "Attendance_Percentage": r["attendance"],
                "SGPI": r["sgpi"],
                "Risk_Reason": r["risk_reason"],
                "Priority": r["priority"]
            })
        fname = sanitize_filename(f"admin_at_risk_report{sem_suffix}.csv")

    elif report_type == "overall":
        kpis = report_data.get("kpis", {})
        headers = ["Metric", "Value"]
        writer = csv.writer(output)
        writer.writerow(headers)
        writer.writerow(["Total Students", kpis.get("total_students", 0)])
        writer.writerow(["Average Performance (%)", f"{kpis.get('average_performance', 0)}%"])
        writer.writerow(["Average Attendance (%)", f"{kpis.get('average_attendance', 0)}%"])
        writer.writerow(["Average SGPI", kpis.get("average_sgpi", 0)])
        writer.writerow(["Highest SGPI", kpis.get("highest_sgpi", 0)])
        writer.writerow(["Lowest SGPI", kpis.get("lowest_sgpi", 0)])
        writer.writerow(["Top Performers (Honors)", kpis.get("top_performers", 0)])
        writer.writerow(["At-Risk Students", kpis.get("at_risk_count", 0)])
        writer.writerow(["Pass Rate (%)", f"{kpis.get('pass_rate', 0)}%"])
        fname = sanitize_filename(f"admin_institutional_overall_report{sem_suffix}.csv")

    elif report_type == "semester":
        records = report_data.get("semester_summary", [])
        headers = ["Semester", "Total_Students", "Average_Marks", "Average_Attendance", "Average_SGPI", "Pass_Rate"]
        writer = csv.DictWriter(output, fieldnames=headers)
        writer.writeheader()
        for r in records:
            writer.writerow({
                "Semester": r["semester"],
                "Total_Students": r["total_students"],
                "Average_Marks": r["average_marks"],
                "Average_Attendance": r["average_attendance"],
                "Average_SGPI": r["average_sgpi"],
                "Pass_Rate": r["pass_rate"]
            })
        fname = sanitize_filename(f"admin_semester_performance_report.csv")

    elif report_type == "subject":
        records = report_data.get("subject_summary", [])
        headers = [
            "Semester", "Subject", "Total_Students", "Average_Internal",
            "Average_External", "Average_Total", "Highest_Marks", "Lowest_Marks", "Average_Attendance"
        ]
        writer = csv.DictWriter(output, fieldnames=headers)
        writer.writeheader()
        for r in records:
            writer.writerow({
                "Semester": r["semester"],
                "Subject": r["subject"],
                "Total_Students": r["students_count"],
                "Average_Internal": r["average_internal"],
                "Average_External": r["average_external"],
                "Average_Total": r["average_total"],
                "Highest_Marks": r["highest_marks"],
                "Lowest_Marks": r["lowest_marks"],
                "Average_Attendance": r["attendance_average"]
            })
        fname = sanitize_filename(f"admin_subject_performance_report{sem_suffix}.csv")

    else:  # default 'performance'
        records = report_data.get("performance_records", [])
        headers = ["Roll_No", "Student_Name", "Semester", "Subject", "Internal", "External", "Total", "Attendance", "Grade", "SGPI"]
        writer = csv.DictWriter(output, fieldnames=headers)
        writer.writeheader()
        for r in records:
            writer.writerow({
                "Roll_No": r["roll"],
                "Student_Name": r["name"],
                "Semester": r["semester"],
                "Subject": r["subject"],
                "Internal": r["internal"],
                "External": r["external"],
                "Total": r["total"],
                "Attendance": r["attendance"],
                "Grade": r["grade"],
                "SGPI": r["sgpi"]
            })
        fname = sanitize_filename(f"admin_performance_report{sem_suffix}.csv")

    return output.getvalue(), fname


# =========================================================
# TEACHER CSV EXPORTERS
# =========================================================

def export_teacher_csv(
    report_data: Dict[str, Any],
    report_type: str = "subject",
    student_roll: Optional[str] = None
) -> Tuple[str, str]:
    """
    Generate CSV content and dynamic filename for Teacher reports.
    
    Supported report_type:
      - 'subject': Complete subject student performance & attendance
      - 'student': Single student drill-down report
      - 'attendance': Attendance records
      - 'at_risk': At-risk students in this class
    """
    subj = report_data.get("selected_subject", "subject")
    sem = report_data.get("selected_semester", "1")
    subj_slug = subj.lower().replace(" ", "_")

    output = io.StringIO()

    if report_type == "student" and student_roll and report_data.get("selected_student_detail"):
        detail = report_data["selected_student_detail"]
        stud = detail["student"]
        subjs = detail["subjects_list"]

        writer = csv.writer(output)
        writer.writerow(["ACADEMIC REPORT - STUDENT PROFILE"])
        writer.writerow(["Roll_No", stud.get("Roll", student_roll)])
        writer.writerow(["Student_Name", stud.get("Name", "")])
        writer.writerow(["Semester", stud.get("Semester", sem)])
        writer.writerow(["Division", stud.get("Division", "A")])
        writer.writerow(["Overall_SGPI", stud.get("SGPI", "")])
        writer.writerow(["Overall_Attendance", stud.get("Attendance", "")])
        writer.writerow([])

        # Subject breakdown
        writer.writerow(["Subject", "Internal", "External", "Total", "Grade", "Attendance"])
        for s in subjs:
            writer.writerow([
                s.get("subject", ""),
                s.get("internal", 0),
                s.get("external", 0),
                s.get("total", 0),
                s.get("grade", ""),
                s.get("attendance", 0)
            ])
        fname = sanitize_filename(f"teacher_student_report_{student_roll}_sem{sem}.csv")

    elif report_type == "attendance":
        records = report_data.get("attendance_records", [])
        headers = ["Roll_No", "Student_Name", "Semester", "Subject", "Attendance", "Status"]
        writer = csv.DictWriter(output, fieldnames=headers)
        writer.writeheader()
        for r in records:
            writer.writerow(r)
        fname = sanitize_filename(f"teacher_attendance_report_sem{sem}_{subj_slug}.csv")

    elif report_type == "at_risk":
        records = report_data.get("at_risk_students", [])
        headers = ["Roll_No", "Student_Name", "Internal", "External", "Total", "Attendance", "Grade", "Risk_Reason"]
        writer = csv.DictWriter(output, fieldnames=headers)
        writer.writeheader()
        for r in records:
            writer.writerow({
                "Roll_No": r["Roll"],
                "Student_Name": r["Name"],
                "Internal": r["Internal"],
                "External": r["External"],
                "Total": r["Total"],
                "Attendance": r["Attendance"],
                "Grade": r["Grade"],
                "Risk_Reason": r["risk_reason"]
            })
        fname = sanitize_filename(f"teacher_at_risk_sem{sem}_{subj_slug}.csv")

    else:  # default 'subject'
        records = report_data.get("students", [])
        headers = ["Roll_No", "Student_Name", "Internal", "External", "Total", "Grade", "Attendance", "Status"]
        writer = csv.DictWriter(output, fieldnames=headers)
        writer.writeheader()
        for r in records:
            writer.writerow({
                "Roll_No": r["Roll"],
                "Student_Name": r["Name"],
                "Internal": r["Internal"],
                "External": r["External"],
                "Total": r["Total"],
                "Grade": r["Grade"],
                "Attendance": r["Attendance"],
                "Status": r["status"]
            })
        fname = sanitize_filename(f"teacher_subject_report_sem{sem}_{subj_slug}.csv")

    return output.getvalue(), fname


# =========================================================
# STUDENT CSV EXPORTERS
# =========================================================

def export_student_csv(student_data: Dict[str, Any]) -> Tuple[str, str]:
    """
    Generate comprehensive CSV export for authenticated student.
    Includes Student Information, Subject Performance, Attendance, SGPI Trend,
    and AI Prediction Outlook.
    """
    stud = student_data["student"]
    roll = stud.get("Roll", "student")
    sem = student_data["semester"]

    output = io.StringIO()
    writer = csv.writer(output)

    # 1. Header & Student Info
    writer.writerow(["ACADEMIC INTELLIGENCE - STUDENT ACADEMIC REPORT"])
    writer.writerow(["Name", stud.get("Name", "")])
    writer.writerow(["Roll_No", roll])
    writer.writerow(["Current_Semester", sem])
    writer.writerow(["Division", stud.get("Division", "A")])
    writer.writerow(["Overall_SGPI", stud.get("SGPI", "")])
    writer.writerow(["Overall_Attendance", f"{stud.get('Attendance', '')}%"])
    writer.writerow(["Attendance_Status", student_data.get("attendance_status", "")])
    writer.writerow([])

    # 2. Subject Performance
    writer.writerow(["SUBJECT PERFORMANCE"])
    writer.writerow(["Subject", "Internal", "External", "Total", "Percentage", "Grade", "Attendance"])
    for s in student_data.get("academic_performance", []):
        writer.writerow([
            s["subject"],
            s["internal"],
            s["external"],
            s["total"],
            s["percentage"],
            s["grade"],
            f"{s['attendance']}%"
        ])
    writer.writerow([])

    # 3. Academic History
    history = student_data.get("academic_history", {})
    trend_data = history.get("trend_data", [])
    if trend_data:
        writer.writerow(["ACADEMIC HISTORY"])
        writer.writerow(["Semester", "Average_Total", "Average_Internal", "Average_External", "Attendance", "SGPI"])
        for h in trend_data:
            writer.writerow([
                h["semester"],
                h["average_total"],
                h["average_internal"],
                h["average_external"],
                f"{h['average_attendance']}%",
                h["sgpi"]
            ])
        writer.writerow([])

    # 4. AI Performance Outlook
    ai_outlook = student_data.get("ai_outlook", {})
    preds = ai_outlook.get("predictions", [])
    if preds:
        writer.writerow(["AI PERFORMANCE OUTLOOK"])
        writer.writerow(["Subject", "Predicted_External", "Target_Total", "Performance_Level"])
        for p in preds:
            writer.writerow([
                p.get("subject", ""),
                f"{p.get('predicted_external', 'N/A')}/70",
                f"{p.get('predicted_total', 'N/A')}/100",
                p.get("classification", {}).get("label", "N/A")
            ])
        writer.writerow([])

    # 5. Improvement Summary
    plan = student_data.get("improvement_plan")
    if plan:
        writer.writerow(["IMPROVEMENT PLAN SUMMARY"])
        weak_names = [w["subject"] for w in plan.get("weak_subjects", [])]
        writer.writerow(["Weak_Subjects", ", ".join(weak_names) if weak_names else "None"])
        if plan.get("learning_topics"):
            top_topics = [t["topic"] for t in plan.get("learning_topics")[:3]]
            writer.writerow(["Priority_Topics", ", ".join(top_topics)])
        if plan.get("action_checklist"):
            actions = [a["text"] for a in plan.get("action_checklist")[:3]]
            writer.writerow(["Recommended_Actions", " | ".join(actions)])

    fname = sanitize_filename(f"student_academic_report_{roll}.csv")
    return output.getvalue(), fname
