"""Master data lookup functions - find and return complete master records.

Instead of fuzzy matching, this module provides lookup functions that find exact
or close matches in master files and return the complete structured row data.
"""

from pathlib import Path
from typing import Dict, List, Optional, Tuple
import pandas as pd

from . import masters


def lookup_caste_by_any_field(
    value: str,
    master_dir: Optional[Path] = None
) -> Optional[Dict[str, str]]:
    """
    Search caste master for given value in ANY column (Jaati, Caste, Gotra, Sakha).
    
    If found, return the first matching complete row with all fields:
    {
        'jaati': '...',
        'caste': '...',
        'gotra': '...',
        'sakha': '...'
    }
    
    This function searches case-insensitively and returns all matching fields
    from the master record, filling in remaining fields based on the match found.
    
    Example:
        - lookup_caste_by_any_field("Upmanyu") -> returns row where Gotra='Upmanyu'
        - lookup_caste_by_any_field("Joshi") -> returns row where Caste='Joshi'
        - lookup_caste_by_any_field("Pareek") -> returns row where Jaati='Pareek'
    """
    if not value or not isinstance(value, str):
        return None
    
    value = value.strip()
    if not value:
        return None
    
    # Default master_dir if not provided
    if master_dir is None:
        master_dir = Path(__file__).resolve().parent.parent / "Data" / "training"
    
    try:
        df = masters.load_master("caste", master_dir=master_dir)
    except Exception as e:
        return None
    
    # Standardize column names - handle different case variations
    df.columns = [col.lower().replace(' ', '_') for col in df.columns]
    
    # Fields to search in (in order of priority - more specific to more general)
    search_fields = ['gotra', 'sakha', 'caste', 'jaati']
    
    # First try exact matches (case-insensitive)
    for search_field in search_fields:
        if search_field in df.columns:
            mask = df[search_field].notna()
            col_data = df[search_field][mask].astype(str).str.lower().str.strip()
            matches = df[mask][col_data == value.lower()]
            if not matches.empty:
                row = matches.iloc[0]
                return {
                    "jaati": str(row.get("jaati", "")).strip() or None,
                    "caste": str(row.get("caste", "")).strip() or None,
                    "gotra": str(row.get("gotra", "")).strip() or None,
                    "sakha": str(row.get("sakha", "")).strip() or None,
                }
    
    # If no exact match, try fuzzy matching for each field
    from .matcher import match_one
    
    for search_field in search_fields:
        if search_field in df.columns:
            field_values = df[search_field].dropna().astype(str).tolist()
            if field_values:
                match, score, details = match_one(value, field_values, scorer="auto", threshold=80.0)
                if match:
                    # Find the row with this match
                    matches = df[df[search_field].astype(str).str.lower().str.strip() == match.lower()]
                    if not matches.empty:
                        row = matches.iloc[0]
                        return {
                            "jaati": str(row.get("jaati", "")).strip() or None,
                            "caste": str(row.get("caste", "")).strip() or None,
                            "gotra": str(row.get("gotra", "")).strip() or None,
                            "sakha": str(row.get("sakha", "")).strip() or None,
                        }
    
    return None


def lookup_height_exact(
    value: str,
    master_dir: Optional[Path] = None
) -> Optional[str]:
    """
    Find exact or very close height match in master and return the canonical format.
    
    Normalizes the input height format and searches for matching entry in master.
    Returns the master format height value.
    
    Example:
        - lookup_height_exact("5ft 11in") -> "4ft 11in (149 cms)" (from master)
        - lookup_height_exact("5 feet 11 inch") -> matches after normalization
    """
    if not value or not isinstance(value, str):
        return None
    
    # Normalize input format: "5 feet 11 inch" -> "5ft 11in"
    normalized = value.lower().strip()
    normalized = normalized.replace("feet", "ft").replace("foot", "ft")
    normalized = normalized.replace("inch", "in").replace("inches", "in")
    normalized = normalized.replace("'", "ft").replace('"', "in")
    normalized = " ".join(normalized.split())  # Clean up spaces
    
    # Default master_dir if not provided
    if master_dir is None:
        master_dir = Path(__file__).resolve().parent.parent / "Data" / "training"
    
    try:
        df = masters.load_master("height", master_dir=master_dir)
    except Exception:
        return None
    
    # Search for exact match (after normalizing master values too)
    height_col = df.columns[0]  # Usually 'Height'
    
    for idx, master_val in enumerate(df[height_col]):
        if not master_val or pd.isna(master_val):
            continue
        
        master_normalized = str(master_val).lower().strip()
        master_normalized = master_normalized.replace("feet", "ft").replace("foot", "ft")
        master_normalized = master_normalized.replace("inch", "in").replace("inches", "in")
        master_normalized = " ".join(master_normalized.split())
        
        # Check if input normalized matches master normalized (or is contained)
        if normalized in master_normalized or master_normalized in normalized:
            return str(master_val).strip()
    
    return None


