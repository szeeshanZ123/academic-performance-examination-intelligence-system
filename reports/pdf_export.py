"""Professional ReportLab PDF Generation Engine for Academic Intelligence.

Generates multi-page, selectable-text PDFs styled according to the global
blue palette with headers, footers, dynamic page numbering, and formatted tables.
"""

import io
from typing import Dict, Any, List, Optional
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    PageBreak,
    KeepTogether,
    HRFlowable
)
from reportlab.pdfgen import canvas

from reports.csv_export import sanitize_filename


# =========================================================================
# COLOR PALETTE TOKENS (Matching Global Design System)
# =========================================================================
PRIMARY = colors.HexColor("#2563EB")
PRIMARY_DARK = colors.HexColor("#1E40AF")
SECONDARY = colors.HexColor("#3B82F6")
DARK_NAVY = colors.HexColor("#0F172A")
TEXT_MUTED = colors.HexColor("#475569")
CARD_BG = colors.HexColor("#F0F8FF")
BORDER = colors.HexColor("#E2E8F0")
HEADER_BG = colors.HexColor("#DBEAFE")
SUCCESS = colors.HexColor("#16A34A")
WARNING = colors.HexColor("#F59E0B")
DANGER = colors.HexColor("#DC2626")
WHITE = colors.HexColor("#FFFFFF")
ROW_ALT = colors.HexColor("#F8FAFC")


