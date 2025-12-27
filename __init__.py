"""
LLM Extraction module for matrimonial biodata.

Converts plain text from the Extraction layer into structured JSON.

Public API:
    - extract_profile(text: str) -> dict: Main extraction function

Example:
    >>> from llmextraction import extract_profile
    >>> text = "John Doe, 28 years, Software Engineer, Hindu, Delhi"
    >>> profile = extract_profile(text)
    >>> print(profile["full_name"])
    John Doe
"""

from .llmextractor import extract_profile, LLMExtractor
from .config import EXTRACTION_SCHEMA

__all__ = ["extract_profile", "LLMExtractor", "EXTRACTION_SCHEMA"]
