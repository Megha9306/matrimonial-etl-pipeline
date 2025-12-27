"""
Field-specific validators to prevent mismatched data in extraction results.
Validates extracted values against field constraints and master data where appropriate.
"""

import re
from typing import Any, Optional, Dict, List, Tuple
from pathlib import Path


class FieldValidator:
    """Validates that extracted values match their field types and constraints."""
    
    # Define field constraints
    FIELD_CONSTRAINTS = {
        # Location fields - must be actual location names
        "state": {
            "type": "location",
            "pattern": r"^[a-zA-Z\s\-'&.]{2,50}$",
            "description": "State/Province name (2-50 chars, letters only)",
            "examples": ["Rajasthan", "Maharashtra", "California"]
        },
        "city": {
            "type": "location",
            "pattern": r"^[a-zA-Z\s\-'&.]{2,50}$",
            "description": "City/Town name (2-50 chars, letters only)",
            "examples": ["Bangalore", "Mumbai", "Delhi"]
        },
        "country": {
            "type": "location",
            "pattern": r"^[a-zA-Z\s\-'&.]{2,50}$",
            "description": "Country name (2-50 chars, letters only)",
            "examples": ["India", "USA", "Canada"]
        },
        "district": {
            "type": "location",
            "pattern": r"^[a-zA-Z\s\-'&.]{2,50}$",
            "description": "District name (2-50 chars, letters only)",
            "examples": ["Alwar", "Jaipur"]
        },
        "village": {
            "type": "location",
            "pattern": r"^[a-zA-Z\s\-'&.]{2,50}$",
            "description": "Village name (2-50 chars, letters only)",
            "examples": ["Rajgarh"]
        },
        "tahsil": {
            "type": "location",
            "pattern": r"^[a-zA-Z\s\-'&.]{2,50}$",
            "description": "Tahsil/Administrative unit (2-50 chars, letters only)",
            "examples": ["Alwar", "Jodhpur"]
        },
        "zip_code": {
            "type": "numeric",
            "pattern": r"^\d{5,10}$",
            "description": "Numeric postal/zip code (5-10 digits only)",
            "examples": ["560001", "400001", "110001"]
        },
        "address": {
            "type": "text",
            "pattern": None,
            "description": "Street address, locality, area - NOT personal names, NOT education",
            "examples": ["MG Road, Bangalore", "123 Main Street"]
        },
        
        # Education fields - only degree/qualification names
        "education": {
            "type": "education",
            "pattern": r"^[A-Z.]+[\w\s\-().,]*$",
            "description": "Degree/Qualification only (B.Tech, MBA, M.Sc, etc) - NOT institution names",
            "examples": ["B.Tech", "MBA", "M.Sc", "B.Com"]
        },
        "specialization": {
            "type": "education",
            "pattern": r"^[a-zA-Z\s\-'&.()]{2,50}$",
            "description": "Field of study only - NOT institution names",
            "examples": ["Computer Science", "Finance", "Marketing"]
        },
        
        # Personal fields - names only, no titles
        "first_name": {
            "type": "name",
            "pattern": r"^[a-zA-Z\s\-']{2,30}$",
            "description": "First name only (no titles, relations)",
            "examples": ["Ankur", "Priya", "Rajesh"]
        },
        "last_name": {
            "type": "name",
            "pattern": r"^[a-zA-Z\s\-']{2,30}$",
            "description": "Last name/surname only",
            "examples": ["Pareek", "Sharma", "Patel"]
        },
        "full_name": {
            "type": "name",
            "pattern": r"^[a-zA-Z\s\-']{4,60}$",
            "description": "Full name (no titles)",
            "examples": ["Ankur Pareek", "Priya Sharma"]
        },
        
        # Occupation field - job title only
        "occupation": {
            "type": "occupation",
            "pattern": r"^[a-zA-Z\s\-']{2,50}$",
            "description": "Profession/Job title only - NOT company names",
            "examples": ["Engineer", "Teacher", "Business"]
        },
        
        # Community/Caste fields - specific meanings for each
        "caste": {
            "type": "caste",
            "pattern": r"^[a-zA-Z\s\-']{2,30}$",
            "description": "Caste/Community name",
            "examples": ["Brahmin", "Kshatriya", "Bohra"]
        },
        "jaati": {
            "type": "caste",
            "pattern": r"^[a-zA-Z\s\-']{2,30}$",
            "description": "Family/Jaati name (not caste)",
            "examples": ["Pareek", "Sharma", "Joshi"]
        },
        "gotra": {
            "type": "caste",
            "pattern": r"^[a-zA-Z\s\-']{2,30}$",
            "description": "Gotra/Clan name only",
            "examples": ["Upmanyu", "Bharadwaj", "Kashyap"]
        },
        "sakha": {
            "type": "caste",
            "pattern": r"^[a-zA-Z\s\-']{2,30}$",
            "description": "Sakha/Vedic branch only",
            "examples": ["Rigveda", "Mudgal", "Shyama"]
        },
        "religion": {
            "type": "caste",
            "pattern": r"^[a-zA-Z\s\-']{2,30}$",
            "description": "Religion name only",
            "examples": ["Hindu", "Muslim", "Christian"]
        },
        
        # Marital status - STRICT: only specific values
        "marital_status": {
            "type": "enum",
            "pattern": None,
            "description": "Marital status - MUST be from master: Single, Married, Divorced, Widowed, Separated, Un-Married, Awaiting Divorce",
            "examples": ["Single", "Married", "Divorced", "Widowed", "Un-Married"],
            "allowed_values": ["Single", "Married", "Divorced", "Widowed", "Separated", "Un-Married", "Awaiting Divorce"]
        },
        
        # Manglik - STRICT: only specific values
        "manglik": {
            "type": "enum",
            "pattern": None,
            "description": "Manglik status - MUST be from master: Yes, No, Don't Know",
            "examples": ["Yes", "No", "Don't Know"],
            "allowed_values": ["Yes", "No", "Don't Know"]
        },
        
        # Contact fields - phone/mobile numbers
        "mobile_no": {
            "type": "phone",
            "pattern": r"^\+91\s?\d{10}$",
            "description": "Mobile number in format: +91 xxxxxxxxxx (10 digits after country code)",
            "examples": ["+91 9876543210", "+919876543210"]
        },
        "phone_no": {
            "type": "phone",
            "pattern": None,
            "description": "Phone number (landline format varies by region)",
            "examples": ["011-12345678", "9876543210"]
        },
    }
    
    # Suspicious patterns that indicate data is in wrong field
    SUSPICIOUS_PATTERNS = {
        "education": {
            # University names commonly mixed with education field (with word boundaries)
            r"(?i)\b(university|college|school|institute|department|faculty|academy)\b",
            # Indicates this should be in address or other field
        },
        "state": {
            # Personal names, names shouldn't be in state
            r"(?i)(road|street|area|colony|sector|plot|house|apartment|bldg|mohalla|lane)",
            # Institution names shouldn't be in state
            r"(?i)(university|college|school|institute|hospital|office|department|faculty|academy)",
            # City names shouldn't be in state 
            r"(?i)(bandar|town|city|municipal)",
            # Multiple words separated by comma/semicolon suggest address
            r",|;",
        },
        "city": {
            # Education terms shouldn't be in city (with word boundaries)
            r"(?i)\b(degree|diploma|certified|b\.tech|mba|m\.sc|b\.com|b\.a|m\.a|university|college)\b",
            # Complex names like "Name Surname" shouldn't be in city (simple 2-word proper names)
            # but valid city names like "New York" are okay
            r"^[A-Z][a-z]*\s[A-Z][a-z]*$",  # Exactly 2 capitalized words (likely a person name)
        },
        "zip_code": {
            # Non-numeric shouldn't be in zip code
            r"[^0-9]",  # Any non-digit
        }
    }
    
    @staticmethod
    def validate_field(field_name: str, value: Any) -> Tuple[bool, Optional[str]]:
        """
        Validate that a field value matches the field's constraints.
        
        Args:
            field_name: Name of the field (e.g., "state", "education")
            value: The extracted value to validate
            
        Returns:
            (is_valid: bool, error_message: str or None)
        """
        if value is None or value == "":
            return True, None  # Null values are always valid
        
        # Convert to string for validation
        value_str = str(value).strip()
        if not value_str:
            return True, None
        
        # Get field constraints
        if field_name not in FieldValidator.FIELD_CONSTRAINTS:
            return True, None  # Unknown fields pass validation
        
        constraint = FieldValidator.FIELD_CONSTRAINTS[field_name]
        
        # Check if field is enum type with allowed values (STRICT validation)
        if constraint.get("type") == "enum" and "allowed_values" in constraint:
            if value_str not in constraint["allowed_values"]:
                # Try case-insensitive match
                matched = False
                for allowed in constraint["allowed_values"]:
                    if allowed.lower() == value_str.lower():
                        matched = True
                        break
                if not matched:
                    return False, f"Field '{field_name}' must be one of: {', '.join(constraint['allowed_values'])} (got: {value_str})"
        
        # Check pattern if defined
        if constraint["pattern"]:
            pattern = constraint["pattern"]
            if not re.match(pattern, value_str):
                return False, f"Field '{field_name}' does not match expected pattern: {constraint['description']}"
        
        # Check for suspicious patterns
        if field_name in FieldValidator.SUSPICIOUS_PATTERNS:
            for suspicious_pattern in FieldValidator.SUSPICIOUS_PATTERNS[field_name]:
                if re.search(suspicious_pattern, value_str):
                    return False, f"Field '{field_name}' contains suspicious text (likely data from different field): {value_str[:50]}"
        
        return True, None
    
    @staticmethod
    def validate_profile(profile: Dict[str, Any]) -> Tuple[bool, Dict[str, List[str]]]:
        """
        Validate all fields in an extracted profile.
        
        Args:
            profile: Dictionary of extracted biodata fields
            
        Returns:
            (is_valid: bool, errors: {field_name: [error_messages]})
        """
        errors: Dict[str, List[str]] = {}
        
        for field_name, value in profile.items():
            if value is None or value == "":
                continue
            
            is_valid, error_msg = FieldValidator.validate_field(field_name, value)
            if not is_valid:
                if field_name not in errors:
                    errors[field_name] = []
                errors[field_name].append(error_msg)
        
        is_valid = len(errors) == 0
        return is_valid, errors
    
    @staticmethod
    def sanitize_profile(profile: Dict[str, Any]) -> Dict[str, Any]:
        """
        Remove or fix fields that fail validation.
        Fields with validation errors are set to None.
        
        Args:
            profile: Dictionary of extracted biodata fields
            
        Returns:
            Sanitized profile with invalid fields set to None
        """
        sanitized = profile.copy()
        
        is_valid, errors = FieldValidator.validate_profile(profile)
        
        # Set invalid fields to None
        for field_name in errors:
            print(f"Warning: Removing invalid data from '{field_name}': {errors[field_name][0]}")
            sanitized[field_name] = None
        
        return sanitized


