"""NLP and rule-based question paper analysis module.

Provides question type classification, multi-signal difficulty estimation,
TF-IDF keyword extraction, unsupervised KMeans topic clustering,
and paper-level analytics & insights.
"""

import re
import numpy as np
from typing import List, Dict, Any
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans


# Rule-based action verbs and keyword patterns for Question Type
TYPE_PATTERNS = {
    "Programming": [
        r"\b(?:write\s+a\s+program|write\s+(?:python|c\+\+|c|java)?\s*code|write\s+a\s+(?:function|script)|implement|develop\s+a\s+program|code\s+for|pseudocode|algorithm\s+to|write\s+(?:an?\s+)?sql\s+query|create\s+a\s+(?:table|database|class|schema))\b"
    ],
    "Numerical": [
        r"\b(?:calculate|compute|find\s+the\s+value|evaluate\s+the\s+expression|solve\s+(?:for|the\s+equation)|determine\s+the\s+(?:cost|time|value|probability)|numerical|estimate\s+the\s+value)\b"
    ],
    "Definition": [
        r"\b(?:define|what\s+is|what\s+are|what\s+do\s+you\s+mean\s+by|state\s+the\s+definition|name\s+the|list\s+the|give\s+the\s+definition|briefly\s+define)\b"
    ],
    "Application": [
        r"\b(?:apply|design|develop|construct|formulate|case\s+study|real-world|scenario|suggest\s+a\s+solution|propose\s+a|how\s+would\s+you\s+design|architect)\b"
    ],
    "Theory/Descriptive": [
        r"\b(?:explain|describe|discuss|elaborate|compare|differentiate|distinguish\s+between|illustrate|justify|summarize|critically\s+examine|clarify)\b"
    ]
}

# Bloom's Taxonomy and difficulty indicators
DIFFICULTY_VERBS = {
    "high": [
        "analyze", "evaluate", "design", "create", "develop", "implement",
        "justify", "optimize", "synthesize", "architect", "formulate",
        "critique", "prove", "derive", "construct", "reconstruct"
    ],
    "medium": [
        "explain", "describe", "compare", "differentiate", "distinguish",
        "illustrate", "discuss", "apply", "calculate", "compute", "solve",
        "demonstrate", "interpret", "show", "categorize"
    ],
    "low": [
        "define", "list", "state", "name", "identify", "what is",
        "what are", "mention", "recall", "label", "enumerate"
    ]
}


def classify_question_type(text: str, marks: int | None = None) -> str:
    """
    Classify question type using rule-based/NLP action verb patterns and marks.
    Transparently rule-based (not fake ML).
    """
    cleaned = text.strip()
    
    # Priority check: Programming and Numerical patterns
    for pat in TYPE_PATTERNS["Programming"]:
        if re.search(pat, cleaned, re.IGNORECASE):
            return "Programming"

    for pat in TYPE_PATTERNS["Numerical"]:
        if re.search(pat, cleaned, re.IGNORECASE):
            return "Numerical"

    for pat in TYPE_PATTERNS["Definition"]:
        if re.search(pat, cleaned, re.IGNORECASE):
            return "Definition"

    for pat in TYPE_PATTERNS["Application"]:
        if re.search(pat, cleaned, re.IGNORECASE):
            return "Application"

    for pat in TYPE_PATTERNS["Theory/Descriptive"]:
        if re.search(pat, cleaned, re.IGNORECASE):
            return "Theory/Descriptive"

    # Fallback based on marks and text length
    if marks is not None and marks <= 2:
        return "Short Answer"
    elif marks is not None and marks >= 10:
        return "Long Answer"
    
    return "Theory/Descriptive"