# =========================================================================
# NUMBERED CANVAS WITH RUNNING HEADER & FOOTER
# =========================================================================
class NumberedCanvas(canvas.Canvas):
    """Two-pass canvas for dynamic 'Page X of Y' and institutional running footers."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_header_footer(num_pages)
            canvas.Canvas.showPage(self)
        canvas.Canvas.save(self)

    def draw_header_footer(self, page_count):
        self.saveState()
        self.setFont("Helvetica", 8)
        self.setFillColor(TEXT_MUTED)

        # Running Footer
        footer_text_left = "Academic Intelligence — Confidential Academic Record"
        footer_text_right = f"Page {self._pageNumber} of {page_count}"
        
        self.setStrokeColor(BORDER)
        self.setLineWidth(0.5)
        self.line(40, 35, 572, 35)

        self.drawString(40, 22, footer_text_left)
        self.drawRightString(572, 22, footer_text_right)

        # Running Top Header on pages after page 1
        if self._pageNumber > 1:
            self.drawString(40, 762, "Academic Performance & Examination Intelligence System")
            self.drawRightString(572, 762, "Official Institutional Report")
            self.line(40, 755, 572, 755)

        self.restoreState()


# =========================================================================
# HELPER FOR STYLES
# =========================================================================
def get_report_styles():
    """Build unified typographical style hierarchy."""
    base = getSampleStyleSheet()

    styles = {
        "DocTitle": ParagraphStyle(
            "DocTitle",
            parent=base["Normal"],
            fontName="Helvetica-Bold",
            fontSize=20,
            leading=24,
            textColor=DARK_NAVY,
            spaceAfter=4
        ),
        "DocSub": ParagraphStyle(
            "DocSub",
            parent=base["Normal"],
            fontName="Helvetica",
            fontSize=10,
            leading=13,
            textColor=PRIMARY,
            spaceAfter=15
        ),
        "SectionHeader": ParagraphStyle(
            "SectionHeader",
            parent=base["Normal"],
            fontName="Helvetica-Bold",
            fontSize=13,
            leading=16,
            textColor=DARK_NAVY,
            spaceBefore=12,
            spaceAfter=8
        ),
        "Normal": ParagraphStyle(
            "Normal",
            parent=base["Normal"],
            fontName="Helvetica",
            fontSize=9,
            leading=12,
            textColor=DARK_NAVY
        ),
        "NormalMuted": ParagraphStyle(
            "NormalMuted",
            parent=base["Normal"],
            fontName="Helvetica",
            fontSize=8.5,
            leading=11,
            textColor=TEXT_MUTED
        ),
        "Bold": ParagraphStyle(
            "Bold",
            parent=base["Normal"],
            fontName="Helvetica-Bold",
            fontSize=9,
            leading=12,
            textColor=DARK_NAVY
        ),
        "TableHeader": ParagraphStyle(
            "TableHeader",
            parent=base["Normal"],
            fontName="Helvetica-Bold",
            fontSize=8.5,
            leading=11,
            textColor=DARK_NAVY,
            alignment=1  # Center
        ),
        "TableCell": ParagraphStyle(
            "TableCell",
            parent=base["Normal"],
            fontName="Helvetica",
            fontSize=8.5,
            leading=11,
            textColor=DARK_NAVY,
            alignment=0  # Left
        ),
        "TableCellCenter": ParagraphStyle(
            "TableCellCenter",
            parent=base["Normal"],
            fontName="Helvetica",
            fontSize=8.5,
            leading=11,
            textColor=DARK_NAVY,
            alignment=1  # Center
        ),
        "BadgeSuccess": ParagraphStyle(
            "BadgeSuccess",
            parent=base["Normal"],
            fontName="Helvetica-Bold",
            fontSize=8,
            leading=10,
            textColor=SUCCESS,
            alignment=1
        ),
        "BadgeDanger": ParagraphStyle(
            "BadgeDanger",
            parent=base["Normal"],
            fontName="Helvetica-Bold",
            fontSize=8,
            leading=10,
            textColor=DANGER,
            alignment=1
        ),
        "BadgeWarning": ParagraphStyle(
            "BadgeWarning",
            parent=base["Normal"],
            fontName="Helvetica-Bold",
            fontSize=8,
            leading=10,
            textColor=WARNING,
            alignment=1
        )
    }
    return styles


# =========================================================================
# STUDENT PDF GENERATOR (Multi-Page Formatted Structure)
# =========================================================================
def generate_student_pdf(student_data: Dict[str, Any]) -> bytes:
    """
    Generate professional 4-page Academic Intelligence Student Report.
      Page 1: Institutional Header & Student Information & Overall Summary
      Page 2: Subject Performance Table
      Page 3: Academic History (SGPI progression & Attendance)
      Page 4: AI Insights & Personalized Improvement Plan Summary
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        leftMargin=40,
        rightMargin=40,
        topMargin=50,
        bottomMargin=50
    )
    styles = get_report_styles()
    story = []

    stud = student_data["student"]
    sem = student_data["semester"]
    summary = student_data["overall_summary"]
    roll = stud.get("Roll", "N/A")
    name = stud.get("Name", "N/A")

    # -------------------------------------------------------------
    # PAGE 1: INSTITUTIONAL HEADER & STUDENT SUMMARY
    # -------------------------------------------------------------
    # Header Banner Card
    banner_data = [
        [
            Paragraph("<font size=16 color='#2563EB'><b>ACADEMIC INTELLIGENCE</b></font><br/><font size=9 color='#475569'>Examination & Performance Analytics System</font>", styles["Normal"]),
            Paragraph(f"<font size=11 color='#0F172A'><b>STUDENT ACADEMIC REPORT</b></font><br/><font size=8.5 color='#475569'>Semester {sem} Official Assessment</font>", styles["TableCellCenter"])
        ]
    ]
    banner_table = Table(banner_data, colWidths=[330, 202])
    banner_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), CARD_BG),
        ('BOX', (0, 0), (-1, -1), 1, BORDER),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, BORDER),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ('LEFTPADDING', (0, 0), (-1, -1), 12),
        ('RIGHTPADDING', (0, 0), (-1, -1), 12),
    ]))
    story.append(banner_table)
    story.append(Spacer(1, 15))

    # Student Information Section
    story.append(Paragraph("STUDENT INFORMATION", styles["SectionHeader"]))
    info_data = [
        [
            Paragraph("<b>Full Name:</b>", styles["TableCell"]),
            Paragraph(name, styles["TableCell"]),
            Paragraph("<b>Roll Number:</b>", styles["TableCell"]),
            Paragraph(roll, styles["TableCell"])
        ],
        [
            Paragraph("<b>Current Semester:</b>", styles["TableCell"]),
            Paragraph(f"Semester {sem}", styles["TableCell"]),
            Paragraph("<b>Division:</b>", styles["TableCell"]),
            Paragraph(str(stud.get("Division", "A")), styles["TableCell"])
        ],
        [
            Paragraph("<b>Email:</b>", styles["TableCell"]),
            Paragraph(str(stud.get("Email", "N/A")), styles["TableCell"]),
            Paragraph("<b>Phone:</b>", styles["TableCell"]),
            Paragraph(str(stud.get("Phone", "N/A")), styles["TableCell"])
        ],
        [
            Paragraph("<b>Academic Status:</b>", styles["TableCell"]),
            Paragraph(str(stud.get("Status", "Active")), styles["BadgeSuccess"]),
            Paragraph("<b>Gender:</b>", styles["TableCell"]),
            Paragraph(str(stud.get("Gender", "N/A")), styles["TableCell"])
        ]
    ]
    info_table = Table(info_data, colWidths=[110, 156, 110, 156])
    info_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), WHITE),
        ('BOX', (0, 0), (-1, -1), 1, BORDER),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, BORDER),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(info_table)
    story.append(Spacer(1, 15))

    # Overall Summary KPI Cards
    story.append(Paragraph("OVERALL ACADEMIC SUMMARY", styles["SectionHeader"]))
    
    perf_color = SUCCESS if summary["sgpi"] >= 7.5 else (WARNING if summary["sgpi"] >= 6.0 else DANGER)
    att_color = SUCCESS if summary["attendance"] >= 75.0 else DANGER
    risk_color = SUCCESS if summary["academic_risk"] == "Low" else (WARNING if summary["academic_risk"] == "Medium" else DANGER)

    kpi_card_data = [
        [
            Paragraph(f"<font size=16 color='{perf_color.hexval()}'><b>{summary['sgpi']}</b></font><br/><font size=8 color='#475569'>Current SGPI</font>", styles["TableCellCenter"]),
            Paragraph(f"<font size=16 color='{att_color.hexval()}'><b>{summary['attendance']}%</b></font><br/><font size=8 color='#475569'>Overall Attendance</font>", styles["TableCellCenter"]),
            Paragraph(f"<font size=16 color='#2563EB'><b>{summary['average_marks']}</b></font><br/><font size=8 color='#475569'>Average Marks / 100</font>", styles["TableCellCenter"]),
            Paragraph(f"<font size=16 color='{risk_color.hexval()}'><b>{summary['academic_risk']}</b></font><br/><font size=8 color='#475569'>Academic Risk Level</font>", styles["TableCellCenter"])
        ]
    ]
    kpi_card_table = Table(kpi_card_data, colWidths=[133, 133, 133, 133])
    kpi_card_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), CARD_BG),
        ('BOX', (0, 0), (-1, -1), 1, BORDER),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, BORDER),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 12),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
    ]))
    story.append(kpi_card_table)
    story.append(Spacer(1, 15))

    # Assessment Commentary Box
    story.append(Paragraph("PERFORMANCE EVALUATION OVERVIEW", styles["SectionHeader"]))
    commentary = (
        f"Student <b>{name}</b> ({roll}) is currently enrolled in Semester {sem}. "
        f"Overall academic performance is evaluated as <b>{summary['overall_performance']}</b> with a cumulative SGPI of <b>{summary['sgpi']}</b>. "
        f"Attendance is recorded at <b>{summary['attendance']}%</b> ({summary['attendance_status']}). "
    )
    if summary['attendance'] < 75:
        commentary += "<b>Notice:</b> Attendance is below the mandatory 75% institutional threshold and requires immediate attention."
    else:
        commentary += "Attendance satisfies the mandatory institutional eligibility criteria."

    comm_table = Table([[Paragraph(commentary, styles["Normal"])]], colWidths=[532])
    comm_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), ROW_ALT),
        ('BOX', (0, 0), (-1, -1), 1, BORDER),
        ('TOPPADDING', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ('LEFTPADDING', (0, 0), (-1, -1), 12),
        ('RIGHTPADDING', (0, 0), (-1, -1), 12),
    ]))
    story.append(comm_table)

    # -------------------------------------------------------------
    # PAGE 2: SUBJECT PERFORMANCE TABLE
    # -------------------------------------------------------------
    story.append(PageBreak())
    story.append(Paragraph("SEMESTER SUBJECT PERFORMANCE", styles["SectionHeader"]))
    story.append(Paragraph(f"Detailed course evaluation marks and attendance for Semester {sem}.", styles["DocSub"]))

    subj_headers = ["Course Subject", "Internal\n(30)", "External\n(70)", "Total\n(100)", "Pct", "Grade", "Attendance", "Status"]
    subj_rows = [[Paragraph(f"<b>{h}</b>", styles["TableHeader"]) for h in subj_headers]]

    for s in student_data.get("academic_performance", []):
        tot = s["total"]
        att = s["attendance"]
        status_text = "Passed" if tot >= 40 else "Backlog"
        status_style = styles["BadgeSuccess"] if tot >= 40 else styles["BadgeDanger"]

        subj_rows.append([
            Paragraph(s["subject"], styles["TableCell"]),
            Paragraph(str(s["internal"]), styles["TableCellCenter"]),
            Paragraph(str(s["external"]), styles["TableCellCenter"]),
            Paragraph(f"<b>{tot}</b>", styles["TableCellCenter"]),
            Paragraph(s["percentage"], styles["TableCellCenter"]),
            Paragraph(f"<b>{s['grade']}</b>", styles["TableCellCenter"]),
            Paragraph(f"{att}%", styles["TableCellCenter"]),
            Paragraph(status_text, status_style)
        ])

    subj_table = Table(subj_rows, colWidths=[152, 50, 50, 50, 45, 45, 70, 70])
    subj_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), HEADER_BG),
        ('BOX', (0, 0), (-1, -1), 1, BORDER),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, BORDER),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 7),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 7),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(subj_table)
    story.append(Spacer(1, 20))

    # Grading Schema Legend
    story.append(Paragraph("GRADING REFERENCE SCALE", styles["SectionHeader"]))
    scale_data = [
        ["Grade", "O", "A+", "A", "B+", "B", "C", "P", "F"],
        ["Marks Range", ">=90", "80-89", "70-79", "60-69", "55-59", "50-54", "40-49", "<40"],
        ["Performance", "Outstanding", "Excellent", "Very Good", "Good", "Fair", "Average", "Pass", "Fail"]
    ]
    scale_table = Table([[Paragraph(c, styles["TableCellCenter"]) for c in row] for row in scale_data], colWidths=[92] + [55]*8)
    scale_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), CARD_BG),
        ('BOX', (0, 0), (-1, -1), 1, BORDER),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, BORDER),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(scale_table)

    # -------------------------------------------------------------
    # PAGE 3: ACADEMIC HISTORY & SGPI PROGRESSION
    # -------------------------------------------------------------
    story.append(PageBreak())
    story.append(Paragraph("ACADEMIC PROGRESSION & HISTORICAL PERFORMANCE", styles["SectionHeader"]))
    story.append(Paragraph("Historical progression across verified semesters.", styles["DocSub"]))

    history = student_data.get("academic_history", {})
    trend_data = history.get("trend_data", [])

    if trend_data:
        hist_headers = ["Academic Term", "Average Total", "Internal Avg", "External Avg", "Attendance", "Term SGPI", "Progression"]
        hist_rows = [[Paragraph(f"<b>{h}</b>", styles["TableHeader"]) for h in hist_headers]]

        prev_sgpi = None
        for h in trend_data:
            curr_sgpi = h["sgpi"]
            if prev_sgpi is None:
                prog = "Baseline"
                prog_style = styles["TableCellCenter"]
            elif curr_sgpi > prev_sgpi:
                prog = f"+{round(curr_sgpi - prev_sgpi, 2)} Up"
                prog_style = styles["BadgeSuccess"]
            elif curr_sgpi < prev_sgpi:
                prog = f"{round(curr_sgpi - prev_sgpi, 2)} Down"
                prog_style = styles["BadgeDanger"]
            else:
                prog = "Stable"
                prog_style = styles["TableCellCenter"]
            prev_sgpi = curr_sgpi

            hist_rows.append([
                Paragraph(f"Semester {h['semester']}", styles["TableCell"]),
                Paragraph(str(h["average_total"]), styles["TableCellCenter"]),
                Paragraph(str(h["average_internal"]), styles["TableCellCenter"]),
                Paragraph(str(h["average_external"]), styles["TableCellCenter"]),
                Paragraph(f"{h['average_attendance']}%", styles["TableCellCenter"]),
                Paragraph(f"<b>{curr_sgpi}</b>", styles["TableCellCenter"]),
                Paragraph(prog, prog_style)
            ])

        hist_table = Table(hist_rows, colWidths=[90, 75, 75, 75, 75, 70, 72])
        hist_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), HEADER_BG),
            ('BOX', (0, 0), (-1, -1), 1, BORDER),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, BORDER),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        story.append(hist_table)
    else:
        story.append(Paragraph("<i>Historical progression records will appear after multi-term data completion.</i>", styles["NormalMuted"]))

    story.append(Spacer(1, 20))

    # Historical Summary KPI box
    hist_summary = history.get("summary", {})
    if hist_summary:
        story.append(Paragraph("CUMULATIVE TRAJECTORY METRICS", styles["SectionHeader"]))
        h_kpis = [
            [
                Paragraph(f"<font size=14 color='#2563EB'><b>{hist_summary.get('highest_sgpi', 0)}</b></font><br/><font size=8 color='#475569'>Highest SGPI Achieved</font>", styles["TableCellCenter"]),
                Paragraph(f"<font size=14 color='#2563EB'><b>{hist_summary.get('average_sgpi', 0)}</b></font><br/><font size=8 color='#475569'>Cumulative SGPI Average</font>", styles["TableCellCenter"]),
                Paragraph(f"<font size=14 color='#2563EB'><b>{hist_summary.get('overall_average_attendance', 0)}%</b></font><br/><font size=8 color='#475569'>Cumulative Attendance</font>", styles["TableCellCenter"]),
                Paragraph(f"<font size=14 color='#2563EB'><b>{hist_summary.get('total_semesters', 1)}</b></font><br/><font size=8 color='#475569'>Terms Recorded</font>", styles["TableCellCenter"]),
            ]
        ]
        h_table = Table(h_kpis, colWidths=[133, 133, 133, 133])
        h_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), CARD_BG),
            ('BOX', (0, 0), (-1, -1), 1, BORDER),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, BORDER),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ]))
        story.append(h_table)

    # -------------------------------------------------------------
    # PAGE 4: AI INSIGHTS & PERSONALIZED IMPROVEMENT PLAN
    # -------------------------------------------------------------
    story.append(PageBreak())
    story.append(Paragraph("AI PERFORMANCE OUTLOOK & STRATEGIC RECOMMENDATIONS", styles["SectionHeader"]))
    story.append(Paragraph("Machine Learning projections and targeted academic coaching roadmap.", styles["DocSub"]))

    # ML Predictions Section
    ai_outlook = student_data.get("ai_outlook", {})
    preds = ai_outlook.get("predictions", [])
    if preds:
        story.append(Paragraph("EXTERNAL EXAMINATION OUTLOOK", styles["Bold"]))
        pred_headers = ["Subject", "Predicted External (70)", "Projected Total (100)", "Performance Outlook"]
        pred_rows = [[Paragraph(f"<b>{h}</b>", styles["TableHeader"]) for h in pred_headers]]

        for p in preds:
            ext_val = p.get("predicted_external", "N/A")
            tot_val = p.get("predicted_total", "N/A")
            lbl = p.get("classification", {}).get("label", "Satisfactory")
            lbl_color = SUCCESS if "High" in lbl or "Distinction" in lbl else (WARNING if "Average" in lbl else DANGER)
            
            pred_rows.append([
                Paragraph(p.get("subject", ""), styles["TableCell"]),
                Paragraph(f"<b>{ext_val} / 70</b>", styles["TableCellCenter"]),
                Paragraph(f"<b>{tot_val} / 100</b>", styles["TableCellCenter"]),
                Paragraph(f"<font color='{lbl_color.hexval()}'><b>{lbl}</b></font>", styles["TableCellCenter"])
            ])

        pred_table = Table(pred_rows, colWidths=[180, 110, 110, 132])
        pred_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), HEADER_BG),
            ('BOX', (0, 0), (-1, -1), 1, BORDER),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, BORDER),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        story.append(pred_table)
        story.append(Spacer(1, 15))

    # Improvement Plan Summary (Phase 8.4)
    plan = student_data.get("improvement_plan")
    if plan:
        story.append(Paragraph("PERSONALIZED IMPROVEMENT ROADMAP", styles["Bold"]))

        # Weak subjects & Priority Topics
        weak_subjs = [w["subject"] for w in plan.get("weak_subjects", [])]
        weak_str = ", ".join(weak_subjs) if weak_subjs else "None identified (All subjects performing stably)"
        
        topics_str = ""
        if plan.get("learning_topics"):
            t_names = [f"• {t['topic']} ({t.get('priority', 'High')})" for t in plan.get("learning_topics")[:3]]
            topics_str = "<br/>".join(t_names)
        else:
            topics_str = "Standard core curriculum review"

        rec_actions = ""
        if plan.get("action_checklist"):
            a_items = [f"• {a['text']}" for a in plan.get("action_checklist")[:3]]
            rec_actions = "<br/>".join(a_items)
        else:
            rec_actions = "• Maintain consistent study schedule<br/>• Practice previous semester examination papers"

        plan_data = [
            [Paragraph("<b>Weak Subject Focus:</b>", styles["TableCell"]), Paragraph(weak_str, styles["TableCell"])],
            [Paragraph("<b>Priority Learning Topics:</b>", styles["TableCell"]), Paragraph(topics_str, styles["TableCell"])],
            [Paragraph("<b>Key Recommended Actions:</b>", styles["TableCell"]), Paragraph(rec_actions, styles["TableCell"])]
        ]
        plan_table = Table(plan_data, colWidths=[150, 382])
        plan_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), WHITE),
            ('BOX', (0, 0), (-1, -1), 1, BORDER),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, BORDER),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('TOPPADDING', (0, 0), (-1, -1), 7),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 7),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ]))
        story.append(plan_table)
    else:
        story.append(Paragraph("<i>Comprehensive improvement plan details are available in the Student Portal.</i>", styles["NormalMuted"]))

    # Build Document
    doc.build(story, canvasmaker=NumberedCanvas)
    return buffer.getvalue()


