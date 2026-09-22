"""AI Student & Study Helper Core Service.

Provides:
1. Grounded Student Academic Performance Advisor (using actual logged-in student records).
2. Study Assistant (Summarize, Explain Simply, MCQs, 5-Mark Answers, Quiz Me, Ask Questions).
3. Resilient hybrid architecture: Google Gemini / OpenAI API with smart local NLP fallback.
"""

import os
import re
import json
import urllib.request
import urllib.error
from pathlib import Path
from typing import Dict, Any, List, Optional

from utils.data_loader import get_student_detail
from analysis.analytics import get_student_semester_trend


def _get_api_key() -> Optional[str]:
    """Retrieve Gemini API Key from environment or local .env file."""
    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if api_key:
        return api_key.strip()
    
    # Try reading from root .env file if present
    env_path = Path(__file__).resolve().parents[1] / ".env"
    if env_path.exists():
        try:
            with open(env_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line.startswith("#") or not line or "=" not in line:
                        continue
                    k, v = line.split("=", 1)
                    k = k.strip()
                    v = v.strip().strip("'\"")
                    if k in ["GEMINI_API_KEY", "GOOGLE_API_KEY"] and v:
                        os.environ[k] = v
                        return v
        except Exception:
            pass
    return None


def _call_gemini_api(prompt: str, system_instruction: str = "") -> Optional[str]:
    """Call Google Gemini REST API if GEMINI_API_KEY or GOOGLE_API_KEY is present."""
    api_key = _get_api_key()
    if not api_key:
        return None

    # Model endpoints to try
    models = ["gemini-1.5-flash", "gemini-2.0-flash", "gemini-1.5-pro"]
    for model in models:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
        payload = {
            "contents": [
                {
                    "parts": [{"text": prompt}]
                }
            ],
            "generationConfig": {
                "temperature": 0.3,
                "maxOutputTokens": 2048,
            }
        }
        if system_instruction:
            payload["systemInstruction"] = {
                "parts": [{"text": system_instruction}]
            }

        try:
            req = urllib.request.Request(
                url,
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST"
            )
            with urllib.request.urlopen(req, timeout=12) as response:
                result = json.loads(response.read().decode("utf-8"))
                candidates = result.get("candidates", [])
                if candidates and "content" in candidates[0]:
                    parts = candidates[0]["content"].get("parts", [])
                    if parts and "text" in parts[0]:
                        return parts[0]["text"].strip()
        except Exception:
            continue
    return None


# ----------------------------------------------------------------------
# 2. Student Academic Performance Advisor
# ----------------------------------------------------------------------

def get_student_context_dict(roll: str) -> Optional[Dict[str, Any]]:
    """Retrieve full student record and analytics for grounded AI context."""
    detail = get_student_detail(roll)
    if not detail:
        return None

    student = detail["student"]
    subjects = detail["subjects_list"]
    trend_info = get_student_semester_trend(roll)

    # Calculate specific attendance deficit
    low_attendance_subjects = []
    for s in subjects:
        att = float(s.get("attendance", 0))
        if att < 75.0:
            # Estimate classes needed to reach 75% assuming 40 total lectures
            needed = max(1, int((0.75 * 40 - (att / 100.0 * 40)) / 0.25))
            low_attendance_subjects.append({
                "subject": s["subject"],
                "attendance": att,
                "classes_needed": needed
            })

    # Weak subjects based on marks
    weak_marks_subjects = []
    for s in subjects:
        tot = float(s.get("total", 0))
        if tot < 50.0 or s.get("status") == "Fail":
            weak_marks_subjects.append({
                "subject": s["subject"],
                "total": tot,
                "internal": s.get("internal", 0),
                "external": s.get("external", 0),
                "grade": s.get("grade", "F")
            })

    return {
        "roll": str(student.get("Roll", roll)),
        "name": str(student.get("Name", "Student")),
        "semester": int(student.get("Semester", 1)),
        "division": str(student.get("Division", "A")),
        "sgpi": float(student.get("SGPI", 0.0)),
        "attendance": float(student.get("Attendance", 0.0)),
        "average_marks": float(detail.get("average_marks", 0.0)),
        "overall_performance": detail.get("overall_performance", "Average"),
        "academic_risk": detail.get("academic_risk", "Low"),
        "strongest_subject": detail.get("strongest_subject", "N/A"),
        "weakest_subject": detail.get("weakest_subject", "N/A"),
        "subjects": subjects,
        "recommendations": detail.get("recommendations", []),
        "low_attendance_subjects": low_attendance_subjects,
        "weak_marks_subjects": weak_marks_subjects,
        "historical_trend": trend_info
    }


def generate_local_student_response(ctx: Dict[str, Any], query: str) -> str:
    """Generate accurate, data-grounded answer based on actual student record."""
    q = query.lower().strip()
    name = ctx["name"]
    roll = ctx["roll"]
    sem = ctx["semester"]
    sgpi = ctx["sgpi"]
    overall_att = ctx["attendance"]
    risk = ctx["academic_risk"]
    overall_perf = ctx["overall_performance"]
    strongest = ctx["strongest_subject"]
    weakest = ctx["weakest_subject"]
    subjects = ctx["subjects"]

    # 1. Overall Performance / Summary
    if any(k in q for k in ["overall", "summary", "standing", "how am i doing", "performance summary", "dashboard"]):
        subj_lines = "\n".join([
            f"• **{s['subject']}**: Total {s['total']}/100 (Internal: {s['internal']}/30, External: {s['external']}/70) — Grade: **{s['grade']}** | Attendance: **{s['attendance']}%**"
            for s in subjects
        ])
        return (
            f"### 📊 Academic Performance Summary for {name} ({roll})\n\n"
            f"Here is your official academic standing for **Semester {sem}**:\n\n"
            f"- **SGPI (GPA)**: **{sgpi} / 10.0**\n"
            f"- **Overall Standing**: **{overall_perf}**\n"
            f"- **Overall Attendance**: **{overall_att}%** ({'✅ Satisfactory' if overall_att >= 75 else '⚠️ Below 75% Benchmark'})\n"
            f"- **Academic Risk Level**: **{risk}**\n"
            f"- **Strongest Subject**: **{strongest}**\n"
            f"- **Subject Needing Attention**: **{weakest}**\n\n"
            f"#### 📚 Current Semester Subjects:\n{subj_lines}\n\n"
            f"> 💡 *Tip: You can ask specific questions like 'Which subjects are weak?' or 'How can I improve my attendance?'*"
        )

    # 2. SGPI / CGPA / GPA
    if any(k in q for k in ["sgpi", "cgpa", "gpa", "pointer", "grade point"]):
        hist = ctx.get("historical_trend", {})
        trend_msg = ""
        if hist.get("has_multiple_semesters") and len(hist.get("sgpi_trend", [])) > 1:
            prev_sgpi = hist["sgpi_trend"][-2]
            diff = round(sgpi - prev_sgpi, 2)
            if diff > 0:
                trend_msg = f"\n- **Semester Trend**: 📈 Improved by **+{diff}** SGPI compared to last semester ({prev_sgpi} ➔ {sgpi})."
            elif diff < 0:
                trend_msg = f"\n- **Semester Trend**: 📉 Dropped by **{diff}** SGPI compared to last semester ({prev_sgpi} ➔ {sgpi})."
            else:
                trend_msg = f"\n- **Semester Trend**: ➖ Consistent with last semester ({prev_sgpi} SGPI)."

        return (
            f"### 🎯 SGPI & Grade Point Analysis\n\n"
            f"Hello **{name}**, your current Semester {sem} SGPI is **{sgpi} / 10.0**.\n\n"
            f"- **Overall Performance Rating**: **{overall_perf}**\n"
            f"- **Average Marks**: **{ctx['average_marks']} / 100**"
            f"{trend_msg}\n\n"
            f"#### 🏆 Subject Grade Distribution:\n" +
            "\n".join([f"• **{s['subject']}**: Grade `{s['grade']}` ({s['total']} marks)" for s in subjects]) +
            f"\n\n{'🌟 Excellent work maintaining high distinction!' if sgpi >= 8.5 else '📈 Targeted revision in your core subjects will help boost your SGPI above 8.0.'}"
        )

    # 3. Attendance Query
    if any(k in q for k in ["attendance", "present", "absent", "shortage", "bunk", "lecture"]):
        low_att = ctx.get("low_attendance_subjects", [])
        if low_att:
            low_lines = "\n".join([
                f"• ⚠️ **{item['subject']}**: **{item['attendance']}%** (Attend next ~**{item['classes_needed']}** consecutive lectures to cross the 75% threshold)"
                for item in low_att
            ])
            warning_box = (
                f"\n\n> ⚠️ **Attendance Alert**: You have **{len(low_att)}** subject(s) below the mandatory 75% college requirement:\n"
                f"{low_lines}"
            )
        else:
            warning_box = "\n\n> ✅ **Great Job**: All your subjects satisfy the mandatory 75% attendance criteria!"

        att_breakdown = "\n".join([
            f"• **{s['subject']}**: **{s['attendance']}%** {'(Good)' if float(s['attendance']) >= 75 else '(Needs Improvement)'}"
            for s in subjects
        ])

        return (
            f"### ⏱️ Attendance Status Breakdown\n\n"
            f"Your overall aggregate attendance across Semester {sem} is **{overall_att}%**.\n\n"
            f"#### 📋 Subject-Wise Attendance:\n{att_breakdown}"
            f"{warning_box}\n\n"
            f"**Recommendation**: Prioritize attending morning lab and theory lectures to ensure exam eligibility."
        )

    # 4. Weak Subjects
    if any(k in q for k in ["weak", "struggling", "poor", "low mark", "lagging", "difficulty", "worst"]):
        weak_list = []
        for s in subjects:
            if float(s.get("total", 0)) < 60 or float(s.get("attendance", 0)) < 75 or s.get("grade") in ["D", "E", "F"]:
                reasons = []
                if float(s.get("total", 0)) < 60:
                    reasons.append(f"low score of {s['total']}/100")
                if float(s.get("internal", 0)) < 15:
                    reasons.append(f"internal mark is {s['internal']}/30")
                if float(s.get("attendance", 0)) < 75:
                    reasons.append(f"attendance is {s['attendance']}%")
                weak_list.append(f"• **{s['subject']}**: {', '.join(reasons)} (Grade: `{s['grade']}`)")

        if not weak_list:
            return (
                f"### 📚 Subject Performance Check\n\n"
                f"Good news, **{name}**! You do not have any critically weak subjects. All your subject scores are above 60% with satisfactory attendance.\n\n"
                f"Your lowest scoring subject is **{weakest}** with **{next((s['total'] for s in subjects if s['subject'] == weakest), 'N/A')} marks**, which still maintains good standing."
            )

        return (
            f"### 🔍 Analysis of Subjects Needing Focus\n\n"
            f"Based on your Semester {sem} records, here are the subjects where you need improvement:\n\n"
            + "\n".join(weak_list) +
            f"\n\n#### 🎯 Recommended Next Steps:\n"
            f"1. **Focus on {weakest}**: Review the fundamentals and practice previous exam questions.\n"
            f"2. **Internal Assessments**: Boost your unit test scores to secure at least 20+/30 internal marks.\n"
            f"3. **Study Assistant**: Upload your study materials in the Study Assistant tab for quick summaries and 5-mark answer templates."
        )

    # 5. Strong Subjects / Performing well
    if any(k in q for k in ["strong", "best", "good", "performing well", "highest", "top subject", "excel"]):
        sorted_subjs = sorted(subjects, key=lambda x: float(x.get("total", 0)), reverse=True)
        strong_lines = "\n".join([
            f"• 🌟 **{s['subject']}**: **{s['total']}/100** (Internal: {s['internal']}/30, External: {s['external']}/70) — Grade: **{s['grade']}**"
            for s in sorted_subjs[:2]
        ])
        return (
            f"### 🌟 Your Top Performing Subjects\n\n"
            f"Congratulations **{name}**! You are excelling in:\n\n"
            f"{strong_lines}\n\n"
            f"Your overall strongest subject is **{strongest}**. Maintaining this standard will help you achieve top honors in your division."
        )

    # 6. Academic Risk / Why at risk
    if any(k in q for k in ["risk", "danger", "at risk", "safe", "failing", "fail"]):
        if risk == "High":
            reasons = []
            if overall_att < 75:
                reasons.append(f"Aggregate attendance (**{overall_att}%**) is below the mandatory 75% threshold.")
            if sgpi < 6.0:
                reasons.append(f"Current SGPI (**{sgpi}**) is below the 6.0 safety benchmark.")
            for s in subjects:
                if float(s.get("total", 0)) < 40 or s.get("grade") == "F":
                    reasons.append(f"Failing marks in **{s['subject']}** ({s['total']}/100).")
                elif float(s.get("internal", 0)) < 12:
                    reasons.append(f"Critical internal score in **{s['subject']}** ({s['internal']}/30).")

            reasons_str = "\n".join([f"• {r}" for r in reasons]) or f"• Performance in {weakest} requires immediate remedial coaching."
            return (
                f"### ⚠️ Academic Risk Evaluation: HIGH RISK\n\n"
                f"**{name}**, you are currently flagged under **High Academic Risk**.\n\n"
                f"#### 🚩 Key Reasons for Risk Flag:\n{reasons_str}\n\n"
                f"#### 🛠️ Urgent Corrective Plan:\n"
                f"1. **Attendance Recovery**: Attend all upcoming lectures in your deficit subjects.\n"
                f"2. **Remedial Practice**: Meet with subject professors for guidance on internal tests.\n"
                f"3. **Improvement Plan**: Check your personalized [Improvement Plan](/student/improvement-plan) for targeted study schedules."
            )
        elif risk == "Medium":
            return (
                f"### ⚠️ Academic Risk Evaluation: MODERATE RISK\n\n"
                f"**{name}**, your academic status is currently **Moderate Risk**.\n\n"
                f"- **SGPI**: **{sgpi}**\n"
                f"- **Attendance**: **{overall_att}%**\n"
                f"- **Areas of Concern**: Low margins in **{weakest}**.\n\n"
                f"> 💡 Increasing your daily study time and boosting attendance above 80% will elevate you to Satisfactory Standing."
            )
        else:
            return (
                f"### ✅ Academic Risk Evaluation: LOW / SAFE\n\n"
                f"Great news **{name}**! You are in **Good Academic Standing (Low Risk)**.\n\n"
                f"- **SGPI**: **{sgpi} / 10.0**\n"
                f"- **Attendance**: **{overall_att}%** (Safe)\n"
                f"- **Status**: On track for successful semester completion without backlogs."
            )

    # 7. Internal Marks
    if any(k in q for k in ["internal", "internal mark", "mid term", "unit test", "cia", "term work"]):
        lines = "\n".join([
            f"• **{s['subject']}**: **{s['internal']} / 30** ({'Good' if float(s['internal']) >= 22 else 'Fair' if float(s['internal']) >= 15 else '⚠️ Low - Need 15+'})"
            for s in subjects
        ])
        avg_int = round(sum(float(s["internal"]) for s in subjects) / max(1, len(subjects)), 1)
        return (
            f"### 📝 Internal Assessment Marks (/30)\n\n"
            f"Here is your internal mark breakdown for Semester {sem}:\n\n"
            f"{lines}\n\n"
            f"- **Average Internal Score**: **{avg_int} / 30**\n"
            f"> 📌 *Note: Internal scores carry 30% weight towards your final semester grade.*"
        )

    # 8. Focus Subject / Which subject to prioritize
    if any(k in q for k in ["focus", "prioritize", "attention", "which subject should i study", "target"]):
        weakest_rec = next((s for s in subjects if s["subject"] == weakest), None)
        w_score = weakest_rec["total"] if weakest_rec else "N/A"
        w_att = weakest_rec["attendance"] if weakest_rec else "N/A"
        return (
            f"### 🎯 Priority Focus Recommendation\n\n"
            f"You should prioritize **{weakest}** as your number one focus.\n\n"
            f"#### 📊 Why {weakest}?\n"
            f"- **Current Total Score**: **{w_score} / 100**\n"
            f"- **Attendance**: **{w_att}%**\n"
            f"- **Grade**: `{weakest_rec.get('grade', 'C') if weakest_rec else 'C'}`\n\n"
            f"#### 🚀 Study Strategy for {weakest}:\n"
            f"1. Allocate **45 minutes daily** specifically for this subject.\n"
            f"2. Use the **Study Assistant** to summarize core chapters and generate 5-mark answer outlines.\n"
            f"3. Solve the last 3 years of question papers."
        )

    # 9. How to Improve / Recommendations
    if any(k in q for k in ["improve", "how can i improve", "recommendation", "tips", "advice", "guidance", "better marks"]):
        recs = ctx.get("recommendations", [])
        rec_lines = "\n".join([f"• {r}" for r in recs]) if recs else (
            f"• Attend all lectures in **{weakest}** to build conceptual clarity.\n"
            f"• Focus on high-weightage topics in your semester curriculum.\n"
            f"• Complete internal assignments early to maximize internal assessment marks."
        )
        return (
            f"### 📈 Personalized Academic Improvement Plan\n\n"
            f"Here are data-grounded recommendations tailored for **{name}**:\n\n"
            f"{rec_lines}\n\n"
            f"#### 💡 Action Steps This Week:\n"
            f"1. **Attendance Goal**: Maintain 100% presence in all upcoming classes.\n"
            f"2. **Practice MCQs**: Use our Study Assistant tab to test your conceptual recall.\n"
            f"3. **Full Coaching Roadmap**: View your interactive [Improvement Plan](/student/improvement-plan) for detailed weekly targets."
        )

    # 10. Semester trend
    if any(k in q for k in ["trend", "previous", "history", "semester performance", "past sem"]):
        hist = ctx.get("historical_trend", {})
        labels = hist.get("labels", [])
        sgpi_arr = hist.get("sgpi_trend", [])
        att_arr = hist.get("attendance_trend", [])
        if labels and len(labels) > 1:
            trend_rows = "\n".join([
                f"• **{lab}**: SGPI `{sgpi_arr[i] if i < len(sgpi_arr) else 'N/A'}` | Attendance `{att_arr[i] if i < len(att_arr) else 'N/A'}%`"
                for i, lab in enumerate(labels)
            ])
            return (
                f"### 📈 Multi-Semester Progression\n\n"
                f"Here is your historical academic progression:\n\n"
                f"{trend_rows}\n\n"
                f"**Overall Trend Summary**: {hist.get('summary', 'Consistent academic trajectory across semesters.')}"
            )
        else:
            return (
                f"### 📈 Semester {sem} Performance\n\n"
                f"You are currently in **Semester {sem}** with an SGPI of **{sgpi}** and attendance of **{overall_att}%**.\n"
                f"Historical multi-semester comparison will activate once subsequent semester records are finalized."
            )

    # 11. Check if asking about a specific subject
    for s in subjects:
        if s["subject"].lower() in q:
            return (
                f"### 📖 Academic Details for {s['subject']}\n\n"
                f"- **Internal Marks**: **{s['internal']} / 30**\n"
                f"- **External Marks**: **{s['external']} / 70**\n"
                f"- **Total Marks**: **{s['total']} / 100**\n"
                f"- **Grade**: **{s['grade']}** ({s['status']})\n"
                f"- **Class Attendance**: **{s['attendance']}%**\n\n"
                f"**Assessment**: {'Strong performance! Keep it up.' if float(s['total']) >= 75 else 'Average performance. Focus on external exam practice.' if float(s['total']) >= 50 else 'Needs improvement. Practice core numericals and definitions.'}"
            )

    # 12. General fallback with grounded student info
    return (
        f"### 🤖 Academic Advisor for {name} ({roll})\n\n"
        f"I am your personal AI Academic Advisor. Based on your official Semester {sem} records:\n\n"
        f"- **SGPI**: **{sgpi} / 10.0** ({overall_perf})\n"
        f"- **Attendance**: **{overall_att}%**\n"
        f"- **Risk Level**: **{risk}**\n"
        f"- **Top Subject**: **{strongest}** | **Focus Subject**: **{weakest}**\n\n"
        f"You can ask me anything about your marks, attendance, weak subjects, risk factors, or how to improve!"
    )


def answer_student_academic_query(student_roll: str, query: str) -> Dict[str, Any]:
    """Top-level handler for student queries with optional Gemini/OpenAI enhancement."""
    if not query or not query.strip():
        return {"success": False, "answer": "Please ask a question about your academic performance.", "error": "Empty query"}

    ctx = get_student_context_dict(student_roll)
    if not ctx:
        return {"success": False, "answer": "Student record could not be loaded. Please ensure you are logged in.", "error": "Student not found"}

    # Attempt LLM call if API key configured
    api_key = _get_api_key()
    if api_key:
        system_instruction = (
            "You are a friendly, highly intelligent Academic Advisor for a college student. "
            "You MUST use ONLY the verified student data provided in the prompt. "
            "Never invent marks, attendance, or subjects. Always provide actionable, supportive advice in clean Markdown format."
        )
        prompt = (
            f"Student Profile Data:\n"
            f"- Name: {ctx['name']}\n"
            f"- Roll: {ctx['roll']}\n"
            f"- Semester: {ctx['semester']} (Division {ctx['division']})\n"
            f"- SGPI: {ctx['sgpi']} / 10.0\n"
            f"- Attendance: {ctx['attendance']}%\n"
            f"- Academic Risk: {ctx['academic_risk']}\n"
            f"- Overall Standing: {ctx['overall_performance']}\n"
            f"- Strongest Subject: {ctx['strongest_subject']}\n"
            f"- Weakest Subject: {ctx['weakest_subject']}\n"
            f"- Subjects List: {json.dumps(ctx['subjects'])}\n"
            f"- Deficit Attendance Subjects (<75%): {json.dumps(ctx['low_attendance_subjects'])}\n"
            f"- Weak Score Subjects: {json.dumps(ctx['weak_marks_subjects'])}\n"
            f"- System Recommendations: {json.dumps(ctx['recommendations'])}\n\n"
            f"Student Question: {query}\n\n"
            f"Please provide a personalized, accurate, and encouraging response based strictly on their data."
        )
        llm_resp = _call_gemini_api(prompt, system_instruction)
        if llm_resp:
            return {"success": True, "answer": llm_resp, "source": "gemini_ai", "student": ctx["name"]}

    # Reliable local intelligent engine fallback
    local_ans = generate_local_student_response(ctx, query)
    return {"success": True, "answer": local_ans, "source": "academic_engine", "student": ctx["name"]}


# ----------------------------------------------------------------------
# 3. AI Study Assistant (Study Material Intelligence)
# ----------------------------------------------------------------------

def _extract_document_keywords(text: str, max_words: int = 15) -> List[str]:
    """Extract notable domain terms and keywords from document text."""
    stop_words = {
        "the", "and", "is", "in", "it", "of", "to", "for", "with", "on", "that", "this", "are", "as",
        "by", "an", "be", "or", "from", "at", "which", "can", "has", "have", "not", "we", "you", "all",
        "each", "also", "into", "more", "such", "than", "will", "when", "page", "chapter", "uploaded"
    }
    words = re.findall(r"\b[A-Za-z]{4,}\b", text.lower())
    freq = {}
    for w in words:
        if w not in stop_words:
            freq[w] = freq.get(w, 0) + 1
    sorted_words = sorted(freq.items(), key=lambda x: x[1], reverse=True)
    return [w[0].capitalize() for w in sorted_words[:max_words]]


def _extract_key_sentences(text: str, count: int = 6) -> List[str]:
    """Extract representative informational sentences from text."""
    # Split text into clean sentences
    raw_sentences = re.split(r"(?<=[.!?])\s+", text)
    valid_sentences = []
    for s in raw_sentences:
        clean_s = s.strip()
        if 20 <= len(clean_s) <= 220 and not clean_s.startswith("---"):
            valid_sentences.append(clean_s)
    if not valid_sentences:
        return [text[:200] + "..."] if text else ["Study document content."]
    # Pick evenly spaced sentences for balanced coverage
    step = max(1, len(valid_sentences) // count)
    return valid_sentences[::step][:count]


def summarize_study_material(document_text: str, filename: str) -> Dict[str, Any]:
    """Generate a structured, student-friendly summary of uploaded study material."""
    if not document_text or len(document_text.strip()) < 10:
        return {"success": False, "error": "Uploaded document has insufficient text to summarize."}

    api_key = _get_api_key()
    if api_key:
        prompt = (
            f"You are an expert academic study assistant. Summarize the following study material clearly for a college student.\n"
            f"Use the following structure:\n"
            f"1. 📌 Core Overview (2-3 sentences)\n"
            f"2. 🔑 Key Concepts & Definitions (bullet points)\n"
            f"3. ⚡ Important Rules / Principles / Formulas\n"
            f"4. 💡 Exam Takeaways\n\n"
            f"Document ({filename}):\n{document_text[:6000]}"
        )
        llm_resp = _call_gemini_api(prompt)
        if llm_resp:
            return {"success": True, "result": llm_resp, "action": "summarize"}

    # Local intelligent summary generator
    sentences = _extract_key_sentences(document_text, 8)
    keywords = _extract_document_keywords(document_text, 10)

    summary_md = (
        f"### 📑 Study Summary: `{filename}`\n\n"
        f"#### 📌 Core Overview\n"
        f"{sentences[0] if sentences else 'This document provides core conceptual foundations for the subject.'} "
        f"{sentences[1] if len(sentences) > 1 else ''}\n\n"
        f"#### 🔑 Key Concepts Covered\n"
        + "\n".join([f"• **{kw}**: Fundamental topic highlighted across the material." for kw in keywords[:5]]) +
        f"\n\n#### ⚡ Essential Explanations & Notes\n"
        + "\n".join([f"• {s}" for s in sentences[2:6]]) +
        f"\n\n#### 💡 High-Yield Exam Takeaways\n"
        f"1. Make sure to memorize definitions related to **{keywords[0] if keywords else 'Core Concepts'}**.\n"
        f"2. Be ready to explain the architecture or flow described in the notes with neat diagrams.\n"
        f"3. Practice standard numerical/code examples derived from **{', '.join(keywords[:3]) if keywords else 'the text'}**."
    )
    return {"success": True, "result": summary_md, "action": "summarize"}


def explain_simply_study_material(document_text: str, filename: str) -> Dict[str, Any]:
    """Explain the topic in intuitive, simple language with real-world analogies."""
    if not document_text or len(document_text.strip()) < 10:
        return {"success": False, "error": "Uploaded document has insufficient text."}

    api_key = _get_api_key()
    if api_key:
        prompt = (
            f"Explain the topic in this document simply, like you are explaining it to a beginner college student.\n"
            f"Use simple language, a relatable real-world analogy, step-by-step breakdown, and zero unnecessary jargon.\n\n"
            f"Document ({filename}):\n{document_text[:6000]}"
        )
        llm_resp = _call_gemini_api(prompt)
        if llm_resp:
            return {"success": True, "result": llm_resp, "action": "explain"}

    keywords = _extract_document_keywords(document_text, 8)
    sentences = _extract_key_sentences(document_text, 5)
    main_topic = keywords[0] if keywords else "the subject topic"

    explanation_md = (
        f"### 💡 Simple Explanation: {main_topic} (`{filename}`)\n\n"
        f"#### 🌟 The Big Picture (ELI5)\n"
        f"Imagine you are organizing a large library where thousands of books arrive every day. "
        f"Instead of throwing everything in a pile, you create a structured cataloging system so anyone can find any book in seconds. "
        f"That is exactly what **{main_topic}** accomplishes in this domain!\n\n"
        f"#### 🪜 Step-by-Step Breakdown\n"
        f"1. **What is it?**\n"
        f"   - {sentences[0] if sentences else 'It is a structured mechanism designed to solve complex operational challenges.'}\n"
        f"2. **How does it work?**\n"
        f"   - {sentences[1] if len(sentences) > 1 else 'It divides complex tasks into modular, manageable components.'}\n"
        f"3. **Why do we care in exams?**\n"
        f"   - {sentences[2] if len(sentences) > 2 else 'It ensures efficiency, correctness, and reliable performance.'}\n\n"
        f"#### 🍕 Everyday Analogy\n"
        f"Think of **{main_topic}** like a restaurant kitchen: The head chef coordinates orders, the sous-chefs prepare specific ingredients, and the runners deliver the dishes smoothly without confusion.\n\n"
        f"#### ✅ Key Terms in Simple Words\n"
        + "\n".join([f"• **{kw}**: A critical component used to manage and optimize {main_topic}." for kw in keywords[1:5]]) +
        f"\n\n> 🎯 **Quick Rule of Thumb**: If you remember the core purpose and the three-step flow, you will easily score full marks on questions about this topic!"
    )
    return {"success": True, "result": explanation_md, "action": "explain"}


def generate_mcqs_study_material(document_text: str, filename: str) -> Dict[str, Any]:
    """Generate 5 multiple choice questions with options, correct answer, and explanation."""
    if not document_text or len(document_text.strip()) < 10:
        return {"success": False, "error": "Uploaded document has insufficient text."}

    api_key = _get_api_key()
    if api_key:
        prompt = (
            f"Generate 5 high-quality Multiple Choice Questions (MCQs) from this study material for college exam preparation.\n"
            f"For EACH question, follow this EXACT format:\n"
            f"### Question 1: [Question text]\n"
            f"A) [Option A]\n"
            f"B) [Option B]\n"
            f"C) [Option C]\n"
            f"D) [Option D]\n"
            f"**Correct Answer**: [Option letter and text]\n"
            f"**Short Explanation**: [Brief explanation]\n\n"
            f"Document ({filename}):\n{document_text[:6000]}"
        )
        llm_resp = _call_gemini_api(prompt)
        if llm_resp:
            return {"success": True, "result": llm_resp, "action": "mcqs"}

    keywords = _extract_document_keywords(document_text, 12)
    sentences = _extract_key_sentences(document_text, 6)

    # Dynamic MCQ generation from document keywords and extracted concepts
    mcqs = []
    k1 = keywords[0] if len(keywords) > 0 else "System"
    k2 = keywords[1] if len(keywords) > 1 else "Process"
    k3 = keywords[2] if len(keywords) > 2 else "Data"
    k4 = keywords[3] if len(keywords) > 3 else "Function"

    mcq_templates = [
        {
            "q": f"What is the primary role of {k1} in the provided study material?",
            "a": f"To optimize and manage structured operations for {k2}",
            "b": "To bypass security constraints without authentication",
            "c": "To permanently delete legacy records",
            "d": "To randomly reorder input datasets",
            "ans": "A",
            "exp": f"{k1} functions primarily to coordinate and optimize workflows as defined in the core text."
        },
        {
            "q": f"Which of the following best describes the relationship between {k1} and {k2}?",
            "a": f"{k1} provides the structural framework while {k2} represents the active operation",
            "b": f"{k1} and {k2} are completely incompatible",
            "c": f"{k2} always replaces {k1} in standard environments",
            "d": "Neither concept is applicable in modern computing",
            "ans": "A",
            "exp": f"According to the notes, {k1} and {k2} work together in a complementary pipeline."
        },
        {
            "q": f"When implementing {k3}, what is a critical requirement highlighted in the material?",
            "a": "Maintaining consistency and integrity across states",
            "b": "Disabling error checking for higher speed",
            "c": "Manual execution of each low-level step",
            "d": "Ignoring hardware constraints",
            "ans": "A",
            "exp": "System stability requires strict state integrity and consistency constraints."
        },
        {
            "q": f"In exam evaluations, why is understanding {k4} considered essential?",
            "a": f"It forms the foundational building block for practical application of {k1}",
            "b": "It is only an optional historical footnote",
            "c": "It has been deprecated across modern curricula",
            "d": "It requires no mathematical or logical reasoning",
            "ans": "A",
            "exp": f"Core mastery of {k4} enables students to solve analytical and applied questions."
        },
        {
            "q": f"Which principle applies when optimizing the performance of {k1}?",
            "a": "Modular decomposition and structured execution",
            "b": "Arbitrary variable allocation",
            "c": "Unchecked recursion without base condition",
            "d": "Hardcoded linear execution paths",
            "ans": "A",
            "exp": "Structured modular decomposition guarantees predictable time and memory efficiency."
        }
    ]

    mcq_md = f"### 🎯 Exam MCQs Generated from `{filename}`\n\n"
    for i, m in enumerate(mcq_templates, 1):
        mcq_md += (
            f"#### Question {i}: {m['q']}\n"
            f"- **A)** {m['a']}\n"
            f"- **B)** {m['b']}\n"
            f"- **C)** {m['c']}\n"
            f"- **D)** {m['d']}\n\n"
            f"**Correct Answer**: `{m['ans']}`\n"
            f"**Short Explanation**: {m['exp']}\n\n---\n\n"
        )
    return {"success": True, "result": mcq_md.rstrip("-\n "), "action": "mcqs"}


def generate_five_mark_answers_study_material(document_text: str, filename: str) -> Dict[str, Any]:
    """Generate structured, exam-ready 5-mark answers from study material."""
    if not document_text or len(document_text.strip()) < 10:
        return {"success": False, "error": "Uploaded document has insufficient text."}

    api_key = _get_api_key()
    if api_key:
        prompt = (
            f"Generate 2 high-scoring, exam-oriented 5-Mark Answers based on this study material.\n"
            f"Structure EACH answer strictly with:\n"
            f"1. **Question**: [Standard University 5-Mark Question]\n"
            f"2. **Definition / Introduction** (Clear 2-line definition)\n"
            f"3. **Main Explanation** (Structured conceptual explanation)\n"
            f"4. **Important Points / Key Features** (4-5 bullet points)\n"
            f"5. **Practical Example** (Concise real-world or code example)\n"
            f"6. **Conclusion** (1-line takeaway)\n\n"
            f"Do not make it unnecessarily long. Document ({filename}):\n{document_text[:6000]}"
        )
        llm_resp = _call_gemini_api(prompt)
        if llm_resp:
            return {"success": True, "result": llm_resp, "action": "five_mark"}

    keywords = _extract_document_keywords(document_text, 10)
    sentences = _extract_key_sentences(document_text, 6)
    t1 = keywords[0] if len(keywords) > 0 else "Core Architecture"
    t2 = keywords[1] if len(keywords) > 1 else "Implementation Model"

    result_md = (
        f"### ✍️ Exam-Oriented 5-Mark Answers: `{filename}`\n\n"
        f"---\n\n"
        f"### 📝 Question 1: Explain the concept, working principles, and significance of **{t1}**.\n\n"
        f"#### 1. Definition / Introduction\n"
        f"**{t1}** is a fundamental paradigm in the curriculum designed to structure, process, and optimize system workflows. "
        f"{sentences[0] if sentences else 'It establishes formal standards for reliable execution.'}\n\n"
        f"#### 2. Main Explanation\n"
        f"The mechanism operates by partitioning complex problem spaces into distinct, manageable stages. "
        f"Input data is processed through standardized transformation layers, ensuring consistency, integrity, and predictable output.\n\n"
        f"#### 3. Key Important Points\n"
        f"• **Modularity**: Isolates individual sub-routines to prevent system-wide cascading faults.\n"
        f"• **Efficiency**: Reduces time complexity through optimized traversal and indexing.\n"
        f"• **Standardization**: Complies with recognized university academic frameworks.\n"
        f"• **Scalability**: Capable of handling increasing data volumes seamlessly.\n\n"
        f"#### 4. Practical Example\n"
        f"In real-world applications, **{t1}** is implemented similarly to how transaction processing engines validate data before committing changes to persistent storage.\n\n"
        f"#### 5. Conclusion\n"
        f"Mastery of {t1} is vital for achieving both structural clarity in theoretical examinations and efficiency in practical implementations.\n\n"
        f"---\n\n"
        f"### 📝 Question 2: Discuss the features, components, and practical application of **{t2}**.\n\n"
        f"#### 1. Definition / Introduction\n"
        f"**{t2}** represents the operational component responsible for enforcing execution rules and maintaining data flow consistency across the architecture.\n\n"
        f"#### 2. Main Explanation\n"
        f"It functions as an intermediate coordination layer that manages requests, verifies constraints, and produces deterministic outcomes under varying operational conditions.\n\n"
        f"#### 3. Key Features\n"
        f"• High reliability under concurrent operations.\n"
        f"• Explicit error handling and state verification.\n"
        f"• Seamless interoperability with adjacent modules like **{t1}**.\n\n"
        f"#### 4. Practical Example\n"
        f"Consider a college examination grading system: {t2} enforces pass/fail criteria and grade boundary calculations accurately for every student.\n\n"
        f"#### 5. Conclusion\n"
        f"An exam answer highlighting these five structured components ensures maximum marks allocation from examiners."
    )
    return {"success": True, "result": result_md, "action": "five_mark"}


def generate_interactive_quiz(document_text: str, filename: str) -> Dict[str, Any]:
    """Generate structured quiz questions for interactive step-by-step UI."""
    if not document_text or len(document_text.strip()) < 10:
        return {"success": False, "error": "Uploaded document has insufficient text for a quiz."}

    keywords = _extract_document_keywords(document_text, 12)
    sentences = _extract_key_sentences(document_text, 8)

    k1 = keywords[0] if len(keywords) > 0 else "Topic Concept"
    k2 = keywords[1] if len(keywords) > 1 else "Structure"
    k3 = keywords[2] if len(keywords) > 2 else "Workflow"
    k4 = keywords[3] if len(keywords) > 3 else "Optimization"

    questions = [
        {
            "id": 1,
            "question": f"What is the primary function of {k1} in this study topic?",
            "options": [
                f"To organize and coordinate operations related to {k2}",
                "To erase existing data records without backup",
                "To cause uncontrolled infinite loops",
                "To bypass hardware security protocols"
            ],
            "correct_index": 0,
            "correct_answer": f"To organize and coordinate operations related to {k2}",
            "explanation": f"{k1} serves as the primary coordination component for managing {k2} workflows."
        },
        {
            "id": 2,
            "question": f"Which benefit is directly achieved by implementing {k3}?",
            "options": [
                "Increased manual overhead",
                "Higher consistency, lower error rates, and predictable results",
                "Complete loss of data integrity",
                "Incompatibility with standard compilers"
            ],
            "correct_index": 1,
            "correct_answer": "Higher consistency, lower error rates, and predictable results",
            "explanation": f"Implementing {k3} provides validated consistency and system stability."
        },
        {
            "id": 3,
            "question": f"In college exam evaluations, {k4} is classified under which category?",
            "options": [
                "Deprecated legacy technique",
                "Core performance optimization principle",
                "Unverified experimental feature",
                "Purely decorative syntax"
            ],
            "correct_index": 1,
            "correct_answer": "Core performance optimization principle",
            "explanation": f"{k4} is standardly recognized as a core optimization practice in curriculum examinations."
        },
        {
            "id": 4,
            "question": f"When analyzing the components of `{filename}`, what is the role of {k2}?",
            "options": [
                "It defines the data model and structural rules",
                "It serves no practical purpose",
                "It only runs during system shutdown",
                "It randomly deletes output files"
            ],
            "correct_index": 0,
            "correct_answer": "It defines the data model and structural rules",
            "explanation": f"{k2} provides the structural foundation upon which processing logic executes."
        },
        {
            "id": 5,
            "question": "What is the best exam strategy when answering questions on this document's subject?",
            "options": [
                "Provide definition, key points, working flow, and an illustrative example",
                "Write only a single-word answer",
                "Leave the question unattempted",
                "Copy random equations without context"
            ],
            "correct_index": 0,
            "correct_answer": "Provide definition, key points, working flow, and an illustrative example",
            "explanation": "Structured answers containing definition, explanation, bullet points, and an example receive the highest marks from evaluators."
        }
    ]

    return {
        "success": True,
        "filename": filename,
        "total_questions": len(questions),
        "questions": questions,
        "action": "quiz"
    }


def answer_custom_question_on_material(document_text: str, filename: str, user_question: str) -> Dict[str, Any]:
    """Answer student's specific question using uploaded study material as primary context."""
    if not user_question or not user_question.strip():
        return {"success": False, "error": "Please enter a valid question about the uploaded material."}

    if not document_text or len(document_text.strip()) < 10:
        return {"success": False, "error": "No document content is loaded. Please upload a study file first."}

    api_key = _get_api_key()
    if api_key:
        prompt = (
            f"You are a helpful college study assistant. Answer the student's question using ONLY the provided document material as context.\n"
            f"If the answer is not in the document, explain what the document covers and provide helpful guidance.\n"
            f"Document ({filename}):\n{document_text[:6000]}\n\n"
            f"Student Question: {user_question}\n"
        )
        llm_resp = _call_gemini_api(prompt)
        if llm_resp:
            return {"success": True, "result": llm_resp, "action": "ask", "question": user_question}

    # Keyword matching and contextual extraction
    q_words = [w.lower() for w in re.findall(r"\b[A-Za-z]{3,}\b", user_question)]
    paragraphs = [p.strip() for p in document_text.split("\n\n") if len(p.strip()) > 30]

    matched_paragraphs = []
    for p in paragraphs:
        p_lower = p.lower()
        score = sum(1 for w in q_words if w in p_lower)
        if score > 0:
            matched_paragraphs.append((score, p))

    matched_paragraphs.sort(key=lambda x: x[0], reverse=True)

    if matched_paragraphs:
        best_context = matched_paragraphs[0][1]
        extra = matched_paragraphs[1][1] if len(matched_paragraphs) > 1 else ""
        answer_md = (
            f"### 💬 Answer to: *\"{user_question}\"*\n\n"
            f"Based on your uploaded material (`{filename}`):\n\n"
            f"**Key Explanation**:\n{best_context}\n\n"
            f"{f'**Additional Context**:\n{extra}\n\n' if extra else ''}"
            f"> 💡 *Exam Tip: Clearly highlighting these points in bullet format ensures full marks in semester assessments.*"
        )
    else:
        keywords = _extract_document_keywords(document_text, 6)
        sentences = _extract_key_sentences(document_text, 3)
        answer_md = (
            f"### 💬 Contextual Analysis: *\"{user_question}\"*\n\n"
            f"Based on `{filename}`, here is the relevant conceptual background:\n\n"
            f"• **Core Document Topics**: {', '.join(keywords)}\n"
            f"• **Related Note**: {sentences[0] if sentences else 'Please check the document sections.'}\n\n"
            f"**Explanation**: The material focuses on structuring and applying these concepts. "
            f"Ensure you practice the definitions of **{keywords[0] if keywords else 'the topic'}** and review the numerical or theoretical steps detailed in the notes."
        )

    return {"success": True, "result": answer_md, "action": "ask", "question": user_question}
