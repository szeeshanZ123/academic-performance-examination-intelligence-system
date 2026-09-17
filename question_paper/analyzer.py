"""NLP, syllabus mapping, and rule-based question paper analysis module.

Provides question type classification, Bloom's Taxonomy mapping,
subject syllabus topic classification with 'Other / Unclassified' fallback,
multi-signal difficulty estimation, TF-IDF keyword extraction,
and data-grounded academic insights.
"""

import re
from typing import List, Dict, Any, Optional
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans


# ----------------------------------------------------------------------
# 1. Subject-Wise Syllabus Topic Registry
# ----------------------------------------------------------------------
SUBJECT_SYLLABUS_TOPICS = {
    "Python for Data Analytics": {
        "NumPy": [
            "numpy", "ndarray", "matrix", "broadcasting", "determinant", "inverse",
            "indexing", "slicing", "vector", "dimension", "identity matrix", "shape",
            "reshape", "dot product", "eigenvalues"
        ],
        "Pandas": [
            "pandas", "series", "dataframe", "groupby", "pivot_table", "csv",
            "dataset", "imputation", "missing values", "forward fill", "read_csv",
            "aggregation", "data grouping", "fillna", "dropna", "merge", "concat"
        ],
        "Data Cleaning": [
            "data cleaning", "clean", "irregular string", "datetime", "iso datetime",
            "time-series", "outlier", "outlier detection", "iqr", "interquartile",
            "scaling", "feature scaling", "normalization", "min-max", "z-score",
            "standardization", "scikit-learn", "data preparation", "missing value"
        ],
        "Data Visualization": [
            "visualization", "matplotlib", "seaborn", "plot", "histogram",
            "boxplot", "heatmap", "correlation heatmap", "chart", "scatter",
            "figure", "axes", "line plot", "bar plot", "visualizing"
        ],
        "Statistics": [
            "statistics", "statistical", "correlation", "pearson", "spearman",
            "rank correlation", "mean", "median", "mode", "variance",
            "standard deviation", "distribution", "hypothesis", "probability", "p-value"
        ],
        "EDA": [
            "eda", "exploratory data analysis", "confirmatory", "confirmatory data analysis",
            "data profiling", "feature analysis", "bivariate", "multivariate",
            "data exploration", "univariate"
        ],
        "Python Basics": [
            "python", "data types", "list", "tuple", "dictionary", "set",
            "lambda", "function", "generator", "decorator", "comprehension", "string"
        ]
    },
    "Database Management Systems": {
        "ER Modeling & Relational Model": [
            "er model", "entity-relationship", "er diagram", "primary key",
            "foreign key", "candidate key", "super key", "schema", "architecture",
            "three-schema", "data independence", "file processing", "attribute", "relationship"
        ],
        "SQL & Relational Algebra": [
            "sql", "relational algebra", "selection", "projection", "cartesian product",
            "natural join", "inner join", "outer join", "query", "create table",
            "insert", "update", "delete", "subquery", "group by", "having"
        ],
        "Normalization": [
            "normalization", "1nf", "2nf", "3nf", "bcnf", "functional dependency",
            "normal form", "decomposition", "lossless", "dependency preserving", "multivalued"
        ],
        "Transaction Processing & Concurrency": [
            "transaction", "acid", "concurrency", "concurrency control", "2pl",
            "two-phase locking", "serializability", "deadlock", "commit", "rollback",
            "banking", "timestamp", "recovery"
        ],
        "Storage & Indexing": [
            "indexing", "b-tree", "b+ tree", "hashing", "file organization",
            "raid", "storage", "cluster", "secondary index"
        ]
    },
    "Python Programming": {
        "Python Basics & Syntax": [
            "python", "features", "advantages", "c++", "interpreter", "syntax",
            "variables", "keywords", "operators", "input", "output", "comments"
        ],
        "Control Flow & Functions": [
            "conditional", "if-elif-else", "loop", "for", "while", "function",
            "recursion", "factorial", "palindrome", "scope", "arguments", "parameters"
        ],
        "Data Structures": [
            "list", "tuple", "dictionary", "set", "mutable", "immutable",
            "indexing", "slicing", "methods", "comprehension", "string", "collections"
        ],
        "Object-Oriented Programming": [
            "oop", "class", "object", "inheritance", "polymorphism",
            "encapsulation", "bankaccount", "methods", "constructor", "init", "abstraction"
        ],
        "File Handling & Exceptions": [
            "exception", "exception handling", "try", "except", "finally",
            "file", "csv module", "reading and writing", "text file", "word count", "with open"
        ]
    },
    "Operating Systems": {
        "Process Management & Scheduling": [
            "process", "cpu scheduling", "fcfs", "round robin", "sjf", "priority scheduling",
            "process states", "pcb", "context switch", "waiting time", "turnaround", "dispatcher"
        ],
        "Threads & Concurrency": [
            "threads", "multithreading", "race condition", "critical section",
            "mutex", "semaphore", "synchronization", "fork", "system call", "inter-process"
        ],
        "Deadlocks": [
            "deadlock", "banker's algorithm", "deadlock prevention", "avoidance",
            "detection", "resource allocation graph", "safe state", "circular wait"
        ],
        "Memory Management & Virtual Memory": [
            "memory management", "paging", "segmentation", "virtual memory",
            "page replacement", "fifo", "lru", "thrashing", "tlb", "demand paging"
        ],
        "File Systems & I/O": [
            "file system", "directory structure", "disk scheduling", "i/o management",
            "sstf", "scan", "c-scan", "allocation methods", "inode"
        ]
    },
    "Data Structures": {
        "Arrays & Linked Lists": [
            "array", "linked list", "singly", "doubly", "circular", "node",
            "traversal", "insertion", "deletion", "pointer"
        ],
        "Stacks & Queues": [
            "stack", "queue", "push", "pop", "enqueue", "dequeue", "circular queue",
            "postfix", "prefix", "expression evaluation", "infix"
        ],
        "Trees & BST": [
            "tree", "binary tree", "binary search tree", "bst", "avl tree",
            "traversal", "inorder", "preorder", "postorder", "heap"
        ],
        "Graphs & Graph Algorithms": [
            "graph", "bfs", "dfs", "dijkstra", "spanning tree", "kruskal",
            "prim", "adjacency matrix", "shortest path", "topological sort"
        ],
        "Searching & Sorting": [
            "search", "binary search", "sorting", "quick sort", "merge sort",
            "heap sort", "bubble sort", "insertion sort", "time complexity", "big-o"
        ]
    },
    "Computer Networks": {
        "Network Models & Architecture": [
            "osi model", "tcp/ip", "layers", "protocol", "topology", "lan", "wan", "star", "mesh"
        ],
        "Data Link Layer": [
            "framing", "error detection", "crc", "flow control", "stop-and-wait", "sliding window", "mac", "ethernet"
        ],
        "Network Layer & Routing": [
            "ip addressing", "ipv4", "ipv6", "subnetting", "routing", "distance vector", "link state", "router", "nat"
        ],
        "Transport Layer": [
            "tcp", "udp", "three-way handshake", "flow control", "congestion control", "port numbers", "segment"
        ],
        "Application Layer": [
            "dns", "http", "https", "ftp", "smtp", "dhcp", "telnet", "socket"
        ]
    },
    "Software Engineering": {
        "SDLC & Agile": [
            "sdlc", "waterfall", "agile", "scrum", "spiral", "iterative", "sprint", "kanban"
        ],
        "Requirement Engineering": [
            "srs", "requirements", "functional", "non-functional", "feasibility", "use case", "user story"
        ],
        "Software Design & Architecture": [
            "architectural design", "coupling", "cohesion", "dfd", "uml", "class diagram", "design patterns"
        ],
        "Software Testing & QA": [
            "testing", "unit testing", "integration testing", "black box", "white box", "verification", "validation", "qa"
        ]
    },
    "Machine Learning": {
        "Supervised Learning": [
            "supervised learning", "linear regression", "logistic regression", "decision tree",
            "svm", "knn", "classification", "regression"
        ],
        "Unsupervised Learning": [
            "unsupervised learning", "clustering", "k-means", "pca", "dimensionality reduction",
            "hierarchical", "density-based"
        ],
        "Model Evaluation": [
            "evaluation", "confusion matrix", "precision", "recall", "f1-score", "roc-auc",
            "cross-validation", "overfitting", "underfitting", "bias-variance"
        ],
        "Deep Learning & Ensembles": [
            "random forest", "gradient boosting", "neural network", "deep learning",
            "perceptron", "backpropagation", "cnn", "rnn"
        ]
    }
}


