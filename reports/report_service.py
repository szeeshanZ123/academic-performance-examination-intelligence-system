"""Reusable Report Service for Academic Intelligence.

Aggregates institutional, faculty, and student academic data using existing
application analytics, KPIs, ML predictions, and improvement plan pipelines.
"""

from typing import Dict, Any, List, Optional
import pandas as pd

from utils.data_loader import (
    load_data,
    get_admin_info,
    get_student_detail,
    get_teacher_assignments,
    get_semester_subjects
)
from analysis.analytics import (
    dashboard_kpis,
    get_teacher_subject_analytics,
    get_student_semester_trend
)
from ml.predictor import predict_subject_performance
from utils.student_recommendations import generate_improvement_plan


# =========================================================================
# ADMIN REPORTS SERVICE
# =========================================================================

def get_admin_reports_data(filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Generate complete institutional report data based on optional filters.
    
    Filters supported:
      - semester: str or int (1-6)
      - subject: str
      - student: str (search query for roll or name)
      - attendance_range: 'all', 'low' (<75%), 'good' (>=75%)
      - performance_range: 'all', 'at_risk' (<6.0 SGPI / <40 marks), 'average' (6.0-7.49), 'good' (7.5-8.49), 'honors' (>=8.5)
      - report_type: 'overall', 'performance', 'attendance', 'at_risk', 'semester', 'subject'
    """
    if filters is None:
        filters = {}

    admin_df, students_df, marks_df, attendance_df, subject_combined = load_data()
    admin_info = get_admin_info()

    sel_semester = str(filters.get("semester", "")).strip()
    sel_subject = str(filters.get("subject", "")).strip()
    sel_student = str(filters.get("student", "")).strip()
    sel_att_range = str(filters.get("attendance_range", "all")).strip().lower()
    sel_perf_range = str(filters.get("performance_range", "all")).strip().lower()
    report_type = str(filters.get("report_type", "overall")).strip().lower()

    # Base active cohort
    filtered_students = students_df.copy()

    # 1. Filter students by semester
    if sel_semester:
        try:
            sem_int = int(sel_semester)
            filtered_students = filtered_students[filtered_students["Semester"] == sem_int]
        except (ValueError, TypeError):
            pass

    # 2. Filter students by query (Roll or Name)
    if sel_student:
        q = sel_student.lower()
        filtered_students = filtered_students[
            filtered_students["Roll"].astype(str).str.lower().str.contains(q, na=False) |
            filtered_students["Name"].astype(str).str.lower().str.contains(q, na=False)
        ]

    # 3. Filter students by attendance range
    if sel_att_range == "low":
        filtered_students = filtered_students[filtered_students["Attendance"] < 75.0]
    elif sel_att_range == "good":
        filtered_students = filtered_students[filtered_students["Attendance"] >= 75.0]

    # 4. Filter students by performance range
    if sel_perf_range == "at_risk":
        filtered_students = filtered_students[
            (filtered_students["Attendance"] < 75.0) | (filtered_students["SGPI"] < 6.0)
        ]
    elif sel_perf_range == "honors":
        filtered_students = filtered_students[filtered_students["SGPI"] >= 8.5]
    elif sel_perf_range == "good":
        filtered_students = filtered_students[
            (filtered_students["SGPI"] >= 7.5) & (filtered_students["SGPI"] < 8.5)
        ]
    elif sel_perf_range == "average":
        filtered_students = filtered_students[
            (filtered_students["SGPI"] >= 6.0) & (filtered_students["SGPI"] < 7.5)
        ]

    # Calculate overall KPIs for current filtered students
    kpis = dashboard_kpis(filtered_students)
    avg_marks = round(float(filtered_students["_average_mark"].mean()), 2) if not filtered_students.empty else 0.0

    overall_kpis = {
        "total_students": kpis["total_students"],
        "average_performance": avg_marks,
        "average_attendance": kpis["average_attendance"],
        "average_sgpi": kpis["average_sgpi"],
        "top_performers": kpis["honors"],
        "at_risk_count": kpis["at_risk"],
        "pass_rate": kpis["pass_rate"],
        "highest_sgpi": kpis["highest_sgpi"],
        "lowest_sgpi": kpis["lowest_sgpi"]
    }

    # -------------------------------------------------------------
    # Build Detailed Subject-Level Student Records
    # -------------------------------------------------------------
    # We join subject_combined with student metadata for consistent display
    student_lookup = students_df[["Roll", "Name", "SGPI", "Attendance"]].drop_duplicates()
    student_lookup = student_lookup.rename(columns={
        "Roll": "Roll_No",
        "Name": "Student_Name",
        "SGPI": "Student_SGPI",
        "Attendance": "Overall_Attendance"
    })

    detailed_df = pd.merge(subject_combined, student_lookup, on="Roll_No", how="inner")

    # Apply semester filter to subject records
    if sel_semester:
        try:
            sem_int = int(sel_semester)
            detailed_df = detailed_df[detailed_df["Semester"] == sem_int]
        except (ValueError, TypeError):
            pass

    # Apply subject filter
    if sel_subject:
        detailed_df = detailed_df[
            detailed_df["Subject"].astype(str).str.lower() == sel_subject.lower()
        ]

    # Apply student query filter
    if sel_student:
        q = sel_student.lower()
        detailed_df = detailed_df[
            detailed_df["Roll_No"].astype(str).str.lower().str.contains(q, na=False) |
            detailed_df["Student_Name"].astype(str).str.lower().str.contains(q, na=False)
        ]

    # Apply attendance filter
    if sel_att_range == "low":
        detailed_df = detailed_df[detailed_df["Attendance"] < 75.0]
    elif sel_att_range == "good":
        detailed_df = detailed_df[detailed_df["Attendance"] >= 75.0]

    # Apply performance filter
    if sel_perf_range == "at_risk":
        detailed_df = detailed_df[
            (detailed_df["Attendance"] < 75.0) | (detailed_df["Total"] < 40) | (detailed_df["Student_SGPI"] < 6.0)
        ]
    elif sel_perf_range == "honors":
        detailed_df = detailed_df[detailed_df["Student_SGPI"] >= 8.5]
    elif sel_perf_range == "good":
        detailed_df = detailed_df[
            (detailed_df["Student_SGPI"] >= 7.5) & (detailed_df["Student_SGPI"] < 8.5)
        ]
    elif sel_perf_range == "average":
        detailed_df = detailed_df[
            (detailed_df["Student_SGPI"] >= 6.0) & (detailed_df["Student_SGPI"] < 7.5)
        ]

    # Sort detailed records deterministically
    detailed_df = detailed_df.sort_values(by=["Semester", "Roll_No", "Subject"])

    # 1. Student Performance Records
    performance_records = []
    for _, row in detailed_df.iterrows():
        performance_records.append({
            "roll": str(row["Roll_No"]).strip(),
            "name": str(row["Student_Name"]).strip(),
            "semester": int(row["Semester"]),
            "subject": str(row["Subject"]).strip(),
            "internal": int(row["Internal"]),
            "external": int(row["External"]),
            "total": int(row["Total"]),
            "attendance": round(float(row["Attendance"]), 1),
            "grade": str(row.get("Grade", "N/A")).strip(),
            "sgpi": round(float(row.get("Student_SGPI", 0.0)), 2)
        })

    # 2. Attendance Report Records
    attendance_records = []
    for _, row in detailed_df.iterrows():
        att_val = round(float(row["Attendance"]), 1)
        attendance_records.append({
            "roll": str(row["Roll_No"]).strip(),
            "name": str(row["Student_Name"]).strip(),
            "semester": int(row["Semester"]),
            "subject": str(row["Subject"]).strip(),
            "attendance": att_val,
            "status": "Good" if att_val >= 75.0 else "Needs Attention"
        })

    # 3. At-Risk Students Report (Student Level + Multi-Factor Reason)
    # Uses existing project logic:
    # - Low Attendance (< 75%)
    # - Low Marks (Total < 40 or SGPI < 6.0)
    # - Declining SGPI (historical check)
    at_risk_records = []
    # Filter candidates who exhibit potential risk (Attendance < 75 or SGPI < 7.0)
    risk_candidates = students_df[
        (students_df["Attendance"] < 75.0) | (students_df["SGPI"] < 7.0)
    ].copy()
    if sel_semester:
        try:
            risk_candidates = risk_candidates[risk_candidates["Semester"] == int(sel_semester)]
        except (ValueError, TypeError):
            pass

    for _, s_row in risk_candidates.iterrows():
        r_roll = str(s_row["Roll"]).strip()
        r_name = str(s_row["Name"]).strip()
        r_sem = int(s_row["Semester"])
        r_att = float(s_row["Attendance"])
        r_sgpi = float(s_row["SGPI"])

        # Check conditions
        reasons = []
        is_high = False

        if r_att < 75.0:
            reasons.append(f"Attendance < 75% ({r_att}%)")
            is_high = True

        if r_sgpi < 6.0:
            reasons.append(f"Low Performance (SGPI: {r_sgpi})")
            is_high = True

        # Check semester trend for decline if multi-semester student
        if r_sem >= 2:
            trend = get_student_semester_trend(r_roll, marks_df=marks_df, attendance_df=attendance_df)
            sgpi_history = trend.get("sgpi_trend", [])
            if len(sgpi_history) >= 2 and sgpi_history[-1] < sgpi_history[-2]:
                reasons.append(f"Declining SGPI ({sgpi_history[-2]} → {sgpi_history[-1]})")

        if reasons:
            priority = "High" if is_high else "Medium"
            at_risk_records.append({
                "roll": r_roll,
                "name": r_name,
                "semester": r_sem,
                "attendance": r_att,
                "sgpi": r_sgpi,
                "risk_reason": " • ".join(reasons),
                "priority": priority
            })

    # Filter at-risk records if student query active
    if sel_student:
        q = sel_student.lower()
        at_risk_records = [
            r for r in at_risk_records
            if q in r["roll"].lower() or q in r["name"].lower()
        ]

    # Sort at risk: High priority first, then lowest SGPI
    at_risk_records.sort(key=lambda r: (0 if r["priority"] == "High" else 1, r["sgpi"]))

    # 4. Semester Performance Summary
    semester_summary = []
    for sem in range(1, 7):
        sem_studs = students_df[students_df["Semester"] == sem]
        if not sem_studs.empty:
            sem_kpis = dashboard_kpis(sem_studs)
            sem_avg_marks = round(float(sem_studs["_average_mark"].mean()), 2)
            semester_summary.append({
                "semester": sem,
                "total_students": sem_kpis["total_students"],
                "average_marks": sem_avg_marks,
                "average_attendance": sem_kpis["average_attendance"],
                "average_sgpi": sem_kpis["average_sgpi"],
                "highest_sgpi": sem_kpis["highest_sgpi"],
                "lowest_sgpi": sem_kpis["lowest_sgpi"],
                "at_risk_count": sem_kpis["at_risk"],
                "honors_count": sem_kpis["honors"],
                "pass_rate": sem_kpis["pass_rate"]
            })

    # 5. Subject Performance Summary
    subject_summary = []
    subj_group = detailed_df.groupby(["Semester", "Subject"])
    for (sem_val, subj_val), grp in subj_group:
        tot_studs = len(grp)
        avg_int = round(float(grp["Internal"].mean()), 2) if tot_studs > 0 else 0.0
        avg_ext = round(float(grp["External"].mean()), 2) if tot_studs > 0 else 0.0
        avg_tot = round(float(grp["Total"].mean()), 2) if tot_studs > 0 else 0.0
        high_tot = int(grp["Total"].max()) if tot_studs > 0 else 0
        low_tot = int(grp["Total"].min()) if tot_studs > 0 else 0
        avg_att = round(float(grp["Attendance"].mean()), 2) if tot_studs > 0 else 0.0

        subject_summary.append({
            "semester": int(sem_val),
            "subject": str(subj_val),
            "students_count": tot_studs,
            "average_internal": avg_int,
            "average_external": avg_ext,
            "average_total": avg_tot,
            "highest_marks": high_tot,
            "lowest_marks": low_tot,
            "attendance_average": avg_att
        })

    subject_summary.sort(key=lambda s: (s["semester"], s["subject"]))

    # Available subjects list for filter dropdown
    all_available_subjects = sorted(list(marks_df["Subject"].unique()))

    return {
        "admin": admin_info,
        "filters": {
            "semester": sel_semester,
            "subject": sel_subject,
            "student": sel_student,
            "attendance_range": sel_att_range,
            "performance_range": sel_perf_range,
            "report_type": report_type
        },
        "available_subjects": all_available_subjects,
        "kpis": overall_kpis,
        "performance_records": performance_records,
        "attendance_records": attendance_records,
        "at_risk_records": at_risk_records,
        "semester_summary": semester_summary,
        "subject_summary": subject_summary,
        "total_records": len(performance_records)
    }


# =========================================================================
# TEACHER REPORTS SERVICE
# =========================================================================

def get_teacher_reports_data(
    teacher_username: str,
    sel_subject: str,
    sel_semester: int,
    student_roll: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """
    Generate authorized subject, class, and student reports for a teacher.
    Strictly verifies that sel_subject and sel_semester belong to teacher's assignments.
    Returns None if unauthorized.
    """
    assignments = get_teacher_assignments(teacher_username)
    if not assignments:
        return None

    # Verify authorization
    is_authorized = False
    teacher_info = None
    for a in assignments:
        if (
            str(a["Subject"]).strip().lower() == str(sel_subject).strip().lower() and
            int(a["Semester"]) == int(sel_semester)
        ):
            is_authorized = True
            teacher_info = a
            break

    if not is_authorized:
        return None

    _, students_df, marks_df, attendance_df, _ = load_data()

    # Reuse teacher subject analytics
    analytics_data = get_teacher_subject_analytics(
        sel_subject,
        sel_semester,
        marks_df,
        attendance_df,
        students_df
    )

    kpis = analytics_data["kpis"]
    student_records = analytics_data["students"]
    at_risk_students = analytics_data["at_risk_students"]

    # Build attendance list
    attendance_records = []
    for s in student_records:
        att = s["Attendance"]
        attendance_records.append({
            "roll": s["Roll"],
            "name": s["Name"],
            "subject": sel_subject,
            "semester": int(sel_semester),
            "attendance": att,
            "status": "Good" if att >= 75.0 else "Needs Attention"
        })

    # Individual student drill-down (if selected)
    selected_student_detail = None
    if student_roll:
        roll_norm = str(student_roll).strip().lower()
        # Verify student belongs to this teacher's cohort
        cohort_rolls = {str(s["Roll"]).strip().lower() for s in student_records}
        if roll_norm in cohort_rolls:
            selected_student_detail = get_student_detail(student_roll)
            if selected_student_detail:
                # Add trend info
                trend = get_student_semester_trend(student_roll)
                selected_student_detail["trend"] = trend

    return {
        "teacher": teacher_info,
        "assignments": assignments,
        "selected_subject": sel_subject,
        "selected_semester": int(sel_semester),
        "kpis": kpis,
        "grade_distribution": analytics_data["grade_distribution"],
        "marks_distribution": analytics_data["marks_distribution"],
        "attendance_distribution": analytics_data["attendance_distribution"],
        "students": student_records,
        "at_risk_students": at_risk_students,
        "attendance_records": attendance_records,
        "selected_student_detail": selected_student_detail,
        "has_data": len(student_records) > 0
    }


# =========================================================================
# STUDENT REPORTS SERVICE
# =========================================================================

def get_student_report_data(student_roll: str) -> Optional[Dict[str, Any]]:
    """
    Generate comprehensive, polished student academic report data for the authenticated student.
    Strictly derives from student profile, marks, attendance, trends, ML predictions, and Phase 8.4 improvement plan.
    """
    roll_str = str(student_roll).strip()
    detail = get_student_detail(roll_str)
    if not detail:
        return None

    student = detail["student"]
    subjects_list = detail["subjects_list"]
    semester = int(student.get("Semester", 1))

    # 1. Historical Trends
    trend_info = get_student_semester_trend(roll_str)

    # 2. AI Performance Outlook (ML Predictions)
    predictions = []
    has_predictions = False
    try:
        for subj in subjects_list:
            subj_name = str(subj.get("subject", "")).strip()
            int_marks = subj.get("internal", 0)
            att = subj.get("attendance", 0.0)
            act_ext = subj.get("external", 0)

            pred_res = predict_subject_performance(
                internal_marks=int_marks,
                attendance=att,
                semester=semester,
                subject=subj_name,
                actual_external=act_ext
            )
            predictions.append(pred_res)
            if pred_res.get("available"):
                has_predictions = True
    except Exception:
        has_predictions = False

    # 3. Improvement Plan Summary (Phase 8.4 Engine)
    improvement_plan = None
    try:
        improvement_plan = generate_improvement_plan(roll_str)
    except Exception:
        improvement_plan = None

    # Format academic performance table
    academic_performance = []
    for s in subjects_list:
        tot = int(s.get("total", 0))
        academic_performance.append({
            "subject": s.get("subject", "N/A"),
            "internal": int(s.get("internal", 0)),
            "external": int(s.get("external", 0)),
            "total": tot,
            "percentage": f"{tot}%",
            "grade": s.get("grade", "N/A"),
            "attendance": s.get("attendance", 0.0)
        })

    return {
        "student": student,
        "semester": semester,
        "academic_performance": academic_performance,
        "overall_summary": {
            "average_marks": detail.get("average_marks", 0.0),
            "overall_performance": detail.get("overall_performance", "Good"),
            "attendance": float(student.get("Attendance", 0.0)),
            "attendance_status": detail.get("attendance_status", "Good"),
            "sgpi": float(student.get("SGPI", 0.0)),
            "academic_risk": detail.get("academic_risk", "Low"),
            "division": student.get("Division", "A")
        },
        "attendance_status": detail.get("attendance_status", "Good"),
        "academic_history": {
            "trend_data": trend_info.get("trend_data", []),
            "summary": trend_info.get("summary", {}),
            "labels": trend_info.get("labels", []),
            "sgpi_trend": trend_info.get("sgpi_trend", []),
            "attendance_trend": trend_info.get("attendance_trend", []),
            "has_multiple_semesters": trend_info.get("has_multiple_semesters", False)
        },
        "ai_outlook": {
            "available": has_predictions,
            "predictions": predictions
        },
        "improvement_plan": improvement_plan
    }