class PhoneNumberValidator:
    """Validates and normalizes phone numbers to +91 xxxxxxxxxx format."""
    
    @staticmethod
    def normalize_mobile_number(value: str) -> Optional[str]:
        """
        Normalize a mobile number to +91 xxxxxxxxxx format.
        Handles various input formats like:
        - 9876543210
        - +919876543210
        - +91-9876543210
        - 91 9876543210
        - 0919876543210
        
        Args:
            value: Raw mobile number string
            
        Returns:
            Normalized mobile number in format +91 xxxxxxxxxx, or None if invalid
        """
        if not value:
            return None
        
        # Convert to string and remove whitespace
        mobile_str = str(value).strip()
        
        # Remove all non-digit characters except leading +
        if mobile_str.startswith('+'):
            # Keep the + and remove other non-digits
            cleaned = '+' + re.sub(r'\D', '', mobile_str)
        else:
            # Remove all non-digits
            cleaned = re.sub(r'\D', '', mobile_str)
        
        # Extract just the digits after any country code
        digits_only = re.sub(r'\D', '', mobile_str)
        
        # Check if it's 10 digits (Indian mobile)
        if len(digits_only) == 10:
            return f"+91 {digits_only}"
        
        # Check if it's 12 digits (91 + 10 digits)
        if len(digits_only) == 12 and digits_only.startswith('91'):
            return f"+91 {digits_only[2:]}"
        
        # Check if it's 13 digits with leading 0 (0 + 91 + 10 digits) 
        if len(digits_only) == 13 and digits_only.startswith('091'):
            return f"+91 {digits_only[3:]}"
        
        # If we have more/less than expected, return None
        return None
    
    @staticmethod
    def is_valid_mobile_number(value: str) -> bool:
        """
        Check if a mobile number is valid (can be normalized).
        
        Args:
            value: Mobile number string to validate
            
        Returns:
            True if the number can be normalized to +91 xxxxxxxxxx format
        """
        if not value:
            return False
        
        normalized = PhoneNumberValidator.normalize_mobile_number(value)
        return normalized is not None