# ----------------------------------------------------------------------
# 2. Bloom's Taxonomy Cognitive Classification
# ----------------------------------------------------------------------
BLOOM_LEVEL_PATTERNS = {
    "Create": [
        r"\b(?:design|develop|construct|formulate|architect|compose|build\s+(?:a\s+)?pipeline|propose\s+a\s+solution|create\s+a\s+(?:system|class|architecture|model))\b"
    ],
    "Evaluate": [
        r"\b(?:evaluate|justify|critique|assess|verify|defend|prioritize|validate|critically\s+examine|judge)\b"
    ],
    "Analyze": [
        r"\b(?:analyze|compare|contrast|differentiate|distinguish\s+between|difference\s+between|differences\s+between|categorize|deconstruct|correlate|examine|investigate|feature\s+analysis)\b"
    ],
    "Apply": [
        r"\b(?:apply|implement|solve|calculate|compute|find\s+the\s+value|write\s+(?:a\s+)?(?:python|c\+\+|java)?\s*(?:program|code|script)|write\s+(?:an?\s+)?sql\s+query|demonstrate|use|utilize|execute)\b"
    ],
    "Understand": [
        r"\b(?:explain|describe|discuss|illustrate|summarize|interpret|clarify|outline|how\s+do\s+they\s+differ|briefly\s+explain|elaborate)\b"
    ],
    "Remember": [
        r"\b(?:define|list|state|name|identify|recall|mention|label|enumerate|what\s+is|what\s+are|give\s+the\s+definition|what\s+do\s+you\s+mean\s+by)\b"
    ]
}


