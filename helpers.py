"""Normalization helper utilities: cleaning, parsing, date normalization, and domain helpers.

These helpers are deterministic and have clear return semantics: return canonical
string values or None when no acceptable mapping exists.
"""
from __future__ import annotations

from datetime import datetime
from typing import Iterable, List, Optional, Tuple

from dateutil import parser as dateparser

from .matcher import match_one
import re
import math


def clean_str(value: Optional[str]) -> Optional[str]:
    """Trim whitespace and normalize internal spacing; return None for empty."""
    if value is None:
        return None
    s = str(value).strip()
    s = " ".join(s.split())
    return s or None


def parse_name(full_name: Optional[str]) -> Tuple[Optional[str], Optional[str]]:
    """Split `full_name` into (first_name, last_name).

    Heuristics:
    - If comma present assume 'Last, First...'
    - Otherwise first token is first_name, last token is last_name when >1 token.
    - Preserve original casing except trim/normalize whitespace.
    """
    s = clean_str(full_name)
    if not s:
        return None, None
    if "," in s:
        parts = [p.strip() for p in s.split(",") if p.strip()]
        if len(parts) >= 2:
            last = parts[0]
            first = parts[1].split()[0] if parts[1].split() else None
            return first or None, last or None
    parts = s.split()
    if len(parts) == 1:
        return parts[0], None
    return parts[0], parts[-1]


def normalize_date(raw: Optional[str]) -> Optional[str]:
    """Parse many common date formats and return ISO `YYYY-MM-DD` or None.

    Deterministic and non-ambiguous parsing is attempted. For ambiguous dates
    the parser's default is used; invalid dates return None.
    """
    if not raw:
        return None
    s = clean_str(raw)
    if not s:
        return None
    try:
        dt = dateparser.parse(s, dayfirst=False, yearfirst=False)
    except (ValueError, OverflowError):
        return None
    if not dt:
        return None
    try:
        return dt.date().isoformat()
    except Exception:
        return None


def normalize_age(raw: Optional[str]) -> Optional[int]:
    """Return integer age if valid (1..120). Otherwise None."""
    if raw is None:
        return None
    s = clean_str(str(raw))
    if not s:
        return None
    # strip non-digits
    digits = "".join([c for c in s if c.isdigit()])
    if not digits:
        return None
    try:
        v = int(digits)
    except ValueError:
        return None
    if 0 < v <= 120:
        return v
    return None


def normalize_height(raw: Optional[str], master_values: Iterable[str], scorer: str = "auto", threshold: float = 80.0) -> Optional[str]:
    """Normalize height format and match against master values.
    
    Converts common height formats (5 feet 11 inch, 5'11", etc.) to standard format
    before fuzzy matching against master values. If master_values is empty, returns
    the normalized format directly.
    """
    s = clean_str(raw)
    if not s:
        return None
    
    # Normalize common height formats
    # Convert "5 feet 11 inch" -> "5ft 11in"
    normalized = s.lower()
    normalized = normalized.replace("feet", "ft").replace("foot", "ft")
    normalized = normalized.replace("inch", "in").replace("inches", "in")
    normalized = normalized.replace("'", "ft").replace('"', "in")
    normalized = " ".join(normalized.split())  # Clean up spaces but keep one space between ft and in
    
    # If no master values provided, just return normalized format
    master_list = list(master_values) if master_values else []
    if not master_list:
        return normalized
    
    # Try to match the normalized value first
    match, score, details = match_one(normalized, master_list, scorer=scorer, threshold=threshold)
    if match:
        return match
    
    # Fallback: try original value
    match, score, details = match_one(s, master_list, scorer=scorer, threshold=threshold)
    if match:
        return match
    
    # If no match found in master, return normalized format anyway
    return normalized


def normalize_via_master(raw: Optional[str], master_values: Iterable[str], scorer: str = "auto", threshold: float = 80.0) -> Optional[str]:
    """Try to map raw string to a canonical master value using fuzzy match.

    Returns canonical master string or None when no acceptable match found.
    """
    s = clean_str(raw)
    if not s:
        return None
    match, score, details = match_one(s, master_values, scorer=scorer, threshold=threshold)
    return match


