"""
Unstructured data extractor for matrimonial profiles.
Extracts education, caste, gotra, sakha from unstructured text.
"""

from typing import Dict, List, Optional, Any
import re
from pathlib import Path

from . import masters


# Common education-related keywords and patterns
EDUCATION_PATTERNS = {
    'degree_markers': [
        r'\b(?:B\.?A|BA|Bachelor of Arts?)\b',
        r'\b(?:B\.?Sc|BSc|Bachelor of Science?)\b',
        r'\b(?:B\.?Com|BCom|Bachelor of Commerce?)\b',
        r'\b(?:B\.?Tech|BTech|Bachelor of Technology?)\b',
        r'\b(?:B\.?E|BE|Bachelor of Engineer[ing]*)\b',
        r'\b(?:M\.?A|MA|Master of Arts?)\b',
        r'\b(?:M\.?Sc|MSc|Master of Science?)\b',
        r'\b(?:M\.?Com|MCom|Master of Commerce?)\b',
        r'\b(?:M\.?Tech|MTech|Master of Technology?)\b',
        r'\b(?:M\.?B\.?A|MBA|Master of Business Admin[istration]*)\b',
        r'\b(?:M\.?C\.?A|MCA|Master of Computer Applications?)\b',
        r'\b(?:B\.?C\.?A|BCA|Bachelor of Computer Applications?)\b',
        r'\b(?:LLB?|Bachelor of Law[s]*)\b',
        r'\b(?:LLM|Master of Law[s]*)\b',
        r'\b(?:MBBS|Bachelor of Medicine[,\s]+ Bachelor of Surgery)\b',
        r'\b(?:M\.?D|MD)\b',
        r'\b(?:Ph\.?D|PhD|Doctor of Philosophy)\b',
        r'\b(?:D\.?M\.?D|DMD)\b',
        r'\b(?:B\.?D\.?S|BDS|Bachelor of Dental Surgery)\b',
        r'\b(?:A\.?D\.?C|ADC|Auxiliary Dental Surgeon)\b',
        r'\b(?:Diploma)\b',
        r'\b(?:HSSC?|High School|10\+2|12th|12 pass)\b',
        r'\b(?:SSC|10th|10 pass)\b',
    ],
    'field_markers': [
        r'(?:Engineering|Engineer)',
        r'(?:Commerce|Commercial)',
        r'(?:Science)',
        r'(?:Arts?|Humanities)',
        r'(?:Medicine|Medical)',
        r'(?:Law|Legal)',
        r'(?:Business|Management)',
        r'(?:Information Technology|IT|Computer)',
        r'(?:Finance|Accounting)',
        r'(?:Marketing)',
        r'(?:Human Resources?|HR)',
        r'(?:Education|Teaching)',
    ]
}

# Caste-related keywords
CASTE_PATTERNS = {
    'jaati_markers': [
        r'(?:Pareek|Joshi|Gupta|Sharma|Verma|Singh|Patel|Reddy|Nair|Iyer|Iyengar)',
        r'(?:Brahmin|Brahman|Bania|Baniya|Kshatriya|Shudra|Vaishya)',
        r'(?:Rajput|Maratha|Ahir|Jat|Yaadav|Yadav)',
    ],
    'gotra_markers': [
        r'Upmanyu|Bharadwaj|Kashyap|Kaushal|Vashist|Atri|Bhrigu|Angirasa',
        r'Kachhyap|Goutam|Maudgalya|Punarvasu|Gautam|Agastya|Rishi',
    ],
    'sakha_markers': [
        r'(?:Rigveda|Yajurveda|Samaveda|Atharvaveda)',
        r'(?:Shukla|Krishna)',
    ]
}


def extract_education_from_text(text: str) -> List[str]:
    """
    Extract education/qualification information from unstructured text.
    
    Searches for degree names, field of study, and education-related keywords.
    
    Args:
        text: Unstructured text containing education information
        
    Returns:
        List of extracted education values
        
    Example:
        text = "B.Tech in Computer Science and M.Tech specializing in AI"
        result = extract_education_from_text(text)
        # Returns something like ['B.Tech', 'M.Tech', 'Computer Science', 'AI']
    """
    if not text or not isinstance(text, str):
        return []
    
    education_items = set()
    text_lower = text.lower()
    
    # Find degree patterns
    for pattern in EDUCATION_PATTERNS['degree_markers']:
        matches = re.finditer(pattern, text, re.IGNORECASE)
        for match in matches:
            education_items.add(match.group(0).strip())
    
    # Find field of study patterns
    for pattern in EDUCATION_PATTERNS['field_markers']:
        matches = re.finditer(pattern, text, re.IGNORECASE)
        for match in matches:
            education_items.add(match.group(0).strip())
    
    # Look for institutions (optional - if mentioned with "from" or "at")
    institution_pattern = r'(?:from|at|studied at)\s+([A-Z][A-Za-z\s&\.,-]*(?:University|College|Institute|School|Academy))'
    inst_matches = re.finditer(institution_pattern, text, re.IGNORECASE)
    for match in inst_matches:
        institution = match.group(1).strip()
        if institution:
            education_items.add(institution)
    
    return sorted(list(education_items))


