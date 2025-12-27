"""
Validation and parsing utilities for LLM responses.
Handles safe extraction of JSON from LLM output and schema validation.
"""

import json
import re
from typing import Any, Optional

# Import field validators
try:
    from .field_validators import sanitize_lm_extraction
except ImportError:
    sanitize_lm_extraction = None


def extract_json_from_response(response_text: str) -> Optional[dict[str, Any]]:
    """
    Extract JSON from LLM response, handling markdown code blocks and extra text.
    
    Args:
        response_text: Raw text response from the LLM
        
    Returns:
        Parsed JSON as dict, or None if parsing fails
        
    Note:
        Attempts to extract JSON in the following order:
        1. JSON within markdown code blocks (```json ... ```)
        2. Raw JSON in the response
        3. First valid JSON object found
    """
    if not response_text or not response_text.strip():
        return None
    
    # Try to extract from markdown code blocks first
    json_match = re.search(r'```(?:json)?\s*(.*?)```', response_text, re.DOTALL)
    if json_match:
        json_text = json_match.group(1).strip()
        try:
            return json.loads(json_text)
        except json.JSONDecodeError:
            pass
    
    # Try to parse the entire response as JSON
    try:
        return json.loads(response_text.strip())
    except json.JSONDecodeError:
        pass
    
    # Try to find and extract JSON object pattern
    json_pattern = r'\{.*\}'
    json_match = re.search(json_pattern, response_text, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group(0))
        except json.JSONDecodeError:
            pass
    
    return None


def validate_extracted_data(data: dict[str, Any], schema: dict[str, Any]) -> tuple[bool, str]:
    """
    Validate extracted data against the expected schema.
    
    Args:
        data: The extracted data dictionary
        schema: The expected schema (keys with null default values)
        
    Returns:
        Tuple of (is_valid: bool, error_message: str)
    """
    if not isinstance(data, dict):
        return False, "Extracted data is not a dictionary"
    
    # Check that all required keys are present
    missing_keys = set(schema.keys()) - set(data.keys())
    if missing_keys:
        return False, f"Missing required keys: {missing_keys}"
    
    # Check that no unexpected keys are present
    extra_keys = set(data.keys()) - set(schema.keys())
    if extra_keys:
        return False, f"Unexpected keys found: {extra_keys}"
    
    return True, ""


def normalize_response(data: dict[str, Any], schema: dict[str, Any]) -> dict[str, Any]:
    """
    Normalize response to match schema exactly.
    Removes extra keys and ensures all schema keys are present.
    
    Args:
        data: The extracted data
        schema: The expected schema
        
    Returns:
        Normalized dictionary matching the schema
    """
    normalized = {}
    for key in schema.keys():
        normalized[key] = data.get(key, None)
    
    return normalized


def sanitize_extracted_data(data: dict[str, Any]) -> dict[str, Any]:
    """
    Apply field-specific validation and sanitization to extracted data.
    Fixes common field mismatching issues where values end up in wrong fields.
    
    Args:
        data: The extracted data from LLM
        
    Returns:
        Sanitized data with validation applied
    """
    if sanitize_lm_extraction:
        return sanitize_lm_extraction(data)
    return data


__all__ = [
    "extract_json_from_response",
    "validate_extracted_data",
    "normalize_response",
    "sanitize_extracted_data",
]


def safe_parse_response(
    response_text: str,
    schema: dict[str, Any],
) -> dict[str, Any]:
    """
    Safely parse and validate LLM response.
    Applies field-specific validation to prevent mismatched data.
    Returns normalized schema on any error.
    
    Args:
        response_text: Raw response from the LLM
        schema: Expected schema
        
    Returns:
        Validated, sanitized and normalized extracted data, or schema with all nulls on error
    """
    # Extract JSON from response
    extracted_data = extract_json_from_response(response_text)
    
    if extracted_data is None:
        # Return schema with all nulls on parsing failure
        return dict(schema)
    
    # Validate against schema
    is_valid, error_msg = validate_extracted_data(extracted_data, schema)
    
    if not is_valid:
        # Log the error but continue (return normalized response)
        print(f"Validation warning: {error_msg}")
        extracted_data = normalize_response(extracted_data, schema)
    
    # Apply field-specific sanitization to fix mismatched data
    extracted_data = sanitize_extracted_data(extracted_data)
    
    # Return normalized response
    return normalize_response(extracted_data, schema)