def classify_bloom_level(text: str) -> str:
    """
    Classify question cognitive depth according to Bloom's Taxonomy.
    Transparent, deterministic rule-based matching.
    """
    cleaned = text.lower()
    for level, patterns in BLOOM_LEVEL_PATTERNS.items():
        for pat in patterns:
            if re.search(pat, cleaned):
                return level
    return "Unclassified"


# ----------------------------------------------------------------------
# 3. Question Type Classification
# ----------------------------------------------------------------------
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
    "Comparison": [
        r"\b(?:compare|differentiate|distinguish\s+between|difference\s+between|differences\s+between|compare\s+and\s+contrast|vs\.?)\b"
    ],
    "Application": [
        r"\b(?:apply|design|develop|construct|formulate|case\s+study|real-world|scenario|suggest\s+a\s+solution|propose\s+a|how\s+would\s+you\s+design|pipeline)\b"
    ],
    "Problem Solving": [
        r"\b(?:handle|clean|detect|troubleshoot|debug|fix|identify\s+missing|imputation|outlier\s+detection)\b"
    ],
    "Explanation": [
        r"\b(?:explain|describe|elaborate|illustrate|clarify)\b"
    ],
    "Theory": [
        r"\b(?:discuss|justify|summarize|critically\s+examine|concept|principles?)\b"
    ]
}


def classify_question_type(text: str, marks: Optional[int] = None) -> str:
    """
    Classify question type using rule-based/NLP action verb patterns and marks.
    Transparently rule-based.
    """
    cleaned = text.strip()
    
    # Priority order checks
    for pat in TYPE_PATTERNS["Programming"]:
        if re.search(pat, cleaned, re.IGNORECASE):
            return "Programming"

    for pat in TYPE_PATTERNS["Numerical"]:
        if re.search(pat, cleaned, re.IGNORECASE):
            return "Numerical"

    for pat in TYPE_PATTERNS["Comparison"]:
        if re.search(pat, cleaned, re.IGNORECASE):
            return "Comparison"

    for pat in TYPE_PATTERNS["Definition"]:
        if re.search(pat, cleaned, re.IGNORECASE):
            return "Definition"

    for pat in TYPE_PATTERNS["Application"]:
        if re.search(pat, cleaned, re.IGNORECASE):
            return "Application"

    for pat in TYPE_PATTERNS["Problem Solving"]:
        if re.search(pat, cleaned, re.IGNORECASE):
            return "Problem Solving"

    for pat in TYPE_PATTERNS["Explanation"]:
        if re.search(pat, cleaned, re.IGNORECASE):
            return "Explanation"

    for pat in TYPE_PATTERNS["Theory"]:
        if re.search(pat, cleaned, re.IGNORECASE):
            return "Theory"

    # Fallback based on marks and text length
    if marks is not None and marks <= 2:
        return "Definition"
    elif marks is not None and marks >= 10:
        return "Explanation"
    
    return "Theory"