def estimate_question_difficulty(text: str, marks: int | None, q_type: str) -> Dict[str, Any]:
    """
    Multi-signal transparent difficulty estimation.
    Signals used:
    1. Action verbs / Bloom's cognitive level
    2. Marks allocation (weightage)
    3. Type complexity (Programming / Numerical / Application)
    4. Text length and detail
    """
    text_lower = text.lower()
    score = 0
    signals = []

    # 1. Action verb analysis
    found_high = [v for v in DIFFICULTY_VERBS["high"] if re.search(rf"\b{v}\b", text_lower)]
    found_med = [v for v in DIFFICULTY_VERBS["medium"] if re.search(rf"\b{v}\b", text_lower)]
    found_low = [v for v in DIFFICULTY_VERBS["low"] if re.search(rf"\b{v}\b", text_lower)]

    if found_high:
        score += 2
        signals.append(f"High-order verbs: {', '.join(found_high[:2])}")
    elif found_med:
        score += 1
        signals.append(f"Medium-order verbs: {', '.join(found_med[:2])}")
    elif found_low:
        score += 0
        signals.append(f"Foundational verbs: {', '.join(found_low[:2])}")
    else:
        score += 1

    # 2. Marks signal
    if marks is not None:
        if marks >= 10:
            score += 2
            signals.append(f"High mark weightage ({marks}M)")
        elif marks >= 5:
            score += 1
            signals.append(f"Standard mark weightage ({marks}M)")
        elif marks <= 2:
            score -= 1
            signals.append(f"Short mark weightage ({marks}M)")

    # 3. Question type complexity
    if q_type in ["Programming", "Application"]:
        score += 1
        signals.append(f"Practical type ({q_type})")
    elif q_type == "Numerical":
        score += 1
        signals.append("Quantitative computation")
    elif q_type == "Definition":
        score -= 1
        signals.append("Direct recall question")

    # 4. Question length
    word_count = len(text.split())
    if word_count > 30:
        score += 1
        signals.append("Complex multi-part phrasing")

    # Final mapping
    if score <= 1:
        difficulty = "Easy"
    elif score <= 3:
        difficulty = "Medium"
    else:
        difficulty = "Hard"

    return {
        "difficulty": difficulty,
        "score": score,
        "signals": signals,
        "disclaimer": "Difficulty is an estimated classification based on question characteristics."
    }


