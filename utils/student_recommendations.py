"""Personalized Academic Improvement & Coaching Recommendation Engine.

Generates data-grounded, multi-factor improvement plans for students based on:
- Actual current semester marks
- Subject-wise attendance
- Historical SGPI trajectory
- ML Random Forest external predictions
- Question Paper Intelligence & Syllabus topic mapping
"""

from typing import Dict, Any, List, Optional
from utils.data_loader import get_student_detail, SEMESTER_SUBJECTS
from analysis.analytics import get_student_semester_trend
from ml.predictor import predict_subject_performance
from question_paper.analyzer import SUBJECT_SYLLABUS_TOPICS, resolve_subject_syllabus


# Known analyzed question paper intelligence cache for curriculum subjects
ANALYZED_EXAM_INTELLIGENCE = {
    "Python for Data Analytics": {
        "available": True,
        "paper_name": "Semester III — Python for Data Analytics",
        "frequently_asked": "Pandas",
        "high_mark_topic": "Data Cleaning",
        "high_mark_val": "25 Marks",
        "common_difficulty": "Medium",
        "total_paper_marks": 75,
        "recommended_focus": "Pandas + Data Cleaning & Normalization",
        "key_topics": ["Pandas", "Data Cleaning", "NumPy", "Data Visualization", "Statistics", "EDA"]
    },
    "Database Management Systems": {
        "available": True,
        "paper_name": "Semester II — Database Management Systems",
        "frequently_asked": "SQL & Relational Algebra",
        "high_mark_topic": "Normalization & Transactions",
        "high_mark_val": "25 Marks",
        "common_difficulty": "Medium",
        "total_paper_marks": 80,
        "recommended_focus": "SQL Queries (Joins) + Normal Forms (BCNF/3NF)",
        "key_topics": ["SQL & Relational Algebra", "Normalization", "ER Modeling", "Transaction Processing", "Concurrency"]
    },
    "Python Programming": {
        "available": True,
        "paper_name": "Semester I — Python Programming",
        "frequently_asked": "Control Flow & Data Structures",
        "high_mark_topic": "Object-Oriented Programming",
        "high_mark_val": "20 Marks",
        "common_difficulty": "Medium",
        "total_paper_marks": 75,
        "recommended_focus": "Classes, Inheritance & Exception Handling",
        "key_topics": ["Python Basics", "Data Structures (Lists/Dicts)", "OOP Concepts", "Exception Handling", "File I/O"]
    }
}


def get_exam_intelligence_for_subject(subject_name: str) -> Dict[str, Any]:
    """Retrieve verified question paper intelligence for a subject if available."""
    if not subject_name:
        return {"available": False, "message": "Exam intelligence will appear once question papers for your subjects are analyzed."}
    
    s_norm = subject_name.lower().strip()
    for key, data in ANALYZED_EXAM_INTELLIGENCE.items():
        k_norm = key.lower()
        if k_norm in s_norm or s_norm in k_norm:
            return data
        if "python" in s_norm and "analytic" in s_norm:
            return data
        if "dbms" in s_norm or "database" in s_norm:
            return data
            
    return {
        "available": False,
        "message": f"Exam intelligence will appear once question papers for {subject_name} are analyzed."
    }


