"""Question detection and marks parsing module.

Identifies question numbers, subquestions, sections, declared paper total marks,
and individual question marks using flexible regex and pattern matching.
"""

import re
from typing import List, Dict, Any, Optional, Tuple


# Regex patterns for section headers
SECTION_PATTERN = re.compile(
    r"^(?:(?:SECTION|Section|PART|Part|MODULE|Module|GROUP|Group)\s+([A-Z0-9IVX]+)|(?:---+\s*(?:SECTION|Section|PART|Part)\s+([A-Z0-9IVX]+)\s*---+))[:.\s-]*",
    re.IGNORECASE
)

# Regex patterns for declared/printed maximum marks in document header
DECLARED_TOTAL_MARKS_PATTERN = re.compile(
    r"(?:(?:Total|Max|Maximum)\s*(?:Marks|Mark)|(?:Max\.?\s*Marks?))\s*[:=–-]?\s*\[?\(?(\d{2,3})\)?\]?",
    re.IGNORECASE
)

# Regex patterns for Question start
QUESTION_START_PATTERNS = [
    # Q1. , Q1) , Q.1 , Q 1. , Question 1: , Que 1.
    re.compile(r"^(?:Q(?:ue(?:stion)?)?\.?\s*(\d+)\s*[:.)-]?\s*(?:\(([a-zA-Z0-9ivx]+)\)|([a-zA-Z])\))?)", re.IGNORECASE),
    # 1. , 1) , 1 - (at the start of a line, ensuring it's not just a date or bullet)
    re.compile(r"^(\d{1,2})\s*([.)])\s*(?:\(([a-zA-Z0-9ivx]+)\)|([a-zA-Z])\))?"),
    # (1) , (Q1)
    re.compile(r"^\((?:Q|Question)?\s*(\d+)\)\s*(?:\(([a-zA-Z0-9ivx]+)\)|([a-zA-Z])\))?", re.IGNORECASE),
]

# Regex patterns for standalone Subquestions: a) , (a) , i) , (i) , a.
SUBQUESTION_START_PATTERN = re.compile(
    r"^(?:\(([a-z0-9ivx]{1,3})\)|([a-z0-9ivx]{1,3})[.)])\s+",
    re.IGNORECASE
)

# Regex patterns to detect marks in question lines
# e.g., [10], (5 Marks), (10 marks), [5M], 10 Marks, (10)
MARKS_PATTERNS = [
    re.compile(r"\[\s*(\d{1,2})\s*(?:Marks?|marks?|M|m)?\s*\]\s*$", re.IGNORECASE),
    re.compile(r"\(\s*(\d{1,2})\s*(?:Marks?|marks?|M|m)\s*\)\s*$", re.IGNORECASE),
    re.compile(r"\(\s*(\d{1,2})\s*\)\s*$", re.IGNORECASE),
    re.compile(r"\[\s*(\d{1,2})\s*\]", re.IGNORECASE),
    re.compile(r"\b(\d{1,2})\s*(?:Marks?|marks?)\b", re.IGNORECASE),
]


def extract_declared_total_marks(text: str) -> Optional[int]:
    """Look for declared total marks in the first ~20 lines of the paper."""
    header_lines = text.split("\n")[:25]
    for line in header_lines:
        match = DECLARED_TOTAL_MARKS_PATTERN.search(line)
        if match:
            try:
                val = int(match.group(1))
                if 10 <= val <= 200:
                    return val
            except (ValueError, TypeError):
                pass
    return None


def extract_marks_from_text(line: str) -> Tuple[Optional[int], str]:
    """
    Extract marks from a question text line if present.
    Returns (marks, cleaned_text_without_marks_token).
    """
    cleaned = line.strip()
    
    for pattern in MARKS_PATTERNS:
        match = pattern.search(cleaned)
        if match:
            try:
                marks = int(match.group(1))
                # Validate reasonable mark range (1 to 50 marks per question)
                if 1 <= marks <= 50:
                    # Remove the marks token from the text
                    cleaned = pattern.sub("", cleaned).strip()
                    # Clean any dangling punctuation left at end
                    cleaned = re.sub(r"[,:–-]\s*$", "", cleaned).strip()
                    return marks, cleaned
            except (ValueError, TypeError):
                continue
                
    return None, cleaned