class AddressValidator:
    """Validates and enforces zip code constraints."""
    
    @staticmethod
    def is_valid_zipcode(value: str) -> bool:
        """
        Check if value is a valid zip code (numeric, 5-10 digits).
        
        Args:
            value: String to validate
            
        Returns:
            True if valid zip code format
        """
        if not value:
            return False
        
        value_str = str(value).strip()
        # Zip code must be 5-10 digits only
        return bool(re.match(r"^\d{5,10}$", value_str))
    
    @staticmethod
    def extract_zipcode(text: str) -> Optional[str]:
        """
        Extract a valid zip code from text if present.
        
        Args:
            text: Text that may contain zip code
            
        Returns:
            Extracted zip code or None
        """
        if not text:
            return None
        
        # Look for 5-10 consecutive digits
        matches = re.findall(r"\b\d{5,10}\b", str(text))
        
        if matches:
            # Return the first valid zip code found
            return matches[0]
        
        return None
    
    @staticmethod
    def validate_address_field(value: str) -> Tuple[bool, Optional[str]]:
        """
        Validate that address field contains address, not personal names or education.
        
        Args:
            value: Address value to validate
            
        Returns:
            (is_valid: bool, error_message: str or None)
        """
        if not value:
            return True, None
        
        value_lower = str(value).lower()
        
        # Red flags for address field containing wrong data
        education_keywords = ["degree", "diploma", "certified", "b.tech", "mba", "m.sc", "b.com",
                             "b.a", "b.sc", "m.a", "engineering", "medical", "university", "college"]
        
        for keyword in education_keywords:
            if keyword in value_lower:
                return False, f"Address field appears to contain education data: '{value[:50]}...'"
        
        # Address should have location-related words or structure
        address_keywords = ["road", "street", "area", "colony", "sector", "plot", "house", "apartment",
                           "lane", "block", "phase", "near", "opposite"]
        
        has_address_keyword = any(keyword in value_lower for keyword in address_keywords)
        
        # If it's just a single name, it's probably wrong
        if len(value_lower.split()) <= 1 and not has_address_keyword:
            return False, f"Address appears to be a single name, likely misplaced: '{value}'"
        
        return True, None