def extract_caste_components_from_text(
    text: str,
    master_dir: Optional[Path] = None
) -> Dict[str, Optional[List[str]]]:
    """
    Extract caste-related components (jaati, gotra, sakha) from unstructured text.
    
    Args:
        text: Unstructured text containing caste information
        master_dir: Optional path to master data directory
        
    Returns:
        Dictionary with keys:
        {
            'jaati': [...],
            'gotra': [...],
            'sakha': [...]
        }
    """
    result = {
        'jaati': [],
        'gotra': [],
        'sakha': []
    }
    
    if not text or not isinstance(text, str):
        return result
    
    text_lower = text.lower()
    
    # Find jaati (caste) patterns
    for pattern in CASTE_PATTERNS['jaati_markers']:
        matches = re.finditer(pattern, text, re.IGNORECASE)
        for match in matches:
            jaati = match.group(0).strip()
            if jaati not in result['jaati']:
                result['jaati'].append(jaati)
    
    # Find gotra patterns
    for pattern in CASTE_PATTERNS['gotra_markers']:
        matches = re.finditer(pattern, text, re.IGNORECASE)
        for match in matches:
            gotra = match.group(0).strip()
            if gotra not in result['gotra']:
                result['gotra'].append(gotra)
    
    # Find sakha patterns
    for pattern in CASTE_PATTERNS['sakha_markers']:
        matches = re.finditer(pattern, text, re.IGNORECASE)
        for match in matches:
            sakha = match.group(0).strip()
            if sakha not in result['sakha']:
                result['sakha'].append(sakha)
    
    # Try to match against master if available
    if master_dir is None:
        master_dir = Path(__file__).resolve().parent.parent / "Data" / "training"
    
    try:
        from .matcher import match_one
        caste_df = masters.load_master("caste", master_dir=master_dir)
        
        # Refine results using master lookups
        refined_result = result.copy()
        
        # For each extracted item, try to find best match in master
        for jaati in result['jaati']:
            best_match = _find_best_caste_match(jaati, caste_df, "Jaati")
            if best_match and best_match not in refined_result['jaati']:
                refined_result['jaati'].append(best_match)
        
        for gotra in result['gotra']:
            best_match = _find_best_caste_match(gotra, caste_df, "Gotra")
            if best_match and best_match not in refined_result['gotra']:
                refined_result['gotra'].append(best_match)
        
        for sakha in result['sakha']:
            best_match = _find_best_caste_match(sakha, caste_df, "Sakha")
            if best_match and best_match not in refined_result['sakha']:
                refined_result['sakha'].append(best_match)
        
        return refined_result
    except Exception:
        # If master lookup fails, return raw extracted values
        return result


def _find_best_caste_match(value: str, df, column: str) -> Optional[str]:
    """Helper to find best match in caste dataframe."""
    if column not in df.columns:
        return None
    
    from fuzzywuzzy import fuzz
    
    best_match = None
    best_score = 0
    
    for master_val in df[column].dropna().astype(str):
        master_val_str = master_val.strip()
        score = fuzz.token_set_ratio(value.lower(), master_val_str.lower())
        if score > best_score and score >= 75:
            best_score = score
            best_match = master_val_str
    
    return best_match


def extract_all_structured_info(text: str) -> Dict[str, Any]:
    """
    Extract all structured information from unstructured text.
    
    Combines extraction of education, caste, gotra, and sakha from text.
    
    Args:
        text: Unstructured text
        
    Returns:
        Dictionary with extracted fields:
        {
            'education': [...],
            'jaati': [...],
            'gotra': [...],
            'sakha': [...],
        }
    """
    result = {}
    
    # Extract education
    education = extract_education_from_text(text)
    if education:
        result['education'] = education
    
    # Extract caste components
    caste_components = extract_caste_components_from_text(text)
    if caste_components['jaati']:
        result['jaati'] = caste_components['jaati']
    if caste_components['gotra']:
        result['gotra'] = caste_components['gotra']
    if caste_components['sakha']:
        result['sakha'] = caste_components['sakha']
    
    return result


def enrich_profile_from_unstructured_text(
    biodata: Dict[str, Any],
    unstructured_text: str
) -> Dict[str, Any]:
    """
    Enrich biodata with extracted information from unstructured text.
    
    Only fills fields that are currently None/empty.
    
    Args:
        biodata: Structured biodata dictionary
        unstructured_text: Raw unstructured text
        
    Returns:
        Updated biodata with enriched fields
    """
    biodata_copy = biodata.copy()
    extracted = extract_all_structured_info(unstructured_text)
    
    # Fill education if empty
    if not biodata_copy.get('education') and extracted.get('education'):
        biodata_copy['education'] = extracted['education'][0]  # Take first match
    
    # Fill jaati if empty
    if not biodata_copy.get('jaati') and extracted.get('jaati'):
        biodata_copy['jaati'] = extracted['jaati'][0]  # Take first match
    
    # Fill gotra if empty
    if not biodata_copy.get('gotra') and extracted.get('gotra'):
        biodata_copy['gotra'] = extracted['gotra'][0]  # Take first match
    
    # Fill sakha if empty
    if not biodata_copy.get('sakha') and extracted.get('sakha'):
        biodata_copy['sakha'] = extracted['sakha'][0]  # Take first match
    
    return biodata_copy


__all__ = [
    "extract_education_from_text",
    "extract_caste_components_from_text",
    "extract_all_structured_info",
    "enrich_profile_from_unstructured_text",
]