# ----------------------------------------------------------------------
# 4. Syllabus Topic Mapping Engine
# ----------------------------------------------------------------------
def resolve_subject_syllabus(subject_name: str) -> Optional[Dict[str, List[str]]]:
    """Find the best matching syllabus dictionary for a subject string."""
    if not subject_name:
        return None
    s_norm = subject_name.lower().strip()
    for subj_key, topics in SUBJECT_SYLLABUS_TOPICS.items():
        k_norm = subj_key.lower()
        if k_norm in s_norm or s_norm in k_norm:
            return topics
        # Alias matching
        if "python" in s_norm and "analytic" in s_norm and "analytics" in k_norm:
            return topics
        if "dbms" in s_norm and "database" in k_norm:
            return topics
        if "os" == s_norm and "operating systems" in k_norm:
            return topics
    return None


def classify_topic(text: str, subject_name: str = "") -> str:
    """
    Map question text to an authentic syllabus topic for the given subject.
    If the question does not match any syllabus topic, return 'Other / Unclassified'.
    Never forces questions into unrelated topics.
    """
    syllabus = resolve_subject_syllabus(subject_name)
    if not syllabus:
        return "Other / Unclassified"

    text_lower = text.lower()
    best_topic = None
    best_score = 0

    for topic_name, keywords in syllabus.items():
        score = 0
        for kw in keywords:
            # Word boundary regex search
            if re.search(rf"\b{re.escape(kw.lower())}\b", text_lower):
                # Weight longer multi-word keywords higher for precision
                score += 2 if " " in kw else 1
        
        if score > best_score:
            best_score = score
            best_topic = topic_name

    if best_score > 0 and best_topic:
        return best_topic

    return "Other / Unclassified"


# ----------------------------------------------------------------------
# 5. Multi-Signal Difficulty Estimation
# ----------------------------------------------------------------------
def estimate_question_difficulty(
    text: str,
    marks: Optional[int],
    q_type: str,
    bloom_level: str
) -> Dict[str, Any]:
    """
    Multi-signal transparent difficulty estimation.
    Signals used:
    1. Bloom's cognitive level
    2. Marks allocation (weightage)
    3. Type complexity (Programming / Application / Comparison / Definition)
    4. Text phrasing complexity
    """
    score = 0
    signals = []

    # 1. Bloom's level signal
    if bloom_level in ["Create", "Evaluate"]:
        score += 3
        signals.append(f"High-order cognitive demand ({bloom_level})")
    elif bloom_level in ["Analyze"]:
        score += 2
        signals.append(f"Analytical synthesis ({bloom_level})")
    elif bloom_level in ["Apply"]:
        score += 1
        signals.append(f"Practical execution ({bloom_level})")
    elif bloom_level in ["Understand"]:
        score += 1
        signals.append(f"Conceptual explanation ({bloom_level})")
    elif bloom_level in ["Remember"]:
        score += 0
        signals.append("Direct factual recall (Remember)")

    # 2. Marks weightage signal
    if marks is not None:
        if marks >= 10:
            score += 2
            signals.append(f"High weightage ({marks} Marks)")
        elif marks >= 5:
            score += 1
            signals.append(f"Standard weightage ({marks} Marks)")
        elif marks <= 2:
            score -= 1
            signals.append(f"Short weightage ({marks} Marks)")

    # 3. Question type complexity
    if q_type in ["Programming", "Application", "Problem Solving"]:
        score += 1
        signals.append(f"Practical/Applied type ({q_type})")
    elif q_type == "Numerical":
        score += 1
        signals.append("Quantitative computation")
    elif q_type == "Comparison":
        score += 1
        signals.append("Comparative analysis")
    elif q_type == "Definition":
        score -= 1
        signals.append("Direct definition")

    # 4. Text length
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
        "disclaimer": "Difficulty is an estimated classification based on cognitive depth, type, and weightage."
    }