# =========================================================================
# TEACHER PDF GENERATOR
# =========================================================================
def generate_teacher_pdf(
    report_data: Dict[str, Any],
    report_type: str = "subject",
    student_roll: Optional[str] = None
) -> bytes:
    """Generate professional PDF report for Teacher scope."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        leftMargin=40,
        rightMargin=40,
        topMargin=50,
        bottomMargin=50
    )
    styles = get_report_styles()
    story = []

    teacher = report_data.get("teacher", {})
    t_name = teacher.get("Teacher_Name", "Faculty Member")
    t_id = teacher.get("Teacher_ID", "")
    subj = report_data.get("selected_subject", "")
    sem = report_data.get("selected_semester", "")
    kpis = report_data.get("kpis", {})

    # Title & Header
    story.append(Paragraph("ACADEMIC INTELLIGENCE — FACULTY REPORT", styles["DocTitle"]))
    story.append(Paragraph(f"Faculty: <b>{t_name}</b> ({t_id}) | Subject: <b>{subj}</b> (Semester {sem})", styles["DocSub"]))

    # Class KPIs
    kpi_rows = [
        [
            Paragraph(f"<font size=14 color='#2563EB'><b>{kpis.get('total_students', 0)}</b></font><br/><font size=8 color='#475569'>Enrolled Students</font>", styles["TableCellCenter"]),
            Paragraph(f"<font size=14 color='#2563EB'><b>{kpis.get('average_marks', 0)}</b></font><br/><font size=8 color='#475569'>Class Average Marks</font>", styles["TableCellCenter"]),
            Paragraph(f"<font size=14 color='#16A34A'><b>{kpis.get('highest_marks', 0)}</b></font><br/><font size=8 color='#475569'>Highest Marks</font>", styles["TableCellCenter"]),
            Paragraph(f"<font size=14 color='#DC2626'><b>{kpis.get('lowest_marks', 0)}</b></font><br/><font size=8 color='#475569'>Lowest Marks</font>", styles["TableCellCenter"]),
            Paragraph(f"<font size=14 color='#2563EB'><b>{kpis.get('average_attendance', 0)}%</b></font><br/><font size=8 color='#475569'>Attendance Average</font>", styles["TableCellCenter"])
        ]
    ]
    kpi_table = Table(kpi_rows, colWidths=[106, 106, 106, 106, 108])
    kpi_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), CARD_BG),
        ('BOX', (0, 0), (-1, -1), 1, BORDER),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, BORDER),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(kpi_table)
    story.append(Spacer(1, 15))

    # If single student drill-down requested
    if report_type == "student" and student_roll and report_data.get("selected_student_detail"):
        detail = report_data["selected_student_detail"]
        stud = detail["student"]
        story.append(Paragraph(f"STUDENT DRILL-DOWN: {stud.get('Name')} ({student_roll})", styles["SectionHeader"]))
        
        stud_headers = ["Course Subject", "Internal (30)", "External (70)", "Total (100)", "Grade", "Attendance"]
        stud_rows = [[Paragraph(f"<b>{h}</b>", styles["TableHeader"]) for h in stud_headers]]
        for s in detail["subjects_list"]:
            stud_rows.append([
                Paragraph(s["subject"], styles["TableCell"]),
                Paragraph(str(s["internal"]), styles["TableCellCenter"]),
                Paragraph(str(s["external"]), styles["TableCellCenter"]),
                Paragraph(f"<b>{s['total']}</b>", styles["TableCellCenter"]),
                Paragraph(s["grade"], styles["TableCellCenter"]),
                Paragraph(f"{s['attendance']}%", styles["TableCellCenter"])
            ])
        s_table = Table(stud_rows, colWidths=[172, 70, 70, 70, 70, 80])
        s_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), HEADER_BG),
            ('BOX', (0, 0), (-1, -1), 1, BORDER),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, BORDER),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        story.append(s_table)
        doc.build(story, canvasmaker=NumberedCanvas)
        return buffer.getvalue()

    # Student Performance Table
    story.append(Paragraph("CLASS PERFORMANCE ROSTER", styles["SectionHeader"]))
    records = report_data.get("students", [])

    table_headers = ["Roll No", "Student Name", "Internal", "External", "Total", "Grade", "Attendance", "Status"]
    table_rows = [[Paragraph(f"<b>{h}</b>", styles["TableHeader"]) for h in table_headers]]

    for r in records:
        status_style = styles["BadgeSuccess"] if r["status"] == "Honors" else (styles["BadgeDanger"] if r["status"] == "At Risk" else styles["TableCellCenter"])
        table_rows.append([
            Paragraph(r["Roll"], styles["TableCell"]),
            Paragraph(r["Name"], styles["TableCell"]),
            Paragraph(str(r["Internal"]), styles["TableCellCenter"]),
            Paragraph(str(r["External"]), styles["TableCellCenter"]),
            Paragraph(f"<b>{r['Total']}</b>", styles["TableCellCenter"]),
            Paragraph(r["Grade"], styles["TableCellCenter"]),
            Paragraph(f"{r['Attendance']}%", styles["TableCellCenter"]),
            Paragraph(r["status"], status_style)
        ])

    roster_table = Table(table_rows, colWidths=[65, 147, 50, 50, 50, 45, 65, 60], repeatRows=1)
    roster_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), HEADER_BG),
        ('BOX', (0, 0), (-1, -1), 1, BORDER),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, BORDER),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
    ]))
    story.append(roster_table)

    # At-Risk Students Subsection
    at_risk = report_data.get("at_risk_students", [])
    if at_risk:
        story.append(Spacer(1, 15))
        story.append(Paragraph("AT-RISK STUDENTS REQUIRING ATTENTION", styles["SectionHeader"]))
        risk_headers = ["Roll No", "Student Name", "Total / 100", "Attendance", "Identified Concern"]
        risk_rows = [[Paragraph(f"<b>{h}</b>", styles["TableHeader"]) for h in risk_headers]]
        for ar in at_risk:
            risk_rows.append([
                Paragraph(ar["Roll"], styles["TableCell"]),
                Paragraph(ar["Name"], styles["TableCell"]),
                Paragraph(str(ar["Total"]), styles["TableCellCenter"]),
                Paragraph(f"{ar['Attendance']}%", styles["TableCellCenter"]),
                Paragraph(ar["risk_reason"], styles["BadgeDanger"])
            ])
        risk_table = Table(risk_rows, colWidths=[70, 162, 70, 70, 160])
        risk_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), HEADER_BG),
            ('BOX', (0, 0), (-1, -1), 1, BORDER),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, BORDER),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ]))
        story.append(risk_table)

    doc.build(story, canvasmaker=NumberedCanvas)
    return buffer.getvalue()


# =========================================================================
# ADMIN PDF GENERATOR
# =========================================================================
def generate_admin_pdf(report_data: Dict[str, Any], report_type: str = "overall") -> bytes:
    """Generate comprehensive institutional PDF for Administrator."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        leftMargin=40,
        rightMargin=40,
        topMargin=50,
        bottomMargin=50
    )
    styles = get_report_styles()
    story = []

    admin = report_data.get("admin", {})
    admin_name = admin.get("Teacher_Name", "Administrator")
    filters = report_data.get("filters", {})
    sem = filters.get("semester", "All Semesters")
    sem_label = f"Semester {sem}" if str(sem).isdigit() else "All Semesters"

    # Title
    story.append(Paragraph("INSTITUTIONAL ACADEMIC REPORT", styles["DocTitle"]))
    story.append(Paragraph(f"Generated by: <b>{admin_name}</b> | Filter Scope: <b>{sem_label}</b>", styles["DocSub"]))

    # Institutional Executive KPIs
    kpis = report_data.get("kpis", {})
    kpi_rows = [
        [
            Paragraph(f"<font size=14 color='#2563EB'><b>{kpis.get('total_students', 0)}</b></font><br/><font size=8 color='#475569'>Total Students</font>", styles["TableCellCenter"]),
            Paragraph(f"<font size=14 color='#2563EB'><b>{kpis.get('average_performance', 0)}%</b></font><br/><font size=8 color='#475569'>Average Performance</font>", styles["TableCellCenter"]),
            Paragraph(f"<font size=14 color='#2563EB'><b>{kpis.get('average_attendance', 0)}%</b></font><br/><font size=8 color='#475569'>Average Attendance</font>", styles["TableCellCenter"]),
            Paragraph(f"<font size=14 color='#2563EB'><b>{kpis.get('average_sgpi', 0)}</b></font><br/><font size=8 color='#475569'>Average SGPI</font>", styles["TableCellCenter"]),
            Paragraph(f"<font size=14 color='#16A34A'><b>{kpis.get('top_performers', 0)}</b></font><br/><font size=8 color='#475569'>Top Performers</font>", styles["TableCellCenter"]),
            Paragraph(f"<font size=14 color='#DC2626'><b>{kpis.get('at_risk_count', 0)}</b></font><br/><font size=8 color='#475569'>At-Risk Students</font>", styles["TableCellCenter"])
        ]
    ]
    kpi_table = Table(kpi_rows, colWidths=[88, 88, 88, 88, 90, 90])
    kpi_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), CARD_BG),
        ('BOX', (0, 0), (-1, -1), 1, BORDER),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, BORDER),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(kpi_table)
    story.append(Spacer(1, 15))

    # Depending on report_type, render the focal table
    if report_type == "at_risk":
        story.append(Paragraph("AT-RISK STUDENTS REPORT", styles["SectionHeader"]))
        records = report_data.get("at_risk_records", [])
        headers = ["Roll No", "Student Name", "Semester", "Attendance", "SGPI", "Primary Concern", "Priority"]
        rows = [[Paragraph(f"<b>{h}</b>", styles["TableHeader"]) for h in headers]]
        for r in records:
            p_style = styles["BadgeDanger"] if r["priority"] == "High" else styles["BadgeWarning"]
            rows.append([
                Paragraph(r["roll"], styles["TableCell"]),
                Paragraph(r["name"], styles["TableCell"]),
                Paragraph(f"Sem {r['semester']}", styles["TableCellCenter"]),
                Paragraph(f"{r['attendance']}%", styles["TableCellCenter"]),
                Paragraph(str(r["sgpi"]), styles["TableCellCenter"]),
                Paragraph(r["risk_reason"], styles["TableCell"]),
                Paragraph(r["priority"], p_style)
            ])
        t = Table(rows, colWidths=[65, 127, 55, 65, 50, 110, 60], repeatRows=1)

    elif report_type == "attendance":
        story.append(Paragraph("ATTENDANCE COMPLIANCE REPORT", styles["SectionHeader"]))
        records = report_data.get("attendance_records", [])
        headers = ["Roll No", "Student Name", "Sem", "Subject", "Attendance", "Status"]
        rows = [[Paragraph(f"<b>{h}</b>", styles["TableHeader"]) for h in headers]]
        for r in records[:200]:  # Cap to first 200 to prevent PDF bloat
            st_style = styles["BadgeSuccess"] if r["status"] == "Good" else styles["BadgeDanger"]
            rows.append([
                Paragraph(r["roll"], styles["TableCell"]),
                Paragraph(r["name"], styles["TableCell"]),
                Paragraph(str(r["semester"]), styles["TableCellCenter"]),
                Paragraph(r["subject"], styles["TableCell"]),
                Paragraph(f"{r['attendance']}%", styles["TableCellCenter"]),
                Paragraph(r["status"], st_style)
            ])
        t = Table(rows, colWidths=[65, 147, 35, 160, 65, 60], repeatRows=1)

    elif report_type == "semester":
        story.append(Paragraph("SEMESTER PERFORMANCE SUMMARY", styles["SectionHeader"]))
        records = report_data.get("semester_summary", [])
        headers = ["Semester", "Students", "Average Marks", "Average Attendance", "Average SGPI", "Pass Rate"]
        rows = [[Paragraph(f"<b>{h}</b>", styles["TableHeader"]) for h in headers]]
        for r in records:
            rows.append([
                Paragraph(f"Semester {r['semester']}", styles["TableCell"]),
                Paragraph(str(r["total_students"]), styles["TableCellCenter"]),
                Paragraph(f"{r['average_marks']}%", styles["TableCellCenter"]),
                Paragraph(f"{r['average_attendance']}%", styles["TableCellCenter"]),
                Paragraph(f"<b>{r['average_sgpi']}</b>", styles["TableCellCenter"]),
                Paragraph(f"{r['pass_rate']}%", styles["TableCellCenter"])
            ])
        t = Table(rows, colWidths=[92, 80, 90, 90, 90, 90])

    elif report_type == "subject":
        story.append(Paragraph("SUBJECT PERFORMANCE SUMMARY", styles["SectionHeader"]))
        records = report_data.get("subject_summary", [])
        headers = ["Sem", "Subject", "Students", "Avg Internal", "Avg External", "Avg Total", "High", "Low", "Attendance"]
        rows = [[Paragraph(f"<b>{h}</b>", styles["TableHeader"]) for h in headers]]
        for r in records:
            rows.append([
                Paragraph(str(r["semester"]), styles["TableCellCenter"]),
                Paragraph(r["subject"], styles["TableCell"]),
                Paragraph(str(r["students_count"]), styles["TableCellCenter"]),
                Paragraph(str(r["average_internal"]), styles["TableCellCenter"]),
                Paragraph(str(r["average_external"]), styles["TableCellCenter"]),
                Paragraph(f"<b>{r['average_total']}</b>", styles["TableCellCenter"]),
                Paragraph(str(r["highest_marks"]), styles["TableCellCenter"]),
                Paragraph(str(r["lowest_marks"]), styles["TableCellCenter"]),
                Paragraph(f"{r['attendance_average']}%", styles["TableCellCenter"])
            ])
        t = Table(rows, colWidths=[35, 157, 50, 50, 50, 50, 45, 45, 50], repeatRows=1)

    else:  # 'performance' or 'overall'
        story.append(Paragraph("STUDENT PERFORMANCE ROSTER", styles["SectionHeader"]))
        records = report_data.get("performance_records", [])
        headers = ["Roll No", "Student Name", "Sem", "Subject", "Internal", "External", "Total", "Grade", "Att", "SGPI"]
        rows = [[Paragraph(f"<b>{h}</b>", styles["TableHeader"]) for h in headers]]
        for r in records[:200]:
            rows.append([
                Paragraph(r["roll"], styles["TableCell"]),
                Paragraph(r["name"], styles["TableCell"]),
                Paragraph(str(r["semester"]), styles["TableCellCenter"]),
                Paragraph(r["subject"], styles["TableCell"]),
                Paragraph(str(r["internal"]), styles["TableCellCenter"]),
                Paragraph(str(r["external"]), styles["TableCellCenter"]),
                Paragraph(f"<b>{r['total']}</b>", styles["TableCellCenter"]),
                Paragraph(r["grade"], styles["TableCellCenter"]),
                Paragraph(f"{r['attendance']}%", styles["TableCellCenter"]),
                Paragraph(f"<b>{r['sgpi']}</b>", styles["TableCellCenter"])
            ])
        t = Table(rows, colWidths=[60, 117, 30, 135, 40, 40, 40, 30, 30, 40], repeatRows=1)

    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), HEADER_BG),
        ('BOX', (0, 0), (-1, -1), 1, BORDER),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, BORDER),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LEFTPADDING', (0, 0), (-1, -1), 4),
        ('RIGHTPADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(t)

    doc.build(story, canvasmaker=NumberedCanvas)
    return buffer.getvalue()
