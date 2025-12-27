"""
Reverse geocoding and address lookup module.
Finds the most accurate ZIP code, state, and city given an address.
"""

from pathlib import Path
from typing import Dict, List, Optional, Tuple
import pandas as pd
from fuzzywuzzy import fuzz
from fuzzywuzzy import process as fuzzy_process

from . import masters


def lookup_zipcode_by_address(
    address: str,
    city: Optional[str] = None,
    state: Optional[str] = None,
    master_dir: Optional[Path] = None
) -> Optional[Dict[str, str]]:
    """
    Find the most accurate ZIP code, state, and city given an address.
    
    Uses fuzzy matching against address master file.
    Can optionally filter by city and state for better accuracy.
    
    Args:
        address: The street address or partial address string
        city: Optional city name to narrow search
        state: Optional state name to narrow search
        master_dir: Optional path to master data directory
        
    Returns:
        Dictionary with keys:
        {
            'zip_code': '...',
            'city': '...',
            'state': '...',
            'country': '...',
            ...other address fields from master...
        }
        
        Returns None if no match found.
        
    Example:
        result = lookup_zipcode_by_address(
            "123 Main Street",
            city="New York",
            state="NY"
        )
    """
    if not address or not isinstance(address, str):
        return None
    
    address = address.strip()
    if not address:
        return None
    
    # Default master_dir if not provided
    if master_dir is None:
        master_dir = Path(__file__).resolve().parent.parent / "Data" / "training"
    
    try:
        df = masters.load_master("country_state", master_dir=master_dir)
    except Exception:
        return None
    
    # Check if there are address-related columns
    # Look for columns that might contain address, street, area, locality, etc.
    address_cols = [col for col in df.columns 
                   if any(x in col.lower() for x in ['address', 'street', 'area', 'locality', 'place'])]
    
    if not address_cols:
        # Fallback: try to match using city/state if they exist
        return _lookup_by_city_state(df, city, state)
    
    # Prepare search dataframe
    search_df = df.copy()
    
    # Filter by city if provided
    if city:
        city_cols = [col for col in df.columns if 'city' in col.lower()]
        if city_cols:
            city_col = city_cols[0]
            city_matches = search_df[city_col].astype(str).str.lower() == city.lower()
            search_df = search_df[city_matches]
    
    # Filter by state if provided
    if state:
        state_cols = [col for col in df.columns if 'state' in col.lower()]
        if state_cols:
            state_col = state_cols[0]
            state_matches = search_df[state_col].astype(str).str.lower() == state.lower()
            search_df = search_df[state_matches]
    
    if search_df.empty:
        search_df = df.copy()
    
    # Find the best match in address columns
    best_match = None
    best_score = 0
    best_row_idx = -1
    
    for addr_col in address_cols:
        for idx, master_addr in enumerate(search_df[addr_col].dropna()):
            master_addr_str = str(master_addr).strip()
            # Calculate similarity score
            score = fuzz.token_set_ratio(address.lower(), master_addr_str.lower())
            
            if score > best_score:
                best_score = score
                best_match = master_addr_str
                best_row_idx = search_df.index[idx]
    
    # Return result if match found with reasonable confidence (>60%)
    if best_row_idx >= 0 and best_score >= 60:
        row = df.loc[best_row_idx]
        result = {}
        for col in df.columns:
            val = row.get(col)
            if pd.notna(val):
                key = col.lower().replace(' ', '_')
                result[key] = str(val).strip()
        return result
    
    return None


def _lookup_by_city_state(
    df: pd.DataFrame,
    city: Optional[str] = None,
    state: Optional[str] = None
) -> Optional[Dict[str, str]]:
    """Helper to lookup by city and state when address columns don't exist."""
    
    if not city and not state:
        return None
    
    matches_df = df
    
    # Filter by city
    if city:
        city_cols = [col for col in df.columns if 'city' in col.lower()]
        if city_cols:
            city_col = city_cols[0]
            matches_df = matches_df[
                matches_df[city_col].astype(str).str.lower() == city.lower()
            ]
    
    # Filter by state
    if state:
        state_cols = [col for col in df.columns if 'state' in col.lower()]
        if state_cols:
            state_col = state_cols[0]
            matches_df = matches_df[
                matches_df[state_col].astype(str).str.lower() == state.lower()
            ]
    
    if matches_df.empty:
        return None
    
    row = matches_df.iloc[0]
    result = {}
    for col in df.columns:
        val = row.get(col)
        if pd.notna(val):
            key = col.lower().replace(' ', '_')
            result[key] = str(val).strip()
    
    return result