def normalize_country_state(raw_country: Optional[str], raw_state: Optional[str], country_state_df, scorer: str = "auto", threshold: float = 80.0) -> Tuple[Optional[str], Optional[str]]:
    """Normalize country and state using CountryState master dataframe.

    Expects a dataframe where at least one column contains country names and one contains state names.
    The function will attempt to match the country first, then restrict state matching to that country.
    If country cannot be matched, state will be attempted against all states; still must meet threshold.
    """
    if country_state_df is None or country_state_df.empty:
        return None, None
    cols = list(country_state_df.columns)
    # heuristics: if there are 2 cols, assume [Country, State]
    if len(cols) >= 2:
        country_col, state_col = cols[0], cols[1]
    else:
        country_col = cols[0]
        state_col = None
    country_list = country_state_df[country_col].dropna().astype(str).unique().tolist()
    state_list = country_state_df[state_col].dropna().astype(str).unique().tolist() if state_col else []

    country = normalize_via_master(raw_country, country_list, scorer=scorer, threshold=threshold)
    state = None
    if country and state_col:
        # restrict states to those with matched country
        states_for_country = country_state_df[country_state_df[country_col].astype(str) == country][state_col].dropna().astype(str).unique().tolist()
        if states_for_country:
            state = normalize_via_master(raw_state, states_for_country, scorer=scorer, threshold=threshold)
    else:
        # try matching state against global list
        if state_col:
            state = normalize_via_master(raw_state, state_list, scorer=scorer, threshold=threshold)
    # If no explicit country was provided in the text (empty/None), default to India
    try:
        raw_country_empty = not clean_str(raw_country)
    except Exception:
        raw_country_empty = True

    if not country and raw_country_empty:
        country = "India"

    return country, state


def normalize_birth_time(raw: Optional[str]) -> Optional[str]:
    """Convert birth time to 12-hour format with A.M./P.M.
    
    Accepts various formats:
    - "14:30" or "14:30:00" (24-hour format)
    - "2:30 PM" or "2:30PM" (12-hour format)
    - "14.30" or "14-30"
    
    Returns:
        String in format "h:MM A.M." or "h:MM P.M." or None if invalid
        Examples: "2:30 A.M.", "11:45 P.M."
    """
    s = clean_str(raw)
    if not s:
        return None
    
    # Try parsing 24-hour format first (HH:MM or HH:MM:SS)
    # Also handle formats like HH.MM or HH-MM
    time_match = re.search(r'(\d{1,2})[:.\-](\d{2})(?:[:.](\d{2}))?', s)
    if time_match:
        try:
            hour = int(time_match.group(1))
            minute = int(time_match.group(2))
            
            # Valid hour and minute
            if 0 <= hour <= 23 and 0 <= minute <= 59:
                # Convert to 12-hour format
                am_pm = "AM" if hour < 12 else "PM"
                if hour == 0:
                    hour_12 = 12
                elif hour > 12:
                    hour_12 = hour - 12
                else:
                    hour_12 = hour
                
                return f"{hour_12}:{minute:02d} {am_pm}"
        except (ValueError, IndexError):
            pass
    
    # Try parsing 12-hour format that's already in correct format
    if re.search(r'(?:A\.M\.|P\.M\.|AM|PM)', s, re.IGNORECASE):
        # Check if it already has A.M./P.M.
        if re.search(r'\d{1,2}:\d{2}\s*(?:A\.M\.|P\.M\.)', s, re.IGNORECASE):
            # Already in correct format, just normalize
            match = re.search(r'(\d{1,2}):(\d{2})\s*([AP])\.?M\.?', s, re.IGNORECASE)
            if match:
                hour = int(match.group(1))
                minute = int(match.group(2))
                am_pm_char = match.group(3).upper()
                if 1 <= hour <= 12 and 0 <= minute <= 59:
                    return f"{hour}:{minute:02d} {am_pm_char}.M."
    
    return None


def normalize_height_format(raw: Optional[str]) -> Optional[str]:
    """Convert height to standard format: "xft yin (in cms)"
    
    Accepts various formats:
    - "5ft 8in" or "5'8\"" or "5 feet 8 inches"
    - "5 ft 8 in" or "5-8"
    - "173 cm" (converts to ft/in equivalent)
    
    Returns:
        String in format like "5ft 8in (173 cms)" or None if invalid
    """
    s = clean_str(raw)
    if not s:
        return None
    
    s_lower = s.lower()
    
    # Check if it's already in the desired format
    if re.search(r'\d+ft\s+\d+in\s*\(\s*\d+\s*cms\s*\)', s):
        return s
    
    # Try to parse feet and inches format
    feet_inches_match = re.search(r'(\d+)\s*(?:ft|feet|\')\s*(\d+)\s*(?:in|inch|inches|")?', s_lower)
    if feet_inches_match:
        try:
            feet = int(feet_inches_match.group(1))
            inches = int(feet_inches_match.group(2))
            
            if 0 <= feet <= 8 and 0 <= inches <= 11:
                # Convert to cm: (feet * 12 + inches) * 2.54
                total_inches = feet * 12 + inches
                cms = round(total_inches * 2.54)
                return f"{feet}ft {inches}in ({cms} cms)"
        except (ValueError, IndexError):
            pass
    
    # Try to parse cm format
    cm_match = re.search(r'(\d+)\s*(?:cm|cms|centimeter)', s_lower)
    if cm_match:
        try:
            cms = int(cm_match.group(1))
            if 100 <= cms <= 250:
                # Convert cm to feet and inches
                total_inches = round(cms / 2.54)
                feet = total_inches // 12
                remaining_inches = total_inches % 12
                return f"{feet}ft {remaining_inches}in ({cms} cms)"
        except (ValueError, IndexError):
            pass
    
    # Try to parse simple format like "5-8" or "5.8"
    simple_match = re.search(r'(\d+)[-.\s](\d+)', s)
    if simple_match:
        try:
            feet = int(simple_match.group(1))
            inches = int(simple_match.group(2))
            
            if 0 <= feet <= 8 and 0 <= inches <= 11:
                total_inches = feet * 12 + inches
                cms = round(total_inches * 2.54)
                return f"{feet}ft {inches}in ({cms} cms)"
        except (ValueError, IndexError):
            pass
    
    return None