def lookup_address_by_pincode(
    pin_code: str,
    master_dir: Optional[Path] = None
) -> Optional[Dict[str, str]]:
    """
    Find address components (country, state, city) by pin code using master.
    
    Handles intelligent filling of missing address components:
    - If pin_code is provided, lookup to get state and city
    - Returns all available fields from the master record
    
    Returns:
    {
        'country': '...',
        'state': '...',
        'city': '...',
        'zip_code': '...',
        ...other fields from master...
    }
    
    Note: Master file structure will determine available fields.
    """
    if not pin_code or not isinstance(pin_code, str):
        return None
    
    pin_code = pin_code.strip()
    if not pin_code:
        return None
    
    # Default master_dir if not provided
    if master_dir is None:
        master_dir = Path(__file__).resolve().parent.parent / "Data" / "training"
    
    try:
        df = masters.load_master("country_state", master_dir=master_dir)
    except Exception:
        return None
    
    # Standardize column names for easier matching
    df.columns = [col.lower().replace(' ', '_') for col in df.columns]
    
    # Check if there's a pin code column
    pin_cols = [col for col in df.columns if 'pin' in col or 'zip' in col or 'postal' in col]
    
    if not pin_cols:
        # If no pin code column, we can't lookup by pin code
        return None
    
    # Search for matching pin code
    for pin_col in pin_cols:
        matches = df[df[pin_col].astype(str).str.strip() == pin_code]
        if not matches.empty:
            row = matches.iloc[0]
            result = {}
            
            # Extract specific fields if they exist
            for field in ['country', 'state', 'city', 'zip_code', 'postal_code']:
                for col in df.columns:
                    if col == field or col.startswith(field):
                        val = row.get(col)
                        if pd.notna(val):
                            result[field] = str(val).strip()
                            break
            
            # If we got the zip_code field, ensure it's included
            if 'zip_code' not in result:
                result['zip_code'] = pin_code
            
            return result if result else None
    
    return None


def lookup_qualification(
    value: str,
    master_dir: Optional[Path] = None
) -> Optional[str]:
    """
    Lookup qualification in master and return canonical form.
    If not found in master, return the original value.
    
    Handles comma-separated qualifications and returns them all (or the first matching one).
    
    Example:
        - lookup_qualification("B.com") -> "B.Com"
        - lookup_qualification("Bachelor of Commerce") -> "B.Com"
        - lookup_qualification("MBA, B.Com") -> "MBA, B.Com" (if both found)
        - lookup_qualification("Some Degree") -> "Some Degree" (if not in master)
    """
    if not value or not isinstance(value, str):
        return None
    
    value = value.strip()
    if not value:
        return None
    
    # Default master_dir if not provided
    if master_dir is None:
        master_dir = Path(__file__).resolve().parent.parent / "Data" / "training"
    
    try:
        df = masters.load_master("qualification", master_dir=master_dir)
    except Exception:
        # If master can't be loaded, return original value
        return value
    
    qual_col = df.columns[0]  # Usually 'Qualification'
    
    # Handle comma-separated values - try each one
    values_to_try = [v.strip() for v in value.split(",")]
    matched_values = []
    unmatched_values = []
    
    for val in values_to_try:
        if not val:
            continue
        
        matched = False
        
        # First try exact match (case-insensitive)
        for master_val in df[qual_col].dropna():
            if str(master_val).lower().strip() == val.lower():
                matched_values.append(str(master_val).strip())
                matched = True
                break
        
        if not matched:
            # Try fuzzy match if no exact match
            from .matcher import match_one
            qual_values = df[qual_col].dropna().astype(str).tolist()
            match, score, details = match_one(val, qual_values, scorer="auto", threshold=80.0)
            if match:
                matched_values.append(match)
                matched = True
        
        if not matched:
            unmatched_values.append(val)
    
    # Return matched values combined with unmatched ones
    all_values = matched_values + unmatched_values
    if all_values:
        return ", ".join(all_values)
    
    # Fallback: return original value
    return value


