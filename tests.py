"""
Unit tests for the LLM Extraction module.
Tests validation, parsing, and error handling.

Run with:
    python -m pytest tests.py -v
"""

import json
import pytest
from unittest.mock import patch, MagicMock

from config import EXTRACTION_SCHEMA
from validators import (
    extract_json_from_response,
    validate_extracted_data,
    normalize_response,
    safe_parse_response,
)


class TestJsonExtraction:
    """Test JSON extraction from various response formats."""
    
    def test_extract_valid_json(self):
        """Test extraction of plain JSON."""
        response = '{"full_name": "John Doe", "age": 28}'
        result = extract_json_from_response(response)
        assert result["full_name"] == "John Doe"
        assert result["age"] == 28
    
    def test_extract_json_from_markdown(self):
        """Test extraction from markdown code blocks."""
        response = """Here is the data:
```json
{"full_name": "Jane Doe", "profession": "Engineer"}
```
"""
        result = extract_json_from_response(response)
        assert result["full_name"] == "Jane Doe"
        assert result["profession"] == "Engineer"
    
    def test_extract_json_with_prose(self):
        """Test extraction when JSON is embedded in text."""
        response = """
        Based on the text, here's the extracted information:
        {"full_name": "Bob Smith", "location": "NYC"}
        This includes all available data.
        """
        result = extract_json_from_response(response)
        assert result["full_name"] == "Bob Smith"
    
    def test_extract_invalid_json_returns_none(self):
        """Test that invalid JSON returns None."""
        response = "{invalid json}"
        result = extract_json_from_response(response)
        assert result is None
    
    def test_extract_empty_string_returns_none(self):
        """Test that empty string returns None."""
        result = extract_json_from_response("")
        assert result is None


class TestValidation:
    """Test data validation against schema."""
    
    def test_valid_data(self):
        """Test validation of correct data."""
        data = {
            "full_name": "John Doe",
            "age": 28,
            "date_of_birth": None,
            "height": None,
            "gender": None,
            "marital_status": None,
            "profession": "Engineer",
            "education": None,
            "religion": None,
            "caste": None,
            "location": "Delhi",
        }
        is_valid, msg = validate_extracted_data(data, EXTRACTION_SCHEMA)
        assert is_valid is True
        assert msg == ""
    
    def test_missing_keys(self):
        """Test detection of missing keys."""
        data = {"full_name": "John Doe"}
        is_valid, msg = validate_extracted_data(data, EXTRACTION_SCHEMA)
        assert is_valid is False
        assert "Missing required keys" in msg
    
    def test_extra_keys(self):
        """Test detection of extra keys."""
        data = dict(EXTRACTION_SCHEMA)
        data["extra_field"] = "value"
        is_valid, msg = validate_extracted_data(data, EXTRACTION_SCHEMA)
        assert is_valid is False
        assert "Unexpected keys" in msg
    
    def test_non_dict_input(self):
        """Test that non-dict input is rejected."""
        is_valid, msg = validate_extracted_data("not a dict", EXTRACTION_SCHEMA)
        assert is_valid is False
        assert "not a dictionary" in msg


class TestNormalization:
    """Test response normalization."""
    
    def test_normalize_adds_missing_fields(self):
        """Test that normalization adds missing fields as None."""
        data = {"full_name": "John Doe"}
        result = normalize_response(data, EXTRACTION_SCHEMA)
        assert len(result) == len(EXTRACTION_SCHEMA)
        assert result["full_name"] == "John Doe"
        assert result["age"] is None
    
    def test_normalize_removes_extra_fields(self):
        """Test that normalization removes extra fields."""
        data = dict(EXTRACTION_SCHEMA)
        data["extra"] = "value"
        result = normalize_response(data, EXTRACTION_SCHEMA)
        assert "extra" not in result
        assert len(result) == len(EXTRACTION_SCHEMA)


class TestSafeParseResponse:
    """Test safe parsing with error handling."""
    
    def test_safe_parse_valid_response(self):
        """Test parsing of valid response."""
        response = json.dumps(dict(EXTRACTION_SCHEMA, full_name="John Doe"))
        result = safe_parse_response(response, EXTRACTION_SCHEMA)
        assert result["full_name"] == "John Doe"
        assert len(result) == len(EXTRACTION_SCHEMA)
    
    def test_safe_parse_invalid_json(self):
        """Test that invalid JSON returns schema with nulls."""
        response = "not valid json"
        result = safe_parse_response(response, EXTRACTION_SCHEMA)
        assert result == EXTRACTION_SCHEMA
        assert all(v is None for v in result.values())
    
    def test_safe_parse_incomplete_data(self):
        """Test parsing of incomplete data."""
        response = '{"full_name": "John"}'
        result = safe_parse_response(response, EXTRACTION_SCHEMA)
        assert result["full_name"] == "John"
        assert result["age"] is None
        assert len(result) == len(EXTRACTION_SCHEMA)
    
    def test_safe_parse_empty_string(self):
        """Test parsing empty string."""
        result = safe_parse_response("", EXTRACTION_SCHEMA)
        assert result == EXTRACTION_SCHEMA


class TestSchemaIntegrity:
    """Test that extraction schema is correct."""
    
    def test_schema_has_all_required_fields(self):
        """Test that schema contains all required fields."""
        required_fields = {
            "full_name", "age", "date_of_birth", "height", "gender",
            "marital_status", "profession", "education", "religion",
            "caste", "location"
        }
        assert set(EXTRACTION_SCHEMA.keys()) == required_fields
    
    def test_schema_values_are_null(self):
        """Test that schema default values are None."""
        assert all(v is None for v in EXTRACTION_SCHEMA.values())


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