def summarize_about_yourself(text: Optional[str]) -> Optional[str]:
    """Generate a summary of additional information from the ABOUT YOURSELF section.
    
    Processes unstructured text and returns a cleaned, formatted summary of
    the person's additional personal and professional information.
    
    Args:
        text: Raw unstructured text from ABOUT YOURSELF section
        
    Returns:
        Formatted summary string or None if text is empty
        
    Example:
        text = "I am a software engineer with 5 years of experience. I love travel and reading."
        result = summarize_about_yourself(text)
        # Returns cleaned and formatted summary
    """
    if not text:
        return None
    
    s = clean_str(text)
    if not s:
        return None
    
    # Remove common separator patterns
    s = re.sub(r'\s*[\*\-_]{2,}\s*', '\n', s)  # Replace long dashes with newlines
    
    # Clean up multiple spaces/newlines
    lines = [line.strip() for line in s.split('\n') if line.strip()]
    
    if not lines:
        return None
    
    # Join cleaned lines with proper spacing
    summary = '\n'.join(lines)
    
    # Limit length if too verbose
    if len(summary) > 1000:
        summary = summary[:1000].rsplit('\n', 1)[0] + '\n[... truncated]'
    
    return summary


# --- Field-specific normalization helpers ---
MARITAL_ALLOWED = [
    "-",
    "Awaiting Divorce",
    "Committed",
    "Divorced",
    "Married",
    "Un-Married",
    "Widow",
    "Widower",
    "Single",
    "Widowed",
    "Separated",
]

MANGLIK_ALLOWED = [
    "Yes",
    "No",
    "Don't Know",
]


def normalize_marital_status(raw: Optional[str], scorer: str = "auto", threshold: float = 80.0) -> Optional[str]:
    """Normalize common marital-status variants to canonical allowed values.

    This is a fallback used when strict master lookup fails (so pipelines still
    get a reasonable canonical value for common variants). Returns one of the
    values in `MARITAL_ALLOWED` or None.
    """
    s = clean_str(raw)
    if not s:
        return None
    low = s.lower()

    # direct case-insensitive match
    for a in MARITAL_ALLOWED:
        if a.lower() == low:
            return a

    # common variant mappings
    variants = {
        "unmarried": "Un-Married",
        "single": "Single",
        "separated": "Separated",
        "awaiting divorce": "Awaiting Divorce",
        "awaiting_divorce": "Awaiting Divorce",
        "awaiting-divorce": "Awaiting Divorce",
        "divorced": "Divorced",
        "married": "Married",
        "widow": "Widow",
        "widower": "Widower",
        "widowed": "Widowed",
        "committed": "Committed",
        "-": "-",
    }

    if low in variants:
        return variants[low]

    # fuzzy match against allowed list
    match, score, details = match_one(s, MARITAL_ALLOWED, scorer=scorer, threshold=threshold)
    return match


def normalize_manglik(raw: Optional[str], scorer: str = "auto", threshold: float = 80.0) -> Optional[str]:
    """Normalize manglik/maanglik values to canonical allowed values.

    Returns one of `MANGLIK_ALLOWED` or None.
    """
    s = clean_str(raw)
    if not s:
        return None
    low = s.lower()

    # direct match
    for a in MANGLIK_ALLOWED:
        if a.lower() == low:
            return a

    variants = {
        "yes": "Yes",
        "y": "Yes",
        "true": "Yes",
        "no": "No",
        "n": "No",
        "false": "No",
        "dont know": "Don't Know",
        "don't know": "Don't Know",
        "dontknow": "Don't Know",
        "unknown": "Don't Know",
        "maybe": None,
    }

    # strip some punctuation
    low_clean = re.sub(r"[^a-z0-9 ]", "", low)
    if low_clean in variants:
        return variants[low_clean]

    # fuzzy match against allowed values
    match, score, details = match_one(s, MANGLIK_ALLOWED, scorer=scorer, threshold=threshold)
    return match