"""
Configuration for LLM extraction settings.
Contains model parameters, prompts, and extraction schema.
"""

from typing import Any

# LLM Configuration
LLM_CONFIG = {
    "model": "gpt-4o-mini",  # OpenAI model for matrimonial biodata extraction
    "temperature": 0.1,  # Low temperature for deterministic extraction
    "max_tokens": 1024,
    "top_p": 0.9,
}

# Extraction Schema - Fields to extract from matrimonial biodata
EXTRACTION_SCHEMA = {
    "first_name": None,
    "last_name": None,
    "full_name": None,
    "gender": None,
    "date_of_birth": None,
    "age": None,
    "birth_time": None,
    "birth_place": None,
    "height": None,
    "marital_status": None,
    "religion": None,
    "caste": None,
    "jaati": None,
    "gotra": None,
    "sakha": None,
    "manglik": None,
    "education": None,
    "specialization": None,
    "occupation": None,
    "annual_income": None,
    "address": None,
    "village": None,
    "tahsil": None,
    "district": None,
    "native_state": None,
    "state": None,
    "city": None,
    "country": None,
    "zip_code": None,
    "email_id": None,
    "mobile_no": None,
    "phone_no": None,
    "about_yourself_summary": None,
}

# Field descriptions for validation
FIELD_DESCRIPTIONS: dict[str, str] = {
    "first_name": "First name of the person (string or null)",
    "last_name": "Last name/surname of the person (string or null)",
    "full_name": "Full name of the person (string or null)",
    "gender": "Gender (e.g., 'Male', 'Female', 'Other') (string or null)",
    "date_of_birth": "Date of birth in YYYY-MM-DD format (string or null)",
    "age": "Age in years (integer or null)",
    "birth_time": "Birth time in HH:MM format (string or null)",
    "birth_place": "Birth place/city (string or null)",
    "height": "Height with unit (e.g., '5.8 ft', '175 cm') (string or null)",
    "marital_status": "Marital status (e.g., 'Single', 'Married', 'Divorced', 'Widowed') (string or null)",
    "religion": "Religion (string or null)",
    "caste": "Caste/Community (string or null)",
    "jaati": "Jaati/Community in Hindi (string or null)",
    "gotra": "Gotra/Clan (string or null)",
    "sakha": "Sakha/Branch (string or null)",
    "manglik": "Manglik status (e.g., 'Yes', 'No', 'Maybe') (string or null)",
    "education": "Educational qualification (string or null)",
    "specialization": "Specialization/Field of study (string or null)",
    "occupation": "Occupation or profession (string or null)",
    "annual_income": "Annual income (string or null)",
    "address": "Full address (string or null)",
    "village": "Village name (string or null)",
    "tahsil": "Tahsil/Administrative division (string or null)",
    "district": "District (string or null)",
    "native_state": "Native state (string or null)",
    "state": "Current state (string or null)",
    "city": "City (string or null)",
    "country": "Country (string or null)",
    "zip_code": "Zip/Postal code (string or null)",
    "email_id": "Email address (string or null)",
    "mobile_no": "Mobile number formatted as +91 xxxxxxxxxx (e.g., +91 9876543210) (string or null)",
    "phone_no": "Phone number (string or null)",
    "about_yourself_summary": "Summary of additional personal/professional information from ABOUT YOURSELF section (string or null)",
}