def extract_keywords_and_clusters(questions: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Perform TF-IDF keyword extraction and unsupervised KMeans topic clustering.
    Uses TF-IDF vectors from genuine question documents.
    """
    if not questions:
        return {
            "top_paper_keywords": [],
            "topic_clusters": [],
            "processed_questions": []
        }

    docs = [q["text"] for q in questions]
    n_docs = len(docs)

    # Clean domain stop words
    custom_stop_words = [
        "question", "marks", "explain", "describe", "define", "what", "write",
        "answer", "following", "following:", "diagram", "diagrams", "example",
        "examples", "state", "list", "discuss", "detail", "details", "short", "note"
    ]

    try:
        tfidf = TfidfVectorizer(
            stop_words="english",
            max_df=0.95,
            min_df=1,
            ngram_range=(1, 2),
            token_pattern=r"(?u)\b[a-zA-Z_][a-zA-Z0-9_-]+\b"
        )
        tfidf_matrix = tfidf.fit_transform(docs)
        feature_names = np.array(tfidf.get_feature_names_out())
        
        # Additional custom stop word filter for top terms
        filtered_indices = [
            i for i, fn in enumerate(feature_names)
            if fn.lower() not in custom_stop_words and len(fn) > 2
        ]
        
        if not filtered_indices:
            filtered_indices = list(range(len(feature_names)))

    except Exception:
        # Fallback if TF-IDF fails on very short/unusual documents
        for q in questions:
            q["keywords"] = [w for w in re.findall(r"\b[a-zA-Z]{4,}\b", q["text"].lower()) if w not in custom_stop_words][:3]
            q["topic_group"] = "General Topic"
        return {
            "top_paper_keywords": ["Academic Exam", "Questions"],
            "topic_clusters": [{"name": "General Topic", "top_terms": ["Exam Topics"], "count": len(questions), "percentage": 100.0}],
            "processed_questions": questions
        }

    # Extract top keywords per question
    for i, q in enumerate(questions):
        row = tfidf_matrix[i].toarray().flatten()
        # Zero out custom stop words
        for idx in range(len(row)):
            if feature_names[idx].lower() in custom_stop_words or len(feature_names[idx]) <= 2:
                row[idx] = 0.0

        top_indices = row.argsort()[::-1][:4]
        q_keywords = [feature_names[idx] for idx in top_indices if row[idx] > 0]
        
        # Fallback to simple words if tf-idf score zeroed out
        if not q_keywords:
            raw_words = [w for w in re.findall(r"\b[a-zA-Z]{4,}\b", q["text"].lower()) if w not in custom_stop_words]
            q_keywords = list(dict.fromkeys(raw_words))[:3]
            
        q["keywords"] = q_keywords

    # Extract top overall paper keywords (mean TF-IDF across all documents)
    mean_scores = tfidf_matrix.toarray().mean(axis=0)
    for idx in range(len(mean_scores)):
        if feature_names[idx].lower() in custom_stop_words or len(feature_names[idx]) <= 2:
            mean_scores[idx] = 0.0

    top_paper_indices = mean_scores.argsort()[::-1][:10]
    top_paper_keywords = [
        feature_names[idx] for idx in top_paper_indices if mean_scores[idx] > 0
    ]

    # Unsupervised Topic Clustering using KMeans
    # Determine appropriate number of clusters k
    if n_docs >= 8:
        k = min(4, max(2, n_docs // 4))
    elif n_docs >= 4:
        k = 2
    else:
        k = 1

    topic_clusters = []
    if k > 1 and len(feature_names) >= k:
        try:
            kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
            cluster_labels = kmeans.fit_predict(tfidf_matrix)
            
            # Get top terms per cluster from cluster centers
            order_centroids = kmeans.cluster_centers_.argsort()[:, ::-1]
            
            for c_id in range(k):
                c_terms = []
                for ind in order_centroids[c_id]:
                    term = feature_names[ind]
                    if term.lower() not in custom_stop_words and len(term) > 2 and term not in c_terms:
                        c_terms.append(term)
                    if len(c_terms) >= 4:
                        break
                
                c_count = int(np.sum(cluster_labels == c_id))
                c_pct = round((c_count / n_docs) * 100, 1) if n_docs > 0 else 0
                topic_clusters.append({
                    "cluster_id": c_id + 1,
                    "name": f"Topic Group {c_id + 1}",
                    "top_terms": c_terms if c_terms else ["General Concepts"],
                    "count": c_count,
                    "percentage": c_pct
                })

            for i, q in enumerate(questions):
                q["topic_group"] = f"Topic Group {cluster_labels[i] + 1}"

        except Exception:
            k = 1

    if k == 1 or not topic_clusters:
        top_terms = top_paper_keywords[:4] if top_paper_keywords else ["General Concepts"]
        topic_clusters = [{
            "cluster_id": 1,
            "name": "Topic Group 1",
            "top_terms": top_terms,
            "count": n_docs,
            "percentage": 100.0
        }]
        for q in questions:
            q["topic_group"] = "Topic Group 1"

    return {
        "top_paper_keywords": top_paper_keywords,
        "topic_clusters": topic_clusters,
        "processed_questions": questions
    }


def generate_paper_insights(
    questions: List[Dict[str, Any]],
    parsed_info: Dict[str, Any],
    topic_clusters: List[Dict[str, Any]],
    diff_dist: Dict[str, int],
    type_dist: Dict[str, int]
) -> List[Dict[str, str]]:
    """Generate honest, data-grounded insights based strictly on parsed metrics."""
    insights = []
    total_q = len(questions)
    if total_q == 0:
        return insights

    # 1. Difficulty distribution insight
    easy_pct = round((diff_dist.get("Easy", 0) / total_q) * 100)
    med_pct = round((diff_dist.get("Medium", 0) / total_q) * 100)
    hard_pct = round((diff_dist.get("Hard", 0) / total_q) * 100)

    if med_pct >= 50:
        insights.append({
            "type": "info",
            "icon": "bi-speedometer2",
            "title": "Balanced Cognitive Difficulty",
            "text": f"Medium-difficulty questions comprise the largest portion ({med_pct}%) of the question paper."
        })
    elif hard_pct >= 40:
        insights.append({
            "type": "warning",
            "icon": "bi-exclamation-triangle",
            "title": "High Cognitive Demand",
            "text": f"Approximately {hard_pct}% of questions are classified as Hard, involving complex analysis, design, or high mark allocations."
        })
    elif easy_pct >= 50:
        insights.append({
            "type": "success",
            "icon": "bi-check2-circle",
            "title": "Foundational Focus",
            "text": f"Over {easy_pct}% of the paper focuses on foundational recall and definition-based questions."
        })

    # 2. Practical / Programming vs Theoretical balance
    prog_count = type_dist.get("Programming", 0)
    num_count = type_dist.get("Numerical", 0)
    app_count = type_dist.get("Application", 0)
    practical_total = prog_count + num_count + app_count
    practical_pct = round((practical_total / total_q) * 100)

    if practical_total > 0:
        insights.append({
            "type": "primary",
            "icon": "bi-code-slash",
            "title": "Practical & Applied Content",
            "text": f"Practical, coding, and application-oriented questions represent {practical_pct}% ({practical_total}/{total_q}) of the paper."
        })
    else:
        insights.append({
            "type": "secondary",
            "icon": "bi-book",
            "title": "Descriptive Theory Emphasis",
            "text": "The paper consists entirely of theoretical, descriptive, and conceptual questions."
        })

    # 3. Marks coverage insight
    detected_marks = parsed_info.get("total_detected_marks", 0)
    declared_marks = parsed_info.get("declared_total_marks")
    with_marks = parsed_info.get("questions_with_marks", 0)

    if declared_marks and detected_marks:
        if detected_marks == declared_marks:
            insights.append({
                "type": "success",
                "icon": "bi-check-all",
                "title": "Full Marks Alignment",
                "text": f"Detected question marks sum exactly to declared total marks ({detected_marks} Marks)."
            })
        else:
            insights.append({
                "type": "warning",
                "icon": "bi-patch-question",
                "title": "Marks Variance",
                "text": f"Detected question sum is {detected_marks} marks vs declared paper total of {declared_marks} marks (some subquestions or options may have separate allocations)."
            })
    elif detected_marks > 0:
        avg_m = round(detected_marks / with_marks, 1) if with_marks > 0 else 0
        insights.append({
            "type": "info",
            "icon": "bi-calculator",
            "title": "Detected Marks Summary",
            "text": f"Identified {detected_marks} total marks across {with_marks} questions (Average: {avg_m} marks per question)."
        })

    # 4. Topic clustering insight
    if topic_clusters:
        top_cluster = max(topic_clusters, key=lambda c: c.get("count", 0))
        terms_str = ", ".join(top_cluster.get("top_terms", [])[:3])
        insights.append({
            "type": "purple",
            "icon": "bi-diagram-3",
            "title": "Dominant Topic Focus",
            "text": f"{top_cluster['name']} ({terms_str}) represents the largest topic concentration with {top_cluster['count']} questions ({top_cluster['percentage']}%)."
        })

    return insights


def analyze_question_paper(parsed_info: Dict[str, Any]) -> Dict[str, Any]:
    """
    Perform full NLP and analytics pipeline on parsed questions.
    """
    questions = parsed_info.get("questions", [])
    if not questions:
        return {
            "success": False,
            "error": parsed_info.get("error", "No questions available to analyze."),
            "kpis": {},
            "charts": {},
            "topic_clusters": [],
            "top_keywords": [],
            "insights": [],
            "questions": []
        }

    # 1. Classify type and estimate difficulty for each question
    for q in questions:
        q_type = classify_question_type(q["text"], q["marks"])
        diff_info = estimate_question_difficulty(q["text"], q["marks"], q_type)
        
        q["question_type"] = q_type
        q["difficulty"] = diff_info["difficulty"]
        q["difficulty_signals"] = diff_info["signals"]

    # 2. NLP TF-IDF & Topic Clustering
    nlp_result = extract_keywords_and_clusters(questions)
    top_keywords = nlp_result["top_paper_keywords"]
    topic_clusters = nlp_result["topic_clusters"]
    processed_questions = nlp_result["processed_questions"]

    # 3. Distributions
    diff_dist = {"Easy": 0, "Medium": 0, "Hard": 0}
    type_dist = {}
    marks_ranges = {"1-2 Marks": 0, "3-5 Marks": 0, "6-10 Marks": 0, "11+ Marks": 0, "Undetected": 0}
    
    valid_marks_list = []
    for q in processed_questions:
        # Difficulty
        d = q.get("difficulty", "Medium")
        diff_dist[d] = diff_dist.get(d, 0) + 1
        
        # Type
        t = q.get("question_type", "Theory/Descriptive")
        type_dist[t] = type_dist.get(t, 0) + 1
        
        # Marks
        m = q.get("marks")
        if m is not None:
            valid_marks_list.append(m)
            if m <= 2:
                marks_ranges["1-2 Marks"] += 1
            elif m <= 5:
                marks_ranges["3-5 Marks"] += 1
            elif m <= 10:
                marks_ranges["6-10 Marks"] += 1
            else:
                marks_ranges["11+ Marks"] += 1
        else:
            marks_ranges["Undetected"] += 1

    # Remove empty marks buckets if undetected is 0
    if marks_ranges["Undetected"] == 0:
        del marks_ranges["Undetected"]

    # 4. KPIs
    total_q = len(processed_questions)
    total_marks = sum(valid_marks_list)
    avg_marks = round(total_marks / len(valid_marks_list), 1) if valid_marks_list else 0.0
    min_marks = min(valid_marks_list) if valid_marks_list else 0
    max_marks = max(valid_marks_list) if valid_marks_list else 0

    kpis = {
        "total_questions": total_q,
        "total_detected_marks": total_marks,
        "declared_total_marks": parsed_info.get("declared_total_marks"),
        "average_marks": avg_marks,
        "min_marks": min_marks,
        "max_marks": max_marks,
        "questions_with_marks": len(valid_marks_list),
        "questions_without_marks": total_q - len(valid_marks_list),
        "hard_questions_count": diff_dist.get("Hard", 0),
        "medium_questions_count": diff_dist.get("Medium", 0),
        "easy_questions_count": diff_dist.get("Easy", 0),
        "topic_groups_count": len(topic_clusters)
    }

    # 5. Charts Data
    charts = {
        "difficulty": {
            "labels": list(diff_dist.keys()),
            "data": list(diff_dist.values()),
            "colors": ["#10b981", "#f59e0b", "#ef4444"]  # Green, Amber, Red
        },
        "question_type": {
            "labels": list(type_dist.keys()),
            "data": list(type_dist.values()),
            "colors": ["#4f46e5", "#0ea5e9", "#8b5cf6", "#ec4899", "#f97316", "#14b8a6"]
        },
        "marks_distribution": {
            "labels": list(marks_ranges.keys()),
            "data": list(marks_ranges.values()),
            "colors": ["#6366f1", "#3b82f6", "#06b6d4", "#10b981", "#94a3b8"]
        },
        "topic_clusters": {
            "labels": [c["name"] for c in topic_clusters],
            "data": [c["count"] for c in topic_clusters],
            "colors": ["#818cf8", "#38bdf8", "#34d399", "#fbbf24"]
        }
    }

    # 6. Automatic Insights
    insights = generate_paper_insights(
        processed_questions,
        parsed_info,
        topic_clusters,
        diff_dist,
        type_dist
    )

    return {
        "success": True,
        "error": None,
        "kpis": kpis,
        "charts": charts,
        "topic_clusters": topic_clusters,
        "top_keywords": top_keywords,
        "insights": insights,
        "questions": processed_questions,
        "sections": parsed_info.get("sections", ["General"])
    }