def lookup_occupation(
    value: str,
    master_dir: Optional[Path] = None
) -> Optional[str]:
    """
    Lookup occupation in master and return canonical form.
    If not found in master, return the original value.
    
    Example:
        - lookup_occupation("Business") -> "Business"
        - lookup_occupation("Self Employed") -> "Self Employed"
        - lookup_occupation("Senior Reference Data Associate") -> "Senior Reference Data Associate" (if not in master)
    """
    if not value or not isinstance(value, str):
        return None
    
    value = value.strip()
    if not value:
        return None
    
    # Default master_dir if not provided
    if master_dir is None:
        master_dir = Path(__file__).resolve().parent.parent / "Data" / "training"
    
    try:
        df = masters.load_master("occupation", master_dir=master_dir)
    except Exception:
        # If master can't be loaded, return original value
        return value
    
    occ_col = df.columns[0]  # Usually 'Occupation'
    
    # First try exact match (case-insensitive)
    for val in df[occ_col].dropna():
        if str(val).lower().strip() == value.lower():
            return str(val).strip()
    
    # Try fuzzy match if no exact match
    from .matcher import match_one
    occ_values = df[occ_col].dropna().astype(str).tolist()
    match, score, details = match_one(value, occ_values, scorer="auto", threshold=80.0)
    # If fuzzy match found, return it; otherwise return original value
    return match if match else value


def lookup_marital_status(
    value: str,
    master_dir: Optional[Path] = None
) -> Optional[str]:
    """
    STRICT lookup for marital_status - ONLY returns value if found in master.
    
    Returns the exact master value if found (exact or fuzzy match).
    Returns None if NOT found in master (no fallback to original value).
    
    Valid values from master: "Single", "Married", "Divorced", "Widowed", 
                              "Separated", "Un-Married", "Awaiting Divorce"
    
    Example:
        - lookup_marital_status("married") -> "Married"
        - lookup_marital_status("single") -> "Single"
        - lookup_marital_status("invalid_status") -> None (STRICT - not in master)
    """
    if not value or not isinstance(value, str):
        return None
    
    value = value.strip()
    if not value:
        return None
    
    # Default master_dir if not provided
    if master_dir is None:
        master_dir = Path(__file__).resolve().parent.parent / "Data" / "training"
    
    try:
        df = masters.load_master("marital_status", master_dir=master_dir)
    except Exception:
        # If master can't be loaded, return None (STRICT mode)
        return None
    
    status_col = df.columns[0]  # Usually 'Marital Status'
    
    # First try exact match (case-insensitive)
    for master_val in df[status_col].dropna():
        if str(master_val).lower().strip() == value.lower():
            return str(master_val).strip()
    
    # Try fuzzy match if no exact match
    from .matcher import match_one
    status_values = df[status_col].dropna().astype(str).tolist()
    match, score, details = match_one(value, status_values, scorer="auto", threshold=80.0)
    
    # STRICT: Only return if fuzzy match found, else None
    return match if match else None


def lookup_manglik(
    value: str,
    master_dir: Optional[Path] = None
) -> Optional[str]:
    """
    STRICT lookup for manglik (maanglik) - ONLY returns value if found in master.
    
    Returns the exact master value if found (exact or fuzzy match).
    Returns None if NOT found in master (no fallback to original value).
    
    Valid values from master: "Yes", "No", "Don't Know"
    
    Example:
        - lookup_manglik("yes") -> "Yes"
        - lookup_manglik("no") -> "No"
        - lookup_manglik("don't know") -> "Don't Know"
        - lookup_manglik("maybe") -> None (STRICT - not in master)
    """
    if not value or not isinstance(value, str):
        return None
    
    value = value.strip()
    if not value:
        return None
    
    # Default master_dir if not provided
    if master_dir is None:
        master_dir = Path(__file__).resolve().parent.parent / "Data" / "training"
    
    try:
        df = masters.load_master("manglik", master_dir=master_dir)
    except Exception:
        # If master can't be loaded, return None (STRICT mode)
        return None
    
    manglik_col = df.columns[0]  # Usually 'Manglik'
    
    # First try exact match (case-insensitive)
    for master_val in df[manglik_col].dropna():
        if str(master_val).lower().strip() == value.lower():
            return str(master_val).strip()
    
    # Try fuzzy match if no exact match
    from .matcher import match_one
    manglik_values = df[manglik_col].dropna().astype(str).tolist()
    match, score, details = match_one(value, manglik_values, scorer="auto", threshold=80.0)
    
    # STRICT: Only return if fuzzy match found, else None
    return match if match else None