def parse_question_paper(raw_text: str) -> Dict[str, Any]:
    """
    Parse raw document text into structured questions and paper metadata.
    """
    if not raw_text or not raw_text.strip():
        return {
            "success": False,
            "error": "The document contains no text to parse.",
            "questions": [],
            "sections": [],
            "declared_total_marks": None,
            "total_detected_marks": 0,
            "questions_with_marks": 0,
            "questions_without_marks": 0,
            "total_questions": 0
        }

    declared_total_marks = extract_declared_total_marks(raw_text)
    
    lines = raw_text.split("\n")
    sections_found = []
    current_section = "General"
    
    questions = []
    current_q: Optional[Dict[str, Any]] = None
    current_main_q_num: Optional[str] = None
    
    for line_idx, line in enumerate(lines):
        stripped = line.strip()
        if not stripped:
            continue

        # Check for Section header
        sec_match = SECTION_PATTERN.match(stripped)
        if sec_match:
            sec_name = sec_match.group(1) or sec_match.group(2)
            current_section = f"Section {sec_name.upper()}" if sec_name else stripped
            if current_section not in sections_found:
                sections_found.append(current_section)
            continue

        # Skip document title / instruction lines (e.g. "Time: 3 Hours", "Note: Answer any 5")
        if (re.match(r"^(?:Time|Note|Instructions?|Date|Duration|Max Marks|Total Marks|Subject Code)\s*[:=]", stripped, re.IGNORECASE) or
            re.match(r"^Answer (?:any|all) (?:questions|the following)", stripped, re.IGNORECASE)):
            continue

        # Check if line starts a new main question
        main_q_detected = False
        detected_q_label = ""
        question_body = stripped

        for q_pat in QUESTION_START_PATTERNS:
            match = q_pat.match(stripped)
            if match:
                num = match.group(1)
                sub1 = match.group(2) if len(match.groups()) >= 2 else None
                sub2 = match.group(3) if len(match.groups()) >= 3 else None
                sub3 = match.group(4) if len(match.groups()) >= 4 else None
                
                sub_val = sub1 or sub2 or sub3
                # If sub1 is just punctuation like '.' or ')', disregard it as a subquestion
                if sub_val in [".", ")", ":", "-"]:
                    sub_val = None

                current_main_q_num = f"Q{num}"
                if sub_val:
                    detected_q_label = f"Q{num}({sub_val.lower()})"
                else:
                    detected_q_label = f"Q{num}"

                question_body = stripped[match.end():].strip()
                main_q_detected = True
                break

        # If not a main question, check if it is a subquestion under current main question
        sub_q_detected = False
        if not main_q_detected and current_main_q_num:
            sub_match = SUBQUESTION_START_PATTERN.match(stripped)
            if sub_match:
                sub_label = sub_match.group(1) or sub_match.group(2)
                # Ignore if it looks like a roman numeral in regular text or single digit
                detected_q_label = f"{current_main_q_num}({sub_label.lower()})"
                question_body = stripped[sub_match.end():].strip()
                sub_q_detected = True

        if main_q_detected or sub_q_detected:
            # Finalize previous question if one was in progress
            if current_q:
                # Re-check marks on accumulated text if not found on first line
                if current_q["marks"] is None:
                    found_marks, cleaned_text = extract_marks_from_text(current_q["text"])
                    if found_marks is not None:
                        current_q["marks"] = found_marks
                        current_q["text"] = cleaned_text
                current_q["text"] = current_q["text"].strip()
                if len(current_q["text"]) > 3:  # Valid question length threshold
                    questions.append(current_q)

            # Start a new question
            marks, cleaned_body = extract_marks_from_text(question_body)
            current_q = {
                "question_number": detected_q_label,
                "section": current_section,
                "text": cleaned_body,
                "marks": marks,
                "raw_text": stripped
            }
        else:
            # Continuation of existing question or preliminary text
            if current_q:
                # Check if continuation line has marks (often on the right side / end of question)
                marks_on_cont, cleaned_cont = extract_marks_from_text(stripped)
                if marks_on_cont is not None and current_q["marks"] is None:
                    current_q["marks"] = marks_on_cont
                    if cleaned_cont:
                        current_q["text"] += " " + cleaned_cont
                else:
                    current_q["text"] += " " + stripped

    # Flush the last question
    if current_q:
        if current_q["marks"] is None:
            found_marks, cleaned_text = extract_marks_from_text(current_q["text"])
            if found_marks is not None:
                current_q["marks"] = found_marks
                current_q["text"] = cleaned_text
        current_q["text"] = current_q["text"].strip()
        if len(current_q["text"]) > 3:
            questions.append(current_q)

    # Fallback: if standard regex couldn't find question numbers (e.g. unnumbered bullet points or plain paragraphs)
    if not questions and len(lines) > 0:
        candidate_paras = [p.strip() for p in raw_text.split("\n\n") if len(p.strip()) > 15]
        for idx, para in enumerate(candidate_paras, start=1):
            marks, cleaned = extract_marks_from_text(para)
            questions.append({
                "question_number": f"Item {idx}",
                "section": "General",
                "text": cleaned,
                "marks": marks,
                "raw_text": para
            })

    # Paper-level marks aggregation
    total_detected_marks = 0
    questions_with_marks = 0
    questions_without_marks = 0

    for q in questions:
        if q["marks"] is not None:
            total_detected_marks += q["marks"]
            questions_with_marks += 1
        else:
            questions_without_marks += 1

    return {
        "success": True if len(questions) > 0 else False,
        "error": None if len(questions) > 0 else "No identifiable questions found in the document.",
        "questions": questions,
        "sections": sections_found if sections_found else ["General"],
        "declared_total_marks": declared_total_marks,
        "total_detected_marks": total_detected_marks,
        "questions_with_marks": questions_with_marks,
        "questions_without_marks": questions_without_marks,
        "total_questions": len(questions)
    }