# ----------------------------------------------------------------------
# 6. TF-IDF Keyword Extraction & Clustering
# ----------------------------------------------------------------------
def extract_keywords_and_clusters(questions: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Perform TF-IDF keyword extraction and unsupervised KMeans topic clustering.
    """
    if not questions:
        return {
            "top_paper_keywords": [],
            "topic_clusters": [],
            "processed_questions": []
        }

    docs = [q["text"] for q in questions]
    n_docs = len(docs)

    custom_stop_words = [
        "question", "marks", "explain", "describe", "define", "what", "write",
        "answer", "following", "following:", "diagram", "diagrams", "example",
        "examples", "state", "list", "discuss", "detail", "details", "short", "note",
        "given", "using", "suitable", "differentiate", "distinguish", "difference"
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
        
        filtered_indices = [
            i for i, fn in enumerate(feature_names)
            if fn.lower() not in custom_stop_words and len(fn) > 2
        ]
        if not filtered_indices:
            filtered_indices = list(range(len(feature_names)))

    except Exception:
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
        for idx in range(len(row)):
            if feature_names[idx].lower() in custom_stop_words or len(feature_names[idx]) <= 2:
                row[idx] = 0.0

        top_indices = row.argsort()[::-1][:4]
        q_keywords = [feature_names[idx] for idx in top_indices if row[idx] > 0]
        
        if not q_keywords:
            raw_words = [w for w in re.findall(r"\b[a-zA-Z]{4,}\b", q["text"].lower()) if w not in custom_stop_words]
            q_keywords = list(dict.fromkeys(raw_words))[:3]
            
        q["keywords"] = q_keywords

    # Extract top overall paper keywords
    mean_scores = tfidf_matrix.toarray().mean(axis=0)
    for idx in range(len(mean_scores)):
        if feature_names[idx].lower() in custom_stop_words or len(feature_names[idx]) <= 2:
            mean_scores[idx] = 0.0

    top_paper_indices = mean_scores.argsort()[::-1][:10]
    top_paper_keywords = [
        feature_names[idx] for idx in top_paper_indices if mean_scores[idx] > 0
    ]

    # Unsupervised Topic Clustering
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


# ----------------------------------------------------------------------
# 7. Paper Insights Generation
# ----------------------------------------------------------------------
def generate_paper_insights(
    questions: List[Dict[str, Any]],
    parsed_info: Dict[str, Any],
    topic_distribution: List[Dict[str, Any]],
    diff_dist: Dict[str, int],
    type_dist: Dict[str, int],
    bloom_dist: Dict[str, int]
) -> List[Dict[str, str]]:
    """Generate honest, data-grounded insights strictly based on calculated values."""
    insights = []
    total_q = len(questions)
    if total_q == 0:
        return insights

    # 1. Topic prominence insight
    classified_topics = [t for t in topic_distribution if t["topic"] != "Other / Unclassified"]
    if classified_topics:
        top_topic = classified_topics[0]
        top_pct = top_topic["percentage"]
        insights.append({
            "type": "primary",
            "icon": "bi-pie-chart",
            "title": f"Top Syllabus Focus: {top_topic['topic']}",
            "text": f"{top_pct}% ({top_topic['count']} questions, {top_topic['marks']} Marks) of the paper is based on {top_topic['topic']}."
        })

        if len(classified_topics) >= 2:
            second_topic = classified_topics[1]
            last_topic = classified_topics[-1]
            if top_topic["marks"] > (last_topic["marks"] * 2):
                insights.append({
                    "type": "info",
                    "icon": "bi-arrow-left-right",
                    "title": "Topic Representation Variance",
                    "text": f"{last_topic['topic']} has relatively lower weightage ({last_topic['marks']}M) compared with {top_topic['topic']} ({top_topic['marks']}M)."
                })

    # 2. Difficulty distribution insight
    hard_count = diff_dist.get("Hard", 0)
    hard_pct = round((hard_count / total_q) * 100)
    hard_marks = sum(q.get("marks", 0) or 0 for q in questions if q.get("difficulty") == "Hard")

    if hard_pct >= 30:
        insights.append({
            "type": "warning",
            "icon": "bi-exclamation-triangle",
            "title": "High Cognitive Demand",
            "text": f"Hard questions account for {hard_pct}% ({hard_count} questions) and contribute {hard_marks} total marks."
        })
    else:
        med_pct = round((diff_dist.get("Medium", 0) / total_q) * 100)
        insights.append({
            "type": "success",
            "icon": "bi-check2-circle",
            "title": "Balanced Question Difficulty",
            "text": f"Medium-difficulty questions comprise {med_pct}% of the paper, offering balanced academic assessment."
        })

    # 3. Practical / Applied content
    practical_types = ["Programming", "Application", "Numerical", "Problem Solving"]
    practical_count = sum(type_dist.get(t, 0) for t in practical_types)
    practical_pct = round((practical_count / total_q) * 100)

    if practical_count > 0:
        insights.append({
            "type": "info",
            "icon": "bi-code-slash",
            "title": "Practical & Application Weightage",
            "text": f"Application, coding, and problem-solving questions account for {practical_pct}% ({practical_count}/{total_q}) of the paper."
        })
    else:
        insights.append({
            "type": "secondary",
            "icon": "bi-book",
            "title": "Theoretical Assessment",
            "text": "The paper focuses predominantly on conceptual explanations and theoretical understanding."
        })

    # 4. Total Marks Verification
    declared = parsed_info.get("declared_total_marks")
    detected = parsed_info.get("total_detected_marks", 0)
    if declared and detected:
        if declared == detected:
            insights.append({
                "type": "success",
                "icon": "bi-patch-check-fill",
                "title": "Total Marks Alignment",
                "text": f"Declared total marks ({declared}M) match detected question marks exactly."
            })
        else:
            diff = abs(detected - declared)
            insights.append({
                "type": "warning",
                "icon": "bi-patch-question",
                "title": "Marks Discrepancy Note",
                "text": f"Detected question marks ({detected}M) differ from declared total marks ({declared}M) by {diff} marks."
            })

    return insights


# ----------------------------------------------------------------------
# 8. Full Question Paper Analysis Pipeline
# ----------------------------------------------------------------------
def analyze_question_paper(parsed_info: Dict[str, Any], subject: str = "") -> Dict[str, Any]:
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
            "topic_distribution": [],
            "topic_clusters": [],
            "top_keywords": [],
            "insights": [],
            "quality_checks": [],
            "questions": [],
            "paper_status": "Review Required"
        }

    # 1. Classify type, Bloom's level, Topic, and Difficulty for each question
    diff_dist = {"Easy": 0, "Medium": 0, "Hard": 0}
    type_dist = {}
    bloom_dist = {}
    topic_counts = {}
    topic_marks = {}

    for q in questions:
        q_type = classify_question_type(q["text"], q["marks"])
        bloom_lvl = classify_bloom_level(q["text"])
        topic_name = classify_topic(q["text"], subject)
        diff_info = estimate_question_difficulty(q["text"], q["marks"], q_type, bloom_lvl)
        
        q["question_type"] = q_type
        q["bloom_level"] = bloom_lvl
        q["topic"] = topic_name
        q["difficulty"] = diff_info["difficulty"]
        q["difficulty_signals"] = diff_info["signals"]

        # Aggregate distributions
        diff_dist[q["difficulty"]] = diff_dist.get(q["difficulty"], 0) + 1
        type_dist[q_type] = type_dist.get(q_type, 0) + 1
        bloom_dist[bloom_lvl] = bloom_dist.get(bloom_lvl, 0) + 1
        
        topic_counts[topic_name] = topic_counts.get(topic_name, 0) + 1
        m_val = q.get("marks") or 0
        topic_marks[topic_name] = topic_marks.get(topic_name, 0) + m_val

    # 2. NLP TF-IDF & Topic Clustering (for unsupervised term verification)
    nlp_result = extract_keywords_and_clusters(questions)
    top_keywords = nlp_result["top_paper_keywords"]
    topic_clusters = nlp_result["topic_clusters"]
    processed_questions = nlp_result["processed_questions"]

    # 3. Topic & Marks Distribution List
    total_q = len(processed_questions)
    total_detected_marks = parsed_info.get("total_detected_marks", 0)

    # Sort topics: classified topics first (by count descending), unclassified last
    sorted_topic_names = sorted(
        topic_counts.keys(),
        key=lambda t: (0 if t != "Other / Unclassified" else 1, -topic_counts[t])
    )

    topic_distribution = []
    for t_name in sorted_topic_names:
        cnt = topic_counts[t_name]
        m = topic_marks.get(t_name, 0)
        pct = round((cnt / total_q) * 100, 1) if total_q > 0 else 0
        m_pct = round((m / total_detected_marks) * 100, 1) if total_detected_marks > 0 else 0
        topic_distribution.append({
            "topic": t_name,
            "count": cnt,
            "marks": m,
            "percentage": pct,
            "marks_percentage": m_pct
        })

    # 4. Marks Range Buckets
    marks_ranges = {"1-2 Marks": 0, "3-5 Marks": 0, "6-10 Marks": 0, "11+ Marks": 0, "Marks not detected": 0}
    valid_marks_list = []
    for q in processed_questions:
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
            marks_ranges["Marks not detected"] += 1

    if marks_ranges["Marks not detected"] == 0:
        del marks_ranges["Marks not detected"]

    # 5. Quality Checks Checklist (Section 19)
    quality_checks = []
    has_review_flags = False

    # Check 1: Questions Detected
    if total_q > 0:
        quality_checks.append({
            "name": "Questions Detected",
            "passed": True,
            "status": "success",
            "icon": "bi-check-circle-fill",
            "label": f"{total_q} questions successfully detected"
        })
    else:
        has_review_flags = True
        quality_checks.append({
            "name": "Questions Detected",
            "passed": False,
            "status": "danger",
            "icon": "bi-x-circle-fill",
            "label": "No questions detected"
        })

    # Check 2: Marks Extraction
    missing_m = total_q - len(valid_marks_list)
    if missing_m == 0 and len(valid_marks_list) > 0:
        quality_checks.append({
            "name": "Marks Detection",
            "passed": True,
            "status": "success",
            "icon": "bi-check-circle-fill",
            "label": f"All {total_q} questions have detected marks ({total_detected_marks} Marks total)"
        })
    elif missing_m > 0:
        has_review_flags = True
        quality_checks.append({
            "name": "Marks Detection",
            "passed": False,
            "status": "warning",
            "icon": "bi-exclamation-triangle-fill",
            "label": f"{missing_m} question(s) without detected marks"
        })

    # Check 3: Total Marks Consistency (Section 7)
    decl_marks = parsed_info.get("declared_total_marks")
    if decl_marks is not None:
        if decl_marks == total_detected_marks:
            marks_status = "Valid"
            quality_checks.append({
                "name": "Total Marks Alignment",
                "passed": True,
                "status": "success",
                "icon": "bi-check-circle-fill",
                "label": f"Declared Total ({decl_marks}M) matches Detected Total ({total_detected_marks}M) — Status: Valid"
            })
        else:
            has_review_flags = True
            marks_status = "Review Required"
            quality_checks.append({
                "name": "Total Marks Alignment",
                "passed": False,
                "status": "warning",
                "icon": "bi-exclamation-triangle-fill",
                "label": f"Declared ({decl_marks}M) vs Detected ({total_detected_marks}M) — Status: Review Required"
            })
    else:
        marks_status = "Review Required"
        quality_checks.append({
            "name": "Total Marks Alignment",
            "passed": False,
            "status": "info",
            "icon": "bi-info-circle-fill",
            "label": f"Detected Total: {total_detected_marks}M (Declared total not stated in header)"
        })

    # Check 4: Duplicate Detection
    dup_count = parsed_info.get("duplicate_count", 0)
    if dup_count == 0:
        quality_checks.append({
            "name": "Duplicate Prevention",
            "passed": True,
            "status": "success",
            "icon": "bi-check-circle-fill",
            "label": "No duplicate questions detected"
        })
    else:
        has_review_flags = True
        quality_checks.append({
            "name": "Duplicate Prevention",
            "passed": False,
            "status": "warning",
            "icon": "bi-exclamation-triangle-fill",
            "label": f"{dup_count} potential duplicate question(s) detected"
        })

    # Check 5: Topic Mapping Coverage (Section 9)
    unclass_count = topic_counts.get("Other / Unclassified", 0)
    if unclass_count == 0:
        quality_checks.append({
            "name": "Syllabus Topic Mapping",
            "passed": True,
            "status": "success",
            "icon": "bi-check-circle-fill",
            "label": "All questions mapped to subject syllabus topics"
        })
    else:
        quality_checks.append({
            "name": "Syllabus Topic Mapping",
            "passed": True if unclass_count <= (total_q // 2) else False,
            "status": "info" if unclass_count <= (total_q // 2) else "warning",
            "icon": "bi-info-circle-fill" if unclass_count <= (total_q // 2) else "bi-exclamation-triangle-fill",
            "label": f"{total_q - unclass_count} mapped, {unclass_count} classified as Other / Unclassified"
        })

    # Check 6: Difficulty Distribution
    quality_checks.append({
        "name": "Difficulty Distribution",
        "passed": True,
        "status": "success",
        "icon": "bi-check-circle-fill",
        "label": f"Easy: {diff_dist.get('Easy', 0)}, Medium: {diff_dist.get('Medium', 0)}, Hard: {diff_dist.get('Hard', 0)}"
    })

    overall_status = "Review Required" if has_review_flags else "Valid"

    # 6. KPIs
    avg_marks = round(total_detected_marks / len(valid_marks_list), 1) if valid_marks_list else 0.0
    min_marks = min(valid_marks_list) if valid_marks_list else 0
    max_marks = max(valid_marks_list) if valid_marks_list else 0
    topics_detected = len([t for t in topic_counts.keys() if t != "Other / Unclassified"])

    kpis = {
        "total_questions": total_q,
        "total_detected_marks": total_detected_marks,
        "declared_total_marks": decl_marks,
        "marks_status": marks_status,
        "average_marks": avg_marks,
        "min_marks": min_marks,
        "max_marks": max_marks,
        "questions_with_marks": len(valid_marks_list),
        "questions_without_marks": total_q - len(valid_marks_list),
        "hard_questions_count": diff_dist.get("Hard", 0),
        "medium_questions_count": diff_dist.get("Medium", 0),
        "easy_questions_count": diff_dist.get("Easy", 0),
        "topics_detected_count": topics_detected if topics_detected > 0 else len(topic_counts),
        "overall_status": overall_status
    }

    # 7. Charts Data
    palette_blue = ["#2563EB", "#3B82F6", "#60A5FA", "#93C5FD", "#1D4ED8", "#1E40AF", "#64748B"]
    charts = {
        "difficulty": {
            "labels": list(diff_dist.keys()),
            "data": list(diff_dist.values()),
            "colors": ["#16A34A", "#F59E0B", "#DC2626"]  # Green, Amber, Red
        },
        "question_type": {
            "labels": list(type_dist.keys()),
            "data": list(type_dist.values()),
            "colors": (palette_blue * 2)[:len(type_dist)]
        },
        "bloom_level": {
            "labels": list(bloom_dist.keys()),
            "data": list(bloom_dist.values()),
            "colors": ["#3B82F6", "#10B981", "#F59E0B", "#8B5CF6", "#EC4899", "#6366F1", "#94A3B8"]
        },
        "marks_distribution": {
            "labels": list(marks_ranges.keys()),
            "data": list(marks_ranges.values()),
            "colors": (palette_blue * 2)[:len(marks_ranges)]
        },
        "topic_distribution": {
            "labels": [t["topic"] for t in topic_distribution],
            "data": [t["count"] for t in topic_distribution],
            "marks": [t["marks"] for t in topic_distribution],
            "colors": (palette_blue * 3)[:len(topic_distribution)]
        },
        "topic_clusters": {
            "labels": [c["name"] for c in topic_clusters],
            "data": [c["count"] for c in topic_clusters],
            "colors": (palette_blue * 2)[:len(topic_clusters)]
        }
    }

    # 8. Automatic Insights
    insights = generate_paper_insights(
        processed_questions,
        parsed_info,
        topic_distribution,
        diff_dist,
        type_dist,
        bloom_dist
    )

    return {
        "success": True,
        "error": None,
        "kpis": kpis,
        "charts": charts,
        "topic_distribution": topic_distribution,
        "topic_clusters": topic_clusters,
        "top_keywords": top_keywords,
        "insights": insights,
        "quality_checks": quality_checks,
        "paper_status": overall_status,
        "questions": processed_questions,
        "sections": parsed_info.get("sections", ["General"])
    }