def parse_education_specialization(
    education_str: str,
    master_dir: Optional[Path] = None
) -> Tuple[Optional[str], Optional[str]]:
    """
    Parse combined education/specialization strings into separate components.
    
    Handles patterns like:
    - "Msc(IT)" -> education="M.Sc", specialization="Information Technology"
    - "B.Tech (Computer Science)" -> education="B.Tech", specialization="Computer Science"
    - "MBA Finance" -> education="MBA", specialization="Finance"
    - "B.Com" -> education="B.Com", specialization=None
    
    Args:
        education_str: Raw education string (may contain both degree and specialization)
        master_dir: Directory containing master Excel files
    
    Returns:
        Tuple of (education, specialization) - both looked up from masters
        Returns (None, None) if no valid master values found
    """
    if not education_str or not isinstance(education_str, str):
        return None, None
    
    education_str = education_str.strip()
    if not education_str:
        return None, None
    
    # Default master_dir if not provided
    if master_dir is None:
        master_dir = Path(__file__).resolve().parent.parent / "Data" / "training"
    
    try:
        qual_df = masters.load_master("qualification", master_dir=master_dir)
    except Exception:
        return None, None
    
    # Patterns to split education and specialization
    import re
    
    # Pattern 1: "Degree(Specialization)" e.g., "Msc(IT)", "B.Tech(CSE)"
    pattern1 = r'^([A-Za-z.]+)\s*\(([^)]+)\)$'
    match = re.match(pattern1, education_str)
    if match:
        degree_raw = match.group(1).strip()
        spec_raw = match.group(2).strip()
    else:
        # Pattern 2: "Degree Specialization" e.g., "MBA Finance", "B.Tech Computer Science"
        # Split on first space or common delimiter
        parts = re.split(r'\s+', education_str, maxsplit=1)
        if len(parts) == 2:
            degree_raw = parts[0].strip()
            spec_raw = parts[1].strip()
        else:
            # Single component - assume it's the degree
            degree_raw = education_str
            spec_raw = None
    
    # Look up degree in qualification master
    qual_col = qual_df.columns[0]
    education_result = None
    
    if degree_raw:
        # Try exact match first
        for master_val in qual_df[qual_col].dropna():
            if str(master_val).lower().strip() == degree_raw.lower():
                education_result = str(master_val).strip()
                break
        
        # Try fuzzy match if no exact match
        if not education_result:
            from .matcher import match_one
            qual_values = qual_df[qual_col].dropna().astype(str).tolist()
            match, score, details = match_one(degree_raw, qual_values, scorer="auto", threshold=80.0)
            if match:
                education_result = match
    
    # Handle specialization - expand abbreviations and normalize
    specialization_result = None
    if spec_raw:
        # Expand common abbreviations
        abbrev_map = {
            "IT": "Information Technology",
            "CS": "Computer Science",
            "CSE": "Computer Science",
            "ECE": "Electronics and Communication",
            "ME": "Mechanical Engineering",
            "CE": "Civil Engineering",
            "EEE": "Electrical and Electronics Engineering",
            "HR": "Human Resources",
            "BM": "Business Management",
            "FM": "Finance Management",
        }
        
        spec_expanded = abbrev_map.get(spec_raw.upper(), spec_raw)
        # Clean up and normalize
        specialization_result = spec_expanded.strip()
    
    return education_result, specialization_result


__all__ = [
    "lookup_caste_by_any_field",
    "lookup_height_exact",
    "lookup_address_by_pincode",
    "lookup_qualification",
    "lookup_occupation",
    "lookup_marital_status",
    "lookup_manglik",
    "parse_education_specialization",
]