def generate_improvement_plan(roll_no: str) -> Optional[Dict[str, Any]]:
    """
    Generate a comprehensive, personalized academic improvement plan for a student.
    All recommendations are strictly derived from the student's actual performance data.
    """
    detail = get_student_detail(roll_no)
    if not detail:
        return None

    student = detail["student"]
    subjects_list = detail["subjects_list"]
    semester = int(student.get("Semester", 1))
    overall_attendance = float(student.get("Attendance", 0))
    sgpi = float(student.get("SGPI", 0))
    avg_marks = float(detail.get("average_marks", 0))

    # 1. Historical SGPI and Attendance Trend
    trend_info = get_student_semester_trend(roll_no)
    sgpi_trend = trend_info.get("sgpi_trend", [])
    attendance_trend = trend_info.get("attendance_trend", [])
    has_multiple_semesters = trend_info.get("has_multiple_semesters", False)
    trend_labels = trend_info.get("labels", [])

    if len(sgpi_trend) >= 2:
        diff = round(sgpi_trend[-1] - sgpi_trend[-2], 2)
        if diff > 0.05:
            trend_direction = "Improving"
            trend_symbol = "↗"
            trend_tone = "Positive"
            trend_commentary = f"Your SGPI increased by {abs(diff)} points (from {sgpi_trend[-2]} to {sgpi_trend[-1]}) in recent semesters. Continue this positive trajectory."
        elif diff < -0.05:
            trend_direction = "Declining"
            trend_symbol = "↘"
            trend_tone = "Warning"
            trend_commentary = f"Your SGPI dropped by {abs(diff)} points (from {sgpi_trend[-2]} to {sgpi_trend[-1]}). Prioritize your weakest subjects to recover your academic momentum."
        else:
            trend_direction = "Stable"
            trend_symbol = "→"
            trend_tone = "Consistent"
            trend_commentary = f"Your SGPI has remained stable at {sgpi_trend[-1]}. Targeted effort in weak subjects will help you transition to distinction."
    else:
        trend_direction = "Baseline"
        trend_symbol = "ℹ"
        trend_tone = "Initial"
        trend_commentary = "Historical trend will appear once more semester data is available."

    # 2. Subject Performance Ranking (Weakest First)
    ranked_subjects = []
    weak_subjects = []
    strong_subjects = []
    
    # Sort subjects by total marks ascending
    sorted_raw_subjects = sorted(subjects_list, key=lambda s: s.get("total", 0))

    for s in sorted_raw_subjects:
        tot = s.get("total", 0)
        att = s.get("attendance", 0)
        subj_name = s.get("subject", "Subject")

        if tot < 50:
            status = "Needs Attention"
            badge = "danger"
            icon = "🔴"
            need_level = "High"
        elif tot < 65:
            status = "Focus Needed"
            badge = "warning"
            icon = "🟠"
            need_level = "Medium"
        elif tot < 75:
            status = "Satisfactory"
            badge = "info"
            icon = "🟡"
            need_level = "Low"
        else:
            status = "Strong"
            badge = "success"
            icon = "🟢"
            need_level = "Maintain"

        item = {
            "subject": subj_name,
            "total": tot,
            "internal": s.get("internal", 0),
            "external": s.get("external", 0),
            "grade": s.get("grade", "N/A"),
            "attendance": att,
            "status": status,
            "badge": badge,
            "icon": icon,
            "need_level": need_level
        }
        ranked_subjects.append(item)

        if tot < 65 or att < 75:
            weak_subjects.append(item)
        if tot >= 70 and att >= 75:
            strong_subjects.append(item)

    # Primary focus subject: lowest-scoring subject if no critical weakness exists
    primary_weak_subject = weak_subjects[0] if weak_subjects else (ranked_subjects[0] if ranked_subjects else None)

    # 3. ML External Predictions for Current Semester Subjects
    predictions = []
    pred_available_count = 0
    total_pred_ext = 0

    for s in subjects_list:
        subj_name = str(s.get("subject", "")).strip()
        int_marks = s.get("internal")
        att = s.get("attendance")
        act_ext = s.get("external")

        pred = predict_subject_performance(
            internal_marks=int_marks,
            attendance=att,
            semester=semester,
            subject=subj_name,
            actual_external=act_ext
        )
        predictions.append(pred)
        if pred.get("available"):
            pred_available_count += 1
            total_pred_ext += (pred.get("predicted_external") or 0)

    avg_predicted_ext = round(total_pred_ext / pred_available_count, 1) if pred_available_count > 0 else None
    avg_predicted_total = round(avg_predicted_ext + (avg_marks * 0.3), 1) if avg_predicted_ext else None
    
    if avg_predicted_ext is not None:
        if avg_predicted_ext >= 50:
            outlook = "Strong"
            outlook_badge = "success"
            outlook_advice = "Your predicted external marks indicate strong exam readiness. Maintain your revision cadence."
        elif avg_predicted_ext >= 35:
            outlook = "Good"
            outlook_badge = "primary"
            outlook_advice = "Focus on revision and previous question papers to elevate your external performance to high honors."
        else:
            outlook = "At Risk"
            outlook_badge = "warning"
            outlook_advice = "Predicted external marks are close to passing margins. Focus heavily on core exam topics immediately."
    else:
        outlook = "Unavailable"
        outlook_badge = "secondary"
        outlook_advice = "AI external prediction will calibrate once internal assessments and attendance are submitted."

    # 4. Exam Focus (Question Paper Intelligence Connection)
    exam_intelligence = None
    exam_target_subject = primary_weak_subject["subject"] if primary_weak_subject else ""
    if exam_target_subject:
        exam_intelligence = get_exam_intelligence_for_subject(exam_target_subject)
    
    # Fallback to any current subject if weak subject has no exam paper
    if (not exam_intelligence or not exam_intelligence.get("available")) and subjects_list:
        for s in subjects_list:
            ei = get_exam_intelligence_for_subject(s.get("subject", ""))
            if ei.get("available"):
                exam_intelligence = ei
                break

    # 5. Topic-Level Learning Plan (Syllabus Mapped)
    learning_topics = []
    revision_topics = []
    practice_topics = []

    if primary_weak_subject:
        target_name = primary_weak_subject["subject"]
        syllabus = resolve_subject_syllabus(target_name)
        
        if syllabus:
            topic_keys = list(syllabus.keys())
            # Top priority topic
            p1_topic = topic_keys[0] if len(topic_keys) > 0 else "Core Concepts"
            p1_subtopics = syllabus[p1_topic][:5] if p1_topic in syllabus else []
            
            p2_topic = topic_keys[1] if len(topic_keys) > 1 else None
            p2_subtopics = syllabus[p2_topic][:4] if p2_topic and p2_topic in syllabus else []

            learning_topics.append({
                "subject": target_name,
                "topic": p1_topic,
                "priority": "HIGH",
                "badge": "danger",
                "why": f"Your current score in {target_name} is {primary_weak_subject['total']}%. This topic forms foundational concepts with heavy exam weightage.",
                "subtopics": p1_subtopics
            })

            if p2_topic:
                learning_topics.append({
                    "subject": target_name,
                    "topic": p2_topic,
                    "priority": "MEDIUM",
                    "badge": "warning",
                    "why": f"Secondary key area in {target_name} carrying significant applied marks in semester examinations.",
                    "subtopics": p2_subtopics
                })

            # What to Revise (Section 9)
            rev_candidates = topic_keys[2:5] if len(topic_keys) > 2 else topic_keys[:2]
            for idx, r_top in enumerate(rev_candidates, 1):
                revision_topics.append({
                    "number": idx,
                    "topic": r_top,
                    "subject": target_name,
                    "reason": f"Appears consistently in question papers and reinforces conceptual clarity for {target_name}."
                })

            # What to Practice (Section 10)
            practice_topics = [
                {"count": "5", "category": f"{p1_topic} core conceptual and coding problems"},
                {"count": "3", "category": f"{p2_topic or 'Applied'} analytical questions"},
                {"count": "2", "category": "Multi-part comprehensive exercises"},
                {"count": "1", "category": "Full previous semester question paper (timed)"}
            ]

        else:
            # Clean fallback when subject has no granular topic config
            learning_topics.append({
                "subject": target_name,
                "topic": f"{target_name} Core Concepts",
                "priority": "HIGH",
                "badge": "warning",
                "why": f"Performance in {target_name} ({primary_weak_subject['total']}%) is below your semester average.",
                "subtopics": ["Fundamental principles", "Lecture notes & assignments", "Previous examination problem sets"]
            })
            revision_topics.append({
                "number": 1,
                "topic": f"{target_name} Comprehensive Review",
                "subject": target_name,
                "reason": "Reinforce syllabus modules before upcoming internal and external evaluations."
            })
            practice_topics = [
                {"count": "5", "category": f"{target_name} textbook exercises"},
                {"count": "1", "category": "Previous semester question paper"}
            ]

    # 6. Attendance Plan (Section 13)
    attendance_issues = [s for s in subjects_list if s.get("attendance", 0) < 75]
    if overall_attendance < 75:
        att_status = "Needs Attention"
        att_badge = "danger"
        att_action = "Your overall attendance is below the mandatory 75% university eligibility threshold. Attend all upcoming lectures without unexcused absences."
    elif attendance_issues:
        att_status = "Selective Focus Needed"
        att_badge = "warning"
        subj_names = ", ".join([s["subject"] for s in attendance_issues])
        att_action = f"Overall attendance is acceptable ({overall_attendance}%), but {subj_names} is below 75%. Prioritize attendance in these specific classes."
    elif overall_attendance >= 90:
        att_status = "Excellent"
        att_badge = "success"
        att_action = "Outstanding attendance record! Maintain this consistency to qualify for honors recognition."
    else:
        att_status = "Good"
        att_badge = "info"
        att_action = "Attendance is healthy. Continue attending scheduled lecture and laboratory sessions consistently."

    attendance_plan = {
        "overall": overall_attendance,
        "status": att_status,
        "badge": att_badge,
        "action": att_action,
        "issues_count": len(attendance_issues),
        "issues": attendance_issues
    }

    # 7. Top Priorities (Section 5)
    priorities = []
    p_num = 1

    # Priority 1: Weakest Subject
    if primary_weak_subject and primary_weak_subject["total"] < 65:
        priorities.append({
            "number": p_num,
            "level": "HIGH PRIORITY",
            "badge": "danger",
            "icon": "🔴",
            "title": f"Improve {primary_weak_subject['subject']}",
            "metric": f"Current Score: {primary_weak_subject['total']}/100",
            "why": f"Your performance in {primary_weak_subject['subject']} is below your academic target and pulls down your overall SGPI.",
            "action": f"Dedicate 45 minutes daily to revise weak concepts and practice problem sets."
        })
        p_num += 1

    # Priority 2: Attendance (if < 75%)
    if overall_attendance < 75 or len(attendance_issues) > 0:
        priorities.append({
            "number": p_num,
            "level": "HIGH PRIORITY" if overall_attendance < 75 else "MEDIUM PRIORITY",
            "badge": "danger" if overall_attendance < 75 else "warning",
            "icon": "🔴" if overall_attendance < 75 else "🟠",
            "title": "Boost Lecture Attendance",
            "metric": f"Current Attendance: {overall_attendance}%",
            "why": "University regulations require at least 75% attendance to maintain examination eligibility without penalty.",
            "action": "Attend all upcoming theory and lab sessions consistently without unexcused absences."
        })
        p_num += 1

    # Priority 3: External Examination Preparation (ML Prediction)
    if avg_predicted_ext is not None:
        p_lvl = "HIGH PRIORITY" if avg_predicted_ext < 35 else "MEDIUM PRIORITY"
        priorities.append({
            "number": p_num,
            "level": p_lvl,
            "badge": "danger" if avg_predicted_ext < 35 else "warning",
            "icon": "🔴" if avg_predicted_ext < 35 else "🟡",
            "title": "Prepare for External Examination",
            "metric": f"AI Predicted External: {avg_predicted_ext}/70",
            "why": "External examinations contribute the largest share (70%) of your semester grade.",
            "action": "Focus on high-weightage topics identified in question paper intelligence and solve previous papers."
        })
        p_num += 1

    # Priority 4: SGPI Trend Recovery (if declining)
    if trend_direction == "Declining":
        priorities.append({
            "number": p_num,
            "level": "MEDIUM PRIORITY",
            "badge": "warning",
            "icon": "🟠",
            "title": "Reverse Declining SGPI Trend",
            "metric": f"Recent Drop: {sgpi_trend[-2]} → {sgpi_trend[-1]}",
            "why": "A downward trend in successive semesters limits placement and higher studies eligibility.",
            "action": "Schedule dedicated weekly revision blocks and seek faculty office hour guidance."
        })
        p_num += 1
    elif len(priorities) < 3 and ranked_subjects:
        # Positive reinforcement priority
        priorities.append({
            "number": p_num,
            "level": "STANDARD FOCUS",
            "badge": "info",
            "icon": "🟡",
            "title": "Maintain Balanced Academic Routine",
            "metric": f"Overall SGPI: {sgpi}",
            "why": "Consistent study distribution prevents last-minute cramming and protects cumulative grades.",
            "action": "Follow the suggested weekly study roadmap and verify completion via the action checklist."
        })

    # 8. Weekly Study Roadmap (Section 16)
    roadmap = []
    subjs = [s["subject"] for s in ranked_subjects]
    w_name = primary_weak_subject["subject"] if primary_weak_subject else (subjs[0] if subjs else "Core Subject")
    s2_name = subjs[1] if len(subjs) > 1 else w_name
    s3_name = subjs[2] if len(subjs) > 2 else s2_name
    s4_name = subjs[3] if len(subjs) > 3 else w_name

    p1_topic_name = learning_topics[0]["topic"] if learning_topics else "Core Fundamentals"
    p2_topic_name = learning_topics[1]["topic"] if len(learning_topics) > 1 else "Applied Concepts"

    roadmap = [
        {"day": "Monday", "subject": w_name, "activity": f"Foundational Theory & Concepts ({p1_topic_name})", "focus": "Deep Learning"},
        {"day": "Tuesday", "subject": s2_name, "activity": "Lecture Notes Review & Lab Exercises", "focus": "Applied Practice"},
        {"day": "Wednesday", "subject": s3_name, "activity": "Numerical Problems & Analytical Tasks", "focus": "Problem Solving"},
        {"day": "Thursday", "subject": w_name, "activity": f"Targeted Problem Solving ({p2_topic_name})", "focus": "Weak Area Drill"},
        {"day": "Friday", "subject": s4_name, "activity": "Case Studies & Assignment Preparation", "focus": "Consolidation"},
        {"day": "Saturday", "subject": "Exam Focus", "activity": "Previous Semester Question Paper (Timed 60 Mins)", "focus": "Test Readiness"},
        {"day": "Sunday", "subject": "Revision", "activity": "Weekly Self-Assessment & Flashcard Review", "focus": "Retention"}
    ]

    # 9. Action Checklist (Section 17)
    action_checklist = []
    if overall_attendance < 75:
        action_checklist.append({"id": "chk_att", "text": f"Attend next 10 consecutive lectures to raise attendance above 75%", "category": "Attendance"})
    if primary_weak_subject:
        action_checklist.append({"id": "chk_w1", "text": f"Complete {p1_topic_name} notes and 5 practice exercises in {w_name}", "category": "Academic"})
    action_checklist.append({"id": "chk_rev", "text": f"Review key formulas and definitions across all Semester {semester} subjects", "category": "Revision"})
    action_checklist.append({"id": "chk_qp", "text": "Attempt 1 full-length previous semester question paper under exam conditions", "category": "Exam Prep"})
    action_checklist.append({"id": "chk_eval", "text": "Review internal assessment feedback with faculty mentors", "category": "Mentoring"})
    action_checklist.append({"id": "chk_sgpi", "text": f"Track target SGPI benchmark ({round(sgpi + 0.5, 1)}) for next semester progression", "category": "Goals"})

    # 10. Areas Needing Attention Count
    areas_count = len(weak_subjects) + (1 if overall_attendance < 75 else 0) + (1 if trend_direction == "Declining" else 0) + (1 if avg_predicted_ext and avg_predicted_ext < 35 else 0)
    if areas_count == 0:
        areas_count = 1  # Standard maintenance area

    return {
        "student": student,
        "semester": semester,
        "overall_score": avg_marks,
        "overall_performance": detail.get("overall_performance", "Good"),
        "attendance": overall_attendance,
        "attendance_plan": attendance_plan,
        "areas_needing_attention": areas_count,
        "sgpi": sgpi,
        "sgpi_trend_direction": trend_direction,
        "sgpi_trend_symbol": trend_symbol,
        "sgpi_trend_tone": trend_tone,
        "sgpi_commentary": trend_commentary,
        "sgpi_history": sgpi_trend,
        "attendance_history": attendance_trend,
        "trend_labels": trend_labels,
        "has_multiple_semesters": has_multiple_semesters,
        "priorities": priorities,
        "ranked_subjects": ranked_subjects,
        "weak_subjects": weak_subjects,
        "strong_subjects": strong_subjects,
        "primary_weak_subject": primary_weak_subject,
        "learning_topics": learning_topics,
        "revision_topics": revision_topics,
        "practice_topics": practice_topics,
        "exam_intelligence": exam_intelligence,
        "predictions": predictions,
        "avg_predicted_ext": avg_predicted_ext,
        "avg_predicted_total": avg_predicted_total,
        "outlook": outlook,
        "outlook_badge": outlook_badge,
        "outlook_advice": outlook_advice,
        "roadmap": roadmap,
        "action_checklist": action_checklist
    }