def extract_address_components(
    full_address: str,
    master_dir: Optional[Path] = None
) -> Dict[str, Optional[str]]:
    """
    Parse and extract components from a full address string.
    Tries to identify city, state, and ZIP code within the address.
    
    Args:
        full_address: The complete address string
        master_dir: Optional path to master data directory
        
    Returns:
        Dictionary with extracted components:
        {
            'street': '...',
            'city': '...',
            'state': '...',
            'zip_code': '...',
            'country': '...'
        }
    """
    result = {
        'street': None,
        'city': None,
        'state': None,
        'zip_code': None,
        'country': None
    }
    
    if not full_address or not isinstance(full_address, str):
        return result
    
    # Simple pattern-based extraction for ZIP code (5-6 digit number)
    import re
    
    # Look for ZIP code pattern (5 or 6 consecutive digits)
    zip_match = re.search(r'\b\d{5,6}\b', full_address)
    if zip_match:
        result['zip_code'] = zip_match.group(0)
        full_address = full_address[:zip_match.start()].strip()
    
    # Split address by comma
    parts = [p.strip() for p in full_address.split(',')]
    
    if len(parts) >= 3:
        # Typical format: Street, City, State/Country
        result['street'] = parts[0]
        result['city'] = parts[-2]
        result['state'] = parts[-1]
    elif len(parts) == 2:
        result['street'] = parts[0]
        result['city'] = parts[1]
    else:
        result['street'] = full_address
    
    return result


def find_closest_zipcode(
    partial_address: str,
    master_dir: Optional[Path] = None,
    threshold: int = 70
) -> List[Dict[str, str]]:
    """
    Find one or more ZIP codes matching a partial address string.
    
    Args:
        partial_address: Partial or complete address
        master_dir: Optional path to master data directory
        threshold: Minimum fuzzy match score (0-100)
        
    Returns:
        List of matching address records sorted by relevance
        Each record contains zip_code, city, state, etc.
    """
    if not partial_address or not isinstance(partial_address, str):
        return []
    
    partial_address = partial_address.strip()
    if not partial_address:
        return []
    
    # Default master_dir if not provided
    if master_dir is None:
        master_dir = Path(__file__).resolve().parent.parent / "Data" / "training"
    
    try:
        df = masters.load_master("country_state", master_dir=master_dir)
    except Exception:
        return []
    
    results = []
    
    # Check for address columns
    address_cols = [col for col in df.columns 
                   if any(x in col.lower() for x in ['address', 'street', 'area', 'locality', 'city'])]
    
    if not address_cols:
        return []
    
    # Score all rows
    scored_rows = []
    for idx, row in df.iterrows():
        max_score = 0
        for addr_col in address_cols:
            master_val = str(row.get(addr_col, "")).strip()
            if master_val:
                score = fuzz.token_set_ratio(partial_address.lower(), master_val.lower())
                max_score = max(max_score, score)
        
        if max_score >= threshold:
            scored_rows.append((idx, max_score, row))
    
    # Sort by score descending
    scored_rows.sort(key=lambda x: x[1], reverse=True)
    
    # Convert to result dicts
    for idx, score, row in scored_rows[:10]:  # Return top 10
        result = {}
        for col in df.columns:
            val = row.get(col)
            if pd.notna(val):
                key = col.lower().replace(' ', '_')
                result[key] = str(val).strip()
        result['_match_score'] = score
        results.append(result)
    
    return results


__all__ = [
    "lookup_zipcode_by_address",
    "extract_address_components",
    "find_closest_zipcode",
]
