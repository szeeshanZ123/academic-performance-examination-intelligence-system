"""Question Paper Intelligence module for the Academic Performance and Examination Intelligence System.

Provides document text extraction, question & marks parsing, NLP topic clustering,
rule-based question classification, difficulty estimation, and paper-level analytics.
"""

from .extractor import extract_text_from_file
from .parser import parse_question_paper
from .analyzer import analyze_question_paper

__all__ = [
    "extract_text_from_file",
    "parse_question_paper",
    "analyze_question_paper"
]