def sanitize_lm_extraction(raw_profile: Dict[str, Any]) -> Dict[str, Any]:
    """
    Post-process LLM extraction to fix common field mismatching issues.
    
    Args:
        raw_profile: Raw extraction output from LLM
        
    Returns:
        Sanitized profile with invalid/mismatched fields fixed
    """
    sanitized = raw_profile.copy()
    
    # Validate and fix fields
    is_valid, errors = FieldValidator.validate_profile(raw_profile)
    
    if errors:
        print(f"Found {len(errors)} validation errors in LLM extraction")
        for field_name, error_list in errors.items():
            print(f"  - {field_name}: {error_list[0]}")
            # Set invalid fields to None
            sanitized[field_name] = None
    
    # Additional cleanup: ensure zip codes are numeric only
    if "zip_code" in sanitized and sanitized["zip_code"]:
        extracted_zip = AddressValidator.extract_zipcode(str(sanitized["zip_code"]))
        if extracted_zip and AddressValidator.is_valid_zipcode(extracted_zip):
            sanitized["zip_code"] = extracted_zip
        elif not AddressValidator.is_valid_zipcode(str(sanitized["zip_code"])):
            print(f"Warning: Invalid zip code format removed: {sanitized['zip_code']}")
            sanitized["zip_code"] = None
    
    # Normalize mobile numbers to +91 xxxxxxxxxx format
    if "mobile_no" in sanitized and sanitized["mobile_no"]:
        normalized_mobile = PhoneNumberValidator.normalize_mobile_number(str(sanitized["mobile_no"]))
        if normalized_mobile:
            sanitized["mobile_no"] = normalized_mobile
        else:
            print(f"Warning: Invalid mobile number format removed: {sanitized['mobile_no']}")
            sanitized["mobile_no"] = None
    
    return sanitized


__all__ = [
    "FieldValidator",
    "PhoneNumberValidator",
    "AddressValidator",
    "sanitize_lm_extraction",
]
