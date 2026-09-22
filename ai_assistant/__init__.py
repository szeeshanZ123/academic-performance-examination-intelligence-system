"""AI Student & Study Helper Module.

Provides:
- ai_helper_bp: Flask blueprint with web views and JSON endpoints.
- answer_student_academic_query: Performance analyzer for logged-in students.
- process_uploaded_document: Document processor for study assistant.
"""

from ai_assistant.routes import ai_helper_bp

__all__ = ["ai_helper_bp"]
